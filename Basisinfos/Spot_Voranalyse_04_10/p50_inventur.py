"""P50 INVENTUR der Spot-Auswahlregeln ab 2024 mit EINHEITLICHEM Massstab (Spot §50/§51.8, O48) - nur lesend.

    python Basisinfos/Spot_Voranalyse_04_10/p50_inventur.py

Massstab (§51.8, Nutzer 14.10.): in EURO, log-Ertrag, nach Kosten. Huerden H1 Inflation (HICP Euroraum), H2 ESTR (Geld auf Zinsen),
H3 BTC (nach Kosten). Dazu - fachliche Pruefung des Massstabs - der BELEG gegen eine Zufallsauswahl aus demselben Universum:
eine Huerde schlaegt in einem steigenden Markt auch der Zufall.

Teil A (12 M, Monatsstichtage E3 02/2024-09/2025, data/_spot/b4_vormessung.csv = Wert ohne F9 in Marktwert-Zellen):
  A1 oberes Fuenftel halten 12 M (Variante von Regel 1: Marktwert- statt Umsatz-Klassen, ohne F9)
  A2 dasselbe mit Fuehrung X2 (raus bei -35 % vom Hoch seit Kauf, Rest auf ESTR)
  A9 unteres Fuenftel (Regel 9, B4)   ·   A0 alle Coins der Zelle (Markt der Watchlist-Klassen)
  Nullwelt: bestaendige Zufallszahl je Coin (wie B4), gleicher Anteil je Zelle, 200 Ziehungen.
Teil B (30 T, gespeicherte Einstiege der Tagesregeln, data/_spot/*_einstiege_*.csv; Index i = Tage seit 2017-08-17):
  Regel 3 K-H1 Momentum (k37), Regel 4 K-3 ruhiger Boden (k3), Regel 6 U2 Gebuehren (k47 U2), Regel 7 U1 Stablecoins (k47 U1);
  nur die U-Dateien (Urteilszeitraum ab 2024; W = Wahljahr 2023). Der Beleg gegen Zufall kommt aus den Messungen (§37, §40, §46); hier nur die Bilanz.
Kosten hin und zurueck: H 0,72 % · M 1,76 % · S 6,4 % (§37/§40) · BTC 0,8 %.
"""
import io
import os
import sys

import numpy as np
import pandas as pd
import requests

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HIER)
import s1_messung as S1   # noqa: E402  (chdir Projektwurzel)

RNG = np.random.default_rng(20261055)
KOST = {"H": 0.0072, "M": 0.0176, "S": 0.064}
KOST_BTC = 0.008
BASIS = pd.Timestamp("2017-08-17")
SPOT = os.path.join("data", "_spot")


def fred(s):
    r = requests.get("https://fred.stlouisfed.org/graph/fredgraph.csv?id=" + s, timeout=120)
    d = pd.read_csv(io.StringIO(r.text))
    d.columns = ["d", s]
    return pd.to_numeric(d.set_index(pd.to_datetime(d.d))[s], errors="coerce").dropna()


class Huerden:
    def __init__(self):
        tage = pd.date_range("2017-01-01", "2027-12-31")
        self.eu = np.log(fred("DEXUSEU").reindex(tage).ffill().bfill())
        h = fred("CP0000EZ19M086NEST")
        lh = np.log(h)
        lh.index = lh.index + pd.Timedelta(days=14)                      # Monatswert zur Monatsmitte
        rate = (lh.iloc[-1] - lh.iloc[-13]) / 365.0                      # nach dem letzten Wert: letzte J/J-Rate fortgeschrieben
        s = lh.reindex(lh.index.union(tage)).interpolate("time")
        nach = s.index > lh.index[-1]
        s[nach] = lh.iloc[-1] + rate * (s.index[nach] - lh.index[-1]).days
        self.hicp = s.reindex(tage)
        self.hicp_ende = lh.index[-1]
        e = fred("ECBESTRVOLWGTTRMDMNRT").reindex(tage).ffill().bfill()   # vor 10/2019 rueckwaerts gefuellt (nur Auskunft)
        self.estr = np.log1p(e / 100 / 360).cumsum()

    def fx(self, a, b):           # log(EURUSD_b / EURUSD_a): Dollar-Ertrag minus diesen Wert = Euro-Ertrag
        return self.eu[b].values - self.eu[a].values

    def h1(self, a, b):
        return self.hicp[b].values - self.hicp[a].values

    def h2(self, a, b):
        return self.estr[b].values - self.estr[a].values


