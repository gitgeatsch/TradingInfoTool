"""P12 / GUI-2 Hebel-Tab (11.10.2026, Plan Schritt 53 G-V) - Pruefstand: die View EINZELN gegen eine WEGWERFkopie der NB-Sicherung.

    python Basisinfos/Rechenkern_02_10/p12_pruefstand.py <Pruefverzeichnis mit tradinginfotool.db und regel0_signale.db>

Nie ``main.py`` (CLAUDE.md: die GUI nie am Desktop starten) - nur ``HebelTab`` in einem unsichtbaren Tk-Fenster.

  T1 alle drei Bereiche gefuellt: Signale (Filter alle), Positionen mit Kurs/Abstand/H15, Abgleich "stimmt", Freigabe mit allen Schaltern
  T2 Detail = Signalmail-Text am Anfang + MAILSTAND (eine Quelle mit der Mail), Signalchart eingesetzt
  T3 Filter heute / 7 Tage / alle und "nur Schalter an" wirken (Zahlen fallen monoton, alle >= 7 Tage >= heute)
  T4 der 3-s-Takt: unveraenderte Daten -> Liste bleibt stehen, Auswahl bleibt, Detail wird NICHT neu gezeichnet
  T5 Positionen/Freigabe rechnen nur sichtbar und hoechstens alle 60 s (H15 nicht im 3-s-Takt)
  T6 GF2: Schalter umschalten schreibt GENAU eine Zeile, die Watchlist-Lesefunktion sieht denselben Wert; zurueckgeschaltet
  T7 Lesen schreibt nichts (Pruefsumme der Wegwerfkopie vor dem Umschalten gleich, Original-Kopie gleich)
  T8 app.py: Tab "Hebel" = HebelTab, der alte HebelView ist nicht mehr eingebunden; kein Job/Mailweg importiert ui/hebel_tab
"""
import hashlib
import os
import sqlite3
import sys
import tempfile
import time
from datetime import datetime, timezone

WURZEL = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, WURZEL)
os.chdir(WURZEL)
D = os.path.abspath(sys.argv[1])
ORIG = os.path.join(D, "tradinginfotool.db")

ERG = []


def pruefe(k, ok, text):
    ERG.append(bool(ok))
    print("%-3s %-9s %s" % (k, "bestanden" if ok else "FEHLER", text))


