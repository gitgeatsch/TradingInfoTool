# -*- coding: utf-8 -*-
"""Verwendung 4 — traegt H als KONDITIONALER FILTER? (30.08.2026)

## Warum diese Messung ueberhaupt noetig wurde

Nutzerfrage: *"ob und wie realistisch die von dir vorgeschlagene Verwendung
ist - erklaere mir wie du die 'Tagesebene' meinst, wir haben keine Trades
welche fuer nur einen Tag relevant sind."*

Die Frage deckte zwei Fehler auf, beide in MEINER Messanlage, nicht in H.

⚠️ FEHLER 1 - DIE FALSCHE VERWENDUNG GEMESSEN. Verwendung 1 fragte, ob ein
H-Asset besser laeuft als andere Assets DESSELBEN Tages. Das System stellt
diese Frage nirgends: die Auswahl zwischen Assets macht `auswahl.py` (A1)
ueber die Jahresentwicklung, und H kommt dort nicht vor. H sitzt
ausschliesslich in `rollen_lauf.py` Stufe 11 - und die entscheidet je Asset
ABSOLUT gegen eine feste Schwelle (`potential.traegt`, 0,010 R).

⚠️ FEHLER 2 - MARKTBEREINIGT, WO ES NICHT HINGEHOERT. Verwendung 2 zog den
Tagesmedian ab. Das beantwortet "ist H etwas ANDERES als der Markt" - eine
saubere Frage, aber nicht die des Systems. Das System fragt "NUETZT es".
Ein 200-Tage-Trendfilter ist ebenfalls "nur Markt" und nuetzt trotzdem,
weil er schlechte Phasen meidet. Wer den Markteffekt herausrechnet, nimmt
einem Marktfilter genau das weg, wofuer er da ist.

## Die Lehrmeinung dazu (Recherche 30.08.2026)

    "You should not ask a CS signal to forecast absolute direction, and
     should not ask a TS signal to explain cross-sectional premia."
     - QuantPedia / JIN System Architect zur TS-CS-Trennung

H ist per Konstruktion ein TIME-SERIES-Signal: boolesch (A UND B), an Stop
und Ziel DIESES Trades gebunden, kein Rangwert. Die Gattung heisst in der
Praxis "Entry Filter" - ein konditionaler Torwaechter, der eine Einladung
annimmt oder ablehnt, nicht ein Score, der Kandidaten sortiert.

Verwendung 1 hat einen TS-Filter cross-sectional getestet. Genau der Test,
den die Lehrmeinung ausschliesst.

## Was hier gemessen wird

    "Sind die Anker, die H durchlaesst, besser als die, die das System
     sonst genommen haette - auf der Zeitachse, ohne Marktbereinigung?"

## ⚠️ Die Gegenprobe, die ueber den Wert entscheidet

Wenn H nur ein Marktfilter ist, dann muss es sich gegen den Marktfilter
behaupten, den das System SCHON HAT: BTC ueber/unter seinem 200-Schnitt
(`auswahl.py` A1b, dort als Schatten). Deshalb die 2x2-Tafel:

           |  BTC ueber 200   |  BTC unter 200
    H ja   |       ?          |       ?
    H nein |       ?          |       ?

Traegt H INNERHALB beider Schichten, ist es mehr als der 200-Schnitt.
Traegt es nur in einer, ist es ein Mitlaeufer dieser Schicht.
Traegt es in keiner, war der ganze Effekt der 200-Schnitt.

## Vorab festgelegt, VOR der ersten Zahl

  traegt als Filter   Vorsprung positiv, Bootstrap ueber Zeitbloecke
                      schliesst die Null nicht ein, UND er bleibt in
                      BEIDEN 200-Schnitt-Schichten bestehen
  Mitlaeufer          nur in einer Schicht
  traegt nicht        in keiner - die Positivkontrolle muss dann zeigen,
                      dass ein Effekt dieser Groesse gefunden worden waere
"""
import io
import json
import sqlite3
import statistics as st
import sys

import numpy as np

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

CACHE = "anker_h_2026_08_30.json"
DB = "file:data/messdaten.db?mode=ro"
BLOCK = 120          # > Horizont 20, und ergibt genug Bloecke fuer den Bootstrap
ZIEHUNGEN = 20000
SCHNITT = 200
MIND_JE_GRUPPE = 30
PLACEBO_LAEUFE = 40
ABSCHNITTE = (("2018-2020", "2018-01-01", "2020-12-31"),
              ("2021-2023", "2021-01-01", "2023-12-31"),
              ("2024-2026", "2024-01-01", "2026-12-31"))


def btc_ueber_schnitt():
    """Je Kalendertag: steht BTC ueber seinem 200-Tage-Schnitt?

    ⚠️ NUR RUECKWAERTS - der Schnitt der Tage i-200 .. i-1, der Kurs von i.
    Ein Schnitt, der den heutigen Kurs enthaelt, waere ein Blick nach vorn.
    """
    c = sqlite3.connect(DB, uri=True)
    reihe = [(t[:10], float(k)) for t, k in c.execute(
        "SELECT date, close FROM price_history_ohlc "
        "WHERE symbol='BTC' AND currency='USD' AND close IS NOT NULL "
        "AND close > 0 ORDER BY date")]
    c.close()
    tage = [t for t, _ in reihe]
    kurs = np.array([k for _, k in reihe])
    aus = {}
    for i in range(SCHNITT, len(kurs)):
        aus[tage[i]] = bool(kurs[i] > kurs[i - SCHNITT:i].mean())
    return aus


