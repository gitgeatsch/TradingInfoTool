# -*- coding: utf-8 -*-
"""K1 SCHRITT 2b - DIE KOMBINATION, ZWEITER ANLAUF (28.09.2026).

Voranalyse: `Basisinfos/Voranalyse_K1_Schritt2b_Kombination_28_09.md`,
abgestimmt (*ja, E1 bis E9 wie empfohlen*). Anlass: 2.677 - das Kurvenmodell
trug nicht, loeste aber die gesuchte Groesse auch nicht auf.

VORAB FESTGELEGT
    E1 Eingaenge   Variante A: rsi, momentum_kurz, ema_abstand_atr SELBSTBEZOGEN
                   (gegen den Median der eigenen letzten 720 h), je AKTUELL und
                   24 H ALT, dazu der bisherige Anstieg (24 h in eigener ATR).
                   Variante B: A plus oi_aenderung roh. KEINE Marktkurven.
    E2 Form        (b) GLATTE Kurve: 12 Stufen (Perzentile 1,10,...,99 des
                   Trainingsfensters), Strafe auf die Differenz benachbarter
                   Stufen (Staerke per Kreuzvalidierung) plus eine kleine feste
                   Grunddaempfung. Rueckfall (a), NUR wenn (b) das Tor (E7) nicht
                   besteht: Raender in 5 Stufen (< P1, P1-P10, Mitte, P90-P99,
                   > P99), Daempfung per Kreuzvalidierung. Der Anstieg in seinen
                   A4-Klassen (< 0, 0-1, 1-2, >= 2 ATR).
    E3 Fenster     WACHSEND: jeder Monat 2024-01 bis 2026-08 auf allen Ankern ab
                   2023-01 davor (nur bekannte Ausgaenge); dazu die feste Teilung
                   Suche 2023-2024 -> Pruefung 2025-01..2026-08 fuer die Nullwelt.
    E4 Lehrer      q5 (+5 vor -5 %, 24 h) gegen das Phase-Normal; 72 h Auskunft.
    E5 Hauptmass   Dq der AUSWAHL: q im obersten Zehntel des geschaetzten q minus
                   Phase-Normal (Summenform wie K1 Schritt 1), ungesehen; die
                   Zehntel-Grenze aus dem TRAININGSfenster (fester q-Wert);
                   gespiegelt das unterste Zehntel (Sperre).
    E6 Nullwelt    Zeitverschiebung je Asset, alle Eingaenge eines Assets um
                   denselben Versatz, 40 Ziehungen, dieselbe Kreuzvalidierung.
    E7 TOR         vor der Messung (--tor): gepflanzt +0,04 auf den oberen Rand
                   (P90+) eines verschobenen Eingangs muss in >= 4 von 5 Ziehungen
                   jenseits der Grenze liegen - sonst (a), sonst keine Messung.
    E8 Gegenpruef. Zufallseingaenge · Summe der Familien · 1 h aelter · je Asset,
                   Jahr, BTC-Drittel · 2022 (Moment-Bezug) · nur Hebelwerte ·
                   Zellen W1/W2 · vier Mengen (Kette).
    E9 kein Blocker stetiges q, K5-Tabelle als Ausgabe, keine Schwelle.

TRAEGT (Abschnitt 3 der Voranalyse)
    T0 Tor bestanden · T1 Dq der Auswahl (A oder B) jenseits der Nullwelt (90.
    Perzentil, Bestes-von-2), feste Teilung, alle vier Mengen; rollierend > 0 ·
    T2 Dq der Auswahl minus Dq der besten Einzelfamilie - fuer diesen Vergleich
    je Modell das oberste Zehntel der EIGENEN Testschaetzungen (gleicher Anteil) -
    jenseits seines Nullbands, >= 3 von 4 Mengen · T3 Rangordnung kalibriert
    (innerhalb jedes Monats, Steigung 0,7-1,3), Niveau ausgewiesen · T4 Dq der
    Auswahl > 0 in jedem Jahr und BTC-Drittel · T5 >= 60 % der Assets (>= 50
    Auswahlanker) mit Dq > 0 · R Zufall im Nullband · S unterstes Zehntel.
    Familien: rsi, momentum, ema_abstand (je mit 24-h-Zwilling), anstieg.

NUR LESEND (`mode=ro`). Keine Gebuehren (Regel 2), kein Stop, kein Ertrag.

    python messe_k1_schritt2b_kombination.py --menge bestand --tor --form b
    python messe_k1_schritt2b_kombination.py --menge unverzerrt:1 --form b
"""
from __future__ import annotations

