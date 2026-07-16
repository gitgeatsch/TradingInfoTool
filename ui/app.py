"""Hauptfenster: Watchlist- und Portfolio-Tab, Basis-UI fuer Phase 1."""
from __future__ import annotations

import logging
import os
import threading
import tkinter as tk
import traceback
from datetime import datetime, timezone
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

import database.db as db
import ui.settings as ui_settings
import ui.theme as theme
from api.bitpanda import is_listed as bitpanda_is_listed
from importer.excel_import import EXPORT_XLSX_PATH, export_holdings, import_holdings
from ui.formatting import format_money, format_price_age, is_price_stale
from ui.heading_tooltip import add_heading_tooltips
from ui.hebel_view import HebelView
from ui.marktscan_view import MarktscanView
from ui.portfolio import PortfolioView
from ui.row_tooltip import add_row_tooltips
from ui.signals_view import SignalsView
from ui.sortable_tree import make_sortable

logger = logging.getLogger(__name__)

UI_POLL_INTERVAL_MS = 3000
DISCLAIMER_TEXT = (
    "Keine Anlageberatung. Alle Angaben algorithmisch/KI-generiert und koennen "
    "fehlerhaft sein. Entscheidung und Verantwortung liegen beim Nutzer."
)

_WATCHLIST_COLUMN_DESCRIPTIONS = {
    "symbol": "Kurzzeichen des Assets (z. B. an der Börse/CoinGecko).",
    "name": "Vollständiger Name des Assets.",
    "rolle": "Core oder taktisch - strategische Einstufung aus der Watchlist-Konfiguration, unabhängig vom aktuellen Bestand.",
    "assetklasse": "Krypto, Aktie, ETF oder Rohstoff.",
    "status": (
        "Gehalten (echter Bestand oder offene Hebel-Position, live abgeleitet) oder - falls nicht gehalten - "
        "Beobachtung (aktive Kandidatur) bzw. Ausgemustert (niedrigste Priorität, aber nicht ausgeschlossen)."
    ),
    "bitpanda": (
        "✓ = auf Bitpanda handelbar, ✗ = nicht gelistet (blockiert Kauf-/Nachkauf-"
        "Signale), ? = noch nicht geprüft, - = nicht zutreffend (Nicht-Krypto-Asset)."
    ),
    "tranchen": (
        "AZ-4-Tranchen-Vorschläge (gestaffelte Kauf-/Verkaufszonen) an/aus - "
        "nur für BTC/ETH verfügbar."
    ),
    "price_usd": "Aktueller Marktpreis pro Einheit in US-Dollar.",
    "price_eur": "Aktueller Marktpreis pro Einheit in Euro.",
    "change_24h": "Preisänderung der letzten 24 Stunden in Prozent.",
    "aktualisiert": (
        "Wie lange der angezeigte Preis her ist. ⚠ markiert einen veralteten "
        "Preis (kein aktuelles Update erhalten)."
    ),
}

# Watchdog-Heartbeat (2026-07-13, siehe monitor/watchdog.py): _poll_prices()
# schreibt hier bei jedem Tick einen Zeitstempel rein - ein externer Watchdog-
# Prozess kann so erkennen, ob der Tk-Event-Loop wirklich noch pumpt (ein
# after()-Callback feuert nur dann), statt sich nur auf "Prozess existiert
# noch" zu verlassen. Ausloeser: GUI verschwand ueber Nacht am 24/7-Notebook,
# Scheduler lief im Hintergrund unbeeindruckt weiter - kein Absturz, sondern
# vermutlich ein eingefrorener/unsichtbarer Mainloop.
HEARTBEAT_PATH = Path(__file__).resolve().parent.parent / "data" / "gui_heartbeat.txt"


