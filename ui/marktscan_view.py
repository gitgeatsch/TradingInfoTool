"""Marktscan-Tab (U-10): zeigt die von agent/marktscan.py entdeckten und bewerteten
Kandidaten (Spezifikation Kap. 13) und erlaubt, einen Scan manuell auszuloesen sowie
Kandidaten zu behalten/verwerfen. Bewusst KEIN automatisches Schreiben in
Basisinfos/config.yaml (siehe Plan, C:\\Users\\Geatsch\\.claude\\plans\\
deep-launching-zebra.md, Design-Entscheidung 1) - "Watchlist-Eintrag vorbereiten"
zeigt stattdessen einen fertigen, copy-paste-baren YAML-Block.

Threading-Muster identisch zu ui/signals_view.py: ein Scan-Lauf braucht mehrere
Sekunden (mehrere CoinGecko-Calls + optional Groq) - synchron im Tk-Main-Thread
wuerde die UI einfrieren."""
from __future__ import annotations

import json
import threading
import tkinter as tk
from tkinter import ttk

import database.db as db
from ui.formatting import format_money

EINSTUFUNG_COLORS = {
    "kaufkandidat": "#1a7f37",
    "watchlist_wuerdig": "#8a5a00",
    "kein_treffer": "#666666",
}
WARN_COLOR = "#b36b00"
INFO_COLOR = "#666666"
STATUS_LABELS = {
    "neu": "neu",
    "nutzer_behalten_manuell_uebernommen": "übernommen",
    "nutzer_verworfen": "verworfen",
}


def _candidate_to_yaml_block(candidate) -> str:
    """Exakt das Format von Basisinfos/config.yaml watchlist: (Kap. 13 MS-1(c)/U-10) -
    Nutzer fuegt das manuell ein, keine automatische Datei-Schreibung (siehe
    Modul-Docstring)."""
    return (
        f"  - symbol: {candidate.symbol}\n"
        f"    name: {candidate.name}\n"
        f"    typ: taktisch\n"
        f"    status: watchlist\n"
        f"    coingecko_id: {candidate.coingecko_id}\n"
    )


class _YamlDialog(tk.Toplevel):
    def __init__(self, parent, symbol: str, yaml_block: str, bitpanda_gelistet: bool | None):
        super().__init__(parent)
        self.title(f"Watchlist-Eintrag für {symbol}")
        self.geometry("520x260" if bitpanda_gelistet is False else "520x220")
        if bitpanda_gelistet is False:
            ttk.Label(
                self,
                text=f"⚠ {symbol} ist NICHT bei Bitpanda gelistet — dort aktuell nicht direkt "
                "kaufbar. Trotzdem zur Beobachtung hinzufügen möglich.",
                wraplength=500, justify="left", foreground="#c0392b",
            ).pack(anchor="w", padx=10, pady=(10, 0))
        ttk.Label(
            self, text="In Basisinfos/config.yaml unter watchlist: einfügen (Notepad++):",
            wraplength=500, justify="left",
        ).pack(anchor="w", padx=10, pady=(10, 4))
        text = tk.Text(self, height=8, wrap="none")
        text.pack(fill="both", expand=True, padx=10, pady=4)
        text.insert("1.0", yaml_block)
        text.focus_set()
        text.tag_add("sel", "1.0", "end")
        ttk.Button(self, text="Schließen", command=self.destroy).pack(pady=(0, 10))


