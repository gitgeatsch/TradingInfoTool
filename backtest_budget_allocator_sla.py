# -*- coding: utf-8 -*-
"""Historischer Backtest (2026-07-21, Nutzer-Vorgabe "umfangreich testen vor
finaler Umsetzung"): spielt den neuen SLA-basierten Auswahlalgorithmus fuer
den Budget-Allocator (siehe Plan-Datei swift-napping-muffin.md) gegen die
ECHTEN historischen hebel_triggers/marktscan_candidates-Daten nach, BEVOR
irgendein Produktivcode geaendert wird.

Liest die von extract_notebook_diagnose.py exportierte
K:/My Drive/Claude_Austauschordner/Notebook_Analysedaten/notebook_diagnose.json
(Sektion `rohdaten_fuer_backtest` + `hebel_signals` fuer die echten
historischen Verarbeitungszeitpunkte), baut daraus eine In-Memory-SQLite-DB
und ruft DIESELBEN database/db.py-Funktionen auf wie der (geplante) Live-
Allocator (get_hebel_wartezeit_stunden_je_paar()/get_marktscan_wartezeit_
stunden_je_coin(), ueber deren as_of-Parameter) - eine Quelle der Wahrheit,
kein Doppelcode.

Simulationsprinzip (Discrete-Event, chronologisch):
- Zyklus-Zeitpunkte = alle echten screened_at-Zeitstempel aus den Hebel-
  Trigger-Kandidaten (das ist der reale ~15-Min-Takt, zu dem auch der
  Allocator lief - Marktscan-Kandidaten werden vom Allocator ebenfalls bei
  JEDEM dieser Zyklen neu betrachtet, auch wenn ihre eigene Discovery nur
  2x/Tag passiert).
- Je Zyklus T: wartender Pool = get_hebel_wartezeit_stunden_je_paar(sim_conn,
  as_of=T) gegen eine SIMULIERTE hebel_signals-Tabelle (beginnt leer, waechst
  nur durch simulierte Verarbeitungen - NICHT die echten historischen
  Zeitpunkte, sonst koennte man ja nie eine FRUEHERE Verarbeitung testen).
- Kapazitaet je Zyklus = Anzahl ECHTER Signale, die historisch in diesem
  Zeitfenster tatsaechlich verarbeitet wurden (reale Kapazitaet nachgebildet,
  nicht neu erfunden - siehe _kapazitaet_je_zyklus()).
- Auswahlregel: ueberfaellig (Wartezeit >= SLA) zuerst nach Wartezeit
  absteigend, dann normal nach score_gesamt absteigend - identisch zur
  geplanten Produktivlogik (_priorisiere_nach_wartezeit() in
  agent/krypto/budget_allocator.py, zum Zeitpunkt dieses Backtests noch
  NICHT implementiert - Reihenfolge bewusst: erst Backtest, dann Code).
- Ausgewaehlte Kandidaten werden in die simulierte hebel_signals-Tabelle
  eingetragen (created_at=T) - das ist ihre NEUE simulierte
  Verarbeitungszeit, aus der sich die neue Wartezeit ergibt.

BEWUSSTE VEREINFACHUNG (siehe Plan-Datei): der Portfolio-Bonus (bereits
gehalten/rolle=core) wird in diesem ersten Backtest-Durchlauf NICHT
simuliert, da dafuer eine historische Bestands-/Watchlist-Zeitreihe noetig
waere, die nicht exportiert wird (der Holdings-Export zeigt nur den
AKTUELLEN Stand). Der Backtest testet damit den Kern-Mechanismus (SLA-
Reservierung/FIFO unter Ueberfaelligen) - der Bonus wuerde reale Kandidaten
nur noch STAERKER in Richtung "schneller dran" verschieben, nie schwaecher
als hier simuliert.

Aufruf: python backtest_budget_allocator_sla.py [HEBEL_SLA_STUNDEN] [MARKTSCAN_SLA_STUNDEN]
  (beide optional, Default 6 / 30 - siehe config.yaml::budget_allocator)
"""
import bisect
import json
import sqlite3
import sys
from pathlib import Path

