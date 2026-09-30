# -*- coding: utf-8 -*-
"""LOSFAHREN AUS DEM STAND - die Anfahr-Kurve und die Lage auf stehenden Ankern (29.09.2026).

Voranalyse `Basisinfos/Voranalyse_Losfahren_aus_dem_Stand_29_09.md`, abgestimmt
(*ja, P1 bis P8 wie empfohlen*). Nutzerbild: *Auto steht noch - Sweet Spot -
das Auto hat sich in Bewegung gesetzt, nicht 0 auf 200, sondern 0 auf 20*.

TEIL 1 (Kern)  rsi allein (Rolle A waehrend), oberstes Zehntel des Beitrags mit
               der Grenze aus dem Training; geschichtet nach der TACHONADEL =
               Anstieg der letzten 24 h in eigener Tages-ATR (vor24 / ATR),
               Klassen < -1 | -1..0 | 0..0,5 | 0,5..1 | 1..2 | > 2. Dq gegen das
               GESCHRUMPFTE Normal (2.684). Urteil L2: frueh (<= 0,5) - spaet (> 2)
TEIL 2         Lage (funding, oi, konten; Fenster 0/24/48 h) auf STEHENDEN Ankern
               (|vor24/ATR| < 0,5, nur ueber den Kurs), je Familie fuer sich,
               dazu Markt/Eigen geteilt (Markt mit gemeinsamer Nullwelt)
KRITERIEN L0-L7 wie Abschnitt 4 der Voranalyse. L0 (R-R11 auf E2g) laeuft als
eigener Schritt: `messe_e2g_fortsetzung.py` unveraendert, Ausgabe bitgleich.

    python messe_losfahren.py --menge bestand --tor      # Tor Teil 1 und Teil 2
    python messe_losfahren.py --menge unverzerrt:1
"""
from __future__ import annotations

import io
import os
import sys
from datetime import datetime

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import messe_e2_beitraege as E2                                   # noqa: E402
import messe_k1_schritt2b_kombination as K2                       # noqa: E402
from messe_e3_vorwaerts import monat_von                          # noqa: E402
from messe_k3_kontextflaeche import reihe                         # noqa: E402

GITTER_NEU = (20.0, 200.0, 2000.0, 20000.0, 200000.0, 2000000.0)
RR11_2680 = {"bestand": 0.0808, "unverzerrt:1": 0.0696, "unverzerrt:2": 0.0700, "unverzerrt:3": 0.0703}
ZIEHUNGEN, SAAT = 40, 20261001
H = K2._h
SUCHE, PRUEF, ROLL = K2.SUCHE, K2.PRUEF, K2.ROLL_MONATE
RSI = ("rsi_s", "rsi_s24")
LAGE = {"funding": ("fu_0", "fu_24", "fu_48"), "oi": ("oi_0", "oi_24", "oi_48"),
        "konten": ("ko_0", "ko_24", "ko_48")}
