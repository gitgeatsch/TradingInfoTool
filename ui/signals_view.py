"""Signale-Tab (U-4): zeigt die zuletzt berechnete Empfehlung je Asset im P-5-Format
und erlaubt, die Agent-Pipeline (agent/pipeline.py) manuell fuer ein ausgewaehltes
Asset auszuloesen (Kap. 5). Bewusst NICHT automatisch/geplant - siehe Plan
(C:\\Users\\Geatsch\\.claude\\plans\\deep-launching-zebra.md), erst Kosten/Qualitaet/
Rate-Limits manuell pruefen, bevor das in den Scheduler wandert.

Threading: ein Pipeline-Lauf braucht mehrere Sekunden (Netzwerk + LLM) - synchron im
Tk-Main-Thread wuerde die UI einfrieren. Der Klick startet einen Daemon-Thread, der
die reine, UI-freie generate_signal() aufruft; das Ergebnis wird per self.after(0,...)
zurueck in den Main-Thread marshalt (Tkinter-Widgets duerfen nur dort angefasst werden).
"""
from __future__ import annotations

import threading
import tkinter as tk
from tkinter import ttk

import database.db as db
from ui.formatting import format_money

ACTION_COLORS = {
    "KAUFEN": "#1a7f37",
    "NACHKAUFEN": "#1a7f37",
    "VERKAUFEN": "#c0392b",
    "TAUSCHEN": "#8a5a00",
    "HALTEN": "#555555",
}
WARN_COLOR = "#b36b00"
INFO_COLOR = "#666666"


