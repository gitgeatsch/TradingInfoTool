"""Gegenprobe O47 Schritt 0 (18.10.2026) - ZWEITER Weg, ohne agent.season_ampel und ohne die Reihenfunktion von o47_schritt0.

    python Basisinfos/Spot_Voranalyse_04_10/o47_schritt0_gegenprobe.py

G1 B3 verkettet neu: je Stablecoin per asof auf jeden Tag (statt Pivot + ffill), Summe, Verzug 1 T; DefiLlama ab 2021-01-01 ueber das
   Niveauverhaeltnis am Vortag des Uebergangs angehaengt -> B3 je Tag gegen o47_schritt0.csv
G2 Stufe neu aus dem Wortlaut §36.5 (if-Kette) + Haltezeit als Zaehler-Zustandsmaschine (7 Tage in Folge) fuer K und V -> je Tag gegen
   o47_schritt0.csv
G3 K2 (Season-Anteil je Stand) fuer V neu gezaehlt
G4 Auskunft: seit wann war B3 vor jedem Season-Start durchgehend an (K gegen V)
"""
import os
import sqlite3
import sys

import pandas as pd
import requests

os.chdir(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:  # noqa: BLE001
    pass
ok = []


def pruefe(name, bed, info=""):
    ok.append(bool(bed))
    print("  %s  %s%s" % ("OK  " if bed else "FEHL", name, ("  (%s)" % info) if info else ""))


K = pd.read_csv("data/_spot/am_kalibrierung.csv", sep=";", parse_dates=["date"]).set_index("date")
K = K[(K.index >= "2019-04-01") & K.wahr_bekannt & K[["B1", "B2", "B3"]].notna().all(axis=1)].copy()
K["season"] = K.season.astype(bool)
E = pd.read_csv("data/_spot/o47_schritt0.csv", sep=";", parse_dates=[0], index_col=0)
tage = pd.date_range(K.index[0] - pd.Timedelta(days=100), K.index[-1])

c = sqlite3.connect("file:data/_spot/o47_cm.db?mode=ro", uri=True, timeout=30)
summe = pd.Series(0.0, index=tage)
for a in ("usdt", "usdc", "pax", "tusd", "gusd", "busd", "dai", "husd", "usdk", "sai"):
    r = pd.read_sql("SELECT tag, SplyCur FROM tag WHERE asset=? AND SplyCur IS NOT NULL ORDER BY tag", c, params=(a,), parse_dates=["tag"])
    if len(r):
        s = r.set_index("tag").SplyCur
        summe += pd.Series([s.asof(t - pd.Timedelta(days=1)) for t in tage], index=tage).fillna(0.0)
c.close()
j = requests.get("https://stablecoins.llama.fi/stablecoincharts/all", timeout=120).json()
dl = pd.Series({pd.Timestamp(int(x["date"]), unit="s").normalize(): x["totalCirculatingUSD"].get("peggedUSD", 0) for x in j}).sort_index()
dl_t = pd.Series([dl.asof(t - pd.Timedelta(days=1)) for t in tage], index=tage)
u = pd.Timestamp("2021-01-01")
v = summe.where(tage < u, dl_t * (summe[u] / dl_t[u]))
b3v = (v / v.shift(91) - 1).reindex(K.index)
print("O47 SCHRITT 0 GEGENPROBE (zweiter Weg)\n")
d = (b3v - E.B3_V).abs()
einseitig = int((b3v.isna() != E.B3_V.isna()).sum())
pruefe("G1 B3 verkettet je Tag gleich (Abweichung < 1e-9) und an JEDEM Tag vorhanden", float(d.max()) < 1e-9 and einseitig == 0
       and int(d.notna().sum()) == len(K), "groesste %.2e, verglichen %d von %d Tagen, nur einseitig vorhanden %d" % (
           float(d.max()), int(d.notna().sum()), len(K), einseitig))


def stufe(b1, b2, b3, breite, war3):
    m1, m2, m3 = b1 > 0.20, b2 > 0.05, b3 > 0.10
    if m1 and m2 and m3:
        return "Ueberhitzung" if breite == breite and breite >= 0.6 else "Season-Klima"
    if war3:
        return "Ende"
    if (not m1) and m2 and m3:
        return "Vorlauf"
    if m1 and m2 and not m3:
        return "ungewohnt"
    return "kalt"


def gelten(T, b3):
    roh, letzte3 = [], None
    for i, t in enumerate(T.index):
        war3 = letzte3 is not None and (t - letzte3).days <= 90
        roh.append(stufe(T.B1.iloc[i], T.B2.iloc[i], b3.iloc[i], T.Breite.iloc[i], war3))
        if T.B1.iloc[i] > 0.20 and T.B2.iloc[i] > 0.05 and b3.iloc[i] > 0.10:
            letzte3 = t
    akt, kand, n, aus = roh[0], roh[0], 0, []
    for s in roh:
        if s == kand:
            n += 1
        else:
            kand, n = s, 1
        if kand != akt and n >= 7:
            akt = kand
        aus.append(akt)
    return pd.Series(aus, index=T.index)


gK, gV = gelten(K, K.B3), gelten(K, b3v)
pruefe("G2 geltende Stufe K je Tag gleich", bool((gK == E.K).all()), "%d von %d" % (int((gK == E.K).sum()), len(K)))
pruefe("G2 geltende Stufe V je Tag gleich", bool((gV == E.V).all()), "%d von %d" % (int((gV == E.V).sum()), len(K)))
gl = float((gV == gK).mean())
pruefe("G2 V gegen K gleich: derselbe Anteil wie Schritt 0", abs(gl - float((E.V == E.K).mean())) < 1e-12, "%.2f %%" % (100 * gl))
st = (K.B1 > 0.20).astype(int) + (K.B2 > 0.05).astype(int) + (b3v > 0.10).astype(int)
r = K.groupby(st).season.mean()
pruefe("G3 K2 V: Ordnung 0 < 1 < 2 < 3 (neu gezaehlt)", bool(r.is_monotonic_increasing),
       " · ".join("%d: %.1f %%" % (k, 100 * x) for k, x in r.items()))
print("\nG4 Auskunft: B3 vor dem Season-Start zuletzt eingeschaltet (durchgehend an bis zum Start)")
for start in ("2020-04-10", "2020-11-12"):
    s = pd.Timestamp(start)
    for name, b in (("K", K.B3), ("V", b3v)):
        an = (b > 0.10)[:s]
        aus_tage = an[~an]
        seit = (an.index[0] if not len(aus_tage) else aus_tage.index[-1] + pd.Timedelta(days=1))
        print("   %s %s: an seit %s (%d T vor dem Start)%s" % (start, name, seit.date(), (s - seit).days,
                                                             " - bis zum Zeitraumbeginn" if not len(aus_tage) else ""))
print("\n%d Pruefungen, %s" % (len(ok), "ALLE BESTANDEN" if all(ok) else "%d FEHLGESCHLAGEN" % ok.count(False)))