LAGE_SP = tuple(x for f in LAGE.values() for x in f)
KLASSEN = (-np.inf, -1.0, 0.0, 0.5, 1.0, 2.0, np.inf)
KLNAME = ("< -1", "-1..0", "0..0,5", "0,5..1", "1..2", "> 2")
# SPAET 2,0 -> 1,0 (Voranalyse Abschnitt 9, NEUE Vorabfestlegung nach dem Werkzeugtest): > 2 ATR hatte
# 0 % der Anker und 150 Auswahlanker (< 200, zaehlt nach eigener Regel nicht) - L2 war nicht auswertbar
FRUEH, SPAET = 0.5, 1.0
STEHEND = 0.5
MIN_KLASSE = 200


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:                                         # noqa: BLE001
        pass
    E2.menge_aus_argv()
    K2.FORM = "b"
    K2.LAMBDAS = GITTER_NEU
    leiter = "--leiter" in sys.argv          # Abschnitt 10: Tor als LEITER - Aufloesung und Uebertragung messen
    tor = "--tor" in sys.argv or leiter
    D1 = (0.04, 0.08, 0.12, 0.20) if leiter else (0.02, 0.04)
    D2 = (0.04, 0.08, 0.12, 0.20) if leiter else (0.04,)
    probe = "--probe" in sys.argv
    zieh = 3 if probe else ZIEHUNGEN
    monate = ROLL[:8] if probe else ROLL
    print("=" * 120)
    print("LOSFAHREN AUS DEM STAND · MENGE %s%s" % (E2.MENGE, " · TOR" if tor else (" · WERKZEUGTEST" if probe else "")))
    print("=" * 120)
    # ── Aufbereitung wie K5 neu / K5-Folge (R-R11 rsi allein) ─────────────
    D = E2.lade(hmax=72, erste=(("u5", 1.05, True), ("d5", 0.95, False)), mit_atr=True)
    SYM, STD = D["SYM"], D["STD"]
    n = len(SYM)
    t_u, t_d = D["T"]["u5"], D["T"]["d5"]
    A24 = ((t_u <= 24) & (t_u < t_d)).astype(np.float64)
    B24 = ((t_d <= 24) & (t_d <= t_u)).astype(np.float64)
    A72 = ((t_u <= 72) & (t_u < t_d)).astype(np.float64)
    B72 = ((t_d <= 72) & (t_d <= t_u)).astype(np.float64)
    ATR = D["ATR"].astype(np.float64)
    V24 = D["X"]["vor24"].astype(np.float64); V120 = D["X"]["vor120"].astype(np.float64)
    FR = {m: D["F"][m].astype(np.float64) for m in ("rsi", "oi_aenderung", "konten_verh", "funding_vortag")}
    SYMS = list(D.get("syms", []))
    if "--l2" in sys.argv:
        # L2 (Voranalyse_L2_Kern_anheben_30_09.md): Potential (MFE) und Risiko (Rueckgang VOR dem Hoch) je Fenster, in %,
        # und alle Kandidaten aus dem Bestand
        L2_MFE = {w: D["Z"][w]["mfe"].astype(np.float64) for w in (6, 24, 72)}
        L2_MAE = {w: D["Z"][w]["maevp"].astype(np.float64) for w in (6, 24, 72)}
        L2_F = {m: D["F"][m].astype(np.float64) for m in (
            "volumenschub", "vola_kausal", "oi_aenderung", "oi_je_umsatz", "bandenge", "funding_vortag",
            "konten_verh", "ema_abstand_atr", "taker_verh", "top_konten_verh")}
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
    NA72, NB72 = normal(A72, B72, 72)
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
    ROH = {"fu": FR["funding_vortag"], "oi": FR["oi_aenderung"], "ko": mittel24(FR["konten_verh"])}
    for kurz, v in ROH.items():
        E[kurz + "_0"] = v; E[kurz + "_24"] = alt(v, 24); E[kurz + "_48"] = alt(v, 48)
    with np.errstate(divide="ignore", invalid="ignore"):
        NADEL = V24 / np.maximum(ATR, 1e-12)
        NADEL120 = V120 / np.maximum(ATR, 1e-12)
    KL = np.searchsorted(np.array(KLASSEN[1:-1]), NADEL, side="right")      # 0..5
    KL[~np.isfinite(NADEL)] = -1
    GRID = np.isin(STD % 24, K2.GITTER)
    BASIS = GRID & np.isfinite(OFF)
    HIT = (A24 + B24) > 0
    such = BASIS & (STD >= SUCHE[0]) & (STD < SUCHE[1])
    pruef = BASIS & (STD >= PRUEF[0]) & (STD < PRUEF[1])
    with np.errstate(divide="ignore", invalid="ignore"):
        QN = NA / (NA + NB)
    print("  Anker (Gitter, mit Phase-Normal): Suche %d · Pruefung %d · Symbole %d" % (
        such.sum(), pruef.sum(), len(np.unique(SYM[such | pruef]))))
    print("  Tachonadel (Pruefung): Anteil je Klasse %s" % " · ".join(
        "%s %.0f %%" % (KLNAME[k], 100 * np.mean(KL[pruef] == k)) for k in range(6)))

    # ── geschrumpftes Normal (wie K5-Folge --gegen, 2.684) ─────────────────
    basis = np.flatnonzero(BASIS & (MON >= 2024 * 12))
    QS = np.full(n, np.nan)
    for mi in np.unique(MON[basis]):
        ix = basis[MON[basis] == mi]
        q = QN[ix]; ok = np.isfinite(q); ix, q = ix[ok], q[ok]
        if len(ix) < 500:
            continue
        us, inv = np.unique(SYM[ix], return_inverse=True)
        qa = np.bincount(inv, weights=q) / np.bincount(inv)
        rate = np.bincount(inv, weights=(NA[ix] + NB[ix])) / np.bincount(inv)
        rausch = qa * (1 - qa) / np.maximum(rate * 365.0, 5.0)
        mitte = float(np.mean(qa)); tau2 = max(float(np.var(qa)) - float(np.mean(rausch)), 0.0)
        QS[ix] = mitte + (tau2 / (tau2 + rausch))[inv] * (q - mitte)
    NAs, NBs = QS * (NA + NB), (1 - QS) * (NA + NB)

    HIT72 = (A72 + B72) > 0

    def dq(ix, y=A24, na=NA, nb=NB, hit=None):
        """wie K5-Folge; `hit` nur fuer die 72-h-Auskunft (sonst HIT, das Pflanzen aendert es nicht)."""
        if not len(ix):
            return np.nan
        h_ = HIT if hit is None else hit
        a = y[ix].sum(); b = (h_[ix] & (y[ix] == 0)).sum()
        sa, sb = na[ix].sum(), nb[ix].sum()
        return a / max(a + b, 1e-12) - sa / max(sa + sb, 1e-12)

    def dqs(ix, y=A24):
        ix = ix[np.isfinite(QS[ix])]
        return dq(ix, y, NAs, NBs)

    r_sa = np.flatnonzero(such); r_s = np.flatnonzero(such & HIT); r_pa = np.flatnonzero(pruef)

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

    # ══ K6 S STUFE 1 (Voranalyse_K6_RS_Signalstaerke_und_Lage_Extreme_29_09.md, Abschnitt 11) ══
    # Signalstaerke: rsi_s mit FESTER Richtung (kein Modell), fuenf Klassen im obersten
    # Zehntel, Grenzen aus der SUCHE; Dq auf q5 gegen das geschrumpfte Normal, feste
    # Teilung auf den VOLLEN Daten. WEITER nur, wenn oberste minus unterste >= +0,04.
    if "--stark" in sys.argv:
        WEITER = 0.04
        KANTEN = (90, 92, 94, 96, 98)
        KNAME = ("P90-92", "P92-94", "P94-96", "P96-98", "P98-100")

        def klassen(v, idx_train):
            g = np.nanpercentile(v[idx_train], KANTEN)
            k = np.full(n, -1, np.int8)
            fin = np.isfinite(v)
            k[fin] = np.searchsorted(g, v[fin], side="right") - 1        # -1 unter P90, 0..4
            return k

        def stufen(v, y=A24):
            k = klassen(v, r_sa)
            werte = [dqs(r_pa[k[r_pa] == c], y) for c in range(5)]
            return k, werte
        KS, W = stufen(E["rsi_s"])
        dif = W[4] - W[0]
        print()
        print("=" * 120)
        print("K6 S STUFE 1 · SIGNALSTAERKE (rsi_s feste Richtung, Grenzen aus der Suche) · feste Teilung, Pruefzeit")
        print("  Querabgleich: oberstes Zehntel gesamt, rohes Normal %+.4f (2.680: einfache Regel rsi selbst +0,0540 bestand) "
              "· geschrumpft %+.4f" % (dq(r_pa[KS[r_pa] >= 0]), dqs(r_pa[KS[r_pa] >= 0])))
        for c in range(5):
            s_ = r_pa[KS[r_pa] == c]
            print("  %-8s Anker %6d · Dq %+.4f" % (KNAME[c], len(s_), W[c]))
        print("  unter P90 (Vergleich): Dq %+.4f" % dqs(r_pa[KS[r_pa] == -1]))
        null = []
        for _ in range(zieh):
            EV = verschoben(E, ("rsi_s",))
            _k, wv = stufen(EV["rsi_s"])
            null.append(wv[4] - wv[0])
        print("  oberste minus unterste %+.4f · Zufallswelt (rsi verschoben, %d Ziehungen) Mittel %+.4f, 90. Perzentil %+.4f" % (
            dif, zieh, float(np.nanmean(null)), float(np.nanpercentile(null, 90))))
        mono = all(W[c + 1] >= W[c] for c in range(4))
        print("  Auskunft: Kurve monoton steigend? %s" % ("ja" if mono else "nein"))
        print("  Auskunft 72 h (rohes 72-h-Normal): %s" % " · ".join(
            "%s %+.4f" % (KNAME[c], dq(r_pa[KS[r_pa] == c], A72, NA72, NB72, HIT72)) for c in range(5)))
        jz = []
        for jj in (2025, 2026):
            ix = r_pa[JAHR[r_pa] == jj]
            jz.append("%d %+.4f" % (jj, dqs(ix[KS[ix] == 4]) - dqs(ix[KS[ix] == 0])))
        print("  Auskunft je Jahr (oberste minus unterste): %s" % " · ".join(jz))
        # Wetter: BTC-Lage der letzten 30 Tage, Drittel-Grenzen aus der SUCHE (kausal)
        btc = reihe([(E2.EINGESTELLT_DB, "SELECT stunde, close FROM stundenkurse WHERE symbol='BTC'"),
                     (E2.STUNDEN_DB, "SELECT stunde, close FROM stundenkurse WHERE symbol='BTC'")])
        b30 = np.full(n, np.nan)
        okb = (STD < len(btc)) & (STD >= 720)
        with np.errstate(divide="ignore", invalid="ignore"):
            b30[okb] = btc[STD[okb]] / btc[STD[okb] - 720] - 1.0
        bq1, bq2 = np.nanquantile(b30[r_sa], (1 / 3, 2 / 3))
        wz = []
        for nm, lo_, hi_ in (("BTC tief", -np.inf, bq1), ("BTC mitte", bq1, bq2), ("BTC hoch", bq2, np.inf)):
            ix = r_pa[np.isfinite(b30[r_pa]) & (b30[r_pa] > lo_) & (b30[r_pa] <= hi_)]
            wz.append("%s: Zehntel %+.4f, oberste %+.4f, unterste %+.4f (%d)" % (
                nm, dqs(ix[KS[ix] >= 0]), dqs(ix[KS[ix] == 4]), dqs(ix[KS[ix] == 0]), int((KS[ix] >= 0).sum())))
        print("  Auskunft WETTER (BTC 30 Tage, Drittel aus der Suche): " + " · ".join(wz))
        print("  WEITER-SCHWELLE +%.2f: %s" % (WEITER, "✔ ERREICHT - Vollmessung vorlegen" if dif >= WEITER
                                              else "⛔ NICHT erreicht - keine Vollmessung, Ergebnis vorlegen"))
        print("SCHLUSS: vollstaendig")
        return 0

    # ══ TEIL 1 · feste Teilung ══════════════════════════════════════════
    def rsi_auswahl(EE, y=A24, ra=r_sa, rt=r_s, ziel=r_pa):
        m, _l = K2.fit_cv(RSI, EE, ra, rt, y[rt], OFF[rt], STD)
        ct = m.z(EE, ra, OFF[ra]) - OFF[ra]; cz = m.z(EE, ziel, OFF[ziel]) - OFF[ziel]
        return m, ziel[cz >= np.quantile(ct, 0.9)]

    def frueh_spaet(sel, y=A24):
        f = sel[np.isfinite(NADEL[sel]) & (NADEL[sel] <= FRUEH)]
        s = sel[np.isfinite(NADEL[sel]) & (NADEL[sel] > SPAET)]
        return dqs(f, y) - dqs(s, y), f, s

    # ══ K5 (Voranalyse_K5_Schwelle_rsi_29_09.md, S1-S7 + K5-6) ════════════════════════
    # Signal rsi allein rollierend (Betriebsform); Vorsprung vh = expit(logit(QS) + Beitrag) - QS.
    # ZWEI SCHRITTE: ohne --bestaetigen wird NUR 2024 ausgewertet und ausgegeben (Wahl);
    # --bestaetigen <s> [--sperre <-s>] wertet einmal 2025-01..2026-08 aus (Bestaetigung).
    if "--k5" in sys.argv or "--kern" in sys.argv or "--l2" in sys.argv:
        from scipy.special import expit as _ex
        best = "--bestaetigen" in sys.argv
        s_best = float(sys.argv[sys.argv.index("--bestaetigen") + 1]) if best else None
        sp_best = float(sys.argv[sys.argv.index("--sperre") + 1]) if "--sperre" in sys.argv else None
        JAHRE = (2024, 2025, 2026) if "--export" in sys.argv else ((2025, 2026) if best else (2024,))
        SCHW = (0.02, 0.04, 0.06, 0.08)
        SPERR = (-0.02, -0.04)
        m0, _s0 = rsi_auswahl(E)
        ct0 = m0.z(E, r_pa, OFF[r_pa]) - OFF[r_pa]
        rr11 = dq(r_pa[ct0 >= np.quantile(m0.z(E, r_sa, OFF[r_sa]) - OFF[r_sa], 0.9)])
        print()
        print("=" * 120)
        print("K5 · %s · rsi allein rollierend, Vorsprung gegen das geschrumpfte Normal" % (
            "BESTAETIGUNG 2025-01..2026-08, Schwelle %+.2f" % s_best if best else "WAHL 2024 (2025-26 wird NICHT ausgewertet)"))
        print("  K5-0 R-R11 rsi allein oben (fest, rohes Normal) %+.4f · 2.680: +0,0808 -> %s" % (
            rr11, "✔ bitgleich" if abs(round(rr11, 4) - 0.0808) < 1e-9 or E2.MENGE != "bestand" else "⛔ ABWEICHUNG"))
        # geschrumpftes Normal STUENDLICH: dieselbe Schrumpfung je Monat und Asset (aus den Gitterankern) auf jede Stunde
        QSh = np.full(n, np.nan)
        for mi in np.unique(MON[basis]):
            ix = basis[MON[basis] == mi]
            q = QN[ix]; okq = np.isfinite(q); ix, q = ix[okq], q[okq]
            if len(ix) < 500:
                continue
            us, inv = np.unique(SYM[ix], return_inverse=True)
            qa = np.bincount(inv, weights=q) / np.bincount(inv)
            rate = np.bincount(inv, weights=(NA[ix] + NB[ix])) / np.bincount(inv)
            rausch = qa * (1 - qa) / np.maximum(rate * 365.0, 5.0)
            mitte = float(np.mean(qa)); tau2 = max(float(np.var(qa)) - float(np.mean(rausch)), 0.0)
            Bm = dict(zip(us.tolist(), (tau2 / (tau2 + rausch)).tolist()))
            ixh = np.flatnonzero((MON == mi) & np.isfinite(QN) & np.isin(SYM, us))
            bb = np.array([Bm[int(x)] for x in SYM[ixh]])
            QSh[ixh] = mitte + bb * (QN[ixh] - mitte)
        chk = np.flatnonzero(np.isfinite(QS))
        print("  Pruefung stuendliches Normal: max |QSh - QS| auf den Gitterankern %.2e" % float(np.nanmax(np.abs(QSh[chk] - QS[chk]))))
        # rollierend: Modell je Monat nur auf der Vergangenheit, Beitrag fuer JEDE Stunde des Monats
        Ch = np.full(n, np.nan); SEL = np.zeros(n, bool); modelle = []
        ab = H(datetime(2023, 1, 1))
        for (j, mo) in monate:
            mi = j * 12 + (mo - 1)
            start = H(datetime(j, mo, 1))
            fen = BASIS & (STD >= ab) & (MON < mi) & (STD < start - 24)
            ra = np.flatnonzero(fen); rt = np.flatnonzero(fen & HIT)
            ziel = np.flatnonzero(BASIS & (MON == mi))
            if len(rt) < 5000 or not len(ziel):
                continue
            m, _l = K2.fit_cv(RSI, E, ra, rt, A24[rt], OFF[rt], STD)
            thr = np.quantile(m.z(E, ra, OFF[ra]) - OFF[ra], 0.9)
            alle_h = np.flatnonzero((MON == mi) & np.isfinite(OFF))
            Ch[alle_h] = m.z(E, alle_h, OFF[alle_h]) - OFF[alle_h]
            SEL[ziel[Ch[ziel] >= thr]] = True
            modelle.append((mi, m))
        urteil_all = np.flatnonzero(BASIS & (MON >= 2024 * 12) & (MON <= 2026 * 12 + 7) & np.isfinite(QS))
        print("  K5-0 rollierende Auswahl im Urteilszeitraum %d (W2: 29.390) -> %s" % (
            int(SEL[urteil_all].sum()), "✔" if int(SEL[urteil_all].sum()) == 29390 or E2.MENGE != "bestand" else "⛔"))
        with np.errstate(divide="ignore", invalid="ignore"):
            VH = _ex(np.log(QSh / (1 - QSh)) + Ch) - QSh
        g = np.flatnonzero(BASIS & np.isfinite(VH) & np.isfinite(QS) & np.isin(JAHR, JAHRE))
        print("  Gitteranker im Auswertungszeitraum %d · Symbole %d" % (len(g), len(np.unique(SYM[g]))))
        # Auskunft (vor dem Lauf ergaenzt, 29.09.): Verteilung von vh - KEINE Schwelle daraus (K5: absolut, kein Rang)
        print("  Auskunft Verteilung vh: P50 %+.4f · P90 %+.4f · P95 %+.4f · P99 %+.4f · Max %+.4f" % tuple(
            np.percentile(VH[g], [50, 90, 95, 99, 100])))
        # ══ KERNMESSUNG Schritt 1 (Voranalyse_Kern_Einstieg_Hebel_29_09.md, N1-N4) ══════════════
        # Ersteintritt in der gegengeprueften Fassung: erste Stunde mit vh >= s, davor 24 h mit >= 20 GUELTIGEN
        # Stunden alle darunter, nicht in den ersten 24 h eines Monats; Einstieg eine Stunde spaeter.
        # WAHL (ohne --bestaetigen): nur 2024, Raster +0,010..+0,050, Regel: groesster Abstand echt - P90 Nullwelt,
        # bei Gleichstand (< 0,005) die niedrigere Stufe. BESTAETIGUNG (--bestaetigen s): einmal 2025-01..2026-08.
        if "--kern" in sys.argv or "--l2" in sys.argv:
            MS = np.array([H(datetime(2020 + mm // 12, mm % 12 + 1, 1)) for mm in range(0, 12 * 8)])

            def erst_v(VHx, s):
                aus = []
                for tl in teile:
                    st = STD[tl]; vv = VHx[tl]
                    fin = np.isfinite(vv)
                    ab_ = np.where(fin, vv >= s, False)
                    cs = np.concatenate([[0], np.cumsum(ab_)]); cf = np.concatenate([[0], np.cumsum(fin)])
                    lo = np.searchsorted(st, st - 24, "left")
                    idx = np.arange(len(tl))
                    erst = ab_ & ((cs[idx] - cs[lo]) == 0) & ((cf[idx] - cf[lo]) >= 20)
                    erst &= (st - MS[np.clip(MON[tl] - 2020 * 12, 0, len(MS) - 1)]) >= 24
                    i_ = np.flatnonzero(erst)
                    i_ = i_[i_ + 1 < len(tl)]
                    i_ = i_[st[i_ + 1] == st[i_] + 1]
                    aus.append(tl[i_ + 1])
                e_ = np.concatenate(aus) if aus else np.zeros(0, int)
                return e_[np.isin(JAHR[e_], JAHRE) & np.isfinite(QSh[e_])]

            def dqh(ix, y=A24):
                ix = ix[np.isfinite(QSh[ix])]
                return dq(ix, y, QSh * (NA + NB), (1 - QSh) * (NA + NB)) if len(ix) else np.nan
            h_ab = np.flatnonzero(np.isfinite(QSh) & np.isin(JAHR, JAHRE) & np.isfinite(OFF))

            def vh_stuendlich(EE):
                v = np.full(n, np.nan)
                for mi, m in modelle:
                    ixm = h_ab[MON[h_ab] == mi]
                    if len(ixm):
                        c = m.z(EE, ixm, OFF[ixm]) - OFF[ixm]
                        v[ixm] = _ex(np.log(QSh[ixm] / (1 - QSh[ixm])) + c) - QSh[ixm]
                return v
            print()
            print("=" * 120)
            if "--l2" in sys.argv:
                import json
                S_KERN = 0.035
                wahl = not best
                JS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "_vergleich", "l2_wahl_bestand.json")

                def erst_p(VHx, s, fenster=24, verzug=1):
                    aus = []
                    for tl in teile:
                        st = STD[tl]; vv = VHx[tl]
                        fin = np.isfinite(vv)
                        ab_ = np.where(fin, vv >= s, False)
                        cs = np.concatenate([[0], np.cumsum(ab_)]); cf = np.concatenate([[0], np.cumsum(fin)])
                        lo = np.searchsorted(st, st - fenster, "left")
                        idx = np.arange(len(tl))
                        erst = ab_ & ((cs[idx] - cs[lo]) == 0) & ((cf[idx] - cf[lo]) >= int(fenster * 20 / 24))
                        erst &= (st - MS[np.clip(MON[tl] - 2020 * 12, 0, len(MS) - 1)]) >= 24
                        i_ = np.flatnonzero(erst)
                        i_ = i_[i_ + verzug < len(tl)]
                        i_ = i_[st[i_ + verzug] == st[i_] + verzug]
                        aus.append(np.stack([tl[i_ + verzug], tl[i_]]) if len(i_) else np.zeros((2, 0), int))
                    e_ = np.concatenate(aus, axis=1) if aus else np.zeros((2, 0), int)
                    ok_ = np.isin(JAHR[e_[0]], JAHRE) & np.isfinite(QSh[e_[0]])
                    return e_[0][ok_], e_[1][ok_]          # Einstieg, Signalstunde

                # Normal fuer Potential und Risiko: eigenes Asset, eigene letzte 12 Monate, nur bekannte Ausgaenge (t-24)
                def normal_mittel(v, W=24):
                    out = np.full(n, np.nan)
                    for tl in teile:
                        st = STD[tl]; x = v[tl]; ok_ = np.isfinite(x)
                        cx = np.concatenate([[0.0], np.cumsum(np.where(ok_, x, 0.0))]); ck = np.concatenate([[0], np.cumsum(ok_)])
                        lo = np.searchsorted(st, st - K2.JAHR_H, "left"); hi = np.searchsorted(st, st - W, "right")
                        k = ck[hi] - ck[lo]
                        out[tl] = np.where(k > 1000, (cx[hi] - cx[lo]) / np.maximum(k, 1), np.nan)
                    return out
                with np.errstate(divide="ignore", invalid="ignore"):
                    POT = L2_MFE[24] / (100.0 * np.maximum(ATR, 1e-12)); RIS = L2_MAE[24] / (100.0 * np.maximum(ATR, 1e-12))
                POTn, RISn = POT - normal_mittel(POT), RIS - normal_mittel(RIS)
                ee, es = erst_p(VH, S_KERN)
                n_roh = len(ee)
                ok = np.isfinite(POTn[ee]) & np.isfinite(RISn[ee])
                ee, es = ee[ok], es[ok]
                print("L2 · %s · Menge %s · Kern-Ersteintritte s = %+.3f: %d vor dem Potential-Filter (R-R11: Wahl 2024 bestand 2.095, Bestaetigung bestand 10.534), %d mit Potential und Risiko (Tage %d)" % (
                    "WAHL 2024 (2025-26 wird NICHT ausgewertet)" if wahl else "BESTAETIGUNG 2025-01..2026-08 (EINMAL)",
                    E2.MENGE, S_KERN, n_roh, len(ee), len(np.unique(STD[ee] // 24))))
                print("  Kern gesamt: Chance Dq %+.4f · Potential %+.3f ATR ueber dem Normal (MFE 24 h) · Risiko %+.3f ATR (Rueckgang vor dem Hoch)" % (
                    dqh(ee), float(np.mean(POTn[ee])), float(np.mean(RISn[ee]))))

                def mass(ix):
                    return (dqh(ix), float(np.mean(POTn[ix])) if len(ix) else np.nan, float(np.mean(RISn[ix])) if len(ix) else np.nan)
                # Kandidaten: roh, funding/konten in Markt und Eigen geteilt
                CAND = {k: L2_F[k] for k in ("volumenschub", "vola_kausal", "oi_aenderung", "oi_je_umsatz", "bandenge",
                                             "ema_abstand_atr", "taker_verh", "top_konten_verh")}
                ko24 = mittel24(L2_F["konten_verh"])
                MARKT = {}
                for kurz, v in (("funding", L2_F["funding_vortag"]), ("konten", ko24)):
                    mk = pd.Series(v).groupby(STD).median().reindex(STD).to_numpy()
                    MARKT[kurz + "_markt"] = mk
                    CAND[kurz + "_eigen"] = v - mk
                CAND.update(MARKT)
                stunden = np.unique(STD)
                idx_st = np.searchsorted(stunden, STD)

                def verschiebe(name, v):
                    if name.endswith("_markt"):
                        ser = pd.Series(v).groupby(STD).first().to_numpy()
                        k_ = int(rng.integers(1440, len(stunden) - 1440))
                        return ser[(idx_st + k_) % len(stunden)]
                    out = np.empty(n)
                    for tl in teile:
                        L_ = len(tl)
                        k_ = int(rng.integers(K2.MIN_VERSATZ, L_ - K2.MIN_VERSATZ)) if L_ > 2 * K2.MIN_VERSATZ else 0
                        out[tl] = np.roll(v[tl], k_)
                    return out

                def drittel_diff(werte, ix, kanten):
                    w = werte[ix]; fin = np.isfinite(w)
                    oben = ix[fin & (w > kanten[1])]; unten = ix[fin & (w <= kanten[0])]
                    mo, mu = mass(oben), mass(unten)
                    return tuple(a - b for a, b in zip(mo, mu)), len(oben), len(unten)
                ST = VH[es]
                if wahl:
                    # ── TEIL A: Staerke (Vorsprung in der Signalstunde), fuenf Klassen, Grenzen aus 2024 ──
                    kA = np.quantile(ST, [0.2, 0.4, 0.6, 0.8]).tolist()
                    kl = np.searchsorted(kA, ST, "right")
                    print()
                    print("  TEIL A1 Staerke (Vorsprung in der Signalstunde), fuenf Klassen:")
                    kal = []
                    for c in range(5):
                        m_ = mass(ee[kl == c]); kal.append(m_)
                        print("    Klasse %d (%d): Chance %+.4f · Potential %+.3f ATR · Risiko %+.3f ATR" % (c + 1, int((kl == c).sum()), *m_))
                    print("    staerkste minus schwaechste: Chance %+.4f · Potential %+.3f · Risiko %+.3f" % tuple(a - b for a, b in zip(kal[4], kal[0])))
                    print("  TEIL A3 Regelparameter (Auskunft, 2024): Wartezeit / Verzug -> Einstiege, Chance, Potential")
                    for fe, vz in ((12, 1), (24, 1), (48, 1), (24, 2), (24, 4)):
                        e2_, _s2 = erst_p(VH, S_KERN, fe, vz)
                        e2_ = e2_[np.isfinite(POTn[e2_])]
                        m_ = mass(e2_)
                        print("    %2d h / %d h: %5d · Chance %+.4f · Potential %+.3f ATR" % (fe, vz, len(e2_), m_[0], m_[1]))
                    # ── TEIL B: Kandidaten, Drittel-Grenzen aus 2024, Nullwelt je Kandidat ──
                    print()
                    print("  TEIL B Kandidaten auf den Kern-Einstiegen (oberes minus unteres Drittel; Nullwelt %d Ziehungen, P75 |Delta|):" % zieh)
                    kanten, ergebnis = {}, {}
                    for nm_, v in CAND.items():
                        w = v[ee]; fin = np.isfinite(w)
                        if fin.sum() < 300:
                            print("    %-17s zu wenige Werte (%d)" % (nm_, int(fin.sum())))
                            continue
                        kk = np.quantile(w[fin], [1 / 3, 2 / 3]).tolist(); kanten[nm_] = kk
                        d_, no, nu = drittel_diff(v, ee, kk)
                        nd = []
                        for _ in range(zieh):
                            vv = verschiebe(nm_, v)
                            w2 = vv[ee]; f2 = np.isfinite(w2)
                            k2 = np.quantile(w2[f2], [1 / 3, 2 / 3]) if f2.sum() > 30 else kk
                            nd.append(drittel_diff(vv, ee, k2)[0])
                        nd = np.array(nd)
                        ergebnis[nm_] = dict(d=d_, p75=np.nanpercentile(np.abs(nd), 75, axis=0).tolist(),
                                             sd=np.nanstd(nd, axis=0, ddof=1).tolist(), n=(no, nu))
                        print("    %-17s oben/unten %4d/%4d · dChance %+.4f (P75 %.4f) · dPotential %+.3f (P75 %.3f) · dRisiko %+.3f (P75 %.3f)" % (
                            nm_, no, nu, d_[0], ergebnis[nm_]["p75"][0], d_[1], ergebnis[nm_]["p75"][1], d_[2], ergebnis[nm_]["p75"][2]))
                    # Filter: je Mass hoechstens drei, |Delta| ueber P75, erwartete Richtung = Chance/Potential hoch, Risiko tief
                    weiter = {}
                    for j_, nm_mass, gut in ((0, "Chance", 1), (1, "Potential", 1), (2, "Risiko", -1)):
                        kand = []
                        for nm_, e_ in ergebnis.items():
                            d = e_["d"][j_]
                            if np.isfinite(d) and abs(d) > e_["p75"][j_]:
                                # Richtung: das Drittel, das im Sinn des Masses besser ist, wird Kennzeichen
                                kand.append((abs(d) / max(e_["sd"][j_], 1e-12), nm_, 1 if d * gut > 0 else -1))
                        kand.sort(reverse=True)
                        weiter[nm_mass] = [(nm_, rich) for _z, nm_, rich in kand[:3]]
                        print("  WEITER (%s): %s" % (nm_mass, ", ".join("%s (%s)" % (a, "oben" if r > 0 else "unten") for a, r in weiter[nm_mass]) or "keiner"))
                    json.dump(dict(kA=kA, kal=kal, kanten=kanten, weiter=weiter), open(JS, "w", encoding="utf-8"), indent=1)
                    print("  festgehalten fuer die Bestaetigung: %s" % JS)
                    # Leiter (Aufloesung) auf 2024 fuer das Potential, an volumenschub (verschoben)
                    if "volumenschub" in kanten:
                        p75 = ergebnis["volumenschub"]["p75"][1]
                        for d_pl in (0.1, 0.2, 0.4):
                            gef = 0
                            for _ in range(5):
                                vv = verschiebe("volumenschub", CAND["volumenschub"])
                                w2 = vv[ee]; f2 = np.isfinite(w2); k2 = np.quantile(w2[f2], [1 / 3, 2 / 3])
                                POT_s = POTn.copy()
                                ob = ee[f2 & (w2 > k2[1])]
                                POTn[ob] = POTn[ob] + d_pl
                                gef += int(abs(drittel_diff(vv, ee, k2)[0][1]) > p75)
                                POTn[:] = POT_s
                            print("  Leiter Potential +%.1f ATR (volumenschub verschoben): gefunden %d von 5" % (d_pl, gef))
                else:
                    cfg = json.load(open(JS, encoding="utf-8"))
                    if "--gegen-atr" in sys.argv:
                        # ── G-ATR (Voranalyse L2 Abschnitt 14, vorab): traegt Teil B auch OHNE die ATR beim Einstieg? ──
                        from scipy.stats import spearmanr
                        ATRrel = ATR / normal_mittel(ATR, W=1)
                        ok_ = np.isfinite(ATRrel[ee]); ee = ee[ok_]
                        print()
                        print("  G-ATR · %d Einstiege · ATRrel P10/P50/P90 %.2f / %.2f / %.2f" % (
                            len(ee), *np.percentile(ATRrel[ee], [10, 50, 90])))
                        POTp = L2_MFE[24] - normal_mittel(L2_MFE[24]); RISp = L2_MAE[24] - normal_mittel(L2_MAE[24])
                        POTa, RISa = POTn, RISn

                        def geschichtet(nm_, ix, j_, rich, gut):
                            kr = np.quantile(ATRrel[ix], [1 / 3, 2 / 3]); ka = np.searchsorted(kr, ATRrel[ix], "right")
                            w_ = []
                            for c in range(3):
                                d_, no_, nu_ = drittel_diff(CAND[nm_], ix[ka == c], cfg["kanten"][nm_])
                                w_.append(d_[j_] * rich * gut if min(no_, nu_) >= 30 else np.nan)
                            return float(np.mean(w_)), w_
                        for j_, nm_mass, gut in ((0, "Chance", 1), (1, "Potential", 1), (2, "Risiko", -1)):
                            for nm_, rich in cfg["weiter"].get(nm_mass, []):
                                w = CAND[nm_][ee]; f_ = np.isfinite(w)
                                rho = float(spearmanr(w[f_], ATRrel[ee][f_])[0])
                                roh = drittel_diff(CAND[nm_], ee, cfg["kanten"][nm_])[0][j_] * rich * gut
                                g_all, g_c = geschichtet(nm_, ee, j_, rich, gut)
                                gj = [geschichtet(nm_, ee[JAHR[ee] == jj], j_, rich, gut)[0] for jj in JAHRE]
                                POTn, RISn = POTp, RISp
                                pz = drittel_diff(CAND[nm_], ee, cfg["kanten"][nm_])[0][j_] * rich * gut
                                pzj = [drittel_diff(CAND[nm_], ee[JAHR[ee] == jj], cfg["kanten"][nm_])[0][j_] * rich * gut for jj in JAHRE]
                                POTn, RISn = POTa, RISa
                                g1 = all(x > 0 for x in gj) and roh > 0 and g_all >= 0.5 * roh
                                print("    %s · %-17s (%s): rho(ATRrel) %+.2f · roh %+.4f · geschichtet %+.4f (Drittel %s) · je Jahr %s · %s"
                                      " · Prozentmass %+.3f (%s)" % (
                                          nm_mass, nm_, "oben" if rich > 0 else "unten", rho, roh, g_all,
                                          " / ".join("%+.4f" % x for x in g_c),
                                          " · ".join("%d %+.4f" % (jj, x) for jj, x in zip(JAHRE, gj)),
                                          "✔ G1 ATR-frei (diese Menge)" if g1 else "⛔ G1",
                                          pz, " · ".join("%d %+.3f" % (jj, x) for jj, x in zip(JAHRE, pzj))))
                        print("SCHLUSS: vollstaendig")
                        return 0
                    kA = cfg["kA"]
                    kl = np.searchsorted(kA, ST, "right")
                    print()
                    print("  TEIL A1 Staerke (Grenzen aus der Wahl 2024):")
                    beob = []
                    for c in range(5):
                        m_ = mass(ee[kl == c]); beob.append(m_)
                        print("    Klasse %d (%d): Chance %+.4f · Potential %+.3f · Risiko %+.3f   (Wahl: %+.4f / %+.3f / %+.3f)" % (
                            c + 1, int((kl == c).sum()), *m_, *cfg["kal"][c]))
                    dA = [a - b for a, b in zip(beob[4], beob[0])]
                    jA = []
                    for jj in JAHRE:
                        mj = np.isin(ee, ee[JAHR[ee] == jj])
                        a4 = mass(ee[(kl == 4) & mj]); a0 = mass(ee[(kl == 0) & mj])
                        jA.append((jj, a4[0] - a0[0], a4[1] - a0[1]))
                    nA = []
                    for _ in range(zieh):
                        v_ = vh_stuendlich(verschoben(E, RSI))
                        e2_, s2_ = erst_p(v_, S_KERN)
                        f_ = np.isfinite(POTn[e2_]); e2_, s2_ = e2_[f_], s2_[f_]
                        k2 = np.searchsorted(kA, v_[s2_], "right")
                        nA.append([a - b for a, b in zip(mass(e2_[k2 == 4]), mass(e2_[k2 == 0]))])
                    nA = np.array(nA)
                    print("    A1 staerkste minus schwaechste: Chance %+.4f (Null P90 %+.4f) · Potential %+.3f (Null P90 %+.3f) · je Jahr %s" % (
                        dA[0], float(np.nanpercentile(nA[:, 0], 90)), dA[1], float(np.nanpercentile(nA[:, 1], 90)),
                        " · ".join("%d %+.4f / %+.3f" % x for x in jA)))
                    gk = [cfg["kal"][c][1] for c in range(5)]; bk = [beob[c][1] for c in range(5)]
                    print("    A2 Kalibrierung Potential (Wahl -> beobachtet je Klasse): Steigung %.2f" % float(np.polyfit(gk, bk, 1)[0]))
                    # ── N2 (Voranalyse L2 Abschnitt 13, VOR der Bestaetigung): die laengere RUHE vor dem Ueberschreiten ──
                    print()
                    print("  N2 RUHE davor (Kriterium: 48 h schlaegt 24 h in Chance UND Potential, 2025 und 2026; 72/96 h Auskunft):")
                    A3 = {}
                    for fe in (24, 48, 72, 96):
                        e3, _s3 = erst_p(VH, S_KERN, fe, 1)
                        e3 = e3[np.isfinite(POTn[e3])]
                        A3[fe] = e3
                        jz = " · ".join("%d %+.4f / %+.3f (%d)" % (jj, *mass(e3[JAHR[e3] == jj])[:2], int((JAHR[e3] == jj).sum())) for jj in JAHRE)
                        print("    %2d h: %5d Einstiege · Chance %+.4f · Potential %+.3f ATR · je Jahr %s" % (fe, len(e3), *mass(e3)[:2], jz))
                    n2 = []
                    for jj in JAHRE:
                        m48 = mass(A3[48][JAHR[A3[48]] == jj]); m24 = mass(A3[24][JAHR[A3[24]] == jj])
                        n2.append((jj, m48[0] - m24[0], m48[1] - m24[1]))
                    ok2 = all(x[1] > 0 and x[2] > 0 for x in n2)
                    # Gegenpruefung Auswahlanteil: 24 h zufaellig auf die Zahl von 48 h ausgeduennt (40 Ziehungen)
                    rz = np.random.default_rng(SAAT + 48); dd = []
                    for _ in range(zieh):
                        sub = rz.choice(A3[24], size=len(A3[48]), replace=False)
                        dd.append(mass(sub)[:2])
                    dd = np.array(dd)
                    print("    48 h minus 24 h je Jahr: %s -> %s" % (" · ".join("%d Chance %+.4f / Potential %+.3f" % x for x in n2),
                                                               "✔ (diese Menge)" if ok2 else "⛔"))
                    print("    Gegenpruefung: 24 h auf %d ausgeduennt - Chance P90 %+.4f, Potential P90 %+.3f gegen 48 h %+.4f / %+.3f" % (
                        len(A3[48]), float(np.nanpercentile(dd[:, 0], 90)), float(np.nanpercentile(dd[:, 1], 90)), *mass(A3[48])[:2]))
                    # TEIL B: nur die weitergereichten Kandidaten, Bestes-von-k
                    print()
                    print("  TEIL B Bestaetigung (nur die auf 2024 weitergereichten, Richtung aus der Wahl, Bestes-von-k):")
                    for j_, nm_mass, gut in ((0, "Chance", 1), (1, "Potential", 1), (2, "Risiko", -1)):
                        liste = cfg["weiter"].get(nm_mass, [])
                        if not liste:
                            print("    %s: keiner weitergereicht" % nm_mass)
                            continue
                        echt = {}
                        for nm_, rich in liste:
                            d_, _no, _nu = drittel_diff(CAND[nm_], ee, cfg["kanten"][nm_])
                            echt[nm_] = d_[j_] * rich * gut           # positiv = im Sinn des Masses besser
                        nmax = []
                        for _ in range(zieh):
                            best_ = -np.inf
                            for nm_, rich in liste:
                                vv = verschiebe(nm_, CAND[nm_])
                                w2 = vv[ee]; f2 = np.isfinite(w2)
                                k2 = np.quantile(w2[f2], [1 / 3, 2 / 3]) if f2.sum() > 30 else cfg["kanten"][nm_]
                                best_ = max(best_, drittel_diff(vv, ee, k2)[0][j_] * rich * gut)
                            nmax.append(best_)
                        p90 = float(np.nanpercentile(nmax, 90))
                        for nm_, rich in liste:
                            jz = []
                            for jj in JAHRE:
                                ixj = ee[JAHR[ee] == jj]
                                jz.append(drittel_diff(CAND[nm_], ixj, cfg["kanten"][nm_])[0][j_] * rich * gut)
                            # je Asset
                            ga = []
                            for si in np.unique(SYM[ee]):
                                ixa = ee[SYM[ee] == si]
                                w = CAND[nm_][ixa]
                                o_ = ixa[w > cfg["kanten"][nm_][1]]; u_ = ixa[w <= cfg["kanten"][nm_][0]]
                                if len(o_) >= 10 and len(u_) >= 10:
                                    ga.append((mass(o_)[j_] - mass(u_)[j_]) * rich * gut > 0)
                            # Tagesblock-Bootstrap
                            tage = STD[ee] // 24; ut, tinv = np.unique(tage, return_inverse=True)
                            je_tag = [ee[tinv == k] for k in range(len(ut))]
                            rb = np.random.default_rng(SAAT + 7); bo = []
                            for _ in range(300):
                                w_ = rb.integers(0, len(ut), len(ut))
                                ixb = np.concatenate([je_tag[k] for k in w_])
                                bo.append(drittel_diff(CAND[nm_], ixb, cfg["kanten"][nm_])[0][j_] * rich * gut)
                            lo95 = float(np.nanpercentile(bo, 2.5))
                            urteil = (echt[nm_] > p90 and all(x > 0 for x in jz) and (np.mean(ga) >= 0.6 if ga else False) and lo95 > 0)
                            print("    %s · %-17s (%s): %+.4f gegen Bestes-von-%d P90 %+.4f · je Jahr %s · Assets %d, %.0f %% · Tagesblock unten %+.4f -> %s" % (
                                nm_mass, nm_, "oben" if rich > 0 else "unten", echt[nm_], len(liste), p90,
                                " · ".join("%d %+.4f" % (jj, x) for jj, x in zip(JAHRE, jz)), len(ga),
                                100 * np.mean(ga) if ga else np.nan, lo95, "✔ TRAEGT (diese Menge)" if urteil else "⛔"))
                print("SCHLUSS: vollstaendig")
                return 0
            if "--export" in sys.argv:
                # ══ KERN SCHRITT 2 (Voranalyse_Kern_Schritt2_H0_29_09.md): die Ersteintritte 2024-01..2026-08 fuer
                # H0 exportieren und die CHANCE im selben Fenster 6/12/24 h (Vergleich, keine Kalibrierung) ══
                s = float(sys.argv[sys.argv.index("--export") + 1])
                ee = np.sort(erst_v(VH, s))
                print("KERN SCHRITT 2 · EXPORT der Ersteintritte s = %+.3f, 2024-01..2026-08, Menge %s: %d Einstiege, %d Tage" % (
                    s, E2.MENGE, len(ee), len(np.unique(STD[ee] // 24))))
                print("  Chance im Fenster (roher 12-Monats-Normal je Fenster, NUR Vergleich):")
                for w in (6, 12, 24):
                    Aw = ((t_u <= w) & (t_u < t_d)).astype(np.float64); Bw = ((t_d <= w) & (t_d <= t_u)).astype(np.float64)
                    NAw, NBw = normal(Aw, Bw, w)
                    hw = (Aw + Bw) > 0
                    jz = " · ".join("%d %+.4f" % (jj, dq(ee[JAHR[ee] == jj], Aw, NAw, NBw, hw)) for jj in (2024, 2025, 2026))
                    print("    %2d h: +5 %% vor -5 %% bei %.1f %% der Einstiege (-5 %% zuerst %.1f %%) · Dq gesamt %+.4f · %s" % (
                        w, 100 * Aw[ee].mean(), 100 * Bw[ee].mean(), dq(ee, Aw, NAw, NBw, hw), jz))
                up = t_u[ee][(t_u[ee] < t_d[ee]) & np.isfinite(t_u[ee]) & (t_u[ee] <= 72)]
                dn = t_d[ee][(t_d[ee] <= t_u[ee]) & np.isfinite(t_d[ee]) & (t_d[ee] <= 72)]
                print("  Zeit bis +5 %% (wo zuerst, binnen 72 h, %d): Median %.0f h · Quartile %.0f / %.0f h · binnen 2/4/6/12 h %s" % (
                    len(up), np.median(up), np.percentile(up, 25), np.percentile(up, 75),
                    " / ".join("%.0f %%" % (100 * np.mean(up <= k)) for k in (2, 4, 6, 12))))
                print("  Zeit bis -5 %% (wo zuerst, binnen 72 h, %d): Median %.0f h · Quartile %.0f / %.0f h · binnen 2/4/6/12 h %s" % (
                    len(dn), np.median(dn), np.percentile(dn, 25), np.percentile(dn, 75),
                    " / ".join("%.0f %%" % (100 * np.mean(dn <= k)) for k in (2, 4, 6, 12))))
                ziel = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "_vergleich",
                                    "kern_einstiege_%s.csv" % E2.MENGE.replace(":", "_"))
                os.makedirs(os.path.dirname(ziel), exist_ok=True)
                with io.open(ziel, "w", encoding="utf-8") as f_:
                    f_.write("symbol;stunde;jahr;t_u;t_d\n")
                    for i in ee:
                        f_.write("%s;%d;%d;%s;%s\n" % (SYMS[int(SYM[i])], int(STD[i]), int(JAHR[i]),
                                                       "%.0f" % t_u[i] if np.isfinite(t_u[i]) else "",
                                                       "%.0f" % t_d[i] if np.isfinite(t_d[i]) else ""))
                print("  geschrieben: %s" % ziel)
                print("SCHLUSS: vollstaendig")
                return 0
            if not best:
                RASTER = [round(0.010 + 0.005 * i, 3) for i in range(9)]
                print("KERN SCHRITT 1 · WAHL DER SCHWELLE auf 2024 (Menge %s) - 2025-26 wird NICHT ausgewertet" % E2.MENGE)
                EE_ = {s: erst_v(VH, s) for s in RASTER}
                echt = {s: dqh(EE_[s]) for s in RASTER}
                for s, soll in ((0.02, 0.0928), (0.04, 0.0759)):
                    print("  R-R11 2.687 (c) Stufe %+.3f: %+.4f · Soll %+.4f -> %s" % (
                        s, echt[s], soll, "✔ bitgleich" if abs(round(echt[s], 4) - soll) < 1e-9 or E2.MENGE != "bestand" else "⛔ ABWEICHUNG"))
                null = {s: [] for s in RASTER}
                for _ in range(zieh):
                    v_ = vh_stuendlich(verschoben(E, RSI))
                    for s in RASTER:
                        null[s].append(dqh(erst_v(v_, s)))
                print("    %-8s %8s %8s %10s %10s %10s %10s" % ("Stufe", "Einstiege", "Tage", "echt", "Null Mittel", "Null P90", "Abstand"))
                abst = {}
                for s in RASTER:
                    p90 = float(np.nanpercentile(null[s], 90)); abst[s] = echt[s] - p90
                    print("    %+.3f   %8d %8d %+10.4f %+10.4f %+10.4f %+10.4f" % (
                        s, len(EE_[s]), len(np.unique(STD[EE_[s]] // 24)), echt[s], float(np.nanmean(null[s])), p90, abst[s]))
                mx = max(abst.values())
                wahl = min(s for s in RASTER if abst[s] >= mx - 0.005)
                print("  REGEL groesster Abstand (Gleichstand < 0,005 -> niedrigere Stufe): hoechster Abstand %+.4f -> GEWAEHLT s = %+.3f" % (mx, wahl))
            else:
                s = s_best
                print("KERN SCHRITT 1 · BESTAETIGUNG 2025-01..2026-08, Stufe %+.3f, Menge %s (EINMAL)" % (s, E2.MENGE))
                ee = erst_v(VH, s)
                gesamt = dqh(ee)
                jz = [(jj, dqh(ee[JAHR[ee] == jj]), int((JAHR[ee] == jj).sum())) for jj in JAHRE]
                b1 = all(x[1] > 0 for x in jz)
                nv = [dqh(erst_v(vh_stuendlich(verschoben(E, RSI)), s)) for _ in range(zieh)]
                p90 = float(np.nanpercentile(nv, 90)); b2 = gesamt > p90
                ga = [dqh(ee[SYM[ee] == si]) > 0 for si in np.unique(SYM[ee]) if (SYM[ee] == si).sum() >= 20]
                b4 = float(np.mean(ga)) if ga else np.nan
                bs0, bs1 = H(datetime(2025, 10, 10)) - 24, H(datetime(2025, 10, 12))
                ohne = ee[(STD[ee] < bs0) | (STD[ee] >= bs1)]
                print("  Einstiege %d an %d verschiedenen Tagen · Dq gesamt %+.4f" % (len(ee), len(np.unique(STD[ee] // 24)), gesamt))
                print("  B1 je Jahr: %s -> %s" % (" · ".join("%d %+.4f (%d)" % x for x in jz), "✔" if b1 else "⛔"))
                print("  B2 Nullwelt (%d Ziehungen) Mittel %+.4f, P90 %+.4f -> %s" % (zieh, float(np.nanmean(nv)), p90, "✔" if b2 else "⛔"))
                print("  B4 je Asset (>= 20 Einstiege): %d Assets, Dq > 0 bei %.0f %% -> %s" % (len(ga), 100 * b4, "✔" if b4 >= 0.6 else "⛔"))
                print("  B5 ohne 10./11.10.2025: %d Einstiege, Dq %+.4f (mit %+.4f)" % (len(ohne), dqh(ohne), gesamt))
                # B6 (Voranalyse Abschnitt 10, vor der Bestaetigung): Tagesblock-Bootstrap - die Einstiege TAGEWEISE
                # gezogen (die Ballung an Markttagen ist normales Marktverhalten und bleibt drin; nur die
                # Unsicherheit wird ueber die Tage statt ueber die Einstiege gerechnet), 1.000 Ziehungen
                tage = STD[ee] // 24
                ut, tinv = np.unique(tage, return_inverse=True)
                je_tag = [ee[tinv == k] for k in range(len(ut))]
                rb = np.random.default_rng(SAAT + 6)
                boot = []
                for _ in range(1000):
                    w_ = rb.integers(0, len(ut), len(ut))
                    boot.append(dqh(np.concatenate([je_tag[k] for k in w_])))
                lo95, hi95 = np.nanpercentile(boot, [2.5, 97.5])
                b6 = lo95 > 0
                print("  B6 Tagesblock-Bootstrap (%d Tage, 1.000 Ziehungen): 95-%%-Intervall %+.4f .. %+.4f -> %s" % (
                    len(ut), lo95, hi95, "✔" if b6 else "⛔"))
                zst = dqs(g[VH[g] >= s])
                print("  Auskunft Zustand (Gitteranker vh >= s): %+.4f gegen Ersteintritt %+.4f" % (zst, gesamt))
                for k in (2, 6):
                    pos = ee + (k - 1)
                    okp = (pos < n)
                    pos = pos[okp]; e0 = ee[okp]
                    okp = (SYM[pos] == SYM[e0]) & (STD[pos] == STD[e0] + (k - 1))
                    print("  Auskunft Einstieg %d h nach dem Signal: %d · Dq %+.4f" % (k, int(okp.sum()), dqh(pos[okp])))
                print("  Auskunft je Monat: " + " · ".join("%d-%02d %+.3f (%d)" % (mm // 12, mm % 12 + 1, dqh(ee[MON[ee] == mm]), int((MON[ee] == mm).sum()))
                                                          for mm in np.unique(MON[ee])))
                print("  URTEIL SCHRITT 1 (Menge %s): B1 %s · B2 %s · B4 %s · B6 %s  (B3 ueber die vier Mengen)" % (
                    E2.MENGE, "✔" if b1 else "⛔", "✔" if b2 else "⛔", "✔" if b4 >= 0.6 else "⛔", "✔" if b6 else "⛔"))
            print("SCHLUSS: vollstaendig")
            return 0

        # ── K5-1 Kalibrierung je Zehntel von vh ──
        kant = np.quantile(VH[g], np.linspace(0, 1, 11)[1:-1]); zg = np.searchsorted(kant, VH[g], "right")
        ges, beo = [], []
        for d_ in range(10):
            ix = g[zg == d_]
            ges.append(float(np.mean(VH[ix]))); beo.append(dqs(ix))
        steig = float(np.polyfit(ges, beo, 1)[0])
        print()
        print("  K5-1 KALIBRIERUNG je Zehntel (geschaetzt -> beobachtet): " + " · ".join("%+.3f->%+.3f" % (a, b) for a, b in zip(ges, beo)))
        print("       Steigung %.2f (Soll 0,7-1,3) · oberstes Zehntel |gesch - beob| %.4f (Soll <= 0,02) -> %s" % (
            steig, abs(ges[-1] - beo[-1]), "✔" if 0.7 <= steig <= 1.3 and abs(ges[-1] - beo[-1]) <= 0.02 else "⛔"))
        for jj in JAHRE:
            ixj = g[JAHR[g] == jj]
            kj = np.quantile(VH[ixj], np.linspace(0, 1, 11)[1:-1]); zj = np.searchsorted(kj, VH[ixj], "right")
            gj = [float(np.mean(VH[ixj[zj == d_]])) for d_ in range(10)]; bj = [dqs(ixj[zj == d_]) for d_ in range(10)]
            print("       %d: Steigung %.2f · oberstes Zehntel gesch %+.4f beob %+.4f" % (jj, float(np.polyfit(gj, bj, 1)[0]), gj[-1], bj[-1]))
        sel_g = g[SEL[g]]
        print("  Auswahl (Trainingsgrenze P90): %d Anker · geschaetzt %+.4f · beobachtet %+.4f" % (
            len(sel_g), float(np.mean(VH[sel_g])), dqs(sel_g)))

        # ── K5-6 Ersteintritt (stuendlich, Einstieg eine Stunde spaeter) ──
        def ersteintritte(s):
            aus = []
            for tl in teile:
                st = STD[tl]; vv = VH[tl]
                ab_ = np.where(np.isfinite(vv), vv >= s, False)
                cs = np.concatenate([[0], np.cumsum(ab_)])
                lo = np.searchsorted(st, st - 24, "left")
                idx = np.arange(len(tl))
                erst = ab_ & ((cs[idx] - cs[lo]) == 0) & ((idx - lo) >= 20)
                i_ = np.flatnonzero(erst)
                i_ = i_[i_ + 1 < len(tl)]
                i_ = i_[st[i_ + 1] == st[i_] + 1]
                aus.append(tl[i_ + 1])
            e_ = np.concatenate(aus) if aus else np.zeros(0, int)
            return e_[np.isin(JAHR[e_], JAHRE) & np.isfinite(QSh[e_])]

        def dqh(ix, y=A24):
            ix = ix[np.isfinite(QSh[ix])]
            w = NA[ix] + NB[ix]
            return dq(ix, y, QSh * (NA + NB), (1 - QSh) * (NA + NB))
        am = np.unique(SYM[g].astype(np.int64) * 100000 + MON[g])
        print()
        print("  K5-2 TABELLE (Signal) und K5-6 ERSTEINTRITT (Einstieg 1 h nach dem ersten Ueberschreiten, davor 24 h darunter)")
        print("    %-8s %8s %8s %10s %10s | %10s %10s %10s %s" % (
            "Schwelle", "Anteil", "Anker", "gesch.", "beob.", "Ersteintr.", "je As.-Mo.", "beob.", "K5-6"))
        tab = {}
        for s in SCHW:
            ix = g[VH[g] >= s]
            ee = ersteintritte(s)
            zst, ers = dqs(ix), dqh(ee)
            ok6 = ers > 0 and ers >= 0.5 * zst
            tab[s] = (zst, ers)
            print("    %+.2f    %7.1f%% %8d %+10.4f %+10.4f | %10d %10.2f %+10.4f %s" % (
                s, 100 * len(ix) / len(g), len(ix), float(np.mean(VH[ix])) if len(ix) else np.nan, zst,
                len(ee), len(ee) / max(len(am), 1), ers, "✔" if ok6 else "⛔"))
        print("  K5-3 SPERRE (unten):")
        for s in SPERR:
            ix = g[VH[g] <= s]
            print("    %+.2f    %7.1f%% %8d %+10.4f %+10.4f" % (
                s, 100 * len(ix) / len(g), len(ix), float(np.mean(VH[ix])) if len(ix) else np.nan, dqs(ix)))
        # ── Nullwelt: die rollierenden Modelle auf rsi, je Asset verschoben (ohne Neuschaetzung) ──
        def vh_welt(EE):
            v = np.full(n, np.nan)
            for mi, m in modelle:
                ixm = g[MON[g] == mi]
                if len(ixm):
                    c = m.z(EE, ixm, OFF[ixm]) - OFF[ixm]
                    v[ixm] = _ex(np.log(QS[ixm] / (1 - QS[ixm])) + c) - QS[ixm]
            return v
        BINS = ((0.02, 0.04), (0.04, 0.06), (0.06, 0.08), (0.08, np.inf))

        def kennz(v, y=A24):
            sig = [dqs(g[v[g] >= s], y) for s in SCHW]
            spe = [dqs(g[v[g] <= s], y) for s in SPERR]
            b_ = [dqs(g[(v[g] >= lo_) & (v[g] < hi_)], y) for lo_, hi_ in BINS]
            return sig, spe, [b_[i + 1] - b_[i] for i in range(3)], b_
        echt = kennz(VH)
        nsig, nspe, ndif = [], [], []
        for _ in range(zieh):
            EV = verschoben(E, RSI)
            k_ = kennz(vh_welt(EV)); nsig.append(k_[0]); nspe.append(k_[1]); ndif.append(k_[2])
        nsig, nspe, ndif = np.array(nsig), np.array(nspe), np.array(ndif)
        print()
        print("  NULLWELT (rollierende Modelle auf verschobenem rsi, %d Ziehungen):" % zieh)
        for i, s in enumerate(SCHW):
            print("    Signal %+.2f: beob %+.4f · Null Mittel %+.4f, P90 %+.4f" % (
                s, echt[0][i], float(np.nanmean(nsig[:, i])), float(np.nanpercentile(nsig[:, i], 90))))
        for i, s in enumerate(SPERR):
            lo10 = float(np.nanpercentile(nspe[:, i], 10))
            print("    Sperre %+.2f: beob %+.4f · Null Mittel %+.4f, P10 %+.4f -> %s" % (
                s, echt[1][i], float(np.nanmean(nspe[:, i])), lo10, "UMKEHR ✔" if echt[1][i] < lo10 and echt[1][i] < 0 else "keine Umkehr"))
        print("  K5-4 STUFEN (Bereiche %s): beob %s" % (
            " · ".join("%+.2f..%s" % (lo_, "" if hi_ == np.inf else "%+.2f" % hi_) for lo_, hi_ in BINS),
            " · ".join("%+.4f" % x for x in echt[3])))
        for i in range(3):
            print("    Unterschied Stufe %d->%d: %+.4f · Null P90 %+.4f -> %s" % (
                i + 1, i + 2, echt[2][i], float(np.nanpercentile(ndif[:, i], 90)),
                "trennscharf" if echt[2][i] >= 0.04 and echt[2][i] > np.nanpercentile(ndif[:, i], 90) else "nicht trennscharf"))
        # Leiter fuer die oberste Stufe (Unterschied Stufe 3 -> 4)
        p90d = float(np.nanpercentile(ndif[:, 2], 90))
        for d in (0.04, 0.08):
            gef, werte = 0, []
            for _ in range(5):
                EV = verschoben(E, RSI); vv = vh_welt(EV)
                top = g[(vv[g] >= 0.08) & HIT[g]]; kand = top[B24[top] == 1]
                y = A24.copy()
                w_ = rng.choice(kand, size=min(int(round(d * len(top))), len(kand)), replace=False)
                y[w_] = 1.0
                dd = kennz(vv, y)[2][2]
                werte.append(dd); gef += int(dd > p90d)
            print("    Leiter oberste Stufe +%.2f: %s -> gefunden %d von 5" % (d, " ".join("%+.4f" % x for x in werte), gef))
        # ══ GEGENPRUEFUNG K5-6 und K5-1 (--gegen6; Voranalyse Abschnitt 11, VOR dem Lauf festgehalten) ══
        if "--gegen6" in sys.argv:
            MON_START = np.array([H(datetime(2020 + mm // 12, mm % 12 + 1, 1)) for mm in range(0, 12 * 8)])

            def erst_v(VHx, s, streng, ohne_wechsel):
                aus = []
                for tl in teile:
                    st = STD[tl]; vv = VHx[tl]
                    fin = np.isfinite(vv)
                    ab_ = np.where(fin, vv >= s, False)
                    cs = np.concatenate([[0], np.cumsum(ab_)]); cf = np.concatenate([[0], np.cumsum(fin)])
                    lo = np.searchsorted(st, st - 24, "left")
                    idx = np.arange(len(tl))
                    if streng:
                        erst = ab_ & ((cs[idx] - cs[lo]) == 0) & ((cf[idx] - cf[lo]) >= 20)
                    else:
                        erst = ab_ & ((cs[idx] - cs[lo]) == 0) & ((idx - lo) >= 20)
                    if ohne_wechsel:
                        ms = MON_START[np.clip(MON[tl] - 2020 * 12, 0, len(MON_START) - 1)]
                        erst &= (st - ms) >= 24
                    i_ = np.flatnonzero(erst)
                    i_ = i_[i_ + 1 < len(tl)]
                    i_ = i_[st[i_ + 1] == st[i_] + 1]
                    aus.append(tl[i_ + 1])
                e_ = np.concatenate(aus) if aus else np.zeros(0, int)
                return e_[np.isin(JAHR[e_], JAHRE) & np.isfinite(QSh[e_])]
            print()
            print("  GEGENPRUEFUNG K5-6 (Ersteintritt): wie registriert / Fenster nur aus gueltigen Stunden / dazu ohne die ersten 24 h eines Monats (Modellwechsel)")
            for s in (0.02, 0.04):
                e1, e2, e3 = erst_v(VH, s, False, False), erst_v(VH, s, True, False), erst_v(VH, s, True, True)
                am1 = np.isin(e1 - 1, e1 - 1)
                w1 = e1[(STD[e1] - MON_START[np.clip(MON[e1] - 2020 * 12, 0, len(MON_START) - 1)]) < 25]
                print("    %+.2f: %d -> %+.4f · %d -> %+.4f · %d -> %+.4f · davon im Monatsanfang %d (%+.4f)" % (
                    s, len(e1), dqh(e1), len(e2), dqh(e2), len(e3), dqh(e3), len(w1), dqh(w1) if len(w1) else np.nan))
            # Nullwelt fuer den Ersteintritt: die rollierenden Modelle auf verschobenem rsi, STUENDLICH
            h24 = np.flatnonzero(np.isfinite(QSh) & np.isin(JAHR, JAHRE) & np.isfinite(OFF))

            def vh_stuendlich(EE):
                v = np.full(n, np.nan)
                for mi, m in modelle:
                    ixm = h24[MON[h24] == mi]
                    if len(ixm):
                        c = m.z(EE, ixm, OFF[ixm]) - OFF[ixm]
                        v[ixm] = _ex(np.log(QSh[ixm] / (1 - QSh[ixm])) + c) - QSh[ixm]
                return v
            for s in (0.02, 0.04):
                echt3 = dqh(erst_v(VH, s, True, True))
                nv = []
                for _ in range(zieh):
                    EV = verschoben(E, RSI)
                    nv.append(dqh(erst_v(vh_stuendlich(EV), s, True, True)))
                print("    Nullwelt %+.2f (streng, ohne Monatsanfang, %d Ziehungen): echt %+.4f · Null Mittel %+.4f, P90 %+.4f -> %s" % (
                    s, zieh, echt3, float(np.nanmean(nv)), float(np.nanpercentile(nv, 90)),
                    "✔ jenseits" if echt3 > np.nanpercentile(nv, 90) else "· nicht jenseits"))
            # K5-1 Gegenpruefung: Zehntel von vh gegen den MOMENT-Bezug (Asset im selben Monat) - nimmt den Monatskontext heraus
            print()
            print("  GEGENPRUEFUNG K5-1: Zehntel von vh, beobachtet gegen das geschrumpfte Normal | gegen den Moment-Bezug (Asset im Monat)")
            print("    " + " · ".join("%+.3f|%+.3f" % (dqs(g[zg == d_]), dq(g[zg == d_], A24, MA, MB)) for d_ in range(10)))
            kc = np.quantile(Ch[g], np.linspace(0, 1, 11)[1:-1]); zc = np.searchsorted(kc, Ch[g], "right")
            print("    Zehntel des BEITRAGS c (statt vh): " + " · ".join("%+.3f|%+.3f" % (dqs(g[zc == d_]), dq(g[zc == d_], A24, MA, MB)) for d_ in range(10)))
            mz = np.unique(MON[g])
            print("    je Monat Anteil |vh| >= 0,04: " + " · ".join("%d-%02d %.1f%%" % (mm // 12, mm % 12 + 1, 100 * np.mean(np.abs(VH[g[MON[g] == mm]]) >= 0.04)) for mm in mz))
        if best:
            print()
            zst, ers = dqs(g[VH[g] >= s_best]), dqh(ersteintritte(s_best))
            jz = [(jj, dqs(g[(VH[g] >= s_best) & (JAHR[g] == jj)])) for jj in JAHRE]
            print("  K5-5 BESTAETIGUNG Schwelle %+.2f: %s · Kalibrierung Steigung %.2f -> %s" % (
                s_best, " · ".join("%d %+.4f" % x for x in jz), steig,
                "✔" if all(x[1] > 0 for x in jz) and 0.7 <= steig <= 1.3 else "⛔ nicht bestaetigt"))
            print("  K5-6 BESTAETIGUNG Ersteintritt %+.4f gegen Zustand %+.4f -> %s" % (
                ers, zst, "✔" if ers > 0 and ers >= 0.5 * zst else "⛔"))
            if sp_best is not None:
                print("  Sperre %+.2f: beob %+.4f" % (sp_best, dqs(g[VH[g] <= sp_best])))
        print("SCHLUSS: vollstaendig")
        return 0

    # ══ W1 (Voranalyse_Beitrag_Kontext_Gewicht_29_09.md, Abschnitte 6 und 10) ══════════
    # Zerlegung je Wetter-Drittel W und Jahr: NIVEAU(W) = Dq aller Anker, ZUWACHS(W) = Dq
    # der Einstiegsauswahl minus Niveau - beides gegen das geschrumpfte Normal.
    # Wetter = BTC-Rendite 30 Tage, Drittel nach dem RANG gegen die eigenen letzten 12
    # Monate (kausal). WEITER nur, wenn Zuwachs(hoch) - Zuwachs(tief) >= +0,04 in 2025 UND 2026.
    if "--wetter" in sys.argv or "--wetter2" in sys.argv:
        WEITER = 0.04
        m0, sel0 = rsi_auswahl(E)
        ct0 = m0.z(E, r_pa, OFF[r_pa]) - OFF[r_pa]
        rr11 = dq(r_pa[ct0 >= np.quantile(m0.z(E, r_sa, OFF[r_sa]) - OFF[r_sa], 0.9)])
        print()
        print("=" * 120)
        print("W1 · WETTER: KONTEXT ODER GEWICHT? (Einstiegsregel rsi allein, feste Teilung, geschrumpftes Normal)")
        print("  R-R11 rsi allein oben (rohes Normal) %+.4f · 2.680: +0,0808 -> %s" % (
            rr11, "✔ bitgleich" if abs(round(rr11, 4) - 0.0808) < 1e-9 or E2.MENGE != "bestand" else "⛔ ABWEICHUNG"))
        btc = reihe([(E2.EINGESTELLT_DB, "SELECT stunde, close FROM stundenkurse WHERE symbol='BTC'"),
                     (E2.STUNDEN_DB, "SELECT stunde, close FROM stundenkurse WHERE symbol='BTC'")])
        LH = len(btc)
        b30h = np.full(LH, np.nan)
        with np.errstate(divide="ignore", invalid="ignore"):
            b30h[720:] = btc[720:] / btc[:-720] - 1.0
        rang = pd.Series(b30h).rolling(8760, min_periods=4000).rank(pct=True).to_numpy()
        zust_h = np.full(LH, -1, np.int8)
        fin = np.isfinite(rang)
        zust_h[fin] = np.where(rang[fin] <= 1 / 3, 0, np.where(rang[fin] <= 2 / 3, 1, 2))
        abs_h = np.full(LH, -1, np.int8)
        fa = np.isfinite(b30h)
        abs_h[fa] = (b30h[fa] >= 0).astype(np.int8)
        ok_std = STD < LH
        WN = ("BTC tief", "BTC mitte", "BTC hoch")
        feste = r_pa[np.isfinite(E["rsi_s"][r_pa]) & (E["rsi_s"][r_pa] >= np.nanpercentile(E["rsi_s"][r_sa], 90))]

        def zustand(zh, versatz=0):
            z = np.full(n, -1, np.int8)
            z[ok_std] = zh[(STD[ok_std] + versatz) % LH]
            return z

        def zerlege(Z, sel, ix_jahr, y=A24):
            aus = []
            for w in range(3):
                alle = ix_jahr[Z[ix_jahr] == w]
                s_ = np.intersect1d(sel, alle)
                niv = dqs(alle, y)
                aus.append((niv, dqs(s_, y) - niv, len(alle), len(s_)))
            return aus

        def episoden(zh, jj):
            hs = np.arange(LH)
            tag = hs[(hs % 24 == 0)]
            tag = tag[(monat_von(tag) // 12) == jj]
            s = zh[tag]
            s = s[s >= 0]
            if not len(s):
                return (0, 0, 0)
            start = np.r_[True, s[1:] != s[:-1]]
            return tuple(int(((s == w) & start).sum()) for w in range(3))
        Z = zustand(zust_h)
        jahre = (2025, 2026)
        erg = {}
        for jj in jahre:
            ixj = r_pa[JAHR[r_pa] == jj]
            erg[jj] = zerlege(Z, sel0, ixj)
            ep = episoden(zust_h, jj)
            print()
            print("  %d · Niveau (alle Anker) · Zuwachs der Einstiegsauswahl · Anker alle/Auswahl · Episoden (Tage-Laeufe)" % jj)
            for w in range(3):
                niv, zuw, na_, ns_ = erg[jj][w]
                print("    %-9s Niveau %+.4f · Zuwachs %+.4f · %6d / %5d · Episoden %d" % (WN[w], niv, zuw, na_, ns_, ep[w]))
            fz = zerlege(Z, feste, ixj)
            print("    Auskunft feste Regel (rsi_s >= P90 Suche): Zuwachs tief %+.4f · mitte %+.4f · hoch %+.4f" % (
                fz[0][1], fz[1][1], fz[2][1]))
        # Nullwelt: die Wetterreihe fuer ALLE Assets gemeinsam verschoben (>= 60 Tage)
        null_z = {jj: [] for jj in jahre}; null_n = {jj: [] for jj in jahre}
        for _ in range(zieh):
            k_ = int(rng.integers(1440, LH - 1440))
            Zv = zustand(zust_h, k_)
            for jj in jahre:
                e_ = zerlege(Zv, sel0, r_pa[JAHR[r_pa] == jj])
                null_z[jj].append(e_[2][1] - e_[0][1]); null_n[jj].append(e_[2][0] - e_[0][0])
        print()
        weiter = True
        for jj in jahre:
            dz = erg[jj][2][1] - erg[jj][0][1]; dn = erg[jj][2][0] - erg[jj][0][0]
            weiter &= dz >= WEITER
            print("  %d · GEWICHT: Zuwachs hoch - tief %+.4f (Nullwelt Mittel %+.4f, 90. Perzentil %+.4f) · "
                  "KONTEXT: Niveau hoch - tief %+.4f (Nullwelt Mittel %+.4f, 90. Perzentil %+.4f)" % (
                      jj, dz, float(np.nanmean(null_z[jj])), float(np.nanpercentile(null_z[jj], 90)),
                      dn, float(np.nanmean(null_n[jj])), float(np.nanpercentile(null_n[jj], 90))))
        # Auskunft absolut: BTC 30 Tage < 0 gegen >= 0
        Za = zustand(abs_h)
        for jj in jahre:
            ixj = r_pa[JAHR[r_pa] == jj]
            t_ = []
            for w, nm in ((0, "BTC 30 T < 0"), (1, "BTC 30 T >= 0")):
                alle = ixj[Za[ixj] == w]; s_ = np.intersect1d(sel0, alle); niv = dqs(alle)
                t_.append("%s: Niveau %+.4f, Zuwachs %+.4f (%d)" % (nm, niv, dqs(s_) - niv, len(s_)))
            print("  Auskunft absolut %d: %s" % (jj, " · ".join(t_)))
        # Auskunft 2022 (Moment-Bezug: das Niveau ist je Asset und Monat herausgenommen, nur der Zuwachs zaehlt)
        r22 = np.flatnonzero(GRID & (JAHR == 2022) & np.isfinite(OFF_M))
        if len(r22):
            c22 = m0.z(E, r22, OFF_M[r22]) - OFF_M[r22]
            s22 = r22[c22 >= np.quantile(m0.z(E, r_sa, OFF[r_sa]) - OFF[r_sa], 0.9)]
            t_ = []
            for w in range(3):
                alle = r22[Z[r22] == w]; s_ = np.intersect1d(s22, alle)
                t_.append("%s %+.4f (%d)" % (WN[w], dq(s_, A24, MA, MB) - dq(alle, A24, MA, MB), len(s_)))
            print("  Auskunft 2022 (Moment-Bezug) Zuwachs: %s" % " · ".join(t_))
        print()
        print("  WEITER-SCHWELLE Zuwachs hoch - tief >= +%.2f in 2025 UND 2026: %s" % (
            WEITER, "✔ ERREICHT - W2 vorlegen" if weiter else "⛔ NICHT erreicht - keine W2 aus diesem Grund, Ergebnis vorlegen"))
        if "--wetter2" in sys.argv:
            # ══ W2 (Voranalyse_W2_Wetter_Gewicht_29_09.md): Urteil 2024-01..2026-08, rollierende
            # Einstiegsregel (jeder Monat fuer rsi ungesehen), Wetter unveraendert aus W1 ══════
            print()
            print("=" * 120)
            print("W2 · ROLLIEREND 2024-01 bis 2026-08, Training wachsend ab 2023-01, Grenze aus dem Training")
            SEL = np.zeros(n, bool)
            ab = H(datetime(2023, 1, 1))
            for (j, mo) in monate:
                mi = j * 12 + (mo - 1)
                start = H(datetime(j, mo, 1))
                fen = BASIS & (STD >= ab) & (MON < mi) & (STD < start - 24)
                ra = np.flatnonzero(fen); rt = np.flatnonzero(fen & HIT)
                ziel = np.flatnonzero(BASIS & (MON == mi))
                if len(rt) < 5000 or not len(ziel):
                    continue
                _m, sv = rsi_auswahl(E, ra=ra, rt=rt, ziel=ziel)
                SEL[sv] = True
            sel = np.flatnonzero(SEL)
            urteil = np.flatnonzero(BASIS & (MON >= 2024 * 12) & (MON <= 2026 * 12 + 7) & np.isfinite(QS))
            sel = np.intersect1d(sel, urteil)
            print("  Urteilsanker %d · Auswahl %d (%.1f %%)" % (len(urteil), len(sel), 100 * len(sel) / max(len(urteil), 1)))

            def G_von(Zx, y=A24, ix=urteil):
                e_ = zerlege(Zx, sel, ix, y)
                return e_[2][1] - e_[0][1], e_[2][0] - e_[0][0], e_
            g, gn, e_all = G_von(Z)
            for w in range(3):
                print("    %-9s Niveau %+.4f · Zuwachs %+.4f · %6d / %5d" % (WN[w], e_all[w][0], e_all[w][1], e_all[w][2], e_all[w][3]))
            null40, nulln40, null400 = [], [], []
            for i_ in range(440):
                k_ = int(rng.integers(1440, LH - 1440))
                gv, gnv, _e = G_von(zustand(zust_h, k_))
                (null40 if i_ < zieh else null400).append(gv)
                if i_ < zieh:
                    nulln40.append(gnv)
            p90 = float(np.nanpercentile(null40, 90))
            p90_400 = float(np.nanpercentile(null40 + null400, 90))
            anteil = float(np.mean(np.array(null40 + null400) >= g))
            print("  G = Zuwachs hoch - tief %+.4f · Nullwelt (40) Mittel %+.4f, P90 %+.4f · (440) P90 %+.4f, Anteil >= G %.3f" % (
                g, float(np.nanmean(null40)), p90, p90_400, anteil))
            print("  Kontext: Niveau hoch - tief %+.4f · Nullwelt (40) Mittel %+.4f, P90 %+.4f" % (
                gn, float(np.nanmean(nulln40)), float(np.nanpercentile(nulln40, 90))))
            # Leiter (vorab): in der VERSCHOBENEN Welt +d auf die Auswahl im Zustand hoch
            aufl = None
            for d in (0.04, 0.08, 0.12):
                gef, werte = 0, []
                for _ in range(5):
                    k_ = int(rng.integers(1440, LH - 1440))
                    Zv = zustand(zust_h, k_)
                    ziel_h = sel[(Zv[sel] == 2) & HIT[sel]]
                    kand = ziel_h[B24[ziel_h] == 1]
                    y = A24.copy()
                    w_ = rng.choice(kand, size=min(int(round(d * len(ziel_h))), len(kand)), replace=False)
                    y[w_] = 1.0
                    gv, _gn, _e = G_von(Zv, y)
                    werte.append(gv); gef += int(gv > p90)
                print("  Leiter +%.2f: %s -> gefunden %d von 5" % (d, " ".join("%+.4f" % x for x in werte), gef))
                if aufl is None and gef >= 4:
                    aufl = d
            print("  G1 Aufloesung: %s" % ("+%.2f" % aufl if aufl else "keine Stufe bis +0,12 -> NICHT AUFLOESBAR"))
            # G3 je Jahr, Episoden
            g3 = []
            for jj in (2024, 2025, 2026):
                ixj = urteil[JAHR[urteil] == jj]
                e_ = zerlege(Z, sel, ixj)
                ep = episoden(zust_h, jj)
                g3.append(e_[2][1] > e_[0][1])
                print("  %d: Zuwachs tief %+.4f · mitte %+.4f · hoch %+.4f · Niveau tief %+.4f / hoch %+.4f · Episoden %s" % (
                    jj, e_[0][1], e_[1][1], e_[2][1], e_[0][0], e_[2][0], "/".join(map(str, ep))))
            # G4 je Asset
            ga = []
            for si in np.unique(SYM[sel]):
                ixa = urteil[SYM[urteil] == si]
                e_ = zerlege(Z, sel, ixa)
                if e_[0][3] >= 30 and e_[2][3] >= 30:
                    ga.append(e_[2][1] > e_[0][1])
            g4 = float(np.mean(ga)) if ga else np.nan
            # G6 Auskunft: Log-Loss Wechselwirkung gegen Addition, Zeitbloecke
            from scipy.special import expit as _ex

            def fit_logit(X, yy, off):
                b = np.zeros(X.shape[1])
                for _ in range(30):
                    z = off + X @ b; pp = _ex(z); W = pp * (1 - pp)
                    Hm = X.T @ (X * W[:, None]) + 1e-6 * np.eye(X.shape[1])
                    b = b + np.linalg.solve(Hm, X.T @ (yy - pp))
                return b

            def ll_gewinn(Zx):
                ix = urteil[HIT[urteil] & (Zx[urteil] >= 0)]
                yy = A24[ix]; off = logit_q(QS[ix], 1 - QS[ix])
                s_ = np.isin(ix, sel).astype(float)
                wt = (Zx[ix] == 0).astype(float); wh = (Zx[ix] == 2).astype(float)
                Xa = np.column_stack([np.ones(len(ix)), s_, wt, wh])
                Xi = np.column_stack([Xa, s_ * wt, s_ * wh])
                kanten = np.quantile(STD[ix], (0.25, 0.5, 0.75)); blk = np.searchsorted(kanten, STD[ix], "right")
                la = li = 0.0
                for b_ in range(4):
                    te, tr = blk == b_, blk != b_
                    ba = fit_logit(Xa[tr], yy[tr], off[tr]); bi = fit_logit(Xi[tr], yy[tr], off[tr])
                    za = off[te] + Xa[te] @ ba; zi = off[te] + Xi[te] @ bi
                    la += float(np.sum(np.logaddexp(0, za) - yy[te] * za)); li += float(np.sum(np.logaddexp(0, zi) - yy[te] * zi))
                return 1000.0 * (la - li) / len(ix)
            g6 = ll_gewinn(Z)
            n6 = [ll_gewinn(zustand(zust_h, int(rng.integers(1440, LH - 1440)))) for _ in range(zieh)]
            print("  G6 (Auskunft) Log-Loss-Gewinn Wechselwirkung ueber Addition %+.4f milli-nat je Anker · Nullwelt Mittel %+.4f, P90 %+.4f" % (
                g6, float(np.mean(n6)), float(np.percentile(n6, 90))))
            print()
            print("  G1 Aufloesung <= +0,12: %s" % ("✔" if aufl else "⛔"))
            print("  G2 G ueber P90 (40) UND ueber der Aufloesung: %s" % (
                "✔" if aufl and g > p90 and g > aufl else "⛔ nicht nachweisbar"))
            print("  G3 hoch > tief in jedem Jahr 2024/2025/2026: %s" % ("✔" if all(g3) else "⛔ %s" % g3))
            print("  G4 je Asset (>= 30 Auswahlanker in hoch und tief): %d Assets, hoch > tief bei %.0f %% -> %s" % (
                len(ga), 100 * g4, "✔" if g4 >= 0.6 else "⛔"))
            print("  G5 Kontext kleiner als Gewicht: Niveau-Differenz %+.4f gegen G %+.4f -> %s" % (gn, g, "✔" if gn < g else "⛔"))
        print("SCHLUSS: vollstaendig")
        return 0

    if tor:
        null = []
        for _ in range(zieh):
            EV = verschoben(E, RSI)
            _m, sv = rsi_auswahl(EV)
            null.append(frueh_spaet(sv)[0])
        grenze = float(np.nanpercentile(null, 90))
        print()
        print("TOR TEIL 1 (L1) frueh - spaet mit verschobenem rsi: Nullwelt Mittel %+.4f, Streuung %.4f, 90. Perzentil %+.4f" % (
            float(np.nanmean(null)), float(np.nanstd(null, ddof=1)), grenze))
        erg = {}
        for d in D1:
            gef, werte, ueb, deck = 0, [], [], []
            for _ in range(5):
                EV = verschoben(E, RSI)
                gr = np.nanpercentile(EV["rsi_s"][r_sa], 90)
                y = A24.copy()
                oben = np.flatnonzero((EV["rsi_s"] >= gr) & HIT & (such | pruef) & (NADEL <= FRUEH))
                kand = oben[B24[oben] == 1]
                w = rng.choice(kand, size=min(int(round(d * len(oben))), len(kand)), replace=False)
                y[w] = 1.0
                _m, sv = rsi_auswahl(EV, y)
                dd, fz, _sz = frueh_spaet(sv, y)
                werte.append(dd); gef += int(dd > grenze)
                # Uebertragung: wie viel der Pflanzung kommt in der fruehen Auswahl an (gleiche Auswahl, y ohne Pflanzung)
                ueb.append(dqs(fz, y) - dqs(fz, A24))
                op = np.intersect1d(oben, r_pa)
                deck.append(len(np.intersect1d(op, sv)) / max(len(op), 1))
            erg[d] = gef
            print("  gepflanzt +%.2f in der fruehen Klasse (P90+ rsi, verschoben): %s -> gefunden %d von 5" % (
                d, " ".join("%+.4f" % x for x in werte), gef))
            print("      angekommen in der fruehen Auswahl %s · Deckung Auswahl/Pflanzbereich %s" % (
                " ".join("%+.4f" % x for x in ueb), " ".join("%.2f" % x for x in deck)))
        if leiter:
            auf = [d for d in D1 if erg[d] >= 4]
            print("  AUFLOESUNG TEIL 1: %s" % ("+%.2f (kleinste Stufe mit >= 4 von 5)" % auf[0] if auf else "keine Stufe bis +0,20"))
        else:
            print("  TOR TEIL 1: %s" % ("✔ BESTANDEN" if erg[0.04] >= 4 else "⛔ NICHT BESTANDEN - kein Urteil zu L2"))
        # Teil 2
        st_sa = r_sa[np.abs(NADEL[r_sa]) < STEHEND]; st_s = r_s[np.abs(NADEL[r_s]) < STEHEND]
        st_pa = r_pa[np.abs(NADEL[r_pa]) < STEHEND]

        def bestes_lage(EE, y=A24):
            best = -np.inf
            for f_, ks in LAGE.items():
                m, _l = K2.fit_cv(ks, EE, st_sa, st_s, y[st_s], OFF[st_s], STD)
                cz = m.z(EE, st_pa, OFF[st_pa]) - OFF[st_pa]
                best = max(best, dqs(st_pa[cz >= np.quantile(cz, 0.9)], y) - dqs(st_pa, y))
            return best
        null2 = [bestes_lage(verschoben(E, LAGE_SP)) for _ in range(zieh)]
        g2 = float(np.nanpercentile(null2, 90))
        print("TOR TEIL 2 Bestes-von-3 Lage auf stehenden Ankern (Lage verschoben): Nullwelt Mittel %+.4f, 90. Perzentil %+.4f" % (
            float(np.nanmean(null2)), g2))
        erg2 = {}
        for d in D2:
          gef, werte, deck = 0, [], []
          for _ in range(5):
            EV = verschoben(E, LAGE_SP)
            gr = np.nanpercentile(EV["oi_24"][st_sa], 90)
            y = A24.copy()
            steh = np.abs(NADEL) < STEHEND
            oben = np.flatnonzero((EV["oi_24"] >= gr) & HIT & (such | pruef) & steh)
            kand = oben[B24[oben] == 1]
            w = rng.choice(kand, size=min(int(round(d * len(oben))), len(kand)), replace=False)
            y[w] = 1.0
            dd = bestes_lage(EV, y)
            werte.append(dd); gef += int(dd > g2)
            m, _l = K2.fit_cv(LAGE["oi"], EV, st_sa, st_s, y[st_s], OFF[st_s], STD)
            cz = m.z(EV, st_pa, OFF[st_pa]) - OFF[st_pa]
            op = np.intersect1d(oben, st_pa)
            deck.append(len(np.intersect1d(op, st_pa[cz >= np.quantile(cz, 0.9)])) / max(len(op), 1))
          erg2[d] = gef
          print("  gepflanzt +%.2f auf P90+ von oi_24 (stehend, verschoben): %s -> gefunden %d von 5 · Deckung oi-Auswahl/Pflanzbereich %s" % (
              d, " ".join("%+.4f" % x for x in werte), gef, " ".join("%.2f" % x for x in deck)))
        if leiter:
            auf = [d for d in D2 if erg2[d] >= 4]
            print("  AUFLOESUNG TEIL 2: %s" % ("+%.2f (kleinste Stufe mit >= 4 von 5)" % auf[0] if auf else "keine Stufe bis +0,20"))
        else:
            print("  TOR TEIL 2: %s" % ("✔ BESTANDEN" if erg2[0.04] >= 4 else "⛔ NICHT BESTANDEN - kein Urteil zu L5"))
        print("SCHLUSS: vollstaendig")
        return 0

    m0, sel0 = rsi_auswahl(E)
    ct0 = m0.z(E, r_pa, OFF[r_pa]) - OFF[r_pa]
    rr11 = dq(r_pa[ct0 >= np.quantile(m0.z(E, r_sa, OFF[r_sa]) - OFF[r_sa], 0.9)])
    soll = RR11_2680.get(E2.MENGE)
    print()
    print("R-R11 rsi allein oben (rohes Normal) %+.4f · 2.680: %s -> %s" % (
        rr11, "%+.4f" % soll if soll is not None else "-",
        ("✔ bitgleich" if soll is not None and abs(round(rr11, 4) - soll) < 1e-9 else "⛔ ABWEICHUNG") if soll is not None else ""))
    d_f, f0, s0 = frueh_spaet(sel0)
    null = []
    for _ in range(zieh):
        EV = verschoben(E, RSI)
        _m, sv = rsi_auswahl(EV)
        null.append(frueh_spaet(sv)[0])
    g1 = float(np.nanpercentile(null, 90))
    print()
    print("=" * 120)
    print("TEIL 1 · FESTE TEILUNG - die ANFAHR-KURVE der rsi-Auswahl (Dq gegen das geschrumpfte Normal)")
    for k in range(6):
        s_ = sel0[KL[sel0] == k]
        print("  %-7s Auswahl %6d (%4.1f %%) · Dq %+.4f%s · alle Anker der Klasse %+.4f" % (
            KLNAME[k], len(s_), 100 * len(s_) / max(len(sel0), 1), dqs(s_),
            "" if len(s_) >= MIN_KLASSE else " (zu wenige)", dqs(r_pa[KL[r_pa] == k])))
    print("  L2 fest: frueh (<= 0,5 ATR) %+.4f (%d) minus spaet (> 1 ATR, Abschnitt 9) %+.4f (%d) = %+.4f gegen Nullband Mittel %+.4f, 90. Perzentil %+.4f -> %s" % (
        dqs(f0), len(f0), dqs(s0), len(s0), d_f, float(np.nanmean(null)), g1, "✔ frueh besser" if d_f > g1 else "· nicht jenseits"))
    print("  Auskunft 72 h (rohes 72-h-Normal): frueh %+.4f · spaet %+.4f" % (
        dq(f0, A72, NA72, NB72, HIT72), dq(s0, A72, NA72, NB72, HIT72)))
    kl120 = np.searchsorted(np.array(KLASSEN[1:-1]), NADEL120, side="right")
    print("  Auskunft 120-h-Nadel: %s" % " · ".join(
        "%s %+.4f (%d)" % (KLNAME[k], dqs(sel0[kl120[sel0] == k]), int((kl120[sel0] == k).sum())) for k in range(6)))
    r22 = np.flatnonzero(GRID & (JAHR == 2022) & np.isfinite(OFF_M))
    d22 = np.nan
    if len(r22):
        c22 = m0.z(E, r22, OFF_M[r22]) - OFF_M[r22]
        s22 = r22[c22 >= np.quantile(m0.z(E, r_sa, OFF[r_sa]) - OFF[r_sa], 0.9)]
        f22 = s22[NADEL[s22] <= FRUEH]; sp22 = s22[NADEL[s22] > SPAET]
        d22 = dq(f22, A24, MA, MB)
        print("  2022 (Moment-Bezug): frueh %+.4f (%d) · spaet %+.4f (%d)" % (d22, len(f22), dq(sp22, A24, MA, MB), len(sp22)))

    # ══ TEIL 1 · rollierend ═════════════════════════════════════════════
    print()
    print("=" * 120)
    print("TEIL 1 · ROLLIEREND, WACHSEND: %d Monate, Grenze aus dem Training" % len(monate))
    SEL = np.zeros(n, bool)
    ab = H(datetime(2023, 1, 1))
    for (j, mo) in monate:
        mi = j * 12 + (mo - 1)
        start = H(datetime(j, mo, 1))
        fen = BASIS & (STD >= ab) & (MON < mi) & (STD < start - 24)
        ra = np.flatnonzero(fen); rt = np.flatnonzero(fen & HIT)
        ziel = np.flatnonzero(BASIS & (MON == mi))
        if len(rt) < 5000 or not len(ziel):
            continue
        _m, sv = rsi_auswahl(E, ra=ra, rt=rt, ziel=ziel)
        SEL[sv] = True
    sel = np.flatnonzero(SEL)
    for k in range(6):
        s_ = sel[KL[sel] == k]
        print("  %-7s Auswahl %6d (%4.1f %%) · Dq %+.4f%s" % (KLNAME[k], len(s_), 100 * len(s_) / max(len(sel), 1), dqs(s_),
                                                           "" if len(s_) >= MIN_KLASSE else " (zu wenige)"))
    d_r, fr, sr = frueh_spaet(sel)
    print("  L2 rollierend: frueh %+.4f minus spaet %+.4f = %+.4f gegen das feste Nullband %+.4f -> %s" % (
        dqs(fr), dqs(sr), d_r, g1, "✔" if d_r > g1 else "·"))
    jj_ = [(jj, dqs(fr[JAHR[fr] == jj]), int((JAHR[fr] == jj).sum())) for jj in (2024, 2025, 2026)]
    print("  L3 frueh je Jahr: %s · 2022 %+.4f -> %s" % (
        " · ".join("%d %+.4f (%d)" % x for x in jj_), d22,
        "✔ jedes > 0" if all(x[1] > 0 for x in jj_) and d22 > 0 else "⛔ nicht jedes"))
    ga = np.array([dqs(fr[SYM[fr] == si]) for si in np.unique(SYM[fr]) if (SYM[fr] == si).sum() >= 30])
    print("  L4 je Asset (frueh, >= 30 Auswahlanker): %d Assets, Dq > 0 bei %.0f %% -> %s" % (
        len(ga), 100 * np.mean(ga > 0) if len(ga) else np.nan, "✔" if len(ga) and np.mean(ga > 0) >= 0.6 else "·"))
    print("  L7 Signale: frueh %.1f %% · spaet %.1f %% der Auswahl" % (100 * len(fr) / max(len(sel), 1), 100 * len(sr) / max(len(sel), 1)))

    # ══ TEIL 2 · Lage auf stehenden Ankern ══════════════════════════════
    print()
    print("=" * 120)
    print("TEIL 2 · LAGE AUF STEHENDEN ANKERN (|Anstieg 24 h| < %.1f ATR), eigenes Zehntel, gegen das geschrumpfte Normal" % STEHEND)
    steh = np.abs(NADEL) < STEHEND
    st_sa, st_s, st_pa = r_sa[steh[r_sa]], r_s[steh[r_s]], r_pa[steh[r_pa]]
    basis_st = dqs(st_pa)
    print("  stehende Pruefanker %d (%.0f %%) · ihr Dq gegen das geschrumpfte Normal %+.4f" % (
        len(st_pa), 100 * len(st_pa) / max(len(r_pa), 1), basis_st))
    # Markt und Eigen
    EM = dict(E)
    stunden = np.unique(STD)
    for kurz, v in ROH.items():
        med = pd.Series(v).groupby(STD).median()
        mk = med.reindex(STD).to_numpy()
        for suf, w in (("_m", mk), ("_e", v - mk)):
            EM[kurz + suf + "_0"] = w; EM[kurz + suf + "_24"] = alt(w, 24); EM[kurz + suf + "_48"] = alt(w, 48)
    LAGE_ME = {}
    for f_, kurz in (("funding", "fu"), ("oi", "oi"), ("konten", "ko")):
        LAGE_ME[f_ + "_markt"] = tuple(kurz + "_m_" + s for s in ("0", "24", "48"))
        LAGE_ME[f_ + "_eigen"] = tuple(kurz + "_e_" + s for s in ("0", "24", "48"))

    def lage_dq(EE, fam, ra=st_sa, rt=st_s, ziel=st_pa):
        m, _l = K2.fit_cv(fam, EE, ra, rt, A24[rt], OFF[rt], STD)
        cz = m.z(EE, ziel, OFF[ziel]) - OFF[ziel]
        return dqs(ziel[cz >= np.quantile(cz, 0.9)]) - dqs(ziel)

    werte = {f_: lage_dq(E, ks) for f_, ks in LAGE.items()}
    null2 = []
    for _ in range(zieh):
        EV = verschoben(E, LAGE_SP)
        null2.append(max(lage_dq(EV, ks) for ks in LAGE.values()))
    g2 = float(np.nanpercentile(null2, 90))
    for f_, v in werte.items():
        print("  %-8s oberstes Zehntel minus alle stehenden %+.4f -> %s" % (f_, v, "✔ ueber dem Band" if v > g2 else "·"))
    print("  Nullband Bestes-von-3 (Lage verschoben): Mittel %+.4f, 90. Perzentil %+.4f" % (float(np.nanmean(null2)), g2))
    rs_st = lage_dq(E, RSI)
    print("  Gegenprobe rsi auf stehenden Ankern: %+.4f" % rs_st)
    # Markt mit gemeinsamer Nullwelt, Eigen mit Verschiebung je Asset
    ME = {f_: lage_dq(EM, ks) for f_, ks in LAGE_ME.items()}
    nm, ne = [], []
    mk_sp = [k for f_, ks in LAGE_ME.items() if f_.endswith("_markt") for k in ks]
    ek_sp = [k for f_, ks in LAGE_ME.items() if f_.endswith("_eigen") for k in ks]
    zieh_me = zieh
    for _ in range(zieh_me):
        k_ = int(rng.integers(24 * 60, 24 * 400))                  # gemeinsame Verschiebung in Stunden
        EV = dict(EM)
        for kk in mk_sp:
            ser = pd.Series(EM[kk]).groupby(STD).first()
            idx = np.searchsorted(stunden, STD)
            EV[kk] = ser.to_numpy()[(idx + k_) % len(stunden)]
        nm.append(max(lage_dq(EV, ks) for f_, ks in LAGE_ME.items() if f_.endswith("_markt")))
        EV2 = verschoben(EM, ek_sp)
        ne.append(max(lage_dq(EV2, ks) for f_, ks in LAGE_ME.items() if f_.endswith("_eigen")))
    gm, ge = float(np.nanpercentile(nm, 90)), float(np.nanpercentile(ne, 90))
    for f_, v in ME.items():
        g_ = gm if f_.endswith("_markt") else ge
        print("  L6 %-15s %+.4f gegen %+.4f -> %s" % (f_, v, g_, "✔" if v > g_ else "·"))
    # rollierend Teil 2 (je Familie eigenes Zehntel)
    rollw = {f_: [] for f_ in LAGE}
    for (j, mo) in monate:
        mi = j * 12 + (mo - 1)
        start = H(datetime(j, mo, 1))
        fen = BASIS & steh & (STD >= ab) & (MON < mi) & (STD < start - 24)
        ra = np.flatnonzero(fen); rt = np.flatnonzero(fen & HIT)
        ziel = np.flatnonzero(BASIS & steh & (MON == mi))
        if len(rt) < 3000 or len(ziel) < 200:
            continue
        for f_, ks in LAGE.items():
            m, _l = K2.fit_cv(ks, E, ra, rt, A24[rt], OFF[rt], STD)
            ct = m.z(E, ra, OFF[ra]) - OFF[ra]; cz = m.z(E, ziel, OFF[ziel]) - OFF[ziel]
            rollw[f_].append(ziel[cz >= np.quantile(ct, 0.9)])
    for f_, lst in rollw.items():
        s_ = np.concatenate(lst) if lst else np.zeros(0, int)
        stz = np.flatnonzero(BASIS & steh & np.isin(MON, np.unique(MON[s_]))) if len(s_) else s_
        v = dqs(s_) - dqs(stz) if len(s_) else np.nan
        print("  L5 rollierend %-8s %+.4f (%d) gegen das feste Band %+.4f -> %s" % (f_, v, len(s_), g2, "✔" if v > g2 else "·"))
    print()
    print("  ⚠️ Gebuehren und Finanzierung sind nicht eingerechnet (Regel 2).")
    print("SCHLUSS: vollstaendig")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