class TradingInfoToolApp(tk.Tk):
    def __init__(
        self, db_conn_factory, watchlist, coingecko_client, kraken_client=None, groq_client=None,
        cerebras_client=None, gemini_client=None, fred_api_key=None, bitpanda_api_key=None,
    ):
        super().__init__()
        self.title("TradingInfoTool")
        self.geometry("900x600")

        self._settings = ui_settings.load_settings()
        theme.set_dark_mode(self._settings["dark_mode"])
        if theme.is_dark():
            theme.apply_dark_mode(self)
        theme.apply_base_style(self)

        self._db_conn_factory = db_conn_factory
        self._watchlist = watchlist
        self._coingecko_client = coingecko_client
        self._kraken_client = kraken_client
        self._groq_client = groq_client
        self._cerebras_client = cerebras_client
        self._gemini_client = gemini_client
        self._fred_api_key = fred_api_key
        self._bitpanda_api_key = bitpanda_api_key
        self._bitpanda_assets: list | None = None
        self._refresh_bitpanda_assets()

        self._build_menu()

        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True)

        self._watchlist_frame = self._build_watchlist_tab(notebook)
        notebook.add(self._watchlist_frame, text="Watchlist")

        self._portfolio_view = PortfolioView(notebook, db_conn_factory, watchlist)
        notebook.add(self._portfolio_view, text="Portfolio")

        self._signals_view = SignalsView(
            notebook, db_conn_factory, watchlist, groq_client, coingecko_client, kraken_client,
            fred_api_key=fred_api_key, cerebras_client=cerebras_client, gemini_client=gemini_client,
        )
        notebook.add(self._signals_view, text="Signale")

        self._marktscan_view = MarktscanView(
            notebook, db_conn_factory, watchlist, groq_client, coingecko_client, kraken_client,
            fred_api_key=fred_api_key,
        )
        notebook.add(self._marktscan_view, text="Marktscan")

        self._hebel_view = HebelView(
            notebook, db_conn_factory, watchlist, groq_client, cerebras_client, coingecko_client,
            kraken_client, fred_api_key=fred_api_key, gemini_client=gemini_client,
        )
        notebook.add(self._hebel_view, text="Hebel")

        disclaimer = ttk.Label(
            self, text=DISCLAIMER_TEXT, foreground=theme.info_color(), wraplength=880, justify="center"
        )
        disclaimer.pack(side="bottom", fill="x", padx=8, pady=4)

        self._refresh_watchlist_from_db()
        self.after(UI_POLL_INTERVAL_MS, self._poll_prices)

    def report_callback_exception(self, exc, val, tb) -> None:
        """Tkinter faengt Exceptions aus Callbacks/after()-Ticks selbst ab und
        ruft diese Methode auf - der Default (Basisklasse) schreibt NUR nach
        stderr, was ohne angehaengte Konsole (Start per Verknuepfung) spurlos
        verschwindet (siehe HEARTBEAT_PATH-Docstring oben, Notebook-Vorfall
        2026-07-13). Zusaetzlich ins normale Logging, damit es in
        data/tradinginfotool.log UND im Watchdog-Crash-Log (stderr-Redirect)
        auftaucht."""
        logger.error("Unbehandelte Exception in Tk-Callback:\n%s", "".join(traceback.format_exception(exc, val, tb)))

    def _build_menu(self) -> None:
        menubar = tk.Menu(self)
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Bestände neu importieren", command=self._reimport_holdings)
        file_menu.add_command(label="Bestände aus Datei importieren…", command=self._import_holdings_from_file)
        file_menu.add_command(label="Bestände exportieren…", command=self._export_holdings)
        file_menu.add_command(
            label="Bestände von Bitpanda abgleichen",
            command=self._sync_bitpanda,
            state=("normal" if self._bitpanda_api_key else "disabled"),
        )
        file_menu.add_command(
            label="Einstandspreise von Bitpanda berechnen",
            command=self._sync_bitpanda_avg_cost,
            state=("normal" if self._bitpanda_api_key else "disabled"),
        )
        self._avg_cost_menu = file_menu
        self._avg_cost_menu_index = file_menu.index("end")
        file_menu.add_separator()
        file_menu.add_command(label="Beenden", command=self.destroy)
        menubar.add_cascade(label="Datei", menu=file_menu)

        view_menu = tk.Menu(menubar, tearoff=0)
        self._dark_mode_var = tk.BooleanVar(value=self._settings["dark_mode"])
        view_menu.add_checkbutton(
            label="Dark Mode", variable=self._dark_mode_var, command=self._toggle_dark_mode
        )
        menubar.add_cascade(label="Ansicht", menu=view_menu)

        benachrichtigung_menu = tk.Menu(menubar, tearoff=0)
        self._email_nur_bitpanda_var = tk.BooleanVar(
            value=self._settings["email_empfehlungen_nur_bitpanda"]
        )
        benachrichtigung_menu.add_checkbutton(
            label="E-Mail-Empfehlungen nur für Bitpanda-gelistete Assets",
            variable=self._email_nur_bitpanda_var,
            command=self._toggle_email_nur_bitpanda,
        )
        menubar.add_cascade(label="Benachrichtigungen", menu=benachrichtigung_menu)

        hebel_menu = tk.Menu(menubar, tearoff=0)
        self._hebel_richtung_var = tk.StringVar(
            value=self._settings["hebel_richtung_modus"]
        )
        hebel_menu.add_radiobutton(
            label="Long + Short analysieren", variable=self._hebel_richtung_var,
            value="beide", command=self._toggle_hebel_richtung,
        )
        hebel_menu.add_radiobutton(
            label="Nur Long analysieren (Bitpanda kann Hebel-Short nicht ausführen)",
            variable=self._hebel_richtung_var,
            value="nur_long", command=self._toggle_hebel_richtung,
        )
        menubar.add_cascade(label="Hebel", menu=hebel_menu)

        self.config(menu=menubar)

    def _toggle_dark_mode(self) -> None:
        """Speichert nur die Praeferenz - wendet sie NICHT live an (siehe
        ui/theme.py-Docstring: Neustart-Modell statt Live-Umfaerben aller bereits
        gerenderten Widgets/Treeview-Tags)."""
        self._settings["dark_mode"] = self._dark_mode_var.get()
        ui_settings.save_settings(self._settings)
        messagebox.showinfo(
            "Dark Mode",
            "Einstellung gespeichert. Bitte TradingInfoTool neu starten, damit die Änderung wirkt.",
        )

    def _toggle_email_nur_bitpanda(self) -> None:
        """Anders als Dark Mode SOFORT wirksam, kein Neustart noetig - der
        Hintergrund-Job liest die Einstellung erst beim tatsaechlichen
        E-Mail-Versand (siehe scheduler/background.py::
        _ist_email_relevantes_asset())."""
        self._settings["email_empfehlungen_nur_bitpanda"] = self._email_nur_bitpanda_var.get()
        ui_settings.save_settings(self._settings)

    def _toggle_hebel_richtung(self) -> None:
        """LIVE wirksam wie E-Mail-Filter, kein Neustart noetig - der
        Budget-Allocator liest die Einstellung direkt vor dem naechsten
        15-Min-Lauf (siehe agent/krypto/budget_allocator.py::
        run_budget_allocator())."""
        self._settings["hebel_richtung_modus"] = self._hebel_richtung_var.get()
        ui_settings.save_settings(self._settings)

    def _build_watchlist_tab(self, parent) -> ttk.Frame:
        frame = ttk.Frame(parent)

        toolbar = ttk.Frame(frame)
        toolbar.pack(fill="x", padx=8, pady=(8, 0))
        ttk.Button(toolbar, text="Jetzt aktualisieren", command=self._manual_refresh).pack(
            side="left"
        )
        ttk.Button(
            toolbar, text="Tranchen-Vorschläge umschalten (BTC/ETH)",
            command=self._toggle_dca_erlaubt,
        ).pack(side="left", padx=(8, 0))
        ttk.Button(
            toolbar, text="Asset hinzufügen…", command=self._open_asset_add_dialog,
        ).pack(side="left", padx=(8, 0))
        ttk.Button(
            toolbar, text="Asset bearbeiten…", command=self._open_asset_edit_dialog,
        ).pack(side="left", padx=(8, 0))

        columns = (
            "symbol",
            "name",
            "rolle",
            "assetklasse",
            "status",
            "bitpanda",
            "tranchen",
            "price_usd",
            "price_eur",
            "change_24h",
            "aktualisiert",
        )
        headings = {
            "symbol": "Symbol",
            "name": "Name",
            "rolle": "Rolle",
            "assetklasse": "Assetklasse",
            "status": "Status",
            "bitpanda": "Bitpanda",
            "tranchen": "AZ-4-Tranchen",
            "price_usd": "Preis (USD)",
            "price_eur": "Preis (EUR)",
            "change_24h": "24h %",
            "aktualisiert": "Aktualisiert",
        }
        tree = ttk.Treeview(frame, columns=columns, show="headings")
        for col in columns:
            tree.heading(col, text=headings[col])
            anchor = "w" if col in ("name", "rolle", "assetklasse", "status") else "e"
            tree.column(col, width=90 if col in ("bitpanda", "tranchen") else 110, anchor=anchor)
        tree.tag_configure("stale", foreground=theme.stale_color())
        tree.tag_configure("bitpanda_fehlt", foreground=theme.danger_color())
        frame.reapply_sort = make_sortable(
            tree, numeric_columns=frozenset({"price_usd", "price_eur", "change_24h"})
        )
        add_heading_tooltips(tree, _WATCHLIST_COLUMN_DESCRIPTIONS)
        add_row_tooltips(tree, self._watchlist_row_tooltip_text)
        tree.bind("<Double-1>", self._open_chart)
        tree.pack(fill="both", expand=True, padx=8, pady=8)

        frame.tree = tree
        return frame

    def _refresh_watchlist_from_db(self) -> None:
        conn = self._db_conn_factory()
        try:
            latest_prices = db.get_latest_prices(conn)
            dca_erlaubt_by_symbol = {
                sym: db.get_dca_erlaubt(conn, sym) for sym in ("BTC", "ETH")
            }
            # Klassifikations-Redesign (2026-07-16): "gehalten" ist kein
            # gespeichertes Feld mehr, sondern wird live aus den echten
            # Bestaenden (Spot) UND offenen Hebel-Positionen abgeleitet - kann
            # dadurch nie veralten (siehe config.py::WatchlistAsset-Docstring).
            gehaltene_symbole = {
                h.symbol for h in db.get_all_holdings(conn)
                if (h.quantity or 0.0) + (h.staked_quantity or 0.0) > 0.0
            }
            offene_hebel_symbole = {p.symbol for p in db.get_open_hebel_positions(conn)}
        finally:
            conn.close()

        tree = self._watchlist_frame.tree
        # GUI-Refresh-Fix (2026-07-16, Nutzer-Fund): dieser Refresh laeuft alle
        # 3 Sek. automatisch (_poll_prices()) - ohne Auswahl-/Sortierungs-
        # Erhalt waere jede Zeilenauswahl/Spaltensortierung binnen 3 Sek.
        # wieder weg. Stabile iid (Symbol) + Auswahl vor dem Neuaufbau merken
        # + danach wiederherstellen, analog zum bereits bestehenden Muster in
        # ui/hebel_view.py::refresh().
        vorher_selected = tree.selection()
        vorher_iid = vorher_selected[0] if vorher_selected else None
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

            if asset.assetklasse != "krypto":
                # Bitpanda-Listing-Check ist Krypto-spezifisch (vergleicht gegen den
                # Krypto-Asset-Katalog) - fuer Aktien/ETF/Rohstoffe ergibt "ist es dort
                # gelistet" keinen Sinn, die liegen ja bereits im Wertpapierdepot des
                # Nutzers (Multi-Asset-Tracking, 2026-07-09).
                bitpanda_text = "-"
                bitpanda_fehlt = False
            elif self._bitpanda_assets is None:
                bitpanda_text = "?"
                bitpanda_fehlt = False
            elif bitpanda_is_listed(asset.symbol, self._bitpanda_assets, name=asset.name):
                bitpanda_text = "✓"
                bitpanda_fehlt = False
            else:
                bitpanda_text = "✗"
                bitpanda_fehlt = True

            tags = []
            if stale:
                tags.append("stale")
            if bitpanda_fehlt:
                tags.append("bitpanda_fehlt")  # zuletzt hinzugefuegt = hoehere Prioritaet bei ttk-Tag-Kollision

            # AZ-4-Tranchen-Toggle (2026-07-12): nur fuer BTC/ETH relevant (siehe
            # agent/krypto/pipeline.py::generate_signal() tranchen_erlaubt-Berechnung).
            if asset.symbol in dca_erlaubt_by_symbol:
                tranchen_text = "An" if dca_erlaubt_by_symbol[asset.symbol] else "Aus"
            else:
                tranchen_text = "-"

            if asset.symbol in gehaltene_symbole or asset.symbol in offene_hebel_symbole:
                status_text = "Gehalten"
            else:
                status_text = asset.beobachtungsstatus

            tree.insert(
                "",
                "end",
                iid=asset.symbol,
                values=(
                    asset.symbol,
                    asset.name,
                    asset.rolle,
                    asset.assetklasse,
                    status_text,
                    bitpanda_text,
                    tranchen_text,
                    price_usd,
                    price_eur,
                    change,
                    aktualisiert,
                ),
                tags=tuple(tags),
            )
        self._watchlist_frame.reapply_sort()
        theme.restripe_treeview(tree)
        if vorher_iid and tree.exists(vorher_iid):
            tree.selection_set(vorher_iid)

    def _watchlist_row_tooltip_text(self, symbol: str) -> str | None:
        """Lazy (nur beim tatsaechlichen Hover aufgerufen, siehe ui/row_tooltip.py)
        - zeigt die letzte echte Analyse fuer dieses Symbol, ohne in den
        Signale-Tab wechseln zu muessen (2026-07-16, Nutzer-Wunsch: sinnvolle
        Zusatzinfo je Zeile, wo es aktuell kein eigenes Detail-Panel gibt)."""
        conn = self._db_conn_factory()
        try:
            signal = db.get_latest_signal(conn, symbol)
        finally:
            conn.close()
        if signal is None:
            return "Noch keine Analyse berechnet."
        when = signal.created_at[:16].replace("T", " ") if signal.created_at else "-"
        conf = f"{signal.confidence_pct:.0f}%" if signal.confidence_pct is not None else "-"
        text = f"Letztes Signal: {signal.action} ({when}, Konfidenz {conf})"
        if signal.short_reasoning:
            text += f"\n{signal.short_reasoning}"
        return text

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

    def _open_asset_add_dialog(self) -> None:
        AssetAddDialog(self, on_added=self._on_watchlist_changed)

    def _open_asset_edit_dialog(self) -> None:
        tree = self._watchlist_frame.tree
        selected = tree.selection()
        if not selected:
            messagebox.showinfo("Asset bearbeiten", "Bitte zuerst eine Zeile in der Watchlist auswählen.")
            return
        symbol = tree.item(selected[0], "values")[0]
        asset = next((a for a in self._watchlist if a.symbol == symbol), None)
        if asset is None:
            return
        AssetEditDialog(self, asset, on_edited=self._on_watchlist_changed)

    def _on_watchlist_changed(self) -> None:
        """Nach Hinzufuegen/Bearbeiten: Watchlist-Anzeige aktualisieren. Wirkt
        NUR auf die Anzeige (self._watchlist selbst wird erst mit einem
        Neustart neu aus config.yaml geladen, gleiche Einschraenkung wie bei
        add_watchlist_entry()/update_watchlist_rolle() schon immer)."""
        messagebox.showinfo(
            "Watchlist geändert",
            "Änderung gespeichert. Für volle Wirkung (Signale/Facts/Cooldown-Einstufung) "
            "ist ein Neustart der App nötig.",
        )

    def _poll_prices(self) -> None:
        self._write_heartbeat()
        self._refresh_watchlist_from_db()
        self._portfolio_view.refresh()
        self._hebel_view.refresh()
        # 2026-07-16, Nutzer-Fund: Signale/Marktscan hatten (anders als Hebel
        # hier schon immer) KEINEN periodischen Refresh - der automatische
        # Scheduler (budget_allocator, alle 15 Min) schreibt neue Signale/
        # Marktscan-Ergebnisse in die DB und verschickt E-Mails, aber die GUI
        # zeigte das erst nach einer manuellen Aktion im jeweiligen Tab. Jetzt
        # konsistent mit Hebel behandelt - sicher seit dem GUI-Refresh-Fix
        # (Auswahl/Sortierung ueberleben einen Neuaufbau).
        self._signals_view._refresh_list()
        self._marktscan_view._refresh_list()
        self.after(UI_POLL_INTERVAL_MS, self._poll_prices)

    def _write_heartbeat(self) -> None:
        """Atomarer Write (tmp-Datei + os.replace) - vermeidet einen Torn-Read,
        falls monitor/watchdog.py genau in dem Moment liest, in dem geschrieben
        wird. Best-effort: ein Schreibfehler (z.B. Datentraeger kurz nicht
        erreichbar) darf die _poll_prices()-Rekursion nicht abbrechen, sonst
        wuerde ausgerechnet der Heartbeat-Mechanismus selbst zum Absturzgrund."""
        try:
            tmp_path = HEARTBEAT_PATH.with_suffix(".tmp")
            tmp_path.write_text(datetime.now(timezone.utc).isoformat(), encoding="utf-8")
            os.replace(tmp_path, HEARTBEAT_PATH)
        except OSError:
            logger.exception("Heartbeat-Datei konnte nicht geschrieben werden")

    def _refresh_bitpanda_assets(self) -> None:
        """Handelsboersen-Check (Nutzer-Wunsch 2026-07-09) - einmalig beim Start und
        bei manuellem Refresh, NICHT im 3-Sekunden-Preis-Poll (Bitpandas gelistete
        Assets aendern sich nicht minuetlich, ein wiederholter Call (paginiert,
        mehrere Requests) waere verschwendet). P-10: Fehlschlag blockiert den Start
        nicht, Spalte zeigt dann "?" statt eines falschen Werts."""
        from api.bitpanda import get_listed_assets

        try:
            self._bitpanda_assets = get_listed_assets()
        except Exception:
            self._bitpanda_assets = None

    def _toggle_dca_erlaubt(self) -> None:
        """AZ-4-Tranchen-Toggle (2026-07-12) - nur fuer BTC/ETH sinnvoll (siehe
        agent/krypto/pipeline.py::generate_signal()), operiert auf der aktuell in der
        Watchlist ausgewaehlten Zeile."""
        tree = self._watchlist_frame.tree
        selected = tree.selection()
        if not selected:
            messagebox.showinfo(
                "Tranchen-Vorschläge umschalten", "Bitte zuerst BTC oder ETH in der Watchlist auswählen."
            )
            return
        symbol = tree.item(selected[0], "values")[0]
        if symbol not in ("BTC", "ETH"):
            messagebox.showinfo(
                "Tranchen-Vorschläge umschalten",
                "AZ-4-Tranchen sind aktuell nur für BTC und ETH vorgesehen.",
            )
            return

        conn = self._db_conn_factory()
        try:
            neuer_wert = not db.get_dca_erlaubt(conn, symbol)
            db.set_dca_erlaubt(conn, symbol, neuer_wert)
        finally:
            conn.close()

        self._refresh_watchlist_from_db()

    def _manual_refresh(self) -> None:
        from scheduler.background import refresh_prices_job

        refresh_prices_job(self._coingecko_client, self._db_conn_factory, self._watchlist)
        self._refresh_bitpanda_assets()
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

    def _import_holdings_from_file(self) -> None:
        """Gegenstueck zum Export (Nutzer-Idee 2026-07-09): laesst den Nutzer eine
        beliebige Excel-Datei (typischerweise die zuvor exportierte, ggf. bearbeitete
        Assets_export.xlsx) auswaehlen, statt fix von Assets.xlsx zu importieren."""
        selected = filedialog.askopenfilename(
            title="Bestände aus Datei importieren",
            initialdir=str(EXPORT_XLSX_PATH.parent),
            filetypes=[("Excel-Dateien", "*.xlsx"), ("Alle Dateien", "*.*")],
        )
        if not selected:
            return

        conn = self._db_conn_factory()
        try:
            result = import_holdings(conn, path=Path(selected))
        finally:
            conn.close()

        self._portfolio_view.refresh()

        message = f"{result.imported_count} Bestände aus '{Path(selected).name}' importiert."
        if result.warnings:
            message += "\n\nWarnungen:\n" + "\n".join(result.warnings)
        messagebox.showinfo("Bestände aus Datei importieren", message)

    def _export_holdings(self) -> None:
        """Gegenstueck zum Import (Nutzer-Idee 2026-07-09): schreibt eine SEPARATE
        Datei (nie die handgepflegte Original-Assets.xlsx direkt), die der Nutzer
        pruefen/bearbeiten und ueber 'Bestände aus Datei importieren…' wieder
        einlesen kann."""
        conn = self._db_conn_factory()
        try:
            count = export_holdings(conn)
        finally:
            conn.close()

        messagebox.showinfo(
            "Bestände exportieren",
            f"{count} Assets nach '{EXPORT_XLSX_PATH.name}' exportiert.\n\n{EXPORT_XLSX_PATH}",
        )

    def _sync_bitpanda(self) -> None:
        """Bestände + EUR-Fiat-Cash live von Bitpanda abgleichen (2026-07-10,
        Nutzer-Wunsch, hybrid neben dem bestehenden Excel-Import/-Export - siehe
        importer/bitpanda_sync.py). Manuell ausgeloest, kein Hintergrund-Job."""
        if not self._bitpanda_api_key:
            return  # defensiver Re-Check, Menuepunkt ist ohne Key ohnehin deaktiviert

        from importer.bitpanda_sync import sync_from_bitpanda

        conn = self._db_conn_factory()
        try:
            try:
                result = sync_from_bitpanda(conn, self._bitpanda_api_key, self._bitpanda_assets or [])
            except Exception as exc:
                messagebox.showerror(
                    "Bestände von Bitpanda abgleichen",
                    f"Abgleich abgebrochen, nichts wurde verändert:\n\n{exc}",
                )
                return
        finally:
            conn.close()

        self._portfolio_view.refresh()
        # Immer neu laden, nicht nur bei result.cash_reserve_updated (2026-07-11) -
        # der "zuletzt synchronisiert"-Zeitstempel aendert sich bei JEDEM erfolgreichen
        # Sync-Check, auch wenn der Cash-Wert selbst unveraendert blieb.
        self._portfolio_view.reload_cash_reserve_from_db()

        # Nutzer-Wunsch (2026-07-10): nach jedem Sync automatisch die Export-Datei
        # aktualisieren, damit sich der Live-Abgleich auch in Excel niederschlaegt -
        # bewusst NICHT die handgepflegte Original-Assets.xlsx (die bleibt wie
        # bisher unangetastet), sondern dieselbe separate Assets_export.xlsx wie
        # beim manuellen "Bestände exportieren…".
        export_conn = self._db_conn_factory()
        try:
            export_holdings(export_conn)
        finally:
            export_conn.close()

        lines = [f"{result.synced_count} Bestände aktualisiert."]
        if result.updated_holdings:
            lines.append("\nGeänderte Bestände:\n" + "\n".join(result.updated_holdings))
        if result.cash_reserve_updated:
            lines.append(
                f"\nFiat-Cash-Reserve: {result.cash_reserve_old_eur:.2f} € → "
                f"{result.cash_reserve_new_eur:.2f} €"
            )
        if result.unmatched_bitpanda_symbols:
            lines.append(
                "\nBei Bitpanda gehalten, aber keiner Watchlist zuordenbar:\n"
                + "\n".join(result.unmatched_bitpanda_symbols)
            )
        if result.stale_bitpanda_sync_symbols:
            lines.append(
                "\n⚠ Früher per Bitpanda-Sync gesetzt, jetzt nicht mehr in der Antwort "
                "(NICHT automatisch auf 0 gesetzt, bitte manuell prüfen):\n"
                + "\n".join(result.stale_bitpanda_sync_symbols)
            )
        if result.auto_confirmed_decreases:
            lines.append(
                "\nRückgänge automatisch übernommen (Staking-Verifikation erfolgreich, "
                "kein echter Verkauf/Staking-Blindspot mehr möglich):\n"
                + "\n".join(result.auto_confirmed_decreases)
            )
        if result.decreased_holdings_needs_confirmation:
            grund = (
                "Staking-Verifikation in diesem Lauf nicht möglich (z. B. Netzwerkfehler "
                "beim Transaktions-Abruf)"
                if not result.staking_verified
                else "unbekannter Grund"
            )
            lines.append(
                f"\n⚠ {len(result.decreased_holdings_needs_confirmation)} Bestand/-e mit "
                f"gemeldetem Rückgang - NICHT automatisch übernommen ({grund}). "
                "Bestätigung im nächsten Dialog nötig."
            )
        if result.warnings:
            lines.append("\nWarnungen:\n" + "\n".join(result.warnings))
        lines.append(
            f"\n'{EXPORT_XLSX_PATH.name}' wurde automatisch aktualisiert."
            "\n\nHinweis: Es werden ausschließlich lesende Abfragen gemacht (kein Order-/"
            "Auszahlungszugriff über Bitpanda-API-Keys möglich)."
        )
        messagebox.showinfo("Bestände von Bitpanda abgleichen", "\n".join(lines))

        if result.plausible_signal_matches:
            BitpandaMatchConfirmDialog(self, self._db_conn_factory, result.plausible_signal_matches)

        if result.decreased_holdings_needs_confirmation:
            BitpandaDecreaseConfirmDialog(
                self, self._db_conn_factory, result.decreased_holdings_needs_confirmation,
                on_applied=self._after_decrease_applied,
            )

    def _sync_bitpanda_avg_cost(self) -> None:
        """Echter Anschaffungspreis (2026-07-11, Nutzer-Wunsch) aus Bitpanda-Trade-
        Historie berechnen - bewusst EIGENER Menuepunkt, unabhaengig vom Bestands-
        abgleich (siehe importer/bitpanda_avg_cost.py Modul-Docstring). Anders als
        _sync_bitpanda() (schnell, ~60 Objekte) braucht dieser Lauf bei einem
        Erstsync bis zu ~9500 Transaktionen (live gemessen: ~40s) - MUSS deshalb
        threaded laufen, sonst friert die UI ein."""
        if not self._bitpanda_api_key:
            return  # defensiver Re-Check, Menuepunkt ist ohne Key ohnehin deaktiviert

        self._avg_cost_menu.entryconfig(self._avg_cost_menu_index, state="disabled")
        self.title("TradingInfoTool — Einstandspreise werden berechnet …")

        thread = threading.Thread(target=self._run_avg_cost_sync, daemon=True)
        thread.start()

    def _run_avg_cost_sync(self) -> None:
        from importer.bitpanda_avg_cost import sync_avg_buy_prices

        def on_progress(loaded: int, total: int) -> None:
            self.after(0, self._update_avg_cost_progress, loaded, total)

        conn = self._db_conn_factory()
        try:
            watchlist = self._watchlist
            result = sync_avg_buy_prices(
                conn, self._bitpanda_api_key, watchlist, self._bitpanda_assets or [], on_progress=on_progress
            )
            error = None
        except Exception as exc:  # noqa: BLE001 - an die UI durchreichen statt den Thread stumm sterben zu lassen
            result = None
            error = exc
        finally:
            conn.close()

        self.after(0, self._on_avg_cost_sync_done, result, error)

    def _update_avg_cost_progress(self, loaded: int, total: int) -> None:
        self.title(f"TradingInfoTool — Einstandspreise werden berechnet … ({loaded}/{total})")

    def _on_avg_cost_sync_done(self, result, error) -> None:
        self.title("TradingInfoTool")
        self._avg_cost_menu.entryconfig(self._avg_cost_menu_index, state="normal")

        if error is not None:
            messagebox.showerror(
                "Einstandspreise von Bitpanda berechnen",
                f"Berechnung abgebrochen, nichts wurde verändert:\n\n{error}",
            )
            return

        self._portfolio_view.refresh()

        lines = [
            f"{result.total_transactions_fetched} Transaktionen "
            f"{'neu ' if result.incremental else ''}geladen, {len(result.updated_symbols)} Assets aktualisiert."
        ]
        if result.unmatched_bitpanda_symbols:
            lines.append(
                "\nBei Bitpanda gehandelt, aber keiner Watchlist zuordenbar:\n"
                + ", ".join(result.unmatched_bitpanda_symbols)
            )
        messagebox.showinfo("Einstandspreise von Bitpanda berechnen", "\n".join(lines))

    def _after_decrease_applied(self) -> None:
        """Callback fuer BitpandaDecreaseConfirmDialog - Portfolio-Ansicht neu laden
        UND die Export-Datei erneut schreiben, damit bestaetigte Rueckgaenge sich
        ebenfalls dort niederschlagen (Nutzer-Wunsch 2026-07-10, siehe _sync_bitpanda())."""
        self._portfolio_view.refresh()
        conn = self._db_conn_factory()
        try:
            export_holdings(conn)
        finally:
            conn.close()


