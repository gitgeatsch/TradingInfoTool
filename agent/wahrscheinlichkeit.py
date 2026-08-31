# -*- coding: utf-8 -*-
"""Wie wahrscheinlich traegt dieser Trade? (22.08.2026)

DAS IST DAS EIGENTLICHE ZIEL DES SYSTEMS, und es war bis heute nicht gebaut.

Nutzereinwand, woertlich: *"Gefuehlt werden die Infos in die eMail uebernommen
- aber das System kann diese Informationen nicht SELBST in Zusammenhang
bringen und eine Bewertung bzw. Wahrscheinlichkeit zum gesamten Trade bzw.
Signal durchzufuehren - was das eigentliche Ziel des Systems ist und war."*

Er hat recht. `gesamtbild.py` ZAEHLT Etiketten ("1 spricht dafuer, 1 dagegen,
2 noch nicht bewertbar") - das ist eine Strichliste und laesst die
Zusammenfuehrung beim Leser. Genau die Arbeit, die das System machen soll.

⚠️ WARUM DAS FRUEHER RICHTIG WAR UND JETZT NICHT MEHR. Bis Kapitel 118 gab es
nichts Gemessenes zu addieren; eine Zahl zu bauen haette Sicherheit
vorgetaeuscht, wo keine war. Seit 119-122 gibt es zwei belastbare Groessen -
die Basisrate aus der Geometrie und den Vorsprung von H. Damit ist die
Zusammenfuehrung keine Behauptung mehr, sondern eine Rechnung.

DIE RECHNUNG, VOLLSTAENDIG:

    Basisrate   = 1 / (1 + CRV)          driftfreier Pfad, reine Arithmetik
    + Beitraege                          nur GEMESSENE Punkte
    = Quote                              geschaetzte Trefferquote
    Breakeven   = (1 + Kosten_R) / (1 + CRV)
    Kosten_R    = 2 * Gebuehr / Stopabstand
    Abstand     = Quote - Breakeven      DAS ist die Aussage

⚠️ WAS DIESE ZAHL NICHT IST. Keine Prognose fuer diesen einen Trade, sondern
die gemessene Haeufigkeit in einer Gruppe, zu der er gehoert. Und das LLM
steckt NICHT darin - dessen Urteil kommt daneben, nicht hinein
(Nutzervorgabe: "die LLM Bewertungen kommen dann on top").

⚠️ UND SIE IST ERWEITERBAR GEBAUT, WEIL SIE ES SEIN MUSS. Nutzervorgabe:
*"Wir muessen aus dem Fleckerteppich ein stabiles und erweiterbares System
bauen was auf einer guten Grundlage basiert."* Deshalb eine REGISTRIERUNG:
jeder Beitrag ist ein Eintrag mit Wert, Zustand, Quelle und Begruendung.
Kommt einer dazu oder wechselt seinen Zustand, ist das EINE Zeile - kein
Umbau der Rechnung, keine zweite Stelle, die auseinanderlaufen kann.

VIER ZUSTAENDE, DIE NIE VERSCHMELZEN - dieselbe Lehre wie bei
`lebendigkeit.ZUSTAENDE`:

    traegt        gemessen und ueber der Zufallsschwelle -> geht in die Zahl
    enthalten     steckt bereits in der Basisrate -> darf NICHT zweimal zaehlen
    null          gemessen und zu klein -> geht NICHT ein, wird GENANNT
    noch_nicht    die eigene Reihe ist zu kurz -> wird genannt, mit Termin
    nie           nie gemessen -> wird genannt, ohne Versprechen

Der Unterschied zwischen `null` und `nie` ist der wichtige: das eine heisst
"geprueft und zu klein", das andere "wir wissen es nicht". Wer sie
zusammenwirft, verliert genau die Information, die sagt, wo sich Arbeit lohnt.
"""
from __future__ import annotations

from dataclasses import dataclass

# ---------------------------------------------------------------------------
# DIE BASISRATE. Reine Arithmetik, kein Messwert - aber gemessen bestaetigt.
# ---------------------------------------------------------------------------
# Auf einem driftfreien Pfad trifft ein Barrierensystem sein Ziel mit
# 1/(1+CRV). Bei CRV 2,0 sind das 33,3 %; gemessen wurden 34,0 % ueber 19.891
# Anker - die 0,7 Punkte sind der leichte Aufwaertsdrift des Marktes.
#
# ⚠️ WIR RECHNEN MIT DER ARITHMETIK, NICHT MIT DEN 34,0 %. Der Drift ist
# nicht garantiert, und ihn einzurechnen hiesse, den guenstigsten der beiden
# Werte zu nehmen. Die vorsichtige Lesart ist hier die richtige.
BASISRATE_GEMESSEN = 0.340
BASISRATE_ANKER = 19891


