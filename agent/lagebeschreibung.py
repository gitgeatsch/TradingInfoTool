# -*- coding: utf-8 -*-
"""Was das Modell sehen muss - als Aussagen, nicht als Zahlenliste (10.08.2026).

DER EINGANG war der zweite Defekt neben dem Ausgang. Gemessen am 10.08. bekam das
Modell vier nackte Zahlen in 574 Zeichen JSON:

    "rsi_14": {"wert": 55.0, "perzentil_eigene_historie": 78}
    "abstand_in_atr": {"sma_200": -3.84}
    "schwankungsbreite": {"atr_relativ_prozent": 2.02}

Drei Gruende, warum daraus nichts Gutes kommen konnte:

1. TOKENISIERUNG. Sprachmodelle zerlegen Zahlen in bedeutungslose Fragmente -
   GPT-3 macht aus 42235630 die Folge [422, 35, 630]. Gemessen faellt GPT-4o bei
   Integer-Addition von ~100 % auf 15 %, sobald die Zahlen laenger werden.
2. SEMANTIK IST DER LEISTUNGSTREIBER. Eine Vergleichsstudie: Modelle sind wirksam
   bei Beschreibungen und Verlaeufen, schwach bei gerundeten Zahleneingaben.
   Umformulierung in natuerliche Sprache ("Umsatz fiel von 180 auf 140")
   verbessert die Leistung deutlich; rohe Werte ohne Zerlegung nehmen dem Modell
   nuetzliche Vorannahmen.
3. TRADER LESEN ANDERES. Die Price-Action-Literatur ist deutlich: nachlaufende
   Indikatoren sind NICHT die primaere Entscheidungsgrundlage. Gelesen werden
   Marktstruktur, Lage zu markanten Niveaus, Umsatzbestaetigung und vergleichbare
   fruehere Lagen.

DER KAS-FALL vom 15.07. zeigt den teuersten Einzelmangel: die Zeile "du haeltst
KAS bereits, aktuell -14,6 %" stand in den RISIKEN und hat die Empfehlung nie
erreicht. Das Modell hat in eine Verlustposition nachgekauft, ohne dass der
Bestand in seiner Entscheidungsgrundlage vorkam. Deshalb steht der Bestand hier
an erster Stelle.

ALLES IN EURO. Nutzer am 10.08.: *"mit +1R fange ich nichts an - EURO und Prozent
bitte"*. R-Vielfache sind ein Messmass fuer uns, keine Sprache fuer einen
Menschen, der 300 Euro einsetzt.
"""
from __future__ import annotations

import numpy as np

FENSTER_SWING = 2  # Williams-Fraktal, 5-Kerzen-Muster


def _swings(h: np.ndarray, l: np.ndarray, bis: int) -> tuple[list, list]:
    """Bestaetigte Swing-Punkte bis Index `bis`.

    Ein Fraktal bei j ist erst ab j+FENSTER sichtbar - wer an Index i alle Swings
    bis i benutzt, liest die Zukunft. Diese Schranke ist der Grund, warum hier
    nicht einfach die fertige Indikator-Funktion aufgerufen wird."""
    hi, lo = [], []
    for i in range(FENSTER_SWING, min(len(h) - FENSTER_SWING, bis - FENSTER_SWING + 1)):
        if h[i] == h[i - FENSTER_SWING:i + FENSTER_SWING + 1].max():
            hi.append(i)
        if l[i] == l[i - FENSTER_SWING:i + FENSTER_SWING + 1].min():
            lo.append(i)
    return hi, lo


def _bestand(symbol: str, menge: float | None, einstand_eur: float | None,
             kurs_eur: float | None) -> list[str]:
    """Block 1 - was ich halte. Im KAS-Fall der fehlende Block.

    Bewusst der erste: die Frage "kaufen oder nicht" hat eine voellig andere
    Antwort, je nachdem ob man nichts haelt oder bereits mit Verlust drinsteht."""
    if not menge or not einstand_eur or not kurs_eur:
        return [f"{symbol} ist nicht im Bestand."]
    investiert = menge * einstand_eur
    wert = menge * kurs_eur
    diff = wert - investiert
    pct = 100.0 * diff / investiert if investiert else 0.0
    lage = "im Plus" if diff > 0 else "im Minus"
    return [
        f"{symbol} ist bereits im Bestand: {investiert:.0f} EUR investiert, "
        f"aktuell {wert:.0f} EUR wert - {abs(diff):.0f} EUR {lage} ({pct:+.1f} %).",
    ]


