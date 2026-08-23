# -*- coding: utf-8 -*-
"""Von der Rollen-Kette in die Tabelle `signals` (Paket 6, 12.08.2026).

DIE FUENF ECKPUNKTE, alle an der Quelle gemessen:

1  DAS AKTIONS-VOKABULAR DECKT SICH NUR ZU DREI VON FUENF.

       gemeinsam   KAUFEN · NACHKAUFEN · VERKAUFEN
       nur alt     HALTEN · TAUSCHEN
       nur neu     NICHTS_TUN · REDUZIEREN

   NICHTS_TUN WIRD AUF HALTEN ABGEBILDET - korrigiert am 12.08. nach
   Nutzereinwand, und meine erste Begruendung war falsch.

   Ich hatte geschrieben, die beiden seien verschieden: "HALTEN heisst den
   Bestand behalten, NICHTS_TUN heisst auch nicht kaufen." Der Nutzer:
   *"auf z.B. Assets haette ich diese analog verstanden - beides bedeutet beim
   Asset keine Aktion, aktueller Stand bleibt so."*

   Er hat recht. Der Unterschied, den ich meinte, steckt NICHT IN DER AKTION,
   sondern im KONTEXT - halte ich das Asset oder nicht. Und der Kontext steht
   laengst woanders: im Bestand (`menge`, `einstand`), der bei jedem Signal
   mitgeschrieben wird. Zwei Etiketten fuer dasselbe Ergebnis verdoppeln eine
   Information, die schon da ist.

   Und es waere SCHAEDLICH fuer genau die Messung, die ich schuetzen wollte:
   laege in der alten Kette HALTEN und in der neuen NICHTS_TUN, muesste jede
   Auswertung beide kennen - sonst zaehlt sie die halbe Wahrheit.

   DIE UNTERSCHEIDUNG, AUF DIE ES BEIM DEADLOOP ANKOMMT, ist ohnehin eine
   andere: selbst gewaehlt gegen degradiert. Dafuer gibt es `original_action`
   und `ist_reines_llm_halten`, und die neue Kette vermerkt eine Ruecknahme in
   `_degradiert`.

   REDUZIEREN BLEIBT EIGENSTAENDIG. Ein Teilverkauf ist kein Vollverkauf - die
   Position wird kleiner statt geschlossen, und das ist ein anderer Ausgang.
   TAUSCHEN bleibt als Altwert fuer bestehende Zeilen gueltig.

2  FUENF FELDER HATTEN KEIN ZUHAUSE. Sie bekommen eigene Spalten, additiv und
   idempotent wie jede Migration hier.

3  NUR FUENF SPALTEN SIND PFLICHT: symbol, created_at, action, gate_passed,
   facts_json. `confidence_pct` ist nullable - die neue Kette darf also NULL
   schreiben, ohne dass etwas bricht. Dass die E-Mail "Konfidenz X %" in eine
   Ueberschrift schreibt, ist ein Anzeigeproblem und gehoert zu Paket 12.

4  `facts_json` IST BEI 78 VON 118 SIGNALEN LEER - UND DAS IST KORREKT.
   KORREKTUR 12.08. abends: hier stand, die Fakten "fehlten bei zwei
   Dritteln". Das war falsch gelesen. Nachgezaehlt nach Gate-Zustand:

       HALTEN, gate=0, "Preis veraltet"     72 von 72 leer
       HALTEN, gate=0, Stablecoin/Historie   6 von  6 leer
       HALTEN, gate=1                        0 von 37 leer
       KAUFEN/NACHKAUFEN/TAUSCHEN, gate=1    0 von  3 leer

   JEDES Signal, das das Gate passiert hat, traegt seine Fakten - ausnahmslos.
   Die leeren sind Abweisungen VOR der Analyse; dort gab es nie Fakten, weil
   die Pipeline vorher anhaelt (`_fixed_signal(facts=None)`). Eine Zahl ohne
   ihre Schichtung ist keine Diagnose.

   Fuer die neue Kette bleibt es trotzdem Pflicht, den Faktensatz
   mitzuschreiben - ohne ihn ist eine Empfehlung im Nachhinein nicht pruefbar.

5  ROLLE 1 IST EINE ZEILE JE DURCHGANG, NICHT JE SIGNAL. Das Lagebild in 44
   Signalzeilen zu kopieren waere 44-fache Redundanz, und bei einer spaeteren
   Korrektur haette man 44 Stellen. Es bekommt eine eigene Tabelle
   `lagebilder`; das Signal traegt nur die Kennung.
"""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone

# Das vereinigte Vokabular. `signals.action` traegt jetzt beide Welten - solange
# die alte Kette laeuft, muessen ihre Werte gueltig bleiben.
AKTIONEN_ALT = ("HALTEN", "KAUFEN", "NACHKAUFEN", "TAUSCHEN", "VERKAUFEN")
#
# IMPORTIERT STATT ABGESCHRIEBEN (Gesamtpruefung 13.08.). Hier stand eine
# HANDKOPIE der fuenf Spot-Aktionen. Als Paket 13 dem Hebel sieben Aktionen
# gab, wusste diese Datei nichts davon - ein Hebel-Signal der neuen Kette
# waere beim Schreiben an der eigenen Vokabularpruefung gescheitert, und zwar
# erst im Betrieb. Dieselbe Sorte Kopie wie die Kostensaetze am 12.08.
from agent.empfehlung_vertrag import AKTIONEN as AKTIONEN_NEU
from agent.empfehlung_vertrag import AKTIONEN_HEBEL

# Was die neue Kette sagt -> was in der Spalte steht. Nur EIN Eintrag, und der
# ist begruendet (siehe Eckpunkt 1): gleiche Aktion, gleiches Ergebnis.
#
# ⚠️ S6a AENDERT HIER NICHTS. Die neue Kette spricht seit S6a nur noch das
# Spot-Vokabular; NICHTS_TUN -> HALTEN gilt unveraendert. Die alten
# Hebel-Namen erreichen die Spalte nicht mehr aus der neuen Kette - sie
# stehen weiter in `hebel_signals` aus der alten und in bestehenden Zeilen.
# Fuer deren Auswertung gibt es `empfehlung_vertrag.AKTION_AUS_HEBEL`.
UMBENENNUNG = {"NICHTS_TUN": "HALTEN"}

# Das Vokabular der SPALTE nach der Abbildung. NICHTS_TUN steht bewusst NICHT
# darin - es erreicht die Datenbank nie.
AKTIONEN = tuple(sorted(
    set(AKTIONEN_ALT)
    | {UMBENENNUNG.get(a, a) for a in AKTIONEN_NEU}
    | {UMBENENNUNG.get(a, a) for a in AKTIONEN_HEBEL}))