def basisrate(crv: float) -> float:
    """Trefferquote eines Barrierensystems auf driftfreiem Pfad."""
    if not crv or float(crv) <= 0:
        raise WahrscheinlichkeitUnbekannt(f"CRV {crv!r} ist nicht positiv")
    return 1.0 / (1.0 + float(crv))


class WahrscheinlichkeitUnbekannt(RuntimeError):
    """Lieber keine Zahl als eine erfundene."""


@dataclass(frozen=True)
class Beitrag:
    """Ein Merkmal und was es zur Trefferquote beitraegt.

    ⚠️ ZWEI BAUFORMEN, und der Unterschied ist der Kern des Umbaus vom
    30.08.2026 (G-2' Schritt 2b):

        SCHALTER    `punkte` gesetzt, `stufen` leer
                    Das Merkmal trifft zu oder nicht - wie Vorfilter H.
        ABGESTUFT   `stufen` gesetzt, `punkte` bleibt 0.0
                    Ein Wert je Fuenftel, von 0 (niedrigster Rang) bis 4.
                    So tragen Funding und Turnover: nicht ja/nein, sondern
                    wo im Markt dieser Wert heute steht.

    `merkmal` ist der Schluessel, unter dem der Wert an `rechne()` uebergeben
    wird. Er ersetzt die Namensabfrage - bis zum 30.08. hing H an
    `b.name.startswith("Vorfilter H")`, und ein zweiter Sonderfall daneben
    haette die Struktur zerfallen lassen.

    ⚠️ SCHRITT 2b AENDERT NOCH NICHTS. Die Felder stehen bereit, `rechne()`
    liest sie noch nicht. Der Bitgleichheitstest muss unveraendert 0 FEHL
    liefern - genau das ist der Zweck dieser Reihenfolge.
    """
    name: str
    zustand: str          # traegt | null | noch_nicht | nie
    punkte: float         # Prozentpunkte; nur bei `traegt` ungleich null
    quelle: str           # woher die Zahl stammt
    warum: str            # warum sie so ist, in einem Satz
    klassen: tuple = ()    # leer = alle; sonst nur diese Anlageklassen
    strategien: tuple = ()  # leer = alle; sonst einstieg | swing | akkumulation
    richtungen: tuple = ()  # leer = alle; sonst long | short
    stufen: tuple = ()     # abgestuft: Punkte je Fuenftel 0..4
    merkmal: str = ""      # Schluessel in `merkmale`; leer = kein Eingabewert
    klammer: str = ""      # unter WELCHEM Vergleich gemessen - siehe unten

    def __post_init__(self):
        """Widersprueche fallen beim Import auf, nicht im Betrieb."""
        if self.stufen:
            if len(self.stufen) != 5:
                raise ValueError(
                    "%s: `stufen` braucht genau 5 Werte (ein Fuenftel je "
                    "Rangplatz), hat aber %d" % (self.name, len(self.stufen)))
            if self.punkte:
                raise ValueError(
                    "%s: `punkte` UND `stufen` gesetzt - dann waere unklar, "
                    "welcher Wert gilt. Abgestufte Beitraege lassen `punkte` "
                    "auf 0.0" % self.name)
            if not self.merkmal:
                raise ValueError(
                    "%s: `stufen` ohne `merkmal` - der Wert kaeme nie an"
                    % self.name)

        # ⚠️⚠️ DIE REGEL, DIE DEN H-FEHLER STRUKTURELL UNMOEGLICH MACHT
        # (31.08.2026). H stand elf Tage lang mit +4,5 Punkten im Betrieb,
        # weil niemand fragte, unter WELCHEM Vergleich diese Zahl entstanden
        # war. Frisch reproduziert (`pruefe_h_original_reproduziert.py`,
        # 609.527 Anker, ohne Zwischenspeicher):
        #
        #     GEPOOLT ueber alles     +3,57 Punkte    <- so wurde gemessen
        #     je 120-Tage-Block       -3,43 Punkte    nicht trennbar
        #     je KALENDERTAG          -1,02 Punkte    nicht trennbar
        #                             [-2,18 .. +0,14] bei 791 Einheiten
        #
        # Die Tagesmessung haette +3,57 um das Dreifache ihrer Intervall-
        # breite gefunden. Sie findet nichts. Der Originalbefund beantwortet
        # also die Frage "an welchen TAGEN tritt H auf", nicht "welches
        # Asset ist heute besser" - und nur die zweite stellt Stufe 11.
        #
        # DESHALB: Wer `traegt` sagt, muss die Klammer nennen. Erlaubt ist
        # dafuer allein `tag` - der Vergleich gegen andere Werte DESSELBEN
        # Kalendertags. Genau so sind Funding und Turnover gemessen.
        if self.zustand == "traegt" and self.klammer != "tag":
            raise ValueError(
                "%s: zustand='traegt' verlangt klammer='tag'. Ein gepoolt "
                "oder je Zeitblock gemessener Vorsprung beschreibt die LAGE, "
                "in der ein Merkmal auftritt - nicht die Guete der Anker, die "
                "es auswaehlt. Genau daran ist H gescheitert (+3,57 gepoolt, "
                "-1,02 je Kalendertag). Erst je Kalendertag messen, dann "
                "registrieren." % self.name)
        if self.klammer and self.klammer not in KLAMMERN:
            raise ValueError(
                "%s: klammer=%r ist unbekannt - erlaubt sind %s"
                % (self.name, self.klammer, ", ".join(KLAMMERN)))


