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

        self.refresh()

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
