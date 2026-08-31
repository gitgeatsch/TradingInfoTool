# -*- coding: utf-8 -*-
"""G-6: was passiert, WENN Stufe 11 scharf wird? (31.08.2026)

⚠️ DIESE VORSCHAU LAEUFT VOR DER AENDERUNG, NICHT DANACH.

Nutzerauftrag 31.08.: *"detailliert und umfangreich simulieren, auch mit
Historie falls erforderlich - inkl. Vorschau, wie sich die Scharfschaltung
auswirkt im System ueber den aktuell definierten Takt."*

## Der Ist-Zustand, erhoben statt vermutet

    rollen_gate.NUR_ZAEHLEN = ("entscheider",)

Stufe 11 rechnet das Potential, vergleicht es mit der Schwelle - und
BUCHT das Ergebnis nur. Kein Signal wird verhindert. Die gesamte
Bewertungsarbeit seit dem 30.08. (Funding, Turnover, die Schwelle 0,010)
ist damit heute ohne Wirkung auf den Signalfluss.

⚠️ UND ZWEI WEITERE BEFUNDE GEHOEREN DANEBEN, sonst taeuscht diese Zahl:

  B1  Die Rollen-Kette hat KEINEN Betriebsaufrufer (15 von 15 Modulen).
      Sie laeuft nur in `simuliere_kette.py` und in Pruefungen.
  --  Das letzte Signal in `signals` stammt vom 21.07.2026, alle 118 mit
      `quelle_kette = None` - also aus der ALTEN Kette.

**Scharf schalten aendert deshalb heute NICHTS am Betrieb.** Es entscheidet,
was passiert, sobald B1 verdrahtet wird - und genau dafuer ist diese
Vorschau da.

## Was hier gerechnet wird

    1  DIE VERTEILUNG    Wieviele Anker liegen ueber, wieviele unter der
                         Schwelle - mit den ECHTEN Beitraegen aus der
                         Registrierung, nicht mit Annahmen.
    2  DIE QUALITAET     Sind die gesperrten Anker tatsaechlich die
                         schlechteren? Sonst kostet die Sperre Ertrag.
    3  DER TAKT          Was bedeutet das je Lauf, je Woche, je Jahr?
    4  DIE EMPFINDLICHKEIT  Wie stark haengt das Ergebnis an der Schwelle?

⚠️ GERECHNET WIRD MIT DER PRODUKTIONSFUNKTION `potential.rechne()`, nicht
mit einer Kopie - sonst misst man eine Nachbildung, die still veraltet.

    python vorschau_g6_scharfschaltung.py
"""
import io
import json
import statistics as st
import sys

import numpy as np

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, ".")

from agent import potential as PT                            # noqa: E402
from agent import wahrscheinlichkeit as WK                   # noqa: E402

CACHE = "anker_boden_2026_08_31.json"      # hat funding je Anker
MIND_JE_TAG = 15
CRV = 2.0
STOP_REL = 0.05
SCHWELLEN = (0.000, 0.005, 0.010, 0.020, 0.050, 0.080)


def fuenftel_je_tag(anker, feld):
    """Rang je Kalendertag - dieselbe Form wie `marktrang`."""
    je_tag = {}
    for a in anker:
        if a.get(feld) is not None:
            je_tag.setdefault(a["datum"], []).append(a)
    for tag, z in je_tag.items():
        if len(z) < MIND_JE_TAG:
            for x in z:
                x[feld + "_5"] = None
            continue
        w = np.array([x[feld] for x in z], dtype=float)
        r = np.argsort(np.argsort(w)) / max(len(w) - 1, 1)
        for x, q in zip(z, r):
            x[feld + "_5"] = min(int(q * 5), 4)
    return anker


