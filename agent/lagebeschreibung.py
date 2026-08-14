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
    Antwort, je nachdem ob man nichts haelt oder bereits mit Verlust drinsteht.

    DREI ZUSTAENDE STATT ZWEI (11.08.). Vorher galt "kein Einstand" als "nicht
    im Bestand" - eine Falschaussage, keine Luecke: das Modell entschied ueber
    einen Neukauf in der Annahme, wir haetten nichts. Ausloeser war ein
    Lesefehler eine Ebene tiefer (nur die berechnete Einstandsspalte, nicht die
    manuell gepflegte). Der ist behoben; diese Fallunterscheidung bleibt als
    Netz, damit derselbe Fehler nie wieder als "nicht im Bestand" erscheint."""
    if not menge:
        return [f"{symbol} ist nicht im Bestand."]
    if not einstand_eur or not kurs_eur:
        # Wir HALTEN - nur Einstand oder Kurs fehlen. Das ist eine andere
        # Aussage als "nicht investiert", und das Modell muss sie kennen.
        return [f"{symbol} ist im Bestand ({menge:.4f} Stueck), aber Einstand "
                f"oder aktueller Kurs fehlen - Gewinn und Verlust dieser "
                f"Position sind unbekannt."]
    investiert = menge * einstand_eur
    wert = menge * kurs_eur
    diff = wert - investiert
    pct = 100.0 * diff / investiert if investiert else 0.0
    lage = "im Plus" if diff > 0 else "im Minus"
    return [
        f"{symbol} ist bereits im Bestand: {investiert:.0f} EUR investiert, "
        f"aktuell {wert:.0f} EUR wert - {abs(diff):.0f} EUR {lage} ({pct:+.1f} %).",
    ]


def _struktur(c: np.ndarray, h: np.ndarray, l: np.ndarray, i: int) -> list[str]:
    """Block 2 - Marktstruktur, MIT ihrem Massstab (Regeln R-T1 und R-T2).

    DER DEFEKT, DEN DAS BEHEBT (Arbeitsstand 7.9). Hier stand ein ABSOLUTES
    Etikett - "ein intakter Abwaertstrend" - auf einem Vergleich der letzten
    ZWEI Wendepunkte, also weniger Tage. Bei ETH am 24.06.2025 stand daneben
    "60 Tage +37,0 %"; das Modell gewichtete das Etikett hoch und die Zahl
    gering und sagte NICHTS_TUN. Der Kurs erreichte danach sein Ziel.

    SYMMETRISCH KORRIGIERT, ausdruecklich nicht in Richtung "mehr kaufen".
    Die Zaehlung ueber 44 Symbole und die ganze Historie (Arbeitsstand 7.11)
    zeigt, dass der HAEUFIGERE Fehler das Gegenteil ist:

        "Aufwaerts"-Etikett bei 60-Tage <= -10 %   11,39 % der Krypto-Tage
        "Abwaerts"-Etikett  bei 60-Tage >= +10 %    6,21 %

        Uebereinstimmung mit der 60-Tage-Bewegung:
            "abwaerts"   74 %
            "aufwaerts"  42 %   <- kaum besser als ein Muenzwurf

    Ein Fix nur in die Richtung, die die verpassten Kaeufe erzeugt hat, haette
    die groessere Haelfte verschaerft - er schoebe in fallende Maerkte hinein.

    DESHALB: KEIN Etikett mehr, in keine Richtung. Genannt wird die
    Beobachtung, ihr Fenster (R-T1) und der uebergeordnete Massstab daneben.
    Das Gewichten ist Aufgabe des Modells, nicht der Beschriftung."""
    hi, lo = _swings(h, l, i)
    if len(hi) < 2 or len(lo) < 2:
        return []
    hoch_steigt = h[hi[-1]] > h[hi[-2]]
    tief_steigt = l[lo[-1]] > l[lo[-2]]
    if hoch_steigt and tief_steigt:
        s = "hoehere Hochs und hoehere Tiefs"
    elif not hoch_steigt and not tief_steigt:
        s = "tiefere Hochs und tiefere Tiefs"
    elif hoch_steigt:
        s = "hoehere Hochs bei tieferen Tiefs"
    else:
        s = "tiefere Hochs bei hoeheren Tiefs"
    # Die Spanne, ueber die der Vergleich ueberhaupt reicht: vom frueheren der
    # beiden vorletzten Wendepunkte bis heute. Ohne diese Zahl klingt eine
    # Aussage ueber wenige Tage wie eine ueber jeden Zeitraum.
    spanne = i - min(hi[-2], lo[-2])
    seit = i - max(hi[-1], lo[-1])
    aus = [f"Auf Sicht der letzten {spanne} Handelstage zeigt die Marktstruktur "
           f"{s}; der letzte Wendepunkt liegt {seit} Handelstage zurueck."]
    if i >= 60:
        b60 = 100.0 * (c[i] / c[i - 60] - 1.0)
        aus.append(f"Zum Vergleich: ueber 60 Handelstage steht der Kurs "
                   f"{b60:+.1f} %.")
    return aus


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


# Ein Niveau, das direkt am Kurs liegt, ist keine Marke - es ist Rauschen.
# Im Trockenlauf vom 10.08. meldete die erste Fassung fuer JEDEN Prueffall
# "Widerstand 0,0 Schwankungsbreiten hoeher": bei taeglichen Fraktalen liegt
# immer ein Swing direkt daneben. Zwei Schranken beheben das.
NIVEAU_MIN_ABSTAND_ATR = 0.5   # naeher als das ist keine eigene Marke
NIVEAU_CLUSTER_ATR = 0.3       # was enger beieinander liegt, ist EIN Niveau


def _kurs(wert: float) -> str:
    """Ein Kurs in der Genauigkeit, die er verdient.

    GEFUNDEN IN DER GEGENPRUEFUNG ZUR ZWEITEN MEINUNG (13.08.). Vorher stand
    hier fest `:.4f` - fuer BTC ergab das "57402.8132 EUR". Vier Nachkommastellen
    auf einen fuenfstelligen Kurs sind VORGETAEUSCHTE GENAUIGKEIT: die Marke
    stammt aus einem Cluster von Hochs und Tiefs, sie ist auf hundert Euro genau
    und nicht auf einen Zehntelcent. Ein Modell liest so etwas als exakt und
    ankert daran.

    Umgekehrt braucht ein Token bei 0,00034 EUR die Stellen wirklich - deshalb
    haengt die Genauigkeit an der Groessenordnung und nicht an einer Konstante.

    Betrifft NICHT nur Z.ai: dieselbe Zeile geht auch an die Rolle BC."""
    w = abs(float(wert))
    if w >= 1000:
        return f"{wert:,.0f}".replace(",", ".")
    if w >= 100:
        return f"{wert:.1f}"
    if w >= 1:
        return f"{wert:.2f}"
    if w >= 0.01:
        return f"{wert:.4f}"
    return f"{wert:.6f}"


def _cluster(punkte: list, atr: float) -> list[tuple[float, int]]:
    """Fasst nahe beieinanderliegende Swings zu einem Niveau zusammen.

    Ein Kurs, der dreimal an derselben Stelle gedreht hat, hat dort EINE Marke -
    und ihre Staerke steckt in der Zahl der Beruehrungen, nicht in drei
    Eintraegen. Gibt (Preis, Beruehrungen) zurueck."""
    if not punkte:
        return []
    aus = []
    for p in sorted(punkte):
        if aus and abs(p - aus[-1][0]) <= NIVEAU_CLUSTER_ATR * atr:
            preis, n = aus[-1]
            aus[-1] = ((preis * n + p) / (n + 1), n + 1)
        else:
            aus.append((p, 1))
    return aus


def _niveaus(c: np.ndarray, h: np.ndarray, l: np.ndarray, i: int,
             atr: float, kurs_eur: float, kurs_quelle: float) -> list[str]:
    """Block 4 - Widerstand und Unterstuetzung, in ATR und in EUR.

    Genannt wird das naechste Niveau, das WEIT GENUG entfernt ist, um eine
    Marke zu sein - und mit der Zahl seiner Beruehrungen, denn ein dreimal
    bestaetigtes Niveau ist etwas anderes als ein einmaliger Wendepunkt."""
    hi, lo = _swings(h, l, i)
    if (not hi and not lo) or atr <= 0:
        return []
    faktor = kurs_eur / kurs_quelle if kurs_quelle else 1.0
    kurs = float(c[i])
    grenze = NIVEAU_MIN_ABSTAND_ATR * atr
    niveaus = _cluster([float(h[j]) for j in hi] + [float(l[j]) for j in lo], atr)

    aus = []
    drueber = [(p, n) for p, n in niveaus if p - kurs >= grenze]
    if drueber:
        p, n = min(drueber, key=lambda x: x[0])
        aus.append(f"Der naechste Widerstand liegt {(p - kurs) / atr:.1f} "
                   f"Schwankungsbreiten hoeher, bei {_kurs(p * faktor)} EUR "
                   f"({n}-mal beruehrt).")
    drunter = [(p, n) for p, n in niveaus if kurs - p >= grenze]
    if drunter:
        p, n = max(drunter, key=lambda x: x[0])
        aus.append(f"Die naechste Unterstuetzung liegt {(kurs - p) / atr:.1f} "
                   f"Schwankungsbreiten tiefer, bei {_kurs(p * faktor)} EUR "
                   f"({n}-mal beruehrt).")
    if not aus:
        # Auch das ist eine Aussage: der Kurs steht im freien Feld.
        aus.append(f"Im Umkreis von {NIVEAU_MIN_ABSTAND_ATR:.1f} "
                   f"Schwankungsbreiten liegt keine markante Marke.")
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


def _finanzierung(zusammenfassung: dict | None) -> list[str]:
    """Block 6 - die Positionierung am Terminmarkt (11.08.2026).

    DER ERSTE FAKT IN DIESER BESCHREIBUNG, DER NICHT AUS UNSERER KURSREIHE
    STAMMT. Struktur, Bewegung und Niveaus sind derselbe Fakt in drei
    Uebersetzungen; der Umsatz ist der zweite. Der Fachstandard verlangt drei
    bis vier UNABHAENGIGE Faktoren (Methodik 2.21.1), und genau daran fehlte es:
    das Modell zaehlte in 72 % der Faelle nur ein bis zwei.

    FORM NACH DEN TEXTREGELN:
      R-T1  das Fenster wird genannt - "die letzten 100 Perioden"
      R-T2  kein Etikett wie "stark long positioniert"
      R-T3  keine Bewertung; die Richtung wird SACHLICH aufgeloest
            ("Longs zahlen Shorts"), weil "positive Rate" ohne diese Erklaerung
            kein Fakt, sondern Fachjargon ist
      R-T5  relativ - Perzentil und Anteil statt der rohen Zahl. 0,0001 sagt
            einem Modell nichts

    KEINE ZEILE, WENN KEINE DATEN. Ein Satz "keine Finanzierungsdaten" waere
    fuer alle Aktien, ETF und Rohstoffe identisch - ein konstantes Feld im Sinne
    von B10, das Platz kostet und nichts unterscheidet."""
    if not zusammenfassung:
        return []
    n = zusammenfassung.get("beobachtungen") or 0
    if n < 20:
        return []
    pos = zusammenfassung.get("anteil_positiv_pct")
    p = zusammenfassung.get("perzentil")
    return [f"Am Terminmarkt war die Finanzierungsrate in {pos} % der letzten "
            f"{n} Perioden positiv - dann zahlen die Long-Positionen an die "
            f"Short-Positionen. Die aktuelle Rate liegt im {p}. Perzentil "
            f"dieser {n} Perioden."]


def beschreibe_lage(*, symbol: str, reihe: list, index: int,
                    kurs_eur: float, atr: float,
                    menge: float | None = None,
                    einstand_eur: float | None = None,
                    finanzierung: dict | None = None) -> list[str]:
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

    return [satz for block in BLOCK_REIHENFOLGE
            for satz in geteilt(symbol=symbol, reihe=reihe, index=index,
                                kurs_eur=kurs_eur, atr=atr, menge=menge,
                                einstand_eur=einstand_eur,
                                finanzierung=finanzierung)[block]]


# Die Bloecke in genau der Reihenfolge, in der sie im Prompt stehen. Sie ist
# NICHT kosmetisch: R-T9 - was zuerst steht, wiegt schwerer.
BLOCK_REIHENFOLGE = ("bestand", "struktur", "bewegung", "marken", "volumen",
                     "finanzierung")


def geteilt(*, symbol: str, reihe: list, index: int,
            kurs_eur: float, atr: float,
            menge: float | None = None,
            einstand_eur: float | None = None,
            finanzierung: dict | None = None) -> dict:
    """Dieselben Saetze, aber nach Bloecken getrennt (14.08.2026).

    WOFUER. Die Kaufmail kann Bestand, Marken und Coin-Fakten getrennt
    darstellen (`signal_mail.baue_mail`), bekam aber keinen davon - die
    Rollen-Kette uebergab nur den Faktenblock. Der Nutzer sah deshalb eine
    Mail, die generisch wirkt, obwohl die Vorlage es nicht ist. Die Saetze
    EXISTIEREN laengst; sie gingen bisher nur ans Modell.

    WARUM NICHT DIE FLACHE LISTE ZERLEGEN. Man koennte `beschreibe_lage()`
    aufrufen und die Saetze am Wortlaut auseinandersortieren ("faengt mit
    'Der naechste Widerstand' an"). Das waere eine zweite, stillschweigende
    Definition derselben Gliederung - und sie bricht, sobald jemand eine
    Formulierung aendert, ohne dass eine Pruefung anschlaegt.

    `beschreibe_lage()` RUFT JETZT DIESE FUNKTION und setzt sie zusammen. Damit
    gibt es die Gliederung genau einmal, und der Prompt bleibt Zeichen fuer
    Zeichen derselbe - was er muss, sonst waeren alle bisherigen Messungen
    nicht mehr vergleichbar."""
    tag_vollstaendig = index < len(reihe) - 1
    hist = reihe[:index + 1]
    leer = {b: [] for b in BLOCK_REIHENFOLGE}
    if len(hist) < 60 or atr <= 0:
        return leer
    c = np.array([k.close for k in hist], dtype=float)
    h = np.array([k.high for k in hist], dtype=float)
    l = np.array([k.low for k in hist], dtype=float)
    v = np.array([k.volume if k.volume is not None else np.nan for k in hist],
                 dtype=float)
    i = len(c) - 1
    return {
        "bestand": _bestand(symbol, menge, einstand_eur, kurs_eur),
        "struktur": _struktur(c, h, l, i),
        "bewegung": _bewegung(c, i),
        "marken": _niveaus(c, h, l, i, atr, kurs_eur, float(c[i])),
        "volumen": _volumen(c, v, i, tag_vollstaendig),
        "finanzierung": _finanzierung(finanzierung),
    }
