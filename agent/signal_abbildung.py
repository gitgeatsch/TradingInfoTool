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


def felder_aus_entscheidung(antwort: dict, *, fakten: dict,
                            lagebild_id: int | None = None,
                            prompt_stand: str | None = None,
                            eur_je_usd: float | None = None) -> dict:
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
        "umgeworfen_durch": antwort.get("umgeworfen_durch"),
        "umgeworfen_preis_eur": antwort.get("umgeworfen_preis_eur"),
        "umgeworfen_bis": antwort.get("umgeworfen_bis"),
        # DER FAKTENSATZ IST PFLICHT (Eckpunkt 4). Ohne ihn ist die Empfehlung
        # im Nachhinein nicht mehr pruefbar.
        "facts_json": json.dumps(fakten or {}, ensure_ascii=False),
        "position_size_eur": antwort.get("tranche_eur"),
    }
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
    for feld, eur_spalte, usd_spalte in (
            ("einstieg", "entry_eur", "entry_usd"),
            ("stop", "stop_loss_eur", "stop_loss_usd"),
            ("ziel", "take_profit_eur", "take_profit_usd")):
        for rand in ("von", "bis"):
            wert = antwort.get(f"{feld}_eur_{rand}")
            if wert is None:
                continue
            aus[f"{eur_spalte}_{rand}"] = wert
            if eur_je_usd:
                aus[f"{usd_spalte}_{rand}"] = round(float(wert) / float(eur_je_usd), 8)
    if eur_je_usd:
        aus["fx_eur_je_usd"] = float(eur_je_usd)
    return {k: v for k, v in aus.items() if v is not None}
