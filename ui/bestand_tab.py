"""Der Bestand-Tab des NEUEN Systems (P15 / GUI-3, 12.10.2026, Plan_Asset_Lebenszyklus_14_09.md G-Y) - ERSETZT den Tab *Portfolio*.

Nutzer 12.10.: *"Ja, den Ausbau eindeutig kennzeichnen, damit man nicht ueber den alten Code stolpert"* - der Knopf *Letzte Bewertung
anzeigen* (letzte KI-Analyse der seit 05.10. angehaltenen Rollen-Kette) ist AUSGEBAUT; ``ui/portfolio.py`` ist als ABGELOEST gekennzeichnet
und nicht mehr in der GUI eingehaengt. Uebernommen (geerbt, unveraendert): Einstand per Doppelklick (GF4, ``AvgBuyPriceDialog``),
Fiat-Feld als Ausnahme, Diversifikation nach Schwerpunkt, Einstands-Tooltip.

BEREICHE:
  Spot     ALLE Bestaende (frei + gestakt > 0, alle Klassen): Symbol, Name, Assetklasse, ROLLE (Kern / L / Cash / - / nicht in Watchlist),
           frei, gestakt, Preis, Wert, Einstand, G/V, B1 (x Startkurs aus dem letzten Dollar-Tagesschluss, Fenster bis, Status) und
           Upbit KRW (aus P16). Die Marktwert-Klasse H/M/S kommt erst mit P18 (der NB rechnet sie heute nicht, Spot §42.1)
  Hebel    die offenen Positionen KURZ (Richtung, Hebel, Eigenkapital, Abstand, H15-Empfehlung) - Details im Hebel-Tab, dieselbe Quelle
  Summen   Spot frei · gestakt · Fiat · Hebel-Eigenkapital · GESAMT (Definition G-K)

LAUFZEIT: die App ruft ``refresh()`` alle 3 s. Holdings und Preise wie bisher; B1, Upbit und Hebel nur, wenn der Tab SICHTBAR ist,
hoechstens alle ``LANGSAM_S`` Sekunden. Unveraenderte Zeilen zeichnen nichts neu. Das Lesen schreibt nichts.
"""
from __future__ import annotations

import logging
import time
import tkinter as tk
from datetime import datetime
from tkinter import ttk

import config as config_module
import database.db as db
import ui.theme as theme
from importer.bitpanda_avg_cost import compute_cost_basis_view
from ui.formatting import format_money, is_price_stale
from ui.heading_tooltip import add_heading_tooltips
from ui.portfolio import PortfolioView
from ui.row_tooltip import add_row_tooltips
from ui.sortable_tree import make_sortable

logger = logging.getLogger(__name__)

LANGSAM_S = 60
KERN = ("BTC", "ETH", "SOL")
SPALTEN = ("symbol", "name", "assetklasse", "rolle", "frei", "gestakt", "price_eur", "value_eur", "avg_buy_price_eur", "pl_pct",
           "b1_x", "b1_bis", "b1_status", "upbit")
KOPF = {"symbol": "Symbol", "name": "Name", "assetklasse": "Assetklasse", "rolle": "Rolle", "frei": "frei", "gestakt": "gestakt",
        "price_eur": "Preis (EUR)", "value_eur": "Wert (EUR)", "avg_buy_price_eur": "Einstand (EUR)", "pl_pct": "G/V %",
        "b1_x": "× Start (B1)", "b1_bis": "Fenster bis", "b1_status": "B1", "upbit": "Upbit KRW"}
TIPP = {
    "rolle": "Kern = BTC/ETH/SOL (Akkumulation) · L = übrige Krypto, wird automatisch geführt (E-90) · Cash = Stablecoin · "
             "- = andere Klasse · 'nicht in Watchlist' = gehalten, aber ohne Stammdaten",
    "frei": "Frei verfügbare Menge (Bitpanda-Wallet).",
    "gestakt": "Gestakte Menge - zählt zum Bestand (bei Bitpanda wie Spot verkaufbar).",
    "value_eur": "Wert von frei + gestakt.",
    "b1_x": "Spot B1: letzter Dollar-Tagesschluss geteilt durch den Startkurs des laufenden Fensters. Ab 3,00 kommt die Mail 'Hälfte verkaufen'.",
    "b1_bis": "Ende des laufenden 365-Tage-Fensters; danach beginnt ein neues mit neuem Startkurs.",
    "b1_status": "laeuft · faellig · gemailt · zu pruefen (Kurssprung) · verpasst · kein Fenster (noch kein Kurs)",
    "upbit": "Spot B3: hat Upbit den Coin schon im Won-Markt? 'nein' = ein Listing wäre ein Verkaufsanlass (Mail). '?' = noch kein Lauf.",
}
HEBEL_SPALTEN = ("asset", "richtung", "hebel", "ek", "abstand", "empfehlung")
HEBEL_KOPF = {"asset": "Asset", "richtung": "Richtung", "hebel": "Hebel", "ek": "Eigenkapital", "abstand": "Abstand Liquidation",
              "empfehlung": "H15-Empfehlung"}