class BitpandaMatchConfirmDialog(tk.Toplevel):
    """Bestaetigungs-Dialog fuer plausible Signal-Umsetzungen, die der Bitpanda-Sync
    erkannt hat (2026-07-10, Nutzer-Idee). Bewusst NICHT der bestehende
    UmsetzungDialog (ui/signals_view.py) - der Bestand ist zu diesem Zeitpunkt vom
    Sync bereits korrekt geschrieben, ein zweiter Schreibpfad in holdings waere hier
    nur redundant. Dieser Dialog schreibt AUSSCHLIESSLICH die Signal-Umsetzungs-
    Rueckmeldung (db.update_signal_umsetzung), nie holdings. Kein Auto-Confirm ohne
    Blick des Nutzers (RG-5/"KI schlaegt vor, Mensch entscheidet")."""

    def __init__(self, parent, db_conn_factory, matches) -> None:
        super().__init__(parent)
        self._db_conn_factory = db_conn_factory
        self._matches = matches
        self._vars = [tk.BooleanVar(value=True) for _ in matches]

        self.title("Signal-Umsetzung erkannt?")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        frame = ttk.Frame(self, padding=12)
        frame.pack(fill="both", expand=True)

        ttk.Label(
            frame,
            text="Diese Bestandsänderungen passen zu noch offenen Signalen. Bestätigen?",
            wraplength=420,
        ).grid(row=0, column=0, sticky="w", pady=(0, 8))

        for i, match in enumerate(matches):
            when = match.signal_datum[:16].replace("T", " ") if match.signal_datum else "-"
            text = (
                f"{match.symbol} — {match.action}: {match.alt_menge:g} → {match.neu_menge:g} "
                f"(Signal vom {when})"
            )
            ttk.Checkbutton(frame, text=text, variable=self._vars[i]).grid(
                row=i + 1, column=0, sticky="w", pady=2
            )

        button_frame = ttk.Frame(frame)
        button_frame.grid(row=len(matches) + 1, column=0, sticky="e", pady=(10, 0))
        ttk.Button(button_frame, text="Abbrechen", command=self.destroy).pack(side="right", padx=(6, 0))
        ttk.Button(button_frame, text="Ausgewählte bestätigen", command=self._on_confirm).pack(side="right")

    def _on_confirm(self) -> None:
        conn = self._db_conn_factory()
        try:
            for match, var in zip(self._matches, self._vars):
                if var.get():
                    db.update_signal_umsetzung(conn, match.signal_id, True, umgesetzt_menge=match.neu_menge)
        finally:
            conn.close()
        self.destroy()


