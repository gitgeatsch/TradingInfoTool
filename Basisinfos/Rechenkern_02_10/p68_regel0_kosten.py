"""P68 REGEL0 KOSTEN (23.10.2026, Voranalyse_REGEL0_Kosten_23_10.md, Plan vorab 82a1fe89): Vorpruefung als OBERGRENZE in der Rueckschau.

    python Basisinfos/Rechenkern_02_10/p68_regel0_kosten.py [--taker 0.0005] [--maker 0.0002]

Einstiege: data/_vergleich/kern48jbz_einstiege_<menge>.csv, 2025-01..2026-08, vier Mengen; Kurse wie p64.reihe (Stundenschluss C, Stundentief L).
P-A  Abdeckung durch Kraken-Perps (data/_perp/kraken_instruments_2026-10-23.json, PF_*), Kosten = 2 x Gebuehr + Funding des Einstiegstags
     (Binance-Tagessumme als Stellvertreter, Long zahlt positiv) + Schlupf 0,02 / 0,05 % je Seite.
O1   Haltedauer 4..24 h gegen Bitpanda 0,30 % + 0,03 % je angefangenem 4-h-Block.
O2   Fuenftel der Schwankung (Std der Stundenrenditen der 168 h VOR dem Einstieg) gegen 0,48 %.
O3   Limit-Einstieg Schluss x (1 - x), x = 0,25 / 0,5 / 1 %, gueltig 4 h; Ausgang wie 24 h nach der Einstiegsstunde (gleicher Endzeitpunkt).
Gebuehren-Vorgabe Kraken: wird durch die Recherche A0 belegt; bis dahin Taker 0,05 %, Maker 0,02 % als ANNAHME (im Bericht ausgewiesen).
"""
import json
import os
import sqlite3
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


def arg(name, vorgabe):
    return float(sys.argv[sys.argv.index(name) + 1]) if name in sys.argv else vorgabe


TAKER, MAKER = arg("--taker", 0.0005), arg("--maker", 0.0002)
MENGEN = ("bestand", "unverzerrt_1", "unverzerrt_2", "unverzerrt_3")
BP_SCHLIESS, BP_BLOCK = 0.0030, 0.0003
_cache = {}


def kraken_basen():
    j = json.load(open(os.path.join("data", "_perp", "kraken_instruments_2026-10-23.json")))
    b = {str(i.get("base", "")).upper() for i in j["instruments"] if str(i.get("symbol", "")).startswith("PF_") and i.get("tradeable")}
    return b | ({"BTC"} if "XBT" in b else set())


def funding():
    c = sqlite3.connect("file:data/funding_historie.db?mode=ro", uri=True)
    F = pd.read_sql("SELECT symbol, datum, wert FROM funding", c)
    c.close()
    return {(s, d): w for s, d, w in zip(F.symbol, F.datum, F.wert)}


def einstiege(menge):
    E = pd.read_csv(os.path.join("data", "_vergleich", "kern48jbz_einstiege_%s.csv" % menge), sep=";")
    E = E[E.jahr >= 2025].copy()
    aus = []
    for s, st in zip(E.symbol, E.stunde):
        if s not in _cache:
            _cache[s] = P.reihe(s)
        x = _cache[s]
        z = dict(symbol=s, stunde=int(st))
        if x is not None:
            a, L, C = x
            i = int(st) - a
            if 168 <= i and i + 24 < len(C) and np.isfinite(C[i]) and np.isfinite(C[i + 24]):
                c0 = C[i]
                for h in (4, 8, 12, 16, 20, 24):
                    z["r%d" % h] = C[i + h] / c0 - 1 if np.isfinite(C[i + h]) else np.nan
                lr = np.diff(np.log(C[i - 168:i + 1]))
                z["vola"] = np.nanstd(lr) if np.isfinite(lr).sum() > 100 else np.nan
                tief4 = np.nanmin(L[i + 1:i + 5]) if np.isfinite(L[i + 1:i + 5]).any() else np.nan
                for x_ in (0.0025, 0.005, 0.01):
                    lim = c0 * (1 - x_)
                    z["lim%g" % x_] = (C[i + 24] / lim - 1) if (np.isfinite(tief4) and tief4 <= lim) else np.nan
        aus.append(z)
    D = pd.DataFrame(aus)
    D = D[D.r24.notna()].copy()
    D["tag"] = D.stunde // 24
    D["datum"] = (P.B0 + pd.to_timedelta(D.stunde, unit="h")).dt.strftime("%Y-%m-%d")
    D["jahr"] = D.datum.str[:4]
    return D


