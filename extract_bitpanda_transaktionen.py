"""Rohexport der Bitpanda-Transaktionshistorie fuer die Portfolio-Wert-
Rekonstruktion (Task #612, Z-3/RM-7 Drawdown-Notbremse).

AM NOTEBOOK AUSFUEHREN:
    python export_bitpanda_transaktionen.py

Schreibt nach K:/My Drive/Claude_Austauschordner/Notebook_Analysedaten/
(bzw. den erkannten Drive-Buchstaben) - derselbe Ordner wie
extract_notebook_diagnose.py.

WARUM DIESER EXPORT
`holdings` ist eine Zustandstabelle: symbol als PRIMARY KEY, jeder Sync
ueberschreibt sie. Der Verlauf der Bestaende existiert nirgends in der DB.
Ohne ihn laesst sich kein Portfoliowert je Tag berechnen, ohne den wiederum
Z-3 nicht gebaut werden kann ("OFFEN - fehlt noch eine Portfolio-Wert-
Historie", Regelwerksmanual).

Ein erster Plan wollte den heutigen Bestand rueckwaerts fortschreiben. Das ist
hinfaellig: die Bitpanda-Aktivitaet zeigt Handel bis zum 1. August, das Fenster
unveraenderter Bestaende betraegt also nur wenige Tage. Es fuehrt kein Weg an
den echten Transaktionen vorbei.

NUR LESEND. Das Skript ruft ausschliesslich GET-Endpunkte und veraendert weder
die Datenbank noch irgendetwas bei Bitpanda.

DER BESTANDS-SCHNAPPSCHUSS IST KEIN BEIWERK
Mitexportiert werden die AKTUELLEN holdings - im selben Lauf, also zum selben
Zeitpunkt wie die Transaktionen. Das ist der Pruefstein der ganzen
Rekonstruktion: rechnet man die Transaktionen von vorne durch, MUSS am Ende
holdings.quantity herauskommen. Trifft man es nicht, ist auch jeder
historische Tageswert falsch - und das faellt so schon vor dem Einsatz auf,
nicht erst hinterher. Ein spaeter gezogener Bestand taugt dafuer nicht, weil
zwischenzeitliche Trades die Differenz erklaeren wuerden.

BEKANNTER FALLSTRICK (steht schon in importer/bitpanda_avg_cost.py):
holdings.quantity enthaelt Einheiten, die NIE ueber einen bepreisten Trade
liefen - Staking-Gutschriften, externe Einzahlungen. Deshalb exportiert dieses
Skript ALLE Transaktionsarten und filtert nichts weg, auch nicht die ohne
trade-Unterobjekt.
"""
from __future__ import annotations

import json
import os
import sys
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import database.db as db
from api.bitpanda import get_wallet_transactions
from extract_notebook_diagnose import ZIEL_ORDNER

DATEINAME = "bitpanda_transaktionen.json"


def _api_key() -> str:
    """API-Key aus der Umgebung oder .env. Bewusst ohne python-dotenv-
    Abhaengigkeit: das Skript soll am Notebook laufen, ohne dass dort erst
    etwas nachinstalliert werden muss."""
    key = os.environ.get("BITPANDA_API_KEY")
    if key:
        return key.strip()
    env_datei = Path(__file__).resolve().parent / ".env"
    if env_datei.exists():
        for zeile in env_datei.read_text(encoding="utf-8").splitlines():
            zeile = zeile.strip()
            if zeile.startswith("BITPANDA_API_KEY") and "=" in zeile:
                return zeile.split("=", 1)[1].strip().strip("\"'")
    raise SystemExit(
        "BITPANDA_API_KEY nicht gefunden - weder in der Umgebung noch in .env.\n"
        "Ohne Key kann die Transaktionshistorie nicht abgerufen werden."
    )