def bloecke(anker, feld, bedingung, block=BLOCK):
    """Je Zeitblock: Lagemass(H-Anker) minus Lagemass(Nicht-H-Anker).

    ⚠️ DER VERGLEICH FINDET IM BLOCK STATT, nicht ueber die Bloecke hinweg.
    Sonst vergleicht man 2019er H-Anker mit 2025er Nicht-H-Ankern, und die
    Marktphase erklaert alles. Gebootstrapt werden erst die Blockwerte.

    ⚠️ ZWEI MASSE, ZWEI LAGEMASSE - der erste Lauf hatte hier einen Fehler.
    `in_r` ist stetig und stark rechtsschief (2,68), dort ist der MEDIAN
    richtig. `ziel` ist 1/0 - "Ziel vor Stop, ja oder nein". Der Median
    einer 0/1-Reihe mit unter 50 % Treffern ist immer 0, die Differenz
    also immer exakt 0. Der erste Lauf meldete darum in ALLEN Bloecken
    +0,0000 und las das als "nicht trennbar" - es war gar keine Messung.
    Bei 0/1 ist das Lagemass die QUOTE, also der Mittelwert.
    """
    quote = (feld == "ziel")
    lagemass = (lambda x: float(np.mean(x))) if quote else st.median
    tage = sorted({a["datum"] for a in anker if bedingung(a)})
    if len(tage) < 2 * block:
        return None
    lage = {t: i // block for i, t in enumerate(tage)}
    je_block = {}
    for a in anker:
        if not bedingung(a):
            continue
        w = a.get(feld)
        if w is None:
            continue
        je_block.setdefault(lage[a["datum"]], ([], []))[0 if a["h"] else 1] \
            .append(float(w))
    werte = [lagemass(mit) - lagemass(ohne)
             for mit, ohne in je_block.values()
             if len(mit) >= MIND_JE_GRUPPE and len(ohne) >= MIND_JE_GRUPPE]
    return werte if len(werte) >= 5 else None


def urteil(titel, werte, rng, einheit="R", einzug=2):
    if werte is None:
        print("%s%-38s zu wenige Bloecke" % (" " * einzug, titel))
        return None
    b = np.array(werte)
    n = len(b)
    boot = np.array([b[rng.integers(0, n, n)].mean() for _ in range(ZIEHUNGEN)])
    u, o = np.quantile(boot, [0.025, 0.975])
    wort = ("TRAEGT" if u > 0 else ("UMGEKEHRT" if o < 0 else "nicht trennbar"))
    print("%s%-38s %+.4f %s [%+.4f .. %+.4f]  %2d/%2d Bloecke +  %s"
          % (" " * einzug, titel, b.mean(), einheit, u, o,
             int((b > 0).sum()), n, wort))
    return u > 0


def main():
    anker = json.loads(io.open(CACHE, encoding="utf-8").read())
    ueber = btc_ueber_schnitt()
    rng = np.random.default_rng(20260830)
    n_h = sum(1 for a in anker if a["h"])

    print("=" * 100)
    print("VERWENDUNG 4 — TRAEGT H ALS KONDITIONALER FILTER AUF DER ZEITACHSE?")
    print("=" * 100)
    print("%d Anker, davon %d mit H (%.1f %%), %d Symbole, %s .. %s"
          % (len(anker), n_h, 100 * n_h / len(anker),
             len({a["sym"] for a in anker}),
             min(a["datum"] for a in anker), max(a["datum"] for a in anker)))
    print("Blocklaenge %d Kalendertage (> Horizont 20), Vergleich JE BLOCK."
          % BLOCK)
    print("KEINE Marktbereinigung - der Markteffekt gehoert zu dem, was ein")
    print("Filter liefert. Genau darum die 200-Schnitt-Gegenprobe unten.")

    for feld, klar, einheit in (("in_r", "BEWEGUNG IN R", "R"),
                                ("ziel", "ZIEL VOR STOP (H's eigenes Mass)", " ")):
        print()
        print("-" * 100)
        print("  %s" % klar)
        print("-" * 100)
        urteil("gesamt", bloecke(anker, feld, lambda a: True), rng, einheit)
        for name, von, bis in ABSCHNITTE:
            urteil(name, bloecke(
                anker, feld,
                lambda a, v=von, b=bis: v <= a["datum"] <= b),
                rng, einheit, einzug=4)

    print()
    print("=" * 100)
    print("⚠️ DIE GEGENPROBE — IST H MEHR ALS DER 200-SCHNITT, DEN WIR SCHON HABEN?")
    print("=" * 100)
    fehlt = sum(1 for a in anker if a["datum"] not in ueber)
    print("  %d Anker ohne 200-Schnitt-Wert (%.1f %%) - fallen heraus."
          % (fehlt, 100 * fehlt / len(anker)))
    print()
    for feld, klar, einheit in (("in_r", "BEWEGUNG IN R", "R"),
                                ("ziel", "ZIEL VOR STOP", " ")):
        print("  %s" % klar)
        for lage, name in ((True, "BTC UEBER 200-Schnitt"),
                           (False, "BTC UNTER 200-Schnitt")):
            urteil(name, bloecke(
                anker, feld,
                lambda a, L=lage: ueber.get(a["datum"]) is L), rng, einheit, 4)
        print()

    print("=" * 100)
    print("POSITIVKONTROLLE — welche Effektgroesse findet diese Messung?")
    print("=" * 100)
    print("  ⚠️ ZWEI FRAGEN, NICHT EINE. Erstens: verschiebt sich der")
    print("  Punktschaetzer um genau den gepflanzten Betrag? Dann ist die")
    print("  Messung UNVERZERRT. Zweitens: ab welchem Betrag verlaesst das")
    print("  Intervall die Null? Das ist die AUFLOESUNGSGRENZE - Nullbefunde")
    print("  darunter sagen 'nichts gesehen', nicht 'nichts da'.")
    print()
    print("  BEWEGUNG IN R")
    roh = bloecke(anker, "in_r", lambda a: True)
    basis = wert_in_r = float(np.mean(roh))
    for staerke in (0.02, 0.05, 0.10, 0.20, 0.40):
        gepflanzt = [{**a, "in_r": a["in_r"] + (staerke if a["h"] else 0.0)}
                     for a in anker]
        w = bloecke(gepflanzt, "in_r", lambda a: True)
        urteil("gepflanzt %+.2f R  (Versatz %+.3f)"
               % (staerke, float(np.mean(w)) - basis), w, rng, einzug=4)

    print()
    print("  ZIEL VOR STOP — Quote angehoben")
    roh_z = bloecke(anker, "ziel", lambda a: True)
    basis_z = wert_ziel = float(np.mean(roh_z))
    for p in (0.01, 0.02, 0.05, 0.10):
        gepflanzt = [
            {**a, "ziel": (1.0 if (a["h"] and a["ziel"] == 0.0
                                   and rng.random() < p) else a["ziel"])}
            for a in anker]
        w = bloecke(gepflanzt, "ziel", lambda a: True)
        urteil("Quote +%.0f %% der H-Stops -> Ziel (Versatz %+.4f)"
               % (100 * p, float(np.mean(w)) - basis_z), w, rng, " ", 4)

    print()
    print("=" * 100)
    print("⚠️ NEGATIVKONTROLLE — DAS PLACEBO-BAND AUS %d ZIRKULAEREN VERSAETZEN"
          % PLACEBO_LAEUFE)
    print("=" * 100)
    print("  ⚠️ DER ERSTE LAUF HATTE HIER EINEN KONSTRUKTIONSFEHLER: EIN")
    print("  einzelner Versatz. Der ist selbst eine Zufallsziehung - er lieferte")
    print("  bei einem RNG-Zustand +0,0048 ('liegt bei null') und bei einem")
    print("  anderen +0,0834 ('TRAEGT'). Eine Kontrolle, deren Urteil vom")
    print("  Zufallsstartwert abhaengt, kontrolliert nichts.")
    print()
    print("  Richtig ist die VERTEILUNG vieler Versaetze. Zirkulaer, nicht frei")
    print("  gemischt: der freie Placebo zerstoert die Autokorrelation und")
    print("  liefert eine zu enge Schwelle (Methodik 2.47).")
    print()
    je_sym = {}
    for a in anker:
        je_sym.setdefault(a["sym"], []).append(a)
    sortiert = {s: sorted(z, key=lambda x: x["datum"]) for s, z in je_sym.items()}
    for feld, klar, echt in (("in_r", "BEWEGUNG IN R", wert_in_r),
                             ("ziel", "ZIEL VOR STOP", wert_ziel)):
        placebo = []
        for _ in range(PLACEBO_LAEUFE):
            versetzt = []
            for z in sortiert.values():
                marken = [x["h"] for x in z]
                v = int(rng.integers(0, max(len(marken), 1)))
                for x, h in zip(z, marken[v:] + marken[:v]):
                    versetzt.append({**x, "h": h})
            w = bloecke(versetzt, feld, lambda a: True)
            if w:
                placebo.append(float(np.mean(w)))
        p = np.array(placebo)
        u, o = np.quantile(p, [0.025, 0.975])
        print("  %s" % klar)
        print("    Placebo-Band   %+.4f .. %+.4f   (Mitte %+.4f, %d Laeufe)"
              % (u, o, float(p.mean()), len(p)))
        print("    gemessen       %+.4f   ->  %s"
              % (echt, "AUSSERHALB des Bandes - der Befund haelt"
                 if (echt < u or echt > o) else
                 "⚠️ INNERHALB des Bandes - vom Zufall nicht zu trennen"))
        print()


if __name__ == "__main__":
    main()
