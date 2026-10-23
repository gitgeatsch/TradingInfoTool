"""P75 ATLAS T1 (Messplan_Indikator_Atlas_23_10.md, vorab ec7ce185): Krypto-Atlas - welche Indikatoren liefen den BTC-Wendepunkten VOR
bzw. NACH, auf zwei Ebenen. Beschreibung mit Pruefung gegen den Zufall, kein Signal.

    python Basisinfos/Rechenkern_02_10/p75_atlas_t1_krypto.py

AUSLEGUNG VOR DEM ERSTEN LAUF (im Plan offen):
- Zustaende je Indikator +1 guenstig / -1 unguenstig / 0 neutral, immer der Wert des VORTAGS (Makro bereits um den Verzug verschoben).
- 'Wechsel auf unguenstig' = Tag d mit Zustand -1 und Vortag != -1 (analog +1). Vorlauf: Wechsel in [T-W, T-1]; Nachlauf: in [T+1, T+W].
- Quote = Anteil der Wendepunkte (Hoch und Tief zusammen) mit passendem Wechsel; Nullwelt: gleich viele Zufallsdaten der Haelfte mit
  gleicher Hoch/Tief-Aufteilung, nur Tage mit gueltigem Indikator; 1.000 Ziehungen; Rang = Anteil Ziehungen mit KLEINERER Quote.
- Stablecoins: DefiLlama (season_ampel.stablecoins), vor 2020-10 unvollstaendig (Omni fehlt) - als Vorbehalt ausgewiesen.
- Dominanz: BTC-Marktwert / Summe der Wochen-Rangliste (cmc_woche, bis 200 Werte), 4-Wochen-Veraenderung.
"""
import json
import os
import sqlite3
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
WURZEL = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, WURZEL)
os.chdir(WURZEL)
import p71_marktfilter as Q  # noqa: E402  (permutiere)
import p72_historie_voranalyse as V  # noqa: E402  (btc, zickzack, uebergeordnet)
from agent import makro_lage as M  # noqa: E402

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:  # noqa: BLE001
    pass
CACHE = os.path.join("data", "_ra", "p75_zustaende.csv")
IDX = pd.date_range("2013-01-01", "2026-10-04", freq="D")
HAELFTEN = (("2013-2019", "2013-01-01", "2019-12-31"), ("2020-2026", "2020-01-01", "2026-10-04"))
ZIEH = 1000


def zustaende():
    if os.path.exists(CACHE):
        return pd.read_csv(CACHE, index_col=0, parse_dates=True)
    import requests
    from dotenv import dotenv_values
    from agent import season_ampel as SA
    key = dotenv_values(".env").get("FRED_API_KEY")
    roh = M.hole_alle(key, heute=pd.Timestamp("2026-10-23").date())
    S = M.scores(roh, IDX)
    Z = pd.DataFrame(index=IDX)
    for k in [k for k in S if k.endswith(" kurz")] + ["Gesamt lang"]:
        Z["Makro " + k] = S[k]
    nq = pd.read_csv(os.path.join("data", "_ra", "p73_fred.csv"), parse_dates=["datum"])
    nq = nq[nq.reihe == "NASDAQCOM"].set_index("datum").wert
    nq.index = nq.index + pd.Timedelta(days=1)
    a = (nq > nq.rolling(200).mean()).where(nq.rolling(200).count() == 200)
    Z["Nasdaq ueber 200 T"] = a.reindex(IDX, method="ffill").map({True: 1.0, False: -1.0})
    st = SA.stablecoins()
    st.index = pd.to_datetime(st.index) + pd.Timedelta(days=1)
    st = st.reindex(IDX, method="ffill")
    Z["Stablecoins 91 T"] = np.sign(st / st.shift(91) - 1).replace(0, np.nan)
    c = sqlite3.connect("file:data/funding_historie.db?mode=ro", uri=True)
    f = pd.read_sql("SELECT datum, wert FROM funding WHERE symbol='BTC'", c, parse_dates=["datum"]).set_index("datum").wert
    c.close()
    f30, med = f.rolling(30).mean(), f.rolling(365, min_periods=180).median()
    Z["Funding BTC 30 T"] = pd.Series(np.where(f30 > med, -1.0, 1.0), index=f.index).where(med.notna()).reindex(IDX)
    r = requests.get("https://api.alternative.me/fng/", params={"limit": 0, "format": "json"}, timeout=60)
    fg = pd.Series({pd.Timestamp(int(x["timestamp"]), unit="s").normalize(): int(x["value"]) for x in r.json()["data"]}).sort_index()
    Z["Fear & Greed"] = pd.Series(np.where(fg < 25, 1.0, np.where(fg > 75, -1.0, 0.0)), index=fg.index).reindex(IDX)
    c = sqlite3.connect("file:data/_spot/o47_cm.db?mode=ro", uri=True)
    w = pd.read_sql("SELECT stichtag, symbol, cap FROM cmc_woche", c, parse_dates=["stichtag"])
    c.close()
    dom = w[w.symbol == "BTC"].set_index("stichtag").cap / w.groupby("stichtag").cap.sum()
    dom.index = dom.index + pd.Timedelta(days=1)
    dd = np.sign(dom / dom.shift(4) - 1)
    Z["BTC-Dominanz 4 W"] = (-dd).reindex(IDX, method="ffill")            # steigende Dominanz = unguenstig
    Z = Z.shift(1)
    os.makedirs(os.path.dirname(CACHE), exist_ok=True)
    Z.to_csv(CACHE)
    return Z


def wechsel(s, ziel):
    v = s.to_numpy()
    w = np.zeros(len(v), bool)
    w[1:] = (v[1:] == ziel) & (v[:-1] != ziel)
    return w


