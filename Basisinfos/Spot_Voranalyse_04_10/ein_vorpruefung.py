"""Vorpruefung SPOT-EINSTIEG auf der Watchlist (Voranalyse_Spot_Neubau_04_10.md §29, Stufe 1) - nur lesend, keine Aufrufe.

    python Basisinfos/Spot_Voranalyse_04_10/ein_vorpruefung.py

ZWECK: vor dem Messplan klaeren, ob die Einstiegsregeln GENUG Faelle haben und in der WAHL-Epoche E2 in die erwartete Richtung zeigen.
E3 bleibt fuer die Bestaetigung UNBERUEHRT: von E3 werden nur ANZAHLEN ausgegeben, keine Ergebnisse.

Grundlage wie die Watchlist (§25.6): Marktwert-Klassen (mk_messung.paare_mw), Kombination F1 unten, F2 oben, F8 oben, F9 oben
(wl_messung.wert), oberes Fuenftel = Perzentil in der Zelle > 0,8. Monatliche Stichtage, Kauf zum Schluss des Folgetags.
  A0   im Fuenftel (jeder Stichtag)                       = was die Monatsmail heute als Liste zeigt
  E-a  Eintritt ins Fuenftel (am Vormonat nicht darin)
  E-b  E-a und Phase-Tor: Altseason-Breite >= 50 % (Anteil der 50 groessten Altcoins mit 90-T-Ertrag ueber BTC)
  E-c  E-a und Relativstaerke: erster Tag binnen 60 T, an dem der 30-T-Ertrag des Coins ueber dem von BTC liegt; Kauf am Folgetag
  KL   alle Coins der Zelle (Vergleich: Kauf irgendeines Coins der Klasse)
Ausstieg: Marke (Schluss unter max(0,65 x Hoch seit Kauf; 0,5 x Kauf) -> Verkauf zum Schluss des Folgetags) oder nach 365 T; eingestellt ->
letzter Kurs. Zielgroesse: Ertrag gegen BTC ueber DIESELBE Haltedauer = (1+r_coin)/(1+r_BTC) - 1 (brutto; Kosten beiderseits gleich).
"""
import os
import sys

import numpy as np
import pandas as pd

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HIER)
os.chdir(os.path.dirname(os.path.dirname(HIER)))
import as_messung as M      # noqa: E402
import mk_messung as MK     # noqa: E402
import wl_messung as W      # noqa: E402

K, IDX, POS, BTCV = M.K, M.IDX, M.POS, M.BTCV


def ausstieg(s, i0, max_t=365):
    """(Ertrag, BTC-Ertrag, Haltetage, Grund) ab Kauf zum Schluss i0."""
    v = K[s].values
    if i0 >= len(v) or np.isnan(v[i0]):
        return None
    k0, hoch = v[i0], v[i0]
    ende = min(i0 + max_t, len(v) - 1)
    j = i0
    while j < ende:
        j += 1
        if np.isnan(v[j]):                                  # eingestellt: letzter Kurs
            j -= 1
            return v[j] / k0 - 1, BTCV[j] / BTCV[i0] - 1, j - i0, "eingestellt"
        hoch = max(hoch, v[j])
        if v[j] < max(0.65 * hoch, 0.5 * k0) and j + 1 <= len(v) - 1 and not np.isnan(v[j + 1]):
            return v[j + 1] / k0 - 1, BTCV[j + 1] / BTCV[i0] - 1, j + 1 - i0, "marke"
    if j - i0 < max_t:
        return None                                         # Fenster noch offen
    return v[j] / k0 - 1, BTCV[j] / BTCV[i0] - 1, j - i0, "365 T"


def breite(t):
    kl, r = MK.rang_mw(t)
    top = [s for s in r.sort_values().index[:50] if s != "BTC"]
    i = POS[t]
    b90 = BTCV[i] / BTCV[i - 90] - 1
    x = [K[s].values[i] / K[s].values[i - 90] - 1 for s in top if K[s].values[i - 90] > 0]
    return np.mean([a > b90 for a in x]) if x else np.nan


def rs_einstieg(s, i, frist=60):
    v = K[s].values
    for j in range(i, min(i + frist, len(v) - 2)):
        if j >= 30 and v[j - 30] > 0 and not np.isnan(v[j]):
            if v[j] / v[j - 30] - 1 > BTCV[j] / BTCV[j - 30] - 1:
                return j + 1
    return None


