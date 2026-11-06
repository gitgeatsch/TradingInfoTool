# -*- coding: utf-8 -*-
"""KURSREAKTION SEIT EINER MELDUNG — ein FAKT, kein Urteil (G7 S7, Voranalyse_G7_S7_Anlage_05_11.md §4a/§4b; Nutzer 05.11.2026:
*„Ja, d + Wort-Arm“* und *„die Kursreaktion muss so angeführt sein, dass diese zum Urteil passt“*).

Form d:  das S7-LLM sieht KEINEN Kurs; dieser Fakt wird je (Meldung E<n>, Asset) NEBEN das S7-Ergebnis gelegt und geht erst an das
         finale LLM - als Zahl (``satz``).
Arm e:   das S7w-LLM sieht nur das WORT (gestiegen / gefallen / unverändert, ``wort``), das finale LLM die Zahl.

Gerechnet wird, was am Stichtag T (00:00 UTC) bekannt war:
  ab      = Stunde, in der die Meldung bekannt wurde (abgerundet); der Kurs ist ihr Schluss - frühestens T 00:00 (nie danach)
  reaktion = ln(P[T 00:00] / P[ab]),  gegen BTC: dasselbe minus BTC (BTC selbst: absolut)
  z       = reaktion / (σ · √Alter in Tagen),  σ = Std. der Tageslog-Erträge der 60 Tage VOR T (mind. 30)
  wort    = gestiegen (z > GRENZE) / gefallen (z < −GRENZE) / unverändert; ohne Kurs: 'kein Kurs'

⚠️ GRENZE 0,5 ist VORAB gesetzt (§4b): bei ±1,0 stünden 83 % auf 'unverändert' - das Wort trüge kaum etwas, der Arm wäre nicht fair.
⚠️ Liest nur ``mode=ro``. Rückspiel: die Kurs-Arbeitskopie ``data/_g7/kurse``; live derselbe Code auf den Betriebsdateien (Ü8).
"""
from __future__ import annotations

import math
import os
import sqlite3

import numpy as np
import pandas as pd

PROJ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KOPIE = os.path.join(PROJ, "data", "_g7", "kurse")
DATEIEN = ("stundenkurse.db", "stundenkurse_alle.db", "stundenkurse_eingestellt.db")   # Betrieb, Bewertung, eingestellte (G7 P-2)
GRENZE = 0.5
SIGMA_TAGE, SIGMA_MIN = 60, 30
WORTE = ("gestiegen", "gefallen", "unverändert", "kein Kurs", "zu frisch")   # zu frisch: Meldung < 1 h vor T (Gegenprüfung 8)


def _ro(pfad: str) -> sqlite3.Connection:
    return sqlite3.connect("file:%s?mode=ro" % pfad.replace("\\", "/"), uri=True)


class Kurse:
    """Stundenschlüsse je Symbol, einmal geladen. Index = Stundenbeginn (naiv, UTC); der Wert ist der Schluss dieser Stunde."""

    def __init__(self, ordner: str = KOPIE):
        self.ordner = ordner
        self._con = {f: _ro(os.path.join(ordner, f)) for f in DATEIEN if os.path.exists(os.path.join(ordner, f))}
        self._reihe: dict = {}

    def reihe(self, sym: str) -> tuple[pd.Series | None, str]:
        if sym not in self._reihe:
            self._reihe[sym] = (None, "")
            for f, c in self._con.items():
                k = c.execute("SELECT stunde, close FROM stundenkurse WHERE symbol=? ORDER BY stunde", (sym,)).fetchall()
                if k:
                    s = pd.Series([float(v) for _, v in k], index=pd.to_datetime([t for t, _ in k]))
                    s = s[~s.index.duplicated(keep="last")]
                    self._reihe[sym] = (s[s > 0], f.replace(".db", ""))
                    break
        return self._reihe[sym]


EINGESTELLT = os.path.join(KOPIE, "stundenkurse_eingestellt.db")
EINGESTELLT_VOR = "2026-10-01"           # nur Werte, deren Reihe davor ENDET (wirklich eingestellt) - lebende fehlen mit Absicht
_EING: dict = {}


