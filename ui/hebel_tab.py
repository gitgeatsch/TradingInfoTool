"""Der Hebel-Tab des NEUEN Systems (P12 / GUI-2, 11.10.2026, Plan_Asset_Lebenszyklus_14_09.md G-V).

Nutzer 11.10.: *"1. bis GUI-4 doppelt lassen 2. aus der GUI entfernen"* - der Hebel-Schalter steht hier UND bis GUI-4 weiter in
der Watchlist; der alte Hebel-Tab (`ui/hebel_view.py`: Altlisten der alten Kette und der Rollen-Kette, Kandidaten, gesperrter
Knopf *Jetzt analysieren*, Signal-Historie `hebel_signals`) ist aus der GUI genommen - der Code bleibt.

DREI BEREICHE:
  Signale (REGEL0)   ALLE Signale der Ablage, Filter heute / 7 Tage / alle und nur Schalter an / alle; Detail = Mailtext + Pruefblock
                     + Mailstand (`agent/regel0_ansicht.detail`, eine Quelle mit der Mail), Signalchart, Knoepfe Wochen-/Tageschart (O45)
  Positionen (H15)   je offener Position Kurs, Liquidation, Abstand, H15-Empfehlung, Finanzierung, Ergebnis (`hebelfuehrung.lade`) und
                     der Abgleich mit Bitpanda (P11, `betriebslage.hebel_wallet_abgleich`)
  Freigabe je Asset  alle Krypto-Assets mit Hebel-Schalter an/aus, REGEL0-Daten vorhanden?, letztes Signal; Knopf *Schalter umschalten*
                     (dieselbe `db.set_hebel_pruefung_erlaubt` wie die Watchlist, GF2)

LAUFZEIT: die App ruft ``refresh()`` alle 3 s. Die Signale lesen die kleine Ablage (mode=ro). Positionen und Freigabe rechnen H15 bzw.
lesen die Kursdateien - sie laufen nur, wenn ihr Bereich SICHTBAR ist, hoechstens alle ``LANGSAM_S`` Sekunden (Knopf *Aktualisieren*
erzwingt es). Das Lesen schreibt nichts; geschrieben wird nur beim Umschalten eines Schalters.

Die Aufbereitung steht in reinen Funktionen (``signal_zeilen``, ``positions_zeilen``, ``freigabe_zeilen``) - Pruefstand und Gegenprobe
pruefen sie ohne Fenster.
"""
from __future__ import annotations

import base64
import logging
import os
import sqlite3
import time
import tkinter as tk
from datetime import datetime, timedelta, timezone
from tkinter import messagebox, ttk

import database.db as db
import ui.theme as theme
from ui.detail_panel import configure_tags, render_detail_text
from ui.formatting import format_money
from ui.heading_tooltip import add_heading_tooltips
from ui.sortable_tree import make_sortable

logger = logging.getLogger(__name__)

LANGSAM_S = 60
FILTER_ZEIT = ("heute", "7_tage", "alle")
URTEIL_WORT = {"stuetzt": "stützt", "spricht_dagegen": "spricht dagegen", "neutral": "neutral", "uneinig": "uneinig"}

SIGNAL_SPALTEN = ("asset", "signal", "stufe", "status", "gemailt", "trader", "ausstieg")
SIGNAL_KOPF = {"asset": "Asset", "signal": "Signal (Ortszeit)", "stufe": "Stufe", "status": "Status", "gemailt": "gemailt",
               "trader": "Trader", "ausstieg": "Ausstieg"}
