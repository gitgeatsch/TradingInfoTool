"""Altcoin Fassung 4 - Momentum statt Umkehr (Voranalyse_Spot_Neubau_04_10.md §17, vorab Commit 3e53077).

    python Basisinfos/Spot_Voranalyse_04_10/m4_messung.py

Universum, Klassen, Kosten, Pfad (eingestellt = letzter Kurs) wie a2_messung.py. Nur lesend.

AUSLEGUNG, vor dem ersten Lauf festgelegt:
  - M1/M2: Entscheid am Schluss des Monatsersten t (Klasse dieses Monats), Kauf Schluss t+1, Verkauf Schluss t+1+28. Kandidat = Klasse passt, Kurs an t,
    t-Rueckblick und t+1. Mindestens 5 Kandidaten, sonst entfaellt der Monat. Oberes Fuenftel = ceil(20 %), mindestens 2. Monate ohne volles
    Haltefenster am Datenende entfallen. Rang = Anteil der 200 Zufallsportfolios (Mittel ueber die Monate der Epoche) unter dem echten Mittel
  - M3: Signal am Schluss t, Kauf t+1; Ausstiegssignal ab dem Kauftag, Verkauf am Folgetag; neuer Kauf fruehestens am Tag nach dem Verkauf;
    Klasse = Klasse am Monatsersten des Signalmonats (ohne Klasse kein Kauf). Nullwelt N1 wie a3_messung (20 Tage im selben Jahr, 200 Ziehungen)
  - M0 (Auskunft): Entscheid alle 7 T ab 07.01.2019, Rueckblick 7, Halten 7; Nullwelt wie M1
"""
import math
import os
import sys

import numpy as np
import pandas as pd

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HIER)
import a2_messung as A  # noqa: E402

K, IDX, POS, ENDE, BTCV = A.K, A.IDX, A.POS, A.ENDE, A.BTCV
KO, KB = A.KO_COIN, A.KO_BTC
RNG = np.random.default_rng(20261009)
NZ = 200
_KL = {}


def kl_monat(t):
    m = pd.Timestamp(t).replace(day=1)
    if m not in _KL:
        _KL[m] = A.klassen(m)[0]
    return _KL[m]


def halte(s, i0, n):
    v, b = A.pfad(s, i0, n)
    if v is None or len(v) < 2:
        return None
    c, bb = v[-1] / v[0], b[-1] / b[0]
    return c * (1 - KO) / (1 + KO) / (bb * (1 - KB) / (1 + KB)) - 1, c / bb - 1


# ---------------------------------------------------------------- M1 / M2 / M0
def querschnitt(klasse, rueck, halten, termine):
    zeilen = []
    for t in termine:
        i = POS.get(t)
        if i is None or i - rueck < 0 or i + 1 + halten >= len(IDX):
            continue
        kl = kl_monat(t)
        kand = []
        for s, k in kl.items():
            if k != klasse:
                continue
            x, x0 = K[s].values[i], K[s].values[i - rueck]
            if np.isnan(x) or np.isnan(x0):
                continue
            h = halte(s, i + 1, halten)
            if h is None:
                continue
            kand.append((x / x0 / (BTCV[i] / BTCV[i - rueck]), h[0], h[1]))
        if len(kand) < 5:
            continue
        kand.sort(key=lambda z: -z[0])
        k = max(2, math.ceil(0.2 * len(kand)))
        net = np.array([z[1] for z in kand]); bru = np.array([z[2] for z in kand])
        nul = np.array([net[RNG.choice(len(net), k, replace=False)].mean() for _ in range(NZ)])
        zeilen.append(dict(t=t, ep=A.epoche(t), n_k=len(kand), k=k, net=net[:k].mean(), bru=bru[:k].mean(), alle=net.mean(), nul=nul))
    return zeilen


