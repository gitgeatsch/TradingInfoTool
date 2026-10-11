"""B4-VORMESSUNG (Spot §43, vorab Commit ae32455) - unteres Fuenftel (Wert ohne F9) gegen BESTAENDIGE Nullwelt, Dollar-Ertrag 12 M. Nur lesend.

    python Basisinfos/Spot_Voranalyse_04_10/b4_vormessung.py

  Teil 0  Dosis ohne F9 wie §39.9 (+-0,15 Pp), sonst Abbruch
  Haupt   Abstand = Mittel(Dollar-Ertrag unteres Fuenftel) - Mittel(Zelle), Stichtag nach Coinzahl gewichtet, Epoche = Mittel der Stichtage;
          Nullwelt beständig: je Ziehung eine Zufallszahl je Coin, gleich ueber alle Stichtage, gleich viele Coins je Zelle; 200 Ziehungen
  Urteil  E3: SCHLECHTER (Abstand < 0, Rang <= 0,025) / BESSER (> 0, Rang >= 0,975) / nicht entscheidbar
  Selbsttest (a) 100 bestaendige Zufallswerte, Fehlalarm <= 5 %; (b) gepflanzt 0,3 x Perzentil(Ertrag) + N(0,1) -> SCHLECHTER
  Auskunft und Teil G siehe §43.2
"""
import os
import sys

import numpy as np
import pandas as pd

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HIER)
os.chdir(os.path.dirname(os.path.dirname(HIER)))
import d4_wirkung as D4  # noqa: E402

MK, M, W = D4.MK, D4.M, D4.W
RNG = np.random.default_rng(20261043)
SOLL = {"E2": [-7.3, -3.2, -0.1, 1.0, 9.2], "E3": [-17.2, -4.7, 3.0, 6.0, 12.1]}
UEBERNOMMEN = ["AIOZ", "AKT", "BRETT", "CAT", "GRIFFAIN", "HYPE", "KAS", "MORPHO", "PLUME", "SUPRA"]


class Rechner:
    """Zellen mit Wert; Auswahl je Zelle = unteres Fuenftel (Perzentil <= 0,2) eines Werts unter den Coins mit Wert."""

    def __init__(self, D, p, y):
        self.D, self.y = D, y
        self.code = pd.factorize(D.sym)[0]
        self.nsym = self.code.max() + 1
        self.zellen = []
        for (t, k), ix in D.groupby(["t", "kl"]).groups.items():
            ix = np.array(ix)
            m = ix[~np.isnan(p[ix])]
            if len(m) >= 10:
                self.zellen.append((t, k, m))
        self.ep = {t: M.A.epoche(t) for t in D.t.unique()}

    def unten(self, f, m):
        r = pd.Series(f[m]).rank(pct=True).values
        return m[r <= 0.2]

    def abstand(self, f, ep, y=None, wahl=None, mittel=np.mean):
        y = self.y if y is None else y
        v, n = {}, {}
        for t, k, m in self.zellen:
            if self.ep[t] != ep:
                continue
            q = self.unten(f, m) if wahl is None else wahl(t, k, m)
            if not len(q):
                continue
            d = mittel(y[q]) - mittel(y[m])
            v[t] = v.get(t, 0) + d * len(m)
            n[t] = n.get(t, 0) + len(m)
        return float(np.mean([v[t] / n[t] for t in n])) if n else np.nan

    def null(self, f, ep, nz, rng):
        """bestaendige Nullwelt: je Ziehung eine Zufallszahl je Coin; je Zelle gleich viele Coins wie die echte Auswahl."""
        anz = {(t, k): len(self.unten(f, m)) for t, k, m in self.zellen if self.ep[t] == ep}
        out = []
        for _ in range(nz):
            R = rng.random(self.nsym)
            out.append(self.abstand(None, ep, wahl=lambda t, k, m: m[np.argsort(R[self.code[m]])[:anz[(t, k)]]]))
        return np.array(out)

    def null_einfach(self, f, ep, nz, rng):
        anz = {(t, k): len(self.unten(f, m)) for t, k, m in self.zellen if self.ep[t] == ep}
        return np.array([self.abstand(None, ep, wahl=lambda t, k, m: rng.choice(m, anz[(t, k)], replace=False)) for _ in range(nz)])


def urteil(a, rang):
    if a < 0 and rang <= 0.025:
        return "SCHLECHTER"
    if a > 0 and rang >= 0.975:
        return "BESSER"
    return "nicht entscheidbar"