# ══ reine Aufbereitung (Pruefstand ohne Fenster) ═════════════════════════════════════════════════════════════════════════════
def rolle(symbol: str, asset) -> str:
    if asset is None:
        return "nicht in Watchlist"
    if getattr(asset, "ist_cash_aequivalent", False):
        return "Cash"
    if getattr(asset, "assetklasse", None) != "krypto":
        return "-"
    return "Kern" if symbol in KERN else "L"


def b1_werte(symbol: str, fenster: dict, letzter_schluss: dict) -> tuple:
    """(x Start, Fenster bis, Status) aus dem offenen B1-Fenster und dem letzten Dollar-Tagesschluss."""
    f = fenster.get(symbol)
    if f is None:
        return "-", "-", "kein Fenster"
    k = letzter_schluss.get(symbol)
    x = ("%.2f" % (k / f["startkurs_usd"])).replace(".", ",") if k and f.get("startkurs_usd") else "-"
    return x, datetime.strptime(f["ende"][:10], "%Y-%m-%d").strftime("%d.%m.%Y"), f.get("status") or "-"


def upbit_wert(symbol: str, ohne_krw: list | None) -> str:
    if ohne_krw is None:
        return "?"
    return "nein" if symbol in ohne_krw else "ja"


def spot_zeilen(holdings: list, preise: dict, watchlist_by_symbol: dict, fenster: dict, letzter_schluss: dict,
                ohne_krw: list | None) -> list:
    """Je Bestand (frei + gestakt > 0) eine Zeile; dazu die Summen-Bausteine. -> [{'symbol', 'werte', 'tags', 'frei_eur', 'gestakt_eur',
    'cost'}]"""
    aus = []
    for h in sorted(holdings, key=lambda x: x.symbol):
        gest = float(h.staked_quantity or 0.0)
        if float(h.quantity or 0.0) == 0 and gest <= 0:
            continue
        a = watchlist_by_symbol.get(h.symbol)
        r = rolle(h.symbol, a)
        p = preise.get(h.symbol)
        pe = p.price_eur if p else None
        stale = is_price_stale(p.fetched_at if p else None)
        menge = float(h.quantity or 0.0) + gest
        cost = compute_cost_basis_view(h, pe, menge=menge)
        if cost.source == "unbekannt":
            avg = "unbekannt"
        else:
            avg = format_money(cost.effective_avg_price_eur)
            if cost.source == "manuell":
                avg += " (manuell)"
            elif cost.unknown_quantity > 0:
                avg += " (⚠ %g unbepreist)" % cost.unknown_quantity
        preis = format_money(pe)
        if stale and preis != "-":
            preis = "⚠ " + preis
        if r == "L":
            b1 = b1_werte(h.symbol, fenster, letzter_schluss)
            ub = upbit_wert(h.symbol, ohne_krw)
        else:
            b1, ub = ("-", "-", "-"), "-"
        tags = []
        if stale:
            tags.append("stale")
        if cost.pl_pct is not None:
            tags.append("pl_positive" if cost.pl_pct >= 0 else "pl_negative")
        if b1[2] in ("faellig", "zu pruefen"):
            tags.append("b1_achtung")
        aus.append({"symbol": h.symbol, "asset": a, "cost": cost, "tags": tuple(tags),
                    "frei_eur": (float(h.quantity or 0.0) * pe) if pe is not None else None,
                    "gestakt_eur": (gest * pe) if pe is not None and gest > 0 else 0.0,
                    "werte": (h.symbol, a.name if a else h.symbol, a.assetklasse if a else "-", r, "%g" % float(h.quantity or 0.0),
                              ("%g" % gest) if gest > 0 else "-", preis, format_money((menge * pe) if pe is not None else None), avg,
                              ("%+.1f%%" % cost.pl_pct) if cost.pl_pct is not None else "-", b1[0], b1[1], b1[2], ub)})
    return aus


