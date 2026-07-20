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

import json
import threading
import tkinter as tk
from tkinter import ttk

import database.db as db
import ui.theme as theme
from ui.formatting import RISIKOFAKTOREN_LEGENDE, format_money, format_risikofaktoren_lines
from ui.heading_tooltip import add_heading_tooltips
from ui.sortable_tree import make_sortable

_SIGNAL_LIST_COLUMN_DESCRIPTIONS = {
    "symbol": "Kurzzeichen des Assets (z. B. an der Börse/CoinGecko).",
    "name": "Vollständiger Name des Assets.",
    "letztes_signal": "Zuletzt berechnete Empfehlung (KAUFEN/NACHKAUFEN/HALTEN/VERKAUFEN/TAUSCHEN).",
    "berechnet": "Zeitpunkt, an dem dieses Signal zuletzt berechnet wurde.",
}

_SIGNAL_HISTORY_COLUMN_DESCRIPTIONS = {
    "datum": "Zeitpunkt, an dem dieses Signal berechnet wurde.",
    "aktion": "Damals empfohlene Aktion (KAUFEN/NACHKAUFEN/HALTEN/VERKAUFEN/TAUSCHEN).",
    "konfidenz": "KI-Konfidenz in Prozent zum Zeitpunkt der Berechnung.",
    "anbieter": "LLM-Anbieter:Modell, der dieses Signal berechnet hat.",
    "outcome": (
        "Ergebnis der Selbstverifikation (Backward-Tracking): ob Take-Profit oder "
        "Stop-Loss erreicht wurde, oder ob das Signal noch offen/abgelaufen ist."
    ),
}


