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

# ══ DIE GEOMETRIE DES NEUBAUS ═══════════════════════════════════════
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


class SpotVermischung(RuntimeError):
    """Eine Hebel-Neubaumessung hat eine Spot-Groesse angefasst."""


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

    # ── Die Geometrie ────────────────────────────────────────────────
    a("-" * 98)
    a("DIE GEOMETRIE - sie ist NICHT die des Spot-Arms")
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
