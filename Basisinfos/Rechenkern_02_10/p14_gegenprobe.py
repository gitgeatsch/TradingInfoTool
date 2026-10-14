"""P14 Spot B1 (11.10.2026) - GEGENPROBE mit eigener Rechnung.

    python Basisinfos/Rechenkern_02_10/p14_gegenprobe.py <Pruefverzeichnis mit Kopie tradinginfotool.db>

  G0 (R-R11) Teil 0: siehe p14_teil0.py - die Betriebsfunktion reproduziert die Uebertragbarkeit auf der Messbasis (7.819 / 7,1 % / +4,87 Pp)
  G1 Kreis an der NB-Kopie: eigenes SQL (holdings frei + gestakt > 0, Watchlist Krypto ohne Stablecoin, ohne Kern) gegen spot_mitnahme.kreis
  G2 Startkurse an der NB-Kopie: erster Lauf (heute = 11.10.) legt je Coin ein Fenster mit dem letzten Dollar-Schluss <= 10.10. an - eigenes SQL
  G3 unabhaengige Schleife: 40 Zufallsreihen x 800 Tage, Fenster/Ausloesung direkt gerechnet (eigene Regel aus §31) gegen den Tag-fuer-Tag-Lauf
"""
import os
import random
import shutil
import sqlite3
import sys
import tempfile
from datetime import date, timedelta
from types import SimpleNamespace as NS

WURZEL = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, WURZEL)
__import__("sys").path.append(__import__("os").path.abspath(__file__).split("TradingInfoTool")[0] + "TradingInfoTool")  # wegwerf.py
import wegwerf  # noqa: E402,F401  Wegwerf-Ordner auf D: und Aufraeumen ohne stilles Scheitern (15.10.2026)
os.chdir(WURZEL)
D = os.path.abspath(sys.argv[1])
import config as C  # noqa: E402
import agent.spot_mitnahme as SM  # noqa: E402

ERG = []


def pruefe(k, ok, text):
    ERG.append(bool(ok))
    print("%-3s %-10s %s" % (k, "gleich" if ok else "ABWEICHUNG", text))


# G1/G2 an der Kopie
c = sqlite3.connect("file:%s?mode=ro" % os.path.join(D, "tradinginfotool.db").replace("\\", "/"), uri=True)
wl = C.get_watchlist()
krypto = {a.symbol for a in wl if a.assetklasse == "krypto" and not a.ist_cash_aequivalent}
eigen = {s for s, q, st in c.execute("SELECT symbol, quantity, staked_quantity FROM holdings") if (q or 0) + (st or 0) > 0
         and s in krypto and s not in ("BTC", "ETH", "SOL")}
fn = set(SM.kreis(c, wl))
pruefe("G1", eigen == fn and len(eigen) > 10, "%d L-Bestaende eigen / %d Funktion, Unterschied %s" % (len(eigen), len(fn), sorted(eigen ^ fn)))
T = tempfile.mkdtemp(prefix="p14g_")
erg = SM.lauf(c, T, wl, date(2026, 10, 11))
a = SM.oeffne(T)
fen = {s: (st, k) for s, st, k in a.execute("SELECT symbol, start, startkurs_usd FROM fenster")}
a.close()
abw = []
for s in sorted(eigen):
    r = c.execute("SELECT date, close FROM price_history_ohlc WHERE symbol=? AND currency='USD' AND date <= '2026-10-10' "
                  "AND COALESCE(quelle,'') != 'rekonstruiert' ORDER BY date DESC LIMIT 1", (s,)).fetchone()
    soll = (r[0][:10], float(r[1])) if r and (date(2026, 10, 10) - date.fromisoformat(r[0][:10])).days <= 3 else None
    if fen.get(s) != soll:
        abw.append((s, fen.get(s), soll))
c.close()
pruefe("G2", not abw and len(fen) == len([s for s in eigen if s in fen]), "%d Fenster angelegt, Startkurse abweichend: %s" % (len(fen), abw[:5]))
wegwerf.aufraeumen(T)

# G3 unabhaengige Schleife
random.seed(11)
T = tempfile.mkdtemp(prefix="p14g3_")
P = os.path.join(T, "p.db")
k = sqlite3.connect(P)
k.execute("CREATE TABLE holdings (symbol TEXT, quantity REAL, staked_quantity REAL)")
k.execute("CREATE TABLE price_history_ohlc (symbol TEXT, currency TEXT, date TEXT, close REAL, quelle TEXT)")
T0 = date(2025, 1, 1)
reihen = {}
for n in range(40):
    s = "Z%02d" % n
    v, xs = 1.0, []
    drift = random.choice([0.0, 0.004, 0.008])
    for i in range(800):
        v *= 1 + random.gauss(drift, 0.04)
        xs.append(v)
    reihen[s] = xs
    k.execute("INSERT INTO holdings VALUES (?,?,?)", (s, 1.0, 0.0))
    k.executemany("INSERT INTO price_history_ohlc VALUES (?,?,?,?,?)", [(s, "USD", (T0 + timedelta(days=i)).isoformat(), x, "gemessen")
                                                                       for i, x in enumerate(xs)])
k.commit()
wl3 = [NS(symbol=s, assetklasse="krypto", ist_cash_aequivalent=False) for s in reihen]
for i in range(0, 799):
    SM.lauf(k, T, wl3, T0 + timedelta(days=i + 1))


def eigene(xs):
    """Fenster ab Tag 0; erster Schluss >= 3 x Start nach dem Start, mit Folgetag im Fenster; am Fensterende neues Fenster."""
    aus, st = [], 0
    while st + 1 < 799:
        ende = st + 365
        hit = None
        for t in range(st + 1, min(ende, 798) + 1):
            if xs[t] >= 3 * xs[st]:
                hit = t
                break
        if hit is not None and (hit < ende or ende > 798):
            sprung = hit > 0 and xs[hit] >= 2 * xs[hit - 1]
            aus.append(((T0 + timedelta(days=st)).isoformat(), (T0 + timedelta(days=hit)).isoformat(), sprung))
        if ende > 798:
            break
        st = ende
    return aus


a = SM.oeffne(T)
diff = []
for s, xs in reihen.items():
    fnz = [(r[0], r[1], r[2] == "zu pruefen") for r in a.execute("SELECT start, ausloese_tag, status FROM fenster WHERE symbol=? AND ausloese_tag "
                                                                  "IS NOT NULL ORDER BY start", (s,))]
    if fnz != eigene(xs):
        diff.append((s, fnz, eigene(xs)))
n_aus = a.execute("SELECT COUNT(*) FROM fenster WHERE ausloese_tag IS NOT NULL").fetchone()[0]
n_fen = a.execute("SELECT COUNT(*) FROM fenster").fetchone()[0]
a.close()
k.close()
pruefe("G3", not diff and n_aus > 5, "40 Reihen x 800 Tage: %d Fenster, %d Ausloesungen, Abweichungen %d %s" % (n_fen, n_aus, len(diff), diff[:2]))
wegwerf.aufraeumen(T)
print()
print("%d von %d gleich (G0 in p14_teil0.py)" % (sum(ERG), len(ERG)))
