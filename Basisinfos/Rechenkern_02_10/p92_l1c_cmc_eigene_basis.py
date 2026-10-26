"""P92 MESSPLAN L1-c (Voranalyse_L1_L2_Asset_Filter_Hebel_25_10.md §9.6, vorab 65c5a2a9): CMC als eigene Messbasis.

    python -X utf8 Basisinfos/Rechenkern_02_10/p92_l1c_cmc_eigene_basis.py

Schritt 0  R-R11: A1 (p86, Top 30 oberes Fuenftel minus Gruppe, 1 M) auf CMC 2019-01..2026-08 nachrechnen; reproduziert, wenn Top 30
           Punktwert > 0 und Band ohne 0. Nur dann Teil 2 (vorab so festgelegt).
Teil 2     Bestaetigung 2017-01..2019-06 auf 7 T: Filter Top 30 & oberes Fuenftel gegen Top 30 gesamt, Nullpunkt aus 200 Zufallskoerben,
           Band zirkulaer Block 3 Wochen; SELBSTTEST vor dem ersten Blick (Fehlalarm <= 5 %, +0,5 Pp je Woche >= 80 %).
Wert, Universum, Klasse aus p89 (lade/merkmale/wert). Ausfaller aus den Top 200: Ertrag nach oben begrenzt durch
(Marktwert Rang 200 am Ende / eigener Marktwert am Start) - 1; Anteil und Rechnung ohne sie ausgewiesen.
Nur lesend.
"""
import os
import sqlite3
import sys

import numpy as np
import pandas as pd

HIER = os.path.dirname(os.path.abspath(__file__))
WURZEL = os.path.dirname(os.path.dirname(HIER))
sys.path.insert(0, os.path.join(WURZEL, "Basisinfos", "Spot_Voranalyse_04_10"))
sys.path.insert(0, HIER)
sys.path.insert(0, WURZEL)
os.chdir(WURZEL)
sys.stdout.reconfigure(encoding="utf-8")
import warnings  # noqa: E402

warnings.filterwarnings("ignore", category=RuntimeWarning)
import p86_a1_zerlegung as P86  # noqa: E402
import p89_l1_cmc as P89  # noqa: E402

RNG = np.random.default_rng(92)
B2_VON, B2_BIS = pd.Timestamp("2017-01-01"), pd.Timestamp("2019-06-30")
STAERKEN = (0.0025, 0.005, 0.01)
BLOCK_W = 3                                   # messnorm._block(7) = 21 T = 3 Wochen


class Basis:
    """Wert je Woche x Coin und Ertraege ueber k Wochen, mit Ausfaller-Regel."""

    def __init__(self):
        c = sqlite3.connect("file:data/_spot/o47_cm.db?mode=ro", uri=True)
        roh = pd.read_sql("SELECT stichtag, id, symbol, rang, preis, cap FROM cmc_woche", c, parse_dates=["stichtag"])
        c.close()
        self.wochen = np.sort(roh.stichtag.unique())
        self.cap200 = roh.groupby("stichtag").cap.min()
        b = roh[roh.symbol.str.upper() == "BTC"].set_index("stichtag").preis
        self.btc = b[~b.index.duplicated()]
        W = P89.merkmale(P89.lade())
        self.T = P89.wert(W).merge(W[["stichtag", "id", "preis", "cap"]], on=["stichtag", "id"])
        self.px = W.set_index(["stichtag", "id"]).preis
        self.px = self.px[~self.px.index.duplicated()]

    def ertrag(self, Z, k):
        """Z: Zeilen einer Woche (stichtag, id, preis, cap) -> Ertrag ueber k Wochen (begrenzt), Flag Ausfaller."""
        w = Z.stichtag.iloc[0]
        i = np.searchsorted(self.wochen, np.datetime64(w))
        if i + k >= len(self.wochen):
            return None, None
        we = self.wochen[i + k]
        ende = self.px.reindex(list(zip([pd.Timestamp(we)] * len(Z), Z.id))).to_numpy()
        aus = np.isnan(ende)
        r = np.where(aus, self.cap200.loc[we] / Z.cap.to_numpy() - 1, ende / Z.preis.to_numpy() - 1)
        return r, aus

    def btc_ertrag(self, w, k):
        i = np.searchsorted(self.wochen, np.datetime64(w))
        return self.btc.get(pd.Timestamp(self.wochen[i + k]), np.nan) / self.btc.get(pd.Timestamp(w), np.nan) - 1


