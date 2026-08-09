"""Selbsttest fuer pruefe_auswertbarkeit() - mit Gegenkontrollen.

Der wichtigste Test ist der REALFALL: die Daten des Wirkungslaufs vom 09.08.
nach fuenf Ankern. Der Waechter MUSS dort abbrechen - sonst haette er die drei
Stunden nicht gespart, um derentwillen er gebaut wurde.

    python teste_auswertbarkeit.py
"""
from __future__ import annotations

import sys

from pruefe_auswertbarkeit import pruefe_auswertbarkeit

_ok, _fehler = 0, []


def pruefe(name, bedingung, detail=""):
    global _ok
    if bedingung:
        _ok += 1
        print(f"  [ok]     {name}" + (f"   {detail}" if detail else ""))
    else:
        _fehler.append(name)
        print(f"  [FEHLER] {name}   {detail}")


def zeile(sym, tag, richtung="SHORT", konf=65.0):
    return {"symbol": sym, "datum": f"2025-01-{tag:02d}", "richtung": richtung,
            "konfidenz": konf}


def lauf(n_anker, long_anteil, arme=("A1", "X"), symbole=10):
    """Kuenstlicher Lauf: n_anker Anker, davon `long_anteil` als LONG.

    Die Mischung muss AUCH BEI WENIGEN ANKERN stimmen - die erste Fassung
    rechnete `i % 10 < anteil*10` und lieferte bei 5 Ankern und 60 % Anteil
    fuenfmal LONG und null SHORT. Der Test schlug dann fehl, obwohl der
    Waechter richtig lag: null SHORT ist tatsaechlich nicht auswertbar.
    Ein Testdatengenerator, der die Eigenschaft nicht herstellt, die er
    behauptet, prueft nichts.
    """
    aus = {a: [] for a in arme}
    n_long = round(n_anker * long_anteil)
    for i in range(n_anker):
        ri = "LONG" if i < n_long else "SHORT"
        for a in arme:
            aus[a].append(zeile(f"S{i % symbole}", i + 1, ri))
    return aus


print("A  Der Realfall vom 09.08. - der Grund, warum es diese Datei gibt")

# Nach 5 von 36 Ankern, LONG-Anteil ~8 % (nemotron): 0 bis 1 LONG-Faelle.
u = pruefe_auswertbarkeit(lauf(5, 0.08), grundlinie="A1", geplant=36, bisher=5,
                          richtungen_noetig=True)
pruefe("A1 bricht nach 5 Ankern ab, weil LONG nie gross genug wird",
       not u.tragfaehig, u.bericht().replace("\n", " | ")[:120])

# GEGENKONTROLLE: derselbe Aufbau mit Geminis LONG-Anteil (~58 %) muss
# DURCHLAUFEN - sonst bricht der Waechter immer ab und ist wertlos.
u = pruefe_auswertbarkeit(lauf(5, 0.6), grundlinie="A1", geplant=36, bisher=5,
                          richtungen_noetig=True)
pruefe("A1g Gegenkontrolle: bei 60 % LONG laeuft er durch",
       u.tragfaehig, u.bericht().replace("\n", " | ")[:120])

print("\nB  Ohne Richtungsbedarf ist derselbe Lauf tragfaehig")
u = pruefe_auswertbarkeit(lauf(5, 0.08), grundlinie="A1", geplant=36, bisher=5,
                          richtungen_noetig=False)
pruefe("B1 wer keine Richtungsaussage braucht, wird nicht gebremst",
       u.tragfaehig)

print("\nC  Die Hochrechnung, nicht der Momentanwert")
# 3 von 36 Ankern, alles SHORT: gepaart 3 - absolut zu wenig, hochgerechnet 36.
u = pruefe_auswertbarkeit(lauf(3, 0.0), grundlinie="A1", geplant=36, bisher=3,
                          richtungen_noetig=False)
pruefe("C1 kleine Zellen am Anfang sind KEIN Abbruchgrund", u.tragfaehig,
       u.bericht().replace("\n", " | ")[:100])
# GEGENKONTROLLE: dieselben 3 Faelle, aber der Lauf ist fast fertig -
# dann ist die Hochrechnung dieselbe Zahl und es reicht nicht.
u = pruefe_auswertbarkeit(lauf(3, 0.0), grundlinie="A1", geplant=4, bisher=3,
                          richtungen_noetig=False)
pruefe("C1g Gegenkontrolle: kurz vor Schluss zaehlt der Istwert",
       not u.tragfaehig, u.bericht().replace("\n", " | ")[:100])

print("\nD  Leere Arme und fehlende Pflichtfelder")
d = lauf(10, 0.5)
d["X"] = []
pruefe("D1 ein leerer Arm bricht sofort ab",
       not pruefe_auswertbarkeit(d, grundlinie="A1", geplant=36,
                                 bisher=10).tragfaehig)
d = lauf(10, 0.5)
for z in d["X"]:
    z["konfidenz"] = None
pruefe("D2 fehlt das Pflichtfeld in der Mehrheit, bricht er ab",
       not pruefe_auswertbarkeit(d, grundlinie="A1", geplant=36, bisher=10,
                                 pflichtfelder=("konfidenz",)).tragfaehig)
# GEGENKONTROLLE: einzelne Luecken sind normal und duerfen nicht abbrechen.
d = lauf(10, 0.5)
d["X"][0]["konfidenz"] = None
pruefe("D2g Gegenkontrolle: eine einzelne Luecke bricht NICHT ab",
       pruefe_auswertbarkeit(d, grundlinie="A1", geplant=36, bisher=10,
                             pflichtfelder=("konfidenz",)).tragfaehig)

print("\nE  Symbolvielfalt zaehlt getrennt von der Fallzahl")
# 36 Faelle, aber nur 2 Symbole - Cluster-Bootstrap traegt das nicht.
u = pruefe_auswertbarkeit(lauf(36, 0.5, symbole=2), grundlinie="A1",
                          geplant=36, bisher=36)
pruefe("E1 viele Faelle aus wenigen Symbolen reichen NICHT",
       not u.tragfaehig, u.bericht().replace("\n", " | ")[:110])
pruefe("E1g Gegenkontrolle: dieselbe Fallzahl aus 10 Symbolen reicht",
       pruefe_auswertbarkeit(lauf(36, 0.5, symbole=10), grundlinie="A1",
                             geplant=36, bisher=36).tragfaehig)

print("\nF  Randfaelle")
pruefe("F1 vor dem ersten Anker kein Urteil",
       pruefe_auswertbarkeit({}, grundlinie="A1", geplant=36,
                             bisher=0).tragfaehig)
pruefe("F2 fehlende Grundlinie bricht ab",
       not pruefe_auswertbarkeit({"X": [zeile("S1", 1)]}, grundlinie="A1",
                                 geplant=36, bisher=5).tragfaehig)

print("\n" + "=" * 70)
print(f"{_ok} Pruefungen bestanden, {len(_fehler)} fehlgeschlagen")
for f in _fehler:
    print(f"   FEHLER: {f}")
sys.exit(1 if _fehler else 0)
