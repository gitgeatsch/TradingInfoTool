"""Aktien/ETF-Screener-Tab (2026-07-19, Nutzer-Wunsch "einen einfachen Aktien/ETF-
Screener... analog Marktscan"). Bewusst EINFACHER als `ui/marktscan_view.py`: kein
Score/keine Einstufung, keine automatische LLM-Begründung, keine DB-Persistenz -
ein Scan liefert eine frische Kandidatenliste (siehe `agent/aktien/screener.py`
fuer die Quellen), die der Nutzer direkt per "In Watchlist übernehmen"
(identisches Muster wie Marktscan, `config.py::add_watchlist_entry()`)
uebernehmen kann. Die eigentliche Bewertung passiert danach ganz regulär über
`agent/multi_asset_batch.py` - kein Doppelbau.

Threading-Muster identisch zu `ui/marktscan_view.py`: der Scan braucht mehrere
Netzwerk-Aufrufe (yfinance-Screens + Bitpanda-Assetliste) - synchron im
Tk-Main-Thread würde die UI einfrieren.

Auto-Scan (2026-07-20, Nutzer-Wunsch "Auto-Screen beim Start bzw. regelmaessige
Updates"): ein GUI-lokaler, selbstverlaengernder `self.after()`-Timer (Muster
wie `ui/app.py::_poll_prices()`), KEIN Scheduler-Job - der Screener persistiert
bewusst nichts in die DB (siehe oben), ein Scheduler-Job haette dafuer eine neue
Tabelle gebraucht, nur damit die GUI sie wieder ausliest. Intervall in
`Basisinfos/config.yaml::screener.auto_scan_intervall_minuten` (Default 60) -
bewusst nicht kuerzer, siehe dortiger Kommentar."""
from __future__ import annotations

import threading
import tkinter as tk
from tkinter import messagebox, ttk

import agent.kategorie_thesen as kategorie_thesen
import config as config_module
import database.db as db
import ui.theme as theme
from ui.formatting import format_money
from ui.heading_tooltip import add_heading_tooltips
from ui.row_tooltip import add_row_tooltips
from ui.sortable_tree import make_sortable
from ui.widget_tooltip import add_widget_tooltip

_SCREENER_COLUMN_DESCRIPTIONS = {
    "symbol": "Symbol/Ticker des Kandidaten.",
    "name": "Name des Unternehmens/Produkts.",
    "assetklasse": "Aktien (yfinance-Screener) oder ETF/ETC (direkt aus Bitpandas eigenem Katalog).",
    "quelle": "Herkunft: Yahoo-Finance-Screen-Name oder 'bitpanda_katalog'.",
    "preis": (
        "Aktueller Preis in USD (nur Aktien - Bitpandas eigener ETF/ETC-Katalog liefert "
        "strukturell keine Preise, live gegenprüft: weder öffentlich noch mit API-Key. "
        "Grund per Mouseover auf die Zeile."
    ),
    "marktkap": "Marktkapitalisierung in USD (nur Aktien).",
    "aenderung": "Tagesänderung in % (nur Aktien).",
    "bitpanda": "Ob der Kandidat bei Bitpanda tatsächlich kaufbar ist (✓/✗) - bei ETF/ETC immer ✓, da direkt aus Bitpandas Katalog stammend.",
    "kategorie": (
        "Hauptgruppe/Unterkategorie aus Basisinfos/kategorien.yaml (nur ETF/ETC, "
        "automatisch anhand des Bitpanda-Symbols zugeordnet; '-' bei Aktien-Kandidaten, "
        "Grund per Mouseover auf die Zeile). ▲/▼/● = aktive These im Schwerpunkte-Tab "
        "(▲ Übergewichten/Aktiv, ▼ Meiden, ● Neutral) - solche Kandidaten stehen "
        "zusätzlich weiter oben in der Liste, Begründung ebenfalls per Mouseover."
    ),
}

_ERKLAERUNG_BITPANDA_KATALOG = (
    "Kein Preis verfügbar: Bitpanda-eigenes ETF/ETC-Produkt, keine öffentliche "
    "Kursquelle - live geprüft, weder Bitpandas Katalog-Endpunkt noch (mit API-Key) "
    "die Wallet-/Transaktions-Endpunkte liefern einen Preis dafür. Manche dieser "
    "Produkte sind zwar durch echte Rohstoff-Futures abgesichert (z.B. Bitpandas "
    "'Grains' durch Mais-/Weizen-/Sojabohnen-Futures), aber Bitpandas eigene "
    "Gewichtung ist extern nicht einsehbar."
)
_ERKLAERUNG_AKTIE_OHNE_KATEGORIE = (
    "Keine Kategorie: der Yahoo-Finance-Screener liefert keine Sektor-/Branchendaten "
    "in der Kandidatenliste selbst - eine automatische Zuordnung bräuchte einen "
    "zusätzlichen Einzelabruf pro Aktie (bei 150-200 Kandidaten pro Scan bewusst "
    "nicht eingebaut, siehe Basisinfos/Regelwerksmanual.md)."
)


