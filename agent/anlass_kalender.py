# -*- coding: utf-8 -*-
"""Was steht an? (Umbauplan 93 D, 20.08.2026)

⚠️ DAS DECKELPROBLEM WIRD DURCH DIE BAUFORM GELOEST, NICHT DURCH EINE REGEL.

Der Nutzer hat diese Stufe am 19.08. als "heikel und schwierig" bezeichnet und
das Deckelproblem benannt. Zu Recht: ein Anlass, der zur BEDINGUNG wird, ist
ein Gate - und ein lueckenhaftes Gate sperrt zufaellig. Genau daran ist der
Deadloop entstanden.

Deshalb urteilt dieses Modul NICHT und sperrt NICHTS. Es nennt Termine mit
Datum und Quelle, und daneben, was das fuer den Einstieg bedeutet. Die
Entscheidung bleibt beim Leser.

⚠️ UND DIE ZWEITE GEFAHR IST DIE LUECKE, NICHT DER FEHLER.

Ein Kalender mit Luecken ist gefaehrlicher als keiner: fehlt ein Anlass, sieht
die Lage RUHIG aus. Deshalb steht in jeder Mail ausdruecklich, welche Quellen
gefragt wurden und welche Ereignisarten NICHT abgedeckt sind. Wer die Zeile
liest, weiss, was er nicht weiss.

DREI QUELLEN, ALLE SCHON IM HAUS:

    FOMC        agent/cycles.FOMC_MEETING_DATES_2026 - statische Liste von
                federalreserve.gov. ⚠️ NUR 2026: ab Januar 2027 liefert sie
                nichts, und das sieht aus wie "keine Sitzung".
    CPI         api/macro.get_next_fred_release - der naechste Termin aus
                FRED. Ohne Schluessel: NICHT ABGEFRAGT, nicht "kein Termin".
    Verfall     Deribit-Optionsverfall mit offenen Kontrakten. NUR BTC und
                ETH - fuer alle anderen Coins gibt es dort nichts.

WAS NICHT ABGEDECKT IST, und zwar wissentlich: Token-Freigaben (Unlocks),
Boersenzugaenge, Netzwerk-Umstellungen, Zwischenfaelle. Fuer keines davon gibt
es eine freie, vollstaendige Quelle - das war der Grund, warum diese Stufe
zurueckgestellt wurde, und er gilt weiter.
"""
from __future__ import annotations

import logging
from datetime import date, datetime, timezone

logger = logging.getLogger(__name__)

DERIBIT_ZUSAMMENFASSUNG = ("https://www.deribit.com/api/v2/public/"
                           "get_book_summary_by_currency")

# Wie weit nach vorn geschaut wird. Zwanzig Handelstage sind das Fenster, in
# dem dieses System plant (Trichter, Haltedauer) - weiter zu schauen hiesse,
# Termine zu nennen, die den Trade nicht mehr betreffen.
VORSCHAU_TAGE = 30

# Ab wann ist ein Verfalltermin ein Ereignis und nicht nur ein Datum? Der
# groesste der naechsten Termine, und nur wenn er die anderen deutlich
# uebersteigt - sonst stuende an jedem Freitag ein "Grossereignis".
VERFALL_FAKTOR = 2.0

# Die Quellen, die dieses Modul kennt. Sie stehen in der Mail, damit die
# Luecke sichtbar ist.
QUELLEN = ("FOMC-Sitzungen", "CPI-Veroeffentlichung",
           "Optionsverfall (nur BTC/ETH)")
NICHT_ABGEDECKT = ("Token-Freigaben", "Boersenzugaenge",
                   "Netzwerk-Umstellungen", "Zwischenfaelle")


def _fomc(heute: date) -> list[dict]:
    try:
        from agent.cycles import get_upcoming_fomc_meetings
        aus = []
        for e in get_upcoming_fomc_meetings(heute, within_days=VORSCHAU_TAGE):
            tage = getattr(e, "days_until", None)
            aus.append({"art": "FOMC", "name": getattr(e, "name", "FOMC"),
                        "tage": int(tage) if tage is not None else None,
                        "quelle": "federalreserve.gov (feste Liste)"})
        return aus
    except Exception as exc:                                 # noqa: BLE001
        logger.info("FOMC-Termine nicht lesbar: %s", exc)
        return []