def main():
    D = MK.paare_mw(365).reset_index(drop=True)
    Z = M.Zellen(D)
    F = M.merkmale(D)
    w9 = W.wert(Z, F, wahl=D4.OHNE_F9)
    print("B4-VORMESSUNG (§43) · Kurse bis %s · Anker %d\n" % (MK.ENDE.date(), len(D)))
    ok = True
    for ep in ("E2", "E3"):
        d = D4.dosis(Z, w9, ep)
        ok &= all(abs(a - b) <= 0.15 for a, b in zip(d, SOLL[ep]))
        print("TEIL 0 Dosis %s ohne F9: %s (Soll %s)" % (ep, " ".join("%+5.1f" % x for x in d), " ".join("%+5.1f" % x for x in SOLL[ep])))
    if not ok:
        print("TEIL 0 FEHLGESCHLAGEN - Abbruch")
        return
    print("-> Teil 0 bestanden\n")
    p = M.pct_in_zelle(Z, w9)
    y = D.ende.values - 1.0
    R = Rechner(D, p, y)

    # Selbsttest
    fa = 0
    for i in range(100):
        g = RNG.random(R.nsym)[R.code]
        g = np.where(np.isnan(p), np.nan, g)
        a = R.abstand(g, "E3")
        nl = R.null(g, "E3", 40, RNG)
        fa += urteil(a, float(np.mean(nl < a))) != "nicht entscheidbar"
    pp = np.full(len(D), np.nan)
    for t, k, m in R.zellen:
        pp[m] = pd.Series(y[m]).rank(pct=True).values
    gp = np.where(np.isnan(p), np.nan, 0.3 * pp + RNG.normal(size=len(D)))
    ag = R.abstand(gp, "E3")
    ug = urteil(ag, float(np.mean(R.null(gp, "E3", 40, RNG) < ag)))
    st_ok = fa <= 5 and ug == "SCHLECHTER"
    print("SELBSTTEST (a) Fehlalarm %d von 100 bestaendigen Zufallswerten (Soll <= 5) · (b) gepflanzt: Abstand %+.1f Pp -> %s  =>  %s\n" % (
        fa, 100 * ag, ug, "bestanden - das Urteil gilt" if st_ok else "NICHT bestanden - das Urteil gilt NICHT"))

    for ep in ("E3", "E2"):
        a = R.abstand(p, ep)
        nl = R.null(p, ep, 200, RNG)
        rang = float(np.mean(nl < a))
        ne = R.null_einfach(p, ep, 200, RNG)
        tage = sorted({t for t, k, m in R.zellen if R.ep[t] == ep})
        n_u = sum(len(R.unten(p, m)) for t, k, m in R.zellen if R.ep[t] == ep)
        print("%s %s: Stichtage %d (%s bis %s) · Anker unteres Fuenftel %d" % (
            "HAUPT" if ep == "E3" else "AUSKUNFT", ep, len(tage), tage[0].date(), tage[-1].date(), n_u))
        print("   Abstand Dollar-Ertrag 12 M unteres Fuenftel - Zelle: %+.2f Pp · bestaendige Nullwelt Mittel %+.2f, 2,5./97,5. Perz. %+.2f / %+.2f · Rang %.3f  ->  %s%s" % (
            100 * a, 100 * nl.mean(), 100 * np.percentile(nl, 2.5), 100 * np.percentile(nl, 97.5), rang, urteil(a, rang),
            "" if ep == "E3" else " (nur Auskunft)"))
        print("   einfache Nullwelt (je Monat, Vergleich): 2,5./97,5. Perz. %+.2f / %+.2f · Rang %.3f" % (
            100 * np.percentile(ne, 2.5), 100 * np.percentile(ne, 97.5), float(np.mean(ne < a))))
        # Auskunft
        abs_u = {}
        for t, k, m in R.zellen:
            if R.ep[t] == ep:
                q = R.unten(p, m)
                abs_u.setdefault(t, []).append((y[q].mean(), y[m].mean(), len(m)))
        au = np.mean([np.average([x[0] for x in v], weights=[x[2] for x in v]) for v in abs_u.values()])
        az = np.mean([np.average([x[1] for x in v], weights=[x[2] for x in v]) for v in abs_u.values()])
        yb = D.ende.values / D.ende_b.values - 1
        ye = np.where(D.eing.values, -1.0, y)
        print("   Auskunft: absolut unteres Fuenftel %+.1f %% / Zelle %+.1f %% · gegen BTC Abstand %+.2f Pp · Median-Abstand %+.2f Pp · eingestellt = -100 %%: %+.2f Pp" % (
            100 * au, 100 * az, 100 * R.abstand(p, ep, y=yb), 100 * R.abstand(p, ep, mittel=np.median), 100 * R.abstand(p, ep, y=ye)))
        kl = []
        for k in ("H", "M", "S"):
            sub = Rechner.__new__(Rechner)
            sub.__dict__.update(R.__dict__)
            sub.zellen = [z for z in R.zellen if z[1] == k]
            kl.append("%s %+.1f" % (k, 100 * sub.abstand(p, ep)))
        jahre = []
        for j in sorted({t.year for t in tage}):
            sub = Rechner.__new__(Rechner)
            sub.__dict__.update(R.__dict__)
            sub.zellen = [z for z in R.zellen if z[0].year == j]
            jahre.append("%d %+.1f" % (j, 100 * sub.abstand(p, ep)))
        print("   je Klasse (Pp): %s · je Jahr (Pp): %s · Saldo unteres Fuenftel %+.1f Pp\n" % (
            " · ".join(kl), " · ".join(jahre), D4.dosis(Z, w9, ep)[0]))

    # Teil G
    maske = ~D.sym.isin(UEBERNOMMEN).values
    DG = D[maske].reset_index(drop=True)
    ZG = M.Zellen(DG)
    FG = {k: v[maske] for k, v in F.items()}
    pG = M.pct_in_zelle(ZG, W.wert(ZG, FG, wahl=D4.OHNE_F9))
    q0, qG = D4.fuenftel(p[maske]), D4.fuenftel(pG)
    e3 = (DG.ep.values == "E3") & ~np.isnan(q0) & ~np.isnan(qG)
    print("TEIL G (Auskunft) Universum OHNE die 10 uebernommenen Reihen, E3: Anker %d · anderes Fuenftel %.1f %% · unteres Fuenftel %d: verlassen %d, neu %d" % (
        e3.sum(), 100 * np.mean(q0[e3] != qG[e3]), (e3 & (q0 == 1)).sum(), (e3 & (q0 == 1) & (qG != 1)).sum(), (e3 & (qG == 1) & (q0 != 1)).sum()))
    pd.DataFrame(dict(t=D.t, sym=D.sym, kl=D.kl, ep=D.ep, p9=p, ende=D.ende, ende_b=D.ende_b, eing=D.eing)).to_csv(
        os.path.join("data", "_spot", "b4_vormessung.csv"), sep=";", index=False)


if __name__ == "__main__":
    main()