class BitpandaDecreaseConfirmDialog(tk.Toplevel):
    """Bestaetigungs-Dialog fuer von Bitpanda gemeldete BESTANDSRUECKGAENGE
    (2026-07-10, live entdeckt: gestakte Anteile sind ueber die Bitpanda-API nicht
    auslesbar - live gegen /wallets, /asset-wallets und /wallets/transactions
    geprueft, keine liefert einen Staking-Wert - ein Rueckgang kann also ein echter
    Verkauf ODER nur ein API-Sichtfeld-Problem sein). Standardmaessig ALLE Checkboxen
    UNGEHAKT (anders als BitpandaMatchConfirmDialog) - ein Rueckgang ist die
    riskantere Richtung, hier soll der Nutzer aktiv zustimmen statt nur abwaehlen."""

    def __init__(self, parent, db_conn_factory, candidates, on_applied=None) -> None:
        super().__init__(parent)
        self._db_conn_factory = db_conn_factory
        self._candidates = candidates
        self._on_applied = on_applied
        self._vars = [tk.BooleanVar(value=False) for _ in candidates]
        # Klassifikations-Redesign (2026-07-16): keine Status-Downgrade-Option
        # mehr hier - "gehalten" wird live aus den echten Bestaenden abgeleitet
        # (siehe config.py::WatchlistAsset-Docstring), es gibt also nichts mehr,
        # das bei einem Verkauf zurueckgesetzt werden muesste. `beobachtungsstatus`
        # bleibt bewusst rein manuell (GUI-Bearbeiten-Dialog), nie automatisch
        # geschrieben.

        self.title("Bestandsrückgänge bestätigen")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        frame = ttk.Frame(self, padding=12)
        frame.pack(fill="both", expand=True)

        ttk.Label(
            frame,
            text=(
                "Bitpanda meldet für diese Bestände einen Rückgang. Das kann ein echter "
                "Verkauf sein, oder nur daran liegen, dass gestakte Anteile über die API "
                "nicht sichtbar sind. Nur bestätigte Positionen werden übernommen."
            ),
            wraplength=440,
        ).grid(row=0, column=0, sticky="w", pady=(0, 8))

        row = 1
        for i, cand in enumerate(candidates):
            text = f"{cand.symbol}: {cand.alt_menge:g} → {cand.neu_menge:g}"
            if cand.matching_signal_id is not None:
                when = cand.matching_signal_datum[:16].replace("T", " ") if cand.matching_signal_datum else "-"
                text += f" (passt zu offenem {cand.matching_signal_action}-Signal vom {when})"
            ttk.Checkbutton(frame, text=text, variable=self._vars[i]).grid(
                row=row, column=0, sticky="w", pady=2
            )
            row += 1

        button_frame = ttk.Frame(frame)
        button_frame.grid(row=row, column=0, sticky="e", pady=(10, 0))
        ttk.Button(button_frame, text="Keine übernehmen", command=self.destroy).pack(side="right", padx=(6, 0))
        ttk.Button(button_frame, text="Ausgewählte übernehmen", command=self._on_confirm).pack(side="right")

    def _on_confirm(self) -> None:
        from importer.bitpanda_sync import apply_decrease

        conn = self._db_conn_factory()
        try:
            for cand, var in zip(self._candidates, self._vars):
                if not var.get():
                    continue
                apply_decrease(conn, cand)
        finally:
            conn.close()
        if self._on_applied:
            self._on_applied()
        self.destroy()


