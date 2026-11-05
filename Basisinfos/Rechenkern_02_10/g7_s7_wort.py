import pandas as pd, numpy as np
C = pd.read_csv("data/_g7/s7_zellen.csv", sep=";")
C = C[C.reaktion_btc.notna() & C.sigma.notna()].copy()
alter = (pd.to_datetime(C.tag).dt.tz_localize("UTC") - pd.to_datetime(C.erst, utc=True)).dt.total_seconds()/86400
C["z"] = C.reaktion_btc / (C.sigma * np.sqrt(alter.clip(lower=1/24)))
print("Zellen", len(C))
for g in (0.5, 1.0):
    w = np.where(C.z > g, "gestiegen", np.where(C.z < -g, "gefallen", "unveraendert"))
    print("Grenze +-%.1f sigma:" % g, pd.Series(w).value_counts(normalize=True).round(3).to_dict())
    C["w%.1f" % g] = w
# haengt das Wort am Meldungstyp? (dann bringt es S7 wenig Neues)
C["typ1"] = C.typen.str.split(",").str[0]
t = pd.crosstab(C.typ1, C["w0.5"], normalize="index").round(2)
t["n"] = C.typ1.value_counts()
print(t.sort_values("n", ascending=False).head(10))
# wie oft wechselt das Wort fuer dieselbe Meldung von Tag zu Tag (Lauf derselben Zelle)?
C = C.sort_values(["asset", "tag"])
same = C.groupby("asset")["w0.5"].shift(1)
print("Wort wie am Vortag (bei Folgezelle):", round((C["w0.5"] == same)[C.vortag].mean(), 3))