SIGNAL_TIPP = {
    "signal": "Schluss der Signalstunde in Ortszeit - ab da stand das Signal fest.",
    "stufe": "Hebelstufe: endgueltig, sonst vorlaeufig (die endgueltige steht nach dem naechsten Lauf fest).",
    "status": "Stand aus den Zeiten der Zeile: Einstieg, laeuft, Ausstieg faellig, beendet, kein Handel, nicht gemailt.",
    "gemailt": "Wann die Signalmail rausging - leer: keine Mail (Schalter aus, Zuordnung, verpasst oder Stufe 0).",
    "trader": "Urteil der Trader-Rolle im Pruefblock (5 Stimmen) - Auskunft, loest nichts aus.",
    "ausstieg": "Schluss der Ausstiegsstunde in Ortszeit (24 h nach dem Einstieg).",
}
POS_SPALTEN = ("asset", "richtung", "hebel", "ek", "kurs", "liq", "abstand", "empfehlung", "fin", "ergebnis", "regel0")
POS_KOPF = {"asset": "Asset", "richtung": "Richtung", "hebel": "Hebel", "ek": "Eigenkapital", "kurs": "Kurs (EUR)", "liq": "Liquidation",
            "abstand": "Abstand", "empfehlung": "H15-Empfehlung", "fin": "Finanzierung bisher / Tag", "ergebnis": "Ergebnis netto",
            "regel0": "REGEL0"}
POS_TIPP = {
    "abstand": "Abstand Kurs -> geschaetzte Liquidation in Prozent des Kurses. Warnstufen ab 15 % (H15).",
    "empfehlung": "Hebelfuehrung H15: LIQUIDIERT > SCHLIESSEN > HEBEL SENKEN > LIQUIDATION NAHE > KURS FEHLT > STOP NACHZIEHEN > HALTEN.",
    "fin": "Finanzierungskosten des Kredits seit Eroeffnung und je Tag (Bitpanda-Satz).",
    "ergebnis": "Ergebnis zum aktuellen Kurs abzueglich der bisherigen Finanzierung - ohne Gebuehren (Regel 2).",
}
FREI_SPALTEN = ("asset", "schalter", "daten", "letztes")
FREI_KOPF = {"asset": "Asset", "schalter": "Hebel-Schalter", "daten": "REGEL0-Daten", "letztes": "letztes REGEL0-Signal"}
FREI_TIPP = {
    "schalter": "Nur mit Schalter AN wird ein REGEL0-Signal gemailt (Opt-in). Offene Positionen werden unabhaengig davon gefuehrt (H15).",
    "daten": "Hat die REGEL0 Stundenkurse fuer dieses Asset (da / keine)? FEHLEN = Schalter an, aber keine Kurse - dann kommt kein Signal.",
}


# ══ reine Aufbereitung ══════════════════════════════════════════════════════════════════════════════════════════════════════
def _lokal(dt: datetime | None) -> str:
    return dt.astimezone().strftime("%d.%m. %H:%M") if dt else "-"


