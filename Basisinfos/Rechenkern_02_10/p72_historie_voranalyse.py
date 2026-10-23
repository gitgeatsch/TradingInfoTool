"""P72 VORANALYSE H-A (23.10.2026, Voranalyse_REGEL0_Historie_23_10.md): Reicht eine laengere REGEL0-Historie, um einen Marktfilter zu
entscheiden? Und wie viele Marktphasen gibt es auf zwei Ebenen? KEINE Messung eines Filters, KEIN Blick auf Filter gegen Ertrag.

    python Basisinfos/Rechenkern_02_10/p72_historie_voranalyse.py

A  Zustandsstrecken der sechs F-1-Filter: 2024-26 gegen 2020-26 (nur die Filterreihen, ohne Ertrag)
B  Aufloesung: kuenstliche Tagesertraege (Ziehen aus dem echten Tagesnetto 2024-26, zentriert) plus gepflanzter Unterschied D zwischen
   an- und aus-Tagen mit der ECHTEN Streckenstruktur von F6 (BTC ueber 200 T); Fundquote (Rang >= 0,99, Strecken-Permutation) je Fenster
C  Marktphasen BTC 2013-2026 auf zwei Ebenen: uebergeordnet = Rueckgang >= 50 % vom Allzeithoch bis zum Zyklustief (und die Auf-Phase
   dazwischen); kleiner = Zickzack -20 % / +25 %
"""
import os
import sqlite3
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
WURZEL = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, WURZEL)
os.chdir(WURZEL)
import p71_marktfilter as Q  # noqa: E402
from agent import makro_lage as M  # noqa: E402

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:  # noqa: BLE001
    pass


def btc():
    c = sqlite3.connect("file:data/_spot/coinmetrics.db?mode=ro", uri=True)
    p = pd.read_sql("SELECT tag, PriceUSD FROM tag WHERE asset='btc' AND PriceUSD IS NOT NULL", c, parse_dates=["tag"]).set_index("tag").PriceUSD
    c.close()
    return p


def filter_lang():
    import requests
    from dotenv import dotenv_values
    key = dotenv_values(".env").get("FRED_API_KEY")
    roh = M.hole_alle(key, heute=pd.Timestamp("2026-10-23").date())
    idx = pd.date_range("2013-01-01", "2026-10-23", freq="D")
    S = M.scores(roh, idx)
    r = requests.get("https://api.stlouisfed.org/fred/series/observations", timeout=60,
                     params={"series_id": "NASDAQCOM", "api_key": key, "file_type": "json", "observation_start": "2018-01-01"})
    obs = [(o["date"], float(o["value"])) for o in r.json()["observations"] if o["value"] not in (".", "")]
    nq = pd.Series([v for _, v in obs], index=pd.to_datetime([d for d, _ in obs]) + pd.Timedelta(days=1))
    nq_an = (nq > nq.rolling(200).mean()).where(nq.rolling(200).count() == 200)
    b = btc()
    b_an = (b > b.rolling(200).mean()).where(b.rolling(200).count() == 200)
    F = pd.DataFrame(index=idx)
    F["F1 Makro Gesamt kurz"] = (S["Gesamt kurz"] != -1).where(S["Gesamt kurz"].notna())
    F["F2 Makro Gesamt lang"] = (S["Gesamt lang"] != -1).where(S["Gesamt lang"].notna())
    F["F3 Netto-Liquiditaet kurz"] = (S["K2 Netto-Liquiditaet kurz"] != -1).where(S["K2 Netto-Liquiditaet kurz"].notna())
    F["F4 Dollar kurz"] = (S["K8 Dollar kurz"] != -1).where(S["K8 Dollar kurz"].notna())
    F["F5 Nasdaq ueber 200 T"] = (nq_an.reindex(idx).ffill() == 1.0).where(nq_an.reindex(idx).ffill().notna())
    F["F6 BTC ueber 200 T"] = (b_an.reindex(idx).ffill() == 1.0).where(b_an.reindex(idx).ffill().notna())
    return F.shift(1)


def strecken_zahl(z):
    z = z.dropna().astype(int).to_numpy()
    return 1 + int(np.abs(np.diff(z)).sum()) if len(z) else 0


def aufloesung(z, tagesnetto, tageszahl, deltas, rng, laeufe=200, k=200):
    """z: 0/1 je Tag (Fenster). Kuenstlich: Tagesmittel aus dem echten Tagesnetto gezogen (zentriert) + D/2 an, -D/2 aus."""
    mitte = tagesnetto - tagesnetto.mean()
    aus = {}
    for d in deltas:
        fund = 0
        for _ in range(laeufe):
            idx = rng.integers(0, len(mitte), len(z))
            m = mitte[idx] + np.where(z == 1, d / 2, -d / 2)
            n = tageszahl[idx]
            s = m * n
            an = s[z == 1].sum() / max(n[z == 1].sum(), 1)
            alle = s.sum() / max(n.sum(), 1)
            echt = an - alle
            null = np.empty(k)
            for i in range(k):
                zp = Q.permutiere(z.copy(), rng)
                null[i] = s[zp == 1].sum() / max(n[zp == 1].sum(), 1) - alle
            fund += int(np.mean(null < echt) >= 0.99)
        aus[d] = fund / laeufe
    return aus


