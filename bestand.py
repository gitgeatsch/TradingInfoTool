# -*- coding: utf-8 -*-
"""DAS REGISTER — eine Quelle, drei Ansichten, eine Selbstpruefung (06.09.2026)

## Warum es das gibt

**Nutzervorgabe 06.09.:** *„wir muessen das Ganze in eine brauchbare Form
bringen ... unter Beruecksichtigung der langen Historie zum Umbau,
Altbestand und Neubestand (Code und Doku) sauber trennen. Sonst findet man
die Punkte nicht mehr oder sie sind teilweise nicht nachvollziehbar."*

Die Lage, gemessen:

    Basisinfos            92.165 Zeilen in 17 Dokumenten
    Messwerkzeuge            281 Dateien
    davon ALTBESTAND         201  = 72 %  (weder Norm noch Tagesklammer)
    Methodik                 119 nummerierte Abschnitte, chronologisch

## ⚠️ Warum das hier KEIN weiteres Dokument ist

Noch ein handgepflegtes Markdown veraltet in zwei Wochen und macht die Lage
schlimmer. Deshalb:

    QUELLE      dieses Modul - strukturierte Daten, im Code
    ANSICHTEN   drei Markdown-Blaetter, ERZEUGT statt geschrieben
    PRUEFUNG    `pruefe()` schlaegt an, wenn Register und laufendes System
                auseinanderlaufen

Die Werkzeugliste wird **gescannt**, nicht gepflegt - 281 Eintraege von Hand
zu fuehren waere dieselbe Falle noch einmal.

## Die drei Register

    KANDIDATEN   je Bewertungsgroesse: Hypothese · FORM (Schalter/Regler) ·
                 Registrierungsbasis · Wert und Band · Live-Verwendung ·
                 die Messkette. Das Fehlen genau dieses Blattes hat am
                 06.09. ZWEI Fehler verursacht (R-R11).
    BEFUNDE      was gilt, was gefallen ist, was offen - mit dem Verweis
                 auf die abloesende Messung. Ohne ihn findet man eine
                 Korrektur nur durch Vorwaertslesen.
    WERKZEUGE    Altbestand gegen Neubestand, nach METHODIKSTAND getrennt,
                 nicht nach Datum (178 Dateien wurden in 14 Tagen angefasst,
                 die meisten nur vom N-19-Fix).

    python bestand.py            # Ansichten erzeugen und pruefen
    python bestand.py --pruefen  # nur pruefen (fuer die Suite)
"""
from __future__ import annotations

import glob
import io
import os
import re
import sys
from dataclasses import dataclass, field

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:                                            # noqa: BLE001
    pass

HIER = os.path.dirname(os.path.abspath(__file__))
BASIS = os.path.join(HIER, "Basisinfos")


# ===================================================================
#  1  DIE KANDIDATEN
# ===================================================================
@dataclass(frozen=True)
class Kandidat:
    """Ein Registrierungsblatt — alles an EINER Stelle."""
    name: str
    hypothese: str                  # WARUM sollte das tragen?
    form: str                       # "regler" | "schalter" | "-"
    basis: str                      # Registrierungsbasis
    wert: str                       # Wert und Band
    live: str                       # wo im laufenden System
    zustand: str                    # traegt | traegt nicht | offen | zurueck
    kette: tuple = ()               # die Messungen, chronologisch
    warnung: str = ""


