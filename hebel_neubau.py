# -*- coding: utf-8 -*-
"""Der HEBEL-NEUBAU - Rollen, Kandidaten und der RIEGEL gegen SPOT.

**27.09.2026.** Nutzervorgabe woertlich: *"WIR sind bei einem NEUBAU des
Hebels, die alten Beitraege sind nicht relevant. NUR HEBEL UMBAU. Die
EINZIGE Gemeinsamkeit ist der Pruefzeitpunkt von SPOT und HEBEL und die
gleichzeitige Bewertung. Der SPOT-Teil kommt spaeter, wenn Hebel
funktioniert - trenne ALT von NEU, sonst killt uns der Umbau."*

Und davor, am 25.09.: *"wir bauen den Hebel-Arm vollstaendig neu. Wenn
Hebel funktioniert, dann gehen wir zu den anderen Strategien."*

═══════════════════════════════════════════════════════════════════════
 ⚠️⚠️⚠️ WOZU DIESES MODUL DA IST
═══════════════════════════════════════════════════════════════════════

Ich bin am 26. und 27.09. **dreimal** in den Spot-Arm zurueckgerutscht:

    1. `funding_fuenftel` und `turnover_fuenftel` als "unsere Beitraege"
       behandelt - sie tragen `instrumente=("spot",)` und sind auf H20
       und `bewegung_r` gemessen, also auf der SPOT-Lage
    2. die Kelly-Nullstelle aus `betraege.hebelrechnung` als
       Bewertungsschwelle benutzt - dieselbe Formel, die der Spot-Arm
       fuer seine Quote verwendet
    3. `ema_abstand_atr` als EINSTIEGSSIGNAL vermessen, obwohl es im
       Neubauplan ausdruecklich die RISIKOSPERRE ist (Rolle C)

⚠️ Ein Hinweis in der Doku hat das nicht verhindert. Deshalb steht der
Riegel hier IM CODE: wer eine Hebel-Neubaumessung baut, importiert
`pruefe_quellen()` und bekommt einen ABBRUCH statt einer Warnung.

═══════════════════════════════════════════════════════════════════════
 DIE DREI ROLLEN - aus dem Neubauplan vom 25.09.
═══════════════════════════════════════════════════════════════════════

    A  RICHTUNG              geht es aufwaerts? Trendumkehr?
                             Testform: monotone Ordnung PLUS Spiegelprobe
    B  BEWEGUNGSERWARTUNG    kommt ueberhaupt etwas?
                             Testform: gegen die AUFLOESUNGSRATE, nicht
                             gegen `q` - B ist richtungslos
    C  RISIKOSPERRE          ueberdehnt, ueberhitzt?
                             Testform: AUSSCHLUSSTEST - verbessert das
                             WEGLASSEN des Extrems das Ergebnis des Rests?

    Anordnung:  A und B und NICHT C
                keine Summe, kein gemeinsames Fuenftel

⚠️ Nutzerbefund 25.09.: *"Mein Fehler bis zum 25.09.: alle drei Rollen in
EINE Rangliste geworfen und nach 'oberstes Fuenftel' gefragt."* - und am
27.09. habe ich denselben Fehler wiederholt.
"""
from __future__ import annotations

# ══ DIE ROLLEN ══════════════════════════════════════════════════════
#
# ⭐⭐⭐ 29.09.2026 GEPRUEFT UND PRAEZISIERT (Basisinfos/Einordnung_Beitraege_29_09.md,
# Abschnitte 8-9; Nutzer: *JA - DU musst noch pruefen und gegenpruefen, ob der
# Vorschlag halten kann*). Das Schema vom 25.09. HAELT - aber B und C wirken
# NICHT als Gewichte auf das Signal, sondern auf ANDERE Ausgaben:
#
#   A  entscheidet OB        - P(oben zuerst), die Richtung. Zeitpunkt:
#                              VORHER (OPTIMUM) oder WAEHREND (Fortsetzung,
#                              eigener Einstiegstyp - Nutzer: Quant +400 %)
#   B  entscheidet WIE WEIT  - richtungslos (oi_aenderung Spiegel 1,02-1,07,
#                              2.655); vergroessert Anstieg UND Rueckgang
#                              (2.655/2.662); in ATR kaum groesser (2.667) ->
#                              Potential und Geometrie, nicht die Wahrscheinlichkeit
#   C  entscheidet WIE VIEL HEBEL - Pfadrisiko: hohes ema_abstand setzt sich
#                              nach OBEN fort (2.655), aber mit groesserem
#                              Rueckgang (2.642) -> Bewertung 2 (Hebel, Stop)
#
# ➤ *A und B und NICHT C* heisst damit: drei verschiedene Ausgaben, keine
#   Summe, kein Blocker (Nutzer 28.09.: *Achsen sind Gewichte*).
ROLLEN = {
    "A": "Richtung - kommt es eher nach OBEN? (P oben zuerst) - liefert das SIGNAL; "
         "vorher (OPTIMUM) oder waehrend (Fortsetzung)",
    "B": "Bewegungserwartung - wie WEIT kann es gehen? (richtungslos) - bestimmt "
         "Potential und Geometrie, nicht die Wahrscheinlichkeit",
    "C": "Risikosperre - wie weit geht es GEGEN mich? - wirkt ueber Bewertung 2 auf "
         "Hebelstufe und Stop, nicht auf das Signal",
}

# ══ DIE DREI ARBEITSMODI - und warum ich sie verwechselt habe ═══════
#
# ⚠️⚠️⚠️ NUTZERVORGABE 27.09.2026: *"Du musst sauber zwischen MESSEN,
# KALIBRIEREN und PRUEFEN AN ECHTDATEN umschalten koennen."*
#
# Es sind keine neuen Phasen - es ist die Feinstruktur von Phase 1 und 2
# des Hauptplans. Aber sie beantworten VERSCHIEDENE Fragen, und ich habe
# die Antworten wiederholt gegeneinander ausgespielt.
MODI = {
    "messen": (
        "Phase 1",
        "Wo liegen historisch die besten LAGEN und Risikobewertungen?",
        "Erlaubt: jede Anordnung, auch Trailing und CRV - sie ist "
        "MESSWERKZEUG, nicht Systemeigenschaft. Verboten: das Ergebnis "
        "als Bewertungsgroesse weiterreichen (Ebene B, 2.641)"),
    "kalibrieren": (
        "Phase 1",
        "Wie wird aus der Lage eine BEWERTUNG - Einstieg gut/sehr gut, "
        "dann Hebelhoehe?",
        "Erlaubt: nur was zum ENTSCHEIDUNGSZEITPUNKT bekannt ist - Kurs, "
        "EMA, ATR, Chance und Risiko als Erwartung. Verboten: Kapital, "
        "Positionsgroesse, Kapazitaet, Kelly, q aus Ertraegen, und die "
        "GEOMETRIE (Nutzervorgabe 27.09.)"),
    "pruefen": (
        "Phase 2",
        "Was kommt an Echtdaten heraus - wieviele Signale, welche Hoehen, "
        "welches Ergebnis?",
        "HIER kommen Hebel 2x bis 5x und die GEOMETRIE wieder ins Spiel "
        "(Nutzervorgabe 27.09.). Und Takt, Cooldown, Kapazitaet - "
        "Ebene C"),
}

# ⚠️⚠️ DIE VERWECHSLUNG, DIE ES ZU VERHINDERN GILT, ist konkret und
# zweimal passiert:
#
#   messen -> kalibrieren   Ich habe `E[R]` (enthaelt CRV 1,5, also eine
#                           REGEL) als Bewertungsgroesse gedacht. Es ist
#                           eine MESSgroesse. Die Bewertung kennt nur
#                           Chance und Risiko.
#   pruefen -> kalibrieren  Ich habe aus dem Depot-Ergebnis auf die
#                           Bewertung zurueckgeschlossen (2.639/2.640,
#                           beide abgeloest).

# ══ DIE EBENE DER AUSWAHL - Markt oder Asset ════════════════════════
#
# ⚠️⚠️⚠️ NUTZERENTSCHEIDUNG 26.09.2026 (Befunde 2.608 bis 2.610),
# woertlich: *"Warum sprichst du von Rangfolge? Das System muss auch bei
# nur 'Einem' Asset funktionieren und nicht besser oder schlechter durch
# die Watchlist werden?!?!"*
#
# ⛔⛔ UND ICH HABE SIE AM SELBEN TAG WIEDER EINGEFUEHRT. `2.626` und
# `2.628` waehlen *je Tag die besten 2 Prozent* - ein Querschnittsrang
# ueber alle Assets, also MARKTEBENE. Im Quelltext steht es sogar so
# (`messe_inverse_achse.taeglich_beste`: *welches Asset ist HEUTE das
# beste?*).
#
# ➤ Ein Perzentil ist eine Aussage ueber die MENGE, keine ueber das
#   ASSET. Dieselbe Lage bekaeme bei 116 Symbolen ein anderes Urteil als
#   bei 28 - derselbe Fehler, vor dem die Regel *die Grundgesamtheit ist
#   keine Stellschraube* warnt, nur in der ANWENDUNG statt in der Messung.
#
# ⚠️ `ema_abstand_atr` ist bereits normiert (Abstand zum 48-h-EMA in
# Einheiten der EIGENEN Volatilitaet) und braucht keinen Vergleich.
AUSWAHLEBENE = {
    "gilt": "ASSET - eine ABSOLUTE Schwelle in ATR",
    "verboten": "MARKT - ein Querschnittsrang oder Perzentil je Tag",
    "betroffen": ("2.626 (Auswahl je Tag beste 1/2/5 Prozent)",
                  "2.628 (Geometrie auf genau dieser Auswahl dimensioniert)"),
    "sauber": ("2.608/2.609/2.610 (absolute Schwelle in ATR)",
               "2.647 (absolute Schwellen -1,0 bis -1,8)"),
}

# ══ ⚠⚠⚠ DREI ABDECKUNGEN, DIE NICHT DASSELBE SIND ═════
#
# Nutzerhinweis 27.09.2026: *"wir sollten ueberall ca. 87 % Abdeckung mit
# Workaround haben"* - und ich hatte gerade `turnover` mit *30 Prozent
# Abdeckung, strukturell nicht zu retten* abgeschrieben. Beides stimmt,
# weil es DREI verschiedene Groessen sind.
ABDECKUNGEN = {
    "mess": ("Anteil der ANKER mit Wert - fuer die MESSUNG",
             "funding 99,1 % · oi_aenderung 98,0 % · "
             "oi_je_umsatz 97,3 % · volumenschub 100 % · "
             "konten_verh 97,6 % · turnover 30,0 %"),
    "symbol": ("Anteil der SYMBOLE mit Wert - fuer den BETRIEB",
               "funding 116/116 · Terminmarkt 116/116 · "
               "turnover 113/116 (97 %) · onchain 17/116 · "
               "tvl 36/116"),
    "betrieb": ("Anteil der FREIGEGEBENEN Hebelsymbole mit Stundenkursen",
                "28 von 43 = 65 % · mit dem Laderfix aus 2.611 +9 "
                "auf 86 % · davon LIQUIDE (>100k USD/h) nur 15 = 35 %"),
}

# ⛔⛔ MEIN FEHLER, benannt: `turnover` hat 30 Prozent
# ZEITabdeckung (die Umlaufmenge reicht nur 1 von 4,8 Jahren zurueck) und
# 97 Prozent SYMBOLabdeckung. Fuer den BETRIEB zaehlt die zweite - er ist
# dort fast vollstaendig da. Was fehlt, ist MESSHISTORIE, nicht
# Verfuegbarkeit. Die Aussage *strukturell nicht zu retten* war falsch.
#
# ⚠ Und die Beschaffung ist versucht worden: `hole_umlaufmenge_cg.py`
# haelt im Kopf fest, dass die Suche nach mehrjaehriger Historie am
# 13.09. gescheitert ist - `market_chart?days=365` liefert genau ein Jahr.
# Das ist eine Grenze der Quelle, kein Versaeumnis.
#
# ⭐ UND EINE FORMFRAGE STECKT DAHINTER: `turnover` = Volumen /
# UMLAUFMENGE ist eine QUERSCHNITTSgroesse - sie vergleicht Assets. Die
# Nutzerentscheidung vom 26.09. verlangt das Gegenteil (*muss auch bei
# nur EINEM Asset funktionieren*). `volumenschub` (Volumen gegen den
# eigenen Schnitt) und `oi_je_umsatz` erfuellen das, haben volle
# Abdeckung und laufen seit 2.651 mit.

OFFENE_AUFGABEN = (
    ("Laderfix 2.611 - 65 % auf 86 % Betriebsabdeckung",
     "`hole_stundenkurse.py` leitet die Symbolliste aus dem TERMINMARKT "
     "ab (Binance Futures), prueft die Handelbarkeit dann aber gegen "
     "api.binance.com - die SPOT-Boerse. Symbole, die es nur als "
     "Perpetual gibt, fallen heraus, obwohl ihre Kurse ueber "
     "fapi.binance.com verfuegbar waeren. 9 von 15 fehlenden waeren "
     "beschaffbar. GEMESSEN am 26.09., NICHT GEBAUT - der Lader ist "
     "unveraendert (Zeile 79/80)"),
    ("Die Liquiditaetsgrenze bleibt",
     "auch mit dem Laderfix erreichen nur 15 von 43 Symbolen 100.000 USD "
     "Medianumsatz je Stunde. Das ist KEIN Asset-Vorurteil (Regel 3), "
     "sondern eine physische Handelsgrenze - bei 13.000 USD "
     "Stundenumsatz waere ein Trade von 5.000 USD 38 Prozent des Volumens"),
    ("Vorlauf bei laengeren Fenstern",
     "2.651 zeigt: je laenger das Fenster, desto hoeher die Haltequote "
     "(0,29 bei H6, 0,74 bei H48). Ob sie bei H72 oder H120 die Schwelle "
     "0,8 erreicht, ist NICHT gemessen - und das waere der erste Beitrag "
     "mit echtem VORLAUF"),
)


