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
    d = pd.Series([float(v) for _, v in obs], index=pd.to_datetime([t for t, _ in obs]) + pd.Timedelta(days=REIHEN.get(series_id, 0)))
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
    """Holt, rechnet, legt ab. Scheitert nie nach aussen: bei einem Fehler bleibt der alte Stand, mit ``fehler`` vermerkt.
    Der Abschnitt ``gesamtmarkt`` (L-A) hat einen EIGENEN Fehlerpfad - O54 haengt nie an ihm, und er behaelt seinen alten Stand."""
    heute = heute or date.today()
    ziel = ziel or ABLAGE
    fred_key = os.environ.get("FRED_API_KEY", "") if fred_key is None else fred_key
    alt = lade(ziel)
    roh = None
    try:
        if not fred_key:
            raise RuntimeError("kein FRED-Schluessel")
        roh = hole_alle(fred_key, heute, http, pause)
        d = lage_aus(roh, heute)
    except Exception as exc:                                                        # noqa: BLE001
        d = dict(alt or {"stand": None, "gesamt_lang": None, "gesamt_kurz": None, "je_kanal": {}, "datenstand": {}})
        d["fehler"] = "%s: %s (%s)" % (type(exc).__name__, str(exc).replace(fred_key or "\0", "***")[:200], heute.isoformat())
        logger.warning("Makro-Lage nicht neu berechnet - alter Stand %s bleibt: %s", d.get("stand"), d["fehler"])
    try:
        if roh is None:
            raise RuntimeError("Makro-Reihen nicht abgerufen")
        d["gesamtmarkt"] = gesamtmarkt(roh, hole_gesamt(fred_key, heute, http, pause), hole_fg(http), heute)
    except Exception as exc:                                                        # noqa: BLE001
        g = dict((alt or {}).get("gesamtmarkt") or {})
        g["fehler"] = "%s: %s (%s)" % (type(exc).__name__, str(exc).replace(fred_key or "\0", "***")[:200], heute.isoformat())
        d["gesamtmarkt"] = g
        logger.warning("Lagebild Gesamtmarkt nicht neu berechnet - alter Stand %s bleibt: %s", g.get("stand"), g["fehler"])
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
    """Fuer die REGEL0-Signalmail (Muster ``termin``): {'ein': Zeile, 'zusatz': [(k, v)], 'technik': [(k, v)]}.
    ``zusatz`` (L-A, E-137): die Zeile Gesamtmarkt direkt unter der Makro-Zeile."""
    d = lade() if d is None else d
    return {"ein": zeile(d), "zusatz": [("Gesamtmarkt", zeile_gesamtmarkt(d))],
            "technik": [("Makro", "Fakt, nicht Teil der Regel (O54) · Kanäle wie Messung §51.7; Richtung und Risiko-"
                                  "Bremse gemessen, beide nicht belegt (Schritt7 §23.56)"),
                        ("Gesamtmarkt", "Fakt, nicht Teil der Regel (L-A, E-137) · Befunde aus dem Indikator-Atlas E-135; "
                                        "rot nur bei Zinskurve UND Sahm-Regel")]}


def zeile_mail(d: dict | None = None, heute: date | None = None) -> str:
    """Fuer die Text-Mails B1/B3/B4 und C1: die Makro-Zeile, darunter (eigene Zeile, eingerueckt) der Gesamtmarkt (L-A, E-137)."""
    d = lade() if d is None else d
    return zeile(d, heute) + "\n  Gesamtmarkt " + zeile_gesamtmarkt(d, heute)


def stand(d: dict | None = None, heute: date | None = None) -> dict:
    """Fuer die Statusseite und die Diagnose."""
    d = lade() if d is None else d
    return {"zustand": zustand(d, heute), "zeile": zeile(d, heute), "lang": _wort((d or {}).get("gesamt_lang")),
            "kurz": _wort((d or {}).get("gesamt_kurz")), "stand": (d or {}).get("stand"), "fehler": (d or {}).get("fehler"),
            "kanaele": [(v["name"], _wort(v.get("lang")), _wort(v.get("kurz"))) for v in (d or {}).get("je_kanal", {}).values()],
            "datenstand": (d or {}).get("datenstand", {}), "gesamtmarkt": stand_gesamtmarkt(d, heute)}


