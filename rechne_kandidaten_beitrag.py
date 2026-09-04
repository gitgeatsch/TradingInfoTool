# -*- coding: utf-8 -*-
"""N-17c: die BEITRAGSTABELLEN der Frontloading-Kandidaten (04.09.2026)

Vorabfestlegung: `Anforderungen_Umbau_28_08.md` 9.6, Abschnitt N-17c -
geschrieben, BEVOR gerechnet wurde. Kurzfassung:

## Die Luecke, die geschlossen wird

9.6 verlangt fuer H-4 *„das Verfahren, mit dem Funding und Turnover
aufgenommen wurden"*. Das hat DREI Schritte; bei den Frontloading-
Kandidaten (F-165, F-209) ist nur der erste gegangen:

    1 Wirkung als Regel      ✔ gemessen
    2 Beitragspunkte         ✖ FEHLT  <- diese Datei
    3 Schwelle kalibrieren   ✖ fehlt  (erst danach, und nur bei Erfolg)

⚠️⚠️ WARUM SCHRITT 2 FEHLTE, und es ist inhaltlich: die Umrechnung
`d(quote) = d(Potential)/(1+CRV)` setzt eine Wirkung in **R** voraus.
`messe_form_kurz_gegen_lang._ziel()` liefert bei ZIEL="frontloading" aber
einen ANTEIL (0..1). Das „R" in F-165s und F-209s Tabellen ist eine
mitgeschleppte Beschriftung aus der H-1-Fassung, KEINE Einheit. Es gab
damit bis heute keine Bruecke von „Frontloading traegt" zu einer
Schwellenaussage.

## Die zwei Aussagen, die nicht dasselbe sind

    Frontloading traegt   die Bewegung ist frueh konzentriert - wie
                          schnell, nicht wohin   -> HORIZONTWAHL
    R-Beitrag traegt      der Ausgang ist besser -> POTENTIAL, SCHWELLE

## Vorab festgelegt - was als Befund gilt

    NUTZBAR        die Stufen sind MONOTON ueber die fuenf Fuenftel
                   UND die Spanne (Fuenftel 0 gegen 4) ist groesser null
                   UND die Kontrollgroesse `zufall` bleibt flach
    NICHT NUTZBAR  sonst - dann wird NICHT registriert und KEINE Schwelle
                   gerechnet

⚠️ An genau dieser Monotonie ist der Schnittabstand am 31.08. gescheitert
(+1,27/+1,59/...) - und ich hatte ihn trotzdem registriert.

## ⚠️ Die eingebaute GEGENPRUEFUNG

`turnover` auf H2 ist in F-203 bereits mit dem BESTEHENDEN Werkzeug
gerechnet worden: (+0,34 / +0,08 / +0,15 / -0,25 / -0,32). Diese Datei
rechnet dieselbe Zelle mit und vergleicht. Weicht sie ab, stimmt etwas am
AUFBAU dieser Datei - dann gilt kein Befund darunter.

Damit steht die Fuenftel-Rechnung hier gegen eine unabhaengige, bereits
produktiv verwendete Implementierung (`rechne_turnover_beitrag.py`) -
statt gegen sich selbst.

## ⚠️ Was diese Datei NICHT entscheidet

1. Ob registriert wird. R-R9 verlangt bei jedem Beitragswechsel eine
   Neukalibrierung der Schwelle; die Vorgabe (0,080) ist Nutzerentscheidung.
2. Den Gabelpunkt aus F-164 (H-2).
3. Die Richtung - alle Kandidaten sagen Ausmass/Tempo (F-165).

## Betriebsrahmen

Nur lokale SQLite-Lesevorgaenge, keine API-Abrufe.

    python rechne_kandidaten_beitrag.py [--horizonte 2,3]
"""
from __future__ import annotations

import argparse as _ap
import statistics as st
import sys

import numpy as np

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import messe_bewertungskennzahl as MB                          # noqa: E402
import messe_eigenschaft_beitrag as B                          # noqa: E402
import messe_funding_niveau as F                               # noqa: E402
import messe_kandidaten_als_regel as K                         # noqa: E402

CRV = 2.0
MIND_JE_TAG = 15          # dieselbe Schwelle wie `rechne_turnover_beitrag`

