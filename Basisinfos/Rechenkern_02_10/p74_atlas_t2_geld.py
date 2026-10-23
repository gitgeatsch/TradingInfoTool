"""P74 ATLAS T2 (Messplan_Indikator_Atlas_23_10.md, vorab ec7ce185): Ist Geldausweitung eine VORAUSSETZUNG fuer steigendes BTC?

    python Basisinfos/Rechenkern_02_10/p74_atlas_t2_geld.py

Geldmasse (Verzug in Tagen wie makro_lage bzw. Veroeffentlichung): (i) US-M2 J/J > 0 [35], (ii) Netto-Liquiditaet Fed (WALCL - TGA - RRP)
26 Wochen > 0 [2], (iii) Notenbank-Bilanzen Fed + EZB + BoJ in USD J/J > 0 [WALCL 2, ECB 7, BoJ 35; Wechselkurse 1]. Auskunft: reales M2.
BTC-Aufwaertsstrecken: Zickzack -20 % / +25 %, Tief -> Hoch, 2013-2026 (CoinMetrics-Tagesschluss).
(a) Anteil der Aufwaerts-TAGE in Phasen OHNE Ausweitung MINUS Zeitanteil dieser Phasen; Nullwelt: Surrogate der Geldreihe (Phasen-
    Randomisierung der Wachstumsreihe, R-R14), 500 Ziehungen; Rang = Anteil Surrogate mit KLEINEREM Anteil (Voraussetzung => Rang <= 0,05)
(b) BTC-Ertrag 90 T je Zustand · (c) uebergeordnete Bullenphasen: Ausweitung am Beginn? (beschreibend)
"""
import os
import sqlite3
import sys
import time

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
WURZEL = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(WURZEL)
import p72_historie_voranalyse as V  # noqa: E402  (zickzack, btc)

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:  # noqa: BLE001
    pass
ABLAGE = os.path.join("data", "_ra", "p74_fred.csv")
REIHEN = {"M2SL": 35, "WALCL": 2, "WTREGEN": 2, "RRPONTSYD": 1, "ECBASSETSW": 7, "JPNASSETS": 35, "DEXUSEU": 1, "DEXJPUS": 1, "CPIAUCSL": 20}


def lade():
    if not os.path.exists(ABLAGE):
        import requests
        from dotenv import dotenv_values
        key = dotenv_values(".env").get("FRED_API_KEY")
        z = []
        for s in REIHEN:
            r = requests.get("https://api.stlouisfed.org/fred/series/observations", timeout=90,
                             params={"series_id": s, "api_key": key, "file_type": "json", "observation_start": "2008-01-01"})
            z += [(s, o["date"], float(o["value"])) for o in r.json()["observations"] if o["value"] not in (".", "")]
            time.sleep(0.3)
        pd.DataFrame(z, columns=["reihe", "datum", "wert"]).to_csv(ABLAGE, index=False)
    d = pd.read_csv(ABLAGE, parse_dates=["datum"])
    return {s: g.set_index("datum").wert.sort_index() for s, g in d.groupby("reihe")}


def taeglich(r, verzug, idx):
    r = r.copy()
    r.index = r.index + pd.Timedelta(days=verzug)
    return r.reindex(r.index.union(idx)).ffill().reindex(idx)


def geldmasse(R, idx):
    m2 = taeglich(R["M2SL"], 35, idx)
    m2y = m2 / m2.shift(365) - 1
    w = pd.concat([R["WALCL"], R["WTREGEN"], R["RRPONTSYD"].resample("W-WED").last()], axis=1).ffill().dropna()
    w.columns = ["WALCL", "WTREGEN", "RRPONTSYD"]
    netto = taeglich((w.WALCL - w.WTREGEN - w.RRPONTSYD * 1000) / 1e6, 2, idx)
    netto26 = netto / netto.shift(182) - 1
    fed = taeglich(R["WALCL"] / 1e6, 2, idx)                                   # Mio USD -> Bio USD
    ecb = taeglich(R["ECBASSETSW"] / 1e6, 7, idx) * taeglich(R["DEXUSEU"], 1, idx)  # Mio EUR -> Bio EUR -> USD
    boj = taeglich(R["JPNASSETS"] / 1e4, 35, idx) / taeglich(R["DEXJPUS"], 1, idx)  # 100 Mio JPY -> Bio JPY -> USD
    zb = fed + ecb + boj
    zby = zb / zb.shift(365) - 1
    cpi = taeglich(R["CPIAUCSL"], 20, idx)
    real = (m2 / cpi)
    realy = real / real.shift(365) - 1
    return {"(i) US-M2 J/J": m2y, "(ii) Netto-Liquiditaet 26 W": netto26, "(iii) ZB-Bilanzen Fed+EZB+BoJ J/J": zby, "Auskunft reales M2 J/J": realy}