# ══ Lagebild Gesamtmarkt (L-A Teil 1, E-137, 24.10.2026) ═════════════════════════════════════════════════════════════════
# Nutzer 24.10.: *"E2 alle"* (L1-L6) · *"E3 ja"* (rot nur bei Kurve UND Sahm) · *"E4 alle"* (Zeile in REGEL0, B1, B3, B4).
# Grundlage: Indikator-Atlas E-135 (Messplan_Indikator_Atlas_23_10.md, p73/p75). ⚠️ FAKT, KEIN SIGNAL - keine Makrogroesse laeuft den
# BTC-Wenden voraus (T1); die Zeile sperrt nichts und aendert nichts. Einzige Farbe: Rezessionsampel ROT.
GESAMT_AB = {"T10Y3M": 6, "SAHMREALTIME": 6, "NASDAQCOM": 60, "DGS10": 6, "THREEFYTP10": 6, "DCOILBRENTEU": 6, "CBBTCUSD": 15}
# Reihe: Jahre Abruf. Ohne Verzug (Beobachtungsdatum) - angezeigt wird der Stand, gerechnet wird nichts Kuenftiges.
# NASDAQCOM 60 J: die Baerenmarkt-Erkennung braucht das Allzeithoch (wie p73 ab 1971); CBBTCUSD (Coinbase, FRED) ab 2014-12.
KURVE_FENSTER_M = 24          # Kurve "angeschlagen": Monatsmittel < 0 binnen 24 Monaten - deckt alle Vorlaeufe der 10J-3M (0-16 Mon.)
SAHM_SCHWELLE = 0.50          # und 9 von 11 der 10J-2J (4-33 Mon., ohne 101) aus p73 (d); Sahm >= 0,50 = Rezessionssignal (p73 (e))
NASDAQ_MEDIAN_M = 60          # Median der 13 Nasdaq-Bullenmaerkte 1971-2026 (p73 (a), 18-239 Mon.)
FG_URL = "https://api.alternative.me/fng/"
GEMESSEN = {
    "L1": "Rezessionen kosteten den Nasdaq seit 1971 jedes Mal 24–68 %; die Kurve lief 1980–2008 jeder Rezession 4–33 Mon. voraus, "
          "2022–24 erstmals ohne Rezession. ROT (Kurve und Sahm) kam 1982–2026 bei allen 5 Rezessionen, aber 1–3 Mon. NACH deren "
          "Beginn – es bestätigt, es warnt nicht vor; ein Fehlalarm (07–10/2024)",
    "L2": "Nasdaq-Bullenmärkte seit 1971: Median 60 Mon. (18–239); BTC: 4 Zyklen – zu wenige für eine Regel",
    "L3": "Geldausweitung ist keine Voraussetzung für BTC oder Aktien (Atlas E-135)",
    "L4": "Fakt, keine gemessene Regel",
    "L5": "Fakt, keine gemessene Regel (Ölschocks gingen Inflations- und Rezessionsschüben voraus)",
    "L6": "einziger gemessener Vorläufer der BTC-Wenden (Rang 0,97), zum Teil aus dem Kurs; als Regel offen",
}


def hole_gesamt(fred_key: str, heute: date | None = None, http=None, pause: float = 0.3) -> dict:
    heute = heute or date.today()
    aus = {}
    for i, (sid, jahre) in enumerate(GESAMT_AB.items()):
        if i and pause:
            time.sleep(pause)
        aus[sid] = hole_reihe(sid, fred_key, (heute - timedelta(days=int(jahre * 365.25))).isoformat(), http)
    return aus


def hole_fg(http=None) -> dict:
    """Fear & Greed (alternative.me, frei): der juengste Tageswert."""
    import requests
    j = (http or requests).get(FG_URL, params={"limit": 1, "format": "json"}, timeout=30).json()["data"][0]
    return {"wert": int(j["value"]), "klasse": j.get("value_classification"),
            "datum": datetime.fromtimestamp(int(j["timestamp"]), tz=timezone.utc).date().isoformat()}


