# -*- coding: utf-8 -*-
"""Makro-Lage als FAKT fuer Statusseite und Handlungsmails (O54, Schritt7 §23.57, 15.10.2026).

Nutzer 15.10.: *"Makro-Regime ist grundsaetzlich fuer alle Assets relevant und sollte eine Rolle spielen"* · *"Ja zu O54 auf der
Statusseite als Bereich oben"*. Die Rolle ist die eines GEWICHTS, das der Nutzer selbst setzt (Vorgabe 01.10.: *"das muss ich dann
in den laufenden Trades selbst bewerten"*) - gemessen ist weder die Richtung (§51.7, Spot) noch die Risiko-Bremse (O53, §23.56):

    Richtung   Gesamt lang/kurz: nicht entscheidbar (13 J BTC ~ drei Zyklen)
    Risiko     Gesamt kurz Gegenwind -> tiefster Stand in 30 T im Mittel rund 7 % tiefer als bei Rueckenwind (p 0,010, Bonferroni
               0,00625 verfehlt, ab 2024 nicht sichtbar); die ATR (Hebelstufe REGEL0) traegt den anhaltenden Teil schon mit

⚠️ KEIN GATE, KEIN GEWICHT IM SYSTEM. Die Zeile sperrt nichts und aendert keinen Hebel.

⚠️ GLEICHE RECHNUNG WIE DIE MESSUNG (R-R11): Kanaele K1-K9 lang/kurz und Gesamt wie ``Basisinfos/Spot_Voranalyse_04_10/
p51_vorpruefung.kanaele/score/scores`` (Verzug je Reihe, Drittel im rollierenden 5-J-Fenster). Nur die QUELLE ist eine andere:
FRED-API mit Schluessel (am NB nachgewiesen, Diagnose 15.10. 11:40) statt fredgraph.csv. Bitgleichheit auf denselben Rohreihen
prueft ``o54_pruefstand.py``.

Ablage ``data/makro_lage.json`` (nicht versioniert). Ein Fehlschlag behaelt den alten Stand MIT Vermerk - nie still.
"""
from __future__ import annotations

import json
import logging
import os
import time
from datetime import date, datetime, timedelta, timezone

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

ABLAGE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "makro_lage.json")   # unabhaengig vom Arbeitsordner
FENSTER, MINDEST = 1826, 1095
VERALTET_TAGE = 3
REIHEN = {"M2SL": 35, "WALCL": 2, "WTREGEN": 2, "RRPONTSYD": 1, "DFII10": 1, "DGS2": 1, "T10Y2Y": 1, "BAA10Y": 1, "NFCI": 5,
          "DTWEXBGS": 1, "VIXCLS": 1}                       # Reihe: Verzug in Tagen (wie p51_vorpruefung.kanaele)
NAME = {"K1 Geldmenge": "Geldmenge M2", "K2 Netto-Liquiditaet": "Netto-Liquidität Fed", "K3 Realzins": "Realzins",
        "K4 Zinspfad 2J": "Zinspfad 2 J", "K5 Kurve": "Zinskurve", "K6 Kredit BAA": "Kreditaufschlag", "K7 NFCI": "Finanzierungsbedingungen",
        "K8 Dollar": "Dollar", "K9 VIX": "Aktien-Angst (VIX)"}
WORT = {1.0: "Rückenwind", 0.0: "neutral", -1.0: "Gegenwind"}
MESSUNG = {
    "lang": "Richtung nicht entscheidbar (Messung 14.10., 13 J BTC)",
    "kurz_gegen": "in kurzen Gegenwind-Phasen fiel BTC binnen 30 T im Mittel rund 7 % tiefer als bei Rückenwind (Tendenz, nicht belegt)",
    "kurz_rueck": "kurzer Rückenwind: BTC lief in 90 T im Mittel besser als bei Gegenwind (Tendenz, nicht belegt)",
    "kurz_neutral": "kurz ohne klare Richtung",
    "atr": "die Hebelstufe berücksichtigt die Schwankung schon über die ATR",
}