def hebel_zeilen(trades: list) -> list:
    aus = []
    for t in trades:
        a = t.get("abstand_liquidation")
        aus.append((t.get("symbol"), t.get("richtung"), ("%.1fx" % t["hebel"]) if t.get("hebel") else "-", format_money(t.get("eigenkapital_eur")),
                    ("%.1f %%" % (100 * a)) if a is not None else "-", str(t.get("empfehlung") or "-")))
    return aus


def summen(zeilen: list, fiat_eur: float, hebel_ek_eur: float) -> dict:
    frei = sum(z["frei_eur"] for z in zeilen if z["frei_eur"] is not None)
    gest = sum(z["gestakt_eur"] or 0.0 for z in zeilen)
    return {"frei": frei, "gestakt": gest, "fiat": fiat_eur or 0.0, "hebel_ek": hebel_ek_eur or 0.0,
            "gesamt": frei + gest + (fiat_eur or 0.0) + (hebel_ek_eur or 0.0)}


def lese_b1(ordner: str) -> tuple:
    """({Symbol: offenes Fenster}, {Symbol: letzter Dollar-Tagesschluss}) - spot_betrieb.db und Produktion nur lesend."""
    import os

    from agent import spot_mitnahme as SM

    p = os.path.join(ordner, SM.ABLAGE)
    if not os.path.exists(p):
        return {}, {}
    c = SM._ro(p)
    try:
        fenster = {r[0]: {"start": r[1], "startkurs_usd": r[2], "ende": r[3], "status": r[4]} for r in c.execute(
            "SELECT symbol, start, startkurs_usd, ende, status FROM fenster WHERE geschlossen_am IS NULL")}
    finally:
        c.close()
    return fenster, {}


def letzte_schluesse(conn, symbole) -> dict:
    out = {}
    for s in symbole:
        r = conn.execute("SELECT close FROM price_history_ohlc WHERE symbol=? AND currency='USD' AND close IS NOT NULL "
                         "AND COALESCE(quelle,'') != 'rekonstruiert' ORDER BY date DESC LIMIT 1", (s,)).fetchone()
        if r:
            out[s] = float(r[0])
    return out


