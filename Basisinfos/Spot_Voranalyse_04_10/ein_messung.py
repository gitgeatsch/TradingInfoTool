"""MESSUNG Spot-Einstieg auf der Watchlist (Voranalyse_Spot_Neubau_04_10.md §29.2, vorab Commit 9700ad0) - nur lesend, keine Aufrufe.

    python Basisinfos/Spot_Voranalyse_04_10/ein_messung.py

Genau nach §29.2:
  Teil 0 (R-R11)  B5 X2 mit dem ALTEN Werkzeug (wl_messung.b5) nachrechnen: Korb nach Kosten E2 +31,8 %, E3 -4,0 % (Abweichung > 1 Pp -> Abbruch);
                  dazu: die Marke dieser Messung (ein_vorpruefung.ausstieg) liefert an JEDEM B5-Kauf denselben Ausstiegstag wie a2_messung.ausstieg('X2')
  Haupt E-b       Eintritt ins oberste Fuenftel bei Altseason-Breite >= 50 %, Ausstieg X2, Ertrag gegen BTC ueber dieselbe Haltedauer (brutto)
  Korb            je Stichtag Mittel seiner Einstiege, dann Mittel ueber die Stichtage
  Traegt (E3)     (1) Korb-Mittel > 0 und Block-Bootstrap ueber Stichtage (2.000, Bloecke zu 3) >= 0,95 ueber null; (2) Rang gegen die Zufallswelt
                  (gleiche Stichtage, gleich viele zufaellige Coins derselben Klasse, gleicher Ausstieg; 200) >= 0,95; (3) >= 20 Einstiege an >= 4 Stichtagen
                  fehlt (3) -> NICHT ENTSCHEIDBAR
  Selbsttest      (a) Zufalls-Tor: gleich viele offene Stichtage zufaellig, Einstiege = E-a an diesen Tagen, 100 Welten, (1)+(2) -> Fehlalarm <= 5 %
                  (b) gepflanzt: an den offenen Stichtagen gleich viele Coins MIT spaeterem Ertrag ueber BTC -> (1)+(2) muessen gelten
  Auskunft        E-a, E-c, A0, KL; E-b gegen E-a; je Klasse; Jahre; Weglassprobe ohne die 5 groessten Gewinner; realisiert >= x2 / <= -50 %;
                  X0 statt X2; netto (Coin 1,25 %, BTC 0,4 % je Seite wie B5)
"""
import os
import sys

import numpy as np
import pandas as pd

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HIER)
os.chdir(os.path.dirname(os.path.dirname(HIER)))
import a2_messung as A2     # noqa: E402
import as_messung as M      # noqa: E402
import ein_vorpruefung as EV  # noqa: E402
import mk_messung as MK     # noqa: E402
import wl_messung as W      # noqa: E402

K, IDX, POS, BTCV = M.K, M.IDX, M.POS, M.BTCV
RNG = np.random.default_rng(20261008)
KO, KB = 0.0125, 0.004


def x0(s, i0):
    v = K[s].values
    ende = min(i0 + 365, len(v) - 1)
    if ende - i0 < 365:
        return None
    w = v[i0:ende + 1]
    ok = ~np.isnan(w)
    j = (np.argmin(ok) - 1) if not ok.all() else len(w) - 1
    return w[j] / w[0] - 1, BTCV[i0 + j] / BTCV[i0] - 1, j, "365 T" if ok.all() else "eingestellt"


def korb(x):
    return x.groupby("t").ex.mean()


def boot(je_t, n=2000):
    vals = je_t.sort_index().values
    if len(vals) < 2:
        return float("nan")
    bs = []
    for _ in range(n):
        st = RNG.integers(0, max(len(vals) - 2, 1), size=int(np.ceil(len(vals) / 3)))
        bs.append(np.concatenate([vals[k:k + 3] for k in st])[:len(vals)].mean())
    return float(np.mean(np.array(bs) > 0))


