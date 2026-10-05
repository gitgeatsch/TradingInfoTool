# Vorpruefung Fassung 3: NUR Zustand q (Klima-Gewicht) je Epoche, KEINE Ertraege
import sqlite3, numpy as np, pandas as pd
c=sqlite3.connect("file:data/_spot/coinmetrics.db?mode=ro",uri=True)
d=pd.read_sql("SELECT tag,PriceUSD k,CapMVRVCur m FROM tag WHERE asset='btc' ORDER BY tag",c,parse_dates=["tag"]).set_index("tag")
p=d.k.asfreq("D").ffill(); m=d.m.asfreq("D").ffill()
dd=p/p.cummax()-1; vol=np.log(p).diff().rolling(365,min_periods=300).std()*np.sqrt(365); ratio=p/p.rolling(1400,min_periods=1400).mean()
def roll(x): return x.rolling(1460,min_periods=730).rank(pct=True)
def wachs(x): x=x[x.index>="2013-01-01"]; return x.expanding(min_periods=365).rank(pct=True).reindex(p.index)
for name,f in (("rollend 4 J",roll),("wachsend ab 2013",wachs)):
    teile=[f(m), 1-f(-dd/vol), f(ratio)]
    verf=sum(t.notna().astype(int) for t in teile)
    q=(sum(t.fillna(0) for t in teile)/verf).where(verf>=2)
    print(name, "q ab", q.first_valid_index().date(), "| alle drei ab", (verf==3).idxmax().date())
    for e,a,b in (("E1","2017-01-01","2020-12-31"),("E2","2021-01-01","2024-01-10"),("E3","2024-01-11","2026-10-04")):
        x=q[a:b]; me=x[x.index.day==1]
        print("   %s %s..%s  q Mittel %.2f  Anteil Tage q<=0,2: %3.0f %%  q>=0,8: %3.0f %%  Kaufanteil (1-q) am Monatsersten Mittel %.2f"%(e,a,b,x.mean(),100*(x<=.2).mean(),100*(x>=.8).mean(),(1-me).mean()))
print("MVRV-Tief je Zyklus (Fakt):", ", ".join("%s %.2f"%(t,m[t]) for t in ("2015-01-14","2018-12-15","2020-03-12","2022-11-21","2026-06-30")))
