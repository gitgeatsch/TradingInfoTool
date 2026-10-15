"""P22b Umlauf-Zusatz fuer Coins ausserhalb Binance (15.10.2026, Spot §57 Variante B) - Pruefstand am SEITENEFFEKT, nur Wegwerf (D:).

    python Basisinfos/Rechenkern_02_10/p22b_pruefstand.py <Prod-Sicherung .db.gz>

Abruf GESTELLT (kein Netz): market_chart mit bekannter Menge (Freigabe +1 % am 14. jedes Monats), ein Stablecoin, eine zu kurze Reihe,
ein Abruffehler; /coins/markets mit bekanntem Tageswert. NB-Lage wie p22 (Betriebskopie 500 T, Mengendatei mit Marke _nur_betrieb).

  Z1  Kandidaten = Watchlist-Krypto mit CoinGecko-ID ohne Reihe in umlaufmenge, ohne Cash-Aequivalente
  Z2  Erstabruf: Menge = Marktwert/Preis exakt; Urteile ok / stablecoin / verworfen / Abruffehler (kein Urteil); umlaufmenge und Marke
      bitgleich
  Z3  zweiter Lauf: kein Erstabruf fuer Fertige, der Abruffehler wird wiederholt; Tageswert genau einmal je Tag
  Z4  B4 BITGLEICH mit und ohne Zusatz (abbau_fuenftel, abbau_lauf, Klassen); die Zusatz-Coins im Universum bekommen eine Verwaesserung
  Z5  turnover-Messbasis (marktrang.messbasis) bitgleich - die Zusatz-Symbole stehen NICHT darin
  Z6  fakt(): Zusatz-Coin mit Vermerk "angewandt, nicht ... gemessen", Wert = unabhaengig gerechnet; 0 % -> "laut CoinGecko unveraendert"
  Z7  PFAD: der echte Codeabschnitt aus scheduler/background.py (Job externe_reihen) laeuft und fuellt die Zusatztabelle
  Z8  stand() fuer Diagnose/Teilexport; Wegwerf-Produktion unveraendert
"""
import gzip
import hashlib
import os
import re
import shutil
import sqlite3
import subprocess
import sys
import tempfile
from datetime import date, datetime, timedelta, timezone

WURZEL = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(WURZEL)
sys.path.insert(0, WURZEL)
import wegwerf  # noqa: E402,F401

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

import agent.spot_abbau as SA  # noqa: E402
import agent.umlauf_zusatz as UZ  # noqa: E402
import agent.verwaesserung as VW  # noqa: E402
import config as C  # noqa: E402
import hole_umlaufmenge_cg as HU  # noqa: E402

ERG = []
UEBERNOMMEN = ["AIOZ", "AKT", "BRETT", "CAT", "GRIFFAIN", "HYPE", "KAS", "MORPHO", "PLUME", "SUPRA"]
RNG = np.random.default_rng(22022)


def pruefe(k, ok, text):
    ERG.append(bool(ok))
    print("%-4s %-9s %s" % (k, "bestanden" if ok else "FEHLER", text))


