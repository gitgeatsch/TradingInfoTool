"""Spot S3-S6 Stufe 1 - Grundrate gegen BTC je Asset-Klasse (Voranalyse_Spot_Neubau_04_10.md §14.3, vorab Commit 7a68051).

    python Basisinfos/Spot_Voranalyse_04_10/s3_stufe1.py

Nur lesend: data/messdaten.db (Krypto USD, mit eingestellten). Kein Netz.

AUSLEGUNG, vor dem ersten Lauf festgelegt (im Plan nicht genau bestimmt):
  - Rang am Monatsersten m nach mittlerem USD-Umsatz der 90 Tage [m-90, m-1], nur Coins mit Kurs am Tag m
  - gerankt wird ein Coin erst ab 30 Tagen Umsatz im Fenster (min_periods=30, stand vor dem ersten Lauf im Code; in der Gegenprobe
    gefunden und hier nachgetragen): ein 90-T-Mittel aus wenigen Listing-Tagen ist kein Groessenmass
  - Klasse H: Rang <= 30 an m, m-1 Monat und m-2 Monate UND erster Kurs >= 730 Tage vor m
  - Coins mit Rang <= 30, die NICHT H sind (jung oder nicht stabil): zaehlen zu M ("gross, aber nicht stabil"); ihre Zahl wird ausgewiesen
  - M: Rang 31-100 (oder Rang <= 30 ohne H); S: Rang >= 101
  - Starts: Monatserste; E2 = 2021-01-01 .. 2024-01-01, E3 = ab 2024-02-01 (erster Monatserste nach dem ETF-Start 11.01.2024)
  - eingestellt: letzter Kurs vor t+h und mehr als 10 T vor Datenende; Ausstieg zum letzten Kurs
"""
import os
import sqlite3

import numpy as np
import pandas as pd

