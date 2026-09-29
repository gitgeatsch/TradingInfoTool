# -*- coding: utf-8 -*-
"""K5-FOLGEMESSUNG - Kombination, Kalibrierung, Normal-Schrumpfung, PBO, Wirkungskurven (29.09.2026).

Voranalyse `Basisinfos/Voranalyse_K5_Folgemessung_Kombination_Kalibrierung_29_09.md`
(Nutzer: *ja, dein Vorschlag 1 und 3, und wenn moeglich noch weitere Punkte - baue
die Messung und fuehre diese auch gleich aus*). Dieselben Daten und Familien wie
K5 neu (`messe_k5_lage_vorlauf.py`); die Aufbereitung ist woertlich uebernommen.

    F1  Varianten K0 rsi allein · K1 gleichgewichtete Summe · K2 Stacking auf dem
        Training · K3 Stacking nicht-negativ auf Out-of-Fold · K4 gemeinsam
    F2  Platt-Kalibrierung: Steigung aus <= 24 Monaten, Achsenabschnitt aus 3
    F3  PBO (CSCV, 8 Monatsgruppen) ueber K0-K4
    F4  Empirical-Bayes-Schrumpfung des Phase-Normals (Abnahmeprobe)
    F5  Wirkungskurven je Beitrag und Fenster
KRITERIEN S0-S7 wie Abschnitt 2 der Voranalyse.

    python messe_k5_folge.py --menge bestand [--probe]
"""
from __future__ import annotations

import itertools
import os
import sys
from datetime import datetime

import numpy as np
import pandas as pd
from scipy.optimize import minimize
from scipy.special import expit

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import messe_e2_beitraege as E2                                   # noqa: E402
import messe_k1_schritt2b_kombination as K2                       # noqa: E402
from messe_e3_vorwaerts import monat_von                          # noqa: E402
from messe_k3_kontextflaeche import reihe                         # noqa: E402

GITTER_NEU = (20.0, 200.0, 2000.0, 20000.0, 200000.0, 2000000.0)
RR11_2680 = {"bestand": 0.0808, "unverzerrt:1": 0.0696, "unverzerrt:2": 0.0700, "unverzerrt:3": 0.0703}
ZIEHUNGEN, SAAT = 40, 20260930
H = K2._h
SUCHE, PRUEF, ROLL = K2.SUCHE, K2.PRUEF, K2.ROLL_MONATE
RSI = ("rsi_s", "rsi_s24")
LAGE = {"funding": ("fu_0", "fu_24", "fu_48"),
        "oi": ("oi_0", "oi_24", "oi_48"),
        "konten": ("ko_0", "ko_24", "ko_48")}
