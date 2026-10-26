"""P95 MESSPLAN V-1 (Voranalyse_REGEL0_Reife_Vola_26_10.md §4, vorab 857c9b9e): Positionsgroesse nach ATR gegen festen Positionswert.

    python -X utf8 Basisinfos/Rechenkern_02_10/p95_v1_groesse_atr.py

G0 Gewicht 1 · G1 Gewicht c/ATR (c = Median der ATR der Einstiege der vorigen 90 T, kausal), gekappt [0,5; 2], auf gleiche Summe normiert.
Ertrag 24 h vor Kosten aus den Stundenkursen data/_hist, ATR nach Betriebsformel (regel0_rechnung.E2._atr). Konto = Summe der Tages-P&L.
(i) groesster Rueckgang, (ii) Schwankung der Tages-P&L (Fassung 1c; Mittel nur Auskunft); Nullwelt: G1-Gewichte je Kalendermonat vertauscht (1.000).
SELBSTTEST vor dem ersten Blick (Fehlalarm <= 5 %, Pflanzung lambda 0,5/1/2, Soll >= 80 % bei 1) - Fassung 1b: gemeinsamer Tagesschock. Gegenprobe eigene Schleife. Nur lesend.
"""
import os
import sqlite3
import sys

import numpy as np
import pandas as pd

HIER = os.path.dirname(os.path.abspath(__file__))
WURZEL = os.path.dirname(os.path.dirname(HIER))
sys.path.insert(0, WURZEL)
os.chdir(WURZEL)
sys.stdout.reconfigure(encoding="utf-8")
import warnings  # noqa: E402

warnings.filterwarnings("ignore", category=RuntimeWarning)
import messnorm  # noqa: E402
from agent import regel0_rechnung as R0  # noqa: E402

B0 = pd.Timestamp("2020-01-01")
MENGEN = {"Referenz": os.path.join("data", "_vergleich", "kern48jbz_einstiege_bestand.csv"),
          "Lauf A": os.path.join("data", "_hist", "einstiege_A.csv")}
RNG = np.random.default_rng(95)
LAMBDAS = (0.5, 1.0, 2.0)


def kurse(symbole):
    cons = [sqlite3.connect("file:data/_hist/%s?mode=ro" % d, uri=True) for d in ("stundenkurse.db", "stundenkurse_alle.db")]
    aus = {}
    for s in symbole:
        d = {}
        for c in cons:
            for st, hi, lo, cl in c.execute("SELECT stunde, high, low, close FROM stundenkurse WHERE symbol=? AND stunde >= '2023-09-01'", (s,)):
                d.setdefault(st, (hi, lo, cl))
        if not d:
            continue
        hs = ((pd.to_datetime(list(d.keys())) - B0) / pd.Timedelta(hours=1)).astype(int).to_numpy()
        o = np.argsort(hs)
        hs = hs[o]
        v = np.array(list(d.values()), float)[o]
        atr = R0.E2._atr(v[:, 0], v[:, 1], v[:, 2])               # Betriebsformel auf den vorhandenen Zeilen (wie atr_je_stunde)
        aus[s] = (hs, v[:, 2], atr)
    for c in cons:
        c.close()
    return aus


