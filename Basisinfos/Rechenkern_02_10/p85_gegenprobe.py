"""P85 GEGENPROBE Voranalyse Vorsprungs-Atlas (25.10.2026): zweiter Weg zu Abdeckung, Aufloesung und erwarteter Groesse.

    python -X utf8 Basisinfos/Rechenkern_02_10/p85_gegenprobe.py

G1  Abdeckung ueber pandas.merge_asof (je Symbol, Stichtag + 1 Tag <= Einstieg) statt searchsorted - gleiche Zahl mit Wert und gleiche
    Fuenftel-Verteilung wie p85 (aus p85_atlas_voranalyse.txt gelesen)
G2  Aufloesung als FORMEL: cluster-robuster Standardfehler (Cluster = Coin x Stichtag) der Differenz 'oberes Fuenftel - Rest' bei
    zufaelliger Einteilung, MDE = 2,5 x SE, je Handel - muss in der Groessenordnung der Simulation liegen (Faktor 0,67-1,5)
G3  die angesetzte Dosis +12,1 Pp (oberes Fuenftel E3, ohne F9, 12 M) steht so in b4_vormessung.txt (Teil 0)
"""
import os
import re
import sys

import numpy as np
import pandas as pd

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HIER)
os.chdir(os.path.dirname(os.path.dirname(HIER)))
sys.stdout.reconfigure(encoding="utf-8")
import p85_atlas_voranalyse as P  # noqa: E402


def main():
    txt = open(os.path.join(HIER, "p85_atlas_voranalyse.txt"), encoding="utf-8").read()
    T = P.wert_tabelle(1)
    E = pd.read_csv(os.path.join("data", "_vergleich", "kern48jbz_einstiege_bestand.csv"), sep=";")
    E["zeit"] = P.B0 + pd.to_timedelta(E.stunde, unit="h")
    T2 = T.rename(columns={"sym": "symbol"}).copy()
    T2["ab"] = T2.t + pd.Timedelta(days=1)
    a = pd.merge_asof(E.sort_values("zeit"), T2.sort_values("ab"), left_on="zeit", right_on="ab", by="symbol", direction="backward")
    a = a[a.t.notna()]
    # nur der juengste Stichtag zaehlt: hat das Symbol am juengsten Stichtag vor dem Einstieg keinen Eintrag, gilt "ohne Wert"
    tage = np.sort(T.t.unique())
    juengst = pd.Series(tage[np.searchsorted(tage + np.timedelta64(1, "D"), a.zeit.values, side="right") - 1], index=a.index)
    a = a[a.t.values == juengst.values]
    mit = int(a.p.notna().sum())
    f = np.ceil(a.p * 5).clip(1, 5)
    vert = " / ".join(str(int((f == q).sum())) for q in (1, 2, 3, 4, 5))
    m = re.search(r"V2 Referenz 2024-26: \d+ Einstiege · mit Wert (\d+) .*?Fuenftel 1-5: ([\d / ]+) ·", txt)
    ok1 = m and int(m.group(1)) == mit and m.group(2).strip() == vert
    print("G1 Abdeckung merge_asof: mit Wert %d, Fuenftel %s (p85: %s / %s) -> %s" % (mit, vert, m.group(1) if m else "?", m.group(2).strip() if m else "?",
                                                                                    "ok" if ok1 else "NICHT OK"))
    K = P.Kurse()
    x = P.einstiege(os.path.join("data", "_vergleich", "kern48jbz_einstiege_bestand.csv"), T, K)
    x = x[x.f.notna() & x["z_24 h"].notna()].reset_index(drop=True)
    z = x["z_24 h"].to_numpy()
    anteil = (x.f == 5).mean()
    g = x.groupby(["symbol", "t"]).ngroup().to_numpy()
    G = g.max() + 1
    # Var(mean_oben - mean_alle) unter Zufallseinteilung je Cluster: (1 - anteil) * Var(mean_oben); Var(mean_oben) ~ sum_c n_c^2 var_c... ueber Clustersummen
    s_c = np.bincount(g, weights=z - z.mean(), minlength=G)
    n_c = np.bincount(g, minlength=G)
    n_oben = anteil * len(z)
    var_mean_oben = anteil * (s_c ** 2).sum() / n_oben ** 2
    se = np.sqrt((1 - anteil) ** 2 * var_mean_oben + 0.0)
    mde_formel = 2.5 * se
    m2 = re.search(r"V3 Referenz 2024-26 24 h: .*?je Handel ([\d.]+) Pp", txt)
    sim = float(m2.group(1)) / 100
    q = mde_formel / sim
    ok2 = 0.67 <= q <= 1.5
    print("G2 MDE 24 h je Handel: Formel (Cluster Coin x Stichtag, %d Cluster) %.2f Pp gegen Simulation %.2f Pp, Verhaeltnis %.2f -> %s" % (
        G, 100 * mde_formel, 100 * sim, q, "ok" if ok2 else "NICHT OK"))
    b4 = open(os.path.join("Basisinfos", "Spot_Voranalyse_04_10", "b4_vormessung.txt"), encoding="utf-8").read()
    m3 = re.search(r"TEIL 0 Dosis E3 ohne F9: ([-+\d. ]+) \(Soll", b4)
    oben = float(m3.group(1).split()[-1]) if m3 else None
    ok3 = oben is not None and abs(oben - 12.1) <= 0.15
    print("G3 Dosis oberes Fuenftel E3 laut b4_vormessung.txt: %s Pp (angesetzt +12,1) -> %s" % (oben, "ok" if ok3 else "NICHT OK"))
    print("ERGEBNIS %d von 3" % sum([bool(ok1), ok2, ok3]))


if __name__ == "__main__":
    main()
