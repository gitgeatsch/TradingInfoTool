"""P19 Season-Ampel - GEGENPROBE zum Bau auf einem ZWEITEN Weg (17.10.2026). Nur Wegwerf-Dateien.

    python Basisinfos/Rechenkern_02_10/p19_bau_gegenprobe.py

  G1  die Ampel auf derselben 500-T-Kopie mit dem Nachbau ``p19_voranalyse`` (14.10., unabhaengig geschrieben) und mit fredgraph.csv
      (ohne Schluessel) statt der FRED-API: Stand und Stufe roh je Tag gleich dem Modul?
  G2  Haltezeit mit der Zustandsmaschine aus ``p19_gegenprobe`` G2 (eigener Code) auf der Rohstufe des Moduls: geltende Stufe je Tag gleich?
  G3  Tag fuer Tag vom 01.08. bis 21.09.2026 mit echten Daten (52 Laeufe, dieselbe Ablage): genau EIN Wechsel kalt -> ungewohnt (am Tag,
      an dem die Rohstufe 7 Tage in Folge 'ungewohnt' war), nie 'faellig' (ungewohnt hat keine Handlung), keine Mail
"""
import os
import sqlite3
import sys
import tempfile
from datetime import date, timedelta

WURZEL = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, WURZEL)
sys.path.insert(0, os.path.join(WURZEL, "Basisinfos", "Spot_Voranalyse_04_10"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import wegwerf  # noqa: E402,F401
os.chdir(WURZEL)
sys.argv = ["x", "-"]
import pandas as pd  # noqa: E402

import config as C  # noqa: E402
C.load_env()
import p19_voranalyse as P  # noqa: E402
import agent.season_ampel as SA  # noqa: E402
import scheduler.background as BG  # noqa: E402
import agent.regel0_groesse as G  # noqa: E402

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:  # noqa: BLE001
    pass
ERG = []
PROD = r"D:\CLAUDE_Temp\TradingInfoTool\p19stand\prod.db"            # Wegwerf-Kopie der NB-Sicherung 16.10. 17:34 (nur lesend)


def baue_kopie(o, uebernommen):
    """Betriebskopie wie am NB: je Reihe die letzten 500 T der Messbasis, ohne die Uebernahmen (wie p18_/p19_pruefstand)."""
    q = sqlite3.connect("file:data/messdaten.db?mode=ro", uri=True)
    z = sqlite3.connect(os.path.join(o, SA.KOPIE))
    z.execute("CREATE TABLE price_history_ohlc (symbol TEXT, assetklasse TEXT, currency TEXT, date TEXT, open REAL, high REAL, low REAL, "
              "close REAL, volume REAL, fetched_at TEXT, quelle TEXT, PRIMARY KEY (symbol, currency, date))")
    for s, letzt in q.execute("SELECT symbol, MAX(date) FROM price_history_ohlc WHERE assetklasse='krypto' AND currency='USD' "
                              "GROUP BY symbol").fetchall():
        if s in uebernommen:
            continue
        ab = (pd.Timestamp(letzt) - pd.Timedelta(days=499)).date().isoformat()
        z.executemany("INSERT INTO price_history_ohlc VALUES (?,?,?,?,?,?,?,?,?,?,?)", q.execute(
            "SELECT symbol, assetklasse, currency, date, open, high, low, close, volume, fetched_at, quelle FROM price_history_ohlc "
            "WHERE symbol=? AND assetklasse='krypto' AND currency='USD' AND date >= ?", (s, ab)).fetchall())
    z.commit()
    z.close()
    q.close()


def pruefe(k, ok, text):
    ERG.append(bool(ok))
    print("%-3s %-10s %s" % (k, "gleich" if ok else "ABWEICHUNG", text))


T = tempfile.mkdtemp(prefix="p19g_")
O = os.path.join(T, "A")
os.makedirs(O)
baue_kopie(O, P.UEBERNOMMEN)
FR = SA.fred_reihen(os.environ["FRED_API_KEY"], date.today())
STB = SA.stablecoins()
HEUTE = date(2026, 9, 21)
SA.lauf(O, None, heute=HEUTE, quellen={"fred": FR, "stb": STB})
k = sqlite3.connect(os.path.join(O, SA.ABLAGE))
M = pd.read_sql("SELECT * FROM ampel_tag", k, parse_dates=["datum"]).set_index("datum")
k.close()

# ── G1: zweiter Rechenweg (p19_voranalyse-Funktionen, fredgraph.csv)
kc = sqlite3.connect(os.path.join(O, SA.KOPIE))
d = pd.read_sql("SELECT symbol, date, close, volume FROM price_history_ohlc", kc)
kc.close()
d["date"] = pd.to_datetime(d.date.str[:10])
K = d.pivot(index="date", columns="symbol", values="close").sort_index().asfreq("D")
U = d.assign(u=d.close * d.volume).pivot(index="date", columns="symbol", values="u").sort_index().asfreq("D")
ret = K.pct_change(fill_method=None)
stable = {s for s in K.columns if ret[s].abs().median() < 0.002}
alts = [s for s in K.columns if s not in stable and s != "BTC"]
tage = list(M.index)
br = P.breite(K, U, alts, K["BTC"], tage)
idx = pd.date_range("2019-01-01", pd.Timestamp(HEUTE) - pd.Timedelta(days=1), freq="D")
m2 = P.fred("M2SL", 35)
B2 = P.taeglich(m2 / m2.shift(12) - 1, idx)
st_t = P.taeglich(STB, idx)
B3 = st_t / st_t.shift(91) - 1
B = K["BTC"].reindex(idx)
B1 = B / B.shift(91) - 1
X = pd.DataFrame({"B1": B1.reindex(tage), "B2": B2.reindex(tage), "B3": B3.reindex(tage), "Breite": br.reindex(tage)}, index=pd.DatetimeIndex(tage))
X["stand"] = [P.stand(a, b, c) for a, b, c in zip(X.B1, X.B2, X.B3)]
X["stufe"] = P.stufen(X)
g_st = (X.stand.values == M.stand.values)
g_sf = (X.stufe.values == M.stufe_roh.values)
d_br = (X.Breite - M.breite).abs().max()
d_b2 = (X.B2 - M.b2).abs().max()
pruefe("G1", g_st.all() and g_sf.all(), "%d Tage: Stand gleich %d, Stufe roh gleich %d · B2 aus fredgraph.csv gegen FRED-API groesste Abweichung %.1e · "
       "Breite eigener Weg groesste %.1e" % (len(M), int(g_st.sum()), int(g_sf.sum()), d_b2, d_br))

# ── G2: Haltezeit mit der Zustandsmaschine aus p19_gegenprobe
s = M.stufe_roh
lauf = (s != s.shift(1)).cumsum()
laenge = s.groupby(lauf).transform("size")
pos = s.groupby(lauf).cumcount() + 1
akt, aus = s.iloc[0], []
for st, ln, ps in zip(s, laenge, pos):
    if st != akt and ps >= 7:
        akt = st
    aus.append(akt)
e = pd.Series(aus, index=s.index)
pruefe("G2", (e.values == M.stufe.values).all(), "geltende Stufe je Tag gleich %d von %d · Wechsel %s" % (
    int((e.values == M.stufe.values).sum()), len(M), " · ".join("%s %s" % (t_.date(), v) for t_, v in e[e != e.shift(1)].items())))

# ── G3: Tag fuer Tag
O3 = os.path.join(T, "B")
os.makedirs(O3)
baue_kopie(O3, P.UEBERNOMMEN)
POST = []
G.season_ampel_aktiv = lambda werte=None: False
faellig, wechsel = [], []
t = date(2026, 8, 1)
while t <= HEUTE:
    j = BG.season_ampel_job(lambda: sqlite3.connect("file:%s?mode=ro" % PROD.replace(chr(92), "/"), uri=True), versand=lambda b, x, bi=None: POST.append(b) or True, heute=t, ordner=O3,
                            quellen={"fred": FR, "stb": STB})
    if j.get("faellig"):
        faellig.append((t, j["faellig"]["stufe"]))
    if j.get("wechsel"):
        wechsel.append((t, j["wechsel"]["von"], j["wechsel"]["nach"], j["wechsel"]["seit"]))
    t += timedelta(days=1)
k = sqlite3.connect(os.path.join(O3, SA.ABLAGE))
mel = k.execute("SELECT stufe, seit, art FROM ampel_meldung ORDER BY rowid").fetchall()
k.close()
erwartet = e[e != e.shift(1)]
erw_ungewohnt = [t_.date().isoformat() for t_, v in erwartet.items() if v == "ungewohnt"]
pruefe("G3", len(wechsel) == 1 and wechsel[0][1] == "kalt" and wechsel[0][2] == "ungewohnt" and wechsel[0][3] in erw_ungewohnt
       and not faellig and not POST and wechsel[0][0] == date.fromisoformat(wechsel[0][3]) + timedelta(days=1),
       "%d Laeufe: Wechsel %s (erwartet geltend seit %s, gemeldet am Folgetag, weil der Tag erst dann abgeschlossen ist) · faellig %s · Mails %d · "
       "Meldungen %s" % ((HEUTE - date(2026, 8, 1)).days + 1, wechsel, erw_ungewohnt, faellig, len(POST), mel))

wegwerf.aufraeumen(T)
print("\n%d von %d gleich" % (sum(ERG), len(ERG)))
sys.exit(0 if all(ERG) else 1)
