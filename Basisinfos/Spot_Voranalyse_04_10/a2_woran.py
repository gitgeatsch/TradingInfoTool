"""Altcoin Fassung 2 - WORAN (E-63), auf den Handeln von a2_messung: A1 (Boden je Coin mit Wende) Klassen M und S, Ausstieg X2 (Nachlauf).
Fragen: (1) Wie frueh wird ausgestoppt? (2) Wie viel Gewinn lag vor dem Ausstieg (MFE)? (3) Was tat der Coin NACH dem Ausstieg?
(4) War die Wende auch eine Wende GEGEN BTC (Coin/BTC ueber seinem 50-T-Schnitt am Einstieg)? (5) Unterschied nach Markt (BTC ueber steigendem 200-T)."""
import os, sys
import numpy as np, pandas as pd
os.chdir(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, "Basisinfos/Spot_Voranalyse_04_10")
import a2_messung as A
K, IDX, POS = A.K, A.IDX, A.POS
rel = K.div(K["BTC"], axis=0); rel50 = rel.rolling(50, min_periods=50).mean()
b200 = K["BTC"].rolling(200).mean(); markt_auf = (K["BTC"] > b200) & (b200 > b200.shift(20))
z = []
for t, s in A.mit_ruhe(A.A1):
    kl, _ = A.klassen(t.replace(day=1))
    if kl.get(s) not in ("M", "S") or A.epoche(t) not in ("E2", "E3"):
        continue
    i0 = POS[t] + 1
    v, b = A.pfad(s, i0, 730)
    if v is None or len(v) < 2:
        continue
    vk = A.ausstieg(v, "X2"); te = vk[-1][0]
    h = A.handel(s, i0, "X2")
    nach = K[s].values[i0 + te:i0 + te + 181]
    nach = nach[~np.isnan(nach)]
    nb = A.BTCV[i0 + te:i0 + te + len(nach)]
    z.append(dict(ep=A.epoche(t), kl=kl[s], tage=te, mfe=v[:te + 1].max() / v[0] - 1, vorteil=h["vorteil"],
                  nach180=(nach[-1] / nach[0]) / (nb[-1] / nb[0]) - 1 if len(nach) > 150 else np.nan,
                  rel_wende=bool(rel.at[t, s] > rel50.at[t, s]) if pd.notna(rel50.at[t, s]) else None, markt=bool(markt_auf.get(t, False))))
Z = pd.DataFrame(z)
print("A1 M+S, X2 - %d Handel" % len(Z))
for ep in ("E2", "E3"):
    x = Z[Z.ep == ep]
    print("\n%s (%d Handel)" % (ep, len(x)))
    print("  (1) Ausstieg nach Tagen: Median %d · innerhalb 30 T %.0f %% · innerhalb 60 T %.0f %%" % (x.tage.median(), 100 * (x.tage <= 30).mean(), 100 * (x.tage <= 60).mean()))
    print("  (2) groesster Gewinn VOR dem Ausstieg (MFE): Median %+.0f %% · >= +50 %%: %.0f %%" % (100 * x.mfe.median(), 100 * (x.mfe >= 0.5).mean()))
    print("  (3) Coin gegen BTC in den 180 T NACH dem Ausstieg: Median %+.0f %% (> 0 heisst: zu frueh ausgestiegen)" % (100 * x.nach180.median()))
    for w, g in x.groupby("rel_wende"):
        print("  (4) Wende auch gegen BTC = %s: n %d · Vorteil Mittel %+.1f %% · Median %+.1f %%" % (w, len(g), 100 * g.vorteil.mean(), 100 * g.vorteil.median()))
    for w, g in x.groupby("markt"):
        print("  (5) BTC im Aufwaertstrend = %s: n %d · Vorteil Mittel %+.1f %% · Median %+.1f %%" % (w, len(g), 100 * g.vorteil.mean(), 100 * g.vorteil.median()))
