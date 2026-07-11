"""Portfolio-Tab: Bestaende, aktueller Preis, aktueller Wert (U-6, Phase-1-Umfang),
seit 2026-07-11 zusaetzlich Einstandspreis + Gewinn/Verlust (siehe
importer/bitpanda_avg_cost.py - echter Marktpreis aus Bitpanda-Trades, EUR)."""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk

import database.db as db
import ui.theme as theme
from database.models import Holding
from importer.bitpanda_avg_cost import compute_cost_basis_view
from ui.formatting import format_money, format_price_age, is_price_stale
from ui.sortable_tree import make_sortable


class PortfolioView(ttk.Frame):
    def __init__(self, parent, db_conn_factory, watchlist):
        super().__init__(parent)
        self._db_conn_factory = db_conn_factory
        self._watchlist_by_symbol = {asset.symbol: asset for asset in watchlist}

        columns = (
            "symbol", "name", "assetklasse", "quantity", "price_usd", "price_eur",
            "value_usd", "value_eur", "avg_buy_price_eur", "pl_pct",
        )
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
            "avg_buy_price_eur": "Einstandspreis (EUR)",
            "pl_pct": "G/V %",
        }
        for col in columns:
            self.tree.heading(col, text=headings[col])
            self.tree.column(col, width=120, anchor="w" if col in ("name", "assetklasse") else "e")
        self.tree.tag_configure("stale", foreground=theme.stale_color())
        self.tree.tag_configure("pl_positive", foreground=theme.success_color())
        self.tree.tag_configure("pl_negative", foreground=theme.danger_color())
        make_sortable(
            self.tree,
            numeric_columns=frozenset(
                {"quantity", "price_usd", "price_eur", "value_usd", "value_eur", "avg_buy_price_eur", "pl_pct"}
            ),
        )
        # Einstandspreis manuell setzen/korrigieren (2026-07-11) - Doppelklick auf eine
        # Zeile, exakt dasselbe Muster wie ui/app.py::_open_chart() (dort fuer die
        # Watchlist), nur hier fuer den Portfolio-Tab.
        self.tree.bind("<Double-1>", self._on_edit_avg_price)
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
        # 2026-07-11, Nutzer-Fund: macht sichtbar, ob der Wert seit dem letzten
        # Bitpanda-Sync ueberholt sein koennte (siehe _update_cash_reserve_synced_label()).
        self.cash_reserve_synced_label = ttk.Label(cash_frame, text="", foreground=theme.info_color())
        self.cash_reserve_synced_label.pack(side="left", padx=(10, 0))

        # Nur einmal beim Start laden, nicht bei jedem refresh() (der auch durch
        # Preis-Updates o.ae. ausgeloest wird) - sonst wuerde eine noch nicht
        # gespeicherte Eingabe des Nutzers ueberschrieben werden.
        self.reload_cash_reserve_from_db()

        self.refresh()

    def reload_cash_reserve_from_db(self) -> None:
        """Laedt das Fiat-Cash-Feld frisch aus der DB - bewusst NICHT Teil von
        refresh() (siehe Kommentar dort), da refresh() auch durch periodische
        Preis-Updates ausgeloest wird und eine noch nicht gespeicherte Nutzereingabe
        sonst ueberschreiben wuerde. Wird beim Start UND nach jedem Bitpanda-Sync
        (ui/app.py::_sync_bitpanda()) aufgerufen."""
        conn = self._db_conn_factory()
        try:
            current_cash = db.get_cash_reserve_fiat_eur(conn)
            synced_at = db.get_cash_reserve_synced_at(conn)
        finally:
            conn.close()
        self.cash_reserve_var.set(f"{current_cash:g}" if current_cash else "")
        self._update_cash_reserve_synced_label(synced_at)

    def _update_cash_reserve_synced_label(self, synced_at: str | None) -> None:
        """2026-07-11, Nutzer-Fund: Bitpanda sperrt fuer offene Fusion-Limit-Orders
        reservierte Betraege sofort aus dem Wallet-Guthaben, ohne dass die App das
        mitbekommt, solange kein neuer Sync laeuft - dieser Zeitstempel macht
        sichtbar, ob die angezeigte Cash-Reserve noch aktuell sein kann. Bewusst
        KEINE Stale-Faerbung wie bei Preisen (staleness.py-Schwelle 30 Min ist fuer
        den 15-Min-Scheduler-Takt gedacht) - ein manueller Sync bleibt normalerweise
        stundenlang "veraltet" im technischen Sinn, ohne dass etwas falsch ist."""
        if synced_at is None:
            self.cash_reserve_synced_label.config(text="nie per Bitpanda-Sync geprüft", foreground=theme.info_color())
            return
        self.cash_reserve_synced_label.config(
            text=f"Bitpanda-Sync: {format_price_age(synced_at)}", foreground=theme.info_color()
        )

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
            fiat_cash_eur = db.get_cash_reserve_fiat_eur(conn)
        finally:
            conn.close()

        for item in self.tree.get_children():
            self.tree.delete(item)

        total_value_usd = 0.0
        total_value_eur = 0.0
        staked_value_eur = 0.0
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

            # 2026-07-11, Nutzer-Fund: gestakte Menge ist ueber die normale Wallet-API
            # unsichtbar (siehe importer/bitpanda_avg_cost.py::compute_staked_quantities()) -
            # additiv zu holding.quantity, nicht darin enthalten. Fliesst separat in die
            # Gesamtwert-Zeile ein (siehe unten), damit sie nicht mit dem regulaeren
            # Bestand verwechselt wird.
            quantity_text = f"{holding.quantity:g}"
            if holding.staked_quantity and holding.staked_quantity > 0:
                quantity_text += f" (+{holding.staked_quantity:g} gestakt)"
                if price_eur is not None:
                    staked_value_eur += holding.staked_quantity * price_eur

            fetched_at = price_snapshot.fetched_at if price_snapshot else None
            stale = is_price_stale(fetched_at)
            price_usd_text = format_money(price_usd)
            if stale and price_usd_text != "-":
                price_usd_text = f"⚠ {price_usd_text}"

            cost_basis = compute_cost_basis_view(holding, price_eur)
            if cost_basis.source == "unbekannt":
                avg_price_text = "unbekannt"
            else:
                avg_price_text = format_money(cost_basis.effective_avg_price_eur)
                if cost_basis.source == "manuell":
                    avg_price_text = f"{avg_price_text} (manuell)"
                elif cost_basis.unknown_quantity > 0:
                    avg_price_text = f"{avg_price_text} (⚠ {cost_basis.unknown_quantity:g} unbepreist)"
            pl_text = f"{cost_basis.pl_pct:+.1f}%" if cost_basis.pl_pct is not None else "-"

            tags = []
            if stale:
                tags.append("stale")
            if cost_basis.pl_pct is not None:
                tags.append("pl_positive" if cost_basis.pl_pct >= 0 else "pl_negative")

            self.tree.insert(
                "",
                "end",
                values=(
                    holding.symbol,
                    name,
                    assetklasse,
                    quantity_text,
                    price_usd_text,
                    format_money(price_eur),
                    format_money(value_usd),
                    format_money(value_eur),
                    avg_price_text,
                    pl_text,
                ),
                tags=tuple(tags),
            )

        # RM-4/Konsistenz-Fix (2026-07-11, Nutzer-Fund): agent/krypto/risk_gate.py::
        # pre_check() zaehlt die Fiat-Cash-Reserve seit 2026-07-10 korrekt zum
        # Portfoliowert dazu (RM-4/RM-1/RM-2 nutzen durchgaengig dieselbe Basis) -
        # diese Anzeige tat das bisher NICHT, zeigte also einen kleineren Wert als
        # den, auf dem die KI ihre Entscheidungen tatsaechlich stuetzt. EUR-Seite ist
        # direkt (fiat_cash_eur ist bereits EUR), USD-Seite nutzt denselben EURCV-
        # Wechselkurs-Trick wie risk_gate.py (1 EURCV ~= 1 EUR, siehe A-5) - fehlt das
        # Snapshot, wird die USD-Seite NICHT hochgerechnet statt falsch geraten (P-10).
        total_value_eur += fiat_cash_eur
        if fiat_cash_eur > 0:
            eurcv_snap = latest_prices.get("EURCV")
            if eurcv_snap and eurcv_snap.price_usd and eurcv_snap.price_eur:
                total_value_usd += fiat_cash_eur * (eurcv_snap.price_usd / eurcv_snap.price_eur)

        # 2026-07-11, Nutzer-Fund: gestakter Wert zaehlt hier zum Gesamtwert dazu (echtes
        # Vermoegen, nur voruebergehend nicht handelbar) - WICHTIG: agent/krypto/
        # risk_gate.py (RM-1/RM-2/RM-4) rechnet aktuell noch OHNE diesen Anteil, diese
        # Anzeige ist also bewusst vollstaendiger als das, was die KI aktuell sieht.
        # Das Zusammenfuehren beider Werte ist ein separates, noch offenes Folge-Thema
        # (siehe Basisinfos/Regelwerksmanual.md Kap. 13/14) - nicht heute in die
        # "unantastbare" Risk-Gate-Formel eingegriffen.
        total_value_eur += staked_value_eur
        eurcv_snap = latest_prices.get("EURCV")
        if staked_value_eur > 0 and eurcv_snap and eurcv_snap.price_usd and eurcv_snap.price_eur:
            total_value_usd += staked_value_eur * (eurcv_snap.price_usd / eurcv_snap.price_eur)

        notes = []
        if fiat_cash_eur > 0:
            notes.append(f"{fiat_cash_eur:,.2f} EUR Fiat-Cash")
        if staked_value_eur > 0:
            notes.append(f"{staked_value_eur:,.2f} EUR gestakt (im Regelwerk noch nicht berücksichtigt)")
        note_text = f" (davon {', '.join(notes)})" if notes else ""
        self.total_label.config(
            text=f"Gesamtwert: {total_value_usd:,.2f} USD / {total_value_eur:,.2f} EUR{note_text}"
        )

    def _on_edit_avg_price(self, event) -> None:
        selected = self.tree.selection()
        if not selected:
            return
        symbol = self.tree.item(selected[0], "values")[0]
        conn = self._db_conn_factory()
        try:
            holding = next((h for h in db.get_all_holdings(conn) if h.symbol == symbol), None)
        finally:
            conn.close()
        if holding is None:
            return
        AvgBuyPriceDialog(self, holding, self._db_conn_factory, on_saved=self.refresh)


