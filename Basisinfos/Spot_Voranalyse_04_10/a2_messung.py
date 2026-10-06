"""Altcoin-Spot Fassung 2 - antizyklisch kaufen und Positionen fuehren (Voranalyse_Spot_Neubau_04_10.md §15, vorab Commit a92ee2d; E-70).

    python Basisinfos/Spot_Voranalyse_04_10/a2_messung.py

Nur lesend: data/messdaten.db (Krypto USD mit eingestellten), data/_spot/coinmetrics.db (BTC-Klima fuer B). Universum und Klassen
H/M/S exakt wie s3_stufe1.py (stabile Highcaps, Midcaps, Smallcaps; ohne BTC/ETH/SOL, Stablecoins, Fiat/Gold/Wrapped).

AUSLEGUNG, vor dem ersten Lauf festgelegt (im Plan nicht genau bestimmt):
  - Ausstiege wie Einstiege zum Schluss des FOLGETAGS (das Signal steht erst am Tagesschluss fest)
  - X2: Nachlauf -35 % vom Hoch seit Einstieg gilt ab dem Kauf; die Notbremse -50 % greift damit nur bei Kursluecken
  - X1: Nachlauf wie X2 auf den jeweils verbliebenen Teil; Gewinnmitnahmen 1/3 bei Schluss >= 2x bzw. >= 3x Einstieg
  - Kosten Coin 1,25 % je Kauf und je Verkauf (Smallcaps Auskunft 3 %); BTC-Vergleich mit 0,4 % je Seite (gemessen, G1-M1)
  - Vorteil gegen BTC = (1 + Ertrag Coin) / (1 + Ertrag BTC mit denselben Kauf- und Verkaufstagen und Anteilen) - 1
  - Klasse des Ereignisses = Klasse am Monatsersten des Ereignismonats
  - Nullwelt: je Ereignis 20 zufaellige Einstiegstage desselben Coins im selben Kalenderjahr (mit Kurs), gleiche Ausstiegsregel;
    200 Gesamtziehungen, je Ereignis eine der 20 zufaellig; Rang = Anteil der Ziehungen unter dem echten Tagesklammer-Mittel
  - Tagesklammer: Mittel je Einstiegstag, dann Mittel bzw. Median ueber die Tage
"""
import os
import sys

import numpy as np
import pandas as pd

HIER = os.path.dirname(os.path.abspath(__file__))
os.chdir(os.path.dirname(os.path.dirname(HIER)))
sys.argv = ["x"]
_src = open(os.path.join(HIER, "s3_stufe1.py"), encoding="utf-8").read().split("zeilen, gnh = [], {}")[0]
G = {"__file__": os.path.join(HIER, "s3_stufe1.py")}
exec(compile(_src, "s3", "exec"), G)
K, UNIV, klassen = G["K"], G["UNIV"], G["klassen"]
ENDE = K.index.max()
RNG = np.random.default_rng(20261006)
KO_COIN, KO_BTC = 0.0125, 0.004
BTCV = K["BTC"].values
IDX = K.index
POS = {t: i for i, t in enumerate(IDX)}


def epoche(t):
    return "E1" if t < pd.Timestamp("2021-01-01") else ("E2" if t < pd.Timestamp("2024-01-11") else "E3")


# ---------------------------------------------------------------- Ereignisse
X = K[UNIV]
hoch = X.rolling(365, min_periods=180).max()
dd = X / hoch - 1
s50 = X.rolling(50, min_periods=50).mean()
unter60 = (X < s50).astype(float).rolling(60).sum().shift(1) >= 60
A1 = (X > s50) & unter60 & (dd.rolling(60).min() <= -0.75)
A2 = (dd <= -0.75) & (dd.shift(1) > -0.75)


def mit_ruhe(E, ab="2020-01-01"):
    out = []
    for s in E.columns:
        last = None
        for t in E.index[E[s].fillna(False).values]:
            if t < pd.Timestamp(ab):
                continue
            if last is None or (t - last).days >= 180:
                out.append((t, s)); last = t
    return out


def markt_boden():
    src = open(os.path.join(HIER, "k3_gewichten.py"), encoding="utf-8").read().split("pb, mb = lade")[0]
    g = {"__file__": os.path.join(HIER, "k3_gewichten.py")}
    exec(compile(src, "k3", "exec"), g)
    pb, mb = g["lade"]("btc")
    q = g["klima"](pb, mb, pd.Timestamp("2013-01-01"))
    z = (q <= 0.20)[q.index >= "2018-01-01"]
    ep, lz = [], None
    for t, v in z.items():
        if v:
            if lz is None or (t - lz).days >= 30:
                ep.append(t)
            lz = t
    return [t for t in ep if t >= IDX[0] + pd.Timedelta(days=400)]