# ⚠️ VORAB BENANNT (Suchpreis 2.49): 7 Kandidaten x 2 Horizonte = 14 Zellen.
# Die Entscheidung haengt an `turnover` - dem staerksten und am wenigsten
# redundanten Fund (F-205); die uebrigen laufen als Einordnung mit.
KANDIDATEN = (
    ("turnover", "menge"),
    ("vola", None),
    ("momentum_kurz", None),
    ("schnitt50", None),
    ("rsi", None),
    ("oi_aenderung", "oi"),
    ("funding_extrem", "funding"),
    ("zufall", None),          # ⚠️ KONTROLLGROESSE - muss flach bleiben
)

# F-203, mit `rechne_turnover_beitrag.py --horizont 2` gerechnet.
KONTROLLE_TURNOVER_H2 = (+0.34, +0.08, +0.15, -0.25, -0.32)


def beitragstabelle(je_tag: dict) -> tuple[list, list, float]:
    """DIE EINE Fuenftel-Rechnung - dieselbe Form wie `rechne_funding_
    beitrag.py` / `rechne_turnover_beitrag.py`.

    Je Kalendertag Fuenftel bilden (Tagesklammer - die Marktlage wird
    festgehalten), Median je Fuenftel, dann ueber die Tage mitteln.
    Rueckgabe: (Bewegung je Fuenftel in R, Punkte GESCHRUMPFT, Spanne).
    """
    sammel: dict = {k: [] for k in range(5)}
    for z in je_tag.values():
        if len(z) < MIND_JE_TAG:
            continue
        w = np.array([x["kennzahl"] for x in z], float)
        y = np.array([x["in_r"] for x in z], float)
        r = np.argsort(np.argsort(w)) / max(len(w) - 1, 1)
        for k in range(5):
            m = (r >= k / 5) & (r < (k + 1) / 5 if k < 4 else r <= 1.0)
            if m.sum() >= 2:
                sammel[k].append(float(np.median(y[m])))
    if any(not sammel[k] for k in range(5)):
        return [], [], 0.0
    werte = [st.mean(sammel[k]) for k in range(5)]
    mittel = st.mean(werte)
    faktor = 1.0 / (1.0 + CRV)
    # ⚠️ GESCHRUMPFT (halbiert) - in-sample kalibriert, dieselbe Vorsicht
    # wie bei `trefferbilanz.geschrumpft()` und bei Funding/Turnover.
    punkte = [round(100.0 * (werte[k] - mittel) * faktor / 2.0, 2)
              for k in range(5)]
    spanne = 100.0 * (werte[0] - werte[4]) * faktor / 2.0
    return werte, punkte, spanne


def urteil(punkte: list, spanne: float) -> tuple[bool, str]:
    """Die VORAB festgelegte Bedingung - keine nachtraegliche Auslegung."""
    if not punkte:
        return False, "zu duenn"
    fallend = all(punkte[k] >= punkte[k + 1] for k in range(4))
    steigend = all(punkte[k] <= punkte[k + 1] for k in range(4))
    if not (fallend or steigend):
        return False, "NICHT MONOTON"
    if abs(spanne) <= 0.0:
        return False, "Spanne null"
    return True, "nutzbar"