class AvgBuyPriceDialog(tk.Toplevel):
    """Manueller Einstandspreis-Override (2026-07-11) - kompletter Vorrang vor dem
    automatisch aus Bitpanda-Trades berechneten Wert (Holding.effective_avg_buy_price_eur).
    Gedacht fuer Bestaende ohne (vollstaendige) Bitpanda-Handelshistorie (Alt-Bestaende,
    Excel-Import) - Struktur wie ui/signals_view.py::UmsetzungDialog."""

    def __init__(self, parent, holding: Holding, db_conn_factory, on_saved) -> None:
        super().__init__(parent)
        self._holding = holding
        self._db_conn_factory = db_conn_factory
        self._on_saved = on_saved

        self.title(f"Einstandspreis — {holding.symbol}")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        frame = ttk.Frame(self, padding=12)
        frame.pack(fill="both", expand=True)

        ttk.Label(frame, text=holding.symbol, font=("", 11, "bold")).grid(
            row=0, column=0, columnspan=2, sticky="w", pady=(0, 8)
        )

        auto_text = (
            format_money(holding.avg_buy_price_eur)
            if holding.avg_buy_price_eur is not None
            else "unbekannt (noch nicht berechnet)"
        )
        tracked = holding.avg_buy_price_tracked_qty or 0.0
        if holding.avg_buy_price_eur is not None and tracked < holding.quantity:
            auto_text += f" (nur {tracked:g} von {holding.quantity:g} bepreist)"
        ttk.Label(frame, text="Automatisch berechnet (aus Bitpanda-Trades):").grid(
            row=1, column=0, columnspan=2, sticky="w"
        )
        ttk.Label(frame, text=auto_text, foreground=theme.info_color()).grid(
            row=2, column=0, columnspan=2, sticky="w", pady=(0, 8)
        )

        ttk.Label(frame, text="Manueller Override (EUR, leer = automatischen Wert nutzen):").grid(
            row=3, column=0, columnspan=2, sticky="w"
        )
        self._manual_var = tk.StringVar(
            value=f"{holding.avg_buy_price_manual_eur:g}" if holding.avg_buy_price_manual_eur is not None else ""
        )
        ttk.Entry(frame, textvariable=self._manual_var, width=18).grid(
            row=4, column=0, columnspan=2, sticky="w", pady=(2, 0)
        )

        self._error_label = ttk.Label(frame, text="", foreground=theme.danger_color(), wraplength=280, justify="left")
        self._error_label.grid(row=5, column=0, columnspan=2, sticky="w", pady=(8, 0))

        button_frame = ttk.Frame(frame)
        button_frame.grid(row=6, column=0, columnspan=2, sticky="e", pady=(12, 0))
        ttk.Button(button_frame, text="Abbrechen", command=self.destroy).pack(side="left", padx=(0, 6))
        ttk.Button(button_frame, text="Speichern", command=self._save).pack(side="left")

    def _save(self) -> None:
        raw = self._manual_var.get().strip().replace(",", ".")
        if not raw:
            value: float | None = None
        else:
            try:
                value = float(raw)
                if value < 0:
                    raise ValueError
            except ValueError:
                self._error_label.config(text="⚠ ungültiger Betrag")
                return

        conn = self._db_conn_factory()
        try:
            db.set_holding_avg_buy_price_manual(conn, self._holding.symbol, value)
        finally:
            conn.close()

        self._on_saved()
        self.destroy()
