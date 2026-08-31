# -*- coding: utf-8 -*-
"""Ist "kein Widerstand oberhalb" ein Befund - oder nur Volatilitaet? (30.08.2026)

`messe_h_neu.py` hat den groessten Einzelunterschied des Tages geliefert,
und zwar an einer Stelle, die als eigene Gruppe VORAB benannt war (nicht
nachtraeglich gesucht - Suchpreis, Methodik 2.57):

    ohne Widerstand    13.221 Anker   Median -0,0247 R
    mit  Widerstand   607.458 Anker   Median -0,2132 R
                                      Unterschied +0,19 R

⚠️ GENAU HIER IST MISSTRAUEN PFLICHT. Marken zaehlen erst ab
`NIVEAU_MIN_ABSTAND_ATR * atr` Abstand. Bei hoher Volatilitaet ist diese
Totzone in Prozent breiter - es ueberleben weniger Marken, und "kein
Widerstand" wird wahrscheinlicher. Der Befund koennte also die relative ATR
in neuen Kleidern sein. Genau dieser Fehler steckte in der alten Groesse A
(Korrelation +0,118).

## Die vier Fragen, vorab festgelegt

  V1 VOLATILITAET   Traegt es INNERHALB von Volatilitaets-Fuenfteln? Wenn
                    der Unterschied dort verschwindet, war es die ATR.
  V2 MARKT          Traegt es gegen Anker DESSELBEN Kalendertags? Sonst
                    beschreibt es nur, wann es auftritt (genau der Fehler,
                    an dem H's +4,5 Punkte zerfielen: Komposition +10,18
                    gegen Leistung -7,14).
  V3 ZEIT           Beide Historienhaelften, drei Zeitabschnitte.
  V4 KONTROLLEN     Placebo aus zirkulaeren Versaetzen je Symbol,
                    Positivkontrolle auf einem Nulldatensatz.

## Vorab festgelegt

  traegt        haelt in V1 UND V2, gleiches Vorzeichen in beiden Haelften,
                ausserhalb des Placebo-Bandes
  Volatilitaet  faellt in V1
  Komposition   faellt in V2 - dann ist es dieselbe Falle wie bei H

    python pruefe_ohne_widerstand.py
"""
import io
import json
import statistics as st
import sys

import numpy as np

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, ".")

CACHE = "anker_h_neu_2026_08_30.json"
BLOCK = 120
MIND_JE_GRUPPE = 30
PLACEBO_LAEUFE = 40
ZIEHUNGEN = 20000
ABSCHNITTE = (("2018-2020", "2018-01-01", "2020-12-31"),
              ("2021-2023", "2021-01-01", "2023-12-31"),
              ("2024-2026", "2024-01-01", "2026-12-31"))


def marke(a):
    return a["raum_atr"] is None


def roh(anker, feld="in_r"):
    o = [a[feld] for a in anker if marke(a) and a.get(feld) is not None]
    m = [a[feld] for a in anker if not marke(a) and a.get(feld) is not None]
    if len(o) < MIND_JE_GRUPPE or len(m) < MIND_JE_GRUPPE:
        return None, 0
    lage = (lambda x: float(np.mean(x))) if feld == "ziel" else st.median
    return lage(o) - lage(m), len(o)


