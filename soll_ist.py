# -*- coding: utf-8 -*-
"""SOLL/IST — steht der Umbau noch im Plan? (10.09.2026)

## ⚠️⚠️⚠️ Warum es dieses Werkzeug gibt

Nutzervorgabe 10.09.:

> *„bau fuer dich eine Hilfe ein, um laufend einen Abgleich zwischen IST
> und SOLL durchzufuehren, damit wir nichts vergessen — die Planung,
> Analyse, Test, Simulation und Umbau ist komplex und umfangreich, sonst
> verlieren wir wieder den Faden."*

**Der Anlass war ein echter Verlust des Fadens.** Am 05.09. stand als
Nutzerentscheidung fest: *„erst die Bewertung, dann der Hebelumbau"*, und
der EINE naechste Schritt war **N-46**. Vom 08. bis 10.09. lief
stattdessen die Messanlage und die Kettenpruefung; N-46 wurde nie
angefasst. Zweimal wurde ausserdem die **Hebelvorgabe** (2-5x, dynamisch
aus der Wahrscheinlichkeit) als „erledigt" behandelt, weil ein
Memory-Eintrag nur die Instrument-Achse abschloss.

> **Ein Register sagt, was GEMESSEN wurde. Dieses Werkzeug sagt, was
> ENTSCHIEDEN wurde - und ob das laufende System noch dazu passt.**

## Was hier steht - und was NICHT

    SOLL   Entscheidungen und Vorgaben, jede mit QUELLE. Handgepflegt,
           weil eine Entscheidung nirgends automatisch ablesbar ist.
    IST    wird GELESEN - aus `wahrscheinlichkeit`, `messnorm`, `bestand`,
           `messmenge` und der Messdatenbank. Nie getippt.

⚠️ Dieselbe Regel wie bei den Registern: **wer eine SOLL-Zeile aendert,
aendert eine ENTSCHEIDUNG** - und die gehoert vorher mit dem Nutzer
abgestimmt und ins Plandokument.

⚠️⚠️ Das Werkzeug urteilt NICHT ueber Messergebnisse. Es prueft nur, ob
das, was laeuft, dem entspricht, was vereinbart ist.

    python soll_ist.py             # der volle Abgleich
    python soll_ist.py --kurz      # nur Abweichungen und der naechste Schritt
"""
from __future__ import annotations

import glob
import os
import sqlite3
import sys
import time
from dataclasses import dataclass, field

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import bestand as BE                                          # noqa: E402
import messmenge                                              # noqa: E402
import markiere_dokumente as MD
import messnorm as N                                          # noqa: E402
from agent import wahrscheinlichkeit as W                     # noqa: E402

DB = "file:data/messdaten.db?mode=ro"


# ============================================================================
# DAS SOLL - handgepflegt, jede Zeile mit Quelle
# ============================================================================

@dataclass(frozen=True)
class Vorgabe:
    """Eine ENTSCHEIDUNG oder Nutzervorgabe - kein Messergebnis."""
    kennung: str
    text: str
    quelle: str
    stand: str = "offen"        # offen | erfuellt | zurueckgestellt


@dataclass(frozen=True)
class Lage:
    """Was fuer eine Lage GILT - und was sie erreichen soll."""
    instrument: str
    strategie: str
    klasse: str
    soll: str
    blocker: str = ""
    erbt_spot: bool = False
    """⚠️ Erbt diese Lage die Spot-Beitraege ABSICHTLICH?

    Nutzerentscheidung 10.09.: der Hebel bekommt **keine eigene
    Bewertungsgruppe**. Eine Bewertung, ein Potential - der Hebel
    entsteht dynamisch daraus. Damit ist das ,Erben' der Spot-Beitraege
    die UMSETZUNG, nicht ein Mangel. Ohne dieses Feld meldete der
    Abgleich es weiter als Abweichung."""


@dataclass
class Schritt:
    """Ein Schritt der vereinbarten Reihenfolge.

    ⚠️ `block` KAM AM 12.09.2026 DAZU, und der Grund steht in Befund 2.395:
    der Plan hatte zwanzig offene Schritte OHNE Rangfolge. `soll_ist` meldete
    "naechster Schritt 25", waehrend an 44 gearbeitet wurde - eine Liste, die
    die Arbeit nicht abbildet, ist Zierde. Der Vorgabewert ist leer, damit
    kein bestehender Schritt bricht; wer keinen Block hat, faellt unter
    "nicht eingeordnet" und faellt damit AUF."""
    nr: int
    kennung: str
    text: str
    quelle: str
    fertig: bool = False
    hinweis: str = ""
    block: str = ""
    # ⚠️⚠️ WORAUF DIESER SCHRITT WARTET (13.09.2026, Schritt 46 Teil 2).
    #
    # DER GRUND: die Blockordnung vom 12.09. ordnet nach DRINGLICHKEIT und
    # kennt keine ABHAENGIGKEIT. Folge: `soll_ist` meldete als naechsten
    # Schritt 28, dessen eigener Text sagt *"ERST NACH DEM ROLLOUT messen
    # - vorher misst man den alten Stand"*. Ein Plan, der auf einen
    # Schritt zeigt, der nicht darf, ist so unbrauchbar wie einer ohne
    # Rangfolge - es ist derselbe Fehler (2.395) eine Ebene tiefer.
    #
    # ⚠️ NUR EINTRAGEN, WAS DER SCHRITT SELBST SAGT. Das Feld ist kein
    # Ort fuer Vermutungen ueber Reihenfolgen; steht die Abhaengigkeit
    # nicht im Text, gehoert sie erst dorthin.
    #
    # ⚠️⚠️ UND NICHT UMSORTIEREN STATTDESSEN: das wuerde die Abhaengigkeit
    # VERSTECKEN - man saehe die richtige Reihenfolge, aber nicht den
    # Grund, und beim naechsten Umbau waere sie wieder weg.
    wartet_auf: tuple = ()
    # ⚠️⚠️ ALT ODER NEU (13.09.2026, Nutzervorgabe: *"Der PLAN muss klar
    # zwischen altem und neuem Umbau unterscheiden"*).
    #
    # DER GRUND, in seinen Worten: *"das zu LLM kann nicht ganz stimmen -
    # Hebel soll nicht aus LLM kommen, du vermischt altes mit neuem"*. Er
    # hatte recht, und die Vermischung war meine: ich hatte den
    # Widerlegungspreis als tragend fuer den Hebel dargestellt, obwohl er
    # nur den STOP setzt - und der Stop ist der ALTE Teil der Rechnung,
    # waehrend `r(q)` der neue ist.
    #
    #     neu       gehoert zum Umbau seit dem 22.08.: die Bewertung
    #               (Potential, Schwelle, Beitraege), `r(q)`, die
    #               Messnorm, die Toepfe und Deckel. Hier wird GEBAUT.
    #     alt       stammt aus der Zeit davor und wird AUFGERAEUMT oder
    #               ERSETZT: die LLM-Rollen (stehen seit 22.08.), die
    #               Geometrie aus Modellangaben, die alte Hebelkette,
    #               der Marktscan.
    #     beides    ein Schritt, der Altes ersetzt UND Neues baut - der
    #               haeufigste Fall, und er gehoert benannt statt
    #               gemittelt.
    #
    # ⚠️ Leer heisst NICHT eingeordnet und faellt in der Ausgabe auf -
    # dieselbe Regel wie beim Block.
    umbau: str = ""


# ---- Die Vorgaben, die ueber allem stehen ---------------------------------
VORGABEN = (
    Vorgabe("HEBEL-ZIEL",
            "Die Wahrscheinlichkeit auf positives Chance-Risiko-Verhaeltnis "
            "soll den Hebel DYNAMISCH erzeugen. Zielzone 2-5x. "
            "⚠️ `hebel = verlustanteil / stop_rel` erzeugt ihn aus der "
            "VOLATILITAET - das ist NICHT dasselbe.",
            "Nutzervorgabe; F-220 / N-40 K1 / memory hebel_scheitert_an_der_bewertung"),
    Vorgabe("REIHENFOLGE",
            "⚠️ ABGELOEST 11.09.: die Entscheidung vom 05.09. (,erst die "
            "Bewertung, dann der Hebelumbau - r(q) hat nichts zu "
            "verteilen') stand auf der GEFALLENEN Kalibrierung (19,5 %). "
            "2.174-neu: unkalibriert erreichen zwei Lagen 2-5x - r(q) hat "
            "etwas zu verteilen. JETZT: Paket B - Hebel (K1, K3, O5) und "
            "Spot VOR dem Rollout, die Akkumulation als Paket 2.",
            "Nutzerentscheidung 05.09. -> abgeloest durch "
            "Nutzerentscheidung 11.09. (Paket B)", "erfuellt"),
    Vorgabe("PAKET-B",
            "HEBEL: risiko = r(q) x Kapital, r(q) = halbes Kelly geklammert "
            "0,50-1,25 % (N-39); Kapital = `portfolio_wert_historie."
            "wert_eur` (P-5); hebel = (risiko / Stop) / 500 EUR; unter 2x "
            "SPOT; harte Grenze 5x bis zur Trennschaerfe (A1); Quote "
            "unkalibriert; Aggregat-Deckel 3 % des Kapitals. SPOT: Betrag "
            "UNVERAENDERT (N-38: ,Spot bleibt unberuehrt'). AKKUMULATION: "
            "gesperrt bis Paket 2.",
            "Nutzerentscheidung 11.09.: ,ja Paket B, Deckel 5x, Rest wie "
            "empfohlen'; Prioritaet ,1 Hebel 2 Spot 3 Akkumulation'"),
    Vorgabe("ZEITFENSTER-AB-2023",
            "⚠️⚠️ NUTZERMEINUNG 13.09., AN DEN DATEN GEPRUEFT UND BESTAETIGT "
            "(Befund 2.414): *,der Kryptomarkt vor sieben Jahren ist nicht "
            "mehr mit heute vergleichbar - die letzten 3 bis 4 Jahre haben "
            "die meiste Aussagekraft.'* GEMESSEN an `turnover`, H20, beide "
            "Haelften gleich lang (je 1.327 Tage): bis 2022 Spanne +2,77 "
            "OHNE Ordnung, ab 2023 Spanne +8,64 SAUBER GEORDNET. 2019 laeuft "
            "sogar UMGEKEHRT (-16,67). ➔ WAS DARAUS FOLGT: (a) eine "
            "Kalibrierung ueber sieben Jahre mittelt eine gute und eine "
            "schlechte Haelfte zusammen und macht den Beitrag SCHWAECHER als "
            "er ist; (b) wer eine Tabelle neu rechnet, nennt das "
            "Zeitfenster - es ist ab jetzt eine ANGABE, keine "
            "Selbstverstaendlichkeit; (c) das gilt zunaechst fuer "
            "`turnover`, geprueft ist nur diese Groesse. "
            "⚠️⚠️⚠️ RICHTIGSTELLUNG 13.09. (Befund 2.416-norm) - ZWEI "
            "PUNKTE OBEN WAREN FALSCH. (1) DIE ZAHLEN SIND KEIN BEFUND: "
            "nackte Fuenftel-Median-Spannen ohne Band, ohne Trennschaerfe, "
            "ohne Positivkontrolle - nach `messnorm` ist damit keines der "
            "vier Urteile aussprechbar. Es sind HINWEISE. Wert haben sie, "
            "weil G2 vom 06.09. dieselbe Richtung NORMGERECHT fand "
            "(+0,0172 gegen +0,0137) - die Messung REPRODUZIERT, sie "
            "stuerzt nichts um. (2) FUER `funding` IST DIE FRAGE NICHT "
            "OFFEN, sie war am 07.09. mit Band und Trennschaerfe "
            "beantwortet (S-7): `funding` ganz +0,0446 / ab 2022 +0,0157 / "
            "ab 2024 +0,0182, stabil bis 0,05 R; `oi_aenderung` +0,0296 / "
            "+0,0296 / +0,0287, stabil bis 0,05 R; `turnover` auf der "
            "50-%-Menge ab 2022 +0,0598, stabil bis 0,10 R. ➔ KEIN "
            "TRAGENDER BEITRAG BRAUCHT WEGEN DES ZEITFENSTERS EINE "
            "NEUKALIBRIERUNG. Was bleibt, ist (b): wer eine Tabelle neu "
            "rechnet, NENNT das Fenster.",
            "Nutzermeinung 13.09.; Befunde 2.414, 2.416-norm; S-7 07.09."),
    Vorgabe("STAND-PRUEFEN-VORHER",
            "⚠️⚠️⚠️ NUTZERVORGABE 13.09.: *,dieser Fall hat mir wieder "
            "gezeigt, wie wichtig es ist, dass du die Verbindung zu den "
            "vorherigen Themen und Ergebnissen hast - schreibe dir fest, "
            "WANN und WO du vor der Messung und Umsetzung den aktuellen "
            "Stand und die Dokumentation pruefen sollst. Das Risiko, dass "
            "Themen auseinanderlaufen, ist hoch.'* "
            "➔ DER FALL: ich habe in Schritt 47 eine Tabelle ,Quote → "
            "Kelly → Hebel' gerechnet - genau diese Tabelle gab es seit "
            "dem 08.09. (2.174-neu), und ihr Hauptbefund war am 11.09. "
            "behoben. Der Nutzer hat es gemerkt, nicht ich. ⚠️ Der Schaden "
            "waere nicht die doppelte Arbeit, sondern die doppelte "
            "AUSSAGE: zwei Zahlenreihen zur selben Frage, die sich "
            "widersprechen, solange niemand sagt, was dazwischenliegt. "
            "➔ VIER AUSLOESER: (1) vor JEDER Messung - auch vor einer "
            ",Nebenrechnung'; eine Nebenrechnung, die der Nutzer als "
            "Tabelle liest, IST eine Messung. (2) Vor jedem Bau, der eine "
            "Zahl, Grenze oder Regel setzt. (3) Vor jeder Aussage ueber "
            "einen Zustand (,X funktioniert nicht', ,Y fehlt', ,nicht "
            "messbar'). (4) Bevor ein offener Punkt VORGELEGT wird - ist "
            "er inzwischen beantwortet? "
            "➔ SECHS ORTE, in dieser Reihenfolge: REGISTER_Befunde (was "
            "gilt, was abgeloest ist und wodurch) · REGISTER_Kandidaten "
            "(Registrierungsbasis je Groesse) · REGISTER_Fakten (die "
            "F-Nummern nach Thema) · `soll_ist` (der Planschritt selbst) · "
            "DAS MODUL (die Zahl steht mit ihrer Begruendung im Code, nicht "
            "im Plan) · `Claude_Austauschordner/DB_Backups` (die taegliche "
            "Produktionssicherung - BEVOR ,nicht messbar' faellt). "
            "➔ DREI FRAGEN: Gibt es die Zahl schon? (dann REPRODUZIEREN, "
            "R-R11, nicht neu rechnen) · Ist der Befund abgeloest, und "
            "wodurch? · Was hat sich seither am CODE geaendert? Eine Zahl "
            "vom 08.09. gilt nicht fuer einen Stand vom 13.09.",
            "Nutzervorgabe 13.09.; Befunde 2.432-lehre, 2.424, "
            "2.422-desktop"),
    Vorgabe("MESSSTANDARD-VOR-DER-MESSUNG",
            "⚠️⚠️⚠️ NUTZERVORGABE 13.09.: *,merke dir dauerhaft den "
            "Messstandard zu beruecksichtigen BEVOR du wieder neue "
            "Pruefungen und Messungen durchfuehrst.'* ➔ DER ANLASS IST "
            "EIN FEHLER AM SELBEN TAG: Befund 2.414 und die Vorgabe "
            "ZEITFENSTER-AB-2023 entstanden aus nackten "
            "Fuenftel-Median-Spannen - `messnorm` wurde ERST DANACH "
            "aufgeschlagen. Es fehlten Band, Trennschaerfe und "
            "Positivkontrolle; und dieselbe Frage war am 07.09. (S-7) "
            "bereits NORMGERECHT beantwortet. Eine Messung ohne Norm "
            "kostet nicht nur den Befund - sie erzeugt eine Vorgabe, "
            "einen Planschritt und eine Entscheidungsgrundlage, die alle "
            "nachgezogen werden muessen. ➔ DIE REIHENFOLGE VOR JEDEM "
            "MESSLAUF, NICHT NACH DEM ERGEBNIS: (1) "
            "`messnorm.standardzeile()` lesen; (2) `frageart` FESTLEGEN "
            "- markt/geometrie auf dem Messuniversum, `beitrag` auf der "
            "SELEKTIERTEN Menge, `zaehlung` beliebig aber benannt; (3) "
            "`messmenge.zeile()` in den Messkopf; (4) REGISTER "
            "nachschlagen - ist die Frage schon gemessen? (R-R11); (5) "
            "Zielgroesse aus der geschlossenen Liste, passend zur LAGE; "
            "(6) Band, Trennschaerfe und Positivkontrolle EINPLANEN, "
            "nicht nachruesten. ⚠️ Kommt ein Ergebnis ohne Band heraus, "
            "heisst das Wort dafuer HINWEIS - nie ,Befund', nie "
            ",traegt', nie ,traegt nicht'.",
            "Nutzervorgabe 13.09.; Befund 2.416-norm; messnorm.py"),
    Vorgabe("KEINE-TEILLOESUNG",
            "⚠️⚠️ NUTZERVORGABE 12.09. zum P-Scan, gilt aber allgemein: "
            "*,eigene Daten erstellen ist eine Loesung, aber hier haben wir "
            "wieder eine unfertige Loesung und Abhaengigkeit - ich waere "
            "fuer MESSEN UND SUCHEN, BIS WIR EINE LOESUNG HABEN, und dann "
            "gleich korrekt umsetzen - fertig.'* ➔ WAS DAS AUSSCHLIESST: "
            "einen Teilbau, der Daten sammelt und dann wartet ("
            ",Stufe 1 Schatten, in vier Wochen sehen wir weiter'). So "
            "entsteht eine halbe Sache im Betrieb, die niemand mehr "
            "anfasst - davon hat das Projekt genug (die alte Hebelkette, "
            "der Marktscan-Rueckstand, der leerlaufende Veto-Arm). ➔ WAS ES "
            "VERLANGT: erst die vollstaendige Loesung KENNEN - Datenweg, "
            "Messweg, Nachweis - und sie dann in EINEM Zug bauen. ⚠️ Wenn "
            "sich zeigt, dass es keine Loesung gibt, ist das ein "
            "ERGEBNIS und kein Grund, trotzdem anzufangen.",
            "Nutzervorgabe 12.09."),
    Vorgabe("AUFRAEUMEN-VOR-NEUBAU",
            "⚠️⚠️ NUTZERZUSTIMMUNG 12.09. auf eigenen Vorschlag, nachdem an "
            "EINEM Tag 12 offene Punkte liegen geblieben waren - einer davon "
            "seit Stunden geloest und nur nicht nachgetragen. DREI REGELN: "
            "(1) KEIN NEUER SCHRITT, solange mehr als DREI selbst erzeugte "
            "Befunde offen sind. Nicht als Vorsatz, sondern als Pruefung im "
            "Paket ,Plan'. (2) NACH JEDEM BAU die Befunde nachziehen, die er "
            "loest - wer baut und den Befund stehen laesst, erzeugt eine "
            "zweite Wahrheit. (3) OFFENE PUNKTE GEHOEREN VORGELEGT, NICHT "
            "ABGELEGT: was ich nicht selbst entscheiden kann, ist eine FRAGE "
            "an den Nutzer und kein Eintrag. ⚠️ Der Nutzer dazu: *,die "
            "Struktur und der Weg scheinen zu stimmen - bei den Details und "
            "Abhaengigkeiten muessen wir vorsichtig und genau vorgehen'*.",
            "Nutzerzustimmung 12.09."),
    Vorgabe("LLM-SCHIENE-GANZ",
            "⚠️⚠️ NUTZERVORGABE 12.09. zum L-Block: *,ohne Messung und "
            "Simulation nicht sinnvoll. Es sollte die GANZE LLM-Schiene "
            "geprueft werden - welche Kriterien werden PRO ROLLE bewertet "
            "und WARUM. Neuen Umbau mit ECHTEN EINSTIEGSGRUENDEN "
            "beruecksichtigen - und dies gleich fuer EIN- UND AUSSTIEG.'* ➔ "
            "VIER TEILE, und keiner davon ist ,den Prompt anpassen': (1) "
            "BESTANDSAUFNAHME je Rolle - welche Kriterien stehen heute im "
            "Prompt, und mit welcher Begruendung? Fuer Rolle A, Rolle BC und "
            "Rolle G getrennt. ⚠️ Erwartung nach 2.398: die meisten "
            "Kriterien stammen aus dem Entwurf vom August und sind nie "
            "gemessen worden. (2) ECHTE EINSTIEGSGRUENDE EINSPEISEN: die "
            "Rollen kennen `potential`, `funding`, `turnover`, `schnitt` und "
            "die Trefferquote mit KEINEM Wort (2.398) - sie raten an einem "
            "anderen Massstab als dem, an dem sie gemessen werden. (3) "
            "AUSSTIEG GLEICHRANGIG: dieselbe Frage fuer die Verkaufsseite - "
            "und dort traegt das Modell nachweislich (2.403: VERKAUFEN "
            "schlaegt den Zufall um 29 Punkte bei H10), waehrend es beim "
            "Einstieg unbelegt ist. (4) ⚠️ ERST MESSEN, DANN AENDERN: ohne "
            "Simulation ist jede Promptaenderung eine Meinung. Schritt 42 "
            "liefert die Grundlage, nicht umgekehrt.",
            "Nutzervorgabe 12.09.; Befunde 2.398, 2.403"),
    Vorgabe("SOFORT-EINTRAGEN",
            "⚠️ NUTZERVORGABE 12.09.: *,offene Punkte und Erledigungen immer "
            "gleich eintragen in Doku und Plan'*. Nicht am Ende einer "
            "Sitzung, nicht ,wenn es rund ist' - SOFORT, im selben Zug wie "
            "die Arbeit. ⚠️ Der Grund steht in der Sitzung selbst: am 12.09. "
            "kamen an einem Tag 15 Befunde und 6 Planschritte dazu; was "
            "nicht im Moment des Findens eingetragen wurde, war eine Stunde "
            "spaeter nicht mehr rekonstruierbar. Ein Befund, der nur im "
            "Gespraech steht, ist verloren. ➔ Gilt fuer BEIDES: was fertig "
            "ist, wird als fertig vermerkt - und was dabei offen bleibt, "
            "wird im selben Zug als offen eingetragen, nicht "
            "mitgeschleppt.",
            "Nutzervorgabe 12.09."),
    Vorgabe("SCHRITT-FUER-SCHRITT",
            "⚠️⚠️ NUTZERVORGABE 12.09.: *,bei der Umsetzung sorgsam Schritt "
            "fuer Schritt vorgehen und IMMER PRUEFEN, ob die Punkte "
            "VOLLSTAENDIG erledigt wurden - und dann erst zum naechsten Punkt "
            "gehen.'* ➔ WAS DAS KONKRET HEISST: (1) ein Schritt gilt erst als "
            "fertig, wenn er GEPRUEFT und GEGENGEPRUEFT ist und in der Doku "
            "steht - drei Teile, nicht einer. (2) Ein Schritt mit "
            "Restpunkten ist NICHT fertig; die Reste werden benannt, nicht "
            "mitgeschleppt (Beispiel Schritt 44: Punkte 1, 3 und 4b gebaut, "
            "2a/2b offen - er bleibt offen). (3) Kein Vorgriff auf den "
            "naechsten Punkt, solange der laufende Reste hat. ⚠️ WARUM DIE "
            "VORGABE KAM: am 12.09. wurden in vier Zuegen der Plan "
            "umgeworfen, drei Befunde revidiert und zwei eigene Vorschlaege "
            "zurueckgezogen - jeder einzelne Schritt war richtig, die "
            "SUMME war Unordnung. Ein Komma in `Schritt(44, ...)` blieb "
            "dabei stundenlang unbemerkt und liess einen offenen Schritt als "
            "erledigt gelten.",
            "Nutzervorgabe 12.09."),
    Vorgabe("REIHENFOLGE-12-09",
            "⚠️⚠️ NUTZERVORGABE 12.09., um das Klein-Klein zu beenden: "
            "*,bevor das ganze im Chaos endet - folgende Vorgehensweise: "
            "ist die deterministische Ebene sauber und stabil, dann sollten "
            "wir diesen Bereich STRAFFEN und KORREKT ABBILDEN. Die LLM "
            "Stufen benoetigen ohnehin eine komplette Ueberarbeitung, da "
            "diese ohne der neuen Bewertung arbeiten.'* ➔ DREI BLOECKE, IN "
            "DIESER REIHENFOLGE: (D1) PRUEFEN, ob die deterministische "
            "Ebene sauber und stabil ist - eine Antwort mit Belegen, keine "
            "Behauptung. (D2) STRAFFEN UND KORREKT ABBILDEN - was dort "
            "steht, muss stimmen und lesbar sein (Trichter, Mail, GUI, "
            "Plan). (L) DIE LLM-STUFEN ALS EIGENER BLOCK, komplett "
            "ueberarbeitet - Grund steht in Befund 2.398: sie kennen die "
            "neue Bewertung mit keinem Wort. ⚠️ Was daraus folgt: KEINE "
            "Einzelaenderung mehr an den LLM-Rollen, bis D1 und D2 stehen. "
            "Auch kein Nachbessern am Widerlegungspreis (2.397) - er bleibt, "
            "wie er ist, und gehoert in den L-Block.",
            "Nutzervorgabe 12.09.; Befund 2.398"),
    Vorgabe("ZWEI-STRAENGE",
            "⚠️ ABGRENZUNG des Nutzers 12.09., von ihm selbst als Gefuehl "
            "gekennzeichnet und AN CODE UND PLAN GEPRUEFT (2.393-straenge): "
            "die Bauarbeit der letzten drei Wochen gehoert zum "
            "DETERMINISTISCHEN Strang und dort zum EINSTIEG (Beitraege, "
            "Messnorm, Potential, Schwelle, r(q), Toepfe, Deckel, Paket B). "
            "Der LLM-Strang wurde im August gebaut und steht seit dem "
            "22.08. ⚠️ Was daraus folgt: (a) jeder Planschritt sagt, "
            "WELCHEM Strang er gehoert; (b) eine Schieflage im LLM-Teil ist "
            "ein VERSAEUMNIS, keine Fehlentscheidung - sie wird "
            "aufgeraeumt, nicht verteidigt; (c) der AUSSTIEG ist in BEIDEN "
            "Straengen unbearbeitet (Schritt 43).",
            "Nutzervorgabe 12.09.; Befund 2.393-straenge"),
    Vorgabe("VERKAUF-VOR-MULTIASSET",
            "⚠️ Die VERKAUFSEMPFEHLUNGEN werden angegangen UND "
            "ABGESCHLOSSEN, bevor Multiasset (Aktien etc.) beginnt. Sie "
            "sind heute der groessere Teil des Betriebs (517 seit 14.08., "
            "15-20 pro Tag) und laufen an den Stufen 10 bis 12 vorbei - "
            "ohne Potential, ohne Schwelle, ohne Deckel und ohne "
            "messbare Guete.",
            "Nutzervorgabe 12.09.: ,das sollten wir vor der Multiasset - "
            "Aktien etc. angehen und abschliessen'; Befund 2.392"),
    Vorgabe("KRYPTO-ZUERST",
            "Multiasset (Aktien, ETF, Rohstoffe, Hedge) ist NACHGELAGERT - "
            "erst nach dem Krypto-Produktivgang. A-1, A-2 und die "
            "N-19-Messbasis sind zurueckgestellt.",
            "Nutzervorgabe 10.09.", "erfuellt"),
    Vorgabe("KRYPTO-STABIL-UND-KORREKT",
            "\u26a0\ufe0f\u26a0\ufe0f Bevor weitergearbeitet wird, muss der Krypto-Teil STABIL UND FUNKTIONAL "
            "KORREKT sein. Deshalb folgt auf die Gesamtmessung (Schritt 59) ein eigener, umfangreicher "
            "Korrekturschritt (Schritt 60): Fehler beheben, die die Messung und der Betrieb zeigen, und "
            "Inhalt und Struktur der eMails - erst dann Verkauf, Akkumulation und alles Weitere.",
            "Nutzervorgabe 15.09.: ,nach dem grossen Punkt 59 einen umfangreichen Zusatzpunkt zur Korrektur "
            "von Fehlern und eMail Inhalt und Struktur einplanen - bevor wir einfach weiterarbeiten, muss der "
            "Kryptoteil stabil und funktional korrekt sein'"),
    Vorgabe("BEZUGSGROESSE",
            "Bezugsgroesse fuer `r x Kapital` ist das GESAMTKAPITAL OHNE "
            "CASH - genau `portfolio_wert_historie.wert_eur` (alle "
            "Klassen, ohne Cash). Der Drawdown-Massstab bleibt "
            "`index_wert` (Z-3).",
            "Nutzerentscheidung 10.09. (P-5)", "erfuellt"),
    Vorgabe("BEWERTUNG-NIE-BLOCKIEREN",
            "⚠️⚠️ Aenderungen im Portfolio duerfen die BEWERTUNG nicht "
            "blockieren - und schon gar nicht still. Das Potential "
            "braucht das Kapital NICHT; nur die DIMENSIONIERUNG braucht "
            "es. Faellt der Wert aus: LAUTE Meldung, kein stiller "
            "Vorgabewert.",
            "Nutzervorgabe 10.09.; N-40 'fail-soft ist fail-silent'"),
    Vorgabe("HEBEL-AUS-SPOT",
            "Der Hebel kommt VORERST aus dem Spot-Weg - nicht weil es "
            "dieselbe Frage waere (Stop, `barriere`, 2,0 Tage Dauer, "
            "taegliche Finanzierung sind reale Unterschiede), sondern "
            "weil eine eigene Bewertung heute NICHT MESSBAR ist (A1), "
            "das Aufteilen der Evidenz beide schwaecht und `r(q)` nur "
            "EINE Quote braucht. ⚠️ AUSLOESER fuer die Trennung: sobald "
            "A1 behoben ist, messen, ob ein Beitrag auf `barriere` anders "
            "wirkt als auf `bewegung_r`. Die NAHT (`Beitrag.instrumente`) "
            "ist gebaut, damit das eine Datenaenderung waere.",
            "Fachliche Bewertung 10.09. (Nutzerauftrag)", "erfuellt"),
    Vorgabe("KORRELATION-IM-DECKEL",
            "Die Korrelation des Marktes gehoert in den AGGREGAT-DECKEL "
            "(K3), nicht in eine Schrumpfung des Einzeltrade-Kelly (K1). "
            "Der Hebel gilt dem EINZELNEN Asset. Vorbedingung fuer K3: "
            "Positionsfuehrung fuer Hebel - Spot ist ein Bestand, Hebel "
            "ein Trade mit Lebenszyklus.",
            "Nutzerentscheidung 10.09. (P-4); N-40 K3"),
    Vorgabe("VIERFACHTEST",
            "Ein neuer Beitrag braucht ALLE VIER: Abdeckung (F-218) · "
            "Stabilitaet (F-217) · Unabhaengig von funding · Regel 3 "
            "laengs im eigenen Symbol (N-43c). Nicht eines davon.",
            "Entscheidung 05.09., 'Der Test, der jetzt der Massstab ist'"),
    Vorgabe("KEIN-BEITRAG-FAELLT",
            "Kein Beitrag faellt ohne konkrete Begruendung; bei "
            "untermaechtig oder nicht bewertbar ist eine LOESUNG zu suchen.",
            "Nutzervorgabe 09.09."),
    Vorgabe("REGEL-2",
            "Gebuehren gehoeren NICHT in die Bewertung - Strategie und "
            "Bewertung neutral, ohne Wirtschaftlichkeit.",
            "CLAUDE.md Regel 2; Nutzervorgabe 09.09."),
    Vorgabe("R-R9",
            "Jeder Beitragswechsel verlangt eine NEUKALIBRIERUNG der "
            "Schwelle. Deshalb steht K-3 (Schwelle) NACH den Beitraegen.",
            "R-R9"),
)