def _ende(txt: str | None) -> datetime | None:
    if not txt:
        return None
    return datetime.strptime(txt[:16], "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc) + timedelta(hours=1)


def _zeit_iso(txt: str | None) -> datetime | None:
    if not txt:
        return None
    try:
        return datetime.fromisoformat(str(txt).replace("Z", "+00:00").replace(" ", "T")[:19]).replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def trader_urteile(ordner: str) -> dict:
    """{(symbol, signalstunde): Urteil-Text} aus der Pruefblock-Tabelle (mode=ro); die juengste Fassung je Signal."""
    import agent.regel0_ablage as AB

    p = os.path.join(ordner, AB.ABLAGE_NAME)
    if not os.path.exists(p):
        return {}
    c = sqlite3.connect("file:%s?mode=ro" % p.replace("\\", "/"), uri=True, timeout=10)
    try:
        if not c.execute("SELECT 1 FROM sqlite_master WHERE name='pruefung'").fetchone():
            return {}
        aus = {}
        for sym, st, urteil, fehler in c.execute("SELECT symbol, signalstunde, urteil, fehler FROM pruefung WHERE rolle='trader' "
                                                  "ORDER BY am"):
            aus[(sym, st)] = URTEIL_WORT.get(urteil, urteil) if urteil else ("(%s)" % ("Fehler" if fehler else "nicht gefragt"))
        return aus
    finally:
        c.close()


def signal_zeilen(rows: list, jetzt: datetime, zeit: str = "7_tage", nur_an: bool = True, urteile: dict | None = None) -> list:
    """Die Liste: juengste zuerst. ``zeit``: heute (Ortskalendertag der Signalstunde) / 7_tage / alle. ``nur_an``: nur Assets mit
    Hebel-Schalter AN zum Zeitpunkt des Signals (Spalte ``hebel_schalter`` der Ablage - derselbe Wert, der das Mailen erlaubt)."""
    from agent import regel0_ansicht as R0A

    urteile = urteile or {}
    heute = jetzt.astimezone().date()
    aus = []
    for r in sorted(rows, key=lambda x: x["signalstunde"], reverse=True):
        ende = _ende(r["signalstunde"])
        if zeit == "heute" and ende.astimezone().date() != heute:
            continue
        if zeit == "7_tage" and ende < jetzt - timedelta(days=7):
            continue
        if nur_an and r.get("hebel_schalter") != 1:
            continue
        gem = _zeit_iso(r.get("mail_signal_am"))
        aus.append({"key": "%s|%s" % (r["symbol"], r["signalstunde"]), "r": r,
                    "werte": (R0A.name(r), _lokal(ende), R0A.hebel_text(r), R0A.status(r, jetzt), _lokal(gem) if gem else "-",
                              urteile.get((r["symbol"], r["signalstunde"]), "-"), _lokal(_ende(r.get("ausstieg"))))})
    return aus


def positions_zeilen(trades: list, regel0_rows: list) -> list:
    """Je offener Position eine Zeile aus der H15-Fuehrung (``hebelfuehrung.lade``)."""
    from agent import regel0_ansicht as R0A

    aus = []
    for t in trades:
        a = t.get("abstand_liquidation")
        fin = (t.get("finanzierung_bisher_eur"), t.get("finanzierung_je_tag_eur"))
        aus.append({"t": t, "werte": (
            t.get("symbol"), t.get("richtung"), ("%.1fx" % t["hebel"]) if t.get("hebel") else "-", format_money(t.get("eigenkapital_eur")),
            format_money(t.get("kurs_eur")), format_money(t.get("liquidation_eur")), ("%.1f %%" % (100 * a)) if a is not None else "-",
            str(t.get("empfehlung") or "-") + ((" (Stufe %d %%)" % round(100 * t["nahe_stufe"])) if t.get("nahe_stufe") else ""),
            ("%s / %s" % (format_money(fin[0]), format_money(fin[1]))) if fin[0] is not None else "-",
            format_money(t.get("ergebnis_netto_eur")),
            R0A.positions_vermerk(t.get("symbol"), t.get("richtung"), t.get("eroeffnet_am"), regel0_rows) or "-")})
    return aus


def freigabe_zeilen(watchlist: list, schalter: dict, mit_daten: set | None, regel0_rows: list) -> list:
    """Alle Krypto-Assets der Watchlist (ohne Stablecoins) plus jedes Asset mit eigener Schalterzeile. ``mit_daten``: die Namen MIT
    REGEL0-Kursen (``betriebslage.mit_regel0_daten``) - fuer ALLE Assets geprueft, nicht nur die mit Schalter an; None = nicht pruefbar.
    Spalte: da / keine, bei Schalter AN ohne Daten FEHLEN (dann kann kein Signal kommen)."""
    from agent import regel0_ansicht as R0A

    namen = {a.symbol for a in watchlist if getattr(a, "assetklasse", None) == "krypto" and not getattr(a, "ist_cash_aequivalent", False)}
    namen |= set(schalter)
    letztes = {}
    for r in regel0_rows:
        n = R0A.name(r)
        if n not in letztes or r["signalstunde"] > letztes[n]:
            letztes[n] = r["signalstunde"]
    aus = []
    for n in sorted(namen):
        an = schalter.get(n, False)
        if mit_daten is None:
            daten = "?"
        elif n in mit_daten:
            daten = "da"
        else:
            daten = "FEHLEN" if an else "keine"
        aus.append({"asset": n, "an": an, "werte": (n, "AN" if an else "aus", daten, _lokal(_ende(letztes.get(n))) if n in letztes else "-")})
    return aus


# ══ die Ansicht ═════════════════════════════════════════════════════════════════════════════════════════════════════════════
class HebelTab(ttk.Frame):
    def __init__(self, parent, db_conn_factory, watchlist: list, regel0_ordner: str | None = None) -> None:
        super().__init__(parent)
        from agent import regel0_ansicht as R0A

        self._conn_factory = db_conn_factory
        self._watchlist = watchlist
        self._ordner = regel0_ordner or R0A.ORDNER_VORGABE
        self._zeit_var = tk.StringVar(value="7_tage")
        self._nur_an_var = tk.BooleanVar(value=True)
        self._regel0_rows: list = []
        self._signal_by_iid: dict = {}
        self._frei_by_iid: dict = {}
        self._zuletzt_langsam = 0.0
        self._bilder = []
        self._signal_stand = None          # was zuletzt in der Liste stand - unveraendert -> nichts neu zeichnen
        self._frei_stand = None
        self._still = False                # Auswahl wird wiederhergestellt -> kein Neuzeichnen des Details
        self._bauen()
        self.refresh(erzwingen=True)

    # ---- Aufbau ----
    def _bauen(self) -> None:
        self._nb = ttk.Notebook(self)
        self._nb.pack(fill="both", expand=True, padx=6, pady=6)
        self._nb.bind("<<NotebookTabChanged>>", lambda _e: self.refresh(erzwingen=True))

        # Signale
        sig = ttk.Frame(self._nb)
        self._nb.add(sig, text="Signale (REGEL0)")
        leiste = ttk.Frame(sig)
        leiste.pack(fill="x", pady=(0, 4))
        ttk.Label(leiste, text="Zeitraum:", foreground=theme.info_color()).pack(side="left", padx=(0, 4))
        for wert, text in (("heute", "heute"), ("7_tage", "7 Tage"), ("alle", "alle")):
            ttk.Radiobutton(leiste, text=text, value=wert, variable=self._zeit_var, command=self._signale_neu).pack(side="left")
        ttk.Checkbutton(leiste, text="nur Hebel-Schalter an", variable=self._nur_an_var, command=self._signale_neu).pack(side="left", padx=(16, 0))
        self.signal_status = ttk.Label(leiste, text="", foreground=theme.info_color())
        self.signal_status.pack(side="left", padx=(16, 0))
        paned = ttk.Panedwindow(sig, orient="horizontal")
        paned.pack(fill="both", expand=True)
        links = ttk.Frame(paned)
        paned.add(links, weight=2)
        self.signal_tree = ttk.Treeview(links, columns=SIGNAL_SPALTEN, show="headings", height=18)
        for c in SIGNAL_SPALTEN:
            self.signal_tree.heading(c, text=SIGNAL_KOPF[c])
            self.signal_tree.column(c, width=150 if c == "status" else 105, anchor="w" if c in ("asset", "status") else "center")
        self._sig_sort = make_sortable(self.signal_tree)
        add_heading_tooltips(self.signal_tree, SIGNAL_TIPP)
        self.signal_tree.pack(fill="both", expand=True)
        self.signal_tree.bind("<<TreeviewSelect>>", self._signal_gewaehlt)
        rechts = ttk.Frame(paned)
        paned.add(rechts, weight=3)
        knoepfe = ttk.Frame(rechts)
        knoepfe.pack(fill="x")
        self.knopf_woche = ttk.Button(knoepfe, text="Wochenchart", state="disabled", command=lambda: self._chart("W"))
        self.knopf_woche.pack(side="left")
        self.knopf_tag = ttk.Button(knoepfe, text="Tageschart", state="disabled", command=lambda: self._chart("D"))
        self.knopf_tag.pack(side="left", padx=(8, 0))
        self.titel = ttk.Label(rechts, text="Keine Auswahl", font=("", 13, "bold"))
        self.titel.pack(anchor="w", pady=(6, 0))
        self.meta = ttk.Label(rechts, text="", foreground=theme.info_color())
        self.meta.pack(anchor="w", pady=(0, 6))
        self.detail_text = tk.Text(rechts, height=28, wrap="word", state="disabled", relief="flat")
        self.detail_text.pack(fill="both", expand=True)
        configure_tags(self.detail_text)

        # Positionen
        pos = ttk.Frame(self._nb)
        self._nb.add(pos, text="Positionen (H15)")
        pl = ttk.Frame(pos)
        pl.pack(fill="x", pady=(0, 4))
        ttk.Button(pl, text="Aktualisieren", command=lambda: self.refresh(erzwingen=True)).pack(side="left")
        self.pos_status = ttk.Label(pl, text="", foreground=theme.info_color())
        self.pos_status.pack(side="left", padx=(12, 0))
        self.pos_tree = ttk.Treeview(pos, columns=POS_SPALTEN, show="headings", height=8)
        for c in POS_SPALTEN:
            self.pos_tree.heading(c, text=POS_KOPF[c])
            self.pos_tree.column(c, width=200 if c in ("empfehlung", "fin", "regel0") else 95,
                                 anchor="w" if c in ("asset", "empfehlung", "regel0") else "center")
        add_heading_tooltips(self.pos_tree, POS_TIPP)
        self.pos_tree.pack(fill="x")
        self.pos_tree.bind("<<TreeviewSelect>>", self._position_gewaehlt)
        self.abgleich = ttk.Label(pos, text="", font=("", 10, "bold"))
        self.abgleich.pack(anchor="w", pady=(8, 2))
        self.abgleich_zeile = ttk.Label(pos, text="", foreground=theme.info_color(), wraplength=1100, justify="left")
        self.abgleich_zeile.pack(anchor="w")
        self.pos_text = tk.Text(pos, height=16, wrap="word", state="disabled", relief="flat")
        self.pos_text.pack(fill="both", expand=True, pady=(8, 0))
        configure_tags(self.pos_text)

        # Freigabe
        fr = ttk.Frame(self._nb)
        self._nb.add(fr, text="Freigabe je Asset")
        fl = ttk.Frame(fr)
        fl.pack(fill="x", pady=(0, 4))
        ttk.Button(fl, text="Schalter umschalten", command=self._umschalten).pack(side="left")
        ttk.Button(fl, text="Aktualisieren", command=lambda: self.refresh(erzwingen=True)).pack(side="left", padx=(8, 0))
        self.frei_status = ttk.Label(fl, text="Nur mit Schalter AN wird ein REGEL0-Signal gemailt. Derselbe Schalter steht bis GUI-4 "
                                              "auch in der Watchlist.", foreground=theme.info_color())
        self.frei_status.pack(side="left", padx=(12, 0))
        self.frei_tree = ttk.Treeview(fr, columns=FREI_SPALTEN, show="headings", height=22)
        for c in FREI_SPALTEN:
            self.frei_tree.heading(c, text=FREI_KOPF[c])
            self.frei_tree.column(c, width=160, anchor="w" if c == "asset" else "center")
        self._frei_sort = make_sortable(self.frei_tree)
        add_heading_tooltips(self.frei_tree, FREI_TIPP)
        self.frei_tree.pack(fill="both", expand=True)

    # ---- Lesen ----
    def _sichtbar(self, index: int) -> bool:
        try:
            return self.winfo_ismapped() and self._nb.index(self._nb.select()) == index
        except tk.TclError:
            return False

    def refresh(self, erzwingen: bool = False) -> None:
        """Signale immer (kleine Ablage); Positionen und Freigabe nur sichtbar und hoechstens alle LANGSAM_S Sekunden."""
        from agent import regel0_ansicht as R0A

        try:
            self._regel0_rows = R0A.lese(self._ordner)
        except Exception:                                   # noqa: BLE001
            logger.exception("Hebel-Tab: REGEL0-Ablage nicht lesbar")
            self._regel0_rows = []
        self._signale_neu()
        jetzt = time.monotonic()
        if erzwingen or jetzt - self._zuletzt_langsam >= LANGSAM_S:
            if erzwingen or self._sichtbar(1):
                self._positionen_neu()
            if erzwingen or self._sichtbar(2):
                self._freigabe_neu()
            self._zuletzt_langsam = jetzt

    def _schalter(self) -> dict:
        conn = self._conn_factory()
        try:
            return db.get_hebel_pruefung_toggle_map(conn)
        finally:
            conn.close()

    def _signale_neu(self) -> None:
        jetzt = datetime.now(timezone.utc)
        try:
            urteile = trader_urteile(self._ordner)
        except Exception:                                   # noqa: BLE001
            urteile = {}
        zeilen = signal_zeilen(self._regel0_rows, jetzt, self._zeit_var.get(), bool(self._nur_an_var.get()), urteile)
        stand = tuple((z["key"], z["werte"]) for z in zeilen)
        if stand == self._signal_stand:          # alle 3 s gerufen: unveraendert -> Liste, Sortierung und Auswahl bleiben stehen
            return
        self._signal_stand = stand
        auswahl = self.signal_tree.selection()
        alt = auswahl[0] if auswahl else None
        self.signal_tree.delete(*self.signal_tree.get_children())
        self._signal_by_iid = {}
        for z in zeilen:
            iid = self.signal_tree.insert("", "end", iid=z["key"], values=z["werte"])
            self._signal_by_iid[iid] = z["r"]
        self._sig_sort()
        if alt and alt in self._signal_by_iid:
            self._still = True
            self.signal_tree.selection_set(alt)
            self.after_idle(lambda: setattr(self, "_still", False))
        gemailt = sum(1 for z in zeilen if z["r"].get("mail_signal_am"))
        self.signal_status.config(text="%d Signale, %d gemailt · Ablage: %d gesamt" % (len(zeilen), gemailt, len(self._regel0_rows)))

    def _positionen_neu(self) -> None:
        from agent import betriebslage as BL
        from agent import hebelfuehrung as HF
        from agent import regel0_groesse as G

        conn = self._conn_factory()
        try:
            trades = HF.lade(conn, nahe_grenze=float(G.lade().get("liquidations_warnung_abstand") or HF.LIQ_NAHE_GRENZE))
            abg = BL.hebel_wallet_abgleich(conn)
        except Exception as exc:                            # noqa: BLE001
            logger.exception("Hebel-Tab: Positionen nicht lesbar")
            self.pos_status.config(text="Positionen nicht lesbar: %s" % type(exc).__name__, foreground=theme.warn_color())
            return
        finally:
            conn.close()
        self.pos_tree.delete(*self.pos_tree.get_children())
        self._pos_by_iid = {}
        zeilen = positions_zeilen(trades, self._regel0_rows)
        if not zeilen:
            self.pos_tree.insert("", "end", values=("Keine offenen Positionen",) + ("-",) * (len(POS_SPALTEN) - 1))
        for i, z in enumerate(zeilen):
            iid = self.pos_tree.insert("", "end", values=z["werte"])
            self._pos_by_iid[iid] = z["t"]
        ok = abg.get("ok")
        self.abgleich.config(text="Abgleich mit Bitpanda (Wallets): " + ("stimmt" if ok else ("nicht prüfbar" if abg.get("fehlt") else "WEICHT AB")),
                             foreground=theme.success_color() if ok else theme.danger_color())
        self.abgleich_zeile.config(text=abg.get("zeile") or "")
        self.pos_status.config(text="Stand %s · %d offen" % (datetime.now().strftime("%H:%M:%S"), len(zeilen)),
                               foreground=theme.info_color())

    def _freigabe_neu(self) -> None:
        from agent import betriebslage as BL

        schalter = self._schalter()
        namen = {a.symbol for a in self._watchlist} | set(schalter)
        try:
            mit = BL.mit_regel0_daten(namen, self._ordner)
        except Exception:                                   # noqa: BLE001
            mit = None
        zeilen = freigabe_zeilen(self._watchlist, schalter, mit, self._regel0_rows)
        stand = tuple(z["werte"] for z in zeilen)
        if stand == self._frei_stand:
            return
        self._frei_stand = stand
        auswahl = self.frei_tree.selection()
        alt = self._frei_by_iid.get(auswahl[0]) if auswahl else None
        self.frei_tree.delete(*self.frei_tree.get_children())
        self._frei_by_iid = {}
        for z in zeilen:
            iid = self.frei_tree.insert("", "end", iid="frei|" + z["asset"], values=z["werte"])
            self._frei_by_iid[iid] = z["asset"]
        self._frei_sort()
        if alt and ("frei|" + alt) in self._frei_by_iid:
            self.frei_tree.selection_set("frei|" + alt)

    # ---- Auswahl und Knoepfe ----
    def _signal_gewaehlt(self, _e=None) -> None:
        from agent import regel0_ansicht as R0A

        if self._still:
            return
        sel = self.signal_tree.selection()
        r = self._signal_by_iid.get(sel[0]) if sel else None
        if r is None:
            return
        self._gewaehlt = r
        titel, meta, text = R0A.detail(r, self._regel0_rows, datetime.now(timezone.utc), pruefzeilen=R0A.pruefung_zeilen(self._ordner, r))
        self.titel.config(text=titel, foreground=theme.action_color("KAUFEN"))
        self.meta.config(text=meta)
        render_detail_text(self.detail_text, text)
        self.knopf_woche.config(state="normal")
        self.knopf_tag.config(state="normal")
        try:                                                # dasselbe Bild wie in der Signalmail (E-50 N-f)
            from agent import regel0_chart as CH
            png = CH.bild(r, self._ordner)
            if png:
                self._bild_einsetzen(self.detail_text, png)
        except Exception:                                   # noqa: BLE001
            logger.exception("Hebel-Tab: Signalchart nicht darstellbar")

    def _bild_einsetzen(self, text_widget, png: bytes) -> None:
        bild = tk.PhotoImage(data=base64.b64encode(png).decode("ascii"))
        self._bilder = self._bilder[-5:] + [bild]
        text_widget.config(state="normal")
        text_widget.insert("end", "\n\n")
        text_widget.image_create("end", image=bild)
        text_widget.config(state="disabled")

    def _chart(self, ebene: str) -> None:
        """O45: Wochen- bzw. Tageschart (Kerzen, RSI 14, MACD 12/26/9) - dieselbe Funktion wie in der Signalmail."""
        r = getattr(self, "_gewaehlt", None)
        if r is None:
            return
        from agent import indikator_chart as IC

        png = IC.bild(self._ordner, r["symbol"], ebene, r.get("bitpanda") or r["symbol"])
        if not png:
            messagebox.showinfo("Chart", "Keine abgeschlossenen Kerzen fuer %s." % (r.get("bitpanda") or r["symbol"]))
            return
        fenster = tk.Toplevel(self)
        fenster.title("%s - %s" % (r.get("bitpanda") or r["symbol"], IC.EBENEN[ebene]["name"]))
        bild = tk.PhotoImage(data=base64.b64encode(png).decode("ascii"))
        self._bilder = self._bilder[-5:] + [bild]
        ttk.Label(fenster, image=bild).pack()

    def _position_gewaehlt(self, _e=None) -> None:
        from agent import hebelfuehrung as HF

        sel = self.pos_tree.selection()
        t = getattr(self, "_pos_by_iid", {}).get(sel[0]) if sel else None
        if t is None:
            return
        try:
            text = "\n".join(HF.zeilen(t))
        except Exception:                                   # noqa: BLE001
            text = str(t.get("gruende") or "")
        render_detail_text(self.pos_text, text)

    def _umschalten(self) -> None:
        """GF2: derselbe Schreibweg wie die Watchlist (``db.set_hebel_pruefung_erlaubt``) - genau eine Zeile in asset_hebel_settings."""
        sel = self.frei_tree.selection()
        sym = self._frei_by_iid.get(sel[0]) if sel else None
        if not sym:
            messagebox.showinfo("Hebel-Schalter", "Bitte zuerst ein Asset in der Liste auswählen.")
            return
        conn = self._conn_factory()
        try:
            neu = not db.get_hebel_pruefung_erlaubt(conn, sym)
            db.set_hebel_pruefung_erlaubt(conn, sym, neu)
        finally:
            conn.close()
        self.frei_status.config(text="%s: Hebel-Schalter jetzt %s." % (sym, "AN" if neu else "aus"), foreground=theme.info_color())
        self._freigabe_neu()
