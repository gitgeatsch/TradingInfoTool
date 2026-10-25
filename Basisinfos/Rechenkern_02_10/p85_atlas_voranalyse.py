"""P85 VORANALYSE VORSPRUNGS-ATLAS (25.10.2026, Nutzer: *"ja Voranalyse Vorsprungs-Atlas starten"*) - MACHBARKEIT und AUFLOESUNG.

    python -X utf8 Basisinfos/Rechenkern_02_10/p85_atlas_voranalyse.py

KEIN Blick auf den echten Effekt der Kombination (der kommt erst mit dem Messplan). Gerechnet wird:
 V1  R-R11 der Auswahl: Wert ohne F9 (B4-Regel) je Coin und Monatsstichtag ueber mk_messung.paare_mw(1) statt (365) - auf den
     gemeinsamen Stichtagen muss das Perzentil gleich sein, wo die Zelle gleich besetzt ist
 V2  Abdeckung: Anteil der REGEL0-Einstiege (Referenz 2024-26, Lauf B 2023) mit Wert am letzten Stichtag VOR dem Einstieg (kausal:
     Stichtag t gilt ab t + 1 Tag); Verteilung ueber Fuenftel, Klassen, Jahre
 V3  Aufloesung: Z1 (Ertrag minus Drift Coin-Jahr, ohne Kosten) fuer 24 h, 7 T, 30 T; 200 ZUFALLS-Einteilungen der Einstiege in
     Fuenftel JE COIN UND STICHTAG (gleiche Anteile wie echt) -> Streuung der Differenz 'oberes Fuenftel - alle' je Handel und je Tag; kleinster
     erkennbarer Unterschied (MDE, 80 % Fundquote, einseitig 5 %) = 2,5 x Streuung
Liest nur (data/ mode=ro ueber die Messmodule, data/_hist mode=ro); schreibt nur die Ausgabe.
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
os.chdir(WURZEL)
sys.stdout.reconfigure(encoding="utf-8")
import d4_wirkung as D4  # noqa: E402

MK, M, W = D4.MK, D4.M, D4.W
B0 = pd.Timestamp("2020-01-01")
HIST = os.path.join("data", "_hist")
HOR = {"24 h": 24, "7 T": 168, "30 T": 720}


def wert_tabelle(h):
    D = MK.paare_mw(h).reset_index(drop=True)
    Z = M.Zellen(D)
    F = M.merkmale(D)
    w = W.wert(Z, F, wahl=D4.OHNE_F9)
    p = M.pct_in_zelle(Z, w)
    T = D[["t", "sym", "kl"]].copy()
    T["p"] = p
    return T


class Kurse:
    def __init__(self):
        self.k = {}
        self.con = [sqlite3.connect("file:%s/%s?mode=ro" % (HIST.replace("\\", "/"), d), uri=True) for d in ("stundenkurse.db", "stundenkurse_alle.db")]

    def reihe(self, s):
        if s not in self.k:
            d = {}
            for c in self.con:
                for st, cl in c.execute("SELECT stunde, close FROM stundenkurse WHERE symbol=? AND stunde >= '2022-12-01'", (s,)):
                    d.setdefault(st, cl)
            if not d:
                self.k[s] = None
                return None
            hs = ((pd.to_datetime(list(d.keys())) - B0) / pd.Timedelta(hours=1)).astype(int).to_numpy()
            a = hs.min()
            C = np.full(hs.max() - a + 1, np.nan)
            C[hs - a] = np.array(list(d.values()), float)
            jahr = (B0 + pd.to_timedelta(a + np.arange(len(C)), unit="h")).year.to_numpy()
            aus = {}
            for name, hh in HOR.items():
                r = np.full(len(C), np.nan)
                r[:len(C) - hh] = C[hh:] / C[:-hh] - 1
                ok = np.isfinite(r)
                aus[name] = (r, {j: float(r[ok & (jahr == j)].mean()) for j in (2023, 2024, 2025, 2026) if (ok & (jahr == j)).any()})
            self.k[s] = (a, jahr, aus)
        return self.k[s]


def einstiege(pfad, T, K):
    E = pd.read_csv(pfad, sep=";")
    E["zeit"] = B0 + pd.to_timedelta(E.stunde, unit="h")
    tage = np.sort(T.t.unique())
    gilt = tage + np.timedelta64(1, "D")                           # Stichtag t gilt ab t + 1 Tag
    i = np.searchsorted(gilt, E.zeit.values, side="right") - 1
    E["t"] = pd.to_datetime(np.where(i >= 0, tage[np.maximum(i, 0)], np.datetime64("NaT")))
    E = E.merge(T, on=["t", "sym"] if "sym" in E else None, how="left") if False else E.merge(T.rename(columns={"sym": "symbol"}), on=["t", "symbol"], how="left")
    E["f"] = np.ceil(E.p * 5).clip(1, 5)
    E["tag"] = E.zeit.dt.normalize()
    for name, hh in HOR.items():
        z = []
        for s, st in zip(E.symbol, E.stunde):
            x = K.reihe(s)
            if x is None:
                z.append(np.nan)
                continue
            a, jahr, aus = x
            r, drift = aus[name]
            j = int(st) - a
            z.append(r[j] - drift[jahr[j]] if 0 <= j < len(r) and np.isfinite(r[j]) and jahr[j] in drift else np.nan)
        E["z_" + name] = z
    return E


def mde(E, name, rng, n=200):
    x = E[E.f.notna() & E["z_" + name].notna()].reset_index(drop=True)
    anteil = (x.f == 5).mean()
    w_tag = 1.0 / x.groupby("tag").tag.transform("size").to_numpy()
    z = x["z_" + name].to_numpy()
    d_h, d_t = [], []
    grp = x.groupby(["symbol", "t"]).ngroup().to_numpy()             # das Fuenftel gilt je Coin und Stichtag, nicht je Einstieg
    for _ in range(n):
        oben = (rng.random(grp.max() + 1) < anteil)[grp]
        d_h.append(z[oben].mean() - z.mean())
        d_t.append((w_tag[oben] * z[oben]).sum() / w_tag[oben].sum() - (w_tag * z).sum() / w_tag.sum())
    return len(x), int((x.f == 5).sum()), 2.5 * np.std(d_h), 2.5 * np.std(d_t)


def main():
    print("P85 VORANALYSE VORSPRUNGS-ATLAS\n")
    T1 = wert_tabelle(1)
    T365 = wert_tabelle(365)
    m = T365.merge(T1, on=["t", "sym"], suffixes=("_365", "_1"))
    gleich_kl = (m.kl_365 == m.kl_1).mean()
    beide = m.p_365.notna() & m.p_1.notna()
    gleich_p = (np.abs(m.p_365[beide] - m.p_1[beide]) < 1e-12).mean()
    print("V1 R-R11 Auswahl: Stichtage h=1 %s..%s (%d) gegen h=365 %s..%s (%d) · gemeinsame Anker %d · Klasse gleich %.1f %% · "
          "Perzentil gleich %.1f %% (beide mit Wert %d) · Anker nur in h=1 an gemeinsamen Stichtagen %d" % (
              T1.t.min().date(), T1.t.max().date(), T1.t.nunique(), T365.t.min().date(), T365.t.max().date(), T365.t.nunique(),
              len(m), 100 * gleich_kl, 100 * gleich_p, int(beide.sum()),
              int(len(T1[T1.t.isin(T365.t.unique())]) - len(m))))
    abw = m[beide & (np.abs(m.p_365 - m.p_1) >= 1e-12)]
    if len(abw):
        print("    abweichende Perzentile: %d, Median |Diff| %.3f, an %d Stichtagen" % (len(abw), float(np.median(np.abs(abw.p_365 - abw.p_1))), abw.t.nunique()))
    K = Kurse()
    rng = np.random.default_rng(85)
    for name, pfad in (("Referenz 2024-26", os.path.join("data", "_vergleich", "kern48jbz_einstiege_bestand.csv")),
                       ("Lauf B 2023", os.path.join(HIST, "einstiege_B.csv"))):
        E = einstiege(pfad, T1, K)
        print("\nV2 %s: %d Einstiege · mit Wert %d (%.0f %%) · ohne Stichtag %d · Fuenftel 1-5: %s · Klassen H/M/S: %s" % (
            name, len(E), int(E.f.notna().sum()), 100 * E.f.notna().mean(), int(E.t.isna().sum()),
            " / ".join(str(int((E.f == q).sum())) for q in (1, 2, 3, 4, 5)),
            " / ".join(str(int((E.kl == k).sum())) for k in ("H", "M", "S"))))
        print("    je Jahr mit Wert: %s · Tage mit Einstieg im oberen Fuenftel: %d" % (
            {int(j): int(g.f.notna().sum()) for j, g in E.groupby(E.zeit.dt.year)}, E[E.f == 5].tag.nunique()))
        ohne = E[E.f.isna()].symbol.value_counts().head(12)
        print("    haeufigste ohne Wert: %s" % ", ".join("%s %d" % (s, n) for s, n in ohne.items()))
        for hn in HOR:
            n, no, mh, mt = mde(E, hn, rng)
            erw = 12.1 * HOR[hn] / 24 / 365                      # belegte Dosis oberes Fuenftel E3 +12,1 Pp in 12 M (b4_vormessung SOLL), anteilig
            print("V3 %s %-4s: %d Einstiege, oberes Fuenftel %d · MDE 'oben - alle' je Handel %.2f Pp · je Tag %.2f Pp · erwarteter "
                  "Auswahl-Effekt, falls gleichmaessig ueber 12 M: %.2f Pp" % (name, hn, n, no, 100 * mh, 100 * mt, erw))


if __name__ == "__main__":
    main()