KANDIDATEN = (
    Kandidat(
        name="funding",
        hypothese=("Querschnittsrang der Finanzierungsrate: wer heute am "
                   "wenigsten zahlt. Viel Funding heisst ueberhitzt."),
        form="regler",
        basis="H20 · 2.369 Kalendertage · 290 Symbole · 6,3 Jahre",
        wert="+0,0246 R (Regelwirkung)",
        live="agent/wahrscheinlichkeit.BEITRAEGE · merkmal funding_fuenftel "
             "· Stufen (+0.82, +1.30, +0.12, -0.54, -1.70)",
        zustand="traegt",
        kette=(
            ("30.08.", "2e registriert, als REGEL gemessen (R-R8)"),
            ("06.09.", "F-212 reproduziert +0,0274 (registriert +0,0246)"),
            ("06.09.", "Schritt 3: H5 ab 2024 +0,0041 - traegt nicht"),
            ("06.09.", "Schritt 4a A: H20 voll +0,02741 REPRODUZIERT"),
            ("06.09.", "Schritt 4a B: H5 voll  +0,00841 TRAEGT"),
            ("06.09.", "G2: faellt in BEIDEN 959-Tage-Fenstern -> "
                       "Datenmenge, nicht Epoche"),
        ),
        warnung="Fremdquelle, deshalb Luecken in der Abdeckung."),
    Kandidat(
        name="turnover",
        hypothese=("Handelsvolumen je Umlaufmenge - viel Aufmerksamkeit "
                   "heisst eher ueberbewertet."),
        form="regler",
        basis="H20 · 2.636 Kalendertage",
        wert="+0,0616 R [+0,0203 .. +0,1111]",
        live="agent/wahrscheinlichkeit.BEITRAEGE · merkmal turnover_fuenftel "
             "· Stufen (+3.15, +0.83, +0.22, -1.79, -2.40)",
        zustand="traegt",
        kette=(
            ("30.08.", "2e registriert"),
            ("02.09.", "F-171 Audit: Band sehr breit, groesste Stufen auf "
                       "der unsichersten Zahl"),
            ("02.09.", "F-170: Rang ist zu 52 % ASSET-Eigenschaft"),
            ("06.09.", "Schritt 4a A: H20 voll +0,06352 REPRODUZIERT"),
            ("06.09.", "Schritt 4a B: H5 voll  +0,02059 TRAEGT"),
            ("06.09.", "G2: juengere Epoche STAERKER (+0,0172 gegen +0,0137)"),
            ("06.09.", "N13: verschiebt die FRONTLOADING-Quote um +4,0 bis "
                       "+4,5 Punkte - bei JEDER Breite (20/10/5 %), Band "
                       "durchgehend ohne Null. Der Tempo-Anzeiger"),
        ),
        warnung="Nur 65 Symbole Abdeckung - das Nullband ist dreimal so "
                "breit wie bei den anderen, das Urteil wandert mit der Saat. "
                "⚠️ OFFEN (N6): turnover traegt AUCH am Randmassstab "
                "(+0,01389 bei H20, 2.119) - registriert ist er nur am "
                "Mittel. Und er erklaert 18 % von `vola` (N1, p=0,025)."),
    Kandidat(
        name="oi_aenderung",
        hypothese=("Aufbau von Open Interest zum Vortag: wo sich Hebel "
                   "auftuermt, kippt die Bewegung eher."),
        form="schalter",
        basis="H20 · 1.702 Kalendertage · 117 Symbole · 126.491 Anker",
        wert="+0,0145 R [+0,0097 .. +0,0193]",
        live="agent/rollen_gate.py Stufe terminmarkt - sperrt das OBERSTE "
             "Fuenftel · nur einstieg · nicht bei Bestand",
        zustand="traegt",
        kette=(
            ("02.09.", "H-4c: traegt, aber SCHALTER statt Regler - die "
                       "Monotonie fiel"),
            ("02.09.", "N-14: als 12. Trichterstufe gebaut"),
            ("04.09.", "F-207: Kombination mit funding_extrem verbessert die "
                       "Sperre NICHT - Status quo bleibt"),
            ("06.09.", "Schritt 3: H5 ab 2024 - traegt nicht"),
            ("06.09.", "Schritt 4a A: H20 voll +0,01418 REPRODUZIERT"),
            ("06.09.", "Schritt 4a B: H5 voll +0,00663 - traegt nicht"),
        ),
        warnung="⚠️ GELTUNGSBEREICH H20. Der Betriebshorizont sind 3-5 Tage. "
                "Ob H20 der richtige Horizont fuer diese Sperre ist, ist eine "
                "ENTWURFSfrage (D3) - keine Messfrage."),
    Kandidat(
        name="vola",
        hypothese=("Schwankungsbreite als Querschnittsrang - hohe "
                   "Volatilitaet als Ausschlusskriterium."),
        form="regler",
        basis="H5/H20 · volle Historie · Massstab RAND > +2 R",
        wert="+0,0100 (H20) · +0,0033 (H5 voll) · +0,0038 (H5 2024)",
        live="- noch nicht registriert",
        zustand="offen",
        kette=(
            ("06.09.", "Schritt 3: traegt am RAND (+0,0038), nicht am "
                       "Mittel - der von 2.112 vorhergesagte Fall"),
            ("06.09.", "Gegenpruefung: ueber drei Saaten stabil"),
            ("06.09.", "Schritt 4a: TRAEGT auf ALLEN DREI Laeufen"),
            ("06.09.", "N1-V2: Richtung geprueft - Gegenrichtung -0,00345, "
                       "spiegelbildlich. Echter Richtungseffekt"),
            ("06.09.", "N1-C: in funding +0,00309 TRAEGT · in turnover "
                       "+0,00281 nicht trennbar"),
            ("06.09.", "N1-D: turnover in vola +0,02217 TRAEGT - wird sogar "
                       "staerker"),
            ("06.09.", "N1-Rangtest, 39 Mischungen: funding erklaert 3 % "
                       "(p=0,325), turnover erklaert 18 % (Rang 1 von 40, "
                       "p=0,025)"),
            ("06.09.", "N5: die Kombination `vola ODER turnover` traegt "
                       "+0,00777 - mengenkontrolliert +26 % bis +34 % ueber "
                       "der besten Einzelgroesse, beide Haelften, drei "
                       "Saaten"),
            ("06.09.", "N12: allein bei 10/20/30/40 % Sperrmenge - ALLE "
                       "tragen. Bei 40 % +0,00647 = 83 % der Kombination, "
                       "aber bei 516 statt 65 Symbolen Abdeckung"),
            ("06.09.", "N13: beim Frontloading +1,5 Punkte (20 %) - traegt, "
                       "aber deutlich schwaecher als turnover (+4,0)"),
        ),
        warnung="⚠️ STAND NACH N12: `vola` ist die einzige der beiden "
                "Groessen, die im Betrieb UEBERALL wirkt (516 von 516 "
                "Symbolen). Allein bei 40 % Sperrmenge erreicht sie 83 % "
                "der Kombinationswirkung - der Kompromiss kostet 17 % "
                "Wirkung und bringt die achtfache Abdeckung. "
                "⚠️⚠️ N1 ENTSCHIEDEN, ABER NICHT ZUR REGISTRIERUNG. "
                "`vola` ist KEIN Mitlaeufer - 82 % bleiben, wenn turnover "
                "festgehalten wird, und funding erklaert nachweislich "
                "nichts. Aber die 18 % Ueberlappung mit turnover sind "
                "belegt, und der Rest ist im Schichtentest NICHT TRENNBAR. "
                "Naechster Schritt ist nicht mehr Messung von vola allein, "
                "sondern die KOMBINATION vola UND turnover am Rand (N5)."),
    Kandidat(
        name="vola ODER turnover",
        hypothese=("Zwei weitgehend unabhaengige Ausschlussgruende: hohe "
                   "Volatilitaet ODER hoher Umschlag. Wer in EINER der "
                   "beiden Groessen im obersten Fuenftel liegt, wird "
                   "gesperrt."),
        form="schalter",
        basis="H5 · volle Historie · Rand > +2 R · Menge frei · 167 Bloecke",
        wert="+0,00777 [+0,00480 .. +0,01153] · Reinheit +0,02143 · "
             "36,1 % gesperrt",
        live="- NICHT gebaut (siehe Warnung)",
        zustand="offen",
        kette=(
            ("06.09.", "N5: fuenf Formen geprueft. UND traegt nicht "
                       "(6,8 % gesperrt, Reinheit sogar NIEDRIGER als "
                       "einzeln), SUMME traegt (+0,00392), ODER traegt am "
                       "staerksten"),
            ("06.09.", "mengenkontrolliert: bei 20 % +26 %, bei 36 % +34 % "
                       "ueber der besten Einzelgroesse. 43 % des rohen "
                       "Vorsprungs waren MENGE"),
            ("06.09.", "beide Historienhaelften tragen einzeln "
                       "(+0,01045 / +0,00554), drei Saaten stabil"),
            ("06.09.", "zwei Konstruktionsfehler von den eigenen Kontrollen "
                       "gefangen: asymmetrische Rangbildung, fehlende "
                       "Symmetrieprobe im Vorabtest"),
        ),
        warnung="⚠️⚠️ BELEGT, ABER IM BETRIEB WEITGEHEND NICHT ABRUFBAR "
                "(N8/2.122): turnover liegt bei 7 von 57 beobachteten Werten "
                "vor. Der gemessene Kombinationsvorteil braucht beide "
                "Groessen. Die praktisch wichtigere Frage ist N12 - traegt "
                "`vola` ALLEIN als Sperre genug? "
                "⚠️ Frueherer Verdacht auf Doppelzaehlung ist ausgeraeumt: "
                "wo turnover vorliegt, verlangt das Tor ohnehin Fuenftel 0, "
                "eine Sperre auf Fuenftel 4 waere wirkungslos. "
                "(N9) 36 % Sperrmenge ist eine erhebliche Verschaerfung bei "
                "zwoelf bestehenden Trichterstufen. (N10) die Potentialformel "
                "meint eine BARRIEREN-Quote, das Randmass eine HORIZONT-Quote. "
                "⚠️ Der Effekt halbiert sich ueber die Zeit "
                "(+0,01045 -> +0,00554)."),
    Kandidat(
        name="schnitt50",
        hypothese="Abstand zum eigenen 50-Tage-Schnitt als Trendlage.",
        form="regler",
        basis="31.08. bei H2 und H20 gemessen - H5 NIE",
        wert="H2 +0,0029 [-0,0005 .. +0,0065] · H20 kein Urteil",
        live="- nicht registriert",
        zustand="offen",
        kette=(
            ("31.08.", "H2 traegt nicht (Messung maechtig), H20 kein Urteil "
                       "- die Positivkontrolle versagte dort"),
            ("06.09.", "Schritt 4a: H5 voll +0,0101 TRAEGT, H5 2024 "
                       "+0,0095 TRAEGT"),
        ),
        warnung="⚠️ NICHT VERWECHSELN mit `schnitt` (200-Tage), der am "
                "31.08. zurueckgenommen wurde. H5 ist neu und gegenzupruefen "
                "(N2) - der Horizontverlauf H2 klein / H5 gross / H20 klein "
                "ist erklaerungsbeduerftig."),
    Kandidat(
        name="schnitt",
        hypothese="Abstand zum eigenen 200-Tage-Schnitt.",
        form="regler",
        basis="H1..H20 Horizontlauf 31.08.",
        wert="H5 -0,0069 · H10 -0,0118 · H20 -0,0221",
        live="- zurueckgenommen",
        zustand="zurueck",
        kette=(
            ("31.08.", "mittags als dritter tragender Beitrag registriert"),
            ("31.08.", "abends im Horizontlauf gefallen - bei keinem "
                       "Horizont trennbar, bei langen negativ"),
        ),
        warnung="⚠️ Die Marken tragen weiterhin den STOP - nur als "
                "BEWERTUNGSbeitrag tragen sie nicht."),
    Kandidat(
        name="amihud",
        hypothese="Illiquiditaet |Rendite|/Umsatz - die Literatur behauptet "
                  "eine Praemie fuer illiquide Werte.",
        form="regler",
        basis="H20 volle Historie, beide Richtungen geprueft",
        wert="-0,0016 R",
        live="- nicht registriert",
        zustand="traegt nicht",
        kette=(("30.08.", "gemessen, beide Richtungen null"),
               ("06.09.", "Schritt 4a: auf keinem Lauf, keinem Massstab")),
        warnung=""),
    Kandidat(
        name="H (Vorfilter)",
        hypothese="Weg frei UND Stop gedeckt.",
        form="schalter",
        basis="gepoolt ueber die ganze Historie",
        wert="gepoolt +3,57 Punkte · je Kalendertag -1,02 nicht trennbar",
        live="agent/wahrscheinlichkeit.BEITRAEGE mit punkte=0.0 - "
             "stillgelegt, nicht entfernt",
        zustand="zurueck",
        kette=(("31.08.", "R1: faellt als Beitrag - gepoolt gemessen, unter "
                          "der Tagesklammer nicht trennbar"),),
        warnung="Die Marken tragen weiterhin den Stop."),
)


