"""Gegenpruefung der Naeherung 'Marktwert(t) = Umlauf HEUTE x Kurs(t)' gegen den echten Marktwert von CoinMetrics (Voranalyse_Spot §25.1).

    python Basisinfos/Spot_Voranalyse_04_10/mw_naeherung_pruefung.py

Nur lesend: data/_spot/strukturprofil.db (Umlauf heute, CoinGecko), data/_spot/altcap.db (CoinMetrics CapMrktCurUSD), messdaten.db (Kurse).
Je Stichtag: Rangkorrelation (Spearman) Naeherung gegen echt, mittlere Abweichung, und wie viele Coins nach der Naeherung in einer ANDEREN
Klasse landen (Rang <= 30 / <= 100 innerhalb der Vergleichsmenge - nur relativ, weil CoinMetrics nicht alle Coins fuehrt).
"""
import os
import sqlite3
import sys

import numpy as np
import pandas as pd

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HIER)
import a2_messung as A  # noqa: E402

K = A.K


def main():
    P = pd.read_sql("SELECT symbol, umlauf FROM profil WHERE umlauf IS NOT NULL", sqlite3.connect("file:data/_spot/strukturprofil.db?mode=ro", uri=True))
    um = dict(zip(P.symbol, P.umlauf))
    C = pd.read_sql("SELECT asset, tag, cap FROM cap", sqlite3.connect("file:data/_spot/altcap.db?mode=ro", uri=True), parse_dates=["tag"])
    C["sym"] = C.asset.str.split("_").str[0].str.upper()
    C = C[~C.asset.str.contains("_")]                                  # nur Hauptnetz, keine Zweitnetz-Kopien
    echt = C.pivot_table(index="tag", columns="sym", values="cap", aggfunc="first")
    gemeinsam = [s for s in echt.columns if s in um and s in K.columns]
    print("Gegenpruefung Naeherung Marktwert · Coins mit CoinMetrics-Marktwert, heutigem Umlauf und Kurs: %d\n" % len(gemeinsam))
    print("  %-10s %4s %9s %22s %26s" % ("Stichtag", "n", "Spearman", "Abweichung Median", "andere Klasse (relativ)"))
    for t in ("2020-01-01", "2021-01-01", "2021-06-01", "2022-06-01", "2023-01-01", "2024-01-01", "2025-01-01", "2026-01-01"):
        t = pd.Timestamp(t)
        z = []
        for s in gemeinsam:
            e = echt[s].get(t, np.nan); k = K[s].get(t, np.nan)
            if e == e and k == k and e > 0:
                z.append((s, e, um[s] * k))
        if len(z) < 10:
            print("  %s  zu wenige (%d)" % (t.date(), len(z))); continue
        d = pd.DataFrame(z, columns=["s", "echt", "nah"])
        rho = d.echt.rank().corr(d.nah.rank())
        abw = np.median(np.abs(d.nah / d.echt - 1))
        n = len(d)
        g1, g2 = max(3, round(n * 30 / 330)), max(6, round(n * 100 / 330))        # Klassenschnitte relativ zur Universumsgroesse
        ke = np.where(d.echt.rank(ascending=False) <= g1, "H", np.where(d.echt.rank(ascending=False) <= g2, "M", "S"))
        kn = np.where(d.nah.rank(ascending=False) <= g1, "H", np.where(d.nah.rank(ascending=False) <= g2, "M", "S"))
        gross = d.assign(f=d.nah / d.echt).sort_values("f")
        print("  %s %4d %9.3f %21.0f %% %18d von %d (%.0f %%) · am staerksten zu gross: %s · zu klein: %s" % (
            t.date(), n, rho, 100 * abw, int((ke != kn).sum()), n, 100 * np.mean(ke != kn),
            ", ".join("%s x%.1f" % (r.s, r.f) for r in gross.tail(3).itertuples()), ", ".join("%s x%.2f" % (r.s, r.f) for r in gross.head(2).itertuples())))


if __name__ == "__main__":
    main()
