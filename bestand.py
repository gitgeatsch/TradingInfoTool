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
    # ⚠️⚠️ DIE BASIS MASCHINENLESBAR (09.09.2026) - `basis` ist Freitext
    # und nennt die MENGE nicht. An EINEM Tag sind daraus DREI
    # R-R11-Fehler entstanden: `turnover` auf der vollen Historie statt
    # auf `frei`, `oi_aenderung` auf 20 % ab 2022 statt auf `frei`, und
    # `funding` beinahe ebenso.
    #
    # ⚠️ NICHT VERWECHSELN mit den Mengen aus Befund 2.162 (turnover 50 %,
    # funding 10 %, oi_aenderung 20 %). Die stammen aus einer EIGENEN
    # Messung zur Zeitstabilitaet - sie sind NICHT die
    # Registrierungsbasis. 2.161-rr11 sagt es woertlich: *"Der
    # registrierte Befund stammt von der FREIEN Menge."*
    menge: str = ""                 # "frei" | "5%" | "10%" | "20%" | "50%"
    fenster: str = ""               # "voll" | "2022-01-01" | ...


def messbasis(name: str) -> tuple:
    """Die REGISTRIERUNGSBASIS eines Kandidaten -> (menge, fenster).

    ⚠️⚠️ VOR JEDER MESSUNG AUFRUFEN. Wer mehrere Kandidaten in einem Lauf
    auf DERSELBEN Menge misst, misst bei mindestens einem etwas anderes
    als das Registrierte - und ein abweichendes Ergebnis widerlegt dann
    nichts (R-R11).

    An einem einzigen Tag (09.09.2026) sind aus genau diesem Muster DREI
    Fehler entstanden. Deshalb gibt es diese Funktion.

        menge, fenster = bestand.messbasis("turnover")   # ("frei", "voll")
        je = {t: z for t, z in je.items()
              if fenster == "voll" or str(t) >= fenster}

    Ein leeres Ergebnis heisst: **die Basis ist nicht maschinenlesbar
    hinterlegt** - dann im Kandidatenregister nachsehen und sie eintragen,
    nicht raten.
    """
    for k in KANDIDATEN:
        if k.name == name:
            return (k.menge, k.fenster)
    raise KeyError("%r steht nicht im Kandidatenregister" % name)


