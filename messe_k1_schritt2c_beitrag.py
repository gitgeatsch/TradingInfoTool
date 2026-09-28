# -*- coding: utf-8 -*-
"""K1 SCHRITT 2c - die Kombination nach dem BEITRAG gegen rsi allein (28.09.2026).

Voranalyse `Basisinfos/Voranalyse_K1_Schritt2c_Beitrag_28_09.md`, abgestimmt
(*ja, F1 bis F9 wie empfohlen*). Grundlage K5 geaendert (vorlaeufig): die
Schwelle liegt auf dem BEITRAG - dem Vorsprung gegen das eigene Normal.

Eigene Datei, damit die laufende K6-Kette (sie importiert die Bausteine aus
messe_k1_schritt2b_kombination) unberuehrt bleibt: das erweiterte Gitter wird
nur in DIESEM Prozess gesetzt.

VORAB FESTGELEGT
    F1/F2  Eingaenge und Form unveraendert aus 2b (A: rsi/momentum/ema_abstand
           selbst, je aktuell und 24 h alt, Anstieg; B: + oi_aenderung; glatte
           12-Stufen-Kurve)
    F3     Daempfung per Kreuzvalidierung, Gitter 20 .. 2.000.000; Randwahl
           ausgewiesen. R-R11 ZUERST mit dem alten Gitter (bis 20.000): die
           Beitragsauswahl aus 2.678 muss bitgleich herauskommen
    F4     Hauptmass Dq der BEITRAGSauswahl: q im obersten Zehntel des Beitrags
           (z - Normal) minus Normal, Grenze = fester Beitragswert aus dem Training
    F5     T2 bei gleichem Anteil (oberstes Zehntel der eigenen Testschaetzungen):
           A gegen rsi allein (Kriterium) und gegen die einfache Regel rsi selbst
           (Auskunft)
    F6     T6 Normal-Drittel (Grenzen aus dem Training), rollierend
    F7     T3 Kalibrierung des Beitrags in q-Punkten: q(Normal+Beitrag) -
           q(Normal) gegen den beobachteten Vorsprung - innerhalb des Monats
           (Steigung) und das Niveau im obersten Zehntel
    F8     Nullwelt (Zeitverschiebung je Asset, 40 Ziehungen), Zufall, TOR auf
           der Beitragsauswahl (+0,04 in >= 4 von 5)
    F9     Gegenpruefungen und die K5-Tabelle auf dem Beitrag
KRITERIEN T0-T6, R, S wie Abschnitt 2 der Voranalyse. Faellt T6 oder T3 ->
K5 neu vorlegen; faellt nur T2 -> die einfachere Regel (rsi allein).

    python messe_k1_schritt2c_beitrag.py --menge bestand --tor
    python messe_k1_schritt2c_beitrag.py --menge unverzerrt:1
"""
from __future__ import annotations

import os
import sqlite3
import sys
from datetime import datetime

import numpy as np
import pandas as pd
from scipy.special import expit

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import messe_e2_beitraege as E2                                   # noqa: E402
import messe_k1_schritt2b_kombination as K2                       # noqa: E402
from messe_e3_vorwaerts import monat_von                          # noqa: E402
from messe_k3_kontextflaeche import reihe                         # noqa: E402

