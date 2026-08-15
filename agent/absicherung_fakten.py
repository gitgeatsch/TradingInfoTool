# -*- coding: utf-8 -*-
"""Die Absicherung als PORTFOLIOFRAGE - Paket 14 (15.08.2026).

WARUM DIE ABSICHERUNG EINE EIGENE ROLLE BRAUCHT. Bis heute lief sie durch
denselben Trader-Prompt wie ein Spot-Kauf: Marktstruktur, Widerstand, Momentum
des Instruments selbst. Das ist bei 3QSS und DBPK die falsche Frage.

    Ein Absicherungsinstrument kauft man nicht, weil SEIN Chart gut aussieht.
    Man kauft es, weil das PORTFOLIO ein Risiko traegt, das man nicht tragen
    will.

Der Chart von 3QSS ist das Spiegelbild des Nasdaq. Ihn technisch zu bewerten
heisst, den Nasdaq technisch zu bewerten und das Ergebnis umzudrehen - eine
Aussage, die die Kette an anderer Stelle schon trifft (Lagebild) und die hier
nichts hinzufuegt.

WAS STATTDESSEN ZAEHLT, und das steht seit dem 07.08. in `toepfe.py`:

    benoetigter Einsatz = abzusicherndes Exposure / Hebelfaktor

Drei Zahlen: wieviel Risiko liegt im Depot, wieviel davon ist schon gedeckt,
und wie stark hebelt dieses Instrument.

DIE RECHNUNG WIRD NICHT NACHGEBAUT. `agent/hedge/pipeline.py` fuehrt sie seit
dem 22.07., samt der Falle, die dort dokumentiert ist: ein Hedge-Instrument
OHNE bekannten Preis wuerde stillschweigend als "0 Abdeckung" gezaehlt, und
eine darauf gestuetzte Empfehlung koennte das Portfolio unbemerkt ueberhedgen.
Diese Datei liest die Konstanten von dort und rechnet in EUR, weil der Nutzer
in EUR rechnet - sie ersetzt die Pipeline nicht.

WAS SIE NICHT TUT: sie begrenzt nichts. Das verbleibende Budget ist eine
ANGABE, kein Deckel - nach derselben Trennlinie wie Topf und Cash seit dem
15.08.: das System bemisst den einzelnen Trade, die Aufteilung des Portfolios
bemisst der Nutzer.
"""
from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

# Laufende Gebuehr gehebelter ETPs, anteilig auf die Haltedauer. Dieselbe Zahl
# wie in `backward_tracking._KOSTEN_HEDGE_TER_P_A` - dort steht auch, dass sie
# GESCHAETZT ist (WisdomTree/Xtrackers 0,6-1,0 % p.a.) und nicht belegt.
TER_P_A = 0.008


def _hedge_symbole() -> dict:
    """Symbol -> Hebelfaktor, aus der EINEN Stelle im Projekt."""
    from agent.hedge.pipeline import SYMBOL_ZU_HEBEL_FAKTOR

    return dict(SYMBOL_ZU_HEBEL_FAKTOR)


def _referenz_index(symbol: str) -> str | None:
    from agent.hedge.pipeline import SYMBOL_ZU_REFERENZ_INDEX

    return SYMBOL_ZU_REFERENZ_INDEX.get(symbol)