# Neue Spalten auf `signals`. Namen bewusst mit `rolle_`-Praefix, wo eine
# Verwechslung mit einem Altfeld moeglich waere - `begruendung` gaebe es sonst
# neben `short_reasoning` und niemand wuesste, welches gilt.
SPALTEN_SIGNAL = {
    "quelle_kette": "TEXT",                 # 'alt' oder 'rollen' - ohne diese
                                            # Spalte laesst sich spaeter keine
                                            # Messung nach Ketten trennen
    "unabhaengige_faktoren": "INTEGER",
    # DIE BELEGE SELBST (14.08.2026) - bis heute ging nur ihre ANZAHL in die
    # Datenbank.
    #
    # WAS DAS GEKOSTET HAT: die Mail zeigt "Belege (5, davon 3 unabhaengige
    # Faktoren)" mit fuenf Zeilen aus Fakt, Richtung und Gewicht. Gespeichert
    # wurde davon die Zahl 5 und die Zahl 3. Die Frage des Nutzers - *"warum
    # erfolgte die Entscheidung, sind die Parameter die richtigen"* - ist damit
    # nachtraeglich NICHT beantwortbar: wir wissen, dass das Modell drei
    # unabhaengige Gruende hatte, aber nicht, welche.
    #
    # UND GENAU DARAUF LAEUFT DIE MESSUNG HINAUS. Welche unserer Fakten fuehren
    # zu Urteilen, die sich tragen? Ohne die Belege ist das unbeantwortbar, und
    # zwar dauerhaft - eine Zeile, die heute ohne sie geschrieben wird, laesst
    # sich spaeter nicht nachruesten.
    #
    # ALS JSON, nicht als Spalten. Fuenf Belege mal drei Felder waeren fuenfzehn
    # Spalten, deren Zahl vom Modell abhaengt; die alte Kette hat das mit
    # `top_grund_1..5` gemacht und dabei den sechsten stillschweigend verloren.
    # DIE AUFFAELLIGEN PERZENTILE, ALS JSON (P1a, 19.08.2026, Kapitel 91).
    #
    # Bis heute war die Kennzeichnung reine ANZEIGE: die Mail setzte
    # auffaellige Werte fett, und mit dem naechsten Umlauf war es vergessen.
    # Damit konnte die einzige Frage, fuer die P1 gebaut wurde, nie gestellt
    # werden: verhalten sich Signale mit auffaelligem Funding anders?
    #
    # Die Antwort braucht Signale, deren Ausgang NOCH OFFEN ist - jeder Tag
    # ohne dieses Feld ist ein verlorener Tag. Es entscheidet nichts und
    # filtert nichts; es haelt nur fest, was in der Mail ohnehin stand.
    "auffaellige_json": "TEXT",
    "belege_json": "TEXT",
    "umgeworfen_durch": "TEXT",
    "umgeworfen_preis_eur": "REAL",
    "umgeworfen_bis": "TEXT",
    "lagebild_id": "INTEGER",
    "prompt_stand": "TEXT",                 # jeder Befund gehoert zu einem
                                            # Prompt-Stand (Nutzervorgabe 11.08.)
    "fx_eur_je_usd": "REAL",                # der EINGEFRORENE Kurs (Paket 7).
                                            # Ohne ihn liesse sich spaeter nicht
                                            # nachrechnen, wie die USD-Zonen
                                            # entstanden sind
    # DIE DREI GEMESSENEN FAKTENFAMILIEN (13.08., Schritt 1 zu Kapitel 15).
    #
    # WARUM SIE AUF DIE SIGNALZEILE GEHOEREN und nicht nur in die Mail:
    # `trefferbilanz.merkmale()` hat VIER Plaetze im Konstellationsschluessel,
    # gefuellt wurde bisher EINER - die Faktorzahl. Und von der ist gemessen,
    # dass sie die Entscheidung nur wiederholt (Faktorzahl 3 -> 82 % Einstieg,
    # Faktorzahl 2 -> 0 %). Ein Meta-Modell, dessen einziges Merkmal die
    # Ausgabe des Primaermodells ist, kann nichts hinzufuegen.
    #
    # `faktenblock.werte_aus_reihe()` rechnet diese drei ohnehin je Asset zum
    # Signalzeitpunkt - sie standen bisher NUR im Mailtext und waren danach
    # weg. Perzentile, nicht Rohwerte: der Vergleichsmassstab ist das eigene
    # Jahr des Symbols, sonst waere BTC nicht mit einem Kleinwert vergleichbar.
    "schwankung_perzentil": "REAL",         # -11,7 pp (ruhig ist besser)
    "momentum_perzentil": "REAL",           # +9,1 pp
    "volumen_perzentil": "REAL",            # +4,5 pp
    # WIE EINIG SICH DIE ZWEITE MEINUNG WAR (13.08., Kapitel 15). Gemessen
    # kippt das Richtungsurteil von Z.ai bei IDENTISCHER Eingabe in 30 % der
    # Faelle (`messe_namensanker.py`, 20 Symbole). Seither werden drei Stimmen
    # geholt; diese Spalte haelt fest, wie viele davon das Urteil trugen.
    # Ohne sie sieht ein Muenzwurf spaeter aus wie ein Befund.
    "zai_stimmen": "INTEGER",
    # RICHTUNG UND HEBELFAKTOR (15.5c, 13.08.) - gefunden im ERSTEN Live-Lauf
    # des Hebel-Wegs, und nur dort zu finden.
    #
    # Paket 13 hat dem Hebel die Richtung gegeben: das Modell nennt sie, sie
    # ist bei EROEFFNEN und NACHKAUFEN Pflicht und wird nie geraten, und sie
    # dreht Stop, Ziel und Liquidation. Beim Schreiben fiel sie trotzdem
    # heraus - `signals` kannte keine solche Spalte (nur `hebel_signals`, die
    # Tabelle der ALTEN Kette). Vier echte Hebel-Signale landeten damit
    # richtungslos in der Datenbank; ein SHORT sah aus wie ein LONG.
    #
    # Der Hebelfaktor genauso: er wird aus Risikobudget und
    # Liquidationsabstand gerechnet und war danach weg. Aus den Zonen laesst
    # sich die Richtung notfalls zurueckrechnen (`_richtung_aus_zonen`), der
    # Faktor nicht - und ohne ihn ist ein Ausgang nicht bewertbar.
    "richtung": "TEXT",
    "hebel": "REAL",
    # WELCHES MODELL DAS URTEIL GEFAELLT HAT (14.08., Voraussetzung fuer die
    # Rueckfallkette).
    #
    # `lagebilder` haelt sein Modell seit Paket 6 fest, die Signalzeile nicht.
    # Sobald die Kette bei erschoepftem Kontingent auf ein anderes Modell
    # ausweicht, mischten sich damit ZWEI Urteilsverteilungen lautlos in
    # dieselbe Trefferbilanz - und genau die Kalibrierung, auf die alles
    # wartet, waere verunreinigt, bevor sie anfaengt.
    #
    # Das ist keine Vermutung: der Mistral-Verhaltensbruch vom 31.07. zeigte
    # 55,4 gegen 68,0 % bei BITGLEICHEM Prompt. Modelle unterscheiden sich
    # messbar, also muss die Zeile sagen, welches gesprochen hat.
    "modell": "TEXT",
}