ZUSTAENDE = ("traegt", "enthalten", "null", "noch_nicht", "nie")

# ⚠️ UNTER WELCHEM VERGLEICH WURDE GEMESSEN? Die Frage, die H elf Tage lang
# niemand gestellt hat.
#
#   tag       gegen andere Werte DESSELBEN Kalendertags. Beantwortet
#             "welches Asset ist HEUTE besser" - die Frage von Stufe 11.
#             ⚠️ NUR DIESE Klammer erlaubt `zustand="traegt"`.
#   block     gegen Anker desselben Zeitblocks (z. B. 120 Tage). Haelt die
#             Marktphase grob fest, laesst die Tageswahl aber offen.
#   gepoolt   gegen alle Anker der Historie. Beantwortet "an welchen Tagen
#             tritt das Merkmal auf" - eine LAGE-Aussage.
#
# Der Unterschied ist nicht akademisch: bei H betrug er 4,6 Punkte
# (+3,57 gepoolt gegen -1,02 je Tag), bei "Boden unten" 0,20 R
# (-0,2023 je Block gegen -0,0019 je Tag).
KLAMMERN = ("tag", "block", "gepoolt")


# ---------------------------------------------------------------------------
# DIE REGISTRIERUNG. Hier wird erweitert - nirgends sonst.
# ---------------------------------------------------------------------------
#
# ⚠️⚠️ WO KALIBRIERTE ZAHLEN STEHEN - DIE VOLLSTAENDIGE LISTE (30.08.2026)
#
# Nutzervorgabe: *"sofort ersichtlich, wo was zu aendern ist, oder eben nur an
# einer Stelle."* Es sind DREI Stellen, und sie bedeuten VERSCHIEDENES:
#
#   agent/vorfilter.GEMESSEN        WAS GEMESSEN WURDE
#                                   +4,5 Punkte, 523 Reihen, Kapitel 108-122.
#                                   Geht in die Mail als Beleg.
#
#   BEITRAEGE hier drunter          WAS WIR DAVON ANSETZEN
#                                   Darf KONSERVATIVER sein als der Messwert -
#                                   und ist es, sobald ein Befund episodisch
#                                   oder nur in-sample belegt ist.
#
#   agent/potential.SCHWELLE_VORGABE  AB WANN ES REICHT
#   agent/potential.KALIBRIERT_FUER   ...und fuer welche Beitragslage
#
# ⚠️ SIE DUERFEN AUSEINANDERLAUFEN - aber BEWUSST. Deshalb sind sie nicht
# zusammengefasst: waere der angesetzte Wert an den gemessenen gekettet,
# koennte man einen episodischen Befund nicht vorsichtig ansetzen.
#
# ⚠️ DAMIT ES NICHT VERSEHENTLICH GESCHIEHT, haelt Paket "Kalibrierung" in
# `pruefe_pakete.py` die Beziehung fest. Wer hier eine Zahl aendert, bekommt
# dort eine Meldung - mit dem Hinweis, was sonst noch nachzuziehen ist:
#
#     1. `potential.KALIBRIERT_FUER` auf die neue Beitragslage
#     2. Schwelle neu kalibrieren (R-R9, Methodik 2.93)
#     3. `Befundkarte.md` 3.9 und dieses Kapitel nachziehen
#
BEITRAEGE = (
    # ---- R1: H FAELLT ALS BEITRAG (31.08.2026) --------------------------
    #
    # ⚠️ NICHT "H TAUGT NICHTS", SONDERN: H BEANTWORTET EINE ANDERE FRAGE.
    # Der Originalbefund ist am 31.08. frisch reproduziert worden
    # (`pruefe_h_original_reproduziert.py`, 609.527 Anker, ohne
    # Zwischenspeicher) - er ist echt, aber gepoolt:
    #
    #     GEPOOLT ueber die ganze Historie   +3,57 Punkte
    #     je 120-Tage-Block                  -3,43   nicht trennbar
    #     je KALENDERTAG                     -1,02   nicht trennbar
    #                                        [-2,18 .. +0,14], 791 Einheiten
    #
    # Die Tagesmessung haette +3,57 um das Dreifache ihrer Intervallbreite
    # gefunden. Sie findet nichts. Damit misst der Originalbefund, an
    # welchen TAGEN H auftritt - nicht, welches Asset heute besser ist.
    # Stufe 11 stellt aber genau die zweite Frage.
    #
    # H IST IN VIER FORMEN UND UNTER DREI KLAMMERN GEMESSEN WORDEN:
    #
    #     H = A UND B          auf drei Geometrien negativ bis nicht trennbar
    #     A allein             +0,0089 R, zieht in BEIDEN B-Schichten nach
    #                          unten (-0,0568 / -0,1451)
    #     B allein             je Block -0,2023 R, je Kalendertag -0,0019 R
    #                          [-0,0257 .. +0,0212] - nicht trennbar
    #     Bodenabstand stetig  U-foermig, Spanne -0,0588 R, Regel netto
    #                          -0,0011 R (sperrt die BESSEREN Anker)
    #
    # Keine traegt unter der Tagesklammer, unter der Funding und Turnover
    # getragen haben. Die Messkette selbst ist validiert
    # (`pruefe_h_kette_von_grund_auf.py`): kein Lookahead, Messung und
    # `vorfilter.bewerte()` urteilen 36/36 identisch, fuenf
    # Zwischenspeicher untereinander konsistent.
    #
    # ⚠️ WAS BLEIBT: die Marken tragen weiterhin den STOP
    # (`entscheidungsrechnung._boeden`, Kapitel 124: -0,0008 R, unschaedlich)
    # - die Verwendung, die auch die Lehrmeinung nennt. Nur als
    # BEWERTUNGSbeitrag tragen sie nicht.
    #
    # ⚠️ WIRKUNG DES WEGFALLS, gemessen (`simuliere_h_varianten.py`,
    # 619.242 Anker): Durchlass 45,5 % -> 44,2 %, Ertrag -0,2098 ->
    # -0,2114 R. 1,2 Punkte und 0,0016 R.
    Beitrag(
        name="Vorfilter H (Weg frei, Stop gedeckt)",
        zustand="null", punkte=0.0, merkmal="h", klammer="gepoolt",
        quelle=("Kapitel 108-122 gepoolt +3,57; je Kalendertag -1,02 "
                "[-2,18 .. +0,14] (31.08.2026, 609.527 Anker)"),
        warum=("gepoolt gemessen und deshalb eine LAGE-Aussage: sagt, an "
               "welchen Tagen H auftritt, nicht welches Asset heute besser "
               "ist. Unter der Tagesklammer nicht von null zu trennen - "
               "ebenso A allein, B allein und der stetige Bodenabstand. "
               "Die Marken tragen weiterhin den Stop"),
        klassen=("krypto",)),
    # ⚠️ NICHT "TRAEGT NICHTS", SONDERN "TRAEGT NEGATIV" (Kapitel 125,
    # 22.08.2026). Auf Nutzerwunsch wurde gefragt, ob sich der Rangplatz so
    # bauen laesst, dass er beitraegt - die Antwort ist deutlicher als
    # erwartet: INNERHALB von H schneidet das beste Fuenftel um 5,8 Punkte
    # SCHLECHTER ab (14.238 Anker, Schwelle +1,8, stabil ueber die Deckel
    # 20/60/120 Tage). Netto je Trade zum Referenzsatz: -0,000 R gegen
    # +0,172 R fuer das uebrige Feld.
    #
    # Ihn als positiven Beitrag zu fuehren waere also nicht nur wirkungslos,
    # sondern schaedlich. Er bleibt `null` - und der Grund steht daneben.
    Beitrag(
        name="Rangplatz in der Anlageklasse",
        zustand="null", punkte=0.0,
        quelle="Kapitel 125, 14.238 H-Anker mit Rangplatz",
        warum=("als ZUSATZbedingung innerhalb von H 5,8 Punkte "
               "SCHLECHTER (Schwelle +1,8). Seit dem 23.08. steht er "
               "deshalb eine Ebene HOEHER: er waehlt aus, WELCHE Werte "
               "beurteilt werden, und geht in diese Zahl bewusst nicht "
               "ein - sonst zaehlte dieselbe Groesse zweimal"),
        klassen=("krypto",)),
    # ---- 2e: DIE ERSTEN ABGESTUFTEN BEITRAEGE (30.08.2026) --------------
    #
    # ⚠️ WARUM SIE UEBERHAUPT GEBRAUCHT WERDEN, und nicht nur "weil sie
    # tragen": bis heute war H der EINZIGE Beitrag. Gemessen an Stufe 11
    # hiess das
    #
    #     h = True         Potential +0,1350 R  -> durch
    #     h = False/None   Potential -0,0000 R  -> gesperrt
    #
    # Ein System mit genau einem Beitrag kann diesen Beitrag nicht mehr
    # pruefen: jede Aenderung an ihm legt den ganzen Trichter stumm. Genau
    # das war am 30.08. der Fall, als H auf drei Geometrien negativ gemessen
    # wurde und trotzdem nicht angefasst werden konnte.
    #
    # ⚠️ BEIDE SIND ALS REGEL GEMESSEN, nicht als Merkmal (R-R8, Methodik
    # 2.87) - der Unterschied betrug bei Funding den Faktor 5,5.
    #
    # ⚠️ DIE STUFEN SIND GESCHRUMPFT (halbiert). Die Kalibrierung ist
    # in-sample, dieselbe Vorsicht wie bei `trefferbilanz.geschrumpft()`.
    # Wer sie aendert: `rechne_funding_beitrag.py` und
    # `rechne_turnover_beitrag.py` liefern die Zahlen, sonst nichts.
    #
    # ⚠️ FUENFTEL 0 IST DER NIEDRIGSTE ROHWERT (`marktrang._rang` sortiert
    # aufsteigend). Bei beiden Groessen ist niedrig das Gute - viel Funding
    # heisst ueberhitzt, viel Turnover heisst ueberbewertet. Wer die
    # Sortierrichtung dreht, dreht die Beitraege ins Gegenteil, ohne dass
    # eine Pruefung anschlaegt.
    Beitrag(
        name="Funding-Rang im Markt",
        zustand="traegt", punkte=0.0, merkmal="funding_fuenftel",
        stufen=(+0.82, +1.30, +0.12, -0.54, -1.70), klammer="tag",
        quelle=("rechne_funding_beitrag.py, 2.369 Kalendertage, 290 Symbole, "
                "6,3 Jahre; Regelwirkung +0,0246 R"),
        warum=("Querschnittsrang: wer heute am wenigsten Finanzierung zahlt. "
               "Traegt in beiden Historienhaelften und beiden Marktphasen, "
               "monoton ueber fuenf Fuenftel, Momentum-Korrelation +0,002"),
        klassen=("krypto",)),
    Beitrag(
        name="Turnover-Rang im Markt",
        zustand="traegt", punkte=0.0, merkmal="turnover_fuenftel",
        stufen=(+3.15, +0.83, +0.22, -1.79, -2.40), klammer="tag",
        quelle=("rechne_turnover_beitrag.py, 2.636 Kalendertage; "
                "Regelwirkung +0,0616 R"),
        warum=("Handelsvolumen je Umlaufmenge - viel Aufmerksamkeit heisst "
               "eher ueberbewertet. Zu 92 % additiv zu Funding "
               "(Korrelation -0,158), Survivorship ausgeraeumt"),
        klassen=("krypto",)),
    # ---- P3: DER BEITRAG, DER BEI ALLEN ASSETS WIRKT (31.08.2026) -------
    #
    # ⚠️ WARUM ER GEBRAUCHT WIRD, obwohl Funding und Turnover tragen:
    # beide kommen aus FREMDQUELLEN und haben deshalb zwangslaeufig
    # Luecken. Nach dem Nachladen am 31.08. blieben 7 von 43 Werten ohne
    # jeden Beitrag - Binance und CoinGecko listen nicht jeden Wert.
    #
    # Nutzervorgabe 31.08.: *"Krypto muss und braucht einen Entscheider,
    # der bei ALLEN Assets wirkt."* Ein Beitrag aus der eigenen KURSREIHE
    # ist der einzige, der das kann. Genau das war die Eigenschaft von
    # Vorfilter H, und sie fehlte seinen Nachfolgern.
    #
    # GEMESSEN (`messe_schnittabstand_beitrag.py`, 655.813 Anker,
    # 3.072 Kalendertage, 523 Reihen):
    #
    #   Abdeckung          523 von 523 Messreihen (100 %)
    #   Tabelle            +1,27 / +1,59 / +0,24 / -1,28 / -1,82
    #   Symbolzahl         >=15: +3,09 · >=250: +2,57  -> robust
    #   beide Haelften     +3,61 / +2,69  gleiches Vorzeichen
    #   Survivorship       lebend +2,59 · eingestellt +4,70
    #   Placebo-Band       [-0,26 .. +0,30], echt +3,09 -> ausserhalb
    #   ALS REGEL          20,2 % gesperrt, Gesperrte -0,4577 gegen
    #                      -0,3962, netto +0,0136 R
    #   additiv            Korrelation zu Funding +0,091; traegt in ALLEN
    #                      fuenf Funding-Fuenfteln (+2,85 .. +4,43)
    #
    # ⚠️ 2018-2020 traegt er kaum (+0,72). Nutzerentscheidung 31.08.:
    # *"2018 2020 - ist OK, da der Markt nun ein anderer ist."*
    #
    # ⚠️ DER RANG MUSS UEBER DIE MESSBASIS LAUFEN. Ueber die Watchlist
    # gerangt DREHT DAS VORZEICHEN (+3,43 gegen -3,10, nur 54 %
    # identische Fuenftel). `marktrang.schnitt_werte()` haelt das ein.
    Beitrag(
        name="Abstand zum eigenen 200-Tage-Schnitt",
        zustand="traegt", punkte=0.0, merkmal="schnitt_fuenftel",
        stufen=(+1.27, +1.59, +0.24, -1.28, -1.82), klammer="tag",
        quelle=("messe_schnittabstand_beitrag.py, 655.813 Anker, "
                "3.072 Kalendertage, 523 Reihen; Regelwirkung +0,0136 R"),
        warum=("Wer heute tief unter seinem eigenen 200-Tage-Schnitt "
               "steht, bewegt sich in den naechsten Wochen staerker "
               "aufwaerts als wer weit darueber steht - am selben Tag "
               "verglichen. Aus der Kursreihe, also fuer JEDEN Wert "
               "verfuegbar"),
        klassen=("krypto",)),
    Beitrag(
        name="Lebendigkeit des Projekts",
        zustand="noch_nicht", punkte=0.0,
        quelle="93 C, sammelt seit 20.08.2026",
        warum="30 Tagesmessungen noetig, auswertbar ab 18.09.2026",
        klassen=("krypto",)),
    Beitrag(
        name="Bekannte Termine",
        zustand="nie", punkte=0.0,
        quelle="93 D",
        warum="Anzeige, nie gegen den Zufall gemessen"),
    Beitrag(
        name="Trichter (uebliche Kursbewegung)",
        zustand="enthalten", punkte=0.0,
        quelle="Kapitel 101",
        warum=("er BESTIMMT die Geometrie und damit die Basisrate - er ist "
               "schon drin und darf nicht zweimal zaehlen")),
)


