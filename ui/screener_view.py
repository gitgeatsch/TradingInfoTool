"""Aktien/ETF-Screener-Tab (2026-07-19, Nutzer-Wunsch "einen einfachen Aktien/ETF-
Screener... analog Marktscan"). Bewusst EINFACHER als `ui/marktscan_view.py`: kein
Score/keine Einstufung, keine automatische LLM-Begründung, keine DB-Persistenz -
ein manueller Klick liefert eine frische Kandidatenliste (siehe
`agent/aktien/screener.py` fuer die Quellen), die der Nutzer direkt per
"In Watchlist übernehmen" (identisches Muster wie Marktscan, `config.py::
add_watchlist_entry()`) uebernehmen kann. Die eigentliche Bewertung passiert
danach ganz regulär über `agent/multi_asset_batch.py` - kein Doppelbau.

Threading-Muster identisch zu `ui/marktscan_view.py`: der Scan braucht mehrere
Netzwerk-Aufrufe (yfinance-Screens + Bitpanda-Assetliste) - synchron im
Tk-Main-Thread würde die UI einfrieren."""
from __future__ import annotations

import threading
import tkinter as tk
from tkinter import messagebox, ttk

import config as config_module
import ui.theme as theme
from ui.formatting import format_money
from ui.heading_tooltip import add_heading_tooltips
from ui.sortable_tree import make_sortable

_SCREENER_COLUMN_DESCRIPTIONS = {
    "symbol": "Symbol/Ticker des Kandidaten.",
    "name": "Name des Unternehmens/Produkts.",
    "assetklasse": "Aktien (yfinance-Screener) oder ETF/ETC (direkt aus Bitpandas eigenem Katalog).",
    "quelle": "Herkunft: Yahoo-Finance-Screen-Name oder 'bitpanda_katalog'.",
    "preis": "Aktueller Preis in USD (nur Aktien - Bitpanda-Katalog liefert keine Preise).",
    "marktkap": "Marktkapitalisierung in USD (nur Aktien).",
    "aenderung": "Tagesänderung in % (nur Aktien).",
    "bitpanda": "Ob der Kandidat bei Bitpanda tatsächlich kaufbar ist (✓/✗) - bei ETF/ETC immer ✓, da direkt aus Bitpandas Katalog stammend.",
    "kategorie": "Hauptgruppe/Unterkategorie aus Basisinfos/kategorien.yaml (nur ETF/ETC, automatisch anhand des Bitpanda-Symbols zugeordnet; '-' wenn nicht zuordenbar oder bei Aktien-Kandidaten).",
}