# ---- Die Lagen ------------------------------------------------------------
LAGEN = (
    # ⚠️ NUTZERVORGABE 10.09.: "Bei Krypto verbleiben KLASSEN: Core-Werte
    # fuer Akkumulation (BTC, ETH, SOL) und SPOT und Hebel." Swing ist
    # KEINE genutzte Strategie mehr; Absicherung gibt es nur ueber zwei
    # Hedge-Positionen, keine in Krypto.
    Lage("spot", "einstieg", "krypto",
         "vermessen - mindestens zwei tragende Beitraege"),
    Lage("spot", "akkumulation", "krypto",
         "Core-Werte BTC, ETH, SOL - Zielgroesse `verbilligung`, H90",
         blocker="⚠️⚠️ GESPERRT BIS PAKET 2 (Nutzerentscheidung "
                 "11.09.) - ohne Beitrag keine Nachkauf-Empfehlung "
                 "(2.374-akku). Messpaket, dann Bau als Regler (Schritte "
                 "AKKU-MESSPAKET, AKKU-BAU). Der Schalter steht fuer BTC, "
                 "ETH und SOL an (2.380-akku-schalter). ⚠️ Die Akkumulation "
                 "lief NIE - der Cooldown sperrt sie hinter der "
                 "Einstiegszelle (2.380-akku-cooldown)"),
    Lage("hebel", "einstieg", "krypto",
         "Hebel faellt dynamisch aus der Quote an, Zielzone 2-5x, nur LONG. "
         "KEINE eigene Bewertungsgruppe (Entscheidung 10.09.)",
         blocker="PAKET B baut r(q) (Schritte H-1 bis H-5). Offen "
                 "danach: A9 - die AUFLOESUNG. ✔✔ GROESSTENTEILS GELOEST "
                 "(13.09., Befund 2.432): der Sprung 1,02x -> 3,90x ist WEG. "
                 "Nachgerechnet mit demselben Aufbau wie am 08.09.: Spot · 2,00x "
                 "· 2,46x · 3,12x · 5,00x · 5,00x - eine durchgehende Leiter, "
                 "VIER von sechs Lagen in der Zielzone (damals zwei). Die "
                 "r-Klammer aus H-2 kappt die Spitze UND hebt den Boden. "
                 "⚠️ WAS BLEIBT: die zwei besten Lagen ergeben BEIDE 5,00x - "
                 "die Obergrenze, nicht die Fuenftel; "
                 "A1 - Band auf binaeren Daten, blockiert die "
                 "TRENNSCHAERFE-Frage. ⚠️ F-220 ist "
                 "ZURUECKGEZOGEN (06.09.) - NICHT mehr zitieren",
         erbt_spot=True),
    Lage("hebel", "swing", "krypto",
         "⚠️ NICHT MEHR GENUTZT - gehoert aus `ZIELGROESSE_JE_LAGE` "
         "entfernt (L2)",
         blocker="L2 - Lage existiert nur noch im Code",
         erbt_spot=True),
    Lage("absicherung", "einstieg", "hedge",
         "nur zwei Hedge-Positionen, KEINE in Krypto - zurueckgestellt",
         blocker="KRYPTO-ZUERST"),

)

# ---- Die vereinbarte Reihenfolge -----------------------------------------
# ---------------------------------------------------------------------------
# ⚠️⚠️ DIE BLOECKE (Nutzervorgabe REIHENFOLGE-12-09, 12.09.2026)
# ---------------------------------------------------------------------------
#
# *"bevor das ganze im Chaos endet - folgende Vorgehensweise: ist die
#  deterministische Ebene sauber und stabil, dann sollten wir diesen Bereich
#  STRAFFEN und KORREKT ABBILDEN. Die LLM Stufen benoetigen ohnehin eine
#  komplette Ueberarbeitung, da diese ohne der neuen Bewertung arbeiten."*
#
# Die Reihenfolge INNERHALB eines Blocks ist die Liste; die Reihenfolge der
# BLOECKE ist die Vorgabe. Ein Schritt ohne Block faellt auf - das ist
# Absicht, sonst sammelt sich hier wieder eine Halde.
# ⚠️⚠️ ALT GEGEN NEU - die zweite Achse neben dem Block (13.09.2026).
#
# NUTZERVORGABE: *"Der PLAN muss klar zwischen altem und neuem Umbau
# unterscheiden"*. Anlass war meine eigene Vermischung: ich hatte den
# Widerlegungspreis als tragend fuer den Hebel dargestellt. Richtig ist,
# dass `r(q)` - der NEUE Teil - den Hebel erzeugt, und der Stop - der ALTE
# Teil - ihn nur skaliert. In einem Bericht ohne diese Achse sieht beides
# gleich aus.
#
# ⚠️ SIE ERSETZT DEN BLOCK NICHT. Der Block sagt, WANN etwas drankommt;
# diese Achse sagt, OB gebaut oder aufgeraeumt wird. Ein Schritt kann
# dringend und trotzdem eine Reparatur sein (Schritt 46), und ein
# unwichtiger kann Neubau sein.
UMBAUZEICHEN = {
    "neu": "NEU",
    "alt": "alt",
    "beides": "a+n",
    "": "?  ",
}

BLOECKE = (
    ("ERLEDIGT", "abgeschlossen - bleibt als Spur stehen"),
    ("D-BETRIEB", "⚠️ DER DETERMINISTISCHE TEIL, der JETZT laeuft und "
                  "Empfehlungen erzeugt. Was hier faul ist, kostet heute "
                  "Geld - nicht in vier Wochen"),
    ("D-ABBILDUNG", "straffen und korrekt abbilden: der Plan, die Doku, die "
                    "Mail und die GUI muessen dasselbe sagen wie der Code"),
    ("D-BEWERTUNG", "die Messarbeit am deterministischen Teil - Beitraege, "
                    "Blocker, Schwelle. Sie geht weiter, blockiert aber "
                    "nichts anderes"),
    ("L-ROLLEN", "⚠️ DIE LLM-STUFEN, KOMPLETT - erst wenn D steht. Grund: "
                 "sie kennen die neue Bewertung mit keinem Wort (2.398)"),
    ("SPAETER", "nachgelagert nach eigener Nutzervorgabe"),
)

# ⚠️⚠️ INNERHALB EINES BLOCKS ZAEHLT DIE POSITION IN DIESER LISTE
# (Nutzerauftrag 12.09.: "Rangfolge innerhalb der Bloecke einfuehren").
#
# NICHT die Schrittnummer - die sagt, WANN ein Schritt entstanden ist, nicht
# wie dringend er ist. Schritt 49 (ein Fehler, der heute wirkt) steht vor
# Schritt 44 (halb fertig), obwohl seine Nummer groesser ist.
#
# UMSORTIEREN HEISST ZEILEN VERSCHIEBEN, und das ist Absicht: eine zweite
# Zahl neben der Schrittnummer waere eine zweite Stelle, die gepflegt werden
# muss - und die erste, die vergessen wird.

