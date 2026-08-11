# -*- coding: utf-8 -*-
"""Gibt es diesen Aufbau ueberhaupt in einer tragfaehigen Variante?

DIE FRAGE, seit 7.23 praezise stellbar. Der Aufbau verliert nicht an der
Geometrie - brutto liegt er bei rund +0,03 R -, sondern an den Kosten:

    krypto 0,257 R · aktien 0,170 R · etf 0,521 R · rohstoffe 0,335 R

Das Sechs- bis Achtzehnfache des Bruttovorteils. Die Frage ist also nicht mehr
"wie waehlen wir besser aus", sondern: LAESST SICH DIE KOSTENQUOTE SENKEN, und
falls ja, was kostet das an anderer Stelle?

DER EINZIGE HEBEL, und warum es nur einer ist. Kosten in R sind

    Kosten_R = Roundtrip in %  /  Stopabstand in %

Der Roundtrip ist vom Broker gesetzt (Bitpanda, 1,5 % je Seite bei Krypto). Der
Stopabstand ist `s x ATR`. Also senkt AUSSCHLIESSLICH ein groesseres `s` die
Kostenquote - proportional. Die Haltedauer tut es bei Spot NICHT: dort faellt
keine Tagesgebuehr an, die Kosten sind einmalig je Roundtrip.

WAS EIN GROESSERES `s` AN ANDERER STELLE KOSTET, ist die eigentliche Frage.
Bleibt das Verhaeltnis Ziel/Stop gleich, aendert sich bei einem reinen
Zufallspfad die Trefferquote nicht - Barrierewahrscheinlichkeiten haengen vom
VERHAELTNIS ab, nicht vom Massstab. Echte Kursreihen haben aber Drift, Trends
und fette Raender, und die Zeit bis zur Aufloesung waechst quadratisch. Deshalb
wird es gemessen und nicht angenommen.

FUER DIE BOERSENKLASSEN kommt ein zweiter Hebel dazu: dort ist 1 EUR je Trade
FIX. Bei 400 EUR sind das 0,25 % je Seite, bei 2.000 EUR nur 0,05 %. Die
Positionsgroesse wirkt dort also - bei Krypto (rein prozentual) nicht.

    python messe_kostenhebel.py --db <pfad>
"""
from __future__ import annotations

import argparse
import sys
from collections import defaultdict

import numpy as np

from backtest_llm1_historisch import lade_reihen_aus_db

VORLAUF = 220
HORIZONT = 250            # grosszuegig, damit auch weite Barrieren aufloesen
STOP_VIELFACHE = (1.5, 3.0, 6.0, 10.0, 15.0)
VERHAELTNIS = 2.0         # Ziel = VERHAELTNIS x Stop, wie im Bestand (3 / 1,5)

# Saetze aus agent/krypto/backward_tracking.py (recherchiert 07.08.)
KRYPTO_JE_SEITE = 0.015
BOERSE_FIX_EUR = 1.0
BOERSE_SPREAD_JE_SEITE = 0.0025
BOERSE_KLASSEN = ("aktien", "etf", "rohstoffe")


def roundtrip(klasse: str, position_eur: float) -> float:
    if klasse == "krypto":
        return 2 * KRYPTO_JE_SEITE
    return 2 * (BOERSE_FIX_EUR / position_eur + BOERSE_SPREAD_JE_SEITE)


