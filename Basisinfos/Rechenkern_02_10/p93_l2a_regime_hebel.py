"""P93 MESSPLAN L2-a STUFE 1 (Voranalyse_L2a_Regime_Hebel_Kern_25_10.md §7, vorab 65c5a2a9): Regime-Hebel auf dem Kern.

    python -X utf8 Basisinfos/Rechenkern_02_10/p93_l2a_regime_hebel.py

Schritt 0  R-R11: E-126 nachrechnen - Fassung 1b (§9, 876072ce): E-126s Groesse S1 (Monate draussen EUR +0,9 % +- 0,2); "an - alle" nur Auskunft
Selbsttest je Wert VOR dem ersten Blick (Fehlalarm <= 5 %, Pflanzung +0,5/1/2/3 Pp, X = kleinste Staerke mit >= 80 % Fund)
Stufe 1    R1 BTC-Schluss am Vortag ueber 200-T-Schnitt; BTC, ETH, SOL; Ertrag 7 T vor Kosten; Vorsprung = Mittel an - Mittel alle
Nullwelt Strecken-Permutation, Nullpunkt = Mittel; Band zirkulaerer Tagesblock (messnorm._block(7) = 21 T); < 20 Bloecke KEIN BEFUND.
Nur lesend.
"""
import os
import sys

import numpy as np
import pandas as pd

HIER = os.path.dirname(os.path.abspath(__file__))
WURZEL = os.path.dirname(os.path.dirname(HIER))
sys.path.insert(0, HIER)
sys.path.insert(0, WURZEL)
os.chdir(WURZEL)
sys.stdout.reconfigure(encoding="utf-8")
import warnings  # noqa: E402

warnings.filterwarnings("ignore", category=RuntimeWarning)
import messnorm  # noqa: E402
import p91_l2a_voranalyse as P91  # noqa: E402

RNG = np.random.default_rng(93)
STAERKEN = (0.005, 0.01, 0.02, 0.03)
ENDE = pd.Timestamp("2026-09-30")


def vorsprung(z, y):
    z = z.astype(bool)
    return y[z].mean() - y.mean() if z.any() else np.nan


def nullwelt(z, y, rng, k):
    return np.array([vorsprung(P91.permutiere(z, rng), y) for _ in range(k)])


def band(z, y, block, rng, n=2000):
    """zirkulaerer Blockbootstrap ueber die Tage (z und y gemeinsam gezogen) -> Verteilung des Vorsprungs."""
    m = len(y)
    st = rng.integers(0, m, (n, int(np.ceil(m / block))))
    ix = ((st[:, :, None] + np.arange(block)) % m).reshape(n, -1)[:, :m]
    Z, Y = z[ix].astype(float), y[ix]
    return (Y * Z).sum(1) / np.maximum(Z.sum(1), 1) - Y.mean(1)


def ak(y, lag):
    y = np.asarray(y, float)
    return float(np.corrcoef(y[:-lag], y[lag:])[0, 1]) if len(y) > lag + 5 else np.nan


def urteil(z, y, block, rng, k_null=1000, n_boot=2000, x=None):
    """-> dict echt, nullpunkt, rang, lo, hi, bloecke, stufe."""
    bl = len(y) / block
    echt = vorsprung(z, y)
    nw = nullwelt(z, y, rng, k_null)
    np0 = float(nw.mean())
    rang = float(np.mean(nw < echt))
    b = band(z, y, block, rng, n_boot) - np0
    lo, hi = np.percentile(b, [2.5, 97.5])
    if bl < 20:
        st = "KEIN BEFUND"
    elif rang >= 0.95 and lo > 0:
        st = "TRAEGT"
    elif x is not None and hi < x:
        st = "TRAEGT NICHT BIS %.1f Pp" % (100 * x)
    else:
        st = "NICHT TRENNBAR"
    return dict(echt=echt, np0=np0, rang=rang, lo=lo, hi=hi, bl=bl, stufe=st)


def zeile(name, u):
    return "%-34s Vorsprung %+.2f Pp · Nullpunkt %+.2f · Rang %.3f · Band (minus Nullpunkt) [%+.2f; %+.2f] Pp · %.0f Bloecke -> %s" % (
        name, 100 * u["echt"], 100 * u["np0"], u["rang"], 100 * u["lo"], 100 * u["hi"], u["bl"], u["stufe"])