def _gilt(b: Beitrag, klasse: str, strategie: str = "",
          richtung: str = "") -> tuple[bool, str]:
    """Gilt dieser Beitrag hier - und wenn nicht, warum?

    ⚠️ DREI ACHSEN SEIT DEM 30.08.2026 (G-2' Schritt 2c). Vorher gab es nur
    `klassen`, und die Bedingung "H nur bei Long" stand deshalb in
    `vorfilter.py` - also beim LIEFERANTEN des Werts statt beim Beitrag.
    Das funktioniert, verteilt aber das Wissen: jeder neue Aufrufer haette
    die Regel kennen muessen.

    Jetzt deklariert jeder Beitrag selbst, wo er gilt. Was nicht passt,
    bekommt `zustand="nie"` MIT Begruendung - nie eine stille Null.
    """
    if b.klassen and str(klasse or "").lower() not in b.klassen:
        # ⚠️ WOERTLICH wie vor dem 30.08. - dieser Satz steht in jeder Mail,
        # und der Bitgleichheitstest haelt ihn fest.
        return False, ("auf %s nie gemessen - %s steht auf Krypto"
                       % (klasse or "?", b.quelle))
    if b.strategien and str(strategie or "").lower() not in b.strategien:
        return False, ("fuer die Strategie %s nie gemessen - %s gilt fuer %s"
                       % (strategie or "?", b.name, "/".join(b.strategien)))
    if b.richtungen and str(richtung or "").lower() not in b.richtungen:
        return False, ("fuer %s nie gemessen - %s ist auf %s belegt"
                       % (richtung or "?", b.name, "/".join(b.richtungen)))
    return True, ""


