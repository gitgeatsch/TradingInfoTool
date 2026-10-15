"""O53 AUSKUNFT (nachtraeglich, NICHT im Messplan): ordnet das Makro das Risiko OHNE die Fortschreibung - und wie viel davon steckt
schon in der eigenen 30-T-Schwankung? Nur lesend, dieselben Daten und dieselbe N2-Bank wie o53_vorpruefung.py.
    python Basisinfos/Rechenkern_02_10/o53_auskunft_roh.py
"""
import io
import os
import sys
from contextlib import redirect_stdout

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding="utf-8")
with redirect_stdout(io.TextIOWrapper(io.BytesIO(), encoding="utf-8")):
    import o53_vorpruefung as V  # noqa: E402

ab = np.array([t >= V.START for t in V.stich])
roh = {"a": np.where(ab, np.log(V.Z["a"].values), np.nan), "b": np.where(ab, V.Z["b"].values, np.nan),
       "vor": np.where(ab, np.log(V.Z["vor"].values), np.nan)}
print("O53 AUSKUNFT roh (ohne Fortschreibung), ab 2013, N2-Bank - Abstand Rueckenwind - Gegenwind")
for zi, name in (("a", "log Schwankung naechste 30 T"), ("b", "tiefster Stand naechste 30 T"), ("vor", "log Schwankung LETZTE 30 T")):
    for m in V.MERK:
        a, ph, pt, npl, nmi, _ok = V.test(m, roh[zi])
        print("  %-30s %-12s n+ %3d n- %3d · Abstand %+.4f · p hoch %.4f tief %.4f" % (name, m, npl, nmi, a, ph, pt))