import database.db as db

HEBEL_SLA_STUNDEN = float(sys.argv[1]) if len(sys.argv) > 1 else 6.0
MARKTSCAN_SLA_STUNDEN = float(sys.argv[2]) if len(sys.argv) > 2 else 30.0


def _finde_export() -> Path:
    """Gleiches Laufwerksbuchstaben-Problem wie extract_notebook_diagnose.py::
    _google_drive_wurzel() - Desktop/Notebook nutzen unterschiedliche
    Laufwerksbuchstaben fuer Google Drive."""
    for laufwerk in ("K", "G", "H", "E", "F"):
        for ordner in ("My Drive", "Meine Ablage"):
            pfad = Path(f"{laufwerk}:/{ordner}/Claude_Austauschordner/Notebook_Analysedaten/notebook_diagnose.json")
            if pfad.exists():
                return pfad
    raise FileNotFoundError(
        "notebook_diagnose.json nicht gefunden - bitte extract_notebook_diagnose.py "
        "zuerst (erneut) laufen lassen und synchronisieren."
    )


def _baue_simulations_db(rohdaten: dict) -> sqlite3.Connection:
    """Minimale In-Memory-Schema-Teilmenge - nur die Spalten, die
    get_hebel_wartezeit_stunden_je_paar()/get_marktscan_wartezeit_stunden_je_coin()
    tatsaechlich lesen (siehe database/db.py). hebel_signals bleibt bewusst
    LEER (siehe Modul-Docstring) - wird erst durch die Simulation selbst
    befuellt."""
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.executescript(
        """
        CREATE TABLE hebel_triggers (
            id INTEGER, symbol TEXT, richtung TEXT, screened_at TEXT,
            score_gesamt REAL, ist_kandidat INTEGER, status TEXT
        );
        CREATE TABLE hebel_signals (
            symbol TEXT, richtung TEXT, created_at TEXT, hebel_trigger_id INTEGER
        );
        CREATE TABLE marktscan_candidates (
            id INTEGER, coingecko_id TEXT, symbol TEXT, discovered_at TEXT,
            score_gesamt REAL, status TEXT, einstufung TEXT, groq_generiert_am TEXT
        );
        """
    )
    for row in rohdaten["hebel_triggers_kandidaten"]:
        conn.execute(
            "INSERT INTO hebel_triggers (id, symbol, richtung, screened_at, score_gesamt, ist_kandidat, status) "
            "VALUES (?, ?, ?, ?, ?, 1, ?)",
            (row["id"], row["symbol"], row["richtung"], row["screened_at"], row["score_gesamt"], row["status"]),
        )
    for row in rohdaten["marktscan_kaufkandidaten"]:
        conn.execute(
            "INSERT INTO marktscan_candidates "
            "(id, coingecko_id, symbol, discovered_at, score_gesamt, status, einstufung, groq_generiert_am) "
            "VALUES (?, ?, ?, ?, ?, ?, 'kaufkandidat', ?)",
            (row["id"], row["coingecko_id"], row["symbol"], row["discovered_at"],
             row["score_gesamt"], row["status"], row["groq_generiert_am"]),
        )
    conn.commit()
    return conn


def _kapazitaet_je_zyklus(zeitpunkte: list[str], zyklen: list[str]) -> dict[str, int]:
    """Zaehlt, wie viele echte Verarbeitungen jeweils dem naechstgelegenen
    (>=) Zyklus zugerechnet werden - reale Kapazitaet nachgebildet statt neu
    erfunden. ISO-8601-Strings mit fixem UTC-Offset sind lexikographisch
    chronologisch sortierbar - bisect auf Strings direkt, kein Parsing
    noetig (schnell genug fuer mehrere tausend Zyklen/Zeitpunkte)."""
    kapazitaet = {z: 0 for z in zyklen}
    for zp in zeitpunkte:
        idx = bisect.bisect_left(zyklen, zp)
        if idx < len(zyklen):
            kapazitaet[zyklen[idx]] += 1
    return kapazitaet


