"""LAGEBILD Altcoins 2023 bis heute (Voranalyse_Spot §30.1) - reine BESCHREIBUNG, kein Test, nur lesend, keine Aufrufe.

    python Basisinfos/Spot_Voranalyse_04_10/lage_e3.py

Nutzer 08.10.2026: 2021 als Massstab war immer problematisch; das System muss an 2024 bis heute angepasst werden. Der Altcoin-Markt ist im
Abstiegstrend, zwischen den BTC-Anstiegen brechen einzelne Altcoins aus; Annahme: es braucht positive Phasen bzw. eine Altseason, und nicht
alles steigt - die Diamanten muessen identifiziert werden.

Grundgesamtheit wie die Watchlist (mk_messung.klassen_mw: Marktwert-Klassen H/M/S, eingestellte Coins eingeschlossen), monatliche Stichtage
2023-01 bis zum letzten Stichtag mit abgeschlossenem 180-T-Fenster. 2023 = Trainingsjahr (Auskunft), Urteilszeitraum ab 2024.
  L1  Markt je Halbjahr: BTC-Ertrag, Altseason-Breite (Anteil Stichtage >= 50 %), Altcoin-Index gegen BTC (gleich- und marktwertgewichtet, Top 100)
  L2  AUSBRUCH (Diamant) = Coin verdoppelt sich GEGEN BTC binnen 180 T nach dem Stichtag (Hoch des Verhaeltnisses Coin/BTC >= x2)
      Haeufigkeit je Stichtag und Klasse; was davon nach 180 T noch da ist; Rueckgabe vom Hoch
  L3  Lage am Stichtag (vorab bekannt): BTC 90 T steigend/fallend x Breite offen/zu -> Ausbruchsquote; dazu BTC im Fenster (RUECKSCHAU)
  L4  Waren die Ausbrecher vorab in der Watchlist? Lift des obersten Fuenftels (Kombination auf E2 gewaehlt -> hier ausserhalb der Wahl)
  L5  Was haelt die Fuehrung X2 vom Ausbruch? (Ertrag gegen BTC bis zum Ausstieg ueber die Marke, Anteil am Hoch)
"""
import os
import sys

import numpy as np
import pandas as pd

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HIER)
os.chdir(os.path.dirname(os.path.dirname(HIER)))
import as_messung as M      # noqa: E402
import ein_vorpruefung as EV  # noqa: E402
import mk_messung as MK     # noqa: E402
import wl_messung as W      # noqa: E402

K, IDX, POS, BTCV = M.K, M.IDX, M.POS, M.BTCV
H = 180


def rel_pfad(s, i0):
    v = K[s].values[i0:i0 + H + 1]
    if np.isnan(v[0]):
        return None
    ok = ~np.isnan(v)
    if not ok.all():
        v = v[:np.argmin(ok)]
    b = BTCV[i0:i0 + len(v)]
    return (v / v[0]) / (b / b[0])


def halbjahr(t):
    return "%d-H%d" % (t.year, 1 if t.month <= 6 else 2)


