"""MACHBARKEIT und TEIL 0 fuer Messplan §40 K-3 "Ruhiger Boden" - nur lesend, KEIN Ergebnis ab 2024.

    python Basisinfos/Spot_Voranalyse_04_10/k3_machbarkeit.py

  M0 Teil 0 (R-R11): Vorpruefung §35.2 Stufe 1b reproduzieren - 'schwankung90 unten UND tiefe unten' (je unteres Fuenftel im
     Tagesquerschnitt), 2023 bis 01.12.: n 2.720, Richtung 1,90, Ende 30 T +2,3 Pp gegen alle
  M1 Einstiege nach der Regel §40.2 (beide unteren Fuenftel am Tag d, Kauf d+1, Zeitgrenze 30 T, Sperre je Coin) je Klasse H/M/S:
     Anzahl, Monate, Coins - 2023 und ab 2024 (NUR Anzahlen)
  M2 Nullwelt-Vorrat (Coins derselben Klasse ohne Signal am Tag) · M3 bei Bitpanda handelbar (Katalog 08.10.)
"""
import os
import sys

import numpy as np
import pandas as pd

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HIER)
os.chdir(os.path.dirname(os.path.dirname(HIER)))
import k37_machbarkeit as KM  # noqa: E402
import tc_vorpruefung as T   # noqa: E402

IDX = T.IDX


def perz(F, m, name):
    X = F[name].where(m)
    p = X.rank(axis=1, pct=True)
    p.loc[X.notna().sum(axis=1) < 30] = np.nan
    return p


def signal(F, m):
    """Ruhiger Boden am Tagesschluss: Schwankung 90 T im unteren Fuenftel UND Tiefe (Schluss/Allzeithoch) im unteren Fuenftel.
    Rueckgabe als 'pct'-Feld fuer k37_machbarkeit.einstiege: 1,0 = Signal, 0,0 = kein Signal, NaN = nicht bewertbar."""
    ps, pt = perz(F, m, "schwankung90"), perz(F, m, "tiefe")
    s = ((ps <= 0.2) & (pt <= 0.2)).astype(float)
    return s.where(ps.notna() & pt.notna())


def main():
    rel, F = T.merkmale()
    up, down, end, fertig = T.ziele(rel)
    m, kl = T.maske()
    m = m & fertig
    w = (IDX >= "2023-01-01") & (IDX <= "2023-12-01")
    mw = m[w]
    P = {nm: perz({nm: F[nm][w]}, mw, nm) for nm in ("rs7", "schwankung90", "tiefe")}
    uw, dw, ew = up[w], down[w], end[w]
    basis = P["rs7"].notna()
    p_up, p_dn, e_all = uw[basis].stack().mean(), dw[basis].stack().mean(), ew[basis].stack().mean()
    sel = (P["schwankung90"] <= 0.2) & (P["tiefe"] <= 0.2)
    n0 = int(sel.values.sum())
    ri = (uw[sel].stack().mean() / p_up) / (dw[sel].stack().mean() / p_dn)
    en = ew[sel].stack().mean() - e_all
    ok0 = n0 == 2720 and abs(ri - 1.90) < 0.006 and abs(100 * en - 2.3) < 0.06
    print("MACHBARKEIT §40 K-3 Ruhiger Boden · Kurse bis %s\n" % T.M.ENDE.date())
    print("M0 TEIL 0 (R-R11) Vorpruefung §35.2 Stufe 1b: n %d (Soll 2.720) · Richtung %.3f (Soll 1,90) · Ende 30 T %+.2f Pp (Soll +2,3) -> %s" % (
        n0, ri, 100 * en, "BESTANDEN" if ok0 else "NICHT bestanden - Messung bricht ab"))
    sig = signal(F, m)
    kat = set(pd.read_csv(os.path.join("data", "_spot", "bitpanda_katalog_krypto_2026-10-08.csv"), sep=";").symbol.str.upper())
    print("\nM1-M3 EINSTIEGE nach Regel §40.2 (nur Anzahlen):")
    alle = {}
    for nm, ab, bis in (("2023 (Wahl)", "2023-01-01", "2023-12-01"), ("ab 2024 (Urteil)", "2024-01-01", str(T.M.ENDE.date()))):
        A = KM.einstiege_alle(sig, kl, m, pd.Timestamp(ab), pd.Timestamp(bis))          # EINE Sperre je Coin ueber alle Klassen
        alle[nm] = A
        print("  ALLE  %-17s Einstiege %4d · Monate %2d · Coins %3d" % (nm, len(A), A.signal.dt.to_period("M").nunique() if len(A) else 0, A.sym.nunique() if len(A) else 0))
    for k in ("H", "M", "S"):
        for nm, ab, bis in (("2023 (Wahl)", "2023-01-01", "2023-12-01"), ("ab 2024 (Urteil)", "2024-01-01", str(T.M.ENDE.date()))):
            E = alle[nm][alle[nm].kl == k].drop(columns="kl")
            mon = E.signal.dt.to_period("M").nunique() if len(E) else 0
            vorrat = [int(((kl.loc[d] == k) & m.loc[d] & ~(sig.loc[d] >= 0.8)).sum()) for d in E.signal.unique()]
            print("  %s %-17s Einstiege %4d · Monate %2d · Coins %3d · Nullwelt-Vorrat je Tag min %s / Median %s · bei Bitpanda %.0f %%" % (
                k, nm, len(E), mon, E.sym.nunique() if len(E) else 0, min(vorrat) if vorrat else "-", int(np.median(vorrat)) if vorrat else "-",
                100 * np.mean([s in kat for s in E.sym]) if len(E) else 0))
            E.to_csv(os.path.join("data", "_spot", "k3_einstiege_%s_%s.csv" % (k, "W" if ab.startswith("2023") else "U")), sep=";", index=False)


if __name__ == "__main__":
    main()
