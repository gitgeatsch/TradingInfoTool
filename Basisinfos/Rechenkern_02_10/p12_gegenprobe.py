"""P12 Hebel-Tab (11.10.2026) - GEGENPROBE mit eigenem SQL und eigener Rechnung, nicht ueber ui/hebel_tab.

    python Basisinfos/Rechenkern_02_10/p12_gegenprobe.py <Pruefverzeichnis mit tradinginfotool.db und regel0_signale.db>

  G1 Signale je Filter: eigene Zaehlung in SQL (Signalstunde + 1 h gegen jetzt - 7 Tage, hebel_schalter = 1) gegen signal_zeilen
  G2 gemailt-Spalte: Zahl der Zeilen mit Mailzeit = COUNT(mail_signal_am) der Ablage (je Filter "alle")
  G3 Positionen: Abstand = (Kurs - Liquidation) / Kurs aus den Rohwerten, eigene Rechnung, gegen die Spalte "Abstand"
  G4 Freigabe: Zahl AN = COUNT(*) WHERE hebel_pruefung_erlaubt = 1 (eigenes SQL) gegen freigabe_zeilen
  G5 Freigabe-Spalte REGEL0-Daten fuer ALLE Assets: eigenes SQL auf die Kursdateien (DISTINCT symbol / _quelle) mit eigener
     Zuordnungslesung gegen betriebslage.mit_regel0_daten (Nutzerbild 11.10.: ausgeschaltete Assets standen auf '-')
"""
import os
import sqlite3
import sys
from datetime import datetime, timedelta, timezone

WURZEL = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, WURZEL)
os.chdir(WURZEL)
D = os.path.abspath(sys.argv[1])
import config as C  # noqa: E402
import agent.hebelfuehrung as HF  # noqa: E402
import agent.regel0_ansicht as R0A  # noqa: E402
import ui.hebel_tab as HT  # noqa: E402

ERG = []


def pruefe(k, ok, text):
    ERG.append(bool(ok))
    print("%-3s %-10s %s" % (k, "gleich" if ok else "ABWEICHUNG", text))


jetzt = datetime.now(timezone.utc)
grenze = (jetzt - timedelta(days=7) - timedelta(hours=1)).strftime("%Y-%m-%d %H:%M")
a = sqlite3.connect("file:%s?mode=ro" % os.path.join(D, "regel0_signale.db").replace("\\", "/"), uri=True)
eigen = {("alle", False): a.execute("SELECT COUNT(*) FROM signal").fetchone()[0],
         ("alle", True): a.execute("SELECT COUNT(*) FROM signal WHERE hebel_schalter=1").fetchone()[0],
         ("7_tage", False): a.execute("SELECT COUNT(*) FROM signal WHERE signalstunde >= ?", (grenze,)).fetchone()[0],
         ("7_tage", True): a.execute("SELECT COUNT(*) FROM signal WHERE signalstunde >= ? AND hebel_schalter=1", (grenze,)).fetchone()[0]}
gemailt = a.execute("SELECT COUNT(mail_signal_am) FROM signal").fetchone()[0]
a.close()
rows = R0A.lese(D)
fn = {k: len(HT.signal_zeilen(rows, jetzt, k[0], k[1])) for k in eigen}
pruefe("G1", fn == eigen, "eigen %s · Tab %s" % (eigen, fn))
gm = sum(1 for z in HT.signal_zeilen(rows, jetzt, "alle", False) if z["werte"][4] != "-")
pruefe("G2", gm == gemailt, "gemailt eigen %d · Tab %d" % (gemailt, gm))

c = sqlite3.connect("file:%s?mode=ro" % os.path.join(D, "tradinginfotool.db").replace("\\", "/"), uri=True)
c.row_factory = sqlite3.Row
trades = HF.lade(c)
z = HT.positions_zeilen(trades, rows)
abw = []
for t, zl in zip(trades, z):
    if t.get("kurs_eur") and t.get("liquidation_eur"):
        richtung = -1 if str(t.get("richtung")).upper() == "SHORT" else 1
        eigen_a = richtung * (t["kurs_eur"] - t["liquidation_eur"]) / t["kurs_eur"]
        if "%.1f %%" % (100 * eigen_a) != zl["werte"][6]:
            abw.append((t["symbol"], eigen_a, zl["werte"][6]))
pruefe("G3", trades and not abw, "%d Positionen, Abweichungen %s" % (len(trades), abw))
an = c.execute("SELECT COUNT(*) FROM asset_hebel_settings WHERE hebel_pruefung_erlaubt=1").fetchone()[0]
schalter = {r["symbol"]: bool(r["hebel_pruefung_erlaubt"]) for r in c.execute("SELECT * FROM asset_hebel_settings")}
c.close()
fz = HT.freigabe_zeilen(C.get_watchlist(), schalter, set(), rows)
pruefe("G4", sum(1 for x in fz if x["an"]) == an, "AN eigen %d · Tab %d · Zeilen %d" % (an, sum(1 for x in fz if x["an"]), len(fz)))

# G5 - an den DESKTOP-Kursdateien (voll; die Kopie traegt nur Stellvertreter), eigene Lesung
import csv  # noqa: E402
import agent.betriebslage as BL  # noqa: E402
datsym = set()
for f, q in (("data/stundenkurse.db", "SELECT DISTINCT symbol FROM stundenkurse"), ("data/stundenkurse_alle.db", "SELECT symbol FROM _quelle")):
    if os.path.exists(f):
        k = sqlite3.connect("file:%s?mode=ro" % f, uri=True)
        datsym |= {x for (x,) in k.execute(q)}
        k.close()
zu = {r["bitpanda"]: (None if r["markt"] == "gesperrt" else r["binance"])
      for r in csv.DictReader(open("Basisinfos/symbol_zuordnung.csv", encoding="utf-8"), delimiter=";")}
namen = {a.symbol for a in C.get_watchlist()} | set(schalter)
eigen5 = {n for n in namen if zu.get(n, n) in datsym}
fn5 = BL.mit_regel0_daten(namen, "data")
aus_mit = sorted(n for n in eigen5 if not schalter.get(n))
pruefe("G5", eigen5 == fn5 and len(datsym) > 100, "mit Daten eigen %d / Funktion %d · davon Schalter aus (vorher faelschlich '-'): %s" % (
    len(eigen5), len(fn5), aus_mit[:12]))
print()
print("%d von %d gleich" % (sum(ERG), len(ERG)))