def main():
    stich = [t for t in pd.date_range("2023-01-01", M.ENDE, freq="MS") if t in POS and POS[t] + 1 + H <= len(IDX) - 1]
    zeilen, markt = [], []
    stich_markt = [t for t in pd.date_range("2023-01-01", M.ENDE, freq="MS") if t in POS and POS[t] + 30 <= len(IDX) - 1]   # L1 braucht nur 30 T
    for t in stich_markt:
        kl, _, _ = MK.klassen_mw(t)
        _, rg = MK.rang_mw(t)
        i = POS[t]
        top = [s for s in rg.sort_values().index[:101] if s != "BTC"][:100]
        mw = {s: MK.umlauf(s, t) * K[s].values[i] for s in top}
        r30 = {s: K[s].values[i + 30] / K[s].values[i] - 1 for s in top if i + 30 < len(IDX) and K[s].values[i + 30] == K[s].values[i + 30]}
        b30 = BTCV[i + 30] / BTCV[i] - 1
        gl = np.mean([(1 + r) / (1 + b30) - 1 for r in r30.values()])
        gew = sum(mw[s] * ((1 + r) / (1 + b30) - 1) for s, r in r30.items()) / sum(mw[s] for s in r30)
        markt.append(dict(t=t, btc30=b30, btc90_vor=BTCV[i] / BTCV[i - 90] - 1, breite=EV.breite(t), alt_gl=gl, alt_mw=gew))
        if t not in stich:
            continue
        for s, k in kl.items():
            if s == "BTC":
                continue
            p = rel_pfad(s, i + 1)
            if p is None or len(p) < 2:
                continue
            j = int(np.argmax(p))
            a = EV.ausstieg(s, i + 1, max_t=H)           # gleiches Fenster wie das Hoch (180 T); KORREKTUR 08.10. vor der Auswertung
            zeilen.append(dict(t=t, sym=s, kl=k, alter=(t - M.G["ERST"][s]).days, hoch=p.max() - 1, ende=p[-1] - 1, tag_hoch=j, eingestellt=len(p) < H + 1,
                               x2=(1 + a[0]) / (1 + a[1]) - 1 if a else np.nan, btc_fenster=BTCV[i + H] / BTCV[i + 1] - 1))
    L = pd.DataFrame(markt)
    R = pd.DataFrame(zeilen)
    R["aus"] = R.hoch >= 1.0
    L["hj"] = L.t.map(halbjahr)
    R["hj"] = R.t.map(halbjahr)
    R = R.merge(L[["t", "btc90_vor", "breite"]], on="t")

    print("LAGEBILD Altcoins 2023 bis heute · Kurse bis %s · Markt (L1) %s bis %s · Ausbrueche (L2-L5, 180-T-Fenster) %s bis %s (%d) · Coin-Stichtage %d\n" % (
        M.ENDE.date(), stich_markt[0].date(), stich_markt[-1].date(), stich[0].date(), stich[-1].date(), len(stich), len(R)))
    print("L1 MARKT je Halbjahr (Monatswerte; Altcoin-Index = Top 100 nach Marktwert ohne BTC, 30-T-Ertrag GEGEN BTC je Monat)")
    print("  Halbjahr  BTC-Ertrag  Breite>=50%%  Altindex gleichgew.  marktwertgew.  (Summe der Monate, verkettet)")
    for hj, g in L.groupby("hj"):
        print("  %s   %+7.1f %%   %3d von %d    %+7.1f %%            %+7.1f %%" % (
            hj, 100 * (np.prod(1 + g.btc30) - 1), int((g.breite >= 0.5).sum()), len(g), 100 * (np.prod(1 + g.alt_gl) - 1), 100 * (np.prod(1 + g.alt_mw) - 1)))
    ab24 = L[L.t >= "2024-01-01"]
    print("  ab 2024 gesamt: BTC %+.0f %% · Altindex gegen BTC gleichgew. %+.0f %% / marktwertgew. %+.0f %% · Breite offen an %d von %d Stichtagen" % (
        100 * (np.prod(1 + ab24.btc30) - 1), 100 * (np.prod(1 + ab24.alt_gl) - 1), 100 * (np.prod(1 + ab24.alt_mw) - 1), int((ab24.breite >= 0.5).sum()), len(ab24)))
    i0, i1 = POS[ab24.t.iloc[0]], POS[ab24.t.iloc[-1]] + 30
    print("  Kern ausserhalb des Universums (Auskunft): %s" % " · ".join("%s/BTC %+.0f %%" % (s, 100 * ((K[s].values[i1] / K[s].values[i0]) / (BTCV[i1] / BTCV[i0]) - 1))
                                                                       for s in ("ETH", "SOL") if s in K.columns))

    print("\nL2 AUSBRUECHE (Coin/BTC binnen 180 T >= x2) - die 'Diamanten'")
    for hj, g in R.groupby("hj"):
        a = g[g.aus]
        print("  %s  %4d Coin-Stichtage · Ausbrueche %3d (%4.1f %%) · Coins %3d · H/M/S %d/%d/%d · nach 180 T noch >= x2: %3.0f %% · Median-Rueckgabe vom Hoch %3.0f %%" % (
            hj, len(g), len(a), 100 * len(a) / len(g), a.sym.nunique(), (a.kl == "H").sum(), (a.kl == "M").sum(), (a.kl == "S").sum(),
            100 * (a.ende >= 1).mean() if len(a) else 0, 100 * np.median(1 - (1 + a.ende) / (1 + a.hoch)) if len(a) else 0))
    for nm, g in (("2023 (Training)", R[R.t < "2024-01-01"]), ("ab 2024", R[R.t >= "2024-01-01"])):
        a = g[g.aus]
        print("  %-16s Ausbruchsquote %.1f %% (H %.1f · M %.1f · S %.1f %%) · %d verschiedene Coins · Hoch nach Median %d T · eingestellt unter den Ausbrechern %d" % (
            nm, 100 * g.aus.mean(), *(100 * g[g.kl == k].aus.mean() for k in "HMS"), a.sym.nunique(), int(a.tag_hoch.median()) if len(a) else 0, int(a.eingestellt.sum())))
    a24 = R[(R.t >= "2024-01-01") & R.aus]
    g24a = R[R.t >= "2024-01-01"]
    print("  ab 2024 nach Alter am Stichtag: < 1 Jahr Quote %.1f %% (%d Coin-Stichtage) · >= 1 Jahr %.1f %% · Anteil junger Coins unter den Ausbrechern %.0f %%" % (
        100 * g24a[g24a.alter < 365].aus.mean(), (g24a.alter < 365).sum(), 100 * g24a[g24a.alter >= 365].aus.mean(), 100 * (a24.alter < 365).mean()))
    top = a24.groupby("sym").hoch.max().sort_values(ascending=False).head(15)
    print("  groesste ab 2024 (Hoch gegen BTC): %s" % " · ".join("%s x%.1f" % (s, 1 + h) for s, h in top.items()))

    print("\nL3 LAGE am Stichtag (vorab bekannt) -> Ausbruchsquote ab 2024")
    g24 = R[R.t >= "2024-01-01"].copy()
    g24["btc_lage"] = np.where(g24.btc90_vor > 0, "BTC 90T steigt", "BTC 90T faellt")
    g24["phase"] = np.where(g24.breite >= 0.5, "Breite offen", "Breite zu")
    for (b, p), g in g24.groupby(["btc_lage", "phase"]):
        print("  %-15s %-13s Stichtage %2d · Quote %4.1f %% · Median Ende gegen BTC %+5.1f %%" % (b, p, g.t.nunique(), 100 * g.aus.mean(), 100 * g.ende.median()))
    g24["btc_fw"] = pd.cut(g24.btc_fenster, [-1, -0.1, 0.1, 10], labels=["BTC im Fenster < -10 %", "BTC -10..+10 %", "BTC > +10 %"])
    for b, g in g24.groupby("btc_fw", observed=True):
        print("  RUECKSCHAU %-24s Stichtage %2d · Quote %4.1f %%" % (b, g.t.nunique(), 100 * g.aus.mean()))
    q = g24.groupby("t").aus.mean()
    print("  Quote je Stichtag ab 2024: Median %.1f %% · hoechste %s" % (100 * q.median(), " · ".join("%s %.0f %%" % (t.date(), 100 * v) for t, v in q.sort_values(ascending=False).head(5).items())))

    print("\nL4 WAREN DIE AUSBRECHER VORAB IN DER WATCHLIST? (oberstes Fuenftel am Stichtag; Kombination auf E2 gewaehlt)")
    D = MK.paare_mw(H).reset_index(drop=True)
    Z = M.Zellen(D)
    D["fuenftel"] = M.pct_in_zelle(Z, W.wert(Z, M.merkmale(D))) > 0.8
    X = R.merge(D[["t", "sym", "fuenftel"]], on=["t", "sym"], how="left")
    for nm, g in (("2023 (Training)", X[X.t < "2024-01-01"]), ("ab 2024", X[X.t >= "2024-01-01"])):
        g = g[g.fuenftel.notna()]
        f = g.fuenftel.astype(bool)
        print("  %-16s Quote im Fuenftel %.1f %% gegen ausserhalb %.1f %% (Lift %.2f) · Anteil der Ausbrecher, die im Fuenftel waren %.0f %% (Fuenftel = %.0f %% der Coins)" % (
            nm, 100 * g[f].aus.mean(), 100 * g[~f].aus.mean(), g[f].aus.mean() / max(g[~f].aus.mean(), 1e-9), 100 * f[g.aus].mean(), 100 * f.mean()))
        for k in "HMS":
            gk = g[g.kl == k]
            fk = gk.fuenftel.astype(bool)
            if fk.sum() and (~fk).sum():
                print("      %s: im Fuenftel %.1f %% · ausserhalb %.1f %%" % (k, 100 * gk[fk].aus.mean(), 100 * gk[~fk].aus.mean()))

    print("\nL5 WAS HAELT DIE FUEHRUNG X2 VOM AUSBRUCH? (ab 2024, Ertrag gegen BTC bis Ausstieg ueber die Marke)")
    a = R[(R.t >= "2024-01-01")]
    for nm, g in (("Ausbrecher", a[a.aus]), ("alle uebrigen", a[~a.aus]), ("alle", a)):
        g = g[g.x2.notna()]
        print("  %-14s n %4d · X2 gegen BTC Median %+6.1f %% / Mittel %+6.1f %% · > BTC %3.0f %% · Halten 180 T Median %+6.1f %% / Mittel %+6.1f %% · Hoch Median %+6.1f %% · Vielfaches gehalten (1+X2)/(1+Hoch) Median %.2f" % (
            nm, len(g), 100 * g.x2.median(), 100 * g.x2.mean(), 100 * (g.x2 > 0).mean(), 100 * g.ende.median(), 100 * g.ende.mean(), 100 * g.hoch.median(),
            np.median((1 + g.x2) / (1 + g.hoch))))
    X.to_csv(os.path.join("data", "_spot", "lage_e3_anker.csv"), sep=";", index=False)   # R samt Fuenftel (fuer die Gegenprobe)
    L.to_csv(os.path.join("data", "_spot", "lage_e3_markt.csv"), sep=";", index=False)


if __name__ == "__main__":
    main()