# ══ DAS REGELWERK - zwei Bewertungen, zwei Zielgroessen ═════
#
# Ausfuehrlich: `Basisinfos/Regelwerk_Hebel_Bewertung_27_09.md`
#
# ⛔⛔⛔ DER FEHLER, DER ES NOETIG MACHTE (Nutzerkritik 27.09.2026):
# *"Was ist mit turnover und funding, diese waren bereits gesetzt oder?
# Du hast recherchiert und noch immer keine Ahnung zum Einstieg und den
# Merkmalen."*
#
# An einem Tag habe ich zehn KURSmerkmale gemessen - und die DREI
# einzigen registrierten Traeger des Systems kein einziges Mal geladen.
# Mein eigener Riegel hat sie mir aus dem Blick genommen: `SPOT_QUELLEN`
# sperrt `funding_fuenftel`, und ich habe die Sperre stillschweigend auf
# die ROHGROESSE `funding` ausgedehnt - obwohl E-3 sie ausdruecklich
# freigibt.
#
# ⭐ DER KERN DES REGELWERKS, und er hat mir bis heute gefehlt:
#
#     EINSTIEG misst gegen die CHANCE, HEBEL gegen das RISIKO.
#     Zwei Zielgroessen, zwei Messungen - ein Merkmal kann in der
#     einen tragen und in der anderen nicht.
# ⭐ 27./28.09. NACHGEZOGEN auf die abgestimmte ANWENDUNGSEBENE K1-K7
# (Basisinfos/Voranalyse_Kombination_Anwendungsebene_27_09.md, Nutzer je
# Punkt *ja, so eintragen*): K4 legt das Ereignis fest (q5), K2 den Bezug
# (die PHASE des eigenen Assets), K5 die Schwelle auf kalibriertem q und
# 3-5 Stufen, K6 die Hebelstufe aus der Liquidationsgefahr. Vorher stand
# hier *+X Prozent in Y Stunden, Lift gegen das eigene Asset* und *MAE in
# ATR* - beides war gesetzt, nicht gemessen (2.655, 2.667).
REGELWERK = {
    "bewertung_1": {
        "name": "Einstieg - zulaessig?",
        "frage": "Kommt eine Bewegung nach oben?",
        "zielgroesse": "EREIGNIS q5: +5 Prozent vor -5 Prozent binnen 24 h "
                       "(K4 - Ausgangsbasis; Hoehe x Fenster ist eine Achse, "
                       "ein spaeterer Erfolg zaehlt mit)",
        "bezug": "die PHASE des eigenen Assets - seine letzten 12 Monate, nur "
                 "bekannte Ausgaenge (K2); Kontrollen: Moment (Monat) und Tag",
        "nullpunkt": "q der Phase (Dq = q(Lage) - q(Phase)) - das Normal ist der "
                     "BEZUGSPUNKT, es entscheidet nicht mit (K5 geaendert 28.09.)",
        # ⭐ K5 GEAENDERT 28.09. (Nutzer: *ja, K5 Schwelle auf den Beitrag*,
        # VORLAEUFIG - *wenn das auch nicht klappt, muessen wir wieder
        # abstimmen*): nach 2.678 waehlt eine Schwelle auf Normal + Kurven das
        # Phase-Normal, und das kehrt zur Mitte zurueck
        # ⛔ 29.09. (2.680): die Beitragsauswahl ist robust (T6), aber der
        # Beitrag ist NICHT kalibriert (T3) und nicht besser als rsi allein
        # (T2) - nach der Vorabfestlegung wird K5 NEU VORGELEGT
        "ergebnis": "nein | 3 bis 5 Stufen, so viele wie trennscharf, Schwelle "
                    "auf dem BEITRAG - dem kalibrierten Vorsprung gegen das eigene "
                    "Normal (K5, vorlaeufig; 2.680: nicht kalibriert, K5 neu "
                    "vorzulegen)",
        # ⚠️ Bis 27.09. abends stand hier ein FILTER (*muss mindestens 3
        # Stunden Karenz ueberleben*). Der Nutzer hatte ihn schon in 2.650
        # verworfen: *bin mir nicht sicher, ob du dies nur fuer die
        # Messung als Annahme siehst oder wir gute Signale kappen.*
        "zusatzbedingung": "KARENZ als ACHSE, nicht als Filter (2.650): "
                           "k=0 ist der BETRIEBSFALL, im Betrieb steigt "
                           "man sofort ein. k>0 ist die Diagnose, ob das "
                           "Merkmal die Bewegung VORHERSAGT oder nur "
                           "begleitet (VORLAUF). Beide Zahlen werden "
                           "ausgewiesen, keine kappt die andere. In K1 "
                           "gemessen als ALTERSACHSE (das Merkmal L Stunden "
                           "alt) und A4 (bisheriger Anstieg in eigener ATR: "
                           "bestaetigt oder gelaufen - Nutzer 28.09.)",
    },
    "bewertung_2": {
        "name": "Hebelhoehe",
        "frage": "Wie weit geht es gegen mich, bevor es fuer mich geht?",
        "zielgroesse": "MAE in PROZENT gegen den Liquidationsabstand der Stufe "
                       "- die LIQUIDATIONSGEFAHR je Stufe (K6), am Markpreis "
                       "(K7: Hauptmass bestaetigt 2.679; Bitpanda-Formel m = "
                       "0,09 vorsichtig, bis 5x an echten Positionen kein "
                       "Fehlalarm; Orientierung 5x ~ -12 "
                       "%, 3x ~ -27 %, 2x ~ -45 %). ATR zum Einstieg ist das "
                       "Risikomass (2.667)",
        "bezug": "das eigene Asset",
        "nullpunkt": "die Nutzergrenze fuer die Liquidationswahrscheinlichkeit",
        "ergebnis": "2x | 3x | 5x - die HOECHSTE Stufe unter der Grenze (K6); "
                    "zuerst nur Risiko (R), R+S als Folgemessung",
        "zusatzbedingung": "geringeres Risiko -> HOEHERE Stufe",
    },
}

# ⚠⚠ WO WELCHER BEITRAG ZAEHLT - der Stand, ehrlich.
#
# ⛔⛔ BIS 27.09. ABENDS STAND HIER DER STAND VOR 2.651 - und die Suite
# erzwang ihn: eine Pruefung verlangte `funding`, `turnover` und
# `oi_aenderung` als "ungemessen". Das Blatt schickte jede neue Session
# auf eine Messung, die schon gelaufen war. Deshalb traegt jetzt JEDER
# Eintrag seinen Befund, und die Wache leitet die gemessenen Merkmale aus
# dem QUELLTEXT der Messskripte ab (`gemessene_merkmale`), nicht aus
# einer Liste, die man vergisst.
#
# Zustaende je Bewertung:
#   "belegt"     gemessen auf DIESER Frage, alle sechs Pruefungen
#   "faellt"     gemessen und durchgefallen (Band, Spiegelprobe, Richtung)
#   "ungemessen" auf dieser Frage NIE gemessen (nicht: gefallen)
#   "spur"       ein Hinweis im Register, nicht gemessen
#
# ⭐ `vorlauf` ist ein EIGENES Feld (E1/E2, 27.09.): die Karenz ist eine
#   ACHSE. "belegt" heisst: traegt beim sofortigen Einstieg (k=0).
#   `vorlauf` sagt, ob es die Bewegung auch VORHER anzeigt - das
#   Optimum laut Nutzerdefinition. None = entfaellt, weil b1 nicht traegt.
#
# ⭐ `live` fragt nach der QUELLE, nicht nach dem heutigen Sammler -
#   Nutzerhinweis 27.09.: *der aktuelle Betriebscode ist veraltet.*
#
# ⭐ `spot` (E-8, Nutzervorgabe 27.09.): die Spot-Quellen sind NICHT
#   irrelevant. Sie wurden fuer H20 optimiert und vermessen - nur die
#   ANWENDUNG ist auf den Hebel zu dimensionieren (kurzer, intensiver
#   Handel). Die Spot-MESSWERTE gelten fuer den Hebel nicht (Riegel).
_Q_TM = ("terminmarkt_historie.db - Binance-Archiv data.binance.vision, "
         "5 min, je Stunde der LETZTE Wert (~HH:55)")
_L_TM = ("ja - dieselben Kennzahlen ueber die Binance-Futures-"
         "Datenendpunkte (an der echten API zu bestaetigen; das Archiv "
         "selbst gibt es nur tageweise)")
_Q_KURS = "stundenkurse.db - Binance-Stundenkerzen"
_L_KURS = "ja - Binance-Stundenkerzen"
BEITRAGSLAGE = {
    # ── die drei registrierten Traeger ───────────────────────────────
    "funding": dict(
        b1="belegt", vorlauf="nein", b2="ungemessen",
        befund=("2.663", "2.665", "2.666", "2.676", "2.683"),
        beleg="mit dem VORTAGESWERT: Lift 4,45 bei <= -0,0040 auf +15 "
              "%/H12 (vorher 9,55 - die Haelfte war Vorgriff), traegt auf "
              "H6/H12/H24, +30 %/H48 nur Bewegung; >= 0,0016 zeigt nach "
              "UNTEN (Spiegel 0,43). K1 (q5 gegen die Phase): die Wirkung ist "
              "MARKT (Tag/Phase 0,02-0,31); geteilt traegt der Asset-Anteil "
              "nicht, der Marktanteil am UNTEREN Rand gegen die gemeinsame "
              "Nullwelt in 4 von 4 Mengen (Suche +0,10..+0,14, 2.675)",
        quelle="funding_historie.db - Binance fundingRate, gespeichert "
               "als TAGESSUMME der drei Abrechnungen (00/08/16 UTC)",
        live="ja - aber als EINZELSATZ je Abrechnung; die Tagessumme ist "
             "erst nach Tagesende bekannt",
        spot="Regler, auf H20/bewegung_r vermessen (290 Symbole, 6,3 Jahre)",
        vorbehalt="NUR IN DER SUCHE NACHGEWIESEN (2.675): Pruefzeit +0,024.."
                  "+0,032 und 2022 +0,031..+0,040 liegen je innerhalb EINER "
                  "Streuung des Marktrauschens (0,035) - die Groesse in "
                  "ungesehener Zeit ist nicht gesichert; als KONTEXT-"
                  "Kandidat, nicht als Beitrag je Asset. KURVE (2.683): stark "
                  "negativ +0,11, sehr hoch -0,10 - vorher A-Kandidat, Extreme "
                  "C-Kandidat (KANDIDATEN)"),
    "oi_aenderung": dict(
        b1="belegt", vorlauf="nein", b2="ungemessen",
        befund=("2.663", "2.662", "2.676"),
        beleg="Lift 6,23 bei >= 0,3355 auf +20 %/H24, 5,02 auf +30 %/H48; "
              ">= 0,1088 traegt auf H12/H24; Haltequote 0,55 bis 0,67. K1: "
              "asset-eigen (Tag/Phase 0,8-0,9), Kurve nicht monoton; UNTERER "
              "Rand nach dem Randkriterium in 3 von 4 Mengen (2.675)",
        quelle=_Q_TM, live=_L_TM,
        spot="Schalter, auf H20 vermessen (117 Symbole, 126.491 Anker)",
        vorbehalt="OHNE UNABHAENGIGE BESTAETIGUNG (2.675): der untere Rand "
                  "liegt in der Pruefzeit bei +0,011..+0,015 - gleich dem "
                  "Versatz der Zufallsraender (+0,009/+0,013)"),
    "turnover": dict(
        b1="faellt", vorlauf=None, b2="ungemessen", befund=("2.663",),
        beleg="ueber dem Band, aber NUR BEWEGUNG (Spiegel 0,76 bis 1,67 "
              "gegen 1,717) in allen vier Fenstern; die voll abgedeckte "
              "Schwestergroesse `volumenschub` faellt genauso",
        quelle="Stundenvolumen / freier Umlauf (umlaufmenge_cg.db) - der "
               "Nenner reicht nur 2025-09 bis 2026-09: 30 % der Anker, "
               "113 von 116 Symbolen",
        live="ja - Stundenkerzen und CoinGecko-Umlauf (taeglich)",
        spot="Regler, auf H20 vermessen - die Spot-Form (Tageskerze, "
             "Fuenftel) ist davon UNBERUEHRT",
        vorbehalt=""),
    # ── Terminmarkt und Volumen, mitgemessen in 2.651 ───────────────
    "konten_verh": dict(
        b1="belegt", vorlauf="nein", b2="ungemessen",
        befund=("2.663", "2.676", "2.683"),
        beleg="Lift 2,96 bei <= 0,5759 - traegt NUR auf H6 und H12; "
              "Haltequote 0,60 bis 0,66. K1: ueberwiegend MARKT (Tag/Phase "
              "0,07-0,18). Marktanteil am UNTEREN Rand (wenige Longs "
              "marktweit) in 3 von 4 Mengen; die SPERRE viele Longs JE ASSET "
              "(2.660/2.674) haelt in der Pruefzeit NICHT (2.675)",
        quelle=_Q_TM, live=_L_TM, spot="",
        vorbehalt="NUR IN DER SUCHE NACHGEWIESEN (2.675): Pruefzeit "
                  "+0,026..+0,028 innerhalb der Marktstreuung; die Sperre je "
                  "Asset ist in der ungesehenen Zeit nicht vorhanden. KURVE "
                  "(2.683): die staerkste - wenige Longs +0,15, viele -0,25"),
    "oi_je_umsatz": dict(
        b1="faellt", vorlauf=None, b2="ungemessen", befund=("2.663", "2.662"),
        beleg="ueber dem Band, aber nur Bewegung (Spiegel 1,00 bis 1,53)",
        quelle=_Q_TM + " und Stundenvolumen", live=_L_TM, spot="",
        vorbehalt=""),
    "volumenschub": dict(
        b1="faellt", vorlauf=None, b2="ungemessen",
        befund=("2.663", "2.662", "2.667", "2.681"),
        beleg="ueber dem Band, aber nur Bewegung (Spiegel 0,95 bis 1,35). "
              "HOEHE auch UEBER die ATR hinaus: P95 +0,08 ATR mfe, 30 von 32 "
              "Monaten, jede BTC-Lage (2.667) - ROLLE B (Hoehe). Als "
              "Risikokurve der Hebelstufe kein Mehrwert ueber die ATR (2.681)",
        quelle=_Q_KURS, live=_L_KURS, spot="", vorbehalt=""),
    "taker_verh": dict(
        b1="faellt", vorlauf=None, b2="ungemessen", befund=("2.663",),
        beleg="in keiner Zielgroesse ueber dem Suchband (Bestes-von-160, "
              "2,834)",
        quelle=_Q_TM, live=_L_TM, spot="", vorbehalt=""),
    "top_konten_verh": dict(
        b1="faellt", vorlauf=None, b2="ungemessen", befund=("2.663",),
        beleg="in keiner Zielgroesse ueber dem Suchband (2,834)",
        quelle=_Q_TM, live=_L_TM, spot="",
        vorbehalt=""),
    "top_summe_verh": dict(
        b1="faellt", vorlauf=None, b2="ungemessen", befund=("2.663",),
        beleg="in keiner Zielgroesse ueber dem Suchband (2,834)",
        quelle=_Q_TM, live=_L_TM, spot="",
        vorbehalt=""),
    # ── Kursmerkmale (EMA/RSI/ATR-Familie, abgeschlossen) ──────────
    "ema_abstand_atr": dict(
        b1="faellt", vorlauf=None, b2="belegt",
        befund=("2.642", "2.647", "2.648", "2.650", "2.671", "2.676"),
        beleg="B2: d 0,521 auf MAE gegen 0,267 auf MFE (2.642), absolut "
              "und je Asset (2.647). B1: Richtung RUNTER - Abstuerze "
              "9,8-fach (2.648), bei Karenz null von 11 (2.650). "
              "Risikosperre, keine Chance. ⚠ K1 (q5 gegen die PHASE, andere "
              "Frage): SELBSTBEZOGEN traegt die Kurve, monoton, asset-eigen, "
              "A4 bestaetigt bis ~2 ATR (2.671); der OBERE Rand kehrt aber 2022 "
              "in allen 4 Mengen (-0,014..-0,020, 2.675)",
        quelle=_Q_KURS, live=_L_KURS, spot="",
        vorbehalt="2022 (2.676): der AKTUELLE Wert am oberen Rand kehrt 2022 "
                  "(-0,014..-0,023), der 24 h alte nicht (+0,026..+0,049) - in "
                  "der Kombination mit dem Alter gewichten, nicht sperren"),
    "momentum_kurz": dict(
        b1="belegt", vorlauf="nein", b2="ungemessen",
        befund=("2.648", "2.650", "2.676"),
        beleg="Lift 6,93 auf +15 %/H6, alle sechs Pruefungen (2.648); "
              "Haltequote k24/k0 0,31, bei k=3 schon null von 11 (2.650) - "
              "BEGLEITET, sagt nicht vorher. K1: OBERER Rand (selbst) traegt "
              "in 4 von 4 Mengen, Pruefzeit +0,026..+0,035 - rund dreimal "
              "der Versatz; A4 bestaetigt, nicht gelaufen (2.675). ALTERSACHSE "
              "gueltig (2.676): am staerksten 1-9 h alt, 24 h alt traegt in "
              "Suche, Pruefzeit und 2022",
        quelle=_Q_KURS, live=_L_KURS, spot="",
        vorbehalt=""),
    "rsi": dict(
        b1="belegt", vorlauf="nein", b2="ungemessen",
        befund=("2.648", "2.650", "2.676", "2.680", "2.683", "2.684"),
        beleg="Lift 4,67 auf +15 %/H6 (2.648); Haltequote 0,43 (2.650). K1: "
              "OBERER Rand (roh und selbst) traegt in 4 von 4 Mengen, "
              "Pruefzeit +0,038..+0,054 - drei- bis sechsmal ueber dem "
              "Versatz; A4 bestaetigt; korreliert mit momentum (+0,62, 2.675). "
              "ALTERSACHSE gueltig (2.676): Delle bei 6-12 h, 24 h alt wieder "
              "voll - in Suche, Pruefzeit und 2022. ALLEIN waehlt es besser aus "
              "als jede Kombination (2.680, 2.683); keine Normal-Verzerrung, "
              "roh fast kalibriert (2.683, 2.684)",
        quelle=_Q_KURS, live=_L_KURS, spot="",
        vorbehalt="ROLLE A WAEHREND (Fortsetzung), nicht OPTIMUM: der RSI der "
                  "letzten 14 h kann einen Anstieg nie VORHER anzeigen (Nutzer "
                  "29.09.: *Sportwagen, der schon 200 faehrt*); 2024 schwach, "
                  "zeitstabil nur in der Betriebsform (2.684)"),
    "vola": dict(
        b1="faellt", vorlauf=None, b2="spur", befund=("2.650", "2.662"),
        beleg="Lift 7,81, faellt an der Spiegelprobe (1,31) = nur "
              "Bewegung. B2-Spur laut Register: *ueber hebel = "
              "verlustanteil / stop_rel faellt daraus der Hebel*. HOEHE "
              "(2.662, als vola_kausal): P99 +6,56 Prozentpunkte mfe, "
              "vorwaerts in jeder BTC-Lage - aber maevp steigt mit. IN ATR "
              "(2.667) dreht es: P99 -0,17 ATR - die Bewegung ist gross, "
              "WEIL die Spanne gross ist. Fuer die Liquidation (Prozent) ist "
              "die ATR zum Einstieg selbst das Risikomass: 5x-Grenze binnen "
              "72 h im obersten ATR-Fuenftel 26,9 %, im untersten 5,8 %",
        quelle=_Q_KURS, live=_L_KURS, spot="",
        vorbehalt=""),
    "bandenge": dict(
        b1="faellt", vorlauf=None, b2="ungemessen", befund=("2.650",),
        beleg="Lift 0,84 bis 1,22 gegen ein Band von 2,77 - es haelt die "
              "Karenz, weil es NICHTS misst. ⚠ Der fruehere Eintrag "
              "*faellt* auf B2 hatte KEINEN Befund: 2.645 mass gegen E[R], "
              "2.650 gegen das Ereignis - keines gegen MAE",
        quelle=_Q_KURS, live=_L_KURS, spot="", vorbehalt=""),
    # ── das Risikomodell der Hebelstufe (29.09.) ────────────────────────
    "atr": dict(
        b1="ungemessen", vorlauf=None, b2="belegt", befund=("2.667", "2.681"),
        beleg="die ATR zum Einstieg sagt die Liquidationsgefahr je Stufe voraus "
              "(2.667); am Markpreis und am Spot-Tief, vier Mengen: 5x vorwaerts "
              "kalibriert, 3x nur geordnet, 2x zu selten; Risikokurven bringen "
              "nichts dazu (2.681). Die Tabelle je Grenze liegt vor",
        quelle=_Q_KURS, live=_L_KURS, spot="",
        vorbehalt="H0 offen: die Gefahr auf der tatsaechlichen EINSTIEGSAUSWAHL "
                  "ist Pflicht vor jeder Verwendung (2.681)"),
}