def _cpi(heute: date, fred_key: str | None) -> tuple[list, bool]:
    """(Termine, abgefragt). ⚠️ Ohne Schluessel wird NICHT abgefragt - und das
    ist etwas anderes als "kein Termin"."""
    if not fred_key:
        return [], False
    try:
        from api.macro import get_next_fred_release
        r = get_next_fred_release(10, "cpi_headline", fred_key,
                                  today=heute.isoformat())
        if not r:
            return [], True
        tag = getattr(r, "date", None) or getattr(r, "datum", None)
        tage = (date.fromisoformat(str(tag)[:10]) - heute).days if tag else None
        if tage is None or tage > VORSCHAU_TAGE:
            return [], True
        return [{"art": "CPI", "name": "CPI-Veroeffentlichung",
                 "tage": tage, "quelle": "FRED"}], True
    except Exception as exc:                                 # noqa: BLE001
        logger.info("CPI-Termin nicht lesbar: %s", exc)
        return [], False


def _verfall(heute: date, symbol: str, sitzung=None) -> tuple[list, str]:
    """Optionsverfall. NUR BTC und ETH - Deribit fuehrt nichts anderes.

    ⚠️ DREI ZUSTAENDE, AUCH HIER (Korrektur beim ersten Probelauf, 20.08.):
    fuer AIOZ meldete die erste Fassung "NICHT ERREICHT". Es gibt dort aber
    keinen Optionsmarkt - das ist "nicht zutreffend", nicht "nicht erfahren".
    Wer beides zusammenwirft, laesst eine Mail nach Ausfall aussehen, wo
    schlicht nichts zu holen ist."""
    waehrung = str(symbol).upper()
    if waehrung not in ("BTC", "ETH"):
        return [], "entfaellt"
    try:
        import requests
        s = sitzung or requests.Session()
        r = s.get(DERIBIT_ZUSAMMENFASSUNG,
                  params={"currency": waehrung, "kind": "option"}, timeout=30)
        r.raise_for_status()
        offen: dict[str, float] = {}
        for x in r.json().get("result") or []:
            teile = str(x.get("instrument_name", "")).split("-")
            if len(teile) < 2:
                continue
            offen[teile[1]] = offen.get(teile[1], 0.0) + float(
                x.get("open_interest") or 0)
        kommend = []
        for schluessel, menge in offen.items():
            try:
                tag = datetime.strptime(schluessel, "%d%b%y").date()
            except ValueError:
                continue
            tage = (tag - heute).days
            if 0 <= tage <= VORSCHAU_TAGE:
                kommend.append((tage, menge))
        if not kommend:
            return [], "ok"
        kommend.sort()
        mengen = sorted(m for _t, m in kommend)
        mitte = mengen[len(mengen) // 2] or 1.0
        gross = [(t, m) for t, m in kommend if m >= VERFALL_FAKTOR * mitte]
        # ⚠️ NUR DIE ZAHL UMSTELLEN, nicht den ganzen Satz. Die erste
        # Fassung rief .replace(",", ".") auf dem fertigen Text auf und
        # machte aus "Optionsverfall BTC, 68.668" ein "BTC. 68.668".
        from agent.schreibweise import de
        return ([{"art": "Verfall",
                  "name": f"Optionsverfall {waehrung}, {de(m, 0)} "
                          f"offene Kontrakte",
                  "tage": t, "quelle": "Deribit"} for t, m in gross[:2]],
                "ok")
    except Exception as exc:                                 # noqa: BLE001
        logger.info("Verfalltermine nicht lesbar: %s", exc)
        return [], "fehler"


def termine(symbol: str, assetklasse: str = "", fred_key: str | None = None,
            heute: date | None = None, sitzung=None) -> dict:
    """Alle bekannten Termine - UND welche Quellen erreicht wurden.

    ⚠️ DREI ZUSTAENDE, wie ueberall in diesem Projekt: ein Termin, kein
    Termin, oder NICHT ABGEFRAGT. Der dritte darf nie wie der zweite
    aussehen."""
    tag = heute or datetime.now(timezone.utc).date()
    if fred_key is None:
        # Wie ueberall im Projekt aus der Umgebung, nicht aus einem Argument
        # mit stiller Vorgabe - sonst faellt die Quelle in der Produktion aus,
        # ohne dass es jemandem auffaellt.
        import os
        fred_key = os.environ.get("FRED_API_KEY") or ""
    liste = _fomc(tag)
    erreicht = {"FOMC-Sitzungen": "ok"}
    cpi, ok = _cpi(tag, fred_key)
    liste += cpi
    erreicht["CPI-Veroeffentlichung"] = "ok" if ok else "fehler"
    verfall, zustand = _verfall(tag, symbol, sitzung)
    liste += verfall
    erreicht["Optionsverfall (nur BTC/ETH)"] = zustand
    liste.sort(key=lambda x: (x["tage"] if x["tage"] is not None else 999))
    return {"termine": liste, "erreicht": erreicht}


def saetze(symbol: str, assetklasse: str = "", fred_key: str | None = None,
           heute: date | None = None, sitzung=None) -> list[str]:
    """Die Zeilen fuer die Mail. KEIN URTEIL, KEIN GATE.

    Sie sperren nichts und empfehlen nichts - sie sagen, was ansteht und was
    das fuer einen Einstieg heisst."""
    from agent.schreibweise import de

    d = termine(symbol, assetklasse, fred_key, heute, sitzung)
    # "fehler" heisst NICHT ERFAHREN, "entfaellt" heisst: gibt es hier nicht.
    fehlend = [q for q, z in d["erreicht"].items() if z == "fehler"]
    entfaellt = [q for q, z in d["erreicht"].items() if z == "entfaellt"]
    aus = ["Bekannte Termine in den naechsten "
           + de(VORSCHAU_TAGE, 0) + " Tagen (Anzeige, kein Urteil):"]
    if d["termine"]:
        for e in d["termine"]:
            wann = ("heute" if e["tage"] == 0 else
                    f"in {de(e['tage'], 0)} Tagen")
            aus.append(f"   {wann}: {e['name']}  [{e['quelle']}]")
        # ⚠️ WAS IST DARAN GUT ODER SCHLECHT (Nutzervorgabe 20.08.2026)?
        naechster = d["termine"][0]
        if naechster["tage"] is not None and naechster["tage"] <= 5:
            aus.append(
                "⚠️ UNGUENSTIG FUER EINEN EINSTIEG JETZT: der naechste Termin "
                "liegt innerhalb der ueblichen Fuenf-Tage-Bewegung. Was dann "
                "passiert, entscheidet die Nachricht - nicht der Aufbau.")
        else:
            aus.append(
                "   GUENSTIG: kein Termin in den naechsten fuenf Tagen - die "
                "naechste Bewegung entscheidet sich am Aufbau, nicht an einer "
                "Veroeffentlichung.")
    else:
        aus.append("   Keiner der abgefragten Quellen bekannt.")
    # ⚠️ DIE LUECKE GEHOERT IN JEDE MAIL. Ein Kalender mit Luecken ist
    # gefaehrlicher als keiner - fehlt ein Anlass, sieht die Lage ruhig aus.
    aus.append("   Gefragt wurde: " + ", ".join(QUELLEN)
               + (". Fuer diesen Wert nicht vorhanden: " + ", ".join(entfaellt)
                  if entfaellt else "")
               + (". NICHT ERREICHT (Ausfall, kein Nein): "
                  + ", ".join(fehlend) if fehlend else "")
               + ".")
    aus.append("⚠️ NICHT ABGEDECKT: " + ", ".join(NICHT_ABGEDECKT)
               + ". Fuer diese gibt es keine freie, vollstaendige Quelle - "
                 "was hier nicht steht, kann trotzdem anstehen.")
    return aus
