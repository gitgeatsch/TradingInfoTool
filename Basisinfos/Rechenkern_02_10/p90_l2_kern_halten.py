"""P90 MESSPLAN L-2 (Voranalyse_L1_L2_Asset_Filter_Hebel_25_10.md §8.0/§8.2, vorab 43772659): RegelXY Hebel - REGEL0 auf dem Kern
(BTC, ETH, SOL), Haltedauer 24 / 72 / 168 h, netto nach Bitpanda-Kosten (0,30 % + 0,18 % je Tag).

    python -X utf8 Basisinfos/Rechenkern_02_10/p90_l2_kern_halten.py

(i)  netto je Handel und je Tag (Tagesmittel, jeder Tag gleich) - Bezug 0
(ii) Vorsprung gegen Zufallsstunden derselben Coins im selben Jahr (Ertrag H minus Drift H Coin-Jahr) - Bezug Nullpunkt (100 Zufallsmengen)
TRAEGT nur, wenn (i) ueber 0 und (ii) ueber dem Nullpunkt, je Handel und je Tag, auf beiden Einstiegswegen 2024-26.
Norm: Block messnorm._block(H in Tagen) = 15/15/21 T, zirkulaer, 1.000 Ziehungen; >= 20 Bloecke, Autokorrelation <= 0,15; Stufen.
SELBSTTEST VOR DEM ERSTEN BLICK je H: 100 Zufallsmengen (Zufallsstunden der Kern-Coins, gleiche Zahl je Coin und Jahr) -> Fehlalarm von
(ii) <= 5 %. FASSUNG 1b (§8.5): Aufloesungskurve 0,5/1/2/3 Pp, Grenze X = kleinste Staerke mit >= 80 % je Gewichtung (Fassung 1 mit fester
+1,0 Pp scheiterte bei 72/168 h an der Aufloesung, nicht am Fehlalarm). Nur lesend.
"""
import os
import sqlite3
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

KERN = ("BTC", "ETH", "SOL")
HS = {"24 h": 24, "72 h": 72, "168 h": 168}
B0 = pd.Timestamp("2020-01-01")
RNG = np.random.default_rng(90)
WEGE = {"Referenz": os.path.join("data", "_vergleich", "kern48jbz_einstiege_bestand.csv"),
        "Lauf A (lang)": os.path.join("data", "_hist", "einstiege_A.csv"),
        "Lauf B 2023": os.path.join("data", "_hist", "einstiege_B.csv")}


def kosten(h):
    return 0.0030 + 0.0018 * h / 24


class Reihe:
    def __init__(self, s):
        c = sqlite3.connect("file:data/_hist/stundenkurse.db?mode=ro", uri=True)
        d = pd.read_sql("SELECT stunde, low, close FROM stundenkurse WHERE symbol=? AND stunde >= '2022-12-01'", c, params=(s,))
        c.close()
        hs = ((pd.to_datetime(d.stunde) - B0) / pd.Timedelta(hours=1)).astype(int).to_numpy()
        self.a = hs.min()
        n = hs.max() - self.a + 1
        self.C = np.full(n, np.nan)
        self.L = np.full(n, np.nan)
        self.C[hs - self.a] = d.close.values
        self.L[hs - self.a] = d.low.values
        self.jahr = (B0 + pd.to_timedelta(self.a + np.arange(n), unit="h")).year.to_numpy()
        self.r, self.tief, self.drift, self.ok = {}, {}, {}, {}
        for name, h in HS.items():
            r = np.full(n, np.nan)
            r[:n - h] = self.C[h:] / self.C[:-h] - 1
            from numpy.lib.stride_tricks import sliding_window_view
            t = np.full(n, np.nan)
            w = sliding_window_view(self.L[1:], h)                 # Tief in (t, t+h]
            t[:len(w)] = np.nanmin(w, axis=1) / self.C[:len(w)] - 1
            ok = np.isfinite(r)
            self.r[name], self.tief[name], self.ok[name] = r, t, ok
            self.drift[name] = {j: float(r[ok & (self.jahr == j)].mean()) for j in (2023, 2024, 2025, 2026) if (ok & (self.jahr == j)).any()}