def baer_phasen(p: pd.Series, grenze: float = 0.20):
    """Wie ``p73_atlas_t3_lang.baer_phasen`` (R-R11): Hoch -> Tief mit Rueckgang >= grenze; -> (abgeschlossene, laufender oder None)."""
    ath, ath_t, phasen = p.iloc[0], p.index[0], []
    tief, tief_t, im_baer = None, None, False
    for t, v in p.items():
        if not im_baer:
            if v > ath:
                ath, ath_t = v, t
            elif v <= ath * (1 - grenze):
                im_baer, tief, tief_t = True, v, t
        else:
            if v < tief:
                tief, tief_t = v, t
            if v >= ath:
                phasen.append((ath_t, tief_t, tief / ath - 1))
                im_baer, ath, ath_t = False, v, t
    offen = (ath_t, tief_t, tief / ath - 1) if im_baer else None
    return phasen, offen


def _monate(a, b) -> float:
    return (pd.Timestamp(b) - pd.Timestamp(a)).days / 30.44


def _letzt(r: pd.Series, verzug: int = 0):
    r = r.dropna()
    return float(r.iloc[-1]), (r.index[-1] - pd.Timedelta(days=verzug)).date().isoformat()


def _vor(r: pd.Series, tage: int):
    r = r.dropna()
    v = r[r.index <= r.index[-1] - pd.Timedelta(days=tage)]
    return float(v.iloc[-1]) if len(v) else None


def rezession(t2: pd.Series, t3: pd.Series, sahm: pd.Series, heute: date) -> dict:
    """L1: Kurve angeschlagen = Monatsmittel 10J-2J ODER 10J-3M < 0 in den letzten 24 Monaten (wie p73 (d)); Sahm >= 0,50; rot = beides."""
    grenze = (pd.Timestamp(heute) - pd.DateOffset(months=KURVE_FENSTER_M)).to_period("M").to_timestamp("M")
    inv = {}
    for name, k in (("10J–2J", t2), ("10J–3M", t3)):
        m = k.dropna().resample("ME").mean()
        neg = m[m < 0]
        inv[name] = neg.index[-1] if len(neg) else None
    kurve_an = any(t is not None and t >= grenze for t in inv.values())
    s, s_dat = _letzt(sahm)
    return {"kurve_2j": _letzt(t2), "kurve_3m": _letzt(t3),
            "inversion_zuletzt": {k: (v.strftime("%Y-%m") if v is not None else None) for k, v in inv.items()},
            "kurve_an": bool(kurve_an), "sahm": (s, s_dat), "sahm_an": bool(s >= SAHM_SCHWELLE),
            "rot": bool(kurve_an and s >= SAHM_SCHWELLE)}


def _z(x: float, n: int = 2) -> str:
    return ("%.*f" % (n, x)).replace(".", ",")


def _p(x: float, n: int = 0) -> str:
    return ("%+.*f %%" % (n, 100 * x)).replace(".", ",")