# ===================================================================
#  2  DIE BEFUNDE — was gilt, was abgeloest ist
# ===================================================================
@dataclass(frozen=True)
class Befundlage:
    kennung: str
    aussage: str
    stand: str                      # gilt | abgeloest | offen
    quelle: str
    abgeloest_durch: str = ""
    warum: str = ""


BEFUNDE = (
    Befundlage("2.112", "Der MITTELWERT ist der falsche Massstab - der "
               "Ertrag liegt im oberen Rand (p50 -0,19 R, aber 6,65 % der "
               "Asset-Tage ueber +2 R)", "gilt", "Methodik 2.112"),
    Befundlage("2.113-M4", "„tief im Rang = mehr Chance ist widerlegt - in "
               "R wird nach unten alles schlechter\"", "abgeloest",
               "Methodik 2.113", abgeloest_durch="2.115",
               warum="am MITTELWERT gemessen und unzulaessig zu einer "
                     "Asset-Aussage verallgemeinert - Regel 3"),
    Befundlage("2.113-S3", "Rangzugehoerigkeit traegt (+0,1020 R zwischen "
               "„in Top 100 geblieben\" und „neu\")", "abgeloest",
               "Methodik 2.113", abgeloest_durch="2.114",
               warum="GEPOOLT gerechnet. Mit Tagesklammer +0,0379, Band "
                     "[-0,0317 .. +0,1030] - traegt nicht"),
    Befundlage("2.115", "Ein im Rang GEFALLENES Asset hat auf kurzer "
               "Zeitachse mehr Randpotential (+0,0068, Band "
               "[+0,0034 .. +0,0108], Zufallskontrolle sauber)", "gilt",
               "Methodik 2.115"),
    Befundlage("2.116", "Die KATEGORIE traegt nicht (1,2 Prozentpunkte ueber "
               "das ganze Universum), der ZUSTAND innerhalb schon", "gilt",
               "Methodik 2.116"),
    Befundlage("2.116-9.7", "Die 9,7 % Ueberdeckung zwischen System und "
               "Messuniversum sind ein Problem", "abgeloest",
               "Methodik 2.116", abgeloest_durch="2.116-Korrektur",
               warum="Nutzerkorrektur: die Bewertung muss allgemein und "
                     "neutral funktionieren. Auf die gehandelten Symbole zu "
                     "messen waere ein Zirkelschluss"),
    Befundlage("2.117", "Der Datenqualitaetsfilter entfernt kein Rauschen, "
               "sondern den BELEG - er zerstoert den Befund aus 2.115",
               "gilt", "Methodik 2.117"),
    Befundlage("2.111-ab2024", "Der Abschnitt ab 2024 ist die primaere "
               "Messbasis", "abgeloest", "Methodik 2.111",
               abgeloest_durch="2.119",
               warum="Die Wirkung der Kandidaten ist NICHT epochenabhaengig. "
                     "Auf 959 Tagen sind sie in JEDEM Fenster unentscheidbar "
                     "- Datenmenge, nicht Epoche. Primaer ist jetzt die "
                     "volle Historie"),
    Befundlage("2.118", "Der Randmassstab hat Trennschaerfe (6 von 6 "
               "Kandidaten) und ist 2,5- bis 10-fach stumpfer als das "
               "Mittel - er wird ZWEITE Zielgroesse", "gilt",
               "Methodik 2.118"),
    Befundlage("S3-Meldung", "Beide registrierten Beitraege fallen bei "
               "H5 ab 2024", "abgeloest", "Schritt 3, 06.09.",
               abgeloest_durch="2.119",
               warum="Zwei Groessen gleichzeitig geaendert (Horizont UND "
                     "Epoche). Alle drei Registrierungen reproduzieren auf "
                     "ihrer eigenen Basis - R-R11"),
    Befundlage("2.119", "Reproduktionspflicht: alle drei Registrierungen "
               "reproduzieren; nichts ist gefallen", "gilt",
               "Methodik 2.119 · R-R11"),
    Befundlage("D3", "Ist H20 der richtige Horizont fuer die OI-Sperre, "
               "wenn der Betriebshorizont 3-5 Tage betraegt?", "offen",
               "Methodik 2.119", warum="ENTWURFSfrage, keine Messfrage - "
                                       "Nutzerentscheidung"),
    Befundlage("N1", "Traegt `vola` unabhaengig, oder ist es redundant zu "
               "funding/turnover?", "abgeloest", "Schritt 4a",
               abgeloest_durch="2.120",
               warum="beantwortet: KEIN Mitlaeufer (82 % bleiben), aber "
                     "auch nicht reif - 18 % Ueberlappung mit turnover "
                     "belegt (Rang 1 von 40, p=0,025), Rest nicht trennbar"),
    Befundlage("2.120", "`vola` ist kein Mitlaeufer, aber nicht reif: "
               "funding erklaert 3 % (p=0,325), turnover 18 % (p=0,025); "
               "der Rest ist im Schichtentest nicht trennbar", "gilt",
               "Methodik 2.120"),
    Befundlage("F-206-Anfuehrung", "F-206 (turnover+vola praktisch "
               "identisch) belegt Redundanz bei N1", "abgeloest",
               "eigene Anfuehrung 06.09.", abgeloest_durch="2.120",
               warum="F-206 wurde auf H2/Frontloading gemessen; F-207 haelt "
                     "fest, dass sich das nicht auf H20/R uebertraegt. Die "
                     "Anfuehrung war eine Horizontverwechslung"),
    Befundlage("N5", "Traegt die KOMBINATION `vola` UND `turnover` am "
               "Randmassstab mehr als jede Groesse einzeln?", "abgeloest",
               "Methodik 2.120", abgeloest_durch="2.121",
               warum="beantwortet: ODER traegt (+0,00777), "
                     "mengenkontrolliert +26 % bis +34 % ueber der besten "
                     "Einzelgroesse, beide Haelften, drei Saaten. UND traegt "
                     "NICHT"),
    Befundlage("2.121", "`vola ODER turnover` traegt am Randmassstab mehr "
               "als jede Einzelgroesse - mengenkontrolliert, in beiden "
               "Historienhaelften, ueber drei Saaten", "gilt",
               "Methodik 2.121"),
    Befundlage("2.121-UND", "Werte mit BEIDEN Extremen sind WENIGER schlecht "
               "als Werte mit EINEM Extrem (UND-Reinheit +0,01267 gegen "
               "+0,01590 / +0,01678 einzeln)", "gilt", "Methodik 2.121",
               warum="unerklaert. Kein Messfehler - die Symmetrieprobe ist "
                     "bitgenau. Es erklaert, warum UND versagt und ODER "
                     "gewinnt"),
    Befundlage("N8", "`turnover` ist bereits als Regler am Mittel "
               "registriert - eine Sperre mit `turnover` wendet ihn ZWEIMAL "
               "an", "abgeloest", "Methodik 2.121", abgeloest_durch="2.122",
               warum="KEINE Doppelzaehlung: wo turnover vorliegt (7 von 57), "
                     "verlangt das Tor ohnehin Fuenftel 0 - die Sperre wuerde "
                     "Fuenftel 4 sperren, das nie durchkommt. Wo er fehlt "
                     "(50 von 57), kann die Sperre ihn nicht auswerten. "
                     "Wirkungslos, nicht doppelt"),
    Befundlage("2.122", "Die Schwelle ist ein Anteil von 59,9 % der bei "
               "DIESER Datenlage erreichbaren Spanne. Ein Wert mit nur "
               "Funding kommt zu 40 % durch, einer mit beiden Raengen nur "
               "zu 12 %", "gilt", "Methodik 2.122"),
    Befundlage("88-Prozent-Meldung", "88 % der beobachteten Werte koennen "
               "die Potentialschwelle nie erreichen", "abgeloest",
               "eigene Rechnung 06.09.", abgeloest_durch="2.122",
               warum="gegen die FESTE Vorgabe 0,080 gerechnet statt gegen "
                     "`Potential.schwelle` je Datenlage. Das Projekt hatte "
                     "genau diesen Fehler am 31.08. selbst gemacht und "
                     "behoben - ich habe ihn nachgebaut"),
    Befundlage("N11", "Die Durchlassquote haengt an der SCHIEFE der "
               "Beitragsstufen, nicht am Asset: funding laesst 2 von 5 "
               "Fuenfteln durch, turnover nur 1 von 5", "offen",
               "Methodik 2.122",
               warum="turnovers Maximum (+3,15) steht allein, der Zweite "
                     "(+0,83) liegt bei 26 % davon. Bei funding liegt der "
                     "Zweite (+0,82) bei 63 % des Maximums (+1,30)"),
    Befundlage("N12", "Traegt `vola` ALLEIN als Sperre genug?",
               "abgeloest", "Methodik 2.122", abgeloest_durch="2.123",
               warum="JA - bei allen vier Sperrmengen (10/20/30/40 %). Bei "
                     "40 % erreicht sie 83 % der Kombinationswirkung bei "
                     "516 statt 65 Symbolen. Der Kompromiss kostet 17 % "
                     "Wirkung fuer die achtfache Abdeckung"),
    Befundlage("2.123", "`vola` allein traegt bei jeder Sperrmenge; der "
               "Abdeckungskompromiss kostet 17 % Wirkung", "gilt",
               "Methodik 2.123"),
    Befundlage("2.124", "`turnover` verschiebt die Frontloading-Quote um "
               "+4,0 bis +4,5 Punkte - bei JEDER Breite, Band ohne Null. "
               "Die Horizontwahl aus der Kursreihe ist belegbar und klein",
               "gilt", "Methodik 2.124"),
    Befundlage("Breite-Hebel", "Eine engere Auswahl verbessert die "
               "Frontloading-Verschiebung um 40 %", "abgeloest",
               "eigene Lesart 06.09.", abgeloest_durch="2.124",
               warum="Punktschaetzer-Vergleich ohne Deckung. Die Baender "
                     "ueberlappen vollstaendig: +4,0 [+2,8 .. +5,2] gegen "
                     "+4,5 [+2,8 .. +6,2]"),
    Befundlage("Kursreihe-Nullaussage", "Die Kursreihe liefert die "
               "Instrumentwahl nicht", "abgeloest", "eigene Formulierung "
               "2.123", abgeloest_durch="2.124",
               warum="Kapitulationsformel statt Analyse. Der richtige "
                     "Vergleich ist nicht ein perfekter Waehler, sondern der "
                     "TAKT - und der hat null gemessenen Vorteil (Regel 1)"),
    Befundlage("N14", "Traegt das HEBEL-SCREENING als zweite, von der "
               "Kursreihe UNABHAENGIGE Quelle fuer die Horizontwahl?",
               "offen", "Methodik 2.124 · F-185",
               warum="227.395 OI-Zeilen, 13.254 Kandidaten. Der einzige "
                     "verbliebene Hebel fuer mehr Trennschaerfe - alle "
                     "Kursreihengroessen sind ausgemessen"),
    Befundlage("N15", "`UND @ 10 %` zeigt 58,3 % frontlastig (+7,1 Punkte, "
               "Band [+2,8 .. +13,0]) bei nur 6,1 % der Anker", "offen",
               "Methodik 2.124",
               warum="Band ohne Null, aber die anteilgewichtete Wirkung "
                     "traegt nicht - zu wenige Anker. Mit mehr "
                     "Terminmarkt-Historie pruefbar. Zurueckgestellt, nicht "
                     "verworfen"),

    Befundlage("N9", "36 % Sperrmenge bei zwoelf bestehenden Trichterstufen "
               "- welche Durchlassmenge bleibt?", "offen", "Methodik 2.121"),
    Befundlage("N10", "Die Potentialformel meint eine BARRIEREN-Quote, das "
               "Randmass eine HORIZONT-Quote", "offen", "Methodik 2.121"),
    Befundlage("N6", "`turnover` traegt auch am RAND (+0,01389 bei H20), "
               "registriert ist er nur am Mittel", "offen",
               "Methodik 2.119"),
    Befundlage("N7", "Der Schichtentest braucht rueckwirkend eine "
               "Trennschaerfe - alle frueheren Nullbefunde daraus sind "
               "unbeziffert", "offen", "Methodik 2.120",
               warum="messe_kandidaten_als_regel.geschichtet() hatte nie "
                     "eine Positivkontrolle"),
    Befundlage("N2", "Warum traegt `schnitt50` bei H5, aber nicht bei H2 "
               "und H20?", "offen", "Schritt 4a"),
)