def _fortschritt(geladen: int, gesamt: int) -> None:
    # Bis zu ~9500 Transaktionen, seitenweise - ohne Ausgabe saehe ein langer
    # Erstlauf wie ein Haenger aus.
    print(f"  ... {geladen} von {gesamt} Transaktionen geladen", flush=True)


def main() -> None:
    print("Bitpanda-Transaktionsexport (Task #612)")
    print("Nur lesend - es wird nichts veraendert.\n")

    key = _api_key()
    print("Rufe Transaktionshistorie ab (das kann einige Minuten dauern)...")
    transaktionen = get_wallet_transactions(key, on_page_fetched=_fortschritt)
    print(f"{len(transaktionen)} Transaktionen geladen.\n")

    zeilen = []
    for t in transaktionen:
        zeile = asdict(t)
        # ISO-Datum aus dem Unix-Zeitstempel, damit sich der Export ohne
        # Umrechnung gegen price_history/price_history_ohlc joinen laesst
        # (beide fuehren `date` als YYYY-MM-DD, UTC).
        zeile["datum_utc"] = datetime.fromtimestamp(
            t.unix_timestamp, tz=timezone.utc
        ).strftime("%Y-%m-%d")
        zeilen.append(zeile)

    # Bestands-Schnappschuss aus DEMSELBEN Lauf - siehe Modul-Docstring.
    conn = db.get_connection()
    try:
        holdings = [
            {
                "symbol": h.symbol,
                "quantity": h.quantity,
                "staked_quantity": getattr(h, "staked_quantity", None),
                "updated_at": h.updated_at,
                "source": h.source,
            }
            for h in db.get_all_holdings(conn)
        ]
    finally:
        conn.close()

    # Tag-Inventar: welche short_names kommen tatsaechlich vor und wie oft?
    # Die Auswertung muss Margin-Buchungen (eigene Wallets, eigene Tabelle
    # hebel_positions) von Spot trennen und Swaps als PAAR erkennen. Welche
    # Tag-Namen die API dafuer genau liefert, soll aus den Daten kommen und
    # nicht aus meiner Vermutung.
    tag_inventar: dict[str, int] = {}
    typ_inventar: dict[str, int] = {}
    for t in transaktionen:
        typ_inventar[t.type] = typ_inventar.get(t.type, 0) + 1
        for tag in t.tags:
            tag_inventar[tag] = tag_inventar.get(tag, 0) + 1

    payload = {
        "erzeugt_am": datetime.now(timezone.utc).isoformat(),
        "zweck": "Portfolio-Wert-Rekonstruktion fuer Z-3/RM-7 (Task #612)",
        "transaktionen_anzahl": len(zeilen),
        "transaktionen": zeilen,
        "holdings_schnappschuss": holdings,
        "tag_inventar": dict(sorted(tag_inventar.items(), key=lambda x: -x[1])),
        "typ_inventar": dict(sorted(typ_inventar.items(), key=lambda x: -x[1])),
    }

    ZIEL_ORDNER.mkdir(parents=True, exist_ok=True)
    ziel = ZIEL_ORDNER / DATEINAME
    ziel.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False, default=str), encoding="utf-8"
    )

    print(f"Geschrieben: {ziel}")
    print(f"  Groesse: {ziel.stat().st_size / 1024 / 1024:.1f} MB")
    print(f"  Transaktionen: {len(zeilen)}")
    print(f"  Holdings im Schnappschuss: {len(holdings)}")
    if zeilen:
        daten = [z["datum_utc"] for z in zeilen]
        print(f"  Zeitraum: {min(daten)} bis {max(daten)}")
    print("\nTyp-Inventar:")
    for typ, anzahl in payload["typ_inventar"].items():
        print(f"  {typ:24s} {anzahl}")
    print("\nTag-Inventar:")
    for tag, anzahl in payload["tag_inventar"].items():
        print(f"  {tag:24s} {anzahl}")
    print("\nFertig. Die Datei liegt im Austauschordner und wird ueber Drive synchronisiert.")


if __name__ == "__main__":
    main()