# ══ Rohreihen ═════════════════════════════════════════════════════════════════════════════════════════════════════════════
def hole_reihe(series_id: str, fred_key: str, start: str, http=None) -> pd.Series:
    """Eine FRED-Reihe ab ``start`` (Beobachtungsdatum), Datum um den Verzug verschoben - wie p51_vorpruefung.fred."""
    import requests
    s = http or requests
    r = s.get("https://api.stlouisfed.org/fred/series/observations",
              params={"series_id": series_id, "api_key": fred_key, "file_type": "json", "observation_start": start}, timeout=60)
    r.raise_for_status()
    obs = [(o["date"], o["value"]) for o in r.json().get("observations", []) if o.get("value") not in (".", "", None)]
    if not obs:
        raise ValueError("FRED %s: keine Beobachtungen" % series_id)
    d = pd.Series([float(v) for _, v in obs], index=pd.to_datetime([t for t, _ in obs]) + pd.Timedelta(days=REIHEN[series_id]))
    return d.sort_index().rename(series_id)


def hole_alle(fred_key: str, heute: date | None = None, http=None, pause: float = 0.3) -> dict:
    """Alle Rohreihen ab 13 Jahren vor heute. ⚠️ ZWEI 5-J-FENSTER HINTEREINANDER (Pruefstand M2, 15.10.): das Gesamt-Drittel rangt die
    Summe der Kanal-Scores im 5-J-Fenster, und jeder Kanal-Score braucht selbst 5 J (dazu 1 J Abstand fuer 'lang' und 1 J fuer M2).
    Mit acht Jahren war das Gesamt-Fenster abgeschnitten - und stimmte nur an 16 von 23 Stichtagen mit der Messung."""
    heute = heute or date.today()
    start = (heute - timedelta(days=13 * 365)).isoformat()
    aus = {}
    for i, sid in enumerate(REIHEN):
        if i and pause:
            time.sleep(pause)
        aus[sid] = hole_reihe(sid, fred_key, start, http)
    return aus


# ══ Rechnung (wie p51_vorpruefung) ═══════════════════════════════════════════════════════════════════════════════════════
def _taeglich(r: pd.Series, idx: pd.DatetimeIndex) -> pd.Series:
    return r.sort_index().reindex(r.index.union(idx)).ffill().reindex(idx)


def _score(x: pd.Series, vz: int) -> pd.Series:
    p = x.rolling(FENSTER, min_periods=MINDEST).rank(pct=True)
    s = pd.Series(np.where(p > 2 / 3, vz, np.where(p < 1 / 3, -vz, 0)).astype(float), index=x.index)
    s[p.isna()] = np.nan
    return s


def kanaele(roh: dict, idx: pd.DatetimeIndex):
    """-> (K, k5_kurz) in der Form von p51_vorpruefung.kanaele: Name -> (lang, vz_lang, kurz, vz_kurz)."""
    m2 = roh["M2SL"]
    m2y = _taeglich(m2 / m2.shift(12) - 1, idx)
    w = pd.concat([roh["WALCL"], roh["WTREGEN"], roh["RRPONTSYD"].resample("W-WED").last()], axis=1, sort=True)
    w.columns = ["WALCL", "WTREGEN", "RRPONTSYD"]
    w = w.ffill().dropna()
    netto = _taeglich((w["WALCL"] - w["WTREGEN"] - w["RRPONTSYD"] * 1000) / 1e6, idx)
    real, zwei, kurve = (_taeglich(roh[k], idx) for k in ("DFII10", "DGS2", "T10Y2Y"))
    baa, nfci, dollar, vix = (_taeglich(roh[k], idx) for k in ("BAA10Y", "NFCI", "DTWEXBGS", "VIXCLS"))
    v = lambda r, t: r.shift(t)                                                    # noqa: E731  idx taeglich ohne Luecke
    K = {
        "K1 Geldmenge": (m2y, +1, m2y - v(m2y, 91), +1),
        "K2 Netto-Liquiditaet": (netto / v(netto, 364) - 1, +1, netto / v(netto, 91) - 1, +1),
        "K3 Realzins": (real, -1, real - v(real, 91), -1),
        "K4 Zinspfad 2J": (zwei, -1, zwei - v(zwei, 91), -1),
        "K5 Kurve": (kurve, +1, None, None),
        "K6 Kredit BAA": (baa, -1, baa - v(baa, 91), -1),
        "K7 NFCI": (nfci, -1, nfci - v(nfci, 91), -1),
        "K8 Dollar": (dollar, -1, dollar / v(dollar, 91) - 1, -1),
        "K9 VIX": (vix, -1, vix - v(vix, 91), -1),
    }
    dk, d2 = kurve - v(kurve, 91), zwei - v(zwei, 91)
    k5 = pd.Series(np.where((dk > 0) & (d2 < 0), 1.0, np.where((dk > 0) & (d2 > 0), -1.0, 0.0)), index=idx)
    k5[dk.isna() | d2.isna()] = np.nan
    return K, k5