def daten(E, R, name):
    """-> DataFrame je Einstieg: tag, netto, z (Vorsprung gg. Drift), tief"""
    z = []
    for s, st in zip(E.symbol, E.stunde):
        x = R[s]
        i = int(st) - x.a
        if 0 <= i < len(x.C) and x.ok[name][i] and x.jahr[i] in x.drift[name]:
            r = x.r[name][i]
            z.append(((B0 + pd.Timedelta(hours=int(st))).normalize(), s, int(x.jahr[i]), r - kosten(HS[name]), r - x.drift[name][x.jahr[i]], x.tief[name][i]))
    return pd.DataFrame(z, columns=["tag", "symbol", "jahr", "netto", "z", "tief"])


def zufall(E, R, name, rng):
    z = []
    for (s, j), g in E.groupby(["symbol", "jahr"]):
        x = R[s]
        kand = np.flatnonzero(x.ok[name] & (x.jahr == j))
        if not len(kand):
            continue
        for i in rng.choice(kand, len(g)):
            r = x.r[name][i]
            z.append(((B0 + pd.Timedelta(hours=int(i + x.a))).normalize(), s, j, r - kosten(HS[name]), r - x.drift[name][j], x.tief[name][i]))
    return pd.DataFrame(z, columns=["tag", "symbol", "jahr", "netto", "z", "tief"])


class Tage:
    def __init__(self, X, spalte, plus=0.0):
        self.tage = pd.date_range(X.tag.min(), X.tag.max(), freq="D")
        ti = ((X.tag - self.tage[0]).dt.days).to_numpy()
        v = X[spalte].to_numpy() + plus
        self.n = len(self.tage)
        self.s = np.bincount(ti, weights=v, minlength=self.n)
        self.k = np.bincount(ti, minlength=self.n).astype(float)
        self.m = np.where(self.k > 0, self.s / np.maximum(self.k, 1), np.nan)

    def wert(self):
        return self.s.sum() / self.k.sum(), np.nanmean(self.m)

    def boot(self, block, zieh=1000, rng=RNG):
        nb = int(np.ceil(self.n / block))
        st = rng.integers(0, self.n, (zieh, nb))
        ix = ((st[:, :, None] + np.arange(block)) % self.n).reshape(zieh, -1)[:, :self.n]
        return self.s[ix].sum(axis=1) / np.maximum(self.k[ix].sum(axis=1), 1), np.nanmean(self.m[ix], axis=1)

    def ak(self, block):
        x = np.nan_to_num(self.m - np.nanmean(self.m))
        return float(np.corrcoef(x[:-block], x[block:])[0, 1])


