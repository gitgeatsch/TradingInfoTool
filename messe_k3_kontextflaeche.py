# -*- coding: utf-8 -*-
"""K3: die KONTEXTFLAECHE - BTC-Rendite x Aenderung der BTC-Dominanz, 3 x 3, je Fenster.

**28.09.2026.** Voranalyse `Basisinfos/Voranalyse_K3_Kontextflaeche_28_09.md`,
A1-A4 abgestimmt (Nutzer: *"ja, A1 bis A4 wie empfohlen ... dann K3 messen"*,
*"pruefen und gegenpruefen"*). Nutzerhypothese: *"BTC steigt oder geht
seitlich und die Dominanz faellt sind zwei positive Effekte."*

VORAB FESTGELEGT (V1-V11 der Voranalyse)
    Kontext      BTC-Rendite und Aenderung des Index BTCDOMUSDT ueber DASSELBE
                 Fenster 24 / 72 / 120 h; Drittel-Grenzen ROLLIEREND aus den
                 12 Monaten davor (nur Vergangenheit) - seitwaerts = Mitte
    Lehrer       q5 = +5 % vor -5 % binnen 24 h URTEILT; Achse +-3/5/10 % x
                 24/72/120 h zeigt die Form (nur fuer die drei Hypothesenfelder)
    Bezug        PHASE: Trefferverhaeltnis desselben Assets in seinen letzten
                 12 Monaten, NUR aus Ausgaengen, die zum Pruefzeitpunkt
                 bekannt sind (Anker <= t - Lehrerfenster, G1); Kontrolle
                 MOMENT (Asset im selben Monat); dazu das ABSOLUTE q.
                 Die Tages-Kontrolle entfaellt beim Kontext (G2, A2).
    Anker        feste Tagesanker je Asset um 00/06/12/18 UTC (gepoolt) -
                 kein Mitternachtseffekt (2.666), Auswahl unabhaengig vom Feld
    Nullwelt     ZEITVERSCHIEBUNG: die Kontextreihe wird um einen Zufallsversatz
                 >= 60 Tage kreisfoermig verschoben, 40 Ziehungen; Grenze
                 Bestes-von-27 (9 Felder x 3 Fenster), 90. Perzentil
    Such/Pruef   Suche 2023-01 bis 2024-12 (urteilt), Pruefung 2025-01 bis
                 2026-08; 2022 nur Kontrolle mit Moment-Bezug (G3, A3)
    Urteil       Feld traegt: jenseits der Grenze (Suche) UND gleiches
                 Vorzeichen in der Pruefung UND >= 3 von 4 Jahren UND
                 vorwaerts >= 75 % der Monate (mind. 30 Anker im Monat)
    Additiv      Feld = Zeile + Spalte + Wechselwirkung; Wechselwirkung (Summe
                 der Quadrate) gegen dieselbe Nullwelt
    Hypothese    V10: (BTC hoch, Dom tief) UND (BTC mitte, Dom tief) positiv,
                 in Suche UND Pruefung
    Pflichtproben G1 Normal MIT den noch unbekannten 24 h (absichtlicher
                 Vorgriff) · G4 Positivkontrolle (Effekt in ein Feld
                 gepflanzt) · G5 ohne die 1 % groessten Stundenspruenge des
                 Index · G6 feste Grenzen aus der Suche · G9 Altersachse
                 (Kontext 6/12/24 h alt)

    python messe_k3_kontextflaeche.py --menge unverzerrt:1

NUR LESEND (`mode=ro`). Kein Stop, kein Trailing, keine Gebuehren (Regel 2).
"""
from __future__ import annotations

import os
import sqlite3
import sys
from datetime import datetime

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import messe_e2_beitraege as E2                                   # noqa: E402
from messe_e3_vorwaerts import monat_von                          # noqa: E402