def summe(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


vor_orig = summe(ORIG)
T = tempfile.mkdtemp(prefix="p12_")
W = os.path.join(T, "w.db")
s_ = sqlite3.connect("file:%s?mode=ro" % ORIG.replace("\\", "/"), uri=True)
d_ = sqlite3.connect(W)
s_.backup(d_)
s_.close(); d_.close()
vor_w = summe(W)


def fabrik():
    c = sqlite3.connect(W)
    c.row_factory = sqlite3.Row
    return c


import tkinter as tk  # noqa: E402

import config as C  # noqa: E402
import agent.hebelfuehrung as HF  # noqa: E402
import agent.regel0_ansicht as R0A  # noqa: E402
import database.db as db  # noqa: E402
import ui.hebel_tab as HT  # noqa: E402

root = tk.Tk()
root.withdraw()
wl = C.get_watchlist()
t0 = time.perf_counter()
tab = HT.HebelTab(root, fabrik, wl, regel0_ordner=D)
t_bau = time.perf_counter() - t0
tab._zeit_var.set("alle"); tab._nur_an_var.set(False); tab._signale_neu()
n_sig = len(tab.signal_tree.get_children())
pos = [tab.pos_tree.item(i, "values") for i in tab.pos_tree.get_children()]
frei = [tab.frei_tree.item(i, "values") for i in tab.frei_tree.get_children()]
an = sum(1 for v in frei if v[1] == "AN")
pruefe("T1", n_sig > 0 and len(pos) == 2 and all(v[4] != "-" and v[6] != "-" and v[7] != "-" for v in pos)
       and tab.abgleich.cget("text").endswith("stimmt") and an == 26 and len(frei) >= 26,
       "Signale %d · Positionen %s · %s · Freigabe %d (AN %d) · Aufbau %.2f s" % (
           n_sig, [(v[0], v[6], v[7]) for v in pos], tab.abgleich.cget("text"), len(frei), an, t_bau))

# T2: ein gemailtes Signal waehlen
gem = [iid for iid, r in tab._signal_by_iid.items() if r.get("mail_signal_am") and (r.get("stufe") or r.get("stufe_vorlaeufig"))]
# die Kopie traegt nur Stellvertreter der Kursdateien (ALT, BTC, ETH je 1-2 Stunden) - fuer das Signalchart ein Asset, das sie fuehrt
gem = sorted(gem, key=lambda i: not i.startswith("ETH|"))
# Das Signalchart braucht Stunden im Signalfenster; die Kopie (Stellvertreter) und die Desktop-Daten (bis 24.09.) haben keine -
# geprueft wird hier der GUI-WEG (Bild ins Detail) mit einem echten PNG; die Erzeugung prueft Regel0Betrieb (regel0_chart).
import agent.regel0_chart as CH  # noqa: E402
import agent.indikator_chart as IC  # noqa: E402
_bild_orig = CH.bild
_ersatz = IC.bild("data", "BTC", "W", "BTC")
CH.bild = lambda r_, o_: _ersatz
tab.signal_tree.selection_set(gem[0]); tab._signal_gewaehlt()
CH.bild = _bild_orig
r = tab._signal_by_iid[gem[0]]
text = tab.detail_text.get("1.0", "end")
_t, _m, soll = R0A.detail(r, tab._regel0_rows, datetime.now(timezone.utc), pruefzeilen=R0A.pruefung_zeilen(D, r))
mail_anfang = soll.split("\n\n")[0].strip()
pruefe("T2", text.strip().startswith(mail_anfang[:60]) and "MAILSTAND" in text and len(tab.detail_text.image_names()) >= 1
       and str(tab.knopf_woche.cget("state")) == "normal",
       "Signal %s · Mailanfang im Detail %s · Bilder %d" % (gem[0], text.strip().startswith(mail_anfang[:60]), len(tab.detail_text.image_names())))

# T3 Filter
zahlen = {}
for z in HT.FILTER_ZEIT:
    for nur in (False, True):
        tab._zeit_var.set(z); tab._nur_an_var.set(nur); tab._signale_neu()
        zahlen[(z, nur)] = len(tab.signal_tree.get_children())
pruefe("T3", zahlen[("alle", False)] >= zahlen[("7_tage", False)] >= zahlen[("heute", False)]
       and all(zahlen[(z, True)] <= zahlen[(z, False)] for z in HT.FILTER_ZEIT) and zahlen[("alle", False)] == len(tab._regel0_rows),
       "%s · Ablage %d" % ({"%s%s" % (z, "+an" if n else ""): v for (z, n), v in zahlen.items()}, len(tab._regel0_rows)))

# T4 3-s-Takt
tab._zeit_var.set("alle"); tab._nur_an_var.set(False); tab._signale_neu()
tab.signal_tree.selection_set(gem[0]); tab._signal_gewaehlt()
root.update()                        # die vom Test selbst ausgeloesten Auswahlereignisse abarbeiten, BEVOR gezaehlt wird
gezeichnet = []
orig = HT.render_detail_text
HT.render_detail_text = lambda *a, **k: gezeichnet.append(1) or orig(*a, **k)
kinder = tab.signal_tree.get_children()
tab.refresh(); root.update()
pruefe("T4", tab.signal_tree.get_children() == kinder and tab.signal_tree.selection() == (gem[0],) and not gezeichnet,
       "Liste gleich %s · Auswahl %s · Detail neu gezeichnet %d" % (tab.signal_tree.get_children() == kinder, tab.signal_tree.selection(),
                                                                    len(gezeichnet)))
HT.render_detail_text = orig

# T5 Positionen nur sichtbar / 60 s
gerufen = []
orig_lade = HF.lade
HF.lade = lambda *a, **k: gerufen.append(1) or orig_lade(*a, **k)
tab._zuletzt_langsam = time.monotonic()
for _ in range(3):
    tab.refresh()
n_kurz = len(gerufen)
tab._zuletzt_langsam = time.monotonic() - 61
tab.refresh()                       # unsichtbar (withdraw) -> auch nach 60 s nicht
n_unsichtbar = len(gerufen)
tab.refresh(erzwingen=True)
n_erzwungen = len(gerufen)
HF.lade = orig_lade
pruefe("T5", n_kurz == 0 and n_unsichtbar == 0 and n_erzwungen == 1,
       "3 Takte: %d H15-Laeufe · nach 60 s unsichtbar: %d · erzwungen (Knopf): %d" % (n_kurz, n_unsichtbar, n_erzwungen - n_unsichtbar))

# T7 vor dem Umschalten: Lesen hat nichts geschrieben
pruefe("T7", summe(W) == vor_w and summe(ORIG) == vor_orig, "Wegwerfkopie nach dem Lesen %s · Original %s" % (
    "gleich" if summe(W) == vor_w else "GEAENDERT", "gleich" if summe(ORIG) == vor_orig else "GEAENDERT"))

# T6 GF2
ziel = next(iid for iid, sym in tab._frei_by_iid.items() if tab.frei_tree.item(iid, "values")[1] == "aus")
sym = tab._frei_by_iid[ziel]
c = fabrik()
vorher = c.execute("SELECT COUNT(*) FROM asset_hebel_settings").fetchone()[0]
c.close()
tab.frei_tree.selection_set(ziel); tab._umschalten()
c = fabrik()
nach = c.execute("SELECT COUNT(*) FROM asset_hebel_settings").fetchone()[0]
wert = db.get_hebel_pruefung_erlaubt(c, sym)
karte = db.get_hebel_pruefung_toggle_map(c).get(sym)
c.close()
zeile_an = tab.frei_tree.item("frei|" + sym, "values")[1]
tab.frei_tree.selection_set("frei|" + sym); tab._umschalten()
c = fabrik()
zurueck = db.get_hebel_pruefung_erlaubt(c, sym)
c.close()
pruefe("T6", wert is True and karte is True and zeile_an == "AN" and zurueck is False and nach - vorher in (0, 1),
       "%s: an %s (Watchlist-Lesefunktion %s, Liste %s), zurueck %s, Zeilen %d -> %d" % (sym, wert, karte, zeile_an, zurueck, vorher, nach))

# T8 Einbindung
app = open("ui/app.py", encoding="utf-8").read()
fremd = []
for o in ("agent", "scheduler", "remote", "api"):
    for w_, _, fs in os.walk(o):
        for f in fs:
            if f.endswith(".py") and "hebel_tab" in open(os.path.join(w_, f), encoding="utf-8", errors="replace").read():
                fremd.append(os.path.join(w_, f))
pruefe("T8", "from ui.hebel_tab import HebelTab" in app and "from ui.hebel_view import" not in app and "HebelTab(notebook" in app
       and not fremd,
       "HebelTab eingebunden %s · alter Import weg %s · fremde Importe %s" % ("HebelTab(notebook" in app, "from ui.hebel_view import" not in app, fremd))
root.destroy()
import shutil  # noqa: E402
shutil.rmtree(T, ignore_errors=True)
print()
print("%d von %d bestanden" % (sum(ERG), len(ERG)))