def schritt0(B):
    """A1 auf CMC: Monatsstichtage 2019-01..2026-08, letzte CMC-Woche am oder vor dem Monatsersten, Ertrag 4 Wochen."""
    print("SCHRITT 0 (R-R11) A1 auf CMC nachrechnen: oberes Fuenftel minus Gruppe, 1 M (4 Wochen), Monatsstichtage 2019-01..2026-08, "
          "Band zirkulaer Block 3 Stichtage")
    stich = pd.date_range("2019-01-01", "2026-08-01", freq="MS")
    zeilen = {g: [] for g in ("Top 30", "Top 100", "Gesamt")}
    ausf, ohne = [], {g: [] for g in zeilen}
    for t in stich:
        i = np.searchsorted(B.wochen, np.datetime64(t), side="right") - 1
        Z = B.T[B.T.stichtag == B.wochen[i]]
        r, aus = B.ertrag(Z, 4)
        if r is None:
            continue
        Z = Z.assign(r=r, aus=aus)
        ausf.append(aus.mean())
        for g, m in (("Top 30", Z.kl == "H"), ("Top 100", Z.arang <= 100), ("Gesamt", np.ones(len(Z), bool))):
            G = Z[m]
            if len(G) < 5 or not (G.f == 5).any():
                continue
            zeilen[g].append(G.r[G.f == 5].mean() - G.r.mean())
            G2 = G[~G.aus]
            ohne[g].append(G2.r[G2.f == 5].mean() - G2.r.mean())
    a1 = {"Top 30": "+3,5 [+0,7; +7,5]", "Top 100": "+1,7 [-0,4; +4,2]", "Gesamt": "+1,5 [+0,3; +2,9]"}
    rep = False
    for g, d in zeilen.items():
        d = np.array(d)
        lo, hi = P86.band(d, 3)
        print("  %-8s %3d Stichtage %.0f Bloecke · F5 - Gruppe %+.1f Pp [%+.1f; %+.1f] · ohne Ausfaller %+.1f Pp · A1 (Binance) %s · AK %.2f" % (
            g, len(d), len(d) / 3, 100 * d.mean(), 100 * lo, 100 * hi, 100 * np.nanmean(ohne[g]), a1[g], P86.ak(d, 3)))
        if g == "Top 30":
            rep = d.mean() > 0 and lo > 0
    print("  Ausfaller aus den Top 200 binnen 4 Wochen: %.2f %% der Ertraege (begrenzt gerechnet)" % (100 * np.mean(ausf)))
    print("  -> %s\n" % ("REPRODUZIERT (Top 30 > 0, Band ohne 0) - weiter mit Teil 2" if rep else "NICHT REPRODUZIERT - keine Bestaetigung, Ursache und Loesung"))
    return rep


def wochen_tabelle(B, von, bis, k=1, klasse="H"):
    """je Woche: Ertraege der Klasse, Fuenftel, Ausfaller, BTC -> Liste von dicts."""
    out = []
    for w in B.wochen[(B.wochen >= np.datetime64(von)) & (B.wochen <= np.datetime64(bis))]:
        Z = B.T[(B.T.stichtag == w) & (B.T.kl == klasse)]
        if len(Z) < 10:
            continue
        r, aus = B.ertrag(Z, k)
        if r is None:
            continue
        out.append(dict(w=pd.Timestamp(w), r=r, f5=(Z.f == 5).to_numpy(), aus=aus, btc=B.btc_ertrag(w, k), ids=Z.id.to_numpy()))
    return out


def reihe(tab, maske_fn, delta=0.0):
    """Filter - Gruppe je Woche; maske_fn(woche) -> boolesche Maske des Filters; delta auf die Filtermitglieder gepflanzt."""
    d = []
    for x in tab:
        m = maske_fn(x)
        r = x["r"] + delta * m
        d.append(r[m].mean() - r.mean())
    return np.array(d)


def nullpunkt(tab, rng, n=200):
    v = []
    for x in tab:
        k = int(x["f5"].sum())
        if k == 0:
            continue
        s = np.array([x["r"][rng.choice(len(x["r"]), k, replace=False)].mean() for _ in range(n)])
        v.append(s.mean() - x["r"].mean())
    return float(np.mean(v))


def bandz(d, block, rng, n=2000):
    d = d[np.isfinite(d)]
    st = rng.integers(0, len(d), (n, int(np.ceil(len(d) / block))))
    ix = ((st[:, :, None] + np.arange(block)) % len(d)).reshape(n, -1)[:, :len(d)]
    m = d[ix].mean(1)
    return float(np.percentile(m, 2.5)), float(np.percentile(m, 97.5))


def zufallskorb(rng):
    def f(x):
        m = np.zeros(len(x["r"]), bool)
        m[rng.choice(len(m), int(x["f5"].sum()), replace=False)] = True
        return m
    return f


def stufe(d, np0, block, x, rng, n=2000):
    bl = np.isfinite(d).sum() / block
    lo, hi = bandz(d - np0, block, rng, n)
    if bl < 20:
        return lo, hi, "KEIN BEFUND"
    if lo > 0:
        return lo, hi, "TRAEGT"
    if x is not None and hi < x:
        return lo, hi, "TRAEGT NICHT BIS %.2f Pp je Woche" % (100 * x)
    return lo, hi, "NICHT TRENNBAR"