def summe(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def tabsumme(p, tab):
    c = sqlite3.connect("file:%s?mode=ro" % p.replace("\\", "/"), uri=True)
    h = hashlib.sha256(repr(c.execute("SELECT * FROM %s ORDER BY 1,2" % tab).fetchall()).encode()).hexdigest()
    c.close()
    return h


T = tempfile.mkdtemp(prefix="p22b_")
PROD_Q = os.path.join(T, "prod_q.db")
with gzip.open(sys.argv[1], "rb") as f, open(PROD_Q, "wb") as g:
    shutil.copyfileobj(f, g)
KOP = os.path.join(T, "kopie.db")
q = sqlite3.connect("file:data/messdaten.db?mode=ro", uri=True)
k = sqlite3.connect(KOP)
k.execute("CREATE TABLE price_history_ohlc (symbol TEXT, assetklasse TEXT, currency TEXT, date TEXT, open REAL, high REAL, low REAL, close REAL, "
          "volume REAL, fetched_at TEXT, quelle TEXT, PRIMARY KEY (symbol, currency, date))")
for s, letzt in q.execute("SELECT symbol, MAX(date) FROM price_history_ohlc WHERE assetklasse='krypto' AND currency='USD' GROUP BY symbol").fetchall():
    if s in UEBERNOMMEN:
        continue
    ab = (pd.Timestamp(letzt) - pd.Timedelta(days=499)).date().isoformat()
    k.executemany("INSERT INTO price_history_ohlc VALUES (?,?,?,?,?,?,?,?,?,?,?)", q.execute(
        "SELECT symbol, assetklasse, currency, date, open, high, low, close, volume, fetched_at, quelle FROM price_history_ohlc "
        "WHERE symbol=? AND assetklasse='krypto' AND currency='USD' AND date >= ?", (s, ab)).fetchall())
k.commit()
k.close()


def baue(name):
    o = os.path.join(T, name, "data")
    os.makedirs(o)
    shutil.copy(KOP, os.path.join(o, SA.KOPIE))
    u = os.path.join(o, SA.UMLAUF)
    shutil.copy("data/umlaufmenge_cg.db", u)
    c = sqlite3.connect(u)
    c.execute("CREATE TABLE _nur_betrieb (hinweis TEXT, tage INTEGER, gebaut_am TEXT)")
    c.execute("INSERT INTO _nur_betrieb VALUES ('Pruefstand', 365, '2026-10-15')")
    c.commit()
    c.close()
    shutil.copy(PROD_Q, os.path.join(o, "prod.db"))
    return o


# ══ gestellter Abruf ═════════════════════════════════════════════════════════════════════════════════════════════════════════
ENDE = date(2026, 9, 20)
TAGE = [ENDE - timedelta(days=365 - i) for i in range(366)]
ANRUFE = {"chart": [], "markets": []}
FEHLER_EINMAL = {"aster-2"}


def menge_soll(cid, d):
    """bekannte Menge: +1 % am 14. jedes Monats (HYPE/KAS/...), XDC fest (0 %)."""
    basis = 1e9 if cid != "xdce-crowd-sale" else 2e10
    if cid == "xdce-crowd-sale":
        return basis
    n = sum(1 for t in TAGE if t <= d and t.day == 14)
    return basis * 1.01 ** n


def http(url):
    if "/market_chart" in url:
        cid = re.search(r"/coins/([^/]+)/market_chart", url).group(1)
        ANRUFE["chart"].append(cid)
        if cid in FEHLER_EINMAL:
            FEHLER_EINMAL.discard(cid)
            return 429, None
        n = 200 if cid == "monad" else 366
        tage = TAGE[-n:]
        if cid == "societe-generale-forge-eurcv":
            pr = [1.0 + 0.0003 * RNG.standard_normal() for _ in tage]
        else:
            pr = list(np.exp(np.cumsum(0.03 * RNG.standard_normal(len(tage)))) * 2.0)
        ms = [int(datetime(t.year, t.month, t.day, tzinfo=timezone.utc).timestamp() * 1000) for t in tage]
        return 200, {"prices": [[m, p] for m, p in zip(ms, pr)], "market_caps": [[m, p * menge_soll(cid, t)] for m, p, t in zip(ms, pr, tage)]}
    if "/coins/markets" in url:
        ids = re.search(r"ids=([^&]+)", url).group(1).split(",")
        ANRUFE["markets"].append(ids)
        return 200, [{"id": i, "circulating_supply": menge_soll(i, ENDE) * 1.005} for i in ids]
    return 404, None


WL = C.get_watchlist()

# ══ Z1 Kandidaten ════════════════════════════════════════════════════════════════════════════════════════════════════════════
O = baue("nb")
U = os.path.join(O, SA.UMLAUF)
c = sqlite3.connect(U)
kand = UZ.kandidaten(c, WL)
c.close()
ks = {s for s, _ in kand}
erwartet = {"HYPE", "XDC", "KAS", "ASTER", "AIOZ", "AKT", "BRETT", "CAT", "GRIFFAIN", "SUPRA", "CANTON", "MON", "VSN", "BIO"}
pruefe("Z1", erwartet <= ks and "EURCV" not in ks and not (ks & {r[0] for r in sqlite3.connect(U).execute("SELECT DISTINCT symbol FROM umlaufmenge")}),
       "%d Kandidaten: %s · EURCV (Cash-Aequivalent) draussen %s" % (len(ks), ", ".join(sorted(ks)), "EURCV" not in ks))

# ══ Z2 Erstabruf ═════════════════════════════════════════════════════════════════════════════════════════════════════════════
haupt_vor, marke_vor = tabsumme(U, "umlaufmenge"), tabsumme(U, "_nur_betrieb")
wl2 = WL + [type("A", (), {"symbol": "EURCV2", "coingecko_id": "societe-generale-forge-eurcv", "assetklasse": "krypto",
                           "ist_cash_aequivalent": False})()]
e1 = UZ.pflege(U, wl2, http=http, heute=ENDE, pause=0)
c = sqlite3.connect(U)
urt = {r[0]: r[1] for r in c.execute("SELECT symbol, urteil FROM abruf_zusatz")}
hype = pd.read_sql("SELECT datum, wert FROM umlaufmenge_zusatz WHERE symbol='HYPE' ORDER BY datum", c)
c.close()
abw = max(abs(w / menge_soll("hyperliquid", date.fromisoformat(d[:10])) - 1) for d, w in zip(hype.datum, hype.wert) if d[:10] != ENDE.isoformat())
pruefe("Z2", urt.get("HYPE") == "ok" and urt.get("EURCV2") == "stablecoin" and urt.get("MON") == "verworfen" and urt.get("ASTER", "").startswith("abruf")
       and abw < 1e-9 and tabsumme(U, "umlaufmenge") == haupt_vor and tabsumme(U, "_nur_betrieb") == marke_vor,
       "Urteile %s · HYPE Menge = Marktwert/Preis, groesste Abweichung %.1e · umlaufmenge + Marke bitgleich %s" % (
           {s: urt.get(s) for s in ("HYPE", "XDC", "MON", "ASTER", "EURCV2")}, abw, tabsumme(U, "umlaufmenge") == haupt_vor))

# ══ Z3 zweiter Lauf ══════════════════════════════════════════════════════════════════════════════════════════════════════════
n_chart = len(ANRUFE["chart"])
e2 = UZ.pflege(U, wl2, http=http, heute=ENDE, pause=0)
neu_chart = ANRUFE["chart"][n_chart:]
c = sqlite3.connect(U)
n_heute = c.execute("SELECT COUNT(*) FROM umlaufmenge_zusatz WHERE datum=?", (ENDE.isoformat(),)).fetchone()[0]
n_ok = c.execute("SELECT COUNT(*) FROM abruf_zusatz WHERE urteil='ok'").fetchone()[0]
c.close()
e3 = UZ.pflege(U, wl2, http=http, heute=ENDE, pause=0)
# KORREKTUR 15.10. (erster Lauf: der Tageswert-Weg lief NIE - der Erstabruf liefert den heutigen Tag schon mit). Deshalb der Folgetag:
n_m = len(ANRUFE["markets"])
e4 = UZ.pflege(U, wl2, http=http, heute=ENDE + timedelta(days=1), pause=0)
c = sqlite3.connect(U)
w_folge = c.execute("SELECT wert FROM umlaufmenge_zusatz WHERE symbol='HYPE' AND datum=?", ((ENDE + timedelta(days=1)).isoformat(),)).fetchone()
c.close()
e5 = UZ.pflege(U, wl2, http=http, heute=ENDE + timedelta(days=1), pause=0)
pruefe("Z3", neu_chart == ["aster-2"] and e2["erstabruf"] == [("ASTER", "ok", 366)] and n_heute == n_ok and e3["tageswert"] == 0 and not e3["erstabruf"]
       and e4["tageswert"] == n_ok and len(ANRUFE["markets"]) == n_m + 1 and w_folge and abs(w_folge[0] / (menge_soll("hyperliquid", ENDE) * 1.005) - 1) < 1e-12
       and e5["tageswert"] == 0,
       "zweiter Lauf: market_chart nur %s · Erstabruf-Tag %d = ok %d · Folgetag: /coins/markets EIN Abruf, Tageswerte %d, HYPE = Sollwert %s · "
       "gleicher Tag nochmal: %d" % (neu_chart, n_heute, n_ok, e4["tageswert"], bool(w_folge), e5["tageswert"]))

# ══ Z4 B4 bitgleich ══════════════════════════════════════════════════════════════════════════════════════════════════════════
O0 = baue("ohne")


def lauf(o):
    cp = sqlite3.connect(os.path.join(o, "prod.db"))
    cp.row_factory = sqlite3.Row
    try:
        def h(sym):
            return [(dd[:10], cc) for dd, cc in q.execute("SELECT date, close FROM price_history_ohlc WHERE symbol=? AND assetklasse='krypto' "
                                                           "AND currency='USD' ORDER BY date", (sym,))]
        return SA.lauf(cp, o, WL, date(2026, 9, 5), h, mit_tabelle=True)
    finally:
        cp.close()


eA, e0 = lauf(O), lauf(O0)


def tabellen(o):
    c = sqlite3.connect(os.path.join(o, SA.ABLAGE))
    try:
        return (sorted(tuple(r) for r in c.execute("SELECT * FROM abbau_fuenftel")),
                sorted(tuple(r)[:1] + tuple(r)[2:] for r in c.execute("SELECT * FROM abbau_lauf")),
                {r[0]: r[1:] for r in c.execute("SELECT symbol, klasse, verw90, fuenftel FROM verw_universum")})
    finally:
        c.close()


fA, lA, vA = tabellen(O)
f0, l0, v0 = tabellen(O0)
kl_gleich = dict(zip(eA["_tabelle"].sym, eA["_tabelle"].kl)) == dict(zip(e0["_tabelle"].sym, e0["_tabelle"].kl))
im_uni = [s for s in ("HYPE", "XDC", "KAS", "BRETT", "SUPRA") if s in vA]
pruefe("Z4", fA == f0 and lA == l0 and kl_gleich and all(vA[s][1] is not None for s in im_uni) and all(v0[s][1] is None for s in im_uni if s in v0),
       "abbau_fuenftel gleich %s · abbau_lauf gleich %s · Klassen gleich %s · Zusatz-Coins im Universum mit Verwaesserung: %s (ohne Zusatz: keine)" % (
           fA == f0, lA == l0, kl_gleich, ", ".join("%s %+.1f %%" % (s, 100 * np.expm1(vA[s][1])) for s in im_uni)))
q.close()

# ══ Z5 turnover-Messbasis ════════════════════════════════════════════════════════════════════════════════════════════════════
code = "import sys; sys.path.insert(0, %r); import agent.marktrang as M; print(sorted(M.messbasis('turnover')))" % WURZEL
mb = [subprocess.run([sys.executable, "-c", code], cwd=os.path.dirname(o), capture_output=True, text=True).stdout.strip() for o in (O, O0)]
pruefe("Z5", mb[0] == mb[1] and mb[0] and "'XDC'" not in mb[0] and "'KAS'" not in mb[0], "turnover-Messbasis mit/ohne Zusatz gleich %s (%d Zeichen), XDC/KAS nicht darin %s" % (
    mb[0] == mb[1], len(mb[0]), "'XDC'" not in mb[0]))

# ══ Z6 fakt() ════════════════════════════════════════════════════════════════════════════════════════════════════════════════
fh = VW.fakt(O, "HYPE", ENDE)
# Sollwert am Folgetag: Tageswert (markets, x 1,005) gegen den Wert vor 90 T (market_chart)
ENDE1 = ENDE + timedelta(days=1)
fh = VW.fakt(O, "HYPE", ENDE1)
eig = np.log(menge_soll("hyperliquid", ENDE) * 1.005 / menge_soll("hyperliquid", ENDE1 - timedelta(days=90)))
fx = VW.fakt(O, "XDC", ENDE - timedelta(days=1))
pruefe("Z6", fh["zusatz"] and VW.ZUSATZ_VERMERK in fh["text"] and abs(fh["heute"] - eig) < 1e-9 and "laut CoinGecko unverändert" in fx["text"],
       "HYPE: %s (eigen %+.4f) | XDC: %s" % (fh["text"][:150], eig, fx["text"][:110]))

# ══ Z7 PFAD: der echte Abschnitt aus dem Job ═════════════════════════════════════════════════════════════════════════════════
O7 = baue("pfad")
U7 = os.path.join(O7, SA.UMLAUF)
quelle = open("scheduler/background.py", encoding="utf-8").read()
a = quelle.index("                # P22b (15.10.2026): Zusatz-Coins ausserhalb Binance")
b = quelle.index('                    logger.warning("Umlauf-Zusatz nicht gepflegt: %s", exc)\n', a)
block = quelle[a:b + len('                    logger.warning("Umlauf-Zusatz nicht gepflegt: %s", exc)\n')]
block = "\n".join(z[16:] for z in block.splitlines())
_orig = HU.hole
HU.hole = http
meldung = []
lg = type("L", (), {"info": lambda self, *x: meldung.append(("info", x[0] % x[1:])), "warning": lambda self, *x: meldung.append(("warn", x[0] % x[1:]))})()
_alt_pause = HU._PAUSE[0]
HU._PAUSE[0] = 0
try:
    exec(block, {"_ziel": U7, "logger": lg, "__name__": "pfad"})
finally:
    HU.hole = _orig
    HU._PAUSE[0] = _alt_pause
st7 = UZ.stand(U7)
pruefe("Z7", st7.get("tabelle") and (st7.get("je_urteil") or {}).get("ok", 0) >= 10 and meldung and meldung[0][0] == "info",
       "Job-Abschnitt: %s · stand %s" % (meldung[0][1][:160] if meldung else "-", st7.get("je_urteil")))

# ══ Z8 stand + Produktion ════════════════════════════════════════════════════════════════════════════════════════════════════
st = UZ.stand(U)
pruefe("Z8", st["tabelle"] and "HYPE" in st["ok"] and summe(os.path.join(O, "prod.db")) == summe(PROD_Q),
       "stand: %s, %s bis %s · Wegwerf-Produktion unveraendert %s" % (st["je_urteil"], st["von"], st["bis"], summe(os.path.join(O, "prod.db")) == summe(PROD_Q)))
wegwerf.aufraeumen(T)
print("\n%d von %d bestanden" % (sum(ERG), len(ERG)))