class MarktscanView(ttk.Frame):
    def __init__(
        self, parent, db_conn_factory, watchlist, groq_client, coingecko_client, kraken_client,
        fred_api_key=None,
    ):
        super().__init__(parent)
        self._db_conn_factory = db_conn_factory
        self._watchlist = watchlist
        self._groq_client = groq_client
        self._coingecko_client = coingecko_client
        self._kraken_client = kraken_client
        self._fred_api_key = fred_api_key
        self._selected_candidate = None
        self._show_alle = tk.BooleanVar(value=False)

        self._build_layout()
        self._refresh_list()

    def _build_layout(self) -> None:
        paned = ttk.Panedwindow(self, orient="horizontal")
        paned.pack(fill="both", expand=True, padx=8, pady=8)

        left = ttk.Frame(paned)
        paned.add(left, weight=1)

        left_toolbar = ttk.Frame(left)
        left_toolbar.pack(fill="x", pady=(0, 4))
        ttk.Checkbutton(
            left_toolbar, text="Alle anzeigen (auch kein_treffer)", variable=self._show_alle,
            command=self._refresh_list,
        ).pack(side="left")

        columns = ("symbol", "tier", "score", "einstufung", "bitpanda", "entdeckt", "status")
        self.tree = ttk.Treeview(left, columns=columns, show="headings", height=20)
        headings = {
            "symbol": "Symbol", "tier": "Tier", "score": "Score", "einstufung": "Einstufung",
            "bitpanda": "Bitpanda", "entdeckt": "Entdeckt", "status": "Status",
        }
        for col in columns:
            self.tree.heading(col, text=headings[col])
            self.tree.column(col, width=90, anchor="w" if col == "symbol" else "center")
        self.tree.pack(fill="both", expand=True)
        self.tree.bind("<<TreeviewSelect>>", self._on_select)

        right = ttk.Frame(paned)
        paned.add(right, weight=3)

        toolbar = ttk.Frame(right)
        toolbar.pack(fill="x", pady=(0, 8))
        self.scan_button = ttk.Button(toolbar, text="Jetzt scannen", command=self._on_scan_clicked)
        self.scan_button.pack(side="left")
        self.writeup_button = ttk.Button(
            toolbar, text="P-5-Begründung generieren", command=self._on_writeup_clicked, state="disabled"
        )
        self.writeup_button.pack(side="left", padx=(8, 0))
        self.watchlist_button = ttk.Button(
            toolbar, text="Watchlist-Eintrag vorbereiten", command=self._on_prepare_watchlist_clicked,
            state="disabled",
        )
        self.watchlist_button.pack(side="left", padx=(8, 0))
        self.reject_button = ttk.Button(
            toolbar, text="Verwerfen", command=self._on_reject_clicked, state="disabled"
        )
        self.reject_button.pack(side="left", padx=(8, 0))

        self.status_label = ttk.Label(right, text="", foreground=INFO_COLOR)
        self.status_label.pack(anchor="w")

        if self._groq_client is None:
            self.status_label.config(
                text="⚠ Kein GROQ_API_KEY gesetzt — P-5-Begründung deaktiviert (siehe .env)",
                foreground=WARN_COLOR,
            )

        self.title_label = ttk.Label(right, text="Kein Kandidat ausgewählt", font=("", 13, "bold"))
        self.title_label.pack(anchor="w", pady=(8, 0))

        self.meta_label = ttk.Label(right, text="", foreground=INFO_COLOR)
        self.meta_label.pack(anchor="w", pady=(0, 8))

        self.detail_text = tk.Text(right, height=26, wrap="word", state="disabled", relief="flat")
        self.detail_text.pack(fill="both", expand=True)

    def _refresh_list(self) -> None:
        conn = self._db_conn_factory()
        try:
            candidates = db.get_marktscan_candidates(conn)
        finally:
            conn.close()

        if not self._show_alle.get():
            candidates = [c for c in candidates if c.einstufung != "kein_treffer"]

        for item in self.tree.get_children():
            self.tree.delete(item)

        self._candidates_by_id: dict[int, object] = {}
        for c in candidates:
            self._candidates_by_id[c.id] = c
            score_text = f"{c.score_gesamt:.1f}" if c.score_gesamt is not None else "-"
            entdeckt_text = c.discovered_at[:16].replace("T", " ")
            if c.bitpanda_gelistet is True:
                bitpanda_text = "✓"
            elif c.bitpanda_gelistet is False:
                bitpanda_text = "✗"
            else:
                bitpanda_text = "?"
            self.tree.insert(
                "", "end", iid=str(c.id),
                values=(c.symbol, c.tier or "-", score_text, c.einstufung or "-", bitpanda_text,
                        entdeckt_text, STATUS_LABELS.get(c.status, c.status)),
                tags=("nicht_gelistet",) if c.bitpanda_gelistet is False else (),
            )
        self.tree.tag_configure("nicht_gelistet", foreground="#c0392b")

    def _on_select(self, event) -> None:
        selected = self.tree.selection()
        if not selected:
            return
        candidate = self._candidates_by_id.get(int(selected[0]))
        self._selected_candidate = candidate
        if candidate is None:
            return

        self.writeup_button.config(
            state="normal" if (self._groq_client is not None and candidate.einstufung == "kaufkandidat") else "disabled"
        )
        self.watchlist_button.config(
            state="normal" if candidate.einstufung in ("kaufkandidat", "watchlist_wuerdig") else "disabled"
        )
        self.reject_button.config(state="normal" if candidate.status == "neu" else "disabled")
        self._render_candidate(candidate)

    def _render_candidate(self, c) -> None:
        color = EINSTUFUNG_COLORS.get(c.einstufung, "black")
        score_text = f"{c.score_gesamt:.1f}" if c.score_gesamt is not None else "-"
        self.title_label.config(text=f"{c.symbol} — {c.name}", foreground=color)

        if c.bitpanda_gelistet is True:
            bitpanda_text = " · Bitpanda: ✓ gelistet"
            bitpanda_color = INFO_COLOR
        elif c.bitpanda_gelistet is False:
            bitpanda_text = " · Bitpanda: ✗ NICHT gelistet"
            bitpanda_color = "#c0392b"
        else:
            bitpanda_text = " · Bitpanda: unbekannt (Prüfung fehlgeschlagen)"
            bitpanda_color = INFO_COLOR
        self.meta_label.config(
            text=f"Einstufung: {c.einstufung or '-'} · Score: {score_text}{bitpanda_text}",
            foreground=bitpanda_color if c.bitpanda_gelistet is False else INFO_COLOR,
        )

        lines: list[str] = []
        lines.append(f"EINSTUFUNG: {c.einstufung}")
        lines.append(c.einstufung_begruendung or "")
        if c.bitpanda_gelistet is False:
            lines.append("\n⚠ NICHT bei Bitpanda gelistet — dort aktuell nicht direkt kaufbar.")
        if c.small_cap_budget_hinweis:
            lines.append(f"\n⚠ {c.small_cap_budget_hinweis}")
        lines.append("")

        change_text = f"{c.change_24h_pct:+.2f}%" if c.change_24h_pct is not None else "-"
        lines.append(
            f"MARKTDATEN\nPreis: {format_money(c.price_usd)} USD · Marktkap.: "
            f"{format_money(c.market_cap_usd)} USD · 24h: {change_text}"
        )
        lines.append(f"Tier: {c.tier or '-'} · Quelle: {c.discovery_source} · Regime beim Scan: {c.regime_bei_scan}")
        lines.append(f"Stufe A: {'bestanden' if c.filter_a_bestanden else 'NICHT bestanden'} — {c.filter_a_begruendung}")
        lines.append("")

        lines.append("STUFE-B-SCORES (0-100 je Kategorie)")
        lines.append(f"  Technik:       {c.score_technik if c.score_technik is not None else '-'}")
        lines.append(f"  Fundamental:   {c.score_fundamental if c.score_fundamental is not None else '-'}")
        lines.append(f"  Momentum:      {c.score_momentum if c.score_momentum is not None else '-'}")
        lines.append(f"  Kontext/Makro: {c.score_kontext_makro if c.score_kontext_makro is not None else '-'}")
        lines.append(f"  GESAMT:        {c.score_gesamt if c.score_gesamt is not None else '-'}")
        lines.append("")

        if c.groq_kurzbegruendung:
            lines.append(f"P-5-KURZBEGRÜNDUNG (generiert {c.groq_generiert_am[:16].replace('T', ' ') if c.groq_generiert_am else ''})")
            lines.append(c.groq_kurzbegruendung)
            lines.append("")
        if c.groq_langbegruendung_json:
            try:
                lang = json.loads(c.groq_langbegruendung_json)
            except (json.JSONDecodeError, TypeError):
                lang = {}
            if lang:
                lines.append("P-5-LANGBEGRÜNDUNG")
                for key, label in (("technisch", "Technisch"), ("fundamental", "Fundamental"), ("makro", "Makro")):
                    if lang.get(key):
                        lines.append(f"{label}: {lang[key]}")
                lines.append("")

        self._set_detail_text("\n".join(lines))

    def _set_detail_text(self, text: str) -> None:
        self.detail_text.config(state="normal")
        self.detail_text.delete("1.0", "end")
        self.detail_text.insert("1.0", text)
        self.detail_text.config(state="disabled")

    def _on_scan_clicked(self) -> None:
        self.scan_button.config(state="disabled")
        self.status_label.config(text="Scanne CoinGecko Trending/Top-Gainers …", foreground=INFO_COLOR)
        thread = threading.Thread(target=self._run_scan, daemon=True)
        thread.start()

    def _run_scan(self) -> None:
        import config as config_module
        from agent.marktscan import run_scan
        from agent.pipeline import compute_current_regime

        conn = self._db_conn_factory()
        try:
            config_dict = config_module.load_config()
            regime_result = compute_current_regime(
                conn, self._coingecko_client, self._watchlist, self._fred_api_key, config_dict
            )
            candidates = run_scan(
                self._coingecko_client, conn, self._watchlist, regime_result, config_dict,
                groq_client=self._groq_client, kraken_client=self._kraken_client,
            )
            error = None
        except Exception as exc:  # noqa: BLE001 - an die UI durchreichen statt den Thread stumm sterben zu lassen
            candidates = []
            error = exc
        finally:
            conn.close()

        self.after(0, self._on_scan_done, candidates, error)

    def _on_scan_done(self, candidates, error) -> None:
        self.scan_button.config(state="normal")
        if error is not None:
            self.status_label.config(text=f"Fehler: {error}", foreground="#c0392b")
            return
        treffer = [c for c in candidates if c.einstufung in ("kaufkandidat", "watchlist_wuerdig")]
        self.status_label.config(
            text=f"Fertig — {len(candidates)} Kandidaten bewertet, {len(treffer)} Treffer.",
            foreground=INFO_COLOR,
        )
        self._refresh_list()

    def _on_writeup_clicked(self) -> None:
        candidate = self._selected_candidate
        if candidate is None or self._groq_client is None:
            return
        self.writeup_button.config(state="disabled")
        self.status_label.config(text=f"Generiere P-5-Begründung für {candidate.symbol} …", foreground=INFO_COLOR)
        thread = threading.Thread(target=self._run_writeup, args=(candidate,), daemon=True)
        thread.start()

    def _run_writeup(self, candidate) -> None:
        import config as config_module
        from agent.marktscan import generate_candidate_writeup
        from agent.pipeline import compute_current_regime

        conn = self._db_conn_factory()
        try:
            config_dict = config_module.load_config()
            regime_result = compute_current_regime(
                conn, self._coingecko_client, self._watchlist, self._fred_api_key, config_dict
            )
            parsed = generate_candidate_writeup(
                candidate, regime_result, self._groq_client, self._kraken_client, conn, self._watchlist,
                config_dict,
            )
            db.update_marktscan_candidate_groq_writeup(
                conn, candidate.id, parsed.get("short_reasoning"),
                json.dumps(parsed.get("long_reasoning") or {}, ensure_ascii=False),
            )
            error = None
        except Exception as exc:  # noqa: BLE001
            error = exc
        finally:
            conn.close()

        self.after(0, self._on_writeup_done, candidate, error)

    def _on_writeup_done(self, candidate, error) -> None:
        self.writeup_button.config(state="normal" if self._groq_client is not None else "disabled")
        if error is not None:
            self.status_label.config(text=f"Fehler: {error}", foreground="#c0392b")
            return
        self.status_label.config(text="Fertig.", foreground=INFO_COLOR)
        self._refresh_list()
        if self._selected_candidate is not None and self._selected_candidate.id == candidate.id:
            conn = self._db_conn_factory()
            try:
                refreshed = next(
                    (c for c in db.get_marktscan_candidates(conn) if c.id == candidate.id), candidate
                )
            finally:
                conn.close()
            self._selected_candidate = refreshed
            self._render_candidate(refreshed)

    def _on_prepare_watchlist_clicked(self) -> None:
        candidate = self._selected_candidate
        if candidate is None:
            return
        yaml_block = _candidate_to_yaml_block(candidate)
        _YamlDialog(self, candidate.symbol, yaml_block, candidate.bitpanda_gelistet)

        conn = self._db_conn_factory()
        try:
            db.update_marktscan_candidate_status(conn, candidate.id, "nutzer_behalten_manuell_uebernommen")
        finally:
            conn.close()
        self._refresh_list()

    def _on_reject_clicked(self) -> None:
        candidate = self._selected_candidate
        if candidate is None:
            return
        conn = self._db_conn_factory()
        try:
            db.update_marktscan_candidate_status(conn, candidate.id, "nutzer_verworfen")
        finally:
            conn.close()
        self.reject_button.config(state="disabled")
        self._refresh_list()
