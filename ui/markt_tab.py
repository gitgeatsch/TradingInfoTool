"""Reiter 3 *Spot* und Reiter 4 *Markt (Krypto)* des NEUEN Systems (P19, 17.10.2026; Plan_Asset_Lebenszyklus_14_09.md G2, Spot §49.3/§49.5).

Nutzer 10.10. (G2): *Markt (Krypto)* zeigt die gemessenen Marktfakten, die die Krypto-Strategien wirklich nutzen - alles als FAKT, kein
Override. *Spot* zeigt die Einstiegs-Kandidaten (oberes Fuenftel je Klasse, Bitpanda-handelbar). Der alte Reiter *Regime* bleibt bis
GUI-5 (Archiv; Regel *Ruecksprache vor dem Entfernen*).

  Markt (Krypto)  Season-Ampel B1-B3 mit Wert, Schwelle, erfuellt, vor 30/90 T; Stufe seit; Breite, Netto-Liquiditaet, Fear & Greed;
                  Verlauf 12 Monate (Stand 0-3 und Stufe); darunter die Makro-Lage (O54, dieselbe Quelle wie Statusseite und Mails)
  Spot            Einstiegs-Kandidaten aus dem B4-Universum am letzten Stichtag (A3) - ORDNET den Fortbestand, ein Einstieg je Asset ist
                  NICHT belegt; gehaltene sind markiert, nicht bevorzugt (O41)

LAUFZEIT: die App ruft ``refresh()`` alle 3 s; gelesen wird nur, wenn der Reiter sichtbar ist, hoechstens alle ``LANGSAM_S`` Sekunden
(Knopf *Aktualisieren* erzwingt es). Nur lesend. Die Aufbereitung steht in reinen Funktionen (``ampel_zeilen``, ``makro_zeilen``,
``kandidaten_zeilen``) - Pruefstand und Suite pruefen sie ohne Fenster.
"""
from __future__ import annotations

import logging
import time
import tkinter as tk
from datetime import date
from tkinter import ttk

import ui.theme as theme
from ui.heading_tooltip import add_heading_tooltips
from ui.sortable_tree import make_sortable

logger = logging.getLogger(__name__)

LANGSAM_S = 60

AMPEL_SPALTEN = ("bedingung", "wert", "schwelle", "erfuellt", "vor30", "vor90")
AMPEL_KOPF = {"bedingung": "Bedingung", "wert": "heute", "schwelle": "Schwelle", "erfuellt": "erfüllt", "vor30": "vor 30 T",
              "vor90": "vor 90 T"}
AMPEL_TIPP = {
    "bedingung": "B1 BTC-Rendite 91 Tage (Binance, Betriebskopie) · B2 Geldmenge M2 gegen Vorjahr (FRED, 35 T Verzug) · "
                 "B3 Stablecoin-Angebot 91 Tage (DefiLlama, ganze Reihe je Lauf).",
    "wert": "Wert am letzten abgeschlossenen Tag (die laufende Tageskerze zählt nicht).",
    "schwelle": "Schwelle aus der Kalibrierung (Spot §36.3, 2020/21) - eingefroren am Holdout 2017/18 geprüft (Spot §59, E-124).",
    "erfuellt": "✔ = Bedingung erfüllt. Die Zahl der erfüllten ist der Stand (0 bis 3).",
    "vor30": "Wert derselben Bedingung 30 Tage vorher.",
    "vor90": "Wert derselben Bedingung 90 Tage vorher.",
}
MAKRO_SPALTEN = ("kanal", "lang", "kurz")
MAKRO_KOPF = {"kanal": "Kanal", "lang": "lang", "kurz": "kurz"}
MAKRO_TIPP = {
    "kanal": "Makro-Kanäle K1 bis K9 wie die Messung Spot §51.7 (FRED). Fakt, kein Signal - du gewichtest (O54).",
    "lang": "Rückenwind / neutral / Gegenwind über das lange Fenster (Drittel im rollierenden 5-Jahres-Fenster).",
    "kurz": "Rückenwind / neutral / Gegenwind über das kurze Fenster.",
}
GESAMT_SPALTEN = ("nr", "stichwort", "wert", "gemessen")
GESAMT_KOPF = {"nr": "", "stichwort": "Lagebild", "wert": "heute", "gemessen": "gemessen"}
GESAMT_TIPP = {
    "nr": "Kennung der Lagebild-Zeile (L1 bis L7).",
    "stichwort": "Lagebild Gesamtmarkt L1-L7 (L-A, E-137; L7 DVOL E-161): Fakt, kein Signal - keine Makrogröße läuft den BTC-Wenden voraus (Atlas E-135).",
    "wert": "Stand heute (FRED, alternative.me). Einzige Farbe: Rezessionsampel ROT, wenn Zinskurve UND Sahm-Regel anschlagen.",
    "gemessen": "Was die Messung dazu sagt (Indikator-Atlas E-135).",
}
KAND_SPALTEN = ("klasse", "asset", "perzentil", "gehalten")
KAND_KOPF = {"klasse": "Klasse", "asset": "Asset (Bitpanda)", "perzentil": "Perzentil", "gehalten": "gehalten"}
KAND_TIPP = {
    "klasse": "Marktwert-Klasse am Stichtag wie B4: H = Rang <= 30 (drei Monate in Folge), M = Rang <= 100, S = Rest.",
    "asset": "Oberes Fünftel des Watchlist-Werts (ohne TVL) in seiner Klasse, bei Bitpanda handelbar. H alle, M und S die besten 10.",
    "perzentil": "Perzentil des Watchlist-Werts in der Zelle Stichtag x Klasse (1,00 = bester). Ordnet den Fortbestand (Spot §25.6), "
                 "ein Einstieg je Asset ist NICHT belegt (E-102).",
    "gehalten": "ja = schon im Bestand (frei + gestakt) - markiert, nicht bevorzugt (O41).",
}