def zeile(name, n, r, h1, h2, h3, extra=""):
    return "  %-46s n %5d | Euro nach Kosten %+7.1f %% (einfach %+4.0f %%) | H1 Infl %+5.1f · H2 ESTR %+5.1f · H3 BTC %+6.1f | ueber H1 %3.0f %% · ueber H3 %3.0f %% | gg. H1 %+7.1f · gg. H3 %+7.1f Pp%s" % (
        name, n, 100 * np.mean(r), 100 * np.expm1(np.mean(r)), 100 * np.mean(h1), 100 * np.mean(h2), 100 * np.mean(h3), 100 * np.mean(r > h1), 100 * np.mean(r > h3),
        100 * np.mean(r - h1), 100 * np.mean(r - h3), extra)


# ══ Teil A ══════════════════════════════════════════════════════════════════════════════════════════════════════════════
def teil_a(H, K):
    D = pd.read_csv(os.path.join(SPOT, "b4_vormessung.csv"), sep=";", parse_dates=["t"])
    D = D[(D.ep == "E3") & D.p9.notna()].reset_index(drop=True)
    tage = sorted(D.t.unique())
    print("TEIL A · 12 M ab Monatsstichtag · E3 %s bis %s · %d Stichtage · %d Anker (Coin x Stichtag)\n" % (
        pd.Timestamp(tage[0]).date(), pd.Timestamp(tage[-1]).date(), len(tage), len(D)))
    c = D.kl.map(KOST).values
    D["r_usd"] = np.log(D.ende.clip(lower=1e-9) * (1 - c))
    D["r_usd_eing"] = np.where(D.eing, np.log(1e-9), D.r_usd)
    D["kauf"] = D.t + pd.Timedelta(days=1)
    D["ende_t"] = D.kauf + pd.Timedelta(days=365)
    # X2: Fuehrung -35 % vom Hoch seit Kauf, danach ESTR
    x2 = np.full(len(D), np.nan)
    sel_o = D.p9.values > 0.8
    for i in np.where(sel_o)[0]:
        s, a, b = D.sym[i], D.kauf[i], D.ende_t[i]
        if s not in K.columns:
            continue
        p = K[s].loc[a:b].ffill().dropna()
        if len(p) < 2:
            continue
        hoch = p.cummax()
        raus = p[p <= 0.65 * hoch]
        if len(raus):
            tx = raus.index[0]
            x2[i] = np.log(p[tx] / p.iloc[0] * (1 - c[i])) + float(H.h2(pd.DatetimeIndex([tx]), pd.DatetimeIndex([b]))[0])
        else:
            x2[i] = np.log(p.iloc[-1] / p.iloc[0] * (1 - c[i]))
    D["r_x2"] = x2
    a_, b_ = pd.DatetimeIndex(D.kauf), pd.DatetimeIndex(D.ende_t)
    fx = H.fx(a_, b_)
    D["h1"], D["h2"] = H.h1(a_, b_), H.h2(a_, b_)
    D["h3"] = np.log(D.ende_b * (1 - KOST_BTC)) - fx

    def korb(mask, spalte="r_usd"):
        """Gleichgewichteter Korb je Stichtag (einfache Ertraege gemittelt), in Euro; Rueckgabe je Stichtag."""
        g = D[mask & D[spalte].notna()].groupby("t")
        r = g[spalte].apply(lambda x: np.log(np.mean(np.exp(x))))
        first = g.first()
        return r, first.h1, first.h2, first.h3, D[mask].groupby("t").kauf.first()

    sets = {"A0 alle Coins der Watchlist-Zellen": D.p9.notna().values,
            "A1 oberes Fuenftel, 12 M halten": D.p9.values > 0.8,
            "A9 unteres Fuenftel (B4)": D.p9.values <= 0.2}
    erg = {}
    for name, m in sets.items():
        r, h1, h2, h3, ka = korb(m)
        fxs = H.fx(pd.DatetimeIndex(ka.values), pd.DatetimeIndex(ka.values + pd.Timedelta(days=365)))
        re = r.values - fxs
        erg[name] = re.mean()
        print(zeile(name, int(m.sum()), re, h1.values, h2.values, h3.values))
        if name.startswith("A1"):
            r2, *_ = korb(m, "r_x2")
            re2 = r2.values - fxs[:len(r2)]
            print(zeile("A2 oberes Fuenftel + Fuehrung X2 (Rest ESTR)", int(np.isfinite(x2).sum()), re2, h1.values, h2.values, h3.values))
            erg["A2"] = re2.mean()
        if name.startswith("A9"):
            r3, *_ = korb(m, "r_usd_eing")
            print("     Auskunft: eingestellte Coins = -100 %%: Korb %+.1f %%" % (100 * (r3.values - fxs).mean()))
    # Nullwelt: bestaendige Zufallszahl je Coin, Fuenftel je Zelle (t x kl)
    print("\n  BELEG gegen Zufallsauswahl (bestaendige Zufallszahl je Coin, gleiches Fuenftel je Zelle, 200 Ziehungen):")
    syms = D.sym.unique()
    null_o, null_u = [], []
    for _ in range(200):
        z = pd.Series(RNG.random(len(syms)), index=syms)
        q = D.assign(z=D.sym.map(z)).groupby(["t", "kl"]).z.rank(pct=True).values
        for lst, mm in ((null_o, q > 0.8), (null_u, q <= 0.2)):
            r, *_ , ka = korb(mm)
            fxs = H.fx(pd.DatetimeIndex(ka.values), pd.DatetimeIndex(ka.values + pd.Timedelta(days=365)))
            lst.append((r.values - fxs).mean())
    for name, lst in (("A1 oberes Fuenftel", null_o), ("A9 unteres Fuenftel", null_u)):
        a = erg[[k for k in erg if k.startswith(name[:2])][0]]
        lst = np.array(lst)
        print("    %-20s %+6.1f %% · Zufall Mittel %+6.1f %% (2,5./97,5. %+6.1f / %+6.1f) · Rang %.3f" % (
            name, 100 * a, 100 * lst.mean(), 100 * np.percentile(lst, 2.5), 100 * np.percentile(lst, 97.5), np.mean(lst < a)))
    return D


