"""S1 Vorpruefung (06.10.2026): Datenlage und EREIGNIS 'echte Altcoin-Phase' (wie K-4 'echter Boden': das Ereignis ist per Definition
rueckblickend), dazu die Zustandshaeufigkeit der Kandidaten-Fakten. KEINE Messung, ob ein Fakt die Phase vorhersagt.
Korb: Top 50 nach 30-Tage-Umsatz (USD) am Monatsersten, gleich gewichtet, mit eingestellten Werten, ohne BTC und Stablecoins."""
import os, sqlite3
import numpy as np, pandas as pd
os.chdir(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
c = sqlite3.connect("file:data/messdaten.db?mode=ro", uri=True)
k = pd.read_sql("SELECT symbol, date, close, volume FROM price_history_ohlc WHERE assetklasse='krypto' AND currency='USD' AND date>='2018-09-01'", c, parse_dates=["date"])
K = k.pivot(index="date", columns="symbol", values="close").sort_index().asfreq("D")
U = (k.assign(u=k.close * k.volume).pivot(index="date", columns="symbol", values="u").sort_index().asfreq("D"))
ret = K.pct_change(fill_method=None)
stable = {s for s in K.columns if ret[s].abs().median() < 0.002}
alts = [s for s in K.columns if s not in stable and s != "BTC"]
B = K["BTC"]
# Korb-Index: monatlich neu Top 50 nach 30-T-Umsatz, taeglich gleich gewichtete Rendite (ffill fuer eingestellte: letzter Kurs, dann 0-Rendite)
idx = K.index[K.index >= "2019-01-01"]
korb_r = pd.Series(0.0, index=idx)
for m in pd.date_range("2019-01-01", idx[-1], freq="MS"):
    vol = U.loc[m - pd.Timedelta(days=30):m, alts].mean().dropna()
    top = vol.sort_values(ascending=False).index[:50]
    sl = (idx >= m) & (idx < m + pd.offsets.MonthBegin(1))
    r = ret.loc[idx[sl], top].fillna(0.0)
    korb_r[idx[sl]] = r.mean(axis=1)
korb = (1 + korb_r).cumprod()
rel90_vor = (korb.shift(-90) / korb) / (B.reindex(idx).shift(-90) / B.reindex(idx)) - 1      # Ereignis: VORAUS 90 T
phase = rel90_vor >= 0.25
ep, a0 = [], None
for t, v in phase.items():
    if v and a0 is None: a0 = t
    if not v and a0 is not None:
        if ep and (a0 - ep[-1][1]).days < 30: ep[-1] = (ep[-1][0], t)
        else: ep.append((a0, t))
        a0 = None
print("ECHTE ALTCOIN-PHASEN (Korb Top 50 schlaegt BTC in den folgenden 90 T um >= 25 Pp; Luecke < 30 T verbindet):")
for a, e in ep:
    if (e - a).days >= 7:
        print("  %s bis %s (%3d T) · bester Vorsprung %+.0f %%" % (a.date(), e.date(), (e - a).days, 100 * rel90_vor[a:e].max()))
print("  Tage mit Phase je Jahr:", phase.groupby(phase.index.year).sum().to_dict())
# Kandidaten-Fakten: nur Zustandshaeufigkeit
eb = pd.read_sql("SELECT tag, PriceUSD FROM tag WHERE asset='eth'", sqlite3.connect("file:data/_spot/coinmetrics.db?mode=ro", uri=True), parse_dates=["tag"]).set_index("tag").PriceUSD
bb = pd.read_sql("SELECT tag, PriceUSD FROM tag WHERE asset='btc'", sqlite3.connect("file:data/_spot/coinmetrics.db?mode=ro", uri=True), parse_dates=["tag"]).set_index("tag").PriceUSD
ethbtc = (eb / bb).reindex(idx)
f1 = (ethbtc > ethbtc.rolling(200).mean()) & (ethbtc.rolling(200).mean() > ethbtc.rolling(200).mean().shift(20))
breite = pd.Series(np.nan, index=idx)
for t in idx[90:]:
    m = t.replace(day=1)
    vol = U.loc[m - pd.Timedelta(days=30):m, alts].mean().dropna()
    top = vol.sort_values(ascending=False).index[:50]
    a90 = K.loc[t, top] / K.loc[t - pd.Timedelta(days=90), top]
    breite[t] = float((a90 > B[t] / B[t - pd.Timedelta(days=90)]).mean())
f2 = breite >= 0.75
rs = (korb / B.reindex(idx)); f3 = (rs > rs.rolling(200).mean()) & (rs.rolling(200).mean() > rs.rolling(200).mean().shift(20))
print("\nKANDIDATEN-FAKTEN, Tage 'an' je Jahr (nur Zustand):")
for n, f in (("F1 ETH/BTC ueber steigendem 200-T-Schnitt", f1), ("F2 Altseason-Breite: >= 75 % der Top 50 schlugen BTC in den letzten 90 T", f2), ("F3 Korb/BTC ueber steigendem 200-T-Schnitt", f3)):
    print("  %-72s %s" % (n, f.groupby(f.index.year).sum().astype(int).to_dict()))