# ===================================================================
#  3  DIE WERKZEUGE — gescannt, nicht gepflegt
# ===================================================================
STUFEN = (
    ("NORM", "ruft `messnorm` - der aktuelle Stand, Trennschaerfe Pflicht"),
    ("TAGESKLAMMER", "Tagesklammer und Band, aber keine Trennschaerfe-Pflicht"),
    ("BLOCK", "eigener Blockbootstrap, ausserhalb der Norm"),
    ("ALTBESTAND", "weder Norm noch Tagesklammer - Befunde nur mit Vorbehalt"),
)


def scanne_werkzeuge() -> dict:
    """Ordnet jedes Messwerkzeug nach METHODIKSTAND ein, nicht nach Datum.

    ⚠️ Das Datum taugt nicht: 178 der 384 Dateien wurden in 14 Tagen
    angefasst, die meisten nur vom N-19-Fix (Krypto-Filter, 44 Skripte).
    """
    aus = {k: [] for k, _ in STUFEN}
    muster = re.compile(r"^(messe|pruefe|rechne|simuliere|schritt|messnorm)")
    for pfad in sorted(glob.glob(os.path.join(HIER, "*.py"))):
        f = os.path.basename(pfad)
        if not muster.match(f):
            continue
        try:
            s = io.open(pfad, encoding="utf-8", errors="replace").read()
        except OSError:
            continue
        if re.search(r"(^|\n)\s*(import|from)\s+messnorm", s):
            k = "NORM"
        elif "urteil_tage" in s:
            k = "TAGESKLAMMER"
        elif "bootstrap" in s.lower() or "percentile" in s:
            k = "BLOCK"
        else:
            k = "ALTBESTAND"
        aus[k].append(f)
    return aus