# ⚠️⚠️ NEUESTER STAND (27.09. abends, E1 bis E2d) - er geht der Beitragslage
# oben VOR. Die Beitragslage misst gegen die Zielgroessen des Regelwerks
# (Ereignis-Lift, MAE); E2 misst gegen das EIGENE Asset und regelfrei. Wo sie
# sich widersprechen, gilt E2, bis die Zielgroessen neu festgelegt sind.
# Die Wache verlangt, dass hier der NEUESTE Neubau-Befund steht - sonst
# veraltet dieses Blatt still, wie am 27.09. schon einmal.
NEUESTER_STAND = (
    ("2.654", "E1: Bewegungen erhoben. Ab +10 Prozent braucht es von einem "
              "beliebigen Zeitpunkt meist mehr als 24 h; fuer 2x/3x ist die "
              "Liquidation kaum der Engpass, das Risiko ist der Rueckgang VOR "
              "dem Gewinn; die Grundrate schwankt je Asset um Faktor 2,6"),
    ("2.655", "E2: die Beitraege sagen die HOEHE stark voraus (vola, "
              "oi_je_umsatz, oi_aenderung, volumenschub), die RICHTUNG nur "
              "schwach - kein Kandidat erreicht die Spiegelschwelle. Spuren: "
              "hoch ueber dem Mittel und wenige Longs positiv, viele Longs "
              "negativ. oi_aenderung ist Hoehe, nicht Richtung"),
    ("2.656", "Der Ertrag der UNTEREN Achse (2.626/2.631/2.647) kam aus der "
              "TRAILING-Regel. Regelfrei ist das untere Ende kein Einstieg; "
              "2.643 (ganze Achse = Sperre) ist ueberholt. Die Trailing-Befunde "
              "gehoeren in die Positionsfuehrung"),
    ("2.657", "Die Lage hohe Vola & wenige Long-Konten (dort noch *Squeeze* "
              "genannt - eine Deutung, keine Messung) haelt im unberuehrten "
              "Jahr 2024 NICHT. Risiko hoch: ueber alle Einstiege binnen 120 h "
              "im Median -10 bis -15 Prozent"),
    ("2.658", "Vorgriff in vola (Median der ganzen Reihe, 2.650) und "
              "Stundenluecken (Zeilen statt Stunden) in aelteren Werkzeugen - "
              "abgeloest durch 2.664"),
    ("2.659", "E3 VORWAERTS 2024-2026 (rollierend kalibriert): KEIN Einstieg "
              "traegt in jedem Regime - nach Nutzervorgabe ein Punkt zum Reden. "
              "Abgeloest durch 2.660"),
    ("2.660", "GEGENPRUEFUNG E3: die Anlage haelt (Selbstprobe, Tausch, "
              "Zufall, Vorgriff erkannt). ZURUECKGENOMMEN: hohe Vola & wenige "
              "Long-Konten ist FRAGIL (1 h Versatz halbiert oder loescht es), "
              "die Bestaetigung hilft nur bei 5 von 9. ROBUST: die SPERRE viele "
              "Longs, in allen Regimen und Laeufen negativ"),
    ("2.661", "RICHTUNGSDATEN geladen und geprueft: Kaeuferanteil, "
              "Premium-Index, BTC-Dominanz-Index (BTCDOMUSDT), stuendlich "
              "2023-01 bis 2026-08, data/richtung_historie.db. Naechster "
              "Schritt: sie mit dem Pflichtablauf messen (E2 -> E3 -> "
              "Gegenpruefung)"),
    ("2.662", "HOEHE GEGENGEPRUEFT: 14 von 16 Auswahlen tragen streng "
              "gegen das eigene Asset im Monat, auf Episoden, vorwaerts in "
              "JEDER BTC-Lage, P2/P4 bestanden. Aber maevp steigt mit: die "
              "Groesse der Bewegung, kein Vorteil. Einheit fuer Bewertung 2 "
              "(Prozent oder ATR) offen"),
    ("2.663", "FUNDING-VORGRIFF GEMESSEN: 2.651 bitgleich reproduziert, mit "
              "dem Vortageswert halbiert sich der Lift (9,55 auf 4,45), 13 "
              "Zellen werden 9. funding traegt weiter, aber der Pflichtablauf "
              "fehlt noch"),
    ("2.664", "2.658 GEMESSEN: Luecken (0,4 Prozent der Anker) und kausale "
              "vola verschieben kein Urteil von 2.648/2.650 - weiter 2 von 11 "
              "bei k=0, 0 bei jeder Karenz; vola bleibt nur Bewegung"),
    ("2.665", "RICHTUNG im Pflichtablauf (E2f/E2g): 4 von 88 halten, 0 von 80 "
              "Zufall. Nur funding ist LAGE VORHER (Vortag negativ q5 +0,037, "
              "hoch = Sperre -0,043) - und klein. kaeufer_24h BEGLEITET die "
              "Bewegung, momentum_kurz IST sie. Such-/Pruef-Trennung fehlt"),
    ("2.666", "FUNDING HAELT AUF 2022 (Mittel +0,028, 10 von 12 Startstunden; "
              "Suchzeitraum +0,025). Die erste Fassung *dreht* war ein "
              "Mitternachtseffekt der Episodenregel. Der alte gute Ruf kam "
              "zusaetzlich aus dem BEZUG: funding markiert auch die PHASE"),
    ("2.667", "HOEHE IN ATR: die Prozent-Hoehe ist groesstenteils die ATR "
              "selbst; ueber sie hinaus traegt vor allem volumenschub. Fuer die "
              "Liquidation ist die ATR zum Einstieg das Risikomass (5x binnen "
              "72 h: 5,8 % im untersten, 26,9 % im obersten ATR-Fuenftel)"),
    ("2.668", "Die Stundenkurse waren UEBERLEBENSVERZERRT (nur TRADING-Paare, "
              "BTC erst ab 2023-09) - abgeloest durch 2.669"),
    ("2.669", "MIT DEN EINGESTELLTEN (137 nachgeladen, geprueft): funding und "
              "Hoehe halten, Kontext stabil; die LIQUIDATIONSGEFAHR bei 3x/2x "
              "steigt um 17-65 Prozent - der Boden fehlte. Richtungsurteile am "
              "Rand kippen, die Werte bleiben. Messbasis ab jetzt --menge unverzerrt"),
    ("2.670", "K3 KONTEXTFLAECHE: kein Feld traegt, deine Hypothese (BTC hoch/"
              "mitte und Dominanz faellt) haelt nicht; die Sperre aus 2.665 "
              "faellt nach R-R11 (z -1,52 statt -6,9). ABER die Anlage sieht "
              "Kontext erst ab ~0,06-0,08 - Kontext wirkt auf Markttage, nicht Anker"),
    ("2.671", "K1 WIRKUNGSKURVEN (11 Merkmale): ema_abstand_atr SELBSTBEZOGEN "
              "traegt (3 von 4 Mengen, monoton, asset-eigen, Lage vorher); A4: "
              "bestaetigt bis ~2 ATR bisherigen Anstieg, danach schwaecher. "
              "Aufloesung +-0,02. Kaeuferanteil, momentum ohne Befund"),
    ("2.672", "Die Dominanz-Sperre aus 2.601 faellt ebenfalls: bitgleich "
              "reproduziert (-0,0134), gegen die Zeitverschiebung z -1,59"),
    ("2.673", "funding/Premium GETEILT: Asset-Anteil traegt nicht, Marktanteil "
              "mit der richtigen (gemeinsamen) Nullwelt nicht nachweisbar - "
              "Aufloesung fuer Marktmerkmale grober als 0,04 - abgeloest durch 2.675"),
    ("2.674", "VIELE LONGS: marktweit ueber der gemeinsamen Nullwelt in allen "
              "4 Mengen (wenige Longs +0,14..+0,39, viele -0,13..-0,25) und je "
              "Asset als oberer Rand eine Sperre (-0,09..-0,14). Formal traegt "
              "keines - das Formkriterium scheitert an der flachen Mitte - "
              "abgeloest durch 2.675 (die Sperre je Asset haelt in der Pruefzeit nicht)"),
    ("2.675", "RANDKRITERIUM (vorab festgelegt), Regeltest bestanden (Zufall 0 von "
              "40 je Asset und als Marktreihe; Aufloesung je Asset +0,02, Markt "
              "~0,08): rsi und momentum tragen am OBEREN Rand je Asset in allen 4 "
              "Mengen, in der Pruefzeit drei- bis sechsmal ueber dem Versatz, A4 "
              "bestaetigt - Altersachse ungeklaert (6 h alt traegt fast nichts), "
              "Rolle Einstieg offen. funding_markt unten nur in der Suche "
              "nachgewiesen. ema_abstand oben kehrt 2022. Viele Longs je Asset "
              "haelt in der Pruefzeit nicht - abgeloest durch 2.676 (der "
              "Altersachsen-Satz war ein Lesefehler, alles uebrige gilt)"),
    ("2.676", "ALTERSACHSE (vorab festgelegt) GUELTIG: keine Umkehr in 11 "
              "Altern x 6 Kurven x 4 Mengen, Regeltest 1/0/0/0 von 88. Der 24 h "
              "ALTE Wert traegt am oberen Rand in Suche, Pruefzeit und 2022 - "
              "auch ema_abstand, das mit dem aktuellen Wert 2022 kehrt. Die "
              "Tagesperiode ist kein Artefakt der Ankeruhrzeit. Kein Blocker: "
              "aktueller und 24 h alter Wert als zwei abgestufte Beitraege"),
    ("2.677", "K1 SCHRITT 2: die Kombination als gemeinsames Kurvenmodell "
              "traegt NICHT (T1-T3 in keiner der vier Mengen, K5-Auswahl q >= "
              "0,55 = Grundrate). Die Regel ist sauber (Zufall schweigt), aber "
              "die Aufloesung reicht nicht (gepflanzt erst +0,16 sicher, gesucht "
              "+0,03..+0,06); der Marktmedian steht fuer die Zeit, 12 Monate "
              "reichen fuer 12-Stufen-Kurven nicht. Die Wirkung ist da: dort, wo "
              "*oben gestreckt*, liegt q ungesehen +0,07..+0,10 ueber der Schaetzung"),
    ("2.678", "K1 SCHRITT 2b: traegt nach dem Vorabkriterium NICHT (T2-T5; die "
              "Kombination ist schlechter als rsi allein). Ursache: wer nach Normal "
              "+ Beitrag auswaehlt, waehlt das PHASE-NORMAL, und das kehrt zur Mitte "
              "zurueck. Nach dem BEITRAG allein ausgewaehlt: q im obersten Zehntel "
              "+0,05 ueber dem Normal in allen vier Mengen, auch rollierend - etwa "
              "so viel wie der rsi-Rand allein. K5 (Schwelle auf Normal + Kurven) "
              "ist damit eine Nutzerentscheidung"),
    ("2.679", "K7: der Binance-MARKPREIS wird Hauptmass fuer K6 (am echten "
              "Bitpanda-Buch fast gleich dem Spot-Tief, nirgends schlechter). "
              "m = 0,09 liquidiert zu frueh, nie zu spaet; alle Fehlalarme in "
              "Buechern ueber 5x. Der Importer teilt die Positionen falsch ein "
              "(Teilschliessungen) und uebersah 3 von 7 Liquidationen"),
    ("2.680", "K1 SCHRITT 2c: die Auswahl nach dem BEITRAG ist robust - in jedem "
              "Drittel des Normals positiv (T6), in jedem Jahr und bei 80-86 % "
              "der Assets. Aber sie bringt NICHT mehr als rsi allein (T2), und der "
              "Beitrag ist nicht kalibriert (T3, Steigung 0,42-0,55). Nach der "
              "Vorabfestlegung: K5 neu vorlegen; rsi allein als einfachere Regel "
              "zur Bestaetigung - mit OPTIMUM (rsi misst die Bewegung)"),
    ("2.681", "K6: die ATR zum Einstieg ALLEIN sagt die Liquidationsgefahr je "
              "Stufe voraus - die Risikokurven bringen nichts dazu; 5x vorwaerts "
              "kalibriert, 3x nur geordnet, 2x zu selten. Die Tabelle liegt vor, "
              "die Grenze ist eine Nutzerentscheidung - erst nach H0 (Pruefung auf "
              "der Einstiegsauswahl)"),
    ("2.682", "K5 NEU: Tor nicht bestanden - kein Urteil. In der Kombination "
              "bestimmt rsi die Auswahl, eine Wirkung der Lage wird verdeckt. Die "
              "Lage muss ZUERST fuer sich als Beitrag gemessen werden, mit eigenem "
              "Tor; K5 bleibt neu vorzulegen"),
    ("2.683", "K5-FOLGE: rsi allein ist zeitstabil (jedes Jahr, auch 2022, jedes "
              "Normal-Drittel) und roh fast kalibriert; das Phase-Normal ist "
              "groesstenteils Rauschen, seine Schrumpfung behebt die Rueckkehr zur "
              "Mitte. Die Lage hat einzeln klare Kurven, in der Kombination kommt "
              "nichts an (Tor nicht bestanden) - sie ist FUER SICH zu messen"),
    ("2.684", "GEGENPRUEFUNG: der rsi-Effekt ist keine Verzerrung des Normals (haelt "
              "gegen das geschrumpfte, Verzerrungsanteil ~0), aber 2024 ist schwach "
              "und zeitstabil nur in der Betriebsform. rsi ist ein Fortsetzungs-"
              "Beitrag, kein Kandidat fuer das OPTIMUM"),
    ("weiter", "Markt-Massstab 2024 bis 2026. DIE ROLLEN (25.09., am 29.09. geprueft, "
               "Einordnung_Beitraege_29_09.md): A Richtung entscheidet OB (Signal), B "
               "Bewegungserwartung WIE WEIT (Potential), C Risikosperre mit der ATR WIE "
               "VIEL HEBEL - keine Summe, kein Blocker. A WAEHREND (Fortsetzung) ist mit "
               "rsi belegt und ein eigener Einstiegstyp (die Positionsfuehrung "
               "entscheidet); A VORHER (OPTIMUM) hat nur Kandidaten (funding negativ, "
               "wenige Longs) - weitgehend schon gemessen (2.650, 2.657, 2.665). B ist "
               "robust (2.655/2.662), in ATR groesstenteils die ATR. Bewertung 2: die "
               "ATR (2.681). Naechste Schritte: K6 R+S (Extreme der Lage), K5 neu "
               "vorlegen, H0, Simulation Ebene 3 und neue Monate ab 2026-09. Black "
               "Swans nur als Stoerfaktor (Nutzer 29.09.)"),
)

