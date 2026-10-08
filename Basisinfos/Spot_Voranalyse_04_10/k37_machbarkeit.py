"""MACHBARKEIT und TEIL 0 fuer Messplan §37 K-H1 (Momentum je Klasse) - nur lesend, KEIN Ergebnis ab 2024.

    python Basisinfos/Spot_Voranalyse_04_10/k37_machbarkeit.py

  M0 Teil 0 (R-R11): Vorpruefung §35 reproduzieren - Richtung rs30 oberes Fuenftel, Klasse H 1,84 / M 1,05 / S 0,83 (2023, bis 01.12.)
  M1 Einstiege nach der Regel §37.2 (rs30 oberes Fuenftel im Tagesquerschnitt, Klasse H bzw. M, Kauf am Folgetag, Sperre bis zum
     Ausstieg nach 30 T): Anzahl, Monate, Coins - 2023 und ab 2024 (NUR Anzahlen)
  M2 Nullwelt-Vorrat: je Einstiegstag Zahl der Coins derselben Klasse OHNE Signal (muss >= 3 sein)
  M3 Bitpanda-Handelbarkeit der Einstiegs-Coins (Katalog 08.10.)
"""
import os
import sys

import numpy as np
import pandas as pd

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HIER)
os.chdir(os.path.dirname(os.path.dirname(HIER)))
import tc_vorpruefung as T  # noqa: E402

K, IDX = T.K, T.IDX


def einstiege(pct, kl, m, klasse, ab, bis, halte=30):
    """Signal am Schluss d (pct >= 0,8, Klasse, Grundgesamtheit) -> Kauf am Schluss d+1, Ausstieg am Schluss d+1+halte; Sperre bis dahin."""
    out = []
    sig = (pct >= 0.8) & (kl == klasse) & m
    for s in sig.columns:
        x = sig[s]
        tage = x.index[x.values & (x.index >= ab) & (x.index <= bis)]
        frei = None
        for d in tage:
            i = IDX.get_loc(d)
            if frei is not None and i <= frei:
                continue
            if i + 1 + halte > len(IDX) - 1:
                break
            out.append((d, s, i + 1, i + 1 + halte))
            frei = i + 1 + halte
    return pd.DataFrame(out, columns=["signal", "sym", "i_kauf", "i_aus"])


def main():
    rel, F = T.merkmale()
    up, down, end, fertig = T.ziele(rel)
    m, kl = T.maske()
    m = m & fertig
    X = F["rs30"].where(m)
    n_tag = X.notna().sum(axis=1)
    pct = X.rank(axis=1, pct=True)
    pct.loc[n_tag < 30] = np.nan
    w = (IDX >= "2023-01-01") & (IDX <= "2023-12-01")
    print("MACHBARKEIT §37 K-H1 · Kurse bis %s\n" % T.M.ENDE.date())
    print("M0 TEIL 0 (R-R11) - Vorpruefung §35 reproduziert (Richtung rs30 oberes Fuenftel, 2023):")
    soll = {"H": 1.84, "M": 1.05, "S": 0.83}
    ok0 = True
    for k in "HMS":
        mk = (kl[w] == k) & m[w]
        basis = pct[w].notna() & mk
        sel = (pct[w] >= 0.8) & mk
        r = (up[w][sel].stack().mean() / up[w][basis].stack().mean()) / (down[w][sel].stack().mean() / down[w][basis].stack().mean())
        ok0 &= abs(r - soll[k]) < 0.02
        print("  %s: Richtung %.3f (Soll %.2f) -> %s" % (k, r, soll[k], "gleich" if abs(r - soll[k]) < 0.02 else "ABWEICHUNG"))
    print("  -> Teil 0 %s" % ("BESTANDEN" if ok0 else "NICHT bestanden - Messung bricht ab"))
    kat = set(pd.read_csv(os.path.join("data", "_spot", "bitpanda_katalog_krypto_2026-10-08.csv"), sep=";").symbol.str.upper())
    print("\nM1-M3 EINSTIEGE nach Regel §37.2 (nur Anzahlen):")
    for k in ("H", "M"):
        for nm, ab, bis in (("2023 (Wahl)", "2023-01-01", "2023-12-01"), ("ab 2024 (Urteil)", "2024-01-01", str(T.M.ENDE.date()))):
            E = einstiege(pct, kl, m, k, pd.Timestamp(ab), pd.Timestamp(bis))
            mon = E.signal.dt.to_period("M").nunique() if len(E) else 0
            vorrat = []
            for d in E.signal.unique():
                ohne = ((kl.loc[d] == k) & m.loc[d] & ~(pct.loc[d] >= 0.8)).sum()
                vorrat.append(ohne)
            bp = np.mean([s in kat for s in E.sym]) if len(E) else 0
            print("  %s %-17s Einstiege %4d · Monate %2d · Coins %3d · Nullwelt-Vorrat je Tag min %s / Median %s · bei Bitpanda %.0f %%" % (
                k, nm, len(E), mon, E.sym.nunique() if len(E) else 0, min(vorrat) if vorrat else "-", int(np.median(vorrat)) if vorrat else "-", 100 * bp))
            E.to_csv(os.path.join("data", "_spot", "k37_einstiege_%s_%s.csv" % (k, "W" if ab.startswith("2023") else "U")), sep=";", index=False)


if __name__ == "__main__":
    main()