REIHENFOLGE = (
    Schritt(61, "BITPANDA-ANBINDUNG AUF DIE NEUE SCHNITTSTELLE - BESTAND, CASH, STAKING, HEBEL",
            "\u26a0\ufe0f\u26a0\ufe0f\u26a0\ufe0f NUTZERENTSCHEIDUNG 15.09.: Stufenplan 0 -> 1 -> (2, 3, 4 nach "
            "Pruefergebnis), EIGENER Schritt vor 55; *,der Umbau ist massiv und du musst hier wirklich detailliert in "
            "Code und Doku, damit wir nichts vergessen - bei den heiklen Bereichen gehen wir in Abstimmung'*. "
            "ANLASS: (a) gebundenes Cash unsichtbar (2.455-cash-gesperrt: 3.000 EUR in 11 Fusion-Limit-Orders); (b) "
            "gestakte Mengen seit 16.07. doppelt, Kapital netto rund 1.720 EUR zu hoch (2.455-bestand-gestakt, "
            "2.455-bitpanda-zuordnung); (c) die alte "
            "API ist abgekuendigt (2.455-cash-messbar). "
            "\u27a4 STUFE 0 PRUEFEN (nur lesend): 0.1 \u2714 Buchungen vollstaendig nur ueber "
            "Datumsfenster, der Cursor ist defekt (2.455-bitpanda-stufe0); 0.2 \u2714 Hebelgeschaefte "
            "enthalten; Bestand aus `asset_balance_after` je Wallet exakt nachbildbar (43 von 43); 0.3 \u2714 "
            "Zuordnung: 34 direkt, CC ueber Override, VST-US und IS0C nur ueber `asset_id`/ISIN, G2X/BW/ROL fehlen im "
            "System ganz, Katalogsymbole nicht eindeutig (2.455-bitpanda-zuordnung); NEBENBEFUND OD7H/OD7C: Ankerpreis "
            "seit 2022 eingefroren, Niveau halb so hoch (2.455-kurs-od7-eingefroren); 0.4 \u2714 Einstand: "
            "Bitpanda-Durchschnitt = investiert durch Bestand, DB-Einstand Krypto seit 11.07. veraltet, manuelle "
            "Einstaende stimmen (2.455-einstand-veraltet); 0.5 \u2714 Staking auf die Einheit erklaert: "
            "Doppelzaehlung plus Belohnungen brutto minus Provision (2.455-bitpanda-staking-ursache); 0.6 \u2714 "
            "Inventur 53 Dateien in `Basisinfos/Bitpanda_Umstellung_Inventur.md`, Vollstaendigkeit prueft das "
            "Suite-Paket BitpandaInventur - VOR JEDEM BAUSCHRITT dort nachsehen (2.455-bitpanda-inventur). "
            "\u27a4 STUFE 1 BESTAND UND CASH: 1.1 eigener lesender Zugang zur neuen API (Ampel, Maskierung, "
            "Zeitlimit, Datumsfenster statt Cursor, Katalog taeglich gepuffert; Pruefskripte biegen `db.DB_PATH` um, "
            "weil `api_health` bei jedem Abruf schreibt); 1.2 Bestand je Wert aus der neuen API "
            "- Menge = verfuegbar im Spot-Wallet, gestakt = Staking-Wallet, Hebel-Wallets getrennt, KEINE Rekonstruktion "
            "aus Transfer-Markierungen und nie aus Buchungssummen (Belohnungen sind brutto); bei Ausfall bleibt der "
            "letzte gute Stand und die Datenfrische meldet; ENTSCHEIDEN mit dem Nutzer: Excel-Import und ,umgesetzt' "
            "im Signalfenster schreiben heute `holdings` - mit der API als Wahrheit nur ohne Schluessel bzw. als "
            "Vormerkung; 1.3 "
            "Cash gesamt/verfuegbar (neue API) und gebunden samt Anzahl, Summe und aeltester offener Order (Fusion, "
            "Leseschluessel `FUSION_API_KEY`, gueltig bis 15.09.2027); 1.4 Mailzeile ,Cash … davon gebunden … frei' und "
            "Warnung mit Rufzeichen und Handlung NUR, WENN DIE SPERRE DIE EMPFEHLUNG TRIFFT (Nutzerentscheidung 15.09.), "
            "Regel A1 (Stand nennen, ab 6 h kein `!!`); 1.5 DATENKORREKTUR: Bestand richtigstellen, Index darf am "
            "Korrekturtag keinen Kursverlust zeigen, Portfoliowert-Historie RUECKWIRKEND sauber aus den taeglichen "
            "Wallet-Salden neu rechnen - ohne Kennzeichen (Nutzer: ,ein sauberer Bestand rueckwirkend waere positiv, "
            "ohne Kennzeichen und Fallstrick'; Sicherung vorher, Vorher/Nachher-Protokoll) - HEIKEL, Umsetzungsschritte "
            "vorab abstimmen; 1.6 GUI-Cashfeld L3 (Anzeige gesamt/verfuegbar/gebunden/Stand, bearbeitbar nur ohne "
            "Schluessel als eigener Wert) - Gestaltung vorab abstimmen; 1.7 Schluesselueberwachung (401 -> Mail mit "
            "Handlung; Fusion-Ablauf 30 Tage vorher erinnern); 1.8 Docstring `toepfe.cash_frei_eur` berichtigen (B1); "
            "1.9 KURSE OD7H/OD7C, VOR 1.5: Ticker auf ISIN.SG wie OD7N/OD7L (`config.yaml` am Notebook), Reihe neu "
            "verankern, pruefen welche Mails und Fakten seit 18.07. das falsche Niveau trugen, Kursalter "
            "`regularMarketTime` fuer alle Nicht-Krypto-Werte in die Datenfrische (2.455-kurs-od7-eingefroren, Klasse "
            "2.453-alterlos); 1.10 ZUORDNUNG ueber `asset_id` (ISIN im Katalog) statt Symbol; Positionen ohne "
            "Watchlist-Eintrag (G2X, BW, ROL) nie stumm verwerfen - NUTZERENTSCHEIDUNG: in die Watchlist oder nur als "
            "Bestand ins Kapital. "
            "\u27a4 STUFE 2 EINSTAND (2.455-einstand-veraltet) - Rechenregel aus den Buchungen fuer Kauf, Swap, "
            "Belohnung, Hebelrueckfluss und Einzahlung; Bitpanda-Durchschnitt nur als Gegenprobe fuer Werte ohne "
            "Teilverkauf; manuelle Einstaende bleiben - HEIKEL, abstimmen. STUFE 3 HEBEL-ABGLEICH auf die neuen "
            "Buchungen (0.2 positiv). STUFE 4 Katalog ,gelistet' auf die neue API. "
            "\u26a0\ufe0f JEDE STUFE: Suite-Paket mit Gegenprobe, Live-Test gegen eine Kopie der Sicherung, Doku "
            "(Befunde, Plan, Regelblatt Schritt 58), Pull + Neustart + Export am Notebook. Messungen sind vom "
            "Bestandsfehler NICHT betroffen, ausser: Hebelgroessen 12. bis 14.09. (fuer Schritt 59 vermerken).",
            "Nutzerentscheidungen 15.09.; Befunde 2.455-cash-gesperrt, 2.455-cash-messbar, 2.455-bestand-gestakt, "
            "2.455-bitpanda-stufe0, 2.455-bitpanda-zuordnung, 2.455-kurs-od7-eingefroren, 2.455-einstand-veraltet, "
            "2.455-bitpanda-staking-ursache, 2.455-bitpanda-inventur, 2.453-alterlos",
            block="D-BETRIEB",
            umbau="beides"),  # ersetzt eine alte Anbindung und baut Bestand/Cash neu
    Schritt(56, "DATENQUELLEN OHNE FRISCHE - DIESELBE KLASSE WIE 2.452",
            "\u26a0\ufe0f\u26a0\ufe0f\u26a0\ufe0f AUS DEM REVIEW VOR DEM ROLLOUT 14.09. (Befund "
            "2.453). Der Nutzer fragte: ,sind alle Datenquellen aktualisiert?' - "
            "NEIN. (1) ✔ GELOEST 14.09. (Weg 1, 2.453-turnover-gebaut): Schritt 49B las die "
            "Umlaufmenge am Notebook aus einer Symbolliste; jetzt holt "
            "`externe_reihen` sie taeglich von Coin Metrics in die "
            "Betriebsdatenbank, identisch zur Messung. (2) \u2714 GELOEST 15.09. (2.453-kurs-gebaut): 2.453-spy US-Referenz "
            "(Rolle A). (3) \u2714 GELOEST 14.09. (2.453-bestand-gebaut): der "
            "Fehlalarm Bestand - Frische misst jetzt den Abgleich, Jobname "
            "korrigiert. \u2714 Dazu gefunden und behoben: 2.453-veto (Export "
            "brach seit 13.09. ab), 2.453-export (Standardpruefung prueft "
            "Terminmarkt und Umlaufmenge). (4) \u2714 GELOEST 15.09.: 2.453-rohstoff bis "
            "6 Tage Rueckstand. (5) 2.453-cache: Prozess-Zwischenspeicher bis zum "
            "Neustart. (6) \u2714 GELOEST 15.09.: 2.453-kursreihe Frische je Wert. "
            "(7) Verdacht 2.453-hebelpos, 2.453-alterlos. (8) \u2714 GELOEST 15.09. (2.453-fredkey-gebaut): 2.453-fredkey: API-"
            "Schluessel im Klartext in `api_health_status` und im Export. "
            "(9) AUS DER NOTEBOOK-KONTROLLE 14.09. (2.454): 2.454-ampel GELOEST (2.454-ampel-gebaut; Folge "
            "von Schritt 54 - Ampel Binance/Bybit/OKX dauerhaft rot), "
            "2.454-laufzeit GELOEST (2.454-laufzeit-gebaut: 26,8 statt 85,5 Prozent), "
            "2.454-etfbestand AUSGEGLIEDERT in Schritt 57 (Ziel am 15.09. entschieden, nachgelagert; im Betrieb ohne Wirkung), 2.454-gemini, 2.454-rauschen, 2.454-vix; dazu "
            "2.452-boerse (OI nur von Binance) und 2.452-anlass. (10) AUS DEM REVIEW 15.09. (2.455-review) - VIER PUNKTE MIT DEM VERMERK ,NACH DEM ROLLOUT', die an erledigten Schritten hingen: 2.387-job (Portfoliowert-Job schrieb 01. bis 11.09. nicht; Sicherung 14.09. 22:40: seit dem Rollout 12.09. je Tag eine Zeile - 11.09., 12.09., 13.09.; offen nur, ob der 04:30-Lauf ohne Neustart schreibt, am naechsten Tag an der Zeile 14.09. bestaetigen), 2.387-fortschreibung (Boersentitel fortgeschrieben; Export 14.09.: 38 Symbole, 0 ohne Kurs - gegen 2.453-kurs-gebaut pruefen), \u2714 GELOEST 15.09. 2.382-rundung (2.455-hebelstufen-gebaut: ein ungerundeter Hebel, in der Mail die einstellbaren Stufen, die untere hervorgehoben). (11) 2.455-refreshzeit: Kursreihen-Tagesjob 24 h nach App-Start statt fester Uhrzeit. (12) \u26a0\ufe0f\u26a0\ufe0f AUSSTEHENDE NOTEBOOK-KONTROLLEN (Nutzervorgabe 15.09.: ,anstehende Pruefungen nicht vergessen und sauber in Plan und Memory mitfuehren') - ein Punkt gilt erst als erledigt, wenn er am Notebook bestaetigt ist: (K1) Pull von `2.455-hebelstufen-gebaut` mit Neustart UND Export nach rund 30 Minuten (Nutzervorgabe 15.09.: ,alle groesseren Aenderungen sollten auf Fehler im Betrieb durchgeprueft werden, sonst verschleppen wir Fehler') - geprueft wird: seit dem Start kein neuer ERROR/Traceback in rollen_lauf, entscheidungsrechnung, signal_mail, hebelfuehrung; jeder Umlauf ,0 Fehler'; keine ,uebersprungen'-Zeile der Hebelfuehrung oder Positionsfuehrung; Jobfehler nur mit bekannter Ursache; (K2) Export 16.09. NACH 06:45: 05:30 erster Lauf `refresh_aktien_ohlc` nach neuer Regel, ggf. Zeilen ,Kursluecke ...' (2.455-kapitalkurse-gebaut); (K3) 06:30 `Tageswert 2026-09-15` OHNE fortgeschriebene Boersentitel; (K4) 2.387-job - die Zeile 15.09. schreibt der 06:30-Lauf OHNE Neustart; (K5) in den Tagen danach die Selbstpruefung ,Schlusskurs-Rueckfall ... ersetzt' mit Abweichung unter 0,5 Prozent; (K6) die erste echte Hebelmail nach dem Pull zeigt die Stufen wie am Pruefstand; (K7) Hebel-Abgleich und Datenfrische weiter ohne Alarm. Ablauf und erwartete Zeilen: Basisinfos/Rollout_Notebook_14_09.md, Nachtraege 15.09. "
            "\u27a4 Reihenfolge und Loesungswege EINZELN mit dem Nutzer. \u27a4 NUTZERENTSCHEIDUNG 15.09. (,Krypto sollte als Gesamtes stabil laufen'): REIHENFOLGE DES RESTS in drei Gruppen - (G1) KAPITAL UND HEBEL: \u27a4 Bestand, Cash und Bitpanda-Anbindung AUSGEGLIEDERT in Schritt 61 (15.09.); \u2714 GELOEST 15.09. 2.453-hebelpos (2.455-hebelabgleich-gebaut: Mail ab 1 Stunde, Stempel, Mailzeile, Datenfrische, Export), \u2714 GELOEST 15.09. 2.387-fortschreibung (2.455-kapitalkurse-gebaut: Job 05:30, Eingabepruefung, Schlusskurs-Rueckfall handelsplatzgenau), 2.382-rundung, 2.387-job; (G2) ALTE FAKTEN ANS MODELL: 2.453-alterlos, 2.453-cache, 2.452-boerse, 2.452-anlass, NEU 2.455-rekonstruktion-heute (rekonstruierte Reihe schreibt eine Kerze mit heutigem Datum), NEU 2.455-cash-gesperrt (Fusion sperrt rund 2.940 EUR, die Schnittstelle zeigt es nicht; GUI-Cashfeld wird ueberschrieben); Punkt 2.453-alterlos wird Punkt fuer Punkt mit dem Nutzer entschieden (Cash: A1, B1, C3 am 15.09.); (G3) BETRIEBSHYGIENE: NEU 2.455-exportveto (Fehlalarm der Standardpruefung bei Veto-Schatten-Zeilen), 2.454-gemini, 2.454-rauschen, 2.454-vix, \u2714 2.455-refreshzeit GELOEST 15.09. (Job 05:30, 2.455-kapitalkurse-gebaut). Jeder Punkt einzeln: pruefen, gegenpruefen, doku.",
            "Befunde 2.453, 2.453-turnover-gebaut, 2.453-kurs-gebaut, 2.453-bestand, "
            "2.453-rohstoff, 2.453-cache, 2.453-kursreihe, 2.453-hebelpos, "
            "2.453-alterlos, 2.453-fredkey-gebaut, 2.453-bestand-gebaut, 2.453-veto, "
            "2.453-export, 2.454-ampel-gebaut, 2.454-laufzeit-gebaut, "
            "2.454-gemini, 2.454-rauschen, 2.454-vix, 2.452-boerse, 2.452-anlass, 2.455-review, 2.455-hebelabgleich-gebaut, 2.455-kapitalkurse-gebaut, 2.455-rekonstruktion-heute, 2.455-exportveto, 2.455-nb-15-09, 2.455-hebelstufen-gebaut, 2.455-cash-gesperrt, 2.455-cash-messbar, 2.455-bestand-gestakt, 2.387-job, 2.387-fortschreibung, 2.382-rundung, 2.455-refreshzeit",
            block="D-BETRIEB",
            umbau="alt"),  # Reparatur
    Schritt(55, "ENTSCHIEDENE UMSETZUNGEN AUS DEN POSITIONSFAELLEN (14.09.)",
            "\u27a4 NUTZERENTSCHEIDUNGEN 14.09. (Befunde 2.451-*, "
            "Basisinfos/Plan_Asset_Lebenszyklus_14_09.md) - ENTSCHIEDEN, NICHT "
            "GEBAUT: (1) Waechter ,gehalten, aber nicht beurteilt' jetzt "
            "(2.451-absicherung: DBPK seit 22.08. ohne Urteil), R2 in Schritt 33; "
            "(2) eine Bestandsaenderung hebt Cooldown/Anlass einmal auf "
            "(2.451-sofort); (3) die taegliche Ausstiegsmail auf POSITIONEN statt "
            "offene Signale (2.451-verkauf); (4) Verkaufsbestaetigung automatisch, "
            "aber nur wenn nicht durch Staking erklaert, gespeichert wird die "
            "VERKAUFTE Stueckzahl (2.451-bestaetigung); (5) Phantombestand melden "
            "(2.451-phantom); (6) ,im Topf frei' kennzeichnen, spaeter ueber die "
            "Kaufverknuepfung zaehlen (2.451-topf); (7d) \u2714 GEBAUT 15.09. (2.455-hebelabgleich-gebaut): Mail bei anhaltendem "
            "Ausfall des Hebel-Abgleichs mit aussagekraeftigem Betreff; (7c) ein "
            "Asset mit Spot- und Hebelposition sauber als ZWEI Positionen - "
            "Gestaltung vor dem Bau abstimmen (2.451-hebel); VSN aus der "
            "Stummzeile ausnehmen (2.442-vier). Nebenpunkte: veralteter Test in "
            "`pruefe_marktrang.py` (2.419-saetze); Planpruefung verschaerfen - Review 15.09.: 19 aeltere offene Messfragen ohne Schritt (Liste in 2.455-review) beim Verschaerfen einordnen; Suite-Hygiene 2.455-suite (dauerhaft erwartete rote Zeilen, Nicht-Krypto-Messbasis); "
            "(2.453-plan); Desktop-DB-Schreibzugriff klaeren (2.453-desktopdb). "
            "\u27a4 Umsetzungsschritte vor dem Bau im Detail abstimmen.",
            "Befunde 2.451-absicherung, 2.451-sofort, 2.451-verkauf, "
            "2.451-bestaetigung, 2.451-phantom, 2.451-topf, 2.451-hebel, "
            "2.442-vier, 2.419-saetze, 2.453-plan, 2.453-desktopdb, 2.455-suite",
            block="D-BETRIEB",
            umbau="neu"),
    Schritt(54, "TERMINMARKT-FAKTEN EINGEFROREN - REPARATUR",
            "\u26a0\ufe0f\u26a0\ufe0f\u26a0\ufe0f GEFUNDEN 14.09. (Befunde 2.452, "
            "2.452-alt, 2.452-anlass). Seit 12.09. 03:28 schreibt niemand "
            "`open_interest_snapshot` (einziger Schreiber war das "
            "stillgelegte Screening), bei 13 Werten schon seit Juli. "
            "`positionierung` liest ohne Altersgrenze - Rolle BC und Rolle G "
            "bekommen eingefrorene Terminmarkt-Saetze als ,letzte 8 Stunden', "
            "und das Modell begruendet Urteile damit. Reparaturwege wurden "
            "EINZELN mit dem Nutzer entschieden. "
            "➤ NUTZERENTSCHEIDUNG 14.09.: Paket aus (1) Sammeln vom Screening "
            "getrennt, fuer ALLE Kryptowerte der Kette, (2) Altersgrenze und "
            "Zeitfenster aus der Uhrzeit in `positionierung`, (3) Frische je "
            "Wert mit Mail bei anhaltendem Ausfall. Offen: die Grenzen - "
            "gemessene Luecken seit 01.08. vorgelegt (Lesegrenze vs. Meldegrenze). "
            "➤ NUTZERENTSCHEIDUNG 14.09.: Lesegrenze 2 h, Meldegrenze 6 h, "
            "EIGENER Job (nicht im Job der Rollen-Kette); Einzelwert-Grenze 24 h. "
            "Live-Probe 14.09.: 39 von 43 Kryptowerten haben Terminmarkt-Daten "
            "(37 davon bei Binance, die `positionierung` liest - 2.452-boerse), ohne: CANTON, SUPRA, "
            "VSN, XNO; ein Durchlauf 143 s. Umsetzungsschritte vorgelegt. "
            "\u27a4 14.09.: A (alte Warnung ersetzt), B (keine Entwarnung), "
            "C (Vergleich 100 h) entschieden. GEBAUT UND AM DESKTOP GEPRUEFT "
            "(2.452-gebaut): eigener Job, Lesegrenze, Meldung, Suite-Paket "
            "TerminmarktDaten. \u2714 AM NOTEBOOK BESTANDEN 14.09. abends (2.454): "
            "Pruefskript 8 von 8 OK, Export ohne Auffaelligkeit, Log sauber. Die "
            "Nebenbefunde 2.452-boerse und 2.452-anlass und die Folge 2.454-ampel "
            "traegt Schritt 56.",
            "Befunde 2.452-gebaut, 2.454 (2.452 und 2.452-alt abgeloest)",
            fertig=True, block="D-BETRIEB",
            umbau="alt"),  # Reparatur, kein Neubau
    Schritt(47, "DER STOP AUF GEMESSENE GRUNDLAGE - VORBEDINGUNG FUER "
            "ALLES AM HEBEL",
            "⚠️⚠️ ERGEBNIS DER WIDERLEGUNGSPREIS-MESSUNG (Befunde 2.397, "
            "2.400). Der Hebel entsteht aus ZWEI Groessen: `hebel = (risiko "
            "/ STOP) / 500`. Die Quote ist gemessen (r(q), halbes Kelly), "
            "DER STOP NICHT. Er kommt in 81,5 %% der Faelle aus einer "
            "Modellangabe, und wo die fehlt, aus `_stop_aus_atr` mit 2,5 x "
            "ATR - was bei Krypto regelmaessig in den Deckel von 25 %% "
            "laeuft. ⚠️ EIN STOP VON 25 %% MACHT JEDEN HEBEL UNMOEGLICH: "
            "ueber die ganze r(q)-Spanne ergibt er 0,72x bis 1,80x. ➔ ZU "
            "TUN: (1) die vorhandenen Messungen zusammentragen - der "
            "Rauschbefund (0,75 ATR wird in 57,3 %% der Faelle binnen fuenf "
            "Handelstagen getroffen, 26.910 Anker) und die Ausstiegsregel "
            "(495 aufgeloeste Signale, +0,092 R). (2) Daraus die Stopweite "
            "je Anlageklasse BEGRUENDEN statt sie zu setzen - `stop_ziel_atr` "
            "2,5 und `stop_max_relativ` 25 %% stehen heute ohne eigenen "
            "Befund in `GRENZEN`. (3) Gegen die echten Faelle rechnen, "
            "vorher und nachher, dieselbe Funktion zweimal - so wie "
            "`messe_widerlegung.py` es vormacht. ⚠️⚠️ ERST WENN DAS STEHT, "
            "kann der Widerlegungspreis aus der Rechnung genommen und zur "
            "reinen Gegenbewertung in der Mail werden, wie der Nutzer es "
            "will. Vorher wuerde die Kette gar keinen Hebel mehr erzeugen. "
            "✔✔ STAND 13.09. - TEILE (1) UND (3) SIND DA, UND SIE DREHEN "
            "DIE ANNAHME DIESES SCHRITTS UM. "
            "(1) DIE MESSUNG GIBT ES SCHON: `messe_stop_abstand_baender.py` "
            "loest genau die Falle, an der zwei Vormessungen gebrochen sind "
            "- KEIN Aufloesungsfilter, jedes Signal wird gegen die echte "
            "Preisreihe neu simuliert. Gelaufen gegen den NB-Export, 1.446 "
            "Signale, H7: nur ZWEI Baender schliessen die Null aus - unter "
            "2 % SCHADET der Stop (-0,564 [-0,965;-0,029]), ueber 12 % "
            "TRAEGT er (+0,230 [+0,014;+0,366]). Dazwischen nichts "
            "trennbar (2.431). "
            "(3) VORHER/NACHHER GERECHNET: Stop 12 % -> 3,75x · 15 % -> "
            "3,00x · 20 % -> 2,25x · 25 % -> Spot. ⚠️⚠️ DAMIT IST DIE "
            "ANNAHME OBEN FALSCH: ein weiter Stop macht den Hebel NICHT "
            "unmoeglich, das gilt erst am DECKEL. Zwischen 12 und rund "
            "22 % erlaubt er 2 bis 3,75x UND liegt im einzigen tragenden "
            "Band (2.431-fenster). ➔ DER HEBEL BRAUCHT DEN "
            "WIDERLEGUNGSPREIS NICHT - er braucht einen Stop zwischen 12 "
            "und 22 %. "
            "⚠️ HEUTE LIEGT ER NICHT DORT: `stop_ziel_atr` = 2,5 trifft bei "
            "BTC rund 7,5 %, und 1.195 von 1.446 Signalen (83 %) liegen "
            "unter 12 %. "
            "➔ TEIL (2) IST DAMIT KEINE MESSUNG MEHR, SONDERN EINE "
            "ENTSCHEIDUNG und sie gehoert dem Nutzer: `stop_ziel_atr` von "
            "2,5 auf einen Wert im tragenden Band anheben? Das aendert die "
            "Hebelhoehe JEDES Signals und die Stopweite jeder Empfehlung. "
            "⚠️ WAS VORHER NOCH FEHLT, damit es ein BEFUND ist und nicht "
            "nur ein starker Hinweis: Trennschaerfe und Positivkontrolle. "
            "Band und Basislinie sind da, die Menge sind Signale mit Zonen "
            "statt des Messuniversums (Vorgabe "
            "MESSSTANDARD-VOR-DER-MESSUNG). "
            "✔ Paket `Stopgrundlage`, 7 Pruefungen: die vier Grenzen stehen "
            "fest verdrahtet, der offene Punkt steht IM CODE bei der Zahl, "
            "und die Hebelrechnung an den gemessenen Baendern ist "
            "festgehalten. Gegengeprueft mit einer verstellten Grenze. "
            "⚠⚠⚠ NACHGETRAGEN 13.09. - TRENNSCHAERFE UND POSITIVKONTROLLE "
            "KIPPEN DAS ERGEBNIS OBEN. Auf Nutzerauftrag nachgezogen, "
            "ZENTRIERT gepflanzt: Trennschaerfe 0,40 R in vier Baendern, "
            "0,20 R in einem - und in ZWEI Baendern (2-3 %, 3-5 %) findet "
            "die Anlage selbst 0,40 R in 0 bzw. 1 von 5 Ziehungen nicht. "
            "Der groesste gemessene Effekt betraegt +0,230 R und liegt "
            "damit UNTER der Aufloesung (2.433). "
            "⚠⚠ UND EIN ZWEITER FEHLER AN DERSELBEN TABELLE: ich hatte "
            "gegen die NULL verglichen statt gegen das NULLMODELL. Das "
            "Nullmodell ist die BASISLINIE (derselbe Stop, dasselbe CRV, "
            "zufaellige Einstiege) - und gegen sie trennt sich KEIN "
            "einziges der sechs Baender (2.433-nullmodell). "
            "➤ DAMIT IST MEINE EMPFEHLUNG ZURUECKGEZOGEN: `stop_ziel_atr` "
            "darf auf dieser Grundlage NICHT geaendert werden, es gibt kein "
            "nachweislich tragendes Band. "
            "✔ WAS BLEIBT: das Werkzeug ist jetzt vollstaendig (Band, "
            "Basislinie, Trennschaerfe, Positivkontrolle, und die "
            "Zentrierungsprobe laeuft in JEDEM Lauf mit); die zwei Zahlen "
            "ohne eigenen Befund sind unveraendert benannt; und der "
            "Zusammenhang Stopweite → Hebel gilt weiter, denn er ist "
            "Arithmetik. ➤ WAS ES BRAUCHT: mehr Faelle oder eine feinere "
            "Zielgroesse. Mit 251 Faellen im breitesten Band und 0,40 R "
            "Aufloesung ist die Frage HEUTE NICHT ENTSCHEIDBAR - und das "
            "ist ein Ergebnis, kein Zwischenstand (2.433-folge). "
            "✔✔✔ UND DAMIT WAR ES NICHT ERLEDIGT - NUTZERVORGABE "
            "KEIN-BEITRAG-FAELLT: *,wenn er faellt, dann suchen wir eine "
            "Loesung!!‘*. Der Satz ,mit den heutigen Daten nicht "
            "entscheidbar‘ war ein Zwischenstand, kein Ergebnis. "
            "➤ DIE URSACHE, MECHANISCH (2.434): der Block-Bootstrap zieht "
            "ueber SYMBOLE - und das ist richtig, mehrere Signale desselben "
            "Symbols teilen dieselbe Kursreihe. Die wirksame Stichprobe ist "
            "damit die SYMBOLZAHL: 251 Faelle im breitesten Band sind 21 "
            "SYMBOLE. Die KI-Breite folgt genau dem (1,695 bei 13 Symbolen, "
            "0,351 bei 21). "
            "➤ DIE LOESUNG (2.434-loesung), und sie ist die des Nutzers: "
            "HISTORISCH SIMULIEREN statt Signalstichprobe. ⚠ `messnorm` "
            "verlangt es ohnehin - frageart `geometrie` heisst Menge = "
            "MESSUNIVERSUM, nicht Signale. Zwei Hebel: (1) 536 Symbole "
            "statt 21, Bandbreite skaliert mit 1/Wurzel(Symbole); (2) "
            "GEPAART - jeder Anker mit JEDER Weite, dieselbe Lage nur "
            "anderer Stop, damit faellt die Auswahl als Stoerquelle weg. "
            "✔ VORABTEST GELAUFEN (60 Symbole, 2.400 gepaarte Anker): "
            "Aufloesung von 0,40 R auf 0,03 bis 0,07 R - Faktor 6 bis 13. "
            "⚠⚠ UND DAS BILD AENDERT SICH (2.434-vorschau): enge Stops "
            "schaden weiterhin (2 %: -0,132), aber ,ueber 12 % traegt‘ "
            "reproduziert NICHT - statt +0,230 R stehen dort +0,019 R. Der "
            "grosse Wert der Signalstichprobe war mit hoher "
            "Wahrscheinlichkeit AUSWAHL. "
            "➤ WAS ZU BAUEN IST, in EINEM Zug (KEINE-TEILLOESUNG) - "
            "Datenweg, Messweg, Nachweis sind bekannt: DATENWEG "
            "`messe_eigenschaft_beitrag.lade()`, 536 Krypto-Reihen, "
            "Median 1.429 Handelstage. MESSWEG je Anker und je Weite "
            "Ziel-vor-Stop mit Mark-to-Market, KEIN Aufloesungsfilter; "
            "gepaart ueber die Weiten; Tagesklammer wie die Norm sie "
            "verlangt; beide Richtungen; mehrere Horizonte. NACHWEIS "
            "Basislinie, Block-Bootstrap ueber Symbole, Trennschaerfe mit "
            "ZENTRIERT gepflanzten Staerken und Positivkontrolle ueber 5 "
            "Ziehungen - alles vier steht seit heute in "
            "`messe_stop_abstand_baender.py` und wird "
            "wiederverwendet, nicht nachgebaut. "
            "\u2714\u2714\u2714 GEBAUT, GELAUFEN, GEGENGEPRUEFT - 13.09. ABENDS. "
            "`messe_stopweite_historisch.py` misst historisch und GEPAART: 534 "
            "Symbole der Messmenge V1, 32.040 Anker je Lauf, JEDER Anker mit "
            "JEDER der sechs Weiten, drei Horizonte, beide Richtungen. Die "
            "Aufloesung faellt von 0,40 R auf 0,010 bis 0,020 R (2.435). "
            "\u27a4 DAS ERGEBNIS, und es ist das UMGEKEHRTE der Annahme oben: "
            "ein Feinraster in Ein-Prozent-Schritten zeigt ein INNERES MAXIMUM "
            "bei 7 bis 9 %% - 5 %% -0,0354 \u00b7 6 %% -0,0177 \u00b7 7 %% -0,0013 \u00b7 "
            "[8 %% Bezug] \u00b7 9 %% -0,0046 \u00b7 10 %% -0,0127 \u00b7 12 %% -0,0182. "
            "`stop_ziel_atr` = 2,5 trifft bei Krypto rund 7,5 bis 8 %% - also "
            "MITTEN HINEIN. \u2714 DIE ZAHL BLEIBT UNVERAENDERT und hat zum "
            "ersten Mal einen eigenen Befund (2.435-optimum). "
            "\u26a0\u26a0 DAMIT IST AUCH DER SATZ AUS TEIL (3) OBEN WIDERLEGT: "
            "der Hebel braucht KEINEN Stop zwischen 12 und 22 %% - dort wird "
            "das Ergebnis messbar SCHLECHTER. Die Rechnung 12 %% -> 3,75x "
            "stimmt weiter, sie ist Arithmetik; sie war nie ein Grund "
            "aufzuweiten. 2.431 und 2.431-fenster sind abgeloest. "
            "\u2714\u2714 EHRENRUNDE (Nutzerauftrag, `pruefe_stopweite_gegen.py`, "
            "acht Proben): Aufloesung feiner nachgemessen \u00b7 "
            "Aufloesungsquote je Weite \u00b7 Gleichtagsregel umgedreht \u00b7 drei "
            "Saaten \u00b7 drei Bezugspunkte samt Additivitaetsprobe (2,8e-17) \u00b7 "
            "drei Zeitfenster \u00b7 R-R11 gegen 2.431 \u00b7 Feinraster. "
            "\u26a0\u26a0\u26a0 UND SIE HAT EINEN FEHLSCHLUSS GEFANGEN "
            "(2.435-gleichtag): ,enge Stops schaden' haengt VOLLSTAENDIG an "
            "der Annahme, dass bei einer Kerze, die Stop UND Ziel beruehrt, "
            "der Stop zuerst kommt. Umgedreht steht bei 2 %% +0,309 statt "
            "-0,240. Aus TAGESDATEN ist die enge Seite nicht entscheidbar - "
            "es braeuchte Intraday-Kerzen. Fuer die Entscheidung folgenlos: "
            "die WEITE Seite ist sich unter beiden Regeln einig. "
            "\u2714\u2714\u2714 UND DER DECKEL IST AUCH ENTSCHIEDEN - "
            "`stop_max_relativ` = 25 %% BLEIBT (2.437). Ich hatte ihn als offenen "
            "Punkt vorgelegt mit dem Satz, er lasse messbar schlechtere Weiten zu. "
            "\u26a0\u26a0 DAS WAR FALSCH, und der Nutzer hat es aufgedeckt: die "
            "Zahl -0,041 R stammt aus der UNBEDINGTEN Messung ueber ALLE Anker - "
            "der Deckel trifft aber nur die schwankungsstarken Lagen. "
            "\u27a4 DORT NACHGEMESSEN (ATR-Rueckfallstop ueber 25 %%, 30.297 "
            "Anker, 520 Symbole, gepaart gegen die 25 %%, die diese Lagen HEUTE "
            "bekommen): LONG bringt enger NICHTS - 8 %% +0,002 \u00b7 10 %% +0,007 "
            "\u00b7 12 %% +0,003 \u00b7 20 %% -0,005, JEDES Band schliesst die Null "
            "ein. Und SHORT wuerde SCHADEN - 8 %% -0,026 \u00b7 12 %% -0,029 \u00b7 "
            "20 %% -0,010, alle fuenf trennbar unter null. Der Grund ist "
            "einsichtig: ein 8-%%-Stop ist dort rund 0,8 ATR und wird vom Rauschen "
            "abgeraeumt. "
            "\u27a4 UND ER IST OHNEHIN KEINE EINGESTELLTE WEITE, SONDERN EINE "
            "NOTBREMSE (2.437-grund, Nutzerhinweis 13.09.: *,der Deckel war eine "
            "vorlaeufige Absicherung'*). Der Code sagt es woertlich: *,ein Stop "
            "von 40 %% faellt durch jede Untergrenze und ruiniert trotzdem die "
            "Rechnung'*. Sie faengt, was sie fangen soll - 7 von 1.446 "
            "Modellzonen (0,5 %%) liegen ueber 25 %%. Eine Senkung auf 12 %% wuerde "
            "252 von 1.446 treffen (17,4 %%): aus der Notbremse wuerde still die "
            "Stopregel fuer jedes sechste Signal. "
            "\u26a0\ufe0f WAS STATTDESSEN OFFEN BLEIBT (2.437-atr): nicht der "
            "Deckel, sondern der ATR-Rueckfall im MITTELFELD. Bei Lagen mit "
            "ATR-Stop 15 bis 25 %% - 47 %% aller Handelstage, und sie werden NICHT "
            "gedeckelt - waere enger LONG messbar besser (8 %%: +0,035, Band ueber "
            "null), SHORT dagegen flach. Eigener Schritt, eigene Gegenpruefung.",
            "Nutzervorgabe 12.09.; Befunde 2.397, 2.400, 2.400-hebel; Ergebnis 2.435, 2.435-optimum, 2.435-gleichtag, 2.435-deckel",
            fertig=True,
            block="D-BETRIEB",
            umbau="beides"),  # ERSETZT die alte Geometrie aus Modellangaben durch einen gemessenen Stop - Vorbedingung des neuen Hebels
    Schritt(1, "N-46a",
            "Zirkulaerer Verschub als Laengs-Nullpunkt GEBAUT - P1/P2/P3 "
            "sauber (gepflanzt 0,20 R -> +0,0420 gefunden).",
            "n98_n46_laengs_nullpunkt.py; Befund 2.275",
            fertig=True,
            umbau="neu"),  # N-46a - Beitragsmessung des Umbaus
    Schritt(2, "N-46b",
            "✔ ENTSCHIEDEN: die TAGESMISCHUNG gewinnt - Fehlalarm 1,0/"
            "4,0 % gegen Soll 2,5 %, Fundquote auf 6 von 8 Sprossen "
            "besser. N-46 ist mit dem VORHANDENEN Werkzeug geloest.",
            "Befund 2.282 / 2.282-fund", fertig=True,
            umbau="neu"),  # N-46b - Beitragsmessung des Umbaus
    Schritt(3, "A2/AKKU",
            "✔ GELOEST: Permutationstest statt Bootstrap-Band. `schnitt` "
            "traegt (+0,0470, 481 Symbole, p 0,000) - der erste gemessene "
            "Beitrag fuer die Akkumulationslage.",
            "Befund 2.286 / 2.286-schnitt", fertig=True,
            umbau="neu"),  # A2/AKKU - Akkumulationsmass
    Schritt(4, "VIERFACHTEST",
            "⚠️ GEMESSEN, ABER NICHT ERFUELLBAR: Kriterium 4 liefert bei "
            "ALLEN Kandidaten untermaechtig - auch bei der Kontrolle. Es "
            "ist falsch konstruiert (Signifikanztest statt "
            "Streuungszerlegung, Methodik 2.101).",
            "Befund 2.292 / 2.292-fehlkonstruktion", fertig=True,
            umbau="neu"),  # der Vierfachtest ist die Huerde des Umbaus
    Schritt(5, "V1 KRITERIUM 4",
            "✔ ERLEDIGT: Kriterium 4 ist ERFUELLBAR. Die meisten "
            "Kandidaten bestehen es ROH - `schnitt` mit 25,4 %. ⚠️ Der "
            "Befund trifft den BESTAND: `turnover` ist zu 51,2 % eine "
            "Asset-Eigenschaft.",
            "Befund 2.297 / 2.298", fertig=True,
            umbau="neu"),  # V1 Kriterium 4
    Schritt(6, "V7 KRITERIUM 3",
            "⚠️ GEMESSEN: nur EIN gedecktes Urteil - `turnover` ist "
            "unabhaengig von `funding` (2 gegen 0 Faecher). Fuer die "
            "KANDIDATEN nicht entscheidbar: die Schichtung kostet die "
            "Macht.",
            "Befund 2.302 / 2.303", fertig=True,
            umbau="neu"),  # V7 Kriterium 3
    Schritt(7, "V8 ZWEI SCHICHTEN",
            "⚠️ WIDERLEGT: mit zwei Faechern ist KEIN Urteil gedeckt - "
            "mit fuenf war es eines. Nicht die Macht war der Engpass, "
            "sondern die ZAEHLMETRIK. ✔ Die Vorfrage ist geloest (auf "
            "20 % tragen alle drei Kandidaten).",
            "Befund 2.308", fertig=True,
            umbau="neu"),  # V8 zwei Schichten
    Schritt(8, "V2 N-73 AUF DEN BESTAND",
            "✔ GEMESSEN: `funding` besteht N-73 NICHT (2 von 3). "
            "`schnitt` besteht sie BESSER als jeder registrierte "
            "Beitrag - die Zweierlei-Mass-Sorge ist umgekehrt "
            "beantwortet.",
            "Befund 2.312 / 2.312-antwort", fertig=True,
            umbau="neu"),  # V2/N-73 - der Bestand an derselben Huerde gemessen
    Schritt(9, "V9 GESCHICHTET ALS EIN BEFUND",
            "✔ ERLEDIGT: Kriterium 3 ist beantwortet - `funding` erklaert "
            "bei KEINEM Kandidaten etwas. ⚠️ Der Zusatz ,`schnitt` hat "
            "damit ALLE VIER Kriterien' (2.319) ist am 10.09. ABGELOEST "
            "durch 2.325 - er hat DREI.",
            "Befund 2.316 · 2.319 abgeloest durch 2.325", fertig=True,
            umbau="neu"),  # V9 geschichtet
    Schritt(10, "S-7 GEKLAERT",
            "✔ ERLEDIGT: S-7 dreifach reproduziert und nur in seinem "
            "eigenen Wortlaut bestaetigt (,unentschieden'). ⚠️⚠️ DABEI "
            "fiel KRITERIUM 2 auf: `n102:135` gab ,Band haelt die Null' "
            "als ✔ aus - je breiter das Band, desto sicherer. Richtig "
            "gemessen FAELLT `schnitt` daran.",
            "Befunde 2.321 bis 2.330", fertig=True,
            umbau="neu"),  # S-7 Zeitstabilitaet der Beitraege
    Schritt(11, "V11 SCHNITT50",
            "⚠️⚠️ ERLEDIGT, ABER NEGATIV: `schnitt50` besteht N-73 NICHT "
            "(2 von 3; Kriterium 1 mit 100 %% erfuellt). ⚠️⚠️⚠️ Und der "
            "AUSWAHL-TEST hat die Zuschreibung aus 2.325 gekippt: "
            "`schnitt`s Instabilitaet gehoert der AUSWAHL, nicht ihm - "
            "Faktor 6 bei VIERMAL schaerferem Test. BILANZ: es gibt "
            "KEINEN dritten Beitrag.",
            "Befunde 2.331 bis 2.339", fertig=True,
            umbau="neu"),  # V11 schnitt50
    Schritt(12, "S-1 SAMMLUNG ABSICHERN",
            "✔ ERLEDIGT 11.09.: die drei Messquellen sind in "
            "`datenfrische` registriert (Rolle M), und ein Ausfall wird "
            "GEMELDET statt nur geloggt - nach JOB gruppiert, mit "
            "Handlungsanweisung. ⚠️ Offen: sie haben weiter keinen Job "
            "und keine `fetched_at`-Spalte; der Abrufstand kommt aus der "
            "Dateizeit.",
            "Befunde 2.358/2.359", fertig=True,
            umbau="alt"),  # S-1 - eine Sammlung, die still abriss; Reparatur
    Schritt(13, "S-2 STILLER AUSFALL",
            "✔ ERLEDIGT 11.09.: ein Ausfall ist keine Messbasisluecke "
            "mehr. Teilausfall wird genannt statt weggelassen, "
            "Totalausfall nennt den AUSFALL statt der falschen Ursache. "
            "Vier Faelle, fuenf Dauerpruefungen.",
            "Befunde 2.357", fertig=True,
            umbau="alt"),  # S-2 - stiller Ausfall der bestehenden Anlage
    Schritt(14, "S-3 JOBSPUR",
            "✔ ERLEDIGT 11.09.: jeder Job hinterlaesst eine Spur - der "
            "Ereignis-Horcher lauscht jetzt auch auf EVENT_JOB_EXECUTED. "
            "Vorher fuehrten nur 6 von 21 eine Zeile in `job_laeufe`, und "
            "nach einem Ausfall war nicht feststellbar, was gefehlt hat. "
            "Zentral statt fuenfzehn Kopien.",
            "Befunde 2.360", fertig=True,
            umbau="alt"),  # S-3 - fehlende Jobspur; Reparatur
    # ================================================================
    # AB HIER: DER PRODUKTIVGANG - PAKET B (Nutzerentscheidung 11.09.2026)
    #
    # > "meine Prioritaet liegt bei 1 Hebel 2 Spot 3 Akkumulation -
    # >  zumindest Hebel und Spot muessen sauber funktionieren."
    # > "ja Paket B, Deckel 5x, Rest wie empfohlen"
    #
    # ⚠️⚠️ WARUM DER FRUEHERE PLAN FALSCH WAR: er stellte den Rollout VOR
    # Hebel und Akkumulation ("der Rollout haengt nicht an der
    # Akkumulation"). Die Vorgabe KRYPTO-ZUERST heisst aber Krypto GESAMT.
    # Beide Luecken standen in der Doku (2.174-ist seit 08.09., null
    # Beitraege der Akkumulation) - sie waren nur nicht als Showstopper
    # benannt (Befund 2.374).
    #
    #   PAKET B   Hebel und Spot sauber, Akkumulation GESPERRT -> Rollout
    #   PAKET 2   Akkumulation messen und bauen -> zweiter Rollout
    # ================================================================
    Schritt(15, "E2E VOR DEM ROLLOUT",
            "✔ ERLEDIGT 11.09.: `simuliere_kette.py` gegen eine KOPIE der "
            "NB-Sicherung - also gegen das alte Schema, auf das der "
            "Rollout trifft. Alle fuenf Gruppen, 0 Fehler; Zellen-Pfad, "
            "Positionsfuehrung und Vorfilter nachgewiesen; die erste "
            "Krypto-Mail end-to-end (ONDO) mit ALLEN heutigen "
            "Mailaenderungen. Gefunden und behoben: englische "
            "Dezimalzahlen in `auswahl.py` (echter Mailfehler), drei "
            "Werkzeugfehler (Trichter gekappt, Luecke ohne Zeile, Mail nicht "
            "abgelegt), ein gemischtes Minuszeichen. NACHTRAG 11.09. nachmittags: der "
            "CHART war nicht geprueft - zwei Zahlenfehler gefunden und "
            "behoben (2.367). ⚠️ NICHT NACHGEWIESEN: ein Hebelgeschaeft "
            "(Faktor ueber 1,0) - in keinem Lauf entstanden (2.371).",
            "Befunde 2.362 bis 2.373", fertig=True,
            umbau="neu"),  # E2E vor dem Rollout des neuen Pakets
    Schritt(16, "AKKU-SPERRE",
            "✔ ERLEDIGT 11.09.: Sicherheitsnetz - die Akkumulation ist ohne "
            "gemessenen Beitrag GESPERRT statt durchgewunken "
            "(`Potential.lage_gesperrt`, geprueft VOR der Notiz ,nicht "
            "vermessen'). Bis dahin entschied ueber einen Nachkauf allein "
            "das Sprachmodell (2.370). Einstieg unberuehrt.",
            "Nutzerentscheidung 11.09. (Paket B); Befund 2.374-akku",
            fertig=True,
            umbau="neu"),  # Akku-Sperre bis der Beitrag steht
    Schritt(17, "H-1 PORTFOLIOWERT",
            "✔ ERLEDIGT 11.09.: das KAPITAL ist lesbar, vollstaendig und "
            "ueberwacht. P-3 Option A - das Gestakte zaehlt; fehlende "
            "Tageskurse von Boersentiteln hoechstens vier Tage "
            "fortgeschrieben; `aktuelles_kapital()` mit frisch/alt/zu_alt "
            "und Klartextsatz, ueber 14 Tage keine Hebelrechnung (Spot), nie "
            "ein stiller Vorgabewert; Quelle `kapital` in der "
            "Frischepruefung. Gegen die NB-Kopie: 9.942 EUR (10 Tage alt) "
            "-> 18.213 EUR, jeder Tag geschrieben, Index ohne Sprung.",
            "Befunde 2.375, 2.376; Nutzerentscheidung 11.09. (P-3 A)",
            fertig=True,
            umbau="neu"),  # H-1 Portfoliowert als Bezugsgroesse fuer r(q)
    Schritt(18, "H-2 r(q)",
            "✔ ERLEDIGT 11.09.: der Hebel entsteht aus der "
            "Wahrscheinlichkeit - halbes Kelly, geklammert 0,50-1,25 % des "
            "Kapitals, Positionswert / 500 EUR; unter 2x Spot mit "
            "unveraendertem Betrag; Grenze 5x und Liquidationsabstand; ohne "
            "positive Erwartung kein Hebel. Das Etikett aus r(q) steuert "
            "Zelle, Schalter und Topf; die Herleitung steht in EUR in der "
            "Mail. Gegenpruefung fand einen Stop-Fehler im ersten Einbau "
            "(behoben, 2.377-gegenpruefung). ⚠️ SCHALTER AUS bis Schritt 19.",
            "Befunde 2.377*; Nutzerentscheidung 11.09. (Paket B)",
            fertig=True,
            umbau="neu"),  # H-2 - r(q) SELBST, der Kern des Hebelumbaus
    Schritt(19, "H-3 HEBELVERTEILUNG",
            "✔ ERLEDIGT 11.09.: `simuliere_hebelverteilung.py` ueber "
            "633.672 echte Anker, Betriebsfall mit Widerlegungspreis. Bei "
            "18.213 EUR: Spot 56 %, Hebel 44 % (Grenze 5x 5 %), "
            "Liquidation nie; stark kapitalabhaengig (12 % bei 9.942, 80 % "
            "bei 30.000). Watchlist 2026: Hebel 58 %, Grenze 5x 10 %, Stop Median 13,7 %. Gegenpruefung G1-G6 "
            "bestanden; Stopregel an 1.289 NB-Einstiegen gegengeprueft. "
            "EMPFEHLUNG: Schalter mit dem Rollout (nach H-4, H-5, E2E).",
            "Befunde 2.378*",
            fertig=True,
            umbau="neu"),  # H-3 Hebelverteilung
    Schritt(20, "H-4 POSITIONSFUEHRUNG HEBEL",
            "✔ ERLEDIGT 11.09.: `agent/hebelfuehrung.py` - jede offene "
            "Position aus `hebel_positions` mit ihrem Plan, Liquidation mit "
            "den echten Tagen, Finanzierung, `bewerte()`; LIQUIDATION "
            "ERREICHT / SCHLIESSEN / HEBEL SENKEN / STOP NACHZIEHEN als eigene "
            "Mail, einmal je Zustand und Tag. DIE GEGENPRUEFUNG FAND VIER "
            "FEHLER: RM-11 liess bei jedem Hebel die Liquidation vor dem Stop "
            "zu (2.379-rm11); Liquidation in Mail und Faktentext ohne "
            "Wartungsmarge (2.379-liq, Prompt-Stand 2026-09-11a); die "
            "Ausstiegsfuehrung haette Rollen-Hebelsignale als Spot gefuehrt "
            "(2.379-instrument); `hebel_screening.aktiv: false` haette die "
            "Kette abgeschaltet (2.379-schalter). Bei 18.213 EUR bleibt die "
            "Hebelverteilung unveraendert. OFFEN (2.379-tage): Tagesreserve "
            "beim Einstieg - erst bei wachsendem Kapital noetig.",
            "Befunde 2.379*, 2.378-korrektur",
            fertig=True,
            umbau="neu"),  # H-4 Positionsfuehrung Hebel
    Schritt(21, "H-5 AGGREGAT-DECKEL",
            "✔ ERLEDIGT 11.09.: `agent/hebel_aggregat.py` - offene Positionen "
            "(bis zum Stop, ohne Stop das Eigenkapital), offene Hebelsignale "
            "und die Signale des Laufs zusammen hoechstens 3 % des Kapitals; "
            "ein neuer Trade bekommt den Rest, unter 2x wird er Spot. Neue "
            "Spalte `verlust_am_stop_eur`. MIT KORREKTUR ZU H-4: die Kette "
            "schrieb `instrument` nie - jetzt ,hebel' fuer r(q)/SHORT "
            "(2.379-instrument-korrektur). ✔ Fenster 24 h (Nutzer 11.09., "
            "2.380-fenster). ✔ Position ohne bekannten Stop: Variante B "
            "(Nutzer 11.09., 2.380-ohne-stop).",
            "Befunde 2.380*, 2.379-instrument-korrektur",
            fertig=True,
            umbau="neu"),  # H-5 Aggregat-Deckel
    Schritt(22, "S-4 SPOT SAUBER",
            "✔ ERLEDIGT 11.09.: (a) der Hebelschalter aendert den Spot-Betrag "
            "nicht - 1.436 NB-Einstiege, Betrag ueberall gleich; 33 % verlieren "
            "nur ihren Scheinhebel 1,2x (2.381-spot). (b) die Mail nach dem "
            "Vorschlag gegliedert, nichts gestrichen, die zweite Trefferquote "
            "im Anhang (2.381-mail). (c) O1 behoben: 12 h wirken wieder, der "
            "kurze Takt erst ab 2x (2.381). Feinschliff der Mail (Kursmarken "
            "und Rangangaben zusammenlegen) NACH dem Rollout.",
            "Befunde 2.381*",
            fertig=True,
            umbau="neu"),  # S-4 Spot sauber
    Schritt(23, "E2E PAKET B",
            "✔ ERLEDIGT 11.09.: `simuliere_kette.py --nachweis-paket-b` gegen "
            "die NB-Sicherung, 17 Faelle gezeigt - Hebelgeschaeft mit Zeile, "
            "Mail, Chart, Hebeltopf, Cooldown 3,5 h, Aggregat-Deckel; "
            "Hebelfuehrung mit Position UND ihrem Signal; Deckel ausgeschoepft "
            "-> Spot mit 800 EUR; Schalter aus -> derselbe Betrag; kein "
            "Akkumulationssignal (2.382). Vorher B gebaut (2.380-ohne-stop). "
            "BEFUNDE: die Akkumulationszelle erreicht ihre Sperre nie - Anlass "
            "und Cooldown je Symbol (2.382-akku-anlass, Schritt 26); der Topf "
            "begrenzt praktisch nie (2.382-topf); B und die Liquidation "
            "(2.382-liquidation); Rundung des Hebels (2.382-rundung).",
            "Befunde 2.382*",
            fertig=True,
            umbau="neu"),  # E2E Paket B
    Schritt(24, "ROLLOUT PAKET B",
            "✔ ERLEDIGT 12.09.: Gesamtpaket am Notebook (142 Commits, "
            "fast-forward). `ausrollen_paket_b.py --nachrechnen` 13 Punkte, 0 "
            "offen - ⚠️ das Kapital war nicht nur alt, sondern FALSCH: 9.942 "
            "-> 17.978 EUR, weil sechs gestakte Positionen fehlten (32 "
            "Symbole mit 6 Kursluecken gegen 38 ohne); der Aggregat-Deckel "
            "steht damit bei 539 statt 298 EUR (2.387). Suite 2.179 ALLE "
            "BESTANDEN mit 5 uebersprungenen Bloecken, `--nachweis-paket-b` 17 "
            "von 17, `finde_freie_namen` 0. Scharf: Hebel aus der Quote AN, "
            "altes Hebel-Screening AUS, Marktscan AN (2.384, 2.385). Zwei "
            "Rote unterwegs, beide kein Betriebscode (2.387-rot). ⚠️ OFFEN "
            "nach dem Neustart: die Abnahme des ersten Umlaufs, der "
            "Schreibjob (2.387-job), die fortgeschriebenen Boersentitel "
            "(2.387-fortschreibung).",
            "Basisinfos/Ausrollen_24_08.md; Notebook-Rollout 12.09.",
            fertig=True,
            umbau="neu"),  # Rollout Paket B
    Schritt(59, "GESAMTKETTE MESSEN UND BEWERTEN - JE STRATEGIE UND PHASE, DETERMINISTISCH UND LLM",
            "\u26a0\ufe0f NUTZERVORGABE 15.09.: *,Zu den Hebelsignalen und Krypto insgesamt muss die "
            "gesamte Ablaufkette und LLMs in einem umfangreichen Planpunkt gemessen und bewertet werden - "
            "erinnere dich, Ziel: Hebel nur dann, wenn ein optimales Chancen-Risiko-Verhaeltnis vorhanden "
            "ist. Die Bewertung sollte aber fuer alle Strategien erfolgen (Spot und Akkumulation) sowie "
            "Unterscheidung Einstieg, Fuehrung und Ausstieg bzw. Reduktion.'* "
            "\u27a4 DIE MATRIX: STRATEGIE (Spot, Hebel, Akkumulation) x PHASE (Einstieg, Fuehrung, "
            "Ausstieg/Reduktion) x EBENE (deterministische Stufen der Kette, LLM-Rollen A, BC, G und die "
            "Gegenpruefung). JE ZELLE DREI FRAGEN: (1) ZAHL - wie viele Empfehlungen, wo faellt was im "
            "Trichter heraus; (2) GUETE - Potential (`bewegung_r`) gegen ein Nullmodell auf derselben Menge, "
            "Tagesklammer, nach Messstandard; (3) BEITRAG - was aendert die Stufe oder Rolle gegen die Kette "
            "ohne sie. FUER DEN HEBEL ZUSAETZLICH: traegt die Quote den Hebel (r(q)), und waere derselbe "
            "Trade als Spot besser - Vorgabe HEBEL-ZIEL. "
            "\u27a4 BAUSTEINE, DIE HIER AUFGEHEN ODER ZULIEFERN (nicht doppelt bauen): 42 T-0 "
            "(Zahl, Guete, LLM-Aussagekraft), 29 T-1 Fehleridentifikation, 30 T-3 historische Simulation auf "
            "Potential, 43 (1) Guetemass des Ausstiegs, 25 Akku-Messpaket, 35 A1 und 37 Kalibrierung (Hebel), "
            "52 Stopregel; 33 LLM-Rollen entscheidet ERST DANACH. "
            "\u27a4 AUSGANGSLAGE 15.09. (2.455-hebelsignale): alle 166 Zeilen der Rollen-Kette seit "
            "12.09. tragen strategie `einstieg`; die 8 Hebelempfehlungen sind NACHKAUFEN auf gehaltenen Werten "
            "- Einstieg und Fuehrung sind in den Daten nicht getrennt, die Akkumulation ist gesperrt. "
            "\u26a0\ufe0f ZUERST DAS MESSDESIGN, dann messen (Vorgaben MESSSTANDARD-VOR-DER-MESSUNG, "
            "KEINE-TEILLOESUNG, STAND-PRUEFEN-VORHER): je Zelle Population, Zielgroesse, Nullmodell, Datenlage "
            "und bekannte Blocker (A1 binaeres Band, A8 Live-Menge, A9 Laengsachse) - vorgelegt und abgestimmt, "
            "bevor eine Zahl gerechnet wird. LLM ist Pruefung, nicht Entscheider.",
            "Nutzervorgabe 15.09. (Position vor 43 und 42 darin bestaetigt); Vorgabe HEBEL-ZIEL; Befunde 2.455-hebelsignale, 2.391*; Schritte 42, 29, 30, 43, 25, 35, 37, 52, 33",
            block="D-BEWERTUNG",
            umbau="beides"),  # misst Alt (LLM-Rollen) und Neu (Bewertung, r(q)) in einer Matrix
    Schritt(60, "KRYPTO STABIL UND FUNKTIONAL KORREKT - FEHLERKORREKTUR, MAIL-INHALT UND -STRUKTUR",
            "\u26a0\ufe0f\u26a0\ufe0f NUTZERVORGABE 15.09. (Vorgabe KRYPTO-STABIL-UND-KORREKT): nach Schritt 59 "
            "ein umfangreicher Zusatzpunkt, BEVOR weitergearbeitet wird. DREI TEILE: (1) FEHLER AUS DER "
            "MESSUNG - was Schritt 59 je Strategie und Phase als falsch oder wirkungslos zeigt, wird korrigiert, "
            "nicht nur benannt. (2) FEHLER AUS DEM BETRIEB, schon bekannt: 2.455-hebel-nachkaufen (ein Hebel-"
            "Einstieg heisst NACHKAUFEN, weil ein Spot-Bestand da ist - fachlich eine neue Position, 7c); die "
            "Rollen-Kette schreibt fuer alles strategie `einstieg`, Einstieg, Fuehrung und Ausstieg sind in den "
            "Daten nicht getrennt (2.455-hebelsignale); was aus Schritt 55 und 56 dann noch offen ist. (3) "
            "eMAIL-INHALT UND -STRUKTUR: auf Grundlage der Fachpruefung (Schritt 41, 2.447-offen) und der "
            "Messung - was in welche Mail gehoert, je Strategie und Phase, samt Betreff, Reihenfolge und "
            "Warnungen (Nutzer 12.09.: ,vor lauter Warnungen sehe ich nicht auf einen Blick, was relevant "
            "ist'). NUTZERHINWEIS 15.09. zur Hebelstufen-Darstellung: ,wichtig fuer den Punkt Ueberarbeitung "
            "der eMails und Gruppierung, Lesbarkeit' - Grundlage ist die Stufendarstellung "
            "(2.455-hebelstufen-gebaut); am Pruefstand beobachtet: Betrag und Ergebnis stehen im Blick-Block "
            "UND in der Rechnung, der Hebel an drei Stellen (Blick, Rechnung, Herleitung). NUTZERVORGABE 15.09.: *,Zur Mailueberarbeitung brauche ich in EINEM Bereich vor allem jene Informationen, die fuer die Empfehlung wichtig sind - aktuell ist dies kaum moeglich'*. Dazu gehoert die Frage, welche Warnungen den Kopf verdienen - Beispiel Cash frei 69 EUR mit `!!` in praktisch jeder Kaufmail (2.453-alterlos, Entscheidung C3). \u26a0\ufe0f Umsetzungsschritte werden nach Schritt 59 im Detail vorgelegt; bis dahin ist "
            "dieser Schritt die Sammelstelle, damit nichts verloren geht.",
            "Nutzervorgabe 15.09.; Vorgabe KRYPTO-STABIL-UND-KORREKT; Befunde 2.455-hebel-nachkaufen, "
            "2.455-hebelsignale, 2.455-hebelstufen-gebaut, 2.447-offen; Schritte 41, 55, 56, 59",
            block="D-ABBILDUNG",
            wartet_auf=(59,),
            umbau="beides"),
    Schritt(43, "VERKAUFSEMPFEHLUNGEN - DIE AUSSTIEGSSEITE ZU ENDE BAUEN",
            "⚠️ NUTZERVORGABE 12.09.: *,nimm noch die Verkaufsempfehlungen in "
            "den Gesamtplan auf - das sollten wir VOR dem Multiasset (Aktien "
            "etc.) angehen und ABSCHLIESSEN'*. ⚠️⚠️ WARUM DAS DRINGEND IST "
            "(Befund 2.392, gemessen): die Ausstiegsseite ist mit 517 "
            "Empfehlungen seit 14.08. und 15 bis 20 pro Tag der GROESSERE "
            "Teil des Betriebs - und sie verzweigt an Stufe 9 direkt in die "
            "Mail. Die Stufen 10 bis 12 sieht sie nie, also gilt fuer sie "
            "weder das gemessene Potential noch eine Schwelle noch ein "
            "Deckel. (1) GUETE ZUERST: `outcome_status` taugt fuer Ausstiege "
            "nicht - 409 von 517 stehen auf ,nicht_anwendbar', der Rest auf "
            "EINSTIEGS-Kategorien. Es braucht ein eigenes Erfolgsmass fuer "
            ",war der Verkauf richtig' - Potential, nicht Zielerreichung: "
            "was hat der Kurs NACH der Empfehlung getan, gegen ein "
            "Nullmodell (halten). (2) STUMME AUSSTIEGE (2.392-stumm): 105 "
            "Ausstiege sind als ,reines LLM-Halten' ohne Mail gebucht, bis "
            "11.09. - den Zweig finden und schliessen. (3) WIEDERHOLUNG: "
            "SUPRA 12x VERKAUFEN, MON 10x REDUZIEREN in 7 Tagen - greift der "
            "Cooldown auf der Ausstiegsseite ueberhaupt? (4) DIE FRIST `umgeworfen_bis` (Nutzerentscheidung "
            "12.09.: *,zur Frist - sollte getrennt fuer die Verkaufsseite "
            "bzw. Ausstieg gesamtheitlich geplant und umgesetzt werden'*). "
            "⚠️ SIE IST IN 0 VON 1.280 ZEILEN GESETZT - LLM-1 Rolle BC "
            "liefert sie nie, und damit laeuft die dritte Pruefung der "
            "`ausstiegsrechnung` vollstaendig leer. Ihr eigener Kopf "
            "beziffert, was das kostet: *,15 bis 21 %% aller Faelle laufen "
            "ohne Entscheidung aus - heute merkt das niemand.'* Zuerst "
            "klaeren, WARUM sie fehlt (Prompt, Schema oder Vertrag), dann "
            "gemeinsam mit den anderen Ausstiegsfragen loesen - nicht als "
            "Einzelfix. (5) ERST DANN die "
            "Frage nach einer eigenen Bewertungsstufe fuer den Ausstieg. ⚠️ "
            "REIHENFOLGE: dieser Schritt steht VOR jeder Multiasset-Arbeit "
            "(Vorgabe KRYPTO-ZUERST bleibt, VERKAUF-VOR-MULTIASSET kommt "
            "davor). \u27a4 NUTZERENTSCHEIDUNGEN 14.09. (Plan_Asset_Lebenszyklus_14_09.md, Abschnitt Ausstieg): (A) VERKAUFEN UND REDUZIEREN GEHOEREN GEMESSEN und sauber ins Konzept - WAS ist der Verkaufsgrund: eine BEWERTUNG je Strategie; die noetigen Bewertungen und Urteile werden mit dem Nutzer dimensioniert wie beim Einstieg. \u26a0\ufe0f DIE VERKAUFSBEWERTUNG IST NICHT GELOEST - Stand 14.09. unveraendert 2.392. (B) HEBEL: Schutzschicht = Regeln alle 15 min mit eigenem Betreff und Mailhinweis; Fuehrung = Modell mit Positionskontext, an die OFFENE POSITION gebunden, 1-h-Takt fuer offene Hebeltrades - erst wenn gemessen ist, dass Verkauf/Reduzieren tragen; eigene Positionsfrage mit Intraday-Fakten. (C) KERN/AKKUMULATION: vorerst KEINE Verkaufsaktionen; nachgelagert: bei laengerem Greed u. U. sinnvoll, Fear nicht. (7c) Ein Asset mit Spot- UND Hebelposition = zwei Positionen, zwei Verkaufssignale, keine Sammelmail. \u27a4 DIE DETAILPLANUNG FOLGT NACH DEM ROLLOUT (Nutzerauftrag: Doku lesen, Messdokumente beachten, testen und simulieren). \u27a4 NUTZERENTSCHEIDUNG 15.09.: VOR DIE AKKUMULATION GEZOGEN (vor die Schritte 25 bis 27). Grund: die Prioritaet des Nutzers vom 11.09. lautet ,1 Hebel 2 Spot 3 Akkumulation', und die Verkaufsseite betrifft Hebel und Spot; sie laeuft taeglich mit 15 bis 20 Empfehlungen ohne gemessene Guete, waehrend die gesperrte Akkumulation nichts ausloest und damit nicht schadet. Schritt 55 geht voraus (Ausstiegsmail nach Positionen).",
            "Nutzervorgabe 12.09.; Befunde 2.392, 2.392-stumm",
            block="D-BEWERTUNG",
            umbau="beides"),  # die Ausstiegsseite laeuft an der neuen Bewertung vorbei
    Schritt(25, "AKKU-MESSPAKET",
            "(1) 2.286/2.287 reproduzieren (R-R11); (2) Zeitstabilitaet je "
            "Kandidat fuer H90 - Permutationstest je Haelfte, `n68` ist "
            "blockbasiert und passt dort nicht; (3) Ueberschneidung der "
            "drei: `schnitt` +0,0470, `funding` UMGEKEHRT -0,0230, "
            "`oi_aenderung` UMGEKEHRT -0,0178; (4) Stufen. Faellt ein "
            "Kandidat: Loesung suchen (KEIN-BEITRAG-FAELLT) - die Sperre "
            "bleibt so lange.",
            "Befunde 2.286 bis 2.290; Nutzerentscheidung 11.09.",
            block="D-BEWERTUNG",
            umbau="neu"),  # Beitrag fuer die Akkumulation - die Lage hat heute keinen
    Schritt(26, "AKKU-BAU",
            "Form REGLER (Fuenftelstufen, nur spot x akkumulation). Eigene "
            "SKALA: `verbilligung` ist ein Rang mit Basisrate 0,500, kein "
            "R - daher eigene Schwelle (R-R9 nur fuer diese Lage). "
            "Registrierung mit `strategien=('akkumulation',)` - die Sperre "
            "faellt damit von selbst. `schnitt` am Notebook aus der "
            "KURSREIHE rechnen - `messdaten.db` liegt dort bewusst nicht. "
            "Mail und Simulation. ⚠️⚠️ DAZU DER COOLDOWN JE STRATEGIE "
            "(2.380-akku-cooldown) UND DIE ANLASS-MESSUNG JE ZELLE "
            "(2.382-akku-anlass): die Akkumulationszelle haengt heute "
            "hinter der Einstiegszelle und kam NIE zum Urteil - mit "
            "Kostenschutz beheben und in `simuliere_kette` zwei Zellen "
            "nachweisen.",
            "vormals Schritt FORM; Befunde 2.286-schnitt, 2.374",
            block="D-BEWERTUNG",
            umbau="neu"),  # Bau des Akkumulationsbeitrags
    Schritt(27, "ROLLOUT PAKET 2",
            "Akkumulation aufs Notebook. Der Schalter steht fuer BTC, ETH "
            "und SOL schon an (2.380-akku-schalter) - mit der Registrierung "
            "faellt die Sperre.",
            "Nutzerentscheidung 11.09.",
            block="D-BEWERTUNG",
            umbau="neu"),  # Rollout des neuen Akkumulationsteils

    # ================================================================
    # NACH DEM PRODUKTIVGANG
    # ================================================================
    Schritt(28, "TAKT UND TOPF",
            "⚠️ ERST NACH DEM ROLLOUT messen - vorher misst man den alten "
            "Stand. Mailaufkommen und Wiederholungsanteil am echten "
            "Betrieb. DAZU DIE TOPFREGEL NEU FASSEN (Nutzer 11.09., "
            "2.382-topf): der Topf zaehlt nur Signale, die die Verfolgung "
            "noch nicht gesehen hat, und begrenzt praktisch nie; beim Hebel "
            "greift der Aggregat-Deckel.",
            "Nutzervorgabe 11.09.; Befund 2.382-topf",
            block="D-ABBILDUNG",
            umbau="alt",
            wartet_auf=(27,),  # ERST NACH DEM ROLLOUT - Schritt 27
            ),  # Takt und Topf stammen aus der alten Kette, werden gemessen

    # ================================================================
    # DAS STANDARDWERKZEUG (Nutzervorschlag 11.09., gestaffelt)
    #
    # > "kein einfacher End2End Test sondern eine umfangreichere Test-
    # >  und Simulationsstufe (ein Standardwerkzeug): Fehleridentifikation,
    # >  Empfehlungen je Strategie, Asset und Zeitraum, unterschiedliche
    # >  Marktphasen, optional eine historische Simulation."
    #
    # ⚠️ NACH dem Rollout, weil erst dann echte Laeufe auf NEUEM Code
    # vorliegen. Ein Werkzeug gegen den alten Stand zu bauen heisst, es
    # beim ersten echten Einsatz nochmal anzufassen.
    # ================================================================
    Schritt(29, "T-1 FEHLERIDENTIFIKATION",
            "Je STRATEGIE, ASSET und ZEITRAUM - baut auf "
            "`simuliere_kette.py` auf, die den Durchlauf schon kann. "
            "⚠️ Ein Standardwerkzeug mit Schaltern statt Wegwerfskripten: "
            "allein am 11.09. sind fuenf entstanden (n108 bis n112), wo "
            "eines gereicht haette.",
            "Nutzervorschlag 11.09.",
            block="D-BEWERTUNG",
            umbau="neu"),  # Fehleridentifikation auf der neuen Bewertung
    Schritt(30, "T-3 HISTORISCHE SIMULATION",
            "⚠️⚠️ AUF `bewegung_r` (POTENTIAL), NICHT auf Zielerreichung. "
            "Nutzervorgabe 23.08.: *,Wichtig fuer den guten Trade ist das "
            "POTENTIAL und NICHT die reelle Zielerreichung, diese ist "
            "immer ausser Reichweite.'* Ein Barrierensystem auf "
            "driftfreiem Pfad hat Erwartungswert NULL fuer jede "
            "Geometrie - ,Ziel vor Stop' faellt per Konstruktion auf "
            "1/(1+CRV). **Wer das misst, misst unsere eigene Zielregel "
            "zurueck** und erzeugt die Nullbefundserie erneut. "
            "✔ GRUNDSTOCK VORHANDEN: `agent/krypto/backtesting.py` (vom "
            "17.07., ohne Aufrufer) - mit ehrlich benannten Grenzen im "
            "Kopf.",
            "feedback_potential_statt_zielerreichung; "
            "agent/krypto/backtesting.py",
            block="D-BEWERTUNG",
            umbau="neu"),  # historische Simulation gegen `bewegung_r` - neues Erfolgsmass

    Schritt(31, "EMAIL STRUKTUR UND INHALTE",
            "⚠️ SETZT AUF SCHRITT 41 AUF (Fachpruefung) - erst pruefen, dann "
            "straffen. ⚠️ NUTZERVORGABE 11.09.: Struktur und Inhalte straffen. "
            "Regel 1 war schon erfuellt (2.356); offen sind Regel 2 "
            "(gleichlautende Luecken zu EINEM Satz, gezaehlt nach GRUND) "
            "und Regel 3 (Anhang statt Weglassen). ⚠️ Vorbehalt aus dem "
            "Vorschlag: die Mail ist lang, WEIL die Bewertung duenn ist - "
            "nach Schritt 21 schrumpft der Lueckenblock von selbst."
            "\u27a4 SEIT SCHRITT 41 (13.09.) LIEGT DER STOFF VOR: 2.446-redundanz, "
            "2.446-lesbarkeit, 2.446-begriffe, 2.446-etiketten (Nutzerentscheidung: "
            "Etiketten streichen oder als ,nicht belegt\u2018 kennzeichnen) und "
            "2.445-fenster (Haltedauer und sicheres Hebelfenster nebeneinander). "
            "Pruefwerkzeug: `pruefstand_hebelmail.py`."
            "✔ FERTIG 13./14.09. (Befund 2.447): Hauptteil 126 -> 111 "
            "Zeilen, 11.014 -> 8.438 Zeichen. Etiketten gestrichen "
            "(2.447-etiketten), Kopf mit Empfehlung und Tatsachen, Anhang D "
            "(Beitraege) und E (Lesehilfen), Tage statt Handelstage bei Krypto, "
            "Hebelfenster gegen Haltedauer (2.447-fenster). ⚠️⚠️ "
            "DABEI DREI SHORT-FALSCHAUSSAGEN BEHOBEN (2.447-short). Paket "
            "`Mailstraffung`. ➤ NICHT angefasst, mit Grund: die Saetze aus "
            "`lagebeschreibung` (Modelltext -> Schritt 33), die "
            "Trichter-Etiketten (-> Schritt 52), Regel 2 als Zaehlzeile "
            "(Grund nur Freitext) - alles in 2.447-offen.",
            "Gesamtplan 11.09. - Mail-Vorschlag",
            fertig=True,
            block="D-ABBILDUNG",
            umbau="beides",
            wartet_auf=(41,),  # 41 sagt: Schritt 31 kommt DANACH und setzt darauf auf
            ),  # alte Mailstruktur ersetzen, neue Bewertung abbilden
    Schritt(32, "GUI UND UEBERSICHTSSEITE",
            "⚠️ Offen seit 07.09., nie begonnen (E1). ⚠️ Die "
            "Uebersichtsseite EXISTIERT (`remote/status.py`, rund 40 "
            "Aggregatoren) - hier geht es um Erweiterung, nicht Neubau. "
            "Die Bewertungsschwelle steht seit dem 11.09. darin (35 "
            "Parameter); in der GUI fehlt sie noch."
            "\u27a4 SEIT SCHRITT 41 (13.09.): 2.446-gui - die alte Dreiteilung mit "
            "Konfidenz steht in `ui/hebel_view.py` UND `ui/signals_view.py`; die "
            "Hebelzeilen unter 2x sind Altbestand vor dem Rollout."
            "➤ GEPRUEFT 14.09. (Befund 2.448): die Oberflaeche ist noch die "
            "der alten Kette. KEIN Reiter zeigt die neue Bewertung (2.448-reiter); "
            "JEDER Analyseknopf startet die alte Pipeline und wuerde ein Signal "
            "der alten Kette in die Produktion schreiben (2.448-knoepfe); "
            "Gleichlauf mit der Mail geht nur ueber den gespeicherten Mailtext - "
            "Schemaaenderung, Nutzerentscheidung (2.448-mail); Uebersichtsseite "
            "gemischt (2.448-uebersicht)."
            "\u2714 FERTIG 14.09. (Befund 2.448-umsetzung): Analyseknoepfe an die "
            "Kettenregel gehaengt, Detailansicht der Rollen-Kette aus DB-Feldern "
            "(`agent/signal_ansicht.py`) in Signale, Hebel und Letzte Bewertung, "
            "Anzeigen der alten Kette gekennzeichnet. Paket `GuiKette`, "
            "Oberflaechenprobe 17/17. \u27a4 Was offen bleibt, steht in "
            "2.448-rest und in Schritt 53.",
            "remote/status.py; Nutzervorgabe 07.09. und 11.09.",
            fertig=True,
            block="D-ABBILDUNG",
            umbau="alt"),  # die GUI zeigt noch die alte Dreiteilung
    Schritt(33, "LLM-ROLLEN UND MODELLE",
            "⚠️⚠️ INHALT AM 12.09. GESETZT (Vorgabe LLM-SCHIENE-GANZ): die "
            "GANZE Schiene, nicht einzelne Prompts. (1) Je Rolle "
            "aufschreiben, WELCHE Kriterien sie heute bewertet und mit "
            "welcher Begruendung - Rolle A, Rolle BC, Rolle G getrennt. (2) "
            "Die echten, GEMESSENEN Einstiegsgruende einspeisen: heute kennt "
            "keine Rolle `potential`, `funding`, `turnover` oder die "
            "Trefferquote (2.398). (3) Dasselbe fuer den AUSSTIEG - dort "
            "traegt das Modell nachweislich (2.403), beim Einstieg nicht. "
            "(4) ⚠️ ERST NACH Schritt 42 [15.09.: Schritt 42 ist in 59 aufgegangen.] ➤ NUTZERKLARSTELLUNG 15.09.: *,die LLM-Kette soll in einem PAKET gemeinsam auf den aktuellen und richtigen Stand gebracht werden - die Einzelmessungen und/oder die gesamte Simulation der Funktion und Wirksamkeit ist wieder umfangreicher'*. Also: keine Rolle einzeln nachbessern, sondern Rolle A (Marktlage), BC und G samt ihrer Fakten und Massstaebe gemeinsam - Fakten wie der Umschlag (2.453-alterlos Punkt B/C) werden hier entschieden, gemessen in Schritt 59.: ohne Messung ist jede "
            "Promptaenderung eine Meinung. "
            "⚠️ NUTZERVORGABE 11.09.: Bewertung und Analyse der Rollen "
            "und Modelle - NACH den eMails. Stehende Vorgaben, die hier "
            "gelten: nur kostenfreie LLMs · das LLM muss den Zufall "
            "schlagen und messbar sein · kein deterministischer Override "
            "des LLM-Werturteils. "
            "⚠️⚠️ ZWEI ENTSCHEIDUNGEN AUS SCHRITT 44 KOMMEN HIERHER "
            "(13.09., Befunde 2.427-rollenfrage und 2.422). Sie sind "
            "GEMESSEN und reproduziert, es fehlt nur die Entscheidung - und "
            "sie ist keine Messfrage. "
            "(R1) DARF DAS MODELL EINE EMPFEHLUNG VERHINDERN? Rolle BC "
            "blockiert an Stufe `aktion` mit NICHTS_TUN: 56 Zellen in 7 "
            "Tagen, gegen 191 deterministische Verluste derselben Stufe "
            "(166 ,Ausstieg steht auf SCHLIESSEN', 25 ,gestakt'). Die "
            "Nutzervorgabe lautet *,die LLM-Stufen sollen eine "
            "ENTSCHEIDUNGSHILFE sein und nichts blockieren oder aendern' "
            "(12.09.) - fuer Rolle A und Z.ai gilt sie, fuer Rolle BC "
            "nicht. "
            "(R2) BRAUCHT DIE ABSICHERUNG EINE RICHTUNG? Sie ist per "
            "Konstruktion ein SHORT auf den Markt, und das Modell liefert "
            "fuer DBPK und 3QSS keine Richtung - ALLE 12 "
            "Absicherungssignale haben `richtung = NULL`. Weil "
            "`BRAUCHT_RICHTUNG` seit S6c `(KAUFEN, NACHKAUFEN)` ist, kann "
            "die Absicherung seit dem 22.08. strukturell nur HALTEN sagen; "
            "betroffen sind zwei GEHALTENE Positionen. Entweder die "
            "Absicherung braucht keine Richtung - oder der Prompt muss sie "
            "fuer diese Klasse liefern. "
            "⚠️ BEIDE ERST NACH DER MESSUNG entscheiden (Vorgabe "
            "LLM-SCHIENE-GANZ: *,ohne Messung und Simulation nicht "
            "sinnvoll'*) - aber sie gehoeren auf die Liste dieses Schritts, "
            "nicht in den D-Block. "
            "➤ AUS SCHRITT 31 (2.447-offen, Punkt 1): die Mailsaetze aus "
            "`lagebeschreibung` gehen DIESELBEN an das Modell - dort stehen "
            "noch ,Handelstage' fuer Krypto, der Widerstand doppelt zur "
            "Markenliste der Rechnung und das Umschlag-Perzentil. Wer sie "
            "strafft, aendert den Prompt - also hier, mit Messung.",
            "Nutzervorgabe 11.09.",
            block="L-ROLLEN",
            umbau="alt",
            wartet_auf=(59,),  # ERST NACH der Messung (Schritt 59, darin 42) - ohne Messung ist jede Promptaenderung eine Meinung
            ),  # die LLM-Rollen stehen seit dem 22.08. - sie werden umgebaut

    # ================================================================
    # ⚠️⚠️⚠️ SONDERPUNKT REGIME (Nutzervorgabe 11.09.2026)
    #
    # > "das Regime-Thema war schon in der Vergangenheit ein schwieriges
    # >  Thema fuer dich auch bei den Messungen - das sollten wir
    # >  jedenfalls detailliert als Sonderpunkt neben der LLM-Thematik
    # >  anlegen."
    # > "Regime konnte fuer unsere Bewertungsgrundlagen bisher kaum
    # >  sinnvoll genutzt werden."
    #
    # Das Verstaendnis des Nutzers ist durch die Daten BESTAETIGT, und
    # der Grund ist praezise: es gab NIE ein brauchbares Regimesignal,
    # gegen das man haette messen koennen. Nicht gemessen ist nicht
    # unwirksam - dieselbe Klasse wie "nicht trennbar" gegen "traegt
    # nicht". Details: Gesamtplan 11.09., Abschnitt Sonderpunkt Regime.
    #
    # ⚠️ Das fruehere T-2 (Regimetrennung der Beitraege) ist hier R-3
    # geworden: ohne eine historisch rekonstruierte Phase (R-1) und eine
    # geklaerte Datenlage je Phase (R-2) ist es nicht ausfuehrbar.
    # ================================================================
    Schritt(34, "SONDERPUNKT REGIME",
            "⚠️⚠️⚠️ BELEGTE AUSGANGSLAGE: (1) das diskrete Regime war nie "
            "etwas anderes als ,baer' - 2.549 Signale 07.07. bis 14.08., "
            "Ursache eine ODER-Bedingung (Fear & Greed allein erzwingt "
            "baer). (2) NEU 11.09.: seit dem 14.08. tragen am Notebook "
            "3.872 von 3.883 Signalen `regime = None` - die Rollenkette "
            "schreibt es gar nicht mit. (3) Das Modell reagiert auf einen "
            "Regimewechsel im Faktensatz nicht messbar. (4) H uebertraegt "
            "sich nicht ueber einen Regimewechsel (Kapitel 109). (5) KEINE "
            "Beitragsmessung ist je nach Regime getrennt worden. "
            "ARBEITSPAKETE: R-1 Regime historisch REKONSTRUIEREN, eine "
            "Definition fuer die ganze Historie, mit Positivkontrolle an "
            "bekannten Wendepunkten · R-2 Datenlage je Phase (Blockregel - "
            "vermutlich Phasen zusammenlegen) · R-3 Beitraege je Phase "
            "(vormals T-2) · R-4 die Schreibluecke im Betrieb · R-5 erst "
            "danach: gehoert Regime ueberhaupt in die Bewertung? ⚠️ "
            "NACHTRAG 11.09.: Quelle und Wirkung in 2.369 - heute wirkt "
            "es NUR im alten Marktscan. Fear & Greed: der mit der besten "
            "Aussagekraft, per Messung in R-3 entschieden "
            "(alternative.me gegen CoinMarketCap, 2.369-fg), dazu Fear & "
            "Greed gegen die Akkumulation.",
            "Nutzervorgabe 11.09.; project_regime_immer_baer_kein_vergleich; "
            "NB-Sicherung 11.09.; agent/krypto/regime.py",
            block="D-BEWERTUNG",
            umbau="neu"),  # Regime als moeglicher neuer Beitrag
    # ================================================================
    # DER HEBEL - die Messung, die Paket B NICHT ersetzt
    #
    # Paket B baut die Regel (r(q)); ob ein hoeherer Hebel auch mit einer
    # hoeheren REALEN Trefferquote einhergeht, ist erst nach A1 messbar.
    # Bis dahin begrenzen die Klammer 0,50-1,25 % und die 5x-Grenze.
    # ================================================================
    Schritt(35, "A1 / HEBEL-SPUR",
            "⚠️⚠️⚠️ DER ENGPASS DES HEBELS, mit BENANNTEM Weg: das Band "
            "auf binaeren Daten ist VIERMAL zu eng (2.238), deshalb "
            "traegt auf `barriere` sogar `zufall`. Loesung laut "
            "2.238-klasse: Fehlalarmquote der Barrieren-Anlage auf "
            "Nullwelten - dasselbe Verfahren, das am 09.09. den Nullbezug "
            "entschieden hat. ⚠️ DANACH erst sind die VIER "
            "Terminmarkt-Kanaele gegen die RICHTIGE Zielgroesse messbar; "
            "bisher sind sie nur gegen `bewegung_r` gefallen, und das VOR "
            "dem Messstandard. \u27a4 AUS DEM REVIEW 15.09.: D3 - ist H20 der richtige "
            "Horizont fuer die OI-Sperre, wenn der Betriebshorizont 3 bis 5 Tage "
            "betraegt? Gehoert zur selben Messung der Terminmarkt-Kanaele.",
            "Befunde 2.238 / 2.238-klasse / 2.169 / D3 / REGISTER_Kandidaten",
            block="D-BEWERTUNG",
            umbau="neu"),  # A1 blockiert JEDE Messung am neuen Hebel
    Schritt(36, "V12 VOLA UND SCHNITT",
            "⚠️ HYPOTHESE, nicht gemessen: beide fallen an Kriterium 2 "
            "mit fast derselben Zahl (+0,2039 gegen +0,1973). "
            "Gemeinsamer geometrischer Anteil? Stuetzt 2.293. "
            "⚠️ Niedrige Dringlichkeit - klaert nur, WARUM zwei "
            "Kandidaten fielen, die ohnehin gefallen sind.",
            "Befund 2.327 - offen",
            block="D-BEWERTUNG",
            umbau="neu"),  # vola und schnitt als moegliche neue Beitraege
    Schritt(37, "KALIBRIERUNG",
            "Kalibrierung neu, dann die Hebelhoehe rechnen: erreicht sie "
            "2-5x? ⚠️ Der Engpass ist die AUFLOESUNG, nicht die Staerke - "
            "die Abstufung sprang 1,02x -> 3,90x, weil die Beitraege "
            "Fuenftel sind (2.174-grenzen). ✔✔ NACHGEMESSEN AM 13.09. "
            "(2.432): der Sprung ist WEG - Spot · 2,00x · 2,46x · 3,12x · "
            "5,00x · 5,00x, vier von sechs Lagen in der Zielzone. Die "
            "r-Klammer (N-39) hat ihn geschlossen. ⚠️ Offen bleibt nur das "
            "OBERE Ende: die zwei besten Lagen ergeben beide 5,00x, weil "
            "die Obergrenze greift - eine bewusste Sicherheitsgrenze, keine "
            "fehlende Aufloesung.",
            "Plan 05.09.",
            block="D-BEWERTUNG",
            umbau="neu"),  # Kalibrierung der neuen Schwelle
    Schritt(42, "T-0 GESAMTKETTE HISTORISCH - ZAHL, GUETE, AUSSAGEKRAFT",
            "⚠️⚠️ MEHRFACH GEFORDERTE NUTZERVORGABE (zuletzt 12.09.): *,eine "
            "historische Pruefung der Gesamtkette - im ersten Schritt sind "
            "Anzahl und Qualitaet der echten Empfehlungen relevant, und dann "
            "darauf aufbauend MUSS eine erste sinnvolle Aussagekraft "
            "(Simulation) der LLM-Stufen erfolgen'*. ZWEI STUFEN, in dieser "
            "Reihenfolge. (1) ZAHL UND GUETE DER ECHTEN EMPFEHLUNGEN: aus "
            "`signals` seit dem Scharfgang - wie viele je Tag, Gruppe, Aktion "
            "und Instrument; wie viele erreichten den Einstieg, wie gingen sie "
            "aus (`outcome_status`), und was war das POTENTIAL (`bewegung_r`), "
            "NICHT die Zielerreichung. Datenlage steht: 3.859 Zeilen der "
            "Rollen-Kette, davon 964 ,Einstieg nie erreicht', 379 offen, 217 "
            "Stop, 214 Ziel. ⚠️ Die Population zuerst definieren - 2.076 "
            "Zeilen sind ,nicht anwendbar' (HALTEN, fehlende Zonen). (2) "
            "AUSSAGEKRAFT DER LLM-STUFEN: traegt das Urteil? Verglichen wird "
            "auf DERSELBEN Menge gegen ein Nullmodell (Zufall bei gleicher "
            "Trefferzahl) - fuer Rolle BC (KAUFEN gegen NICHTS_TUN), fuer den "
            "Widerlegungspreis (veraendert er den Stop zum Besseren?) und fuer "
            "Z.ai (Einwand ja/nein gegen Ausgang). Mit Tagesklammer, mit "
            "Zufallskontrolle, Erfolgsmass POTENTIAL. ⚠️ Ohne diese Messung "
            "ist der Beitrag der Modelle unbelegt (2.391) - und die "
            "Entscheidungen aus 2.391-hilfe sind nicht begruendbar. "
            "\u27a4 15.09.: IN SCHRITT 59 AUFGEGANGEN (Nutzerentscheidung 15.09.: ,42 geht auf') (Gesamtkette je Strategie "
            "und Phase) - die LLM-Aussagekraft wird dort in derselben Matrix gemessen.",
            "Nutzervorgabe mehrfach, zuletzt 12.09.; Befunde 2.391*; Schritt 59",
            fertig=True,  # 15.09.: in Schritt 59 aufgegangen (Nutzerentscheidung)
            block="L-ROLLEN",
            umbau="neu"),  # misst die neue Gesamtkette gegen ein Nullmodell
    Schritt(41, "MAIL UND GUI - FACHPRUEFUNG VOR DER STRAFFUNG",
            "⚠️ NUTZERVORGABE 12.09. nach der ERSTEN echten Hebelmail: *,die "
            "Struktur der eMail ist nicht schlecht, jedoch sehe ich vor lauter "
            "Warnungen nicht auf einen Blick was relevant ist - davor aber "
            "eine saubere fachliche und inhaltliche Bewertung'*. ⚠️⚠️ DIE "
            "REIHENFOLGE IST DIE VORGABE: erst pruefen, DANN straffen - wer "
            "kuerzt, bevor er weiss, was fehlt und was falsch ist, kuerzt das "
            "Falsche. (1) FACHPRUEFUNG: fehlen relevante Bewertungen? Sind die "
            "ZAHLEN korrekt? ✔ DER ERSTE VERDACHT IST GEPRUEFT UND "
            "BEHOBEN (2.390-zahlen, 12.09.): die Kosten-EUR bezogen sich "
            "auf den Einsatz statt auf den Positionswert - 27 EUR statt "
            "105, genau der Faktor Hebel. Die Prozente und die R-Aussage "
            "waren richtig, die Mail widersprach sich SELBST. ⚠️ Das ist "
            "EIN Zahlenfehler von vermutlich mehreren - die Pruefung der "
            "uebrigen Zahlen steht aus. (2) REDUNDANZ: echte Doppelungen gegen "
            "bewusste Wiederholung trennen (2.390-warnungen: Kursmarke "
            "dreimal, Stopabstand dreimal, ,EIN Beitrag' zweimal). (3) "
            "LESBARKEIT: 19 Warnzeilen gegen null Dafuer-Zeilen - was "
            "ENTSCHEIDET, muss oben stehen. (4) BEGRIFFE: ,Modell' meint im "
            "Kopf das LLM und in Abschnitt 5 die Rollen - doppelt belegt; wo "
            "stehen die LLM-Bewertungen und was ist aus der Konfidenz "
            "geworden? (5) GLEICHLAUF MIT DER GUI (2.390-gui): die Oberflaeche "
            "zeigt die alte Dreiteilung, leere Konfidenz-/Trigger-Spalten und "
            "1,0-1,2x-Zeilen als ,Hebel'. ⚠️ Schritt 31 (Straffung nach Regel "
            "2 und 3) kommt DANACH und setzt auf diesem Ergebnis auf."
            "✔ BEGONNEN 13.09. ABENDS - PUNKT (1), ERSTER FUND (2.443). "
            "Eine echte Hebelrechnung ueber den Betriebsweg gebaut und ihre "
            "Zahlen nachgerechnet: Stop, Einstiegszone, Ziel, Hebel, Verlust am "
            "Stop und Gewinn am Ziel stimmen exakt (8 %% Stop aus 2,5 x ATR; "
            "Ziel 116 = 2 x Risiko; Hebel 2.500/500 = 5,0; Verlust 200 = "
            "Gewinn 400 / 2). ⚠⚠ ABER ZWEI FRISTEN WIDERSPRECHEN SICH: die "
            "Mail schreibt ,Haltedauer etwa 25 Handelstage' und zwanzig Zeilen "
            "spaeter ,hinter dem Stop bis etwa Tag 21' - und vergleicht sie nie. "
            "In 5 von 14 gerasterten Hebelfaellen liegt die Haltedauer ueber dem "
            "sicheren Fenster. Verschaerft dadurch, dass die eine Zahl "
            "HANDELStage zaehlt und die andere KALENDERtage (die Finanzierung "
            "laeuft taeglich): 25 Handelstage sind rund 35 Kalendertage. "
            "➤ NICHT GEAENDERT - die Vorgabe dieses Schritts lautet ,erst "
            "pruefen, DANN straffen'. ⚠️ WAS NOCH AUSSTEHT: der Rest von "
            "(1), sowie (2) Redundanz, (3) Lesbarkeit, (4) Begriffe und (5) "
            "Gleichlauf mit der GUI."
            "⚠⚠⚠ ZWEITER FUND (2.444) - UND ER ERKLAERT DEN ERSTEN: die ,25 Handelstage‘ sind eine KONSTANTE. `_haltedauer_tage = "
            "(Zielweg/ATR)²`, Stop 2,5 ATR, Ziel bei CRV 2 also 5 ATR, 5² = 25 - "
            "bei jedem Trade mit ATR-Stop, egal welches Asset. Die Formel misst "
            "den Weg zum ZIEL, ein Trade endet aber an der ersten Marke. Gemessen "
            "liegen dagegen vor: 80 %% der Anker loesen bei 8 %% Stop in 10 Tagen "
            "auf; echte NB-Positionen hielten im Median 0,3 Tage; Betriebshorizont "
            "3-5 Tage (2.226, D3). ➤ NAECHSTER PRUEFSCHRITT: die Haltedauer "
            "gegen die eigenen Reihen MESSEN (Zeit bis zur ersten Marke, je Stop "
            "in ATR) und die Formel ersetzen - erst danach ist 2.443 beurteilbar."
            "\u2714\u2714 GEMESSEN (2.445) - UND ZWEI MEINER EIGENEN SAETZE OBEN SIND "
            "FALSCH. `messe_haltedauer.py`, 32.040 Anker, Positivkontrolle 5/5, "
            "Reproduktion von 2.435 identisch. Median bis zur ERSTEN Marke: 1 ATR "
            "5 Tage, 2,5 ATR 23 (LONG) / 27 (SHORT) - die Formel sagt 25. "
            "\u2716 FALSCH war ,die Formel beantwortet die falsche Frage, 25 statt "
            "5\u2018 (2.444): fuer einen 2,5-ATR-Stop stimmen die 25 Tage auf rund "
            "10 %%; die 3-5 Tage des Nutzers stimmen fuer 1-ATR-Stops. Die "
            "Finanzierung in der Mail ist NICHT ueberzeichnet. \u2716 FALSCH war "
            "auch ,25 Handelstage sind rund 35 Kalendertage\u2018 (2.443): "
            "Krypto-Kerzen enthalten Wochenenden. \u26a0\ufe0f WAS BLEIBT "
            "(2.445-fenster, offen): die Mail vergleicht Haltedauer und sicheres "
            "Hebelfenster nie - ein echter Konflikt aber nur bei "
            "schwankungsarmen Werten am 5x-Deckel. Und zwei BEGRIFFE sind "
            "ungenau: ,Handelstage\u2018 (fuer Krypto Kalendertage) und ,bis zum "
            "Ziel\u2018 (gemeint ist die erste Marke) - beides gehoert in Punkt (4)."
            "\u2714\u2714\u2714 ABGESCHLOSSEN 13.09. ABENDS - alle fuenf Punkte gepruef"
            "t, an einer ECHTEN aktuellen Mail (2.446: Pruefstand, echte Kette auf "
            "einer Kopie der Produktionssicherung). \u26a0\u26a0\u26a0 DER WICHTIGSTE FUND "
            "WURDE SOFORT BEHOBEN (2.446-richtung): eine SHORT-Empfehlung las sich "
            "als ,KAUFEN (Hebel)\u2018, Stop ueber dem Kurs mit ,-11,2 %%\u2018 - jetzt "
            ",KAUFEN (Hebel, SHORT)\u2018, Richtungszeile oben, Plus am Stop. Wie "
            "2.390-zahlen: eine Falschaussage, kein Straffen. "
            "(1) ZAHLEN: alle nachgerechnet, alle richtig (2.446-zahlen). "
            "(2) REDUNDANZ: Stopabstand fuenfmal, Marke 91,15 dreimal (2.446-redundanz). "
            "(3) LESBARKEIT: 14 Warnzeilen gegen 3 Dafuer-Etiketten - und die drei "
            "stehen auf einer gepoolten Augustmessung, die das Register nicht traegt "
            "(2.446-lesbarkeit, 2.446-etiketten). "
            "(4) BEGRIFFE: Konfidenz und Modell erledigt; offen Handelstage, drei "
            "Woerter fuer Schwankung, Umschlag doppelt belegt (2.446-begriffe). "
            "(5) GUI: alte Dreiteilung in ZWEI Reitern (2.446-gui). "
            "\u27a4 UMSETZUNG: (2)-(4) in Schritt 31, (5) in Schritt 32. Ausserdem "
            "vorgeschlagen: den Mailtext beim Versand mitschreiben (2.446).",
            "Nutzervorgabe 12.09.; Befunde 2.390*",
            block="D-ABBILDUNG",
            umbau="beides",
            fertig=True),  # Fachpruefung von Mail und GUI vor der Straffung
    Schritt(40, "ALTBESTAND STILLLEGEN",
            "✔ ERLEDIGT AM 12.09. (Befunde 2.404*): der Screening-Rang "
            "altert nicht mehr still (`RANG_MAX_ALTER_TAGE`, gemeldet je "
            "Lauf), die leere Kandidatenliste sagt warum sie leer ist, und "
            "die Leser des Altbestands sind aufgeschrieben (2.404-leser). "
            "⚠️ Punkt (3) Log war schon am selben Tag behoben, Punkt (1) "
            "Verfall am Notebook gelaufen. ⚠️ NICHT ERLEDIGT und "
            "ausdruecklich VERSCHOBEN: die 4.071 Marktscan-Kandidaten - sie "
            "sind erst mit Schritt 39 entscheidbar, weil vorher niemand "
            "sagen kann, ob sie Wert haben. "
            "⚠️ NUTZERVORGABE 12.09.: *,damit wir nicht laufend ueber "
            "Altbestaende stolpern, sollten wir diese sauber stilllegen'*. "
            "AUFNAHME statt Einzelfaelle: (1) die alte Hebelkette - Screening "
            "ist AUS (2.384), der Verbraucher steht seit 10.08., die 1.029 "
            "wartenden Kandidaten sind verfallen gesetzt; offen bleibt die "
            "Anzeige in der Oberflaeche (2.388). (2) Der Marktscan bleibt AN, "
            "aber 4.071 Kandidaten warten unbearbeitet - erst mit Schritt 39 "
            "entscheidbar. (3) Das LOG: ein abgesprochener Zustand wird 262x "
            "in 72 h als ERROR gemeldet (2.389-log). (4) Was NICHT stillgelegt "
            "wird und warum: `hebel_triggers` bleibt als Messgrundlage von "
            "`messe_allocator_gegen_zufall.py` stehen. ⚠️ Jede Stilllegung "
            "braucht den Satz ,wer liest das noch' - eine geloeschte "
            "Messgrundlage kommt nicht zurueck.",
            "Nutzervorgabe 12.09.; Befunde 2.388, 2.389-log, 2.404*",
            # ⚠️ FERTIG TROTZ EINES VERSCHOBENEN PUNKTES - und das ist keine
            # Aufweichung der Vorgabe SCHRITT-FUER-SCHRITT. Die 4.071
            # Marktscan-Kandidaten waren von Anfang an als "erst mit Schritt
            # 39 entscheidbar" beschrieben: ob sie Wert haben, kann vor dem
            # P-Scan niemand sagen. Sie gehoeren also zu 39, nicht als Rest
            # zu 40. Alles, was 40 SELBST leisten kann, ist geleistet.
            fertig=True, block="D-BETRIEB",
            umbau="alt"),  # Altbestand der alten Hebelkette aufgeraeumt
    Schritt(39, "P-SCAN - ENTDECKUNG AUS DEM POTENTIAL",
            "⚠️ NUTZERENTSCHEIDUNG 12.09.: *,Marktscan ist fuer mich "
            "klar, trending koennte eine Loesung sein'* - und der Auftrag, "
            "das fachlich zu entscheiden. ➔ NAECHSTER TEILSCHRITT IST DAMIT "
            "gesetzt: `trending` messen (2.406-luecke, 812 Kandidaten, nie "
            "ausgewertet), BEVOR ein Ersatz gebaut wird. Erst wenn feststeht, "
            "ob Aufmerksamkeit besser traegt als Kursanstieg, ist "
            "entscheidbar, ob der Scan eine neue Quelle oder eine neue "
            "Bewertung braucht. ✔ GEMESSEN AM 12.09. (2.406-luecke), und "
            "das Ergebnis dreht die Frage um: von 94 auswertbaren Faellen "
            "waren 24 Coins AUCH im Trending - Median -16,3 %% gegen Markt, "
            "nur 29,2 %% besser. Die uebrigen 70 liegen bei -3,1 %% und 44,3 "
            "%%, also auf Zufallsniveau. ➔ DER SCAN LIEGT NUR WEGEN DER "
            "TRENDING-UEBERSCHNEIDUNG UNTER DEM ZUFALL. ,Auch im Trending' "
            "ist ein NEGATIVES Merkmal, keine Quelle - Aufmerksamkeit PLUS "
            "Anstieg ist Ueberhitzung. ⚠️ Damit ist ,trending als Loesung' "
            "vom Tisch, und ein neuer Gedanke steht im Raum: es als "
            "AUSSCHLUSS zu verwenden. Vorher gehoert n=24 vergroessert. "
            "⚠️ Die Alters-Luecke (685 Zeilen) BLEIBT bewusst offen - sie zu "
            "schliessen waere billig (91 von 129 Coins haben ihr Alter in "
            "der eigenen Tabelle), wuerde aber genau die schlechteren "
            "Kandidaten hereinlassen. ✔ UND DIE HANDELBARKEIT TRAEGT "
            "(2.405-folge): 42,6 %% positiv gegen 32,1 %%, und der "
            "Unterschied bleibt INNERHALB derselben Groessenklasse (41,9 %% "
            "gegen 25,0 %% mit Marktklammer) - es ist also kein "
            "Groesseneffekt. ⚠️ Er macht den Scan aber nur weniger schlecht, "
            "nicht gut: 44,4 %% gegen 44,7 %% Zufall. ➔ FUER DIESEN SCHRITT "
            "HEISST DAS: der Handelbarkeitsfilter gehoert in JEDE Loesung "
            "(was man nicht kaufen kann, ist keine Empfehlung), aber er ist "
            "kein Ersatz fuer eine Bewertung. ⚠️ DIE SELEKTION BLEIBT "
            "UNHEILBAR und muss bei jeder Aussage mitgenannt werden: von "
            "374 bewerteten Kandidaten wurden 114 verfolgt, davon 67 %% der "
            "hoeher eingestuften gegen 23 %% der niedrigeren. Die Verzerrung "
            "geht ZUGUNSTEN des Scans - er verliert trotzdem. "
            "⚠️⚠️ NUTZERVORGABE 12.09. - DAS ZIEL DIESES SCHRITTS IN "
            "EINEM SATZ: *,der Marktscan sollte zukuenftig ebenfalls aus "
            "einer sinnvollen BEWERTUNG erfolgen - ein erst kuerzlich "
            "gestiegenes Asset ist keine Empfehlung, sondern eher ein "
            "Risiko'*. ✔ BELEGT (2.406): alle 114 gemessenen Kandidaten "
            "stammen aus `top_gainers`, keiner war beim Fund im Minus, und "
            "das Ergebnis ist Ø -9,6 %%. Der Scan hat nie BEWERTET, er hat "
            "SORTIERT - Regel 4 in Reinform, ein Fakt ueber die "
            "Vergangenheit als Begruendung fuer die Zukunft. ⚠️ Und die "
            "zweite Quelle `trending` (812 Kandidaten, 20 %%) ist NIE "
            "gemessen worden (2.406-luecke) - sie misst Aufmerksamkeit statt "
            "Kursanstieg und faellt damit nicht automatisch unter denselben "
            "Verstoss. Diese Luecke gehoert VOR jedes Urteil ueber die "
            "Entdeckung. "
            "✔ DIE WERTPRUEFUNG IST GELAUFEN (Nutzerauftrag 12.09., Befund "
            "2.405): der alte Marktscan schlaegt den Zufall NICHT - 40,4 %% "
            "seiner Funde liefen besser als der Markt, ein Zufallsgriff in "
            "die eigene Watchlist erreicht 44,7 %%. ⚠️ DAMIT HAT DIESER "
            "SCHRITT EINEN MASSSTAB: der Ersatz muss 44,7 %% schlagen, nicht "
            "null. ⚠️ Und die 4.071 unbearbeiteten Kandidaten sind kein "
            "Rueckstand mehr - eine Quelle ohne nachweisbaren Wert erzeugt "
            "keinen Verlust durch Warten. ➔ ZWEI PUNKTE VORGEZOGEN (2.405-"
            "folge): (a) ,bei Bitpanda handelbar' liegt bei -3,13 %% gegen "
            "-7,12 %% insgesamt - wenn das traegt, ist der HANDELBARKEITS-"
            "Filter mehr wert als die ganze Bewertung des Scans, und das "
            "waere billig zu haben; (b) die Selektion heilen: solange nur "
            "verfolgt wird, was der Scan selbst hoch einstuft, misst man "
            "seine Konsistenz statt seiner Guete. "
            "⚠️ ERSATZ FUER DEN ALTEN MARKTSCAN, in drei Stufen (2.385-pscan): "
            "(1) SCHATTEN - denselben gemessenen Rang wie in der Kette taeglich "
            "fuer ALLE Werte mitschreiben, fuer die die Messbasis reicht (heute "
            "42, davon 35 ausserhalb der Watchlist); (2) MESSEN - traegt ein "
            "hoher Rang ausserhalb der Watchlist mehr Potential (`bewegung_r`, "
            "nicht Zielerreichung)? Ohne Nachweis keine Empfehlung; (3) erst "
            "dann eine Aufnahme-Liste, gefiltert auf bei Bitpanda handelbare "
            "Werte. ⚠️⚠️ DER ,ENGPASS ONCHAIN-BASIS (66 SYMBOLE)' WAR EIN "
            "DENKFEHLER (Befund 2.408, korrigiert 12.09.): das ist die "
            "MESSBASIS aus `messdaten.db`, nicht die ANWENDUNGSBASIS. Der "
            "Live-Rang kommt aus CoinGecko-Markets und den "
            "Binance-Perpetuals und braucht KEINE Historie - turnover 233 "
            "Symbole, funding 851, BEIDE 137, davon 112 ausserhalb der "
            "Watchlist. ➔ DER P-SCAN IST HEUTE BAUBAR, ohne eine einzige "
            "neue Datenquelle. ✔ RECHERCHE EXTERN GELAUFEN (2.409): keine "
            "fertige Loesung passt - sie liefern Faktoren OHNE Messung, "
            "was der Vierfachtest verbietet. DefiLlama (TVL, frei, ohne "
            "Schluessel) ist als DRITTER BEITRAG interessant, gehoert "
            "aber in die Kette (Schritt 38), nicht in die Entdeckung. "
            "⚠️ OFFEN BLEIBT DER VORBEHALT (2.408-vorbehalt): gemessen "
            "ist der Beitrag auf 66 Symbolen, angewendet wuerde er auf "
            "233 - die Form des H-Fehlers, und genau der Inhalt von "
            "Stufe 2. ⚠️⚠️ DER P-SCAN IST DAMIT TEIL 4 VON SCHRITT 49 "
            "geworden - er haengt an derselben Datenbasis, und die muss "
            "zuerst sauber sein (Befund 2.410: der gemessene und der "
            "angewendete `turnover` sind heute nicht dieselbe Groesse). "
            "Was HIER bleibt: der alte Marktscan, seine Bewertung und die "
            "Frage, ob ,auch im Trending' als AUSSCHLUSS taugt. Bis dahin "
            "bleibt der alte Marktscan an.",
            "Nutzerauftrag 12.09.; Befunde 2.385, 2.385-pscan",
            block="D-BEWERTUNG",
            umbau="beides"),  # ersetzt den alten Marktscan durch Entdeckung aus dem Potential
    Schritt(46, "D2 - STRAFFEN UND KORREKT ABBILDEN",
            "⚠️ NUTZERVORGABE 12.09. (REIHENFOLGE-12-09): *,ist die "
            "deterministische Ebene sauber und stabil, dann sollten wir "
            "diesen Bereich STRAFFEN und KORREKT ABBILDEN'*. D1 ist "
            "beantwortet (Befund 2.399): stabil im Betrieb, nicht sauber in "
            "den Belegen. Dieser Schritt raeumt die ABBILDUNG auf - nicht "
            "die Messung. (1) CLAUDE.md nachziehen: sie behauptet, der "
            "Selbsttest der Messanlage fehle - er ist seit Befund 2.204 "
            "gelaufen. ⚠️ Die wichtigste Datei des Projekts darf keine "
            "geschlossene Luecke behaupten. (2) DIE RANGFOLGE: 20 offene "
            "Schritte ohne Ordnung, `soll_ist` meldet ,naechster Schritt 25' "
            "waehrend an 44 gearbeitet wird. Der Plan muss die Arbeit "
            "abbilden, sonst ist er Zierde. (3) Erledigte Befunde "
            "schliessen (2.395-erledigt). (4) Trichter, Mail und GUI muessen "
            "DASSELBE sagen - das ist Schritt 41, er gehoert hierher. ⚠️ "
            "KEINE neue Messung, kein neuer Beitrag, keine LLM-Aenderung."
            "\u2714\u2714\u2714 ERLEDIGT 13.09. ABENDS - DREI TEILE GEBAUT, DER "
            "VIERTE IST SCHRITT 41 UND BLEIBT ES. "
            "\u2714 (1) CLAUDE.md: der Satz ,der Selbsttest der Anlage gegen "
            "bekannte Wahrheit fehlt weiterhin' ist weg - er ist am 08.09. "
            "gelaufen (2.204). Der Abschnitt nennt jetzt Fehlalarmquote (0 von "
            "50 Nullwelten), Aufloesung (+0,0293 R bei 80 %% Fundquote) und die "
            "ZWEI Einschraenkungen, die dazugehoeren: die Dreierregel schliesst "
            "eine wahre Quote bis 6 %% nicht aus, und ein Selbsttest prueft die "
            "ANLAGE, nicht die DATEN. \u26a0\ufe0f DABEI FIELEN VIER WEITERE "
            "VERALTETE ZAHLEN AUF, alle nachgezaehlt: 148 F-Nummern (sind 75) \u00b7 "
            "85 Methodik-Abschnitte (sind 124) \u00b7 72 %% von 281 Werkzeugen "
            "Altbestand (sind 176 von 308 = 57 %%) \u00b7 92.000 Zeilen (sind "
            "107.000). Und das Werkzeugregister widersprach SICH SELBST - "
            "Kopfzeile 281, Tabelle 308; die 281 war im Generator hart "
            "hinterlegt und wird jetzt gezaehlt. "
            "\u27a4 NEUES PAKET `Abbildung` (7 Pruefungen): es vergleicht die "
            "Zahlen in CLAUDE.md gegen die ERZEUGTEN Register, statt sie zu "
            "wiederholen - von Hand nachgezogen laufen sie wieder weg. "
            "\u2714\u2714 (2) DIE RANGFOLGE - und hier war noch ein Fehler drin. Die "
            "Bloecke vom 12.09. ordnen nach DRINGLICHKEIT, kannten aber keine "
            "ABHAENGIGKEIT: gemeldet wurde Schritt 28, dessen eigener Text sagt "
            "*,ERST NACH DEM ROLLOUT messen - vorher misst man den alten "
            "Stand'*. Das ist derselbe Fehler wie 2.395, eine Ebene tiefer. "
            "\u27a4 GEBAUT: das Feld `wartet_auf`, drei Eintraege aus den Texten "
            "selbst (28\u219227 \u00b7 31\u219241 \u00b7 33\u219242), und die Ausgabe zeigt "
            "Wartende getrennt an. \u26a0\ufe0f NICHT umsortiert - das haette die "
            "Abhaengigkeit versteckt. \u27a4 UND DIE ORDNUNG IST JETZT EINE "
            "FUNKTION (`soll_ist.geordnet()`): Plan und Pruefung riefen bis "
            "eben je eine eigene Sortierung, und als `wartet_auf` dazukam, "
            "meldete die eine 32 und die andere 28 - ein Test, der seine Kopie "
            "prueft, merkt so etwas nicht. Fuenf neue Waechter, darunter einer, "
            "der FINDET, wenn ein Schritt ,ERST NACH' sagt und das Feld nicht "
            "traegt, und zwei Regeltests auf gestellten Schritten. "
            "\u2714 (3) BEFUNDE GESCHLOSSEN: 2.146-luecke und 2.343 standen schon "
            "auf gilt. Dazu 2.399-abbildung (drei seiner vier Punkte sind "
            "erledigt, der vierte ist 2.390-gui) und 2.400-hebel (,die Quote ist "
            "gemessen, der Stop nicht' - seit 2.435-optimum und 2.437 stimmt das "
            "nicht mehr). \u26a0\ufe0f Was davon UEBRIG bleibt, steht als 2.438 und "
            "wird nicht mitgeschleppt: im Betrieb kommt der Stop in 81,5 %% der "
            "Faelle aus dem Modell, dessen Median mit 8,0 %% zwar genau auf dem "
            "Gipfel liegt - ob die EINZELentscheidung traegt, ist nicht gemessen. "
            "\u26a0\ufe0f\u26a0\ufe0f (4) TRICHTER, MAIL UND GUI - DAS IST SCHRITT 41 UND "
            "BLEIBT EIN EIGENER SCHRITT. Er steht offen im selben Block "
            "(D-ABBILDUNG) mit fuenf Unterpunkten (Fachpruefung der Zahlen, "
            "Redundanz, Lesbarkeit, Begriffe, Gleichlauf mit der GUI). Er ist "
            "hier BENANNT, nicht erledigt - und 31 wartet nachweislich auf ihn.",
            "Nutzervorgabe 12.09.; Befunde 2.399, 2.399-abbildung",
            block="D-ABBILDUNG",
            umbau="alt",
            fertig=True),  # D2 - was falsch abgebildet ist, stammt aus der Zeit davor
    Schritt(49, "TURNOVER: EINE GROESSE STATT ZWEI",
            "⚠️⚠️ DER FEHLER, DER HEUTE WIRKT (Befund 2.410): der GEMESSENE "
            "und der ANGEWENDETE `turnover` sind nicht dieselbe Groesse. "
            "Beide rechnen `Volumen / (Preis x Umlaufmenge)`, aber die MENGE "
            "kommt aus zwei Quellen - die Messung nimmt `splycur` (Coin "
            "Metrics), der Betrieb `circulating_supply` (CoinGecko). 16 von "
            "33 vergleichbaren Symbolen weichen ab, LINK aus der Watchlist "
            "um -25,2 %. ⚠️ Betroffen ist EINER DER ZWEI TRAGENDEN "
            "BEITRAEGE, und er traegt die groessten Stufen im System (+3,15 "
            "bis -2,40). "
            "➔ DREI TEILE. (A) `splycur` NACHLADEN - unsere Kopie endet am "
            "2026-08-28/29, die Quelle steht auf 2026-09-12 (2.417-frische). "
            "Lueckenschluss, kein Umbau. (B) `marktrang.turnover_werte` auf "
            "`splycur` UMSTELLEN - danach messen und wirken beide Seiten auf "
            "derselben Groesse, die registrierte Tabelle bleibt gueltig und "
            "`MESSBASIS` bleibt per Definition richtig. (C) "
            "`data/markt_historie.db` NICHT in Betrieb nehmen - sie bleibt "
            "als Beleg fuer 2.416/2.417 liegen. "
            "⚠️⚠️ DIE RICHTUNG IST DIE UMGEKEHRTE VON DER, DIE ICH AM 12.09. "
            "VORGESCHLAGEN HATTE: nicht die Messung auf eine breitere "
            "Quelle heben, sondern die ANWENDUNG an die Messung angleichen. "
            "Der Grund in einem Satz: es gibt keine freie historische "
            "Umlaufmenge - neun Anbieter direkt geprueft, keiner liefert sie "
            "ohne Schluessel (2.417). Die Kuerzung auf `Volumen / "
            "Marktkapitalisierung` waere rechnerisch richtig gewesen, aber "
            "der einzige freie Weg dahin holt die TOP 250 VON HEUTE - ein "
            "Survivorship-Filter (2.416) - und reicht nur 366 Tage weit "
            "(2.416-laenge). "
            "⚠️⚠️⚠️ WAS BESTEHEN BLEIBT UND GENANNT GEHOERT: der registrierte "
            "Vorbehalt der Groesse - `turnover` deckt 66 von 536 Symbolen "
            "ab, sein Nullband ist dreimal so breit wie bei den anderen, das "
            "Urteil wandert mit der Saat (2.408-vorbehalt). Dieser Schritt "
            "loest den Fehler, NICHT den Vorbehalt. Mit freien Mitteln ist "
            "der Vorbehalt nicht aufloesbar. "
            "📇 DIE UNTERSUCHUNG DAZU steht in den Befunden, nicht hier: "
            "2.410 (der Fehler) · 2.411 bis 2.413 (Ladelauf und R-R11) · "
            "2.414 (Zeitfenster) · 2.415 (Verteilung) · 2.416 (Survivorship, "
            "Laenge, Reihenfolge, Norm) · 2.417 (Quellensuche, Frische, "
            "Naeherung). ⚠️ Der P-Scan war einmal Teil 4 dieses Schritts und "
            "ist zurueck in Schritt 39 - er haengt an seiner EIGENEN "
            "Datenfrage. "
            "✔✔✔ ERLEDIGT AM 13.09. (A) `hole_fremdreihen.py splycur` "
            "gebaut - es gab bis dahin KEINEN Aufruf; 66 von 66 geladen, bis "
            "2026-09-12, Messmenge unveraendert (2.418). (B) "
            "`marktrang.turnover_werte` stellt BEIDE Haelften auf die "
            "Messquelle um: Binance-Stueckvolumen durch `splycur` mit "
            "Frischegrenze 21 Tage (2.419). ⚠⚠ DER SCHRITT HAT DABEI EINEN "
            "ZWEITEN FEHLER GEFUNDEN, den 2.410 zwar nannte und ich zuerst "
            "uebersah: der ZAEHLER wich staerker ab als der Nenner (57,1 % "
            "gegen 86,2 % gleiches Fuenftel). Und eine WICHTIGERE "
            "Nebenwirkung: der Betrieb sieht jetzt 60 statt 33 Symbole - der "
            "alte Weg las die CoinGecko-Top-250 und verlor damit die Haelfte "
            "der Messbasis, derselbe Survivorship-Schnitt wie in 2.416, nur "
            "auf der Anwendungsseite (2.419-breite). ✔ R-R11 vor dem Bau "
            "erfuellt (2.419-rr11). ✔ Paket Turnoverquelle umgeschrieben, 14 "
            "Waechter. ⚠ OFFEN GEBLIEBEN und VORGELEGT: 2.419-saetze - zwei "
            "veraltete Zeilen in `pruefe_marktrang.py`, vor diesem Schritt "
            "schon rot, gehoeren in einen eigenen Zug.",
            "Befunde 2.410 bis 2.419-saetze; Nutzerauftraege 12./13.09.; "
            "Vorgaben KEINE-TEILLOESUNG, MESSSTANDARD-VOR-DER-MESSUNG",
            fertig=True, block="D-BETRIEB",
            umbau="neu"),  # turnover ist ein Beitrag des neuen Bewertungswegs
    Schritt(50, "ZWEI STRUKTURMAENGEL IN DEN MESSDATENBANKEN",
            "⚠️ Beide stammen aus Schritt 45 und sind dort GEPRUEFT worden - "
            "sie stehen hier, weil sie Struktur aendern und nicht nebenbei "
            "gehoeren. "
            "(A) `messreihen` FUEHRT FUER SIEBEN SYMBOLE DIE FALSCHE KLASSE "
            "(2.421). Der Primaerschluessel ist `symbol TEXT PRIMARY KEY`, "
            "kann also nur EINE Klasse je Symbol; `price_history_ohlc` hat "
            "`(symbol, assetklasse, currency, date)` und fuehrt zwei. "
            "Betroffen sind Ticker-Kollisionen: BOND, C, DASH, DIA, MDT, "
            "STX, T. ✔ HEUTE FOLGENLOS - `lade()` liefert die Krypto-Reihe, "
            "und `_reihen_roh` nimmt die Klasse aus der Spalte (Fix 07.09.). "
            "➔ ZU TUN: Primaerschluessel auf `(symbol, assetklasse)`, "
            "`lade_messreihen` schreibt beide, `klassen_aus_db` liefert "
            "`(symbol, klasse)` statt `symbol -> Klasse`. ⚠️ Es ist ein "
            "Schemawechsel - Sicherung zuerst, und die "
            "Pruefung ,keine NEUE Klassenkollision' wird danach auf eine "
            "LEERE Bekanntenliste gestellt. "
            "(B) KEINE MESSQUELLE FUEHRT `fetched_at` (2.359-abruf-loesung). "
            "⚠️⚠️ UND DIE NAHELIEGENDE LOESUNG WAERE DIE FALSCHE: "
            "`MAX(fetched_at)` sagt genau dasselbe wie die Aenderungszeit "
            "der Datei - wann zuletzt geschrieben wurde. Die Frage des "
            "Befundes ist *war der Abruf VOLLSTAENDIG?*, und die beantwortet "
            "nur eine ZAEHLUNG JE SYMBOL gegen eine Erwartungszahl (funding "
            "300, terminmarkt 122, splycur 66). ➔ ZU TUN, in EINEM Zug "
            "(KEINE-TEILLOESUNG): `fetched_at` pro Zeile in den drei "
            "Ladeskripten, eine Erwartungstabelle, und "
            "`datenfrische._stand_datei` meldet ,X von Y Symbolen im letzten "
            "Lauf beruehrt' statt eines Zeitstempels. "
            "⚠️⚠️ RISIKOPRUEFUNG 13.09., VOR JEDER AENDERUNG - UND SIE HAT "
            "MEINE EIGENE EINSCHAETZUNG WIDERLEGT. Ich hatte (A) als "
            "*,Schemawechsel an 5,1 Mio Zeilen`* beschrieben. Falsch: das "
            "sind die Zeilen von `price_history_ohlc`, und DIE wird gar "
            "nicht angefasst. `messreihen` hat 1.327 Zeilen, sieben "
            "Dateien lesen sie (`lade_messreihen`, `uebernehme_messreihen`, "
            "`simuliere_bremse`, `messe_ueberleben` und drei Pruefskripte), "
            "und der Wechsel erzeugt GENAU SIEBEN neue Zeilen - eine je "
            "Ticker-Kollision. ➔ (A) IST DAMIT EIN KLEINER, gut umgrenzter "
            "Eingriff, kein Risiko fuer die Messbasis. "
            "⚠️ FUER (B) HAT DIE PRUEFUNG ZWEI DINGE ERGEBEN. (1) Die "
            "Spalte ist additiv: nur EINE Stelle im ganzen Projekt macht "
            "`SELECT *` auf eine der drei Tabellen (`pruefe_pakete.py`, "
            "`FROM terminmarkt`) - die gehoert vorher angesehen, sonst "
            "stoert eine neue Spalte niemanden. (2) ⚠️ DIE ERWARTUNGSZAHL "
            "GEHOERT AN DIE MESSBASIS-DEFINITION, NICHT AN EINE TABELLE: "
            "`terminmarkt_tag` hat 100 Symbole, `terminmarkt` 122, die "
            "VEREINIGUNG 122 - und genau die ist `MESSBASIS[oi]`. `funding` "
            "hat 302 Symbole, davon 300 in `messmenge.V1`. Wer gegen eine "
            "Tabelle zaehlt statt gegen die Messbasis, erzeugt einen "
            "Fehlalarm - mir ist er beim Pruefen selbst passiert. "
            "⚠️ REIHENFOLGE BLEIBT: (B) vor (A). Nicht wegen des Risikos - "
            "das ist bei beiden klein -, sondern weil (B) zeigt, ob die "
            "Ladelaeufe vollstaendig sind, und (A) danach auf einer "
            "nachweislich vollstaendigen Basis stattfindet. "
            "✔✔✔ TEIL B ERLEDIGT AM 13.09. (Befunde 2.425 bis "
            "2.425-additiv) - ABER NICHT WIE HIER BESCHRIEBEN. ⚠️⚠️ "
            "`fetched_at` PRO ZEILE WAERE FALSCH GEWESEN, und beides ist vor "
            "dem Bau geprueft worden: es sagt dasselbe wie die Dateizeit, "
            "und alle INSERTs der Ladeskripte schreiben POSITIONELL "
            "(`VALUES (?,?,?)`) - eine vierte Spalte haette sie STUMM "
            "gebrochen. ➔ GEBAUT WURDE EINE ZEILE JE SYMBOL "
            "(`abruf_symbol`), in allen drei Messdateien, geschrieben nur "
            "im Erfolgszweig. ⚠️ `hole_terminmarkt_historie` fuehrte schon "
            "`abruf_status` je (Symbol, Tag) - das ist keine Dopplung: es "
            "sagt WELCHE TAGE vorliegen und traegt keinen Zeitstempel. "
            "✔ AM ECHTEN LAUF NACHGEWIESEN: `datenfrische` meldet jetzt "
            "*,2026-09-13T10:05:26 (65 von 66 Symbolen)'* - und die fehlende "
            "ist ZRX, ein echter voruebergehender Abrufausfall, den die "
            "Dateizeit nicht gesehen haette. ✔ Paket `Abrufvermerk`, 9 "
            "Pruefungen, gegengeprueft mit einem absichtlich falsch "
            "platzierten Vermerk. ➔ OFFEN BLEIBT NUR TEIL A. "
            "✔✔✔ TEIL A ERLEDIGT AM 13.09. (Befunde 2.426 bis "
            "2.426-pruefungen). Sicherung vorher: "
            "`data/messdaten_vor_klassenschluessel_13_09.db`, 1,57 GB, "
            "`quick_check` ok. Migration an einer KOPIE vorabgeprueft, dann "
            "gelaufen: 1.327 → 1.334 in `messreihen` UND "
            "`messreihen_status` - letzteres hatte dieselbe Mehrdeutigkeit "
            "und ist mitgewandert. ⚠️ DIE EIGENTLICHE AENDERUNG WAR NICHT "
            "DAS SCHEMA, sondern die ZUORDNUNG: `klassen_aus_db` liefert "
            "jetzt `symbol -> Menge von Klassen` statt einer einzelnen, und "
            "der Filter fragt `klasse not in ...` statt `!=`. Vier von "
            "sieben Lesern angepasst. ✔ MESSUNGEN BITGLEICH: `lade()` 536 "
            "Reihen = V1, DASH weiter die Krypto-Reihe mit 2.722 Punkten, "
            "`_reihen_roh` je Klasse 536/470/293/35 wie vorher. ✔ Suite "
            "2.343, dieselben drei bekannten Ausfaelle. ⚠️ Eine Pruefzeile "
            "hing am WORTLAUT der Filterzeile und fiel durch die "
            "Verbesserung - Absicht unveraendert, nachgezogen samt "
            "Begruendung (2.426-pruefungen).",
            "Befunde 2.421, 2.421-rot, 2.359-abruf-loesung; ausgezogen aus "
            "Schritt 45 am 13.09.",
            fertig=True, block="D-BETRIEB",
            umbau="alt"),  # Strukturmaengel der Messdatenbanken, vor dem Umbau entstanden
    Schritt(45, "DIE VERGESSENEN VIER - AUS DER GEGENPRUEFUNG",
            "⚠️ Aus der Gegenpruefung vom 12.09. (Befund 2.395): vier offene "
            "Punkte standen in KEINEM Schritt. (1) 2.380-annahmen - drei "
            "gesetzte Annahmen sind seit dem 11.09. mit ,zur Abstimmung' "
            "markiert und nie abgestimmt worden, darunter "
            "`hebelfuehrung.KOPPEL_TAGE` (wie weit ein Signal einer "
            "Position zugerechnet wird). ⚠️ Eine Annahme, die niemand "
            "bestaetigt hat, ist kein Vorgabewert, sondern eine offene "
            "Frage - Nutzervorgabe ,bei Zweifel in die Abstimmung'. "
            "⚠️⚠️ NACHTRAG 13.09.: ALLE DREI WAREN AM 11.09. ENTSCHIEDEN und "
            "der Befund nur nie nachgezogen. Das Fenster steht seither auf "
            "24 STUNDEN (2.380-fenster; `KOPPEL_TAGE` = 1.0, bewacht von "
            "`ausrollen_paket_b`); ohne bekannten Stop gilt VARIANTE B, und "
            "die hier genannte Annahme ,ganzes Eigenkapital' ist genau die "
            "vom Nutzer ABGELEHNTE Variante A (2.380-ohne-stop); der "
            "urspruengliche Stop ist als ,Verlust bis zum Plan-Stop' gebaut "
            "und mit ,Rest wie empfohlen' angenommen. (2) "
            "2.389-richtung - die Absicherung verliert Signale an der "
            "Richtungspflicht. (3) 2.359-abruf - keine der drei Messquellen "
            "fuehrt `fetched_at`; das gemeldete Alter ist das Datenalter, "
            "nicht das Abrufalter (zwei Alter, Nutzervorgabe). (4) "
            "2.148-sperre / 2.149-prod - `messreihen` hat den "
            "Primaerschluessel ohne `assetklasse`, die Produktionsdatenbank "
            "die Spalte gar nicht. ⚠️ ZWEI WEITERE BEFUNDE SIND ERLEDIGT "
            "und nur nicht nachgezogen (2.395-erledigt): 2.146-luecke (alle "
            "neun Werte haben laengst eine Kursreihe) und 2.343 "
            "(`hebel_signals` ist die Tabelle der ALTEN Pipeline, kein "
            "Ausfall). "
            "⚠️⚠️ STAND 13.09. - ZWEI DER VIER SIND BEANTWORTET, ZWEI SIND "
            "AUSGEZOGEN, UND DIE ZWEI ,ERLEDIGTEN' STIMMTEN NICHT GANZ. "
            "✔ 2.146-luecke: es sind SIEBEN von neun, nicht neun. ASTER und "
            "MON haben null Punkte - mit 318 bzw. 269 USD-Tagen unter "
            "`MIN_KERZEN` = 400, weil die Coins erst seit 10/2025 und "
            "11/2025 existieren. Datenlage-Grenze, in 2.185-rest schon "
            "registriert. "
            "✔ 2.343: begruendetes Schweigen - `hebel_analyst` hat KEINE "
            "Aufrufstelle im Projekt, und das Paket `gesamt` haelt das jetzt "
            "als Zeile fest (gegengeprueft: mit Testimport rot). "
            "✔ PUNKT 4 (2.148-sperre / 2.149-prod): die Klassenkollision ist "
            "real - sieben TICKER-Kollisionen, DASH ist DoorDash UND die "
            "Kryptowaehrung, T ist AT&T UND Threshold - aber FOLGENLOS: "
            "`lade()` liefert fuer alle sieben die Krypto-Reihe, und "
            "`_reihen_roh` ueberspringt den `messreihen`-Filter seit dem "
            "07.09. (2.421). Der Schemafix ist damit keine SPERRE mehr, "
            "sondern Aufraeumen - ausgezogen nach Schritt 50. "
            "➔ PUNKT 3 (2.359-abruf): geprueft, keine der drei Quellen "
            "fuehrt `fetched_at`. ⚠️ Eine Spalte allein loest es aber NICHT: "
            "`MAX(fetched_at)` sagt dasselbe wie die Dateizeit. Die Frage "
            ",war der Abruf VOLLSTAENDIG?' beantwortet nur eine ZAEHLUNG je "
            "Symbol gegen eine Erwartungszahl - ebenfalls Schritt 50. "
            "⚠️ WAS IN DIESEM SCHRITT BLEIBT: (1) 2.380-annahmen - drei "
            "Annahmen, die NUR DER NUTZER entscheiden kann; sie sind ihm am "
            "13.09. vorgelegt. (2) 2.389-richtung - die Absicherung verlor "
            "an EINEM Lauf zwei Signale an der Richtungspflicht und am "
            "naechsten nicht. ⚠️ Am Desktop NICHT pruefbar: die Produktion "
            "laeuft am Notebook, die Desktop-Kopie hat 5 statt 1.998 Zeilen. "
            "Es braucht eine Beobachtung ueber mehrere NB-Laeufe, keine "
            "Codeaenderung ins Blaue. "
            "⚠️⚠️⚠️ NACHGETRAGEN 13.09. - DAS WAR FALSCH, und der Nutzer "
            "hat es sofort bemerkt (*,du hast ein DB Backup'*). Unter "
            "`K:/My Drive/Claude_Austauschordner/DB_Backups` liegen sieben "
            "Produktionssicherungen, die juengste vom 12.09. 06:46. An ihr "
            "GEMESSEN (2.422): die Absicherung kann seit dem 22.08. nur noch "
            "HALTEN sagen. Alle 12 Absicherungssignale haben `richtung = "
            "NULL`, und `BRAUCHT_RICHTUNG` ist `(KAUFEN, NACHKAUFEN)` - die "
            "beiden HANDELNDEN Aktionen werden strukturell abgelehnt, HALTEN "
            "und VERKAUFEN kommen durch. Betroffen sind ZWEI GEHALTENE "
            "Positionen (3QSS 218,25 Stueck zu 2,05 EUR, DBPK 1.739,16 zu "
            "0,1713 EUR); in 22 Lauftagen seit dem 22.08. gab es an DREI "
            "Tagen ein Absicherungssignal, bei DBPK an EINEM. "
            "➔ DIE URSACHE IST DAMIT BEKANNT und der Punkt ist hier fertig. "
            "Was bleibt, ist eine ENTSCHEIDUNG und keine Messung: braucht "
            "die Absicherung ueberhaupt eine Richtung - sie ist per "
            "Konstruktion ein SHORT auf den Markt - oder muss der Prompt sie "
            "fuer diese Klasse liefern? Das ist eine ROLLENFRAGE und gehoert "
            "in den L-Block (Schritt 33), nicht in den D-Block.",
            "Gegenpruefung 12.09.; Befunde 2.395, 2.395-erledigt",
            fertig=True, block="D-BETRIEB",
            umbau="alt"),  # vergessene Punkte aus der Zeit vor dem Umbau
    Schritt(44, "DIE KETTE GERADEZIEHEN - TRICHTER, WAECHTER, "
            "ENTSCHEIDUNGSHILFE TRENNEN",
            "✔ PUNKTE 1, 3 UND 4b GEBAUT AM 12.09. (Befund 2.396): vier "
            "Verlustarten, Z1 immer im Bericht, LLM-2 Rolle G mit eigener "
            "Zeile. ✔ PUNKTE 2a UND 2b EBENFALLS (Befund 2.407): die "
            "Vier-Felder-Messung ist vollstaendig - die Nein-Zeile traegt "
            "die Bewertung, und der Entscheider-Verlust hinterlaesst eine "
            "aufloesbare Zeile statt eines `return`. ✔ PUNKT 4 entschieden "
            "und zurueckgezogen (2.397): der Widerlegungspreis bleibt. ⚠️ "
            "OFFEN BLEIBEN: (4a) ihn in der Mail eindeutig kennzeichnen "
            "(gehoert in Schritt 41), (2.407-namensschatten) die "
            "Wiederverwendung von `risk_veto` ist eine Schuld, keine "
            "Loesung, und die Wiederholung des E2E am Notebook gegen eine "
            "frische Sicherung (2.396-e2e). "
            "⚠️⚠️ DIE ABGRENZUNG, die der Nutzer am 12.09. gezogen hat - "
            "*,wir bauen seit Wochen am DETERMINISTISCHEN EINSTIEG je "
            "Strategie, das LLM wurde lange Zeit nicht angegriffen, auch "
            "nicht in der Planung'* - und seine eigene Auflage dazu: *,das "
            "ist mein Gefuehl, pruefen musst du das ueber Doku und Code'*. "
            "GEPRUEFT an der Git-Historie und am Plan, Ergebnis in Befund "
            "2.393-straenge: die Abgrenzung TRAEGT, der Stichtag ist aber "
            "der 22.08., nicht der 10.08. Bis dahin wurde der LLM-Strang "
            "sehr wohl gebaut (21 von 23 Aenderungen an `rolle_trader.py` "
            "fallen in die zwoelf Tage vom 10. bis 22.08.); SEITHER steht "
            "er - `rolle_analyst.py` seit 12.08., `gegenpruefer_rollen.py` "
            "seit 18.08., `zweite_meinung.py` inhaltlich seit 17.08. Im "
            "selben Zeitraum liefen im deterministischen Strang 33 "
            "Aenderungen an `entscheidungsrechnung.py` und 12 an "
            "`potential.py`, bis zum 11.09. ⚠️ Und die Planung: der erste "
            "LLM-Punkt ueberhaupt ist Schritt 33, angelegt am 11.09. - "
            "nachgelagert und ohne Bauschritte. ⚠️⚠️ Damit ist dieser "
            "Schritt der erste ECHTE Zugriff auf den LLM-Strang seit drei "
            "Wochen. Die Schieflage ist ein Versaeumnis, keine "
            "Fehlentscheidung. ⚠️ Deshalb AUFRAEUMEN, nicht Umbau: keine "
            "neue LLM-Faehigkeit, keine neue Rolle, kein zusaetzlicher "
            "Aufruf. ⚠️ NUTZERAUFTRAG "
            "12.09.: *,Z1 kommt gar nicht vor bzw. sehe ich "
            "diese in der Kette nicht, ZAI hat keine Stufe? Nichts tun ist "
            "heikel bzw. gemischte Stufe hoert sich schon seltsam an - wie "
            "lautet deine Empfehlung um die Kette inkl. LLMs sauber "
            "geradezuziehen?'* Alle drei Einwaende sind bestaetigt (Befund "
            "2.393). ⚠️⚠️ DER ENTWURFSFEHLER: EIN Zaehlwerk versucht DREI "
            "Fragen zu beantworten - wer kommt durch, ist die Antwort "
            "sauber, was raet das Sprachmodell. Der Vorschlag trennt sie in "
            "DREI ACHSEN. (1) VERLUSTARTEN TYPISIEREN: jeder "
            "`durchlauf.verloren()` bekommt eine Art - `nicht_gefragt` "
            "(Kosten), `nicht_moeglich` (Daten), `bewertet_nein` "
            "(Qualitaet), `betriebszustand` (SCHLIESSEN, gestakt). Damit "
            "loest sich die ,gemischte Stufe' 9 auf: 56 bewertet_nein gegen "
            "191 betriebszustand. ⚠️ (2) NACH DER PRUEFUNG REVIDIERT (Befunde 2.394, "
            "2.394-inventur): mein erster Vorschlag war ,die Zelle laeuft "
            "weiter' - das ist unnoetig und aendert den Ablauf. Der "
            "Kontrollarm ist SCHON GEBAUT: `_schreibe_nein` legt bei jedem "
            "NICHTS_TUN eine aufloesbare Zeile an (`ist_reines_llm_halten=1`, "
            "OHNE Mail), `backward_tracking` verfolgt sie ueber das "
            "Selbst-Halten-Schatten-Tracking, und in der Rollen-Kette sind "
            "das bereits 1.576 aufgeloeste Faelle. ⚠️ Die Nutzervorgabe "
            "*,in die Mail soll es nicht als Signal'* ist damit HEUTE SCHON "
            "erfuellt. WAS FEHLT, sind zwei Felder der Vier-Felder-Messung "
            "aus dem Konzept vom 29.08.: (2a) die Halten-Schattenzeile "
            "bekommt KEINE Bewertung, weil die Zelle Stufe 12 nie erreicht - "
            "in `_schreibe_nein` das Potential mitrechnen und mitschreiben, "
            "ohne Ablauf- und ohne Mailaenderung; (2b) beim "
            "ENTSCHEIDER-Verlust (1.251 in 7 Tagen) steht nur `return` - "
            "dort ebenfalls eine Schattenzeile, denn der Veto-Schatten-Motor "
            "dafuer laeuft seit 28.07. leer (2.394-motor). Erst mit beiden "
            "ist ,traegt das Modell' UND ,traegt die Bewertung' "
            "beantwortbar. ⚠️ TRICHTER-ENTSCHEIDUNG (vom Nutzer delegiert): "
            "NICHTS_TUN BLEIBT im Trichter gebucht, aber als Art "
            "`bewertet_nein`. Grund: der Trichter soll erklaeren, WARUM "
            "nichts herauskommt - eine Antwort ,nein' gehoert dazu; sie darf "
            "nur nicht mit Betriebszustaenden in einer Spalte stehen. "
            "Herausnehmen wuerde ausserdem alte und neue Laeufe "
            "unvergleichbar machen (R-R11). (3) EIGENE SICHTBARE SPUR FUER DIE DREI LLM-STELLEN und "
            "fuer Z1 - keine Filterstufen, sondern Vermerkstufen mit Quote: "
            "je Lauf ,Rolle A geliefert', ,Z1 sauber/angeschlagen', "
            ",Gegenpruefung Einwand/kein Einwand/nicht gefragt'. Heute "
            "steht davon NICHTS im Trichter, obwohl Z1 in 15,4 %% anschlaegt "
            "und Z.ai in 60 von 163 Faellen widerspricht. ⚠️⚠️ (4) DER WIDERLEGUNGSPREIS - VORSCHLAG "
            "ZURUECKGEZOGEN, GEMESSEN (Befunde 2.397, 2.397-antwort). Ich "
            "hatte vorgeschlagen, ihn aus der Geometrie zu nehmen. Die "
            "Messung an 1.084 echten Signalen (dieselbe Funktion zweimal "
            "gefahren) sagt: er macht den Stop in 81,5 %% ENGER, nicht "
            "weiter - denn ohne ihn greift der ATR-Rueckfall mit 2,5 x ATR, "
            "gedeckelt bei 25 %%. OHNE IHN ERZEUGT DIE KETTE GAR KEINEN "
            "HEBEL MEHR: bei 25 %% Stop erreicht kein r(q)-Wert der Spanne "
            "0,50-1,25 %% die Grenze von 2,0x (0,72x bis 1,80x). ➔ ER "
            "BLEIBT. ⚠️ WAS STATTDESSEN ZU TUN IST: (4a) EINDEUTIG "
            "KENNZEICHNEN (Nutzervorgabe 12.09.) - die Mail sagt heute nur "
            "beilaeufig ,Zone und Stop teils aus einer Modellangabe'; wo "
            "eine Modellzahl die Rechnung bestimmt, muss das AN DER ZAHL "
            "stehen (Schritt 41). (4c) UND DER BEFUND GEHOERT AN DEN ANFANG "
            "VON SCHRITT 42: der gesamte Hebel haengt an einer Zahl, die ein "
            "Sprachmodell nennt und deren Guete nie gemessen wurde. (4b) Z.AI WIEDER SICHTBAR (Nutzerwunsch 12.09.: "
            "*,wenn moeglich und sinnvoll haette ich ZAI wieder im "
            "System'*): sie LAEUFT bereits, und ihr Faktensatz ist seit dem "
            "Umbau gesund - Terminmarkt statt der drei defekten Groessen "
            "regime/trend/technische_konfluenz, die die "
            "Fakten-Entscheidungsmappe 13.5 verworfen hat. Was fehlt, ist "
            "SICHTBARKEIT: sie steht in keiner Zeile des Trichters, obwohl "
            "sie in 7 Tagen 60 Einwaende bei 163 Antworten erhoben hat. "
            "Ueber mehr als Sichtbarkeit wird nach der Wirkungsmessung "
            "entschieden - so die Nutzervorgabe. "
            "(5) ERST DANN SCHRITT 42 - die Aussagekraft je "
            "Stelle gegen ein Nullmodell. ⚠️ Reihenfolge: 44 ordnet, 42 "
            "misst. Ohne (1) bis (3) misst 42 auf einer Buchhaltung, die "
            "Bewertung und Betriebszustand vermengt. ⚠️⚠️ KEINE STELLE "
            "FAELLT hier weg (KEIN-BEITRAG-FAELLT) - sie werden sichtbar "
            "und messbar gemacht. "
            "✔✔✔ ERLEDIGT AM 13.09. - DIE BEIDEN RESTPUNKTE SIND ZU. "
            "(2.396-e2e) DER E2E-NACHWEIS IST ERBRACHT: er war an einer "
            "NB-Kopie gescheitert, deren Kursreihen nicht bis zum "
            "Simulationstag reichten. Gegen die PRODUKTIONSSICHERUNG vom "
            "12.09. 06:46 laeuft er durch - 17 Faelle, 17 gezeigt, 0 offen; "
            "ONDO wird ein echtes Hebelgeschaeft (3,7x), AKT faellt am "
            "Aggregat-Deckel auf Spot (2.427). ⚠️ ,Am Notebook wiederholen' "
            "war nicht noetig - die taegliche Sicherung im Austauschordner "
            "genuegt; ich hatte den Nachweis zu Unrecht fuer nur dort "
            "machbar erklaert (2.422-desktop). "
            "(2.391-hilfe) AUSGEZOGEN IN DEN L-BLOCK, nachdem die Zahlen "
            "reproduziert wurden: 56 NICHTS_TUN von 247 Verlusten der Stufe "
            "`aktion` (die uebrigen 191 sind deterministisch), 1.251 am "
            "Entscheider. ✔ Die zweite ihrer beiden Fragen ist beantwortet - "
            "der Widerlegungspreis BLEIBT, weil ohne ihn gar kein Hebel mehr "
            "entsteht (2.397); die Kennzeichnung an der Zahl ist Schritt 41. "
            "⚠️ Die erste - darf das Modell eine Empfehlung verhindern? - "
            "gehoert zu Schritt 33, denn dieser Schritt ist ausdruecklich "
            "AUFRAEUMEN und kein Umbau. "
            "➔ (4a) bleibt wie vorgesehen in Schritt 41, "
            "(2.407-namensschatten) ist am 12.09. mit `veto_art` geloest.",
            "Nutzerauftrag 12.09.; Befunde 2.393, 2.393-wirkung, 2.391-hilfe",
            fertig=True, block="D-BETRIEB",
            umbau="beides"),  # alte Trichterbuchhaltung ersetzt, Vier-Felder neu
    Schritt(48, "AUSSTIEG: DEFEKT UND ERFASSUNG - OHNE UMBAU",
            "✔ 48a ERLEDIGT AM 12.09. (Befund 2.402): die gestakte Position "
            "bekommt einen eigenen Mailabschnitt statt Schweigen; Paket "
            ",Gestakt' mit 15 Pruefungen, auf dem echten Weg gegengeprueft. "
            "✔ 48b ERLEDIGT AM 12.09. (Befunde 2.403*): "
            "`messe_ausstiegsguete.py` misst die Guete gegen die "
            "Tagesklammer, mit Zufallskontrolle ueber 200 Ziehungen; Paket "
            ",Ausstiegsguete' prueft das Werkzeug gegen bekannte Wahrheit "
            "(12 Pruefungen). ⚠️ ERGEBNIS: VERKAUFEN schlaegt den Zufall "
            "(H10 78,8 %% gegen 50,0 %%), REDUZIEREN nicht. ⚠️ WAS OFFEN "
            "BLEIBT und in Schritt 43 gehoert: der Kurs zum "
            "Empfehlungszeitpunkt wird bei Ausstiegen NICHT festgehalten "
            "(`rechnung=None` in `_sende_ausstieg`) - gerechnet wird mit dem "
            "Tagesschluss, und das ist die Untergrenze der Aufloesung (H3 "
            "liegt deshalb am Zufall). "
            "⚠️ AUS DER EXPERTENANTWORT (Befund 2.400-verkauf): der Nutzer "
            "hat recht, der UMBAU der Verkaufsseite gehoert hinter die "
            "stabilen Einstiege. Zwei Punkte sind aber kein Umbau. (1) DER "
            "DEFEKT: 105 Ausstiege sind als ,reines LLM-Halten' gebucht und "
            "haben den Nutzer NIE erreicht (2.392-stumm) - bis 11.09. Den "
            "Zweig finden und schliessen; eine Empfehlung, die niemand "
            "liest, ist ein Ausfall. (2) DIE ERFASSUNG: die Guete der 517 "
            "Ausstiege ist nicht messbar (409 auf `nicht_anwendbar`). Ein "
            "eigenes Erfolgsmass anlegen und MITSCHREIBEN - Potential nach "
            "der Empfehlung gegen ein Nullmodell (halten), keine "
            "Zielerreichung. ⚠️ NUR ERFASSEN, NICHTS BEWERTEN und nichts "
            "sperren. Bei 15-20 Faellen pro Tag sind das in vier Wochen rund "
            "500 auswertbare Faelle - wer erst mit dem Umbau anfaengt zu "
            "messen, beginnt ihn mit null Daten. "
            "✔✔✔ ERLEDIGT AM 13.09. - BEIDE PUNKTE. "
            "(1) DER DEFEKT IST GESCHLOSSEN, und zwar vollstaendig: von den "
            "105 stummen Ausstiegen betreffen 95 Werte, die VOLLSTAENDIG "
            "GESTAKT sind (HYPE 45, SOL 27, NEAR 7, SUI 7, AVAX 3, VSN 3, "
            "TAO 2, SEI 1) - sie bekommen seit 48a einen eigenen "
            "Mailabschnitt. Die uebrigen 10 stehen ALLE am 14.08. zwischen "
            "07:14 und 07:16, also vier Stunden VOR dem Fix von damals "
            "(Commit 153b2bd, 11:39). Zwischen dem 14.08. 07:16 und dem "
            "11.09. gibt es keinen unerklaerten Fall mehr (2.428). ⚠️ Der "
            "Befund hatte nur 25 der 105 belegt - die restlichen 80 waren "
            "eine plausible Annahme, keine Zaehlung. "
            "(2) DIE ERFASSUNG STEHT: `kurs_bei_empfehlung_eur` wird "
            "mitgeschrieben. Ein Einstieg hielt seine Lage in `entry_*` und "
            "`stop_loss_*` fest, ein Ausstieg GAR NICHTS - `_sende_ausstieg` "
            "reichte `rechnung=None` durch, obwohl `kurs_e` dort seit jeher "
            "vorliegt. Ohne ihn rechnet die Guetemessung mit dem "
            "Tagesschluss, und bei H3 liegt sie deshalb am Zufall (2.403). "
            "⚠️⚠️ NUR ERFASSEN: eine Pruefung haelt fest, dass der Wert in "
            "`entscheidungsrechnung`, `potential`, `wahrscheinlichkeit`, "
            "`rollen_gate` und `signal_mail` NICHT vorkommt (2.428-"
            "erfassung). ✔ Paket `Ausstiegserfassung`, 10 Pruefungen, mit "
            "zwei eingesetzten Defekten gegengeprueft. "
            "⚠️ DIE SUITE FING DABEI DIE KOPPLUNG zum zweiten Mal an einem "
            "Tag: eine neue `signals`-Spalte muss in `SPALTEN_SIGNAL`, in "
            "`models.Signal` UND im NB-Export stehen - ich hatte die dritte "
            "vergessen (2.428-kopplung). "
            "➔ WAS BLEIBT: der UMBAU der Verkaufsseite ist Schritt 43, so "
            "wie der Nutzer es wollte.",
            "Expertenempfehlung 12.09.; Befunde 2.392-stumm, 2.394",
            fertig=True, block="D-BETRIEB",
            umbau="beides"),  # alter Defekt geschlossen, Erfassung neu
    Schritt(38, "KETTE",
            "K-3 (Schwelle), dann K-2, K-4, K-5. ⚠️ HIER GEHOERT AUCH DER "
            "DRITTE BEITRAG HIN (Befund 2.409-kandidaten): DefiLlama-TVL ist "
            "kostenfrei, ohne Schluessel und die einzige ECHTE "
            "Onchain-Groesse der Recherche vom 12.09. - sie stammt NICHT "
            "wieder aus der Kursreihe, der Vorwurf der ,illusion of "
            "confirmation' trifft sie also nicht. ⚠️ Sie deckt nur "
            "DeFi-Protokolle ab und muss den VIERFACHTEST bestehen wie jeder "
            "andere. Ebenfalls hier: `schnitt` (heute nur Anzeige) und "
            "`oi_aenderung` (heute nur Sperre) brauchen keine Datenarbeit, "
            "sondern eine MESSUNG.",
            "Kettenplan 09.09.; NACH den Beitraegen wegen R-R9",
            block="D-BEWERTUNG",
            umbau="neu"),  # K-3 Schwelle und die Kettenpunkte des Umbaus


    Schritt(51, "DREI GEHALTENE WERTE OHNE MESSREIHE - UND DAS ALTER DER "
            "NICHT-KRYPTO-MESSBASEN",
            "\u26a0\u26a0 DIE DREI ROTEN ZEILEN DER SUITE (2.436), geklaert "
            "statt nur gezaehlt. Sie sind DATENSTAND, nicht Logik, und "
            "nicht heute entstanden - `git diff HEAD` zeigt an den "
            "betroffenen Pruefungen keine Aenderung. "
            "(1) ASTER (nur 318 USD-Tage) und MON (269) liegen unter der "
            "Mindestlaenge, CANTON hat auch in der PRODUKTION keine Reihe. "
            "Alle drei sind GEHALTEN - ohne Messreihe kann die Kette sie "
            "weder zum Nachkauf noch zum Verkauf bewerten. "
            "(2) CANTON ist zusaetzlich KERNWERT ohne jeden Beitrag; das "
            "ist dieselbe Ursache, nicht ein zweiter Fall. Bei Meme- und "
            "Smallcap-Werten waere es laut Nutzervorgabe unkritisch, bei "
            "einem Kernwert nicht. "
            "(3) Die Nicht-Krypto-Messbasen sind 10 Tage alt (Median "
            "2026-09-03; aktien 470/470, rohstoffe 35/35, themen_etf "
            "293/293 aelter als 7 Tage). \u26a0\ufe0f Am DESKTOP ist das zu "
            "erwarten - er faehrt nach stehender Vorgabe nie gegen die "
            "Produktiv-DB. \u27a4 ZU TUN: (1) und (2) brauchen eine "
            "Entscheidung zur Mindestlaenge oder eine Quelle fuer CANTON; "
            "(3) braucht eine Messung AM NOTEBOOK, bevor daraus ueberhaupt "
            "ein Befund wird - ob es dort auch rot ist, ist NICHT geprueft."
            "\u2714\u2714 STAND 13.09. ABENDS - ZWEI DER DREI ZEILEN WAREN FEHLER "
            "IN DER PRUEFUNG, NICHT IN DEN DATEN (2.441). \u26a0\ufe0f Und mein Text "
            "oben war an zwei Stellen falsch - beides, weil ich eine "
            "Pruefungsausgabe weitergeschrieben habe, statt sie an der Quelle "
            "gegenzupruefen. "
            "\u2716 FALSCH WAR: ,CANTON hat auch in der PRODUKTION keine "
            "Kursreihe'. Gelesen wird `data/tradinginfotool.db` am DESKTOP, und "
            "deren OHLC endet am 2026-08-19. In der Produktionssicherung vom "
            "12.09. hat CANTON 63 USD-Tage ab 2026-05-07, ASTER 342 (nicht 318) "
            "und MON 293 (nicht 269). \u27a4 ALLE DREI HABEN EINE REIHE - es ist "
            "derselbe Fall dreimal, zu kurz. \u2714 Die Pruefung nennt die Quelle "
            "jetzt beim Namen samt Stand. "
            "\u2716 FALSCH WAR AUCH: ,(3) braucht eine Messung AM NOTEBOOK'. Die "
            "Nicht-Krypto-Reihen kommen aus yfinance, das der Desktop selbst "
            "erreicht. Die Meldung war ein WAEHRUNGSFEHLER: "
            "`FRISCHE_GRENZE_TAGE = 7` traegt die Begruendung ,Krypto handelt "
            "durchgehend' und wurde auf Maerkte angewandt, die schliessen. Am "
            "So, 13.09. war die Median-Reihe vom Do, 03.09. - 10 KALENDERtage, "
            "aber 6 HANDELStage. \u2714 GEBAUT: fuer schliessende Maerkte wird in "
            "Handelstagen gezaehlt, die Grenze bleibt 7. Die Zeile ist GRUEN, "
            "regelkonform und nicht durch Lockerung. "
            "\u2714\u2714 DIE DRITTE ZEILE IST ECHT - loest sich aber grossteils von "
            "selbst (2.441-warten): keine Quelle macht eine junge Reihe laenger. "
            "ASTER erreicht die 400 Tage am 2026-11-09, MON am 2026-12-28, "
            "CANTON erst am 2027-08-15. Fuer zwei von dreien ist WARTEN die "
            "richtige Antwort. Fuer CANTON nicht - und CANTON ist zugleich der "
            "einzige KERNWERT der drei. "
            "\u26a0\u26a0 OFFEN UND NUTZERENTSCHEIDUNG (2.441-still): das eigentliche "
            "Problem ist nicht die Luecke, sondern ihre STILLE. `agent/` und "
            "`ui/` durchsucht - es gibt KEINE Mailzeile, keine GUI-Spalte und "
            "keinen Hinweis fuer ,gehalten, aber nicht bewertbar'. Die Kette ist "
            "zu diesen Werten stumm: kein Nachkauf, kein Verkauf, keine "
            "Begruendung. Genau das war der Ursprung des Pakets (Nutzerhinweis "
            "08.09.). \u26a0\ufe0f NICHT gebaut, und zwar absichtlich: eine neue "
            "Mailzeile gehoert in Schritt 41, dessen Vorgabe ,erst pruefen, DANN "
            "straffen' lautet. \u27a4 FRAGE: soll die Mail eine Zeile ,gehalten, "
            "nicht bewertbar (Grund)' fuehren - fuer alle drei oder nur fuer "
            "Kernwerte?"
            "✔✔✔ UND DIE MAILZEILE IST GEBAUT (2.442) - Nutzerentscheidung 13.09.: *,ja Mailzeile fuer alle drei'*. "
            "`verkaufsrechnung.stumme_bestaende()` liest `holdings` und meldet jede gehaltene Kryptoposition mit zu kurzer USD-Kursreihe im Abschnitt ,STUMM: GEHALTEN, ABER NICHT BEWERTBAR'; der Betreff "
            "nennt sie mit. ⚠️ Das Laufzeitkriterium ist bewusst ein anderes als in der Suite: das Notebook hat `messdaten.db` planmaessig nicht, also entscheidet die Kursreihenlaenge - mit "
            "DERSELBEN Grenze, importiert statt abgeschrieben. 13 Pruefungen, davon 10 Regeltests auf einer gestellten DB. "
            "⚠⚠ ES SIND VIER, NICHT DREI (2.442-vier, offen): gefiltert wird ueber EIGENSCHAFTEN, nicht ueber Namen - CANTON, VSN, MON, "
            "ASTER. VSN ist der vierte; ihn auszublenden waere dieselbe Stille, die hier behoben wird. Das gehoert dem Nutzer, nicht mir.",
            "Befund 2.436; pruefe_pakete.py --paket Neuaufnahme",
            block="D-BETRIEB",
            umbau="alt",
            fertig=True),  # Altbestand an Haltepositionen, keine Umbauleistung
    Schritt(52, "DIE STOPREGEL JENSEITS DER WEITE - DREI FRAGEN AUS "
            "SCHRITT 47",
            "\u2714 SCHRITT 47 HAT DIE WEITE GEKLAERT (2.435-optimum: "
            "inneres Maximum bei 7-9 %%, `stop_ziel_atr` = 2,5 trifft es) "
            "UND DEN DECKEL (2.437: 25 %% bleibt). Dabei sind DREI Fragen "
            "entstanden, die alle dieselbe Messanlage benutzen und deshalb "
            "zusammengehoeren. \u26a0\ufe0f KEINE davon rechtfertigt fuer sich "
            "einen Eingriff - sie sind Messfragen, keine Reparaturen. "
            "(1) DER ATR-RUECKFALL IM MITTELFELD (2.437-atr): bei Lagen mit "
            "ATR-Rueckfallstop 15-25 %% - das sind 47 %% aller Handelstage, "
            "und sie werden NICHT gedeckelt - waere ein engerer Stop LONG "
            "messbar besser (8 %%: +0,035, Band ueber null), SHORT dagegen "
            "flach. Eine Regel, die nur LONG hilft, braucht eine eigene "
            "Gegenpruefung. "
            "(2) MODELLSTOP GEGEN REGELSTOP (2.438): im Betrieb kommt der "
            "Stop in 81,5 %% der Faelle aus dem Widerlegungspreis, nicht aus "
            "der Regel. Der Median der 1.446 Modellzonen liegt mit 8,0 %% "
            "genau auf dem Gipfel - ob die EINZELentscheidung traegt, ist "
            "nicht gemessen. \u27a4 MESSBAR mit dem vorhandenen Werkzeug: je "
            "Signal den Modellstop gegen den Regelstop am SELBEN Anker, "
            "gepaart. "
            "(3) DER BP-SATZ (2.440-was-hilft): beim teuren Satz ist der "
            "gemessene Optimalstop wirtschaftlich der unguenstigste "
            "Bereich - Netto bei 8 %% -0,319 R, bei 20 %% -0,136 R. "
            "Aufweiten halbiert die Luecke (Quotenluecke 12 -> 5 Punkte), "
            "schliesst sie aber nicht; CRV anheben hilft NICHT (2.440-crv, "
            "gemessen). \u26a0\u26a0 EINE HANDELSPLATZABHAENGIGE STOPWEITE "
            "WAERE EINE GEBUEHR IN DER BEWERTUNG DURCH DIE HINTERTUER "
            "(Regel 2) - das ist eine Nutzerentscheidung, keine Messfolge. "
            "\u26a0\ufe0f WERKZEUG STEHT: `messe_stopweite_historisch.py` mit "
            "`atr_band`, `crv` und `stop_zuerst` als Parametern, "
            "`pruefe_stopweite_gegen.py` mit acht Proben. "
            "➤ (4) AUS SCHRITT 31 (2.447-offen, Punkt 2): der Trichter "
            "schreibt zum Stop ausserhalb der 5-Tage-Spanne ,GUENSTIG - wer ihn "
            "ausloest, hat ein Argument geliefert'. Die Spanne ist gemessen, "
            "der Halbsatz nicht - und `gesamtbild` zaehlt das Etikett. Dieselbe "
            "Messanlage beantwortet es: loesen Stops ausserhalb der Spanne "
            "seltener ohne Grund aus als solche innerhalb? "
            "\u27a4 (5) AUS DEM REVIEW 15.09.: 2.379-tage - wie lange bleibt ein Hebel "
            "sicher, bevor die Finanzierung die Liquidation an den Stop schiebt? "
            "Beim heutigen Kapital keine Handlung noetig (Median 79 Tage); ueber eine "
            "Tagesreserve beim Einstieg ist zu entscheiden, wenn das Kapital waechst.",
            "Befunde 2.437-atr, 2.438, 2.440-was-hilft, 2.379-tage; "
            "messe_stopweite_historisch.py",
            block="D-BEWERTUNG",
            umbau="neu"),  # die Stopregel ist der Nenner des neuen Hebels
    Schritt(53, "GUI UND ANWENDUNGSFAELLE - DIE GROSSE PLANUNG (E1)",
            "\u26a0\ufe0f\u26a0\ufe0f NUTZERVORGABE 07.09. (Gesamtplan 28.08., Punkt E1): "
            "die umfangreiche Planung mit GUI, Funktionalitaeten und "
            "Anwendungsfaellen - neue Assets, Assets fallen weg oder aendern "
            "sich. \u27a4 AUSGEGLIEDERT AUS SCHRITT 32 (14.09.): 32 hat die "
            "Oberflaeche an die LAUFENDE Kette angeglichen (2.448-umsetzung), "
            "diese Planung aber nicht begonnen. Stoff aus 2.448-rest: (1) die "
            "Anwendungsfaelle selbst; (2) Uebersichtsseite - ,Offene Signale' "
            "und ,Ausstiegsempfehlungen' ohne Kettentrennung; (3) ein Verlauf der "
            "Rollen-Hebelzeilen fehlt; (4) die Detailansicht nennt ihre Luecken "
            "(Trefferquote, Gebuehren, Marktvergleich, Termine) - schliessbar nur "
            "ueber den gespeicherten Mailtext, am 14.09. dagegen entschieden; "
            "(5) was mit den stillgelegten alten GUI-Wegen endgueltig geschieht."
            "➤ GEPRUEFT 14.09. (Befund 2.450): Ist-Aufnahme und Vorschlag in "
            "`Basisinfos/Plan_Asset_Lebenszyklus_14_09.md` - Luecken 2.450-cache "
            "(gepullte Watchlist wirkt erst nach Neustart), 2.450-neu (7 von 43 "
            "ohne Datengrundlage, nur im Log), 2.450-weg (kein Entfernen, "
            "entfernter Bestand verliert still die Fuehrung), 2.450-aendert "
            "(kein Bruchschutz). Vorschlag in drei Stufen A Betrieb / B "
            "Oberflaeche / C Messung - NUTZERENTSCHEIDUNG offen."
            "\u27a4 14.09.: A1 entschieden (Doku + Hinweis Neustart); Neuaufnahme-"
            "Ablauf abgestimmt (gehaltene automatisch, config.yaml, Daten "
            "automatisch, kein Einstieg ohne Messbasis). Positionsfaelle Spot/"
            "Hebel geprueft (2.451): 2.451-sofort, 2.451-absicherung (DBPK seit "
            "22.08. ohne Urteil), 2.451-verkauf, 2.451-bestaetigung, 2.451-phantom, "
            "2.451-topf, 2.451-hebel - am 14.09. ENTSCHIEDEN "
            "(Punkte 1-6, 7c, 7d; Umsetzung in Schritt 55). VSN wird aus der Stummzeile "
            "ausgenommen (Nutzerentscheidung zu 2.442-vier).",
            "Gesamtplan 28.08. E1; Befund 2.448-rest",
            block="D-ABBILDUNG",
            umbau="beides"),  # Planung, nicht Angleichung
    Schritt(58, "REGELWERK-DOKUMENTE: WELCHE REGEL GILT HEUTE, UND WO STEHT SIE?",
            "\u27a4 AUS DEM REVIEW 15.09. (Befund 2.455-regelwerk). Das Manual "
            "(fuer den Nutzer: jede Regel mit Wert und Begruendung) steht auf dem "
            "06.09., der Entscheidungslog auf dem 03.09. Seither entstandene Regeln "
            "stehen nur in Code, Befunden und Plan-Vorgaben - Paket B, Stopweite, "
            "Terminmarkt- und Kursfrische, Ampel. Die Register beantworten ,was "
            "wurde festgestellt', nicht ,welche Regel gilt mit welchem Wert'. "
            "\u27a4 NUTZERENTSCHEIDUNG 15.09.: WEG A - *,zentrale und wichtige Dokumentation duerfen nicht auseinanderlaufen, du benoetigst laufend die Informationen - sorge dafuer, dass du alles auffinden und nachvollziehen kannst'*. Umsetzungsschritte vor dem Bau vorlegen. Die zwei Wege waren: (A) ein Regelblatt, das "
            "aus dem Code ERZEUGT wird wie die Register - kann nicht veralten, "
            "braucht je Regel einen Eintrag mit Wert, Quelle und Befund; (B) Manual "
            "und Log formal stilllegen und die Frage einem bestehenden Register "
            "uebertragen. \u26a0\ufe0f Nicht: das Manual von Hand nachtragen - "
            "genau das ist dreimal veraltet (Landkarte 16.08.).",
            "Befund 2.455-regelwerk; Memory feedback_doku_struktur_zuordnung",
            block="D-ABBILDUNG",
            umbau="alt"),  # Dokumentation nachziehen, keine Umbauleistung
    Schritt(57, "ETF-BESTAND DER ROHSTOFFE - TRAEGT DIE INFORMATION?",
            "\u27a4 AUSGEGLIEDERT AUS SCHRITT 56 (15.09., Befund "
            "2.454-etfbestand-quelle). Die Reihe sollte Rolle G fuer Rohstoffe "
            "eine ZWEITE unabhaengige Quelle neben COT geben (G1) - physisch "
            "eingelagertes Metall als Nachfrage unabhaengig vom Kurs. Sie hat "
            "diese Groesse NIE geliefert: yfinance gibt einen ruhenden "
            "Stammdatenwert, fuer SLV und UNG seit 25.08. gar nichts. "
            "\u27a4 NUTZERENTSCHEIDUNG 15.09. - DAS ZIEL: nicht ,Rolle G eine "
            "zweite Quelle geben', sondern pruefen, ob ETF-Zu- und Abfluesse "
            "den weiteren Kursverlauf der Rohstoff-ETCs VORHERSAGEN. Nur dann "
            "ist eine fragile Emittentenquelle den Aufwand wert (Regel 4: ein "
            "Fakt ist keine Begruendung - auch nicht fuer eine Gegenpruefung). "
            "VIER TEILE, in dieser Reihenfolge: (1) DATENLAGE, nur recherchieren: "
            "gibt es kostenfreie Tages-Historie ueber mehrere Jahre fuer GLD, "
            "SLV, UNG und CPER? Stand 15.09. angetestet: iShares-SLV-Datei nennt "
            "Ounces und Shares Outstanding, eine Historie ist nicht bestaetigt; "
            "SPDR-Archiv liefert PDF; USCF hat eine Historienseite zu UNG, nicht "
            "ausgewertet. (2) MESSBARKEIT VORAB (Vorgabe "
            "MESSSTANDARD-VOR-DER-MESSUNG): 4 Werte erlauben keinen Querschnitt, "
            "die Laengsachse loest erst ab 0,08 R auf (Blocker A9). Ist die Frage "
            "schon vorher nicht aufloesbar, ist DAS das Ergebnis - dann erst die "
            "Loesungssuche, keine Messung ins Blaue. (3) MESSUNG nach "
            "Messstandard, Zeitfenster genannt. (4) ENTSCHEIDUNG: traegt die "
            "Groesse, die Emittentenquellen in EINEM Zug bauen (Abruf, Frische, "
            "Leser in `positionierung`, Satz fuer Rolle G - Vorgabe "
            "KEINE-TEILLOESUNG); traegt sie nicht, den Abruf mit Grund "
            "stilllegen und nachsehen, wer die Reihe sonst noch liest. "
            "\u26a0\ufe0f BIS DAHIN: der Abruf bleibt, er ist ohne Wirkung - "
            "`positionierung._etf_bestand` verlangt 90 Punkte und bildet nie "
            "einen Satz. \u26a0\ufe0f REIHENFOLGE: SPAETER, weil Rohstoffe "
            "Multiasset sind (Vorgaben KRYPTO-ZUERST, VERKAUF-VOR-MULTIASSET) "
            "und das Ergebnis in die Kriterien von Rolle G gehoert (Vorgabe "
            "LLM-SCHIENE-GANZ, Schritt 33).",
            "Nutzerentscheidung 15.09.; Befunde 2.454-etfbestand-quelle, 2.283 (A9)",
            block="SPAETER",
            umbau="alt"),  # eine Augustquelle klaeren: bauen oder stilllegen
)

