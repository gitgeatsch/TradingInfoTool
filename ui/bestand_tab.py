"""Der Bestand-Tab des NEUEN Systems (P15 / GUI-3, 12.10.2026, Plan_Asset_Lebenszyklus_14_09.md G-Y) - ERSETZT den Tab *Portfolio*.

Nutzer 12.10.: *"Ja, den Ausbau eindeutig kennzeichnen, damit man nicht ueber den alten Code stolpert"* - der Knopf *Letzte Bewertung
anzeigen* (letzte KI-Analyse der seit 05.10. angehaltenen Rollen-Kette) ist AUSGEBAUT; ``ui/portfolio.py`` ist als ABGELOEST gekennzeichnet
und nicht mehr in der GUI eingehaengt. Uebernommen (geerbt, unveraendert): Einstand per Doppelklick (GF4, ``AvgBuyPriceDialog``),
Fiat-Feld als Ausnahme, Einstands-Tooltip. Die DIVERSIFIKATION NACH SCHWERPUNKT (Multi-Asset, Thesen des Schwerpunkte-Tabs) ist seit
P15e (13.10.2026, Nutzer: *"Ja, 1 bis 3 so umsetzen"*) NICHT mehr hier: an ihrer Stelle die AUFTEILUNG NACH ROLLE (Kern / L / Cash / Fiat /
andere Klassen / Hebel). Die Schwerpunkt-Diversifikation zieht mit GUI-5 in den Tab *Multi-Asset (ruht)* (Plan P20, fuer O39) - der Code
dafuer bleibt in ``PortfolioView._refresh_diversifikation``.

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
# P15b (12.10.2026, Nutzer: *"bitte ueberall ein Mouseover mit der genauen Bedeutung der Spalten"*): JEDE Spalte jeder Tabelle erklaert
# (Suite GuiKette prueft die Vollstaendigkeit gegen die Spaltenliste)
TIPP = {
    "symbol": "Kurzzeichen des Assets, wie bei Bitpanda geführt.",
    "name": "Vollständiger Name des Assets (aus der Watchlist; ohne Eintrag dort steht das Kurzzeichen).",
    "assetklasse": "krypto, aktien, etf oder rohstoffe - aus der Watchlist.",
    "price_eur": "Letzter Kurs in Euro aus dem Preis-Abruf (Krypto: CoinGecko, Wertpapiere: yfinance). ⚠ = veraltet, kein aktueller Abruf.",
    "avg_buy_price_eur": "Durchschnittlicher Einstandspreis je Stück in Euro - aus deinen Bitpanda-Käufen berechnet. '(m)' = manuell per "
                         "Doppelklick überschrieben, '⚠' = ein Teil der Menge ohne bekannten Kaufpreis (z. B. Staking-Gutschrift) - wie viel, "
                         "zeigt das Mouseover auf der Zeile.",
    "pl_pct": "Gewinn/Verlust in Prozent: Wert von frei + gestakt gegen den Einstand (ohne Gebühren). '-' = Einstand unbekannt.",
    "rolle": "Kern = BTC/ETH/SOL (Akkumulation) · L = übrige Krypto, wird automatisch geführt (E-90) · Cash = Stablecoin · "
             "- = andere Klasse · 'nicht in Watchlist' = gehalten, aber ohne Stammdaten",
    "frei": "Frei verfügbare Menge in Stück (Bitpanda-Wallet).",
    "gestakt": "Gestakte Menge in Stück - zählt zum Bestand (bei Bitpanda wie Spot verkaufbar; nur ETH braucht Tage zum Entstaken).",
    "value_eur": "Wert in Euro von frei + gestakt zum letzten Kurs.",
    "b1_x": "Spot B1: letzter Dollar-Tagesschluss geteilt durch den Startkurs des laufenden Fensters. Ab 3,00 kommt die Mail 'Hälfte verkaufen'.",
    "b1_bis": "Ende des laufenden 365-Tage-Fensters; danach beginnt ein neues mit neuem Startkurs.",
    "b1_status": "laeuft · faellig · gemailt · zu pruefen (Kurssprung) · verpasst · kein Fenster (noch kein Kurs)",
    "upbit": "Spot B3: hat Upbit den Coin schon im Won-Markt? 'nein' = ein Listing wäre ein Verkaufsanlass (Mail). '?' = noch kein Lauf.",
}
HEBEL_SPALTEN = ("asset", "richtung", "hebel", "ek", "abstand", "empfehlung")
HEBEL_TIPP = {
    "asset": "Asset der offenen Hebelposition bei Bitpanda.",
    "richtung": "LONG = auf steigende Kurse, SHORT = auf fallende Kurse.",
    "hebel": "Effektiver Hebel der Position (von Bitpanda gemeldet; fehlt er, Positionswert / Eigenkapital).",
    "ek": "Eigenkapital in Euro, das in der Position steckt (zählt zum Gesamtwert).",
    "abstand": "Abstand vom aktuellen Kurs zum geschätzten Liquidationspreis, in Prozent des Kurses. Warnstufen ab 15 % (H15).",
    "empfehlung": "Hebelführung H15: LIQUIDIERT > SCHLIESSEN > HEBEL SENKEN > LIQUIDATION NAHE > KURS FEHLT > STOP NACHZIEHEN > HALTEN. "
                  "Details, Kurs, Liquidationspreis und Finanzierung im Hebel-Tab.",
}
AUF_REIHE = ("Kern", "L", "Cash", "Fiat", "andere Klassen", "nicht in Watchlist", "Hebel")
# P15f (13.10.2026, Nutzerbild: *"der Bereich unten mit Aufteilung nach Rolle ist leer"* - er lag unter dem Fensterrand): WAAGRECHT, eine
# Spalte je Gruppe, zwei Zeilen (Wert, Anteil) - braucht drei statt acht Zeilen Hoehe
AUF_SPALTEN = ("zeile",) + AUF_REIHE
AUF_KOPF = dict({"zeile": ""}, **{g: g for g in AUF_REIHE})
AUF_TIPP = {
    "zeile": "Wert in Euro und Anteil am Gesamtwert (oben) je Gruppe - die Anteile ergeben zusammen 100 %.",
    "Kern": "BTC, ETH, SOL - Akkumulation, frei + gestakt zum letzten Kurs.",
    "L": "Übrige Krypto-Bestände (E-90) - geführt mit Mitnahme ×3 (B1) und Upbit-Verkaufsanlass (B3).",
    "Cash": "Stablecoins (z. B. EURCV), frei + gestakt.",
    "Fiat": "Euro-Guthaben auf der Börse (Bitpanda-Abgleich).",
    "andere Klassen": "Aktien, ETF und Rohstoffe.",
    "nicht in Watchlist": "Gehaltene Assets, die in der Watchlist fehlen (z. B. XDC) - ohne Rolle, nicht in B1/B3.",
    "Hebel": "Eigenkapital der offenen Hebelpositionen - dieselbe Summe wie in der Hebel-Überschrift darüber.",
}
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


def menge_text(x: float) -> str:
    """Stueckzahl lesbar: ab einer Million ganzzahlig mit Tausendertrennung (Nutzerbild 12.10.: CAT stand als 2.6188e+07), sonst wie bisher %g."""
    return "{:,.0f}".format(x) if abs(x) >= 1e6 else "%g" % x


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
        # P15c (12.10.2026, Nutzerbild): kompakt - die Einzelheiten (Herkunft, unbepreiste Menge) stehen im Zeilen-Mouseover
        if cost.source == "unbekannt":
            avg = "unbekannt"
        else:
            avg = format_money(cost.effective_avg_price_eur)
            if cost.source == "manuell":
                avg += " (m)"
            elif cost.unknown_quantity > 0:
                avg += " ⚠"
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
                    "werte": (h.symbol, a.name if a else h.symbol, a.assetklasse if a else "-", r, menge_text(float(h.quantity or 0.0)),
                              menge_text(gest) if gest > 0 else "-", preis, format_money((menge * pe) if pe is not None else None), avg,
                              ("%+.1f%%" % cost.pl_pct) if cost.pl_pct is not None else "-", b1[0], b1[1], b1[2], ub)})
    return aus


def hebel_zeilen(trades: list) -> list:
    aus = []
    for t in trades:
        a = t.get("abstand_liquidation")
        aus.append((t.get("symbol"), t.get("richtung"), ("%.1fx" % t["hebel"]) if t.get("hebel") else "-", format_money(t.get("eigenkapital_eur")),
                    ("%.1f %%" % (100 * a)) if a is not None else "-", str(t.get("empfehlung") or "-")))
    return aus


def aufteilung(zeilen: list, s: dict) -> list:
    """P15e: [(Gruppe, Wert EUR, Anteil %)] nach Rolle - Anteile am Gesamtwert, zusammen 100 %. Gruppen ohne Wert entfallen."""
    gruppe = {"Kern": "Kern", "L": "L", "Cash": "Cash", "-": "andere Klassen", "nicht in Watchlist": "nicht in Watchlist"}
    w = dict.fromkeys(AUF_REIHE, 0.0)
    for z in zeilen:
        if z["frei_eur"] is None:
            continue
        w[gruppe[z["werte"][3]]] += (z["frei_eur"] or 0.0) + (z["gestakt_eur"] or 0.0)
    w["Fiat"] += s["fiat"]
    w["Hebel"] += s["hebel_ek"]
    g = s["gesamt"] or 0.0
    return [(k, w[k], (100.0 * w[k] / g) if g else 0.0) for k in AUF_REIHE if w[k] > 0]


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
    """Erbt die bewaehrten Teile von PortfolioView (Einstand, Fiat, Einstands-Tooltip) - der Aufbau ist NEU (P15); statt der Diversifikation
    nach Schwerpunkt die Aufteilung nach Rolle (P15e)."""

    def __init__(self, parent, db_conn_factory, watchlist, spot_ordner: str | None = None):     # noqa: D401 - eigener Aufbau
        ttk.Frame.__init__(self, parent)                     # bewusst NICHT PortfolioView.__init__ (dort: Knopf 'Letzte Bewertung')
        from agent import regel0_nachlader as NL

        self._db_conn_factory = db_conn_factory
        self._cost_basis_by_symbol: dict = {}
        self._watchlist_by_symbol = {a.symbol: a for a in watchlist}
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
        # P15d (13.10.2026, Nutzer: *"Summe fuer Hebel ist nicht sichtbar"*): der Gesamtwert steht OBEN - unten passte er bei 150 %
        # Anzeige nicht mehr ins Fenster
        self.total_label = ttk.Label(self, text="Gesamtwert: -", font=("", 10, "bold"))
        self.total_label.pack(anchor="w", padx=8, pady=(2, 0))
        # P15g (13.10.2026, Nutzer: *"die drei Bereiche auch in der Hoehe anpassbar machen zum Verschieben"*): Spot, Hebel und Aufteilung
        # liegen in EINEM senkrechten PanedWindow - die Trennleisten lassen sich mit der Maus ziehen. Das Fiat-Feld haengt FEST unten
        # (zuerst gepackt, side=bottom), damit es beim Ziehen nie aus dem Fenster rutscht.
        cash_frame = ttk.Frame(self)
        cash_frame.pack(side="bottom", anchor="e", padx=8, pady=(0, 8))
        self._paned = ttk.PanedWindow(self, orient="vertical")
        self._paned.pack(fill="both", expand=True, padx=8, pady=(4, 4))
        rahmen = ttk.Frame(self._paned)                             # P15e: senkrechte UND waagrechte Laufleiste
        self._paned.add(rahmen, weight=4)
        self._spot_rahmen = rahmen
        self.tree = ttk.Treeview(rahmen, columns=SPALTEN, show="headings", height=12)          # P15f: 12 Zeilen, Rest ueber die Laufleiste
        for c in SPALTEN:
            self.tree.heading(c, text=KOPF[c])
            # P15c: Summe der Breiten passt auch bei 150 % Anzeige in ein Vollbild; dazu die waagrechte Laufleiste (keine Spalte verschwindet)
            self.tree.column(c, width={"symbol": 70, "name": 130, "assetklasse": 75, "rolle": 100, "frei": 95, "gestakt": 85, "price_eur": 90,
                                       "value_eur": 85, "avg_buy_price_eur": 110, "pl_pct": 65, "b1_x": 75, "b1_bis": 85, "b1_status": 70,
                                       "upbit": 75}[c], minwidth=40,
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
        _xs = ttk.Scrollbar(rahmen, orient="horizontal", command=self.tree.xview)
        _ys = ttk.Scrollbar(rahmen, orient="vertical", command=self.tree.yview)
        self.tree.configure(xscrollcommand=_xs.set, yscrollcommand=_ys.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        _ys.grid(row=0, column=1, sticky="ns")
        _xs.grid(row=1, column=0, sticky="ew")
        rahmen.rowconfigure(0, weight=1)
        rahmen.columnconfigure(0, weight=1)

        hebel_bereich = ttk.Frame(self._paned)
        self._paned.add(hebel_bereich, weight=1)
        self.hebel_kopf = ttk.Label(hebel_bereich, text="Hebel – offene Positionen (kurz; Details im Hebel-Tab)", font=("", 10, "bold"))
        self.hebel_kopf.pack(anchor="w", pady=(4, 0))                # P15d: nennt die Hebel-Summe (Zahl, Eigenkapital zusammen)
        self.hebel_tree = ttk.Treeview(hebel_bereich, columns=HEBEL_SPALTEN, show="headings", height=2)   # P15f: Hoehe = Zahl der Positionen
        for c in HEBEL_SPALTEN:
            self.hebel_tree.heading(c, text=HEBEL_KOPF[c])
            self.hebel_tree.column(c, width=130 if c == "empfehlung" else 110, anchor="w" if c in ("asset", "richtung", "empfehlung") else "e")
        add_heading_tooltips(self.hebel_tree, HEBEL_TIPP)
        self.hebel_tree.pack(fill="both", expand=True, pady=(2, 4))

        # P15e: AUFTEILUNG NACH ROLLE statt Diversifikation nach Schwerpunkt (die zieht mit GUI-5 nach Multi-Asset (ruht), Plan P20)
        auf_bereich = ttk.Frame(self._paned)
        self._paned.add(auf_bereich, weight=1)
        ttk.Label(auf_bereich, text="Aufteilung nach Rolle", font=("", 10, "bold")).pack(anchor="w", pady=(4, 2))
        self.aufteilung_tree = ttk.Treeview(auf_bereich, columns=AUF_SPALTEN, show="headings", height=2)
        for c in AUF_SPALTEN:
            self.aufteilung_tree.heading(c, text=AUF_KOPF[c])
            self.aufteilung_tree.column(c, width=90 if c == "zeile" else 120, anchor="w" if c == "zeile" else "e")
        add_heading_tooltips(self.aufteilung_tree, AUF_TIPP)
        self.aufteilung_tree.pack(fill="both", expand=True, pady=(0, 4))

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
        self.hebel_kopf.config(text="Hebel – offene Positionen: %d · Eigenkapital zusammen %s EUR (kurz; Details im Hebel-Tab)" % (
            len(self._hebel), format_money(self._hebel_ek)))
        self.hebel_tree.delete(*self.hebel_tree.get_children())
        for z in self._hebel or [("Keine offenen Positionen", "-", "-", "-", "-", "-")]:
            self.hebel_tree.insert("", "end", values=z)
        self.hebel_tree.configure(height=max(1, min(5, len(self._hebel))))

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
            self.aufteilung_tree.delete(*self.aufteilung_tree.get_children())
            auf = {g: (w, a) for g, w, a in aufteilung(zeilen, s)}
            self.aufteilung_tree.insert("", "end", iid="auf|wert", values=("Wert (EUR)",) + tuple(
                format_money(auf[g][0]) if g in auf else "-" for g in AUF_REIHE))
            self.aufteilung_tree.insert("", "end", iid="auf|anteil", values=("Anteil %",) + tuple(
                ("%.1f" % auf[g][1]) if g in auf else "-" for g in AUF_REIHE))
        self.status.config(text="Stand %s · %d Bestände" % (datetime.now().strftime("%H:%M:%S"), len(zeilen)))