def tb(x, tag, saat=1, n=2000):
    g = pd.DataFrame({"x": x, "t": tag}).groupby("t").x.agg(["sum", "count"])
    idx = np.random.default_rng(saat).integers(0, len(g), (n, len(g)))
    m = g["sum"].to_numpy()[idx].sum(1) / g["count"].to_numpy()[idx].sum(1)
    return np.percentile(m, 2.5), np.percentile(m, 97.5)


def main():
    K = kraken_basen()
    FU = funding()
    print("P68 REGEL0 KOSTEN · Einstiege 2025-01..2026-08 · Kraken-Perps (Basen) %d · Kraken-Gebuehr ANNAHME Taker %.3f %% / Maker %.3f %%\n"
          % (len(K), 100 * TAKER, 100 * MAKER))
    for menge in MENGEN:
        D = einstiege(menge)
        print("=== %s: %d Einstiege an %d Tagen · 24 h Rohvorteil %+.3f %%" % (menge, len(D), D.tag.nunique(), 100 * D.r24.mean()))
        # P-A
        A = D[D.symbol.isin(K)].copy()
        A["fund"] = [FU.get((s, d), np.nan) for s, d in zip(A.symbol, A.datum)]
        print("  P-A Abdeckung Kraken: %.1f %% der Einstiege (%d), Rohvorteil dort %+.3f %% · Funding bekannt %.0f %%, Mittel %+.4f %% je Tag"
              % (100 * len(A) / len(D), len(A), 100 * A.r24.mean(), 100 * A.fund.notna().mean(), 100 * A.fund.mean()))
        fu = A.fund.fillna(A.fund.mean())
        for name, geb in (("Taker", TAKER), ("Maker", MAKER)):
            for schl in (0.0002, 0.0005):
                net = A.r24 - 2 * geb - 2 * schl - fu
                lo, hi = tb(net.values, A.tag.values)
                print("      %s + Schlupf %.2f %%: Kosten %.3f %% · netto %+.3f %% [Tagesblock %+.2f; %+.2f] · je Jahr %s"
                      % (name, 100 * schl, 100 * (2 * geb + 2 * schl + fu.mean()), 100 * net.mean(), 100 * lo, 100 * hi,
                         " / ".join("%s %+.3f" % (j, 100 * net[A.jahr == j].mean()) for j in ("2025", "2026"))))
        # O1
        teile = []
        for h in (4, 8, 12, 16, 20, 24):
            kost = BP_SCHLIESS + BP_BLOCK * int(np.ceil(h / 4))
            teile.append("%d h %+.3f (Kosten %.2f, netto %+.3f)" % (h, 100 * D["r%d" % h].mean(), 100 * kost, 100 * (D["r%d" % h].mean() - kost)))
        print("  O1 Haltedauer: " + " · ".join(teile))
        # O2
        V = D[D.vola.notna()].copy()
        V["f"] = pd.qcut(V.vola, 5, labels=False)
        print("  O2 Schwankungs-Fuenftel (1 ruhig .. 5 unruhig), 24 h Rohvorteil / netto 0,48 %%: " + " · ".join(
            "F%d %+.3f / %+.3f (n %d)" % (f + 1, 100 * V[V.f == f].r24.mean(), 100 * (V[V.f == f].r24.mean() - 0.0048), (V.f == f).sum()) for f in range(5)))
        # O3
        teile = []
        for x_ in (0.0025, 0.005, 0.01):
            col = "lim%g" % x_
            g = D[col].notna()
            teile.append("%.2f %%: gefuellt %.0f %%, Rohvorteil %+.3f, netto %+.3f" % (100 * x_, 100 * g.mean(), 100 * D.loc[g, col].mean(),
                                                                                      100 * (D.loc[g, col].mean() - 0.0048)))
        print("  O3 Limit-Einstieg (4 h gueltig): " + " · ".join(teile))
        print()


if __name__ == "__main__":
    main()