def main() -> int:
    import config
    from indicators.calculations import atr_wilder
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--db", default="data/tradinginfotool.db")
    args = p.parse_args()

    reihen = lade_reihen_aus_db(args.db)
    klasse_von = {a.symbol: a.assetklasse for a in config.get_watchlist()}
    reihen = {s: r for s, r in reihen.items()
              if klasse_von.get(s) in ("krypto",) + BOERSE_KLASSEN}

    # je (Klasse, Stopvielfaches): Zaehler und die R-Werte offener Faelle
    erg: dict = defaultdict(lambda: {"ziel": 0, "stop": 0, "offen": []})
    stop_rel: dict = defaultdict(list)     # Stopabstand als Anteil am Kurs

    for sym, r in reihen.items():
        kl = klasse_von[sym]
        if len(r) < VORLAUF + HORIZONT + 1:
            continue
        c = np.array([k.close for k in r], dtype=float)
        h_ = np.array([k.high for k in r], dtype=float)
        l_ = np.array([k.low for k in r], dtype=float)
        atr = np.asarray(atr_wilder(h_, l_, c).value, dtype=float)
        for i in range(VORLAUF, len(c) - HORIZONT):
            a = atr[i]
            if not np.isfinite(a) or a <= 0 or c[i] <= 0:
                continue
            ein = c[i]
            for s in STOP_VIELFACHE:
                abstand = s * a
                z_kurs, s_kurs = ein + VERHAELTNIS * abstand, ein - abstand
                e = erg[(kl, s)]
                if s == STOP_VIELFACHE[0]:
                    pass
                stop_rel[(kl, s)].append(abstand / ein)
                treffer = None
                for j in range(i + 1, i + HORIZONT + 1):
                    if l_[j] <= s_kurs:
                        treffer = "stop"
                        break
                    if h_[j] >= z_kurs:
                        treffer = "ziel"
                        break
                if treffer:
                    e[treffer] += 1
                else:
                    e["offen"].append((c[i + HORIZONT] - ein) / abstand)

    print(f"Horizont {HORIZONT} Handelstage · Ziel = {VERHAELTNIS:.0f} x Stop\n")
    print(f"{'Klasse':10} {'Stop':>5} {'Stop %':>7} {'Treffer':>8} {'offen':>7} "
          f"{'Brutto R':>9} {'Kosten R':>9} {'NETTO R':>9}")
    print("-" * 74)
    for kl in ("krypto",) + BOERSE_KLASSEN:
        for s in STOP_VIELFACHE:
            e = erg.get((kl, s))
            if not e:
                continue
            n = e["ziel"] + e["stop"] + len(e["offen"])
            if not n:
                continue
            offen_r = np.array(e["offen"]) if e["offen"] else np.array([0.0])
            brutto = ((e["ziel"] / n) * VERHAELTNIS + (e["stop"] / n) * (-1.0)
                      + (len(e["offen"]) / n) * float(offen_r.mean()))
            sr = float(np.median(stop_rel[(kl, s)]))
            k_r = roundtrip(kl, 400.0) / sr
            treffer = 100.0 * e["ziel"] / n
            print(f"{kl:10} {s:5.1f} {100*sr:6.1f}% {treffer:7.1f}% "
                  f"{100*len(e['offen'])/n:6.1f}% {brutto:+9.3f} {k_r:9.3f} "
                  f"{brutto - k_r:+9.3f}")
        print()

    # --- zweiter Hebel: Positionsgroesse, nur bei den Boersenklassen -------
    print("POSITIONSGROESSE - wirkt nur dort, wo eine FIXE Gebuehr anfaellt")
    print("(Krypto ist rein prozentual, dort aendert die Groesse nichts)\n")
    print(f"{'Klasse':10} {'Stop':>5} " + " ".join(f"{g:>9}" for g in
          (400, 1000, 2500, 5000)) + "   (Netto-R je Positionsgroesse in EUR)")
    print("-" * 74)
    for kl in BOERSE_KLASSEN:
        for s in (1.5, 6.0):
            e = erg.get((kl, s))
            if not e:
                continue
            n = e["ziel"] + e["stop"] + len(e["offen"])
            offen_r = np.array(e["offen"]) if e["offen"] else np.array([0.0])
            brutto = ((e["ziel"] / n) * VERHAELTNIS + (e["stop"] / n) * (-1.0)
                      + (len(e["offen"]) / n) * float(offen_r.mean()))
            sr = float(np.median(stop_rel[(kl, s)]))
            zeile = " ".join(f"{brutto - roundtrip(kl, g)/sr:+9.3f}"
                             for g in (400, 1000, 2500, 5000))
            print(f"{kl:10} {s:5.1f} {zeile}")
    print()
    print("LESART: Gesucht ist eine Zeile mit positivem NETTO-R. Gibt es keine,")
    print("existiert dieser Aufbau bei diesen Gebuehren in KEINER Variante -")
    print("und das ist eine Entscheidungsgrundlage, keine Niederlage.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
