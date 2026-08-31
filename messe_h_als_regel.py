# -*- coding: utf-8 -*-
"""H als REGEL — die fehlende Prüfung (30.08.2026)

## Warum diese Messung die wichtigste ist

H ist der **einzige** Beitrag, der heute im System wirkt. Und die eine
Bedingung, die R-R8 (B3) fuer jeden anderen Beitrag zur Pflicht macht, fehlt
bei ihm: **H wurde nie als Regel gerechnet.** Alle bisherigen Zahlen sind
Merkmalsvergleiche ("H-Anker gegen alle Anker").

Bei Funding war der Unterschied **Faktor 5,5** - Merkmal +0,132 R, Regel
+0,024 R. Bei H ist er unbekannt.

## ⚠️ ZWEI AENDERUNGEN GEGENUEBER ALLEN BISHERIGEN H-MESSUNGEN

**1. Das Mass.** Bisher wurde "Ziel vor Stop" gezaehlt - das blinde Mass, das
per Konstruktion auf 1/(1+CRV) faellt. Hier zaehlt die **Bewegung in R**.

**2. Der Vergleich.** Bisher "H gegen ALLE Anker" - das mischt Auswahlleistung
und Selektionseffekt. Hier gegen eine **quotengleiche** Zufallsauswahl
desselben Kalendertags (Methodik 2.93). ⚠️ Bei H ist das besonders wichtig:
es trifft nur auf rund 3,3 % zu, und bei so kleinen Auswahlen ist der
Selektionseffekt am groessten.

## Der vollstaendige Pruefplan

`Basisinfos/Pruefplan_H_als_Regel_30_08.md` - 15 Fehlerquellen, jede mit
Massnahme. Hier eingebaut:

    Datenbrueche raus        Sprung > Faktor 5 im Vorwaertsfenster
    Median statt Mittel      Schiefe 2,68
    quotengleicher Zufall    je Kalendertag, 30 Ziehungen
    Block-Bootstrap          250 Tage > Horizont 20
    beide Haelften           getrennt
    je Zeitabschnitt         wegen des Struktureinbruchs 2024
    Positivkontrolle         kuenstliches Merkmal bekannter Guete
    Survivorship             Endstand der H-Symbole gegen den Rest

## Vorab festgelegt, VOR der ersten Zahl

  traegt          Netto positiv, Bootstrap ohne Null, beide Haelften gleiches
                  Vorzeichen
  traegt nicht    sonst UND die Positivkontrolle haette es gefunden
  unentscheidbar  Netto <= 0, Positivkontrolle faellt ebenfalls

⚠️ Die Konsequenz ist vorab benannt: Traegt H als Regel nicht, wird der
Beitrag auf `zustand="null"` gesetzt - NICHT auf einen kleineren Wert. Ein
Zwischenwert waere das Nachjustieren, das der Nutzer zu Recht zurueckgewiesen
hat.
"""
import io
import statistics as st
import sys

import numpy as np

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import messe_bewertungskennzahl as MB
import messe_eigenschaft_beitrag as B
import messe_marken as MM

HORIZONT = 20
BLOCK = 250          # > Horizont (Kapitel 103.6)
ZIEHUNGEN = 30
BRUCH = 5.0
ABSCHNITTE = (("2018-2020", "2018-01-01", "2020-12-31"),
              ("2021-2023", "2021-01-01", "2023-12-31"),
              ("2024-2026", "2024-01-01", "2026-12-31"))


