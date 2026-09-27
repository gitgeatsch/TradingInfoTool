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
ROLLEN = {
    "A": "Richtung - geht es aufwaerts? Trendumkehr?",
    "B": "Bewegungserwartung - kommt ueberhaupt etwas? (richtungslos)",
    "C": "Risikosperre - ueberdehnt, ueberhitzt?",
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
        ("momentum_kurz", "teilbelegt", "2.594/2.603",
         "RICHTUNG belegt: Lift 1,937 bis zur strengsten Vola-Kontrolle, "
         "Spiegelprobe bestanden (geeichte Schwelle 1,717). ABER auf einem "
         "EREIGNIS (+10 %/6 h) gemessen, nie auf dieser Geometrie"),
        ("rsi", "teilbelegt", "2.594",
         "RICHTUNG belegt: Lift 1,893 unter strengster Kontrolle. Dieselbe "
         "Einschraenkung wie momentum_kurz"),
        ("trendstruktur", "faellt", "2.645",
         "E[R] +0,00032, Tagesfehler +-0,00294 - Faktor 9 zu klein"),
        ("ema_lage", "faellt", "2.645", "E[R] +0,00037, nicht von null zu trennen"),
        ("ema_steigung", "faellt", "2.645", ""),
        ("rsi_aenderung", "faellt", "2.645", ""),
        ("rsi_umkehr", "faellt", "2.645",
         "mit rsi kombiniert nur 1 von 5 Jahren positiv"),
    ],
    "B": [
        ("bandenge", "offen", "",
         "Squeeze. ⚠️ In 2.645 lief es MIT, aber gegen `E[R]` - das ist die "
         "A-Frage. Die B-Testform ist die AUFLOESUNGSRATE (kommt ueberhaupt "
         "etwas?), und die ist RICHTUNGSLOS. So ist es nie gemessen worden"),
    ],
    "C": [
        ("ema_abstand_atr", "belegt", "2.642/2.647",
         "RISIKOSPERRE: d 0,521 auf MAE gegen 0,267 auf MFE (2.642). Traegt "
         "absolut (84-facher Markt) UND je Asset (99,1 % des Lifts bleiben "
         "symbolintern), alle sechs Pruefungen (2.647)"),
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
         "bewertet. Das ist laut Nutzervorgabe 27.09. die einzige "
         "Gemeinsamkeit der beiden Arme - und sie bleibt"),
        ("Der Spot-Arm", "laeuft unveraendert weiter und fuehrt die offenen "
         "Positionen. Er wird NICHT stillgelegt und ist hier kein Thema"),
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
# ⚠️⚠️ Der Neubau hat HEUTE KEINEN EINSTIEG. Das ist kein Mangel, den man
# verschweigt, sondern der Stand: belegt ist eine Sperre (C), nicht ein
# Ausloeser. Wer nach "dem aktuellen Hebel-Einstieg" fragt, bekommt
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
    a("⛔⛔ ES GIBT HEUTE KEINEN EINSTIEG - belegt ist eine SPERRE, kein")
    a("    AUSLOESER. Das ist der Stand, nicht ein Versaeumnis.")
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