def main():
    D = MK.paare_mw(365).reset_index(drop=True)
    Z = M.Zellen(D)
    F = M.merkmale(D)
    w = W.wert(Z, F)
    p = M.pct_in_zelle(Z, w)
    D["fuenftel"] = p > 0.8
    vor = {(t + pd.DateOffset(months=1), s): f for t, s, f in zip(D.t, D.sym, D.fuenftel)}
    D["eintritt"] = D.fuenftel & ~np.array([vor.get((t, s), False) for t, s in zip(D.t, D.sym)])
    BR = {t: breite(t) for t in D.t.unique()}
    D["breite"] = D.t.map(BR)
    zeilen = []
    for r in D.itertuples():
        i0 = POS[r.t] + 1
        arme = ["KL"] + (["A0"] if r.fuenftel else []) + (["E-a"] if r.eintritt else []) + (["E-b"] if r.eintritt and r.breite >= 0.5 else [])
        a = ausstieg(r.sym, i0)
        if a is not None:
            for arm in arme:
                zeilen.append((arm, r.ep, r.kl, r.t, r.sym) + a)
        if r.eintritt:
            j = rs_einstieg(r.sym, POS[r.t])
            if j is not None:
                a = ausstieg(r.sym, j)
                if a is not None:
                    zeilen.append(("E-c", r.ep, r.kl, r.t, r.sym) + a)
    R = pd.DataFrame(zeilen, columns=["arm", "ep", "kl", "t", "sym", "r", "rb", "tage", "grund"])
    R["ex"] = (1 + R.r) / (1 + R.rb) - 1
    print("VORPRUEFUNG Spot-Einstieg (§29, Stufe 1) · Kurse bis %s · Stichtage %d · Coin-Anker %d" % (M.ENDE.date(), D.t.nunique(), len(D)))
    print("Altseason-Breite je Epoche (Mittel, Anteil Stichtage >= 50 %%): %s\n" % " · ".join(
        "%s %.0f %% / %.0f %%" % (e, 100 * D[D.ep == e].groupby("t").breite.first().mean(), 100 * (D[D.ep == e].groupby("t").breite.first() >= 0.5).mean())
        for e in ("E2", "E3")))
    print("ANZAHL Einstiege (abgeschlossene Fenster) je Arm, Epoche und Klasse - E3 NUR ANZAHL:")
    print(R.groupby(["arm", "ep", "kl"]).size().unstack(["ep", "kl"]).fillna(0).astype(int).to_string())
    print("\nE2 (WAHL-Epoche) - Ertrag gegen BTC ueber dieselbe Haltedauer:")
    e2 = R[R.ep == "E2"]
    for arm in ("KL", "A0", "E-a", "E-b", "E-c"):
        x = e2[e2.arm == arm]
        if len(x) == 0:
            print("  %-4s -" % arm); continue
        mo = x.groupby(x.t.dt.to_period("M")).ex.mean()
        print("  %-4s n %4d · Mittel %+6.1f %% · Median %+6.1f %% · Anteil > BTC %3.0f %% · Monatsmittel > 0 in %d von %d Monaten · "
              "Ausstieg Marke %2.0f %% / 365 T %2.0f %% / eingestellt %2.0f %% · Haltedauer Median %d T" % (
                  arm, len(x), 100 * x.ex.mean(), 100 * x.ex.median(), 100 * (x.ex > 0).mean(), int((mo > 0).sum()), len(mo),
                  100 * (x.grund == "marke").mean(), 100 * (x.grund == "365 T").mean(), 100 * (x.grund == "eingestellt").mean(), int(x.tage.median())))
    print("  je Klasse (Mittel / Median gegen BTC):")
    for arm in ("KL", "A0", "E-a", "E-b", "E-c"):
        print("    %-4s %s" % (arm, " · ".join("%s n %d %+5.1f / %+5.1f %%" % (k, len(g), 100 * g.ex.mean(), 100 * g.ex.median())
                                            for k, g in e2[e2.arm == arm].groupby("kl"))))
    R.to_csv(os.path.join("data", "_spot", "ein_vorpruefung_anker.csv"), sep=";", index=False)


if __name__ == "__main__":
    main()