def _struktur(h: np.ndarray, l: np.ndarray, i: int) -> list[str]:
    """Block 2 - Marktstruktur. Was ein Trader zuerst liest."""
    hi, lo = _swings(h, l, i)
    if len(hi) < 2 or len(lo) < 2:
        return []
    hoch_steigt = h[hi[-1]] > h[hi[-2]]
    tief_steigt = l[lo[-1]] > l[lo[-2]]
    if hoch_steigt and tief_steigt:
        s = "hoehere Hochs und hoehere Tiefs - ein intakter Aufwaertstrend"
    elif not hoch_steigt and not tief_steigt:
        s = "tiefere Hochs und tiefere Tiefs - ein intakter Abwaertstrend"
    elif hoch_steigt:
        s = "hoehere Hochs bei tieferen Tiefs - die Spanne weitet sich"
    else:
        s = "tiefere Hochs bei hoeheren Tiefs - die Spanne verengt sich"
    seit = i - max(hi[-1], lo[-1])
    return [f"Die Marktstruktur zeigt {s}. Der letzte Wendepunkt liegt "
            f"{seit} Handelstage zurueck."]


def _bewegung(c: np.ndarray, i: int) -> list[str]:
    """Block 3 - was der Kurs zuletzt getan hat.

    Der heutige Faktensatz enthaelt NUR den Abstand zu einem Durchschnitt. Das ist
    ein Niveau, keine Bewegung - das Modell weiss nicht, ob der Kurs steigt oder
    faellt."""
    teile = []
    for tage in (5, 20, 60):
        if i >= tage:
            teile.append(f"{tage} Tage {100.0 * (c[i] / c[i - tage] - 1.0):+.1f} %")
    return [f"Kursentwicklung: {', '.join(teile)}."] if teile else []


def _niveaus(c: np.ndarray, h: np.ndarray, l: np.ndarray, i: int,
             atr: float, kurs_eur: float, kurs_quelle: float) -> list[str]:
    """Block 4 - wo liegen Widerstand und Unterstuetzung, in ATR und in EUR."""
    hi, lo = _swings(h, l, i)
    if not hi and not lo:
        return []
    faktor = kurs_eur / kurs_quelle if kurs_quelle else 1.0
    punkte = [h[j] for j in hi] + [l[j] for j in lo]
    drueber = [p for p in punkte if p > c[i]]
    drunter = [p for p in punkte if p < c[i]]
    aus = []
    if drueber:
        w = min(drueber)
        aus.append(f"Der naechste Widerstand liegt {(w - c[i]) / atr:.1f} "
                   f"Schwankungsbreiten hoeher, bei {w * faktor:.4f} EUR.")
    if drunter:
        u = max(drunter)
        aus.append(f"Die naechste Unterstuetzung liegt {(c[i] - u) / atr:.1f} "
                   f"Schwankungsbreiten tiefer, bei {u * faktor:.4f} EUR.")
    return aus


