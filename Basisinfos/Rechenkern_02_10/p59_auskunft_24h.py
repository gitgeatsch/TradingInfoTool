"""P59 AUSKUNFT (nachtraeglich, NICHT im Messplan - nur Einordnung): Wie gross ist der Termin-Ausschlag gemessen am 24-h-Fenster?
BTC |log-Rendite| ueber 24 h ab 1 h vor Termin gegen dieselbe Uhrzeit an Werktagen ohne Termin (Ersatzpools aus p59). Nur lesend.
    python Basisinfos/Rechenkern_02_10/p59_auskunft_24h.py
"""
import io
import os
import sys
from contextlib import redirect_stdout

import numpy as np

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HIER)
sys.stdout.reconfigure(encoding="utf-8")
_puffer = io.TextIOWrapper(io.BytesIO(), encoding="utf-8")
with redirect_stdout(_puffer):
    import p59_termin_vorpruefung as V  # noqa: E402


def bew(h, n):
    i = h - V.H0
    if i - 1 < 0 or i + n - 1 >= len(V.lc):
        return np.nan
    return abs(V.lc[i + n - 1] - V.lc[i - 1])


print("P59 AUSKUNFT: Termin-Ausschlag 2 h gegen 24 h (BTC, Mittel |log-Rendite|, Ersatz = selbe Uhrzeit ohne Termin)")
hs = [h for a in V.TERM for h in V.TERM[a] if V.H0 < h < V.H1 - 26]
for n in (2, 24):
    e = np.nanmean([bew(h, n) for h in hs])
    o = np.nanmean([bew(x, n) for h in hs for x in V.ersatz(h, 200, np.random.default_rng(h)) if V.H0 < x < V.H1 - 26])
    print("   %2d h  Termin %.2f %% · ohne %.2f %% · Verhaeltnis %.2f" % (n, 100 * e, 100 * o, e / o))