# ---- Blocker, die benannt sind -------------------------------------------
BLOCKER = (
    ("A1", "Band auf BINAEREN Daten viermal zu eng (erwartet ±0,0023, "
           "beobachtet ±0,0006) - die Kontrolle traegt dadurch",
     "blockiert `barriere`, also jede Hebelmessung", "2.238"),
    ("A2", "✔ GELOEST 10.09. - ein PERMUTATIONSTEST (zirkulaerer "
           "Verschub) braucht keine Bloecke, weil er die "
           "Abhaengigkeitsstruktur erhaelt statt sie zu zerschneiden",
     "die Akkumulation ist messbar; `schnitt` traegt", "2.286"),
    ("A6", "`messe_volumenanteil` faehrt seine Negativkontrolle mit EINER "
           "Ziehung", "Befund N-13-1' steht unter Vorbehalt", "2.203"),
    ("A8", "Die Messnorm ist auf der LIVE-Menge nicht anwendbar - "
           "`pruefe_auswahl` misst unter der Tagesklammer, bei k=2 bleiben "
           "0 verwertbare Tage",
     "K-1a ist dort nicht entscheidbar", "2.273"),
    ("A9", "Die LAENGS-Achse loest bei beharrlichen Groessen erst ab "
           "0,08 R auf: 0,03 R -> 20 %, 0,05 R -> 50 %, 0,08 R -> 90 %. "
           "Die echten Kandidaten liegen bei 0,02 bis 0,05 R",
     "ein ,traegt nicht laengs' ist dort UNTERMACHT, kein Nullbefund",
     "2.283"),
)