_LAGEBILDER = """
CREATE TABLE IF NOT EXISTS lagebilder (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    datum         TEXT NOT NULL,
    erstellt_am   TEXT NOT NULL,
    lage          TEXT,
    belege_json   TEXT,
    klassen_json  TEXT,
    gleichlauf    TEXT,
    fakten_json   TEXT NOT NULL,
    prompt_stand  TEXT,
    modell        TEXT
)
"""


def migriere(conn: sqlite3.Connection) -> list[str]:
    """Additiv und idempotent. Gibt zurueck, was neu angelegt wurde."""
    neu = []
    vorhanden = {r[1] for r in conn.execute("PRAGMA table_info(signals)")}
    for name, typ in SPALTEN_SIGNAL.items():
        if name not in vorhanden:
            conn.execute(f"ALTER TABLE signals ADD COLUMN {name} {typ}")
            neu.append(f"signals.{name}")
    tabellen = {r[0] for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'")}
    if "lagebilder" not in tabellen:
        conn.execute(_LAGEBILDER)
        neu.append("lagebilder")
    conn.commit()
    return neu


def schreibe_lagebild(conn: sqlite3.Connection, *, datum: str, antwort: dict,
                      fakten: list, prompt_stand: str | None = None,
                      modell: str | None = None) -> int:
    """Eine Zeile je Durchgang. Gibt die Kennung zurueck.

    `fakten` ist der Faktensatz, den das Modell GESEHEN hat - nicht der, den
    man heute neu bauen wuerde. Ohne ihn ist eine Antwort im Nachhinein nicht
    mehr erklaerbar, und genau das war bei zwei Dritteln der Altsignale der
    Fall."""
    migriere(conn)
    cur = conn.execute(
        "INSERT INTO lagebilder (datum, erstellt_am, lage, belege_json, "
        "klassen_json, gleichlauf, fakten_json, prompt_stand, modell) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (datum, datetime.now(timezone.utc).isoformat(),
         antwort.get("lage"),
         json.dumps(antwort.get("belege") or [], ensure_ascii=False),
         json.dumps(antwort.get("klassen") or [], ensure_ascii=False),
         antwort.get("gleichlauf"),
         json.dumps(fakten or [], ensure_ascii=False),
         prompt_stand, modell))
    conn.commit()
    return int(cur.lastrowid)


def juengstes_lagebild(conn: sqlite3.Connection,
                       max_alter_stunden: float) -> tuple | None:
    """Das juengste Lagebild, wenn es noch frisch genug ist - sonst None.

    WOZU. Rolle A beschreibt den GESAMTMARKT und laeuft einmal je Durchgang.
    Bei einem 15-Minuten-Takt waeren das 96 Aufrufe am Tag je Instrument, fuer
    eine Aussage, die sich in 15 Minuten nicht aendert. Mit drei Stunden
    Haltbarkeit sind es acht.

    DREI STUNDEN, NICHT ACHT (Nutzerentscheidung 14.08.). Das Lagebild speist
    JEDEN Trader-Aufruf in seinem Fenster - je aelter es ist, desto mehr
    Urteile haengen an einem veralteten Marktbild. Der Unterschied kostet 10
    Aufrufe am Tag gegen ein Budget von 500.

    Gibt `(id, antwort)` zurueck, wobei `antwort` die Form hat, die
    `rolle_analyst.validiere()` liefert - der Aufrufer merkt nicht, ob es
    gerade erfragt oder wiederverwendet wurde.

    Fail-soft: bei fehlender Tabelle oder unlesbarem JSON gibt es kein
    Zwischenergebnis, also wird neu gefragt. Ein kaputter Zwischenspeicher darf
    hoechstens Geld kosten, nie ein falsches Marktbild liefern."""
    from datetime import timedelta

    try:
        zeile = conn.execute(
            "SELECT id, erstellt_am, lage, belege_json, klassen_json, "
            "gleichlauf FROM lagebilder ORDER BY id DESC LIMIT 1").fetchone()
    except Exception:                                        # noqa: BLE001
        return None
    if not zeile:
        return None
    kennung, erstellt, lage, belege, klassen, gleichlauf = tuple(zeile)
    try:
        wann = datetime.fromisoformat(str(erstellt))
        if wann.tzinfo is None:
            wann = wann.replace(tzinfo=timezone.utc)
        if datetime.now(timezone.utc) - wann > timedelta(hours=max_alter_stunden):
            return None
        antwort = {"lage": lage,
                   "belege": json.loads(belege or "[]"),
                   "klassen": json.loads(klassen or "[]")}
    except Exception:                                        # noqa: BLE001
        return None
    if gleichlauf:
        antwort["gleichlauf"] = gleichlauf
    return int(kennung), antwort


