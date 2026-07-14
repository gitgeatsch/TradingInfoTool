"""Hebel-Tab (2026-07-14, Phase 6): zeigt Hebel-Empfehlungen (`hebel_signals`),
wartende Screening-Kandidaten (`hebel_triggers`) und offene Margin-Positionen
(`hebel_positions`) - die komplette Pipeline (Phase 1-5) lief bisher nur im
Hintergrund/Log, ohne jede UI-Sichtbarkeit. Mirrort ui/signals_view.py::
SignalsView 1:1 im Aufbau (Liste+Detail-Panedwindow, bewährtes Muster).

Threading: "Jetzt analysieren" ruft generate_hebel_signal() im Hintergrund-
Thread auf (Netzwerk+LLM dauert mehrere Sekunden), identisches Muster wie
ui/marktscan_view.py::MarktscanView._run_writeup(). Bewusst OHNE Budget-/
Cooldown-Pruefung (anders als agent/krypto/budget_allocator.py) - ein
manueller Klick ist ein expliziter Einzel-Wunsch, analog zu den bestehenden
manuellen Buttons bei Spot-Signalen/Marktscan."""
from __future__ import annotations

import threading
import tkinter as tk
from tkinter import ttk

import database.db as db
import ui.theme as theme
from ui.formatting import format_money
from ui.heading_tooltip import add_heading_tooltips
from ui.sortable_tree import make_sortable

_LIST_COLUMN_DESCRIPTIONS = {
    "symbol": "Kurzzeichen des Assets.",
    "richtung": "LONG oder SHORT.",
    "status": "Letzte KI-Empfehlung, oder \"Kandidat (wartet auf Analyse)\", falls noch keine Empfehlung vorliegt.",
    "hebel_score": "Bei einer Empfehlung: der final gedeckelte Hebel. Bei einem wartenden Kandidaten: der Trigger-Score (0-100).",
    "zeitpunkt": "Wann die Empfehlung berechnet wurde bzw. wann der Kandidat gefunden wurde.",
}

_POSITIONS_COLUMN_DESCRIPTIONS = {
    "symbol": "Kurzzeichen des Assets.",
    "richtung": "LONG oder SHORT.",
    "hebel_effektiv": "Über alle Tranchen geblendeter tatsächlicher Hebel.",
    "eigenkapital": "Eigenkapital in der Position (EUR).",
    "eroeffnet": "Datum, an dem die Position eröffnet wurde.",
    "liquidationspreis": "Zuletzt geschätzter Liquidationspreis (EUR, konservative Schätzung).",
}