# ============================================================================
# DAS IST - gelesen, nie getippt
# ============================================================================

def ist_beitraege() -> dict:
    """Was traegt LIVE, je (klasse, strategie)?"""
    aus = {}
    for b in W.BEITRAEGE:
        if b.zustand != "traegt":
            continue
        for kl in (b.klassen or ("*",)):
            for st in (b.strategien or ("*",)):
                aus.setdefault((kl, st), []).append(b)
    return aus


def ist_datenlage() -> list:
    """Symbole und Volumenabdeckung je Klasse - aus der Messdatenbank."""
    try:
        c = sqlite3.connect(DB, uri=True)
    except sqlite3.Error:
        return []
    try:
        q = ("SELECT assetklasse, COUNT(DISTINCT symbol), "
             "COUNT(DISTINCT CASE WHEN volume IS NOT NULL AND volume > 0 "
             "THEN symbol END) FROM price_history_ohlc GROUP BY assetklasse")
        return list(c.execute(q))
    except sqlite3.Error:
        return []
    finally:
        c.close()


def ist_kandidat(name: str):
    for k in BE.KANDIDATEN:
        if k.name == name:
            return k
    return None


# ============================================================================
# DER ABGLEICH
# ============================================================================

def datenstand() -> list:
    """Wie ALT sind die Datenbanken? - je Datei der juengste Zeitstempel.

    ## ⚠️⚠️⚠️ Warum das hier steht (10.09.2026)

    Am 10.09. habe ich Betriebszahlen aus `data/tradinginfotool.db`
    zitiert - Watchlist 43, 118 Signale, `strategie` nie gesetzt - und
    sie als heutigen Stand ausgegeben. **Die juengste Zeile dort ist vom
    19.08., die Signale enden am 21.07.** Die Produktion laeuft auf dem
    Notebook; ihre Daten liegen auf dem Desktop nicht vor.

    ⚠️ **Die Messbefunde sind davon NICHT betroffen** - sie stehen auf
    `data/messdaten.db`, und die ist aktuell. Betroffen ist alles, was
    ueber den BETRIEB gesagt wird.
    """
    aus = []
    for pfad, rolle in (("data/messdaten.db", "MESSUNGEN"),
                        ("data/tradinginfotool.db", "BETRIEB")):
        if not os.path.exists(pfad):
            aus.append((rolle, pfad, "fehlt", 0))
            continue
        try:
            c = sqlite3.connect("file:%s?mode=ro" % pfad, uri=True)
        except sqlite3.Error:
            aus.append((rolle, pfad, "nicht lesbar", 0))
            continue
        juengste, zeilen = "", 0
        try:
            for (t,) in c.execute("SELECT name FROM sqlite_master "
                                  "WHERE type='table'"):
                spalten = [x[1] for x in c.execute("PRAGMA table_info(%s)" % t)]
                try:
                    zeilen += c.execute("SELECT COUNT(*) FROM %s" % t).fetchone()[0]
                except sqlite3.Error:
                    continue
                for k in spalten:
                    if k not in ("created_at", "updated_at", "date", "tag",
                                 "datum", "zeitpunkt", "erstellt_am"):
                        continue
                    try:
                        v = c.execute("SELECT MAX(%s) FROM %s" % (k, t)).fetchone()[0]
                    except sqlite3.Error:
                        continue
                    if v and str(v) > juengste:
                        juengste = str(v)[:10]
        finally:
            c.close()
        aus.append((rolle, pfad, juengste or "kein Zeitstempel", zeilen))
    return aus