B0 = datetime(2020, 1, 1)
RICHTUNG_DB = os.path.join(E2.HIER, "data", "richtung_historie.db")
FENSTER = (24, 72, 120)
HOEHEN = (3, 5, 10)
LEHRER_W = (24, 72, 120)
GITTER = (0, 6, 12, 18)
JAHR_H = 8760
ZIEHUNGEN, SAAT = 40, 20261005
MIN_VERSATZ_H = 60 * 24
NAMEN_B = ("BTC tief", "BTC mitte", "BTC hoch")
NAMEN_D = ("Dom tief", "Dom mitte", "Dom hoch")
HYPO = ((2, 0), (1, 0))          # (BTC hoch, Dom tief), (BTC mitte, Dom tief)
SPERRE = (2, 2)                  # (BTC hoch, Dom hoch) - 2.601


def _h(d):
    return int((d - B0).total_seconds() // 3600)


SUCHE = (_h(datetime(2023, 1, 1)), _h(datetime(2025, 1, 1)))
PRUEF = (_h(datetime(2025, 1, 1)), _h(datetime(2026, 9, 1)))
KONTR = (_h(datetime(2022, 1, 1)), _h(datetime(2023, 1, 1)))


def reihe(sqls):
    """Stundenschluesse aus mehreren (db, sql) vereinigt -> Array je Stunde seit 2020."""
    d = {}
    for db, sql in sqls:
        for st, c in sqlite3.connect("file:%s?mode=ro" % db, uri=True).execute(sql):
            d.setdefault(st, c)
    st = np.array([s.replace(" ", "T") for s in d], "datetime64[h]")
    h = (st - np.datetime64("2020-01-01T00", "h")).astype(np.int64)
    aus = np.full(int(h.max()) + 1, np.nan)
    aus[h] = list(d.values())
    return aus


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:                                         # noqa: BLE001
        pass
    E2.menge_aus_argv()
    print("=" * 120)
    print("K3 - KONTEXTFLAECHE BTC-Rendite x Dominanz-Aenderung (3 x 3) · MENGE %s" % E2.MENGE)
    print("=" * 120)
    erste = tuple(x for X in HOEHEN for x in (("u%d" % X, 1 + X / 100, True),
                                              ("d%d" % X, 1 - X / 100, False)))
    D = E2.lade(hmax=max(LEHRER_W), erste=erste)
    SYM, STD, T = D["SYM"], D["STD"], D["T"]
    del D
    n = len(SYM)
    MON = monat_von(STD)
    JAHR = (MON // 12).astype(np.int16)
    rng = np.random.default_rng(SAAT)

    def ab(X, W):
        tu, td = T["u%d" % X], T["d%d" % X]
        return (((tu <= W) & (tu < td)).astype(np.float32),
                ((td <= W) & (td <= tu)).astype(np.float32))

    # ── Phasen-Normal: letzte 12 Monate des Assets, nur BEKANNTE Ausgaenge
    ordnung = np.lexsort((STD, SYM))
    grenzen = np.flatnonzero(np.diff(SYM[ordnung])) + 1
    teile = np.split(ordnung, grenzen)

    def normal(a, b, W, vorgriff=False):
        na, nb = np.full(n, np.nan, np.float32), np.full(n, np.nan, np.float32)
        for tl in teile:
            s = STD[tl]
            ca = np.concatenate([[0.0], np.cumsum(a[tl])])
            cb = np.concatenate([[0.0], np.cumsum(b[tl])])
            lo = np.searchsorted(s, s - JAHR_H, "left")
            hi = (np.searchsorted(s, s, "left") if vorgriff
                  else np.searchsorted(s, s - W, "right"))
            k = hi - lo
            gut = (s - s[0] >= JAHR_H) & (k > 1000)
            na[tl] = np.where(gut, (ca[hi] - ca[lo]) / np.maximum(k, 1), np.nan)
            nb[tl] = np.where(gut, (cb[hi] - cb[lo]) / np.maximum(k, 1), np.nan)
        return na, nb

    A5, B5 = ab(5, 24)
    NA, NB = normal(A5, B5, 24)
    # Moment-Kontrolle: Asset im selben Monat
    SM = SYM.astype(np.int64) * 1000 + (MON - MON.min())
    _u, sm_i = np.unique(SM, return_inverse=True)
    sm_n = np.maximum(np.bincount(sm_i), 1)
    MA = (np.bincount(sm_i, weights=A5) / sm_n)[sm_i]
    MB = (np.bincount(sm_i, weights=B5) / sm_n)[sm_i]

    # ── Kontext
    btc = reihe([(E2.EINGESTELLT_DB, "SELECT stunde, close FROM stundenkurse WHERE symbol='BTC'"),
                 (E2.STUNDEN_DB, "SELECT stunde, close FROM stundenkurse WHERE symbol='BTC'")])
    dom = reihe([(E2.EINGESTELLT_DB, "SELECT stunde, close FROM btcdom"),
                 (RICHTUNG_DB, "SELECT stunde, close FROM btcdom")])
    L = max(len(btc), len(dom), int(STD.max()) + 2)
    btc = np.concatenate([btc, np.full(L - len(btc), np.nan)])
    dom = np.concatenate([dom, np.full(L - len(dom), np.nan)])

    def aenderung(x, k):
        v = np.full(L, np.nan)
        v[k:] = x[k:] / x[:-k] - 1.0
        return v

    def drittel(v, fest=None):
        if fest is None:
            s = pd.Series(v)
            q1 = s.rolling(JAHR_H, min_periods=6000).quantile(1 / 3).shift(1).to_numpy()
            q2 = s.rolling(JAHR_H, min_periods=6000).quantile(2 / 3).shift(1).to_numpy()
        else:
            q1, q2 = fest
        c = np.full(L, -1, np.int8)
        ok = np.isfinite(v) & np.isfinite(q1) & np.isfinite(q2)
        c[ok] = np.where(v[ok] <= q1[ok] if fest is None else v[ok] <= q1, 0,
                         np.where(v[ok] <= (q2[ok] if fest is None else q2), 1, 2))
        return c

    KC, KFEST, SPR = {}, {}, {}
    dlog = np.abs(np.diff(np.log(dom), prepend=np.nan))
    grenze_spr = np.nanpercentile(dlog, 99)
    for k in FENSTER:
        rb, rd = aenderung(btc, k), aenderung(dom, k)
        cb, cd = drittel(rb), drittel(rd)
        KC[k] = np.where((cb >= 0) & (cd >= 0), cb * 3 + cd, -1).astype(np.int8)
        such = np.zeros(L, bool); such[SUCHE[0]:SUCHE[1]] = True
        fb = (np.nanpercentile(rb[such], 100 / 3), np.nanpercentile(rb[such], 200 / 3))
        fd = (np.nanpercentile(rd[such], 100 / 3), np.nanpercentile(rd[such], 200 / 3))
        cbf, cdf = drittel(rb, fb), drittel(rd, fd)
        KFEST[k] = np.where((cbf >= 0) & (cdf >= 0), cbf * 3 + cdf, -1).astype(np.int8)
        m = pd.Series(dlog).rolling(k, min_periods=1).max().to_numpy()
        SPR[k] = m > grenze_spr

    # ── Anker: feste Tagesanker, mit Phase gueltig
    gitter = np.isin(STD % 24, GITTER)
    PH = np.isfinite(NA) & np.isfinite(NB)
    zeit = {"suche": (STD >= SUCHE[0]) & (STD < SUCHE[1]),
            "pruef": (STD >= PRUEF[0]) & (STD < PRUEF[1]),
            "2022": (STD >= KONTR[0]) & (STD < KONTR[1])}
    basis = gitter & PH
    print("  Anker (Tagesanker, Phase gueltig): Suche %d · Pruefung %d · 2022 (Moment) %d · Symbole %d"
          % ((basis & zeit["suche"]).sum(), (basis & zeit["pruef"]).sum(),
             (gitter & zeit["2022"]).sum(), len(np.unique(SYM[basis]))))

    def dq(sel, a=A5, b=B5, na=NA, nb=NB):
        if sel.sum() < 30:
            return np.nan
        q = a[sel].mean() / max(a[sel].mean() + b[sel].mean(), 1e-12)
        q0 = na[sel].mean() / max(na[sel].mean() + nb[sel].mean(), 1e-12)
        return float(q - q0)

    def dq_moment(sel):
        return dq(sel, na=MA, nb=MB)

    def qabs(sel):
        return float(A5[sel].mean() / max(A5[sel].mean() + B5[sel].mean(), 1e-12)) if sel.sum() else np.nan

    def gruppe(idx, keys, a=A5, b=B5, na=NA, nb=NB, minn=30):
        """-> (schluessel, Dq, Anzahl) je Gruppe - Summen statt Masken."""
        u, inv = np.unique(keys[idx] if len(keys) == n else keys, return_inverse=True)
        sa = np.bincount(inv, weights=a[idx]); sb = np.bincount(inv, weights=b[idx])
        sna = np.bincount(inv, weights=na[idx]); snb = np.bincount(inv, weights=nb[idx])
        cnt = np.bincount(inv)
        d = sa / np.maximum(sa + sb, 1e-12) - sna / np.maximum(sna + snb, 1e-12)
        d = np.where(cnt >= minn, d, np.nan)
        return u, d, cnt

    def flaeche(kc, auswahl, fn=None, a=A5, b=B5, na=NA, nb=NB):
        idx = np.flatnonzero(auswahl)
        zell = kc[STD[idx]]
        aus = np.full(9, np.nan)
        if fn is not None:                    # Sonderfaelle (Moment, q abs)
            for z in range(9):
                aus[z] = fn(np.isin(np.arange(n), idx[zell == z]))
            return aus
        ok = zell >= 0
        u, d, _c = gruppe(idx[ok], zell[ok], a, b, na, nb)
        aus[u] = d
        return aus

    def verschoben(kc, v):
        lo, hi = KONTR[0], PRUEF[1]
        s = kc.copy()
        s[lo:hi] = np.roll(kc[lo:hi], v)
        return s

    # ── Wert und Nullwelt (Suche)
    wert = {k: flaeche(KC[k], basis & zeit["suche"]) for k in FENSTER}
    null = {k: np.zeros((ZIEHUNGEN, 9)) for k in FENSTER}
    spanne = PRUEF[1] - KONTR[0]
    for zi in range(ZIEHUNGEN):
        v = int(rng.integers(MIN_VERSATZ_H, spanne - MIN_VERSATZ_H))
        for k in FENSTER:
            null[k][zi] = flaeche(verschoben(KC[k], v), basis & zeit["suche"])
    mu = {k: np.nanmean(null[k], axis=0) for k in FENSTER}
    sd = {k: np.maximum(np.nanstd(null[k], axis=0, ddof=1), 1e-9) for k in FENSTER}
    maxz = np.nanmax(np.stack([np.abs((null[k] - mu[k]) / sd[k]) for k in FENSTER], axis=2)
                     .reshape(ZIEHUNGEN, -1), axis=1)
    grenze = float(np.percentile(maxz, 90))

    def interaktion(f):
        m = f.reshape(3, 3)
        g = np.nanmean(m)
        r = np.nanmean(m, axis=1, keepdims=True) - g
        c = np.nanmean(m, axis=0, keepdims=True) - g
        return float(np.nansum((m - g - r - c) ** 2))

    print()
    print("  Grenze Bestes-von-27 (Zeitverschiebung, %d Ziehungen): z %.2f" % (ZIEHUNGEN, grenze))
    ergebnis = {}
    for k in FENSTER:
        z = (wert[k] - mu[k]) / sd[k]
        pr = flaeche(KC[k], basis & zeit["pruef"])
        k22 = flaeche(KC[k], gitter & zeit["2022"], na=MA, nb=MB)
        mo = flaeche(KC[k], basis & zeit["suche"], na=MA, nb=MB)
        idx_a = np.flatnonzero(basis & (zeit["suche"] | zeit["pruef"]))
        za = KC[k][STD[idx_a]]
        aq = np.array([A5[idx_a][za == z].sum() / max(A5[idx_a][za == z].sum() + B5[idx_a][za == z].sum(), 1e-12)
                       for z in range(9)])
        alle = basis & (zeit["suche"] | zeit["pruef"])
        zell = KC[k][STD]
        print()
        print("-" * 120)
        print("FENSTER %d h - Dq gegen die PHASE (q5, 24 h) · Suche 2023-24 urteilt" % k)
        print("  %-21s %8s %6s | %8s | %8s %8s | %6s | %5s %6s %6s | %s" % (
            "Feld", "Dq Suche", "z", "Dq Pruef", "Moment", "2022 Mo", "q abs", "Jahre",
            "vorw.", "Asset", "Urteil"))
        for zz in range(9):
            i, j = divmod(zz, 3)
            idx = np.flatnonzero(alle & (zell == zz))
            vz = np.sign(wert[k][zz])
            _u, dj, _c = gruppe(idx, JAHR, minn=200)
            jahre = [x for x in dj if np.isfinite(x)]
            j_ok = sum(int(np.sign(x) == vz) for x in jahre)
            _u, dm, _c = gruppe(idx, MON, minn=30)
            mon = [x for x in dm if np.isfinite(x)]
            m_ok = sum(int(np.sign(x) == vz) for x in mon)
            _u, ds, _c = gruppe(idx, SYM, minn=20)
            je = [np.sign(x) == vz for x in ds if np.isfinite(x)]
            asset = np.mean(je) if je else np.nan
            traegt = (abs(z[zz]) > grenze and np.sign(pr[zz]) == vz and len(jahre) >= 3
                      and j_ok >= 3 and mon and m_ok >= 0.75 * len(mon))
            ergebnis[(k, zz)] = (wert[k][zz], pr[zz], traegt)
            print("  %-21s %+8.4f %+6.2f | %+8.4f | %+8.4f %+8.4f | %6.3f | %d/%-3d %2d/%-3d %5.0f%% | %s" % (
                "%s / %s" % (NAMEN_B[i], NAMEN_D[j]), wert[k][zz], z[zz], pr[zz], mo[zz], k22[zz],
                aq[zz], j_ok, len(jahre), m_ok, len(mon), 100 * asset if np.isfinite(asset) else float("nan"),
                ("✔ TRAEGT +" if vz > 0 else "⛔ SPERRE") if traegt else "· nein"))
        ia = interaktion(wert[k])
        ia_null = np.array([interaktion(null[k][zi]) for zi in range(ZIEHUNGEN)])
        print("  Additivitaet: Wechselwirkung %.6f · Nullwelt Mittel %.6f, 90. Perzentil %.6f -> %s" % (
            ia, ia_null.mean(), np.percentile(ia_null, 90),
            "Wechselwirkung JENSEITS der Nullwelt - die Flaeche bleibt EIN Beitrag"
            if ia > np.percentile(ia_null, 90) else "additiv - zwei Kontextkurven reichen"))
        ik = np.flatnonzero(alle & (zell == 6))
        tage = STD[ik] // 24
        klumpen = [len(np.unique(SYM[ik][tage == d])) for d in np.unique(tage)[:300]]
        print("  Klumpen: im Feld BTC hoch / Dom tief liegen je Tag im Mittel %.0f Assets zugleich" % (
            np.mean(klumpen) if klumpen else 0))

    # ── V10 die Hypothese
    print()
    print("=" * 120)
    print("V10 - DEINE HYPOTHESE: (BTC hoch, Dom tief) UND (BTC mitte, Dom tief) positiv, Suche UND Pruefung")
    for k in FENSTER:
        teile_h = []
        for zz in (HYPO[0][0] * 3 + HYPO[0][1], HYPO[1][0] * 3 + HYPO[1][1]):
            w, p_, t_ = ergebnis[(k, zz)]
            teile_h.append("%s: Suche %+.4f, Pruef %+.4f%s" % (
                NAMEN_B[zz // 3], w, p_, " (traegt)" if t_ else ""))
        ok = all(ergebnis[(k, zz)][0] > 0 and ergebnis[(k, zz)][1] > 0
                 for zz in (HYPO[0][0] * 3 + HYPO[0][1], HYPO[1][0] * 3 + HYPO[1][1]))
        print("  %3d h  %s  ->  %s" % (k, " · ".join(teile_h),
                                       "✔ Vorzeichen wie vermutet" if ok else "⛔ nicht wie vermutet"))

    # ── Achse fuer die drei Felder
    print()
    print("=" * 120)
    print("ACHSE (Form, urteilt nicht): Dq gegen die Phase, Suche+Pruefung, fuer die Hypothesenfelder und die Sperre")
    alle = basis & (zeit["suche"] | zeit["pruef"])
    cache = {}
    for X in HOEHEN:
        for W in LEHRER_W:
            a_, b_ = ab(X, W)
            cache[(X, W)] = (a_, b_) + normal(a_, b_, W)
    for k in FENSTER:
        zell = KC[k][STD]
        for zz in (6, 3, 8):
            werte = []
            for X in HOEHEN:
                for W in LEHRER_W:
                    a, b, na, nb = cache[(X, W)]
                    ok = alle & (zell == zz) & np.isfinite(na)
                    werte.append("%d%%/%dh %+.3f" % (X, W, dq(ok, a, b, na, nb)))
            print("  %3d h %-20s %s" % (k, "%s/%s" % (NAMEN_B[zz // 3], NAMEN_D[zz % 3]), " · ".join(werte)))

    # ── Pflichtproben
    print()
    print("=" * 120)
    print("PFLICHTPROBEN (Suche, q5/24 h, Felder: BTC hoch/Dom tief · BTC mitte/Dom tief · BTC hoch/Dom hoch)")
    VNA, VNB = normal(A5, B5, 24, vorgriff=True)
    for k in FENSTER:
        zell = KC[k][STD]
        sel_s = basis & zeit["suche"]
        g1 = [dq(sel_s & (zell == zz), na=VNA, nb=VNB) - wert[k][zz] for zz in (6, 3, 8)]
        g5 = [dq(sel_s & (zell == zz) & ~SPR[k][STD]) for zz in (6, 3, 8)]
        g6 = [dq(sel_s & (KFEST[k][STD] == zz)) for zz in (6, 3, 8)]
        g9 = []
        for alt in (6, 12, 24):
            za = KC[k][np.maximum(STD - alt, 0)]
            g9.append("%dh alt: %s" % (alt, " ".join("%+.4f" % dq(sel_s & (za == zz)) for zz in (6, 3, 8))))
        print("  %3d h  Wert %s" % (k, " ".join("%+.4f" % wert[k][zz] for zz in (6, 3, 8))))
        print("        G1 Vorgriff im Normal (Differenz zum Wert): %s" % " ".join("%+.4f" % x for x in g1))
        print("        G5 ohne Indexspruenge: %s · G6 feste Grenzen: %s" % (
            " ".join("%+.4f" % x for x in g5), " ".join("%+.4f" % x for x in g6)))
        print("        G9 Altersachse: %s" % " · ".join(g9))
    # G4 Positivkontrolle: in (BTC hoch, Dom tief), 72 h, Treffer gepflanzt
    k, zz = 72, 6
    zell = KC[k][STD]
    sel = basis & zeit["suche"] & (zell == zz)
    print("  G4 Positivkontrolle (72 h, BTC hoch/Dom tief): Dq + d gepflanzt - gefunden (|z| > Grenze)?")
    # 0,01-0,04 vorab festgelegt; 0,08 und 0,16 nachgetragen (28.09.), um die
    # AUFLOESUNG zu bestimmen - ein Diagnosewert, kein Urteil
    for d in (0.01, 0.02, 0.04, 0.08, 0.16):
        gef = 0
        for _ in range(5):
            a = A5.copy(); b = B5.copy()
            idx = np.flatnonzero(sel & (b == 1))
            # d ist die Erhoehung von q: q = A/(A+B); b->a erhoeht A um m bei
            # gleichem A+B, also m = d * (Zahl der Anker mit einem Treffer)
            m = int(round(d * ((a + b)[sel] > 0).sum()))
            wahl = rng.choice(idx, size=min(m, len(idx)), replace=False)
            a[wahl], b[wahl] = 1, 0
            w = dq(sel, a, b)
            gef += int(abs((w - mu[k][zz]) / sd[k][zz]) > grenze)
        print("     +%.2f: gefunden %d von 5" % (d, gef))
    # ── R-R11: die Kontextzeilen aus E2f/2.665 ZUERST reproduzieren (Vorzeichen-
    # Felder, Moment-Bezug, 24 h, 2023-01 bis 2026-08), dann gegen die
    # Zeitverschiebung halten - erst dann darf K3 sie umstossen
    print()
    print("=" * 120)
    print("R-R11 - die Kontextzeilen aus E2f (2.665) nachgerechnet: Vorzeichen-Felder, Moment-Bezug, "
          "24 h, 2023-01 bis 2026-08, Tagesanker")
    rb24, rd24 = aenderung(btc, 24), aenderung(dom, 24)
    vz = np.where(np.isfinite(rb24) & np.isfinite(rd24),
                  (rb24 > 0).astype(np.int8) * 2 + (rd24 > 0).astype(np.int8), -1).astype(np.int8)
    fenster_e2f = gitter & (STD >= SUCHE[0]) & (STD < PRUEF[1])
    namen_vz = {3: "BTC 24h > 0 UND Dominanz > 0 (2.601-Sperre)", 2: "BTC 24h > 0 UND Dominanz < 0",
                1: "BTC 24h < 0 UND Dominanz > 0", 0: "BTC 24h < 0 UND Dominanz < 0"}
    def vz_werte(code):
        idx = np.flatnonzero(fenster_e2f)
        c_ = code[STD[idx]]
        ok = c_ >= 0
        u, d, _c = gruppe(idx[ok], c_[ok], na=MA, nb=MB)
        aus = np.full(4, np.nan); aus[u] = d
        return aus
    w_vz = vz_werte(vz)
    nz = np.array([vz_werte(verschoben(vz, int(rng.integers(MIN_VERSATZ_H, spanne - MIN_VERSATZ_H))))
                   for _ in range(ZIEHUNGEN)])
    for c_ in (3, 2, 1, 0):
        z_ = (w_vz[c_] - np.nanmean(nz[:, c_])) / max(np.nanstd(nz[:, c_], ddof=1), 1e-9)
        print("  %-46s q5 Dq %+.4f (E2f: %s) · z gegen die ZEITVERSCHIEBUNG %+.2f" % (
            namen_vz[c_], w_vz[c_], {3: "-0,019 / z -6,9", 2: "-0,003", 1: "+0,010 / z +3,6",
                                      0: "-0,002"}[c_], z_))
    print()
    print("  ⚠️ Gebuehren und Finanzierung sind nicht eingerechnet (Regel 2).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
