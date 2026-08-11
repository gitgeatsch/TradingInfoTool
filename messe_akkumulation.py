# -*- coding: utf-8 -*-
"""S2: Schlaegt antizyklische Akkumulation (AZ-4) das stumpfe DCA?

DIE FRAGE, und warum sie nach dem 11.08. die wichtigste ist. Alles Gemessene
sagt dasselbe: im Kursverlauf ist auf Barrieren-Granularitaet nichts zu finden
(34,0 % gegen 33,3 % bei reinem Zufall, Arbeitsstand 7.25). Was bleibt, ist der
Weg, der KEINE Vorhersagekraft braucht - den Aufwaertsdrift einsammeln, statt
Wendepunkte zu treffen.

AZ-4 ist genau das, nur mit einer Zusatzannahme: antizyklisch kaufen, also
bevorzugt tief. Diese Annahme ist pruefbar - und sie steht seit dem 07.08. als
Punkt S2 auf der eigenen Liste, dort als "guenstigster Punkt der ganzen Liste"
markiert. Gemessen wurde sie nie.

DER AUFBAU, und warum er ohne Ausstieg auskommt

Jede Regel bekommt DENSELBEN Betrag je Periode. Wer nicht kauft, legt ihn als
Barmittel zurueck - Warten ist also nicht gratis, es bindet Kapital. Am Ende
zaehlt der Gesamtwert: Stuecke mal Schlusskurs plus die nicht ausgegebenen
Barmittel.

Das ist der ehrliche Vergleich. Wer nur den Durchschnittspreis vergleicht,
belohnt eine Regel, die fast nie kauft - sie hat dann zwar den besten Preis,
aber kaum Stuecke.

DIE REGELN

    DCA        kauft jede Periode. Der Massstab.
    UNTER_SMA  kauft nur, wenn der Kurs unter seinem 200-Tage-Schnitt steht
    RUECKGANG  kauft nur bei >= X % Abstand zum 1-Jahres-Hoch
    GESTAFFELT kauft immer, aber MEHR je tiefer der Rueckgang (Tranchenlogik)

KOSTEN sind enthalten und einseitig: bei Akkumulation wird gekauft, nicht
verkauft. Krypto 1,5 % je Kauf, Boerse 1 EUR fix plus 0,25 % (Saetze aus
agent/krypto/backward_tracking.py). Eine Regel, die oefter kauft, zahlt oefter -
das gehoert in den Vergleich.

KEIN LOOKAHEAD: Jede Entscheidung liest nur `reihe[:i+1]`. Das 1-Jahres-Hoch ist
das Hoch BIS zum Kauftag, nicht das der ganzen Reihe.

    python messe_akkumulation.py --db <pfad>
"""
from __future__ import annotations

import argparse
import sys
from collections import defaultdict

import numpy as np

VORLAUF = 260              # genug fuer 200-Tage-Schnitt und 1-Jahres-Hoch
PERIODE = 7                # Kauftakt in Handelstagen (woechentlich)
BUDGET = 100.0             # EUR je Periode, fuer jede Regel gleich
KRYPTO_JE_KAUF = 0.015
BOERSE_FIX_EUR, BOERSE_SPREAD = 1.0, 0.0025


def _kosten(klasse: str, betrag: float) -> float:
    if klasse == "krypto":
        return betrag * KRYPTO_JE_KAUF
    return BOERSE_FIX_EUR + betrag * BOERSE_SPREAD


