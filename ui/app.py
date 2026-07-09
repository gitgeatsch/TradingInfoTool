"""Hauptfenster: Watchlist- und Portfolio-Tab, Basis-UI fuer Phase 1."""
from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk

import database.db as db
from importer.excel_import import import_holdings
from ui.formatting import format_money, format_price_age, is_price_stale
from ui.marktscan_view import MarktscanView
from ui.portfolio import PortfolioView
from ui.signals_view import SignalsView

STALE_COLOR = "#b36b00"

UI_POLL_INTERVAL_MS = 3000
DISCLAIMER_TEXT = (
    "Keine Anlageberatung. Alle Angaben algorithmisch/KI-generiert und koennen "
    "fehlerhaft sein. Entscheidung und Verantwortung liegen beim Nutzer."
)


class TradingInfoToolApp(tk.Tk):
    def __init__(
        self, db_conn_factory, watchlist, coingecko_client, kraken_client=None, groq_client=None,
        fred_api_key=None,
    ):
        super().__init__()
        self.title("TradingInfoTool")
        self.geometry("900x600")

        self._db_conn_factory = db_conn_factory
        self._watchlist = watchlist
        self._coingecko_client = coingecko_client
        self._kraken_client = kraken_client
        self._groq_client = groq_client
        self._fred_api_key = fred_api_key

        self._build_menu()

        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True)

        self._watchlist_frame = self._build_watchlist_tab(notebook)
        notebook.add(self._watchlist_frame, text="Watchlist")

        self._portfolio_view = PortfolioView(notebook, db_conn_factory, watchlist)
        notebook.add(self._portfolio_view, text="Portfolio")

        self._signals_view = SignalsView(
            notebook, db_conn_factory, watchlist, groq_client, coingecko_client, kraken_client,
            fred_api_key=fred_api_key,
        )
        notebook.add(self._signals_view, text="Signale")

        self._marktscan_view = MarktscanView(
            notebook, db_conn_factory, watchlist, groq_client, coingecko_client, kraken_client,
            fred_api_key=fred_api_key,
        )
        notebook.add(self._marktscan_view, text="Marktscan")

        disclaimer = ttk.Label(
            self, text=DISCLAIMER_TEXT, foreground="#666666", wraplength=880, justify="center"
        )
        disclaimer.pack(side="bottom", fill="x", padx=8, pady=4)

        self._refresh_watchlist_from_db()
        self.after(UI_POLL_INTERVAL_MS, self._poll_prices)

    def _build_menu(self) -> None:
        menubar = tk.Menu(self)
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Bestände neu importieren", command=self._reimport_holdings)
        file_menu.add_separator()
        file_menu.add_command(label="Beenden", command=self.destroy)
        menubar.add_cascade(label="Datei", menu=file_menu)
        self.config(menu=menubar)

    def _build_watchlist_tab(self, parent) -> ttk.Frame:
        frame = ttk.Frame(parent)

        toolbar = ttk.Frame(frame)
        toolbar.pack(fill="x", padx=8, pady=(8, 0))
        ttk.Button(toolbar, text="Jetzt aktualisieren", command=self._manual_refresh).pack(
            side="left"
        )

        columns = (
            "symbol",
            "name",
            "typ",
            "status",
            "price_usd",
            "price_eur",
            "change_24h",
            "aktualisiert",
        )
        headings = {
            "symbol": "Symbol",
            "name": "Name",
            "typ": "Typ",
            "status": "Status",
            "price_usd": "Preis (USD)",
            "price_eur": "Preis (EUR)",
            "change_24h": "24h %",
            "aktualisiert": "Aktualisiert",
        }
        tree = ttk.Treeview(frame, columns=columns, show="headings")
        for col in columns:
            tree.heading(col, text=headings[col])
            anchor = "w" if col in ("name", "typ", "status") else "e"
            tree.column(col, width=110, anchor=anchor)
        tree.tag_configure("stale", foreground=STALE_COLOR)
        tree.bind("<Double-1>", self._open_chart)
        tree.pack(fill="both", expand=True, padx=8, pady=8)

        frame.tree = tree
        return frame

    def _refresh_watchlist_from_db(self) -> None:
        conn = self._db_conn_factory()
        try:
            latest_prices = db.get_latest_prices(conn)
        finally:
            conn.close()

        tree = self._watchlist_frame.tree
        for item in tree.get_children():
            tree.delete(item)

        for asset in sorted(self._watchlist, key=lambda a: a.symbol):
            snap = latest_prices.get(asset.symbol)
            price_usd = format_money(snap.price_usd if snap else None)
            price_eur = format_money(snap.price_eur if snap else None)
            change = f"{snap.change_24h_pct:+.2f}" if snap and snap.change_24h_pct is not None else "-"

            fetched_at = snap.fetched_at if snap else None
            stale = is_price_stale(fetched_at)
            age_text = format_price_age(fetched_at)
            aktualisiert = f"⚠ {age_text}" if stale else age_text

            tree.insert(
                "",
                "end",
                values=(
                    asset.symbol,
                    asset.name,
                    asset.typ,
                    asset.status,
                    price_usd,
                    price_eur,
                    change,
                    aktualisiert,
                ),
                tags=("stale",) if stale else (),
            )

    def _open_chart(self, event) -> None:
        tree = self._watchlist_frame.tree
        selected = tree.selection()
        if not selected:
            return
        symbol = tree.item(selected[0], "values")[0]
        asset = next((a for a in self._watchlist if a.symbol == symbol), None)
        if asset is None:
            return

        from ui.charts import ChartWindow

        ChartWindow(self, self._db_conn_factory, asset)

    def _poll_prices(self) -> None:
        self._refresh_watchlist_from_db()
        self._portfolio_view.refresh()
        self.after(UI_POLL_INTERVAL_MS, self._poll_prices)

    def _manual_refresh(self) -> None:
        from scheduler.background import refresh_prices_job

        refresh_prices_job(self._coingecko_client, self._db_conn_factory, self._watchlist)
        self._refresh_watchlist_from_db()
        self._portfolio_view.refresh()

    def _reimport_holdings(self) -> None:
        conn = self._db_conn_factory()
        try:
            result = import_holdings(conn)
        finally:
            conn.close()

        self._portfolio_view.refresh()

        message = f"{result.imported_count} Bestände importiert."
        if result.warnings:
            message += "\n\nWarnungen:\n" + "\n".join(result.warnings)
        messagebox.showinfo("Bestände neu importieren", message)


def run_app(
    db_conn_factory, watchlist, coingecko_client, kraken_client=None, groq_client=None,
    fred_api_key=None,
) -> None:
    app = TradingInfoToolApp(
        db_conn_factory, watchlist, coingecko_client, kraken_client, groq_client,
        fred_api_key=fred_api_key,
    )
    app.mainloop()
