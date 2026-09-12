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
    """Ein Schritt der vereinbarten Reihenfolge."""
    nr: int
    kennung: str
    text: str
    quelle: str
    fertig: bool = False
    hinweis: str = ""


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
    Vorgabe("KRYPTO-ZUERST",
            "Multiasset (Aktien, ETF, Rohstoffe, Hedge) ist NACHGELAGERT - "
            "erst nach dem Krypto-Produktivgang. A-1, A-2 und die "
            "N-19-Messbasis sind zurueckgestellt.",
            "Nutzervorgabe 10.09.", "erfuellt"),
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
                 "danach: A9 - die AUFLOESUNG: die Abstufung springt 1,02x -> 3,90x, "
                 "weil die Beitraege Fuenftel sind (2.174-grenzen); "
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
REIHENFOLGE = (
    Schritt(1, "N-46a",
            "Zirkulaerer Verschub als Laengs-Nullpunkt GEBAUT - P1/P2/P3 "
            "sauber (gepflanzt 0,20 R -> +0,0420 gefunden).",
            "n98_n46_laengs_nullpunkt.py; Befund 2.275",
            fertig=True),
    Schritt(2, "N-46b",
            "✔ ENTSCHIEDEN: die TAGESMISCHUNG gewinnt - Fehlalarm 1,0/"
            "4,0 % gegen Soll 2,5 %, Fundquote auf 6 von 8 Sprossen "
            "besser. N-46 ist mit dem VORHANDENEN Werkzeug geloest.",
            "Befund 2.282 / 2.282-fund", fertig=True),
    Schritt(3, "A2/AKKU",
            "✔ GELOEST: Permutationstest statt Bootstrap-Band. `schnitt` "
            "traegt (+0,0470, 481 Symbole, p 0,000) - der erste gemessene "
            "Beitrag fuer die Akkumulationslage.",
            "Befund 2.286 / 2.286-schnitt", fertig=True),
    Schritt(4, "VIERFACHTEST",
            "⚠️ GEMESSEN, ABER NICHT ERFUELLBAR: Kriterium 4 liefert bei "
            "ALLEN Kandidaten untermaechtig - auch bei der Kontrolle. Es "
            "ist falsch konstruiert (Signifikanztest statt "
            "Streuungszerlegung, Methodik 2.101).",
            "Befund 2.292 / 2.292-fehlkonstruktion", fertig=True),
    Schritt(5, "V1 KRITERIUM 4",
            "✔ ERLEDIGT: Kriterium 4 ist ERFUELLBAR. Die meisten "
            "Kandidaten bestehen es ROH - `schnitt` mit 25,4 %. ⚠️ Der "
            "Befund trifft den BESTAND: `turnover` ist zu 51,2 % eine "
            "Asset-Eigenschaft.",
            "Befund 2.297 / 2.298", fertig=True),
    Schritt(6, "V7 KRITERIUM 3",
            "⚠️ GEMESSEN: nur EIN gedecktes Urteil - `turnover` ist "
            "unabhaengig von `funding` (2 gegen 0 Faecher). Fuer die "
            "KANDIDATEN nicht entscheidbar: die Schichtung kostet die "
            "Macht.",
            "Befund 2.302 / 2.303", fertig=True),
    Schritt(7, "V8 ZWEI SCHICHTEN",
            "⚠️ WIDERLEGT: mit zwei Faechern ist KEIN Urteil gedeckt - "
            "mit fuenf war es eines. Nicht die Macht war der Engpass, "
            "sondern die ZAEHLMETRIK. ✔ Die Vorfrage ist geloest (auf "
            "20 % tragen alle drei Kandidaten).",
            "Befund 2.308", fertig=True),
    Schritt(8, "V2 N-73 AUF DEN BESTAND",
            "✔ GEMESSEN: `funding` besteht N-73 NICHT (2 von 3). "
            "`schnitt` besteht sie BESSER als jeder registrierte "
            "Beitrag - die Zweierlei-Mass-Sorge ist umgekehrt "
            "beantwortet.",
            "Befund 2.312 / 2.312-antwort", fertig=True),
    Schritt(9, "V9 GESCHICHTET ALS EIN BEFUND",
            "✔ ERLEDIGT: Kriterium 3 ist beantwortet - `funding` erklaert "
            "bei KEINEM Kandidaten etwas. ⚠️ Der Zusatz ,`schnitt` hat "
            "damit ALLE VIER Kriterien' (2.319) ist am 10.09. ABGELOEST "
            "durch 2.325 - er hat DREI.",
            "Befund 2.316 · 2.319 abgeloest durch 2.325", fertig=True),
    Schritt(10, "S-7 GEKLAERT",
            "✔ ERLEDIGT: S-7 dreifach reproduziert und nur in seinem "
            "eigenen Wortlaut bestaetigt (,unentschieden'). ⚠️⚠️ DABEI "
            "fiel KRITERIUM 2 auf: `n102:135` gab ,Band haelt die Null' "
            "als ✔ aus - je breiter das Band, desto sicherer. Richtig "
            "gemessen FAELLT `schnitt` daran.",
            "Befunde 2.321 bis 2.330", fertig=True),
    Schritt(11, "V11 SCHNITT50",
            "⚠️⚠️ ERLEDIGT, ABER NEGATIV: `schnitt50` besteht N-73 NICHT "
            "(2 von 3; Kriterium 1 mit 100 %% erfuellt). ⚠️⚠️⚠️ Und der "
            "AUSWAHL-TEST hat die Zuschreibung aus 2.325 gekippt: "
            "`schnitt`s Instabilitaet gehoert der AUSWAHL, nicht ihm - "
            "Faktor 6 bei VIERMAL schaerferem Test. BILANZ: es gibt "
            "KEINEN dritten Beitrag.",
            "Befunde 2.331 bis 2.339", fertig=True),
    Schritt(12, "S-1 SAMMLUNG ABSICHERN",
            "✔ ERLEDIGT 11.09.: die drei Messquellen sind in "
            "`datenfrische` registriert (Rolle M), und ein Ausfall wird "
            "GEMELDET statt nur geloggt - nach JOB gruppiert, mit "
            "Handlungsanweisung. ⚠️ Offen: sie haben weiter keinen Job "
            "und keine `fetched_at`-Spalte; der Abrufstand kommt aus der "
            "Dateizeit.",
            "Befunde 2.358/2.359", fertig=True),
    Schritt(13, "S-2 STILLER AUSFALL",
            "✔ ERLEDIGT 11.09.: ein Ausfall ist keine Messbasisluecke "
            "mehr. Teilausfall wird genannt statt weggelassen, "
            "Totalausfall nennt den AUSFALL statt der falschen Ursache. "
            "Vier Faelle, fuenf Dauerpruefungen.",
            "Befunde 2.357", fertig=True),
    Schritt(14, "S-3 JOBSPUR",
            "✔ ERLEDIGT 11.09.: jeder Job hinterlaesst eine Spur - der "
            "Ereignis-Horcher lauscht jetzt auch auf EVENT_JOB_EXECUTED. "
            "Vorher fuehrten nur 6 von 21 eine Zeile in `job_laeufe`, und "
            "nach einem Ausfall war nicht feststellbar, was gefehlt hat. "
            "Zentral statt fuenfzehn Kopien.",
            "Befunde 2.360", fertig=True),
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
            "Befunde 2.362 bis 2.373", fertig=True),
    Schritt(16, "AKKU-SPERRE",
            "✔ ERLEDIGT 11.09.: Sicherheitsnetz - die Akkumulation ist ohne "
            "gemessenen Beitrag GESPERRT statt durchgewunken "
            "(`Potential.lage_gesperrt`, geprueft VOR der Notiz ,nicht "
            "vermessen'). Bis dahin entschied ueber einen Nachkauf allein "
            "das Sprachmodell (2.370). Einstieg unberuehrt.",
            "Nutzerentscheidung 11.09. (Paket B); Befund 2.374-akku",
            fertig=True),
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
            fertig=True),
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
            fertig=True),
    Schritt(19, "H-3 HEBELVERTEILUNG",
            "✔ ERLEDIGT 11.09.: `simuliere_hebelverteilung.py` ueber "
            "633.672 echte Anker, Betriebsfall mit Widerlegungspreis. Bei "
            "18.213 EUR: Spot 56 %, Hebel 44 % (Grenze 5x 5 %), "
            "Liquidation nie; stark kapitalabhaengig (12 % bei 9.942, 80 % "
            "bei 30.000). Watchlist 2026: Hebel 58 %, Grenze 5x 10 %, Stop Median 13,7 %. Gegenpruefung G1-G6 "
            "bestanden; Stopregel an 1.289 NB-Einstiegen gegengeprueft. "
            "EMPFEHLUNG: Schalter mit dem Rollout (nach H-4, H-5, E2E).",
            "Befunde 2.378*",
            fertig=True),
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
            fertig=True),
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
            fertig=True),
    Schritt(22, "S-4 SPOT SAUBER",
            "✔ ERLEDIGT 11.09.: (a) der Hebelschalter aendert den Spot-Betrag "
            "nicht - 1.436 NB-Einstiege, Betrag ueberall gleich; 33 % verlieren "
            "nur ihren Scheinhebel 1,2x (2.381-spot). (b) die Mail nach dem "
            "Vorschlag gegliedert, nichts gestrichen, die zweite Trefferquote "
            "im Anhang (2.381-mail). (c) O1 behoben: 12 h wirken wieder, der "
            "kurze Takt erst ab 2x (2.381). Feinschliff der Mail (Kursmarken "
            "und Rangangaben zusammenlegen) NACH dem Rollout.",
            "Befunde 2.381*",
            fertig=True),
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
            fertig=True),
    Schritt(24, "ROLLOUT PAKET B",
            "Gesamtpaket auf das Notebook (stehende Regel). Checkliste "
            "`Basisinfos/Ausrollen_24_08.md` vorher aktualisieren: "
            "Pruefungszahl, `config.yaml` am Notebook VOR dem Pull "
            "abgleichen, S-1 erkennt die Symbolliste (2.368), "
            "Portfoliowert 02.09. bis Rollout einmal nachrechnen "
            "(2.376-rollout). ⚠️ Der "
            "Akkumulationsschalter steht fuer BTC, ETH und SOL seit langem "
            "an (Vorgabe von `get_dca_erlaubt`, 2.380-akku-schalter) und "
            "wirkt bis Paket 2 nicht (Sperre). ✔ Fenster 24 h, Position "
            "ohne Stop Variante B mit Liquidationsregel (2.382-liquidation); "
            "die Topfregel bleibt bis nach dem Rollout (2.382-topf). ✔ "
            "VORBEREITET: `ausrollen_paket_b.py` (2.383), am NB mit "
            "`--nachrechnen` vor dem Neustart; Ablauf in "
            "`Basisinfos/Ausrollen_24_08.md`, Abschnitt PAKET B. ⚠️ Der Hebel-Schalter je Asset ist opt-in - am NB "
            "23 von 43 Kryptowerten an; nur dort entsteht ein Hebelgeschaeft. "
            "Nach dem Nachrechnen des Portfoliowerts den E2E "
            "(`--nachweis-paket-b`) gegen die frische Sicherung wiederholen. "
            "OFFEN: alter Marktscan "
            "weiter aktiv? ✔ ENTSCHIEDEN 12.09.: der Marktscan bleibt AN - "
            "er ist die einzige Entdeckung ausserhalb der Watchlist und "
            "kostet keine Modellaufrufe (2.385); der Ersatz wird gemessen, "
            "bevor er ihn ersetzt (Schritt 39). Das ALTE Hebel-Screening ist "
            "AUS, der Hebel aus der Quote ist AN (2.384). "
            "Prompt-Stand 2026-09-11a (2.379-liq).",
            "Basisinfos/Ausrollen_24_08.md; Nutzerentscheidung 11.09."),

    # ================================================================
    # PAKET 2 - DIE AKKUMULATION (Messen vor Bauen)
    # ================================================================
    Schritt(25, "AKKU-MESSPAKET",
            "(1) 2.286/2.287 reproduzieren (R-R11); (2) Zeitstabilitaet je "
            "Kandidat fuer H90 - Permutationstest je Haelfte, `n68` ist "
            "blockbasiert und passt dort nicht; (3) Ueberschneidung der "
            "drei: `schnitt` +0,0470, `funding` UMGEKEHRT -0,0230, "
            "`oi_aenderung` UMGEKEHRT -0,0178; (4) Stufen. Faellt ein "
            "Kandidat: Loesung suchen (KEIN-BEITRAG-FAELLT) - die Sperre "
            "bleibt so lange.",
            "Befunde 2.286 bis 2.290; Nutzerentscheidung 11.09."),
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
            "vormals Schritt FORM; Befunde 2.286-schnitt, 2.374"),
    Schritt(27, "ROLLOUT PAKET 2",
            "Akkumulation aufs Notebook. Der Schalter steht fuer BTC, ETH "
            "und SOL schon an (2.380-akku-schalter) - mit der Registrierung "
            "faellt die Sperre.",
            "Nutzerentscheidung 11.09."),

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
            "Nutzervorgabe 11.09.; Befund 2.382-topf"),

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
            "Nutzervorschlag 11.09."),
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
            "agent/krypto/backtesting.py"),

    Schritt(31, "EMAIL STRUKTUR UND INHALTE",
            "⚠️ NUTZERVORGABE 11.09.: Struktur und Inhalte straffen. "
            "Regel 1 war schon erfuellt (2.356); offen sind Regel 2 "
            "(gleichlautende Luecken zu EINEM Satz, gezaehlt nach GRUND) "
            "und Regel 3 (Anhang statt Weglassen). ⚠️ Vorbehalt aus dem "
            "Vorschlag: die Mail ist lang, WEIL die Bewertung duenn ist - "
            "nach Schritt 21 schrumpft der Lueckenblock von selbst.",
            "Gesamtplan 11.09. - Mail-Vorschlag"),
    Schritt(32, "GUI UND UEBERSICHTSSEITE",
            "⚠️ Offen seit 07.09., nie begonnen (E1). ⚠️ Die "
            "Uebersichtsseite EXISTIERT (`remote/status.py`, rund 40 "
            "Aggregatoren) - hier geht es um Erweiterung, nicht Neubau. "
            "Die Bewertungsschwelle steht seit dem 11.09. darin (35 "
            "Parameter); in der GUI fehlt sie noch.",
            "remote/status.py; Nutzervorgabe 07.09. und 11.09."),
    Schritt(33, "LLM-ROLLEN UND MODELLE",
            "⚠️ NUTZERVORGABE 11.09.: Bewertung und Analyse der Rollen "
            "und Modelle - NACH den eMails. Stehende Vorgaben, die hier "
            "gelten: nur kostenfreie LLMs · das LLM muss den Zufall "
            "schlagen und messbar sein · kein deterministischer Override "
            "des LLM-Werturteils.",
            "Nutzervorgabe 11.09."),

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
            "NB-Sicherung 11.09.; agent/krypto/regime.py"),
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
            "dem Messstandard.",
            "Befunde 2.238 / 2.238-klasse / 2.169 / REGISTER_Kandidaten"),
    Schritt(36, "V12 VOLA UND SCHNITT",
            "⚠️ HYPOTHESE, nicht gemessen: beide fallen an Kriterium 2 "
            "mit fast derselben Zahl (+0,2039 gegen +0,1973). "
            "Gemeinsamer geometrischer Anteil? Stuetzt 2.293. "
            "⚠️ Niedrige Dringlichkeit - klaert nur, WARUM zwei "
            "Kandidaten fielen, die ohnehin gefallen sind.",
            "Befund 2.327 - offen"),
    Schritt(37, "KALIBRIERUNG",
            "Kalibrierung neu, dann die Hebelhoehe rechnen: erreicht sie "
            "2-5x? ⚠️ Der Engpass ist die AUFLOESUNG, nicht die Staerke - "
            "die Abstufung springt 1,02x -> 3,90x, weil die Beitraege "
            "Fuenftel sind (2.174-grenzen).",
            "Plan 05.09."),
    Schritt(39, "P-SCAN - ENTDECKUNG AUS DEM POTENTIAL",
            "⚠️ ERSATZ FUER DEN ALTEN MARKTSCAN, in drei Stufen (2.385-pscan): "
            "(1) SCHATTEN - denselben gemessenen Rang wie in der Kette taeglich "
            "fuer ALLE Werte mitschreiben, fuer die die Messbasis reicht (heute "
            "42, davon 35 ausserhalb der Watchlist); (2) MESSEN - traegt ein "
            "hoher Rang ausserhalb der Watchlist mehr Potential (`bewegung_r`, "
            "nicht Zielerreichung)? Ohne Nachweis keine Empfehlung; (3) erst "
            "dann eine Aufnahme-Liste, gefiltert auf bei Bitpanda handelbare "
            "Werte. ⚠️ Der Engpass ist die Onchain-Basis (66 Symbole) - sie zu "
            "verbreitern ist der eigentliche Bauteil. Bis dahin bleibt der "
            "alte Marktscan an.",
            "Nutzerauftrag 12.09.; Befunde 2.385, 2.385-pscan"),
    Schritt(38, "KETTE",
            "K-3 (Schwelle), dann K-2, K-4, K-5.",
            "Kettenplan 09.09.; NACH den Beitraegen wegen R-R9"),


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


def main() -> int:
    kurz = "--kurz" in sys.argv
    ab = abgleich()
    offen = [s for s in REIHENFOLGE if not s.fertig]

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

    print("  DIE VEREINBARTE REIHENFOLGE")
    for s in REIHENFOLGE:
        z = "✔" if s.fertig else ("→" if offen and s is offen[0] else " ")
        print("   %s %d %-14s %s" % (z, s.nr, s.kennung, s.text[:66]))
        if not kurz:
            print("       %-14s Quelle: %s" % ("", s.quelle))
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
    if offen:
        print("   NAECHSTER SCHRITT: %d %s — %s"
              % (offen[0].nr, offen[0].kennung, offen[0].text))
        print("   Quelle: %s" % offen[0].quelle)
    else:
        print("   Alle Schritte der Reihenfolge sind abgearbeitet.")
    return 1 if ab else 0


if __name__ == "__main__":
    sys.exit(main())
