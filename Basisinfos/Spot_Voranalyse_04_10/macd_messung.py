"""Monatlicher MACD der Altcoins (Voranalyse_Spot_Neubau_04_10.md §20, vorab Commit e4ee60b) - nur Auskunft.

    python Basisinfos/Spot_Voranalyse_04_10/macd_messung.py

Liest data/_spot/altcap.db (lade_altcap.py) und fuer die Breite s1_messung (messdaten.db, mode=ro). Schreibt nichts.

AUSLEGUNG, vor dem ersten Lauf festgelegt:
  - Index als KETTENINDEX: Tagesaenderung = Summe der Marktwerte der Assets, die an BEIDEN Tagen einen Wert haben (sonst springt der Index,
    wenn ein grosses Asset neu dazukommt); Start 2014-01-01. Monatsschluss = letzter Tag des Monats
  - ausgeschlossen: btc, Stablecoins, Gold, Wrapped/Bridge, Zweitnetz-Doppel (Liste STATT unten)
  - Altseason nach dem Signal (vorab §20): hoechster Tageswert von I2 in den 365 T nach dem Monatsschluss >= 1,5 x Wert am Monatsschluss;
    Breite (Top 50 gegen BTC ueber 90 T >= 75 %) als zweite Angabe ab 2018
"""
import os
import sqlite3
import sys

import numpy as np
import pandas as pd

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HIER)
os.chdir(os.path.dirname(os.path.dirname(HIER)))

STATT = {"btc", "busd", "dai", "gusd", "husd", "pax", "paxg", "sai", "tusd", "tusd_eth", "tusd_trx", "usdc", "usdc_avaxc", "usdc_eth", "usdc_trx", "usdk",
         "usdt", "usdt_avaxc", "usdt_eth", "usdt_omni", "usdt_trx", "usdd_eth", "usde_eth", "usdm_eth", "susde_eth", "sdai_eth", "lusd_eth", "frax_eth",
         "fdusd_eth", "eurc_eth", "pyusd_eth", "crvusd_eth", "buidl_eth", "xaut", "wbtc", "hbtc", "renbtc", "weth", "wnxm", "bnb_eth", "flow_native",
         "leo_eth"}


def lade():
    c = sqlite3.connect("file:data/_spot/altcap.db?mode=ro", uri=True)
    d = pd.read_sql("SELECT asset, tag, cap FROM cap", c, parse_dates=["tag"])
    return d.pivot(index="tag", columns="asset", values="cap").sort_index().asfreq("D")


def kette(P):
    P = P[P.index >= "2014-01-01"]
    v, h = P.values, P.shift(1).values
    beide = ~np.isnan(v) & ~np.isnan(h) & (h > 0)
    r = np.where(beide, v, 0).sum(axis=1) / np.where(beide, h, 0).sum(axis=1)
    r[0] = 1.0
    r = np.where(np.isfinite(r), r, 1.0)
    return pd.Series(np.cumprod(r), index=P.index)


def macd(m):
    e12, e26 = m.ewm(span=12, adjust=False).mean(), m.ewm(span=26, adjust=False).mean()
    l = e12 - e26
    s = l.ewm(span=9, adjust=False).mean()
    return l, s


