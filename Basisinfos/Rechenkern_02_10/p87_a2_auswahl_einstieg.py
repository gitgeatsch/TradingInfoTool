"""P87 MESSPLAN A TEIL A2 (Voranalyse_Vorsprungs_Atlas_25_10.md §6.3, berichtigt §6.5; vorab a5825547/ec3f83e4/aec7f041):
Zusammenwirken Auswahl x Einstieg - laufen REGEL0-Einstiege im OBEREN Fuenftel der Watchlist-Ordnung besser als die uebrigen?

    python -X utf8 Basisinfos/Rechenkern_02_10/p87_a2_auswahl_einstieg.py

Z1 (24 h, ohne Kosten) = Ertrag minus Drift Coin-Jahr (wie p83/p85). D = Z1(Fuenftel 5) - Z1(Fuenftel 1-4), je Handel und je Tag.
FASSUNG 1b (§6.6, nach Selbsttest Fassung 1): je Tag = TAGESKLAMMER - an Tagen mit beiden Gruppen das Tagesmittel oben minus das
Tagesmittel der uebrigen, dann jeder dieser Tage gleich (Fassung 1 verglich verschiedene Tage: Nullpunkt +0,30 Pp, Fehlalarm 6 %,
Erkennung 65 %). Band/Rang ueber 15-Tage-Bloecke (messnorm._block(1) = 15), zirkulaer, 1.000 Ziehungen; Autokorrelation
beim Blockabstand <= 0,15 (pruefe_block); unter 20 Bloecken KEIN BEFUND. Nullpunkt = Mittel von 100 Zufallseinteilungen je Coin und
Stichtag. SELBSTTEST VOR DEM ERSTEN BLICK auf der Referenz: (a) Fehlalarm <= 5 %, (b) +0,5 Pp gepflanzt erkannt >= 80 %, je Gewichtung.
Urteil in den Stufen der Norm. Nur lesend.
"""
import os
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
import messnorm  # noqa: E402
import p85_atlas_voranalyse as P85  # noqa: E402

MK = P85.MK
BLOCK = messnorm._block(1)                                   # 15 Tage
ZIEH = 1000
RNG = np.random.default_rng(87)
WEGE = {"Referenz": os.path.join("data", "_vergleich", "kern48jbz_einstiege_bestand.csv"),
        "Lauf A (lang)": os.path.join("data", "_hist", "einstiege_A.csv"),
        "Lauf B 2023": os.path.join("data", "_hist", "einstiege_B.csv")}


class Tage:
    """Tagesaggregate einer Einstiegsmenge mit Gruppenzuordnung oben (bool) - fuer schnelle Bootstraps."""

    def __init__(self, E, z, oben):
        tag = pd.to_datetime(E.tag.values)
        self.tage = pd.date_range(tag.min(), tag.max(), freq="D")
        ti = ((tag - self.tage[0]) / pd.Timedelta(days=1)).astype(int).to_numpy()
        n = len(self.tage)
        self.ti, self.z, self.n = ti, z, n
        self.setze(oben)

    def setze(self, oben, plus=0.0):
        z = self.z + np.where(oben, plus, 0.0)
        o, r = oben, ~oben
        self.s5 = np.bincount(self.ti[o], weights=z[o], minlength=self.n)
        self.n5 = np.bincount(self.ti[o], minlength=self.n).astype(float)
        self.sR = np.bincount(self.ti[r], weights=z[r], minlength=self.n)
        self.nR = np.bincount(self.ti[r], minlength=self.n).astype(float)
        with np.errstate(invalid="ignore", divide="ignore"):
            self.m5 = np.where(self.n5 > 0, self.s5 / self.n5, np.nan)
            self.mR = np.where(self.nR > 0, self.sR / self.nR, np.nan)
        self.dd = self.m5 - self.mR          # FASSUNG 1b: TAGESKLAMMER - nur Tage mit beiden Gruppen, oben gegen uebrige am SELBEN Tag
        return self

    def d(self, ix=None):
        if ix is None:
            return (self.s5.sum() / self.n5.sum() - self.sR.sum() / self.nR.sum(), np.nanmean(self.dd))
        h = self.s5[ix].sum(axis=1) / self.n5[ix].sum(axis=1) - self.sR[ix].sum(axis=1) / self.nR[ix].sum(axis=1)
        t = np.nanmean(self.dd[ix], axis=1)
        return h, t

    def bloecke(self, zieh=ZIEH, rng=RNG):
        nb = int(np.ceil(self.n / BLOCK))
        st = rng.integers(0, self.n, (zieh, nb))
        return ((st[:, :, None] + np.arange(BLOCK)) % self.n).reshape(zieh, -1)[:, :self.n]

    def ak(self):
        x = np.nan_to_num(self.m5 - self.mR)
        a, b = x[:-BLOCK], x[BLOCK:]
        return float(np.corrcoef(a, b)[0, 1])


