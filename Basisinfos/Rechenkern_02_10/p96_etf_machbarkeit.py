"""P96 ETF-FLUESSE STUFE 0 - MACHBARKEIT (Recherche_Ergaenzung_26_10.md §5, vorab c2ac58d5). Kein Ergebnis, nur Pruefstand.

    python -X utf8 Basisinfos/Rechenkern_02_10/p96_etf_machbarkeit.py

Farside-Tabelle (einmal geladen nach data/_etf/farside_btc.html), Spalte Total je US-Handelstag; Tage, an denen alle Fonds '-' fuehren
(Feiertag, noch nicht veroeffentlicht), entfallen. Zustand Z(t) = Summe der Nettofluesse der letzten 3 Handelstage > 0, wirksam ab dem
Schluss t + 1 Tag (UTC). Ziel: BTC-Tagesschluss (CoinMetrics), Ertrag 1 T / 7 T ab Schluss t + 1. Orakel, Fehlalarm (Zufallszustand mit
derselben Streckenstruktur), Aufloesung (Pflanzung) wie p91. Nur lesend.
"""
import io
import os
import sys

import numpy as np
import pandas as pd

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HIER)
import p91_l2a_voranalyse as P91  # noqa: E402  (setzt Pfad und Arbeitsordner)

RNG = np.random.default_rng(96)
STAERKEN = (0.0025, 0.005, 0.01, 0.02)


def fluesse():
    t = max(pd.read_html(io.StringIO(open("data/_etf/farside_btc.html", encoding="utf-8", errors="replace").read())), key=len)
    t = t[pd.to_datetime(t.Date, format="%d %b %Y", errors="coerce").notna()].copy()
    t.index = pd.to_datetime(t.Date, format="%d %b %Y")
    fonds = [c for c in t.columns if c not in ("Date", "Total")]
    leer = t[fonds].astype(str).apply(lambda s: s.str.strip().isin(["-", "nan"])).all(axis=1)
    t = t[~leer]
    v = t.Total.astype(str).str.replace(",", "").str.strip()
    neg = v.str.startswith("(")
    v = pd.to_numeric(v.str.strip("()"), errors="coerce")
    return v.where(~neg, -v).dropna()


def main():
    F = fluesse()
    K = P91.kurse()
    btc = K.btc.dropna()
    print("P96 ETF-FLUESSE STUFE 0 (Machbarkeit) · Farside %s..%s, %d US-Handelstage · BTC CoinMetrics bis %s\n" % (
        F.index[0].date(), F.index[-1].date(), len(F), btc.index[-1].date()))
    for fenster in (3, 1, 5):
        z_us = (F.rolling(fenster).sum() > 0).astype(float).where(F.rolling(fenster).count() == fenster)
        # wirksam ab Schluss t + 1 Tag (UTC): Zustand je Kalendertag = letzter bekannter US-Wert bis zum VORTAG
        tage = btc.index[(btc.index > F.index[0] + pd.Timedelta(days=fenster + 1))]
        z = z_us.reindex(tage - pd.Timedelta(days=1), method="ffill").to_numpy()
        for h in (1, 7):
            y_all = (btc.shift(-h) / btc - 1).reindex(tage).to_numpy()
            ok = np.isfinite(z) & np.isfinite(y_all)
            zz, y = z[ok].astype(int), y_all[ok]
            st = P91.strecken(zz)
            haupt = fenster == 3
            zeile = "%s Fenster %d T · Ertrag %d T: %d Tage · Zufluss %.0f %% · %d Strecken" % (
                "HAUPT  " if haupt else "Auskunft", fenster, h, len(y), 100 * zz.mean(), len(st))
            if not (haupt or h == 1):
                print("  " + zeile)
                continue
            orakel = (pd.Series(y).rolling(7, center=True, min_periods=3).mean() > 0).astype(int).to_numpy()
            r_o = P91.rang(orakel, y, RNG, 500)
            fa = np.mean([P91.rang(P91.permutiere(zz, RNG), y, RNG, 200) >= 0.95 for _ in range(100)])
            fund = {}
            for d in STAERKEN:
                n = 0
                for _ in range(100):
                    zp = P91.permutiere(zz, RNG)
                    n += P91.rang(zp, y + d * zp, RNG, 200) >= 0.95
                fund[d] = n / 100
            x = next((d for d in STAERKEN if fund[d] >= 0.8), None)
            messbar = fa <= 0.05 and x is not None and x <= 0.01
            print("  %s · Orakel Rang %.3f · Fehlalarm %.0f %% · Fund %s · Aufloesung X %s%s" % (
                zeile, r_o, 100 * fa, " ".join("%+.2f Pp %.0f %%" % (100 * d, 100 * f) for d, f in fund.items()),
                "%.2f Pp" % (100 * x) if x else "keine <= 2 Pp", " -> MESSBAR" if (haupt and h == 1 and messbar) else
                (" -> nicht messbar" if (haupt and h == 1) else "")))
    print("\nTagesschwankung BTC 2024-26: %.2f %%" % (100 * np.log(btc["2024":]).diff().std()))


if __name__ == "__main__":
    main()
