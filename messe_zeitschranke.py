# -*- coding: utf-8 -*-
"""Was passiert wirklich mit Trades, die die Zeitschranke erreichen?

DIE ANNAHME, die hier ersetzt wird. Abschnitt 6.3 rechnet den Erwartungswert so:

    0,225 x 2R  +  0,565 x (-1R)  =  -0,115 R je Trade

Die dritte Gruppe - Faelle, die weder Ziel noch Stop erreichen - taucht darin
GAR NICHT auf. Sie werden damit implizit mit 0 R bewertet. Bei Horizont 20 sind
das 15 bis 21 % aller Faelle (7.22), also jeder sechste bis fuenfte Trade.

Das ist eine SETZUNG, keine Messung. Ein Trade, der die Zeitschranke erreicht,
wird dort geschlossen - zu irgendeinem Kurs, nicht bei null. Er kann bei +1,4 R
stehen oder bei -0,8 R. Beides ist nicht null, und beides ist messbar: der Kurs
steht in der Reihe.

WAS GERECHNET WIRD

    R = (Schlusskurs bei Zeitablauf - Einstieg) / Stopabstand

Der Stopabstand ist 1,5 ATR, also ist 1 R genau der Betrag, den ein
ausgestoppter Trade verliert. Ziel bei 3 ATR sind entsprechend +2 R. Damit sind
alle drei Gruppen in derselben Einheit.

WARUM DER MEDIAN MITGEHT: Ein Mittelwert kann von wenigen Ausreissern getragen
werden. Steht der Median deutlich anders, ist die Verteilung schief - und dann
sagt der Mittelwert wenig ueber den typischen Fall.

WAS DIESE MESSUNG NICHT LEISTET: Sie rechnet BRUTTO. Das Kostenmodell vom
04.08. ergab netto -0,233 R. Ein Bruttoergebnis nahe null bleibt danach klar
negativ. Diese Messung korrigiert eine Annahme, sie beantwortet nicht die Frage,
ob sich der Aufbau lohnt.

    python messe_zeitschranke.py --db <pfad>
"""
from __future__ import annotations

import argparse
import sys
from collections import defaultdict

import numpy as np

from backtest_llm1_historisch import lade_reihen_aus_db

VORLAUF = 220
ZIEL_ATR, STOP_ATR = 3.0, 1.5
HORIZONTE = (10, 20, 30, 40, 60)