def lage(conn, symbol: str, kurse_eur: dict | None = None,
         watchlist=None) -> dict:
    """Die Absicherungslage in EUR - oder ein leeres dict, wenn nicht lesbar.

    `kurse_eur` ist Symbol -> Preis; fehlt es, wird aus `price_cache` gelesen.

    FAIL-SOFT MIT VERMERK. Faellt eine Zahl aus, steht das im Ergebnis unter
    `unsicher` - und der Prompt sagt es dem Modell. Eine Absicherungsrechnung,
    die eine Luecke stillschweigend als Null behandelt, ist genau der Fehler,
    den `hedge/pipeline.py` am 18.07. an echten Daten gefunden hat."""
    import config as config_module

    aus: dict = {"unsicher": []}
    try:
        if watchlist is None:
            watchlist = config_module.get_watchlist()
        if kurse_eur is None:
            kurse_eur = {str(r[0]).upper(): r[1] for r in conn.execute(
                "SELECT symbol, price_eur FROM price_cache")}
        from database import db as DB

        bestaende = {str(h.symbol).upper(): h
                     for h in DB.get_all_holdings(conn)
                     if (h.quantity or 0) > 0}
    except Exception as exc:                                 # noqa: BLE001
        logger.info("Absicherungslage nicht lesbar: %s", exc)
        return {}

    hedge = {k.upper(): v for k, v in _hedge_symbole().items()}
    cash = {str(a.symbol).upper() for a in watchlist
            if getattr(a, "ist_cash_aequivalent", False)}

    # DAS ABZUSICHERNDE EXPOSURE: alles, was im Depot liegt, OHNE die
    # Absicherungen selbst und OHNE Cash-Aequivalente. Ein Stablecoin faellt
    # nicht, und eine Absicherung sichert sich nicht selbst ab.
    exposure = 0.0
    ohne_preis = []
    for sym, h in bestaende.items():
        kurs = kurse_eur.get(sym)
        if kurs is None:
            if sym in hedge:
                ohne_preis.append(sym)
            continue
        if sym in hedge or sym in cash:
            continue
        exposure += float(h.quantity or 0.0) * float(kurs)

    # DIE ABDECKUNG IST LEVERAGE-ADJUSTIERT: 1 EUR in einem 3x-Short deckt
    # 3 EUR Long-Exposure. Summiert ueber ALLE gehaltenen Instrumente, nicht
    # nur ueber das gerade beurteilte.
    abdeckung = 0.0
    for sym, faktor in hedge.items():
        h = bestaende.get(sym)
        kurs = kurse_eur.get(sym)
        if not h or kurs is None:
            continue
        abdeckung += float(h.quantity or 0.0) * float(kurs) * float(faktor)

    if ohne_preis:
        # GENAU DER FUND VOM 18.07.: ein gehaltenes Hedge-Instrument ohne
        # Preis wuerde als "0 Abdeckung" durchgehen, und ein Aufbau daraufhin
        # koennte unbemerkt ueberhedgen. Hier wird es GESAGT.
        aus["unsicher"].append(
            f"Kein Preis fuer gehaltene Absicherung: {', '.join(sorted(ohne_preis))} "
            f"- die Abdeckung ist damit UNTERSCHAETZT")

    faktor = hedge.get(str(symbol).upper())
    aus.update({
        "exposure_eur": round(exposure, 2),
        "abdeckung_eur": round(abdeckung, 2),
        "abdeckung_anteil": (round(abdeckung / exposure, 4)
                             if exposure > 0 else None),
        "hebelfaktor": faktor,
        "referenz_index": _referenz_index(str(symbol).upper()),
        "ter_p_a": TER_P_A,
    })
    if faktor:
        # `benoetigter Einsatz = abzusicherndes Exposure / Hebelfaktor`
        offen = max(0.0, exposure - abdeckung)
        aus["noch_offen_eur"] = round(offen, 2)
        aus["einsatz_fuer_volle_deckung_eur"] = round(offen / float(faktor), 2)
    return aus


def saetze(e: dict) -> list[str]:
    """Die Lage als Aussagen - fuer den Prompt UND fuer die Mail.

    DIESELBEN SAETZE AN BEIDE. Das ist die Regel dieser Kette seit dem 12.08.:
    was das Modell liest, soll der Nutzer auch lesen koennen. Zwei Formulierungen
    derselben Zahl laufen auseinander."""
    if not e:
        return []
    from agent.signal_mail import eur, preis

    z = []
    if e.get("exposure_eur") is not None:
        z.append(f"Abzusicherndes Exposure: {eur(e['exposure_eur'], 0)} EUR "
                 f"(alles im Depot ausser Absicherungen und Cash).")
    if e.get("abdeckung_eur") is not None:
        anteil = e.get("abdeckung_anteil")
        z.append(f"Davon bereits abgesichert: {eur(e['abdeckung_eur'], 0)} EUR"
                 # KEIN pauschales replace - es erwischt den Satzpunkt.
                 # Bei ganzen Prozenten gibt es ohnehin kein Komma.
                 + (f" - das sind {100 * anteil:.0f} %."
                    if anteil is not None else "."))
    if e.get("hebelfaktor"):
        z.append(f"Dieses Instrument hebelt {e['hebelfaktor']:.0f}-fach"
                 + (f" auf den {e['referenz_index']}" if e.get("referenz_index")
                    else "")
                 + f"; 1 EUR darin deckt {e['hebelfaktor']:.0f} EUR Exposure.")
    if e.get("einsatz_fuer_volle_deckung_eur") is not None:
        z.append(f"Fuer volle Deckung der offenen "
                 f"{eur(e.get('noch_offen_eur', 0), 0)} EUR waeren "
                 f"{eur(e['einsatz_fuer_volle_deckung_eur'], 0)} EUR in diesem "
                 f"Instrument noetig.")
    if e.get("ter_p_a"):
        prozent = f"{100 * e['ter_p_a']:.1f}".replace(".", ",")
        z.append(f"Laufende Gebuehr etwa {prozent} % pro Jahr - eine "
                 f"Absicherung kostet auch dann, wenn nichts passiert.")
    for u in (e.get("unsicher") or []):
        z.append(f"ACHTUNG: {u}.")
    return z