# ⭐ WELCHES MESSSKRIPT WELCHE MERKMALE AUF WELCHER BEWERTUNG GEMESSEN HAT.
# Die Merkmalsliste wird aus dem QUELLTEXT gelesen (AST, kein Import) -
# die Wache kann damit nicht hinter eine neue Messung zurueckfallen.
# ⚠️ Das Skript muss im Quellenfeld des Befundes stehen; sonst bricht die
# Wache ab (der Eintrag hier waere dann erfunden).
MESSUNGEN_NEUBAU = {
    "2.663": ("messe_traeger_auf_bewertung1.py", "GRUPPEN", "b1"),
    "2.650": ("messe_lage_vor_der_bewegung.py", "NAMEN", "b1"),
}
KONTROLLMERKMALE = ("zufall",)


def gemessene_merkmale() -> dict:
    """-> {befund: (bewertung, {merkmal, ...})} aus dem Quelltext, OHNE Import.

    ⚠️ Fehlt ein Skript oder die Variable, wird abgebrochen - eine leere
    Menge saehe aus wie *nichts gemessen*, und genau diesen Fehler
    beseitigt dieses Paket.
    """
    import ast
    import io as _io
    import os as _os

    aus = {}
    hier = _os.path.dirname(_os.path.abspath(__file__))
    for befund, (skript, variable, bewertung) in MESSUNGEN_NEUBAU.items():
        baum = ast.parse(_io.open(_os.path.join(hier, skript),
                                  encoding="utf-8").read())
        wert = None
        for k in ast.walk(baum):
            if (isinstance(k, ast.Assign) and len(k.targets) == 1
                    and getattr(k.targets[0], "id", "") == variable):
                wert = ast.literal_eval(k.value)
                break
        if wert is None:
            raise RuntimeError("%s: `%s` nicht gefunden in %s"
                               % (befund, variable, skript))
        namen = ([n for g in wert.values() for n in g]
                 if isinstance(wert, dict) else list(wert))
        aus[befund] = (bewertung, {n for n in namen
                                   if n not in KONTROLLMERKMALE})
    return aus


# ⭐ DIE NAECHSTEN MESSUNGEN, in dieser Reihenfolge.
#   art "probe"    prueft einen Vorbehalt an einem geltenden Befund (R-R11:
#                  erst reproduzieren, dann die vorgriffsfreie Form)
#   art "vorlauf"  dieselben Traeger auf laengeren Fenstern - die ACHSE
#   art "neu"      ein Merkmal auf einer Bewertung, auf der es NIE
#                  gemessen wurde
# ⚠️ Der Laderfix 2.611 ist keine Messung und steht unter OFFENE_AUFGABEN.
# ⚠️ 28.09. abends: die Probe ALTERSACHSE ist gelaufen (2.676) - gueltig,
# keine Umkehr, der 24 h alte Wert traegt in jedem Zeitraum; sie ist hier
# gestrichen. Naechster Schritt ist K1 Schritt 2 (im Hauptplan).
# ⚠️ 28.09. nachgezogen: die Probe *funding gegen die Phase* (2.666) ist
# durch K1 beantwortet (2.673, 2.675) - der Asset-Anteil traegt nicht, der
# Marktanteil am unteren Rand nur in der Suche. Neu: die Altersachse von
# *oben gestreckt*, und die Bestaetigung der Suche-Raender in ungesehener
# Zeit. Danach K1 Schritt 2 (gemeinsame Schaetzung) - eine Kombination,
# kein Merkmal, deshalb nicht in dieser Liste, sondern im Hauptplan.
NAECHSTE_MESSUNGEN = (
    dict(was="Die Suche-Raender in UNGESEHENER Zeit bestaetigen",
         art="probe", bewertung="b1",
         merkmale=("funding", "konten_verh", "oi_aenderung", "ema_abstand_atr"),
         prueft="2.676",
         warum="funding_markt und konten_verh_markt unten stehen nur in der "
               "Suche (Pruefzeit und 2022 im Marktrauschen), oi_aenderung "
               "unten nur auf dem Versatz, ema_abstand oben kehrt 2022 mit dem "
               "aktuellen Wert (mit 24 h Alter nicht). Mehr Pruefzeit gibt es nicht - die "
               "Bestaetigung kommt aus der Simulation (Ebene 3) auf "
               "ungesehenen Monaten, mit der Marktstreuung als Massstab"),
    dict(was="Vorlauf bei H72 und H120",
         art="vorlauf", bewertung="b1",
         merkmale=("funding", "oi_aenderung", "konten_verh"),
         warum="die Haltequote steigt mit dem Fenster (0,43 bei H6, 0,66 "
               "bei H24, Vortag) - erreicht sie 0,8? Teil 0 von 2.651 kennt die "
               "brauchbaren Ziele schon (+20 %/H72, +30 %/H72, +30 %/H120). "
               "`funding` in der Form, die die Probe ergibt"),
    dict(was="K6 H0: die Liquidationsgefahr der ATR-Stufen auf der tatsaechlichen "
             "EINSTIEGSAUSWAHL (Pflicht vor jeder Verwendung)",
         art="probe", bewertung="b2", merkmale=("atr",), prueft="2.681",
         warum="K6 hat auf ALLEN Ankern gemessen; der Einstieg waehlt besondere "
               "Zeitpunkte (Fortsetzung, Squeeze-Lage) - stehende Regel *unbedingte "
               "Messung nicht auf eine Teilmenge uebertragen*. Braucht die "
               "Einstiegsregel (K5)"),
    dict(was="rsi (Rolle A waehrend) auf UNGESEHENEN Monaten und 2024 - traegt die "
             "Fortsetzung ueber die Zeit?",
         art="probe", bewertung="b1", merkmale=("rsi",), prueft="2.684",
         warum="2024 ist schwach, zeitstabil nur in der Betriebsform (2.684); die "
               "Pruefzeit ist mehrfach gesehen - die Antwort kommt aus der "
               "Simulation (Ebene 3) und den Monaten ab 2026-09 (Z6)"),
    dict(was="K6 R+S: die EXTREME der Lage (funding hoch, viele Longs) als "
             "Risikogewicht der Hebelstufe - Black Swans nur als Stoerfaktor",
         art="neu", bewertung="b2",
         merkmale=("funding", "oi_aenderung", "konten_verh"),
         warum="Bewertung 2 traegt heute nur die ATR (2.681); die ATR misst die "
               "Schwankung, nicht wie EINSEITIG der Markt gehebelt ist. Kurven "
               "(2.683) und Recherche (hoher Carry -> Crash) zeigen in diese "
               "Richtung; die drei Risikokurven aus K6 trugen nichts dazu, die "
               "Erwartung ist bescheiden. Der 10./11.10. nur mit/ohne (Nutzer: "
               "*Black Swans haben keine Moeglichkeit der Messung*)"),
)

# ⛔ UND WAS NICHT MEHR GEMESSEN WIRD: weitere Kursmerkmale aus der
# EMA/RSI/ATR-Familie. Drei unabhaengige Messungen (2.578, 2.645, 2.650)
# sagen dasselbe - dort ist nichts.

# ══ ⭐⭐⭐ WAS *OPTIMUM* HEISST - die Zieldefinition ═════════════════
#
# NUTZERDEFINITION 27.09.2026, woertlich:
#
#   *"OPTIMUM ist: wir kennen die Bewertungen und die LAGE VOR DER
#   BEWEGUNG. Das ist das Ziel, und ist fuer mich auch eine
#   Wahrscheinlichkeit. Die Bewertung eines BEREITS GESTIEGENEN Assets
#   ist weder das Ziel noch ist es ein Optimum - dazu brauche ich kein
#   System, das sehe ich am Kurs, und dann steige ich ein und RATE, ob er
#   noch weiter steigt."*
#
# ⛔⛔ DAS DISQUALIFIZIERT MEINEN EIGENEN BEFUND VON HEUTE ALS
# EINSTIEGSSIGNAL - nicht als Messung, sondern als ZWECK. 2.648 hat
# `momentum_kurz >= 0,8509` gemessen, und das heisst woertlich *in den
# letzten 6 Stunden stark gestiegen*. Der Lift 6,931 auf *+15 Prozent in
# den NAECHSTEN 6 Stunden* misst damit zu einem guten Teil die
# FORTSETZUNG einer laufenden Bewegung.
#
# ⚠️ Der Befund BLEIBT - er ist gemessen und geprueft. Was sich aendert,
# ist seine ROLLE: er beantwortet *wo ist eine Bewegung wahrscheinlich*,
# nicht *wo ist noch etwas uebrig*.
#
# ➤ DIE UNTERSCHEIDUNG, DIE AB JETZT GILT:
#
#     WAHRSCHEINLICHKEIT   wo kommt am ehesten ein Anstieg?
#                          -> auch mitten in der Bewegung. KEIN Optimum
#     OPTIMUM              wo ist am meisten UEBRIG?
#                          -> VOR der Bewegung. Das ist das Ziel
#
# ⚠️⚠️ DAS AUSSCHLUSSKRITERIUM, und es ist hart: ein Merkmal, das die
# BEWEGUNG SELBST misst, ist kein Einstiegssignal. Wer erst kauft, wenn
# der Kurs schon gestiegen ist, braucht dafuer kein System.
OPTIMUM = {
    "ist": "die Lage und Bewertung VOR der Bewegung - eine "
           "Wahrscheinlichkeit dafuer, dass eine Bewegung BEGINNT",
    "ist_nicht": "die Bewertung eines bereits gestiegenen Assets - das "
                 "sieht man am Kurs, und der Einstieg dort ist Raten",
    "ausschluss": "ein Merkmal, das die BEWEGUNG SELBST misst, ist kein "
                  "Einstiegssignal (betrifft momentum_kurz und rsi aus "
                  "2.648 in ihrer heutigen Form)",
    "pruefform": "KARENZ - die Lage bei t, das Ereignis erst ab t+k. "
                 "Bricht der Lift mit wachsendem k ein, war er "
                 "Fortsetzung; haelt er, war die Lage VORHER erkennbar",
    "zweite_achse": "VORLAUF - wie weit ist das Asset in den letzten "
                    "Stunden schon gelaufen? Nutzerbeispiel: *wenn das "
                    "Asset bereits 50 Prozent gestiegen ist, ist das "
                    "Risiko einer Korrektur eher gegeben*",
}