def zickzack(p, ab, auf):
    rich, et, ep, wende = "auf", p.index[0], p.iloc[0], []
    for t, v in p.items():
        if rich == "auf":
            if v > ep:
                et, ep = t, v
            elif v <= ep * (1 - ab):
                wende.append((et, "Hoch"))
                rich, et, ep = "ab", t, v
        else:
            if v < ep:
                et, ep = t, v
            elif v >= ep * (1 + auf):
                wende.append((et, "Tief"))
                rich, et, ep = "auf", t, v
    return wende


def uebergeordnet(p):
    """Baerenphasen: vom Allzeithoch, das mindestens -50 % folgen laesst, bis zum Tief vor dem naechsten Allzeithoch."""
    ath, ath_t, phasen, i = p.iloc[0], p.index[0], [], 0
    werte, tage = p.to_numpy(), p.index
    while i < len(werte):
        if werte[i] >= ath:
            ath, ath_t = werte[i], tage[i]
            i += 1
            continue
        j = i
        while j < len(werte) and werte[j] < ath:
            j += 1
        seg = werte[i:j]
        k = int(np.argmin(seg))
        if seg[k] <= ath * 0.5:
            phasen.append((ath_t, tage[i + k], seg[k] / ath - 1, j >= len(werte)))
        i = j
    return phasen


def main():
    rng = np.random.default_rng(72)
    print("P72 VORANALYSE H-A · REGEL0-Historie verlaengern?\n")
    F = filter_lang()
    print("A  Zustandsstrecken je Filter (nur Filterreihen):")
    for c in F.columns:
        a = strecken_zahl(F[c]["2024-01-01":"2026-08-31"])
        b = strecken_zahl(F[c]["2020-06-01":"2026-08-31"])
        print("   %-26s 2024-26: %3d Strecken · 2020-06..2026-08: %3d Strecken · erste Zustand %s" % (c, a, b, F[c].first_valid_index().date()))
    R = Q.tagesreihe("unverzerrt_1")
    s, n = R
    tag = np.where(n > 0, s / np.maximum(n, 1), 0.0)
    z_k = F["F6 BTC ueber 200 T"]["2024-01-01":"2026-08-31"].fillna(1).astype(int).to_numpy()
    z_l = F["F6 BTC ueber 200 T"]["2020-06-01":"2026-08-31"].fillna(1).astype(int).to_numpy()
    print("\nB  Aufloesung (Struktur F6, Tagesnetto aus 2024-26 gezogen, Fundquote Rang >= 0,99; Unterschied an minus aus in Pp):")
    for name, z in (("2024-26 (heute)", z_k), ("2020-06..2026-08 (verlaengert)", z_l)):
        a = aufloesung(z, tag, n, (0.005, 0.01, 0.015), rng)
        print("   %-30s Tage %4d · Strecken %3d · Fundquote D 0,5 / 1,0 / 1,5 Pp: %.0f %% / %.0f %% / %.0f %%"
              % (name, len(z), 1 + int(np.abs(np.diff(z)).sum()), 100 * a[0.005], 100 * a[0.01], 100 * a[0.015]))
    p = btc()["2013-01-01":]
    print("\nC  Marktphasen BTC 2013-2026 (Tagesschluss, CoinMetrics):")
    print("   uebergeordnet (Baerenphasen >= -50 % vom Allzeithoch):")
    for h, t, r, offen in uebergeordnet(p):
        print("     %s -> %s  %.0f %%%s" % (h.date(), t.date(), 100 * r, "  (laufend/kein neues Hoch)" if offen else ""))
    w = zickzack(p, 0.20, 0.25)
    j = pd.Series([t.year for t, _ in w]).value_counts().sort_index()
    print("   kleiner (Zickzack -20 %% / +25 %%): %d Wendepunkte 2013-2026; je Jahr: %s" % (len(w), " · ".join("%d %d" % (k, v) for k, v in j.items())))
    print("   davon 2020-06..2026-08: %d · 2024-01..2026-08: %d" % (sum(1 for t, _ in w if pd.Timestamp("2020-06-01") <= t <= pd.Timestamp("2026-08-31")),
                                                                  sum(1 for t, _ in w if pd.Timestamp("2024-01-01") <= t <= pd.Timestamp("2026-08-31"))))


if __name__ == "__main__":
    main()