def main() -> int:
    p = _ap.ArgumentParser()
    p.add_argument("--horizonte", default="2,3")
    horizonte = [int(x) for x in p.parse_known_args()[0].horizonte.split(",")]

    print("Lade Reihen und Zusatzquellen...", flush=True)
    reihen = B.lade()
    quellen = {
        "menge": MB.reihe("data/onchain_historie.db", "splycur"),
        "funding": F.lade_funding(),
        "oi": K.lade_terminmarkt()["oi_aenderung"],
    }
    print("%d Krypto-Reihen (F-204-gefiltert)" % len(reihen))

    ergebnisse: dict = {}
    for hor in horizonte:
        print()
        print("#" * 88)
        print("# HORIZONT H%d   —   CRV %.1f, Punkte GESCHRUMPFT (halbiert)" % (hor, CRV))
        print("#" * 88)
        print()
        print("  %-16s %7s  %-38s %8s  %s"
              % ("Kandidat", "Tage", "Punkte je Fuenftel (0..4)", "Spanne", "URTEIL"))
        for art, quelle in KANDIDATEN:
            je_tag = K.baue(reihen, art, quellen.get(quelle), horizont=hor)
            tage = sum(1 for z in je_tag.values() if len(z) >= MIND_JE_TAG)
            werte, punkte, spanne = beitragstabelle(je_tag)
            ok, grund = urteil(punkte, spanne)
            ergebnisse[(art, hor)] = (punkte, spanne, ok)
            if not punkte:
                print("  %-16s %7d  %s" % (art, tage, grund))
                continue
            marke = " ⚠️KONTROLLE" if art == "zufall" else ""
            print("  %-16s %7d  %-38s %+8.2f  %s%s"
                  % (art, tage,
                     " ".join("%+5.2f" % x for x in punkte),
                     spanne, "✔ nutzbar" if ok else "✖ " + grund, marke))

    # ---- DIE GEGENPRUEFUNGEN ------------------------------------------
    print()
    print("=" * 88)
    print("GEGENPRUEFUNG 1 — reproduziert diese Datei F-203s turnover H2?")
    print("=" * 88)
    hat_h2 = ("turnover", 2) in ergebnisse
    if not hat_h2:
        print("  H2 nicht gerechnet - uebersprungen (mit --horizonte 2,3 laufen)")
    else:
        neu = ergebnisse[("turnover", 2)][0]
        print("  F-203 (rechne_turnover_beitrag.py --horizont 2):  %s"
              % " ".join("%+5.2f" % x for x in KONTROLLE_TURNOVER_H2))
        print("  diese Datei:                                      %s"
              % " ".join("%+5.2f" % x for x in neu))
        abw = max(abs(a - b) for a, b in zip(neu, KONTROLLE_TURNOVER_H2))
        print("  groesste Abweichung: %.2f Punkte" % abw)
        if abw > 0.10:
            print("  ⚠️⚠️ ABWEICHUNG > 0,10 - der AUFBAU dieser Datei stimmt")
            print("     nicht. KEIN Befund oben gilt, bevor das geklaert ist.")
        else:
            print("  ✔ deckt sich - die Fuenftel-Rechnung hier ist dieselbe")
            print("    wie in der produktiv verwendeten Implementierung.")

    print()
    print("=" * 88)
    print("GEGENPRUEFUNG 2 — bleibt die Kontrollgroesse `zufall` flach?")
    print("=" * 88)
    schlimm = False
    for hor in horizonte:
        e = ergebnisse.get(("zufall", hor))
        if not e or not e[0]:
            continue
        _, spanne, ok = e
        print("  H%-3d Spanne %+6.2f Punkte   %s"
              % (hor, spanne, "⚠️ NUTZBAR - das ist der Fehlalarm" if ok
                 else "✔ nicht nutzbar (erwartet)"))
        if ok:
            schlimm = True
    if schlimm:
        print()
        print("  ⚠️⚠️ DIE KONTROLLGROESSE IST NUTZBAR. Dann traegt das")
        print("     VERFAHREN, nicht der Kandidat - ALLE Befunde oben sind")
        print("     ungueltig, auch die positiven.")
    else:
        print("  ✔ Das Verfahren erzeugt keine nutzbare Tabelle aus dem Nichts.")

    print()
    print("=" * 88)
    print("BEFUND")
    print("=" * 88)
    nutzbar = [(a, h) for (a, h), (_, _, ok) in ergebnisse.items()
               if ok and a != "zufall"]
    if not nutzbar:
        print("  KEIN Kandidat erfuellt die vorab gesetzte Bedingung.")
        print("  -> nichts wird registriert, keine Schwelle wird gerechnet.")
    else:
        for a, h in sorted(nutzbar):
            print("  ✔ %s auf H%d — Stufen %s"
                  % (a, h, " ".join("%+5.2f" % x for x in ergebnisse[(a, h)][0])))
        print()
        print("  ⚠️ NICHT registrieren ohne R-R9: jeder Beitragswechsel")
        print("     verlangt eine Neukalibrierung der Schwelle, und die")
        print("     Vorgabe (0,080) ist eine NUTZERENTSCHEIDUNG.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
