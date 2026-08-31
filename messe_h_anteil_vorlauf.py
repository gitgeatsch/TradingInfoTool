# -*- coding: utf-8 -*-
"""Sagt der H-ANTEIL voraus - oder beschreibt er nur? (30.08.2026)

## Die Frage, die ueber die Einordnung von H entscheidet

`zerlege_h_widerspruch.py` hat gezeigt: der gepoolte H-Vorsprung von
+3,04 Punkten besteht aus

    innerhalb der Zeitbloecke   -7,14 Punkte   was ein H-Anker leistet
    Komposition                +10,18 Punkte   dass H in guten Zeiten auftritt

und die Korrelation zwischen dem H-Anteil eines Blocks und dem Niveau
desselben Blocks betraegt +0,524.

⚠️ ABER DAS IST GLEICHZEITIG GEMESSEN. Die Anker eines Blocks starten im
Block und laufen 20 Tage - der H-Anteil und das Niveau beschreiben
weitgehend denselben Zeitraum. Nach der Prueffrage aus CLAUDE.md:

    FAKT       beschreibt die GEGENWART
    BEWERTUNG  sagt etwas ueber das, was KOMMT

Ein gleichzeitiger Zusammenhang ist ein FAKT. Er gehoert in die Mail,
nicht in die Ausloesung. Nur wenn der H-Anteil von HEUTE die Bewegung der
NAECHSTEN 20 Tage trennt, ist er eine Bewertung - und damit brauchbar.

## Der Aufbau

    H-Anteil am Tag t   aus allen Ankern des Tages t - steht am Tag t fest
    Bewegung t..t+20    aus denselben Ankern - liegt VOLLSTAENDIG in der
                        Zukunft von t

⚠️ KEIN LOOKAHEAD, aber auch KEINE TRENNUNG DER ZEITRAEUME: Anker des Tages
t laufen bis t+20. Der H-Anteil von t ist trotzdem am Tag t bekannt. Das
ist genau die Lage einer echten Entscheidung.

## Der Massstab: das Placebo-Band, nicht der Bootstrap

Ein Bootstrap ueber Bloecke hat bei dieser Frage schon einmal versagt
(`messe_h_als_marktmerkmal.py`: die Positivkontrolle fand nicht einmal
+0,40 R). Hier steht deshalb die Reihe der H-Anteile gegen ZIRKULAER
VERSETZTE Fassungen ihrer selbst - der Versatz erhaelt die Autokorrelation
beider Reihen und zerstoert nur den Gleichlauf.

  traegt        der echte Zusammenhang liegt ausserhalb des Placebo-Bandes
                aus %d Versaetzen
  traegt nicht  innerhalb - dann ist der H-Anteil ein FAKT ueber die
                laufende Phase, keine Aussage ueber die kommende
"""
import io
import json
import sys

import numpy as np

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

CACHE = "anker_h_2026_08_30.json"
MIND_ANKER = 20
VERSAETZE = 400
MIND_VERSATZ = 60      # kleinere Versaetze lassen den Gleichlauf teilweise stehen


def tagesreihen():
    """Je Kalendertag: H-Anteil, Median-Bewegung, Ziel-Quote."""
    anker = json.loads(io.open(CACHE, encoding="utf-8").read())
    je_tag = {}
    for a in anker:
        je_tag.setdefault(a["datum"], []).append(a)
    tage = sorted(t for t, z in je_tag.items() if len(z) >= MIND_ANKER)
    anteil = np.array([sum(1 for a in je_tag[t] if a["h"]) / len(je_tag[t])
                       for t in tage])
    bewegung = np.array([float(np.median([a["in_r"] for a in je_tag[t]]))
                         for t in tage])
    ziel = []
    for t in tage:
        mit = [a["ziel"] for a in je_tag[t] if a["ziel"] is not None]
        ziel.append(float(np.mean(mit)) if mit else np.nan)
    return tage, anteil, bewegung, np.array(ziel)


def zusammenhang(anteil, ergebnis, grenze=0.8):
    """Hohe-H-Anteil-Tage minus uebrige - in der Einheit von `ergebnis`."""
    gut = np.isfinite(ergebnis)
    a, e = anteil[gut], ergebnis[gut]
    s = float(np.quantile(a, grenze))
    hoch, tief = e[a >= s], e[a < s]
    if len(hoch) < 50 or len(tief) < 50:
        return None
    return float(np.mean(hoch) - np.mean(tief))


def band(anteil, ergebnis, rng):
    """Placebo: die H-Anteil-Reihe zirkulaer gegen das Ergebnis versetzen."""
    n = len(anteil)
    werte = []
    for _ in range(VERSAETZE):
        v = int(rng.integers(MIND_VERSATZ, n - MIND_VERSATZ))
        w = zusammenhang(np.concatenate((anteil[v:], anteil[:v])), ergebnis)
        if w is not None:
            werte.append(w)
    return np.array(werte)


def zeige(name, echt, p, einheit):
    u, o = np.quantile(p, [0.025, 0.975])
    drin = u <= echt <= o
    print("  %-22s echt %+.4f %s   Placebo %+.4f .. %+.4f (Mitte %+.4f)"
          % (name, echt, einheit, u, o, float(p.mean())))
    print("  %-22s -> %s" % ("", "⚠️ INNERHALB des Bandes - ein FAKT ueber die "
                             "laufende Phase, keine Vorhersage" if drin else
                             "AUSSERHALB - der H-Anteil trennt die kommenden Tage"))
    return not drin


def main():
    tage, anteil, bewegung, ziel = tagesreihen()
    rng = np.random.default_rng(20260830)
    print("=" * 96)
    print("SAGT DER H-ANTEIL VORAUS — ODER BESCHREIBT ER NUR?")
    print("=" * 96)
    print("%d Kalendertage mit mindestens %d Ankern, %s .. %s"
          % (len(tage), MIND_ANKER, tage[0], tage[-1]))
    print("H-Anteil je Tag: Median %.1f %%, oberstes Fuenftel ab %.1f %%"
          % (100 * float(np.median(anteil)), 100 * float(np.quantile(anteil, 0.8))))
    print("Placebo: %d zirkulaere Versaetze, mindestens %d Tage."
          % (VERSAETZE, MIND_VERSATZ))
    print()

    for name, reihe, einheit in (("BEWEGUNG IN R", bewegung, "R"),
                                 ("ZIEL VOR STOP", ziel, " ")):
        echt = zusammenhang(anteil, reihe)
        zeige(name, echt, band(anteil, reihe, rng), einheit)
        print()

    print("=" * 96)
    print("POSITIVKONTROLLE — waere ein echter Vorlauf gefunden worden?")
    print("=" * 96)
    print("  Gepflanzt wird ein ECHTER Vorlauf: auf Tage mit hohem H-Anteil")
    print("  kommt ein Zuschlag auf die Bewegung. Findet die Anlage ihn nicht,")
    print("  ist der Nullbefund oben wertlos.")
    s = float(np.quantile(anteil, 0.8))
    for staerke in (0.05, 0.10, 0.20, 0.40):
        gepflanzt = bewegung + np.where(anteil >= s, staerke, 0.0)
        echt = zusammenhang(anteil, gepflanzt)
        p = band(anteil, gepflanzt, rng)
        u, o = np.quantile(p, [0.025, 0.975])
        print("  gepflanzt %+.2f R   echt %+.4f   Placebo %+.4f .. %+.4f   %s"
              % (staerke, echt, u, o,
                 "gefunden" if not (u <= echt <= o) else "⚠️ NICHT gefunden"))


if __name__ == "__main__":
    main()