def anker_mit_bewegung():
    """H-Anker plus die Bewegung in R - und ohne Datenbrueche."""
    print("Lade Anker (523 Reihen, dauert ~10 Minuten)...", flush=True)
    faelle = MM.laufe("data/messdaten.db", "krypto", roh_pruefen=False,
                      fortschritt=True)
    reihen = B.lade()
    # je Symbol: Datum -> (Index, Bewegung in R, Bruch im Fenster?)
    tabelle = {}
    for sym, roh in reihen.items():
        c = np.array([x[1] for x in roh])
        h = np.array([x[2] for x in roh])
        t_ = np.array([x[3] for x in roh])
        breite = B.spanne(h, t_, c, B.SCHWANKUNG)
        verh = c[1:] / np.maximum(c[:-1], 1e-12)
        bruch = (verh > BRUCH) | (verh < 1.0 / BRUCH)
        je_tag = {}
        for i in range(len(c) - HORIZONT):
            r = breite[i]
            if not np.isfinite(r) or r <= 0:
                continue
            if bruch[i:i + HORIZONT].any():
                continue                       # Massnahme 8
            je_tag[roh[i][0]] = float((c[i + HORIZONT] - c[i]) / r)
        tabelle[sym] = je_tag
    aus, verworfen = [], 0
    for f in faelle:
        w = tabelle.get(f["sym"], {}).get(f["datum"])
        if w is None:
            verworfen += 1
            continue
        # ⚠️ BEIDE MASSE. `in_r` ist die Bewegung - das neutrale Mass.
        # `ziel` ist "Ziel vor Stop" - das Mass, FUER DAS H GEBAUT IST.
        # Faellt H im einen durch und traegt im anderen, ist das ein
        # Befund und kein Nullbefund: dann beschreibt H die Geometrie,
        # und die steckt bereits im Nullpunkt (Doppelzaehlung).
        ziel = (1.0 if f.get("ausgang") == "ziel"
                else 0.0 if f.get("ausgang") == "stop" else None)
        aus.append({"sym": f["sym"], "datum": f["datum"],
                    "h": bool(f["frei"] and f["gedeckt"]),
                    "phase": f.get("phase"), "in_r": w, "ziel": ziel})
    print("%d Anker mit Bewegung (%d ohne - Datenbruch oder Randlage)."
          % (len(aus), verworfen))
    return aus


def je_tag(anker):
    d = {}
    for a in anker:
        d.setdefault(a["datum"], []).append(a)
    return d


def wirkung(tage, rng, pflanze_guete=None, feld="in_r"):
    """Je Kalendertag: Median(H) minus Median(quotengleicher Zufall)."""
    aus = {}
    for tag, z in tage.items():
        vorhanden = [a for a in z if a.get(feld) is not None]
        if len(vorhanden) < 6:
            continue
        y = np.array([a[feld] for a in vorhanden])
        if pflanze_guete is None:
            m = np.array([a["h"] for a in vorhanden])
        else:
            # kuenstliches Merkmal bekannter Guete (Massnahme 9)
            k = int(sum(a["h"] for a in vorhanden))
            if k < 1:
                continue
            # ⚠️ VORZEICHEN. Erste Fassung rechnete `-y + Rauschen` und
            # waehlte damit die SCHLECHTESTEN Anker - das perfekte Orakel
            # lieferte -3,57 R statt des Maximums. Eine Kontrolle mit
            # verdrehtem Vorzeichen belegt gar nichts (30.08.2026).
            wert = y + rng.normal(0, pflanze_guete * (np.std(y) or 1.0), len(y))
            m = np.zeros(len(y), bool)
            m[np.argsort(wert)[-k:]] = True
        k = int(m.sum())
        if k < 2 or k >= len(vorhanden) - 1:
            continue
        echt = float(np.median(y[m]))
        zufall = float(np.mean([
            float(np.median(y[rng.choice(len(y), k, replace=False)]))
            for _ in range(ZIEHUNGEN)]))
        aus[tag] = echt - zufall
    return aus


