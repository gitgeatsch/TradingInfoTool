"""O47 Schritt 0 (18.10.2026, Spot §59.4, vorab 08f61223): Haelt die Einteilung §36.5 auf einer VOLLSTAENDIGEN Stablecoin-Reihe?

    python Basisinfos/Spot_Voranalyse_04_10/o47_schritt0.py

Nur der Kalibrierungszeitraum (2019-04 bis 2026-06) - der Holdout 2017/18 wird nicht beruehrt.
Drei Fassungen von B3, alles andere (B1, B2, Breite, Wahrheit) aus den EINGEFRORENEN Spalten von data/_spot/am_kalibrierung.csv:
  K    B3 wie kalibriert (DefiLlama-Summe, Stand 08.10.)
  DLf  DefiLlama-Summe frisch (Auskunft: trennt die Revision vom Quelleneffekt)
  V    verkettet: CoinMetrics-Summe (usdt/usdc/pax/tusd/gusd/busd/dai/husd/usdk/sai) bis 2020-12-31, ab 2021-01-01 DefiLlama, am Uebergangstag
       auf die Hoehe der CoinMetrics-Reihe gebracht (die 91-T-Rate bleibt stetig). Verzug 1 T wie in der Kalibrierung.
Regel = agent.season_ampel (stufen, geltend; Schwellen, Stufen, Haltezeit 7 T unveraendert).
Urteil (vorab): HAELT = geltende Stufe V gegen K an >= 95 % der Tage gleich UND die K2-Ordnung (Season-Anteil 0 < 1 < 2 < 3 von 3) bleibt;
sonst VERSCHIEBT SICH. Beides wird berichtet.
"""
import os
import sqlite3
import sys

import numpy as np
import pandas as pd
import requests

WURZEL = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, WURZEL)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.chdir(WURZEL)
import agent.season_ampel as SA  # noqa: E402
import s1_messung as S1  # noqa: E402

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:  # noqa: BLE001
    pass
STABLE_CM = ("usdt", "usdc", "pax", "tusd", "gusd", "busd", "dai", "husd", "usdk", "sai")
UEBERGANG = pd.Timestamp("2021-01-01")


def taeglich(r, idx):
    return r.sort_index().reindex(r.index.union(idx)).ffill().reindex(idx)


def reihen():
    c = sqlite3.connect("file:data/_spot/o47_cm.db?mode=ro", uri=True, timeout=30)
    S = pd.read_sql("SELECT asset, tag, SplyCur FROM tag WHERE SplyCur IS NOT NULL AND asset IN (%s)" % ",".join("?" * len(STABLE_CM)), c,
                    params=STABLE_CM, parse_dates=["tag"])
    c.close()
    cm = S.pivot(index="tag", columns="asset", values="SplyCur").sort_index().asfreq("D").ffill().fillna(0).sum(axis=1)
    cm.index = cm.index + pd.Timedelta(days=1)                       # Verzug 1 T wie DefiLlama in der Kalibrierung
    j = requests.get("https://stablecoins.llama.fi/stablecoincharts/all", timeout=120).json()
    dl = pd.Series({pd.Timestamp(int(x["date"]), unit="s").normalize() + pd.Timedelta(days=1): x["totalCirculatingUSD"].get("peggedUSD", 0)
                    for x in j}).sort_index()
    k = cm.asof(UEBERGANG) / dl.asof(UEBERGANG)
    v = pd.concat([cm[cm.index < UEBERGANG], dl[dl.index >= UEBERGANG] * k]).sort_index()
    return cm, dl, v, k


def fassung(T0, st):
    """B3 auf einem DURCHGEHENDEN Tagesraster ab 2018-12 (KORREKTUR vor der Bewertung: die erste Fassung rechnete die 91-T-Rate nur
    auf dem Zeitraum selbst, die ersten 91 Tage waren leer und galten als 'aus')."""
    T = T0.copy()
    tage = pd.date_range("2018-12-01", T.index[-1])
    s = taeglich(st, tage)
    T["B3"] = (s / s.shift(91) - 1).reindex(T.index)
    return T


def k2(T):
    st = ((T.B1 > SA.SCHWELLE["B1"]).astype(int) + (T.B2 > SA.SCHWELLE["B2"]).astype(int) + (T.B3 > SA.SCHWELLE["B3"]).astype(int))
    basis = T.season.mean()
    r = T.groupby(st).season.agg(["size", "mean"])
    mono = all(r["mean"].iloc[i] <= r["mean"].iloc[i + 1] + 1e-12 for i in range(len(r) - 1))
    return r, basis, mono, st


def muster(T):
    m = list(zip(T.B1 > SA.SCHWELLE["B1"], T.B2 > SA.SCHWELLE["B2"], T.B3 > SA.SCHWELLE["B3"]))
    namen = {(False, False, False): "keine", (True, False, False): "nur BTC", (True, False, True): "BTC + Stablecoins, M2 fehlt",
             (False, True, False): "nur M2", (False, False, True): "nur Stablecoins", (False, True, True): "Geld (M2 UND Stablecoins), BTC schwach",
             (True, True, True): "alle drei", (True, True, False): "BTC + M2, Stablecoins fehlen"}
    return pd.Series([namen[x] for x in m], index=T.index)