def zufall_oben(E, anteil, rng):
    g = E.groupby(["symbol", "t"]).ngroup().to_numpy()
    return (rng.random(g.max() + 1) < anteil)[g]


def urteil(rang, d, null, x_bis):
    if rang >= 0.95:
        return "TRAEGT"
    return "NICHT TRENNBAR" if d - null > x_bis else "TRAEGT NICHT BIS %.2f Pp" % (100 * x_bis)


def main():
    print("P87 MESSPLAN A · TEIL A2 ZUSAMMENWIRKEN AUSWAHL x EINSTIEG · Block %d Tage (messnorm._block(1))\n" % BLOCK)
    T1 = P85.wert_tabelle(1)
    K = P85.Kurse()
    E = {k: P85.einstiege(p, T1, K) for k, p in WEGE.items()}
    # R-R11: Z1 24 h der Referenz ueber alle Einstiege = p83 (+0,718 % je Handel)
    z_all = E["Referenz"]["z_24 h"]
    print("R-R11 Z1 24 h Referenz (alle %d Einstiege mit Kurs): %+.3f %% (p83 +0,718) -> %s" % (
        int(z_all.notna().sum()), 100 * z_all.mean(), "ok" if abs(100 * z_all.mean() - 0.718) < 0.001 else "ABWEICHUNG"))
    if abs(100 * z_all.mean() - 0.718) >= 0.001:
        return 1
    X = {k: e[e.f.notna() & e["z_24 h"].notna()].reset_index(drop=True) for k, e in E.items()}
    # ── SELBSTTEST VOR DEM ERSTEN BLICK (Referenz, 24 h) ─────────────────────────────────────────────────────────────────
    x = X["Referenz"]
    anteil = float((x.f == 5).mean())
    T = Tage(x, x["z_24 h"].to_numpy(), np.zeros(len(x), bool))
    ix = T.bloecke()
    null_h, null_t, fa_h, fa_t, er_h, er_t = [], [], 0, 0, 0, 0
    labels = [zufall_oben(x, anteil, RNG) for _ in range(100)]
    for o in labels:
        T.setze(o)
        h, t = T.d()
        null_h.append(h)
        null_t.append(t)
    nh, nt = float(np.mean(null_h)), float(np.mean(null_t))
    for o in labels:
        T.setze(o)
        bh, bt = T.d(ix)
        fa_h += np.mean(bh > nh) >= 0.95
        fa_t += np.mean(bt > nt) >= 0.95
        T.setze(o, plus=0.005)
        bh, bt = T.d(ix)
        er_h += np.mean(bh > nh) >= 0.95
        er_t += np.mean(bt > nt) >= 0.95
    ok_st = max(fa_h, fa_t) <= 5 and min(er_h, er_t) >= 80
    print("SELBSTTEST (Referenz, 24 h, 100 Zufallseinteilungen je Coin x Stichtag, Anteil oben %.1f %%): Nullpunkt je Handel %+.3f / je Tag "
          "%+.3f Pp · Fehlalarm %d %% / %d %% (Soll <= 5) · +0,5 Pp erkannt %d %% / %d %% (Soll >= 80) -> %s\n" % (
              100 * anteil, 100 * nh, 100 * nt, fa_h, fa_t, er_h, er_t, "BESTANDEN" if ok_st else "NICHT BESTANDEN"))
    if not ok_st:
        print("Selbsttest nicht bestanden - es wird NICHT gemessen (§6.3).")
        return 1
    # ── MESSUNG ──────────────────────────────────────────────────────────────────────────────────────────────────────────
    erg = {}
    for weg, x in X.items():
        anteil = float((x.f == 5).mean())
        oben = (x.f == 5).to_numpy()
        T = Tage(x, x["z_24 h"].to_numpy(), oben)
        nb = T.n / BLOCK
        a = T.ak()
        nh_, nt_ = [], []
        for _ in range(100):
            T.setze(zufall_oben(x, anteil, RNG))
            h, t = T.d()
            nh_.append(h)
            nt_.append(t)
        null = (float(np.mean(nh_)), float(np.mean(nt_)))
        T.setze(oben)
        d = T.d()
        bh, bt = T.d(T.bloecke())
        rang = (float(np.mean(bh > null[0])), float(np.mean(bt > null[1])))
        bandh, bandt = np.percentile(bh, [2.5, 97.5]), np.percentile(bt, [2.5, 97.5])
        kein = nb < 20 or abs(a) > 0.15
        u = ["KEIN BEFUND (%.0f Bloecke, AK %.2f)" % (nb, a) if kein else urteil(rang[i], d[i], null[i], 0.005) for i in (0, 1)]
        erg[weg] = (d, rang, u)
        print("%-14s %5d Einstiege (oben %d, %.1f %%) · %d Tage, %.0f Bloecke, AK %.2f" % (weg, len(x), int(oben.sum()), 100 * anteil, T.n, nb, a))
        print("   je Handel: D %+.3f Pp [%+.3f; %+.3f] · Nullpunkt %+.3f · Rang %.3f -> %s" % (
            100 * d[0], 100 * bandh[0], 100 * bandh[1], 100 * null[0], rang[0], u[0]))
        print("   je Tag   : D %+.3f Pp [%+.3f; %+.3f] · Nullpunkt %+.3f · Rang %.3f -> %s" % (
            100 * d[1], 100 * bandt[0], 100 * bandt[1], 100 * null[1], rang[1], u[1]))
    k1 = all(erg[w][1][i] >= 0.95 and erg[w][2][i] == "TRAEGT" for w in ("Referenz", "Lauf A (lang)") for i in (0, 1))
    k2 = all(erg["Lauf B 2023"][0][i] > 0 for i in (0, 1))
    print("\n-> URTEIL A2: %s (2024-26 beide Wege, beide Gewichtungen TRAEGT: %s · 2023 D > 0 in beiden Gewichtungen: %s)\n" % (
        "TRAEGT" if k1 and k2 else "TRAEGT NICHT (Stufen je Weg oben)", k1, k2))
    # ── AUSKUNFT ─────────────────────────────────────────────────────────────────────────────────────────────────────────
    rg = {t: MK.rang_mw(pd.Timestamp(t))[1] for t in T1.t.unique()}
    import agent.season_ampel as SA
    Z = pd.read_csv(os.path.join("data", "_spot", "am_kalibrierung.csv"), sep=";", parse_dates=["date"]).set_index("date")
    st = SA.geltend(SA.stufen(Z))
    print("AUSKUNFT (Punktwerte D = oben - uebrige, je Handel / je Tag, Pp; n oben):")
    for weg, x in X.items():
        x = x.copy()
        x["rang"] = [rg[t].get(s, np.nan) for t, s in zip(x.t, x.symbol)]
        x["stufe"] = [st.asof(z) if z >= st.index[0] and z <= st.index[-1] + pd.Timedelta(days=31) else None for z in x.zeit]
        zeilen = []
        for name, m in [("7 T", None), ("30 T", None), ("H", x.kl == "H"), ("M", x.kl == "M"), ("S", x.kl == "S"),
                        ("Top 30", x.rang <= 30), ("Top 50", x.rang <= 50), ("Top 100", x.rang <= 100)] + \
                       [("Jahr %d" % j, x.zeit.dt.year == j) for j in sorted(x.zeit.dt.year.unique())] + \
                       [("Ampel %s" % s, x.stufe == s) for s in sorted(x.stufe.dropna().unique())]:
            y = x if m is None else x[m]
            col = "z_" + name if name in ("7 T", "30 T") else "z_24 h"
            y = y[y[col].notna()]
            o = (y.f == 5).to_numpy()
            if o.sum() < 20 or (~o).sum() < 20:
                zeilen.append("%s zu wenige" % name)
                continue
            Tt = Tage(y, y[col].to_numpy(), o)
            h, t = Tt.d()
            zeilen.append("%s %+.2f/%+.2f (%d)" % (name, 100 * h, 100 * t, int(o.sum())))
        print("  %-14s %s" % (weg, " · ".join(zeilen)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
