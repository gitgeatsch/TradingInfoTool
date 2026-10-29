# -*- coding: utf-8 -*-
"""Grundmodul Messplan W „Wal-Fluss“ (``Basisinfos/Messplan_Wale_29_10.md``, vorab 3c9e873f, Nutzer-Ja 29.10.2026).

EIN Rechenweg für Vorprüfung, Selbsttest und Messung — der Selbsttest prüft damit denselben PFAD, nicht eine Nachbildung
(Memory „Ein Test deckt die Funktion ab, nicht den Pfad“). Die Gegenprobe rechnet absichtlich NICHT hiermit.

    G   Netto der größten Sweeps mit zusammen >= q des Tagesumsatzes / Tagesumsatz        (Messplan §4)
    R   Netto der übrigen Sweeps / Tagesumsatz
    E   G - (b0 + b1 R + b2 r_t), b aus den vorangehenden 180 Tagen (bis t-1)             Hauptgröße
    L   Fünftel von E gegen die vorangehenden 365 Tage: +1 oberstes, -1 unterstes, 0 sonst
    y   Log-Ertrag Spot ab 00:00 UTC t+1 (bzw. 06:00, Verzug) über H Tage, brutto
    D   Mittel(y | L=+1) - Mittel(y | L=-1)                                                Hauptstatistik

Nur lesend (``mode=ro``); die geschützte Datei wird vorher/nachher verglichen (``fingerabdruck``).
"""
import os
import sqlite3
import sys
from datetime import date, datetime, timedelta, timezone

import numpy as np

HIER = os.path.dirname(os.path.abspath(__file__))
WURZEL = os.path.dirname(os.path.dirname(HIER))
sys.path.insert(0, WURZEL)
import messnorm as N  # noqa: E402

ABLAGE = os.path.join(WURZEL, "data", "_wale", "wale_voll.db")
GESCHUETZT = [os.path.join(WURZEL, "data", "tradinginfotool.db")]
SYMBOLE = ("BTCUSDT", "ETHUSDT")
MAERKTE = ("spot", "futures")
STUFEN = (0.01, 0.05, 0.10, 0.20)
Q_HAUPT = 0.05
HORIZONTE = (1, 3, 7)
HYPOTHESEN = len(MAERKTE) * len(HORIZONTE)          # 6 je Wert, Bonferroni (Messplan §5)
ALPHA = 0.05
NULL_N = 40                                          # Messstandard 09.09.: Nullpunkt = Mittel aus 40 Ziehungen
NULL_BLOCK = 15                                      # Nullwelt: E in 15-T-Blöcken vertauscht (§5)
FENSTER_B, FENSTER_RANG, MIN_BEOB = 180, 365, 120
START = date(2023, 1, 1)
URTEIL = (date(2025, 1, 1), date(2026, 9, 30))
EPOCHE2 = (date(2023, 7, 1), date(2024, 12, 31))
JAHRE = {"2025": (date(2025, 1, 1), date(2025, 12, 31)), "2026": (date(2026, 1, 1), date(2026, 9, 30))}
NULLWELT = "block"                                   # vom Selbsttest nach Vorab-Regel bestätigt oder ersetzt (§5)


def ro(pfad=ABLAGE):
    return sqlite3.connect("file:%s?mode=ro" % pfad.replace("\\", "/"), uri=True)


def fingerabdruck():
    return [(p, os.path.getsize(p), os.path.getmtime(p)) if os.path.exists(p) else (p, None, None) for p in GESCHUETZT]


def tage(bis: date) -> list:
    return [START + timedelta(days=i) for i in range((bis - START).days + 1)]


# ── Fluss ────────────────────────────────────────────────────────────────────────────────────────────────────────────────
def fluss(con, symbol: str, markt: str, tg: list) -> dict:
    """-> {q: (G, R)} je Tag (Arrays über ``tg``, NaN wo der Tag fehlt). Grenzklasse ganz dabei (wie Stichprobe §6)."""
    idx = {d.isoformat(): i for i, d in enumerate(tg)}
    kl = np.zeros((len(tg), 37, 2))                       # [Tag, Klasse, kauf/verkauf]
    da = np.zeros(len(tg), bool)
    for datum, seite, klasse, usd in con.execute(
            "SELECT datum, seite, klasse, usd FROM verteilung WHERE symbol=? AND markt=? AND einheit='sweep'", (symbol, markt)):
        i = idx.get(datum)
        if i is not None:
            kl[i, klasse, 0 if seite == "kauf" else 1] += usd
            da[i] = True
    ges = kl.sum(axis=(1, 2))
    netto = kl[:, :, 0] - kl[:, :, 1]
    oben = (kl.sum(axis=2))[:, ::-1].cumsum(axis=1)[:, ::-1]      # Umsatz der Klassen >= k
    aus = {}
    for q in STUFEN:
        with np.errstate(invalid="ignore", divide="ignore"):
            # Grenzklasse: die HÖCHSTE Klasse k, ab der die Klassen >= k zusammen >= q des Umsatzes machen
            reicht = oben >= q * ges[:, None]
            k = np.where(reicht.any(axis=1), 36 - np.argmax(reicht[:, ::-1], axis=1), 0)
            maske = np.arange(37)[None, :] >= k[:, None]
            g = (netto * maske).sum(axis=1) / ges
            r = (netto * ~maske).sum(axis=1) / ges
        aus[q] = (np.where(da, g, np.nan), np.where(da, r, np.nan))
    return aus


