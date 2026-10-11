"""P12 Hebel-Tab (11.10.2026) - GEGENPROBE mit eigenem SQL und eigener Rechnung, nicht ueber ui/hebel_tab.

    python Basisinfos/Rechenkern_02_10/p12_gegenprobe.py <Pruefverzeichnis mit tradinginfotool.db und regel0_signale.db>

  G1 Signale je Filter: eigene Zaehlung in SQL (Signalstunde + 1 h gegen jetzt - 7 Tage, hebel_schalter = 1) gegen signal_zeilen
  G2 gemailt-Spalte: Zahl der Zeilen mit Mailzeit = COUNT(mail_signal_am) der Ablage (je Filter "alle")
  G3 Positionen: Abstand = (Kurs - Liquidation) / Kurs aus den Rohwerten, eigene Rechnung, gegen die Spalte "Abstand"
  G4 Freigabe: Zahl AN = COUNT(*) WHERE hebel_pruefung_erlaubt = 1 (eigenes SQL) gegen freigabe_zeilen
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
fz = HT.freigabe_zeilen(C.get_watchlist(), schalter, [], rows)
pruefe("G4", sum(1 for x in fz if x["an"]) == an, "AN eigen %d · Tab %d · Zeilen %d" % (an, sum(1 for x in fz if x["an"]), len(fz)))
print()
print("%d von %d gleich" % (sum(ERG), len(ERG)))
