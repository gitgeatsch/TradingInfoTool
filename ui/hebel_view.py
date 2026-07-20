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

import json
import threading
import tkinter as tk
from tkinter import ttk

import database.db as db
import ui.theme as theme
from ui.formatting import RISIKOFAKTOREN_LEGENDE, format_money, format_risikofaktoren_lines
from ui.heading_tooltip import add_heading_tooltips
from ui.sortable_tree import make_sortable

_LIST_COLUMN_DESCRIPTIONS = {
    "symbol": "Kurzzeichen des Assets.",
    "richtung": "LONG oder SHORT.",
    "status": "Letzte KI-Empfehlung, oder \"Kandidat (wartet auf Analyse)\", falls noch keine Empfehlung vorliegt.",
    "hebel_score": "Bei einer Empfehlung: der final gedeckelte Hebel. Bei einem wartenden Kandidaten: der Trigger-Score (0-100).",
    "these": (
        "Zeithorizont der KI-These, NICHT die empfohlene Haltedauer fuer dich als "
        "Trader: 'Einmaltrade' = kurzlebige, ereignisgetriebene Gegenbewegung "
        "(Zweig Kontra). 'Swing' = bestaetigter mehrtaegiger Trend (Zweig "
        "Trendfolge). Deine eigene Ausfuehrung ist in beiden Faellen identisch: "
        "Position eroeffnen, Stop-Loss setzen, in der Take-Profit-Zone oder am "
        "Stop-Loss aussteigen - siehe Regelwerksmanual."
    ),
    "zeitpunkt": "Wann die Empfehlung berechnet wurde bzw. wann der Kandidat gefunden wurde.",
}

