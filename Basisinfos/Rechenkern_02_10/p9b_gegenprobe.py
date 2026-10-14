"""P9b (10.10.2026) - Laufzeit der Statusseite: GEGENPROBE alt gegen neu, bitgleich.

    python Basisinfos/Rechenkern_02_10/p9b_gegenprobe.py <Pruefverzeichnis mit Kopie tradinginfotool.db>

  B1 db.get_latest_prices: neue Abfrage (Sprung ueber den Index) gegen die ALTE (GROUP BY), Kopie der Produktion, jedes Feld
  B2 dieselbe Probe an Randfaellen in einer Wegwerf-DB (leer, ein Symbol, viele Zeitstempel, Gross/Klein, NULL-Werte in
     Preis-Spalten, Zeitstempel-Formate gemischt)
  B3 Marktscan-Karte: neue gezielte Abfrage gegen die alte Rechnung ueber 500 Objekte (Kopie)
  B4 dieselbe Probe an Randfaellen (leer, zwei Laeufe, Treffer-Einstufungen, Lauf mit > 500 Kandidaten -> neu vollstaendig)
  B5 Laufzeit: get_latest_prices und Marktscan alt/neu; warmer Statusaufbau
  B6 Rollen-Kontingent: traegt jetzt eine Frist (60 s), nicht mehr in _LIVE_GETTER; Ergebnis gleich der direkten Zaehlung
  B7 Pruefsumme der Kopie unveraendert
"""
import hashlib
import os
import sqlite3
import sys
import tempfile
import time
from pathlib import Path

WURZEL = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, WURZEL)
__import__("sys").path.append(__import__("os").path.abspath(__file__).split("TradingInfoTool")[0] + "TradingInfoTool")  # wegwerf.py
import wegwerf  # noqa: E402,F401  Wegwerf-Ordner auf D: und Aufraeumen ohne stilles Scheitern (15.10.2026)
os.chdir(WURZEL)
D = os.path.abspath(sys.argv[1])
import agent.betriebslage as BL  # noqa: E402

BL.DATEN = D
import config as C  # noqa: E402
import database.db as db  # noqa: E402
import remote.status as RS  # noqa: E402

ERG = []
ALT_PREISE = """SELECT p.symbol, p.coingecko_id, p.price_usd, p.price_eur, p.market_cap_usd, p.volume_24h_usd, p.change_24h_pct,
p.fetched_at FROM price_cache p INNER JOIN (SELECT symbol, MAX(fetched_at) AS max_fetched_at FROM price_cache GROUP BY symbol) latest
ON p.symbol = latest.symbol AND p.fetched_at = latest.max_fetched_at"""


def pruefe(k, ok, text):
    ERG.append(ok)
    print("%-3s %-10s %s" % (k, "gleich" if ok else "ABWEICHUNG", text))


def alt_preise(c):
    cur = c.execute(ALT_PREISE)
    namen = [x[0] for x in cur.description]
    return {r[0]: db.PriceSnapshot(**dict(zip(namen, tuple(r)))) for r in cur.fetchall()}


def alt_marktscan(c):
    """Die Fassung vor P9b, woertlich."""
    candidates = db.get_marktscan_candidates(c, limit=500)
    if not candidates:
        return None
    lid = candidates[0].scan_run_id
    lauf = [x for x in candidates if x.scan_run_id == lid]
    return {"discovered_at": lauf[0].discovered_at, "kandidaten": len(lauf),
            "treffer": len([x for x in lauf if x.einstufung in RS._TREFFER_EINSTUFUNGEN])}