# ══ Teil B ══════════════════════════════════════════════════════════════════════════════════════════════════════════════
REGELN_B = [("Regel 3 K-H1 Momentum 30 T", "k37_einstiege_%s_%s", ("H", "M")),
            ("Regel 4 K-3 ruhiger Boden", "k3_einstiege_%s_%s", ("H", "M", "S")),
            ("Regel 6 U2 Gebuehren-Wachstum", "k47_einstiege_U2_%s", None),
            ("Regel 7 U1 Stablecoins je Kette", "k47_einstiege_U1_%s", None)]
BELEG_B = {"Regel 3": "§37: trägt nicht (H) / schadet (M)", "Regel 4": "§40: schadet", "Regel 6": "§46: schadet", "Regel 7": "§46: trägt nicht"}


def teil_b(H, K):
    print("\nTEIL B · 30 T je Einstieg (Tagesregeln, gespeicherte Einstiege ab 2024) · Bilanz je Einstieg; Beleg aus der jeweiligen Messung")
    btc = K["BTC"].ffill()
    tage = K.index
    gegen = []
    for name, muster, klassen in REGELN_B:
        for var in ("U",):          # W = Wahljahr 2023, nicht im Urteilszeitraum
            teile = []
            if klassen:
                for k in klassen:
                    f = os.path.join(SPOT, (muster % (k, var)) + ".csv")
                    if os.path.exists(f):
                        teile.append(pd.read_csv(f, sep=";").assign(kl=k))
            else:
                f = os.path.join(SPOT, (muster % var) + ".csv")
                if os.path.exists(f):
                    teile.append(pd.read_csv(f, sep=";"))
            if not teile:
                continue
            E = pd.concat(teile, ignore_index=True)
            E = E[E.signal >= "2024-01-01"].reset_index(drop=True)
            a = BASIS + pd.to_timedelta(E.i_kauf, unit="D")
            b = BASIS + pd.to_timedelta(E.i_aus, unit="D")
            ok = (b <= tage[-1]).values
            E, a, b = E[ok].reset_index(drop=True), pd.DatetimeIndex(a[ok]), pd.DatetimeIndex(b[ok])
            pa = np.array([K[s].get(t, np.nan) if s in K.columns else np.nan for s, t in zip(E.sym, a)])
            pb = np.array([K[s].get(t, np.nan) if s in K.columns else np.nan for s, t in zip(E.sym, b)])
            fx = H.fx(a, b)
            r = np.log(pb / pa * (1 - E.kl.map(KOST).values)) - fx
            h3 = np.log(btc[b].values / btc[a].values * (1 - KOST_BTC)) - fx
            h1, h2 = H.h1(a, b), H.h2(a, b)
            gut = np.isfinite(r)
            gegen.append(np.log(pb / pa) - np.log(btc[b].values / btc[a].values))
            jahr = 365.0 / 30
            print(zeile(name, int(gut.sum()), r[gut], h1[gut], h2[gut], h3[gut],
                        " | je Jahr hochgerechnet %+.0f %% (H1 %+.1f %%) | Beleg %s" % (100 * np.mean(r[gut]) * jahr, 100 * np.mean(h1[gut]) * jahr, BELEG_B[name[:7]])))
    return gegen


