# -*- coding: utf-8 -*-
"""Makro-Termine im Fenster eines REGEL0-Trades - als FAKT mit gemessenem Wert (O52, Schritt7 §23.53, E-112, 15.10.2026).

Nutzer 15.10.: *"CPI ... als Terminangabe relativ sinnfrei ohne Werte"*. Deshalb steht neben dem Termin, was er gemessen
bedeutet (p59_termin_vorpruefung, 127 Termine 2023-2026, Selbsttest im Band, Gegenprobe 11/11):

    BTC bewegt sich in den 2 Stunden ab dem Termin  CPI 1,83x · Arbeitsmarkt 1,49x · FOMC 2,28x  so stark wie sonst zur selben
    Uhrzeit (p < 0,001), ueber 24 Stunden nur 1,10x. Fuer REGEL0-Trades mit Termin im Fenster ist KEIN Unterschied belegt
    (blind unter etwa 10 Pp).

⚠️ KEIN GATE, KEIN GEWICHT. Die Zeile sperrt nichts und aendert keinen Hebel - der Termin ist fuer den 24-h-Trade nicht belegt.
Die alte Fassung (`anlass_kalender`) nannte einen Termin in fuenf Tagen "ungünstig fuer einen Einstieg" - das war nie gemessen
und steht hier bewusst NICHT.

⚠️ DREI ZUSTAENDE: Termin im Fenster · kein Termin · NICHT ABGEFRAGT (FRED nicht erreicht oder kein Schluessel). Der dritte darf
nie wie der zweite aussehen.

Quellen: CPI und Arbeitsmarkt aus FRED (`release/dates` 10/50, 08:30 New York), FOMC aus der festen Fed-Liste
(`agent.cycles.FOMC_MEETING_DATES`, Erklaerung 14:00 New York). Ein FRED-Abruf je Tag und Art, Fehlschlaege werden mitgemerkt.
"""
from __future__ import annotations

import logging
import os
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

logger = logging.getLogger(__name__)

NY = ZoneInfo("America/New_York")
ORT = ZoneInfo("Europe/Vienna")
FRED = {"cpi": 10, "nfp": 50}
NAME = {"cpi": "US-Inflation (CPI)", "nfp": "US-Arbeitsmarkt", "fomc": "US-Zinsentscheid (FOMC)"}
UHR = {"cpi": "08:30", "nfp": "08:30", "fomc": "14:00"}
# gemessen p59 (Schritt7 §23.53) - mittlere |Rendite| BTC ab Termin gegen dieselbe Uhrzeit an Werktagen ohne Termin
FAKTOR_2H = {"cpi": 1.83, "nfp": 1.49, "fomc": 2.28}
FAKTOR_24H = 1.10
MESSLAGE = "gemessen 2023-2026 an 127 Terminen (Schritt7 §23.53); für REGEL0-Trades mit Termin im Fenster kein Unterschied belegt"
_SPEICHER: dict = {}


def _fred_naechster(art: str, heute: date, fred_key: str):
    """(Datum oder None, abgefragt) - einmal je Tag und Art, auch Fehlschlaege gemerkt."""
    k = (art, heute.isoformat())
    if k not in _SPEICHER:
        try:
            from api.macro import get_next_fred_release
            r = get_next_fred_release(FRED[art], art, fred_key, today=heute.isoformat())
            _SPEICHER[k] = ((date.fromisoformat(str(r.date)[:10]) if r else None), True)
        except Exception as exc:                                   # noqa: BLE001
            logger.info("Termin %s aus FRED nicht lesbar: %s", art, exc)
            _SPEICHER[k] = (None, False)
        if len(_SPEICHER) > 32:
            for x in list(_SPEICHER)[:16]:
                _SPEICHER.pop(x, None)
    return _SPEICHER[k]


def _zeitpunkt(tag: date, art: str) -> datetime:
    return datetime.fromisoformat("%s %s" % (tag.isoformat(), UHR[art])).replace(tzinfo=NY).astimezone(timezone.utc)