os.chdir(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
H = (90, 180, 365)
SONDER = {"AEUR", "AUD", "EUR", "EURI", "GBP", "PAXG", "WBTC", "WBETH", "BNSOL", "BFUSD", "BUSD", "FDUSD", "PAX", "TUSD", "USD1", "USDC",
          "USDP", "USDSOLD", "XUSD", "BTC", "ETH", "SOL"}


def lade():
    c = sqlite3.connect("file:data/messdaten.db?mode=ro", uri=True)
    k = pd.read_sql("SELECT symbol, date, close, volume FROM price_history_ohlc WHERE assetklasse='krypto' AND currency='USD'", c, parse_dates=["date"])
    c.close()
    K = k.pivot(index="date", columns="symbol", values="close").sort_index().asfreq("D")
    U = k.assign(u=k.close * k.volume).pivot(index="date", columns="symbol", values="u").sort_index().asfreq("D")
    return K, U


K, U = lade()
ENDE = K.index.max()
ret = K.pct_change(fill_method=None)
stabil = {s for s in K.columns if ret[s].abs().median() < 0.002}
UNIV = [s for s in K.columns if s not in stabil and s not in SONDER]
ERST = K[UNIV].apply(lambda x: x.first_valid_index())
LETZT = K[UNIV].apply(lambda x: x.last_valid_index())
U90 = U[UNIV].rolling(90, min_periods=30).mean().shift(1)          # Umsatz der 90 Tage VOR dem Tag
SD90 = ret[UNIV].rolling(90, min_periods=60).std().shift(1)


def rang(m):
    da = [s for s in UNIV if pd.notna(K.at[m, s])]
    return U90.loc[m, da].dropna().rank(ascending=False)


_RANG = {}


def rang_c(m):
    if m not in _RANG:
        _RANG[m] = rang(m)
    return _RANG[m]


def klassen(m):
    r = rang_c(m)
    r1, r2 = rang_c(m - pd.DateOffset(months=1)), rang_c(m - pd.DateOffset(months=2))
    out, gross_nicht_h = {}, 0
    for s, x in r.items():
        if x <= 30 and r1.get(s, 999) <= 30 and r2.get(s, 999) <= 30 and (m - ERST[s]).days >= 730:
            out[s] = "H"
        elif x <= 100:
            out[s] = "M"
            gross_nicht_h += x <= 30
        else:
            out[s] = "S"
    return out, gross_nicht_h


def epoche(m):
    if pd.Timestamp("2021-01-01") <= m <= pd.Timestamp("2024-01-01"):
        return "E2"
    if m >= pd.Timestamp("2024-02-01"):
        return "E3"
    return "E1"


zeilen, gnh = [], {}
for m in pd.date_range("2020-01-01", ENDE, freq="MS"):
    if pd.isna(K.at[m, "BTC"]):
        continue
    kl, g = klassen(m)
    gnh[m] = (g, sum(v == "H" for v in kl.values()), sum(v == "M" for v in kl.values()), sum(v == "S" for v in kl.values()))
    sd = SD90.loc[m, list(kl)].dropna()
    terz = sd.rank(pct=True)
    for h in H:
        te = m + pd.Timedelta(days=h)
        if te > ENDE:
            continue
        b = K.at[te, "BTC"] / K.at[m, "BTC"]
        for s, c_ in kl.items():
            pe = K.loc[m:te, s].ffill().iloc[-1]
            eing = LETZT[s] < te and LETZT[s] < ENDE - pd.Timedelta(days=10)
            alter = (m - ERST[s]).days
            zeilen.append((m, h, s, c_, pe / K.at[m, s], b, eing, "ab 2 J" if alter >= 730 else ("1-2 J" if alter >= 365 else "< 1 J"),
                           ("ruhig" if terz[s] <= 1 / 3 else "mittel" if terz[s] <= 2 / 3 else "wild") if s in terz else None))
Z = pd.DataFrame(zeilen, columns=["start", "h", "sym", "klasse", "r", "btc", "eing", "alter", "schw"])
Z["rel"] = Z["r"] / Z["btc"] - 1
Z["ep"] = Z["start"].map(epoche)


def kennzahlen(x):
    korb = x.groupby("start").apply(lambda g: g["r"].mean() / g["btc"].iloc[0] - 1, include_groups=False)
    mkorb = x.groupby("start").apply(lambda g: g["r"].median() / g["btc"].iloc[0] - 1, include_groups=False)
    return dict(n=len(x), st=x["start"].nunique(), med=x["rel"].median(), vor=(x["rel"] > 0).mean(), korb=korb.median(), mkorb=mkorb.median(),
                m90=(x["r"] <= 0.1).mean(), eing=x["eing"].mean())


def tabelle(sel, spalte, werte, titel):
    print("\n" + titel)
    print("  Ep. Klasse        h | Faelle Starts | Median gg. BTC | vor BTC | Korb  | Median-Korb | -90 %% | eingest.")
    for ep in ("E2", "E3"):
        for w in werte:
            for h in H:
                x = sel[(sel["ep"] == ep) & (sel[spalte] == w) & (sel["h"] == h)]
                if len(x) < 20:
                    continue
                k = kennzahlen(x)
                print("  %s  %-12s %4d | %6d %5d | %+8.1f %%     | %4.0f %%  | %+5.0f %% | %+7.0f %%    | %4.0f %% | %4.0f %%" % (
                    ep, w, h, k["n"], k["st"], 100 * k["med"], 100 * k["vor"], 100 * k["korb"], 100 * k["mkorb"], 100 * k["m90"], 100 * k["eing"]))


print("Spot S3-S6 Stufe 1 - Grundrate gegen BTC je Klasse (Voranalyse_Spot §14.3) · messdaten bis %s" % ENDE.date())
print("Universum %d Altcoins (ohne BTC/ETH/SOL, %d Stablecoins, 19 Sonder-Tokens)" % (len(UNIV), len(stabil)))
for j in (2021, 2022, 2023, 2024, 2025, 2026):
    m = pd.Timestamp("%d-07-01" % j)
    if m in gnh:
        g, nh, nm, ns = gnh[m]
        print("  %d-07: H %d · M %d (davon Top 30 ohne H: %d) · S %d" % (j, nh, nm, g, ns))
tabelle(Z, "klasse", ("H", "M", "S"), "GROESSENKLASSEN (relativer Ertrag gegen BTC = (P_ende/P_start)/(BTC_ende/BTC_start) - 1)")

print("\nZULASSUNG fuer Stufe 2 (vorab §14.3): Korb in E3 auf 180 ODER 365 T im Median hoechstens 10 Pp hinter BTC")
zul = []
for c_ in ("H", "M", "S"):
    w = {h: kennzahlen(Z[(Z["ep"] == "E3") & (Z["klasse"] == c_) & (Z["h"] == h)])["korb"] for h in (180, 365)}
    ok = any(v >= -0.10 for v in w.values())
    zul.append((c_, ok))
    print("  %s: Korb E3 180 T %+.0f %% · 365 T %+.0f %% -> %s" % (c_, 100 * w[180], 100 * w[365], "ZULAESSIG" if ok else "nicht zulaessig"))

print("\nAUSKUNFT LINK, ETH, SOL gegen BTC (Median je Start):")
for s in ("LINK", "ETH", "SOL"):
    teile = []
    for ep in ("E2", "E3"):
        for h in (180, 365):
            ms = [m for m in pd.date_range("2021-01-01", ENDE, freq="MS") if epoche(m) == ep and m + pd.Timedelta(days=h) <= ENDE]
            v = [(K.at[m + pd.Timedelta(days=h), s] / K.at[m, s]) / (K.at[m + pd.Timedelta(days=h), "BTC"] / K.at[m, "BTC"]) - 1 for m in ms
                 if pd.notna(K.at[m, s]) and pd.notna(K.at[m + pd.Timedelta(days=h), s])]
            if v:
                teile.append("%s %dT %+.0f %% (vor BTC %d/%d)" % (ep, h, 100 * np.median(v), sum(x > 0 for x in v), len(v)))
    print("  %-4s %s" % (s, " · ".join(teile)))
lk = Z[Z["sym"] == "LINK"].groupby("ep")["klasse"].agg(lambda x: x.value_counts().to_dict())
print("  LINK war in der Klasse:", lk.to_dict())
tabelle(Z, "alter", ("ab 2 J", "1-2 J", "< 1 J"), "AUSKUNFT ALTER")
tabelle(Z[Z["schw"].notna()], "schw", ("ruhig", "mittel", "wild"), "AUSKUNFT SCHWANKUNG (90 T vor dem Start, Drittel)")
print("\nFOLGE (vorab): " + ("Stufe 2 fuer " + ", ".join(c for c, o in zul if o) if any(o for _c, o in zul) else
                            "KEINE Klasse zulaessig -> D4 zur Vorlage (Altcoin-Spot entfaellt bzw. nur Auskunft), mit dem WORAN je Klasse"))
Z.to_pickle(os.path.join(os.environ.get("TEMP", "."), "s3_stufe1_z.pkl"))
