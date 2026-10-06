"""Vorpruefung Liquiditaet und Verwaesserung (python Basisinfos/Spot_Voranalyse_04_10/l1_vorpruefung.py) - NUR Datenlage, keine Wirkung.

Liest FRED (ohne Schluessel, fredgraph.csv) und DefiLlama (Stablecoins gesamt) live, schreibt nichts.
  - Netto-Liquiditaet USA = WALCL - WTREGEN - RRPONTSYD (Wochenwert, Mittwoch); Veroeffentlichung Donnerstag -> nutzbar ab Freitag
  - Stablecoin-Umlauf gesamt (DefiLlama), M2SL (monatlich, Veroeffentlichung ~4 Wochen spaeter)
  - Wie viele PHASEN (Vorzeichen der 13-Wochen-Aenderung) gibt es je Epoche? Das ist die Fallzahl fuer jede Aussage ueber die Zeit
  - Wie viele A1-Ereignisse (Fassung 2/3) haben eine Umlaufmengen-Historie (onchain_historie.splycur, umlaufmenge_cg)?
"""
import io, os, sqlite3, sys
import pandas as pd, requests

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HIER)


def fred(s):
    r = requests.get("https://fred.stlouisfed.org/graph/fredgraph.csv?id=" + s, timeout=60)
    d = pd.read_csv(io.StringIO(r.text)); d.columns = ["datum", s]
    d["datum"] = pd.to_datetime(d["datum"]); d[s] = pd.to_numeric(d[s], errors="coerce")
    return d.set_index("datum")[s]


walcl, tga, rrp, m2 = fred("WALCL"), fred("WTREGEN"), fred("RRPONTSYD"), fred("M2SL")
w = pd.concat([walcl, tga, rrp.resample("W-WED").last()], axis=1).dropna()
netto = (w["WALCL"] - w["WTREGEN"] - w["RRPONTSYD"] * 1000) / 1e6       # Bio. USD (WALCL/WTREGEN Mio., RRP Mrd.)
j = requests.get("https://stablecoins.llama.fi/stablecoincharts/all", timeout=60).json()
st = pd.Series({pd.Timestamp(int(x["date"]), unit="s"): x["totalCirculatingUSD"].get("peggedUSD", 0) for x in j}).sort_index() / 1e9


def phasen(x, name, frist):
    a = (x / x.shift(frist) - 1).dropna()
    a = a[a.index >= "2019-01-01"]
    vz = (a > 0).astype(int); wechsel = vz.diff().abs().fillna(0).cumsum()
    print("\n%s (Aenderung ueber %d Werte) - Phasen ab 2019:" % (name, frist))
    for p, g in a.groupby(wechsel):
        print("  %s bis %s  %-9s  %3d Wochen  Aenderung von %+.1f %% bis %+.1f %%" % (
            g.index[0].date(), g.index[-1].date(), "STEIGEND" if g.iloc[0] > 0 else "fallend", len(g) if frist == 13 else len(g) // 7, 100 * g.min(), 100 * g.max()))
    for e, (a0, a1) in {"E2": ("2021-01-01", "2024-01-10"), "E3": ("2024-01-11", "2026-12-31")}.items():
        g = a[(a.index >= a0) & (a.index <= a1)]
        print("  %s: steigend in %3.0f %% der Zeit, %d Vorzeichenwechsel" % (e, 100 * (g > 0).mean(), int((g > 0).astype(int).diff().abs().sum())))


print("Datenlage bis: Netto-Liquiditaet %s · Stablecoins %s · M2 %s" % (netto.index[-1].date(), st.index[-1].date(), m2.dropna().index[-1].date()))
print("Netto-Liquiditaet heute %.2f Bio. USD (WALCL %.2f, TGA %.2f, RRP %.3f)" % (netto.iloc[-1], w["WALCL"].iloc[-1] / 1e6, w["WTREGEN"].iloc[-1] / 1e6, w["RRPONTSYD"].iloc[-1] / 1e3))
phasen(netto, "Netto-Liquiditaet USA", 13)
phasen(st, "Stablecoin-Umlauf", 91)

import a2_messung as A  # noqa: E402
ev = A.mit_ruhe(A.A1)
c = sqlite3.connect("file:data/onchain_historie.db?mode=ro", uri=True)
sp = {s: (pd.Timestamp(a), pd.Timestamp(b)) for s, a, b in c.execute("SELECT symbol, MIN(datum), MAX(datum) FROM splycur GROUP BY symbol")}
c2 = sqlite3.connect("file:data/umlaufmenge_cg.db?mode=ro", uri=True)
cg = {s: (pd.Timestamp(a), pd.Timestamp(b)) for s, a, b in c2.execute("SELECT symbol, MIN(datum), MAX(datum) FROM umlaufmenge GROUP BY symbol")}
print("\nA1-Ereignisse mit Umlaufmenge 180 T VOR dem Ereignis (Wachstum messbar):")
for e in ("E1", "E2", "E3"):
    x = [(t, s) for t, s in ev if A.epoche(t) == e]
    def hat(q, t, s): return s in q and q[s][0] <= t - pd.Timedelta(days=180) and q[s][1] >= t
    a = sum(hat(sp, t, s) for t, s in x); b = sum(hat(cg, t, s) for t, s in x); ab = sum(hat(sp, t, s) or hat(cg, t, s) for t, s in x)
    kl = {}
    for t, s in x:
        if hat(sp, t, s) or hat(cg, t, s):
            k = A.klassen(t.replace(day=1))[0].get(s, "-"); kl[k] = kl.get(k, 0) + 1
    print("  %s  %4d Ereignisse · Coin Metrics %4d · CoinGecko %4d · eines von beiden %4d  (Klassen %s)" % (e, len(x), a, b, ab, kl))