def bewerte_qs(z):
    out = {}
    for ep in ("E1", "E2", "E3"):
        x = [r for r in z if r["ep"] == ep]
        if len(x) < 6:
            out[ep] = None; continue
        net = np.array([r["net"] for r in x]); nul = np.array([r["nul"] for r in x]).mean(axis=0)
        out[ep] = dict(n=len(x), mittel=net.mean(), median=np.median(net), plus=(net > 0).mean(), bru=np.mean([r["bru"] for r in x]),
                       alle=np.mean([r["alle"] for r in x]), rang=float(np.mean(nul < net.mean())), k=np.mean([r["k"] for r in x]), n_k=np.mean([r["n_k"] for r in x]))
    return out


# ---------------------------------------------------------------- M3
RATIO = K[A.UNIV].div(K["BTC"], axis=0)
M50 = RATIO.rolling(50, min_periods=50).mean()
REL28 = RATIO / RATIO.shift(28) - 1
EIN = (RATIO > M50) & (REL28 > 0)
AUS = (RATIO < M50).values
SPALTE = {s: j for j, s in enumerate(RATIO.columns)}


def trend_handel(s, i0):
    v, b = A.pfad(s, i0, 365)
    if v is None or len(v) < 2:
        return None
    a = AUS[i0:i0 + len(v), SPALTE[s]]
    hit = np.where(a)[0]
    j = min(hit[0] + 1, len(v) - 1) if len(hit) else len(v) - 1
    c, bb = v[j] / v[0], b[j] / b[0]
    return dict(vorteil=c * (1 - KO) / (1 + KO) / (bb * (1 - KB) / (1 + KB)) - 1, brutto=c / bb - 1, r=c * (1 - KO) / (1 + KO) - 1, tage=j,
                offen=(i0 + j >= len(IDX) - 1) and not len(hit))


def m3_ereignisse():
    ev = []
    ab = POS[pd.Timestamp("2019-01-01")]
    E = EIN.values
    for s in RATIO.columns:
        j = SPALTE[s]
        i = ab
        while i < len(IDX) - 2:
            if E[i, j]:
                k = kl_monat(IDX[i]).get(s)
                if k in ("H", "M", "S"):
                    h = trend_handel(s, i + 1)
                    if h is not None:
                        ev.append(dict(h, t=IDX[i], sym=s, kl=k, ep=A.epoche(IDX[i]), einstieg=IDX[i + 1]))
                        i = i + 1 + h["tage"] + 1
                        continue
            i += 1
    return pd.DataFrame(ev)


def m3_nullwelt(x):
    pools = []
    for t, s in zip(x["t"], x["sym"]):
        reihe = K[s].dropna().index
        tage = reihe[(reihe.year == t.year) & (reihe <= ENDE - pd.Timedelta(days=2))]
        z = RNG.choice(tage, size=20, replace=True)
        pools.append([(pd.Timestamp(d), h["vorteil"]) for d in z for h in [trend_handel(s, POS[pd.Timestamp(d)] + 1)] if h is not None])
    w = []
    for _ in range(NZ):
        zz = [p[RNG.integers(len(p))] for p in pools if p]
        d = pd.DataFrame(zz, columns=["einstieg", "vorteil"])
        w.append(d.groupby("einstieg")["vorteil"].mean().mean())
    return np.array(w)


def bewerte_m3(D, klasse):
    out = {}
    for ep in ("E1", "E2", "E3"):
        x = D[(D["kl"] == klasse) & (D["ep"] == ep)]
        if len(x) < 10:
            out[ep] = None; continue
        tk = x.groupby("einstieg")["vorteil"].mean()
        rang = float(np.mean(m3_nullwelt(x) < tk.mean())) if ep in ("E2", "E3") else None
        out[ep] = dict(n=len(x), tage=len(tk), mittel=tk.mean(), median=tk.median(), plus=(x["vorteil"] > 0).mean(),
                       bru=x.groupby("einstieg")["brutto"].mean().mean(), halte=x["tage"].mean(), offen=x["offen"].mean(), rang=rang, r_med=x["r"].median())
    return out