# ══ reine Aufbereitung ══════════════════════════════════════════════════════════════════════════════════════════════════════
def _pct(x) -> str:
    return "–" if x is None else ("%+.1f %%" % (100 * float(x))).replace(".", ",")


def ampel_zeilen(d: dict) -> list:
    """Zeilen der Bedingungen aus ``season_ampel.uebersicht`` -> [(Bedingung, heute, Schwelle, erfuellt, vor 30 T, vor 90 T)]."""
    if not d or not d.get("bedingungen"):
        return []
    v30, v90 = d.get("vor30") or {}, d.get("vor90") or {}
    sp = ("b1", "b2", "b3")
    return [(n, w, s, "✔" if an else "✗", _pct(v30.get(sp[i])), _pct(v90.get(sp[i])))
            for i, (n, w, an, s) in enumerate(d["bedingungen"])]


def ampel_kopf(d: dict) -> str:
    if not d or d.get("zustand") == "fehlt":
        return "Season-Ampel: nicht verfügbar (noch nicht berechnet)"
    seit = d.get("seit")
    return "Season-Ampel: %s · %s von 3%s%s" % (d.get("stufe_name"), d.get("stand"),
                                                 (" · seit %s" % date.fromisoformat(seit).strftime("%d.%m.%Y")) if seit else "",
                                                 " · VERALTET" if d.get("zustand") == "veraltet" else "")


def kontext_text(d: dict) -> str:
    if not d or not d.get("datum"):
        return ""
    teile = ["Stand %s" % date.fromisoformat(d["datum"]).strftime("%d.%m.%Y")]
    if d.get("breite") is not None:
        teile.append("Breite %s (Überhitzung ab 0,60)" % ("%.2f" % d["breite"]).replace(".", ","))
    if d.get("netto13") is not None:
        teile.append("Netto-Liquidität 13 W %s" % _pct(d["netto13"]))
    if d.get("fg") is not None:
        teile.append("Fear & Greed %.0f" % d["fg"])
    return " · ".join(teile)


def makro_zeilen(m: dict) -> list:
    return [tuple(k) for k in (m or {}).get("kanaele") or []]


def gesamt_zeilen(m: dict) -> list:
    """[(Nr, Stichwort, heute, gemessen)] aus ``makro_lage.stand()['gesamtmarkt']`` (L-A)."""
    return [tuple(z) for z in ((m or {}).get("gesamtmarkt") or {}).get("zeilen") or []]


def kandidaten_zeilen(k: dict | None) -> list:
    """[(Klasse, Asset, Perzentil, gehalten)] aus ``spot_abbau.kandidaten``."""
    if not k:
        return []
    aus = []
    for kl in ("H", "M", "S"):
        for bp, pz, geh in (k.get("liste") or {}).get(kl, []):
            aus.append((kl, bp, ("%.2f" % pz).replace(".", ","), "ja" if geh else ""))
    return aus


def verlauf(d_lade: dict | None) -> list:
    """[(datum, stand, stufe)] der letzten 12 Monate."""
    return [(r[0], r[2], r[1]) for r in ((d_lade or {}).get("verlauf") or [])]


