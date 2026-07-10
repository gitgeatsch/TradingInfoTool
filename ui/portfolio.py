"""Portfolio-Tab: Bestaende, aktueller Preis, aktueller Wert (U-6, Phase-1-Umfang)."""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk

import database.db as db
import ui.theme as theme
from ui.formatting import format_money, is_price_stale
from ui.sortable_tree import make_sortable


class PortfolioView(ttk.Frame):
    def __init__(self, parent, db_conn_factory, watchlist):
        super().__init__(parent)
        self._db_conn_factory = db_conn_factory
        self._watchlist_by_symbol = {asset.symbol: asset for asset in watchlist}

        columns = ("symbol", "name", "assetklasse", "quantity", "price_usd", "price_eur", "value_usd", "value_eur")
        self.tree = ttk.Treeview(self, columns=columns, show="headings")
        headings = {
            "symbol": "Symbol",
            "name": "Name",
            "assetklasse": "Assetklasse",
            "quantity": "Bestand",
            "price_usd": "Preis (USD)",
            "price_eur": "Preis (EUR)",
            "value_usd": "Wert (USD)",
            "value_eur": "Wert (EUR)",
        }
        for col in columns:
            self.tree.heading(col, text=headings[col])
            self.tree.column(col, width=120, anchor="w" if col in ("name", "assetklasse") else "e")
        self.tree.tag_configure("stale", foreground=theme.stale_color())
        make_sortable(
            self.tree,
            numeric_columns=frozenset({"quantity", "price_usd", "price_eur", "value_usd", "value_eur"}),
        )
        self.tree.pack(fill="both", expand=True, padx=8, pady=8)

        self.total_label = ttk.Label(self, text="Gesamtwert: -", font=("", 10, "bold"))
        self.total_label.pack(anchor="e", padx=8, pady=(0, 8))

        # RM-4-Erweiterung (2026-07-10): echtes Fiat-Guthaben auf der Boerse (z.B.
        # Bitpanda) ist der App sonst nirgends bekannt - kein Boersen-API-Zugriff (P-7),
        # daher manuell gepflegt, analog zu den Bestaenden selbst.
        cash_frame = ttk.Frame(self)
        cash_frame.pack(anchor="e", padx=8, pady=(0, 8))
        ttk.Label(cash_frame, text="Fiat-Guthaben auf Börse (EUR, manuell):").pack(side="left", padx=(0, 6))
        self.cash_reserve_var = tk.StringVar()
        cash_entry = ttk.Entry(cash_frame, textvariable=self.cash_reserve_var, width=10, justify="right")
        cash_entry.pack(side="left")
        ttk.Button(cash_frame, text="Speichern", command=self._save_cash_reserve).pack(side="left", padx=(6, 0))
        self.cash_reserve_status = ttk.Label(cash_frame, text="")
        self.cash_reserve_status.pack(side="left", padx=(6, 0))

        # Nur einmal beim Start laden, nicht bei jedem refresh() (der auch durch
        # Preis-Updates o.ae. ausgeloest wird) - sonst wuerde eine noch nicht
        # gespeicherte Eingabe des Nutzers ueberschrieben werden.
        self.reload_cash_reserve_from_db()

        self.refresh()

    def reload_cash_reserve_from_db(self) -> None:
        """Laedt das Fiat-Cash-Feld frisch aus der DB - bewusst NICHT Teil von
        refresh() (siehe Kommentar dort), da refresh() auch durch periodische
        Preis-Updates ausgeloest wird und eine noch nicht gespeicherte Nutzereingabe
        sonst ueberschreiben wuerde. Wird beim Start UND explizit nach einem
        erfolgreichen Bitpanda-Sync (ui/app.py::_sync_bitpanda()) aufgerufen, wenn der
        Sync die Cash-Reserve tatsaechlich veraendert hat."""
        conn = self._db_conn_factory()
        try:
            current_cash = db.get_cash_reserve_fiat_eur(conn)
        finally:
            conn.close()
        self.cash_reserve_var.set(f"{current_cash:g}" if current_cash else "")

    def _save_cash_reserve(self) -> None:
        raw = self.cash_reserve_var.get().strip().replace(",", ".")
        try:
            value_eur = float(raw) if raw else 0.0
            if value_eur < 0:
                raise ValueError
        except ValueError:
            self.cash_reserve_status.config(text="⚠ ungültiger Betrag", foreground=theme.stale_color())
            return
        conn = self._db_conn_factory()
        try:
            db.set_cash_reserve_fiat_eur(conn, value_eur)
        finally:
            conn.close()
        self.cash_reserve_status.config(text="gespeichert", foreground=theme.info_color())

    def refresh(self) -> None:
        conn = self._db_conn_factory()
        try:
            holdings = db.get_all_holdings(conn)
            latest_prices = db.get_latest_prices(conn)
        finally:
            conn.close()

        for item in self.tree.get_children():
            self.tree.delete(item)

        total_value_usd = 0.0
        total_value_eur = 0.0
        for holding in sorted(holdings, key=lambda h: h.symbol):
            asset = self._watchlist_by_symbol.get(holding.symbol)
            name = asset.name if asset else holding.symbol
            assetklasse = asset.assetklasse if asset else "-"
            price_snapshot = latest_prices.get(holding.symbol)
            price_usd = price_snapshot.price_usd if price_snapshot else None
            price_eur = price_snapshot.price_eur if price_snapshot else None
            value_usd = (holding.quantity * price_usd) if price_usd is not None else None
            value_eur = (holding.quantity * price_eur) if price_eur is not None else None
            if value_usd is not None:
                total_value_usd += value_usd
            if value_eur is not None:
                total_value_eur += value_eur

            fetched_at = price_snapshot.fetched_at if price_snapshot else None
            stale = is_price_stale(fetched_at)
            price_usd_text = format_money(price_usd)
            if stale and price_usd_text != "-":
                price_usd_text = f"⚠ {price_usd_text}"

            self.tree.insert(
                "",
                "end",
                values=(
                    holding.symbol,
                    name,
                    assetklasse,
                    f"{holding.quantity:g}",
                    price_usd_text,
                    format_money(price_eur),
                    format_money(value_usd),
                    format_money(value_eur),
                ),
                tags=("stale",) if stale else (),
            )

        self.total_label.config(
            text=f"Gesamtwert: {total_value_usd:,.2f} USD / {total_value_eur:,.2f} EUR"
        )
