# -*- coding: utf-8 -*-
"""Haengt die Rangfolge der Akkumulationsregeln an der MARKTRICHTUNG? (23.08.2026)

DIE FRAGE, DIE DER GESAMTLAUF NICHT BEANTWORTEN KANN.

`messe_akkumulation.py` hat am 11.08. gemessen und am 23.08. bestaetigt: die
Kontrolle HALBE_QUOTE (investiert stur die Haelfte, ohne hinzusehen) schlaegt
jede antizyklische Regel. Der Schluss dort lautete:

    "Der antizyklische Vorteil ist vollstaendig durch die Investitionsquote
     erklaert. Die Rangfolge ist eine Funktion der Marktrichtung im Zeitraum,
     nicht der Klugheit der Regel."

⚠️ DAS WAR EINE BEHAUPTUNG MIT EINEM BELEG AUS ZWEI AKTIEN. Sie stuetzte sich
darauf, dass bei PLTR und VST - den einzigen gestiegenen Reihen - DCA gewann.
n = 2.

UND DER GESAMTLAUF KANN SIE NICHT PRUEFEN: er integriert ueber die ganze Reihe.
Krypto liegt seit 2017 vor, ueberwiegend fallend; acht zusaetzliche Tage in
einer neuen Marktphase aendern an einem Neunjahresmittel nichts. Wer fragt, ob
die Rangfolge in einer steigenden Phase kippt, muss die Reihe ZERLEGEN.

DER AUFBAU, und was daran vorab festgelegt ist (Suchpreis, Methodik 2.x):

    Fenster      104 Kauftermine = zwei Jahre woechentlich, NICHT ueberlappend
    Etikett      Rendite des Werts ueber das Fenster: > 0 steigend, sonst fallend
    Mass         Endwert je bereitgestelltem EUR INNERHALB des Fensters
    Historie     die Regel sieht weiterhin die ganze Vergangenheit
                 (200-Tage-Schnitt, 1-Jahres-Hoch) - nur die KAUFTAGE sind
                 eingegrenzt

⚠️ DAS ETIKETT IST BESCHREIBEND, KEINE HANDELSREGEL. Es benutzt die Rendite des
Fensters, die man zu Beginn nicht kennt. Das ist erlaubt, weil hier nichts
gehandelt wird: die Frage lautet "WENN der Markt gestiegen ist, welche Regel
lag dann vorn", nicht "woran erkenne ich das vorher". Wer daraus eine
Handelsregel macht, hat Lookahead gebaut.

DIE ZWEI FRAGEN, GETRENNT - und das ist der eigentliche Punkt:

    QUOTE   schlaegt eine Regel das DCA?          - vermischt Timing und Quote
    TIMING  schlaegt eine Regel die KONTROLLE?    - Quote herausgerechnet

Die Kontrolle HALBE_QUOTE investiert konstant die Haelfte. Eine antizyklische
Regel, die SIE schlaegt, hat etwas geleistet, was blosses Zurueckhalten nicht
erklaert. Genau das ist die Frage, die 7.27 offen liess.

POSITIVKONTROLLE (Methodik 2.58/2.59): das Vorzeichen der Kontrolle MUSS
drehen - in fallenden Fenstern schlaegt HALBE_QUOTE das DCA, in steigenden
verliert sie. Dreht es nicht, ist die Zerlegung kaputt und kein Ergebnis
belastbar.

EINE Definition der Regeln: `messe_akkumulation.anteil_der_regel()`. Zwei
Kopien wuerden auseinanderlaufen, und der Unterschied saehe aus wie ein Befund.
"""
from __future__ import annotations

import argparse
from collections import defaultdict

import numpy as np

from messe_akkumulation import (BUDGET, PERIODE, VORLAUF, _kosten,
                                anteil_der_regel, simuliere)

# Der quotengleiche Zufall (23.08.2026) - ohne ihn misst auch dieses Werkzeug
# noch die Quote. Feste Saat: dieselbe Zahl bei jedem Lauf.
ZUFALL_WDH = 20
SAAT = 20260823