def eingestellte_am(T, min_stunden: int | None = None, pfad: str = EINGESTELLT) -> set:
    """G7 P-2 (Gegenprüfung 05.11.2026): die im Rückspiel EINGESTELLTEN Werte, die am Stichtag T nach der Regel von
    ``ereignisse.assets_am`` in der S7-Menge gestanden hätten: >= ``min_stunden`` Stunden Kurs VOR dem Tag - und, weil eine beendete
    Reihe ihre Stunden behält, am Vortag noch GEHANDELT (sonst bliebe ein delisteter Wert für immer in der Menge). Ohne sie fielen ihre
    Ereignisse heraus - Auswahl mit Wissen nach T. Lebende Werte außerhalb der Stundendateien kommen NICHT dazu (andere
    Grundgesamtheit). Live gibt es die Datei nicht -> leere Menge."""
    if min_stunden is None:                                     # dieselbe Schwelle wie die Bewertungsreihe in ereignisse.assets_am
        from agent import ereignisse as EV
        min_stunden = EV.MIN_STUNDEN["stundenkurse_alle.db"]
    if pfad not in _EING:
        _EING[pfad] = None
        if os.path.exists(pfad):
            c = _ro(pfad)
            x = pd.read_sql("SELECT symbol, substr(stunde, 1, 10) tag, COUNT(*) n FROM stundenkurse WHERE symbol IN "
                            "(SELECT symbol FROM stundenkurse GROUP BY symbol HAVING MAX(stunde) < ?) GROUP BY 1, 2 ORDER BY 1, 2",
                            c, params=(EINGESTELLT_VOR,))
            c.close()
            x["kum"] = x.groupby("symbol").n.cumsum()
            _EING[pfad] = x
    x = _EING[pfad]
    if x is None or not len(x):
        return set()
    t = _T(T)
    vortag = (t - pd.Timedelta(days=1)).strftime("%Y-%m-%d")
    y = x[x.tag < t.strftime("%Y-%m-%d")].groupby("symbol").agg(kum=("kum", "last"), letzt=("tag", "last"))
    return set(y[(y.kum >= min_stunden) & (y.letzt >= vortag)].index)


def _T(tag_oder_zeit) -> pd.Timestamp:
    t = pd.Timestamp(tag_oder_zeit)
    return t.tz_convert("UTC").tz_localize(None) if t.tzinfo is not None else t


def _sigma(s: pd.Series, T: pd.Timestamp) -> float | None:
    d = s[s.index < T].resample("D").last().dropna()
    r = np.log(d).diff().dropna().iloc[-SIGMA_TAGE:]
    return float(r.std()) if len(r) >= SIGMA_MIN and r.std() > 0 else None


def reaktion(k: Kurse, asset: str, ab, T) -> dict:
    """-> dict(asset, ab, bis, stunden, pct, pct_btc, z, wort, bezug, quelle). Nur Kurse mit Stundenschluss <= T."""
    T = _T(T)
    ab = min(_T(ab).floor("h"), T - pd.Timedelta(hours=1))   # Schluss der Stunde 'ab' liegt bei ab + 1 h <= T
    letzt = T - pd.Timedelta(hours=1)                          # Schluss der Stunde 23:00 = Kurs um T 00:00
    # "ab" = Zeitpunkt des Ausgangskurses (Schluss der Stunde, in der die Meldung bekannt wurde), "bis" = T 00:00
    aus = {"asset": asset, "ab": (ab + pd.Timedelta(hours=1)).strftime("%Y-%m-%d %H:00"), "bis": T.strftime("%Y-%m-%d %H:00"),
           "stunden": round((T - ab).total_seconds() / 3600 - 1, 1), "pct": None, "pct_btc": None, "z": None, "wort": "kein Kurs",
           "bezug": "absolut" if asset == "BTC" else "gegen BTC", "quelle": ""}
    s, quelle = k.reihe(asset)
    if s is None:
        return aus
    pe, pT = s.get(ab), s.get(letzt)
    sig = _sigma(s, T)
    aus["quelle"] = quelle
    if not (pe and pT):
        return aus
    r = math.log(pT / pe)
    aus["pct"] = round(100 * (math.exp(r) - 1), 2)
    rel = r
    if asset != "BTC":
        b, _ = k.reihe("BTC")
        be, bT = (b.get(ab), b.get(letzt)) if b is not None else (None, None)
        if not (be and bT):
            return aus
        rel = r - math.log(bT / be)
        aus["pct_btc"] = round(100 * (math.exp(rel) - 1), 2)
    if sig is None:
        return aus
    if aus["stunden"] < 1:                                     # keine volle Stunde Zeit zu reagieren - kein "unverändert" behaupten
        aus["wort"] = "zu frisch"
        return aus
    alter = aus["stunden"] / 24
    z = rel / (sig * math.sqrt(alter))
    aus["z"] = round(z, 3)
    aus["wort"] = "gestiegen" if z > GRENZE else "gefallen" if z < -GRENZE else "unverändert"
    return aus


def _p(x) -> str:
    return ("%+.1f %%" % x).replace(".", ",").replace("-", "−")


def satz(r: dict) -> str:
    """Für das FINALE LLM (Zahl, Fakt) - je Asset und Meldung, damit es zum S7-Urteil derselben Meldung passt."""
    if r.get("pct") is None:
        return "%s · Kurs seit Meldung: kein Kurs · Fakt" % r["asset"]
    h = r["stunden"]
    alter = ("%.0f h" % h) if h < 48 else ("%.1f T" % (h / 24)).replace(".", ",")
    teil = ["%s · Kurs seit Meldung (%s, ab %s UTC): %s" % (r["asset"], alter, r["ab"], _p(r["pct"]))]
    if r["bezug"] == "gegen BTC":
        teil.append("gegen BTC %s" % (_p(r["pct_btc"]) if r["pct_btc"] is not None else "–"))
    if r["z"] is not None:
        teil.append("= %s übliche Schwankungen" % ("%+.1f" % r["z"]).replace(".", ",").replace("-", "−"))
    return ", ".join(teil) + " · Quelle %s · Fakt" % r["quelle"]