# ══ ⛔⛔⛔ WAS ENDGUELTIG TOT IST ════════════════════════════════════
#
# NUTZERFESTLEGUNG 27.09.2026, woertlich: *"Zur Sicherheit: SPOT = HEBEL
# ist TOT fuer IMMER und EWIG. Das Geruest von 22.08.26 ist ueberholt.
# Bauformen 30.08. Optionen, aber keine Gueltigkeit."*
#
# ⚠️ Das ist keine Einordnung, sondern eine Anweisung - und sie schliesst
# genau die drei Tueren, durch die ich immer wieder zurueckgekommen bin.
TOT = {
    "spot_gleich_hebel": (
        "SPOT = HEBEL",
        "TOT fuer immer und ewig. Die beiden Arme sind nicht dieselbe "
        "Frage - nicht rechnerisch, nicht fachlich. Die EINZIGE "
        "Gemeinsamkeit ist der Pruefzeitpunkt"),
    "geruest_22_08": (
        "`agent/wahrscheinlichkeit.rechne` - Basisrate + Beitraege = "
        "Quote, Abstand = Quote - Breakeven (22.08.2026)",
        "UEBERHOLT. Vier Stellen kollidieren mit den Festlegungen vom "
        "27.09.: die Basisrate 1/(1+CRV) kommt aus der GEOMETRIE und ist "
        "zugleich die Kelly-Nullstelle (2.634); der Breakeven enthaelt "
        "GEBUEHREN (Regel 2); `stufen` je Fuenftel ist ein "
        "QUERSCHNITTSRANG (2.649); und `Quote` setzt Barrieren voraus, "
        "also wieder Geometrie"),
    "bauformen_30_08": (
        "SCHALTER und ABGESTUFT (G-2' Schritt 2b, 30.08.2026)",
        "OPTIONEN, aber KEINE GUELTIGKEIT. Sie duerfen erwogen werden; "
        "gesetzt ist keine von beiden. Und die Stufengrundlage *Fuenftel* "
        "faellt ohnehin mit 2.649"),
}

# ⭐ WAS AUS DEM ALTEN GERUEST TROTZDEM UEBERTRAGBAR IST - und das ist
# kein Widerspruch zu TOT, sondern die Unterscheidung zwischen einer
# RECHNUNG (tot) und einer BUCHFUEHRUNG (brauchbar):
UEBERTRAGBAR = {
    "registrierung": "jeder Beitrag ist ein Eintrag mit Wert, Zustand, "
                     "Quelle und Begruendung - ein neuer Beitrag ist EINE "
                     "Zeile, kein Umbau der Rechnung",
    "fuenf_zustaende": "traegt / enthalten / null / noch_nicht / nie, plus "
                       "`luecke` additiv. Sie loesen die Frage *wurde hier "
                       "gemessen oder war nur nichts da* - im Neubau "
                       "unveraendert noetig",
    "additiv_belegt": "die additive Verrechnung ist durch 2.302 BELEGT "
                      "(turnover unabhaengig von funding), nicht "
                      "angenommen - das Verfahren bleibt pruefbar",
}

# ══ ⚠️⚠️⚠️ EIN HINWEIS IST KEINE UMSTURZANWEISUNG ═══════════════════
#
# NUTZERMAHNUNG 27.09.2026, woertlich: *"bitte wirf nicht alle bisherigen
# Festlegungen weg, und meine Aussagen sind oft NUR TEXT."*
#
# ⛔ MEIN MUSTER, an einem Tag mehrfach: auf einen Hinweis hin eine
# ganze Befundlage in Frage stellen, statt den Hinweis EINZUORDNEN.
#
# ⭐ DER FALL, DER ES AUSGELOEST HAT - und er ist lehrreich, weil ich
# fast das Gegenteil des Richtigen geschlossen haette: die Messung vom
# 27.09. zeigt, dass `ema_abstand_atr <= -1,0` ABSTUERZE staerker
# vorhersagt als Anstiege (Lift 6,71 nach unten gegen 2,67 nach oben).
# Ich war dabei, daraus eine Abwertung zu machen.
#
# ⛔ FALSCH. `ema_abstand_atr` IST Rolle C, die RISIKOSPERRE (2.642,
# 2.643). Dass sie Abstuerze anzeigt, ist GENAU IHRE AUFGABE. Die
# Messung BESTAETIGT sie auf einer voellig anderen Zielgroesse - sie
# widerlegt nichts. 2.647 bleibt unveraendert.
#
# ➤ DIE PRUEFFRAGE VOR JEDEM WIDERRUF:
#     1.  Widerspricht der neue Befund dem alten wirklich - oder
#         beantwortet er eine ANDERE Frage?
#     2.  Ist der Hinweis eine ANWEISUNG oder eine EINORDNUNG?
#     3.  R-R11: habe ich den alten Befund erst REPRODUZIERT?

# ══ DIE HEBELSTUFEN - vom Nutzer festgelegt, nicht gemessen ═════════
#
# ⚠️⚠️ NUTZERFESTLEGUNG 27.09.2026: *"festgelegt ist aktuell 2x 3x und 5x
# als Hoehe, das Chance-Risiko-Verhaeltnis kommt aus den MESSUNGEN."*
#
# ➤ Die STUFEN sind gesetzt (Risikoappetit - Nutzerentscheidung, siehe
#   `Entscheidungen_Hebelneubau.md`, "Die Grenze"). Was GEMESSEN wird,
#   ist die ZUORDNUNG: welche Lage bekommt welche Stufe.
HEBELSTUFEN = (2, 3, 5)

# ✔ GEKLAERT 27.09.2026 auf Nachfrage: *"2x 3x 5x entspricht den aktuell
# HANDELBAREN Stufen, damit kannst du dann 4x weglassen."* Es ist also
# keine Messfrage, sondern eine Eigenschaft der Boerse.
#
# ⚠️ Der frueher genannte Wert bleibt als Vergleich stehen - der
# abgeloeste Befund 2.632 hiess *vier Hebelstufen 2x/3x/4x/5x tragen*,
# und wer ihn liest, muss sehen, warum dort vier stehen.
HEBELSTUFEN_FRUEHER = (2, 3, 4, 5)
HEBELSTUFEN_GRUND = ("aktuell HANDELBARE Stufen (Nutzerauskunft 27.09.) - "
                     "keine Messfrage, sondern eine Eigenschaft der Boerse")

# ══ DIE ZWEI ZEITPUNKTE - und was an jedem gilt ═════════════════════
#
# ⚠️⚠️⚠️ NUTZERBEISPIEL 27.09.2026, woertlich: *"Annahme Hebel
# funktioniert im System - 1. Neutrale Bewertung und Hebelhoehe bei
# Pruefung, Ablaufkette, eMail. 2. ich sehe die Empfehlung, mache eine
# Position auf UND DANN kommt eine NEUE Hebelposition ins Spiel, wo
# wieder alle Parameter wie Stop etc. relevant sind."*
#
# ⭐ Und die Praezisierung dazu: *"Trailing ist NICHT FALSCH, sondern
# nicht korrekt eingeordnet - diese kommt bei der Positionsfuehrung ins
# Spiel. Dort sind wir noch nicht (Hauptplan)."*
#
# ⚠️ Das ist ein Unterschied, den ich vorher nicht gefuehrt habe: es sind
# ZWEI Zeitpunkte mit verschiedenen Groessen, nicht eine Bewertung, die
# alles auf einmal entscheidet.
ZEITPUNKTE = {
    "T1_bewertung": (
        "Pruefzeitpunkt - die Empfehlung entsteht",
        ["Einstieg: GUT oder SEHR GUT - der OPTIMALE Einstieg ist zu "
         "MESSEN, daraus ergeben sich die Bewertungen",
         "Hebelhoehe: die Stufen sind gesetzt (2x/3x/5x), die ZUORDNUNG "
         "wird gemessen und kalibriert - Chance-Risiko aus den Messungen",
         "dann weiter in der Kette wie heute -> Mail"],
        "NEUTRAL: kein Kapital, keine Positionsgroesse, kein Ergebnis, "
        "KEINE Geometrie. Es gibt noch keine Position, also auch keinen "
        "Stop und kein Trailing"),
    "T2_positionsfuehrung": (
        "nach der Eroeffnung - eine NEUE Hebelposition existiert",
        ["Stop", "Trailing", "Ausstieg", "Nachfuehrung"],
        "HIER sind alle diese Parameter relevant und richtig. Phase 5 "
        "des Hauptplans - dort sind wir noch nicht"),
}

# ⚠️⚠️ WAS DARAUS FUER DAS TRAILING FOLGT - und es ist NICHT "falsch":
#
#   in T1    hat es nichts zu suchen. Es gibt keine Position
#   in T2    ist es die richtige Groesse - Positionsfuehrung
#   im MESSEN  ist es ein WERKZEUG: um zu pruefen, ob eine Lage traegt,
#              muss ein Ausgang definiert sein. Das ist Ebene B und
#              sagt nichts darueber, wo es im BETRIEB steht
#
# ➤ Mein Fehler war die EINORDNUNG, nicht die Verwendung: ich habe die
#   Messanordnung als Systemeigenschaft gefuehrt und daraus geschlossen,
#   der Hebel "sei" H24 mit Trailing.

# ══ DIE GEOMETRIE - MESSWERKZEUG, nicht Systemeigenschaft ═══════════
#
# ⚠️⚠️⚠️ NUTZERVORGABE 27.09.2026: *"hierbei ist die GEOMETRIE des Hebels
# bei der BEWERTUNG nicht direkt relevant, sondern wird durch CHANCE und
# RISIKO gesteuert"* und *"Trailing ist SPAETER zur Positionsfuehrung"*.
#
# ⛔ Dieses Modul hat die Geometrie bis zum 27.09. als *die Geometrie des
# Neubaus* gefuehrt, ganz oben, als waere sie eine Eigenschaft des
# Systems. Sie ist es nicht: sie ist die ANORDNUNG, mit der gemessen
# wird - Modus `messen`, Ebene B. In die Bewertung geht sie NICHT ein,
# und das Trailing gehoert in Phase 5.
#
# ⚠️ Sie bleibt trotzdem stehen, weil eine Messung ohne Anordnung nicht
# geht - aber sie steht jetzt dort, wo sie hingehoert.
#
# ⚠️⚠️ SIE IST NICHT DIE DES SPOT-ARMS, UND DAS IST DER GANZE PUNKT. Der
# Spot-Arm misst auf H20 gegen `bewegung_r` mit fixen Barrieren. Hier
# gilt H24 mit einem TRAILING-Stop - und der Unterschied ist nicht
# kosmetisch: bei `ema_abstand_atr` hat genau er die Deutung gedreht
# (MFE/MAE sagte "kontraindiziert", der Ertrag unter Trailing sagte
# 84-facher Markt, 2.647). Eine Groesse, die auf der Spot-Geometrie
# gemessen wurde, sagt hier NICHTS - auch wenn sie denselben Namen traegt.
GEOMETRIE = {
    "fenster_stunden": 24,      # 2.642, Standard nachgezogen in 2.646
    "stop_atr": 1.00,           # 2.628
    "trailing_ausloeser_r": 1.5,
    "trailing_abstand_r": 0.5,
    "zielgroesse": "E[R]",      # 2.644 - ordnet 138 % schaerfer als MFE/MAE
    "messbasis": "data/stundenkurse.db, 115 Symbole ohne BTC, "
                 "3,19 Mio Anker, 01.12.2021 bis 24.09.2026",
}

# ══ DIE KANDIDATEN je Rolle ═════════════════════════════════════════
#
# Die Staende, und was sie bedeuten:
#
#   belegt        auf der NEUBAU-Geometrie gemessen und durch alle sechs
#                 Pruefungen (Nullwelt, Zeitstabilitaet, Weglassprobe,
#                 Mehrfachtesten, Ebene, je Asset)
#   teilbelegt    eine Eigenschaft ist belegt, aber NICHT auf dieser
#                 Geometrie - der Befund traegt hier noch nicht
#   faellt        auf dieser Geometrie gemessen und durchgefallen
#   offen         nie gemessen
#
# ⚠️ `teilbelegt` ist die wichtigste Stufe: sie verhindert, dass ein
# Befund von der einen Geometrie stillschweigend auf die andere wandert.
# Genau das ist am 27.09. zweimal passiert.
KANDIDATEN = {
    "A": [
        # WAEHREND - Fortsetzung, gemessen
        ("rsi", "belegt", "2.675/2.683/2.684",
         "WAEHREND (Fortsetzung): RSI der letzten 14 h, traegt je Asset auf q5 "
         "gegen die Phase; keine Normal-Verzerrung, roh fast kalibriert, 2024 "
         "schwach. Karenz 0,43 (2.650) - sagt nicht VORHER"),
        ("momentum_kurz", "belegt", "2.675/2.680",
         "WAEHREND (Fortsetzung): dieselbe Familie wie rsi (+0,62), schwaecher - "
         "nicht zusaetzlich zaehlen. Karenz 0,31 (2.650)"),
        # VORHER - Kandidaten, kein Nachweis in ungesehener Zeit
        ("funding", "kandidat", "2.663/2.665/2.675/2.683",
         "VORHER-Kandidat: negativ = Shorts zahlen (Spiegel 1,10, Kurve +0,11); "
         "einzige 'Lage vorher' in 2.665, aber klein und nur in der Suche (2.675)"),
        ("konten_verh", "kandidat", "2.663/2.655/2.675/2.683",
         "VORHER-Kandidat: wenige Longs (Spiegel 1,18, Kurve +0,15); vor allem "
         "Markt, nur in der Suche (2.675). ⛔ die Squeeze-Familie mit vola haelt "
         "2024 nicht (2.657)"),
        ("trendstruktur", "faellt", "2.645",
         "E[R] +0,00032, Tagesfehler +-0,00294 - Faktor 9 zu klein"),
        ("ema_lage", "faellt", "2.645", "E[R] +0,00037, nicht von null zu trennen"),
        ("ema_steigung", "faellt", "2.645", ""),
        ("rsi_aenderung", "faellt", "2.645", ""),
        ("rsi_umkehr", "faellt", "2.645",
         "mit rsi kombiniert nur 1 von 5 Jahren positiv"),
    ],
    "B": [
        ("vola_kausal", "belegt", "2.655/2.662/2.667",
         "HOEHE: P99 +6,56 Prozentpunkte mfe, vorwaerts in jeder BTC-Lage; in ATR "
         "ist es die ATR selbst (2.667) - die Hebelstufe gleicht das aus"),
        ("volumenschub", "belegt", "2.655/2.662/2.667",
         "HOEHE: P99 +1,82 mfe; traegt auch UEBER die ATR (+0,08 ATR, 30 von 32 "
         "Monaten)"),
        ("oi_je_umsatz", "belegt", "2.655/2.662",
         "HOEHE: tief = mehr Bewegung (P1 +2,18 mfe); in ATR nicht mehr (2.667)"),
        ("oi_aenderung", "belegt", "2.655/2.662/2.667",
         "HOEHE, reine Bewegung (Spiegel 1,02-1,07): stark = mehr (P99 +3,23); "
         "tief = weniger - in Prozent NICHT tragend (2.662), in ATR -0,16 (2.667)"),
        ("bandenge", "offen", "",
         "Squeeze. ⚠️ In 2.645 lief es MIT, aber gegen `E[R]` - das ist die "
         "A-Frage. Die B-Testform ist die AUFLOESUNGSRATE (kommt ueberhaupt "
         "etwas?), und die ist RICHTUNGSLOS. So ist es nie gemessen worden"),
    ],
    "C": [
        ("ema_abstand_atr", "belegt", "2.642/2.647",
         "RISIKOSPERRE: d 0,521 auf MAE gegen 0,267 auf MFE (2.642). Traegt "
         "absolut (84-facher Markt) UND je Asset (99,1 % des Lifts bleiben "
         "symbolintern), alle sechs Pruefungen (2.647). ⚠ fuer die LIQUIDATION "
         "kein Mehrwert ueber die ATR (2.681) - wirkt ueber Bewertung 2"),
        ("funding", "kandidat", "2.655/2.663/2.683",
         "Extrem HOCH: Spiegel 0,85, >= 0,0016 zeigt nach unten, Kurve -0,10; "
         "Recherche: hoher Carry sagt Crashs voraus (BIS) - ungemessen gegen die "
         "Liquidation (K6 R+S)"),
        ("konten_verh", "kandidat", "2.655/2.683",
         "Extrem viele Longs: Spiegel 0,63, Kurve -0,25 - ungemessen gegen die "
         "Liquidation (K6 R+S)"),
    ],
}