def termine(von: datetime, bis: datetime, fred_key: str | None = None) -> dict:
    """Termine im Zeitraum [von, bis) (UTC-bewusst). -> {"termine": [{art, utc}], "nicht_abgefragt": [art], "fomc_bis": date}."""
    if fred_key is None:
        fred_key = os.environ.get("FRED_API_KEY") or ""
    aus, fehlt = [], []
    for art in FRED:
        if not fred_key:
            fehlt.append(art)
            continue
        tag, ok = _fred_naechster(art, von.astimezone(NY).date(), fred_key)
        if not ok:
            fehlt.append(art)
        elif tag is not None:
            t = _zeitpunkt(tag, art)
            if von <= t < bis:
                aus.append({"art": art, "utc": t})
    from agent.cycles import FOMC_MEETING_DATES, fomc_liste_reicht_bis
    for _start, ende in FOMC_MEETING_DATES:
        t = _zeitpunkt(ende, "fomc")
        if von <= t < bis:
            aus.append({"art": "fomc", "utc": t})
    if bis.date() > fomc_liste_reicht_bis():
        fehlt.append("fomc")
    aus.sort(key=lambda x: x["utc"])
    return {"termine": aus, "nicht_abgefragt": fehlt, "fomc_bis": fomc_liste_reicht_bis()}


def _komma(x: float) -> str:
    return ("%.1f" % x).replace(".", ",")


def _abstand(std: float) -> str:
    a = abs(std)
    return ("%d h" % round(a)) if a >= 1 else ("%d min" % round(a * 60))


def zeile(einstieg: datetime, bis: datetime, fred_key: str | None = None) -> str:
    """Eine Zeile fuer die Mail: was im Trade-Fenster ansteht und was das gemessen heisst. Gefragt wird ab 2 h VOR dem Einstieg -
    der gemessene Ausschlag dauert 2 h, ein Termin kurz davor laeuft also noch in den Trade hinein."""
    d = termine(einstieg - timedelta(hours=2), bis, fred_key)
    teile = []
    for e in d["termine"]:
        std = (e["utc"] - einstieg).total_seconds() / 3600
        teile.append("%s %s Uhr (%s %s dem Einstieg) – BTC bewegt sich in den 2 h danach im Mittel %s× so stark wie sonst"
                     % (NAME[e["art"]], e["utc"].astimezone(ORT).strftime("%d.%m. %H:%M"), _abstand(std),
                        "nach" if std >= 0 else "vor", _komma(FAKTOR_2H[e["art"]])))
    if teile:
        txt = " · ".join(teile) + "; über 24 h nur %s× – Einstieg vor oder nach dem Termin ist deine Wahl" % _komma(FAKTOR_24H)
    else:
        txt = "kein US-Inflations-, Arbeitsmarkt- oder Zinstermin im 24-h-Fenster dieses Trades (ab 2 h vor dem Einstieg)"
    if d["nicht_abgefragt"]:
        txt += " · ⚠ NICHT ABGEFRAGT (kein Nein): " + ", ".join(NAME[a] for a in d["nicht_abgefragt"])
    return txt


def mailteil(r: dict, fred_key: str | None = None) -> dict:
    """Fuer die REGEL0-Signalmail (Muster ``ankuendigung``/``verwaesserung``): {'ein': Zeile, 'technik': [(k, v)]}.
    Fenster = Einstieg (Schluss der Einstiegsstunde) bis Ausstieg - wie in ``regel0_mail._signal_teile``."""
    from agent.regel0_mail import _t
    von = _t(r["einstieg"]) + timedelta(hours=1)
    bis = _t(r["ausstieg"]) + timedelta(hours=1)
    return {"ein": zeile(von, bis, fred_key),
            "technik": [("Termin", "Fakt, nicht Teil der Regel (O52) · %s · FOMC-Liste bis %s"
                         % (MESSLAGE, __import__("agent.cycles", fromlist=["x"]).fomc_liste_reicht_bis().strftime("%d.%m.%Y")))]}
