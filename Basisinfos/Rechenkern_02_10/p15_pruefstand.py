"""P15 GUI-3 Bestand-Tab (12.10.2026, Plan_Asset_Lebenszyklus G-Y) - Pruefstand: die View EINZELN (Tk unsichtbar) gegen eine Wegwerf-
KOPIE der NB-Sicherung, B1-Ablage aus spot_mitnahme.lauf, B3-Ablage aus spot_upbit.lauf (KRW-Liste gestellt). Die GUI wird NICHT ueber
main.py gestartet (Projektregel).

    python Basisinfos/Rechenkern_02_10/p15_pruefstand.py <NB-Sicherung tradinginfotool.db>

  P1  eine Zeile je Bestand mit frei + gestakt > 0 (47), Schluessel = Symbol
  P2  Rolle: Kern 3 · L 27 · Cash 1 · andere Klassen 15 · nicht in Watchlist 1 (Desktop-Watchlist)
  P3  B1 fuer jeden L-Bestand mit Fenster: x Start, Fenster bis, Status; Nicht-L '-'
  P4  Upbit KRW fuer L: 'nein' genau fuer den Kreis ohne KRW, sonst 'ja'; Nicht-L '-'
  P5  Hebel kurz = hebelfuehrung.lade (Symbole, Abstand)
  P6  Gesamtwert = frei + gestakt + Fiat + Hebel-Eigenkapital, die Teile in der Zeile
  P7  KEIN Knopf 'Letzte Bewertung' im Tab (Widgetbaum); geerbt: Doppelklick, Fiat-Feld, Diversifikation
  P8  ui/app.py haengt BestandTab als 'Bestand' ein, PortfolioView nicht mehr; Kennzeichnung ABGELOEST in portfolio.py / letzte_bewertung.py
  P9  unveraenderte Daten -> kein Neuzeichnen (delete wird nicht gerufen)
  P10 Lesen schreibt nichts: Produktion und Ablage unveraendert (Pruefsumme)
  P11 Laufzeit: schneller Teil und langsamer Teil
"""
import hashlib
import os
import shutil
import sqlite3
import sys
import tempfile
import time
from datetime import date

WURZEL = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, WURZEL)
os.chdir(WURZEL)
import tkinter as tk  # noqa: E402
from tkinter import ttk  # noqa: E402

import agent.spot_mitnahme as SM  # noqa: E402
import agent.spot_upbit as SU  # noqa: E402
import config as C  # noqa: E402
import ui.bestand_tab as BT  # noqa: E402
from agent import hebelfuehrung as HF  # noqa: E402

ERG = []


def pruefe(k, ok, text):
    ERG.append(bool(ok))
    print("%-4s %-9s %s" % (k, "bestanden" if ok else "FEHLER", text))