def summe(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


KOPIE = os.path.join(D, "tradinginfotool.db")
vor = summe(KOPIE)
c = sqlite3.connect("file:%s?mode=ro" % KOPIE.replace("\\", "/"), uri=True)
c.row_factory = sqlite3.Row

# B1
a, n = alt_preise(c), db.get_latest_prices(c)
pruefe("B1", a == n and len(a) > 0, "%d Symbole alt, %d neu, Unterschiede %s" % (len(a), len(n), sorted(set(a) ^ set(n))[:5]))

# B2 Randfaelle
with tempfile.TemporaryDirectory() as t:
    w = sqlite3.connect(os.path.join(t, "w.db"))
    w.execute("CREATE TABLE price_cache (symbol TEXT NOT NULL, coingecko_id TEXT, price_usd REAL, price_eur REAL, market_cap_usd REAL, "
              "volume_24h_usd REAL, change_24h_pct REAL, fetched_at TEXT NOT NULL, PRIMARY KEY (symbol, fetched_at))")
    faelle = []
    faelle.append(("leer", alt_preise(w) == db.get_latest_prices(w) == {}))
    w.execute("INSERT INTO price_cache VALUES ('BTC','bitcoin',1,1,1,1,1,'2026-10-10T10:00:00+00:00')")
    faelle.append(("ein Symbol", alt_preise(w) == db.get_latest_prices(w)))
    zeilen = []
    for i, sym in enumerate(["ETH", "eth", "A", "ZZZ", "1INCH", "BTC", "SOL"]):
        for h in range(5):
            zeilen.append((sym, None if h == 2 else sym.lower(), None if h == 3 else 10.0 + i + h, 9.0 + i * h, None, None, None,
                           "2026-10-%02dT%02d:00:00%s" % (5 + h, h, "+00:00" if h % 2 else "Z")))
    w.executemany("INSERT OR IGNORE INTO price_cache VALUES (?,?,?,?,?,?,?,?)", zeilen)
    faelle.append(("viele Zeitstempel, Gross/Klein, NULL-Preise, gemischte Formate", alt_preise(w) == db.get_latest_prices(w)))
    w.execute("INSERT INTO price_cache VALUES ('NUR1',NULL,NULL,NULL,NULL,NULL,NULL,'2020-01-01')")
    faelle.append(("Symbol mit nur einer Zeile, alles NULL", alt_preise(w) == db.get_latest_prices(w)))
    # B4 Randfaelle Marktscan in derselben Wegwerf-DB, Schema aus der Kopie
    schema = c.execute("SELECT sql FROM sqlite_master WHERE name='marktscan_candidates'").fetchone()[0]
    w.execute(schema)
    w.row_factory = sqlite3.Row
    spalten = [r[1] for r in w.execute("PRAGMA table_info(marktscan_candidates)")]
    ms = []
    ms.append(("leer", alt_marktscan(w) == RS._get_marktscan_last(w) is None or (alt_marktscan(w) is None and RS._get_marktscan_last(w) is None)))
    beispiel = dict(c.execute("SELECT * FROM marktscan_candidates ORDER BY discovered_at DESC LIMIT 1").fetchone())

    def ein(run, cg, zeit, einst):
        z = dict(beispiel, scan_run_id=run, coingecko_id=cg, discovered_at=zeit, einstufung=einst)
        if "id" in z:
            z["id"] = None
        w.execute("INSERT INTO marktscan_candidates (%s) VALUES (%s)" % (",".join(spalten), ",".join("?" * len(spalten))),
                  [z.get(k) for k in spalten])
    for i, e in enumerate(["kaufkandidat", "watchlist_wuerdig", "verworfen", None, "kaufkandidat"]):
        ein("lauf-a", "a%d" % i, "2026-10-09T02:00:%02d" % i, e)
    for i, e in enumerate(["verworfen", "watchlist_wuerdig", "kaufkandidat"]):
        ein("lauf-b", "b%d" % i, "2026-10-10T02:00:%02d" % i, e)
    ms.append(("zwei Laeufe, Treffer-Einstufungen", alt_marktscan(w) == RS._get_marktscan_last(w)))
    for i in range(520):
        ein("lauf-c", "c%d" % i, "2026-10-11T02:%02d:%02d" % (i // 60, i % 60), "kaufkandidat" if i % 7 == 0 else "verworfen")
    neu_c = RS._get_marktscan_last(w)
    ms.append(("Lauf mit 520 Kandidaten: neu zaehlt vollstaendig", neu_c["kandidaten"] == 520 and alt_marktscan(w)["kandidaten"] == 500))
    w.close()
pruefe("B2", all(ok for _, ok in faelle), " · ".join("%s %s" % (f, "ok" if ok else "FEHLER") for f, ok in faelle))

# B3
a3, n3 = alt_marktscan(c), RS._get_marktscan_last(c)
pruefe("B3", a3 == n3, "alt %s · neu %s" % (a3, n3))
pruefe("B4", all(ok for _, ok in ms), " · ".join("%s %s" % (f, "ok" if ok else "FEHLER") for f, ok in ms))

# B5
def zeit(fn, n=5):
    fn()
    t = time.perf_counter()
    for _ in range(n):
        fn()
    return (time.perf_counter() - t) / n
t_pa, t_pn = zeit(lambda: alt_preise(c)), zeit(lambda: db.get_latest_prices(c))
t_ma, t_mn = zeit(lambda: alt_marktscan(c)), zeit(lambda: RS._get_marktscan_last(c))
RS.leere_aggregat_cache()
wl = C.get_watchlist()
RS.build_status(c, wl, Path(D) / "keins.log")
t_b = zeit(lambda: RS.build_status(c, wl, Path(D) / "keins.log"))
pruefe("B5", t_pn < t_pa / 5 and t_mn < t_ma and t_b < 0.1,
       "Preise %.4f -> %.4f s · Marktscan %.4f -> %.4f s · warmer Aufbau %.3f s (Ziel < 0,1 s am Desktop)" % (t_pa, t_pn, t_ma, t_mn, t_b))

# B6
ist_frist = (getattr(RS._get_rollen_budget, "_frist_sekunden", None) or 0) >= 60 and "_get_rollen_budget" not in RS._LIVE_GETTER
RS.leere_aggregat_cache()
rb = RS._get_rollen_budget(c)
z = db.zaehle_rollen_urteile_heute(c)
pruefe("B6", ist_frist and rb["signale_heute"] == z["gesamt"] and rb.get("davon_hebel") == z["hebel"],
       "Frist %s s, nicht live: %s · Urteile heute %s/%s" % (getattr(RS._get_rollen_budget, "_frist_sekunden", None),
                                                          "_get_rollen_budget" not in RS._LIVE_GETTER, rb["signale_heute"], z["gesamt"]))
c.close()
pruefe("B7", summe(KOPIE) == vor, "Pruefsumme der Kopie %s" % ("gleich" if summe(KOPIE) == vor else "GEAENDERT"))
print()
print("%d von %d gleich" % (sum(ERG), len(ERG)))
