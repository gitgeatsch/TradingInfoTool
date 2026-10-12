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
       len(tab.diversifikation_tree.get_children()) > 0, "Knoepfe %s · Doppelklick gebunden · Diversifikation %d Zeilen" % (
           knoepfe, len(tab.diversifikation_tree.get_children())))
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
root.destroy()
c.close()
print("\nBeispielzeilen:")
for s in ("BEAMX", "LINK", "BTC", "EURCV", "VVMX", "XDC"):
    if s in z:
        print("  " + " | ".join("%s=%s" % (k, z[s][k]) for k in ("symbol", "rolle", "frei", "gestakt", "value_eur", "b1_x", "b1_bis", "b1_status", "upbit")))
shutil.rmtree(T, ignore_errors=True)
print("\n%d von %d bestanden" % (sum(ERG), len(ERG)))