# ===================================================================
#  DIE SELBSTPRUEFUNG
# ===================================================================
def pruefe(still: bool = False) -> list:
    """Laeuft das Register mit dem SYSTEM mit? Gibt die Abweichungen."""
    fehler = []

    # 1 — jeder tragende REGLER muss in BEITRAEGE stehen
    try:
        sys.path.insert(0, HIER)
        from agent import wahrscheinlichkeit as WK           # noqa: PLC0415
        merkmale = {b.merkmal for b in WK.BEITRAEGE}
    except Exception as e:                                   # noqa: BLE001
        fehler.append("BEITRAEGE nicht lesbar: %s" % e)
        merkmale = None
    if merkmale is not None:
        for k in KANDIDATEN:
            if k.zustand != "traegt" or k.form != "regler":
                continue
            if not any(k.name in m for m in merkmale):
                fehler.append(
                    "%s gilt als tragender REGLER, steht aber nicht in "
                    "wahrscheinlichkeit.BEITRAEGE" % k.name)

    # 2 — jeder tragende SCHALTER muss eine Gate-Stufe haben
    try:
        g = io.open(os.path.join(HIER, "agent", "rollen_gate.py"),
                    encoding="utf-8", errors="replace").read()
    except OSError as e:
        fehler.append("rollen_gate.py nicht lesbar: %s" % e)
        g = ""
    for k in KANDIDATEN:
        if k.zustand == "traegt" and k.form == "schalter" and g:
            stufe = k.live.split("Stufe ")[-1].split(" ")[0] if "Stufe " in k.live else ""
            if stufe and stufe not in g:
                fehler.append("%s gilt als tragender SCHALTER, Stufe %r "
                              "steht nicht in rollen_gate.py" % (k.name, stufe))

    # 3 — kein Befund darf "gilt" sein und zugleich abgeloest
    for b in BEFUNDE:
        if b.stand == "gilt" and b.abgeloest_durch:
            fehler.append("%s steht auf 'gilt' und hat zugleich einen "
                          "Abloeser (%s)" % (b.kennung, b.abgeloest_durch))
        if b.stand == "abgeloest" and not b.abgeloest_durch:
            fehler.append("%s ist abgeloest, aber ohne Verweis - dann "
                          "findet es niemand" % b.kennung)
        if b.stand == "abgeloest" and not b.warum:
            fehler.append("%s ist abgeloest ohne BEGRUENDUNG (R-R11)"
                          % b.kennung)

    if not still:
        print("=" * 78)
        print("SELBSTPRUEFUNG DES REGISTERS")
        print("=" * 78)
        if fehler:
            for f in fehler:
                print("  ⚠️ %s" % f)
        else:
            print("  ✔ Register und laufendes System stimmen ueberein")
    return fehler


