"""P11d GEGENPROBE (17.10.2026): alle REGEL0-ERGEBNIS-Zeilen aus dem NB-Export durch ``regel0_meldung_art`` - gegen eine eigene,
unabhaengige Textregel (Stichwoerter). Nur lesend.

    python Basisinfos/Rechenkern_02_10/p11d_gegenprobe.py
"""
import glob
import json
import os
import re
import sys

WURZEL = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, WURZEL)
os.chdir(WURZEL)
import scheduler.background as BG  # noqa: E402

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:  # noqa: BLE001
    pass
QUELLE = r"K:\My Drive\Claude_Austauschordner\Notebook_Analysedaten"
gesehen, je, abw = set(), {"keine": 0, "nachgeholt": 0, "fehler": 0}, []
for f in glob.glob(os.path.join(QUELLE, "*")):
    try:
        txt = open(f, encoding="utf-8", errors="replace").read()
    except OSError:
        continue
    for m in re.finditer(r'REGEL0-ERGEBNIS (\{.*?\})(?:"|$|\n)', txt.replace('\\"', '"')):
        try:
            e = json.loads(m.group(1))
        except ValueError:
            continue
        k = (e.get("jetzt"), e.get("meldung"))
        if k in gesehen:
            continue
        gesehen.add(k)
        a = BG.regel0_meldung_art(e)
        mm = e.get("meldung") or ""
        eigen = "keine" if not mm else ("fehler" if ("veraltet" in mm or "NICHT nachholbar" in mm) else "nachgeholt")
        je[a] += 1
        if a != eigen:
            abw.append((e.get("jetzt"), mm, a, eigen))
print("P11d GEGENPROBE · %d verschiedene REGEL0-Laeufe aus dem NB-Export: %s" % (len(gesehen), je))
for z in sorted({x for x in gesehen if x[1]}):
    print("   %s  %s -> %s" % (z[0], z[1][:110], BG.regel0_meldung_art({"jetzt": z[0], "meldung": z[1]})))
print("Abweichungen gegen die eigene Textregel: %d %s" % (len(abw), abw[:5]))
print("%s" % ("GLEICH" if not abw and len(gesehen) > 0 else "ABWEICHUNG"))
sys.exit(0 if not abw and gesehen else 1)
