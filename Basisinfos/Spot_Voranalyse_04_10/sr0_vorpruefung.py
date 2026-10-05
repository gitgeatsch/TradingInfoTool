# Vorpruefung SPOT-REGEL0: NUR Ereigniszahlen je Familie und Jahr, KEINE Ertraege
import sqlite3, numpy as np, pandas as pd
c=sqlite3.connect("file:data/messdaten.db?mode=ro",uri=True)
k=pd.read_sql("SELECT symbol,date,close FROM price_history_ohlc WHERE assetklasse='krypto' AND currency='USD' AND date>='2022-06-01'",c,parse_dates=["date"]); c.close()
K=k.pivot(index="date",columns="symbol",values="close").sort_index().asfreq("D")
print("Symbole",K.shape[1],"Tage",K.index[0].date(),"bis",K.index[-1].date())
s50=K.rolling(50,min_periods=50).mean()
d=K.diff(); up=d.clip(lower=0).ewm(alpha=1/14,min_periods=14).mean(); dn=(-d.clip(upper=0)).ewm(alpha=1/14,min_periods=14).mean(); rsi=100-100/(1+up/dn)
def erst(bed, vorher, ruhe):
    b=bed.fillna(False); vor=(~b).astype(int).rolling(vorher).sum().shift(1)==vorher
    ev=b&vor
    out=ev.copy()*False
    for s in ev.columns:
        last=None
        for t in ev.index[ev[s]]:
            if last is None or (t-last).days>=ruhe: out.loc[t,s]=True; last=t
    return out
fam={"T Trendwende (Schluss > S50 nach 20 T darunter)":erst(K>s50,20,20),
     "T' Spiegel (Schluss < S50 nach 20 T darueber)":erst(K<s50,20,20),
     "R Rueckgang (RSI14 < 30 Ersteintritt nach 10 T)":erst(rsi<30,10,10),
     "R' Spiegel (RSI14 > 70 Ersteintritt nach 10 T)":erst(rsi>70,10,10)}
for n,e in fam.items():
    j=e.sum(axis=1).groupby(e.index.year).sum()
    print("%-50s"%n, " ".join("%d: %5d"%(y,v) for y,v in j.items()), "| Assets mit >=1 Ereignis 2024: %d"%int((e.loc["2024"].sum()>0).sum()))
