# -*- coding: utf-8 -*-
"""K5 NEU - Lage mit Vorlauf und rsi jetzt, additiv, einzeln geschaetzt, nachkalibriert (29.09.2026).

Voranalyse `Basisinfos/Voranalyse_K5_neu_Lage_mit_Vorlauf_29_09.md`, abgestimmt
(*ja, V1 bis V10 wie empfohlen*). Datenaufbereitung WOERTLICH aus 2c
(messe_k1_schritt2c_beitrag.py), damit rsi allein bitgleich reproduziert (T1).

VORAB FESTGELEGT
    V1  Ausloeser rsi-Familie (rsi_s, rsi_s24), wie 2c
    V2  Lage: funding_vortag, oi_aenderung, konten_verh - ROH, in der Form, in
        der sie als Traeger gemessen sind (2.651/2.663)
    V3  Fenster statt Punktwert: je Beitrag drei Bloecke 0-24, 24-48, 48-72 h
        (funding: Tag -1/-2/-3; oi_aenderung ist schon eine 24-h-Aenderung ->
        ihre Werte bei 0/24/48 h; konten_verh: 24-h-Mittel bei 0/24/48 h);
        die drei Bloecke sind EINE Familie, kein bestes Fenster wird gewaehlt
    V4  jede Familie einzeln (eigene Daempfung, Gitter bis 2.000.000), dann EIN
        Gewicht je Familie (Stacking auf dem Training)
    V5  q5, Phase-Normal, vier Mengen
    V6  Nachkalibrierung: monotone Uebersetzung Beitrag -> beobachteter
        Vorsprung, aus den UNGESEHENEN Schaetzungen der letzten 3 bzw. 12 Monate
    V7  Zeit: T4 in jedem Jahr 2024-2026 UND 2022; Z3 das tragende Fenster je Jahr
    V8  Nullwelt Zeitverschiebung je Asset (40); T2-Nullwelt verschiebt NUR die
        Lage (rsi bleibt echt); Regeltest Zufallslage; Tor gepflanzt auf einer
        Lage-Spalte
    V9  funding als Vortag; Gegenprobe Eingaenge 1 h aelter
BAUENTSCHEIDUNGEN (vor den Laeufen, Abschnitt 10 der Voranalyse)
    B1  T2 rollierend: Differenz gegen das Nullband der FESTEN Teilung (eine
        rollierende Nullwelt mit 40 Ziehungen waere Tage Rechnung)
    B2  Nachkalibrierung nur aus ungesehenen Schaetzungen; Monate ohne genug
        Vorgeschichte gehen nicht in T3 ein; Z4-Vergleich auf gemeinsamen Monaten
    B3  Stacking auf den Trainingsschaetzungen der Familien (nicht out-of-fold)

    python messe_k5_lage_vorlauf.py --menge bestand --tor
    python messe_k5_lage_vorlauf.py --menge unverzerrt:1
"""
from __future__ import annotations

import os
import sqlite3
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
# 2.680, feste Teilung, rsi allein oben (T1 / R-R11)
RR11_2680 = {"bestand": 0.0808, "unverzerrt:1": 0.0696, "unverzerrt:2": 0.0700, "unverzerrt:3": 0.0703}
ZIEHUNGEN, SAAT = 40, 20260929
H = K2._h
SUCHE, PRUEF, ROLL = K2.SUCHE, K2.PRUEF, K2.ROLL_MONATE
RSI = ("rsi_s", "rsi_s24")
LAGE = {"funding": ("fu_0", "fu_24", "fu_48"),
        "oi": ("oi_0", "oi_24", "oi_48"),
        "konten": ("ko_0", "ko_24", "ko_48")}
