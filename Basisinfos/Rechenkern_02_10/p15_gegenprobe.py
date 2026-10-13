"""P15 GUI-3 Bestand-Tab (12.10.2026, G-Y) - GEGENPROBE mit eigenem Rechenweg (ohne die Funktionen des Tabs). Nur lesend.

    python Basisinfos/Rechenkern_02_10/p15_gegenprobe.py <NB-Sicherung tradinginfotool.db>

  G1 Summen per eigenem SQL: frei x juengster price_eur, gestakt x price_eur, Fiat (meta), Hebel-Eigenkapital (offene Positionen) -
     gegen bestand_tab.summen auf denselben Daten (+-0,01 EUR)
  G2 Rolle je Bestand mit eigener Regel aus den Watchlist-Feldern - gegen bestand_tab.rolle
  G3 x Startkurs fuer alle L-Bestaende: letzter Dollar-Schluss (eigenes SQL, ohne rekonstruiert) / Startkurs aus der Ablage (eigenes SQL)
     an einem Folgetag mit neuem Kurs - gegen bestand_tab.b1_werte
"""
import os
import shutil
import sqlite3
import sys
import tempfile
from datetime import date

WURZEL = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, WURZEL)
os.chdir(WURZEL)
import agent.spot_mitnahme as SM  # noqa: E402
import config as C  # noqa: E402
import database.db as db  # noqa: E402
import ui.bestand_tab as BT  # noqa: E402
from agent import hebelfuehrung as HF  # noqa: E402

ERG = []


def pruefe(k, ok, text):
    ERG.append(bool(ok))
    print("%-3s %-10s %s" % (k, "gleich" if ok else "ABWEICHUNG", text))


T = tempfile.mkdtemp(prefix="p15g_")
PROD = os.path.join(T, "prod.db")
shutil.copy(sys.argv[1], PROD)
c = sqlite3.connect("file:%s?mode=ro" % PROD.replace("\\", "/"), uri=True)
c.row_factory = sqlite3.Row
WL = C.get_watchlist()
wl = {a.symbol: a for a in WL}

# G1
preis = {}
for r in c.execute("SELECT symbol, price_eur, fetched_at FROM price_cache p WHERE fetched_at = (SELECT MAX(fetched_at) FROM price_cache q WHERE q.symbol = p.symbol)"):
    preis[r["symbol"]] = r["price_eur"]
frei = gest = 0.0
for r in c.execute("SELECT symbol, quantity, staked_quantity FROM holdings"):
    q, st = float(r["quantity"] or 0), float(r["staked_quantity"] or 0)
    if q + st <= 0 or preis.get(r["symbol"]) is None:
        continue
    frei += q * preis[r["symbol"]]
    gest += st * preis[r["symbol"]]
fiat = float(c.execute("SELECT value FROM meta WHERE key='cash_reserve_fiat_eur'").fetchone()[0] or 0)
ek = sum(float(r[0] or 0) for r in c.execute("SELECT eigenkapital_eur FROM hebel_positions WHERE geschlossen_am IS NULL"))
zeilen = BT.spot_zeilen(db.get_all_holdings(c), db.get_latest_prices(c), wl, {}, {}, None)
s = BT.summen(zeilen, db.get_cash_reserve_fiat_eur(c), sum(float(t.get("eigenkapital_eur") or 0) for t in HF.lade(c)))
abw = max(abs(s["frei"] - frei), abs(s["gestakt"] - gest), abs(s["fiat"] - fiat), abs(s["hebel_ek"] - ek))
pruefe("G1", abw < 0.01, "eigen: frei %.2f · gestakt %.2f · Fiat %.2f · Hebel-EK %.2f · gesamt %.2f · Tab gesamt %.2f · groesste Abweichung %.4f" % (
    frei, gest, fiat, ek, frei + gest + fiat + ek, s["gesamt"], abw))

# G2
falsch = []
for r in c.execute("SELECT symbol, quantity, staked_quantity FROM holdings"):
    if float(r["quantity"] or 0) + float(r["staked_quantity"] or 0) <= 0:
        continue
    a = wl.get(r["symbol"])
    if a is None:
        e = "nicht in Watchlist"
    elif a.ist_cash_aequivalent:
        e = "Cash"
    elif a.assetklasse == "krypto":
        e = "Kern" if r["symbol"] in ("BTC", "ETH", "SOL") else "L"
    else:
        e = "-"
    if e != BT.rolle(r["symbol"], a):
        falsch.append(r["symbol"])
pruefe("G2", not falsch, "Rolle eigene Regel gegen den Tab: Abweichungen %s" % falsch)

