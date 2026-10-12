"""P16 Spot B3 Upbit (12.10.2026, Spot §47.4) - GEGENPROBE mit eigenem Rechenweg. Nur lesend (bis auf eine Wegwerf-Ablage).

    python Basisinfos/Rechenkern_02_10/p16_gegenprobe.py <NB-Sicherung tradinginfotool.db>

  G1 eigene Regel OHNE regulaeren Ausdruck (Zeichen fuer Zeichen: Klammern vor dem Stichwort, nur A-Z/0-9, Laenge 2-15) am Archiv
     gegen spot_upbit.listing - dieselben 137
  G2 ECHTER Lauf (echtes Upbit, Wegwerf-Ablage, Kopie der NB-Sicherung): Kreis ohne KRW gegen eigenes SQL + eigene Abfrage der
     KRW-Maerkte (/v1/ticker je Coin) - gleich
  G3 echter Abruf: Meldungen geholt, Zeiten lesbar, erster Lauf = Startmarke ohne Fall
  G4 Hinweis 'ausserhalb Binance' an den ECHTEN Stundenkursen (data/): BEAMX hat REGEL0-Daten, KAS/BRETT/SUPRA nicht
"""
import os
import shutil
import sqlite3
import sys
import tempfile
import time

import requests

WURZEL = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, WURZEL)
os.chdir(WURZEL)
import agent.spot_mitnahme as SM  # noqa: E402
import agent.spot_upbit as SU  # noqa: E402
import config as C  # noqa: E402
from agent import betriebslage as BL  # noqa: E402

ERG = []


def pruefe(k, ok, text):
    ERG.append(bool(ok))
    print("%-3s %-10s %s" % (k, "gleich" if ok else "ABWEICHUNG", text))


def eigene_regel(titel):
    i = titel.find(SU.STICHWORT)
    if i < 0 or "KRW" not in titel:
        return []
    vorn, aus, j = titel[:i], [], 0
    while True:
        a = vorn.find("(", j)
        if a < 0:
            break
        e = vorn.find(")", a + 1)
        if e < 0:
            break
        k = vorn[a + 1:e]
        if 2 <= len(k) <= 15 and all(ch in "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789" for ch in k):
            aus.append(k)
        j = a + 1
    return aus


a = sqlite3.connect("file:data/_c2/ankuendigungen.db?mode=ro", uri=True)
x1 = sorted((u, k) for t, u in a.execute("SELECT titel, utc FROM upbit") for k in eigene_regel(t))
x2 = sorted((u, k) for t, u in a.execute("SELECT titel, utc FROM upbit") for k in SU.listing(t))
pruefe("G1", x1 == x2 and len(x1) == 137, "eigene Regel %d · listing %d · gleich %s" % (len(x1), len(x2), x1 == x2))

T = tempfile.mkdtemp(prefix="p16g_")
PROD = os.path.join(T, "prod.db")
shutil.copy(sys.argv[1], PROD)
cp = sqlite3.connect("file:%s?mode=ro" % PROD.replace("\\", "/"), uri=True)
WL = C.get_watchlist()
erg = SU.lauf(cp, T, WL)
krypto = {w.symbol for w in WL if w.assetklasse == "krypto" and not getattr(w, "ist_cash_aequivalent", False)}
L = sorted(s for s, q, st in cp.execute("SELECT symbol, quantity, staked_quantity FROM holdings") if (q or 0) + (st or 0) > 0 and s in krypto
           and s not in ("BTC", "ETH", "SOL"))
ohne = []
for s in L:
    k = {"CANTON": "CC"}.get(s, s)
    r = requests.get("https://api.upbit.com/v1/ticker", params={"markets": "KRW-%s" % k}, timeout=30)
    if not (r.status_code == 200 and isinstance(r.json(), list) and r.json()):
        ohne.append(s)
    time.sleep(0.15)
pruefe("G2", erg["ok"] and erg["ohne_krw"] == sorted(ohne), "echter Lauf: Kreis ohne KRW %s · eigene Abfrage %s" % (erg["ohne_krw"], sorted(ohne)))
c = sqlite3.connect(os.path.join(T, SM.ABLAGE))
n_m, n_f = c.execute("SELECT COUNT(*) FROM upbit_meldung").fetchone()[0], c.execute("SELECT COUNT(*) FROM upbit_fall").fetchone()[0]
juengste = c.execute("SELECT MAX(utc) FROM upbit_meldung").fetchone()[0]
c.close()
pruefe("G3", erg["startmarke"] and n_f == 0 and erg["neu"] >= 0 and (n_m == 0 or juengste[:2] == "20"),
       "echter Abruf: Startmarke %s · abgelegte Listing-Kuerzel %d (juengste %s) · Faelle %d" % (erg["startmarke"], n_m, juengste, n_f))
# 1. Lauf: mit_regel0_daten zaehlte KAS/BRETT (nur Futures) als 'Binance' -> ABWEICHUNG; ersetzt durch betriebslage.mit_binance_spot
mit = BL.mit_binance_spot({"BEAMX", "TURBO", "CAT", "KAS", "BRETT", "SUPRA", "HYPE", "CANTON"}, os.path.join(WURZEL, "data"))
eigen = {r[0] for r in sqlite3.connect("file:data/messdaten.db?mode=ro", uri=True).execute(
    "SELECT symbol FROM price_history_ohlc WHERE quelle='binance_mess' AND symbol IN ('BEAMX','TURBO','1000CAT','KAS','BRETT','SUPRA','HYPE','CC') "
    "GROUP BY symbol")}
pruefe("G4", mit == {"BEAMX", "TURBO", "CAT"} and eigen == {"BEAMX", "TURBO", "1000CAT"},
       "mit Binance-Spot (data/): %s · eigenes SQL (Binance-Namen) %s - KAS, BRETT, SUPRA, HYPE, CANTON ohne Spot" % (sorted(mit), sorted(eigen)))
cp.close()
shutil.rmtree(T, ignore_errors=True)
print("\n%d von %d gleich" % (sum(ERG), len(ERG)))
