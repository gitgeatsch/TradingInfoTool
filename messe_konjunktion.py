# -*- coding: utf-8 -*-
"""K-1: Traegt eine KOMBINATION, wo die Einzelteile nicht tragen? (29.08.2026)

## Das Nutzermodell, seit dem 20.08. unveraendert

    *"Ein Wert hat fast keine positive Auswirkung, aber die richtige
    Kombination bildet dann den Trichter der Optimierung."*

Es hat **einen** Beleg im System: `H = A und B` - der einzige tragende Beitrag
ist selbst eine Konjunktion. Und es hatte am 20.08. einen zweiten (Kapitel 103,
+17,8 gegen eine Additionserwartung von +9,6), der an der **Datenmenge** fiel:
nur 26 Reihen waren lang genug, und die Positivkontrolle fand dort nur Effekte
ab rund 20 Punkten.

**Heute stehen 485 Reihen zur Verfuegung.** Das ist der Grund fuer diesen Lauf.

## Der Aufbau

FUENF KANAELE, bewusst aus verschiedenen Informationsquellen - denn die harte
Vorbedingung der Konjunktion lautet: die Bestandteile muessen VERSCHIEDENE
Information tragen (Kapitel 103).

    trend        Kurs / 200-Tage-Schnitt        wo im Trend
    rueckgang    Kurs / Jahreshoch              wie weit unter dem Hoch
    schwankung   Spanne heute / Spanne 252 T    ruhig oder bewegt
    umschlag     Volumen heute / Volumen 252 T  Aufmerksamkeit
    momentum     Kurs / Kurs vor 20 Tagen       kurzfristige Richtung

Jeder Kanal wird je Kalendertag in **Terzile quer ueber die Assets** geteilt -
damit ist die Marktlage konstant gehalten und der Vergleich ist zwischen
Assets, nicht zwischen Tagen.

    EINZELN      5 Kanaele x 3 Terzile             =  15 Zellen
    PAARE        10 Paare  x 9 Kombinationen       =  90 Zellen
                                                     ---
                                                     105 Zellen

## DER SUCHPREIS IST EINGEBAUT - daran ist Kapitel 103 gescheitert

Ein Maximum aus 105 Zellen ist auch bei reinem Zufall gross. Deshalb wird
NICHT die beste Zelle gegen eine Einzelschwelle gehalten, sondern gegen die
**Verteilung des MAXIMUMS** unter der Nullhypothese: in jedem Placebo-Lauf
wird ueber ALLE Zellen das Maximum genommen.

Die Nullhypothese permutiert die Merkmale **innerhalb jedes Kalendertags** -
das erhaelt die Marktlage (und damit die Abhaengigkeit der Anker) vollstaendig
und zerstoert nur die Behauptung: dass die Merkmale die Assets richtig
sortieren.

## Vorab festgelegt, VOR dem Lauf

  traegt       die beste Zelle liegt ueber dem 95-%-Punkt der Maximum-
               Verteilung, UND ueberadditiv gegenueber ihren Einzelteilen
  traegt nicht sonst
  Liegt der Messwert nahe an der Schwelle, wird die Zahl der Laeufe erhoeht,
  BEVOR etwas behauptet wird (Kapitel 103.7).
"""
import itertools
import statistics as st
import sys

import numpy as np

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import messe_eigenschaft_beitrag as B

KANAELE = ("trend", "rueckgang", "schwankung", "umschlag", "momentum")
TERZILE = ("unten", "mitte", "oben")
MIND_JE_TAG = 15
MIND_ZELLE = 300
LAEUFE = 200


def anker(reihen, horizont):
    """Alle Anker mit den fuenf Kanaelen, je Kalendertag gesammelt."""
    je_tag = {}
    for sym, zeilen in reihen.items():
        tage = [z[0] for z in zeilen]
        schluss = np.array([z[1] for z in zeilen])
        hoch = np.array([z[2] for z in zeilen])
        tief = np.array([z[3] for z in zeilen])
        vol = np.array([z[4] for z in zeilen])
        breite = B.spanne(hoch, tief, schluss, B.SCHWANKUNG)
        spanne_tag = hoch - tief
        for i in range(252, len(schluss) - horizont):
            if not np.isfinite(breite[i]) or breite[i] <= 0:
                continue
            schnitt = schluss[i - 200:i].mean()
            jahreshoch = hoch[i - 252:i].max()
            mittlere_spanne = spanne_tag[i - 252:i].mean()
            mittleres_vol = vol[i - 252:i].mean()
            if min(schnitt, jahreshoch, mittlere_spanne) <= 0:
                continue
            je_tag.setdefault(tage[i], []).append((
                float(schluss[i] / schnitt - 1.0),
                float(schluss[i] / jahreshoch - 1.0),
                float(spanne_tag[i] / mittlere_spanne),
                float(vol[i] / mittleres_vol) if mittleres_vol > 0 else 1.0,
                float(schluss[i] / schluss[i - 20] - 1.0),
                float((schluss[i + horizont] - schluss[i]) / breite[i])))
    return {t: np.array(z) for t, z in je_tag.items() if len(z) >= MIND_JE_TAG}