def gegenprobe_b(K):
    """Rechenweg-Probe: (Coin/BTC - 1) ueber i_kauf..i_aus gegen 'ex' aus den gespeicherten Messungen."""
    btc = K["BTC"].ffill()
    aus = []
    for f in ("k37_messung_H", "k3_messung", "k47_messung_U2"):
        E = pd.read_csv(os.path.join(SPOT, f + ".csv"), sep=";")
        E = E[E.signal >= "2024-01-01"].head(200)
        a = BASIS + pd.to_timedelta(E.i_kauf, unit="D")
        b = BASIS + pd.to_timedelta(E.i_aus, unit="D")
        mine = np.array([K[s].get(x, np.nan) / K[s].get(y, np.nan) / (btc[x] / btc[y]) - 1 if s in K.columns else np.nan
                         for s, x, y in zip(E.sym, b, a)])
        d = np.abs(mine - E.ex.values)
        aus.append("%s: %d von %d gleich (|d| < 0,001), Median |d| %.5f" % (f, int(np.nansum(d < 1e-3)), int(np.isfinite(d).sum()), np.nanmedian(d)))
    print("\nGEGENPROBE Rechenweg Teil B (Index-Basis 2017-08-17, Ertrag gegen BTC = 'ex' der Messung): " + " · ".join(aus))


def main():
    H = Huerden()
    K, _ = S1.lade()
    print("P50 INVENTUR · Massstab §51.8 · Kurse bis %s · HICP bis %s (danach letzte J/J-Rate) · alle Ertraege log, in Euro, nach Kosten\n" % (
        K.index[-1].date(), H.hicp_ende.strftime("%m/%Y")))
    teil_a(H, K)
    teil_b(H, K)
    gegenprobe_b(K)
    a, b = pd.DatetimeIndex(["2024-01-01"]), pd.DatetimeIndex([K.index[-1]])
    btc = K["BTC"].ffill()
    print("\nBILANZ ganzer Zeitraum 01/2024 bis %s (Euro): H1 Inflation %+.1f %% · H2 ESTR %+.1f %% · BTC halten %+.1f %% (log)" % (
        K.index[-1].date(), 100 * H.h1(a, b)[0], 100 * H.h2(a, b)[0], 100 * (np.log(btc[b[0]] / btc[a[0]] * (1 - KOST_BTC)) - H.fx(a, b)[0])))


if __name__ == "__main__":
    main()