def simuliere(c: np.ndarray, klasse: str, regel: str, schwelle: float = 0.20):
    """Gibt (Endwert, investiert, Kaeufe, Durchschnittspreis) zurueck."""
    stuecke = bar = investiert = 0.0
    kaeufe = 0
    for i in range(VORLAUF, len(c), PERIODE):
        bar += BUDGET
        fenster = c[max(0, i - 251):i + 1]        # nur Vergangenheit
        sma = float(fenster[-200:].mean())
        hoch = float(fenster.max())
        rueckgang = 1.0 - c[i] / hoch if hoch > 0 else 0.0

        if regel == "DCA":
            anteil = 1.0
        elif regel == "UNTER_SMA":
            anteil = 1.0 if c[i] < sma else 0.0
        elif regel == "RUECKGANG":
            anteil = 1.0 if rueckgang >= schwelle else 0.0
        elif regel == "GESTAFFELT":
            # AZ-4-Tranchenlogik MIT Reserve (korrigiert 11.08.): in normalen
            # Zeiten wird nur die Haelfte eingesetzt, damit ueberhaupt eine
            # Reserve entsteht - erst dann kann bei Rueckgang mehr fliessen.
            # Die erste Fassung setzte immer mindestens das volle Budget ein
            # und war damit rechnerisch IDENTISCH zu DCA (0 von 43 besser).
            anteil = min(4.0, 0.5 + 5.0 * rueckgang)
        elif regel == "HALBE_QUOTE":
            # KONTROLLE (11.08.): investiert konstant die Haelfte, ohne jedes
            # Timing. Wer in einem fallenden Markt weniger investiert, steht
            # allein dadurch besser da. Schlaegt eine antizyklische Regel diese
            # Kontrolle NICHT, misst sie Quotenreduktion statt Timing.
            anteil = 0.5
        else:
            raise ValueError(regel)

        einsatz = min(bar, BUDGET * anteil)
        if einsatz <= 0:
            continue
        netto = einsatz - _kosten(klasse, einsatz)
        if netto <= 0:
            continue
        stuecke += netto / c[i]
        bar -= einsatz
        investiert += einsatz
        kaeufe += 1
    endwert = stuecke * float(c[-1]) + bar
    schnitt = (investiert / stuecke) if stuecke else float("nan")
    return endwert, investiert, kaeufe, schnitt


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

    regeln = ("DCA", "HALBE_QUOTE", "UNTER_SMA", "RUECKGANG", "GESTAFFELT")
    je_klasse: dict = defaultdict(lambda: defaultdict(list))
    einzeln: dict = {}

    for sym, r in reihen.items():
        if len(r) < VORLAUF + 60:
            continue
        c = np.array([k.close for k in r], dtype=float)
        kl = klasse_von[sym]
        zeile = {}
        for regel in regeln:
            endwert, inv, n, schnitt = simuliere(c, kl, regel, args.schwelle)
            # Einheitliches Mass: Endwert je eingesetztem EUR. Wer weniger
            # investiert, haelt den Rest bar - das steckt im Endwert drin.
            gesamt = BUDGET * len(range(VORLAUF, len(c), PERIODE))
            zeile[regel] = endwert / gesamt if gesamt else float("nan")
            zeile[f"quote_{regel}"] = inv / gesamt if gesamt else 0.0
            je_klasse[kl][regel].append(zeile[regel])
            je_klasse[kl][f"quote_{regel}"].append(zeile[f"quote_{regel}"])
        einzeln[sym] = zeile

    print(f"{len(einzeln)} Symbole · Takt {PERIODE} Handelstage · "
          f"{BUDGET:.0f} EUR je Periode · Rueckgangsschwelle "
          f"{100*args.schwelle:.0f} %")
    print("Mass: Endwert je bereitgestelltem EUR (nicht Investiertes bleibt bar)\n")

    print(f"{'Klasse':12} {'n':>4} " + " ".join(f"{r:>12}" for r in regeln))
    print("-" * 66)
    for kl in sorted(je_klasse):
        werte = je_klasse[kl]
        n = len(werte["DCA"])
        med = {r: float(np.median(werte[r])) for r in regeln}
        print(f"{kl:12} {n:4} " + " ".join(f"{med[r]:12.3f}" for r in regeln))

    alle = {r: [v[r] for v in einzeln.values()] for r in regeln}
    print("-" * 66)
    print(f"{'GESAMT':12} {len(einzeln):4} "
          + " ".join(f"{float(np.median(alle[r])):12.3f}" for r in regeln))

    print("\nWie oft schlaegt die Regel das DCA (je Symbol)?")
    for regel in regeln[1:]:
        besser = sum(1 for v in einzeln.values() if v[regel] > v["DCA"])
        print(f"   {regel:12} {besser:3} von {len(einzeln)} "
              f"= {100*besser/len(einzeln):3.0f} %")

    print("\nLESART: Ein Wert von 1,000 heisst 'am Ende so viel wert wie")
    print("eingezahlt'. Schlaegt keine antizyklische Regel das DCA, ist die")
    print("Zusatzannahme von AZ-4 - antizyklisch ist besser - nicht belegt,")
    print("und der einfachere Sparplan ist vorzuziehen.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
