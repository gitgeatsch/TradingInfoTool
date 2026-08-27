# -*- coding: utf-8 -*-
"""Welche Staffelung erzeugt den besseren Durchschnittseinstand? (27.08.2026)

⚠️ DIESER KOPF IST DIE VORABFESTLEGUNG, geschrieben BEVOR gerechnet wurde.

DER ANLASS. Der Nutzer hat entschieden: der Kern (BTC/ETH/SOL) wird
akkumuliert, nicht getimt - "Staffelung wie in akkumulation beschrieben, das
passt zur Praxis". Und er hat den Denkfehler der ersten Fassung gefunden:

    *"regelmaessig aber nie teurer als zuletzt hoert sich richtig an, macht
    aber an anderer stelle ein problem: nach einem boden gibt es keine
    nachkaeufe mehr und keine signale oder? sollte nicht eine dynamische
    variante zur anwendung kommen"*

Er hat recht - eine Ja/Nein-Schwelle auf den letzten Kaufpreis verstummt nach
jedem Boden. Die dynamische Form fragt nicht OB, sondern WIEVIEL.

WARUM DIESE MESSUNG NICHT AN N-10 SCHEITERT. Alle bisherigen Nullbefunde sind
an "Ziel vor Stop" gemessen, das per Konstruktion auf die Basisrate faellt.
`handelsauftrag.py` gibt der Akkumulation ausdruecklich ein ANDERES
Erfolgsmass: *"Durchschnittskurs und Endvermoegen statt Ziel vor Stop"*. Das
ist direkt rechenbar und braucht weder Barriere noch Trefferquote.

    Vergleichsmass:  ENDVERMOEGEN JE EINGESETZTEM EURO
                     = (Summe menge_i) * endkurs / (Summe betrag_i)

    Es ist automatisch auf den Einsatz normiert - eine Variante, die mehr
    kauft, gewinnt dadurch NICHT. Genau das war die Falle.

DIE VARIANTEN:

    V0  fest        jeder Takt derselbe Betrag        (der Massstab)
    V1  BTC-Lage    Faktor aus BTCs Abstand zum 200-Schnitt
    V2  eigene Lage Faktor aus dem EIGENEN Abstand
    V3  nie teurer  nur kaufen, wenn unter dem letzten Kaufkurs

DIE FAKTORFUNKTION ist linear und geklemmt:

    faktor = clip(1 - k * abstand, 0.25, 2.5)      k = 2.0

⚠️ SIE IST GESETZT, NICHT GEMESSEN - dieselbe Klasse von Annahme wie die vier
aus `Vorabfestlegung_S1_S4`. Deshalb wird k variiert (1.0 / 2.0 / 3.0). Haengt
das Ergebnis an k, ist die Form die Aussage und nicht der Bezug.

⚠️ KEIN LOOKAHEAD. Der 200-Schnitt wird ausschliesslich aus Kursen VOR dem
Kauftag gebildet (`werte[i-200:i]`, i exklusiv). Der Kauf geschieht zum
Schlusskurs des Tages, an dem entschieden wird.

⚠️ VIELE STARTPUNKTE, NICHT EINER. Ein einzelner Startzeitpunkt ist eine
Stichprobe von eins - wer im Maerz 2020 beginnt, misst den Einstiegstag und
nicht die Regel. Gerechnet wird ueber ALLE moeglichen Starttage mit
mindestens `MIN_KAEUFE` Kaeufen; berichtet werden Median und Spanne.

VORAB FESTGELEGT, WAS WELCHES ERGEBNIS BEDEUTET:

    V1 schlaegt V0 deutlich und ueber alle drei Symbole
        -> die BTC-Lage traegt die Tranchengroesse; Nutzerwahl (a) bestaetigt
    V2 schlaegt V1
        -> ⚠️ der EIGENE Abstand ist der bessere Bezug. Dann ist die
           Uebertragung des Tagewahl-Befundes auf die Groesse falsch gewesen
    V1 ~ V2 ~ V0
        -> die Dynamik traegt nichts; dann ist die einfachste Form richtig
           (fester Betrag), und das ist ein Ergebnis, kein Fehlschlag
    V3 kauft deutlich seltener
        -> der Einwand des Nutzers ist belegt (erwartet, aber zu zeigen)

⚠️ WAS DIESE MESSUNG NICHT KANN. Sie misst EINE Vergangenheit je Symbol -
keine Blockpermutation, keine Signifikanz. Drei Symbole sind drei Faelle. Ein
Unterschied von wenigen Prozent ist hier KEIN Befund, sondern Rauschen. Die
Aussage, die sie treffen kann, ist eine ueber die GROESSENORDNUNG und ueber
das Verstummen von V3.

    python simuliere_staffelung.py [--takt 14] [--k 2.0]
"""
from __future__ import annotations

import argparse
import io
import json
import sqlite3
import sys

import numpy as np

SYMBOLE = ("BTC", "ETH", "SOL")
FENSTER = 200
MIN_KAEUFE = 20          # weniger ist keine Staffelung, sondern ein Kauf
BETRAG = 250.0           # spot.akkumulation aus betraege.py


def _reihe(c: sqlite3.Connection, sym: str) -> tuple[list, np.ndarray]:
    r = list(c.execute("SELECT date, close FROM price_history_ohlc "
                       "WHERE symbol=? AND currency='EUR' ORDER BY date", (sym,)))
    if not r:
        r = list(c.execute("SELECT date, close FROM price_history_ohlc "
                           "WHERE symbol=? ORDER BY date", (sym,)))
    r = [(d, float(x)) for d, x in r if x and float(x) > 0]
    return [d for d, _ in r], np.array([x for _, x in r])