def gesamtmarkt(roh: dict, ex: dict, fg: dict | None, heute: date) -> dict:
    """L1-L6 als Fakt -> {'stand', 'rot', 'zeilen': [(Nr, Stichwort, Wert, gemessen)], 'kurz': Mailzeile, 'werte': {...}, 'fehler': None}."""
    t2 = roh["T10Y2Y"].copy()
    t2.index = t2.index - pd.Timedelta(days=REIHEN["T10Y2Y"])                            # zurueck aufs Beobachtungsdatum (wie p73)
    L1 = rezession(t2, ex["T10Y3M"], ex["SAHMREALTIME"], heute)
    nq = ex["NASDAQCOM"].dropna()
    phasen, offen = baer_phasen(nq)
    nq_bull = None if offen else (phasen[-1][1].date().isoformat() if phasen else None)
    btc = ex["CBBTCUSD"].dropna()
    ath_t = btc.idxmax()
    m2y = (roh["M2SL"] / roh["M2SL"].shift(12) - 1).dropna()
    w = pd.concat([roh["WALCL"], roh["WTREGEN"], roh["RRPONTSYD"].resample("W-WED").last()], axis=1, sort=True)
    w.columns = ["WALCL", "WTREGEN", "RRPONTSYD"]
    w = w.ffill().dropna()
    netto = (w["WALCL"] - w["WTREGEN"] - w["RRPONTSYD"] * 1000) / 1e6                       # wie kanaele() K2
    n_vor = _vor(netto, 182)
    d10, d10_dat = _letzt(ex["DGS10"])
    d10_vor = _vor(ex["DGS10"], 365)
    tp, tp_dat = _letzt(ex["THREEFYTP10"])
    br, br_dat = _letzt(ex["DCOILBRENTEU"])
    br_vor = _vor(ex["DCOILBRENTEU"], 365)
    W = {"rezession": L1,
         "nasdaq": {"stand": _letzt(nq), "bull_seit": nq_bull, "bull_monate": None if offen or not nq_bull else round(_monate(nq_bull, nq.index[-1]), 1),
                    "baer_seit": offen[0].date().isoformat() if offen else None, "baer_tief": offen[2] if offen else None},
         "btc": {"stand": _letzt(btc), "hoch": float(btc.max()), "hoch_am": ath_t.date().isoformat(), "abstand": float(btc.iloc[-1] / btc.max() - 1),
                 "monate_seit_hoch": round(_monate(ath_t, btc.index[-1]), 1)},
         "geld": {"m2_jj": (float(m2y.iloc[-1]), (m2y.index[-1] - pd.Timedelta(days=REIHEN["M2SL"])).date().isoformat()),
                  "netto_26w": None if not n_vor else float(netto.iloc[-1] / n_vor - 1),
                  "netto_stand": (roh["WALCL"].dropna().index[-1] - pd.Timedelta(days=REIHEN["WALCL"])).date().isoformat()},
         "anleihen": {"zehn": (d10, d10_dat), "zehn_12m": None if d10_vor is None else d10 - d10_vor, "praemie": (tp, tp_dat)},
         "oel": {"brent": (br, br_dat), "brent_12m": None if not br_vor else br / br_vor - 1},
         "fg": fg}
    # Texte
    inv = [("%s zuletzt %s" % (k, v[5:] + "/" + v[:4])) for k, v in L1["inversion_zuletzt"].items() if v]
    if L1["rot"]:
        t1 = "ROT – Zinskurve und Sahm-Regel schlagen an"
    elif L1["kurve_an"]:
        t1 = "Warnung der Zinskurve (%s invertiert), Sahm %s – kein Rot" % (", ".join(inv), _z(L1["sahm"][0]))
    elif L1["sahm_an"]:
        t1 = "Sahm-Regel %s schlägt an, Kurve nicht invertiert – kein Rot" % _z(L1["sahm"][0])
    else:
        t1 = "keine Rezessionssignale (Kurve %s/%s, Sahm %s)" % (_z(L1["kurve_2j"][0]), _z(L1["kurve_3m"][0]), _z(L1["sahm"][0]))
    n = W["nasdaq"]
    t2n = ("Nasdaq-Bull seit %.0f Mon. (Median %d)" % (n["bull_monate"], NASDAQ_MEDIAN_M)) if n["bull_monate"] is not None else \
        ("Nasdaq im Bärenmarkt seit %s (%s)" % (n["baer_seit"], _p(n["baer_tief"])) if n["baer_seit"] else "Nasdaq: keine Phase erkennbar")
    b = W["btc"]
    t2b = "BTC %s vom Hoch (vor %.0f Mon.)" % (_p(b["abstand"]), b["monate_seit_hoch"]) if b["abstand"] < -0.005 else "BTC am Allzeithoch"
    g = W["geld"]
    t3 = "M2 %s J/J%s" % (_p(g["m2_jj"][0], 1), (" · Netto-Liquidität %s in 26 W" % _p(g["netto_26w"], 1)) if g["netto_26w"] is not None else "")
    a = W["anleihen"]
    t4 = "10J %s %%%s · Laufzeitprämie %s %%" % (_z(a["zehn"][0]), (" (%s Pp in 12 M)" % ("%+.2f" % a["zehn_12m"]).replace(".", ","))
                                                if a["zehn_12m"] is not None else "", _z(a["praemie"][0]))
    o = W["oel"]
    t5 = "Brent %s $%s" % (_z(o["brent"][0], 0), (" (%s in 12 M)" % _p(o["brent_12m"])) if o["brent_12m"] is not None else "")
    t6 = ("F&G %d (%s%s)" % (fg["wert"], fg.get("klasse") or "", ", Extrem" if fg["wert"] < 25 or fg["wert"] > 75 else "")) if fg else "F&G nicht verfügbar"
    zeilen = [("L1", "Rezessionsampel", t1, GEMESSEN["L1"]), ("L2", "Reifegrad", t2n + " · " + t2b, GEMESSEN["L2"]),
              ("L3", "Geld", t3, GEMESSEN["L3"]), ("L4", "Zinsen und Anleihen", t4, GEMESSEN["L4"]),
              ("L5", "Öl", t5, GEMESSEN["L5"]), ("L6", "Fear & Greed", t6, GEMESSEN["L6"])]
    kurz = " · ".join(["Rezessionsampel ROT" if L1["rot"] else ("Kurve warnt, kein Rot" if L1["kurve_an"] else
                                                                ("Sahm schlägt an, kein Rot" if L1["sahm_an"] else "keine Rezessionssignale")),
                       t2n, t2b, "10J %s %%" % _z(a["zehn"][0]), "Brent %s $" % _z(o["brent"][0], 0)] + ([t6.split(" (")[0]] if fg else []))
    return {"stand": heute.isoformat(), "rot": L1["rot"], "zeilen": zeilen, "kurz": kurz, "werte": W,
            "datenstand": {"Kurve": L1["kurve_3m"][1], "Sahm": L1["sahm"][1], "Nasdaq": n["stand"][1], "BTC": b["stand"][1],
                           "10J": d10_dat, "Prämie": tp_dat, "Brent": br_dat, "F&G": (fg or {}).get("datum")},
            "berechnet_am": datetime.now(timezone.utc).isoformat(timespec="seconds"), "fehler": None}