class ScreenerView(ttk.Frame):
    def __init__(self, parent, db_conn_factory, watchlist) -> None:
        super().__init__(parent)
        self._db_conn_factory = db_conn_factory
        self._watchlist = watchlist
        self._candidates: list = []
        self._selected_candidate = None

        self._build_layout()

    def _build_layout(self) -> None:
        toolbar = ttk.Frame(self)
        toolbar.pack(fill="x", padx=8, pady=(8, 4))
        self.scan_button = ttk.Button(toolbar, text="Jetzt scannen", command=self._on_scan_clicked)
        self.scan_button.pack(side="left")
        self.watchlist_button = ttk.Button(
            toolbar, text="In Watchlist übernehmen", command=self._on_adopt_clicked, state="disabled",
        )
        self.watchlist_button.pack(side="left", padx=(8, 0))

        self.status_label = ttk.Label(self, text=(
            "Noch nicht gescannt. \"Jetzt scannen\" durchsucht 3 Yahoo-Finance-Screens (Aktien) "
            "und Bitpandas eigenen ETF/ETC-Katalog nach neuen Kandidaten, die noch nicht in der Watchlist stehen."
        ), foreground=theme.info_color(), wraplength=900, justify="left")
        self.status_label.pack(anchor="w", padx=8, pady=(0, 8))

        columns = ("symbol", "name", "assetklasse", "quelle", "preis", "marktkap", "aenderung", "bitpanda", "kategorie")
        self.tree = ttk.Treeview(self, columns=columns, show="headings", height=24)
        headings = {
            "symbol": "Symbol", "name": "Name", "assetklasse": "Klasse", "quelle": "Quelle",
            "preis": "Preis", "marktkap": "Marktkap.", "aenderung": "Änd. %", "bitpanda": "Bitpanda",
            "kategorie": "Kategorie",
        }
        widths = {
            "symbol": 70, "name": 240, "assetklasse": 70, "quelle": 170,
            "preis": 80, "marktkap": 100, "aenderung": 70, "bitpanda": 70, "kategorie": 200,
        }
        for col in columns:
            self.tree.heading(col, text=headings[col])
            self.tree.column(col, width=widths[col], anchor="w" if col in ("symbol", "name", "quelle") else "center")
        self._reapply_sort = make_sortable(self.tree, numeric_columns=frozenset({"preis", "marktkap", "aenderung"}))
        add_heading_tooltips(self.tree, _SCREENER_COLUMN_DESCRIPTIONS)
        self.tree.pack(fill="both", expand=True, padx=8, pady=(0, 8))
        self.tree.bind("<<TreeviewSelect>>", self._on_select)

    def _on_scan_clicked(self) -> None:
        self.scan_button.config(state="disabled")
        self.watchlist_button.config(state="disabled")
        self.status_label.config(
            text="Scanne Yahoo-Finance-Screens + Bitpanda-Katalog …", foreground=theme.info_color(),
        )
        thread = threading.Thread(target=self._run_scan, daemon=True)
        thread.start()

    def _run_scan(self) -> None:
        from api.bitpanda import get_listed_non_crypto_assets
        from agent.aktien.screener import scan_aktien_candidates, scan_etf_candidates

        try:
            bitpanda_assets = get_listed_non_crypto_assets()
            aktien_candidates = scan_aktien_candidates(self._watchlist, bitpanda_assets)
            etf_candidates = scan_etf_candidates(self._watchlist, bitpanda_assets)
            candidates = aktien_candidates + etf_candidates
            error = None
        except Exception as exc:  # noqa: BLE001 - an die UI durchreichen statt den Thread stumm sterben zu lassen
            candidates = []
            error = exc

        self.after(0, self._on_scan_done, candidates, error)

    def _on_scan_done(self, candidates, error) -> None:
        self.scan_button.config(state="normal")
        if error is not None:
            self.status_label.config(text=f"Scan fehlgeschlagen: {error}", foreground=theme.danger_color())
            return

        self._candidates = candidates
        for item in self.tree.get_children():
            self.tree.delete(item)
        for idx, c in enumerate(candidates):
            preis_text = f"{format_money(c.preis_usd)} $" if c.preis_usd is not None else "-"
            marktkap_text = f"{c.marktkap_usd / 1e9:.1f} Mrd." if c.marktkap_usd is not None else "-"
            aenderung_text = f"{c.aenderung_pct:+.1f}%" if c.aenderung_pct is not None else "-"
            bitpanda_text = "✓" if c.bitpanda_gelistet else ("✗" if c.bitpanda_gelistet is False else "?")
            kategorie_text = config_module.get_kategorie_name(c.hauptgruppe, c.unterkategorie) or "-"
            self.tree.insert(
                "", "end", iid=str(idx),
                values=(c.symbol, c.name, c.assetklasse, c.quelle, preis_text, marktkap_text, aenderung_text, bitpanda_text, kategorie_text),
                tags=("nicht_gelistet",) if c.bitpanda_gelistet is False else (),
            )
        self.tree.tag_configure("nicht_gelistet", foreground=theme.danger_color())
        self._reapply_sort()
        theme.restripe_treeview(self.tree)

        aktien_anzahl = sum(1 for c in candidates if c.assetklasse == "aktien")
        etf_anzahl = sum(1 for c in candidates if c.assetklasse == "etf")
        self.status_label.config(
            text=f"{aktien_anzahl} neue Aktien-Kandidaten (Yahoo-Finance-Screener), "
                 f"{etf_anzahl} neue ETF/ETC-Kandidaten (Bitpanda-Katalog).",
            foreground=theme.info_color(),
        )

    def _on_select(self, event) -> None:
        selected = self.tree.selection()
        if not selected:
            self.watchlist_button.config(state="disabled")
            self._selected_candidate = None
            return
        self._selected_candidate = self._candidates[int(selected[0])]
        self.watchlist_button.config(state="normal")

    def _on_adopt_clicked(self) -> None:
        candidate = self._selected_candidate
        if candidate is None:
            return

        warn_text = ""
        if candidate.bitpanda_gelistet is False:
            warn_text = "\n\n⚠ NICHT bei Bitpanda gelistet — dort aktuell nicht direkt kaufbar."
        hinweis_text = f"\n\n{candidate.hinweis}" if candidate.hinweis else ""
        confirmed = messagebox.askyesno(
            "In Watchlist übernehmen",
            f"{candidate.symbol} ({candidate.name}) in Basisinfos/config.yaml aufnehmen?\n\n"
            "Ein Backup der Datei wird vorher automatisch angelegt "
            f"(.claude/backups/).{warn_text}{hinweis_text}\n\n"
            "Hinweis: für volle Wirkung (Signale/Portfolio) ist ein Neustart der App nötig -"
            " die Watchlist-Liste laufender Tabs wird nicht automatisch neu geladen.",
        )
        if not confirmed:
            return

        yfinance_symbol = candidate.symbol if candidate.assetklasse == "aktien" else None
        try:
            config_module.add_watchlist_entry(
                symbol=candidate.symbol, name=candidate.name, rolle="taktisch",
                beobachtungsstatus="beobachtung", assetklasse=candidate.assetklasse,
                yfinance_symbol=yfinance_symbol,
                hauptgruppe=candidate.hauptgruppe, unterkategorie=candidate.unterkategorie,
            )
        except config_module.WatchlistWriteError as exc:
            messagebox.showerror(
                "In Watchlist übernehmen",
                f"Automatisches Schreiben fehlgeschlagen: {exc}\n\n"
                "Bitte den Eintrag manuell in Basisinfos/config.yaml ergänzen.",
            )
            return

        messagebox.showinfo(
            "In Watchlist übernehmen",
            f"{candidate.symbol} wurde in Basisinfos/config.yaml aufgenommen.\n\n"
            "Bitte die App neu starten, damit der Eintrag überall (Signale, Portfolio) wirkt.",
        )