def je_block(anker, feld="in_r", schluessel=None, block=BLOCK):
    """Vergleich JE ZEITBLOCK - sonst misst man die Komposition mit."""
    lage = (lambda x: float(np.mean(x))) if feld == "ziel" else st.median
    tage = sorted({a["datum"] for a in anker})
    if len(tage) < 2 * block:
        return None
    zuord = {t: i // block for i, t in enumerate(tage)}
    eimer = {}
    for a in anker:
        if a.get(feld) is None:
            continue
        k = (schluessel or marke)(a)
        eimer.setdefault(zuord[a["datum"]], ([], []))[0 if k else 1] \
            .append(float(a[feld]))
    werte = [lage(o) - lage(m) for o, m in eimer.values()
             if len(o) >= MIND_JE_GRUPPE and len(m) >= MIND_JE_GRUPPE]
    return werte if len(werte) >= 5 else None


def je_tag(anker, feld="in_r"):
    """⚠️ V2: gegen Anker DESSELBEN Kalendertags - der Test, an dem H fiel."""
    lage = (lambda x: float(np.mean(x))) if feld == "ziel" else st.median
    tabelle = {}
    for a in anker:
        if a.get(feld) is None:
            continue
        tabelle.setdefault(a["datum"], ([], []))[0 if marke(a) else 1] \
            .append(float(a[feld]))
    d = [lage(o) - lage(m) for o, m in tabelle.values()
         if len(o) >= 3 and len(m) >= 15]
    return d if len(d) >= 100 else None


def urteil(titel, werte, rng, einheit="R", einzug=2):
    if werte is None:
        print("%s%-40s zu wenige Faelle" % (" " * einzug, titel))
        return None
    b = np.array(werte, dtype=float)
    n = len(b)
    boot = np.array([b[rng.integers(0, n, n)].mean() for _ in range(ZIEHUNGEN)])
    u, o = np.quantile(boot, [0.025, 0.975])
    print("%s%-40s %+.4f %s [%+.4f .. %+.4f] %3d/%3d +  %s"
          % (" " * einzug, titel, b.mean(), einheit, u, o,
             int((b > 0).sum()), n,
             "TRAEGT" if u > 0 else ("UMGEKEHRT" if o < 0 else "nicht trennbar")))
    return float(b.mean())


def main():
    anker = json.loads(io.open(CACHE, encoding="utf-8").read())
    rng = np.random.default_rng(20260830)
    n = len(anker)
    ohne = sum(1 for a in anker if marke(a))

    print("=" * 104)
    print('IST "KEIN WIDERSTAND OBERHALB" EIN BEFUND - ODER NUR VOLATILITAET?')
    print("=" * 104)
    print("%d Anker, davon %d ohne Widerstand (%.2f %%)"
          % (n, ohne, 100 * ohne / n))
    d, _ = roh(anker)
    print("Roh (gepoolt, wie in messe_h_neu): %+.4f R" % d)
    print("⚠️ Gepoolt ist der Wert, der bei H die Falle war. Alles Weitere")
    print("   rechnet JE BLOCK oder JE TAG.")

    print()
    print("-" * 104)
    print("  V1 — TRAEGT ES INNERHALB VON VOLATILITAETS-FUENFTELN?")
    print("-" * 104)
    va = np.array([a["atr_rel"] for a in anker])
    q = np.quantile(va, [0, .2, .4, .6, .8, 1.0])
    print("  Anteil 'ohne Widerstand' je Fuenftel — die Kernfrage:")
    for i in range(5):
        teil = [a for a in anker if q[i] <= a["atr_rel"] <= q[i + 1]]
        o_ = sum(1 for a in teil if marke(a))
        print("    ATR %5.3f .. %5.3f   %6d Anker   ohne Widerstand %5.2f %%"
              % (q[i], q[i + 1], len(teil), 100 * o_ / max(len(teil), 1)))
    print()
    print("  Wirkung je Fuenftel (Block-Bootstrap):")
    for i in range(5):
        teil = [a for a in anker if q[i] <= a["atr_rel"] <= q[i + 1]]
        urteil("ATR-Fuenftel %d" % i, je_block(teil), rng, "R", 4)

    print()
    print("-" * 104)
    print("  ⚠️ V2 — GEGEN ANKER DESSELBEN KALENDERTAGS (der Test, an dem H fiel)")
    print("-" * 104)
    for feld, klar, einheit in (("in_r", "Bewegung in R", "R"),
                                ("ziel", "Ziel vor Stop", " ")):
        urteil(klar, je_tag(anker, feld), rng, einheit, 4)

    print()
    print("-" * 104)
    print("  V3 — ZEIT: Bloecke, Abschnitte, Haelften")
    print("-" * 104)
    for feld, klar, einheit in (("in_r", "Bewegung in R", "R"),
                                ("ziel", "Ziel vor Stop", " ")):
        urteil(klar + " (gesamt, je Block)", je_block(anker, feld), rng,
               einheit, 4)
    for name, von, bis in ABSCHNITTE:
        urteil(name, je_block([a for a in anker if von <= a["datum"] <= bis]),
               rng, "R", 6)
    tage = sorted({a["datum"] for a in anker})
    mitte = tage[len(tage) // 2]
    for name, bed in (("erste Haelfte", lambda a: a["datum"] < mitte),
                      ("zweite Haelfte", lambda a: a["datum"] >= mitte)):
        urteil(name, je_block([a for a in anker if bed(a)]), rng, "R", 6)

    print()
    print("-" * 104)
    print("  V4 — KONTROLLEN")
    print("-" * 104)
    echt = float(np.mean(je_block(anker)))
    je_sym = {}
    for a in anker:
        je_sym.setdefault(a["sym"], []).append(a)
    sortiert = {s: sorted(z, key=lambda x: x["datum"]) for s, z in je_sym.items()}
    p = []
    for _ in range(PLACEBO_LAEUFE):
        versetzt = []
        for z in sortiert.values():
            mk = [x["raum_atr"] for x in z]
            v = int(rng.integers(0, max(len(mk), 1)))
            for x, r_ in zip(z, mk[v:] + mk[:v]):
                versetzt.append({**x, "raum_atr": r_})
        w = je_block(versetzt)
        if w:
            p.append(float(np.mean(w)))
    p = np.array(p)
    u, o = np.quantile(p, [0.025, 0.975])
    print("    NEGATIV: Band %+.4f .. %+.4f (Mitte %+.4f, %d Laeufe)"
          % (u, o, float(p.mean()), len(p)))
    print("    echt %+.4f  ->  %s"
          % (echt, "AUSSERHALB - der Befund haelt" if (echt < u or echt > o)
             else "⚠️ INNERHALB - vom Zufall nicht zu trennen"))

    print()
    print("    POSITIV (auf einem Nulldatensatz gepflanzt):")
    null = []
    for z in sortiert.values():
        mk = [x["raum_atr"] for x in z]
        v = int(rng.integers(0, max(len(mk), 1)))
        for x, r_ in zip(z, mk[v:] + mk[:v]):
            null.append({**x, "raum_atr": r_})
    basis = float(np.mean(je_block(null)))
    print("      Nulldatensatz: %+.4f R" % basis)
    for staerke in (0.02, 0.05, 0.10, 0.20):
        g = [{**a, "in_r": a["in_r"] + (staerke if marke(a) else 0.0)}
             for a in null]
        urteil("gepflanzt %+.2f R" % staerke, je_block(g), rng, "R", 6)


if __name__ == "__main__":
    main()