def zustand_gesamtmarkt(d: dict | None, heute: date | None = None) -> str:
    g = (d or {}).get("gesamtmarkt") or {}
    if not g.get("stand") or not g.get("kurz"):
        return "fehlt"
    heute = heute or date.today()
    return "veraltet" if (heute - date.fromisoformat(g["stand"])).days > VERALTET_TAGE else "ok"


def zeile_gesamtmarkt(d: dict | None = None, heute: date | None = None) -> str:
    """Eine Zeile fuer Mail und Statusseite - Fakt, kein Signal."""
    d = lade() if d is None else d
    z = zustand_gesamtmarkt(d, heute)
    if z == "fehlt":
        return "Lagebild NICHT VERFÜGBAR (noch nicht berechnet oder Quelle nicht erreicht) – kein Urteil"
    g = d["gesamtmarkt"]
    txt = g["kurz"] + " · Stand %s" % date.fromisoformat(g["stand"]).strftime("%d.%m.")
    if z == "veraltet":
        txt += " ⚠ VERALTET"
    if g.get("fehler"):
        txt += " · letzter Abruf gescheitert"
    return txt


def stand_gesamtmarkt(d: dict | None, heute: date | None = None) -> dict:
    g = (d or {}).get("gesamtmarkt") or {}
    return {"zustand": zustand_gesamtmarkt(d, heute), "zeile": zeile_gesamtmarkt(d or {}, heute), "rot": bool(g.get("rot")),
            "zeilen": [list(x) for x in g.get("zeilen") or []], "stand": g.get("stand"), "fehler": g.get("fehler"),
            "datenstand": g.get("datenstand") or {}}