def _validate_new_asset(
    symbol: str, name: str, assetklasse: str, coingecko_id: str | None, coingecko_client,
) -> list[str]:
    """Live-Validierung gegen CoinGecko + Bitpanda (2026-07-16, Nutzer-Wunsch:
    "gleich eine Validierung ... ob das Asset korrekt eingetragen ist und
    gelistet") - analog zum manuellen BRETT-Check aus derselben Session, jetzt
    fest eingebaut statt Einzelfall-Handarbeit. Gibt eine Liste von
    Warnungen zurueck (leer = alles ok) - blockiert das Hinzufuegen NICHT
    (P-10: der Nutzer behaelt die letzte Entscheidung, aber wird gewarnt statt
    eines stillen Fehlschlags)."""
    warnungen: list[str] = []

    if assetklasse == "krypto":
        if coingecko_id:
            try:
                prices = coingecko_client.get_simple_prices([coingecko_id])
                if coingecko_id not in prices or not prices[coingecko_id]:
                    warnungen.append(
                        f"CoinGecko-ID '{coingecko_id}' liefert keine Preisdaten - bitte prüfen, ob sie korrekt ist."
                    )
            except Exception as exc:
                warnungen.append(f"CoinGecko-Validierung fehlgeschlagen (Netzwerkfehler?): {exc}")
        else:
            warnungen.append("Keine CoinGecko-ID angegeben - Spot-Analyse funktioniert erst, wenn sie nachgetragen wird.")

        try:
            from api.bitpanda import get_listed_assets
            listed = get_listed_assets()
            if not bitpanda_is_listed(symbol, listed, name=name):
                warnungen.append(f"'{symbol}' wurde nicht in Bitpandas Krypto-Katalog gefunden.")
        except Exception as exc:
            warnungen.append(f"Bitpanda-Validierung fehlgeschlagen (Netzwerkfehler?): {exc}")
    else:
        try:
            from api.bitpanda import get_listed_non_crypto_assets
            listed = get_listed_non_crypto_assets()
            if not bitpanda_is_listed(symbol, listed, name=name):
                warnungen.append(f"'{symbol}' wurde nicht in Bitpandas Nicht-Krypto-Katalog gefunden.")
        except Exception as exc:
            warnungen.append(f"Bitpanda-Validierung fehlgeschlagen (Netzwerkfehler?): {exc}")

    return warnungen