def _format_json_pretty(raw: str | None) -> str:
    if not raw:
        return "-"
    try:
        return json.dumps(json.loads(raw), indent=2, ensure_ascii=False)
    except (TypeError, ValueError):
        return raw

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
        fred_api_key=None, gemini_client=None, mistral_client=None,
    ):
        super().__init__(parent)
        self._db_conn_factory = db_conn_factory
        # Multi-Asset-Tracking (Nutzer-Idee 2026-07-09): Aktien/ETF/Rohstoffe werden
        # HIER bewusst herausgefiltert, nicht nur aus der Anzeige-Liste - die Krypto-
        # Agent-Pipeline (Regime/Risiko-Gate) "weiss" nichts von diesen Assetklassen.
        # Wuerden sie in _full_watchlist landen, wuerde
        # agent/krypto/risk_gate.py::_portfolio_values_usd() ihren Wert in die
        # Gesamtportfolio-Summe einrechnen und damit die Krypto-Allokations-Prozente
        # verzerren, obwohl das Risiko-Gate nichts von ihnen "weiss".
        krypto_watchlist = [a for a in watchlist if a.assetklasse == "krypto"]
        self._full_watchlist = krypto_watchlist  # generate_signal braucht ALLE
        # Krypto-Assets (Stablecoins zaehlen z.B. als Cash-Reserve) - nur die
        # Anzeige-Liste filtert zusaetzlich Stablecoins raus.
        self._watchlist = [a for a in krypto_watchlist if not a.ist_cash_aequivalent]
        # Non-Krypto-Agent-Pipeline Phase 1 (2026-07-15, agent/aktien/pipeline.py) -
        # eigene, von der Krypto-Portfolio-Summe getrennte Watchlist (analoges
        # Prinzip wie oben: RM-2-Allokations-Prozent soll sich auf den Aktien-Anteil
        # beziehen, nicht auf das gemischte Gesamtportfolio). ETFs (Hedge-Instrumente)
        # folgen als eigene Pipeline (agent/hedge/), deshalb hier bewusst nur
        # "aktien", nicht "assetklasse != 'krypto'".
        self._aktien_watchlist = [a for a in watchlist if a.assetklasse == "aktien"]
        # Multi-Asset-Roadmap Phase 2 (2026-07-18, agent/rohstoff/pipeline.py) -
        # gleiches Prinzip wie Aktien: eigene Watchlist-Teilmenge fuer die Anzeige/
        # Auswahl, generate_signal() dort filtert intern erneut fuer RM-2.
        self._rohstoff_watchlist = [a for a in watchlist if a.assetklasse == "rohstoffe"]
        # Portfolio-Hedge-Instrumente (2026-07-18, agent/hedge/pipeline.py) - kein
        # eigenes assetklasse-Feld (bleiben "etf", siehe SYMBOL_ZU_HEBEL_FAKTOR dort),
        # daher per Symbol statt per Assetklasse gefiltert.
        from agent.hedge.pipeline import SYMBOL_ZU_HEBEL_FAKTOR as _hedge_symbole
        self._hedge_watchlist = [a for a in watchlist if a.symbol in _hedge_symbole]
        # Themen-ETFs (2026-07-18, agent/themen_etf/pipeline.py) - restliche
        # assetklasse=="etf"-Assets, die NICHT Hedge-Instrumente sind (VVMX/X136/
        # EXH3/CEBS/ISOC). Standen bis hierher ohne jede Pipeline in der Watchlist
        # (Multi-Asset-Vollstaendigkeitspruefung, siehe Memory project_multi_asset_batch.md).
        self._themen_etf_watchlist = [
            a for a in watchlist if a.assetklasse == "etf" and a.symbol not in _hedge_symbole
        ]
        # agent/aktien/pipeline.py::generate_signal() braucht die VOLLSTAENDIGE
        # Watchlist (inkl. BTC) fuer compute_current_regime() - filtert intern selbst
        # auf die Aktien-Teilmenge fuer RM-2, siehe dessen Docstring.
        self._raw_watchlist = watchlist
        self._groq_client = groq_client
        # 2026-07-14: Einzel-Klick-Button UND Batch-Button teilen sich denselben
        # Groq-dann-Mistral-dann-Gemini-Fallback wie ui/hebel_view.py
        # (Batch: pro Asset einzeln entschieden, siehe agent/krypto/signal_batch.py).
        self._gemini_client = gemini_client
        self._mistral_client = mistral_client
        self._coingecko_client = coingecko_client
        self._kraken_client = kraken_client
        self._fred_api_key = fred_api_key  # optional (P-8) - ohne Key liefert
        # agent/krypto/pipeline.py fuer die FRED-Felder sauber None statt abzustuerzen.
        self._selected_asset = None
        self._current_signal = None
        # GUI-Refresh-Fix Teil 2 (2026-07-16, Nutzer-Fund): selection_set() in
        # _refresh_list() feuert <<TreeviewSelect>> auch, wenn dieselbe Zeile
        # erneut ausgewaehlt wird - das hat bei JEDEM periodischen Refresh das
        # rechte Detail-Panel komplett neu aufgebaut (Scroll-Position verloren),
        # obwohl sich am Signal meistens gar nichts geaendert hat. Dieser Guard
        # unterdrueckt den dadurch ausgeloesten _on_select().
        self._suppress_select_event = False

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
        self._reapply_sort = make_sortable(self.tree)
        add_heading_tooltips(self.tree, _SIGNAL_LIST_COLUMN_DESCRIPTIONS)
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
        # Batch-Signal-Berechnung (2026-07-13) - manueller "genau jetzt sofort"-Pfad,
        # bleibt bestehen neben dem automatischen Budget-Allocator (2026-07-14, Phase 5,
        # siehe agent/krypto/budget_allocator.py), siehe agent/krypto/signal_batch.py
        # Modul-Docstring fuer die Budget-Herleitung. Braucht keinen Asset-Fokus,
        # daher nicht an self._selected_asset gekoppelt wie compute_button/history_button.
        self.batch_button = ttk.Button(
            toolbar, text="Fällige Signale jetzt berechnen", command=self._on_batch_clicked,
            state="normal" if self._any_llm_client_available() else "disabled",
        )
        self.batch_button.pack(side="left", padx=(6, 0))
        self.status_label = ttk.Label(toolbar, text="", foreground=theme.info_color())
        self.status_label.pack(side="left", padx=(12, 0))

        if not self._any_llm_client_available():
            self.status_label.config(
                text="⚠ Kein GROQ_API_KEY/MISTRAL_API_KEY/GEMINI_API_KEY gesetzt — Signalberechnung deaktiviert (siehe .env)",
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

    def _any_llm_client_available(self) -> bool:
        return (
            self._groq_client is not None or self._mistral_client is not None
            or self._gemini_client is not None
        )

    def _asset_by_symbol(self, symbol: str):
        return next(
            (
                a for a in self._watchlist + self._aktien_watchlist + self._rohstoff_watchlist
                + self._hedge_watchlist + self._themen_etf_watchlist
                if a.symbol == symbol
            ),
            None,
        )

    def _refresh_list(self) -> None:
        alle_assets = (
            self._watchlist + self._aktien_watchlist + self._rohstoff_watchlist
            + self._hedge_watchlist + self._themen_etf_watchlist
        )
        conn = self._db_conn_factory()
        try:
            latest_by_symbol = {a.symbol: db.get_latest_signal(conn, a.symbol) for a in alle_assets}
        finally:
            conn.close()

        # GUI-Refresh-Fix (2026-07-16, Nutzer-Fund): Auswahl vor dem Neuaufbau
        # merken + danach wiederherstellen (iid war hier schon stabil), analog
        # zu ui/hebel_view.py::refresh().
        vorher_selected = self.tree.selection()
        vorher_iid = vorher_selected[0] if vorher_selected else None
        for item in self.tree.get_children():
            self.tree.delete(item)

        for asset in sorted(alle_assets, key=lambda a: a.symbol):
            sig = latest_by_symbol.get(asset.symbol)
            action_text = sig.action if sig else "-"
            created_text = sig.created_at[:16].replace("T", " ") if sig else "-"
            self.tree.insert("", "end", iid=asset.symbol, values=(asset.symbol, asset.name, action_text, created_text))
        self._reapply_sort()
        theme.restripe_treeview(self.tree)
        if vorher_iid and self.tree.exists(vorher_iid):
            # 2026-07-16, Nutzer-Fund (Detail-Panel resettet trotz Fix weiterhin):
            # <<TreeviewSelect>> feuert asynchron (Tk-Event-Queue), nicht sofort -
            # das Flag im finally-Block zurueckzusetzen war zu frueh, das
            # verzoegerte Event traf danach ein und wurde NICHT unterdrueckt (per
            # echtem mainloop()-Test bestaetigt). Fix: Flag erst per
            # after_idle() zuruecksetzen (nach allen bereits anstehenden Events).
            self._suppress_select_event = True
            self.tree.selection_set(vorher_iid)
            self.after_idle(self._clear_suppress_select_event)
            # Nur re-rendern, wenn sich das Signal fuer die ausgewaehlte Zeile
            # tatsaechlich geaendert hat (z.B. neuer automatischer Signal-Lauf) -
            # sonst bleibt das Detail-Panel (inkl. Scroll-Position) unangetastet.
            neues_signal = latest_by_symbol.get(vorher_iid)
            if neues_signal != self._current_signal:
                self._selected_asset = self._asset_by_symbol(vorher_iid)
                can_compute = self._any_llm_client_available()
                self.compute_button.config(state="normal" if can_compute else "disabled")
                self.history_button.config(state="normal")
                self._render_signal(self._selected_asset, neues_signal)

    def _clear_suppress_select_event(self) -> None:
        self._suppress_select_event = False

    def _on_select(self, event) -> None:
        if self._suppress_select_event:
            return
        selected = self.tree.selection()
        if not selected:
            return
        symbol = selected[0]
        self._selected_asset = self._asset_by_symbol(symbol)
        can_compute = self._any_llm_client_available()
        self.compute_button.config(state="normal" if can_compute else "disabled")
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
                f"Anbieter: {signal.groq_model or '-'} · "
                f"Berechnet: {signal.created_at[:16].replace('T', ' ')}"
            )
        )

        gate_notes = []
        if not signal.gate_passed:
            gate_notes.append(f"⚠ Datenqualitäts-Gate nicht bestanden: {signal.gate_reason}")
        if signal.risk_veto:
            gate_notes.append(f"⚠ Risiko-Veto: {signal.risk_veto_reason}")
        # Cash-Veto (2026-07-18, Detailanalyse "Anzeige/Info bei Cash-Block") -
        # bewusst UNABHAENGIG von signal.risk_veto geprueft: risk_veto feuert nur,
        # wenn das Modell die kauf_erlaubt-Regel missachtet hat, cash_veto
        # dagegen IMMER, wenn RM-4 bei dieser Bewertung aktiv war - auch wenn das
        # Modell selbst schon regelkonform HALTEN gesagt hat (der bisher
        # unsichtbare Normalfall, siehe risk_gate.py-Docstring).
        if signal.cash_veto:
            gate_notes.append(f"⚠ WARNUNG - Cash-Veto (System beeinträchtigt): {signal.cash_veto_reason}")
        self.gate_label.config(text="\n".join(gate_notes))

        # 2026-07-19 (Nutzer-Wunsch nach dem echten AVAX-Hebel-Fund): E-Mail
        # UND App-Detail-Panel klar in drei Abschnitte getrennt - 1. was ist
        # deterministisch berechnet, 2. was sagt die LLM-Bewertung, 3. eine
        # zusammenfassende Konklusion mit positiven/neutralen/negativen
        # Risikofaktoren (deterministisch, NICHT vom LLM). Drei getrennte
        # Listen statt einer, damit die Reihenfolge (AZ-4-Bausteine oben,
        # LLM-Inhalte in der Mitte, Risikofaktoren am Ende) unabhaengig von
        # der Berechnungsreihenfolge im Code ist.
        abschnitt_1: list[str] = []
        abschnitt_2: list[str] = []

        # AZ-4-Tranchen (2026-07-12): rein informativ, siehe agent/krypto/analyst.py.
        # entry_usd_von/_bis bleibt bei aktiven Tranchen die Gesamtspanne - Zeile wird
        # dann als "Gesamt-Zone" statt "Kauf-Zone" beschriftet.
        tranchen = None
        if signal.tranchen_json:
            try:
                tranchen = sorted(json.loads(signal.tranchen_json), key=lambda t: t.get("rang", 0))
            except (ValueError, TypeError):
                tranchen = None

        # --- Abschnitt 1: Mathematisch berechnet (AZ-4-Bausteine, vollstaendig
        # deterministisch, NICHT vom LLM) ---
        if asset.symbol in ("BTC", "ETH"):
            conn = self._db_conn_factory()
            try:
                macro_snap = db.get_latest_macro_snapshot(conn)
            finally:
                conn.close()
            if macro_snap is not None:
                von = macro_snap.btc_boden_zielzone_von if asset.symbol == "BTC" else macro_snap.eth_boden_zielzone_von
                bis = macro_snap.btc_boden_zielzone_bis if asset.symbol == "BTC" else macro_snap.eth_boden_zielzone_bis
                if von is not None and bis is not None:
                    abschnitt_1.append("Boden-Zielzone (Wahrscheinlichkeits-Zone, kein hartes Kursziel):")
                    abschnitt_1.append(f"  {format_money(von)}–{format_money(bis)} USD")
                    if asset.symbol == "ETH":
                        abschnitt_1.append("  ⚠ Niedrige Konfidenz (nur 2 historische ETH-Zyklus-Tiefpunkte)")
                    if macro_snap.equities_sp500_drawdown_pct is not None or macro_snap.equities_nasdaq_drawdown_pct is not None:
                        sp500_text = (
                            f"{macro_snap.equities_sp500_drawdown_pct:+.1f}%"
                            if macro_snap.equities_sp500_drawdown_pct is not None else "n/v"
                        )
                        nasdaq_text = (
                            f"{macro_snap.equities_nasdaq_drawdown_pct:+.1f}%"
                            if macro_snap.equities_nasdaq_drawdown_pct is not None else "n/v"
                        )
                        abschnitt_1.append(f"  Aktien-Kontext: S&P 500 {sp500_text}, Nasdaq {nasdaq_text} vom Hoch")
                    abschnitt_1.append("")

        if asset.symbol in ("BTC", "ETH") and signal.cash_reserve_ziel_gesamt_usd is not None:
            abschnitt_1.append("Cash-Reserve-Ziel (Info, keine harte Regel - RM-4-Minimum bleibt bindend):")
            abschnitt_1.append(f"  Gesamt: {format_money(signal.cash_reserve_ziel_gesamt_usd)} USD")
            abschnitt_1.append(
                f"  davon BTC: {format_money(signal.cash_reserve_ziel_btc_usd)} USD, "
                f"ETH: {format_money(signal.cash_reserve_ziel_eth_usd)} USD"
            )
            if signal.cash_reserve_ziel_begruendung:
                abschnitt_1.append(f"  {signal.cash_reserve_ziel_begruendung}")
            abschnitt_1.append("")

        # --- Abschnitt 2: LLM-Bewertung (Top-Gruende, Begruendungen, Zonen,
        # Positionsgroesse/Tranchen, Gegenargument [NEU], Halte-Kriterium,
        # Risiken, Forecast, Tausch-Ziel - alles vom Modell gewaehlt/erzeugt,
        # auch wenn aus echten Referenzpunkten abgeleitet) ---
        top_gruende_pairs = [
            (getattr(signal, f"top_grund_{i}_kategorie"), getattr(signal, f"top_grund_{i}_text"))
            for i in range(1, 6)
        ]
        top_gruende_pairs = [(k, t) for k, t in top_gruende_pairs if t]
        if top_gruende_pairs:
            abschnitt_2.append("Top 5 Gründe:")
            for idx, (kategorie, text) in enumerate(top_gruende_pairs, start=1):
                tag = f"[{kategorie}] " if kategorie else ""
                abschnitt_2.append(f"  {idx}. {tag}{text}")
            abschnitt_2.append("")

        if signal.short_reasoning:
            abschnitt_2.append(f"Kurzbegründung:\n{signal.short_reasoning}\n")
        if signal.long_reasoning_technisch or signal.long_reasoning_fundamental or signal.long_reasoning_makro:
            abschnitt_2.append("Langbegründung:")
            if signal.long_reasoning_technisch:
                abschnitt_2.append(f"  Technisch: {signal.long_reasoning_technisch}")
            if signal.long_reasoning_fundamental:
                abschnitt_2.append(f"  Fundamental: {signal.long_reasoning_fundamental}")
            if signal.long_reasoning_makro:
                abschnitt_2.append(f"  Makro: {signal.long_reasoning_makro}")
            abschnitt_2.append("")

        if signal.gegenargument:
            abschnitt_2.append(f"Gegenargument (stärkster Einwand gegen diese Empfehlung):\n{signal.gegenargument}\n")

        if signal.position_size_usd or signal.position_size_eur or signal.position_size_note:
            abschnitt_2.append(
                f"Positionsgröße:\n{format_money(signal.position_size_usd)} USD / "
                f"{format_money(signal.position_size_eur)} EUR"
            )
            if signal.position_size_note:
                abschnitt_2.append(signal.position_size_note)
            abschnitt_2.append("")

        if signal.entry_usd_von is not None or signal.stop_loss_usd_von is not None or signal.take_profit_usd_von is not None:
            abschnitt_2.append("Kauf-Zone / Stop-Loss-Zone / Take-Profit-Zone (USD | EUR):")
            entry_label = "Gesamt-Zone: " if tranchen else "Kauf-Zone:   "
            abschnitt_2.append(
                f"  {entry_label} {format_money(signal.entry_usd_von)}–{format_money(signal.entry_usd_bis)} | "
                f"{format_money(signal.entry_eur_von)}–{format_money(signal.entry_eur_bis)}"
            )
            abschnitt_2.append(
                f"  Stop-Loss:    {format_money(signal.stop_loss_usd_von)}–{format_money(signal.stop_loss_usd_bis)} | "
                f"{format_money(signal.stop_loss_eur_von)}–{format_money(signal.stop_loss_eur_bis)}"
            )
            abschnitt_2.append(
                f"  Take-Profit:  {format_money(signal.take_profit_usd_von)}–{format_money(signal.take_profit_usd_bis)} | "
                f"{format_money(signal.take_profit_eur_von)}–{format_money(signal.take_profit_eur_bis)}"
            )
            abschnitt_2.append("")

            if tranchen:
                abschnitt_2.append("AZ-4-Tranchen (Info, keine automatische Ausführung):")
                gesamt_usd = signal.position_size_usd
                for eintrag in tranchen:
                    anteil = eintrag.get("anteil_prozent")
                    zone = eintrag.get("zone", {})
                    betrag_text = ""
                    if gesamt_usd and anteil is not None:
                        betrag_text = f" (~{format_money(gesamt_usd * anteil / 100)} USD)"
                    abschnitt_2.append(
                        f"  Tranche {eintrag.get('rang')}: {anteil:g}%{betrag_text} bei "
                        f"{format_money(zone.get('usd_von'))}–{format_money(zone.get('usd_bis'))} USD | "
                        f"{format_money(zone.get('eur_von'))}–{format_money(zone.get('eur_bis'))} EUR"
                    )
                    if eintrag.get("trigger_bedingung"):
                        abschnitt_2.append(f"    Trigger: {eintrag['trigger_bedingung']}")
                abschnitt_2.append("")
        elif signal.entry_usd or signal.stop_loss_usd or signal.take_profit_usd:
            abschnitt_2.append("Einstieg / Stop-Loss / Take-Profit (USD | EUR):")
            abschnitt_2.append(f"  Entry:        {format_money(signal.entry_usd)} | {format_money(signal.entry_eur)}")
            abschnitt_2.append(f"  Stop-Loss:    {format_money(signal.stop_loss_usd)} | {format_money(signal.stop_loss_eur)}")
            abschnitt_2.append(f"  Take-Profit:  {format_money(signal.take_profit_usd)} | {format_money(signal.take_profit_eur)}")
            abschnitt_2.append("")

        if signal.halte_kriterium_bucket:
            abschnitt_2.append("Halte-Kriterium:")
            abschnitt_2.append(f"  Grobe Einordnung: {signal.halte_kriterium_bucket}")
            if signal.halte_kriterium_ziel_preis_usd or signal.halte_kriterium_ziel_preis_eur:
                abschnitt_2.append(
                    f"  Ziel-Kurs: {format_money(signal.halte_kriterium_ziel_preis_usd)} USD / "
                    f"{format_money(signal.halte_kriterium_ziel_preis_eur)} EUR"
                )
            if signal.halte_kriterium_ziel_datum:
                abschnitt_2.append(f"  Ziel-Datum: {signal.halte_kriterium_ziel_datum}")
            if signal.halte_kriterium_bedingung_text:
                abschnitt_2.append(f"  Bedingung: {signal.halte_kriterium_bedingung_text}")
            if signal.halte_kriterium_reasoning:
                abschnitt_2.append(f"  Begründung: {signal.halte_kriterium_reasoning}")
            abschnitt_2.append("")
        elif signal.holding_duration:
            abschnitt_2.append(f"Haltedauer:\n{signal.holding_duration} — {signal.holding_duration_reason}\n")

        if signal.key_risks_text:
            abschnitt_2.append("Wichtigste Risiken:")
            for risk in signal.key_risks_text.split("\n"):
                abschnitt_2.append(f"  • {risk}")
            abschnitt_2.append("")

        if signal.forecast_bull_text or signal.forecast_base_text or signal.forecast_bear_text:
            abschnitt_2.append("Forecast-Szenarien:")
            if signal.forecast_bull_text:
                abschnitt_2.append(f"  Bull ({signal.forecast_bull_prob_pct}%): {signal.forecast_bull_text}")
            if signal.forecast_base_text:
                abschnitt_2.append(f"  Base ({signal.forecast_base_prob_pct}%): {signal.forecast_base_text}")
            if signal.forecast_bear_text:
                abschnitt_2.append(f"  Bear ({signal.forecast_bear_prob_pct}%): {signal.forecast_bear_text}")
            abschnitt_2.append("")

        if signal.tauschen_target_symbol:
            abschnitt_2.append(f"Tausch-Ziel:\n{signal.tauschen_target_symbol}\n")

        # --- Abschnitt 3: Konklusion (Risikofaktoren, NEU 2026-07-19) -
        # deterministisch aus agent/krypto/risk_gate.py::compute_risikofaktoren(),
        # bewusst NICHT vom LLM (siehe dortigen Docstring, echter AVAX-Fund). ---
        risikofaktoren_lines = format_risikofaktoren_lines(signal.risikofaktoren_json)

        lines = ["--- 1. MATHEMATISCH BERECHNET ---"]
        lines.extend(abschnitt_1 if abschnitt_1 else ["(keine assetspezifischen Rechenwerte für dieses Symbol)", ""])
        conf_text_2 = f"{signal.confidence_pct:.0f}%" if signal.confidence_pct is not None else "-"
        lines.append(f"--- 2. LLM-BEWERTUNG (Konfidenz {conf_text_2}) ---")
        lines.extend(abschnitt_2)
        lines.append("--- 3. KONKLUSION (RISIKOFAKTOREN) ---")
        lines.append(RISIKOFAKTOREN_LEGENDE)
        lines.extend(risikofaktoren_lines if risikofaktoren_lines else ["Keine strukturierten Risikofaktoren verfügbar."])

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
        if asset is None or not self._any_llm_client_available():
            return

        self.compute_button.config(state="disabled")
        self.status_label.config(text=f"Berechne Signal für {asset.symbol} …", foreground=theme.info_color())

        thread = threading.Thread(target=self._run_pipeline, args=(asset,), daemon=True)
        thread.start()

    def _run_pipeline(self, asset) -> None:
        """Groq-dann-Mistral-dann-Gemini-Fallback, analog
        ui/hebel_view.py::_run_analysis() - ein manueller Einzel-Klick soll
        nicht hart mit dem rohen Groq-429-Fehler abbrechen, wenn Mistral/
        Gemini noch Kapazitaet haben.

        2026-07-15: verzweigt nach assetklasse - Aktien laufen ueber die neue
        agent/aktien/pipeline.py (siehe deren Modul-Docstring fuer die
        Architektur-Begruendung), Krypto weiterhin ueber agent/krypto/pipeline.py."""
        def _attempt(llm_client):
            conn = self._db_conn_factory()
            try:
                if asset.assetklasse == "aktien":
                    from agent.aktien.pipeline import generate_signal as generate_aktien_signal

                    return generate_aktien_signal(asset, self._raw_watchlist, conn, llm_client, self._coingecko_client)

                if asset.assetklasse == "rohstoffe":
                    from agent.rohstoff.pipeline import generate_signal as generate_rohstoff_signal

                    return generate_rohstoff_signal(asset, self._raw_watchlist, conn, llm_client, self._coingecko_client)

                if asset.symbol in {a.symbol for a in self._hedge_watchlist}:
                    from agent.hedge.pipeline import generate_signal as generate_hedge_signal

                    return generate_hedge_signal(asset, self._raw_watchlist, conn, llm_client, self._coingecko_client)

                if asset.symbol in {a.symbol for a in self._themen_etf_watchlist}:
                    from agent.themen_etf.pipeline import generate_signal as generate_themen_etf_signal

                    return generate_themen_etf_signal(asset, self._raw_watchlist, conn, llm_client, self._coingecko_client)

                from agent.krypto.pipeline import generate_signal

                return generate_signal(
                    asset, self._full_watchlist, conn, llm_client, self._coingecko_client, self._kraken_client,
                    fred_api_key=self._fred_api_key,
                )
            finally:
                conn.close()

        signal, error = None, None
        for llm_client in (self._groq_client, self._mistral_client, self._gemini_client):
            if llm_client is None:
                continue
            try:
                signal = _attempt(llm_client)
                error = None
                break
            except Exception as exc:  # noqa: BLE001 - an die UI durchreichen statt den Thread stumm sterben zu lassen
                error = exc

        self.after(0, self._on_pipeline_done, asset, signal, error)

    def _on_pipeline_done(self, asset, signal, error) -> None:
        can_compute = self._any_llm_client_available()
        self.compute_button.config(state="normal" if can_compute else "disabled")
        if error is not None:
            self.status_label.config(text=f"Fehler: {error}", foreground=theme.danger_color())
            return
        self.status_label.config(text="Fertig.", foreground=theme.info_color())
        self._refresh_list()
        if self._selected_asset is not None and self._selected_asset.symbol == asset.symbol:
            self._render_signal(asset, signal)

    def _on_batch_clicked(self) -> None:
        import scheduler.background as background

        # Non-blocking Check (wie remote/server.py::api_refresh_prices()) -
        # verhindert einen doppelten gleichzeitigen Lauf bei Mehrfach-Klick.
        # Das eigentliche Acquire passiert im Hintergrund-Thread selbst
        # (_run_batch()).
        if background.signal_batch_lock.locked():
            self.status_label.config(
                text="Batch-Berechnung läuft bereits (Scheduler oder vorheriger Klick) …",
                foreground=theme.warn_color(),
            )
            return

        self.batch_button.config(state="disabled")
        self.status_label.config(text="Prüfe fällige Assets …", foreground=theme.info_color())
        thread = threading.Thread(target=self._run_batch, daemon=True)
        thread.start()

    def _set_status(self, text: str, color: str) -> None:
        """Kleiner Helper, damit self.after(0, ...) einfache Positionsargumente
        durchreichen kann (statt der tkinter-Eigenheit, ein dict als
        .config()-cnf-Argument zu uebergeben - hier bewusst vermieden, um
        jeden Zweifel an der Aufrufsemantik auszuschliessen)."""
        self.status_label.config(text=text, foreground=color)

    def _on_batch_progress(self, done: int, total: int, symbol: str) -> None:
        self.after(0, self._set_status, f"Berechne {done + 1}/{total}: {symbol} …", theme.info_color())

    def _run_batch(self) -> None:
        import config as config_module
        import scheduler.background as background
        from agent.krypto.signal_batch import run_signal_batch

        if not background.signal_batch_lock.acquire(blocking=False):
            self.after(0, self._set_status, "Batch-Berechnung läuft bereits.", theme.warn_color())
            self.after(0, self.batch_button.config, state="normal")
            return

        try:
            daily_budget = config_module.load_config().get("signale_batch", {}).get("taegliches_budget", 15)
            result = run_signal_batch(
                self._db_conn_factory, self._full_watchlist, self._groq_client, self._coingecko_client,
                self._kraken_client, self._fred_api_key, daily_budget=daily_budget,
                progress_callback=self._on_batch_progress,
                gemini_client=self._gemini_client, mistral_client=self._mistral_client,
            )
            error = None
        except Exception as exc:  # noqa: BLE001 - an die UI durchreichen statt den Thread stumm sterben zu lassen
            result = None
            error = exc
        finally:
            background.signal_batch_lock.release()

        self.after(0, self._on_batch_done, result, error)

    def _on_batch_done(self, result, error) -> None:
        self.batch_button.config(state="normal" if self._any_llm_client_available() else "disabled")
        if error is not None:
            self.status_label.config(text=f"Fehler: {error}", foreground=theme.danger_color())
            return

        anzahl = len(result.berechnet)
        text = f"{anzahl} Signal(e) berechnet."
        if result.fehlgeschlagen:
            text += f" {len(result.fehlgeschlagen)} fehlgeschlagen ({', '.join(result.fehlgeschlagen)})."
        if result.budget_erschoepft:
            text += " Tagesbudget für heute aufgebraucht."
        elif result.verbleibend_ueberfaellig == 0:
            text += " Keine Assets mehr überfällig."
        self.status_label.config(
            text=text,
            foreground=theme.danger_color() if result.fehlgeschlagen else theme.info_color(),
        )
        self._refresh_list()


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
    "ueberholt_durch_neuere_analyse": "Überholt (neuere Analyse vorhanden)",
    "nicht_anwendbar": "Nicht anwendbar",
}


