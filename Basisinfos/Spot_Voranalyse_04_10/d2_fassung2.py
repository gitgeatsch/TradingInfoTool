"""Spot D2 Fassung 2 (Voranalyse_Spot_Neubau_04_10.md §12.8, vorab Commit 5853684): Teilverkauf, wenn die Ueberhitzung KIPPT.

    python Basisinfos/Spot_Voranalyse_04_10/d2_fassung2.py

Dieselbe Rechnung wie d_kern_teilverkauf.py (Daten, Zufluss, Ausfuehrung t+1, Rueckkauf gestaffelt wie b2, H0, Kriterium), nur der
Verkaufs-Ausloeser ist neu:
  K1  scharf ab q >= 0,90; Verkauf je 10 % beim Fall unter 0,85 / 0,75 / 0,65
  K2  scharf ab q >= 0,80; Verkauf je 10 % beim Fall 0,10 / 0,20 / 0,30 unter das Zyklushoch von q
  dK1 / dK2 Entnahme statt Rueckkauf; Auskunft: K1/K2 mit 20 % je Stufe
Wieder scharf erst nach einer Zone (q <= 0,20). Nur lesend.
"""
import os
import sys

import numpy as np
import pandas as pd

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HIER)
import d_kern_teilverkauf as D  # noqa: E402  (laedt Daten und Klima, rechnet nichts beim Import)

FAELLE = {"K1": ("abs", 0.90, (0.85, 0.75, 0.65), 0.10, "drittel"), "K2": ("rel", 0.80, (0.10, 0.20, 0.30), 0.10, "drittel"),
          "dK1": ("abs", 0.90, (0.85, 0.75, 0.65), 0.10, "entnahme"), "dK2": ("rel", 0.80, (0.10, 0.20, 0.30), 0.10, "entnahme"),
          "K1_20": ("abs", 0.90, (0.85, 0.75, 0.65), 0.20, "drittel"), "K2_20": ("rel", 0.80, (0.10, 0.20, 0.30), 0.20, "drittel")}


def d2k(sym, start, fall):
    art, scharf_ab, stufen, anteil, rk = FAELLE[fall]
    kurs = D.KURS[sym]
    idx = pd.date_range(start, kurs.index[-1])
    zt = set(D.zuflusstage(idx, start))
    qv = D.Q.shift(1)
    st = kost = geld = entn = ein = 0.0
    an, hoch, offen, zyklus = False, 0.0, [], None
    verk = rueck = 0
    gewinne, rows = [], []
    for t in idx:
        p = kurs[t]
        q = qv.get(t, np.nan)
        if t in zt:
            ein += 1.0; st += 1.0 / p; kost += 1.0
        if not np.isnan(q):
            if q <= 0.20:
                an, hoch, offen = False, 0.0, []
                if rk == "drittel" and geld > 1e-12:
                    if zyklus is None:
                        zyklus = {"basis": geld, "t1": t, "stufe": set()}
                    for grenze in (0.20, 0.10, 0.05):
                        if q <= grenze and grenze not in zyklus["stufe"]:
                            zyklus["stufe"].add(grenze)
                            b = min(zyklus["basis"] / 3 if grenze != 0.05 else geld, geld)
                            st += b / p; kost += b; geld -= b; rueck += 1
            if q >= scharf_ab and not an:
                an, hoch, offen = True, q, list(stufen)
            if an:
                hoch = max(hoch, q)
                for s_ in list(offen):
                    grenze = s_ if art == "abs" else hoch - s_
                    if q < grenze:
                        offen.remove(s_)
                        m = st * anteil; erl = m * p; ek = kost * anteil
                        gewinne.append((t, s_, erl - ek))
                        st -= m; kost -= ek; verk += 1
                        if rk == "entnahme":
                            entn += erl
                        else:
                            geld += erl
            if rk == "drittel" and zyklus is not None and geld > 1e-12 and (t - zyklus["t1"]).days >= 365:
                st += geld / p; kost += geld; geld = 0.0; rueck += 1
            if zyklus is not None and geld <= 1e-12:
                zyklus = None
        rows.append((t, st * p, geld, entn, ein, st))
    r = pd.DataFrame(rows, columns=["t", "wert", "geld", "entn", "ein", "stueck"]).set_index("t")
    r.attrs.update(verk=verk, rueck=rueck, gewinne=gewinne, stueck=st)
    return r