# ══ der Tab ═════════════════════════════════════════════════════════════════════════════════════════════════════════════════
class BestandTab(PortfolioView):
    """Erbt die bewaehrten Teile von PortfolioView (Einstand, Fiat, Diversifikation, Tooltip) - der Aufbau ist NEU (P15)."""

    def __init__(self, parent, db_conn_factory, watchlist, spot_ordner: str | None = None):     # noqa: D401 - eigener Aufbau
        ttk.Frame.__init__(self, parent)                     # bewusst NICHT PortfolioView.__init__ (dort: Knopf 'Letzte Bewertung')
        from agent import regel0_nachlader as NL

        self._db_conn_factory = db_conn_factory
        self._cost_basis_by_symbol: dict = {}
        self._watchlist_by_symbol = {a.symbol: a for a in watchlist}
        self._diversifikation_tooltips: dict = {}
        self._ordner = spot_ordner or NL.DATEN_VORGABE
        self._zuletzt_langsam = 0.0
        self._fenster: dict = {}
        self._schluss: dict = {}
        self._ohne_krw = None
        self._hebel: list = []
        self._hebel_ek = 0.0
        self._stand = None
        self._bauen()
        self.reload_cash_reserve_from_db()
        self.refresh(erzwingen=True)

    def _bauen(self) -> None:
        kopf = ttk.Frame(self)
        kopf.pack(fill="x", padx=8, pady=(8, 0))
        ttk.Label(kopf, text="Spot – alle Bestände (frei + gestakt)", font=("", 10, "bold")).pack(side="left")
        ttk.Button(kopf, text="Aktualisieren", command=lambda: self.refresh(erzwingen=True)).pack(side="right")
        self.status = ttk.Label(kopf, text="", foreground=theme.info_color())
        self.status.pack(side="right", padx=8)
        self.tree = ttk.Treeview(self, columns=SPALTEN, show="headings", height=16)
        for c in SPALTEN:
            self.tree.heading(c, text=KOPF[c])
            self.tree.column(c, width={"name": 150, "symbol": 70, "rolle": 110, "assetklasse": 80, "b1_status": 85, "upbit": 70}.get(c, 95),
                             anchor="w" if c in ("name", "assetklasse", "rolle", "b1_status") else "e")
        self.tree.tag_configure("stale", foreground=theme.stale_color())
        self.tree.tag_configure("pl_positive", foreground=theme.success_color())
        self.tree.tag_configure("pl_negative", foreground=theme.danger_color())
        self.tree.tag_configure("b1_achtung", foreground=theme.warn_color())
        self._reapply_sort = make_sortable(self.tree, numeric_columns=frozenset({"frei", "gestakt", "price_eur", "value_eur", "avg_buy_price_eur",
                                                                                  "pl_pct", "b1_x"}))
        add_heading_tooltips(self.tree, TIPP)
        add_row_tooltips(self.tree, self._row_tooltip_text)
        self.tree.bind("<Double-1>", self._on_edit_avg_price)        # GF4 Einstand (geerbt)
        self.tree.pack(fill="both", expand=True, padx=8, pady=(4, 6))

        ttk.Label(self, text="Hebel – offene Positionen (kurz; Details im Hebel-Tab)", font=("", 10, "bold")).pack(anchor="w", padx=8)
        self.hebel_tree = ttk.Treeview(self, columns=HEBEL_SPALTEN, show="headings", height=3)
        for c in HEBEL_SPALTEN:
            self.hebel_tree.heading(c, text=HEBEL_KOPF[c])
            self.hebel_tree.column(c, width=130 if c == "empfehlung" else 110, anchor="w" if c in ("asset", "richtung", "empfehlung") else "e")
        self.hebel_tree.pack(fill="x", padx=8, pady=(2, 6))

        ttk.Label(self, text="Diversifikation nach Schwerpunkt", font=("", 10, "bold")).pack(anchor="w", padx=8, pady=(4, 2))
        dspalten = ("schwerpunkt", "wert_eur", "anteil_pct")
        self.diversifikation_tree = ttk.Treeview(self, columns=dspalten, show="headings", height=5)
        for c, t in zip(dspalten, ("Schwerpunkt", "Wert (EUR)", "Anteil %")):
            self.diversifikation_tree.heading(c, text=t)
            self.diversifikation_tree.column(c, width=160, anchor="w" if c == "schwerpunkt" else "e")
        self.diversifikation_tree.tag_configure("these_positiv", foreground=theme.success_color())
        self.diversifikation_tree.tag_configure("these_negativ", foreground=theme.danger_color())
        self.diversifikation_tree.tag_configure("these_neutral", foreground=theme.info_color())
        self._diversifikation_reapply_sort = make_sortable(self.diversifikation_tree, numeric_columns=frozenset({"wert_eur", "anteil_pct"}))
        add_row_tooltips(self.diversifikation_tree, lambda iid: self._diversifikation_tooltips.get(iid))
        self.diversifikation_tree.pack(fill="x", padx=8, pady=(0, 6))

        self.total_label = ttk.Label(self, text="Gesamtwert: -", font=("", 10, "bold"))
        self.total_label.pack(anchor="e", padx=8, pady=(0, 4))
        cash_frame = ttk.Frame(self)
        cash_frame.pack(anchor="e", padx=8, pady=(0, 8))
        ttk.Label(cash_frame, text="Fiat-Guthaben auf Börse (EUR, vom Bitpanda-Abgleich; Speichern nur als Ausnahme):").pack(side="left", padx=(0, 6))
        self.cash_reserve_var = tk.StringVar()
        ttk.Entry(cash_frame, textvariable=self.cash_reserve_var, width=10, justify="right").pack(side="left")
        ttk.Button(cash_frame, text="Speichern", command=self._save_cash_reserve).pack(side="left", padx=(6, 0))
        self.cash_reserve_status = ttk.Label(cash_frame, text="")
        self.cash_reserve_status.pack(side="left", padx=(6, 0))
        self.cash_reserve_synced_label = ttk.Label(cash_frame, text="", foreground=theme.info_color())
        self.cash_reserve_synced_label.pack(side="left", padx=(10, 0))

    # ---- Lesen ----
    def _langsam(self) -> None:
        from agent import betriebslage as BL
        from agent import hebelfuehrung as HF
        from agent import regel0_groesse as G

        try:
            self._fenster, _ = lese_b1(self._ordner)
            su = BL.spot_upbit(self._ordner)
            self._ohne_krw = su.get("ohne_krw") if su.get("laeufe") else None
        except Exception:                                   # noqa: BLE001
            logger.exception("Bestand-Tab: B1/B3-Ablage nicht lesbar")
        conn = self._db_conn_factory()
        try:
            self._schluss = letzte_schluesse(conn, list(self._fenster))
            trades = HF.lade(conn, nahe_grenze=float(G.lade().get("liquidations_warnung_abstand") or HF.LIQ_NAHE_GRENZE))
            self._hebel = hebel_zeilen(trades)
            self._hebel_ek = sum(float(t.get("eigenkapital_eur") or 0.0) for t in trades)
        except Exception:                                   # noqa: BLE001
            logger.exception("Bestand-Tab: Hebelpositionen nicht lesbar")
        finally:
            conn.close()
        self.hebel_tree.delete(*self.hebel_tree.get_children())
        for z in self._hebel or [("Keine offenen Positionen", "-", "-", "-", "-", "-")]:
            self.hebel_tree.insert("", "end", values=z)

    def refresh(self, erzwingen: bool = False) -> None:
        jetzt = time.monotonic()
        if erzwingen or (self.winfo_ismapped() and jetzt - self._zuletzt_langsam >= LANGSAM_S):
            self._langsam()
            self._zuletzt_langsam = jetzt
        conn = self._db_conn_factory()
        try:
            holdings = db.get_all_holdings(conn)
            preise = db.get_latest_prices(conn)
            fiat = db.get_cash_reserve_fiat_eur(conn)
            thesen = db.get_aktive_thesen(conn)
        finally:
            conn.close()
        zeilen = spot_zeilen(holdings, preise, self._watchlist_by_symbol, self._fenster, self._schluss, self._ohne_krw)
        s = summen(zeilen, fiat, self._hebel_ek)
        stand = (tuple((z["werte"], z["tags"]) for z in zeilen), round(s["gesamt"], 2))
        if stand != self._stand:
            self._stand = stand
            auswahl = self.tree.selection()
            alt = auswahl[0] if auswahl else None
            self.tree.delete(*self.tree.get_children())
            self._cost_basis_by_symbol = {}
            for z in zeilen:
                self._cost_basis_by_symbol[z["symbol"]] = z["cost"]
                self.tree.insert("", "end", iid=z["symbol"], values=z["werte"], tags=z["tags"])
            self._reapply_sort()
            theme.restripe_treeview(self.tree)
            if alt and self.tree.exists(alt):
                self.tree.selection_set(alt)
            teile = "Spot frei %s · gestakt %s · Fiat %s · Hebel-Eigenkapital %s" % tuple(
                format_money(s[k]) for k in ("frei", "gestakt", "fiat", "hebel_ek"))
            self.total_label.config(text="Gesamtwert: %s EUR  (%s)" % (format_money(s["gesamt"]), teile))
            self._diversifikation_neu(zeilen, s, thesen)
        self.status.config(text="Stand %s · %d Bestände" % (datetime.now().strftime("%H:%M:%S"), len(zeilen)))

    def _diversifikation_neu(self, zeilen: list, s: dict, thesen: list) -> None:
        """Wie bisher (PortfolioView): Spot frei + gestakt + Fiat nach Hauptgruppe - ohne Hebel."""
        je_gruppe, gruppen_id, thesen_je = {}, {}, {}
        for t in thesen:
            thesen_je.setdefault(t.hauptgruppe, []).append(t)
        for z in zeilen:
            w = (z["frei_eur"] or 0.0) + (z["gestakt_eur"] or 0.0)
            if z["frei_eur"] is None:
                continue
            a = z["asset"]
            name = config_module.get_hauptgruppe_name(a.hauptgruppe) if a else None
            k = name or "ohne Schwerpunkt"
            je_gruppe[k] = je_gruppe.get(k, 0.0) + w
            if a and a.hauptgruppe:
                gruppen_id.setdefault(k, a.hauptgruppe)
        if s["fiat"] > 0:
            je_gruppe["Cash/Sonstiges"] = je_gruppe.get("Cash/Sonstiges", 0.0) + s["fiat"]
        self._refresh_diversifikation(je_gruppe, s["frei"] + s["gestakt"] + s["fiat"], gruppen_id, thesen_je)