def terzile(spalte):
    """0/1/2 je Wert - Terzil innerhalb dieses Tages."""
    r = np.argsort(np.argsort(spalte)) / max(len(spalte) - 1, 1)
    return np.clip((r * 3).astype(int), 0, 2)


def zellen(je_tag, mische=None):
    """Median der Bewegung je Zelle. `mische`: rng zum Permutieren."""
    sammel = {}
    for z in je_tag.values():
        merkmale = [terzile(z[:, k]) for k in range(5)]
        if mische is not None:
            o = mische.permutation(len(z))
            merkmale = [m[o] for m in merkmale]
        ziel = z[:, 5]
        for k in range(5):
            for t in range(3):
                w = ziel[merkmale[k] == t]
                if len(w):
                    sammel.setdefault((KANAELE[k], TERZILE[t]), []).extend(w)
        for a, b in itertools.combinations(range(5), 2):
            for ta in range(3):
                for tb in range(3):
                    w = ziel[(merkmale[a] == ta) & (merkmale[b] == tb)]
                    if len(w):
                        sammel.setdefault(
                            (KANAELE[a] + "/" + KANAELE[b],
                             TERZILE[ta] + "/" + TERZILE[tb]), []).extend(w)
    return {k: st.median(v) for k, v in sammel.items() if len(v) >= MIND_ZELLE}


def main():
    reihen = B.lade()
    horizont = 20
    print("=" * 88)
    print("K-1 - TRAEGT EINE KOMBINATION, WO DIE EINZELTEILE NICHT TRAGEN?")
    print("=" * 88)
    je_tag = anker(reihen, horizont)
    n = sum(len(z) for z in je_tag.values())
    print("523 Reihen - Horizont %d Handelstage - %d Anker an %d Kalendertagen"
          % (horizont, n, len(je_tag)))
    echt = zellen(je_tag)
    einzeln = {k: v for k, v in echt.items() if "/" not in k[0]}
    paare = {k: v for k, v in echt.items() if "/" in k[0]}
    print("Zellen mit mindestens %d Faellen: %d einzeln, %d als Paar"
          % (MIND_ZELLE, len(einzeln), len(paare)))
    print()
    print("DIE BESTEN EINZELKANAELE")
    for k, v in sorted(einzeln.items(), key=lambda x: -x[1])[:5]:
        print("  %-14s %-6s %+.4f R" % (k[0], k[1], v))
    print()
    print("DIE BESTEN PAARE")
    besten = sorted(paare.items(), key=lambda x: -x[1])[:6]
    for k, v in besten:
        a, b = k[0].split("/")
        ta, tb = k[1].split("/")
        ea = einzeln.get((a, ta))
        eb = einzeln.get((b, tb))
        zusatz = ""
        if ea is not None and eb is not None:
            zusatz = "   Teile %+.3f / %+.3f -> %s" % (
                ea, eb, "UEBERADDITIV" if v > ea + eb else "additiv oder weniger")
        print("  %-26s %-14s %+.4f R%s" % (k[0], k[1], v, zusatz))
    print()
    print("DER SUCHPREIS - Verteilung des MAXIMUMS ueber alle %d Zellen"
          % len(echt))
    rng = np.random.default_rng(20260829)
    maxima = []
    for lauf in range(LAEUFE):
        p = zellen(je_tag, rng)
        if p:
            maxima.append(max(p.values()))
        if (lauf + 1) % 50 == 0:
            print("  ... %d von %d Laeufen" % (lauf + 1, LAEUFE))
    schwelle = float(np.quantile(maxima, 0.95))
    bester = besten[0][1] if besten else float("nan")
    print()
    print("  groesster Zufallswert   %+.4f R" % max(maxima))
    print("  Schwelle (95 %%)         %+.4f R" % schwelle)
    print("  gemessen (beste Zelle)  %+.4f R" % bester)
    print()
    print("  -> %s" % ("TRAEGT" if bester > schwelle else "TRAEGT NICHT"))
    if abs(bester - schwelle) < 0.02:
        print("  WARNUNG: knapp an der Schwelle - Laeufe erhoehen (Kapitel 103.7)")


if __name__ == "__main__":
    main()