def main():
    K = pd.read_csv(os.path.join("data", "_spot", "am_kalibrierung.csv"), sep=";", parse_dates=["date"]).set_index("date")
    K = K[(K.index >= "2019-04-01") & K.wahr_bekannt & K[["B1", "B2", "B3"]].notna().all(axis=1)].copy()
    K["season"] = K.season.astype(bool)
    print("O47 SCHRITT 0 · B3-Quelle · Kalibrierungszeitraum %s..%s, %d Tage (Holdout nicht beruehrt)\n" % (K.index[0].date(), K.index[-1].date(), len(K)))
    st_rr = ((K.B1 > 0.20).astype(int) + (K.B2 > 0.05).astype(int) + (K.B3 > 0.10).astype(int))
    print("R-R11 Stand aus den eingefrorenen Spalten = Spalte 'stand' der Kalibrierung: %d von %d Tagen" % (int((st_rr == K["stand"]).sum()), len(K)))
    cm, dl, v, k = reihen()
    print("Verkettung am %s: CoinMetrics %.2f Mrd / DefiLlama %.2f Mrd -> Faktor %.4f fuer DefiLlama ab dem Uebergang\n" % (
        UEBERGANG.date(), cm.asof(UEBERGANG) / 1e9, dl.asof(UEBERGANG) / 1e9, k))
    F = {"K": K, "DLf": fassung(K, dl), "V": fassung(K, v)}
    S, G = {}, {}
    for n, T in F.items():
        S[n] = SA.stufen(T)
        G[n] = SA.geltend(S[n])
    ep = S1.episoden(K.season)
    print("Season-Episoden (Wahrheit der Kalibrierung): %s\n" % " · ".join("%s..%s" % (a.date(), e.date()) for a, e in ep))

    print("B3 AN (91 T > 10 %) je Jahr:  " + " | ".join("%d: K %.0f %% · DLf %.0f %% · V %.0f %%" % (
        y, 100 * (F["K"].B3[F["K"].index.year == y] > 0.1).mean(), 100 * (F["DLf"].B3[F["DLf"].index.year == y] > 0.1).mean(),
        100 * (F["V"].B3[F["V"].index.year == y] > 0.1).mean()) for y in sorted(set(K.index.year))))
    print()
    for n in ("DLf", "V"):
        roh = float((S[n] == S["K"]).mean())
        gel = float((G[n] == G["K"]).mean())
        wech = int((G[n] != G[n].shift(1)).sum() - 1)
        print("STUFE %s gegen K: roh gleich %.1f %% · geltend gleich %.1f %% (%d von %d Tagen) · Wechsel der geltenden Stufe %d (K: %d)" % (
            n, 100 * roh, 100 * gel, int((G[n] == G["K"]).sum()), len(K), wech, int((G["K"] != G["K"].shift(1)).sum() - 1)))
        d = G["K"][G[n] != G["K"]]
        if len(d):
            x = pd.crosstab(G["K"][G[n] != G["K"]], G[n][G[n] != G["K"]])
            print("   abweichende Tage je Jahr: %s" % " · ".join("%d: %d" % (y, int(c)) for y, c in d.groupby(d.index.year).size().items()))
            print("   K -> %s (Zeilen K, Spalten %s):\n%s" % (n, n, "\n".join("      " + z for z in x.to_string().splitlines())))
    print()
    urteil = {}
    for n, T in F.items():
        r, basis, mono, _st = k2(T)
        print("K2 %-3s (Basis %.1f %%): %s -> Ordnung %s" % (n, 100 * basis, " · ".join(
            "%d von 3: %d T, Season %.1f %% (Lift %.2f)" % (i, int(row["size"]), 100 * row["mean"], row["mean"] / basis) for i, row in r.iterrows()),
            "HAELT" if mono else "BRICHT"))
        urteil[n] = mono
    print()
    for n, T in F.items():
        m = muster(T)
        g = T.groupby(m).season.agg(["size", "mean"]).sort_values("size", ascending=False)
        print("K2b %-3s: %s" % (n, " · ".join("%s %d T (%.1f %%)" % (i, int(row["size"]), 100 * row["mean"]) for i, row in g.iterrows())))
    print("\nK4 (Auskunft) geltende Stufe vor jeder Episode, Fenster [Start - 120 T, Start + 30 T]: Tage Vorlauf / Season-Klima / Ueberhitzung")
    for a, e in ep:
        w = lambda s: s[(s.index >= a - pd.Timedelta(days=120)) & (s.index <= a + pd.Timedelta(days=30))]  # noqa: E731
        print("   %s: %s" % (a.date(), " | ".join("%s %d/%d/%d" % (n, int((w(G[n]) == "Vorlauf").sum()), int((w(G[n]) == "Season-Klima").sum()),
                                                                      int((w(G[n]) == "Ueberhitzung").sum())) for n in F)))
    gel_v = float((G["V"] == G["K"]).mean())
    haelt = gel_v >= 0.95 and urteil["V"]
    print("\nURTEIL Schritt 0 (vorab: geltend gleich >= 95 %% UND K2-Ordnung bleibt): %s (geltend gleich %.1f %%, Ordnung %s)" % (
        "HAELT" if haelt else "VERSCHIEBT SICH", 100 * gel_v, "haelt" if urteil["V"] else "bricht"))
    out = pd.DataFrame({"K": G["K"], "DLf": G["DLf"], "V": G["V"], "B3_K": F["K"].B3, "B3_DLf": F["DLf"].B3, "B3_V": F["V"].B3})
    out.to_csv(os.path.join("data", "_spot", "o47_schritt0.csv"), sep=";")


if __name__ == "__main__":
    main()