def vermessen(klasse: str = "", strategie: str = "",
              richtung: str = "") -> list:
    """Welche tragenden Beitraege sind fuer DIESE Lage ueberhaupt registriert?

    ⚠️ DIE FRAGE, DIE AM 31.08. DEN ROLLOUT AUFGEHALTEN HAT.

    Die Kettensimulation gegen die Notebook-Produktion lieferte mit scharfer
    Stufe 11 **null Signale ueber alle fuenf Gruppen**. Ursache war nicht
    die Datenlage einzelner Werte, sondern eine Ebene darueber:

        krypto      3 tragende Beitraege
        aktien      0
        themen_etf  0
        rohstoffe   0
        hedge       0

    Alle drei Beitraege (Funding, Turnover, Schnittabstand) tragen
    `klassen=("krypto",)`. Fuer die uebrigen vier Klassen gibt es KEINE
    Messung - und ein Filter ohne Messgrundlage sperrt nach DATENLAGE,
    nicht nach Qualitaet.

    ## Warum das kein Aufweichen ist, sondern die Abgrenzung selbst

    Das uebergeordnete Ziel verlangt "eine neutrale, BEGRUENDETE Aussage
    ueber das Potential". "Fuer diese Klasse haben wir nie gemessen" ist
    ein FAKT ueber unseren Kenntnisstand - keine Aussage darueber, was
    kommt. Regel 4: **ein Fakt ist keine Begruendung.** Wer daraus eine
    Sperre macht, hat die Frage nicht beantwortet, sondern umformuliert.

    Und die Nutzervorgabe vom 31.08. sagt es woertlich fuer Krypto:
    *"Die Scharfschaltung muss und darf erst erfolgen, wenn alle Assets
    einen Beitrag haben."* Fuer die anderen vier Klassen gilt derselbe
    Satz - dort ist die Bedingung nur noch nicht erfuellt.

    ⚠️ UNTERSCHEIDE DREI ZUSTAENDE, nicht zwei:

        keine Beitraege registriert  ->  NICHT VERMESSEN  ->  nicht sperren
        registriert, Wert fehlt      ->  DATENLUECKE      ->  sperren
        registriert, Wert da         ->  BEWERTUNG        ->  entscheiden

    Der mittlere Fall bleibt scharf: bei einer Klasse, die wir vermessen
    haben, ist ein fehlender Wert ein Mangel dieses Assets - und Krypto
    hat seit P2 (Schnittabstand aus der eigenen Kursreihe) 43 von 43.
    """
    return [b for b in BEITRAEGE
            if b.zustand == "traegt" and _gilt(b, klasse, strategie,
                                               richtung)[0]]