def _outcome_color(status: str | None):
    if status == "take_profit_erreicht":
        return theme.umgesetzt_color()
    if status == "stop_loss_erreicht":
        return theme.danger_color()
    if status in ("abgelaufen_unentschieden", "ueberholt_durch_neuere_analyse"):
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
        self._asset = asset
        self.title(f"Signal-Historie — {asset.symbol}")
        self.resizable(True, True)
        self.transient(parent)
        self.grab_set()
        self.geometry("760x420")

        frame = ttk.Frame(self, padding=12)
        frame.pack(fill="both", expand=True)

        if not history:
            ttk.Label(frame, text="Noch keine Signale für dieses Asset vorhanden.").pack(anchor="w")
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
        add_heading_tooltips(tree, _SIGNAL_HISTORY_COLUMN_DESCRIPTIONS)
        tree.pack(fill="both", expand=True)

        self._history_by_item: dict[str, object] = {}
        for signal in history:
            when = signal.created_at[:16].replace("T", " ") if signal.created_at else "-"
            konfidenz = f"{signal.confidence_pct:.0f} %" if signal.confidence_pct is not None else "-"
            status = signal.outcome_status
            outcome_text = _OUTCOME_LABELS.get(status, "—") if status else "—"
            if status == "take_profit_erreicht" and signal.outcome_realisiertes_crv is not None:
                outcome_text += f" (CRV {signal.outcome_realisiertes_crv:.2f})"
            item_id = tree.insert(
                "", "end",
                values=(when, signal.action, konfidenz, signal.groq_model or "-", outcome_text),
                tags=(status or "none",),
            )
            self._history_by_item[item_id] = signal
            tree.tag_configure(status or "none", foreground=_outcome_color(status))
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
        LlmAbfrageDialog(self, self._asset.symbol, signal)


class LlmAbfrageDialog(tk.Toplevel):
    """Zeigt die an die KI gesendeten Fakten (facts_json) sowie deren Roh-Antwort fuer
    ein historisches Signal (2026-07-18, Nutzer-Wunsch "kann man in der historie die
    zugehoerige llm abfrage auch anzeigen lassen"). Reine Anzeige aus bereits
    gespeicherten Daten (facts_json/groq_raw_response), kein neuer Netzwerk-Call."""

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
            frame, text=f"Anbieter: {signal.groq_model or '-'}   ·   Berechnet: {zeitpunkt}",
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
