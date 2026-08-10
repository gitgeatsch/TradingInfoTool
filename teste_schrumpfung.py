"""Selbsttest fuer schrumpfe_zu_neutral() - jede Zusicherung mit Gegenkontrolle.

Schrumpfung ist eine Rechnung, die eine unerfreuliche Zahl weicher aussehen
laesst. Genau deshalb muss sie besonders eng gepruefte Grenzen haben: sie darf
NIE ueber den Messwert hinausschiessen, NIE das Vorzeichen drehen, und bei
n=0 muss exakt der neutrale Anker herauskommen - sonst waere sie ein
Beschoenigungsautomat statt einer Kalibrierung.

    python teste_schrumpfung.py
"""
from __future__ import annotations

import sys

from agent.krypto.backward_tracking import PSEUDO_STICHPROBE, schrumpfe_zu_neutral

_ok, _fehler = 0, []


def pruefe(name, bedingung, detail=""):
    global _ok
    if bedingung:
        _ok += 1
        print(f"  [ok]     {name}" + (f"   {detail}" if detail else ""))
    else:
        _fehler.append(name)
        print(f"  [FEHLER] {name}   {detail}")


print("A  Die Randfaelle")

s = schrumpfe_zu_neutral(gemessen=16.0, n=0, neutral=26.7, k=50)
pruefe("A1 n=0 -> EXAKT der neutrale Anker",
       abs(s["gewichtet"] - 26.7) < 1e-9 and s["gewicht"] == 0.0,
       f"{s['gewichtet']} bei Gewicht {s['gewicht']}")

s = schrumpfe_zu_neutral(gemessen=16.0, n=1_000_000, neutral=26.7, k=50)
pruefe("A2 sehr grosses n -> praktisch der Messwert",
       abs(s["gewichtet"] - 16.0) < 0.01, str(s["gewichtet"]))

s = schrumpfe_zu_neutral(gemessen=16.0, n=50, neutral=26.7, k=50)
pruefe("A3 n=k -> exakt die Mitte",
       abs(s["gewichtet"] - (16.0 + 26.7) / 2) < 1e-9 and s["gewicht"] == 0.5,
       str(s["gewichtet"]))

# GEGENKONTROLLE zu A1/A2: die Funktion darf nicht einfach immer dasselbe
# liefern - zwischen n=0 und n=gross MUSS ein Unterschied stehen.
a = schrumpfe_zu_neutral(16.0, 0, 26.7, 50)["gewichtet"]
b = schrumpfe_zu_neutral(16.0, 500, 26.7, 50)["gewichtet"]
pruefe("A3g Gegenkontrolle: n aendert das Ergebnis wirklich",
       abs(a - b) > 5.0, f"n=0 -> {a}, n=500 -> {b}")

print("\nB  Die Grenzen, die sie NIE ueberschreiten darf")

for n in (0, 1, 5, 20, 50, 94, 500):
    s = schrumpfe_zu_neutral(16.0, n, 26.7, 50)
    innen = 16.0 - 1e-9 <= s["gewichtet"] <= 26.7 + 1e-9
    if not innen:
        pruefe(f"B1 n={n}: Ergebnis liegt zwischen Messwert und Anker", False,
               str(s["gewichtet"]))
        break
else:
    pruefe("B1 Ergebnis liegt IMMER zwischen Messwert und Anker "
           "(sieben Stichproben)", True)

# GEGENKONTROLLE: bei einem Messwert UEBER dem Anker muss es genauso gelten -
# sonst prueft B1 nur eine Richtung.
for n in (0, 1, 50, 500):
    s = schrumpfe_zu_neutral(45.0, n, 26.7, 50)
    innen = 26.7 - 1e-9 <= s["gewichtet"] <= 45.0 + 1e-9
    if not innen:
        pruefe("B1g Gegenkontrolle: gilt auch fuer Messwert UEBER dem Anker",
               False, str(s["gewichtet"]))
        break
else:
    pruefe("B1g Gegenkontrolle: gilt auch fuer Messwert UEBER dem Anker", True)

# Ein negativer Erwartungswert darf durch Schrumpfung NIE positiv werden,
# solange der Anker 0 ist. Das ist die wichtigste Grenze ueberhaupt.
schlimmste = min(schrumpfe_zu_neutral(-0.176, n, 0.0, 50)["gewichtet"]
                 for n in (0, 1, 10, 94, 1000))
groesste = max(schrumpfe_zu_neutral(-0.176, n, 0.0, 50)["gewichtet"]
               for n in (0, 1, 10, 94, 1000))
pruefe("B2 negativer Erwartungswert bleibt <= 0 (Anker 0)", groesste <= 1e-9,
       f"groesster Wert {groesste}")
pruefe("B2g Gegenkontrolle: er wird auch nicht schlimmer als gemessen",
       schlimmste >= -0.176 - 1e-9, f"kleinster Wert {schlimmste}")

print("\nC  Wenn es nichts zu schrumpfen gibt")
s = schrumpfe_zu_neutral(26.7, 5, 26.7, 50)
pruefe("C1 Messwert == Anker -> unveraendert, egal bei welchem n",
       abs(s["gewichtet"] - 26.7) < 1e-9)

print("\nD  Ehrlichkeit: die rohe Zahl bleibt sichtbar")
s = schrumpfe_zu_neutral(16.0, 94, 26.7, 50)
pruefe("D1 `roh` traegt den unveraenderten Messwert", s["roh"] == 16.0)
pruefe("D2 `gewicht` wird mitgeliefert",
       abs(s["gewicht"] - 94 / 144) < 0.001, str(s["gewicht"]))
pruefe("D3 `neutral`, `n` und `k` ebenfalls",
       s["neutral"] == 26.7 and s["n"] == 94 and s["k"] == 50)
# GEGENKONTROLLE: ohne `roh` waere die Schrumpfung eine stille Ersetzung -
# genau das, wovor der systemguete-Docstring warnt.
pruefe("D3g Gegenkontrolle: gewichtet und roh sind WIRKLICH verschieden",
       abs(s["gewichtet"] - s["roh"]) > 1.0,
       f"roh {s['roh']}, gewichtet {s['gewichtet']}")

print("\nE  Kaputte Eingaben liefern None, keinen Ersatzwert")
pruefe("E1 fehlender Messwert", schrumpfe_zu_neutral(None, 10, 5.0) is None)
pruefe("E2 fehlender Anker", schrumpfe_zu_neutral(1.0, 10, None) is None)
pruefe("E3 fehlendes n", schrumpfe_zu_neutral(1.0, None, 5.0) is None)
pruefe("E4 negatives n", schrumpfe_zu_neutral(1.0, -1, 5.0) is None)
pruefe("E5 k <= 0 (waere Division durch null bei n=0)",
       schrumpfe_zu_neutral(1.0, 0, 5.0, k=0) is None)

print("\nF  Die Vorgabe fuer k ist begruendet, nicht geraten")
pruefe("F1 PSEUDO_STICHPROBE = 50 (unteres Ende der Literaturempfehlung "
       "50-100 je Setup)", PSEUDO_STICHPROBE == 50, str(PSEUDO_STICHPROBE))

print("\n" + "=" * 68)
print(f"{_ok} Pruefungen bestanden, {len(_fehler)} fehlgeschlagen")
for f in _fehler:
    print(f"   FEHLER: {f}")
sys.exit(1 if _fehler else 0)