_TRADE_THESIS_LABELS = {"einmal_trade": "Einmaltrade", "swing_strategie": "Swing"}

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
        self, parent, db_conn_factory, watchlist, groq_client,
        coingecko_client, kraken_client, fred_api_key=None, gemini_client=None,
        mistral_client=None, zai_client=None,
    ):
        super().__init__(parent)
        self._db_conn_factory = db_conn_factory
        self._watchlist = watchlist
        self._groq_client = groq_client
        self._gemini_client = gemini_client
        self._mistral_client = mistral_client
        self._zai_client = zai_client
        self._coingecko_client = coingecko_client
        self._kraken_client = kraken_client
        self._fred_api_key = fred_api_key

        # iid -> ("signal", HebelSignal) oder ("kandidat", HebelTrigger)
        self._rows: dict[str, tuple[str, object]] = {}
        self._selected_row: tuple[str, object] | None = None
        # GUI-Refresh-Fix Teil 2 (2026-07-16) - siehe ui/signals_view.py fuer die
        # volle Begruendung: unterdrueckt das durch die periodische selection_set()-
        # Wiederherstellung ausgeloeste <<TreeviewSelect>>, das sonst das rechte
        # Detail-Panel bei jedem 3-Sek.-Refresh unnoetig neu aufgebaut haette.
        self._suppress_select_event = False

        self._build_layout()
        self.refresh()

    def _any_llm_client_available(self) -> bool:
        return (
            self._groq_client is not None or self._mistral_client is not None
            or self._gemini_client is not None or self._zai_client is not None
        )

    def _build_layout(self) -> None:
        paned = ttk.Panedwindow(self, orient="horizontal")
        paned.pack(fill="both", expand=True, padx=8, pady=8)

        left = ttk.Frame(paned)
        paned.add(left, weight=1)

        columns = ("symbol", "richtung", "status", "hebel_score", "these", "zeitpunkt")
        self.tree = ttk.Treeview(left, columns=columns, show="headings", height=16)
        headings = {
            "symbol": "Symbol", "richtung": "Richtung", "status": "Status/Aktion",
            "hebel_score": "Hebel/Score", "these": "These", "zeitpunkt": "Zeitpunkt",
        }
        for col in columns:
            self.tree.heading(col, text=headings[col])
            self.tree.column(col, width=110, anchor="w" if col in ("symbol", "status") else "center")
        self.tree.tag_configure("kandidat", foreground=theme.info_color())
        self._reapply_sort = make_sortable(self.tree)
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
        self.history_button = ttk.Button(
            toolbar, text="Signal-Historie", command=self._on_history_clicked, state="disabled"
        )
        self.history_button.pack(side="left", padx=(8, 0))
        self.status_label = ttk.Label(toolbar, text="", foreground=theme.info_color())
        self.status_label.pack(side="left", padx=(12, 0))

        if not self._any_llm_client_available():
            self.status_label.config(
                text="⚠ Kein Groq-/Mistral-/Gemini-Key gesetzt — manuelle Analyse deaktiviert",
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
            # get_latest_hebel_signal_per_symbol_and_richtung() statt der reinen
            # Pro-Symbol-Variante (2026-07-16, entdeckt bei der These-Spalten-Ergaenzung):
            # LONG/SHORT sind unabhaengige Thesen (siehe hebel_backward_tracking.py) -
            # die Pro-Symbol-Variante haette ein aelteres, weiterhin relevantes Signal der
            # jeweils anderen Richtung stillschweigend aus der Liste verschwinden lassen,
            # sobald fuer dieselbe Symbol die andere Richtung neuer analysiert wurde.
            signals = db.get_latest_hebel_signal_per_symbol_and_richtung(conn)
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
            these_text = _TRADE_THESIS_LABELS.get(sig.trade_thesis_typ, sig.trade_thesis_typ or "-")
            self.tree.insert(
                "", "end", iid=iid,
                values=(sig.symbol, sig.richtung, sig.action, hebel_text, these_text, zeit),
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
                values=(trig.symbol, trig.richtung, "Kandidat (wartet auf Analyse)", score_text, "-", zeit),
                tags=("kandidat",),
            )

        self._reapply_sort()
        theme.restripe_treeview(self.tree)

        if vorher_iid and vorher_iid in self._rows:
            # 2026-07-16, Nutzer-Fund (Detail-Panel resettet trotz Fix weiterhin):
            # <<TreeviewSelect>> wird von selection_set() NICHT synchron gefeuert,
            # sondern erst im naechsten Tk-Event-Loop-Durchlauf (Tcl "event
            # generate" ohne "-when now" haengt hinten an die Event-Queue an) -
            # das Flag sofort im finally-Block zurueckzusetzen kam also zu frueh,
            # das Event traf erst danach ein und wurde NICHT unterdrueckt (per
            # echtem mainloop()-Test bestaetigt, mit synchronem Test/ohne Mainloop
            # unsichtbar geblieben). Fix: Flag erst per after_idle() zuruecksetzen,
            # also NACH allen bereits anstehenden Events (inkl. dem verzoegerten
            # <<TreeviewSelect>>).
            self._suppress_select_event = True
            self.tree.selection_set(vorher_iid)
            self.after_idle(self._clear_suppress_select_event)
            # Nur re-rendern, wenn sich die Zeile tatsaechlich geaendert hat (z.B.
            # neue Analyse fuer denselben Kandidaten) - sonst bleibt das
            # Detail-Panel (inkl. Scroll-Position) unangetastet.
            neue_row = self._rows.get(vorher_iid)
            if neue_row != self._selected_row:
                self._render_selection(neue_row)
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

    def _clear_suppress_select_event(self) -> None:
        self._suppress_select_event = False

    def _on_select(self, event) -> None:
        if self._suppress_select_event:
            return
        selected = self.tree.selection()
        if not selected:
            self._render_selection(None)
            return
        self._render_selection(self._rows.get(selected[0]))

    def _render_selection(self, row) -> None:
        self._selected_row = row
        if row is None:
            self.analyze_button.config(state="disabled")
            self.history_button.config(state="disabled")
            self.action_label.config(text="Keine Auswahl", foreground=theme.default_text_color())
            self.meta_label.config(text="")
            self._set_detail_text("")
            return
        self.history_button.config(state="normal")

        kind, obj = row
        if kind == "kandidat":
            self._render_kandidat(obj)
        else:
            self._render_signal(obj)

    def _render_kandidat(self, trig) -> None:
        can_analyze = self._any_llm_client_available()
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

        # Abschnitt 1 (2026-07-19, Nutzer-Wunsch nach dem echten AVAX-Hebel-
        # Fund: klare Trennung, was deterministisch berechnet ist vs. was die
        # KI bewertet hat vs. eine zusammenfassende Konklusion): nur echte
        # Rechenwerte, nichts vom LLM Erzeugtes.
        lines.append("--- 1. MATHEMATISCH BERECHNET ---")
        if signal.hebel_vorschlag is not None or signal.hebel_final is not None:
            final_text = f"{signal.hebel_final:.2f}x" if signal.hebel_final is not None else "-"
            lines.append(f"Hebel final (gedeckelt): {final_text}")
            if signal.hebel_korrektur_hinweis:
                lines.append(f"  Hinweis: {signal.hebel_korrektur_hinweis}")
        if signal.liquidationspreis_geschaetzt_usd is not None:
            lines.append(f"Geschätzter Liquidationspreis: {format_money(signal.liquidationspreis_geschaetzt_usd)} USD")
        if signal.eigenkapitalbedarf_usd is not None:
            lines.append(f"Eigenkapitalbedarf: {format_money(signal.eigenkapitalbedarf_usd)} USD")
        if signal.hebel_senkung_eigenkapital_nachschuss_eur is not None:
            lines.append(
                f"Eigenkapital-Nachschuss für Hebel-Senkung: "
                f"{format_money(signal.hebel_senkung_eigenkapital_nachschuss_eur)} EUR"
            )
        if signal.ausfuehrbarkeit_hinweis:
            lines.append(f"Ausführbarkeit: {signal.ausfuehrbarkeit_hinweis}")
        lines.append("")

        # Abschnitt 2: alles, was das LLM selbst entschieden/formuliert hat -
        # inkl. gegenargument (2026-07-19 NEU, fehlte bisher komplett, obwohl
        # Regel 13 im SYSTEM_PROMPT es zur Pflicht macht) und Entry/SL/TP-
        # Zonen (vom LLM aus echten Referenzpunkten GEWÄHLT, nicht rein
        # mathematisch determiniert).
        conf_text = f"{signal.confidence_pct:.0f}%" if signal.confidence_pct is not None else "-"
        lines.append(f"--- 2. LLM-BEWERTUNG (Konfidenz {conf_text}) ---")
        if signal.richtung:
            lines.append(f"Richtung: {signal.richtung}")
        if signal.trade_thesis_typ:
            lines.append(f"These: {signal.trade_thesis_typ}")

        top_gruende_pairs = [
            (getattr(signal, f"top_grund_{i}_kategorie"), getattr(signal, f"top_grund_{i}_text"))
            for i in range(1, 6)
        ]
        top_gruende_pairs = [(k, t) for k, t in top_gruende_pairs if t]
        if top_gruende_pairs:
            lines.append("")
            lines.append("Top 5 Gründe:")
            for idx, (kategorie, text) in enumerate(top_gruende_pairs, start=1):
                tag = f"[{kategorie}] " if kategorie else ""
                lines.append(f"  {idx}. {tag}{text}")

        if signal.short_reasoning:
            lines.append(f"\nKurzbegründung:\n{signal.short_reasoning}")
        if signal.long_reasoning_technisch or signal.long_reasoning_fundamental or signal.long_reasoning_makro:
            lines.append("\nLangbegründung:")
            if signal.long_reasoning_technisch:
                lines.append(f"  Technisch: {signal.long_reasoning_technisch}")
            if signal.long_reasoning_fundamental:
                lines.append(f"  Fundamental: {signal.long_reasoning_fundamental}")
            if signal.long_reasoning_makro:
                lines.append(f"  Makro: {signal.long_reasoning_makro}")

        if signal.gegenargument:
            lines.append(f"\nGegenargument (stärkster Einwand gegen diese Empfehlung):\n{signal.gegenargument}")

        if (
            signal.entry_usd_von is not None
            or signal.stop_loss_usd_von is not None
            or signal.take_profit_usd_von is not None
        ):
            lines.append("\nEntry / Stop-Loss / Take-Profit-Zone (USD | EUR):")
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

        if signal.halte_kriterium_bucket:
            lines.append("\nHalte-Kriterium:")
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

        if signal.key_risks_text:
            lines.append("\nWichtigste Risiken:")
            for risk in signal.key_risks_text.split("\n"):
                lines.append(f"  • {risk}")

        if signal.forecast_bull_text or signal.forecast_base_text or signal.forecast_bear_text:
            lines.append("\nForecast-Szenarien:")
            if signal.forecast_bull_text:
                lines.append(f"  Bull ({signal.forecast_bull_prob_pct}%): {signal.forecast_bull_text}")
            if signal.forecast_base_text:
                lines.append(f"  Base ({signal.forecast_base_prob_pct}%): {signal.forecast_base_text}")
            if signal.forecast_bear_text:
                lines.append(f"  Bear ({signal.forecast_bear_prob_pct}%): {signal.forecast_bear_text}")
        lines.append("")

        # Abschnitt 3 (NEU, 2026-07-19): deterministische Risikofaktoren-Liste,
        # bewusst NICHT vom LLM generiert - siehe agent/krypto/hebel_risk_gate.py::
        # compute_risikofaktoren_hebel()-Docstring (echter AVAX-Fund als Ausloeser).
        lines.append("--- 3. KONKLUSION (RISIKOFAKTOREN) ---")
        lines.append(RISIKOFAKTOREN_LEGENDE)
        risikofaktoren_lines = format_risikofaktoren_lines(signal.risikofaktoren_json)
        if risikofaktoren_lines:
            lines.extend(risikofaktoren_lines)
        else:
            lines.append("Keine strukturierten Risikofaktoren verfügbar.")

        self._set_detail_text("\n".join(lines))

    def _set_detail_text(self, text: str) -> None:
        self.detail_text.config(state="normal")
        self.detail_text.delete("1.0", "end")
        self.detail_text.insert("1.0", text)
        self.detail_text.config(state="disabled")

    def _on_analyze_clicked(self) -> None:
        if self._selected_row is None or self._selected_row[0] != "kandidat":
            return
        if not self._any_llm_client_available():
            return

        trig = self._selected_row[1]
        self.analyze_button.config(state="disabled")
        self.status_label.config(text=f"Analysiere {trig.symbol} {trig.richtung} …", foreground=theme.info_color())
        thread = threading.Thread(target=self._run_analysis, args=(trig,), daemon=True)
        thread.start()

    def _run_analysis(self, trig) -> None:
        """Groq-dann-Mistral-dann-Gemini-Fallback (bewusst ohne Budget-/
        Cooldown-Pruefung - ein manueller Klick ist ein expliziter
        Einzel-Wunsch)."""
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
        for llm_client in (self._zai_client, self._mistral_client, self._groq_client, self._gemini_client):
            if llm_client is None:
                continue
            try:
                _attempt(llm_client)
                error = None
                break
            except Exception as exc:
                error = exc

        self.after(0, self._on_analysis_done, error)

    def _on_analysis_done(self, error) -> None:
        if error is not None:
            self.status_label.config(text=f"Fehler: {error}", foreground=theme.danger_color())
        else:
            self.status_label.config(text="Fertig.", foreground=theme.info_color())
        self.refresh()

    def _on_history_clicked(self) -> None:
        """Signal-Historie-Dialog (2026-07-16, mirror ui/signals_view.py::
        SignalHistoryDialog) - macht die Ueberholt-/Ablauf-/Take-Profit-/
        Stop-Loss-/Liquidations-Ergebnisse aus dem Hebel-Backward-Tracking
        erstmals im Hebel-Tab sichtbar (bisher nur per direkter DB-Abfrage
        einsehbar). Nach (symbol, richtung) gefiltert, da LONG/SHORT
        unabhaengige Thesen sind - identisches Prinzip wie die neue
        Ueberholt-Erkennung."""
        if self._selected_row is None:
            return
        _, obj = self._selected_row
        symbol, richtung = obj.symbol, obj.richtung
        conn = self._db_conn_factory()
        try:
            history = db.get_hebel_signal_history(conn, symbol, richtung)
        finally:
            conn.close()
        HebelSignalHistoryDialog(self, symbol, richtung, history)


_HEBEL_OUTCOME_LABELS = {
    "offen": "Offen",
    "take_profit_erreicht": "Take-Profit erreicht",
    "stop_loss_erreicht": "Stop-Loss erreicht",
    "liquidation_wahrscheinlich": "Liquidation wahrscheinlich",
    "abgelaufen_unentschieden": "Abgelaufen (unentschieden)",
    "ueberholt_durch_neuere_analyse": "Überholt (neuere Analyse vorhanden)",
    "nicht_anwendbar": "Nicht anwendbar",
}


def _hebel_outcome_color(status: str | None):
    if status == "take_profit_erreicht":
        return theme.umgesetzt_color()
    if status in ("stop_loss_erreicht", "liquidation_wahrscheinlich"):
        return theme.danger_color()
    if status in ("abgelaufen_unentschieden", "ueberholt_durch_neuere_analyse"):
        return theme.stale_color()
    if status == "offen":
        return theme.info_color()
    return theme.default_text_color()


_HEBEL_SIGNAL_HISTORY_COLUMN_DESCRIPTIONS = {
    "datum": "Zeitpunkt der Analyse.",
    "aktion": "Empfohlene Aktion.",
    "konfidenz": "Von der KI angegebene Konfidenz (0-100%).",
    "anbieter": "LLM-Anbieter:Modell, der dieses Signal berechnet hat.",
    "outcome": "Ergebnis des Hebel-Backward-Trackings (taeglicher 06:00-Job).",
}


def _format_json_pretty(raw: str | None) -> str:
    if not raw:
        return "-"
    try:
        return json.dumps(json.loads(raw), indent=2, ensure_ascii=False)
    except (TypeError, ValueError):
        return raw


class HebelSignalHistoryDialog(tk.Toplevel):
    """Hebel-Pendant zu ui/signals_view.py::SignalHistoryDialog - reine
    Anzeige aller bisherigen Hebel-Signale fuer EIN (symbol, richtung),
    inkl. Outcome-Status (Take-Profit/Stop-Loss/Liquidation/Abgelaufen/
    Überholt/Offen)."""

    def __init__(self, parent, symbol: str, richtung: str, history: list) -> None:
        super().__init__(parent)
        self.title(f"Hebel-Signal-Historie — {symbol} ({richtung})")
        self.resizable(True, True)
        self.transient(parent)
        self.grab_set()
        self.geometry("760x420")

        frame = ttk.Frame(self, padding=12)
        frame.pack(fill="both", expand=True)

        if not history:
            ttk.Label(frame, text="Noch keine Hebel-Signale für diese Richtung vorhanden.").pack(anchor="w")
            ttk.Button(frame, text="Schließen", command=self.destroy).pack(anchor="e", pady=(10, 0))
            return

        columns = ("datum", "aktion", "konfidenz", "anbieter", "outcome")
        tree = ttk.Treeview(frame, columns=columns, show="headings", height=14)
        headings = {
            "datum": "Datum", "aktion": "Aktion", "konfidenz": "Konfidenz",
            "anbieter": "Anbieter", "outcome": "Ergebnis",
        }
        for col in columns:
            tree.heading(col, text=headings[col])
            tree.column(col, width=150 if col != "outcome" else 200, anchor="w")
        add_heading_tooltips(tree, _HEBEL_SIGNAL_HISTORY_COLUMN_DESCRIPTIONS)
        tree.pack(fill="both", expand=True)

        self._history_by_item: dict[str, object] = {}
        for signal in history:
            when = signal.created_at[:16].replace("T", " ") if signal.created_at else "-"
            konfidenz = f"{signal.confidence_pct:.0f} %" if signal.confidence_pct is not None else "-"
            status = signal.outcome_status
            outcome_text = _HEBEL_OUTCOME_LABELS.get(status, "—") if status else "—"
            if status in ("take_profit_erreicht", "stop_loss_erreicht") and signal.outcome_realisiertes_crv is not None:
                outcome_text += f" (CRV {signal.outcome_realisiertes_crv:.2f})"
            item_id = tree.insert(
                "", "end",
                values=(when, signal.action, konfidenz, signal.llm_model or "-", outcome_text),
                tags=(status or "none",),
            )
            self._history_by_item[item_id] = signal
            tree.tag_configure(status or "none", foreground=_hebel_outcome_color(status))
        theme.restripe_treeview(tree)
        tree.bind("<Double-1>", self._on_row_double_click)

        ttk.Label(
            frame, text="Doppelklick auf eine Zeile zeigt die zugehörige LLM-Anfrage/Antwort.",
            foreground=theme.info_color(),
        ).pack(anchor="w", pady=(6, 0))

        ttk.Button(frame, text="Schließen", command=self.destroy).pack(anchor="e", pady=(10, 0))

    def _on_row_double_click(self, event) -> None:
        item_id = event.widget.identify_row(event.y)
        signal = self._history_by_item.get(item_id)
        if signal is None:
            return
        HebelLlmAbfrageDialog(self, signal.symbol, signal)


class HebelLlmAbfrageDialog(tk.Toplevel):
    """Hebel-Pendant zu ui/signals_view.py::LlmAbfrageDialog - zeigt facts_json +
    Roh-Antwort eines historischen Hebel-Signals (2026-07-18, gleicher Nutzer-Wunsch)."""

    def __init__(self, parent, symbol: str, signal) -> None:
        super().__init__(parent)
        self.title(f"LLM-Abfrage — {symbol}")
        self.resizable(True, True)
        self.transient(parent)
        self.grab_set()
        self.geometry("640x600")

        frame = ttk.Frame(self, padding=12)
        frame.pack(fill="both", expand=True)

        zeitpunkt = signal.created_at[:16].replace("T", " ") if signal.created_at else "-"
        ttk.Label(
            frame, text=f"Anbieter: {signal.llm_model or '-'}   ·   Berechnet: {zeitpunkt}",
            font=("", 10, "bold"),
        ).pack(anchor="w", pady=(0, 8))

        ttk.Label(frame, text="Angefragte Fakten (facts_json):").pack(anchor="w")
        facts_frame = ttk.Frame(frame)
        facts_frame.pack(fill="both", expand=True, pady=(0, 8))
        facts_text = tk.Text(facts_frame, height=14, wrap="word")
        facts_scroll = ttk.Scrollbar(facts_frame, orient="vertical", command=facts_text.yview)
        facts_text.configure(yscrollcommand=facts_scroll.set)
        facts_text.pack(side="left", fill="both", expand=True)
        facts_scroll.pack(side="right", fill="y")
        facts_text.insert("1.0", _format_json_pretty(signal.facts_json))
        facts_text.config(state="disabled")

        ttk.Label(frame, text="Roh-Antwort der KI:").pack(anchor="w")
        response_frame = ttk.Frame(frame)
        response_frame.pack(fill="both", expand=True)
        response_text = tk.Text(response_frame, height=14, wrap="word")
        response_scroll = ttk.Scrollbar(response_frame, orient="vertical", command=response_text.yview)
        response_text.configure(yscrollcommand=response_scroll.set)
        response_text.pack(side="left", fill="both", expand=True)
        response_scroll.pack(side="right", fill="y")
        response_text.insert("1.0", _format_json_pretty(signal.groq_raw_response))
        response_text.config(state="disabled")

        ttk.Button(frame, text="Schließen", command=self.destroy).pack(anchor="e", pady=(10, 0))
