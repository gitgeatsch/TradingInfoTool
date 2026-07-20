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

import agent.kategorie_thesen as kategorie_thesen
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
from ui.regime_view import RegimeView
from ui.row_tooltip import add_row_tooltips
from ui.screener_view import ScreenerView
from ui.signals_view import SignalsView
from ui.sortable_tree import make_sortable
from ui.thesen_view import ThesenView
from ui.widget_tooltip import add_notebook_tab_tooltips

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
    "schwerpunkt": (
        "Hauptgruppe / Unterkategorie (z. B. \"Edelmetalle / Gold\") aus der festen "
        "Kategorie-Taxonomie (Basisinfos/kategorien.yaml) - über 'Asset hinzufügen/"
        "bearbeiten' setzbar, Basis für die Diversifikations-Übersicht im Portfolio-Tab. "
        "▲/▼/● = aktive These im Schwerpunkte-Tab (▲ Übergewichten/Aktiv, ▼ Meiden, "
        "● Neutral) - solche Zeilen stehen zusätzlich weiter oben in der Liste "
        "(gehaltene Assets vor reinen Beobachtungskandidaten), Begründung per Mouseover "
        "auf die Zeile."
    ),
    "status": (
        "Gehalten (echter Bestand oder offene Hebel-Position, live abgeleitet) oder - falls nicht gehalten - "
        "Beobachtung (aktive Kandidatur) bzw. Ausgemustert (niedrigste Priorität, aber nicht ausgeschlossen). "
        "⚠ keine CoinGecko-ID = Spot-Analyse für dieses Asset strukturell inaktiv (z. B. automatisch aus einer "
        "Hebel-Position ergänzt) - ID über 'Asset hinzufügen/bearbeiten' nachtragen. "
        "⚠ kein yfinance-Symbol = dieselbe Lücke für Aktien/Themen-ETFs - über 'Asset bearbeiten' nachtragen."
    ),
    "bitpanda": (
        "✓ = auf Bitpanda handelbar, ✗ = nicht gelistet (blockiert Kauf-/Nachkauf-"
        "Signale), ? = noch nicht geprüft, - = nicht zutreffend (Nicht-Krypto-Asset)."
    ),
    "tranchen": (
        "AZ-4-Tranchen-Vorschläge (gestaffelte Kauf-/Verkaufszonen) an/aus - "
        "nur für BTC/ETH/SOL verfügbar."
    ),
    "hebel_pruefung": (
        "An = wird beim automatischen 15-Min-Hebel-Screening berücksichtigt (OI-Abruf, "
        "Trendfolge-/Kontra-Scoring, ggf. LLM-Call). Aus = kein neuer Hebel-Trigger für "
        "dieses Asset mehr, taucht nicht mehr als neuer Kandidat im Hebel-Tab auf. Bereits "
        "offene Hebel-Positionen bleiben davon unberührt und weiterhin risikoüberwacht. "
        "Nur für Krypto-Assets relevant. ⚠ = liefert seit mehreren Läufen in Folge von "
        "keiner der drei Börsen (Binance/Bybit/OKX) Open-Interest-Daten (siehe E-Mail-"
        "Warnung) - Hebel-Prüfung läuft technisch weiter, aber ohne OI-/Long-Short-"
        "Kontext; kein automatisches Abschalten."
    ),
    "price_usd": "Aktueller Marktpreis pro Einheit in US-Dollar.",
    "price_eur": "Aktueller Marktpreis pro Einheit in Euro.",
    "change_24h": "Preisänderung der letzten 24 Stunden in Prozent.",
    "aktualisiert": (
        "Wie lange der angezeigte Preis her ist. ⚠ markiert einen veralteten "
        "Preis (kein aktuelles Update erhalten)."
    ),
}

