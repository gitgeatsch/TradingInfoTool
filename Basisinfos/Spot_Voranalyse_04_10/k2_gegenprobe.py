# Gegenprobe K-2 (python Basisinfos/Spot_Voranalyse_04_10/k2_gegenprobe.py): V2/DCA unabhaengig nachgerechnet (andere Schleife), dazu WORAN: wohin floss das Kapital
import sys, importlib.util, numpy as np, pandas as pd
sys.argv=["x"]
spec=importlib.util.spec_from_file_location("k2","Basisinfos/Spot_Voranalyse_04_10/k2_zone_aufbau.py")
src=open("Basisinfos/Spot_Voranalyse_04_10/k2_zone_aufbau.py",encoding="utf-8").read().split("ergebnis = {}")[0]
g={"__file__":"Basisinfos/Spot_Voranalyse_04_10/k2_zone_aufbau.py"}; exec(compile(src,"k2","exec"),g)
for asset,ab in (("btc","2013-01-01"),("eth","2015-08-08")):
    p,m=g["lade"](asset); A=g["zone"](p,m,pd.Timestamp(ab))
    # unabhaengig: Zufluss-Tage aus Monatsliste, Kauf t+1 ueber Index-Verschiebung
    tage=p["2017-01-01":].index; bar=0; coins=0; rows=[]
    for i,t in enumerate(tage):
        if t.day==1: bar+=1
        prev=t-pd.Timedelta(days=1)
        if bool(A.get(prev,False)):
            k=bar/30; coins+=k/p[t]; bar-=k; rows.append((t,k,p[t]))
    v2=coins*p.iloc[-1]+bar
    dca=sum(1/p[t] for t in tage if t.day==1)*p.iloc[-1]
    print(asset.upper(),"Gegenprobe Start 2017: V2 %.1f DCA %.1f Verhaeltnis %.2f"%(v2,dca,v2/dca))
    r=pd.DataFrame(rows,columns=["t","betrag","kurs"]).set_index("t")
    r["ep"]=(r.index.to_series().diff().dt.days.fillna(999)>=30).cumsum()
    for e,gr in r.groupby("ep"):
        print("   Kaeufe %s..%s: Kapital %5.1f zum Mittel %10.2f"%(gr.index[0].date(),gr.index[-1].date(),gr.betrag.sum(),(gr.betrag.sum()/(gr.betrag/gr.kurs).sum())))