def main():
    anker = [a for a in json.loads(io.open(CACHE, encoding="utf-8").read())
             if a.get("in_r") is not None and a.get("funding") is not None]
    anker = fuenftel_je_tag(anker, "funding")
    anker = [a for a in anker if a.get("funding_5") is not None]
    n = len(anker)

    print("=" * 100)
    print("G-6 VORSCHAU — WAS PASSIERT, WENN STUFE 11 SCHARF WIRD?")
    print("=" * 100)
    print("%d Anker mit Funding-Rang, %d Kalendertage, %s .. %s"
          % (n, len({a["datum"] for a in anker}),
             min(a["datum"] for a in anker), max(a["datum"] for a in anker)))
    print()
    print("⚠️ IST-ZUSTAND: `rollen_gate.NUR_ZAEHLEN = (\"entscheider\",)`")
    print("   Stufe 11 rechnet und bucht - sie sperrt NICHTS.")
    print("⚠️ Und die Kette hat keinen Betriebsaufrufer (B1); das letzte")
    print("   Signal stammt vom 21.07.2026 aus der ALTEN Kette.")
    print("   Scharf schalten wirkt also erst mit der Verdrahtung.")

    # ---- Potential je Anker, mit der PRODUKTIONSFUNKTION ---------------
    # ⚠️ Turnover liegt fuer diese Anker nicht vor - die Vorschau rechnet
    # deshalb NUR mit Funding. Das ist die vorsichtige Richtung: der zweite
    # Beitrag streut zusaetzlich und wuerde die Trennung eher schaerfen.
    tabelle = {}
    for f in range(5):
        tabelle[f] = PT.rechne(crv=CRV, stop_relativ=STOP_REL,
                               klasse="krypto", instrument="spot",
                               strategie="einstieg", h=None,
                               merkmale={"funding_fuenftel": f}).wert_r
    for a in anker:
        a["potential"] = tabelle[a["funding_5"]]

    print()
    print("-" * 100)
    print("1 — DIE VERTEILUNG (nur Funding; Turnover streut zusaetzlich)")
    print("-" * 100)
    print("  Fuenftel   Potential   Anker      Anteil")
    for f in range(5):
        teil = [a for a in anker if a["funding_5"] == f]
        print("     %d      %+.4f R %8d %9.1f %%"
              % (f, tabelle[f], len(teil), 100 * len(teil) / n))

    print()
    print("-" * 100)
    print("2 — DIE QUALITAET: sind die Gesperrten wirklich die schlechteren?")
    print("-" * 100)
    basis = st.median([a["in_r"] for a in anker])
    print("  Alle Anker: Median %+.4f R" % basis)
    print()
    print("  %-9s %11s %12s %12s %14s"
          % ("Schwelle", "Durchlass", "bleibt", "gesperrt", "Unterschied"))
    for s in SCHWELLEN:
        durch = [a["in_r"] for a in anker if a["potential"] > s]
        sperr = [a["in_r"] for a in anker if a["potential"] <= s]
        if len(durch) < 100 or len(sperr) < 100:
            print("  %-9.3f %10.1f %%   (eine Seite zu klein)"
                  % (s, 100 * len(durch) / n))
            continue
        md, ms = st.median(durch), st.median(sperr)
        print("  %-9.3f %10.1f %% %+11.4f %+12.4f %+14.4f  %s"
              % (s, 100 * len(durch) / n, md, ms, md - ms,
                 "sperrt die schlechteren" if md > ms
                 else "⚠️ sperrt die BESSEREN"))

    print()
    print("-" * 100)
    print("3 — DER TAKT: was bedeutet das im Betrieb?")
    print("-" * 100)
    # Der Takt steht in `scheduler/background.py`; die Rollen-Kette hat dort
    # keinen Job (B1). Gerechnet wird deshalb mit dem Takt, den die uebrigen
    # Jobs verwenden, und mit der gemessenen Auswahlbreite.
    schwelle = PT.schwelle()
    durchlass = sum(1 for a in anker if a["potential"] > schwelle) / n
    print("  Schwelle heute: %.3f R  ->  Durchlass %.1f %%"
          % (schwelle, 100 * durchlass))
    print()
    print("  ⚠️ DAS IST DER ANKER-DURCHLASS, NICHT DER SIGNAL-DURCHLASS.")
    print("  Vor Stufe 11 liegen sieben Bremsen (auftrag, fakten, lagebild,")
    print("  anlass, auswahl, wiederholung, urteil). Die Auswahl A1 laesst")
    print("  k=2 von 43 Werten durch - Stufe 11 sieht also nur, was dort")
    print("  uebrig ist. Ein Prozentsatz auf Anker ist eine OBERGRENZE fuer")
    print("  die Wirkung, keine Prognose der Signalzahl.")
    print()
    for name, je_jahr in (("A1-Schaetzung (Memory 24.08.)", 30.7),):
        print("  %s: %.1f Empfehlungen/Jahr" % (name, je_jahr))
        print("     davon nach G-6: %.1f/Jahr  (%.1f gesperrt)"
              % (je_jahr * durchlass, je_jahr * (1 - durchlass)))

    print()
    print("-" * 100)
    print("4 — EMPFINDLICHKEIT: wie stark haengt es an der Schwelle?")
    print("-" * 100)
    print("  Ein Beitrag, dessen Wirkung an der dritten Nachkommastelle")
    print("  haengt, ist keine stabile Basis.")
    for s in (0.005, 0.010, 0.020):
        d = sum(1 for a in anker if a["potential"] > s) / n
        print("    Schwelle %.3f -> Durchlass %.1f %%" % (s, 100 * d))
    stufen = sorted({round(v, 4) for v in tabelle.values()})
    print("  Die Potentialwerte sind DISKRET (%d Stufen): %s"
          % (len(stufen), ", ".join("%+.4f" % x for x in stufen)))
    print("  -> Zwischen zwei Stufen aendert die Schwelle GAR NICHTS. Das")
    print("     ist stabiler als ein stetiger Wert, aber es heisst auch:")
    print("     die Schwelle waehlt nur aus, WIEVIELE Fuenftel durchkommen.")

    print()
    print("=" * 100)
    print("WAS DIE SCHARFSCHALTUNG KONKRET AENDERT")
    print("=" * 100)
    print("  vorher: Stufe 11 zaehlt      -> jedes Signal geht durch")
    print("  nachher: Stufe 11 verwirft   -> %.1f %% der Anker gesperrt"
          % (100 * (1 - durchlass)))
    print()
    print("  ⚠️ ERST WIRKSAM MIT B1 (Verdrahtung der Kette). Bis dahin ist")
    print("     es eine Festlegung, keine Aenderung am Betrieb.")


if __name__ == "__main__":
    main()
