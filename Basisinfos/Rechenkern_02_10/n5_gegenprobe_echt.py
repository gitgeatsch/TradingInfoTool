"""N5 GEGENPROBE am ECHTEN Lauf (15.10.2026) - eigener Rechenweg gegen n5_auswertung: Mehrheit aus den ROHSTIMMEN selbst gezaehlt
(stimme, teil T, gueltig), Trennwert stuetzt - dagegen je Jahr selbst gerechnet. Nur lesend (mode=ro).

    python Basisinfos/Rechenkern_02_10/n5_gegenprobe_echt.py
"""
import os
import sqlite3
import sys

WURZEL = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(WURZEL)
import pandas as pd  # noqa: E402

c = sqlite3.connect("file:data/_n5/n5_ablage.db?mode=ro", uri=True)
st = pd.read_sql("SELECT pos, urteil, gueltig FROM stimme WHERE teil='T'", c)
c.close()
st = st[st.gueltig == 1]


def mehrheit(g):
    z = g.urteil.value_counts()
    if len(z) > 1 and z.iloc[0] == z.iloc[1]:
        return "uneinig"
    return z.index[0] if z.iloc[0] >= 3 else "uneinig"


m = st.groupby("pos").apply(mehrheit)
d = pd.read_csv("data/_n5/n5_bericht_anker.csv", sep=";").set_index("pos")
eig = m.map({"stuetzt": 1, "spricht_dagegen": -1, "neutral": 0, "uneinig": 0}).reindex(d.index)
gleich = int((eig == d.lab).sum())
print("Mehrheit selbst gezaehlt: %s · gleich dem Bericht: %d von %d" % (m.value_counts().to_dict(), gleich, len(d)))
for j in (2025, 2026):
    x = d[d.jahr == j]
    e = eig[x.index]
    print("  %d: stuetzt %d, dagegen %d · Unterschied stuetzt - dagegen %+.2f Pp" % (j, (e == 1).sum(), (e == -1).sum(),
                                                                                100 * (x.spot[e == 1].mean() - x.spot[e == -1].mean())))
sys.exit(0 if gleich == len(d) else 1)