def teil2(B):
    tab = wochen_tabelle(B, B2_VON, B2_BIS)
    tab = [x for x in tab if x["f5"].any()]
    np0 = nullpunkt(tab, RNG)
    print("TEIL 2 Bestaetigung %s..%s auf 7 T · Top 30 (Klasse H) · %d Wochen = %.0f Bloecke a 3 Wochen · Filter im Mittel %.1f Coins · "
          "Nullpunkt (200 Zufallskoerbe) %+.3f Pp · Ausfaller %.2f %%" % (
              tab[0]["w"].date(), tab[-1]["w"].date(), len(tab), len(tab) / BLOCK_W, np.mean([x["f5"].sum() for x in tab]), 100 * np0,
              100 * np.mean(np.concatenate([x["aus"] for x in tab]))))
    # SELBSTTEST vor dem ersten Blick
    fa = np.mean([stufe(reihe(tab, zufallskorb(RNG)), np0, BLOCK_W, None, RNG, 500)[2] == "TRAEGT" for _ in range(200)])
    fund = {d: np.mean([stufe(reihe(tab, zufallskorb(RNG), d), np0, BLOCK_W, None, RNG, 500)[2] == "TRAEGT" for _ in range(100)])
            for d in STAERKEN}
    x = next((d for d in STAERKEN if fund[d] >= 0.8), None)
    ok = fa <= 0.05 and fund[0.005] >= 0.8
    print("  SELBSTTEST: Fehlalarm %.1f %% (Soll <= 5 %%) · Fund %s · Aufloesung X %s -> %s" % (
        100 * fa, " · ".join("%+.2f Pp %.0f %%" % (100 * d, 100 * f) for d, f in fund.items()),
        "%.2f Pp je Woche" % (100 * x) if x else "keine", "BESTANDEN" if ok else "NICHT BESTANDEN - echtes Ergebnis wird nicht angesehen"))
    if not ok:
        return
    d = reihe(tab, lambda x: x["f5"])
    lo, hi, st = stufe(d, np0, BLOCK_W, x, RNG)
    print("  (a) Filter - Top 30: %+.3f Pp je Woche · minus Nullpunkt %+.3f [%+.3f; %+.3f] · AK %.2f -> %s" % (
        100 * d.mean(), 100 * (d.mean() - np0), 100 * lo, 100 * hi, P86.ak(d, BLOCK_W), st))
    dohne = np.array([x["r"][x["f5"] & ~x["aus"]].mean() - x["r"][~x["aus"]].mean() for x in tab])
    print("      ohne Ausfaller: %+.3f Pp je Woche" % (100 * np.nanmean(dohne)))
    db = np.array([x["r"][x["f5"]].mean() - x["btc"] for x in tab])
    lo_b, hi_b = bandz(db, BLOCK_W, RNG)
    print("  (b) Filter - BTC (Auskunft gegen 0): %+.3f Pp je Woche [%+.3f; %+.3f] · Top 30 gesamt - BTC %+.3f" % (
        100 * np.nanmean(db), 100 * lo_b, 100 * hi_b, 100 * np.nanmean([x["r"].mean() - x["btc"] for x in tab])))
    return st, x, np0


def auskunft(B, x):
    print("\nAUSKUNFT (entscheidet nicht):")
    for name, von, bis, kl in (("2019-07..2026 (gesehen) Top 30", "2019-07-01", "2026-09-30", "H"),
                               ("2017-01..2019-06 Klasse M", B2_VON, B2_BIS, "M")):
        tab = [t for t in wochen_tabelle(B, von, bis, 1, kl) if t["f5"].any()]
        np0 = nullpunkt(tab, RNG, 100)
        d = reihe(tab, lambda t: t["f5"])
        lo, hi, st = stufe(d, np0, BLOCK_W, x, RNG)
        print("  %-32s %d Wochen · F5 - Gruppe %+.3f Pp je Woche · minus Nullpunkt [%+.3f; %+.3f] · %s" % (
            name, len(tab), 100 * d.mean(), 100 * lo, 100 * hi, st))
    tab = [t for t in wochen_tabelle(B, B2_VON, B2_BIS, 4, "H") if t["f5"].any()]
    d = reihe(tab, lambda t: t["f5"])
    print("  1 M (4 Wochen) 2017-01..2019-06 Top 30: F5 - Gruppe %+.1f Pp je Monat (Wochenstart, ueberlappend; %.0f Bloecke a 90 T -> KEIN BEFUND per Regel)" % (
        100 * d.mean(), len(tab) * 7 / 90))
    # Zombie-Pruefpunkt: Filtermitglieder 2017-19, die 52 Wochen spaeter nicht mehr in den Top 200 stehen
    tab = [t for t in wochen_tabelle(B, B2_VON, B2_BIS, 52, "H") if t["f5"].any()]
    z_f = np.mean(np.concatenate([t["aus"][t["f5"]] for t in tab]))
    z_g = np.mean(np.concatenate([t["aus"] for t in tab]))
    print("  Zombie-Pruefpunkt: nach 52 Wochen aus den Top 200 gefallen - Filter %.0f %% · Top 30 gesamt %.0f %%" % (100 * z_f, 100 * z_g))


def main():
    B = Basis()
    print("P92 MESSPLAN L1-c · CMC als eigene Messbasis · Wochen %s..%s\n" % (pd.Timestamp(B.wochen[0]).date(), pd.Timestamp(B.wochen[-1]).date()))
    if not schritt0(B):
        return 1
    r = teil2(B)
    if r is None:
        return 1
    auskunft(B, r[1])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