LAGE_SP = tuple(x for f in LAGE.values() for x in f)
FAMILIEN = {"rsi": RSI, **LAGE}
GEDAECHTNIS = (3, 12)


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:                                         # noqa: BLE001
        pass
    E2.menge_aus_argv()
    K2.FORM = "b"
    K2.LAMBDAS = GITTER_NEU
    tor = "--tor" in sys.argv
    probe = "--probe" in sys.argv
    zieh = 3 if probe else ZIEHUNGEN
    monate = ROLL[:6] if probe else ROLL
    print("=" * 120)
    print("K5 NEU - LAGE MIT VORLAUF + rsi JETZT · MENGE %s%s" % (
        E2.MENGE, " · TOR" if tor else (" · WERKZEUGTEST" if probe else "")))
    print("=" * 120)
    # ── Aufbereitung WOERTLICH wie 2c ────────────────────────────────────
    D = E2.lade(hmax=72, erste=(("u5", 1.05, True), ("d5", 0.95, False)), mit_atr=True)
    SYM, STD, syms = D["SYM"], D["STD"], D["syms"]
    n = len(SYM)
    t_u, t_d = D["T"]["u5"], D["T"]["d5"]
    A24 = ((t_u <= 24) & (t_u < t_d)).astype(np.float64)
    B24 = ((t_d <= 24) & (t_d <= t_u)).astype(np.float64)
    ATR = D["ATR"]; VOR24 = D["X"]["vor24"]
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
        """24-h-Mittel bis einschliesslich der Stunde (wie der Wert zur Stunde selbst)."""
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
    with np.errstate(divide="ignore", invalid="ignore"):
        ANST = VOR24 / np.maximum(ATR, 1e-12)
    GRID = np.isin(STD % 24, K2.GITTER)
    BASIS = GRID & np.isfinite(OFF)
    HIT = (A24 + B24) > 0
    such = BASIS & (STD >= SUCHE[0]) & (STD < SUCHE[1])
    pruef = BASIS & (STD >= PRUEF[0]) & (STD < PRUEF[1])
    with np.errstate(divide="ignore", invalid="ignore"):
        QN = NA / (NA + NB)
    print("  Anker (Gitter, mit Phase-Normal): Suche %d · Pruefung %d · Symbole %d" % (
        such.sum(), pruef.sum(), len(np.unique(SYM[such | pruef]))))
    print("  Abdeckung Lage (Anteil der Pruefanker mit Wert): %s" % " · ".join(
        "%s %.0f %%" % (k, 100 * np.mean(np.isfinite(E[k][pruef]))) for k in LAGE_SP))

    def dq(ix, y=A24, na=NA, nb=NB):
        if not len(ix):
            return np.nan
        a = y[ix].sum(); b = (HIT[ix] & (y[ix] == 0)).sum()
        sa, sb = na[ix].sum(), nb[ix].sum()
        return a / max(a + b, 1e-12) - sa / max(sa + sb, 1e-12)

    r_sa = np.flatnonzero(such); r_s = np.flatnonzero(such & HIT); r_pa = np.flatnonzero(pruef)

    def stapel(C, y, off):
        """ein Gewicht je Familie: z = off + a + sum w_f c_f (V4)."""
        M = np.column_stack(C)

        def f(p):
            z = off + p[0] + M @ p[1:]
            r = expit(z) - y
            return float(np.sum(np.logaddexp(0.0, z) - y * z)), np.concatenate([[r.sum()], M.T @ r])
        return minimize(f, np.r_[0.0, np.ones(M.shape[1])], jac=True, method="L-BFGS-B").x

    def kombi(EE, ra, rt, y, off, fam=FAMILIEN):
        """-> dict(modelle, gew, lam) - Familien einzeln, dann gestapelt."""
        mods, lams = {}, {}
        for f_, ks in fam.items():
            mods[f_], lams[f_] = K2.fit_cv(ks, EE, ra, rt, y, off, STD)
        C = [mods[f_].z(EE, rt, off) - off for f_ in fam]
        return dict(m=mods, gew=stapel(C, y, off), lam=lams, fam=tuple(fam))

    def score(k, EE, rows, off, ohne=()):
        """Beitrag (Log-Odds gegen das Normal) der gestapelten Kombination."""
        s = np.full(len(rows), k["gew"][0])
        for i, f_ in enumerate(k["fam"]):
            if f_ in ohne:
                continue
            s = s + k["gew"][1 + i] * (k["m"][f_].z(EE, rows, off) - off)
        return s

    def fest(EE, y=A24, fam=FAMILIEN):
        k = kombi(EE, r_sa, r_s, y[r_s], OFF[r_s], fam)
        c_tr, c_te = score(k, EE, r_sa, OFF[r_sa]), score(k, EE, r_pa, OFF[r_pa])
        e_hi = np.quantile(c_te, 0.9)
        rs_tr = k["m"]["rsi"].z(EE, r_sa, OFF[r_sa]) - OFF[r_sa]
        rs_te = k["m"]["rsi"].z(EE, r_pa, OFF[r_pa]) - OFF[r_pa]
        return dict(k=k, c_tr=c_tr, c_te=c_te,
                    oben=dq(r_pa[c_te >= np.quantile(c_tr, 0.9)], y),
                    unten=dq(r_pa[c_te <= np.quantile(c_tr, 0.1)], y),
                    eigen=dq(r_pa[c_te >= e_hi], y),
                    rsi_oben=dq(r_pa[rs_te >= np.quantile(rs_tr, 0.9)], y),
                    rsi_eigen=dq(r_pa[rs_te >= np.quantile(rs_te, 0.9)], y))

    def verschoben(EE, nur=None):
        aus = dict(EE)
        rr = {}
        for tl in teile:
            L = len(tl)
            rr[int(SYM[tl[0]])] = int(rng.integers(K2.MIN_VERSATZ, L - K2.MIN_VERSATZ)) if L > 2 * K2.MIN_VERSATZ else 0
        for k in (nur if nur is not None else EE.keys()):
            v = np.empty(n)
            for tl in teile:
                v[tl] = np.roll(EE[k][tl], rr[int(SYM[tl[0]])])
            aus[k] = v
        return aus

    # ══ T1 / R-R11: rsi allein bitgleich zu 2.680 ═══════════════════════
    haupt = fest(E)
    soll = RR11_2680.get(E2.MENGE)
    print()
    print("T1 R-R11: rsi allein oben %+.4f · 2.680: %s -> %s" % (
        haupt["rsi_oben"], "%+.4f" % soll if soll is not None else "-",
        ("✔ bitgleich" if soll is not None and abs(round(haupt["rsi_oben"], 4) - soll) < 1e-9 else "⛔ ABWEICHUNG")
        if soll is not None else "(kein Vergleichswert)"))
    print("  Daempfung je Familie: %s · Gewichte: Achse %+.3f, %s" % (
        " · ".join("%s %.0f%s" % (f_, l_, " (RAND)" if l_ == GITTER_NEU[-1] else "") for f_, l_ in haupt["k"]["lam"].items()),
        haupt["k"]["gew"][0], ", ".join("%s %+.3f" % (f_, w_) for f_, w_ in zip(haupt["k"]["fam"], haupt["k"]["gew"][1:]))))

    # T2-Nullband: nur die Lage verschoben, rsi echt
    def t2_diff(EE, y=A24):
        r_ = fest(EE, y)
        return r_["eigen"] - r_["rsi_eigen"], r_

    # ══ TOR ═════════════════════════════════════════════════════════════
    if tor:
        null_d = np.array([t2_diff(verschoben(E, LAGE_SP))[0] for _ in range(zieh)])
        grenze = float(np.nanpercentile(null_d, 90))
        print()
        print("TOR (V8) T2-Differenz mit verschobener Lage: Nullwelt Mittel %+.4f, Streuung %.4f, 90. Perzentil %+.4f" % (
            float(np.nanmean(null_d)), float(np.nanstd(null_d, ddof=1)), grenze))
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
                dd = t2_diff(EV, y)[0]
                werte.append(dd); gef += int(dd > grenze)
            erg[d] = gef
            print("  gepflanzt +%.2f auf P90+ von oi_24 (Lage verschoben): %s -> gefunden %d von 5" % (
                d, " ".join("%+.4f" % x for x in werte), gef))
        print("  TOR: %s" % ("✔ BESTANDEN" if erg[0.04] >= 4 else "⛔ NICHT BESTANDEN - kein Urteil"))
        print("SCHLUSS: vollstaendig")
        return 0

    # ══ FESTE TEILUNG ═══════════════════════════════════════════════════
    nO, nD = [], []
    for _ in range(zieh):
        nO.append(fest(verschoben(E))["oben"])
        nD.append(t2_diff(verschoben(E, LAGE_SP))[0])
    nO, nD = np.array(nO), np.array(nD)
    g1, g2 = float(np.nanpercentile(nO, 90)), float(np.nanpercentile(nD, 90))
    d2 = haupt["eigen"] - haupt["rsi_eigen"]
    print()
    print("=" * 120)
    print("FESTE TEILUNG Suche 2023-2024 -> Pruefung 2025-01..2026-08")
    print("  rsi + Lage   oben %+.4f · unten %+.4f · eigenes Zehntel %+.4f" % (haupt["oben"], haupt["unten"], haupt["eigen"]))
    print("  rsi allein   oben %+.4f · eigenes Zehntel %+.4f" % (haupt["rsi_oben"], haupt["rsi_eigen"]))
    print("  Nullwelt (alles verschoben): 90. Perzentil %+.4f -> Auswahl %s" % (g1, "✔ jenseits" if haupt["oben"] > g1 else "· nicht jenseits"))
    print("  T2 fest: rsi+Lage minus rsi allein %+.4f gegen Nullband (nur Lage verschoben) Mittel %+.4f, 90. Perzentil %+.4f -> %s" % (
        d2, float(np.nanmean(nD)), g2, "✔ Lage bringt etwas dazu" if d2 > g2 else "· Lage bringt nichts dazu"))
    lo_k = [f_ for f_ in LAGE]
    c_lage_tr = score(haupt["k"], E, r_sa, OFF[r_sa], ohne=("rsi",))
    c_lage_te = score(haupt["k"], E, r_pa, OFF[r_pa], ohne=("rsi",))
    print("  T7 nur die Lage (ohne rsi): oben %+.4f (Anteil %.1f %%) · eigenes Zehntel %+.4f" % (
        dq(r_pa[c_lage_te >= np.quantile(c_lage_tr, 0.9)]), 100 * np.mean(c_lage_te >= np.quantile(c_lage_tr, 0.9)),
        dq(r_pa[c_lage_te >= np.quantile(c_lage_te, 0.9)])))
    for f_ in lo_k:
        r1 = fest(E, fam={"rsi": RSI, f_: LAGE[f_]})
        print("     Weglassprobe: rsi + nur %-8s eigenes Zehntel %+.4f (Differenz zu rsi allein %+.4f)" % (
            f_, r1["eigen"], r1["eigen"] - r1["rsi_eigen"]))
    # Z3: welches Fenster traegt (je Jahr der Pruefung)
    print("  Z3 je Fenster allein (oberstes Zehntel, 2025 / 2026):")
    for f_, ks in LAGE.items():
        zz = []
        for kk in ks:
            m1, _l = K2.fit_cv((kk,), E, r_sa, r_s, A24[r_s], OFF[r_s], STD)
            c1t = m1.z(E, r_sa, OFF[r_sa]) - OFF[r_sa]; c1 = m1.z(E, r_pa, OFF[r_pa]) - OFF[r_pa]
            s1 = r_pa[c1 >= np.quantile(c1t, 0.9)]
            zz.append("%s %+.4f / %+.4f" % (kk, dq(s1[JAHR[s1] == 2025]), dq(s1[JAHR[s1] == 2026])))
        print("     %-8s %s" % (f_, " · ".join(zz)))
    # R Zufallslage
    rz = np.random.default_rng(SAAT + 1)
    EZ = dict(E)
    for i, k in enumerate(LAGE_SP):
        x = rz.standard_normal(n); v = np.empty(n); g_ = (6, 24, 48)[i % 3]
        for tl in teile:
            c = np.concatenate([[0.0], np.cumsum(x[tl])]); kk = np.arange(1, len(tl) + 1)
            v[tl] = (c[kk] - c[np.maximum(0, kk - g_)]) / np.minimum(kk, g_)
        EZ[k] = v
    dz = t2_diff(EZ)[0]
    print("  R  Zufallslage: T2-Differenz %+.4f gegen %+.4f -> %s" % (dz, g2, "✔ im Nullband" if dz <= g2 else "⛔ JENSEITS"))
    E1 = {k: alt(v, 1) for k, v in E.items()}
    print("  V9 Eingaenge 1 h aelter: rsi + Lage oben %+.4f" % fest(E1)["oben"])
    # 2022 (Moment-Bezug; das Phase-Normal braucht 12 Monate Vorgeschichte)
    r22 = np.flatnonzero(GRID & (JAHR == 2022) & np.isfinite(OFF_M))
    d22 = r22_rsi = np.nan
    if len(r22):
        c22 = score(haupt["k"], E, r22, OFF_M[r22])
        d22 = dq(r22[c22 >= np.quantile(haupt["c_tr"], 0.9)], A24, MA, MB)
        rs22 = haupt["k"]["m"]["rsi"].z(E, r22, OFF_M[r22]) - OFF_M[r22]
        rs_tr = haupt["k"]["m"]["rsi"].z(E, r_sa, OFF[r_sa]) - OFF[r_sa]
        r22_rsi = dq(r22[rs22 >= np.quantile(rs_tr, 0.9)], A24, MA, MB)
        print("  2022 (Moment-Bezug): rsi + Lage oben %+.4f · rsi allein oben %+.4f" % (d22, r22_rsi))

    # ══ ROLLIEREND, wachsend ═══════════════════════════════════════════
    print()
    print("=" * 120)
    print("ROLLIEREND, WACHSEND: %d Monate, Auswahl mit Grenze aus dem Training" % len(monate))
    ZC, ZR, ZL = np.full(n, np.nan), np.full(n, np.nan), np.full(n, np.nan)
    SEL, SELR, SELL = np.zeros(n, bool), np.zeros(n, bool), np.zeros(n, bool)
    RSI_UNTEN = np.zeros(n, bool)
    DRITTEL = np.full(n, -1, np.int8)
    lams, gews = [], []
    ab = H(datetime(2023, 1, 1))
    for (j, mo) in monate:
        mi = j * 12 + (mo - 1)
        start = H(datetime(j, mo, 1))
        fen = BASIS & (STD >= ab) & (MON < mi) & (STD < start - 24)
        ra = np.flatnonzero(fen); rt = np.flatnonzero(fen & HIT)
        ziel = np.flatnonzero(BASIS & (MON == mi))
        if len(rt) < 5000 or not len(ziel):
            continue
        k = kombi(E, ra, rt, A24[rt], OFF[rt])
        lams.append(k["lam"]); gews.append(k["gew"])
        ct = score(k, E, ra, OFF[ra]); cz = score(k, E, ziel, OFF[ziel])
        ZC[ziel] = cz
        SEL[ziel] = cz >= np.quantile(ct, 0.9)
        rt_ = k["m"]["rsi"].z(E, ra, OFF[ra]) - OFF[ra]; rz_ = k["m"]["rsi"].z(E, ziel, OFF[ziel]) - OFF[ziel]
        ZR[ziel] = rz_
        SELR[ziel] = rz_ >= np.quantile(rt_, 0.9)
        lt_ = score(k, E, ra, OFF[ra], ohne=("rsi",)); lz_ = score(k, E, ziel, OFF[ziel], ohne=("rsi",))
        ZL[ziel] = lz_; SELL[ziel] = lz_ >= np.quantile(lt_, 0.9)
        RSI_UNTEN[ziel] = E["rsi_s"][ziel] < np.nanquantile(E["rsi_s"][ra], 2 / 3)
        q1, q2 = np.nanquantile(QN[ra], (1 / 3, 2 / 3))
        DRITTEL[ziel] = np.where(QN[ziel] <= q1, 0, np.where(QN[ziel] <= q2, 1, 2))
    alle = np.flatnonzero(np.isfinite(ZC))
    sel, selr, sell = alle[SEL[alle]], alle[SELR[alle]], alle[SELL[alle]]
    rand = np.mean([v == GITTER_NEU[-1] for l_ in lams for v in l_.values()]) if lams else np.nan
    g_mit = np.mean(np.array(gews), axis=0) if gews else None
    print("  Randwahl der Daempfung: %.0f %% (Familie x Monat) · mittlere Gewichte: %s" % (
        100 * rand, ", ".join("%s %+.3f" % (f_, w_) for f_, w_ in zip(FAMILIEN, g_mit[1:])) if g_mit is not None else "-"))
    ca, cr = ZC[alle], ZR[alle]
    d_roll = dq(alle[ca >= np.quantile(ca, 0.9)]) - dq(alle[cr >= np.quantile(cr, 0.9)])
    print("  Auswahl rsi + Lage oben %+.4f (Anteil %.1f %%) · rsi allein %+.4f · nur Lage %+.4f" % (
        dq(sel), 100 * SEL[alle].mean(), dq(selr), dq(sell)))
    print("  T2 rollierend (gleicher Anteil, B1: gegen das feste Nullband %+.4f): %+.4f - %+.4f = %+.4f -> %s" % (
        g2, dq(alle[ca >= np.quantile(ca, 0.9)]), dq(alle[cr >= np.quantile(cr, 0.9)]), d_roll,
        "✔" if d_roll > g2 else "·"))
    print("  T7 Signale von rsi + Lage, bei denen rsi NICHT im oberen Drittel liegt: %.1f %% (Dq dort %+.4f, %d)" % (
        100 * RSI_UNTEN[sel].mean(), dq(sel[RSI_UNTEN[sel]]), int(RSI_UNTEN[sel].sum())))
    # A4 ausgewiesen
    z4a = []
    for nm, lo_, hi_ in (("Anstieg < 0", -np.inf, 0), ("0-1 ATR", 0, 1), ("1-2 ATR", 1, 2), ("> 2 ATR", 2, np.inf)):
        s_ = sel[(ANST[sel] >= lo_) & (ANST[sel] < hi_)]
        z4a.append("%s %+.4f (%d)" % (nm, dq(s_), len(s_)))
    print("  A4 (ausgewiesen, keine Sperre): %s" % " · ".join(z4a))
    # T6
    t6 = []
    for d_, nm in ((0, "Normal unten"), (1, "Normal mitte"), (2, "Normal oben")):
        s_ = sel[DRITTEL[sel] == d_]
        t6.append((nm, dq(s_), len(s_)))
    print("  T6 je Drittel des Normals: %s -> %s" % (
        " · ".join("%s %+.4f (%d)" % x for x in t6),
        "✔ ueberall positiv" if all(v > 0 for _n, v, k in t6 if k >= 200) and all(k >= 200 for *_x, k in t6)
        else "⛔ NICHT ueberall positiv"))
    # T4 und T5
    btc = reihe([(E2.EINGESTELLT_DB, "SELECT stunde, close FROM stundenkurse WHERE symbol='BTC'"),
                 (E2.STUNDEN_DB, "SELECT stunde, close FROM stundenkurse WHERE symbol='BTC'")])
    b30 = np.full(n, np.nan)
    okb = (STD < len(btc)) & (STD >= 720)
    with np.errstate(divide="ignore", invalid="ignore"):
        b30[okb] = btc[STD[okb]] / btc[STD[okb] - 720] - 1.0
    w4, z4 = [], []
    for jj in (2024, 2025, 2026):
        v = dq(sel[JAHR[sel] == jj]); w4.append(v); z4.append("%d %+.4f" % (jj, v))
    bb = b30[alle]; fin = np.isfinite(bb)
    q1, q2 = np.quantile(bb[fin], (1 / 3, 2 / 3))
    for nm, lo_, hi_ in (("BTC tief", -np.inf, q1), ("BTC mitte", q1, q2), ("BTC hoch", q2, np.inf)):
        s_ = sel[np.isfinite(b30[sel]) & (b30[sel] > lo_) & (b30[sel] <= hi_)]
        v = dq(s_); w4.append(v); z4.append("%s %+.4f (%d)" % (nm, v, len(s_)))
    w4.append(d22); z4.append("2022 %+.4f" % d22)
    print("  T4 je Jahr, BTC-Lage und 2022: %s -> %s" % (
        " · ".join(z4), "✔" if np.nanmin(w4) > 0 and np.isfinite(d22) else "⛔ NICHT zeitstabil"))
    ga = np.array([dq(sel[SYM[sel] == si]) for si in np.unique(SYM[sel]) if (SYM[sel] == si).sum() >= 50])
    print("  T5 je Asset (>= 50 Auswahlanker): %d Assets, Dq > 0 bei %.0f %% -> %s" % (
        len(ga), 100 * np.mean(ga > 0), "✔" if np.mean(ga > 0) >= 0.6 else "·"))

    # ══ NACHKALIBRIERUNG (V6, B2) und T3 ════════════════════════════════
    print()
    print("=" * 120)
    print("NACHKALIBRIERUNG - Uebersetzung Beitrag -> beobachteter Vorsprung aus den UNGESEHENEN Schaetzungen")
    ev_all = alle[HIT[alle]]
    dy_all = A24 - QN

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

    def kalibriere(G):
        bcal = np.full(n, np.nan)
        for mi in np.unique(MON[alle]):
            start = mi  # Monatsindex
            quelle = ev_all[(MON[ev_all] >= mi - G) & (MON[ev_all] < mi)]
            ziel = alle[MON[alle] == mi]
            ms = MON[quelle]
            # nur Ausgaenge, die vor dem Zielmonat bekannt waren: der letzte Tag des Vormonats faellt heraus
            j_, m_ = divmod(int(mi), 12)
            grenz = H(datetime(j_, m_ + 1, 1)) - 24
            quelle = quelle[STD[quelle] < grenz]
            if len(quelle) < 2000 or len(np.unique(ms)) < G:
                continue
            s_q = ZC[quelle]; y_q = dy_all[quelle]
            ok = np.isfinite(s_q) & np.isfinite(y_q)
            s_q, y_q = s_q[ok], y_q[ok]
            kan = np.quantile(s_q, np.linspace(0, 1, 21))
            kb = np.clip(np.searchsorted(kan, s_q, "right") - 1, 0, 19)
            cnt = np.bincount(kb, minlength=20).astype(float)
            mw = np.bincount(kb, weights=y_q, minlength=20) / np.maximum(cnt, 1)
            mitte = np.bincount(kb, weights=s_q, minlength=20) / np.maximum(cnt, 1)
            gut = cnt > 0
            yy, ww = pav(mw[gut], cnt[gut])
            # zurueck auf die Stufen verteilen
            werte, xs = [], []
            k0 = 0
            xm = mitte[gut]; cm = cnt[gut]
            for yv, wv in zip(yy, ww):
                acc, idx = 0.0, []
                while acc < wv - 1e-9 and k0 < len(xm):
                    acc += cm[k0]; idx.append(k0); k0 += 1
                xs.append(float(np.average(xm[idx], weights=cm[idx]))); werte.append(yv)
            bcal[ziel] = np.interp(ZC[ziel], xs, werte)
        return bcal

    def t3(bv, ev):
        b = bv[ev]; dy = dy_all[ev]
        ok = np.isfinite(b) & np.isfinite(dy)
        ev, b, dy = ev[ok], b[ok], dy[ok]
        if len(ev) < 1000:
            return np.nan, (np.nan, np.nan), {}
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
        je = {}
        for jj in (2024, 2025, 2026):
            kj = JAHR[ev] == jj
            if kj.sum() >= 1000:
                je[jj] = (float(b[kj & top].mean()) if (kj & top).any() else np.nan,
                          float(dy[kj & top].mean()) if (kj & top).any() else np.nan)
        return sl, (b[top].mean(), dy[top].mean()), je

    roh = np.full(n, np.nan); roh[alle] = expit(ZC[alle]) - expit(OFF[alle])
    sl0, lv0, _ = t3(roh, ev_all)
    print("  ohne Nachkalibrierung: Steigung %.2f · oberstes Zehntel geschaetzt %+.4f beobachtet %+.4f" % (sl0, lv0[0], lv0[1]))
    bc = {G: kalibriere(G) for G in GEDAECHTNIS}
    gemein = ev_all[np.isfinite(bc[3][ev_all]) & np.isfinite(bc[12][ev_all])]
    res = {G: t3(bc[G], gemein) for G in GEDAECHTNIS}
    for G in GEDAECHTNIS:
        sl, lv, je = res[G]
        print("  Gedaechtnis %2d Monate (gemeinsame Monate): Steigung %.2f · oberstes Zehntel geschaetzt %+.4f beobachtet %+.4f · je Jahr %s" % (
            G, sl, lv[0], lv[1], " / ".join("%d %+.3f|%+.3f" % (jj, a_, b_) for jj, (a_, b_) in je.items())))
    kurz_gut = all(abs(res[3][2][jj][0] - res[3][2][jj][1]) <= abs(res[12][2][jj][0] - res[12][2][jj][1]) + 1e-12
                   for jj in res[3][2] if jj in res[12][2])
    G_w = 3 if kurz_gut else 12
    sl, lv, _je = res[G_w]
    print("  Z4: gewaehlt %d Monate (%s)" % (G_w, "die kuerzere ist in keinem Jahr schlechter" if kurz_gut else "die kuerzere ist in einem Jahr schlechter"))
    print("  T3 nachkalibriert: Steigung %.2f · oberstes Zehntel |geschaetzt - beobachtet| %.4f -> %s" % (
        sl, abs(lv[0] - lv[1]), "✔ kalibriert" if 0.7 <= sl <= 1.3 and abs(lv[0] - lv[1]) <= 0.02 else "⛔ nicht kalibriert"))

    # ══ K5-TABELLE auf dem nachkalibrierten Beitrag ═════════════════════
    print()
    print("=" * 120)
    print("K5-TABELLE AUF DEM NACHKALIBRIERTEN BEITRAG (Gedaechtnis %d Monate; Ausgabe, KEINE Schwelle)" % G_w)
    bw = bc[G_w]
    mit = alle[np.isfinite(bw[alle])]
    nmon = len(np.unique(MON[mit])); nas = len(np.unique(SYM[mit]))
    for nm, s_ in ([("Beitrag >= +%.2f" % s, bw[mit] >= s) for s in (0.02, 0.04, 0.06, 0.08)] +
                   [("Beitrag <= %.2f" % s, bw[mit] <= s) for s in (-0.02, -0.04)]):
        ix = mit[s_]
        qj = [dq(ix[JAHR[ix] == jj]) if (JAHR[ix] == jj).sum() >= 100 else np.nan for jj in (2024, 2025, 2026)]
        print("  %-17s Anker %7d · je Asset/Monat %6.2f · beobachteter Vorsprung %+.4f · je Jahr %s" % (
            nm, len(ix), len(ix) / max(nmon * nas, 1), dq(ix),
            " / ".join("%+.4f" % x if np.isfinite(x) else "-" for x in qj)))
    print()
    print("  ⚠️ Gebuehren und Finanzierung sind nicht eingerechnet (Regel 2).")
    print("SCHLUSS: vollstaendig")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