def _frist_oder_nichts(datum_text, heute=None):
    """Eine Frist, die schon abgelaufen ist, ist keine Frist (15.08.2026).

    GEMESSEN AM ERSTEN PRODUKTIONSLAUF: von 37 Fristen, die das Modell
    genannt hat, lagen 36 in der VERGANGENHEIT - allein 29-mal der
    Fuellwert "2024-12-31". Ein Datum, das vor dem Tag des Signals liegt, ist
    keine Aussage ueber die Haltbarkeit der Begruendung, sondern ein Modell,
    das ein Pflichtfeld gefuellt hat.

    WARUM DAS NICHT FOLGENLOS BLIEB. `ausstiegsrechnung` fuehrt die Frist als
    drittes Kriterium und setzt "· FRIST ABGELAUFEN" in die Ueberschrift der
    Empfehlung. Am 15.08. traf das erst 1 von 40 Positionen - nur weil die
    alten Signale das Feld gar nicht hatten. Mit jedem neuen Signal waere es
    gewachsen, bis fast jede gehaltene Position eine abgelaufene Begruendung
    gemeldet haette.

    NICHT REPARIERT, SONDERN VERWORFEN. Ein Datum zu raten waere schlimmer:
    `rollen_lauf._tage_bis()` faellt bei fehlender Frist auf die Schaetzung aus
    Weg und Schwankung zurueck, und die ist gerechnet statt geraten."""
    from datetime import date

    if not datum_text:
        return None
    try:
        ziel = date.fromisoformat(str(datum_text)[:10])
    except (ValueError, TypeError):
        return None
    vergleich = heute or date.today()
    return ziel.isoformat() if ziel > vergleich else None