def umbaugrenze() -> dict:
    """VOR oder NACH dem Umbau? - fuer Code, Messungen UND Dokumente.

    ## ⚠️⚠️⚠️ Warum das getrennt gehoert (Nutzervorgabe 10.09.)

    > *„du musst sauber trennen nach vor und nach dem aktuellen Umbau -
    > das gilt fuer Messungen, Dokumente und Code!!!"*

    **Die Grenze ist der MESSSTANDARD**, gesetzt am 08./09.09.2026
    (`messnorm.MESSSTANDARD_AB`). Davor galten ein anderer Nullpunkt
    (Maximum ueber fuenf Ziehungen), eine andere Trennschaerfe (gegen
    null statt gegen den Nullpunkt) und eine kuerzere Leiter (bis 0,10
    statt 0,40).

    ⚠️ **Fuer CODE gibt es die Trennung schon** - `REGISTER_Werkzeuge`
    nach Methodikstand, per Scan erzeugt. Fuer MESSUNGEN und DOKUMENTE
    gab es sie nicht; hier wird sie ergaenzt.

    ⚠️ **Messungen** werden am Feld `Befundlage.basis` unterschieden: es
    wurde am 08.09. eingefuehrt, und ein leeres Feld heisst „Basis nicht
    vermerkt" - also nicht nachpruefbar, ob der Befund der Norm genuegt.

    ⚠️ **Dokumente** am Aenderungsdatum. Das ist ein grober Anhalt, kein
    Urteil: ein altes Dokument kann richtig sein. Es sagt nur, dass es
    den Umbau nicht gesehen hat.
    """
    aus = {"grenze": N.MESSSTANDARD_AB}
    try:
        stufen = BE.scanne_werkzeuge()
        aus["code"] = {k: len(v) for k, v in stufen.items()}
    except Exception:                                        # noqa: BLE001
        aus["code"] = {}
    mit = [b for b in BE.BEFUNDE if getattr(b, "basis", "")]
    aus["messungen"] = {"mit_basis": len(mit),
                        "ohne_basis": len(BE.BEFUNDE) - len(mit)}
    dok = []
    for pfad in sorted(glob.glob("Basisinfos/*.md")):
        # ⚠️⚠️ DER STANDKOPF SCHLAEGT DAS DATEIDATUM (11.09.2026).
        # `markiere_dokumente.py` setzt in jedes Vor-Umbau-Dokument eine
        # Zeile `<!-- STAND: JJJJ-MM-TT ... -->`. Das SETZEN hat das
        # Aenderungsdatum auf heute gezogen - ohne diese Abfrage wuerden
        # danach ALLE 48 als Nach-Umbau gelten, und die Trennung waere
        # durch den Versuch zerstoert, sie herzustellen.
        try:
            m = MD.stand(pfad)[0]
        except Exception:                                    # noqa: BLE001
            try:
                m = time.strftime("%Y-%m-%d",
                                  time.localtime(os.stat(pfad).st_mtime))
            except OSError:
                continue
        dok.append((m, os.path.basename(pfad)))
    aus["dokumente"] = dok
    return aus