def main():
    # ---------------- Teil 0
    Dw = M.paare(365).reset_index(drop=True)
    Zw = M.Zellen(Dw)
    ww = W.wert(Zw, M.merkmale(Dw))
    V0 = M.pct_in_zelle(Zw, ww) > 0.8
    RANG = W.monatsrang()
    B = W.b5(Dw, V0, RANG)
    b2 = B[B.regel == "X2"]
    k0 = {e: b2[b2.ep == e].groupby("t").r.mean().mean() for e in ("E2", "E3")}
    print("MESSUNG Spot-Einstieg (§29.2) · Kurse bis %s\n\nTEIL 0 (R-R11) B5 X2 mit wl_messung.b5: Korb E2 %+.1f %% · E3 %+.1f %% (Soll +31,8 / -4,0)" % (
        M.ENDE.date(), 100 * k0["E2"], 100 * k0["E3"]))
    if abs(100 * k0["E2"] - 31.8) > 1 or abs(100 * k0["E3"] + 4.0) > 1:
        print("REPRODUKTION FEHLGESCHLAGEN - Abbruch"); return
    gleich = tot = 0
    for r in b2.itertuples():
        v, b = A2.pfad(r.sym, POS[r.t] + 1, 365)
        alt = A2.ausstieg(v, "X2")[0][0]
        neu = EV.ausstieg(r.sym, POS[r.t] + 1)
        tot += 1
        gleich += neu is not None and neu[2] == alt
    print("  Ausstiegstag der Marke dieser Messung = a2_messung.ausstieg('X2') an %d von %d B5-Kaeufen" % (gleich, tot))
    if gleich < tot:
        print("  ⚠️ ABWEICHUNG der Ausstiegsumsetzung - Abbruch"); return

    # ---------------- Anker, Arme
    D = MK.paare_mw(365).reset_index(drop=True)
    Z = M.Zellen(D)
    w = W.wert(Z, M.merkmale(D))
    D["fuenftel"] = M.pct_in_zelle(Z, w) > 0.8
    vor = {(t + pd.DateOffset(months=1), s): f for t, s, f in zip(D.t, D.sym, D.fuenftel)}
    D["eintritt"] = D.fuenftel & ~np.array([vor.get((t, s), False) for t, s in zip(D.t, D.sym)])
    D["breite"] = D.t.map({t: EV.breite(t) for t in D.t.unique()})
    zeilen = []
    for r in D.itertuples():
        i0 = POS[r.t] + 1
        a2, a0 = EV.ausstieg(r.sym, i0), x0(r.sym, i0)
        arme = ["KL"] + (["A0"] if r.fuenftel else []) + (["E-a"] if r.eintritt else []) + (["E-b"] if r.eintritt and r.breite >= 0.5 else [])
        for arm in arme:
            if a2 is not None:
                zeilen.append((arm, "X2", r.ep, r.kl, r.t, r.sym) + a2)
            if a0 is not None and arm in ("E-b", "A0"):
                zeilen.append((arm, "X0", r.ep, r.kl, r.t, r.sym) + a0)
        if r.eintritt:
            j = EV.rs_einstieg(r.sym, POS[r.t])
            a = EV.ausstieg(r.sym, j) if j is not None else None
            if a is not None:
                zeilen.append(("E-c", "X2", r.ep, r.kl, r.t, r.sym) + a)
    R = pd.DataFrame(zeilen, columns=["arm", "aus", "ep", "kl", "t", "sym", "r", "rb", "tage", "grund"])
    R["ex"] = (1 + R.r) / (1 + R.rb) - 1
    R["ex_netto"] = (1 + R.r) * (1 - KO) / (1 + KO) / ((1 + R.rb) * (1 - KB) / (1 + KB)) - 1
    KLX = R[(R.arm == "KL") & (R.aus == "X2")]
    pool = {(t, k): g.ex.values for (t, k), g in KLX.groupby(["t", "kl"])}

    def zufall(x, nz=200):
        out = []
        for _ in range(nz):
            m = []
            for t, g in x.groupby("t"):
                vals = []
                for k, gg in g.groupby("kl"):
                    p = pool.get((t, k))
                    if p is not None and len(p):
                        vals += list(RNG.choice(p, size=len(gg), replace=len(p) < len(gg)))
                if vals:
                    m.append(np.mean(vals))
            out.append(np.mean(m) if m else np.nan)
        return np.array(out)

    def urteil(x, mit3=True):
        jt = korb(x)
        b = boot(jt)
        z = zufall(x)
        rang = float(np.mean(z < jt.mean())) if len(jt) else float("nan")
        e12 = len(jt) > 0 and jt.mean() > 0 and b >= 0.95 and rang >= 0.95
        e3 = len(x) >= 20 and x.t.nunique() >= 4
        return e12, e3, jt, b, rang

    print("\nHAUPT-HYPOTHESE E-b (Eintritt ins Fuenftel bei Altseason-Breite >= 50 %, Ausstieg X2, gegen BTC)")
    eb = R[(R.arm == "E-b") & (R.aus == "X2")]
    erg = {}
    for ep in ("E2", "E3"):
        x = eb[eb.ep == ep]
        e12, e3, jt, b, rang = urteil(x)
        erg[ep] = (e12, e3)
        print("  %s Einstiege %d an %d Stichtagen · Korb %+.1f %% (Median der Koerbe %+.1f %%) · Bootstrap %.2f · Zufallswelt-Rang %.2f · netto %+.1f %% · "
              "realisiert >= x2 %d %% / <= -50 %% %d %% · Haltedauer Median %d T" % (
                  ep, len(x), x.t.nunique(), 100 * jt.mean(), 100 * jt.median(), b, rang, 100 * x.groupby("t").ex_netto.mean().mean(),
                  100 * (x.r >= 1).mean(), 100 * (x.r <= -0.5).mean(), x.tage.median()))
    e12, e3 = erg["E3"]
    print("  -> URTEIL (vorab, E3): %s" % ("TRAEGT" if (e12 and e3) else ("NICHT ENTSCHEIDBAR (zu wenige Faelle/Stichtage)" if not e3 else "TRAEGT NICHT")))

    print("\nSELBSTTEST (nur Bedingungen 1+2, E3)")
    x3 = R[(R.arm == "E-a") & (R.aus == "X2") & (R.ep == "E3")]
    offen = eb[eb.ep == "E3"].t.nunique()
    tage3 = np.array(sorted(x3.t.unique()))
    fehl = 0
    for _ in range(100):
        wahl = RNG.choice(tage3, size=min(offen, len(tage3)), replace=False) if len(tage3) else []
        e12z = urteil(x3[x3.t.isin(wahl)])[0] if len(wahl) else False
        fehl += bool(e12z)
    print("  (a) Zufalls-Tor (%d offene Stichtage zufaellig), 100 Welten: Fehlalarm %d %% (Soll <= 5 %%) -> %s" % (
        offen, fehl, "bestanden" if fehl <= 5 else "NICHT bestanden"))
    k3 = KLX[(KLX.ep == "E3") & KLX.t.isin(eb[eb.ep == "E3"].t.unique())]
    gut = k3[k3.ex > 0]
    n_eb = len(eb[eb.ep == "E3"])
    je = max(1, int(round(n_eb / max(offen, 1))))
    pf = pd.concat([g.sample(min(len(g), je), random_state=1) for _, g in gut.groupby("t")]) if len(gut) else gut
    e12p = urteil(pf)[0] if len(pf) else False
    print("  (b) gepflanzt (%d Coins mit spaeterem Ertrag ueber BTC an den offenen Stichtagen): %s" % (len(pf), "erkannt (bestanden)" if e12p else "NICHT erkannt"))

    print("\nAUSKUNFT - alle Arme (Ausstieg X2), Korb gegen BTC je Epoche:")
    for arm in ("KL", "A0", "E-a", "E-b", "E-c"):
        teile = []
        for ep in ("E2", "E3"):
            x = R[(R.arm == arm) & (R.aus == "X2") & (R.ep == ep)]
            if len(x):
                jt = korb(x)
                teile.append("%s n %5d · Korb %+6.1f %% · Bootstrap %.2f · Anteil > BTC %3.0f %%" % (ep, len(x), 100 * jt.mean(), boot(jt, 500), 100 * (x.ex > 0).mean()))
        print("  %-4s %s" % (arm, " | ".join(teile)))
    print("  X0 (12 Monate halten) statt X2: %s" % " | ".join(
        "%s %s Korb %+.1f %%" % (arm, ep, 100 * korb(R[(R.arm == arm) & (R.aus == "X0") & (R.ep == ep)]).mean())
        for arm in ("E-b", "A0") for ep in ("E2", "E3") if len(R[(R.arm == arm) & (R.aus == "X0") & (R.ep == ep)])))
    for ep in ("E2", "E3"):
        x = eb[eb.ep == ep]
        if not len(x):
            continue
        print("  E-b %s je Klasse: %s" % (ep, " · ".join("%s n %d %+.1f %%" % (k, len(g), 100 * korb(g).mean()) for k, g in x.groupby("kl"))))
        print("  E-b %s je Jahr: %s" % (ep, " · ".join("%d n %d %+.1f %%" % (j, len(g), 100 * korb(g).mean()) for j, g in x.groupby(x.t.dt.year))))
        top5 = x.sort_values("ex", ascending=False).sym.head(5).tolist()
        xw = x[~x.sym.isin(top5)]
        print("  E-b %s Weglassprobe ohne %s: Korb %+.1f %%" % (ep, ",".join(top5), 100 * korb(xw).mean() if len(xw) else float("nan")))
        ea = R[(R.arm == "E-a") & (R.aus == "X2") & (R.ep == ep)]
        print("  E-b gegen E-a %s: %+.1f Pp (Korb E-a %+.1f %%)" % (ep, 100 * (korb(x).mean() - korb(ea).mean()), 100 * korb(ea).mean()))
    R.to_csv(os.path.join("data", "_spot", "ein_messung_anker.csv"), sep=";", index=False)


if __name__ == "__main__":
    main()