import os
import sqlite3
import sys
from datetime import datetime

import numpy as np
import pandas as pd
from scipy import sparse
from scipy.optimize import minimize
from scipy.special import expit

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import messe_e2_beitraege as E2                                   # noqa: E402
from messe_e3_vorwaerts import monat_von                          # noqa: E402
from messe_k3_kontextflaeche import reihe                         # noqa: E402

B0 = datetime(2020, 1, 1)
PERZ12 = (1, 10, 20, 30, 40, 50, 60, 70, 80, 90, 99)
PERZ5 = (1, 10, 90, 99)
KANTEN_FEST = {"anstieg": (0.0, 1.0, 2.0)}
GITTER = (0, 6, 12, 18)
JAHR_H = 8760
SELBST_H = 720
MIN_VERSATZ = 1440
ZIEHUNGEN, SAAT = 40, 20261009
LAMBDAS = (20.0, 200.0, 2000.0, 20000.0)
GRUND = 1.0            # (b): kleine feste Grunddaempfung, macht b0/Stufen eindeutig
CV_BLOECKE = 4
HEBEL_DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "tradinginfotool.db")
FORM = "b"


def _h(d):
    return int((d - B0).total_seconds() // 3600)


SUCHE = (_h(datetime(2023, 1, 1)), _h(datetime(2025, 1, 1)))
PRUEF = (_h(datetime(2025, 1, 1)), _h(datetime(2026, 9, 1)))
ROLL_MONATE = [(j, m) for j in (2024, 2025, 2026) for m in range(1, 13) if (j, m) <= (2026, 8)]
FAM = {"rsi": ("rsi_s", "rsi_s24"), "momentum": ("mom_s", "mom_s24"),
       "ema_abstand": ("ema_s", "ema_s24"), "anstieg": ("anstieg",)}
VAR_A = tuple(x for f in FAM.values() for x in f)
VAR_B = VAR_A + ("oi",)


def logloss(z, y):
    return float(np.mean(np.logaddexp(0.0, z) - y * z)) if len(y) else np.nan


class Modell:
    """Logistisch additiv auf Log-Odds; Form (b) glatt, Form (a) Raender (E2)."""

    def __init__(self, namen, lam=20.0):
        self.namen = tuple(namen)
        self.lam = lam

    def _stufen(self, k):
        if k in KANTEN_FEST:
            return None
        return PERZ12 if FORM == "b" else PERZ5

    def _X(self, E, rows):
        r_, c_ = [], []
        for j, k in enumerate(self.namen):
            v = E[k][rows]
            ok = np.flatnonzero(np.isfinite(v))
            r_.append(ok)
            c_.append(self.ofs[j] + np.searchsorted(self.grenzen[j], v[ok]))
        r_ = np.concatenate(r_) if r_ else np.zeros(0, int)
        c_ = np.concatenate(c_) if c_ else np.zeros(0, int)
        return sparse.csr_matrix((np.ones(len(r_)), (r_, c_)), shape=(len(rows), int(self.ofs[-1])))

    def _strafe(self):
        """Strafmatrix P (w' P w / 2): (b) Nachbardifferenzen x lam + GRUND,
        (a) lam auf jede Stufe."""
        blocks = []
        for g in self.grenzen:
            m = len(g) + 1
            if FORM == "b" and m > 2:
                Dm = sparse.diags([np.ones(m - 1), -np.ones(m - 1)], [0, 1], shape=(m - 1, m))
                blocks.append(self.lam * (Dm.T @ Dm) + GRUND * sparse.identity(m))
            else:
                blocks.append(self.lam * sparse.identity(m))
        return sparse.block_diag(blocks, format="csr") if blocks else sparse.csr_matrix((0, 0))

    def fit(self, E, rows_alle, rows, y, off):
        self.grenzen = []
        for k in self.namen:
            st = self._stufen(k)
            if st is None:
                self.grenzen.append(np.array(KANTEN_FEST[k]))
            else:
                v = E[k][rows_alle]
                self.grenzen.append(np.nanpercentile(v, st) if np.isfinite(v).any()
                                    else np.full(len(st), np.nan))
        self.ofs = np.concatenate([[0], np.cumsum([len(g) + 1 for g in self.grenzen])]).astype(int)
        X = self._X(E, rows)
        P = self._strafe()

        def f(w):
            z = off + w[0] + X @ w[1:]
            r = expit(z) - y
            Pw = P @ w[1:] if P.shape[0] else np.zeros(0)
            val = float(np.sum(np.logaddexp(0.0, z) - y * z) + 0.5 * w[1:] @ Pw)
            return val, np.concatenate([[r.sum()], X.T @ r + Pw])
        w0 = np.zeros(X.shape[1] + 1)
        w0[0] = float(np.log(max(y.mean(), 1e-6) / max(1 - y.mean(), 1e-6)) - np.mean(off))
        self.w = minimize(f, w0, jac=True, method="L-BFGS-B", options={"maxiter": 800}).x
        return self

    def z(self, E, rows, off):
        return off + self.w[0] + self._X(E, rows) @ self.w[1:]


def fit_cv(namen, E, ra, rt, y, off, std):
    """Daempfung per zeitlich geblockter Kreuzvalidierung im Fenster (Ä1/Pflichtschritt 24)."""
    if not namen:
        return Modell(()).fit(E, ra, rt, y, off), np.nan
    st, sta = std[rt], std[ra]
    kanten = np.quantile(st, np.linspace(0, 1, CV_BLOECKE + 1)[1:-1])
    blk = np.searchsorted(kanten, st, "right"); blka = np.searchsorted(kanten, sta, "right")
    bester, wert = LAMBDAS[-1], np.inf
    for lam in LAMBDAS:
        tot = 0.0
        for b in range(CV_BLOECKE):
            te = blk == b
            if not te.any():
                continue
            lo, hi = st[te].min(), st[te].max()
            tr = (blk != b) & ((st < lo - 24) | (st > hi + 24))
            tra = (blka != b) & ((sta < lo - 24) | (sta > hi + 24))
            if tr.sum() < 1000:
                continue
            m = Modell(namen, lam).fit(E, ra[tra], rt[tr], y[tr], off[tr])
            z = m.z(E, rt[te], off[te])
            tot += float(np.sum(np.logaddexp(0.0, z) - y[te] * z))
        if tot < wert:
            bester, wert = lam, tot
    return Modell(namen, bester).fit(E, ra, rt, y, off), bester


def main() -> int:
    global FORM
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:                                         # noqa: BLE001
        pass
    E2.menge_aus_argv()
    FORM = sys.argv[sys.argv.index("--form") + 1] if "--form" in sys.argv else "b"
    tor = "--tor" in sys.argv
    probe = "--probe" in sys.argv
    zieh = 3 if probe else ZIEHUNGEN
    monate = ROLL_MONATE[:3] if probe else ROLL_MONATE
    print("=" * 120)
    print("K1 SCHRITT 2b - KOMBINATION · MENGE %s · FORM (%s) %s%s" % (
        E2.MENGE, FORM, "glatte 12-Stufen-Kurve" if FORM == "b" else "Raender in 5 Stufen",
        " · AUFLOESUNGS-TOR (--tor)" if tor else (" · WERKZEUGTEST (--probe)" if probe else "")))
    print("=" * 120)
    D = E2.lade(hmax=72, erste=(("u5", 1.05, True), ("d5", 0.95, False)), mit_atr=True)
    SYM, STD, syms = D["SYM"], D["STD"], D["syms"]
    n = len(SYM)
    t_u, t_d = D["T"]["u5"], D["T"]["d5"]
    A24 = ((t_u <= 24) & (t_u < t_d)).astype(np.float64)
    B24 = ((t_d <= 24) & (t_d <= t_u)).astype(np.float64)
    A72 = ((t_u <= 72) & (t_u < t_d)).astype(np.float64)
    B72 = ((t_d <= 72) & (t_d <= t_u)).astype(np.float64)
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
            lo = np.searchsorted(st, st - JAHR_H, "left")
            hi = np.searchsorted(st, st - W, "right")
            k = hi - lo
            gut = (st - st[0] >= JAHR_H) & (k > 1000)
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
            med = ser.rolling("%dh" % SELBST_H, closed="left", min_periods=240).median().to_numpy()
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

    GRID = np.isin(STD % 24, GITTER)
    BASIS = GRID & np.isfinite(OFF)
    HIT = (A24 + B24) > 0
    such = BASIS & (STD >= SUCHE[0]) & (STD < SUCHE[1])
    pruef = BASIS & (STD >= PRUEF[0]) & (STD < PRUEF[1])
    print("  Anker (Gitter, mit Phase-Normal): Suche %d · Pruefung %d · mit Treffer %d / %d · Symbole %d" % (
        such.sum(), pruef.sum(), (such & HIT).sum(), (pruef & HIT).sum(), len(np.unique(SYM[such | pruef]))))
    print("  Eingaenge A: %s · B: + oi · Daempfung per Kreuzvalidierung %s · Nullwelt %d Ziehungen" % (
        ", ".join(VAR_A), "/".join("%.0f" % x for x in LAMBDAS), zieh))

    def dq(ix, na=NA, nb=NB):
        """Dq wie K1 Schritt 1: q der Auswahl minus Normal, Summenform."""
        if not len(ix):
            return np.nan
        a, b = A24[ix].sum(), B24[ix].sum()
        sa, sb = na[ix].sum(), nb[ix].sum()
        return a / max(a + b, 1e-12) - sa / max(sa + sb, 1e-12)

    r_sa = np.flatnonzero(such); r_s = np.flatnonzero(such & HIT)
    r_pa = np.flatnonzero(pruef); r_p = np.flatnonzero(pruef & HIT)

    def fest(EE, namen, y=A24):
        """Feste Teilung: Dq der Auswahl mit Grenze aus dem Training (E5) und mit dem
        Zehntel der eigenen Testschaetzungen (T2), dazu G (Log-Loss)."""
        m, lam = fit_cv(namen, EE, r_sa, r_s, y[r_s], OFF[r_s], STD)
        b = Modell(()).fit(EE, r_sa, r_s, y[r_s], OFF[r_s])
        z_tr = m.z(EE, r_sa, OFF[r_sa]); z_te = m.z(EE, r_pa, OFF[r_pa])
        g_hi, g_lo = np.quantile(z_tr, 0.9), np.quantile(z_tr, 0.1)
        e_hi, e_lo = np.quantile(z_te, 0.9), np.quantile(z_te, 0.1)
        aus = dict(lam=lam, m=m, anteil=float(np.mean(z_te >= g_hi)))
        # Dq mit dem (ggf. gepflanzten) y: Treffer oben = y, Treffer unten = HIT und y == 0
        yy = y

        def dq_y(ix):
            if not len(ix):
                return np.nan
            a = yy[ix].sum(); bb = (HIT[ix] & (yy[ix] == 0)).sum()
            sa, sb = NA[ix].sum(), NB[ix].sum()
            return a / max(a + bb, 1e-12) - sa / max(sa + sb, 1e-12)
        aus["oben"] = dq_y(r_pa[z_te >= g_hi]); aus["unten"] = dq_y(r_pa[z_te <= g_lo])
        aus["oben_eigen"] = dq_y(r_pa[z_te >= e_hi]); aus["unten_eigen"] = dq_y(r_pa[z_te <= e_lo])
        zb = b.z(EE, r_p, OFF[r_p]); zm = m.z(EE, r_p, OFF[r_p])
        aus["G"] = 1000 * (logloss(zb, y[r_p]) - logloss(zm, y[r_p]))
        return aus

    def verschoben(EE):
        aus = dict(EE)
        rr = {}
        for tl in teile:
            L = len(tl)
            rr[int(SYM[tl[0]])] = int(rng.integers(MIN_VERSATZ, L - MIN_VERSATZ)) if L > 2 * MIN_VERSATZ else 0
        for k in EE:
            v = np.empty(n)
            for tl in teile:
                v[tl] = np.roll(EE[k][tl], rr[int(SYM[tl[0]])])
            aus[k] = v
        return aus

    # ══ E7 AUFLOESUNGS-TOR ═══════════════════════════════════════════════
    if tor:
        null_o = []
        for _ in range(zieh):
            null_o.append(fest(verschoben(E), VAR_A)["oben"])
        null_o = np.array(null_o)
        grenze = float(np.nanpercentile(null_o, 90))
        print()
        print("AUFLOESUNGS-TOR (E7) - Form (%s), feste Teilung, Variante A: Nullwelt Dq der Auswahl Mittel %+.4f, "
              "Streuung %.4f, 90. Perzentil %+.4f (%d Ziehungen)" % (FORM, float(np.nanmean(null_o)),
                                                                   float(np.nanstd(null_o, ddof=1)), grenze, zieh))
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
            print("  gepflanzt +%.2f auf den oberen Rand (P90+) von rsi_s (verschobene Kopie): Dq der Auswahl %s -> "
                  "gefunden %d von 5" % (d, " ".join("%+.4f" % x for x in werte), gef))
        ok = erg[0.04] >= 4
        print("  TOR (+0,04 in >= 4 von 5): %s" % ("✔ BESTANDEN - Form (%s) wird gemessen" % FORM if ok else
                                                  "⛔ NICHT BESTANDEN - Form (%s) loest +0,04 nicht auf" % FORM))
        print("SCHLUSS: vollstaendig")
        return 0

    # ══ FESTE TEILUNG: T1, T2, R, Gegenpruefungen ═════════════════════════
    rA, rB = fest(E, VAR_A), fest(E, VAR_B)
    rF = {f: fest(E, ks) for f, ks in FAM.items()}
    nO, nD = [], []
    for _ in range(zieh):
        EV = verschoben(E)
        a_, b_ = fest(EV, VAR_A), fest(EV, VAR_B)
        f_ = {f: fest(EV, ks) for f, ks in FAM.items()}
        nO.append(max(a_["oben"], b_["oben"]))
        nD.append(a_["oben_eigen"] - max(v["oben_eigen"] for v in f_.values()))
    nO, nD = np.array(nO), np.array(nD)
    g1, g2 = float(np.nanpercentile(nO, 90)), float(np.nanpercentile(nD, 90))
    print()
    print("=" * 120)
    print("FESTE TEILUNG Suche 2023-2024 -> Pruefung 2025-01..2026-08 · Dq der AUSWAHL (oberstes Zehntel des "
          "geschaetzten q, Grenze aus dem Training)")
    print("  A: oben %+.4f (Anteil im Test %.1f %%) · unten %+.4f · G %+.3f · Daempfung %.0f" % (
        rA["oben"], 100 * rA["anteil"], rA["unten"], rA["G"], rA["lam"]))
    print("  B: oben %+.4f (Anteil %.1f %%) · unten %+.4f · G %+.3f · Daempfung %.0f" % (
        rB["oben"], 100 * rB["anteil"], rB["unten"], rB["G"], rB["lam"]))
    print("  Nullwelt (Bestes-von-2): Mittel %+.4f · 90. Perzentil %+.4f" % (float(np.nanmean(nO)), g1))
    print("  Familien einzeln (eigenes Zehntel): %s" % " · ".join(
        "%s %+.4f" % (f, v["oben_eigen"]) for f, v in rF.items()))
    bf = max(rF, key=lambda f: rF[f]["oben_eigen"])
    d2 = rA["oben_eigen"] - rF[bf]["oben_eigen"]
    print("  T2 A (eigenes Zehntel %+.4f) minus beste Familie %s (%+.4f) = %+.4f gegen Nullband 90. Perzentil %+.4f" % (
        rA["oben_eigen"], bf, rF[bf]["oben_eigen"], d2, g2))
    print("  T1 %s · T2 %s" % ("✔ jenseits der Nullwelt" if max(rA["oben"], rB["oben"]) > g1 else "· nicht jenseits",
                               "✔ mehr als der beste Teil" if d2 > g2 else "· nicht mehr als der beste Teil"))
    print("  S  unterstes Zehntel: A %+.4f · B %+.4f (Sperre, wenn negativ)" % (rA["unten"], rB["unten"]))
    # R Zufall
    rz = np.random.default_rng(SAAT + 1)
    EZ = dict(E)
    for i, k in enumerate(VAR_A):
        x = rz.standard_normal(n); v = np.empty(n); g_ = (6, 24)[i % 2]
        for tl in teile:
            c = np.concatenate([[0.0], np.cumsum(x[tl])]); kk = np.arange(1, len(tl) + 1)
            v[tl] = (c[kk] - c[np.maximum(0, kk - g_)]) / np.minimum(kk, g_)
        EZ[k] = v
    zO = fest(EZ, VAR_A)["oben"]
    print("  R  Zufallseingaenge: Dq der Auswahl %+.4f gegen die Grenze %+.4f -> %s" % (
        zO, g1, "✔ im Nullband" if zO <= g1 else "⛔ JENSEITS"))
    # Summe der Familien (Doppelzaehlung)
    b0 = Modell(()).fit(E, r_sa, r_s, A24[r_s], OFF[r_s])
    zsum = b0.z(E, r_pa, OFF[r_pa]); zsum_tr = b0.z(E, r_sa, OFF[r_sa])
    for f, v in rF.items():
        mf = v["m"]
        zsum = zsum + mf.z(E, r_pa, OFF[r_pa]) - OFF[r_pa] - mf.w[0]
        zsum_tr = zsum_tr + mf.z(E, r_sa, OFF[r_sa]) - OFF[r_sa] - mf.w[0]
    gs = np.quantile(zsum_tr, 0.9)
    print("  Summe der einzeln geschaetzten Familien: Dq der Auswahl %+.4f (gemeinsam %+.4f)" % (
        dq(r_pa[zsum >= gs]), rA["oben"]))
    # 1 h aelter
    E1 = {k: alt(v, 1) for k, v in E.items()}
    print("  Eingaenge 1 h aelter: Dq der Auswahl %+.4f (aktuell %+.4f)" % (fest(E1, VAR_A)["oben"], rA["oben"]))
    # 2022 mit Moment-Bezug
    r22 = np.flatnonzero(GRID & (JAHR == 2022) & np.isfinite(OFF_M))
    if len(r22):
        z22 = rA["m"].z(E, r22, OFF_M[r22]); z_tr = rA["m"].z(E, r_sa, OFF[r_sa])
        g_hi = np.quantile(z_tr, 0.9); g_lo = np.quantile(z_tr, 0.1)
        print("  2022 (Moment-Bezug, Modell aus der Suche): oben %+.4f · unten %+.4f (Anteil oben %.1f %%)" % (
            dq(r22[z22 >= g_hi], MA, MB), dq(r22[z22 <= g_lo], MA, MB), 100 * np.mean(z22 >= g_hi)))

    # ══ ROLLIEREND, wachsendes Fenster (E3) ══════════════════════════════
    print()
    print("=" * 120)
    print("ROLLIEREND, WACHSEND: %d Monate %04d-%02d bis %04d-%02d, je auf allen Ankern ab 2023-01 davor" % (
        len(monate), monate[0][0], monate[0][1], monate[-1][0], monate[-1][1]))
    ZA, Z0 = np.full(n, np.nan), np.full(n, np.nan)
    SEL, SELU = np.zeros(n, bool), np.zeros(n, bool)
    ZF = {f: np.full(n, np.nan) for f in FAM}
    lams = []
    ab = _h(datetime(2023, 1, 1))
    for (j, mo) in monate:
        mi = j * 12 + (mo - 1)
        start = _h(datetime(j, mo, 1))
        fen = BASIS & (STD >= ab) & (MON < mi) & (STD < start - 24)
        ra = np.flatnonzero(fen); rt = np.flatnonzero(fen & HIT)
        ziel = np.flatnonzero(BASIS & (MON == mi))
        if len(rt) < 5000 or not len(ziel):
            continue
        y = A24[rt]; off = OFF[rt]
        Z0[ziel] = Modell(()).fit(E, ra, rt, y, off).z(E, ziel, OFF[ziel])
        m, lam = fit_cv(VAR_A, E, ra, rt, y, off, STD)
        lams.append(lam)
        zt = m.z(E, ra, OFF[ra])
        ZA[ziel] = m.z(E, ziel, OFF[ziel])
        SEL[ziel] = ZA[ziel] >= np.quantile(zt, 0.9)
        SELU[ziel] = ZA[ziel] <= np.quantile(zt, 0.1)
        for f, ks in FAM.items():
            ZF[f][ziel] = fit_cv(ks, E, ra, rt, y, off, STD)[0].z(E, ziel, OFF[ziel])
    alle = np.flatnonzero(np.isfinite(ZA))
    ev = alle[HIT[alle]]
    print("  gewaehlte Daempfung je Monat: %s" % " ".join("%.0f" % x for x in lams))
    sel = alle[SEL[alle]]; selu = alle[SELU[alle]]
    print("  Dq der Auswahl rollierend: oben %+.4f (Anteil %.1f %%) · unten %+.4f · G %+.3f" % (
        dq(sel), 100 * SEL[alle].mean(), dq(selu),
        1000 * (logloss(Z0[ev], A24[ev]) - logloss(ZA[ev], A24[ev]))))
    fz = []
    for f in FAM:
        zf = ZF[f][alle]
        fz.append("%s %+.4f" % (f, dq(alle[zf >= np.quantile(zf, 0.9)])))
    print("  Familien rollierend (eigenes Zehntel): %s · A (eigenes Zehntel) %+.4f" % (
        " · ".join(fz), dq(alle[ZA[alle] >= np.quantile(ZA[alle], 0.9)])))
    # 72 h
    s72 = sel[(A72[sel] + B72[sel]) > 0]; a72 = alle[(A72[alle] + B72[alle]) > 0]
    print("  72 h (Auskunft): q der Auswahl %.4f gegen alle %.4f" % (A72[s72].mean(), A72[a72].mean()))
    # T3 Rangordnung innerhalb des Monats
    pz = expit(ZA[ev]); yy = A24[ev]; mm = MON[ev]
    dp = np.empty_like(pz); dy = np.empty_like(pz)
    for mi in np.unique(mm):
        k = mm == mi
        dp[k] = pz[k] - pz[k].mean(); dy[k] = yy[k] - yy[k].mean()
    dez = np.quantile(dp, np.linspace(0, 1, 11))
    kb = np.clip(np.searchsorted(dez, dp, "right") - 1, 0, 9)
    cnt = np.bincount(kb, minlength=10)
    mp = np.bincount(kb, weights=dp, minlength=10) / np.maximum(cnt, 1)
    mo_ = np.bincount(kb, weights=dy, minlength=10) / np.maximum(cnt, 1)
    wt = cnt / cnt.sum()
    sl = np.sum(wt * (mp - np.sum(wt * mp)) * (mo_ - np.sum(wt * mo_))) / max(np.sum(wt * (mp - np.sum(wt * mp)) ** 2), 1e-12)
    print("  T3 Rangordnung innerhalb des Monats: Steigung %.2f -> %s" % (
        sl, "✔ kalibriert" if 0.7 <= sl <= 1.3 else "· nicht kalibriert"))
    print("     Zehntel geschaetzt (gegen Monatsmittel): %s" % " ".join("%+.3f" % x for x in mp))
    print("     Zehntel beobachtet (gegen Monatsmittel): %s" % " ".join("%+.3f" % x for x in mo_))
    print("     Niveau (Auskunft): geschaetzt %.4f · beobachtet %.4f" % (pz.mean(), yy.mean()))
    # T4
    btc = reihe([(E2.EINGESTELLT_DB, "SELECT stunde, close FROM stundenkurse WHERE symbol='BTC'"),
                 (E2.STUNDEN_DB, "SELECT stunde, close FROM stundenkurse WHERE symbol='BTC'")])
    b30 = np.full(n, np.nan)
    ok = (STD < len(btc)) & (STD >= 720)
    with np.errstate(divide="ignore", invalid="ignore"):
        b30[ok] = btc[STD[ok]] / btc[STD[ok] - 720] - 1.0
    werte4, zeile = [], []
    for j in (2024, 2025, 2026):
        v = dq(sel[JAHR[sel] == j]); werte4.append(v); zeile.append("%d %+.4f" % (j, v))
    bb = b30[alle]; okb = np.isfinite(bb)
    q1, q2 = np.quantile(bb[okb], (1 / 3, 2 / 3))
    for nm, lo_, hi_ in (("BTC tief", -np.inf, q1), ("BTC mitte", q1, q2), ("BTC hoch", q2, np.inf)):
        s_ = sel[np.isfinite(b30[sel]) & (b30[sel] > lo_) & (b30[sel] <= hi_)]
        v = dq(s_); werte4.append(v); zeile.append("%s %+.4f (%d)" % (nm, v, len(s_)))
    print("  T4 je Jahr und BTC-Drittel: %s · %s" % (" · ".join(zeile),
          "✔ ueberall positiv" if np.nanmin(werte4) > 0 else "⚠ NICHT ueberall positiv - reden"))
    # T5
    ga = [dq(sel[SYM[sel] == si]) for si in np.unique(SYM[sel]) if (SYM[sel] == si).sum() >= 50]
    ga = np.array(ga)
    print("  T5 je Asset (>= 50 Auswahlanker): %d Assets, Dq > 0 bei %.0f %% · %s" % (
        len(ga), 100 * np.mean(ga > 0), "✔" if np.mean(ga > 0) >= 0.6 else "·"))
    # nur Hebelwerte (Auskunft)
    try:
        c = sqlite3.connect("file:%s?mode=ro" % HEBEL_DB, uri=True)
        hebel = {r[0].upper() for r in c.execute("SELECT symbol FROM asset_hebel_settings")}
        c.close()
        in_h = np.array([s.upper() in hebel for s in syms])[SYM]
        sh = sel[in_h[sel]]
        print("  nur Hebelwerte des Betriebs (Namensgleichheit, Vorbehalt 2.612): %d Symbole · Dq der Auswahl %+.4f (%d)" % (
            len(np.unique(SYM[alle][in_h[alle]])), dq(sh), len(sh)))
    except Exception as exc:                                  # noqa: BLE001
        print("  Hebelwerte nicht lesbar: %s" % exc)
    # W1/W2 Hinweis
    print("  W1/W2 (Hinweis fuer Schritt 3, rollierend, beobachtet minus geschaetzt q):")
    pal = expit(ZA)
    for kurz, nm in (("rsi", "rsi"), ("mom", "momentum"), ("ema", "ema_abstand")):
        g90 = np.nanpercentile(E[kurz + "_s"][r_sa], 90); g90a = np.nanpercentile(E[kurz + "_s24"][r_sa], 90)
        ob = E[kurz + "_s"][ev] >= g90; ob24 = E[kurz + "_s24"][ev] >= g90a
        z2 = []
        for lab, s_ in (("beide oben", ob & ob24), ("nur jetzt", ob & ~ob24), ("nur 24 h", ~ob & ob24), ("keiner", ~ob & ~ob24)):
            z2.append("%s %+.3f (%d)" % (lab, A24[ev][s_].mean() - pal[ev][s_].mean(), s_.sum()) if s_.sum() >= 100 else "%s -" % lab)
        z1 = []
        for lab, s_ in (("<0", anst[ev] < 0), ("0-1", (anst[ev] >= 0) & (anst[ev] < 1)), ("1-2", (anst[ev] >= 1) & (anst[ev] < 2)), (">=2", anst[ev] >= 2)):
            t_ = ob & s_
            z1.append("%s %+.3f (%d)" % (lab, A24[ev][t_].mean() - pal[ev][t_].mean(), t_.sum()) if t_.sum() >= 100 else "%s -" % lab)
        print("     W2 %-11s %s" % (nm, " · ".join(z2)))
        print("     W1 %-11s oben x Anstieg: %s" % (nm, " · ".join(z1)))
    # K5-Tabelle
    print()
    print("=" * 120)
    print("K5-TABELLE (E9: Ausgabe, KEINE Schwelle) - rollierend, Variante A")
    nmon = len(np.unique(MON[alle])); nas = len(np.unique(SYM[alle]))
    pa_ = pal[alle]
    for nm, s_ in ([("q >= %.2f" % s, pa_ >= s) for s in (0.52, 0.55, 0.58, 0.60)] +
                   [("q <= %.2f" % s, pa_ <= s) for s in (0.45, 0.42, 0.40)]):
        ix = alle[s_]; ih = ix[HIT[ix]]
        qj = [A24[ih[JAHR[ih] == j]].mean() if (JAHR[ih] == j).sum() >= 50 else np.nan for j in (2024, 2025, 2026)]
        print("  %-10s Anker %7d · je Asset/Monat %6.2f · q beob %.4f · Dq %+.4f · je Jahr %s" % (
            nm, len(ix), len(ix) / max(nmon * nas, 1), A24[ih].mean() if len(ih) else np.nan, dq(ix),
            " / ".join("%.4f" % x if np.isfinite(x) else "-" for x in qj)))
    print("  Grundrate %.4f · Anker %d · Monate %d · Assets %d" % (A24[ev].mean(), len(alle), nmon, nas))
    print()
    print("  ⚠️ Gebuehren und Finanzierung sind nicht eingerechnet (Regel 2).")
    print("SCHLUSS: vollstaendig")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
