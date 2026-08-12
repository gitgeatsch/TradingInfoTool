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

# TRENDFENSTER. 250 Handelstage sind rund zwoelf Monate - der Rueckblick, den
# Moskowitz/Ooi/Pedersen (2012) ueber 58 Kontrakte und vier Anlageklassen als
# Trendmass belegen. 60 Handelstage sind das kurze Fenster daneben; erst der
# VERGLEICH beider macht den Fall lesbar, an dem wir gescheitert sind
# (Arbeitsstand 7.9): Jahr steigend, Quartal fallend - eine Korrektur im
# Aufwaertstrend. Genau die hat `_struktur()` "intakter Abwaertstrend" genannt.
TREND_LANG = 250
TREND_KURZ = 60


def _bis(reihe: list, datum: str, vorlauf: int = MIN_VORLAUF) -> int | None:
    """Index des letzten Tages <= `datum`. None, wenn zu wenig Vorlauf.

    `vorlauf` je Aussage, nicht global: eine Aussage, die ihre eigene
    Datentiefe nicht hat, schweigt - waehrend die anderen weiterreden. Eine
    fehlende Aussage ist ein sichtbares Loch, eine auf zu duenner Historie
    gerechnete ist ein unsichtbarer Fehler."""
    idx = None
    for i, k in enumerate(reihe):
        if k.date > datum:
            break
        idx = i
    return idx if idx is not None and idx >= vorlauf else None


def _richtung(pct: float) -> tuple[str, float]:
    """Vorzeichen als Wort, Betrag als Zahl.

    "ueber"/"unter" ist KEIN Etikett im Sinne von R-T2 - es benennt das
    Vorzeichen einer Zahl, die im selben Satz steht. Verboten sind Woerter, die
    ueber die Zahl hinaus deuten ("intakt", "stark", "Trendbruch")."""
    return ("ueber" if pct >= 0 else "unter"), abs(pct)


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


def beschreibe_trend(reihen: dict, klasse: str, datum: str) -> list[str]:
    """Dimension 2 von vier: wo steht dieser Markt, und wo kam er her?

    ZWEI AUSSAGEN, ZWEI QUELLEN, ZWEI VERSCHIEDENE FRAGEN.

    (1) BEWEGUNG - Moskowitz/Ooi/Pedersen, *Time Series Momentum*, JFE 2012.
        Die eigene Rendite ueber zwoelf Monate sagt die kuenftige mit vorher;
        gemessen an 58 Futures und Forwards ueber 25 Jahre, positiv in jeder
        Anlageklasse und in jedem einzelnen Kontrakt. Das ist das am breitesten
        belegte Trendmass, das es gibt - und es ist eine ZAHL, kein Etikett.
        Daneben dasselbe ueber 60 Handelstage. Der Vergleich beider ist der
        eigentliche Inhalt: laufen sie auseinander, ist das eine Korrektur -
        der Fall, den `_struktur()` als "intakter Abwaertstrend" beschriftet
        hat, obwohl die Jahreszahl daneben stieg.

    (2) LAGE IN DER SPANNE - George/Hwang, *The 52-Week High and Momentum
        Investing*, Journal of Finance 2004. Die Naehe zum Jahreshoch schlaegt
        die vergangene Rendite als Vorhersagegroesse und ist in 18 von 20
        Maerkten profitabel. Wir geben die Lage zwischen Jahrestief und
        Jahreshoch an, also beide Raender - "12 % unter dem Hoch" allein laesst
        offen, ob das Tief 5 % oder 60 % entfernt liegt.

    VERWORFEN: der Abstand zur 200-Tage-Linie (Faber 2007). Zwei Gruende. Er
    verleitet zur Binaerlesung "darueber/darunter", und genau ein solches
    Etikett hat uns den Deadloop gebaut. Und er misst weitgehend dasselbe wie
    (1) aus derselben Kursreihe - drei Kennzahlen aus einer Quelle sind der
    Standardfehler "illusion of confirmation", nicht drei Faktoren.

    KEIN PERZENTIL, anders als bei der Volatilitaet. Ein Perzentil ueber
    250-Tage-Renditen braucht 500 Handelstage Vorlauf. BTC hat in unserer
    Datenbank 733 Kerzen ab 17.07.2024 - die Aussage waere fuer zwei Drittel
    der Krypto-Historie nicht berechenbar, waehrend sie fuer Aktien (8.423
    Kerzen) immer kaeme. Eine Kennzahl, die je Klasse mal da ist und mal nicht,
    ist schlimmer als eine schlichtere, die ueberall gleich aussieht.

    STRENG KAUSAL: gelesen wird nur bis zum Ankertag."""
    sym = BENCHMARK.get(klasse)
    reihe = reihen.get(sym) if sym else None
    if not reihe:
        return []
    i = _bis(reihe, datum, vorlauf=TREND_LANG)
    if i is None:
        return []
    c = np.array([k.close for k in reihe[:i + 1]], dtype=float)
    jetzt = float(c[-1])
    if not np.isfinite(jetzt) or jetzt <= 0:
        return []

    name = BENCHMARK_NAME.get(sym, sym)
    saetze = []

    lang, kurz = float(c[-1 - TREND_LANG]), float(c[-1 - TREND_KURZ])
    if np.isfinite(lang) and lang > 0 and np.isfinite(kurz) and kurz > 0:
        rl, vl = _richtung(100.0 * (jetzt / lang - 1.0))
        rk, vk = _richtung(100.0 * (jetzt / kurz - 1.0))
        saetze.append(
            f"{name} steht {vl:.1f} % {rl} seinem Schlusskurs von vor "
            f"{TREND_LANG} Handelstagen und {vk:.1f} % {rk} dem von vor "
            f"{TREND_KURZ} Handelstagen.")

    # +1, damit "dieser 250 Handelstage" WOERTLICH dieselbe Spanne meint wie
    # der Satz davor - von vor 250 Handelstagen bis heute, beide Raender
    # eingeschlossen. Ein Satz, der sich auf den vorigen bezieht, muss auf
    # denselben Zahlen stehen, sonst widersprechen sich zwei Bloecke (R-T8).
    fenster = c[-(TREND_LANG + 1):]
    hoch, tief = float(np.nanmax(fenster)), float(np.nanmin(fenster))
    if np.isfinite(hoch) and np.isfinite(tief) and tief > 0 and hoch > tief:
        # WORTWAHL, absichtlich: "Schlusskurs-Hoch" statt "hoechster
        # Schlusskurs". `waechter_zuspitzung` fuehrt "hoechst" in der
        # HART-Liste - gemeint ist das Steigerungswort ("hoechst
        # bemerkenswert"), getroffen wird per Teilstring auch der gemessene
        # Superlativ ueber ein benanntes Fenster, der voellig zulaessig ist.
        #
        # Geaendert wurde deshalb DER SATZ, NICHT DER WAECHTER. Ein Netz
        # weiter zu machen, damit der eigene Text hindurchpasst, ist die
        # Umkehrung seines Zwecks - und der naechste, der eine Ausnahme
        # braucht, findet dann schon eine vor. Der Preis ist ein Wort.
        saetze.append(
            f"{name} liegt {100.0 * (1.0 - jetzt / hoch):.1f} % unter dem "
            f"Schlusskurs-Hoch und {100.0 * (jetzt / tief - 1.0):.1f} % ueber "
            f"dem Schlusskurs-Tief dieser {TREND_LANG} Handelstage.")
    return saetze