class AssetAddDialog(tk.Toplevel):
    """Manuelles Hinzufügen eines neuen Watchlist-Assets (2026-07-16,
    Klassifikations-Redesign - Nutzer-Beispiel: ein Symbol wie Solana soll mit
    `rolle=core` eintragbar sein, BEVOR es je gekauft wurde; bisher war das
    nur per Hand in config.yaml möglich, der einzige GUI-Weg war das
    Marktscan-"Übernehmen", das immer taktisch/beobachtung fest verdrahtete).
    Führt vor dem eigentlichen Schreiben eine Live-Validierung gegen
    CoinGecko/Bitpanda durch (_validate_new_asset()) - Warnungen blockieren
    NICHT, der Nutzer entscheidet nach Kenntnis der Warnung final selbst."""

    def __init__(self, parent, on_added=None) -> None:
        super().__init__(parent)
        self._parent_app = parent
        self._on_added = on_added
        self.title("Asset hinzufügen")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        frame = ttk.Frame(self, padding=12)
        frame.pack(fill="both", expand=True)

        self._symbol_var = tk.StringVar()
        self._name_var = tk.StringVar()
        self._assetklasse_var = tk.StringVar(value="krypto")
        self._rolle_var = tk.StringVar(value="taktisch")
        self._beobachtungsstatus_var = tk.StringVar(value="beobachtung")
        self._coingecko_id_var = tk.StringVar()
        self._yfinance_symbol_var = tk.StringVar()

        fields = [
            ("Symbol", self._symbol_var, None),
            ("Name", self._name_var, None),
            ("Assetklasse", self._assetklasse_var, ("krypto", "aktien", "etf", "rohstoffe")),
            ("Rolle", self._rolle_var, ("core", "taktisch")),
            ("Beobachtungsstatus", self._beobachtungsstatus_var, ("beobachtung", "ausgemustert")),
            ("CoinGecko-ID (optional)", self._coingecko_id_var, None),
            ("yfinance-Symbol (optional)", self._yfinance_symbol_var, None),
        ]
        for row, (label, var, values) in enumerate(fields):
            ttk.Label(frame, text=label).grid(row=row, column=0, sticky="w", pady=2)
            if values:
                ttk.Combobox(frame, textvariable=var, values=values, state="readonly", width=22).grid(
                    row=row, column=1, sticky="w", pady=2, padx=(8, 0)
                )
            else:
                ttk.Entry(frame, textvariable=var, width=25).grid(
                    row=row, column=1, sticky="w", pady=2, padx=(8, 0)
                )

        button_frame = ttk.Frame(frame)
        button_frame.grid(row=len(fields), column=0, columnspan=2, sticky="e", pady=(10, 0))
        ttk.Button(button_frame, text="Abbrechen", command=self.destroy).pack(side="right", padx=(6, 0))
        ttk.Button(button_frame, text="Hinzufügen", command=self._on_submit).pack(side="right")

    def _on_submit(self) -> None:
        import config as config_module

        symbol = self._symbol_var.get().strip().upper()
        name = self._name_var.get().strip()
        assetklasse = self._assetklasse_var.get()
        coingecko_id = self._coingecko_id_var.get().strip() or None
        yfinance_symbol = self._yfinance_symbol_var.get().strip() or None

        if not symbol or not name:
            messagebox.showwarning("Asset hinzufügen", "Symbol und Name sind Pflichtfelder.")
            return

        warnungen = _validate_new_asset(
            symbol, name, assetklasse, coingecko_id, self._parent_app._coingecko_client,
        )
        if warnungen:
            proceed = messagebox.askyesno(
                "Validierungswarnungen",
                "Folgende Punkte wurden auffällig:\n\n" + "\n".join(f"- {w}" for w in warnungen)
                + "\n\nTrotzdem hinzufügen?",
            )
            if not proceed:
                return

        try:
            config_module.add_watchlist_entry(
                symbol=symbol, name=name, rolle=self._rolle_var.get(),
                beobachtungsstatus=self._beobachtungsstatus_var.get(),
                coingecko_id=coingecko_id, assetklasse=assetklasse, yfinance_symbol=yfinance_symbol,
            )
        except config_module.WatchlistWriteError as exc:
            messagebox.showerror("Asset hinzufügen", f"Fehlgeschlagen: {exc}")
            return

        self.destroy()
        if self._on_added:
            self._on_added()