# ===================================================================
#  DIE ANSICHTEN
# ===================================================================
def _kandidatenblatt() -> str:
    z = ["# REGISTER — DIE KANDIDATEN",
         "",
         "*Erzeugt aus `bestand.py`. **Nicht von Hand aendern** — die "
         "Aenderung gehoert in das Modul, sonst laeuft das Blatt weg.*",
         "",
         "⚠️ **Wofuer dieses Blatt existiert:** am 06.09.2026 wurden drei "
         "Kandidaten auf der FALSCHEN Basis gemessen, weil ihre "
         "Registrierungsbasen ueber `wahrscheinlichkeit.BEITRAEGE`, "
         "Memory-Dateien, Befundkarte und Methodik verstreut lagen. Und "
         "`schnitt` wurde mit `schnitt50` verwechselt. Beides waere mit "
         "diesem Blatt nicht passiert (R-R11).",
         ""]
    sym = {"traegt": "✔", "traegt nicht": "✖", "offen": "○", "zurueck": "↩"}
    z += ["## Uebersicht", "",
          "| | Kandidat | Form | Zustand | Registrierungsbasis |",
          "|---|---|---|---|---|"]
    for k in KANDIDATEN:
        z.append("| %s | **`%s`** | %s | %s | %s |"
                 % (sym.get(k.zustand, "?"), k.name, k.form, k.zustand,
                    k.basis))
    z.append("")
    for k in KANDIDATEN:
        z += ["---", "", "## %s `%s`" % (sym.get(k.zustand, "?"), k.name), "",
              "**Hypothese:** %s" % k.hypothese, "",
              "| | |", "|---|---|",
              "| **Form** | %s |" % k.form,
              "| **Registrierungsbasis** | %s |" % k.basis,
              "| **Wert** | %s |" % k.wert,
              "| **Live** | %s |" % k.live,
              "| **Zustand** | **%s** |" % k.zustand, ""]
        if k.kette:
            z += ["**Die Messkette:**", ""]
            for datum, was in k.kette:
                z.append("- **%s** — %s" % (datum, was))
            z.append("")
        if k.warnung:
            z += [k.warnung if k.warnung.startswith("⚠️")
                  else "⚠️ %s" % k.warnung, ""]
    return "\n".join(z) + "\n"


def _befundblatt() -> str:
    z = ["# REGISTER — DIE BEFUNDE",
         "",
         "*Erzeugt aus `bestand.py`. **Nicht von Hand aendern.***",
         "",
         "⚠️ **Wofuer:** eine Korrektur findet man in einem chronologischen "
         "Dokument nur durch VORWAERTSLESEN. Hier steht bei jedem "
         "abgeloesten Befund, **wodurch** und **warum**.",
         ""]
    for stand, titel in (("gilt", "✔ WAS GILT"),
                         ("offen", "○ WAS OFFEN IST"),
                         ("abgeloest", "↩ WAS ABGELOEST IST")):
        z += ["## %s" % titel, ""]
        teil = [b for b in BEFUNDE if b.stand == stand]
        if not teil:
            z += ["*(nichts)*", ""]
            continue
        for b in teil:
            z.append("**%s** — %s" % (b.kennung, b.aussage))
            z.append("")
            z.append("- Quelle: %s" % b.quelle)
            if b.abgeloest_durch:
                z.append("- **Abgeloest durch: %s**" % b.abgeloest_durch)
            if b.warum:
                z.append("- Warum: %s" % b.warum)
            z.append("")
    return "\n".join(z) + "\n"


def _werkzeugblatt() -> str:
    w = scanne_werkzeuge()
    ges = sum(len(v) for v in w.values())
    z = ["# REGISTER — DIE WERKZEUGE (Altbestand gegen Neubestand)",
         "",
         "*Erzeugt aus `bestand.py` durch **Scan**, nicht gepflegt — 281 "
         "Eintraege von Hand zu fuehren waere dieselbe Falle noch einmal.*",
         "",
         "⚠️ **Getrennt wird nach METHODIKSTAND, nicht nach Datum.** 178 von "
         "384 Dateien wurden in 14 Tagen angefasst, die meisten nur vom "
         "N-19-Fix (Krypto-Filter, 44 Skripte). Das Datum sagt nichts "
         "darueber, ob ein Werkzeug der Norm genuegt.",
         "",
         "| Stufe | Anzahl | Anteil | Bedeutung |", "|---|---|---|---|"]
    for k, txt in STUFEN:
        z.append("| **%s** | %d | %.0f %% | %s |"
                 % (k, len(w[k]), 100 * len(w[k]) / max(ges, 1), txt))
    z += ["",
          "> ⚠️ **%d von %d Werkzeugen (%.0f %%) sind Altbestand.** Ein "
          "Befund aus dieser Gruppe gilt nur mit Vorbehalt — er hat weder "
          "Tagesklammer noch Trennschaerfe."
          % (len(w["ALTBESTAND"]), ges, 100 * len(w["ALTBESTAND"]) / max(ges, 1)),
          "",
          "## Die Regel fuer neue Arbeit", "",
          "    NEUE Messung        ruft `messnorm` oder `messnorm_rand`",
          "    BESTEHENDE Messung  bleibt, wird aber nicht als Beleg fuer",
          "                        einen NEUEN Befund herangezogen, ohne",
          "                        vorher unter die Norm gestellt zu werden",
          "                        (R-R11: erst reproduzieren)",
          ""]
    for k, _t in STUFEN:
        z += ["## %s (%d)" % (k, len(w[k])), ""]
        z += ["    " + "\n    ".join(
            ", ".join(w[k][i:i + 4]) for i in range(0, len(w[k]), 4))
            if w[k] else "*(keine)*", ""]
    return "\n".join(z) + "\n"