def _abstaende(werte: np.ndarray) -> np.ndarray:
    """Abstand zum eigenen 200-Schnitt je Index; NaN, wo die Reihe zu kurz ist.

    ⚠️ `werte[i-FENSTER:i]` - i EXKLUSIV. Der heutige Kurs geht nicht in
    seinen eigenen Schnitt ein; sonst waere der Abstand systematisch zu klein
    und der Kauftag kennte einen Teil seiner selbst."""
    aus = np.full(len(werte), np.nan)
    for i in range(FENSTER, len(werte)):
        sma = werte[i - FENSTER:i].mean()
        if sma > 0:
            aus[i] = werte[i] / sma - 1.0
    return aus


def _faktor(abstand: float, k: float) -> float:
    if not np.isfinite(abstand):
        return 1.0
    return float(np.clip(1.0 - k * abstand, 0.25, 2.5))


def _lauf(kurse, eigen_abs, btc_abs, start, takt, k, variante):
    """Ein Durchgang ab `start`. Gibt (einsatz, menge, kaeufe) zurueck."""
    einsatz = menge = 0.0
    kaeufe = 0
    letzter_kauf = None
    for i in range(start, len(kurse), takt):
        kurs = kurse[i]
        if variante == "V0":
            betrag = BETRAG
        elif variante == "V1":
            betrag = BETRAG * _faktor(btc_abs[i], k)
        elif variante == "V2":
            betrag = BETRAG * _faktor(eigen_abs[i], k)
        else:  # V3 - nur, wenn billiger als der letzte Kauf
            if letzter_kauf is not None and kurs >= letzter_kauf:
                continue
            betrag = BETRAG
        einsatz += betrag
        menge += betrag / kurs
        letzter_kauf = kurs
        kaeufe += 1
    return einsatz, menge, kaeufe


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="data/messdaten.db")
    ap.add_argument("--takt", type=int, default=14, help="Kauftakt in Tagen")
    ap.add_argument("--k", type=float, default=2.0, help="Steilheit des Faktors")
    ap.add_argument("--datei", default="messwerte_staffelung.json")
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    c = sqlite3.connect(f"file:{a.db}?mode=ro", uri=True)
    print("=" * 78)
    print(f"STAFFELUNG - Endvermoegen je eingesetztem Euro (Takt {a.takt} Tage, k={a.k})")
    print("=" * 78)
    print("V0 fest | V1 nach BTC-Lage | V2 nach eigener Lage | V3 nie teurer")
    print()

    btc_tage, btc_werte = _reihe(c, "BTC")
    btc_abs_map = dict(zip(btc_tage, _abstaende(btc_werte)))

    alles = {}
    for sym in SYMBOLE:
        tage, werte = _reihe(c, sym)
        if len(werte) < FENSTER + MIN_KAEUFE * a.takt:
            print(f"{sym}: Reihe zu kurz ({len(werte)} Tage)")
            continue
        eigen = _abstaende(werte)
        btc_a = np.array([btc_abs_map.get(d, np.nan) for d in tage])
        endkurs = werte[-1]

        # Alle Startpunkte, die noch MIN_KAEUFE Kaeufe zulassen.
        letzter_start = len(werte) - MIN_KAEUFE * a.takt
        starts = range(FENSTER, max(FENSTER + 1, letzter_start))
        erg = {v: [] for v in ("V0", "V1", "V2", "V3")}
        kaeufe_zahl = {v: [] for v in erg}
        for s in starts:
            for v in erg:
                einsatz, menge, n = _lauf(werte, eigen, btc_a, s, a.takt, a.k, v)
                if einsatz <= 0 or n < MIN_KAEUFE:
                    continue
                erg[v].append(menge * endkurs / einsatz)
                kaeufe_zahl[v].append(n)

        print(f"--- {sym}   {len(tage)} Tage, {len(list(starts))} Startpunkte,"
              f" Endkurs {endkurs:,.0f} EUR".replace(",", ".") + " ---")
        print(f"   {'Variante':10s}{'Median':>10s}{'25 %':>10s}{'75 %':>10s}"
              f"{'Kaeufe':>9s}   gegen V0")
        basis = float(np.median(erg["V0"])) if erg["V0"] else None
        for v in ("V0", "V1", "V2", "V3"):
            if not erg[v]:
                print(f"   {v:10s}   keine gueltigen Laeufe")
                continue
            w = np.array(erg[v])
            m = float(np.median(w))
            rel = "" if v == "V0" or not basis else f"{100*(m/basis-1):+7.2f} %"
            print(f"   {v:10s}{m:>10.3f}{float(np.percentile(w,25)):>10.3f}"
                  f"{float(np.percentile(w,75)):>10.3f}"
                  f"{int(np.median(kaeufe_zahl[v])):>9d}   {rel}")
        alles[sym] = {v: {"median": float(np.median(erg[v])) if erg[v] else None,
                          "kaeufe": int(np.median(kaeufe_zahl[v])) if kaeufe_zahl[v] else 0}
                      for v in erg}
        print()

    print("=" * 78)
    print("LESART - vorab festgelegt")
    print("=" * 78)
    print("  Ein Unterschied von wenigen Prozent ist hier RAUSCHEN, kein Befund:")
    print("  drei Symbole sind drei Faelle, und es gibt keine Blockpermutation.")
    print("  Belastbar ist die GROESSENORDNUNG - und die Kaufzahl von V3.")

    if a.datei:
        io.open(a.datei, "w", encoding="utf-8").write(json.dumps(
            {"takt": a.takt, "k": a.k, "betrag": BETRAG, "ergebnis": alles},
            ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
