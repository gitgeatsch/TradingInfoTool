"""MACHBARKEIT Messplan U2/U1 (Spot §46, vor dem Plan) - nur Anzahlen, keine Ertraege ab 2024. Nur lesend.

    python Basisinfos/Spot_Voranalyse_04_10/k47_machbarkeit.py

  M0 Teil 0 (R-R11): Stufe 1 reproduziert - gebuehr90 oben 1,25 / stab90 unten 1,29 (+-0,01), sonst Abbruch
  M1 Einstiege nach Regel (Signal am Tagesschluss d im Fuenftel des Tagesquerschnitts >= 30 Coins, Kauf d+1, Zeitgrenze 30 T, EINE Sperre
     je Coin ueber alle Klassen = k37_machbarkeit.einstiege_alle): 2023 (Wahl) und ab 2024 (Urteil) - Einstiege, Monate, Coins, je Klasse
  M2 Nullwelt-Vorrat je Signaltag: Coins derselben Klasse MIT Merkmalswert und OHNE Signal (Haupt) bzw. alle der Klasse (Auskunft)
  M3 bei Bitpanda handelbar (Katalog 08.10.)
Ablage: data/_spot/k47_einstiege_<U2|U1>_<W|U>.csv
"""
import os
import sys

import numpy as np
import pandas as pd

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HIER)
import kp46_vorpruefung as V  # noqa: E402
import k37_machbarkeit as KM  # noqa: E402

T, K, IDX = V.T, V.K, V.IDX
HYP = {"U2": ("gebuehr90", "oben", 1.25), "U1": ("stab90", "unten", 1.29)}


def perz(X, m):
    Xm = X.where(m)
    p = Xm.rank(axis=1, pct=True)
    p.loc[Xm.notna().sum(axis=1) < 30] = np.nan
    return p


def main():
    rel = K.div(T.B, axis=0)
    up, down, end, fertig = T.ziele(rel)
    m, kl = T.maske()
    m = m & fertig
    w = (IDX >= "2023-01-01") & (IDX <= "2023-12-01")
    F = V.merkmale()
    print("MACHBARKEIT Messplan U2/U1 (§46) · Kurse bis %s\n" % T.M.ENDE.date())
    ok0 = True
    for h, (name, seite, soll) in HYP.items():
        r = V.auswerten(F[name], up, down, end, m, kl, w, 30)[seite]["richtung"]
        ok0 &= abs(r - soll) < 0.01
        print("M0 Teil 0 %s %s %s: Richtung %.3f (Soll %.2f) -> %s" % (h, name, seite, r, soll, "gleich" if abs(r - soll) < 0.01 else "ABWEICHUNG"))
    if not ok0:
        print("TEIL 0 FEHLGESCHLAGEN - Abbruch")
        return
    kat = set(pd.read_csv(os.path.join("data", "_spot", "bitpanda_katalog_krypto_2026-10-08.csv"), sep=";").symbol.str.upper())
    print()
    for h, (name, seite, _) in HYP.items():
        X = F[name]
        p = perz(X, m)
        pv = p if seite == "oben" else 1 - p
        for nm, ab, bis in (("2023 (Wahl)", "2023-01-01", "2023-12-01"), ("ab 2024 (Urteil)", "2024-01-01", str(T.M.ENDE.date()))):
            E = KM.einstiege_alle(pv, kl, m, pd.Timestamp(ab), pd.Timestamp(bis))
            vor_h, vor_a = [], []
            for d, g in E.groupby("signal"):
                for k in g.kl.unique():
                    mk = (kl.loc[d] == k) & m.loc[d]
                    vor_h.append(int((mk & X.loc[d].notna() & ~(pv.loc[d] >= 0.8)).sum()))
                    vor_a.append(int((mk & ~(pv.loc[d] >= 0.8)).sum()))
            jk = " · ".join("%s %d" % (k, (E.kl == k).sum()) for k in "HMS")
            print("M1 %s %-17s Einstiege %4d · Monate %2d · Coins %3d · je Klasse %s" % (
                h, nm, len(E), E.signal.dt.to_period("M").nunique() if len(E) else 0, E.sym.nunique() if len(E) else 0, jk))
            if vor_h:
                print("M2    Nullwelt-Vorrat je Tag und Klasse: mit Merkmal min %d / Median %d · alle der Klasse min %d / Median %d" % (
                    min(vor_h), int(np.median(vor_h)), min(vor_a), int(np.median(vor_a))))
            print("M3    bei Bitpanda handelbar %.0f %%" % (100 * np.mean([s in kat for s in E.sym]) if len(E) else 0))
            E.to_csv(os.path.join("data", "_spot", "k47_einstiege_%s_%s.csv" % (h, "W" if ab.startswith("2023") else "U")), sep=";", index=False)
        print()


if __name__ == "__main__":
    main()
