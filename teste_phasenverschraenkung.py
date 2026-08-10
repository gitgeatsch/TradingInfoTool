"""Selbsttest fuer die Phasenverschraenkung - mit Gegenkontrollen.

DER FALL (09.08. abends, echter Lauf). Die Wirkungsmessung war auf 60 Anker
ueber drei Marktphasen geplant und brach nach 25 ab. Die Stichprobe enthielt:

    BULLE 17, SEITWAERTS 8, BAER 0

Ausgerechnet die Baerenphase - die einzige, in der die Produktion tatsaechlich
laeuft (siehe Memory project_regime_immer_baer_kein_vergleich) - fehlte
vollstaendig. Ursache: die Anker wurden Phase fuer Phase aneinandergehaengt und
dann nach DATUM sortiert. Die Baerenphase ist die juengste, ihre Anker standen
also am Ende. Jede Kuerzung schnitt genau sie ab.

Folgefehler aus derselben Wurzel: in Bullen- und Seitwaertsphasen waehlte der
Grundlinienarm 25 von 25 mal LONG. Ohne SHORT in der Grundlinie gibt es keine
gepaarte SHORT-Zelle - die Kontrollbedingung der Messregel war nicht pruefbar.

Der Test prueft die Eigenschaft, auf die es ankommt: JEDER ANFANG der Liste
muss phasenausgewogen sein, nicht nur die vollstaendige Liste. Und er prueft
gegen, dass die ALTE Sortierung daran scheitert - sonst wuerde er nichts
zeigen.

    python teste_phasenverschraenkung.py
"""
from __future__ import annotations

import sys
from collections import Counter, namedtuple

from messe_umbau_wirkung import verschraenke_phasen

_ok, _fehler = 0, []


def pruefe(name, bedingung, detail=""):
    global _ok
    if bedingung:
        _ok += 1
        print(f"  [ok]     {name}" + (f"   {detail}" if detail else ""))
    else:
        _fehler.append(name)
        print(f"  [FEHLER] {name}   {detail}")


Kerze = namedtuple("Kerze", "date")
PHASEN = ("BULLE", "SEITWAERTS", "BAER")
LABEL = {p: p[0] for p in PHASEN}

# Zwoelf Symbole mit je 90 Tagen. Die Phasen liegen NACHEINANDER in der Zeit,
# genau wie in echt: Bulle frueh, Baer zuletzt. Das ist die Konstellation, in
# der die alte Sortierung versagt.
SYMBOLE = [f"S{i}" for i in range(1, 13)]
REIHEN = {s: [Kerze(f"2025-{1 + t // 30:02d}-{1 + t % 30:02d}") for t in range(90)]
          for s in SYMBOLE}
FENSTER = {"BULLE": range(0, 30), "SEITWAERTS": range(30, 60),
           "BAER": range(60, 90)}


def je_phase(n_je_phase=20):
    """20 Anker je Phase, gleichmaessig ueber die Symbole verteilt."""
    aus = {}
    for phase in PHASEN:
        idx = list(FENSTER[phase])
        aus[phase] = [(SYMBOLE[k % len(SYMBOLE)], idx[k % len(idx)])
                      for k in range(n_je_phase)]
    return aus