def main() -> int:
    import config
    from indicators.calculations import atr_wilder
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--db", default="data/tradinginfotool.db")
    args = p.parse_args()

    reihen = lade_reihen_aus_db(args.db)
    handelbar = {a.symbol for a in config.get_watchlist()}
    reihen = {s: r for s, r in reihen.items() if s in handelbar}
    maxh = max(HORIZONTE)

    # je Horizont: Listen der R-Werte, getrennt nach Ausgang
    ziel = {h: 0 for h in HORIZONTE}
    stop = {h: 0 for h in HORIZONTE}
    offen_r: dict[int, list] = {h: [] for h in HORIZONTE}

    for sym, r in reihen.items():
        if len(r) < VORLAUF + maxh + 1:
            continue
        c = np.array([k.close for k in r], dtype=float)
        h_ = np.array([k.high for k in r], dtype=float)
        l_ = np.array([k.low for k in r], dtype=float)
        atr = np.asarray(atr_wilder(h_, l_, c).value, dtype=float)
        for i in range(VORLAUF, len(c) - maxh):
            a = atr[i]
            if not np.isfinite(a) or a <= 0:
                continue
            ein = c[i]
            z_kurs, s_kurs = ein + ZIEL_ATR * a, ein - STOP_ATR * a
            stopabstand = STOP_ATR * a
            erg, tag = None, None
            for j in range(i + 1, i + maxh + 1):
                if l_[j] <= s_kurs:
                    erg, tag = "STOP", j - i
                    break
                if h_[j] >= z_kurs:
                    erg, tag = "ZIEL", j - i
                    break
            for H in HORIZONTE:
                if erg and tag <= H:
                    (ziel if erg == "ZIEL" else stop)[H] += 1
                else:
                    # HIER liegt der Unterschied: nicht 0, sondern der Kurs.
                    offen_r[H].append((c[i + H] - ein) / stopabstand)

    print(f"{len(reihen)} handelbare Reihen, Ziel {ZIEL_ATR} ATR / "
          f"Stop {STOP_ATR} ATR\n")
    print(f"{'Hor.':>5} {'Ziel':>7} {'Stop':>7} {'offen':>7} {'offen %':>8} "
          f"{'R offen, Mittel':>16} {'Median':>8} {'EW=0':>8} {'EW echt':>9}")
    print("-" * 86)
    for H in HORIZONTE:
        n = ziel[H] + stop[H] + len(offen_r[H])
        rs = np.array(offen_r[H]) if offen_r[H] else np.array([0.0])
        mittel, median = float(rs.mean()), float(np.median(rs))
        anteil_offen = len(offen_r[H]) / n
        ew_null = (ziel[H] / n) * 2.0 + (stop[H] / n) * (-1.0)
        ew_echt = ew_null + anteil_offen * mittel
        print(f"{H:5} {ziel[H]:7} {stop[H]:7} {len(offen_r[H]):7} "
              f"{100*anteil_offen:7.1f}% {mittel:16.3f} {median:8.3f} "
              f"{ew_null:+8.3f} {ew_echt:+9.3f}")

    print("\nVERTEILUNG der offenen Faelle bei Horizont 20 "
          "(die Einstellung aus 6.3):")
    rs = np.sort(np.array(offen_r[20]))
    if len(rs):
        for q in (5, 25, 50, 75, 95):
            print(f"   {q:2}. Perzentil  {np.percentile(rs, q):+.3f} R")
        print(f"   Anteil im Plus: {100.0 * (rs > 0).mean():.1f} %")

    # --- NETTO, je Assetklasse -------------------------------------------
    #
    # Die bisher zitierten -0,233 R sind eine HEBEL-Zahl: sie enthalten eine
    # TAGESGEBUEHR (Funding) und haengen an 2,6 Tagen Haltedauer. Bei Spot gibt
    # es kein Funding - dort zaehlen Gebuehr und Spread einmal je Seite,
    # unabhaengig von der Haltedauer. Die Saetze stehen in
    # agent/krypto/backward_tracking.py und sind seit 07.08. je Klasse getrennt.
    #
    # Kosten in R = Roundtrip in % / Stopabstand in %. Der Stopabstand ist
    # 1,5 ATR - also je Asset und Tag verschieden. Deshalb wird er je Anker
    # gerechnet und nicht pauschal gesetzt.
    print("\n\nNETTO JE ASSETKLASSE (Horizont 20), Saetze aus backward_tracking.py")
    print("Krypto 1,5 % je Seite · Boerse 1 EUR fix + 0,25 % Spread "
          "bei 400 EUR Position\n")
    klasse_von = {a.symbol: a.assetklasse for a in config.get_watchlist()}
    RT = {"krypto": 0.03, "aktien": 0.01, "etf": 0.01, "rohstoffe": 0.01}
    kosten_r = defaultdict(list)
    for sym, r in reihen.items():
        kl = klasse_von.get(sym)
        if kl not in RT or len(r) < VORLAUF + maxh + 1:
            continue
        c = np.array([k.close for k in r], dtype=float)
        h_ = np.array([k.high for k in r], dtype=float)
        l_ = np.array([k.low for k in r], dtype=float)
        atr = np.asarray(atr_wilder(h_, l_, c).value, dtype=float)
        for i in range(VORLAUF, len(c) - maxh):
            a = atr[i]
            if not np.isfinite(a) or a <= 0 or c[i] <= 0:
                continue
            stop_rel = STOP_ATR * a / c[i]          # Stopabstand als Anteil
            if stop_rel > 0:
                kosten_r[kl].append(RT[kl] / stop_rel)

    print(f"{'Klasse':12} {'Anker':>7} {'Stop % Median':>14} "
          f"{'Kosten in R':>12} {'Brutto-EW':>10} {'Netto-EW':>10}")
    print("-" * 70)
    brutto = None
    for H in (20,):
        n = ziel[H] + stop[H] + len(offen_r[H])
        rs = np.array(offen_r[H]) if offen_r[H] else np.array([0.0])
        brutto = ((ziel[H] / n) * 2.0 + (stop[H] / n) * (-1.0)
                  + (len(offen_r[H]) / n) * float(rs.mean()))
    for kl in ("krypto", "aktien", "etf", "rohstoffe"):
        v = kosten_r.get(kl)
        if not v:
            continue
        med_kosten = float(np.median(v))
        # Stopabstand zurueckrechnen, damit die Zahl lesbar bleibt
        med_stop = 100.0 * RT[kl] / med_kosten
        print(f"{kl:12} {len(v):7} {med_stop:13.1f}% {med_kosten:12.3f} "
              f"{brutto:+10.3f} {brutto - med_kosten:+10.3f}")

    print("\nDer Brutto-EW ist hier fuer ALLE Klassen derselbe - er stammt aus")
    print("der Gesamtauswertung oben. Die Kosten sind es NICHT: sie haengen am")
    print("Stopabstand, und der ist bei Krypto weiter, bei Boersenwerten enger.")

    print("\nLESART: Die Spalte 'EW=0' ist die Rechnung aus 6.3 - offene Faelle")
    print("zaehlen als null. 'EW echt' setzt stattdessen den tatsaechlichen Kurs")
    print("bei Zeitablauf ein. Der Abstand zwischen beiden ist der Preis der")
    print("Annahme. ALLES BRUTTO - netto lag der Erwartungswert am 04.08. bei")
    print("-0,233 R, und das aendert diese Messung nicht.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
