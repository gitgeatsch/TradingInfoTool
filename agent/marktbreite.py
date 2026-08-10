# -*- coding: utf-8 -*-
"""Wie breit ist der Markt getragen? - Eingang fuer Rolle A (10.08.2026).

WARUM DIESER FAKT FEHLT. Das System kennt heute `regime.wert` ("baer"),
Fear & Greed und den BTC-Abstand zur EMA50. Alle drei beschreiben BTC oder die
Stimmung - keiner sagt, ob eine Bewegung von VIELEN Assets getragen wird oder
von zweien.

Aus der Praxisliteratur zur Sektorrotation: *"Steigt ein Sektor, aber nur eine
Handvoll Schwergewichte tragen ihn, ist die Staerke konzentriert und bruechig;
beteiligt sich die Mehrheit, ist die Bewegung eher institutionell getragen und
dauerhaft."* Der uebliche Messwert dafuer ist der Anteil der Titel ueber ihrer
50- und 200-Tage-Linie.

WOZU ROLLE A DAS BRAUCHT. Sie beantwortet eine einzige Frage: wie viel Risiko
ist heute angemessen. Ein Markt, in dem 30 von 40 Coins ueber ihrer 200-Tage-
Linie stehen, traegt eine andere Antwort als einer mit 8 von 40 - und genau
diese Unterscheidung existiert im heutigen Faktensatz nicht.

KEIN URTEIL, NUR DIE ZAEHLUNG. Der Waechter `enthaelt_werturteile()` wuerde ein
Feld wie `breite_einordnung: "schwach"` zu Recht ablehnen. Die Aussage nennt die
Zahlen und ihren historischen Bezug; was daraus folgt, entscheidet das Modell.
"""
from __future__ import annotations

import numpy as np

# Mindestlaenge, damit ein Asset ueberhaupt zaehlt. Wer 23 Kerzen hat, kann
# keine 200-Tage-Linie haben - er wuerde die Quote sonst still verzerren.
MIN_KERZEN = 210
LINIEN = (50, 200)


def _anteil_ueber(reihen: dict, index_datum: str, tage: int) -> tuple[int, int]:
    """Wie viele Assets stehen ueber ihrer N-Tage-Linie, von wie vielen zaehlbaren?

    KAUSAL: je Asset wird nur bis zum Ankerdatum gelesen. Ein Asset, das an
    diesem Datum noch keine Historie hat, zaehlt nicht mit - und zwar weder im
    Zaehler noch im Nenner."""
    drueber = zaehlbar = 0
    for reihe in reihen.values():
        bis = [k for k in reihe if k.date <= index_datum]
        if len(bis) < max(MIN_KERZEN, tage + 10):
            continue
        c = np.array([k.close for k in bis], dtype=float)
        linie = float(c[-tage:].mean())
        zaehlbar += 1
        if c[-1] > linie:
            drueber += 1
    return drueber, zaehlbar


def _historischer_bezug(reihen: dict, index_datum: str, tage: int,
                        aktuell_pct: float, rueckblick: int = 250) -> int | None:
    """In wie viel Prozent der letzten Tage war die Breite NIEDRIGER als heute?

    Ohne diesen Bezug ist "12 von 40" eine nackte Zahl: das Modell kann nicht
    wissen, ob das viel oder wenig ist. Mit dem Perzentil steht daneben, wie
    ungewoehnlich der Wert im eigenen Verlauf ist - dasselbe Muster wie beim
    ATR-Perzentil, das sich bewaehrt hat."""
    daten = sorted({k.date for r in reihen.values() for k in r if k.date <= index_datum})
    if len(daten) < 60:
        return None
    # Bewusst grob abgetastet: die Breite aendert sich langsam, und eine
    # Auswertung ueber 250 Tage x 40 Assets waere sonst unnoetig teuer.
    proben = daten[-rueckblick::5]
    werte = []
    for d in proben:
        ueber, gesamt = _anteil_ueber(reihen, d, tage)
        if gesamt >= 10:
            werte.append(100.0 * ueber / gesamt)
    if len(werte) < 12:
        return None
    return int(round(100.0 * sum(1 for w in werte if w < aktuell_pct) / len(werte)))


def beschreibe_marktbreite(reihen: dict, index_datum: str,
                           mit_bezug: bool = True) -> list[str]:
    """Die Marktbreite als Aussagen - Eingang fuer Rolle A.

    `reihen` ist die volle Sammlung aus `lade_reihen()`; `index_datum` schneidet
    kausal ab. Gibt eine leere Liste zurueck, wenn zu wenige Assets zaehlbar
    sind - lieber kein Fakt als ein irrefuehrender."""
    aus: list[str] = []
    for tage in LINIEN:
        ueber, gesamt = _anteil_ueber(reihen, index_datum, tage)
        if gesamt < 10:
            continue
        pct = 100.0 * ueber / gesamt
        satz = (f"Von {gesamt} beobachteten Coins stehen {ueber} ueber ihrer "
                f"{tage}-Tage-Linie ({pct:.0f} %).")
        if mit_bezug:
            p = _historischer_bezug(reihen, index_datum, tage, pct)
            if p is not None:
                satz += (f" In den letzten 250 Handelstagen war dieser Anteil in "
                         f"{p} % der Faelle niedriger.")
        aus.append(satz)
    return aus