# ══ DER HAUPTPLAN - dieses Modul ersetzt ihn NICHT ══════════════════
#
# ⚠️⚠️⚠️ NUTZERKRITIK 27.09.2026: *"wir haben einen HAUPTPLAN - was ist
# mit diesem? wenn du wieder etwas NEUES PARALLEL machst, bringt das
# nichts."*
#
# ⛔ Sie trifft. Ich war dabei, hier ein ZWEITES Planungsdokument
# aufzubauen - Rollen, offene Punkte, Stand -, waehrend der Hauptplan
# dasselbe fuehrt. Zwei Listen laufen immer auseinander, und dann weiss
# niemand mehr, welche gilt. Genau daran ist am 06.09. schon einmal eine
# Messung auf der falschen Basis gelaufen (die Register entstanden daraus).
#
# ➤ DIE AUFTEILUNG, DIE STATTDESSEN GILT:
#
#     Der HAUPTPLAN     fuehrt die PHASEN, die Reihenfolge und die
#                       Entscheidungen. Er ist das Dokument fuer den
#                       Nutzer und bleibt die oberste Liste.
#     Dieses MODUL      fuehrt den FAKTENTEIL - welche Rolle steht wo,
#                       auf welcher Geometrie, mit welchem Befund. Also
#                       genau das, was ich nicht aus dem Kopf schreiben
#                       darf, ohne zu vermischen.
#
# ⚠️ Und damit sie nicht auseinanderlaufen, LIEST `stand()` die Phasen
# aus dem Hauptplan, statt sie zu kopieren. Fehlt er, bricht es ab.
HAUPTPLAN = "Basisinfos/Plan_Hebel_fuenf_Phasen_27_09.md"


def _phasen_aus_hauptplan() -> tuple:
    """-> (phasen, hier) aus dem Hauptplan gelesen, nicht kopiert.

    ⚠️ Kein stiller Rueckfall auf eine eingebaute Liste: fehlt der Plan
    oder aendert er sein Format, wird das GEMELDET. Eine Kopie, die
    stillschweigend einspringt, ist genau die zweite Liste, die hier
    vermieden werden soll.
    """
    import io as _io
    import os as _os
    import re as _re

    pfad = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)),
                         *HAUPTPLAN.split("/"))
    if not _os.path.exists(pfad):
        raise FileNotFoundError(HAUPTPLAN)
    text = _io.open(pfad, encoding="utf-8").read()
    phasen = []
    for zeile in text.split("\n"):
        # | **1** | **Grundlage** | *"..."* |
        m = _re.match(r"\|\s*\*\*(\d)\*\*\s*\|\s*\*\*([^|*]+)\*\*\s*\|",
                      zeile)
        if m:
            phasen.append((int(m.group(1)), m.group(2).strip()))
    m = _re.search(r"\*\*Wir sind in Phase (\d)\.?\*\*", text)
    hier = int(m.group(1)) if m else None
    if not phasen or hier is None:
        raise ValueError(
            "Hauptplan gelesen, aber Phasen (%d) oder 'Wir sind in Phase' "
            "(%s) nicht gefunden - Format geaendert?" % (len(phasen), hier))
    return phasen, hier


# ══ DIE EINBETTUNG - was BLEIBT und was ERSETZT wird ════════════════
#
# ⚠️⚠️⚠️ NUTZERPRAEZISIERUNG 27.09.2026, woertlich: *"der Umbau betrifft
# den HEBEL-ARM - aber die ABLAUFKETTE ALS GANZES ist weiterhin die
# AUSGANGSBASIS."*
#
# ⭐ Sie schliesst den UMGEKEHRTEN Fehler aus. Es gibt zwei, und beide
# habe ich gemacht:
#
#     1.  Den Spot-Arm hereinholen und seine Bewertung als "unsere"
#         ausgeben - dagegen steht `pruefe_quellen()`
#     2.  ⚠️ So tun, als faenge alles bei NULL an - und dabei
#         vergessen, dass der Hebel in einer bestehenden Kette laeuft,
#         die Symbole liefert, Zeitpunkte setzt und Mails schreibt
#
# ➤ NEU GEBAUT WIRD GENAU EINE SCHICHT: die BEWERTUNG des Hebels. Der
#   Rahmen darum bleibt und ist die Ausgangsbasis.
EINBETTUNG = {
    "bleibt": [
        ("Die Ablaufkette", "Symbolauswahl, Prueflauf, Reihenfolge der "
         "Stufen, Mailausgabe - sie ist der Rahmen und wird NICHT "
         "neu gebaut"),
        ("Der Pruefzeitpunkt", "Spot und Hebel werden zum SELBEN Zeitpunkt "
         "bewertet - ZWEI unterschiedliche Pruefungen, EIN Gewinner "
         "(E-8). Das ist laut Nutzervorgabe 27.09. die einzige "
         "Gemeinsamkeit der beiden Arme - und sie bleibt"),
        ("Die Datenquellen", "die Spot-Quellen sind NICHT irrelevant: sie "
         "wurden fuer H20 optimiert und vermessen. Nur ihre ANWENDUNG wird "
         "auf den Hebel dimensioniert - kurzer, intensiver Handel (E-8)"),
        ("Der Spot-Arm", "laeuft unveraendert weiter und fuehrt die offenen "
         "Positionen. In seiner HEUTIGEN Form (Code und Produktion) ist er "
         "fuer den Hebel TOT. Er wird selbst neu gebaut, wenn der Hebel in "
         "der ganzen Ablaufkette funktioniert (E-8)"),
        ("Die Betriebsbedingungen", "Takt, Cooldown, Kapazitaet, "
         "Aggregatdeckel - Ebene C (2.641). Sie gelten, gehoeren aber "
         "NICHT in die Bewertung"),
    ],
    "ersetzt": [
        ("Die Hebel-BEWERTUNG", "wie aus der Lage eine Hebelhoehe wird. "
         "Bisher: q -> Kelly -> r. Kuenftig: aus den drei Rollen, ohne "
         "jede Ertragsgroesse (2.641)"),
        ("Die Hebel-GEOMETRIE", "H24 mit Trailing statt H20 mit fixen "
         "Barrieren (2.628)"),
        ("Die Hebel-MERKMALE", "eigene Skala, eigene Messung - auch dort, "
         "wo der Spot-Arm dieselbe Rohgroesse verwendet (E-3)"),
    ],
}

# ══ WAS NOCH FEHLT, bevor der Neubau ein EINSTIEG ist ═══════════════
#
# ⚠️⚠️ Der Neubau hat HEUTE KEINE EINSTIEGSREGEL. Bewertung 1 hat Traeger
# beim sofortigen Einstieg (2.648, 2.651), aber keinen mit Vorlauf, und
# kalibriert ist nichts - die Zahlen leitet `stand()` aus BEITRAGSLAGE ab.
# Wer nach "dem aktuellen Hebel-Einstieg" fragt, bekommt
# deshalb DIESE Liste - und nicht die Spot-Kette aus agent/betraege.py.
OFFEN = [
    ("A auf dieser Geometrie", "momentum_kurz und rsi tragen RICHTUNG, "
     "aber gemessen auf einem Ereignis mit fixen Barrieren. Auf H24 mit "
     "Trailing sind sie ungemessen"),
    ("B ueberhaupt", "bandenge ist nie gegen die Aufloesungsrate gemessen "
     "worden - nur gegen E[R], und das ist die falsche Frage fuer B"),
    ("Die Anordnung", "A und B und NICHT C ist eine Testform. Wie daraus "
     "eine HEBELHOEHE wird, ist offen - E4 sagt Beitragssystem, nicht "
     "Blocksystem"),
    ("Die Hebelhoehe", "sie folgt dem RISIKO, nicht dem Ertrag (2.641). "
     "Woraus genau, ist nicht entschieden"),
]

# ══ DER RIEGEL ══════════════════════════════════════════════════════
#
# Alles hier drin gehoert zum SPOT-Arm und hat im Hebel-Neubau nichts zu
# suchen. Die Liste ist bewusst KONKRET - ein allgemeines "keine
# Spot-Sachen" haette mich nicht aufgehalten.
# ⚠️⚠️ KORRIGIERT 27.09. (E-3): der erste Riegel war ZU SCHARF. Er
# sperrte `terminmarkt` und `funding` komplett - und der Terminmarkt IST
# die Hebelboerse. Nutzerpraezisierung: *"die alten - damit meinte ich
# die Ergebnisse und Messungen der alten Regelwerke VOR dem Umbau. Spot
# und Hebel war vorher ein Ablauf; Hebel ist nun ganz anders gebaut, mit
# teilweise DENSELBEN Beitraegen."*
#
# ➤ Gesperrt sind die alten MESSWERTE (fertige Beitragsstufen aus H20 und
#   `bewegung_r`), NICHT die Rohgroessen. Eine Rohgroesse darf im Neubau
#   verwendet werden - sie muss nur NEU gemessen werden, auf der
#   Hebel-Lage.
SPOT_QUELLEN = {
    "funding_fuenftel": "ALTE Beitragsstufe (+0,82/+1,30/+0,12/-0,54/-1,70), "
                        "gemessen auf H20 und bewegung_r - die Spot-Lage. "
                        "Die ROHGROESSE `funding` ist frei",
    "turnover_fuenftel": "ALTE Beitragsstufe, gemessen auf der Spot-Lage. "
                         "Die Rohgroesse ist frei",
    "schnitt_fuenftel": "ALTE Beitragsstufe, zustand='null', seit 18.09. "
                        "ausgefallen (2.486-schnitt-tot)",
}

# ⚠️ Kelly ist KEINE Spot-Quelle, aber die Formel, mit der ich zweimal
# die Bewertung aus dem ERTRAG abgeleitet habe (2.641). Sie gehoert in
# die Erfolgsmessung, nie in die Bewertung.
# ⚠️ PRAEZISIERT 27.09. (E-2, Befund 2.644): `E[R]` ist als ZIELGROESSE
# einer Messung erlaubt und sogar die beste Wahl (d 0,402 gegen 0,168 bei
# MFE/MAE). Verboten ist es als EINGANG der Bewertung im Betrieb. Der
# verbotene Fall war die RUECKWAERTSOPTIMIERUNG - eine Schwelle aus der
# Kelly-Nullstelle ableiten.
ERTRAGSGROESSEN = {
    "kelly": "als BEWERTUNGSEINGANG verboten (2.641): aus q und CRV, also "
             "rueckwaerts aus Ertraegen. Als Kennzahl einer Messung "
             "unproblematisch",
    "hebelrechnung": "agent/betraege.py - rechnet die Spot-Quote in einen "
                     "Hebel um; der Neubau ersetzt genau diese Kette",
    "bewegung_r": "ALTE Spot-Zielgroesse (H20) - fuer den Hebel gilt E[R] "
                  "auf der Hebel-Lage (2.644)",
}


# ⚠️⚠️ DIE QUERSCHNITTSGROESSEN - gesperrt seit der Nutzerentscheidung
# vom 26.09. (2.608-2.610, siehe AUSWAHLEBENE oben). Sie sind Aussagen
# ueber die MENGE, nicht ueber das ASSET.
QUERSCHNITT = {
    "taeglich_beste": "waehlt je Tag die besten k Prozent - ein "
                      "Querschnittsrang. 2.626 und 2.628 stehen darauf, "
                      "und beide widersprechen der Nutzerentscheidung vom "
                      "SELBEN Tag. Die Bewertung ist eine ABSOLUTE "
                      "Schwelle in ATR",
    "perzentil_je_stunde": "dasselbe auf Stundenebene",
    "rangplatz": "ein Rang haengt an der Grundgesamtheit - dieselbe Lage "
                 "bekaeme bei 116 Symbolen ein anderes Urteil als bei 28",
    "querschnittsrang": "Sammelbegriff - siehe AUSWAHLEBENE",
}


class SpotVermischung(RuntimeError):
    """Eine Hebel-Neubaumessung hat eine Spot- oder Querschnittsgroesse
    angefasst."""


def pruefe_quellen(*namen: str, erlaubt: tuple = ()) -> None:
    """ABBRUCH, wenn eine Spot- oder Ertragsgroesse im Hebel-Neubau auftaucht.

    ⚠️ Bewusst ein Abbruch und keine Warnung: eine Warnung haette ich
    dreimal ueberlesen. Wer eine Groesse WIRKLICH braucht, nennt sie in
    `erlaubt` - dann steht die Ausnahme im Aufruf und ist beim Lesen
    sichtbar, statt sich in einem Vorgabewert zu verstecken.

    >>> pruefe_quellen("ema_abstand_atr")           # geht durch
    >>> pruefe_quellen("funding_fuenftel")          # bricht ab
    Traceback (most recent call last):
    hebel_neubau.SpotVermischung: ...
    """
    schlecht = []
    for n in namen:
        k = str(n).strip().lower()
        if k in erlaubt:
            continue
        if k in SPOT_QUELLEN:
            schlecht.append("%s -> %s" % (n, SPOT_QUELLEN[k]))
        elif k in ERTRAGSGROESSEN:
            schlecht.append("%s -> %s" % (n, ERTRAGSGROESSEN[k]))
        elif k in QUERSCHNITT:
            schlecht.append("%s -> %s" % (n, QUERSCHNITT[k]))
    if schlecht:
        raise SpotVermischung(
            "HEBEL-NEUBAU: diese Groessen gehoeren zum SPOT-Arm oder sind "
            "Ertragsgroessen und haben hier nichts zu suchen:\n  "
            + "\n  ".join(schlecht)
            + "\n\nDer Hebel wird VOLLSTAENDIG NEU gebaut (Nutzervorgabe "
              "25.09.). Die einzige Gemeinsamkeit mit Spot ist der "
              "PRUEFZEITPUNKT.\nWird eine Groesse wirklich gebraucht, "
              "gehoert sie sichtbar in `erlaubt=(...)`.")