def handel(pfad):
    e = pd.read_csv(pfad, sep=";")
    e = e[(B0 + pd.to_timedelta(e.stunde, unit="h")) >= pd.Timestamp("2024-01-01")].copy()
    K = kurse(sorted(e.symbol.unique()))
    r, a = np.full(len(e), np.nan), np.full(len(e), np.nan)
    for i, (s, st) in enumerate(zip(e.symbol, e.stunde)):
        k = K.get(s)
        if k is None:
            continue
        hs, cl, atr = k
        j = np.searchsorted(hs, st)
        if j < len(hs) and hs[j] == st:
            j2 = np.searchsorted(hs, st + 24)
            if j2 < len(hs) and hs[j2] == st + 24:
                r[i] = cl[j2] / cl[j] - 1
            a[i] = atr[j]
    e["r"], e["atr"] = r, a
    e = e[np.isfinite(e.r) & np.isfinite(e.atr) & (e.atr > 0)].sort_values("stunde").reset_index(drop=True)
    e["zeit"] = B0 + pd.to_timedelta(e.stunde, unit="h")
    e["tag"] = (e.stunde // 24).astype(int)
    e["monat"] = e.zeit.dt.year * 12 + e.zeit.dt.month
    c = pd.Series(e.atr.to_numpy(), index=e.zeit).rolling("90D", closed="left").median().to_numpy()
    c = np.where(np.isfinite(c), c, np.nan)
    w = np.clip(c / e.atr.to_numpy(), 0.5, 2.0)
    ok = np.isfinite(w)
    e = e[ok].reset_index(drop=True)
    w = w[ok]
    e["w1"] = w * len(w) / w.sum()
    return e


class Pruefstand:
    def __init__(self, e):
        self.tag = pd.factorize(e.tag)[0]
        self.nt = self.tag.max() + 1
        self.gruppen = [np.flatnonzero(e.monat.to_numpy() == m) for m in np.unique(e.monat)]

    def tages(self, w, r):
        return np.bincount(self.tag, weights=w * r, minlength=self.nt)

    @staticmethod
    def kennzahlen(p):
        k = np.cumsum(p)
        return float(np.max(np.maximum.accumulate(k) - k)), float(p.std())     # FASSUNG 1c (§4.2): Schwankung statt Mittel/Schwankung

    def vertausche(self, w, rng):
        v = w.copy()
        for g in self.gruppen:
            v[g] = w[rng.permutation(g)]
        return v

    def urteil(self, w, r, rng, k=1000):
        dd, q = self.kennzahlen(self.tages(w, r))
        nd, nq = np.empty(k), np.empty(k)
        for i in range(k):
            nd[i], nq[i] = self.kennzahlen(self.tages(self.vertausche(w, rng), r))
        return dd, q, float(np.mean(nd > dd)), float(np.mean(nq > q))       # kleiner Rueckgang und kleinere Schwankung sind besser


def bremse(r1, r2):
    return r1 >= 0.95 and r2 >= 0.95


def band(p1, p0, block, rng, n=2000):
    m = len(p1)
    st = rng.integers(0, m, (n, int(np.ceil(m / block))))
    ix = ((st[:, :, None] + np.arange(block)) % m).reshape(n, -1)[:, :m]
    d = p1[ix].mean(1) - p0[ix].mean(1)                                      # Auskunft 1c: Mittel je Tag G1 - G0
    return np.percentile(d, [2.5, 97.5])


def gegenprobe(e, w):
    tage = {}
    for t, x, rr in zip(e.tag, w, e.r):
        tage[t] = tage.get(t, 0.0) + x * rr
    p = np.array([tage[t] for t in sorted(tage)])
    k, hoch, dd = 0.0, 0.0, 0.0
    for x in p:
        k += x
        hoch = max(hoch, k)
        dd = max(dd, hoch - k)
    return dd, p.std()


def main():
    print("P95 MESSPLAN V-1 · Groesse nach ATR gegen festen Positionswert · Ertrag 24 h vor Kosten (neutral)\n")
    daten = {name: handel(p) for name, p in MENGEN.items()}
    block = messnorm._block(1)
    print("SELBSTTEST Fassung 1c vor dem ersten Blick (Fehlalarm 200 Nullwelt-Ziehungen statt G1; Pflanzung r' = r + lambda * ATR * m_Tag, je 100):")
    ok_alle = True
    for name, e in daten.items():
        P = Pruefstand(e)
        w1, r = e.w1.to_numpy(), e.r.to_numpy()
        fa = np.mean([bremse(*P.urteil(P.vertausche(w1, RNG), r, RNG, 200)[2:]) for _ in range(200)])
        fund = {}
        for lam in LAMBDAS:
            # FASSUNG 1b (§4.1): EIN gemeinsamer Schock je Tag, Staerke proportional zur ATR (Fassung 1 zog je Handel - wegdiversifiziert)
            fund[lam] = np.mean([bremse(*P.urteil(w1, r + lam * e.atr.to_numpy() * RNG.standard_normal(P.nt)[P.tag], RNG, 200)[2:])
                                 for _ in range(100)])
        ok = fa <= 0.05 and fund[1.0] >= 0.8
        ok_alle &= ok
        print("  %-8s %5d Handel an %d Tagen (%.0f Bloecke) · Fehlalarm %.1f %% · Fund %s -> %s" % (
            name, len(e), P.nt, P.nt / block, 100 * fa, " · ".join("lambda %.1f %.0f %%" % (l, 100 * f) for l, f in fund.items()),
            "ok" if ok else "NICHT BESTANDEN"))
    if not ok_alle:
        print("\nSELBSTTEST NICHT BESTANDEN - echtes Ergebnis wird nicht angesehen (Plan §4).")
        return 1
    print("  -> bestanden\n")
    urteile = {}
    for name, e in daten.items():
        P = Pruefstand(e)
        r, w1 = e.r.to_numpy(), e.w1.to_numpy()
        w0 = np.ones(len(e))
        p0, p1 = P.tages(w0, r), P.tages(w1, r)
        dd0, q0 = P.kennzahlen(p0)
        dd1, q1, rg1, rg2 = P.urteil(w1, r, RNG)
        lo, hi = band(p1, p0, block, RNG)
        lo2, hi2 = band(p1, p0, 2 * block, RNG)
        st = "TRAEGT als Bremse" if bremse(rg1, rg2) else ("TRAEGT NICHT (schadet)" if min(rg1, rg2) <= 0.05 else "NICHT TRENNBAR")
        urteile[name] = st
        eng = 1.0 * len(e) / P.nt
        print("%-8s G0: Rueckgang %.2f · Schwankung %.3f · Mittel je Tag %+.4f | G1: Rueckgang %.2f (Rang %.3f) · Schwankung %.3f (Rang %.3f) · Mittel je Tag %+.4f" % (
            name, dd0, q0, p0.mean(), dd1, rg1, q1, rg2, p1.mean()))
        print("         Auskunft Mittel je Tag G1-G0 %+.4f · Band 15 T [%+.4f; %+.4f] · Band 30 T [%+.4f; %+.4f] -> Urteil %s" % (
            p1.mean() - p0.mean(), lo, hi, lo2, hi2, st))
        for j in (2024, 2025, 2026):
            m = (e.zeit.dt.year == j).to_numpy()
            if m.sum() < 50:
                continue
            Pj = Pruefstand(e[m].reset_index(drop=True))
            a0, b0 = Pj.kennzahlen(Pj.tages(w0[m], r[m]))
            a1, b1 = Pj.kennzahlen(Pj.tages(w1[m], r[m]))
            s0 = np.mean(Pj.tages(w0[m], r[m]) <= -0.03 * eng)
            s1 = np.mean(Pj.tages(w1[m], r[m]) <= -0.03 * eng)
            print("         Auskunft %d: Rueckgang %.2f -> %.2f · Schwankung %.3f -> %.3f · Tage mit Verlust >= 3 %% des Tagesengagements %.1f %% -> %.1f %%" % (
                j, a0, a1, b0, b1, 100 * s0, 100 * s1))
        g = gegenprobe(e, w1)
        print("         Gegenprobe eigene Schleife G1: Rueckgang %.6f / %.6f · Verhaeltnis %.6f / %.6f -> %s" % (
            g[0], dd1, g[1], q1, "gleich" if abs(g[0] - dd1) < 1e-9 and abs(g[1] - q1) < 1e-9 else "UNGLEICH"))
    ges = all(v == "TRAEGT als Bremse" for v in urteile.values())
    print("\nGESAMTURTEIL (Plan §4): %s" % ("TRAEGT als Bremse in beiden Mengen -> Bauvorschlag" if ges else "nicht in beiden Mengen -> fester Positionswert bleibt"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
