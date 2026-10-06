"""Die sechs Pruefungen fuer die KOMBINATION aus as_messung.py (F1 unten, F2 oben, F8 oben, F9 oben; Voranalyse_Spot §19.6) - nur lesend.

    python Basisinfos/Spot_Voranalyse_04_10/as_pruefungen_komb.py

Dosis (Fuenftel 1..5), je Klasse, je Jahr, Weglassprobe (ohne die 5 Coins mit den meisten R2-Treffern), Ueberschneidung mit F8 (traegt das
Alter allein?), Kombination OHNE F8 (traegt der Rest?), dazu die Kandidatenliste zum letzten Stichtag als Beispiel (Auskunft, kein Signal).
"""
import os
import sys

import numpy as np
import pandas as pd

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HIER)
import as_messung as M  # noqa: E402

A = M.A
WAHL = [("F1", "unten"), ("F2", "oben"), ("F8", "oben"), ("F9", "oben")]


def wert(Z, F, wahl):
    P = np.vstack([M.pct_in_zelle(Z, F[k]) if s == "oben" else 1 - M.pct_in_zelle(Z, F[k]) for k, s in wahl])
    with np.errstate(all="ignore"):
        return np.where(np.isnan(P).all(axis=0), np.nan, np.nanmean(P, axis=0))


def main():
    D = M.paare(365).reset_index(drop=True)
    Z = M.Zellen(D)
    M.baue_grid(Z)
    F = M.merkmale(D)
    w = wert(Z, F, WAHL)
    print("PRUEFUNGEN der Kombination %s (oberes Fuenftel)\n" % ", ".join("%s %s" % x for x in WAHL))
    for e in ("E2", "E3"):
        d = [M.bewerte(Z, w, "oben", null=False, ep_liste=(e,), quintil=q)[e] for q in (1, 2, 3, 4, 5)]
        print("  Dosis %s  Fuenftel 1..5 Saldo: %s" % (e, " ".join("%+5.1f" % (100 * x["saldo"]) for x in d)))
    for kl in ("H", "M", "S"):
        m = D.kl.values == kl
        Zk = M.Zellen(D[m].reset_index(drop=True))
        o = M.bewerte(Zk, w[m], "oben", null=False, ep_liste=("E2", "E3"))
        print("  Klasse %s  %s" % (kl, " · ".join("%s Saldo %+5.1f Pp · Lift R2 %.2f / D2 %.2f · Korb %+4.0f %% (Klasse %+4.0f %%)" % (
            e, 100 * o[e]["saldo"], o[e]["lift_r2"], o[e]["lift_d2"], 100 * o[e]["korb"], 100 * o[e]["korb_k"]) if o.get(e) else "%s -" % e for e in ("E2", "E3"))))
    for j in sorted(D.t.dt.year.unique()):
        m = (D.t.dt.year == j).values
        o = M.bewerte(M.Zellen(D[m].reset_index(drop=True)), w[m], "oben", null=False, ep_liste=(A.epoche(pd.Timestamp("%d-06-01" % j)),))
        x = list(o.values())[0]
        print("  Jahr %d  %s" % (j, ("Saldo %+5.1f Pp · Lift R2 %.2f / D2 %.2f · %d Coins" % (100 * x["saldo"], x["lift_r2"], x["lift_d2"], x["coins"])) if x else "-"))
    p = M.pct_in_zelle(Z, w)
    for e in ("E2", "E3"):
        q = (p > 0.8) & (D.ep.values == e) & (Z.r2 > 0)
        top5 = pd.Series(D.sym.values[q]).value_counts().index[:5].tolist()
        o = M.bewerte(Z, w, "oben", null=False, ep_liste=(e,), ohne=top5)[e]
        ok = M.spiegel_ok(o, e)
        print("  Weglassprobe %s ohne %s: Saldo %+5.1f Pp · Lift R2 %.2f / D2 %.2f · Spiegelprobe %s" % (e, ",".join(top5), 100 * o["saldo"], o["lift_r2"], o["lift_d2"],
                                                                                                         "besteht" if ok else "nein"))
    p8 = M.pct_in_zelle(Z, F["F8"])
    beide = (p > 0.8) & (p8 > 0.8)
    print("\n  Ueberschneidung: %.0f %% des Kombinations-Fuenftels sind auch im obersten Alters-Fuenftel" % (100 * beide.sum() / (p > 0.8).sum()))
    w2 = wert(Z, F, [x for x in WAHL if x[0] != "F8"])
    o = M.bewerte(Z, w2, "oben", ep_liste=("E2", "E3"))
    print("  Kombination OHNE F8 (F1 unten, F2 oben, F9 oben):")
    for e in ("E2", "E3"):
        x = o[e]
        print("    %s Saldo %+5.1f Pp · Rang %.3f · Lift R2 %.2f / D2 %.2f · Spiegelprobe %s · %d Coins" % (e, 100 * x["saldo"], x["rang"], x["lift_r2"], x["lift_d2"],
                                                                                                   "besteht" if M.spiegel_ok(x, e) else "nein", x["coins"]))
    t = D.t.max()
    m = (D.t == t).values
    print("\n  Beispiel: oberes Fuenftel am letzten Stichtag mit abgeschlossenem 12-Monats-Fenster (%s; Auskunft, KEIN Signal):" % t.date())
    for kl in ("H", "M", "S"):
        x = D[m & (D.kl.values == kl) & (p > 0.8)]
        print("    %s: %s" % (kl, ", ".join("%s%s" % (s, "*" if r2 else "") for s, r2 in zip(x.sym, x.r2))))
    print("    (* = hat sich danach binnen 12 Monaten zeitweise verdoppelt)")


if __name__ == "__main__":
    main()
