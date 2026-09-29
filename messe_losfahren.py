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
        print("  Querabgleich: oberstes Zehntel gesamt, rohes Normal %+.4f (2.680: einfache rsi-Regel etwa +0,073..+0,078) "
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