def main():
    C = lade()
    alt = [a for a in C.columns if a not in STATT]
    btc = C["btc"][C.index >= "2014-01-01"]
    I1 = kette(C[alt])
    I3 = kette(C[[a for a in alt if a != "eth"]])
    I2, I4 = I1 / btc * btc.iloc[0], I3 / btc * btc.iloc[0]
    try:
        import s1_messung as S1
        breite = S1.baue()["breite"]
    except Exception as e:                                                  # noqa: BLE001
        print("Breite nicht verfuegbar: %s" % e); breite = pd.Series(dtype=float)
    ende = C.dropna(how="all").index.max()
    print("Monatlicher MACD(12,26,9) der Altcoins (§20) · CoinMetrics bis %s · %d Altcoin-Assets im Index (ohne BTC, Stablecoins, Wrapped) · NUR AUSKUNFT\n" % (ende.date(), len(alt)))
    print("Anzahl Assets im Index (mit Wert): " + " · ".join("%d: %d" % (j, C[alt].loc["%d-06-30" % j].notna().sum()) for j in range(2014, 2027)))
    reihen = {"I1 Alt-Marktwert USD (mit ETH)": I1, "I2 Alt / BTC (mit ETH)": I2, "I3 ohne ETH, USD": I3, "I4 ohne ETH / BTC": I4}
    tage_i2 = {"I1": I2, "I2": I2, "I3": I4, "I4": I4}
    for name, x in reihen.items():
        mo = x.resample("ME").last()
        mo = mo[mo.index <= ende]
        if mo.index[-1].month == ende.month and ende.day < mo.index[-1].day:
            mo = mo.iloc[:-1]                                              # laufender Monat ist nicht abgeschlossen
        l, s = macd(mo)
        gueltig = mo.index[35:]
        bez = tage_i2[name[:2]]
        print("\n%s  (ausgewertet ab %s; Altseason-Pruefung auf %s)" % (name, gueltig[0].date(), "I2" if bez is I2 else "I4"))
        zeilen = []
        for art in ("S", "N"):
            for k in range(1, len(mo)):
                t = mo.index[k]
                if t not in gueltig:
                    continue
                hit = (l.iloc[k] > s.iloc[k] and l.iloc[k - 1] <= s.iloc[k - 1]) if art == "S" else (l.iloc[k] > 0 and l.iloc[k - 1] <= 0)
                if hit:
                    zeilen.append((art, t))
        def folge(t):
            def ch(r, m):
                z = r.resample("ME").last()
                i = z.index.get_loc(t)
                return z.iloc[i + m] / z.iloc[i] - 1 if i + m < len(z) and z.index[i + m] <= ende else np.nan
            fen = bez[(bez.index > t) & (bez.index <= t + pd.Timedelta(days=365))]
            mx = fen.max() / bez[:t].iloc[-1] - 1 if len(fen) else np.nan
            br = breite[(breite.index > t) & (breite.index <= t + pd.Timedelta(days=365))]
            return ch(x, 3), ch(x, 6), ch(x, 12), ch(bez, 12), mx, (br.max() if len(br) else np.nan), (t + pd.Timedelta(days=365) <= ende)
        for art in ("S", "N"):
            ev = [t for a, t in zeilen if a == art]
            print("  %s %s: %d Signale" % (art, "MACD kreuzt Signallinie nach oben" if art == "S" else "MACD kreuzt Nulllinie nach oben", len(ev)))
            for t in ev:
                f3, f6, f12, b12, mx, br, voll = folge(t)
                alts = (mx >= 0.5) if not np.isnan(mx) and voll else None
                print("     %s | %s 3/6/12 M %+5.0f / %+5.0f / %+5.0f %% | Alt/BTC 12 M %+5.0f %% · Hoechststand %+5.0f %% | Breite max %s | Altseason %s" % (
                    t.strftime("%Y-%m"), name[:2], 100 * f3, 100 * f6, 100 * f12, 100 * b12, 100 * mx, ("%3.0f %%" % (100 * br)) if not np.isnan(br) else "  - ",
                    "JA" if alts else ("nein" if alts is not None else "offen")))
        alle = [t for t in gueltig if t + pd.Timedelta(days=365) <= ende]
        mx_all = [folge(t)[4] for t in alle]
        print("  Grundrate alle %d Monate: Altseason danach in %.0f %% (Hoechststand Alt/BTC >= +50 %% in 12 M)" % (len(alle), 100 * np.mean([m >= 0.5 for m in mx_all])))
        print("  HEUTE (Monatsschluss %s): MACD %+.4g · Signal %+.4g · Histogramm %+.4g · MACD %s Null · letztes S-Signal %s · letztes N-Signal %s" % (
            mo.index[-1].date(), l.iloc[-1], s.iloc[-1], l.iloc[-1] - s.iloc[-1], "ueber" if l.iloc[-1] > 0 else "unter",
            max([t for a, t in zeilen if a == "S"], default=pd.NaT).strftime("%Y-%m") if any(a == "S" for a, _ in zeilen) else "-",
            max([t for a, t in zeilen if a == "N"], default=pd.NaT).strftime("%Y-%m") if any(a == "N" for a, _ in zeilen) else "-"))


if __name__ == "__main__":
    main()