REGELN = ("DCA", "HALBE_QUOTE", "UNTER_SMA", "RUECKGANG", "GESTAFFELT")
KONTROLLE = "HALBE_QUOTE"
FENSTER_TERMINE = 104          # zwei Jahre woechentlich
MINDEST_TERMINE = 52           # ein Restfenster unter einem Jahr zaehlt nicht


def fenster(n: int) -> list[tuple[int, int]]:
    """Nicht ueberlappende Kauffenster als (von, bis) in Indexform."""
    aus = []
    laenge = FENSTER_TERMINE * PERIODE
    i = VORLAUF
    while i + MINDEST_TERMINE * PERIODE <= n:
        aus.append((i, min(i + laenge, n)))
        i += laenge
    return aus


def zufall_gleiche_quote(c, klasse, regel, schwelle, von, bis, rng):
    """Dieselben Betraege, dieselbe Anzahl Kauftage - ZUFAELLIG platziert.

    ⚠️ WARUM DAS DIE EIGENTLICHE KONTROLLE IST. Jeder Vergleich gegen DCA
    oder gegen HALBE_QUOTE vermischt zwei Dinge: WIEVIEL investiert wird und
    WANN. In einem fallenden Fenster gewinnt jede Regel, die zurueckhaelt; in
    einem steigenden jede, die frueh kauft. Beides ist Quote, kein Timing.

    Diese Kontrolle haelt die Quote FEST und wuerfelt nur die Tage. Was eine
    Regel gegen sie gewinnt, kann sie nur durch die WAHL DER TAGE gewonnen
    haben - und genau das behauptet "antizyklisch kaufen"."""
    termine = list(range(max(von, VORLAUF), bis, PERIODE))
    einsaetze = []
    bar = 0.0
    for i in termine:
        bar += BUDGET
        e = min(bar, BUDGET * anteil_der_regel(c, i, regel, schwelle))
        einsaetze.append(e)
        bar -= e
    reserve = bar
    aktiv = [e for e in einsaetze if e > 0]
    if not aktiv:
        return float("nan")
    ergebnisse = []
    for _ in range(ZUFALL_WDH):
        tage = rng.choice(len(termine), size=len(aktiv), replace=False)
        stuecke = 0.0
        for e, t_ in zip(aktiv, sorted(tage)):
            netto = e - _kosten(klasse, e)
            if netto > 0:
                stuecke += netto / c[termine[t_]]
        ergebnisse.append(stuecke * float(c[bis - 1]) + reserve)
    return float(np.mean(ergebnisse))