def scores(roh: dict, idx: pd.DatetimeIndex) -> dict:
    """Score je Kanal lang/kurz und 'Gesamt lang'/'Gesamt kurz' (+1 Rueckenwind, 0 Mitte, -1 Gegenwind) - wie p51_vorpruefung.scores."""
    K, k5k = kanaele(roh, idx)
    S = {}
    for n, (lg, vl, kz, vk) in K.items():
        S[n + " lang"] = _score(lg, vl)
        S[n + " kurz"] = k5k if kz is None else _score(kz, vk)
    L = pd.concat([S[k] for k in S if k.endswith("lang")], axis=1)
    Kz = pd.concat([S[k] for k in S if k.endswith("kurz")], axis=1)
    for name, M in (("Gesamt lang", L), ("Gesamt kurz", Kz)):
        S[name] = _score(M.sum(axis=1, min_count=6), +1)
    return S


# ══ Lauf, Ablage ═════════════════════════════════════════════════════════════════════════════════════════════════════════
def _schreibe(ziel: str, d: dict) -> None:
    os.makedirs(os.path.dirname(ziel) or ".", exist_ok=True)
    tmp = ziel + ".neu"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=1)
    os.replace(tmp, ziel)


def lage_aus(roh: dict, heute: date) -> dict:
    idx = pd.date_range(min(r.index.min() for r in roh.values()).normalize(), pd.Timestamp(heute), freq="D")
    S = scores(roh, idx)
    t = idx[-1]
    wert = lambda k: (None if pd.isna(S[k].loc[t]) else float(S[k].loc[t]))         # noqa: E731
    je = {n: {"name": NAME[n], "lang": wert(n + " lang"), "kurz": wert(n + " kurz")} for n in NAME}
    return {"stand": heute.isoformat(), "gesamt_lang": wert("Gesamt lang"), "gesamt_kurz": wert("Gesamt kurz"), "je_kanal": je,
            "datenstand": {k: (r.index.max() - pd.Timedelta(days=REIHEN[k])).date().isoformat() for k, r in roh.items()},
            "berechnet_am": datetime.now(timezone.utc).isoformat(timespec="seconds"), "fehler": None}


def lauf(ziel: str | None = None, fred_key: str | None = None, heute: date | None = None, http=None, pause: float = 0.3) -> dict:
    """Holt, rechnet, legt ab. Scheitert nie nach aussen: bei einem Fehler bleibt der alte Stand, mit ``fehler`` vermerkt."""
    heute = heute or date.today()
    ziel = ziel or ABLAGE
    fred_key = os.environ.get("FRED_API_KEY", "") if fred_key is None else fred_key
    try:
        if not fred_key:
            raise RuntimeError("kein FRED-Schluessel")
        d = lage_aus(hole_alle(fred_key, heute, http, pause), heute)
    except Exception as exc:                                                        # noqa: BLE001
        d = lade(ziel) or {"stand": None, "gesamt_lang": None, "gesamt_kurz": None, "je_kanal": {}, "datenstand": {}}
        d["fehler"] = "%s: %s (%s)" % (type(exc).__name__, str(exc).replace(fred_key or "\0", "***")[:200], heute.isoformat())
        logger.warning("Makro-Lage nicht neu berechnet - alter Stand %s bleibt: %s", d.get("stand"), d["fehler"])
    _schreibe(ziel, d)
    return d