def _priorisiere(kandidaten_mit_score: list[tuple], wartezeiten: dict, sla_stunden: float) -> list[tuple]:
    """Identischer Algorithmus zur geplanten Produktivfunktion
    _priorisiere_nach_wartezeit() in agent/krypto/budget_allocator.py (zum
    Zeitpunkt dieses Backtests noch nicht implementiert) - eigenstaendige
    Kopie hier, damit der Backtest unabhaengig von der spaeteren
    Implementierung lauffaehig bleibt. `kandidaten_mit_score`:
    [(schluessel, score_gesamt), ...]."""
    ueberfaellig = [k for k in kandidaten_mit_score if wartezeiten.get(k[0], 0.0) >= sla_stunden]
    normal = [k for k in kandidaten_mit_score if wartezeiten.get(k[0], 0.0) < sla_stunden]
    ueberfaellig.sort(key=lambda k: wartezeiten.get(k[0], 0.0), reverse=True)
    normal.sort(key=lambda k: k[1] or 0.0, reverse=True)
    return ueberfaellig + normal


def _simuliere_hebel(sim_conn: sqlite3.Connection, zyklen: list[str], kapazitaet: dict[str, int]) -> list[dict]:
    ergebnisse = []
    for zyklus in zyklen:
        wartezeiten = db.get_hebel_wartezeit_stunden_je_paar(sim_conn, as_of=zyklus)
        n = kapazitaet.get(zyklus, 0)
        if not wartezeiten or n == 0:
            continue
        kandidaten = []
        for paar in wartezeiten:
            symbol, richtung = paar
            row = sim_conn.execute(
                "SELECT score_gesamt FROM hebel_triggers WHERE symbol = ? AND richtung = ? "
                "AND screened_at <= ? ORDER BY screened_at DESC LIMIT 1",
                (symbol, richtung, zyklus),
            ).fetchone()
            kandidaten.append((paar, row["score_gesamt"] if row else 0.0))
        for (symbol, richtung), _score in _priorisiere(kandidaten, wartezeiten, HEBEL_SLA_STUNDEN)[:n]:
            ergebnisse.append({
                "symbol": symbol, "richtung": richtung, "simulierter_verarbeitungszeitpunkt": zyklus,
                "simulierte_wartezeit_stunden": round(wartezeiten[(symbol, richtung)], 1),
            })
            sim_conn.execute(
                "INSERT INTO hebel_signals (symbol, richtung, created_at, hebel_trigger_id) VALUES (?, ?, ?, 1)",
                (symbol, richtung, zyklus),
            )
        sim_conn.commit()
    return ergebnisse


def _simuliere_marktscan(sim_conn: sqlite3.Connection, zyklen: list[str], kapazitaet: dict[str, int]) -> list[dict]:
    ergebnisse = []
    for zyklus in zyklen:
        wartezeiten = db.get_marktscan_wartezeit_stunden_je_coin(sim_conn, as_of=zyklus)
        n = kapazitaet.get(zyklus, 0)
        if not wartezeiten or n == 0:
            continue
        kandidaten = []
        symbol_je_coin = {}
        for coingecko_id in wartezeiten:
            row = sim_conn.execute(
                "SELECT symbol, score_gesamt FROM marktscan_candidates WHERE coingecko_id = ? "
                "AND discovered_at <= ? ORDER BY discovered_at DESC LIMIT 1",
                (coingecko_id, zyklus),
            ).fetchone()
            kandidaten.append((coingecko_id, row["score_gesamt"] if row else 0.0))
            symbol_je_coin[coingecko_id] = row["symbol"] if row else coingecko_id
        for coingecko_id, _score in _priorisiere(kandidaten, wartezeiten, MARKTSCAN_SLA_STUNDEN)[:n]:
            ergebnisse.append({
                "coingecko_id": coingecko_id, "symbol": symbol_je_coin.get(coingecko_id),
                "simulierter_verarbeitungszeitpunkt": zyklus,
                "simulierte_wartezeit_stunden": round(wartezeiten[coingecko_id], 1),
            })
            sim_conn.execute(
                "UPDATE marktscan_candidates SET groq_generiert_am = ? "
                "WHERE coingecko_id = ? AND discovered_at <= ? AND groq_generiert_am IS NULL",
                (zyklus, coingecko_id, zyklus),
            )
        sim_conn.commit()
    return ergebnisse