def main():
    import json
    import os
    # ⚠️ ZWISCHENSPEICHER. Das Laden dauert zehn Minuten; beide Masse auf
    # denselben Ankern zu rechnen darf nicht zwanzig kosten.
    cache = "anker_h_2026_08_30.json"
    if os.path.exists(cache):
        anker = json.loads(io.open(cache, encoding="utf-8").read())
        print("%d Anker aus dem Zwischenspeicher." % len(anker))
    else:
        anker = anker_mit_bewegung()
        io.open(cache, "w", encoding="utf-8").write(json.dumps(anker))
        print("Anker zwischengespeichert -> %s" % cache)
    rng = np.random.default_rng(20260830)
    tage = je_tag(anker)
    n_h = sum(1 for a in anker if a["h"])
    print()
    print("=" * 92)
    print("H ALS REGEL — was aendert 'nimm bevorzugt H' an echten Einstiegen?")
    print("=" * 92)
    print("%d Anker, davon %d mit H (%.1f %%), %d Kalendertage"
          % (len(anker), n_h, 100 * n_h / len(anker), len(tage)))
    print("Mass: Bewegung in R ueber %d Tage. Vergleich: quotengleicher Zufall"
          % HORIZONT)
    print()
    print("  %-16s %10s   %s" % ("Ausschnitt", "H-Anker", "H minus quotengleicher Zufall"))
    for name, von, bis in (("gesamt", "2000-01-01", "2099-12-31"),) + ABSCHNITTE:
        teil = {t: z for t, z in tage.items() if von <= t <= bis}
        if len(teil) < 100:
            print("  %-16s zu wenige Tage" % name)
            continue
        h_zahl = sum(1 for z in teil.values() for a in z if a["h"])
        print("  %-16s %10d   " % (name, h_zahl), end="")
        MB.urteil_tage("", wirkung(teil, rng), rng, BLOCK)

    print()
    print("### Beide Haelften (Massnahme 11) ###")
    sortiert = sorted(tage)
    mitte = sortiert[len(sortiert) // 2]
    for name, bed in (("erste Haelfte", lambda t: t < mitte),
                      ("zweite Haelfte", lambda t: t >= mitte)):
        teil = {t: z for t, z in tage.items() if bed(t)}
        print("  %-16s " % name, end="")
        MB.urteil_tage("", wirkung(teil, rng), rng, BLOCK)

    print()
    print("### Je Marktphase (Massnahme 15) ###")
    for phase in ("bulle", "seitwaerts", "baer"):
        teil = {t: [a for a in z if a["phase"] == phase] for t, z in tage.items()}
        teil = {t: z for t, z in teil.items() if len(z) >= 8}
        if len(teil) < 100:
            print("  %-16s zu wenige Tage" % phase)
            continue
        print("  %-16s " % phase, end="")
        MB.urteil_tage("", wirkung(teil, rng), rng, BLOCK)

    print()
    print("### POSITIVKONTROLLE — welche Merkmalsguete faende diese Messung? ###")
    for guete in (0.0, 1.0, 3.0, 6.0, 12.0):
        w = wirkung(tage, rng, pflanze_guete=max(guete, 1e-9))
        print("  Rauschen x%-5.1f " % guete, end="")
        MB.urteil_tage("", w, rng, BLOCK)

    print()
    print("=" * 92)
    print("DASSELBE MIT DEM MASS, FUER DAS H GEBAUT IST: 'Ziel vor Stop'")
    print("=" * 92)
    print("⚠️ H prueft die BARRIEREN (Weg frei bis zum Ziel, Stop gedeckt).")
    print("   Traegt es hier, aber nicht in R, beschreibt es die GEOMETRIE -")
    print("   und die steckt bereits im Nullpunkt 1/(1+CRV).")
    print()
    for name, von, bis in (("gesamt", "2000-01-01", "2099-12-31"),) + ABSCHNITTE:
        teil = {t: z for t, z in tage.items() if von <= t <= bis}
        if len(teil) < 100:
            continue
        print("  %-16s " % name, end="")
        MB.urteil_tage("", wirkung(teil, rng, feld="ziel"), rng, BLOCK)
    print()
    for name, bed in (("erste Haelfte", lambda t: t < mitte),
                      ("zweite Haelfte", lambda t: t >= mitte)):
        teil = {t: z for t, z in tage.items() if bed(t)}
        print("  %-16s " % name, end="")
        MB.urteil_tage("", wirkung(teil, rng, feld="ziel"), rng, BLOCK)

    print()
    print("### SURVIVORSHIP (Massnahme 12) ###")
    # ⚠️ ERSTE FASSUNG WAR SINNLOS: alle 523 Symbole haben H-Anker, die
    # Vergleichsgruppe war leer. Die richtige Frage ist nicht "welche
    # Symbole", sondern "haeufen sich H-Anker bei den Ueberlebenden?".
    reihen = B.lade()
    anteil = {}
    for a in anker:
        t, h = anteil.get(a["sym"], (0, 0))
        anteil[a["sym"]] = (t + 1, h + (1 if a["h"] else 0))
    ueberlebt, gefallen = [], []
    for sym, (t, h) in anteil.items():
        z = reihen.get(sym)
        if not z or t < 100:
            continue
        (gefallen if z[-1][1] < z[200][1] else ueberlebt).append(100.0 * h / t)
    print("  H-Anteil bei Reihen, die HOEHER enden : %.2f %% (%d Reihen)"
          % (st.mean(ueberlebt) if ueberlebt else float("nan"), len(ueberlebt)))
    print("  H-Anteil bei Reihen, die TIEFER enden : %.2f %% (%d Reihen)"
          % (st.mean(gefallen) if gefallen else float("nan"), len(gefallen)))
    print("  -> %s"
          % ("⚠️ H haeuft sich bei den Ueberlebenden - Auswahleffekt moeglich"
             if ueberlebt and gefallen
             and st.mean(ueberlebt) > 1.3 * st.mean(gefallen)
             else "kein auffaelliger Unterschied"))


if __name__ == "__main__":
    main()
