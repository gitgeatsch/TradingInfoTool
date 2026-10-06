"""Gegenprobe L1-L4 (python Basisinfos/Spot_Voranalyse_04_10/l_gegenprobe.py) - eigener Rechenweg, nur lesend.

  G1 Liquiditaetszustand: FRED neu geladen, Zustand per merge_asof auf (t - 2 T) statt searchsorted -> alle A1-Ereignisse vergleichen
  G2 Umlaufwachstum: 8 Ereignisse direkt per SQL nachgerechnet
  G3 L1 E2/E3 X4: Unterschied mit dem Zustand aus G1 und eigener Tagesklammer neu gerechnet
  G4 L4 E3 'q Mitte' und E2 'q Mitte': BTC-Folgeertrag mit eigener Schleife direkt aus SQL
"""
import io, os, random, sqlite3, sys
from datetime import timedelta
import numpy as np, pandas as pd, requests

os.chdir(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, "Basisinfos/Spot_Voranalyse_04_10")
import l_messung as L  # noqa: E402
A, M = L.A, L.M


def fred(s):
    d = pd.read_csv(io.StringIO(requests.get("https://fred.stlouisfed.org/graph/fredgraph.csv?id=" + s, timeout=60).text))
    d.columns = ["datum", "v"]; d["datum"] = pd.to_datetime(d["datum"]); d["v"] = pd.to_numeric(d["v"], errors="coerce")
    return d.dropna()


wa, tg, rr = fred("WALCL"), fred("WTREGEN"), fred("RRPONTSYD")
rr["woche"] = rr["datum"] + pd.to_timedelta((2 - rr["datum"].dt.weekday) % 7, unit="D")     # auf den Mittwoch dieser Woche
rrw = rr.groupby("woche")["v"].last()
n = wa.set_index("datum")["v"].to_frame("wa").join(tg.set_index("datum")["v"].rename("tg"), how="inner").join(rrw.rename("rr"), how="inner")
n["netto"] = n["wa"] - n["tg"] - n["rr"] * 1000
n["st"] = n["netto"] > n["netto"].shift(13)
n = n[n["netto"].shift(13).notna()].reset_index().rename(columns={"index": "datum"})
n["ab"] = n["datum"] + timedelta(days=2)

d = L.ereignisse("X4")
q = pd.DataFrame({"t": d["t"]}).sort_values("t")
z = pd.merge_asof(q, n[["ab", "st"]].sort_values("ab"), left_on="t", right_on="ab", direction="backward")
eigen = z.set_index(q.index)["st"].reindex(d.index)
mess = pd.Series([L.ZW[w] if w >= 0 else np.nan for w in d["wi"]], index=d.index)
ok = eigen.notna() & (d["wi"] >= 13)
print("G1 Liquiditaetszustand: %d von %d Ereignissen gleich" % (int((eigen[ok].astype(bool) == mess[ok].astype(bool)).sum()), int(ok.sum())))

random.seed(9)
c = sqlite3.connect("file:data/onchain_historie.db?mode=ro", uri=True)
c2 = sqlite3.connect("file:data/umlaufmenge_cg.db?mode=ro", uri=True)
kand = [(t, s) for t, s in zip(d["t"], d["sym"]) if L.wachstum(s, t)[0] is not None]
gl = 0
for t, s in random.sample(kand, 8):
    g, quelle, fe = L.wachstum(s, t)
    con, tab = (c, "splycur") if quelle == "CM" else (c2, "umlaufmenge")
    a = con.execute("SELECT wert FROM %s WHERE symbol=? AND datum<=? ORDER BY datum DESC LIMIT 1" % tab, (s, t.date().isoformat())).fetchone()[0]
    b = con.execute("SELECT wert FROM %s WHERE symbol=? AND datum<=? ORDER BY datum DESC LIMIT 1" % tab, (s, (t - timedelta(days=180)).date().isoformat())).fetchone()[0]
    e = a / b - 1; gl += abs(e - g) < 1e-12
    print("G2 %s %-8s %s  Messung %+.4f  Gegenprobe %+.4f%s" % (t.date(), s, quelle, g, e, "  (Datenfehler)" if fe else ""))
print("G2 %d von 8 gleich" % gl)

for ep in ("E2", "E3"):
    x = d[(d["ep"] == ep) & ok]
    st = eigen[x.index].astype(bool)
    def klammer(m):
        sumv, zahl = {}, {}
        for e_, v in zip(x["einstieg"][m], x["vorteil"][m]):
            sumv[e_] = sumv.get(e_, 0) + v; zahl[e_] = zahl.get(e_, 0) + 1
        return sum(sumv[k] / zahl[k] for k in sumv) / len(sumv)
    print("G3 L1 X4 %s  Unterschied Gegenprobe %+.4f  (Messung siehe l_messung.txt)" % (ep, klammer(st.values) - klammer(~st.values)))

cm = sqlite3.connect("file:data/messdaten.db?mode=ro", uri=True)
btc = dict(cm.execute("SELECT date, close FROM price_history_ohlc WHERE assetklasse='krypto' AND currency='USD' AND symbol='BTC'").fetchall())
qs = pd.Series(M.QV, index=A.IDX)
for ep, a0, a1 in (("E2", "2021-01-01", "2024-01-10"), ("E3", "2024-01-11", "2026-12-31")):
    werte = {True: [], False: []}
    for t in A.IDX[(A.IDX >= a0) & (A.IDX <= a1)]:
        qv = qs[t]
        if np.isnan(qv) or not (1 / 3 <= qv < 2 / 3):
            continue
        k1, k2 = (t + timedelta(days=1)).date().isoformat(), (t + timedelta(days=181)).date().isoformat()
        if k1 not in btc or k2 not in btc:
            continue
        r = z_ = n[n["ab"] <= t]
        if not len(r):
            continue
        werte[bool(r["st"].iloc[-1])].append(btc[k2] / btc[k1] - 1)
    print("G4 L4 %s q Mitte  Tage %d (steigend %d) · steigend %+.4f · fallend %+.4f · Unterschied %+.4f" % (
        ep, len(werte[True]) + len(werte[False]), len(werte[True]), np.mean(werte[True]), np.mean(werte[False]), np.mean(werte[True]) - np.mean(werte[False])))
