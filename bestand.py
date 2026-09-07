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
             "· Stufen (+0.33, +0.33, +0.33, -0.48, -0.48) seit 07.09. "
             "(vorher +3.15/+0.83/+0.22/-1.79/-2.40, 2.141)",
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
        warnung="✔✔ TABELLE STEHT (Stand 07.09. nach dem Audit 2.143). "
                "F-212 vom 04.09. hat auf der SELEKTIERTEN Menge gemessen "
                "und reproduziert: +0,0635 R gegen registriert +0,0616. "
                "⚠️ Meine Gegenmessungen N-56 und N-58 liefen auf der "
                "FREIEN Menge, wo die Beitraege laut F-212 auf 1,5 % der "
                "Anker wirken - dort liegt selbst funding bei -0,0003 R. "
                "Beide sind abgeloest, die daraus gefolgte Live-Aenderung "
                "(+0,33/-0,48) ist ZURUECKGENOMMEN. "
                "⚠️ WER DIESE TABELLE AENDERN WILL, MUSS AUF DER "
                "SELEKTIERTEN MENGE MESSEN. "
                "--- UEBERHOLT: ⚠️⚠️⚠️ REPRODUKTION FEHLGESCHLAGEN 06.09. (N-56): auf der "
                "EIGENEN Basis (H20, bewegung_r, oberstes Fuenftel) kommt "
                "-0,06293 [-0,13183 .. -0,00785] heraus gegen registriert "
                "+0,0616 - gleiche Groessenordnung, UMGEKEHRTES Vorzeichen. "
                "Die Fuenftel haben keine Ordnung: +0,009 · +0,053 · -0,265 "
                "· -0,041 · +0,229; das BESTE ist Fuenftel 4, das die "
                "Tabelle mit -2,40 am haertesten bestraft. Bestaetigt 2.133 "
                "(0 von 2 Nachbarn getrennt, beide Haelften). "
                "⚠️ DIE GROESSE BLEIBT - sie traegt Richtung (GS +0,00512, "
                "der staerkste der drei). NICHT belegt ist die TABELLE, und "
                "es sind die groessten Stufen im System. Nach 2.133 ist die "
                "belegte Form eine ZWEITEILUNG. "
                "--- ✔✔ REHABILITIERT 06.09. (N-53): `turnover` traegt RICHTUNG +0,00512 [+0,00212 .. +0,00831], 0/5 - richtungsrein der STAERKSTE der drei Groessen, zweieinhalbmal `funding`. Auf der registrierten Barrieren-Quote traegt es NICHT (+0,00168, Band mit Null), weil sein Aufloesungskanal (-0,00218) gegen die Richtung laeuft und den Effekt verdeckt. Der Vorschlag vom Vormittag (2.133: stilllegen) ist damit ueberholt - er stand auf dem gemischten Massstab. ⚠️ R-R9 OFFEN: auf welcher Zielgroesse die Stufen kalibriert werden. `q` ist ,Ziel vor Stop' (= G0); dort ist turnover schwach, weil die GEOMETRIE es daempft - das ist eine Aussage ueber die Geometrie, nicht ueber den Beitrag. --- FRUEHER: Nur 65 Symbole Abdeckung - das Nullband ist dreimal so "
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
            ("06.09.", "N23-E1: einzige belegte DREITEILUNG, beide Haelften, "
                       "2/2 Nachbarn getrennt"),
            ("06.09.", "✖✖✖ N-52: KEINE RICHTUNG. Richtungsrein (GS) "
                       "-0,00041 [-0,00287 .. +0,00194], 2/5 - und die "
                       "Drittel haben KEINE Ordnung mehr"),
            ("06.09.", "N-52: der Befund geht restlos in Groessenkanaele auf "
                       "- Aufloesungsquote +0,03088, Rest G0R +0,00760 "
                       "gegen Kunstwelt-Artefakt +0,00770 / +0,00731"),
        ),
        warnung="⚠️⚠️⚠️ STAND NACH N-52 (06.09.): `vola` GEHOERT NICHT IN "
                "`BEITRAEGE`. Richtungsrein gemessen traegt es nichts "
                "(GS -0,00041, 2/5, keine Ordnung der Drittel). Der starke "
                "Befund war unsere eigene Geometrie: ruhige Assets loesen "
                "ihre Barrieren oefter auf (+0,03088), und eine Aufloesung "
                "ist bei CRV 2 zu einem Drittel ein Treffer. Der Rest ist "
                "zahlengleich mit dem Artefakt aus zwei richtungsfreien "
                "Kunstwelten. "
                "✔✔ ABER KEIN NULLBEFUND: +3,1 Punkte auf die "
                "AUFLOESUNGSQUOTE sind der groesste saubere Effekt des "
                "Tages. `vola` gehoert in die GEOMETRIE- und HORIZONTWAHL - "
                "und ueber `hebel = verlustanteil / stop_rel` faellt daraus "
                "der Hebel. Das ist die als fehlend gefuehrte Horizont-"
                "Achse. "
                "⚠️ OFFEN (R-R11): N1-V2 fand am RANDMASS einen "
                "spiegelbildlichen Richtungseffekt (-0,00345). Das ist "
                "durch N-52 NICHT widerlegt - andere Zielgroesse -, steht "
                "aber unter Verdacht, weil das Randmass sich den "
                "Schiefe-Kanal mit `bewegung_r` teilt. Richtungsreine "
                "Nachmessung am Rand steht aus. "
                "--- FRUEHERER STAND (N12): `vola` ist die einzige der beiden "
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
    Befundlage("2.145", "`schnitt` (Abstand zum eigenen 200-Tage-Schnitt) "
               "TRAEGT auf der selektierten Menge: +0,1707 R "
               "[+0,0723 .. +0,2781] bei 20 %, Trennschaerfe 0,020. "
               "Abdeckung 516/516 (100 %), Redundanz gering (r -0,097 zu "
               "funding, -0,168 zu turnover). War als ,traegt nicht' "
               "abgelehnt", "gilt",
               "Methodik 2.145 / n59_abgelehnte_auf_selektierter_menge.py"),
    Befundlage("2.145-zeit", "⚠️ ABER `schnitt` haelt ueber die ZEIT nicht "
               "durch: erste Haelfte +0,3483 (nur 17 Bloecke), zweite "
               "+0,0375 (Trennschaerfe 0,10 - untermaechtig, nicht "
               "widerlegt). KANDIDAT, kein registrierungsreifer Befund",
               "offen", "Methodik 2.145"),
    Befundlage("2.145-turnover5", "⚠️ `turnover` verliert bei 5 % "
               "Auswahlstaerke ALLE Tage (65 Symbole, davon 5 % = 2 Anker). "
               "Die Produktionsauswahl IST diese 5 % - sein Beitrag ist bei "
               "der tatsaechlichen Auswahlstaerke NICHT messbar", "gilt",
               "Methodik 2.145"),
    Befundlage("2.150", "⚠️⚠️ `marktrang.schnitte()` rangte gegen ALLE "
               "1.314 Symbole der Messbasis - 798 davon Nicht-Krypto. Der "
               "Krypto-Schnittrang lief gegen AAPL. Gefixt: "
               "assetklasse='krypto' an beiden Stellen, 1.314 -> 516",
               "gilt", "Methodik 2.150 / agent/marktrang.py"),
    Befundlage("2.150-zufall", "✔ Es schlug nicht durch, weil "
               "`schnitt_werte()` einen Binance-USDT-Preis braucht - den "
               "haben Aktien nicht (0 von 29 Watchlist-Werten wechselten "
               "das Fuenftel). ⚠️ Aber es war Schutz durch ZUFALL der "
               "Datenlage, nicht durch Design", "gilt", "Methodik 2.150"),
    Befundlage("2.150-acht", "⚠️ Acht Werte waren doch falsch: BOND, C, "
               "DASH, DIA, MDT, MUB, STX, T - die F-198-Kollisionen. Fuer "
               "DASH wurde der Kryptopreis durch den DoorDash-Aktienschnitt "
               "geteilt", "gilt", "Methodik 2.150"),
    Befundlage("2.149", "STRUKTURFIX: F-198s Reparatur war im LADEPFAD nie "
               "angekommen - `lade_reihen_aus_db` las die "
               "`assetklasse`-Spalte nicht und gruppierte nach "
               "(symbol, currency). Jetzt filtert die Abfrage, und "
               "`_reihen_roh` ueberspringt die schaedliche 1:1-Zuordnung "
               "aus `messreihen`", "gilt",
               "Methodik 2.149 / pruefe_assetklassen_trennung.py"),
    Befundlage("2.149-beweis", "Der Fix aendert HEUTE NICHTS: ueber alle "
               "vier Klassen und 5,1 Mio Kurswerte BITGLEICH (516/470/293/"
               "35 Symbole). Kein bestehender Befund ist betroffen. 25 "
               "abhaengige Module importieren, Suite 1.988 bestanden",
               "gilt", "Methodik 2.149"),
    Befundlage("2.149-prod", "⚠️ Die PRODUKTIONSDATENBANK hat die "
               "`assetklasse`-Spalte NICHT. F-198 fuehrte sie nur in der "
               "Messbasis ein. Heute folgenlos (Watchlist-Symbole sind "
               "eindeutig), aber die Trennung ist dort strukturell nicht "
               "moeglich", "offen", "Methodik 2.149"),
    Befundlage("2.148", "F-198s offener Punkt ist BEANTWORTET: sieben "
               "Kryptoreihen fehlen wirklich (DASH 2.721 Kerzen, STX 2.510, "
               "DIA 2.195, MDT 2.149, T 1.656, BOND 1.114, C 417). Von 183 "
               ",fehlenden' Paaren sind 175 zu kurz und 7 Kollisionen",
               "gilt", "Methodik 2.148 / pruefe_messbasis_wechsel.py"),
    Befundlage("2.148-sperre", "⚠️ LADEN IST NOCH NICHT SICHER: F-198 hat "
               "`price_history_ohlc` gefixt (PK mit assetklasse), aber "
               "`messreihen` nicht - dort gilt ,eine Klasse je Symbol'. "
               "Rund zehn Messwerkzeuge lesen `klassen_aus_db` und wuerden "
               "die neuen Kryptokerzen falsch einordnen. ERST Strukturfix, "
               "DANN laden", "offen", "Methodik 2.148"),
    Befundlage("2.148-engpass", "⚠️ Die Messung scheitert NICHT an der "
               "Datenmenge: `schnitt` hat 233 Anker je Tag und 186 Bloecke "
               "(Grenze 20). Der Engpass ist die Wirkungsgroesse gegen die "
               "Streuung. Meine Empfehlung ,Kursreihen nachladen hilft' war "
               "falsch", "gilt", "Methodik 2.148"),
    Befundlage("2.147", "`schnitt`s STABILITAET ist mit diesen Daten NICHT "
               "ENTSCHEIDBAR. Bei H20 fehlen die Bloecke (BAER 19 von 20), "
               "bei H5 die Trennschaerfe (0,05 R ueber den Effekten). Die "
               "Gegenprobe `funding` faellt BEIDE Male in jeder Phase durch "
               "- ein Befund ueber die SCHICHTUNG, nicht ueber `schnitt`",
               "gilt", "Methodik 2.147 / n60_schnitt_stabilitaet.py"),
    Befundlage("2.147-weg", "⚠️ Die Frage braucht MEHR ANKER, nicht eine "
               "andere Schichtung. Eine dritte Einteilung zu suchen, bis "
               "eine ,traegt', waere der Fehler aus Prueflliste 2.80. Was "
               "hilft: die neun fehlenden Kursreihen nachladen", "offen",
               "Methodik 2.147"),
    Befundlage("2.146", "Abdeckung: Kern (BTC, ETH, SOL) 3/3 und grosse "
               "Werte 8/8 zu 100 % bewertbar - KEINE Luecke bei den "
               "stabilen Werten. Uebrige 16/33. ⚠️ 13 Nicht-Krypto-"
               "Eintraege gehoeren nicht in die Rechnung (richtig ist "
               "29 von 44, nicht von 57)", "gilt",
               "Methodik 2.146 / zeige_abdeckung_krypto.py"),
    Befundlage("2.146-luecke", "⚠️ Neun Watchlist-Werte haben funding/oi, "
               "aber KEINE Kursreihe: AKT, ASTER, BRETT, GRIFFAIN, HYPE, "
               "KAS, MON, MORPHO, PLUME. Keine Symbolfehler - die "
               "coingecko-IDs stimmen, die Kurse wurden nie geladen. "
               "Behebbar", "offen", "Methodik 2.146"),
    Befundlage("2.144", "Die MENGE ist jetzt an die FRAGE gebunden: "
               "`messnorm.FRAGEARTEN` lehnt ein Beitragsurteil auf der "
               "freien Menge ab und verweist auf `messnorm_auswahl`. Sechs "
               "Suite-Pruefungen sichern die Bindung", "gilt",
               "Methodik 2.144 / messnorm.FRAGEARTEN"),
    Befundlage("2.144-mengen", "Die tatsaechlichen Groessen: Messuniversum "
               "516 · Watchlist 57 (davon nur 29 im Messuniversum!) · "
               "selektiert ~2-3 je Tag · Abdeckung funding 288 (56 %), oi "
               "115 (22 %), turnover 65 (13 %)", "gilt", "Methodik 2.144"),
    Befundlage("2.144-ast", "⚠️ `ast.parse` faengt doppelte "
               "Schluesselwortargumente NICHT - nur `compile()`. Die "
               "Syntaxpruefung meldete 0 Fehler, waehrend Python beim "
               "Import SyntaxError warf", "gilt", "Methodik 2.144"),
    Befundlage("2.143", "AUDIT: sechs von sieben Messungen des 06./07.09. "
               "liefen auf der FREIEN statt der selektierten Menge. F-212 "
               "belegt seit 04.09., dass die Beitraege dort auf 1,5 % der "
               "Anker wirken. Dieselbe Fehlerklasse wie 2.134 - die "
               "Grundmenge ist Teil der FRAGE", "gilt",
               "Methodik 2.143 / pruefe_audit_06_07_09.py"),
    Befundlage("2.143-norm", "⚠️ Vier Nullbefunde ohne Trennschaerfe. Ich "
               "habe `messnorm` umgangen, weil meine Zielgroesse dort nicht "
               "vorgesehen war - und der Grund dafuer WAR der Befund. Wer "
               "die Norm umgeht, umgeht die Pruefung, die den eigenen "
               "Aufbau ablehnen wuerde", "gilt", "Methodik 2.143"),
    Befundlage("2.141", "„`turnover`s Stufen lassen sich nicht herleiten\"",
               "abgeloest", "Methodik 2.141", abgeloest_durch="2.143",
               warum="auf der FREIEN Menge gemessen, wo selbst funding bei "
                     "-0,0003 R liegt. Auf der selektierten reproduziert "
                     "turnover: +0,0635 gegen registriert +0,0616 (F-212)"),
    Befundlage("2.142", "„Kalibrierung durchgefuehrt: turnover auf "
               "+0,33/-0,48, Schwelle 0,005\"", "abgeloest",
               "Methodik 2.142", abgeloest_durch="2.143",
               warum="ZURUECKGENOMMEN - stand auf 2.139 und 2.141, beide "
                     "gefallen. Es bleibt der R-R9-Verstoss (nach Wirkung "
                     "statt Durchlassquote kalibriert) und die "
                     "Reproduktion des Verfahrens"),
    Befundlage("2.142-alt", "Kalibrierung durchgefuehrt: turnover-Stufen auf "
               "(+0,33 x3, -0,48 x2), SCHWELLE_VORGABE 0,080 -> 0,005. "
               "erreichbar_max faellt 0,1335 -> 0,0489 R, Durchlass steigt "
               "16,4 % -> 54,0 %. Verfahren vorher an der alten Lage "
               "REPRODUZIERT (gab 0,080 zurueck)", "gilt",
               "Methodik 2.142 / Befundkarte 3.9d"),
    Befundlage("2.142-fiktion", "⚠️⚠️ Haerter filtern macht das Ergebnis "
               "SCHLECHTER (bei 0,010: -0,0558 je verworfenem). Die alte "
               "Schwelle 0,080 war die beste WEGEN turnovers riesiger "
               "Stufen - die Trennschaerfe der Schwelle kam aus einer "
               "Fiktion", "gilt", "Methodik 2.142"),
    Befundlage("2.141", "`turnover`s Stufen lassen sich NICHT herleiten - "
               "weder als Fuenfteilung noch als Zweiteilung noch als "
               "SCHALTER. Trennschaerfe 2,0 Punkte; die registrierte "
               "Tabelle hat 5,55 Punkte Spanne - waere sie echt, wuerde man "
               "sie sehen", "gilt",
               "Methodik 2.141 / n58_turnover_stufen_neu.py"),
    Befundlage("2.141-lage", "⚠️ ENTSCHEIDUNG OFFEN: Tabelle lassen (aktiv "
               "falsch), auf die gemessene Zweiteilung +0,33/-0,48 (nicht "
               "belegt, aber 17x kleiner und gleichgerichtet) oder auf null "
               "(entfernt einen belegten Richtungstraeger). Jeder Weg "
               "verlangt R-R9", "offen", "Methodik 2.141"),
    Befundlage("2.140", "Bei H5 laufen 31,4 % der Anker FLACH aus (H20: "
               "5,3 %). Die Kalibrierungsbasis zaehlt sie als "
               "Nicht-Treffer und liegt damit um +0,2898 R daneben - mit "
               "falschem Vorzeichen (-0,3654 gegen +0,0430)", "gilt",
               "Methodik 2.140 / n57_flach_in_der_produktion.py"),
    Befundlage("2.140-formel", "✔ Die POTENTIALFORMEL stimmt fuer die "
               "Produktion: unter den Aufgeloesten liegt die Trefferquote "
               "bei 34,8 %, die Formel setzt basisrate(2,0) = 33,3 %. "
               "Kaputt ist die Messung, nicht die Bewertung", "gilt",
               "Methodik 2.140"),
    Befundlage("2.139-quote-deutung", "„`q` in der Potentialformel zaehlt "
               "einen wertlosen Kanal mit\"", "abgeloest", "Methodik 2.139",
               abgeloest_durch="2.140",
               warum="falsch adressiert. Die Kette hat KEINEN Zeitausstieg "
                     "- in der Produktion laeuft eine Position bis Stop "
                     "oder Ziel. Der Fehler sitzt in der Messkonvention "
                     "mit festem Horizont, nicht in der Formel"),
    Befundlage("2.139", "Die LIVE geschaltete OI-Sperre traegt RICHTUNG: "
               "GS +0,00220 [+0,00058 .. +0,00373] bei H20 und +0,00381 "
               "[+0,00205 .. +0,00550] bei H5, beide 0/5. Reproduktion in "
               "der Live-Form gelungen (+0,00978, registriert +0,0145 im "
               "Band)", "gilt", "Methodik 2.139 / n56_oi_richtungsrein.py"),
    Befundlage("2.139-quote", "⚠️ Dieselbe Sperre SENKT bei H5 die "
               "Barrieren-Trefferquote (-0,00262, Band ganz im Minus), weil "
               "der Aufloesungskanal dagegenlaeuft (-0,00989). Richtung "
               "besser, Quote schlechter - und `q` in der Potentialformel "
               "IST die Quote", "gilt", "Methodik 2.139"),
    Befundlage("2.139-turnover", "⚠️⚠️ `turnover` reproduziert NICHT: "
               "gemessen -0,06293 [-0,13183 .. -0,00785] gegen registriert "
               "+0,0616 - gleiche Groessenordnung, umgekehrtes Vorzeichen. "
               "Die Fuenftel haben keine Ordnung (bestes ist 4, die Tabelle "
               "bestraft es mit -2,40). Bestaetigt 2.133", "gilt",
               "Methodik 2.139"),
    Befundlage("2.139-funding", "`funding` reproduziert bis in die FORM: "
               "Fuenftel +0,071 +0,083 +0,009 -0,053 -0,105, monoton, und "
               "auch die registrierte Tabelle hat bei Fuenftel 1 ihr "
               "Maximum", "gilt", "Methodik 2.139"),
    Befundlage("Audit-H20R", "„Die Registrierungsbasis H20/R ist "
               "kontaminiert\"", "abgeloest", "Audit 06.09.",
               abgeloest_durch="2.139",
               warum="zu stark formuliert. Belegt war die Kontamination "
                     "fuer H5 mit `vola`; bei H20 mit externen Kennzahlen "
                     "feuert `bewegung_r` in keiner der beiden Kunstwelten"),
    Befundlage("2.138", "`vola` ordnet den realisierten Ertrag: die "
               "Spreizung ruhig-lebhaft liegt in ALLEN 12 Geometrien ueber "
               "der artefaktbedingten (+0,035 bis +0,126 R, Tagesklammer). "
               "Es waehlt aber KEINE Bauform - dieselbe Geometrie gewinnt "
               "in allen Dritteln (Stop 2,0 x ATR / H20)", "gilt",
               "Methodik 2.138 / n55_vola_in_der_geometrie.py"),
    Befundlage("2.138-null", "Der Nullpunkt fuer ,EW in R' ist NICHT null: "
               "Tageskerzen ueberschiessen die Barriere, die nahe staerker "
               "als die ferne (P(Ziel|aufgeloest) 0,344 statt 0,333). Er "
               "wird aus drei GEEICHTEN Kunstwelten gewonnen; ungeeicht "
               "unterschaetzt man ihn um das Doppelte", "gilt",
               "Methodik 2.138"),
    Befundlage("2.138-offen", "⚠️ Die ZUSCHREIBUNG der Spreizung ist offen. "
               "Die Kunstwelt hat einen Strukturfehler: Hoch und Tief sind "
               "dort unabhaengiges Rauschen um den Schluss, in echten Daten "
               "liegt an einem Aufwaertstag das Tief nahe der Eroeffnung. "
               "Sie ueberschaetzt die Stop-Treffer. Naechster Schritt: "
               "Brownsche Bruecke je Tag", "offen", "Methodik 2.138"),
    Befundlage("2.136", "`turnover` traegt RICHTUNG +0,00512 "
               "[+0,00212 .. +0,00831], 0/5 - richtungsrein der STAERKSTE "
               "der drei. Auf der registrierten Barrieren-Quote traegt es "
               "nicht (+0,00168 ns), weil sein Aufloesungskanal (-0,00218) "
               "gegen die Richtung laeuft", "gilt",
               "Methodik 2.136 / n53_richtungsprobe_alle_drei.py"),
    Befundlage("2.136-f", "`funding` traegt RICHTUNG +0,00197 "
               "[+0,00024 .. +0,00376], 0/5, und reitet den "
               "Aufloesungskanal NICHT (AUF ns) - sein G0-Befund war "
               "sauber, nur unguenstig gemessen", "gilt", "Methodik 2.136"),
    Befundlage("2.136-EWR", "Auch der Erwartungswert in R ist kontaminiert: "
               "er feuert in der richtungsfreien Kunstwelt (+0,01363). Vier "
               "von sechs Massstaeben sind es - sauber ist allein GS",
               "gilt", "Methodik 2.136"),
    Befundlage("2.133-turnover", "„`turnover` ist in keiner Form belegt und "
               "gehoert stillgelegt\"", "abgeloest", "Methodik 2.133",
               abgeloest_durch="2.136",
               warum="auf der Barrieren-Quote gemessen, die Aufloesung und "
                     "Richtung mischt. Richtungsrein ist turnover der "
                     "staerkste der drei"),
    Befundlage("2.137", "Die zwei Ebenen spielen NICHT zusammen - funding "
               "und turnover wirken nicht staerker im guten vola-Drittel "
               "(Baender ueberlappen). `vola` ist ein UNABHAENGIGER "
               "Geometriehebel", "gilt", "Methodik 2.137"),
    Befundlage("2.135", "`vola` traegt KEINE Richtung - richtungsrein "
               "(symmetrische Barrieren, nur aufgeloeste Anker) -0,00041 "
               "[-0,00287 .. +0,00194], 2/5, keine Ordnung der Drittel. "
               "Der Befund geht restlos in zwei GROESSENkanaele auf",
               "gilt", "Methodik 2.135 / n52_vola_geometrieprobe.py"),
    Befundlage("2.135-AUF", "Die AUFLOESUNGSQUOTE traegt +0,03088 "
               "[+0,02753 .. +0,03436], monoton ueber die Drittel - ruhige "
               "Assets loesen ihre Barrieren nachweisbar oefter auf. "
               "Groesster sauberer Effekt des Tages, aber ueber die "
               "GEOMETRIE, nicht ueber den Markt", "gilt", "Methodik 2.135"),
    Befundlage("2.133-vola", "„`vola` ist die einzige Groesse mit belegter "
               "Stufenordnung und gehoert registriert\"", "abgeloest",
               "Methodik 2.133", abgeloest_durch="2.135",
               warum="an der Barrieren-Quote gemessen, die Aufloesung und "
                     "Richtung mischt. Richtungsrein bleibt nichts uebrig"),
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
               "- welche Durchlassmenge bleibt?", "abgeloest",
               "Methodik 2.121", abgeloest_durch="2.126",
               warum="Die Frage war falsch gestellt. Die Werte passieren die "
                     "Auswahl ueber den BESTANDSVORRANG, nicht ueber den "
                     "Momentum-Rang (F-180/F-182) - eine Durchlassrechnung "
                     "auf der Momentum-Auswahl bildet den Betrieb nicht ab. "
                     "Und eine vola-Sperre stuende vor derselben Gabel wie "
                     "N-14: mit Bestandsausnahme wirkungslos, ohne sie "
                     "trifft sie genau die Werte, die als einzige durchkommen"),
    Befundlage("2.126", "Die SPERRFORM ist fuer `vola` der falsche Weg - er "
               "gehoert als BEITRAG. Ein Beitrag unterliegt nicht der "
               "Bestandsausnahme und passt zur Quoten-Architektur", "gilt",
               "Methodik 2.126"),
    Befundlage("2.126-Auswahl", "Die 250-Tage-Momentum-Auswahl selektiert "
               "systematisch HOCHVOLATILE Werte: bei 5 % Auswahl trifft eine "
               "20-%-vola-Sperre 74,8 % statt der erwarteten 20 %", "gilt",
               "Methodik 2.126",
               warum="auf der FREIEN Menge sind beide unabhaengig (20,3 % "
                     "gegen 20,0 %) - die Ueberschneidung entsteht "
                     "ausschliesslich durch die Auswahl"),
    Befundlage("N16", "`vola` als BEITRAG verdrahten - Quotenpunkte je "
               "Fuenftel aus der Randwirkung", "offen", "Methodik 2.126",
               warum="R-R9 beachten: Beitragswechsel = Neukalibrierung der "
                     "Schwelle plus Nachzug von KALIBRIERT_FUER"),
    Befundlage("N17", "Traegt der Momentum-Rang etwas ueber `vola` hinaus? "
               "74,8 % Ueberschneidung bei 5 % Auswahl", "offen",
               "Methodik 2.126"),
    Befundlage("N18", "Der Engpass ist der COOLDOWN (93,8 %), nicht die "
               "Auswahl und nicht eine fehlende Sperre", "offen",
               "F-180/F-182 · Methodik 2.126",
               warum="jede weitere Sperre verschaerft ein System, dessen "
                     "Problem nicht Durchlaessigkeit ist"),
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