KANDIDATEN = (
    Kandidat(
        menge="frei", fenster="voll",
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
        menge="frei", fenster="voll",
        name="turnover",
        hypothese=("Handelsvolumen je Umlaufmenge - viel Aufmerksamkeit "
                   "heisst eher ueberbewertet."),
        form="regler",
        basis="H20 · 2.636 Kalendertage",
        wert="+0,0616 R [+0,0203 .. +0,1111]",
        # ⚠️⚠️ AM 07.09. STAND HIER EIN VERALTETER WERT. Das Feld nannte
        # "(+0.33, +0.33, +0.33, -0.48, -0.48) seit 07.09." - die
        # Aenderung war am selben Tag ZURUECKGENOMMEN (2.143), und die
        # `warnung` unten sagte das auch. Das Blatt widersprach sich
        # selbst und dem Code. Genau der Fall, den das Register
        # verhindern soll.
        live="agent/wahrscheinlichkeit.BEITRAEGE · merkmal turnover_fuenftel "
             "· Stufen (+3.15, +0.83, +0.22, -1.79, -2.40) "
             "· 07.09. entzerrt NACHGERECHNET und bestaetigt "
             "(Querschnitt +3,13/+0,76/+0,22/-1,73/-2,38, Methodik 2.165)",
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
        menge="frei", fenster="voll",
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
        name="akkumulationsmass (= schnitt, H90)",
        hypothese=("Kauf in BODENNAEHE: je tiefer unter dem eigenen "
                   "200-Tage-Schnitt, desto guenstiger der Einstieg "
                   "innerhalb einer Akkumulation."),
        form="regler",
        basis="H90 · 505 Krypto-Reihen · 3.292 Tage · zirkulaerer Verschub",
        wert="stetig monoton ueber NEUN Baender: unter -40 % +0,0960 "
             "(+6,06 %) bis ueber +30 % -0,1508 (-11,79 %)",
        live="- NICHT registriert",
        zustand="offen",
        kette=(
            ("28.08.", "Nutzerauftrag: ,fuer Akkumulation eine Begruendung, "
                       "also echtes Signalmass finden'"),
            ("28.08.", "Schalter UNTER_SMA +0,0283 (p=0,000) - traegt, aber "
                       "feuert an 68,5 % aller Tage"),
            ("28.08.", "Die STETIGE Form ist staerker und monoton ueber "
                       "neun Baender, in BEIDEN Kalenderhaelften"),
            ("28.08.", "Kontrollen: TIEFPUNKT +0,4242 (Maschine intakt) · "
                       "WOCHENTAG -0,0008 p=0,978 · DCA exakt 0,0000"),
            ("28.08.", "⚠️⚠️ TRAEGT NICHT FUER BTC/ETH/SOL - und genau die "
                       "sind fuer akkumulation freigeschaltet"),
            ("07.09.", "N-59: DERSELBE Wert traegt bei `einstieg` auf der "
                       "selektierten Menge (+0,1707 R, 100 % Abdeckung)"),
        ),
        warnung="⚠️⚠️ ES IST DERSELBE WERT WIE `schnitt` - nur auf H90 "
                "statt H20 und als Akkumulationsmass gelesen. Das war bis "
                "zum 07.09. nicht verknuepft: der Befund vom 28.08. stand "
                "in `Befund_Akkumulationsmass_28_08.md` und NICHT im "
                "Register. "
                "⚠️ DIE ENTSCHEIDENDE EINSCHRAENKUNG: fuer BTC (-0,0251, "
                "p=0,723), ETH (-0,0308) und SOL (-0,0291) traegt es NICHT "
                "- und `asset_dca_settings` enthaelt genau BTC und ETH. "
                "Es ist kein n=3-Rauschen: die Kernwerte liegen 2,39 "
                "Standardfehler unter dem Mittel, und nur 14,3 % aller 505 "
                "Symbole haben einen negativen Vorsprung. "
                "⚠️ Der Effekt SCHRUMPFT: unterstes Band 1. Haelfte +0,2020 "
                "-> 2. Haelfte +0,0879, Faktor 2,3. "
                "⚠️ Und es ist KEIN Alpha-Nachweis: es sagt, WANN innerhalb "
                "einer Akkumulation gekauft wird - nicht, OB akkumuliert "
                "werden soll."),
    Kandidat(
        name="schnitt",
        hypothese="Abstand zum eigenen 200-Tage-Schnitt.",
        form="regler",
        basis="H1..H20 Horizontlauf 31.08.",
        wert="H5 -0,0069 · H10 -0,0118 · H20 -0,0221",
        live="- zurueckgenommen",
        zustand="offen",
        kette=(
            ("31.08.", "mittags als dritter tragender Beitrag registriert"),
            ("31.08.", "abends im Horizontlauf gefallen - bei keinem "
                       "Horizont trennbar, bei langen negativ"),
        ),
        warnung="✔✔ DER 31.08.-BEFUND IST ABGELOEST (07.09., 2.153). Reproduziert mit DEMSELBEN Werkzeug drehen ALLE Vorzeichen: H5 -0,0069 -> +0,0092 ✔ · H10 -0,0118 -> +0,0158 ✔ · H20 -0,0221 -> +0,0299 (nicht trennbar). Die Kontrolle reproduziert bitgenau (funding H20 +0,0246). ⚠️ URSACHE: am 31.08. lief die Messung auf 1.314 Symbolen - Krypto PLUS 798 Aktien/ETF/Rohstoffe. Der N-19-Fix kam erst am 03./04.09. `funding` war geschuetzt (krypto-exklusive Quelle), `schnitt` NICHT - er kommt aus Kursreihen, und die gab es fuer Aktien. ⚠️⚠️ MEIN VERFAHRENSFEHLER: N-59 hat den Befund umgestossen, OHNE ihn zuerst zu reproduzieren (R-R11). Dass er am Ende faellt, macht das Verfahren nicht richtig. --- FRUEHER: ⚠️ Die Marken tragen weiterhin den STOP - nur als "
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
    basis: str = ""
    """⚠️⚠️ AUF WELCHER MESSBASIS STEHT DIESER BEFUND? (08.09.2026)

    Am 08.09. wurde die Messbasis zweimal geaendert - Auffrischung (347
    Reihen auf den 08.09.) und Uebernahme (10 Symbole, 526 -> 536). Danach
    war nicht mehr feststellbar, welche der 92 geltenden Befunde auf
    welcher Grundlage entstanden waren; 25 tragen Messzahlen, und jede
    einzelne haette geprueft werden muessen.

    ⚠️ **R-R11 verlangt Reproduktion vor Widerruf - aber wer nicht weiss,
    WORAUF ein Befund steht, kann ihn nicht reproduzieren.** Genau das
    macht dieses Feld sichtbar.

    Vorgabe leer, damit die 92 Altbefunde unveraendert bleiben; ein
    leeres Feld heisst "Basis nicht vermerkt", nicht "keine Basis". Ab
    dem 08.09. wird es gefuellt."""


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
    Befundlage("2.162", "✔✔ DIE LOESUNG FUER `turnover`: DIE MENGE MUSS "
               "ZUR DATENLAGE PASSEN. Kriterium, vorab gesetzt und fuer "
               "ALLE Beitraege gleich: die SCHMALSTE Menge, die noch >= "
               "12 Anker je Tag liefert (dieselbe Untergrenze, die "
               "`sammle` bereits im Code verwendet). Ergebnis: turnover "
               "50 %, funding 10 %, oi_aenderung 20 %, zufall 5 %. Dort "
               "traegt jeder der drei ab 2022 - turnover +0,0598, "
               "funding +0,0607, oi_aenderung +0,0446, alle mit Band "
               "ohne Null; `zufall` +0,0052 mit Null im Band", "gilt",
               "Methodik 2.162 / n72_turnover_loesung.py"),
    Befundlage("2.162-grund", "Der GRUND war nie der Beitrag: `turnover` "
               "deckt 66 von 524 Symbolen ab. 20 % davon sind 10,1 Anker "
               "je Tag - und N-65 hat gemessen, dass die Statistik bei "
               "so kleinen Gruppen fast nur Rauschen ist. Wer alle "
               "Beitraege auf 20 % zwingt, misst bei einem von ihnen "
               "Rauschen", "gilt", "Methodik 2.162"),
    Befundlage("2.162-b", "⚠️ Die DATENQUELLE wurde mitgeprueft und ist "
               "in Ordnung (stehende Vorgabe). Der `splycur`-Ausreisser "
               "ab 2023 ist XVG - aber eine grosse UMLAUFMENGE macht den "
               "Quotienten KLEIN. Die Kennzahl selbst ist stabil ueber "
               "alle Jahre (Median 0,003-0,010, P95 0,036-0,079) und "
               "geht ohnehin als RANG ein", "gilt", "Methodik 2.162"),
    Befundlage("2.162-extreme", "Und die Fuenftel zeigen, warum die "
               "LIVE-Regel nie betroffen war: die EXTREME sind ueber die "
               "Aeren stabil - F0 +0,2314 -> +0,2745, F4 -0,1354 -> "
               "-0,1316. Nur die MITTE dreht (F1 +0,5334 -> +0,0375). "
               "Die Sperre trifft F4", "gilt", "Methodik 2.162"),
    Befundlage("2.161", "✔✔ DIE ZEITSTABILITAET DER LEBENDEN BEITRAEGE - "
               "erstmals gemessen. `oi_aenderung` ist der SOLIDESTE: "
               "stabil bis 0,05 R (Haelften -0,0038) und traegt in JEDEM "
               "Fenster - ganz +0,0296 [+0,0146 .. +0,0443], ab 2022 "
               "+0,0296, ab 2024 +0,0287. Praktisch unveraendert ueber "
               "die Zeit. `funding` ebenso: stabil bis 0,05 R, traegt ab "
               "2022 (+0,0157) und ab 2024 (+0,0182)", "gilt",
               "Methodik 2.161 / n70_stabilitaet_der_lebenden.py"),
    Befundlage("2.161-turnover", "„`turnover` dreht ab 2022 das "
               "Vorzeichen (-0,0112 / -0,0307)\"", "abgeloest",
               "Methodik 2.161", abgeloest_durch="2.162",
               warum="auf der 20-%-Menge gemessen, die seine Datenlage "
                     "NICHT traegt: 10,1 Anker je Tag (frueh 5,3). "
                     "`pruefe_auswahl` reproduziert den Wechsel NICHT und "
                     "sagt woertlich 'KEIN BEFUND - untermaechtig'. Auf "
                     "der Menge, die seine Abdeckung traegt (50 %), ist "
                     "er ab 2022 POSITIV: +0,0598 [+0,0066 .. +0,1139]"),
    Befundlage("2.161-rr11", "R-R11 erfuellt, BEVOR das behauptet wird: "
               "`pruefe_auswahl` reproduziert den registrierten Anker "
               "exakt - turnover frei +0,0616 [+0,0185 .. +0,1084] gegen "
               "Anker +0,06163 [+0,01851 .. +0,10841]. ⚠️ AUF DER "
               "SELEKTIERTEN Menge aber, wo Beitraege zu beurteilen sind "
               "(F-212, frageart=beitrag), liegt er bei +0,0865 [-0,0060 "
               ".. +0,1696] - das Band schliesst die Null EIN, Urteil "
               "'traegt nicht bis 0,10 R'. Der registrierte Befund stammt "
               "von der FREIEN Menge", "gilt", "Methodik 2.161"),
    Befundlage("2.161-f217", "⚠️ Das VERSTAERKT F-217 ('funding haelt, "
               "turnover NICHT - gegen zwei Nullpunkte') aus einer "
               "voellig anderen Richtung: dort war es die Kalibrierung, "
               "hier die Zeitachse. Zwei unabhaengige Zugaenge, dasselbe "
               "Ergebnis - das ist mehr als eine Wiederholung", "gilt",
               "Methodik 2.161"),
    Befundlage("2.161-massstab", "⚠️ WARUM DIESE MESSUNG UEBERHAUPT KAM: "
               "der Test, an dem `schnitt` gescheitert ist, war auf die "
               "LIVE laufenden Beitraege nie angewandt worden. Einen "
               "Kandidaten an einer Huerde scheitern zu lassen, die die "
               "Bestandsbeitraege nie nehmen mussten, waere zweierlei "
               "Mass gewesen", "gilt", "Methodik 2.161"),
    Befundlage("2.160", "„`schnitt` ist nicht zeitstabil: Haelften "
               "+0,2238 R [+0,0792 .. +0,3988], Trennschaerfe 0,02 R\"",
               "abgeloest", "Methodik 2.160", abgeloest_durch="2.163",
               warum="ZWEI Fehler, beide eigene. (1) Gemessen auf der "
                     "20-%-Menge - `schnitt`s Datenlage verlangt 10 % "
                     "(schmalste mit >= 12 Ankern UND >= 20 Bloecken). "
                     "Dort ist der Unterschied -0,0647 [-0,3098 .. "
                     "+0,2161], also mit umgekehrtem Vorzeichen und "
                     "nicht trennbar. (2) Die Trennschaerfe war auf die "
                     "ECHTE Reihe gepflanzt, also auf einen bereits "
                     "trennbaren Unterschied - dann bleibt er es bei "
                     "jedem Versatz. 'Ab 0,02 R' hiess nur 'der Effekt "
                     "ist gross'. Zentriert gemessen liegt sie bei "
                     ">0,20 R"),
    Befundlage("2.171", "⛔⛔ `hedge` IST STRUKTURELL AUSSERHALB DER "
               "BEITRAGSMASCHINERIE - aus DREI unabhaengigen Gruenden, "
               "nicht wegen fehlender Daten. Jeder einzelne genuegt", "gilt",
               "Methodik 2.171 / Bestandsdurchsicht 07.09."),
    Befundlage("2.171-zwei", "GRUND 1 - ZWEI INSTRUMENTE. `hedge` kennt "
               "DBPK (S&P 500 2x invers) und 3QSS (Nasdaq-100 3x short). "
               "`messe_beitrag_auf_auswahl.sammle` verwirft Tage mit "
               "weniger als 12 Werten. Zwei Werte sind kein Querschnitt - "
               "es gibt nichts zu rangen", "gilt", "Methodik 2.171"),
    Befundlage("2.171-rekonstruiert", "GRUND 2 - DIE REIHEN SIND "
               "REKONSTRUIERT und ihre Grenze steht in der eigenen "
               "Dokumentation: `agent/rekonstruktion.py` sagt woertlich, "
               "die Reihen taugen 'fuer KURZE Horizonte (Tage bis zwei "
               "Wochen)' und 'NICHT fuer Aussagen ueber Monate'. Es "
               "fehlen Rollkosten, Gebuehren und beim Hebelprodukt der "
               "Wechselkurs. ⚠️ H20 sind VIER Wochen - ausserhalb der "
               "benannten Gueltigkeit", "gilt", "Methodik 2.171"),
    Befundlage("2.171-frage", "GRUND 3 - ES IST EINE ANDERE FRAGE. Das "
               "Hedge-Regelwerk (`agent/hedge/analyst.py`) fragt WANN "
               "abgesichert wird: Regel 5 nennt `aktien_baermarkt.aktiv`, "
               "VIX, DXY, Regel 6 die Makro-Analoge. Das ist eine "
               "ZEITREIHEN-Frage. Die Beitragsmaschinerie rangt "
               "innerhalb des Tages - sie ist querschnittlich (N-75). "
               "Und Regel 3 sagt ausdruecklich: 'das Ziel ist NICHT "
               "maximaler Gewinn der Hedge-Position selbst, sondern eine "
               "ANGEMESSENE Portfolio-Absicherung' - `bewegung_r` misst "
               "also die falsche Groesse", "gilt", "Methodik 2.171"),
    Befundlage("2.171-aufbau", "WIE `hedge` HEUTE FUNKTIONIERT: es ist "
               "KEINE Assetklasse, sondern eine ROLLE - die Instrumente "
               "stehen in der Watchlist als `etf`, deshalb hat "
               "`price_history_ohlc` keine hedge-Zeile. Deckel: "
               "max_abdeckung_anteil 1,0, "
               "bull_wahrscheinlichkeit_schwelle 35 % mit "
               "Positionsdeckel 0,5. Beide Positionen sind GEHALTEN "
               "(3QSS 218,25 · DBPK 1.739,16) und haben Einstandspreise "
               "(2,05 bzw. 0,1713 EUR, in `avg_buy_price_manual_eur`)",
               "gilt", "Methodik 2.171"),
    Befundlage("2.171-offen", "⚠️ WAS VON HIER AUS NICHT FESTSTELLBAR "
               "IST: ob `hedge` produktiv Signale erzeugt. Die "
               "Desktop-Kopie der Produktiv-DB endet Mitte Juli 2026 "
               "(`signals` 21.07., `holdings` 19.07.); die laufende "
               "Produktion ist das Notebook. Die 0 Hedge-Signale in "
               "dieser DB sind deshalb KEIN Befund ueber den Betrieb",
               "gilt", "Methodik 2.171"),
    Befundlage("2.171-weg", "WAS `hedge` STATTDESSEN BRAUCHT: ein "
               "eigenes Bewertungsverfahren auf der ZEITACHSE - 'wann "
               "absichern', gemessen gegen die Regime-Groessen, die das "
               "Regelwerk bereits nennt. ⚠️ Das ist dieselbe Frage wie "
               "die der MAKRO-Schichter aus N-8: `macro_snapshot` (3.384 "
               "Tage) und `makro_historie_monat` (1.184 Monate) haben je "
               "Tag EINEN Wert fuer alle Assets - sie koennen kein "
               "Querschnittsbeitrag sein, wohl aber ein Regime-Schichter",
               "gilt", "Methodik 2.171"),
    Befundlage("2.170", "„In Aktien traegt kein Kandidat - ein "
               "belastbarer Nullbefund\"", "abgeloest", "Methodik 2.170",
               abgeloest_durch="2.172",
               warum="die Zielgroesse `bewegung_r` ist ueber die Klassen "
                     "NICHT vergleichbar. Sie teilt durch "
                     "max(5 % Kurs, 0,75 ATR) - und bei Nicht-Krypto "
                     "bindet fast immer der 5-%-Boden (Aktien 97,1 %, "
                     "ETF 99,2 %). Der Stop liegt dort 2,29 bzw. 4,43 "
                     "ATR entfernt statt 0,75. In eigenen "
                     "Streuungseinheiten sind die Aktien-Effekte GENAUSO "
                     "GROSS wie die von Krypto (0,038 gegen 0,047) - sie "
                     "waren nur nicht von null zu trennen"),
    Befundlage("2.170-grundbefund", "„Der Grundbefund vom 10.08. ist "
               "nicht krypto-spezifisch - er gilt in Aktien genauso\"",
               "abgeloest", "Methodik 2.170", abgeloest_durch="2.172",
               warum="stand auf 2.170 und faellt mit ihm. Die Messung "
                     "konnte in Aktien gar nichts zeigen"),
    Befundlage("2.189", "N-82: die Beitragslage unter BEIDEN Nullregeln, "
               "16 Kandidaten auf allen zulaessigen selektierten Mengen. "
               "`zufall` traegt unter KEINER der beiden - der Lauf ist "
               "gueltig. 14 von 16 Kandidaten behalten ihr Urteil "
               "UNVERAENDERT", "gilt",
               "n82_beitragslage_beide_nullregeln.py",
               basis="Messbasis 08.09.2026, 536 Krypto-Reihen, H20"),
    Befundlage("2.189-wechsel", "⚠️ Genau EIN Kandidat wechselt: `funding` "
               "von TRAEGT auf NICHT ENTSCHEIDBAR. Er trug nur bei 50 % "
               "und dort mit +0,0002 R Abstand. ⚠️ NICHT ENTSCHEIDBAR ist "
               "eine Aussage ueber die MESSUNG, nicht ueber `funding` - "
               "er ist damit NICHT widerlegt", "gilt",
               "n82_beitragslage_beide_nullregeln.py",
               basis="Messbasis 08.09.2026, selektierte Mengen"),
    Befundlage("2.189-beidseitig", "⚠️ DIE NEUE REGEL IST NICHT STRENGER, "
               "SONDERN STABIL - sie bewegt sich in BEIDE Richtungen. "
               "`schnitt` bei 10 % kippt umgekehrt, von traegt-nicht auf "
               "TRAEGT (null_oben 0,0609 -> 0,0482), weil das Maximum "
               "ueber fuenf Ziehungen dort zufaellig HOCH lag. Wer die "
               "Regel fuer eine Verschaerfung haelt, hat sie nicht "
               "verstanden", "gilt", "n82_beitragslage_beide_nullregeln.py",
               basis="Messbasis 08.09.2026, 536 Krypto-Reihen"),
    Befundlage("2.190", "✔✔ R-R11 ERFUELLT: der `funding`-Originalbefund "
               "vom 30.08. (+0,137 R) stand auf der Menge `frei` - die "
               "Mengen-Systematik gab es damals nicht. Auf DIESER Basis "
               "nachgemessen traegt er unter BEIDEN Regeln: Abstand "
               "+0,0042 (alt) und +0,0044 (neu), 353.892 Anker, 299 "
               "Symbole, 39 Bloecke. Der Befund steht", "gilt",
               "n83_frei_beide_nullregeln.py",
               basis="Messbasis 08.09.2026, Menge `frei`, H20"),
    Befundlage("2.190-form", "✔ UND DIE LIVE-FORM PASST DAZU: `funding` "
               "ist als 'Funding-Rang im MARKT' registriert - `frei` "
               "beantwortet nach P6/F-212 genau die Marktfrage. Was "
               "faellt, ist `funding` als BEITRAG auf der selektierten "
               "Menge; die live genutzte Form ist davon unberuehrt",
               "gilt", "n83_frei_beide_nullregeln.py",
               basis="agent/wahrscheinlichkeit.BEITRAEGE, Stand 08.09."),
    Befundlage("2.191", "⚠️⚠️ `turnover` KIPPT dagegen auf seiner einzigen "
               "Basis `frei`: Abstand +0,0018 (alt) -> -0,0008 (neu), "
               "Urteil NICHT TRENNBAR. Auf den selektierten Mengen war er "
               "schon vorher nicht entscheidbar. Damit hat `turnover` "
               "unter der stabilen Nullregel KEINE Basis mehr, auf der er "
               "traegt", "gilt", "n83_frei_beide_nullregeln.py",
               basis="Messbasis 08.09.2026, Menge `frei`, 124.221 Anker"),
    Befundlage("2.191-inkonsistenz", "⚠️⚠️ UND GENAU DORT SCHLAEGT DIE "
               "ZWEITE UNSTIMMIGKEIT DURCH (2.188-inkonsistenz): "
               "`turnover`s Urteil lautet woertlich 'Wirkung +0,0639 "
               "ueber der Trennschaerfe 0,0500 R, aber ...'. Die "
               "TRENNSCHAERFE wurde gegen NULL bestimmt, das URTEIL "
               "faellt gegen null_oben = 0,0220. Beide Massstaebe in "
               "EINEM Satz, und sie widersprechen sich", "gilt",
               "n83_frei_beide_nullregeln.py",
               basis="Messbasis 08.09.2026, Menge `frei`"),
    Befundlage("2.192", "⚠️ DER STAND DER DREI LIVE GEMESSENEN BEITRAEGE "
               "unter der stabilen Nullregel: `schnitt` traegt als "
               "BEITRAG (10 % und 20 %, Abstand bis +0,0569) · `funding` "
               "traegt als MARKT-Aussage (frei, +0,0044) · `turnover` "
               "traegt NIRGENDS mehr. ⚠️ Die Nullregel ist NICHT "
               "umgestellt - sie ist nur als Parameter verfuegbar, "
               "Vorgabe unveraendert. Das ist eine Nutzerentscheidung",
               "gilt", "N-82 / N-83 / Nutzervorlage 08.09.",
               basis="Messbasis 08.09.2026, 536 Krypto-Reihen, H20"),
    Befundlage("2.193", "⚠️ ORDNUNGSFEHLER IN `messnorm.urteil`: die "
               "Abfrage `if self.trennschaerfe is None -> KEIN BEFUND` "
               "steht VOR `if self.traegt -> TRAEGT`. Ein echtes TRAEGT "
               "wird dadurch verdeckt. `Befund.traegt` selbst bleibt "
               "korrekt - nur der ausgegebene Satz widerspricht ihm",
               "gilt", "n84_trennschaerfe_massstab.py",
               basis="Messbasis 08.09.2026, Codelesung messnorm.py"),
    Befundlage("2.194", "⚠️⚠️ DIE LEITER DER GEPFLANZTEN STAERKEN ENDET ZU "
               "FRUEH: (0,02 · 0,05 · 0,10), waehrend `schnitt` bei 20 % "
               "eine Wirkung von +0,1858 hat - fast doppelt so viel wie "
               "die groesste Stufe. 'Untermaechtig' war eine Aussage "
               "ueber die LEITER, nicht ueber die Anlage", "gilt",
               "n85_leiter_zu_kurz.py",
               basis="Messbasis 08.09.2026, 536 Krypto-Reihen, H20"),
    Befundlage("2.194-bestand", "⚠️ Und der eigene Werkzeugkasten "
               "widerspricht sich hier: `messnorm_rand.py` benutzt seit "
               "jeher die laengere Leiter (0,02 · 0,05 · 0,10 · 0,20), "
               "`messnorm.py` und `messnorm_auswahl.py` die kurze",
               "gilt", "Codelesung 08.09.2026"),
    Befundlage("2.194-probe", "✔ DIE LANGE LEITER IST KEIN FREIBRIEF - das "
               "war die vorab benannte Probe. Sie holt `schnitt` 10 % und "
               "20 % von KEIN BEFUND auf TRAEGT zurueck, rettet aber "
               "`turnover` und `funding`-50 % NICHT: dort bleibt es bei "
               "'traegt nicht bis 0,20/0,40 R'. Und `zufall` traegt unter "
               "keiner Leiter", "gilt", "n85_leiter_zu_kurz.py",
               basis="Messbasis 08.09.2026, 536 Krypto-Reihen, H20"),
    Befundlage("2.195", "⚠️ `traegt` hat sich unter KEINER der drei "
               "Aenderungen geaendert (Nullregel ausgenommen): weder die "
               "gleichgezogene Trennschaerfe noch die laengere Leiter "
               "beruehren es. Beide aendern nur die BEGRUENDUNG - was "
               "genau der Zweck der vier Urteile ist", "gilt",
               "n84 + n85", basis="Messbasis 08.09.2026"),
    Befundlage("2.196", "⚠️ TURNOVER IST NICHT WIDERLEGT, SONDERN "
               "UNENTSCHIEDEN: mit langer Leiter lautet sein Urteil "
               "'traegt nicht bis 0,20 R' auf `frei` und 'bis 0,40 R' bei "
               "50 %. Ausgeschlossen sind also nur Effekte ab 0,20 R - "
               "seine gemessene Wirkung betraegt +0,0639. Ueber DIESE "
               "Groesse sagt die Anlage nichts", "gilt",
               "n85_leiter_zu_kurz.py",
               basis="Messbasis 08.09.2026, Menge `frei`, 124.221 Anker"),
    Befundlage("2.197", "✔✔ `funding` AUF `frei` IST DER ROBUSTESTE "
               "BEFUND: er traegt unter beiden Nullregeln, unter beiden "
               "Trennschaerfe-Massstaeben und unter beiden Leitern - "
               "einziger Fall, der ALLE vier Varianten uebersteht, mit "
               "einer Trennschaerfe von 0,10 statt 0,40", "gilt",
               "n83 + n84 + n85",
               basis="Messbasis 08.09.2026, Menge `frei`, 353.892 Anker"),
    Befundlage("2.198", "⚠️ OFFEN UND NICHT VERFOLGT: die "
               "Positivkontrolle pflanzt in die GEMISCHTE Welt, deren "
               "Band breiter sein kann als das der echten. Dann "
               "ueberschaetzt die Trennschaerfe systematisch, was noetig "
               "waere - `schnitt` traegt mit Wirkung +0,186 bei "
               "ausgewiesener Trennschaerfe 0,40. Dritter Punkt derselben "
               "Anlage, bewusst nicht im selben Zug geaendert", "gilt",
               "n85_leiter_zu_kurz.py",
               basis="Messbasis 08.09.2026"),
    Befundlage("2.199", "✔ DER MESSSTANDARD IST GESETZT (08.09.2026, "
               "Nutzerentscheidung): NULL_ZIEHUNGEN=40 · "
               "NULL_PERZENTIL=90 · TRENNSCHAERFE_GEGEN_NULLPUNKT=True · "
               "STAERKEN bis 0,40. Benannt in `messnorm`, von "
               "`messnorm_auswahl` und `messnorm_rand` von DORT bezogen, "
               "in Klartext ausgebbar (`standardzeile`)", "gilt",
               "messnorm.py / Methodik 2.188",
               basis="Messbasis 08.09.2026, 536 Krypto-Reihen"),
    Befundlage("2.199-abnahme", "✔ UND ER WURDE ABGENOMMEN, BEVOR ER "
               "STANDARD WURDE: erst neutral parametrisiert und Ziffer "
               "fuer Ziffer gegen die Vorgaengerfassung geprueft · dann "
               "beide Regeln nebeneinander (N-82: `zufall` unter keiner "
               "tragend, 14 von 16 Urteilen unveraendert) · dann R-R11 "
               "auf der Originalbasis (N-83) · dann die vorab benannte "
               "Probe gegen Gefaelligkeit (N-85)", "gilt",
               "N-81 bis N-85 / Methodik 2.188",
               basis="Messbasis 08.09.2026, 536 Krypto-Reihen"),
    Befundlage("2.199-waechter", "✔ Das Pruefpaket `Messstandard` "
               "bewacht ihn mit zehn Pruefungen - nicht die WERTE (die "
               "duerfen sich begruendet aendern), sondern dass sie "
               "benannt, an EINER Stelle und ueberall gleich sind. Alle "
               "zehn sind durch MUTATION belegt: Fehler zurueckgebaut, "
               "Waechter feuert", "gilt", "pruefe_pakete.py --paket "
               "Messstandard"),
    Befundlage("2.199-rand", "⚠️ DABEI KAM EIN VIERTES BETROFFENES MODUL "
               "HERAUS: `messnorm_rand.py` hatte ALLE DREI Fehler, und "
               "zwar in BEIDEN Messfunktionen. Es gehoert zur Normfamilie "
               "und war bis dahin nie mitbetrachtet worden - genau die "
               "Uneinheitlichkeit, die 2.194 aufgedeckt hat", "gilt",
               "Codelesung 08.09.2026"),
    Befundlage("2.199-offen", "⚠️⚠️ WAS DER STANDARD NICHT LEISTET: er "
               "macht die Urteile WIDERSPRUCHSFREI, nicht SCHAERFER. "
               "Offen bleiben 2.198 (Positivkontrolle pflanzt in die "
               "gemischte Welt), `ZIEHUNGEN`=5 in der Positivkontrolle, "
               "ob p90 zum Vertrauensniveau des Bandes passt - und vor "
               "allem der SELBSTTEST der ganzen Anlage gegen bekannte "
               "Wahrheit (Fehlalarm- UND Fundquote). 'Die Basis steht' "
               "waere eine Behauptung, kein Befund", "gilt",
               "Methodik 2.188 / Expertenurteil 08.09."),
    Befundlage("2.200", "⚠️⚠️ R-R9 GREIFT: die Beitragslage hat sich "
               "geaendert, also ist eine Neukalibrierung faellig. Live "
               "registriert sind `funding` (Markt-Rang - haelt), "
               "`turnover` (Markt-Rang - jetzt unentschieden) und "
               "`schnitt` (haelt, und traegt jetzt auf ZWEI Mengen statt "
               "einer). ⚠️ `turnover`s Stufen (3,15/0,83/0,22/-1,79/-2,4) "
               "stehen auf einer Basis, die keinen tragenden Befund mehr "
               "liefert", "gilt", "agent/wahrscheinlichkeit.BEITRAEGE",
               basis="Messbasis 08.09.2026, Stand nach N-85"),
    Befundlage("2.200-nicht-abraeumen", "⚠️ ABER `turnover` WIRD NICHT "
               "ABGERAEUMT. Sein Urteil lautet 'traegt nicht bis 0,20 R' "
               "- ausgeschlossen sind nur Effekte ab 0,20 R, seine "
               "Wirkung betraegt +0,0639. Ueber DIESE Groesse sagt die "
               "Anlage nichts. Nutzervorgabe, stehend: 'bevor eine "
               "Bewertung faellt muessen wir alles unternehmen'. Das "
               "verlangt eine bessere Messung, keine Abwertung", "gilt",
               "Nutzervorgabe / Befund 2.196",
               basis="Messbasis 08.09.2026, Menge `frei`"),
    Befundlage("2.201", "⚠️⚠️⚠️ FEHLER 5 - TRENNSCHAERFE UND WIRKUNG "
               "STANDEN AUF ZWEI SKALEN, und `messnorm.urteil` verglich "
               "sie miteinander. `trennschaerfe` war die GEPFLANZTE "
               "Staerke, `wirkung` die GEMESSENE Groesse. Der Faktor ist "
               "(1 - GRENZE) = 20 %: gesenkt werden die oberen 20 %, "
               "`median(alle)` verschiebt sich nur um diesen Anteil, "
               "`median(frei)` gar nicht", "gilt",
               "selbsttest_welt.py + Nachmessung 08.09.",
               basis="Theorie + Kunstwelt + Messbasis 08.09.2026"),
    Befundlage("2.201-beleg", "✔ DREIFACH BELEGT: aus der Definition "
               "hergeleitet (20 %) · in der Kunstwelt gemessen (17,8 / "
               "18,7 / 19,3 / 19,7 / 19,5 % ueber fuenf Staerken) · an "
               "den ECHTEN Daten nach Abzug des Grundpegels (+0,0145) "
               "gemessen: 20,3 / 20,1 / 19,6 / 19,2 % fuer s = 0,05 / "
               "0,10 / 0,20 / 0,40", "gilt",
               "Nachmessung 08.09.2026",
               basis="Messbasis 08.09.2026, Menge 20 %, `zufall`-Welt"),
    Befundlage("2.201-loest-2198", "✔✔ UND ES LOEST BEFUND 2.198 AUF: "
               "`schnitt` traegt mit Wirkung +0,186 bei ausgewiesener "
               "Trennschaerfe 0,40 - das sah nach Widerspruch aus. Auf "
               "der gemessenen Skala betraegt die Trennschaerfe 0,0944, "
               "und 0,186 liegt klar darueber. KEIN Widerspruch. Die "
               "Vermutung 'die Positivkontrolle pflanzt in die gemischte "
               "Welt und ueberschaetzt' war die falsche Spur",
               "gilt", "Nachmessung 08.09.2026",
               basis="Messbasis 08.09.2026, 536 Krypto-Reihen"),
    Befundlage("2.201-turnover", "⚠️⚠️ UND ES AENDERT `turnover`s "
               "URTEILSKATEGORIE: Wirkung +0,0639 gegen die gemessene "
               "Trennschaerfe 0,0456 - die Wirkung liegt UEBER der "
               "Aufloesung, das Band schliesst die Null aber ein. Das "
               "Urteil lautet jetzt NICHT TRENNBAR statt 'traegt nicht "
               "bis 0,20 R'. Er ist unentschieden, und die Anlage sagt "
               "das jetzt auch", "gilt", "Nachmessung 08.09.2026",
               basis="Messbasis 08.09.2026, Menge `frei`, 124.221 Anker"),
    Befundlage("2.201-satz-war-falsch", "⚠️ Der Satz 'Effekte ab dieser "
               "Groesse sind ausgeschlossen' war damit um Faktor 5 zu "
               "schwach. Ausgeschlossen waren nie Effekte ab 0,20 R, "
               "sondern ab rund 0,046 R. Jede so begruendete Ablehnung "
               "war zu nachsichtig formuliert", "gilt",
               "messnorm.Befund.urteil"),
    Befundlage("2.201-rand-hatte-recht", "⚠️ ZUM DRITTEN MAL AN EINEM "
               "TAG: `messnorm_rand.py` trennte beide Skalen SEIT JEHER "
               "richtig (`trennschaerfe = mean(werte)`, "
               "`trennschaerfe_in_r = s`) - `messnorm` und "
               "`messnorm_auswahl` nicht. Erst war es die Leiter (2.194), "
               "dann die Nullregel, jetzt die Skala. Das Modul war nie "
               "Teil der Normbetrachtung", "gilt",
               "Codelesung 08.09.2026"),
    Befundlage("2.202", "⚠️ DER PRUEFSTAND FUER DEN SELBSTTEST STEHT und "
               "hat seinen Vorabtest bestanden: die Nullwelt ist leer "
               "(Mittel -0,0011 bei Streuung 0,0019) · die wahre Wirkung "
               "je Staerke ist nachgemessen statt angenommen · die "
               "Autokorrelation auf Blocklaenge ist mit der echten "
               "vergleichbar (+0,032 gegen -0,004, Grenze 0,15)",
               "gilt", "selbsttest_welt.py",
               basis="Kunstwelten, 1500 Tage x 150 Werte"),
    Befundlage("2.202-nicht-pflanze", "⚠️⚠️ ENTWURFSREGEL DES "
               "PRUEFSTANDES: er benutzt `pflanze` NICHT. Die Welten "
               "werden von Grund auf mit der Beziehung gebaut, sonst "
               "pruefte der Test den Mechanismus mit sich selbst - und "
               "genau dieser Mechanismus stand unter Verdacht. Der "
               "Tagesschock ist AR(1), weil unabhaengige Tage keine "
               "Bloecke braeuchten und die Fehlalarmquote schmeichelhaft "
               "ausfiele", "gilt", "selbsttest_welt.py"),
    Befundlage("2.203", "⚠️⚠️ DIE LEHRE AUS DREI FEHLERN AN EINEM TAG: "
               "`messnorm_rand.py` hatte jedes Mal recht, weil es aus der "
               "Normbetrachtung ausgeklammert war. Daraus die Frage, die "
               "vor jeder Normaenderung zu stellen ist: WER GEHOERT NOCH "
               "ZUR FAMILIE? Nachgesehen: die Normfamilie ist "
               "`messnorm` + `messnorm_auswahl` + `messnorm_rand` - alle "
               "drei sind jetzt gleichgezogen", "gilt",
               "Codedurchsicht 08.09.2026"),
    Befundlage("2.203-altbestand", "⚠️⚠️ ABER DREI ALTBESTANDSWERKZEUGE "
               "bauen eigene Kontrollen: `messe_beitragssumme.py` "
               "(mittelt ueber Ziehungen und weist die Streuung aus - "
               "sauber), `n19e_neukalibrierung.py` und "
               "`messe_volumenanteil.py`", "gilt",
               "Codedurchsicht 08.09.2026"),
    Befundlage("2.203-volumenanteil", "⚠️⚠️⚠️ `messe_volumenanteil.py` "
               "faehrt seine Negativkontrolle mit EINER EINZIGEN Ziehung "
               "(`mische=rng`, kein Wiederholen, keine Mehrheitsregel), "
               "Positivkontrolle nur bis 0,05. Das verletzt die eigene "
               "stehende Vorgabe 'eine Ziehung ist kein Nullpunkt' direkt "
               "- und aus diesem Werkzeug stammt der registrierte Befund "
               "N-13-1' 'der Volumenanteil traegt'. ⚠️ NICHT nachgemessen "
               "(08.09.), nur festgestellt - der Befund steht damit unter "
               "Vorbehalt, ist aber NICHT widerlegt", "gilt",
               "Codedurchsicht 08.09.2026",
               basis="Codelesung, keine Nachmessung"),
    Befundlage("2.204", "✔✔✔ DER SELBSTTEST DER MESSANLAGE GEGEN "
               "BEKANNTE WAHRHEIT IST GELAUFEN - zum ersten Mal. 50 "
               "Nullwelten und 120 Welten mit bekanntem Effekt, gebaut "
               "OHNE `pflanze`, mit AR(1)-Tagesschock und der echten "
               "Streuung der Messbasis (IQA 3,073)", "gilt",
               "selbsttest_messanlage.py / selbsttest_welt.py",
               basis="182 Kunstwelten, 1500 Tage x 150 Werte, H20, 20 %"),
    Befundlage("2.204-fehlalarm", "✔ FEHLALARMQUOTE: 0 von 50 Nullwelten. "
               "Sollwert war <= 2,5 % (das Band ist ein 95-%-Band). ⚠️ "
               "0/50 schliesst eine wahre Quote bis rund 6 % NICHT aus "
               "(Dreierregel) - 'nicht hoch' ist belegt, 'exakt null' "
               "nicht", "gilt", "selbsttest_messanlage.py",
               basis="50 Kunstwelten ohne Effekt"),
    Befundlage("2.204-aufloesung", "✔ DIE AUFLOESUNG BETRAEGT +0,0293 R "
               "(80-%-Fundquote). Die Uebergangszone ist schmal: "
               "+0,0104 -> 0 % · +0,0195 -> 30 % · +0,0293 -> 95 % · "
               "+0,0363 -> 100 %. Von blind zu sicher in 0,01 R - kein "
               "Graubereich", "gilt", "selbsttest_messanlage.py",
               basis="120 Kunstwelten, sechs Effektstufen"),
    Befundlage("2.204-behauptung", "✔✔ UND DIE ANLAGE SAGT DIE WAHRHEIT "
               "UEBER SICH SELBST: sie weist eine Trennschaerfe von "
               "+0,0389 aus und findet tatsaechlich ab +0,0293 - sie ist "
               "also 25 % BESSER als versprochen, nicht schlechter. "
               "Nullbefunde sind damit staerker, als die Anlage selbst "
               "ausweist", "gilt", "selbsttest_messanlage.py",
               basis="12 Kunstwelten mit voller Leiter"),
    Befundlage("2.204-bestaetigt-2201", "✔✔ DAMIT IST DIE "
               "SKALENKORREKTUR (2.201) UNABHAENGIG BESTAETIGT: vor ihr "
               "haette die Anlage 'Trennschaerfe 0,20' behauptet bei "
               "einer echten Aufloesung von 0,029 - Faktor 7 daneben. "
               "Nach ihr stimmen Behauptung und Wirklichkeit auf 25 % "
               "ueberein", "gilt", "selbsttest_messanlage.py",
               basis="182 Kunstwelten"),
    Befundlage("2.205", "⚠️⚠️ WAS DER SELBSTTEST UEBER `turnover` SAGT: "
               "seine Wirkung (+0,0639) liegt beim 2,2-fachen der "
               "Aufloesung (0,0293) - sie ist NICHT zu klein zum Sehen. "
               "Dass das Band den Nullpunkt trotzdem einschliesst, heisst "
               "die Wirkung ist ueber die BLOECKE instabil. Das ist ein "
               "anderer Befund als 'zu schwach' - und er sagt, wo "
               "nachzusehen waere", "gilt", "selbsttest_messanlage.py",
               basis="Vergleich Kunstwelt-Aufloesung gegen Messbasis"),
    Befundlage("2.205-einschraenkung", "⚠️ EINSCHRAENKUNG, DIE DAZUGEHOERT: "
               "die Kunstwelt hat 150 Symbole x 1500 Tage, `turnover` auf "
               "`frei` nur 66 Symbole. Die Aufloesungszahl ist deshalb "
               "NICHT eins zu eins uebertragbar - der Vergleich ist ein "
               "Hinweis, kein Beweis", "gilt", "selbsttest_messanlage.py"),
    Befundlage("2.206", "⚠️⚠️ EINE LUECKE IM EIGENEN PRUEFSTAND, VOR DEM "
               "ERGEBNIS GEFUNDEN: er zog die Kennzahl jeden Tag neu "
               "(Autokorrelation 0). An den echten Daten gemessen: "
               "`zufall` -0,001 · `funding` +0,608 · `schnitt` +0,985. "
               "Bei `schnitt` stehen an fast allen Tagen DIESELBEN "
               "Symbole in der gesperrten Gruppe - ein Pruefstand ohne "
               "Beharrlichkeit sagt ueber die beiden TRAGENDEN Beitraege "
               "nichts", "gilt", "selbsttest_welt.py",
               basis="536 Krypto-Symbole mit >= 200 Tagen"),
    Befundlage("2.206-gebaut", "✔ Die Achse ist eingebaut und geprueft: "
               "AR(1) je Symbol, eingestellt 0,000/0,610/0,985 -> "
               "gemessen -0,007/0,601/0,978. Die Vorgabe bleibt 0, damit "
               "die schon gemessenen Zahlen reproduzierbar bleiben",
               "gilt", "selbsttest_welt.py"),
    Befundlage("2.207", "✔✔✔ DIE BEHARRLICHKEIT AENDERT NICHTS: 0 "
               "Fehlalarme in 50 Nullwelten bei AK 0,610 (funding-artig) "
               "UND 0 in 50 bei AK 0,985 (schnitt-artig). Auch die "
               "Streuung der Nullwelten bleibt praktisch gleich (0,0047 / "
               "0,0042 gegen 0,0047 ohne Beharrlichkeit). Die "
               "Blockbootstrap faengt sie ab", "gilt",
               "selbsttest_messanlage.py --ak",
               basis="2 x 50 Kunstwelten, 1500 Tage x 150 Werte"),
    Befundlage("2.207-schaerfer", "✔✔ DAMIT WIRD DIE AUSSAGE SCHAERFER: "
               "0 Fehlalarme in 150 Nullwelten ueber DREI "
               "Beharrlichkeitsstufen. Obere 95-%-Schranke nach der "
               "Dreierregel: 2 % - unterhalb des nominalen Sollwerts von "
               "2,5 %. Das ist der erste belastbare Nachweis, dass die "
               "Anlage nicht ins Leere feuert", "gilt",
               "selbsttest_messanlage.py",
               basis="150 Kunstwelten ohne Effekt, drei AK-Stufen"),
    Befundlage("2.207-vermutung-falsch", "⚠️ UND EINE EIGENE VERMUTUNG "
               "WAR FALSCH: ich hatte erwartet, die Beharrlichkeit werde "
               "die Fehlalarmquote treiben, weil sie weniger unabhaengige "
               "Beobachtungen bedeutet. Sie tut es nicht. Die Sorge war "
               "berechtigt, das Nachmessen richtig - das Ergebnis "
               "entlastet", "gilt", "selbsttest_messanlage.py --ak"),
    Befundlage("2.208", "✔ R-R9 IM ENGEREN SINN IST ERFUELLT: die "
               "Beitragslage im Code ist unveraendert (funding + "
               "turnover), der Fingerabdruck `KALIBRIERT_FUER` stimmt mit "
               "`BEITRAEGE` ueberein, und die Kalibrierung reproduziert "
               "auf der HEUTIGEN Messbasis praktisch ziffergenau: 0,080 "
               "-> 16,5 % Durchlass (31.08. ebenso), Gewinn +0,1316 gegen "
               "+0,1324. Basis von 123.465 auf 124.221 Anker gewachsen",
               "gilt", "messe_schwelle_kalibrierung.py",
               basis="Messbasis 08.09.2026, 124.221 Anker, 2.744 Tage"),
    Befundlage("2.208-schnitt", "⚠️⚠️ DABEI KAM HERAUS, DASS `schnitt` "
               "NIE WIEDER AUFGENOMMEN WURDE: seine Ruecknahme vom 31.08. "
               "ist seit dem 07.09. als ABGELOEST verzeichnet (2.153, "
               "kontaminierte Basis - 1.314 Symbole statt Krypto allein), "
               "aber im Code steht er weiter auf `zustand=null, "
               "stufen=None`. Die Ruecknahme ist gefallen, die "
               "Konsequenz daraus nie gezogen", "gilt",
               "agent/wahrscheinlichkeit.BEITRAEGE / REGISTER_Kandidaten"),
    Befundlage("2.208-n86", "✔ N-86 bestaetigt das unabhaengig mit einem "
               "ANDEREN Werkzeug: `schnitt` auf `frei` bei H5 +0,0094 "
               "gegen +0,0092 der 07.09.-Reproduktion. Und auf der "
               "20-%-Menge traegt er bei FUENF von sechs Horizonten, mit "
               "monoton wachsender Wirkung (+0,0130 H1 -> +0,0418 H5 -> "
               "+0,1858 H20). Die Ausnahme H10 ist eine Enthaltung, kein "
               "Widerspruch", "gilt", "n86_rr9_schnitt_ueber_horizonte.py",
               basis="Messbasis 08.09.2026, sechs Horizonte, vier Mengen"),
    Befundlage("2.208-aber", "⚠️ ABER `schnitt` KANN TROTZDEM KEIN REGLER "
               "SEIN: 2.158 gilt unveraendert - die fuenf Stufen sind ein "
               "BUCKEL (+4,07/+5,55/+9,49/+1,71/-4,65, Hochpunkt bei "
               "Fuenftel 2), zweimal gemessen. Die Vorabfestlegung "
               "verlangt Monotonie. Es gibt also gar keinen "
               "Beitragswechsel, fuer den zu kalibrieren waere - der "
               "Registerstand 'offen, nicht live' ist richtig", "gilt",
               "Befund 2.158 / REGISTER_Kandidaten"),
    Befundlage("2.209", "⚠️⚠️ EIGENE KORREKTUR: ich habe `turnover` heute "
               "auf der VOLLEN Historie gemessen und daraus 'nicht "
               "trennbar' geschlossen. Seine registrierte Basis ist aber "
               "50 % AB 2022 (2.162). Das war derselbe R-R11-Verstoss, "
               "den ich bei `funding` am selben Tag noch vermieden hatte",
               "gilt", "n87_rr11_auf_der_eigenen_basis.py"),
    Befundlage("2.209-reproduziert", "✔ AUF DER EIGENEN BASIS "
               "REPRODUZIEREN DIE WIRKUNGEN FAST ZIFFERGENAU: turnover "
               "+0,0608 gegen Anker +0,0598 · oi_aenderung +0,0442 gegen "
               "+0,0446 · funding +0,0542 gegen +0,0607. Was sich "
               "geaendert hat, ist NICHT der Effekt, sondern das "
               "KRITERIUM", "gilt", "n87_rr11_auf_der_eigenen_basis.py",
               basis="Messbasis 08.09.2026, je eigene Menge, ab 2022"),
    Befundlage("2.210", "⚠️⚠️⚠️ FEHLER 6 - DAS KRITERIUM ZAEHLT DIE "
               "UNSICHERHEIT DOPPELT. `traegt = unten > null_oben` "
               "verlangt, dass die UNTERE Vertrauensgrenze des Effekts "
               "die OBERE der Nullwelt ueberschreitet - also zwei "
               "95-%-Baender, die sich nicht ueberlappen. Das entspricht "
               "etwa p < 0,005, nicht p < 0,05", "gilt",
               "Nullpunkt-Zerlegung 08.09.2026",
               basis="Messbasis 08.09.2026, vier Kandidaten ab 2022"),
    Befundlage("2.210-beleg", "✔ DER BELEG: der Nullpunkt hat kaum "
               "VERSATZ, aber ein breites BAND. null MITTEL +0,0068 "
               "(turnover) / +0,0106 (funding) / +0,0172 (oi_aenderung) / "
               "+0,0081 (zufall) - null_oben dagegen +0,0592 / +0,0414 / "
               "+0,0495 / +0,0397. `null_oben` ist also im Wesentlichen "
               "die obere Vertrauensgrenze EINER Nullwelt, ein Streumass "
               "- und die Streuung steckt im Band schon drin", "gilt",
               "Nullpunkt-Zerlegung 08.09.2026",
               basis="Messbasis 08.09.2026, Fenster ab 2022"),
    Befundlage("2.210-erklaert", "✔✔ UND ES ERKLAERT ZWEI BISHER "
               "UNVERBUNDENE BEOBACHTUNGEN: warum der Selbsttest 0 "
               "Fehlalarme in 150 Welten fand (nominal 2,5 % erlaubt - "
               "die Anlage ist uebervorsichtig), und warum das dort kaum "
               "auffiel: in der Kunstwelt (150 Symbole, 1500 Tage) sind "
               "die Baender ENG, die Doppelzaehlung faellt kaum ins "
               "Gewicht. Auf den echten schmalen Basen (turnover: 66 "
               "Symbole) sind sie BREIT - dort dominiert sie", "gilt",
               "selbsttest_messanlage.py + Nullpunkt-Zerlegung"),
    Befundlage("2.210-nicht-geaendert", "⚠️⚠️ NICHTS DAVON WURDE "
               "GEAENDERT. Den Standard zu lockern, weil er den eigenen "
               "Beitraegen im Weg steht, waere motiviertes Rechnen. Der "
               "saubere Weg ist der, fuer den der Pruefstand gebaut "
               "wurde: die Alternative auf Fehlalarm- UND Fundquote "
               "messen, BEVOR sie gewaehlt wird", "gilt",
               "Nutzervorgabe 08.09. / selbsttest_messanlage.py"),
    Befundlage("2.211", "⚠️ EINE LUECKE IM KALIBRIERUNGSWERKZEUG, "
               "beilaeufig gefunden: `messe_schwelle_kalibrierung.py` "
               "liest die Stufen zwar aus der LIVE-Registrierung (keine "
               "Kopie), aber nur fuer die zwei fest verdrahteten Merkmale "
               "`funding_fuenftel` und `turnover_fuenftel`. Ein DRITTER "
               "Beitrag wuerde still ignoriert - und die Kalibrierung "
               "waere falsch, ohne dass es auffaellt", "gilt",
               "messe_schwelle_kalibrierung.py"),
    Befundlage("2.212", "⚠️⚠️⚠️ EINSCHRAENKUNG DES SELBSTTESTS VOM "
               "08.09.: die Kunstwelt ist SECHSMAL PRAEZISER als die "
               "Wirklichkeit. Bandbreite 0,018 gegen 0,108 beim echten "
               "`turnover` auf 50 % ab 2022. Die dort gemessene "
               "Aufloesung von +0,0293 R und die 0 Fehlalarme gelten "
               "damit fuer eine Welt, die deutlich leichter ist als die "
               "echte", "gilt", "selbsttest_kriterien.py / Nachmessung "
               "09.09.", basis="Kunstwelt gegen Messbasis 08.09.2026"),
    Befundlage("2.212-diagnose", "⚠️ DIE URSACHE LIEGT IN DER TAGESREIHE, "
               "aus der das Band entsteht: echt 1.692 Tage mit SD 0,3307 "
               "und Autokorrelation +0,602 (SD je Block 0,1473) - "
               "kuenstlich SD 0,1500, AK1 +0,197, SD je Block 0,0315. Die "
               "echte Reihe ist doppelt so streuend UND dreimal so "
               "traege", "gilt", "Nachmessung 09.09.2026",
               basis="turnover 50 % ab 2022 gegen Kunstwelt 66x1700"),
    Befundlage("2.212-drei-versuche", "⚠️ DREI ERKLAERUNGSVERSUCHE, ALLE "
               "UNZUREICHEND: Schwankung des Effekts ueber die Tage "
               "(selbst beim Fuenffachen nur 0,031) · Ueberlappung der "
               "Zielgroesse (H20 teilt 19 von 20 Tagen - brachte nichts, "
               "0,015) · Beharrlichkeit der Kennzahl (turnover +0,669 "
               "gemessen). Alle drei zusammen: 0,029 gegen echte 0,108",
               "gilt", "Nachmessung 09.09.2026"),
    Befundlage("2.212-abgebrochen", "⚠️⚠️ UND DANN ABGEBROCHEN, statt "
               "weiterzukalibrieren: eine Kunstwelt so lange anzupassen, "
               "bis sie passt, ist Probieren - und hinterher nicht mehr "
               "auseinanderzuhalten. Die drei Achsen bleiben im Werkzeug "
               "(`staerke_streuung`, `ueberlappung`, `kennzahl_ak`), alle "
               "mit Vorgabe 0, damit die Zahlen vom 08.09. reproduzierbar "
               "bleiben", "gilt", "selbsttest_welt.py"),
    Befundlage("2.213", "✔✔ DER BESSERE PRUEFSTAND SIND DIE ECHTEN DATEN "
               "SELBST: eine NULLWELT entsteht durch Mischen der Raenge "
               "je Kalendertag. Sie hat die echte Streuung, die echte "
               "Traegheit und die echte Symbolzahl von selbst, ohne jede "
               "Kalibrierung - und enthaelt per Konstruktion keinen "
               "Zusammenhang. Jedes 'traegt' darauf ist ein Fehlalarm",
               "gilt", "selbsttest_kriterien_echt.py"),
    Befundlage("2.213-erste-zahlen", "⚠️ UND DER KURZLAUF ZEIGT SOFORT, "
               "was die Kunstwelt NIE gezeigt haette (dort 0 % Fehlalarm "
               "fuer alle drei): auf `turnover` findet Kriterium A eine "
               "Wirkung von +0,0457 in KEINEM Fall, B und C in allen - "
               "und auf `funding` erzeugen B und C in 1 von 4 Nullwelten "
               "einen Fehlalarm. ⚠️ Acht Welten sind keine Aussage, aber "
               "der Aufbau trennt", "gilt",
               "selbsttest_kriterien_echt.py --klein",
               basis="8 Nullwelten, 18 gepflanzte - KURZLAUF"),
    Befundlage("2.213-versatz", "⚠️ Und er zeigt den Versatz: die Nullwelt "
               "auf `funding` 10 % hat eine Wirkung von +0,0164 - in "
               "einer Welt OHNE jeden Zusammenhang. Genau diesen Versatz "
               "korrigiert `nullpunkt`, und genau deshalb ist 'Band ohne "
               "Null' (Kriterium C) zu wenig", "gilt",
               "selbsttest_kriterien_echt.py --klein"),
    Befundlage("2.214", "✔✔✔ DIE DREI KRITERIEN SIND GEGEN BEKANNTE "
               "WAHRHEIT GEMESSEN - auf ECHTEN Daten, Nullwelten durch "
               "Mischen der Raenge (100 Nullwelten, 36 gepflanzte, zwei "
               "Basen). Sollwert 2,5 % Fehlalarme, weil das Band ein "
               "95-%-Band ist", "gilt",
               "selbsttest_kriterien_echt.py",
               basis="turnover 50 % + funding 10 %, je ab 2022"),
    Befundlage("2.214-c", "⚠️⚠️⚠️ KRITERIUM C IST WIDERLEGT: `unten > 0` "
               "liefert 22 von 100 Fehlalarmen (22,0 % ± 4,1) gegen einen "
               "Sollwert von 2,5 %. Fast ein Viertel der Nullwelten "
               "besteht es. ⚠️ DAS IST DAS KRITERIUM AUS BEFUND 2.162 - "
               "auf ihm wurden `turnover`, `funding` und `oi_aenderung` "
               "auf ihren eigenen Basen als tragend gefuehrt", "gilt",
               "selbsttest_kriterien_echt.py",
               basis="100 Nullwelten aus echten Daten"),
    Befundlage("2.214-a", "⚠️⚠️ KRITERIUM A IST ZU STRENG - und zwar "
               "gemessen, nicht nur hergeleitet: 0 von 100 Fehlalarmen, "
               "aber es findet eine Wirkung von +0,0448 in KEINEM "
               "einzigen von sechs Faellen und +0,0676 nur in vier von "
               "sechs. Fundquote insgesamt 58,3 %. ⚠️ `turnover`s echte "
               "Wirkung betraegt +0,0608 - sie liegt genau in dem "
               "Bereich, den A nicht sieht", "gilt",
               "selbsttest_kriterien_echt.py",
               basis="100 Nullwelten, 36 gepflanzte Welten"),
    Befundlage("2.214-b", "✔✔ KRITERIUM B TRIFFT DAS ZIEL: `unten > "
               "max(0, nullpunkt)` liefert 3 von 100 Fehlalarmen (3,0 % "
               "± 1,7) - das Vertrauensband schliesst den Sollwert 2,5 % "
               "EIN, es ist davon nicht unterscheidbar. Und die "
               "Fundquote betraegt 97,2 % (35 von 36)", "gilt",
               "selbsttest_kriterien_echt.py",
               basis="100 Nullwelten, 36 gepflanzte Welten"),
    Befundlage("2.214-warum", "✔ UND ES PASST ZUR HERLEITUNG (2.210): der "
               "Nullpunkt hat einen VERSATZ (Mittel +0,007 bis +0,017, "
               "auf `funding`s Nullwelten sogar +0,0139 Wirkung ohne "
               "jeden Zusammenhang) - den muss man abziehen, sonst ist C "
               "zu locker. Aber seine STREUUNG steckt im Band bereits - "
               "wer auch die abzieht, zaehlt doppelt und bekommt A",
               "gilt", "selbsttest_kriterien_echt.py"),
    Befundlage("2.214-vorhersage", "✔ DIE VORHERSAGE STAND VOR DEM LAUF "
               "und ist eingetroffen: 'A FA nahe 0, Fundquote bricht ein "
               "· B FA um 2,5 %, Fundquote deutlich besser · C FA "
               "deutlich ueber 2,5 %'. ⚠️ Und der Ausgang, der den "
               "heutigen Standard bestaetigt haette - B mit hoher "
               "Fehlalarmquote - war ausdruecklich benannt", "gilt",
               "selbsttest_kriterien_echt.py"),
    Befundlage("2.214-nicht-gesetzt", "⚠️⚠️ NICHTS DAVON IST GESETZT. Der "
               "Wechsel von A auf B wuerde Urteile zugunsten der eigenen "
               "Beitraege drehen - er gehoert dem Nutzer vorgelegt, wie "
               "der Messstandard am 08.09. auch", "gilt",
               "Nutzerentscheidung offen"),
    Befundlage("2.215", "✔ GEGENPRUEFUNG AUF EINER DRITTEN, "
               "UNABHAENGIGEN BASIS: `oi_aenderung` 20 % ab 2022 - andere "
               "Datenquelle (Terminmarkt statt Kursreihe), andere Menge, "
               "122 statt 64 Symbole. Fehlalarme A 0/50 · B 1/50 = 2,0 % "
               "· C 20/50 = 40,0 %. Das Ergebnis ist NICHT basisabhaengig",
               "gilt", "selbsttest_kriterien_echt.py",
               basis="50 Nullwelten aus echten Terminmarktdaten"),
    Befundlage("2.215-gesamt", "✔✔ UEBER ALLE DREI BASEN, 150 "
               "Nullwelten: A 0/150 = 0,0 % Fehlalarme bei 63 % "
               "Fundquote · B 4/150 = 2,7 % bei 98 % · C 42/150 = 28,0 % "
               "bei 100 %. Der Sollwert ist 2,5 %, weil das Band ein "
               "95-%-Band ist", "gilt", "selbsttest_kriterien_echt.py",
               basis="150 Nullwelten, 54 gepflanzte, drei echte Basen"),
    Befundlage("2.216", "✔✔✔ NUTZERENTSCHEIDUNG 09.09.2026: KRITERIUM B "
               "IST GESETZT. `messnorm.NULLBEZUG = 'nullpunkt'` - das "
               "Urteil prueft gegen den VERSATZ der Nullwelten, nicht "
               "gegen ihre STREUUNG. Alternativen bleiben waehlbar "
               "('null_oben', 'null'), damit der frueher Stand "
               "reproduzierbar bleibt", "gilt",
               "messnorm.py / Nutzerentscheidung 09.09.",
               basis="150 Nullwelten ueber drei echte Basen"),
    Befundlage("2.216-ein-bezug", "⚠️⚠️ UND URTEIL UND TRENNSCHAERFE LESEN "
               "DENSELBEN BEZUG (`messnorm._bezug`). Fehler 2 vom 08.09. "
               "war genau das Gegenteil - zwei Massstaebe in EINEM Satz. "
               "Wer sie trennt, baut ihn neu ein; deshalb gibt es die "
               "Funktion, und deshalb bewacht sie das Pruefpaket", "gilt",
               "messnorm._bezug / pruefe_pakete --paket Messstandard"),
    Befundlage("2.216-reproduziert", "✔ DIE UMSTELLUNG IST SAUBER "
               "GEKAPSELT: mit `NULLBEZUG='null_oben'` reproduzieren ALLE "
               "ACHT Pruefpunkte den Stand vom 08.09. ziffergenau "
               "(schnitt 20 %, funding frei/10 %, turnover frei/50 %, "
               "oi_aenderung 20 %, zufall frei/5 %) - Wirkung, Urteil und "
               "Trennschaerfe", "gilt", "b_abnahme, Teil 1",
               basis="Messbasis 08.09.2026"),
    Befundlage("2.217", "✔✔ DIE BEITRAGSLAGE UNTER B - und die Kontrolle "
               "haelt: `schnitt` 20 % +0,1858 TRAEGT · `funding` frei "
               "+0,0249 TRAEGT · `turnover` frei +0,0639 TRAEGT · "
               "`turnover` 50 % ab 2022 +0,0608 TRAEGT · `funding` 10 % "
               "ab 2022 +0,0542 TRAEGT · `oi_aenderung` 20 % ab 2022 "
               "+0,0442 TRAEGT. ⚠️ `zufall` traegt WEDER auf `frei` NOCH "
               "auf 5 % - B ist nicht 'alles traegt'", "gilt",
               "b_abnahme, Teil 2",
               basis="Messbasis 08.09.2026, je eigene Basis"),
    Befundlage("2.217-trennschaerfe", "✔ Und die Trennschaerfen liegen "
               "jetzt bei 0,010 bis 0,053 statt bei 0,08 bis 0,10 - in "
               "der Groessenordnung der gemessenen Aufloesung statt "
               "darueber", "gilt", "b_abnahme, Teil 2"),
    Befundlage("2.218", "⚠️⚠️ WAS DAMIT NICHT GEMESSEN IST - "
               "Nutzerhinweis 09.09., woertlich: *'wir sind noch in der "
               "Pruefung und Kalibrierung einzelner Beitraege. Die "
               "LEISTUNG DER KETTE ist hier noch nicht beruecksichtigt.'* "
               "Alles bisher Gemessene betrifft EINZELNE Beitraege auf "
               "ihrer eigenen Basis - nicht, was die Kette als Ganzes "
               "daraus macht", "gilt", "Nutzervorgabe 09.09.2026"),
    Befundlage("2.218-was-fehlt", "⚠️ Konkret ungemessen: das ZUSAMMEN"
               "WIRKEN der Beitraege in `potential.rechne` · die Wirkung "
               "der Schwelle 0,080 auf die tatsaechlich erzeugten Signale "
               "· die Trichterstufen davor (Auswahl, Sperren) · und ob "
               "die Kette am Ende besser ist als ihre Teile. Die "
               "Kalibrierung 16,5 % Durchlass sagt, wie STRENG die "
               "Schwelle ist - nicht, was dabei herauskommt", "gilt",
               "Nutzervorgabe 09.09.2026 / agent/potential.py"),
    Befundlage("2.219", "✔✔ DER GESAMTSTAND UNTER KRITERIUM B - 16 "
               "Kandidaten, alle zulaessigen selektierten Mengen, ein "
               "Lauf. ⚠️ DIE KONTROLLE HAELT: `zufall` traegt auf KEINER "
               "der drei Mengen. Fuenf tragen (funding, turnover, "
               "oi_aenderung, vola, schnitt), SIEBEN nicht (oi_je_umsatz, "
               "long_bias, top_bias, taker_bias, amihud, rsi, zufall), "
               "VIER widersprechen sich (schnitt50, momentum, "
               "momentum_kurz, funding_extrem). B laesst nicht alles "
               "durch", "gilt", "messe_alle_kandidaten.py",
               basis="Messbasis 08.09.2026, 536 Krypto-Reihen, H20"),
    Befundlage("2.219-schnitt", "✔ `schnitt` ist der ROBUSTESTE: er "
               "traegt auf ALLEN DREI Mengen (10 %, 20 %, 50 %), drei von "
               "drei Aussagen. ⚠️ Registrierbar ist er trotzdem nicht - "
               "2.158 gilt unveraendert, seine Stufen sind ein Buckel. "
               "Das ist eine Frage der FORM, nicht der Signifikanz",
               "gilt", "messe_alle_kandidaten.py / Befund 2.158"),
    Befundlage("2.219-vola", "⚠️ `vola` TRAEGT NEU - aber nur mit EINER "
               "Aussage von drei Mengen, die anderen beiden sind "
               "Enthaltungen. Unter dem alten Bezug war er WIDERSPRUCH. "
               "Eine einzelne Aussage ist duenn und keine "
               "Registrierungsgrundlage; ausserdem gilt 2.143 weiter "
               "('vola traegt KEINE Richtung')", "gilt",
               "messe_alle_kandidaten.py",
               basis="Messbasis 08.09.2026, eine von drei Mengen"),
    Befundlage("2.220", "⚠️⚠️⚠️ NOCH VOR DER ERSTEN KETTENMESSUNG "
               "GEFUNDEN, durch Nachsehen statt Annehmen: die KETTENMENGE "
               "ist keine momentum-selektierte Menge. Von 43 Krypto-"
               "Werten passieren 25 die Auswahl, WEIL SIE BESTAND HABEN - "
               "nach nichts selektiert; nur 2 kommen von A1 (top-k nach "
               "Jahresentwicklung). Die Beitraege sind aber auf den "
               "Mengen 5/10/20/50 % belegt, alle nach Momentum verengt",
               "gilt", "agent/auswahl.py / Kettenplan 09.09.",
               basis="43 Krypto-Werte im Lauf, NB-Backup 03.09."),
    Befundlage("2.220-signale", "⚠️ Und die Signalverteilung bestaetigt "
               "es: `NACHKAUFEN` mit 51,7 Mails am Tag hat per Definition "
               "Bestand - der groesste Einzelposten der Kette entsteht auf "
               "der Menge, auf der die Beitraege NIE gemessen wurden",
               "gilt", "Kettenplan 09.09. / F-172"),
    Befundlage("2.220-haltefrage", "⚠️⚠️ UND EINE ZWEITE, DARAUS "
               "FOLGENDE: `agent/auswahl.py` schreibt selbst in die Mail "
               "'bei einer gehaltenen Position lautet die Frage halten "
               "oder verkaufen'. Alle Beitraege sind fuer die Lage "
               "`instrument=spot, strategie=einstieg` gemessen. Ob sie "
               "fuer die HALTEFRAGE gelten, ist nie geprueft worden",
               "gilt", "agent/auswahl.py / agent/wahrscheinlichkeit.py"),
    Befundlage("2.220-plan", "✔ K-1 wurde daraufhin in DREI Teile "
               "zerlegt: K-1a auf der A1-Menge (dafuer sind sie gebaut) · "
               "K-1b auf der BESTANDS-Menge (dort entstehen die meisten "
               "Signale, dort nie gemessen) · K-1c fuer die Haltefrage "
               "statt den Einstieg. ⚠️ Das ist bereits ein Befund vor der "
               "Messung: die Beitraege werden auf einer Menge angewandt, "
               "auf der sie nie geprueft wurden", "gilt",
               "Kettenplan 09.09.2026"),
    Befundlage("2.221", "✔✔ K-1b GEMESSEN: tragen die Beitraege auf "
               "einer UNSELEKTIERTEN Menge? Verglichen wurde die "
               "Momentum-Auswahl gegen FUENF Zufallsauswahlen gleicher "
               "Groesse, alles andere unveraendert. ⚠️ Ein "
               "Zufallsausschnitt ist ein STELLVERTRETER - eine "
               "Bestands-Historie gibt es nicht (`holdings` 55 Zeilen "
               "ohne Zeitachse, `portfolio_wert_historie` leer)",
               "gilt", "k1b_beitrag_auf_bestandsmenge.py",
               basis="Messbasis 08.09.2026, je registrierte Menge"),
    Befundlage("2.221-turnover", "✔✔ `turnover` IST DER ROBUSTESTE: "
               "+0,0608 auf der Momentummenge -> +0,0470 auf "
               "Zufallsmengen, 5 von 5 tragen, 3,2-fach ueber der "
               "Kontrolle. Sein Beleg haengt NICHT an der Auswahl",
               "gilt", "k1b_beitrag_auf_bestandsmenge.py",
               basis="Menge 50 % ab 2022, 5 Zufallsziehungen"),
    Befundlage("2.221-funding", "✔ `funding` uebertraegt sich auch: "
               "+0,0542 -> +0,0320, 4 von 5, 2,2-fach ueber der "
               "Kontrolle. ⚠️ Aber die Wirkung faellt um ein Drittel - "
               "die Momentum-Auswahl konzentriert den Effekt, macht ihn "
               "aber nicht aus", "gilt",
               "k1b_beitrag_auf_bestandsmenge.py",
               basis="Menge 10 % ab 2022, 5 Zufallsziehungen"),
    Befundlage("2.222", "⚠️⚠️⚠️ `schnitt`s WIRKUNG IST ZU VIER FUENFTELN "
               "EIN AUSWAHL-ARTEFAKT: +0,1858 auf der Momentummenge -> "
               "+0,0366 auf Zufallsmengen, ein Faktor 5. Er traegt zwar "
               "weiter (4 von 5, 2,5-fach ueber der Kontrolle), aber die "
               "Zahl, die ihn am Vormittag als '6,3-fach ueber der "
               "Aufloesung' und 'solidesten' auswies, gilt NUR auf der "
               "momentum-verengten Menge", "gilt",
               "k1b_beitrag_auf_bestandsmenge.py",
               basis="Menge 20 %, 5 Zufallsziehungen"),
    Befundlage("2.222-passt", "✔ Und es passt zu 2.158-redundanz: "
               "`schnitt` und die Auswahl korrelieren mit Spearman +0,704 "
               "im vollen Querschnitt. Auf der momentum-verengten Menge "
               "misst `schnitt` also teilweise die AUSWAHL mit - genau "
               "der Anteil, der auf einer Zufallsmenge wegfaellt",
               "gilt", "Befund 2.158-redundanz / K-1b"),
    Befundlage("2.222-rangfolge", "⚠️⚠️ DIE RANGFOLGE DREHT SICH DAMIT "
               "UM. Auf der Menge, auf der die KETTE arbeitet, gilt: "
               "`turnover` +0,0470 (3,2x) > `schnitt` +0,0366 (2,5x) > "
               "`funding` +0,0320 (2,2x) > `oi_aenderung` +0,0267 "
               "(1,8x). Am Vormittag stand `schnitt` mit +0,186 weit "
               "vorn", "gilt", "k1b_beitrag_auf_bestandsmenge.py",
               basis="Messbasis 08.09.2026, Zufallsmengen"),
    Befundlage("2.223", "✖ ZURUECKGEZOGEN (2.225) - falsche Basis. "
               "War: `oi_aenderung` BRICHT EIN: +0,0442 -> "
               "+0,0267, nur 2 von 5 tragen, und das ist nur das "
               "1,8-fache der Kontrolle (die auf Zufallsmengen +0,0146 "
               "wirkt). Auf einer unselektierten Menge ist er vom Zufall "
               "kaum zu unterscheiden - und er laeuft LIVE als Sperre",
               "gilt", "k1b_beitrag_auf_bestandsmenge.py",
               basis="Menge 20 % ab 2022 - NICHT seine Basis"),
    Befundlage("2.224", "⚠️⚠️ EIGENER FEHLER IN DER KONTROLLREGEL, "
               "korrigiert: der erste K-1b-Lauf erklaerte sich fuer "
               "wertlos, weil `zufall` in 1 von 6 Varianten trug. Die "
               "Regel war falsch - Kriterium B HAT eine Fehlalarmquote "
               "von 2,7 %, bei sechs Ziehungen sieht man mit 15 % "
               "Wahrscheinlichkeit mindestens einen. Eine Kontrolle, die "
               "nie feuern darf, verlangt implizit 0 % - also genau das "
               "am selben Tag verworfene `null_oben`", "gilt",
               "k1b_beitrag_auf_bestandsmenge.py"),
    Befundlage("2.224-ersatz", "✔ Die Regel prueft jetzt die WIRKUNG "
               "statt der Quote: mit fuenf Ziehungen laesst sich eine "
               "Quote ohnehin nicht schaetzen. Massstab ist die Kontrolle "
               "auf DERSELBEN Art Menge (+0,0146), und der Kandidat muss "
               "sie deutlich uebertreffen", "gilt",
               "k1b_beitrag_auf_bestandsmenge.py"),
    Befundlage("2.225", "✖ ZURUECKGEZOGEN: '`oi_aenderung` bricht ein - "
               "vom Zufall kaum zu unterscheiden' (2.223). Die Aussage "
               "stand auf der Menge 20 % ab 2022. Seine "
               "REGISTRIERUNGSBASIS ist `frei` auf der vollen Historie, "
               "und dort traegt er: +0,0126 R [+0,0071 .. +0,0184], "
               "131.869 Anker, 122 Symbole", "gilt",
               "Nachmessung 09.09.2026",
               basis="Messbasis 08.09.2026, Menge `frei`, volle Historie"),
    Befundlage("2.225-reproduziert", "✔ Der registrierte Wert "
               "reproduziert im Rahmen der geaenderten Basis: +0,0145 R "
               "auf 126.491 Ankern und 117 Symbolen (02.09.) gegen "
               "+0,0126 R auf 131.869 Ankern und 122 Symbolen (heute). "
               "Die Messbasis wurde am 08.09. aufgefrischt und um zehn "
               "Reihen erweitert", "gilt", "Nachmessung 09.09.2026"),
    Befundlage("2.225-k1b-trifft-nicht", "⚠️⚠️ UND DIE K-1b-FRAGE TRIFFT "
               "IHN OHNEHIN NICHT - sie ist fuer ihn schon beantwortet. "
               "K-1b fragt 'gilt der Beleg auf einer UNSELEKTIERTEN "
               "Menge?'. Seine Registrierungsbasis IST die unselektierte "
               "Menge (`frei`). Und live wirkt er nur bei EINSTIEG, NICHT "
               "bei Bestand - die Bestandsfrage stellt sich fuer ihn gar "
               "nicht", "gilt",
               "REGISTER_Kandidaten / agent/rollen_gate.py"),
    Befundlage("2.225-dritter-fehler", "⚠️⚠️⚠️ DRITTER R-R11-FEHLER "
               "DERSELBEN KLASSE AN EINEM TAG: `turnover` auf der vollen "
               "Historie statt 50 % ab 2022 · `funding` beinahe ebenso "
               "(rechtzeitig gefangen) · `oi_aenderung` auf 20 % ab 2022 "
               "statt `frei`. Die Ursache ist immer dieselbe: ich messe "
               "mehrere Kandidaten in EINEM Lauf auf EINER Menge, statt "
               "jeden auf SEINER Basis. ⚠️ Das Kandidatenregister nennt "
               "die Basis je Kandidat - es gehoert VOR jeden Lauf "
               "geoeffnet, nicht danach", "gilt",
               "Selbstbefund 09.09.2026"),
    Befundlage("2.226", "⚠️ WAS ZU `oi_aenderung` OFFEN BLEIBT: die "
               "Wirkung ist mit +0,0126 R die KLEINSTE der vier und nah "
               "an der Aufloesung · bei 50 % ab 2022 traegt er NICHT "
               "(Band [-0,0005 .. +0,0283]) · der Geltungsbereich ist "
               "H20, der Betriebshorizont aber 3-5 Tage, und bei H5 "
               "traegt er nicht (+0,00663, 06.09.) · und er wirkt nur auf "
               "10,6 von 174,3 Signalen am Tag. Korrekt belegt, aber "
               "wenig wirksam", "gilt",
               "Nachmessung 09.09. / REGISTER_Kandidaten / F-172",
               basis="Messbasis 08.09.2026 + NB-Backup 29.08."),
    Befundlage("2.227", "⚠️⚠️⚠️ DIE URSACHE DER DREI R-R11-FEHLER IST "
               "STRUKTURELL: das Feld `Kandidat.basis` ist FREITEXT ('H20 "
               "· 2.369 Kalendertage · 290 Symbole') und nennt die MENGE "
               "nicht. Die Basis war dokumentiert, aber fuer den Code "
               "nicht benutzbar - deshalb wiederholte sich der Fehler",
               "gilt", "bestand.Kandidat / Selbstbefund 09.09."),
    Befundlage("2.227-aufloesung", "✔✔ UND DABEI KAM DIE AUFLOESUNG "
               "HERAUS: ALLE DREI live registrierten Beitraege stehen auf "
               "`frei` - dem vollen Tagesquerschnitt. 2.161-rr11 sagt es "
               "woertlich fuer `turnover` ('Der registrierte Befund "
               "stammt von der FREIEN Menge'), `oi_aenderung`s Ankerzahl "
               "bestaetigt es (126.491 ~ frei), und `funding`s "
               "Originalbefund vom 30.08. war der Querschnitt je "
               "Kalendertag", "gilt", "bestand.py / Nachmessung 09.09.",
               basis="Messbasis 08.09.2026"),
    Befundlage("2.227-nicht-2162", "⚠️⚠️ DIE MENGEN AUS BEFUND 2.162 "
               "(turnover 50 %, funding 10 %, oi_aenderung 20 %) SIND "
               "NICHT DIE REGISTRIERUNGSBASIS - sie stammen aus einer "
               "eigenen Messung zur Zeitstabilitaet. Genau diese "
               "Verwechslung hat heute N-87 auf die falsche Basis "
               "gefuehrt", "gilt", "Befund 2.162 / 2.161-rr11"),
    Befundlage("2.227-auf-frei", "✔✔ AUF IHREN ECHTEN "
               "REGISTRIERUNGSBASEN TRAGEN UNTER KRITERIUM B ALLE DREI: "
               "`funding` frei +0,0249 · `turnover` frei +0,0639 · "
               "`oi_aenderung` frei +0,0126. Das ist ein saubereres Bild "
               "als das, was N-87 auf den 2.162-Mengen zeigte", "gilt",
               "Nachmessung 09.09.2026",
               basis="Messbasis 08.09.2026, Menge `frei`, volle Historie"),
    Befundlage("2.227-gebaut", "✔ ABGESTELLT STATT VORGENOMMEN: "
               "`Kandidat` hat jetzt `menge` und `fenster` "
               "maschinenlesbar, `bestand.messbasis(name)` gibt sie "
               "heraus, und zwei Waechter im Paket `Messstandard` "
               "erzwingen sie fuer jeden TRAGENDEN Kandidaten - beide "
               "durch Mutation belegt", "gilt",
               "bestand.messbasis / pruefe_pakete --paket Messstandard"),
    Befundlage("2.228", "⚠️⚠️ EIN WIDERSPRUCH BLEIBT OFFEN und gehoert in "
               "die Kettenpruefung: die drei Beitraege sind auf `frei` "
               "registriert - das ist nach P6/F-212 die MARKT-Frage. "
               "F-212 verlangt aber, einen BEITRAG auf der SELEKTIERTEN "
               "Menge zu beurteilen. 2.161-rr11 hat das schon benannt. "
               "Solange das nicht entschieden ist, steht jeder Beitrag "
               "auf einer Basis, die eine andere Frage beantwortet als "
               "die, fuer die er benutzt wird", "gilt",
               "Befund 2.161-rr11 / F-212 / Kettenplan"),
    Befundlage("2.229", "✔✔✔ K-1w GEMESSEN - die Beitraege auf der "
               "WATCHLIST, auf der die Kette wirklich arbeitet (43 "
               "Krypto-Werte, davon 39 in der Messbasis). ⚠️ Rang ueber "
               "die MESSBASIS, gemessen auf der Watchlist - ueber die "
               "Watchlist gerangt dreht das Vorzeichen (REGISTER_"
               "Kandidaten). Dafuer bekam `sammle` den Parameter `nur`, "
               "der NACH dem Rang verengt", "gilt",
               "k1w_beitrag_auf_der_watchlist.py",
               basis="Watchlist 43 Symbole, Rang ueber 536"),
    Befundlage("2.229-funding", "✔✔ `funding` TRAEGT AUF DER WATCHLIST - "
               "und zwar STAERKER: +0,0886 gegen +0,0249 auf der "
               "Messbasis, Band [+0,0582 .. +0,1458], 34 Bloecke, "
               "Trennschaerfe 0,0775. Genug Macht, echtes Urteil",
               "gilt", "k1w_beitrag_auf_der_watchlist.py",
               basis="Watchlist, Menge frei, 40.195 Anker, 34 Bloecke"),
    Befundlage("2.229-turnover", "⚠️⚠️ `turnover` IST AUF DER WATCHLIST "
               "NICHT MESSBAR - nur 5 Bloecke gegen 20 geforderte, Urteil "
               "'KEIN BEFUND'. ⚠️ Das ist laut Norm eine Aussage ueber die "
               "MESSUNG, nicht ueber die Welt. Er deckt 66 Symbole ab, "
               "und davon liegen zu wenige in der 43er-Watchlist",
               "gilt", "k1w_beitrag_auf_der_watchlist.py",
               basis="Watchlist, 15.354 Anker, 321 Tage, 5 Bloecke"),
    Befundlage("2.229-oi", "⚠️ `oi_aenderung` IST AUF DER WATCHLIST "
               "UNENTSCHIEDEN: Wirkung +0,0146 gegen eine Trennschaerfe "
               "von 0,0473 - die Anlage kann dort Effekte dieser Groesse "
               "nicht aufloesen. 21 Bloecke, also gerade ueber der "
               "Grenze. Kein Nullbefund", "gilt",
               "k1w_beitrag_auf_der_watchlist.py",
               basis="Watchlist, 29.728 Anker, 1.319 Tage, 21 Bloecke"),
    Befundlage("2.229-kontrolle", "✔ Die Kontrolle haelt: `zufall` traegt "
               "auf der Watchlist NICHT (+0,0179, 43 Bloecke, "
               "Trennschaerfe 0,0606)", "gilt",
               "k1w_beitrag_auf_der_watchlist.py"),
    Befundlage("2.230", "⚠️⚠️⚠️ DER EIGENTLICHE BEFUND: DIE WATCHLIST IST "
               "ZU KLEIN, UM ZWEI DER DREI BEITRAEGE DORT ZU PRUEFEN. "
               "`turnover` erreicht 5 von 20 noetigen Bloecken, "
               "`oi_aenderung` loest seine eigene Wirkung nicht auf. Nur "
               "`funding` hat genug Abdeckung. Das ist keine Aussage "
               "GEGEN die beiden - es heisst, dass ihre Wirkung auf der "
               "Kettenmenge UNBELEGT ist", "gilt",
               "k1w_beitrag_auf_der_watchlist.py",
               basis="Watchlist 43 Symbole"),
    Befundlage("2.230-folge", "⚠️ WAS DARAUS FOLGT: der Widerspruch aus "
               "2.228 (frei gegen selektiert) laesst sich auf der "
               "Watchlist NICHT entscheiden - dafuer fehlen die Daten. "
               "Fuer `funding` ist er entschieden (traegt dort, "
               "staerker); fuer die anderen beiden bleibt er offen, und "
               "zwar aus Datenmangel, nicht aus Uneinigkeit", "gilt",
               "Befund 2.228 / K-1w"),
    Befundlage("2.230-anzeigefehler", "⚠️ Eigener Anzeigefehler dabei "
               "gefunden: eine abgeleitete Spalte 'Anker/Tag' zeigte 47,8 "
               "bei nur 43 Watchlist-Symbolen - unmoeglich. `n_anker` "
               "zaehlt ueber ALLE Tage der Sammlung, `n_tage` nur die, "
               "die die Tagesklammer ueberstehen. Die beiden Zahlen sind "
               "nicht teilbar; massgeblich sind die BLOECKE", "gilt",
               "Selbstbefund 09.09.2026"),
    Befundlage("2.231", "⚠️⚠️ NUTZEREINWAND 09.09., BERECHTIGT: 'wenn "
               "die Watchlist ein Asset ist, sollte es egal sein'. Er hat "
               "recht - ich hatte ZWEI Fragen vermischt. 'Traegt die "
               "REGEL?' ist eine Aussage ueber die Welt, dafuer ist die "
               "MESSBASIS die richtige und staerkere Basis. 'Wirkt sie "
               "auf UNSEREN Werten?' ist die Watchlist-Frage. K-1w hat "
               "die zweite gemessen und ich habe sie als Antwort auf die "
               "erste gelesen", "gilt", "Nutzereinwand 09.09.2026"),
    Befundlage("2.231-folge", "⚠️ DAMIT IST K-1w NEU ZU LESEN: auf 43 "
               "statt 536 Symbolen werden 92 % der Daten weggeworfen - "
               "`turnover`s 5 Bloecke sind ein Befund ueber die "
               "MESSANLAGE, nicht ueber `turnover`. Der "
               "Messbasis-Befund steht. Uebrig bleibt nur die kleinere "
               "Frage, ob die Watchlist systematisch anders ist",
               "gilt", "Nutzereinwand 09.09.2026 / K-1w"),
    Befundlage("2.232", "✔✔✔ DIE MESSMENGE IST EINGEFROREN "
               "(Nutzerentscheidung 09.09.): `messmenge.V1`, 536 Symbole, "
               "davon 174 EINGESTELLTE Reihen - der Survivorship-Schutz. "
               "Keine Auswahl nach Groesse, Liquiditaet oder Leistung. "
               "`lade()` liefert genau sie und MELDET, wenn eine Reihe "
               "fehlt, statt stillschweigend weniger zu messen", "gilt",
               "messmenge.py / messe_eigenschaft_beitrag.lade",
               basis="Messmenge Krypto v1, gesetzt 09.09.2026"),
    Befundlage("2.232-warum", "⚠️⚠️ DER GRUND IST NICHT ABDECKUNG, "
               "SONDERN REPRODUZIERBARKEIT: bis heute war die Messmenge "
               "das, was gerade in der Datenbank stand. `oi_aenderung` "
               "war auf 117 Symbolen registriert, heute waren es 122 - "
               "und der Wert wanderte von +0,0145 auf +0,0126. R-R11 ist "
               "nicht durchsetzbar, wenn sich die Basis unter dem Befund "
               "wegschiebt", "gilt", "messmenge.py",
               basis="Befund 2.225-reproduziert"),
    Befundlage("2.232-abnahme", "✔ Abgenommen: die eingefrorene Menge "
               "liefert 536 = 536 identisch, und `funding` frei +0,0249 "
               "sowie `turnover` frei +0,0639 reproduzieren ziffergenau. "
               "Vier Waechter im Paket `Messstandard` halten es fest",
               "gilt", "pruefe_pakete --paket Messstandard"),
    Befundlage("2.233", "✔ DIE TURNOVER-ABDECKUNG IST EINE GRENZE DER "
               "QUELLE, NICHT DES ZUSCHNITTS: der Coin-Metrics-"
               "Community-Katalog fuehrt fuer `SplyCur` (1d) insgesamt "
               "139 Assets. Davon liegen 66 in unserer Messmenge von 536 "
               "- also 12 %. Selbst bei vollstaendiger Abdeckung des "
               "Katalogs waeren es 26 %", "gilt",
               "Katalogabfrage 09.09.2026",
               basis="community-api.coinmetrics.io/v4/catalog/asset-metrics"),
    Befundlage("2.233-nicht-brauchbar", "⚠️⚠️ UND DIE 18 SCHEINBAR "
               "GEWINNBAREN SIND NICHT BRAUCHBAR: sie heissen `BNB_ETH`, "
               "`USDC_ETH`, `SHIB_ETH`, `MATIC_ETH`, `TRX_ETH` - das sind "
               "die Mengen AUF ETHEREUM, nicht die Umlaufmengen. "
               "`turnover` ist Umsatz durch Umlaufmenge; wer die "
               "Wrapped-Menge einsetzt, misst einen Bruchteil des Tokens "
               "auf einer Kette, und die Kennzahl waere STILL falsch",
               "gilt", "Katalogabfrage 09.09.2026"),
    Befundlage("2.233-offen", "⚠️ OFFEN BLEIBT DER WEG UEBER EINE ANDERE "
               "QUELLE: CoinGecko fuehrt Umlaufmengen fuer weit mehr "
               "Coins. Er ist der einzige, der etwas aendern wuerde - "
               "braucht aber eine eigene Pruefung, weil zwei Quellen fuer "
               "dieselbe Groesse still auseinanderlaufen koennen "
               "(stehende Vorgabe: die Datenquelle mitpruefen)", "gilt",
               "Nutzerentscheidung offen"),
    Befundlage("2.234", "⚠️⚠️⚠️ DIE LAGE WAR BIS ZUM 09.09. NUR EIN "
               "ETIKETT: `pruefe_auswahl` hatte `zielgroesse='bewegung_r'` "
               "FEST VERDRAHTET und reichte die `lage` nur an den Befund "
               "durch. Eine Messung mit `lage=Lage('hebel',...)` haette "
               "Spot-Bewegung gemessen und 'Hebel' daraufgeschrieben",
               "gilt", "messnorm_auswahl.py / Selbstbefund 09.09."),
    Befundlage("2.234-zielgroessen", "⚠️⚠️ UND `ZIELGROESSEN` KANNTE DIE "
               "VERBILLIGUNG NICHT, obwohl die Akkumulation seit dem "
               "28.08. mit ihr gemessen wird. Ein Zielgroessenregister, "
               "das die laufende Zielgroesse einer Lage nicht kennt, kann "
               "nicht verhindern, dass eine Lage mit dem Massstab einer "
               "anderen gemessen wird", "gilt", "messnorm.ZIELGROESSEN"),
    Befundlage("2.234-behoben", "✔ BEHOBEN: `verbilligung` ist "
               "nachgetragen, `ZIELGROESSE_JE_LAGE` ordnet jeder Lage ihr "
               "Mass zu (spot/einstieg -> bewegung_r · spot/akkumulation "
               "-> verbilligung · hebel/* -> barriere), und "
               "`pruefe_auswahl` WEIST AB, wenn beides nicht "
               "zusammenpasst", "gilt", "messnorm.py / messnorm_auswahl.py"),
    Befundlage("2.235", "⚠️⚠️⚠️ K-1c: DIE AKKUMULATIONSLAGE IST MIT DER "
               "BLOCKREGEL NICHT MESSBAR. Alle fuenf Kandidaten - "
               "einschliesslich der Kontrolle `zufall` - liefern KEIN "
               "BEFUND: 6 bis 10 Bloecke gegen 20 geforderte. Die Ursache "
               "ist strukturell: bei H90 betraegt die Blocklaenge 3 x 90 "
               "= 270 Tage, fuer 20 Bloecke braeuchte es 5.400 "
               "Handelstage - rund 22 Jahre. Der Kryptomarkt hat 2.900",
               "gilt", "k1c_lagen_eigene_zielgroesse.py",
               basis="Messmenge v1, Zielgroesse verbilligung, H90"),
    Befundlage("2.235-nicht-dagegen", "⚠️ DAS IST KEINE AUSSAGE GEGEN DIE "
               "BEITRAEGE. 'Kein Befund' ist laut Norm eine Aussage ueber "
               "die MESSUNG. Weder fuer noch gegen - die Anlage kann auf "
               "diesem Horizont nicht urteilen", "gilt",
               "k1c_lagen_eigene_zielgroesse.py"),
    Befundlage("2.235-eigener-fehler", "⚠️⚠️ EIGENER FEHLER, sofort "
               "korrigiert: die erste Fassung des Skripts las `b.traegt` "
               "statt das URTEIL und meldete drei Traeger, waehrend ALLE "
               "FUENF 'KEIN BEFUND' lauteten. `traegt` prueft nur 'Band "
               "ueber dem Bezugspunkt' und weiss NICHTS von der "
               "Blockzahl. Dieselbe Verwechslung wie Fehler 4 vom 08.09. "
               "- diesmal an der Norm VORBEI, weil das Skript die "
               "Eigenschaft direkt gelesen hat", "gilt",
               "k1c_lagen_eigene_zielgroesse.py"),
    Befundlage("2.236", "⚠️⚠️ WAS DARAUS FOLGT - und es beruehrt die "
               "Nutzerwarnung vom 08.09. ('keine unerreichbaren Regeln "
               "aufstellen'): 20 Bloecke bei H90 SIND unerreichbar, "
               "solange der Kryptomarkt jung ist. Entweder der Horizont "
               "oder die Blockregel muss sich aendern - das ist eine "
               "ENTWURFSfrage, keine Messfrage. ⚠️ Und `NACHKAUFEN` mit "
               "51,7 Mails am Tag laeuft auf genau dieser Lage", "gilt",
               "k1c_lagen_eigene_zielgroesse.py / Nutzervorgabe 08.09."),
    Befundlage("2.236-hebel", "⚠️ HEBEL IST NOCH NICHT GEMESSEN, und der "
               "Grund gehoert benannt: die vorhandene Barrierenfunktion "
               "(`messe_sentiment_je_horizont.barriere`) rechnet mit "
               "STOP_ATR = 2,5, die Produktion aber mit max(5 % Kurs, "
               "0,75 x ATR). Sie misst ein ANDERES System. Fuer "
               "`hebel x einstieg` braeuchte es die Barriere auf der "
               "Produktionsgeometrie - ein eigener Baustein", "gilt",
               "messe_sentiment_je_horizont.py / Kettenplan"),
    Befundlage("2.236-neutral", "✔ NUTZERWARNUNG 09.09. EINGEHALTEN "
               "('fuer Strategie und Bewertung neutral ohne "
               "Wirtschaftlichkeit'): die Verbilligung ist reine "
               "Kursbewegung - keine Gebuehr, kein Breakeven. Fuer den "
               "Hebelpfad gilt dasselbe: `barriere` ist Ziel vor Stop, "
               "ebenfalls ohne Kosten. Regel 2", "gilt",
               "Nutzervorgabe 09.09.2026"),
    Befundlage("2.237", "⚠️⚠️ K-1c HEBEL: DER LAUF IST UNGUELTIG - die "
               "Kontrolle `zufall` TRAEGT (+0,0007, Band [+0,0002 .. "
               "+0,0013], 48 Bloecke). Drei Kandidaten sahen wie Traeger "
               "aus (turnover, oi_aenderung, schnitt); keiner davon "
               "gilt", "gilt", "k1c_hebel_barriere.py",
               basis="Messmenge v1, Zielgroesse barriere, H20"),
    Befundlage("2.237-median", "✔ DER MEDIAN IST BEI BINAEREN DATEN "
               "ENTARTET - belegt: bei 0/1-Ausgaengen und zufaelliger "
               "Sperrgruppe hat `median(frei) - median(alle)` die "
               "Streuung 0,00000 und nur den Wert 0,0. Deshalb konnte "
               "`barriere` mit der bisherigen Anlage gar nicht gemessen "
               "werden - das war ein echtes Hindernis, kein erfundenes",
               "gilt", "Kunstprobe 09.09.2026",
               basis="2.000 Ziehungen, 300 Anker je Tag"),
    Befundlage("2.237-mittel-ok", "✔ UND DIE MITTEL-STATISTIK IST "
               "UNVERZERRT: ueber 4.000 Ziehungen betraegt "
               "`mean(frei) - mean(alle)` im Mittel +0,00004 bis "
               "+0,00042 bei einer Streuung von 0,0136. Der Fehler liegt "
               "also NICHT in der Statistik", "gilt",
               "Kunstprobe 09.09.2026",
               basis="4.000 Ziehungen je Trefferquote 0,30/0,35/0,40"),
    Befundlage("2.238", "⚠️⚠️⚠️ DER FEHLER LIEGT IM BAND: bei rund 250 "
               "Ankern je Tag und 48 Bloecken muesste das Band etwa "
               "±0,0023 breit sein - beobachtet sind ±0,0006, also "
               "VIERMAL ZU ENG. Ein zu enges Band laesst jede Winzigkeit "
               "'tragen', und genau das tut `zufall` hier", "gilt",
               "k1c_hebel_barriere.py / Ueberschlagsrechnung 09.09.",
               basis="Messmenge v1, Zielgroesse barriere"),
    Befundlage("2.238-klasse", "⚠️ DAS IST DIESELBE KLASSE WIE FEHLER 6: "
               "die EICHUNG DES BANDES auf einem neuen Datentyp war nie "
               "geprueft. Der Pruefstand kann es beantworten - "
               "Fehlalarmquote der Barrieren-Anlage auf Nullwelten, genau "
               "wie am 09.09. fuer den Nullbezug", "gilt",
               "Selbstbefund 09.09.2026"),
    Befundlage("2.238-gebaut", "✔ WAS TROTZDEM STEHT: die Zielgroesse "
               "`barriere` ist jetzt BAUBAR - `ZIELGROESSEN` traegt die "
               "Statistik je Zielgroesse, `je_tag_wirkung` hat die "
               "Mittel-Variante (Vorgabe bleibt Median, "
               "Neutralitaetsprobe bestanden), und die Barriere laeuft "
               "auf der PRODUKTIONSGEOMETRIE min(25 %, max(5 %, 0,75 x "
               "ATR)) mit CRV 2,0 - nicht auf der 2,5er-Variante aus "
               "`messe_sentiment_je_horizont`", "gilt",
               "messnorm.py / pruefe_n31_tagesklammer.py / "
               "k1c_hebel_barriere.py"),
    Befundlage("2.238-auswahl", "⚠️ Und eine Auswahl gehoert benannt: im "
               "Fenster von 20 Tagen loesen sich 94,7 % der Anker, die "
               "uebrigen fallen heraus. Das ist verwandt mit den 79 % "
               "'Einstieg nie erreicht' aus K-6 - dort aber viel "
               "groesser, weil die Kette eine EINSTIEGSZONE hat, die erst "
               "erreicht werden muss", "gilt", "k1c_hebel_barriere.py"),
    Befundlage("2.239", "⚠️ EIGENE UEBERVORSICHT, vom Nutzer korrigiert: "
               "ich hatte gefragt statt gebaut ('wir bauen doch gerade "
               "alles um - verstehe den Grund nicht'). Er hatte recht: "
               "eine Barrierenfunktion auf Produktionsgeometrie ist genau "
               "die laufende Arbeit, keine Grundsatzentscheidung. ⚠️ Das "
               "ECHTE Hindernis lag woanders und war vorher nicht "
               "sichtbar - der entartete Median", "gilt",
               "Nutzereinwand 09.09.2026"),
    Befundlage("2.240", "✔✔✔ N-88: `schnitt`s ZEITSTABILITAET IST "
               "ENTSCHIEDEN - und zwar GEGEN ihn. Ueber alle fuenf Mengen "
               "gemessen dreht sein Haelftenunterschied das Vorzeichen "
               "(-0,431 / -0,081 / +0,197 / +0,002 / +0,018) und ist auf "
               "ZWEI Mengen TRENNBAR - auf 5 % mit -0,43, auf 20 % mit "
               "+0,20. Widerspruechliche signifikante Antworten je nach "
               "Menge", "gilt", "n88_schnitt_zeitstabil_neu.py",
               basis="Messmenge v1, entzerrte Reihe, H20, fuenf Mengen"),
    Befundlage("2.240-kontrollen", "✔ UND DIE KONTROLLEN TRENNEN DAS AB: "
               "`funding` zeigt ueber alle fuenf Mengen DASSELBE "
               "Vorzeichen (+0,060 bis +0,003) und auf KEINER einen "
               "trennbaren Unterschied - er ist zeitstabil. `zufall` "
               "dreht zwar auch, wird aber NIE trennbar. Nur `schnitt` "
               "liefert gegenlaeufige SIGNIFIKANTE Unterschiede",
               "gilt", "n88_schnitt_zeitstabil_neu.py"),
    Befundlage("2.240-abbruch", "⚠️⚠️ DIE ABBRUCHBEDINGUNG AUS DEM "
               "KANDIDATENREGISTER IST DAMIT BESTAETIGT, nicht "
               "aufgeloest. 'Unentschieden' (07.09.) war zu freundlich: "
               "der Test gibt je nach Menge widerspruechliche "
               "SIGNIFIKANTE Antworten, und das ist eine Eigenschaft von "
               "`schnitt`, nicht des Verfahrens. Die Sperre ist NICHT "
               "baubar", "gilt", "n88_schnitt_zeitstabil_neu.py / "
               "REGISTER_Kandidaten"),
    Befundlage("2.240-standard", "⚠️ Der neue Messstandard hat daran "
               "NICHTS geaendert - richtig so: die Zeitstabilitaet haengt "
               "nicht am Nullbezug (dort wird ein UNTERSCHIED gegen null "
               "geprueft, keine Wirkung gegen eine gemischte Welt), "
               "sondern an der Menge. Die Vorhersage stand vor dem Lauf "
               "und ist eingetroffen", "gilt",
               "n88_schnitt_zeitstabil_neu.py"),
    Befundlage("2.241", "✔ REVIEW DER ERLEDIGTEN HEBEL-BEFUNDE "
               "(Nutzerauftrag 09.09., keine Doppelmessung sondern Suche "
               "nach Showstoppern): KEIN Showstopper beim "
               "Kalibrierungsfaktor. `hebel_scheitert_an_der_bewertung` "
               "rechnet mit 19,5 % - das ist der ERSATZ F-219, gemessen "
               "mit der Invarianz als vorab gesetztem Annahmekriterium "
               "(ROH und ANTEIL fielen durch, RANG war exakt invariant). "
               "Gefallen war die ALTE Zahl 16,8 %", "gilt",
               "Review 09.09.2026 / F-219"),
    Befundlage("2.241-horizont", "⚠️⚠️ DER EINE ECHTE SHOWSTOPPER IST "
               "BEKANNT UND GEMESSEN, nicht uebersehen: die Beitraege "
               "sind auf H20 belegt (funding +0,0246, turnover +0,0616), "
               "bei H1/H2 aber 6-7x kleiner (+0,0019 / +0,0026). N-17a "
               "hat die H2-Kalibrierung vollstaendig durchgemessen "
               "(F-203): die beste Schwelle ist praktisch 0,000, r ~ "
               "0,02. ✔ BEWUSST NICHT live registriert - 'eine Schwelle "
               "ohne Trennschaerfe waere eine Mengenbremse ohne "
               "Qualitaetsaussage'", "gilt", "Review 09.09. / F-185 / "
               "F-203 / F-210"),
    Befundlage("2.241-nur-hebel", "✔✔ UND ER TRIFFT NUR DEN HEBEL, NICHT "
               "SPOT: die 2,0 Tage mediane Dauer (F-202) stammen aus "
               "Trades MIT Barrieren. Spot hat nach Nutzerentscheidung "
               "vom 03.09. KEINEN Stop - der Ausstieg ist rein "
               "bewertungsbasiert, nichts zwingt zum frueher Ausstieg. "
               "Fuer `spot x einstieg` ist H20 damit stimmig. Genau "
               "deshalb heisst der Befund 'der HEBEL scheitert an der "
               "Bewertung' und nicht 'die Bewertung scheitert'", "gilt",
               "Review 09.09.2026 / F-202 / N-16e"),
    Befundlage("2.188", "⚠️⚠️⚠️ DIE URSACHE DES HIN UND HER GEFUNDEN: "
               "`messnorm_auswahl.ZIEHUNGEN` ist 5, und `Befund.traegt` "
               "prueft `unten > max(0, null_oben)` - wobei `null_oben` "
               "das MAXIMUM ueber diese fuenf Mischungen ist. Ein "
               "Maximum ueber wenige Ziehungen ist systematisch ZU "
               "NIEDRIG, also faellt das Urteil zu WOHLWOLLEND aus",
               "gilt", "Methodik 2.188 / Nutzervorgabe 08.09.",
               basis="Messbasis 08.09.2026, 536 Krypto-Symbole"),
    Befundlage("2.188-beleg", "⚠️⚠️ DER BELEG, an `funding` bei 50 % "
               "(Abstand `unten - null_oben`): bei 5 Ziehungen +0,0002 R "
               "-> TRAEGT · bei 20 Ziehungen -0,0045 -> NICHT TRENNBAR · "
               "bei 40 Ziehungen -0,0056 -> TRAEGT NICHT bis 0,05. ZWEI "
               "Zehntausendstel R entschieden ueber das Urteil. "
               "`null_oben` steigt dabei von +0,0192 auf +0,0250",
               "gilt", "Methodik 2.188",
               basis="Messbasis 08.09.2026, 536 Krypto-Symbole"),
    Befundlage("2.188-schnitt", "✔ NICHT ALLE URTEILE HAENGEN DARAN: "
               "`schnitt` bei 20 % haelt bei 5, 10, 20 UND 40 Ziehungen "
               "durchgehend TRAEGT - der Abstand betraegt dort +0,0595 "
               "bis +0,0521. Ein Befund mit grossem Abstand ist robust; "
               "gefaehrlich sind die knappen", "gilt", "Methodik 2.188",
               basis="Messbasis 08.09.2026, 536 Krypto-Symbole"),
    Befundlage("2.188-vorgabe", "⚠️ UND ES WIDERSPRICHT ZWEI EIGENEN "
               "STEHENDEN VORGABEN: 'Die ZIEHUNGSZAHL gehoert in JEDE "
               "Kontrolle' und 'EINE ZIEHUNG IST KEIN NULLPUNKT'. Beide "
               "wurden fuer die WIRKUNG befolgt und fuer den NULLPUNKT "
               "uebersehen", "gilt", "Methodik 2.188"),
    Befundlage("2.188-inkonsistenz", "⚠️ Und eine zweite Unstimmigkeit "
               "in derselben Anlage: die TRENNSCHAERFE prueft "
               "`pb['unten'] > 0` - gegen NULL. Das URTEIL prueft gegen "
               "`null_oben`. Wenn `null_oben` > 0 ist, ist das Urteil "
               "STRENGER als die Trennschaerfe angibt. Ein Kandidat kann "
               "eine Trennschaerfe von 0,02 haben und bei einem Effekt "
               "von 0,05 kein TRAEGT erreichen", "gilt",
               "Methodik 2.188"),
    Befundlage("2.188-nichtsaat", "⚠️ Eine eigene Vermutung wurde dabei "
               "WIDERLEGT: ich hielt `null_oben` fuer saatabhaengig. Es "
               "ist deterministisch - die Nullziehungen laufen auf der "
               "festen Saat `SAAT + z`, nicht auf der uebergebenen "
               "`rng`. Fuenf Saaten liefern +0,0375 bis +0,0383. Was "
               "wandert, ist die Reaktion auf geaenderte DATEN, nicht "
               "auf Zufall", "gilt", "Methodik 2.188"),
    Befundlage("2.187", "⚠️⚠️ R-R11 AUF DER NEUEN MESSBASIS: die "
               "Durchsicht aller Kandidaten (N-73) ist auf der Basis vom "
               "08.09. (536 Symbole) wiederholt. DIE WIRKUNGEN "
               "REPRODUZIEREN FAST EXAKT - turnover 50 % +0,0913 gegen "
               "+0,0909, schnitt 20 % +0,1858 gegen +0,1759, funding "
               "frei +0,0249 gegen +0,0246. ABER DREI URTEILE WANDERN, "
               "weil sich Nullpunkte und Trennschaerfen verschieben",
               "gilt", "Methodik 2.187 / n73 auf neuer Basis",
               basis="Messbasis 08.09.2026, 536 Krypto-Symbole"),
    Befundlage("2.187-was-haelt", "✔ WAS REPRODUZIERT: `schnitt` ist "
               "weiterhin NICHT ROBUST (traegt nur bei 20 %, nicht bei "
               "10 % oder frei) · `amihud`, `rsi`, `momentum` und "
               "`schnitt50` bleiben abgelehnt, auf ALLEN Mengen · "
               "`zufall` traegt nirgends. Die tragenden Ablehnungen des "
               "07.09. stehen", "gilt", "Methodik 2.187",
               basis="Messbasis 08.09.2026, 536 Krypto-Symbole"),
    Befundlage("2.187-was-wandert", "⚠️ WAS WANDERT, jeweils bei nahezu "
               "gleicher Wirkung: `turnover` 50 % von TRAEGT auf 'nicht "
               "trennbar' · `funding` frei von 'traegt nicht bis 0,10' "
               "auf TRAEGT · `vola` 20 % von 'nicht trennbar' auf "
               "TRAEGT. Die Zahl der Mengen-Widersprueche steigt von "
               "ZWEI auf VIER", "gilt", "Methodik 2.187",
               basis="Messbasis 08.09.2026, 536 Krypto-Symbole"),
    Befundlage("2.187-lehre", "⚠️⚠️ DIE LEHRE: die Urteile der Norm "
               "haengen an NULLPUNKT und TRENNSCHAERFE, und beide werden "
               "je Lauf aus Ziehungen geschaetzt. Eine um 2 % "
               "veraenderte Messbasis verschiebt die WIRKUNG um weniger "
               "als 0,0005 R, kann aber ein Urteil kippen. Wer nur die "
               "Wirkung vergleicht, sieht das nicht - wer nur das Urteil "
               "vergleicht, haelt eine Verschiebung des Nullpunkts fuer "
               "einen neuen Befund", "gilt", "Methodik 2.187"),
    Befundlage("2.187-feld", "✔ STRUKTURELLER FIX: `Befundlage` hat "
               "jetzt ein Feld `basis`. Am 08.09. war nach zwei "
               "Basiswechseln nicht mehr feststellbar, welche der 92 "
               "geltenden Befunde auf welcher Grundlage entstanden waren "
               "- 25 tragen Messzahlen. ⚠️ R-R11 verlangt Reproduktion "
               "vor Widerruf, aber wer nicht weiss, WORAUF ein Befund "
               "steht, kann ihn nicht reproduzieren. Vorgabe leer (die "
               "Altbefunde bleiben unveraendert), ab jetzt gefuellt",
               "gilt", "Methodik 2.187"),
    Befundlage("2.186", "⚠️ MEINE AUSSAGE 'CANTON HAT GAR KEINE "
               "KURSREIHE' WAR ZU ENG. Es hat 252 CoinGecko-Tagespreise "
               "in `price_history`. Was fehlt, ist OHLC - nur `close`, "
               "also kein ATR, keine Stopgeometrie, kein `vola`. Fuer "
               "einen gleitenden Schnitt genuegt es; `marktrang.py` "
               "nutzt genau das", "gilt",
               "Methodik 2.186 / Nutzerhinweis 08.09."),
    Befundlage("2.186-symbol", "✔ DAS SYMBOLPROBLEM IST REAL, "
               "DOKUMENTIERT UND GELOEST: CoinGecko fuehrt "
               "`canton-network` unter dem Symbol **CC**, unsere "
               "Watchlist unter `CANTON`. Der Abgleich lief ueber das "
               "SYMBOL - 'CANTON konnte deshalb NIE gefunden werden, und "
               "zwar lautlos' (marktrang.py). Seit 31.08. laeuft er ueber "
               "die `coingecko_id`", "gilt", "Methodik 2.186"),
    Befundlage("2.186-frische", "⚠️⚠️ WARUM CANTON TROTZDEM IN "
               "`schnitte()` FEHLT - und der Grund ist NICHT CANTON: "
               "`SCHNITT_FRISCHE_TAGE` ist 10, CANTONs letzter Tagespreis "
               "ist vom 2026-07-19 und damit 51 Tage alt. ⚠️ ABER "
               "`bitcoin` und `kaspa` sind in `price_history` GENAUSO 51 "
               "Tage alt - DIE GANZE TABELLE STEHT SEIT DEM 19.07. "
               "STILL. Das ist ein Datenstand-Befund ueber die "
               "DESKTOP-KOPIE", "gilt", "Methodik 2.186"),
    Befundlage("2.186-notebook", "⚠️ WAS VON HIER AUS NICHT FESTSTELLBAR "
               "IST: ob `refresh_prices_job` auf dem NOTEBOOK weiterlaeuft. "
               "Steht `price_history` auch dort seit dem 19.07., fehlen "
               "seit 51 Tagen die Tagespreise fuer ALLE Werte ohne "
               "Boersenlisting (CANTON, VSN, AIOZ, SUPRA). Das waere kein "
               "niedrig priorisierter Punkt mehr - es ist eine "
               "RUECKFRAGE, keine Messung", "gilt", "Methodik 2.186"),
    Befundlage("2.186-abstand", "⚠️ UND DIE UEBERNAHME HAT EINE NEUE "
               "LUECKE ERZEUGT: `schnitte()` liefert jetzt 536 Symbole, "
               "`schnitt_werte()` nur 516. ACHT der zehn Uebernommenen "
               "(AIOZ, AKT, BRETT, CAT, GRIFFAIN, HYPE, KAS, SUPRA) "
               "haben einen 200-Tage-Schnitt, aber KEINEN Abstand - "
               "`schnitt_werte` braucht einen AKTUELLEN Kurs vom "
               "Binance-Ticker, und dort sind sie nicht gelistet. MORPHO "
               "und PLUME funktionieren (sie haben Binance-Zeilen). ✔ "
               "Heute FOLGENLOS, weil `schnitt` nicht registriert ist "
               "(zustand='null') und die Messungen direkt aus der "
               "Messbasis lesen - aber bei einer Aktivierung waeren "
               "diese acht ohne Rang", "gilt", "Methodik 2.186"),
    Befundlage("2.185", "✔✔ D-1 ERLEDIGT: ZEHN REIHEN AUS DER "
               "PRODUKTION UEBERNOMMEN (AIOZ, AKT, BRETT, CAT, GRIFFAIN, "
               "HYPE, KAS, MORPHO, PLUME, SUPRA) - 6.768 Zeilen, alle "
               "mit Median-Tagesabstand 1, null Luecken, null Zeilen "
               "ohne Tagesspanne. Messbasis 526 -> 536 Krypto-Symbole. "
               "Die gehaltenen Luecken sinken von ACHT auf DREI",
               "gilt", "Methodik 2.185 / uebernehme_messreihen.py"),
    Befundlage("2.185-quelle", "⚠️⚠️ DIE QUELLENREINHEIT BLEIBT SICHTBAR: "
               "jede uebernommene Zeile traegt eine eigene Quelle - "
               "`uebernommen_gemessen` 3.878, `uebernommen_bybit` 2.822, "
               "`uebernommen_binance` 68 gegen `binance_mess` 5.121.873. "
               "Ein `SELECT DISTINCT quelle` zeigt es sofort. Bei "
               "mehreren Quellen je Tag gewinnt die beste: binance vor "
               "bybit vor gemessen", "gilt", "Methodik 2.185"),
    Befundlage("2.185-veralten", "⚠️ UND DER PREIS IST BENANNT: diese "
               "Symbole sind NICHT auf Binance - `lade_messreihen.py` "
               "kann sie NIE auffrischen. Sie enden am 19.08. bzw. "
               "13.07. und bleiben dort stehen. Deshalb tragen sie in "
               "`messreihen_status` den eigenen Status `uebernommen` "
               "statt `handelnd` - sichtbar statt still", "gilt",
               "Methodik 2.185"),
    Befundlage("2.185-rest", "WAS OFFEN BLEIBT, mit prazisierter "
               "Begruendung: ASTER (318 USD-Tage) und MON (269) liegen "
               "unter der 400er-Grenze - eine DATENLAGE-Grenze, keine "
               "Nachlaessigkeit; die Coins existieren erst seit 10/2025 "
               "bzw. 11/2025. CANTON hat in der Produktion GAR KEINE "
               "Kursreihe und ist zugleich Kernwert. VSN ist auf "
               "Nutzerentscheidung 08.09. ausgenommen ('vsn ist nicht "
               "relevant')", "gilt", "Methodik 2.185"),
    Befundlage("2.185-meldung", "⚠️ Die Meldung selbst war nach der "
               "Uebernahme UNGENAU geworden: sie sagte bei ASTER und MON "
               "weiter 'die Daten sind da, nur nicht uebernommen', "
               "dabei sind sie zu kurz. Ursache: sie zaehlte die "
               "GESAMTzeilen (USD+EUR) statt der USD-Tage. Korrigiert - "
               "jetzt nennt sie die USD-Tageszahl und trennt 'zu kurz' "
               "von 'nicht uebernommen'", "gilt", "Methodik 2.185"),
    Befundlage("2.184", "✔✔ DIE AUFFRISCHUNG IST DURCH: 347 Reihen, "
               "539.568 Kerzen, 259 s. Die Krypto-Messbasis steht jetzt "
               "auf 2026-09-08 statt 2026-08-21 - nur noch drei Reihen "
               "auf dem alten Stand. Ablauf protokolliert: Sicherung "
               "(SHA-256 bitgleich) -> Anker VORHER -> Trockenlauf -> "
               "Schreiben -> Anker NACHHER", "gilt",
               "Methodik 2.184 / Gesamtplan 08.09."),
    Befundlage("2.184-urteile", "⚠️⚠️ ZWEI URTEILE HABEN SICH GEAENDERT, "
               "und beide sind VERBESSERUNGEN durch mehr Daten, keine "
               "Instabilitaet: `funding` H20 frei geht von 'traegt nicht "
               "bis 0,10 R' auf TRAEGT (+0,02458 -> +0,02581, also nur "
               "+0,00123 Verschiebung), und `zufall` H20 5 % von 'KEIN "
               "BEFUND' auf 'traegt nicht bis 0,05 R'. In beiden Faellen "
               "ist das BAND enger geworden - 526 statt 524 Symbole und "
               "18 Tage mehr Daten", "gilt", "Methodik 2.184"),
    Befundlage("2.184-logik", "⚠️ DABEI EINE EIGENE FEHLANNAHME "
               "KORRIGIERT: ich hielt 'TRAEGT' fuer 'Effekt ueber der "
               "Trennschaerfe'. `messnorm.Befund.urteil` sagt es anders - "
               "TRAEGT heisst 'das Band schliesst den NULLPUNKT aus'. Die "
               "Trennschaerfe blieb bei 0,1; sie erklaert den Wechsel "
               "nicht. Und er ist SAATSTABIL: fuenf Saaten, ein Urteil",
               "gilt", "Methodik 2.184"),
    Befundlage("2.184-rr11", "⚠️ R-R11 GILT TROTZDEM: die Anker in "
               "`messbasis_anker.json` stehen jetzt auf der NEUEN Basis. "
               "Der registrierte `funding`-Befund (+0,0246) und alle "
               "heutigen Messungen (N-73 bis N-80) liefen auf der ALTEN. "
               "Die groesste Verschiebung betraegt +0,01358 R (`schnitt` "
               "H20 20 %: +0,17593 -> +0,18951) - kein Urteil dort "
               "aendert sich, aber die ZAHLEN sind nachzuziehen", "gilt",
               "Methodik 2.184"),
    Befundlage("2.182", "✔ DIE FRISCHEPRUEFUNG WAR ZU STRENG und ist "
               "korrigiert: EINGESTELLTE Reihen sind VOLLSTAENDIG, nicht "
               "veraltet - sie handeln nicht mehr, es gibt keine neuen "
               "Kurse. Die erste Fassung zaehlte alle 174 eingestellten "
               "Krypto-Reihen als Mangel und haette das Paket dauerhaft "
               "rot gehalten fuer etwas, das kein Fehler ist. Jetzt: 350 "
               "handelnde, davon 344 veraltet (98 %); die 174 "
               "eingestellten getrennt ausgewiesen", "gilt",
               "Methodik 2.182"),
    Befundlage("2.182-trocken", "DER TROCKENLAUF DER AUFFRISCHUNG: 347 "
               "von 487 Binance-Paaren brauchbar, 539.568 Kerzen, 4,6 "
               "Minuten. 140 abgelehnt - ALLE wegen 'zu kurz' (< 400 "
               "Kerzen), keine Plausibilitaets- oder Lueckenfehler. "
               "Schreibsemantik ist ein sauberer Upsert (INSERT OR "
               "REPLACE, PK ueber symbol/assetklasse/currency/date) - "
               "eine Auffrischung ERGAENZT, sie ueberschreibt keine "
               "Historie. Die harte Sperre gegen die Produktions-DB "
               "greift", "gilt", "Methodik 2.182 / lade_messreihen.py"),
    Befundlage("2.183", "⚠️⚠️ DIE F-198-KOLLISIONEN SIND NUR HALB "
               "BEREINIGT: sieben Symbole (BOND, C, DASH, DIA, MDT, STX, "
               "T) tragen in `price_history_ohlc` eine ANDERE Klasse als "
               "in `messreihen`. Alle sieben haben Kurse in ZWEI Klassen "
               "- DASH etwa aktien 1.440 UND krypto 2.721 -, aber "
               "`messreihen.symbol` ist PRIMARY KEY und kann nur EINER "
               "Klasse zuordnen", "gilt", "Methodik 2.183"),
    Befundlage("2.183-folge", "✔ DIE MESSUNGEN SIND NICHT BETROFFEN: "
               "`_reihen_roh` ueberspringt den `messreihen`-Filter, wenn "
               "`price_history_ohlc` die Spalte `assetklasse` traegt - "
               "der Fix vom 07.09. ⚠️ ABER `klassen_aus_db()` liest "
               "weiterhin aus `messreihen` und liefert fuer diese sieben "
               "die FALSCHE Klasse. Ueber ZEHN Messwerkzeuge importieren "
               "sie. Wer sie zur Klassenentscheidung nutzt, bekommt dort "
               "das Falsche", "gilt", "Methodik 2.183"),
    Befundlage("2.183-nichtjetzt", "⚠️ NICHT JETZT REPARIERT, und mit "
               "Grund: der saubere Fix verlangt, dass ein Symbol "
               "MEHREREN Klassen zugeordnet werden kann - das ist eine "
               "Strukturaenderung an `messreihen` und beruehrt zehn "
               "Werkzeuge. Nutzervorgabe 08.09.: 'langsam und vorsichtig "
               "planen und umsetzen'. Als Suitepruefung gemeldet, damit "
               "es nicht wieder untergeht", "gilt", "Methodik 2.183"),
    Befundlage("2.181", "⚠️ KORREKTUR AN MEINER EIGENEN "
               "KLASSIFIZIERUNG: `HYPE` IST AUFNEHMBAR. Ich hatte es als "
               "'zu kurz' gefuehrt (bybit 238, gemessen 167) - "
               "KOMBINIERT ergeben die beiden USD-Quellen 405 "
               "einzigartige Tage von 405 moeglichen, also LUECKENLOS "
               "und ueber der 400er-Grenze. Sie ergaenzen sich exakt: "
               "bybit 2025-07-11 bis 2026-08-19, gemessen 2026-01-28 bis "
               "2026-07-13. Damit sind es ZEHN aufnehmbare, nicht neun",
               "gilt", "Methodik 2.181 / Nutzerhinweis 08.09."),
    Befundlage("2.181-grenzen", "ASTER (318 Tage) und MON (269) bleiben "
               "auch kombiniert unter 400 - aber der Grund ist die "
               "DATENLAGE, nicht die Sammlung: die Coins existieren erst "
               "seit 10/2025 bzw. 11/2025. Beide Reihen sind zu 100 % "
               "lueckenlos. Das ist eine Grenze, keine Nachlaessigkeit",
               "gilt", "Methodik 2.181"),
    Befundlage("2.181-canton", "⚠️⚠️ CANTON ist der schwierigste Fall - "
               "und er hat DOCH Daten, nur in der falschen Tabelle: "
               "`price_history` (CoinGecko-Tagespreise) fuehrt "
               "`canton-network` mit 252 Zeilen (2025-11-10 bis "
               "2026-07-19). ⚠️ Diese Tabelle hat aber NUR "
               "`price_usd`/`price_eur` - KEIN Hoch/Tief. Ohne "
               "Tagesspanne gibt es kein ATR, keine Stopgeometrie und "
               "kein `vola`. CANTON ist damit zu kurz UND ohne Spanne - "
               "als KERNWERT im Bestand ist das eine echte "
               "Einschraenkung, die der Nutzer kennen muss", "gilt",
               "Methodik 2.181"),
    Befundlage("2.181-gemessen", "✔ Entwarnung zur Quelle `gemessen`: "
               "laut `database/db.py` ist sie ein 'echter Kursabruf' "
               "(ueber `api/boersen_klines.py` bzw. "
               "`api/yfinance_krypto_fallback.py`), also echte Kerzen "
               "mit Hoch und Tief. Der Anteil ohne Tagesspanne betraegt "
               "bei den fraglichen Symbolen 0,0 %", "gilt",
               "Methodik 2.181"),
    Befundlage("2.180", "⚠️⚠️ DIE FEHLENDEN MESSREIHEN SIND KEIN "
               "UEBERNAHMEVERSAEUMNIS, sondern eine QUELLENFRAGE. Die "
               "Messbasis laedt Binance-USDT-Spotpaare "
               "(`quelle='binance_mess'`, 5.114.965 Zeilen einheitlich). "
               "Binance FUEHRT die fehlenden Symbole ueberwiegend nicht: "
               "von 14 haben nur ASTER (51 Zeilen), MORPHO (31) und "
               "PLUME (37) ueberhaupt Binance-Daten, alle erst seit "
               "Juli 2026", "gilt", "Methodik 2.180 / Audit 08.09."),
    Befundlage("2.180-ersatz", "Die Produktion ergaenzt aus ANDEREN "
               "Quellen: `bybit` (AIOZ, BRETT, CAT, HYPE, KAS, MON, "
               "SUPRA) und `gemessen` (AKT, GRIFFAIN und andere). ⚠️ "
               "Eine Uebernahme wuerde die Quellenreinheit der Messbasis "
               "brechen - deshalb ist Kopieren NICHT der saubere Weg, "
               "sondern Uebernahme MIT Quellenkennzeichnung", "gilt",
               "Methodik 2.180"),
    Befundlage("2.180-qualitaet", "GEPRUEFT, ob die Ersatzquellen die "
               "Aufnahmebedingungen halten (Median-Tagesabstand genau 1, "
               ">= 400 Kerzen, < 5 % Luecken): NEUN sind aufnehmbar - "
               "AIOZ (bybit 592), AKT (gemessen 727), BRETT (bybit 854), "
               "CAT (418), GRIFFAIN (537), KAS (608 bzw. bybit 470), "
               "MORPHO (606), PLUME (447), SUPRA (bybit 631). DREI sind "
               "zu kurz: ASTER (267), HYPE (238), MON (232). ZWEI haben "
               "nirgends Daten: CANTON, VSN", "gilt", "Methodik 2.180"),
    Befundlage("2.180-gehalten", "Auf die ACHT gehaltenen Positionen "
               "heruntergebrochen: VIER aufnehmbar (BRETT, KAS, MORPHO, "
               "SUPRA), ZWEI zu kurz (ASTER, MON - das ist eine "
               "Datenlage-Grenze, keine Nachlaessigkeit), ZWEI ohne jede "
               "Quelle (CANTON, VSN)", "gilt", "Methodik 2.180"),
    Befundlage("2.180-spanne", "⚠️ Ein Qualitaetsverdacht wurde geprueft "
               "und AUSGERAEUMT: `gemessen` hat insgesamt in 6,6 % der "
               "Zeilen `high = low = close` - also keine Tagesspanne, "
               "womit ATR und `vola` dort wertlos waeren. Bei den 14 "
               "fraglichen Symbolen betraegt der Anteil aber 0,0 %. Die "
               "6,6 % betreffen andere Werte", "gilt", "Methodik 2.180"),
    Befundlage("2.180-vorrang", "⚠️⚠️ ENTSCHEIDUNG ZUR REIHENFOLGE: die "
               "GROESSERE Luecke ist die Frische. 518 von 524 "
               "Krypto-Reihen sind 18 Tage alt; neun Reihen zu "
               "ergaenzen, waehrend 518 veralten, waere die falsche "
               "Reihenfolge. Und die Auffrischung hat KEIN "
               "Qualitaetsproblem - dieselbe Quelle, dasselbe Werkzeug",
               "gilt", "Methodik 2.180"),
    Befundlage("2.179", "✔ DIE MELDELUECKE IST GESCHLOSSEN: "
               "`pruefe_neuaufnahme.py` prueft die drei "
               "Lebenszyklus-Faelle, die der Nutzer benannt hat - NEU "
               "(Watchlist/Bestand ohne Messreihe), FAELLT WEG (nur "
               "berichtet, KEIN Mangel wegen P6) und AENDERT SICH "
               "(Frische je Klasse). Dazu die Beitragslage der "
               "gehaltenen Werte. Als Suitepaket `Neuaufnahme` "
               "verdrahtet", "gilt",
               "Methodik 2.179 / pruefe_neuaufnahme.py"),
    Befundlage("2.179-rot", "⚠️⚠️ DAS PAKET IST ROT, UND DAS IST "
               "RICHTIG: 3 von 5 Pruefungen schlagen an. Ein Paket, das "
               "eine offene Luecke gruen faerbt, waere schlimmer als "
               "keines. Gruen wird es, wenn die acht Messreihen "
               "uebernommen und die Krypto-Basis nachgeladen ist",
               "gilt", "Methodik 2.179"),
    Befundlage("2.179-frische", "⚠️⚠️⚠️ DABEI GEFUNDEN: DIE "
               "KRYPTO-MESSBASIS IST ZU 99 % VERALTET. Die Median-Reihe "
               "endet am 21.08.2026 - 18 Tage alt; 518 von 524 Reihen "
               "sind aelter als sieben Tage. Nur SECHS Reihen (die am "
               "07.09. nachgeladenen) reichen bis heute. Die "
               "Nicht-Krypto-Klassen sind mit 5 Tagen aktuell", "gilt",
               "Methodik 2.179"),
    Befundlage("2.179-median", "⚠️ Und die Pruefung hat einen Fehler in "
               "SICH SELBST aufgedeckt: die erste Fassung nahm das "
               "MAXIMUM je Klasse und meldete 'krypto 1 Tag alt' - weil "
               "sechs frische Reihen die ganze Klasse frisch aussehen "
               "liessen. Der MEDIAN und der Anteil der Veralteten sind "
               "das richtige Mass. Dieselbe Fehlerklasse wie beim "
               "Stichprobenmedian in N-65", "gilt", "Methodik 2.179"),
    Befundlage("2.179-core", "⚠️ DREI KERNWERTE betroffen, nicht einer: "
               "CANTON (gehalten, `rolle=core`, NIRGENDS Daten), MORPHO "
               "(gehalten, `core`, 1.243 Zeilen in der Produktion) und "
               "HYPE (Watchlist, `core`, 572 Zeilen). Ich hatte zuerst "
               "nur CANTON gesehen", "gilt", "Methodik 2.179"),
    Befundlage("2.176", "⚠️⚠️⚠️ ACHT GEHALTENE KRYPTO-POSITIONEN HABEN "
               "KEINE MESSREIHE - und NICHTS meldet es. Betroffen: "
               "ASTER, BRETT, CANTON, KAS, MON, MORPHO, SUPRA, VSN. "
               "⚠️ CANTON hat `rolle=core` - ein KERNWERT ohne jede "
               "Kursreihe. Gefunden auf Nutzerhinweis 08.09.: 'neues "
               "Asset in der Watchlist oder neuer Coin-Bestand - die "
               "Daten zur Bewertung muessen vorhanden sein'", "gilt",
               "Methodik 2.176 / Audit 08.09."),
    Befundlage("2.176-vorhanden", "⚠️ SECHS DAVON HABEN HISTORIE IN DER "
               "PRODUKTIONS-DB, sie wurde nur nie in die Messbasis "
               "uebernommen: KAS 1.686 Zeilen · MORPHO 1.243 · BRETT "
               "854 · SUPRA 631 · ASTER 585 · MON 501. Zwei haben gar "
               "nichts: CANTON und VSN. Es ist also ueberwiegend ein "
               "UEBERNAHME-, kein Beschaffungsproblem", "gilt",
               "Methodik 2.176"),
    Befundlage("2.176-still", "⚠️⚠️ UND ES IST STILL: die acht sind in "
               "`messreihen` UND `messreihen_status` gar nicht gefuehrt, "
               "und es gibt KEINE Pruefung, die fehlende Messreihen fuer "
               "gehaltene Positionen meldet (im ganzen Baum kein "
               "Treffer). Werkzeuge zum Nachladen existieren "
               "(`lade_messreihen.py`), aber kein Automatismus bei "
               "Neuaufnahme", "gilt", "Methodik 2.176"),
    Befundlage("2.176-eurcv", "✔ EURCV gehoert NICHT in diese Liste "
               "(Nutzerhinweis 08.09.): es hat `ist_cash_aequivalent = "
               "True` und ist das Cash-Aequivalent, kein zu bewertender "
               "Coin. `asset_schalter.py` behandelt es gesondert und "
               "notiert den Datenmangel bereits. Es braucht einen PREIS "
               "fuer die Cash-Quote, aber keine Bewertung", "gilt",
               "Methodik 2.176"),
    Befundlage("2.177", "⚠️ AUFLAGE 2 GEPRUEFT - die Trennung Bewertung "
               "gegen Wirtschaftlichkeit ist im CODE sauber: "
               "`potential.py` rechnet ausdruecklich gebuehrenfrei "
               "('BEWERTUNG = ist das ein guter Trade, OHNE Gebuehren', "
               "`gebuehr_je_seite=0.0` ist kein Versehen), und "
               "`stop_relativ` geht nicht in die Quote ein - Stop 5 % "
               "und 25 % liefern beide 0,373033", "gilt",
               "Methodik 2.177"),
    Befundlage("2.177-etikett", "⚠️⚠️ ABER DIE STUFENBESCHRIFTUNG IST "
               "ALTBESTAND: `rollen_gate.STUFEN` nennt die zwoelfte "
               "Stufe 'Trefferquote schlaegt den Breakeven'. Seit U-1 "
               "(30.08.) entscheidet dort `potential.traegt()` - "
               "gebuehrenfrei. Der Kommentar darueber sagt es selbst "
               "('die alte Begruendung galt einem Modul, das an dieser "
               "Stelle nicht mehr steht'), aber das ETIKETT wurde nicht "
               "nachgezogen. Wer es liest, glaubt an einen "
               "Wirtschaftlichkeitsfilter, den es nicht gibt", "gilt",
               "Methodik 2.177 / Auflage 1"),
    Befundlage("2.178", "⚠️⚠️ AUFLAGE 3 BESTAETIGT (Nutzerhinweis): SPOT "
               "HAT IN DER BEWERTUNG KEINEN STOP. "
               "`messnorm.STOP_BEENDET` kennt nur hebel x einstieg und "
               "hebel x swing. ⚠️ ABER die Zielgroesse `bewegung_r` "
               "aller Messungen TEILT DURCH DIE STOPWEITE - sie normiert "
               "bei Spot durch eine Groesse, die die Bewertung dort "
               "nicht kennt. Dieselbe Fehlerklasse wie 2.172 (geliehene "
               "Geometrie); bei Krypto ist die Weite rund 0,75 ATR und "
               "damit ein brauchbarer Massstab, aber es gehoert benannt",
               "gilt", "Methodik 2.178"),
    Befundlage("2.178-instrument", "Und ein Nebenfund: `instrument = "
               "'hebel'` hat es in der NEUEN Kette nie gegeben - 3.513 "
               "spot, 11 absicherung, 0 hebel. Der Hebel entsteht als "
               "ETIKETT innerhalb von spot x einstieg, sobald "
               "`verlustanteil / stop_rel > 1`", "gilt",
               "Methodik 2.178"),
    Befundlage("2.175", "✔ N-11 DURCHGEFUEHRT: die Klassen in "
               "STREUUNGSEINHEITEN gemessen (in_r geteilt durch den IQA "
               "der eigenen Kandidatenwelt, Fenster ab 2018). Ergebnis: "
               "krypto `schnitt` +0,059 (1 von 4 Mengen) · themen_etf "
               "`vola` +0,062 (2 von 5) · rohstoffe `schnitt` +0,025 (0 "
               "von 2) · aktien `schnitt` und `vola` je +0,015 (0 von "
               "allen). `zufall` in jeder Klasse sauber", "gilt",
               "Methodik 2.175 / n80_streuungseinheiten.py"),
    Befundlage("2.175-aktien", "⚠️ DIE AKTIEN-EFFEKTE SIND RUND EIN "
               "VIERTEL VON KRYPTO (+0,015 gegen +0,059), nicht "
               "gleichauf. Meine Handrechnung hatte das Gegenteil "
               "nahegelegt - sie stand auf dem falschen Nenner. Der "
               "N-8-Nullbefund fuer Aktien bleibt damit ZURUECKGEZOGEN "
               "(die Messung war zu grob), aber die Effekte sind dort "
               "auch normiert klein", "gilt", "Methodik 2.175"),
    Befundlage("2.175-etf", "⚠️⚠️ DER STAERKSTE WERT DES GANZEN LAUFS "
               "ist `vola` bei THEMEN_ETF: +0,062 Streuungseinheiten und "
               "als einziger auf ZWEI von fuenf zulaessigen Mengen "
               "tragend - mehr als Krypto `schnitt` (1 von 4). ⚠️ Der "
               "Vorbehalt aus 2.170-etf bleibt: die Klasse hat effektiv "
               "nur 1,9 unabhaengige Reihen", "gilt", "Methodik 2.175"),
    Befundlage("2.175-robust", "⚠️ UND DER NUECHTERNE GESAMTBEFUND: KEIN "
               "Kandidat traegt in KEINER Klasse auf ALLEN zulaessigen "
               "Mengen. Krypto `schnitt` 1 von 4, ETF `vola` 2 von 5, "
               "alles andere 0. Nach der N-73-Regel ist damit keiner "
               "robust - auch nach der Normierung nicht", "gilt",
               "Methodik 2.175"),
    Befundlage("2.174", "⚠️⚠️⚠️ DAS HEBELKONZEPT IST NICHT GESCHEITERT - "
               "es wurde auf einer inzwischen GEFALLENEN Kalibrierung fuer "
               "gescheitert erklaert. Nutzervorgabe (F-220, woertlich): "
               "'die Wahrscheinlichkeit auf positives "
               "Chance-Risiko-Verhaeltnis soll den Hebel dynamisch "
               "erzeugen', Zielzone 2-5x", "gilt",
               "Methodik 2.174 / Recherche 08.09."),
    Befundlage("2.174-ist", "⚠️⚠️ WAS HEUTE GEBAUT IST: die Produktion "
               "rechnet `hebel_noetig = verlustanteil / stop_rel`. Die "
               "QUOTE geht NICHT ein - `agent/assetklassen.py` sagt es "
               "ausdruecklich ('es gibt keinen Zirkelbezug, hebel_noetig "
               "haengt an Verlustanteil'). Der Hebel entsteht aus der "
               "GEOMETRIE, nicht aus der Wahrscheinlichkeit. Die "
               "Nutzervorgabe ist damit NICHT umgesetzt", "gilt",
               "Methodik 2.174"),
    Befundlage("2.174-f220", "F-220 rechnete mit einem "
               "Kalibrierungsfaktor 0,195 und kam zu 'nur EINE Lage "
               "erreicht 2-5x'. ⚠️ Zwei Dinge dazu: (a) der Faktor ist am "
               "05.09. GEFALLEN - F-215s Kalibrierung besteht die "
               "Invarianzpruefung nicht (Verfuegbarkeits-Artefakt), und "
               "(b) er wird NIRGENDS IM CODE angewandt. Die Produktion "
               "rechnet unkalibriert. F-220 selbst ist am 06.09. "
               "zurueckgezogen", "gilt", "Methodik 2.174"),
    Befundlage("2.174-neu", "✔✔ UNKALIBRIERT MIT DER HEUTIGEN "
               "BEITRAGSLAGE GERECHNET (Kapital 10.000, Einsatz 500, "
               "Stop 5 %, halbes Kelly, CRV 2,0) FUNKTIONIERT DIE "
               "DYNAMISCHE ERZEUGUNG: kein Beitrag 0,00x · mittlere Lage "
               "1,02x · nur funding bestes 3,90x · bestes funding + "
               "mittleres turnover 4,56x · nur turnover bestes 9,45x · "
               "beide bestes 13,35x. ZWEI Lagen liegen in der Zielzone "
               "2-5x, und die Abstufung ist echt", "gilt",
               "Methodik 2.174"),
    Befundlage("2.174-grenzen", "⚠️ ZWEI EINSCHRAENKUNGEN, benannt: (1) "
               "die Spitze 13,35x braucht den vorhandenen Deckel "
               "`GRENZEN['hebel_max']` = 10,0. (2) Die Abstufung SPRINGT "
               "von 1,02x auf 3,90x - zwischen 'kein Hebel' und 'fast "
               "4x' liegt nichts. Ursache ist die grobe "
               "Fuenftel-Aufloesung der Beitraege. Fuer eine feine "
               "Zielzone 2-5x reicht sie nicht", "gilt",
               "Methodik 2.174"),
    Befundlage("2.173", "⚠️⚠️ ZWEI EIGENE FEHLDARSTELLUNGEN ZUM "
               "STRATEGIESTAND, vom Nutzer korrigiert (08.09.). Ich hatte "
               "gesagt, `swing` und `hebel` haetten 'keine Beitraege' und "
               "das als Luecke dargestellt. Beides war falsch "
               "eingeordnet", "gilt",
               "Methodik 2.173 / Nutzerkorrektur 08.09."),
    Befundlage("2.173-swing", "`swing` IST KEINE LUECKE, SONDERN "
               "GESTRICHEN. `Anforderungen_Umbau_28_08.md`: 'hebel x "
               "swing entfaellt (Nutzerentscheidung 31.08.: nur Einstieg "
               "reicht)' und 'spot x swing ist ausdruecklich gestrichen'. "
               "Begruendung dort: bei 1-20 Tagen Horizont ist der "
               "praktische Unterschied zu `einstieg` klein, und Swing "
               "verlangt ein eigenes Ausstiegswerk", "gilt",
               "Methodik 2.173"),
    Befundlage("2.173-hebel", "⚠️⚠️ DER HEBEL BEKOMMT SEHR WOHL EINE "
               "BEWERTUNG - sie ist nur nicht vom Spot UNTERSCHEIDBAR. "
               "Im Code geprueft: `wahrscheinlichkeit.Beitrag` hat die "
               "Felder klassen/strategien/richtungen, aber KEIN "
               "`instrumente`. Und `rechne()` liefert bei Stop 6,4 % "
               "gegen 2,5 % und mit Finanzierung 0,02 R dreimal EXAKT "
               "dieselbe Quote 0,373033. Das ist der Befund vom 01.09. "
               "('die Bewertung hat keine Instrument-Achse'), nicht "
               "'keine Bewertung'", "gilt", "Methodik 2.173"),
    Befundlage("2.173-regel2", "Nebenbei belegt: `rechne()` rechnet "
               "`kosten_r` aus Gebuehr und Finanzierung, laesst sie aber "
               "NICHT in die Quote einfliessen. Regel 2 (Gebuehren "
               "gehoeren nicht in die Bewertung) ist im Code korrekt "
               "umgesetzt", "gilt", "Methodik 2.173"),
    Befundlage("2.173-amihud", "⚠️ UND EINE LUECKE IN MEINER EIGENEN "
               "N-76-ARBEIT: ich habe `amihud` nur als NIVEAU gemessen "
               "(feste Baender, Regel-3-konform). F-228 hatte die "
               "VERAENDERUNG als Hebel-Kandidaten benannt. ⚠️ F-228 ist "
               "zwar am 06.09. selbst zurueckgezogen (gemessen auf 'Ziel "
               "vor Stop' und/oder der freien Menge) - aber die Frage "
               "nach der VERAENDERUNG ist damit weder bestaetigt noch "
               "widerlegt. `messe_fremdgroesse.py` trennt beides "
               "ausdruecklich: NIVEAU = Eigenschaft, VERAENDERUNG = LAGE",
               "gilt", "Methodik 2.173"),
    Befundlage("2.172", "⚠️⚠️ DIE ZIELGROESSE `bewegung_r` IST UEBER DIE "
               "ASSETKLASSEN NICHT VERGLEICHBAR - und das entwertet den "
               "N-8-Nullbefund. Sie teilt durch max(5 % Kurs, 0,75 ATR). "
               "Gemessen ab 2018: der Boden bindet bei Krypto in 29,1 % "
               "der Anker, bei AKTIEN in 97,1 %, bei THEMEN_ETF in "
               "99,2 %, bei Rohstoffen in 97,4 %. Der Stop liegt dort "
               "2,29 / 4,43 / 2,50 ATR entfernt statt 0,75", "gilt",
               "Methodik 2.172 / Nutzerhinweis 08.09."),
    Befundlage("2.172-streuung", "„In Streuungseinheiten liegen die "
               "Effekte fast gleichauf - Aktien 0,038, Rohstoffe "
               "0,070\"", "abgeloest", "Methodik 2.172",
               abgeloest_durch="2.175",
               warum="HANDRECHNUNG mit dem falschen Nenner: ich habe "
                     "durch die Streuung der GANZEN Klasse geteilt, "
                     "gemessen wird aber die Kandidatenwelt (bei "
                     "Rohstoffen IQA 4,775 statt 1,715). Sauber "
                     "gemessen (N-80): Aktien +0,015, Rohstoffe +0,025 "
                     "gegen Krypto +0,059"),
    Befundlage("2.172-untermacht", "⚠️⚠️ DAMIT IST DER AKTIEN-BEFUND "
               "UNTERMACHT, KEIN NULLBEFUND. Ein Effekt der "
               "Krypto-Groesse haette in Aktien +0,0915 R ergeben - die "
               "Trennschaerfe lag bei 0,05 bis 0,10 R, also genau an der "
               "Grenze. Gemessen wurden +0,0725. Die Messung KONNTE "
               "dort nichts zeigen", "gilt", "Methodik 2.172"),
    Befundlage("2.172-etf", "⚠️ Und der ETF-Befund wird dadurch nicht "
               "kleiner, sondern GROESSER: `vola` liegt dort bei 0,254 "
               "Streuungseinheiten (5 %: 0,322) - das FUENFFACHE des "
               "staerksten Krypto-Effekts. Der Vorbehalt aus 2.170-etf "
               "bleibt (1 von 5 Mengen, effektiv 1,9 unabhaengige "
               "Reihen), aber die Groesse verdient eine eigene Messung",
               "gilt", "Methodik 2.172"),
    Befundlage("2.172-lehre", "⚠️ DIE LEHRE: eine Zielgroesse, die durch "
               "eine GEOMETRIE normiert, ist nur dort vergleichbar, wo "
               "die Geometrie gleich wirkt. Der 5-%-Boden ist fuer "
               "Krypto gebaut (ATR/Kurs 8,6 %) und bindet dort selten; "
               "bei Aktien (2,2 %) und ETF (1,1 %) bindet er fast "
               "immer. Wer Klassen vergleicht, muss die Effekte in "
               "EIGENEN Streuungseinheiten ausdruecken - oder die "
               "Geometrie je Klasse kalibrieren", "gilt",
               "Methodik 2.172"),
    Befundlage("2.170-rohstoffe", "ROHSTOFFE sind NICHT MESSBAR: 35 "
               "Symbole, 28,8 Werte je Tag, nur `50%` und `frei` "
               "zulaessig - und dort lautet JEDES Urteil 'KEIN BEFUND'. "
               "Die Norm sagt es selbst. Das ist eine Datenlage-Aussage, "
               "keine Bewertung", "gilt", "Methodik 2.170"),
    Befundlage("2.170-etf", "⚠️ THEMEN_ETF: `vola` traegt bei 10 % "
               "(+0,2303 [+0,0993 .. +0,3712]) und zeigt einen MONOTON "
               "fallenden Verlauf ueber alle fuenf Mengen (+0,2911 / "
               "+0,2303 / +0,0919 / +0,0382 / +0,0287) - ein Effekt, der "
               "auf die selektiertesten Werte konzentriert ist. Kein "
               "Mengenartefakt: `zufall` zeigt in KEINER Klasse einen "
               "fallenden Verlauf", "gilt", "Methodik 2.170"),
    Befundlage("2.170-etf-vorbehalt", "⚠️⚠️ ABER DER ETF-BEFUND STEHT "
               "AUF DUENNEM EIS: nur 1 von 5 Mengen erreicht 'TRAEGT' "
               "(N-73-Regel: nicht robust), UND die Klasse hat die "
               "hoechste Querschnittskorrelation aller vier - im Mittel "
               "0,527 gegen 0,209 bei Aktien. Das entspricht effektiv "
               "1,9 unabhaengigen Reihen. 293 Themen-ETF halten "
               "grossteils DIESELBEN Aktien; der Blockbootstrap "
               "behandelt Zeit-, nicht Querschnittsabhaengigkeit",
               "gilt", "Methodik 2.170"),
    Befundlage("2.170-g6", "WAS FUER G-6 FOLGT: die Sperre der vier "
               "Klassen nach DATENLAGE bleibt begruendet. Fuer Aktien "
               "und Rohstoffe gibt es keinen tragenden Beitrag, bei "
               "Themen-ETF nur einen nicht robusten Hinweis. ⚠️ Die "
               "Sperre ist damit nicht mehr nur 'nach Datenlage' - fuer "
               "Aktien ist sie jetzt GEMESSEN begruendet", "gilt",
               "Methodik 2.170"),
    Befundlage("2.170-fenster", "Das gemeinsame Fenster ab 2018-01-01 "
               "stand VOR der Messung fest und ist vom Nutzer bestaetigt: "
               "'zu den daten ab 1972 - auch hier aehnlich wie bei "
               "krypto, waere ich der Meinung sollte man vorsichtig "
               "sein'. Ohne es haette man Krypto ab 2017 gegen Aktien ab "
               "1972 gestellt - und Aktien haetten mit 211 gegen 42 "
               "Bloecken allein durch Aussagekraft besser ausgesehen",
               "gilt", "Methodik 2.170"),
    Befundlage("2.169", "⛔ N-9 ERLEDIGT: KEINER DER VIER "
               "TERMINMARKT-KANAELE TRAEGT AUF `bewegung_r`. "
               "`oi_je_umsatz` 0 von 3 zulaessigen Mengen, `long_bias` 0 "
               "von 3, `top_bias` 0 von 2, `taker_bias` 0 von 3. Die "
               "Referenz `oi_aenderung` dagegen 3 von 3 - ihr Band "
               "schliesst in JEDER Menge die Null aus (+0,0469 / +0,0243 "
               "/ +0,0145). `zufall` traegt auf keiner", "gilt",
               "Methodik 2.169 / n78_terminmarkt_kanaele.py"),
    Befundlage("2.169-zielgroesse", "⚠️⚠️ DAMIT UEBERTRAGEN SICH DIE "
               "N-17b-BEFUNDE NICHT. Dort trugen `oi_je_umsatz`, "
               "`long_bias` und `top_bias` - aber gegen FRONTLOADING, "
               "eine andere Zielgroesse. Genau diese Verwechslung hat "
               "F-207 schon einmal erzeugt. Ein Kandidat, der die "
               "Frontloading-Quote verschiebt, verbessert deshalb nicht "
               "das ERGEBNIS", "gilt", "Methodik 2.169"),
    Befundlage("2.169-redundanz", "Zwei Redundanzen sauber gemessen, "
               "beide INNERHALB der Auswahl: `oi_je_umsatz` gegen "
               "`turnover` -0,490 - beide sind umsatznormiert, das ist "
               "eine echte Ueberschneidung. Und `long_bias` gegen "
               "`top_bias` +0,950, was N-17b (+0,955) exakt "
               "REPRODUZIERT. Die drei uebrigen Paare liegen unter "
               "0,16", "gilt", "Methodik 2.169"),
    Befundlage("2.169-gesamt", "⚠️ DER GESAMTBEFUND: mit den vorhandenen "
               "Daten gibt es keinen vierten Beitrag AUS DEN GEPRUEFTEN "
               "QUELLEN. Kursreihe erschoepft (2.168), Terminmarkt "
               "erschoepft (nur `oi_aenderung` traegt), onchain liefert "
               "`turnover`, Binance liefert `funding`", "gilt",
               "Methodik 2.169"),
    Befundlage("2.169-korrektur", "⚠️⚠️ EINSCHRAENKUNG, am selben Abend "
               "gefunden: 'alle Quellen erschoepft' war ZU WEIT gefasst. "
               "Die Durchsicht des Datenbestands (auf Nutzerhinweis) "
               "zeigt zwei weitere Quellen, die es gibt und die gemessen "
               "WURDEN - aber unter der ALTEN Norm vom 30.08., vor den "
               "heutigen Mengenregeln: `tvl_historie` (188 Symbole, "
               "261.406 Zeilen, ab 2018-02) und `adractcnt` - aktive "
               "Adressen (66 Symbole, 203.378 Zeilen, ab 2013-01), beide "
               "in `messe_fremdgroesse.py`. Sie gehoeren unter der "
               "heutigen Norm nachgemessen - das ist ein OFFENER Punkt, "
               "kein erledigter", "gilt", "Methodik 2.169"),
    Befundlage("2.168", "⛔ N-6 IST FALSCH GESTELLT UND WIRD "
               "GESTRICHEN. Die Abdeckungsluecke ist kein "
               "BETRIEBSproblem: ueber die Watchlist mit k=2 haben nur "
               "4,2 % der gewaehlten Anker keinen Beitrag, und das sind "
               "FLOKI und XNO. ⚠️ Nutzervorgabe 07.09. woertlich: bei "
               "Meme- und Smallcap-Werten ist eine fehlende Bewertung "
               "'als UNKRITISCH zu bewerten'", "gilt",
               "Methodik 2.168 / n77_ist_die_abdeckung_repraesentativ.py"),
    Befundlage("2.168-mess", "Als MESSfrage ist die Luecke groesser: auf "
               "der Messbasis haben 32,4 % der gewaehlten Anker keinen "
               "Beitrag. Geprueft, ob die abgedeckte Teilmenge deshalb "
               "verzerrt: `schnitt` und `vola` (beide 100 % Abdeckung) "
               "zeigen zwischen den Gruppen -0,0774 bzw. -0,0885, beide "
               "Baender schliessen null ein. ⚠️ ABER die Trennschaerfe "
               "liegt bei 0,10 R - groesser als die Effekte, um die es "
               "geht (0,02 bis 0,09 R). Also NICHT ENTSCHIEDEN auf der "
               "Aufloesung, die zaehlen wuerde", "gilt",
               "Methodik 2.168"),
    Befundlage("2.168-kontrolle", "⚠️⚠️ Und die Kontrolle hat einen "
               "eigenen Fehler gefangen: der erste Anlauf differenzierte "
               "die ROHEN Tagesreihen der beiden Gruppen. Bei 35 gegen "
               "20 Ankern je Tag ist die N-65-Verzerrung UNGLEICH - "
               "`zufall` zeigte prompt einen 'Unterschied' von -0,0212 "
               "[-0,0417 .. -0,0038]. Mit je Gruppe entzerrten Reihen: "
               "-0,0056, Band schliesst null ein", "gilt",
               "Methodik 2.168"),
    Befundlage("2.168-erschoepft", "⚠️⚠️ WARUM EIN NEUER "
               "KURSREIHEN-BEITRAG NICHT DIE ANTWORT IST: die "
               "Kombinationsmatrix vom 27.08. hat es bereits "
               "festgehalten - von 17 Merkmalen sind M2 bis M12 und M15 "
               "bis M17 ALLE aus Kurs, Volumen oder Modellantwort "
               "abgeleitet. 'Die Information steckt nicht in den "
               "Kursdaten. Wer nur Kursreihen kombiniert, kombiniert "
               "Ableitungen derselben Quelle.' Die heutige Durchsicht "
               "bestaetigt das: schnitt, vola, rsi, amihud, momentum, "
               "schnitt50 sind alle gemessen, keiner traegt robust",
               "gilt", "Methodik 2.168"),
    Befundlage("2.168-quellen", "DIE BEIDEN ECHTEN FREMDQUELLEN, "
               "geprueft: M13 Terminmarkt ist REALISIERT (122 Symbole, "
               "1.734 Tage bis 02.09.2026) - deckt aber nur 122 von 524 "
               "ab und schliesst die Luecke NICHT. M14 "
               "Entwickleraktivitaet: das Messwerkzeug existiert, aber "
               "in KEINER Datenbank liegt eine Tabelle dazu. ⚠️ Es gibt "
               "derzeit keine verfuegbare Quelle, die die Luecke "
               "schliessen wuerde", "gilt", "Methodik 2.168"),
    Befundlage("2.168-offen", "⚠️ WAS STATTDESSEN OFFEN IST, ohne neue "
               "Datenquelle: der Terminmarkt liefert VIER weitere "
               "Kanaele, die nicht registriert sind - `oi_wert`, "
               "`long_bias`, `top_bias`, `taker_bias`, je 122 Symbole "
               "und rund 1.400 bis 1.736 Tage. Zwei davon (long_bias, "
               "top_bias) sind in N-17b als nicht unabhaengig vom RSI "
               "gemessen; `oi_wert` und `taker_bias` nie unter der Norm",
               "gilt", "Methodik 2.168"),
    Befundlage("2.167", "⛔ `amihud` TRAEGT AUCH AN DER POSITIONSGROESSE "
               "NICHT - aber jetzt mit einem GRUND, nicht als "
               "Nullbefund. Zwei Hypothesen, beide gemessen, beide "
               "verneint: der Stop rutscht nicht, und die Mehrstreuung "
               "liegt auf der falschen Seite", "gilt",
               "Methodik 2.167 / n76_amihud_an_der_groesse.py"),
    Befundlage("2.167-luecke", "⚠️⚠️ DER STOP-DURCHSCHLAG EXISTIERT IN "
               "KRYPTO PRAKTISCH NICHT: 71 Faelle von 728.920 Ankern "
               "(0,0097 %). Der Grund generalisiert - KRYPTO HANDELT "
               "DURCHGEHEND. Ein Kurstag, der GANZ unter dem Stop liegt, "
               "verlangt eine Uebernachtluecke, und die gibt es an einem "
               "24/7-Markt nicht. Die Kontrolle (gemischt) liefert "
               "15/10/20/14 gegen echte 0/14/18/28/11 - nicht "
               "unterscheidbar", "gilt", "Methodik 2.167"),
    Befundlage("2.167-rm1", "✔✔ DARAUS FOLGT ETWAS NUETZLICHES, "
               "unabhaengig von amihud: RM-1 rechnet "
               "`max_position = risk_budget / (stop_abstand / kurs)` und "
               "SETZT VORAUS, DASS DER STOP HAELT. Fuer Krypto ist diese "
               "Annahme belegt - in 99,99 % der Anker war der Stop zum "
               "Stoppreis handelbar", "gilt", "Methodik 2.167"),
    Befundlage("2.167-open", "⚠️⚠️ KORREKTUR 07.09. abends: N-76 nannte "
               "als Vorbehalt 'ohne Eroeffnungskurs ist nur nachweisbar, "
               "was den GANZEN Tag unter dem Stop lag'. DIE SPALTE `open` "
               "GIBT ES - in `price_history_ohlc`, zu 100 % gefuellt, in "
               "ALLEN vier Assetklassen. Nur "
               "`messe_eigenschaft_beitrag.lade()` liest sie nicht. Der "
               "Stop-Durchschlag waere damit EXAKT messbar statt "
               "konservativ genaehert - gefunden erst, als der Nutzer "
               "eine Durchsicht des Datenbestands verlangte", "gilt",
               "Methodik 2.167 / Datenbestandsdurchsicht 07.09."),
    Befundlage("2.167-seite", "⚠️⚠️ DIE ZWEITE HYPOTHESE (illiquide Werte "
               "streuen breiter, also kleiner dimensionieren) IST "
               "WIDERLEGT - und zwar an der SEITE. Der "
               "Interquartilsabstand steigt zwar (3,251 -> 3,780 gegen "
               "eine Kontrollspanne von nur 0,027), aber er steigt "
               "VOLLSTAENDIG NACH OBEN: P75-Median 1,342 -> 2,054, "
               "waehrend Median-P25 von 1,909 auf 1,727 FAELLT. Auf der "
               "VERLUSTSEITE sind illiquide Werte enger. Kleiner zu "
               "dimensionieren waere unbegruendet", "gilt",
               "Methodik 2.167"),
    Befundlage("2.167-geometrie", "Der naheliegende Einwand wurde "
               "geprueft und AUSGERAEUMT: der 5-%-Boden koennte bei "
               "ruhigen Werten oefter binden und die kleinere "
               "R-Streuung erzeugen. Gemessen bindet er bei Band 0 in "
               "38,2 % und bei Band 4 in 38,5 % der Anker, ATR/Kurs "
               "0,0790 gegen 0,0752 - praktisch gleich. Der Unterschied "
               "ist echt, nur zeigt er nach oben", "gilt",
               "Methodik 2.167"),
    Befundlage("2.167-ausgabe", "⚠️ ZWEI EIGENE AUSGABEFEHLER, beide "
               "zwischen Ergebnis und Deutung gefangen (Methodik 2.80): "
               "'Durchschlag 0,0 %' war GERUNDET statt null - die "
               "Mittelwerte standen auf 11 Faellen, ohne dass die Zahl "
               "dastand. Und die STANDARDABWEICHUNG als Streuungsmass "
               "lag bei 250, getragen von 0,06 % der Anker (ein Coin, "
               "der sich in 20 Tagen verzwanzigfacht, ergibt bei 5 % "
               "Stopweite 400 R). Beides ersetzt durch absolute Zahlen "
               "und den Interquartilsabstand", "gilt", "Methodik 2.167"),
    Befundlage("2.166", "DIE DURCHSICHT DER GEFALLENEN BEITRAEGE: bei "
               "VIER von fuenf ist ein Messfehler ausgeschlossen. `rsi` "
               "und `amihud` tragen auf KEINER Achse (quer wie laengs) "
               "und ueber alle zulaessigen Mengen (N-73) - sie sind "
               "sauber abgelehnt. `schnitt` ist vierfach geprueft. "
               "Offen bleibt allein `H`", "gilt",
               "Methodik 2.166 / n75_quer_gegen_laengs.py"),
    Befundlage("2.166-these", "⚠️ MEINE THESE WAR: die Beitragsmaschinerie "
               "rangt INNERHALB DES TAGES, ist also rein "
               "querschnittlich - Kandidaten mit Zeitreihen-Natur (`H`, "
               "`rsi`, `schnitt`) waeren mit dem falschen Instrument "
               "gemessen. GEMESSEN UND WIDERLEGT: kein Kandidat traegt "
               "NUR laengs. Kontrollen halten - `zufall` traegt auf "
               "keiner Achse, `funding` (ein CS-Signal) ist quer "
               "staerker als laengs (+0,0229 gegen +0,0011), wie es "
               "muss", "gilt", "Methodik 2.166"),
    Befundlage("2.166-momentum", "⚠️⚠️ AUSNAHME `momentum`: sein Urteil "
               "'traegt nicht' ist NICHT INTERPRETIERBAR. Spearman "
               "+0,930 zur Auswahlgroesse `momentum250` der Stufe 5 - er "
               "wird auf der Menge gemessen, die er selbst definiert. "
               "Das ist kein Befund ueber Momentum, sondern eine "
               "Tautologie. Er sitzt bereits an Stufe 5", "gilt",
               "Methodik 2.166"),
    Befundlage("2.166-h", "⚠️ `H` IST DER EINZIGE, BEI DEM EIN "
               "MESSFEHLER OFFEN BLEIBT. Er braucht Marken, Stop und "
               "Ziel - nicht nur Kursreihen - und laesst sich deshalb "
               "durch `messe_kandidaten_als_regel` gar nicht messen. "
               "Sein Fall beruht auf gepoolt (+4,5) gegen je Tag "
               "(-1,02). ⚠️ Und er ist ein ABSOLUTES Kriterium je Asset, "
               "waehrend die Maschinerie querschnittlich rangt - "
               "`messe_h_als_filter` nennt genau das im eigenen Kopf",
               "gilt", "Methodik 2.166"),
    Befundlage("2.166-woanders", "WO EIN GEFALLENER SINNVOLL WAERE: "
               "`amihud` misst Illiquiditaet - das ist eine Frage der "
               "AUSFUEHRBARKEIT und POSITIONSGROESSE (wieviel laesst "
               "sich handeln, ohne den Kurs zu bewegen), nicht der "
               "Richtung. Dort nie geprueft. `schnitt` traegt auf der "
               "VERBILLIGUNG bei H90 (+0,0292, im flachsten Fuenftel "
               "+0,0481) - das ist die AKKUMULATION, nicht `einstieg`. "
               "⚠️ Kein Widerspruch zu 2.164: andere Zielgroesse, "
               "anderer Horizont", "gilt", "Methodik 2.166"),
    Befundlage("2.166-register", "⚠️ Beim Durchsehen gefunden: das "
               "`live`-Feld von `turnover` nannte noch die am 07.09. "
               "ZURUECKGENOMMENEN Stufen (+0,33 x3 / -0,48 x2) - "
               "waehrend die `warnung` desselben Eintrags die Ruecknahme "
               "beschrieb. Das Blatt widersprach sich selbst und dem "
               "Code. Die Selbstpruefung fing es nicht: sie prueft nur, "
               "OB ein Merkmal vorkommt. Jetzt vergleicht sie die ZAHLEN "
               "(scharf getestet)", "gilt", "Methodik 2.166"),
    Befundlage("2.165", "✔✔ N-7 ERLEDIGT: `turnover`s STUFEN SIND "
               "RICHTIG. Entzerrt nachgerechnet ergibt der Querschnitt "
               "+3,13 / +0,76 / +0,22 / -1,73 / -2,38 gegen registriert "
               "+3,15 / +0,83 / +0,22 / -1,79 / -2,40 - Abweichung "
               "hoechstens 0,07 Punkte. Monoton, Spanne +5,51 gegen "
               "+5,55. Kontrolle `zufall` bei maximal 0,38 Punkten. "
               "R-R11 vorab erfuellt: `rechne_turnover_beitrag.py` "
               "reproduziert die Tabelle exakt", "gilt",
               "Methodik 2.165 / n74_turnover_stufen_nachgerechnet.py"),
    Befundlage("2.165-warum", "⚠️ WARUM DIE ENTZERRUNG HIER NICHTS "
               "AENDERT, bei `schnitt` aber alles: im Querschnitt sind "
               "die Fuenftel GLEICH GROSS (9,0 bis 9,8 Anker je Tag). "
               "Die Verzerrung aus N-65 trifft alle fuenf gleich und "
               "hebt sich im Bezug auf den Mittelwert der fuenf auf. Bei "
               "`schnitt` auf der selektierten Menge hatte Fuenftel 0 "
               "dagegen 1,49 Anker und Fuenftel 4 dann 29,35", "gilt",
               "Methodik 2.165"),
    Befundlage("2.165-auswahl", "⚠️ Auf der AUSWAHL (50 %) waere die "
               "Tabelle um 25 % steiler: +4,04 / +0,96 / -0,04 / -2,06 "
               "/ -2,90, Spanne +6,94. Das passt zur Richtung aus N-73 "
               "(Wirkung dort 48 % staerker). ⚠️ ABER: die Fuenftel "
               "haben dort nur 3,9 bis 5,2 Anker, und die Auswahl nach "
               "momentum250 ist nur ein STELLVERTRETER fuer die Werte, "
               "die in der Kette wirklich bis zur Bewertung kommen. Die "
               "registrierte Tabelle UNTERSCHAETZT also - und "
               "unterschaetzen ist die sichere Richtung", "gilt",
               "Methodik 2.165"),
    Befundlage("2.165-entscheidung", "EMPFEHLUNG: Tabelle NICHT aendern. "
               "Sie reproduziert, ist monoton, haelt der Entzerrung "
               "stand und ihre Ableitungsbasis (voller Querschnitt) ist "
               "GENAU die, auf der `marktrang` auch in der Produktion "
               "rangt. Die steilere Variante stuende auf duennerer "
               "Besetzung und einem Stellvertreter - und loeste R-R9 "
               "aus (Neukalibrierung der Schwelle 0,080) ohne belegten "
               "Gewinn", "gilt", "Methodik 2.165"),
    Befundlage("2.164", "✔✔ DIE DURCHSICHT ALLER KANDIDATEN (N-5) ist "
               "durch und faellt BERUHIGEND aus: von zehn Kandidaten "
               "aendern nur ZWEI ihr Urteil mit der Menge. `amihud`, "
               "`rsi`, `schnitt50`, `vola`, `momentum` und `funding` "
               "urteilen ueber alle Mengen gleich - ihre Befunde stehen. "
               "`zufall` traegt auf keiner Menge", "gilt",
               "Methodik 2.164 / n73_durchsicht_kandidaten.py"),
    Befundlage("2.164-turnover", "„`turnover` traegt auf 50 % "
               "(+0,0909, Urteil TRAEGT) und ist damit voll "
               "rehabilitiert\"", "abgeloest", "Methodik 2.164",
               abgeloest_durch="2.187",
               warum="R-R11 auf der NEUEN Messbasis (08.09., 536 "
                     "Symbole): die WIRKUNG reproduziert auf drei "
                     "Stellen (+0,0913 gegen +0,0909), aber das URTEIL "
                     "auf 50 % ist jetzt 'NICHT TRENNBAR' - der "
                     "Nullpunkt hat sich in das Band geschoben. ⚠️ "
                     "`turnover` traegt weiterhin, aber auf `frei` "
                     "(+0,0639, TRAEGT), nicht auf 50 %"),
    Befundlage("2.164-schnitt", "⚠️⚠️ `schnitt` IST NICHT ROBUST: "
               "zulaessig sind {10 %, 20 %, 50 %, frei}, aber er traegt "
               "NUR bei 20 % (+0,1759 [+0,0715 .. +0,2907]). Bei 10 % "
               "steht fast derselbe Punktschaetzer (+0,1780) mit "
               "breiterem Band [+0,0274 .. +0,3361] - 'nicht trennbar'. "
               "Der N-59-Befund haengt an der Wahl 20 %", "gilt",
               "Methodik 2.164"),
    Befundlage("2.164-regel", "⚠️ UND EIN DENKFEHLER IN DER EIGENEN "
               "REGEL, von der Durchsicht aufgedeckt: die SCHMALSTE "
               "zulaessige Menge ist zugleich die RAUSCHENDSTE. Sie zum "
               "alleinigen Massstab zu machen bestraft Kandidaten mit "
               "guter Abdeckung. Richtig: die Zulaessigkeit sortiert aus, "
               "was zu duenn ist - das URTEIL muss ueber ALLE "
               "zulaessigen Mengen halten. Gebaut als "
               "`zulaessige_mengen()`", "gilt", "Methodik 2.164"),
    Befundlage("2.163", "⚠️⚠️ DIE ZEITSTABILITAET, korrekt gemessen: "
               "jeder Beitrag auf SEINER Menge, Trennschaerfe ZENTRIERT. "
               "`oi_aenderung` stabil bis 0,05 R (-0,0051), `turnover` "
               "und `funding` stabil bis 0,10 R (+0,0256 / +0,0415), "
               "`zufall` stabil bis 0,05 R. ⚠️ `schnitt` auf 10 %: "
               "-0,0647 [-0,3098 .. +0,2161] bei einer Trennschaerfe von "
               ">0,20 R - UNENTSCHIEDEN, weder stabil noch instabil "
               "nachgewiesen", "gilt", "Methodik 2.163"),
    Befundlage("2.163-schnitt", "Fuer `schnitt` bleibt das PRAKTISCHE "
               "Ergebnis unveraendert, aber der Grund ist schwaecher: "
               "nicht 'instabil belegt', sondern 'nichts davon "
               "entscheidbar'. Die Stufen sind nicht monoton (2.158), "
               "die heutige Wirkung nicht trennbar (+0,1152 [-0,0377 .. "
               "+0,2687] ab 2022 auf 10 %), die Stabilitaet "
               "unentschieden. ⚠️ Drei offene Fragen sind keine "
               "Bauentscheidung", "gilt", "Methodik 2.163"),
    Befundlage("2.163-massstab", "⚠️⚠️ UND EIN BEFUND UEBER `schnitt` "
               "SELBST: sein Haelftenunterschied DREHT mit der Menge "
               "(+0,2238 bei 20 %, -0,0647 bei 10 %). Bei `funding` "
               "(+0,0473 / +0,0415) und `zufall` (-0,0083 / -0,0229) "
               "tut er das NICHT. Eine Groesse, deren Vorzeichen am "
               "Messfenster haengt, ist keine verlaessliche Grundlage - "
               "das ist die stehende Vorgabe 'der Massstab entscheidet "
               "das Vorzeichen', hier zum wiederholten Mal", "gilt",
               "Methodik 2.163"),
    Befundlage("2.163-anker", "R-R11 nach dem Umbau: alle SIEBEN Anker "
               "aus `messbasis_anker.json` reproduzieren auf fuenf "
               "Stellen. Das Hinzufuegen von `50%` und "
               "`menge_nach_datenlage` hat keine bestehende Messung "
               "verschoben", "gilt", "Methodik 2.163"),
    Befundlage("2.160-heute", "⛔⛔ UND ER TRAEGT HEUTE NICHT MEHR "
               "NACHWEISBAR - weder allein noch in der Kette. Allein: ab "
               "2022 +0,0414 [-0,0307 .. +0,1002], ab 2023 +0,0478, ab "
               "2024 +0,0855 - kein Band schliesst null aus. In der "
               "Kette: ab 2022 +0,0165, ab 2023 +0,0216, ab 2024 +0,0264 "
               "- ebenfalls keines", "gilt",
               "Methodik 2.160 / n69_traegt_er_heute_noch.py"),
    Befundlage("2.160-kontrolle", "⚠️⚠️ UND ES LIEGT NICHT AN DER "
               "MESSDAUER: `funding` traegt in DENSELBEN Fenstern - ab "
               "2022 +0,0157 [+0,0043 .. +0,0318], ab 2023 +0,0170, ab "
               "2024 +0,0182 - mit einem KLEINEREN Effekt als `schnitt`. "
               "`schnitt`s Baender sind rund fuenfmal breiter: der "
               "Effekt ist gross, aber zu unruhig", "gilt",
               "Methodik 2.160"),
    Befundlage("2.160-epoche", "Der Jahresverlauf zeigt die Quelle: 2019 "
               "+0,4532 / 2020 +0,5100 / 2021 +0,3440 / 2022 +0,0187 / "
               "2023 -0,0498 / 2024 +0,1603 / 2025 +0,1280 / 2026 "
               "-0,1158. ⚠️ `funding` zeigt DASSELBE Muster schwaecher "
               "(2020 +0,2876, danach +0,01 bis +0,03) - ein Teil "
               "gehoert der EPOCHE, nicht dem Kandidaten: der fruehe "
               "Kryptomarkt war ineffizienter", "gilt", "Methodik 2.160"),
    Befundlage("2.160-genauigkeit", "⚠️ WAS NICHT GESAGT IST: 'traegt "
               "heute nicht NACHWEISBAR' ist nicht 'traegt nicht'. Die "
               "Trennschaerfe liegt allein bei 0,10 R und in der Kette "
               "bei 0,05 R; die gemessenen Werte liegen darunter. Es ist "
               "UNENTSCHIEDEN, nicht widerlegt - aber eine "
               "Bauentscheidung braucht einen Nachweis, keine offene "
               "Frage. Das Fenster ab 2024 hat zudem nur 15 Bloecke und "
               "verfehlt die eigene 20er-Regel", "gilt",
               "Methodik 2.160"),
    Befundlage("2.160-methode", "Und WARUM N-60 nicht weiterkam: es "
               "fragte 'traegt er in A?' UND 'traegt er in B?' - zwei "
               "halbierte Tests. Die richtige Frage ist EINE: 'ist (A-B) "
               "von null zu trennen?' auf der ganzen Reihe. Der Test "
               "wurde auf Kunstdaten geeicht (40 Laeufe je Fall): 18 % "
               "Fehlalarm bei Wahrheit null statt nominell 10 %, 100 % "
               "Treffer ab +0,03. Er erklaert also zu OFT einen "
               "Unterschied - was den gefundenen Unterschied vorsichtig, "
               "einen Nullbefund aber stark macht", "gilt",
               "Methodik 2.160"),
    Befundlage("2.159", "✔✔ `schnitt` TRAEGT ZUSAETZLICH - ueber die "
               "Kette simuliert. Nach Auswahl (Stufe 5) UND nach funding "
               "+ turnover gemessen: +0,0397 R entzerrt, Rohband "
               "[+0,0132 .. +0,0751] - es schliesst den eigenen Nullwert "
               "+0,0052 AUS. Die Kontrolle `zufall` an derselben Stelle: "
               "+0,0058 entzerrt, Rohband [-0,0003 .. +0,0230] - "
               "schliesst ihn EIN. 2.461 Kalendertage", "gilt",
               "Methodik 2.159 / n67_schnitt_ueber_die_kette.py"),
    Befundlage("2.159-quote", "Die Durchlassquote der simulierten Kette: "
               "50,6 Anker je Tag nach der Auswahl, 43,0 nach funding + "
               "turnover (die beiden sperren nur 15 %, weil ihre "
               "Abdeckung bei 56 % bzw. 13 % liegt), davon sperrt "
               "`schnitt` weitere 21,6 %", "gilt", "Methodik 2.159"),
    Befundlage("2.159-grenze", "⚠️ WAS OFFEN BLEIBT: die Rohbaender von "
               "`schnitt` und `zufall` UEBERLAPPEN in [+0,0132 .. "
               "+0,0230]. Der Nachweis stuetzt sich darauf, dass nur "
               "`schnitt`s Band den eigenen Nullwert ausschliesst - nicht "
               "auf getrennte Baender. Und eine TRENNSCHAERFE wurde in "
               "diesem Aufbau nicht bestimmt", "gilt", "Methodik 2.159"),
    Befundlage("2.158", "⚠️⚠️ DIE FUENF STUFEN FUER `schnitt` LASSEN SICH "
               "NICHT HERLEITEN. Entzerrt ergeben sie +4,07 / +5,55 / "
               "+9,49 / +1,71 / -4,65 Punkte - ein BUCKEL mit Hochpunkt "
               "bei Fuenftel 2, nicht bei 0. Die Vorabfestlegung in "
               "`messe_schnittabstand_beitrag.py` verlangt Monotonie fuer "
               "nutzbar. Zum ZWEITEN Mal bei derselben Groesse (31.08.: "
               "+1,27 +1,59 +0,24 -1,28 -1,82, ebenfalls Buckel) und in "
               "derselben Form wie der 27.08.-Buckel", "gilt",
               "Methodik 2.158 / n64+n65"),
    Befundlage("2.158-verzerrung", "⚠️⚠️ Und die eigene Kontrolle fing "
               "einen Konstruktionsfehler: `median(Gruppe) - median(alle)` "
               "lieferte bei GEMISCHTEN Raengen +0,10 bis +0,16 R statt "
               "null - der Stichprobenmedian kleiner Gruppen ist bei "
               "schiefer Verteilung nach oben verzerrt. Fuenftel 0 hat "
               "1,49 Anker je Tag. Die Verzerrung war so gross wie die "
               "gesuchten Effekte; alle Zahlen sind seither entzerrt "
               "(Nullwert je Gruppe abgezogen, 20 Ziehungen)", "gilt",
               "Methodik 2.158 / n65"),
    Befundlage("2.158-form", "Die FORMFRAGE bleibt OFFEN. "
               "Gleichstandsfrei gemessen (Schalter fragt `kennzahl<0` "
               "direkt statt ueber den Rang): SCHALTER +0,0370 R "
               "[-0,0511 .. +0,2498], REGLER -0,1399 R [-0,0627 .. "
               "+0,0440] fuer die Gruppe UEBER dem Schnitt. Die "
               "Rohbaender UEBERLAPPEN - die Formen sind nicht "
               "unterscheidbar", "gilt", "Methodik 2.158 / n66"),
    Befundlage("2.158-redundanz", "⚠️ `schnitt` und die AUSWAHL der Kette "
               "messen teilweise dasselbe: Spearman +0,704 im vollen "
               "Tagesquerschnitt, aber +0,418 INNERHALB der Auswahl - und "
               "nur die zweite Zahl zaehlt, weil Stufe 12 auf der bereits "
               "ausgewaehlten Menge arbeitet. Ursache: hohes "
               "250-Tage-Momentum heisst fast zwangslaeufig ueber dem "
               "eigenen 200-Schnitt. 60,6 % der Gewaehlten liegen "
               "darueber, im vollen Querschnitt nur 34,8 %", "gilt",
               "Methodik 2.158 / n66"),
    Befundlage("2.157", "⚠️⚠️ `schnitt` UND DAS AKKUMULATIONSMASS SIND "
               "DIESELBE GROESSE: `c/mean(200)-1` als Regler gegen "
               "`kurs<sma200` als Schalter. Sie standen nie nebeneinander, "
               "weil der 28.08.-Befund nie ins Register kam und `schnitt` "
               "am 31.08. auf kontaminierter Basis verworfen wurde "
               "(2.153). Damit sind 'schnitt wieder einbauen' und "
               "'Akkumulationsmass als Beitrag' EINE Aufgabe", "gilt",
               "Methodik 2.157 / n63_form_der_achse.py"),
    Befundlage("2.157-form", "„Die Form ist entschieden: REGLER +0,1759 R "
               "schlaegt SCHALTER +0,0040 R\"", "abgeloest",
               "Methodik 2.157", abgeloest_durch="2.158",
               warum="der Schalter-Arm hat NIE einen Schalter gemessen. "
                     "`pruefe_auswahl` sperrt Rang >= 0,8; bei einer "
                     "0/1-Kennzahl mit 65,2 % Einsen liegt das oberste "
                     "Rangfuenftel GANZ in der Einser-Gruppe, und `rang` "
                     "bricht Gleichstaende nach ARRAY-REIHENFOLGE. "
                     "Belegt: nach Umsortieren der Zeilen EINES Tages "
                     "sind nur 15 von 62 Symbolen dieselben. Der Arm mass "
                     "eine BELIEBIGE Teilmenge - +0,0040 R ist genau das "
                     "erwartete Nichts. Die Formfrage ist wieder OFFEN"),
    Befundlage("2.157-regler", "Was aus N-63 BLEIBT: der Regler-Arm "
               "reproduziert den registrierten Anker auf die vierte "
               "Stelle (+0,17593 gegen +0,1759). Dort gibt es keine "
               "Gleichstaende. Die FORMFRAGE ist damit wieder OFFEN", 
               "gilt", "Methodik 2.157 / R-R11"),
    Befundlage("2.157-anker", "⚠️ Und die Messung REPRODUZIERT den "
               "registrierten Anker auf die vierte Stelle: +0,17593 "
               "(messbasis_anker.json, N-59) gegen +0,1759 heute. Der "
               "Schalter kommt aus DERSELBEN Kandidatenwelt, nur die "
               "Kennzahl ist 0/1 - der Unterschied kann nicht aus der "
               "Datenlage stammen", "gilt", "Methodik 2.157 / R-R11"),
    Befundlage("2.157-grenze", "⚠️ WAS DAMIT NICHT GESAGT IST: der "
               "Schalter verliert auf `bewegung_r`. Das 28.08.-Mass wurde "
               "auf der VERBILLIGUNG gemessen (Perzentilrang der eigenen "
               "Reihe) - ein anderes Erfolgsmass fuer eine andere Frage. "
               "2.154 bleibt dort gueltig", "gilt", "Methodik 2.157"),
    Befundlage("2.156", "⚠️⚠️ BTC/ETH/SOL BRAUCHEN KEINE EIGENE LOESUNG. "
               "Die -0,0251/-0,0308/-0,0291 aus 2.154 sind mit p 0,833 "
               "NICHT von null zu trennen - drei Reihen, 8 bis 12 Bloecke. "
               "Auf allen 507 Reihen nach Tiefanteil geschichtet traegt "
               "`UNTER_SMA` in 4 von 5 Fuenfteln, und im FLACHSTEN - dort "
               "liegen BTC (2,0 %) und ETH (9,7 %) - am staerksten von "
               "allen: +0,0481 (p 0,000, 101 Reihen). SOL liegt im "
               "zweiten (+0,0246, p 0,035)", "gilt",
               "Methodik 2.156 / n62_wirkung_nach_tiefe.py"),
    Befundlage("2.156-tiefe", "Der ZAEHLBEFUND dahinter (3.003 Tage, keine "
               "Untermacht): BTC liegt an 2,0 % der Tage unter -40 % vom "
               "eigenen 200-Schnitt, das uebrige Universum an 20,6 % - "
               "zehnfacher Unterschied. Umgekehrt liegt BTC an 21,1 % der "
               "Tage ueber +30 % (Universum 13,2 %). Die Kernwerte sind "
               "seltener tief, nicht anders gebaut", "gilt",
               "Methodik 2.156 / n61_kernwerte_akkumulation.py"),
    Befundlage("2.156-eigenschaft", "⚠️ Und der Schichter ERKLAERT die "
               "Wirkung nicht: der Verlauf ueber die fuenf Fuenftel ist "
               "nicht monoton (+0,048 / +0,025 / +0,016 / +0,025 / "
               "+0,032). Das REPRODUZIERT den Vorbefund "
               "`eigenschaften_erklaeren_den_vorsprung_nicht` - es ist "
               "kein neuer Nullbefund. Vorab benannt, nicht nachtraeglich",
               "gilt", "Methodik 2.156"),
    Befundlage("2.155", "⚠️⚠️ Die DURCHLASSQUOTE ist entschieden: "
               "Schwelle 0,080 R = 16,4 % Durchlass = rund 6 "
               "Empfehlungen/Woche. R-R9 verlangt sie als "
               "NUTZERENTSCHEIDUNG, und sie stand seit dem 30.08. aus - "
               "damit war jede Kalibrierung willkuerlich. Haerter "
               "filtern ist gemessen SCHAEDLICH (0,010: -0,0558 je "
               "verworfenem Signal)", "gilt",
               "Nutzerentscheidung 07.09. / agent/potential.py"),
    Befundlage("2.155-sicht", "⚠️⚠️ Und der Befund dahinter: die Zahl, die "
               "entscheidet OB eine Empfehlung entsteht, war UNSICHTBAR - "
               "nur Konstante im Code, kein `bewertung`-Block in "
               "config.yaml, kein Wort in Mail oder GUI. Nutzerhinweis: "
               "'so einen Parameter vergesse ich in Kuerze und du auch - "
               "die Doku reicht bei so einer zentralen Einstellung "
               "nicht'. Jetzt: config.yaml steuert ohne Neustart, jede "
               "Mail nennt Wert/Quelle/Alter, fuenf Suitepruefungen "
               "halten es offen", "gilt",
               "Methodik 2.155 / paket Kalibrierung"),
    Befundlage("2.155-leiche", "⚠️ Beim Aufraeumen gefunden: der Docstring "
               "in potential.py behauptete noch 'steht seit 07.09. auf "
               "0,005' - der Wert der am selben Tag zurueckgenommenen "
               "Aenderung. Genau der Fall, vor dem die Datei selbst warnt "
               "('eine falsche Zahl im Docstring einer Schwelle ist "
               "teurer als anderswo')", "gilt", "Methodik 2.155"),
    Befundlage("2.154", "Das AKKUMULATIONSMASS haelt auf der neuen Basis: "
               "UNTER_SMA +0,0288 (28.08.: +0,0283), TIEFPUNKT +0,4242 "
               "BITGLEICH, WOCHENTAG -0,0008. Kennlinie weiter monoton "
               "ueber neun Baender. BTC -0,0251 / ETH -0,0308 / SOL -0,0291 "
               "bis auf die dritte Stelle reproduziert", "gilt",
               "Methodik 2.154 / messe_akkumulationsmass.py"),
    Befundlage("2.154-achse", "⚠️ Das Werkzeug war heute unsicher: es "
               "fragte OHNE Filter ab. Die Symbole fielen durch die "
               "Lueckenlosigkeitspruefung heraus (Aktien haben "
               "Wochenendluecken), aber die KALENDERACHSE blieb bei 14.728 "
               "statt 3.309 Tagen - und ueber die laeuft der zirkulaere "
               "Verschub. Eine zu enge Nullverteilung erzeugt falsch "
               "positive Befunde. Gefixt", "gilt", "Methodik 2.154"),
    Befundlage("2.153", "Der 31.08.-Befund zu `schnitt` ist ABGELOEST: "
               "reproduziert mit demselben Werkzeug drehen alle Vorzeichen "
               "(H5 -0,0069 -> +0,0092). Ursache: die Messung lief auf "
               "1.314 Symbolen inkl. 798 Nicht-Krypto; der N-19-Fix kam "
               "erst am 03.09.", "gilt", "Methodik 2.153"),
    Befundlage("2.152", "Der Zustand der Kette je Strategie: bei "
               "`einstieg` ENTSCHEIDET Stufe 12 (funding+turnover), bei "
               "`akkumulation` WINKT SIE DURCH (vermessen=False, Notiz "
               "statt Sperre - eine Sperre ohne Beitraege waere eine "
               "Sperre nach Datenlage, Regel 4)", "gilt", "Methodik 2.152"),
    Befundlage("2.152-akkum", "⚠️⚠️ Das Akkumulationsmass IST `schnitt` "
               "(Abstand zum 200-Schnitt, H90 statt H20). Gemessen am "
               "28.08., monoton ueber NEUN Baender in beiden "
               "Kalenderhaelften - aber es kam NIE ins Kandidatenregister. "
               "N-59 fand am 07.09. denselben Wert fuer `einstieg`, ohne "
               "dass die Verbindung gezogen war", "gilt", "Methodik 2.152"),
    Befundlage("2.152-kern", "⚠️⚠️ Das Akkumulationsmass traegt NICHT fuer "
               "BTC (-0,0251, p=0,723), ETH (-0,0308) und SOL (-0,0291) - "
               "und `asset_dca_settings` enthaelt genau BTC und ETH. Die "
               "Akkumulation laeuft auf den Werten, fuer die das Mass keine "
               "Begruendung liefert", "offen", "Methodik 2.152"),
    Befundlage("2.152-nummer", "⚠️ Namensschatten: der `entscheider` ist "
               "die ZWOELFTE Stufe, heisst aber ueberall ,Stufe 11'. "
               "`terminmarkt` wurde nachtraeglich eingefuegt (N-14). "
               "Folgenlos, weil der Code ueber NAMEN adressiert - jetzt in "
               "`rollen_gate.STUFEN` vermerkt", "gilt", "Methodik 2.152"),
    Befundlage("2.151", "Die sieben F-198-Kryptoreihen sind GELADEN "
               "(8 von 183, 13.168 Kerzen; 175 zu kurz). Messbasis "
               "516 -> 524. Die Trennung haelt: DASH aktien 1.440 Kerzen ab "
               "2020, krypto 2.721 ab 2019. Kursprobe eindeutig: T 0,0044 $ "
               "(Threshold, nicht AT&T)", "gilt",
               "Methodik 2.151 / lade_messreihen.py"),
    Befundlage("2.151-filter", "⚠️ Ohne den Fix waeren SECHS Aktien-/"
               "ETF-Reihen mit Kryptokerzen verwoben worden (C, DASH, MDT, "
               "STX, BOND, DIA) - und die sieben Kryptoreihen haette die "
               "1:1-Zuordnung trotzdem verworfen. Beide Haelften des Fixes "
               "waren noetig", "gilt", "Methodik 2.151"),
    Befundlage("2.151-anker", "Beim Basiswechsel kippen ZWEI Urteile - "
               "beide auf der FREIEN Menge (funding traegt->traegt nicht, "
               "turnover nicht trennbar->traegt). Die Wirkungen bewegten "
               "sich nur um 0,002-0,003 R. JEDER Anker auf der SELEKTIERTEN "
               "Menge ist unveraendert - `schnitt` bleibt Kandidat "
               "(+0,17593 statt +0,17072)", "gilt", "Methodik 2.151"),
    Befundlage("2.151-suite", "⚠️ Eine Suite-Pruefung hatte selbst den "
               "Fehler, den sie verhindern soll: sie pruefte gegen "
               "`messreihen` (1:1) und meldete die sieben Kryptowerte als "
               ",Nicht-Krypto'. Umgestellt auf "
               "`price_history_ohlc.assetklasse`", "gilt", "Methodik 2.151"),
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

    # 1b — ⚠️⚠️ DIE GENANNTEN STUFEN MUESSEN DIE LAUFENDEN SEIN.
    #
    # Am 07.09.2026 stand im `live`-Feld von `turnover` noch
    # "(+0.33, +0.33, +0.33, -0.48, -0.48) seit 07.09." - eine am selben
    # Tag zurueckgenommene Aenderung. Der Code fuehrte laengst wieder
    # (+3.15, +0.83, +0.22, -1.79, -2.40), und die `warnung` desselben
    # Eintrags sagte das auch. **Das Blatt widersprach sich selbst.**
    #
    # Die Pruefung oben faengt das NICHT: sie prueft nur, ob das Merkmal
    # ueberhaupt vorkommt. Ein Register, dessen Zahlen weglaufen, ist
    # schlimmer als keines - man glaubt ihm.
    try:
        from agent import wahrscheinlichkeit as _W
        _lauf = {b.merkmal: b.stufen for b in _W.BEITRAEGE}
    except Exception as _e:                                  # noqa: BLE001
        fehler.append("wahrscheinlichkeit nicht lesbar: %s" % _e)
        _lauf = {}
    for k in KANDIDATEN:
        if "Stufen (" not in (k.live or ""):
            continue
        _m = k.live.split("merkmal ")[-1].split(" ")[0] if "merkmal " in k.live else ""
        _echt = _lauf.get(_m)
        if _echt is None:
            continue
        _genannt = k.live.split("Stufen (")[1].split(")")[0]
        try:
            _z = tuple(round(float(x), 2) for x in _genannt.split(","))
        except ValueError:
            fehler.append("%s: Stufen im Register nicht lesbar: %r"
                          % (k.name, _genannt))
            continue
        if tuple(round(float(x), 2) for x in _echt) != _z:
            fehler.append(
                "%s: das Register nennt Stufen %s, der Code fuehrt %s - "
                "eine der beiden Zahlen ist falsch, und man glaubt dem "
                "Register" % (k.name, _z,
                              tuple(round(float(x), 2) for x in _echt)))

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