# ===================================================================
#  4  DIE METHODIK — thematischer Zugang statt Nummernfolge
# ===================================================================
# ⚠️ Die Methodik hat 85 nummerierte Abschnitte und ist CHRONOLOGISCH
# gewachsen - sie steht nicht einmal in numerischer Reihenfolge (2.13,
# 2.17, 2.16, 2.15 ...). Wer wissen will, wie eine Blocklaenge zu belegen
# ist, muss wissen, dass das in 2.95 und 2.111 steht.
#
# Der Inhalt wird NICHT umgeschrieben - die Chronologie ist selbst ein
# Beleg (man sieht, wann was gelernt wurde). Stattdessen ein erzeugter
# Zugang nach Themen, mit Zeilennummern.
THEMEN = (
    ("Klammer und Nullpunkt",
     ("klammer", "gepoolt", "tagesklammer", "nullpunkt", "zufallskontrolle",
      "negativkontrolle", "placebo", "ziehung")),
    ("Block, Bootstrap und Abhaengigkeit",
     ("block", "bootstrap", "ueberlappend", "überlappend", "persistenz",
      "anker", "autokorrelation")),
    ("Trennschaerfe und Positivkontrolle",
     ("trennschaerfe", "trennschärfe", "positivkontrolle", "maechtig",
      "mächtig", "untermaechtig", "untermächtig", "gepflanzt", "suchpreis")),
    ("Zielgroesse und MASSSTAB",
     ("zielgroesse", "zielgröße", "massstab", "maßstab", "barriere",
      "bewegung_r", "rand", "mittelwert", "median", "potential")),
    ("Auswahl, Menge und Universum",
     ("auswahl", "menge", "universum", "abdeckung", "survivorship",
      "filter", "kategorie")),
    ("Kombination, Schichtung, Redundanz",
     ("kombination", "schicht", "redundanz", "mitlaeufer", "mitläufer",
      "additiv", "korrelation")),
    ("Datenlage, Simulation, zu wenig Daten",
     ("datenlage", "datengrundlage", "simulation", "kunstdaten",
      "marktdaten", "zu wenig", "basisloesung", "basislösung", "epoche")),
    ("Marktbefunde",
     ("markt", "alltag", "rang", "phase", "dominanz", "regime", "zyklus",
      "struktureinbruch", "verfall")),
    # ⚠️ ENG GEFASST (06.09., beim Lesen des eigenen Ergebnisses gefunden).
    # Die erste Fassung enthielt "fehler", "kontrolle", "regel", "norm" -
    # Woerter, die in JEDEM Abschnitt stehen. Das Thema fing 73 von 85
    # Abschnitten ein. Eine Kategorie mit 86 % Trefferquote ordnet nichts.
    ("Pruefdisziplin und Urteilslogik",
     ("reproduk", "pruefliste", "prüfliste", "widerruf", "selbsttest",
      "gegenpruefung", "gegenprüfung", "vorabfestlegung", "r-r1")),
)


def _methodikblatt() -> str:
    import re as _re
    p = os.path.join(BASIS, "Test_und_Verifikationsmethodik.md")
    try:
        roh = io.open(p, encoding="utf-8", errors="replace").read()
        zeilen = roh.splitlines()
    except OSError as e:
        return "# REGISTER — METHODIK\n\nnicht lesbar: %s\n" % e
    # ⚠️ UEBER DEN ABSCHNITTSTEXT, NICHT NUR DEN TITEL (06.09., beim Lesen
    # des eigenen Ergebnisses gefunden). Die erste Fassung suchte die
    # Schlagworte nur in der Ueberschrift - 57 von 85 Abschnitten blieben
    # unzugeordnet, und ein Index, der zwei Drittel nicht einordnet, ist
    # keiner. Titel sind beschreibende Prosa, die Begriffe stehen im Text.
    kopf = []
    for i, z in enumerate(zeilen, 1):
        m = _re.match(r"^##\s+(2[\.\d]*)\s+(.*)$", z)
        if m:
            kopf.append((m.group(1), m.group(2).strip(), i))
    abschnitte = []
    for j, (n, t, i) in enumerate(kopf):
        ende = kopf[j + 1][2] - 1 if j + 1 < len(kopf) else len(zeilen)
        rumpf = "\n".join(zeilen[i - 1:ende]).lower()
        abschnitte.append((n, t, i, rumpf))
    out = ["# REGISTER — METHODIK NACH THEMEN",
           "",
           "*Erzeugt aus `bestand.py`. **Nicht von Hand aendern.***",
           "",
           "⚠️ **Wofuer:** die Methodik hat **%d** nummerierte Abschnitte "
           "und ist chronologisch gewachsen — sie steht nicht einmal in "
           "numerischer Reihenfolge. Der Inhalt wird bewusst NICHT "
           "umgeschrieben: die Chronologie ist selbst ein Beleg dafuer, "
           "wann was gelernt wurde. Hier ist nur der Zugang."
           % len(abschnitte),
           "",
           "Die Zeilennummer bezieht sich auf "
           "`Basisinfos/Test_und_Verifikationsmethodik.md`.",
           ""]
    # Je Abschnitt die STAERKSTEN Themen, hoechstens drei - sonst steht
    # jeder Abschnitt unter jedem Thema und der Index traegt wieder nichts.
    zuordnung: dict = {}
    for n, t, i, rumpf in abschnitte:
        punkte = []
        for titel, schluessel in THEMEN:
            # der Titel zaehlt dreifach, der Rumpf einfach
            p = sum(3 * t.lower().count(k) + rumpf.count(k)
                    for k in schluessel)
            if p:
                punkte.append((p, titel))
        punkte.sort(reverse=True)
        zuordnung[n] = [x[1] for x in punkte[:3]]

    getroffen = set()
    for titel, _schluessel in THEMEN:
        treffer = [(n, t, i) for n, t, i, _r in abschnitte
                   if titel in zuordnung.get(n, ())]
        out += ["## %s (%d)" % (titel, len(treffer)), ""]
        if not treffer:
            out += ["*(keiner)*", ""]
            continue
        out += ["| Abschnitt | Titel | Zeile |", "|---|---|---|"]
        for n, t, i in treffer:
            getroffen.add(n)
            out.append("| **%s** | %s | %d |" % (n, t[:96], i))
        out.append("")
    rest = [(n, t, i) for n, t, i, _r in abschnitte if n not in getroffen]
    out += ["## Ohne Thema zugeordnet (%d)" % len(rest), ""]
    if rest:
        out += ["| Abschnitt | Titel | Zeile |", "|---|---|---|"]
        for n, t, i in rest:
            out.append("| %s | %s | %d |" % (n, t[:96], i))
    out.append("")
    return "\n".join(out) + "\n"