def main():
    print("P90 MESSPLAN L-2 · RegelXY Hebel: REGEL0 auf BTC/ETH/SOL, Haltedauer 24/72/168 h, netto Bitpanda\n")
    R = {s: Reihe(s) for s in KERN}
    E = {}
    for weg, p in WEGE.items():
        e = pd.read_csv(p, sep=";")
        e = e[e.symbol.isin(KERN)].copy()
        e["jahr"] = (B0 + pd.to_timedelta(e.stunde, unit="h")).dt.year
        E[weg] = e[e.jahr >= (2024 if weg != "Lauf B 2023" else 2023)]
    # ── SELBSTTEST VOR DEM ERSTEN BLICK (Referenz, je H) ─────────────────────────────────────────────────────────────────
    ok_alle = True
    X_BIS = {}
    STAERKEN = (0.005, 0.01, 0.02, 0.03)                    # FASSUNG 1b (§8.5): Aufloesungskurve statt fester +1,0 Pp
    for name, h in HS.items():
        block = messnorm._block(max(1, h // 24))
        mengen = [zufall(E["Referenz"], R, name, RNG) for _ in range(100)]
        null = np.mean([Tage(x, "z").wert() for x in mengen], axis=0)
        fa = np.zeros(2)
        er = {st: np.zeros(2) for st in STAERKEN}
        for x in mengen:
            b = Tage(x, "z").boot(block, 300)
            fa += [np.mean(b[0] > null[0]) >= 0.95, np.mean(b[1] > null[1]) >= 0.95]
            for st in STAERKEN:
                b = Tage(x, "z", plus=st).boot(block, 300)
                er[st] += [np.mean(b[0] > null[0]) >= 0.95, np.mean(b[1] > null[1]) >= 0.95]
        gefunden = [st for st in STAERKEN if er[st].min() >= 80]
        X_BIS[name] = gefunden[0] if gefunden else None
        ok = fa.max() <= 5 and X_BIS[name] is not None
        ok_alle &= ok
        print("SELBSTTEST %-5s (Block %d T): Nullpunkt (ii) %+.3f / %+.3f Pp · Fehlalarm %d %% / %d %% (Soll <= 5) · Aufloesungskurve erkannt %s · "
              "Grenze X = %s -> %s" % (name, block, 100 * null[0], 100 * null[1], fa[0], fa[1],
                                       " ".join("%.1f Pp %d/%d %%" % (100 * st, er[st][0], er[st][1]) for st in STAERKEN),
                                       ("%.1f Pp" % (100 * X_BIS[name])) if X_BIS[name] else "keine", "bestanden" if ok else "NICHT BESTANDEN"))
    if not ok_alle:
        print("\nSelbsttest nicht bestanden - es wird NICHT gemessen (§8.2); Ursache und Loesung folgen.")
        return 1
    print()
    # ── MESSUNG ──────────────────────────────────────────────────────────────────────────────────────────────────────────
    urteile = {}
    for weg, e in E.items():
        print("%s: %d Kern-Einstiege (BTC %d, ETH %d, SOL %d)" % (weg, len(e), (e.symbol == "BTC").sum(), (e.symbol == "ETH").sum(), (e.symbol == "SOL").sum()))
        basis = None
        for name, h in HS.items():
            block = messnorm._block(max(1, h // 24))
            X = daten(e, R, name)
            if name == "24 h":
                basis = X.set_index(["tag", "symbol"]).netto
            null = np.mean([Tage(x, "z").wert() for x in (zufall(e, R, name, RNG) for _ in range(100))], axis=0)
            Tn, Tz = Tage(X, "netto"), Tage(X, "z")
            nb = Tn.n / block
            a = Tn.ak(block)
            wn, wz = Tn.wert(), Tz.wert()
            bn, bz = Tn.boot(block), Tz.boot(block)
            r_n = [float(np.mean(bn[i] > 0)) for i in (0, 1)]
            r_z = [float(np.mean(bz[i] > null[i])) for i in (0, 1)]
            kein = nb < 20 or abs(a) > 0.15
            traegt = (not kein) and min(r_n) >= 0.95 and min(r_z) >= 0.95
            stufe = "KEIN BEFUND (%.0f Bloecke, AK %.2f)" % (nb, a) if kein else ("TRAEGT" if traegt else (
                "NICHT TRENNBAR" if max(wz) - max(null) > X_BIS[name] else "TRAEGT NICHT BIS %.1f Pp" % (100 * X_BIS[name])))
            urteile[(weg, name)] = traegt
            gep = X.set_index(["tag", "symbol"]).netto - basis.reindex(X.set_index(["tag", "symbol"]).index)
            liq = " · ".join("%dx %.1f %%" % (k, 100 * np.mean(X.tief <= -g)) for k, g in ((2, 0.50), (3, 0.33), (5, 0.20)))
            print("   %-6s netto je Handel %+.2f %% [%+.2f; %+.2f] / je Tag %+.2f %% [%+.2f; %+.2f] · Vorsprung %+.2f / %+.2f Pp (Nullpunkt %+.2f / %+.2f, "
                  "Rang %.2f / %.2f) · %.0f Bl. AK %.2f -> %s" % (
                      name, 100 * wn[0], 100 * np.percentile(bn[0], 2.5), 100 * np.percentile(bn[0], 97.5), 100 * wn[1],
                      100 * np.percentile(bn[1], 2.5), 100 * np.percentile(bn[1], 97.5), 100 * wz[0], 100 * wz[1], 100 * null[0], 100 * null[1],
                      r_z[0], r_z[1], nb, a, stufe))
            print("          Auskunft: gepaart gegen 24 h %+.2f Pp · Liquidationsnaehe (Tief binnen H) %s · je Coin netto %s · je Jahr netto %s" % (
                100 * np.nanmean(gep), liq, " ".join("%s %+.2f" % (s, 100 * g.netto.mean()) for s, g in X.groupby("symbol")),
                " ".join("%d %+.2f" % (j, 100 * g.netto.mean()) for j, g in X.groupby("jahr"))))
        print()
    for name in HS:
        t = urteile.get(("Referenz", name)) and urteile.get(("Lauf A (lang)", name))
        print("-> URTEIL L-2 %-6s: %s" % (name, "TRAEGT (beide Wege)" if t else "TRAEGT NICHT (Stufen oben)"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
