"""P92c URSACHE L1-c zu Ende (Voranalyse_L1_L2 §9.8, vorab 876072ce): an welcher Abgrenzung haengt der A1-Vorsprung der Top 30?

    python -X utf8 Basisinfos/Rechenkern_02_10/p92c_ursache_abgrenzung.py

Ausgang A1 (p86.anker(30): Binance 30 T, Gruppe rang_mw <= 30, Binance-Fuenftel). Je EINE Sache in Richtung CMC getauscht:
V1 Menge (nur Coins auch in den CMC Top 200 der Woche) · V2 Gruppe (CMC-Rang <= 30 = Klasse H) · V3 Ertrag (CMC 4 Wochen) · V4 Gruppe + Ertrag.
KORREKTUR nach dem ersten Lauf (§9.9): V3/V4 starten an der CMC-Woche VOR dem Stichtag (bis 6 T Ueberlapp mit der Information des
Binance-Werts) -> V3b/V4b ab der ersten CMC-Woche NACH dem Stichtag. Fehlt ein Coin dort, bleibt er weg (V1-Menge gilt fuer r_c).
Groesse je Stichtag oberes Fuenftel - Gruppe, Band p86.band (Block 3 Stichtage). Gegenprobe V0/V4 ueber eine eigene Schleife.
Nur lesend.
"""
import os
import sys

import numpy as np
import pandas as pd

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HIER)
import p92_l1c_cmc_eigene_basis as P92  # noqa: E402  (setzt Pfad und Arbeitsordner)

import p85_atlas_voranalyse as P85  # noqa: E402

P86 = P92.P86


def tabelle():
    B = P92.Basis()
    D = P86.anker(30, P85.wert_tabelle(1))
    D = D[(D.t >= "2019-01-01") & (D.t <= "2026-08-01") & D.r.notna()].copy()
    teile = []
    for t, g in D.groupby("t"):
        i = np.searchsorted(B.wochen, np.datetime64(t), side="right") - 1
        Z = B.T[B.T.stichtag == B.wochen[i]]
        Z = Z[~Z.symbol.duplicated(keep=False)]
        r, aus = B.ertrag(Z, 4)
        c = pd.DataFrame({"sym": Z.symbol.to_numpy(), "h_c": (Z.kl == "H").to_numpy(), "r_c": r if r is not None else np.nan})
        # KORREKTUR 26.10. (nach dem ersten Lauf, §9.9): r_c beginnt an der CMC-Woche AM ODER VOR dem Stichtag - bis 6 T, die der
        # Binance-Wert schon kennt. r_c2 beginnt an der ersten CMC-Woche NACH dem Stichtag (kein Ueberlapp mit der Information).
        j = np.searchsorted(B.wochen, np.datetime64(t), side="right")
        Z2 = B.T[B.T.stichtag == B.wochen[j]]
        Z2 = Z2[~Z2.symbol.duplicated(keep=False)]
        r2, _ = B.ertrag(Z2, 4)
        c = c.merge(pd.DataFrame({"sym": Z2.symbol.to_numpy(), "r_c2": r2 if r2 is not None else np.nan}), on="sym", how="left")
        teile.append(g.merge(c, on="sym", how="left"))
    X = pd.concat(teile, ignore_index=True)
    X["in_cmc"] = X.r_c.notna()
    return X


VARIANTEN = {
    "V0 A1":               dict(menge=False, gruppe="rang", ertrag="r"),
    "V1 Menge":            dict(menge=True, gruppe="rang", ertrag="r"),
    "V2 Gruppe":           dict(menge=True, gruppe="cmc", ertrag="r"),
    "V3 Ertrag":           dict(menge=True, gruppe="rang", ertrag="r_c"),
    "V4 Gruppe + Ertrag":  dict(menge=True, gruppe="cmc", ertrag="r_c"),
    "V3b Ertrag nach t":   dict(menge=True, gruppe="rang", ertrag="r_c2"),
    "V4b Gruppe + Ertr. b": dict(menge=True, gruppe="cmc", ertrag="r_c2"),
}