def surrogat(x, rng):
    """Phasen-Randomisierung (Amplitudenspektrum bleibt, Phasen zufaellig) auf der Wochenreihe, dann taeglich."""
    w = x.resample("W").last().dropna()
    v = w.to_numpy() - w.mean()
    f = np.fft.rfft(v)
    ph = rng.uniform(0, 2 * np.pi, len(f))
    ph[0] = 0.0
    s = np.fft.irfft(np.abs(f) * np.exp(1j * ph), n=len(v)) + w.mean()
    return pd.Series(s, index=w.index).reindex(x.index, method="ffill")


def main():
    R = lade()
    p = V.btc()["2013-01-01":"2026-10-04"]
    idx = p.index
    G = geldmasse(R, idx)
    w = V.zickzack(p, 0.20, 0.25)
    auf = np.zeros(len(idx), bool)
    strecken_auf = []
    for (t1, a1), (t2, a2) in zip(w[:-1], w[1:]):
        if a1 == "Tief" and a2 == "Hoch":
            auf[(idx >= t1) & (idx <= t2)] = True
            strecken_auf.append((t1, t2, p[t2] / p[t1] - 1))
    print("P74 ATLAS T2 · BTC 2013-01..2026-10 · Aufwaertsstrecken (-20 %%/+25 %%): %d, Anteil Aufwaerts-Tage %.0f %%\n" % (len(strecken_auf), 100 * auf.mean()))
    rng = np.random.default_rng(74)
    for name, g in G.items():
        ok = g.notna().to_numpy()
        ohne = (g <= 0).to_numpy() & ok
        anteil_zeit = ohne[ok].mean()
        anteil_auf = ohne[auf & ok].sum() / max((auf & ok).sum(), 1)
        null = []
        for _ in range(500):
            sg = surrogat(g[ok], rng)
            oh = (sg <= 0).to_numpy()
            null.append(oh[auf[ok]].mean() - oh.mean())       # KORREKTUR vor der Bewertung: Differenz zum Zeitanteil, wie §T2 (a)
        rang = float(np.mean(np.array(null) < anteil_auf - anteil_zeit))
        r90 = (p.shift(-90) / p - 1)
        e_mit = r90[(g > 0) & r90.notna()].mean()
        e_ohne = r90[(g <= 0) & r90.notna()].mean()
        ganz_ohne = sum(1 for t1, t2, r in strecken_auf if (g[t1:t2] <= 0).all())
        print("%-34s gueltig ab %s · Zeit ohne Ausweitung %.0f %% · Aufwaerts-Tage ohne Ausweitung %.0f %% · Rang %.2f%s"
              % (name, g.first_valid_index().date(), 100 * anteil_zeit, 100 * anteil_auf, rang, "  <- Voraussetzung?" if rang <= 0.05 else ""))
        print("%34s BTC 90 T: mit Ausweitung %+.0f %% · ohne %+.0f %% · Aufwaertsstrecken GANZ ohne Ausweitung: %d von %d"
              % ("", 100 * e_mit, 100 * e_ohne, ganz_ohne, len(strecken_auf)))
    print("\n(c) Uebergeordnete Bullenphasen (Tief des Zyklus-Baeren -> naechstes Hoch) und Geld am Beginn / im Mittel:")
    for t1, t2 in ((pd.Timestamp("2015-01-14"), pd.Timestamp("2017-12-16")), (pd.Timestamp("2018-12-15"), pd.Timestamp("2021-11-08")),
                   (pd.Timestamp("2022-11-09"), pd.Timestamp("2025-10-06"))):
        teile = []
        for name, g in G.items():
            if pd.notna(g.get(t1)):
                teile.append("%s Beginn %+.1f %% / Anteil Tage mit Ausweitung %.0f %%" % (name.split()[0], 100 * g[t1], 100 * (g[t1:t2] > 0).mean()))
        print("   %s -> %s (BTC x%.1f): %s" % (t1.date(), t2.date(), p[t2] / p[t1], " · ".join(teile)))


if __name__ == "__main__":
    main()