class AssetEditDialog(tk.Toplevel):
    """Bearbeiten von `rolle`/`beobachtungsstatus` eines bestehenden Watchlist-
    Assets (2026-07-16, Klassifikations-Redesign) - z.B. um ein taktisches
    Asset nach einem Strategiewechsel auf "ausgemustert" zu setzen, oder
    core/taktisch umzustellen. Symbol/Name/CoingeckoID etc. bleiben hier
    unveraendert (Symbol-Umbenennung o.ae. ist ein anderer, hier nicht
    abgedeckter Vorgang)."""

    def __init__(self, parent, asset, on_edited=None) -> None:
        super().__init__(parent)
        self._asset = asset
        self._on_edited = on_edited
        self.title(f"Asset bearbeiten: {asset.symbol}")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        frame = ttk.Frame(self, padding=12)
        frame.pack(fill="both", expand=True)

        ttk.Label(frame, text=f"{asset.symbol} — {asset.name}", font=("", 10, "bold")).grid(
            row=0, column=0, columnspan=2, sticky="w", pady=(0, 8)
        )

        self._rolle_var = tk.StringVar(value=asset.rolle)
        self._beobachtungsstatus_var = tk.StringVar(value=asset.beobachtungsstatus)

        ttk.Label(frame, text="Rolle").grid(row=1, column=0, sticky="w", pady=2)
        ttk.Combobox(
            frame, textvariable=self._rolle_var, values=("core", "taktisch"), state="readonly", width=22
        ).grid(row=1, column=1, sticky="w", pady=2, padx=(8, 0))

        ttk.Label(frame, text="Beobachtungsstatus").grid(row=2, column=0, sticky="w", pady=2)
        ttk.Combobox(
            frame, textvariable=self._beobachtungsstatus_var, values=("beobachtung", "ausgemustert"),
            state="readonly", width=22,
        ).grid(row=2, column=1, sticky="w", pady=2, padx=(8, 0))
        ttk.Label(
            frame, text="(wirkt nur, solange das Asset nicht gehalten wird - siehe Spalte 'Status')",
            wraplength=280, foreground=theme.stale_color(),
        ).grid(row=3, column=0, columnspan=2, sticky="w", pady=(0, 8))

        button_frame = ttk.Frame(frame)
        button_frame.grid(row=4, column=0, columnspan=2, sticky="e", pady=(10, 0))
        ttk.Button(button_frame, text="Abbrechen", command=self.destroy).pack(side="right", padx=(6, 0))
        ttk.Button(button_frame, text="Speichern", command=self._on_submit).pack(side="right")

    def _on_submit(self) -> None:
        import config as config_module

        try:
            config_module.update_watchlist_rolle(self._asset.symbol, self._rolle_var.get())
            config_module.update_watchlist_beobachtungsstatus(self._asset.symbol, self._beobachtungsstatus_var.get())
        except config_module.WatchlistWriteError as exc:
            messagebox.showerror("Asset bearbeiten", f"Fehlgeschlagen: {exc}")
            return

        self.destroy()
        if self._on_edited:
            self._on_edited()


def run_app(
    db_conn_factory, watchlist, coingecko_client, kraken_client=None, groq_client=None,
    cerebras_client=None, gemini_client=None, fred_api_key=None, bitpanda_api_key=None,
) -> None:
    app = TradingInfoToolApp(
        db_conn_factory, watchlist, coingecko_client, kraken_client, groq_client,
        cerebras_client=cerebras_client, gemini_client=gemini_client, fred_api_key=fred_api_key,
        bitpanda_api_key=bitpanda_api_key,
    )
    app.mainloop()
