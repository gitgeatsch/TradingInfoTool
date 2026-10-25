"""P88 GEGENPROBE Voranalyse L-1/L-2 (25.10.2026): zweiter Weg zu Bestandseinordnung, Aufloesung und Kosten.

    python -X utf8 Basisinfos/Rechenkern_02_10/p88_gegenprobe.py

G1  Rang und Fuenftel der Bestaende am letzten Stichtag ueber einen zweiten Weg: Marktwert (Umlauf x Kurs) selbst sortiert statt rang_mw,
    Fuenftel ueber d4_wirkung.fuenftel statt ceil(p*5) - gleich p88 (aus p88_l1_l2_voranalyse.txt gelesen)
G2  Aufloesung L2 BTC 24 h als Formel: 2,5 x Standardabweichung / Wurzel(n), jeder BTC-Einstieg an einem eigenen Tag (unabhaengig) -
    in der Groessenordnung des Block-Bootstraps (Faktor 0,67-1,5)
G3  Kostenformel 0,30 % + 0,18 % je Tag steht so in Voranalyse_Schritt7_Betrieb_02_10.md §23.68
"""
import os
import re
import sys

import numpy as np
import pandas as pd

HIER = os.path.dirname(os.path.abspath(__file__))
WURZEL = os.path.dirname(os.path.dirname(HIER))
sys.path.insert(0, os.path.join(WURZEL, "Basisinfos", "Spot_Voranalyse_04_10"))
sys.path.insert(0, HIER)
os.chdir(WURZEL)
sys.stdout.reconfigure(encoding="utf-8")
import warnings  # noqa: E402

warnings.filterwarnings("ignore", category=RuntimeWarning)
import d4_wirkung as D4  # noqa: E402
import p85_atlas_voranalyse as P85  # noqa: E402

MK = P85.MK


def main():
    txt = open(os.path.join(HIER, "p88_l1_l2_voranalyse.txt"), encoding="utf-8").read()
    T1 = P85.wert_tabelle(1)
    t = T1.t.max()
    kl = MK.A.klassen(t)[0]
    i = MK.POS[t]
    mw = {s: MK.umlauf(s, t) * MK.K[s].values[i] for s in kl}
    mw = pd.Series({s: v for s, v in mw.items() if v == v and v > 0}).sort_values(ascending=False)
    rang2 = {s: k + 1 for k, s in enumerate(mw.index)}
    L = T1[T1.t == t].set_index("sym")
    ok1, n = True, 0
    for m in re.finditer(r"^    (\S+)\s+Klasse (\S+)\s+Rang (\S+)\s+Fuenftel (\S+)\s+->", txt, flags=re.M):
        s, k, r, f = m.groups()
        if k in ("Kern", "-"):
            continue
        n += 1
        f2 = D4.fuenftel(np.array([L.p[s]]))[0]
        r2 = rang2.get(s)
        gl = (r == "kein Umlauf" and r2 is None) or (r2 is not None and abs(float(r) - r2) < 0.6)
        gl &= str(int(f2)) == f
        if not gl:
            print("   abweichend: %s Rang %s/%s Fuenftel %s/%s" % (s, r, r2, f, f2))
        ok1 &= gl
    print("G1 Bestaende im Universum: %d geprueft (Rang selbst sortiert, Fuenftel ueber d4_wirkung.fuenftel) -> %s" % (n, "ok" if ok1 else "NICHT OK"))
    K = P85.Kurse()
    E = P85.einstiege(os.path.join("data", "_vergleich", "kern48jbz_einstiege_bestand.csv"), T1, K)
    z = E[(E.symbol == "BTC") & (E.zeit.dt.year >= 2024)]["z_24 h"].dropna()
    formel = 2.5 * z.std() / np.sqrt(len(z))
    m = re.search(r"L2 Referenz:.*?\n    BTC\s+\d+ Einstiege an\s+\d+ Tagen · 24 h MDE ([\d.]+) Pp", txt, flags=re.S)
    boot = float(m.group(1)) / 100
    q = formel / boot
    ok2 = 0.67 <= q <= 1.5
    print("G2 BTC 24 h: Formel %.2f Pp (n %d, Tage %d) gegen Block-Bootstrap %.2f Pp, Verhaeltnis %.2f -> %s" % (
        100 * formel, len(z), E[(E.symbol == "BTC") & (E.zeit.dt.year >= 2024)].tag.nunique(), 100 * boot, q, "ok" if ok2 else "NICHT OK"))
    q7 = open(os.path.join("Basisinfos", "Voranalyse_Schritt7_Betrieb_02_10.md"), encoding="utf-8").read()
    ok3 = "0,30 % Gebühr + 0,18 % je Tag Finanzierung" in q7
    print("G3 Kostenformel in §23.68: %s -> %s" % ("gefunden" if ok3 else "nicht gefunden", "ok" if ok3 else "NICHT OK"))
    print("ERGEBNIS %d von 3" % sum([ok1, ok2, ok3]))


if __name__ == "__main__":
    main()