# ── Kurse und Erträge ────────────────────────────────────────────────────────────────────────────────────────────────────
def kurse(con, symbol: str) -> dict:
    return dict(con.execute("SELECT ts, eroeffnung FROM kurs WHERE symbol=?", (symbol,)))


def _ms(d: date, stunde: int = 0) -> int:
    return int(datetime(d.year, d.month, d.day, stunde, tzinfo=timezone.utc).timestamp() * 1000)


def bewegung(px: dict, tg: list) -> np.ndarray:
    """r_t = ln(P(t+1 00:00) / P(t 00:00)) — die Bewegung DES Tages t (Fakt am Tagesende)."""
    a = np.array([px.get(_ms(d), np.nan) for d in tg])
    b = np.array([px.get(_ms(d + timedelta(days=1)), np.nan) for d in tg])
    return np.log(b / a)


def ertrag(px: dict, tg: list, h: int, verzug: int = 0) -> np.ndarray:
    """y_t = ln(P(t+1+h, verzug) / P(t+1, verzug)) — Einstieg am Schluss von t (00:00 t+1) bzw. ``verzug`` Stunden später."""
    a = np.array([px.get(_ms(d + timedelta(days=1), verzug), np.nan) for d in tg])
    b = np.array([px.get(_ms(d + timedelta(days=1 + h), verzug), np.nan) for d in tg])
    return np.log(b / a)


# ── Hauptgröße E und Fünftel L ───────────────────────────────────────────────────────────────────────────────────────────
def residuum(g, r, bew, fenster=FENSTER_B, minimum=MIN_BEOB):
    """E_t = G_t - (b0 + b1 R_t + b2 r_t), b per OLS aus [t-fenster, t-1] (mindestens ``minimum`` vollständige Tage)."""
    n = len(g)
    e = np.full(n, np.nan)
    X = np.column_stack([np.ones(n), r, bew])
    ok = np.isfinite(g) & np.isfinite(r) & np.isfinite(bew)
    for t in range(n):
        if not ok[t]:
            continue
        lo = max(0, t - fenster)
        m = ok[lo:t]
        if m.sum() < minimum:
            continue
        b, *_ = np.linalg.lstsq(X[lo:t][m], g[lo:t][m], rcond=None)
        e[t] = g[t] - X[t] @ b
    return e


def fuenftel(e, fenster=FENSTER_RANG, minimum=MIN_BEOB):
    """L_t: +1 wenn E_t über dem 80. Perzentil der vorangehenden ``fenster`` Tage, -1 unter dem 20., 0 sonst, NaN ohne Vorlauf.
    ⚠️ Fassung 2 (beim Bau): bis 365 Werte vorliegen, gilt der vorhandene Vorlauf, mindestens 120 (sonst begänne der Rang erst 2024-07)."""
    n = len(e)
    lab = np.full(n, np.nan)
    for t in range(n):
        if not np.isfinite(e[t]):
            continue
        v = e[max(0, t - fenster):t]
        v = v[np.isfinite(v)]
        if len(v) < minimum:
            continue
        lo, hi = np.quantile(v, (0.2, 0.8))
        lab[t] = 1.0 if e[t] > hi else (-1.0 if e[t] < lo else 0.0)
    return lab


# ── Statistik, Band, Nullwelt, Urteil ────────────────────────────────────────────────────────────────────────────────────
def maske(tg, zeitraum):
    a, b = zeitraum
    return np.array([a <= d <= b for d in tg])


def differenz(lab, y):
    o, u = (lab == 1) & np.isfinite(y), (lab == -1) & np.isfinite(y)
    if o.sum() == 0 or u.sum() == 0:
        return float("nan")
    return float(y[o].mean() - y[u].mean())


