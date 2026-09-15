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

Die Werkzeugliste wird **gescannt**, nicht gepflegt - Hunderte Eintraege von Hand
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
    # ⚠️⚠️ DIE LOESUNGSSPUR (11.09.2026). Nutzervorgabe, mehrfach
    # wiederholt: *"kein Beitrag faellt ohne Grund, es ist eine Loesung
    # zu suchen."* Ohne dieses Feld stand die Begruendung verstreut in
    # den Befunden und die Vorgabe war nicht pruefbar - acht von sechzehn
    # gemessenen Kandidaten hatten ueberhaupt kein Blatt.
    #
    # Hier gehoert hinein: WARUM er gefallen ist, WAS versucht wurde und
    # WAS offen bleibt. Ein leeres Feld bei `zustand="traegt nicht"` ist
    # ein Mangel, kein Normalfall.
    loesung: str = ""


def umbauseite(k) -> tuple:
    """VOR oder NACH dem Messstandard? — abgeleitet aus der Messkette.

    ## ⚠️⚠️ Nutzervorgabe 10./11.09.2026

    > *„du musst sauber trennen nach vor und nach dem aktuellen Umbau -
    > das gilt fuer Messungen, Dokumente und Code!!!"*

    Fuer CODE gibt es die Trennung (`REGISTER_Werkzeuge`, nach
    Methodikstand), fuer MESSUNGEN und DOKUMENTE auch
    (`soll_ist.umbaugrenze`). Fuer die KANDIDATENBLAETTER fehlte sie -
    und gerade dort entscheidet sie, ob ein Urteil ueberhaupt zaehlt.

    ⚠️ **Es wird kein neues Feld erfunden.** Die Seite folgt aus dem
    letzten Eintrag der vorhandenen `kette`, so wie die Dokumentenseite
    aus dem Aenderungsdatum folgt.

    ⚠️⚠️ **DAS DATUM IST EIN ANHALT, KEIN URTEIL** - dieselbe
    Einschraenkung wie bei den Dokumenten. Ein altes Urteil kann richtig
    sein; es sagt nur, dass es die Norm vom 08./09.09. nicht gesehen hat.

    ⚠️ NICHT lexikalisch vergleichen: „30.08." ist als Zeichenkette
    groesser als „06.09.". Sortiert wird nach (Monat, Tag) - der Fehler
    ist beim Bauen dieser Funktion einmal passiert.
    """
    tage = []
    for datum, _was in (k.kette or ()):
        teile = str(datum).strip(".").split(".")
        if len(teile) >= 2 and teile[0].isdigit() and teile[1].isdigit():
            tage.append((int(teile[1]), int(teile[0])))   # (Monat, Tag)
    if not tage:
        return ("ohne Datum", "?")
    m, t = max(tage)
    letzte = "%02d.%02d." % (t, m)
    # Der Messstandard gilt ab dem 09.09.2026.
    return (("nach Umbau" if (m, t) >= (9, 9) else "vor Umbau"), letzte)


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
        
               ("10.09.", "⚠️ V2/N-73: besteht die Huerde NICHT - 2 von 3 Beitragsmengen (10 %% +0,0688 TRAEGT · 20 %% +0,0582 NICHT TRENNBAR · 50 %% +0,0313 TRAEGT)"),
               ("11.09.", "⚠️ V11: kippt unter dem schaerferen Stabilitaetstest mit ZUFALLSauswahl in 1 von 3 Saaten (+0,0417 [+0,0036 .. +0,0785])"),
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
        
               ("10.09.", "⚠️ V2/N-73: 1 von 1 - aber nur, weil bei seiner Abdeckung (66 von 536) UEBERHAUPT NUR EINE Beitragsmenge zulaessig ist. Eine SCHWAECHERE Aussage als 3-von-3"),
               ("11.09.", "✔ V11: stabil auf seiner einen Menge (bis 0,10)"),
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
        
               ("10.09.", "✔ V2/N-73: 2 von 2 - der einzige live laufende Beitrag, der die Huerde ohne Einschraenkung nimmt"),
               ("11.09.", "✔ V11: stabil auf beiden Mengen (bis 0,05 · 0,02) - die schaerfsten Schranken im Feld"),
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
        
               ("10.09.", "⚠️ V9: unabhaengig von funding, aber geschichtet NICHT MEHR TRENNBAR (echter Nullbefund, 0,05 R)"),
               ("10.09.", "⚠️⚠️ Kriterium 2 FAELLT: +0,2039 [+0,0760 .. +0,3912] auf der 20-%%-Menge, Band schliesst die Null aus"),
               ("10.09.", "⚠️ N-73 nur 1 von 3 Mengen - der wackligste Kandidat"),
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
        
               ("10.09.", "✔ V9: unabhaengig von funding · ✔ Kriterium 2: stabil auf ALLEN drei Mengen (bis 0,20 · 0,20 · 0,05)"),
               ("11.09.", "⚠️⚠️ V11: Kriterium 1 erfuellt (100 %%), N-73 aber NICHT - 2 von 3. Als Ersatz fuer `schnitt` gefallen"),
               ),
        loesung=("⚠️⚠️ ALS ERSATZ FUER `schnitt` GEPRUEFT UND GEFALLEN "
                 "(V11, 11.09.): Kriterium 1 erfuellt er mit 100 %% "
                 "Abdeckung, N-73 aber NICHT - 2 von 3 Mengen "
                 "(10 %% +0,0846 TRAEGT · 20 %% +0,0698 TRAEGT · "
                 "50 %% +0,0156 TRAEGT NICHT bis 0,0213 R). Bei 50 %% ist "
                 "es eine ECHTE Aussage, kein ,nicht trennbar'. "
                 "⚠️⚠️ UND DIE ZWEITE STUETZE IST AUCH WEG: ,die einzige "
                 "MONOTONE Form' stammt aus **F-222/N-45** - einem Blatt "
                 "mit Sperrkopf (,GILT NICHT ALS BEITRAGSURTEIL', "
                 "gemessen auf Ziel-vor-Stop und/oder der freien Menge). "
                 "Beide Argumente fuer ihn sind damit gefallen. "
                 "➔ OFFEN bliebe nur eine andere FORM oder ein anderer "
                 "HORIZONT (N2: H5 ist nie gegengeprueft)"),
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
        
               ("07.09.", "✔ N-59: traegt auf der selektierten Menge, 100 %% Abdeckung"),
               ("10.09.", "✔ A2: traegt fuer die AKKUMULATION (+0,0470, p 0,000, 481 von 518 Symbolen) - auf der FREIEN Messmenge V1"),
               ("10.09.", "⚠️⚠️ Kriterium 2 FAELLT auf der Betriebsmenge: +0,1973 [+0,0717 .. +0,3892] bei 20 %%"),
               ("11.09.", "⚠️⚠️⚠️ ABER die Instabilitaet gehoert der AUSWAHL: mit ZUFALLSauswahl +0,0380 / +0,0264 / +0,0310, stabil in 3 von 3 - bei VIERMAL schaerferem Test"),
               ("11.09.", "⚠️⚠️ Der tragende Einwand ist ein anderer: Spearman +0,704 mit der Auswahl, Wirkung zu 4/5 Auswahlartefakt (2.222/2.335)"),
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
               ("06.09.", "Schritt 4a: auf keinem Lauf, keinem Massstab"),
               ("09.09.", "2.244-amihud: der EINZIGE mit sauberem "
                          "Stabilitaetsbild - nirgends trennbar UND "
                          "konsistentes Vorzeichen (+0,004 bis +0,029)"),
               ("11.09.", "⚠️ laeuft LAENGS rueckwaerts (V4, offen)")),
        loesung=("⚠️⚠️ NICHT ALS BEITRAG, SONDERN AN ANDERER STELLE - und "
                 "das ist belegt, nicht geraten: 2.166-woanders haelt "
                 "fest, dass er AUSFUEHRBARKEIT misst, nicht Ertrag. Eine "
                 "Groesse, die sagt ,wie teuer ist der Ausstieg hier', "
                 "gehoert in die DIMENSIONIERUNG (Positionsgroesse, "
                 "Slippage), nicht in die Potentialbewertung. ⚠️ Dazu "
                 "2.244-amihud: er ist zeitstabil und wirkungslos - das "
                 "ist kein Kandidat, aber ein Grund, ihn nicht "
                 "abzuschreiben. ⚠️ OFFEN bleibt V4: er laeuft LAENGS "
                 "rueckwaerts, und das ist ungeklaert"),
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

    # ================================================================
    # DIE VIER TERMINMARKT-KANAELE (N-9, 2.169)
    # ⚠️⚠️ ALLE VIER sind auf `bewegung_r` gefallen - der SPOT-Zielgroesse.
    # Gegen `barriere`, die Zielgroesse des HEBELS, ist keiner je gemessen
    # worden. A1 blockiert das (2.238: das Band ist viermal zu eng).
    # ================================================================
    Kandidat(
        menge="frei", fenster="voll",
        name="oi_je_umsatz",
        hypothese=("Offene Terminpositionen je Umsatz - wie stark steht "
                   "der Terminmarkt relativ zum Kassamarkt?"),
        form="regler",
        basis="H20 · 122 Symbole · rund 1.400 bis 1.736 Tage",
        wert="traegt auf KEINER der 3 zulaessigen Mengen",
        live="- nicht registriert",
        zustand="traegt nicht",
        kette=(("06.09.", "N-9: 0 von 3 zulaessigen Mengen auf "
                          "`bewegung_r` (Referenz `oi_aenderung` 3 von 3)"),
               ("06.09.", "2.169-zielgroesse: trug in N-17b gegen "
                          "FRONTLOADING - eine ANDERE Zielgroesse")),
        loesung=("⚠️⚠️ OFFEN UND KONKRET: er ist gegen `bewegung_r` "
                 "gefallen, also gegen die SPOT-Frage. Die HEBEL-Frage "
                 "ist `barriere` (Ziel vor Stop) - dagegen ist er NIE "
                 "gemessen. Der Weg dorthin fuehrt ueber **A1**: das Band "
                 "auf binaeren Daten ist viermal zu eng (2.238), deshalb "
                 "traegt dort sogar `zufall`. A1 hat einen benannten "
                 "Loesungsweg (2.238-klasse): Fehlalarmquote der "
                 "Barrieren-Anlage auf Nullwelten - dasselbe Verfahren, "
                 "das am 09.09. den Nullbezug entschieden hat")),
    Kandidat(
        menge="frei", fenster="voll",
        name="long_bias",
        hypothese=("Anteil der Long-Konten am Terminmarkt - viele Longs "
                   "heissen einseitige Positionierung."),
        form="regler",
        basis="H20 · 122 Symbole · rund 1.400 bis 1.736 Tage",
        wert="traegt auf KEINER der 3 zulaessigen Mengen",
        live="- nicht registriert",
        zustand="traegt nicht",
        kette=(("06.09.", "N-9: 0 von 3 zulaessigen Mengen auf "
                          "`bewegung_r`"),
               ("06.09.", "2.169-zielgroesse: trug gegen FRONTLOADING"),
               ("05.09.", "N-17b: NICHT unabhaengig vom `rsi`")),
        loesung=("⚠️ ZWEIFACH belastet: gegen `bewegung_r` gefallen UND "
                 "nicht unabhaengig vom `rsi`. Die `barriere`-Spur aus "
                 "`oi_je_umsatz` gilt auch hier, ist bei ihm aber "
                 "schwaecher - selbst wenn er dort traegt, bliebe die "
                 "Redundanz mit `rsi` zu klaeren")),
    Kandidat(
        menge="frei", fenster="voll",
        name="top_bias",
        hypothese=("Positionierung der groessten Konten - folgen die "
                   "Grossen oder stehen sie dagegen?"),
        form="regler",
        basis="H20 · 122 Symbole · rund 1.400 bis 1.736 Tage",
        wert="traegt auf KEINER der 2 zulaessigen Mengen",
        live="- nicht registriert",
        zustand="traegt nicht",
        kette=(("06.09.", "N-9: 0 von 2 zulaessigen Mengen auf "
                          "`bewegung_r`"),
               ("06.09.", "2.169-zielgroesse: trug gegen FRONTLOADING"),
               ("05.09.", "N-17b: NICHT unabhaengig vom `rsi`")),
        loesung=("⚠️ Wie `long_bias` - und mit der duennsten Datenlage der "
                 "vier: nur ZWEI Mengen sind ueberhaupt zulaessig. Ein "
                 "Urteil auf zwei Mengen ist schwaecher als eines auf "
                 "drei (2.312: ,1 von 1' ist keine starke Aussage)")),
    Kandidat(
        menge="frei", fenster="voll",
        name="taker_bias",
        hypothese=("Verhaeltnis aggressiver Kaeufer zu Verkaeufern - wer "
                   "nimmt den Preis, statt zu warten?"),
        form="regler",
        basis="H20 · 122 Symbole · rund 1.400 bis 1.736 Tage",
        wert="traegt auf KEINER der 3 zulaessigen Mengen",
        live="- nicht registriert",
        zustand="traegt nicht",
        kette=(("06.09.", "N-9: 0 von 3 zulaessigen Mengen auf "
                          "`bewegung_r`"),),
        loesung=("⚠️⚠️ DER AUSSICHTSREICHSTE DER VIER - und der einzige, "
                 "bei dem die Redundanzfrage offen ist statt negativ "
                 "beantwortet: `oi_wert` und `taker_bias` sind laut "
                 "2.168-offen NIE unter der Norm gemessen worden, und "
                 "anders als `long_bias`/`top_bias` ist er nicht als "
                 "`rsi`-redundant belegt. Dieselbe `barriere`-Spur wie "
                 "`oi_je_umsatz`, ohne dessen Vorbelastung")),

    # ================================================================
    # DIE KURSREIHEN-GROESSEN, die nicht tragen
    # ================================================================
    Kandidat(
        menge="frei", fenster="voll",
        name="rsi",
        hypothese=("Relative-Staerke-Index - ueberkauft heisst Rueckschlag, "
                   "ueberverkauft heisst Erholung."),
        form="regler",
        basis="H20 · volle Historie · 536 Symbole",
        wert="traegt nicht UND auf drei Mengen zeitinstabil",
        live="- nicht registriert",
        zustand="traegt nicht",
        kette=(("09.09.", "Gesamtlauf: traegt auf keiner Menge (2.219)"),
               ("09.09.", "N-89: auf DREI Mengen zeitinstabil (2.244)"),
               ("09.09.", "2.256: besteht die Spannenpruefung auf `frei` "
                          "mit 2,16 - aber die Pruefung laesst JEDEN "
                          "durch und taugt nicht")),
        loesung=("⛔ DOPPELT gefallen: wirkungslos UND zeitinstabil. Das "
                 "ist der einzige Kandidat, bei dem beide Hauptkriterien "
                 "gleichzeitig reissen. ⚠️ Er gehoert ausserdem zur "
                 "Familie um `vola`/`schnitt` (Ueberlappung 0,25 bis "
                 "0,70, F-222/N-45) - aus der gehoert ohnehin nur EINE "
                 "Vertreterin in die Bewertung. Eine Loesung waere nur "
                 "ueber eine andere FORM denkbar, und dafuer gibt es "
                 "keinen Anhaltspunkt")),
    Kandidat(
        menge="frei", fenster="voll",
        name="momentum",
        hypothese=("Kursentwicklung ueber 250 Tage - wer gestiegen ist, "
                   "steigt weiter."),
        form="regler",
        basis="H20 · volle Historie · 536 Symbole",
        wert="widerspricht sich ueber die Mengen",
        live="- nicht als Beitrag; er IST die Auswahl (`auswahl.waehle`, "
             "RUECKBLICK_TAGE = 250)",
        zustand="traegt nicht",
        kette=(("09.09.", "Gesamtlauf: widerspricht sich ueber die "
                          "Mengen (2.219)"),
               ("09.09.", "2.220: die KETTENMENGE ist gar keine "
                          "momentum-selektierte - von 43 Werten "
                          "passieren 25, WEIL sie Bestand haben")),
        loesung=("⚠️⚠️ HIER IST DIE LOESUNG KEINE MESSFRAGE: `momentum` "
                 "ist bereits im System - als AUSWAHL, nicht als "
                 "Beitrag. Ihn zusaetzlich als Beitrag zu fuehren, hiesse "
                 "dieselbe Groesse zweimal zu zaehlen; genau daran ist "
                 "`schnitt` gescheitert (2.335: Spearman +0,704 mit der "
                 "Auswahl). ⚠️ Die OFFENE Frage ist eine andere und steht "
                 "als N17 im Plan: **gehoert die Auswahl selbst "
                 "ersetzt?**")),
    Kandidat(
        menge="frei", fenster="voll",
        name="momentum_kurz",
        hypothese=("Kursentwicklung ueber wenige Wochen statt ueber ein "
                   "Jahr - die kurze Variante von `momentum`."),
        form="regler",
        basis="H20 · volle Historie · 536 Symbole",
        wert="widerspricht sich ueber die Mengen",
        live="- nicht registriert",
        zustand="traegt nicht",
        kette=(("09.09.", "Gesamtlauf: widerspricht sich ueber die "
                          "Mengen (2.219)"),),
        loesung=("⚠️ OFFEN, aber schwach: er ist der einzige der acht, zu "
                 "dem es ausser dem Gesamtlauf KEINE eigene Untersuchung "
                 "gibt. Er teilt die Kollinearitaetsfrage mit "
                 "`momentum`. ⚠️ Ihn ernsthaft zu pruefen hiesse, ihn "
                 "gegen die AUSWAHL zu entzerren - dasselbe Verfahren, "
                 "das bei `schnitt` am 11.09. gelaufen ist "
                 "(`entzerrte_reihe(auswahl_saat=...)`)")),
    Kandidat(
        menge="frei", fenster="voll",
        name="funding_extrem",
        hypothese=("Abstand der Finanzierungsrate vom EIGENEN "
                   "Normalzustand in MAD, vorzeichenlos - nicht der "
                   "Querschnittsrang, sondern die eigene Auffaelligkeit."),
        form="regler",
        basis="H20 · 300 Symbole (Funding-Abdeckung)",
        wert="widerspricht sich ueber die Mengen",
        live="- nicht registriert",
        zustand="traegt nicht",
        kette=(("09.09.", "Gesamtlauf: widerspricht sich ueber die "
                          "Mengen (2.219)"),
               ("09.09.", "2.255: er misst eine ANDERE Achse als "
                          "`funding` - Eigen-Normalzustand statt "
                          "Querschnittsrang"),
               ("05.09.", "N-17b: die Kombination mit `oi_aenderung` ist "
                          "echte Verstaerkung - aber F-207 zeigte, dass "
                          "sie die LIVE-Sperre nicht verbessert")),
        loesung=("⚠️ OFFEN: er ist der einzige Gefallene, der in "
                 "KOMBINATION schon einmal getragen hat (N-17b mit "
                 "`oi_aenderung`). ⚠️ Aber F-207/F-208 haben gezeigt, "
                 "dass die Kombination weder die Live-Sperre verbessert "
                 "noch F-165s Schwelle erreicht. Als EIGENSTAENDIGER "
                 "Beitrag ist er widerspruechlich; als Verstaerker ist er "
                 "gemessen und zu schwach")),
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
    Befundlage("2.240-abbruch", "⚠️ TEILWEISE ABGELOEST DURCH 2.243 "
               "(die Instabilitaet war Kollinearitaet). War: DIE "
               "ABBRUCHBEDINGUNG AUS DEM "
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
    Befundlage("2.242", "✔✔✔ N-89 TEIL B: `schnitt`s ZEITINSTABILITAET "
               "IST KOLLINEARITAET MIT DER AUSWAHL, nicht seine "
               "Eigenschaft. Auf 5 % faellt der Haelftenunterschied von "
               "-0,4310 (Momentum, trennbar) auf -0,013 bis +0,005 "
               "(fuenf Zufallsauswahlen, KEINE trennbar). Auf 20 % von "
               "+0,1973 auf +0,021 bis +0,045, davon 1 von 5 trennbar - "
               "bei einem Test mit 18 % Fehlalarmquote das Erwartete",
               "gilt", "n89_familie_und_schnitt_loesung.py",
               basis="Messmenge v1, entzerrte Reihe, 5 Zufallsziehungen"),
    Befundlage("2.242-warum", "✔ DIE ERKLAERUNG PASST ZUM MECHANISMUS: "
               "`schnitt` und das Auswahl-Momentum korrelieren mit "
               "Spearman +0,704. Auf der Momentumspitze liegen fast alle "
               "Werte ueber ihrem eigenen Schnitt - es bleibt kaum "
               "Streuung uebrig, und die Messung wird instabil. Je "
               "schmaler die Menge, desto staerker: -0,431 bei 5 %, "
               "+0,197 bei 20 %, +0,002 bei 50 %", "gilt",
               "n89 / Befund 2.158-redundanz"),
    Befundlage("2.242-k1b", "✔✔ UND ES ERKLAERT K-1b VON DER ANDEREN "
               "SEITE: dort brach `schnitt`s Wirkung auf Zufallsmengen "
               "von +0,186 auf +0,037 ein (2.222). Beides ist derselbe "
               "Mechanismus - auf der Momentummenge misst `schnitt` "
               "teilweise die AUSWAHL mit", "gilt", "n89 / Befund 2.222"),
    Befundlage("2.243", "⚠️⚠️ DAMIT IST DIE ABBRUCHBEDINGUNG ANDERS ZU "
               "LESEN ALS IN 2.240: `schnitt` ist NICHT gefallen - er "
               "wurde auf der FALSCHEN Menge geprueft. Auf einer nicht "
               "momentum-selektierten Menge ist er zeitstabil. ⚠️ Und die "
               "KETTE arbeitet auf genau so einer Menge (ueberwiegend "
               "Bestand, nach nichts selektiert - Befund 2.220)", "gilt",
               "n89_familie_und_schnitt_loesung.py"),
    Befundlage("2.243-offen", "⚠️ WAS DAMIT NICHT GELOEST IST: die FORM. "
               "Der Buckel (+4,07/+5,55/+9,49/+1,71/-4,65) ist dreimal "
               "aufgetreten. ⚠️⚠️ ABER: N-64/N-65 haben die Stufen auf "
               "der SELEKTIERTEN Menge gerechnet - wenn `schnitt` dort "
               "mit dem Momentum kollinear ist, koennte der Buckel "
               "DASSELBE Artefakt sein. Das ist pruefbar und die "
               "naechste Frage", "gilt",
               "Befund 2.158 / n89 / offene Frage"),
    Befundlage("2.244", "⚠️ N-89 TEIL A: KEINE VERTRETERIN DER FAMILIE "
               "BESTEHT BEIDE HUERDEN. `vola` traegt, ist aber auf 20 % "
               "zeitinstabil - GENAU WIE `schnitt`, und beide "
               "korrelieren mit 0,703, also vermutlich dieselbe "
               "Kollinearitaet. `schnitt50` ist zeitstabil, liefert aber "
               "einen WIDERSPRUCH im Gesamtlauf. `rsi` ist auf DREI "
               "Mengen zeitinstabil und traegt nicht", "gilt",
               "n89_familie_und_schnitt_loesung.py",
               basis="Messmenge v1, fuenf Mengen, entzerrte Reihe"),
    Befundlage("2.244-amihud", "⚠️⚠️ `amihud` IST DER EINZIGE MIT "
               "SAUBEREM STABILITAETSBILD: nirgends trennbar UND "
               "konsistentes Vorzeichen (+0,004 bis +0,029) - besser als "
               "die Kontrolle, deren Vorzeichen dreht. ⚠️ Er traegt "
               "aber nicht (Gesamtlauf 09.09.: TRAEGT NICHT auf allen "
               "drei Mengen). Zeitstabil und wirkungslos ist kein "
               "Kandidat - aber es ist ein Grund, ihn nicht abzuschreiben "
               "(Befund 2.166-woanders: er misst AUSFUEHRBARKEIT)",
               "gilt", "n89_familie_und_schnitt_loesung.py"),
    Befundlage("2.245", "⚠️⚠️ N-90 IST UNGUELTIG - die KONTROLLE ist "
               "wilder als der Kandidat. `zufall` erzeugt auf "
               "Zufallsmengen Stufen von -33,89 bis +90,85 Punkten, "
               "waehrend die ganze Beitragsskala bei +-5 liegt. Bei rund "
               "9 Ankern je Tag und Fuenftel ist `median(Fuenftel) - "
               "median(alle)` zu verrauscht, und die Entzerrung "
               "verstaerkt es. Die FORMFRAGE bleibt unbeantwortet",
               "gilt", "n90_buckel_oder_artefakt.py",
               basis="Messmenge v1, Menge 20 %, 5 Zufallsziehungen"),
    Befundlage("2.245-besetzung", "✔✔ EINE SACHE IST ABER SAUBER UND "
               "BELEGT DIE KOLLINEARITAET ZUM DRITTEN MAL: die BESETZUNG "
               "der Fuenftel geht von 1,5 / 2,2 / 3,7 / 8,5 / 29,7 "
               "(Momentum) auf 8,7 / 9,0 / 9,3 / 9,4 / 9,2 (zufaellig) - "
               "ein zwanzigfaches Ungleichgewicht wird zu perfekter "
               "Gleichverteilung. Auf der Momentumspitze liegen fast "
               "alle Werte ueber ihrem eigenen Schnitt", "gilt",
               "n90_buckel_oder_artefakt.py"),
    Befundlage("2.245-momentum", "✔ Und der Momentum-Bezugsfall "
               "reproduziert N-65 sauber: +3,01 / +5,32 / +9,35 / +2,64 "
               "/ -4,57 gegen +4,07 / +5,55 / +9,49 / +1,71 / -4,65 - "
               "Buckel bei Fuenftel 2, Besetzung 1,5 gegen 29,7. Die "
               "kleinen Unterschiede stammen aus der geaenderten "
               "Messbasis", "gilt", "n90_buckel_oder_artefakt.py"),
    Befundlage("2.246", "✔✔ ALLE OFFENEN PUNKTE VON GESTERN UND HEUTE "
               "SIND IM GESAMTPLAN GESAMMELT (Nutzerauftrag 09.09.): A1 "
               "bis A7 Messanlage · B1 bis B8 Beitraege · C1 bis C10 "
               "Kettenpruefung · D1 bis D6 Datenlage und Betrieb · E1 bis "
               "E3 die grosse Planung. Erledigte werden dort "
               "durchgestrichen, nicht geloescht - sonst geht verloren, "
               "warum etwas einmal offen war", "gilt",
               "Basisinfos/Gesamtplan_Wo_wir_stehen_28_08.md"),
    Befundlage("2.247", "⚠️⚠️ GEGENPROBE ERGAB FUENF EINTRAEGE, DIE ALS "
               "OFFEN GEFUEHRT WURDEN OBWOHL ERLEDIGT (Nutzerauftrag "
               "09.09.): `bewertung_hat_keine_instrument_achse` und "
               "`die_begruendung_waehlt_nicht_das_instrument` sind seit "
               "dem 04.09. als KATEGORIENVERWECHSLUNG aufgeloest · "
               "`hebel_hat_eine_bewertung_nie_validiert` ist in der "
               "Rahmung erledigt · KEINER von ihnen verwies auf die "
               "Aufloesung, und der Index fuehrte alle mit Warnzeichen",
               "gilt", "Memory-Durchsicht 09.09.2026"),
    Befundlage("2.247-zwei-andere", "⚠️ Zwei weitere waren NICHT erledigt, "
               "sondern nur ANDERS zu lesen: `hebel_faktisch_kein_hebel` "
               "(der Median 1,10 ist die FOLGE der kalibrierten Quote, "
               "kein Defekt) und `s1_blockiert_akkumulation` (die Spalte "
               "`strategie` existiert inzwischen, wird aber nie gesetzt - "
               "alle 118 Signale NULL). Beide nachgezogen statt "
               "geschlossen", "gilt", "Memory-Durchsicht 09.09.2026"),
    Befundlage("2.247-lehre", "⚠️⚠️ DIE LEHRE: ein aufgeloester Befund "
               "loescht die alten Eintraege NICHT automatisch. Wer nur "
               "den neuen schreibt, laesst funf alte als offen "
               "stehen - und der naechste Blick in den Index zeigt "
               "Arbeit, die es nicht mehr gibt. **Beim Aufloesen gehoert "
               "der Rueckverweis in die alten Eintraege**", "gilt",
               "Selbstbefund 09.09.2026"),
    Befundlage("2.248", "✔✔ N-91: DAS VERFAHREN IST GEGEN BEKANNTE "
               "WAHRHEIT GEEICHT, BEVOR es lief. Auf Kunstdaten (400 Tage "
               "x 60 Anker) erkennt es alle drei Formen: monoton "
               "(-0,392, beide Haelften -0,21/-0,20) · Buckel (-0,004 "
               "GESAMT, aber +0,246/-0,255 in den Haelften) · nichts "
               "(-0,015/-0,014/-0,010). ⚠️ Und es zeigt die Falle: ein "
               "Buckel liefert eine GESAMT-Rangkorrelation von -0,004 - "
               "von 'nichts' NICHT zu unterscheiden. Nur die Haelften "
               "trennen sie", "gilt", "n91_rangkorrelation_form.py",
               basis="Kunstdaten mit bekannter Form"),
    Befundlage("2.249", "✔✔✔ `schnitt` HAT KEINEN BUCKEL. Ueber die "
               "Rangkorrelation je Kalendertag zeigen BEIDE Haelften "
               "dasselbe negative Vorzeichen - auf der Momentummenge "
               "(-0,0311 / -0,0441) wie auf Zufallsmengen (-0,0155 / "
               "-0,0406 und weitere). Der Buckel aus den Fuenfteln war "
               "ein ARTEFAKT DER GRUPPENMEDIANE bei ungleicher Besetzung "
               "(1,5 gegen 29,7 Anker je Tag)", "gilt",
               "n91_rangkorrelation_form.py",
               basis="Messmenge v1, Menge 20 %, H20, Spearman je Tag"),
    Befundlage("2.249-richtung", "✔ UND DIE RICHTUNG STIMMT MIT DER "
               "HYPOTHESE: negativ heisst hoeherer Rang -> schlechteres "
               "Ergebnis, also 'tief unter dem eigenen Schnitt ist "
               "besser'. Das ist genau die Akkumulationsthese", "gilt",
               "n91_rangkorrelation_form.py"),
    Befundlage("2.249-zufall-staerker", "✔✔ UND AUF ZUFALLSMENGEN IST ER "
               "STAERKER: die Gesamtkorrelation ist dort in 4 von 5 "
               "Faellen trennbar negativ (-0,043 bis -0,054, Baender ohne "
               "null), auf der Momentummenge dagegen nicht (-0,0278). "
               "Auch das passt zur Kollinearitaet - auf der "
               "Momentumspitze bleibt zu wenig Streuung", "gilt",
               "n91_rangkorrelation_form.py"),
    Befundlage("2.250", "⚠️⚠️ UEBERRASCHUNG: DEN BUCKEL HAT `funding`, "
               "nicht `schnitt`. Auf der Momentummenge zeigen seine "
               "Haelften GEGENLAEUFIGE und BEIDE TRENNBARE Werte (+0,0541 "
               "[+0,022..+0,088] und -0,0268 [-0,049..-0,004]). Auf "
               "Zufallsmengen verschwindet er - derselbe "
               "Kollinearitaetseffekt, nur bei einem Beitrag, der LIVE "
               "laeuft", "gilt", "n91_rangkorrelation_form.py",
               basis="Messmenge v1, Menge 20 %, H20"),
    Befundlage("2.250-folge", "⚠️ WAS DARAUS FOLGT: `funding`s "
               "Fuenftel-Stufen (+0,82/+1,30/+0,12/-0,54/-1,70) sind "
               "NICHT monoton - Fuenftel 1 liegt ueber Fuenftel 0. Das "
               "stand immer da und galt als hinnehmbar. Die "
               "Rangkorrelation zeigt jetzt, dass es auf der "
               "Momentummenge ein TRENNBARER Buckel ist. ⚠️ Ob das die "
               "Live-Stufen entwertet, ist eine eigene Frage - sie sind "
               "auf `frei` kalibriert, nicht auf 20 %", "gilt",
               "n91 / agent/wahrscheinlichkeit.BEITRAEGE"),
    Befundlage("2.250-kontrolle", "✔ Die Kontrolle sitzt: `zufall` "
               "bleibt ueber alle sechs Auswahlen bei +-0,005 bis "
               "+-0,011, gegen `schnitt`s -0,03 bis -0,05. Zwei von "
               "sechs zeigen 'nur die obere trennbar' mit +0,0074 und "
               "-0,0113 - bei sechs Ziehungen und einem 95-%-Band das "
               "Erwartete", "gilt", "n91_rangkorrelation_form.py"),
    Befundlage("2.251", "✔✔ B9 BEANTWORTET: `funding`s BUCKEL BETRIFFT "
               "DIE LIVE-STUFEN NICHT. Er ist auf der 20-%-Menge "
               "trennbar (+0,0541 / -0,0268, beide Baender ohne null), "
               "auf `frei` aber NICHT - dort hat die untere Haelfte die "
               "Null gerade noch im Band (+0,0211 [-0,000 .. +0,042]). "
               "⚠️ Und die Live-Stufen stehen auf `frei`, an der Quelle "
               "geprueft: `rechne_funding_beitrag.py` bildet KEINE "
               "Auswahl", "gilt", "n92_b9_funding_buckel_auf_frei.py",
               basis="Messmenge v1, Menge frei und 20 %, H20"),
    Befundlage("2.251-reproduziert", "✔✔ UND DIE LIVE-STUFEN "
               "REPRODUZIEREN EXAKT: +0,77 / +1,40 / +0,22 / -0,64 / "
               "-1,75 gegen registriert +0,82 / +1,30 / +0,12 / -0,54 / "
               "-1,70. Abweichungen hoechstens 0,10, durch die gewachsene "
               "Messbasis erklaert", "gilt",
               "n92_b9_funding_buckel_auf_frei.py",
               basis="Messmenge v1, Menge frei"),
    Befundlage("2.251-besetzung", "✔✔ UND DIE URSACHE AUS N-90 LIEGT "
               "HIER NICHT VOR: die Fuenftel sind auf `frei` "
               "ausgeglichen besetzt (30 / 29 / 30 / 29 / 30). In N-90 "
               "standen 1,5 gegen 29,7 Anker - genau das machte die "
               "Gruppenmediane dort unbrauchbar. Auf `frei` tragen sie",
               "gilt", "n92_b9_funding_buckel_auf_frei.py"),
    Befundlage("2.252", "⚠️ WAS TROTZDEM STEHT: die NICHT-MONOTONIE ist "
               "real und reproduziert - Fuenftel 1 (+1,40) liegt ueber "
               "Fuenftel 0 (+0,77). Sie war immer bekannt und galt als "
               "hinnehmbar. ⚠️ Die Kontrolle ist uebrigens AUCH nicht "
               "monoton (-0,17/+0,07/+0,09/+0,11/-0,10) - bei fuenf "
               "verrauschten Punkten ist exakte Monotonie selten "
               "zufaellig. Aber `funding`s Spanne ist ZEHNMAL groesser",
               "gilt", "n92_b9_funding_buckel_auf_frei.py"),
    Befundlage("2.252-inhaltlich", "⚠️⚠️ UND SIE IST INHALTLICH "
               "MERKWUERDIG: 'zweitbestes Funding schlaegt bestes "
               "Funding'. Das koennte heissen, dass EXTREMES Funding ein "
               "Warnsignal ist statt des besten Falls - eine eigene "
               "Hypothese, die nie geprueft wurde. ⚠️ Nicht Teil von B9, "
               "aber notiert", "gilt",
               "n92_b9_funding_buckel_auf_frei.py / offene Frage"),
    Befundlage("2.253", "✔✔ B10: AUF `frei` IST DIE BESETZUNG "
               "AUSGEGLICHEN UND DER BUCKEL VERAENDERT. `schnitt` "
               "liefert dort +1,28 / +1,59 / +0,28 / -1,19 / -1,96 bei "
               "48/48/47/48/48 Ankern je Fuenftel. N-65 fand auf der "
               "20-%-Menge dagegen +4,07 / +5,55 / +9,49 / +1,71 / -4,65 "
               "- einen ausgepraegten HOCHPUNKT IN DER MITTE. Auf `frei` "
               "sind nur Fuenftel 0 und 1 vertauscht, danach faellt es "
               "sauber", "gilt", "n93_b10_schnitt_stufen_auf_frei.py",
               basis="Messmenge v1, Menge frei, Live-Ableitung"),
    Befundlage("2.253-dieselbe-form", "✔✔✔ UND ES IST EXAKT DIESELBE "
               "FORM WIE BEI `funding`: +0,77 / +1,40 / +0,22 / -0,64 / "
               "-1,75, ebenfalls Hochpunkt bei Fuenftel 1. Zwei "
               "UNABHAENGIGE Groessen - Funding aus dem Terminmarkt, "
               "`schnitt` aus der Kursreihe - zeigen auf `frei` denselben "
               "Knick an derselben Stelle", "gilt",
               "n93_b10_schnitt_stufen_auf_frei.py",
               basis="Messmenge v1, Menge frei"),
    Befundlage("2.253-kontrolle", "✔ Die Kontrolle trennt sauber: "
               "`zufall` hat auf `frei` eine Spanne von 0,28 gegen "
               "`schnitt`s 3,55 und `funding`s 3,15 - beide Beitraege "
               "liegen ZWOELFFACH darueber", "gilt",
               "n93_b10_schnitt_stufen_auf_frei.py"),
    Befundlage("2.253-schaetzer", "⚠️ DIE GEGENPROBE HAT SICH GELOHNT: "
               "bei `schnitt` gehen Median (+1,28) und MITTEL (+62,39) "
               "weit auseinander - seine Verteilung hat schwere Raender "
               "(536 Symbole gegen `funding`s 300, die zusaetzlichen sind "
               "kleinere Coins). Bei `funding` stimmen beide fast "
               "ueberein. ⚠️ Auch die Kontrolle wird mit dem Mittel wild "
               "(+0,56 / -7,23 / +2,72 / -0,60 / +4,55) - der MEDIAN ist "
               "hier richtig", "gilt",
               "n93_b10_schnitt_stufen_auf_frei.py"),
    Befundlage("2.254", "⚠️⚠️⚠️ B10 IST DAMIT KEINE MESSFRAGE MEHR, "
               "SONDERN EINE MASSSTABSFRAGE: `schnitt` erfuellt die "
               "Monotonie-Vorgabe GENAUSO WENIG wie `funding` - und "
               "`funding` laeuft LIVE. Entweder die Vorgabe gilt streng, "
               "dann muesste auch `funding` fallen; oder sie gilt nicht "
               "streng, dann ist `schnitt` registrierbar (100 % "
               "Abdeckung, R-R9 im Gefolge). Das ist eine "
               "Nutzerentscheidung", "gilt",
               "n93_b10_schnitt_stufen_auf_frei.py"),
    Befundlage("2.254-praezedenz", "✔ Und das Projekt hat genau diese "
               "Lage schon einmal benannt (2.161-massstab): 'Einen "
               "Kandidaten an einer Huerde scheitern zu lassen, die die "
               "Bestandsbeitraege nie nehmen mussten, waere zweierlei "
               "Mass gewesen.' Damals fuehrte es zur Zeitstabilitaets"
               "pruefung der LEBENDEN Beitraege - hier fuehrt es zur "
               "Monotoniefrage", "gilt", "Befund 2.161-massstab"),
    Befundlage("2.255", "⚠️ B11 IST NICHT UNBERUEHRT - Nutzerhinweis "
               "09.09.: 'glaube zu Extremfunding gab es bereits eine "
               "Bewertung'. Er hat recht: `funding_extrem` ist ein "
               "registrierter Kandidat. ⚠️ ABER er misst eine ANDERE "
               "Achse - den Abstand vom EIGENEN Normalzustand in MAD, "
               "VORZEICHENLOS, je Symbol. B11 fragt nach der FORM der "
               "Querschnitts-Rangskala", "gilt",
               "messe_kandidaten_als_regel.py / Nutzerhinweis 09.09."),
    Befundlage("2.255-teilbeleg", "⚠️ Trotzdem ist er ein TEILBELEG "
               "gegen die B11-These: waere extremes Funding ein "
               "Warnsignal, muesste `funding_extrem` es zeigen. Er zeigt "
               "im Gesamtlauf WIDERSPRUCH (traegt auf 20 %, nicht auf "
               "50 %), und F-207 haelt fest, dass er die Live-Sperre "
               "NICHT verbessert", "gilt",
               "Befund 2.219 / F-207"),
    Befundlage("2.255-aber", "⚠️⚠️ WAS DIE THESE DAGEGEN STUETZT: der "
               "Knick sitzt bei `funding` UND bei `schnitt` an DERSELBEN "
               "Stelle (Fuenftel 1 ueber Fuenftel 0), auf `frei`, bei "
               "zwei unabhaengigen Datenquellen. Das ist schwer als "
               "Zufall zu lesen - und es waere eine Aussage ueber den "
               "MARKT, keine Messschwaeche", "gilt",
               "n93_b10_schnitt_stufen_auf_frei.py"),
    Befundlage("2.256", "⚠️⚠️⚠️ MEIN VORSCHLAG IST DURCHGEFALLEN: die "
               "SPANNE gegen den Nullpunkt trennt NICHT. Auf `frei` "
               "bestehen ALLE ACHT Kandidaten - darunter `rsi` (2,16) "
               "und `amihud` (1,32), die im Gesamtlauf NICHT tragen. Nur "
               "die Kontrolle faellt durch (0,28 gegen p97,5 = 0,70). Ein "
               "Kriterium, das jeden durchlaesst, haelt niemanden auf",
               "gilt", "n94_spanne_statt_monotonie.py",
               basis="Messmenge v1, Menge frei, 40 Nullziehungen"),
    Befundlage("2.256-grund", "✔ DER GRUND IST IM NACHHINEIN "
               "EINLEUCHTEND: die Spanne misst, ob die Fuenftel "
               "AUSEINANDERLIEGEN - nicht, ob sie etwas BEDEUTEN. Auch "
               "`rsi` spreizt sich, ohne zu tragen. Spreizung und "
               "Wirkung sind zwei verschiedene Dinge", "gilt",
               "n94_spanne_statt_monotonie.py"),
    Befundlage("2.257", "⚠️⚠️ UND DIE GEGENPROBE ZEIGT, WIE SCHIEF DIE "
               "MONOTONIE STEHT: von acht Kandidaten sind nur `turnover` "
               "und `vola` monoton. SECHS sind es nicht - darunter ZWEI "
               "LIVE LAUFENDE (`funding` und `oi_aenderung`). Die "
               "Vorgabe wurde nie an den Bestandsbeitraegen geprueft",
               "gilt", "n94_spanne_statt_monotonie.py",
               basis="Messmenge v1, Menge frei"),
    Befundlage("2.258", "⚠️ DIE RICHTIGE FRAGE IST EINE ANDERE, und sie "
               "braucht kein drittes Kriterium: IST DIE NICHT-MONOTONIE "
               "STABIL? Reproduziert 'Fuenftel 1 ueber Fuenftel 0' ueber "
               "Haelften und Teilmengen, ist es ein MARKTEFFEKT - dann "
               "ist die Stufentabelle richtig und die Monotonie-Vorgabe "
               "war falsch. Kippt es, ist es Rauschen und die Vorgabe hat "
               "einen Sinn", "gilt", "Vorschlag 09.09.2026"),
    Befundlage("2.258-beides", "✔ Und es beantwortet B10 UND B11 in einem "
               "Zug: der Knick sitzt bei `funding` und `schnitt` an "
               "DERSELBEN Stelle, bei zwei unabhaengigen Datenquellen. "
               "Ist er stabil, ist 'das Extrem ist nicht der beste Fall' "
               "belegt - und das waere eine Aussage ueber den MARKT",
               "gilt", "Vorschlag 09.09.2026"),
    Befundlage("2.259", "✔✔✔ N-95: DER KNICK IST NICHT BELEGT - und "
               "zwar mit TRENNSCHAERFE, nicht aus Untermacht. Bei den "
               "beiden Beitraegen, wo die Maschinerie nachweislich "
               "arbeitet (`funding` d34 +0,0656 [+0,019..+0,118] "
               "TRENNBAR, `oi_aenderung` d34 +0,0520 [+0,007..+0,094] "
               "TRENNBAR), ist d01 NICHT trennbar (+0,0402 [-0,037.."
               "+0,116] und +0,0260 [-0,027..+0,083])", "abgeloest",
               "n95_ist_der_knick_stabil.py",
               abgeloest_durch="2.263",
               warum="Gemessen wurde auf `frei` - der RANGmenge. Auf der AUSWAHLmenge (20 %), fuer die die Beitraege gebaut sind, ist d01 bei `funding` TRENNBAR (+0,2069 [+0,0137 .. +0,4304]) bei stummer Kontrolle. Der Nullbefund gilt fuer die Rangmenge, nicht fuer die Bewertungsmenge - N-96 hat ihn auf `frei` exakt reproduziert (R-R11 erfuellt), bevor er eingeschraenkt wurde.",
               basis="Messmenge v1, Menge frei, 40 Nullziehungen"),
    Befundlage("2.259-b11", "✔✔ DAMIT IST B11 BEANTWORTET: 'das Extrem "
               "ist nicht der beste Fall' ist NICHT belegt. Der "
               "Unterschied zwischen Fuenftel 0 und 1 ist Rauschen. ⚠️ "
               "Und das passt zu `funding_extrem`, der im Gesamtlauf "
               "Widerspruch zeigt und die Live-Sperre nicht verbessert "
               "(F-207) - zwei unabhaengige Zugaenge, dasselbe Ergebnis",
               "abgeloest", "n95_ist_der_knick_stabil.py",
               abgeloest_durch="2.263 / 2.264",
               warum="Auf der Auswahlmenge ist der Unterschied trennbar, auf der Live-Menge (k=2 je Tag) mangels Besetzung gar nicht beurteilbar. B11 ist damit wieder OFFEN - als Frage der Datenlage, nicht als beantwortete Frage."),
    Befundlage("2.259-kontrollen", "✔ Die Kontrolle ist ueberall sauber: "
               "`zufall` zeigt weder bei d01 noch bei d34 einen "
               "trennbaren Wert, in keiner Haelfte. Und `schnitt` ist "
               "UNTERMAECHTIG - auch sein d34 ist nicht trennbar, also "
               "sagt sein d01 nichts. `turnover` zeigt ein trennbares "
               "NEGATIVES d01, dessen Haelften aber kippen (+0,021 gegen "
               "-0,262)", "gilt", "n95_ist_der_knick_stabil.py"),
    Befundlage("2.260", "✔✔✔ UND DAMIT IST AUCH B10 GELOEST - OHNE DIE "
               "MONOTONIE-VORGABE AUFZUGEBEN. Werden die zwei Stufen "
               "zusammengelegt, die GEMESSEN nicht unterscheidbar sind, "
               "werden BEIDE Tabellen monoton fallend: `funding` +1,06 / "
               "+1,06 / +0,12 / -0,54 / -1,70 und `schnitt` +1,44 / "
               "+1,44 / +0,28 / -1,19 / -1,96", "abgeloest",
               "n95_ist_der_knick_stabil.py",
               abgeloest_durch="2.263 / 2.264 / 2.265",
               warum="Die Zusammenlegung ist NICHT AUSGEFUEHRT. Es gibt keine Menge, auf der d01 und der Pruefstein d34 zusammenpassen. Und `pruefe_funding_monoton.py:59` prueft mit 0,02 R Toleranz, waehrend die Inversion 0,002 R betrug - der Knick war bekannt und bewusst durchgelassen, das Zusammenlegen waere Kosmetik statt Korrektur.",
               basis="Messmenge v1, Menge frei"),
    Befundlage("2.260-nicht-angepasst", "⚠️ UND ES IST KEINE ANPASSUNG "
               "AN DAS GEWUENSCHTE ERGEBNIS: die Zusammenlegung ist durch "
               "die MESSUNG begruendet (d01 nicht trennbar, waehrend d34 "
               "es ist) und war VORAB als Konsequenz benannt - im "
               "Skriptkopf, vor dem Lauf: 'Dann waeren Stufe 0 und 1 "
               "ZUSAMMENZULEGEN, nicht die Beitraege zu verwerfen'",
               "abgeloest", "n95_ist_der_knick_stabil.py",
               abgeloest_durch="2.263",
               warum="Die Aussage ueber das VERFAHREN bleibt richtig - die Konsequenz stand vorab im Skriptkopf. Sie praesupponiert aber die Zusammenlegung, und die ist nicht ausgefuehrt: auf der Auswahlmenge ist d01 trennbar."),
    Befundlage("2.260-rr9", "⚠️⚠️ ES IST ABER EIN EINGRIFF IN EINEN LIVE "
               "LAUFENDEN BEITRAG: `funding`s registrierte Stufen "
               "wuerden von +0,82/+1,30/... auf +1,06/+1,06/... wechseln. "
               "Das aendert die Beitragslage und loest R-R9 aus - die "
               "Schwelle waere neu zu kalibrieren. NUTZERENTSCHEIDUNG, "
               "nicht stille Automatik", "abgeloest",
               "agent/wahrscheinlichkeit.BEITRAEGE / R-R9",
               abgeloest_durch="2.263",
               warum="Die Bedingung ist richtig geblieben, der Fall aber nicht eingetreten: die Stufen wurden NICHT geaendert, R-R9 wurde nicht ausgeloest. Der Vorgang steht als Kommentar neben der Tabelle in `agent/wahrscheinlichkeit.py`."),
    Befundlage("2.261", "⚠️ ZWEI VORSCHLAEGE VON MIR SIND HEUTE "
               "DURCHGEFALLEN, bevor der dritte trug: die MONOTONIE als "
               "Huerde (sie reisst den Bestand mit - sechs von acht "
               "Kandidaten brechen sie, darunter zwei live) und die "
               "SPANNE als Ersatz (sie laesst alle acht durch). Erst die "
               "Frage 'ist der Knick STABIL' hat entschieden - und sie "
               "brauchte kein neues Kriterium, nur die vorhandene "
               "Maschinerie", "abgeloest", "Selbstbefund 09.09.2026",
               abgeloest_durch="2.263 / 2.266",
               warum="Auch der DRITTE Vorschlag hat nicht getragen. Die Frage 'ist der Knick stabil' war richtig gestellt, aber auf der falschen Menge beantwortet - und mein erster Korrekturlauf hatte selbst die Rangreihenfolge vertauscht. Der Tag endete mit drei durchgefallenen Vorschlaegen, nicht mit zweien."),
    Befundlage("2.262", "⚠️⚠️⚠️ DER BETRIEBSABLAUF IST ZWEISTUFIG - und "
               "F-212s Messmenge bildet ihn nach. `marktrang.raenge` "
               "bildet den Rang ueber die MESSBASIS (536) und liest ihn "
               "fuer unsere Symbole nur ab (,DER RANG ENTSTEHT UEBER DEN "
               "MARKT'); `auswahl.waehle` nimmt danach k=2 aus der "
               "Watchlist nach 250-Tage-Entwicklung - 4,7 %. F-212s "
               ",oberste 5 % nach Momentum' ist damit KEIN Messkonstrukt, "
               "sondern eine Nachbildung genau dieser Auswahl, nur auf "
               "der Messbasis statt auf der Watchlist. ⚠️ Damit ist der "
               "Widerspruch aus 2.228 aufloesbar: die Ableitungsbasis "
               "(`frei`) ist die Rangmenge, die Auswahlmenge ist die "
               "Bewertungsmenge - zwei verschiedene Rollen, kein "
               "Widerspruch", "gilt",
               "agent/marktrang.py:643 / agent/auswahl.py:70"),
    Befundlage("2.263", "⚠️⚠️⚠️ DIE MENGE ENTSCHEIDET DAS URTEIL UEBER "
               "DEN KNICK (N-96). `d01` = Fuenftel 1 minus Fuenftel 0 bei "
               "`funding`: auf `frei` +0,0402 [-0,0369 .. +0,1159] NICHT "
               "trennbar, auf 20 % +0,2069 [+0,0137 .. +0,4304] "
               "TRENNBAR - und die Kontrolle ist in BEIDEN Zellen stumm "
               "(+0,0139 bzw. +0,0033). Auf `frei` traegt `d34` (+0,0656 "
               "[+0,0191 .. +0,1180]), der Aufbau arbeitet dort also; auf "
               "20 % traegt `d34` NICHT (+0,0786), waehrend `d01` traegt. "
               "⚠️⚠️ ES GIBT KEINE MENGE, AUF DER BEIDES ZUSAMMENPASST - "
               "und damit keinen Beleg fuer das Zusammenlegen von Stufe 0 "
               "und 1", "gilt",
               "n96_d01_auf_der_selektierten_menge.py",
               basis="H20 · Messmenge V1 · frei/5/10/20 % · 40 Nullziehungen"),
    Befundlage("2.264", "⚠️⚠️ AUF DER LIVE-MENGE IST DIE FRAGE NICHT "
               "BEANTWORTBAR (N-97). Auf der Watchlist (43 Werte, Rang "
               "ueber die Messbasis, Verengung NACH dem Rang wie 2.229) "
               "hat `d34` nur 2,7 bzw. 2,4 Anker je Fuenftel - KEIN "
               "BEFUND, nicht ,traegt nicht'; `d01` hat dort ein Band von "
               "±0,25 R. ⚠️⚠️ Und die Menge, auf der die ENTSCHEIDUNG "
               "faellt, sind k=2 Werte pro Tag. Eine fuenfstufige Tabelle "
               "laesst sich darauf nicht beurteilen - das ist keine Frage "
               "der Sorgfalt, sondern der Datenlage. Nebenbefund: von 43 "
               "Watchlist-Werten liegen je Tag 4,2/4,1/~11/2,7/2,4 in den "
               "Funding-Fuenfteln - die Stufen -0,54 und -1,70 tragen "
               "unter drei Werte je Tag", "gilt",
               "n97_d01_auf_der_watchlist.py",
               basis="H20 · Watchlist 43 Symbole · Rang ueber 536"),
    Befundlage("2.265", "⚠️⚠️ ,MONOTON' HIESS NIE STRENG MONOTON. "
               "`pruefe_funding_monoton.py:59` prueft mit einer TOLERANZ "
               "von 0,02 R (`werte[i] >= werte[i+1] - 0.02`). Die "
               "Inversion vom 30.08. betrug 0,002 R - ein Zehntel davon. "
               "Der Knick war BEKANNT und bewusst durchgelassen, nicht "
               "uebersehen. ⚠️ Die Toleranz steht nirgends in der "
               "Registrierung, die schlicht ,monoton ueber fuenf "
               "Fuenftel' behauptet - und sie ist die EINZIGE "
               "Monotoniepruefung im System; `turnover` hat gar keine. "
               "Damit waere das Zusammenlegen keine Fehlerkorrektur, "
               "sondern Kosmetik an einer bereits bewerteten Stelle",
               "gilt", "pruefe_funding_monoton.py:59"),
    Befundlage("2.266", "⚠️⚠️⚠️ EIGENER KONSTRUKTIONSFEHLER, VOM CODE "
               "GEFANGEN: der erste N-96-Lauf hat ZUERST VERENGT UND DANN "
               "GERANGT. Damit entstehen Fuenftel INNERHALB der Kohorte - "
               "ein Merkmal, das weder `marktrang.raenge` noch `sammle` "
               "berechnet (beide: ,NACH dem Rang verengen, nie davor'). "
               "Vorabtest auf Kunstdaten mit korrelierter Auswahl: 0 % "
               "gemeinsame Mitglieder in Fuenftel 0. ⚠️ Bei `funding` "
               "blieb der Schaden klein (+0,2317 gegen +0,2069), weil "
               "seine Momentum-Korrelation +0,002 ist - der Fehler war "
               "real, seine Wirkung hier zufaellig gering. ⚠️⚠️ Gefunden "
               "hat ihn nicht die Pruefsuite, sondern das Nachlesen im "
               "BETRIEBSCODE - dieselbe Lehre wie 2.229", "gilt",
               "Selbstbefund 09.09.2026 / Befund 2.229"),
    Befundlage("2.267", "⚠️⚠️⚠️ K-1a GEMESSEN: KEIN registrierter "
               "Beitrag traegt auf der A1-MENGE - und zwar bei KEINEM k "
               "(2, 3, 5, 8, 13, 21, alle A1-waehlbaren). `funding` "
               "-0,0264 bei k=2 bis +0,0151 bei allen; `turnover` "
               "durchgehend negativ (-0,0590 bis -0,0116); "
               "`oi_aenderung` +0,0374 bis +0,0220. Alle Baender "
               "schliessen den Nullpunkt ein. ⚠️ Die Kontrolle `zufall` "
               "traegt bei KEINEM k - 7 von 7 sauber, der Lauf gilt",
               "gilt", "k1a_beitrag_auf_der_a1_menge.py",
               basis="H20 · A1-Menge top-k je Tag · gepoolt nach "
                     "Messstandard · 40 Nullziehungen"),
    Befundlage("2.267-kein-nullbefund", "⚠️⚠️ UND DAS IST KEIN "
               "NULLBEFUND, sondern fehlende AUFLOESUNG: bei k=2 findet "
               "die Anlage nicht einmal einen GEPFLANZTEN Effekt von "
               "0,40 R - Urteil ,KEIN BEFUND (Leiter zu kurz)' bei "
               "`funding`, `turnover` UND der Kontrolle. Erst ab k=21 "
               "bzw. auf der vollen A1-Menge reicht die Leiter (,traegt "
               "nicht bis 0,20'). ⚠️ Die registrierten Beitraege sind "
               "damit NICHT widerlegt - sie sind dort nicht pruefbar",
               "gilt", "k1a_beitrag_auf_der_a1_menge.py"),
    Befundlage("2.268", "⚠️⚠️⚠️ `schnitt` SAH BEI k=2 UND k=3 WIE EIN "
               "TRAEGER AUS (+0,8697 [+0,1099 .. +1,6776] und +0,4989) - "
               "es ist die KOLLINEARITAET aus 2.242. Die Diagnose zeigt "
               "es unmittelbar: die Regel sperrt auf der A1-Menge 82,3 % "
               "der Gewaehlten statt der definitionsgemaessen 20 %, und "
               "`frei` traegt im Schnitt 0,35 Anker JE TAG - weniger als "
               "einen. Der Sperranteil faellt 82/75/66/59/49/43/34 mit "
               "wachsendem k, die Wirkung spiegelbildlich "
               "0,87/0,50/0,21/0,11/0,04/-0,00/-0,03. ⚠️ Ursache: die "
               "A1-Regel waehlt die zwei besten nach 250-Tage-"
               "Entwicklung - wer so gestiegen ist, steht ueber seinem "
               "eigenen Schnitt. A1 und `schnitt` messen dasselbe",
               "gilt", "k1a_diagnose_besetzung.py",
               basis="H20 · A1-Menge · Sperranteil je k"),
    Befundlage("2.269", "⚠️⚠️ DIE REGISTRIERTEN SPERREN FEUERN IM "
               "BETRIEB KAUM: auf der Watchlist sperrt `turnover` 1,9 % "
               "der Werte (bei k=2: 5,5 %), `funding` 13,2 %, waehrend "
               "`oi_aenderung` mit 20,4 % und die Kontrolle mit 20,0 % "
               "genau auf dem definitionsgemaessen Fuenftel liegen. "
               "⚠️ Eine Sperre, die zwei von hundert Werten trifft, ist "
               "praktisch keine - und sie erklaert, warum die Beitraege "
               "laut F-212 auf 1,5 % der Anker wirken. Der Grund ist die "
               "Messbasis: `turnover` deckt 66 von 536 Symbolen ab, und "
               "die Watchlist liegt in seiner Verteilung unten",
               "gilt", "k1a_diagnose_besetzung.py"),
    Befundlage("2.270", "✔ A1 SPERRT WIRKLICH - am Betriebscode "
               "geprueft, nicht angenommen: `rollen_lauf.py:1269` endet "
               "mit `return`, wenn ein Symbol nicht in "
               "`auswahl['gewaehlt']` steht. ⚠️ ABER NUR OHNE BESTAND "
               "(`not _hat_bestand`) - gehaltene Positionen umgehen die "
               "Auswahl ganz. Damit ist die Einstiegsmenge bestaetigt "
               "k=2 je Tag, und K-1b (Bestandsmenge) ist eine echte "
               "zweite Frage, keine Variante derselben",
               "gilt", "agent/rollen_lauf.py:1269"),
    Befundlage("2.271", "⚠️⚠️ 14 VON 43 WATCHLIST-WERTEN SIND HEUTE GAR "
               "NICHT A1-WAEHLBAR - ihnen fehlt die Jahreshistorie, und "
               "`auswahl.rangliste` ueberspringt Werte mit "
               "`len(kerzen) <= 250`: AIOZ, AKT, ASTER, BRETT, CANTON, "
               "CAT, GRIFFAIN, HYPE, KAS, MON, MORPHO, PLUME, SUPRA, "
               "VSN. ⚠️ Ueber die ganze Historie sind im Schnitt nur "
               "14,0 Werte je Tag waehlbar (33 %), 2026 aber 37,5 "
               "(87 %) - wer den Durchschnitt als heutigen Zustand "
               "liest, unterschaetzt die Menge um mehr als das Doppelte",
               "gilt", "k1a_beitrag_auf_der_a1_menge.py"),
    Befundlage("2.272", "⚠️ KEIN WIDERSPRUCH ZU 2.229-funding, ABER "
               "AUCH KEINE REPRODUKTION (R-R11): K-1w misst `funding` "
               "auf der Watchlist mit +0,0886 [+0,0582 .. +0,1458], "
               "K-1a auf seiner vollen A1-Menge mit +0,0151 [-0,0101 .. "
               "+0,0366]. Zwei Unterschiede, beide meine: anderer "
               "SCHAETZER (gepoolt statt Tagesklammer) und andere MENGE "
               "(nur A1-waehlbare Symbole statt aller 43). 2.229-funding "
               "steht unveraendert - K-1a hat es nicht gemessen",
               "gilt", "k1a_beitrag_auf_der_a1_menge.py / R-R11"),
    Befundlage("2.273", "⚠️⚠️⚠️ DIE DRITTE STRUKTURELLE SPERRE DERSELBEN "
               "BAUART: `messnorm_auswahl.pruefe_auswahl` misst unter "
               "der TAGESKLAMMER - median(frei) minus median(alle) "
               "INNERHALB jedes Tages. Auf der A1-Menge (k=2) bleiben "
               "gemessen NULL verwertbare Tage. ⚠️ Zusammen mit A1 "
               "(Hebel: Band auf binaeren Daten viermal zu eng) und A2 "
               "(Akkumulation: Blockregel bei H90 braeuchte 22 Jahre) "
               "steht dreimal dieselbe Aussage: DIE MESSANLAGE REICHT "
               "NICHT DORTHIN, WO DAS SYSTEM ENTSCHEIDET. Das ist kein "
               "Messfehler, sondern eine Aussage ueber die Datenlage - "
               "und die Folge ist eine NUTZERENTSCHEIDUNG: entweder die "
               "Kette entscheidet auf breiterer Menge, oder die "
               "Bewertung gilt ausdruecklich nur auf einer "
               "Stellvertretermenge als validiert",
               "gilt", "k1a_beitrag_auf_der_a1_menge.py / A1 / A2"),
    Befundlage("2.274", "⚠️⚠️⚠️ N-46 IST NICHT GESCHLOSSEN - meine "
               "BEGRUENDUNG ist von der eigenen Abbruchbedingung "
               "widerlegt. Vorhergesagt war: die Tagesmischung liegt "
               "DEUTLICH HOEHER als der Verschub. Gemessen liegt sie "
               "durchgehend NIEDRIGER (Faktor 0,2 bis 0,6): amihud "
               "+0,0070 gegen +0,0323 · vola +0,0078 gegen +0,0364 · "
               "schnitt +0,0154 gegen +0,0571 · rsi +0,0121 gegen "
               "+0,0271 · zufall +0,0041 gegen +0,0069. ⚠️ Die "
               "Tagesmischung ist damit der GROSSZUEGIGERE Nullpunkt, "
               "nicht der zu strenge - genau umgekehrt zu meiner "
               "Begruendung", "gilt", "n98_n46_laengs_nullpunkt.py",
               basis="H20 · Laengs-Rang FENSTER 250 · 40 Verschuebe "
                     "(min. 250 Tage) · Messmenge V1"),
    Befundlage("2.274-rr11", "⚠️⚠️ UND DIE AUSGANGSBEOBACHTUNG VON N-46 "
               "IST NICHT REPRODUZIERT: sie lautet ,bei `amihud` "
               "lieferte die Kontrolle +0,620 gegen einen echten Wert "
               "von +0,713'. Gemessen steht amihuds echter Wert bei "
               "-0,0445 und die Tagesmischung bei +0,0022 - drei "
               "Groessenordnungen daneben, also eine andere Skala und "
               "eine andere Messung. **R-R11 ist nicht erfuellt**, und "
               "ohne Reproduktion ist der Blocker N-46 weder geloest "
               "noch widerlegt", "gilt",
               "n98_n46_laengs_nullpunkt.py / R-R11"),
    Befundlage("2.275", "✔✔ WAS TROTZDEM STEHT - der zirkulaere Verschub "
               "ist als Nullmodell BRAUCHBAR, drei von vier Pruefungen "
               "sauber. P1 ZENTRIERT: bei `zufall` +0,0034 mit Streuung "
               "0,0026, also nahe null. P2 KONTROLLE: `zufall` traegt "
               "unter Verschub NICHT. P3 MACHT: ein gepflanzter Effekt "
               "von 0,20 R wird mit +0,0420 [+0,0374 .. +0,0465] "
               "gefunden - erwartet waren 0,20 x (1 - GRENZE) = 0,040. "
               "⚠️ Der Treffer ist exakt und bestaetigt nebenbei zum "
               "dritten Mal den 20-%%-Skalenfaktor aus Fehler 5",
               "gilt", "n98_n46_laengs_nullpunkt.py"),
    Befundlage("2.276", "⚠️⚠️ DIE ENTSCHEIDUNG ZWISCHEN DEN BEIDEN "
               "NULLPUNKTEN HAENGT NICHT AN IHRER HOEHE, sondern an der "
               "FEHLALARMQUOTE gegen bekannte Wahrheit. Genau dieses "
               "Verfahren hat am 09.09. den Nullbezug entschieden (150 "
               "Nullwelten, drei Basen: `nullpunkt` 2,7 %% Fehlalarme "
               "bei Soll 2,5 %%, `null_oben` 0 %% aber nur 63 %% "
               "Fundquote, `null` 28 %%). Fuer die LAENGS-Achse steht "
               "dieser Selbsttest aus - er ist der naechste Schritt von "
               "N-46, nicht eine weitere Begruendung", "gilt",
               "selbsttest_messanlage.py / Befund 2.204"),
    Befundlage("2.277", "⚠️ NEBENBEFUND: KEIN Kandidat traegt auf der "
               "LAENGS-Achse - weder unter dem Verschub noch unter der "
               "Tagesmischung. `amihud` -0,0445 · `vola` +0,0056 · "
               "`schnitt` -0,0163 · `rsi` -0,0104. ⚠️⚠️ `amihud` ist "
               "dabei UMGEKEHRT gerichtet und sein Band schliesst die "
               "Null knapp aus ([-0,0994 .. -0,0005]) - das ist keine "
               "Bestaetigung, aber auch kein Nullbefund, und es passt "
               "zu 2.166 (er misst Ausfuehrbarkeit, nicht Potential). "
               "⚠️ Das Urteil steht unter dem Vorbehalt aus 2.274: "
               "solange der Nullpunkt nicht entschieden ist, ist auch "
               ",traegt nicht' nur vorlaeufig", "abgeloest",
               "n98_n46_laengs_nullpunkt.py",
               abgeloest_durch="2.283",
               warum="Es ist UNTERMACHT, kein Nullbefund. Bei der Beharrlichkeit von `schnitt` (0,985) findet die Anlage einen Effekt von 0,03 R in 20 % und von 0,05 R in 50 % der Faelle - die echten Kandidaten liegen genau in diesem Bereich. Ein ,traegt nicht' sagt dort nichts ueber die Welt.",
               basis="H20 · Laengs-Rang FENSTER 250 · Messmenge V1"),
    Befundlage("2.278", "✔ HERKUNFT SAUBER GETRENNT (Nutzervorgabe "
               "10.09.: ,trennen nach vor und nach dem aktuellen Umbau - "
               "Messungen, Dokumente und Code'). N-46 uebernimmt "
               "`laengs_rang` und `wirkung` aus `n75` (07.09., VOR dem "
               "Standard) - beides DEFINITIONEN, kein Nullmodell. Band, "
               "Nullpunkt, Perzentil und Leiter kommen aus `messnorm` "
               "(NACH). Der Akkumulationsbefund vom 28.08. dient als "
               "VORBILD, nicht als Beleg. ⚠️ Dafuer gibt es jetzt "
               "`soll_ist.py`, das die Grenze fuer alle drei Ebenen "
               "ausweist: Code 174 von 303 Altbestand · Messungen 356 "
               "von 458 ohne vermerkte Basis · Dokumente 48 von 55 vor "
               "dem Umbau", "gilt", "soll_ist.py / REGISTER_Werkzeuge"),
    Befundlage("2.279", "⚠️⚠️⚠️ DIE HEBELDIAGNOSE IST KORRIGIERT: "
               "NICHT ,die Bewertung ist zu schwach', sondern ,sie ist zu "
               "GROB'. Ich habe drei Tage lang F-220 zitiert (,nur EINE "
               "Lage erreicht 2,60x') - F-220 ist am 06.09. "
               "ZURUECKGEZOGEN, und der Kalibrierungsfaktor 19,5 % ist am "
               "05.09. gefallen. Es gilt 2.174-neu: unkalibriert "
               "erreichen ZWEI Lagen die Zielzone (funding bestes 3,90x, "
               "funding bestes + turnover mittleres 4,56x), und die "
               "Abstufung ist ECHT", "gilt", "Befund 2.174 / 2.174-neu"),
    Befundlage("2.279-zerlegt", "✔ ,SCHWACH' IST DAMIT ZERLEGT - auf "
               "Nutzerfrage 10.09. (,erkennen wir ueberhaupt gute "
               "Hebelchancen?'): NIVEAU ✔ ja, zwei Lagen erreichen "
               "2-5x · AUFLOESUNG ⚠️ nein, die Abstufung SPRINGT von "
               "1,02x auf 3,90x, weil die Beitraege Fuenftel sind "
               "(2.174-grenzen) · TRENNSCHAERFE ⚠️ NIE GEMESSEN - ob eine "
               "hoehere Quote mit einer hoeheren REALEN Trefferquote "
               "einhergeht · DECKEL ✔ `hebel_max` = 10 vorhanden. "
               "⚠️⚠️ Wir erkennen ,gut' gegen ,nicht gut', aber nicht "
               ",wie gut'", "gilt", "Befund 2.174-grenzen / Nutzerfrage "
               "10.09."),
    Befundlage("2.280", "⚠️⚠️ A1 IST DAMIT KEINE NACHARBEIT MEHR, "
               "SONDERN VORAUSSETZUNG. Die offene Trennschaerfefrage "
               "(,geht ein hoeherer Hebel mit einer hoeheren realen "
               "Trefferquote einher?') fragt nach BINAEREN Ausgaengen - "
               "und genau dort ist unser Band viermal zu eng, weshalb die "
               "Kontrolle traegt (2.238). Ohne A1 ist die Frage nicht "
               "beantwortbar, mit welcher Simulation auch immer",
               "gilt", "Befund 2.238 / 2.279-zerlegt"),
    Befundlage("2.281", "⚠️⚠️⚠️ DREI FEHLAUSSAGEN AN EINEM TAG AUS "
               "DERSELBEN URSACHE: ich habe aus MEMORY-Eintraegen "
               "zitiert, ohne im REGISTER gegenzupruefen. (1) ,Der Hebel "
               "ist konzeptionell abgeschlossen' - der Eintrag schliesst "
               "nur die Instrument-Achse. (2) ,`portfolio_wert_historie` "
               "ist LEER' - sie laeuft seit dem 08.05. mit 91 Zeilen, ich "
               "las die veraltete Desktop-Kopie. (3) ,Nur EINE Lage "
               "erreicht 2,60x' - F-220 ist zurueckgezogen. "
               "⚠️⚠️ Ein Memory-Eintrag ist ein SCHNAPPSCHUSS vom Tag "
               "seiner Entstehung; das Register wird ERZEUGT und ist "
               "aktuell. Beide sehen beim Lesen gleich verbindlich aus",
               "gilt", "Selbstbefund 10.09.2026"),
    Befundlage("2.282", "✔✔✔ N-46 IST GELOEST - UND ZWAR MIT DEM "
               "VORHANDENEN WERKZEUG. Gegen bekannte Wahrheit gemessen "
               "(100 Nullwelten je Beharrlichkeit, Soll 2,5 %) arbeiten "
               "BEIDE Nullmodelle: Verschub 0,0 %% / 1,0 %%, "
               "Tagesmischung 1,0 %% / 4,0 %%. ⚠️⚠️ Damit ist N-46s "
               "Praemisse WIDERLEGT - ,die Tagesmischung taugt dort "
               "nicht' trifft nicht zu. Kriterium 4 des Vierfachtests "
               "(Regel 3 laengs) ist nicht mehr blockiert, und damit "
               "auch nicht der Weg zu einem dritten Beitrag", "gilt",
               "n99_n46b_fehlalarm_laengs.py",
               basis="100 Nullwelten je Beharrlichkeit 0,61 und 0,985 · "
                     "ueberlappung=H20 · 20 Ziehungen je Nullpunkt"),
    Befundlage("2.282-fund", "✔✔ UND DIE FUNDQUOTE ENTSCHEIDET KLAR FUER "
               "DIE TAGESMISCHUNG - auf SECHS von acht Sprossen besser, "
               "auf zwei gleich, nirgends schlechter. Bei 0,985: 0,03 R "
               "20,0 %% gegen 5,0 %% · 0,05 R 50,0 %% gegen 25,0 %% · "
               "0,08 R 90,0 %% gegen 70,0 %%. ⚠️ Das ist exakt das "
               "`null_oben`-Muster vom 09.09.: das konservativere Modell "
               "hat weniger Fehlalarme und zahlt mit Fundkraft. Dort fiel "
               "die Entscheidung genauso - fuer das Modell, das die "
               "SOLLQUOTE trifft", "gilt",
               "n99_n46b_fehlalarm_laengs.py",
               basis="40 Welten je Sprosse · Leiter 0,03/0,05/0,08/0,12 R "
                     "auf den LAENGS-Rang gepflanzt"),
    Befundlage("2.283", "⚠️⚠️⚠️ DIE AUFLOESUNGSGRENZE DER LAENGS-ACHSE - "
               "und sie entwertet einen eigenen Nebenbefund. Bei hoher "
               "Beharrlichkeit (0,985, wie `schnitt`) findet die Anlage "
               "einen Effekt von 0,03 R in 20 %%, von 0,05 R in 50 %% "
               "und erst ab 0,08 R in 90 %% der Faelle. **Die echten "
               "Kandidaten liegen bei 0,02 bis 0,05 R.** ⚠️⚠️ Damit ist "
               "N-46as Nebenbefund ,kein Kandidat traegt laengs' (2.277) "
               "KEINE Aussage ueber die Welt, sondern UNTERMACHT - "
               "genau fuer die beharrlichen Groessen, um die es geht",
               "gilt", "n99_n46b_fehlalarm_laengs.py"),
    Befundlage("2.284", "⚠️⚠️ SELBSTBEFUND: MEIN VERSCHUB-BAU WAR NICHT "
               "NOETIG. N-46a hat ein Nullmodell gebaut, um ein Problem "
               "zu loesen, das die Messung nicht bestaetigt - die "
               "Tagesmischung war die ganze Zeit brauchbar. ⚠️ Die "
               "Ursache steht in 2.274-rr11: ich habe N-46s "
               "Ausgangsbeobachtung (,amihud: Kontrolle +0,620 gegen "
               "echten Wert +0,713') NIE reproduziert, sondern auf ihr "
               "gebaut. R-R11 verlangt die Reproduktion VOR dem Bau, "
               "nicht nur vor dem Widerruf", "gilt",
               "Selbstbefund 10.09.2026 / R-R11"),
    Befundlage("2.285", "⚠️ EIN VORBEHALT ZUR TAGESMISCHUNG, benannt: "
               "bei hoher Beharrlichkeit feuert sie mit 4,0 %% gegen ein "
               "Soll von 2,5 %% - das 1,6-fache. Bei niedriger "
               "Beharrlichkeit liegt sie mit 1,0 %% darunter. Sie "
               "KLAMMERT das Soll also, waehrend der Verschub durchgehend "
               "darunter liegt. Fuer beharrliche Groessen ist ein "
               "TRAEGT-Urteil damit etwas grosszuegiger, als das Band "
               "verspricht - kein Fehler, aber beim naechsten Grenzfall "
               "zuerst hier hinsehen", "gilt",
               "n99_n46b_fehlalarm_laengs.py"),
    Befundlage("2.286", "✔✔✔ A2 IST GELOEST - DIE AKKUMULATION IST "
               "MESSBAR. Nicht durch eine Aenderung am Horizont, sondern "
               "durch einen METHODENWECHSEL: ein PERMUTATIONSTEST "
               "(zirkulaerer Verschub) statt eines Bootstrap-Bandes. Er "
               "braucht keine Bloecke, weil der Verschub die "
               "Abhaengigkeitsstruktur ERHAELT statt sie zu zerschneiden - "
               "genau deshalb funktioniert er bei H90, wo 20 Bloecke "
               "5.400 Handelstage braeuchten. ⚠️ N-46b hat das NICHT "
               "geloest: dort ging es um den Nullpunkt, hier fehlte das "
               "BAND", "gilt", "n101_a2_akkumulation.py",
               basis="H90 · verbilligung als Perzentilrang · 518 Reihen · "
                     "400 Verschuebe · Messmenge V1"),
    Befundlage("2.286-schnitt", "✔✔ `schnitt` TRAEGT FUER DIE "
               "AKKUMULATION - der erste gemessene Beitrag fuer diese "
               "Lage ueberhaupt: Rangvorsprung +0,0470 gegen ein Nullband "
               "[-0,0121 .. +0,0106], p 0,000, auf 481 von 518 Symbolen, "
               "Kaufquote 19,3 %%. ⚠️ Das ist STAERKER als `UNTER_SMA` am "
               "28.08. (+0,0283) - und es passt, denn 2.155 haelt fest: "
               "`schnitt` und das Akkumulationsmass sind DIESELBE "
               "GROESSE", "gilt", "n101_a2_akkumulation.py"),
    Befundlage("2.287", "⚠️⚠️⚠️ `funding` UND `oi_aenderung` WIRKEN FUER "
               "DIE AKKUMULATION UMGEKEHRT - und das ist KEIN Nullbefund. "
               "`funding` -0,0230 gegen [-0,0105 .. +0,0093], p 0,000 · "
               "`oi_aenderung` -0,0178 gegen [-0,0075 .. +0,0076], "
               "p 0,000. Ihr ,gutes' Fuenftel (wenig Funding, wenig "
               "OI-Aufbau) ist systematisch der SCHLECHTERE Kauftag. "
               "⚠️⚠️ Beide sind LIVE als `strategien=(\'einstieg\',)` "
               "deklariert und wirken deshalb NICHT auf die Akkumulation - "
               "das ist nach diesem Befund ein GLUECK, kein Zufall: "
               "wuerden sie dort greifen, liefen sie rueckwaerts",
               "gilt", "n101_a2_akkumulation.py"),
    Befundlage("2.288", "⚠️ `turnover` TRAEGT fuer die Akkumulation "
               "(+0,0353, p 0,005) - aber auf nur 49 von 518 Symbolen, "
               "und sein Nullband ist mit ±0,022 das breiteste im Lauf. "
               "Dieselbe Abdeckungsgrenze wie ueberall (B6: die "
               "Umlaufmenge kommt fuer 66 Werte). Ein Befund unter "
               "Vorbehalt der Abdeckung, kein tragfaehiger Beitrag",
               "gilt", "n101_a2_akkumulation.py"),
    Befundlage("2.289", "✔✔ R-R11 IST ERFUELLT - die Kontrollen "
               "reproduzieren den 28.08.-Stand vor der ersten neuen "
               "Aussage: TIEFPUNKT (Positivkontrolle) +0,4245 gegen "
               "+0,4242 · WOCHENTAG (Negativkontrolle) -0,0005 gegen "
               "-0,0008 · `zufall` +0,0015, p 0,223. ⚠️ Die Aufloesung "
               "dieser Zielgroesse betraegt 0,0216 in RANGeinheiten - "
               "A9s Grenze (0,08 R) gilt hier NICHT, weil `verbilligung` "
               "ein Perzentilrang mit Basisrate 0,500 ist und keine "
               "R-Groesse", "gilt", "n101_a2_akkumulation.py"),
    Befundlage("2.290", "⚠️⚠️ DREI EIGENE FEHLER BEIM BAU, alle vor dem "
               "Lauf gefangen: (1) die Kauftage wurden ueber die "
               "Tagesliste aus `K.baue` auf die Kursreihe gemappt - die "
               "beginnt aber spaeter (Horizontabschnitt), die Maske waere "
               "STILL um einen unbekannten Betrag verschoben gewesen; "
               "jetzt kommt die Datumszuordnung aus derselben Abfrage wie "
               "die Kurse. (2) Der Verschub zog den Startpunkt des "
               "Symbols ab - das ist der dokumentierte 28.08.-Fehler mit "
               "umgekehrtem Vorzeichen, jede symbolabhaengige "
               "Verschiebung hebt die Gleichzeitigkeit auf. (3) Das "
               "Urteil kannte nur TRAEGT/traegt nicht und haette "
               "`funding` als Nullbefund ausgewiesen - dieselbe "
               "Verwechslung wie Fehler 4 vom 08.09.",
               "gilt", "Selbstbefund 10.09.2026"),
    Befundlage("2.291", "✔ DIE NAHT IST GEBAUT: `Beitrag.instrumente` "
               "als vierte Achse neben klassen/strategien/richtungen, "
               "Vorgabe LEER = alle. Bitgleich nachgewiesen (Quote "
               "0,37303333333333333 vor und nach dem Umbau), vier "
               "Waechter im Paket ,Stufen' - darunter einer, der "
               "festhaelt, dass HEUTE kein Beitrag eine Instrumentliste "
               "traegt. ⚠️ Der Grund: die Antwort ,gilt fuer alle "
               "Instrumente' steckte bis heute in der ABWESENHEIT eines "
               "Feldes - derselbe Fehler, den `assetklassen."
               "hebel_handelbar()` schon einmal behoben hat", "gilt",
               "agent/wahrscheinlichkeit.py / pruefe_pakete --paket Stufen"),
    Befundlage("2.291-entscheidung", "⚠️⚠️ FACHLICHE BEWERTUNG 10.09. "
               "(Nutzerauftrag): DER HEBEL KOMMT VORERST AUS DEM "
               "SPOT-WEG - aber NICHT, weil es dieselbe Frage waere. Es "
               "gibt drei belegte Unterschiede: Stop (Hebel ja, Spot "
               "nein), Zielgroesse (`barriere` binaer gegen "
               "`bewegung_r`), Dauer (2,0 Tage Median gegen H20) und "
               "taegliche Finanzierung. Entschieden wurde so, weil "
               "(1) eine eigene Hebelbewertung heute NICHT MESSBAR ist "
               "(A1), (2) das Aufteilen der Evidenz beide schwaecht - "
               "zwei Beitraege auf 1,5 %% der Anker - und (3) `r(q)` nur "
               "EINE Quote braucht", "gilt",
               "Fachliche Bewertung 10.09.2026 / Befund 2.173-hebel"),
    Befundlage("2.291-ausloeser", "✔ UND DER AUSLOESER FUER DIE ECHTE "
               "TRENNUNG IST BENANNT UND PRUEFBAR: sobald A1 behoben und "
               "`barriere` messbar ist, wird gemessen, ob ein Beitrag auf "
               "`barriere` ANDERS wirkt als auf `bewegung_r`. Traegt er "
               "dort anders, bekommt der Hebel seine eigene Bewertung - "
               "sonst nicht. ⚠️ Das ist eine Messfrage mit einem Datum, "
               "kein offener Vorbehalt", "gilt",
               "Fachliche Bewertung 10.09.2026"),
    Befundlage("2.292", "⚠️⚠️⚠️ DER VIERFACHTEST IST IN SEINER FASSUNG "
               "VOM 05.09. VON NIEMANDEM ZU BESTEHEN. Kriterium 4 (Regel "
               "3 laengs) liefert bei ALLEN fuenf gemessenen Kandidaten "
               "UNTERMACHT - einschliesslich der Kontrolle. Das ist der "
               "vorab benannte Ausgang: ein Befund ueber die ANLAGE, "
               "nicht ueber die Kandidaten. A9 (2.283) ist damit an "
               "echten Daten bestaetigt: die Laengs-Achse loest bei "
               "0,02 bis 0,05 R nicht auf, und genau dort liegen alle "
               "Kandidaten", "gilt", "n102_vierfachtest.py",
               basis="H20 · alle zulaessigen Mengen je Kandidat · "
                     "Messmenge V1 · 20 Nullziehungen"),
    Befundlage("2.292-fehlkonstruktion", "⚠️⚠️⚠️ UND KRITERIUM 4 IST "
               "FALSCH KONSTRUIERT - es muss nicht ausgesetzt, sondern "
               "mit dem RICHTIGEN Werkzeug gemessen werden. Es prueft "
               "heute mit einem SIGNIFIKANZTEST auf der Laengs-Achse, ob "
               "eine Groesse eine verkleidete Asset-Eigenschaft ist. Das "
               "richtige Mass steht seit dem 02.09. in Methodik 2.101: "
               "die STREUUNGSZERLEGUNG (Asset-Anteil = zwischen / "
               "(zwischen + innerhalb)), mit geeichter Skala - fester "
               "Wert je Symbol 95,9 %%, Zufall 0,1 %%, turnover 52 %%, "
               "volumenanteil roh 73 %% gegen relativ 1 %%. ⚠️⚠️ Das ist "
               "BESCHREIBEND, kein Signifikanztest - und deshalb von A9 "
               "GAR NICHT betroffen", "gilt",
               "Methodik 2.101 / Fachliche Bewertung 10.09.2026"),
    Befundlage("2.292-regel3", "⚠️ Dazu kommt: CLAUDE.md haelt "
               "ausdruecklich fest, dass Regel 3 den QUERSCHNITTSVERGLEICH "
               "NICHT VERBIETET. Ein Signifikanztest auf der Laengs-Achse "
               "verlangt damit MEHR, als die Regel fordert - Regel 3 "
               "verbietet das dauerhafte Asset-Urteil und den Asset-Rang "
               "beim Hebel, nicht die Querschnittsmessung", "gilt",
               "CLAUDE.md Regel 3 / F-227"),
    Befundlage("2.293", "✔✔ `schnitt` IST DER EINZIGE ROBUSTE KANDIDAT - "
               "und N-73 ist damit das ANTI-HIN-UND-HER-WERKZEUG. Ueber "
               "alle zulaessigen Beitragsmengen gemessen: `schnitt` "
               "traegt auf 3 von 3 (+0,1830 / +0,1858 / +0,0434), "
               "`schnitt50` auf 2 von 3, `vola` auf 1 von 3, `amihud` "
               "und `zufall` auf 0 von 3. ⚠️⚠️ DAS PROFIL ,traegt auf "
               "einer Menge, auf zweien nicht' IST das Hin und Her - je "
               "nach gewaehlter Menge lautet das Urteil anders. `schnitt` "
               "hat es nicht. Alle vier Kandidaten haben 100 %% "
               "Abdeckung und bestehen Kriterium 2", "gilt",
               "n102_vierfachtest.py"),
    Befundlage("2.293-abgrenzung", "⚠️ ABGRENZUNG, damit daraus kein "
               "voreiliger Schluss wird: das hier gemessene Kriterium 2 "
               "fragt ,erste gegen zweite Haelfte' (N-68). S-7 hat am "
               "07.09. eine ANDERE Frage gestellt - ,traegt er in den "
               "Fenstern ab 2022?'. Mein ,stabil' hebt S-7 NICHT auf",
               "gilt", "n102_vierfachtest.py / S-7"),
    Befundlage("2.294", "⚠️⚠️ DIE LUECKE, DIE VOR JEDER REGISTRIERUNG ZU "
               "SCHLIESSEN IST: `funding` und `turnover` sind VOR N-73 "
               "registriert worden, auf `frei`. Sie sind NIE ueber alle "
               "zulaessigen Mengen geprueft worden. Einen neuen "
               "Kandidaten daran zu messen und die Bestandsbeitraege "
               "nicht, waere zweierlei Mass - genau der Fehler, der am "
               "07.09. schon einmal gefangen wurde (N-2: ,einen "
               "Kandidaten an einer Huerde scheitern zu lassen, die die "
               "laufenden Beitraege nie nehmen mussten')", "gilt",
               "n102_vierfachtest.py / N-73 / N-2"),
    Befundlage("2.295", "⚠️ `amihud` LAEUFT LAENGS RUECKWAERTS: -0,0445 "
               "[-0,0994 .. -0,0005], das Band schliesst die Null "
               "negativ aus. Mein ,untermaechtig'-Etikett verschluckt "
               "das - dieselbe Grobheit wie bei A2 am selben Tag, nur "
               "umgekehrt. ⚠️ Es passt zu 2.166: er misst "
               "Ausfuehrbarkeit, nicht Potential", "gilt",
               "n102_vierfachtest.py"),
    Befundlage("2.296", "✔ DIE KONTROLLE ARBEITET, und das ist der "
               "Nachweis, dass der Messstandard tut, wofuer er gesetzt "
               "wurde: `zufall` hat bei 20 %% ein Band OHNE Null "
               "(+0,0026 .. +0,0321) - und die Norm ueberstimmt es "
               "korrekt mit ,traegt nicht bis 0,0346'. Ohne den "
               "Nullpunkt waere daraus ein Scheinbefund geworden",
               "gilt", "n102_vierfachtest.py / Messstandard 08.09."),
    Befundlage("2.297", "✔✔✔ V1: KRITERIUM 4 IST ERFUELLBAR - der "
               "Deadlock ist aufgeloest. Mit der STREUUNGSZERLEGUNG "
               "(Methodik 2.101) statt eines Signifikanztests bestehen "
               "die meisten Kandidaten es in der ROHEN Form: "
               "`oi_aenderung` 0,4 %% · `schnitt50` 6,9 %% · `funding` "
               "15,7 %% · `vola` 16,5 %% · `schnitt` 25,4 %% - alle "
               "ueberwiegend ZEITPUNKT-Aussagen. Die Skala ist geeicht "
               "(FEST 99,9 %%, ZUFALL 0,1 %%), beide Arme auf der Menge "
               "des Kandidaten", "gilt", "n103_v1_asset_anteil.py",
               basis="H20 · Messmenge V1 · Rang je Kalendertag · "
                     "Kontrollen auf derselben Symbolmenge"),
    Befundlage("2.297-rr11", "✔ R-R11 ERFUELLT VOR DER ERSTEN NEUEN "
               "AUSSAGE: `turnover` roh 51,2 %% gegen die registrierten "
               "52 %% aus F-170. Die Messung reproduziert, also gilt der "
               "Lauf", "gilt", "n103_v1_asset_anteil.py / F-170"),
    Befundlage("2.298", "⚠️⚠️⚠️ UND DER BEFUND TRIFFT DEN BESTAND, NICHT "
               "DIE KANDIDATEN: `turnover` laeuft LIVE und ist zu 51,2 %% "
               "eine ASSET-Eigenschaft - er sagt zur Haelfte, WELCHES "
               "Asset, nicht WANN. `amihud` liegt mit 70,7 %% noch "
               "hoeher, ist aber nicht registriert. ⚠️ Haette ich nur die "
               "Kandidaten gemessen, waere `turnover` mit 51 %% "
               "durchgelaufen, waehrend ein neuer Kandidat mit demselben "
               "Wert gefallen waere - zweierlei Mass, der Fehler von N-2",
               "gilt", "n103_v1_asset_anteil.py / F-170 / 2.294"),
    Befundlage("2.299", "⚠️⚠️⚠️ MEINE EIGENE LOESUNG IST WIDERLEGT - von "
               "der eigenen Gegenpruefung. Ich hatte die RELATIVE Form "
               "(Standardisierung gegen den eigenen 20-Tage-Schnitt) als "
               "Behandlungsvorschlag gefuehrt, weil sie alle Kandidaten "
               "unter 1,5 %% bringt. Auf Kunstdaten mit EINGESTELLTEM "
               "Asset-Anteil: gebaut 10 %% -> relativ 0,0 %% · gebaut "
               "50 %% -> 0,0 %% · gebaut 90 %% -> 0,0 %%. ⚠️⚠️ Die "
               "Standardisierung entfernt das Symbolmittel PER "
               "KONSTRUKTION - sie senkt JEDE Groesse auf null und "
               "beweist NICHTS", "gilt",
               "n103_v1_asset_anteil.py / Selbstbefund 10.09.2026"),
    Befundlage("2.299-folge", "⚠️ WAS DARAUS FOLGT, und es ist kein "
               "Nullbefund: die relative Form bleibt ein moeglicher "
               "UMBAU - aber der Nachweis muss dann ueber die WIRKUNG der "
               "umgeformten Groesse laufen, nicht ueber ihren "
               "Asset-Anteil. Genau so war es beim Volumenanteil: "
               "relative Form 1,4 %% Asset-Anteil UND +0,0231 R Wirkung. "
               "BEIDES, nicht eines", "gilt",
               "n103_v1_asset_anteil.py / F-170"),
    Befundlage("2.300", "✔✔ `schnitt` BESTEHT KRITERIUM 4 IN DER ROHEN "
               "FORM (25,4 %% Asset-Anteil, ueberwiegend Zeitpunkt) - "
               "und er ist zugleich der EINZIGE robuste Kandidat aus dem "
               "Vierfachtest (3 von 3 Mengen, 2.293) und der erste "
               "gemessene Beitrag der Akkumulationslage (2.286-schnitt). "
               "⚠️ Damit besteht er drei der vier Kriterien; Kriterium 3 "
               "(unabhaengig von `funding`) steht noch aus", "gilt",
               "n103_v1_asset_anteil.py / 2.293 / 2.286-schnitt"),
    Befundlage("2.301", "⚠️ NEU AUS V1: `turnover`s Asset-Anteil von "
               "51,2 %% ist ein offener Punkt AM BESTAND, kein Grund zum "
               "Abschalten. Regel 3 verbietet das dauerhafte "
               "Asset-Urteil; 51 %% heisst, dass die HAELFTE der Streuung "
               "aus dem Symbol kommt - nicht, dass der Beitrag falsch "
               "ist. ⚠️ Er bleibt registriert; zu klaeren ist, ob eine "
               "andere FORM (wie beim Volumenanteil) denselben Beitrag "
               "mit weniger Asset-Anteil UND erhaltener Wirkung liefert",
               "gilt", "n103_v1_asset_anteil.py"),
    Befundlage("2.302", "✔✔ V7/KRITERIUM 3: `turnover` IST UNABHAENGIG "
               "VON `funding` - und das ist das EINZIGE gedeckte Urteil "
               "des Laufs. In Funding-Fuenftel geschichtet traegt er in "
               "2 von 5 echten Faechern und in 0 von 5 GEMISCHTEN. Zwei "
               "Faecher Unterschied, ueber der Aufloesung. ⚠️ Damit ist "
               "die Registrierungsaussage ,zu 92 %% additiv zu Funding' "
               "erstmals UNTER DER NORM bestaetigt", "gilt",
               "n104_v7_kriterium3.py",
               basis="H20 · frei (Registrierungsbasis) · 5 "
                     "Funding-Fuenftel je Tag · 30 Symbole je Fach"),
    Befundlage("2.302-gegenkontrolle", "✔ UND DIE GEGENKONTROLLE IST DER "
               "GRUND, WARUM DAS URTEIL TRAEGT. Dieselbe Schichtung mit "
               "GEMISCHTEM Funding - gleiche Fachgroesse, keine "
               "Information. Ohne diesen Arm waere jedes ,traegt nicht "
               "mehr' wertlos, weil es allein daher kommen koennte, dass "
               "ein Fuenftel ein Fuenftel der Anker hat. Die Konstruktion "
               "stammt aus `pruefe_n1_schichtung_gegen_partner`",
               "gilt", "n104_v7_kriterium3.py"),
    Befundlage("2.303", "⚠️⚠️ FUER DIE KANDIDATEN IST KRITERIUM 3 MIT "
               "DIESEM AUFBAU NICHT ENTSCHEIDBAR - aus DREI verschiedenen "
               "Gruenden, und sie sind zu trennen: `vola` traegt ohne "
               "Schichtung, aber in 0 von 5 Faechern - echt WIE gemischt, "
               "also kostet die SCHICHTUNG (kein Redundanzbefund). "
               "`schnitt` und `schnitt50` tragen auf `frei` ohnehin nicht "
               "- das ist die MARKT-Frage, nicht ihre Beitragsmenge. "
               "`oi_aenderung` liegt mit 2 gegen 3 Faechern auf der "
               "Aufloesungsgrenze", "gilt", "n104_v7_kriterium3.py"),
    Befundlage("2.303-struktur", "⚠️ DIESELBE STRUKTUR WIE BEI KRITERIUM "
               "4 VOR V1 - aber NICHT dieselbe Ursache. Bei Kriterium 4 "
               "war das WERKZEUG falsch (Signifikanztest statt "
               "Streuungszerlegung). Hier ist das Werkzeug richtig, es "
               "fehlt die MACHT: Schichtung mal schmale Menge laesst zu "
               "wenige Anker. Das ist ein Dimensionierungsproblem, kein "
               "Konstruktionsfehler", "gilt", "n104_v7_kriterium3.py"),
    Befundlage("2.304", "⚠️⚠️ EIGENE UEBERDEUTUNG, VOM ERGEBNIS GEFANGEN: "
               "der erste Lauf las `oi_aenderung`s ,2 gegen 3 Fuenftel' "
               "als ,`funding` erklaert einen Teil mit'. Bei fuenf "
               "Faechern ist EIN Fach die feinste unterscheidbare "
               "Einheit - ein Unterschied von einem Fuenftel ist die "
               "GRENZE, keine Aussage. ⚠️ Dieselbe Ueberdeutung wie beim "
               "Gleichstand in N-46b; dort hat der Vorabtest sie "
               "gefangen, hier erst das Ergebnis. Die Aufloesungsgrenze "
               "steht jetzt im Werkzeug", "gilt",
               "n104_v7_kriterium3.py / Selbstbefund 10.09.2026"),
    Befundlage("2.305", "⚠️⚠️ UND EINE STILLE VERENGUNG, VOM NUTZER "
               "GEFANGEN: ich hatte `schnitt50` aus dem Lauf genommen - "
               "aus LAUFZEITgruenden (9 Minuten je Kandidat), nicht aus "
               "Sachgruenden. Er steht sachlich gut da: 100 %% "
               "Abdeckung, 6,9 %% Asset-Anteil (der zweitbeste Wert nach "
               "`oi_aenderung`), stabil, und laut 2.222 die EINZIGE "
               "monotone Form - genau das zaehlt beim Schritt FORM. "
               "⚠️ Nachgemessen: dasselbe Bild wie `schnitt` (2 gegen 1 "
               "Fach, auf `frei`). Die Kuerzung war trotzdem falsch - "
               "sie im Skriptkopf zu vermerken ist nicht dasselbe wie sie "
               "zu begruenden", "gilt",
               "Nutzereinwand 10.09. / n104_v7_kriterium3.py"),
    Befundlage("2.306", "⚠️ DER MENGENVORBEHALT, jetzt benannt statt "
               "stillschweigend: fuer die REGISTRIERTEN Beitraege "
               "(`turnover`, `oi_aenderung`) ist `frei` die "
               "Registrierungsbasis - dort richtig. Fuer KANDIDATEN ohne "
               "Basis (`schnitt`, `schnitt50`, `vola`) ist `frei` die "
               "MARKT-Frage (P6). Behoben werden kann es hier nicht: "
               "eine Momentum-Menge UND ein Funding-Fuenftel zugleich "
               "liessen rund SECHS Anker je Tag uebrig", "gilt",
               "n104_v7_kriterium3.py / P6"),
    Befundlage("2.307", "➔ DER LOESUNGSWEG FUER KRITERIUM 3 (Nutzervorgabe "
               ",kein Beitrag faellt ohne Loesung'): ZWEI Schichten statt "
               "fuenf. Bei fuenf Faechern bleiben 30 Symbole je Tag; bei "
               "zwei waeren es 75, und auf der 20-%%-Beitragsmenge immer "
               "noch rund 25 - ueber dem Mindestquerschnitt von 12. "
               "⚠️ Das halbiert den Machtverlust UND erlaubt, die "
               "Kandidaten auf ihrer BEITRAGSmenge zu messen statt auf "
               "`frei`. Damit waeren beide Gruende aus 2.303 zugleich "
               "adressiert", "offen", "V8, aus 2.303 und 2.306"),
    Befundlage("2.308", "⚠️⚠️⚠️ V8 WIDERLEGT MEINEN EIGENEN LOESUNGSWEG "
               "AUS 2.307. Mit ZWEI Faechern statt fuenf ist KEIN Urteil "
               "mehr gedeckt - mit fuenf war es eines. `turnover` hatte "
               "bei fuenf Faechern 2 gegen 0; dieselben Daten liefern bei "
               "zwei Faechern 2 gegen 1, und das ist nur EIN Fach "
               "Unterschied. ⚠️⚠️ NICHT DIE MACHT WAR DER ENGPASS, "
               "SONDERN DIE ZAEHLMETRIK: weniger Faecher geben mehr Anker "
               "je Fach, aber die Zaehlung hat dann nur noch drei "
               "moegliche Werte (0, 1, 2)", "gilt",
               "n105_v8_kriterium3_zwei_faecher.py",
               basis="H20 · 2 Funding-Faecher · Kandidaten auf 20 %, "
                     "Bestand auf frei · 74 Symbole je Fach"),
    Befundlage("2.308-vorfrage", "✔ WAS V8 TROTZDEM GELOEST HAT: die "
               "VORFRAGE. Auf der 20-%%-Menge tragen `schnitt` "
               "(+0,1858), `schnitt50` (+0,0698) und `vola` (+0,1332) "
               "ohne Schichtung - auf `frei` taten sie das nicht. Der "
               "Mengenvorbehalt aus 2.306 ist damit ausgeraeumt, und die "
               "Messung ist ueberhaupt erst aussagekraeftig geworden",
               "gilt", "n105_v8_kriterium3_zwei_faecher.py"),
    Befundlage("2.309", "⚠️⚠️⚠️ UND DAS RICHTIGE WERKZEUG LAG DIE GANZE "
               "ZEIT VOR - ich habe es wegen eines AUFRUFPARAMETERS "
               "verworfen. `messnorm_rand.pruefe_geschichtet` misst die "
               "Schichtung als EINEN Befund mit EINEM Band - Nullpunkt, "
               "Trennschaerfe und eine eingebaute Positivkontrolle "
               "(`pflanze`), die dem Original fehlt. Und `marke=None` "
               "gibt die Median-Differenz, also den STANDARDmassstab. "
               "⚠️ Ich habe es abgelehnt, weil der eine Aufrufer, den ich "
               "ansah (`pruefe_n1_schichtung_gegen_partner`), "
               "`marke=2.0` uebergab - ich habe das Argument eines "
               "Aufrufers fuer die Natur des Werkzeugs gehalten",
               "gilt", "messnorm_rand.py:290 / Selbstbefund 10.09.2026"),
    Befundlage("2.310", "➔ V9 IST DER RICHTIGE WEG FUER KRITERIUM 3: "
               "`pruefe_geschichtet(..., marke=None)` statt einer Zaehlung "
               "ueber Faecher. Eine STETIGE Kennzahl mit einem Band "
               "schlaegt eine Zaehlung mit drei bis sechs moeglichen "
               "Werten - genau der Unterschied, an dem V7 und V8 "
               "gescheitert sind. Die Gegenkontrolle (GEMISCHTES Funding) "
               "bleibt, sie ist von der Kennzahl unabhaengig",
               "offen", "V9, aus 2.308 und 2.309"),
    Befundlage("2.311", "✔ KANARIENVOGEL IN V8: `traegt_wirklich()` liest "
               "das URTEIL statt der Eigenschaft `traegt`. Bei zwei "
               "Faechern auf einer 20-%%-Menge ist die Blockzahl knapp, "
               "und `Befund.traegt` weiss nichts davon - genau der Fehler "
               "4 vom 08.09., an dem `k1c_lagen_eigene_zielgroesse` "
               "einmal gescheitert ist (drei gemeldete Traeger, waehrend "
               "alle fuenf KEIN BEFUND lauteten). Auf Kunstdaten "
               "geprueft", "gilt",
               "n105_v8_kriterium3_zwei_faecher.py"),
    Befundlage("2.312", "⚠️⚠️⚠️ V2: `funding` BESTEHT N-73 NICHT - ein "
               "LIVE laufender, registrierter Beitrag traegt auf 2 von 3 "
               "zulaessigen Beitragsmengen (10 %% +0,0688 TRAEGT · 20 %% "
               "+0,0582 NICHT TRENNBAR · 50 %% +0,0313 TRAEGT). Das ist "
               "dasselbe Profil wie `schnitt50` - und schwaecher als der "
               "Kandidat `schnitt` mit 3 von 3", "gilt",
               "n106_v2_n73_auf_dem_bestand.py",
               basis="H20 · alle zulaessigen Mengen je Beitrag · "
                     "Messmenge V1"),
    Befundlage("2.312-antwort", "✔✔✔ DAMIT IST DIE ZWEIERLEI-MASS-SORGE "
               "AUS 2.294 BEANTWORTET - und zwar UMGEKEHRT zur "
               "Erwartung: `schnitt` besteht N-73 BESSER als jeder "
               "registrierte Beitrag. Ihn an dieser Huerde zu messen ist "
               "nicht unfair - er nimmt sie sauberer als der Bestand. "
               "⚠️ Die Huerde bleibt damit gueltig; sie ist fuer den "
               "BESTAND neu zu begruenden, nicht fuer den Kandidaten zu "
               "senken", "gilt", "n106_v2_n73_auf_dem_bestand.py / 2.294"),
    Befundlage("2.313", "⚠️⚠️ UND EINE LESART, DIE DER BRUCH VERSTECKT: "
               "`turnover` besteht mit ,1 von 1' - aber nur, weil bei "
               "seiner Abdeckung (66 von 536) UEBERHAUPT NUR EINE "
               "Beitragsmenge zulaessig ist (50 %%). ,1 von 1' ist eine "
               "SCHWAECHERE Aussage als ,3 von 3'. Der N-73-Bruch haengt "
               "daran, wie viele Mengen die Datenlage traegt - wer nur "
               "den Bruch liest, haelt einen duennen Beitrag fuer so "
               "robust wie einen breiten", "gilt",
               "n106_v2_n73_auf_dem_bestand.py"),
    Befundlage("2.314", "✔ `oi_aenderung` BESTEHT N-73 SAUBER: 2 von 2 "
               "(20 %% +0,0464 · 50 %% +0,0211), dazu `frei` +0,0126. "
               "⚠️ Er ist damit der einzige LIVE laufende Beitrag, der "
               "die Huerde ohne Einschraenkung nimmt - und er laeuft als "
               "SPERRE, nicht als Regler", "gilt",
               "n106_v2_n73_auf_dem_bestand.py"),
    Befundlage("2.315", "➔ WAS AUS 2.312 FOLGT - und es ist KEIN "
               "Abschalten: `funding` traegt auf 10 %% und 50 %%, nur "
               "bei 20 %% nicht. Nach der Nutzervorgabe faellt kein "
               "Beitrag ohne Grund, und ein Nichttragen auf EINER von "
               "drei Mengen ist ein Grund zum Nachsehen, keiner zum "
               "Entfernen. ⚠️ Zu klaeren: ob die 20-%%-Menge bei "
               "`funding` eine Besonderheit hat (Abdeckung 300 von 536 - "
               "die Momentum-Auswahl und die Funding-Verfuegbarkeit "
               "koennten sich ueberschneiden) oder ob es Rauschen ist",
               "offen", "V10, aus 2.312"),
    Befundlage("2.325-auswahl", "⚠️⚠️ 2.325 IST ZU BERICHTIGEN, NICHT "
               "ZU WIDERRUFEN - und die beiden Teile sind zu trennen: "
               "(a) die MESSUNG steht - auf der Momentum-20-%%-Menge ist "
               "der Haelftenunterschied +0,1973 [+0,0717 .. +0,3892] "
               "nachgewiesen und dreifach reproduziert. (b) die "
               "ZUSCHREIBUNG faellt - es ist nicht `schnitt`s Eigenschaft, "
               "sondern die der KOLLINEARITAET mit der Auswahl (2.333). "
               "⚠️ FUER DEN VIERFACHTEST AENDERT SICH NICHTS: er ist auf "
               "der SELEKTIERTEN Menge definiert (F-212), und dort faellt "
               "`schnitt` an Kriterium 2. **2.319 bleibt abgeloest**",
               "gilt", "n112_v11_gegenpruefung.py / F-212"),
    Befundlage("2.325-warum-egal", "✔ UND DIE PRAKTISCHE FOLGE DREHT SICH "
               "DADURCH NICHT UM: der Grund gegen `schnitt` als dritten "
               "Beitrag ist jetzt 2.335 (er bildet zu vier Fuenfteln die "
               "AUSWAHL nach) - ein Grund, der von Kriterium 2 voellig "
               "unabhaengig ist und schon seit dem 09.09. im Bestand "
               "steht. ⚠️ Wer nur 2.333 liest, koennte meinen, `schnitt` "
               "sei rehabilitiert. Ist er nicht - der Einwand ist nur ein "
               "anderer geworden, und ein staerkerer", "gilt",
               "2.335 / 2.222 / 2.158-redundanz"),
    Befundlage("2.392", "⚠️⚠️⚠️ DIE VERKAUFSSEITE LAEUFT AN DER GANZEN "
               "BEWERTUNG VORBEI - und sie ist die groessere Haelfte des "
               "Betriebs. GEMESSEN an der NB-Sicherung 12.09.: 517 "
               "Ausstiegsempfehlungen seit 14.08. (405 REDUZIEREN, 112 "
               "VERKAUFEN), zuletzt 15 bis 20 JEDEN TAG - dem stehen 202 "
               "Signale gegenueber, die der Einstiegstrichter in 7 Tagen "
               "ganz durchlaufen hat. ⚠️ DER WEG IST KUERZER: In "
               "`rollen_lauf` verzweigt die Ausstiegsaktion an Stufe 9 "
               "(`aktion`) direkt nach `_sende_ausstieg` und kehrt zurueck - "
               "die Stufen 10 (`geometrie`), 11 (`risikoschicht`) und 12 "
               "(`entscheider`) werden NIE erreicht. Damit gilt fuer den "
               "Ausstieg NICHTS von dem, was die Einstiegsseite traegt: kein "
               "gemessenes Potential (`agent/potential.py` verwirft dort 92 "
               "%%), keine Schwelle je Datenlage, kein Aggregat-Deckel, keine "
               "Trefferquote. Was verkauft wird, entscheidet allein LLM-1 "
               "Rolle BC; `agent/verkaufsrechnung.py` rechnet nur noch Stueck "
               "und Euro aus - das sagt sein eigener Kopf: *,es entscheidet "
               "nicht, OB verkauft wird'*. ⚠️⚠️ UND DIE GUETE IST NICHT "
               "MESSBAR: von 517 Ausstiegen stehen 409 auf "
               "`outcome_status='nicht_anwendbar'` (79 %%), 59 auf "
               "`stop_loss_erreicht`, 46 auf `einstieg_nie_erreicht`. Die "
               "beiden letzten sind EINSTIEGS-Kategorien, auf einen Ausstieg "
               "angewandt - ,der Einstieg wurde nie erreicht' ist ueber einen "
               "Verkauf keine Aussage. Es gibt keine einzige Zahl darueber, "
               "ob ein Verkauf richtig war. ⚠️ DAZU WIEDERHOLUNG: SUPRA 12x "
               "VERKAUFEN, MON 10x REDUZIEREN in sieben Tagen", "gilt",
               "NB-Sicherung 12.09. · agent/rollen_lauf.py · "
               "agent/verkaufsrechnung.py"),
    Befundlage("2.392-stumm", "⚠️⚠️ 105 AUSSTIEGE WURDEN ALS ,REINES "
               "LLM-HALTEN' GEBUCHT - also OHNE MAIL. Gezaehlt in der "
               "NB-Sicherung 12.09.: 100 REDUZIEREN und 5 VERKAUFEN tragen "
               "`ist_reines_llm_halten=1`, verteilt vom 14.08. bis zum "
               "11.09. - das ist KEIN abgeschlossener Altbestand, sondern "
               "laeuft bis gestern. ⚠️ Genau dieser Fehler ist am 14.08. "
               "schon einmal gefunden worden und steht im Kopf von "
               "`agent/verkaufsrechnung.py`: *,Verkaufen wurde mit Nichtstun "
               "in einen Topf geworfen'*. Er ist damals fuer den HAUPTWEG "
               "behoben worden (305 REDUZIEREN und 107 VERKAUFEN gingen "
               "seither regulaer heraus), aber offenbar nicht auf ALLEN "
               "Wegen. ⚠️ ZU KLAEREN, nicht angenommen: welcher Zweig "
               "`_schreibe_nein` mit einer Ausstiegsaktion erreicht - der "
               "Verdacht faellt auf ,ohne Bestand / vollstaendig gestakt' "
               "(Stufe 9, 25 Faelle in 7 Tagen) und auf ,Ausstieg steht auf "
               "SCHLIESSEN' (166). Beide buchen ein Nein und schicken keine "
               "Mail - bei einem Einstieg ist das richtig, bei einem "
               "Ausstieg ist es die Frage. ✔ AUFGEKLAERT UND BEHOBEN AM "
               "SELBEN TAG (48a, Befunde 2.401-gestakt und 2.402): an den "
               "echten Trichtergruenden nachgesehen lauteten ALLE 25 "
               "Faelle *,vollstaendig gestakt, nicht frei verkaeuflich'* "
               "- KEIN einziger ,ohne Bestand'. Und die 166 "
               "SCHLIESSEN-Faelle sind EINSTIEGE (NACHKAUFEN), gehoeren "
               "also gar nicht dazu. Der gestakte Fall bekommt seit 48a "
               "einen eigenen Mailabschnitt statt Schweigen. ⚠️ DIESER "
               "NACHTRAG KAM ERST ABENDS, und das ist selbst ein Befund: "
               "der Fall war seit Stunden geloest und stand hier weiter "
               "auf offen - genau das, was die Vorgabe SOFORT-EINTRAGEN "
               "verhindern soll "
               "✔✔✔ VOLLSTAENDIG DURCHGEZAEHLT AM 13.09. (2.428) - der "
               "Nachtrag oben belegte 25 der 105 Faelle und hielt den Rest "
               "fuer denselben Fall. Nachgezaehlt sind es 95 vollstaendig "
               "GESTAKTE (die 48a loest) und 10 vom 14.08. zwischen 07:14 "
               "und 07:16 - vier Stunden vor dem Fix von damals (Commit "
               "153b2bd, 11:39). Dazwischen: nichts. ⚠️ Eine plausible "
               "Annahme ueber 80 Faelle ist keine Zaehlung, auch wenn sie "
               "am Ende stimmt",
               "gilt",
               "NB-Sicherung 12.09. · Schritt 43"),
    Befundlage('2.453-fredkey-gebaut', '✔✔ KEIN ZUGANGSSCHLUESSEL MEHR IN DATENBANK, LOG ODER EXPORT. Ursache: `requests` nennt bei HTTP-Fehlern die volle URL; FRED und EIA tragen `api_key`, Finnhub `token` als Parameter. 📏 Export 15.09.: 8 Treffer des FRED-Schluessels (Ampel 1, Log-Auszug 4, Job-Fehlschlaege 3), kein anderer Schluessel, kein Bearer-Token. ➤ GEBAUT: `geheimnisse.py` - eine Regel (Wert nach `?`/`&` bei Schluesselnamen -> ***; Anbieter und Parametername bleiben lesbar); maskiert in `track_api_health` VOR dem Kuerzen und in `db.record_api_health_error`; `main.py` setzt einen Formatter, der jede fertige Log-Zeile samt Traceback maskiert; `init_db` bereinigt Altbestand in `api_health_status` (idempotent); der Export maskiert Log-Auszug, Job-Fehlschlaege, Groq-Ereignisse, Ampel und Auffaelligkeiten - die alten Log-Dateien am Notebook tragen den Schluessel bis zur Rotation. 📏 Gegen den echten Export: 8 -> 0; Migration auf der Kopie: 1 Zeile bereinigt, zweiter Lauf 0. Paket Geheimnisse: Regel, Speichern, Migration, Logging mit Traceback, Verdrahtung; mit altem Code rot. ⚠️ NICHT BEHOBEN UND NUTZERSACHE: der Schluessel liegt noch in den bisherigen Exporten und DB-Sicherungen im Google-Drive-Austauschordner - Empfehlung: den kostenlosen FRED-Schluessel neu ausstellen', 'gilt',
               'geheimnisse.py; database/api_health.py; database/db.py; main.py; extract_notebook_diagnose.py; pruefe_pakete.py Geheimnisse', '', '', 'Export 15.09. 00:37 gescannt (8 Treffer maskiert ausgegeben); Maskierung gegen denselben Export und Migration gegen eine Kopie der Sicherung 12.09.; Suite-Paket Geheimnisse (9) mit Gegenprobe gegen den alten Code'),
    Befundlage('2.454-etfbestand-quelle', "⚠️⚠️⚠️ DIE ETF-BESTANDSREIHE WAR NIE EINE MESSGROESSE - nicht nur Silber und Erdgas stehen, auch Gold. yfinance `sharesOutstanding` ist ein RUHENDER Stammdatenwert: Gold 27 Tageswerte, ALLE 260.300.000; Silber und Erdgas je 9, alle gleich. Seit dem 25.08. liefert yfinance fuer SLV und UNG gar nichts mehr - `if stueck:` ueberging das STILL, ohne Log-Zeile. Die gemeinte Groesse ,Metall wird ein- oder ausgelagert' kam also nie an. Wirkung heute: keine - `positionierung._etf_bestand` verlangt 90 Punkte, es entstand nie ein Satz; Rolle G hat fuer Rohstoffe weiter nur COT (G1 unerfuellt). 📏 Live 15.09.: `fast_info.shares` None, `get_shares_full` leer, `totalAssets/navPrice` weicht um Faktor 1,5 bis 4,7 vom gespeicherten Wert ab (nicht verlaesslich). Echte Tageswerte gibt es nur bei den Emittenten, je in eigenem Format: iShares SLV (Ounces in Trust, in 1,5 MB HTML), USCF UNG (HTML-Tabelle), SPDR GLD (Archiv liefert inzwischen PDF). ➤ NUTZERENTSCHEIDUNG 15.09.: das ZIEL ist nicht ,Rolle G eine zweite Quelle geben', sondern die Frage, ob ETF-Zu- und Abfluesse den weiteren Kursverlauf der Rohstoff-ETCs vorhersagen - nur dann ist eine Emittentenquelle den Aufwand wert. Weg: Datenlage (Tages-Historie ueber Jahre), Messbarkeit vorab (4 Werte, kein Querschnitt, Blocker A9), Messung nach Messstandard, dann bauen oder stilllegen. Planschritt 57, Block SPAETER (Vorgaben KRYPTO-ZUERST und VERKAUF-VOR-MULTIASSET). Bis dahin bleibt der Abruf ohne Wirkung stehen", 'offen',
               'scheduler/background.py externe_reihen_job (ROHSTOFF_ZU_ETF); agent/positionierung.py _etf_bestand; agent/datenfrische.py (etf_bestand)', '', '', 'Sicherung 2026-09-12_0646 (externe_reihe etf_bestand), Export 15.09., yfinance live 15.09. (GLD/SLV/UNG/CPER: sharesOutstanding, fast_info, get_shares_full, totalAssets/navPrice), Emittentenseiten live abgerufen'),
    Befundlage('2.455-review', "✔ REVIEW DER AENDERUNGEN 13. BIS 15.09. (Nutzerauftrag 15.09.: ,ist alles dokumentiert, geplant, in den Regelwerken eingetragen, fehlen offene Punkte?'). GEPRUEFT: (1) jeder offene Befund seit 2.441 steht mit EXAKTER Kennung in einem offenen Planschritt - ja, alle 27; (2) abgeloeste Befunde haben einen bekannten Nachfolger - ja; (3) jede geaenderte Datei ist in einem Befund genannt - ja bis auf UI-Nachzuege, die unter 2.448 und Schritt 50 stehen; (4) neue Skripte im Werkzeugkasten der Methodik - zwei fehlten (`pruefstand_hebelmail.py`, `vergleiche_hebel_und_mailrechnung.py`), nachgetragen; (5) Befund 2.442 galt ohne Basis - nachgetragen; (6) die Rollout-Anleitung 14.09. kannte die Pulls vom 14. abends bis 15.09. nicht - Nachtrag geschrieben; (7) GEGENPROBE SCHLUESSEL: die Sicherung 14.09. 22:40 in ALLEN Textspalten durchsucht - einzig `api_health_status` traegt einen Schluessel, genau die Stelle, die die Migration bereinigt. ➤ GEFUNDEN UND EINGEORDNET: (a) VIER BEFUNDE MIT DEM VERMERK ,NACH DEM ROLLOUT' hingen an ERLEDIGTEN Schritten und waren damit nirgends offen: 2.387-job, 2.387-fortschreibung, 2.382-rundung (jetzt Schritt 56), 2.379-tage (Schritt 52); dazu D3 (Schritt 35). Die Planpruefung sah das nicht, weil sie nur die 20 hoechsten Nummern liest (2.453-plan). (b) 19 AELTERE offene Messfragen stehen in keinem offenen Schritt: 2.138-offen, 2.141-lage, 2.145-zeit, 2.147-weg, 2.152-kern, 2.307, 2.310, 2.315 und N2, N6, N7, N10, N11, N14 bis N18 - einzuordnen, wenn die Pruefung verschaerft wird (Schritt 55). (c) neu 2.455-refreshzeit, 2.455-regelwerk, 2.455-suite", 'gilt',
               'bestand.py; soll_ist.py; pruefe_pakete.py; Basisinfos/Rollout_Notebook_14_09.md; Basisinfos/Test_und_Verifikationsmethodik.md', '', '', 'git 2f0c73f..8bedff5 (6 Commits, 64 Dateien); bestand.BEFUNDE gegen soll_ist.REIHENFOLGE mit exakter Kennung; volle Suite 15.09. (2.574 Pruefungen); Sicherung 2026-09-14_2240 nur lesend (alle Textspalten nach Schluesseln durchsucht); Export 15.09. 00:41; Basisinfos-Dokumente'),
    Befundlage('2.455-refreshzeit',
               '○ DER TAGESJOB DER KURSREIHEN LAEUFT 24 STUNDEN NACH DEM APP-START, nicht zu einer festen Uhrzeit. Faellt der Lauf vor Mitternacht UTC, fehlt den Wertpapieren der gerade abgeschlossene Handelstag - bis zu 2 Handelstage Rueckstand, INNERHALB der Meldegrenze von 3 (2.453-kurs-gebaut). Wirkung heute: keine Meldung, aber Rolle A und die Rohstoffe sehen morgens den Vorvortag. Vorschlag vom 15.09., NICHT entschieden: ein fester Morgenlauf zusaetzlich',
               'abgeloest',
               'scheduler/background.py refresh_aktien_ohlc_job, _refresh_nicht_aktien_ohlc; staleness.reihe_ist_ueberholt',
               '2.455-kapitalkurse-gebaut',
               'der Kursreihen-Job laeuft taeglich 05:30 statt 24 h ab App-Start (15.09.)',
               'git 2f0c73f..8bedff5 (6 Commits, 64 Dateien); bestand.BEFUNDE gegen soll_ist.REIHENFOLGE mit exakter Kennung; volle Suite 15.09. (2.574 Pruefungen); Sicherung 2026-09-14_2240 nur lesend (alle Textspalten nach Schluesseln durchsucht); Export 15.09. 00:41; Basisinfos-Dokumente'),
    Befundlage('2.455-regelwerk', "⚠️⚠️ WAS GILT, STEHT SEIT DEM MESSSTANDARD NICHT MEHR IN DEN REGELWERKEN. `Regelwerksmanual.md` (IST-Zustand der Regeln) steht auf dem 06.09., `Regelwerk_Entscheidungslog.md` auf dem 03.09.; beide tragen einen Standkopf ,sah den Umbau nicht - was gilt, steht in REGISTER_Befunde'. Die Regeln seither stehen nur in Code, Befunden und den Vorgaben von `soll_ist`: Paket B (r-Klammer 0,50 bis 1,25, Hebel 2x bis 5x, Aggregat-Deckel 3), Stopweite und Deckel 25 (Schritt 47), Terminmarkt-Lesegrenze 2 h, Meldegrenze 6 h, Einzelwert 24 h (Schritt 54), Kursfrische 2 Tage Krypto und 3 Handelstage Wertpapiere, Ampel nur bei echtem Ausfall. REGISTER_Befunde beantwortet ,was wurde festgestellt', nicht ,welche Regel gilt heute mit welchem Wert' - die Frage, fuer die das Manual gebaut wurde (,fuer den Nutzer, in normaler Sprache'). Die Landkarte der Dokumente (Memory, Stand 16.08.) fuehrt beide weiter als ,laufend fortzuschreiben'. NUTZERENTSCHEIDUNG OFFEN: Manual neu fassen (aus dem Code erzeugt, wie die Register) oder beide formal stilllegen und die Rolle einem Register uebertragen. ➤ NUTZERENTSCHEIDUNG 15.09.: WEG A - ein aus dem Code erzeugtes Regelblatt; zentrale Dokumentation darf nicht auseinanderlaufen und muss fuer die Arbeit auffindbar und nachvollziehbar sein. Schritt 58", 'offen',
               'Basisinfos/Regelwerksmanual.md; Basisinfos/Regelwerk_Entscheidungslog.md; REGISTER_Befunde.md', '', '', 'git 2f0c73f..8bedff5 (6 Commits, 64 Dateien); bestand.BEFUNDE gegen soll_ist.REIHENFOLGE mit exakter Kennung; volle Suite 15.09. (2.574 Pruefungen); Sicherung 2026-09-14_2240 nur lesend (alle Textspalten nach Schluesseln durchsucht); Export 15.09. 00:41; Basisinfos-Dokumente'),
    Befundlage('2.455-suite', '⚠️ VOLLE SUITE 15.09.: 2.574 PRUEFUNGEN, 3 ROT - alle im Paket Neuaufnahme, alle DATENSTAND, keine Codefolge. (1) und (2) sind DAUERHAFT ROT mit bekanntem Enddatum (2.441-warten): ASTER, MON, CANTON zu kurze Reihe, CANTON Kernwert ohne Beitrag - rot bis 09.11.2026, 28.12.2026 und 15.08.2027. Eine Zeile, die monatelang erwartbar rot ist, verdeckt die naechste echte rote Zeile im selben Paket. (3) NEU DURCH ZEITABLAUF: die Nicht-Krypto-Messbasen am Desktop (aktien 470, rohstoffe 35, themen_etf 293) stehen auf dem 03.09., heute 8 Handelstage bei Grenze 7. Nach Vorgabe KRYPTO-ZUERST folgenlos, aber die Zeile bleibt rot, bis jemand `lade_messreihen` fuer diese Klassen laufen laesst. ZU ENTSCHEIDEN: erwartete Datenstaende als WARTEN statt FEHL fuehren (mit Enddatum), und ob die Nicht-Krypto-Basen jetzt aufgefrischt werden', 'offen',
               'pruefe_pakete.py paket_neuaufnahme; lade_messreihen.py; Befunde 2.441, 2.436', '', '', 'git 2f0c73f..8bedff5 (6 Commits, 64 Dateien); bestand.BEFUNDE gegen soll_ist.REIHENFOLGE mit exakter Kennung; volle Suite 15.09. (2.574 Pruefungen); Sicherung 2026-09-14_2240 nur lesend (alle Textspalten nach Schluesseln durchsucht); Export 15.09. 00:41; Basisinfos-Dokumente'),
    Befundlage('2.455-hebelabgleich-gebaut', "✔✔ HEBEL-ABGLEICH: EIN AUSFALL AB 1 STUNDE KOMMT PER MAIL (Nutzerentscheidungen 7d vom 14.09. und Grenze 1 Stunde vom 15.09.; Befund 2.453-hebelpos). GEBAUT: (1) `agent/hebel_abgleich.py` - Stempel `hebel_positions_synced_at` in `meta` (wann zuletzt ERFOLGREICH abgeglichen; der alte Transaktionsstempel steht ohne Handel still), `frische` mit Grenze 1 Stunde gezaehlt ab dem spaeteren von letztem Erfolg und App-Start, `meldung` einmal je Ausfall ohne Wiederholung und Entwarnung, Fehlertext maskiert, `positionsstand_zeile`. (2) `hebel_screening_job` setzt den Stempel NACH Abgleich und Liquidationspreisen im `try`, merkt den Fehlertext im `except` und ruft danach `_pruefe_hebel_abgleich` - vor dem Umlauf der Rollen-Kette, nur mit Bitpanda-Schluessel. (3) Die Hebelfuehrungs-Mail nennt ,POSITIONSSTAND VOM ...', wenn der Abgleich veraltet ist - ein Fakt, kein Ausloeser; ohne jeden erfolgreichen Abgleich keine Zeile. (4) Datenfrische: Quelle `hebel_abgleich` (Rolle H, totes Netz, findet auch einen stehenden Job; Uebergang ueber `bitpanda_holdings_synced_at` bis zum ersten Lauf). (5) Export: Abschnitt `hebel_abgleich` mit Alter in Stunden und Konsolenzeile. 📏 LIVE gegen die Kopie, BEIDE WEGE mit echtem Bitpanda-Abruf: ERFOLG mit dem Projekt-Schluessel - 1 Transaktion seit dem Watermark, 1,6 s, Stempel gesetzt, Datenfrische und Export frisch, keine Mailzeile; FEHLSCHLAG mit ungueltigem Schluessel - echter 401, Stempel unveraendert, der Waechter schickt bei 2 Stunden Alter EINE Mail mit dem echten Fehlertext, der zweite Lauf keine; vor dem ersten Abgleich steht die Datenfrische ueber den Uebergang auf ,frisch'. ⚠️ RICHTIGSTELLUNG: ein erster Lauf meldete ,Desktop-Schluessel abgelehnt' - FALSCH. `load_dotenv()` sucht die .env ab dem Ordner des SKRIPTS (Scratchpad), fand keine und schickte einen LEEREN Schluessel; der Nutzer hatte recht, die Schluessel sind auf beiden Geraeten gleich und gueltig. Lehre: Testskripte ausserhalb des Projektordners lesen die .env mit ausdruecklichem Pfad. ⚠️ GRENZE: laeuft die App nicht, kommt keine Mail", 'gilt',
               'agent/hebel_abgleich.py; scheduler/background.py hebel_screening_job, _pruefe_hebel_abgleich; database/db.py get/set_hebel_positions_synced_at; agent/hebelfuehrung.py sammel_mail; agent/rollen_lauf.py; agent/datenfrische.py _stand_hebel_abgleich; extract_notebook_diagnose.py _hebel_abgleich; pruefe_pakete.py HebelAbgleich', '', '', 'Code 15.09.; Suite-Paket HebelAbgleich (16 Pruefungen, Gegenprobe gegen den alten Code: Stempel, Fehlertext, Waechter, Mailzeile, Datenfrische und Export fehlen dort); volle Suite 2.588 Pruefungen, nur die 3 bekannten Datenstand-Zeilen rot; Live-Test gegen eine Kopie der Sicherung 2026-09-14_2240 mit echtem Bitpanda-Abruf (Erfolg und 401); Notebook-Log 12.09. bis 15.09.'),
    Befundlage('2.455-kapitalkurse',
               '⚠️ KAPITALKURSE: GEBAUT, ABER FUER VIER XETRA-TITEL NICHT AUSREICHEND (Nutzerentscheidung 15.09.: Paket aus 2.387-fortschreibung umsetzen). GEBAUT UND GEPRUEFT: (1) `refresh_aktien_ohlc` taeglich 05:30 mit Nachholen statt 24 h ab App-Start, eigener Lock; (2) `portfolio_historie.fehlende_handelstagskurse` und `_tageswert_mit_eingabepruefung` im Portfoliowert - fehlt einem Boersentitel an einem Werktag der Kurs des Tages, einmal nachladen und neu rechnen, sonst WARNING mit Namen. 📏 LIVE gegen die Kopie, Tageswert Montag 14.09.: OHNE Nachladen 10 Titel 3 T fortgeschrieben (genau die Vorhersage fuer die 06:30-Zeile am Notebook); MIT Nachladen bekommen ISOC, X136, OD7C/H/L/N den Montag - CEBS, DBPK, EXH3 und VVMX NICHT, die Pruefung meldet sie beim Namen. ⚠️⚠️ NEUE URSACHE: Yahoos TAGESHISTORIE dieser vier Xetra-Titel (.DE) enthaelt den Montag am Dienstag 05:45 UTC noch nicht - und das UNSTABIL: 2 von rund 15 Abfragen lieferten ihn (period 10d um 05:20, start 2026-08-01 um 05:37), die uebrigen nicht, auch mit gleichen Parametern. X136.MU, IS0C.SG, VST, SPY und ^GSPC liefern ihn stabil. `fast_info` kennt den Montag dagegen richtig: CEBS letzter Kurs 9,745, Vortagesschluss 10,14 - derselbe Wert, den `price_cache` um 22:32 UTC speicherte; VVMX 11,774, DBPK 0,1374, EXH3 63,52. WIRKUNG: der Tageswert Montag steigt mit dem Paket um nur 3,16 EUR, weil die vier fehlen - mit ihnen waeren es rund 30 EUR. Und ohne weitere Loesung kaeme die WARNING an jedem Werktag fuer dieselben vier (Rauschen, 2.454-rauschen). NUTZERENTSCHEIDUNG OFFEN: Rueckfall auf den Schlusskurs aus `fast_info`, wenn die Tageshistorie den letzten Handelstag nicht hat - oder erst messen, wann Yahoo liefert',
               'abgeloest',
               'scheduler/background.py refresh_aktien_ohlc_job, _lade_wertpapier_kursreihen, _tageswert_mit_eingabepruefung, build_scheduler; agent/portfolio_historie.py fehlende_handelstagskurse; pruefe_pakete.py Kapitalkurse; api/yfinance_history.py',
               '2.455-kapitalkurse-gebaut',
               'Schlusskurs-Rueckfall aus der Kursangabe gebaut (Nutzerentscheidung A, 15.09.)',
               'Code 15.09.; Suite-Paket Kapitalkurse (11 Pruefungen, Gegenprobe gegen den alten Code rot); volle Suite 2.599 Pruefungen, nur die 3 bekannten Datenstand-Zeilen rot; Live-Test gegen eine Kopie der Sicherung 2026-09-14_2240 mit echtem yfinance-Nachladen; yfinance 1.5.1 live 15.09. 05:20 bis 05:45 UTC (period 5d/10d/1mo/3mo/max, start, fast_info)'),
    Befundlage('2.455-kapitalkurse-gebaut', "✔✔ KAPITALKURSE: DER PORTFOLIOWERT RECHNET AN WERKTAGEN MIT DEM KURS DIESES TAGES - HANDELSPLATZGENAU (Nutzerentscheidungen 15.09.: Paket aus 2.387-fortschreibung, dann Weg A; Nutzerfrage ,Unterscheidung der Handelstage - Krypto hat keine, Aktien, ETF und Rohstoffe sind an Handelsplatz und Zeit gebunden'). DREI URSACHEN, drei Teile: (1) der Kursreihen-Job lief 24 h ab App-Start (am Notebook 22:32 UTC), als der Tag noch nicht als abgeschlossen galt -> jetzt Cron 05:30 mit Nachholen, vor Backward-Tracking 06:00, Portfoliowert 06:30, Lagebild 06:40; eigener Lock. Loest 2.455-refreshzeit mit. (2) Der Portfoliowert prueft seine Eingabe (`_tageswert_mit_eingabepruefung`): fehlt einem Nicht-Krypto-Titel an Mo bis Fr der Kurs des Tages, einmal nachladen und neu rechnen. (3) YAHOOS TAGESHISTORIE hinkte bei vier Xetra-Titeln (CEBS, VVMX, DBPK, EXH3 - Montag am Dienstag 05:45 UTC noch nicht, und unstabil), die Kursangabe nicht -> `agent/kursluecke.py` + `yfinance_history.letzter_handel`: fehlt nach dem Laden der letzte abgeschlossene Handelstag, wird der LETZTE HANDEL abgefragt (Tag in der Zeitzone des Platzes, Kurs, Hoch, Tief, Handelsperiode) und eine Kerze `quelle='schnappschuss'` geschrieben - nur wenn der Tag nach der letzten Kerze liegt, die Sitzung beendet ist und die Waehrung passt. Liefert Yahoo die echte Kerze spaeter, ersetzt sie den Rueckfall, und die Abweichung steht im Log (WARNING ab 0,5 Prozent) - der Rueckfall prueft sich selbst. Ausgenommen: Krypto und die rekonstruierten Reihen (Kursangabe veraltet, OD7C.SG: 2022). ⚠️ HANDELSPLATZGENAU OHNE FEIERTAGSKALENDER: liegt der letzte Handel eines Platzes VOR dem Bezugstag (Feiertag, oder kein Umsatz an einem duennen Platz), nennt die Eingabepruefung das als Grund (INFO), statt zu warnen; WARNING nur, wenn der Platz gehandelt hat und der Kurs trotzdem fehlt. Die Uhrzeit 05:30 passt fuer alle Plaetze: der Vortag ist ueberall geschlossen (spaetestens US 20:00 UTC), keiner ist offen (fruehestens Stuttgart/Muenchen 06:00 UTC). 📏 LIVE, Tageswert Montag 14.09. an der Kopie: ohne Paket 10 Titel mit Freitagskurs (genau die Vorhersage fuer die 06:30-Zeile am Notebook), 17.690,83 EUR; mit Paket KEIN fortgeschriebener Titel, 17.674,74 EUR (-16,09 EUR, -0,09 Prozent). Die vier Xetra-Titel bekamen ihren Schlusskurs aus dem letzten Handel 15:35 UTC (Schlussauktion): CEBS 9,745 (Hoch 9,971, Tief 9,626), VVMX 11,774, DBPK 0,1374, EXH3 63,52. ⚠️ GRENZEN: die Ersatzkerze hat keine Eroeffnung (Angabe fehlt, Eroeffnung = Schluss); ob der Rueckfall dem offiziellen Schluss entspricht, zeigt erst die Selbstpruefung am Notebook in den naechsten Tagen (Logzeile ,Schlusskurs-Rueckfall ... ersetzt')", 'gilt',
               'scheduler/background.py refresh_aktien_ohlc_job, _lade_wertpapier_kursreihen, _schliesse_kursluecken, _tageswert_mit_eingabepruefung, build_scheduler; agent/kursluecke.py; api/yfinance_history.py letzter_handel; agent/portfolio_historie.py fehlende_handelstagskurse; pruefe_pakete.py Kapitalkurse', '', '', 'Code 15.09.; Suite-Paket Kapitalkurse (21 Pruefungen; Gegenprobe gegen den Stand vor dem Paket und gegen den Stand vor dem Rueckfall jeweils rot); volle Suite 2.609 Pruefungen, nur die 3 bekannten Datenstand-Zeilen rot; Live-Test gegen eine Kopie der Sicherung 2026-09-14_2240 mit echtem yfinance (Tageshistorie, history_metadata); NB-Log 12. bis 15.09.'),
    Befundlage('2.455-rekonstruktion-heute', '○ BEOBACHTET IM LIVE-TEST 15.09., NICHT GEPRUEFT: die rekonstruierten Rohstoff-ETC-Reihen (OD7C/H/L/N) schreiben beim Laden eine Kerze mit dem HEUTIGEN Datum (15.09. um 05:40 UTC), gebildet aus der laufenden Futures-Kerze und dem aktuellen ETC-Ankerpreis. Fuer den Portfoliowert folgenlos (er liest den Bezugstag), aber jeder Leser, der die LETZTE Kerze nimmt (Rolle-Fakten, ATR), bekaeme eine unfertige Tageskerze - dieselbe Klasse wie 2.418-teilkerze bei Krypto. Zu pruefen: welche Leser die rekonstruierte Reihe ohne Datumsgrenze lesen', 'offen',
               'agent/rohstoff/pipeline.py _rekonstruiere_etc_reihe; agent/rekonstruktion.py', '', '', 'Live-Test gegen eine Kopie der Sicherung 2026-09-14_2240, 15.09. 05:40 UTC'),
    Befundlage('2.455-nb-15-09', "✔ NOTEBOOK NACH DEN PULLS 15.09. GEPRUEFT - KEIN NEUER FEHLER AUS DEM CODE. (1) FRED-Schluessel: 0 Treffer im Export, 10 Stellen maskiert (2.453-fredkey-gebaut wirkt). (2) Hebel-Abgleich: letzter Erfolg 06:32 UTC, vor 0,02 h, offen keine (2.455-hebelabgleich-gebaut wirkt). (3) Datenfrische 21 von 21 frisch - die neue Quelle `hebel_abgleich` zaehlt mit. (4) DIE VORHERSAGE TRAF: Tageswert 14.09. um 06:30 mit genau den 10 vorhergesagten Titeln fortgeschrieben (CEBS, DBPK, EXH3, ISOC, OD7C/H/L/N, VVMX, X136), 3QSS und VST nicht. ⚠️ Mein Wortlaut ,1 T' war falsch - die Zeile zaehlt Kalendertage, Freitag bis Montag sind 3 T. (5) DIE +3 JOBFEHLER (Preis-Refresh, yfinance 0 von 13, Fehlermail) sind EIN Netzausfall des Notebooks 07:48 bis 07:50: yfinance, CoinGecko, Bitpanda, Kraken und SMTP liefen gleichzeitig in den Timeout; der Hebel-Abgleich uebersprang einen Lauf, danach lief alles wieder. (6) Seit dem letzten Start 08:16:50 (Stand 9d5d82f) 34 Zeilen WARNING/ERROR, ausschliesslich bekanntes Rauschen (2.454-rauschen: BC3 je Nicht-Krypto-Wert, EURCV-Kerzen, marktrang ohne messdaten.db). (7) Der Kursreihen-Job lief nach dem Start 08:16 NICHT nach - richtig, er lief heute 07:33 noch nach altem Takt; der erste Lauf nach neuer Regel ist 16.09. 05:30 und dort zu bestaetigen (Rollout-Anleitung Nachtrag 15.09.)", 'gilt',
               'notebook_diagnose.json; data/tradinginfotool.log', '', '', 'Notebook T440: notebook_diagnose.json 15.09. 08:34 (Log 12.09. 08:46 bis 15.09. 08:34, 13.396 Zeilen), Sicherung 2026-09-15_0545 nur lesend, Screenshot der NB-Zusammenfassung'),
    Befundlage('2.455-exportveto', "○ FEHLALARM IN DER STANDARDPRUEFUNG: `extract_notebook_diagnose._auffaelligkeiten` meldet ,risk_veto_ohne_halten' fuer Zeilen der Rollen-Kette, deren Veto die Entscheiderstufe setzt (`veto_art='entscheider'`, ,Potential unter der Schwelle'). Dort steht die Aktion des Modells ABSICHTLICH neben dem Veto - es ist der Veto-Schatten-Arm (`rollen_lauf`, Schritt 44). Die Regel nimmt die Rollen-Kette nur beim Gate-Flag aus, nicht beim Veto. Folge am 15.09.: ,Auffaelligkeiten 2 -> 4' (XLM und BEAMX NACHKAUFEN, je 14. und 15.09.), von der Notebook-Zusammenfassung als Verschlechterung gelesen. Loesung: Zeilen mit `veto_art='entscheider'` der Rollen-Kette ausnehmen", 'offen',
               'extract_notebook_diagnose.py _auffaelligkeiten; agent/rollen_lauf.py _schreibe_nein', '', '', 'Notebook T440: notebook_diagnose.json 15.09. 08:34 (Log 12.09. 08:46 bis 15.09. 08:34, 13.396 Zeilen), Sicherung 2026-09-15_0545 nur lesend, Screenshot der NB-Zusammenfassung'),
    Befundlage('2.455-hebelsignale', "⚠️ RICHTIGSTELLUNG UND AUSGANGSLAGE FUER SCHRITT 59. Im Gespraech 15.09. sagte ich ,seit dem 12.09. kein einziges Hebelsignal' - FALSCH: meine Abfrage suchte die Spalte `hebel_faktor`, sie heisst `hebel`. Richtig (Sicherung 15.09. 05:45): Zeilen mit Hebel ueber 1 - 12.09. 9, 13.09. 3, 14.09. 3, 15.09. 0; davon durchgelassen 2, 3, 3. ALLE 8 durchgelassenen sind NACHKAUFEN mit instrument hebel auf GEHALTENEN Werten (BTC 5,0x, SOL 3,9x, TAO 2,5 bis 2,7x, BEAMX 2,2x; Symbole AVAX, BEAMX, BNB, BTC, LINK, QNT, SEI, SOL, TAO). Die Rollen-Kette schrieb seit 12.09. 166 Zeilen, ALLE mit strategie `einstieg`: NACHKAUFEN spot 93, REDUZIEREN 24, HALTEN 23, VERKAUFEN 16, NACHKAUFEN hebel 8, KAUFEN 2. ➤ Die Unterscheidung Einstieg / Fuehrung / Ausstieg ist in den Daten NICHT abgebildet, und der Hebel entsteht heute als Aufstockung eines Bestands - beides ist Stoff fuer Schritt 59 (und 7c: Spot und Hebel auf demselben Wert als zwei Positionen)", 'gilt',
               'signals (hebel, action, strategie, instrument, gate_passed, risk_veto); holdings', '', '', 'Sicherung 2026-09-15_0545 nur lesend'),
    Befundlage('2.455-hebel-nachkaufen', "⚠️ NUTZERHINWEIS 15.09.: ,beim Einstieg BTC, SOL, TAO in Hebelpositionen sollte es nicht NACHKAUFEN sein'. AM CODE: das Aktionsvokabular der Rollen-Kette (`empfehlung_vertrag.AKTIONEN`) kennt KAUFEN, NACHKAUFEN, REDUZIEREN, VERKAUFEN, NICHTS_TUN - Rolle BC sagt NACHKAUFEN, weil ein SPOT-Bestand da ist. Ob der Trade gehebelt wird, entscheidet danach die Rechnung aus der Geometrie (`entscheidungsrechnung`, Etikett hebel bei noetigem Faktor ueber 1). So entsteht ,NACHKAUFEN (Hebel)' fuer eine Hebelposition, die es noch gar nicht gibt - am Notebook alle 8 durchgelassenen Hebelempfehlungen seit 12.09. (2.455-hebelsignale). Fachlich ist das ein EINSTIEG in eine neue, eigene Position (Nutzerentscheidung 7c vom 14.09.: Spot und Hebel auf demselben Wert sind zwei Positionen); NACHKAUFEN waere es nur bei einer offenen HEBELposition. Folgen noch nicht geprueft: Cooldown, Topf, Aggregat-Deckel und Mailbetreff lesen die Aktion. Getragen von Schritt 60, gemessen in Schritt 59", 'offen',
               'agent/empfehlung_vertrag.py AKTIONEN; agent/entscheidungsrechnung.py etikett; agent/rollen_lauf.py', '', '', 'Sicherung 2026-09-15_0545 (signals); Code 15.09.; Nutzerhinweis 15.09.'),
    Befundlage('2.455-hebelstufen-gebaut', "✔✔ HEBEL: EINE ZAHL FUER ALLE RECHNUNGEN, IN DER MAIL DIE EINSTELLBAREN STUFEN (Nutzerauskunft 15.09.: bei Bitpanda meist 2x, 3x, 5x, 10x, nicht fuer jedes Asset gleich; Nutzerentscheidung 15.09.: beide Nachbarstufen zeigen, die untere hervorheben, NICHT aufrunden - fachliche Begruendung: Aufrunden sprengt das Budget, ONDO 2,09x -> 3x waeren 44 Prozent darueber, und 1,9x -> 2x machte aus Spot einen Hebel, den die Bewertung verneint). GEBAUT: (1) `rechne` rundet nicht mehr - Verlust, Gewinn, Datenbank, Deckel, Liquidation und ,Tage bis zum Stop' rechnen mit demselben Hebel. ⚠️ Auch nicht auf zwei Stellen: die Suite fing, dass bei RM-11-Bindung ein Aufrunden um 0,005 die Liquidation vor den Stop schiebt. (2) `hebel_stufen`: die hoechste Stufe <= Hebel (hervorgehoben, liegt immer im Budget und ist immer sicher) und die naechste darueber mit Ueberschuss ueber das Budget - nur bis zur Hebelgrenze, jenseits von RM-11 ,NICHT SICHER'; genau auf einer Stufe nur sie; Stufen aus `rollen_kette.hebel_aus_quote.hebel_stufen` (Vorgabe 2/3/5/10). (3) Mail: ,Hebel rechnerisch 4,17x - einstellbar' mit einer Zeile je Stufe (Verlust, Gewinn, Liquidation, sicheres Fenster), Pfeil an der unteren; Ergebnissatz und Blick-Block nennen die untere Stufe; der Kopfhinweis ,!! Liquidation vor Ablauf der Haltedauer' gilt der empfohlenen Stufe, die obere sagt es in ihrer eigenen Zeile. Die Regel ,unter 2x Spot' bleibt unberuehrt. 📏 PRUEFSTAND SOL, Sicherung 15.09.: LONG rechnerisch 4,17x - 3x im Budget (am Stop -159 EUR, Liquidation 63,04 EUR, sicher bis Tag 81), 5x +20 Prozent (-266 EUR, Liquidation 75,65 EUR, nur 7 Tage - kuerzer als die Haltedauer); SHORT 3x im Budget, 5x NICHT SICHER. In 400 Zufallsfaellen lag die hervorgehobene Stufe nie ueber dem Budget. ⚠️ FUER SCHRITT 60 (Mailstruktur) beobachtet: Betrag und Ergebnis stehen im Blick-Block UND in der Rechnung, der Hebel an drei Stellen (Blick, Rechnung, Herleitung aus der Wahrscheinlichkeit)", 'gilt',
               'agent/entscheidungsrechnung.py rechne, hebel_stufen, stufen_kurz, saetze; agent/signal_mail.py Blick-Block; agent/betraege.py HEBEL_AUS_QUOTE_VORGABE; agent/rollen_lauf.py; pruefe_pakete.py Hebelstufen', '', '', 'Code 15.09.; Suite-Paket Hebelstufen (12 Pruefungen, darunter 400 Zufallsfaelle; Gegenprobe gegen den alten Code rot am Befund selbst); volle Suite 2.610 Pruefungen, nur die 3 bekannten Datenstand-Zeilen rot, fuenf bestehende Pruefungen auf die neue Darstellung umgestellt; Pruefstand `pruefstand_hebelmail.py` SOL LONG und SHORT gegen die Sicherung 2026-09-15_0545 mit echter config.yaml'),
    Befundlage('2.455-cash-gesperrt', "⚠️⚠️ DAS CASH IST UM RUND 2.940 EUR ZU NIEDRIG - WEIL BITPANDA FUSION ES SPERRT, UND DIE SCHNITTSTELLE ZEIGT DAS NICHT. Nutzerauskunft 15.09.: Cash bei Bitpanda rund 3.600 EUR, Stablecoin rund 1.360 EUR (nach einem Swap). Live-Abfrage der API v1 am 15.09.: EUR-Wallet `balance` 659,99 EUR, `pending_transactions_count` 0, KEIN Feld fuer gesperrte Betraege; EURCV 1.359,25 (stimmt). Die Differenz ist das in offenen Fusion-Orders gebundene Geld - Bitpanda nimmt es aus dem synchronisierten Guthaben (bekannt seit 11.07., Kommentar in `bitpanda_sync`). FOLGEN: (1) ,Cash frei' rechnet mit 659,99 statt rund 3.600 und meldet heute 69 EUR frei; (2) das GUI-Feld ,Fiat-Guthaben auf Boerse (EUR, manuell)' schreibt in DENSELBEN Schluessel, den der Bitpanda-Abgleich alle 30 Minuten ueberschreibt, sobald der Wert abweicht - eine Eingabe dort haelt hoechstens bis zum naechsten Abgleich; das Feld stammt aus der Zeit ohne API (P-7, 10.07.). (3) Eine Sperre bleibt unbemerkt. MOEGLICHE QUELLE: Bitpanda Fusion hat eine eigene Schnittstelle mit offenen Orders (docs.fusion.bitpanda.com, Fusion API) - braucht einen eigenen Schluessel, nicht geprueft. NUTZERVORGABE 15.09.: *,Eine Warnung mit Rufzeichen und Handlung sollte erfolgen, wenn etwas sperrt'*; das GUI-Feld soll bewertet werden. Loesungsweg vorgelegt ➤ FUSION-DOKU GEPRUEFT 15.09. (docs.fusion.bitpanda.com): `GET https://api.fusion.bitpanda.com/v1/account/balances` liefert je Waehrung `available` und `locked` (,in offenen Orders gebunden'); `GET /v1/account/orders?status=open` die offenen Orders (pair, side, type, quantity, amount, limitPrice, filledQuantity, createdAt); Kopfzeile `x-api-key`; Grenze 1.000 Anfragen je Minute; Schluessel mit Berechtigungen Read, Trade, Transfer, hoechstens 1 Jahr gueltig, Kosten nicht genannt. LIVE-PROBE mit dem vorhandenen Bitpanda-Schluessel: beide Endpunkte 401 (,Credentials / Access token wrong') - es braucht einen EIGENEN Fusion-Schluessel, nur Berechtigung Read, den der Nutzer anlegt. ⚠️ WEITERER VERDACHT, noch NICHT geprueft: laut Bitpanda fehlen in offenen Fusion-Orders gebundene Bestaende generell im synchronisierten Guthaben - gilt das auch fuer KRYPTO in offenen Verkaufsorders, fehlt dieser Teil in `holdings` und damit im Portfoliowert, im Kapital fuer r x Kapital und in der Ausstiegsfuehrung. Mit dem Read-Schluessel pruefbar (`locked` je Symbol). ➤ FUSION-SCHLUESSEL AKTIV 15.09. (nur Read, gueltig bis 15.09.2027, in `.env` als `FUSION_API_KEY`). Live-Test nur lesend: `/v1/account/balances` 200 - EUR verfuegbar 659,99, gebunden 3.000,00; `/v1/account/orders?status=open` 200 - 11 offene KAUF-Limit-Orders, Summe 3.000 EUR (BTC 1.000/500/400/200/200, TAO 150/100, ETH 150/100, BNB 100, XLM 100; aelteste 04.06.2026); leerer POST auf `/account/orders` 401 - kein Schreibrecht, wie gewollt. KEINE gebundene Krypto (keine Verkaufsorders) - der zweite Verdacht trifft heute nicht zu, der Bestandsfehler 2.455-bestand-gestakt hat eine andere Ursache. Die Public API zeigte 3.007,52 Differenz - 7,52 EUR vermutlich vorgemerkte Gebuehren, beim Bau pruefen", 'offen',
               'agent/toepfe.py cash_frei_eur; importer/bitpanda_sync.py sync_fiat_cash_from_bitpanda; ui/portfolio.py Cash-Feld', '', '', 'Bitpanda API v1 live 15.09. (fiatwallets, asset-wallets, nur lesend); ui/portfolio.py; importer/bitpanda_sync.py; Nutzerauskunft 15.09.'),
    Befundlage('2.455-cash-messbar', "✔ DAS GESPERRTE CASH IST MESSBAR - OHNE NEUEN SCHLUESSEL. Die NEUE Bitpanda-Schnittstelle (Public API, `api.public.bitpanda.com/v1/portfolio`) nimmt den VORHANDENEN Schluessel an (Kopfzeile `X-Api-Key`) und liefert je Position `balance` (gesamt) und `available_balance` (verfuegbar). EUR live 15.09.: gesamt 3.667,51, verfuegbar 659,99 - 3.007,52 EUR gebunden, deckt sich mit der Nutzerauskunft (rund 3.600). Die ALTE Schnittstelle (`api.bitpanda.com/v1`, unsere heutige Anbindung) kennt nur den verfuegbaren Teil. Die Fusion-API braeuchte einen eigenen Schluessel (Probe 401) und bleibt nur fuer die ORDERLISTE interessant (welche Orders binden das Geld). ⚠️ DIE ALTE SCHNITTSTELLE IST ABGEKUENDIGT: laut Migrationsleitfaden (docs.public.bitpanda.com, ,Migrating from the legacy API') ersetzt `/v1/portfolio` die Endpunkte `/wallets`, `/fiatwallets`, `/asset-wallets`, und `/v1/operations` ersetzt `/wallets/transactions`, `/fiatwallets/transactions`, `/trades` - ein Abschaltdatum nennt der Leitfaden nicht. Daran haengen heute Bestand, Cash, Staking und der Hebel-Abgleich. ➤ UMFANG DER NEUEN API LIVE GEPRUEFT 15.09. (nur lesend): `/v1/portfolio` je Position `balance`, `available_balance`, `invested_amount`, `average_buy_price`, `currency_balance` (EUR-Wert), `total_return`, `total_return_percent` - Krypto, Aktien, ETF, Metalle und EUR (43 Positionen); `/v1/operations` mit typisierten Vorgaengen (u. a. reward, passive_earn_reward, onetime_reward, stake, swap, savings_plan, advanced_trading_reserve, stock_exchange_buy/sell/reserve, securities_tax_refund), je Buchung Betrag, Gebuehr, Kurs, Saldo danach; `/v1/portfolio-history` (Kontowert-Verlauf, Zeitraum YEAR: 180 Punkte); `/v1/assets` Katalog mit Cursor. ⚠️ ZU PRUEFEN VOR EINEM UMBAU: (a) die Probe ueber 8 Seiten `/v1/operations` lieferte Zaehlungen, die alle durch 8 teilbar sind - Verdacht, dass die Paginierung dieselbe Seite wiederholt; (b) Hebel-/Margin-Vorgaenge tauchten in diesen 800 Buchungen nicht auf - ob die neue API sie fuehrt, ist offen (der Hebel-Abgleich braucht sie); (c) `average_buy_price` rechnet anders als unser Einstand (BTC: 152.932 EUR bei 0,0522 Stueck und 7.984 EUR investiert). Die Fusion-API deckt nur die in Fusion handelbaren Kryptopaare und Fiat ab - nicht das ganze Portfolio", 'gilt',
               'importer/bitpanda_sync.py; api/bitpanda.py (alte Schnittstelle)', '', '', 'Bitpanda Public API live 15.09. (`GET https://api.public.bitpanda.com/v1/portfolio`, `/v1/assets` 140 Seiten, nur lesend, vorhandener Schluessel); Sicherung 2026-09-15_0545 (holdings, price_cache); Nutzerauskunft 15.09.'),
    Befundlage('2.455-bestand-gestakt', '⚠️⚠️⚠️ DER BESTAND IN DER DATENBANK STIMMT NICHT - DIE GESTAKTEN MENGEN STEHEN SEIT DEM 16.07. Abgleich 15.09. Public API gegen `holdings` (Sicherung 05:45): TAO Bitpanda 2,99 gegen DB gestakt 5,82 (Stand 16.07.); SUI 821,5 gegen 1.554,1 (16.07.); SOL 3,01 gegen 5,93 (16.07.); NEAR 194,3 gegen 266,8 (16.07.); HYPE 1,52 gegen 3,02 (16.07.); AVAX 25,4 gegen 40,4 (16.07.); ETH 0,512 gegen 0,026 + 0,943 gestakt (28.08.); BNB 0,124 gegen 0,159; umgekehrt ASTER 187,7 gegen 106,6 (16.07.). Zu aktuellen Preisen fuehrt die DB rund 2.600 EUR MEHR, als bei Bitpanda liegt - bei 17.696 EUR Kapital rund 15 Prozent. `updated_at` zeigt: die gestakten Mengen wurden seit dem Import am 16.07. nicht nachgefuehrt (SEI, VSN, BNB am 09.09. dagegen schon). FOLGEN: das KAPITAL fuer r x Kapital (Hebel) ist zu hoch, der Portfoliowert und Z-3 ebenso; die Kette beurteilt Bestaende, die es so nicht gibt (Nachkaufen, Reduzieren, Stummmeldung, Einstand). URSACHE NOCH NICHT BELEGT: Verkauf oder Unstaking nach dem 16.07., das der Abgleich ueber die alte Schnittstelle nicht erfasst. Symbolnamen weichen teils ab (Bitpanda VST-US, IS0C, CC gegen VST, ISOC, CANTON) - fuer einen Umbau zu klaeren. EURCV 50 weniger ist der Swap des Nutzers (erwartet). ➤ URSACHE BELEGT 15.09. (Screenshots Bitpanda Earn: TAO 2,99159105 und SOL 3,01197743 zu 100 Prozent gestakt - deckungsgleich mit der Public API). Nachgerechnet mit `compute_staked_quantities` ueber die VOLLE Transaktionshistorie der alten API (9.605 Buchungen, nur lesend): TAO 2,910364, SUI 777,025585, NEAR 133,412137, AVAX 20,184026, HYPE 1,507860 - die DB fuehrt davon EXAKT DAS DOPPELTE (5,820728 / 1.554,051170 / 266,824275 / 40,368052 / 3,015719). URSACHE 1 DOPPELZAEHLUNG: `sync_from_bitpanda` rechnet die gestakte Menge als `existing` plus Stake-Transfers seit seinem EIGENEN Cursor; beim ersten Lauf (Cursor leer, 16.07.) enthielt `existing` schon die vom Einstandspreis-Knopf berechnete Menge, und die volle Historie wurde noch einmal addiert. URSACHE 2 REWARDS FEHLEN: die Rekonstruktion zaehlt nur stake/unstake-Transfers; Staking-Ertraege tauchen dort nicht auf - TAO live 2,991591 minus gerechnet 2,910364 = 0,081227, exakt die im Screenshot genannten Rewards (0,08122702 TAO). Bei NEAR (+61) und AVAX (+5,3) ist die Differenz groesser als plausible Rewards - dort fehlt noch etwas, nicht geklaert. Kleine Reste bleiben ungestakt (ETH 0,0259 verfuegbar) - Nutzerhinweis, kein Fehler. FOLGERUNG: eine Rekonstruktion aus Buchungen bleibt fehleranfaellig; die Public API liefert den Bestand je Position direkt', 'offen',
               'database holdings.staked_quantity; importer/bitpanda_sync.py; agent/portfolio_historie.py schreibe_tageswert', '', '', 'Bitpanda Public API live 15.09. (`GET https://api.public.bitpanda.com/v1/portfolio`, `/v1/assets` 140 Seiten, nur lesend, vorhandener Schluessel); Sicherung 2026-09-15_0545 (holdings, price_cache); Nutzerauskunft 15.09.'),
    Befundlage('2.455-bitpanda-stufe0', '✔✔ STUFE 0 DER BITPANDA-UMSTELLUNG, PRUEFUNGEN 0.1 UND 0.2 (15.09.). (0.1) Die Buchungsliste der neuen API IGNORIERT DEN CURSOR - `next_cursor` ist ein Base64-Zeitstempel, jeder Folgeabruf liefert Seite 1 erneut (Fehler bei Bitpanda; `cursor`, `page_cursor`, `after`, `next_cursor` alle wirkungslos). ZUVERLAESSIG ist das Abrufen ueber DATUMSFENSTER (`to` = aeltester Zeitpunkt der letzten Seite): 7.857 Vorgaenge, 19.482 Buchungen, KEINE doppelte Buchungs-ID, 13.09.2024 bis 15.09.2026. (0.2) HEBELGESCHAEFTE SIND ENTHALTEN: margin_trading_open_long 917, close_long 308, liquidation_long 7; dazu stake 384, unstake 170, reward 955, onetime_reward 67, best_reward 21, passive_earn_reward 5, instant_trade_bonus 1.468, swap 682, dust_swap 49, advanced_trading_reserve/release/buy, stock_exchange_buy/sell/reserve, deposit, withdrawal, refund, ca_dividend, merger_crypto. ➤ DER BESTAND IST EXAKT NACHBILDBAR: jede Buchung traegt `asset_balance_after` je Wallet (`wallet_owner`: shared-default, staking-service, margin-trading, margin-trading-credit, stock-exchange, advanced-trading); die Summe der letzten Salden je Wallet stimmt fuer ALLE 43 Positionen mit `/v1/portfolio` ueberein (Abweichung 0). Damit ist der Bestand fuer jeden Tag seit 09.2024 rekonstruierbar - Voraussetzung fuer eine saubere Rueckrechnung der Portfoliowert-Historie OHNE Vermerk. ⚠️ Beim Umbau zu trennen: margin-Wallets gehoeren zum Hebel, nicht zum Spot-Bestand. WIRKUNG DES BESTANDSFEHLERS (am Code): Kapital fuer r x Kapital (`aktuelles_kapital`, nur juengste Zeile) seit dem Rollout Paket B zu hoch - die 8 Hebelempfehlungen 12. bis 14.09. rechneten mit rund 15 Prozent zu viel Risiko; Z-3 (`index_wert`) mit falscher Gewichtung, kein Alarm ausgeloest; Bestandsmenge und -wert in Prompt und Mail (`rollen_eingabe`, `rollen_lauf`), Verkaufsmenge (`verkaufsrechnung`), Stummmeldung. NICHT betroffen: alle Beitrags-, Schwellen-, Stopweiten- und Messnorm-Messungen (Kurs- und Terminmarktdaten, `messdaten.db`); die Portfoliowert-Historie liest ausser Kapital und Z-3 nur ein Altbestand-Werkzeug (`messe_akkumulation_az4`)', 'gilt',
               'Bitpanda Public API /v1/operations, /v1/portfolio; agent/portfolio_historie.py; agent/rollen_eingabe.py; agent/rollen_lauf.py; agent/verkaufsrechnung.py', '', '', 'Bitpanda Public API live 15.09. nur lesend: `/v1/operations` vollstaendig ueber Datumsfenster (79 Abrufe, 40 s), `/v1/portfolio`; Code-Suche nach Lesern von holdings, staked_quantity, portfolio_wert_historie'),
    Befundlage('2.454', "✔✔ NOTEBOOK-KONTROLLE NACH DEM ROLLOUT BESTANDEN (Commit 15341b8). Pruefskript 8 von 8 OK: Module, Terminmarkt 39 Werte in 30 min, BTC frisch, Umlaufmenge 61, Migration, Datenfrische. Export: Abschnitt Terminmarkt ohne Auffaelligkeit (Leser 37 frisch, 2 nicht bei Binance, 4 nie), Datenfrische 20 von 20 frisch - Bestand frisch mit Job bitpanda_holdings, keine ueberfaelligen Jobs, keine Schema-Drift. Log: `terminmarkt_job` laeuft am Notebook 3 bis 4 min und endet jedes Mal erfolgreich; nach dem Start 20:21 ,Datenfrische: alle 20 Faktenquellen frisch'. Der Start 20:19 endete nach 16 s ohne Fehler (manuell?). Offene Funde: 2.454-ampel (Folge von Schritt 54), -laufzeit, -gemini, -etfbestand, -rauschen, -vix", 'gilt',
               'Schritt 54; Befunde 2.454-*', '', '', 'Notebook T440, 14.09.2026 abends: pruefe_rollout_14_09_T440.txt, notebook_diagnose.json (Export 20:33), log_auszug 11.09. 20:41 bis 14.09. 20:26 (12.815 Zeilen)'),
    Befundlage('2.454-ampel-gebaut', "✔✔ DIE AMPEL MELDET NUR NOCH ECHTE AUSFAELLE. Neue Ausnahme `api.derivatives.SymbolNichtGelistetError` (Unterart von NoOpenInterestDataError, alte Faenger greifen weiter); `track_api_health` bucht sie WEDER als Fehler NOCH als Erfolg. Erkannt an genau den Antworten, die die Boersen live gaben: Binance OI HTTP 400 Code -1121; Binance Long-Konten HTTP 200 leere Liste; Bybit retCode 10001 ,Symbol Is Invalid' (VSN, SUPRA, CANTON) ODER retCode 0 mit leerer Liste (XNO) - die zweite Bybit-Variante fand erst der Live-Durchlauf; OKX Code 51001. Die Log-Zeile je nicht gelistetem Symbol geht von INFO auf DEBUG (rund 770 Zeilen weniger am Tag). 📏 LIVE: nach einem echten Durchlauf ueber alle 43 Kryptowerte Binance, Bybit und OKX ,ok' OHNE gebuchten Fehler; GEGENPROBE echter Verbindungsfehler -> rot, naechster Erfolg -> gruen. Suite-Paket Ampel: fuenf ,gibt es nicht'-Antworten ohne Buchung, fuenf echte Fehler (HTTP 500, anderer Binance-Code, Bybit 10001 mit anderem Text, OKX-Code mit leerer Liste, Verbindungsfehler) weiter rot, Erfolg weiter gruen, Abdeckungszaehler unveraendert; mit dem alten `api_health.py` wird die Kernpruefung rot. ⚠️ Am Notebook wird die Ampel mit dem ersten erfolgreichen Abruf nach dem Neustart gruen ✔ AM NOTEBOOK BESTAETIGT 15.09.: Binance, Bybit, OKX ok, letzter Fehler vor dem Neustart", 'gilt',
               'api/derivatives.py SymbolNichtGelistetError; database/api_health.py; agent/krypto/hebel_screening.py fetch_and_store_oi_snapshot; pruefe_pakete.py Ampel', '', '', 'Live 14.09. abends: Antworten von Binance, Bybit und OKX fuer XNO, VSN, SUPRA, CANTON, AIOZ, FLOKI und BTC; terminmarkt_job gegen eine DB-Kopie; Suite-Paket Ampel (6) mit Gegenprobe gegen den alten api_health.py'),
    Befundlage('2.454-ampel', "⚠️ FOLGE VON SCHRITT 54: DIE ANBIETER-AMPEL FUER BINANCE, BYBIT UND OKX STEHT DAUERHAFT AUF ROT. Der neue Job fragt ALLE Kryptowerte ab - auch die vier, die keine Boerse fuehrt (CANTON, SUPRA, VSN, XNO), und bei Binance AIOZ/FLOKI. Jeder Durchlauf erzeugt dort Fehler, der letzte Fehler ist juenger als der letzte Erfolg -> `api_health_status` ,fehler' (Export: binance/bybit/okx fehler, Erfolg 18:25, Fehler 18:26). Das alte Screening fragte diese Werte nicht (Filter Hebelpruefung). Folge: die Ampel der Uebersichtsseite meldet einen Ausfall, der keiner ist - und ein echter waere nicht mehr zu sehen", 'abgeloest',
               'agent/krypto/hebel_screening.py fetch_and_store_oi_snapshot; database/api_health.py', '2.454-ampel-gebaut', 'nicht gelistete Symbole buchen keinen Ausfall mehr', 'Notebook T440, 14.09.2026 abends: pruefe_rollout_14_09_T440.txt, notebook_diagnose.json (Export 20:33), log_auszug 11.09. 20:41 bis 14.09. 20:26 (12.815 Zeilen)'),
    Befundlage('2.454-laufzeit-gebaut', "✔✔ DIE LAUFZEIT-KENNZAHL STIMMT WIEDER. `_LUECKE_AB_MINUTEN` 8 -> 20 (dichtester Takt 15 Minuten plus 5 fuer gestaffelte Starts und lange Laeufe; am Notebook-Log liegt zwischen 15 und 20 Minuten keine Luecke). `messe_basislinie.py` rechnete dieselbe Kennzahl mit 10 Minuten - liest jetzt dieselbe Konstante. 📏 NACHGESPIELT am Notebook-Log 11.-14.09.: alter Code reproduziert den Export exakt (85,5 %%, 61,4 h, 208 Luecken), neuer Code 26,8 %%, 19,2 h, 3 Luecken - 12.09. 12:33 bis 13.09. 05:48 (17,3 h), 12.09. 05:30 bis 07:08 (1,6 h), 12.09. 08:10 bis 08:31; die Basislinie kommt auf dieselben 19,2 h. Suite-Paket Laufzeit an kuenstlichen Logs mit bekannter Wahrheit: Dauerbetrieb 0, ein Ausfall genau einmal, Grenze 21/19 Minuten, Basislinie gleich; mit dem alten Code 4 von 5 rot. ⚠️ VORBEHALT FUER FRUEHERE ZAHLEN: ,Ausfallzeit 70,2 %%' (17.08., als Treiber der Signalflut nach dem Neustart genannt) und ,51 %%' stammen sehr wahrscheinlich aus derselben Rechnung. Das Log von damals gibt es nicht mehr - NICHT reproduzierbar, also nach R-R11 nicht umgestossen, aber nur unter Vorbehalt zu lesen ✔ AM NOTEBOOK BESTAETIGT 15.09.: Export 26,7 %% Ausfall, 3 Luecken, Schwelle 20", 'gilt',
               'extract_notebook_diagnose.py _LUECKE_AB_MINUTEN, _laufzeit; messe_basislinie.py _laufzeit; pruefe_pakete.py Laufzeit', '', '', 'Notebook-Log 11.09. 20:41 bis 14.09. 20:26 (12.815 Zeilen) mit altem und neuem Code nachgespielt; Suite-Paket Laufzeit (5 + Standard-DB) mit Gegenprobe gegen den alten Code'),
    Befundlage('2.454-laufzeit', "⚠️⚠️ DIE LAUFZEIT-KENNZAHL DES EXPORTS IST FALSCH: ,85,5 %% Ausfall, 61,4 von 71,7 Stunden fehlen, 208 Luecken'. Nachgezaehlt am Log: die App lief vom 13.09. 06:00 bis 14.09. 20:00 OHNE eine Luecke ueber 15 Minuten (laengste 13,1 min); echte Ausfaelle im Fenster nur 12.09. 12:33 bis 13.09. 05:48 (17,3 h) und 12.09. 05:30 (1,6 h). Ursache: `_LUECKE_AB_MINUTEN = 8` - begruendet mit ,dichtester Takt 15 Minuten, acht sind grosszuegig'. Das ist umgekehrt: zwischen zwei 15-Minuten-Laeufen schweigt das Log bis zu 15 Minuten, jede Pause zaehlt als Ausfall. Seit das Hebel-Screening (12.09.) nichts mehr loggt, ist die Luecke zwischen den Laeufen die Regel. Mit Schwelle 20 Minuten: 3 Luecken, 19,2 h", 'abgeloest',
               'extract_notebook_diagnose.py:1322 _LUECKE_AB_MINUTEN, _laufzeit', '2.454-laufzeit-gebaut', 'Schwelle 20 Minuten, eine Definition fuer Export und Basislinie', 'Notebook T440, 14.09.2026 abends: pruefe_rollout_14_09_T440.txt, notebook_diagnose.json (Export 20:33), log_auszug 11.09. 20:41 bis 14.09. 20:26 (12.815 Zeilen)'),
    Befundlage('2.454-gemini', "○ GEMINI HTTP 503 (,high demand') OHNE AUSWEICHEN. 34 Antworten 503 am 14.09. ab 16:49; nach drei Versuchen gibt die Kette fuer den Wert auf (6 Urteile: ETH, AVAX, HYPE 2x, XLM, TAO), `waehle_client` wechselt nur nach Kontingent, nicht nach Ausfall. Der Wert wird im naechsten Umlauf (15 min) erneut gefragt (HYPE 18:22 und 18:36) - Verzoegerung, kein Verlust. Zu beobachten, wenn es tagelang anhaelt", 'offen',
               'scheduler/rollen_job.py waehle_client; api/gemini.py', '', '', 'Notebook T440, 14.09.2026 abends: pruefe_rollout_14_09_T440.txt, notebook_diagnose.json (Export 20:33), log_auszug 11.09. 20:41 bis 14.09. 20:26 (12.815 Zeilen)'),
    Befundlage('2.454-etfbestand', '⚠️ ETF-BESTAENDE SILBER UND ERDGAS SEIT 494 STUNDEN (20 Tagen) NICHT AKTUALISIERT (Export `externe_reihen.veraltet`). Die Datenfrische prueft `etf_bestand` je Quelle - solange Gold frisch ist, bleiben Silber und Erdgas unsichtbar. Dieselbe Klasse wie 2.452 und 2.453-kursreihe', 'abgeloest',
               'scheduler/background.py externe_reihen_job (ETF-Bestaende); agent/datenfrische.py', '2.454-etfbestand-quelle', 'die Ursache liegt tiefer: die Quelle liefert keine Tageswerte', 'Notebook T440, 14.09.2026 abends: pruefe_rollout_14_09_T440.txt, notebook_diagnose.json (Export 20:33), log_auszug 11.09. 20:41 bis 14.09. 20:26 (12.815 Zeilen)'),
    Befundlage('2.454-rauschen', "○ LOG-RAUSCHEN, das echte Warnungen verdeckt (14.09.: 1.274 WARNING, 7 ERROR). (1) `mindestkriterien` BC3 fuer die zehn Nicht-Kryptowerte je Umlauf: rund 900 WARNING am Tag - gemeldet wird nur, gesperrt nichts. (2) `backtest_llm1_historisch` ,EURCV keine Tageskerzen' 410x am Tag, steigend (68/222/365/410 vom 11. bis 14.09.). (3) `marktrang` ERROR ,Messbasis schnitt nicht lesbar (data/messdaten.db)' bei JEDEM Start - die Datei fehlt am Notebook bewusst; der Beitrag steht auf 0 Punkten, heute also wirkungslos, fuer die Akkumulation (Paket 2) aber zu klaeren. (4) Absicherung ,NACHKAUFEN ohne Richtung' (3QSS/NQSS/DBPK) = bekannt 2.451-absicherung", 'offen',
               'agent/mindestkriterien.py melde; scheduler/rollen_job.py:432; agent/marktrang.py schnitt', '', '', 'Notebook T440, 14.09.2026 abends: pruefe_rollout_14_09_T440.txt, notebook_diagnose.json (Export 20:33), log_auszug 11.09. 20:41 bis 14.09. 20:26 (12.815 Zeilen)'),
    Befundlage('2.454-vix', '○ `yfinance ^VIX: possibly delisted; no price data found` taeglich 03:32 (ERROR). Ob `macro_snapshot.vix_wert` dadurch veraltet, ist NICHT geprueft', 'offen',
               'api/macro.py (VIX)', '', '', 'Notebook T440, 14.09.2026 abends: pruefe_rollout_14_09_T440.txt, notebook_diagnose.json (Export 20:33), log_auszug 11.09. 20:41 bis 14.09. 20:26 (12.815 Zeilen)'),
    Befundlage('2.453', "📋 REVIEW VOR DEM ROLLOUT (Nutzerauftrag 14.09.: ,tiefes und detailliertes Review und Gegenpruefung - sind alle Datenquellen aktualisiert, alles verdrahtet?'). ⚠️ DAS PAKET IST NICHT NUR SCHRITT 54: seit dem letzten Commit (13.09. 06:09) liegen 122 Befunde und Schritte 31, 32, 41, 48, 49B, 50B, 51, 53, 54 unkommittet, das Notebook laeuft auf dem Stand 13.09. frueh. ✔ Kompiliert, importiert, Scheduler baut 22 Jobs inklusive `terminmarkt`, Migration gegen die NB-Sicherung additiv und wiederholbar (vier neue signals-Spalten beim ersten Umlauf), alte Signale lesbar. ✖ ANTWORT AUF DIE FRAGE ,ALLE DATENQUELLEN AKTUELL': NEIN - 2.453-turnover (Blocker), -spy, -rohstoff, -bestand, -cache, -kursreihe; Verdacht -hebelpos, -alterlos; dazu -fredkey (Sicherheit), -desktopdb, -plan", 'gilt',
               'Schritt 56; Befunde 2.453-*', '', '', 'Review vor dem Rollout 14.09.: drei unabhaengige Pruefungen (Laufzeit, Datenquellen, Doku) und eigene Nachpruefung; Produktionssicherung 2026-09-12_0646 nur lesend; Messbasis-Paket im Austauschordner'),
    Befundlage('2.453-bestand-gebaut', "✔✔ FEHLALARM BESTAND BEHOBEN - ausgeloest vom echten Fall: 14.09. 19:54 ,Job datenfrische fehlgeschlagen - refresh_bitpanda_holdings seit 3 Tagen', direkt nach dem Neustart des Rollouts. Der Abgleich lief alle 30 Minuten (Sicherung: Joblauf und Cash-Abgleich 12.09. 06:31, API-Erfolg 06:46), `holdings.updated_at` stand auf 11.09. 09:42. ➤ GEBAUT: (1) `sync_from_bitpanda` setzt am Ende jedes erfolgreichen Abgleichs `meta.bitpanda_holdings_synced_at` - auch ohne Mengenaenderung, nach den Wallet-Abrufen; (2) `datenfrische._stand_bestand` liest diesen Stempel als Daten- und Abrufstand, im Uebergang `cash_reserve_synced_at`, ohne jeden Abgleich wie frueher `updated_at`; (3) Jobname `bitpanda_holdings` (die echte Scheduler-ID). 📏 Nachgespielt: dieselbe Sicherung am 14.09. geprueft - alt ,abruf 3 Tage', neu ,frisch'. Paket Bestandsfrische: ruhiger Bestand frisch, alter Abgleich weiter ,abruf', Uebergang, Vorrang, Stempel nach den Abrufen, Jobname im Scheduler vorhanden", 'gilt',
               'importer/bitpanda_sync.py; database/db.py get/set_bitpanda_holdings_synced_at; agent/datenfrische.py _stand_bestand; pruefe_pakete.py Bestandsfrische', '', '', '14.09. abends: Fehlalarm-Mail 19:54 am Notebook; Nachspielen an der Sicherung 2026-09-12_0646; Suite-Pakete Bestandsfrische (8), Vetoart (Schemapruefung mit Gegenprobe), voller Exportlauf gegen eine Kopie mit umgelenktem Ziel (TIT_EXPORT_ZIEL)'),
    Befundlage('2.453-veto', '⚠️⚠️⚠️ DER NOTEBOOK-EXPORT BRACH SEIT DEM PULL VOM 13.09. AB - nicht durch das heutige Paket, sondern durch Commit 44a8947 (12.09. 17:30). `_aggregate_resolved_signal_rows(veto=True)` wandte den Filter `NUR_RISK_GATE` (veto_art) auch auf `hebel_signals` an; dort gibt es die Spalte nicht - `no such column: veto_art` auf JEDER Datenbank. Betroffen: `compute_veto_shadow_performance` im Export (der GANZE Export bricht ab - juengste Exportdatei im Austauschordner vom 12.09. 08:47) und in der Uebersichtsseite (`remote/status.py`). Gefunden beim Probelauf des Exports gegen eine Kopie, auf der Desktop-DB reproduziert. ➤ BEHOBEN: eigener `hebel_filter` ohne `veto_art` - die Begruendung stand schon an der dritten NUR_RISK_GATE-Stelle des Moduls (hebel_signals kann keine Entscheider-Zeile enthalten). ✔ Die Suite prueft jetzt die Veto- und Provider-Auswertungen gegen das ECHTE Schema (init_db + migriere); GEGENPROBE: mit dem alten Code rot. Warum sie es drei Tage nicht sah: alle Pruefungen lasen Quelltext oder Einzelfunktionen, keine lief gegen die Tabellenstruktur', 'gilt',
               'agent/krypto/backward_tracking.py _aggregate_resolved_signal_rows; extract_notebook_diagnose.py; remote/status.py:722; pruefe_pakete.py Vetoart', '', '', '14.09. abends: Fehlalarm-Mail 19:54 am Notebook; Nachspielen an der Sicherung 2026-09-12_0646; Suite-Pakete Bestandsfrische (8), Vetoart (Schemapruefung mit Gegenprobe), voller Exportlauf gegen eine Kopie mit umgelenktem Ziel (TIT_EXPORT_ZIEL)'),
    Befundlage('2.453-export', "✔✔ DIE STANDARDPRUEFUNG DES NOTEBOOKS (`extract_notebook_diagnose.py`) PRUEFT SCHRITT 54 UND DIE UMLAUFMENGE MIT (Nutzervorgabe 14.09.). Neuer Abschnitt `terminmarkt_und_umlaufmenge`: SAMMLUNG je Wert (Zeilen in 30 Minuten, Gesamtausfall, ueber 24 h, nie), LESER je Wert (frisch / veraltet / nie / nicht bei Binance - was Rolle BC und G wirklich bekommen), UMLAUF (was `marktrang.umlaufmengen` findet, ohne Nenner); die Auffaelligkeiten und die auffaelligen Datenfrische-Quellen stehen jetzt auch in der KONSOLE. Dazu migriert der Export die Spalten der Rollen-Kette (`signal_abbildung.migriere`) - gegen eine Datenbank ohne Kettenlauf brach er sonst an `veto_art` ab. 📏 GEGENPROBE an der eingefrorenen Sicherung 12.09.: ,GESAMTAUSFALL seit 62,5 h' und ,37 Werte bekommen keine aktuelle Angabe'. ⚠️ OFFEN: der Export ist 277 MB gross, weil er die ganze OI-Historie schreibt - und die waechst ab jetzt um rund 13.600 statt 8.350 Zeilen je Tag", 'gilt',
               'extract_notebook_diagnose.py _terminmarkt_und_umlaufmenge, main()', '', '', '14.09. abends: Fehlalarm-Mail 19:54 am Notebook; Nachspielen an der Sicherung 2026-09-12_0646; Suite-Pakete Bestandsfrische (8), Vetoart (Schemapruefung mit Gegenprobe), voller Exportlauf gegen eine Kopie mit umgelenktem Ziel (TIT_EXPORT_ZIEL)'),
    Befundlage('2.453-kurs-gebaut', "✔✔ KURSREIHEN: S&P-REFERENZ, NACHLADEN NACH HANDELSTAGEN, FRISCHE JE WERT (Nutzerentscheidung 15.09.: A, B und C zusammen). URSACHE, am Code und am Notebook-Log belegt: (1) die S&P-Reihe lud nur die alte Themen-ETF-Pipeline - Stand 13.08.; (2) der Tagesjob benutzte die Waechter der Pipelines, die erst nach MEHR ALS 5 (Hedge 3) KALENDERTAGEN nachluden - am Montag 14.09. abends ankerten Rohstoffe, Themen-ETF und Hedge auf dem 11.09., Themen-ETF nur 4 von 5 gedeckt; (3) die Frische mass die Tabelle, Krypto verdeckte alles. ➤ GEBAUT: A `_refresh_nicht_aktien_ohlc` laedt `_ensure_benchmark_backfilled` mit; B `staleness.reihe_ist_ueberholt` (letzter Kurs vor dem letzten abgeschlossenen Handelstag, Wochenenden zaehlen nicht) in Themen-ETF, Rohstoffe und Hedge; C `datenfrische._kursreihen_je_wert`: jedes Watchlist-Symbol ohne Cash und jede Referenz (S&P, Rohstoff-Futures, Hedge-Index), Krypto > 2 Tage, Wertpapiere und Referenzen > 3 Handelstage -> Urteil ,werte', das per Mail meldet - mit den Werten beim Namen und OHNE einen Abrufausfall zu behaupten; Werte ohne jede Reihe unter ,ohne_reihe', nicht gemeldet (A2/2.450-neu); Export nennt die Werte. 📏 NACHGESPIELT Sicherung 12.09.: meldet S&P (13.08.), OD7C/H/L/N samt Futures (07.09.), ISOC - die alte Pruefung sagte ,frisch'. 📏 LIVE gegen Kopie: vorher 13 Wertpapier-/Referenzreihen veraltet, nach dem Tagesjob (13 s) keine; S&P, Rohstoffe, Futures, ISOC auf dem 14.09., CEBS/VVMX/X136/DBPK auf dem 11.09. (yfinance ohne Montag fuer diese EU-Kuerzel zu der Uhrzeit, innerhalb der Grenze). Paket Kursreihen: Handelstage, Pipelines, S&P im Job, je Wert, Gegenprobe Tabelle, Mail; mit dem alten Code rot. ⚠️ Kosten: der Tagesjob holt fuer ueberholte Reihen die volle Historie - rund 15 yfinance-Abrufe am Tag ✔ AM NOTEBOOK BESTAETIGT 15.09. 00:32 (Export): Nicht-Aktien-Refresh 11 Assets (hedge 2, referenz_spy 1, rohstoffe 4, themen_etf 5), S&P-Referenz auf dem 14.09., Datenfrische 20 von 20 frisch, kursreihe 62 Werte ohne Befund. ⚠️ ZEITPUNKT: der Refresh laeuft 24 h nach dem App-Start; lief er vor Mitternacht UTC, ist der Montag noch nicht der letzte abgeschlossene Handelstag - die Wertpapiere blieben auf dem 11.09. und holen Montag und Dienstag im naechsten Lauf. Rueckstand damit bis 2 Handelstage, innerhalb der Grenze 3", 'gilt',
               'staleness.py; agent/themen_etf/pipeline.py _is_history_stale; agent/rohstoff/pipeline.py _is_rohstoff_history_stale; agent/hedge/pipeline.py _ensure_ohlc_backfilled; scheduler/background.py _refresh_nicht_aktien_ohlc, _melde_datenfrische; agent/datenfrische.py _kursreihen_je_wert; extract_notebook_diagnose.py _datenfrische; pruefe_pakete.py Kursreihen', '', '', 'Sicherung 2026-09-12_0646 nachgespielt (am 12. und 14.09. geprueft); refresh_aktien_ohlc_job live gegen eine DB-Kopie (13 s); Notebook-Log 14.09. (Ankertage je Gruppe); Suite-Paket Kursreihen (10) mit Gegenprobe gegen den alten Code'),
    Befundlage('2.453-turnover-gebaut', '✔✔ BLOCKER GELOEST (Weg 1, Nutzerentscheidung 14.09.): DIE UMLAUFMENGE KOMMT TAEGLICH IN DIE BETRIEBSDATENBANK. `api.onchain.get_splycur_history` holt `SplyCur` von Coin Metrics Community - DIESELBE Quelle wie die Messung - in EINEM Abruf fuer die Messbasis von turnover (am 14.09.: 66 angefragt, 61 mit Reihe, 0,6 s; BNB, DOT, GAS, NEO, XTZ enden an der Quelle). Der Job `externe_reihen` (beim Start und taeglich 06:35) schreibt sie als `externe_reihe` quelle `coinmetrics_splycur`, 30 Tage Rueckgriff, eigener Fehlerfang. `marktrang.umlaufmengen` liest ZUERST die Betriebsdatenbank, dann ergaenzend die Messdatei - nur wenn sie Datum und Wert fuehrt; jeder Ort einzeln gefangen, leer = WARNUNG. Die Datenfrische ueberwacht die Quelle (Rolle W, 6 Tage, Job externe_reihen). 📏 IDENTITAET: an 1.769 gemeinsamen Tagen kein abweichender Wert gegenueber der Messdatei; turnover-Fuenftel Notebook-Lage gegen Desktop-Lage 61 von 61 gleich. 📏 NOTEBOOK-LAGE: 61 Werte mit Nenner; vor dem ersten Joblauf leer ohne Fehler. GEGENPROBE: der alte Leser wirft dort `no such column: datum`. Keine Schreibzugriffe auf die Standard-DB. ➤ UNABHAENGIGE GEGENPRUEFUNG 14.09.: kein Pflichtfehler; umgesetzt wurden drei Punkte - (a) ein unbekanntes Symbol kippte den GANZEN Abruf (live: HTTP 400), jetzt `ignore_unsupported_errors`/`ignore_forbidden_errors`, live mit Fremdsymbol 61 Werte; (b) der Abruf laeuft VOR dem 800-Tage-Boersenfluss, damit die Frischepruefung beim Start ihn schon sieht; (c) die Suitepruefung NUR LESEND verlangt auch `uri=True`. Bewusst offen: beide Coin-Metrics-Abrufe teilen eine Gesundheitsampel', 'gilt',
               'api/onchain.py:get_splycur_history; scheduler/background.py:externe_reihen_job; agent/marktrang.py:umlaufmengen, SPLYCUR_QUELLE; agent/datenfrische.py; pruefe_pakete.py Umlaufmenge', '', '', 'Live 14.09.: externe_reihen_job gegen eine Kopie der NB-Sicherung (20 s), Leser mit der NB-Symbollistendatei aus dem Austauschordner; Coin Metrics gegen die Messdatei (1.769 gemeinsame Tage); Suite-Paket Umlaufmenge (13)'),
    Befundlage('2.453-turnover', '⛔⛔⛔ ROLLOUT-BLOCKER: SCHRITT 49B SCHALTET AM NOTEBOOK DEN TURNOVER-BEITRAG AB. `marktrang.umlaufmengen()` liest `splycur (symbol, datum, wert)` aus `data/onchain_historie.db`. Am Notebook liegt diese Datei BEWUSST nur als SYMBOLLISTE (2.368, Paket vom 02.09., Tabelle `splycur (symbol TEXT)`). Nachgeprueft am Paket im Austauschordner: `no such column: datum`. Die Funktion hat nur try/finally, `raenge()` loggt und laesst turnover weg - EINER DER ZWEI TRAGENDEN BEITRAEGE faellt fuer alle Werte aus, schlechter als heute (dort 33 Werte ueber CoinGecko). Zweitens hat `splycur` keinen Job: nach 21 Tagen ohne `hole_fremdreihen.py splycur` verstummt turnover still - dieselbe Klasse wie 2.452. NUTZERENTSCHEIDUNG NOETIG vor dem Rollout', 'abgeloest',
               'agent/marktrang.py:636-677 umlaufmengen; Befunde 2.419, 2.368', '2.453-turnover-gebaut', 'geloest mit Weg 1 (Nutzerentscheidung 14.09.): taeglicher Abruf in die Betriebsdatenbank', 'Review vor dem Rollout 14.09.: drei unabhaengige Pruefungen (Laufzeit, Datenquellen, Doku) und eigene Nachpruefung; Produktionssicherung 2026-09-12_0646 nur lesend; Messbasis-Paket im Austauschordner'),
    Befundlage('2.453-spy', '⚠️⚠️ DIE US-MARKTREFERENZ STEHT SEIT 13.08. `_THEMEN_ETF_BENCHMARK_SPY` schreibt nur die ALTE Themen-ETF-Pipeline (`themen_etf/pipeline.py:122-131`), die seit der Umstellung auf die Rollen-Kette nicht mehr laeuft. `marktlage._bis` nimmt die letzte Kerze vor dem Ankertag OHNE Altersgrenze - Rolle A bekommt Saetze zum US-Aktienmarkt aus Daten vom 13.08.; `relative_staerke` laesst den Block nach 7 Tagen still weg. Nachgesehen an der Sicherung: letzte Kerze 2026-08-13. Besteht schon am Notebook, kommt NICHT mit diesem Paket', 'abgeloest',
               'agent/marktlage.py:78-90; agent/rollen_eingabe.py:411,474; agent/themen_etf/pipeline.py:122-131', '2.453-kurs-gebaut', 'Tagesjob laedt S&P-Referenz, Nachladen nach Handelstagen, Frische je Wert', 'Review vor dem Rollout 14.09.: drei unabhaengige Pruefungen (Laufzeit, Datenquellen, Doku) und eigene Nachpruefung; Produktionssicherung 2026-09-12_0646 nur lesend; Messbasis-Paket im Austauschordner'),
    Befundlage('2.453-rohstoff', '⚠️ DIE ROHSTOFF-REFERENZEN LAUFEN BIS ZU SECHS TAGE HINTERHER. `_ROHSTOFF_HISTORY_STALE_THRESHOLD_TAGE = 5` - nachgeladen wird erst danach. Sicherung 12.09.: `_ROHSTOFF_FUTURES_OD7C/H/L/N` und OD7* enden am 07.09. Rolle A liest den Rohstoff-Referenzsatz ohne Altersangabe. Bestand, nicht neu', 'abgeloest',
               'agent/rohstoff/pipeline.py:56,217-219', '2.453-kurs-gebaut', 'Tagesjob laedt S&P-Referenz, Nachladen nach Handelstagen, Frische je Wert', 'Review vor dem Rollout 14.09.: drei unabhaengige Pruefungen (Laufzeit, Datenquellen, Doku) und eigene Nachpruefung; Produktionssicherung 2026-09-12_0646 nur lesend; Messbasis-Paket im Austauschordner'),
    Befundlage('2.453-bestand', "⚠️⚠️ DIE FRISCHE DES BESTANDS MISST DAS FALSCHE - FEHLALARM. `holdings.updated_at` wird nur geschrieben, wenn sich die MENGE aendert (`bitpanda_sync.py:270-280`); die Datenfrische wertet es mit Zwei-Tage-Grenze als Abruf und MAILT ,Handlungsbedarf'. Sicherung: letzte Aenderung 11.09. 09:42 - ab dem 13.09. ohne Handel wahrscheinlich eine taegliche Fehlmeldung. Dazu ist der registrierte Jobname falsch (`refresh_bitpanda_holdings` statt `bitpanda_holdings`). Die Eskalationsmail steht schon im Commit-Stand", 'abgeloest',
               'agent/datenfrische.py:156,499; importer/bitpanda_sync.py:270-280', '2.453-bestand-gebaut', 'repariert 14.09. nach dem Fehlalarm um 19:54', 'Review vor dem Rollout 14.09.: drei unabhaengige Pruefungen (Laufzeit, Datenquellen, Doku) und eigene Nachpruefung; Produktionssicherung 2026-09-12_0646 nur lesend; Messbasis-Paket im Austauschordner'),
    Befundlage('2.453-cache', '⚠️ ZWEI PROZESS-ZWISCHENSPEICHER FRIEREN WERTE BIS ZUM NEUSTART EIN. `marktrang._SCHNITT_ZWISCHEN` (200-Tage-Schnitte, Frischepruefung und `eigenkurs` fuer Werte ohne Binance: CANTON, VSN, AIOZ, SUPRA) und `rollen_eingabe._benchmark_speicher` werden einmal je App-Start gerechnet und nie geleert. Das Notebook laeuft tagelang. Bestand, nicht neu', 'offen',
               'agent/marktrang.py:180-237,341,363; agent/rollen_eingabe.py:420-441', '', '', 'Review vor dem Rollout 14.09.: drei unabhaengige Pruefungen (Laufzeit, Datenquellen, Doku) und eigene Nachpruefung; Produktionssicherung 2026-09-12_0646 nur lesend; Messbasis-Paket im Austauschordner'),
    Befundlage('2.453-kursreihe', '⚠️ DIE FRISCHE DER KERZENREIHE IST JE TABELLE - DIESELBE BLINDSTELLE WIE 2.452. `kursreihe` misst `MAX(fetched_at)` ueber ganz `price_history_ohlc`; `refresh_aktien_ohlc` schreibt in dieselbe Tabelle. Ein eingefrorener Kryptowert, die SPY-Referenz (2.453-spy) oder ein einzelnes Symbol fallen nicht auf', 'abgeloest',
               'agent/datenfrische.py (Quelle kursreihe)', '2.453-kurs-gebaut', 'Tagesjob laedt S&P-Referenz, Nachladen nach Handelstagen, Frische je Wert', 'Review vor dem Rollout 14.09.: drei unabhaengige Pruefungen (Laufzeit, Datenquellen, Doku) und eigene Nachpruefung; Produktionssicherung 2026-09-12_0646 nur lesend; Messbasis-Paket im Austauschordner'),
    Befundlage('2.453-hebelpos', '○ VERDACHT: `hebel_positions` und die Liquidationspreise werden nur im Job der Rollen-Kette abgeglichen; ein Bitpanda-Ausfall ist nur eine Logwarnung, es gibt keine Frischepruefung (deckt sich mit 7d, 2.451-hebel). ➤ GEPRUEFT 15.09. (Code, Notebook-Log 12.09. 00:41 bis 15.09. 00:37, Sicherung 14.09. 22:40). TEIL 1 STIMMT, IST ABER HARMLOS: der Abgleich haengt am Job `hebel_screening`, laeuft seit H-4 (11.09.) unabhaengig vom Screening-Schalter - 212 Abgleiche, Abstand im Median 15,0 Minuten. Die zwei langen Luecken (114 und 1.038 Minuten am 12.09.) sind Zeiten, in denen die App nicht lief - im Log steht dort gar nichts. TEIL 2 STIMMT: zwei Ausfaelle in drei Tagen (503 von Bitpanda, 12.09. 07:08 und 14.09. 07:34), jeder EINZELN und im naechsten Lauf nachgeholt - der Abgleich laedt ab der letzten Transaktion und verliert nichts. Ein anhaltender Ausfall bliebe aber unbemerkt: nur eine WARNING je Lauf, kein Zeitstempel des letzten ERFOLGREICHEN Abgleichs (`hebel_position_last_synced_unix` ist die Zeit der letzten TRANSAKTION und steht ohne Handel still - am 14.09. auf dem 11.09.). Die gesamte Bitpanda-Stoerung faenge erst die Datenfrische des Spot-Bestands (Grenze 3 Tage). WIRKUNG HEUTE: KEINE - 0 offene Hebelpositionen, letzte geschlossen am 26.07. WIRKUNG MIT OFFENER POSITION: die Hebelfuehrung fuehrt einen veralteten Bestand (eine geschlossene Position bekaeme weiter Empfehlungen, eine neue keine), und der Aggregat-Deckel zaehlt falsch. Der Liquidationspreis selbst ist unkritisch - die Hebelfuehrung rechnet ihn mit den echten Tagen neu. LOESUNG = Entscheidung 7d vom 14.09. (Mail bei anhaltendem Ausfall), Umsetzungsschritte vorgelegt', 'abgeloest',
               'scheduler/background.py hebel_screening_job', '2.455-hebelabgleich-gebaut', 'Stempel, Mail ab 1 Stunde, Mailzeile, Datenfrische und Export gebaut (15.09.)', 'Review vor dem Rollout 14.09.: drei unabhaengige Pruefungen (Laufzeit, Datenquellen, Doku) und eigene Nachpruefung; Produktionssicherung 2026-09-12_0646 nur lesend; Messbasis-Paket im Austauschordner'),
    Befundlage('2.453-alterlos', '○ VERDACHT, NICHT EINZELN GEPRUEFT: weitere Leser ohne Altersgrenze, deren Saetze an ein Modell gehen - `positionierung._etf_bestand`, `_insider`, `_aus_reihe` (DefiLlama, Deribit), `rollen_eingabe.fundamentaldaten` und `umschlag`; manche Saetze tragen ihr Datum, Stablecoin, Optionsmarkt, Fundamentaldaten und Umschlag nicht. Dazu die Cash-Reserve (`toepfe.py:245`) ohne Blick auf `cash_reserve_synced_at` ➤ GEPRUEFT 15.09. (Code, Sicherung 15.09. 05:45). MIT ALTERSGRENZE: Boersenfluss, COT und Eindeckungsdauer (`_gepflegte_reihe`: Datenbank nur bis 30 h nach dem Abruf, der Satz nennt das Datum). OHNE GRENZE UND OHNE DATUM IM SATZ - Verdacht BESTAETIGT: (a) Stablecoin-Angebot und Optionsmarkt DVOL/Skew (`_aus_reihe`, Krypto/Rolle G) - am Notebook erst 30 Punkte, Satz ab 90 bzw. 60: HEUTE STUMM, Deribit spricht ab etwa 16.10., Stablecoin ab etwa 15.11.; (b) Insidergeschaefte (`_insider`) und Gewinn-/Umsatzwachstum (`rollen_eingabe.fundamentaldaten`) - nur Aktien, lesen den juengsten Punkt, AKTIV; (c) ETF-Bestand - ruht (Schritt 57); (d) Umschlag (`rollen_eingabe.umschlag`, Krypto/Rolle BC) - juengster `price_cache`-Stand ohne Blick auf `fetched_at`, AKTIV; (e) Cash-Reserve (`toepfe.cash_frei_eur`) - ohne Blick auf den Abgleich, AKTIV; ⚠️ RICHTIGSTELLUNG gegen meine erste Fassung: sie BEGRENZT NICHT, sie steht nur als Zeile ,Cash frei … EUR“ in der Mail, mit `!! reicht fuer diese Position nicht` im Kopf (Nutzer: ,Deckel laufen nur als Info fuer den User mit im eMail“; `entscheidungsrechnung`: ,Diese Zahlen begrenzen die Empfehlung NICHT“). Der Docstring von `toepfe.cash_frei_eur` sagt noch ,SIE BEGRENZT“ - ein Doku-Widerspruch. Mit den Zahlen vom 15.09. (EUR 659,99 + EURCV 1.409,25 - Reserve 2.000) sind 69 EUR frei - jede Kaufempfehlung ueber 69 EUR traegt damit das `!!`. ➤ NUTZERENTSCHEIDUNGEN 15.09. ZUR CASH-RESERVE: A1 - ist der Abgleich aelter als 6 Stunden, nennt die Zeile den Stand und traegt KEIN `!!`; B1 - Docstring von `toepfe.cash_frei_eur` berichtigen (begrenzt nicht); C3 - die Dauerwarnung gehoert in die Mailueberarbeitung (Schritt 60), jetzt keine Aenderung. Dazu neu 2.455-cash-gesperrt. WIRKUNG HEUTE: KEINE - alle Quellen heute 05:33 bis 05:34 UTC abgerufen, Cash 05:34. WIRKUNG BEI AUSFALL: das Modell bekaeme einen alten Stand als aktuellen Satz, und die Cash-Zeile nennte ein altes Guthaben - bis die Datenfrische nach 2 Tagen (Bestand 3 Tage) mailt, und auch danach weiter. Loesungsweg vorgelegt', 'offen',
               'agent/positionierung.py:450,547,592; agent/rollen_eingabe.py:221,263; agent/toepfe.py:245', '', '', 'Review vor dem Rollout 14.09.: drei unabhaengige Pruefungen (Laufzeit, Datenquellen, Doku) und eigene Nachpruefung; Produktionssicherung 2026-09-12_0646 nur lesend; Messbasis-Paket im Austauschordner'),
    Befundlage('2.453-fredkey', '⚠️⚠️ SICHERHEIT: DER FRED-SCHLUESSEL STEHT IM KLARTEXT IN DER DATENBANK. `api_health_status.last_error_message` speichert die volle Fehler-URL einschliesslich `api_key=` (Sicherung 12.09., Quelle fred, ein 502) - und diese Tabelle geht in den Notebook-Export im Austauschordner', 'abgeloest',
               'database/db.py track_api_health; extract_notebook_diagnose.py', '2.453-fredkey-gebaut', 'Schluessel maskiert in DB, Log und Export', 'Review vor dem Rollout 14.09.: drei unabhaengige Pruefungen (Laufzeit, Datenquellen, Doku) und eigene Nachpruefung; Produktionssicherung 2026-09-12_0646 nur lesend; Messbasis-Paket im Austauschordner'),
    Befundlage('2.453-desktopdb', '⚠️ DIE DESKTOP-STANDARD-DB WURDE AM 14.09. UM 18:28:56 GESCHRIEBEN - waehrend meines Laufs `simuliere_kette.py --db <Kopie>` (18:28:01 bis 18:29:05). Zwei nachverfolgte Wiederholungen mit Verbindungsprotokoll schrieben NICHT; die Ursache ist offen. Die Desktop-DB ist nicht die Produktion, die Regel gilt trotzdem. Die Spalten `kurs_bei_empfehlung_eur` und `veto_art` stehen dort - wann sie kamen, ist nicht feststellbar', 'offen',
               'simuliere_kette.py; data/tradinginfotool.db', '', '', 'Review vor dem Rollout 14.09.: drei unabhaengige Pruefungen (Laufzeit, Datenquellen, Doku) und eigene Nachpruefung; Produktionssicherung 2026-09-12_0646 nur lesend; Messbasis-Paket im Austauschordner'),
    Befundlage('2.453-plan', "⚠️ DIE PLANPRUEFUNG ,JEDER OFFENE BEFUND HAT EINEN OFFENEN SCHRITT' SIEHT NUR DIE 20 HOECHSTEN NUMMERN und vergleicht als Teilzeichenkette (`2.452` gilt als getragen, wenn `2.452-alt` im Plan steht). So blieben 2.419-saetze und 2.445-fenster ohne Traeger. Beide sind im Review nachgezogen; die Pruefung selbst ist noch nicht verschaerft", 'offen',
               'pruefe_pakete.py:20557-20582', '', '', 'Review vor dem Rollout 14.09.: drei unabhaengige Pruefungen (Laufzeit, Datenquellen, Doku) und eigene Nachpruefung; Produktionssicherung 2026-09-12_0646 nur lesend; Messbasis-Paket im Austauschordner'),
    Befundlage('2.452', "⚠️⚠️⚠️ DIE TERMINMARKT-FAKTEN SIND EINGEFROREN - UND WERDEN ALS AKTUELL AUSGEGEBEN. Einziger Schreiber von `open_interest_snapshot` ist `hebel_screening.fetch_and_store_oi_snapshot`, aufgerufen NUR innerhalb von `run_hebel_screening`. Seit `hebel_screening.aktiv: false` (12.09., 2.379-schalter) schreibt ihn niemand: letzte Zeile 2026-09-12T03:28 auf allen vier Boersen (24 Symbole). `positionierung._reihe` liest die letzten 400 Zeilen OHNE Altersgrenze, und das Rueckblickfenster wird aus der ZEILENZAHL gerechnet (32 Zeilen = ,8 Stunden'), nicht aus der Zeit. Folge: Rolle BC (Faktenlage, `rollen_lauf.py:1533`) und Rolle G (`zweite_meinung.py:485`) bekommen fuer jeden Kryptowert Saetze wie ,in den letzten 8 Stunden praktisch unveraendert' aus Daten vom 12.09. ⚠️ Warum es niemand sah: die Datenfrische prueft die TABELLE als Ganzes (`MAX(fetched_at)`), einmal taeglich und mit der Grenze ZWEI TAGE - eine Mail kommt fruehestens nach ueber zwei Tagen Totalausfall und nie fuer einen einzelnen Wert (Richtigstellung 14.09.: zuerst hiess es hier ,meldet nur ins Log'). ⚠️ Die Stilllegungspruefung 2.404-leser fragte ,wer liest das noch' fuer `hebel_triggers`, nicht ,wer SCHREIBT das noch' fuer die Nebenprodukte des Jobs. ✔ NICHT betroffen: OI-Sperre (Stufe 12, `marktrang.oi_werte` live von Binance), Funding-Rang (live), die Finanzierungsrate in BC beim Hebel (`hole_finanzierung`, live)", 'abgeloest',
               'agent/positionierung.py:70; agent/krypto/hebel_screening.py:60-157,379; scheduler/background.py:3371; agent/datenfrische.py:171,317', '2.452-gebaut', 'behoben mit Schritt 54 (14.09.): eigener Sammeljob fuer alle Kryptowerte, Lesegrenze 2 h, Meldung ab 6 h', 'Code positionierung.py, hebel_screening.py, rollen_lauf.py, datenfrische.py, background.hebel_screening_job; Produktionssicherung 2026-09-12_0646 (open_interest_snapshot, signals, anlass_beobachtung); positionierung.lage/saetze an der Kopie nachgespielt (echte Funktion)'),
    Befundlage('2.452-alt', "⚠️⚠️⚠️ DERSELBE FEHLER BESTEHT BEI 13 WERTEN SCHON SEIT JULI - unabhaengig von Schritt 40. Der Schreiber laeuft nur fuer Werte mit `hebel_pruefung_erlaubt`; AVAX, APT, S, IMX, W, BRETT, BIO, PLUME, IO, MON, QNT, ASTER (letzte Zeile 18.07.) und KAS (22.07.) wurden danach nicht mehr erfasst, ihre Terminmarkt-Saetze stammen seither aus Juli. 📏 Alle 13 werden beurteilt (je 289 Anlassbeobachtungen 09.-12.09.); 154 gespeicherte Urteile 02.-12.09. tragen die Saetze in `facts_json` (103 NACHKAUFEN, 27 REDUZIEREN, 23 HALTEN, 1 VERKAUFEN), 195 Gegenpruefungen der Rolle G seit 17.08. Das Modell BEGRUENDET damit: ASTER NACHKAUFEN 11.09. (,extrem niedriges Sentiment der Konten auf der Kaufseite'), KAS HALTEN 07./09.09. (,Nachkauf derzeit nicht ratsam' - Kontenanteil im 96. Perzentil, Stand 22.07.). Nachgespielt: AVAX meldet ,1. Perzentil ... aussergewoehnlich wenige', KAS ,96. Perzentil ... aussergewoehnlich viele'", 'abgeloest',
               'signals facts_json/belege_json/zai_gegenpruefung_kurzbegruendung; open_interest_snapshot MAX(fetched_at) je Symbol', '2.452-gebaut', 'behoben mit Schritt 54 (14.09.): eigener Sammeljob fuer alle Kryptowerte, Lesegrenze 2 h, Meldung ab 6 h', 'Code positionierung.py, hebel_screening.py, rollen_lauf.py, datenfrische.py, background.hebel_screening_job; Produktionssicherung 2026-09-12_0646 (open_interest_snapshot, signals, anlass_beobachtung); positionierung.lage/saetze an der Kopie nachgespielt (echte Funktion)'),
    Befundlage('2.452-gebaut', "✔✔ SCHRITT 54 GEBAUT - DIE TERMINMARKT-DATEN SIND FRISCH ODER ES WIRD GESAGT (Nutzerentscheidungen 14.09.). (1) EIGENER JOB `terminmarkt_job` (15 min, eigener Lock) sammelt fuer ALLE Kryptowerte der Kette, unabhaengig von `hebel_screening.aktiv` und `hebel_pruefung_erlaubt`; das Screening schreibt nicht mehr. (2) `positionierung` liest NACH DER UHR: ist der juengste Wert aelter als 2 h, gibt es keine Zahl, sondern ,keine aktuelle Angabe - der letzte Stand ist X alt'; das 8-Stunden-Fenster ist der Stand von vor 8 h (Toleranz 30 min), nicht die 32. Zeile; der Vergleich fuer ,gewohnt/aussergewoehnlich' reicht 100 h zurueck statt 400 Zeilen. Fehlt der Vergleichsstand oder ist die Finanzierungsreihe zu kurz, steht ein Satz da statt Stille. (3) MELDUNG im Job der Rollen-Kette: 6 h ohne jede neue Zeile oder ein Wert 24 h ohne Zeile -> eine Mail je Ausfall, eigener Betreff, gezaehlt ab App-Start, keine Entwarnung; die alte Mail ,8 Fehlschlaege je Wert' ist ersetzt. 📏 Live gegen Kopie: 139 Zeilen, 37 von 43 Werten frisch, keine Schreibzugriffe auf die Standard-DB; KAS und AVAX wieder mit frischen Daten. 📏 ALT GEGEN NEU an 24 frischen Werten: OI-Aenderung und Fenster IDENTISCH; Perzentile weichen um wenige Punkte ab (381 statt 400 Vergleichswerte), an der 10/90-Grenze kippt die Einordnung in 3 von 96 Faellen (BNB Finanzierung 10->11, KAIA Divergenz 10->11, NEAR Divergenz 90->89). ⚠️ In den ersten 8 h nach dem Einspielen fehlt die OI-Aenderung (benannt), die Einordnung der Finanzierungsrate und des Kontenanteils bei den 13 Juli-Werten rund 7,5 h", 'gilt',
               'agent/terminmarkt_sammlung.py; scheduler/background.py (terminmarkt_job, _pruefe_terminmarkt_frische); agent/positionierung.py; database/db.py:lies_funding_reihe; pruefe_pakete.py TerminmarktDaten', '', '', 'Suite-Paket TerminmarktDaten (35 Pruefungen, mit Gegenprobe); Live-Durchlauf des Jobs gegen eine Kopie der Sicherung 12.09. (echte Boersen, 142 s); Vergleich alter/neuer Leser an 24 Werten; simuliere_kette auf der Kopie'),
    Befundlage('2.452-boerse', "○ OPEN INTEREST UND KONTENANTEIL LIEST `positionierung` NUR VON BINANCE - beim Live-Durchlauf 14.09. hatten AIOZ (nur Bybit) und FLOKI (nur OKX) Daten, bekommen aber ,keine Angabe: Open Interest'. FLOKI heisst bei Binance vermutlich `1000FLOKIUSDT` (Kontraktgroesse), der Abruf fragt `FLOKIUSDT`. Bestand seit dem 16.08., NICHT durch Schritt 54 entstanden. Zu klaeren: Symbolzuordnung je Boerse, oder OI aus der naechsten verfuegbaren Boerse", 'offen',
               "agent/positionierung.py:_zeitreihe (boerse='binance'); agent/krypto/hebel_screening.py:fetch_and_store_oi_snapshot", '', '', 'Suite-Paket TerminmarktDaten (35 Pruefungen, mit Gegenprobe); Live-Durchlauf des Jobs gegen eine Kopie der Sicherung 12.09. (echte Boersen, 142 s); Vergleich alter/neuer Leser an 24 Werten; simuliere_kette auf der Kopie'),
    Befundlage('2.452-anlass', "⚠️ DER TERMINMARKT STEHT NICHT IM ANLASS-FINGERABDRUCK - entgegen der Absicht von Umbauplan Schritt 5 (Kommentar `rollen_lauf.py:1510`: ,eine Groesse, die dort nicht steht, kann keine neue Frage ausloesen'). `AN.beobachte(fakten=bc_ein)` rechnet den Abdruck in Zeile 1298 sofort als Zeichenkette; `bc_ein['terminmarkt']` kommt erst in Zeile 1539 dazu. Eine Bewegung am Terminmarkt loest also keinen Anlass aus. Fuer 2.452 heisst das: das Einfrieren hat den Anlass NICHT verfaelscht - es hat ihn nie erreicht", 'offen',
               'agent/rollen_lauf.py:1296-1313,1531-1543; agent/anlass.py:206,272', '', '', 'Code positionierung.py, hebel_screening.py, rollen_lauf.py, datenfrische.py, background.hebel_screening_job; Produktionssicherung 2026-09-12_0646 (open_interest_snapshot, signals, anlass_beobachtung); positionierung.lage/saetze an der Kopie nachgespielt (echte Funktion)'),
    Befundlage('2.451', "📋 POSITIONSFAELLE SPOT UND HEBEL IM DETAIL GEPRUEFT (Nutzerauftrag 14.09.: *,pruefe im Detail alle Anwendungsfaelle, dass das System mit neuen, geaenderten, verkauften Positionen korrekt umgehen kann'*). Vollstaendig in `Basisinfos/Plan_Asset_Lebenszyklus_14_09.md`, Abschnitt Positionsfaelle. Die folgenreichen Punkte: 2.451-sofort, -absicherung, -verkauf, -bestaetigung, -phantom, -topf. ➤ Takte: Spot-Abgleich 30 min, Hebel-Abgleich und Kette 15 min, Kapital taeglich 06:30; NICHTS startet einen Lauf sofort", 'offen',
               'Basisinfos/Plan_Asset_Lebenszyklus_14_09.md', '', '', 'Code-Aufnahme der Positionspfade (Spot, Hebel), tragende Aussagen einzeln gegengelesen; Messungen an der Produktionssicherung 2026-09-12_0646 (anlass_beobachtung, signals, holdings)'),
    Befundlage('2.451-hebel', '📋 DIE KLEINEREN HEBEL-FAELLE GEGENGEPRUEFT. 7a TEILSCHLIESSUNG ALS VOLLSCHLIESSUNG: KEIN FEHLER - am echten HYPE-Fall (26.07.) verkaufte Bitpanda 7,70 Stueck zur Tilgung und die restlichen 3,79 im selben Moment; eine Vollschliessung in zwei Buchungen. Produktionstabelle: 188 Positionen, keine offen. ⚠️ Nachspielen mit dem Export 03.08. nicht deckungsgleich (4 statt 184 Schliessungen) - kein Befund daraus. 7b LIQUIDATION NACHTRAEGLICH: bewusst (API meldet keine; 1-%%-Gebuehr, 4 Faelle belegt), Warnung vorher am geschaetzten Preis. 7c SPOT UND HEBEL AUF DEMSELBEN WERT: bewusst Hebel-Vorrang (S6b) - die Verkaufsempfehlung uebergeht den Spot-Bestand; theoretisch, seit Paket B wieder moeglich. 7d HEBEL-ABGLEICH FAELLT AUS: bewusst nur Logwarnung (Vorfall 18.08.), ein laenger anhaltender Ausfall bleibt unbemerkt. ➤ NUTZERENTSCHEIDUNGEN 14.09.: 7d - Mail bei anhaltendem Ausfall mit aussagekraeftigem Betreff und Inhalt; 7c - ein Asset mit zwei Positionen wird sauber getrennt behandelt (Umbau, Gestaltung vor dem Bau abzustimmen). ✔ 7d GEBAUT 15.09. (2.455-hebelabgleich-gebaut) - offen bleibt 7c', 'offen',
               'importer/bitpanda_margin_positions.py:226-253; agent/rollen_lauf.py:1676; scheduler/background.py:3447', '', '', 'Code bitpanda_margin_positions.py, hebelfuehrung.py, rollen_lauf.py, background.py; Produktionstabelle hebel_positions (Sicherung 12.09.); Bitpanda-Export 03.08. (Notebook_Analysedaten), HYPE-Buchungen 26.07.'),
    Befundlage('2.451-sofort', "⚠️⚠️ EIN NEUER BESTAND WIRD NICHT SOFORT BEURTEILT - gegen die Nutzervorgabe 14.09. (*,sobald ein neuer Bestand vorhanden ist, muss die laufende Bewertung und gesamte Ablaufkette starten'*). Der Wert ueberspringt die Auswahl, aber Anlassstufe und Cooldown (Krypto 12 h, Akkumulation 48 h) gelten weiter; die Anlassbeobachtung wird VOR dem Cooldown geschrieben (`rollen_lauf.py:1294-1456`), die Aenderung ist beim naechsten Takt verbraucht. 📏 gehaltene Kryptowerte 09.-12.09. alle 12-20 h beurteilt, 27 %% der Beobachtungen ,unveraendert'. Ein Kauf AUSSERHALB der Watchlist wird gar nicht beurteilt (S2). ➤ NUTZERENTSCHEIDUNG 14.09.: eine Bestandsaenderung seit dem letzten Urteil (holdings.updated_at; Hebel eroeffnet/geschlossen) hebt Cooldown und Anlassstufe EINMAL auf - Urteil im naechsten Takt, spaetestens ~45 min; die Routinebremsen bleiben", 'offen',
               'agent/rollen_lauf.py:1294-1456; agent/anlass.py; agent/wiederholung.py', '', '', 'Code-Aufnahme der Positionspfade (Spot, Hebel), tragende Aussagen einzeln gegengelesen; Messungen an der Produktionssicherung 2026-09-12_0646 (anlass_beobachtung, signals, holdings)'),
    Befundlage('2.451-absicherung', "⚠️⚠️⚠️ EINE GEHALTENE ABSICHERUNG IST SEIT DREI WOCHEN OHNE URTEIL. 📏 DBPK (1.739 Stueck gehalten): letzte Rollen-Zeile 22.08.; seither passierte es die Anlassstufe neunmal, ein Urteil entstand nie. Folge von R2 (Schritt 33, 2.422): die Absicherung liefert keine Richtung, KAUFEN/NACHKAUFEN verlangen eine. 3QSS wird beurteilt (09.09.). Bisher als ,kann nur HALTEN sagen' beschrieben - die Wirkung ist schaerfer: gar kein Urteil. ➤ URSACHE IM NOTEBOOK-LOG BELEGT (31.08.): ,DBPK: NACHKAUFEN ohne Richtung - erlaubt (LONG, SHORT), bekommen None' - die verworfene Empfehlung schreibt KEINE Zeile, nur eine Warnung; 3QSS ebenso. Nebenbei: yfinance meldete am 02.09. ,DBPK.DE: possibly delisted'. ➤ NUTZERENTSCHEIDUNG 14.09.: Waechter ,gehalten, aber seit N Tagen nicht beurteilt' in der Sammelmail, samt Grund; R2 selbst bleibt in Schritt 33", 'offen',
               'signals DBPK; anlass_beobachtung DBPK; Befund 2.422', '', '', 'Code-Aufnahme der Positionspfade (Spot, Hebel), tragende Aussagen einzeln gegengelesen; Messungen an der Produktionssicherung 2026-09-12_0646 (anlass_beobachtung, signals, holdings)'),
    Befundlage('2.451-verkauf', "⚠️⚠️ NACH EINEM KOMPLETTVERKAUF EMPFIEHLT DIE AUSSTIEGSMAIL WEITER ,STOP NACHZIEHEN'. Sie listet offene SIGNALE ueber der Schwelle, nicht Bestaende (`backward_tracking.py:5386`, `background.py:604`); offene Signale eines verkauften Werts bleiben offen und werden nur am Preis aufgeloest. Umgekehrt stehen dort auch Empfehlungen, die nie ausgefuehrt wurden. ➤ PRAEZISIERT 14.09. (gemessen, Sicherung 12.09.): das Hauptproblem ist nicht der Verkauf, sondern die Einheit - 127 Zeilen fuer 23 Werte (18x QNT, 17x AVAX, 15x ETH), 125 aus der Rollen-Kette, 13 fuer nicht gehaltene Werte, 0 als umgesetzt markiert. `positionsfuehrung.py` beschreibt das Problem seit 15.08. und liess die Mail bewusst unberuehrt. ⚠️ Eigene Korrektur: SEI/BNB/VSN stehen auf Menge 0, sind aber vollstaendig GESTAKT, nicht verkauft. ➤ NUTZERENTSCHEIDUNG: Mail auf Positionen umstellen (je gehaltene Position eine Zeile aus positionsfuehrung; Hebel mit Stop, Spot ohne R; nicht gehaltene nur in der Messung)", 'offen',
               'agent/krypto/backward_tracking.py:5386; scheduler/background.py:562-660', '', '', 'Code-Aufnahme der Positionspfade (Spot, Hebel), tragende Aussagen einzeln gegengelesen; Messungen an der Produktionssicherung 2026-09-12_0646 (anlass_beobachtung, signals, holdings)'),
    Befundlage('2.451-bestaetigung', '⚠️ JEDER RUECKGANG EINES BITPANDA-GUTHABENS BESTAETIGT EIN OFFENES VERKAUFEN/REDUZIEREN AUTOMATISCH ALS UMGESETZT - ohne Pruefung, warum die Menge sank (Staking-Transfer, Umbuchung). `umgesetzt_menge` bekommt die RESTmenge, nicht die verkaufte (`bitpanda_sync.py:312-340`, 398). 📏 bisher EIN Fall (XNO REDUZIEREN 24.08., Menge 0,0). ➤ NUTZERENTSCHEIDUNG 14.09.: automatisch bleibt (manuell ist schwierig), praezisiert - nur bestaetigen, wenn der Rueckgang nicht durch mehr gestakte Stueck erklaert ist; gespeichert wird die VERKAUFTE Stueckzahl. Massgeblich ist immer die MENGE DES ASSETS (Wallet-Balance in Stueck), nicht Cash', 'offen',
               'importer/bitpanda_sync.py:312-340', '', '', 'Code-Aufnahme der Positionspfade (Spot, Hebel), tragende Aussagen einzeln gegengelesen; Messungen an der Produktionssicherung 2026-09-12_0646 (anlass_beobachtung, signals, holdings)'),
    Befundlage('2.451-phantom', "⚠️ FEHLT EIN WALLET IN DER BITPANDA-ANTWORT, BLEIBT DIE ALTE MENGE STEHEN - bewusst (,unbekannt ist nicht verkauft', P-10), aber nur im Ergebnisobjekt vermerkt, nicht gemeldet. Ein Phantombestand zaehlt weiter fuer Kapital, Kette und Fuehrung", 'offen',
               'importer/bitpanda_sync.py:344-349', '', '', 'Code-Aufnahme der Positionspfade (Spot, Hebel), tragende Aussagen einzeln gegengelesen; Messungen an der Produktionssicherung 2026-09-12_0646 (anlass_beobachtung, signals, holdings)'),
    Befundlage('2.451-topf', "○ ,IM TOPF FREI' IN DER MAIL ZEIGT FAST IMMER DEN VOLLEN TOPF. `belegt_eur` zaehlt nur Signale ohne Ergebnisstatus; das Backward-Tracking setzt ,offen', sobald sich der Buchgewinn aendert. 📏 1 Signal (500 EUR) belegt statt 239 offener (115.100 EUR). Der Aggregat-Deckel zaehlt ,offen' mit - beide widersprechen sich. Reine Anzeige, begrenzt keinen Betrag. ⚠️ Die offenen mitzuzaehlen waere FALSCH: 115.100 EUR aus meist nie ausgefuehrten, mehrfachen Empfehlungen. Richtig: aus Empfehlungen GEKAUFT und noch gehalten - dafuer fehlt die Verknuepfung Kauf <-> Empfehlung (der Abgleich bestaetigt nur Verkaeufe). ➤ NUTZERENTSCHEIDUNG 14.09.: jetzt kennzeichnen (Fuellstand nicht bestimmbar), spaeter richtig zaehlen ueber die Kaufverknuepfung", 'offen',
               'agent/toepfe.py:321; agent/krypto/backward_tracking.py:1308; agent/hebel_aggregat.py:67', '', '', 'Code-Aufnahme der Positionspfade (Spot, Hebel), tragende Aussagen einzeln gegengelesen; Messungen an der Produktionssicherung 2026-09-12_0646 (anlass_beobachtung, signals, holdings)'),
    Befundlage('2.450', '📋 SCHRITT 53 GEPRUEFT: DER LEBENSZYKLUS EINES ASSETS AM CODE AUFGENOMMEN - neu, faellt weg, aendert sich, gehalten ohne Watchlist. Vollstaendig mit Fundstellen und Vorschlag in `Basisinfos/Plan_Asset_Lebenszyklus_14_09.md`. ➤ Die tragenden Luecken: 2.450-cache, -neu, -weg, -aendert. ➤ Nichts gebaut - Planung, Entscheidungen beim Nutzer', 'offen',
               'Basisinfos/Plan_Asset_Lebenszyklus_14_09.md', '', '', 'Code am 14.09. (Explore-Aufnahme, tragende Aussagen gegengeprueft: config-Zwischenspeicher, Auto-Add, Ausstiegsfilter, Stummmeldung, fehlendes Entfernen, keine Datengrundlage); Messbasis-Dateien Desktop; Produktionssicherung 2026-09-12_0646'),
    Befundlage('2.450-cache', "⚠️⚠️ EINE GEPULLTE WATCHLIST WIRKT AM NOTEBOOK ERST NACH EINEM NEUSTART. `config.load_config()` liest `config.yaml` einmal und haelt sie (`config.py:86`); nur Schreibvorgaenge DESSELBEN Prozesses leeren den Speicher. Der Kommentar in `scheduler/background.py:170` (,liest config.yaml ohne Caching') ist falsch - er stimmt nur fuer Aenderungen ueber die GUI im selben Prozess. Folge: jede per git gelieferte Aenderung an Watchlist oder Schwellen wirkt still nicht, bis jemand neu startet. ➤ EINORDNUNG 14.09.: der dokumentierte Ablauf ist ,Pull + Neustart', und der Nutzer startet nach jedem Pull neu - klein. NUTZERENTSCHEIDUNG: Kommentare berichtigen + Hinweis ,Neustart ausstehend', KEIN automatisches Neueinlesen (Einstellungen wuerden mitten im Lauf wechseln, beim Import gelesene Werte zoegen nicht mit). ⚠️ Die Asset-Schalter (Hebel-Pruefung, DCA, Bitpanda-Override) stehen in der Datenbank DES GERAETS, werden je Lauf frisch gelesen und NICHT synchronisiert - ein Haekchen am Desktop aendert am Notebook nichts", 'offen',
               'config.py:86; scheduler/background.py:170', '', '', 'Code am 14.09. (Explore-Aufnahme, tragende Aussagen gegengeprueft: config-Zwischenspeicher, Auto-Add, Ausstiegsfilter, Stummmeldung, fehlendes Entfernen, keine Datengrundlage); Messbasis-Dateien Desktop; Produktionssicherung 2026-09-12_0646'),
    Befundlage('2.450-neu', "⚠️⚠️ EIN NEUES ASSET WIRD NICHT VON SELBST BEWERTBAR. Automatisch laden Preise und Kerzen; Funding-, Umlaufmengen-, Terminmarkt-Historie und Messreihen nur von Hand (Messreihen nur am Desktop). Die Kette braucht >250 Kerzen (Auswahl), 310 (Faktenblock) und einen Rang in einer Messbasis - sonst ,keine Datengrundlage' (`rollen_lauf.py:2461`), und das steht nur im Log. GEMESSEN 14.09.: 7 von 43 Watchlist-Krypto in KEINER der beiden tragenden Messbasen (FLOKI, AIOZ, SUPRA, CAT, CANTON, VSN, XNO); Funding 36/43, Turnover 7/43 (Messbasis-Datei am Desktop). ⚠️ Die Messbasis zu erweitern ist eine MESSfrage (R-R11), keine reine Datenfrage. ➤ Wege hinein: GUI-Dialog, Marktscan, und AUTOMATISCH alle 15 Minuten fuer offene Hebel-Positionen auf unbekannten Symbolen - auch bei abgeschaltetem Screening (`background.py:3405`)", 'offen',
               'agent/rollen_lauf.py:2461; agent/marktrang.py MESSBASIS; scheduler/background.py:3405', '', '', 'Code am 14.09. (Explore-Aufnahme, tragende Aussagen gegengeprueft: config-Zwischenspeicher, Auto-Add, Ausstiegsfilter, Stummmeldung, fehlendes Entfernen, keine Datengrundlage); Messbasis-Dateien Desktop; Produktionssicherung 2026-09-12_0646'),
    Befundlage('2.450-weg', '⚠️⚠️ EIN ASSET ZU ENTFERNEN IST NICHT VORGESEHEN - und ein entfernter, noch gehaltener Wert verliert STILL seine Fuehrung. Es gibt keine Entfernen-Funktion (GUI, config.py, Uebersichtsseite). Wer config.yaml von Hand kuerzt: Bestand eingefroren (Bitpanda-Sync ueberspringt ihn), keine Preise, KEINE Ausstiegs- und Liquidationsmail (Positions- und Hebelfuehrung filtern auf die Laufsymbole, `rollen_lauf.py:939/966`), und eine offene Hebel-Position holt das Symbol nach 15 Minuten zurueck. Heute NICHT eingetreten: Sicherung 12.09. - 29 Bestaende, alle in der Watchlist. Die Stummmeldung (2.442) und `pruefe_neuaufnahme` ueberspringen Bestaende ausserhalb der Watchlist', 'offen',
               'agent/rollen_lauf.py:939,966; importer/bitpanda_sync.py:256; agent/verkaufsrechnung.py:381', '', '', 'Code am 14.09. (Explore-Aufnahme, tragende Aussagen gegengeprueft: config-Zwischenspeicher, Auto-Add, Ausstiegsfilter, Stummmeldung, fehlendes Entfernen, keine Datengrundlage); Messbasis-Dateien Desktop; Produktionssicherung 2026-09-12_0646'),
    Befundlage('2.450-aendert', '⚠️ EIN ASSET, DAS SICH AENDERT, HAT IM BETRIEB KEINEN SCHUTZ. Token-Umstellung/Redenominierung: der Sprungfilter steht nur in Messskripten (`messe_zielregel.py:72`). Umbenennung nur ueber feste Tabellen; der Bearbeiten-Dialog kann Symbol, Klasse, Cash-Kennzeichen nicht aendern. Eine geaenderte CoinGecko-ID laesst die alte Preishistorie verwaisen. Gleiches Symbol in zwei Klassen: Produktions-Kerzentabelle ohne Klassenschluessel (D3). Bitpanda-Delisting: eine fehlgeschlagene Abfrage gilt als handelbar', 'offen',
               'messe_zielregel.py:72; ui/app.py:1780; database/db.py:71,98; agent/asset_schalter.py:178', '', '', 'Code am 14.09. (Explore-Aufnahme, tragende Aussagen gegengeprueft: config-Zwischenspeicher, Auto-Add, Ausstiegsfilter, Stummmeldung, fehlendes Entfernen, keine Datengrundlage); Messbasis-Dateien Desktop; Produktionssicherung 2026-09-12_0646'),
    Befundlage('2.449', '⚠️⚠️⚠️ DIE PRUEFSUITE SCHRIEB IN DIE STANDARD-DATENBANK - AM NOTEBOOK DIE PRODUKTION. BEHOBEN (Nutzerentscheidung 14.09.: Weg A, gezielte Reparatur statt zentraler Umleitung). ➤ GEMESSEN, alle 77 Pakete einzeln: ZWEI schrieben. PAKET 15 buchte ueber `track_api_health` einen GESTELLTEN Gemini-Fehler ,HTTP 400 {"e": 1}\' in `api_health_status` - am Notebook stand danach die Anbieter-Ampel der Uebersichtsseite auf Rot, ohne Stoerung (genau die Verwechslung, die am 09.08. zwei Tage Diagnose kostete); dazu echte coinmetrics-/finra-Zeitstempel des Probelaufs. PAKET 6 fuehrte `signal_abbildung.migriere()` auf der ECHTEN Datenbank aus und legte ein Test-Lagebild an - heute folgenlos (die Kette migriert vor jedem Lauf selbst, `rollen_lauf.py:510`), aber eine neue Spalte haette die SUITE der Produktion angelegt, vor dem Start der App. ➤ REPARIERT: Paket 6 prueft Migration, Idempotenz und Lagebild an einer Speicherkopie des echten Schemas (nur lesend geholt); Paket 15 laeuft in `_ohne_statusbuchung` - fuer seine Dauer zeigt `api_health.db` auf einen Ersatz mit Speicher-Datenbank, alle anderen Wege bleiben. Pruefzahlen unveraendert (6: 17, 15: 535) - es wird dasselbe geprueft. ➤ BEWACHT: `_standard_db_waechter_an` in JEDEM Suitelauf (Zeile ,Standard-DB\'), Selbsttest im Paket `StandardDB`. ➤ NACHGEWIESEN: Suite 2.490, nur die zwei bekannten Luecken rot; Tabellenvergleich der Desktop-DB ueber den ganzen Lauf ohne jede Aenderung. ➤ WAS NICHT FOLGT: keine Aenderung an App, Kette, Mail, Schema oder Scheduler - nur `pruefe_pakete.py`', 'gilt',
               'pruefe_pakete.py: paket_6, _ohne_statusbuchung, _standard_db_waechter_an, paket_standard_db', '', '', 'Desktop 14.09.: alle 77 Pakete einzeln mit Tabellen-Fingerabdruck der Standard-DB davor/danach; Authorizer-Waechter gegen den Stand vor der Reparatur (meldet Pakete 6 und 15) und danach (meldet nichts); Tabellenvergleich der Desktop-DB ueber einen vollen Suitelauf'),
    Befundlage('2.449-schutz', "⚠️⚠️ EIN SCHUTZ, DER DASTEHT UND NICHT GREIFT. In Paket 15 stand seit Wochen der Kommentar ,NICHT IN DIE PRODUKTIVDATEI SCHREIBEN' und darunter `_AH.track_api_health = ...` samt Zuruecksetzen. Er war NIE wirksam: die Gemini-Methoden sind beim IMPORT dekoriert - wer danach die Dekorator-FABRIK ersetzt, aendert an ihnen nichts. Wirksam ist nur, was der Dekorator ZUR LAUFZEIT nachschlaegt (`api_health.db`). ➤ REGEL: ein Schutz gegen einen Seiteneffekt wird am Seiteneffekt nachgewiesen (Waechter meldet ihn vorher, meldet ihn nachher nicht), nicht am Vorhandensein des Schutzcodes. Dieselbe Klasse wie ,Kontrollen muessen selbst geprueft werden' (Methodik) und die Oberflaechensperre aus Schritt 32, die die leere Code-Vorgabe las", 'gilt',
               'pruefe_pakete.py paket_15 (alter Stand); Memory feedback_kontrollen_muessen_selbst_geprueft_werden', '', '', 'Desktop 14.09.: alle 77 Pakete einzeln mit Tabellen-Fingerabdruck der Standard-DB davor/danach; Authorizer-Waechter gegen den Stand vor der Reparatur (meldet Pakete 6 und 15) und danach (meldet nichts); Tabellenvergleich der Desktop-DB ueber einen vollen Suitelauf'),
    Befundlage('2.449-notebook', "➤ WARUM NICHTS AM NOTEBOOK BRICHT - einzeln geprueft. (1) Geaendert ist ausschliesslich `pruefe_pakete.py`; App, Scheduler, Kette und Schema sind unberuehrt. (2) Der Waechter BLOCKIERT NICHTS (Authorizer gibt immer SQLITE_OK) - er meldet nur. (3) Er sieht NUR Verbindungen, die DIESER Prozess beschreibbar auf die Standard-Datei oeffnet; `mode=ro`, `:memory:` und Kopien nicht. (4) Die Produktion schreibt am Notebook waehrend des Suitelaufs selbst - das loest KEINEN Fehlalarm aus (Selbsttest mit zweitem Prozess). Deshalb bewusst kein Datei-Fingerabdruck vorher/nachher. (5) Paket 6 liest das Schema der Produktions-DB nur lesend (WAL erlaubt das neben dem Scheduler). (6) Paket 15 kopierte die DB schon vorher in den Speicher - daran aendert sich nichts. ➤ ERWARTUNG FUER DEN ERSTEN NOTEBOOK-LAUF: die Zeile ,Standard-DB' ist gruen. Wird sie ROT, schreibt ein Paket, das am Desktop nicht schreibt (datenabhaengiger Zweig oder am Desktop uebersprungen) - dann nennt die Zeile Paket, Aktion, Tabelle und Aufrufstelle, und DAS ist der Fund, nicht der Waechter. ➤ Greift am Notebook erst mit dem naechsten Gesamtpaket", 'gilt',
               'pruefe_pakete.py; Paket StandardDB; Memory feedback_desktop_kein_produktivstart', '', '', 'Desktop 14.09.: alle 77 Pakete einzeln mit Tabellen-Fingerabdruck der Standard-DB davor/danach; Authorizer-Waechter gegen den Stand vor der Reparatur (meldet Pakete 6 und 15) und danach (meldet nichts); Tabellenvergleich der Desktop-DB ueber einen vollen Suitelauf'),
    Befundlage('2.448-umsetzung', "✔✔ SCHRITT 32 UMGESETZT (Nutzerentscheidungen 14.09.: Knoepfe stilllegen mit Hinweis · Detailansicht in der neuen Gliederung AUS DB-FELDERN · Anzeigen der alten Kette kennzeichnen). ➤ KNOEPFE: ,Signal berechnen', ,Faellige Signale jetzt berechnen', ,Jetzt analysieren' (Hebel), ,P-5-Begruendung generieren' fragen vor jedem Start `rollen_job.alte_analyse_hinweis` - dieselbe Regel wie `bedient_neue_kette`, keine feste Sperre: faellt eine Klasse aus `aktiv_fuer`, ist ihr Knopf wieder frei. ,Jetzt scannen' bleibt frei (kein Modellaufruf, derselbe Scan wie der laufende Job). ➤ ANSICHT: `agent/signal_ansicht.py` - dieselben Abschnittstitel wie die Mail, nur gespeicherte Felder, erste Zeile nennt was NICHT gespeichert ist (Trefferquote, Gebuehren, Faktenblock, Marktvergleich, Termine); Stopvorzeichen nach Richtung, Nein-Buchungen benannt, Gegenpruefung als ,kein Einwand/EINWAND', Hebelzahlen ohne Hebelgeschaeft als ,Spot, vor Paket B'. Genutzt in Signale, Hebel und Portfolio/,Letzte Bewertung' (die bisher NUR Zeilen vom 14.08. zeigte). Richtungszeile und Belegmarker stehen jetzt einmal in `signal_mail` und werden geholt. ➤ KENNZEICHNUNG: Regime-Reiter (Stand und Override ,wirkt nur auf die ALTE Kette' - am Code geprueft, die Rollen-Kette liest beides nicht), Regime-Karte der Uebersichtsseite, Signal-Verlauf (Spalte ,Kette / Konfidenz'), Hebel-Verlauf (,nur alte Kette'), Watchlist-Tooltip; Marktscan-Spalte ,Potential' heisst ,Reifegrad' (sie ist `score_momentum`, nicht das Potential der Bewertung); Spaltenhilfe ,Hebel-Pruefung' beschreibt die Wirkung in der Rollen-Kette statt des stillgelegten Screenings. ⚠️⚠️ EIN FEHLER DER ERSTEN FASSUNG, gefunden von der Oberflaechenprobe: die Regel reichte `config=None` durch, `aktiv_fuer(None)` ist die LEERE Code-Vorgabe - jeder Knopf blieb frei, ein Klick startete die alte Pipeline (auf der Kopie, mit Stellvertreter-Client, ohne Folgen). Behoben, bewacht. ➤ NACHGEWIESEN: Oberflaechenprobe 17/17, Desktop-DB hashgleich; Paket GuiKette 21 Pruefungen, gegen die GUI-Dateien vor Schritt 32 schlagen 10 an; Suite 2.483, nur die zwei bekannten Luecken. ⚠️ WAS NICHT FOLGT: die Ansicht ist NICHT die Mail - Gleichlauf per Bau gibt es nur mit gespeichertem Mailtext, und der wurde bewusst nicht gewaehlt (2.448-mail)", 'gilt',
               'agent/signal_ansicht.py; scheduler/rollen_job.py; ui/*; remote/status.py; Paket GuiKette', '', '', 's32_gui_probe: Reiter einzeln gegen eine Kopie der Produktionssicherung 2026-09-12_0646, DB_PATH umgebogen, Stellvertreter-Clients, kein main.py; Paket GuiKette; Gegenprobe gegen die GUI-Dateien vor Schritt 32'),
    Befundlage('2.448-rest', "➤ WAS NACH SCHRITT 32 OFFEN BLEIBT - bewusst, mit Grund. (1) E1, DIE GROSSE PLANUNG (Nutzervorgabe 07.09.): GUI, Funktionalitaeten und Anwendungsfaelle - neue Assets, Assets fallen weg oder aendern sich. Schritt 32 hat die Oberflaeche an die laufende Kette angeglichen, er hat sie nicht neu geplant. (2) UEBERSICHTSSEITE: ,Offene Signale' und ,Ausstiegsempfehlungen' lesen beide Ketten ohne Trennung. (3) HEBEL-VERLAUF liest nur `hebel_signals` (Titel gekennzeichnet) - ein Verlauf der Rollen-Hebelzeilen fehlt. (4) DIE ANSICHT HAT LUECKEN, die sie selbst nennt: Trefferquote, Gebuehren, Marktvergleich, Termine. Schliessen liessen sie sich nur ueber den gespeicherten Mailtext (2.448-mail) - Nutzerentscheidung 14.09. dagegen, jederzeit neu entscheidbar. (5) Die alten Pipelines und ihre GUI-Wege bleiben im Code (Rueckfallweg, `zweite_meinung`-Kopf) - stillgelegt, nicht geloescht", 'offen',
               'Schritt 32; Gesamtplan 28.08. E1; remote/status.py; ui/hebel_view.py', '', '', 's32_gui_probe: Reiter einzeln gegen eine Kopie der Produktionssicherung 2026-09-12_0646, DB_PATH umgebogen, Stellvertreter-Clients, kein main.py; Paket GuiKette; Gegenprobe gegen die GUI-Dateien vor Schritt 32'),
    Befundlage('2.448', "⚠️⚠️⚠️ SCHRITT 32 GEPRUEFT: DIE OBERFLAECHE IST NOCH DIE DER ALTEN KETTE. Alle acht Reiter, die Menues und die Uebersichtsseite am Code durchgesehen, tragende Aussagen einzeln gegengeprueft. ➤ KEIN REITER zeigt die neue Bewertung: Trefferquote/Potential, Belege, Widerlegungsbedingung, Strategie, Topf, Verlust am Stop, Liquidation der neuen Kette - nirgends. Die Bewertungsschwelle steht NUR in der Parametertabelle (Regime-Reiter und Uebersichtsseite). ➤ DIE DATENLAGE ERKLAERT DIE MISCHUNG: seit dem 15.08. schreibt die alte Kette KEINE Zeile mehr (Sicherung 12.09.: 0), die neue `quelle_kette='rollen'` rund 800 in 12 Tagen. Wo die GUI die JUENGSTE Zeile nimmt (`db.get_latest_signal`), zeigt sie eine neue Zeile in der alten Gliederung - mit leeren Feldern (Konfidenz, Top-5-Gruende, Langbegruendung, Forecast, Halte-Kriterium, Risikofaktoren: bei 2.357 neuen Zeilen 0x gefuellt). Wo sie `groq_raw_response IS NOT NULL` filtert (`get_latest_real_signal_per_symbol` -> Portfolio ,Letzte Bewertung'), sieht sie NUR alte Zeilen, Stand 14.08. Einzelheiten 2.448-knoepfe, -reiter, -mail, -uebersicht", 'gilt',
               'ui/*.py; remote/status.py; database/db.py 2838-2881', '', '', 'Code ui/*.py, remote/status.py, database/db.py (Stand 14.09.); Datenlage an der Produktionssicherung 2026-09-12_0646'),
    Befundlage('2.448-knoepfe', "⚠️⚠️⚠️ JEDER ANALYSEKNOPF STARTET DIE ALTE PIPELINE. Signale-Reiter: ,Signal berechnen' -> `agent.krypto.pipeline.generate_signal` bzw. die Aktien-/Rohstoff-/Hedge-/Themen-ETF-Pipelines; ,Faellige Signale jetzt berechnen' -> `signal_batch.run_signal_batch`. Hebel-Reiter: ,Jetzt analysieren' -> `hebel_pipeline.generate_hebel_signal`. Marktscan: ,Jetzt scannen' und ,P-5-Begruendung generieren' (LLM, alte Zaehler). Kein Knopf und kein Menue startet `rollen_lauf`. ➤ FOLGE, WENN JEMAND KLICKT: ein Signal der ALTEN Kette entsteht in der Produktions-DB (`insert_signal`, `quelle_kette` leer), mit echtem Modellaufruf aus dem geteilten Kontingent - genau die Populationsmischung, die am 05.08. einen Tag Ursachensuche kostete. Seit 15.08. nicht passiert (0 alte Zeilen). Am Notebook laeuft die GUI mit der Produktion - dort ist das scharf", 'abgeloest',
               'ui/signals_view.py 172-185, 719-830; ui/hebel_view.py 192, 846-863; ui/marktscan_view.py 177-179', '2.448-umsetzung', 'Alle vier Analyseknoepfe fragen vor dem Start die Kettenregel; Oberflaechenprobe und Paket GuiKette belegen es.', 'Code ui/*.py, remote/status.py, database/db.py (Stand 14.09.); Datenlage an der Produktionssicherung 2026-09-12_0646'),
    Befundlage('2.448-reiter', "➤ JE REITER (Kurzfassung). WATCHLIST: Tooltip ,Letztes Signal ... Konfidenz' (immer ,-'), Spaltenhilfe ,hebel_pruefung' beschreibt das stillgelegte 15-Min-Screening. PORTFOLIO/LETZTE BEWERTUNG: nur alte Kette, ,x %% Konfidenz', Langbegruendung. SIGNALE: Dreiteilung ,1. MATHEMATISCH BERECHNET / 2. LLM-BEWERTUNG (Konfidenz) / 3. KONKLUSION', Top 5 Gruende, Forecast, Halte-Kriterium, Verlauf mit Spalte Konfidenz. HEBEL: dieselbe Dreiteilung, Meta ,Konfidenz · Trigger', Verlauf liest NUR `hebel_signals` (letzte Zeile 10.08.); zeigt fuer neue Zeilen Richtung und Hebel, aber nicht `liquidation_etwa_eur`; die Zeilen unter 2x bleiben Altbestand (2.446-gui). REGIME: liest `signals.regime` - die neue Kette setzt es nie, der Reiter steht auf dem 14.08.; ,Mindestkonfidenz'. MARKTSCAN: NAMENSGLEICHHEIT - die Spalte ,Potential' ist `score_momentum`, nicht das Potential der Bewertung. SCREENER, SCHWERPUNKTE: keiner Kette zugeordnet, nichts Falsches", 'abgeloest',
               'Bestandsaufnahme 14.09. je Reiter', '2.448-umsetzung, 2.448-rest', 'Signale, Hebel, Letzte Bewertung zeigen die neue Gliederung; Regime, Verlaeufe, Watchlist, Marktscan gekennzeichnet. Was bleibt, steht in 2.448-rest.', 'Code ui/*.py, remote/status.py, database/db.py (Stand 14.09.); Datenlage an der Produktionssicherung 2026-09-12_0646'),
    Befundlage('2.448-mail', "➤ WARUM ,GUI UND MAIL DUERFEN NICHT AUSEINANDERLAUFEN' (Nutzervorgabe 12.09.) HEUTE NICHT HERSTELLBAR IST: die Mail entsteht beim Versand aus Rechnung, Faktenblock, Marktraengen, Terminen, Modellantworten und Gegenpruefung - und wird NIRGENDS gespeichert (2.446). Die GUI kann sie nicht nachbauen: ein Teil der Eingaben (Marktraenge, Termine, zweite Meinung, Lage zum Zeitpunkt) liegt spaeter nicht mehr vor, und ein zweiter Bauweg waere die Kopierfalle. ➤ DER EINZIGE WEG ZUM GLEICHLAUF IST, DEN MAILTEXT MIT DEM SIGNAL ZU SCHREIBEN - Aufwand klein (2-25 versandfaehige Einstiege je Tag, rund 12 KB je Mail), aber eine SCHEMAAENDERUNG und damit ein Notebook-Gesamtpaket. NUTZERENTSCHEIDUNG", 'gilt',
               'agent/signal_mail.py; agent/rollen_lauf.py 2938; Befund 2.446', '', '', 'Code ui/*.py, remote/status.py, database/db.py (Stand 14.09.); Datenlage an der Produktionssicherung 2026-09-12_0646'),
    Befundlage('2.448-uebersicht', '➤ UEBERSICHTSSEITE (`remote/status.py`): NEUE Kette - `_get_rollen_budget` (Toepfe, Urteile heute) und die Parametertabelle mit der Bewertungsschwelle. NUR ALTE Kette - `_get_budget_heute` (zaehlt `groq_raw_response`), `_get_regime_status` (steht auf 14.08.), `_get_provider_sendezaehler`, die Halten-Performance nach `top_grund_1_kategorie`, Marktscan-Karten. GEMISCHT ohne Kettentrennung - offene Signale und Ausstiegsempfehlungen. Definiert, aber nicht ausgeliefert: Konfidenz-Kalibrierung u.a.; `remote/server.py` traegt noch das JS der Konfidenzkarte', 'abgeloest',
               'remote/status.py 420-449, 907-1176', '2.448-umsetzung, 2.448-rest', 'Regime-Karte gekennzeichnet; die Budgetkarte trennte die Ketten schon; Anbieter- und Halten-Karten werden gesendet, aber nicht angezeigt. Die gemischten Karten stehen in 2.448-rest.', 'Code ui/*.py, remote/status.py, database/db.py (Stand 14.09.); Datenlage an der Produktionssicherung 2026-09-12_0646'),
    Befundlage('2.447', '✔✔ SCHRITT 31 UMGESETZT - DIE MAIL IST GESTRAFFT, UND DREI SHORT-FALSCHAUSSAGEN SIND BEHOBEN. Gemessen am Pruefstand, derselbe Trade vorher und nachher: Hauptteil (bis zum Anhang) 126 -> 111 Zeilen, 11.014 -> 8.438 Zeichen (-23 %%). Nichts gestrichen, was eine Tatsache ist - Erklaerungen und Beitragsbeschreibungen stehen im Anhang (Regel 3 des Mailvorschlags). ➤ GESTRICHEN sind nur Bewertungen ohne Beleg (2.447-etiketten) und eine doppelte, beim SHORT falsche Zeile (2.447-short). ✔ Paket `Mailstraffung`, 20 Pruefungen; gegen die vier vorher eingecheckten Module (trefferbilanz, trichter, gesamtbild, faktenblock) schlagen 7 an, die uebrigen belegt der Vorher-Nachher-Vergleich am Pruefstand. Suite 2.460 Pruefungen, nur die zwei bekannten Neuaufnahme-Luecken rot', 'gilt',
               'Schritt 31; pruefstand_hebelmail.py; pruefe_pakete --paket Mailstraffung', '', '', 'pruefstand_hebelmail.py: echte Kette im Trockenlauf auf einer Kopie der Produktionssicherung 2026-09-12_0646, echte config.yaml, SOL Hebel LONG und SHORT, vorher und nachher; Modellantworten und Marktraenge gestellt'),
    Befundlage('2.447-schalter', "✔✔ NACHPRUEFUNG 14.09. (Nutzerauftrag: *,pruefe, dass bei long und short sowie LONG ONLY nichts gebrochen ist'*): DER RICHTUNGSSCHALTER IST UNBERUEHRT UND WIRKT. ➤ AM CODE: keine Aenderung aus Schritt 41 oder 31 liegt in `asset_schalter.mail_richtung_erlaubt`, am Versand in `rollen_lauf` (beide Versandstellen mit `_mail_erlaubt`), in `scheduler/background` (alter Weg), `config.py`, `ui/app.py`, `ui/hebel_view.py` (GUI-Filter ,handelbar') oder `config.yaml` (`hebel_richtung_modus: nur_long`, Standard). Die geaenderten Funktionen (`trefferbilanz.kosten_r_aus_stop`/`satz`, `trichter`, `gesamtbild`, `faktenblock`, `entscheidungsrechnung.saetze`, `signal_mail`) liest NUR der Mailbau der Rollen-Kette - kein Gate, kein Schreibpfad, keine Bewertung (`bewertung` aus `TB.bewerte` geht ausschliesslich in `TB.satz`). ➤ AM LAUF (scharf, Versand abgefangen): nur_long LONG versendet · nur_long SHORT NICHT versendet (`nicht_versendet=nur_long`) · beide LONG versendet · beide SHORT versendet - in allen vier Faellen wird das Signal geschrieben, die Messung bleibt unberuehrt (Vorgabe 05.08.). Die LONG-Mail ist in beiden Stellungen textgleich. ➤ WAS DARAUS FUER DIE SHORT-FUNDE FOLGT: sie waren nur in der Stellung ,beide' versandwirksam; im Standard hat keiner eine Mail erreicht. Behoben bleiben sie trotzdem - der Schalter ist eine Nutzereinstellung und darf umgestellt werden. ➤ NEBENBEFUNDE, KEIN BRUCH: (1) der TROCKENLAUF kehrt VOR dem Schalter zurueck - `pruefstand_hebelmail.baue()` zeigt deshalb auch bei nur_long eine SHORT-Mail; daher `schalterprobe()`. (2) Die Kette notiert den Abruf der freien CoinMetrics-Quelle in `api_health_status` der STANDARD-DB des Geraets, auch wenn sie auf einer Kopie laeuft (gemessen: einzige geaenderte Tabelle). ✖ KORRIGIERT 14.09.: das ist NICHT harmlos - nach der Regel aus dem Vorfall 21.07. darf kein Pruefskript die Standard-DB beschreiben; `pruefstand_hebelmail.baue` biegt `DB_PATH` seitdem auf eine Wegwerfkopie um (Desktop-DB vorher/nachher hashgleich). Die SUITE selbst schreibt ebenfalls dorthin (api_health_status, lagebilder-Zaehler) - ERLEDIGT am selben Tag, Befund 2.449. (3) Fehlt der Schluessel in config.yaml, gilt im Code ,beide' (fail-open, seit 05.08. so gewollt). (4) Eine Richtung aus der Geometrie statt aus dem Urteil (Rueckfall im Mailbetreff) kann bei KAUFEN/NACHKAUFEN nicht vorkommen: `empfehlung_vertrag` lehnt diese Aktionen ohne Richtung ab", 'gilt',
               'agent/asset_schalter.py; agent/rollen_lauf.py; agent/empfehlung_vertrag.py; pruefstand_hebelmail.py schalterprobe; Entscheidungslog 05.08.', '', '', 'pruefstand_hebelmail.py --schalter: Kette SCHARF mit gestelltem Modell-Client, zai_client=None und abgefangenem Versand, auf einer Kopie der Produktionssicherung 2026-09-12_0646; SOL LONG und SHORT, hebel_richtung_modus nur_long und beide'),
    Befundlage('2.447-short', "⚠️⚠️⚠️ DREI WEITERE SHORT-FALSCHAUSSAGEN - gefunden, weil LONG und SHORT desselben Trades nebeneinander lagen (Stop 11,2 %%, Ziel 22 %% entfernt). (1) ANHANG B: ohne Kosten, ,noetig 33 von hundert - Traegt sich' - die LONG-Mail sagte ,53 - Traegt sich NICHT', der Kopf derselben SHORT-Mail ,Bitpanda noetig 53,0 %% - ZU WENIG'. Ursache: `trefferbilanz.kosten_r_aus_stop` und `satz` verlangten `einstieg > stop`. (2) TRICHTER: die Zielzeile fehlte, weil `ziel_relativ = (ziel - einstieg)/einstieg` beim SHORT negativ ist; der Kopf zaehlte dadurch ,1 dafuer, 1 dagegen' statt ,2 dagegen'. (3) MARKEN: Marken UNTER dem Kurs hiessen ,+1,0 Schwankungsbreiten'. ➤ Dieselbe Fehlerklasse wie 2.446-richtung: ein Vorzeichen, das nur LONG kennt. ➤ WIRKUNG: nur Mailtext - `kosten_r` liest ausser Anhang B niemand (die Bewertung rechnet gebuehrenfrei ueber `potential`), der Trichter sperrt nichts. EINGETRETEN: nein, seit 22.08. kein SHORT-Signal - und mit der Standardeinstellung `nur_long` waere keine dieser Mails versendet worden (2.447-schalter); betroffen war nur die Stellung ,beide'. ✔ behoben und bewacht", 'gilt',
               'agent/trefferbilanz.py; agent/entscheidungsrechnung.py; Paket Mailstraffung', '', '', 'pruefstand_hebelmail.py: echte Kette im Trockenlauf auf einer Kopie der Produktionssicherung 2026-09-12_0646, echte config.yaml, SOL Hebel LONG und SHORT, vorher und nachher; Modellantworten und Marktraenge gestellt'),
    Befundlage('2.447-etiketten', "✔ NUTZERENTSCHEIDUNG UMGESETZT (13.09.: ,ja streichen'). Der Faktenblock zeigt Schwankungsbreite, Abstand zum 60-Tage-Hoch und Volumen als WERT mit Beschreibung - ohne GUENSTIG/MITTEL/UNGUENSTIG und ohne ,ueber alle Einstiege gemessen: 29,5 %% gegen 17,8 %%'. Der Luecken-Satz sagt nicht mehr ,ein Punkt weniger steht hinter dieser Empfehlung' - die Werte tragen sie nicht. ➤ `KERN` und `_urteil()` bleiben als Rueckweg: traegt eine Familie spaeter nach Standard, kommt ihr Etikett mit dem NEUEN Beleg zurueck. ➤ NEBENBEI KORRIGIERT: ,Hoch der letzten drei Monate' - das Fenster sind 60 Tage. ➤ WAS NICHT FOLGT: Signal, Hebel und Bewertung aendern sich nicht; die Etiketten gingen in keine Rechnung und wurden vom Kopf nicht gezaehlt. Die Perzentile rechnet `werte_aus_reihe` weiter - die Trefferbilanz (Anhang B) braucht sie", 'gilt',
               'agent/faktenblock.py; Paket 12; Paket Mailstraffung', '', '', 'pruefstand_hebelmail.py: echte Kette im Trockenlauf auf einer Kopie der Produktionssicherung 2026-09-12_0646, echte config.yaml, SOL Hebel LONG und SHORT, vorher und nachher; Modellantworten und Marktraenge gestellt'),
    Befundlage('2.447-straffung', "✔ REDUNDANZ UND LESBARKEIT. (a) ,Auf einen Blick' beginnt mit ,Empfehlung KAUFEN - Urteil des Modells (Abschnitt 5)' - sie stand nur im Betreff und in Zeile 115. (b) ,Was dagegen spricht' nennt die TATSACHE (,Ihr Ziel liegt 22,3 %% entfernt - JENSEITS der ueblichen Bewegung von 20 Tagen'), nicht den halben Bewertungssatz, der unten woertlich wiederkam. (c) ANHANG D: die Beschreibung jedes eingerechneten Beitrags - beim Turnover-Rang 480 Zeichen samt Audit-Notiz - stand zwischen den Zeilen 33,3 + 0,8 + 3,1 = 37,3. (d) ANHANG E ,Lesehilfen': Markenerklaerung, Trichtererklaerung, ,Nicht zu verwechseln', Lebendigkeit ,Zu lesen' (stand zweimal), Perzentil-Erklaerung, Merkmalszeile - je einmal. (e) die fuenfte Nennung des Stopabstands (Anhang B) ist weg, sie war beim SHORT falsch. (f) ,Auf einen Blick: von 3 Merkmalen' im Abschnitt AUF EINEN BLICK heisst jetzt ,Merkmale'. ➤ Beim Straffen gefunden: die Pruefung ,der Faktenblock steht in Abschnitt 1, vor der Rechnung' war seit S-4 (11.09.) falsch und bestand NUR, weil im Kopf ,Schwankungsbreite und Stop' stand - jetzt am wirklichen Ort (Abschnitt 3) geprueft", 'gilt',
               'agent/signal_mail.py; agent/gesamtbild.py; Paket Mailstraffung; Paket 12', '', '', 'pruefstand_hebelmail.py: echte Kette im Trockenlauf auf einer Kopie der Produktionssicherung 2026-09-12_0646, echte config.yaml, SOL Hebel LONG und SHORT, vorher und nachher; Modellantworten und Marktraenge gestellt'),
    Befundlage('2.447-begriffe', "✔ BEGRIFFE. (a) Krypto: ,Tage' statt ,Handelstage' in Trichter und Haltedauer (die Kerzen enthalten Wochenenden); Aktien behalten ,Handelstage'. (b) EIN Wort je Groesse: der Faktenblock-Wert heisst ,Schwankungsbreite' - er IST die ATR, in der die Mail alle Abstaende misst; der Kopf nennt den Trichter ,Uebliche Kursbewegung' statt ,Schwankungsbreite und Stop'. (e) ,noetig 53' nennt seinen Satz (,Bitpanda 1,50 %%', aus `SAETZE_JE_SEITE_MAILTEXT`, nicht abgeschrieben). ✖ KORREKTUR ZU 2.446-begriffe (c): ,Umschlag' sind NICHT zwei Groessen - beide Stellen meinen Volumen je Umlaufmenge, einmal gegen die eigene Geschichte (Abschnitt 3), einmal gegen den Markt (Abschnitt 4), und beide nennen ihren Bezug. Bleibt. ➤ (d) ,Take-Profit' BLEIBT: so heisst das Feld in der Bitpanda-App, der Renderer erkennt es als Handelsparameter (`ui.formatting.HANDELSPARAMETER`), und die GUI nutzt es", 'gilt',
               'agent/trichter.py; agent/entscheidungsrechnung.py; agent/trefferbilanz.py; ui/formatting.py', '', '', 'pruefstand_hebelmail.py: echte Kette im Trockenlauf auf einer Kopie der Produktionssicherung 2026-09-12_0646, echte config.yaml, SOL Hebel LONG und SHORT, vorher und nachher; Modellantworten und Marktraenge gestellt'),
    Befundlage('2.447-fenster', "✔ 2.445-FENSTER IN DER MAIL. Ist das sichere Hebelfenster kuerzer als die geschaetzte Haltedauer, steht unter der Hebelzeile ,Sicher bis Tag 20 !! kuerzer als die geschaetzte Haltedauer von 25 Tagen - danach liegt die Liquidation vor dem Stop' - und durch die Marke `!!` auch im Kopf. Im Normalfall steht nichts zusaetzlich da. Reine Arithmetik aus zwei Zahlen der Rechnung, keine Bewertung. ➤ Am Pruefstand trifft es den SHORT (Fenster 20, Haltedauer 25), nicht den LONG (32 gegen 25): die Finanzierung laeuft beim Short schneller gegen den Stop", 'gilt',
               'agent/entscheidungsrechnung.py; Befund 2.445-fenster; Paket Mailstraffung', '', '', 'pruefstand_hebelmail.py: echte Kette im Trockenlauf auf einer Kopie der Produktionssicherung 2026-09-12_0646, echte config.yaml, SOL Hebel LONG und SHORT, vorher und nachher; Modellantworten und Marktraenge gestellt'),
    Befundlage('2.447-offen', "➤ WAS SCHRITT 31 BEWUSST NICHT ANGEFASST HAT, UND WARUM. (1) DIE SAETZE AUS `lagebeschreibung` - Widerstand/Unterstuetzung (dieselbe Marke 91,15 EUR steht dort und in der Rechnung), ,Auf Sicht der letzten 27 Handelstage', Umschlag-Perzentil: DIESELBEN Saetze liest das Modell. Sie zu aendern waere eine Promptaenderung - Schritt 33, erst nach der Messung. Paket Mailstraffung haelt fest, dass sie unveraendert sind. (2) DIE TRICHTER-ETIKETTEN (,GUENSTIG: gewoehnliches Schwanken allein erreicht ihn nicht - wer ihn ausloest, hat ein Argument geliefert') - Arithmetik gegen eine gemessene Spanne, aber der zweite Halbsatz ist eine Deutung ohne eigene Messung; nicht Teil der Nutzerentscheidung, und `gesamtbild` zaehlt sie. OFFENE FRAGE, kein Befund. (3) REGEL 2 (Zaehlzeile ,5 nicht eingerechnet - x gemessen und gefallen, y Anzeige') im Hauptteil: nicht gebaut, weil der Grund nur als Freitext vorliegt - zaehlen hiesse raten. Seit S-4 steht der Block ohnehin im Anhang. (4) DIE ZAHL IM KOPF: ,Merkmale 2 dagegen' und darunter drei Dagegen-Zeilen, wenn eine Grenze der Rechnung dazukommt - beides stimmt, es sind verschiedene Mengen", 'offen',
               'Schritt 31; agent/lagebeschreibung.py; agent/trichter.py; agent/wahrscheinlichkeit.py', '', '', 'pruefstand_hebelmail.py: echte Kette im Trockenlauf auf einer Kopie der Produktionssicherung 2026-09-12_0646, echte config.yaml, SOL Hebel LONG und SHORT, vorher und nachher; Modellantworten und Marktraenge gestellt'),
    Befundlage("2.446", "\u2714\u2714 SCHRITT 41 GEPRUEFT AN EINER ECHTEN, AKTUELLEN MAIL - UND DER WEG DAHIN IST SELBST EIN BEFUND. \u26a0\ufe0f VERSANDTE MAILS WERDEN NIRGENDS GESPEICHERT: keine Tabelle, keine Datei, kein Exportfeld. Die Beispiele im Austauschordner reichen bis 03.09., vor der neuen Gliederung (S-4) und vor Paket B. Eine Mail laesst sich im Nachhinein nur pruefen, wenn der Nutzer sie weiterleitet. \u2714 GEBAUT: `pruefstand_hebelmail.py` - `fuehre_lauf(betriebsart=trocken)`, dieselbe Kette wie im Betrieb, auf einer im Speicher geoeffneten Kopie der Sicherung, mit der ECHTEN `config.yaml`; nur Modellantworten und Marktraenge sind gestellt und im Text als [GESTELLT] markiert. Ergebnis deckt sich mit der echten SOL-Mail vom 12.09.: 17.987 EUR Kapital, 500 EUR Einsatz, r(q)-Zeile. \u26a0\ufe0f DIE ERSTE FASSUNG DES PRUEFSTANDS WAR FALSCH: sie uebergab nur die Bremsen-Konfiguration, `hebel_aus_quote.aktiv` fiel auf die Code-Vorgabe `False`, und die Mail zeigte ,Hebel 1,3x\u2018 aus dem alten Risikobudget-Weg. Fast waere daraus ein Befund geworden. \u27a4 VORSCHLAG: den Mailtext beim Versand mitschreiben - dann wird die naechste Fachpruefung an den Mails gemacht, die tatsaechlich rausgingen", "gilt",
               "pruefstand_hebelmail.py; Suche in database/, agent/, api/", "", "", "pruefstand_hebelmail.py: echte Kette im Trockenlauf auf einer Kopie der Produktionssicherung 2026-09-12_0646, echte config.yaml, SOL, LONG und SHORT; Modellantworten und Marktraenge gestellt"),
    Befundlage("2.446-richtung", "\u26a0\ufe0f\u26a0\ufe0f\u26a0\ufe0f DIE HEBELMAIL NANNTE IHRE RICHTUNG NICHT - UND EINE SHORT-EMPFEHLUNG LAS SICH ALS KAUF. BEHOBEN. Am Pruefstand kam ein Short als *,SOL - KAUFEN (Hebel)\u2018*, mit dem Stop UEBER dem Kurs, beschriftet *,(-11,2 %%)\u2018*, und dem Ziel darunter; das Wort SHORT stand nur im Anhang. In der ganzen LONG-Mail kam ,LONG\u2018 nicht ein einziges Mal vor. Ausgefuehrt wird von Hand in der Bitpanda-App - wer ,KAUFEN\u2018 liest, eroeffnet die Gegenposition. \u27a4 IM CODE BESTAETIGT: Betreff `{symbol} - {aktion}` ohne Richtung, Stopzeile fest `(-x %%)`. \u27a4 EINGETRETEN? NEIN, NOCH NICHT: seit dem 22.08. kein SHORT-Signal in der Produktion; vom 15. bis 22.08. waren es 252 (alte Kette). Der Weg ist offen (S6c). \u26a0\ufe0f PRAEZISIERT 14.09. (2.447-schalter): mit der STANDARDEINSTELLUNG `hebel_richtung_modus: nur_long` geht eine SHORT-Mail gar nicht hinaus - der Schalter sitzt am Versand. Hinaus waere die falsche Mail nur mit ,beide\u2018 gegangen. \u2714 BEHOBEN in `signal_mail.baue_mail`: Betreff ,KAUFEN (Hebel, SHORT)\u2018 bzw. ,(Hebel, LONG)\u2018 - SHORT immer, LONG beim Hebel; ,Auf einen Blick\u2018 beginnt mit ,Richtung SHORT - Gewinn bei FALLENDEM Kurs\u2018; der Stopabstand traegt bei SHORT ein Plus. Die Richtung kommt aus dem Urteil, sonst aus der Geometrie. Am Pruefstand beide Richtungen nachgewiesen. \u2714 PAKET `Mailrichtung` (7 Pruefungen) - gegen den alten Mailbauer schlagen 4 davon an. Zwei aeltere Betreffpruefungen verlangten den alten Wortlaut und sind nachgezogen", "gilt",
               "agent/signal_mail.py; pruefstand_hebelmail.py SOL LONG/SHORT; signals in der Sicherung 12.09.", "", "", "pruefstand_hebelmail.py: echte Kette im Trockenlauf auf einer Kopie der Produktionssicherung 2026-09-12_0646, echte config.yaml, SOL, LONG und SHORT; Modellantworten und Marktraenge gestellt"),
    Befundlage("2.446-zahlen", "\u2714 PUNKT (1), DIE ZAHLEN: JEDE NACHGERECHNET, ALLE STIMMEN. Gegen die echten Funktionen, nicht gegen eine zweite Rechnung: Stop 11,2 %% (2,5 x ATR) \u00b7 Risiko 1,25 %% x 17.987 = 225 EUR \u00b7 Positionswert 2.013 EUR / 500 = 4,0x \u00b7 am Stop -223, am Ziel +447 \u00b7 sicher bis Tag 32 (`tage_bis_liquidation_am_stop` 32,4) \u00b7 Huerde 45,9 %% / 53,0 %% (`wahrscheinlichkeit.rechne` mit Finanzierung) \u00b7 Kosten 84 EUR auf 2.000 EUR Position, frisst 38 %% des Risikos \u00b7 Anhang C gegen `estimate_liquidation_price`: 26,7 / 8,4 / 1,1 %% bei 3x / 6x / 10x \u00b7 Markenabstaende in Schwankungsbreiten \u00b7 Haltedauer 25 Tage bei 2,5 ATR (gemessen 23-27, 2.445). \u26a0\ufe0f EINE KLEINE ABWEICHUNG, SCHON BEKANNT: die Liquidation 72,79 EUR rechnet mit dem UNGERUNDETEN Hebel 4,025, die Ergebniszeile mit dem angezeigten 4,0 - das ist 2.382-rundung, kein neuer Befund", "gilt",
               "pruefstand_hebelmail.py; Nachrechnung 13.09. gegen die Betriebsfunktionen", "", "", "pruefstand_hebelmail.py: echte Kette im Trockenlauf auf einer Kopie der Produktionssicherung 2026-09-12_0646, echte config.yaml, SOL, LONG und SHORT; Modellantworten und Marktraenge gestellt"),
    Befundlage("2.446-etiketten", "\u26a0\ufe0f\u26a0\ufe0f DIE DREI GUENSTIG-ETIKETTEN IN ,DIE LAGE DES WERTS\u2018 TRAEGT DAS REGISTER NICHT. Schwankung, Kurs (unter dem 60-Tage-Hoch) und Volumen stehen dort mit GUENSTIG/MITTEL/UNGUENSTIG und dem Satz ,ueber alle Einstiege gemessen: 29,5 %% Treffer am guten Ende gegen 17,8 %%\u2018. \u27a4 DIE QUELLE IST `faktenblock.KERN`: eine GEPOOLTE Messung vom 12.08. (37 Symbole, 20.494 Anker) - vor der Tagesklammer (31.08.) und vor dem Messstandard (08.09.). \u27a4 DAGEGEN REGISTRIERT: Schwankung - 2.135 (gilt): ,vola traegt KEINE Richtung\u2018; Kurs/Momentum - REGISTER_Kandidaten `momentum` und `momentum_kurz` \u2716 traegt nicht (09.09., 536 Symbole); Volumen je Mittel - kein Kandidat. \u27a4 FOLGE FUER DEN LESER: der Kopf zaehlt diese Etiketten richtigerweise NICHT (`gesamtbild` kennt vier feste Merkmale) - aber der Rumpf zeigt drei ,dafuer\u2018 an, die keinen gueltigen Beleg haben. Genau daher kam der Eindruck ,viele Warnungen, und das Dafuer sieht man nicht\u2018: das Dafuer, das es gibt, ist nicht belegt. \u27a4 NUTZERENTSCHEIDUNG FUER SCHRITT 31: die Werte behalten (sie sind Fakten), die Etiketten streichen oder als ,nicht belegt\u2018 kennzeichnen", "abgeloest",
               "agent/faktenblock.py KERN; Befund 2.135; REGISTER_Kandidaten momentum", '2.447-etiketten', 'Nutzerentscheidung 13.09. umgesetzt: Etiketten und Wirkungssatz gestrichen, Wert und Beschreibung bleiben.', "pruefstand_hebelmail.py: echte Kette im Trockenlauf auf einer Kopie der Produktionssicherung 2026-09-12_0646, echte config.yaml, SOL, LONG und SHORT; Modellantworten und Marktraenge gestellt"),
    Befundlage("2.446-redundanz", "\u27a4 PUNKT (2), REDUNDANZ - an der aktuellen Mail neu gezaehlt, der Stand von 2.390-warnungen ist teils ueberholt. \u2714 BEWUSST: ,Auf einen Blick\u2018 wiederholt Zone, Stop, Take-Profit, Betrag und Ergebnis aus Abschnitt 2 - das ist die Zusammenfassung nach dem Mailvorschlag vom 11.09. \u26a0\ufe0f ECHTE DOPPELUNGEN: der Stopabstand 11,2 %% steht FUENFMAL (Kopf, Rechnung, Trichter, Anhang B zweimal); die Marke 91,15 EUR DREIMAL (Marken der Rechnung, Widerstand in der Lage, ,3,4 %% hoeher\u2018 in den Kursmarken); die Stuetze 84,13 EUR ZWEIMAL (Lage, ,4,5 %% tiefer\u2018); die beiden UNGUENSTIG-Saetze (Trichter-Ziel, Termine) stehen im Kopf fast woertlich wie weiter unten, obwohl der Kopf ,je eine Zeile, Einzelheiten weiter unten\u2018 verspricht; ein Erklaersatz der Lebendigkeit zweimal woertlich. \u27a4 NICHT BEURTEILBAR am Pruefstand: ,steht auf EINEM Beitrag\u2018 und der Umschlag in den Belegen - beides haengt an gestellten Teilen", "abgeloest",
               "pruefstand_hebelmail.py SOL LONG, Zaehlung 13.09.", '2.447-straffung, 2.447-short', 'Kopf nennt die Tatsache statt des Satzes, die fuenfte Stopnennung ist weg, der Lebendigkeitssatz steht einmal im Anhang E. Die doppelte Marke aus `lagebeschreibung` bleibt - Modelltext (2.447-offen).', "pruefstand_hebelmail.py: echte Kette im Trockenlauf auf einer Kopie der Produktionssicherung 2026-09-12_0646, echte config.yaml, SOL, LONG und SHORT; Modellantworten und Marktraenge gestellt"),
    Befundlage("2.446-lesbarkeit", "\u27a4 PUNKT (3), LESBARKEIT. 152 nicht leere Zeilen; 14 Warn- und Dagegen-Zeilen gegen 3 Dafuer-Etiketten, und diese drei sind unbelegt (2.446-etiketten). \u26a0\ufe0f DIE AKTION STEHT NUR IM BETREFF UND IN ABSCHNITT 5 (Zeile 115 von 177) - ,Auf einen Blick\u2018 nennt seit heute die Richtung, aber nicht, was zu tun ist. \u26a0\ufe0f ACHT wiederkehrende Erklaersaetze je Mail (,Was das heisst\u2018, ,Der Trichter sagt WIE WEIT\u2018, ,Zu lesen\u2018, ,Nicht zu verwechseln\u2018, Perzentil-Erklaerung, Beobachtungssatz) - sie erklaeren beim ersten Lesen und stehen in jeder weiteren Mail wieder. \u26a0\ufe0f DIE MAIL STELLT HALTEDAUER UND SICHERES HEBELFENSTER NIE NEBENEINANDER (2.445-fenster). \u27a4 Der Stoff fuer die Straffung (Schritt 31) - dort nach Regel 2 und 3, hier nur gezaehlt", "abgeloest",
               "pruefstand_hebelmail.py SOL LONG, Zaehlung 13.09.", '2.447-straffung, 2.447-fenster', 'Empfehlung im Kopf, Erklaersaetze im Anhang E, Beitragsbeschreibungen im Anhang D, Haltedauer gegen Hebelfenster verglichen.', "pruefstand_hebelmail.py: echte Kette im Trockenlauf auf einer Kopie der Produktionssicherung 2026-09-12_0646, echte config.yaml, SOL, LONG und SHORT; Modellantworten und Marktraenge gestellt"),
    Befundlage("2.446-begriffe", "\u27a4 PUNKT (4), BEGRIFFE. \u2714 ERLEDIGT: ,Konfidenz\u2018 kommt nicht mehr vor; ,Modell\u2018 meint durchgehend das Sprachmodell, Abschnitt 5 ist als ,BEHAUPTET - Rolle Haendler\u2018 gekennzeichnet. \u26a0\ufe0f OFFEN: (a) ,Handelstage\u2018 achtmal - fuer Krypto sind es Kalendertage (Kerzen mit Wochenende, 2.445); (b) DREI Woerter fuer Schwankung - ,Schwankungsbreiten\u2018 (zehnmal, = ATR), ,Schwankung 4,4 %% je Tag\u2018 und ,Uebliche Kursbewegung\u2018; die Mail muss selbst warnen ,nicht zu verwechseln\u2018; (c) ,Umschlag\u2018 fuer ZWEI Groessen - das eigene Perzentil in der Lage und den Querschnittsrang im Marktvergleich; (d) ,Take-Profit\u2018 neben ,Ziel\u2018; (e) zwei Trefferquoten - 37,3 %% in Abschnitt 1 und die ,Erfahrungsrate\u2018 34 in Anhang B, dort ,noetig 46\u2018 ohne Angabe, zu welchem Gebuehrensatz (es ist Bitpanda); (f) die Haltedauer heisst ,bis zum Ziel\u2018, gemeint ist die erste Marke", "abgeloest",
               "pruefstand_hebelmail.py SOL LONG; Befund 2.445", '2.447-begriffe', 'Tage statt Handelstage bei Krypto, ein Wort je Groesse, Gebuehrensatz genannt; Umschlag korrigiert (dieselbe Groesse, zwei Bezuege); Take-Profit bleibt mit Grund.', "pruefstand_hebelmail.py: echte Kette im Trockenlauf auf einer Kopie der Produktionssicherung 2026-09-12_0646, echte config.yaml, SOL, LONG und SHORT; Modellantworten und Marktraenge gestellt"),
    Befundlage("2.446-gui", "\u27a4 PUNKT (5), GLEICHLAUF MIT DER GUI - 2.390-gui am Code nachgeprueft und erweitert. \u26a0\ufe0f DIE ALTE DREITEILUNG STEHT WEITER IM CODE, UND ZWAR ZWEIMAL: ,1. MATHEMATISCH BERECHNET / 2. LLM-BEWERTUNG (Konfidenz) / 3. KONKLUSION\u2018 in `ui/hebel_view.py` UND in `ui/signals_view.py` - der Signale-Reiter war in 2.390-gui nicht genannt. \u27a4 DIE ZEILEN UNTER 2x sind Altbestand: 55 von 56 Hebelzeilen seit 11.09. liegen bei 1,0-1,2x, alle VOR dem Rollout (juengste 12.09. 02:59). Seit H-2 schreibt die Kette dort keine Hebelspalte mehr (Etikett spot); die GUI zeigt aber je Symbol und Richtung die LETZTE Zeile - die alten bleiben stehen, bis eine neue kommt. \u2714 UMGEKEHRT: die GUI hatte die Spalte ,Richtung\u2018 - die Mail nicht (seit 2.446-richtung behoben). \u27a4 Umsetzung ist Schritt 32", "abgeloest",
               "ui/hebel_view.py 535/600/709; ui/signals_view.py 547-552; database/db.get_latest_rollen_hebel_signal_per_symbol_and_richtung; Sicherung 12.09.", '2.448-umsetzung', "Die alte Dreiteilung ist fuer Rollen-Signale in beiden Reitern ersetzt, die Hebelzeilen unter 2x sind als ,Spot, vor Paket B' benannt.", "pruefstand_hebelmail.py: echte Kette im Trockenlauf auf einer Kopie der Produktionssicherung 2026-09-12_0646, echte config.yaml, SOL, LONG und SHORT; Modellantworten und Marktraenge gestellt"),
    Befundlage("2.445", "\u2714\u2714\u2714 DIE HALTEDAUER IST GEMESSEN - UND DIE "
               "FORMEL DER MAIL IST EINE BRAUCHBARE NAEHERUNG, NICHT DER "
               "FEHLER, FUER DEN ICH SIE GEHALTEN HABE. `messe_haltedauer.py`: "
               "Tage bis zur ERSTEN Marke (Stop oder Ziel), Stop k x ATR, "
               "Ziel CRV 2, Horizont 120, zensierte gezaehlt. Positivkontrolle "
               "an driftfreien Kunstreihen mit bekannter Wahrheit 5/5 "
               "bestanden; Reproduktion von 2.435 Probe 2 IDENTISCH (25.590 "
               "von 32.040 aufgeloest, 79,9 %%). \u27a4 MEDIAN IN TAGEN, LONG / "
               "SHORT: 0,75 ATR 3/3 \u00b7 1,0 ATR 5/5 \u00b7 1,5 ATR 10/10 \u00b7 2,0 ATR "
               "16/17 \u00b7 2,5 ATR 23/27 \u00b7 3,0 ATR 33/37. Die Formel "
               "`(CRV x k)\u00b2` sagt 2,2 \u00b7 4 \u00b7 9 \u00b7 16 \u00b7 25 \u00b7 36. \u27a4 AM "
               "BETRIEBSPUNKT 2,5 ATR LIEGT SIE +9 %% (LONG) BZW. -7 %% (SHORT) "
               "NEBEN DEM MEDIAN; bei engen Stops unterschaetzt sie um 20-25 %%. "
               "Nach der vorab festgelegten Regel ist sie in den meisten "
               "Zeilen WIDERLEGT - die Baender sind bei 32.040 Ankern nur "
               "einen Tag breit. Praktisch ist sie eine Naeherung auf rund "
               "10 %% am Betriebspunkt. \u2714 GEGENPROBEN: nur ab 2023 und "
               "zweite Saat aendern keinen Median um mehr als einen Tag. "
               "\u26a0\ufe0f KALENDER: Krypto-Kerzen enthalten Wochenenden - "
               "ein Tag ist hier ein KALENDERtag, fuer Krypto ist das "
               "dasselbe wie ein Handelstag", "gilt",
               "messe_haltedauer.py, Lauf 13.09. abends", "", "", "messmenge.V1, 534 Krypto-Reihen, 32.040 Anker, Stop k x ATR (atr_wilder), CRV 2, Horizont 120 Kalendertage, Stand 13.09.2026"),
    Befundlage("2.445-mechanismus", "\u2716 MEINE ERKLAERUNG, WARUM DIE FORMEL "
               "PASST, IST WIDERLEGT - im selben Lauf. Vermutet hatte ich "
               "(nach dem Vorabtest, als Nachtrag im Werkzeugkopf benannt): "
               "die Zeit bis zur ersten von zwei Schranken ist in einer "
               "Brownschen Bewegung a x b in Tagesschwankungen; mit ATR/sigma "
               "nahe Wurzel 2 ergaebe das genau `(CRV x k)\u00b2`. GEMESSEN: "
               "ATR/sigma liegt im Median bei 1,83, und die daraus folgende "
               "Vorhersage waere 42 Tage bei 2,5 ATR statt gemessener 23. "
               "\u27a4 ECHTE KRYPTOPFADE ERREICHEN DIE MARKEN DEUTLICH SCHNELLER "
               "als eine Irrfahrt mit derselben Schwankung - vereinbar mit "
               "dicken Raendern und Schwankungsschueben, aber das ist "
               "hier NICHT gemessen. \u26a0\ufe0f DASS DIE FORMEL PASST, IST "
               "EMPIRISCH BELEGT UND NICHT ERKLAERT. Wer sie auf eine andere "
               "Klasse uebertraegt (Aktien, Rohstoffe), hat dafuer keinen "
               "Beleg", "gilt",
               "messe_haltedauer.py, Spalten a x b und ATR/sigma", "", "", "messmenge.V1, 534 Krypto-Reihen, 32.040 Anker, Stop k x ATR (atr_wilder), CRV 2, Horizont 120 Kalendertage, Stand 13.09.2026"),
    Befundlage("2.445-wirkung", "\u27a4 WAS DARAUS FUER KETTE UND MAIL FOLGT - "
               "und was NICHT. \u2714 DIE ,25 TAGE\u2018 SIND FUER EINEN 2,5-ATR-STOP "
               "RICHTIG (gemessen 23-27). Die Finanzierung in der "
               "Mailrechnung ist damit NICHT ueberzeichnet. \u2714 DIE "
               "NUTZERERWARTUNG ,3-5 TAGE\u2018 IST EBENFALLS RICHTIG - fuer Stops "
               "von 0,75 bis 1 ATR (Median 3 bzw. 5 Tage). Beides stimmt; es "
               "sind verschiedene Trades. Einordnung: der Widerlegungspreis "
               "des Modells, aus dem 81,5 %% der Stops kommen, liegt im "
               "Median bei 8 %% - bei typischer Krypto-ATR von 6-10 %% des "
               "Kurses also um 1 ATR, und dort sind 3-5 Tage die Regel. Der "
               "ATR-Rueckfall setzt 2,5 ATR, bei Krypto meist um 20 %% des "
               "Kurses - ein weiter, langsamer Trade. \u2714 NICHT BETROFFEN: "
               "Bewertung, Hebel, Stop. \u27a4 EIN ERSATZ DER FORMEL durch die "
               "gemessene Tabelle braechte am Betriebspunkt rund 10 %%, bei "
               "engen Stops 20-25 %% - ein Feinschliff, kein Fehler", "gilt",
               "Befunde 2.445, 2.437-atr, 2.438; messe_haltedauer.py", "", "",
               "messmenge.V1, 534 Krypto-Reihen, 32.040 Anker, Stop k x ATR (atr_wilder), CRV 2, Horizont 120 Kalendertage, Stand 13.09.2026"),
    Befundlage("2.445-fenster", "\u26a0\ufe0f\u26a0\ufe0f WAS VON 2.443 BLEIBT - PRAEZISIERT. "
               "Die Mail nennt Haltedauer und sicheres Hebelfenster und "
               "vergleicht sie nie - das stimmt weiter. \u2716 FALSCH war dort: "
               ",25 Handelstage sind rund 35 Kalendertage\u2018. Krypto handelt "
               "durchgehend, die Tage SIND Kalendertage; es gibt keinen "
               "Waehrungsfehler. \u27a4 WO DER KONFLIKT ECHT IST: das sichere "
               "Fenster haengt am Stop IN PROZENT und am Hebel (8 %% und 5x: "
               "20,7 Tage), die Haltedauer am Stop IN ATR (2,5 ATR: Median "
               "23, bis Tag 20 aufgeloest 46 %%). Beides trifft nur dort "
               "zusammen, wo 2,5 ATR um 8 %% liegen - bei SCHWANKUNGSARMEN "
               "Werten wie BTC, die zugleich den Hebeldeckel von 5x "
               "erreichen. Dort ueberlebt rund die Haelfte der Trades das "
               "sichere Fenster. Beim typischen Krypto-ATR-Stop um 20 %% ist "
               "der Hebel 2-2,5x und das Fenster ueber 100 Tage - kein "
               "Konflikt. \u26a0\ufe0f BEGRIFF FUER SCHRITT 41: die Mail schreibt "
               ",Handelstage\u2018 und der Code-Kopf ,bis zum Ziel\u2018 - beides "
               "ist fuer Krypto ungenau: es sind Kalendertage, und gemeint ist "
               "die erste Marke, nicht das Ziel ➤ ERLEDIGT durch Schritt 31 (2.447-fenster: Zeile ,Sicher bis ... !! kuerzer als die geschaetzte Haltedauer' in der Mail; 2.447-begriffe: Tage statt Handelstage bei Krypto) - Review 14.09.", "abgeloest",
               "Befunde 2.443, 2.445; agent/krypto/hebel_risk_gate."
               "tage_bis_liquidation_am_stop", "2.447-fenster", "in der Mail umgesetzt mit Schritt 31", "messmenge.V1, 534 Krypto-Reihen, 32.040 Anker, Stop k x ATR (atr_wilder), CRV 2, Horizont 120 Kalendertage, Stand 13.09.2026"),
    Befundlage("2.444", "⚠️⚠️⚠️ DIE ,25 HANDELSTAGE‘ IN DER MAIL "
               "SIND KEINE SCHAETZUNG DIESES TRADES, SONDERN EINE KONSTANTE. "
               "Nutzerfrage 13.09.: *,keine Ahnung warum 25 Handelstage "
               "steht - eigentlich war ich der Meinung, dass die meisten "
               "Trades zwischen 3-5 Tagen das Ziel erreichen'*. Er "
               "verwechselt nichts. ➤ DIE FORMEL: "
               "`_haltedauer_tage = (Zielweg / ATR)²` - Zeit waechst mit dem "
               "Quadrat der Strecke (driftfreier Pfad). Der Stop liegt bei "
               "2,5 ATR, das Ziel bei CRV 2 also bei 5 ATR, und 5² = 25. "
               "⚠️ DAMIT STEHT BEI JEDEM TRADE, DESSEN STOP AUS DER "
               "ATR-REGEL KOMMT, IMMER 25 - egal welches Asset, egal welche "
               "Lage. Nur beim Widerlegungspreis des Modells aendert sich "
               "die Zahl. ➤ UND DIE FORMEL BEANTWORTET DIE FALSCHE FRAGE: "
               "sie rechnet, wie lange der Weg bis zum ZIEL dauert - ein "
               "Trade endet aber an der Marke, die ZUERST kommt, und das ist "
               "meist der Stop. ➤ WAS DAGEGEN GEMESSEN VORLIEGT: bei 8 %% "
               "Stop loesen 80 %% der Anker innerhalb von 10 Tagen an Stop "
               "oder Ziel auf (2.435, Probe 2, 32.040 Anker); die 188 echten "
               "NB-Hebelpositionen hielten im Median 0,3 Tage, 90 %% unter "
               "3,3 (2.380-annahmen); der Betriebshorizont ist in 2.226 und "
               "D3 mit 3-5 Tagen dokumentiert. ⚠️ DER DOCSTRING SAGT ES "
               "SELBST: *,sie gehoert gegen die eigenen Reihen nachgerechnet "
               "- offener Punkt'* - das ist nie geschehen. "
               "➤ WIRKUNG AUF DIE KETTE: die Zahl speist die FINANZIERUNG "
               "in der Mailrechnung. 25 statt rund 5 Tage ueberzeichnen die "
               "Kosten eines Hebeltrades - die Mail laesst Hebel "
               "wirtschaftlich schlechter aussehen, als er ist. Und der "
               "Widerspruch aus 2.443 (Haltedauer ueber dem sicheren "
               "Fenster) ist grossteils ein Folgefehler dieser Zahl. "
               "✖ NICHT BETROFFEN: Bewertung, Hebelhoehe, Stop - die Zahl "
               "wirkt nur in der Mail (Regel 2)", "abgeloest",
               "agent/entscheidungsrechnung._haltedauer_tage Zeile 527; "
               "Befunde 2.226, 2.380-annahmen, 2.435; D3",
               abgeloest_durch="2.445, 2.445-wirkung",
               warum="Die Messung hat drei meiner Saetze widerlegt. (1) 'Die "
                     "Formel beantwortet die falsche Frage' - sie misst zwar "
                     "formal den Zielweg, trifft den gemessenen Median bis zur "
                     "ERSTEN Marke aber am Betriebspunkt auf rund 10 %. (2) '25"
                     " statt rund 5 Tage' - fuer einen 2,5-ATR-Stop sind 23-27 "
                     "Tage gemessen; die 5 Tage gelten fuer 1-ATR-Stops. (3) "
                     "'Die Mail ueberzeichnet die Finanzierung' - sie tut es "
                     "nicht. Ich hatte eine ERKLAERUNG als Befund geschrieben, "
                     "BEVOR gemessen war."),
    Befundlage("2.443", "⚠️⚠️⚠️ SCHRITT 41, ERSTER FUND DER "
               "ZAHLENPRUEFUNG: DIE MAIL NENNT ZWEI FRISTEN, DIE SICH "
               "WIDERSPRECHEN - UND STELLT SIE NIE NEBENEINANDER. In "
               "`entscheidungsrechnung` schreibt Zeile 1240 *,Haltedauer "
               "etwa N Handelstage'*, und zwanzig Zeilen spaeter (1260) "
               "*,Liquidation etwa X EUR, hinter dem Stop bis etwa Tag "
               "M'*. Beide Zahlen stammen aus derselben Rechnung, keine "
               "Zeile vergleicht sie. ➤ GEMESSEN ueber ein Raster aus "
               "ATR und Risikobudget, MIT der Betriebsgrenze von 5x: in 5 "
               "von 14 Hebelfaellen liegt die geschaetzte Haltedauer UEBER "
               "dem Zeitraum, in dem der Hebel nachweislich hinter dem Stop "
               "bleibt. Beispiel Stop 8 %%, Risiko 200 EUR, Hebel 5,0x: "
               "Haltedauer 25, sicher bis Tag 20,7. "
               "⚠⚠ UND ES IST SCHLIMMER, WEIL DIE BEIDEN ZAHLEN IN "
               "VERSCHIEDENEN WAEHRUNGEN STEHEN: die Haltedauer zaehlt "
               "HANDELStage, die Liquidationsfrist KALENDERtage - die "
               "Finanzierung laeuft taeglich, auch am Wochenende "
               "(`funding_rate_daily_pct`). 25 Handelstage sind rund 35 "
               "Kalendertage; der Abstand ist also nicht 4 Tage, sondern "
               "rund 14. ⚠️ DAS IST DERSELBE FEHLERTYP wie die "
               "Frischegrenze in Schritt 51 (Kalender- statt Handelstage) "
               "und wie 2.390-zahlen (die Mail widersprach sich selbst): "
               "jede Zahl fuer sich richtig, die Aussage zusammen falsch. "
               "➤ ABGEGRENZT GEGEN 2.379-tage: der misst die VERTEILUNG "
               "gegen ECHTE Haltedauern (Median 0,3 Tage am NB) und kommt "
               "zu ,keine Handlung noetig'. Hier geht es nicht um die "
               "Wirklichkeit, sondern darum, dass die MAIL ihre eigene "
               "Schaetzung nicht mit ihrer eigenen Grenze vergleicht. "
               "⚠️ NICHT GEAENDERT: Schritt 41 verlangt ausdruecklich "
               "*,erst pruefen, DANN straffen'* - was mit den beiden Zeilen "
               "geschieht, gehoert an das Ende der Fachpruefung, nicht in "
               "ihre Mitte", "abgeloest",
               "agent/entscheidungsrechnung.py Zeilen 1240 und 1260-1267; "
               "Raster ueber ATR und Risikobudget 13.09.",
               abgeloest_durch="2.445-fenster",
               warum="Der Kern bleibt und steht praezisiert in 2.445-fenster: "
                     "die Mail vergleicht Haltedauer und sicheres Hebelfenster "
                     "nie. Falsch war der Satz '25 Handelstage sind rund 35 "
                     "Kalendertage': Krypto-Kerzen enthalten Wochenenden, die "
                     "Tage sind Kalendertage. Und der Konflikt ist nicht "
                     "allgemein, sondern trifft schwankungsarme Werte am "
                     "5x-Deckel."),
    Befundlage("2.442", "✔✔✔ DIE STUMMMELDUNG IST GEBAUT - die Kette "
               "sagt jetzt, wozu sie NICHTS sagen kann. Nutzerentscheidung "
               "13.09.: *,ja Mailzeile fuer alle drei'*. "
               "`verkaufsrechnung.stumme_bestaende()` liest `holdings` und "
               "meldet jede gehaltene Kryptoposition, deren USD-Kursreihe "
               "kuerzer ist als `lade_messreihen.MIN_KERZEN` (400). "
               "⚠️ DAS LAUFZEITKRITERIUM IST BEWUSST EIN ANDERES ALS IN "
               "DER SUITE: die Suite fragt nach einer Messreihe in "
               "`data/messdaten.db` - die das NOTEBOOK planmaessig NICHT "
               "hat, weshalb sich das Paket dort selbst ueberspringt. Im "
               "Betrieb entscheidet die Kursreihenlaenge aus "
               "`price_history_ohlc`, mit DERSELBEN Grenze, importiert "
               "statt abgeschrieben. ➤ UND DIE QUELLE IST `holdings`, "
               "NICHT DIE WATCHLIST DES LAUFS - CANTON steht im Bestand "
               "und nicht in der Watchlist; wer die Laufsymbole nimmt, "
               "sieht genau die Werte nicht, um die es geht. "
               "✔ GEPRUEFT an einer gestellten DB: 399 Tage werden "
               "gemeldet, 400 nicht, eine Aktie nicht, ein Cash-Aequivalent "
               "nicht; der kuerzeste steht oben; `stumm` allein loest KEINE "
               "Mail aus (sonst kaeme sie taeglich ohne Anlass); faehrt sie "
               "mit, steht der Abschnitt drin und der Betreff nennt ihn. "
               "13 Pruefungen im Paket Neuaufnahme ⚠️ RICHTIGSTELLUNG 14.09. (Review): CANTON steht sehr wohl in der Watchlist, und `stumme_bestaende` UEBERSPRINGT jeden Bestand ohne Watchlist-Eintrag - ein gehaltener Wert ausserhalb der Watchlist bleibt still (Planpunkt A2, 2.450-neu).", "gilt",
               "agent/verkaufsrechnung.stumme_bestaende; agent/rollen_lauf; "
               "pruefe_pakete.py --paket Neuaufnahme",
               "", "", "gestellte DB mit 13 Pruefungen im Paket Neuaufnahme (13.09.); "
               "Produktionssicherung 2026-09-12_0646; Review 14.09. (Richtigstellung)"),
    Befundlage("2.442-vier", "⚠️ ES SIND VIER, NICHT DREI - UND DAS "
               "GEHOERT VORGELEGT. Gefiltert wird ueber EIGENSCHAFTEN "
               "(Assetklasse krypto, kein Cash-Aequivalent), nicht ueber "
               "eine Symbolliste - eine Ausnahmeliste im Betriebscode waere "
               "die naechste Stelle, die niemand pflegt. Damit meldet die "
               "Mail: CANTON (0 von 400) · VSN (0) · MON (269) · ASTER "
               "(318). ➤ VSN IST DER VIERTE. Der Nutzer hatte am 08.09. "
               "gesagt *,vsn ist nicht relevant'* - das war eine Ausnahme "
               "von der roten SUITE-Zeile, und ihre Begruendung lautet "
               "woertlich *,es hat weder in der Messbasis noch in der "
               "Produktion eine Kursreihe; eine Bewertung ist damit ohnehin "
               "nicht moeglich'*. Genau das sagt die neue Mailzeile. "
               "⚠⚠ IHN AUSZUBLENDEN WAERE DIESELBE STILLE, DIE HIER "
               "BEHOBEN WIRD - deshalb ist er drin. Wenn der Nutzer ihn "
               "nicht sehen will, ist das eine Zeile Aenderung, aber es "
               "soll seine Entscheidung sein, nicht meine stille ➤ NUTZERENTSCHEIDUNG 14.09.: VSN wird aus der Stummzeile AUSGENOMMEN (vollstaendig gestakt). ⚠️ NICHT GEBAUT - `verkaufsrechnung.stumme_bestaende` hat keine Ausnahme; getragen von Schritt 55.",
               "offen",
               "agent/verkaufsrechnung.stumme_bestaende, Lauf 13.09.; "
               "pruefe_neuaufnahme.AUSNAHMEN"),
    Befundlage("2.441", "\u2716\u2716\u2716 ZWEI DER DREI ROTEN ZEILEN WAREN "
               "FEHLER IN DER PRUEFUNG, NICHT IN DEN DATEN - und einer "
               "davon war eine FALSCHE AUSSAGE. \u27a4 (1) DIE PRUEFUNG "
               "NANNTE EINE LOKALE KOPIE ,DIE PRODUKTION'. Sie meldete "
               "*,CANTON hat auch in der PRODUKTION KEINE Kursreihe'*. "
               "Gelesen wird aber `data/tradinginfotool.db` am DESKTOP, und "
               "deren OHLC endet am 2026-08-19 - 25 Tage alt. In der "
               "Produktionssicherung vom 12.09. steht: CANTON 63 USD-Tage "
               "ab 2026-05-07 \u00b7 ASTER 342 (lokal 318) \u00b7 MON 293 (lokal "
               "269). \u26a0\ufe0f ALLE DREI HABEN EINE KURSREIHE. Es ist "
               "derselbe Fall dreimal - zu kurz -, nicht ein Fehlen und "
               "zwei Kuerzen. \u27a4 (2) EINE KRYPTO-BEGRUENDUNG AUF "
               "MAERKTE, DIE SCHLIESSEN: `FRISCHE_GRENZE_TAGE = 7` traegt "
               "die Begruendung *,Krypto handelt durchgehend'* und wurde "
               "auf aktien, rohstoffe und themen_etf angewandt. Am So, "
               "13.09. war die Median-Reihe vom Do, 03.09.: 10 "
               "KALENDERtage, aber nur 6 HANDELStage. \u2714 GEBAUT: die "
               "Frische wird fuer schliessende Maerkte in HANDELStagen "
               "gerechnet - die Grenze bleibt 7, gezaehlt wird nur, was der "
               "Markt liefern konnte. Die Zeile ist damit GRUEN, und zwar "
               "regelkonform, nicht durch Lockerung", "gilt",
               "pruefe_neuaufnahme.py; Produktionssicherung 12.09.", "", "",
               "Produktionssicherung 2026-09-12_0646 gegen die lokale Kopie (OHLC-Stand 2026-08-19); messdaten.db Stand 13.09.2026"),
    Befundlage("2.441-warten", "\u2714\u2714 UND DIE DRITTE ZEILE IST ECHT - "
               "ABER SIE LOEST SICH GROSSTEILS VON SELBST. Alle drei "
               "gehaltenen Werte liegen unter der 400-Tage-Grenze, und "
               "keine Quelle aendert das: es sind junge Werte, die Reihe "
               "IST vollstaendig. Hochgerechnet (Krypto handelt "
               "durchgehend, USD-Tage sind Kalendertage): ASTER erreicht "
               "die Grenze am 2026-11-09 (58 Tage), MON am 2026-12-28 (107 "
               "Tage), CANTON erst am 2027-08-15 (337 Tage). \u27a4 FUER "
               "ZWEI VON DREI IST WARTEN DIE RICHTIGE ANTWORT und kostet "
               "zwei bis vier Monate. Fuer CANTON nicht - und CANTON ist "
               "zugleich der einzige KERNWERT unter den dreien, also der "
               "Fall, bei dem eine fehlende Bewertung laut Nutzervorgabe "
               "NICHT unkritisch ist", "gilt",
               "Produktionssicherung 12.09., Hochrechnung 13.09.", "", "",
               "Produktionssicherung 2026-09-12_0646 gegen die lokale Kopie (OHLC-Stand 2026-08-19); messdaten.db Stand 13.09.2026"),
    Befundlage("2.441-still", "\u26a0\ufe0f\u26a0\ufe0f UND DAS EIGENTLICHE PROBLEM "
               "IST NICHT DIE LUECKE, SONDERN IHRE STILLE: EINE GEHALTENE "
               "POSITION OHNE MESSREIHE WIRD DEM NUTZER NIRGENDS GEMELDET. "
               "Durchsucht wurden `agent/` und `ui/` - es gibt keine "
               "Mailzeile, keine GUI-Spalte und keinen Warnhinweis fuer "
               ",gehalten, aber nicht bewertbar'. Die Kette ist zu diesen "
               "Werten schlicht STUMM: kein Nachkauf, kein Verkauf, keine "
               "Begruendung. \u27a4 GENAU DAS WAR DER URSPRUNG DES PAKETS "
               "(Nutzerhinweis 08.09.: *,es muessen die Daten zur Bewertung "
               "fuer das Asset vorhanden sein bzw. das Asset in der "
               "Ablaufkette sauber aufgenommen werden'*) - die Meldeluecke "
               "im Betrieb ist geblieben, nur die Suite sieht sie. "
               "\u26a0\ufe0f NICHT GEBAUT, UND ZWAR ABSICHTLICH: eine neue "
               "Mailzeile gehoert in Schritt 41, dessen Vorgabe lautet "
               "*,erst pruefen, DANN straffen - wer kuerzt, bevor er weiss, "
               "was fehlt, kuerzt das Falsche'*. Eine Zeile hinzuzufuegen, "
               "bevor die Mail geprueft ist, arbeitet gegen diese "
               "Reihenfolge. \u27a4 NUTZERENTSCHEIDUNG: soll die Mail eine "
               "Zeile ,gehalten, nicht bewertbar (Grund)' fuehren - und "
               "wenn ja, fuer alle drei oder nur fuer Kernwerte?", "abgeloest",
               "Suche in agent/ und ui/ 13.09.; Nutzerhinweis 08.09.; "
               "Schritt 41", "2.442, 2.442-vier", "Die Mailzeile ist gebaut (2.442): `stumme_bestaende()` "
                     "meldet jede gehaltene Kryptoposition mit zu kurzer "
                     "Kursreihe im Abschnitt 'STUMM: GEHALTEN, ABER NICHT "
                     "BEWERTBAR', und der Betreff nennt sie. Die Stille ist "
                     "damit beendet. Was NICHT geschlossen ist: die Luecke "
                     "selbst - die Reihen bleiben zu kurz, bis sie lang genug "
                     "sind (2.441-warten).", "Produktionssicherung 2026-09-12_0646 gegen die lokale Kopie (OHLC-Stand 2026-08-19); messdaten.db Stand 13.09.2026"),
    Befundlage("2.440", "\u2714\u2714\u2714 WARUM DER GEMESSENE OPTIMALSTOP BEIM "
               "BP-SATZ DER SCHLECHTERE IST - und die Antwort lautet: DER "
               "STOP IST DORT ZU ENG. Nutzerfrage 13.09.: *,warum ist der "
               "gemessene Optimalstop der schlechtere? Wie koennte man das "
               "optimieren, ist der BP-Stop zu eng oder zu weit?'* "
               "\u27a4 DIE MECHANIK: `kosten_r = 2 x Satz / stop_rel`. Bei "
               "festem Risikobudget kauft ein WEITER Stop eine KLEINERE "
               "Position, und die Gebuehr faellt auf den Positionswert - in "
               "R gemessen wird sie also kleiner, je weiter der Stop ist. "
               "Der gemessene Ertrag hat sein Maximum bei 7-9 %%, die "
               "Gebuehr ihr Minimum am weiten Ende. Beim teuren Satz "
               "gewinnt die Gebuehr. \u27a4 NETTO GERECHNET (gemessener EW "
               "minus Gebuehr, LONG H10): bei 0,30 %% ist es FLACH - 8 %% "
               "-0,019 \u00b7 12 %% -0,012 \u00b7 20 %% -0,016 R, und die "
               "Unterschiede von 0,004 bis 0,007 R liegen UNTER der "
               "Aufloesung von 0,010 bis 0,020 R (2.435). Bei 1,50 %% ist es "
               "eindeutig: 8 %% -0,319 \u00b7 12 %% -0,212 \u00b7 20 %% -0,136 R - "
               "Unterschiede von 0,1 bis 0,2 R, weit ueber der Aufloesung. "
               "\u26a0\ufe0f ANTWORT: beim Standardsatz ist die Weite egal, beim "
               "BP-Satz ist sie ZU ENG", "gilt",
               "messe_stopweite_historisch mit crv-Parameter, Lauf 13.09.; "
               "vergleiche_hebel_und_mailrechnung.py", "", "", "messmenge.V1, 534 Symbole, 32.040 Anker, H10 LONG, Netto = gemessener EW minus 2 x Satz / stop_rel, Stand 13.09.2026"),
    Befundlage("2.440-grenze", "\u26a0\ufe0f\u26a0\ufe0f ABER AUFWEITEN SCHLIESST DIE "
               "LUECKE NICHT - es halbiert sie. Zur Nutzerannahme *,wenn "
               "der Hebel wie geplant funktioniert, sollte das erreichbar "
               "sein'*: nachgerechnet, und die Antwort ist NEIN, jedenfalls "
               "nicht ueber die Stopweite. \u27a4 IN TREFFERQUOTEN (CRV 2, "
               "1,50 %%): noetig sind bei 8 %% Stop 45,8 %%, bei 12 %% 41,7 %%, "
               "bei 20 %% 38,3 %%. Die Kette schaetzt heute rund 33 bis 34 %% "
               "(Basisrate 33,3 %% plus Beitraege). Aufweiten von 8 %% auf "
               "20 %% verkleinert die Luecke also von rund 12 auf rund 5 "
               "Prozentpunkte - es beseitigt sie nicht. \u27a4 IN R "
               "GERECHNET dasselbe: das Netto bleibt bei 20 %% mit -0,136 R "
               "negativ, und der hoechste ueberhaupt gemessene Roh-EW ist "
               "+0,056 R bei 8 %%. \u26a0\ufe0f DIE GROESSENORDNUNG IST DER "
               "PUNKT: die Gebuehr bei 1,50 %% und 8 %% Stop ist 0,375 R, "
               "waehrend die GESAMTE Spanne, die die Stopweite ueberhaupt "
               "hergibt, +-0,04 R betraegt (2.435-optimum). Die Gebuehr ist "
               "das Zehnfache des groessten Hebels, den wir an dieser "
               "Schraube haben", "gilt",
               "Netto-Rechnung 13.09.; Befund 2.435-optimum", "", "", "messmenge.V1, 534 Symbole, 32.040 Anker, H10 LONG, Netto = gemessener EW minus 2 x Satz / stop_rel, Stand 13.09.2026"),
    Befundlage("2.440-crv", "\u2716\u2716 UND DIE NAHELIEGENDE LOESUNG TRAEGT "
               "NICHT: CRV ANHEBEN HILFT NICHT. Die Huerdenformel "
               "`(1 + kosten_r) / (1 + CRV)` legt es nahe - CRV steht im "
               "NENNER, also muesste ein hoeheres CRV die Huerde stark "
               "senken. Tut es auch: bei 1,50 %% und 8 %% Stop faellt sie von "
               "45,8 %% (CRV 2) auf 34,4 %% (CRV 3). \u26a0\u26a0 GEMESSEN "
               "PASSIERT TROTZDEM NICHTS: derselbe Lauf mit CRV 3 statt 2 "
               "ergibt bei 8 %% einen Roh-EW von +0,058 statt +0,056 R, und "
               "NETTO bei 1,50 %% -0,317 statt -0,319 R. Bei 20 %%: -0,141 "
               "statt -0,136. \u27a4 DER GRUND: die Huerde sinkt, weil ein "
               "Treffer mehr einbringt - aber die TREFFERQUOTE faellt in "
               "genau demselben Mass, weil das Ziel weiter weg liegt. Beide "
               "Effekte heben sich auf. \u26a0\ufe0f\u26a0\ufe0f LEHRE: die noetige "
               "Trefferquote ALLEIN ist eine irrefuehrende Kennzahl. Sie "
               "haette hier eine Loesung nahegelegt, die es nicht gibt - "
               "erst der gemessene Erwartungswert entscheidet. Ich war "
               "selbst dabei, CRV als Hebel vorzuschlagen", "gilt",
               "messe_stopweite_historisch crv=3.0 gegen crv=2.0, Lauf "
               "13.09., je 32.040 Anker", "", "", "messmenge.V1, 534 Symbole, 32.040 Anker, H10 LONG, Netto = gemessener EW minus 2 x Satz / stop_rel, Stand 13.09.2026"),
    Befundlage("2.440-was-hilft", "\u27a4 WAS BEIM BP-SATZ TATSAECHLICH "
               "HILFT - der Reihe nach, mit Zahlen. (1) DEN STOP AUFWEITEN: "
               "von 8 %% auf 12-20 %% bringt +0,11 bis +0,18 R netto und "
               "verkleinert die Quotenluecke von 12 auf 5 Punkte. Das ist "
               "der einzige Hebel, der IN der Stopfrage liegt - und er "
               "reicht nicht allein. \u26a0\ufe0f Er ist ausserdem nicht gratis: "
               "`hebel` ist proportional zu 1/stop_rel, 20 %% ergibt 2,5x "
               "statt 5x. (2) DIE TREFFERQUOTE HEBEN - rund 5 Prozentpunkte "
               "fehlen bei 20 %% Stop. Bei CRV 2 ist ein Prozentpunkt rund "
               "0,03 R wert; das ist die Aufgabe der Beitraege und damit "
               "des laufenden Umbaus, nicht der Stopregel. (3) DEN "
               "HANDELSPLATZ: bei 0,30 %% steht dasselbe System bei -0,019 R "
               "netto statt -0,319 R - Faktor 17. Die gesamte Luecke bei BP "
               "IST die Gebuehr. \u2716 WAS NICHT HILFT: CRV (2.440-crv), und "
               "die Gebuehr in die Bewertung zu nehmen (Regel 2 - sie ist "
               "eine Eigenschaft des Handelsplatzes, nicht des Trades). "
               "\u26a0\ufe0f KEINE AENDERUNG VORGENOMMEN: `stop_ziel_atr` bleibt "
               "2,5. Eine handelsplatzabhaengige Stopweite waere eine "
               "Gebuehr in der Bewertung durch die Hintertuer - wenn, dann "
               "als bewusste Nutzerentscheidung", "offen",
               "Netto-Rechnung 13.09.; Befunde 2.435-optimum, 2.439-spannung",
               "", "", "messmenge.V1, 534 Symbole, 32.040 Anker, H10 LONG, Netto = gemessener EW minus 2 x Satz / stop_rel, Stand 13.09.2026"),
    Befundlage("2.439", "\u2714\u2714\u2714 REGEL 2 AM HEBEL - GEPRUEFT, "
               "GEGENGEPRUEFT, UND DIE NAHT LIEGT RICHTIG. Nutzerabgleich "
               "13.09.: *,neutrale Bewertung fuer die Signale und "
               "Empfehlung, Wirtschaftlichkeit und Rechnung (Gebuehren 0,3 "
               "und 1,5) erfolgt im eMail'* - praezisiert: *,ich rede vom "
               "Hebel'*. \u27a4 AN DER QUELLE NACHGESEHEN, nicht erinnert: "
               "`betraege.hebelrechnung` rechnet `kelly = (q x (1+c) - 1) / "
               "c` - Quote und CRV, KEIN Gebuehrenparameter in der "
               "Signatur. Bei q = 33,3 %% und CRV 2 wird Kelly exakt 0, also "
               "kein Hebel, also Spot: das ist der GEBUEHRENFREIE "
               "Break-even. Mit 0,30 %% laege die Huerde bei 34,3 %%, mit "
               "1,50 %% bei 38,3 %% - der Hebel trifft keine davon. "
               "`potential.rechne` ruft `wahrscheinlichkeit` mit "
               "`gebuehr_je_seite=0.0`; dort ist der Break-even exakt "
               "1/(1+CRV) und `kosten_r` exakt 0. Und die Gegenrichtung "
               "stimmt auch: die Mail fuehrt beide Saetze mit "
               "`kosten_r = 2 x Satz / stop_rel` plus Finanzierung. "
               "\u2714 NEUES PAKET `Gebuehrengrenze` (7 Pruefungen) bewacht "
               "es - vorher stand die Trennung nur als Kommentar im Code, "
               "und ein Kommentar haelt niemanden auf", "gilt",
               "agent/betraege.hebelrechnung; agent/potential.py Zeile 381; "
               "agent/wahrscheinlichkeit.py Zeile 776; "
               "pruefe_pakete.py --paket Gebuehrengrenze"),
    Befundlage("2.439-naht", "\u2714\u2714 UND DIE NAHT LIEGT AN DER RICHTIGEN "
               "STELLE - das ist die eigentliche Fachfrage, nicht ob beide "
               "Seiten dieselbe Zahl sagen (das duerfen sie gar nicht). Die "
               "Kostenseite zerfaellt in ZWEI Teile, und sie verhalten sich "
               "verschieden. \u27a4 DIE HANDELSGEBUEHR HAENGT NICHT AM HEBEL: "
               "`kosten_r = 2 x Satz / stop_rel`, und das Nominal (Einsatz x "
               "Hebel) steht in Zaehler UND Nenner. Nachgerechnet bei 8 %% "
               "Stop und 1,50 %%: 0,3750 R bei 1x, 2x, 3x UND 5x - dieselbe "
               "Zahl. Sie KANN die Hebelentscheidung nicht verzerren, auch "
               "nicht theoretisch. \u27a4 NUR DIE FINANZIERUNG WAECHST "
               "(geliehenes Kapital = Nominal x (1 - 1/Hebel)): 0,0000 \u00b7 "
               "0,0750 \u00b7 0,1000 \u00b7 0,1200 R. \u26a0\ufe0f DAMIT IST DER PREIS DER "
               "TRENNUNG BEZIFFERBAR - das Quotenfenster, in dem ein Trade "
               "UNGEHEBELT tragen wuerde und GEHEBELT nicht: 5 %% Stop 6,4 "
               "Prozentpunkte \u00b7 8 %% 4,0 \u00b7 12 %% 2,5 \u00b7 20 %% 1,2. Es ist "
               "am ENGEN Stop am breitesten. \u27a4 KEIN FEHLER, sondern der "
               "Preis: die Bewertung DARF ihn nicht kennen, die Mail MUSS "
               "ihn zeigen - und sie tut es, weil sie die Huerde je "
               "Gebuehrensatz MIT Finanzierung ausweist", "gilt",
               "vergleiche_hebel_und_mailrechnung.py, Lauf 13.09."),
    Befundlage("2.439-spannung", "\u26a0\ufe0f\u26a0\ufe0f DIE TRENNUNG IST NICHT "
               "KOSMETISCH - SIE AENDERT DIE ANTWORT, UND ZWAR STARK. "
               "`kosten_r = 2 x Satz / stop_rel` waechst, je ENGER der Stop "
               "ist: bei 1,50 %% sind das 1,50 R bei 2 %% Stop, 0,375 R bei "
               "8 %%, 0,150 R bei 20 %%. \u27a4 ZUM VERGLEICH: die gesamten "
               "Weitenunterschiede, die 2.435-optimum GEBUEHRENFREI gemessen "
               "hat, liegen bei +-0,04 R. Die Gebuehr beim teuren Satz ist "
               "also rund das ZEHNFACHE des gemessenen Effekts - und sie "
               "zeigt in die ANDERE Richtung. \u26a0\ufe0f GEGENUEBERGESTELLT "
               "(Kapital 20.000 EUR, 5 Tage, CRV 2): bei 5 %% Stop traegt "
               "sich beim Satz 1,50 %% NICHT EINMAL eine Quote von 50 %% "
               "(-9,7 Prozentpunkte); bei 20 %% Stop traegt schon 40 %%. Bei "
               "0,30 %% dagegen traegt 8 %% Stop ab 40 %%. \u27a4 FACHLICH "
               "RICHTIG BLEIBT DIE TRENNUNG: eine Gebuehr ist eine "
               "Eigenschaft des HANDELSPLATZES, nicht des Trades - wer sie "
               "in die Bewertung nimmt, bekommt fuer denselben Trade zwei "
               "verschiedene Potentiale, je nach Broker. \u26a0\u26a0 ABER SIE "
               "MUSS SICHTBAR BLEIBEN: beim teuren Satz ist der gemessene "
               "Optimalstop (7-9 %%) wirtschaftlich der unguenstigste "
               "Bereich. Das ist eine Aussage fuer die MAIL und "
               "gegebenenfalls fuer die Wahl des Handelsplatzes - keine "
               "Aufforderung, `stop_ziel_atr` zu bewegen", "gilt",
               "vergleiche_hebel_und_mailrechnung.py; Befunde 2.435-optimum, "
               "2.437"),
    Befundlage("2.438", "\u26a0\ufe0f DIE SCHAERFERE FRAGE, DIE VON 2.400-hebel "
               "UEBRIG BLEIBT: IST DER STOP DES MODELLS BESSER ALS DIE "
               "REGEL? 2.400-hebel sagte, der Nenner der Hebelkette sei "
               "ungemessen. Das ist seit 2.435-optimum und 2.437 nicht mehr "
               "wahr - die REGEL ist gemessen. Aber im Betrieb kommt der "
               "Stop in 81,5 %% der Faelle NICHT aus der Regel, sondern aus "
               "dem Widerlegungspreis des Modells. \u2714 WAS DAFUER SPRICHT: "
               "der Median dieser 1.446 Modellzonen liegt bei 8,0 %% - genau "
               "auf dem gemessenen Gipfel (7 bis 9 %%). Die Verteilung ist "
               "also nicht falsch. \u26a0\ufe0f WAS OFFEN IST: ob die "
               "EINZELENTSCHEIDUNG traegt. Ein Modell, das im Mittel richtig "
               "liegt, kann im Einzelfall trotzdem schlechter sein als eine "
               "feste Regel - dann waere der Widerlegungspreis Zierde. "
               "\u27a4 MESSBAR MIT DEM VORHANDENEN WERKZEUG: je Signal den "
               "Modellstop gegen den Regelstop (2,5 x ATR, gedeckelt) am "
               "SELBEN Anker rechnen - gepaart, wie in "
               "`messe_stopweite_historisch`. \u26a0\ufe0f NICHT IN SCHRITT 46: "
               "das ist eine Messung, und 46 ist ausdruecklich ein "
               "Abbildungsschritt (,KEINE neue Messung')", "offen",
               "Befunde 2.400-hebel, 2.435-optimum, 2.437; "
               "notebook_diagnose.json hebel_signals, 1.446 Modellzonen"),
    Befundlage("2.437", "\u2714\u2714\u2714 DIE DECKELFRAGE IST ENTSCHIEDEN - "
               "`stop_max_relativ` = 25 %% BLEIBT. Und meine eigene Vorlage "
               "dazu (2.435-deckel) war FALSCH. Nutzerfrage 13.09.: *,ok "
               "also der aktuelle Wert ist schlechter und was ist deine "
               "Empfehlung? - offenbar ist eine korrekte Aenderung nur "
               "positiv oder wenn die richtigen Trades in den Hebel "
               "fallen'*. Genau das war der Fehler: ich hatte eine "
               "UNBEDINGTE Messung (alle Anker) auf eine BEDINGTE Teilmenge "
               "angewendet (die Lagen, die der Deckel trifft). "
               "\u27a4 NACHGEMESSEN, GETRENNT NACH LAGE (gepaart gegen 25 %%, "
               "also gegen den Stop, den diese Lagen HEUTE bekommen): "
               "\u26a0\ufe0f\u26a0\ufe0f DORT WO DER DECKEL BINDET (ATR-Stop ueber "
               "25 %%, 30.297 Anker, 520 Symbole) BRINGT ENGER NICHTS: LONG "
               "8 %% +0,002 \u00b7 10 %% +0,007 \u00b7 12 %% +0,003 \u00b7 15 %% -0,001 \u00b7 "
               "20 %% -0,005 - JEDES Band schliesst die Null ein. Und SHORT "
               "wuerde SCHADEN: 8 %% -0,026 \u00b7 12 %% -0,029 \u00b7 20 %% -0,010, "
               "alle fuenf trennbar unter null. \u27a4 DER GRUND IST "
               "EINSICHTIG: das sind die schwankungsstarken Lagen. Ein "
               "8-%%-Stop ist dort rund 0,8 ATR - er wird vom Rauschen "
               "abgeraeumt. Der Vorteil aus der kleineren Position ist in R "
               "bereits herausgerechnet", "gilt",
               "messe_stopweite_historisch.sammle(atr_band=...) 13.09. "
               "abends; Lauf ueber messmenge.V1", "", "", "messmenge.V1, 534 Krypto-Reihen, ATR nach indicators.atr_wilder, je Band 60 Anker x 520 Symbole, CRV 2,0, Stand 13.09.2026"),
    Befundlage("2.437-grund", "\u2714\u2714 UND DER DECKEL IST GAR KEINE "
               "EINGESTELLTE WEITE - ER IST EINE NOTBREMSE. Nutzerhinweis "
               "13.09.: *,der Deckel war eine vorlaeufige Absicherung aber "
               "du kennst sicher den echten Grund'*. Er hat recht, und der "
               "Grund steht woertlich im Code: *,OBERGRENZE - NEU, es gab "
               "bisher keine. Ein Stop von 40 %% faellt durch jede "
               "Untergrenze und ruiniert trotzdem die Rechnung: er macht "
               "die Position winzig und die Haltedauer unbegrenzt.'* "
               "\u27a4 DAMIT IST DIE FRAGE FALSCH GESTELLT GEWESEN. Sie "
               "lautete ,ist 25 %% die beste Weite' - sie lautet ,faengt die "
               "Notbremse noch, was sie fangen soll'. \u2714 JA: an den 1.446 "
               "Modellzonen des Exports liegen 7 (0,5 %%) ueber 25 %%, das "
               "Maximum bei 34,5 %%. Der Ausreisser existiert, er ist selten, "
               "und er wird gefangen. \u26a0\ufe0f EINE SENKUNG AUF 12 %% WAERE "
               "ETWAS ANDERES: 252 von 1.446 Modellzonen (17,4 %%) liegen "
               "darueber. Aus der Notbremse wuerde die faktische Stopregel "
               "fuer jedes sechste Signal - eine Sicherheitsgrenze, die "
               "still die Stoplogik uebernimmt", "gilt",
               "agent/entscheidungsrechnung.py Zeile 196 (Ursprungskommentar); "
               "notebook_diagnose.json hebel_signals, 1.446 Zonen", "", "", "messmenge.V1, 534 Krypto-Reihen, ATR nach indicators.atr_wilder, je Band 60 Anker x 520 Symbole, CRV 2,0, Stand 13.09.2026"),
    Befundlage("2.437-atr", "\u26a0\ufe0f\u26a0\ufe0f WAS DABEI AUFFIEL UND EIN "
               "EIGENES THEMA IST: NICHT DER DECKEL IST DIE SCHWACHSTELLE, "
               "SONDERN DER ATR-RUECKFALL IM MITTELFELD. Verteilung des "
               "ATR-Rueckfallstops (2,5 x ATR / Kurs) ueber 677.440 "
               "Handelstage: unter 10 %% nur 5,2 %% \u00b7 10-15 %% 15,3 %% \u00b7 "
               "15-20 %% 25,2 %% \u00b7 20-25 %% 21,8 %% \u00b7 ueber 25 %% 32,5 %%. "
               "\u27a4 IN DER GRUPPE 15 BIS 25 %% - das sind 47 %% aller Tage, "
               "und sie werden NICHT gedeckelt - waere ein engerer Stop "
               "LONG messbar besser: 8 %% +0,035 \u00b7 10 %% +0,035 \u00b7 12 %% "
               "+0,030 \u00b7 15 %% +0,022 \u00b7 20 %% +0,007, alle fuenf trennbar "
               "ueber null. SHORT dagegen flach (groesste Abweichung "
               "0,005, kein Band trennt). \u26a0\ufe0f DAS IST KEIN AUFTRAG ZUR "
               "AENDERUNG: es beruehrt `stop_ziel_atr`, dessen Optimum "
               "2.435-optimum unbedingt bei 7-9 %% gemessen hat, und es ist "
               "RICHTUNGSABHAENGIG - eine Regel, die nur LONG hilft und "
               "SHORT nichts bringt, ist ein eigener Schritt mit eigener "
               "Gegenpruefung. \u27a4 WICHTIG FUER DIE EINORDNUNG: im "
               "LAUFENDEN Betrieb kommt der Stop in 81,5 %% der Faelle aus "
               "dem Widerlegungspreis des Modells, nicht aus dem "
               "ATR-Rueckfall - der Median der 1.446 Modellzonen liegt bei "
               "8,0 %%, also genau auf dem gemessenen Gipfel", "offen",
               "Verteilung ueber messmenge.V1 13.09.; Befund 2.435-optimum; "
               "notebook_diagnose.json hebel_signals", "", "", "messmenge.V1, 534 Krypto-Reihen, ATR nach indicators.atr_wilder, je Band 60 Anker x 520 Symbole, CRV 2,0, Stand 13.09.2026"),
    Befundlage("2.436", "\u26a0\ufe0f\u26a0\ufe0f DIE DREI ROTEN ZEILEN DER SUITE - "
               "GEKLAERT STATT NUR GENANNT (R-R9). Nach Schritt 47 stehen "
               "2.385 Pruefungen, davon 3 rot, ALLE im Paket Neuaufnahme "
               "und alle DATENSTAND, nicht Logik. Gegengeprueft: "
               "`git diff HEAD -- pruefe_neuaufnahme.py` zeigt an diesen "
               "drei Pruefungen KEINE Aenderung - sie sind nicht heute "
               "entstanden. \u27a4 (1) DREI GEHALTENE POSITIONEN OHNE "
               "MESSREIHE: ASTER (nur 318 USD-Tage), MON (269) - beide "
               "unter der Mindestlaenge - und CANTON, das auch in der "
               "PRODUKTION keine hat. Ohne Messreihe kann die Kette den "
               "Wert weder zum Nachkauf noch zum Verkauf bewerten. "
               "\u27a4 (2) CANTON IST ZUSAETZLICH KERNWERT OHNE JEDEN "
               "BEITRAG - bei Meme- und Smallcap-Werten ist das laut "
               "Nutzervorgabe unkritisch, bei einem Kernwert nicht. Es ist "
               "dieselbe Ursache wie (1), nicht ein zweiter Fall. "
               "\u27a4 (3) DIE NICHT-KRYPTO-MESSBASEN SIND 10 TAGE ALT "
               "(Median 2026-09-03; aktien 470/470, rohstoffe 35/35, "
               "themen_etf 293/293 aelter als 7 Tage). \u26a0\ufe0f Das ist am "
               "DESKTOP zu erwarten - er faehrt nach stehender Vorgabe nie "
               "gegen die Produktiv-DB, die Auffrischung laeuft am "
               "Notebook. Ob es dort auch rot ist, ist NICHT geprueft und "
               "waere die eigentliche Frage. \u27a4 WAS ZU TUN IST: (1) und "
               "(2) brauchen eine Entscheidung zur Mindestlaenge oder eine "
               "Quelle fuer CANTON; (3) braucht eine Messung AM NOTEBOOK, "
               "bevor daraus ein Befund wird. Beides gehoert NICHT in "
               "Schritt 47 und wurde dort auch nicht angefasst", "abgeloest",
               "pruefe_pakete.py --paket Neuaufnahme, Lauf 13.09. abends; "
               "git diff HEAD -- pruefe_neuaufnahme.py",
               abgeloest_durch="2.441, 2.441-warten, 2.441-still",
               warum="Der Befund uebernahm die Aussage der Pruefung, CANTON "
                     "habe 'auch in der PRODUKTION keine Kursreihe'. Das war "
                     "falsch: gelesen wurde die LOKALE Kopie, deren OHLC am "
                     "2026-08-19 endet. In der Produktionssicherung vom 12.09. "
                     "hat CANTON 63 USD-Tage. Auch die Zahlen fuer ASTER (318 "
                     "statt 342) und MON (269 statt 293) stammten aus der "
                     "veralteten Kopie. Und die Vermutung, die Messbasen-"
                     "Frische sei 'am Notebook zu messen', war ebenfalls falsch"
                     " - die Nicht-Krypto-Reihen kommen aus yfinance, und die "
                     "Meldung war ein Waehrungsfehler (Kalender- statt "
                     "Handelstage). Ich habe eine Pruefungsausgabe "
                     "weitergeschrieben, statt sie an der Quelle "
                     "gegenzupruefen."),
    Befundlage("2.435", "\u2714\u2714\u2714 DIE LOESUNG TRAEGT - DIE AUFLOESUNG IST DA. "
               "`messe_stopweite_historisch.py` gebaut und ueber die volle "
               "Messmenge gelaufen: 534 Symbole, 32.040 Anker je Lauf, jeder "
               "Anker mit ALLEN sechs Weiten (GEPAART), drei Horizonte, beide "
               "Richtungen. \u27a4 DIE AUFLOESUNG FAELLT VON 0,40 R AUF 0,010 "
               "BIS 0,020 R - Faktor 20 bis 40. Gemessen mit einer FEINEREN "
               "Staerkenleiter (0,002 / 0,005 / 0,01 / 0,02 ...), weil die "
               "Normleiter bei 0,02 anfaengt und ,ab 0,02' dort nur der BODEN "
               "der Leiter waere, keine Messung. Jeder gemessene Effekt liegt "
               "damit UEBER der Aufloesung. \u26a0\ufe0f Die Tagesklammer ist per "
               "Konstruktion erfuellt, nicht umgangen: beide Weiten werden am "
               "SELBEN Anker desselben Tages gerechnet", "gilt",
               "messe_stopweite_historisch.py Lauf 13.09.; "
               "pruefe_stopweite_gegen.py Probe 1", "", "", "messmenge.V1, 534 Krypto-Reihen ueber 400 Tagen, 32.040 Anker je Lauf, CRV 2,0, Kosten 0,00 %, Stand 13.09.2026"),
    Befundlage("2.435-optimum", "\u2714\u2714\u2714 UND DER HEUTIGE BETRIEBSPUNKT IST "
               "DER GIPFEL - `stop_ziel_atr` = 2,5 HAT JETZT EINEN EIGENEN "
               "BEFUND UND BLEIBT. Feinraster in Ein-Prozent-Schritten um den "
               "Betriebspunkt (LONG, H10, gepaart gegen 8 %%): 5 %% -0,0354 \u00b7 "
               "6 %% -0,0177 \u00b7 7 %% -0,0013 \u00b7 [8 %% Bezug] \u00b7 9 %% -0,0046 \u00b7 "
               "10 %% -0,0127 \u00b7 12 %% -0,0182. \u27a4 EIN ECHTES INNERES "
               "MAXIMUM: 7 bis 9 %% bilden ein Plateau, das nicht trennbar "
               "ist, ALLES darum herum ist messbar schlechter. `stop_ziel_atr` "
               "= 2,5 trifft bei Krypto rund 7,5 bis 8 %% - also mitten hinein. "
               "\u26a0\ufe0f DAS SCHLIESST DIE HAELFTE VON 2.431-grenzen, DIE "
               "`stop_ziel_atr` BETRIFFT: die Zahl stand auf fremden "
               "Praxisstandards, jetzt steht sie auf 32.040 gepaarten Ankern "
               "ueber 534 Symbole. \u27a4 SIE WIRD NICHT GEAENDERT - und das ist "
               "ein Ergebnis, kein Aufschub", "gilt",
               "pruefe_stopweite_gegen.py Probe 8, Feinraster 5-12 %%", "", "",
               "messmenge.V1, 534 Krypto-Reihen ueber 400 Tagen, 32.040 "
               "Anker je Lauf, CRV 2,0, Kosten 0,00 %, Stand 13.09.2026"),
    Befundlage("2.435-gleichtag", "\u26a0\ufe0f\u26a0\ufe0f\u26a0\ufe0f DIE ENGE SEITE IST AUS "
               "TAGESDATEN NICHT ENTSCHEIDBAR - UND DAMIT IST ,ENGE STOPS "
               "SCHADEN' EIN HINWEIS, KEIN BEFUND. Die Ehrenrunde hat es "
               "gefangen: dreht man die Gleichtagsregel um (Ziel vor Stop "
               "statt Stop vor Ziel), wechselt das Vorzeichen vollstaendig. "
               "LONG H10 gepaart gegen 8 %%: 2 %% -0,240 gegen +0,309 \u00b7 3 %% "
               "-0,127 gegen +0,110 \u00b7 5 %% -0,035 gegen +0,019. \u27a4 DER "
               "GRUND IST MECHANISCH: bei 2 %% Stop und 4 %% Ziel beruehrt eine "
               "Krypto-Tageskerze sehr oft BEIDE Marken, und aus Tagesdaten "
               "ist die Reihenfolge nicht bekannt. 97 %% der Anker loesen bei "
               "2 %% auf - fast jeder davon ist von dieser Annahme betroffen. "
               "\u26a0\ufe0f WAS TROTZDEM STEHT: auf der WEITEN Seite sind sich "
               "beide Regeln einig (9 %%, 10 %%, 12 %% unter beiden Regeln nicht "
               "besser als 8 %%) - die Entscheidung ,nicht aufweiten' haengt "
               "NICHT an der Annahme. \u27a4 DIE LOESUNG, falls die enge Seite "
               "je gebraucht wird: Intraday-Kerzen (1h) - dort ist die "
               "Reihenfolge beobachtbar. Nicht gebaut, weil die Entscheidung "
               "sie nicht braucht", "gilt",
               "pruefe_stopweite_gegen.py Proben 2 und 3", "", "", "messmenge.V1, 534 Krypto-Reihen ueber 400 Tagen, 32.040 Anker je Lauf, CRV 2,0, Kosten 0,00 %, Stand 13.09.2026"),
    Befundlage("2.435-richtung", "\u26a0\ufe0f LONG UND SHORT VERHALTEN SICH "
               "VERSCHIEDEN - UND BEI SHORT IST DIE STOPWEITE EGAL. LONG: das "
               "Feinraster zeigt ein klares Maximum bei 7-9 %%. SHORT: im "
               "ganzen Raster 5-12 %% trennt sich KEINE Weite von 8 %% (groesste "
               "Differenz +0,0042). \u27a4 FUER DEN BETRIEB heisst das: die "
               "Stopregel ist fuer LONG belegt und fuer SHORT unschaedlich - "
               "eine richtungsabhaengige Stopweite waere nicht begruendet. "
               "\u26a0\ufe0f SEPARAT UND NICHT ZU VERWECHSELN: der Erwartungswert "
               "SELBST unterscheidet sich (LONG bei 8 %%: +0,020 / +0,056 / "
               "+0,044 R ueber H5/H10/H20, SHORT: -0,033 / -0,039 / -0,025). "
               "Das ist die Drift der Messmenge, GEOMETRIE und kein Beitrag - "
               "ein Zufallseinstieg long verdient historisch, short verliert. "
               "Als Signalgeber taugt es nicht (Regel 4: ein Fakt ist keine "
               "Begruendung), als Hintergrund fuer die Richtungsfrage schon",
               "gilt", "messe_stopweite_historisch.py Lauf 13.09.; "
               "pruefe_stopweite_gegen.py Probe 8", "", "", "messmenge.V1, 534 Krypto-Reihen ueber 400 Tagen, 32.040 Anker je Lauf, CRV 2,0, Kosten 0,00 %, Stand 13.09.2026"),
    Befundlage("2.435-stabil", "\u2714\u2714 WAS DIE EHRENRUNDE SONST GEPRUEFT HAT - "
               "und wo das Bild WEICH ist. \u2714 SAAT UND ANKERZAHL (Probe 4): "
               "zwei weitere Saaten und die halbe Ankerzahl aendern die enge "
               "Seite kaum (2 %%: -0,240 / -0,235 / -0,241); 12 %% wandert "
               "zwischen -0,018 und -0,004 - dort liegt der Effekt an der "
               "Aufloesungsgrenze. \u2714 BEZUGSPUNKT (Probe 5): gegen 5 %% und "
               "gegen 12 %% nachgerechnet, die Rangfolge bleibt; 8 %% schlaegt "
               "5 %% (+0,035) UND 12 %% (+0,018). Die Additivitaetsprobe - "
               "d(w gegen 5 %%) minus d(8 %% gegen 5 %%) muss exakt d(w gegen "
               "8 %%) sein - stimmt auf 2,8e-17. \u26a0\ufe0f ZEITFENSTER (Probe 6, "
               "die WEICHE Stelle): ab 2025 schwaecht sich alles ab (LONG 2 %%: "
               "-0,240 ueber die ganze Historie, -0,096 ab 2025), und SHORT "
               "dreht sogar (ganze Historie 20 %%: +0,009, ab 2025: -0,040). "
               "\u27a4 WAS DAVON UNBERUEHRT BLEIBT: in KEINEM Fenster und KEINER "
               "Richtung ist eine Weite ueber 9 %% je BESSER als 8 %%. Die "
               "Entscheidung steht also auch im weichen Teil", "gilt",
               "pruefe_stopweite_gegen.py Proben 4, 5, 6", "", "", "messmenge.V1, 534 Krypto-Reihen ueber 400 Tagen, 32.040 Anker je Lauf, CRV 2,0, Kosten 0,00 %, Stand 13.09.2026"),
    Befundlage("2.435-deckel", "\u26a0\ufe0f\u26a0\ufe0f OFFEN UND DEM NUTZER VORZULEGEN: "
               "`stop_max_relativ` = 25 %% ERLAUBT WEITEN, DIE MESSBAR "
               "SCHLECHTER SIND. Die zweite Haelfte von 2.431-grenzen ist "
               "damit NICHT geschlossen, aber zum ersten Mal beziffert. "
               "Gemessen (LONG, gepaart gegen 8 %%): 12 %% -0,018 \u00b7 20 %% "
               "-0,041. Der Deckel laesst bis 25 %% zu. \u27a4 DIE AUSWIRKUNG AUF "
               "DIE KETTE, GERECHNET: `hebel = risiko_eur / (einsatz x "
               "stop_rel)` ist streng proportional zu 1/stop_rel, der Faktor "
               "also parameterfrei - 8 %% = 1,00x \u00b7 12 %% = 0,67x \u00b7 20 %% = "
               "0,40x \u00b7 25 %% = 0,32x. Zusaetzlich faellt der "
               "Liquidationsdeckel `hebel_sicher` von 6,14x bei 8 %% auf 3,15x "
               "bei 25 %%. \u26a0\ufe0f EIN WEITER STOP WIRD ALSO DOPPELT "
               "ENTHEBELT - und traegt zugleich schlechter. \u27a4 WAS ICH NICHT "
               "TUE: den Deckel eigenmaechtig senken. Er ist eine "
               "Betriebsgrenze, seine Senkung erhoeht den Hebel genau der "
               "Trades, die heute in Spot fallen - das ist eine "
               "Nutzerentscheidung, keine Messfolge", "abgeloest",
               "pruefe_stopweite_gegen.py Probe 8; agent/entscheidungsrechnung "
               "hebel_sicher, GRENZEN", "2.437, 2.437-grund", "Der Satz 'der Deckel laesst Weiten zu, die messbar "
                     "schlechter sind' nahm eine UNBEDINGTE Messung (alle "
                     "Anker, 20 % gegen 8 %: -0,041 R) und wendete sie auf eine"
                     " BEDINGTE Teilmenge an - die schwankungsstarken Lagen, "
                     "die der Deckel ueberhaupt nur trifft. Dort gemessen "
                     "verschwindet der Effekt: LONG schliesst jedes Band die "
                     "Null ein (groesste Abweichung +0,007), SHORT waere enger "
                     "sogar schlechter (-0,010 bis -0,029). Die Empfehlung "
                     "lautet deshalb: 25 % bleibt unveraendert.", "messmenge.V1, 534 Krypto-Reihen ueber 400 Tagen, 32.040 Anker je Lauf, CRV 2,0, Kosten 0,00 %, Stand 13.09.2026"),
    Befundlage("2.434", "\u2714\u2714\u2714 WORAN DIE AUFLOESUNG SCHEITERT - MECHANISCH, "
               "MIT ZAHLEN (Nutzerauftrag 13.09.: *,woran scheitert die "
               "Pruefung konkret, du zaehlst mir Fehler auf?'*). Er hat "
               "recht: ich hatte rote Zeilen aufgezaehlt statt die Ursache "
               "zu nennen. \u27a4 DIE URSACHE IST DER BLOCK-BOOTSTRAP UEBER "
               "SYMBOLE - und der ist RICHTIG so: mehrere Signale desselben "
               "Symbols teilen dieselbe Kursreihe, ueber Einzelfaelle zu "
               "ziehen ergaebe zu enge Baender. Damit ist die WIRKSAME "
               "Stichprobe die SYMBOLZAHL, nicht die Fallzahl. Gezaehlt: "
               "0-2 %% 38 Faelle aber 14 Symbole \u00b7 2-3 %% 58/13 \u00b7 3-5 %% "
               "201/22 \u00b7 5-8 %% 428/27 \u00b7 8-12 %% 470/28 \u00b7 >12 %% 251 "
               "Faelle und nur 21 SYMBOLE. Die KI-Breite folgt dem genau: "
               "1,695 bei 13 Symbolen, 0,351 bei 21, 0,367 bei 28. "
               "\u26a0\ufe0f 251 Faelle sehen nach viel aus - es sind 21 Symbole", "gilt",
               "messe_stop_abstand_baender, Symbolzaehlung je Band 13.09."),
    Befundlage("2.434-loesung", "\u2714\u2714\u2714 UND ES GIBT EINE LOESUNG - "
               "HISTORISCH SIMULIEREN STATT SIGNALSTICHPROBE. Nutzerfrage "
               "13.09.: *,kann man ueber historische Daten simulieren?'* Ja "
               "- und `messnorm` verlangt es ohnehin: frageart "
               "`geometrie` -> Menge = MESSUNIVERSUM, nicht Signale. Ich "
               "hatte das selbst notiert und die Folge nicht gezogen. "
               "\u27a4 ZWEI HEBEL, und der zweite ist der staerkere. (1) MEHR "
               "SYMBOLE: 536 statt 21, die Bandbreite skaliert mit "
               "1/Wurzel(Symbole) - Faktor 5. (2) GEPAART RECHNEN: heute "
               "bekommt jedes Signal EINE Stopweite, verglichen werden also "
               "verschiedene Signale mit verschiedenen Weiten, und in jedem "
               "Vergleich steckt die Frage ,waren das dieselben Lagen?'. "
               "Historisch kann JEDER Anker mit JEDER Weite gerechnet "
               "werden - dieselbe Lage, nur ein anderer Stop. Die Auswahl "
               "faellt als Stoerquelle weg. \u2714\u2714 VORABTEST GELAUFEN (60 "
               "Symbole, 2.400 Anker, jeder mit sechs Weiten): die "
               "KI-Breite faellt von 0,351 auf 0,069 bis 0,138, die "
               "Aufloesung von 0,40 R auf 0,03 bis 0,07 R - Faktor 6 bis "
               "13, und das mit 60 statt 536 Symbolen", "gilt",
               "Vorabtest 13.09. gegen messmenge.V1; messnorm.FRAGEARTEN"),
    Befundlage("2.434-vorschau", "\u26a0\ufe0f\u26a0\ufe0f UND DAS BILD AENDERT SICH - "
               "VORLAEUFIG, aus dem Vorabtest. Auf der historischen Menge "
               "(60 Symbole, 2.400 gepaarte Anker, H7, CRV 2,0, LONG): "
               "2 %% -0,132 \u00b7 3 %% -0,049 \u00b7 5 %% -0,016 \u00b7 8 %% -0,012 \u00b7 "
               "12 %% +0,019 \u00b7 20 %% -0,001. \u27a4 ENGE STOPS SCHADEN - das "
               "reproduziert. \u26a0\ufe0f\u26a0\ufe0f ABER ,UEBER 12 %% TRAEGT' "
               "REPRODUZIERT NICHT: statt +0,230 R stehen dort +0,019 R. "
               "Der grosse Wert der Signalstichprobe war mit hoher "
               "Wahrscheinlichkeit AUSWAHL - dieselben 21 Symbole, die "
               "einen weiten Stop bekamen. \u26a0\ufe0f DAS IST NOCH KEIN BEFUND: "
               "dem Vorabtest fehlen Basislinie, Tagesklammer, "
               "Trennschaerfe mit gepflanzten Staerken, die volle Menge und "
               "die Gegenrichtung. Er beantwortet EINE Frage - ob die "
               "Aufloesung reicht - und die beantwortet er mit ja", "abgeloest",
               "Vorabtest 13.09.; gegen Befund 2.431",
               abgeloest_durch="2.435-gleichtag",
               warum="Der Vorabtest meldete 'enge Stops schaden - das "
                     "reproduziert' (2 %: -0,132). Die Ehrenrunde zeigt, dass "
                     "dieser Wert vollstaendig an der Gleichtagsregel haengt: "
                     "mit 'Ziel zuerst' steht dort +0,309 statt -0,240. Aus "
                     "Tagesdaten ist die enge Seite nicht entscheidbar. Die "
                     "zweite Haelfte der Vorschau - 'ueber 12 % traegt "
                     "reproduziert NICHT' - hat sich dagegen auf der vollen "
                     "Menge bestaetigt."),
    Befundlage("2.433", "\u26a0\ufe0f\u26a0\ufe0f\u26a0\ufe0f TRENNSCHAERFE UND POSITIVKONTROLLE "
               "KIPPEN 2.431 - UND ZWAR VOLLSTAENDIG. Nachgezogen am 13.09. "
               "auf Nutzerauftrag, in `messe_stop_abstand_baender.py`, "
               "ZENTRIERT gepflanzt (stehende Vorgabe 07.09.: wer auf die "
               "echte Reihe pflanzt, misst den vorhandenen Effekt noch "
               "einmal). H7, Staerkenleiter wie `messnorm.STAERKEN`: 0-2 %% "
               "Trennschaerfe ab 0,40 R, Positivkontrolle 3 von 5 \u00b7 2-3 %% "
               "> 0,40 R, 0 von 5 \u00b7 3-5 %% > 0,40 R, 1 von 5 \u00b7 5-8 %% ab "
               "0,40 R, 5 von 5 \u00b7 8-12 %% ab 0,20 R, 5 von 5 \u00b7 >12 %% ab "
               "0,40 R, 5 von 5. \u27a4 DIE GEMESSENEN EFFEKTE LIEGEN UNTER "
               "DER AUFLOESUNG: >12 %% zeigt +0,230 R, gefunden wuerde erst "
               "0,40 R. \u26a0\ufe0f\u26a0\ufe0f UND ZWEI BAENDER SEHEN GAR NICHTS: bei "
               "2-3 %% und 3-5 %% findet die Anlage selbst einen gepflanzten "
               "Effekt von 0,40 R in 0 bzw. 1 von 5 Ziehungen nicht. Jeder "
               "Nullbefund dort ist bedeutungslos - das ist ,KEIN BEFUND', "
               "nicht ,traegt nicht'", "gilt",
               "messe_stop_abstand_baender.py mit Trennschaerfe und "
               "Positivkontrolle, Lauf 13.09."),
    Befundlage("2.433-nullmodell", "\u26a0\ufe0f\u26a0\ufe0f\u26a0\ufe0f MEIN ZWEITER FEHLER AN "
               "DERSELBEN TABELLE: ICH HABE GEGEN DIE NULL VERGLICHEN, "
               "NICHT GEGEN DAS NULLMODELL. Ich hatte gemeldet: *,nur zwei "
               "Baender schliessen die Null aus - unter 2 %% schadet der "
               "Stop, ueber 12 %% traegt er'*. Der Satz stimmt woertlich "
               "und ist trotzdem falsch: das Nullmodell dieser Messung ist "
               "die BASISLINIE (derselbe Stop, dasselbe CRV, zufaellige "
               "Einstiege), nicht die Zahl 0. Nachgerechnet: 0-2 %% KI "
               "[-0,965;-0,029] gegen Basislinie -0,131 - die Basislinie "
               "liegt IM Band. >12 %% KI [+0,014;+0,366] gegen Basislinie "
               "+0,024 - ebenfalls IM Band. \u27a4 KEIN EINZIGES DER SECHS "
               "BAENDER TRENNT SICH VON SEINER BASISLINIE. Zusammen mit "
               "2.433 heisst das: die Stopweite traegt in keinem Band "
               "nachweisbar, und in zwei Baendern kann die Anlage gar "
               "nichts sehen. \u26a0\ufe0f Die Basislinie stand die ganze Zeit in "
               "der Tabelle, eine Spalte neben dem Band - ich habe die "
               "falsche Spalte gelesen", "gilt",
               "messe_stop_abstand_baender Ausgabe 13.09., nachgerechnet"),
    Befundlage("2.433-folge", "\u27a4 WAS DARAUS FUER SCHRITT 47 FOLGT - und was "
               "NICHT. \u26a0\ufe0f\u26a0\ufe0f `stop_ziel_atr` DARF AUF DIESER GRUNDLAGE "
               "NICHT GEAENDERT WERDEN. Meine Empfehlung von vorhin (,von "
               "2,5 auf einen Wert im tragenden Band anheben') ist "
               "zurueckgezogen: es gibt kein nachweislich tragendes Band. "
               "\u2714 WAS BLEIBT UND WEITER GILT: (1) das Werkzeug ist jetzt "
               "vollstaendig - Band, Basislinie, Trennschaerfe, "
               "Positivkontrolle, und die Zentrierungsprobe laeuft in jedem "
               "Lauf mit; (2) `stop_ziel_atr` = 2,5 und `stop_max_relativ` "
               "= 25 %% stehen weiterhin OHNE eigenen Befund (2.431-"
               "grenzen) - das ist unveraendert wahr, nur ist der Ersatz "
               "noch nicht da; (3) der Zusammenhang Stopweite → Hebel gilt "
               "unveraendert (12 %% → 3,75x, 20 %% → 2,25x, 25 %% → Spot), "
               "denn er ist Arithmetik, keine Messung. \u27a4 WAS ES BRAUCHT: "
               "mehr Faelle oder eine feinere Zielgroesse. Bei 251 Faellen "
               "im breitesten Band und einer Auflösung von 0,40 R ist die "
               "Frage mit den heutigen Daten NICHT entscheidbar - und das "
               "ist ein ERGEBNIS, kein Zwischenstand", "abgeloest",
               "Befunde 2.431, 2.433, 2.433-nullmodell",
               abgeloest_durch="2.435-optimum",
               warum="Der Satz 'mit den heutigen Daten NICHT entscheidbar - und"
                     " das ist ein ERGEBNIS, kein Zwischenstand' war falsch, "
                     "und zwar gegen die stehende Nutzervorgabe KEIN-BEITRAG-"
                     "FAELLT-OHNE-LOESUNGSSUCHE. Er war ein Zwischenstand: "
                     "dieselben Daten, historisch und GEPAART gerechnet, "
                     "entscheiden die Frage. Was aus 2.433-folge bleibt, ist "
                     "die Schlussfolgerung selbst - `stop_ziel_atr` wird nicht "
                     "geaendert -, jetzt aber belegt statt mangels Nachweis."),
    Befundlage("2.432", "\u2714\u2714\u2714 A9 IST GROESSTENTEILS GELOEST - DER SPRUNG "
               "1,02x AUF 3,90x GIBT ES NICHT MEHR. Nutzerhinweis 13.09.: "
               "*,mir kommt die Tabelle bekannt vor - du hattest Spruenge "
               "und es war zu grob, und du hast eine Loesung gefunden'*. Er "
               "hat recht, und ich haette es nachschlagen muessen, bevor "
               "ich in Schritt 47 eine neue Tabelle rechne. \u27a4 R-R11: die "
               "Tabelle aus 2.174-neu mit DEMSELBEN Aufbau nachgerechnet "
               "(Kapital 10.000, Einsatz 500, Stop 5 %, CRV 2,0), heutiger "
               "Code gegen den Stand vom 08.09.: kein Beitrag Spot (0,00x) "
               "\u00b7 mittlere Lage 2,00x (1,02x) \u00b7 nur funding bestes 2,46x "
               "(3,90x) \u00b7 funding best + turnover mittel 3,12x (4,56x) \u00b7 "
               "nur turnover bestes 5,00x (9,45x) \u00b7 beide bestes 5,00x "
               "(13,35x). \u2714\u2714 DIE LEITER IST DURCHGEHEND, und VIER von "
               "sechs Lagen liegen in der Zielzone 2-5x - damals zwei. "
               "\u27a4 DIE LOESUNG WAR DIE r-KLAMMER (N-39, halbes Kelly "
               "geklammert 0,50-1,25 %) zusammen mit der harten Grenze 5x "
               "und der Regel ,unter 2x wird es Spot' - gebaut als H-2 "
               "(2.377). Sie kappt die Spitze (13,35 auf 5,00) UND hebt den "
               "Boden (1,02 auf 2,00, weil `r_min` greift); genau dazwischen "
               "lag der Sprung. \u26a0\ufe0f WAS BLEIBT: bei den zwei besten Lagen "
               "greift die OBERGRENZE - 36,5 % und 37,3 % ergeben beide "
               "5,00x. Dort ist die Aufloesung weiterhin weg, aber am "
               "oberen Ende und durch eine bewusste Sicherheitsgrenze, "
               "nicht durch die Fuenftel. Das ist etwas anderes als der "
               "urspruengliche Befund", "gilt",
               "agent/wahrscheinlichkeit + agent/betraege.hebelrechnung, "
               "gerechnet 13.09.; Befunde 2.174-neu, 2.174-grenzen, 2.377"),
    Befundlage("2.432-lehre", "\u26a0\ufe0f\u26a0\ufe0f ICH HABE EINE TABELLE NEU "
               "GERECHNET, DIE ES SCHON GAB - und der Nutzer hat es "
               "gemerkt, nicht ich. In Schritt 47 habe ich Quote, Kelly und "
               "Hebel ueber die Beitragslagen aufgestellt, ohne "
               "nachzuschlagen, dass genau diese Tabelle am 08.09. als "
               "2.174-neu entstanden ist und dass ihr Hauptbefund - der "
               "Sprung - am 11.09. mit H-2 behoben wurde. \u26a0\ufe0f DER SCHADEN "
               "waere nicht die doppelte Arbeit gewesen, sondern die "
               "doppelte AUSSAGE: meine Zahlen (4,50x / 2,21x / Spot) und "
               "die alten (13,35x / 3,90x / 1,02x) stehen nebeneinander und "
               "widersprechen sich, solange niemand sagt, dass die Klammer "
               "dazwischenliegt. \u27a4 Es gibt schon eine Regel dagegen - "
               ",Faktenregister vor jeder Messung' und R-R11 - und sie "
               "greift offenbar nicht, wenn ich die Zahl fuer eine "
               "Nebenrechnung halte statt fuer eine Messung. Eine "
               "Nebenrechnung, die der Nutzer als Tabelle liest, IST eine "
               "Messung", "gilt",
               "Nutzerhinweis 13.09.; Befunde 2.174-neu, 2.431-fenster"),
    Befundlage("2.431", "\u26a0\ufe0f\u26a0\ufe0f\u26a0\ufe0f SCHRITT 47, TEIL 1: DIE MESSUNG "
               "GIBT ES SCHON - UND SIE DREHT DIE ANNAHME DES PLANSCHRITTS "
               "UM. `messe_stop_abstand_baender.py` misst genau die Frage "
               "und loest dabei die Falle, an der zwei Vormessungen "
               "gebrochen sind: KEIN Aufloesungsfilter, jedes Signal wird "
               "gegen die echte Preisreihe neu simuliert, wer nichts "
               "trifft, bekommt Mark-to-Market. Ohne das haengt die "
               "Stichprobe am Messgegenstand - ein enger Stop loest fast "
               "immer auf, ein weiter faellt heraus. GELAUFEN am 13.09. "
               "gegen den NB-Export, 1.446 Signale, 50 Symbole, H7: "
               "0-2 %% EW -0,564 [-0,965;-0,029] \u00b7 2-3 %% -0,017 \u00b7 3-5 %% "
               "+0,138 \u00b7 5-8 %% -0,042 \u00b7 8-12 %% +0,011 \u00b7 >12 %% +0,230 "
               "[+0,014;+0,366]. \u27a4 NUR ZWEI BAENDER SCHLIESSEN DIE NULL "
               "AUS: enge Stops unter 2 %% SCHADEN nachweislich, Stops ueber "
               "12 %% TRAGEN nachweislich. Alles dazwischen ist nicht "
               "trennbar. \u26a0\ufe0f KEIN BEFUND NACH NORM: Bootstrap-Band und "
               "Basislinie sind da, Trennschaerfe und Positivkontrolle "
               "fehlen, und die Menge sind Signale mit Zonen, nicht das "
               "Messuniversum. Ein starker HINWEIS mit n=251 im tragenden "
               "Band - nicht mehr "
               "⚠️⚠️⚠️ RICHTIGGESTELLT AM SELBEN TAG (2.433, "
               "2.433-nullmodell): der Satz ,nur zwei Baender schliessen "
               "die Null aus‘ stimmt woertlich und ist trotzdem falsch - "
               "das Nullmodell ist die BASISLINIE, nicht die Zahl 0. Gegen "
               "die Basislinie trennt sich KEIN einziges Band. Und die "
               "nachgezogene Trennschaerfe liegt bei 0,40 R, waehrend der "
               "groesste gemessene Effekt +0,230 R betraegt; zwei Baender "
               "bestehen nicht einmal die Positivkontrolle. ➤ Die Aussage "
               ",unter 2 %% schadet, ueber 12 %% traegt‘ ist ZURUECKGEZOGEN",
               "abgeloest",
               "messe_stop_abstand_baender.py gegen notebook_diagnose.json "
               "vom 12.09., Lauf 13.09.",
               abgeloest_durch="2.435-optimum, 2.435-gleichtag",
               warum="Die Signalstichprobe hatte 21 wirksame Symbole im "
                     "breitesten Band (2.434). Die historische gepaarte Messung"
                     " ueber 534 Symbole hat den Kernsatz 'ueber 12 % traegt' "
                     "nach R-R11 ZUERST REPRODUZIERT - auf genau denselben 21 "
                     "Symbolen - und dort statt +0,230 R einen Wert von -0,004 "
                     "R gefunden, dessen Band die Null einschliesst. Der grosse"
                     " Wert war die AUSWAHL der Signale, nicht die Stopweite."),
    Befundlage("2.431-fenster", "\u2714\u2714\u2714 ES GIBT EIN FENSTER, DAS BEIDES "
               "ERFUELLT - und der Planschritt hat es nicht gesehen. Er "
               "sagte: *,ein Stop von 25 %% macht jeden Hebel unmoeglich'* "
               "und schloss daraus, der ATR-Rueckfall sei unbrauchbar. Das "
               "gilt aber NUR am Deckel. Durchgerechnet (Kapital 17.987 "
               "EUR, Einsatz 500 EUR, CRV 2,0, Quote 37,3 %%): Stop 12 %% -> "
               "3,75x \u00b7 15 %% -> 3,00x \u00b7 20 %% -> 2,25x \u00b7 25 %% -> 1,00x "
               "und damit Spot. \u27a4 ZWISCHEN 12 UND RUND 22 %% LIEGT EIN "
               "BEREICH, DER GLEICHZEITIG einen Hebel von 2 bis 3,75x "
               "erlaubt UND im einzigen Band liegt, das nachweislich traegt "
               "(+0,230 R). \u26a0\ufe0f\u26a0\ufe0f UND DIE HEUTIGE VORGABE LIEGT NICHT "
               "DARIN: `stop_ziel_atr = 2,5` trifft bei BTC rund 7,5 %% - "
               "das Band 5-8 %% misst -0,042 und ist nicht trennbar. "
               "Gezaehlt liegen 1.195 von 1.446 Signalen (83 %%) unter "
               "12 %%, also im nicht trennbaren oder schaedlichen Bereich; "
               "nur 251 (17 %%) im tragenden Band. \u27a4 DAMIT BRAUCHT DER "
               "HEBEL DEN WIDERLEGUNGSPREIS NICHT - er braucht einen Stop "
               "zwischen 12 und 22 %%. Genau das war die Frage des "
               "Schritts", "gilt",
               "agent/betraege.hebelrechnung gegen 2.431, gerechnet 13.09."),
    Befundlage("2.431-grenzen", "\u26a0\ufe0f\u26a0\ufe0f WAS IN `GRENZEN` OHNE EIGENEN BEFUND "
                                "STEHT - nachgesehen, wie der Schritt es "
                                "verlangt. \u2714 BEGRUENDET: `stop_min_relativ` 5 "
                                "%% (RM-1b) und `stop_min_atr` 0,75 (RM-1c) "
                                "stehen auf den Tagesspannen-Perzentilen - 5,0 "
                                "%% entsprechen 0,78 Tagesspannen im Median, "
                                "die beiden Grenzen sagen dasselbe einmal "
                                "relativ und einmal absolut. \u2716 NICHT "
                                "BEGRUENDET, beide: `stop_ziel_atr` = 2,5 steht"
                                " auf FREMDEN Praxisstandards (Chandelier 3x, "
                                "Elder 2x) plus einem Backtest vom 28.07. mit "
                                "61 aufgeloesten Trades - genau der "
                                "Survivorship-Stichprobe, die "
                                "`messe_stop_abstand_baender` als unbrauchbar "
                                "nachgewiesen hat. `stop_max_relativ` = 25 %% "
                                "traegt im Code den Vermerk *,NEU, es gab "
                                "bisher keine'* und die Begruendung *,25 %% ist"
                                " rund 8 x ATR bei Krypto - jenseits davon ist "
                                "es kein Stop mehr'*: eine Plausibilitaet, "
                                "keine Messung. \u27a4 BEIDE Zahlen lassen sich "
                                "jetzt an 2.431 messen statt setzen - und beide"
                                " muessten sich bewegen: der Zielwert nach "
                                "OBEN, der Deckel bleibt oder wird enger, weil "
                                "er ohnehin den Hebel abschneidet \u2714\u2714\u2714 NACHTRAG "
                                "13.09., ZWEITE TAGESHAELFTE: `stop_ziel_atr` "
                                "HAT JETZT EINEN EIGENEN BEFUND (2.435-optimum)"
                                " - 32.040 gepaarte Anker ueber 534 Symbole "
                                "zeigen ein inneres Maximum bei 7 bis 9 %, und "
                                "2,5 x ATR trifft es. Die Zahl bleibt, aber sie"
                                " steht nicht mehr auf fremden Praxisstandards."
                                " \u26a0\ufe0f OFFEN BLEIBT `stop_max_relativ` = 25 %, "
                                "erstmals beziffert in 2.435-deckel: der Deckel"
                                " laesst Weiten zu, die messbar schlechter sind"
                                " (20 %: -0,041 R gegen den Betriebspunkt). Das"
                                " ist eine Nutzerentscheidung, keine Messfolge "
                                "- eine Senkung hebt den Hebel genau der "
                                "Trades, die heute in Spot fallen.",
               "gilt",
               "agent/entscheidungsrechnung.GRENZEN Zeilen 48-164; "
               "Befund 2.431"),
    Befundlage("2.430", "\u2714\u2714 DER PLAN HAT EINE ZWEITE ACHSE: ALT GEGEN NEU "
               "(Nutzervorgabe 13.09.: *,Der PLAN muss klar zwischen altem "
               "und neuem Umbau unterscheiden'*). \u26a0\ufe0f DER ANLASS WAR MEINE "
               "EIGENE VERMISCHUNG: ich hatte den Widerlegungspreis als "
               "tragend fuer den Hebel dargestellt. Richtig ist, dass "
               "`r(q)` - der NEUE Teil - den Hebel ERZEUGT und der Stop - "
               "der ALTE Teil - ihn nur SKALIERT. Der Nutzer hat das sofort "
               "bemerkt: *,du vermischt altes mit neuem'*. \u27a4 GEBAUT: das "
               "Feld `Schritt.umbau` mit genau drei Woertern - `neu` (wird "
               "gebaut), `alt` (wird aufgeraeumt oder ersetzt), `beides` "
               "(ersetzt Altes UND baut Neues). Alle 50 Schritte "
               "eingeordnet, begruendet je Schritt im Quelltext. VERTEILUNG "
               "gesamt 33 neu / 10 alt / 7 beides, OFFEN 11 neu / 4 alt / 5 "
               "beides. \u26a0\ufe0f SIE ERSETZT DEN BLOCK NICHT: der Block sagt, "
               "WANN etwas drankommt, die neue Achse sagt, OB gebaut oder "
               "aufgeraeumt wird. Ein Schritt kann dringend und trotzdem "
               "eine Reparatur sein (46), ein unwichtiger kann Neubau sein. "
               "\u2714 Die Ausgabe zeigt es je Schritt und je Block gezaehlt; "
               "drei Pruefungen halten fest, dass jeder Schritt eines der "
               "drei Woerter traegt und dass die Ausgabe es zeigt. "
               "Gegengeprueft mit einer fehlenden und einer falschen "
               "Kennzeichnung", "gilt",
               "soll_ist.Schritt.umbau; UMBAUZEICHEN; Nutzervorgabe 13.09."),
    Befundlage("2.430-s47", "\u2714\u2714\u2714 SCHRITT 47 STEHT AN DER SPITZE UND HAT "
               "DEN BLOCK GEWECHSELT - D-BEWERTUNG nach D-BETRIEB "
               "(Nutzerentscheidung 13.09.). \u26a0\ufe0f\u26a0\ufe0f DER GRUND IST "
               "GEMESSEN, nicht empfunden: `hebel = risiko_eur / (einsatz x "
               "stop_rel)`. Der ZAEHLER ist der Umbau der letzten Wochen "
               "und er ist sauber - `r(q)`, halbes Kelly aus der gemessenen "
               "Quote. Der NENNER ist es nicht: `stop_rel` ist der weiteste "
               "von vier Boeden, und einer davon ist der WIDERLEGUNGSPREIS "
               "DES MODELLS. Damit haengt der Hebel jedes laufenden Signals "
               "an einer Zahl, deren Guete nie gemessen wurde. \u27a4 UND DIE "
               "MODELLZAHL EINFACH ZU STREICHEN GEHT NICHT (2.397): ohne "
               "sie greift der ATR-Rueckfall mit 2,5 x ATR, gedeckelt bei "
               "25 % - dann erreicht kein r(q) der Spanne 0,50-1,25 % die "
               "Grenze von 2,0x, und es gaebe GAR KEINEN Hebel mehr. Der "
               "Ausweg ist ein GEMESSENER Stop, und genau das ist Schritt "
               "47. \u26a0\ufe0f WARUM DER BLOCK WECHSELT: unter D-BEWERTUNG stand "
               "er neben Schritten, die *,nichts anderes blockieren'*. Das "
               "trifft hier nicht zu - er kostet heute Geld, und das ist "
               "die Beschreibung von D-BETRIEB", "gilt",
               "agent/betraege.hebelrechnung; agent/entscheidungsrechnung "
               "Boeden; Befunde 2.397, 2.400-hebel"),
    Befundlage("2.430-hebel-gerechnet", "\u2714\u2714\u2714 DER HEBEL ENTSTEHT WIE "
               "GEFORDERT - und meine Darstellung davor war ZU DUESTER. "
               "Nutzerfrage 13.09.: *,wird dieser nun dynamisch erstellt wie "
               "gefordert - aus der Wahrscheinlichkeit eines optimalen "
               "Chance-Risiko-Verhaeltnisses?'* DURCHGERECHNET ueber die "
               "echte Kette (Kapital 17.987 EUR, Einsatz 500 EUR, CRV 2,0, "
               "Stop 10 %): beide Beitraege im besten Fuenftel -> Quote "
               "37,3 %, halbes Kelly +2,98 %, r 1,25 % (Obergrenze), Hebel "
               "4,50x. Nur `funding` im besten -> 34,2 %, +0,61 %, Hebel "
               "2,21x. KEIN Beitrag -> 33,3 % = Basisrate, Kelly 0,00 %, "
               "SPOT. Beide im schlechtesten -> 29,2 %, Kelly -3,08 %, "
               "SPOT. \u27a4 DIE BASISRATE 33,3 % IST EXAKT DER BREAK-EVEN BEI "
               "CRV 2. Weniger Evidenz fuehrt also automatisch zu weniger "
               "Hebel und im Zweifel zu Spot - das ist die eingebaute "
               "Vorsicht, kein Loch. \u26a0\ufe0f\u26a0\ufe0f ICH HATTE ,38 von 44 Werten "
               "stehen auf funding allein' als Mangel dargestellt, ohne die "
               "Wirkung zu rechnen. `funding` allein traegt 2,21x. Eine "
               "Deckungszahl ohne Wirkungsrechnung kann das Bild kippen - "
               "daraus ist die stehende Vorgabe ,immer Gesamtsicht und "
               "Auswirkung' geworden", "gilt",
               "agent/wahrscheinlichkeit.rechne + agent/betraege."
               "hebelrechnung, gerechnet 13.09."),
    Befundlage("2.429", "⚠️⚠️ Z1 UND Z.AI STANDEN UNTER EINER "
               "UEBERSCHRIFT - Nutzereinwand 13.09.: *,die Vermischung von Z1 "
               "und ZAI LLM finde ich kritisch'*. Der Einwand trifft, und "
               "derselbe Fehler ist schon einmal korrigiert worden: der "
               "Modulkopf von `gegenpruefer_rollen.py` haelt fest, Z1 habe "
               "urspruenglich ,der Gegenpruefer der neuen Kette' geheissen "
               "und das sei *,vereinnahmend'* gewesen. ✔ IM CODE WAREN SIE "
               "GETRENNT - die beiden Berichtszeilen lauteten schon vorher "
               ",Z1 Treue zur Eingabe (Rechnung, kein Filter)' und ,LLM-2 "
               "Rolle G / Z.ai (kein Veto)'. ✖ ABER DIE FUNKTION HIESS "
               "`bericht_llm()` und stellte damit beide unter dieselbe "
               "Ueberschrift, obwohl Z1 GAR KEIN Sprachmodell ist. "
               "➤ UMBENANNT in `bericht_pruefstellen()`, die Zeilen "
               "beschriftet mit ,RECHNUNG Z1' und ,SPRACHMODELL LLM-2 Rolle "
               "G / Z.ai', und der Unterschied steht jetzt im Docstring: Z1 "
               "ist eine RECHNUNG und faengt ERFINDUNG (Treue zur Eingabe, "
               "kostenlos, kann sich nicht irren); Z.ai ist ein "
               "SPRACHMODELL-Aufruf und faengt DENKFEHLER (prueft das "
               "Urteil, kann sich irren). ✔ Kein Schaden entstanden: die "
               "Trennung war in der Sache immer da, nur der Name war "
               "falsch. Zwei Pruefzeilen hingen am alten Wortlaut und sind "
               "nachgezogen", "gilt",
               "agent/rollen_gate.bericht_pruefstellen; "
               "agent/gegenpruefer_rollen.py Modulkopf; Nutzereinwand 13.09."),
    Befundlage("2.428", "\u2714\u2714\u2714 SCHRITT 48 (1) DER DEFEKT IST GESCHLOSSEN - "
               "und zwar VOLLSTAENDIG, nicht nur zu einem Viertel. 2.392-"
               "stumm nannte 105 Ausstiege, die als ,reines LLM-Halten' "
               "gebucht wurden und den Nutzer nie erreichten, und erklaerte "
               "davon 25 mit dem gestakten Fall. An der "
               "Produktionssicherung vom 12.09. ALLE 105 durchgezaehlt: 95 "
               "betreffen Werte, die VOLLSTAENDIG GESTAKT sind (quantity 0, "
               "staked > 0) - HYPE 45, SOL 27, NEAR 7, SUI 7, AVAX 3, VSN "
               "3, TAO 2, SEI 1; sie bekommen seit 48a einen eigenen "
               "Mailabschnitt. \u27a4 DIE UEBRIGEN 10 STEHEN ALLE AM 14.08. "
               "ZWISCHEN 07:14 UND 07:16 - einem Drei-Minuten-Fenster. Der "
               "Fix von damals ist Commit 153b2bd, *,Die Verkaufsseite - "
               "drei Klassen statt zwei'*, vom 14.08. um 11:39: die zehn "
               "liegen VIER STUNDEN DAVOR. \u2714 Zwischen dem 14.08. 07:16 und "
               "dem 11.09. gibt es KEINEN unerklaerten Fall mehr. Der Zweig "
               "ist gefunden und geschlossen", "gilt",
               "signals der Sicherung 2026-09-12 gegen holdings.staked_"
               "quantity; git log 14.08."),
    Befundlage("2.428-erfassung", "\u2714\u2714 SCHRITT 48 (2) DIE ERFASSUNG STEHT: "
               "DER KURS ZUM EMPFEHLUNGSZEITPUNKT WIRD MITGESCHRIEBEN. Ein "
               "EINSTIEG haelt seine Lage in `entry_usd_von/bis` und "
               "`stop_loss_*` fest - ein AUSSTIEG hielt GAR NICHTS fest, "
               "nachgesehen an einer echten Zeile: bei REDUZIEREN ist von "
               "allen Preisfeldern nur `umgeworfen_preis_eur` gefuellt, und "
               "das ist die Modellangabe, nicht der Kurs. `_sende_ausstieg` "
               "reichte `rechnung=None` durch, obwohl `kurs_e` dort seit "
               "jeher vorliegt. \u26a0\ufe0f WAS DAS KOSTET, steht in 2.403: die "
               "Guetemessung rechnet mit dem TAGESSCHLUSS. Bei H10 schlaegt "
               "VERKAUFEN den Zufall deutlich (78,8 % gegen 50,0 %), bei H3 "
               "liegt es AM Zufall - wer den Kurs der Stunde nicht kennt, "
               "kann kurze Horizonte nicht beurteilen. \u27a4 GEBAUT: die "
               "Spalte `kurs_bei_empfehlung_eur` in `SPALTEN_SIGNAL`, das "
               "Feld in `models.Signal`, der Parameter in "
               "`felder_aus_entscheidung`, die Durchreichung in "
               "`_sende_ausstieg`. \u26a0\ufe0f\u26a0\ufe0f NUR ERFASSEN: kein Ablauf, "
               "keine Mail, keine Sperre aendert sich - und eine Pruefung "
               "haelt fest, dass der Wert in `entscheidungsrechnung`, "
               "`potential`, `wahrscheinlichkeit`, `rollen_gate` und "
               "`signal_mail` NICHT vorkommt. Bei 15 bis 20 Ausstiegen am "
               "Tag stehen in vier Wochen rund 500 auswertbare Faelle da",
               "gilt",
               "agent/signal_abbildung.py; database/models.py; "
               "agent/rollen_lauf._sende_ausstieg; Paket "
               "Ausstiegserfassung, 10 Pruefungen"),
    Befundlage("2.428-kopplung", "\u26a0\ufe0f\u26a0\ufe0f DIE SUITE HAT DIE KOPPLUNG ZUM "
               "ZWEITEN MAL AN EINEM TAG GEFANGEN: eine neue "
               "`signals`-Spalte muss an DREI Stellen bekannt sein, nicht "
               "an einer. (1) `SPALTEN_SIGNAL` legt sie an; (2) "
               "`models.Signal` muss das Feld haben, denn `_row_to_signal` "
               "baut aus `SELECT *` - fehlt es, ist JEDES Signal unlesbar, "
               "auch jedes alte (der Ausfall vom 14.08., dreizehn Aufrufer "
               "von `get_latest_signal` hingen daran); (3) der NB-Export "
               "muss sie mitnehmen, sonst ist sie am Desktop nicht da - und "
               "dort wird gemessen. \u2714 Ich hatte (1) und (2) gebaut und (3) "
               "vergessen; die Zeile *,keine signals-Spalte ist mehr "
               "unexportiert'* wurde rot, genau wie heute Vormittag bei "
               "`veto_art`. \u27a4 Die drei Stellen stehen jetzt zusammen im "
               "Paket `Ausstiegserfassung`, damit die naechste Spalte nicht "
               "wieder einzeln nachgezogen werden muss. \u2714 Gegengeprueft: "
               "zwei absichtlich eingesetzte Defekte (Durchreichung "
               "abgeklemmt, Erwaehnung in `potential.py`) machen das Paket "
               "rot, danach 10 von 10", "gilt",
               "pruefe_pakete Paket Ausstiegserfassung; "
               "extract_notebook_diagnose.py"),
    Befundlage("2.427", "\u2714\u2714\u2714 DER E2E-NACHWEIS FUER PAKET B IST "
               "ERBRACHT (2.396-e2e nachgeholt). Er war am 12.09. an einer "
               "NB-Kopie gescheitert, deren Kursreihen nicht bis zum "
               "Simulationstag reichten - GEGEN DIE PRODUKTIONSSICHERUNG "
               "vom 12.09. 06:46 laeuft er durch: 17 Faelle, 17 gezeigt, 0 "
               "offen. ONDO wird ein echtes Hebelgeschaeft (instrument "
               "`hebel`, 3,7x, Verlust am Stop 226,76 EUR, Liquidation "
               "hinter dem Stop bis Tag 39), AKT faellt am Aggregat-Deckel "
               "auf Spot (frei nur noch 30 von 540 EUR) und die Mail sagt "
               "warum. Hebeltopf, Cooldown 3,5 h gegen 12 h, "
               "Hebelfuehrung mit HEBEL SENKEN, Schalter-aus-Gegenprobe - "
               "alles gruen. \u26a0\ufe0f DER LAUF MELDET OBEN ZWEIMAL ,MARKTRANG "
               "AUSGEFALLEN` - das ist ABSICHT und kein Defekt: der "
               "Kernwert-Fall wird mit `OHNE = {oi_fuenftel: 1, "
               "querschnitt_oi: 122}` gefahren, also bewusst ohne Funding "
               "und Turnover, und die Kette meldet den Ausfall korrekt. "
               "Gegengeprueft, dass es nicht am heutigen Umbau liegt: "
               "`marktrang.raenge([BTC])` liefert funding-Fuenftel 3 und "
               "turnover-Fuenftel 0 bei Querschnitten 302 und 60. "
               "\u26a0\ufe0f Nutzerhinweis vom 13.09. hat das moeglich gemacht - ich "
               "hatte den Nachweis fuer ,nur am Notebook machbar` erklaert "
               "(2.422-desktop)", "gilt",
               "simuliere_kette.py --nachweis-paket-b gegen die Sicherung "
               "2026-09-12 06:46, Lauf 13.09."),
    Befundlage("2.427-rollenfrage", "\u26a0\ufe0f\u26a0\ufe0f 2.391-hilfe IST EINE "
               "ROLLENFRAGE UND WANDERT IN DEN L-BLOCK - reproduziert, "
               "bevor sie weitergereicht wird (R-R11). An der "
               "Produktionssicherung nachgezaehlt, Rollen-Laeufe vom 05. "
               "bis 12.09.: 3.365 Laeufe, 39.707 Zellen hinein; Stufe "
               "`aktion` verliert 247, davon 166 ,Ausstieg steht auf "
               "SCHLIESSEN` und 25 ,vollstaendig gestakt` (beides "
               "deterministisch) und **56 NICHTS_TUN** - das Modell. Stufe "
               "`entscheider` 1.251. Beide Zahlen treffen den Befund "
               "genau. \u27a4 ZWEI ENTSCHEIDUNGEN STEHEN AN, und keine ist im "
               "D-Block zu treffen: (1) DARF DAS MODELL EINE EMPFEHLUNG "
               "VERHINDERN? 56 Zellen in 7 Tagen. (2) DARF SEINE "
               "PREISANGABE DIE GEOMETRIE BESTIMMEN? \u2714 Die zweite ist "
               "faktisch beantwortet: 2.397 hat gemessen, dass OHNE den "
               "Widerlegungspreis gar kein Hebel mehr entsteht (bei 25 % "
               "ATR-Stop erreicht kein r(q) die 2,0x-Grenze) - er BLEIBT, "
               "und was fehlt, ist die Kennzeichnung an der Zahl in der "
               "Mail (Schritt 41). \u26a0\ufe0f Offen bleibt die ERSTE, und sie "
               "gehoert zu Schritt 33: Schritt 44 ist ausdruecklich "
               ",AUFRAEUMEN, nicht Umbau - keine neue LLM-Faehigkeit`",
               "gilt",
               "gate_durchlaessigkeit der Sicherung 2026-09-12, 3.365 "
               "Rollen-Laeufe; Befunde 2.391-hilfe, 2.397"),
    Befundlage("2.426", "\u2714\u2714\u2714 SCHRITT 50 TEIL A GEBAUT: `messreihen` "
               "TRAEGT DIE KLASSE IM SCHLUESSEL. Vorher `symbol TEXT "
               "PRIMARY KEY` - eine Klasse je Ticker; jetzt `PRIMARY KEY "
               "(symbol, assetklasse)`, wie `price_history_ohlc` es "
               "laengst tut. \u26a0\ufe0f `messreihen_status` GEHOERT DAZU und ist "
               "mitgewandert: es hatte dieselbe Mehrdeutigkeit - EINE "
               "Statuszeile fuer ZWEI Reihen. Nur eine Tabelle zu aendern "
               "haette die Mehrdeutigkeit eine Tabelle weiter geschoben. "
               "\u27a4 MIGRATION statt blossem Schema: `CREATE TABLE IF NOT "
               "EXISTS` aendert eine bestehende Tabelle nicht - dieselbe "
               "Lage wie bei `hole_terminmarkt_historie.migriere` am "
               "01.09. `lade_messreihen.migriere_klassenschluessel()` baut "
               "beide Tabellen neu, uebernimmt jede Zeile und ergaenzt die "
               "fehlende zweite. GELAUFEN: 1.327 -> 1.334 in beiden "
               "Tabellen, DASH steht jetzt als `aktien` UND `krypto`. "
               "\u2714 VORAB AN EINER KOPIE GEPRUEFT, nicht am Original: "
               "+7/+7, und ein zweiter Lauf liefert (0, 0). "
               "\u2714 SICHERUNG VORHER: `data/messdaten_vor_klassenschluessel_"
               "13_09.db`, 1,57 GB, `PRAGMA quick_check` = ok. "
               "\u2714\u2714 UND DIE MESSUNGEN SIND BITGLEICH: `lade()` liefert "
               "weiter 536 Reihen = `messmenge.V1`, DASH weiter die "
               "Krypto-Reihe mit 2.722 Punkten, und `_reihen_roh` je "
               "Klasse krypto 536 / aktien 470 / themen_etf 293 / "
               "rohstoffe 35 - dieselben Zahlen wie vor der Migration",
               "gilt",
               "lade_messreihen.migriere_klassenschluessel; Lauf 13.09.; "
               "Sicherung data/messdaten_vor_klassenschluessel_13_09.db"),
    Befundlage("2.426-verbraucher", "\u26a0\ufe0f\u26a0\ufe0f DIE ZUORDNUNG IST JETZT EINE "
               "MENGE, UND DAS WAR DIE EIGENTLICHE AENDERUNG. "
               "`simuliere_bremse.klassen_aus_db` lieferte `symbol -> EINE "
               "Klasse` - fuer die sieben Ticker-Kollisionen zwangslaeufig "
               "die falsche. Jetzt `symbol -> frozenset(Klassen)`, und der "
               "Filter fragt `klasse not in kl.get(sym)` statt "
               "`kl.get(sym) != klasse`. \u26a0\ufe0f AUCH DER RUECKFALL AUF DIE "
               "WATCHLIST liefert eine Menge - sonst haetten die beiden "
               "Wege verschiedene Formen, und `'krypto' in 'krypto_alt'` "
               "waere als Teilstring wahr geworden statt als Menge falsch. "
               "\u27a4 WEITER ANGEPASST: `lade_messreihen` (eine zweite Klasse "
               "ist keine KOLLISION mehr, sondern eine zweite Zeile - "
               "gezaehlt wird sie weiter, als DOPPELTICKER), "
               "`uebernehme_messreihen` (fragt nach (Symbol, 'krypto') "
               "statt nur nach dem Symbol - sonst haette eine Aktie mit "
               "demselben Ticker die Krypto-Uebernahme still abgelehnt), "
               "`pruefe_neuaufnahme` (`'krypto' in k`). \u2714 Sieben Leser "
               "geprueft, vier geaendert; `messe_ueberleben` liest nur "
               "`messreihen_status`, `pruefe_assetklassen_datenlage` nur "
               "eine Gruppierung", "gilt",
               "simuliere_bremse; lade_messreihen; uebernehme_messreihen; "
               "pruefe_neuaufnahme"),
    Befundlage("2.426-pruefungen", "\u26a0\ufe0f\u26a0\ufe0f DIESELBE PRUEFZEILE MUSSTE AN "
               "EINEM TAG ZWEIMAL UMGEBAUT WERDEN, und beide Male zu "
               "Recht. VORMITTAGS war *,`messreihen` und die Kursdaten "
               "sind klassengleich'* DAUERROT - sie meldete seit Tagen "
               "dieselben sieben und wurde ueberlesen; umgebaut auf "
               "*,keine NEUE Kollision'*. NACHMITTAGS hat Teil A die "
               "URSACHE beseitigt: eine Kollision gibt es nicht mehr. "
               "\u27a4 JETZT PRUEFT SIE DIE INVARIANTE DAHINTER - jede "
               "(Symbol, Klasse) mit Kursdaten hat eine Zeile in "
               "`messreihen` (sonst faende die Reihe keine Messung) - und "
               "eine zweite Zeile haelt fest, dass die sieben Doppelticker "
               "SICHTBAR bleiben: verschwaenden sie, waere eine Reihe "
               "verloren. \u26a0\ufe0f EINE DRITTE PRUEFUNG hing am WORTLAUT der "
               "Filterzeile (`kl.get(sym) != klasse`) und fiel durch die "
               "Verbesserung. Ihre ABSICHT gilt weiter - der 1:1-Filter "
               "greift nur ohne die Spalte -, nur die Gleichheitsfrage ist "
               "eine Mengenfrage geworden. Nachgezogen samt Begruendung, "
               "plus eine neue Zeile, die `frozenset` verlangt. "
               "\u2714 Dazu drei Waechter fuer Schema und Migration, letztere "
               "an einer Datenbank IM SPEICHER geprueft - eine Migration, "
               "die beim zweiten Lauf wieder zuschlaegt, verdoppelt Zeilen "
               "oder verliert welche", "gilt",
               "pruefe_pakete Pakete Neuaufnahme, Messstandard, "
               "Assetklassen; Suite 2.343 Pruefungen"),
    Befundlage("2.425", "\u2714\u2714\u2714 SCHRITT 50 TEIL B GEBAUT: DER ABRUFSTAND "
               "SAGT JETZT ,X VON Y SYMBOLEN', NICHT NUR EINEN ZEITSTEMPEL "
               "(Befund 2.359-abruf). \u26a0\ufe0f\u26a0\ufe0f UND DER PLANPUNKT "
               "BESCHRIEB DIE FALSCHE LOESUNG - `fetched_at` pro Zeile. Zwei "
               "Gruende, beide VOR dem Bau geprueft: (1) `MAX(fetched_at)` "
               "sagt exakt dasselbe wie die Aenderungszeit der Datei, "
               "beantwortet also die Frage nicht; (2) alle INSERTs der "
               "Ladeskripte schreiben POSITIONELL (`VALUES (?,?,?)`) - eine "
               "vierte Spalte haette sie STUMM gebrochen. \u27a4 GEBAUT WURDE "
               "STATTDESSEN eine Zeile JE SYMBOL: `abruf_symbol (tabelle, "
               "symbol, zuletzt_ok, zeilen)`, angelegt in allen drei "
               "Messdateien, geschrieben NUR im Erfolgszweig der Ladeskripte "
               "(`hole_fremdreihen.vermerke()` an drei Stellen, "
               "`hole_terminmarkt_historie` an einer). "
               "\u26a0\ufe0f `hole_terminmarkt_historie` FUEHRTE SCHON `abruf_status` "
               "(389.189 Zeilen je Symbol und Tag) - das ist keine Dopplung: "
               "`abruf_status` sagt WELCHE TAGE vorliegen und macht den Lauf "
               "wiederaufnehmbar, es traegt keinen Zeitstempel. "
               "\u2714\u2714 SOFORT AM ECHTEN LAUF NACHGEWIESEN: `splycur` neu "
               "geladen, danach meldet `datenfrische` *,2026-09-13T10:05:26 "
               "(65 von 66 Symbolen)'* - und die 65 sind kein Rundungsfehler. "
               "ZRX bekam keinen Vermerk, weil sein Abruf in diesem Lauf "
               "scheiterte; an der Quelle liefert es 3.320 Punkte, der "
               "Ausfall war voruebergehend. \u27a4 GENAU DAS IST DER FALL, DEN "
               "DIE DATEIZEIT NICHT SIEHT: die Datei war frisch geschrieben, "
               "die Daten von ZRX stammten aus einem frueheren Lauf, und "
               "nichts haette darauf hingewiesen", "gilt",
               "hole_fremdreihen.py; hole_terminmarkt_historie.py; "
               "agent/datenfrische.py; Lauf 13.09. 10:05"),
    Befundlage("2.425-erwartung", "\u26a0\ufe0f\u26a0\ufe0f DIE ERWARTUNGSZAHL GEHOERT AN "
               "DIE MESSBASIS-DEFINITION, NICHT AN EINE TABELLE - und ich "
               "bin beim Bauen zweimal hineingetappt, obwohl ich die Falle "
               "beim ersten Mal selbst aufgeschrieben hatte. `terminmarkt_"
               "tag` hat 100 Symbole, `terminmarkt` 122, und `MESSBASIS[oi]` "
               "ist die VEREINIGUNG, also 122. Meine erste Fassung zaehlte "
               "gegen die Tagestabelle und haette dauerhaft ,100 von 122' "
               "gemeldet - ein Fehlalarm, der die Anzeige wertlos gemacht "
               "haette. Ebenso `funding`: 302 Symbole in der Datei, aber 300 "
               "in `messmenge.V1`. \u27a4 GEBAUT: das Feld `Quelle."
               "vermerk_tabellen` nennt die Tabellen, ueber die gezaehlt "
               "wird, und die Zaehlung ist DISTINCT - ein Symbol in beiden "
               "Terminmarkt-Tabellen ist EIN Symbol der Messbasis. Eine "
               "Pruefung haelt fest, dass die drei Erwartungszahlen mit "
               "`messmenge.ABDECKUNG` uebereinstimmen", "gilt",
               "agent/datenfrische.Quelle; messmenge.ABDECKUNG; "
               "marktrang.MESSBASIS"),
    Befundlage("2.425-additiv", "\u2714 DIE UMSTELLUNG MELDET KEINEN ALARM UEBER "
               "SICH SELBST. Der Vermerk fuellt sich erst mit dem naechsten "
               "Ladelauf; solange die Tabelle fehlt oder leer ist, bleibt "
               "der Abrufstand die Dateizeit wie bisher. Sonst haetten "
               "`funding` und `terminmarkt` ab sofort ,0 von 300' und ,0 von "
               "122' gemeldet - ein Fehlalarm ueber die eigene Aenderung, "
               "und genau die Sorte, die eine Anzeige verlernt. \u2714 "
               "Gegengeprueft mit einer leeren Datenbank im Speicher und mit "
               "einer Quelle ohne Erwartungszahl: beide liefern None. \u2714 UND "
               "DAS PAKET SELBST IST GEGENGEPRUEFT: ein vierter, absichtlich "
               "falsch platzierter Vermerk macht es rot, danach 9 von 9",
               "gilt",
               "Paket Abrufvermerk, 9 Pruefungen; agent/datenfrische."
               "_abrufvermerk"),
    Befundlage("2.424", "\u26a0\ufe0f\u26a0\ufe0f\u26a0\ufe0f ZUM ZWEITEN MAL AN EINEM TAG "
               "EINE BEREITS BEANTWORTETE FRAGE ALS OFFEN VORGELEGT - und "
               "diesmal mit einer Empfehlung dazu. Ich habe dem Nutzer die "
               "drei Annahmen aus 2.380-annahmen zur Entscheidung gestellt "
               "und zu Punkt (1) empfohlen, `KOPPEL_TAGE` von 3 auf 1 Tag "
               "zu setzen. Er hat GENAU DAS am 11.09. selbst entschieden "
               "(2.380-fenster, ,24 Stunden statt 3 Tage'), der Code steht "
               "seit Commit 08a21f6 auf 1.0, und `ausrollen_paket_b` "
               "bewacht den Wert. Punkt (2) war ebenfalls entschieden - und "
               "die Annahme, die ich referierte (,ganzes Eigenkapital'), "
               "ist genau die Variante A, die er ABGELEHNT hatte. "
               "\u26a0\ufe0f DER ERSTE FALL AM SELBEN TAG war 2.415-alle: die "
               "Zeitfensterfrage, am 07.09. mit Band und Trennschaerfe "
               "beantwortet (S-7), von mir zwei Tage spaeter schlechter "
               "gestellt und als offen gefuehrt. \u27a4 DAS MUSTER: ein Befund "
               "wird ,offen' angelegt, am selben oder naechsten Tag "
               "beantwortet - und die Antwort landet in einem NEUEN Befund, "
               "waehrend der alte offen stehen bleibt. Beim Aufraeumen "
               "sieht er dann aus wie eine unerledigte Frage. \u2714\u2714 GEBAUT, "
               "damit es auffaellt: das Paket `Register` prueft, dass KEIN "
               "offener Punkt - Befund oder Planschritt - eine Konstante "
               "mit einem Wert zitiert, der im Code laengst anders steht. "
               "Genau daran haette man es gesehen: Schritt 45 nannte "
               "`hebelfuehrung.KOPPEL_TAGE` = 3, im Code stand 1.0. "
               "\u26a0\ufe0f VORAB GEPRUEFT statt blind eingebaut: im ganzen "
               "Bestand gibt es 5 Konstanten-Zitate, alle aufloesbar, genau "
               "EIN Treffer - kein Fehlalarm. \u2714 Gegengeprueft: das Zitat "
               "wieder eingesetzt macht das Paket rot, danach 13 von 13. "
               "\u26a0\ufe0f WAS DIE PRUEFUNG NICHT KANN: eine entschiedene Frage "
               "ohne Zahl erkennen. Dagegen hilft nur die Gewohnheit, vor "
               "dem Vorlegen die spaeteren Befunde derselben Familie zu "
               "lesen", "gilt",
               "Befunde 2.380-annahmen, 2.380-fenster, 2.380-ohne-stop, "
               "2.415-alle; pruefe_pakete Paket Register"),
    Befundlage("2.423", "\u2714\u2714 DIE DREI VERBLIEBENEN ROTEN ZEILEN DER SUITE "
               "SIND EINE DATENLAGE-GRENZE MIT BEKANNTEM ENDDATUM - keine "
               "Defekte. An der Produktionssicherung vom 12.09. gezaehlt "
               "(USD-Tage gegen `lade_messreihen.MIN_KERZEN` = 400): ASTER "
               "342 (58 Tage fehlen, also etwa Ende Oktober), MON 293 (107 "
               "Tage, etwa Januar), CANTON 63 (337 Tage). \u26a0\ufe0f UND EINE "
               "KORREKTUR AN 2.185-rest: dort steht *,CANTON hat in der "
               "Produktion GAR KEINE Kursreihe'*. Das gilt nicht mehr - "
               "CANTON hat 370 OHLC-Punkte seit 2025-11-10, davon 63 in "
               "USD. Die Zahlen fuer ASTER (318) und MON (269) sind "
               "ebenfalls gewachsen. \u27a4 DIE DREI ZEILEN MELDEN ALSO "
               "RICHTIG, aber sie melden etwas, das sich von selbst loest: "
               "die Coins existieren erst seit 10/2025 bis 11/2025 und sind "
               "nicht auf Binance-USDT, `lade_messreihen` kann sie also nie "
               "auffrischen - sie kaemen ueber `uebernehme_messreihen` mit "
               "Status `uebernommen` (2.185-veralten). \u26a0\ufe0f Die dritte "
               "Zeile (,die Messbasis ist nicht veraltet') betrifft "
               "`aktien`, `rohstoffe` und `themen_etf` mit je 10 Tagen "
               "Median-Alter - das ist die Folge der Vorgabe "
               "KRYPTO-ZUERST, nicht ein Ausfall. \u27a4 KEINE HANDLUNG "
               "NOETIG, aber benannt statt uebersehen: eine rote Zeile, die "
               "man kennt und nicht erklaeren kann, ist etwas anderes als "
               "eine, die man kennt und erklaeren kann", "gilt",
               "Produktionssicherung 2026-09-12; lade_messreihen.MIN_KERZEN; "
               "Befunde 2.185-rest, 2.185-veralten"),
    Befundlage("2.422", "\u26a0\ufe0f\u26a0\ufe0f\u26a0\ufe0f 2.389-richtung IST GROESSER ALS "
               "GEMELDET: DIE ABSICHERUNG KANN SEIT DEM 22.08. NUR NOCH "
               ",HALTEN' SAGEN. Der Befund sprach von *,zwei Signalen an "
               "einem Lauf, im zweiten Umlauf trat es nicht auf - es haengt "
               "am Modell, nicht an der Struktur.'* An der "
               "Produktionssicherung vom 12.09. gemessen ist es das "
               "Gegenteil: es haengt an der Struktur und es ist nicht "
               "gelegentlich. GEZAEHLT: von 12 Absicherungssignalen haben "
               "ALLE 12 `richtung = NULL`, ebenso alle 55 Signale von DBPK "
               "und 3QSS ueberhaupt. `empfehlung_vertrag.BRAUCHT_RICHTUNG` "
               "ist `(KAUFEN, NACHKAUFEN)` - HALTEN und VERKAUFEN kommen "
               "ohne Richtung durch, die beiden HANDELNDEN Aktionen nicht. "
               "\u27a4 DER ZEITPUNKT PASST GENAU: die letzten NACHKAUFEN der "
               "Absicherung stehen am 15., 16., 17. und 19.08. - alle noch "
               "OHNE Richtung, weil die Pflicht bis dahin nur fuer den "
               "Hebel galt (der alte Name `HEBEL_MIT_EINSTIEG` stand in der "
               "Bedingung). S6c hat sie am 22.08. instrumentunabhaengig "
               "gemacht. Seither: 03.09. HALTEN, 09.09. HALTEN - sonst "
               "nichts. \u26a0\ufe0f\u26a0\ufe0f UND ES BETRIFFT ZWEI GEHALTENE "
               "POSITIONEN: 3QSS 218,25 Stueck zu 2,05 EUR Einstand, DBPK "
               "1.739,16 Stueck zu 0,1713 EUR. In 22 Lauftagen seit dem "
               "22.08. bekam die Absicherung an DREI Tagen ein Signal, DBPK "
               "an EINEM. \u26a0\ufe0f WAS DIE ZAHLEN NICHT HERGEBEN: ob an den "
               "uebrigen 19 Tagen ein KAUFEN/NACHKAUFEN ABGELEHNT wurde "
               "oder gar keines vorgeschlagen war - die Tabelle speichert "
               "nur angenommene Signale. Belegt ist der MECHANISMUS (100 % "
               "ohne Richtung), nicht die Haeufigkeit. Dafuer braucht es "
               "die Ablehnungen aus dem Lauf, nicht die Datenbank", "gilt",
               "Produktionssicherung 2026-09-12 06:46 (Kopie im Scratchpad, "
               "nur lesend); agent/empfehlung_vertrag.BRAUCHT_RICHTUNG"),
    Befundlage("2.422-desktop", "\u26a0\ufe0f RICHTIGSTELLUNG EINER EIGENEN "
               "BEHAUPTUNG VON HEUTE: ich hatte geschrieben, 2.389 sei *,am "
               "Desktop nicht pruefbar - die Desktop-Kopie hat 5 statt "
               "1.998 Zeilen'*. Das war falsch, und der Nutzer hat es "
               "sofort bemerkt: *,du hast ein DB Backup'*. Ich hatte "
               "`data/tradinginfotool.db` angesehen - eine "
               "Entwicklungsdatenbank - und daraus geschlossen, es gebe "
               "keine Produktionsdaten. Tatsaechlich liegen unter "
               "`K:\\My Drive\\Claude_Austauschordner\\DB_Backups` sieben "
               "Sicherungen, die juengste vom 12.09. 06:46 mit 122 MB "
               "gepackt. \u27a4 GEGENPROBE, dass es die richtige ist: "
               "`hebel_signals` enthaelt 1.998 Zeilen - genau die Zahl aus "
               "dem Befund. \u26a0\ufe0f LEHRE: ,nicht messbar' ist eine Aussage "
               "ueber die eigene Suche, nicht ueber die Datenlage. Vor "
               "einem solchen Satz gehoert der Austauschordner "
               "nachgesehen. \u2714 Nebenbei bestaetigt: 2.343 stimmt auch an "
               "den echten Daten - `hebel_signals` endet am 2026-08-10, "
               "`signals` laeuft bis 2026-09-12", "gilt",
               "K:/My Drive/Claude_Austauschordner/DB_Backups; Nutzerhinweis "
               "13.09."),
    Befundlage("2.421", "\u2714\u2714 2.148-sperre UND 2.149-prod BEANTWORTET: DIE "
               "KLASSENKOLLISION IST REAL, ABER FOLGENLOS - und der "
               "Strukturfix, den 2.148 forderte, ist durch eine bessere "
               "Loesung ueberholt. WAS WIRKLICH DASTEHT: `messreihen` hat "
               "`symbol TEXT PRIMARY KEY`, kann also nur EINE Klasse je "
               "Symbol fuehren; `price_history_ohlc` hat `PRIMARY KEY "
               "(symbol, assetklasse, currency, date)` und fuehrt zwei. "
               "SIEBEN Symbole sind betroffen, und es sind TICKER-"
               "KOLLISIONEN, keine Datenfehler: BOND (BarnBridge gegen "
               "einen ETF), C (Citigroup), DASH (DoorDash gegen die "
               "Kryptowaehrung), DIA (Dow-ETF), MDT (Medtronic), STX "
               "(Seagate gegen Stacks), T (AT&T gegen Threshold). "
               "\u2714 DIE MESSUNG IST NICHT BETROFFEN, nachgezaehlt: `lade()` "
               "liefert fuer alle sieben die KRYPTO-Reihe, Punkt fuer Punkt "
               "gleich der Zahl in `price_history_ohlc` mit "
               "`assetklasse=krypto` (DASH 2.722, STX 2.511, DIA 2.196, MDT "
               "2.149, T 1.657, BOND 1.114, C 418). \u2714\u2714 UND DER GRUND STEHT "
               "SEIT DEM 07.09. IM CODE: `simuliere_bremse._reihen_roh` "
               "ueberspringt den 1:1-Filter aus `messreihen`, sobald die "
               "Kerzen ihre Klasse selbst tragen - der Kommentar dort nennt "
               "DASH namentlich. Alle Verbraucher von `klassen_aus_db` "
               "gehen durch diese Funktion, auch `messe_drift_absolut`. "
               "\u27a4 DER SCHEMAFIX IST DAMIT KEINE SPERRE MEHR, sondern "
               "Aufraeumen: `messreihen` fuehrt fuer diese sieben eine "
               "Klasse, die nicht stimmt. Als eigener Planschritt "
               "aufgenommen, nicht nebenbei erledigt - es ist ein "
               "Schemawechsel an einer Messdatenbank mit 5,1 Mio Zeilen. "
               "\u26a0\ufe0f 2.149-prod (die Produktionsdatenbank hat die Spalte gar "
               "nicht) bleibt davon unberuehrt und heute folgenlos: die "
               "Watchlist-Symbole sind eindeutig "
               "✔✔✔ AUFGERAEUMT AM 13.09. (Schritt 50 Teil A, 2.426): "
               "`messreihen` und `messreihen_status` tragen die Klasse "
               "jetzt im Schluessel, die sieben Doppelticker stehen mit "
               "BEIDEN Klassen da. Die Pruefzeile misst seither die "
               "Invariante statt der Kollision - jede (Symbol, Klasse) mit "
               "Kursdaten hat eine Zuordnung",
               "gilt",
               "data/messdaten.db sqlite_master; simuliere_bremse."
               "_reihen_roh Zeilen 143-170; gezaehlt 13.09."),
    Befundlage("2.421-rot", "\u26a0\ufe0f\u26a0\ufe0f EINE PRUEFUNG, DIE DAUERHAFT ROT "
               "IST, IST KEINE PRUEFUNG MEHR. Die Zeile *,`messreihen` und "
               "die Kursdaten sind klassengleich' meldet seit Tagen "
               "dieselben sieben Symbole und wird deshalb ueberlesen - sie "
               "war eine von vier Dauerroten in der Suite. \u27a4 UMGEBAUT ZU "
               "*,KEINE NEUE Klassenkollision': die sieben bekannten stehen "
               "namentlich in der Pruefung, ein ACHTES macht sie rot. Damit "
               "behaelt sie ihre Warnkraft fuer den Fall, der zaehlt - ein "
               "unbemerkter neuer Doppelticker - und verliert die "
               "Abstumpfung. \u26a0\ufe0f DAS IST AUSDRUECKLICH KEIN GRUENFAERBEN: "
               "der Schemamangel bleibt als Planschritt stehen, und die "
               "Pruefung nennt ihn im Begruendungstext. Ein Test an den "
               "Code anzupassen waere die Bewegung, mit der man einen "
               "Defekt zudeckt - hier ist die Sachlage vorher gemessen "
               "worden (2.421)", "gilt",
               "pruefe_pakete Paket Neuaufnahme; Befund 2.421"),
    Befundlage("2.359-abruf-loesung", "\u27a4 2.359-abruf: DIE LOESUNG STEHT, "
               "UND SIE IST NICHT DIE, DIE DER BEFUND NAHELEGT. Nachgesehen "
               "am 13.09.: keine der drei Messquellen fuehrt `fetched_at` - "
               "`funding` und `splycur` haben (symbol, datum, wert), "
               "`terminmarkt_tag` neun Spalten, keine davon ein "
               "Abrufstempel. \u26a0\ufe0f\u26a0\ufe0f ABER EINE SPALTE ALLEIN LOEST ES "
               "NICHT: `MAX(fetched_at)` sagt genau dasselbe wie die "
               "Aenderungszeit der Datei - wann zuletzt geschrieben wurde. "
               "Die Frage des Befundes ist eine andere: *war der Abruf "
               "VOLLSTAENDIG?* \u27a4 DIE BEANTWORTET NUR EINE ZAEHLUNG JE "
               "SYMBOL: wie viele der erwarteten Symbole hat der letzte "
               "Lauf beruehrt? Dafuer braucht es `fetched_at` PRO ZEILE und "
               "eine Erwartungszahl je Quelle (funding 300, terminmarkt "
               "122, splycur 66). Erst beides zusammen trennt ,der Job "
               "laeuft' von ,der Job war vollstaendig'. \u26a0\ufe0f Als "
               "Planschritt aufgenommen - drei Ladeskripte, eine "
               "Leserstelle (`datenfrische._stand_datei`) und eine "
               "Erwartungstabelle gehoeren in EINEN Zug (Vorgabe "
               "KEINE-TEILLOESUNG) "
               "✔✔✔ GEBAUT AM 13.09. (Schritt 50 Teil B, 2.425) - "
               "allerdings ANDERS als hier vorgeschlagen. `fetched_at` PRO "
               "ZEILE waere falsch gewesen: es sagt dasselbe wie die "
               "Dateizeit, und alle INSERTs der Ladeskripte schreiben "
               "positionell, eine vierte Spalte haette sie stumm gebrochen. "
               "Gebaut wurde eine Zeile JE SYMBOL (`abruf_symbol`). Der "
               "Rest dieses Befundes - Zaehlung gegen eine Erwartungszahl - "
               "war richtig und ist so umgesetzt",
               "gilt",
               "PRAGMA table_info der drei Messdatenbanken 13.09.; "
               "agent/datenfrische._stand_datei"),
    Befundlage("2.420", "\u26a0\ufe0f\u26a0\ufe0f\u26a0\ufe0f DIESELBE FEHLERKLASSE ZUM ZWEITEN "
               "MAL AN ZWEI TAGEN: EIN VERSCHOBENES ARGUMENT. Am 12.09. war "
               "es ein Komma in `Schritt(...)`, das den Text zum vierten "
               "Argument machte und `quelle` in `fertig` schob. Heute traf "
               "es `Befundlage`: ein Hilfsskript ersetzte das Stand-Literal "
               "`'offen',` durch `'langer Text', 'gilt',`. Weil `stand` das "
               "DRITTE Argument ist, wurde daraus stand = der lange Text "
               "(gehoerte in die AUSSAGE), quelle = 'gilt' (gehoerte in den "
               "STAND), abgeloest_durch = die echte Quelle (gehoerte in die "
               "QUELLE). \u26a0\ufe0f SECHS BEFUNDE STANDEN SO DA - 2.408-vorbehalt, "
               "2.410, 2.410-loesung, 2.413-dilemma, 2.413-zerfall und "
               "2.415-alle - und ZWEI WEITERE waeren dazugekommen "
               "(2.146-luecke, 2.343), wenn es nicht aufgefallen waere. "
               "\u26a0\ufe0f\u26a0\ufe0f WARUM ES BEIM LESEN NICHT AUFFIEL: der Text war "
               "vollstaendig und stand im Register - nur im falschen Feld. "
               "Gefunden habe ich es beim ZAEHLEN der Stand-Werte, nicht "
               "beim Lesen. Eine Verteilung zeigt, was ein Blick "
               "ueberliest. \u27a4 REPARIERT ueber den Syntaxbaum statt ueber "
               "Textersetzung: alle sechs neu gesetzt, Nachfolger "
               "eingetragen (2.416-norm, 2.414-laenge, 2.417, 2.419). "
               "\u2714\u2714 UND DREI WAECHTER GEBAUT, Paket `Register`: (1) jeder "
               "Befund hat einen STAND, der eines der drei bekannten "
               "Woerter ist - steht dort ein SATZ, ist ein Argument "
               "verschoben; (2) jeder ABGELOESTE nennt seinen Nachfolger "
               "(R-R11: ein Befund faellt nicht weg, er wird ERSETZT); (3) "
               "jeder Befund nennt eine QUELLE. \u2714 Gegengeprueft: ein "
               "absichtlich verdorbener Stand macht das Paket rot, danach "
               "wieder 12 von 12", "gilt",
               "bestand.py; pruefe_pakete Paket Register; Reparatur 13.09."),
    Befundlage("2.419", "✔✔✔ SCHRITT 49 TEIL B GEBAUT: DER BETRIEB "
               "RECHNET JETZT DIESELBE GROESSE WIE DIE MESSUNG - 2.410 "
               "ist geschlossen. ⚠️⚠️ UND ER NANNTE ZWEI UNTERSCHIEDE, "
               "NICHT EINEN; ich hatte zuerst nur den Nenner gesehen. "
               "Beide auf dem vollstaendigen Tag 07.09. gemessen, "
               "frageart `zaehlung`, Gegenprobe je 100,0 %: NENNER "
               "(Umlaufmenge) 86,2 % gleiches Fuenftel, Randwechsel "
               "13,8 % - ZAEHLER (Volumenquelle) nur 57,1 %, "
               "Randwechsel 28,6 %, und der Binance-Anteil am "
               "Gesamtvolumen streut von 0,1 % (TUSD) bis 35,9 % (ICP), "
               "kuerzt sich also nicht weg. Wer nur den Nenner "
               "umstellt, repariert die kleinere Haelfte. "
               "➤ GEBAUT: `marktrang.turnover_werte` nimmt Binance "
               "`/api/v3/ticker/24hr` (BASIS-Volumen in Stueck, ein "
               "Aufruf, 3.701 Paare, schluessellos) geteilt durch die "
               "neue Funktion `marktrang.umlaufmengen()` - `splycur`, "
               "nur lesend, mit Frischegrenze `SPLYCUR_FRISCHE_TAGE = "
               "21`. Dieselbe Paarung `<SYM>USDT` wie "
               "`lade_messreihen.py`. ⚠️ DIE FRISCHEGRENZE IST KEINE "
               "Formalie: `splycur` fuehrt fuenf Reihen, die an der "
               "QUELLE enden (BNB 2019-04-22, DOT und XTZ 2022, GAS und "
               "NEO 2025-10-30). Ohne sie kaeme eine sieben Jahre alte "
               "Umlaufmenge als heutiger Nenner durch", "gilt",
               "agent/marktrang.py; Messungen 13.09. auf dem 07.09.; "
               "Paket Turnoverquelle, 14 Pruefungen"),
    Befundlage("2.419-breite", "✔✔ NEBENWIRKUNG, UND SIE IST DIE "
               "WICHTIGERE: DER BETRIEB SIEHT JETZT 60 STATT 33 "
               "SYMBOLE. Der alte Weg las die CoinGecko-Marktliste "
               "`per_page=250` und schnitt sie mit der MESSBASIS (66) - "
               "uebrig blieben 33. ⚠️⚠️⚠️ DAS WAR DERSELBE "
               "SURVIVORSHIP-SCHNITT, den 2.416 in der MESSUNG gefunden "
               "hat, nur auf der ANWENDUNGSSEITE und seit Wochen "
               "wirksam: die Haelfte der Messbasis bekam keinen "
               "Beitrag, weil sie heute nicht gross genug ist. Binance "
               "fuehrt USDT-Paare ohne Groessenschnitt, damit sind es "
               "60 von 66. ⚠️ DIE MESSMENGE AENDERT SICH DABEI NICHT - "
               "`MESSBASIS[turnover]` bleibt `splycur`, also 66. Es ist "
               "keine Verbreiterung, sondern das Ende eines stillen "
               "Verlusts INNERHALB der bestehenden Menge. ⚠️ Die "
               "restlichen 6 fehlen mit Grund: fuenf, weil ihre "
               "Umlaufmenge an der Quelle endet, eines ohne "
               "USDT-Paarung", "gilt",
               "agent/marktrang.turnover_werte, gezaehlt 13.09."),
    Befundlage("2.419-rr11", "✔✔ R-R11 ERFUELLT, BEVOR ETWAS "
               "ANGETASTET WURDE: der Modulkopf von `marktrang` trug "
               "seit dem 30.08. den Satz *,Rangkorrelation +0,967, und "
               "die Sperrentscheidung waere bei 33 von 33 Symbolen "
               "identisch - der Wechsel ist damit unkritisch.` "
               "Reproduziert am 13.09. auf derselben Menge: 33 "
               "Symbole, Spearman +0,975, Sperrentscheidung 33 von 33 "
               "identisch. ✔ DER BEFUND GILT WEITER und ist nicht "
               "widerlegt. ⚠️⚠️ ER SAGT ABER NUR ETWAS UEBER DIE "
               "SPERRE (Fuenftel 4). Ueber die BEITRAGSSTUFEN sagt er "
               "nichts - dort wandern 4 von 33 Symbolen, alle an der "
               "Grenze Fuenftel 0 zu 1 (XLM und XRP je 1 nach 0). Genau "
               "dort liegt mit +3,15 gegen +0,83 die groesste Stufe des "
               "Systems. ➤ Ein Befund deckt, was er misst - nicht, "
               "was daneben liegt. Der Satz im Modulkopf ist "
               "entsprechend praezisiert, nicht gestrichen", "gilt",
               "agent/marktrang.py Modulkopf (Stand 30.08.); Reproduktion 13.09."),
    Befundlage("2.419-saetze", "⚠️⚠️ NEBENFUND, NICHT VON MIR VERURSACHT UND "
               "NICHT IN DIESEM SCHRITT ZU LOESEN: `pruefe_marktrang.py` "
               "hat zwei rote Zeilen, und sie sind ein VERALTETER TEST, "
               "kein Defekt. `MR.saetze({funding_fuenftel: 4, ...})` "
               "liefert seit der S-2-Aenderung vom 11.09. korrekt ZWEI "
               "Zeilen - den Verfuegbarkeitshinweis (,Heute nicht "
               "verfuegbar: Umschlag, Terminmarkt, Schnittabstand`) und "
               "die Funding-Zeile. Die Pruefung erwartet noch EINE und "
               "liest deshalb auch den Querschnitt an der falschen "
               "Stelle. ⚠️ NACHGEPRUEFT mit `git stash`: beide Zeilen "
               "waren VOR Schritt 49 Teil B schon rot. ➤ Der Test "
               "gehoert nachgezogen - aber in einem eigenen Zug, nicht "
               "nebenbei. Einen Test an den Code anzupassen ist genau "
               "die Bewegung, mit der man einen echten Defekt "
               "zudeckt; sie braucht ihre eigene Begruendung ➤ Getragen von Schritt 55 (Review 14.09.: der Befund hing nur an Schritt 49, der fertig ist).", "offen",
               "pruefe_marktrang.py Abschnitt 6; agent/marktrang.saetze"),
    Befundlage("2.418", "✔✔ SCHRITT 49 TEIL A ERLEDIGT: `splycur` HAT "
               "JETZT EINEN AUFRUF - er hatte bis heute KEINEN. Die Reihe "
               "wurde einmal von Hand geholt, und `hole_fremdreihen.py "
               "onchain` laedt `AdrActCnt`, nicht `SplyCur`. Deshalb lief "
               "sie zwoelf Tage aus dem Takt, ohne dass es auffiel: es gab "
               "keinen Aufruf, den man haette vergessen koennen. ➤ GEBAUT: "
               "`hole_fremdreihen.py splycur`, bewusst NICHT in ,beides' - "
               "`onchain` laedt eine ANDERE Metrik in dieselbe Datei. "
               "✔ GELAUFEN: 66 von 66 Symbolen, 203.546 Tagespunkte "
               "(+867), jetzt bis 2026-09-12. ✔ GEGENGEPRUEFT: die Menge "
               "bleibt bei 66 - `messmenge.ABDECKUNG[turnover]` stimmt "
               "weiter, die Messmenge hat sich NICHT verschoben. ⚠️ Fuenf "
               "Reihen enden trotzdem frueher (BNB 2019-04-22, XTZ und DOT "
               "2022, GAS und NEO 2025-10-30) - nachgeprueft: an der QUELLE "
               "steht nichts danach. Das sind eingestellte Reihen, also der "
               "Survivorship-Schutz, kein Ladefehler. ⚠️ Meine erste "
               "Gegenpruefung war falsch gebaut (Abfrage ab 2026-08-20 gegen "
               "einen Endpunkt von 2019 - sie verglich gegen ein leeres "
               "Fenster und meldete ,ABWEICHUNG')", "gilt",
               "hole_fremdreihen.py splycur; Lauf 13.09."),
    Befundlage("2.418-teilkerze", "⚠️⚠️⚠️ DIE LETZTE ZEILE JEDER "
               "MESSREIHE IST EINE TEILKERZE - gefunden beim Versuch, den "
               "Zaehler zu pruefen. Gegen Binance nachgerechnet: an den "
               "vollstaendigen Tagen stimmt unser Volumen BITGENAU (Faktor "
               "1,000 fuer BTC, ETH, LINK, ADA, SOL am 05., 06. und 07.09.), "
               "am letzten gespeicherten Tag (08.09.) betraegt der Faktor "
               "nur 0,19 bis 0,39. Ursache: `lade_messreihen.py` holt "
               "`interval=1d` und speichert auch die LAUFENDE Kerze - sie "
               "enthaelt das Volumen bis zum Abrufzeitpunkt, nicht des "
               "ganzen Tages. ➤ FUER DIE BEITRAGSMESSUNG ist das folgenlos: "
               "bei H20 kann der letzte Tag ohnehin kein Anker sein, ihm "
               "fehlen die zwanzig Folgetage. ⚠️ FUER JEDE ,HEUTE'-"
               "RECHNUNG ist es das nicht - wer die letzte Zeile als "
               "Tagesvolumen liest, unterschaetzt es um 60 bis 80 %. "
               "⚠️⚠️ UND ES HAT ZWEI MEINER EIGENEN PRUEFUNGEN "
               "VERFAELSCHT: der ,Quelleneffekt im Zaehler' von 50,0 % und "
               "die Probe ,dieselbe Quelle, derselbe Tag' von 61,9 % liefen "
               "beide auf dem 08.09. Die Probe MUSSTE 100 % geben - dass sie "
               "es nicht tat, hat den Fehler aufgedeckt. Eine Gegenprobe, "
               "die man nur mitlaufen laesst, weil sie trivial aussieht, "
               "ist genau dann etwas wert", "gilt",
               "Binance /api/v3/klines gegen data/messdaten.db, 5 Symbole x "
               "4 Tage, 13.09.; lade_messreihen.py"),
    Befundlage("2.418-quelle-stimmt", "✔ RICHTIGSTELLUNG ZU EINER EIGENEN "
               "FEHLDEUTUNG: ich hatte aus dem Docstring von "
               "`api/boersen_klines.py` (*,Kraken bleibt erste Quelle'*) "
               "geschlossen, der Zaehler der MESSUNG sei eine Mischung "
               "verschiedener Boersen - und daraus einen schweren Mangel an "
               "der registrierten Groesse abgeleitet. ✖ FALSCH. Jener "
               "Docstring beschreibt die PRODUKTIONS-Datenbank "
               "(`tradinginfotool.db`); die MESSdatenbank fuellt "
               "`lade_messreihen.py` und traegt `quelle='binance_mess'`. "
               "Nachgezaehlt: alle 66 Symbole der Messbasis haben GENAU "
               "diese eine Quelle, keines hat zwei. ➤ Befund 2.410 hatte "
               "recht - der Zaehler der Messung ist Binance-USDT, "
               "einheitlich. ⚠️ LEHRE: ein Docstring beschreibt das Modul, "
               "in dem er steht, nicht die Datenlage. Die Quelle stand als "
               "SPALTE in der Datenbank und war in einer Abfrage zu "
               "beantworten", "gilt",
               "data/messdaten.db price_history_ohlc.quelle, gezaehlt 13.09.; "
               "lade_messreihen.py Zeile 333"),
    Befundlage("2.417", "⚠️⚠️⚠️ DIE QUELLENSUCHE IST BEENDET UND "
               "SIE HAT NICHTS GEFUNDEN - das ist das ERGEBNIS, nicht das "
               "Scheitern (Vorgabe KEINE-TEILLOESUNG). Gesucht war: freie "
               "historische UMLAUFMENGE oder Marktkapitalisierung, ohne "
               "Schluessel, ohne Groessenschnitt, mehrjaehrig. AN DER "
               "QUELLE GEPRUEFT am 13.09., nicht in Prospekten gelesen: "
               "CoinGecko `market_chart` frei bis GENAU `days=365`, ab "
               "`days=400` hart HTTP 401 (400/500/730/1095/1500 alle 401). "
               "⚠️ 401 ist eine POLICY-Antwort, 429 nur Drosselung - "
               "beide wurden mit bis zu drei Versuchen und 20/40 s "
               "Nachwartezeit getrennt, sonst haette die Drosselung wie ein "
               "Verbot ausgesehen. WEITER: CoinPaprika Katalog 61.486 Werte "
               "frei, Historie HTTP 402 Payment Required; CoinLore Katalog "
               "frei, KEINE Historie; Messari `sply.circ/time-series` HTTP "
               "404; CoinCap alte Domain tot, neue HTTP 401; "
               "CryptoCompare/CoinDesk `blockchain histo/day` HTTP 401; "
               "CoinMarketCap HTTP 401; DefiLlama nur Preise, keine "
               "Umlaufmenge. UND DER AMTSINHABER: Coin Metrics community "
               "fuehrt SplyCur fuer genau 139 Assets - der Katalog "
               "bestaetigt die seit 09.09. bekannte Obergrenze. ➤ ES GIBT "
               "SIE NICHT. Wer mehr Historie will, zahlt oder hat einen "
               "Schluessel - beides schliesst die stehende Vorgabe ,nur "
               "kostenfreie Datenquellen` aus", "gilt",
               "Direktabrufe 13.09.: CoinGecko, CoinPaprika, CoinLore, "
               "Messari, CoinCap, CryptoCompare, CoinMarketCap, DefiLlama, "
               "Coin Metrics catalog-v2"),
    Befundlage("2.417-eigenfehler", "⚠️⚠️⚠️ DER GROESSENSCHNITT AUS "
               "2.416 WAR MEINER, NICHT DER VON COINGECKO - und er ist ohne "
               "neue Quelle behebbar. GEPRUEFT: `coins/list` liefert 21.158 "
               "Werte OHNE jeden Groessenschnitt, und `market_chart` "
               "antwortet auch fuer Werte weit ausserhalb der Top 250 - "
               "SUSHI, YFI, ZRX, BAT je 366 Punkte - und sogar fuer TOTE: "
               "FTT liefert 366 Punkte mit Marktkapitalisierung 0, SRM und "
               "LUNC ebenso. ➤ DER SURVIVORSHIP LAG ALLEIN IM ABRUF "
               "`order=market_cap_desc&per_page=250`. Wer die Symbolliste "
               "aus unseren 536 statt aus der Marktrangliste bildet, "
               "bekommt eine Menge OHNE Groessenschnitt. ⚠️⚠️ WAS "
               "DAMIT NICHT GELOEST IST: die 365-Tage-Grenze. Sie bleibt "
               "der Kalibrierungsblocker (2.416-laenge) und ist keine "
               "Abrufsache, sondern Politik der Quelle", "gilt",
               "Direktabrufe 13.09.; Befunde 2.416, 2.416-laenge"),
    Befundlage("2.417-frische", "✔✔ ZAEHLUNG 2a: EINE 15 TAGE ALTE "
               "UMLAUFMENGE SCHADET NICHT - 98,9 % der Anker behalten ihr "
               "Fuenftel, 0,0 % liegen um zwei oder mehr Stufen daneben, "
               "0,6 % wechseln in oder aus einem RANDFUENFTEL (dort haengen "
               "die groessten Stufen, +3,15 und -2,40). Gemessen auf "
               "123.047 gemeinsamen Ankern, 66 Symbole, H20, mit dem ECHTEN "
               "Code (`MB.reihe` + `K.baue` wie `rechne_turnover_beitrag`) "
               "- nur die Menge wurde getauscht. ⚠️ GEGENPROBE ZUERST: "
               "Wahrheit gegen Wahrheit ergibt 100,0 %. ZUR EINORDNUNG: der "
               "Praezedenzfall im System ist die Schnitt-Frischegrenze, "
               "gezogen bei 93,5 % identischen Fuenfteln (10 Tage alt) - "
               "98,9 % liegt deutlich darueber. ⚠️⚠️⚠️ UND DER "
               "VERZUG IST OHNEHIN UNSER FEHLER, NICHT DER DER QUELLE: Coin "
               "Metrics fuehrt SplyCur fuer BTC, ETH und LINK bis "
               "2026-09-12, unsere Kopie endet am 2026-08-28/29. Das ist "
               "eine ABRUFLUECKE von 15 bis 16 Tagen - sie wird "
               "nachgeladen, nicht wegdiskutiert", "gilt",
               "frageart `zaehlung`, Menge: die 66 Symbole mit `splycur` in "
               "messmenge.V1, H20; Coin Metrics timeseries 13.09."),
    Befundlage("2.417-naeherung", "⚠️⚠️ ZAEHLUNG 2b: DIE KONSTANTE "
               "UMLAUFMENGE IST KEINE BRAUCHBARE NAEHERUNG - jedenfalls "
               "nicht auf der ganzen Historie. Heutige Menge rueckwaerts "
               "konstant angesetzt, gegen die Wahrheit: ganze Historie nur "
               "81,7 % gleiches Fuenftel, 3,7 % um 2+ Stufen daneben, "
               "10,4 % Randfuenftel gewechselt. ✔ DER FEHLER HAENGT AM "
               "ZEITFENSTER, sauber monoton: ab 2022 86,1 % · ab 2023 "
               "88,1 % · ab 2024 90,1 % · ab 2025 93,6 %. ✔ UND ER "
               "HAENGT AN WENIGEN WERTEN: ab 2023 tragen ihn WNXM (91 % "
               "falsch), MKR (84 %), SNX (77 %), PAXG (55 %) und USDC "
               "(45 %) - ohne die zehn schlechtesten steigt die "
               "Uebereinstimmung auf 93,5 % und der Randwechsel faellt auf "
               "3,0 %. ⚠️ MKR -91 % und WNXM +40.215.118 % sind "
               "Token-Umstellungen, also der bekannte Datenfehler und keine "
               "echte Emission. ➤ URTEIL: bei 88,1 % ab 2023 liegt die "
               "Naeherung UNTER dem Praezedenzfall 93,5 %, und die "
               "Randfuenftel - die wirksamsten - irren in 6,0 % der Faelle. "
               "Als ERSATZ fuer eine echte Umlaufmenge taugt sie nicht. Als "
               "AUSWEITUNG auf Symbole, fuer die es gar keine gibt, bleibt "
               "sie offen - dann aber mit ausgeschlossenen "
               "Umstellungswerten und benanntem Fenster", "gilt",
               "frageart `zaehlung`, Menge: die 66 Symbole mit `splycur` in "
               "messmenge.V1, H20, 123.079 bzw. 66.399 Anker"),
    Befundlage("2.416", "⚠️⚠️⚠️ DIE NEUE TURNOVER-QUELLE IST EIN "
               "SURVIVORSHIP-FILTER - UND DAMIT VERLETZT SIE DIE "
               "EINGEFRORENE MESSMENGE. Gezaehlt am 13.09. gegen "
               "`messmenge.V1` (536 Symbole, davon 172 EINGESTELLTE Reihen "
               "= 32 %): ALT `splycur` 66 Symbole, davon 19 eingestellt "
               "(29 %) - NEU CoinGecko 109 Symbole in V1, davon nur 4 "
               "eingestellt (4 %). ➤ DIE NEUE BASIS IST KEINE "
               "OBERMENGE: 33 Symbole liegen in BEIDEN, 76 nur neu - und "
               "33 FALLEN WEG (ALPHA, BAT, MKR, SUSHI, WBTC, YFI, ZRX, "
               "FTT, SRM, REN ...). ⚠️⚠️ DIE URSACHE STEHT IM ABRUF: "
               "`coins/markets?order=market_cap_desc&per_page=250&page=1` "
               "ist die Liste der HEUTE groessten 250. Genau das verbietet "
               "`messmenge.py` woertlich: *,Nicht nach Marktkapitalisierung "
               "filtern. Das waere Survivorship durch die Hintertuer: gross "
               "ist, was gross GEWORDEN ist.'* Und: *,Die eingestellten "
               "Reihen sind kein Ballast, sie sind der Schutz.'* ➤ Die "
               "Verdreifachung aus 2.412 (66 auf 246) ist auf der Messmenge "
               "keine: dort sind es 66 auf 109, und der Zugewinn ist "
               "einseitig nach oben ausgewaehlt. ⚠️⚠️ DIE GEGENPRUEFUNG "
               "TRENNT DIE BEIDEN URSACHEN UND SCHLIESST DEN ZUFALL AUS: von "
               "den 33 Weggefallenen sind 18 EINGESTELLT (der Survivorship-"
               "Schnitt) und 15 LAUFEN NOCH (BAT, SUSHI, WBTC, YFI, ZRX, "
               "FLOW, LPT ... - sie sind nur aus den Top 250 gerutscht). Und "
               "der Anteil Eingestellter misst die Verzerrung direkt: V1 "
               "gesamt 32 %, ALT `splycur` 29 % - REPRAESENTATIV -, NEU 4 % "
               "- um den Faktor acht daneben", "gilt",
               "messmenge.py Zuschnitt; data/markt_historie.db gegen "
               "messmenge.V1, gezaehlt 13.09."),
    Befundlage("2.416-laenge", "⚠️⚠️ DIE NEUE BASIS KANN NICHT "
               "KALIBRIEREN - SIE IST ZU KURZ, und das ist an unseren "
               "eigenen Zahlen entschieden, nicht geschaetzt. Neu: 366 Tage "
               "(2025-09-13 .. 2026-09-12), 39.320 Anker auf den 109 "
               "V1-Symbolen. Registriert ist `turnover` auf 2.636 "
               "KALENDERTAGEN. ⚠️ 2.414-laenge hat gemessen, dass 341 "
               "Tage fuer eine Fuenftel-Ordnung NICHT REICHEN: von 20 "
               "zufaelligen 341-Tage-Fenstern aus dem ganzen Zeitraum sind "
               "nur 5 geordnet - unabhaengig davon, wo sie liegen. ➤ EINE "
               "NEUKALIBRIERUNG AUF DER NEUEN BASIS IST DAMIT NICHT "
               "VERFUEGBAR, und auch die Reproduktion nach R-R11 ist es "
               "nicht: man kann einen 2.636-Tage-Befund nicht auf 366 Tagen "
               "reproduzieren. Das ist kein Mangel des Laufs, sondern die "
               "freie Grenze der Quelle (`days=max` verlangt einen "
               "Schluessel, HTTP 401, geprueft 12.09.)", "gilt",
               "data/markt_historie.db 13.09.; Befund 2.414-laenge; "
               "REGISTER_Kandidaten Zeile 68"),
    Befundlage("2.416-reihenfolge", "⚠️⚠️⚠️ ,ERST DEN BETRIEB "
               "UMSCHALTEN, DANN KALIBRIEREN' IST PER KONSTRUKTION "
               "AUSGESCHLOSSEN - ich hatte es selbst vorgeschlagen, und der "
               "Code sagt woertlich das Gegenteil. `marktrang.MESSBASIS` "
               "IST definiert als *,die Symbole, auf denen die "
               "Beitragstabelle ENTSTANDEN ist. Nur hier gilt, was "
               "`rechne_turnover_beitrag.py` ausgerechnet hat'* - und "
               "darunter: *,FEHLT DIE MESSBASIS, GIBT ES KEINEN RANG. Ein "
               "Rang ueber die falsche Menge saehe genauso aus wie ein "
               "richtiger - und niemand koennte ihm widersprechen.'* ⚠️ "
               "WIE TEUER DER FEHLER IST, IST GEMESSEN: am 31.08. bekamen "
               "von 293 gemeinsamen Symbolen nur 56 % dasselbe Fuenftel "
               "wie in der Messung, Abweichung bis zu DREI Stufen; bei "
               "`schnitt` DREHTE das Vorzeichen (+3,43 auf -3,10), als der "
               "Rang ueber die falsche Menge lief. ➤ Wer den Betrieb auf "
               "109 Symbole stellt und die auf 66 kalibrierte Tabelle "
               "(+3.15 bis -2.40, die groessten Stufen im System) darauf "
               "anwendet, baut 2.410 NEU AUF, nur andersherum: nicht mehr "
               "Messung gegen Anwendung, sondern Tabelle gegen Menge", "gilt",
               "agent/marktrang.py Zeilen 94-124, 335-341; Nutzerfrage "
               "13.09."),
    Befundlage("2.416-norm", "⚠️⚠️ MEINE EIGENE ZEITFENSTERMESSUNG IST "
               "KEIN BEFUND NACH DER MESSNORM - Selbstkorrektur, bevor sie "
               "eine Entscheidung traegt. Die Zahlen aus 2.414 (bis 2022 "
               "Spanne +2,77 ohne Ordnung, ab 2023 +8,64 geordnet) sind "
               "nackte Fuenftel-Median-Spannen: OHNE Band "
               "(Block-Bootstrap, Block ≥ 3x Horizont), OHNE "
               "Trennschaerfe gegen den Nullpunkt, OHNE Positivkontrolle. "
               "`messnorm` verlangt alle drei und kennt genau drei Urteile "
               "- TRAEGT, TRAEGT NICHT, KEIN BEFUND. Ohne Band ist keines "
               "davon aussprechbar. ➤ SIE SIND HINWEISE, KEINE BEFUNDE. "
               "⚠️ DASS SIE TROTZDEM ETWAS WERT SIND, liegt an einer "
               "unabhaengigen Quelle: G2 vom 06.09. hat dieselbe Richtung "
               "normgerecht gefunden (*,juengere Epoche STAERKER, +0,0172 "
               "gegen +0,0137'*). Meine Zahl REPRODUZIERT einen "
               "registrierten Befund - sie stuerzt keinen um. ⚠️⚠️ UND "
               "FUER DIE ANDEREN BEITRAEGE IST DIE FRAGE BEREITS BEANTWORTET "
               "(07.09., S-7, mit Band und Trennschaerfe): `oi_aenderung` "
               "ganz +0,0296 / ab 2022 +0,0296 / ab 2024 +0,0287 - stabil "
               "bis 0,05 R; `funding` +0,0446 / +0,0157 / +0,0182 - stabil "
               "bis 0,05 R; `turnover` auf der 50-%-Menge ab 2022 +0,0598, "
               "stabil bis 0,10 R. ➤ KEIN TRAGENDER BEITRAG BRAUCHT WEGEN "
               "DES ZEITFENSTERS EINE NEUKALIBRIERUNG. Die Frage aus "
               "2.415-alle ist damit fuer `funding` und `oi_aenderung` "
               "NICHT mehr offen - sie war schon gemessen, und ich habe sie "
               "als offen gefuehrt", "gilt",
               "messnorm.standardzeile(); Befund 2.414; REGISTER_Kandidaten "
               "G2 06.09.; project_zeitstabilitaet_geklaert 07.09."),
    Befundlage("2.415", "✔✔ DIE VERTEILUNGSMESSUNG BEANTWORTET DIE OFFENE "
               "FRAGE AUS 2.414-laenge - UND KORRIGIERT MEINE EIGENE SORGE. "
               "Nutzerauftrag 13.09.: *,wenn es nur um Turnover geht, musst "
               "du vorher wissen was zu tun ist und damit vorher "
               "durchpruefen - Verteilungsmessung.'* GEMESSEN: 344 "
               "zusammenhaengende Fenster von je 341 Tagen (jede Woche "
               "eines), Spanne der Fuenftel-Tabelle je Fenster. VERTEILUNG: "
               "Minimum -13,41 · 10. Perzentil -1,81 · MEDIAN +8,20 · 90. "
               "Perzentil +14,58 · Maximum +21,65. ⚠️ DAS LETZTE JAHR LIEGT "
               "BEI +3,31 UND DAMIT AUF DEM 38. PERZENTIL - im normalen "
               "Bereich, nicht auffaellig. ➔ `turnover` WIRD NICHT "
               "SCHWAECHER. ⚠️⚠️ MEIN FRUEHERER VERGLEICH WAR IRREFUEHREND: "
               "ich hatte +3,31 gegen einen Median von +10,80 gestellt, der "
               "aus nur ZWANZIG Ziehungen stammte. Mit 344 Fenstern liegt "
               "der Median bei +8,20 - zwanzig Ziehungen sind kein "
               "Nullmodell, und ich habe daraus eine Sorge abgeleitet, die "
               "die Daten nicht hergeben. ✔ UND DIE ZWEITE ZAHL "
               "BESTAETIGT SICH: nur 37 von 172 Fenstern sind geordnet = 22 "
               "%%. Ein ungeordnetes Jahresfenster ist der NORMALFALL",
               "gilt", "Verteilungsmessung 13.09.; korrigiert 2.414-laenge"),
    Befundlage("2.415-alle", "⚠️⚠️⚠️ DIE ZEITFENSTERFRAGE WIRKT BEI JEDEM BEITRAG ANDERS - "
               "eine Neukalibrierung ist deshalb NICHT neutral. Nutzerauftrag "
               "13.09.: *,welche Indikatoren sind betroffen und was bedeutet "
               "das fuer das Gesamtsystem'*. GEMESSEN, alle drei mit "
               "derselben Mechanik, H20, Haelften gleich lang: TURNOVER ganz "
               "+5,70 (geordnet) · bis 2022 +2,77 (nein) · ab 2023 +8,64 (JA) "
               "-> WIRD UM DIE HAELFTE STAERKER. FUNDING ganz +2,52 (nein) · "
               "bis 2022 +3,23 (nein) · ab 2023 +1,94 (nein) -> WIRD "
               "SCHWAECHER, und es ist in KEINEM Fenster geordnet: Fuenftel 1 "
               "liegt ueber Fuenftel 0. SCHNITT ganz +3,23 (nein) · bis 2022 "
               "+3,18 (nein) · ab 2023 +3,30 (JA) -> wird ERSTMALS geordnet, "
               "bei gleicher Spanne. ➔ EINE UMSTELLUNG AUF ab-2023 VERSCHIEBT "
               "DIE GEWICHTE ZWISCHEN DEN BEIDEN LIVE-BEITRAEGEN: turnover "
               "+52 %%, funding -23 %%. Das ist eine Aenderung an der "
               "Bewertung, nicht an einer Messung. ⚠️ Und der Nebenbefund "
               "ueber `funding` ist eigenstaendig: es ist in keinem der drei "
               "Fenster monoton - das gehoert geprueft, unabhaengig von jeder "
               "Umstellung ⚠️⚠️⚠️ ABGELOEST AM 13.09. DURCH 2.416-norm - DIE "
               "FRAGE WAR SCHON BEANTWORTET. S-7 vom 07.09. hat `funding`, "
               "`oi_aenderung` und `turnover` mit Band und Trennschaerfe "
               "ueber dieselben Fenster gemessen; kein tragender Beitrag "
               "braucht wegen des Zeitfensters eine Neukalibrierung. Ich habe "
               "die Frage zwei Tage spaeter schlechter gestellt und als offen "
               "gefuehrt",
               "abgeloest",
               "Messung 13.09.; Nutzerauftrag Punkt 1",
               abgeloest_durch="2.416-norm",
               warum="die Frage war am 07.09. mit Band und Trennschaerfe beantwortet (S-7) - ich habe sie zwei Tage spaeter schlechter gestellt und als offen gefuehrt"),
    Befundlage("2.414", "✔✔✔ DIE NUTZERTHESE IST BELEGT - UND SIE DREHT DAS "
               "ERGEBNIS UM. Nutzermeinung 13.09.: *,der Kryptomarkt vor "
               "sieben Jahren ist nicht mehr mit heute vergleichbar, die "
               "letzten 3 bis 4 Jahre haben die meiste Aussagekraft.'* "
               "GEMESSEN auf der alten Basis, H20, gleiche Laenge in beiden "
               "Haelften (je 1.327 Tage): BIS 2022 -> (+1,59 / +1,63 / +0,46 "
               "/ -2,49 / -1,18), Spanne +2,77, KEINE Ordnung. AB 2023 -> "
               "(+4,82 / +0,19 / -0,10 / -1,09 / -3,81), Spanne +8,64, "
               "SAUBER GEORDNET. ⚠️⚠️ Die registrierte Tabelle (+5,70 ueber "
               "sieben Jahre) ist also ein MITTELWERT AUS EINER GUTEN UND "
               "EINER SCHLECHTEN HAELFTE - auf den letzten Jahren ist der "
               "Beitrag um die Haelfte STAERKER. ⚠️ Je Jahr wird es noch "
               "deutlicher: 2019 laeuft mit -16,67 UMGEKEHRT, 2020 mit "
               "+16,46 sauber geordnet, danach schwankt es. Ab 2022 ist die "
               "Tabelle geordnet (+6,99), ab 2023 ebenfalls (+8,64). ➔ WER "
               "die Tabelle heute kalibriert, sollte NICHT sieben Jahre "
               "nehmen", "gilt",
               "Nutzermeinung 13.09.; Messung je Jahr 13.09."),
    Befundlage("2.414-laenge", "⚠️ DER ,ZERFALL IM LETZTEN JAHR' AUS "
               "2.413-zerfall IST GROESSTENTEILS DIE LAENGE, nicht die Zeit "
               "- aber nicht ganz. GEGENPROBE: 20 ZUFAELLIGE Fenster von je "
               "341 Tagen aus dem ganzen Zeitraum. Nur 5 von 20 sind "
               "geordnet - ein 341-Tage-Fenster ist also zu drei Vierteln "
               "ungeordnet, ganz gleich WANN es liegt. ➔ Damit ist ,keine "
               "Ordnung im letzten Jahr' KEIN Befund ueber die Zeit. ⚠️ "
               "ABER die SPANNE ist es moeglicherweise doch: der Median der "
               "zwanzig Fenster liegt bei +10,80, das letzte Jahr bei +3,31 "
               "- deutlich darunter. Ob das auffaellig ist, sagt diese "
               "Ziehung nicht (keine Verteilung, keine Trennschaerfe). ➔ "
               "ZWEI FOLGEN: (1) die NEUE Basis mit ihren 365 Tagen reicht "
               "fuer eine eigene Fuenftel-Kalibrierung NICHT - das ist jetzt "
               "belegt und nicht mehr Meinung; (2) ob `turnover` zuletzt "
               "schwaecher wird, bleibt offen und braucht eine eigene "
               "Messung mit Verteilung", "gilt",
               "Zufallskontrolle 20 Fenster 13.09.; Befund 2.413-zerfall"),
    Befundlage("2.414-verwendung", "📇 WO DIE BEIDEN BASEN IM SYSTEM "
               "VERWENDET WERDEN (Nutzerauftrag 13.09.). ALTE BASIS "
               "(`onchain_historie.db` / `splycur`): (1) ⚠️ IM BETRIEB - "
               "`marktrang.MESSBASIS` fuehrt `turnover` mit *,SELECT "
               "DISTINCT symbol FROM splycur'*. Diese Liste entscheidet, "
               "WELCHE Symbole als vermessen gelten, und damit, wo der "
               "Beitrag ueberhaupt wirken darf - die 66 Symbole sind also "
               "nicht nur eine Messgrenze, sondern eine BETRIEBSGRENZE. (2) "
               "`datenfrische` ueberwacht die Datei auf Alter. (3) 22 "
               "Messwerkzeuge lesen `splycur`. NEUE BASIS "
               "(`markt_historie.db`): bisher NUR `hole_fremdreihen` "
               "(schreibt) und `messe_kandidaten_als_regel` (kann sie ueber "
               "die Art `turnover_markt` lesen) - im Betrieb noch nirgends. "
               "➔ EINE UMSTELLUNG WAERE KEIN AUSTAUSCH EINER DATEI: sie "
               "veraendert ueber `MESSBASIS` auch, auf welchen Symbolen der "
               "Beitrag live wirkt - von 66 auf 246", "gilt",
               "grep 13.09.; agent/marktrang.py Zeile 340"),
    Befundlage("2.413", "✔ R-R11 ERFUELLT: die Reproduktion trifft den "
               "registrierten Anker. `rechne_turnover_beitrag.py --horizont "
               "20` auf der ALTEN Basis liefert (+3,20 / +0,91 / +0,18 / "
               "-1,79 / -2,50) gegen registriert (+3,15 / +0,83 / +0,22 / "
               "-1,79 / -2,40) - 2.654 Kalendertage gegen 2.636 bei der "
               "Registrierung, die kleinen Abweichungen stammen aus den "
               "seither dazugekommenen Tagen. Dauer: 7 Sekunden. ⚠️ Damit "
               "ist die Vorbedingung fuer jede Aenderung an dieser Groesse "
               "erfuellt (R-R11: wer die Basis wechselt und ein anderes "
               "Ergebnis bekommt, hat nichts widerlegt - er hat etwas "
               "anderes gemessen)", "gilt",
               "rechne_turnover_beitrag.py 13.09.; REGISTER_Kandidaten"),
    Befundlage("2.413-zerfall", "⚠️⚠️⚠️ DIE REGISTRIERTE TABELLE IST IM LETZTEN JAHR NICHT "
               "REPRODUZIERBAR - UND ZWAR AUF BEIDEN BASEN. Gemessen mit "
               "gemeinsamem Zeitfenster (Vorgabe: sonst misst man den "
               "Kalender), Horizont 20, dieselbe Mechanik: ALT ueber 2.654 "
               "Tage (+3,20 / +0,91 / +0,18 / -1,79 / -2,50, Spanne +5,70, "
               "sauber geordnet) · ALT ueber die letzten 341 Tage (+3,86 / "
               "-1,89 / -1,70 / -0,81 / +0,55, Spanne +3,31) · NEU ueber "
               "dieselben 341 Tage (+1,28 / -1,25 / -0,03 / -0,42 / +0,42, "
               "Spanne +0,87). ⚠️ IN BEIDEN KURZEN FASSUNGEN GIBT ES KEINE "
               "ORDNUNG MEHR: Fuenftel 1 ist schlechter als Fuenftel 4. ➔ DER "
               "UNTERSCHIED IST ALSO NICHT DIE DATENQUELLE - er ist der "
               "ZEITRAUM. Die schoene Monotonie stammt aus sieben Jahren; im "
               "letzten Jahr traegt `turnover` auf KEINER der beiden Basen. "
               "⚠️⚠️ WAS DAS NICHT IST: ein Widerruf. 341 Tage sind wenig, es "
               "ist keine Trennschaerfe gerechnet und kein Nullmodell "
               "gefahren - ein Fuenftel-Median ueber 341 Tage rauscht. Und "
               "2.163 hat die Zeitstabilitaet ueber HAELFTEN der Historie "
               "gemessen und ,stabil bis 0,10 R' gefunden. ⚠️ WAS ES IST: ein "
               "Hinweis, der VOR jeder Umstellung geklaert gehoert - und der "
               "einen der zwei tragenden Beitraege betrifft ✔ ERKLAERT AM "
               "13.09.: der Zerfall ist zu drei Vierteln die LAENGE "
               "(2.414-laenge) und im Rest das ZEITFENSTER (2.414) - NICHT "
               "die Datenquelle",
               "abgeloest",
               "Messung 13.09. mit gemeinsamem Zeitfenster; Befunde 2.163, "
               "2.410",
               abgeloest_durch="2.414-laenge",
               warum="der Zerfall ist zu drei Vierteln die LAENGE des Fensters und im Rest das ZEITFENSTER - nicht die Datenquelle, wie der Befund vermutete"),
    Befundlage("2.413-dilemma", "⚠️⚠️ DAS DILEMMA, DAS TEIL 3 ZU ENTSCHEIDEN HAT - und es ist "
               "keine Kleinigkeit. Die beiden Basen sind nicht ,alt gegen "
               "neu', sondern jede hat einen Mangel, den die andere nicht "
               "hat: ALTE BASIS - sieben Jahre Historie (2.654 Tage), aber "
               "die FALSCHE Menge (Gesamtausgabe statt umlaufend, bei 16 von "
               "33 Symbolen um 5 bis 74 %% daneben) und nur 66 Symbole; "
               "ausserdem Stueckvolumen EINER Boerse. NEUE BASIS - die "
               "richtige Groesse aus EINER Quelle, 246 Symbole, USD-Volumen "
               "ALLER Boersen, aber nur 365 Tage: mehr gibt CoinGecko ohne "
               "Schluessel nicht her (`days=max` -> HTTP 401). ➔ EINE "
               "UMSTELLUNG WUERDE DIE TABELLE AUF EINEM SIEBTEL DER HISTORIE "
               "NEU KALIBRIEREN. Das ist nicht automatisch besser - es "
               "tauscht einen Fehler in der GROESSE gegen einen Mangel an "
               "DATEN. ⚠️ Und im kurzen Fenster traegt keine von beiden "
               "(2.413-zerfall), also entscheidet die Messung die Frage "
               "derzeit nicht ✔✔ AUFGELOEST AM 13.09. DURCH 2.416-laenge UND "
               "2.417 - es gibt kein Dilemma mehr, weil die neue Basis gar "
               "nicht zur Wahl steht: 366 Tage koennen nicht kalibrieren, und "
               "eine freie Quelle mit Historie existiert nicht. Es bleibt bei "
               "den 66 Symbolen",
               "abgeloest",
               "Befunde 2.410, 2.413-zerfall; Schritt 49 Teil 3",
               abgeloest_durch="2.417",
               warum="das Dilemma setzte voraus, dass die neue Basis zur Wahl steht. Sie steht nicht zur Wahl: 366 Tage koennen nicht kalibrieren, und eine freie Quelle mit Historie gibt es nicht"),
    Befundlage("2.412", "✔✔ SCHRITT 49 TEIL 1 FERTIG: 246 SYMBOLE, 365 "
               "TAGE, 81.424 TAGESPUNKTE in `data/markt_historie.db`. Von "
               "250 Symbolen der Marktliste kamen 246 durch; vier blieben an "
               "der Drosselung haengen und koennen jederzeit nachgeholt "
               "werden - der Lauf ueberspringt, was aktuell ist. ⚠️ ZUM "
               "VERGLEICH: die bisherige Messbasis fuer `turnover` sind 66 "
               "Symbole aus `onchain_historie.db`. Das ist eine "
               "Verdreifachung, und sie trifft genau den registrierten "
               "VORBEHALT der Groesse: *,Nur 65 Symbole Abdeckung - das "
               "Nullband ist dreimal so breit wie bei den anderen, das "
               "Urteil wandert mit der Saat.'* Und 2.162-grund sagt es noch "
               "deutlicher: *,turnover deckt 66 von 524 Symbolen ab. 20 %% "
               "davon sind 10,1 Anker je Tag - und N-65 hat gemessen, dass "
               "die Statistik bei so kleinen Gruppen fast nur Rauschen "
               "ist.'* ➔ Die neue Basis macht die Frage moeglicherweise "
               "ERST ENTSCHEIDBAR - sie misst nicht nur sauberer", "gilt",
               "hole_fremdreihen.py; data/markt_historie.db 13.09."),
    Befundlage("2.412-lage", "⚠️⚠️ DER REGISTRIERTE STAND VON `turnover` IST "
               "SCHWAECHER, ALS ICH IHN BEHANDELT HABE - nachgelesen im "
               "Register, bevor Teil 2 beginnt. REGISTRIERT: ,traegt', "
               "Regler, H20, Anker +0,0616 R, auf der selektierten Menge "
               "reproduziert mit +0,0635 (F-212). ⚠️ ABER: 2.191 - "
               "*,turnover KIPPT auf seiner einzigen Basis frei: Abstand "
               "+0,0018 (alt) -> -0,0008 (neu), Urteil NICHT TRENNBAR'*; "
               "2.192 - *,turnover traegt NIRGENDS mehr'* unter der stabilen "
               "Nullregel; 2.196 - *,nicht widerlegt, sondern UNENTSCHIEDEN: "
               "ausgeschlossen sind nur Effekte ab 0,20 R, seine gemessene "
               "Wirkung betraegt +0,0639 - ueber DIESE Groesse sagt die "
               "Anlage nichts.'* ➔ WAS DAS FUER TEIL 2 HEISST: die "
               "Reproduktion nach R-R11 muss den Anker +0,0616 auf der "
               "SELEKTIERTEN Menge treffen (nicht auf `frei` - dort war er "
               "nie belegt). Und der Ausgang ist offener als gedacht: "
               "turnover koennte auf der breiten Basis erstmals TRAGEN - "
               "oder endgueltig fallen. Beides ist ein Ergebnis", "gilt",
               "REGISTER_Kandidaten Zeile 16/68; Befunde 2.191, 2.192, "
               "2.196, 2.162-grund"),
    Befundlage("2.411", "✔✔ SCHRITT 49 TEIL 1 GEBAUT: DIE TURNOVER-HISTORIE "
               "KOMMT AUS EINER KUERZUNG, NICHT AUS EINER NEUEN QUELLE. "
               "`hole_fremdreihen.turnover()` - KEIN neues Skript, sondern "
               "eine dritte Funktion neben `funding()` und `onchain()`, "
               "damit Wiederholung, Pausen und Tagesverdichtung nur einmal "
               "existieren. Sie holt `market_chart?days=365&interval=daily` "
               "je Symbol und rechnet `total_volumes / market_caps` - die "
               "Umlaufmenge KUERZT SICH heraus, also kann keine zweite "
               "Quelle mehr abweichen (das war 2.410). Ziel: "
               "`data/markt_historie.db`, Tabelle `turnover`, Schema wie die "
               "anderen (symbol, datum, wert). ⚠️ VORABTEST VOR DEM LANGEN "
               "LAUF (stehende Vorgabe): drei Symbole, 365 Tagespunkte "
               "jeweils, gegen die Live-Funktion gegengerechnet - ADA -0,01 "
               "%%, LINK +0,05 %%, BTC -0,22 %%. ⚠️⚠️ UND GENAU DIE 250 VON "
               "SEITE 1: `marktrang.turnover_werte` liest "
               "`per_page=250&page=1`, und wer hier breiter laedt, misst "
               "wieder etwas anderes als der Betrieb anwendet - 2.410 neu "
               "aufgebaut, nur andersherum. Die Suite prueft, dass BEIDE "
               "Seiten dieselbe Seite lesen. ⚠️ `days=365` ist die freie "
               "Grenze: `days=max` beantwortet CoinGecko ohne Schluessel mit "
               "HTTP 401. ✔ Paket ,Turnoverquelle', 10 Pruefungen", "gilt",
               "hole_fremdreihen.py; Vorabtest 12.09.; Befund 2.410-loesung"),
    Befundlage("2.411-import", "⚠️ ZUM ZWEITEN MAL AN EINEM TAG: "
               "`sys.stdout.reconfigure` auf MODULEBENE macht ein Werkzeug "
               "unimportierbar. `pruefe_pakete` ersetzt `sys.stdout` durch "
               "einen Mitschnitt, und der kennt die Methode nicht - das "
               "Paket brach beim Import ab, bevor eine einzige Pruefung "
               "lief. Erst bei `messe_ausstiegsguete`, dann bei "
               "`hole_fremdreihen`. ➔ REGEL: die Umstellung gehoert in "
               "`main()` oder in ein `try`, nie auf die Modulebene. Ein "
               "Werkzeug, das man nicht importieren kann, kann man auch "
               "nicht pruefen - und genau das ist der Zweck. ⚠️⚠️ UND EIN "
               "ZWEITER, TEURERER SCHAETZFEHLER AM SELBEN WERKZEUG: ich "
               "habe die Dauer mit ,rund zehn Minuten fuer 250 Symbole' "
               "angegeben, gestuetzt auf ,die freie Grenze liegt bei "
               "etwa 30 Anfragen je Minute'. GEMESSEN am echten Lauf: 2 "
               "Symbole je Minute - hochgerechnet 125 MINUTEN. Der "
               "Grund: CoinGecko antwortet mit HTTP 429, und jede "
               "Wiederholung kostet zusaetzlich. Der Abruf selbst dauert "
               "0,2 Sekunden; die Zeit geht vollstaendig fuer abgewiesene "
               "Anfragen drauf. ✔ BEHOBEN: Pause auf 6 s (rund zehn "
               "Anfragen je Minute, etwa 25 Minuten fuer 250 Symbole) "
               "und ein 429 wird als ANSAGE behandelt - 15, 30, 45 "
               "Sekunden statt der allgemeinen Wiederholungspause. Wer es "
               "eilig hat, gewinnt nichts: mit 2,2 s dauerte derselbe "
               "Lauf fuenfmal so lange. ⚠️ Die Vorgabe *,vor jedem "
               "Messlauf Limits und Dauer' war eingehalten - die ZAHL "
               "war trotzdem falsch, weil sie aus der Doku stammte und "
               "nicht aus einer Messung. ⚠️⚠️ UND DANN NOCH EINMAL: auch "
               "die KORREKTUR war geraten. 6 s brachten den Lauf ganz zum "
               "Stehen - die Drosselung traf danach sogar `/ping`, null "
               "Symbole in einer Minute. Erst ein Test mit sechs "
               "Anfragen hintereinander zeigte, was traegt: bei 8 s "
               "Pause (7,5 Anfragen/Minute) kamen 6 von 6 durch. ➔ 250 "
               "Symbole = rund 33 Minuten. ⚠️ DREI ANLAEUFE FUER EINE "
               "ZAHL, die man in vier Minuten messen kann - das ist die "
               "eigentliche Lehre, nicht die Zahl. ✔ Die Drosselung ist "
               "KEIN Bann: sie loest sich in unter einer Minute. ✔ Und "
               "der Lauf ist jetzt WIEDERAUFNEHMBAR (Symbole mit Daten "
               "bis gestern werden uebersprungen) - ohne das haette der "
               "zweite Abbruch die ersten 45 Symbole noch einmal "
               "gekostet. ⚠️ WER ES EILIGER BRAUCHT: ein "
               "CoinGecko-Demo-Schluessel ist frei (30 Anfragen/Minute, "
               "10.000 im Monat) - das waere eine Abhaengigkeit mehr und "
               "eine Nutzerentscheidung; ohne ihn geht es auch", "gilt",
               "pruefe_pakete.py; messe_ausstiegsguete.py; "
               "hole_fremdreihen.py"),
    Befundlage("2.410", "⚠️⚠️⚠️ DER GEMESSENE UND DER ANGEWENDETE `turnover` SIND "
               "NICHT DIESELBE GROESSE - bei der HAELFTE der Symbole. "
               "Gefunden am 12.09. beim Suchen nach einer P-Scan-Datenbasis, "
               "betrifft aber den LAUFENDEN BETRIEB und einen der ZWEI "
               "tragenden Beitraege. DIE FORMEL IST BEIDE MALE `Volumen / "
               "(Preis x Umlaufmenge)` - aber die UMLAUFMENGE kommt aus zwei "
               "verschiedenen Quellen: `rechne_turnover_beitrag.py` nimmt "
               "`splycur` aus `data/onchain_historie.db` (66 Symbole), "
               "`marktrang.turnover_werte()` nimmt `circulating_supply` von "
               "CoinGecko. GEMESSEN an 33 vergleichbaren Symbolen: 17 weichen "
               "unter 5 %% ab, ⚠️ 16 (48 %%) ab 5 %% - und teils massiv: GNO "
               "-73,6 %%, XLM -66,7 %%, DOT +45,7 %%, QNT -40,5 %%, UNI -37,7 "
               "%%, XRP -37,1 %%, BNB -29,3 %%, LINK -25,2 %%. ⚠️⚠️ LINK "
               "STEHT IN DER WATCHLIST. DIE URSACHE IST SICHTBAR: die "
               "Onchain-Werte sind runde Zahlen (UNI 1.000.000.000, LINK "
               "1.000.000.000, GNO 10.000.000) - das ist die GESAMTAUSGABE, "
               "nicht die UMLAUFENDE Menge. Zwei verschiedene Begriffe unter "
               "einem Namen. ➔ DAS IST DER H-FEHLER IN REINFORM (,die "
               "Anwendung reicht weiter als die Messung'), nur schlimmer: sie "
               "reicht nicht weiter, sie misst etwas anderes. Ein Beitrag, "
               "dessen Kennzahl im Betrieb um 25 bis 74 %% von der gemessenen "
               "abweicht, ist nicht der gemessene Beitrag ✔✔✔ GESCHLOSSEN AM "
               "13.09. DURCH SCHRITT 49 TEIL B (2.419): der Betrieb rechnet "
               "jetzt Binance-Stueckvolumen durch `splycur` - dieselbe "
               "Groesse, mit der gemessen wurde. ⚠️ Der Befund nannte ZWEI "
               "Unterschiede; der ZAEHLER war der groessere (57,1 % gleiches "
               "Fuenftel gegen 86,2 % beim Nenner) und wurde beim ersten "
               "Anlauf uebersehen",
               "gilt",
               "data/onchain_historie.db; agent/marktrang.turnover_werte; "
               "CoinGecko-Markets 12.09."),
    Befundlage("2.410-loesung", "➔ DIE LOESUNG LOEST BEIDE PROBLEME AUF EINMAL - und sie "
               "braucht keine neue Quelle. `turnover = Volumen / (Preis x "
               "Menge)` kuerzt sich zu `Volumen / MARKTKAPITALISIERUNG` - und "
               "beide Groessen liefert CoinGecko `market_chart` HISTORISCH "
               "und KOSTENFREI. Praktisch geprueft am 12.09.: `days=365` gibt "
               "366 Tage mit `prices`, `market_caps` UND `total_volumes`, "
               "ohne Schluessel; `days=max` verlangt einen (HTTP 401). "
               "Gegengerechnet an ADA: Historie 0,039040 gegen Live-Funktion "
               "0,039041 - identisch. ✔ WAS DAS BRINGT: (a) Messung und "
               "Anwendung nutzen DIESELBE Quelle und dieselbe Supply- "
               "Definition - 2.410 ist behoben; (b) die Messbasis waechst von "
               "66 auf 233+ Symbole; (c) kein Sammeln ueber Wochen, sondern "
               "ein Abruf je Symbol (233 Aufrufe, rund acht Minuten bei "
               "30/Minute); (d) die `onchain_historie.db` wird fuer "
               "`turnover` NICHT MEHR GEBRAUCHT. Auch die FUNDING-Historie "
               "ist frei: Binance `/fapi/v1/fundingRate` liefert ohne "
               "Schluessel 500 Saetze = 166 Tage je Abruf, paginierbar. ⚠️⚠️ "
               "ABER R-R11 GILT: bevor auf der neuen Basis gemessen wird, "
               "muss der bestehende Befund ,turnover traegt' auf der ALTEN "
               "Basis REPRODUZIERT werden. Traegt er auf der neuen nicht "
               "mehr, ist das ein Widerruf und kein Messfehler ✖✖✖ WIDERLEGT "
               "AM 13.09. - DIESER VORSCHLAG WAR MEINER UND ER WAR FALSCH. "
               "Die Kuerzung auf `Volumen / Marktkapitalisierung` stimmt "
               "rechnerisch, aber der Weg, sie zu holen, holte die TOP 250 "
               "VON HEUTE - ein Survivorship-Filter (2.416: 4 % eingestellte "
               "Reihen gegen 32 % in der Messmenge) - und er reicht nur 366 "
               "Tage weit (2.416-laenge). ➤ DIE RICHTIGE LOESUNG IST DIE "
               "UMGEKEHRTE: nicht die Messung an die Anwendung angleichen, "
               "sondern die ANWENDUNG an die MESSUNG - "
               "`marktrang.turnover_werte` auf `splycur`",
               "abgeloest",
               "Praktische Pruefung 12.09.; Befund 2.410",
               abgeloest_durch="2.419",
               warum="der Vorschlag war meiner und er war falsch. Die richtige Loesung ist die umgekehrte - nicht die Messung an die Anwendung heben, sondern die ANWENDUNG an die MESSUNG angleichen"),
    Befundlage("2.409", "➔ RECHERCHE INTERN UND EXTERN (Nutzerauftrag "
               "12.09.: *,pruefe welche Einzelindikatoren in Frage kommen "
               "oder ob es eine freie fertige Loesung gibt'*). ⚠️ ERGEBNIS "
               "IN EINEM SATZ: der P-Scan braucht KEINE neue Datenquelle und "
               "KEINE fremde Loesung - die Reichweite lag schon vor "
               "(2.408). INTERN: turnover 233 Symbole (CoinGecko-Markets: "
               "`total_volume` / `current_price` / `circulating_supply`), "
               "funding 851 (Binance-Perpetuals), beide zusammen 137, davon "
               "112 ausserhalb der Watchlist. Weder das eine noch das andere "
               "braucht Historie - nur den heutigen Wert. EXTERN GEPRUEFT, "
               "nur kostenfreie Dienste (stehende Vorgabe): CoinPaprika "
               "(rund 20.000 Aufrufe/Monat OHNE Schluessel, 12.000+ Werte - "
               "koennte `turnover` ueber 233 hinaus verbreitern), DefiLlama "
               "(TVL, Gebuehren, Erloese, Ertraege ueber 6.000+ Protokolle, "
               "frei und ohne Schluessel - die einzige ECHTE Onchain-Quelle "
               "in der Liste), DexScreener (DEX-Paare, 2 Mio. Token, frei). "
               "⛔ Glassnode faellt raus: 800+ Onchain-Kennzahlen, aber "
               "kein freier Zugang - 999 USD im Monat. ⚠️⚠️ FERTIGE "
               "LOESUNGEN: es gibt sie, und sie passen NICHT. "
               "`ml-quant-trading` bringt 213 Faktoren mit, "
               "`OpenTerminalUI` einen Faktor-Baukasten, `Loris Tools` einen "
               "Funding-Arbitrage-Scanner. Alle liefern FAKTOREN OHNE "
               "MESSUNG - und genau das verbietet dieses Projekt: ein "
               "Beitrag muss den Vierfachtest bestehen, bevor er wirkt. 213 "
               "ungeprüfte Faktoren zu uebernehmen waere die groesste "
               "denkbare Verletzung von R-R11", "gilt",
               "Nutzerauftrag 12.09.; Live-Abruf; Websuche 12.09."),
    Befundlage("2.409-kandidaten", "➔ WELCHE EINZELINDIKATOREN IN FRAGE "
               "KOMMEN - geordnet nach dem, was sie KOSTEN. (A) SCHON DA, "
               "GEMESSEN, LIVE: `funding` (851 Symbole) und `turnover` (233) "
               "- beide registriert, beide tragend, beide ohne neuen Abruf. "
               "Sie reichen fuer den P-Scan. (B) SCHON DA, ABER NICHT ALS "
               "BEITRAG: `schnitt` (nur Anzeige, N-59) und `oi_aenderung` "
               "(wirkt als SPERRE im obersten Fuenftel, F-168, nicht als "
               "Beitrag). Beide brauchen keine Datenarbeit, sondern eine "
               "MESSUNG. (C) NEU UND KOSTENFREI ERREICHBAR: DefiLlama-TVL "
               "und -Gebuehren. ⚠️ Das ist die interessanteste Spur, weil es "
               "eine ECHTE Onchain-Groesse ist und nicht wieder aus der "
               "Kursreihe stammt - der Vorwurf der ,illusion of "
               "confirmation' trifft sie nicht. ABER: sie deckt nur "
               "DeFi-Protokolle ab, nicht jeden Coin, und sie muesste den "
               "Vierfachtest bestehen. (D) NUR BREITE, KEIN NEUER GEDANKE: "
               "CoinPaprika wuerde `turnover` von 233 auf mehr Symbole "
               "heben - lohnt erst, wenn 233 zu wenig sind. ➔ FUER DEN "
               "P-SCAN REICHT (A). (C) ist ein Kandidat fuer einen DRITTEN "
               "Beitrag und gehoert in die Kette (Schritt 38), nicht in die "
               "Entdeckung", "offen",
               "Befund 2.409; REGISTER_Kandidaten"),
    Befundlage("2.408", "⚠️⚠️⚠️ DER ENGPASS DES P-SCAN WAR EIN DENKFEHLER "
               "VON MIR - DIE BASIS IST DREIMAL SO BREIT. In 2.385-pscan "
               "steht: *,Funding 302, Terminmarkt 100, Onchain/Turnover nur "
               "66 - beide tragenden Beitraege liegen fuer 42 Werte vor, "
               "davon 35 NICHT in der Watchlist. Der Engpass ist die "
               "Onchain-Basis.'* GEMESSEN AM 12.09. an den LIVE-Quellen: "
               "turnover 233 Symbole, funding 851, BEIDE zusammen 137 - "
               "davon 112 ausserhalb der Watchlist. ⚠️ DER FEHLER WAR EINE "
               "VERWECHSLUNG, und zwar die bekannteste des Projekts: ich "
               "habe die MESSBASIS mit der ANWENDUNGSBASIS verwechselt. Die "
               "66 stammen aus `messdaten.db` - der Historie, die man fuer "
               "den NACHWEIS braucht, dass ein Beitrag traegt. Der LIVE-Rang "
               "kommt aus einem ganz anderen Weg: "
               "`marktrang.turnover_werte()` holt `circulating_supply`, "
               "`total_volume` und `current_price` aus CoinGecko-Markets, "
               "`funding_werte()` die Perpetual-Raten von Binance - beide "
               "brauchen KEINE Historie, nur den heutigen Wert. ➔ FUER DEN "
               "P-SCAN HEISST DAS: die Reichweite ist kein Engpass. 112 "
               "Werte ausserhalb der Watchlist koennen HEUTE bewertet "
               "werden, ohne eine einzige neue Datenquelle", "gilt",
               "agent/marktrang.py; Live-Abruf 12.09.; korrigiert 2.385-pscan"),
    Befundlage("2.408-vorbehalt", "⚠️⚠️ WAS 2.408 NICHT AUFHEBT: der Beitrag ist auf 66 Symbolen "
               "GEMESSEN und wuerde auf 233 ANGEWENDET. Das ist die Form des "
               "H-Fehlers (*,die Anwendung reicht weiter als die Messung'*), "
               "und sie gehoert benannt. ⚠️ ABER SIE IST NICHT NEU UND NICHT "
               "DURCH DEN P-SCAN ENTSTANDEN: die Kette bildet den Rang seit "
               "dem 31.08. ausdruecklich ueber den GANZEN Markt, nicht ueber "
               "die Watchlist - mit der Begruendung, dass ein Rang ueber 43 "
               "Werte eine ANDERE Groesse ist als der gemessene (das war der "
               "Fehler, an dem H gescheitert war). Der P-Scan wuerde also "
               "nichts Neues tun, sondern dieselbe Bewertung auf Symbole "
               "anwenden, die nicht auf der Watchlist stehen. ➔ Die Frage "
               ",traegt der Beitrag auch ausserhalb der 66 gemessenen "
               "Symbole' bleibt offen - sie ist der eigentliche Inhalt von "
               "Stufe 2 des P-Scan (SCHATTEN messen, bevor empfohlen wird) "
               "⚠️⚠️⚠️ BESTAETIGT UND ENDGUELTIG AM 13.09. (2.417): der "
               "Vorbehalt ist mit freien Mitteln NICHT aufloesbar. Neun "
               "Anbieter geprueft, keiner liefert historische Umlaufmenge "
               "ohne Schluessel. Er bleibt stehen und wird genannt, nicht "
               "umgangen",
               "gilt",
               "Befund 2.408; agent/marktrang.funding_werte Docstring"),
    Befundlage("2.407", "✔✔ SCHRITT 44, PUNKTE 2a UND 2b GEBAUT - DIE "
               "VIER-FELDER-MESSUNG IST VOLLSTAENDIG. Der Plan stand seit "
               "dem 29.08. im Konzept und hatte zwei leere Felder (2.394). "
               "(2a) `_schreibe_nein` rechnet jetzt das Potential MIT und "
               "schreibt es in zwei neue Spalten `potential_r` und "
               "`potential_schwelle_r`. ⚠️ ZWEI Spalten, nicht eine: 0,05 R "
               "kann ueber oder unter der Schwelle liegen, je nach Datenlage "
               "des Symbols (Schwelle je Datenlage, 31.08.) - wer nur den "
               "Wert speichert, muss die Schwelle spaeter rekonstruieren, "
               "und sie aendert sich. (2b) Beim ENTSCHEIDER-Verlust stand "
               "bisher nur `return` - 1.251 Zellen in sieben Tagen "
               "verschwanden dort spurlos. Jetzt wird auch dort eine "
               "aufloesbare Zeile geschrieben. ⚠️⚠️ DIE BEIDEN ARME WERDEN "
               "UNTERSCHIEDEN: `grund_art='modell'` setzt "
               "`ist_reines_llm_halten` (Selbst-Halten-Arm seit 31.07.), "
               "`grund_art='bewertung'` setzt `risk_veto` (Veto-Schatten-Arm "
               "seit 28.07., der bis heute LEER lief). Sie schliessen "
               "einander aus - eine Zeile mit beiden Marken wuerde von "
               "beiden Armen aufgeloest und doppelt gezaehlt. ⚠️ DER "
               "TRICHTER BUCHT DEN VERLUST WEITERHIN: eine Schattenzeile ist "
               "keine Handlung. ✔ 14 Pruefungen (Paket Vierfelder), Suite "
               "2.279", "gilt",
               "agent/rollen_lauf.py; agent/signal_abbildung.py; "
               "pruefe_pakete.py Paket Vierfelder"),
    Befundlage("2.407-namensschatten", "⚠️ EIN NAMENSSCHATTEN MIT OFFENEN "
               "AUGEN: `risk_veto` heisst nach dem Risk-Gate der ALTEN "
               "Kette, und die Entscheiderstufe ist kein Risk-Gate. Ich "
               "benutze das Feld trotzdem, und der Grund gehoert "
               "aufgeschrieben, damit ihn spaeter jemand widerlegen kann: "
               "die Alternative waere eine zweite Spalte PLUS ein zweiter "
               "Auswertungszweig in `backward_tracking` gewesen - fuer "
               "genau dieselbe Frage (,war unser Nein richtig'). Der "
               "vorhandene Zweig ist seit dem 28.07. gemessen und hat 418 "
               "Faelle aufgeloest; ihn zu duplizieren waere teurer als der "
               "unscharfe Name. ⚠️ WER DIE ZEILEN SPAETER TRENNEN WILL, "
               "nimmt `quelle_kette='rollen'`: alle 418 alten Veto-Zeilen "
               "stammen aus der alten Kette, alle neuen aus dieser. ➔ Das "
               "ist eine Schuld, keine Loesung - sie steht hier, damit sie "
               "ist eine Schuld, keine Loesung - sie steht hier, damit "
               "sie nicht in einem Jahr als Absicht gelesen wird. "
               "✔ GELOEST AM 12.09. (Nutzerentscheidung C, mit dem "
               "Auftrag, vorher nach einer eleganteren Loesung zu "
               "suchen). ⚠️ DIE SUCHE HAT ZWEI DINGE ERGEBEN. (1) DAS "
               "PROJEKT HAT BEREITS EINE KONVENTION, und sie steht in "
               "`models.Signal.veto_outcome_status`: *,komplett "
               "getrennte Spalten (Option B) statt Wiederverwendung der "
               "outcome_*-Felder, damit eine vergessene Filterstelle nie "
               "hypothetische mit echten Trade-Ergebnissen vermischt* - "
               "zweimal so entschieden (28.07., 31.07.). ⚠️ Sie richtet "
               "sich aber gegen das Vermischen von ERGEBNISSEN; hier ist "
               "die FRAGE dieselbe (,war unser Nein richtig), nur der "
               "GRUND unterscheidet sich. (2) MEIN VORSCHLAG "
               ",quelle_kette als Trenner war SCHLECHTER ALS GEDACHT: er "
               "ist ein PROXY, stimmt heute zufaellig und hoerte auf zu "
               "stimmen, sobald die neue Kette je ein echtes "
               "Risk-Gate-Veto schriebe. ➔ GEBAUT WURDE DAHER EIN "
               "EXPLIZITES FELD `veto_art` (NULL = Altbestand = "
               "risk_gate · risk_gate · entscheider). Beide Arten werden "
               "von DERSELBEN Mechanik aufgeloest - eine zweite Kopie "
               "waere eine zweite Stelle zum Auseinanderlaufen - und "
               "GETRENNT GEMELDET ueber die neue Funktion "
               "`backward_tracking.veto_schatten_bilanz()`. ⚠️⚠️ DIE "
               "ZENTRALE BESCHREIBUNG steht an EINER Stelle "
               "(`models.Signal.veto_art`) samt dem Satz, der zaehlt: "
               "WER `risk_veto` AUSWERTET, MUSS `veto_art` MITFILTERN. "
               "✔ Paket Vetoart, 10 Pruefungen; die Suite hat dabei "
               "erneut gefangen, dass die Spalte im NB-Export fehlte. "
               "⚠️⚠️ NACHTRAG AUF NUTZERFRAGE (,ist diese Thematik "
               "geschlossen und fertig?'): NEIN, sie war es NICHT - und "
               "der Fund ist unangenehm. Ich hatte EINE von SECHS "
               "Auswertungsstellen angefasst. `backward_tracking` fragt "
               "an sechs Stellen `WHERE risk_veto = 1`, und fuenf davon "
               "haetten weiter gemischt - genau die ,vergessene "
               "Filterstelle', vor der der Docstring warnt, den ich "
               "eine Stunde vorher selbst zitiert hatte. ✔ BEHOBEN: "
               "eine ZENTRALE Bedingung `NUR_RISK_GATE` statt fuenf "
               "gleicher Zeichenketten, und jede Stelle ist jetzt "
               "ENTSCHIEDEN - entweder gefiltert, oder ausdruecklich als "
               "`BEIDE-ARTEN-GEWOLLT` markiert (die Aufloesung: die "
               "Frage ist fuer beide dieselbe), oder sie gruppiert "
               "selbst nach Art. ⚠️ UND DAS WIRD MASCHINELL GEPRUEFT: "
               "die Suite liest den Quelltext, sucht JEDE "
               "`risk_veto = 1`-Stelle auf `signals` und verlangt eine "
               "der drei Marken - ein Gedaechtnis reicht hier "
               "nachweislich nicht", "gilt",
               "agent/rollen_lauf.py; agent/krypto/backward_tracking.py"),
    Befundlage("2.407-suite", "✔ DIE SUITE HAT ZWEI EIGENE VERSAEUMNISSE "
               "SOFORT GEFANGEN. Nach dem Anlegen der beiden Spalten meldete "
               "sie (1) *,die neuen Spalten sind auch als Feld deklariert - "
               "SPALTEN_SIGNAL und models.Signal muessen zusammen wachsen'* "
               "und (2) *,keine signals-Spalte ist mehr unexportiert - "
               "offen: potential_r, potential_schwelle_r'*. Beides "
               "nachgezogen. ⚠️ Ohne diese zwei Waechter waeren die Spalten "
               "in der Datenbank gelandet, aber weder im Datenmodell noch im "
               "NB-Export - die Messung haette geschrieben und niemand "
               "haette sie von aussen gesehen. Genau die Klasse Fehler, "
               "wegen der das Projekt diese Waechter hat", "gilt",
               "pruefe_pakete.py; Suite-Lauf 12.09."),
    Befundlage("2.406", "✔✔✔ DIE NUTZERANMERKUNG IST BELEGT - UND SIE "
               "ERKLAERT DEN BEFUND 2.405. Nutzervorgabe 12.09.: *,der "
               "Marktscan sollte zukuenftig ebenfalls aus einer sinnvollen "
               "Bewertung erfolgen - ein erst kuerzlich gestiegenes Asset "
               "ist keine Empfehlung, sondern eher ein Risiko'*. AN DEN "
               "DATEN GEPRUEFT: von 4.088 Kandidaten stammen 3.276 aus "
               "`top_gainers` und 812 aus `trending`. ⚠️ ALLE 114 Faelle mit "
               "gemessenem Ertrag stammen aus `top_gainers` - die "
               "trending-Quelle wurde NIE verfolgt. Die gesamte Messung aus "
               "2.405 betrifft also ausschliesslich ,kuerzlich gestiegen', "
               "und sie ergibt Ø -9,6 %% bei 37,7 %% positiven. ⚠️⚠️ UND ES "
               "GIBT KEINEN EINZIGEN gemessenen Kandidaten, der beim Fund "
               "NICHT gestiegen war: alle liegen ueber +5 %% auf 24 Stunden. "
               "Der Scan waehlt also gar nichts aus - er nimmt, was oben "
               "steht. Aufgeteilt: stark gestiegen (>=20 %%) n=75, Ø -8,5 %%, "
               "41,3 %% positiv; gestiegen (5-20 %%) n=39, Ø -11,7 %%, 30,8 "
               "%% positiv. Beide negativ, kein sauberer Gradient. ➔ DAS IST "
               "REGEL 4 IN REINFORM: ,kuerzlich gestiegen' ist ein FAKT ueber "
               "die Vergangenheit, keine Bewertung dessen, was kommt - und "
               "ein Fakt ist keine Begruendung. Der Scan hat nie bewertet, "
               "er hat sortiert", "gilt",
               "Nutzervorgabe 12.09.; NB-Sicherung; agent/krypto/marktscan.py"),
    Befundlage("2.406-luecke", "⚠️ DIE ZWEITE QUELLE IST NIE GEMESSEN WORDEN. "
               "`trending` liefert 812 der 4.088 Kandidaten (20 %%) - und "
               "KEINE einzige davon hat einen gemessenen Ertrag. Der Grund "
               "liegt vermutlich in der Einstufung: verfolgt wird nur, was "
               "der Scan selbst hoch bewertet, und offenbar landet dort "
               "nichts aus `trending`. ⚠️ Damit steht ueber ein Fuenftel der "
               "Entdeckung KEINE Aussage - weder gut noch schlecht. "
               ",Trending' ist ausserdem etwas anderes als ,Top Gainer': "
               "Aufmerksamkeit statt Kursanstieg, also nicht automatisch "
               "derselbe Regelverstoss. ➔ Vor jedem Urteil ueber die "
               "Entdeckung "
               "gehoert diese Luecke geschlossen (Schritt 39). ✔ GEPRUEFT "
               "AM 12.09., und das Ergebnis dreht die Frage um. (1) DIE "
               "URSACHE IST KEIN DEFEKT, sondern eine dokumentierte "
               "Vereinfachung: `/search/trending` liefert kein `atl_date`, "
               "und ohne Alter faellt ein Kandidat durch den "
               "Alters-Filter - 685 der 812 Zeilen scheitern NUR daran "
               "(,geschaetztes Alter None Tage unter Mindestalter 90'). "
               "Es steht seit dem Bau im Modulkopf von `marktscan.py`. "
               "(2) DIE LUECKE WAERE BILLIG ZU SCHLIESSEN: 91 der 129 "
               "eindeutigen Trending-Coins (71 %%) haben ihr Alter bereits "
               "in einer top_gainers-Zeile DERSELBEN Tabelle - kein "
               "einziger zusaetzlicher API-Aufruf noetig. ⚠️⚠️ (3) ABER "
               "DIE MESSUNG SPRICHT DAGEGEN, und zwar deutlich. Von den "
               "94 auswertbaren Faellen waren 24 Coins AUCH im Trending: "
               "Median -16,29 %% gegen Markt, nur 29,2 %% besser als der "
               "Markt. Die uebrigen 70 (nur top_gainer): Median -3,13 %%, "
               "44,3 %% besser - praktisch auf Zufallsniveau (44,7 %%). "
               "➔ DER GANZE MARKTSCAN LIEGT NUR WEGEN DER "
               "TRENDING-UEBERSCHNEIDUNG UNTER DEM ZUFALL. ,Auch im "
               "Trending' ist kein neutrales, sondern ein NEGATIVES "
               "Merkmal - Aufmerksamkeit PLUS Anstieg ist Ueberhitzung. "
               "Das stuetzt die Nutzeranmerkung (2.406) ein zweites Mal. "
               "⚠️ WAS DAS NICHT IST: eine Aussage ueber REINES Trending "
               "- die 685 Zeilen ohne Ertrag bleiben unbeantwortet, dafuer "
               "fehlen Kursdaten. n=24 ist klein", "gilt",
               "NB-Sicherung 12.09.; messe_marktscan_wert.py; Befund 2.406"),
    Befundlage("2.405", "⚠️⚠️⚠️ DER MARKTSCAN SCHLAEGT DEN ZUFALL NICHT - "
               "er ist sogar schlechter als eine zufaellige Wahl aus der "
               "eigenen Watchlist. Nutzerauftrag 12.09.: *,Marktscan "
               "Pruefung auf Wert ist notwendig'*. GEMESSEN mit "
               "`messe_marktscan_wert.py`: 4.088 Kandidaten seit 09.07., "
               "davon 94 mit gemessenem Ertrag UND auswertbarem Fenster "
               "(der Rest ist ,kein_treffer' und wurde nie verfolgt). "
               "Verglichen wird JE FALL gegen die Median-Bewegung unserer 62 "
               "Krypto-Symbole in GENAU seinem Fenster (im Schnitt 5,8 "
               "Tage) - nicht gegen einen Gesamtzeitraum, sonst misst man "
               "den Kalender. ERGEBNIS: alle 94 -> Median -7,12 %%, nur 40,4 "
               "%% liefen besser als der Markt. watchlist_wuerdig -7,23 %% "
               "(n=55), kaufkandidat -7,00 %% (n=39) - die HOEHERE "
               "Einstufung ist nicht besser. Bei Bitpanda handelbar -3,13 %% "
               "(n=54), am wenigsten schlecht. ⚠️ ZUFALLSKONTROLLE, 200 "
               "Ziehungen, gleiche Fenster, zufaelliges eigenes Symbol: der "
               "Zufall liegt bei 44,7 %% (95. Perzentil 52,1 %%), der "
               "Marktscan bei 40,4 %%. Er liegt also UNTER dem Zufall. ⚠️⚠️ "
               "WAS DAS NICHT IST: ein Befund nach Norm. n=94, gemessen nur "
               "auf den Faellen, die das Tracking verfolgt hat - und wer "
               "dort hineinkommt, entscheidet die Einstufung des Scans "
               "SELBST (Selektion durch die gepruefte Groesse). Die "
               "Bezugsmenge sind Watchlist-Werte, die Funde sind Small "
               "Caps", "gilt",
               "messe_marktscan_wert.py; NB-Sicherung 12.09.; Nutzerauftrag"),
    Befundlage("2.405-folge", "➔ WAS AUS 2.405 FOLGT - und was NICHT. ⚠️ ES "
               "FOLGT NICHT ,Marktscan abschalten': das waere zum zweiten "
               "Mal derselbe Fehler (2.385, meine voreilige Empfehlung vom "
               "12.09. frueh), und es widerspricht KEIN-BEITRAG-FAELLT. Der "
               "Scan ist ausserdem die EINZIGE Entdeckung ausserhalb der "
               "Watchlist - faellt er, faellt die Entdeckung ganz. ✔ ES "
               "FOLGT: (1) die 4.071 unbearbeiteten Kandidaten brauchen "
               "keine Eile - eine Quelle, die den Zufall nicht schlaegt, "
               "erzeugt keinen Rueckstand, sondern eine Warteschlange ohne "
               "Verlust. Damit ist der letzte offene Punkt aus Schritt 40 "
               "entschaerft. (2) Schritt 39 (P-Scan) bekommt einen MASSSTAB: "
               "sein Ersatz muss 44,7 %% schlagen, nicht null. (3) Die "
               "auffaelligste Teilzahl gehoert nachgemessen: ,bei Bitpanda "
               "handelbar' liegt bei -3,13 %% gegen -7,12 %% insgesamt. Wenn "
               "das traegt, ist der Filter ,handelbar' mehr wert als die "
               "ganze Bewertung des Scans - das waere ein billiger Gewinn. "
               "(4) Und die Selektion ist zu heilen: solange nur verfolgt "
               "wird, was der Scan selbst hoch einstuft, misst man seine "
               "misst man seine Konsistenz und nicht seine Guete. ✔ ALLE "
               "VIER PUNKTE BEANTWORTET AM 12.09. (1) und (2) durch die "
               "Trending-Messung (2.406-luecke). ✔ (3) DIE HANDELBARKEIT "
               "TRAEGT, UND ZWAR NICHT ALS GROESSENEFFEKT: handelbar 61 "
               "Faelle, Median -8,2 %%, 42,6 %% positiv gegen 53 nicht "
               "handelbare mit -19,1 %% und 32,1 %%. ⚠️ Handelbare Werte "
               "sind auch die groesseren - deshalb dieselbe Frage "
               "INNERHALB der groesseren Haelfte, mit Marktklammer: 41,9 "
               "%% gegen 25,0 %% besser als der Markt (n=31 gegen 16). Der "
               "Unterschied bleibt, also ist es die HANDELBARKEIT. Zum "
               "Vergleich trennt die EIGENE Bewertung des Scans gar nicht "
               "(watchlist_wuerdig 40,0 %%, kaufkandidat 41,0 %%). ⚠️ ABER "
               "ER MACHT DEN SCAN NUR WENIGER SCHLECHT, NICHT GUT: mit "
               "Filter 44,4 %%, Zufall 44,7 %%. Und was man nicht kaufen "
               "kann, ist ohnehin keine Empfehlung - der Filter ist keine "
               "Entdeckung, sondern eine Selbstverstaendlichkeit, die "
               "gefehlt hat. ✔ (4) DIE SELEKTION IST NICHT HEILBAR und "
               "muss benannt bleiben: von 4.088 Kandidaten bestanden 374 "
               "den Filter A, gemessen wurden 114 - und zwar SCHIEF: 67 "
               "%% der ,kaufkandidat' gegen 23 %% der "
               ",watchlist_wuerdig'. Nachtraeglich messbar sind sie "
               "nicht: von 260 ohne Ertrag haben DREI eine eigene "
               "Kursreihe. ⚠️⚠️ DIE RICHTUNG DER VERZERRUNG IST ABER "
               "BEKANNT - sie bevorzugt die HOEHER eingestuften, und die "
               "sind nicht besser. Die Messung ist damit wenn ueberhaupt "
               "ZU GUENSTIG fuer den Scan, und Befund 2.405 wird dadurch "
               "robuster, nicht schwaecher", "gilt",
               "Befund 2.405; Schritte 39 und 40"),
    Befundlage("2.404", "✔✔ SCHRITT 40 GEBAUT - UND DER WICHTIGSTE FUND WAR "
               "NICHT DAS AUFRAEUMEN, SONDERN EIN STILLER AUSFALL IN SPE. "
               "`agent/warteschlange._rang()` las `MAX(score_gesamt) FROM "
               "hebel_triggers` OHNE Datumsfilter - und diese Tabelle wird "
               "seit dem 12.09. nicht mehr beschrieben (`hebel_screening."
               "aktiv: false`). Die Kette haette also auf unbestimmte Zeit "
               "nach einer EINGEFRORENEN Zahl sortiert, ohne Absturz und "
               "ohne Meldung. ⚠️ Schon heute wirkte es: von 43 Symbolen mit "
               "Score liegen nur 24 innerhalb von 30 Tagen - 19 wurden nach "
               "einem ueber einen Monat alten Rang einsortiert. NEU: "
               "`RANG_MAX_ALTER_TAGE = 30` als benannte Setzung (kein "
               "Befund - sie steht so da, damit sie jemand widerlegen kann) "
               "und `rang_alter_tage()`, damit das Altern ABFRAGBAR ist. "
               "`rollen_lauf` meldet es einmal je Lauf: unter der halben "
               "Grenze still, darueber als Hinweis, jenseits der Grenze als "
               "Warnung im Log. ⚠️ Der Rang FILTERT nichts - faellt er weg, "
               "sortiert die Warteschlange nach Wartezeit weiter. Es geht "
               "also nichts kaputt, es wird nur ehrlich", "gilt",
               "agent/warteschlange.py; agent/rollen_lauf.py; "
               "pruefe_pakete.py Paket Altbestand"),
    Befundlage("2.404-leer", "✔ EINE LEERE LISTE SAGT JETZT, WARUM SIE LEER "
               "IST. Der Hebel-Tab zeigt wartende Screening-Kandidaten; seit "
               "der Stilllegung ist die Liste dauerhaft leer. ⚠️ Eine leere "
               "Liste sagt aber ZWEI voellig verschiedene Dinge: ,es gibt "
               "gerade keinen Kandidaten' (ein Befund) und ,hier schaut "
               "niemand mehr nach' (ein Zustand) - ohne Satz sind sie nicht "
               "zu unterscheiden, und der Nutzer sucht beim naechsten Mal "
               "wieder danach. Genau die Klasse 2.386 und 2.389-log: ein "
               "abgesprochener Zustand, der aussieht wie ein Ausfall. NEU: "
               "`datenfrische.stillgelegt_hinweis()`. ⚠️⚠️ DIE REGEL STEHT "
               "NICHT IN DER TKINTER-ANSICHT, sondern im Modul - eine Regel "
               "in der GUI kann die Suite nicht pruefen, und genau so ist "
               "der letzte Altbestand entstanden. Die Ansicht zeigt nur an. "
               "Sie meldet auch bei UEBRIGEN Zeilen: ,X Kandidaten aus dem "
               "STILLGELEGTEN Screening - Altbestand'", "gilt",
               "agent/datenfrische.py; ui/hebel_view.py"),
    Befundlage("2.404-leser", "📇 WER LIEST DEN ALTBESTAND NOCH - die Antwort "
               "auf die eigene Auflage aus Schritt 40 (*,jede Stilllegung "
               "braucht den Satz: wer liest das noch'*). Fuer "
               "`hebel_triggers` (112.775 Zeilen) an der Quelle "
               "nachgesehen, nicht vermutet. ⚠️ SIE IST NICHT TOT, und das "
               "war die Ueberraschung: (1) BETRIEB - "
               "`agent/warteschlange._rang()` sortiert die Kette danach "
               "(seit heute mit Altersgrenze); (2) BETRIEB - `ui/hebel_view` "
               "zeigt wartende Kandidaten, `hebel_signals` (1.998 Zeilen, "
               "letzte 10.08.) und `hebel_positions` (188, letzte 22.07.); "
               "(3) MESSUNG - `messe_allocator_gegen_zufall.py`, "
               "`messe_halten_ursache.py`; (4) DIAGNOSE - "
               "`extract_notebook_diagnose`, `pruefe_export_standard`. ➔ "
               "LOESCHEN WAERE FALSCH: die Tabelle ist die Messgrundlage von "
               "`messe_allocator_gegen_zufall` - eine geloeschte "
               "Messgrundlage kommt nicht zurueck. Sie bleibt stehen und "
               "wird als das behandelt, was sie ist: Altbestand mit "
               "Ablaufdatum", "gilt",
               "grep ueber alle Module 12.09.; Schritt 40"),
    Befundlage("2.403", "✔✔✔ 48b GEBAUT - UND DAS ERGEBNIS IST DER ERSTE "
               "NACHWEIS IN DIESEM PROJEKT, DASS EIN SPRACHMODELL-URTEIL DEN "
               "ZUFALL SCHLAEGT. `messe_ausstiegsguete.py` misst, was der "
               "Kurs NACH einer Ausstiegsempfehlung tat - gegen die "
               "TAGESKLAMMER (Median aller an diesem Tag bewerteten Werte), "
               "nicht gegen null. Guete = -(bewegung_asset - "
               "bewegung_median): positiv heisst, der Wert fiel staerker als "
               "der Markt, der Verkauf hat also getragen. ⚠️ MIT "
               "ZUFALLSKONTROLLE, 200 Ziehungen, gleiche Tage, zufaellig "
               "gezogenes Symbol - nur die WAHL faellt weg. ERGEBNIS ueber "
               "517 Faelle aus 45 Tagen: VERKAUFEN schlaegt den Zufall "
               "deutlich (H5 59,6 %% gegen 50,0 %%; H10 78,8 %% gegen 50,0 %%, "
               "n=80; H20 81,0 %% gegen 50,0 %%, n=21 - alle ueber dem 95. "
               "Perzentil der Ziehungen). REDUZIEREN schlaegt ihn NICHT (H10 "
               "53,2 %% gegen 49,8 %%). Alle gemailten zusammen: H10 61,1 %% "
               "gegen 49,6 %%. ⚠️ H3 liegt ueberall AM oder UNTER dem Zufall "
               "- das passt zur Unschaerfe des Tagesschlusses und ist kein "
               "Gegenbefund, sondern die Untergrenze der Aufloesung. ⚠️⚠️ "
               "KEIN BEFUND NACH NORM: keine Trennschaerfe, kein p-Wert, "
               "Tagesschluss statt Empfehlungskurs, n bei H20 einstellig bis "
               "niedrig zweistellig. Es ist ein HINWEIS, und er sagt: hier "
               "lohnt die volle Messung", "gilt",
               "messe_ausstiegsguete.py; NB-Sicherung 12.09.; Schritt 48b"),
    Befundlage("2.403-umkehr", "⚠️⚠️ DIE VERKAUFSSEITE IST DIE STELLE, AN DER "
               "DAS SPRACHMODELL TRAEGT - und genau sie war die "
               "unbearbeitete. Nebeneinandergestellt: auf der EINSTIEGSSEITE "
               "verwirft die gerechnete Entscheiderstufe 92 %% dessen, was "
               "Rolle BC empfiehlt, und das Modell selbst verwirft nur 2,7 %% "
               "- sein Beitrag dort ist bis heute unbelegt (2.393-wirkung). "
               "Auf der AUSSTIEGSSEITE entscheidet das Modell praktisch "
               "allein (2.392), und dort schlaegt sein VERKAUFEN-Urteil den "
               "Zufall um 29 Punkte bei H10. ➔ Das dreht die stille Annahme "
               "des Projekts um: nicht ,das Modell muss noch beweisen, dass "
               "es etwas kann', sondern ,es kann etwas an der Stelle, an der "
               "wir es nie gemessen haben'. ⚠️ ZUR VORSICHT: n=80, ein "
               "Zeitraum, ein Markt - und REDUZIEREN, der HAEUFIGERE Fall "
               "(368 gegen 99), traegt NICHT. Wer daraus ,das Modell ist "
               "gut' liest, hat die zweite Zeile nicht gelesen", "gilt",
               "messe_ausstiegsguete.py; Befunde 2.392, 2.393-wirkung"),
    Befundlage("2.403-stumm", "⚠️ UND EIN NEBENBEFUND ZU 48a: DIE STUMMEN "
               "AUSSTIEGE WAREN UEBERWIEGEND FALSCH. Die 105 gestakten Faelle "
               "(die den Nutzer nie erreichten) liegen bei H3 auf 34,7 %% "
               "Anteil ueber null, H5 46,9 %%, H20 40,0 %% - also unter dem "
               "Muenzwurf. Ihr Median ist bei drei von vier Horizonten "
               "NEGATIV. ➔ Das Schweigen hat den Nutzer nichts gekostet, "
               "eher im Gegenteil. ⚠️⚠️ WAS DAS NICHT HEISST: dass 48a "
               "unnoetig war. Eine Empfehlung zu unterdruecken, WEIL sie "
               "vermutlich falsch ist, waere ein deterministischer Override "
               "des Modellurteils - und niemand hat das entschieden; sie "
               "fiel durch eine Luecke, nicht durch eine Regel. Ausserdem: "
               "n=98 auf einer Sondermenge (gestakte Werte sind meist grosse "
               "Coins). Der richtige Umgang ist, sie zu ZEIGEN und zu "
               "MESSEN - genau das ist jetzt der Fall", "gilt",
               "messe_ausstiegsguete.py; Befunde 2.402, 2.403"),
    Befundlage("2.402", "✔✔ 48a GEBAUT: DIE GESTAKTE POSITION BEKOMMT EINEN "
               "HINWEIS STATT SCHWEIGEN. Bis heute endeten zwei sehr "
               "verschiedene Faelle in derselben Stille: ,ohne Bestand' (es "
               "gibt nichts zu verkaufen - Schweigen ist RICHTIG) und "
               ",vollstaendig gestakt' (die Position GIBT es, sie ist nur "
               "nicht frei). Gemessen waren ALLE 25 stummen Faelle der "
               "letzten sieben Tage der zweite Fall. NEU: "
               "`verkaufsrechnung.gesperrt_durch_staking()` - eine DRITTE "
               "Klasse zwischen Auftrag und Schweigen. Sie erzeugt "
               "ausdruecklich KEINEN Verkaufsauftrag (die Menge ist nicht "
               "verfuegbar, daran aendert ein Hinweis nichts) und keine "
               "Verkaufsmenge, sondern nennt Bestand, Wert und Stand. In der "
               "Sammelmail steht sie in einem EIGENEN Abschnitt ,GESPERRT: "
               "DIE MENGE IST GESTAKT', getrennt von der Auftragsliste - "
               "dieselbe Trennung, die die Hebelaenderungen schon haben. ⚠️ "
               "DREI DINGE, DIE DABEI AUFFIELEN und mitbehoben sind: (1) ein "
               "Lauf mit NUR gesperrten Faellen erzeugte gar keine Mail "
               "(`sammel_mail` fiel auf None) - genau die 25 stummen Faelle; "
               "(2) der Betreff hiess dann ,TradingInfoTool: ' - leer, und "
               "ein leerer Betreff wird ungelesen weggeklickt; (3) der "
               "Kopfsatz ,Ausfuehrung manuell ueber die Bitpanda-App' stand "
               "auch dort, wo es nichts auszufuehren gibt. ⚠️⚠️ DIE ZELLE "
               "BLEIBT VERLOREN an Stufe `aktion` mit `art=betriebszustand` "
               "- ein Hinweis ist kein Auftrag, und der Trichter darf nicht "
               "behaupten, hier sei etwas durchgekommen. ✔ GEPRUEFT: Paket "
               ",Gestakt', 15 Pruefungen, darunter der Gegenfall (teilweise "
               "gestakt und ohne Bestand melden sich NICHT) und die "
               "Rueckwaertsvertraeglichkeit (ein Lauf ohne Sperre sieht aus "
               "wie immer). GEGENGEPRUEFT auf dem echten Weg von "
               "`rechne()=None` bis in die Mail. Suite 2.235", "gilt",
               "agent/verkaufsrechnung.py; agent/rollen_lauf.py:1717; "
               "pruefe_pakete.py Paket Gestakt"),
    Befundlage("2.401", "⚠️⚠️⚠️ ES IST GENAU VERKEHRT HERUM: DIE "
               "AUSSTIEGE, DIE HERAUSGEHEN, WERDEN NICHT VERFOLGT - DIE "
               "UNTERDRUECKTEN SCHON. Gezaehlt an der NB-Sicherung 12.09., "
               "beim Aufbereiten der Entscheidung zu Schritt 48: von 412 "
               "GEMAILTEN Ausstiegen stehen 409 auf "
               "`outcome_status='nicht_anwendbar'` und 3 auf NULL - also "
               "KEIN EINZIGER wird ausgewertet. Von den 105 STUMMEN "
               "(`ist_reines_llm_halten=1`, ohne Mail) sind 72 offen, 23 "
               "take_profit, 9 stop_loss - sie werden vollstaendig verfolgt. "
               "⚠️ Der Grund ist kein Versehen, sondern eine fehlende "
               "Kategorie: der Schatten-Arm hat mit `selbst_halten_outcome_*` "
               "eine eigene Maschine (seit 31.07.), der Hauptarm kennt nur "
               "EINSTIEGS-Kategorien - ,einstieg_nie_erreicht' und "
               ",stop_loss_erreicht' sind ueber einen Verkauf keine Aussage, "
               "also faellt alles auf ,nicht_anwendbar'. ➔ Wir messen die "
               "Empfehlungen, die wir NICHT geben, und nicht die, die wir "
               "geben", "gilt",
               "NB-Sicherung 12.09.; Schritt 48"),
    Befundlage("2.401-gestakt", "✔ DER ,DEFEKT' AUS 2.392-stumm IST "
               "PRAEZISIERT - und er ist kleiner und zugleich klarer als "
               "gedacht. An den Trichtergruenden der letzten 7 Tage "
               "nachgesehen, statt vermutet: ALLE 25 Faelle an Stufe "
               "`aktion` lauten *,vollstaendig gestakt, nicht frei "
               "verkaeuflich'* (22 REDUZIEREN, 3 VERKAUFEN) - KEIN einziger "
               "lautet ,ohne Bestand'. ⚠️ Das aendert die Bewertung: bei "
               ",ohne Bestand' ist Schweigen richtig, denn es gibt nichts zu "
               "verkaufen. Bei ,vollstaendig gestakt' GIBT ES die Position - "
               "sie ist nur nicht frei verfuegbar, und der Nutzer koennte "
               "entstaken. Ihm wird also eine Handlungsmoeglichkeit "
               "verschwiegen. ⚠️⚠️ Der Code kennt die Unterscheidung seit "
               "dem 17.08. im WORTLAUT (*,ZWEI SEHR VERSCHIEDENE GRUENDE, "
               "EIN WORT'*), zieht aber keine Konsequenz daraus: beide Wege "
               "enden in `_schreibe_nein` ohne Mail. Aufwand damit klein: "
               "EINE Verzweigung an Zeile 1717", "gilt",
               "gate_durchlaessigkeit 7 Tage; agent/rollen_lauf.py:1717"),
    Befundlage("2.400", "➔ FACHLICHE AUSSAGE ZUM WIDERLEGUNGSPREIS "
               "(Nutzerauftrag 12.09.: *,zum Widerlegungspreis fehlt mir "
               "deine fachliche Aussage'*). ⚠️ DER NUTZER HAT FACHLICH "
               "RECHT, UND MEINE MESSUNG WIDERSPRICHT IHM NICHT - sie legt "
               "nur offen, dass etwas ANDERES kaputt ist. Seine Vorgabe: "
               "*,der Hebel soll ueber echte Gruende dynamisch entstehen "
               "2-5x'* und *,der Widerlegungspreis soll als Information und "
               "Gegenbewertung in der Mail stehen, nicht als doppelte "
               "Pruefung zu Spot und Hebel'*. Sachlich richtig: eine "
               "Modellangabe gehoert nicht in die Geometrie. ⚠️⚠️ ABER DER "
               "GRUND, WARUM SIE HEUTE DORT GEBRAUCHT WIRD, IST NICHT DAS "
               "MODELL - ES IST DER RUECKFALLSTOP. Ohne These rechnet "
               "`_stop_aus_atr` mit `stop_ziel_atr` = 2,5 x ATR und deckelt "
               "bei `stop_max_relativ` = 25 %% des Kurses. Bei Krypto laeuft "
               "das REGELMAESSIG in den Deckel: der Median-Stop ohne These "
               "ist exakt 25,0 %%. Ein Stop von 25 %% macht jeden Hebel "
               "unmoeglich - nicht weil das Modell fehlt, sondern weil 2,5 x "
               "ATR fuer diese Anlageklasse kein Stop ist, sondern ein "
               "Notnagel. ➔ DIE REIHENFOLGE IST DAMIT ZWINGEND: (1) den "
               "Stop auf eine GEMESSENE Grundlage stellen - die Zahlen dafuer "
               "liegen vor (0,75 ATR wird in 57,3 %% der Faelle binnen fuenf "
               "Handelstagen vom blossen Rauschen getroffen, 26.910 Anker; "
               "die Ausstiegsregel ist an 495 aufgeloesten Signalen "
               "gemessen); (2) ERST DANN den Widerlegungspreis aus der "
               "Rechnung nehmen. Wer die Reihenfolge umdreht, verliert den "
               "Hebel vollstaendig (2.397). ⚠️ Und die zweite Bedingung des "
               "Nutzers - *,dazu sollte dieser auch die korrekten "
               "Informationen bewerten'* - ist heute NICHT erfuellt: Rolle "
               "BC kennt die neue Bewertung mit keinem Wort (2.398). Eine "
               "Gegenbewertung, die die Bewertung nicht kennt, ist keine "
               "Gegenbewertung. Das ist der L-Block", "gilt",
               "Nutzervorgabe 12.09.; Befunde 2.397, 2.398; "
               "agent/entscheidungsrechnung.py GRENZEN"),
    Befundlage("2.400-hebel", "⚠️ ZUR NUTZERANNAHME *,der Hebel soll jetzt "
               "sauber ueber echte Gruende dynamisch entstehen 2-5x - das "
               "hast du hoffentlich sauber umgesetzt'*: HALB. Was stimmt: "
               "`r(q)` ist gebaut und ausgerollt - halbes Kelly aus der "
               "gemessenen Quote, geklammert 0,50-1,25 %%, Aggregat-Deckel, "
               "unter 2x wird es Spot. Das ist der ,echte Grund' und er "
               "wirkt. ⚠️ WAS NICHT STIMMT: der Hebel entsteht aus ZWEI "
               "Groessen, nicht aus einer - `hebel = (risiko / STOP) / 500`. "
               "Die Quote ist gemessen, der STOP nicht: er kommt in 81,5 %% "
               "der Faelle aus einer Modellangabe und sonst aus einem "
               "Rueckfall, der in den 25-%%-Deckel laeuft. ➔ Solange das so "
               "ist, entsteht der Hebel NICHT allein aus echten Gruenden - "
               "die halbe Rechnung haengt an einer ungemessenen Zahl. Das "
               "ist keine Kritik an r(q), sondern die zweite Haelfte "
               "derselben Aufgabe", "abgeloest",
               "Nutzeraussage 12.09.; Befunde 2.397, 2.400",
               abgeloest_durch="2.435-optimum, 2.437, 2.438",
               warum="Der Kernsatz war: 'die Quote ist gemessen, der STOP "
                     "nicht'. Seit dem 13.09. abends ist auch der Stop gemessen"
                     " - `stop_ziel_atr` = 2,5 trifft ein inneres Maximum bei 7"
                     " bis 9 % (2.435-optimum, 32.040 gepaarte Anker ueber 534 "
                     "Symbole), und der Deckel von 25 % ist dort geprueft, wo "
                     "er bindet (2.437). Damit steht die Hebelkette auf zwei "
                     "gemessenen Groessen statt auf einer. \u26a0\ufe0f Was von der Frage"
                     " uebrig bleibt, ist SCHAERFER und steht als 2.438: im "
                     "Betrieb kommt der Stop in 81,5 % der Faelle aus dem "
                     "Modell, nicht aus der Regel - dessen Median liegt zwar "
                     "mit 8,0 % genau auf dem Gipfel, aber ob die "
                     "Einzelentscheidung traegt, ist nicht gemessen."),
    Befundlage("2.400-verkauf", "➔ EXPERTENANTWORT ZUR VERKAUFSSEITE "
               "(Nutzerfrage 12.09.: *,ich haette die Verkaufsseite erst als "
               "Paket gesehen wenn die Einstiege stabil sind - was sagt der "
               "Experte?'*). ⚠️ DER NUTZER HAT IN DER SACHE RECHT, ICH "
               "ZIEHE MEINE EMPFEHLUNG ZUR HAELFTE ZURUECK. Wofuer er recht "
               "hat: eine Bewertung fuer den AUSSTIEG ist eine eigene "
               "Messfrage - die zwei tragenden Beitraege sind am EINSTIEG "
               "gemessen (`bewegung_r` ab Einstiegszeitpunkt), und ob "
               "dieselben Groessen etwas ueber den richtigen "
               "AUSSTIEGSzeitpunkt sagen, ist unbelegt. Sie einfach zu "
               "uebertragen waere der H-Fehler (,die Anwendung reicht weiter "
               "als die Messung'). Dazu: an beiden Enden gleichzeitig "
               "umzubauen macht die Wirkung unzuordenbar - genau das Chaos, "
               "das er vermeiden will. ⚠️⚠️ WOFUER ICH TROTZDEM STEHE - UND "
               "ES IST NICHT DER UMBAU: zwei Punkte der Ausstiegsseite sind "
               "KEINE Bauarbeit, sondern ein DEFEKT und eine LEITUNG. (a) "
               "DEFEKT: 105 Ausstiege sind als ,reines LLM-Halten' gebucht "
               "und haben den Nutzer NIE ERREICHT (2.392-stumm), verteilt "
               "bis zum 11.09. Eine Empfehlung, die niemand liest, ist ein "
               "Ausfall, kein offener Planpunkt. (b) LEITUNG: die Guete der "
               "517 Ausstiege ist heute nicht messbar (409 auf "
               "`nicht_anwendbar`, der Rest auf EINSTIEGS-Kategorien). Wer "
               "die Erfassung erst startet, wenn der Umbau beginnt, startet "
               "ihn mit NULL Daten - so wie heute. Bei 15 bis 20 Faellen pro "
               "Tag sind das in vier Wochen rund 500 auswertbare Faelle "
               "gegen null. ➔ EMPFEHLUNG: den UMBAU der Verkaufsseite nach "
               "hinten, wie der Nutzer sagt. Den DEFEKT und die ERFASSUNG "
               "sofort - beides ohne Eingriff in die Bewertung", "gilt",
               "Nutzerfrage 12.09.; Befunde 2.392, 2.392-stumm, 2.394"),
    Befundlage("2.399", "➔ D1 BEANTWORTET: DIE DETERMINISTISCHE EBENE IST "
               "STABIL IM BETRIEB, ABER NICHT SAUBER IN DEN BELEGEN - und "
               "der groesste Riss liegt nicht dort, wo wir zuletzt gearbeitet "
               "haben. ✔ STABIL: Paket B ist ausgerollt und Ende zu Ende "
               "nachgewiesen (17/17 am Notebook), Kapital, Toepfe, "
               "Aggregat-Deckel, r(q) und Hebelfuehrung laufen, die Suite "
               "steht bei 2.212 Pruefungen mit vier bekannten "
               "Desktop-Rotmeldungen aus dem Datenstand, und der Trichter "
               "trennt seit heute die vier Verlustarten. ⚠️ NICHT SAUBER, "
               "mit Nummern: (a) VIER OFFENE BLOCKER - A1 (Band auf binaeren "
               "Daten viermal zu eng, blockiert JEDE Hebelmessung), A6, A8, "
               "A9; (b) die Bewertung steht fuer spot/einstieg auf ZWEI "
               "Beitraegen; (c) die Akkumulation ist ohne Beitrag gesperrt; "
               "(d) vier von fuenf Assetklassen ohne Beitrag - gewollt "
               "(KRYPTO-ZUERST), aber es bleibt eine Luecke. ⚠️⚠️ UND DER "
               "GROESSTE RISS IST DIE VERKAUFSSEITE (2.392): 517 "
               "Empfehlungen seit 14.08., 15 bis 20 pro Tag, und sie "
               "verzweigt an Stufe 9 an der ganzen Bewertung vorbei - kein "
               "Potential, keine Schwelle, kein Deckel, keine messbare "
               "Guete. Das ist KEIN LLM-Thema, sondern ein Loch in der "
               "deterministischen Ebene selbst. ➔ SCHRITT 43 GEHOERT DAMIT "
               "IN DEN D-BLOCK, nicht dahinter", "gilt",
               "Nutzerfrage D1 12.09.; soll_ist.BLOCKER; Befunde 2.392, "
               "2.394; Suite 12.09."),
    Befundlage("2.399-abbildung", "⚠️ WAS FALSCH ABGEBILDET IST - der Stoff "
               "fuer D2 (,straffen und korrekt abbilden'). Gefunden beim "
               "Beantworten von D1, alles nachgeprueft: (1) CLAUDE.md sagt "
               "ueber den Messstandard *,Der Selbsttest der Anlage gegen "
               "bekannte Wahrheit - Fehlalarm- und Fundquote - FEHLT "
               "WEITERHIN'*. Er ist gelaufen: Befund 2.204, 50 Nullwelten "
               "und 120 Welten mit bekanntem Effekt. Die wichtigste Datei "
               "des Projekts behauptet eine Luecke, die geschlossen ist. (2) "
               "`soll_ist` meldet ,NAECHSTER SCHRITT 25 AKKU-MESSPAKET', "
               "waehrend an 44 gearbeitet wird - die Rangfolge bildet die "
               "Arbeit nicht ab (2.395). (3) Zwei Befunde stehen auf "
               "offen und sind erledigt (2.395-erledigt). (4) Die GUI zeigt "
               "die alte Dreiteilung mit leeren Konfidenz-Spalten und "
               "1,1x-Zeilen als ,Hebel' (2.390-gui). ⚠️ Der gemeinsame Nenner: "
               "die Doku ist nicht falsch geschrieben, sie ist an vier "
               "Stellen nicht NACHGEZOGEN worden - und jede davon hat uns "
               "heute Zeit gekostet", "abgeloest",
               "CLAUDE.md; soll_ist.py; Befunde 2.204, 2.390-gui, 2.395",
               abgeloest_durch="2.435-optimum, Schritt 46",
               warum="DREI DER VIER PUNKTE SIND ERLEDIGT, der vierte hat einen "
                     "eigenen Befund. (1) CLAUDE.md fuehrt den Selbsttest nicht"
                     " mehr als fehlend - der Abschnitt nennt jetzt "
                     "Fehlalarmquote (0 von 50), Aufloesung (+0,0293 R) und die"
                     " zwei Einschraenkungen; das Paket `Abbildung` prueft es. "
                     "(2) Die Rangfolge bildet die Arbeit ab: Bloecke seit "
                     "12.09., und seit heute kennt der Plan auch "
                     "ABHAENGIGKEITEN (`wartet_auf`) - er meldete 28 als "
                     "naechsten, obwohl 28 selbst sagt 'erst nach dem Rollout'."
                     " (3) 2.146-luecke und 2.343 stehen auf gilt. (4) BLEIBT "
                     "OFFEN und wird nicht mitgeschleppt: die GUI zeigt weiter "
                     "die alte Dreiteilung - das ist 2.390-gui und Schritt "
                     "41/32, nicht dieser Befund."),
    Befundlage("2.398", "⚠️⚠️⚠️ BESTAETIGT UND SCHAERFER ALS VERMUTET: "
               "DIE LLM-ROLLEN KENNEN DIE NEUE BEWERTUNG NICHT - KEIN "
               "EINZIGES WORT DAVON. Nutzeraussage 12.09.: *,die LLM Stufen "
               "benoetigen ohnehin eine komplette Ueberarbeitung, da diese "
               "OHNE DER NEUEN BEWERTUNG arbeiten'*. GEPRUEFT an den "
               "Prompt-Modulen und am Faktensatz, nicht angenommen. In "
               "`agent/rolle_trader.py` (Rolle BC) und "
               "`agent/rolle_analyst.py` (Rolle A) kommen die Woerter "
               "`potential`, `beitrag`, `funding`, `turnover`, `kelly` und "
               "`r(q)` NICHT VOR; `trefferquote` steht dreimal - "
               "ausschliesslich in KOMMENTAREN, nie im Prompt. Was Rolle BC "
               "wirklich bekommt (`rollen_eingabe.baue_fall` plus drei "
               "Ergaenzungen in `rollen_lauf`): Kursfakten, das Lagebild von "
               "Rolle A, seit 01.09. den Terminmarkt und bei Hedges die "
               "Absicherungslage. ⚠️⚠️ DIE FOLGE IST GROESSER ALS EINE "
               "LUECKE: die gerechnete Entscheiderstufe verwirft 92 %% "
               "dessen, was Rolle BC empfohlen hat - und Rolle BC kennt das "
               "Kriterium nicht, an dem sie gemessen wird. Sie kann es also "
               "weder treffen noch verfehlen; sie raet an einem anderen "
               "Massstab. ⚠️ Das erklaert auch, warum das Modell so wenig "
               "verwirft (56 Zellen = 2,7 %%): es kennt die Schwelle nicht. "
               "➔ Die beiden Straenge sind nicht nur getrennt GEBAUT "
               "(2.393-straenge) - sie REDEN NICHT MITEINANDER", "gilt",
               "Nutzeraussage 12.09.; agent/rolle_trader.py; "
               "agent/rolle_analyst.py; agent/rollen_eingabe.baue_fall"),
    Befundlage("2.397", "⚠️⚠️⚠️ KORREKTUR MEINER EIGENEN AUSSAGE VON "
               "HEUTE FRUEH: DER WIDERLEGUNGSPREIS MACHT DEN STOP ENGER, "
               "NICHT WEITER - UND OHNE IHN GAEBE ES KEINEN HEBEL MEHR. Ich "
               "hatte in 2.395-widerlegung geschrieben, er koenne den Stop "
               ",nur weiten, nie verengen', gestuetzt auf `max(boeden)`. Das "
               "ist innerhalb der drei Boeden richtig und als GESAMTAUSSAGE "
               "FALSCH. Der Grund steht im Code direkt darunter: `if ,These' "
               "not in boeden: boeden[,ATR-Rueckfall'] = _stop_aus_atr(...)` "
               "- der Rueckfall (2,5 x ATR, gedeckelt bei 25 %% des Kurses) "
               "greift NUR, wenn das Modell nichts sagt, und er ist rund "
               "dreimal so weit wie der Rauschboden (0,75 x ATR). Sobald "
               "eine These da ist, faellt er weg. ✔ GEMESSEN, nicht "
               "geschaetzt: `messe_widerlegung.py` faehrt "
               "`entscheidungsrechnung.rechne()` fuer 1.084 echte Signale "
               "der letzten 14 Tage ZWEIMAL - einmal mit, einmal ohne "
               "`umgeworfen_preis_eur`. Ergebnis: 883 (81,5 %%) ENGER, 201 "
               "(18,5 %%) gleich, 0 weiter. Median-Stop ohne 25,0 %% (der "
               "Deckel), mit rund 13 %%. ⚠️⚠️ FOLGE FUER DEN HEBEL: in 822 "
               "von 1.084 Faellen (76 %%) steigt er durch die Modellangabe "
               "UEBER 2x - ohne sie waere es Spot. Gegengerechnet ueber die "
               "ganze r(q)-Spanne bei 17.987 EUR Kapital: bei 25 %% Stop "
               "ergibt 0,50 %% -> 0,72x, 0,75 %% -> 1,08x, 0,97 %% -> 1,40x, "
               "1,25 %% -> 1,80x. KEIN einziger Wert erreicht 2,0x. ➔ Ohne "
               "den Widerlegungspreis erzeugt die Kette bei diesem Kapital "
               "GAR KEINEN Hebel mehr ⚠️ REVIEW 14.09.: das genannte Werkzeug `messe_widerlegung.py` liegt weder im Arbeitsstand noch in der git-Historie - die Messung ist nicht reproduzierbar (R-R11). Der Befund bleibt stehen, eine Neumessung muss ihn zuerst reproduzieren.", "gilt",
               "messe_widerlegung.py 12.09.; agent/entscheidungsrechnung.py "
               "Zeile 349-352, 367-385"),
    Befundlage("2.397-antwort", "✔ DIE DREI NUTZERFRAGEN ZUM "
               "WIDERLEGUNGSPREIS, BEANTWORTET (12.09.). (1) *,Filtert oder "
               "blockiert dieser?'* - NEIN, nicht direkt: er wirft keine "
               "Zelle aus dem Trichter, gemessen 0 von 1.084 Faellen "
               "zusaetzlich blockiert. Er wirkt AUSSCHLIESSLICH ueber den "
               "Stop. ⚠️ Ein Weg dorthin besteht aber: `rechne()` wirft "
               "`RechnungBlockiert`, wenn `betrag = risiko / stop_rel` unter "
               "die Mindestgroesse faellt - ein WEITERER Stop kann also "
               "blockieren. Da die Modellangabe nur verengt, tritt der Fall "
               "hier nicht ein; er waere die Folge ihres WEGFALLS. (2) *,Nur "
               "eine Zusatzinfo (Rechnung) in der eMail, dann eindeutig "
               "kennzeichnen?'* - NEIN, sie ist keine Zusatzinfo. Sie steht "
               "IN der Rechnung und bestimmt in 81,5 %% der Faelle die "
               "Stopweite, und daran haengen Betrag, Hebel, Ziel und "
               "Liquidationsabstand. ⚠️ Die Mail sagt es heute nur beilaeufig "
               "(*,Zone und Stop teils aus einer Modellangabe'*) - die "
               "geforderte eindeutige Kennzeichnung fehlt und gehoert nach "
               "Schritt 41. (3) *,Wenn wir dann nur Spot generieren macht es "
               "keinen Sinn'* - genau das waere die Folge: siehe 2.397, kein "
               "r(q)-Wert erreicht beim Rueckfallstop 2,0x. ➔ EMPFEHLUNG: "
               "NICHT herausnehmen. ⚠️⚠️ ABER DER BEFUND IST UNBEQUEM: der "
               "gesamte Hebel des Systems haengt an einer Zahl, die ein "
               "Sprachmodell nennt und deren Guete nie gemessen wurde. Das "
               "ist keine Entscheidungshilfe mehr, das ist die "
               "Geschaeftsgrundlage - und es gehoert an den Anfang von "
               "Schritt 42", "gilt",
               "Nutzerfragen 12.09.; messe_widerlegung.py; Befund 2.397"),
    Befundlage("2.396", "✔✔ SCHRITT 44 PUNKTE 1, 3 UND 4b GEBAUT - der "
               "Trichter sagt jetzt, WELCHE ART von Nein er zaehlt. (1) VIER "
               "ARTEN in `agent/rollen_gate.py`: `nicht_gefragt` "
               "(Kostenfilter - anlass, auswahl, terminmarkt, wiederholung), "
               "`nicht_moeglich` (Daten oder Antwort unbrauchbar - fakten, "
               "lagebild, urteil, geometrie), `bewertet_nein` (gefragt UND "
               "bewertet - NICHTS_TUN, entscheider) und `betriebszustand` "
               "(Depot oder Schalter). ⚠️ DIE ART HAENGT AN DER STUFE "
               "(`ART_JE_STUFE`), nicht am Aufruf - damit muss keine der "
               "zwanzig Aufrufstellen angefasst werden. Nur die WIRKLICH "
               "gemischte Stufe `aktion` gibt sie an zwei Stellen "
               "ausdruecklich mit. ⚠️⚠️ UND DIE ZEITREIHE BLEIBT HEIL: "
               "`verloren` zaehlt Zahl fuer Zahl weiter wie bisher, `arten` "
               "steht ADDITIV daneben (R-R11). (3) Z1 STEHT JETZT IMMER IM "
               "BERICHT - vorher nur bei einem Befund, und ,keine Zeile' war "
               "von ,gar nicht gelaufen' nicht zu unterscheiden. (4b) LLM-2 "
               "ROLLE G bekommt ihre erste Zeile ueberhaupt: Einwand / kein "
               "Einwand / unklar / nicht gefragt, gezaehlt im HAUPTFADEN "
               "nach dem `join` - nicht im Nebenfaden. ⚠️ ,nicht gefragt' "
               "wird von ,kein Einwand' getrennt, und die Umkehrung (,ja' "
               "heisst EINWAND) laeuft ueber `einwand_liegt_vor()` statt "
               "ueber einen Textvergleich. ✔ GEPRUEFT: 16 neue Pruefungen, "
               "Suite 2.212 mit nur den vier bekannten Desktop-Rotmeldungen "
               "aus Paket Neuaufnahme", "gilt",
               "agent/rollen_gate.py; agent/rollen_lauf.py; "
               "pruefe_pakete.py Paket 12d"),
    Befundlage("2.396-fund", "⚠️ DIE EIGENE PRUEFUNG HAT EINEN FEHLER IN "
               "MEINEM BAU GEFUNDEN - und genau die Sorte, die dieser "
               "Schritt beseitigen soll. Erste Fassung von "
               "`Durchlauf.verloren`: `verloren_je_stufe[stufe] += 1` stand "
               "VOR `art_fuer(...)`. Da `art_fuer` bei unbekannter Art "
               "wirft, hinterliess ein solcher Aufruf einen HALB gebuchten "
               "Verlust - der Zaehler um eins hoeher, `arten` leer. Die "
               "Pruefung ,⚠️⚠️ und `verloren` zaehlt UNVERAENDERT weiter' "
               "hat es sofort gemeldet, weil sie die beiden Zaehler "
               "gegeneinander stellt. ✔ Behoben: die Art wird zuerst "
               "bestimmt. ⚠️ Merksatz: eine Pruefung, die zwei Zaehler "
               "gegeneinander stellt, findet mehr als eine, die jeden "
               "einzeln ansieht", "gilt",
               "pruefe_pakete.py Paket 12d; agent/rollen_gate.verloren"),
    Befundlage("2.396-e2e", "✔ DER E2E-NACHWEIS SCHLAEGT FEHL - UND ES LIEGT "
               "NICHT AN DIESER AENDERUNG. `simuliere_kette.py "
               "--nachweis-paket-b` gegen die NB-Kopie vom 12.09. 07:47 "
               "meldet ,kein Kandidat kam als Hebel durch', Verluste je "
               "Symbol `{fakten: 2, anlass: 1}`. GEGENGEPRUEFT statt "
               "behauptet: derselbe Lauf mit `git stash` auf dem Stand VOR "
               "dem Bau liefert ZEICHENGLEICH dieselben Verluste. Ursache "
               "ist der Datenstand der Kopie (die Kursreihen reichen nicht "
               "bis zum Simulationstag), nicht die Buchhaltung. ⚠️ Der "
               "Nachweis ist damit fuer diese Aenderung NICHT erbracht, "
               "sondern nur nicht widerlegt - er gehoert am Notebook gegen "
               "eine frische Sicherung wiederholt "
               "✔✔✔ NACHGEHOLT AM 13.09. (2.427): gegen die "
               "PRODUKTIONSSICHERUNG vom 12.09. 06:46 laeuft der Nachweis "
               "durch - 17 Faelle, 17 gezeigt, 0 offen. Die Vermutung "
               "dieses Befundes war richtig: es lag am Datenstand der "
               "Kopie, nicht an der Buchhaltung. ⚠️ Und ,am Notebook "
               "wiederholen` war nicht noetig - die taegliche Sicherung im "
               "Austauschordner genuegt (2.422-desktop)",
               "gilt",
               "simuliere_kette.py 12.09.; git stash-Vergleich"),
    Befundlage("2.395", "✔ GEGENPRUEFUNG DES PLANS vor dem Bau "
               "(Nutzerauftrag 12.09.: *,noch davor eine letzte saubere und "
               "umfangreiche Gegenpruefung des aktuellen Plans damit wir "
               "nichts vergessen'*). MASCHINELL ABGEGLICHEN: 39 offene "
               "Befunde gegen alle Planschritte und Vorgaben. 26 werden in "
               "KEINEM Schritt genannt. Davon sind 13 Messkandidaten "
               "(N-Nummern, D3) - die leben im Kandidatenregister und "
               "gehoeren nicht in den Ablaufplan. ⚠️ VIER GEHOEREN "
               "HINEIN und fehlten: (a) 2.380-annahmen - DREI GESETZTE "
               "ANNAHMEN, ausdruecklich ,zur Abstimmung' markiert und nie "
               "abgestimmt (u.a. `hebelfuehrung.KOPPEL_TAGE`=3 Tage, wie "
               "weit ein Signal einer Position zugerechnet wird); (b) "
               "2.389-richtung - die Absicherung verliert Signale an der "
               "Richtungspflicht; (c) 2.359-abruf - keine der drei "
               "Messquellen fuehrt eine `fetched_at`-Spalte, das Alter der "
               "Daten ist damit nicht das Abrufalter; (d) 2.148-sperre / "
               "2.149-prod - `messreihen` hat den Primaerschluessel ohne "
               "`assetklasse`, die Produktionsdatenbank die Spalte gar "
               "nicht. ⚠️⚠️ UND DER GROESSTE MANGEL IST KEINE LUECKE, "
               "SONDERN DIE ORDNUNG: der Plan hat 20 offene Schritte OHNE "
               "Rangfolge. `soll_ist` meldet ,NAECHSTER SCHRITT 25 "
               "AKKU-MESSPAKET', waehrend an 44 gearbeitet wird - die "
               "Nutzervorgaben vom 12.09. (39 bis 44) sind hinten "
               "angehaengt, nicht eingeordnet", "gilt",
               "Nutzerauftrag 12.09.; maschineller Abgleich bestand x "
               "soll_ist"),
    Befundlage("2.395-erledigt", "✔ ZWEI ,OFFENE' BEFUNDE SIND IN "
               "WIRKLICHKEIT ERLEDIGT - an den Daten geprueft, nicht "
               "angenommen. (1) 2.146-luecke behauptet, neun "
               "Watchlist-Werte haetten funding/oi aber KEINE Kursreihe. "
               "Nachgesehen in der NB-Sicherung: ASTER 670 Kerzen, BRETT "
               "878, HYPE 657, KAS 1.765, MON 586, MORPHO 1.322 - alle bis "
               "12.09. Die Luecke ist geschlossen, der Befund war nur nie "
               "nachgezogen. (2) 2.343 fragt, ob `hebel_signals` "
               "(1.998 Zeilen, letzte am 10.08.) ein Ausfall ist. "
               "NEIN: die Tabelle gehoert der ALTEN Hebel-Pipeline. Die "
               "neue Kette schreibt Hebelsignale in `signals` mit "
               "`instrument='spot'` und gesetzter Spalte `hebel` - 1.604 "
               "Zeilen vom 14.08. bis 12.09. Das ist genau die Vorgabe "
               "HEBEL-AUS-SPOT und kein stiller Ausfall. ⚠️ ABER ES "
               "ERKLAERT 2.390-gui: die Oberflaeche liest `hebel` und zeigt "
               "1,1x und 1,2x als ,Hebel', obwohl alles unter 2x seit dem "
               "Rollout SPOT ist", "gilt",
               "NB-Sicherung 12.09.; price_history_ohlc; signals"),
    Befundlage("2.395-widerlegung", "✔✔✔ DER WIDERLEGUNGSPREIS - DIE ZAHLEN "
               "ZUR ENTSCHEIDUNG (Nutzerauftrag 12.09.: *,gib mir die "
               "erforderlichen Infos zur Funktionsweise'*). ⚠️ MEINE "
               "FRUEHERE DARSTELLUNG WAR EINSEITIG: ich schrieb, die "
               "Modellangabe ,bestimmt die Geometrie'. Sie kann sie nur in "
               "EINE Richtung bewegen. WIE ES RECHNET "
               "(`entscheidungsrechnung._boeden` / `_stop_abstand`): drei "
               "Boeden, und `max(boeden, key=boeden.get)` - DER WEITESTE "
               "GEWINNT. Rauschen = max(2,5 %% Kurs, k x ATR) · Struktur = "
               "Marke +- 0,25 ATR · These = Widerlegungspreis. ➔ Liegt die "
               "Modellangabe INNERHALB des Rauschens, gilt der Rauschboden. "
               "Der Docstring sagt es woertlich: *,Damit kann aus dieser "
               "Quelle kein 1,5-%%-Stop werden, auch wenn das Modell einen "
               "nennt.'* ✔ DIE MODELLANGABE KANN DEN STOP NUR WEITEN, NIE "
               "VERENGEN - sie wirkt konservativ. GEMESSEN ueber 14 Tage, "
               "1.084 vergleichbare Faelle: in 252 (23,2 %%) bestimmt die "
               "These den Stop, in 832 (76,8 %%) ist Rauschen oder Struktur "
               "weiter. Rolle BC nennt fast immer einen Preis: 1.275 von "
               "1.280 Zeilen. ⚠️ WAS DARAN TROTZDEM ZU ENTSCHEIDEN IST: ein "
               "weiterer Stop senkt bei festem Risiko den HEBEL (hebel = "
               "risiko/stop) und weitet das ZIEL (CRV 2,0 mechanisch) - er "
               "kann einen Trade unter 2x druecken und damit aus einem "
               "Hebel- einen Spotfall machen. Die Groesse ist also wirksam, "
               "nur nicht in die gefaehrliche Richtung. ⚠️⚠️ UND EIN FUND "
               "NEBENBEI: `umgeworfen_bis` (die Frist) ist in 0 von 1.280 "
               "Zeilen gesetzt. Die Fristpruefung der `ausstiegsrechnung` "
               "(,15 bis 21 %% aller Faelle laufen ohne Entscheidung aus') "
               "laeuft damit vollstaendig leer", "gilt",
               "agent/entscheidungsrechnung.py Zeile 249-264, 355; "
               "NB-Sicherung 12.09."),
    Befundlage("2.394", "⚠️⚠️⚠️ DIE VIER-FELDER-MESSUNG HAT ZWEI LEERE "
               "FELDER - und der fehlende Vergleich ist genau der, den der "
               "Nutzer seit Wochen fordert. DER PLAN STEHT SEIT DEM 29.08. "
               "in `Konzept_Bewertungsstufe_29_08.md`, Abschnitt 5: wer NACH "
               "dem Modellaufruf verwirft, bekommt ein natuerliches "
               "Experiment - LLM kaufen/halten x Bewertung ja/nein. Daraus "
               "lassen sich BEIDE Fragen getrennt beantworten: ,verworfen "
               "gegen durchgelassen bei gleichem LLM-Urteil' misst die "
               "BEWERTUNG, ,LLM-kaufen gegen LLM-halten bei gleicher "
               "Bewertung' misst das MODELL (das offene N-7). ✔ FELD 1 "
               "GEFUELLT: LLM kaufen + Bewertung ja -> Empfehlung geht "
               "hinaus. ✔ FELD 4: LLM haelt + keine Bewertung -> Ruhe. ⚠️ "
               "FELD 2 LEER: LLM kaufen + Bewertung NEIN sind die 1.251 "
               "Entscheider-Verluste in 7 Tagen - dort steht im Code nur "
               "`return`, KEINE Schattenzeile. ⚠️ FELD 3 HALB: das reine "
               "LLM-Halten bekommt zwar eine auflösbare Zeile "
               "(`_schreibe_nein`, `ist_reines_llm_halten=1`, ohne Mail), "
               "aber NIE eine Bewertung - die Zelle erreicht Stufe 12 nicht. "
               "⚠️⚠️ FOLGE FUER MEINE EIGENE ZAHL AUS 2.393-wirkung: die 578 "
               "take_profit gegen 482 stop_loss der gehaltenen Faelle sind "
               "NICHT mit den echten Signalen vergleichbar - die haben "
               "zusaetzlich Stufe 12 passiert, die Schatten nicht. Aepfel "
               "gegen Birnen; der Hinweis bleibt ein Hinweis", "gilt",
               "Konzept_Bewertungsstufe_29_08.md Abschnitt 5; "
               "agent/rollen_lauf.py; NB-Sicherung 12.09."),
    Befundlage("2.394-motor", "✔✔ DER MOTOR FUER DAS LEERE FELD 2 IST "
               "GEBAUT UND GEMESSEN - er bekommt nur kein Futter. "
               "`backward_tracking` fuehrt seit dem 28.07. einen "
               "VETO-SCHATTEN-ZWEIG: `_hat_veto_schatten_these` sucht "
               "`risk_veto=True` UND `action='HALTEN'` UND alle drei Zonen "
               "gesetzt, und `check_signal_veto_shadow_outcome` loest solche "
               "Zeilen auf (Spalten `veto_outcome_*`). Gemessen an der "
               "NB-Sicherung: 418 aufgeloeste Veto-Schatten - ALLE aus der "
               "ALTEN Kette. Von 3.950 Zeilen der Rollen-Kette hat KEINE "
               "EINZIGE `risk_veto=1`. ⚠️ Das ist woertlich dieselbe Lage "
               "wie beim Selbst-Halten-Arm am 14.08.: *,Die Maschine "
               "existiert seit dem 31.07. - sie bekam nur nie Futter aus der "
               "neuen Kette.'* ➔ Der Bau fuer Feld 2 ist damit klein: beim "
               "Entscheider-Verlust eine Schattenzeile schreiben, wie sie "
               "der Halten-Zweig schon schreibt. ⚠️ ZU KLAEREN, NICHT "
               "ANGENOMMEN: ob dafuer `risk_veto` benutzt werden darf - das "
               "Feld heisst nach dem Risk-Gate der alten Kette, und der "
               "Entscheider ist kein Risk-Gate. Ein Namensschatten waere "
               "hier teuer", "gilt",
               "agent/krypto/backward_tracking.py; NB-Sicherung 12.09."),
    Befundlage("2.394-inventur", "✔✔ DIE ERFOLGSMESSUNG IST DA - VIER VON "
               "FUENF ARMEN LAUFEN AUCH IN DER NEUEN KETTE. Nutzerhinweis "
               "12.09.: *,wir hatten Backtracking als Funktion im System und "
               "Erfolgsmessung, das sollte noch helfen bei der Suche'* und "
               "*,und Schattenmessungen'*. ✔ BESTAETIGT und inventarisiert "
               "an der NB-Sicherung. FUENF ARME: (1) HAUPT - `outcome_status` "
               "auf den echten Signalen: 2.983 alt / 3.943 Rollen-Kette; (2) "
               "SELBST-HALTEN-SCHATTEN (seit 31.07.) - ,war die "
               "Zurueckhaltung im Nachhinein richtig?': 769 alt / 1.576 "
               "Rollen-Kette; (3) `vorfilter_schatten` - 915 Zeilen, letzte "
               "am 12.09.; (4) `auswahl_schatten` - 103.998 Zeilen; ⚠️ (5) "
               "VETO-SCHATTEN (seit 28.07.) - 418 alt / **0** Rollen-Kette. "
               "➔ Das System kann die Frage ,war unser Nein richtig' bereits "
               "beantworten, und tut es fuer das Nein DES MODELLS (Arm 2). "
               "Fuer das Nein DER BEWERTUNG (Arm 5, Stufe 12, 1.251 Faelle "
               "in 7 Tagen) ist der Motor gebaut und laeuft leer. ⚠️ Das ist "
               "kein neues Werkzeug, sondern eine fehlende Leitung - genau "
               "die Klasse Fund, die am 14.08. schon einmal 809 Zeilen "
               "gekostet hat", "gilt",
               "Nutzerhinweis 12.09.; NB-Sicherung; "
               "agent/krypto/backward_tracking.py"),
    Befundlage("2.394-risiko","✔ RISIKOPRUEFUNG ZU SCHRITT 44 (Nutzerauftrag "
               "12.09.: *,bevor wir reinstarten fuehre eine Pruefung durch "
               "ob bzw. Risiko dass etwas bricht'*). DIE BUCHHALTUNG IST "
               "UNGEFAEHRLICH: `gate_durchlaessigkeit` speichert alles in "
               "EINER Spalte `daten_json TEXT` - ein zusaetzlicher "
               "Schluessel braucht KEINE Schemamigration. Alle sieben Leser "
               "sind Diagnose oder Pruefung (`rollen_gate`, `bestand`, "
               "`extract_notebook_diagnose`, `pruefe_export_standard`, "
               "`pruefe_export_vollcheck`, `pruefe_pakete`, "
               "`simuliere_rollout_gegen_nb`) - KEIN Betriebscode haengt "
               "daran, kein Handel, keine Mail. Die Suite prueft "
               "STRUKTURELL (,ist entfaltet, nicht als JSON-String', "
               "`isinstance(dict)`), nicht auf Werte - additive Aenderungen "
               "brechen sie nicht. ✔ UND Z1 STEHT SCHON IM PAYLOAD: "
               "`z1_verstoesse`, `z1_zahlen_geprueft`, "
               "`z1_ausgaben_ohne_zahl` werden seit jeher mitgeschrieben - "
               "sie werden nur nirgends ANGEZEIGT. Z1 sichtbar zu machen ist "
               "damit reine Darstellung, null Risiko. Z.ai fehlt im Payload "
               "ganz. ⚠️ DAS RISIKO LIEGT WOANDERS: (a) die ZEITREIHE - wer "
               "NICHTS_TUN aus `verloren.aktion` herausnimmt, macht alte und "
               "neue Laeufe unvergleichbar (R-R11); deshalb wird "
               "TYPISIERT, nicht umgebucht; (b) der WIDERLEGUNGSPREIS "
               "(Punkt 4) aendert die Geometrie JEDES Hebelsignals - das ist "
               "der einzige Punkt mit echtem Bruchrisiko und braucht eine "
               "Vorher-Nachher-Messung an denselben Faellen", "gilt",
               "Nutzerauftrag 12.09.; agent/rollen_gate.py Zeile 372; "
               "pruefe_pakete.py Zeile 3910"),
    Befundlage("2.393", "⚠️⚠️⚠️ DREI KONSTRUKTIONSFEHLER IN DER KETTE - "
               "alle drei vom Nutzer am 12.09. benannt, alle drei "
               "bestaetigt. (A) DER TRICHTER MISCHT DREI ARTEN VON ,NEIN' IN "
               "EINER SPALTE. `durchlauf.verloren()` kennt nur einen "
               "Verlust, gebucht werden aber drei voellig verschiedene "
               "Dinge: WIR HABEN NICHT GEFRAGT (anlass, auswahl, "
               "wiederholung, terminmarkt - Kostenfilter, spart Aufrufe), "
               "WIR KONNTEN NICHT (fakten, geometrie, Vertrag - Datenmangel) "
               "und WIR HABEN GEFRAGT UND DIE ANTWORT WAR NEIN (NICHTS_TUN, "
               "entscheider unter Schwelle - eine BEWERTUNG). ⚠️ Die "
               "Unterscheidung ist im Projekt bekannt und steht woertlich im "
               "Kopf von `agent/rollen_gate.py` (,drei Arten von nicht "
               "jetzt: Kostenfilter, Nutzerentscheidung, Qualitaetsfilter'), "
               "sie ist nur nie abgebildet worden. Daher die ,gemischte "
               "Stufe' 9: 56 Zellen ,NICHTS_TUN' (Bewertung) neben 166 "
               ",Ausstieg steht auf SCHLIESSEN' (Betriebszustand) und 25 "
               ",vollstaendig gestakt' (Bestandslage) - in derselben Spalte. "
               "(B) Z1 UND Z.AI SIND IM TRICHTER UNSICHTBAR, weil sie nichts "
               "verwerfen. Das ist Absicht und richtig - die Folge ist "
               "trotzdem, dass ihre Wirkung NIRGENDS steht. (C) DIE "
               "LLM-STELLEN HABEN KEINE EIGENE STUFE: Rolle A wird an "
               "`lagebild` nur indirekt geprueft, Z1 bucht auf `urteil` "
               "mit, Z.ai auf gar nichts. Wer den Trichter liest, sieht die "
               "Sprachmodelle nicht", "gilt",
               "Nutzereinwand 12.09.; agent/rollen_gate.py; "
               "agent/gegenpruefer_rollen.py; agent/zweite_meinung.py"),
    Befundlage("2.393-wirkung", "⚠️⚠️⚠️ ERSTER HINWEIS: WEDER Z1 NOCH DER "
               "Z.AI-EINWAND TRENNEN DIE AUSGAENGE. ⚠️ KEIN BEFUND NACH "
               "NORM - ohne Tagesklammer, ohne Nullmodell, roh an "
               "`outcome_status` gezaehlt (NB-Sicherung 12.09.). Er steht "
               "hier, weil er die Richtung von Schritt 42 vorgibt, NICHT "
               "als Nachweis. WIE OFT SIE UEBERHAUPT ANSCHLAGEN (7 Tage, "
               "449 Urteile): Z1 in 69 Faellen = 15,4 %% (60x Z-1 "
               "Zahlendeckung, 9x Z-3 Zuspitzung) - in jedem siebenten "
               "Urteil nennt LLM-1 Rolle BC also eine Zahl, die in der "
               "Eingabe nicht steht, und die Empfehlung geht unveraendert "
               "hinaus. Z.ai wurde 163x beantwortet (286x nicht gefragt, "
               "G5): 60 Einwand, 96 kein Einwand, 7 unklar. ⚠️ UND DER "
               "AUSGANG UNTERSCHEIDET SICH NICHT: Z.ai-Einwand JA -> 54 "
               "take_profit / 41 stop_loss = 56,8 %%; Einwand NEIN -> 33 / "
               "23 = 58,9 %%. Z1 angeschlagen -> 36 / 48 = 42,9 %%; Z1 "
               "sauber -> 179 / 237 = 43,0 %%. Beide Male praktisch "
               "identisch. ⚠️ DAZU DAS ,REINE LLM-HALTEN': 578 der "
               "gehaltenen Faelle haetten das Ziel erreicht, 482 den Stop "
               "(516 offen) - eine Sperre, die 55 %% Gewinner mit "
               "aussortiert, ist kein Filter. ⚠️⚠️ WAS DAS NICHT HEISST: "
               "dass die Stellen wegkoennen (KEIN-BEITRAG-FAELLT). Es "
               "heisst, dass ihr Beitrag bis heute unbelegt ist und dass "
               "Schritt 42 genau hier ansetzen muss", "gilt",
               "NB-Sicherung 12.09.; roh, ohne Tagesklammer - Schritt 42"),
    Befundlage("2.393-straenge", "✔ DAS GEFUEHL DES NUTZERS TRAEGT - MIT "
               "EINEM ANDEREN STICHTAG. Er sagte am 12.09.: *,wir bauen "
               "seit Wochen am deterministischen Einstieg je Strategie, das "
               "LLM wurde lange Zeit nicht angegriffen, auch nicht in der "
               "Planung'* - und gab die Auflage mit: *,das ist mein "
               "Gefuehl, pruefen musst du das ueber Doku und Code'*. "
               "GEPRUEFT an der Git-Historie seit 01.08. ⚠️ DIE EINFACHE "
               "FASSUNG WAERE FALSCH: der LLM-Strang wurde sehr wohl "
               "gebaut, nur frueher. 21 der 23 Aenderungen an "
               "`rolle_trader.py` fallen in die zwoelf Tage vom 10. bis "
               "22.08. (Prompts von 34.611 auf 3.183 Zeichen, Betrag "
               "entzogen, Falsifikator pruefbar, Vokabular Spot/Hebel); 18 "
               "der 20 an `zweite_meinung.py` liegen vor dem 18.08. ✔ WAS "
               "STIMMT, IST DER STILLSTAND SEITHER: `rolle_analyst.py` "
               "letzte Aenderung 12.08., `gegenpruefer_rollen.py` (Z1) "
               "18.08., `zweite_meinung.py` inhaltlich 17.08. (der "
               "03.09.-Commit legt nur tote Felder still), `rolle_trader.py` "
               "22.08. - der 11.09.-Commit dort kam aus dem HEBELBAU und "
               "hat das Urteil nicht angefasst. Im selben Zeitraum: 33 "
               "Aenderungen an `entscheidungsrechnung.py`, 12 an "
               "`potential.py`, beide bis 11.09., `marktrang.py` bis 12.09. "
               "✔ UND DIE PLANUNG: der erste LLM-Punkt ueberhaupt ist "
               "Schritt 33, angelegt am 11.09. auf Nutzervorgabe - "
               "nachgelagert (,NACH den eMails') und ohne einen einzigen "
               "Bauschritt. Davor kein LLM-Punkt im Plan. ➔ RICHTIGE "
               "FASSUNG: drei Wochen Stillstand im LLM-Strang bei "
               "durchgehendem Bau im deterministischen - und der Ausstieg "
               "in beiden unbearbeitet (2.392)", "gilt",
               "Git-Historie 01.08.-12.09.; soll_ist.py Schritt 33"),
    Befundlage("2.391", "✔✔ DIE LANDKARTE DER KETTE - was rechnet, was "
               "urteilt, und wo (`Basisinfos/Kette_Landkarte.md`, "
               "Nutzerfrage 12.09.). ZWOELF STUFEN, davon SIEBEN VOR dem "
               "ersten Modellaufruf - jede von ihnen hat eine eigene Stufe, "
               "WEIL sie keinen Aufruf kostet (anlass 16.08., auswahl 23.08., "
               "terminmarkt 02.09.). Das Modell wird an Stufe 8 gefragt "
               "(`urteil`, Rolle BC, einmal je Asset), Rolle A einmal je "
               "Umlauf davor, Z.ai nebenlaeufig danach. ⚠️ KLARSTELLUNG: DER "
               "*ENTSCHEIDER* IST KEINE LLM-ROLLE MEHR - Haendler und "
               "Entscheider wurden am 10.08. in EINEN Aufruf gelegt (162 "
               "Aufrufe taeglich waren nicht tragbar); die gleichnamige STUFE "
               "12 ist gerechnet (`potential.traegt`, Schwelle 0,080 R). "
               "GEMESSEN ueber 7 Tage (3.345 Laeufe, 39.471 Zellen hinein, 202 "
               "heraus): der haerteste Filter ist die GERECHNETE "
               "Entscheiderstufe mit 1.251 von 1.366 (92 %%); davor liegen "
               "anlass 12.005, wiederholung 14.187 und auswahl 10.555 - alle "
               "ohne Modellaufruf", "gilt",
               "Basisinfos/Kette_Landkarte.md · gate_durchlaessigkeit "
               "NB-Sicherung 12.09."),
    Befundlage("2.391-hilfe", "⚠️⚠️ VORGABE GEGEN IST: *,die LLM-Stufen "
               "sollen eine Entscheidungshilfe sein und nichts blockieren oder "
               "aendern'* (Nutzer 12.09.). Gemessen gilt das fuer ZWEI der "
               "drei Stellen: Rolle A verliert an `lagebild` NULL Zellen, Z.ai "
               "hat kein Veto (ihr Einwand steht als Text in der Mail). ⚠️ "
               "ROLLE BC TUT BEIDES: (1) SIE BLOCKIERT - 56 Zellen in 7 Tagen "
               "fielen an der Aktionsstufe mit ,NICHTS_TUN' (von 247 "
               "Verlusten dort sind die uebrigen deterministisch: 166 ,Ausstieg "
               "steht auf SCHLIESSEN', 25 ,vollstaendig gestakt'); das sind "
               "2,7 %% der 2.046 beurteilten Zellen - wenig, aber nicht null. "
               "(2) SIE AENDERT ZAHLEN - ihr WIDERLEGUNGSPREIS geht in die "
               "Stopweite ein (`rechne(umgeworfen_preis_eur=...)`), und am Stop "
               "haengen Betrag, Hebel und Ziel. In der SOL-Mail vom 12.09. "
               "stammt der Stop 80,26 EUR aus dieser Angabe: daraus folgen 8,9 "
               "%% Stopabstand, Hebel 3,9x und 174 EUR Risiko. ➔ ZWEI "
               "ENTSCHEIDUNGEN STEHEN AN: darf das Modell eine Empfehlung "
               "verhindern, und darf seine Preisangabe die Geometrie "
               "bestimmen? "
               "➔ AUSGEZOGEN AM 13.09. IN DEN L-BLOCK (2.427-rollenfrage), "
               "nachdem die Zahlen an der Produktionssicherung "
               "REPRODUZIERT wurden: 56 NICHTS_TUN von 247 Verlusten der "
               "Stufe `aktion`, 1.251 am Entscheider. ✔ Die zweite der "
               "beiden Fragen ist beantwortet - der Widerlegungspreis "
               "bleibt, weil ohne ihn gar kein Hebel mehr entsteht "
               "(2.397); was fehlt, ist die Kennzeichnung in der Mail "
               "(Schritt 41). ⚠️ Die erste - darf das Modell eine "
               "Empfehlung verhindern? - ist eine ROLLENFRAGE und gehoert "
               "zu Schritt 33. Schritt 44 ist ausdruecklich Aufraeumen, "
               "nicht Umbau",
               "gilt",
               "gate_durchlaessigkeit 7 Tage · rollen_lauf · Nutzer 12.09."),
    Befundlage("2.390", "✔✔✔ DIE ERSTE ECHTE HEBELMAIL AUS PAKET B - "
               "SOL, 12.09.2026 07:39, Modell gemini-3.1-flash-lite. DIE "
               "RECHNUNG STIMMT UND IST NACHVOLLZIEHBAR: Trefferquote 34,6 %% "
               "bei CRV 2,0 -> halbes Kelly 0,97 %% -> Risiko 0,97 %% von "
               "17.987 EUR = 175 EUR; Aggregat-Deckel 0 von 540 EUR belegt; "
               "bei 8,9 %% Stop 1.962 EUR Positionswert / 500 EUR Einsatz = "
               "3,9x; am Stop -174 EUR, am Ziel +349 EUR. Nachgerechnet: "
               "Stopabstand (88,14 -> 80,26) = 8,9 %%, Ziel = 2x Stopabstand = "
               "17,9 %%, Liquidation 72,17 EUR ,hinter dem Stop bis etwa Tag "
               "46'. Die Mail nennt die Herleitung in EUR, den Deckel und die "
               "Grenze - genau wie gebaut. ⚠️ Der Trade traegt sich nach "
               "Gebuehren NICHT (noetig 44,4 %% Standard / 53,3 %% Bitpanda "
               "gegen 34,6 %% geschaetzt) - das steht da und sperrt nichts "
               "(Regel 2)", "gilt",
               "Mail SOL 12.09. · GUI Hebel-Reiter"),
    Befundlage("2.390-gui", "⚠️⚠️ GUI UND MAIL LAUFEN AUSEINANDER "
               "(Nutzerbefund 12.09.: *,die GUI bzw. Anzeige und eMail sollten "
               "nicht wesentlich auseinanderlaufen'*). Die Mail hat seit S-4 "
               "die neue Gliederung (AUF EINEN BLICK · WAS DAGEGEN SPRICHT · "
               "sechs Abschnitte · Anhang A/B/C). Der Hebel-Reiter der "
               "Oberflaeche zeigt weiter die ALTE Dreiteilung: ,1. "
               "MATHEMATISCH BERECHNET / 2. LLM-BEWERTUNG (Konfidenz -) / 3. "
               "KONKLUSION (RISIKOFAKTOREN)' mit ,Keine strukturierten "
               "Risikofaktoren verfuegbar'. ⚠️ DREI KONKRETE ABWEICHUNGEN: (1) "
               "die Spalten ,Konfidenz' und ,Trigger' sind leer, weil die neue "
               "Kette sie bewusst nicht liefert (Konfidenz war 77,5 %% "
               "vorhergesagt gegen 33,3 %% eingetreten); (2) die Liste fuehrt "
               "Zeilen mit 1,0x bis 1,2x als ,Hebel' - seit dem Rollout ist "
               "alles unter 2x SPOT, die Zeilen stammen aus Laeufen vor 07:08; "
               "(3) die GUI zeigt Zonen in USD UND EUR, die Mail nur in EUR. "
               "Es sind ZWEI Leser desselben Signals, und sie erzaehlen "
               "Verschiedenes", "abgeloest",
               "GUI Hebel-Reiter 12.09. · Mail SOL 12.09.",
               abgeloest_durch="2.446-gui",
               warum="Am Code nachgeprueft: die alte Dreiteilung steht auch im "
                     "Signale-Reiter, nicht nur im Hebel-Reiter; die Zeilen "
                     "unter 2x sind Altbestand vor dem Rollout und bleiben "
                     "stehen, bis eine neue Zeile je Symbol kommt."),
    Befundlage("2.390-warnungen", "⚠️⚠️ DIE MAIL WARNT MEHR ALS SIE SAGT "
               "(Nutzerbefund 12.09.: *,ich sehe vor lauter Warnungen was "
               "nicht passen koennte nicht auf einen Blick was relevant "
               "ist'*). Gezaehlt an der SOL-Mail: rund 19 Warn- und "
               "Dagegen-Zeilen (Kopf 3, ,Was dagegen spricht' 3, Bewertung 3, "
               "Rechnung 2, Marktvergleich 3, Termine und Projekt 4, Anhang "
               "1). Dem steht KEINE einzige Dafuer-Zeile gegenueber: ,von 4 "
               "pruefbaren Merkmalen 2 dagegen, 2 noch nicht bewertbar'. ⚠️ "
               "Das ist kein Darstellungsfehler, sondern die ehrliche Folge "
               "einer duennen Bewertung (EIN tragender Beitrag) - die Mail "
               "sagt es sogar selbst. Die Frage ist, ob der Leser bei dieser "
               "Dichte noch erkennt, was ENTSCHEIDET. ⚠️ Dazu echte "
               "Doppelungen in derselben Mail: ,steht auf EINEM Beitrag' "
               "zweimal, die Kursmarke 91,15 EUR dreimal (Marken, Widerstand, "
               "Kursmarken), der Umschlag 7,6 %% zweimal (Lage und Belege), "
               "der Stopabstand 8,9 %% dreimal", "abgeloest",
               "Mail SOL 12.09. · Nutzerbefund",
               abgeloest_durch="2.446-redundanz, 2.446-lesbarkeit, 2.446-etiketten",
               warum="An der aktuellen Mail neu gezaehlt (Pruefstand, echte "
                     "Kette). Die Doppelungen stehen weiter, teils in anderer "
                     "Zahl (Stopabstand fuenfmal statt dreimal). Neu ist die "
                     "Ursache fuer 'kein Dafuer': die Dafuer-Etiketten, die es "
                     "gibt, stehen auf einer gepoolten Augustmessung, die das "
                     "Register nicht mehr traegt."),
    Befundlage("2.390-zahlen", "⚠️⚠️⚠️ ZAHLENVERDACHT IN ANHANG B: DIE "
               "GEBUEHREN IGNORIEREN DEN HEBEL. Der Kopf rechnet gehebelt (,am "
               "Stop -174 EUR' bei 3,9x), Anhang B rechnet auf den EINSATZ: "
               ",Standard 0,30 %%: 3,0 %% des Einsatzes (rund 15 EUR) - davon "
               "Handel 0,6 %%, Finanzierung 2,4 %% fuer 16 Tage -> frisst 33 %% "
               "Ihres Risikos'. Die 33 %% ergeben sich gegen 44,50 EUR, also "
               "gegen das UNGEHEBELTE Risiko (8,9 %% von 500 EUR) - nicht "
               "gegen die 174 EUR aus dem Kopf. Und die Finanzierung von 2,4 "
               "%% ist auf 500 EUR gerechnet; bei 3,9x liegt der KREDIT bei "
               "rund 1.462 EUR, 16 Tage x 0,18 %% waeren rund 42 EUR statt 12. "
               "⚠️ WENN DAS ZUTRIFFT, ist die Kostenaussage bei jedem "
               "Hebelgeschaeft zu niedrig - und sie steht in derselben Mail "
               "wie die gehebelte Ergebniszeile. ZU PRUEFEN, nicht "
               "angenommen: an `trefferbilanz`/`kosten` gegen die echten "
               "angenommen: an `trefferbilanz`/`kosten` gegen die echten "
               "Funktionen, mit einem Fall ohne und einem mit Hebel. ✔ "
               "GEPRUEFT UND BEHOBEN AM 12.09.: der Verdacht traf ZUM "
               "TEIL. Die PROZENTE und die R-Aussage waren IMMER richtig "
               "- `kosten_r = kosten_rel / stop_rel`, und dort kuerzt "
               "sich der Hebel heraus, weil Gebuehr und Risiko beide mit "
               "dem Nominal skalieren. FALSCH war allein die EUR-ZAHL: "
               "`kosten_rel` bezieht sich auf das NOMINAL (so der Kopf "
               "von `kosten_in_r`: ,N = E x L, und darauf faellt "
               "derselbe Handelssatz an'), die Mailzeile multiplizierte "
               "es aber mit dem EINSATZ. ⚠️⚠️ DIE MAIL WIDERSPRACH SICH "
               "damit SELBST: oben ,rund 27 EUR', unten ,frisst 60 %% "
               "Ihres Risikos' - und 0,600 R x 174 EUR Risiko sind 105 "
               "EUR. Der Fehler war genau der Faktor Hebel (3,9). ✔ "
               "BEHOBEN: die Zeile nennt jetzt ,des Positionswerts' und "
               "schreibt den Bezug dazu (,rund 105 EUR auf 1.950 EUR "
               "Position, nicht auf 500 EUR Einsatz'). BEI SPOT AENDERT "
               "SICH NICHTS - dort ist Nominal = Einsatz. Gegengeprueft "
               "ueber ZWEI unabhaengige Wege (kosten_rel x Nominal gegen "
               "kosten_r x Risiko), die vor dem Fix auseinanderliefen "
               "und jetzt dieselbe Zahl ergeben: Paket ,Kostenbezug', 9 "
               "Pruefungen", "gilt",
               "Mail SOL 12.09. Anhang B · Schritt 41"),
    Befundlage("2.389", "✔✔ DIE ABNAHME DES ERSTEN UMLAUFS (12.09.2026, "
               "aus dem Logfenster des NB-Exports). Neustart 07:08:06, alle "
               "Schluessel gefunden, Fernsteuerseite oben. In 17 Minuten ZWEI "
               "vollstaendige Umlaeufe ueber ALLE fuenf Ketten - aktien, "
               "hedge, krypto (43 von 43 gedeckt), rohstoffe, themen_etf, "
               "jeweils scharf. 0 Signale, Mails gehen raus (SMTP arbeitet: "
               "Verkaufsvorschlaege und Stop-Nachzieh-Empfehlungen an den "
               "Nutzer). Nur 4 Fehler seit dem Neustart, alle vier derselbe "
               "bekannte (`marktrang`, messdaten.db - siehe 2.389-log). ✔ UND "
               "DER SCHALTER WIRKT WIE GEBAUT: `hebel_screening_job` laeuft "
               "weiter alle 15 Minuten und protokolliert ,Screening "
               "uebersprungen; Positionsabgleich laeuft weiter' - genau die "
               "Trennung aus 2.379-schalter, jetzt im Betrieb belegt", "gilt",
               "NB-Export 12.09. 07:25 · log_auszug"),
    Befundlage("2.389-log", "⚠️⚠️ EIN ABGESPROCHENER ZUSTAND WIRD ALS ERROR "
               "PROTOKOLLIERT - 262 MAL IN 72 STUNDEN. `agent.marktrang` "
               "meldet bei JEDEM Lauf ,Messbasis schnitt nicht lesbar "
               "(data/messdaten.db)' auf ERROR-Ebene; die Datei fehlt am "
               "Notebook planmaessig (166 MB, Rollout 02.09.), und `schnitt` "
               "ist seit dem 31.08. ohnehin nur noch Anzeige. Von 362 "
               "Fehlerzeilen der letzten 72 Stunden sind 262 diese eine. ⚠️ "
               "DAS IST DIESELBE KLASSE WIE 2.386: ein geplanter Zustand, als "
               "Fehler gemeldet - nur kostet er hier keinen Absturz, sondern "
               "die Lesbarkeit des Logs. Wer echte Fehler sucht, sucht sie in "
               "einem Rauschen aus Falschmeldungen. ➔ Einmal je Lauf als "
               "Hinweis statt bei jedem Symbol als ERROR. ✔ BEHOBEN AM SELBEN "
               "TAG (Nutzerentscheidung 12.09.): `marktrang._messbasis_ausfall` "
               "unterscheidet, was vorher in einen Topf fiel - FEHLT die Datei, "
               "ist der Rang unmoeglich und das ist abgesprochen (EINMAL je "
               "Prozess ein Hinweis, danach still); IST sie da und liefert "
               "nichts, bleibt es ein Fehler bei JEDEM Lauf. Die Unterscheidung "
               "steht an EINER Stelle - die Rangschleife entscheidet sie nicht "
               "selbst, sonst laufen zwei Fassungen auseinander. Gegengeprueft "
               "an der ECHTEN Funktion mit Log-Mitschnitt (Paket Luecken, drei "
               "Pruefungen): hinweis / still / fehler. Erwartete Wirkung am "
               "Notebook: 262 der 362 Fehlerzeilen fallen weg", "gilt",
               "NB-Export 12.09. · agent/marktrang._messbasis_ausfall"),
    Befundlage("2.389-richtung", "⚠️ ABSICHERUNG: ZWEI SIGNALE FIELEN AN DER "
               "RICHTUNGSPFLICHT. Im ersten Umlauf nach dem Neustart meldete "
               "hedge/absicherung 2 Fehler: *,DBPK: NACHKAUFEN ohne Richtung - "
               "erlaubt (LONG, SHORT), bekommen None'*, dasselbe fuer 3QSS. "
               "S6c verlangt die Richtung instrumentunabhaengig; das Modell "
               "liefert sie fuer die beiden Absicherungstitel nicht. Im "
               "ZWEITEN Umlauf trat es nicht auf - es haengt am Modell, nicht "
               "an der Struktur. ⚠️ Folge: an solchen Laeufen entsteht fuer "
               "die Absicherung kein Signal, ohne dass es jemandem auffaellt "
               "(2 von 2 Werten) "
               "✔✔ BEANTWORTET AM 13.09. AN DER PRODUKTIONSSICHERUNG "
               "(2.422) - und groesser als gemeldet. Nicht ,zwei Signale "
               "an einem Lauf`: ALLE 12 Absicherungssignale haben "
               "`richtung = NULL`, und `BRAUCHT_RICHTUNG` ist `(KAUFEN, "
               "NACHKAUFEN)` - seit S6c am 22.08. kann die Absicherung "
               "strukturell nur HALTEN sagen. ➔ Was bleibt, ist eine "
               "ENTSCHEIDUNG und keine Messung: braucht die Absicherung "
               "eine Richtung, oder muss der Prompt sie liefern? Das ist "
               "eine Rollenfrage und steht im L-Block (Schritt 33)",
               "gilt",
               "NB-Export 12.09. 07:09 · empfehlung_vertrag.BRAUCHT_RICHTUNG"),
    Befundlage("2.388", "⚠️⚠️ DIE WARTESCHLANGEN DER ALTEN KETTE - 112.775 "
               "ZEILEN, DIE NIEMAND MEHR ANFASST (Nutzerbeobachtung 12.09.: "
               "*,die Urteile bewegen sich nicht mehr'*). An der frischen "
               "NB-Sicherung gezaehlt: `hebel_triggers` 96.000 auf ,neu' OHNE "
               "Kandidatenstatus (14.07. bis 12.09.), 14.047 verfallen, 1.699 "
               "auf ,llm_generiert' - und die JUENGSTE davon vom 10.08. 04:50. "
               "DREI URSACHEN, sauber getrennt: (1) der VERBRAUCHER steht seit "
               "33 Tagen - `llm_generiert` setzt nur die alte Hebel-Pipeline "
               "ueber den Budget-Allocator, und die urteilt nicht mehr; die "
               "1.699 sind ein Endstand, kein klemmender Zaehler. (2) Der "
               "ERZEUGER lief bis 12.09. 03:28 weiter: das alte Screening legt "
               "alle 15 Minuten je Symbol und Richtung eine Zeile an, rund "
               "2.300 am Tag. (3) Der VERFALL kann sie nicht abraeumen - er "
               "fasst ausdruecklich nur `ist_kandidat = 1` an. ✔ SEIT 12.09. "
               "07:08 IST DER ERZEUGER AUS (2.384, im Log belegt). ⚠️ NICHT "
               "LOESCHEN: die Tabelle ist die Messgrundlage von "
               "`messe_allocator_gegen_zufall.py` (ausgewaehlt gegen verfallen) "
               "- und die 96.000 Messzeilen duerfen NICHT auf ,verfallen' "
               "gesetzt werden, das hiesse dort ,Kandidat, nie ausgewaehlt' und "
               "verfaelschte den Vergleich. ➔ Nutzerentscheidung 12.09.: die "
               "1.029 wartenden KANDIDATEN auf ,verfallen' - sie stehen in der "
               "Warteliste der Oberflaeche und werden nie mehr verarbeitet. "
               "DASSELBE MUSTER beim Marktscan: 4.071 Kandidaten auf ,neu', 10 "
               "verworfen, 7 uebernommen - eine Entdeckung, die 4.071 "
               "unbearbeitete Vorschlaege erzeugt, hat kein Erkenntnis-, "
               "sondern ein Auswahlproblem (stuetzt Schritt 39). ⚠️⚠️ UND ES IST "
               "KEIN EINMALIGER ALTBESTAND, SONDERN EIN KREISLAUF: der "
               "Rueckstau wurde schon dreimal von Hand geleert - 696 Zeilen am "
               "19.07., 1.077 am 30.08., 1.029 am 12.09. Genau dazu passt, "
               "dass `llm_generiert` seit Wochen exakt auf 1.699 steht. ✔ "
               "AUSGEFUEHRT 12.09. (Nutzerentscheidung): die 1.029 wartenden "
               "Kandidaten stehen auf ,verfallen' (14.047 -> 15.076), "
               "`llm_generiert` unberuehrt, die 96.000 Messzeilen unberuehrt. "
               "Ruecknahme-Marke: `status_geaendert_am = "
               "2026-09-12T06:22:10.655469+00:00` traegt genau diese 1.029 "
               "Zeilen. ➔ WEIL DER RUECKSTAU WIEDERKEHRT, wird die Prognose "
               "jetzt GEPRUEFT statt geglaubt: der Export fuehrt den "
               "Altbestand mit Zeitstempel, und der Vollcheck fragt (E8), ob "
               "die Kette NACH dem letzten Trigger lief - dann ist der alte "
               "Erzeuger nachweislich still. In beide Richtungen an einer "
               "Testdatei geprueft", "gilt",
               "NB-Sicherung 12.09. · hebel_triggers · Nutzer 12.09."),
    Befundlage("2.387", "✔✔ DER ROLLOUT AM NOTEBOOK - Paket B laeuft dort "
               "(12.09.2026). Pull auf 9f9408c (142 Commits, fast-forward, "
               "keine Konflikte, `config.yaml` lokal unveraendert). "
               "`ausrollen_paket_b.py`: lesend 2 Punkte offen (Kapital ,alt', "
               "Quelle kapital) - genau die vorhergesagten; mit "
               "`--nachrechnen` 10 Tage geschrieben, danach 13 Punkte, 0 "
               "offen. ⚠️⚠️ DAS KAPITAL WAR NICHT NUR ALT, SONDERN FALSCH: "
               "9.942 -> 17.978 EUR (+81 %%), und das ist KEINE "
               "Marktbewegung - die zehn nachgerechneten Tage liegen zwischen "
               "17.612 und 18.742 EUR. Die alte Zeile vom 01.09. fuehrte 32 "
               "Symbole und 6 OHNE KURS, die neuen 38 und 0: es fehlten sechs "
               "Positionen komplett (die gestakten, P-3). Der Aggregat-Deckel "
               "steht damit bei 539 statt 298 EUR - haetten wir nicht "
               "nachgerechnet, waere er auf der halben Groesse gelaufen. "
               "Schalterstand am Geraet bestaetigt: Hebel aus der Quote AN, "
               "altes Hebel-Screening AUS, Marktscan AN. Spalten `instrument`, "
               "`verlust_am_stop_eur`, `strategie` vorhanden und LESBAR. ✔ DIE "
               "KETTE IST DURCH: Suite 2.179 Pruefungen ALLE BESTANDEN, 5 "
               "Bloecke uebersprungen, Exit 0; `--nachweis-paket-b` 17 von 17 "
               "Faellen, davon D2 der Kern: der Deckel WANDELT statt zu "
               "sperren (frei 30 von 539 EUR -> Spot mit 800 EUR, Cooldown 12 "
               "statt 3,5 h), und die Mail begruendet es im Klartext; "
               "`finde_freie_namen` 0. ⚠️ EINE ABHAENGIGKEIT, die der "
               "Notebook-Lauf selbst benannt hat: der Nachweis rechnet gegen "
               "539 EUR - also gegen die Kapitalbasis, die dieser Rollout "
               "ERST HERGESTELLT hat. Mit dem alten Wert waeren es 298 EUR "
               "gewesen und der Deckel haette frueher auf Spot "
               "zurueckgestuft", "gilt",
               "ausrollen_paket_b.py am Notebook 12.09."),
    Befundlage("2.387-rot", "⚠️ DIE ZWEI ROTEN DES ERSTEN NOTEBOOK-LAUFS - "
               "keine davon ein Fehler des Betriebscodes. (1) Paket Register: "
               "zwei Dokumente ohne Standkopf, die es NUR am Notebook gibt "
               "(`LLM_BUDGET_ANALYSE_2026-07-15.md`, "
               "`LLM_BUDGET_SESSION_2026-07-16.md`, beide unversioniert) - "
               "ein Geraeteartefakt, Entscheidung des Nutzers (loeschen oder "
               "Kopf ergaenzen). (2) Paket 15: ,die Mail traegt die Kennung "
               "des geschriebenen Signals'. ⚠️ NICHT DER CODE - "
               "`rollen_lauf` setzt sie direkt nach dem Schreiben. Der "
               "aufgezeichnete Client antwortet KAUFEN, die Kette machte "
               "daraus einen AUSSTIEG (Ausstiegsempfehlung SCHLIESSEN), es "
               "entstand also GAR KEINE Einstiegsmail - 4x NICHTS_TUN, 1x "
               "KAUFEN mit Ausstieg. Die Pruefung verlangte eine Kennung an "
               "einer Mail, die es in diesem Lauf nicht gab. ➔ Sie haengt "
               "jetzt an ihrer Voraussetzung: gibt es eine Asset-Mail, MUSS "
               "sie die Kennung tragen; gibt es keine, wird das BENANNT "
               "(uebersprungen). Ein gruener Haken ohne Gegenstand waere "
               "schlimmer als ein rotes Kreuz. ✔ BEIDE ERLEDIGT: die zwei "
               "Juli-Dokumente haben ueber `markiere_dokumente.py` ihren "
               "Standkopf mit dem URSPRUENGLICHEN Datum bekommen (2 gesetzt, "
               "48 unveraendert; unversioniert, also nur am Geraet) - danach "
               "2.179 Pruefungen ALLE BESTANDEN. ⚠️ Und das Werkzeug nennt "
               "die Einbahnstrasse selbst: das Aenderungsdatum steht jetzt auf "
               "heute, die Einstufung kommt ab sofort NUR noch aus dem Kopf", "gilt",
               "Notebook-Lauf 12.09. · pruefe_pakete Paket 15"),
    Befundlage("2.387-job", "⚠️ OFFEN NACH DEM ROLLOUT: DER "
               "PORTFOLIOWERT-JOB HAT ZEHN TAGE NICHT GESCHRIEBEN (01.09. bis "
               "11.09., am Notebook beim Rollout gesehen). Er ist eingeplant "
               "(`id=portfolio_wert`, mit Nachholfenster), und seine "
               "Abdeckungsschranke kann es nicht gewesen sein: 26 von 32 "
               "Werten mit Kurs sind 81 %% gegen die geforderten 80 %%. Das "
               "Nachrechnen hat die LUECKE geschlossen, nicht die URSACHE. ➔ "
               "Nach dem Neustart an der juengsten Zeile pruefen: schreibt er "
               "wieder taeglich, war es der abgeraeumte Prozess vom 02.09.; "
               "schreibt er nicht, ist es der Job selbst. ⚠️ Dazu ein zweiter "
               "Punkt: die aelteren Luecken der Zeitreihe (03.08.->20.08., "
               "20.08.->26.08., 26.08.->01.09.) werden NICHT nachgerechnet - "
               "der Verlauf hat dort weiter Sprungstellen, der Index bleibt "
               "stetig", "offen",
               "Notebook-Rollout 12.09. · scheduler/background.portfolio_wert_job"),
    Befundlage('2.387-fortschreibung',
               "⚠️ OFFEN NACH DEM ROLLOUT: SECHS BOERSENTITEL WERDEN DAUERND FORTGESCHRIEBEN. In jeder nachgerechneten Zeile stehen dieselben Symbole (ISOC, OD7C, OD7H, OD7L, OD7N, CEBS, DBPK, EXH3, VVMX) mit 3 bis 4 Tagen Fortschreibung - genau die, die yfinance am 02.09. 31-mal als ,possibly delisted' meldete und die damals als FREMDE Quelle abgehakt wurden. ✔ Die Fortschreibung ist gedeckelt (`MAX_FORTSCHREIBEN_TAGE = 4`), danach zaehlt der Wert als ohne Kurs und drueckt die Abdeckung - sie kann also nicht unbemerkt weiterlaufen. ⚠️ Aber: eine Meldung aus fremder Quelle hat Folgen in der eigenen Rechnung, denn aus dem Kapital kommt der Hebel-Deckel. Zu pruefen sind die TICKER (VVMX.DE, DBPK.DE, X136.MU, EXH3.DE, CEBS.DE, ISOC.SG), nicht die Fortschreibung ➤ GEPRUEFT 15.09. (NB-Log 12. bis 15.09., Sicherung 14.09. 22:40, yfinance live). (1) DIE TICKER STIMMEN: alle sechs liefern Tageskerzen, um 05:20 UTC am 15.09. auch den Montag (X136.MU notiert ohne Umsatz, aber mit Kurs); OD7C/H/L/N und 3QSS haben bei yfinance keine Historie und werden aus der Referenz rekonstruiert (bekannt, `rekonstruktion.py`). ,possibly delisted' stand in drei Tagen Log nur fuer ^VIX (2.454-vix). (2) DIE LANGEN FORTSCHREIBUNGEN (3 bis 4 Tage an Handelstagen, Tageswert 11.09.: CEBS, EXH3, VVMX 3 T, ISOC und OD7* 4 T) kamen vom alten Nachladewaechter (erst nach mehr als 5 Kalendertagen) - behoben mit 2.453-kurs-gebaut; seit dem Neustart 15.09. 00:34 stehen am Sonntag alle 12 Titel auf dem Freitag (2 T) - richtig. (3) ⚠️ ES BLEIBT EIN SYSTEMATISCHER TAG RUECKSTAND AN WERKTAGEN, und die Ursache ist unsere Regel, nicht Yahoo: `letzter_abgeschlossener_handelstag` zaehlt den heutigen Tag erst ab Mitternacht UTC als abgeschlossen. Der Tagesjob lief am Notebook um 22:32 UTC (24 h nach App-Start) - am Montag galt der Freitag als letzter abgeschlossener Tag, eine Reihe mit Freitagskurs als aktuell, der Montagskurs wurde nicht geholt. Der Tageswert fuer Montag entsteht aber um 04:30 UTC am Dienstag. Folge: an jedem Werktag rechnet der Portfoliowert Boersentitel mit dem Kurs des Vortags, solange der Tagesjob nicht zufaellig zwischen 00:00 und 04:30 UTC laeuft. Die Docstrings von `portfolio_wert_job` und Backward-Tracking setzen einen ,naechtlichen Kurs-Refresh' voraus, den es seit der Umstellung auf 24 h ab App-Start nicht gibt. 📏 WIRKUNG: die 12 Boersentitel sind 25 Prozent des Kapitals (rund 4.500 EUR von 17.696); CEBS fiel Freitag -> Montag 3,9, VVMX 3,3 Prozent - rund 30 EUR, 0,2 Prozent des Kapitals; auf r x Kapital (hoechstens 1,25 Prozent) unter 1 EUR. Der Index (Z-3) korrigiert sich am Folgetag selbst, weil beide Kurse neu gelesen werden; falsch bleibt `wert_eur` der Tageszeile. KLEIN, ABER JEDEN WERKTAG und an der Bezugsgroesse des Hebels. Loesungsweg vorgelegt",
               'abgeloest',
               'Notebook-Lauf 12.09. · portfolio_historie.MAX_FORTSCHREIBEN_TAGE',
               '2.455-kapitalkurse-gebaut',
               'Kursreihen-Job 05:30, Eingabepruefung und Schlusskurs-Rueckfall (15.09.)',
               ''),
    Befundlage("2.386", "⚠️⚠️⚠️ AM NOTEBOOK STARB DIE GANZE SUITE - 0 von "
               "2.193 Pruefungen, ohne eine einzige ausgegebene Zeile "
               "(Rollout 12.09., gefunden im ersten Lauf nach dem Pull). "
               "URSACHE: drei ZUSTANDSpruefungen oeffneten `data/messdaten.db` "
               "ungeschuetzt - die Datei liegt am Notebook BEWUSST nicht (166 "
               "MB, so entschieden beim Rollout 02.09.). `sqlite3."
               "OperationalError` in `paket_assetklassen_trennung`, und weil "
               "die Pakete VOR der Ausgabe laufen, fiel damit alles aus. Am "
               "Desktop faellt es nie auf, weil die Datei hier liegt - "
               "dieselbe Klasse wie `paket_b1` (24.08.), der KeyError vom "
               "02.09. und die `.index()`-Pruefung vom 03.09.: eine Pruefung, "
               "die stirbt, prueft nichts mehr. ➔ DRITTE KATEGORIE statt "
               "Absturz ODER falschem Rot: `_datei_fehlt()` bucht den Block "
               "als UEBERSPRUNGEN, die Schlussausgabe nennt ihn samt Grund. "
               "Gegengeprueft: am Desktop unveraendert (Assetklassen 13, "
               "Kalibrierung 51, Neuaufnahme 6); mit simuliert fehlender Datei "
               "kein Absturz, 7 Pruefungen weniger, 3 Bloecke uebersprungen. "
               "⚠️⚠️ ES WAREN FUENF STELLEN, NICHT DREI - und die vierte fand "
               "erst der zweite Notebook-Lauf: `paket_messstandard` ruft "
               "`messe_eigenschaft_beitrag.lade()`, und ERST DIESE Funktion "
               "oeffnet die Datei (Konstante `DB` im Modul). Gesucht worden war "
               "nach `connect(`-Aufrufen IM Pruefcode - eine Suche beweist "
               "Abwesenheit nur dort, wo sie gesucht hat. Die fuenfte: "
               "`pruefe_neuaufnahme.pruefe()` liest BEIDE Datenbanken und riss "
               "das ganze Paket mit (0 statt 6 Pruefungen). ➔ DREI EBENEN "
               "statt einer: (a) gezielte Wachen an den vier Bloecken, (b) das "
               "Paket Neuaufnahme wird als GANZES uebersprungen - dort ist die "
               "Frage ohne Messdatenbank nicht beantwortbar, (c) ein FANGNETZ "
               "um jeden Paketaufruf in `main()`: eine planmaessig fehlende "
               "Datei wird uebersprungen, JEDER andere Abbruch ist rot und mit "
               "Traceback - ein Paket darf die Suite nie wieder mitnehmen. "
               "ERWARTUNG AM NOTEBOOK: 2.180 Pruefungen, 4 Bloecke "
               "uebersprungen, 0 Rote. ⚠️⚠️ NULL ROTE HEISST DORT NICHT ,alles "
               "in Ordnung': alle vier bekannten Roten liegen im Paket "
               "Neuaufnahme und sind am Notebook NICHT BEANTWORTBAR. Sie "
               "gelten weiter - beantwortet werden sie am Desktop. ⚠️ Und auch "
               "dort nur auf dessen Bestandsstand (19.08.): wer ,jede "
               "GEHALTENE Position hat eine Messreihe' wirklich pruefen will, "
               "braucht Bestand UND Messreihen am selben Ort - das hat heute "
               "kein Geraet", "gilt",
               "pruefe_pakete._datei_fehlt · Fangnetz in main() · "
               "Notebook-Laeufe 12.09."),
    Befundlage("2.384", "✔✔✔ SCHARF GESCHALTET MIT DEM ROLLOUT VON PAKET B "
               "(Nutzerentscheidungen 12.09.2026). (1) `rollen_kette."
               "hebel_aus_quote.aktiv: true` - ab jetzt entsteht der Hebel aus "
               "der Wahrscheinlichkeit r(q) statt aus der Stopgeometrie; die "
               "Vorgabe im CODE bleibt AUS, eingeschaltet wird allein in der "
               "config.yaml. Voraussetzungen lagen vor: Verteilung simuliert "
               "(2.378), E2E gezeigt (2.382), Rollout-Skript geprueft (2.383). "
               "(2) `hebel_screening.aktiv: false` - das ALTE Hebel-Screening "
               "verbraucht keine Rechenzeit mehr; Positionsabgleich und "
               "Hebelfuehrung laufen weiter (2.379-schalter, im Paket "
               "Hebelfuehrung gegen den Quelltext geprueft). (3) Der alte "
               "MARKTSCAN bleibt AN - siehe 2.385. Die Paketpruefung verlangt "
               "jetzt ausdruecklich `aktiv is True` in der config und `False` "
               "in der Code-Vorgabe: wer den Schalter zuruecknimmt, sieht es "
               "in der Suite", "gilt",
               "Basisinfos/config.yaml · Nutzerentscheidung 12.09."),
    Befundlage("2.385", "⚠️⚠️ DER ALTE MARKTSCAN HAT KEINEN ERSATZ - meine "
               "Empfehlung ,ausschalten' war voreilig und ist zurueckgezogen "
               "(Nutzerfrage 12.09.: *,warum sollen wir den Marktscan "
               "ausschalten bzw. was ist der Ersatz dafuer?'*). AN DER QUELLE "
               "GELESEN: `marktscan_job` (04:00/16:00) ruft "
               "`agent/krypto/marktscan.run_scan` - Entdeckung neuer Assets "
               "ueber CoinGecko Trending/Top-Gainers, Stufen A-D "
               "deterministisch, SEIT 14.07. OHNE Modellaufrufe; er schreibt "
               "`marktscan_candidates`, meldet Kaufkandidaten und ,Watchlist "
               "heiss' per Mail, entscheidet aber nichts (Aufnahme ueber die "
               "GUI). Er kostet CoinGecko-Abrufe, keine LLM-Kontingente. DIE "
               "ROLLEN-KETTE BEWERTET NUR DIE WATCHLIST (44 Kryptowerte) - "
               "ausserhalb sucht NIEMAND sonst. Ihn abzuschalten hiesse: keine "
               "neuen Werte mehr, ohne Ersatz. ⚠️ Zwei Einwaende bleiben: "
               "seine Schwellen (Score 70 / 50) sind VORLAEUFIG und nie gegen "
               "eigene Daten gemessen, und er meldet auf einer anderen "
               "Grundlage als die Kette", "gilt",
               "agent/krypto/marktscan.py · scheduler/background.marktscan_job "
               "· config.yaml marktscan"),
    Befundlage("2.385-pscan", "➔ VORSCHLAG P-SCAN: DIE ENTDECKUNG AUF DAS "
               "POTENTIAL STELLEN (Nutzerauftrag 12.09.: *,ueberlege dir als "
               "Experte eine neue Loesung, um Assets mit Potential zu "
               "empfehlen'*). Die Idee: dieselbe gemessene Bewertung wie in "
               "der Kette (`potential.rechne` aus den registrierten "
               "Beitraegen) NICHT nur auf die Watchlist anwenden, sondern auf "
               "alle Werte, fuer die die Messbasis reicht - der Rang ist ein "
               "Querschnittsvergleich und dafuer ausdruecklich zugelassen "
               "(Regel 3). ⚠️ DIE REICHWEITE IST HEUTE BEGRENZT, gemessen am "
               "Desktop 12.09.: Funding 302 Symbole, Terminmarkt 100, "
               "Onchain/Turnover nur 66 - BEIDE tragenden Beitraege liegen fuer "
               "42 Werte vor, davon 35 NICHT in der Watchlist (ADA, DOT, DOGE, "
               "AAVE, BCH ...). Der Engpass ist die Onchain-Basis, nicht die "
               "Idee. Vorgehen in drei Stufen: (1) SCHATTEN - den Rang je Tag "
               "mitschreiben, ohne Mail; (2) MESSEN - traegt ein hoher Rang "
               "ausserhalb der Watchlist mehr Potential (`bewegung_r`, NICHT "
               "Zielerreichung) als die heutige Watchlist? Ohne diesen Nachweis "
               "keine Empfehlung (P-1); (3) erst dann eine woechentliche "
               "AUFNAHME-Liste mit Begruendung, gefiltert auf bei Bitpanda "
               "handelbare Werte (`config.kandidat_ist_handelbar`). ⚠️ Regel 1: "
               "die Liste schlaegt BEOBACHTUNG vor, kein Handeln - das Signal "
               "entsteht weiter in der Kette. Solange das nicht gemessen ist, "
               "bleibt der alte Marktscan an", "offen",
               "Schritt 39 · 2.385 · Messbasis-Zaehlung 12.09."),
    Befundlage("2.383", "✔✔ SCHRITT 24 VORBEREITET - `ausrollen_paket_b.py`, "
               "die Vollstaendigkeitspruefung fuer das Notebook (stehende Regel: "
               "Gesamtpaket statt Einzelschritte). Prueft Code, config, Schema "
               "mit LESEPROBE, Kapital, Datenfrische, Hebel-Schalter und Deckel; "
               "`--nachrechnen` schreibt die fehlenden Tage in "
               "`portfolio_wert_historie` (2.376-rollout). Getestet gegen eine "
               "Kopie der NB-Sicherung 11.09.: ohne Nachrechnen 2 Punkte offen "
               "(Kapital ,alt' 9.942 EUR, Quelle kapital ,abruf') - richtig "
               "gemeldet; mit Nachrechnen 9 Tage (02.09.-10.09.), Abdeckung je "
               "1,0, Kapital FRISCH 18.213 EUR - derselbe Wert wie in H-1 ueber "
               "einen anderen Weg. Der INDEX springt nicht (95,58 -> 95,43), nur "
               "der Wert einmal (das Gestakte, 2.375-index). Neue Spalte "
               "`verlust_am_stop_eur` angelegt und gelesen; Deckel 546 EUR. "
               "SCHUTZSPERRE geprueft (Betriebspfad auf eine Attrappe gelenkt): "
               "am Desktop ohne `--db` Abbruch, keine Datei angelegt; als "
               "Notebook greift sie nicht. Am NB 24 von 44 Kryptowerten mit "
               "Hebel-Schalter. Suite 2193 Pruefungen, 4 bekannte Rote", "gilt",
               "ausrollen_paket_b.py · NB-Sicherung 11.09. (Kopie)"),
    Befundlage("2.382", "✔✔✔ SCHRITT 23 - PAKET B VON ANFANG BIS ENDE "
               "NACHGEWIESEN (Befund 2.371: bis dahin nie ein Hebelgeschaeft "
               "simuliert). `simuliere_kette.py --nachweis-paket-b` gegen die "
               "NB-Sicherung 11.09. 04:48, zwei Kopien (Schalter an / aus), die "
               "Attrappe gezielt ueber die Marktraenge gesteuert (Funding 0 + "
               "Turnover 0 -> Quote 0,373). 17 Faelle gezeigt: ONDO wird "
               "HEBELGESCHAEFT - Zeile instrument ,hebel', 2,1x, Verlust am Stop "
               "125,15 EUR; Mail mit Kopf ,Betrag 500 EUR - Hebel 2,1x', "
               "Hebelrechnung samt Aggregat-Satz, Liquidation, Anhang C, Chart "
               "als PNG; Hebeltopf 1.500 -> 2.000 EUR, Spot-Topf unveraendert; "
               "Cooldown 3,5 h (Spot 12 h). Aggregat im Lauf 170,20 EUR "
               "(ZZPLAN: Liquidation vor dem Stop = Eigenkapital 100; "
               "ZZOHNESTOP nach B: 70,20), mit dem Signal 295,35. Hebelfuehrung "
               "ordnet ZZPLAN SEIN geschriebenes Signal zu (HEBEL SENKEN mit "
               "Nachschuss), ZZOHNESTOP KURS FEHLT mit dem B-Hinweis. Derselbe "
               "Wert gleich danach: kein Modellaufruf (Anlass). Deckel "
               "ausgeschoepft (frei 2,90 EUR): AKT wird SPOT mit 800 EUR, die "
               "Mail nennt den Grund, Cooldown 12 h; mit Schalter AUS derselbe "
               "Betrag 800 EUR (N-38). BTC laeuft mit zwei Zellen, kein "
               "Akkumulationssignal. Kapital der Kopie 9.942 EUR (Stand 01.09., "
               "alt) -> Deckel 298 EUR; beim Rollout nachrechnen "
               "(2.376-rollout). Erster Lauf 16 von 18: ein Fehler der Pruefung "
               "selbst (erwartete frei 30 EUR, wo nur 3 frei waren) und der "
               "Befund 2.382-akku-anlass. Suite 2.192 Pruefungen, 4 bekannte "
               "Rote", "gilt",
               "simuliere_kette.py --nachweis-paket-b · NB-Sicherung 11.09. 04:48"),
    Befundlage("2.382-akku-anlass", "⚠️⚠️ ZU 2.380-akku-cooldown: DIE "
               "AKKUMULATIONSZELLE ERREICHT IHRE SPERRE IM LAUF NIE - und nicht "
               "nur wegen des Cooldowns. `anlass.beobachte` ist je Symbol und "
               "Instrument verschluesselt, nicht je Strategie; die "
               "Einstiegszelle laeuft zuerst (`_REIHENFOLGE`), die zweite sieht "
               ",nur 0 zaehlende Blockaenderung(en)' - die Anlass-Sperre ist im "
               "Betrieb aktiv. Ohne Anlass-Sperre (nur in der Kopie) fielen "
               "beide Zellen am Cooldown je Symbol. `zellen()` laesst (spot, "
               "einstieg) IMMER zu - ein Kernwert hat stets zwei Zellen. Folge "
               "fuer Paket B: kein Akkumulationssignal (gewollt), aber der "
               "Grund im Trichter lautet ,anlass' statt der Sperre; die "
               "Verdrahtung der Sperre belegt die Suite (Paket 17). Folge fuer "
               "Schritt 26: Anlass UND Cooldown je Zelle, mit Kostenschutz - "
               "sonst bleibt die Akkumulation auch nach der Registrierung "
               "stumm", "offen",
               "simuliere_kette --nachweis-paket-b 11.09. · "
               "rollen_lauf._REIHENFOLGE · anlass.beobachte"),
    Befundlage("2.382-topf", "✔ NUTZERENTSCHEIDUNG 11.09. spaet: WIE "
               "EMPFOHLEN - fuer Paket B bleibt die Topfregel, sie wird nach "
               "dem Rollout neu gefasst (Schritt 28). Der Befund: DER TOPF BEGRENZT "
               "PRAKTISCH NIE. `toepfe.belegt_eur` zaehlt nur Einstiege mit "
               "`outcome_status IS NULL` - die Zeilen, die die Signalverfolgung "
               "noch nicht gesehen hat. Am NB (11.09. 04:48): 5 Zeilen (Hebel "
               "1.500, Spot 1.000 EUR). NICHT gezaehlt: 379 laufende Einstiege "
               "(,offen' - Hebelspalte 77 zu 37.500 EUR Tranche, alle Geometrie "
               "1,0-1,5x; Spot 302 zu 144.000 EUR). Beide Lesarten gehen nicht "
               "auf: ,offen' mitzuzaehlen sperrte jeden Topf dauerhaft (Signale "
               "sind Empfehlungen, keine Positionen), es nicht zu tun macht den "
               "Deckel wirkungslos. Fuer den HEBEL begrenzt seit H-5 der "
               "Aggregat-Deckel (Positionen + Signale der letzten 24 h) - er "
               "ist die Grenze, die greift. Dazu trennt der Topf an der Spalte "
               "`hebel`: alte Geometriezeilen 1,2x zaehlen weiter als Hebel. "
               "Empfehlung: fuer Paket B nichts aendern, die Topfregel nach dem "
               "Rollout neu fassen", "gilt",
               "NB-Sicherung 11.09. signals · toepfe.belegt_eur"),
    Befundlage("2.382-liquidation", "✔ NUTZERENTSCHEIDUNG 11.09. spaet: B "
               "MIT DER LIQUIDATIONSREGEL - gebaut und geprueft (Paket "
               "Aggregat-Deckel: Eigenschaft ueber 34 Faelle der echten "
               "Fuehrung gegen die unabhaengige Tagesformel; die Mutante ohne "
               "Regel wird gefangen). Vorgelegt war: VARIANTE B UND DIE "
               "LIQUIDATION. B wurde als min(11,7 %% x Positionswert, "
               "Eigenkapital) vorgelegt und so gebaut. Fuer eine Position MIT "
               "Plan gilt aber: liegt die Liquidation vor dem Stop, zaehlt das "
               "Eigenkapital. Dieselbe Regel auf den ANGENOMMENEN Stop, an 185 "
               "geschlossenen NB-Positionen (Haltedauer bis zum Schluss, Median "
               "0,31 Tage): bei 56 %% laege die Liquidation davor - die meisten "
               "Altpositionen ueber 5x. Median 170 -> 176 EUR, 90 %% 496 -> 609 "
               "EUR, allein im Deckel 9,2 -> 14,1 %%. Neue Positionen des Systems "
               "sind auf 5x und RM-11 gedeckelt; betroffen waeren vor allem von "
               "Hand eroeffnete", "gilt",
               "NB-Sicherung 11.09. hebel_positions · Nutzer 11.09."),
    Befundlage("2.382-rundung", "○ FEINSCHLIFF (nach dem Rollout): der Hebel "
               "wird auf 0,1 GERUNDET (`round(hebel, 1)`), und der Verlust am "
               "Stop rechnet mit dem gerundeten Wert - aufgerundet ueberschreitet "
               "er das r(q)-Budget um bis zu 2,5 %% (ONDO: 2,09 -> 2,1x, 125,15 "
               "statt 124 EUR); die Liquidation nimmt den ungerundeten. Und "
               "Anhang C sagt auch bei einem Hebelgeschaeft ,falls ein Hebel "
               "noetig wird ➤ GEPRUEFT 15.09. (Code, Sicherung 15.09. 05:45). (1) DIE ZAHL: `entscheidungsrechnung.rechne` rundet `e['hebel'] = round(hebel, 1)`; mit dem GERUNDETEN Wert rechnen Verlust und Gewinn am Stop/Ziel, `signals.hebel`, der Mailsatz ,Hebel …x' und der Aggregat-Deckel (`hebel_aggregat` liest `verlust_am_stop_eur` und `hebel`); mit dem UNGERUNDETEN rechnen Liquidationspreis und ,Tage bis die Liquidation den Stop erreicht'. Zwei Hebel in einer Mail. (2) DIE GROESSE: die Abweichung liegt zwischen -0,05/h und +0,05/h - bei 2,0x bis 2,5 %%, bei 5,0x 1 %%, im Mittel null; aufgerundet ueberschreitet das Risiko das r(q)-Budget, abgerundet bleibt es darunter. Die Schwelle ,unter 2x Spot' prueft den UNGERUNDETEN Wert (`betraege`), die Grenze 5x ist exakt. (3) OFFENE VORAUSSETZUNG: welche Hebelstufen die Bitpanda-App tatsaechlich einstellen laesst. Die 188 echten Positionen zeigen EFFEKTIVE Hebel wie 5,61x - das sagt nicht, was man waehlen kann; Haeufungen bei 3, 5, 8 und 10 deuten auf gewaehlte Stufen. Loesungsweg vorgelegt. ➤ NUTZERAUSKUNFT 15.09.: bei Bitpanda meist die Stufen 2x, 3x, 5x und 10x, NICHT fuer alle Assets gleich; die tatsaechliche Position entscheidet der Nutzer selbst, gewuenscht ist eine generische, einfache Loesung in der Empfehlung. Vorschlag zur Darstellung vorgelegt, Entscheidung offen", "abgeloest",
               "simuliere_kette --nachweis-paket-b 11.09. · "
               "entscheidungsrechnung.rechne", "2.455-hebelstufen-gebaut", "ein ungerundeter Hebel fuer alle Zahlen, in der Mail die einstellbaren Stufen (15.09.)"),
    Befundlage("2.381", "✔✔ S-4 (c) O1 BEHOBEN - DIE 12 STUNDEN FUER "
               "KRYPTO WIRKTEN NICHT. `wiederholung.stunden` nahm den "
               "3,5-h-Takt fuer JEDES letzte Signal mit Hebel ueber 1,0 - und "
               "die Geometrie schrieb auf Spot-Signale 1,0-1,5x (am NB 77 "
               "offene Zeilen, alle auf Spotbestaenden). Gerechnet mit der "
               "echten Funktion: BTC 11.09. 04:47 (Hebel 1,2) war nur bis "
               "08:17 gesperrt. ➔ der kurze Takt gilt erst ab `hebel_ab` "
               "(2,0x, die Paket-B-Regel); danach BTC gesperrt bis 16:47 "
               "(12 h). Gegenprobe: 1,0 / 1,2 / 1,99 -> 12 h, 2,0 / 3,5 -> "
               "3,5 h", "gilt", "agent/wiederholung.stunden · NB-Sicherung 11.09."),
    Befundlage("2.381-spot", "✔ S-4 (a) NACHWEIS: DER HEBELSCHALTER "
               "VERAENDERT DEN SPOT-BETRAG NICHT (N-38). Ueber `rechne()` an "
               "1.436 echten NB-Einstiegen seit 23.08., mit und ohne Schalter: "
               "Betrag in ALLEN gleich (800 EUR). 472 davon (32,9 %%) trugen "
               "ohne Schalter einen Geometriehebel von 1,2x - mit Schalter "
               "reiner Spot: Verlust am Stop 48 -> 40 EUR (Median), der "
               "Betreff verliert ,(Hebel)', kein Buchen in den Hebeltopf. Die "
               "uebrigen 964 bitgleich. Das ist der Wegfall eines Scheinhebels, "
               "keine Aenderung der Spot-Groesse", "gilt",
               "s4_spot_nachweis.py 11.09. · NB-Sicherung 11.09."),
    Befundlage("2.381-mail", "✔✔ S-4 (b) DIE MAIL GEGLIEDERT - nach dem "
               "Vorschlag vom 11.09. (2.372), NICHTS GESTRICHEN. Kopf AUF "
               "EINEN BLICK (Zone, Stop, Ziel, Betrag und Hebel, Ergebnis in "
               "EUR, Trefferquote, beide Gebuehrenzeilen, Gesamtbild) · WAS "
               "DAGEGEN SPRICHT (je eine Zeile: Widerspruch der Gegenpruefung, "
               "UNGUENSTIG-Merkmale, Grenzen der Rechnung, Z1) · 1 Bewertung · "
               "2 Rechnung · 3 Lage des Werts · 4 Marktvergleich · 5 Modelle "
               "(Urteil; Gegenpruefung mit dem Widerspruch in der "
               "Ueberschrift) · 6 Termine und Projekt · ANHANG (A nicht "
               "eingerechnet, B die ZWEITE, aeltere Trefferquote als solche "
               "benannt, C Liquidationsabstaende). Die zwei Trefferquoten: "
               "entschieden wird nach Abschnitt 1 (im Kopf), die "
               "Erfahrungsrate steht nur noch im Anhang. Der Kopf LIEST die "
               "fertigen Abschnitte (`gesamtbild.saetze/dagegen`) - keine "
               "zweite Rechnung. Trennstellen als Konstanten in "
               "`wahrscheinlichkeit`. Nachweis: Paket Mailgliederung 12 "
               "Pruefungen, darunter die EIGENSCHAFT ,jede uebergebene Zeile "
               "steht in der Mail'; Kettensimulation gegen die NB-Kopie baut "
               "die ONDO-Mail ueber den echten Weg, ohne neue Luecke. ⚠️ NICHT "
               "ERLEDIGT - Feinschliff nach dem Rollout: dieselbe Kursmarke "
               "aus drei Modulen (Marken, Weg zum Ziel, Vorfilter) und drei "
               "Rangangaben stehen weiter getrennt; die Gebuehren stehen im "
               "Kopf und im Anhang B", "gilt",
               "agent/signal_mail.baue_mail · gesamtbild.dagegen · Paket "
               "Mailgliederung · simuliere_kette 11.09."),
    Befundlage("2.380-fenster", "✔ NUTZERENTSCHEIDUNG 11.09.: DAS FENSTER "
               "BETRAEGT 24 STUNDEN (vorher gesetzt 3 Tage). "
               "`hebelfuehrung.KOPPEL_TAGE = 1.0` - es bestimmt, welches "
               "Signal einer Position als Plan gilt, und wie lange ein nicht "
               "eroeffnetes Hebelsignal im Aggregat-Deckel Risiko belegt. Laut "
               "2.380-sim macht der Deckel damit rund 32 %% statt 73 %% der "
               "Hebelkandidaten zu Spot (Watchlist 2026, 18.213 EUR). Folge: "
               "wer spaeter als 24 h nach dem Signal eroeffnet, hat keinen "
               "Plan - siehe 2.380-ohne-stop", "gilt",
               "Nutzerentscheidung 11.09. · 2.380-annahmen"),
    Befundlage("2.380-ohne-stop", "✔ NUTZERENTSCHEIDUNG 11.09.: VARIANTE B - "
               "eine Position OHNE bekannten Stop zaehlt im Aggregat-Deckel "
               "mit einem angenommenen Stop von 11,7 %% ab Einstand (Median "
               "der Systemstops, 2.378-gegenpruefung), hoechstens mit dem "
               "Eigenkapital (`hebel_aggregat.STOP_ANGENOMMEN`). Variante A "
               "(ganzes Eigenkapital) vom Nutzer ABGELEHNT: *,eine Position "
               "blockiert alles, das passt nicht zu unserem Vorgehen - initial "
               "haben wir angedacht, dass zumindest drei Hebelpositionen offen "
               "sein koennen'*. An den 188 echten Positionen: A Median 222 EUR "
               "(90 %% 720), allein im Deckel 18 %%, im Median passen 2,5; B "
               "Median 166 EUR (90 %% 500), allein 9 %%, im Median passen 3,3. "
               "Die Hebelmail sagt es: ,Stop unbekannt - im Aggregat-Deckel "
               "angenommen 11,7 %%' und je Position ,Im Deckel X EUR'. "
               "Nachweis: Paket Aggregat-Deckel (Eigenschaft ueber 27 Faelle), "
               "Mutationstest (A macht 4 Pruefungen rot, B ohne EK-Grenze 1), "
               "E2E 2.382. ✔ Dazu die Liquidationsregel (Nutzer 11.09. spaet, "
               "2.382-liquidation): liegt die Liquidation schon vor dem "
               "angenommenen Stop, zaehlt das Eigenkapital", "gilt",
               "NB-Sicherung 11.09. hebel_positions · Nutzer 11.09. · "
               "agent/hebel_aggregat.py"),
    Befundlage("2.380", "✔✔✔ H-5 GEBAUT - DER AGGREGAT-DECKEL "
               "(`agent/hebel_aggregat.py`, Nutzerentscheidung 11.09.: alle "
               "Hebelrisiken zusammen hoechstens 3 %% des Kapitals; P-4: die "
               "Korrelation gehoert hierher). Offen gezaehlt: Positionen aus "
               "`hebel_positions` (Verlust bis zum Plan-Stop, hoechstens das "
               "Eigenkapital; ohne bekannten Stop oder mit Liquidation vor dem "
               "Stop das Eigenkapital - ⚠️ ohne Stop seit dem Nutzerentscheid "
               "Variante B, 2.380-ohne-stop), offene Hebelsignale (nicht aufgeloest, "
               "Frist nicht abgelaufen, im Zuordnungsfenster, keiner Position "
               "zugeordnet) und die Signale DIESES Laufs. Die Summe unterstellt "
               "Korrelation 1. Der Deckel BEGRENZT: ein neuer Trade bekommt "
               "hoechstens das freie Restrisiko, faellt er unter 2x, wird er "
               "Spot mit dem gewohnten Betrag. Faellt die Abfrage aus: kein "
               "Hebel, laut. Neue Signalspalte `verlust_am_stop_eur` (die "
               "Tranche in `position_size_eur` ist nicht der gerechnete "
               "Betrag), in `models.Signal` und im Export. Nachweis: Paket "
               "Aggregat-Deckel 17 Pruefungen, von Hand gerechnet; "
               "MUTATIONSTEST - vier eingebaute Fehler, jeder macht Pruefungen "
               "rot (7 / 1 / 4 / 4 von 17); NB-Kopie: 0 EUR offen, Deckel 546 "
               "EUR; mit zwei kuenstlichen Positionen 158 EUR (57,50 bis zum "
               "Stop + 100 Eigenkapital ohne Plan), das Plan-Signal nicht "
               "doppelt", "gilt",
               "agent/hebel_aggregat.py · pruefe_pakete --paket Aggregat-Deckel "
               "· Mutationstest und NB-Kopie 11.09."),
    Befundlage("2.380-sim", "⚠️⚠️ WAS DER DECKEL MIT DEN HEBELTRADES TUT - "
               "und wie stark es an EINER Annahme haengt. "
               "`simuliere_hebelverteilung.py` Abschnitt 3b: Hebelkandidaten "
               "der Auswahl je Tag, beste Quote zuerst, jeder belegt sein "
               "Risiko W Tage (Signal offen oder Position gehalten). WATCHLIST "
               "2026, 18.213 EUR: W = 1 Tag -> voll 55,9 %% · gekuerzt 11,7 %% "
               "· durch den Deckel Spot 32,4 %% · Median 3 Hebeltrades je Tag. "
               "W = 3 Tage -> voll 8,0 %% · gekuerzt 19,3 %% · Spot 72,7 %% · "
               "Median 1 je Tag. Alle Jahre, 18.213 EUR: W 1 -> Spot 61,0 %%, "
               "W 3 -> 84,0 %%. Gegenpruefung G7 (ein nicht greifender Deckel "
               "aendert nichts, 500 x 3) und G8 (die Belegung ueberschreitet "
               "den Deckel nie) bestanden. ⚠️ Naeherung: Tagesanker, keine "
               "Ausstiege vor Ablauf von W, kein Cooldown", "gilt",
               "simuliere_hebelverteilung.py 11.09. (drei Laeufe)"),
    Befundlage("2.380-annahmen", "⚠️⚠️ ZUR ABSTIMMUNG - drei gesetzte "
               "Annahmen. (1) DAS FENSTER (`hebelfuehrung.KOPPEL_TAGE` = 3 "
               "Tage): wie weit ein Signal vor der Eroeffnung als Plan gilt "
               "UND wie lange ein nicht eroeffnetes Hebelsignal Risiko belegt. "
               "Echte Latenz Signal -> Eroeffnung am NB: 0,5 / 0,6 / 3,4 "
               "STUNDEN (nur drei Faelle seit 14.07.); Haltedauer der 188 "
               "echten Positionen Median 0,3 Tage, 90 %% unter 3,3. Bei 3 Tagen "
               "macht der Deckel 72,7 %% der Hebelkandidaten zu Spot, bei 1 Tag "
               "32,4 %% (2.380-sim). (2) POSITION OHNE BEKANNTEN STOP zaehlt mit "
               "dem ganzen Eigenkapital: echte Positionen Median 222 EUR, 90 %% "
               "720, hoechstens 1.831 EUR - schon eine groessere Handposition "
               "fuellt den Deckel von 546 EUR allein; gleichzeitig offen waren "
               "hoechstens 5 Positionen mit 3.944 EUR Eigenkapital. (3) "
               "Gezaehlt wird bis zum URSPRUENGLICHEN Stop - ein nachgezogener "
               "Stop senkt das Risiko nicht, weil das System nicht weiss, "
               "welcher Stop bei der Boerse liegt "
               "✔✔✔ GESCHLOSSEN AM 13.09. - ALLE DREI WAREN AM SELBEN "
               "TAG ENTSCHIEDEN, an dem sie gestellt wurden; der Befund ist "
               "nur nie nachgezogen worden. (1) DAS FENSTER: "
               "Nutzerentscheidung 11.09., 24 Stunden statt 3 Tage - steht "
               "in 2.380-fenster, `hebelfuehrung.KOPPEL_TAGE = 1.0` seit "
               "Commit 08a21f6, und `ausrollen_paket_b.py` bewacht den Wert "
               "(`abs(KOPPEL_TAGE - 1.0) < 1e-9`). (2) OHNE BEKANNTEN STOP: "
               "Nutzerentscheidung 11.09., VARIANTE B - angenommener Stop "
               "11,7 % ab Einstand, hoechstens das Eigenkapital "
               "(2.380-ohne-stop). ⚠️ Die hier genannte Annahme ,zaehlt mit "
               "dem ganzen Eigenkapital' ist genau die Variante A, die der "
               "Nutzer ABGELEHNT hat: *,eine Position blockiert alles, das "
               "passt nicht zu unserem Vorgehen'*. (3) BIS ZUM "
               "URSPRUENGLICHEN STOP: als ,Verlust bis zum Plan-Stop' in "
               "`hebel_aggregat` gebaut und mit *,ja Paket B, Deckel 5x, "
               "Rest wie empfohlen'* angenommen. "
               "⚠️⚠️⚠️ WAS DARAN MEIN FEHLER IST: ich habe dem Nutzer am "
               "13.09. alle drei als OFFEN vorgelegt und zu (1) eine "
               "Empfehlung ausgesprochen - fuer etwas, das er zwei Tage "
               "zuvor selbst entschieden hatte und was seither im Code "
               "steht. Wer einen offenen Befund vorlegt, ohne zu pruefen, "
               "ob ein SPAETERER ihn beantwortet, laesst den Nutzer zweimal "
               "dasselbe entscheiden",
               "gilt",
               "NB-Sicherung 11.09. hebel_positions/hebel_signals · 2.380-sim"),
    Befundlage("2.379-instrument-korrektur", "⚠️⚠️⚠️ KORREKTUR ZU 2.379 UND "
               "2.379-instrument: die Kette schrieb `signals.instrument` NIE. "
               "Die Spalte fuellte erst die Start-Migration mit dem Instrument "
               "der GRUPPE - fuer Krypto immer spot (NB: 3.838 spot, 12 "
               "absicherung, 0 hebel). Hebelfuehrung und Ausstiegsfuehrung "
               "lesen genau diese Spalte - im Betrieb haetten sie nie ein "
               "Hebelsignal gefunden. Der E2E-Nachweis aus 2.379 hatte die "
               "Zeile VON HAND auf hebel gesetzt und das verdeckt. Die Spalte "
               "`hebel` taugt nicht als Ersatz: alle 77 offenen Zeilen mit "
               "`hebel` (1,0-1,5x, Geometrie) stehen auf SPOTbestaenden. ➔ "
               "`felder_aus_entscheidung` schreibt jetzt instrument hebel fuer "
               "ein Hebelgeschaeft aus r(q) oder SHORT, sonst das Instrument "
               "des Laufs; die Migration fasst nur leere Zeilen an. Nachweis "
               "ueber den ECHTEN Schreibweg (felder + schreibe_signal), "
               "Mutationstest: ohne die Korrektur 7 von 17 Pruefungen rot. "
               "Topf und Cooldown (Spalte `hebel`) unveraendert", "gilt",
               "signal_abbildung.felder_aus_entscheidung · NB-Sicherung 11.09. "
               "· Paket Aggregat-Deckel"),
    Befundlage("2.380-akku-schalter", "⚠️⚠️ KORREKTUR EINES PLANPUNKTS "
               "(Nutzerfund 11.09. an der GUI): der Akkumulationsschalter steht "
               "fuer BTC, ETH und SOL SEIT LANGEM auf An. `db.get_dca_erlaubt()` "
               "liefert ohne Tabellenzeile die Vorgabe {BTC, ETH, SOL}; GUI, "
               "`handelsauftrag.strategie_fuer` und `assetklassen._schalter` "
               "lesen darueber - richtig. NUR die L1-Pruefung in `soll_ist.py` "
               "las die TABELLE (`WHERE dca_erlaubt=1`), und dort steht am NB "
               "nur BTC als Zeile. Daraus entstanden der Planpunkt ,ETH und "
               "SOL erst mit Paket 2 setzen' und meine Aussage ,am NB nur BTC' "
               "- beide falsch. ➔ L1 prueft ueber `get_dca_erlaubt`; Lage, "
               "Schritt 24 und 27 berichtigt", "gilt",
               "database/db.get_dca_erlaubt · soll_ist.py L1 · NB-Sicherung 11.09."),
    Befundlage("2.380-akku-cooldown", "⚠️⚠️⚠️ DIE AKKUMULATION LIEF IM "
               "BETRIEB NIE - trotz Schalter. NB-Sicherung 11.09.: 0 von 3.859 "
               "Rollen-Signalen mit Strategie akkumulation (1.994 einstieg, "
               "1.865 aus der Zeit vor der Strategiespalte). BTC, ETH und SOL "
               "tragen nur einstieg (88 / 79 / 77). URSACHE im Code: "
               "`wiederholung.gesperrt_bis()` bekommt die Strategie, fragt aber "
               "das juengste Signal des SYMBOLS ab, gleich welcher Strategie. "
               "Die Zellen laufen einstieg vor akkumulation "
               "(`rollen_lauf._REIHENFOLGE`). REPRODUZIERT mit der echten "
               "Funktion an der NB-Sicherung: nach dem Einstiegssignal BTC "
               "11.09. 04:47 ist die Einstiegszelle nach 12 h frei, die "
               "Akkumulationszelle bis 13.09. 04:47 gesperrt (48 h) - und weil "
               "die Einstiegszelle rund alle 12 h eine neue Zeile schreibt, "
               "laeuft die 48-h-Sperre nie ab. Dieselbe Ursache hinter der "
               "alten Simulationsluecke ,KEIN Asset lief mit zwei Zellen "
               "durch'. ⚠️ Fuer Paket B ohne Wirkung (die Akkumulation ist "
               "gesperrt). ⚠️ Der Fix gehoert in Paket 2 (Schritt 26) und "
               "braucht einen Kostenschutz: eine gesperrte Akkumulationszelle "
               "schreibt keine Zeile - ohne Cooldown holte sie sich sonst je "
               "Lauf ein eigenes Modellurteil", "offen",
               "wiederholung.gesperrt_bis · rollen_lauf._REIHENFOLGE · "
               "NB-Sicherung 11.09."),
    Befundlage("2.379", "✔✔✔ H-4 GEBAUT - DIE HEBELFUEHRUNG "
               "(`agent/hebelfuehrung.py`). Jede OFFENE Position aus "
               "`hebel_positions` (echter Bitpanda-Abgleich) wird mit ihrem "
               "Plan verbunden: dem juengsten Rollen-Hebelsignal desselben "
               "Symbols und derselben Richtung bis 3 Tage vor der Eroeffnung "
               "(gesetzt, nicht gemessen - Signalnummer steht in der Mail). "
               "Gefuehrt: Einstand, Tage, Ergebnis vor und nach Finanzierung, "
               "Finanzierung bisher und je Tag (Staffel aus "
               "`backward_tracking`), Liquidationspreis mit den echten Tagen, "
               "der Plan ueber `ausstiegsrechnung.bewerte()`. Empfehlungen "
               "nach Dringlichkeit: LIQUIDATION ERREICHT · SCHLIESSEN · HEBEL "
               "SENKEN (mit Nachschuss) · KURS FEHLT · STOP NACHZIEHEN · "
               "HALTEN. Eigene Mail aus dem Rollen-Lauf, einmal je Zustand und "
               "Tag, vermerkt erst NACH dem Versand; die Zeilen stehen "
               "zusaetzlich in der Verkaufsmail. Finanzierung = Information, "
               "kein Ausloeser (Regel 2); HEBEL SENKEN ist RM-11, keine "
               "Bewertung. Nachweis: Paket Hebelfuehrung 31 Pruefungen, "
               "Faelle von Hand gerechnet; E2E an der NB-Kopie mit "
               "kuenstlicher Position (LINK 5x, Stop 11,5 %%: Tag 1,5 HALTEN "
               "bis Tag 3,0 - Tag 3,5 HEBEL SENKEN, Nachschuss 0,48 EUR); "
               "`simuliere_kette` bringt die Hebelmail an", "gilt",
               "agent/hebelfuehrung.py · pruefe_pakete --paket Hebelfuehrung "
               "· h4_e2e / simuliere_kette 11.09."),
    Befundlage("2.379-rm11", "⚠️⚠️⚠️ RM-11 WAR FALSCH - bei JEDEM "
               "erlaubten Hebel lag die geschaetzte Liquidation VOR dem Stop. "
               "`max_safe_hebel` rechnete `(1 - Marge) / Stop` aus der Zeit, "
               "als die Marge ein Puffer auf 1/Hebel war (0,175). Am 16.07. "
               "bekam dieselbe Zahl in `estimate_liquidation_price` die "
               "Bedeutung Wartungsmarge (am echten LINK-Fall kalibriert), am "
               "19.07. wurde sie 0,09 - `max_safe_hebel` wurde nicht "
               "nachgezogen. REPRODUZIERT mit den echten Funktionen: Stop 5 %% "
               "-> 18,20x erlaubt, Liquidation 3,85 %% UEBER dem Einstieg; "
               "11,7 %% (Betriebsmedian) -> 7,78x, Liquidation 4,24 %% unter "
               "dem Einstieg; 16,4 %% -> 5,55x / 9,91 %%; 25 %% -> 3,64x / "
               "20,30 %%. Richtig (Liquidation und Stop gleichgesetzt): 7,38 "
               "· 5,09 · 4,18 · 3,15x. Die Pruefung, die das finden sollte, "
               "verglich `rechne()` mit `max_safe_hebel()` - die Funktion mit "
               "sich selbst. ➔ neu hergeleitet fuer LONG und SHORT, mit "
               "Haltetagen; geprueft gegen die EIGENSCHAFT (294 Faelle, "
               "Abweichung 2,8e-14). Betrifft auch die alte Kette "
               "(`pre_check_hebel`, RM-11 exakt)", "gilt",
               "hebel_risk_gate.max_safe_hebel · h4_sichtung / h4_pruefung 11.09."),
    Befundlage("2.379-liq", "⚠️⚠️ ZWEI WEITERE STELLEN MIT 1/HEBEL. (1) "
               "`rechne()` schrieb `liquidation_etwa_eur = Kurs x (1 - "
               "1/Hebel)` - bei 5x 20 %% unter dem Einstieg, kalibriert 12,1 "
               "%%; dazu auf 2 Stellen gerundet, bei Werten um 0,05 EUR "
               "wertlos. Jetzt `estimate_liquidation_price` Tag 0, 6 Stellen, "
               "und der Rechnungssatz nennt, bis zu welchem Tag die "
               "Liquidation hinter dem Stop bleibt. (2) Der Faktentext fuer "
               "Rolle BC (`lagebeschreibung._hebelgeometrie`) nannte bei "
               "3/6/10-fach 33/17/10 %% - richtig 27/8/1 %%, beim "
               "Hoechsthebel neunmal zu weit. Ein Fakt, den das Modell liest: "
               "Prompt-Stand 2026-09-11a. Die Pruefung dazu testete die "
               "Identitaet 1-(1-1/h) = 1/h", "gilt",
               "entscheidungsrechnung.rechne · lagebeschreibung · "
               "rolle_trader.PROMPT_STAND"),
    Befundlage("2.379-instrument", "⚠️⚠️ DIE AUSSTIEGSFUEHRUNG HAETTE "
               "JEDES HEBELSIGNAL DER ROLLEN-KETTE ALS SPOT GEFUEHRT. "
               "`compute_ausstiegs_empfehlungen` setzte `ist_hebel` nach der "
               "TABELLE (`hebel_signals`); die Rollen-Kette schreibt nach "
               "`signals` mit der Spalte `instrument`. Folge: Fuehrung unter "
               "(Symbol, spot), gegen den Spotbestand geprueft, und "
               "`_fuehrung_zu(..., hebel)` fand nie etwas. Am NB unsichtbar: "
               "0 von 3.859 Zeilen der Rollen-Kette tragen instrument hebel. "
               "➔ die Zeile entscheidet, in beiden Schleifen. E2E an der "
               "NB-Kopie: das kuenstliche Signal steht als Hebel UND Bestand; "
               "die neun Spotsignale von LINK bleiben Spot (ihre zwei "
               "SCHLIESSEN standen schon vorher)", "gilt",
               "backward_tracking.compute_ausstiegs_empfehlungen · h4_e2e 11.09."),
    Befundlage("2.379-schalter", "⚠️⚠️ `hebel_screening.aktiv: false` "
               "HAETTE DIE ROLLEN-KETTE ABGESCHALTET. Der Schalter stand vor "
               "einem `return True` am Anfang von `hebel_screening_job` - "
               "dahinter liegen der Abgleich der echten Hebelpositionen und "
               "der Umlauf der Rollen-Kette. Genau dieser Schalter liegt nahe, "
               "wenn die alte Kette beim Rollout stillgelegt wird (offene "
               "Frage 2.369): keine Urteile, keine Mails, keine Meldung. ➔ er "
               "legt nur noch das Screening still", "gilt",
               "scheduler/background.hebel_screening_job"),
    Befundlage("2.379-tage", "⚠️⚠️ WIE LANGE EIN HEBEL SICHER BLEIBT. "
               "RM-11 prueft bei der Eroeffnung Tag 0 (Nutzerentscheidung "
               "14.07.: keine Haltedauer raten); die Finanzierung schiebt die "
               "Liquidation um rund 0,2 %% des Einstiegs je Tag. "
               "`simuliere_hebelverteilung.py` mit korrigiertem RM-11: bei "
               "18.213 EUR erreicht die Liquidation den Stop im Median nach 79 "
               "Tagen (10 %% nach 26), KEIN Fall unter 3,3 Tagen; Watchlist "
               "2026 Median 73 (10 %% 25). Bei 30.000 EUR: Median 31 (10 %% "
               "2,6), am ersten Tag 8,5 %%, unter 3,3 Tagen 11,2 %%. Die 188 "
               "echten Positionen am NB hielten im Median 0,3 Tage (90 %% "
               "unter 3,3; Hebel Median 5,6x). ➔ beim heutigen Kapital keine "
               "Handlung noetig; ueber eine Tagesreserve beim Einstieg ist zu "
               "entscheiden, wenn das Kapital waechst", "offen",
               "simuliere_hebelverteilung.py 11.09. (drei Laeufe) · NB "
               "hebel_positions"),
    Befundlage("2.378-korrektur", "⚠️ KORREKTUR ZU 2.378, nach 2.379-rm11 "
               "reproduziert (R-R11): ,Liquidationsabstand greift nie' gilt "
               "bei 9.942 und 18.213 EUR UNVERAENDERT - dort begrenzt das "
               "Kapital den Hebel, bevor RM-11 erreicht wird; alle Zahlen bei "
               "18.213 EUR bitgleich. Bei 30.000 EUR greift das korrigierte "
               "RM-11 in 6,4 %% aller Durchgelassenen (Watchlist 2026: 3,7 "
               "%%); die Grenze 5x sinkt dort von 19,0 auf 16,0 %% (Watchlist "
               "29,6 auf 26,9 %%). Der Hebelanteil bleibt 79,8 %%", "gilt",
               "h4_hebelverteilung_voll/_2026/_2026_watchlist.log 11.09."),
    Befundlage("2.378", "✔✔ H-3 - WAS r(q) TUT, UEBER ECHTE ANKER "
               "SIMULIERT (`simuliere_hebelverteilung.py`, Standardwerkzeug "
               "mit Schaltern). Messmenge V1, 633.672 Anker 2019-2026, 536 "
               "Symbole; Bewertung, Stop und Hebel ueber die ECHTEN "
               "Funktionen. Durch die Bewertungsschwelle: 113.224 (17,9 %%). "
               "BEI 18.213 EUR KAPITAL: Spot 56,3 %% · Hebel 43,7 %% (2x 24,2 "
               "· 3x 9,7 · 4x 4,4 · Grenze 5x 5,3 %%); Liquidationsabstand "
               "greift NIE. Nach Beitragslage: nur funding 34,0 %% Hebel · "
               "funding+turnover 93,6 %% (28,1 %% an der 5x-Grenze) · nur "
               "turnover 91,6 %%. Kapital 9.942 EUR: 12,1 %% Hebel; 30.000 "
               "EUR: 79,8 %% (19,0 %% an der Grenze). Risiko je Hebeltrade "
               "Median 178 EUR bei 18.213 EUR. Ab 2026: Spot 54,0 %% · Hebel "
               "46,0 %%; in der Auswahlmenge (oberste 20 %%) 62,6 %%. NUR "
               "WATCHLIST 2026: 39 Werte, 8.606 Anker, 3.694 durch die Schwelle (42,9 %%); Spot 41,6 %% · Hebel 58,4 %% (2x 28,3 · 3x 13,2 · 4x 7,1 · Grenze 5x 9,8 %%); Stop Median 13,7 %% - naeher am Betrieb (11,7 %%); in der Auswahlmenge 77,3 %% Hebel", "gilt",
               "simuliere_hebelverteilung.py · Laeufe 11.09.",
               basis="Messmenge V1 · Kapital 9.942/18.213/30.000 EUR · "
                     "Einstellungen aus config.yaml"),
    Befundlage("2.378-stop", "⚠️⚠️ EIN IRRTUM IM ERSTEN ENTWURF - vom "
               "Vorabtest gefangen, nicht vom Lauf. Das Werkzeug rechnete "
               "zuerst OHNE Widerlegungspreis und nahm an, er koenne den "
               "Stop nur weiter machen. FALSCH: `_stop_abstand` nimmt den "
               "Rueckfall 2,5 x ATR nur ohne Widerlegungspreis; mit ihm "
               "gilt der Rauschboden max(2 x ATR, 5 %%), der Stop wird "
               "ENGER. Am Notebook nennt das Modell ihn in 1.425 von 1.427 "
               "Einstiegen. Der Vorabtest ergab Stops um 20 %% gegen echte "
               "7,6 %% - der Abgleich mit den NB-Signalen hat den Fehler "
               "gezeigt. Jetzt: Betriebsfall mit Widerlegungspreis im "
               "Rauschen, der Fall ohne als Empfindlichkeit", "gilt",
               "Vorabtest 11.09. · NB-Sicherung 11.09."),
    Befundlage("2.378-gegenpruefung", "✔ GEGENPRUEFUNG, im Werkzeug "
               "eingebaut und in jedem Lauf bestanden: G1 Hebel unabhaengig "
               "nachgerechnet (2.000 Anker x 3 Kapitalstufen, 0 "
               "Abweichungen) · G2 Rohhebel linear im Kapital · G3 mehr "
               "Kapital nie weniger Hebel · G4 ATR identisch mit "
               "`rollen_eingabe.atr_bis` · G5 Quote je Beitragslage = "
               "direkte Bewertung · G6 Stop = `rechne()` mit und ohne "
               "Widerlegungspreis. DAZU UNABHAENGIG: die Stopregel des NEUEN "
               "Codes auf 1.289 echte NB-Einstiege angewandt, mit deren "
               "Widerlegungspreis - Median 11,7 %% (10 %% 5,9 · 90 %% 16,0); "
               "ohne Widerlegungspreis 14,6 %%; alter Code am NB 7,7 %%",
               "gilt", "simuliere_hebelverteilung.py G1-G6 · NB-Sicherung"),
    Befundlage("2.378-deutung", "⚠️⚠️ WAS DIE ZAHLEN FUER DAS "
               "SCHARFSCHALTEN HEISSEN: (1) die Regel verhaelt sich wie "
               "gebaut - Spot, wo die Quote nichts hergibt; Hebel, wo "
               "Beitraege tragen; die Grenzen greifen. (2) Die HISTORISCHEN "
               "Stops (Median 16,4 %%) sind WEITER als die zu erwartenden "
               "des Betriebs (11,7 %%) - im Betrieb entsteht also eher MEHR "
               "Hebel als simuliert. (3) Der Hebel haengt stark am KAPITAL "
               "(12 %% -> 80 %% zwischen 9.942 und 30.000 EUR) - deshalb war "
               "P-3 kein Detail. (4) Die GROBE Stufung (A9) wird sichtbar: "
               "wo beide Beitraege vorliegen, landet fast jeder Fall ueber 2x "
               "und ein grosser Teil an der Grenze. (5) Ob hoeherer Hebel "
               "haeufiger traegt, zeigt die Simulation NICHT (A1). ➔ "
               "EMPFEHLUNG: den Schalter erst mit Positionsfuehrung (H-4), "
               "Aggregat-Deckel (H-5) und dem E2E-Nachweis (Schritt 23) "
               "einschalten - also mit dem Rollout von Paket B, nicht jetzt",
               "gilt", "Befund 2.378 · Nutzerentscheidung offen"),
    Befundlage("2.377", "✔✔✔ H-2 GEBAUT - DER HEBEL ENTSTEHT AUS DER "
               "WAHRSCHEINLICHKEIT, wie beauftragt (28.08./05.09./11.09.). "
               "`betraege.hebelrechnung`: Risiko = r(q) x Kapital, r(q) = "
               "halbes Kelly geklammert 0,50-1,25 %% (N-39); Positionswert = "
               "Risiko / Stop; Hebel = Positionswert / 500 EUR. Unter 2x "
               "SPOT mit unveraendertem Betrag (N-38); harte Grenze 5x bis "
               "zur Trennschaerfe; ohne positive Erwartung (Kelly <= 0) KEIN "
               "Hebel, auch nicht die Untergrenze. In der Kette: die Quote "
               "wird VOR der Vorabrechnung bestimmt, das Etikett aus r(q) "
               "steuert taktische Zelle, Hebel-Schalter und Topf; `rechne()` "
               "bekommt Risiko, Einsatz und Grenze. Ohne Kapital oder Quote: "
               "kein Hebel, Satz in der Mail, einmal je Lauf im Log. Die "
               "Herleitung steht in EUR im Abschnitt DIE RECHNUNG. ⚠️ "
               "Schalter `rollen_kette.hebel_aus_quote.aktiv` steht AUS - "
               "Schritt 19 simuliert die Hebelverteilung vor dem "
               "Scharfschalten", "gilt",
               "agent/betraege.py · agent/rollen_lauf.py · "
               "agent/entscheidungsrechnung.py · config.yaml"),
    Befundlage("2.377-gegenpruefung", "⚠️⚠️ DIE GEGENPRUEFUNG HAT EINEN "
               "ECHTEN FEHLER IM ERSTEN EINBAU GEFUNDEN. Das Etikett kam aus "
               "dem Stop von `dimensioniere` - der kennt die Zielweite 2,5 x "
               "ATR nicht. In 20 von 144 Rasterfaellen setzte `rechne()` den "
               "Stop weiter (10 statt 8 %%, 20 statt 16 %%), und aus ,Hebel "
               "2,0x' im Etikett wurde 1,6x in der Rechnung - unter der "
               "Grenze, ab der es ueberhaupt ein Hebel ist. Dazu deckelt "
               "`rechne()` auf den Liquidationsabstand. ➔ Neu: "
               "`entscheidungsrechnung.stop_relativ()` und `hebel_sicher()` "
               "- dieselbe Stelle, die `rechne()` benutzt; `hebelrechnung` "
               "rechnet die Liquidationsgrenze mit. Nachweis: 400 "
               "Zufallsfaelle durch BEIDE echten Funktionen, Stop und "
               "Etikett und Hebel identisch. Die Formel selbst: 2.000 "
               "Zufallsfaelle unabhaengig nachgerechnet, 0 Abweichungen. ✔ "
               "KETTE gegen die NB-Kopie, Schalter nur im Speicher an: 1 "
               "Signal, 1 Mail, 0 Fehler, keine Quotenabweichung; ONDO-Mail: "
               ",Trefferquote 34,6 %% ... halbes Kelly 0,97 %% ... = 97 EUR' "
               "und ,bei 11,9 %% Stop: 813 EUR Positionswert / 500 EUR "
               "Einsatz = 1,6x - unter 2,0x, daher Spot mit dem gewohnten "
               "Betrag', darunter der Kapitalhinweis (10 Tage alt)", "gilt",
               "Gegenpruefung 11.09. · pruefe_pakete --paket ,Hebel aus Quote'"),
    Befundlage("2.377-grenzen", "⚠️ WAS H-2 NICHT LEISTET, benannt: (1) die "
               "TRENNSCHAERFE (steigt die reale Trefferquote mit dem Hebel?) "
               "ist weiter ungemessen - A1; bis dahin begrenzen Klammer und "
               "5x. (2) Die Stufung der Quote bleibt grob (Fuenftel, A9). (3) "
               "Der Hebel wird auf 0,1x gerundet; das Risiko am Stop kann "
               "dadurch um wenige Euro ueber r(q) liegen (gemessen hoechstens "
               "rund 1 %%). (4) Der Faktentext der Lagebeschreibung sagt noch "
               ",Welcher Faktor es wird, folgt aus dem Risikobudget und dem "
               "gewaehlten Stopabstand' - mit Schalter stimmt das nur halb. "
               "Er geht auch an das Modell; geaendert wird er deshalb nicht "
               "nebenbei, sondern in Schritt 22 (Mail) mit Blick auf den "
               "Prompt. (5) Ein Hebelgeschaeft ist in der Kette noch nicht "
               "end-to-end simuliert - Schritt 23. (6) Bei SPOT stehen jetzt "
               "zwei Risikozahlen untereinander: 97 EUR aus der "
               "Hebelrechnung und ,Am Stop verlieren Sie 95 EUR' aus dem "
               "Spot-Betrag - Feinschliff in Schritt 22", "gilt",
               "Befund 2.377 · A1/A9 · Schritt 22/23"),
    Befundlage("2.377-pruefung", "✔ EINE BESTEHENDE PRUEFUNG WURDE BEWUSST "
               "ANGEPASST, nicht umgangen: ,beide Rechnungen fragen die "
               "Strategie' zaehlte `_HA_HEBEL_OK(strategie)` und erwartete 2. "
               "Seit H-2 fragt auch die Hebelrechnung - sonst rechnete sie "
               "fuer eine Akkumulation einen Hebel, den beide Rechnungen "
               "danach verweigern. Erwartet sind jetzt 3, mit Begruendung",
               "gilt", "pruefe_pakete Paket ,Zellen'"),
    Befundlage("2.376", "✔✔✔ H-1 GEBAUT - DAS KAPITAL IST LESBAR, "
               "VOLLSTAENDIG UND UEBERWACHT. (1) P-3 Option A "
               "(Nutzerentscheidung 11.09.): `schreibe_tageswert` zaehlt "
               "`quantity + staked_quantity`. (2) FORTSCHREIBUNG: ein "
               "fehlender Tageskurs wird hoechstens VIER Tage durch den "
               "letzten bekannten Schlusskurs ersetzt und im Log genannt; "
               "die 80-%%-Wache bleibt und zaehlt danach. (3) LESEPFAD "
               "`aktuelles_kapital()`: frisch bis 3 Tage, alt bis 14 (wird "
               "verwendet und genannt), darueber NICHT verwendbar - dann "
               "keine Hebelrechnung, der Trade wird Spot, mit Satz in "
               "Klartext; nie ein stiller Vorgabewert (P-2). (4) "
               "UEBERWACHUNG: Quelle `kapital` (Rolle K) in "
               "`datenfrische`, Grenze 3 Tage. Zwoelf Pruefungen im neuen "
               "Paket ,Kapital', alle durch die echten Funktionen", "gilt",
               "agent/portfolio_historie.py · agent/datenfrische.py · "
               "pruefe_pakete --paket Kapital"),
    Befundlage("2.376-nb", "✔✔ GEGEN DIE NB-SICHERUNG (Kopie) NACHGEWIESEN: "
               "vorher ,Kapital 9.942 EUR - Stand 01.09., 10 Tage alt, 6 von "
               "32 Werten ohne Kurs'. Nachgerechnet 02.09. bis 10.09.: JEDER "
               "Tag geschrieben, Abdeckung 100 %%, 0 ohne Kurs; "
               "fortgeschrieben wurden nur Boersentitel (am Wochenende 12, "
               "werktags 5 bis 9, hoechstens 3 Tage). Kapital am 10.09.: "
               "18.212,70 EUR ohne Cash. Der Index lief ohne Sprung weiter "
               "(01.09. 95,578 -> 02.09. 95,431), obwohl der Wert von 9.942 "
               "auf 17.610 EUR stieg - 2.375-index ist damit am echten "
               "Bestand bestaetigt. ✔ GEGENPRUEFUNG: unabhaengig per SQL "
               "nachgerechnet (juengster EUR-Kurs, sonst USD x EUR/USD des "
               "Stichtags, EURCV = 1): 18.212,22 gegen 18.212,70 EUR - 0,48 "
               "EUR (0,003 %%) Abweichung, in keiner Rechnung fehlt ein "
               "Posten. Die Ursache ist NICHT einzeln aufgeschluesselt; "
               "vermutet wird der Wechselkurs bei fortgeschriebenen "
               "USD-Kursen (Kette: Kurstag, Nachrechnung: Stichtag)", "gilt",
               "pruefe_kapital_nb.py (Scratchpad) · NB-Sicherung 11.09."),
    Befundlage("2.376-korrektur", "⚠️ ZWEI MEINER AUSSAGEN IN 2.375 WAREN "
               "FALSCH - die Diagnose je Tag hat sie widerlegt: EURCV hat "
               "nicht ,keinen Kurs', es ist ein Cash-Aequivalent und zaehlt "
               "mit 1,00 EUR; KAIA, SUPRA und BRETT haben EUR-Kurse aus "
               "`price_history`, nicht nur USD. Ich hatte nur "
               "`price_history_ohlc` abgefragt - die Tabelle, die "
               "`_eur_kurse_je_symbol` ausdruecklich als EINE von ZWEI "
               "Quellen fuehrt. Die echten Luecken waren ausschliesslich "
               "BOERSENTITEL (Wochenende, ein bis drei Tage Nachlauf). Die "
               "vorgeschlagene USD-Umrechnung war deshalb unnoetig und ist "
               "nicht gebaut", "gilt",
               "Diagnose 11.09. · agent/portfolio_historie._eur_kurse_je_symbol"),
    Befundlage("2.376-rollout", "⚠️ FUER DEN ROLLOUT: am Notebook fehlen "
               "Zeilen 02.09. bis zum Rollout. Der Job schreibt danach nur "
               "den Vortag - das Kapital ist damit ab dem ersten Morgen "
               "frisch, die LUECKE im Verlauf bleibt aber. Einmal "
               "nachrechnen mit `schreibe_tageswert(datum=...)` je Tag, "
               "sonst meldet die Frischepruefung am Rollout-Tag ,kapital: "
               "abruf', bis der erste Lauf geschrieben hat", "gilt",
               "Rollout-Checkliste"),
    Befundlage("2.376-log", "⚠️ UND EIN LOGFEHLER: an verworfenen Tagen "
               "formatierte `portfolio_wert_job` `%%.2f` auf None - ein "
               ",Logging error' statt einer Aussage. Die Zeile steht jetzt "
               "nur, wenn geschrieben wurde, und nennt die Zahl der "
               "fortgeschriebenen Kurse", "gilt",
               "scheduler/background.portfolio_wert_job"),
    Befundlage("2.375", "⚠️⚠️⚠️ H-1 VOR DEM BAU: DAS KAPITAL IST NICHT "
               "VERWENDBAR, WIE ES HEUTE GESCHRIEBEN WIRD - zwei Befunde "
               "am Notebook (Sicherung 11.09.). (1) ES FEHLT DAS GESTAKTE: "
               "`schreibe_tageswert` zaehlt nur `quantity > 0`, nicht "
               "`staked_quantity`. Neun Werte liegen NUR gestaked (SOL, TAO, "
               "SUI, NEAR, AVAX, HYPE, SEI, BNB, VSN), ETH zu 97 %%. Rund "
               "6.093 EUR fehlen - bei 9.942 EUR ausgewiesenem Wert rund 38 %% "
               "des Kapitals ohne Cash. Das ist P-3 (offene "
               "Nutzerentscheidung seit 10.09.). (2) ES WIRD SELTEN "
               "GESCHRIEBEN: juengste Zeile 01.09., davor 26.08. und 20.08. "
               "Der Job LAEUFT (`job_laeufe` 11.09.), verwirft aber die "
               "meisten Tage an der Abdeckungswache (80 %%): im Log 62 %% und "
               "75 %%. Ursachen: ETF/ETC ohne Wochenendkurs (CEBS, DBPK, "
               "EXH3, VVMX, ISOC), Werte nur mit USD-Reihe (KAIA, SUPRA, "
               "BRETT, VST), vier Rohstoff-ETC mit USD-Reihe bis 07.09., "
               "EURCV (Stablecoin) ohne Kurs seit 07.08.", "gilt",
               "NB-Sicherung 11.09. · NB-Log 31.08./01.09./02.09. · "
               "agent/portfolio_historie.schreibe_tageswert"),
    Befundlage("2.375-index", "✔ WARUM DIE REPARATUR VON P-3 DEN INDEX NICHT "
               "SPRINGEN LAESST - und P-3 damit kleiner ist, als seine "
               "Begruendung sagt. `index_wert` wird MENGENKONSTANT aus den "
               "Mengen des VORTAGS gerechnet (`mengen_json` der Vorzeile, "
               "beide Kurse gegen dieselbe Menge). Kommt das Gestakte hinzu, "
               "rechnet der erste Tag noch mit der alten Menge, jeder "
               "weitere mit der neuen - der Index bekommt keinen Sprung, "
               "Z-3 (Drawdown) ist nicht betroffen. Springen wuerde nur "
               "`wert_eur`, EINMAL, und genau das ist die Korrektur", "gilt",
               "agent/portfolio_historie.schreibe_tageswert Z. 1025-1035"),
    Befundlage("2.375-notify", "⚠️ UND EIN FEHLER IM FEHLERZWEIG: "
               "`portfolio_wert_job` rief `_notify_job_failure` mit EINEM "
               "statt zwei Argumenten - der Aufruf warf selbst einen "
               "TypeError, die Meldung kam nie an. Behoben, mit "
               "Dauerpruefung ueber ALLE Aufrufe", "gilt",
               "scheduler/background.portfolio_wert_job"),
    Befundlage("2.374", "⚠️⚠️⚠️ NUTZERENTSCHEIDUNG 11.09. - PAKET B, UND "
               "WARUM DER FRUEHERE PLAN FALSCH WAR. Nutzer: ,meine "
               "Prioritaet liegt bei 1 Hebel 2 Spot 3 Akkumulation - "
               "zumindest Hebel und Spot muessen sauber funktionieren' und "
               ",ja Paket B, Deckel 5x, Rest wie empfohlen'. Mein Plan "
               "stellte den Rollout VOR Hebel und Akkumulation, obwohl die "
               "Vorgabe KRYPTO-ZUERST Krypto GESAMT meint und beide Luecken "
               "dokumentiert waren (2.174-ist seit 08.09.: ,die "
               "Nutzervorgabe ist damit NICHT umgesetzt'; null Beitraege "
               "der Akkumulation) - sie waren nur nicht als Showstopper "
               "benannt. PAKET B: Akkumulation gesperrt, Portfoliowert, "
               "r(q), Hebelverteilung simulieren, Positionsfuehrung Hebel, "
               "Aggregat-Deckel 3 %%, Spot sauber, E2E, Rollout. PAKET 2: "
               "Akkumulation messen und bauen. Schaetzung rund 7 und 4-5 "
               "Arbeitstage, plus/minus 50 %%", "gilt",
               "Nutzerentscheidung 11.09.2026 · soll_ist Vorgabe PAKET-B"),
    Befundlage("2.374-rq", "⚠️⚠️ MEINE EMPFEHLUNG ,r(q) als EINE Regel fuer "
               "Spot und Hebel' (11.09.) WAR FALSCH und ist zurueckgezogen. "
               "Sie widerspricht der dokumentierten Entscheidung N-38 vom "
               "05.09.: ,Damit trifft der Umbau genau die Hebelseite. Spot "
               "bleibt unberuehrt, ohne dass zwei Regeln gebaut werden "
               "muessen.' Gefunden erst durch die Recherche auf "
               "Nutzerhinweis (,mir fehlt die Info zur Entscheidung'). Der "
               "Zirkelbezug aus `config.yaml` (ein Verlustanteil fuer "
               "beide) loest sich ueber die Reihenfolge: zuerst die "
               "Hebelrechnung, unter 2x Spot mit unveraendertem Betrag",
               "gilt", "Anforderungen_Umbau_28_08.md N-38 (Z. 2776, "
               "2900-2926) · Recherche 11.09."),
    Befundlage("2.374-akku", "⚠️⚠️ DIE AKKUMULATION IST GESPERRT (Paket B) - "
               "und das kehrt einen GEWOLLTEN Zustand um. Die Pruefung "
               ",Kette je Strategie' hielt seit 07.09. ,AKKUMULATION: sie "
               "WINKT DURCH, sie sperrt nicht' als Absicht fest, begruendet "
               "mit Regel 4. Die Folge (2.370): ueber einen Nachkauf "
               "entschied allein das Sprachmodell der Rolle Haendler "
               "(Gemini Flash-Lite, Ausweich OpenRouter und Groq). Seit "
               "11.09.: `Potential.lage_gesperrt`, geprueft VOR der Notiz "
               ",nicht vermessen', mit Grund im Trichter; der Einstieg ist "
               "unberuehrt; drei neue Pruefungen", "gilt",
               "agent/potential.py · agent/rollen_lauf.py · pruefe_pakete "
               "Kette je Strategie"),
    Befundlage("2.374-messen", "✔ EXPERTENURTEIL ZUR NUTZERFRAGE ,alle "
               "Messungen fuer Krypto vor dem Umbau?' (11.09.): NEIN, "
               "gezielt. ,Messen vor Bauen' gilt fuer "
               "BEWERTUNGSBEITRAEGE - deshalb ist das Messpaket Schritt 1 "
               "von Paket 2. `r(q)` ist KEIN neuer Beitrag, es verteilt "
               "Risiko auf den registrierten Beitraegen. Die fehlende "
               "Hebelmessung (steigt die reale Trefferquote mit dem "
               "Hebel?) haengt an A1, dauert Wochen und aendert nicht, WAS "
               "Paket B baut; bis dahin begrenzen die Klammer 0,50-1,25 %% "
               "und die 5x-Grenze. ERGAENZT: vor dem Scharfschalten die "
               "Hebelverteilung simulieren (Schritt H-3, Nutzervorgabe "
               "28.08.: ,vorher pruefen und simulieren')", "gilt",
               "Expertenurteil 11.09.2026"),
    Befundlage("2.373", "⚠️ SICHTUNG DER LETZTEN TAGE (Nutzerauftrag "
               "11.09.). Verifiziert und behoben: 2.367 und 2.368. "
               "Verifiziert offen: die Rollout-Checkliste nennt noch 2048 "
               "Pruefungen und drei Rote (heute 2084 und vier); der alte "
               "Marktscan ist in der `config.yaml` des Desktops aktiv "
               "(2.369). GEMELDET, noch einzeln zu pruefen: `config.yaml` "
               "wird am Notebook ueber die GUI geaendert - vor dem Pull "
               "abgleichen · K-6/K-7 fehlen in Schritt 29 · die O-Liste vom "
               "05.09. (O1 Cooldown, O3 Mindeststop, O6, O7) steht nicht im "
               "Plan · L4 Short, D-2 CANTON, V3/V4/V6/V10/N17 ohne Schritt · "
               "A7 (das Kalibrierwerkzeug kennt nur funding und turnover) · "
               "`messdaten.db` fehlt am Notebook, `schnitt` liest daraus",
               "gilt", "Sichtung 11.09. (Protokoll, soll_ist, Gesamtplan, "
               "Register)"),
    Befundlage("2.372", "⚠️⚠️ DIE ONDO-MAIL, GEGLIEDERT, ZEIGT FUENF "
               "DOPPELUNGEN (Nutzerhinweis 11.09.: ,der Text erschlaegt "
               "einen'): (1) dieselbe Kursmarke dreimal, in zwei Einheiten; "
               "(2) ZWEI Trefferquoten - 34,6 %% (die Bewertung, nach der "
               "entschieden wird) und 34 -> 32 von 100 (die aeltere "
               "Erfahrungsrate in EINORDNUNG), dazu zweimal ,noetig' "
               "(41,7 %% und 42); (3) die Gebuehren dreimal; (4) drei "
               "Rangangaben (1 von 3, 12 von 41, Platz 2/3/3); (5) "
               "Liquidationsabstaende in einer Spot-Mail mit Hebel 1,0. "
               "Vorschlag: Kopf ,Auf einen Blick' und ,Was dagegen "
               "spricht', sechs Abschnitte, Anhang - nichts gestrichen",
               "gilt", "krypto_spot_ONDO.txt · Mailgliederung_Vorschlag_ONDO"),
    Befundlage("2.371", "⚠️⚠️ HEBEL IST KEINE EIGENE LAGE, SONDERN EIN "
               "ERGEBNIS DER RECHNUNG - und end-to-end nie nachgewiesen. "
               "Krypto laeuft nur als `spot` (`INSTRUMENTE_JE_GRUPPE`); ein "
               "Hebelgeschaeft entsteht, wenn Risikobudget und Stopabstand "
               "einen Faktor ueber 1,0 ergeben, gedeckelt durch "
               "Liquidationsabstand und Hoechsthebel. Die HOEHE kommt aus "
               "der Geometrie, NICHT aus der Bewertung (A9/A1/P-1 offen). "
               "⚠️ In keiner Simulation von Schritt 15 entstand ein Signal "
               "mit Faktor ueber 1,0 - Mail und Signalzeile eines "
               "Hebelgeschaefts sind nicht nachgewiesen. ⚠️ Am Notebook "
               "(alter Code): `hebel_signals` endet am 10.08.; seit dem "
               "14.08. traegt KEIN Signal instrument ,hebel', aber 974 "
               "Rollen-Signale haben einen Faktor 1,1 bis 10,0 und stehen "
               "als ,spot' (971) oder ohne Instrument (3)", "gilt",
               "agent/assetklassen.py · entscheidungsrechnung · "
               "NB-Sicherung 11.09."),
    Befundlage("2.370", "⚠️⚠️⚠️ DIE AKKUMULATION LAEUFT HEUTE OHNE "
               "BEWERTUNG DURCH - am Verhalten geprueft: "
               "`potential.rechne(strategie=,akkumulation')` liefert "
               "vermessen=False und getragen_von=0. Stufe 11 ZAEHLT dann "
               "nur und sperrt nicht (Regel 4: nicht nach Datenlage "
               "sperren). Folge nach dem Rollout: jede Akkumulationszelle "
               "(am Notebook BTC, nach dem GUI-Schalter auch ETH und SOL) "
               "entscheidet allein das Modellurteil. ⚠️ Am Notebook gab es "
               "bisher KEIN Signal mit Strategie akkumulation, und "
               "`dca_erlaubt` steht dort NUR fuer BTC (am Desktop BTC und "
               "ETH). Der Zustand ist also neu, nicht alt", "gilt",
               "agent/potential.py · rollen_lauf Stufe 11 · NB-Sicherung "
               "11.09."),
    Befundlage("2.369-fg", "⚠️ ,DER FEAR & GREED MIT DER BESTEN "
               "AUSSAGEKRAFT' IST EINE MESSFRAGE, KEINE AUSWAHL NACH "
               "BESCHREIBUNG. Kandidaten: alternative.me - NUR Bitcoin, zur "
               "Haelfte Kursdaten, Historie ab 01.02.2018 (bei uns "
               "geladen); CoinMarketCap - zehn groesste Werte ohne "
               "Stablecoins, dazu implizite Volatilitaet BTC/ETH, "
               "Put/Call-Verhaeltnis, Stablecoin-Verhaeltnis und Suchdaten, "
               "ohne Schluessel abrufbar, Historie erst ab 20.07.2023 (rund "
               "3,1 Jahre - knapp UNTER der Blockregel 20 x 60 Tage). ⚠️ Der "
               "Nutzen haengt daran, was ein Index NEBEN unseren Beitraegen "
               "weiss: Momentum und Schwankung decken Trichter und Auswahl "
               "ab, Finanzierung und OI sind eigene Beitraege - neu waeren "
               "bei CMC nur Optionsmarkt und Stablecoin-Verhaeltnis. "
               "Gehoert in R-1/R-3", "gilt",
               "alternative.me · CMC public-api v3/fear-and-greed/historical "
               "(abgefragt 11.09.)"),
    Befundlage("2.369", "✔ WOHER DAS REGIME KOMMT UND WO ES WIRKT - aus dem "
               "Code gelesen (Nutzerfrage 11.09.). QUELLE: "
               "`regime.determine_regime`, gerufen NUR im alten "
               "`marktscan_job` (04:00 und 16:00): BTC gegen EMA20/50/200, "
               "30-Tage-Aenderung, Fear & Greed von alternative.me, dazu "
               "Liquiditaets-Regime und Zyklus-Risiko. WIRKUNG: nur im "
               "ALTEN Marktscan (Kontext-Score, Gewichtsprofil je Regime, "
               "Small-Cap-Budget) und als Anzeige (Uebersichtsseite, "
               "GUI-Tab). In der ROLLENKETTE: KEINE - nicht in der "
               "Bewertung, seit 16.08. nicht im Faktensatz, nicht in der "
               "Signalzeile (2.361), nicht in der Mail. Fear & Greed selbst "
               "geht nur als Perzentil ohne Etikett in Rolle A. ⚠️ Der alte "
               "Marktscan ist in der `config.yaml` des Desktops weiter aktiv "
               "und verschickt eigene Mails", "gilt",
               "agent/krypto/regime.py · background.marktscan_job · "
               "config.yaml marktscan.aktiv"),
    Befundlage("2.368", "⚠️⚠️⚠️ S-1 HAETTE AM NOTEBOOK AB DEM ERSTEN LAUF "
               "ALARM GESCHLAGEN - eigener Baufehler, gefunden bei der "
               "Sichtung. Zwei Gruende: (1) am Notebook liegen die drei "
               "Messquellen nur als SYMBOLLISTE ohne Datum "
               "(`baue_messbasis_paket.py`, Tabelle `_nur_symbolliste`) -> "
               ",fehlt'; (2) die Zwei-Tage-Grenze fuer den Abruf galt auch "
               "fuer die von Hand geladene Messbasis -> ,abruf' nach 48 "
               "Stunden; am Desktop standen alle drei tatsaechlich darauf. "
               "Keine Pruefung sah es, weil alle mit `mit_dateien=False` "
               "oder kuenstlichen Urteilen liefen. ➔ Die Symbolliste "
               "bekommt das Urteil ,liste' (nicht auffaellig, leer bleibt "
               "sie ,fehlt'); Rolle M nutzt ihre eigene Obergrenze von 21 "
               "Tagen auch fuer den Abruf; Quellen mit Job bleiben bei zwei "
               "Tagen. Fuenf Pruefungen mit ECHTEN Dateien durch die echte "
               "`pruefe()`. Desktop jetzt: alle drei ,frisch'", "gilt",
               "agent/datenfrische.py · pruefe_pakete.py"),
    Befundlage("2.367", "⚠️⚠️ DER CHART IN DER MAIL HATTE EINEN EIGENEN, "
               "ZWEITEN ZAHLENWEG - Nutzerhinweis 11.09. (,das eMail "
               "generiert auch einen Chart - nicht vergessen und pruefen'). "
               "Die Simulation baute das Bild, legte es aber nie ab; "
               "Schritt 15 hat es damit nicht geprueft. Abgelegt und "
               "angesehen: (1) an allen sechs Marken stand ,0' - "
               "`f'{wert:,.0f}'` bei ONDO 0,32 EUR, derselbe Fehler wie "
               "PLUME am 14.08. im Mailtext; (2) die Preisachse schrieb "
               "englisch ,0.38'. Beide behoben (`trade_chart.marke_text` "
               "ueber `signal_mail.preis`, `achse` mit Tausenderpunkt und "
               "ohne Exponentenschreibweise), drei Dauerpruefungen. "
               "Nachweis im neu abgelegten Bild: ,0,3372 5x', Achse ,0,38'",
               "gilt", "ui/trade_chart.py · simuliere_kette.py"),
    Befundlage("2.366", "✔✔✔ DIE HEUTIGEN MAILAENDERUNGEN SIND IN EINER "
               "FERTIGEN KRYPTO-MAIL NACHGEWIESEN - nicht nur in Pruefungen. "
               "ONDO, gegen die NB-Sicherung, abgelegt unter "
               "%%TEMP%%/simuliere_kette_mails: ,Ausgangspunkt: Ziel "
               "2,0-mal so weit wie der Stop' · ,+ Funding-Rang im Markt "
               "+1,3 %%' · ,✖  Standard 0,30 %%: ... 0,4 Prozentpunkte ZU "
               "WENIG (-0,011 R je Trade = −1,08 EUR)' · die "
               "Bewertungsschwelle · der Vorfilter · die Lebendigkeit. Die "
               "englischen Dezimalzahlen aus 2.363 sind in Krypto- UND "
               "Rohstoff-Mail verschwunden. ⚠️ Nicht nachweisbar in einem "
               "normalen Lauf: die S-2-Ausfallzeile (sie erscheint nur bei "
               "einem echten Abrufausfall) - dafuer stehen fuenf "
               "Dauerpruefungen", "gilt",
               "simuliere_kette.py · krypto_spot_ONDO.txt",
               basis="NB-Sicherung 11.09. 04:48; Werte RENDER/ONDO/KAITO"),
    Befundlage("2.366-minus", "⚠️ UND EIN SCHOENHEITSFEHLER, DEN ICH AM "
               "11.09. SELBST EINGEBAUT HATTE und erst in der fertigen Mail "
               "sah: ,(-0,011 R je Trade = −1,08 EUR)' - Bindestrich und "
               "typografisches Minus in EINER Klammer. `_in_eur` schreibt "
               "jetzt mit `de(..., vorzeichen=True)` wie die R-Zahl davor. "
               "⚠️ Kein Pruefpaket haette das gefunden - genau dafuer gilt "
               "der Grundsatz, dass eine Stufe erst IN DER FERTIGEN MAIL als "
               "gebaut gilt", "gilt", "agent/wahrscheinlichkeit._in_eur"),
    Befundlage("2.362", "✔✔ SCHRITT 15 - DIE KETTE REISST NICHT, auf dem "
               "Datenstand des NOTEBOOKS: `simuliere_kette.py` lief gegen "
               "eine Kopie der NB-Sicherung vom 11.09. 04:48 - also genau "
               "gegen das alte Schema, auf das der Rollout trifft. Alle "
               "fuenf Gruppen durchlaufen, 0 Fehler. Nachgewiesen: der "
               "Zellen-Pfad (BTC mit zwei Zellen), Schritt 7 "
               "(Positionsfuehrung in der Mail), der Vorfilter-Schatten. "
               "Und im gezielten Lauf die erste KRYPTO-Mail end-to-end "
               "(ONDO: Trichter vollstaendig, heraus 1)", "gilt",
               "simuliere_kette.py gegen NB-Sicherung 2026-09-11",
               basis="NB-Sicherung 11.09. 04:48, Kopie im Temp-Verzeichnis"),
    Befundlage("2.362-krypto", "⚠️ WARUM DER ERSTE LAUF KEINE KRYPTO-MAIL "
               "LIEFERTE - und alle Verwerfungen waren richtig: (1) die "
               "Simulation nahm die ersten fuenf Werte mit Kursreihe; der "
               "einzige Ueberlebende hatte Potential −0,016 R gegen die "
               "Schwelle 0,023 R seiner Datenlage. (2) Mit live tragenden "
               "Werten (BNB, SEI) verwarf die Kette KAUFEN, weil beide im "
               "Bestand sind und die Positionsfuehrung SCHLIESSEN sagt. "
               "(3) Die Attrappe gibt die Aktionen REIHUM aus - eine "
               "Einstiegsmail entsteht nur, wenn KAUFEN auf einen Wert ohne "
               "Bestand faellt. ➔ Mit RENDER/ONDO/KAITO (ohne Bestand, live "
               "ueber der Schwelle) kam sie", "gilt",
               "gate_durchlaessigkeit der Simulationskopie"),
    Befundlage("2.363", "⚠️⚠️ ECHTER MAILFEHLER, VON DER SIMULATION "
               "GEFUNDEN: `agent/auswahl.py` formatierte an ZWEI Stellen mit "
               "`:.1f` - in einer echten Rohstoff-Mail ,Der "
               "Rohstoff-Referenzkontrakt steht 11.5 %% ueber seinem "
               "eigenen Schnitt', in der Krypto-Mail ,2.7 Prozentpunkte' "
               "und ,11.9 %%'. Die zweite Stelle traf JEDE gewaehlte Mail. "
               "➔ Beide auf `schreibweise.de()`; dazu die Sperrbegruendung "
               "in `entscheidungsrechnung.py`, die im Trichter steht. "
               "Dauerpruefung im Paket Mail - am Verhalten, nicht am "
               "Quelltext", "gilt", "agent/auswahl.py / pruefe_pakete.py"),
    Befundlage("2.364", "⚠️⚠️ DREI FEHLER IM WERKZEUG SELBST: (1) der "
               "Trichter wurde auf 16 Zeilen GEKAPPT - bei vielen "
               "Begruendungszeilen fielen die letzten Stufen und ,heraus' "
               "aus der Anzeige, und es sah aus wie ein stiller Verlust in "
               "der Kette. (2) Die Zahlschreibweise-Luecke nannte nur die "
               "Zahl, nicht die ZEILE - und weil der Mailtext nirgends "
               "gespeichert wurde, war sie nicht auffindbar. (3) Der "
               "Mailtext wurde nur im Speicher geprueft; ob eine Zeile "
               "WIRKLICH in der Mail steht, war nachher nicht nachsehbar. "
               "Alle drei behoben; fertige Mails liegen jetzt unter "
               "%%TEMP%%/simuliere_kette_mails. Dazu ein irrefuehrender "
               "Hinweis: `--symbole` umgeht die Vorauswahl der SIMULATION, "
               "nicht die Stufe ,beste k' der Kette", "gilt",
               "simuliere_kette.py"),
    Befundlage("2.365", "⚠️ ZWEI EIGENE FEHLER BEIM AUSWERTEN, beide selbst "
               "gefunden: (1) ich meldete einen stillen Verlust in der "
               "Krypto-Kette - es war die 16-Zeilen-Kappung der Anzeige. "
               "(2) Ich meldete einen Widerspruch ,Kette haelt BNB und SEI "
               "fuer Bestand, das NB haelt sie nicht' - meine Abfrage "
               "pruefte nur `quantity > 0` und uebersah `staked_quantity` "
               "(SEI 2.711, BNB 0,159). `rollen_eingabe.bestand()` zaehlt "
               "Gestaktes seit dem 17.08. zu Recht mit. Die Kette hatte "
               "recht. ⚠️ Derselbe Fehler steckt vermutlich in meiner "
               "Zaehlung ,29 Bestaende' aus 2.346", "gilt",
               "Selbstbefund 11.09.2026"),
    Befundlage("2.361", "⚠️⚠️⚠️ DIE ROLLENKETTE SCHREIBT DAS REGIME NICHT "
               "MIT: seit dem 14.08. tragen am Notebook 3.872 von 3.883 "
               "Signalen `regime = None`, `regime_source` ebenfalls leer. "
               "Davor (07.07. bis 14.08., alte Kette) trugen 2.549 Signale "
               "ausnahmslos ,baer'. Es gab damit NIE ein zweites Label in "
               "den Betriebsdaten - erst gar keines. ⚠️ Jeder Tag nach dem "
               "Rollout ohne diese Spalte fehlt spaeter fuer eine Trennung "
               "am echten Betrieb", "gilt",
               "NB-Sicherung 2026-09-11 · signals.regime",
               basis="Notebook-Sicherung, ALTER Codestand; "
                     "am Desktop-Code ebenfalls kein Schreiber gefunden"),
    Befundlage("2.361-verstaendnis", "✔ DAS NUTZERVERSTAENDNIS IST "
               "BESTAETIGT, und praezisiert: *,Regime konnte fuer unsere "
               "Bewertungsgrundlagen bisher kaum sinnvoll genutzt werden.'* "
               "Der Grund ist nicht, dass Regime unwichtig waere, sondern "
               "dass es NIE ein brauchbares Regimesignal gab, gegen das man "
               "haette messen koennen. **Nicht gemessen ist nicht "
               "unwirksam** - dieselbe Klasse wie ,nicht trennbar' gegen "
               ",traegt nicht'. Deshalb Sonderpunkt mit fuenf "
               "Arbeitspaketen (R-1 bis R-5), nicht Abschluss", "gilt",
               "Nutzerhinweis 11.09. / Gesamtplan Sonderpunkt Regime"),
    Befundlage("2.360", "✔✔✔ S-3 IST GEBAUT - jeder Job hinterlaesst "
               "eine Spur. Von 21 geplanten fuehrten nur SECHS eine Zeile "
               "in `job_laeufe`, und die sechs nicht aus "
               "Ueberwachungsgruenden: `merke_joblauf` wurde fuer den "
               "NACHHOLER gebaut, und nur Jobs mit Nachholbedarf riefen "
               "sie. Fuer `refresh_prices`, `refresh_history`, "
               "`marktscan`, `hebel_screening` und elf weitere war nach "
               "einem Ausfall NICHT feststellbar, wann sie zuletzt "
               "liefen - also auch nicht, was gefehlt hat", "gilt",
               "scheduler/background._log_job_event"),
    Befundlage("2.360-zentral", "✔✔ ZENTRAL STATT FUENFZEHN KOPIEN: der "
               "Ereignis-Horcher lauscht jetzt zusaetzlich auf "
               "EVENT_JOB_EXECUTED - vorher nur auf ERROR und MISSED, "
               "also blieb ein Job, der SAUBER lief, unsichtbar. "
               "⚠️ Fuenfzehn Einzelaufrufe von Hand einzustreuen hiesse, "
               "beim naechsten neuen Job einen zu vergessen - und genau "
               "der waere dann der unsichtbare. Der Horcher sieht jeden "
               "Lauf, auch kuenftige. Das Projekt kennt die Lehre: *drei "
               "Kopien laufen garantiert auseinander*", "gilt",
               "scheduler/background.py"),
    Befundlage("2.360-gegenprobe", "✔✔ VIER VERHALTEN GEGENGEPRUEFT: ein "
               "ERFOLGREICHER Lauf wird vermerkt · ein FEHLGESCHLAGENER "
               "NICHT (er ist nicht gelaufen - ihn zu vermerken hiesse, "
               "einen Ausfall als Erfolg zu buchen), die Fehlermeldung "
               "geht trotzdem raus · OHNE Verbindung stolpert der Horcher "
               "nicht (ein Listener, der wirft, stoert den Scheduler bei "
               "JEDEM Job) · und er ist auf EVENT_JOB_EXECUTED "
               "registriert. ⚠️ Die Gegenprobe wird ROT, sobald man den "
               "Zweig abschaltet", "gilt", "pruefe_pakete.py"),
    Befundlage("2.360-verhalten", "⚠️ UND DIESMAL PRUEFT DIE PRUEFUNG DAS "
               "VERHALTEN, NICHT DEN QUELLTEXT - die Lehre von S-1 vom "
               "selben Tag: dort blieb eine Pruefung gruen, die nur nach "
               "einem Funktionsnamen im Text suchte; der Aufruf stand "
               "noch da und wurde nur nie erreicht. Hier wird der Horcher "
               "mit echten Ereignissen gerufen. ⚠️ Die vierte Pruefung "
               "(Registrierung) bleibt eine Textpruefung - und zwar "
               "bewusst: die drei darueber rufen die Funktion DIREKT und "
               "wuerden auch dann gruen bleiben, wenn niemand sie je "
               "anschliesst", "gilt", "Selbstbefund 11.09.2026"),
    Befundlage("2.358", "✔✔✔ S-1 IST GEBAUT - die drei MESSQUELLEN "
               "sind ueberwacht. `funding_historie`, "
               "`terminmarkt_historie` und `onchain_historie` standen in "
               "KEINER Registratur - also auch nicht in der "
               "Frischepruefung, die es seit dem 17.08. gibt. Jetzt in "
               "`datenfrische.REGISTRATUR` mit eigener ROLLE ,M'. Am "
               "Desktop melden sie sofort: funding 11 Tage, terminmarkt 7, "
               "onchain 12 - Urteil ,abruf', also **unser** Fehler, nicht "
               "der des Anbieters", "gilt", "agent/datenfrische.py"),
    Befundlage("2.358-rolle", "✔ DIE ROLLE ,M' IST DIE WICHTIGE "
               "UNTERSCHEIDUNG: A, BC und G speisen PROMPTS - faellt dort "
               "etwas aus, urteilt das Modell auf altem Stand. M speist "
               "die MESSBASIS, also die Symbolliste, gegen die gerangt "
               "wird; die laufenden WERTE kommen aus Live-Abrufen. Ein "
               "Ausfall dort blockiert KEINE Signale, macht aber jede "
               "Neumessung und Kalibrierung auf altem Stand. "
               "⚠️ Nutzervorgabe 10.09.: *,Aenderungen duerfen die "
               "Bewertung nicht blockieren - und schon gar nicht still.'* "
               "Blockieren tut hier nichts; das Schweigen faellt weg",
               "gilt", "agent/datenfrische.py"),
    Befundlage("2.358-handlung", "✔✔ UND DER HANDLUNGSBEDARF WIRD "
               "GEMELDET, nicht nur geloggt. Nutzervorgabe 11.09.: *,bei "
               "Totalausfall besteht Handlungsbedarf - wenn eine ganze "
               "Datenquelle oder Bereich ausfaellt sollte nach kritischen "
               "Meldungen klar sein dass etwas zu tun ist.'* "
               "`_melde_datenfrische` schrieb bis heute NUR ins Log. "
               "⚠️ Eskaliert wird NUR bei ,fehlt' und ,abruf', nicht bei "
               ",daten' - der Kopf von `datenfrische` sagt warum: *,Ein "
               "Anbieter, der nichts Neues hat, ist normal. Ein Job, der "
               "nicht laeuft, ist es nie.'* Wer auch ,daten' meldet, "
               "meldet bald nichts mehr", "gilt",
               "scheduler/background._melde_datenfrische"),
    Befundlage("2.358-gruppiert", "⚠️ UND DIE MELDUNG IST NACH JOB "
               "GRUPPIERT, nicht je Quelle: die erste Fassung schrieb 18 "
               "Zeilen, und ACHT davon hatten dieselbe Ursache "
               "(`externe_reihen` laeuft nicht). **Eine Textwand macht "
               "keinen Handlungsbedarf klar, sie verdeckt ihn.** Der JOB "
               "ist die Handlungseinheit - wer liest, will wissen, was er "
               "anfassen muss. Dasselbe Prinzip wie "
               "`signal_mail.ohne_gewohntes`", "gilt",
               "scheduler/background.py"),
    Befundlage("2.359", "⚠️⚠️ ZWEI EIGENE FEHLER BEIM BAUEN, BEIDE VON "
               "DER GEGENPROBE GEFANGEN: (1) meine Pruefung suchte "
               "`_notify_job_failure(` im QUELLTEXT - schaltet man die "
               "Eskalation ab, steht der Aufruf noch da und wird nur nie "
               "erreicht. Sie blieb GRUEN. **Derselbe Fehlertyp wie am "
               "selben Tag beim Bitgleichheitstest: eine Pruefung, die "
               "einen Pfad nicht laeuft, sagt ueber ihn nichts.** Jetzt "
               "wird die Funktion mit vier kuenstlichen Lagen gerufen. "
               "(2) meine Dateiquellen lesen FESTE Pfade unter `data/` "
               "und damit an `conn` vorbei - vier bestehende Pruefungen "
               "mit kuenstlicher Datenbank kippten. `mit_dateien=False` "
               "ist die ehrliche Zwischenloesung, nicht die schoene",
               "gilt", "Selbstbefund 11.09.2026"),
    Befundlage("2.359-abruf", "⚠️ UND EINE OFFENE UNGENAUIGKEIT, benannt "
               "statt verschwiegen: keine der drei Messquellen fuehrt "
               "eine `fetched_at`-Spalte. Der ABRUFSTAND - nach dem Kopf "
               "des Moduls *,der eigentliche Gesundheitswert'* - kommt "
               "deshalb aus der AENDERUNGSZEIT der Datei. Die beweist, "
               "dass ueberhaupt geschrieben wurde, NICHT dass der Abruf "
               "vollstaendig war. Fuer ,laeuft der Job noch?' genuegt "
               "das; fuer ,war er vollstaendig?' nicht. Eine echte "
               "`fetched_at`-Spalte kommt, wenn die drei Jobs bekommen "
               "✔✔✔ GELOEST AM 13.09. (Schritt 50 Teil B, 2.425): der "
               "Abrufstand kommt nicht mehr aus der Dateizeit, sondern aus "
               "`abruf_symbol` - einer Zeile JE SYMBOL, geschrieben nur im "
               "Erfolgszweig. `datenfrische` meldet jetzt ,X von Y "
               "Symbolen`. ⚠️ Und die Sorge des Befundes war berechtigt: "
               "der erste Lauf danach meldete 65 von 66, weil ZRX "
               "voruebergehend ausfiel - die Datei sah frisch aus, ein "
               "Symbol war es nicht",
               "gilt", "agent/datenfrische._stand_datei"),
    Befundlage("2.357", "✔✔✔ S-2 IST GEBAUT - ein Ausfall ist keine "
               "Messbasisluecke mehr. Nutzervorgabe 11.09.: *,die API "
               "Abfragen und Datensammlungen am Notebook muessen stabil "
               "umgesetzt werden, damit ein kurzer Ausfall so wie heute "
               "keinen Schaden anrichten kann.'* Faellt der Abruf aus, war "
               "das Fuenftel None und die Zeile wurde SCHLICHT "
               "WEGGELASSEN - die Mail sah normal aus, nur kuerzer, und "
               "die Bewertung war an dem Tag stumm um einen Beitrag "
               "aermer", "gilt", "agent/marktrang.py"),
    Befundlage("2.357-falsch", "⚠️⚠️ UND BEI TOTALAUSFALL NANNTE DIE MAIL "
               "DIE FALSCHE URSACHE: ,er gehoert weder zur Funding- noch "
               "zur Umschlag- noch zur Terminmarkt-Messbasis' - auch "
               "dann, wenn schlicht das NETZ weg war. **Eine falsche "
               "Begruendung ist schlimmer als keine: sie schickt den "
               "Leser an die falsche Stelle.** Er haette die Messbasis "
               "geprueft, waehrend die Ursache im Abruf lag", "gilt",
               "agent/marktrang.py"),
    Befundlage("2.357-daten", "✔ DIE UNTERSCHEIDUNG STECKTE SCHON IN DEN "
               "DATEN, sie wurde nur nicht ausgewertet: `raenge()` setzt "
               "`querschnitt_<name>` ERST nach erfolgreichem Abruf und "
               "nach der Mindestquerschnittspruefung. Also bedeutet "
               "querschnitt == 0 ,der ganze Rang ist heute ausgefallen' "
               "und querschnitt > 0 mit fehlendem Fuenftel ,dieser Wert "
               "gehoert nicht dazu'. ⚠️ Alle DREI Abbruchstellen in "
               "`raenge()` melden bereits ins Log - keine erreichte die "
               "MAIL. Genau das ist fail-soft-ist-fail-silent", "gilt",
               "agent/marktrang.raenge / Analyse 11.09."),
    Befundlage("2.357-gegenprobe", "✔✔ GEGENGEPRUEFT ueber VIER Faelle, "
               "mit fuenf Dauerpruefungen im Paket Terminmarkt: NORMAL "
               "(keine Ausfallzeile - wo nichts ausgefallen ist, darf "
               "nichts gemeldet werden, sonst stumpft die Meldung ab) · "
               "TEILAUSFALL (wird genannt UND benennt die Groesse) · "
               "MESSBASISLUECKE (bleibt, was sie war - die alte Zeile ist "
               "dort richtig) · TOTALAUSFALL (nennt den Ausfall, NICHT "
               "die Messbasis). ⚠️ Die Gegenprobe wird ROT, sobald man "
               "die Teilausfallzeile abschaltet", "gilt",
               "pruefe_pakete.py Paket Terminmarkt"),
    Befundlage("2.351", "⚠️⚠️⚠️ ANALYSE DER BEWERTUNGSSCHICHT - DER "
               "SCHWERSTE FUND, und er ist REPRODUZIERT: `schwelle()` und "
               "`schwellenzeile()` ermittelten die QUELLE getrennt. Die "
               "eine nahm den Wert, die andere fragte nur, ob der "
               "Schluessel existiert. Bei `potential_schwelle_r: 0,02` - "
               "Komma statt Punkt, in einem deutschsprachigen Projekt die "
               "naheliegendste Verwechslung - liest YAML eine Zeichenkette, "
               "`float()` wirft, der Rueckfall greift: wirksam bleibt "
               "0,080, und die Mail meldet trotzdem ,(config.yaml)'. "
               "**Der Nutzer haette geglaubt, seine Einstellung wirke**",
               "gilt", "agent/potential.py / Analyse 11.09.2026"),
    Befundlage("2.351-warum-schwer", "⚠️⚠️ WARUM DAS SCHWERER WIEGT ALS "
               "EIN GEWOEHNLICHER FEHLER: es trifft genau den Parameter, "
               "zu dem der Nutzer am 07.09. sagte - *,so einen Parameter "
               "vergesse ich in Kuerze und du auch, die Doku reicht bei "
               "so einer zentralen Einstellung nicht.'* Daraufhin "
               "entstanden die Steuerbarkeit ueber `config.yaml` und die "
               "Mailzeile. **Beide Vorkehrungen waren vorhanden - und "
               "genau ihr Zusammenspiel war kaputt.** Die Schwelle "
               "entscheidet ueber die ZAHL der Empfehlungen", "gilt",
               "Nutzerhinweis 07.09. / Analyse 11.09."),
    Befundlage("2.351-ursache", "✔ DIE URSACHE IST DIE ZWEITE ERMITTLUNG, "
               "NICHT DER RUECKFALL. Der Rueckfall ist richtig - ohne ihn "
               "stuende das System bei einem Tippfehler still. Falsch war, "
               "dass niemand davon erfuhr. ➔ `schwelle_und_quelle()` "
               "liefert Wert, Quelle UND Stoerung aus EINEM Vorgang; "
               "`schwelle()` meldet die Stoerung ins Log, "
               "`schwellenzeile()` in die MAIL. Dasselbe Prinzip, das das "
               "Projekt schon kennt: *drei Kopien laufen garantiert "
               "auseinander*", "gilt", "agent/potential.py"),
    Befundlage("2.351-gegenprobe", "✔✔ GEGENGEPRUEFT ueber VIER Faelle, "
               "und der gueltige Weg wirkt weiterhin: `0,02` (Komma) -> "
               "Code-Vorgabe + Hinweis · `zwei` -> Code-Vorgabe + Hinweis · "
               "Schluessel FEHLT -> Code-Vorgabe OHNE Hinweis (das ist der "
               "Normalfall) · `0.02` gueltig -> config.yaml, 0,020 wirkt. "
               "Acht neue Pruefungen im Paket Kalibrierung halten alle "
               "vier fest", "gilt", "pruefe_pakete.py Paket Kalibrierung"),
    Befundlage("2.352", "✔ WAS DIE ANALYSE SONST GEFUNDEN HAT - und es "
               "spricht FUER die Schicht: das Paket Kalibrierung prueft "
               "die Schwelle bereits mit ueber 20 Zeilen (Steuerbarkeit, "
               "Mail, Alter, Stufen, R-R9). Die 13 Module ohne Aufrufer "
               "sind SAMTLICH erklaert - `remote/server` wird in "
               "`main.py:387` in einem Thread gestartet (Fehlalarm der "
               "Modulkarte durch dynamischen Import), `szenario_*` ist als "
               "Kontrollgroesse in der Pruefsuite gefuehrt, der Rest "
               "traegt GESTRICHEN oder ABGELOEST im Kopf", "gilt",
               "zeige_modulkarte.py --tot / Analyse 11.09."),
    Befundlage("2.352-still", "✔ UND DIE STILLEN AUSFAELLE SIND SORTIERT: "
               "von 14 except-Bloecken in der Bewertungsschicht melden "
               "die Betriebspfade, und die stillen liegen auf "
               "SCHATTENpfaden - `auswahl.marktzustand` sagt im eigenen "
               "Docstring *,Schatten, keine Schranke'*, ein stilles None "
               "sperrt dort nichts. Die EINE Ausnahme war die Schwelle "
               "(2.351)", "gilt", "Analyse 11.09.2026"),
    Befundlage("2.353", "⚠️ LESBARE WERTE (Nutzervorgabe 11.09., "
               "woertlich: *,ich sollte im Text immer fuer mich lesbare "
               "und zuordenbare Werte und Textformulierungen erhalten "
               "(kein 2R), EUR Betraege, etc.'*): vier Stellen "
               "richtiggestellt - CRV ausgeschrieben (,Ziel 2,0-mal so "
               "weit wie der Stop'), die Einheit an die Beitragszahl "
               "(+1,3 %%), ,Punkte' -> ,Prozentpunkte', und R bekommt den "
               "Eurobetrag daneben (−0,467 R je Trade = −34,99 EUR). "
               "⚠️ DIE ZAHL IN R BLEIBT - nur sie ist ueber Trades "
               "vergleichbar", "gilt", "agent/wahrscheinlichkeit.py"),
    Befundlage("2.353-eur", "✔ UND DIE UMRECHNUNG HAENGT NICHT AM "
               "KAPUTTEN PORTFOLIOWERT: `R` ist der Betrag, der beim Stop "
               "verloren geht (`betraege.py`: Risiko in Euro = Einsatz x "
               "Verlustanteil). Gebraucht wird nur das Risiko DIESES "
               "Trades, und das steht in derselben `rechnung` wie Stop und "
               "Ziel. Wichtig, weil `portfolio_wert_historie` am Notebook "
               "seit dem 01.09. stillsteht (2.341)", "gilt",
               "agent/betraege.py / agent/rollen_lauf.py"),
    Befundlage("2.354", "⚠️⚠️ EIN ZEICHEN STAND FUER DREI DINGE - und das "
               "IST der Nutzerbefund *,schwer abgrenzbare Hinweise, "
               "Warnungen und ehrliche Luecken'*: ⚠️ markierte die "
               "BEWERTUNG (,kein Beitrag greift hier'), die GEBUEHR "
               "(,deckt nicht'} und einen DAUERVORBEHALT (,keine "
               "Prognose'). ➔ Die Gebuehrenzeile bekommt ✔/✖. "
               "⚠️ NICHT weggelassen: ,deckt die Gebuehr nicht' ist eine "
               "Aussage, kein Schmuck - und Regel 2 verlangt ohnehin, dass "
               "Gebuehren nicht in die BEWERTUNG eingehen; ein "
               "Warnzeichen legt genau das nahe", "gilt",
               "agent/wahrscheinlichkeit.py / Nutzerbefund 11.09."),
    Befundlage("2.355", "✔✔ DIE SPERRE GEGEN DAS BEQUEME NEUAUFZEICHNEN: "
               "die vier Textaenderungen machten 144 von 432 "
               "Bitgleichheitsfaellen rot. Neu aufzeichnen war richtig - "
               "aber das ist ein URTEIL, kein Handgriff, und dieselbe "
               "Geste koennte beim naechsten Mal eine geaenderte ZAHL "
               "mitloeschen. ✔ GEMESSEN: 144 Abweichungen, ALLE unter "
               "Text-Schluesseln, NULL unter Zahlen. ➔ `--aufzeichnen` "
               "verweigert jetzt den Dienst, wenn sich eine ZAHL geaendert "
               "hat, und nennt die Schluessel; `--auch-zahlen` hebt es "
               "auf. Beide Richtungen gegengeprueft", "gilt",
               "pruefe_wahrscheinlichkeit_bitgleich.py"),
    Befundlage("2.356", "⚠️ EIGENE KORREKTUR: ich hatte vorgeschlagen, die "
               "Zeile ,KEIN gemessener Beitrag greift hier' nach oben zu "
               "holen - sie steht bereits an Position 4 von 16, direkt "
               "unter der Trefferquote. Regel 1 des Mailvorschlags war "
               "schon erfuellt. Nachgemessen statt umgebaut", "gilt",
               "Selbstbefund 11.09.2026"),
    Befundlage("2.347", "⚠️⚠️⚠️ EIGENER VERFAHRENSFEHLER, vom Nutzer "
               "gestoppt: ich wollte S-1/S-2/S-3 bauen, ohne "
               "`zeige_modulkarte.py` zu benutzen - obwohl sie GENAU "
               "gegen diesen Fehler gebaut ist und als stehende Vorgabe "
               "im Memory steht (,Vor jeder Ausarbeitung: "
               "zeige_modulkarte.py'). Ihr eigener Docstring zitiert den "
               "Nutzerbefund woertlich: *,das ist ein problem des "
               "projektes dass du immer nur die haelfte der infos bei der "
               "ausarbeitung kennst dann bleibt immer etwas liegen'* - "
               "und listet sechs Beispiele, darunter ,welche sind Kern?' "
               "-> GUI-Schalter nennt BTC/ETH/SOL. **Exakt mein heutiger "
               "Fall.** Der Nutzerhinweis lautete: ,ich wuerde auch einen "
               "code Review und doku empfehlen damit du keine Funktionen "
               "und kritischen Punkte uebersiehst'", "gilt",
               "zeige_modulkarte.py / Nutzerhinweis 11.09.2026"),
    Befundlage("2.348", "✔✔✔ UND DER REVIEW HAT S-1/S-3 DRASTISCH "
               "VERKLEINERT: `agent/datenfrische.py` existiert seit dem "
               "17.08. und ist GENAU das Muster, das gebraucht wird. Es "
               "unterscheidet ZWEI Alter, und die Unterscheidung ist der "
               "ganze Trick: DATENSTAND (juengstes Datum in der Reihe - "
               "haengt am ANBIETER, ein hohes Alter kann richtig sein) "
               "gegen ABRUFSTAND (wann wir zuletzt erfolgreich "
               "nachgesehen haben - haengt an UNS, und ist der eigentliche "
               "Gesundheitswert). *,Ein Anbieter, der nichts Neues hat, "
               "ist normal. Ein Job, der nicht laeuft, ist es nie.'*",
               "gilt", "agent/datenfrische.py"),
    Befundlage("2.348-anlass", "⚠️ UND SEIN ANLASS IST MEIN BEFUND 2.341, "
               "nur einen Monat aelter: am 17.08. stellte sich heraus, "
               "dass DREI Rolle-A-Quellen von einem Skript stammten, das "
               "ein Mensch von Hand gestartet hatte. Der Docstring: *,Ein "
               "fehlender Satz faellt auf; ein alter Satz sieht aus wie "
               "ein frischer. Das ist fail-soft-ist-fail-silent in seiner "
               "unangenehmsten Form: hier faellt nicht einmal etwas aus. "
               "Es steht nur still.'* Genau die Klasse, die ich heute in "
               "`portfolio_wert_historie` gefunden habe", "gilt",
               "agent/datenfrische.py / 2.341"),
    Befundlage("2.349", "⚠️⚠️ DIE LUECKE IST PRAEZISE UND KLEIN: die "
               "Registratur fuehrt 15 Quellen - alle in der BETRIEBS-DB. "
               "Die drei MESSquellen fehlen: `funding_historie.db` (nicht "
               "registriert), `onchain_historie.db`/splycur -> turnover "
               "(nicht registriert), und `terminmarkt_historie.db` - der "
               "Eintrag `terminmarkt` meint eine ANDERE Tabelle "
               "(`open_interest_snapshot` via `hebel_screening`). "
               "➔ S-1/S-3 heisst damit NICHT ,ein Ueberwachungssystem "
               "bauen', sondern ,drei Zeilen in eine vorhandene "
               "Registratur eintragen' - plus eine kleine Erweiterung, "
               "weil `datenfrische` heute nur Tabellen der Betriebs-DB "
               "kennt und die drei EIGENE Dateien sind", "gilt",
               "agent/datenfrische.REGISTRATUR"),
    Befundlage("2.350", "⚠️ UND NOCH EINE UEBERSEHENE FUNKTION, vom "
               "Nutzer genannt (*,wir pruefen auch die Datenquellen und "
               "Abfragen auf der Uebersichtsseite'*): `remote/status.py` "
               "ist eine Statusseite mit rund VIERZIG Aggregatoren, "
               "darunter `_get_api_health`, `_get_coingecko_quota`, "
               "`_get_llm_kontingent` und `is_price_stale`. Sie prueft "
               "Datenquellen und Kontingente bereits. ⚠️ Ich haette S-1 "
               "gebaut, ohne sie zu kennen", "gilt", "remote/status.py"),
    Befundlage("2.340", "⚠️⚠️⚠️ L1 IST GRAVIERENDER ALS ANGENOMMEN - "
               "am NOTEBOOK steht NUR BTC im DCA-Schalter, nicht einmal "
               "ETH. Die Nutzervorgabe nennt BTC, ETH UND SOL. Damit "
               "laufen ZWEI VON DREI Kernwerten produktiv nach "
               "`einstieg`, also MIT Stop und Trailing - statt als "
               "Akkumulation. ⚠️ Die Desktop-Kopie hatte BTC+ETH und "
               "verdeckte damit die Haelfte des Problems", "gilt",
               "NB-Sicherung 2026-09-11 04:48 · asset_dca_settings",
               basis="Notebook-Sicherung, ALTER Codestand"),
    Befundlage("2.341", "⚠️⚠️ EIN STILLER AUSFALL, LIVE BELEGT: der Job "
               "`portfolio_wert` lief am 11.09. um 04:43 - die juengste "
               "Zeile in `portfolio_wert_historie` ist aber vom 01.09. "
               "Er schreibt nur rund alle SECHS Tage (01.09., 26.08., "
               "20.08.). ⚠️ Und genau diese Tabelle liefert nach "
               "Nutzerentscheidung P-5 die BEZUGSGROESSE fuer r x "
               "Kapital", "gilt",
               "NB-Sicherung 2026-09-11 · job_laeufe / "
               "portfolio_wert_historie",
               basis="Notebook-Sicherung, ALTER Codestand"),
    Befundlage("2.341-ursache", "✔ DIE URSACHE IST EINE RICHTIG GEBAUTE "
               "SCHRANKE: `MIN_ABDECKUNG_FUER_TAGESWERT = 0,80` - unter "
               "80 %% Kursabdeckung wird NICHTS geschrieben, mit der "
               "ausdruecklichen Begruendung *,Lieber eine sichtbare "
               "Luecke als ein plausibel aussehender Falschwert.' Die "
               "letzte geschriebene Zeile hatte 6 von 32 Symbolen ohne "
               "Kurs, also 81 %% - knapp darueber. ⚠️⚠️ DIE SCHRANKE IST "
               "RICHTIG, DAS SCHWEIGEN IST DAS PROBLEM: ,sichtbar' ist "
               "die Luecke nur fuer den, der in die Tabelle sieht. Zehn "
               "Tage ohne Bezugsgroesse, und niemand erfaehrt es",
               "gilt", "agent/portfolio_historie.py:147"),
    Befundlage("2.342", "⚠️ NUR SECHS VON 21 JOBS HINTERLASSEN EINE SPUR: "
               "`job_laeufe` fuehrt ausstiegs_empfehlungen, "
               "portfolio_wert, externe_reihen, lagebild_reihen, "
               "backward_tracking und makro_analog. Fuer die uebrigen 15 "
               "- darunter `refresh_prices`, `refresh_history`, "
               "`marktscan`, `hebel_screening` - ist NICHT nachvoll"
               "ziehbar, wann sie zuletzt liefen. Nach einem Ausfall ist "
               "damit nicht feststellbar, was gefehlt hat", "gilt",
               "NB-Sicherung 2026-09-11 · job_laeufe",
               basis="Notebook-Sicherung, ALTER Codestand"),
    Befundlage("2.343", "⚠️ `hebel_signals` STEHT SEIT DEM 10.08. - ein "
               "Monat ohne neue Zeile, bei 1.998 vorhandenen. Ob das ein "
               "Ausfall oder die richtige Folge der Lage ist, ist NICHT "
               "geklaert. ⚠️ Es passt zur Hebelspur: die Lage `hebel` "
               "ist blockiert (A1/A9/P-1), aber ein stilles Versiegen "
               "sieht genauso aus wie ein begruendetes Schweigen. "
               "✔✔ BEANTWORTET AM 13.09.: BEGRUENDETES SCHWEIGEN, KEIN "
               "AUSFALL. `hebel_signals` gehoert der ALTEN Kette; ihr "
               "einziger Schreiber ist `hebel_analyst`, und "
               "`empfehlung_vertrag` sagt dazu woertlich: *,DIE ALTE KETTE "
               "BLEIBT UNBERUEHRT ... sie schreibt in `hebel_signals` und "
               "laeuft fuer Krypto nicht mehr. Ein Eingriff dort waere "
               "Arbeit an einem toten Pfad.`* Nachgezaehlt: KEINE einzige "
               "Aufrufstelle im Projekt - alle Treffer auf `hebel_analyst` "
               "sind Kommentare und Zitate. Die neue Kette schreibt ueber "
               "`signal_abbildung` nach `signals`, und fuer Krypto gilt "
               "`INSTRUMENTE_JE_GRUPPE[krypto] = (spot,)` - der Hebel "
               "entsteht als ETIKETT auf einem Spot-Signal, nicht als "
               "eigenes Instrument. ⚠️⚠️ UND DER EIGENTLICHE EINWAND IST "
               "GEBAUT, nicht nur beantwortet: das Paket `gesamt` fuehrt "
               "jetzt die Zeile *,`hebel_analyst` BLEIBT OHNE AUFRUFER`. "
               "Wird er je wieder verdrahtet, faellt sie, und die Frage "
               "wird bewusst neu gestellt statt still zu bleiben. "
               "✔ Der Waechter ist GEGENGEPRUEFT: mit einem eingesetzten "
               "Testimport meldet das Paket 1 FEHLGESCHLAGEN, ohne ihn 27 "
               "von 27 - eine Kontrolle, die nur gruen sein kann, ist "
               "keine", "gilt", "NB-Sicherung 2026-09-11 · hebel_signals",
               basis="Notebook-Sicherung, ALTER Codestand"),
    Befundlage("2.344", "✔ WAS AM NOTEBOOK LAEUFT: `signals` bis 11.09. "
               "04:48 (6.842 Zeilen) · `price_history` und "
               "`price_history_ohlc` bis 10.09. · `macro_snapshot` und "
               "`externe_reihe` bis 11.09. Der Betrieb laeuft, die "
               "Kursdaten sind frisch. Die Luecken sitzen in den "
               "ABGELEITETEN Groessen, nicht in der Beschaffung",
               "gilt", "NB-Sicherung 2026-09-11",
               basis="Notebook-Sicherung, ALTER Codestand"),
    Befundlage("2.345", "⚠️⚠️ ALLE NB-BEFUNDE STEHEN UNTER EINEM "
               "VORBEHALT, den der Nutzer am 11.09. genannt hat: *,der "
               "Codestand am NB ist sehr alt und wir machen jetzt einen "
               "massiven Umbau.'* Was ich aus der Sicherung lese, ist die "
               "AUSGABE VON ALTEM CODE. ➔ Das entwertet die Befunde "
               "nicht, aber es aendert ihre Folge: **der Rollout ist der "
               "Moment, sie zu beheben** - der Code wird ohnehin ersetzt, "
               "und S-1/S-2 gehoeren in dasselbe Paket", "gilt",
               "Nutzerhinweis 11.09."),
    Befundlage("2.346", "⚠️ EIGENER FEHLGRIFF, sofort bemerkt: ich wollte "
               "die sechs Symbole ohne Kurs benennen und habe Symbol "
               "gegen `coingecko_id` gejoint - die Watchlist steht aber "
               "NICHT in der Datenbank (sie kommt aus `config.yaml` und "
               "`Assets.xlsx`). Das Ergebnis meldete BTC und ETH als "
               ",kein Kurs', was offensichtlich falsch ist. Belastbar ist "
               "allein die Zahl aus der Tabelle selbst: 6 von 32",
               "gilt", "Selbstbefund 11.09.2026"),
    Befundlage("2.331", "⚠️⚠️ V11: `schnitt50` BESTEHT N-73 NICHT - "
               "2 von 3 Beitragsmengen. Er traegt auf 10 %% (+0,0846) und "
               "20 %% (+0,0698), bei 50 %% lautet das Urteil TRAEGT NICHT "
               "bis 0,0213 R - eine ECHTE Aussage, kein nicht-trennbar. "
               "Kriterium 1 dagegen ist erfuellt: 536 Symbole = 100 %%, "
               "251,6 Anker/Tag. ⚠️ Damit steht er SCHWAECHER da als "
               "`schnitt` (3 von 3) und gleichauf mit `funding` (2 von 3) "
               "- als robuster Ersatz taugt er nicht", "gilt",
               "n111_v11_schnitt50.py"),
    Befundlage("2.331-2187", "✔ UND DER WIDERSPRUCH IM BESTAND IST "
               "AUFGELOEST: 2.187-was-haelt (,`schnitt50` bleibt "
               "abgelehnt, auf ALLEN Mengen') und 2.219 (,widerspricht "
               "sich ueber die Mengen') hatten DIESELBE Basis und sagten "
               "das Gegenteil. **2.219 hatte recht** - er traegt auf 10 %% "
               "und 20 %%, nicht auf 50 %%. 2.187s Formulierung war zu "
               "weit", "gilt", "n111_v11_schnitt50.py / 2.219"),
    Befundlage("2.332", "⚠️⚠️ DIE EHRLICHE GEGENFRAGE AUS V11 TEIL C: ein "
               "Kandidat OHNE Wirkung ist trivial stabil - also stehen "
               "Wirkung und Haelftenunterschied nebeneinander. Auf der "
               "20-%%-Menge bewegen sich ALLE DREI um 80 bis 106 %% ihrer "
               "eigenen Wirkung: `schnitt` 1,06 · `funding` 0,89 · "
               "`schnitt50` 0,80. ⚠️ Der einzige Unterschied ist der "
               "BETRAG - `schnitt`s groesserer Wert schliesst die Null "
               "aus, die kleineren fallen unter dieselbe ABSOLUTE Leiter. "
               "Kriterium 2 trennt damit nicht stabil von instabil, "
               "sondern GROSS von KLEIN", "gilt",
               "n111_v11_schnitt50.py Teil C / n112 G4"),
    Befundlage("2.333", "⚠️⚠️⚠️ UND DAMIT FAELLT DIE ZUSCHREIBUNG AUS "
               "2.325: `schnitt`s Instabilitaet ist eine Eigenschaft der "
               "AUSWAHL, nicht seine. Mit gleich grosser, aber "
               "ZUFAELLIGER Auswahl (`entzerrte_reihe(auswahl_saat=...)`, "
               "drei Saaten) faellt der Haelftenunterschied auf der "
               "20-%%-Menge von +0,1973 auf +0,0380 / +0,0264 / +0,0310 - "
               "ein Faktor 6, und STABIL in allen drei. Das ist genau "
               "der Test, den der Docstring des Parameters vorgibt: "
               ",Traegt die Instabilitaet dann nicht mehr, ist sie eine "
               "Eigenschaft der AUSWAHL und nicht von `schnitt`'", "gilt",
               "n112_v11_gegenpruefung.py G3 / N-88 / 2.222"),
    Befundlage("2.333-schaerfer", "✔✔ DIE NAHELIEGENDE GEGENERKLAERUNG IST "
               "AUSGESCHLOSSEN - und zwar umgekehrt: unter Zufallsauswahl "
               "ist der Test nicht SCHWAECHER, sondern VIERMAL SCHAERFER. "
               "Trennschaerfe 0,05 statt 0,20, Band [-0,0055 .. +0,0897] "
               "statt [+0,0717 .. +0,3892]. **Ein Nullbefund bei hoeherer "
               "Aufloesung** - das sauberste Ergebnis, das der Aufbau "
               "liefern kann", "gilt", "n112 Zusatzpruefung"),
    Befundlage("2.334", "⚠️⚠️ UND UNTER DEMSELBEN SCHAERFEREN TEST KIPPT "
               "AUSGERECHNET `funding` - der LIVE laeuft: bei Saat "
               "20260911 auf der 20-%%-Menge +0,0417 [+0,0036 .. +0,0785], "
               "Band schliesst die Null AUS, also NICHT STABIL. In 1 von "
               "3 Saaten. `schnitt`, `schnitt50` und `zufall` sind dort "
               "in 3 von 3 stabil. ⚠️ Kein Grund zum Abschalten - aber "
               "dieselbe Lage wie bei V2/2.312: die Huerde ist fuer den "
               "BESTAND neu zu begruenden, nicht fuer den Kandidaten zu "
               "senken", "gilt", "n112_v11_gegenpruefung.py G3"),
    Befundlage("2.335", "⚠️⚠️⚠️ DER EIGENTLICHE EINWAND GEGEN `schnitt` "
               "IST EIN ANDERER UND STAERKERER - und er steht seit dem "
               "09.09. da: er bildet die AUSWAHL nach. Spearman +0,704 "
               "mit dem 250-Tage-Momentum (2.158-redundanz), Wirkung zu "
               "vier Fuenfteln Auswahlartefakt (+0,1858 auf der "
               "Momentummenge gegen +0,0366 auf Zufallsmengen, 2.222). "
               "**Ein Beitrag, der die bereits getroffene Auswahl "
               "wiederholt, bringt der Kette wenig Neues** - und dieser "
               "Grund ist von Kriterium 2 voellig unabhaengig", "gilt",
               "2.222 / 2.222-passt / 2.158-redundanz"),
    Befundlage("2.336", "⚠️⚠️ BILANZ NACH V11: ES GIBT KEINEN DRITTEN "
               "BEITRAG. `schnitt` bildet zu 4/5 die Auswahl nach "
               "(2.335) · `schnitt50` besteht N-73 nicht (2.331) · `vola` "
               "faellt an Kriterium 2 UND hat N-73 mit 1 von 3 (2.327, "
               "2.293). Das deckt sich mit dem frueheren Befund, dass die "
               "Kursreihe als Quelle erschoepft ist - ein weiterer "
               "Beitrag braucht eine NEUE Quelle", "gilt",
               "V11 / 2.168-erschoepft"),
    Befundlage("2.337", "⚠️⚠️ EIGENER FEHLER, ZWEITER DIESER ART IN ZWEI "
               "TAGEN: ich habe `entzerrte_reihe` korrigiert und "
               "erweitert, ohne zu sehen, dass sie seit dem 09.09. einen "
               "Parameter `auswahl_saat` GENAU FUER DIESE FRAGE hat - "
               "samt Testvorschrift im Docstring. Am 10.09. war es "
               "dasselbe Muster bei V9 (,das richtige Werkzeug lag vor, "
               "wegen eines Aufrufparameters verworfen'). **Vor dem "
               "Aendern eines Werkzeugs seine SIGNATUR und seinen "
               "Docstring ganz lesen**, nicht nur die Stelle, die man "
               "aendern will", "gilt", "Selbstbefund 11.09.2026"),
    Befundlage("2.338", "⚠️ UND EINE FALSCHE ZITIERUNG, DIE ICH WEITER-"
               "GEREICHT HABE: ,`schnitt50` ist nach 2.222 die einzige "
               "monotone Form' steht in 2.305, 2.326, im Gesamtplan und "
               "im Kopf von `n102` - aber **2.222 sagt das nicht**, es "
               "handelt von `schnitt`s Auswahlartefakt. Die Behauptung "
               "stammt aus `Anforderungen_Umbau_28_08.md` (O4/N2), gilt "
               "dort nur LAENGS, ist vorstandardlich, und ihr eigener "
               "Nachtest N2 ist OFFEN. Im Hebelzusammenhang (H2/H3) "
               "fuehrt die Fakten-Entscheidungsmappe `schnitt50` sogar "
               "ausdruecklich als NICHT MONOTON", "gilt",
               "Basisinfos/Anforderungen_Umbau_28_08.md O4/N2 / "
               "Fakten_Entscheidungsmappe.md"),
    Befundlage("2.339", "✔ WAS V11 SAUBER REPRODUZIERT HAT (R-R11): alle "
               "ZWOELF Haelftenunterschiede aus n110 auf vier "
               "Nachkommastellen · `schnitt`s Wirkungen aus n108 (+0,1830 "
               "/ +0,1858 / +0,0434) · `funding`s (+0,0688 / +0,0582 / "
               "+0,0313) · `schnitt50`s +0,0698 aus 2.308-vorfrage. "
               "⚠️ UND DER MASSSTAB IST GEPRUEFT: mean(entzerrte Reihe) "
               "trifft Wirkung minus Nullpunkt bei allen vier Kandidaten "
               "- ohne das waere das Verhaeltnis in 2.332 sinnlos "
               "gewesen", "gilt", "n112_v11_gegenpruefung.py G1/G2"),
    Befundlage("2.321", "✔ S-7 IST GEKLAERT - und REPRODUZIERT, auf drei "
               "Wegen: die Wirkungszahlen (Faktor 1,14 bis 1,45 gegen "
               "S-7s Tafel), der JAHRESVERLAUF (2019 +0,52 gegen +0,45 · "
               "2022 +0,022 gegen +0,019 · 2023 −0,047 gegen −0,050) und "
               "der HAELFTENUNTERSCHIED (+0,1973 gegen +0,2238, samt der "
               "Vorzeichendrehung bei 10 %%: −0,0805 gegen −0,0647). "
               "R-R11 ist erfuellt, das Urteil darf gedeutet werden",
               "gilt", "n108_s7_geklaert.py / n109_s7_gegenpruefung.py"),
    Befundlage("2.321-wortlaut", "⚠️⚠️ ABER S-7 IST NUR IN SEINEM EIGENEN "
               "WORTLAUT BESTAETIGT - *,es ist unentschieden'* - und "
               "NICHT in der Lesart, `schnitt` trage ab 2022 nicht. Auf "
               "allen drei Mengen ab 2022 lautet das Urteil NICHT "
               "TRENNBAR, nicht TRAEGT NICHT. Der Unterschied ist der "
               "Kern der Norm: `zufall` bekommt in JEDER Zeile ein "
               "TRAEGT NICHT bis X - eine Aussage ueber die Welt. "
               "`schnitt` bekommt dreimal keine Aussage", "gilt",
               "n108_s7_geklaert.py / messnorm.urteil"),
    Befundlage("2.321-ab2024", "⚠️⚠️ UND S-7s SPALTE ,AB 2024' WAR NIE "
               "GUELTIG: 962 Tage = 16 Bloecke, gefordert sind 20. Unter "
               "dem heutigen Standard ist das KEIN BEFUND, nicht traegt "
               "nicht. ⚠️ Mein eigener Hauptlauf sagte es NICHT - bei "
               "leerer Mengenliste laeuft die innere Schleife nie und es "
               "wird gar nichts gedruckt. Fail-silent im eigenen "
               "Werkzeug; die Abnahmetafel hat es aufgefangen, die Zeile "
               "nicht", "gilt", "n109_s7_gegenpruefung.py G4"),
    Befundlage("2.322", "⚠️⚠️ DER MECHANISMUS IST DIE BANDBREITE, NICHT "
               "ein fehlender Effekt. Bei GLEICHER Blockzahl ist "
               "`schnitt`s Band rund sechsmal breiter als `funding`s "
               "(ab 2022, 10 %%: 0,383 gegen 0,063). Signal je "
               "Bandbreite im Mittel 0,36 gegen 0,61. Er hat die "
               "GROESSERE Wirkung und den SCHLECHTEREN Schaetzer - und "
               "das bestaetigt die Notiz vom 07.09. (`schnitt`s Baender "
               "sind fuenfmal breiter) aus eigener Rechnung", "gilt",
               "n109_s7_gegenpruefung.py G2"),
    Befundlage("2.323", "✖ MEINE ERKLAERUNG ,KLUMPIGKEIT' IST WIDERLEGT - "
               "und zwar von der eigenen Kontrolle. Das Kriterium "
               "Streuung-ueber-Mittel gab ALLEN dreien klumpig, auch "
               "`zufall` (Str/Mit 1,25). Damit misst es eine Eigenschaft "
               "des Jahresfensters, nicht des Kandidaten. ⚠️ Die Tafel "
               "zeigt statt Streuen einen NIVEAUABFALL: 2019 bis 2021 "
               "bei +0,36 bis +0,57, ab 2022 zwischen −0,05 und +0,17 - "
               "und `zufall` liegt dort bei 0,03 bis 0,07, also zehnmal "
               "kleiner. Die Frueh-Erhoehung ist NICHT vom Zeitfenster "
               "erklaert", "gilt", "n109_s7_gegenpruefung.py G3"),
    Befundlage("2.324", "⚠️⚠️⚠️ UND DABEI IST EIN FEHLER IM VIERFACHTEST "
               "SELBST AUFGEFALLEN: `n102_vierfachtest.py:135` entschied "
               "Kriterium 2 allein ueber d[unten] <= 0.0 <= d[oben] - "
               "STABIL hiess dort nur DAS BAND SCHLIESST DIE NULL EIN. "
               "Ein NICHT-Verwerfen, als Haken ausgegeben, mit einer "
               "Richtung, die den falschen Kandidaten belohnt: JE "
               "BREITER DAS BAND, DESTO SICHERER DAS ✔. `schnitt`, "
               "dessen Baender sechsmal breiter sind, bestand also "
               "nicht, WEIL er stabil ist, sondern WEIL er unruhig ist",
               "gilt", "n102_vierfachtest.py:135 / Selbstbefund 10.09."),
    Befundlage("2.324-n73", "⚠️⚠️ ZWEITER FEHLER, GLEICHE STELLE: N-73 "
               "war bei Kriterium 2 nie angewandt. Im selben `main()`, "
               "zehn Zeilen auseinander, lief Kriterium 1 ueber ALLE "
               "zulaessigen Mengen und Kriterium 2 ueber EINE. Und genau "
               "das kippt: `schnitt`s Haelftenunterschied dreht mit der "
               "Menge (−0,0805 bei 10 %%, +0,1973 bei 20 %%). WER EINE "
               "MENGE WAEHLT, WAEHLT DAS URTEIL. Der Bestand hatte es am "
               "07.09. schon notiert, es war nur nie in den Test "
               "gewandert", "gilt", "n102_vierfachtest.py / 2.7-07.09."),
    Befundlage("2.325", "⚠️⚠️⚠️ RICHTIG GEMESSEN FAELLT `schnitt` AN "
               "KRITERIUM 2 - und es ist KEIN nicht-trennbar, sondern "
               "ein NACHGEWIESENER Unterschied: auf der 20-%%-Menge "
               "+0,1973 [+0,0717 .. +0,3892], Band schliesst die Null "
               "AUS, 20/20 Bloecke. Auf 10 %% und 50 %% ist er stabil - "
               "nach N-73 zaehlt das nicht als Entlastung, sondern als "
               "fehlende Robustheit. ⚠️ `zufall` bekommt nirgends NICHT "
               "STABIL (stabil bis 0,02 bis 0,05) - die Kontrolle "
               "haelt", "gilt", "n110_kriterium2_mit_trennschaerfe.py"),
    Befundlage("2.325-2319", "⚠️⚠️⚠️ DAMIT IST 2.319 ZU WIDERRUFEN: "
               "`schnitt` hat NICHT alle vier Kriterien. Er hat DREI - "
               "Abdeckung, Unabhaengigkeit, Regel 3 - und faellt an der "
               "STABILITAET. ⚠️ Der Widerruf ist zulaessig, weil er "
               "reproduziert wurde (2.321): dreimal, auf drei "
               "verschiedenen Wegen. R-R11 ist erfuellt", "gilt",
               "n110_kriterium2_mit_trennschaerfe.py / R-R11"),
    Befundlage("2.326", "✔✔ DIE LOESUNG STEHT IN DERSELBEN TAFEL - "
               "`schnitt50` ist auf ALLEN DREI Mengen stabil (bis 0,20 · "
               "0,20 · 0,05). ⚠️ Nutzervorgabe: Kein Beitrag darf einfach "
               "fallen, konkrete Begruendung erforderlich und ggf. "
               "Loesung suchen. Die Begruendung steht in 2.325; die "
               "Loesung ist die 50er-Form, die der Nutzer am 09.09. "
               "selbst zurueckgeholt hat (Warum hast du schnitt50 "
               "einfach herausgenommen?) und die nach 2.222 die einzige "
               "MONOTONE Form ist. Zu pruefen bleiben bei ihm "
               "Kriterium 1 und N-73", "abgeloest",
               "n110_kriterium2_mit_trennschaerfe.py / 2.222",
               abgeloest_durch="2.331",
               warum="V11 hat beide Stuetzen weggenommen: N-73 besteht er\n                     NICHT (2 von 3, 2.331), und die Monotonie war FALSCH\n                     ZITIERT (2.338). Kriterium 1 erfuellt er - das allein\n                     macht ihn nicht zum Ersatz"),
    Befundlage("2.327", "⚠️ `vola` FAELLT AN DERSELBEN STELLE - und fast "
               "mit derselben Zahl: +0,2039 [+0,0760 .. +0,3912] auf "
               "20 %%, gegen `schnitt`s +0,1973, beide mit 20/20 "
               "Bloecken. Das ist zu aehnlich fuer Zufall und stuetzt "
               "2.293 (`vola` ist Geometrie, nicht Richtung): die beiden "
               "koennten denselben geometrischen Anteil enthalten. "
               "⚠️ HYPOTHESE, nicht Befund - sie ist nicht gemessen",
               "offen", "n110_kriterium2_mit_trennschaerfe.py"),
    Befundlage("2.328", "✔✔ KEIN LAUFENDER BEITRAG IST BETROFFEN: "
               "`funding` (bis 0,10 · 0,10 · 0,05), `oi_aenderung` (bis "
               "0,05 · 0,02) und `turnover` (bis 0,10) sind auf ALLEN "
               "ihren zulaessigen Mengen stabil - mit Aussage, nicht mit "
               "nicht-trennbar. Dieser Lauf aendert nichts am Betrieb; "
               "er verhindert eine Registrierung, die sonst auf einem "
               "fehlerhaften Kriterium beruht haette", "gilt",
               "n110_kriterium2_mit_trennschaerfe.py"),
    Befundlage("2.329", "⚠️ VOM VORABTEST GEFANGEN - DIE ZWEI LEITERN "
               "SIND NICHT DIESELBE SKALA: der Stabilitaetstest pflanzt "
               "den Versatz 1:1 auf die entzerrte Reihe, `messnorm` "
               "pflanzt gegen den Nullpunkt mit der Daempfung aus "
               "GRENZE = 0,80 (gepflanzte 0,10 R erscheinen als rund "
               "0,02). Ein bis-0,20 im Stabilitaetstest ist NICHT mit "
               "einem 0,05 R der Norm zu vergleichen. Steht jetzt im "
               "Kopf beider Werkzeuge und in der Ausgabe", "gilt",
               "n110 / n68.stabilitaetsurteil"),
    Befundlage("2.330", "✔ DAS KORRIGIERTE URTEIL STEHT AN DER QUELLE - "
               "`n68_zeitstabilitaet.stabilitaetsurteil()`, gerufen von "
               "`n102` UND `n110`. Vorgabe: ein Test muss die ECHTE "
               "Funktion rufen, nie eine Kopie. ⚠️ Die alte Konstruktion "
               "sitzt sonst nirgends: `n88:152` und `n89:106` nutzen "
               "dieselbe Zeile in der RICHTIGEN Richtung (als trennt), "
               "geprueft per Suche ueber alle Skripte", "gilt",
               "n68_zeitstabilitaet.py / n102 / n110"),
    Befundlage("2.316", "✔✔✔ V9: KRITERIUM 3 IST BEANTWORTET - "
               "`funding` erklaert bei KEINEM Kandidaten etwas. "
               "Geschichtet gemessen als EIN Befund mit EINEM Band: "
               "`schnitt` echt +0,0388 gegen gemischt +0,0361 · "
               "`schnitt50` +0,0300 gegen +0,0311 · `turnover` +0,0442 "
               "gegen +0,0514 · `oi_aenderung` +0,0135 gegen +0,0128. "
               "⚠️⚠️ Der ABFALL durch die Schichtung (`schnitt` von "
               "+0,1858 auf +0,0388) tritt mit BEDEUTUNGSLOSEM Partner "
               "genauso ein - er ist ein Artefakt der Schichtung, keine "
               "Redundanz", "gilt", "n107_v9_kriterium3_ein_befund.py",
               basis="H20 · Kandidaten auf 20 % (vorab), Bestand auf "
                     "seiner Basis · marke=None · 5 Funding-Faecher"),
    Befundlage("2.316-lesart", "✔ DIE LESART GIBT DAS WERKZEUG SELBST "
               "VOR - `pruefe_n1_schichtung_gegen_partner`: ,Bleibt es "
               "auch dort beim selben Wert, ist es die SCHICHTUNG - der "
               "Partner erklaert NICHTS.' Und ,der Partner erklaert "
               "nichts' IST Unabhaengigkeit, also genau das, was "
               "Kriterium 3 fragt. ⚠️ Meine erste Ausgabe sagte nur "
               ",kein Unterschied, Baender ueberlappen' - technisch "
               "richtig, aber sie liess den Leser mit der Zahl allein, "
               "statt den Schluss zu ziehen", "gilt",
               "n107_v9_kriterium3_ein_befund.py"),
    Befundlage("2.317", "✔✔ UND DIE TRENNSCHAERFE IST BEZIFFERT: 0,05 R "
               "in jeder Zeile. Bei den Zaehlmetriken von V7 und V8 gab "
               "es KEINE - ein ,traegt nicht' war dort nie von "
               "Untermacht zu unterscheiden. Jetzt ist der Nullbefund "
               "bei `zufall` eine echte Aussage. ⚠️ Das ist der Grund, "
               "warum V9 gelingt, wo V7 und V8 gescheitert sind: eine "
               "STETIGE Kennzahl mit Band und Leiter statt einer "
               "Zaehlung mit drei bis sechs moeglichen Werten",
               "gilt", "n107_v9_kriterium3_ein_befund.py"),
    Befundlage("2.318", "⚠️⚠️ DREI ANLAEUFE, DREI EIGENE FEHLER - und "
               "jeder von einer anderen Instanz gefangen: V7 - "
               "Zaehlmetrik zu grob, und die Kontrolle bekam ,unabhaengig' "
               "(vom VORABTEST gefangen). V8 - mein Loesungsweg ,weniger "
               "Faecher' machte die Zaehlmetrik GROEBER statt besser (vom "
               "ERGEBNIS gefangen). V9 - das richtige Werkzeug lag vor, "
               "ich hatte es wegen eines Aufrufparameters verworfen, und "
               "beim Umbau die Vorfrage aus V7 nicht mitgenommen (vom "
               "ERGEBNIS gefangen, weil `zufall` wieder ein positives "
               "Urteil bekam)", "gilt", "Selbstbefund 10.09.2026"),
    Befundlage("2.319", "✔✔✔ `schnitt` HAT DAMIT ALLE VIER KRITERIEN: "
               "1 ABDECKUNG 100 %% (536 von 536) · 2 STABILITAET stabil "
               "(N-68-Form) · 3 UNABHAENGIG von `funding` (V9) · "
               "4 REGEL 3 mit 25,4 %% Asset-Anteil roh bestanden. Dazu "
               "N-73 mit 3 von 3 Mengen - BESSER als jeder registrierte "
               "Beitrag (`funding` 2 von 3) - und er traegt zusaetzlich "
               "in der AKKUMULATIONSlage (+0,0470, p 0,000). "
               "⚠️ Die Entscheidung ueber die Registrierung ist eine "
               "NUTZERENTSCHEIDUNG und loest R-R9 aus: die Schwelle "
               "0,080 waere neu zu kalibrieren", "abgeloest",
               "V1/V2/V9 · Vierfachtest · 2.286-schnitt",
               abgeloest_durch="2.325",
               warum="Kriterium 2 war fehlerhaft konstruiert "
                     "(2.324): ,stabil' hiess dort nur ,das Band schliesst "
                     "die Null ein', ohne Trennschaerfe und auf EINER "
                     "Menge statt allen. Richtig gemessen ist `schnitt`s "
                     "Haelftenunterschied auf der 20-%%-Menge NACHGEWIESEN "
                     "(+0,1973 [+0,0717 .. +0,3892], 20/20 Bloecke) - er "
                     "hat DREI Kriterien, nicht vier. ⚠️ Reproduziert vor "
                     "dem Widerruf, dreifach (2.321), R-R11 erfuellt"),
    Befundlage("2.320", "⚠️ WAS BEI `vola` UEBRIG BLEIBT: geschichtet "
               "traegt er nicht mehr - echt wie gemischt, bei einer "
               "Trennschaerfe von 0,05 R. Das ist ein ECHTER Nullbefund, "
               "keine Untermacht: `funding` erklaert auch bei ihm nichts, "
               "aber die Schichtung nimmt ihm die Trennbarkeit. Zusammen "
               "mit N-73 (1 von 3 Mengen) bleibt er der wackligste der "
               "Kandidaten", "gilt",
               "n107_v9_kriterium3_ein_befund.py / 2.293"),
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
               "07.09. stehen", "abgeloest", "Methodik 2.187",
               basis="Messbasis 08.09.2026, 536 Krypto-Symbole",
               abgeloest_durch="2.331-2187",
               warum="Die Teilaussage zu `schnitt50` (,bleibt "
                     "abgelehnt, auf ALLEN Mengen') ist FALSCH - "
                     "er traegt auf 10 %% (+0,0846) und 20 %% "
                     "(+0,0698), nur auf 50 %% nicht. 2.219 hatte "
                     "recht. Der Rest des Befundes steht"),
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
               "moeglich "
               "✔ MIT 2.426 GEKLAERT UND BEWUSST NICHT GEAENDERT: die "
               "Messbasis traegt die Klasse jetzt im Schluessel, die "
               "PRODUKTIONSdatenbank fuehrt die Spalte weiterhin nicht. "
               "⚠️ Das bleibt folgenlos, solange die Watchlist-Symbole "
               "eindeutig sind - keiner der sieben Doppelticker (BOND, C, "
               "DASH, DIA, MDT, STX, T) steht dort. ➔ Faellt das je, ist "
               "es an der Neuaufnahme zu sehen, nicht hier: die Watchlist "
               "waere um einen Ticker erweitert worden, den es zweimal "
               "gibt",
               "gilt", "Methodik 2.149"),
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
               "DANN laden "
               "✔✔✔ ERLEDIGT AM 13.09. (Schritt 50 Teil A, 2.426): "
               "`messreihen` traegt die Klasse jetzt im Schluessel, "
               "`messreihen_status` ebenso. ⚠️ Die Sperre, die dieser "
               "Befund forderte (,ERST Strukturfix, DANN laden`), war "
               "allerdings ueberholt: das Laden ist laengst passiert, und "
               "der Fix vom 07.09. in `_reihen_roh` hat es folgenlos "
               "gemacht (2.421). Der Schemawechsel war Aufraeumen, keine "
               "Rettung",
               "gilt", "Methodik 2.148"),
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
               "Behebbar. "
               "✔✔ ERLEDIGT AM 13.09., ABER NICHT SO, WIE 2.395-erledigt es "
               "sagte: dort stand *,alle neun Werte haben laengst eine "
               "Kursreihe`* - nachgezaehlt sind es SIEBEN. AKT (727 Punkte), "
               "BRETT (854), GRIFFAIN (537), HYPE (405), KAS (1.078), "
               "MORPHO (637) und PLUME (484) haben eine; ASTER und MON haben "
               "NULL. ⚠️ Und die beiden sind kein Rest, sondern eine REGEL - "
               "bereits registriert in 2.185-rest: mit 318 bzw. 269 "
               "USD-Tagen liegen sie unter `lade_messreihen.MIN_KERZEN` = "
               "400, weil die Coins erst seit 10/2025 und 11/2025 "
               "existieren. Eine Datenlage-Grenze, keine Nachlaessigkeit. "
               "➤ Der Befund ist damit geschlossen; was von ihm bleibt, "
               "steht in 2.185-rest und faellt weg, sobald die beiden "
               "Reihen lang genug sind", "gilt", "Methodik 2.146"),
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
    seite = {k.name: umbauseite(k) for k in KANDIDATEN}
    vor = [k for k in KANDIDATEN if seite[k.name][0] != "nach Umbau"]
    z += ["⚠️⚠️ **VOR ODER NACH DEM UMBAU?** Die Grenze ist der "
          "Messstandard vom 08./09.09.2026. **%d von %d Blaettern "
          "stammen von davor** — ihre Urteile haben die Norm nicht "
          "gesehen (anderer Nullpunkt, andere Trennschaerfe, kuerzere "
          "Leiter)." % (len(vor), len(KANDIDATEN)),
          "",
          "⚠️ Das Datum ist ein **Anhalt, kein Urteil**: ein altes "
          "Ergebnis kann richtig sein. Es sagt nur, dass es unter "
          "anderen Regeln entstanden ist und vor einem Widerruf "
          "reproduziert gehoert (R-R11).",
          ""]
    z += ["## Uebersicht", "",
          "| | Kandidat | Form | Zustand | Umbauseite | letzte Messung | "
          "Registrierungsbasis |",
          "|---|---|---|---|---|---|---|"]
    for k in KANDIDATEN:
        wo, wann = seite[k.name]
        marke = {"nach Umbau": "✔ nach", "vor Umbau": "⚠️ VOR",
                 "ohne Datum": "? ohne"}.get(wo, wo)
        z.append("| %s | **`%s`** | %s | %s | %s | %s | %s |"
                 % (sym.get(k.zustand, "?"), k.name, k.form, k.zustand,
                    marke, wann, k.basis))
    z.append("")
    if vor:
        z += ["### ⚠️ Diese Blaetter stammen von VOR dem Messstandard", "",
              ", ".join("`%s`" % k.name for k in vor), ""]
    for k in KANDIDATEN:
        z += ["---", "", "## %s `%s`" % (sym.get(k.zustand, "?"), k.name), "",
              "**Hypothese:** %s" % k.hypothese, "",
              "| | |", "|---|---|",
              "| **Form** | %s |" % k.form,
              "| **Registrierungsbasis** | %s |" % k.basis,
              "| **Wert** | %s |" % k.wert,
              "| **Live** | %s |" % k.live,
              "| **Zustand** | **%s** |" % k.zustand,
              "| **Umbauseite** | %s (letzte Messung %s) |"
              % (("✔ **nach** dem Messstandard"
                  if umbauseite(k)[0] == "nach Umbau" else
                  "⚠️ **VOR** dem Messstandard — Urteil unter anderen "
                  "Regeln entstanden"
                  if umbauseite(k)[0] == "vor Umbau" else
                  "? kein Datum in der Messkette"), umbauseite(k)[1]), ""]
        if k.kette:
            z += ["**Die Messkette:**", ""]
            for datum, was in k.kette:
                z.append("- **%s** — %s" % (datum, was))
            z.append("")
        if k.loesung:
            z += ["**Die Loesungsspur** — *kein Beitrag faellt ohne "
                  "Grund:*", "", "> %s" % k.loesung, ""]
        elif k.zustand == "traegt nicht":
            z += ["⚠️⚠️ **KEINE LOESUNGSSPUR HINTERLEGT.** Die "
                  "Nutzervorgabe verlangt sie bei jedem gefallenen "
                  "Beitrag — hier fehlt sie.", ""]
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
         "*Erzeugt aus `bestand.py` durch **Scan**, nicht gepflegt — %d "
         "Eintraege von Hand zu fuehren waere dieselbe Falle noch einmal.*"
         % ges,   # ⚠️ GEZAEHLT, nicht hart: die 281 hier standen im
                  # Widerspruch zur Tabelle zwei Zeilen darunter (308).
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
