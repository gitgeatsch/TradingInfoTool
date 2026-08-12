# -*- coding: utf-8 -*-
"""Die EINE Stelle, an der die Eingabe fuer die Rollen entsteht.

WARUM ES DIESE DATEI GIBT (12.08.2026). Bis hierher baute jedes Messskript die
Eingabe selbst zusammen - `pruefe_rollenkette`, `messe_degradierung`,
`messe_faktorzahl`, `messe_dritter_faktor`, `messe_abgleich_alt_neu`,
`messe_marktphasen`. Sechs Stellen mit demselben Aufbau.

Das hatte zwei Folgen, beide belegt:

  * Die Finanzierungsrate war gebaut (Faktenmappe 12.9) und liess sich trotzdem
    nicht "anschliessen" - es gab keinen Ort dafuer. Sie haette in sechs
    Skripte einzeln eingesetzt werden muessen.
  * Zwei Skripte riefen die Marktbreite mit `mit_bezug=False` auf, zwei mit
    `True`. Der Kalibrierungssatz, der die Zuspitzung eindaemmen soll, fehlte
    also in der Haelfte aller Messungen - unbemerkt (Arbeitsstand 7.14).

Wer die Eingabe aendern will, aendert sie hier. Wer sie an sechs Stellen
aendert, aendert sie an fuenf.

WAS HIER NICHT HINEINGEHOERT: Netzwerkaufrufe im Zweifel. `finanzierung` wird
als fertige Zusammenfassung uebergeben, nicht hier geholt - sonst haengt eine
Beschreibung an einer Boersen-API und faellt mit ihr aus. Der Aufrufer holt und
entscheidet, was bei einem Ausfall geschieht.
"""
from __future__ import annotations

import numpy as np


def baue_lagebild_eingabe(reihen: dict, datum: str) -> dict:
    """Eingabe fuer das Lagebild. MIT historischem Bezug, immer.

    `mit_bezug=True` ist hier nicht optional: der Satz "in X % der Faelle war
    dieser Anteil niedriger" ist die einzige Kalibrierung, die das Modell vor
    einer Zuspitzung schuetzt. Zwei Messungen liefen ohne ihn, und in genau
    einer davon wurde aus einem knapp durchschnittlichen Wert eine "extreme
    Schieflage"."""
    from agent.marktbreite import beschreibe_marktbreite
    return {"marktlage": beschreibe_marktbreite(reihen, datum, mit_bezug=True)}


def baue_befund_eingabe(*, symbol: str, reihe: list, index: int,
                        kurs_eur: float, atr: float,
                        menge: float | None = None,
                        einstand_eur: float | None = None,
                        finanzierung: dict | None = None,
                        lagebild: dict | None = None) -> dict:
    """Eingabe fuer Befund und Entscheidung - alle Bloecke an einer Stelle."""
    from agent.lagebeschreibung import beschreibe_lage
    aus = {"asset": symbol,
           "stand": beschreibe_lage(symbol=symbol, reihe=reihe, index=index,
                                    kurs_eur=kurs_eur, atr=atr, menge=menge,
                                    einstand_eur=einstand_eur,
                                    finanzierung=finanzierung)}
    if lagebild:
        aus["marktlage_beurteilung"] = {"traegt": lagebild.get("traegt"),
                                        "lage": lagebild.get("lage")}
    return aus


def hole_finanzierung(symbol: str, datum: str, session=None,
                      zwischenspeicher: dict | None = None) -> dict | None:
    """Finanzierungsrate zum ANKERTAG, kausal abgeschnitten.

    FAIL-SOFT UND STILL: Faellt die Boerse aus oder kennt sie das Symbol nicht,
    kommt None zurueck und der Block entfaellt. Das ist richtig so - ein Satz
    "keine Finanzierungsdaten" waere fuer alle Aktien, ETF und Rohstoffe
    identisch und damit ein konstantes Feld (B10).

    ABER: der Aufrufer muss zaehlen, wie oft None kam. Ein stiller Ausfall, den
    niemand zaehlt, ist genau das U-Boot, das dieses Projekt mehrfach bezahlt
    hat. `zwischenspeicher` dient zugleich der Taktung - dieselbe Kombination
    wird nur einmal geholt."""
    from datetime import datetime, timezone
    schluessel = (symbol, datum[:10])
    if zwischenspeicher is not None and schluessel in zwischenspeicher:
        return zwischenspeicher[schluessel]
    ergebnis = None
    try:
        from api.derivatives import get_funding_history, summarize_funding
        ende = int(datetime.fromisoformat(datum[:10]).replace(
            tzinfo=timezone.utc).timestamp() * 1000)
        ergebnis = summarize_funding(
            get_funding_history(f"{symbol}USDT", 100, session, ende))
    except Exception:                                            # noqa: BLE001
        ergebnis = None
    if zwischenspeicher is not None:
        zwischenspeicher[schluessel] = ergebnis
    return ergebnis