def quote(s, tage, art, W, nach=False):
    """Anteil der Wendepunkte mit passendem Wechsel im Fenster. tage: Positionen im Index, art: 'Hoch'/'Tief'."""
    wn, wp = wechsel(s, -1.0), wechsel(s, 1.0)
    cn, cp = np.concatenate([[0], np.cumsum(wn)]), np.concatenate([[0], np.cumsum(wp)])
    treffer = 0
    for t, a in zip(tage, art):
        lo, hi = (t + 1, t + W + 1) if nach else (t - W, t)
        lo, hi = max(lo, 0), min(hi, len(s))
        c = cn if a == "Hoch" else cp
        treffer += int(c[hi] - c[lo] > 0)
    return treffer / max(len(tage), 1)


def bewerte(s, wende, W, rng, nach=False):
    """-> je Haelfte (quote, null_mittel, rang, n) ; nur Wendepunkte/Zufallstage mit gueltigem Indikator."""
    gueltig = s.notna().to_numpy()
    out = {}
    for name, a, b in HAELFTEN:
        lo, hi = IDX.get_loc(pd.Timestamp(a)), IDX.get_loc(pd.Timestamp(b))
        wt = [(IDX.get_loc(t), k) for t, k in wende if a <= str(t.date()) <= b and gueltig[IDX.get_loc(t)]]
        if len(wt) < 5:
            out[name] = None
            continue
        tage, art = [x for x, _ in wt], [k for _, k in wt]
        q = quote(s, tage, art, W, nach)
        kand = np.flatnonzero(gueltig[lo:hi + 1]) + lo
        null = np.empty(ZIEH)
        for i in range(ZIEH):
            null[i] = quote(s, rng.choice(kand, len(tage)), art, W, nach)
        out[name] = (q, null.mean(), float(np.mean(null < q)), len(tage))
    return out


def kandidat(res):
    return all(r is not None and r[2] >= 0.95 and r[0] > r[1] for r in res.values())


def main():
    rng = np.random.default_rng(75)
    p = V.btc()["2013-01-01":"2026-10-04"]
    wende = V.zickzack(p, 0.20, 0.25)
    baer = V.uebergeordnet(p)
    print("P75 ATLAS T1 · BTC-Wendepunkte klein %d (2013-2026) · uebergeordnete Baerenphasen %d\n" % (len(wende), len(baer)))
    Z = zustaende()
    # Selbsttest
    basis = Z["Nasdaq ueber 200 T"].copy()
    ok_b = basis.notna()
    fehl = 0
    for i in range(200):
        s = basis.copy()
        v = s[ok_b].to_numpy()
        s[ok_b] = Q.permutiere(v, rng)
        fehl += int(kandidat(bewerte(s, wende, 30, rng)))
    bau = pd.Series(0.0, index=IDX)
    for t, k in wende:
        i = IDX.get_loc(t)
        bau.iloc[max(i - 10, 0):min(i + 10, len(IDX))] = -1.0 if k == "Hoch" else 1.0
    pos = kandidat(bewerte(bau, wende, 30, rng))
    ok = fehl / 200 <= 0.05 and pos
    print("SELBSTTEST: Zufallsindikatoren als Kandidat %d von 200 (%.1f %%, Soll <= 5 %%) · gebauter Vorlauf-Indikator erkannt: %s -> %s\n"
          % (fehl, 100 * fehl / 200, "ja" if pos else "nein", "BESTANDEN" if ok else "NICHT BESTANDEN"))
    if not ok:
        print("Selbsttest nicht bestanden - es wird NICHT gemessen.")
        return
    print("KLEINE EBENE (Zickzack -20 %/+25 %, W = 30 T): Vorlauf-Quote / Zufall / Rang je Haelfte · Nachlauf")
    kand = []
    for c in Z.columns:
        s = Z[c]
        rv = bewerte(s, wende, 30, rng)
        rn = bewerte(s, wende, 30, rng, nach=True)
        k = kandidat(rv)
        if k:
            kand.append(c)
        fmt = lambda r: "-" if r is None else "%.0f%%/%.0f%%/%.2f (n%d)" % (100 * r[0], 100 * r[1], r[2], r[3])  # noqa: E731
        print("  %-30s VOR  %s | %s   NACH  %s | %s%s" % (c, fmt(rv["2013-2019"]), fmt(rv["2020-2026"]), fmt(rn["2013-2019"]), fmt(rn["2020-2026"]),
                                                         "   <- KANDIDAT" if k else ""))
    print("\nKandidaten (Vorlauf in beiden Haelften, Rang >= 0,95): %s" % (", ".join(kand) if kand else "KEINE"))
    print("\nUEBERGEORDNETE EBENE (W = 90 T, beschreibend): passender Wechsel in den 90 T VOR der Wende (x) je Indikator")
    punkte = [(h, "Hoch") for h, *_ in baer] + [(t, "Tief") for _, t, _, offen in baer]
    punkte.sort()
    kopf = [c for c in Z.columns]
    for t, k in punkte:
        i = IDX.get_loc(t)
        zeile = []
        for c in kopf:
            s = Z[c]
            if pd.isna(s.iloc[max(i - 90, 0)]) and pd.isna(s.iloc[i]):
                zeile.append(".")
                continue
            w = wechsel(s, -1.0 if k == "Hoch" else 1.0)[max(i - 90, 0):i]
            zeile.append("x" if w.any() else "-")
        print("  %s %-4s %s" % (t.date(), k, " ".join(zeile)))
    print("  Spalten: " + " | ".join("%d=%s" % (j + 1, c) for j, c in enumerate(kopf)))


if __name__ == "__main__":
    main()