def schritt0(K):
    b = K.btc.dropna()
    me = b.resample("ME").last()
    stand = me > me.rolling(10).mean()
    t1 = [b.index[b.index.searchsorted(t + pd.Timedelta(days=1))] for t in me.index[:-1]]
    kurs1 = b.reindex(t1).to_numpy()
    r = pd.Series(kurs1[1:] / kurs1[:-1] - 1, index=me.index[:-2])        # Ertrag des Folgemonats, gehandelt t+1
    s = stand.reindex(r.index)
    ok = (r.index >= pd.Timestamp("2016-12-31")) & (r.index <= pd.Timestamp("2026-08-31")) & s.notna().to_numpy()
    z, y = s[ok].astype(int).to_numpy(), r[ok].to_numpy()
    block = int(np.ceil(messnorm._block(30) / 30.4))
    u = urteil(z, y, block, RNG)
    print("SCHRITT 0 (R-R11) E-126 nachrechnen: BTC Monatsschluss > 10-Monats-Schnitt, Folgemonat t+1, %s..%s, %d Monate, an %.0f %%, Block %d Monate" % (
        r.index[ok][0].date(), r.index[ok][-1].date(), len(y), 100 * z.mean(), block))
    print("  " + zeile("10-Monats-Schnitt (M-A)", u))
    print("  Auskunft: Monatsertrag an %+.1f %% · aus %+.1f %% (E-126 Teil B: Monate draussen +0,9 %% in EUR)" % (
        100 * y[z == 1].mean(), 100 * y[z == 0].mean()))
    rep = u["stufe"] != "TRAEGT"
    print("  -> %s\n" % ("REPRODUZIERT (nicht TRAEGT, wie E-126)" if rep else "NICHT REPRODUZIERT - Halt, Pruefstand und E-126 widersprechen sich"))
    return rep


def schritt0_1b(K):
    """Fassung 1b (§9, vorab 876072ce): E-126s eigene Groesse S1 - Monate DRAUSSEN in EUR, Teil B - reproduziert bei +0,9 % +- 0,2 Pp."""
    import p93b_schritt0_klaerung as KL
    usd = K.btc.dropna()
    e = pd.read_csv("data/_spot/ma_eurusd_ezb.csv")
    e = e.set_index(pd.to_datetime(e.iloc[:, 0])).iloc[:, -1].astype(float)
    eur = (usd / e.reindex(usd.index).ffill()).dropna()
    z, y = KL.monate(eur, "2016-12-31", "2026-08-31")
    s1 = y[z == 0].mean()
    rep = abs(100 * s1 - 0.9) <= 0.2
    print("SCHRITT 0 FASSUNG 1b (R-R11 auf E-126s Groesse S1): Monate draussen BTC in EUR, Teil B, %d Monate davon %d draussen: %+.2f %% "
          "(E-126: +0,9 %%, n 38) -> %s\n" % (len(y), int((z == 0).sum()), 100 * s1, "REPRODUZIERT" if rep else "NICHT REPRODUZIERT - Halt"))
    return rep


def reihe(K, a, Z):
    y_all = K[a].shift(-7) / K[a] - 1
    ab = max(pd.Timestamp("2015-01-01"), K[a].first_valid_index() + pd.Timedelta(days=200))
    tage = y_all.index[(y_all.index >= ab) & (y_all.index <= ENDE) & y_all.notna()]
    z = Z.reindex(tage)
    ok = z.notna().to_numpy()
    return tage[ok], z[ok].astype(int).to_numpy(), y_all.reindex(tage[ok]).to_numpy()


def selbsttest(z, y, block, rng):
    """Fehlalarm und Aufloesungskurve auf Zufallsregimen mit der Streckenstruktur von z (echtes Ergebnis nicht angesehen)."""
    fa = sum(urteil(P91.permutiere(z, rng), y, block, rng, 200, 300)["stufe"] == "TRAEGT" for _ in range(100)) / 100
    fund = {}
    for d in STAERKEN:
        n = 0
        for _ in range(100):
            zp = P91.permutiere(z, rng)
            n += urteil(zp, y + d * zp, block, rng, 200, 300)["stufe"] == "TRAEGT"
        fund[d] = n / 100
    x = next((d for d in STAERKEN if fund[d] >= 0.8), None)
    return fa, fund, x