# ---------------------------------------------------------------- Pfad und Ausstieg
def pfad(sym, i0, maxtage):
    v = K[sym].values[i0:i0 + maxtage + 1]
    ok = ~np.isnan(v)
    if not ok[0]:
        return None, None
    if not ok.all():
        v = v[:np.argmin(ok)]                                  # endet beim ersten fehlenden Kurs (eingestellt)
    return v, BTCV[i0:i0 + len(v)]


def ausstieg(v, art):
    """Liste (Tag, Anteil) der Verkaeufe; Ausfuehrung am Folgetag des Signals; sonst Rest am letzten Tag."""
    n = len(v)
    if art == "X3":
        return [(min(365, n - 1), 1.0)]
    h = np.maximum.accumulate(v)
    trail = np.where(v < 0.65 * h)[0]
    t_tr = trail[0] + 1 if len(trail) else None
    if art == "X2":
        stop = np.where(v < 0.5 * v[0])[0]
        cand = [x + 1 for x in (trail[:1].tolist() + stop[:1].tolist())]
        t = min(cand) if cand else None
        return [(min(t, n - 1), 1.0)] if t is not None else [(n - 1, 1.0)]
    out, rest = [], 1.0
    for faktor in (2.0, 3.0):
        hit = np.where(v >= faktor * v[0])[0]
        if len(hit) and (t_tr is None or hit[0] + 1 < t_tr):
            out.append((min(hit[0] + 1, n - 1), 1 / 3)); rest -= 1 / 3
    out.append((min(t_tr, n - 1) if t_tr is not None else n - 1, rest))
    return out


def handel(sym, i0, art, ko=KO_COIN):
    maxt = 365 if art == "X3" else 730
    v, b = pfad(sym, i0, maxt)
    if v is None or len(v) < 2:
        return None
    vk = ausstieg(v, art)
    erl_c = sum(a * v[t] / v[0] * (1 - ko) for t, a in vk) / (1 + ko)
    erl_b = sum(a * b[t] / b[0] * (1 - KO_BTC) for t, a in vk) / (1 + KO_BTC)
    offen = (i0 + len(v) - 1 >= len(IDX) - 1) and vk[-1][0] == len(v) - 1 and art != "X3"
    # KORREKTUR 06.10.: eingestellt = der Handel ENDETE erzwungen, weil die Reihe des Coins aufhoerte (nicht: irgendwann danach eingestellt)
    eing = (i0 + len(v) - 1 < len(IDX) - 1) and len(v) < (maxt + 1) and vk[-1][0] == len(v) - 1
    return dict(r=erl_c - 1, rb=erl_b - 1, vorteil=erl_c / erl_b - 1, tage=max(t for t, _ in vk), offen=offen, eing=eing)


# ---------------------------------------------------------------- Auswertung
def tagesklammer(df, spalte="vorteil"):
    t = df.groupby("einstieg")[spalte].mean()
    return t.mean(), t.median(), len(t)


def nullwelt(ereignisse, art, ko=KO_COIN):
    """je Ereignis 20 zufaellige Einstiegstage desselben Coins im selben Jahr."""
    pools = []
    for t, s in ereignisse:
        jahr = K[s][str(t.year)].dropna().index
        jahr = jahr[jahr <= ENDE - pd.Timedelta(days=2)]
        if len(jahr) == 0:
            pools.append(None); continue
        tage = RNG.choice(jahr, size=20, replace=True)
        erg = [handel(s, POS[pd.Timestamp(x)] + 1, art, ko) for x in tage]
        pools.append([(pd.Timestamp(x), e["vorteil"]) for x, e in zip(tage, erg) if e is not None])
    werte = []
    for _ in range(200):
        z = [p[RNG.integers(len(p))] for p in pools if p]
        d = pd.DataFrame(z, columns=["einstieg", "vorteil"])
        werte.append(d.groupby("einstieg")["vorteil"].mean().mean())
    return np.array(werte)


