"""Signale-Tab (U-4): zeigt die zuletzt berechnete Empfehlung je Asset im P-5-Format
und erlaubt, die Agent-Pipeline (agent/krypto/pipeline.py) manuell fuer ein ausgewaehltes
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
import ui.theme as theme
from ui.formatting import format_money
from ui.sortable_tree import make_sortable

# Vorzeichen fuer die Bestand-Aktualisierungs-Vorschlagslogik (Nutzeridee 2026-07-07,
# umgesetzt 2026-07-09): bei TAUSCHEN wird nur die Quell-Position reduziert, das
# Ziel-Asset wird bewusst NICHT automatisch angelegt (out of scope fuer diese Slice,
# Nutzer muesste das separat/manuell erfassen).
ACTION_HOLDING_SIGN = {"KAUFEN": 1, "NACHKAUFEN": 1, "VERKAUFEN": -1, "TAUSCHEN": -1}


def _parse_optional_float(text: str) -> float | None:
    """Wie importer/excel_import.py::_parse_quantity() - deutsches Komma als
    Dezimaltrennzeichen akzeptieren (Nutzer-Review 2026-07-09: dieselbe Konvention
    gilt bereits beim Excel-Import, ein rohes float() waere hier inkonsistent)."""
    text = text.strip().replace(",", ".")
    return float(text) if text else None


class SignalsView(ttk.Frame):
    def __init__(
        self, parent, db_conn_factory, watchlist, groq_client, coingecko_client, kraken_client,
        fred_api_key=None,
    ):
        super().__init__(parent)
        self._db_conn_factory = db_conn_factory
        # Multi-Asset-Tracking (Nutzer-Idee 2026-07-09): Aktien/ETF/Rohstoffe werden
        # HIER bewusst herausgefiltert, nicht nur aus der Anzeige-Liste - die Agent-
        # Pipeline (Regime/Risiko-Gate) ist fuer diese Assetklassen nicht gebaut, siehe
        # Spezifikation Kap. 11 "Zielarchitektur fuer Multi-Asset-Erweiterbarkeit".
        # Wuerden sie in _full_watchlist landen, wuerde
        # agent/krypto/risk_gate.py::_portfolio_values_usd() ihren Wert in die
        # Gesamtportfolio-Summe einrechnen und damit die Krypto-Allokations-Prozente
        # verzerren, obwohl das Risiko-Gate nichts von ihnen "weiss".
        krypto_watchlist = [a for a in watchlist if a.assetklasse == "krypto"]
        self._full_watchlist = krypto_watchlist  # generate_signal braucht ALLE
        # Krypto-Assets (Stablecoins zaehlen z.B. als Cash-Reserve) - nur die
        # Anzeige-Liste filtert zusaetzlich Stablecoins raus.
        self._watchlist = [a for a in krypto_watchlist if a.typ != "stablecoin"]
        self._groq_client = groq_client
        self._coingecko_client = coingecko_client
        self._kraken_client = kraken_client
        self._fred_api_key = fred_api_key  # optional (P-8) - ohne Key liefert
        # agent/krypto/pipeline.py fuer die FRED-Felder sauber None statt abzustuerzen.
        self._selected_asset = None
        self._current_signal = None

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
        make_sortable(self.tree)
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
        self.history_button = ttk.Button(
            toolbar, text="Signal-Historie", command=self._on_history_clicked, state="disabled"
        )
        self.history_button.pack(side="left", padx=(6, 0))
        self.status_label = ttk.Label(toolbar, text="", foreground=theme.info_color())
        self.status_label.pack(side="left", padx=(12, 0))

        if self._groq_client is None:
            self.status_label.config(
                text="⚠ Kein GROQ_API_KEY gesetzt — Signalberechnung deaktiviert (siehe .env)",
                foreground=theme.warn_color(),
            )

        self.action_label = ttk.Label(right, text="Kein Asset ausgewählt", font=("", 13, "bold"))
        self.action_label.pack(anchor="w")

        self.meta_label = ttk.Label(right, text="", foreground=theme.info_color())
        self.meta_label.pack(anchor="w", pady=(0, 8))

        self.gate_label = ttk.Label(right, text="", foreground=theme.warn_color(), wraplength=600, justify="left")
        self.gate_label.pack(anchor="w", pady=(0, 4))

        umsetzung_frame = ttk.Frame(right)
        umsetzung_frame.pack(fill="x", pady=(0, 8))
        self.umsetzung_label = ttk.Label(umsetzung_frame, text="", foreground=theme.info_color())
        self.umsetzung_label.pack(side="left")
        self.umsetzung_button = ttk.Button(
            umsetzung_frame, text="Rückmeldung erfassen", command=self._on_umsetzung_clicked, state="disabled"
        )
        self.umsetzung_button.pack(side="left", padx=(12, 0))

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
        self.history_button.config(state="normal")  # braucht keinen Groq-Key, reine DB-Anzeige

        conn = self._db_conn_factory()
        try:
            signal = db.get_latest_signal(conn, symbol)
        finally:
            conn.close()
        self._render_signal(self._selected_asset, signal)

    def _render_signal(self, asset, signal) -> None:
        self._current_signal = signal
        self._render_umsetzung_status(signal)

        if signal is None:
            self.action_label.config(text=f"{asset.symbol} — noch kein Signal berechnet", foreground=theme.default_text_color())
            self.meta_label.config(text="")
            self.gate_label.config(text="")
            self._set_detail_text("")
            return

        color = theme.action_color(signal.action)
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
        top_gruende_pairs = [
            (getattr(signal, f"top_grund_{i}_kategorie"), getattr(signal, f"top_grund_{i}_text"))
            for i in range(1, 6)
        ]
        top_gruende_pairs = [(k, t) for k, t in top_gruende_pairs if t]
        if top_gruende_pairs:
            lines.append("TOP 5 GRÜNDE")
            for idx, (kategorie, text) in enumerate(top_gruende_pairs, start=1):
                tag = f"[{kategorie}] " if kategorie else ""
                lines.append(f"  {idx}. {tag}{text}")
            lines.append("")

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

        if signal.entry_usd_von is not None or signal.stop_loss_usd_von is not None or signal.take_profit_usd_von is not None:
            lines.append("KAUF-ZONE / STOP-LOSS-ZONE / TAKE-PROFIT-ZONE (USD | EUR)")
            lines.append(
                f"  Kauf-Zone:    {format_money(signal.entry_usd_von)}–{format_money(signal.entry_usd_bis)} | "
                f"{format_money(signal.entry_eur_von)}–{format_money(signal.entry_eur_bis)}"
            )
            lines.append(
                f"  Stop-Loss:    {format_money(signal.stop_loss_usd_von)}–{format_money(signal.stop_loss_usd_bis)} | "
                f"{format_money(signal.stop_loss_eur_von)}–{format_money(signal.stop_loss_eur_bis)}"
            )
            lines.append(
                f"  Take-Profit:  {format_money(signal.take_profit_usd_von)}–{format_money(signal.take_profit_usd_bis)} | "
                f"{format_money(signal.take_profit_eur_von)}–{format_money(signal.take_profit_eur_bis)}"
            )
            lines.append("")
        elif signal.entry_usd or signal.stop_loss_usd or signal.take_profit_usd:
            lines.append("EINSTIEG / STOP-LOSS / TAKE-PROFIT (USD | EUR)")
            lines.append(f"  Entry:        {format_money(signal.entry_usd)} | {format_money(signal.entry_eur)}")
            lines.append(f"  Stop-Loss:    {format_money(signal.stop_loss_usd)} | {format_money(signal.stop_loss_eur)}")
            lines.append(f"  Take-Profit:  {format_money(signal.take_profit_usd)} | {format_money(signal.take_profit_eur)}")
            lines.append("")

        if signal.halte_kriterium_bucket:
            lines.append("HALTE-KRITERIUM")
            lines.append(f"  Grobe Einordnung: {signal.halte_kriterium_bucket}")
            if signal.halte_kriterium_ziel_preis_usd or signal.halte_kriterium_ziel_preis_eur:
                lines.append(
                    f"  Ziel-Kurs: {format_money(signal.halte_kriterium_ziel_preis_usd)} USD / "
                    f"{format_money(signal.halte_kriterium_ziel_preis_eur)} EUR"
                )
            if signal.halte_kriterium_ziel_datum:
                lines.append(f"  Ziel-Datum: {signal.halte_kriterium_ziel_datum}")
            if signal.halte_kriterium_bedingung_text:
                lines.append(f"  Bedingung: {signal.halte_kriterium_bedingung_text}")
            if signal.halte_kriterium_reasoning:
                lines.append(f"  Begründung: {signal.halte_kriterium_reasoning}")
            lines.append("")
        elif signal.holding_duration:
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

    def _render_umsetzung_status(self, signal) -> None:
        if signal is None:
            self.umsetzung_label.config(text="")
            self.umsetzung_button.config(state="disabled")
            return

        self.umsetzung_button.config(state="normal")
        if signal.umgesetzt is None:
            self.umsetzung_label.config(text="Umsetzung: noch keine Rückmeldung", foreground=theme.info_color())
        elif signal.umgesetzt:
            detail_parts = []
            if signal.umgesetzt_menge is not None:
                detail_parts.append(f"Menge {signal.umgesetzt_menge}")
            if signal.umgesetzt_preis_usd is not None:
                detail_parts.append(f"Preis {format_money(signal.umgesetzt_preis_usd)} USD")
            detail = f" ({', '.join(detail_parts)})" if detail_parts else ""
            when = signal.umgesetzt_am[:16].replace("T", " ") if signal.umgesetzt_am else "-"
            self.umsetzung_label.config(text=f"✓ Umgesetzt am {when}{detail}", foreground=theme.umgesetzt_color())
        else:
            when = signal.umgesetzt_am[:16].replace("T", " ") if signal.umgesetzt_am else "-"
            self.umsetzung_label.config(text=f"✗ Nicht umgesetzt (Rückmeldung am {when})", foreground=theme.nicht_umgesetzt_color())

    def _on_umsetzung_clicked(self) -> None:
        if self._selected_asset is None or self._current_signal is None:
            return
        UmsetzungDialog(self, self._selected_asset, self._current_signal, self._db_conn_factory, self._on_umsetzung_saved)

    def _on_umsetzung_saved(self) -> None:
        asset = self._selected_asset
        conn = self._db_conn_factory()
        try:
            signal = db.get_latest_signal(conn, asset.symbol) if asset else None
        finally:
            conn.close()
        self._refresh_list()
        if asset is not None:
            self._render_signal(asset, signal)

    def _on_history_clicked(self) -> None:
        """Backward-Tracking (2026-07-10, Selbstverifikations-Vision Schritt 2) -
        macht db.get_signal_history() sichtbar, das bis dahin toter Code war (nie
        in der UI verdrahtet). Reine Anzeige, keine Eingabe."""
        if self._selected_asset is None:
            return
        conn = self._db_conn_factory()
        try:
            history = db.get_signal_history(conn, self._selected_asset.symbol)
        finally:
            conn.close()
        SignalHistoryDialog(self, self._selected_asset, history)

    def _on_compute_clicked(self) -> None:
        asset = self._selected_asset
        if asset is None or self._groq_client is None:
            return

        self.compute_button.config(state="disabled")
        self.status_label.config(text=f"Berechne Signal für {asset.symbol} …", foreground=theme.info_color())

        thread = threading.Thread(target=self._run_pipeline, args=(asset,), daemon=True)
        thread.start()

    def _run_pipeline(self, asset) -> None:
        from agent.krypto.pipeline import generate_signal

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
            self.status_label.config(text=f"Fehler: {error}", foreground=theme.danger_color())
            return
        self.status_label.config(text="Fertig.", foreground=theme.info_color())
        self._refresh_list()
        if self._selected_asset is not None and self._selected_asset.symbol == asset.symbol:
            self._render_signal(asset, signal)


class UmsetzungDialog(tk.Toplevel):
    """Modal-Dialog fuer die Umsetzungs-Rueckmeldung (Nutzeridee 2026-07-07, umgesetzt
    2026-07-09). Optionaler zweiter Schritt "Bestand jetzt aktualisieren" ist bewusst
    ein SEPARATER, vom Nutzer explizit bestaetigter Schreibpfad in holdings (kein
    automatischer Auto-Write) - schlaegt lediglich einen aus Aktion+Menge berechneten
    neuen Gesamtbestand vor, der Nutzer kann ihn vor dem Speichern frei ueberschreiben."""

    def __init__(self, parent, asset, signal, db_conn_factory, on_saved) -> None:
        super().__init__(parent)
        self._asset = asset
        self._signal = signal
        self._db_conn_factory = db_conn_factory
        self._on_saved = on_saved

        self.title(f"Umsetzungs-Rückmeldung — {asset.symbol}")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self._umgesetzt_var = tk.StringVar(value="ja" if signal.umgesetzt in (True, None) else "nein")
        self._menge_var = tk.StringVar(value=str(signal.umgesetzt_menge) if signal.umgesetzt_menge is not None else "")
        self._preis_var = tk.StringVar(
            value=str(signal.umgesetzt_preis_usd) if signal.umgesetzt_preis_usd is not None else ""
        )
        self._bestand_aktualisieren_var = tk.BooleanVar(value=False)
        self._neuer_bestand_var = tk.StringVar(value="")
        # Vorschlag live neu berechnen, wenn die Menge SPAETER (nach dem Ankreuzen der
        # Checkbox) eingegeben wird - sonst bliebe der Vorschlag auf menge=0 stehen
        # (Nutzer-Review 2026-07-09).
        self._menge_var.trace_add("write", lambda *_: self._on_bestand_toggle())

        frame = ttk.Frame(self, padding=12)
        frame.pack(fill="both", expand=True)

        ttk.Label(frame, text=f"{asset.symbol} — {signal.action}", font=("", 11, "bold")).grid(
            row=0, column=0, columnspan=2, sticky="w", pady=(0, 8)
        )

        ttk.Label(frame, text="Empfehlung umgesetzt?").grid(row=1, column=0, sticky="w")
        radio_frame = ttk.Frame(frame)
        radio_frame.grid(row=1, column=1, sticky="w")
        ttk.Radiobutton(radio_frame, text="Ja", variable=self._umgesetzt_var, value="ja", command=self._on_umgesetzt_toggle).pack(side="left")
        ttk.Radiobutton(radio_frame, text="Nein", variable=self._umgesetzt_var, value="nein", command=self._on_umgesetzt_toggle).pack(side="left")

        ttk.Label(frame, text="Menge (optional):").grid(row=2, column=0, sticky="w", pady=(8, 0))
        self._menge_entry = ttk.Entry(frame, textvariable=self._menge_var, width=18)
        self._menge_entry.grid(row=2, column=1, sticky="w", pady=(8, 0))

        ttk.Label(frame, text="Ausführungspreis USD (optional):").grid(row=3, column=0, sticky="w", pady=(4, 0))
        self._preis_entry = ttk.Entry(frame, textvariable=self._preis_var, width=18)
        self._preis_entry.grid(row=3, column=1, sticky="w", pady=(4, 0))

        self._bestand_check = ttk.Checkbutton(
            frame, text="Bestand (Portfolio) jetzt aktualisieren", variable=self._bestand_aktualisieren_var,
            command=self._on_bestand_toggle,
        )
        self._bestand_check.grid(row=4, column=0, columnspan=2, sticky="w", pady=(12, 0))

        self._bestand_info_label = ttk.Label(frame, text="", foreground=theme.info_color(), wraplength=320, justify="left")
        self._bestand_info_label.grid(row=5, column=0, columnspan=2, sticky="w")

        ttk.Label(frame, text="Neuer Bestand (gesamt):").grid(row=6, column=0, sticky="w", pady=(4, 0))
        self._neuer_bestand_entry = ttk.Entry(frame, textvariable=self._neuer_bestand_var, width=18, state="disabled")
        self._neuer_bestand_entry.grid(row=6, column=1, sticky="w", pady=(4, 0))

        self._error_label = ttk.Label(frame, text="", foreground=theme.danger_color(), wraplength=320, justify="left")
        self._error_label.grid(row=7, column=0, columnspan=2, sticky="w", pady=(8, 0))

        button_frame = ttk.Frame(frame)
        button_frame.grid(row=8, column=0, columnspan=2, sticky="e", pady=(12, 0))
        ttk.Button(button_frame, text="Abbrechen", command=self.destroy).pack(side="left", padx=(0, 8))
        ttk.Button(button_frame, text="Speichern", command=self._on_save_clicked).pack(side="left")

        self._on_umgesetzt_toggle()

    def _on_umgesetzt_toggle(self) -> None:
        ja = self._umgesetzt_var.get() == "ja"
        state = "normal" if ja else "disabled"
        self._menge_entry.config(state=state)
        self._preis_entry.config(state=state)
        self._bestand_check.config(state="normal" if ja else "disabled")
        if not ja:
            self._bestand_aktualisieren_var.set(False)
            self._on_bestand_toggle()

    def _current_holding_quantity(self) -> float:
        conn = self._db_conn_factory()
        try:
            holdings = db.get_all_holdings(conn)
        finally:
            conn.close()
        existing = next((h for h in holdings if h.symbol == self._asset.symbol), None)
        return existing.quantity if existing else 0.0

    def _on_bestand_toggle(self) -> None:
        if not self._bestand_aktualisieren_var.get():
            self._neuer_bestand_entry.config(state="disabled")
            self._bestand_info_label.config(text="")
            return

        current_qty = self._current_holding_quantity()
        sign = ACTION_HOLDING_SIGN.get(self._signal.action)
        try:
            menge = _parse_optional_float(self._menge_var.get()) or 0.0
        except ValueError:
            menge = 0.0
        suggestion = current_qty + sign * menge if sign is not None else current_qty

        warn = " ⚠ Ergibt einen negativen Bestand — bitte prüfen." if suggestion < 0 else ""
        self._bestand_info_label.config(
            text=f"Aktueller Bestand: {current_qty}. Vorschlag basiert auf Aktion '{self._signal.action}' "
            f"und Menge — bitte prüfen und bei Bedarf anpassen.{warn}",
            foreground=theme.danger_color() if suggestion < 0 else theme.info_color(),
        )
        self._neuer_bestand_var.set(str(suggestion))
        self._neuer_bestand_entry.config(state="normal")

    def _on_save_clicked(self) -> None:
        self._error_label.config(text="")
        umgesetzt = self._umgesetzt_var.get() == "ja"

        try:
            menge = _parse_optional_float(self._menge_var.get())
            preis = _parse_optional_float(self._preis_var.get())
        except ValueError:
            self._error_label.config(text="Menge/Preis müssen Zahlen sein.")
            return

        neuer_bestand = None
        if umgesetzt and self._bestand_aktualisieren_var.get():
            try:
                neuer_bestand = _parse_optional_float(self._neuer_bestand_var.get())
            except ValueError:
                self._error_label.config(text="Neuer Bestand muss eine Zahl sein.")
                return
            if neuer_bestand is None:
                self._error_label.config(text="Neuer Bestand darf nicht leer sein.")
                return
            if neuer_bestand < 0:
                self._error_label.config(text="Neuer Bestand darf nicht negativ sein.")
                return

        conn = self._db_conn_factory()
        try:
            db.update_signal_umsetzung(conn, self._signal.id, umgesetzt, umgesetzt_menge=menge, umgesetzt_preis_usd=preis)
            if neuer_bestand is not None:
                db.upsert_holding(conn, self._asset.symbol, neuer_bestand, source="signal_bestaetigung")
        finally:
            conn.close()

        self.destroy()
        self._on_saved()


_OUTCOME_LABELS = {
    "offen": "Offen",
    "take_profit_erreicht": "Take-Profit erreicht",
    "stop_loss_erreicht": "Stop-Loss erreicht",
    "abgelaufen_unentschieden": "Abgelaufen (unentschieden)",
    "nicht_anwendbar": "Nicht anwendbar",
}


def _outcome_color(status: str | None):
    if status == "take_profit_erreicht":
        return theme.umgesetzt_color()
    if status == "stop_loss_erreicht":
        return theme.danger_color()
    if status == "abgelaufen_unentschieden":
        return theme.stale_color()
    if status == "offen":
        return theme.info_color()
    return theme.default_text_color()


class SignalHistoryDialog(tk.Toplevel):
    """Backward-Tracking-Anzeige (2026-07-10, Selbstverifikations-Vision Schritt 2)
    - reine Anzeige aller bisherigen Signale eines Assets inkl. Outcome-Status, macht
    db.get_signal_history() (bis dahin toter Code) erstmals in der UI sichtbar. Kein
    Aggregat/keine Statistik in dieser Slice - das ist Schritt 3 (KI-Trimm-
    Vorschlaege brauchen genau diese Aggregation als Eingabe)."""

    def __init__(self, parent, asset, history: list) -> None:
        super().__init__(parent)
        self.title(f"Signal-Historie — {asset.symbol}")
        self.resizable(True, True)
        self.transient(parent)
        self.grab_set()
        self.geometry("720x400")

        frame = ttk.Frame(self, padding=12)
        frame.pack(fill="both", expand=True)

        if not history:
            ttk.Label(frame, text="Noch keine Signale für dieses Asset vorhanden.").pack(anchor="w")
            ttk.Button(frame, text="Schließen", command=self.destroy).pack(anchor="e", pady=(10, 0))
            return

        columns = ("datum", "aktion", "konfidenz", "outcome")
        tree = ttk.Treeview(frame, columns=columns, show="headings", height=14)
        headings = {"datum": "Datum", "aktion": "Aktion", "konfidenz": "Konfidenz", "outcome": "Ergebnis"}
        for col in columns:
            tree.heading(col, text=headings[col])
            tree.column(col, width=150 if col != "outcome" else 220, anchor="w")
        tree.pack(fill="both", expand=True)

        for signal in history:
            when = signal.created_at[:16].replace("T", " ") if signal.created_at else "-"
            konfidenz = f"{signal.confidence_pct:.0f} %" if signal.confidence_pct is not None else "-"
            status = signal.outcome_status
            outcome_text = _OUTCOME_LABELS.get(status, "—") if status else "—"
            if status == "take_profit_erreicht" and signal.outcome_realisiertes_crv is not None:
                outcome_text += f" (CRV {signal.outcome_realisiertes_crv:.2f})"
            item_id = tree.insert(
                "", "end", values=(when, signal.action, konfidenz, outcome_text), tags=(status or "none",)
            )
            tree.tag_configure(status or "none", foreground=_outcome_color(status))

        ttk.Button(frame, text="Schließen", command=self.destroy).pack(anchor="e", pady=(10, 0))
