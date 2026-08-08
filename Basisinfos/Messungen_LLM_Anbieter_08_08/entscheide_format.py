"""Liest schema.log und sagt, welches response_format der Rueckspiel-Lauf
bekommt. Die Regel steht hier und nicht im Kopf, damit sie morgen nachpruefbar
ist statt rekonstruiert werden zu muss.

REGEL: das strikte Schema gewinnt nur, wenn es MEHR gueltige Antworten liefert
UND nicht langsamer ist. Gleichstand geht an `json_object` - das ist der
heutige Produktivzustand, und ohne belegten Vorteil wird nichts umgestellt.
"""
import pathlib
import re
import sys

log = pathlib.Path(__file__).parent / "schema.log"
if not log.exists():
    print("")               # kein Ergebnis -> json_object
    sys.exit(0)

text = log.read_text(encoding="utf-8", errors="replace")
werte = {}
for zeile in text.splitlines():
    m = re.search(r"=> ([AB]) .*?:\s*(\d+)/(\d+) gueltig, Median ([\d.]+)s", zeile)
    if m:
        werte[m.group(1)] = (int(m.group(2)), float(m.group(4)))

if "A" not in werte or "B" not in werte:
    print("")
    sys.exit(0)

(a_ok, a_med), (b_ok, b_med) = werte["A"], werte["B"]
besser = b_ok > a_ok and b_med <= a_med * 1.10
sys.stderr.write(f"A json_object: {a_ok} gueltig, {a_med:.1f}s | "
                 f"B json_schema: {b_ok} gueltig, {b_med:.1f}s -> "
                 f"{'SCHEMA' if besser else 'json_object'}\n")
print("--schema" if besser else "")