# ══ die Reiter ══════════════════════════════════════════════════════════════════════════════════════════════════════════════
class _Basis(ttk.Frame):
    def __init__(self, parent, notebook: ttk.Notebook):
        super().__init__(parent, padding=8)
        self._notebook = notebook
        self._zuletzt = -1e9
        from agent import regel0_nachlader as NL
        self._ordner = NL.DATEN_VORGABE

    def _sichtbar(self) -> bool:
        try:
            return self.winfo_ismapped() and self._notebook.nametowidget(self._notebook.select()) is self
        except (tk.TclError, KeyError):
            return False

    def refresh(self, erzwingen: bool = False) -> None:
        jetzt = time.monotonic()
        if not erzwingen and (jetzt - self._zuletzt < LANGSAM_S or not self._sichtbar()):
            return
        self._zuletzt = jetzt
        try:
            self._neu()
        except Exception:                                   # noqa: BLE001
            logger.exception("%s: Anzeige nicht aufgebaut", type(self).__name__)


class MarktKryptoTab(_Basis):
    """Reiter 4 *Markt (Krypto)*: Season-Ampel und Makro-Lage als Fakt."""

    def __init__(self, parent, notebook: ttk.Notebook):
        super().__init__(parent, notebook)
        leiste = ttk.Frame(self)
        leiste.pack(fill="x")
        ttk.Button(leiste, text="Aktualisieren", command=lambda: self.refresh(erzwingen=True)).pack(side="left")
        self.kopf = ttk.Label(leiste, text="Season-Ampel: -", font=("", 12, "bold"))
        self.kopf.pack(side="left", padx=(12, 0))
        self.bedeutung = ttk.Label(self, text="", foreground=theme.info_color(), wraplength=1100, justify="left")
        self.bedeutung.pack(anchor="w", pady=(4, 2))
        self.ampel_tree = ttk.Treeview(self, columns=AMPEL_SPALTEN, show="headings", height=3)
        for c in AMPEL_SPALTEN:
            self.ampel_tree.heading(c, text=AMPEL_KOPF[c])
            self.ampel_tree.column(c, width=230 if c == "bedingung" else 110, anchor="w" if c == "bedingung" else "center")
        add_heading_tooltips(self.ampel_tree, AMPEL_TIPP)
        self.ampel_tree.pack(fill="x")
        self.kontext = ttk.Label(self, text="", foreground=theme.info_color())
        self.kontext.pack(anchor="w", pady=(4, 0))
        self.vorbehalt = ttk.Label(self, text="⚠ Geprüft an zwei Zyklen (2017/18, 2020/21) – trennt Season-Phase und Bärenmarkt, erkennt den "
                                              "Beginn nicht genau vorab. Mail beim Stufenwechsel mit Handlung (Schalter season_ampel_aktiv).",
                                   foreground=theme.info_color(), wraplength=1100, justify="left")
        self.vorbehalt.pack(anchor="w", pady=(2, 6))
        self.grafik = ttk.Frame(self)
        self.grafik.pack(fill="x")
        self._canvas = None
        ttk.Label(self, text="Makro-Lage (O54)", font=("", 11, "bold")).pack(anchor="w", pady=(8, 0))
        self.makro_zeile = ttk.Label(self, text="", foreground=theme.info_color(), wraplength=1100, justify="left")
        self.makro_zeile.pack(anchor="w")
        self.makro_tree = ttk.Treeview(self, columns=MAKRO_SPALTEN, show="headings", height=9)
        for c in MAKRO_SPALTEN:
            self.makro_tree.heading(c, text=MAKRO_KOPF[c])
            self.makro_tree.column(c, width=260 if c == "kanal" else 140, anchor="w" if c == "kanal" else "center")
        add_heading_tooltips(self.makro_tree, MAKRO_TIPP)
        self.makro_tree.pack(fill="x", pady=(2, 0))
        ttk.Label(self, text="Lagebild Gesamtmarkt (L-A)", font=("", 11, "bold")).pack(anchor="w", pady=(8, 0))
        self.gesamt_zeile = ttk.Label(self, text="", foreground=theme.info_color(), wraplength=1100, justify="left")
        self.gesamt_zeile.pack(anchor="w")
        self.gesamt_tree = ttk.Treeview(self, columns=GESAMT_SPALTEN, show="headings", height=6)
        for c, b in zip(GESAMT_SPALTEN, (40, 170, 420, 520)):
            self.gesamt_tree.heading(c, text=GESAMT_KOPF[c])
            self.gesamt_tree.column(c, width=b, anchor="w")
        add_heading_tooltips(self.gesamt_tree, GESAMT_TIPP)
        self.gesamt_tree.pack(fill="x", pady=(2, 0))
        self.lauf = ttk.Label(self, text="", foreground=theme.info_color())
        self.lauf.pack(anchor="w", pady=(6, 0))

    def _neu(self) -> None:
        from agent import makro_lage as ML
        from agent import season_ampel as SA

        d = SA.uebersicht(self._ordner)
        self.kopf.configure(text=ampel_kopf(d))
        self.bedeutung.configure(text=d.get("bedeutung") or d.get("zeile") or "")
        self.ampel_tree.delete(*self.ampel_tree.get_children())
        for z in ampel_zeilen(d):
            self.ampel_tree.insert("", "end", values=z)
        self.kontext.configure(text=kontext_text(d))
        l = d.get("lauf") or {}
        self.lauf.configure(text=("letzter Lauf %s · %s%s" % (l.get("am"), l.get("status"), (" · " + l["fehler"]) if l.get("fehler") else ""))
                            if l else "noch kein Lauf (Job season_ampel, täglich 07:30)")
        self._zeichne(verlauf(SA.lade(self._ordner)))
        m = ML.stand()
        self.makro_zeile.configure(text=m.get("zeile") or "")
        self.makro_tree.delete(*self.makro_tree.get_children())
        for z in makro_zeilen(m):
            self.makro_tree.insert("", "end", values=z)
        self.gesamt_zeile.configure(text=((m.get("gesamtmarkt") or {}).get("zeile")) or "")
        self.gesamt_tree.delete(*self.gesamt_tree.get_children())
        for z in gesamt_zeilen(m):
            self.gesamt_tree.insert("", "end", values=z)

    def _zeichne(self, vl: list) -> None:
        if self._canvas is not None:
            self._canvas.get_tk_widget().destroy()
            self._canvas = None
        if not vl:
            return
        import pandas as pd
        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
        from matplotlib.figure import Figure

        x = pd.to_datetime([r[0] for r in vl])
        fig = Figure(figsize=(11, 1.8), dpi=90)
        ax = fig.add_subplot(111)
        ax.step(x, [r[1] for r in vl], where="post", linewidth=1.4)
        ax.set_ylim(-0.3, 3.3)
        ax.set_yticks([0, 1, 2, 3])
        ax.set_ylabel("Stand")
        alt = None
        for xi, (_d, _s, st) in zip(x, vl):
            if st != alt:
                ax.axvline(xi, color="0.75", linewidth=0.6)
                ax.text(xi, 3.05, st, fontsize=7, va="bottom")
                alt = st
        ax.set_title("Season-Ampel, letzte 12 Monate (Stand 0-3, Stufe nach Haltezeit 7 T)", fontsize=9)
        fig.tight_layout()
        self._canvas = FigureCanvasTkAgg(fig, master=self.grafik)
        self._canvas.draw()
        self._canvas.get_tk_widget().pack(fill="x")


