# -*- coding: utf-8 -*-
"""Von der Rollen-Kette in die Tabelle `signals` (Paket 6, 12.08.2026).

DIE FUENF ECKPUNKTE, alle an der Quelle gemessen:

1  DAS AKTIONS-VOKABULAR DECKT SICH NUR ZU DREI VON FUENF.

       gemeinsam   KAUFEN · NACHKAUFEN · VERKAUFEN
       nur alt     HALTEN · TAUSCHEN
       nur neu     NICHTS_TUN · REDUZIEREN

   ENTSCHEIDUNG: erweitern, nicht abbilden. `HALTEN` und `NICHTS_TUN` sind
   NICHT dasselbe - HALTEN heisst "den Bestand behalten", NICHTS_TUN heisst
   auch "nicht kaufen". Wer beides in eine Spalte wirft, kann hinterher nie
   mehr unterscheiden, ob das System eine Position gehalten oder einen Einstieg
   verweigert hat. Genau diese Unterscheidung ist der Deadloop.
   `signals.action` traegt keine CHECK-Bedingung (geprueft) - die Erweiterung
   kostet keine Tabellenumstellung.

2  FUENF FELDER HATTEN KEIN ZUHAUSE. Sie bekommen eigene Spalten, additiv und
   idempotent wie jede Migration hier.

3  NUR FUENF SPALTEN SIND PFLICHT: symbol, created_at, action, gate_passed,
   facts_json. `confidence_pct` ist nullable - die neue Kette darf also NULL
   schreiben, ohne dass etwas bricht. Dass die E-Mail "Konfidenz X %" in eine
   Ueberschrift schreibt, ist ein Anzeigeproblem und gehoert zu Paket 12.

4  `facts_json` WAR BEI 78 VON 118 SIGNALEN LEER. Die Fakten, auf denen die
   Empfehlung steht, fehlten bei zwei Dritteln. Fuer die neue Kette ist das
   Pflicht: der Faktensatz, den das Modell gesehen hat, wird MITGESCHRIEBEN.
   Ohne ihn ist eine Empfehlung im Nachhinein nicht mehr pruefbar - und der
   Nutzer hat mehrfach verlangt, die Grundlage zu sehen.

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
AKTIONEN_NEU = ("KAUFEN", "NACHKAUFEN", "NICHTS_TUN", "REDUZIEREN", "VERKAUFEN")
AKTIONEN = tuple(sorted(set(AKTIONEN_ALT) | set(AKTIONEN_NEU)))

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
                            prompt_stand: str | None = None) -> dict:
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
        "action": aktion,
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
    for feld, spalten in (("einstieg", "entry_eur"), ("stop", "stop_loss_eur"),
                          ("ziel", "take_profit_eur")):
        for rand in ("von", "bis"):
            wert = antwort.get(f"{feld}_eur_{rand}")
            if wert is not None:
                aus[f"{spalten}_{rand}"] = wert
    return {k: v for k, v in aus.items() if v is not None}