def rollenblatt() -> str:
    """Die drei Rollen und der Stand je Kandidat, in Klartext."""
    z = ["DER HEBEL-NEUBAU - drei Rollen, Anordnung A und B und NICHT C", ""]
    for r in ("A", "B", "C"):
        z.append("  %s  %s" % (r, ROLLEN[r]))
        for name, stand, _befund, hinweis in KANDIDATEN[r]:
            z.append("       %-18s %-12s %s" % (name, stand, hinweis[:56]))
        z.append("")
    return "\n".join(z)


# ══════════════════════════════════════════════════════════════════════
#  DER STAND - und warum er aus CODE kommt und nicht aus meinem Kopf
# ══════════════════════════════════════════════════════════════════════
#
# ⚠️⚠️⚠️ NUTZERKRITIK 27.09.2026, woertlich: *"JETZT explodiere ich
# gleich - wenn du noch einmal Spot und Hebelgeschaeft vermischst [...]
# du kannst nichts trennen und vermischst wieder Altes mit Neuem."*
#
# ⛔ DER AUSLOESER: auf die Frage *"zeige mir den aktuellen Hebel-Einstieg
# und die Bewertung"* habe ich `agent/betraege.py` vorgelegt - Kelly,
# Basisrate, `funding_fuenftel`, die Rollen-Kette. Also den ALTEN
# SPOT-ABLAUF, praesentiert als der Ist-Stand des Hebels.
#
# ⚠️⚠️ UND DAS SCHLIMMERE: der Riegel dagegen stand seit dem Vortag in
# DIESER Datei. `pruefe_quellen("funding_fuenftel")` bricht ab. Aber ein
# BERICHT ist kein Code - der Riegel bewacht Messskripte, nicht Prosa.
# Genau da bin ich durchgerutscht.
#
# ➤ DIE MASSNAHME: der Bericht WIRD Code. `stand()` kennt nur den Neubau.
#   Es liest die Befunde per AST aus `bestand.py`, ohne irgendetwas zu
#   importieren - es KANN also nicht in den Spot-Arm abdriften, auch
#   wenn ich es wollte.
#
# ⚠️⚠️ UND DER NACHWEIS IST EIN SEITENEFFEKT, KEINE TEXTSUCHE: nach einem
# Aufruf von `stand()` darf `sys.modules` kein `agent.*`, kein
# `marktrang`, kein `betraege` enthalten. Ein Textvergleich haette nur
# die Importzeilen geprueft und einen Import INNERHALB einer Funktion
# uebersehen - das ist die registrierte Regel *ein Test deckt die
# FUNKTION ab, nicht den PFAD*.

# ⚠️ 2.625 ist der erste Befund des Neubaus (25.09.) - und der Punkt ist
# ein TAUSENDERtrennzeichen, keine Gliederung. Die erste Fassung las
# `kopf.split(".")[1]` und bekam 625; gegen die Grenze 2625 fiel damit
# JEDER Befund heraus und das Blatt meldete "0 gelten". Ein Fehler, der
# sich selbst versteckt: eine leere Liste sieht aus wie ein Zustand.
NEUBAU_AB = 2625
NEUBAU_AB_TEXT = "2.625"

# ⚠️ Module, die es nach einem `stand()`-Aufruf NICHT geben darf. Der
# Spot-Arm plus alles, was ihn mitzieht.
VERBOTENE_MODULE = ("agent", "marktrang", "database", "scheduler", "ui")


def _befunde_ab(grenze: int = NEUBAU_AB) -> list:
    """-> [(kennung, stand, kopf)] fuer Befunde ab `grenze`, OHNE Import.

    ⚠️⚠️ Bewusst per AST statt `import bestand`. Zwei Gruende:

        1.  Ein Import zieht mit, was `bestand.py` heute oder morgen
            importiert - und damit faellt der Nachweis ueber `sys.modules`
            in sich zusammen. Er soll aber HART sein.
        2.  `bestand.py` ist eine Datendatei in Python-Form. Sie zu PARSEN
            statt auszufuehren ist auch sachlich das Richtige.

    ⚠️ Die Sortierung ist NUMERISCH nach der Nummer hinter dem Punkt,
    nicht alphabetisch - sonst stuende 2.647 vor 2.65.
    """
    import ast
    import io as _io
    import os as _os

    pfad = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)),
                         "bestand.py")
    baum = ast.parse(_io.open(pfad, encoding="utf-8").read())
    aus = []
    for k in ast.walk(baum):
        if not (isinstance(k, ast.Call)
                and getattr(k.func, "id", "") == "Befundlage"):
            continue
        teile = [a.value if isinstance(a, ast.Constant) else None
                 for a in k.args]
        if len(teile) < 3 or not isinstance(teile[0], str):
            continue
        kennung, aussage, zustand = teile[0], teile[1], teile[2]
        kopf = kennung.split("-")[0]
        # ⚠️ Der Punkt ist ein TAUSENDERtrennzeichen: "2.647" ist
        # zweitausendsechshundertsiebenundvierzig. Nur dieses Format
        # zaehlt; alles andere ist aelter als der Neubau.
        teil = kopf.split(".")
        if len(teil) != 2 or not teil[1].isdigit() or len(teil[1]) != 3:
            continue
        try:
            nr = int(kopf.replace(".", ""))
        except ValueError:
            continue
        if nr < grenze:
            continue
        aus.append((nr, kennung, zustand or "?",
                    (aussage or "").strip()))
    aus.sort(key=lambda x: (x[0], x[1]))
    return [(k, z, a) for _n, k, z, a in aus]


def _erster_satz(text: str, breite: int = 96) -> str:
    """Der Kern einer Befundaussage - bis zum ersten Punkt-Leerzeichen."""
    t = " ".join(str(text).split())
    for i in range(len(t) - 1):
        if t[i] == "." and t[i + 1] == " " and not t[max(0, i - 4):i].isdigit():
            t = t[:i]
            break
    return t if len(t) <= breite else t[:breite - 1].rstrip() + "…"


