"""MESSUNG D4 und ABDECKUNGSGRAD (Spot §39.9, vorab Commit 8eecc64) - nur lesend, keine Aufrufe.

    python Basisinfos/Spot_Voranalyse_04_10/d4_wirkung.py

  Teil 0  Dosis §25.6 mit vollem Watchlist-Wert (F1, F2, F8, F9) wiedergeben (+-0,15 Pp), sonst Abbruch
  D4      Wert OHNE F9 (TVL): Fuenftel-Wechsel je Epoche, unteres Fuenftel rein/raus, Dosis ohne F9 (entscheidet: unteres Fuenftel in
          E2 UND E3 das schlechteste und < 0 -> D4 darf hinter B4)
  ABDECKUNG  23 Krypto-Bestaende ohne Kern (NB-Teilexport 09.10.) am letzten Monatsstichtag; Universum ab 2024
"""
import os
import sys

import numpy as np
import pandas as pd

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HIER)
os.chdir(os.path.dirname(os.path.dirname(HIER)))
import mk_messung as MK  # noqa: E402

M, W = MK.M, MK.W
K, POS, ENDE = MK.K, MK.POS, MK.ENDE
OHNE_F9 = [x for x in W.WAHL if x[0] != "F9"]
SOLL = {"E2": [-6.5, -4.0, -0.7, 0.3, 10.5], "E3": [-16.3, -6.7, 3.2, 5.5, 13.6]}
BESTAND = ["ALGO", "ASTER", "AVAX", "BEAMX", "BIO", "BRETT", "CANTON", "CT", "INJ", "KAIA", "KAS", "LINK", "MON", "MORPHO", "NEAR", "PLUME",
           "QNT", "SUI", "SUPRA", "TURBO", "W", "XDC", "XLM"]


def dosis(Z, w, ep):
    return [100 * M.bewerte(Z, w, "oben", null=False, ep_liste=(ep,), quintil=q)[ep]["saldo"] for q in (1, 2, 3, 4, 5)]


def fuenftel(p):
    return np.where(np.isnan(p), np.nan, np.clip(np.ceil(p * 5), 1, 5))


def main():
    D = MK.paare_mw(365).reset_index(drop=True)
    Z = M.Zellen(D)
    F = M.merkmale(D)
    w, w9 = W.wert(Z, F), W.wert(Z, F, wahl=OHNE_F9)
    print("MESSUNG D4 + ABDECKUNG (§39.9) · Kurse bis %s\n" % ENDE.date())
    ok = True
    for ep in ("E2", "E3"):
        d = dosis(Z, w, ep)
        ok &= all(abs(a - b) <= 0.15 for a, b in zip(d, SOLL[ep]))
        print("TEIL 0 Dosis %s voller Wert: %s (Soll %s)" % (ep, " ".join("%+5.1f" % x for x in d), " ".join("%+5.1f" % x for x in SOLL[ep])))
    if not ok:
        print("TEIL 0 FEHLGESCHLAGEN - Abbruch"); return
    print("-> Teil 0 bestanden\n")
    p, p9 = M.pct_in_zelle(Z, w), M.pct_in_zelle(Z, w9)
    q, q9 = fuenftel(p), fuenftel(p9)
    tvl = ~np.isnan(F["F9"])
    entscheid = True
    for ep in ("E2", "E3"):
        e = (D.ep.values == ep) & ~np.isnan(q) & ~np.isnan(q9)
        u = e & (q == 1)
        print("D4 %s: Anker %d · anderes Fuenftel ohne F9 %.1f %% (nur Coins mit TVL %.1f %%, n %d) · unteres Fuenftel %d: verlassen %d (%.1f %%), neu %d" % (
            ep, e.sum(), 100 * np.mean(q[e] != q9[e]), 100 * np.mean(q[e & tvl] != q9[e & tvl]) if (e & tvl).any() else float("nan"), (e & tvl).sum(),
            u.sum(), (u & (q9 != 1)).sum(), 100 * np.mean(q9[u] != 1), (e & (q9 == 1) & (q != 1)).sum()))
        d9 = dosis(Z, w9, ep)
        unten = d9[0] < 0 and d9[0] == min(d9)
        entscheid &= unten
        print("   Dosis %s OHNE F9: %s -> unteres Fuenftel %s" % (ep, " ".join("%+5.1f" % x for x in d9), "schlechtestes und < 0" if unten else "NICHT schlechtestes/< 0"))
    print("\n=> D4 %s" % ("darf HINTER B4 ruecken (B4 vorlaeufig ohne TVL-Merkmal)" if entscheid else "bleibt PFLICHT VOR B4"))

    print("\nABDECKUNG Universum ab 2024 (Anker der Messung): F9 bekannt %.0f %% · alle vier Merkmale bekannt %.0f %% · F1/F2/F8 bekannt %.0f %%" % (
        100 * np.mean(tvl[D.t.values >= np.datetime64("2024-01-01")]),
        100 * np.mean(np.all([~np.isnan(F[k]) for k, _ in W.WAHL], axis=0)[D.t.values >= np.datetime64("2024-01-01")]),
        100 * np.mean(np.all([~np.isnan(F[k]) for k, _ in OHNE_F9], axis=0)[D.t.values >= np.datetime64("2024-01-01")])))
    t = max(x for x in POS if x.day == 1)
    out, _, _ = MK.klassen_mw(t)
    Dt = pd.DataFrame([dict(t=t, sym=s, kl=k) for s, k in out.items() if not np.isnan(K[s].values[POS[t]])])
    Ft = M.merkmale(Dt)
    Zl = W.Leicht(Dt)
    pt, pt9 = M.pct_in_zelle(Zl, W.wert(Zl, Ft)), M.pct_in_zelle(Zl, W.wert(Zl, Ft, wahl=OHNE_F9))
    print("\nABDECKUNG BESTAND am Stichtag %s (Universum %d Coins):" % (t.date(), len(Dt)))
    zaehl = {"voll": 0, "ohne_tvl": 0, "nicht": 0}
    for s in BESTAND:
        j = np.where(Dt.sym.values == s)[0]
        binance = s in K.columns and not np.isnan(K[s].values[POS[t]])
        if not len(j):
            zaehl["nicht"] += 1
            print("  %-7s NICHT im Watchlist-Universum · Kurs B1: %s" % (s, "Binance" if binance else "nur Prod (D5)"))
            continue
        j = j[0]
        bek = [k for k, _ in W.WAHL if not np.isnan(Ft[k][j])]
        zaehl["voll" if len(bek) == 4 else "ohne_tvl"] += 1
        print("  %-7s Klasse %s · Merkmale %s · Fuenftel %s (ohne F9 %s) · Kurs B1: Binance" % (
            s, Dt.kl.values[j], ",".join(bek), "%d" % fuenftel(pt[j:j + 1])[0] if pt[j] == pt[j] else "-", "%d" % fuenftel(pt9[j:j + 1])[0] if pt9[j] == pt9[j] else "-"))
    print("  -> %d von %d mit allen vier Merkmalen · %d ohne TVL · %d nicht im Universum (B4 nur eingeordnet ueber D5)" % (
        zaehl["voll"], len(BESTAND), zaehl["ohne_tvl"], zaehl["nicht"]))
    pd.DataFrame(dict(t=D.t, sym=D.sym, kl=D.kl, ep=D.ep, q=q, q9=q9)).to_csv(os.path.join("data", "_spot", "d4_wirkung.csv"), sep=";", index=False)


if __name__ == "__main__":
    main()
