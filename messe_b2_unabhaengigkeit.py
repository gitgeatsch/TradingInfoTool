# -*- coding: utf-8 -*-
"""B-2: WO sitzt der B-Schaden, und ist er eigenstaendig? (31.08.2026)

⚠️ DIESER KOPF IST DIE VORABFESTLEGUNG, geschrieben BEVOR gerechnet wurde.

## Der Befund, der hierher fuehrt (30.08.2026)

`messe_h3_totzone_und_kombination.py` hat H zerlegt:

    A  freier Weg          trifft  4,0 %    +0,0089 R   neutral
    B  Stop gedeckt        trifft 85,7 %    -0,2023 R   ueber der Huerde
    H  = A UND B           trifft  2,2 %    -0,1476 R

**B ist in H als POSITIVE Bedingung eingebaut und wirkt NEGATIV.** Der
Befund haelt in allen fuenf ATR-Fuenfteln, beiden Historienhaelften, allen
drei Zeitabschnitten, und liegt ausserhalb des Placebo-Bandes.

## ⚠️ EINE VERMUTUNG WAR SCHON FALSCH

Ich hatte gedeutet: "eine Unterstuetzung knapp ueber dem Stop heisst, der
Stop liegt in der Zone, in der Stops abgeraeumt werden". Die Totzonen-Reihe
widerlegt das:

    Marke ab 0,25 ATR unter Kurs   -0,2144   (88,0 %)
    Marke ab 0,50 ATR              -0,2023   (85,7 %)
    Marke ab 1,00 ATR              -0,1551   (78,7 %)
    Marke ab 1,50 ATR              -0,1030   (58,6 %)

Je NAEHER am Stop, desto SCHWAECHER. Der Schaden kommt also nicht vom Stop
her, sondern von Marken NAHE AM KURS. Diese Messung klaert, welches Band es
genau ist - und ob der Effekt dann noch eigenstaendig ist.

## Die vier Fragen, vorab festgelegt

  F1 WO       In welchem Abstandsband sitzt die schaedliche Marke? Gerechnet
              wird DISJUNKT: "die naechste Marke liegt in [x, y)" - nicht
              "es gibt eine ab x", sonst ueberlappen alle Baender.
  F2 ADDITIV  Traegt B INNERHALB der Funding-Fuenftel? Faellt es dort weg,
              ist es ein Mitlaeufer des staerksten bekannten Beitrags.
  F3 EIGEN    Ist B nur die Markendichte? Wenn "viele Marken unten" dasselbe
              sagt wie "es gibt eine", ist B eine Dichteangabe.
  F4 RICHTUNG Gilt dasselbe fuer Marken OBERHALB (A's Seite)? Wenn ja, ist
              es kein Boden-Effekt, sondern "Kurs klebt an einer Marke".

## Vorab festgelegt

  eigenstaendig   traegt in F2 innerhalb der Funding-Fuenftel UND ist in F3
                  nicht durch die Dichte ersetzbar
  Mitlaeufer      faellt in F2 oder F3
  anderer Effekt  F4 zeigt dasselbe oben - dann ist die Deutung "Boden"
                  falsch und muss neu gefasst werden

    python messe_b2_unabhaengigkeit.py
"""
import io
import json
import sys

import numpy as np

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, ".")

import messe_h3_totzone_und_kombination as M                     # noqa: E402

CACHE = "anker_h3_2026_08_30.json"
HUERDE = 0.1733          # aus dem H-3-Lauf, ueber 33 Zellen
PLACEBO_LAEUFE = 40
# Die Totzonen-Schluessel, wie sie im Cache heissen ("%g")
BAENDER = (("0.25", 0.25), ("0.5", 0.5), ("1", 1.0), ("1.5", 1.5), ("2", 2.0))


def zeige(titel, w, einzug=4, huerde=HUERDE):
    if w is None:
        print("%s%-46s zu wenige Bloecke" % (" " * einzug, titel))
        return None
    b = np.array(w)
    m = float(b.mean())
    print("%s%-46s %+.4f R  %2d/%2d +   %s"
          % (" " * einzug, titel, m, int((b > 0).sum()), len(b),
             "⚠️ ueber der Huerde" if abs(m) > huerde else "unter der Huerde"))
    return m


