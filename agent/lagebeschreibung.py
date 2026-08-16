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
             kurs_eur: float | None, instrument: str = "spot",
             gegenseite: str | None = None) -> list[str]:
    """Block 1 - was ich halte. Im KAS-Fall der fehlende Block.

    Bewusst der erste: die Frage "kaufen oder nicht" hat eine voellig andere
    Antwort, je nachdem ob man nichts haelt oder bereits mit Verlust drinsteht.

    DREI ZUSTAENDE STATT ZWEI (11.08.). Vorher galt "kein Einstand" als "nicht
    im Bestand" - eine Falschaussage, keine Luecke: das Modell entschied ueber
    einen Neukauf in der Annahme, wir haetten nichts. Ausloeser war ein
    Lesefehler eine Ebene tiefer (nur die berechnete Einstandsspalte, nicht die
    manuell gepflegte). Der ist behoben; diese Fallunterscheidung bleibt als
    Netz, damit derselbe Fehler nie wieder als "nicht im Bestand" erscheint.

    ZWEI BESTAENDE STATT EINEM (15.08.2026, erster Produktionslauf). Dieser
    Block sagte im HEBEL-Lauf "LINK ist bereits im Bestand: 4.100 EUR
    investiert" - und meinte den SPOT-Bestand, weil `rollen_eingabe.bestand()`
    nur `holdings` las. Das Modell hat daraufhin getan, was jeder tun wuerde,
    der das liest: es empfahl SCHLIESSEN. Danach sah der Code in
    `hebel_positions` nach, fand nichts und verwarf die Antwort.

        22x SCHLIESSEN und 3x TEILVERKAUF "ohne Bestand" an einem Vormittag -
        9 % aller Modellaufrufe, auf eine Frage mit falschen Fakten.

    Der Kommentar im Verwerfzweig sagte, das sei kein Fehler des Modells, es
    kenne den Bestand nicht. Das stimmte nicht: es kannte einen Bestand, nur
    den falschen. Jetzt steht hier der Bestand DES INSTRUMENTS - und die
    andere Seite wird ausdruecklich benannt statt verschwiegen, weil sie fuer
    das Urteil zaehlt (`gegenseite`)."""
    ist_hebel = str(instrument) == "hebel"
    was = "eine offene Hebelposition" if ist_hebel else "im Bestand"
    hinweis = [gegenseite] if gegenseite else []
    if not menge:
        # KEIN "nicht im Bestand" IM HEBEL-LAUF. Der Satz waere dort mehrdeutig:
        # er koennte den Spot-Bestand meinen, den es sehr wohl geben kann.
        return ([f"In {symbol} besteht keine offene Hebelposition."]
                if ist_hebel else [f"{symbol} ist nicht im Bestand."]) + hinweis
    if not einstand_eur or not kurs_eur:
        # Wir HALTEN - nur Einstand oder Kurs fehlen. Das ist eine andere
        # Aussage als "nicht investiert", und das Modell muss sie kennen.
        # Bei einer Hebelposition ist das der REGELFALL und kein Mangel: sie
        # fuehrt keinen Einstandspreis je Stueck, der Buchwert steckt im
        # Positionswert (`hebel_positions` hat keine solche Spalte).
        return [f"{symbol} hat {was} ({menge:.4f} Stueck), aber Einstand "
                f"oder aktueller Kurs fehlen - Gewinn und Verlust dieser "
                f"Position sind unbekannt."] + hinweis
    investiert = menge * einstand_eur
    wert = menge * kurs_eur
    diff = wert - investiert
    pct = 100.0 * diff / investiert if investiert else 0.0
    lage = "im Plus" if diff > 0 else "im Minus"
    return [
        f"{symbol} ist bereits im Bestand: {investiert:.0f} EUR investiert, "
        f"aktuell {wert:.0f} EUR wert - {abs(diff):.0f} EUR {lage} ({pct:+.1f} %).",
    ] + hinweis


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
    return [f"Auf Sicht der letzten {spanne} Handelstage zeigt die "
            f"Marktstruktur {s}; der letzte Wendepunkt liegt {seit} "
            f"Handelstage zurueck."]