def rechne(*, crv: float, stop_relativ: float, gebuehr_je_seite: float,
           klasse: str = "", h: bool | None = None, strategie: str = "",
           richtung: str = "", merkmale: dict | None = None) -> dict:
    """Die vollstaendige Rechnung. WIRFT, statt zu raten.

    `h` ist das Ergebnis von `vorfilter.bewerte()["h"]` - `None` heisst
    unbekannt und traegt dann nichts bei, ohne als Nein zu gelten."""
    if not stop_relativ or float(stop_relativ) <= 0:
        raise WahrscheinlichkeitUnbekannt(
            f"Stopabstand {stop_relativ!r} ist nicht positiv")
    if gebuehr_je_seite is None or float(gebuehr_je_seite) < 0:
        raise WahrscheinlichkeitUnbekannt("Gebuehr fehlt")
    basis = basisrate(crv)

    # ⚠️ H WIRD WIE JEDER ANDERE MERKMALSBEITRAG BEHANDELT (Schritt 2c,
    # 30.08.2026). Vorher stand hier `b.name.startswith("Vorfilter H")` -
    # ein Sonderfall am NAMEN. Der zweite Beitrag daneben (Funding, ein
    # Rangplatz aus fuenf Stufen) haette einen zweiten Namensvergleich
    # gebraucht, und damit waere die Registrierung zur Attrappe geworden.
    werte = dict(merkmale or {})
    if h is not None or "h" not in werte:
        werte.setdefault("h", h)

    zeilen, zuschlag = [], 0.0
    for b in BEITRAEGE:
        passt, grund = _gilt(b, klasse, strategie, richtung)
        if not passt:
            zeilen.append({"name": b.name, "zustand": "nie", "punkte": 0.0,
                           "warum": grund})
            continue
        zustand, punkte, warum = b.zustand, 0.0, b.warum
        if b.zustand == "traegt" and b.merkmal:
            wert = werte.get(b.merkmal)
            if wert is None:
                zustand, warum = "nie", "an diesem Anker nicht bestimmbar"
            elif b.stufen:
                # abgestuft: der Wert IST der Rangplatz 0..4
                stufe = max(0, min(int(wert), len(b.stufen) - 1))
                punkte = float(b.stufen[stufe])
            elif wert:
                punkte = b.punkte
            else:
                zustand, warum = "null", "trifft an diesem Anker NICHT zu"
        elif b.zustand == "traegt":
            punkte = b.punkte
        zuschlag += punkte
        zeilen.append({"name": b.name, "zustand": zustand,
                       "punkte": punkte, "warum": warum})

    quote = basis + zuschlag / 100.0
    kosten_r = 2.0 * float(gebuehr_je_seite) / float(stop_relativ)
    breakeven = (1.0 + kosten_r) / (1.0 + float(crv))
    return {"crv": float(crv), "basisrate": basis, "zuschlag_punkte": zuschlag,
            "quote": quote, "kosten_r": kosten_r, "breakeven": breakeven,
            "abstand_punkte": 100.0 * (quote - breakeven),
            "erwartungswert_r": quote * float(crv) - (1.0 - quote) - kosten_r,
            "beitraege": zeilen, "klasse": str(klasse or "").lower()}