def main() -> int:
    import config

    from backtest_llm1_historisch import lade_reihen_aus_db

    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--db", default="data/tradinginfotool.db")
    p.add_argument("--schwelle", type=float, default=0.20)
    args = p.parse_args()

    klasse_von = {a.symbol: a.assetklasse for a in config.get_watchlist()}
    reihen = lade_reihen_aus_db(args.db)
    reihen = {s: r for s, r in reihen.items() if s in klasse_von}

    # (klasse, phase) -> regel -> Liste der Fensterergebnisse
    topf: dict = defaultdict(lambda: defaultdict(list))
    schlaegt: dict = defaultdict(lambda: defaultdict(lambda: [0, 0]))
    # Die eigentliche Timing-Frage: jede Regel gegen IHREN EIGENEN
    # quotengleichen Zufall.
    timing: dict = defaultdict(lambda: defaultdict(lambda: [0, 0]))
    vorsprung: dict = defaultdict(lambda: defaultdict(list))
    rng = np.random.RandomState(SAAT)
    fenster_zahl = 0

    for sym, r in reihen.items():
        c = np.array([k.close for k in r], dtype=float)
        if len(c) < VORLAUF + MINDEST_TERMINE * PERIODE:
            continue
        kl = klasse_von[sym]
        for von, bis in fenster(len(c)):
            rendite = c[bis - 1] / c[von] - 1.0
            phase = "steigend" if rendite > 0 else "fallend"
            termine = len(range(von, bis, PERIODE))
            gesamt = BUDGET * termine
            werte = {}
            for regel in REGELN:
                endwert, _inv, _n, _s = simuliere(c, kl, regel, args.schwelle,
                                                  von=von, bis=bis)
                werte[regel] = endwert / gesamt
                topf[(kl, phase)][regel].append(werte[regel])
            for regel in REGELN:
                for gegen in ("DCA", KONTROLLE):
                    if regel == gegen:
                        continue
                    z = schlaegt[(kl, phase, gegen)][regel]
                    z[1] += 1
                    z[0] += 1 if werte[regel] > werte[gegen] else 0
            for regel in REGELN:
                zufall = zufall_gleiche_quote(c, kl, regel, args.schwelle,
                                              von, bis, rng) / gesamt
                if zufall == zufall:              # nicht NaN
                    z2 = timing[(kl, phase)][regel]
                    z2[1] += 1
                    z2[0] += 1 if werte[regel] > zufall else 0
                    vorsprung[(kl, phase)][regel].append(werte[regel] - zufall)
            fenster_zahl += 1

    print(f"{len(reihen)} Symbole · {fenster_zahl} nicht ueberlappende "
          f"Fenster a {FENSTER_TERMINE} Kauftermine · {BUDGET:.0f} EUR je "
          f"Termin\nMass: Endwert je bereitgestelltem EUR IM FENSTER\n")

    print(f"{'Klasse':10} {'Phase':10} {'k':>4} "
          + " ".join(f"{r:>12}" for r in REGELN))
    print("-" * 78)
    for kl, phase in sorted(topf):
        z = topf[(kl, phase)]
        k = len(z["DCA"])
        print(f"{kl:10} {phase:10} {k:4} "
              + " ".join(f"{np.mean(z[r]):12.3f}" for r in REGELN))

    for gegen in ("DCA", KONTROLLE):
        print(f"\nWie oft schlaegt die Regel {gegen}? (je Fenster)")
        print(f"{'Klasse':10} {'Phase':10} "
              + " ".join(f"{r:>12}" for r in REGELN if r != gegen))
        for kl, phase in sorted(topf):
            zeile = []
            for r in REGELN:
                if r == gegen:
                    continue
                a, b = schlaegt[(kl, phase, gegen)][r]
                zeile.append(f"{a:4}/{b:<3} {100*a/b if b else 0:3.0f}%")
            print(f"{kl:10} {phase:10} " + " ".join(f"{s:>12}" for s in zeile))

    print("")
    print("⚠️ DIE TIMING-FRAGE: schlaegt die Regel ihren EIGENEN "
          "quotengleichen Zufall?")
    print("   (gleiche Betraege, gleiche Anzahl Kauftage, nur die TAGE "
          "gewuerfelt)")
    print(f"{'Klasse':10} {'Phase':10} " + " ".join(f"{r:>14}" for r in REGELN))
    for kl, phase in sorted(topf):
        zeile = []
        for r in REGELN:
            a, b = timing[(kl, phase)][r]
            d = np.mean(vorsprung[(kl, phase)][r]) if b else float("nan")
            zeile.append(f"{100*a/b if b else 0:3.0f}% {d:+.3f}")
        print(f"{kl:10} {phase:10} " + " ".join(f"{s:>14}" for s in zeile))

    # POSITIVKONTROLLE: das Vorzeichen der Kontrolle muss drehen.
    print("\nPOSITIVKONTROLLE - dreht das Vorzeichen der Kontrolle?")
    for kl in sorted({k for k, _ in topf}):
        z = []
        for phase in ("fallend", "steigend"):
            t = topf.get((kl, phase))
            if not t:
                z.append((phase, None))
                continue
            z.append((phase, np.mean(t[KONTROLLE]) - np.mean(t["DCA"])))
        beschreibung = " · ".join(
            f"{p}: {('%+.3f' % v) if v is not None else 'kein Fenster'}"
            for p, v in z)
        werte = [v for _, v in z if v is not None]
        ok = len(werte) == 2 and werte[0] > 0 > werte[1]
        print(f"   {kl:10} {beschreibung:44} "
              f"{'BESTANDEN' if ok else 'nicht erfuellt'}")
    print("\n⚠️ Das Phasen-Etikett benutzt die Fensterrendite und ist deshalb "
          "BESCHREIBEND.\n   Es ist keine Handelsregel - wer daraus eine "
          "macht, hat Lookahead gebaut.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