# ===================================================================
#  5  DIE FAKTEN — die F-Nummern, gescannt und nach Thema erschlossen
# ===================================================================
# ⚠️⚠️ WARUM ES DAS GIBT (06.09.2026, nach dem dritten eigenen Verstoss
# gegen R-R10 an EINEM Tag).
#
# Die Fakten-Entscheidungsmappe hat 9.154 Zeilen und ueber 230 F-Nummern,
# chronologisch. Am 06.09. wurde dreimal gemessen, was dort bereits stand:
#
#   F-206 falsch angefuehrt   (auf H2 gemessen, nicht auf H20/R)
#   F-165 nicht geoeffnet     (Frontloading war beantwortet)
#   F-205..F-210 uebersehen   (N13 war eine Wiederholung von F-208,
#                              N14 war durch F-210 abgeschlossen)
#
# Ein Vorsatz hilft dagegen nicht - ein durchsuchbarer Index schon.
FAKTEN_THEMEN = (
    ("Frontloading und Horizontwahl",
     ("frontloading", "steil-kurz", "flach-lang", "horizont", "instrument",
      "wegwahl", "hebel")),
    ("Beitraege: Funding, Turnover, OI",
     ("funding", "turnover", "oi_aenderung", "oi-", "terminmarkt",
      "beitrag", "stufen")),
    ("Kombination und Redundanz",
     ("kombination", "redundanz", "mitlaeufer", "mitläufer", "schicht",
      "korrelation", "und/oder")),
    ("Schwelle, Kalibrierung, Potential",
     ("schwelle", "kalibr", "potential", "quote", "crv", "punkte")),
    ("Messfehler und Kontamination",
     ("kontamination", "fehler", "nebenwirkung", "artefakt", "falsch",
      "korrektur", "zurueckgenommen", "zurückgenommen")),
    ("Kette, Trichter, Sperren",
     ("trichter", "sperre", "gate", "stufe", "durchlass", "kette")),
)


def _faktenblatt() -> str:
    import re as _re
    p = os.path.join(BASIS, "Fakten_Entscheidungsmappe.md")
    try:
        zeilen = io.open(p, encoding="utf-8", errors="replace").read().splitlines()
    except OSError as e:
        return "# REGISTER - FAKTEN\n\nnicht lesbar: %s\n" % e
    kopf = []
    for i, z in enumerate(zeilen, 1):
        m = _re.match(r"^##\s+(F-\d+[a-z]?)\s+(.*)$", z)
        if m:
            kopf.append((m.group(1), m.group(2).strip(), i))
    eintraege = []
    for j, (n, t, i) in enumerate(kopf):
        ende = kopf[j + 1][2] - 1 if j + 1 < len(kopf) else len(zeilen)
        eintraege.append((n, t, i, "\n".join(zeilen[i - 1:ende]).lower()))
    out = ["# REGISTER — DIE FAKTEN (F-Nummern)",
           "",
           "*Erzeugt aus `bestand.py` durch **Scan** der "
           "`Fakten_Entscheidungsmappe.md`. Nicht von Hand aendern.*",
           "",
           "⚠️⚠️ **Wofuer:** am 06.09.2026 wurde **dreimal an einem Tag** "
           "gemessen, was in der Mappe bereits stand — F-206 falsch "
           "angefuehrt, F-165 nicht geoeffnet, F-205 bis F-210 uebersehen "
           "(N13 war eine Wiederholung von F-208, N14 durch F-210 "
           "abgeschlossen). **Vor jeder neuen Messung hier nachsehen.**",
           "",
           "**%d Eintraege**, Zeilennummer bezieht sich auf "
           "`Basisinfos/Fakten_Entscheidungsmappe.md`." % len(eintraege),
           ""]
    zug = {}
    for n, t, i, rumpf in eintraege:
        p2 = []
        for titel, schl in FAKTEN_THEMEN:
            w = sum(3 * t.lower().count(k) + rumpf.count(k) for k in schl)
            if w:
                p2.append((w, titel))
        p2.sort(reverse=True)
        zug[n] = [x[1] for x in p2[:2]]
    getroffen = set()
    for titel, _s in FAKTEN_THEMEN:
        tr = [(n, t, i) for n, t, i, _r in eintraege if titel in zug.get(n, ())]
        out += ["## %s (%d)" % (titel, len(tr)), ""]
        if not tr:
            out += ["*(keiner)*", ""]
            continue
        out += ["| Nr. | Titel | Zeile |", "|---|---|---|"]
        for n, t, i in tr:
            getroffen.add(n)
            out.append("| **%s** | %s | %d |" % (n, t[:100], i))
        out.append("")
    rest = [(n, t, i) for n, t, i, _r in eintraege if n not in getroffen]
    out += ["## Ohne Thema zugeordnet (%d)" % len(rest), ""]
    if rest:
        out += ["| Nr. | Titel | Zeile |", "|---|---|---|"]
        for n, t, i in rest:
            out.append("| %s | %s | %d |" % (n, t[:100], i))
    out.append("")
    return "\n".join(out) + "\n"


def schreibe() -> None:
    for datei, inhalt in (("REGISTER_Kandidaten.md", _kandidatenblatt()),
                          ("REGISTER_Befunde.md", _befundblatt()),
                          ("REGISTER_Werkzeuge.md", _werkzeugblatt()),
                          ("REGISTER_Methodik_Themen.md", _methodikblatt()),
                          ("REGISTER_Fakten.md", _faktenblatt())):
        p = os.path.join(BASIS, datei)
        with io.open(p, "w", encoding="utf-8") as f:
            f.write(inhalt)
        print("  geschrieben: Basisinfos/%s (%d Zeilen)"
              % (datei, inhalt.count("\n")))


def main() -> int:
    nur = "--pruefen" in sys.argv
    if not nur:
        print("=" * 78)
        print("DIE ANSICHTEN ERZEUGEN")
        print("=" * 78)
        schreibe()
        print()
    fehler = pruefe()
    return 1 if fehler else 0


if __name__ == "__main__":
    sys.exit(main())
