"""P70 MESSPLAN E-A FASSUNG 1b (Voranalyse_Einstieg_EA_23_10.md §5/§5.1, vorab 4241f1e0; Zielgroesse am gemeinsamen Endpunkt): REGEL0 als Kaufzeitpunkt geplanter Monatskaeufe.

    python Basisinfos/Rechenkern_02_10/p70_ea_kaufzeitpunkt.py

(1) SELBSTTEST (Zufallspfad + Zufallssignale -> ~0, Rang gleichverteilt; Signale an Tiefs -> > 0, Rang >= 0,95) - sonst Abbruch.
(2) Faelle: je Coin (mit REGEL0-Einstiegen in der Menge) und Monat 2024-01..2026-08: geplanter Kauf 1. des Monats 00:00 UTC.
    Kauf zum Schluss der ersten REGEL0-Einstiegsstunde in N Tagen, sonst zum Schluss am Fensterende.
    Kaufvorteil (Fassung 1b) = P_T / P_Kauf - P_T / P_plan mit T = Fensterende + 24 h: Wertunterschied je eingesetztem Euro am gemeinsamen
    Endpunkt (unverzerrt unter einem Zufallspfad; P_plan / P_Kauf - 1 war durch die Konvexitaet verzerrt, Selbsttest §5.1).
(3) Nullwelt: gleiche Zahl Zufallsstunden im selben Fenster, die frueheste zaehlt; 200 Ziehungen.
"""
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.chdir(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import p64_lc_voranalyse as P  # noqa: E402

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:  # noqa: BLE001
    pass
FENSTER = (3, 7, 14)
MENGEN = ("bestand", "unverzerrt_1", "unverzerrt_2", "unverzerrt_3")
UNV = MENGEN[1:]
KERN = ("BTC", "ETH", "SOL")
ZIEH = 200
MONATE = pd.date_range("2024-01-01", "2026-08-01", freq="MS")


# ── (1) Selbsttest ──────────────────────────────────────────────────────────────────────────────────────────────────────────
def auswertung(C, signale, fenster_h, rng):
    """C: Kurse (Faelle x Stunden, Fallbeginn = Index 0), signale: Liste je Fall (Stundenindizes). -> echt-Mittel, Null-Mittel je Ziehung"""
    echt, null = [], np.zeros(ZIEH)
    for c, s in zip(C, signale):
        s = [x for x in s if x < fenster_h]
        pt = c[fenster_h + 24]
        kauf = c[s[0]] if s else c[fenster_h]
        echt.append(pt / kauf - pt / c[0])
        if s:
            z = rng.integers(0, fenster_h, (ZIEH, len(s))).min(axis=1)
            null += pt / c[z] - pt / c[0]
        else:
            null += pt / c[fenster_h] - pt / c[0]
    return np.mean(echt), null / len(C)


def selbsttest():
    rng = np.random.default_rng(23)
    n, fh = 3000, 7 * 24
    z = rng.standard_t(4, (n, fh + 25)) / np.sqrt(2) * 0.006
    C = np.cumprod(1 + z, axis=1)
    raenge = []
    for k in range(5):
        sig = [sorted(rng.integers(0, fh, rng.poisson(1.0)).tolist()) for _ in range(n)]
        e, nw = auswertung(C, sig, fh, np.random.default_rng(100 + k))
        raenge.append(float(np.mean(nw < e)))
    e0, _ = auswertung(C, [sorted(rng.integers(0, fh, rng.poisson(1.0)).tolist()) for _ in range(n)], fh, np.random.default_rng(7))
    sig_tief = [[int(np.argmin(c[:fh]))] for c in C]
    ep, nwp = auswertung(C, sig_tief, fh, np.random.default_rng(8))
    rp = float(np.mean(nwp < ep))
    ok = abs(e0) < 0.002 and all(0.02 < r < 0.98 for r in raenge) and ep > 0 and rp >= 0.95
    print("SELBSTTEST: Zufallssignale Kaufvorteil %+.3f %%, Raenge %s · Signale an Tiefs %+.3f %%, Rang %.2f -> %s\n"
          % (100 * e0, " / ".join("%.2f" % r for r in raenge), 100 * ep, rp, "BESTANDEN" if ok else "NICHT BESTANDEN"))
    return ok


# ── (2)/(3) Messung ─────────────────────────────────────────────────────────────────────────────────────────────────────────
_r = {}


def reihe(s):
    if s not in _r:
        _r[s] = P.reihe(s)
    return _r[s]


def faelle(menge, N):
    E = pd.read_csv(os.path.join("data", "_vergleich", "kern48jbz_einstiege_%s.csv" % menge), sep=";")
    sig = E.groupby("symbol").stunde.apply(lambda x: np.sort(x.to_numpy()))
    fh = N * 24
    out = []
    for s, st in sig.items():
        x = reihe(s)
        if x is None:
            continue
        a, L, C = x
        for m in MONATE:
            h0 = int((m - P.B0) / pd.Timedelta(hours=1)) - a
            if h0 < 0 or h0 + fh + 30 >= len(C):
                continue
            c = C[h0:h0 + fh + 30]
            if not np.isfinite(c[[0, fh, fh + 24]]).all():
                continue
            w = st[(st >= h0 + a) & (st < h0 + a + fh)] - (h0 + a)
            w = [int(i) for i in w if np.isfinite(c[int(i)])]
            lo = L[h0:h0 + fh + 30]
            out.append((s, m.year, m, c, w, lo))
    return out


def kennzahl(F, N, saat):
    fh = N * 24
    rng = np.random.default_rng(saat)
    echt, null = [], np.zeros(ZIEH)
    for s, j, m, c, w, lo in F:
        pt = c[fh + 24]
        kauf = c[w[0]] if w else c[fh]
        echt.append(pt / kauf - pt / c[0])
        if w:
            gueltig = np.flatnonzero(np.isfinite(c[:fh]))
            z = gueltig[rng.integers(0, len(gueltig), (ZIEH, len(w)))].min(axis=1)
            null += pt / c[z] - pt / c[0]
        else:
            null += pt / c[fh] - pt / c[0]
    e = float(np.mean(echt))
    nw = null / max(len(F), 1)
    return e, float(np.mean(nw < e)), float(nw.mean()), float(np.mean([bool(f[4]) for f in F]))


def limit_variante(F, N):
    fh = N * 24
    r = []
    for s, j, m, c, w, lo in F:
        if w:
            i = w[0]
            lim = c[i] * 0.995
            t = lo[i + 1:i + 5]
            kauf = lim if (np.isfinite(t).any() and np.nanmin(t) <= lim) else c[min(i + 4, len(c) - 1)]
        else:
            kauf = c[fh]
        r.append(c[fh + 24] / kauf - c[fh + 24] / c[0])
    return float(np.nanmean(r))


def regime_btc():
    import sqlite3
    c = sqlite3.connect("file:data/_spot/coinmetrics.db?mode=ro", uri=True)
    p = pd.read_sql("SELECT tag, PriceUSD FROM tag WHERE asset='btc' AND PriceUSD IS NOT NULL", c, parse_dates=["tag"]).set_index("tag").PriceUSD
    c.close()
    p = p["2023-01-01":]
    lab = pd.Series("auf", index=p.index)
    rich, ext_t, ext_p = "auf", p.index[0], p.iloc[0]
    wende = []
    for t, v in p.items():
        if rich == "auf":
            if v > ext_p:
                ext_t, ext_p = t, v
            elif v <= ext_p * 0.80:
                wende.append((ext_t, "ab"))
                rich, ext_t, ext_p = "ab", t, v
        else:
            if v < ext_p:
                ext_t, ext_p = t, v
            elif v >= ext_p * 1.25:
                wende.append((ext_t, "auf"))
                rich, ext_t, ext_p = "auf", t, v
    aktuell = "auf"
    for t in p.index:
        for wt, r in wende:
            if t == wt:
                aktuell = r
        lab[t] = aktuell
    return lab


def main():
    print("P70 E-A KAUFZEITPUNKT · geplante Kaeufe am Monatsersten 2024-01..2026-08 · Fenster %s Tage\n" % (FENSTER,))
    if not selbsttest():
        print("Selbsttest nicht bestanden - es wird NICHT gemessen (§5).")
        return
    FF = {(m, N): faelle(m, N) for m in MENGEN for N in FENSTER}
    ges = {N: np.mean([kennzahl([f for f in FF[(m, N)] if f[1] == 2024], N, 1)[0] for m in MENGEN]) for N in FENSTER}
    wahl = max(ges, key=ges.get)
    print("WAHL 2024 (alle Coins, Mittel der vier Mengen): %s -> gewaehlt N = %d Tage\n"
          % (" · ".join("%d T %+.3f %%" % (N, 100 * v) for N, v in ges.items()), wahl))
    traegt = True
    for j in (2025, 2026):
        for m in MENGEN:
            F = [f for f in FF[(m, wahl)] if f[1] == j and f[0] not in KERN]
            e, rang, nwm, anteil = kennzahl(F, wahl, saat=hash((m, j)) % 2 ** 32)
            if m in UNV:
                traegt &= e > 0 and rang >= 0.90
            print("  %d %-13s Altcoins: %5d Faelle · mit Signal %.0f %% · Kaufvorteil %+.3f %% · Nullwelt %+.3f %% · Rang %.2f · Limit-Variante %+.3f %%"
                  % (j, m, len(F), 100 * anteil, 100 * e, 100 * nwm, rang, 100 * limit_variante(F, wahl)))
        F = [f for m in MENGEN for f in FF[(m, wahl)] if f[1] == j and f[0] in KERN]
        e, rang, nwm, anteil = kennzahl(F, wahl, saat=j)
        kern_ok = e > 0 and rang >= 0.90
        traegt &= kern_ok
        print("  %d KERN (BTC/ETH/SOL, vier Mengen gemeinsam): %d Faelle · mit Signal %.0f %% · Kaufvorteil %+.3f %% · Nullwelt %+.3f %% · Rang %.2f\n"
              % (j, len(F), 100 * anteil, 100 * e, 100 * nwm, rang))
    print("URTEIL nach §5: %s\n" % ("TRAEGT" if traegt else "TRAEGT NICHT"))
    lab = regime_btc()
    print("Auskunft je Regime (BTC-Zickzack -20 %/+25 %, unverzerrt_1, alle Coins, N gewaehlt):")
    F = FF[("unverzerrt_1", wahl)]
    for r in ("auf", "ab"):
        Fr = [f for f in F if lab.get(f[2], "auf") == r]
        if Fr:
            e, rang, nwm, _ = kennzahl(Fr, wahl, saat=5)
            print("  %-3s %5d Faelle · Kaufvorteil %+.3f %% · Nullwelt %+.3f %% · Rang %.2f" % (r, len(Fr), 100 * e, 100 * nwm, rang))


if __name__ == "__main__":
    main()