def pruefe_lagebild(ausgabe: dict, eingabe: dict) -> dict:
    """Der Waechter auf der NAHT zwischen den Rollen (R-T8).

    Die bestehenden Waechter pruefen EINGABEN. Die Ausgabe des Lagebilds ist die
    Eingabe der Entscheidung - und wurde nie geprueft. Belegt am 11.08.: aus
    "8 % ueber der 50-Tage-Linie, in 46 % der Faelle war dieser Anteil
    niedriger" wurde "extreme Schieflage mit starkem Abwaertsdruck", und dieser
    Satz erreichte die Entscheidung als Beleg mit Gewicht HOCH.

    VERMERKEN, NICHT ABLEHNEN. Eine Ablehnung erzeugt eine Wiederholung und am
    Ende kein Signal - derselbe Deadloop an anderer Stelle (R-A5). Und den Text
    umzuschreiben waere schlimmer: dann stuende dort ein Satz, den niemand
    verantwortet. Der Verstoss wird gezaehlt und sichtbar gemacht; was daraus
    folgt, ist eine Entscheidung des Nutzers, keine des Waechters."""
    from agent.waechter_zuspitzung import pruefe
    text = " ".join(str(v) for v in (ausgabe.get("lage"), *(ausgabe.get("belege") or [])))
    ergebnis = pruefe(text, eingabe.get("marktlage") or [])
    if ergebnis.get("verstoss"):
        ausgabe["_zuspitzung"] = (
            f"unbelegte Gradbehauptung {ergebnis['hart']} - {ergebnis['grund']}")
    return ergebnis


# --- Geteilte Helfer (12.08.2026) -------------------------------------------
#
# WARUM SIE HIERHER WANDERN. Bis heute standen `_bestand`, `_kurs_eur`, `_atr`,
# `frage` und `_client` in `pruefe_rollenkette.py` - einem SKRIPT. Sieben
# Messskripte importierten sie von dort und bogen dessen Modulkonstante `DB`
# um. Ein Skript als Bibliothek zu benutzen funktioniert, bis jemand es
# ausfuehrt oder umbenennt.
#
# Sie liegen jetzt hier, wo auch die Eingabe entsteht. `pruefe_rollenkette`
# importiert sie zurueck, damit bestehende Aufrufe unveraendert bleiben.

DB = "data/tradinginfotool.db"


def bestand(symbol: str, db: str | None = None):
    """Menge und wirksamer Einstand. NAEHERUNG bei historischen Faellen: der
    heutige Bestand, nicht der von damals - Bestandshistorie fuehren wir nicht.

    Liest BEIDE Einstandsspalten. Die manuelle geht vor - dieselbe Vorrangregel
    wie `database/models.py::effective_avg_buy_price_eur`. Ohne sie meldete die
    Kette 14 von 28 gehaltenen Positionen als "nicht im Bestand"."""
    import sqlite3
    c = sqlite3.connect(f"file:{db or DB}?mode=ro", uri=True)
    r = c.execute("select quantity, avg_buy_price_eur, avg_buy_price_manual_eur "
                  "from holdings where symbol=?", (symbol,)).fetchone()
    if not r:
        return (None, None)
    menge, berechnet, manuell = r
    return (menge, manuell if manuell is not None else berechnet)


def kurs_eur(symbol: str, reihe, index: int, db: str | None = None):
    """EUR-Kurs am Ankertag.

    Liegt die REIHE bereits in EUR, wird NICHT umgerechnet - sonst waere es
    eine stille Doppelumrechnung um den Wechselkurs. Und `price_cache` ist eine
    Historie, kein Cache: ohne `order by` kaeme die aelteste Zeile."""
    import sqlite3
    from backtest_llm1_historisch import waehrung_je_symbol
    pfad = db or DB
    if waehrung_je_symbol(pfad).get(symbol) == "EUR":
        return float(reihe[index].close)
    c = sqlite3.connect(f"file:{pfad}?mode=ro", uri=True)
    r = c.execute("select price_usd, price_eur from price_cache where symbol=? "
                  "order by fetched_at desc limit 1", (symbol,)).fetchone()
    if not r or not r[0] or not r[1]:
        return float(reihe[index].close)
    return float(reihe[index].close) * (float(r[1]) / float(r[0]))


def atr_bis(reihe, index: int) -> float:
    """ATR aus `reihe[:index+1]` - streng kausal."""
    from indicators.calculations import atr_wilder, latest_value
    h = np.array([k.high for k in reihe[:index + 1]], dtype=float)
    l = np.array([k.low for k in reihe[:index + 1]], dtype=float)
    c = np.array([k.close for k in reihe[:index + 1]], dtype=float)
    return float(latest_value(atr_wilder(h, l, c)) or 0.0)


def baue_fall(*, symbol: str, reihe: list, index: int, reihen: dict,
              lagebild: dict | None = None, db: str | None = None,
              session=None, finanz_zwischenspeicher: dict | None = None,
              mit_finanzierung: bool = True) -> tuple[dict, dict]:
    """Beide Eingaben fuer EINEN Fall - die einzige Stelle, die das tut.

    Rueckgabe: (lagebild_eingabe, befund_eingabe). Wer das Lagebild schon hat,
    uebergibt es als `lagebild` und ignoriert den ersten Rueckgabewert.

    `mit_finanzierung=False` ist der Vergleichsarm fuer gepaarte Messungen -
    er darf nicht heimlich abweichen, deshalb steht er hier und nicht im
    Aufrufer."""
    datum = reihe[index].date
    menge, einstand = bestand(symbol, db)
    fin = (hole_finanzierung(symbol, datum, session, finanz_zwischenspeicher)
           if mit_finanzierung else None)
    return (
        baue_lagebild_eingabe(reihen, datum),
        baue_befund_eingabe(symbol=symbol, reihe=reihe, index=index,
                            kurs_eur=kurs_eur(symbol, reihe, index, db) or 0.0,
                            atr=atr_bis(reihe, index), menge=menge,
                            einstand_eur=einstand, finanzierung=fin,
                            lagebild=lagebild),
    )
