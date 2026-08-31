# -*- coding: utf-8 -*-
"""Traegt H im HEUTIGEN Markt noch? (30.08.2026)

## Der Anlass

Nutzerhinweis: *"der Kryptomarkt hat sich vor allem im Bereich BTC geaendert,
er ist abgeflachter, geringere Anstiege als vor 2024."*

**Gemessen und bestaetigt** (`pruefe_btc_abflachung.py`):

    Bewegung in R, Median 20 Tage
      2018-2020   +0,1397
      2021-2023   -0,2469
      2024-2026   -0,6251

Das ist unser Messmasz. H wurde ueber 2018-2026 gemessen (+4,5 Punkte) - also
zum groeszten Teil auf einem Markt, den es so nicht mehr gibt.

## Die Frage

    Traegt H im Abschnitt ab 2024 noch - und wenn nicht: liegt das am Markt
    oder an der kleineren Stichprobe?

⚠️ Die zweite Haelfte der Frage ist die wichtigere. Ein Drittel der Anker
liefert eine schwaechere Messung; ein Nullbefund koennte reiner Datenmangel
sein. Deshalb laeuft eine POSITIVKONTROLLE je Abschnitt mit.

## Der Aufbau

`messe_marken.laufe()` liefert je Anker `frei`, `gedeckt`, `ausgang` und
`datum`. Ausgewertet wird wie im Original (`bewerte()`), aber je Abschnitt
getrennt - und zusaetzlich je Marktphase innerhalb der Abschnitte.

⚠️ Vorab festgelegt, VOR dem Lauf:

  H traegt noch      Vorsprung ab 2024 positiv UND ueber der Blockschwelle
  H traegt nicht mehr  Vorsprung <= 0, UND die Positivkontrolle zeigt, dass
                     ein Effekt dieser Groesse gefunden worden waere
  unentscheidbar     Vorsprung <= 0, aber die Positivkontrolle faellt auch
"""
import statistics as st
import sys

import numpy as np

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import messe_marken as MM

ABSCHNITTE = (("2018-2020", "2018-01-01", "2020-12-31"),
              ("2021-2023", "2021-01-01", "2023-12-31"),
              ("2024-2026", "2024-01-01", "2026-12-31"))
BLOCK_LAEUFE = 40


def quote(faelle):
    """Anteil 'Ziel vor Stop' unter den entschiedenen Faellen."""
    ent = [f for f in faelle if f["ausgang"] in ("ziel", "stop")]
    if len(ent) < 200:
        return None, len(ent)
    return sum(1 for f in ent if f["ausgang"] == "ziel") / len(ent), len(ent)


def vorsprung(faelle):
    """H-Quote minus Quote aller Anker desselben Ausschnitts, in Punkten."""
    q_h, n_h = quote([f for f in faelle if f["frei"] and f["gedeckt"]])
    q_a, n_a = quote(faelle)
    if q_h is None or q_a is None:
        return None, n_h, n_a
    return 100.0 * (q_h - q_a), n_h, n_a


def blockschwelle(faelle, rng):
    """Wie gross wird der Vorsprung, wenn H zufaellig verteilt ist?

    Ganze Zeitbloecke je Reihe tauschen - der freie Placebo waere hier kein
    Massstab, weil die Anker einander zu ueber 99 % ueberlappen (2.47).
    """
    je_reihe = {}
    for f in faelle:
        je_reihe.setdefault(f["sym"], []).append(f)
    werte = []
    for _ in range(BLOCK_LAEUFE):
        gemischt = []
        for zeilen in je_reihe.values():
            zeilen = sorted(zeilen, key=lambda x: x["datum"])
            marken = [(z["frei"], z["gedeckt"]) for z in zeilen]
            versatz = int(rng.integers(0, max(len(marken), 1)))
            marken = marken[versatz:] + marken[:versatz]      # zirkulaer
            for z, (fr, ge) in zip(zeilen, marken):
                gemischt.append({**z, "frei": fr, "gedeckt": ge})
        v, _, _ = vorsprung(gemischt)
        if v is not None:
            werte.append(v)
    return (float(np.quantile(werte, 0.95)), max(werte)) if werte else (None, None)


def main():
    print("Lade Anker - das dauert (523 Reihen)...", flush=True)
    faelle = MM.laufe("data/messdaten.db", "krypto", roh_pruefen=False,
                      fortschritt=True)
    print("%d Anker geladen." % len(faelle))
    rng = np.random.default_rng(20260830)

    print()
    print("=" * 90)
    print("TRAEGT H IM HEUTIGEN MARKT?  Vorsprung je Zeitabschnitt")
    print("=" * 90)
    print("  %-12s %9s %9s %11s %12s %s"
          % ("Abschnitt", "H-Faelle", "alle", "Vorsprung", "Blockschw.", "Urteil"))
    for name, von, bis in ABSCHNITTE:
        teil = [f for f in faelle if von <= f["datum"] <= bis]
        v, n_h, n_a = vorsprung(teil)
        if v is None:
            print("  %-12s %9d %9d   zu wenige entschiedene Faelle"
                  % (name, n_h, n_a))
            continue
        s95, groesster = blockschwelle(teil, rng)
        urteil = ("traegt" if s95 is not None and v > s95
                  else "TRAEGT NICHT")
        print("  %-12s %9d %9d %+10.1f %+11.1f  %s"
              % (name, n_h, n_a, v, s95 if s95 is not None else float("nan"),
                 urteil))

    print()
    print("=" * 90)
    print("POSITIVKONTROLLE — waere ein Effekt im juengsten Abschnitt gefunden worden?")
    print("=" * 90)
    juengste = [f for f in faelle if f["datum"] >= "2024-01-01"]
    s95, _ = blockschwelle(juengste, rng)
    print("  Blockschwelle im Abschnitt 2024-2026: %+.1f Punkte" % s95)
    for staerke in (2.0, 4.5, 8.0):
        # in H-Faellen kuenstlich Ziele erzeugen, bis der Vorsprung passt
        gepflanzt = []
        for f in juengste:
            g = dict(f)
            if (f["frei"] and f["gedeckt"] and f["ausgang"] == "stop"
                    and rng.random() < staerke / 100.0 * 2.2):
                g["ausgang"] = "ziel"
            gepflanzt.append(g)
        v, _, _ = vorsprung(gepflanzt)
        print("  gepflanzt ~%+.1f Punkte -> gemessen %+.1f  %s"
              % (staerke, v, "gefunden" if v > s95 else "NICHT gefunden"))

    print()
    print("=" * 90)
    print("JE MARKTPHASE INNERHALB des juengsten Abschnitts")
    print("=" * 90)
    for phase in ("bulle", "seitwaerts", "baer"):
        teil = [f for f in juengste if f.get("phase") == phase]
        v, n_h, n_a = vorsprung(teil)
        print("  %-12s %9s %9s %s"
              % (phase, n_h, n_a,
                 "%+.1f Punkte" % v if v is not None else "zu wenige Faelle"))


if __name__ == "__main__":
    main()
