# -*- coding: utf-8 -*-
"""Einmal-Diagnoseskript (2026-07-17): breiter Gesundheits-/Optimierungs-Export
seit dem heutigen Notebook-Neustart + Sync (Mistral-Integration, RM-4,
selektiver Holdings-Sync, Long/Short-Bugfix), PLUS Einzelfall-Tiefenanalyse
fuer ein Symbol (Standard: LINK, siehe Hebelverhalten-Diskussion).

Ziel laut Nutzer: primaer Bugs/Fehler identifizieren, sekundaer Ansatzpunkte
fuer LLM-Budget/Parameter-Optimierung und praezisere Empfehlungen liefern -
deshalb rohe, aber vollstaendige Daten statt vorgefertigter Schlussfolgerungen,
die Bewertung passiert danach gemeinsam.

Aufruf am Notebook: python extract_notebook_diagnose.py [SYMBOL]
  (SYMBOL optional, Default LINK, fuer den Tiefenanalyse-Teil)
Schreibt nach K:/My Drive/Claude_Austauschordner/Notebook_Analysedaten/
"""
import json
import sys
from collections import Counter
from pathlib import Path

import database.db as db
from agent.krypto.backward_tracking import compute_provider_performance
from agent.krypto.regime import get_last_known_regime_status

DEEP_DIVE_SYMBOL = sys.argv[1] if len(sys.argv) > 1 else "LINK"
ZIEL_ORDNER = Path("K:/My Drive/Claude_Austauschordner/Notebook_Analysedaten")

# Bewusst schlanke Spaltenauswahl fuer signals/hebel_signals - die langen
# facts_json/*_raw_response-Felder sind redundant zu den strukturierten
# Feldern und blaehen die Datei unnoetig auf.
_HEBEL_SIGNAL_SPALTEN = (
    "id, symbol, created_at, richtung, action, hebel_vorschlag, hebel_final, "
    "hebel_korrektur_hinweis, trade_thesis_typ, trigger_zweig, trigger_score, "
    "confidence_pct, short_reasoning, entry_eur_von, entry_eur_bis, "
    "stop_loss_eur_von, stop_loss_eur_bis, take_profit_eur_von, take_profit_eur_bis, "
    "liquidationspreis_geschaetzt_usd, eigenkapitalbedarf_usd, ausfuehrbarkeit_hinweis, "
    "gate_passed, gate_reason, risk_veto, risk_veto_reason, llm_model, "
    "outcome_status, outcome_geprueft_am, outcome_realisiertes_crv"
)
_SPOT_SIGNAL_SPALTEN = (
    "id, symbol, created_at, action, confidence_pct, short_reasoning, "
    "entry_eur_von, entry_eur_bis, stop_loss_eur_von, stop_loss_eur_bis, "
    "take_profit_eur_von, take_profit_eur_bis, regime, gate_passed, gate_reason, "
    "risk_veto, risk_veto_reason, groq_model, outcome_status, outcome_geprueft_am, "
    "outcome_realisiertes_crv"
)


def row_to_dict(row) -> dict:
    return {k: row[k] for k in row.keys()}


def haeufigkeit(rows, feld: str) -> dict:
    zaehler = Counter(r[feld] for r in rows if r[feld])
    return dict(zaehler.most_common())


