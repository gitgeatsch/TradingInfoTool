"""Selbsttest fuer pruefe_auswertbarkeit() - mit Gegenkontrollen.

Der wichtigste Test ist der REALFALL: die Daten des Wirkungslaufs vom 09.08.
nach fuenf Ankern. Der Waechter MUSS dort abbrechen - sonst haette er die drei
Stunden nicht gespart, um derentwillen er gebaut wurde.

    python teste_auswertbarkeit.py
"""
from __future__ import annotations

import sys

from pruefe_auswertbarkeit import _hoechstens_noch, pruefe_auswertbarkeit

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

    NACHTRAG 09.08. abends: der Satz "null SHORT ist tatsaechlich nicht
    auswertbar" oben stimmt SO NICHT. Null SHORT nach fuenf Ankern sagt
    ueber sechzig Anker nichts aus - siehe Abschnitt G und
    pruefe_auswertbarkeit._hoechstens_noch().
    """
    aus = {a: [] for a in arme}
    n_long = round(n_anker * long_anteil)
    for i in range(n_anker):
        ri = "LONG" if i < n_long else "SHORT"
        for a in arme:
            aus[a].append(zeile(f"S{i % symbole}", i + 1, ri))
    return aus


print("A  Der Realfall vom 09.08. - der Grund, warum es diese Datei gibt")

# Nach 5 von 36 Ankern, LONG-Anteil ~8 % (nemotron): NULL LONG-Faelle.
#
# KORREKTUR 09.08. abends. Diese Datei behauptete urspruenglich, der Waechter
# haette hier "nach fuenf Ankern" abgebrochen - und ich habe das so berichtet.
# Das war zu stark: bei 8 % sieht man in fuenf Ankern null Faelle, und null
# Treffer in fuenf Versuchen schliessen nichts aus. Der Abbruch beruhte auf
# einem Punktschaetzer, der bei n=0 eine harte Null behauptet (siehe
# Abschnitt G). Nach der Reparatur greift der Schutz beim ZEHNTEN Anker -
# immer noch weit vor den drei Stunden, aber eben nicht beim fuenften.
u = pruefe_auswertbarkeit(lauf(5, 0.08), grundlinie="A1", geplant=36, bisher=5,
                          richtungen_noetig=True)
pruefe("A1 nach 5 Ankern ist noch NICHTS ausgeschlossen - kein Abbruch",
       u.tragfaehig, u.bericht().replace("\n", " | ")[:120])
u = pruefe_auswertbarkeit(lauf(10, 0.08), grundlinie="A1", geplant=36,
                          bisher=10, richtungen_noetig=True)
pruefe("A1b nach 10 Ankern mit 1 LONG-Fall greift der Schutz",
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

print("\nG  Null Beobachtungen sind kein Beweis fuer eine Nullrate")
#
# DER FALL (09.08. abends, echter Lauf): die Wirkungsmessung wurde nach FUENF
# Ankern getoetet, weil noch kein einziges SHORT-Signal aufgetreten war. Der
# Punktschaetzer n * geplant/bisher liefert bei n=0 eine harte Null - obwohl
# null Treffer in fuenf Versuchen gar nichts ausschliessen. Nach der
# Dreierregel liegt die 95%-Obergrenze der Rate bei 3/5, ueber 60 Anker also
# bis zu 36 moegliche Faelle.
#
# Die REGEL war richtig (einen aussichtslosen Lauf toeten), der SCHAETZER
# nicht. Repariert wird der Schaetzer, nicht die Regel.

u = pruefe_auswertbarkeit(lauf(5, 1.0), grundlinie="A1", geplant=60, bisher=5,
                          richtungen_noetig=True)
pruefe("G1 bei 0 von 5 wird NICHT abgebrochen", u.tragfaehig)
pruefe("G2 aber es wird gemeldet, nicht verschwiegen",
       "Noch nicht entschieden" in u.bericht(),
       u.bericht().replace("\n", " | ")[:120])

# GEGENKONTROLLE: irgendwann traegt der Abbruch. 3/30 x 60 = 6 < 8.
pruefe("G2g Gegenkontrolle: bei 0 von 30 WIRD abgebrochen",
       not pruefe_auswertbarkeit(lauf(30, 1.0), grundlinie="A1", geplant=60,
                                 bisher=30, richtungen_noetig=True).tragfaehig)
# Die Kante: 3/22 x 60 = 8 (reicht), 3/23 x 60 = 7 (reicht nicht).
pruefe("G3 Kante 22 Anker: gerade noch moeglich",
       pruefe_auswertbarkeit(lauf(22, 1.0), grundlinie="A1", geplant=60,
                             bisher=22, richtungen_noetig=True).tragfaehig)
pruefe("G3g Gegenkontrolle Kante 23 Anker: nicht mehr moeglich",
       not pruefe_auswertbarkeit(lauf(23, 1.0), grundlinie="A1", geplant=60,
                                 bisher=23, richtungen_noetig=True).tragfaehig)

print("\nH  Der Schaetzer selbst")
pruefe("H1 0 von 5 auf 60 -> bis zu 36 moeglich",
       _hoechstens_noch(0, 5, 60) == 36, str(_hoechstens_noch(0, 5, 60)))
pruefe("H2 0 von 30 auf 60 -> nur noch 6",
       _hoechstens_noch(0, 30, 60) == 6, str(_hoechstens_noch(0, 30, 60)))
# GEGENKONTROLLE: fuer n > 0 darf sich NICHTS geaendert haben - diese Fassung
# ist gegen echte Daten geprueft, und die Reparatur soll sie nicht anfassen.
pruefe("H2g Gegenkontrolle: bei n>0 bleibt es beim Punktschaetzer",
       all(_hoechstens_noch(n, b, g) == int(n * g / b)
           for n, b, g in ((5, 10, 60), (3, 5, 36), (12, 20, 60), (1, 30, 60))))
# GEGENKONTROLLE: die Obergrenze darf die geplante Zahl nie ueberschreiten -
# sonst behauptet der Waechter mehr Faelle, als es ueberhaupt Anker gibt.
pruefe("H3g Gegenkontrolle: nie mehr als geplant",
       _hoechstens_noch(0, 2, 60) == 60 and _hoechstens_noch(0, 1, 36) == 36,
       f"{_hoechstens_noch(0, 2, 60)}, {_hoechstens_noch(0, 1, 36)}")

print("\n" + "=" * 70)
print(f"{_ok} Pruefungen bestanden, {len(_fehler)} fehlgeschlagen")
for f in _fehler:
    print(f"   FEHLER: {f}")
sys.exit(1 if _fehler else 0)