class SpotTab(_Basis):
    """Reiter 3 *Spot*: Einstiegs-Kandidaten (A3) mit der Ampel als Kopf."""

    def __init__(self, parent, notebook: ttk.Notebook):
        super().__init__(parent, notebook)
        leiste = ttk.Frame(self)
        leiste.pack(fill="x")
        ttk.Button(leiste, text="Aktualisieren", command=lambda: self.refresh(erzwingen=True)).pack(side="left")
        self.kopf = ttk.Label(leiste, text="Einstiegs-Kandidaten", font=("", 12, "bold"))
        self.kopf.pack(side="left", padx=(12, 0))
        self.ampel = ttk.Label(self, text="", foreground=theme.info_color(), wraplength=1100, justify="left")
        self.ampel.pack(anchor="w", pady=(4, 2))
        self.hinweis = ttk.Label(self, text="Ordnet den Fortbestand (Spot §25.6/§39.9) – ein Einstieg je Asset ist NICHT belegt. Zur "
                                            "Handlung werden die Kandidaten erst mit der Ampel-Stufe Vorlauf oder Season-Klima.",
                                 foreground=theme.info_color(), wraplength=1100, justify="left")
        self.hinweis.pack(anchor="w", pady=(0, 6))
        self.tree = ttk.Treeview(self, columns=KAND_SPALTEN, show="headings", height=24)
        for c in KAND_SPALTEN:
            self.tree.heading(c, text=KAND_KOPF[c])
            self.tree.column(c, width=200 if c == "asset" else 110, anchor="w" if c == "asset" else "center")
        self._sort = make_sortable(self.tree)
        add_heading_tooltips(self.tree, KAND_TIPP)
        self.tree.pack(fill="both", expand=True)

    def _neu(self) -> None:
        from agent import season_ampel as SA
        from agent import spot_abbau as AB

        self.ampel.configure(text="Season-Ampel: " + SA.zeile(self._ordner))
        k = AB.kandidaten(self._ordner)
        self.kopf.configure(text=("Einstiegs-Kandidaten · Stichtag %s · %d handelbar (von %d im oberen Fünftel)" % (
            k["stichtag"], k["anzahl"], k["oben_gesamt"])) if k else "Einstiegs-Kandidaten · ab dem nächsten B4-Stichtag")
        self.tree.delete(*self.tree.get_children())
        for z in kandidaten_zeilen(k):
            self.tree.insert("", "end", values=z)