def main():
    K = P91.kurse()
    print("P93 MESSPLAN L2-a STUFE 1 · Regime-Hebel Kern · Ertrag 7 T vor Kosten (neutral, Gebuehren nachgelagert)\n")
    print("(Auskunft, entscheidet seit Fassung 1b nicht:)")
    schritt0(K)
    if not schritt0_1b(K):
        return 1
    Z = P91.kandidaten(K)
    r1, r2 = Z.columns[0], Z.columns[1]
    block = messnorm._block(7)
    daten = {a: reihe(K, a, Z[r1]) for a in ("btc", "eth", "sol")}
    print("SELBSTTEST vor dem ersten Blick (100 Zufallsregime je Stufe, Strecken wie R1; Soll Fehlalarm <= 5 %, Fund >= 80 %):")
    xs, bestanden = {}, True
    for a, (tage, z, y) in daten.items():
        fa, fund, x = selbsttest(z, y, block, RNG)
        xs[a] = x
        ok = fa <= 0.05
        bestanden &= ok
        print("  %s %s..%s %d Tage · %.0f Bloecke · AK y beim Blockabstand %.2f · Fehlalarm %.0f %% %s · Fund %s · Aufloesung X %s" % (
            a.upper(), tage[0].date(), tage[-1].date(), len(y), len(y) / block, ak(y, block), 100 * fa, "ok" if ok else "NICHT OK",
            " ".join("%+.1f Pp %.0f %%" % (100 * d, 100 * f) for d, f in fund.items()), "%.1f Pp" % (100 * x) if x else "keine <= 3 Pp"))
    if not bestanden:
        print("\nSELBSTTEST NICHT BESTANDEN - echtes Ergebnis wird nicht angesehen (Plan §7).")
        return 1
    print("  -> Selbsttest bestanden\n")
    print("STUFE 1 · R1 BTC ueber 200-T-Schnitt (Vortag):")
    st = {}
    for a, (tage, z, y) in daten.items():
        u = urteil(z, y, block, RNG, x=xs[a])
        st[a] = u
        print("  " + zeile("%s (an %.0f %%)" % (a.upper(), 100 * z.mean()), u))
    print("\nJE HAELFTE und EPOCHE (Punktwert, Rang gegen Strecken-Permutation 1.000):")
    haelften = {}
    for a, (tage, z, y) in daten.items():
        teile = []
        for name, m in (("2015-2020", tage.year <= 2020), ("2021-2026", tage.year >= 2021), ("ab 11.01.2024", tage >= pd.Timestamp("2024-01-11"))):
            if m.sum() < 100:
                continue
            v = vorsprung(z[m], y[m])
            rg = float(np.mean(nullwelt(z[m], y[m], RNG, 1000) < v))
            teile.append("%s %+.2f Pp (Rang %.2f, %.0f Bl.)" % (name, 100 * v, rg, m.sum() / block))
            haelften[(a, name)] = v
        print("  %s: %s" % (a.upper(), " · ".join(teile)))
    vola = np.log(K.btc).diff()
    print("  Auskunft BTC-Schwankung (aufs Jahr): 2015-2020 %.0f %% · 2021-2026 %.0f %%" % (
        100 * vola["2015":"2020"].std() * np.sqrt(365), 100 * vola["2021":"2026-09"].std() * np.sqrt(365)))
    print("\nAUSKUNFT R2 BTC 91 T > +20 % (Fehlalarm ueber dem Soll, entscheidet nicht):")
    for a in ("btc", "eth", "sol"):
        tage, z, y = reihe(K, a, Z[r2])
        v = vorsprung(z, y)
        print("  %s Vorsprung %+.2f Pp · Rang %.3f" % (a.upper(), 100 * v, float(np.mean(nullwelt(z, y, RNG, 1000) < v))))
    traegt = (st["btc"]["stufe"] == "TRAEGT" and (st["eth"]["stufe"] == "TRAEGT" or st["sol"]["stufe"] == "TRAEGT")
              and haelften.get(("btc", "2015-2020"), -1) > 0 and haelften.get(("btc", "2021-2026"), -1) > 0)
    print("\nGESAMTURTEIL (Plan §7): %s" % ("TRAEGT -> Stufe 2 Top 30 zur Abstimmung" if traegt else
                                         "TRAEGT NICHT - Hebel bleibt bei REGEL0, kein weiterer Trendfilter (Folge §5)"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