def stand(mit_befunden: bool = True) -> str:
    """Der VOLLSTAENDIGE Stand des Hebel-Neubaus - und nur dieser.

    ⚠️⚠️ DIES IST DIE QUELLE JEDES STATUSBERICHTS zum Hebel. Nicht mein
    Gedaechtnis, nicht eine Zusammenfassung, nicht `agent/betraege.py`.

    Was hier NICHT steht, gehoert nicht zum Neubau:
      - die Spot-Kette (`agent/rollen_lauf.py`, `agent/betraege.py`)
      - `q`, Kelly, Basisrate, die acht Spot-Beitraege
      - jeder Befund vor 2.625
    """
    L = []
    a = L.append
    a("=" * 98)
    a("DER HEBEL-NEUBAU - STAND")
    a("=" * 98)
    a("  Nutzervorgabe 25.09.2026: *wir bauen den Hebel-Arm VOLLSTAENDIG")
    a("  NEU. Wenn Hebel funktioniert, dann gehen wir zu den anderen*")
    a("  ⛔ Dieses Blatt kennt den Spot-Arm NICHT - mit Absicht.")
    a("")
    a("  ⭐⭐ NEU IN EINER SESSION? Zehn Fragen, zehn Antworten,")
    a("     jede mit dem Befehl zum Selbstpruefen:")
    a("     Basisinfos/UEBERGABE_Hebelneubau_27_09.md")
    a("")

    # ── Neuester Stand - VOR allem anderen, damit er nicht ueberlesen wird
    a("-" * 98)
    a("⚠️⚠️ NEUESTER STAND - er geht dem Rest dieses Blattes VOR")
    for befund, text in NEUESTER_STAND:
        zeilen = _umbruch(text, 86)
        a("  %-6s %s" % (befund, zeilen[0]))
        for z in zeilen[1:]:
            a("  %-6s %s" % ("", z))
    a("")

    # ── Der Hauptplan ────────────────────────────────────────────────
    a("-" * 98)
    a("DER HAUPTPLAN führt die Phasen - dieses Blatt nur den FAKTENTEIL")
    a("  %s" % HAUPTPLAN)
    a("")
    try:
        phasen, hier = _phasen_aus_hauptplan()
        for nr, titel in phasen:
            a("    %s %d  %s" % ("➤" if nr == hier else " ", nr, titel))
        a("")
        a("  ➤ WIR SIND IN PHASE %d. Alles unten gehoert dort hinein -" % hier)
        a("    es ist KEINE zweite Liste und keine Parallelplanung.")
    except Exception as e:
        a("  ⛔⛔ HAUPTPLAN NICHT LESBAR: %s" % e)
        a("     Kein Rueckfall auf eine eingebaute Kopie - eine zweite")
        a("     Liste ist genau das Problem, das hier vermieden wird.")
    a("")

    # ── Die Einbettung ───────────────────────────────────────────────
    a("-" * 98)
    a("DIE EINBETTUNG - der Umbau betrifft EINE SCHICHT, nicht alles")
    a("  Nutzervorgabe 27.09.: *der Umbau betrifft den Hebel-Arm - aber die")
    a("  ABLAUFKETTE ALS GANZES ist weiterhin die AUSGANGSBASIS*")
    a("")
    a("  ✔ BLEIBT - Rahmen, nicht Baustelle")
    for titel, text in EINBETTUNG["bleibt"]:
        a("      %-24s %s" % (titel, _umbruch(text, 62)[0]))
        for zeile in _umbruch(text, 62)[1:]:
            a("      %-24s %s" % ("", zeile))
    a("")
    a("  ⭐ WIRD ERSETZT - und nur das")
    for titel, text in EINBETTUNG["ersetzt"]:
        a("      %-24s %s" % (titel, _umbruch(text, 62)[0]))
        for zeile in _umbruch(text, 62)[1:]:
            a("      %-24s %s" % ("", zeile))
    a("")

    # ── Der Ablauf zum Pruefzeitpunkt ────────────────────────────────
    a("-" * 98)
    a("DER ABLAUF ZUM PRUEFZEITPUNKT - hintereinander, nicht in einem")
    a("  Nutzervorgabe 27.09.: *1. Einstieg GUT oder SEHR GUT")
    a("                         2. Hebelerzeugung (kalibrierte Bewertung)")
    a("                         3. dann weiter in der Kette wie heute*")
    a("")
    a("  ⚠️ NEUTRAL: kein Kapital, keine Positionsgroesse, kein Ergebnis.")
    a("  ⚠️ Das System arbeitet auf ASSETEBENE (Nutzervorgabe 27.09.).")
    a("")
    a("  Hebelstufen   %s  - vom Nutzer FESTGELEGT (Risikoappetit)"
      % " / ".join("%dx" % x for x in HEBELSTUFEN))
    a("  Gemessen wird die ZUORDNUNG: welche Lage bekommt welche Stufe.")
    a("  Das Chance-Risiko-Verhaeltnis kommt aus den MESSUNGEN.")
    a("  ✔ Grund: %s" % HEBELSTUFEN_GRUND)
    a("     (der abgeloeste 2.632 nennt vier Stufen - daher die Differenz)")
    a("")

    # ── Die drei Abdeckungen ─────────────────────────────────────────
    a("-" * 98)
    a("⚠️⚠️ DREI ABDECKUNGEN, DIE NICHT DASSELBE SIND")
    a("  Nutzerhinweis 27.09.: *wir sollten ueberall ca. 87 % Abdeckung")
    a("  mit Workaround haben* - und ich hatte `turnover` gerade mit")
    a("  *30 %, strukturell nicht zu retten* abgeschrieben. Beides stimmt.")
    a("")
    for schl, (was, zahlen) in ABDECKUNGEN.items():
        a("  %-10s %s" % (schl.upper(), was))
        for zeile in _umbruch(zahlen, 76):
            a("             %s" % zeile)
    a("")
    a("  ⛔ `turnover` hat 30 % ZEIT- und 97 % SYMBOLabdeckung. Fuer den")
    a("     BETRIEB zaehlt die zweite. Was fehlt, ist MESSHISTORIE.")
    a("")
    a("  ⚠️ OFFENE AUFGABEN:")
    for was, warum in OFFENE_AUFGABEN:
        a("      · %s" % was)
        for zeile in _umbruch(warum, 76):
            a("        %s" % zeile)
    a("")

    # ── Das Regelwerk ────────────────────────────────────────────────
    a("-" * 98)
    a("DAS REGELWERK - zwei Bewertungen, ZWEI ZIELGROESSEN")
    a("  Basisinfos/Regelwerk_Hebel_Bewertung_27_09.md")
    a("")
    a("  ⭐ EINSTIEG misst gegen die CHANCE, HEBEL gegen das RISIKO.")
    a("     Ein Merkmal kann in der einen tragen und in der anderen nicht.")
    a("")
    for schl in ("bewertung_1", "bewertung_2"):
        r = REGELWERK[schl]
        a("  %s  %s" % (schl.upper().replace("_", " "), r["name"]))
        a("      Frage        %s" % r["frage"])
        a("      Zielgroesse  %s" % r["zielgroesse"])
        a("      Bezug        %s" % r["bezug"])
        a("      Nullpunkt    %s" % r["nullpunkt"])
        a("      Ergebnis     %s" % r["ergebnis"])
        for i, zeile in enumerate(_umbruch(r["zusatzbedingung"], 62)):
            a("      %-12s %s" % ("Bedingung" if i == 0 else "", zeile))
        a("")

    # ── Wo welcher Beitrag zaehlt ────────────────────────────────────
    a("-" * 98)
    a("WO WELCHER BEITRAG ZAEHLT - der Stand, ehrlich")
    a("  ⛔ Nutzerkritik 27.09.: *Was ist mit turnover und funding, diese")
    a("     waren bereits gesetzt oder?* - An einem Tag zehn KURSmerkmale")
    a("     gemessen und die DREI registrierten Traeger nie geladen -")
    a("     nachgeholt in 2.651.")
    a("  ⭐ Bewertung 1 gilt bei k=0 (Betriebsfall); VORLAUF ist eine")
    a("     eigene Spalte, die Karenz ist eine ACHSE (2.650).")
    a("")
    a("  %-16s %-13s %-8s %-13s %s"
      % ("Merkmal", "Bewertung1", "Vorlauf", "Bewertung2", "Befund"))
    _mk = {"belegt": "✔✔ belegt", "ungemessen": "⬜ ungemessen",
           "faellt": "⛔ faellt", "spur": "⭐ spur"}
    for name, e in BEITRAGSLAGE.items():
        b1 = _mk.get(e["b1"], e["b1"]) + ("*" if e["vorbehalt"] else "")
        a("  %-16s %-13s %-8s %-13s %s"
          % (name, b1, e["vorlauf"] or "-", _mk.get(e["b2"], e["b2"]),
             ", ".join(e["befund"])))
        for zeile in _umbruch(e["beleg"], 76):
            a("  %-16s %s" % ("", zeile))
        if e["vorbehalt"]:
            for i, zeile in enumerate(_umbruch(e["vorbehalt"], 74)):
                a("  %-16s %s %s" % ("", "* " if i == 0 else "  ", zeile))
    a("")
    _tr1 = [n for n, e in BEITRAGSLAGE.items() if e["b1"] == "belegt"]
    _vl1 = [n for n in _tr1 if BEITRAGSLAGE[n]["vorlauf"] == "ja"]
    _vb1 = [n for n in _tr1 if BEITRAGSLAGE[n]["vorbehalt"]]
    _tr2 = [n for n, e in BEITRAGSLAGE.items() if e["b2"] == "belegt"]
    _off2 = [n for n, e in BEITRAGSLAGE.items()
             if e["b2"] in ("ungemessen", "spur")]
    a("  ➤ Bewertung 1 hat %d Traeger beim sofortigen Einstieg (%s)."
      % (len(_tr1), ", ".join(_tr1)))
    a("    ⚠️ davon mit VORLAUF: %s" % (", ".join(_vl1) or "KEINER"))
    if _vb1:
        a("    ⚠️ unter Vorbehalt (*): %s" % ", ".join(_vb1))
    a("  ➤ Bewertung 2 hat %d Traeger (%s)." % (len(_tr2), ", ".join(_tr2)))
    a("    ungemessen: %s" % ", ".join(_off2))
    a("")
    a("  QUELLEN - und ob sie LIVE beschaffbar sind (nicht: ob der heutige")
    a("  Betriebscode sie sammelt; der ist veraltet, Nutzer 27.09.)")
    _gesehen = set()
    for name, e in BEITRAGSLAGE.items():
        if (e["quelle"], e["live"]) in _gesehen:
            continue
        _gesehen.add((e["quelle"], e["live"]))
        _wer = [n for n, x in BEITRAGSLAGE.items()
                if (x["quelle"], x["live"]) == (e["quelle"], e["live"])]
        a("    · %s" % ", ".join(_wer))
        for zeile in _umbruch("Quelle: " + e["quelle"], 86):
            a("        %s" % zeile)
        for zeile in _umbruch("live:   " + e["live"], 86):
            a("        %s" % zeile)
    _sp = [(n, e["spot"]) for n, e in BEITRAGSLAGE.items() if e["spot"]]
    if _sp:
        a("")
        a("  SPOT-VERMESSUNG (E-8): fuer H20 optimiert und vermessen - nur")
        a("  die ANWENDUNG wird auf den Hebel dimensioniert")
        for n, t in _sp:
            a("    · %-14s %s" % (n, t))
    a("")
    a("  ⭐ DIE NAECHSTEN MESSUNGEN:")
    for i, m in enumerate(NAECHSTE_MESSUNGEN, 1):
        a("      %d. %s  [%s · %s: %s]"
          % (i, m["was"], m["art"], m["bewertung"].upper(),
             ", ".join(m["merkmale"])))
        for zeile in _umbruch(m["warum"], 76):
            a("         %s" % zeile)
    a("")

    # ── Was OPTIMUM heisst ───────────────────────────────────────────
    a("-" * 98)
    a("⭐⭐⭐ WAS *OPTIMUM* HEISST - die Zieldefinition")
    a("  Nutzerdefinition 27.09.: *OPTIMUM ist, wir kennen die Bewertungen")
    a("  und die LAGE VOR DER BEWEGUNG. Die Bewertung eines bereits")
    a("  gestiegenen Assets ist weder das Ziel noch ein Optimum - dazu")
    a("  brauche ich kein System, das sehe ich am Kurs.*")
    a("")
    for schl in ("ist", "ist_nicht", "ausschluss", "pruefform",
                 "zweite_achse"):
        a("  %-14s %s" % (schl.upper(), _umbruch(OPTIMUM[schl], 76)[0]))
        for zeile in _umbruch(OPTIMUM[schl], 76)[1:]:
            a("  %-14s %s" % ("", zeile))
    a("")
    a("  ⛔⛔ Das disqualifiziert 2.648 als EINSTIEGSSIGNAL - nicht als")
    a("     Messung, sondern als ZWECK. Der Befund bleibt; seine ROLLE")
    a("     aendert sich.")
    a("")

    # ── Was tot ist ──────────────────────────────────────────────────
    a("-" * 98)
    a("⛔⛔⛔ WAS ENDGUELTIG TOT IST")
    a("  Nutzerfestlegung 27.09.: *SPOT = HEBEL ist TOT fuer IMMER und")
    a("  EWIG. Das Geruest von 22.08.26 ist ueberholt. Bauformen 30.08.")
    a("  Optionen, aber keine Gueltigkeit.*")
    a("")
    for _s, (was, warum) in TOT.items():
        a("  ⛔ %s" % was)
        for zeile in _umbruch(warum, 84):
            a("       %s" % zeile)
    a("")
    a("  ⭐ UEBERTRAGBAR bleibt die BUCHFUEHRUNG, nicht die RECHNUNG:")
    for was, warum in UEBERTRAGBAR.items():
        a("      %-18s %s" % (was, _umbruch(warum, 60)[0]))
        for zeile in _umbruch(warum, 60)[1:]:
            a("      %-18s %s" % ("", zeile))
    a("")

    # ── Die zwei Zeitpunkte ──────────────────────────────────────────
    a("-" * 98)
    a("DIE ZWEI ZEITPUNKTE - Bewertung und Positionsfuehrung")
    a("  Nutzerbeispiel 27.09.: *ich sehe die Empfehlung, mache eine")
    a("  Position auf UND DANN kommt eine NEUE Hebelposition ins Spiel,")
    a("  wo wieder alle Parameter wie Stop etc. relevant sind*")
    a("")
    for schl, (wann, was, regel) in ZEITPUNKTE.items():
        a("  %s  %s" % (schl.split("_")[0], wann))
        for x in was:
            a("        · %s" % x)
        for zeile in _umbruch(regel, 78):
            a("      %s" % zeile)
        a("")
    a("  ⭐ Das TRAILING ist damit nicht falsch, sondern in T2 zu Hause -")
    a("     und im Modus MESSEN ein Werkzeug. Beides gleichzeitig.")
    a("")

    # ── Die drei Arbeitsmodi ─────────────────────────────────────────
    a("-" * 98)
    a("DIE DREI ARBEITSMODI - sie beantworten VERSCHIEDENE Fragen")
    a("")
    for name, (phase, frage, regel) in MODI.items():
        a("  %-12s (%s)  %s" % (name.upper(), phase, frage))
        for zeile in _umbruch(regel, 78):
            a("       %s" % zeile)
        a("")

    # ── Die Auswahlebene ─────────────────────────────────────────────
    a("-" * 98)
    a("DIE AUSWAHLEBENE - Asset, nicht Markt")
    a("  Nutzerentscheidung 26.09.: *das System muss auch bei nur EINEM")
    a("  Asset funktionieren und nicht besser oder schlechter durch die")
    a("  Watchlist werden*")
    a("")
    a("  ✔ GILT       %s" % AUSWAHLEBENE["gilt"])
    a("  ⛔ VERBOTEN  %s" % AUSWAHLEBENE["verboten"])
    a("")
    a("  ⛔⛔ AUF DER FALSCHEN EBENE gemessen (Querschnittsrang):")
    for x in AUSWAHLEBENE["betroffen"]:
        a("       %s" % x)
    a("  ✔ sauber (absolute Schwelle):")
    for x in AUSWAHLEBENE["sauber"]:
        a("       %s" % x)
    a("")

    # ── Die Geometrie ────────────────────────────────────────────────
    a("-" * 98)
    a("DIE MESSANORDNUNG - Werkzeug des Modus MESSEN, NICHT Bewertung")
    a("  ⚠️ Nutzervorgabe 27.09.: die Geometrie ist bei der BEWERTUNG")
    a("     nicht relevant; das Trailing gehoert in die POSITIONSFUEHRUNG")
    a("     (Phase 5). Sie steht hier, weil eine Messung ohne Anordnung")
    a("     nicht geht - nicht als Eigenschaft des Systems.")
    a("")
    a("  Messfenster       H%d Stunden" % GEOMETRIE["fenster_stunden"])
    a("  Stop              %.2f x ATR" % GEOMETRIE["stop_atr"])
    a("  Trailing          Ausloeser %.1f R, Abstand %.1f R"
      % (GEOMETRIE["trailing_ausloeser_r"], GEOMETRIE["trailing_abstand_r"]))
    a("  Zielgroesse       %s" % GEOMETRIE["zielgroesse"])
    a("  Messbasis         %s" % GEOMETRIE["messbasis"])
    a("")
    a("  ⚠️ Der Spot-Arm misst H20 gegen `bewegung_r` mit FIXEN Barrieren.")
    a("     Eine Groesse, die DORT gemessen wurde, sagt hier nichts -")
    a("     auch wenn sie denselben Namen traegt.")
    a("")

    # ── Die drei Rollen ──────────────────────────────────────────────
    a("-" * 98)
    a("DIE DREI ROLLEN - Anordnung A und B und NICHT C")
    a("")
    zaehl = {}
    for r in ("A", "B", "C"):
        a("  %s  %s" % (r, ROLLEN[r]))
        for name, zst, befund, hinweis in KANDIDATEN[r]:
            zaehl[zst] = zaehl.get(zst, 0) + 1
            marke = {"belegt": "✔✔", "teilbelegt": "⭐⚠", "faellt": "⛔",
                     "offen": "· "}.get(zst, "? ")
            a("      %s %-16s %-12s %s" % (marke, name, zst, befund))
            if hinweis:
                for zeile in _umbruch(hinweis, 78):
                    a("           %s" % zeile)
        a("")
    a("  ➤ %s"
      % " · ".join("%d %s" % (v, k) for k, v in sorted(zaehl.items())))
    a("")

    # ── Was fehlt ────────────────────────────────────────────────────
    a("-" * 98)
    _t1 = [n for n, e in BEITRAGSLAGE.items() if e["b1"] == "belegt"]
    _v1 = [n for n in _t1 if BEITRAGSLAGE[n]["vorlauf"] == "ja"]
    a("⛔⛔ ES GIBT HEUTE KEINE EINSTIEGSREGEL - Bewertung 1 hat %d Traeger"
      % len(_t1))
    a("    beim sofortigen Einstieg, davon %d mit VORLAUF, und kalibriert"
      % len(_v1))
    a("    (nein / gut / sehr gut) ist nichts. Das ist der Stand, nicht ein")
    a("    Versaeumnis.")
    a("")
    for titel, text in OFFEN:
        a("  ⚠️ %s" % titel)
        for zeile in _umbruch(text, 88):
            a("       %s" % zeile)
    a("")

    # ── Die Befunde des Neubaus ──────────────────────────────────────
    if mit_befunden:
        a("-" * 98)
        try:
            bef = _befunde_ab()
        except Exception as e:                       # pragma: no cover
            bef = []
            a("⚠️ Befunde nicht lesbar: %s" % e)
        gilt = [b for b in bef if b[1] == "gilt"]
        weg = [b for b in bef if b[1] == "abgeloest"]
        a("DIE BEFUNDE DES NEUBAUS (ab %s) - %d gelten, %d abgeloest"
          % (NEUBAU_AB_TEXT, len(gilt), len(weg)))
        if not bef:
            a("  ⛔⛔ KEINE gefunden - das ist ein FEHLER im Leser, kein")
            a("      Zustand. Eine leere Liste sieht aus wie eine Aussage.")
        a("")
        for kennung, _z, aussage in gilt:
            a("  ✔ %-44s %s" % (kennung, _erster_satz(aussage, 48)))
        if weg:
            a("")
            for kennung, _z, aussage in weg:
                a("  ⛔ %-44s %s" % (kennung, _erster_satz(aussage, 48)))
        a("")
    a("=" * 98)
    return "\n".join(L)


def _umbruch(text: str, breite: int) -> list:
    """Wortweiser Umbruch - `textwrap` wuerde die Emojis falsch zaehlen."""
    worte, zeilen, z = str(text).split(), [], ""
    for w in worte:
        if z and len(z) + 1 + len(w) > breite:
            zeilen.append(z)
            z = w
        else:
            z = (z + " " + w).strip()
    if z:
        zeilen.append(z)
    return zeilen


def nachweis_sauber(verboten: tuple = None) -> tuple:
    """-> (ok, gefunden) - hat `stand()` den Spot-Arm angefasst?

    ⚠️⚠️ DER NACHWEIS AM SEITENEFFEKT, nicht an einer Textsuche. Ruft
    `stand()` in einem FRISCHEN Interpreter auf und sieht danach in
    `sys.modules` nach. Ein Import innerhalb einer Funktion - genau das,
    was eine Textsuche uebersieht - faellt hier auf.

    ⚠️ Eigener Interpreter, weil `sys.modules` im laufenden Prozess
    laengst verschmutzt ist (die Suite importiert alles).

    ⚠️⚠️ `verboten` IST NICHT KOSMETIK, SONDERN DIE GEGENPROBE. Die erste
    Fassung las die Liste im Kindprozess aus dem frisch importierten
    Modul - eine Aenderung im ELTERNprozess kam dort nie an. Damit liess
    sich die Pruefung nicht zum Fehlschlagen bringen, und eine Pruefung,
    die nicht fehlschlagen KANN, prueft nichts. Gefunden hat das die
    Gegenprobe in der Suite, nicht ich.
    """
    import json as _j
    import subprocess
    import sys as _s
    import os as _os
    liste = tuple(verboten) if verboten is not None else VERBOTENE_MODULE
    code = (
        "import sys, json\n"
        "VERBOTEN = json.loads(%r)\n"
        "import hebel_neubau as H\n"
        "H.stand()\n"
        "schlecht = sorted({m.split('.')[0] for m in sys.modules\n"
        "                   if m.split('.')[0] in VERBOTEN})\n"
        "print(json.dumps(schlecht))\n" % _j.dumps(list(liste)))
    r = subprocess.run(
        [_s.executable, "-c", code],
        cwd=_os.path.dirname(_os.path.abspath(__file__)),
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        env=dict(_os.environ, PYTHONIOENCODING="utf-8"))
    if r.returncode != 0:
        return False, ["ABBRUCH: %s" % (r.stderr or "")[-300:]]
    import json
    try:
        schlecht = json.loads((r.stdout or "[]").strip().splitlines()[-1])
    except Exception:
        return False, ["Ausgabe unlesbar: %r" % (r.stdout or "")[-200:]]
    return (not schlecht), schlecht


if __name__ == "__main__":
    # ⚠️ Die Windows-Konsole faellt sonst auf cp1252 zurueck und bricht
    # am ersten Pfeil ab - derselbe Fehler wie in mehreren Messskripten.
    import sys
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    if "--rollen" in sys.argv:
        print(rollenblatt())
    elif "--nachweis" in sys.argv:
        ok, schlecht = nachweis_sauber()
        print("SEITENEFFEKT-NACHWEIS: %s"
              % ("✔ stand() hat den Spot-Arm NICHT angefasst" if ok
                 else "⛔ ANGEFASST: %s" % ", ".join(schlecht)))
        raise SystemExit(0 if ok else 1)
    else:
        print(stand())