def traegt(out):
    return all(out.get(e) and out[e]["mittel"] > 0 and out[e]["median"] > 0 and (out[e]["rang"] or 0) >= 0.95 for e in ("E2", "E3"))


def pz(x):
    return "%+6.1f %%" % (100 * x)


def main():
    print("Altcoin Fassung 4 - Momentum (Voranalyse_Spot §17) · Daten bis %s · Vorteil gegen BTC an denselben Tagen, nach Kosten" % ENDE.date())
    monate = [t for t in pd.date_range("2019-01-01", ENDE, freq="MS") if t in POS]
    gesamt = []
    for name, rueck in (("M1 Querschnitt 4 W", 28), ("M2 Querschnitt 12 W", 84)):
        for kl in ("H", "M", "S"):
            out = bewerte_qs(querschnitt(kl, rueck, 28, monate))
            tr = traegt(out); gesamt.append(("%s · %s" % (name, kl), tr))
            print("\n%s · Klasse %s (oberes Fuenftel, 28 T halten)  ->  %s" % (name, kl, "TRAEGT" if tr else "traegt nicht"))
            for e in ("E1", "E2", "E3"):
                o = out.get(e)
                if not o:
                    print("  %s  zu wenige Monate" % e); continue
                print("  %s  %2d Monate · je Monat %.1f von %.0f Coins | Mittel %s · Median %s · Monate vor BTC %3.0f %% | brutto %s · alle der Klasse %s | Rang %.2f" % (
                    e, o["n"], o["k"], o["n_k"], pz(o["mittel"]), pz(o["median"]), 100 * o["plus"], pz(o["bru"]), pz(o["alle"]), o["rang"]))
    D = m3_ereignisse()
    for kl in ("H", "M", "S"):
        out = bewerte_m3(D, kl)
        tr = traegt(out); gesamt.append(("M3 Trend gg. BTC · %s" % kl, tr))
        print("\nM3 Trend Coin/BTC ueber 50-T + 28-T > 0, Ausstieg unter 50-T · Klasse %s  ->  %s" % (kl, "TRAEGT" if tr else "traegt nicht"))
        for e in ("E1", "E2", "E3"):
            o = out.get(e)
            if not o:
                print("  %s  zu wenige" % e); continue
            print("  %s  n %4d (%3d Tage) | Mittel %s · Median %s · Handel vor BTC %3.0f %% | brutto %s | Coin selbst Median %s | Halten %3.0f T · offen %2.0f %% | Rang N1 %s" % (
                e, o["n"], o["tage"], pz(o["mittel"]), pz(o["median"]), 100 * o["plus"], pz(o["bru"]), pz(o["r_med"]), o["halte"], 100 * o["offen"],
                "%.2f" % o["rang"] if o["rang"] is not None else "-"))
    wochen = [t for t in pd.date_range("2019-01-07", ENDE, freq="7D") if t in POS]
    print("\nM0 Auskunft - Literatur 1 W (Rueckblick 7 T, Halten 7 T, oberes Fuenftel):")
    for kl in ("H", "M"):
        out = bewerte_qs(querschnitt(kl, 7, 7, wochen))
        for e in ("E1", "E2", "E3"):
            o = out.get(e)
            if o:
                print("  %s %s  %3d Wochen | netto Mittel %s · Median %s | brutto %s · alle der Klasse %s | Rang %.2f" % (
                    kl, e, o["n"], pz(o["mittel"]), pz(o["median"]), pz(o["bru"]), pz(o["alle"]), o["rang"]))
    print("\nGESAMT (vorab §17: E2 UND E3 Mittel > 0, Median > 0, Rang >= 0,95):")
    for n, t in gesamt:
        print("  %-26s %s" % (n, "TRAEGT" if t else "-"))


if __name__ == "__main__":
    main()