def band(lab, y, block, alpha):
    """Cluster-robustes t-Band über Kalenderblöcke (wie H-1 Fassung 4: t-Quantil nb-1, Faktor sqrt(nb/(nb-1)))."""
    from scipy.stats import t as _t
    o, u = (lab == 1) & np.isfinite(y), (lab == -1) & np.isfinite(y)
    b = np.arange(len(y)) // block
    nimm = o | u
    ub, inv = np.unique(b[nimm], return_inverse=True)
    nb = len(ub)
    if nb < 2 or o.sum() == 0 or u.sum() == 0:
        return float("nan"), float("nan"), nb
    so = np.bincount(inv, weights=np.where(o, y, 0)[nimm], minlength=nb)
    ko = np.bincount(inv, weights=o[nimm].astype(float), minlength=nb)
    su = np.bincount(inv, weights=np.where(u, y, 0)[nimm], minlength=nb)
    ku = np.bincount(inv, weights=u[nimm].astype(float), minlength=nb)
    mo, mu = so.sum() / ko.sum(), su.sum() / ku.sum()
    einfluss = (so - mo * ko) / ko.sum() - (su - mu * ku) / ku.sum()
    halb = _t.ppf(1 - alpha / 2, nb - 1) * np.sqrt(nb / (nb - 1)) * np.sqrt((einfluss ** 2).sum())
    d = mo - mu
    return float(d - halb), float(d + halb), nb


def vertausche(lab, rng, art=None):
    """Nullwelt: ``block`` = L in 15-T-Blöcken vertauscht (Ballung bleibt), ``kreis`` = zirkulär um 60..n-60 Tage verschoben."""
    art = art or NULLWELT
    n = len(lab)
    if art == "kreis":
        return np.roll(lab, int(rng.integers(60, max(61, n - 60))))
    teile = [lab[i:i + NULL_BLOCK] for i in range(0, n, NULL_BLOCK)]
    return np.concatenate([teile[i] for i in rng.permutation(len(teile))])


def nullpunkt(lab, y, rng, n=NULL_N, art=None):
    w = np.array([differenz(vertausche(lab, rng, art), y) for _ in range(n)])
    w = w[np.isfinite(w)]
    return float(w.mean()), float(np.quantile(w, 0.9)), float(np.quantile(w, 0.1))


def bewerte(lab, y, h, rng, aufloesung=None, art=None, mit_block=True):
    """-> dict: D, Band, Nullpunkt, Blöcke, Autokorrelation, Stufe (messnorm-Stufen; zweiseitig, Vorzeichen ausgewiesen)."""
    ok = np.isfinite(lab) & np.isfinite(y)
    lab, y = np.where(ok, lab, np.nan), np.where(ok, y, np.nan)
    blk = N._block(h)
    d = differenz(lab, y)
    u, o, nb = band(lab, y, blk, ALPHA / HYPOTHESEN)
    npkt, n90, n10 = nullpunkt(lab, y, rng, art=art)
    ak = float("nan")
    if mit_block:
        je_tag = {i: float(lab[i] * y[i]) for i in range(len(y)) if ok[i] and lab[i] != 0}
        pb = N.pruefe_block(je_tag, blk)
        ak, block_ok = pb["ak"], pb["ok"] or not np.isfinite(pb["ak"])
    else:
        block_ok = True
    if not np.isfinite(d):
        st = "KEIN BEFUND - keine Fünftel"
    elif nb < 20:
        st = "KEIN BEFUND - nur %d Blöcke" % nb
    elif not block_ok:
        st = "KEIN BEFUND - Block %d zu kurz (AK %.3f)" % (blk, ak)
    elif u > npkt or o < npkt:
        st = "TRAEGT (%s)" % ("oberstes Fünftel HÖHER" if d > npkt else "oberstes Fünftel NIEDRIGER")
    elif aufloesung is not None and (o - npkt) < aufloesung and (npkt - u) < aufloesung:
        st = "TRAEGT NICHT BIS %.2f Pp" % (100 * aufloesung)
    else:
        st = "NICHT TRENNBAR"
    return {"D": d, "unten": u, "oben": o, "nullpunkt": npkt, "null90": n90, "null10": n10, "n_bloecke": nb, "block": blk,
            "ak": ak, "n_oben": int((lab == 1).sum()), "n_unten": int((lab == -1).sum()), "stufe": st}


# ── Laden ─────────────────────────────────────────────────────────────────────────────────────────────────────────────────
def lade(bis: date | None = None):
    """-> (tg, {symbol: {"r": r_t, "y": {(h, verzug): y}, "markt": {markt: {q: (G, R, E, L)}}}})."""
    con = ro()
    bis = bis or date.fromisoformat(con.execute("SELECT MIN(m) FROM (SELECT MAX(datum) m FROM tag GROUP BY symbol, markt)").fetchone()[0])
    tg = tage(bis)
    aus = {}
    for s in SYMBOLE:
        px = kurse(con, s)
        bew = bewegung(px, tg)
        aus[s] = {"r": bew, "y": {(h, v): ertrag(px, tg, h, v) for h in HORIZONTE for v in (0, 6)}, "markt": {}}
        for m in MAERKTE:
            aus[s]["markt"][m] = {}
            for q, (g, r) in fluss(con, s, m, tg).items():
                e = residuum(g, r, bew)
                aus[s]["markt"][m][q] = (g, r, e, fuenftel(e))
    con.close()
    return tg, aus