def lade(ziel: str | None = None) -> dict | None:
    ziel = ziel or ABLAGE                                         # erst beim Aufruf - sonst haelt der Vorgabewert einen alten Pfad fest
    try:
        with open(ziel, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


# ══ Texte ════════════════════════════════════════════════════════════════════════════════════════════════════════════════
def _wort(x) -> str:
    return "nicht verfügbar" if x is None else WORT[float(x)]


def zustand(d: dict | None, heute: date | None = None) -> str:
    """'ok' | 'veraltet' | 'fehlt' - drei Zustaende, nie verwechselt."""
    if not d or not d.get("stand") or d.get("gesamt_kurz") is None:
        return "fehlt"
    heute = heute or date.today()
    return "veraltet" if (heute - date.fromisoformat(d["stand"])).days > VERALTET_TAGE else "ok"


def treiber(d: dict, seite: str = "kurz") -> list:
    """Die Kanaele, die in dieselbe Richtung zeigen wie das Gesamt (bei 'neutral': keine)."""
    g = d.get("gesamt_" + seite)
    if g is None or float(g) == 0.0:
        return []
    return [v["name"] for v in d.get("je_kanal", {}).values() if v.get(seite) is not None and float(v[seite]) == float(g)]


def zeile(d: dict | None = None, heute: date | None = None) -> str:
    """Eine Zeile fuer Mail und Statusseite."""
    d = lade() if d is None else d
    z = zustand(d, heute)
    if z == "fehlt":
        return "Makro-Lage NICHT VERFÜGBAR (noch nicht berechnet oder FRED nicht erreicht) – kein Urteil"
    k = d["gesamt_kurz"]
    tr = treiber(d, "kurz")
    satz = MESSUNG["kurz_gegen"] if k == -1 else (MESSUNG["kurz_rueck"] if k == 1 else MESSUNG["kurz_neutral"])
    txt = "lang: %s · kurz: %s%s – %s; %s" % (_wort(d["gesamt_lang"]), _wort(k), (" (%s)" % ", ".join(tr)) if tr else "", satz,
                                              MESSUNG["atr"])
    txt += " · Stand %s" % date.fromisoformat(d["stand"]).strftime("%d.%m.")
    if z == "veraltet":
        txt += " ⚠ VERALTET"
    if d.get("fehler"):
        txt += " · letzter Abruf gescheitert"
    return txt


def mailteil(d: dict | None = None) -> dict:
    """Fuer die REGEL0-Signalmail (Muster ``termin``): {'ein': Zeile, 'technik': [(k, v)]}."""
    return {"ein": zeile(d), "technik": [("Makro", "Fakt, nicht Teil der Regel (O54) · Kanäle wie Messung §51.7; Richtung und Risiko-"
                                                  "Bremse gemessen, beide nicht belegt (Schritt7 §23.56)")]}


def stand(d: dict | None = None, heute: date | None = None) -> dict:
    """Fuer die Statusseite und die Diagnose."""
    d = lade() if d is None else d
    return {"zustand": zustand(d, heute), "zeile": zeile(d, heute), "lang": _wort((d or {}).get("gesamt_lang")),
            "kurz": _wort((d or {}).get("gesamt_kurz")), "stand": (d or {}).get("stand"), "fehler": (d or {}).get("fehler"),
            "kanaele": [(v["name"], _wort(v.get("lang")), _wort(v.get("kurz"))) for v in (d or {}).get("je_kanal", {}).values()],
            "datenstand": (d or {}).get("datenstand", {})}