class HebelView(ttk.Frame):
    def __init__(
        self, parent, db_conn_factory, watchlist, groq_client, cerebras_client,
        coingecko_client, kraken_client, fred_api_key=None,
    ):
        super().__init__(parent)
        self._db_conn_factory = db_conn_factory
        self._watchlist = watchlist
        self._groq_client = groq_client
        self._cerebras_client = cerebras_client
        self._coingecko_client = coingecko_client
        self._kraken_client = kraken_client
        self._fred_api_key = fred_api_key

        # iid -> ("signal", HebelSignal) oder ("kandidat", HebelTrigger)
        self._rows: dict[str, tuple[str, object]] = {}
        self._selected_row: tuple[str, object] | None = None

        self._build_layout()
        self.refresh()

    def _build_layout(self) -> None:
        paned = ttk.Panedwindow(self, orient="horizontal")
        paned.pack(fill="both", expand=True, padx=8, pady=8)

        left = ttk.Frame(paned)
        paned.add(left, weight=1)

        columns = ("symbol", "richtung", "status", "hebel_score", "zeitpunkt")
        self.tree = ttk.Treeview(left, columns=columns, show="headings", height=16)
        headings = {
            "symbol": "Symbol", "richtung": "Richtung", "status": "Status/Aktion",
            "hebel_score": "Hebel/Score", "zeitpunkt": "Zeitpunkt",
        }
        for col in columns:
            self.tree.heading(col, text=headings[col])
            self.tree.column(col, width=110, anchor="w" if col in ("symbol", "status") else "center")
        self.tree.tag_configure("kandidat", foreground=theme.info_color())
        make_sortable(self.tree)
        add_heading_tooltips(self.tree, _LIST_COLUMN_DESCRIPTIONS)
        self.tree.pack(fill="both", expand=True)
        self.tree.bind("<<TreeviewSelect>>", self._on_select)

        ttk.Label(left, text="Offene Hebel-Positionen", font=("", 10, "bold")).pack(anchor="w", pady=(8, 2))
        pos_columns = ("symbol", "richtung", "hebel_effektiv", "eigenkapital", "eroeffnet", "liquidationspreis")
        self.positions_tree = ttk.Treeview(left, columns=pos_columns, show="headings", height=5)
        pos_headings = {
            "symbol": "Symbol", "richtung": "Richtung", "hebel_effektiv": "Hebel",
            "eigenkapital": "Eigenkapital (EUR)", "eroeffnet": "Eröffnet am",
            "liquidationspreis": "Liq.-Preis (EUR)",
        }
        for col in pos_columns:
            self.positions_tree.heading(col, text=pos_headings[col])
            self.positions_tree.column(col, width=110, anchor="w" if col == "symbol" else "center")
        add_heading_tooltips(self.positions_tree, _POSITIONS_COLUMN_DESCRIPTIONS)
        self.positions_tree.pack(fill="x", pady=(0, 4))

        right = ttk.Frame(paned)
        paned.add(right, weight=3)

        toolbar = ttk.Frame(right)
        toolbar.pack(fill="x", pady=(0, 8))
        self.analyze_button = ttk.Button(
            toolbar, text="Jetzt analysieren", command=self._on_analyze_clicked, state="disabled"
        )
        self.analyze_button.pack(side="left")
        self.status_label = ttk.Label(toolbar, text="", foreground=theme.info_color())
        self.status_label.pack(side="left", padx=(12, 0))

        if self._groq_client is None and self._cerebras_client is None:
            self.status_label.config(
                text="⚠ Kein Groq-/Cerebras-Key gesetzt — manuelle Analyse deaktiviert",
                foreground=theme.warn_color(),
            )

        self.action_label = ttk.Label(right, text="Keine Auswahl", font=("", 13, "bold"))
        self.action_label.pack(anchor="w")

        self.meta_label = ttk.Label(right, text="", foreground=theme.info_color())
        self.meta_label.pack(anchor="w", pady=(0, 8))

        self.detail_text = tk.Text(right, height=28, wrap="word", state="disabled", relief="flat")
        self.detail_text.pack(fill="both", expand=True)

    def refresh(self) -> None:
        conn = self._db_conn_factory()
        try:
            signals = db.get_latest_hebel_signal_per_symbol(conn)
            kandidaten = db.get_pending_hebel_candidates(conn)
            positions = db.get_open_hebel_positions(conn)
        finally:
            conn.close()

        vorher_selected = self.tree.selection()
        vorher_iid = vorher_selected[0] if vorher_selected else None

        for item in self.tree.get_children():
            self.tree.delete(item)
        self._rows = {}

        covered = {(s.symbol, s.richtung) for s in signals.values()}
        for sig in sorted(signals.values(), key=lambda s: s.created_at, reverse=True):
            iid = f"{sig.symbol}:{sig.richtung}"
            self._rows[iid] = ("signal", sig)
            zeit = sig.created_at[:16].replace("T", " ") if sig.created_at else "-"
            hebel_text = f"{sig.hebel_final:.1f}x" if sig.hebel_final else "-"
            self.tree.insert(
                "", "end", iid=iid,
                values=(sig.symbol, sig.richtung, sig.action, hebel_text, zeit),
            )

        for trig in kandidaten:
            if (trig.symbol, trig.richtung) in covered:
                continue  # bereits als echtes Signal oben gelistet
            iid = f"{trig.symbol}:{trig.richtung}"
            if iid in self._rows:
                continue  # zweiter Kandidat fuer dasselbe Symbol+Richtung (Trendfolge+
                # Kontra koennen beide dieselbe Richtung vorschlagen) - der zuerst
                # verarbeitete (score-staerkere, da kandidaten bereits score-sortiert
                # aus der DB kommt) gewinnt in dieser kompakten Liste.
            self._rows[iid] = ("kandidat", trig)
            zeit = trig.screened_at[:16].replace("T", " ") if trig.screened_at else "-"
            score_text = f"{trig.score_gesamt:.0f}" if trig.score_gesamt is not None else "-"
            self.tree.insert(
                "", "end", iid=iid,
                values=(trig.symbol, trig.richtung, "Kandidat (wartet auf Analyse)", score_text, zeit),
                tags=("kandidat",),
            )

        theme.restripe_treeview(self.tree)

        if vorher_iid and vorher_iid in self._rows:
            self.tree.selection_set(vorher_iid)
        else:
            self._render_selection(None)

        self._refresh_positions(positions)

    def _refresh_positions(self, positions) -> None:
        for item in self.positions_tree.get_children():
            self.positions_tree.delete(item)
        if not positions:
            self.positions_tree.insert("", "end", values=("Keine offenen Positionen", "-", "-", "-", "-", "-"))
            return
        for pos in positions:
            eroeffnet = pos.eroeffnet_am[:10] if pos.eroeffnet_am else "-"
            hebel_text = f"{pos.hebel_effektiv:.2f}x" if pos.hebel_effektiv else "-"
            self.positions_tree.insert(
                "", "end",
                values=(
                    pos.symbol, pos.richtung, hebel_text,
                    format_money(pos.eigenkapital_eur), eroeffnet,
                    format_money(pos.liquidationspreis_geschaetzt_eur),
                ),
            )

    def _on_select(self, event) -> None:
        selected = self.tree.selection()
        if not selected:
            self._render_selection(None)
            return
        self._render_selection(self._rows.get(selected[0]))

    def _render_selection(self, row) -> None:
        self._selected_row = row
        if row is None:
            self.analyze_button.config(state="disabled")
            self.action_label.config(text="Keine Auswahl", foreground=theme.default_text_color())
            self.meta_label.config(text="")
            self._set_detail_text("")
            return

        kind, obj = row
        if kind == "kandidat":
            self._render_kandidat(obj)
        else:
            self._render_signal(obj)

    def _render_kandidat(self, trig) -> None:
        can_analyze = self._groq_client is not None or self._cerebras_client is not None
        self.analyze_button.config(state="normal" if can_analyze else "disabled")
        self.action_label.config(
            text=f"{trig.symbol} {trig.richtung}: Kandidat (wartet auf Analyse)",
            foreground=theme.info_color(),
        )
        gefunden = (trig.screened_at or "-")[:16].replace("T", " ")
        self.meta_label.config(
            text=f"Trigger-Zweig: {trig.trigger_zweig or '-'} · Score: "
            f"{trig.score_gesamt if trig.score_gesamt is not None else '-'} · Gefunden: {gefunden}"
        )
        lines = [
            "NOCH NICHT ANALYSIERT",
            "Wird automatisch im nächsten Budget-Allocator-Lauf (15-Min-Takt) "
            "verarbeitet, sofern das Tagesbudget das zulässt - oder jetzt manuell "
            "auslösen (Button oben).",
            "",
            "TRIGGER-DETAILS",
            f"  Zweig: {trig.trigger_zweig or '-'}",
            f"  Score gesamt: {trig.score_gesamt if trig.score_gesamt is not None else '-'}",
            f"  OI-Änderung (Lookback): "
            f"{trig.oi_change_pct_lookback if trig.oi_change_pct_lookback is not None else '-'}%",
            f"  Kursänderung (Lookback): "
            f"{trig.kursaenderung_pct_lookback if trig.kursaenderung_pct_lookback is not None else '-'}%",
            f"  Funding-Rate aktuell: "
            f"{trig.funding_rate_aktuell if trig.funding_rate_aktuell is not None else '-'}",
            f"  Long-Konten-Anteil: "
            f"{trig.long_konten_anteil_prozent if trig.long_konten_anteil_prozent is not None else '-'}%",
        ]
        self._set_detail_text("\n".join(lines))

    def _render_signal(self, signal) -> None:
        self.analyze_button.config(state="disabled")  # bereits analysiert, kein erneuter manueller Call noetig
        color = theme.action_color(signal.action)
        self.action_label.config(text=f"{signal.symbol} {signal.richtung}: {signal.action}", foreground=color)
        conf_text = f"{signal.confidence_pct:.0f}%" if signal.confidence_pct is not None else "-"
        self.meta_label.config(
            text=(
                f"Konfidenz: {conf_text} · Trigger: {signal.trigger_zweig or '-'} "
                f"({signal.trigger_score if signal.trigger_score is not None else '-'}) · "
                f"Anbieter: {signal.llm_model or '-'} · "
                f"Berechnet: {signal.created_at[:16].replace('T', ' ')}"
            )
        )

        lines = []
        if not signal.gate_passed:
            lines.append(f"⚠ DATENQUALITÄTS-GATE NICHT BESTANDEN: {signal.gate_reason}\n")
        if signal.risk_veto:
            lines.append(f"⚠ RISIKO-VETO: {signal.risk_veto_reason}\n")

        if signal.trade_thesis_typ:
            lines.append(f"THESE: {signal.trade_thesis_typ}\n")

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

        if signal.hebel_vorschlag is not None or signal.hebel_final is not None:
            lines.append("HEBEL")
            vorschlag_text = f"{signal.hebel_vorschlag:.2f}x" if signal.hebel_vorschlag is not None else "-"
            final_text = f"{signal.hebel_final:.2f}x" if signal.hebel_final is not None else "-"
            lines.append(f"  Vorschlag (KI): {vorschlag_text}")
            lines.append(f"  Final (gedeckelt): {final_text}")
            if signal.hebel_korrektur_hinweis:
                lines.append(f"  Hinweis: {signal.hebel_korrektur_hinweis}")
            lines.append("")

        if (
            signal.entry_usd_von is not None
            or signal.stop_loss_usd_von is not None
            or signal.take_profit_usd_von is not None
        ):
            lines.append("ENTRY / STOP-LOSS / TAKE-PROFIT-ZONE (USD | EUR)")
            lines.append(
                f"  Entry:        {format_money(signal.entry_usd_von)}–{format_money(signal.entry_usd_bis)} | "
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

        if signal.liquidationspreis_geschaetzt_usd is not None or signal.eigenkapitalbedarf_usd is not None:
            lines.append("RISIKO-KENNZAHLEN")
            if signal.liquidationspreis_geschaetzt_usd is not None:
                lines.append(
                    f"  Geschätzter Liquidationspreis: {format_money(signal.liquidationspreis_geschaetzt_usd)} USD"
                )
            if signal.eigenkapitalbedarf_usd is not None:
                lines.append(f"  Eigenkapitalbedarf: {format_money(signal.eigenkapitalbedarf_usd)} USD")
            lines.append("")

        if signal.ausfuehrbarkeit_hinweis:
            lines.append(f"AUSFÜHRBARKEIT\n{signal.ausfuehrbarkeit_hinweis}\n")

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

        self._set_detail_text("\n".join(lines))

    def _set_detail_text(self, text: str) -> None:
        self.detail_text.config(state="normal")
        self.detail_text.delete("1.0", "end")
        self.detail_text.insert("1.0", text)
        self.detail_text.config(state="disabled")

    def _on_analyze_clicked(self) -> None:
        if self._selected_row is None or self._selected_row[0] != "kandidat":
            return
        if self._groq_client is None and self._cerebras_client is None:
            return

        trig = self._selected_row[1]
        self.analyze_button.config(state="disabled")
        self.status_label.config(text=f"Analysiere {trig.symbol} {trig.richtung} …", foreground=theme.info_color())
        thread = threading.Thread(target=self._run_analysis, args=(trig,), daemon=True)
        thread.start()

    def _run_analysis(self, trig) -> None:
        from agent.krypto.hebel_pipeline import generate_hebel_signal

        asset = next((a for a in self._watchlist if a.symbol == trig.symbol), None)
        if asset is None:
            self.after(0, self._on_analysis_done, Exception(f"Asset {trig.symbol} nicht in Watchlist gefunden"))
            return

        def _attempt(llm_client) -> None:
            conn = self._db_conn_factory()
            try:
                generate_hebel_signal(
                    trig, asset, self._watchlist, conn, llm_client,
                    self._coingecko_client, self._kraken_client, self._fred_api_key,
                )
            finally:
                conn.close()

        error = None
        if self._groq_client is not None:
            try:
                _attempt(self._groq_client)
            except Exception as exc:
                error = exc
                if self._cerebras_client is not None:
                    try:
                        _attempt(self._cerebras_client)
                        error = None
                    except Exception as exc2:
                        error = exc2
        elif self._cerebras_client is not None:
            try:
                _attempt(self._cerebras_client)
            except Exception as exc:
                error = exc

        self.after(0, self._on_analysis_done, error)

    def _on_analysis_done(self, error) -> None:
        if error is not None:
            self.status_label.config(text=f"Fehler: {error}", foreground=theme.danger_color())
        else:
            self.status_label.config(text="Fertig.", foreground=theme.info_color())
        self.refresh()