LAGE_SP = tuple(x for f in LAGE.values() for x in f)
FAMILIEN = {"rsi": RSI, **LAGE}
ALLE_SP = RSI + LAGE_SP
VARIANTEN = ("K0", "K1", "K2", "K3", "K4")
NAMEN = {"K0": "rsi allein", "K1": "Summe gleich", "K2": "Stacking Training",
         "K3": "Stacking OOF >= 0", "K4": "gemeinsam"}


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:                                         # noqa: BLE001
        pass
    E2.menge_aus_argv()
    K2.FORM = "b"
    K2.LAMBDAS = GITTER_NEU
    probe = "--probe" in sys.argv
    zieh = 3 if probe else ZIEHUNGEN
    monate = ROLL[:8] if probe else ROLL
    print("=" * 120)
    print("K5-FOLGEMESSUNG · MENGE %s%s" % (E2.MENGE, " · WERKZEUGTEST" if probe else ""))
    print("=" * 120)
    # ── Aufbereitung WOERTLICH wie K5 neu ────────────────────────────────
    D = E2.lade(hmax=72, erste=(("u5", 1.05, True), ("d5", 0.95, False)), mit_atr=True)
    SYM, STD = D["SYM"], D["STD"]
    n = len(SYM)
    t_u, t_d = D["T"]["u5"], D["T"]["d5"]
    A24 = ((t_u <= 24) & (t_u < t_d)).astype(np.float64)
    B24 = ((t_d <= 24) & (t_d <= t_u)).astype(np.float64)
    FR = {m: D["F"][m].astype(np.float64) for m in ("rsi", "oi_aenderung", "konten_verh", "funding_vortag")}
    del D
    MON = monat_von(STD)
    JAHR = (MON // 12).astype(np.int16)
    rng = np.random.default_rng(SAAT)
    ordnung = np.lexsort((STD, SYM))
    teile = np.split(ordnung, np.flatnonzero(np.diff(SYM[ordnung])) + 1)

    def normal(a, b, W):
        na, nb = np.full(n, np.nan), np.full(n, np.nan)
        for tl in teile:
            st = STD[tl]
            ca = np.concatenate([[0.0], np.cumsum(a[tl])]); cb = np.concatenate([[0.0], np.cumsum(b[tl])])
            lo = np.searchsorted(st, st - K2.JAHR_H, "left")
            hi = np.searchsorted(st, st - W, "right")
            k = hi - lo
            gut = (st - st[0] >= K2.JAHR_H) & (k > 1000)
            na[tl] = np.where(gut, (ca[hi] - ca[lo]) / np.maximum(k, 1), np.nan)
            nb[tl] = np.where(gut, (cb[hi] - cb[lo]) / np.maximum(k, 1), np.nan)
        return na, nb
    NA, NB = normal(A24, B24, 24)
    SM = SYM.astype(np.int64) * 1000 + (MON - MON.min())
    _u, smi = np.unique(SM, return_inverse=True)
    smn = np.maximum(np.bincount(smi), 1)
    MA = (np.bincount(smi, weights=A24) / smn)[smi]; MB = (np.bincount(smi, weights=B24) / smn)[smi]

    def logit_q(a, b):
        with np.errstate(divide="ignore", invalid="ignore"):
            q = np.clip(a / (a + b), 0.02, 0.98)
        return np.log(q / (1 - q))
    OFF = logit_q(NA, NB)
    OFF_M = logit_q(MA, MB)

    def selbst(v):
        s = np.full(n, np.nan)
        for tl in teile:
            ser = pd.Series(v[tl], index=pd.to_datetime(STD[tl].astype("int64") * 3600, unit="s"))
            med = ser.rolling("%dh" % K2.SELBST_H, closed="left", min_periods=240).median().to_numpy()
            s[tl] = v[tl] - med
        return s

    def alt(v, L):
        out = np.full(n, np.nan)
        for tl in teile:
            ss = STD[tl]
            j = np.searchsorted(ss, ss - L)
            jj = np.minimum(j, len(ss) - 1)
            ok = (j < len(ss)) & (ss[jj] == ss - L)
            w = np.full(len(tl), np.nan); w[ok] = v[tl][jj[ok]]
            out[tl] = w
        return out

    def mittel24(v):
        s = np.full(n, np.nan)
        for tl in teile:
            ser = pd.Series(v[tl], index=pd.to_datetime(STD[tl].astype("int64") * 3600, unit="s"))
            s[tl] = ser.rolling("24h", closed="right", min_periods=12).mean().to_numpy()
        return s

    E = {}
    s_rsi = selbst(FR["rsi"])
    E["rsi_s"] = s_rsi
    E["rsi_s24"] = alt(s_rsi, 24)
    fu, oi, ko = FR["funding_vortag"], FR["oi_aenderung"], mittel24(FR["konten_verh"])
    for kurz, v in (("fu", fu), ("oi", oi), ("ko", ko)):
        E[kurz + "_0"] = v
        E[kurz + "_24"] = alt(v, 24)
        E[kurz + "_48"] = alt(v, 48)
    GRID = np.isin(STD % 24, K2.GITTER)
    BASIS = GRID & np.isfinite(OFF)
    HIT = (A24 + B24) > 0
    such = BASIS & (STD >= SUCHE[0]) & (STD < SUCHE[1])
    pruef = BASIS & (STD >= PRUEF[0]) & (STD < PRUEF[1])
    with np.errstate(divide="ignore", invalid="ignore"):
        QN = NA / (NA + NB)
    print("  Anker (Gitter, mit Phase-Normal): Suche %d · Pruefung %d · Symbole %d" % (
        such.sum(), pruef.sum(), len(np.unique(SYM[such | pruef]))))

    def dq(ix, y=A24, na=NA, nb=NB):
        if not len(ix):
            return np.nan
        a = y[ix].sum(); b = (HIT[ix] & (y[ix] == 0)).sum()
        sa, sb = na[ix].sum(), nb[ix].sum()
        return a / max(a + b, 1e-12) - sa / max(sa + sb, 1e-12)

    r_sa = np.flatnonzero(such); r_s = np.flatnonzero(such & HIT); r_pa = np.flatnonzero(pruef)

    def stapel(C, y, off, nichtneg=False):
        M = np.column_stack(C)

        def f(p):
            z = off + p[0] + M @ p[1:]
            r = expit(z) - y
            return float(np.sum(np.logaddexp(0.0, z) - y * z)), np.concatenate([[r.sum()], M.T @ r])
        gr = [(None, None)] + [((0.0, None) if nichtneg else (None, None))] * M.shape[1]
        return minimize(f, np.r_[0.0, np.ones(M.shape[1])], jac=True, method="L-BFGS-B", bounds=gr).x

    def oof(EE, ks, lam, ra, rt, y, off):
        """Out-of-Fold-Beitraege auf rt (B1): 4 Zeitbloecke, 24 h Abstand, feste Daempfung."""
        st, sta = STD[rt], STD[ra]
        kanten = np.quantile(st, np.linspace(0, 1, K2.CV_BLOECKE + 1)[1:-1])
        blk = np.searchsorted(kanten, st, "right"); blka = np.searchsorted(kanten, sta, "right")
        aus = np.zeros(len(rt))
        for b in range(K2.CV_BLOECKE):
            te = blk == b
            if not te.any():
                continue
            lo, hi = st[te].min(), st[te].max()
            tr = (blk != b) & ((st < lo - 24) | (st > hi + 24))
            tra = (blka != b) & ((sta < lo - 24) | (sta > hi + 24))
            m = K2.Modell(ks, lam).fit(EE, ra[tra], rt[tr], y[tr], off[tr])
            aus[te] = m.z(EE, rt[te], off[te]) - off[te]
        return aus

    def schaetze(EE, ra, rt, y, off, mit_k4=True, fertig=None):
        """-> dict je Variante: Funktion rows,off -> Beitrag; dazu Familienmodelle.
        `fertig`: schon geschaetzte Familien (z. B. rsi), werden uebernommen."""
        mods, lams = dict(fertig or {}), {}
        for f_, ks in FAMILIEN.items():
            if f_ in mods:
                continue
            mods[f_], lams[f_] = K2.fit_cv(ks, EE, ra, rt, y, off, STD)
        C = [mods[f_].z(EE, rt, off) - off for f_ in FAMILIEN]
        g2 = stapel(C, y, off)
        Co = [oof(EE, FAMILIEN[f_], mods[f_].lam, ra, rt, y, off) for f_ in FAMILIEN]
        g3 = stapel(Co, y, off, nichtneg=True)
        k4 = K2.fit_cv(ALLE_SP, EE, ra, rt, y, off, STD)[0] if mit_k4 else None

        def beitr(rows, o, v):
            cf = [mods[f_].z(EE, rows, o) - o for f_ in FAMILIEN]
            if v == "K0":
                return cf[0]
            if v == "K1":
                return sum(cf)
            if v == "K2":
                return g2[0] + sum(w * c for w, c in zip(g2[1:], cf))
            if v == "K3":
                return g3[0] + sum(w * c for w, c in zip(g3[1:], cf))
            return k4.z(EE, rows, o) - o
        return dict(beitr=beitr, mods=mods, g2=g2, g3=g3, k4=k4)

    def fest(EE, varianten=VARIANTEN, fertig=None):
        s = schaetze(EE, r_sa, r_s, A24[r_s], OFF[r_s], mit_k4="K4" in varianten, fertig=fertig)
        aus = {}
        for v in varianten:
            c_tr, c_te = s["beitr"](r_sa, OFF[r_sa], v), s["beitr"](r_pa, OFF[r_pa], v)
            aus[v] = dict(oben=dq(r_pa[c_te >= np.quantile(c_tr, 0.9)]), eigen=dq(r_pa[c_te >= np.quantile(c_te, 0.9)]),
                          c_tr=c_tr)
        return aus, s

    def verschoben(EE, nur):
        aus = dict(EE)
        rr = {}
        for tl in teile:
            L = len(tl)
            rr[int(SYM[tl[0]])] = int(rng.integers(K2.MIN_VERSATZ, L - K2.MIN_VERSATZ)) if L > 2 * K2.MIN_VERSATZ else 0
        for k in nur:
            v = np.empty(n)
            for tl in teile:
                v[tl] = np.roll(EE[k][tl], rr[int(SYM[tl[0]])])
            aus[k] = v
        return aus

    # ══ TOR (Nachtrag 29.09., Voranalyse Abschnitt 5 - VOR der Auswertung festgelegt) ══
    if "--tor" in sys.argv:
        r0, s0 = fest(E, varianten=("K0",))
        rsi_mod0 = {"rsi": s0["mods"]["rsi"]}

        def bestes(EE, y=A24):
            s = schaetze(EE, r_sa, r_s, y[r_s], OFF[r_s], mit_k4=False, fertig=rsi_mod0)
            e = {}
            for v in ("K0", "K1", "K2", "K3"):
                c_te = s["beitr"](r_pa, OFF[r_pa], v)
                e[v] = dq(r_pa[c_te >= np.quantile(c_te, 0.9)], y)
            return max(e[v] - e["K0"] for v in ("K1", "K2", "K3"))
        null = np.array([bestes(verschoben(E, LAGE_SP)) for _ in range(zieh)])
        grenze = float(np.nanpercentile(null, 90))
        print()
        print("TOR Bestes-von-3-Differenz mit verschobener Lage: Nullwelt Mittel %+.4f, Streuung %.4f, 90. Perzentil %+.4f" % (
            float(np.nanmean(null)), float(np.nanstd(null, ddof=1)), grenze))
        erg = {}
        for d in (0.02, 0.04):
            gef, werte = 0, []
            for _ in range(5):
                EV = verschoben(E, LAGE_SP)
                gr = np.nanpercentile(EV["oi_24"][r_sa], 90)
                y = A24.copy()
                oben = np.flatnonzero((EV["oi_24"] >= gr) & HIT & (such | pruef))
                kand = oben[B24[oben] == 1]
                w = rng.choice(kand, size=min(int(round(d * len(oben))), len(kand)), replace=False)
                y[w] = 1.0
                dd = bestes(EV, y)
                werte.append(dd); gef += int(dd > grenze)
            erg[d] = gef
            print("  gepflanzt +%.2f auf P90+ von oi_24 (Lage verschoben): %s -> gefunden %d von 5" % (
                d, " ".join("%+.4f" % x for x in werte), gef))
        print("  TOR: %s" % ("✔ BESTANDEN" if erg[0.04] >= 4 else "⛔ NICHT BESTANDEN - S1 bleibt Auskunft"))
        print("SCHLUSS: vollstaendig")
        return 0

    # ══ F1 FESTE TEILUNG ════════════════════════════════════════════════
    haupt, sh = fest(E)
    soll = RR11_2680.get(E2.MENGE)
    print()
    print("S0 R-R11: K0 rsi allein oben %+.4f · 2.680: %s -> %s" % (
        haupt["K0"]["oben"], "%+.4f" % soll if soll is not None else "-",
        ("✔ bitgleich" if soll is not None and abs(round(haupt["K0"]["oben"], 4) - soll) < 1e-9 else "⛔ ABWEICHUNG")
        if soll is not None else "(kein Vergleichswert)"))
    print("  Gewichte K2 (Training): %s · K3 (OOF, >= 0): %s" % (
        ", ".join("%s %+.3f" % (f_, w) for f_, w in zip(FAMILIEN, sh["g2"][1:])),
        ", ".join("%s %+.3f" % (f_, w) for f_, w in zip(FAMILIEN, sh["g3"][1:]))))
    rsi_mod = {"rsi": sh["mods"]["rsi"]}
    nullmax, nullv = [], {v: [] for v in ("K1", "K2", "K3")}
    for _ in range(zieh):
        EV = verschoben(E, LAGE_SP)
        r_, _s = fest(EV, varianten=("K0", "K1", "K2", "K3"), fertig=rsi_mod)
        d_ = {v: r_[v]["eigen"] - r_["K0"]["eigen"] for v in ("K1", "K2", "K3")}
        for v in d_:
            nullv[v].append(d_[v])
        nullmax.append(max(d_.values()))
    gB = float(np.nanpercentile(nullmax, 90))
    print()
    print("=" * 120)
    print("F1 FESTE TEILUNG Suche 2023-2024 -> Pruefung 2025-01..2026-08 (eigenes Zehntel, Differenz zu rsi allein)")
    print("  Nullband Bestes-von-3 (nur Lage verschoben, %d Ziehungen): 90. Perzentil %+.4f · je Variante %s" % (
        zieh, gB, " · ".join("%s %+.4f" % (v, float(np.nanpercentile(x, 90))) for v, x in nullv.items())))
    for v in VARIANTEN:
        d = haupt[v]["eigen"] - haupt["K0"]["eigen"]
        print("  %s %-18s oben %+.4f · eigenes Zehntel %+.4f · Differenz %+.4f%s" % (
            v, NAMEN[v], haupt[v]["oben"], haupt[v]["eigen"], d,
            "" if v in ("K0",) else (" -> ✔ ueber dem Band" if v != "K4" and d > gB else (" (Kontrolle)" if v == "K4" else " -> ·"))))
    # 2022 mit Moment-Bezug
    r22 = np.flatnonzero(GRID & (JAHR == 2022) & np.isfinite(OFF_M))
    d22 = {}
    if len(r22):
        for v in VARIANTEN:
            c22 = sh["beitr"](r22, OFF_M[r22], v)
            d22[v] = dq(r22[c22 >= np.quantile(haupt[v]["c_tr"], 0.9)], A24, MA, MB)
        print("  2022 (Moment-Bezug) oben: %s" % " · ".join("%s %+.4f" % (v, x) for v, x in d22.items()))

    # ══ F5 WIRKUNGSKURVEN ═══════════════════════════════════════════════
    print()
    print("=" * 120)
    print("F5 WIRKUNGSKURVEN je Beitrag (feste Teilung, Familie einzeln; Log-Odds je Stufe relativ zur mittleren Stufe)")
    perz = ("<P1",) + tuple("P%d-%d" % (a, b) for a, b in zip(K2.PERZ12[:-1], K2.PERZ12[1:])) + (">P99",)
    for f_, ks in FAMILIEN.items():
        m = sh["mods"][f_]
        for j, k in enumerate(m.namen):
            w = m.w[1 + m.ofs[j]: 1 + m.ofs[j + 1]]
            w = w - np.median(w)
            g = m.grenzen[j]
            print("  %-8s %-7s %s" % (f_, k, " ".join("%s:%+.2f" % (p, x) for p, x in zip(perz, w))))
            print("  %-8s %-7s Grenzen %s" % ("", "", " ".join("%.4g" % x for x in g)))

    # ══ ROLLIEREND ══════════════════════════════════════════════════════
    print()
    print("=" * 120)
    print("ROLLIEREND, WACHSEND: %d Monate" % len(monate))
    Z = {v: np.full(n, np.nan) for v in VARIANTEN}
    SEL = {v: np.zeros(n, bool) for v in VARIANTEN}
    DRITTEL = np.full(n, -1, np.int8)
    ab = H(datetime(2023, 1, 1))
    for (j, mo) in monate:
        mi = j * 12 + (mo - 1)
        start = H(datetime(j, mo, 1))
        fen = BASIS & (STD >= ab) & (MON < mi) & (STD < start - 24)
        ra = np.flatnonzero(fen); rt = np.flatnonzero(fen & HIT)
        ziel = np.flatnonzero(BASIS & (MON == mi))
        if len(rt) < 5000 or not len(ziel):
            continue
        s = schaetze(E, ra, rt, A24[rt], OFF[rt])
        for v in VARIANTEN:
            ct = s["beitr"](ra, OFF[ra], v); cz = s["beitr"](ziel, OFF[ziel], v)
            Z[v][ziel] = cz; SEL[v][ziel] = cz >= np.quantile(ct, 0.9)
        q1, q2 = np.nanquantile(QN[ra], (1 / 3, 2 / 3))
        DRITTEL[ziel] = np.where(QN[ziel] <= q1, 0, np.where(QN[ziel] <= q2, 1, 2))
    alle = np.flatnonzero(np.isfinite(Z["K0"]))
    eig = {v: dq(alle[Z[v][alle] >= np.quantile(Z[v][alle], 0.9)]) for v in VARIANTEN}
    print("  gleicher Anteil (oberstes Zehntel im Test): %s" % " · ".join("%s %+.4f" % (v, eig[v]) for v in VARIANTEN))
    best, bestd = None, -np.inf
    for v in ("K1", "K2", "K3"):
        d = eig[v] - eig["K0"]
        print("  %s %-18s Differenz zu rsi allein %+.4f gegen Band %+.4f -> %s" % (v, NAMEN[v], d, gB, "✔" if d > gB else "·"))
        dfest = haupt[v]["eigen"] - haupt["K0"]["eigen"]
        if d > gB and dfest > gB and d > bestd:
            best, bestd = v, d
    print("  S1: %s" % ("✔ %s %s schlaegt rsi allein fest und rollierend" % (best, NAMEN[best]) if best else
                        "· keine Variante schlaegt rsi allein fest UND rollierend"))
    print("  S2 Kontrolle K4 gemeinsam: Differenz %+.4f" % (eig["K4"] - eig["K0"]))
    # S4 Zeit fuer die beste (oder, falls keine, fuer K3 als Auskunft) und K0
    btc = reihe([(E2.EINGESTELLT_DB, "SELECT stunde, close FROM stundenkurse WHERE symbol='BTC'"),
                 (E2.STUNDEN_DB, "SELECT stunde, close FROM stundenkurse WHERE symbol='BTC'")])
    b30 = np.full(n, np.nan)
    okb = (STD < len(btc)) & (STD >= 720)
    with np.errstate(divide="ignore", invalid="ignore"):
        b30[okb] = btc[STD[okb]] / btc[STD[okb] - 720] - 1.0
    bb = b30[alle]; fin = np.isfinite(bb)
    bq1, bq2 = np.quantile(bb[fin], (1 / 3, 2 / 3))
    for v in dict.fromkeys(([best] if best else []) + ["K3", "K0"]):
        sel = alle[SEL[v][alle]]
        w4, z4 = [], []
        for jj in (2024, 2025, 2026):
            x = dq(sel[JAHR[sel] == jj]); w4.append(x); z4.append("%d %+.4f" % (jj, x))
        for nm, lo_, hi_ in (("BTC tief", -np.inf, bq1), ("BTC mitte", bq1, bq2), ("BTC hoch", bq2, np.inf)):
            s_ = sel[np.isfinite(b30[sel]) & (b30[sel] > lo_) & (b30[sel] <= hi_)]
            x = dq(s_); w4.append(x); z4.append("%s %+.4f" % (nm, x))
        x22 = d22.get(v, np.nan); w4.append(x22); z4.append("2022 %+.4f" % x22)
        t6 = [dq(sel[DRITTEL[sel] == d_]) for d_ in (0, 1, 2)]
        ga = np.array([dq(sel[SYM[sel] == si]) for si in np.unique(SYM[sel]) if (SYM[sel] == si).sum() >= 50])
        print("  S4 %s %-18s %s -> %s · Normal-Drittel %s · Assets > 0: %.0f %%" % (
            v, NAMEN[v], " · ".join(z4), "✔ zeitstabil" if np.nanmin(w4) > 0 and np.isfinite(x22) else "⛔ nicht zeitstabil",
            " / ".join("%+.4f" % x for x in t6), 100 * np.mean(ga > 0) if len(ga) else np.nan))

    # ══ F2 KALIBRIERUNG ═════════════════════════════════════════════════
    print()
    print("=" * 120)
    print("F2 KALIBRIERUNG aus UNGESEHENEN Schaetzungen (nur Ausgaenge vor dem Zielmonat bekannt)")
    dy_all = A24 - QN
    ev_all = alle[HIT[alle]]

    def bekannt(quelle, mi):
        j_, m_ = divmod(int(mi), 12)
        return quelle[STD[quelle] < H(datetime(j_, m_ + 1, 1)) - 24]

    def platt(v, lang=24, kurz=3, nachfuehren=True):
        out = np.full(n, np.nan)
        for mi in np.unique(MON[alle]):
            ziel = alle[MON[alle] == mi]
            hist = bekannt(ev_all[(MON[ev_all] >= mi - lang) & (MON[ev_all] < mi)], mi)
            if len(np.unique(MON[hist])) < 6:
                continue
            s_h, o_h, y_h = Z[v][hist], OFF[hist], A24[hist]

            def f(p, s_, o_, y_, b_fest=None):
                b = p[1] if b_fest is None else b_fest
                z = o_ + p[0] + b * s_
                r = expit(z) - y_
                val = float(np.sum(np.logaddexp(0.0, z) - y_ * z))
                g = [r.sum()] + ([float(r @ s_)] if b_fest is None else [])
                return val, np.array(g)
            ab_ = minimize(f, np.r_[0.0, 1.0], args=(s_h, o_h, y_h), jac=True, method="L-BFGS-B").x
            a_, b_ = ab_
            if nachfuehren:
                kz = bekannt(ev_all[(MON[ev_all] >= mi - kurz) & (MON[ev_all] < mi)], mi)
                if len(kz) >= 500:
                    a_ = minimize(lambda p: f(np.r_[p[0], 0.0], Z[v][kz], OFF[kz], A24[kz], b_fest=b_),
                                  np.r_[a_], jac=True, method="L-BFGS-B").x[0]
            out[ziel] = expit(OFF[ziel] + a_ + b_ * Z[v][ziel]) - expit(OFF[ziel])
        return out

    def pav(y_, w_):
        y_, w_ = list(y_), list(w_)
        i = 0
        while i < len(y_) - 1:
            if y_[i] > y_[i + 1]:
                yy = (y_[i] * w_[i] + y_[i + 1] * w_[i + 1]) / (w_[i] + w_[i + 1])
                y_[i:i + 2] = [yy]; w_[i:i + 2] = [w_[i] + w_[i + 1]]
                i = max(i - 1, 0)
            else:
                i += 1
        return y_, w_

    def monoton(v, G):
        out = np.full(n, np.nan)
        for mi in np.unique(MON[alle]):
            ziel = alle[MON[alle] == mi]
            q = ev_all[(MON[ev_all] >= mi - G) & (MON[ev_all] < mi)]
            if len(np.unique(MON[q])) < G:
                continue
            q = bekannt(q, mi)
            s_q, y_q = Z[v][q], dy_all[q]
            ok = np.isfinite(s_q) & np.isfinite(y_q)
            s_q, y_q = s_q[ok], y_q[ok]
            if len(s_q) < 2000:
                continue
            kan = np.quantile(s_q, np.linspace(0, 1, 21))
            kb = np.clip(np.searchsorted(kan, s_q, "right") - 1, 0, 19)
            cnt = np.bincount(kb, minlength=20).astype(float)
            mw = np.bincount(kb, weights=y_q, minlength=20) / np.maximum(cnt, 1)
            mit = np.bincount(kb, weights=s_q, minlength=20) / np.maximum(cnt, 1)
            gut = cnt > 0
            yy, ww = pav(mw[gut], cnt[gut])
            xm, cm = mit[gut], cnt[gut]
            xs, k0 = [], 0
            for wv in ww:
                acc, idx = 0.0, []
                while acc < wv - 1e-9 and k0 < len(xm):
                    acc += cm[k0]; idx.append(k0); k0 += 1
                xs.append(float(np.average(xm[idx], weights=cm[idx])))
            out[ziel] = np.interp(Z[v][ziel], xs, yy)
        return out

    def t3(bv, ev):
        b = bv[ev]; dy = dy_all[ev]
        ok = np.isfinite(b) & np.isfinite(dy)
        ev, b, dy = ev[ok], b[ok], dy[ok]
        if len(ev) < 1000:
            return np.nan, np.nan, np.nan, ""
        db, ddy = b.copy(), dy.copy()
        for mi in np.unique(MON[ev]):
            k = MON[ev] == mi
            db[k] -= b[k].mean(); ddy[k] -= dy[k].mean()
        dz = np.quantile(db, np.linspace(0, 1, 11))
        kb = np.clip(np.searchsorted(dz, db, "right") - 1, 0, 9)
        cnt = np.bincount(kb, minlength=10)
        mp = np.bincount(kb, weights=db, minlength=10) / np.maximum(cnt, 1)
        mo_ = np.bincount(kb, weights=ddy, minlength=10) / np.maximum(cnt, 1)
        wt = cnt / cnt.sum()
        sl = np.sum(wt * (mp - np.sum(wt * mp)) * (mo_ - np.sum(wt * mo_))) / max(np.sum(wt * (mp - np.sum(wt * mp)) ** 2), 1e-12)
        top = b >= np.quantile(b, 0.9)
        je = []
        for jj in (2024, 2025, 2026):
            kj = (JAHR[ev] == jj) & top
            if kj.sum() >= 200:
                je.append("%d %+.3f|%+.3f" % (jj, b[kj].mean(), dy[kj].mean()))
        return sl, b[top].mean(), dy[top].mean(), " / ".join(je)

    for v in dict.fromkeys(([best] if best and best != "K0" else []) + ["K3", "K0"]):
        kal = {"Platt 24/3": platt(v), "Platt 24 ohne Nachfuehrung": platt(v, nachfuehren=False),
               "monoton 3": monoton(v, 3), "monoton 12": monoton(v, 12)}
        gem = ev_all.copy()
        for x in kal.values():
            gem = gem[np.isfinite(x[gem])]
        roh = np.full(n, np.nan); roh[alle] = expit(OFF[alle] + Z[v][alle]) - expit(OFF[alle])
        sl, ge, be, _ = t3(roh, gem)
        print("  %s %-18s roh: Steigung %.2f · oberstes Zehntel geschaetzt %+.4f beobachtet %+.4f (gemeinsame Monate, %d Ereignisse)" % (
            v, NAMEN[v], sl, ge, be, len(gem)))
        for nm, x in kal.items():
            sl, ge, be, je = t3(x, gem)
            ok3 = 0.7 <= sl <= 1.3 and abs(ge - be) <= 0.02
            print("     %-27s Steigung %.2f · oberstes Zehntel %+.4f / %+.4f -> %s · je Jahr %s" % (
                nm, sl, ge, be, "✔ S3" if ok3 else "·", je))

    # ══ F3 PBO ══════════════════════════════════════════════════════════
    print()
    print("=" * 120)
    mons = np.unique(MON[alle])
    M = np.array([[dq(alle[(MON[alle] == mi) & SEL[v][alle]]) for v in VARIANTEN] for mi in mons])
    ok_m = np.all(np.isfinite(M), axis=1)
    M = M[ok_m]
    S = 8
    gruppen = np.array_split(np.arange(len(M)), S)
    unter, lam_ = 0, []
    kombis = list(itertools.combinations(range(S), S // 2))
    for c in kombis:
        is_ = np.concatenate([gruppen[i] for i in c]); oos = np.concatenate([gruppen[i] for i in range(S) if i not in c])
        bi = int(np.argmax(M[is_].mean(axis=0)))
        rang = (M[oos].mean(axis=0) < M[oos].mean(axis=0)[bi]).sum() + 1      # 1 = schlechteste
        w = rang / (len(VARIANTEN) + 1)
        lam_.append(np.log(w / (1 - w)))
        unter += int(w <= 0.5)
    print("F3 PBO (CSCV, %d Monate in %d Gruppen, %d Aufteilungen, Varianten %s): PBO %.2f · Median logit %.2f" % (
        len(M), S, len(kombis), "/".join(VARIANTEN), unter / len(kombis), float(np.median(lam_))))
    print("   Monatsmittel je Variante: %s" % " · ".join("%s %+.4f" % (v, x) for v, x in zip(VARIANTEN, M.mean(axis=0))))

    # ══ F4 NORMAL-SCHRUMPFUNG ═══════════════════════════════════════════
    print()
    print("=" * 120)
    print("F4 EMPIRICAL-BAYES-SCHRUMPFUNG DES PHASE-NORMALS (Abnahmeprobe: oberstes Normal-Zehntel je Monat)")
    basis = np.flatnonzero(BASIS & (MON >= 2024 * 12))          # ab 2024: das Phase-Normal braucht 12 Monate
    QS = np.full(n, np.nan)
    Bw = []
    for mi in np.unique(MON[basis]):
        ix = basis[MON[basis] == mi]
        q = QN[ix]; ok = np.isfinite(q)
        ix, q = ix[ok], q[ok]
        if len(ix) < 500:
            continue
        # je Asset ein Wert (Monatsmittel des Normals), Rauschen aus der effektiven Ereigniszahl
        sy = SYM[ix]
        us, inv = np.unique(sy, return_inverse=True)
        qa = np.bincount(inv, weights=q) / np.bincount(inv)
        rate = np.bincount(inv, weights=(NA[ix] + NB[ix])) / np.bincount(inv)
        n_eff = np.maximum(rate * 365.0, 5.0)
        rausch = qa * (1 - qa) / n_eff
        mitte = float(np.mean(qa))
        tau2 = max(float(np.var(qa)) - float(np.mean(rausch)), 0.0)
        B = tau2 / (tau2 + rausch)
        Bw.append(float(np.median(B)))
        QS[ix] = mitte + B[inv] * (q - mitte)
    ms = np.flatnonzero(np.isfinite(QS))
    NAs, NBs = QS * (NA + NB), (1 - QS) * (NA + NB)
    top, bot = np.zeros(n, bool), np.zeros(n, bool)
    for mi in np.unique(MON[ms]):
        ix = ms[MON[ms] == mi]
        g9, g1 = np.quantile(QN[ix], (0.9, 0.1))
        top[ix] = QN[ix] >= g9; bot[ix] = QN[ix] <= g1
    t_, b_ = ms[top[ms]], ms[bot[ms]]
    roh_o, roh_u = dq(t_), dq(b_)
    sch_o, sch_u = dq(t_, A24, NAs, NBs), dq(b_, A24, NAs, NBs)
    print("  Schrumpfungsfaktor B (Median je Monat): %.2f bis %.2f" % (min(Bw), max(Bw)))
    print("  oberstes Normal-Zehntel: beobachtet minus Normal roh %+.4f · minus geschrumpftes Normal %+.4f" % (roh_o, sch_o))
    print("  unterstes Normal-Zehntel: roh %+.4f · geschrumpft %+.4f" % (roh_u, sch_u))
    print("  S6 -> %s" % ("✔ die Rueckkehr zur Mitte ist mindestens halbiert" if abs(sch_o) <= abs(roh_o) / 2 else
                           "⛔ die Schrumpfung behebt die Rueckkehr nicht"))
    print()
    print("  ⚠️ Gebuehren und Finanzierung sind nicht eingerechnet (Regel 2).")
    print("SCHLUSS: vollstaendig")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
