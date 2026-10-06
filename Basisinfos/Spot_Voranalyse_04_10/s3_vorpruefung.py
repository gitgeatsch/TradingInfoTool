"""S3-S6 Vorpruefung (06.10.2026): NUR Klassengroessen und Zuordnung, KEINE Ertraege.
Universum: Altcoins aus messdaten.db (mit eingestellten), ohne BTC, ohne Kern ETH/SOL, ohne Stablecoins. Klassen am Monatsersten:
Groesse nach 30-T-Umsatz-Rang (1-20 Highcap, 21-100 Midcap, 101+ Smallcap), Alter (Tage seit erstem Kurs), Schwankung (90-T, Drittel)."""
import os, sqlite3
import numpy as np, pandas as pd
os.chdir(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
c = sqlite3.connect("file:data/messdaten.db?mode=ro", uri=True)
k = pd.read_sql("SELECT symbol, date, close, volume FROM price_history_ohlc WHERE assetklasse='krypto' AND currency='USD'", c, parse_dates=["date"])
K = k.pivot(index="date", columns="symbol", values="close").sort_index().asfreq("D")
U = k.assign(u=k.close * k.volume).pivot(index="date", columns="symbol", values="u").sort_index().asfreq("D")
ret = K.pct_change(fill_method=None)
stable = {s for s in K.columns if ret[s].abs().median() < 0.002}
alts = [s for s in K.columns if s not in stable and s not in ("BTC", "ETH", "SOL")]
erst = K[alts].apply(lambda x: x.first_valid_index())
print("Universum: %d Altcoins (ohne BTC, ETH, SOL, %d Stablecoins) · Daten ab %s" % (len(alts), len(stable), K.index[0].date()))
print("  Jahr | Coins mit Kurs | High | Mid | Small | davon >= 2 Jahre gelistet | LINK-Rang (Juli)")
for j in range(2019, 2027):
    m = pd.Timestamp("%d-07-01" % j) if j < 2026 else pd.Timestamp("2026-07-01")
    vol = U.loc[m - pd.Timedelta(days=30):m, alts].mean().dropna()
    da = vol.index[K.loc[m, vol.index].notna()]
    r = vol[da].rank(ascending=False)
    alt2 = int(sum((m - erst[s]).days >= 730 for s in da))
    print("  %d |     %3d        |  %2d  | %3d |  %3d  |     %3d                  | %s" % (j, len(da), int((r <= 20).sum()), int(((r > 20) & (r <= 100)).sum()),
          int((r > 100).sum()), alt2, int(r.get("LINK")) if "LINK" in r else "-"))
m = pd.Timestamp("2026-07-01"); vol = U.loc[m - pd.Timedelta(days=30):m, alts].mean().dropna()
print("Highcaps 07/2026 (Top 20 nach Umsatz):", ", ".join(vol.sort_values(ascending=False).index[:20]))
