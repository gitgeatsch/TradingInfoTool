"""P52 GEGENPROBE Ordnung x Regime (Spot §52.1) - eigener Rechenweg: Schleife je Zelle mit pandas, Regime neu aus den BTC-Kursen.

    python Basisinfos/Spot_Voranalyse_04_10/p52_gegenprobe.py

Vergleicht alle Abstaende (Auswahl x Ziel x Regime) mit p52_messung.txt (Toleranz 0,05 Pp).
"""
import io
import os
import re
import sys

import numpy as np
import pandas as pd

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HIER)
import s1_messung as S1   # noqa: E402


def main():
    D = pd.read_csv(os.path.join("data", "_spot", "b4_vormessung.csv"), sep=";", parse_dates=["t"])
    D = D[D.p9.notna()]
    K, _ = S1.lade()
    b = K["BTC"].ffill()
    reg = {}
    for t in D.t.unique():
        t = pd.Timestamp(t)
        hist = b[:t].dropna()
        reg[t] = {"BTC ueber 200T": hist.iloc[-1] > hist.iloc[-200:].mean(),
                  "BTC 90T steigt": hist.iloc[-1] > b[:t - pd.Timedelta(days=90)].dropna().iloc[-1]}
    werte = []
    for (t, kl), g in D.groupby(["t", "kl"]):
        r = reg[pd.Timestamp(t)]
        regime = ["BTC ueber 200T" if r["BTC ueber 200T"] else "BTC unter 200T",
                  "BTC 90T steigt" if r["BTC 90T steigt"] else "BTC 90T faellt", g.ep.iloc[0]]
        for auswahl, m in (("oben", g.p9 > 0.8), ("unten", g.p9 <= 0.2)):
            if m.sum() == 0:
                continue
            z1 = np.log(g.ende[m].clip(lower=1e-6)).mean() - np.log(g.ende.clip(lower=1e-6)).mean()
            z2 = np.log(g.ende[m].mean()) - np.log(g.ende.mean())
            for rg in regime:
                werte.append((auswahl, "Z1", rg, z1))
                werte.append((auswahl, "Z2", rg, z2))
    W = pd.DataFrame(werte, columns=["a", "z", "r", "v"]).groupby(["a", "z", "r"]).v.mean()
    txt = io.open(os.path.join(HIER, "p52_messung.txt"), encoding="utf-8").read()
    soll = {(m.group(1), m.group(2), m.group(3).strip()): float(m.group(4)) for m in
            re.finditer(r"^\s{2}(oben|unten)\s+(Z\d)\s+(.+?)\s+\d+\s+\|\s+([+-]\d+\.\d) Pp", txt, re.M)}
    gleich = 0
    print("P52 GEGENPROBE · %d Abstaende aus p52_messung.txt\n" % len(soll))
    for k, s in soll.items():
        v = 100 * W.get(k, np.nan)
        ok = abs(v - s) <= 0.05 + 1e-9
        gleich += ok
        print("  %-6s %s %-16s Gegenprobe %+7.2f Pp · Messung %+6.1f · %s" % (k[0], k[1], k[2], v, s, "gleich" if ok else "ABWEICHUNG"))
    print("\n=> %d von %d gleich (Toleranz 0,05 Pp)" % (gleich, len(soll)))


if __name__ == "__main__":
    main()