# G3 - Ablage am 12.10. anlegen, dann einen neuen Kurs fuer 5 Coins einsetzen (Kopie wird dafuer beschreibbar geoeffnet)
ABL = os.path.join(T, "ablage")
os.makedirs(ABL)
SM.lauf(c, ABL, WL, date(2026, 10, 12))
w = sqlite3.connect(PROD)
neu = {"LINK": 1.37, "BEAMX": 0.81, "INJ": 3.05, "KAS": 2.2, "W": 1.0}
for sym, f in neu.items():
    k = w.execute("SELECT close FROM price_history_ohlc WHERE symbol=? AND currency='USD' AND COALESCE(quelle,'')!='rekonstruiert' ORDER BY date DESC LIMIT 1",
                  (sym,)).fetchone()[0]
    w.execute("INSERT OR REPLACE INTO price_history_ohlc (symbol, currency, date, open, high, low, close, volume, fetched_at, quelle) "
              "VALUES (?, 'USD', '2026-10-12', ?, ?, ?, ?, 0, '2026-10-12', 'gegenprobe')", (sym, k * f, k * f, k * f, k * f))   # Schema der PRODUKTION (ohne assetklasse)
w.commit()
w.close()
c2 = sqlite3.connect("file:%s?mode=ro" % PROD.replace("\\", "/"), uri=True)
fenster, _ = BT.lese_b1(ABL)
schl = BT.letzte_schluesse(c2, list(fenster))
abl = sqlite3.connect(os.path.join(ABL, SM.ABLAGE))
abw = []
for sym in fenster:
    start = abl.execute("SELECT startkurs_usd FROM fenster WHERE symbol=? AND geschlossen_am IS NULL", (sym,)).fetchone()[0]
    letzt = c2.execute("SELECT close FROM price_history_ohlc WHERE symbol=? AND currency='USD' AND COALESCE(quelle,'')!='rekonstruiert' ORDER BY date DESC LIMIT 1",
                       (sym,)).fetchone()[0]
    eigen = ("%.2f" % (letzt / start)).replace(".", ",")
    tab = BT.b1_werte(sym, fenster, schl)[0]
    if eigen != tab:
        abw.append((sym, eigen, tab))
beispiele = {s: BT.b1_werte(s, fenster, schl)[0] for s in neu}
pruefe("G3", not abw and beispiele == {"LINK": "1,37", "BEAMX": "0,81", "INJ": "3,05", "KAS": "2,20", "W": "1,00"},
       "x Start fuer %d Fenster eigen gleich Tab · neue Kurse %s" % (len(fenster), beispiele))
c.close()
c2.close()
abl.close()
shutil.rmtree(T, ignore_errors=True)
# G4 (P15e): Aufteilung nach Rolle per eigenem SQL und eigener Regel - gegen bestand_tab.aufteilung
c3 = sqlite3.connect("file:%s?mode=ro" % sys.argv[1].replace("\\", "/"), uri=True)
c3.row_factory = sqlite3.Row
pr3 = {r["symbol"]: r["price_eur"] for r in c3.execute(
    "SELECT symbol, price_eur FROM price_cache p WHERE fetched_at = (SELECT MAX(fetched_at) FROM price_cache q WHERE q.symbol = p.symbol)")}
eig = {}
for r in c3.execute("SELECT symbol, quantity, staked_quantity FROM holdings"):
    m_ = float(r["quantity"] or 0) + float(r["staked_quantity"] or 0)
    if m_ <= 0 or pr3.get(r["symbol"]) is None:
        continue
    a_ = wl.get(r["symbol"])
    g_ = ("nicht in Watchlist" if a_ is None else "Cash" if a_.ist_cash_aequivalent else
          ("Kern" if r["symbol"] in ("BTC", "ETH", "SOL") else "L") if a_.assetklasse == "krypto" else "andere Klassen")
    eig[g_] = eig.get(g_, 0.0) + m_ * pr3[r["symbol"]]
eig["Fiat"] = float(c3.execute("SELECT value FROM meta WHERE key='cash_reserve_fiat_eur'").fetchone()[0] or 0)
eig["Hebel"] = sum(float(r[0] or 0) for r in c3.execute("SELECT eigenkapital_eur FROM hebel_positions WHERE geschlossen_am IS NULL"))
z3 = BT.spot_zeilen(db.get_all_holdings(c3), db.get_latest_prices(c3), wl, {}, {}, None)
s3 = BT.summen(z3, db.get_cash_reserve_fiat_eur(c3), sum(float(t.get("eigenkapital_eur") or 0) for t in HF.lade(c3)))
tab3 = {g_: w_ for g_, w_, _ in BT.aufteilung(z3, s3)}
abw3 = max(abs(tab3.get(k_, 0.0) - v_) for k_, v_ in eig.items())
pruefe("G4", abw3 < 0.01 and set(tab3) == {k_ for k_, v_ in eig.items() if v_ > 0},
       "Aufteilung eigen %s · groesste Abweichung %.4f" % ({k_: round(v_, 2) for k_, v_ in eig.items()}, abw3))
c3.close()
print("\n%d von %d gleich" % (sum(ERG), len(ERG)))