def main() -> None:
    conn = db.get_connection()
    try:
        # 1) Holdings-Check: hat der selektive Sync die Einstandspreise
        # korrekt uebernommen?
        holdings = conn.execute(
            "SELECT symbol, quantity, avg_buy_price_eur, avg_buy_price_manual_eur FROM holdings"
        ).fetchall()

        # 2) API-Gesundheit aller Quellen
        api_health = db.get_api_health_status(conn)

        # 3) Echte LLM-Aufrufe heute je Anbieter + Gesamtvolumen je Tier
        llm_calls_heute = {
            "groq": db.count_real_llm_calls_today_by_provider(conn, "groq:"),
            "mistral": db.count_real_llm_calls_today_by_provider(conn, "mistral:"),
            "cerebras": db.count_real_llm_calls_today_by_provider(conn, "cerebras:"),
            "gemini": db.count_real_llm_calls_today_by_provider(conn, "gemini:"),
        }
        signal_volumen_heute = {
            "spot": db.count_real_signals_today(conn),
            "hebel": db.count_real_hebel_signals_today(conn),
            "marktscan_writeups": db.count_real_marktscan_writeups_today(conn),
        }

        # 4) Provider-Performance (Win-Rate/CRV je Anbieter, Spot+Hebel getrennt)
        provider_performance = compute_provider_performance(conn)

        # 5) Alle Hebel-Signale (fuer Long/Short-Bugfix-Verifikation +
        # Gate/Veto-Muster + Outcome-Verteilung)
        hebel_signals = conn.execute(
            f"SELECT {_HEBEL_SIGNAL_SPALTEN} FROM hebel_signals ORDER BY created_at ASC"
        ).fetchall()
        hebel_positions = conn.execute(
            "SELECT * FROM hebel_positions ORDER BY eroeffnet_am ASC"
        ).fetchall()

        # 6) Alle Spot-Signale (gleiche Fragestellung fuer die Spot-Seite)
        spot_signals = conn.execute(
            f"SELECT {_SPOT_SIGNAL_SPALTEN} FROM signals ORDER BY created_at ASC"
        ).fetchall()

        # 7) Regime-Status (laeuft der neue Tab/die Persistenz fehlerfrei?)
        regime_status = get_last_known_regime_status(conn)

        # 8) Einzelfall-Tiefenanalyse (Standard: LINK)
        deep_signale = conn.execute(
            "SELECT * FROM hebel_signals WHERE symbol = ? ORDER BY created_at ASC", (DEEP_DIVE_SYMBOL,)
        ).fetchall()
        deep_positionen = conn.execute(
            "SELECT * FROM hebel_positions WHERE symbol = ? ORDER BY eroeffnet_am ASC", (DEEP_DIVE_SYMBOL,)
        ).fetchall()
        deep_trigger = conn.execute(
            "SELECT * FROM hebel_triggers WHERE symbol = ? ORDER BY screened_at ASC", (DEEP_DIVE_SYMBOL,)
        ).fetchall()
        deep_preis = []
        if deep_signale:
            von = deep_signale[0]["created_at"][:10]
            deep_preis = conn.execute(
                "SELECT * FROM price_history_ohlc WHERE symbol = ? AND date >= ? ORDER BY date ASC",
                (DEEP_DIVE_SYMBOL, von),
            ).fetchall()
    finally:
        conn.close()

    hebel_rows = [row_to_dict(r) for r in hebel_signals]
    spot_rows = [row_to_dict(r) for r in spot_signals]

    payload = {
        "holdings_check": [row_to_dict(r) for r in holdings],
        "api_health": api_health,
        "llm_calls_heute": llm_calls_heute,
        "signal_volumen_heute": signal_volumen_heute,
        "provider_performance": provider_performance,
        "hebel_signals": hebel_rows,
        "hebel_positions": [row_to_dict(r) for r in hebel_positions],
        "spot_signals": spot_rows,
        "gate_veto_haeufigkeit": {
            "hebel_gate_reason": haeufigkeit(hebel_rows, "gate_reason"),
            "hebel_risk_veto_reason": haeufigkeit(hebel_rows, "risk_veto_reason"),
            "spot_gate_reason": haeufigkeit(spot_rows, "gate_reason"),
            "spot_risk_veto_reason": haeufigkeit(spot_rows, "risk_veto_reason"),
        },
        "regime_status": regime_status,
        "deep_dive": {
            "symbol": DEEP_DIVE_SYMBOL,
            "hebel_signals": [row_to_dict(r) for r in deep_signale],
            "hebel_positions": [row_to_dict(r) for r in deep_positionen],
            "hebel_triggers": [row_to_dict(r) for r in deep_trigger],
            "price_history_ohlc": [row_to_dict(r) for r in deep_preis],
        },
    }

    ZIEL_ORDNER.mkdir(parents=True, exist_ok=True)
    ziel_datei = ZIEL_ORDNER / "notebook_diagnose.json"
    ziel_datei.write_text(json.dumps(payload, indent=2, ensure_ascii=False, default=str), encoding="utf-8")

    print(f"Geschrieben: {ziel_datei}")
    print(f"  Holdings: {len(holdings)}, Hebel-Signale: {len(hebel_rows)}, "
          f"Spot-Signale: {len(spot_rows)}, Hebel-Positionen: {len(hebel_positions)}")
    print(f"  LLM-Calls heute: {llm_calls_heute}")
    print(f"  Deep-Dive ({DEEP_DIVE_SYMBOL}): {len(deep_signale)} Signale, "
          f"{len(deep_positionen)} Positionen, {len(deep_trigger)} Trigger, "
          f"{len(deep_preis)} Preispunkte")


if __name__ == "__main__":
    main()
