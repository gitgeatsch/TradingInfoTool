"""P18 Teil 2c (Spot §48.6, 13.10.2026) - Umlauf der VORMONATE am NB. Nur lesend.

    python Basisinfos/Spot_Voranalyse_04_10/p18_teil2c.py

Am NB reicht die CoinGecko-Umlaufreihe (umlaufmenge_cg.db, Betriebskopie) nur bis etwa 08.09.2026 zurueck. Die Klasse H braucht den
Marktwert-Rang an t, t-1M und t-2M: fuer den Stichtag 01.10. fehlen am NB beide Vormonate, fuer 01.11. einer; ab 01.12. ist alles da.

Ersatzregel (wie die Messung vor 21.09.2025: Umlauf von HEUTE mal Kurs des Tages, mk_messung.umlauf_stufe): fehlt der Umlauf zu einem
Vormonat, gilt der Umlauf am Stichtag t. Gemessen wird die Wirkung an 2026-08-01 und 2026-09-01 - NB-Lage nachgestellt: CoinGecko-Umlauf
nur ab t-7 T - gegen den vollen Umlauf (Teil 2b). Zum Vergleich: ohne Ersatz (die Vormonate ohne Umlauf).
"""
import os
import sys

import numpy as np
import pandas as pd

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HIER)
sys.argv = ["x", "-"]
import p18_voranalyse as P  # noqa: E402

MK = P.MK
K, U = P.G["K"], P.G["U"]
aus = set(P.G["SONDER"]) | {s for s in K.columns if s not in P.G["UNIV"]}


def nb_lage(t, mit_ersatz):
    ab = t - pd.Timedelta(days=7)

    def u(s, m):
        r = MK.CGH.get(s)
        if r is not None:
            r = r[ab:]
        h = MK._asof(r, m) if r is not None and len(r) else None
        if h is None and mit_ersatz and r is not None and len(r):
            h = MK._asof(r, t)
        return h if h is not None else np.nan
    return u


for t in (pd.Timestamp("2026-08-01"), pd.Timestamp("2026-09-01")):
    voll = P.B4(K, U, aus, P.cgh_nur).fuenftel(t)
    for name, ers in (("NB mit Ersatz (Umlauf von t)", True), ("NB ohne Ersatz", False)):
        z = P.B4(K, U, aus, nb_lage(t, ers)).fuenftel(t)
        m = voll.merge(z, on="sym", suffixes=("_v", "_n"))
        m = m[m.q_v.notna() & m.q_n.notna()]
        h_v, h_n = (voll.kl == "H").sum(), (z.kl == "H").sum()
        print("%s %-30s gemeinsam %d · anderes Fuenftel %d (%.1f %%) · andere Klasse %d · H %d -> %d · unteres Fuenftel verlassen %d / neu %d" % (
            t.date(), name, len(m), (m.q_v != m.q_n).sum(), 100 * (m.q_v != m.q_n).mean(), (m.kl_v != m.kl_n).sum(), h_v, h_n,
            ((m.q_v == 1) & (m.q_n != 1)).sum(), ((m.q_n == 1) & (m.q_v != 1)).sum()))