class SignalsView(ttk.Frame):
    def __init__(
        self, parent, db_conn_factory, watchlist, groq_client, coingecko_client, kraken_client,
        fred_api_key=None,
    ):
        super().__init__(parent)
        self._db_conn_factory = db_conn_factory
        self._full_watchlist = watchlist  # generate_signal braucht ALLE Assets (Stablecoins
        # zaehlen z.B. als Cash-Reserve in agent/risk_gate.py) - nur die Anzeige-Liste filtert.
        self._watchlist = [a for a in watchlist if a.typ != "stablecoin"]
        self._groq_client = groq_client
        self._coingecko_client = coingecko_client
        self._kraken_client = kraken_client
        self._fred_api_key = fred_api_key  # optional (P-8) - ohne Key liefert
        # agent/pipeline.py fuer die FRED-Felder sauber None statt abzustuerzen.
        self._selected_asset = None

        self._build_layout()
        self._refresh_list()

    def _build_layout(self) -> None:
        paned = ttk.Panedwindow(self, orient="horizontal")
        paned.pack(fill="both", expand=True, padx=8, pady=8)

        left = ttk.Frame(paned)
        paned.add(left, weight=1)

        columns = ("symbol", "name", "letztes_signal", "berechnet")
        self.tree = ttk.Treeview(left, columns=columns, show="headings", height=20)
        headings = {"symbol": "Symbol", "name": "Name", "letztes_signal": "Letztes Signal", "berechnet": "Berechnet"}
        for col in columns:
            self.tree.heading(col, text=headings[col])
            self.tree.column(col, width=110, anchor="w" if col in ("symbol", "name") else "center")
        self.tree.pack(fill="both", expand=True)
        self.tree.bind("<<TreeviewSelect>>", self._on_select)

        right = ttk.Frame(paned)
        paned.add(right, weight=3)

        toolbar = ttk.Frame(right)
        toolbar.pack(fill="x", pady=(0, 8))
        self.compute_button = ttk.Button(
            toolbar, text="Signal berechnen", command=self._on_compute_clicked, state="disabled"
        )
        self.compute_button.pack(side="left")
        self.status_label = ttk.Label(toolbar, text="", foreground=INFO_COLOR)
        self.status_label.pack(side="left", padx=(12, 0))

        if self._groq_client is None:
            self.status_label.config(
                text="⚠ Kein GROQ_API_KEY gesetzt — Signalberechnung deaktiviert (siehe .env)",
                foreground=WARN_COLOR,
            )

        self.action_label = ttk.Label(right, text="Kein Asset ausgewählt", font=("", 13, "bold"))
        self.action_label.pack(anchor="w")

        self.meta_label = ttk.Label(right, text="", foreground=INFO_COLOR)
        self.meta_label.pack(anchor="w", pady=(0, 8))

        self.gate_label = ttk.Label(right, text="", foreground=WARN_COLOR, wraplength=600, justify="left")
        self.gate_label.pack(anchor="w", pady=(0, 4))

        self.detail_text = tk.Text(right, height=28, wrap="word", state="disabled", relief="flat")
        self.detail_text.pack(fill="both", expand=True)

    def _asset_by_symbol(self, symbol: str):
        return next((a for a in self._watchlist if a.symbol == symbol), None)

    def _refresh_list(self) -> None:
        conn = self._db_conn_factory()
        try:
            latest_by_symbol = {a.symbol: db.get_latest_signal(conn, a.symbol) for a in self._watchlist}
        finally:
            conn.close()

        for item in self.tree.get_children():
            self.tree.delete(item)

        for asset in sorted(self._watchlist, key=lambda a: a.symbol):
            sig = latest_by_symbol.get(asset.symbol)
            action_text = sig.action if sig else "-"
            created_text = sig.created_at[:16].replace("T", " ") if sig else "-"
            self.tree.insert("", "end", iid=asset.symbol, values=(asset.symbol, asset.name, action_text, created_text))

    def _on_select(self, event) -> None:
        selected = self.tree.selection()
        if not selected:
            return
        symbol = selected[0]
        self._selected_asset = self._asset_by_symbol(symbol)
        self.compute_button.config(state="normal" if self._groq_client is not None else "disabled")

        conn = self._db_conn_factory()
        try:
            signal = db.get_latest_signal(conn, symbol)
        finally:
            conn.close()
        self._render_signal(self._selected_asset, signal)

    def _render_signal(self, asset, signal) -> None:
        if signal is None:
            self.action_label.config(text=f"{asset.symbol} — noch kein Signal berechnet", foreground="black")
            self.meta_label.config(text="")
            self.gate_label.config(text="")
            self._set_detail_text("")
            return

        color = ACTION_COLORS.get(signal.action, "black")
        self.action_label.config(text=f"{asset.symbol}: {signal.action}", foreground=color)
        conf_text = f"{signal.confidence_pct:.0f}%" if signal.confidence_pct is not None else "-"
        self.meta_label.config(
            text=(
                f"Konfidenz: {conf_text} · Regime: {signal.regime or '-'} ({signal.regime_source or '-'}) · "
                f"Berechnet: {signal.created_at[:16].replace('T', ' ')}"
            )
        )

        gate_notes = []
        if not signal.gate_passed:
            gate_notes.append(f"⚠ Datenqualitäts-Gate nicht bestanden: {signal.gate_reason}")
        if signal.risk_veto:
            gate_notes.append(f"⚠ Risiko-Veto: {signal.risk_veto_reason}")
        self.gate_label.config(text="\n".join(gate_notes))

        lines = []
        if signal.short_reasoning:
            lines.append(f"KURZBEGRÜNDUNG\n{signal.short_reasoning}\n")
        if signal.long_reasoning_technisch or signal.long_reasoning_fundamental or signal.long_reasoning_makro:
            lines.append("LANGBEGRÜNDUNG")
            if signal.long_reasoning_technisch:
                lines.append(f"Technisch: {signal.long_reasoning_technisch}")
            if signal.long_reasoning_fundamental:
                lines.append(f"Fundamental: {signal.long_reasoning_fundamental}")
            if signal.long_reasoning_makro:
                lines.append(f"Makro: {signal.long_reasoning_makro}")
            lines.append("")

        if signal.position_size_usd or signal.position_size_eur or signal.position_size_note:
            lines.append(
                f"POSITIONSGRÖSSE\n{format_money(signal.position_size_usd)} USD / "
                f"{format_money(signal.position_size_eur)} EUR"
            )
            if signal.position_size_note:
                lines.append(signal.position_size_note)
            lines.append("")

        if signal.entry_usd or signal.stop_loss_usd or signal.take_profit_usd:
            lines.append("EINSTIEG / STOP-LOSS / TAKE-PROFIT (USD | EUR)")
            lines.append(f"  Entry:        {format_money(signal.entry_usd)} | {format_money(signal.entry_eur)}")
            lines.append(f"  Stop-Loss:    {format_money(signal.stop_loss_usd)} | {format_money(signal.stop_loss_eur)}")
            lines.append(f"  Take-Profit:  {format_money(signal.take_profit_usd)} | {format_money(signal.take_profit_eur)}")
            lines.append("")

        if signal.holding_duration:
            lines.append(f"HALTEDAUER\n{signal.holding_duration} — {signal.holding_duration_reason}\n")

        if signal.key_risks_text:
            lines.append("WICHTIGSTE RISIKEN")
            for risk in signal.key_risks_text.split("\n"):
                lines.append(f"  • {risk}")
            lines.append("")

        if signal.forecast_bull_text or signal.forecast_base_text or signal.forecast_bear_text:
            lines.append("FORECAST-SZENARIEN")
            if signal.forecast_bull_text:
                lines.append(f"  Bull ({signal.forecast_bull_prob_pct}%): {signal.forecast_bull_text}")
            if signal.forecast_base_text:
                lines.append(f"  Base ({signal.forecast_base_prob_pct}%): {signal.forecast_base_text}")
            if signal.forecast_bear_text:
                lines.append(f"  Bear ({signal.forecast_bear_prob_pct}%): {signal.forecast_bear_text}")
            lines.append("")

        if signal.tauschen_target_symbol:
            lines.append(f"TAUSCH-ZIEL\n{signal.tauschen_target_symbol}\n")

        self._set_detail_text("\n".join(lines))

    def _set_detail_text(self, text: str) -> None:
        self.detail_text.config(state="normal")
        self.detail_text.delete("1.0", "end")
        self.detail_text.insert("1.0", text)
        self.detail_text.config(state="disabled")

    def _on_compute_clicked(self) -> None:
        asset = self._selected_asset
        if asset is None or self._groq_client is None:
            return

        self.compute_button.config(state="disabled")
        self.status_label.config(text=f"Berechne Signal für {asset.symbol} …", foreground=INFO_COLOR)

        thread = threading.Thread(target=self._run_pipeline, args=(asset,), daemon=True)
        thread.start()

    def _run_pipeline(self, asset) -> None:
        from agent.pipeline import generate_signal

        conn = self._db_conn_factory()
        try:
            signal = generate_signal(
                asset, self._full_watchlist, conn, self._groq_client, self._coingecko_client, self._kraken_client,
                fred_api_key=self._fred_api_key,
            )
            error = None
        except Exception as exc:  # noqa: BLE001 - an die UI durchreichen statt den Thread stumm sterben zu lassen
            signal = None
            error = exc
        finally:
            conn.close()

        self.after(0, self._on_pipeline_done, asset, signal, error)

    def _on_pipeline_done(self, asset, signal, error) -> None:
        self.compute_button.config(state="normal" if self._groq_client is not None else "disabled")
        if error is not None:
            self.status_label.config(text=f"Fehler: {error}", foreground="#c0392b")
            return
        self.status_label.config(text="Fertig.", foreground=INFO_COLOR)
        self._refresh_list()
        if self._selected_asset is not None and self._selected_asset.symbol == asset.symbol:
            self._render_signal(asset, signal)