def felder_aus_entscheidung(antwort: dict, *, fakten: dict,
                            lagebild_id: int | None = None,
                            prompt_stand: str | None = None,
                            eur_je_usd: float | None = None,
                            familien: dict | None = None,
                            rechnung: dict | None = None,
                            modell: str | None = None,
                            instrument: str | None = None) -> dict:
    """Die Spaltenwerte fuer EIN Signal aus der Antwort der Rollen-Kette.

    SCHREIBT NICHT - der Aufrufer entscheidet, ob und wann. Diese Trennung ist
    Absicht: eine Abbildungsfunktion, die selbst schreibt, laesst sich nicht
    trocken pruefen.

    WAS BEWUSST LEER BLEIBT und warum es kein Versehen ist:

        confidence_pct   die neue Kette nennt keine Konfidenz (77,5 %
                         vorhergesagt gegen 33,3 % eingetreten)
        regime           ueber 1.022 Faelle konstant "baer"
        top_grund_1..5   ersetzt durch `belege` mit Richtung und Gewicht
        forecast_*       drei Szenarien mit Prozentzahlen - dieselbe
                         Kalibrierungsschwaeche wie die Konfidenz

    Eine leere Spalte ist hier eine ENTSCHEIDUNG. Sie mit einem Ersatzwert zu
    fuellen waere schlimmer: dann stuende eine Zahl da, die niemand gerechnet
    hat."""
    aktion = str(antwort.get("aktion") or "").strip().upper()
    aus = {
        "action": UMBENENNUNG.get(aktion, aktion),
        "quelle_kette": "rollen",
        "prompt_stand": prompt_stand,
        "lagebild_id": lagebild_id,
        "short_reasoning": antwort.get("begruendung"),
        "gegenargument": antwort.get("was_dagegen"),
        "unabhaengige_faktoren": antwort.get("unabhaengige_faktoren"),
        "belege_json": (json.dumps(antwort["belege"], ensure_ascii=False)
                        if antwort.get("belege") else None),
        "umgeworfen_durch": antwort.get("umgeworfen_durch"),
        "umgeworfen_preis_eur": antwort.get("umgeworfen_preis_eur"),
        "umgeworfen_bis": _frist_oder_nichts(antwort.get("umgeworfen_bis")),
        # DER FAKTENSATZ IST PFLICHT (Eckpunkt 4). Ohne ihn ist die Empfehlung
        # im Nachhinein nicht mehr pruefbar.
        "facts_json": json.dumps(fakten or {}, ensure_ascii=False),
        "position_size_eur": antwort.get("tranche_eur"),
        # NUR WENN DAS MODELL SIE GENANNT HAT. Bei Spot gibt es keine
        # Richtung - dort waere ein eingetragenes "LONG" eine Behauptung, die
        # niemand aufgestellt hat.
        "richtung": antwort.get("richtung"),
        "modell": modell,
    }
    # DER HEBELFAKTOR KOMMT AUS DER RECHNUNG, nicht aus der Antwort. Das Modell
    # nennt die Richtung, das System rechnet den Faktor (Paket 13) - er darf
    # deshalb auch nur von dort kommen.
    #
    # NUR ECHTE HEBEL, NICHT DIE 1,0 VON SPOT (gefunden im Watchlist-Probelauf
    # 13.08.). `entscheidungsrechnung` setzt fuer Spot `hebel = 1.0`, damit
    # Verlust und Gewinn mit derselben Formel gerechnet werden koennen. Auf der
    # Signalzeile ist diese 1,0 aber KEINE Information, sondern ein Fehler mit
    # Folgen: `toepfe.belegt_eur()` trennt die Toepfe an genau dieser Spalte
    # (`hebel IS NULL` = Spot). Neun Spot-Signale trugen damit 2.250 EUR in den
    # HEBEL-Topf, und der haette sich nach zwei Laeufen als voll gemeldet.
    # AM INSTRUMENT UNTERSCHEIDEN, NICHT AM WERT (15.08.2026).
    #
    # Die erste Fassung fragte `hebel > 1.0` - richtig gemeint, aber am
    # falschen Merkmal. Sie traf auch einen ECHTEN Hebel-Trade, dessen
    # sicherer Faktor auf 1,0 faellt: bei KAITO (9,9 % Stop) und CAT (17,4 %)
    # drueckte `max_safe_hebel()` den Faktor auf den Boden, weil die
    # Liquidation sonst vor dem Stop laege. Beide wurden als SPOT geschrieben,
    # fielen damit aus dem Hebel-Cooldown (`hebel IS NOT NULL`) und aus dem
    # Hebel-Topf - und trugen trotzdem den Mailbetreff "EROEFFNEN (Hebel)".
    #
    # Das Instrument ist bekannt und eindeutig; der Wert ist es nicht.
    # ⚠️ A2 (23.08.2026): DIE SPALTE FOLGT DEM ERGEBNIS, NICHT DEM LAUF.
    #
    # Hier stand `str(instrument) == "hebel"`. Seit S6b ist das fuer Krypto
    # nie wieder wahr - die Spalte blieb leer, und daran haengen ZWEI Dinge,
    # die keine Buchhaltung sind:
    #
    #   `toepfe.sql_bedingung()`  trennt die Toepfe an `hebel IS NOT NULL`.
    #                             Der Hebel-Topf ist eine Nutzerentscheidung
    #                             vom 13.08. ("gesamt 3000 EUR, eine Position
    #                             vorerst 1000") und ein RISIKODECKEL: der
    #                             Hebel ist die einzige Position, die mehr
    #                             verlieren kann als ihren Einsatz.
    #   `wiederholung`            der eigene Cooldown-Topf des Hebels.
    #
    # ⚠️ DESHALB GEHOEREN A1 UND A2 ZUSAMMEN. A1 allein liesse den Hebel
    # wieder entstehen, ohne ihn in den gedeckelten Topf zu buchen - eine
    # 3.000-EUR-Obergrenze, die nichts sieht.
    #
    # WARUM DAS ETIKETT UND NICHT DER WERT. Der Kommentar von damals bleibt
    # richtig: `hebel > 1.0` traf einen echten Hebel-Trade nicht, dessen
    # sicherer Faktor auf 1,0 faellt. Das Etikett aus `rechne()` trifft ihn,
    # denn es fragt den NOETIGEN Faktor, nicht den gedeckelten.
    #
    # RUECKFALL: kein Etikett in der Rechnung (alte Ketten) -> das Instrument.
    _etikett = (rechnung or {}).get("etikett")
    _ist_hebel = (_etikett == "hebel" if _etikett
                  else str(instrument) == "hebel")
    if _ist_hebel and rechnung and rechnung.get("hebel"):
        aus["hebel"] = float(rechnung["hebel"])
    # Die Zonen nur, wenn es sie gibt - bei NICHTS_TUN und bei Akkumulation
    # entfallen sie, und ein Nullwert waere dort eine Aussage, die niemand
    # getroffen hat.
    #
    # UND ZUSAETZLICH IN USD (Paket 7). Das Backward-Tracking laedt
    # `price_history_ohlc WHERE currency = 'USD'` und vergleicht gegen
    # `entry_usd`/`stop_loss_usd`/`take_profit_usd`. Ein Signal mit nur
    # EUR-Zonen bliebe deshalb fuer immer unaufgeloest - der Faden zur
    # Erfolgsmessung waere gerissen, und ohne sie gibt es keine Trefferbilanz
    # (Paket 8) und damit keine Zahl fuer die E-Mail.
    #
    # DER KURS WIRD ZUM SIGNALZEITPUNKT EINGEFROREN, und das ist Absicht:
    # so misst der Ausgang die Bewegung des ASSETS, nicht die des Wechselkurses.
    # Wer spaeter mit dem dann gueltigen Kurs zurueckrechnete, mische
    # FX-Rauschen in jede Trefferquote. Dieselbe Linie faehrt die alte Kette
    # bereits mit `eur_aus_usd(..., eur_usd_fx_rate)`.
    #
    # Ohne Kurs KEINE USD-Spalten - ein geratener Umrechnungsfaktor waere
    # schlimmer als eine leere Spalte.
    # DIE GEOMETRIE KOMMT AUS DER RECHNUNG, NICHT AUS DER ANTWORT (15.08.2026).
    #
    # Hier stand `antwort.get(f"{feld}_eur_{rand}")` - also die Zahlen des
    # MODELLS. Die Mail zeigt seit dem 14.08. die der RECHNUNG. Damit trug
    # dasselbe Signal zwei Geometrien: eine, die der Nutzer liest, und eine,
    # die in der Datenbank steht.
    #
    # GEMESSEN an den 23 Einstiegen des ersten Produktionsvormittags: die
    # Zeile trug bei 19 von ihnen einen ENGEREN Stop als die Mail, im Median
    # um den Faktor 1,5, im Aeussersten 2,8 (ETH 0,94 % gegen 2,50 %). Sieben
    # Zeilen lagen unter RM-1b (2,5 %) - der Klasse, fuer die dieses Projekt
    # 0,0 % Trefferquote ueber 9 Trades gemessen hat.
    #
    # WARUM DAS MEHR IST ALS EINE UNSAUBERKEIT: `stop_loss_*` wird von 17
    # Modulen gelesen, darunter `backward_tracking` - die Erfolgsmessung. Sie
    # haette jedes Rollen-Signal an einem Stop gemessen, der nie empfohlen
    # wurde, und die Trefferbilanz waere systematisch zu schlecht ausgefallen.
    #
    # DER STOP IST EIN PUNKT, KEINE ZONE. `rechne()` liefert fuer Einstieg und
    # Ziel je eine Spanne, fuer den Stop bewusst nur einen Wert - eine Marke,
    # an der geschlossen wird, hat keine zwei Kanten. `von` und `bis` tragen
    # ihn deshalb beide; `backward_tracking._zonen_schwelle()` bekommt damit
    # zwei gleiche Kanten und keine Zweideutigkeit.
    #
    # DAS MODELL BLEIBT RUECKFALL - fuer Zeilen ohne Rechnung. Und seine
    # Zahlen sind nicht verloren: `umgeworfen_preis_eur` steht daneben und
    # geht als EINGABE in genau diesen Stop ein.
    _geo = {}
    if rechnung:
        _geo = {
            "einstieg_von": rechnung.get("einstieg_von_eur"),
            "einstieg_bis": rechnung.get("einstieg_bis_eur"),
            "stop_von": rechnung.get("stop_eur"),
            "stop_bis": rechnung.get("stop_eur"),
            "ziel_von": rechnung.get("ziel_von_eur"),
            "ziel_bis": rechnung.get("ziel_bis_eur"),
        }
    for feld, eur_spalte, usd_spalte in (
            ("einstieg", "entry_eur", "entry_usd"),
            ("stop", "stop_loss_eur", "stop_loss_usd"),
            ("ziel", "take_profit_eur", "take_profit_usd")):
        for rand in ("von", "bis"):
            wert = _geo.get(f"{feld}_{rand}")
            if wert is None:
                wert = antwort.get(f"{feld}_eur_{rand}")
            if wert is None:
                continue
            aus[f"{eur_spalte}_{rand}"] = wert
            if eur_je_usd:
                aus[f"{usd_spalte}_{rand}"] = round(float(wert) / float(eur_je_usd), 8)
    if eur_je_usd:
        aus["fx_eur_je_usd"] = float(eur_je_usd)
    # DIE DREI FAMILIEN, wenn sie gerechnet wurden. `werte_aus_reihe()` liefert
    # `None`, solange die Reihe zu kurz fuer einen Rang ist - dann bleibt die
    # Spalte leer, und `merkmale()` legt sie in ein eigenes Band. Eine 0 waere
    # hier eine Aussage ("niedrigstes Perzentil"), die niemand gemessen hat.
    for name in ("schwankung_perzentil", "momentum_perzentil",
                 "volumen_perzentil"):
        wert = (familien or {}).get(name)
        if wert is not None:
            aus[name] = float(wert)
    return {k: v for k, v in aus.items() if v is not None}


