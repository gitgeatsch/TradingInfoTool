# -*- coding: utf-8 -*-
"""K1 SCHRITT 2 - DIE KOMBINATION: die Kurven GEMEINSAM schaetzen (28.09.2026).

Voranalyse: `Basisinfos/Voranalyse_K1_Schritt2_Kombination_28_09.md`, abgestimmt
(*ja, C1 bis C8 wie empfohlen*) und committet VOR dem Bau (1295641).

VORAB FESTGELEGT
    C1 Eingaenge   Variante A (Hauptmodell), 9 Kurven: rsi, momentum_kurz,
                   ema_abstand_atr SELBSTBEZOGEN (gegen den Median der eigenen
                   letzten 720 h), je AKTUELL und 24 H ALT; funding_vortag und
                   konten_verh als MARKTmedian (alle Assets der Menge zur Stunde);
                   der bisherige Anstieg (24 h in eigener ATR). Variante B: A plus
                   oi_aenderung roh. Bestes-von-2.
    C2 Modell      logistisch additiv auf Log-Odds:
                       logit q = logit(q_Phase) + b0 + Summe Kurve_j(Stufe x_j)
                   12 Stufen je Kurve (Perzentile 1,10,...,99 des TRAININGS-
                   fensters), feste L2-Daempfung LAMBDA auf den Stufengewichten,
                   b0 frei. Fehlender Wert -> kein Beitrag dieser Kurve.
                   ⛔ GEAENDERT NACH DEM WERKZEUGTEST (abgestimmt 28.09., Voranalyse
                   Abschnitt 9, VOR der Messung): Ä1 die Daempfung je Modell und
                   Trainingsfenster per zeitlich geblockter Kreuzvalidierung (4
                   Bloecke, Gitter 20/200/2.000/20.000) statt fest 20 · Ä2 die
                   Marktkurven in DRITTELN · Ä3 dieselbe Kreuzvalidierung in jeder
                   Nullwelt-Ziehung. Anlass: die Anker sind nicht unabhaengig, die
                   feste Daempfung lernte Rauschen (Nullwelt im Mittel -17).
    C3 Kalibrierung ROLLIEREND: jeder Monat 2024-01 bis 2026-08 auf den 12 Monaten
                   davor geschaetzt (nur Anker, deren 24-h-Ausgang vor dem Monat
                   bekannt ist), dann auf den Monat angewandt. Zusaetzlich FEST:
                   Suche 2023-2024 -> Pruefung 2025-01 bis 2026-08 fuer die Nullwelt.
    C4 Lehrer      q5 (+5 vor -5 %, 24 h), nur Anker mit Treffer, gegen das
                   Phase-Normal (eigene letzte 12 Monate, Ausgaenge <= t - 24 h).
                   72 h als Auskunft: die Spanne darf das Vorzeichen nicht drehen.
    C5 Nullwelt    Zeitverschiebung: je Ziehung ALLE Asset-Eingaenge eines Assets um
                   DENSELBEN Versatz (>= 1.440 h), die Markteingaenge GEMEINSAM fuer
                   alle Assets; 40 Ziehungen; identisch geschaetzt (feste Teilung).
    C6 Regeltest   Zufallseingaenge derselben Art im selben Modell; Pflanzung +0,02 /
                   +0,04 auf den oberen Rand einer verschobenen (wirkungslosen) Kopie.
    C7 Gegenpruef. (a) Summe der einzeln geschaetzten Kurven gegen die gemeinsame
                   Schaetzung · (b) Eingaenge 1 h aelter · (c) je Asset, Jahr,
                   BTC-Drittel · (d) 2022 mit Moment-Bezug · (e) vier Mengen (Kette)
                   · (f) Marktmedian nur ueber die Hebelwerte des Betriebs · (g)
                   Vorpruefung der Wechselwirkungen W1/W2 (nur Auskunft).
    C8 kein Blocker stetiges q je Anker; die K5-Tabelle wird AUSGEGEBEN, keine
                   Schwelle gesetzt.

KENNZAHL G = mittlerer Log-Loss-Gewinn je Anker (in tausendstel nat) gegen das
Phase-Normal mit freiem b0, auf UNGESEHENEN Ankern.

TRAEGT (vorab, Abschnitt 3 der Voranalyse)
    T1 G der Kombination jenseits der Nullwelt (90. Perzentil, Bestes-von-2) -
       feste Teilung, in allen vier Mengen
    T2 G(A) - max G(einzelne Familie) jenseits seines Nullbands, >= 3 von 4 Mengen
    T3 kalibriert (rollierend): Steigung 0,7-1,3 und |beob - geschaetzt| <= 0,02 in
       jedem Zehntel mit >= 1.000 Ankern
    T4 G > 0 in jedem Jahr 2024/2025/2026 und jedem BTC-Drittel (rollierend)
    T5 >= 60 % der Assets (>= 200 Anker) mit G > 0 (rollierend)
    R  Zufallseingaenge im Nullband; Pflanzung gefunden ab einer benannten Groesse
    Familie = ein Merkmal mit seinem 24-h-Zwilling (rsi, momentum, ema_abstand,
    funding_markt, konten_markt, anstieg).

NUR LESEND (`mode=ro`). Keine Gebuehren (Regel 2), kein Stop, kein Ertrag.

    python messe_k1_schritt2_kombination.py --menge unverzerrt:1
    python messe_k1_schritt2_kombination.py --menge bestand --probe   (Werkzeugtest)
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
PERZ = (1, 10, 20, 30, 40, 50, 60, 70, 80, 90, 99)
NST = len(PERZ) + 1
GITTER = (0, 6, 12, 18)
JAHR_H = 8760
SELBST_H = 720
MIN_VERSATZ = 1440
ZIEHUNGEN, SAAT = 40, 20261008
LAMBDA = 20.0
HEBEL_DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "tradinginfotool.db")


def _h(d):
    return int((d - B0).total_seconds() // 3600)


SUCHE = (_h(datetime(2023, 1, 1)), _h(datetime(2025, 1, 1)))
PRUEF = (_h(datetime(2025, 1, 1)), _h(datetime(2026, 9, 1)))
ROLL_MONATE = [(j, m) for j in (2024, 2025, 2026) for m in range(1, 13) if (j, m) <= (2026, 8)]

FAM_A = {"rsi": ("rsi_s", "rsi_s24"), "momentum": ("mom_s", "mom_s24"),
         "ema_abstand": ("ema_s", "ema_s24"), "funding_markt": ("fund_m",),
         "konten_markt": ("kv_m",), "anstieg": ("anstieg",)}
VAR_A = tuple(x for f in FAM_A.values() for x in f)
VAR_B = VAR_A + ("oi",)
MARKT = ("fund_m", "kv_m")


def logloss(z, y):
    return float(np.mean(np.logaddexp(0.0, z) - y * z)) if len(y) else np.nan


# Stufen je Eingang - Vorgabe PERZ; per Option --markt-drittel die Marktkurven
# in Dritteln (Werkzeugtest 28.09.: 12 Stufen je Markttag ueberanpassen, siehe
# Voranalyse Abschnitt 9)
PERZ_JE = {}


class Modell:
    """Logistisch additiv, Stufen je Kurve aus dem Trainingsfenster (C2)."""

    def __init__(self, namen, lam=None):
        self.namen = tuple(namen)
        self.lam = LAMBDA if lam is None else lam
        self.perz = [PERZ_JE.get(k, PERZ) for k in self.namen]
        self.ofs = np.concatenate([[0], np.cumsum([len(p) + 1 for p in self.perz])]).astype(int)

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

    def fit(self, E, rows_alle, rows, y, off):
        self.grenzen = [np.nanpercentile(E[k][rows_alle], p) if np.isfinite(E[k][rows_alle]).any()
                        else np.full(len(p), np.nan) for k, p in zip(self.namen, self.perz)]
        X = self._X(E, rows)
        p = X.shape[1]

        lam = self.lam

        def f(w):
            z = off + w[0] + X @ w[1:]
            r = expit(z) - y
            val = float(np.sum(np.logaddexp(0.0, z) - y * z) + 0.5 * lam * w[1:] @ w[1:])
            return val, np.concatenate([[r.sum()], X.T @ r + lam * w[1:]])
        w0 = np.zeros(p + 1)
        w0[0] = float(np.log(max(y.mean(), 1e-6) / max(1 - y.mean(), 1e-6)) - np.mean(off))
        self.w = minimize(f, w0, jac=True, method="L-BFGS-B", options={"maxiter": 800}).x
        return self

    def z(self, E, rows, off):
        return off + self.w[0] + self._X(E, rows) @ self.w[1:]


# Ä1 (abgestimmt 28.09., Voranalyse Abschnitt 9): die Daempfung je Modell und
# Trainingsfenster selbst bestimmt - zeitlich geblockte Kreuzvalidierung
# INNERHALB des Fensters, 4 Bloecke, je 24 h Abstand an den Blockgrenzen
# (ueberlappende Ausgangsfenster), das Gitter unten; das beste nach Log-Loss
# auf dem ausgelassenen Block. Nur Vergangenheit.
LAMBDAS = (20.0, 200.0, 2000.0, 20000.0)
CV_BLOECKE = 4


def fit_cv(namen, E, ra, rt, y, off, std):
    """-> (Modell mit der gewaehlten Daempfung, Daempfung). y/off je Zeile von rt."""
    if not namen:
        return Modell(()).fit(E, ra, rt, y, off), np.nan
    st, sta = std[rt], std[ra]
    kanten = np.quantile(st, np.linspace(0, 1, CV_BLOECKE + 1)[1:-1])
    blk = np.searchsorted(kanten, st, "right"); blka = np.searchsorted(kanten, sta, "right")
    bester, wert = None, np.inf
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
    global LAMBDA
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:                                         # noqa: BLE001
        pass
    E2.menge_aus_argv()
    probe = "--probe" in sys.argv
    zieh = 3 if probe else ZIEHUNGEN
    monate = ROLL_MONATE[:3] if probe else ROLL_MONATE
    print("=" * 120)
    print("K1 SCHRITT 2 - KOMBINATION · MENGE %s%s" % (E2.MENGE, " · WERKZEUGTEST (--probe)" if probe else ""))
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
    FR = {m: D["F"][m].astype(np.float64) for m in
          ("rsi", "momentum_kurz", "ema_abstand_atr", "funding_vortag", "konten_verh", "oi_aenderung")}
    del D
    MON = monat_von(STD)
    JAHR = (MON // 12).astype(np.int16)
    rng = np.random.default_rng(SAAT)
    ordnung = np.lexsort((STD, SYM))
    teile = np.split(ordnung, np.flatnonzero(np.diff(SYM[ordnung])) + 1)
    H0 = STD - STD.min()
    LH = int(H0.max()) + 1

    # ── Phase-Normal (wie K1 Schritt 1) und Moment
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

    # ── Eingaenge
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

    def markt_h(v, maske=None):
        """Median aller (bzw. der maskierten) Assets je Stunde -> Reihe je Stunde."""
        m = np.isfinite(v) if maske is None else (np.isfinite(v) & maske)
        s = pd.Series(v[m]).groupby(H0[m]).median()
        aus = np.full(LH, np.nan); aus[s.index.to_numpy()] = s.to_numpy()
        return aus

    with np.errstate(divide="ignore", invalid="ignore"):
        anst = VOR24 / np.maximum(ATR, 1e-12)
    E = {}
    for kurz, m in (("rsi", "rsi"), ("mom", "momentum_kurz"), ("ema", "ema_abstand_atr")):
        s = selbst(FR[m])
        E[kurz + "_s"] = s
        E[kurz + "_s24"] = alt(s, 24)
    MH = {"fund_m": markt_h(FR["funding_vortag"]), "kv_m": markt_h(FR["konten_verh"])}
    for k in MARKT:
        E[k] = MH[k][H0]
    E["anstieg"] = anst
    E["oi"] = FR["oi_aenderung"]
    ASSET_IN = [k for k in E if k not in MARKT]

    GRID = np.isin(STD % 24, GITTER)
    BASIS = GRID & np.isfinite(OFF)
    HIT = (A24 + B24) > 0
    such = BASIS & (STD >= SUCHE[0]) & (STD < SUCHE[1])
    pruef = BASIS & (STD >= PRUEF[0]) & (STD < PRUEF[1])
    print("  Anker (Gitter, mit Phase-Normal): Suche %d · Pruefung %d · mit Treffer %d / %d · Symbole %d" % (
        such.sum(), pruef.sum(), (such & HIT).sum(), (pruef & HIT).sum(), len(np.unique(SYM[such | pruef]))))
    print("  Eingaenge A: %s · B: + oi · LAMBDA %.0f · Stufen %d · Nullwelt %d Ziehungen" % (
        ", ".join(VAR_A), LAMBDA, NST, zieh))

    if "--diag-suche" in sys.argv:
        # WERKZEUGDIAGNOSE (28.09.): NUR innerhalb der Suche - 2023 schaetzen,
        # 2024 anwenden. Die Pruefzeit 2025/26 bleibt unberuehrt, damit die
        # Stufenzahl der Marktkurven nicht nach dem Ergebnis gewaehlt wird
        t_a = np.flatnonzero(BASIS & (JAHR == 2023)); t_h = np.flatnonzero(BASIS & (JAHR == 2023) & HIT)
        e_h = np.flatnonzero(BASIS & (JAHR == 2024) & HIT)
        print()
        print("WERKZEUGDIAGNOSE innerhalb der Suche: 2023 -> 2024 (Anker %d / %d)" % (len(t_h), len(e_h)))
        for bez, pj in (("Marktkurven 12 Stufen", {}), ("Marktkurven in Dritteln", {k: (100 / 3, 200 / 3) for k in MARKT})):
            PERZ_JE.clear(); PERZ_JE.update(pj)
            zeile = []
            nur_asset = tuple(k for k in VAR_A if k not in MARKT)
            for nm, ks in list(FAM_A.items()) + [("A gesamt", VAR_A), ("A ohne Markt", nur_asset)]:
                m = Modell(ks).fit(E, t_a, t_h, A24[t_h], OFF[t_h])
                b = Modell(()).fit(E, t_a, t_h, A24[t_h], OFF[t_h])
                gi = 1000 * (logloss(b.z(E, t_h, OFF[t_h]), A24[t_h]) - logloss(m.z(E, t_h, OFF[t_h]), A24[t_h]))
                go = 1000 * (logloss(b.z(E, e_h, OFF[e_h]), A24[e_h]) - logloss(m.z(E, e_h, OFF[e_h]), A24[e_h]))
                zeile.append("%s %+.2f/%+.2f" % (nm, gi, go))
            print("  %-24s (G in der Schaetzung / auf 2024): %s" % (bez, " · ".join(zeile)))
        PERZ_JE.clear()
        # Daempfung: wie haengt der Uebertrag 2023 -> 2024 an LAMBDA?
        l0 = LAMBDA
        nur_asset = tuple(k for k in VAR_A if k not in MARKT)
        PERZ_JE.update({k: (100 / 3, 200 / 3) for k in MARKT})
        for lam in (20.0, 200.0, 2000.0, 20000.0):
            LAMBDA = lam
            zeile = []
            for nm, ks in (("ema_abstand", FAM_A["ema_abstand"]), ("rsi", FAM_A["rsi"]),
                           ("A ohne Markt", nur_asset), ("A gesamt (Markt in Dritteln)", VAR_A)):
                m = Modell(ks).fit(E, t_a, t_h, A24[t_h], OFF[t_h])
                b = Modell(()).fit(E, t_a, t_h, A24[t_h], OFF[t_h])
                go = 1000 * (logloss(b.z(E, e_h, OFF[e_h]), A24[e_h]) - logloss(m.z(E, e_h, OFF[e_h]), A24[e_h]))
                zeile.append("%s %+.2f" % (nm, go))
            print("  LAMBDA %7.0f (G auf 2024): %s" % (lam, " · ".join(zeile)))
        LAMBDA = l0
        PERZ_JE.clear()
        print("SCHLUSS: vollstaendig")
        return 0
    # Ä2 (abgestimmt 28.09.): Marktkurven in DRITTELN - ihre Fallzahl sind
    # Markttage (wie K3a)
    PERZ_JE.clear()
    PERZ_JE.update({k: (100 / 3, 200 / 3) for k in MARKT})
    print("  Ä1 Daempfung je Modell und Fenster per Kreuzvalidierung (%d Bloecke, Gitter %s) · "
          "Ä2 Marktkurven in Dritteln (%s)" % (CV_BLOECKE, "/".join("%.0f" % x for x in LAMBDAS), ", ".join(MARKT)))

    # ══ FESTE TEILUNG (Suche -> Pruefung): G, Familien, Nullwelt ══════════
    r_sa = np.flatnonzero(such); r_s = np.flatnonzero(such & HIT); r_p = np.flatnonzero(pruef & HIT)

    LAM_FEST = {}

    def g_fest(EE, namen, y=A24, merke=None):
        m, lam = fit_cv(namen, EE, r_sa, r_s, y[r_s], OFF[r_s], STD)
        if merke:
            LAM_FEST[merke] = lam
        b = Modell(()).fit(EE, r_sa, r_s, y[r_s], OFF[r_s])
        zb = b.z(EE, r_p, OFF[r_p]); zm = m.z(EE, r_p, OFF[r_p])
        return 1000 * (logloss(zb, y[r_p]) - logloss(zm, y[r_p])), m, b

    def alle_g(EE, merke=False):
        gA, mA, bA = g_fest(EE, VAR_A, merke="A" if merke else None)
        gB = g_fest(EE, VAR_B, merke="B" if merke else None)[0]
        gf = {f: g_fest(EE, ks, merke=f if merke else None)[0] for f, ks in FAM_A.items()}
        return gA, gB, gf, mA, bA

    gA, gB, gF, mA_f, bA_f = alle_g(E, merke=True)
    print("  gewaehlte Daempfung (feste Teilung): %s" % " · ".join(
        "%s %.0f" % (k, v) for k, v in LAM_FEST.items()))

    def verschoben(EE):
        aus = dict(EE)
        rr = {}
        for tl in teile:
            L = len(tl)
            rr[int(SYM[tl[0]])] = int(rng.integers(MIN_VERSATZ, L - MIN_VERSATZ)) if L > 2 * MIN_VERSATZ else 0
        for k in ASSET_IN:
            v = np.empty(n)
            for tl in teile:
                v[tl] = np.roll(EE[k][tl], rr[int(SYM[tl[0]])])
            aus[k] = v
        R = int(rng.integers(60 * 24, LH - 60 * 24))
        for k in MARKT:
            aus[k] = np.roll(MH[k], R)[H0]
        return aus

    nullA, nullB, nullD = [], [], []
    for _ in range(zieh):
        a_, b_, f_, _m, _b = alle_g(verschoben(E))
        nullA.append(a_); nullB.append(b_); nullD.append(a_ - max(f_.values()))
    nullA, nullB, nullD = map(np.array, (nullA, nullB, nullD))
    grenze1 = float(np.percentile(np.maximum(nullA, nullB), 90))
    grenze2 = float(np.percentile(nullD, 90))
    print()
    print("=" * 120)
    print("FESTE TEILUNG Suche 2023-2024 -> Pruefung 2025-01..2026-08 · G in tausendstel nat je Anker")
    print("  Kombination A  G %+.3f · Kombination B  G %+.3f · Nullwelt (Bestes-von-2) Mittel %+.3f, "
          "90. Perzentil %+.3f" % (gA, gB, float(np.mean(np.maximum(nullA, nullB))), grenze1))
    print("  Familien einzeln: %s" % " · ".join("%s %+.3f" % (f, g) for f, g in gF.items()))
    bestf = max(gF, key=gF.get)
    print("  T2 A minus beste Familie (%s): %+.3f gegen Nullband 90. Perzentil %+.3f" % (bestf, gA - gF[bestf], grenze2))
    print("  T1 %s · T2 %s" % ("✔ jenseits der Nullwelt" if max(gA, gB) > grenze1 else "· nicht jenseits",
                               "✔ mehr als der beste Teil" if gA - gF[bestf] > grenze2 else "· nicht mehr als der beste Teil"))

    # ── C6 Regeltest: Zufallseingaenge und Pflanzung
    rz = np.random.default_rng(SAAT + 1)
    EZ = dict(E)
    for i, k in enumerate(("rsi_s", "rsi_s24", "mom_s", "mom_s24", "ema_s", "ema_s24", "anstieg")):
        x = rz.standard_normal(n); v = np.empty(n); g_ = (6, 24)[i % 2]
        for tl in teile:
            c = np.concatenate([[0.0], np.cumsum(x[tl])]); kk = np.arange(1, len(tl) + 1)
            v[tl] = (c[kk] - c[np.maximum(0, kk - g_)]) / np.minimum(kk, g_)
        EZ[k] = v
    for k in MARKT:
        x = rz.standard_normal(LH); c = np.concatenate([[0.0], np.cumsum(x)]); kk = np.arange(1, LH + 1)
        EZ[k] = ((c[kk] - c[np.maximum(0, kk - 24)]) / np.minimum(kk, 24))[H0]
    gZ = g_fest(EZ, VAR_A)[0]
    print("  R  Zufallseingaenge (A-Aufbau): G %+.3f gegen die Grenze %+.3f -> %s" % (
        gZ, grenze1, "✔ im Nullband" if gZ <= grenze1 else "⛔ JENSEITS - die Regel meldet Zufall"))
    for d in (0.02, 0.04):
        gef = 0
        for _ in range(2 if probe else 5):
            EV = verschoben(E)
            gr = np.nanpercentile(EV["rsi_s"][r_sa], (90,))[0]
            y = A24.copy()
            oben = np.flatnonzero((EV["rsi_s"] >= gr) & HIT & (such | pruef))
            kand = oben[B24[oben] == 1]
            w = rz.choice(kand, size=min(int(round(d * len(oben))), len(kand)), replace=False)
            y[w] = 1.0
            gP = g_fest(EV, VAR_A, y=y)[0]
            gef += int(gP > grenze1)
        print("  R  Pflanzung +%.2f auf den oberen Rand (P90+) einer verschobenen Kopie: gefunden %d von %d" % (
            d, gef, 2 if probe else 5))

    # ── C7 (a) Doppelzaehlung: Summe der einzeln geschaetzten Familien
    zb = bA_f.z(E, r_p, OFF[r_p])
    zsum = zb.copy()
    for f, ks in FAM_A.items():
        mf = fit_cv(ks, E, r_sa, r_s, A24[r_s], OFF[r_s], STD)[0]
        bf = mf.w[0]
        zsum += mf.z(E, r_p, OFF[r_p]) - OFF[r_p] - bf
    zA = mA_f.z(E, r_p, OFF[r_p])
    gsum = 1000 * (logloss(zb, A24[r_p]) - logloss(zsum, A24[r_p]))

    def steigung(z, y):
        p = expit(z)
        dez = np.quantile(p, np.linspace(0, 1, 11))
        k = np.clip(np.searchsorted(dez, p, "right") - 1, 0, 9)
        cnt = np.bincount(k, minlength=10); mp = np.bincount(k, weights=p, minlength=10) / np.maximum(cnt, 1)
        mo = np.bincount(k, weights=y, minlength=10) / np.maximum(cnt, 1)
        w = cnt / cnt.sum(); xm = np.sum(w * mp); ym = np.sum(w * mo)
        sl = np.sum(w * (mp - xm) * (mo - ym)) / max(np.sum(w * (mp - xm) ** 2), 1e-12)
        return sl, mp, mo, cnt
    print("  C7a Summe der einzeln geschaetzten Familien: G %+.3f (gemeinsam %+.3f) · Kalibrierungssteigung "
          "Summe %.2f / gemeinsam %.2f" % (gsum, gA, steigung(zsum, A24[r_p])[0], steigung(zA, A24[r_p])[0]))

    # ── C7 (b) Eingaenge 1 h aelter
    E1 = dict(E)
    for k in ("rsi", "mom", "ema"):
        E1[k + "_s"] = alt(E[k + "_s"], 1); E1[k + "_s24"] = alt(E[k + "_s"], 25)
    E1["anstieg"] = alt(E["anstieg"], 1); E1["oi"] = alt(E["oi"], 1)
    for k in MARKT:
        E1[k] = np.roll(MH[k], 1)[H0]
    print("  C7b Eingaenge 1 h aelter: G %+.3f (aktuell %+.3f)" % (g_fest(E1, VAR_A)[0], gA))

    # ── C7 (d) 2022 mit Moment-Bezug (Modell aus der Suche)
    r22 = np.flatnonzero(GRID & HIT & (JAHR == 2022) & np.isfinite(OFF_M))
    if len(r22):
        m22 = mA_f
        b22 = Modell(()).fit(E, r_sa, r_s, A24[r_s], OFF[r_s])
        g22 = 1000 * (logloss(b22.z(E, r22, OFF_M[r22]), A24[r22]) - logloss(m22.z(E, r22, OFF_M[r22]), A24[r22]))
        print("  C7d 2022 (Moment-Bezug, Modell aus der Suche): G %+.3f auf %d Ankern" % (g22, len(r22)))
    else:
        print("  C7d 2022: keine Anker")

    # ── C7 (f) Marktmedian nur ueber die Hebelwerte des Betriebs
    try:
        c = sqlite3.connect("file:%s?mode=ro" % HEBEL_DB, uri=True)
        hebel = {r[0].upper() for r in c.execute("SELECT symbol FROM asset_hebel_settings")}
        c.close()
    except Exception as exc:                                  # noqa: BLE001
        hebel = set(); print("  C7f Hebelliste nicht lesbar: %s" % exc)
    if hebel:
        in_h = np.array([s.upper() in hebel for s in syms])
        mask = in_h[SYM]
        EF = dict(E); MF = {}
        for k, m in (("fund_m", "funding_vortag"), ("kv_m", "konten_verh")):
            MF[k] = markt_h(FR[m], mask); EF[k] = MF[k][H0]
        kor = [float(pd.Series(MH[k]).corr(pd.Series(MF[k]))) for k in MARKT]
        print("  C7f Marktmedian nur ueber die Hebelwerte (%d von %d der Liste in der Menge, Namensgleichheit - "
              "Vorbehalt 2.612): Korrelation mit dem Median ueber alle %.3f / %.3f · G %+.3f (alle %+.3f)" % (
                  len({syms[i].upper() for i in np.unique(SYM)} & hebel), len(hebel), kor[0], kor[1],
                  g_fest(EF, VAR_A)[0], gA))

    # ══ ROLLIEREND (C3): jeder Monat aus den 12 Monaten davor ═════════════
    print()
    print("=" * 120)
    print("ROLLIEREND: %d Monate %04d-%02d bis %04d-%02d, je auf den 12 Monaten davor geschaetzt" % (
        len(monate), monate[0][0], monate[0][1], monate[-1][0], monate[-1][1]))
    ZA, ZB, Z0 = np.full(n, np.nan), np.full(n, np.nan), np.full(n, np.nan)
    ZF = {f: np.full(n, np.nan) for f in FAM_A}
    LAM_ROLL = []
    for (j, mo) in monate:
        mi = j * 12 + (mo - 1)
        start = _h(datetime(j, mo, 1))
        fen = BASIS & (MON >= mi - 12) & (MON < mi) & (STD < start - 24)
        ra = np.flatnonzero(fen); rt = np.flatnonzero(fen & HIT)
        ziel = np.flatnonzero(BASIS & (MON == mi))
        if len(rt) < 5000 or not len(ziel):
            continue
        y = A24[rt]; off = OFF[rt]
        b = Modell(()).fit(E, ra, rt, y, off)
        Z0[ziel] = b.z(E, ziel, OFF[ziel])
        mA_r, lA = fit_cv(VAR_A, E, ra, rt, y, off, STD)
        ZA[ziel] = mA_r.z(E, ziel, OFF[ziel])
        ZB[ziel] = fit_cv(VAR_B, E, ra, rt, y, off, STD)[0].z(E, ziel, OFF[ziel])
        LAM_ROLL.append(lA)
        for f, ks in FAM_A.items():
            ZF[f][ziel] = fit_cv(ks, E, ra, rt, y, off, STD)[0].z(E, ziel, OFF[ziel])
    ev = np.flatnonzero(np.isfinite(ZA) & HIT)
    y = A24[ev]
    print("  gewaehlte Daempfung A je Monat: %s" % " ".join("%.0f" % x for x in LAM_ROLL))

    def G(z0, z, ix):
        return 1000 * (logloss(z0[ix], A24[ix]) - logloss(z[ix], A24[ix])) if len(ix) else np.nan
    print("  G rollierend: A %+.3f · B %+.3f · Familien %s" % (
        G(Z0, ZA, ev), G(Z0, ZB, ev), " · ".join("%s %+.3f" % (f, G(Z0, ZF[f], ev)) for f in FAM_A)))
    pA = expit(ZA[ev])
    dez = np.quantile(pA, (0.1, 0.9))
    lo, hi = pA <= dez[0], pA >= dez[1]
    print("  Spanne 24 h: q beobachtet unterstes Zehntel %.4f · alle %.4f · oberstes Zehntel %.4f (geschaetzt %.4f / %.4f)" % (
        y[lo].mean(), y.mean(), y[hi].mean(), pA[lo].mean(), pA[hi].mean()))
    ev72 = np.flatnonzero(np.isfinite(ZA) & ((A72 + B72) > 0))
    p72 = expit(ZA[ev72]); d72 = np.quantile(p72, (0.1, 0.9))
    print("  C4 Spanne 72 h (dasselbe Modell): unterstes Zehntel %.4f · alle %.4f · oberstes Zehntel %.4f" % (
        A72[ev72][p72 <= d72[0]].mean(), A72[ev72].mean(), A72[ev72][p72 >= d72[1]].mean()))

    # T3 Kalibrierung
    sl, mp, mo_, cnt = steigung(ZA[ev], y)
    dmax = max(abs(mo_[i] - mp[i]) for i in range(10) if cnt[i] >= 1000) if (cnt >= 1000).any() else np.nan
    print("  T3 Kalibrierung: Steigung %.2f · groesste Abweichung je Zehntel %.4f · %s" % (
        sl, dmax, "✔ kalibriert" if 0.7 <= sl <= 1.3 and dmax <= 0.02 else "· NICHT kalibriert"))
    print("     Zehntel geschaetzt: %s" % " ".join("%.3f" % x for x in mp))
    print("     Zehntel beobachtet: %s" % " ".join("%.3f" % x for x in mo_))
    zk = ZA.copy()
    for mi in np.unique(MON[ev]):
        ix = ev[MON[ev] == mi]
        lo_, hi_ = -3.0, 3.0
        for _ in range(40):
            c_ = 0.5 * (lo_ + hi_)
            if expit(ZA[ix] + c_).mean() > A24[ix].mean():
                hi_ = c_
            else:
                lo_ = c_
        zk[ix] = ZA[ix] + 0.5 * (lo_ + hi_)
    sl2, mp2, mo2, cnt2 = steigung(zk[ev], y)
    dmax2 = max(abs(mo2[i] - mp2[i]) for i in range(10) if cnt2[i] >= 1000) if (cnt2 >= 1000).any() else np.nan
    print("     ohne Monatsversatz (Diagnose, nutzt den Monatsausgang): Steigung %.2f · groesste Abweichung %.4f" % (
        sl2, dmax2))

    # T4 je Jahr und BTC-Drittel
    btc = reihe([(E2.EINGESTELLT_DB, "SELECT stunde, close FROM stundenkurse WHERE symbol='BTC'"),
                 (E2.STUNDEN_DB, "SELECT stunde, close FROM stundenkurse WHERE symbol='BTC'")])
    b30 = np.full(n, np.nan)
    ok = (STD < len(btc)) & (STD - 720 >= 0)
    with np.errstate(divide="ignore", invalid="ignore"):
        b30[ok] = btc[STD[ok]] / btc[STD[ok] - 720] - 1.0
    zeile = []
    for j in (2024, 2025, 2026):
        ix = ev[JAHR[ev] == j]
        zeile.append("%d %+.3f (%d)" % (j, G(Z0, ZA, ix), len(ix)))
    bb = b30[ev]; okb = np.isfinite(bb)
    q1, q2 = np.quantile(bb[okb], (1 / 3, 2 / 3))
    for nm, sel in (("BTC tief", bb <= q1), ("BTC mitte", (bb > q1) & (bb <= q2)), ("BTC hoch", bb > q2)):
        ix = ev[sel & okb]
        zeile.append("%s %+.3f (%d)" % (nm, G(Z0, ZA, ix), len(ix)))
    gj = [G(Z0, ZA, ev[JAHR[ev] == j]) for j in (2024, 2025, 2026)]
    gb = [G(Z0, ZA, ev[s & okb]) for s in (bb <= q1, (bb > q1) & (bb <= q2), bb > q2)]
    print("  T4 je Jahr und BTC-Drittel (30 Tage): %s · %s" % (
        " · ".join(zeile), "✔ ueberall positiv" if min(gj + gb) > 0 else "⚠ NICHT ueberall positiv - reden"))

    # T5 je Asset
    ga = []
    for si in np.unique(SYM[ev]):
        ix = ev[SYM[ev] == si]
        if len(ix) >= 200:
            ga.append(G(Z0, ZA, ix))
    ga = np.array(ga)
    print("  T5 je Asset (>= 200 Anker): %d Assets, G > 0 bei %.0f %% · Median %+.3f · %s" % (
        len(ga), 100 * np.mean(ga > 0), float(np.median(ga)), "✔" if np.mean(ga > 0) >= 0.6 else "·"))

    # C7 (g) Vorpruefung W1/W2 - additives Modell in den Zellen systematisch daneben?
    print("  C7g Vorpruefung Wechselwirkungen (rollierend, beobachtet minus geschaetzt, Anker):")
    for kurz, nm in (("rsi", "rsi"), ("mom", "momentum"), ("ema", "ema_abstand")):
        g90 = np.nanpercentile(E[kurz + "_s"][r_sa], 90); g90a = np.nanpercentile(E[kurz + "_s24"][r_sa], 90)
        oben = E[kurz + "_s"][ev] >= g90
        z1 = []
        for lab, s in (("Anstieg <0", anst[ev] < 0), ("0-1", (anst[ev] >= 0) & (anst[ev] < 1)),
                       ("1-2", (anst[ev] >= 1) & (anst[ev] < 2)), (">=2", anst[ev] >= 2)):
            ix = oben & s
            z1.append("%s %+.3f (%d)" % (lab, y[ix].mean() - pA[ix].mean(), ix.sum()) if ix.sum() >= 100
                      else "%s -" % lab)
        oben24 = E[kurz + "_s24"][ev] >= g90a
        z2 = []
        for lab, s in (("beide oben", oben & oben24), ("nur jetzt", oben & ~oben24),
                       ("nur 24 h", ~oben & oben24), ("keiner", ~oben & ~oben24)):
            z2.append("%s %+.3f (%d)" % (lab, y[s].mean() - pA[s].mean(), s.sum()) if s.sum() >= 100
                      else "%s -" % lab)
        print("     W1 %-11s oben x Anstieg: %s" % (nm, " · ".join(z1)))
        print("     W2 %-11s jetzt x 24 h:   %s" % (nm, " · ".join(z2)))

    # C8 K5-Tabelle
    print()
    print("=" * 120)
    print("K5-TABELLE (C8: Ausgabe, KEINE Schwelle) - rollierend, Modell A, alle Gitteranker mit Normal")
    alle = np.flatnonzero(np.isfinite(ZA))
    pal = expit(ZA[alle])
    nmon = len(np.unique(MON[alle])); nasset = len(np.unique(SYM[alle]))
    print("  %-10s %8s %14s %9s %9s %s" % ("Schwelle", "Anker", "je Asset/Monat", "q beob", "ohne Tr.",
                                           "q je Jahr 2024 / 2025 / 2026"))
    for nm, sel in ([("q >= %.2f" % s, pal >= s) for s in (0.52, 0.55, 0.58, 0.60, 0.65)] +
                    [("q <= %.2f" % s, pal <= s) for s in (0.45, 0.42, 0.40)]):
        ix = alle[sel]
        ih = ix[HIT[ix]]
        qj = [A24[ih[JAHR[ih] == j]].mean() if (JAHR[ih] == j).sum() >= 50 else np.nan for j in (2024, 2025, 2026)]
        print("  %-10s %8d %14.2f %9.4f %8.1f%% %s" % (
            nm, len(ix), len(ix) / max(nmon * nasset, 1), A24[ih].mean() if len(ih) else np.nan,
            100 * (1 - HIT[ix].mean()) if len(ix) else np.nan,
            " / ".join("%.4f" % x if np.isfinite(x) else "-" for x in qj)))
    print("  Grundrate (alle Anker mit Treffer): %.4f · Anker gesamt %d · Monate %d · Assets %d" % (
        A24[alle[HIT[alle]]].mean(), len(alle), nmon, nasset))
    print()
    print("  ⚠️ Gebuehren und Finanzierung sind nicht eingerechnet (Regel 2).")
    print("SCHLUSS: vollstaendig")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
