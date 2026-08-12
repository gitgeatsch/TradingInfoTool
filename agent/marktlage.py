# -*- coding: utf-8 -*-
"""Die Marktlage als Aussagen - vier Dimensionen, je Assetklasse.

WAS DIESE DATEI ERSETZT. Bis heute bekam das Lagebild GENAU ZWEI Saetze, beide
Marktbreite:

    Von 51 beobachteten Coins stehen 18 ueber ihrer 50-Tage-Linie (35 %). ...
    Von 51 beobachteten Coins stehen 11 ueber ihrer 200-Tage-Linie (22 %). ...

Der Fachstandard nennt vier Dimensionen einer Marktlage - Trend, Volatilitaet,
Breite und Liquiditaet (Methodik 2.21.2). Vorhanden war eine davon, und
ausgerechnet die, die fuer vier von fuenf Assetklassen gar nicht berechenbar
ist: Aktien 2 Symbole, ETF 6, Rohstoffe 3. Eine Breite ueber zwei Aktien ist
keine (Faktenmappe 11.4).

DIE MARKTBREITE ENTFAELLT ERSATZLOS. Sie klassenweise zu behalten hiesse, eine
Kennzahl zu pflegen, die nur fuer eine von fuenf Klassen existiert - und deren
Richtung obendrein invers gemessen ist (Arbeitsstand 7.4: kein Zeitpunkt mit
breitem Markt war je ein guter Einstieg). An ihre Stelle tritt der
Klassen-Benchmark, den es fuer jede Klasse gibt.

DER BENCHMARK JE KLASSE

    krypto      BTC
    aktien      _THEMEN_ETF_BENCHMARK_SPY   (in der Datenbank seit 1993)
    etf         dito, als Naeherung
    rohstoffe   die Futures-Referenzreihen

FORM NACH DEN TEXTREGELN. Jede Aussage nennt ihr Fenster (R-T1), traegt kein
absolutes Etikett (R-T2), enthaelt kein Werturteil (R-T3) und ist relativ zur
eigenen Historie formuliert (R-T5). "Die Schwankungsbreite betraegt 3,2 %" sagt
einem Modell nichts; "sie liegt im 88. Perzentil der letzten 250 Handelstage"
ist eine Aussage.

STRENG KAUSAL: gelesen wird nur bis zum Ankertag.
"""
from __future__ import annotations

import numpy as np

BENCHMARK = {
    "krypto": "BTC",
    "aktien": "_THEMEN_ETF_BENCHMARK_SPY",
    "etf": "_THEMEN_ETF_BENCHMARK_SPY",
    "rohstoffe": "_ROHSTOFF_FUTURES_OD7C",
}

# LESBARE NAMEN, keine internen Schluessel (12.08.2026). Der erste Lauf
# schrieb "Die Schwankungsbreite von _THEMEN_ETF_BENCHMARK_SPY betraegt ..." -
# ein Tabellenschluessel im Faktensatz. Ein Modell soll den Markt lesen, nicht
# unsere Datenbank; und ein Name, den niemand ausspricht, ist auch fuer den
# spaeteren Leser der E-Mail wertlos.
# Der Name steht im Satz als SUBJEKT, nicht nach einer Praeposition - sonst
# muesste je Eintrag der Fall gepflegt werden ("von DER breite US-Aktienmarkt"
# im ersten Lauf). Ein Satzbau, der keine Beugung braucht, ist einer weniger,
# den man falsch machen kann.
BENCHMARK_NAME = {
    "BTC": "Bitcoin",
    "_THEMEN_ETF_BENCHMARK_SPY": "Der breite US-Aktienmarkt",
    "_ROHSTOFF_FUTURES_OD7C": "Der Rohstoff-Referenzkontrakt",
}

FENSTER_HISTORIE = 250      # Bezugsraum fuer jedes Perzentil
MIN_VORLAUF = 220


def _bis(reihe: list, datum: str) -> int | None:
    """Index des letzten Tages <= `datum`. None, wenn zu wenig Vorlauf."""
    idx = None
    for i, k in enumerate(reihe):
        if k.date > datum:
            break
        idx = i
    return idx if idx is not None and idx >= MIN_VORLAUF else None


def _perzentil(werte: np.ndarray, aktuell: float) -> int:
    """Wo steht der aktuelle Wert in seiner eigenen Historie?"""
    return int(round(100.0 * float((werte < aktuell).mean())))


def beschreibe_volatilitaet(reihen: dict, klasse: str, datum: str) -> list[str]:
    """Dimension 1 von vier: wie stark schwankt dieser Markt gerade?

    WARUM SIE ZUERST KOMMT. Der Standard nennt die Volatilitaet als die
    Dimension, die bestimmt, wie wahrscheinlich ein Stop getroffen wird - und
    genau das ist bei uns die teuerste Groesse: der Stopabstand entscheidet ueber
    die Kostenquote in R (Arbeitsstand 7.23, ETF 0,52 R bei 1,9 % Stop).

    Gemessen wird die wahre Schwankungsbreite (ATR) im Verhaeltnis zum Kurs,
    also in Prozent - sonst waeren Assets verschiedener Preisklassen nicht
    vergleichbar. Der Bezug ist die eigene Historie, nicht eine feste Schwelle:
    3 % sind bei Krypto normal und bei einem ETF aussergewoehnlich."""
    from indicators.calculations import atr_wilder
    sym = BENCHMARK.get(klasse)
    reihe = reihen.get(sym) if sym else None
    if not reihe:
        return []
    i = _bis(reihe, datum)
    if i is None:
        return []
    h = np.array([k.high for k in reihe[:i + 1]], dtype=float)
    l = np.array([k.low for k in reihe[:i + 1]], dtype=float)
    c = np.array([k.close for k in reihe[:i + 1]], dtype=float)
    atr = np.asarray(atr_wilder(h, l, c).value, dtype=float)
    rel = 100.0 * atr / c                       # ATR als Anteil am Kurs
    gueltig = rel[np.isfinite(rel)]
    if len(gueltig) < FENSTER_HISTORIE // 2:
        return []
    aktuell = float(rel[i])
    if not np.isfinite(aktuell):
        return []
    fenster = gueltig[-FENSTER_HISTORIE:]
    p = _perzentil(fenster, aktuell)
    name = BENCHMARK_NAME.get(sym, sym)
    return [f"{name} schwankt taeglich um {aktuell:.1f} % des Kurses; das "
            f"liegt im {p}. Perzentil der letzten {len(fenster)} "
            f"Handelstage."]