def abgleich() -> list:
    """Gibt die Abweichungen zurueck - leer heisst: alles im Plan."""
    ab = []
    live = ist_beitraege()

    # 1 - Jede Lage: ist sie so vermessen, wie das SOLL es verlangt?
    for lg in LAGEN:
        hat = W.vermessen(lg.klasse, lg.strategie)
        if lg.blocker and hat and not lg.erbt_spot:
            # ⚠️⚠️⚠️ NICHT das SOLL nachziehen - das IST hat hier eine
            # LUECKE. `wahrscheinlichkeit.vermessen` nimmt (klasse,
            # strategie, richtung) und kennt KEINE Instrument-Achse. Die
            # Hebel-Lage bekommt deshalb automatisch die Spot-Beitraege.
            # Das ist der Befund vom 01.09. ("spot x einstieg und hebel x
            # einstieg liefern bei gleicher Lage exakt dieselbe Zahl,
            # +0,119100 R") - er laeuft unveraendert weiter.
            ab.append("%s x %s ist als BLOCKIERT gefuehrt, meldet aber %d "
                      "tragende Beitraege. URSACHE: `vermessen()` kennt "
                      "keine INSTRUMENT-Achse - die Lage erbt die "
                      "Spot-Beitraege (Befund 01.09.). Das SOLL ist "
                      "richtig, das IST hat die Luecke."
                      % (lg.instrument, lg.strategie, len(hat)))
        if not lg.blocker and not hat:
            ab.append("%s x %s SOLL vermessen sein, hat aber KEINEN "
                      "tragenden Beitrag" % (lg.instrument, lg.strategie))

    # 2 - Zielgroesse je Lage: kennt `messnorm` sie ueberhaupt?
    for lg in LAGEN:
        schluessel = (lg.instrument, lg.strategie)
        if schluessel not in N.ZIELGROESSE_JE_LAGE:
            ab.append("Fuer %s x %s ist in `messnorm.ZIELGROESSE_JE_LAGE` "
                      "keine Zielgroesse hinterlegt" % schluessel)

    # 3 - Jeder LIVE tragende Beitrag muss im Kandidatenregister stehen
    for (kl, st), bs in live.items():
        for b in bs:
            k = ist_kandidat((b.merkmal or "").replace("_fuenftel", ""))
            if k is None:
                ab.append("Beitrag `%s` traegt LIVE, steht aber nicht im "
                          "Kandidatenregister" % b.merkmal)

    # 4 - Die Hebelvorgabe: solange F-220 offen ist, MUSS die Lage
    #     blockiert gefuehrt sein - sonst geht die Vorgabe verloren.
    hebel = [lg for lg in LAGEN if lg.instrument == "hebel"]
    if not any(lg.blocker for lg in hebel):
        ab.append("⚠️⚠️ Die Hebel-Lagen sind ohne Blocker gefuehrt, obwohl "
                  "F-220 offen ist - genau der Fehler vom 05. und 10.09.")

    # 5 - Der Betriebsdatenstand: veraltete Zahlen duerfen nicht als
    #     aktuell durchgehen (Fehler vom 10.09.).
    for rolle, pfad, jung, _z in datenstand():
        if rolle == "BETRIEB" and jung < N.MESSSTANDARD_AB:
            ab.append("Die BETRIEBSdatenbank %s ist auf Stand %s - jede "
                      "Aussage ueber den laufenden Betrieb aus dieser "
                      "Quelle ist veraltet. Die Produktion laeuft am "
                      "Notebook." % (pfad, jung))

    # 6 - Nutzervorgabe: Core sind BTC, ETH UND SOL.
    #
    # ⚠️⚠️ DIESE PRUEFUNG LAS DAS FALSCHE GERAET (behoben 11.09.2026).
    # Sie oeffnete `data/tradinginfotool.db` - die DESKTOP-Kopie, die nie
    # produktiv ist und am 11.09. auf Stand 19.08. stand. Sie meldete
    # damit ueber ein Geraet, auf dem der Schalter gar nichts bewirkt.
    #
    # Am NOTEBOOK (Sicherung 11.09. 04:48) stand NUR BTC - nicht einmal
    # ETH. Die Desktop-Kopie hatte BTC+ETH und verdeckte die Haelfte des
    # Problems.
    #
    # ⚠️ Der Schalter EXISTIERT in der Oberflaeche ("Akkumulation
    # umschalten (Krypto)", Watchlist-Reiter). Er wirkt aber auf die DB
    # des Geraets, auf dem die GUI laeuft - L1 ist deshalb KEINE
    # Entwicklungsaufgabe, sondern ein Schritt der Rollout-Checkliste.
    for _pfad, _wo in (("data/tradinginfotool.db", "DESKTOP (nicht "
                        "produktiv - nur zur Anzeige)"),):
        # ⚠️⚠️ DIE PRUEFUNG LAS DIE TABELLE STATT DES SCHALTERS (11.09.2026,
        # Nutzerfund an der GUI). Hier stand `SELECT symbol FROM
        # asset_dca_settings WHERE dca_erlaubt=1`. `db.get_dca_erlaubt()`
        # liefert OHNE Zeile aber die Vorgabe {BTC, ETH, SOL} - und genau
        # darueber lesen GUI, `handelsauftrag.strategie_fuer` und
        # `assetklassen._schalter`. Am NB steht nur BTC als ZEILE; ETH und SOL
        # sind ueber die Vorgabe an, seit langem. Aus dieser Pruefung entstand
        # der falsche Planpunkt "ETH und SOL erst mit Paket 2 setzen"
        # (2.380-akku-schalter). Jetzt dieselbe Funktion wie der Betrieb.
        try:
            import database.db as _DBl
            c = sqlite3.connect("file:%s?mode=ro" % _pfad, uri=True)
            c.row_factory = sqlite3.Row
            gesetzt = {s for s in ("BTC", "ETH", "SOL")
                       if _DBl.get_dca_erlaubt(c, s)}
            c.close()
        except sqlite3.Error:
            continue
        fehlt = {"BTC", "ETH", "SOL"} - gesetzt
        if fehlt:
            ab.append("L1: die Akkumulation ist fuer %s AUS (`get_dca_erlaubt`, "
                      "samt Vorgabe) - die Nutzervorgabe nennt BTC, ETH und "
                      "SOL. ⚠️ GELESEN AUF: %s. Massgeblich ist das NOTEBOOK."
                      % (", ".join(sorted(fehlt)), _wo))

    # 7 - `swing` ist laut Nutzervorgabe keine genutzte Strategie mehr.
    #     ⚠️ Geprueft wird die STILLLEGUNG, nicht das Fehlen: der Eintrag
    #     bleibt stehen, damit die Betriebskette unangetastet ist (G-a).
    if not N.stillgelegt("hebel", "swing"):
        ab.append("L2: die Lage (hebel, swing) ist NICHT stillgelegt - "
                  "laut Nutzervorgabe 10.09. ist `swing` keine genutzte "
                  "Strategie mehr. Erwartet wird ein Eintrag in "
                  "`messnorm.LAGEN_STILLGELEGT`.")

    # 5 - Die Reihenfolge: hoechstens EIN Schritt darf offen und zugleich
    #     der naechste sein; spaetere duerfen nicht vorgezogen sein.
    offen = [s for s in REIHENFOLGE if not s.fertig]
    if offen:
        erster = offen[0]
        for s in REIHENFOLGE:
            if s.fertig and s.nr > erster.nr:
                ab.append("Schritt %d (%s) ist als fertig gefuehrt, obwohl "
                          "Schritt %d (%s) noch offen ist - die "
                          "Reihenfolge ist gebrochen"
                          % (s.nr, s.kennung, erster.nr, erster.kennung))
    return ab


