"""'Letzte Bewertung'-Anzeige (2026-07-16, Klassifikations-Redesign, Nutzer-
Wunsch: "ein Textfeld je Asset, das die letzte aktuelle Bewertung kurz-/
mittel-/langfristig mitfuehrt - Ergebnisse der LLM-Abfragen?"). Kein neues
Feld/keine neue Datenspeicherung noetig - die Daten existieren bereits pro
Signal (long_reasoning.technisch/fundamental/makro, top_gruende), sowohl fuer
Spot-Krypto (agent/krypto/analyst.py) als auch Aktien (agent/aktien/
analyst.py, identisches Schema). Diese Datei liefert nur die fehlende
Anzeige-Oberflaeche - eine kompakte Uebersicht des JEWEILS LETZTEN echten
Signals je Symbol, statt dass der Nutzer sich durch die Signal-Historie
klicken muss. Wiederverwendet von ui/portfolio.py (gehaltene Assets) UND
ui/signals_view.py (auch nicht gehaltene Watchlist-Kandidaten)."""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk

import database.db as db


def show_letzte_bewertung(parent, db_conn_factory, symbol: str) -> None:
    conn = db_conn_factory()
    try:
        latest = db.get_latest_real_signal_per_symbol(conn).get(symbol)
    finally:
        conn.close()

    dialog = tk.Toplevel(parent)
    dialog.title(f"Letzte Bewertung: {symbol}")
    dialog.resizable(False, False)
    dialog.transient(parent)

    frame = ttk.Frame(dialog, padding=12)
    frame.pack(fill="both", expand=True)

    if latest is None:
        ttk.Label(frame, text=f"Für {symbol} liegt noch keine echte KI-Analyse vor.").pack(anchor="w")
        ttk.Button(frame, text="Schließen", command=dialog.destroy).pack(anchor="e", pady=(10, 0))
        return

    when = latest.created_at[:16].replace("T", " ") if latest.created_at else "-"
    ttk.Label(
        frame, text=f"{symbol} — letzte Analyse vom {when} ({latest.action}, {latest.confidence_pct or '-'}% Konfidenz)",
        font=("", 10, "bold"), wraplength=480,
    ).pack(anchor="w", pady=(0, 8))

    sections = [
        ("Kurz-/mittelfristig (technisch)", latest.long_reasoning_technisch),
        ("Langfristig (fundamental)", latest.long_reasoning_fundamental),
        ("Makro/Regime", latest.long_reasoning_makro),
    ]
    for title, text in sections:
        if not text:
            continue
        ttk.Label(frame, text=title, font=("", 9, "bold")).pack(anchor="w", pady=(6, 0))
        ttk.Label(frame, text=text, wraplength=480, justify="left").pack(anchor="w")

    ttk.Button(frame, text="Schließen", command=dialog.destroy).pack(anchor="e", pady=(10, 0))
