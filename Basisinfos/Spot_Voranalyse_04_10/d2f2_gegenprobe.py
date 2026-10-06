"""Gegenprobe D2 Fassung 2 (python Basisinfos/Spot_Voranalyse_04_10/d2f2_gegenprobe.py): BTC K1 ab 2017 und ETH K2 ab 2019, eigene einfache Schleife."""
import os
import pandas as pd
os.chdir(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
src = open("Basisinfos/Spot_Voranalyse_04_10/k3_gewichten.py", encoding="utf-8").read().split("pb, mb = lade")[0]
g = {"__file__": os.path.abspath("Basisinfos/Spot_Voranalyse_04_10/k3_gewichten.py")}; exec(compile(src, "k3", "exec"), g)
pb, mb = g["lade"]("btc"); pe, _ = g["lade"]("eth"); q = g["klima"](pb, mb, pd.Timestamp("2013-01-01"))


def rechne(p, start, art, scharf_ab, stufen):
    tage = pd.date_range(start, p.index[-1]); stk = h = geld = 0.0
    an, hoch, offen, z = False, 0.0, [], None
    for t in tage:
        if t == tage[0] or t.day == 1:
            stk += 1 / p[t]; h += 1 / p[t]
        x = q.get(t - pd.Timedelta(days=1))
        if x is None or x != x:
            continue
        if x <= 0.2:
            an, hoch, offen = False, 0.0, []
            if geld > 0:
                if z is None:
                    z = [geld, t, set()]
                for gr in (0.2, 0.1, 0.05):
                    if x <= gr and gr not in z[2]:
                        z[2].add(gr); b = min(z[0] / 3 if gr != 0.05 else geld, geld); stk += b / p[t]; geld -= b
        if x >= scharf_ab and not an:
            an, hoch, offen = True, x, list(stufen)
        if an:
            hoch = max(hoch, x)
            for s in list(offen):
                if x < (s if art == "abs" else hoch - s):
                    offen.remove(s); geld += 0.1 * stk * p[t]; stk *= 0.9
        if z is not None and geld > 0 and (t - z[1]).days >= 365:
            stk += geld / p[t]; geld = 0.0
        if z is not None and geld <= 1e-12:
            z = None
    return stk / h


print("BTC K1 ab 2017: Stueck / H0 = %.3f" % rechne(pb, "2017-01-01", "abs", 0.90, (0.85, 0.75, 0.65)))
print("ETH K2 ab 2019: Stueck / H0 = %.3f" % rechne(pe, "2019-01-01", "rel", 0.80, (0.10, 0.20, 0.30)))