def _statistik(werte: list[float]) -> dict:
    if not werte:
        return {
            "anzahl": 0, "min_stunden": None, "max_stunden": None,
            "median_stunden": None, "durchschnitt_stunden": None,
        }
    sortiert = sorted(werte)
    n = len(sortiert)
    return {
        "anzahl": n, "min_stunden": round(sortiert[0], 1), "max_stunden": round(sortiert[-1], 1),
        "median_stunden": round(sortiert[n // 2], 1), "durchschnitt_stunden": round(sum(sortiert) / n, 1),
    }


def main() -> None:
    export_pfad = _finde_export()
    print(f"Lade Export: {export_pfad}")
    with export_pfad.open(encoding="utf-8") as f:
        export = json.load(f)

    rohdaten = export["rohdaten_fuer_backtest"]
    hebel_zyklen = sorted({r["screened_at"] for r in rohdaten["hebel_triggers_kandidaten"]})
    echte_hebel_zeitpunkte = sorted(
        s["created_at"] for s in export["hebel_signals"] if s.get("hebel_trigger_id") is not None
    )
    echte_marktscan_zeitpunkte = sorted(
        row["groq_generiert_am"] for row in rohdaten["marktscan_kaufkandidaten"] if row.get("groq_generiert_am")
    )
    hebel_kapazitaet = _kapazitaet_je_zyklus(echte_hebel_zeitpunkte, hebel_zyklen)
    marktscan_kapazitaet = _kapazitaet_je_zyklus(echte_marktscan_zeitpunkte, hebel_zyklen)

    print(f"{len(hebel_zyklen)} Zyklen rekonstruiert, "
          f"{len(rohdaten['hebel_triggers_kandidaten'])} Hebel-Trigger-Zeilen, "
          f"{len(rohdaten['marktscan_kaufkandidaten'])} Marktscan-Zeilen, "
          f"{len(echte_hebel_zeitpunkte)} echte Hebel-Signale, "
          f"{len(echte_marktscan_zeitpunkte)} echte Marktscan-Bewertungen.")
    print(f"HEBEL_SLA_STUNDEN={HEBEL_SLA_STUNDEN}, MARKTSCAN_SLA_STUNDEN={MARKTSCAN_SLA_STUNDEN}")

    sim_conn = _baue_simulations_db(rohdaten)
    hebel_ergebnisse = _simuliere_hebel(sim_conn, hebel_zyklen, hebel_kapazitaet)
    marktscan_ergebnisse = _simuliere_marktscan(sim_conn, hebel_zyklen, marktscan_kapazitaet)
    sim_conn.close()

    print()
    print("=== SIMULIERT (neuer SLA-Algorithmus) ===")
    print("Hebel:", _statistik([e["simulierte_wartezeit_stunden"] for e in hebel_ergebnisse]))
    print("Marktscan:", _statistik([e["simulierte_wartezeit_stunden"] for e in marktscan_ergebnisse]))

    print()
    print("=== IST (heutiger Algorithmus, aus notebook_diagnose.json) ===")
    print("Hebel (Stunden):", export.get("hebel_erstmalige_erkennung_delta", {}).get("statistik"))
    print("Marktscan (Minuten, /60 fuer Stunden):", export.get("marktscan_discovery_llm_delta", {}).get("statistik"))

    print()
    print("Top 10 groesste SIMULIERTE Hebel-Wartezeiten:")
    for e in sorted(hebel_ergebnisse, key=lambda x: -x["simulierte_wartezeit_stunden"])[:10]:
        print(" ", e)
    print("Top 10 groesste SIMULIERTE Marktscan-Wartezeiten:")
    for e in sorted(marktscan_ergebnisse, key=lambda x: -x["simulierte_wartezeit_stunden"])[:10]:
        print(" ", e)


if __name__ == "__main__":
    main()