def alte_fassung(jp, hoechstens):
    """Die Fassung von vor dem 09.08. - zum Vergleich, nicht zum Benutzen."""
    anker = [(p, LABEL[p], s, i) for p in PHASEN for s, i in jp[p]]
    anker.sort(key=lambda x: (REIHEN[x[2]][x[3]].date, x[2]))
    if len(anker) > hoechstens:
        anker = anker[::max(1, len(anker) // hoechstens)][:hoechstens]
    return anker


def unwucht(anker):
    """Groesster Abstand zwischen der haeufigsten und der seltensten Phase."""
    z = Counter(a[0] for a in anker)
    return max(z.get(p, 0) for p in PHASEN) - min(z.get(p, 0) for p in PHASEN)


print("A  JEDER Anfang der Liste ist phasenausgewogen - nicht nur das Ganze")

anker = verschraenke_phasen(je_phase(), PHASEN, LABEL, REIHEN, 60)
schlimmste = max(range(3, len(anker) + 1), key=lambda k: unwucht(anker[:k]))
pruefe("A1 an KEINER Stelle weicht eine Phase um mehr als 1 ab",
       all(unwucht(anker[:k]) <= 1 for k in range(3, len(anker) + 1)),
       f"schlimmster Praefix {schlimmste}: "
       f"{dict(Counter(a[0] for a in anker[:schlimmste]))}")

# Genau der reale Abbruchpunkt.
pruefe("A2 nach 25 Ankern sind alle drei Phasen vertreten",
       len({a[0] for a in anker[:25]}) == 3,
       str(dict(Counter(a[0] for a in anker[:25]))))

# GEGENKONTROLLE: die ALTE Fassung muss hier scheitern. Taete sie es nicht,
# haette der Test nichts gezeigt und die Reparatur waere unbegruendet.
alt = alte_fassung(je_phase(), 60)
pruefe("A2g Gegenkontrolle: die alte Fassung verliert eine Phase komplett",
       len({a[0] for a in alt[:25]}) < 3,
       str(dict(Counter(a[0] for a in alt[:25]))))
pruefe("A3g Gegenkontrolle: und zwar die BAERENPHASE - die juengste",
       Counter(a[0] for a in alt[:25])["BAER"] == 0,
       str(dict(Counter(a[0] for a in alt[:25]))))

print("\nB  Obergrenze und Vollstaendigkeit")

pruefe("B1 nie mehr als gefordert",
       len(verschraenke_phasen(je_phase(), PHASEN, LABEL, REIHEN, 17)) == 17)
pruefe("B2 mehr gefordert als vorhanden: alles, was da ist, ohne Endlosschleife",
       len(verschraenke_phasen(je_phase(5), PHASEN, LABEL, REIHEN, 999)) == 15)
pruefe("B3 Null gefordert ergibt nichts",
       verschraenke_phasen(je_phase(), PHASEN, LABEL, REIHEN, 0) == [])

print("\nC  Ungleich grosse Phasen")

# Die Baerenphase hat nur 3 Anker, die anderen 20. Reihum muss sie zuerst
# ausgehen, ohne dass die Liste abbricht - sonst verliert man den Rest.
schief = je_phase()
schief["BAER"] = schief["BAER"][:3]
a = verschraenke_phasen(schief, PHASEN, LABEL, REIHEN, 40)
z = Counter(x[0] for x in a)
pruefe("C1 die kleine Phase geht aus, die anderen laufen weiter",
       z["BAER"] == 3 and len(a) == 40, str(dict(z)))
pruefe("C1g Gegenkontrolle: die knappe Phase ist trotzdem GANZ vorne dabei",
       Counter(x[0] for x in a[:9])["BAER"] == 3,
       str(dict(Counter(x[0] for x in a[:9]))))

leer = je_phase()
leer["BAER"] = []
pruefe("C2 eine vollstaendig leere Phase bricht nichts",
       len(verschraenke_phasen(leer, PHASEN, LABEL, REIHEN, 40)) == 40)

print("\nD  Innerhalb einer Phase bleibt die Zeitordnung")

a = verschraenke_phasen(je_phase(), PHASEN, LABEL, REIHEN, 60)
for phase in PHASEN:
    daten = [REIHEN[x[2]][x[3]].date for x in a if x[0] == phase]
    pruefe(f"D-{phase} aufsteigend nach Datum", daten == sorted(daten),
           f"{len(daten)} Anker")

print("\nE  Aufbau der Eintraege unveraendert")

x = verschraenke_phasen(je_phase(), PHASEN, LABEL, REIHEN, 3)[0]
pruefe("E1 (phase, label, symbol, index) wie bisher",
       len(x) == 4 and x[0] in PHASEN and x[1] == LABEL[x[0]]
       and x[2] in SYMBOLE and isinstance(x[3], int), str(x))

print("\n" + "=" * 70)
print(f"{_ok} Pruefungen bestanden, {len(_fehler)} fehlgeschlagen")
for f in _fehler:
    print(f"   FEHLER: {f}")
sys.exit(1 if _fehler else 0)
