"""UEBERTRAGBARKEIT B1 (Spot §39.6, vorab festgelegt) - Mitnahme Z1 x3 auf dem GANZEN Bestandskreis statt nur den L-Kandidaten.

    python Basisinfos/Spot_Voranalyse_04_10/fb_uebertrag.py

Regel UNVERAENDERT aus §31 (fb_messung: l_regel, l_auswerten, l_null, urteil, boot) - keine neue Wahl, nur eine andere Grundgesamtheit:
  Teil 0  oberes Fuenftel (wie §31) muss +5,50 Pp ab 2024 wiedergeben, sonst Abbruch
  HAUPT   alle Watchlist-Coins des Starttags OHNE Kern (BTC, ETH, SOL) - so wie B1 im Betrieb gilt (E-90: alles ausser Kern ist L)
  Auskunft nur ausserhalb des oberen Fuenftels (der Teil, um den erweitert wird) · je Klasse · je Jahr
Urteil wie §31.3 (Korb > 0, Bootstrap >= 0,95, Rang >= 0,95, >= 20 Ausloesungen an >= 6 Starttagen; zweiseitig SCHADET); Selbsttest (a).
"""
import os
import sys

import numpy as np

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HIER)
os.chdir(os.path.dirname(os.path.dirname(HIER)))
import fb_messung as FB      # noqa: E402

K, POS, BTCV, M, MK, W = FB.K, FB.POS, FB.BTCV, FB.M, FB.MK, FB.W
KERN = {"BTC", "ETH", "SOL"}


def anker(menge):
    D = MK.paare_mw(365).reset_index(drop=True)
    Z = M.Zellen(D)
    D["fuenftel"] = M.pct_in_zelle(Z, W.wert(Z, M.merkmale(D))) > 0.8
    D = D[(D.t >= "2024-01-01")]
    if menge == "fuenftel":
        D = D[D.fuenftel & (D.sym != "BTC")]
    elif menge == "alle":
        D = D[~D.sym.isin(KERN)]
    else:
        D = D[~D.fuenftel & ~D.sym.isin(KERN)]
    pf = []
    for r in D.reset_index(drop=True).itertuples():
        i = POS[r.t]
        v = K[r.sym].values
        x = v[i + 1:i + 1 + 365]
        b = BTCV[i + 1:i + 1 + 365] / BTCV[i]
        ok = ~np.isnan(x)
        if not ok.all():
            x, b = x[:np.argmin(ok)], b[:np.argmin(ok)]
        lr = np.diff(np.log(v[i - 90:i + 1]))
        pf.append(dict(t=r.t, sym=r.sym, kl=r.kl, ep="U", x=x / v[i], b=b, sig=np.nanstd(lr) * np.sqrt(90)))
    return pf


def lauf(pf, name):
    df = FB.l_auswerten(pf, "Z1 x3")
    je = FB.korb(df, "d", "t")
    null = FB.l_null(pf, df)
    u = FB.urteil(je, null, int(df.aus.sum()), df[df.aus].t.nunique())
    a = df[df.aus]
    print("  %-28s Positionen %5d · ausgeloest %4d (%.1f %%) · Korb %+.2f Pp · Bootstrap %.2f · Rang %.2f -> %s · je Ausloesung Median %+.1f Pp, besser in %.0f %%" % (
        name, len(df), len(a), 100 * df.aus.mean(), 100 * u[1], u[2], u[3], u[0], 100 * a.d.median() if len(a) else float("nan"), 100 * (a.d > 0).mean() if len(a) else 0))
    return df, u


def main():
    print("UEBERTRAGBARKEIT B1 Mitnahme Z1 x3 (§39.6) · Kurse bis %s · ab 2024\n" % M.ENDE.date())
    df0, u0 = lauf(anker("fuenftel"), "Teil 0 oberes Fuenftel (§31)")
    if abs(100 * u0[1] - 5.50) > 0.01:
        print("TEIL 0 FEHLGESCHLAGEN - Abbruch"); return
    print("  -> Teil 0 bestanden (+5,50 Pp)\n\nHAUPT:")
    pf = anker("alle")
    df, u = lauf(pf, "ALLE ohne Kern (Betrieb)")
    fehl = 0
    for _ in range(100):
        zt = FB.l_auswerten(pf, "Z1 x3", verkauf=lambda a: (int(FB.RNG.integers(1, len(a["x"]))) if FB.RNG.random() < df.aus.mean() and len(a["x"]) > 1 else None))
        jz = FB.korb(zt, "d", "t")
        fehl += (jz.mean() > 0 and FB.boot(jz.sort_index().values, 300) >= 0.95 and np.mean(FB.l_null(pf, zt, nz=50) < jz.mean()) >= 0.95)
    print("  SELBSTTEST (a) Zufalls-Kriterium 100 Welten: Fehlalarm %d %% -> %s" % (fehl, "bestanden" if fehl <= 5 else "NICHT bestanden - Urteil gilt nicht"))
    print("\nAUSKUNFT:")
    lauf(anker("rest"), "nur AUSSERHALB oberes Fuenftel")
    print("  je Klasse: %s" % " · ".join("%s %+.1f Pp (ausgeloest %d)" % (k, 100 * FB.korb(g, "d", "t").mean(), int(g.aus.sum())) for k, g in df.groupby("kl")))
    print("  je Jahr: %s" % " · ".join("%d %+.1f Pp" % (j, 100 * FB.korb(g, "d", "t").mean()) for j, g in df.groupby(df.t.dt.year)))
    df.to_csv(os.path.join("data", "_spot", "fb_uebertrag.csv"), sep=";", index=False)


if __name__ == "__main__":
    main()
