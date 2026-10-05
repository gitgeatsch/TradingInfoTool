"""Spot G1-M2 (Voranalyse_Spot_Neubau_04_10.md §10.7, Commit 289a872): Grundrate Altcoins gegen BTC, unverzerrt, je Epoche.

    python Basisinfos/Spot_Voranalyse_04_10/g1_m2_grundrate_altcoins.py

Nur lesend: data/messdaten.db (Krypto USD, mit eingestellten Werten). Kein Netz.

AUSLEGUNG, vor dem ersten Lauf festgelegt (im Plan nicht genau bestimmt):
  - Kurs am Start: Schluss am Starttag; fehlt er, gilt der Coin an diesem Start als nicht gelistet
  - eingestellt: letzter Kurs liegt vor t+h UND mehr als 10 T vor dem Datenende
  - Hebeltoken: Endung UP/DOWN/BULL/BEAR und der Grundname ist selbst ein Symbol der Menge
  - Liquiditaet (Auskunft): Mittel von Schluss x Volumen der 30 T vor dem Start
"""
import json
import os
import sqlite3

import numpy as np
import pandas as pd

os.chdir(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
H = (90, 180, 365, 730)
EPOCHEN = (("E1 2019-2020", "2019-01-01", "2020-12-31"), ("E2 2021-10.01.2024", "2021-01-01", "2024-01-10"), ("E3 ab 11.01.2024", "2024-01-11", "2099-01-01"))

c = sqlite3.connect("file:data/messdaten.db?mode=ro", uri=True)
k = pd.read_sql("SELECT symbol, date, close, volume FROM price_history_ohlc WHERE assetklasse='krypto' AND currency='USD' AND date>='2018-06-01'",
                c, parse_dates=["date"])
c.close()
K = k.pivot(index="date", columns="symbol", values="close").sort_index()
V = (k.assign(u=k["close"] * k["volume"]).pivot(index="date", columns="symbol", values="u").sort_index())
ENDE = K.index.max()
alle = set(K.columns)
ret = K.pct_change(fill_method=None)
stable = {s for s in alle if ret[s].abs().median() < 0.002}
hebel = {s for s in alle for suf in ("UP", "DOWN", "BULL", "BEAR") if s.endswith(suf) and s[:-len(suf)] in alle}
ALT = sorted(alle - {"BTC"} - stable - hebel)
letzter = {s: K[s].last_valid_index() for s in ALT}
nutzer = set()
try:
    d = json.load(open(r"K:\My Drive\Claude_Austauschordner\Notebook_Analysedaten\bitpanda_transaktionen.json", encoding="utf-8"))
    nutzer = {t["cryptocoin_symbol"] for t in d["transaktionen"] if t["type"] in ("buy", "sell")}
except OSError:
    pass
print("Spot G1-M2 Grundrate Altcoins gegen BTC (Voranalyse_Spot §10.7), messdaten.db bis %s" % ENDE.date())
print("Symbole %d · ausgenommen: BTC, Stablecoins %d (%s), Hebeltoken %d · Altcoins %d, davon eingestellt (Reihe endet > 10 T vor Datenende) %d" % (
    len(alle), len(stable), ",".join(sorted(stable)[:12]), len(hebel), len(ALT), sum(1 for s in ALT if letzter[s] < ENDE - pd.Timedelta(days=10))))

starts = pd.date_range("2019-01-01", ENDE, freq="MS")
zeilen = []
for t in starts:
    if t not in K.index or pd.isna(K.at[t, "BTC"]):
        continue
    for h in H:
        te = t + pd.Timedelta(days=h)
        if te > ENDE:
            continue
        b = K.at[te, "BTC"] / K.at[t, "BTC"]
        ps = K.loc[t, ALT]
        da = ps.dropna().index
        if len(da) == 0:
            continue
        fenster = K.loc[t:te, da]
        pe = fenster.ffill().iloc[-1]
        eing = pd.Series({s: (letzter[s] < te) and (letzter[s] < ENDE - pd.Timedelta(days=10)) for s in da})
        r = pe / ps[da]
        liq = V.loc[t - pd.Timedelta(days=30):t, da].mean()
        for s in da:
            zeilen.append((t, h, s, r[s], b, bool(eing[s]), liq[s], s in nutzer))
Z = pd.DataFrame(zeilen, columns=["start", "h", "sym", "r", "btc", "eingestellt", "liq", "nutzer"])
Z["rel"] = Z["r"] / Z["btc"] - 1


def epoche(t):
    for n, a, e in EPOCHEN:
        if pd.Timestamp(a) <= t <= pd.Timestamp(e):
            return n
    return None


Z["ep"] = Z["start"].map(epoche)
Z = Z.dropna(subset=["ep"])


def tabelle(sel, titel):
    print()
    print(titel)
    print("  %-19s %4s | %6s %5s | %8s %9s | %9s | %6s %6s | %5s | %s" % ("Epoche", "h", "Faelle", "Starts", "Median", "vor BTC", "Korb-Med.",
                                                                       "-50%", "-90%", "eing.", "unabh. Starts"))
    for n, _a, _e in EPOCHEN:
        for h in H:
            x = sel[(sel["ep"] == n) & (sel["h"] == h)]
            if x.empty:
                print("  %-19s %4d | keine vollstaendigen Fenster" % (n, h))
                continue
            korb = x.groupby("start").apply(lambda g: g["r"].mean() / g["btc"].iloc[0] - 1, include_groups=False)
            sp = (x["start"].max() - x["start"].min()).days
            print("  %-19s %4d | %6d %5d | %+7.1f %% %8.0f %% | %+8.1f %% | %5.0f %% %5.0f %% | %4.0f %% | %d" % (
                n, h, len(x), x["start"].nunique(), 100 * x["rel"].median(), 100 * (x["rel"] > 0).mean(), 100 * korb.median(),
                100 * (x["r"] <= 0.5).mean(), 100 * (x["r"] <= 0.1).mean(), 100 * x["eingestellt"].mean(), sp // h + 1))


tabelle(Z, "ALLE ALTCOINS (unverzerrt, mit eingestellten) - relativer Ertrag gegen BTC = (P_ende/P_start) / (BTC_ende/BTC_start) - 1")
eth = Z[Z["sym"] == "ETH"]
print()
print("AUSKUNFT ETH gegen BTC (je Start): " + " · ".join(
    "%s %dT Median %+.0f %% (vor BTC %d/%d)" % (n[:2], h, 100 * eth[(eth["ep"] == n) & (eth["h"] == h)]["rel"].median(),
                                               int((eth[(eth["ep"] == n) & (eth["h"] == h)]["rel"] > 0).sum()), len(eth[(eth["ep"] == n) & (eth["h"] == h)]))
    for n, _a, _e in EPOCHEN for h in (365, 730) if len(eth[(eth["ep"] == n) & (eth["h"] == h)])))
med_liq = Z.groupby(["start", "h"])["liq"].transform("median")
tabelle(Z[Z["liq"] > med_liq], "AUSKUNFT - nur die liquidere Haelfte (30-T-Umsatz am Start ueber dem Median)")
tabelle(Z[Z["nutzer"]], "AUSKUNFT - nur Coins, die du bei Bitpanda gehandelt hast (%d)" % Z[Z["nutzer"]]["sym"].nunique())

# Folge nach §10.7
print()
f = []
for n, _a, _e in EPOCHEN:
    for h in (365, 730):
        x = Z[(Z["ep"] == n) & (Z["h"] == h)]
        if x.empty:
            continue
        korb = x.groupby("start").apply(lambda g: g["r"].mean() / g["btc"].iloc[0] - 1, include_groups=False).median()
        f.append(((x["rel"] > 0).mean() < 0.5) and korb < 0)
print("FOLGE (vorab §10.7): Anteil vor BTC < 50 %% UND Korb-Median < 0 auf 365/730 T in allen Epochen: %s -> %s" % (
    "JA" if f and all(f) else "NEIN (%d von %d Zellen)" % (sum(f), len(f)),
    "als GRUNDRATE ist bei Altcoin-Spot nichts zu holen; ein Spot-Weg muesste eine Auswahl nachweisen, die das deutlich schlaegt (sonst D4)"
    if f and all(f) else "die Grundrate schliesst Altcoin-Spot nicht aus"))