def _erklaerung_fehlende_daten(c) -> str | None:
    """Transparenz-Prinzip (2026-07-20, Nutzer-Nachfrage 'warum sind die Assets
    nicht durchgängig kategorisiert bzw. haben keinen Preis'): live geprüfte,
    strukturelle Lücken - keine geratenen/automatisch angereicherten Werte (siehe
    Regelwerksmanual: yfinance-Namenssuche wurde bewusst NICHT automatisiert, da
    sie live nachweislich auch falsche Treffer liefert)."""
    if c.quelle == "bitpanda_katalog":
        return _ERKLAERUNG_BITPANDA_KATALOG
    if c.assetklasse == "aktien" and c.hauptgruppe is None:
        return _ERKLAERUNG_AKTIE_OHNE_KATEGORIE
    return None

_THESE_MARKER_UND_TAG = {
    "uebergewichten": ("▲", "these_positiv"),
    "aktiv": ("▲", "these_positiv"),
    "meiden": ("▼", "these_negativ"),
    "neutral": ("●", "these_neutral"),
    "inaktiv": ("●", "these_neutral"),
}


class ScreenerView(ttk.Frame):
    def __init__(self, parent, db_conn_factory, watchlist) -> None:
        super().__init__(parent)
        self._db_conn_factory = db_conn_factory
        self._watchlist = watchlist
        self._candidates: list = []
        self._selected_candidate = None
        # Zeilen-Tooltips (2026-07-20) - kombiniert die Stufe-1-These-Begruendung
        # (Task #343) MIT der Erklaerung fuer fehlenden Preis/Kategorie
        # (_erklaerung_fehlende_daten()), siehe _on_scan_done().
        self._row_tooltips: dict[str, str] = {}
        # Auto-Scan (2026-07-20) - Intervall aus config.yaml, Default 60 Min
        # falls die Sektion (noch) fehlt (P-10, kein Absturz bei alter Config).
        screener_cfg = config_module.load_config().get("screener", {})
        intervall_minuten = screener_cfg.get("auto_scan_intervall_minuten", 60)
        self._auto_scan_intervall_ms = intervall_minuten * 60 * 1000
        self._auto_scan_after_id: str | None = None

        self._build_layout()
        # Erster Scan kurz nach dem Aufbau (Fenster soll erst rendern), danach
        # uebernimmt _on_scan_done() das selbstverlaengernde Nachplanen.
        self.after(500, self._on_scan_clicked)

    def _build_layout(self) -> None:
        toolbar = ttk.Frame(self)
        toolbar.pack(fill="x", padx=8, pady=(8, 4))
        self.scan_button = ttk.Button(toolbar, text="Jetzt scannen", command=self._on_scan_clicked)
        self.scan_button.pack(side="left")
        add_widget_tooltip(
            self.scan_button,
            "Sucht sofort neu nach Kandidaten (3 Yahoo-Finance-Screens fuer Aktien + "
            "Bitpandas eigener ETF/ETC-Katalog), zusaetzlich zum automatischen Scan alle "
            f"{self._auto_scan_intervall_ms // 60000} Minuten. Uebernimmt NICHTS "
            "automatisch in die Watchlist.",
        )
        self.watchlist_button = ttk.Button(
            toolbar, text="In Watchlist übernehmen", command=self._on_adopt_clicked, state="disabled",
        )
        self.watchlist_button.pack(side="left", padx=(8, 0))
        add_widget_tooltip(
            self.watchlist_button,
            "Uebernimmt den ausgewaehlten Kandidaten in Basisinfos/config.yaml (mit "
            "Sicherheits-Nachfrage). Bewertet ihn NICHT automatisch - das passiert erst "
            "danach ganz regulaer ueber die normale Signal-Pipeline, nach einem App-Neustart.",
        )

        self.status_label = ttk.Label(self, text=(
            "Scanne automatisch beim Start und danach alle "
            f"{self._auto_scan_intervall_ms // 60000} Minuten erneut (zusätzlich "
            "jederzeit manuell über \"Jetzt scannen\" möglich) - durchsucht 3 "
            "Yahoo-Finance-Screens (Aktien) und Bitpandas eigenen ETF/ETC-Katalog nach "
            "neuen Kandidaten, die noch nicht in der Watchlist stehen."
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
        add_row_tooltips(self.tree, lambda iid: self._row_tooltips.get(iid))
        self.tree.pack(fill="both", expand=True, padx=8, pady=(0, 8))
        self.tree.bind("<<TreeviewSelect>>", self._on_select)

    def _on_scan_clicked(self) -> None:
        if str(self.scan_button["state"]) == "disabled":
            # Schutz vor Doppel-Scans: kann passieren, wenn der automatische
            # Timer genau in dem Moment feuert, in dem bereits ein manueller
            # Scan laeuft (oder umgekehrt).
            return
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
        self._schedule_next_auto_scan()
        if error is not None:
            self.status_label.config(
                text=f"Scan fehlgeschlagen: {error} (naechster automatischer Versuch in "
                     f"{self._auto_scan_intervall_ms // 60000} Minuten)",
                foreground=theme.danger_color(),
            )
            return

        self._candidates = candidates
        for item in self.tree.get_children():
            self.tree.delete(item)
        self._row_tooltips.clear()

        # Stufe-1-Hervorhebung (2026-07-20, Task #343) - aktive Thesen einmal
        # laden, In-Memory-Index statt N Einzel-Queries (Muster wie
        # ui/app.py::_refresh_watchlist_from_db()).
        conn = self._db_conn_factory()
        try:
            these_index = kategorie_thesen.index_aktive_thesen(db.get_aktive_thesen(conn))
        finally:
            conn.close()

        # NUR die initiale Einsortierung (aktive These zuerst) - keine
        # gehalten-Prioritaet noetig, Screener-Kandidaten sind per Definition
        # noch nicht in der Watchlist. Nach dem ersten Rendern greift wie
        # gewohnt eine manuelle Spaltensortierung (make_sortable()).
        indices_sortiert = sorted(
            range(len(candidates)),
            key=lambda i: 0 if kategorie_thesen.lookup_these(
                these_index, candidates[i].hauptgruppe, candidates[i].unterkategorie
            ) is not None else 1,
        )

        for idx in indices_sortiert:
            c = candidates[idx]
            preis_text = f"{format_money(c.preis_usd)} $" if c.preis_usd is not None else "-"
            marktkap_text = f"{c.marktkap_usd / 1e9:.1f} Mrd." if c.marktkap_usd is not None else "-"
            aenderung_text = f"{c.aenderung_pct:+.1f}%" if c.aenderung_pct is not None else "-"
            bitpanda_text = "✓" if c.bitpanda_gelistet else ("✗" if c.bitpanda_gelistet is False else "?")
            kategorie_text = config_module.get_kategorie_name(c.hauptgruppe, c.unterkategorie) or "-"

            tags = []
            tooltip_teile = []
            these = kategorie_thesen.lookup_these(these_index, c.hauptgruppe, c.unterkategorie)
            if these is not None:
                marker, tag = _THESE_MARKER_UND_TAG.get(these.richtung, ("●", "these_neutral"))
                kategorie_text = f"{kategorie_text} {marker}"
                tags.append(tag)
                richtung_label = {"uebergewichten": "Übergewichten", "meiden": "Meiden", "neutral": "Neutral",
                                   "aktiv": "Aktiv", "inaktiv": "Inaktiv"}.get(these.richtung, these.richtung)
                these_kategorie_name = (
                    config_module.get_kategorie_name(these.hauptgruppe, these.unterkategorie)
                    or config_module.get_hauptgruppe_name(these.hauptgruppe)
                )
                tooltip_teile.append(
                    f"Aktive These ({these_kategorie_name}, {richtung_label}): {these.begruendung}"
                )
            erklaerung = _erklaerung_fehlende_daten(c)
            if erklaerung is not None:
                tooltip_teile.append(erklaerung)
            if tooltip_teile:
                self._row_tooltips[str(idx)] = "\n\n".join(tooltip_teile)
            if c.bitpanda_gelistet is False:
                tags.append("nicht_gelistet")  # zuletzt hinzugefuegt = hoehere Prioritaet bei ttk-Tag-Kollision

            self.tree.insert(
                "", "end", iid=str(idx),
                values=(c.symbol, c.name, c.assetklasse, c.quelle, preis_text, marktkap_text, aenderung_text, bitpanda_text, kategorie_text),
                tags=tuple(tags),
            )
        self.tree.tag_configure("nicht_gelistet", foreground=theme.danger_color())
        self.tree.tag_configure("these_positiv", foreground=theme.success_color())
        self.tree.tag_configure("these_negativ", foreground=theme.danger_color())
        self.tree.tag_configure("these_neutral", foreground=theme.info_color())
        self._reapply_sort()
        theme.restripe_treeview(self.tree)

        aktien_anzahl = sum(1 for c in candidates if c.assetklasse == "aktien")
        etf_anzahl = sum(1 for c in candidates if c.assetklasse == "etf")
        self.status_label.config(
            text=f"{aktien_anzahl} neue Aktien-Kandidaten (Yahoo-Finance-Screener), "
                 f"{etf_anzahl} neue ETF/ETC-Kandidaten (Bitpanda-Katalog). "
                 f"Naechster automatischer Scan in {self._auto_scan_intervall_ms // 60000} Minuten.",
            foreground=theme.info_color(),
        )

    def _schedule_next_auto_scan(self) -> None:
        """Selbstverlaengernder Timer (2026-07-20) - plant den naechsten
        automatischen Scan ab JETZT (egal ob der vorangegangene Scan manuell
        oder automatisch ausgeloest wurde). Bricht einen evtl. noch
        ausstehenden aelteren Timer ab, damit nie zwei parallele Ketten
        entstehen (z.B. wenn der Nutzer manuell scannt, waehrend noch ein
        automatischer Termin aussteht)."""
        if self._auto_scan_after_id is not None:
            self.after_cancel(self._auto_scan_after_id)
        self._auto_scan_after_id = self.after(self._auto_scan_intervall_ms, self._on_scan_clicked)

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