# Stufe-1-Hervorhebung (2026-07-20, Task #343 - Release 2, Marktscan/Screener-
# Bias-Vorstufe): rein visuelle Markierung + Sortier-Prioritaet fuer Assets,
# deren Hauptgruppe/Unterkategorie eine AKTIVE These hat (Basisinfos/
# Kategorie_Basisinformationen_Release2.md Abschnitt 5, Stufe 1 - explizit KEIN
# Scoring-Einfluss, siehe agent/kategorie_thesen.py). Transparenz-Prinzip
# (Nutzer-Vorgabe): jede Zeile, die dadurch bevorzugt einsortiert wird, traegt
# sichtbar einen der drei Marker - nie eine stille Umsortierung.
_THESE_MARKER_UND_TAG = {
    "uebergewichten": ("▲", "these_positiv"),
    "aktiv": ("▲", "these_positiv"),
    "meiden": ("▼", "these_negativ"),
    "neutral": ("●", "these_neutral"),
    "inaktiv": ("●", "these_neutral"),
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
        gemini_client=None, fred_api_key=None, bitpanda_api_key=None,
        mistral_client=None,
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
        self._gemini_client = gemini_client
        self._mistral_client = mistral_client
        self._fred_api_key = fred_api_key
        self._bitpanda_api_key = bitpanda_api_key
        self._bitpanda_assets: list | None = None
        self._bitpanda_non_crypto_assets: list | None = None
        self._refresh_bitpanda_assets()
        # Stufe-1-Hervorhebung (2026-07-20, Task #343) - je Symbol die aktive
        # These, falls eine passt (siehe _refresh_watchlist_from_db()), fuer den
        # Zeilen-Tooltip (_watchlist_row_tooltip_text()).
        self._these_by_symbol: dict[str, object] = {}

        self._build_menu()

        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True)

        self._watchlist_frame = self._build_watchlist_tab(notebook)
        notebook.add(self._watchlist_frame, text="Watchlist")

        self._portfolio_view = PortfolioView(notebook, db_conn_factory, watchlist)
        notebook.add(self._portfolio_view, text="Portfolio")

        self._signals_view = SignalsView(
            notebook, db_conn_factory, watchlist, groq_client, coingecko_client, kraken_client,
            fred_api_key=fred_api_key, gemini_client=gemini_client,
            mistral_client=mistral_client,
        )
        notebook.add(self._signals_view, text="Signale")

        self._marktscan_view = MarktscanView(
            notebook, db_conn_factory, watchlist, groq_client, coingecko_client, kraken_client,
            fred_api_key=fred_api_key,
        )
        notebook.add(self._marktscan_view, text="Marktscan")

        self._screener_view = ScreenerView(notebook, db_conn_factory, watchlist)
        notebook.add(self._screener_view, text="Screener")

        self._hebel_view = HebelView(
            notebook, db_conn_factory, watchlist, groq_client, coingecko_client,
            kraken_client, fred_api_key=fred_api_key, gemini_client=gemini_client,
            mistral_client=mistral_client,
        )
        notebook.add(self._hebel_view, text="Hebel")

        self._regime_view = RegimeView(notebook, db_conn_factory)
        notebook.add(self._regime_view, text="Regime")

        self._thesen_view = ThesenView(notebook, db_conn_factory)
        notebook.add(self._thesen_view, text="Schwerpunkte")

        # Tab-Kopf-Tooltips (2026-07-20, Nutzer-Wunsch: Kurzbeschreibung bei
        # Mouseover fuer die "Primaerseiten") - bewusst vorerst nur fuer die
        # beiden Tabs, deren Verhalten sich in dieser Runde geaendert/neu
        # entstanden ist (Screener: Auto-Scan; Schwerpunkte: neuer Tab); die
        # uebrigen Tabs koennen bei Bedarf im selben Muster ergaenzt werden.
        import config as config_module

        screener_intervall_minuten = config_module.load_config().get("screener", {}).get(
            "auto_scan_intervall_minuten", 60
        )
        add_notebook_tab_tooltips(notebook, {
            4: (
                f"Screener: sucht automatisch alle {screener_intervall_minuten} Minuten "
                "(+ jederzeit manuell) neue Aktien-/ETF-Kandidaten, die noch nicht in der "
                "Watchlist stehen. Kein Automatismus bei der Uebernahme: jede Aufnahme in "
                "die Watchlist braucht eine manuelle Bestaetigung, keine Bewertung/kein "
                "Score hier - das passiert erst danach ueber die normale Signal-Pipeline."
            ),
            7: (
                "Schwerpunkte: manuelle Verwaltung von Kategorie-Thesen (Übergewichten/"
                "Neutral/Meiden je Hauptgruppe/Unterkategorie). Wirkt sich NUR auf "
                "Hervorhebung/Sortierung in Watchlist, Portfolio und Screener aus "
                "(▲/▼/●-Marker) - KEIN Einfluss auf KI-Signale/Scores. Kein Automatismus: "
                "Thesen werden ausschliesslich hier manuell angelegt/bearbeitet."
            ),
        })

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
            toolbar, text="Tranchen-Vorschläge umschalten (BTC/ETH/SOL)",
            command=self._toggle_dca_erlaubt,
        ).pack(side="left", padx=(8, 0))
        ttk.Button(
            toolbar, text="Hebel-Prüfung umschalten",
            command=self._toggle_hebel_pruefung_erlaubt,
        ).pack(side="left", padx=(8, 0))
        ttk.Button(
            toolbar, text="Asset hinzufügen…", command=self._open_asset_add_dialog,
        ).pack(side="left", padx=(8, 0))
        ttk.Button(
            toolbar, text="Asset bearbeiten…", command=self._open_asset_edit_dialog,
        ).pack(side="left", padx=(8, 0))
        ttk.Button(
            toolbar, text="Zusammensetzung anzeigen…", command=self._open_asset_quality_dialog,
        ).pack(side="left", padx=(8, 0))

        columns = (
            "symbol",
            "name",
            "rolle",
            "assetklasse",
            "schwerpunkt",
            "status",
            "bitpanda",
            "tranchen",
            "hebel_pruefung",
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
            "schwerpunkt": "Schwerpunkt",
            "status": "Status",
            "bitpanda": "Bitpanda",
            "tranchen": "AZ-4-Tranchen",
            "hebel_pruefung": "Hebel-Prüfung",
            "price_usd": "Preis (USD)",
            "price_eur": "Preis (EUR)",
            "change_24h": "24h %",
            "aktualisiert": "Aktualisiert",
        }
        tree = ttk.Treeview(frame, columns=columns, show="headings")
        for col in columns:
            tree.heading(col, text=headings[col])
            anchor = "w" if col in ("name", "rolle", "assetklasse", "schwerpunkt", "status") else "e"
            tree.column(col, width=90 if col in ("bitpanda", "tranchen", "hebel_pruefung") else 110, anchor=anchor)
        tree.tag_configure("stale", foreground=theme.stale_color())
        tree.tag_configure("bitpanda_fehlt", foreground=theme.danger_color())
        tree.tag_configure("externe_id_fehlt", foreground=theme.danger_color())
        tree.tag_configure("these_positiv", foreground=theme.success_color())
        tree.tag_configure("these_negativ", foreground=theme.danger_color())
        tree.tag_configure("these_neutral", foreground=theme.info_color())
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
        import config as config_module

        conn = self._db_conn_factory()
        try:
            latest_prices = db.get_latest_prices(conn)
            dca_erlaubt_by_symbol = {
                sym: db.get_dca_erlaubt(conn, sym) for sym in ("BTC", "ETH", "SOL")
            }
            # Hebel-Pruefung-Toggle (2026-07-18) - fuer ALLE Krypto-Assets
            # relevant (nicht nur BTC/ETH/SOL wie beim Tranchen-Toggle), da
            # jedes Krypto-Asset per Default vom automatischen Hebel-Screening
            # erfasst wird (siehe agent/krypto/hebel_screening.py).
            hebel_pruefung_erlaubt_by_symbol = {
                a.symbol: db.get_hebel_pruefung_erlaubt(conn, a.symbol)
                for a in self._watchlist
                if a.assetklasse == "krypto" and not a.ist_cash_aequivalent
            }
            # OI-Abdeckungs-Warnung (2026-07-19, echter Notebook-Fund KAS/KAIA/
            # FLOKI/TURBO/CANTON) - sichtbare Markierung, wenn ein Symbol
            # wiederholt keine Open-Interest-Daten liefert (siehe
            # scheduler/background.py::_pruefe_oi_abdeckung_warnung()).
            import config as config_module

            hebel_cfg = config_module.load_config().get("hebel_screening", {})
            oi_schwelle = hebel_cfg.get("oi_abdeckung_schwelle_fehlschlaege", 8)
            oi_abdeckung_status = db.get_oi_abdeckung_status(conn)
            # Klassifikations-Redesign (2026-07-16): "gehalten" ist kein
            # gespeichertes Feld mehr, sondern wird live aus den echten
            # Bestaenden (Spot) UND offenen Hebel-Positionen abgeleitet - kann
            # dadurch nie veralten (siehe config.py::WatchlistAsset-Docstring).
            gehaltene_symbole = {
                h.symbol for h in db.get_all_holdings(conn)
                if (h.quantity or 0.0) + (h.staked_quantity or 0.0) > 0.0
            }
            offene_hebel_symbole = {p.symbol for p in db.get_open_hebel_positions(conn)}
            # Stufe-1-Hervorhebung (2026-07-20, Task #343) - aktive Thesen
            # einmal laden, In-Memory-Index statt N Einzel-Queries.
            these_index = kategorie_thesen.index_aktive_thesen(db.get_aktive_thesen(conn))
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
        self._these_by_symbol.clear()

        # Stufe-1-Sortier-Prioritaet (2026-07-20, Task #343, Nutzer-Entscheidung
        # "die gehaltenen Assets sollten Prioritaet erhalten"): NUR die initiale
        # Einsortierung, kein Eingriff in eine manuelle Spaltensortierung durch
        # den Nutzer (make_sortable()/reapply_sort() greift danach wie gewohnt).
        # Gruppe 0 = gehalten + aktive These, 1 = nicht gehalten + aktive These,
        # 2 = Rest - jede bevorzugt einsortierte Zeile traegt sichtbar einen der
        # drei Marker (siehe _THESE_MARKER_UND_TAG), keine stille Umsortierung.
        def _these_sort_key(asset):
            these = kategorie_thesen.lookup_these(these_index, asset.hauptgruppe, asset.unterkategorie)
            if these is None:
                return (2, asset.symbol)
            gehalten = asset.symbol in gehaltene_symbole or asset.symbol in offene_hebel_symbole
            return (0 if gehalten else 1, asset.symbol)

        for asset in sorted(self._watchlist, key=_these_sort_key):
            these = kategorie_thesen.lookup_these(these_index, asset.hauptgruppe, asset.unterkategorie)
            if these is not None:
                self._these_by_symbol[asset.symbol] = these
            snap = latest_prices.get(asset.symbol)
            price_usd = format_money(snap.price_usd if snap else None)
            price_eur = format_money(snap.price_eur if snap else None)
            change = f"{snap.change_24h_pct:+.2f}" if snap and snap.change_24h_pct is not None else "-"

            fetched_at = snap.fetched_at if snap else None
            stale = is_price_stale(fetched_at)
            age_text = format_price_age(fetched_at)
            aktualisiert = f"⚠ {age_text}" if stale else age_text

            # Bugfix 2026-07-18: fruehere Annahme "Bitpanda-Listing-Check ergibt fuer
            # Nicht-Krypto keinen Sinn" war seit dem 2026-07-16-Ausbau ueberholt -
            # agent/aktien/pipeline.py und agent/rohstoff/pipeline.py berechnen den
            # echten Status laengst (ueber get_listed_non_crypto_assets()), die
            # Watchlist-Spalte zeigte ihn nur nie an. Krypto und Nicht-Krypto nutzen
            # jetzt denselben Katalog-abhaengigen Vergleich, nur mit unterschiedlichem
            # Katalog.
            katalog = self._bitpanda_assets if asset.assetklasse == "krypto" else self._bitpanda_non_crypto_assets
            if katalog is None:
                bitpanda_text = "?"
                bitpanda_fehlt = False
            elif bitpanda_is_listed(asset.symbol, katalog, name=asset.name):
                bitpanda_text = "✓"
                bitpanda_fehlt = False
            else:
                bitpanda_text = "✗"
                bitpanda_fehlt = True

            tags = []
            if stale:
                tags.append("stale")
            if these is not None:
                tags.append(_THESE_MARKER_UND_TAG.get(these.richtung, ("●", "these_neutral"))[1])
            if bitpanda_fehlt:
                tags.append("bitpanda_fehlt")  # zuletzt hinzugefuegt = hoehere Prioritaet bei ttk-Tag-Kollision

            # AZ-4-Tranchen-Toggle (2026-07-12, 2026-07-18 um SOL erweitert): nur
            # fuer BTC/ETH/SOL relevant (siehe agent/krypto/pipeline.py::
            # generate_signal() tranchen_erlaubt-Berechnung).
            if asset.symbol in dca_erlaubt_by_symbol:
                tranchen_text = "An" if dca_erlaubt_by_symbol[asset.symbol] else "Aus"
            else:
                tranchen_text = "-"

            # Hebel-Pruefung-Toggle (2026-07-18) - fuer alle Krypto-Assets.
            if asset.symbol in hebel_pruefung_erlaubt_by_symbol:
                hebel_pruefung_text = "An" if hebel_pruefung_erlaubt_by_symbol[asset.symbol] else "Aus"
                oi_eintrag = oi_abdeckung_status.get(asset.symbol)
                if oi_eintrag and oi_eintrag.get("konsekutive_fehlschlaege", 0) >= oi_schwelle:
                    hebel_pruefung_text += " ⚠"
            else:
                hebel_pruefung_text = "-"

            if asset.symbol in gehaltene_symbole or asset.symbol in offene_hebel_symbole:
                status_text = "Gehalten"
            else:
                status_text = asset.beobachtungsstatus

            # 2026-07-19, Konsistenz-Check Watchlist-Tab (Nutzer-Wunsch): ein
            # Krypto-Asset ohne coingecko_id (z.B. automatisch aus einer
            # Hebel-Position ergaenzt, siehe importer/bitpanda_margin_
            # positions.py::auto_add_unknown_hebel_symbols()) bekommt bei
            # select_assets_due_for_signal() als "nie berechnet" IMMER die
            # hoechste Prioritaet, kann aber generate_signal() strukturell nie
            # erfolgreich durchlaufen (keine Kurshistorie ohne ID) - ohne
            # sichtbaren Hinweis wuerde das dauerhaft, unbemerkt einen
            # Spot-Budget-Slot pro Allocator-Lauf verschwenden. Jetzt zusaetzlich
            # in signal_batch.py aus der Kandidatenauswahl ausgeschlossen -
            # diese Markierung bleibt trotzdem, damit der Nutzer den fehlenden
            # Eintrag findet und ergaenzt (Spot-Analyse ist bis dahin inaktiv).
            coingecko_id_fehlt = (
                asset.assetklasse == "krypto" and not asset.ist_cash_aequivalent and not asset.coingecko_id
            )
            if coingecko_id_fehlt:
                status_text += " ⚠ keine CoinGecko-ID"
                tags.append("externe_id_fehlt")

            # 2026-07-19, Konsistenz-Check ueber alle Assetklassen (Nutzer-
            # Wunsch, gleiches Muster wie oben): Aktien UND Themen-ETFs
            # brauchen asset.yfinance_symbol fuer generate_signal() - ohne ID
            # kam es bisher sogar zu einem rohen Absturz (yf.Ticker(None), live
            # bestaetigt und in agent/aktien/pipeline.py behoben) statt nur
            # verschwendeter Budget-Slots. Rohstoffe (hartkodierter Futures-
            # Ticker) und Hedge-Instrumente (kein OHLC noetig) sind NICHT
            # betroffen, siehe agent/multi_asset_batch.py::_kandidaten().
            from agent.hedge.pipeline import SYMBOL_ZU_HEBEL_FAKTOR as _hedge_symbole

            yfinance_symbol_fehlt = (
                asset.symbol not in _hedge_symbole
                and (asset.assetklasse == "aktien" or asset.assetklasse == "etf")
                and not asset.yfinance_symbol
            )
            if yfinance_symbol_fehlt:
                status_text += " ⚠ kein yfinance-Symbol"
                tags.append("externe_id_fehlt")

            schwerpunkt_text = config_module.get_kategorie_name(asset.hauptgruppe, asset.unterkategorie) or "-"
            if these is not None:
                marker = _THESE_MARKER_UND_TAG.get(these.richtung, ("●", "these_neutral"))[0]
                schwerpunkt_text = f"{schwerpunkt_text} {marker}"

            tree.insert(
                "",
                "end",
                iid=asset.symbol,
                values=(
                    asset.symbol,
                    asset.name,
                    asset.rolle,
                    asset.assetklasse,
                    schwerpunkt_text,
                    status_text,
                    bitpanda_text,
                    tranchen_text,
                    hebel_pruefung_text,
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
        text = ""
        these = self._these_by_symbol.get(symbol)
        if these is not None:
            # Stufe-1-Hervorhebung (2026-07-20, Task #343, Transparenz-Prinzip):
            # erklaert konkret, WARUM diese Zeile markiert/bevorzugt einsortiert
            # wurde - siehe _THESE_MARKER_UND_TAG.
            import config as config_module

            kategorie_name = (
                config_module.get_kategorie_name(these.hauptgruppe, these.unterkategorie)
                or config_module.get_hauptgruppe_name(these.hauptgruppe)
            )
            richtung_label = {"uebergewichten": "Übergewichten", "meiden": "Meiden", "neutral": "Neutral",
                               "aktiv": "Aktiv", "inaktiv": "Inaktiv"}.get(these.richtung, these.richtung)
            text = f"Aktive These ({kategorie_name}, {richtung_label}): {these.begruendung}"

        conn = self._db_conn_factory()
        try:
            signal = db.get_latest_signal(conn, symbol)
        finally:
            conn.close()
        if signal is None:
            return text or "Noch keine Analyse berechnet."
        when = signal.created_at[:16].replace("T", " ") if signal.created_at else "-"
        conf = f"{signal.confidence_pct:.0f}%" if signal.confidence_pct is not None else "-"
        if text:
            text += "\n\n"
        text += f"Letztes Signal: {signal.action} ({when}, Konfidenz {conf})"
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

    def _open_asset_quality_dialog(self) -> None:
        """2026-07-19, Nutzer-Wunsch: Fonds-Zusammensetzung/-Kennzahlen fuer ein
        Watchlist-Asset anzeigen (siehe api/asset_quality.py). Nur fuer Assets
        mit `yfinance_symbol` sinnvoll - bei Krypto/Bitpanda-eigenen ETC-
        Basketprodukten (kein echter Ticker) meldet der Dialog das klar statt
        eine leere Tabelle zu zeigen."""
        tree = self._watchlist_frame.tree
        selected = tree.selection()
        if not selected:
            messagebox.showinfo("Zusammensetzung anzeigen", "Bitte zuerst eine Zeile in der Watchlist auswählen.")
            return
        symbol = tree.item(selected[0], "values")[0]
        asset = next((a for a in self._watchlist if a.symbol == symbol), None)
        if asset is None:
            return
        if not asset.yfinance_symbol:
            messagebox.showinfo(
                "Zusammensetzung anzeigen",
                f"{symbol} hat kein hinterlegtes yfinance-Symbol - Zusammensetzungsdaten "
                "sind nur für Assets mit echtem Börsenticker verfügbar (nicht für Krypto "
                "oder Bitpanda-eigene Themenkorb-Produkte).",
            )
            return
        AssetQualityDialog(self, asset)

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
        self._regime_view.refresh()
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
        nicht, Spalte zeigt dann "?" statt eines falschen Werts.

        Non-Crypto-Katalog (2026-07-18-Fix) separat mitgeladen - die Watchlist-
        Spalte zeigte fuer Aktien/ETF/Rohstoffe bisher hartkodiert "-", obwohl
        agent/aktien/pipeline.py und agent/rohstoff/pipeline.py den echten
        Bitpanda-Listing-Status laengst berechnen (seit 2026-07-16, siehe
        api/bitpanda.py::get_listed_non_crypto_assets()) - Nachzieh-Luecke, siehe
        Regelwerksmanual."""
        from api.bitpanda import get_listed_assets, get_listed_non_crypto_assets

        try:
            self._bitpanda_assets = get_listed_assets()
        except Exception:
            self._bitpanda_assets = None

        try:
            self._bitpanda_non_crypto_assets = get_listed_non_crypto_assets()
        except Exception:
            self._bitpanda_non_crypto_assets = None

    def _toggle_dca_erlaubt(self) -> None:
        """AZ-4-Tranchen-Toggle (2026-07-12, 2026-07-18 um SOL erweitert) - nur
        fuer BTC/ETH/SOL sinnvoll (siehe agent/krypto/pipeline.py::
        generate_signal()), operiert auf der aktuell in der Watchlist
        ausgewaehlten Zeile."""
        tree = self._watchlist_frame.tree
        selected = tree.selection()
        if not selected:
            messagebox.showinfo(
                "Tranchen-Vorschläge umschalten", "Bitte zuerst BTC, ETH oder SOL in der Watchlist auswählen."
            )
            return
        symbol = tree.item(selected[0], "values")[0]
        if symbol not in ("BTC", "ETH", "SOL"):
            messagebox.showinfo(
                "Tranchen-Vorschläge umschalten",
                "AZ-4-Tranchen sind aktuell nur für BTC, ETH und SOL vorgesehen.",
            )
            return

        conn = self._db_conn_factory()
        try:
            neuer_wert = not db.get_dca_erlaubt(conn, symbol)
            db.set_dca_erlaubt(conn, symbol, neuer_wert)
        finally:
            conn.close()

        self._refresh_watchlist_from_db()

    def _toggle_hebel_pruefung_erlaubt(self) -> None:
        """Hebel-Pruefung-Toggle (2026-07-18, Budget/Asset-Optimierung) - fuer
        alle Krypto-Assets verfuegbar (anders als der Tranchen-Toggle oben),
        operiert auf der aktuell in der Watchlist ausgewaehlten Zeile. Betrifft
        NUR die Neuentdeckung neuer Hebel-Trigger (agent/krypto/
        hebel_screening.py) - bereits offene Hebel-Positionen bleiben
        unabhaengig vom Toggle weiter risikoueberwacht."""
        tree = self._watchlist_frame.tree
        selected = tree.selection()
        if not selected:
            messagebox.showinfo(
                "Hebel-Prüfung umschalten", "Bitte zuerst ein Krypto-Asset in der Watchlist auswählen."
            )
            return
        symbol = tree.item(selected[0], "values")[0]
        asset = next((a for a in self._watchlist if a.symbol == symbol), None)
        if asset is None or asset.assetklasse != "krypto" or asset.ist_cash_aequivalent:
            messagebox.showinfo(
                "Hebel-Prüfung umschalten",
                "Die Hebel-Prüfung ist nur für Krypto-Assets (ohne Stablecoins) vorgesehen.",
            )
            return

        conn = self._db_conn_factory()
        try:
            neuer_wert = not db.get_hebel_pruefung_erlaubt(conn, symbol)
            db.set_hebel_pruefung_erlaubt(conn, symbol, neuer_wert)
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

        # 2026-07-18 (Multi-Asset-Vollstaendigkeitspruefung): "etf" deckt ZWEI
        # verschiedene Pipelines ab, unterschieden nur per Symbol-Zugehoerigkeit
        # zu agent.hedge.pipeline.SYMBOL_ZU_HEBEL_FAKTOR (kein eigenes Dropdown-
        # Feld dafuer) - ein neu hinzugefuegtes Hedge-Instrument wuerde sonst
        # STILLSCHWEIGEND als Themen-ETF behandelt (falsche Sektor-Rotations-
        # Logik statt Portfolio-Absicherungslogik), bis ein Entwickler es dort
        # manuell eintraegt (hebel_faktor/referenz_index sind ohnehin
        # hartkodiert, das laesst sich nicht per UI abbilden).
        if assetklasse == "etf":
            from agent.hedge.pipeline import SYMBOL_ZU_HEBEL_FAKTOR as _hedge_symbole
            if symbol not in _hedge_symbole:
                warnungen.append(
                    f"'{symbol}' wird als Themen-/Sektor-ETF behandelt (agent/themen_etf/). "
                    "Falls stattdessen ein neues Portfolio-Hedge-Instrument gemeint ist: dafür "
                    "muss zusätzlich SYMBOL_ZU_HEBEL_FAKTOR in agent/hedge/pipeline.py per Code "
                    "ergänzt werden (hebel_faktor/Referenzindex lassen sich nicht per UI eintragen)."
                )

    return warnungen


_KEIN_SCHWERPUNKT = "(kein Schwerpunkt)"


def _build_kategorie_selector(frame, row: int, initial_hauptgruppe: str | None = None, initial_unterkategorie: str | None = None):
    """Baut zwei kaskadierende Comboboxen (Hauptgruppe -> Unterkategorie, je 1
    Zeile im `frame`-Grid ab `row`) fuer die strukturierte Kategorie-Zuordnung
    (2026-07-19, ersetzt das anfaengliche Freitext-Schwerpunkt-Feld NOCH AM
    SELBEN TAG - siehe config.py::WatchlistAsset-Docstring: Freitext war fuer
    automatische Prozesse/Kategorie-Gruppierung nicht zuverlaessig genug).
    Gemeinsam genutzt von `AssetAddDialog`/`AssetEditDialog`. Gibt eine
    `get_ids()`-Funktion zurueck, die `(hauptgruppe_id, unterkategorie_id)`
    oder `(None, None)` liefert (Feld ist optional, "(kein Schwerpunkt)" bleibt
    immer die erste Combobox-Option)."""
    import config as config_module

    kategorien = config_module.get_kategorien()
    hauptgruppen = kategorien["hauptgruppen"]
    hg_name_to_id = {hg["name"]: hg["id"] for hg in hauptgruppen}
    hg_id_to_obj = {hg["id"]: hg for hg in hauptgruppen}

    hauptgruppe_var = tk.StringVar()
    unterkategorie_var = tk.StringVar()

    ttk.Label(frame, text="Hauptgruppe").grid(row=row, column=0, sticky="w", pady=2)
    hg_combo = ttk.Combobox(
        frame, textvariable=hauptgruppe_var, state="readonly", width=25,
        values=[_KEIN_SCHWERPUNKT] + [hg["name"] for hg in hauptgruppen],
    )
    hg_combo.grid(row=row, column=1, sticky="w", pady=2, padx=(8, 0))

    ttk.Label(frame, text="Unterkategorie").grid(row=row + 1, column=0, sticky="w", pady=2)
    uk_combo = ttk.Combobox(frame, textvariable=unterkategorie_var, state="readonly", width=25, values=[])
    uk_combo.grid(row=row + 1, column=1, sticky="w", pady=2, padx=(8, 0))

    def _on_hauptgruppe_changed(event=None) -> None:
        hg_name = hauptgruppe_var.get()
        if hg_name == _KEIN_SCHWERPUNKT or not hg_name:
            uk_combo.config(values=[])
            unterkategorie_var.set("")
            return
        hg_obj = hg_id_to_obj.get(hg_name_to_id.get(hg_name))
        uk_names = [uk["name"] for uk in hg_obj["unterkategorien"]] if hg_obj else []
        uk_combo.config(values=uk_names)
        if unterkategorie_var.get() not in uk_names:
            unterkategorie_var.set(uk_names[0] if uk_names else "")

    hg_combo.bind("<<ComboboxSelected>>", _on_hauptgruppe_changed)

    # Vorbelegung (Bearbeiten-Dialog) - unbekannte/veraltete IDs (z.B. falls
    # kategorien.yaml sich seither geaendert hat) degradieren still auf
    # "kein Schwerpunkt" statt eines Absturzes (P-10).
    hg_obj = hg_id_to_obj.get(initial_hauptgruppe) if initial_hauptgruppe else None
    if hg_obj is not None:
        hauptgruppe_var.set(hg_obj["name"])
        _on_hauptgruppe_changed()
        uk_obj = next((uk for uk in hg_obj["unterkategorien"] if uk["id"] == initial_unterkategorie), None)
        if uk_obj is not None:
            unterkategorie_var.set(uk_obj["name"])
    if not hauptgruppe_var.get():
        hauptgruppe_var.set(_KEIN_SCHWERPUNKT)

    def get_ids() -> tuple[str | None, str | None]:
        hg_name = hauptgruppe_var.get()
        if hg_name == _KEIN_SCHWERPUNKT or not hg_name:
            return None, None
        hg_id = hg_name_to_id.get(hg_name)
        hg_obj = hg_id_to_obj.get(hg_id)
        uk_obj = next((uk for uk in hg_obj["unterkategorien"] if uk["name"] == unterkategorie_var.get()), None) if hg_obj else None
        if hg_id is None or uk_obj is None:
            return None, None
        return hg_id, uk_obj["id"]

    return get_ids


def _try_auto_resolve_coingecko_id(symbol: str, coingecko_client) -> str | None:
    """Automatische `coingecko_id`-Aufloesung via Bitpanda-Namensabgleich
    (2026-07-19, Nutzer-Vorschlag: "in dieser Schleife sollte das Symbol
    schon eindeutig sein, sonst gibt's da schon Inkonsistenzen") - gemeinsam
    genutzt von `AssetAddDialog` (interaktiv, mit automatischem
    `CoinSearchDialog`-Rueckfall bei Fehlschlag) und `AssetEditDialog`
    (still, kein Dialog-Popup beim blossen Oeffnen). Prueft zuerst, ob das
    Symbol ueberhaupt bei Bitpanda gelistet ist (liefert dabei Bitpandas
    eigenen, kuratierten Namen), sucht dann per CoinGecko `/search` und
    verlangt EXAKT EINE Namensuebereinstimmung (siehe api/coingecko.py::
    resolve_coingecko_id_by_name()-Docstring fuer die Begruendung/live-
    Verifikation). Gibt None zurueck bei fehlendem Bitpanda-Listing, echter
    Mehrdeutigkeit ODER einem Netzwerkfehler - niemals eine geratene ID."""
    try:
        from api.bitpanda import find_listed_asset, get_listed_assets
        from api.coingecko import resolve_coingecko_id_by_name

        listed_assets = get_listed_assets()
        bitpanda_asset = find_listed_asset(symbol, listed_assets)
        if bitpanda_asset is None:
            return None
        results = coingecko_client.search_coins(symbol)
        return resolve_coingecko_id_by_name(results, bitpanda_asset.name)
    except Exception as exc:
        logging.getLogger(__name__).info("Automatische CoinGecko-ID-Aufloesung fuer %s fehlgeschlagen: %s", symbol, exc)
        return None


class CoinSearchDialog(tk.Toplevel):
    """CoinGecko-Symbolsuche (2026-07-19, Watchlist-Tab-Konsistenzpruefung -
    Nutzer-Nachfrage "das solltest du doch automatisch ergaenzen koennen").
    Bewusst KEINE automatische Auswahl: ein Symbol wie "SOL" hat bei CoinGecko
    12 verschiedene IDs (echtes Solana + gebrueckte/gewrappte Varianten), live
    verifiziert - eine stille automatische Wahl haette das Risiko, dauerhaft
    die falsche Coin-Historie zu laden. Stattdessen zeigt dieser Dialog alle
    Treffer (exakte Symbol-Treffer zuerst, sortiert nach Marktkap.-Rang -
    siehe api/coingecko.py::CoinGeckoClient.search_coins()), der Nutzer
    bestaetigt die Auswahl selbst per Doppelklick oder Button."""

    def __init__(self, parent, coingecko_client, initial_query: str, on_selected) -> None:
        super().__init__(parent)
        self._coingecko_client = coingecko_client
        self._on_selected = on_selected
        self.title("CoinGecko-ID suchen")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        frame = ttk.Frame(self, padding=12)
        frame.pack(fill="both", expand=True)

        search_row = ttk.Frame(frame)
        search_row.pack(fill="x")
        self._query_var = tk.StringVar(value=initial_query)
        ttk.Entry(search_row, textvariable=self._query_var, width=22).pack(side="left")
        ttk.Button(search_row, text="Suchen", command=self._on_search).pack(side="left", padx=(6, 0))

        self._status_label = ttk.Label(frame, text="", foreground=theme.info_color())
        self._status_label.pack(anchor="w", pady=(4, 4))

        columns = ("symbol", "name", "coingecko_id", "rang")
        self._tree = ttk.Treeview(frame, columns=columns, show="headings", height=10, selectmode="browse")
        headings = {"symbol": "Symbol", "name": "Name", "coingecko_id": "CoinGecko-ID", "rang": "Marktkap.-Rang"}
        widths = {"symbol": 70, "name": 160, "coingecko_id": 180, "rang": 90}
        for col in columns:
            self._tree.heading(col, text=headings[col])
            self._tree.column(col, width=widths[col], anchor="w")
        self._tree.pack(fill="both", expand=True)
        self._tree.bind("<Double-1>", lambda _event: self._on_confirm())

        button_frame = ttk.Frame(frame)
        button_frame.pack(fill="x", pady=(10, 0))
        ttk.Button(button_frame, text="Abbrechen", command=self.destroy).pack(side="right", padx=(6, 0))
        ttk.Button(button_frame, text="Übernehmen", command=self._on_confirm).pack(side="right")

        if initial_query.strip():
            self._on_search()

    def _on_search(self) -> None:
        query = self._query_var.get().strip()
        if not query:
            return
        for item in self._tree.get_children():
            self._tree.delete(item)
        self._status_label.config(text="Suche läuft …", foreground=theme.info_color())
        self.update_idletasks()
        try:
            results = self._coingecko_client.search_coins(query)
        except Exception as exc:
            self._status_label.config(text=f"Suche fehlgeschlagen: {exc}", foreground=theme.danger_color())
            return
        if not results:
            self._status_label.config(text="Keine Treffer.", foreground=theme.stale_color())
            return
        query_upper = query.upper()
        for r in results:
            rang_text = str(r.market_cap_rank) if r.market_cap_rank is not None else "-"
            markierung = " (exakt)" if r.symbol == query_upper else ""
            self._tree.insert(
                "", "end", iid=r.coingecko_id,
                values=(r.symbol, r.name + markierung, r.coingecko_id, rang_text),
            )
        self._status_label.config(
            text=f"{len(results)} Treffer - exakte Symbol-Treffer zuerst, sortiert nach Marktkap.-Rang.",
            foreground=theme.info_color(),
        )

    def _on_confirm(self) -> None:
        selected = self._tree.selection()
        if not selected:
            messagebox.showinfo("CoinGecko-ID suchen", "Bitte zuerst einen Treffer auswählen.")
            return
        coingecko_id = selected[0]
        self.destroy()
        self._on_selected(coingecko_id)


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
                if var is self._coingecko_id_var:
                    # 2026-07-19, Watchlist-Tab-Konsistenzpruefung: Symbol ist
                    # bei CoinGecko nicht eindeutig (siehe CoinSearchDialog-
                    # Docstring) - Suchen statt Freihandeintrag raten muessen.
                    ttk.Button(frame, text="Suchen …", command=self._on_search_coingecko_id).grid(
                        row=row, column=2, sticky="w", pady=2, padx=(6, 0)
                    )

        # Kategorie-Auswahl (2026-07-19, ersetzt das anfaengliche Freitext-
        # Schwerpunkt-Feld noch am selben Tag - siehe config.py::WatchlistAsset-
        # Docstring): zwei kaskadierende Comboboxen statt Freihandeintrag, damit
        # die Werte fuer Diversifikations-Uebersicht/Marktscan-Bias zuverlaessig
        # gruppierbar bleiben.
        self._get_kategorie_ids = _build_kategorie_selector(frame, row=len(fields))

        button_frame = ttk.Frame(frame)
        button_frame.grid(row=len(fields) + 2, column=0, columnspan=3, sticky="e", pady=(10, 0))
        ttk.Button(button_frame, text="Abbrechen", command=self.destroy).pack(side="right", padx=(6, 0))
        ttk.Button(button_frame, text="Hinzufügen", command=self._on_submit).pack(side="right")

    def _on_search_coingecko_id(self) -> None:
        query = self._symbol_var.get().strip()
        CoinSearchDialog(
            self, self._parent_app._coingecko_client, query,
            on_selected=lambda cid: self._coingecko_id_var.set(cid),
        )

    def _on_submit(self) -> None:
        import config as config_module

        symbol = self._symbol_var.get().strip().upper()
        name = self._name_var.get().strip()
        assetklasse = self._assetklasse_var.get()
        coingecko_id = self._coingecko_id_var.get().strip() or None
        yfinance_symbol = self._yfinance_symbol_var.get().strip() or None
        hauptgruppe, unterkategorie = self._get_kategorie_ids()

        if not symbol or not name:
            messagebox.showwarning("Asset hinzufügen", "Symbol und Name sind Pflichtfelder.")
            return

        if assetklasse == "krypto" and not coingecko_id:
            # 2026-07-19, Nutzer-Vorschlag: der Dialog soll gleich bei der
            # Aufnahme in die Watchlist kommen, nicht erst auf manuellen
            # "Suchen"-Klick warten. Erst still per Bitpanda-Namensabgleich
            # versuchen (siehe _try_auto_resolve_coingecko_id()-Docstring) -
            # schlaegt das fehl (nicht bei Bitpanda gelistet ODER echte
            # Mehrdeutigkeit), automatisch CoinSearchDialog OEFFNEN statt
            # einen Klick vom Nutzer zu verlangen. Abbrechen im Dialog laesst
            # das Feld leer, identisch zum bisherigen Standardverhalten.
            coingecko_id = _try_auto_resolve_coingecko_id(symbol, self._parent_app._coingecko_client)
            if coingecko_id:
                self._coingecko_id_var.set(coingecko_id)
            else:
                picked: list[str] = []
                dialog = CoinSearchDialog(
                    self, self._parent_app._coingecko_client, symbol,
                    on_selected=lambda cid: picked.append(cid),
                )
                self.wait_window(dialog)
                if picked:
                    coingecko_id = picked[0]
                    self._coingecko_id_var.set(coingecko_id)

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
                hauptgruppe=hauptgruppe, unterkategorie=unterkategorie,
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
    core/taktisch umzustellen. Symbol/Name bleiben unveraendert (Symbol-
    Umbenennung o.ae. ist ein anderer, hier nicht abgedeckter Vorgang).

    2026-07-19 (Watchlist-Tab-Konsistenzpruefung) um `coingecko_id` erweitert
    - vorher gab es fuer ein BEREITS bestehendes Krypto-Asset ohne ID (z.B.
    automatisch aus einer Hebel-Position ergaenzt, siehe importer/
    bitpanda_margin_positions.py::auto_add_unknown_hebel_symbols()) gar
    keinen GUI-Weg, sie nachzutragen - nur beim Erst-Anlegen ueber
    AssetAddDialog. Nur fuer assetklasse=krypto sichtbar (Aktien/ETF/
    Rohstoffe haben kein CoinGecko-Pendant)."""

    def __init__(self, parent, asset, on_edited=None) -> None:
        super().__init__(parent)
        self._parent_app = parent
        self._asset = asset
        self._on_edited = on_edited
        self.title(f"Asset bearbeiten: {asset.symbol}")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        frame = ttk.Frame(self, padding=12)
        frame.pack(fill="both", expand=True)

        ttk.Label(frame, text=f"{asset.symbol} — {asset.name}", font=("", 10, "bold")).grid(
            row=0, column=0, columnspan=3, sticky="w", pady=(0, 8)
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
        ).grid(row=3, column=0, columnspan=3, sticky="w", pady=(0, 8))

        # Kategorie-Auswahl (2026-07-19, ersetzt das anfaengliche Freitext-
        # Schwerpunkt-Feld noch am selben Tag, siehe _build_kategorie_selector()
        # Docstring) - zwei kaskadierende Comboboxen, vorbelegt mit der
        # aktuellen Zuordnung des Assets.
        self._get_kategorie_ids = _build_kategorie_selector(
            frame, row=4, initial_hauptgruppe=asset.hauptgruppe, initial_unterkategorie=asset.unterkategorie,
        )
        ttk.Label(
            frame, text="(Basis für den Diversifikations-Überblick im Portfolio-Tab)",
            wraplength=280, foreground=theme.info_color(),
        ).grid(row=6, column=0, columnspan=3, sticky="w", pady=(0, 8))

        next_row = 7
        auto_resolved_id = asset.coingecko_id
        if asset.assetklasse == "krypto" and not asset.ist_cash_aequivalent and not asset.coingecko_id:
            # 2026-07-19, Nutzer-Vorschlag: still versuchen, BEVOR das Feld
            # angezeigt wird - genau der Fall, der diese Erweiterung
            # ausgeloest hat (z.B. automatisch aus einer Hebel-Position
            # ergaenztes Symbol ohne ID). Kein Dialog-Popup beim blossen
            # Oeffnen dieses Dialogs (der Nutzer koennte hier auch nur
            # rolle/beobachtungsstatus aendern wollen) - nur bei tatsaechlichem
            # Speichern-Klick mit weiterhin leerem Feld greift die manuelle
            # "Suchen"-Option.
            auto_resolved_id = _try_auto_resolve_coingecko_id(asset.symbol, parent._coingecko_client)
        self._coingecko_id_var = tk.StringVar(value=auto_resolved_id or "")
        if asset.assetklasse == "krypto" and not asset.ist_cash_aequivalent:
            ttk.Label(frame, text="CoinGecko-ID").grid(row=next_row, column=0, sticky="w", pady=2)
            ttk.Entry(frame, textvariable=self._coingecko_id_var, width=25).grid(
                row=next_row, column=1, sticky="w", pady=2, padx=(8, 0)
            )
            ttk.Button(frame, text="Suchen …", command=self._on_search_coingecko_id).grid(
                row=next_row, column=2, sticky="w", pady=2, padx=(6, 0)
            )
            next_row += 1
            if not auto_resolved_id:
                ttk.Label(
                    frame, text="⚠ ohne ID keine Spot-Analyse für dieses Asset möglich",
                    wraplength=280, foreground=theme.danger_color(),
                ).grid(row=next_row, column=0, columnspan=3, sticky="w", pady=(0, 8))
                next_row += 1

        button_frame = ttk.Frame(frame)
        button_frame.grid(row=next_row, column=0, columnspan=3, sticky="e", pady=(10, 0))
        ttk.Button(button_frame, text="Abbrechen", command=self.destroy).pack(side="right", padx=(6, 0))
        ttk.Button(button_frame, text="Speichern", command=self._on_submit).pack(side="right")

    def _on_search_coingecko_id(self) -> None:
        CoinSearchDialog(
            self, self._parent_app._coingecko_client, self._asset.symbol,
            on_selected=lambda cid: self._coingecko_id_var.set(cid),
        )

    def _on_submit(self) -> None:
        import config as config_module

        try:
            config_module.update_watchlist_rolle(self._asset.symbol, self._rolle_var.get())
            config_module.update_watchlist_beobachtungsstatus(self._asset.symbol, self._beobachtungsstatus_var.get())
            new_hauptgruppe, new_unterkategorie = self._get_kategorie_ids()
            if new_hauptgruppe and new_unterkategorie and (
                new_hauptgruppe != self._asset.hauptgruppe or new_unterkategorie != self._asset.unterkategorie
            ):
                config_module.update_watchlist_kategorie(self._asset.symbol, new_hauptgruppe, new_unterkategorie)
            new_coingecko_id = self._coingecko_id_var.get().strip()
            if new_coingecko_id and new_coingecko_id != (self._asset.coingecko_id or ""):
                config_module.update_watchlist_coingecko_id(self._asset.symbol, new_coingecko_id)
        except config_module.WatchlistWriteError as exc:
            messagebox.showerror("Asset bearbeiten", f"Fehlgeschlagen: {exc}")
            return

        self.destroy()
        if self._on_edited:
            self._on_edited()


class AssetQualityDialog(tk.Toplevel):
    """Zeigt Fonds-Zusammensetzung/-Kennzahlen fuer ein Watchlist-Asset an
    (2026-07-19, Nutzer-Wunsch: "wie setzt sich zusammen" - siehe
    api/asset_quality.py::get_asset_quality()). Laedt im Hintergrund-Thread
    (Netzwerk-Aufruf, gleiches Muster wie ui/marktscan_view.py/ui/screener_view.py
    - synchron im Tk-Main-Thread wuerde die UI einfrieren)."""

    def __init__(self, parent, asset) -> None:
        super().__init__(parent)
        self._asset = asset
        self.title(f"Zusammensetzung — {asset.symbol}")
        self.geometry("520x460")
        self.transient(parent)
        self.grab_set()

        frame = ttk.Frame(self, padding=12)
        frame.pack(fill="both", expand=True)

        ttk.Label(frame, text=f"{asset.symbol} — {asset.name}", font=("", 11, "bold")).pack(anchor="w")
        ttk.Label(frame, text=f"yfinance-Ticker: {asset.yfinance_symbol}", foreground=theme.info_color()).pack(
            anchor="w", pady=(0, 8)
        )

        self.status_label = ttk.Label(frame, text="Lade Daten …", foreground=theme.info_color())
        self.status_label.pack(anchor="w")

        self.meta_label = ttk.Label(frame, text="", justify="left")
        self.meta_label.pack(anchor="w", pady=(4, 8))

        ttk.Label(frame, text="Top-Holdings", font=("", 10, "bold")).pack(anchor="w")
        self.holdings_text = tk.Text(frame, height=10, wrap="word", state="disabled", relief="flat")
        self.holdings_text.pack(fill="both", expand=True, pady=(2, 8))

        ttk.Label(frame, text="Sektor-Gewichtung", font=("", 10, "bold")).pack(anchor="w")
        self.sektor_text = tk.Text(frame, height=6, wrap="word", state="disabled", relief="flat")
        self.sektor_text.pack(fill="both", expand=True, pady=(2, 8))

        ttk.Button(frame, text="Schließen", command=self.destroy).pack(anchor="e")

        thread = threading.Thread(target=self._load, daemon=True)
        thread.start()

    def _load(self) -> None:
        from api.asset_quality import get_asset_quality

        try:
            result = get_asset_quality(self._asset.yfinance_symbol)
            error = None
        except Exception as exc:  # noqa: BLE001 - an die UI durchreichen statt den Thread stumm sterben zu lassen
            result = None
            error = exc
        self.after(0, self._on_loaded, result, error)

    def _set_text(self, widget: tk.Text, content: str) -> None:
        widget.config(state="normal")
        widget.delete("1.0", "end")
        widget.insert("1.0", content)
        widget.config(state="disabled")

    def _on_loaded(self, result, error) -> None:
        if error is not None:
            self.status_label.config(text=f"Abruf fehlgeschlagen: {error}", foreground=theme.danger_color())
            return
        if result is None:
            self.status_label.config(
                text="Keine Daten gefunden (unbekannter Ticker oder Netzwerkfehler).",
                foreground=theme.danger_color(),
            )
            return

        self.status_label.config(text=f"Typ: {result.quote_type or 'unbekannt'}", foreground=theme.info_color())

        if result.quote_type == "EQUITY":
            self.meta_label.config(text="Einzelaktie - keine Fonds-Kennzahlen (AUM/Kostenquote/Holdings) vorhanden.")
            self._set_text(self.holdings_text, "(nicht zutreffend für Einzelaktien)")
            self._set_text(self.sektor_text, "(nicht zutreffend für Einzelaktien)")
            return

        meta_lines = []
        if result.fund_family:
            meta_lines.append(f"Anbieter: {result.fund_family}")
        if result.aum_usd is not None:
            meta_lines.append(f"Fondsvolumen (AUM): {result.aum_usd:,.0f} USD")
        else:
            meta_lines.append("Fondsvolumen (AUM): nicht verfügbar")
        if result.expense_ratio_pct is not None:
            meta_lines.append(f"Kostenquote (TER): {result.expense_ratio_pct:.2f}%")
        else:
            meta_lines.append("Kostenquote (TER): nicht verfügbar")
        self.meta_label.config(text="\n".join(meta_lines))

        if result.top_holdings:
            holdings_text = "\n".join(f"{pct:5.2f}%  {name}" for name, pct in result.top_holdings)
        else:
            holdings_text = "(keine Holdings-Daten verfügbar)"
        self._set_text(self.holdings_text, holdings_text)

        if result.sektor_gewichtung:
            sektor_text = "\n".join(
                f"{pct:5.2f}%  {sektor}"
                for sektor, pct in sorted(result.sektor_gewichtung.items(), key=lambda kv: kv[1], reverse=True)
            )
        else:
            sektor_text = "(keine Sektor-Daten verfügbar)"
        self._set_text(self.sektor_text, sektor_text)


def run_app(
    db_conn_factory, watchlist, coingecko_client, kraken_client=None, groq_client=None,
    gemini_client=None, fred_api_key=None, bitpanda_api_key=None,
    mistral_client=None,
) -> None:
    app = TradingInfoToolApp(
        db_conn_factory, watchlist, coingecko_client, kraken_client, groq_client,
        gemini_client=gemini_client, fred_api_key=fred_api_key,
        bitpanda_api_key=bitpanda_api_key, mistral_client=mistral_client,
    )
    app.mainloop()