def _volumen(c: np.ndarray, v: np.ndarray, i: int,
             tag_vollstaendig: bool = True) -> list[str]:
    """Block 5 - Umsatzbestaetigung. Bis 10.08. gar nicht geliefert.

    Die Praxisliteratur: institutionelle Akkumulation zeigt sich als STETIGER
    Umsatz ueber mehrere Sitzungen, nicht als ein einzelner Ausbruchstag. Und
    entscheidend ist das Verhaeltnis von Auf- zu Abwaertstagen, nicht die Hoehe.

    Absolute Umsaetze werden nie genannt - sie sind zwischen Assets bedeutungslos
    (BTC handelt in Coins, FLOKI in Milliarden Stueck)."""
    if i < 21:
        return []
    fenster = v[i - 20:i]
    fehlend = int(np.sum(~np.isfinite(fenster)) + np.sum(fenster == 0))
    if fehlend > 6:
        return []  # lieber kein Fakt als ein falscher
    d20 = float(np.nanmean(fenster))
    if not d20:
        return []
    # DER LETZTE TAG DER REIHE IST EIN TEILTAG. Gemessen am 10.08. ueber alle
    # Symbole: BTC 0,08x, ETH 0,09x, LINK 0,06x, IMX 0,01x gegen den 20-Tage-
    # Schnitt - waehrend der jeweilige Vortag bei 0,3 bis 0,5x lag. Die Daten
    # werden mitten am Tag geholt, der Umsatz ist noch nicht fertig.
    #
    # Ohne diese Schranke haette die Beschreibung fuer JEDES aktuelle Signal
    # "der Umsatz liegt beim 0,1-fachen des Schnitts" behauptet - eine Aussage,
    # die nicht den Markt beschreibt, sondern die Uhrzeit des Datenabrufs.
    aus = []
    if tag_vollstaendig:
        aus.append(f"Der Umsatz liegt beim {v[i] / d20:.1f}-fachen "
                   f"des 20-Tage-Schnitts.")
    # Auch hier endet das Fenster VOR dem Teiltag - sonst verzerrt ein halber
    # Handelstag das Verhaeltnis von Auf- zu Abwaertsumsatz.
    ende = i + 1 if tag_vollstaendig else i
    auf = float(sum(v[j] for j in range(ende - 20, ende) if c[j] > c[j - 1]))
    ab = float(sum(v[j] for j in range(ende - 20, ende) if c[j] < c[j - 1]))
    if auf + ab > 0:
        q = 100.0 * auf / (auf + ab)
        wer = ("ueberwiegend auf Aufwaertstagen" if q >= 60 else
               "ueberwiegend auf Abwaertstagen" if q <= 40 else
               "ohne klares Uebergewicht")
        aus.append(f"Von den letzten 20 Tagen entfielen {q:.0f} % des Umsatzes "
                   f"auf Aufwaertstage - {wer}.")
    ueber = sum(1 for j in range(ende - 10, ende) if v[j] > d20)
    art = ("stetig ueber mehrere Sitzungen" if ueber >= 6 else
           "auf einzelne Tage konzentriert" if ueber <= 2 else "uneinheitlich")
    aus.append(f"An {ueber} der letzten 10 Tage lag er ueber dem Schnitt - {art}.")
    return aus


def beschreibe_lage(*, symbol: str, reihe: list, index: int,
                    kurs_eur: float, atr: float,
                    menge: float | None = None,
                    einstand_eur: float | None = None) -> list[str]:
    """Die Lage als Aussagen - der EINZIGE Weg von Kursdaten zur Beschreibung.

    Streng kausal: es wird nur `reihe[:index+1]` gelesen. Die Kausalitaetsprobe
    (Beschreibung aus voller Reihe gegen abgeschnittene) muss bitgleiche
    Ergebnisse liefern."""
    # Ist das der letzte Tag der Reihe, ist er noch nicht abgeschlossen -
    # siehe _volumen(). Diese Information gibt es NUR hier, vor dem Zuschnitt.
    tag_vollstaendig = index < len(reihe) - 1
    hist = reihe[:index + 1]
    if len(hist) < 60 or atr <= 0:
        return []
    c = np.array([k.close for k in hist], dtype=float)
    h = np.array([k.high for k in hist], dtype=float)
    l = np.array([k.low for k in hist], dtype=float)
    v = np.array([k.volume if k.volume is not None else np.nan for k in hist],
                 dtype=float)
    i = len(c) - 1

    aus: list[str] = []
    aus += _bestand(symbol, menge, einstand_eur, kurs_eur)
    aus += _struktur(h, l, i)
    aus += _bewegung(c, i)
    aus += _niveaus(c, h, l, i, atr, kurs_eur, float(c[i]))
    aus += _volumen(c, v, i, tag_vollstaendig)
    return aus