def geordnet() -> tuple[list, list, list]:
    """Die offenen Schritte in der geltenden Ordnung: (alle, bereit, wartend).

    ⚠️⚠️ DIE EINZIGE STELLE, DIE DIE REIHENFOLGE KENNT. `main()` UND die
    Pruefung in `pruefe_pakete` rufen sie - vorher sortierte jede fuer
    sich, und als `wartet_auf` dazukam, meldete die eine 32 und die
    andere 28.

    ZWEI ACHSEN, und sie greifen in dieser Reihenfolge:

      1. BLOCK          die Reihenfolge von BLOECKE (Dringlichkeit)
      2. LISTENPOSITION innerhalb eines Blocks - NICHT die Nummer

    ⚠️ DIE SCHRITTNUMMER IST KEIN RANG. Sie sagt, WANN ein Schritt
    entstanden ist, nicht wie dringend er ist - Schritt 49 (ein Fehler im
    laufenden Betrieb) gehoert vor Schritt 44 (halb fertig), obwohl seine
    Nummer groesser ist.

    ⚠️⚠️ UND DANN FAELLT HERAUS, WER WARTET. Die Blockordnung sortiert
    nach Dringlichkeit und kannte keine Abhaengigkeit; deshalb meldete
    der Plan Schritt 28, dessen eigener Text sagt *"ERST NACH DEM ROLLOUT
    messen - vorher misst man den alten Stand"*. Das ist derselbe Fehler
    wie 2.395 (keine Rangfolge), eine Ebene tiefer.

    ⚠️ UMSORTIEREN HEISST ZEILEN VERSCHIEBEN. Das ist Absicht: eine
    zweite Zahl neben der Schrittnummer waere eine zweite Stelle, die
    gepflegt werden muss - und die erste, die vergessen wird.
    """
    _rang = {name: i for i, (name, _) in enumerate(BLOECKE)}
    _pos = {s.nr: i for i, s in enumerate(REIHENFOLGE)}
    offen = sorted((s for s in REIHENFOLGE if not s.fertig),
                   key=lambda s: (_rang.get(s.block, len(BLOECKE)),
                                  _pos[s.nr]))
    fertig_nr = {s.nr for s in REIHENFOLGE if s.fertig}
    wartend = [s for s in offen
               if any(n not in fertig_nr for n in s.wartet_auf)]
    bereit = [s for s in offen if s not in wartend]
    return offen, bereit, wartend


def main() -> int:
    kurz = "--kurz" in sys.argv
    ab = abgleich()
    # ⚠️ DIE BLOCKORDNUNG ENTSCHEIDET, NICHT DIE LISTENPOSITION (12.09.2026).
    # Vorher meldete diese Stelle "naechster Schritt 25", waehrend an 44
    # gearbeitet wurde - die Liste war die Reihenfolge ihrer Entstehung, nicht
    # die der Arbeit. Jetzt gilt die Reihenfolge der Bloecke (Befund 2.395).
    # ⚠️⚠️ ZWEI EBENEN, UND BEIDE SIND ABSICHT (12.09.2026, Nutzerauftrag
    # "Rangfolge innerhalb der Bloecke einfuehren"):
    #
    #   zwischen den Bloecken   die Reihenfolge von BLOECKE
    #   INNERHALB eines Blocks  die REIHENFOLGE DER LISTE, nicht die Nummer
    #
    # ⚠️ DIE SCHRITTNUMMER IST KEIN RANG. Sie sagt, WANN ein Schritt
    # entstanden ist, nicht wie dringend er ist - Schritt 49 (ein Fehler im
    # laufenden Betrieb) gehoert vor Schritt 44 (halb fertig), obwohl seine
    # Nummer groesser ist. Vorher sortierte diese Stelle nach `s.nr` und
    # meldete deshalb 44.
    #
    # ⚠️⚠️ UMSORTIEREN HEISST ZEILEN VERSCHIEBEN. Das ist Absicht: eine
    # zweite Zahl neben der Schrittnummer waere eine zweite Stelle, die
    # gepflegt werden muss - und die erste, die vergessen wird.
    offen, _bereit, _wartend = geordnet()
    _fertig_nr = {s.nr for s in REIHENFOLGE if s.fertig}

    print("=" * 100)
    print("SOLL / IST — steht der Umbau noch im Plan?")
    print("=" * 100)

    if not kurz:
        print()
        print("  DIE VORGABEN, DIE UEBER ALLEM STEHEN")
        for v in VORGABEN:
            zeichen = {"erfuellt": "✔", "zurueckgestellt": "○"}.get(
                v.stand, "⚠️")
            print("   %s %-16s %s" % (zeichen, v.kennung, v.text))
            print("     %-16s Quelle: %s" % ("", v.quelle))
        print()

        print("  DIE LAGEN — SOLL gegen IST")
        print("   %-12s %-14s %-9s %s"
              % ("Instrument", "Strategie", "Beitraege", "Stand"))
        for lg in LAGEN:
            hat = W.vermessen(lg.klasse, lg.strategie)
            stand = ("BLOCKIERT: " + lg.blocker) if lg.blocker else lg.soll
            print("   %-12s %-14s %-9d %s"
                  % (lg.instrument, lg.strategie, len(hat), stand[:58]))
            if lg.blocker and len(stand) > 58:
                print("   %-12s %-14s %-9s %s" % ("", "", "", stand[58:]))
        print()

        print("  ⚠️⚠️ DER DATENSTAND — welche Datenbank ist wie alt?")
        print("   %-10s %-30s %-14s %10s"
              % ("Rolle", "Datei", "juengste Zeile", "Zeilen"))
        for rolle, pfad, jung, zeilen in datenstand():
            mark = ""
            if rolle == "BETRIEB" and jung < N.MESSSTANDARD_AB:
                mark = "  ⚠️ VERALTET - Produktion laeuft am Notebook"
            print("   %-10s %-30s %-14s %10d%s"
                  % (rolle, pfad, jung, zeilen, mark))
        print()
        print("  DIE DATENLAGE — gelesen aus der Messdatenbank")
        print("   %-14s %9s %14s" % ("Klasse", "Symbole", "mit Volumen"))
        for kl, n, mv in ist_datenlage():
            print("   %-14s %9d %14d" % (kl, n, mv))
        print("   %s" % messmenge.zeile())
        print()

        u = umbaugrenze()
        print("  ⚠️⚠️ VOR / NACH DEM UMBAU — Grenze ist der Messstandard "
              "vom %s" % u["grenze"])
        if u["code"]:
            print("   CODE (Methodikstand, aus REGISTER_Werkzeuge):")
            for stufe, _t in BE.STUFEN:
                n = u["code"].get(stufe, 0)
                mark = "  ⚠️ nur mit Vorbehalt" if stufe == "ALTBESTAND" else ""
                print("      %-14s %4d%s" % (stufe, n, mark))
        m = u["messungen"]
        print("   MESSUNGEN (Befunde):")
        print("      %-14s %4d   Basis vermerkt, nachpruefbar"
              % ("nach Umbau", m["mit_basis"]))
        print("      %-14s %4d   ⚠️ Basis NICHT vermerkt - nicht "
              "nachpruefbar" % ("vorher", m["ohne_basis"]))
        vor = [d for d in u["dokumente"] if d[0] < u["grenze"]]
        nach = [d for d in u["dokumente"] if d[0] >= u["grenze"]]
        print("   DOKUMENTE:")
        print("      %-14s %4d" % ("nach Umbau", len(nach)))
        print("      %-14s %4d   ⚠️ haben den Umbau nicht gesehen"
              % ("vorher", len(vor)))
        print("      die groessten davon:")
        for d, n_ in sorted(
                vor, key=lambda x: -os.stat("Basisinfos/" + x[1]).st_size)[:5]:
            print("        %s  %-46s %8d Bytes"
                  % (d, n_, os.stat("Basisinfos/" + n_).st_size))
        print()
        print("  DIE BENANNTEN BLOCKER")
        for k, was, folge, q in BLOCKER:
            print("   ⚠️ %-6s %s" % (k, was))
            print("      %-6s -> %s   (%s)" % ("", folge, q))
        print()

    # ⚠️ NACH BLOECKEN, NICHT ALS LISTE (12.09.2026, Befund 2.395). Eine
    # Liste von zwanzig offenen Schritten ohne Rangfolge sagt nicht, was als
    # naechstes dran ist - sie sagt nur, dass viel offen ist.
    print("  DIE VEREINBARTE REIHENFOLGE — nach Bloecken")
    fertige = [s for s in REIHENFOLGE if s.fertig]
    print("   ✔ ERLEDIGT: %d Schritte (%s)"
          % (len(fertige), ", ".join(str(s.nr) for s in fertige)))
    print()
    for name, warum in BLOECKE:
        if name == "ERLEDIGT":
            continue
        drin = [s for s in REIHENFOLGE if s.block == name and not s.fertig]
        if not drin:
            continue
        print("   %-14s %s" % (name, warum))
        # ⚠️⚠️ ALT ODER NEU STEHT AN JEDEM SCHRITT (13.09.2026,
        # Nutzervorgabe *"Der PLAN muss klar zwischen altem und neuem Umbau
        # unterscheiden"*). Ohne das Zeichen liest sich eine Reparatur wie
        # ein Baufortschritt - genau die Vermischung, die der Nutzer
        # bemaengelt hat.
        _je = {}
        for s in drin:
            _je[s.umbau or "?"] = _je.get(s.umbau or "?", 0) + 1
        print("   %-14s %s" % ("", "davon " + " · ".join(
            "%d %s" % (n, UMBAUZEICHEN.get(k, k))
            for k, n in sorted(_je.items(), key=lambda x: -x[1]))))
        for _r, s in enumerate(drin, 1):
            z = "→" if offen and s is offen[0] else " "
            # DER RANG STEHT DA, sonst haelt ihn jemand fuer die Nummer.
            print("     %s %d. [%s] Schritt %-3d %-14s %s"
                  % (z, _r, UMBAUZEICHEN.get(s.umbau, "?  "), s.nr,
                     s.kennung, s.text[:44]))
            if not kurz:
                print("           %-12s Quelle: %s" % ("", s.quelle))
        print()
    # ⚠️ WER KEINEN BLOCK HAT, FAELLT AUF - sonst sammelt sich wieder eine Halde.
    lose = [s for s in REIHENFOLGE if not s.block and not s.fertig]
    if lose:
        print("   ⚠️⚠️ NICHT EINGEORDNET (%d) - gehoert in einen Block:" % len(lose))
        for s in lose:
            print("      %d %-14s %s" % (s.nr, s.kennung, s.text[:58]))
        print()

    print("=" * 100)
    if ab:
        print("⚠️⚠️ %d ABWEICHUNG(EN) ZWISCHEN SOLL UND IST" % len(ab))
        for x in ab:
            print("   ⚠️ %s" % x)
    else:
        print("✔ KEINE ABWEICHUNG — das laufende System entspricht den "
              "Entscheidungen.")
    print()
    if _wartend:
        print("   ⏸ WARTET AUF EINEN ANDEREN SCHRITT — nicht als naechster "
              "gemeldet:")
        for s in _wartend:
            _offen_auf = [n for n in s.wartet_auf if n not in _fertig_nr]
            print("      Schritt %-3d %-38s wartet auf %s"
                  % (s.nr, s.kennung[:38],
                     ", ".join(str(n) for n in _offen_auf)))
        print()
    if _bereit:
        print("   NAECHSTER SCHRITT: %d %s — %s"
              % (_bereit[0].nr, _bereit[0].kennung, _bereit[0].text))
        print("   Quelle: %s" % _bereit[0].quelle)
    elif offen:
        # ⚠️ ALLES OFFENE WARTET - das ist KEIN "fertig", sondern eine
        # Blockade, und sie gehoert benannt statt verschwiegen.
        print("   ⚠️⚠️ KEIN SCHRITT IST BEREIT — alle %d offenen warten "
              "auf einen anderen. Das ist eine Blockade, kein Abschluss."
              % len(offen))
    else:
        print("   Alle Schritte der Reihenfolge sind abgearbeitet.")
    return 1 if ab else 0


if __name__ == "__main__":
    sys.exit(main())