# ⚠️ HIER STAND EIN ZWEITER SATZ, UND ER WAR EINE WOERTLICHE DOPPELUNG
# (entfernt 16.08.2026).
#
#     _struktur:  "Zum Vergleich: ueber 60 Handelstage steht der Kurs -32.0 %."
#     _bewegung:  "Kursentwicklung: 5 Tage -2.5 %, ..., 60 Tage -32.0 %."
#
# Bitgleiche Formel `100 * (c[i]/c[i-60] - 1)`, dieselbe Zahl, zwei Saetze.
# Gemessen ueber alle Reihen mit voller Historie: 42 von 42 identisch, KEINE
# Ausnahme - also in jedem Prompt und jedem Lauf.
#
# ZWEI SCHAEDEN, nicht nur Redundanz:
#   GEWICHT   eine Zahl, die zweimal dasteht, wiegt schwerer. Das ist
#             dieselbe Mechanik wie R-T9 (was zuerst steht, wiegt schwerer),
#             nur ueber Wiederholung statt ueber Position - und sie war
#             nicht beabsichtigt.
#   MESSUNG   `messe_begruendungen.py` ordnet Belege ihrem Block zu. Ein
#             Beleg "60 Tage -32 %" war NICHT zuordenbar; das Woerterbuch
#             fuehrte "zum vergleich" und "60 handelstage" unter `bewegung`,
#             der Satz stand aber in `struktur`. Die Blockmessung lief durch
#             genau den Fehler, den sie messen sollte.
#
# WARUM DER SATZ TROTZDEM NICHT ERSATZLOS VERSCHWINDET. Er wurde am 11.08.
# ABSICHTLICH neben die Strukturaussage gesetzt: im ETH-Fall vom 24.06.
# gewichtete das Modell das Etikett hoch und die Zahl daneben gering. Diese
# Nachbarschaft war der Fix. Deshalb werden die beiden BLOECKE zusammengelegt
# (`verlauf`) statt eine Zeile zu loeschen - die Nachbarschaft bleibt, die
# zweite Nennung geht.


def _bewegung(c: np.ndarray, i: int) -> list[str]:
    """Block 3 - was der Kurs zuletzt getan hat.

    Der heutige Faktensatz enthaelt NUR den Abstand zu einem Durchschnitt. Das ist
    ein Niveau, keine Bewegung - das Modell weiss nicht, ob der Kurs steigt oder
    faellt.

    "IM SELBEN RAHMEN" (16.08.2026) - das ist kein Fuellwort. Der Satz steht
    seit heute direkt unter der Strukturaussage, und die 60-Tage-Zahl ist der
    uebergeordnete Massstab, gegen den sie zu lesen ist. Vorher stand dieser
    Bezug als eigener Satz im Struktur-Block und wiederholte dabei die Zahl."""
    teile = []
    for tage in (5, 20, 60):
        if i >= tage:
            teile.append(f"{tage} Tage {100.0 * (c[i] / c[i - tage] - 1.0):+.1f} %")
    return ([f"Kursentwicklung im selben Rahmen: {', '.join(teile)}."]
            if teile else [])


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