def reihe(X, v):
    Y = X[X.in_cmc] if v["menge"] else X
    m = (Y.rang <= 30) if v["gruppe"] == "rang" else Y.h_c.astype(bool)
    Y = Y[m]
    d, n, nf = [], [], []
    for t, g in Y.groupby("t"):
        if len(g) < 5 or not (g.f == 5).any():
            continue
        d.append(g[v["ertrag"]][g.f == 5].mean() - g[v["ertrag"]].mean())
        n.append(len(g)); nf.append(int((g.f == 5).sum()))
    return np.array(d), np.mean(n), np.mean(nf)


def gegenprobe(X, v):
    """eigene Schleife: Stichtag fuer Stichtag, Zeile fuer Zeile."""
    werte = []
    for t in sorted(X.t.unique()):
        summe_f = summe_g = 0.0
        k_f = k_g = 0
        for _, z in X[X.t == t].iterrows():
            if v["menge"] and not z.in_cmc:
                continue
            drin = (z.rang <= 30) if v["gruppe"] == "rang" else bool(z.h_c)
            if not drin:
                continue
            w = z[v["ertrag"]]
            if w != w:                                    # kein Ertrag (Coin fehlt in der Folgewoche) - wie pandas.mean
                continue
            summe_g += w; k_g += 1
            if z.f == 5:
                summe_f += w; k_f += 1
        if k_g >= 5 and k_f:
            werte.append(summe_f / k_f - summe_g / k_g)
    return float(np.mean(werte))


def gruppen_unterschied(X):
    """Auskunft: welche Coins stehen in der einen Top-30-Gruppe und nicht in der anderen (gemeinsame Menge)?"""
    Y = X[X.in_cmc]
    nur_rang = Y[(Y.rang <= 30) & ~Y.h_c.astype(bool)]
    nur_cmc = Y[(Y.rang > 30) & Y.h_c.astype(bool)]
    for name, Z in (("nur in rang_mw <= 30", nur_rang), ("nur in CMC-Rang <= 30", nur_cmc)):
        h = Z.sym.value_counts().head(12)
        print("  %-22s %.1f je Stichtag · F5-Anteil %.0f %% · mittlerer Ertrag 1 M %+.1f %% (Gruppe V0 %+.1f %%) · haeufig: %s" % (
            name, len(Z) / X.t.nunique(), 100 * (Z.f == 5).mean(), 100 * Z.r.mean(), 100 * Y[Y.rang <= 30].r.mean(),
            ", ".join("%s %d" % (k, v) for k, v in h.items())))


def main():
    X = tabelle()
    print("P92c URSACHE L1-c · A1-Anker 1 M 2019-01..2026-08 · %d Anker · davon in den CMC Top 200 der Woche %.0f %%\n" % (len(X), 100 * X.in_cmc.mean()))
    erg = {}
    for name, v in VARIANTEN.items():
        d, n, nf = reihe(X, v)
        lo, hi = P86.band(d, 3)
        erg[name] = d.mean()
        print("  %-20s %3d Stichtage %.0f Bloecke · Gruppe %.0f Coins, Fuenftel %.1f · F5 - Gruppe %+.1f Pp [%+.1f; %+.1f]%s" % (
            name, len(d), len(d) / 3, n, nf, 100 * d.mean(), 100 * lo, 100 * hi,
            "" if name == "V0 A1" else " · gegen V0 %+.1f Pp" % (100 * (d.mean() - erg["V0 A1"]))))
    print("\nAUSKUNFT Gruppenunterschied (gemeinsame Coins):")
    gruppen_unterschied(X)
    ok0 = abs(100 * erg["V0 A1"] - 3.5) <= 0.1
    print("\n  V0 trifft A1 (+3,5 +- 0,1 Pp): %s" % ("ja" if ok0 else "NEIN - Halt"))
    for name in ("V0 A1", "V4 Gruppe + Ertrag", "V3b Ertrag nach t"):
        g = gegenprobe(X, VARIANTEN[name])
        print("  Gegenprobe %-20s eigene Schleife %+.2f Pp · Hauptweg %+.2f Pp -> %s" % (
            name, 100 * g, 100 * erg[name], "gleich" if abs(g - erg[name]) < 1e-4 else "UNGLEICH"))


if __name__ == "__main__":
    main()