def main():
    anker = json.loads(io.open(CACHE, encoding="utf-8").read())
    rng = np.random.default_rng(20260831)
    n = len(anker)

    print("=" * 104)
    print("B-2 — WO SITZT DER SCHADEN, UND IST ER EIGENSTAENDIG?")
    print("=" * 104)
    print("%d Anker. Huerde aus dem H-3-Lauf: %.4f R" % (n, HUERDE))

    # ---------------------------------------------------------------- F1
    print()
    print("-" * 104)
    print("  F1 — IN WELCHEM BAND SITZT DIE NAECHSTE MARKE? (disjunkt)")
    print("-" * 104)
    print("  ⚠️ DISJUNKT gerechnet: 'die naechste Marke liegt in [x, y)'.")
    print("  Die Reihe aus dem H-3-Lauf war KUMULATIV ('es gibt eine ab x') -")
    print("  dort ueberlappen alle Baender, und ein Vergleich zwischen ihnen")
    print("  misst nur, wieviel jedes zusaetzlich enthaelt.")
    print()
    for i, (s, gr) in enumerate(BAENDER):
        naechst = BAENDER[i + 1][0] if i + 1 < len(BAENDER) else None
        if naechst is None:
            def bed(a, k="ged_%s_2" % s):
                return a[k]
            klar = "Marke ab %.2f ATR (letztes Band)" % gr
        else:
            def bed(a, k="ged_%s_2" % s, k2="ged_%s_2" % naechst):
                return a[k] and not a[k2]
            klar = "naechste Marke in [%.2f .. %.2f) ATR" % (gr, BAENDER[i + 1][1])
        q = 100 * sum(1 for a in anker if bed(a)) / n
        zeige("%s  (%5.1f %%)" % (klar, q),
              M.je_block(anker, bed))

    # ---------------------------------------------------------------- F4
    print()
    print("-" * 104)
    print("  F4 — GILT DASSELBE OBERHALB? (dann ist 'Boden' die falsche Deutung)")
    print("-" * 104)
    print("  A ist die ABWESENHEIT eines Widerstands. Die Anwesenheit ist")
    print("  also `not frei` - dieselbe Frage, andere Richtung.")
    for s, gr in BAENDER[:4]:
        q = 100 * sum(1 for a in anker if not a["frei_%s_2" % s]) / n
        zeige("Widerstand ab %.2f ATR ueber Kurs  (%5.1f %%)" % (gr, q),
              M.je_block(anker, lambda a, k="frei_%s_2" % s: not a[k]))

    # ---------------------------------------------------------------- F3
    print()
    print("-" * 104)
    print("  F3 — IST B NUR DIE DICHTE? Marke unten UND oben gegen nur unten")
    print("-" * 104)
    F = "ged_0.5_2"
    G = "frei_0.5_2"
    for klar, bed in (
            ("nur unten eine Marke",
             lambda a: a[F] and a[G]),
            ("nur oben eine Marke",
             lambda a: (not a[F]) and (not a[G])),
            ("beidseitig eingeklemmt",
             lambda a: a[F] and not a[G]),
            ("frei nach beiden Seiten",
             lambda a: (not a[F]) and a[G])):
        q = 100 * sum(1 for a in anker if bed(a)) / n
        zeige("%s  (%5.1f %%)" % (klar, q), M.je_block(anker, bed))

    # ---------------------------------------------------------------- F2
    print()
    print("-" * 104)
    print("  F2 — ADDITIV ZU FUNDING? B innerhalb der Funding-Fuenftel")
    print("-" * 104)
    mitf = [a for a in anker if a.get("funding") is not None]
    print("  %d Anker mit Funding-Wert (%.1f %%)" % (len(mitf), 100 * len(mitf) / n))
    je_tag = {}
    for a in mitf:
        je_tag.setdefault(a["datum"], []).append(a)
    for tag, z in je_tag.items():
        if len(z) < 15:
            for x in z:
                x["f5"] = None
            continue
        w = np.array([x["funding"] for x in z], dtype=float)
        r = np.argsort(np.argsort(w)) / max(len(w) - 1, 1)
        for x, q_ in zip(z, r):
            x["f5"] = min(int(q_ * 5), 4)
    werte = []
    for k in range(5):
        m = zeige("Funding-Fuenftel %d" % k,
                  M.je_block(mitf, lambda a: a[F],
                             bedingung=lambda a, kk=k: a.get("f5") == kk))
        werte.append(m)
    gueltig = [x for x in werte if x is not None]
    if gueltig:
        print()
        print("    -> %s"
              % ("alle Fuenftel gleiches Vorzeichen - B ist ADDITIV"
                 if all(x < 0 for x in gueltig) or all(x > 0 for x in gueltig)
                 else "⚠️ Vorzeichen wechselt - B haengt an Funding"))

    # ------------------------------------------------------------ Kontrolle
    print()
    print("-" * 104)
    print("  NEGATIVKONTROLLE fuer das staerkste Band aus F1")
    print("-" * 104)
    je_sym = {}
    for a in anker:
        je_sym.setdefault(a["sym"], []).append(a)
    sortiert = {s: sorted(z, key=lambda x: x["datum"]) for s, z in je_sym.items()}
    p = []
    for _ in range(PLACEBO_LAEUFE):
        versetzt = []
        for z in sortiert.values():
            v = int(rng.integers(0, max(len(z), 1)))
            um = z[v:] + z[:v]
            for x, y in zip(z, um):
                versetzt.append({**x, F: y[F], G: y[G]})
        w = M.je_block(versetzt, lambda a: a[F])
        if w:
            p.append(float(np.mean(w)))
    p = np.array(p)
    u, o = np.quantile(p, [0.025, 0.975])
    echt = float(np.mean(M.je_block(anker, lambda a: a[F])))
    print("    Band %+.4f .. %+.4f (Mitte %+.4f, %d Laeufe)"
          % (u, o, float(p.mean()), len(p)))
    print("    echt %+.4f  ->  %s"
          % (echt, "AUSSERHALB - der Befund haelt" if (echt < u or echt > o)
             else "⚠️ INNERHALB"))


if __name__ == "__main__":
    main()