def _finanzierung(zusammenfassung: dict | None,
                  instrument: str = "spot") -> list[str]:
    """Block 6 - die Positionierung am Terminmarkt (11.08.2026).

    NUR NOCH BEIM HEBEL (Phase I, Schritt 2, 16.08.2026). Bis heute stand
    dieser Block in JEDEM Krypto-Prompt, auch im Spot-Lauf - und er beschreibt
    eine Zahlung zwischen Long- und Short-Positionen am Terminmarkt, die ein
    Spot-Kaeufer weder leistet noch erhaelt. Gemessen (O-34) wurde er trotzdem
    in 63 % der Spot-Urteile als Beleg zitiert: ein Fakt, der zur Sache nichts
    beitraegt, hat dort ein Sechstel der Begruendungen getragen.

    DIE INFORMATION GEHT NICHT VERLOREN, sie wechselt die Stufe. Rolle G
    (`agent/positionierung.py`) liest dieselbe Finanzierungsrate als
    Perzentil - und zwar fuer Spot GENAUSO wie fuer Hebel. Damit ist die
    Konstruktionsbedingung der zweiten Stufe erfuellt: bei Spot gehoert das
    Funding jetzt zu GENAU EINEM Modell.

    WAS DAS KOSTET, offen gesagt: Funding war bei Spot der einzige Fakt, der
    nicht aus der eigenen Kursreihe stammte - also der dritte unabhaengige
    Faktor, um den es am 11.08. ueberhaupt ging. Faellt er weg, faellt bei
    manchem Spot-Urteil `unabhaengige_faktoren` von 3 auf 2, und daran haengt
    ueber `tranche_aus_faktoren()` der Betrag. Das ist die richtige Folge und
    keine unerwuenschte: ein Faktor, der zur Sache nichts sagt, hat nie
    getragen - er wurde nur mitgezaehlt.

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
    if str(instrument) != "hebel":
        return []
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


# Die drei Faktoren, an denen der Abstand zur Zwangsaufloesung abgelesen wird.
# NICHT frei gewaehlt: 10 ist `entscheidungsrechnung.GRENZEN["hebel_max"]` und
# zugleich die Obergrenze von Bitpanda Margin, 3 der kleinste Faktor, der in
# der Praxis vorkommt, 6 die Mitte. Drei Punkte genuegen - die Kurve 1/h ist
# monoton, und eine laengere Tabelle waere Zahlensalat statt Aussage.
GRENZHEBEL = (3.0, 6.0, 10.0)


def _hebelgeometrie(atr: float, close: float,
                    instrument: str = "spot") -> list[str]:
    """Wie weit die Zwangsaufloesung entfernt liegt - je Grenzhebel.

    DIE GROESSTE LUECKE DES HEBEL-KORBS (Bestandserhebung 16.08., Kapitel
    35.1). Das Modell waehlte EROEFFNEN, ohne den Liquidationsabstand zu
    kennen - er wird zwei Schritte SPAETER gerechnet und steht dann in der
    Mail. Am AKT-Signal lag er komfortabel; aus Sicht des Modells war das
    Zufall, es hat ihn nicht beurteilt.

    DAS HENNE-EI-PROBLEM UND SEINE LOESUNG. Der Faktor folgt aus dem
    Stopabstand, den das Modell erst nennen wird - vorher kennt ihn niemand.
    Der ABSTAND je Faktor steht aber schon fest: er ist `1/Hebel`, genau die
    Formel, mit der `entscheidungsrechnung` spaeter `liquidation_etwa_eur`
    rechnet. Eine Tabelle ueber drei Stuetzstellen statt eines Kreisbezugs.

    WARUM DAS KEIN KONSTANTES FELD IST (R-T6). Die Prozentwerte 33/17/10 sind
    ueber alle Assets gleich - fuer sich genommen waeren sie genau das
    stehende Feld, das nichts unterscheidet. Die Schwankungsbreiten daneben
    sind es nicht: bei einem ruhigen Wert sind 10 % viele ATR, bei einem
    unruhigen wenige. ERST DIESER BEZUG macht die Zeile zu einer Aussage
    ueber DIESES Asset - und er ist zugleich die Form, die `_niveaus()` fuer
    Widerstand und Unterstuetzung ohnehin benutzt.

    GRUEN, NICHT GELB. Der Satz beschreibt eine Geometrie und bewertet sie
    nicht. Der Unterschied ist gemessen und teuer: der Kostenhinweis
    ("kostet 4,5 % der Margin im Monat") liess die EROEFFNEN-Quote von 93 %
    auf 3 % einbrechen. Deshalb steht hier KEIN Betrag und KEINE Warnung -
    die Finanzierungshoehe ist Phase III und braucht einen gepaarten
    Vergleich.

    BEIDE ZAHLEN IN DER QUELLWAEHRUNG. `close` ist `c[i]`, nicht `kurs_eur` -
    sonst waere das Verhaeltnis zum ATR um den Wechselkurs verfaelscht.
    Derselbe Fehler ist am 12.08. in `leite_zonen_ab()` schon einmal
    passiert (Spanne 14,4 % zu breit)."""
    if str(instrument) != "hebel":
        return []
    if not close or close <= 0 or not atr or atr <= 0:
        return []
    teile = [f"bei {h:.0f}-fach {100.0 / h:.0f} %, also "
             f"{(float(close) / h) / float(atr):.1f} Schwankungsbreiten"
             for h in GRENZHEBEL]
    return ["Der Abstand zur Zwangsaufloesung haengt allein am Hebelfaktor: "
            + "; ".join(teile) + ".",
            "Welcher Faktor es wird, folgt aus dem Risikobudget und dem "
            "Stopabstand, den du nennst - gerechnet wird er nach deiner "
            "Antwort."]


def _referenz(referenz: dict | None) -> list[str]:
    """Der Sektorbezug eines Themen-ETF - relative Staerke zum breiten Markt.

    WARUM ES DEN BLOCK GIBT (Kapitel 35.5). *"Ein Kupfer-ETF folgt dem
    Kupferpreis, nicht seinem eigenen Chart."* Bis heute lieferten wir nur
    den eigenen Chart. Der Bezug zum breiten Markt ist die tragende
    Information dieser Gruppe und die einzige, die sagt, ob eine Bewegung dem
    Thema gehoert oder allen.

    NICHTS NEU GEHOLT. Die Groesse gibt es seit langem - `themen_etf/
    pipeline._compute_sektor_rotation()` rechnet sie gegen dieselbe
    SPY-Reihe. Sie war nur an die alte Pipeline gebunden und hat die
    Rollen-Kette nie erreicht. Das ist keine neue Datenquelle, sondern eine
    Verdrahtung.

    KEINE BEWERTUNG (R-T3). "Outperformance" und "in Rotation" sind Etiketten;
    hier steht, um wieviel Prozentpunkte die Reihe besser oder schlechter lief,
    ueber ein benanntes Fenster (R-T1).

    FUER DIE ABSICHERUNG NICHT. DBPK und 3QSS nennen ihren Referenzindex
    bereits in ihrem eigenen Block (`absicherung_fakten.saetze()`: "hebelt
    3-fach auf den Nasdaq-100"). Die LAGE dieses Index gehoert nach der
    Aufteilung LLM1/LLM2 zur zweiten Stufe, nicht hierher."""
    if not referenz:
        return []
    z = []
    for tage, schluessel in ((30, "rel_30"), (90, "rel_90")):
        wert = referenz.get(schluessel)
        if wert is None:
            continue
        wie = "besser" if wert >= 0 else "schlechter"
        z.append(f"Ueber die letzten {tage} Handelstage lief dieser Wert "
                 f"{abs(float(wert)):.1f} Prozentpunkte {wie} als "
                 f"{referenz.get('name', 'der breite Markt')}.")
    return z


def _luecken(hist_laenge: int, volumen: list, marken: list) -> list[str]:
    """Was FEHLT - benannt, statt stillschweigend weggelassen.

    DIE ERSTE KORREKTUR AUS DER BESTANDSERHEBUNG (Kapitel 34.6): acht von 56
    Assets urteilen unvollstaendig, und der Faktensatz sagt es nicht. Vier
    Rohstoff-Zertifikate und 3QSS fuehren in unserer Reihe kein Volumen; das
    Modell sieht dann keinen Volumensatz und liest Abwesenheit als
    UNAUFFAELLIGKEIT statt als NICHT VORHANDEN.

    Das ist der KAS-Fall in anderer Gestalt: dort fehlte der Bestand im
    Prompt, und das Modell kaufte in eine Verlustposition nach. Ein Fakt, den
    niemand nennt, wird nicht als fehlend gelesen - er wird gar nicht gelesen.

    DIE SPANNUNG ZU R-T6 IST ECHT UND WIRD IN KAUF GENOMMEN. Fuer alle vier
    Rohstoff-Zertifikate steht hier derselbe Satz - innerhalb der Gruppe also
    ein konstantes Feld. Er unterscheidet aber die GRUPPEN voneinander, und
    genau das ist seine Aufgabe: er sagt einem Urteil ueber OD7C, dass es auf
    einem Block weniger steht als ein Urteil ueber SOL. R-T6 verbietet
    stehende Felder, weil sie nichts trennen; dieses trennt.

    KEINE HANDLUNGSANWEISUNG. "deshalb vorsichtiger sein" waere ein Regelwerk
    im Faktentext und zugleich gelb im Sinne der Risikoklassen - der
    Kostenhinweis hat gezeigt, was ein bewertender Zusatz anrichtet. Hier
    steht nur, was fehlt."""
    z = []
    if not volumen:
        # "WIRD KEIN UMSATZ AUSGEWIESEN", nicht "liegen keine Daten vor".
        # Der Unterschied ist an ISOC aufgefallen: dort steht der Umsatz nicht
        # auf NULL-Werten, sondern auf 2.517 gemeldeten Nullen. Beides fuehrt
        # zu keinem Volumensatz, und beides heisst fuer das Urteil dasselbe -
        # aber "keine Daten" waere fuer ISOC schlicht falsch, und ein Fakt,
        # der ueber sich selbst die Unwahrheit sagt, ist schlimmer als keiner.
        z.append("Fuer dieses Instrument wird KEIN Umsatz ausgewiesen. Das "
                 "ist eine fehlende Angabe, kein unauffaelliger Umsatz - "
                 "ueber die Beteiligung am Markt sagt diese Beschreibung "
                 "nichts.")
    if len(marken) < 2:
        z.append("Es liess sich weniger als eine Marke oberhalb UND eine "
                 "unterhalb bestimmen; die Lage zwischen zwei Niveaus ist "
                 "hier also nur teilweise beschrieben.")
    # 250 Handelstage: dieselbe Grenze, die `_volumen()` und `marktlage.py`
    # fuer ihre Perzentile brauchen. Darunter ist ein Perzentil nicht falsch,
    # aber es vergleicht gegen eine kuerzere Geschichte, als der Satz behauptet.
    if hist_laenge < 250:
        z.append(f"Die Kursreihe umfasst erst {hist_laenge} Handelstage. "
                 f"Vergleiche ueber ein volles Jahr sind hier nicht moeglich; "
                 f"alle Einordnungen stehen auf einer kuerzeren Geschichte.")
    return z


def beschreibe_lage(*, symbol: str, reihe: list, index: int,
                    kurs_eur: float, atr: float,
                    menge: float | None = None,
                    einstand_eur: float | None = None,
                    finanzierung: dict | None = None,
                    instrument: str = "spot",
                    gegenseite: str | None = None,
                    referenz: dict | None = None,
                    bloecke_ziel: dict | None = None) -> list[str]:
    """Die Lage als Aussagen - der EINZIGE Weg von Kursdaten zur Beschreibung.

    `bloecke_ziel` (15.08.2026) ist ein AUSGANG, kein Eingang: wird ein dict
    uebergeben, stehen darin hinterher die Bloecke einzeln. Der Anlassfilter
    (O-36) braucht sie, um sagen zu koennen, WELCHER Block eine Frage neu
    gemacht hat - und er darf sie nicht ein zweites Mal rechnen, weil die
    Finanzierung dafuer erneut an die Boerse muesste.

    WARUM NICHT ALS RUECKGABEWERT: `beschreibe_lage()` gibt die flache Liste,
    und die geht so in den Prompt. Ein zweiter Rueckgabewert haette jeden
    Aufrufer gebrochen, ein zusaetzlicher SCHLUESSEL im Faktensatz waere im
    Prompt gelandet und haette alle bisherigen Messungen unvergleichbar
    gemacht.

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

    # EINMAL RECHNEN, ZWEIMAL BRAUCHEN. Vorher stand `geteilt()` INNERHALB
    # der Schleife - also einmal je Block, sechsmal dieselbe Rechnung ueber
    # dieselbe Reihe. Jetzt einmal, und das Ergebnis geht auf Wunsch nach
    # draussen: der Anlassfilter braucht die Bloecke einzeln und darf sie
    # nicht neu rechnen, weil die Finanzierung dafuer wieder an die Boerse
    # muesste.
    bloecke = geteilt(symbol=symbol, reihe=reihe, index=index,
                      kurs_eur=kurs_eur, atr=atr, menge=menge,
                      einstand_eur=einstand_eur, finanzierung=finanzierung,
                      instrument=instrument, gegenseite=gegenseite,
                      referenz=referenz)
    if bloecke_ziel is not None:
        bloecke_ziel.clear()
        bloecke_ziel.update(bloecke)
    return [satz for block in BLOCK_REIHENFOLGE for satz in bloecke[block]]


# Die Bloecke in genau der Reihenfolge, in der sie im Prompt stehen. Sie ist
# NICHT kosmetisch: R-T9 - was zuerst steht, wiegt schwerer.
#
# DREI NEUE BLOECKE (Phase I, 16.08.2026) - und die RELATIVE Reihenfolge der
# sechs alten bleibt unveraendert. Das ist Absicht: die neuen Bloecke sind
# eingeschoben, nicht dazwischengemischt. Ein Vergleich zweier Prompt-Staende
# soll den Unterschied als HINZUGEKOMMEN lesen koennen und nicht zusaetzlich
# eine Umsortierung mitmessen muessen.
#
#   hebelgeometrie  direkt nach `marken` - es ist dieselbe Art Aussage
#                   (ein Preisabstand in Schwankungsbreiten) und sie gehoert
#                   neben Widerstand und Unterstuetzung gelesen
#   referenz        daneben, aus demselben Grund: eine Einordnung von aussen
#   luecken         ZULETZT. Was fehlt, soll gesagt sein - aber es darf nicht
#                   schwerer wiegen als das, was da ist (R-T9)
#
# `struktur` UND `bewegung` SIND EIN BLOCK GEWORDEN (16.08.2026): `verlauf`.
# Grund und Messwert stehen bei `_struktur()`. Die Saetze selbst sind
# unveraendert bis auf die entfallene Doppelung und den Bezug "im selben
# Rahmen" - die Reihenfolge der uebrigen Bloecke bleibt, wie sie war.
BLOCK_REIHENFOLGE = ("bestand", "verlauf", "marken",
                     "hebelgeometrie", "referenz", "volumen",
                     "finanzierung", "luecken")


def geteilt(*, symbol: str, reihe: list, index: int,
            kurs_eur: float, atr: float,
            menge: float | None = None,
            einstand_eur: float | None = None,
            finanzierung: dict | None = None,
            instrument: str = "spot",
            gegenseite: str | None = None,
            referenz: dict | None = None) -> dict:
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
    marken = _niveaus(c, h, l, i, atr, kurs_eur, float(c[i]))
    volumen = _volumen(c, v, i, tag_vollstaendig)
    return {
        "bestand": _bestand(symbol, menge, einstand_eur, kurs_eur,
                            instrument=instrument, gegenseite=gegenseite),
        # EIN BLOCK, ZWEI SATZBAUER. Die Funktionen bleiben getrennt - sie
        # rechnen Verschiedenes (Wendepunkte bzw. Prozentveraenderungen) -,
        # aber ihre Saetze gehoeren zusammen gelesen und werden deshalb
        # zusammen gezaehlt. Der Anlassfilter sieht damit EINEN Abdruck fuer
        # den Verlauf statt zweier, die sich gemeinsam bewegen.
        "verlauf": _struktur(c, h, l, i) + _bewegung(c, i),
        "marken": marken,
        "hebelgeometrie": _hebelgeometrie(atr, float(c[i]), instrument),
        "referenz": _referenz(referenz),
        "volumen": volumen,
        "finanzierung": _finanzierung(finanzierung, instrument),
        # DIE LUECKEN STEHEN AUF DEN FERTIGEN BLOECKEN, nicht auf den Rohdaten.
        # Sonst gaebe es eine zweite Definition von "kein Volumen" - eine im
        # Block und eine im Luecken-Satz -, und sie koennten auseinanderlaufen,
        # ohne dass eine Pruefung anschlaegt. Dieselbe Ueberlegung wie bei
        # `geteilt()` selbst.
        "luecken": _luecken(len(hist), volumen, marken),
    }