def summe(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


T = tempfile.mkdtemp(prefix="p15_")
PROD = os.path.join(T, "prod.db")
shutil.copy(sys.argv[1], PROD)
ABL = os.path.join(T, "ablage")
os.makedirs(ABL)
WL = C.get_watchlist()


def conn_factory():
    c = sqlite3.connect("file:%s?mode=ro" % PROD.replace("\\", "/"), uri=True)
    c.row_factory = sqlite3.Row
    return c


SM.lauf(conn_factory(), ABL, WL, date(2026, 10, 12))
KRW = ["KRW-" + s for s in ("ALGO", "AVAX", "BIO", "CC", "INJ", "KAIA", "LINK", "MON", "MORPHO", "NEAR", "PLUME", "SEI", "SUI", "TAO", "W", "XLM")]
SU.lauf(conn_factory(), ABL, WL, http=lambda url, params: [{"market": m} for m in KRW] if url == SU.MAERKTE else {"data": {"notices": []}})
vor_p, vor_a = summe(PROD), summe(os.path.join(ABL, SM.ABLAGE))

root = tk.Tk()
root.withdraw()
nb = ttk.Notebook(root)
t0 = time.perf_counter()
tab = BT.BestandTab(nb, conn_factory, WL, spot_ordner=ABL)
t_init = time.perf_counter() - t0
nb.add(tab, text="Bestand")
z = {tab.tree.set(i, "symbol"): {c: tab.tree.set(i, c) for c in BT.SPALTEN} for i in tab.tree.get_children()}
c = conn_factory()
n47 = c.execute("SELECT COUNT(*) FROM holdings WHERE COALESCE(quantity,0) + COALESCE(staked_quantity,0) > 0").fetchone()[0]
pruefe("P1", len(z) == n47 == 47 and all(tab.tree.exists(s) for s in z), "Zeilen %d · Bestaende %d · Schluessel = Symbol" % (len(z), n47))
rollen = {}
for s, r in z.items():
    rollen[r["rolle"]] = rollen.get(r["rolle"], 0) + 1
pruefe("P2", rollen == {"Kern": 3, "L": 27, "Cash": 1, "-": 15, "nicht in Watchlist": 1}, "Rollen %s" % rollen)
kreis = SM.kreis(c, WL)
fenster = {r[0] for r in sqlite3.connect(os.path.join(ABL, SM.ABLAGE)).execute("SELECT symbol FROM fenster WHERE geschlossen_am IS NULL")}
b1_ok = all((z[s]["b1_status"] == "laeuft" and z[s]["b1_x"] == "1,00" and z[s]["b1_bis"] != "-") if s in fenster else z[s]["b1_status"] == "kein Fenster"
            for s in kreis) and all(z[s]["b1_x"] == "-" for s in z if z[s]["rolle"] != "L")
pruefe("P3", b1_ok and len(fenster) == len(kreis) == 27, "B1: %d Fenster fuer %d L-Bestaende, x 1,00 am Starttag, Nicht-L '-'" % (len(fenster), len(kreis)))
ohne = set(SU.stand(ABL)["ohne_krw"])
up_ok = all(z[s]["upbit"] == ("nein" if s in ohne else "ja") for s in kreis) and all(z[s]["upbit"] == "-" for s in z if z[s]["rolle"] != "L")
pruefe("P4", up_ok and len(ohne) == 11, "Upbit KRW: 'nein' fuer %d (%s)" % (len(ohne), ", ".join(sorted(ohne))))
trades = HF.lade(c)
h = [tab.hebel_tree.item(i, "values") for i in tab.hebel_tree.get_children()]
pruefe("P5", sorted(x[0] for x in h) == sorted(t["symbol"] for t in trades) == ["BTC", "ETH"],
       "Hebel kurz: %s" % [(x[0], x[4], x[5]) for x in h])
txt = tab.total_label.cget("text")
pruefe("P6", all(w in txt for w in ("Spot frei", "gestakt", "Fiat", "Hebel-Eigenkapital")) and tab._hebel_ek > 0, "Summenzeile: %s" % txt)
knoepfe = []


def alle(w):
    for k in w.winfo_children():
        if isinstance(k, (ttk.Button, tk.Button)):
            knoepfe.append(k.cget("text"))
        alle(k)


alle(tab)
pruefe("P7", not any("Bewertung" in k for k in knoepfe) and "Speichern" in knoepfe and tab.tree.bind("<Double-1>") and
       len(tab.aufteilung_tree.get_children()) > 0 and not hasattr(tab, "diversifikation_tree"),
       "Knoepfe %s · Doppelklick gebunden · Aufteilung nach Rolle %d Zeilen · keine Schwerpunkt-Tabelle" % (
           knoepfe, len(tab.aufteilung_tree.get_children())))
app = open("ui/app.py", encoding="utf-8").read()
pruefe("P8", "BestandTab(notebook, db_conn_factory, watchlist)" in app and 'text="Bestand"' in app and "PortfolioView(" not in app
       and "ABGELOEST" in open("ui/portfolio.py", encoding="utf-8").read()[:200] and "ABGELOESTEN ui/portfolio.py" in open("ui/letzte_bewertung.py", encoding="utf-8").read(),
       "app.py haengt BestandTab als 'Bestand' ein · PortfolioView nicht mehr · Kennzeichnung in portfolio.py und letzte_bewertung.py")
geloescht = []
alt_delete = tab.tree.delete
tab.tree.delete = lambda *a: (geloescht.append(a), alt_delete(*a))
t1 = time.perf_counter()
tab.refresh()
t_schnell = time.perf_counter() - t1
pruefe("P9", not geloescht, "zweiter refresh ohne Aenderung: delete gerufen %d mal" % len(geloescht))
t2 = time.perf_counter()
tab.refresh(erzwingen=True)
t_langsam = time.perf_counter() - t2
pruefe("P10", summe(PROD) == vor_p and summe(os.path.join(ABL, SM.ABLAGE)) == vor_a, "Produktion und Ablage nach dem Lesen unveraendert")
pruefe("P11", t_schnell < 1.0 and t_langsam < 5.0, "Laufzeit: Aufbau %.2f s · schneller Teil %.3f s · langsamer Teil %.2f s (Desktop)" % (t_init, t_schnell, t_langsam))
# P15c (12.10.2026, Nutzerbild: Spalte 'Upbit KRW' abgeschnitten, Mouseover rechts nicht lesbar)
breite = sum(int(tab.tree.column(c_, "width")) for c_ in BT.SPALTEN)
pruefe("P12", breite * 1.5 <= 1900 and bool(tab.tree.cget("xscrollcommand")), "Spaltenbreiten zusammen %d (x 1,5 = %d <= 1900) · waagrechte Laufleiste %s" % (
    breite, breite * 1.5, bool(tab.tree.cget("xscrollcommand"))))
lang = [z[s_]["avg_buy_price_eur"] for s_ in z if "unbepreist" in z[s_]["avg_buy_price_eur"] or "e+" in z[s_]["avg_buy_price_eur"]]
pruefe("P13", not lang and any(z[s_]["avg_buy_price_eur"].endswith(" ⚠") for s_ in z), "Einstand kompakt ('⚠' statt '(⚠ n unbepreist)'): lange Texte %s" % lang[:3])
from ui.heading_tooltip import lage
pruefe("P14", lage(1900, 500, 300, 80, 2000, 1100) == (1588, 518) and lage(1000, 500, 300, 80, 2000, 1100) == (1012, 518)
       and "platziere(tip, tree)" in open("ui/row_tooltip.py", encoding="utf-8").read() and "platziere(tip, tree)" in open("ui/heading_tooltip.py", encoding="utf-8").read(),
       "Mouseover am rechten Rand links vom Zeiger, Spaltenkopf UND Zeile")
# P15d (13.10.2026, Nutzer: *"Summe fuer Hebel ist nicht sichtbar"*): Gesamtwert OBEN (vor der Spot-Tabelle), Hebel-Summe in der Hebel-Ueberschrift
reihe = [w_ for w_ in tab.pack_slaves()]
oben = reihe.index(tab.total_label) < reihe.index(tab._paned)                  # P15g: die drei Bereiche sitzen im verschiebbaren PanedWindow
hk = tab.hebel_kopf.cget("text")
pruefe("P15", oben and "Hebel-Eigenkapital" in tab.total_label.cget("text") and "offene Positionen: 2" in hk and "900.00" in hk and int(tab.tree.cget("height")) == 12,
       "Gesamtwert oben %s · Hebel-Ueberschrift '%s' · Spot-Hoehe %s" % (oben, hk, tab.tree.cget("height")))
# P15e (13.10.2026, Nutzer: *"Ja, 1 bis 3 so umsetzen"*): Aufteilung nach Rolle, senkrechte Laufleiste
# P15f: waagrecht - Zeile 'Wert (EUR)' und 'Anteil %', eine Spalte je Gruppe
auf = {g_: (tab.aufteilung_tree.set("auf|wert", g_), tab.aufteilung_tree.set("auf|anteil", g_)) for g_ in BT.AUF_REIHE
       if tab.aufteilung_tree.set("auf|wert", g_) != "-"}
summe_anteil = sum(float(v_[1]) for v_ in auf.values())
pruefe("P16", set(auf) == {"Kern", "L", "Cash", "Fiat", "andere Klassen", "nicht in Watchlist", "Hebel"} and abs(summe_anteil - 100.0) < 0.5
       and auf["Hebel"][0] == "900.00", "Aufteilung %s · Anteile zusammen %.1f %%" % (auf, summe_anteil))
hoehe = int(tab.tree.cget("height")) + int(tab.hebel_tree.cget("height")) + int(tab.aufteilung_tree.cget("height"))
pruefe("P18", hoehe <= 16 and int(tab.hebel_tree.cget("height")) == 2 and len(tab.aufteilung_tree.get_children()) == 2,
       "Zeilen zusammen %d (Spot %s + Hebel %s + Aufteilung %s) - vorher 13 + 3 + 7 = 23" % (
           hoehe, tab.tree.cget("height"), tab.hebel_tree.cget("height"), tab.aufteilung_tree.cget("height")))
# P15g (13.10.2026, Nutzer: *"die drei Bereiche in der Hoehe anpassbar machen"*): ein senkrechtes PanedWindow mit Spot, Hebel, Aufteilung;
# das Fiat-Feld haengt fest unten AUSSERHALB davon; die Trennleiste laesst sich setzen (Fenster kurz sichtbar, ausserhalb des Bildschirms)
panes = [str(p_) for p_ in tab._paned.panes()]
inhalt = [str(tab.tree.master), str(tab.hebel_tree.master), str(tab.aufteilung_tree.master)]
root.deiconify()
root.geometry("1400x900+-3000+-3000")
nb.pack(fill="both", expand=True)
root.update()
vorher = tab._paned.sashpos(0)
tab._paned.sashpos(0, max(50, vorher - 120))
root.update()
nachher = tab._paned.sashpos(0)
pruefe("P19", str(tab._paned.cget("orient")) == "vertical" and panes == inhalt and vorher > 0 and nachher < vorher
       and str(tab.cash_reserve_status.master) not in panes and "Speichern" in knoepfe,
       "PanedWindow senkrecht, Bereiche %s · Trennleiste 1: %s -> %s · Fiat-Feld ausserhalb" % (
           [p_.rsplit(".", 1)[-1] for p_ in panes], vorher, nachher))
root.withdraw()
pruefe("P17", bool(tab.tree.cget("yscrollcommand")) and bool(tab.tree.cget("xscrollcommand")), "Spot-Tabelle: senkrechte %s und waagrechte %s Laufleiste" % (
    bool(tab.tree.cget("yscrollcommand")), bool(tab.tree.cget("xscrollcommand"))))
root.destroy()
c.close()
print("\nBeispielzeilen:")
for s in ("BEAMX", "LINK", "BTC", "EURCV", "VVMX", "XDC"):
    if s in z:
        print("  " + " | ".join("%s=%s" % (k, z[s][k]) for k in ("symbol", "rolle", "frei", "gestakt", "value_eur", "b1_x", "b1_bis", "b1_status", "upbit")))
shutil.rmtree(T, ignore_errors=True)
print("\n%d von %d bestanden" % (sum(ERG), len(ERG)))
