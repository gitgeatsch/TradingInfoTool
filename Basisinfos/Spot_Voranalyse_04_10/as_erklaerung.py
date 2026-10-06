"""Erklaerung der Asymmetrie-Kombination (Voranalyse_Spot §19.7) - NUR Auskunft, keine neue Hypothese, kein Urteil.

    python Basisinfos/Spot_Voranalyse_04_10/as_erklaerung.py

  1. Wirkung je Faktor: die Kombination OHNE jeweils einen Faktor (Saldo, Lift R2/D2) - was faellt weg, wenn er fehlt?
  2. Rangstabilitaet: wie viele Coins bleiben von Monat zu Monat im oberen Fuenftel, wie lange bleibt ein Coin drin, Ueberlappung nach 12 Monaten
  3. Liste gegen Watchlist: NEU ins Fuenftel gekommen gegen SCHON DRIN gewesen (Anteil verdoppelt / -70 % oder eingestellt gegen die Klasse)
  4. Die Liste zum letzten Monatsersten der Daten (ohne Ausgang - Beispiel, KEIN Signal)
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
NAME = {"F1": "Absturz tief (weit unter Allzeithoch)", "F2": "Hoch liegt lange zurueck", "F8": "Alter hoch", "F9": "TVL waechst schneller als der Kurs"}


def wert(Z, F, wahl):
    P = np.vstack([M.pct_in_zelle(Z, F[k]) if s == "oben" else 1 - M.pct_in_zelle(Z, F[k]) for k, s in wahl])
    with np.errstate(all="ignore"):
        return np.where(np.isnan(P).all(axis=0), np.nan, np.nanmean(P, axis=0))


def main():
    D = M.paare(365).reset_index(drop=True)
    Z = M.Zellen(D)
    F = M.merkmale(D)
    print("Erklaerung der Kombination (§19.7, Auskunft) · %d Coin-Anker\n" % len(D))
    print("1. WIRKUNG JE FAKTOR (oberes Fuenftel; Saldo = Anteil verdoppelt - Anteil -70 %/eingestellt, gegen die Klasse am Stichtag)")
    for titel, wahl in [("alle vier", WAHL)] + [("ohne %s (%s)" % (k, NAME[k]), [x for x in WAHL if x[0] != k]) for k, _ in WAHL]:
        o = M.bewerte(Z, wert(Z, F, wahl), "oben", null=False, ep_liste=("E2", "E3"))
        print("   %-46s %s" % (titel, " · ".join("%s Saldo %+5.1f Pp (verdoppelt %+4.1f Pp, Absturz %+4.1f Pp)" % (
            e, 100 * o[e]["saldo"], 100 * (o[e]["lift_r2"] - 1) * np.mean(Z.r2), 100 * (o[e]["lift_d2"] - 1) * np.mean(Z.d2)) for e in ("E2", "E3"))))
    for k, s in WAHL:
        o = M.bewerte(Z, F[k], s, null=False, ep_liste=("E2", "E3"))
        print("   einzeln %-39s %s" % ("%s %s" % (k, NAME[k]), " · ".join("%s Saldo %+5.1f Pp" % (e, 100 * o[e]["saldo"]) for e in ("E2", "E3"))))
    w = wert(Z, F, WAHL)
    p = M.pct_in_zelle(Z, w)
    D["oben"] = p > 0.8
    D["p"] = p
    print("\n2. RANGSTABILITAET (oberes Fuenftel je Klasse)")
    for kl in ("H", "M", "S"):
        x = D[(D.kl == kl) & D.p.notna()]
        tage = sorted(x.t.unique())
        sets = {t: set(x[(x.t == t) & x.oben].sym) for t in tage}
        bleib, bleib12 = [], []
        for i in range(1, len(tage)):
            a, b = sets[tage[i - 1]], sets[tage[i]]
            if b:
                bleib.append(len(a & b) / len(b))
            if i >= 12 and b:
                bleib12.append(len(sets[tage[i - 12]] & b) / len(b))
        dauer = []
        for s in x.sym.unique():
            folge = [s in sets[t] for t in tage]
            n = 0
            for f in folge + [False]:
                if f:
                    n += 1
                elif n:
                    dauer.append(n); n = 0
        print("   %s  je Monat %4.1f Coins im Fuenftel · davon schon im Vormonat %3.0f %% · noch nach 12 Monaten %3.0f %% · ein Coin bleibt im Median %d Monate (Mittel %.1f) · verschiedene Coins insgesamt %d" % (
            kl, np.mean([len(v) for v in sets.values()]), 100 * np.mean(bleib), 100 * np.mean(bleib12), int(np.median(dauer)), np.mean(dauer), len({s for v in sets.values() for s in v})))
    print("\n3. LISTE GEGEN WATCHLIST: neu ins Fuenftel gekommen gegen schon im Vormonat drin")
    D["vor"] = False
    for (kl), x in D.groupby("kl"):
        tage = sorted(x.t.unique())
        vor = {tage[i]: set(x[(x.t == tage[i - 1]) & x.oben].sym) for i in range(1, len(tage))}
        for j in x.index:
            D.at[j, "vor"] = D.sym[j] in vor.get(D.t[j], set())
    for e in ("E2", "E3"):
        x = D[(D.ep == e) & D.p.notna()]
        alle = x.groupby(["t", "kl"]).agg(r2=("r2", "mean"), l=("l", "mean"))
        for name, m in (("neu im Fuenftel", x.oben & ~x.vor), ("schon drin", x.oben & x.vor)):
            q = x[m]
            if not len(q):
                continue
            ref = alle.loc[list(zip(q.t, q.kl))]
            print("   %s %-16s n %4d | verdoppelt %4.1f %% (Klasse %4.1f %%) · -70 %%/eingestellt %4.1f %% (Klasse %4.1f %%)" % (
                e, name, len(q), 100 * q.r2.mean(), 100 * ref.r2.mean(), 100 * q.l.mean(), 100 * ref.l.mean()))
    # 4. aktuelle Liste
    t = pd.Timestamp(A.ENDE).replace(day=1)
    kl = A.klassen(t)[0]
    Dn = pd.DataFrame([dict(t=t, sym=s, kl=k, ep="E3", r2=False, r3=False, l=False, d2=False, eing=False, ende=1.0, ende_b=1.0) for s, k in kl.items()])
    Fn = M.merkmale(Dn)
    Zn = M.Zellen(Dn)
    wn = wert(Zn, Fn, WAHL)
    pn = M.pct_in_zelle(Zn, wn)
    print("\n4. LISTE ZUM %s (Beispiel, KEIN Signal; Wert = Mittel der vier Perzentile in der Klasse, 1 = bester)" % t.date())
    for k in ("H", "M", "S"):
        m = (Dn.kl.values == k) & (pn > 0.8)
        x = pd.DataFrame({"sym": Dn.sym.values[m], "wert": wn[m], "tiefe": Fn["F1"][m], "alter": Fn["F8"][m] / 365, "dauer": Fn["F2"][m] / 30.4,
                          "tvl": Fn["F9"][m]}).sort_values("wert", ascending=False)
        print("   %s (%d):" % (k, len(x)))
        for r in x.head(25).itertuples():
            print("      %-8s Wert %.2f · %4.0f %% unter Allzeithoch · Hoch vor %3.0f Monaten · Alter %4.1f J · TVL gg. Kurs %s" % (
                r.sym, r.wert, -100 * r.tiefe, r.dauer, r.alter, ("%+.2f" % r.tvl) if not np.isnan(r.tvl) else "  -  "))


if __name__ == "__main__":
    main()