def main():
    starts = {"BTC": ["2015-01-01", "2017-01-01", "2019-01-01", "2021-01-01", "2023-01-01", "2024-01-11"],
              "ETH": ["2017-01-01", "2019-01-01", "2021-01-01", "2023-01-01", "2024-01-11"],
              "SOL": ["2020-09-01", "2021-01-01", "2023-01-01", "2024-01-11"]}
    print("Spot D2 Fassung 2 - Verkauf beim KIPPEN der Ueberhitzung (Voranalyse_Spot §12.8)")
    stimmig = {}
    for sym in ("BTC", "ETH", "SOL"):
        print("\n%s (Ende %s)" % (sym, D.KURS[sym].index[-1].date()))
        print("  Fall  | (b) Stueck / H0 je Start %s | Verm. / H0 | Rueckgang (H0) | Geld am Ende | Verk./Rueckk." % "/".join(x[:7] for x in starts[sym]))
        h0 = {s: D.d2(sym, pd.Timestamp(s), None) for s in starts[sym]}
        for fall in ("K1", "K2", "K1_20", "K2_20"):
            sq, wq, rg, rg0, gl, vk, rk = [], [], [], [], [], 0, 0
            for s in starts[sym]:
                r, h = d2k(sym, pd.Timestamp(s), fall), h0[s]
                sq.append(r.attrs["stueck"] / h.attrs["stueck"][sym])
                wq.append((r["wert"].iloc[-1] + r["geld"].iloc[-1]) / h["wert"].iloc[-1])
                rg.append(D.max_rueckgang(r["wert"] + r["geld"], r["ein"])); rg0.append(D.max_rueckgang(h["wert"], h["ein"]))
                gl.append(r["geld"].iloc[-1] / r["ein"].iloc[-1]); vk += r.attrs["verk"]; rk += r.attrs["rueck"]
            ok_ = sum(x > 1 for x in sq) >= 2 / 3 * len(sq) and sq[-1] >= 0.95
            stimmig[(sym, fall)] = ok_
            print("  %-5s | %s | %s | %+.0f %% (%+.0f %%) | %3.0f %% | %d/%d%s" % (
                fall, " ".join("%.3f" % x for x in sq), " ".join("%.2f" % x for x in wq), 100 * np.median(rg), 100 * np.median(rg0),
                100 * np.median(gl), vk, rk, "   (Auskunft)" if "_20" in fall else ""))
        for fall in ("dK1", "dK2"):
            rel, ent = [], []
            for s in starts[sym]:
                r, h = d2k(sym, pd.Timestamp(s), fall), h0[s]
                rel.append((r["wert"].iloc[-1] + r["entn"].iloc[-1]) / h["wert"].iloc[-1]); ent.append(r["entn"].iloc[-1] / r["ein"].iloc[-1])
            print("  %-5s | (d) Rest + Entnahme / H0: %s | entnommen in %% des Eingezahlten: %s" % (
                fall, " ".join("%.2f" % x for x in rel), " ".join("%.0f %%" % (100 * x) for x in ent)))
        r = d2k(sym, pd.Timestamp(starts[sym][0]), "K2")
        print("  K2 Verkaeufe (Start %s): %s" % (starts[sym][0][:7], " · ".join(
            "%s Stufe %.2f Kurs %.0f" % (t.date(), s_, D.KURS[sym][t]) for t, s_, _g in r.attrs["gewinne"])))
    print("\nSTIMMIG (b) nach §12.3/§12.8 (Stueck > H0 bei BTC UND ETH in >= 2/3 der Starts, Start 2024 >= 0,95; SOL Auskunft):")
    for fall in ("K1", "K2"):
        print("  %s: BTC %s, ETH %s, SOL (Auskunft) %s -> %s" % (fall, *("ja" if stimmig[(s, fall)] else "nein" for s in ("BTC", "ETH", "SOL")),
                                                                "STIMMIG" if stimmig[("BTC", fall)] and stimmig[("ETH", fall)] else "nicht stimmig"))


if __name__ == "__main__":
    main()