GITTER_ALT = (20.0, 200.0, 2000.0, 20000.0)
GITTER_NEU = (20.0, 200.0, 2000.0, 20000.0, 200000.0, 2000000.0)
# 2.678, feste Teilung, Variante A, Beitragsauswahl oben (R-R11)
RR11_2678 = {"bestand": 0.0611, "unverzerrt:1": 0.0569, "unverzerrt:2": 0.0543, "unverzerrt:3": 0.0549}
ZIEHUNGEN, SAAT = 40, 20261011
H = K2._h
SUCHE, PRUEF, ROLL = K2.SUCHE, K2.PRUEF, K2.ROLL_MONATE
FAM, VAR_A, VAR_B = K2.FAM, K2.VAR_A, K2.VAR_B


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:                                         # noqa: BLE001
        pass
    E2.menge_aus_argv()
    K2.FORM = "b"
    tor = "--tor" in sys.argv
    probe = "--probe" in sys.argv
    zieh = 3 if probe else ZIEHUNGEN
    monate = ROLL[:3] if probe else ROLL
    print("=" * 120)
    print("K1 SCHRITT 2c - KOMBINATION NACH DEM BEITRAG · MENGE %s%s" % (
        E2.MENGE, " · TOR" if tor else (" · WERKZEUGTEST" if probe else "")))
    print("=" * 120)
    # ── Aufbereitung WOERTLICH wie 2b (R-R11) ───────────────────────────
    D = E2.lade(hmax=72, erste=(("u5", 1.05, True), ("d5", 0.95, False)), mit_atr=True)
    SYM, STD, syms = D["SYM"], D["STD"], D["syms"]
    n = len(SYM)
    t_u, t_d = D["T"]["u5"], D["T"]["d5"]
    A24 = ((t_u <= 24) & (t_u < t_d)).astype(np.float64)
    B24 = ((t_d <= 24) & (t_d <= t_u)).astype(np.float64)
    ATR = D["ATR"]; VOR24 = D["X"]["vor24"]
    FR = {m: D["F"][m].astype(np.float64) for m in ("rsi", "momentum_kurz", "ema_abstand_atr", "oi_aenderung")}
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

    with np.errstate(divide="ignore", invalid="ignore"):
        anst = VOR24 / np.maximum(ATR, 1e-12)
    E = {}
    for kurz, m in (("rsi", "rsi"), ("mom", "momentum_kurz"), ("ema", "ema_abstand_atr")):
        s = selbst(FR[m])
        E[kurz + "_s"] = s
        E[kurz + "_s24"] = alt(s, 24)
    E["anstieg"] = anst
    E["oi"] = FR["oi_aenderung"]
    GRID = np.isin(STD % 24, K2.GITTER)
    BASIS = GRID & np.isfinite(OFF)
    HIT = (A24 + B24) > 0
    such = BASIS & (STD >= SUCHE[0]) & (STD < SUCHE[1])
    pruef = BASIS & (STD >= PRUEF[0]) & (STD < PRUEF[1])
    with np.errstate(divide="ignore", invalid="ignore"):
        QN = NA / (NA + NB)                     # Normal als q (bedingt auf Treffer)
    print("  Anker (Gitter, mit Phase-Normal): Suche %d · Pruefung %d · Symbole %d" % (
        such.sum(), pruef.sum(), len(np.unique(SYM[such | pruef]))))

    def dq(ix, y=A24, na=NA, nb=NB):
        if not len(ix):
            return np.nan
        a = y[ix].sum(); b = (HIT[ix] & (y[ix] == 0)).sum()
        sa, sb = na[ix].sum(), nb[ix].sum()
        return a / max(a + b, 1e-12) - sa / max(sa + sb, 1e-12)

    r_sa = np.flatnonzero(such); r_s = np.flatnonzero(such & HIT); r_pa = np.flatnonzero(pruef)

    def fest(EE, namen, y=A24):
        m, lam = K2.fit_cv(namen, EE, r_sa, r_s, y[r_s], OFF[r_s], STD)
        c_tr = m.z(EE, r_sa, OFF[r_sa]) - OFF[r_sa]
        c_te = m.z(EE, r_pa, OFF[r_pa]) - OFF[r_pa]
        g_hi, g_lo = np.quantile(c_tr, 0.9), np.quantile(c_tr, 0.1)
        e_hi = np.quantile(c_te, 0.9)
        return dict(m=m, lam=lam, c_te=c_te, c_tr=c_tr,
                    oben=dq(r_pa[c_te >= g_hi], y), unten=dq(r_pa[c_te <= g_lo], y),
                    anteil=float(np.mean(c_te >= g_hi)), eigen=dq(r_pa[c_te >= e_hi], y))

    def verschoben(EE):
        aus = dict(EE)
        rr = {}
        for tl in teile:
            L = len(tl)
            rr[int(SYM[tl[0]])] = int(rng.integers(K2.MIN_VERSATZ, L - K2.MIN_VERSATZ)) if L > 2 * K2.MIN_VERSATZ else 0
        for k in EE:
            v = np.empty(n)
            for tl in teile:
                v[tl] = np.roll(EE[k][tl], rr[int(SYM[tl[0]])])
            aus[k] = v
        return aus

    def regel_rsi(EE, y=A24):
        """die einfache Regel: oberstes Zehntel von rsi selbst im Test (gleicher Anteil)."""
        v = EE["rsi_s"][r_pa]; ok = np.isfinite(v)
        return dq(r_pa[ok & (v >= np.nanquantile(v, 0.9))], y)

    # ══ R-R11 mit dem alten Gitter ══════════════════════════════════════
    K2.LAMBDAS = GITTER_ALT
    rr = fest(E, VAR_A)
    soll = RR11_2678.get(E2.MENGE)
    print()
    print("R-R11 (altes Gitter bis 20.000): Beitragsauswahl A oben %+.4f · 2.678: %s -> %s" % (
        rr["oben"], "%+.4f" % soll if soll is not None else "-",
        ("✔ bitgleich" if soll is not None and abs(round(rr["oben"], 4) - soll) < 1e-9 else "⛔ ABWEICHUNG")
        if soll is not None else "(kein Vergleichswert)"))
    K2.LAMBDAS = GITTER_NEU
    print("  ab hier Gitter %s" % "/".join("%.0f" % x for x in GITTER_NEU))

    # ══ TOR auf der Beitragsauswahl (F8) ════════════════════════════════
    if tor:
        null_o = np.array([fest(verschoben(E), VAR_A)["oben"] for _ in range(zieh)])
        grenze = float(np.nanpercentile(null_o, 90))
        print()
        print("TOR (F8) Beitragsauswahl, Variante A: Nullwelt Mittel %+.4f, Streuung %.4f, 90. Perzentil %+.4f" % (
            float(np.nanmean(null_o)), float(np.nanstd(null_o, ddof=1)), grenze))
        erg = {}
        for d in (0.02, 0.04, 0.08):
            gef, werte = 0, []
            for _ in range(5):
                EV = verschoben(E)
                gr = np.nanpercentile(EV["rsi_s"][r_sa], 90)
                y = A24.copy()
                oben = np.flatnonzero((EV["rsi_s"] >= gr) & HIT & (such | pruef))
                kand = oben[B24[oben] == 1]
                w = rng.choice(kand, size=min(int(round(d * len(oben))), len(kand)), replace=False)
                y[w] = 1.0
                o = fest(EV, VAR_A, y=y)["oben"]
                werte.append(o); gef += int(o > grenze)
            erg[d] = gef
            print("  gepflanzt +%.2f auf P90+ von rsi_s (verschoben): %s -> gefunden %d von 5" % (
                d, " ".join("%+.4f" % x for x in werte), gef))
        print("  TOR: %s" % ("✔ BESTANDEN" if erg[0.04] >= 4 else "⛔ NICHT BESTANDEN - kein Urteil"))
        print("SCHLUSS: vollstaendig")
        return 0

    # ══ FESTE TEILUNG: T1, T2, R ═══════════════════════════════════════
    rA, rB, rR = fest(E, VAR_A), fest(E, VAR_B), fest(E, FAM["rsi"])
    rF = {f: fest(E, ks) for f, ks in FAM.items() if f != "rsi"}
    rg = regel_rsi(E)
    nO, nD, nDr = [], [], []
    for _ in range(zieh):
        EV = verschoben(E)
        a_, b_, r_ = fest(EV, VAR_A), fest(EV, VAR_B), fest(EV, FAM["rsi"])
        nO.append(max(a_["oben"], b_["oben"])); nD.append(a_["eigen"] - r_["eigen"])
        nDr.append(a_["eigen"] - regel_rsi(EV))
    nO, nD, nDr = map(np.array, (nO, nD, nDr))
    g1, g2, g2r = (float(np.nanpercentile(x, 90)) for x in (nO, nD, nDr))
    print()
    print("=" * 120)
    print("FESTE TEILUNG Suche 2023-2024 -> Pruefung 2025-01..2026-08 · Dq der BEITRAGSauswahl")
    for nm, r_ in (("A", rA), ("B", rB), ("rsi allein", rR)):
        print("  %-11s oben %+.4f (Anteil %.1f %%) · unten %+.4f · eigenes Zehntel %+.4f · Daempfung %.0f%s" % (
            nm, r_["oben"], 100 * r_["anteil"], r_["unten"], r_["eigen"], r_["lam"],
            " (RAND)" if r_["lam"] == GITTER_NEU[-1] else ""))
    print("  Familien (eigenes Zehntel): %s · einfache Regel rsi selbst (oberstes Zehntel im Test) %+.4f" % (
        " · ".join("%s %+.4f" % (f, v["eigen"]) for f, v in rF.items()), rg))
    print("  Nullwelt (Bestes-von-2): Mittel %+.4f · 90. Perzentil %+.4f" % (float(np.nanmean(nO)), g1))
    print("  T1 fest: %s" % ("✔ jenseits" if max(rA["oben"], rB["oben"]) > g1 else "· nicht jenseits"))
    d2, d2r = rA["eigen"] - rR["eigen"], rA["eigen"] - rg
    print("  T2 A minus rsi allein %+.4f gegen Nullband %+.4f -> %s" % (
        d2, g2, "✔ mehr als rsi allein" if d2 > g2 else "· nicht mehr als rsi allein"))
    print("     Auskunft: A minus einfache rsi-Regel %+.4f gegen Nullband %+.4f -> %s" % (
        d2r, g2r, "mehr" if d2r > g2r else "nicht mehr"))
    print("  S  unterstes Zehntel A %+.4f · B %+.4f" % (rA["unten"], rB["unten"]))
    rz = np.random.default_rng(SAAT + 1)
    EZ = dict(E)
    for i, k in enumerate(VAR_A):
        x = rz.standard_normal(n); v = np.empty(n); g_ = (6, 24)[i % 2]
        for tl in teile:
            c = np.concatenate([[0.0], np.cumsum(x[tl])]); kk = np.arange(1, len(tl) + 1)
            v[tl] = (c[kk] - c[np.maximum(0, kk - g_)]) / np.minimum(kk, g_)
        EZ[k] = v
    zO = fest(EZ, VAR_A)["oben"]
    print("  R  Zufallseingaenge: %+.4f gegen %+.4f -> %s" % (zO, g1, "✔ im Nullband" if zO <= g1 else "⛔ JENSEITS"))
    csum_tr = sum(v["c_tr"] for v in list(rF.values()) + [rR]); csum_te = sum(v["c_te"] for v in list(rF.values()) + [rR])
    print("  Summe der einzeln geschaetzten Familien: %+.4f (gemeinsam %+.4f)" % (
        dq(r_pa[csum_te >= np.quantile(csum_tr, 0.9)]), rA["oben"]))
    E1 = {k: alt(v, 1) for k, v in E.items()}
    print("  Eingaenge 1 h aelter: %+.4f" % fest(E1, VAR_A)["oben"])
    r22 = np.flatnonzero(GRID & (JAHR == 2022) & np.isfinite(OFF_M))
    if len(r22):
        c22 = rA["m"].z(E, r22, OFF_M[r22]) - OFF_M[r22]
        print("  2022 (Moment-Bezug): oben %+.4f · unten %+.4f (Anteil oben %.1f %%)" % (
            dq(r22[c22 >= np.quantile(rA["c_tr"], 0.9)], A24, MA, MB),
            dq(r22[c22 <= np.quantile(rA["c_tr"], 0.1)], A24, MA, MB), 100 * np.mean(c22 >= np.quantile(rA["c_tr"], 0.9))))

    # ══ ROLLIEREND, wachsend ═══════════════════════════════════════════
    print()
    print("=" * 120)
    print("ROLLIEREND, WACHSEND: %d Monate, Beitragsauswahl mit Grenze aus dem Training" % len(monate))
    ZA, ZR = np.full(n, np.nan), np.full(n, np.nan)
    SEL, SELU, SELR = np.zeros(n, bool), np.zeros(n, bool), np.zeros(n, bool)
    DRITTEL = np.full(n, -1, np.int8)
    lams = []
    ab = H(datetime(2023, 1, 1))
    for (j, mo) in monate:
        mi = j * 12 + (mo - 1)
        start = H(datetime(j, mo, 1))
        fen = BASIS & (STD >= ab) & (MON < mi) & (STD < start - 24)
        ra = np.flatnonzero(fen); rt = np.flatnonzero(fen & HIT)
        ziel = np.flatnonzero(BASIS & (MON == mi))
        if len(rt) < 5000 or not len(ziel):
            continue
        y = A24[rt]; off = OFF[rt]
        m, lam = K2.fit_cv(VAR_A, E, ra, rt, y, off, STD); lams.append(lam)
        ct = m.z(E, ra, OFF[ra]) - OFF[ra]
        ZA[ziel] = m.z(E, ziel, OFF[ziel])
        cz = ZA[ziel] - OFF[ziel]
        SEL[ziel] = cz >= np.quantile(ct, 0.9); SELU[ziel] = cz <= np.quantile(ct, 0.1)
        mr, _l = K2.fit_cv(FAM["rsi"], E, ra, rt, y, off, STD)
        ZR[ziel] = mr.z(E, ziel, OFF[ziel])
        SELR[ziel] = (ZR[ziel] - OFF[ziel]) >= np.quantile(mr.z(E, ra, OFF[ra]) - OFF[ra], 0.9)
        q1, q2 = np.nanquantile(QN[ra], (1 / 3, 2 / 3))
        DRITTEL[ziel] = np.where(QN[ziel] <= q1, 0, np.where(QN[ziel] <= q2, 1, 2))
    alle = np.flatnonzero(np.isfinite(ZA))
    sel, selu, selr = alle[SEL[alle]], alle[SELU[alle]], alle[SELR[alle]]
    rand = np.mean([x == GITTER_NEU[-1] for x in lams]) if lams else np.nan
    print("  Daempfung je Monat: %s · Rand (%.0f) gewaehlt in %.0f %% der Monate" % (
        " ".join("%.0f" % x for x in lams), GITTER_NEU[-1], 100 * rand))
    print("  T1 rollierend: A oben %+.4f (Anteil %.1f %%) · unten %+.4f · rsi allein oben %+.4f (Anteil %.1f %%)" % (
        dq(sel), 100 * SEL[alle].mean(), dq(selu), dq(selr), 100 * SELR[alle].mean()))
    ca, cr = ZA[alle] - OFF[alle], ZR[alle] - OFF[alle]
    print("     gleicher Anteil (oberstes Zehntel im Test): A %+.4f · rsi allein %+.4f" % (
        dq(alle[ca >= np.quantile(ca, 0.9)]), dq(alle[cr >= np.quantile(cr, 0.9)])))
    # T6 Normal-Drittel
    t6 = []
    for d_, nm in ((0, "Normal unten"), (1, "Normal mitte"), (2, "Normal oben")):
        s_ = sel[DRITTEL[sel] == d_]
        t6.append((nm, dq(s_), len(s_)))
    print("  T6 je Drittel des Normals: %s -> %s" % (
        " · ".join("%s %+.4f (%d)" % x for x in t6),
        "✔ ueberall positiv" if all(v > 0 for _n, v, k in t6 if k >= 200) and all(k >= 200 for *_x, k in t6)
        else "⛔ NICHT ueberall positiv"))
    # T3 Kalibrierung des Beitrags (q-Punkte)
    ev = alle[HIT[alle]]
    b = expit(ZA[ev]) - expit(OFF[ev]); dy = A24[ev] - QN[ev]
    ok = np.isfinite(b) & np.isfinite(dy)
    ev, b, dy = ev[ok], b[ok], dy[ok]
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
    lvl = (b[top].mean(), dy[top].mean())
    print("  T3 Beitrag kalibriert: Steigung im Monat %.2f · oberstes Zehntel geschaetzt %+.4f beobachtet %+.4f -> %s" % (
        sl, lvl[0], lvl[1], "✔" if 0.7 <= sl <= 1.3 and abs(lvl[0] - lvl[1]) <= 0.02 else "⛔ nicht kalibriert"))
    print("     Zehntel geschaetzt (gegen Monatsmittel): %s" % " ".join("%+.3f" % x for x in mp))
    print("     Zehntel beobachtet (gegen Monatsmittel): %s" % " ".join("%+.3f" % x for x in mo_))
    # T4, T5
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
    print("  T4 je Jahr und BTC-Drittel: %s -> %s" % (" · ".join(z4), "✔" if np.nanmin(w4) > 0 else "⚠ NICHT ueberall positiv - reden"))
    ga = np.array([dq(sel[SYM[sel] == si]) for si in np.unique(SYM[sel]) if (SYM[sel] == si).sum() >= 50])
    print("  T5 je Asset (>= 50 Auswahlanker): %d Assets, Dq > 0 bei %.0f %% -> %s" % (
        len(ga), 100 * np.mean(ga > 0), "✔" if np.mean(ga > 0) >= 0.6 else "·"))
    try:
        c = sqlite3.connect("file:%s?mode=ro" % K2.HEBEL_DB, uri=True)
        hebel = {r_[0].upper() for r_ in c.execute("SELECT symbol FROM asset_hebel_settings")}
        c.close()
        in_h = np.array([s.upper() in hebel for s in syms])[SYM]
        print("  nur Hebelwerte (Namensgleichheit, Vorbehalt 2.612): %d Symbole · %+.4f (%d)" % (
            len(np.unique(SYM[alle][in_h[alle]])), dq(sel[in_h[sel]]), int(in_h[sel].sum())))
    except Exception as exc:                                  # noqa: BLE001
        print("  Hebelwerte nicht lesbar: %s" % exc)
    print("  W1/W2 (Hinweis fuer Schritt 3): beobachteter minus geschaetzter Vorsprung")
    bev = np.full(n, np.nan); bev[ev] = b; dyv = np.full(n, np.nan); dyv[ev] = dy
    for kurz, nm in (("rsi", "rsi"), ("mom", "momentum"), ("ema", "ema_abstand")):
        g90 = np.nanpercentile(E[kurz + "_s"][r_sa], 90); g90a = np.nanpercentile(E[kurz + "_s24"][r_sa], 90)
        ob = E[kurz + "_s"][ev] >= g90; ob24 = E[kurz + "_s24"][ev] >= g90a
        z2 = []
        for lab, s_ in (("beide oben", ob & ob24), ("nur jetzt", ob & ~ob24), ("nur 24 h", ~ob & ob24), ("keiner", ~ob & ~ob24)):
            z2.append("%s %+.3f (%d)" % (lab, dy[s_].mean() - b[s_].mean(), s_.sum()) if s_.sum() >= 100 else "%s -" % lab)
        print("     W2 %-11s %s" % (nm, " · ".join(z2)))
    # K5-Tabelle auf dem Beitrag
    print()
    print("=" * 120)
    print("K5-TABELLE AUF DEM BEITRAG (Ausgabe, KEINE Schwelle) - rollierend, Variante A, Beitrag in q-Punkten")
    ba = expit(ZA[alle]) - expit(OFF[alle])
    nmon = len(np.unique(MON[alle])); nas = len(np.unique(SYM[alle]))
    for nm, s_ in ([("Beitrag >= +%.2f" % s, ba >= s) for s in (0.02, 0.04, 0.06, 0.08)] +
                   [("Beitrag <= %.2f" % s, ba <= s) for s in (-0.02, -0.04)]):
        ix = alle[s_]
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