def saetze(*, crv: float, stop_relativ: float, klasse: str = "",
           h: bool | None = None, saetze_zum_berichten=None,
           merkmale: dict | None = None) -> list[str]:
    """Die Zeilen fuer den Kopf der Mail.

    ⚠️ SIE SPERREN NICHTS. Auch "traegt nicht" ist kein Veto - es ist die
    Zusammenfassung dessen, was weiter unten ohnehin steht.

    ⚠️⚠️ `merkmale` FEHLTE BIS ZUM 31.08.2026 - UND DAS WAR EIN BRUCH.
    Die Mail rechnete OHNE die Merkmale, mit denen Stufe 11 entscheidet.
    Gemessen an einem Beispiel:

        Stufe 11 entscheidet   Potential +0,1191 R  (Quote 37,0 %)
        die Mail zeigte        33,3 % und "20,0 Punkte ZU WENIG"

    Der Leser bekam eine Rechnung zu sehen, die es so nicht gab - und
    zwar mit dem gegenteiligen Vorzeichen. Wer eine Empfehlung erhaelt,
    deren Begruendung ihr widerspricht, kann ihr nicht widersprechen.
    """
    from agent.schreibweise import de

    if saetze_zum_berichten is None:
        saetze_zum_berichten = (("Referenz 0,30 %", 0.003),
                                ("Betrieb 1,50 %", 0.015))
    try:
        erste = rechne(crv=crv, stop_relativ=stop_relativ, klasse=klasse,
                       h=h, gebuehr_je_seite=saetze_zum_berichten[0][1],
                       merkmale=merkmale)
    except WahrscheinlichkeitUnbekannt as exc:
        return ["Wie wahrscheinlich traegt dieser Trade?",
                f"   Nicht berechenbar: {exc}"]

    # ⚠️ EINE FESTE SPALTE FUER DIE ZAHLEN. Wer drei Prozentwerte
    # untereinander lesen soll, darf sie nicht suchen muessen.
    def _zeile(text: str, wert: str) -> str:
        return f"   {text:<52}{wert:>7}"

    aus = ["Wie wahrscheinlich traegt dieser Trade? (gerechnet, kein Urteil)",
           _zeile(f"Ausgangspunkt aus der Geometrie (CRV "
                  f"{de(erste['crv'], 1)})",
                  f"{de(100 * erste['basisrate'], 1)} %")]
    for z in erste["beitraege"]:
        if z["zustand"] == "traegt":
            aus.append(_zeile(f"+ {z['name']}", f"+{de(z['punkte'], 1)}"))
            aus.append(f"     ({z['warum']})")
    aus.append(_zeile("= geschaetzte Trefferquote",
                      f"{de(100 * erste['quote'], 1)} %"))

    # ⚠️ BEIDE SAETZE NEBENEINANDER - seit Kapitel 119 die Vorgabe. Ein
    # einzelner Satz beantwortet je nur eine der beiden Fragen.
    for name, satz in saetze_zum_berichten:
        r = rechne(crv=crv, stop_relativ=stop_relativ, klasse=klasse, h=h,
                   gebuehr_je_seite=satz, merkmale=merkmale)
        # ⚠️ DREI PROZENTZAHLEN OHNE BEZUG WAREN NICHT LESBAR (Nutzerfrage
        # 28.08.: *"1,5 Prozent traegt sich nicht und 60 % - was bedeutet das,
        # was sind die 60 %?"*).
        #
        # Hier stand: "noetig bei Betrieb 1,50 %: 66,7 % -> -28,8 Punkte".
        # Der Gebuehrensatz, die NOETIGE Quote und die Luecke standen
        # nebeneinander, ohne dass eine sagte, was sie ist - und die
        # GESCHAETZTE Quote, gegen die verglichen wird, stand fuenf Zeilen
        # weiter oben. Wer die Zeile allein las, konnte 66,7 % fuer das
        # Ergebnis halten.
        #
        # Jetzt stehen NOETIG und GESCHAETZT in derselben Zeile nebeneinander,
        # und das Urteil steht am Ende statt in der Mitte.
        traegt = r["abstand_punkte"] > 0
        marke = "   " if traegt else "⚠️ "
        aus.append(f"{marke}{name}: noetig {de(100 * r['breakeven'], 1)} %, "
                   f"geschaetzt {de(100 * r['quote'], 1)} % - "
                   f"{de(abs(r['abstand_punkte']), 1)} Punkte "
                   f"{'MEHR als noetig, TRAEGT' if traegt else 'ZU WENIG'}"
                   f" ({de(r['erwartungswert_r'], 3)} R je Trade)")

    # ⚠️ WAS NICHT DRINSTECKT, GEHOERT IN DIESELBE ZUSAMMENFASSUNG.
    # Ohne diese Zeilen liest sich die Quote, als waere alles beruecksichtigt
    # worden, was in der Mail steht - und drei Merkmale sind es nicht.
    enthalten = [z for z in erste["beitraege"]
                 if z["zustand"] == "enthalten"]
    for z in enthalten:
        aus.append(f"   Bereits enthalten: {z['name']} - {z['warum']}")
    offen = [z for z in erste["beitraege"]
             if z["zustand"] not in ("traegt", "enthalten")]
    if offen:
        aus.append("   Nicht eingerechnet, und warum:")
        for z in offen:
            aus.append(f"      {z['name']}: {z['warum']}")
    aus.append("⚠️ KEINE PROGNOSE FUER DIESEN TRADE, sondern die gemessene "
               "Haeufigkeit in einer Gruppe, zu der er gehoert. Das Urteil "
               "der Modelle steckt NICHT in dieser Zahl - es steht daneben.")
    return aus
