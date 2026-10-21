"""GRID STUFE 1 FASSUNG 2b (Recherche_Grid_Trading_21_10.md §9.2/§9.3): Nullwelt = Zufallspfad mit GEMEINSAMER Drift.

Fassung 2 (Ziehen mit Zuruecklegen samt Monatsdrift) fiel im Selbsttest (unabhaengige Welten Rang ~1, §9.3). Fassung 2b: Stundenrenditen
je Monat um das eigene Monatsmittel bereinigt, mit Zuruecklegen gezogen, plus die gemeinsame Drift des ganzen Fensters.

    python Basisinfos/Spot_Voranalyse_04_10/grid_stufe1_f2.py

Ablauf: (1) SELBSTTEST mit bekannter Wahrheit - nur wenn er besteht, (2) Messung BTC/ETH 1/2/3 %, Auskunft 0,5 % sowie SOL/LINK.
Das Gitter selbst (grid_stufe1.gitter, gegengeprueft in G1) und alle Auslegungen aus Fassung 1 bleiben unveraendert.
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import grid_stufe1 as G  # noqa: E402

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:  # noqa: BLE001
    pass
D = G.ZIEHUNGEN


def monat_null(r, rng, mu, D=D):
    z = rng.choice(r - r.mean(), size=(D, len(r)), replace=True) + mu
    return np.concatenate([np.zeros((D, 1)), np.cumsum(z, axis=1)], axis=1)


def zellen(monatsrenditen, stufen, saat=22102026):
    rng = np.random.default_rng(saat)
    mu = float(np.mean(np.concatenate(monatsrenditen)))
    aus = {g: [] for g in stufen}
    for r in monatsrenditen:
        echt = np.concatenate([[0.0], np.cumsum(r)])[None, :]
        null = monat_null(r, rng, mu)
        for g in stufen:
            e, ne = G.gitter(echt, g)
            nn, nne = G.gitter(null, g)
            aus[g].append((None, e[0], ne[0], nn, nne))
    return aus


def rang(z):
    echt = sum(x[1] for x in z)
    null = np.sum([x[3] for x in z], axis=0)
    return float(np.mean(null < echt))


def selbsttest():
    sig = np.std(np.diff(np.log(G.stunden("BTC")[0].values)))

    def welt(phi, saat):
        rr = np.random.default_rng(saat)
        aus = []
        for _ in range(36):
            e = rr.normal(0, sig * np.sqrt(1 - phi ** 2), 719)
            x = np.empty(719)
            x[0] = e[0]
            for t in range(1, 719):
                x[t] = phi * x[t - 1] + e[t]
            aus.append(x)
        return aus

    erg = {}
    for name, phi in (("Rueckkehr", -0.10), ("Trend", +0.10), ("unabhaengig", 0.0)):
        erg[name] = [rang(zellen(welt(phi, 10 + i), (0.01,))[0.01]) for i in range(3)]
    ok = all(v >= 0.95 for v in erg["Rueckkehr"]) and all(v <= 0.05 for v in erg["Trend"]) and all(0.05 < v < 0.95 for v in erg["unabhaengig"])
    print("SELBSTTEST (je 3 kuenstliche Welten, 36 Monate, BTC-Stundenschwankung, g 1 %%): Rueckkehr %s · Trend %s · unabhaengig %s -> %s"
          % tuple([" / ".join("%.3f" % v for v in erg[k]) for k in ("Rueckkehr", "Trend", "unabhaengig")] + ["BESTANDEN" if ok else "NICHT BESTANDEN"]))
    return ok


def messe(sym, stufen):
    P, fehlt = G.stunden(sym)
    mon = sorted(set(P.index.to_period("M")))
    rr = [np.diff(np.log(P[P.index.to_period("M") == m].values)) for m in mon]
    return zellen(rr, stufen), fehlt, len(mon)


def main():
    print("GRID STUFE 1 FASSUNG 2b · %s bis %s · Nullwelt Zufallspfad (%d Ziehungen je Monat, mit Zuruecklegen, gemeinsame Drift) · Schwelle %.2f %%\n"
          % (G.VON, G.BIS, D, 100 * G.GEBUEHR))
    if not selbsttest():
        print("\nSELBSTTEST NICHT BESTANDEN - es wird NICHT gemessen (§9.2).")
        return
    print()
    urteil = {}
    for sym in ("BTC", "ETH"):
        z, fehlt, nm = messe(sym, G.STUFEN + (G.AUSKUNFT_STUFE,))
        print("%s: %d Monate, fehlende Stunden %d" % (sym, nm, fehlt))
        for g in G.STUFEN:
            urteil[(sym, g)] = G.auswerten(sym, z[g], g)
        print("  Auskunft:")
        G.auswerten(sym, z[G.AUSKUNFT_STUFE], G.AUSKUNFT_STUFE)
        print()
    tr = [k for k, v in urteil.items() if v[0]]
    um = [k for k, v in urteil.items() if v[1]]
    print("URTEIL nach §9.2: tragende Zellen %d von %d %s · umgekehrt (Trend) %d %s" % (len(tr), len(urteil), tr, len(um), um))
    print("FOLGE: %s" % ("STUFE 2 (1-Minuten-Rueckspiel, Download braucht Nutzer-Ja)" if tr else "W-A ENDET - zurueck zu Alternativen / Bestehendes"))
    print("\nAUSKUNFT SOL und LINK (gleiches Fenster):")
    for sym in ("SOL", "LINK"):
        z, fehlt, nm = messe(sym, G.STUFEN)
        print("%s: %d Monate, fehlende Stunden %d" % (sym, nm, fehlt))
        for g in G.STUFEN:
            G.auswerten(sym, z[g], g)


if __name__ == "__main__":
    main()