def schreibe_signal(conn: sqlite3.Connection, felder: dict, *,
                    symbol: str, erstellt_am: str | None = None) -> int:
    """Eine Signalzeile aus der Rollen-Kette. Gibt die Kennung zurueck.

    WARUM HIER UND NICHT `db.insert_signal()` - das ist der Kern:
    `db._SIGNAL_COLUMNS` kennt KEINE der elf Spalten, die dieses Modul anlegt.
    Der Weg ueber die alte Funktion wuerde `quelle_kette`, `lagebild_id`,
    `umgeworfen_*`, `unabhaengige_faktoren` und die drei Familien
    STILLSCHWEIGEND fallen lassen - und zwar ohne Fehler, weil sie schlicht
    nicht in der Spaltenliste stehen. Die Spalten existieren seit dem 13.08.,
    der Export exportiert sie, eine Pruefung bestaetigt den Export - und
    fuellen konnte sie bis heute niemand.

    `models.Signal` bleibt bewusst unangetastet: die alte Kette baut dieses
    Objekt an sechs Stellen, und eine Erweiterung dort haette sechs
    Aufrufer zu tragen, die von der neuen Kette nichts wissen.

    SCHREIBT NUR, WAS ES KENNT. Die Spaltenliste kommt aus der Tabelle selbst,
    nicht aus einer Konstante hier - so kann diese Funktion nicht an einer
    Spalte scheitern, die eine spaetere Migration wieder entfernt, und sie
    kann auch keine erfinden."""
    migriere(conn)
    vorhanden = {r[1] for r in conn.execute("PRAGMA table_info(signals)")}
    werte = {k: v for k, v in (felder or {}).items()
             if k in vorhanden and v is not None}

    # DIE PFLICHTFELDER DER TABELLE. Ohne sie schlaegt der INSERT fehl, und
    # zwar erst zur Laufzeit im Betrieb - deshalb hier gesetzt, nicht gehofft.
    werte["symbol"] = symbol
    werte["created_at"] = erstellt_am or datetime.now(timezone.utc).isoformat()
    werte.setdefault("facts_json", "{}")
    # `gate_passed` MEINT IN DIESER KETTE ETWAS ANDERES als in der alten, und
    # das gehoert hierher statt in eine Auswertung: geschrieben wird eine Zeile
    # nur, wenn sie alle VERWERFENDEN Stufen des Gates passiert hat (Auftrag
    # bis Risikoschicht). Der Entscheider zaehlt nur und nimmt nichts heraus -
    # eine Zeile mit `gate_passed = 1` kann sich also trotzdem nicht tragen.
    # `quelle_kette` trennt beide Bedeutungen fuer jede spaetere Abfrage.
    werte.setdefault("gate_passed", 1)
    werte.setdefault("quelle_kette", "rollen")

    spalten = list(werte)
    cur = conn.execute(
        f"INSERT INTO signals ({', '.join(spalten)}) "
        f"VALUES ({', '.join('?' for _ in spalten)})",
        [werte[s] for s in spalten])
    conn.commit()
    return int(cur.lastrowid)