def messe(name, ereignisse, art, klasse=None, ko=KO_COIN, null=True):
    zeilen = []
    for t, s in ereignisse:
        if klasse is not None:
            kl, _ = klassen(t.replace(day=1))
            if kl.get(s) != klasse:
                continue
        i0 = POS[t] + 1
        if i0 >= len(IDX):
            continue
        e = handel(s, i0, art, ko)
        if e is None:
            continue
        zeilen.append(dict(e, ereignis=t, einstieg=IDX[i0], sym=s, ep=epoche(t)))
    D = pd.DataFrame(zeilen)
    out = {}
    for ep in ("E1", "E2", "E3"):
        x = D[D["ep"] == ep] if len(D) else D
        if len(x) < 5:
            out[ep] = None; continue
        m, md, ntage = tagesklammer(x)
        rang = None
        if null and ep in ("E2", "E3"):
            nw = nullwelt([(r.ereignis, r.sym) for r in x.itertuples()], art, ko)
            rang = float(np.mean(nw < m))
        out[ep] = dict(n=len(x), tage=ntage, mittel=m, median=md, med_handel=x["vorteil"].median(), ge100=(x["vorteil"] >= 1.0).mean(),
                       le50=(x["r"] <= -0.5).mean(), halte=x["tage"].mean(), offen=x["offen"].mean(), eing=x["eing"].mean(), rang=rang,
                       r_med=x["r"].median(), rb_med=x["rb"].median())
    return out, D


def zeile(name, out):
    traegt = all(out.get(ep) and out[ep]["mittel"] > 0 and out[ep]["median"] > 0 and (out[ep]["rang"] or 0) >= 0.95 for ep in ("E2", "E3"))
    print("\n%s  ->  %s" % (name, "TRAEGT" if traegt else "traegt nicht"))
    for ep in ("E1", "E2", "E3"):
        o = out.get(ep)
        if not o:
            print("  %s  zu wenige Ereignisse" % ep); continue
        print("  %s  n %4d (%3d Tage) | Vorteil gg. BTC: Mittel %+6.1f %% · Median %+6.1f %% (Tagesklammer) · Median je Handel %+6.1f %% | "
              ">= +100 %% gg. BTC %3.0f %% · Ertrag <= -50 %% %3.0f %% | Ertrag Coin Median %+5.0f %% (BTC %+5.0f %%) | Halten %3.0f T, offen %2.0f %%, "
              "eingestellt %2.0f %% | Nullwelt-Rang %s" % (
                  ep, o["n"], o["tage"], 100 * o["mittel"], 100 * o["median"], 100 * o["med_handel"], 100 * o["ge100"], 100 * o["le50"],
                  100 * o["r_med"], 100 * o["rb_med"], o["halte"], 100 * o["offen"], 100 * o["eing"], "%.2f" % o["rang"] if o["rang"] is not None else "-"))
    return traegt


def main():
    print("Altcoin-Spot Fassung 2 (Voranalyse_Spot §15) - antizyklisch kaufen, Positionen fuehren · Daten bis %s" % ENDE.date())
    ea1, ea2 = mit_ruhe(A1), mit_ruhe(A2)
    mb = markt_boden()
    eb = []
    for t in mb:
        kl, _ = klassen(t.replace(day=1))
        eb += [(t, s) for s, c in kl.items() if pd.notna(K.at[t, s])]
    print("Ereignisse: A1 %d · A2 %d · B %d Tage (%s)" % (len(ea1), len(ea2), len(mb), ", ".join(str(t.date()) for t in mb)))
    ergebnis = []
    for kl in ("H", "M", "S"):
        for art in ("X1", "X2", "X3"):
            name = "A1 Boden je Coin mit Wende · Klasse %s · %s" % (kl, art)
            out, _ = messe(name, ea1, art, kl)
            ergebnis.append((name, zeile(name, out)))
    for kl in ("M", "S"):
        name = "A2 Boden ohne Wende (fallendes Messer) · Klasse %s · X2" % kl
        out, _ = messe(name, ea2, "X2", kl)
        ergebnis.append((name, zeile(name, out)))
    for kl in ("H", "M"):
        for art in ("X1", "X2"):
            name = "B Markt-Boden-Korb · Klasse %s · %s" % (kl, art)
            out, D = messe(name, eb, art, kl)
            ergebnis.append((name, zeile(name, out)))
            if len(D):
                je = D.groupby("einstieg")["vorteil"].mean()
                print("    je Episode (Korb gegen BTC): " + " · ".join("%s %+.0f %%" % (t.date(), 100 * v) for t, v in je.items()))
    print("\nAUSKUNFT Smallcaps mit 3 % Kosten je Seite (A1 · S):")
    for art in ("X1", "X2", "X3"):
        out, _ = messe("A1 S %s 3 %%" % art, ea1, art, "S", ko=0.03, null=False)
        print("  %s: " % art + " · ".join("%s Mittel %+.1f %% Median %+.1f %%" % (ep, 100 * out[ep]["mittel"], 100 * out[ep]["median"])
                                         for ep in ("E2", "E3") if out.get(ep)))
    print("\nGESAMT (vorab §15.5: E2 UND E3 Mittel > 0, Median > 0, Nullwelt-Rang >= 0,95):")
    for n, t in ergebnis:
        print("  %-60s %s" % (n, "TRAEGT" if t else "-"))


if __name__ == "__main__":
    main()
