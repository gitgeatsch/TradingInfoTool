"""MESSUNG K-3 "Ruhiger Boden" (Spot §40.2, vorab Commit 2150ba7) - nur lesend, keine Aufrufe.

    python Basisinfos/Spot_Voranalyse_04_10/k3_messung.py

Signal: Schwankung 90 T UND Tiefe je im unteren Fuenftel des Tagesquerschnitts; Kauf d+1; Zeitgrenze 30 T; EINE Sperre je Coin ueber
alle Klassen (einstiege_alle); gegen BTC brutto; Korb je Monat; Haupt-Hypothese ALLE Klassen gemeinsam; Schwelle 0,975; Nullwelt je
Einstieg ein zufaelliger Coin DERSELBEN Klasse ohne Signal am selben Tag (200); Spiegel; Mindestzahl; Selbsttest; Kosten je Klasse.
"""
import os
import sqlite3
import sys

import numpy as np
import pandas as pd

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HIER)
os.chdir(os.path.dirname(os.path.dirname(HIER)))
import fb_messung as FB      # noqa: E402
import k37_machbarkeit as KM  # noqa: E402
import k37_messung as K37     # noqa: E402
import k3_machbarkeit as K3M  # noqa: E402
import tc_vorpruefung as T    # noqa: E402

K, IDX, BTCV = T.K, T.IDX, T.BTCV
RNG = np.random.default_rng(20261040)
KOSTEN = {"H": 0.0072, "M": 0.0176, "S": 0.064}
SCHWELLE = 0.975


def kandidaten(E, sig, kl, m):
    out = {}
    for (d, k), _ in E.groupby(["signal", "kl"]):
        i = IDX.get_loc(d)
        z = (kl.loc[d] == k) & m.loc[d] & ~(sig.loc[d] >= 0.8) & K.iloc[i + 1].notna()
        out[(d, k)] = list(z.index[z.values])
    return out


def vorrat(E, kand):
    v = {}
    for (d, k), g in E.groupby(["signal", "kl"]):
        r = g.iloc[0]
        v[(d, k)] = np.array([K37.ex(s, r.i_kauf, r.i_aus) for s in kand[(d, k)]])
    return v


def nullwelt(E, vor, nz=200):
    je = E.groupby(["signal", "kl"]).size()
    out = []
    for _ in range(nz):
        w = {}
        for (d, k), n in je.items():
            x = vor[(d, k)]
            if len(x):
                w.setdefault(d.to_period("M"), []).extend(RNG.choice(x, size=n, replace=len(x) < n))
        out.append(np.mean([np.mean(x) for x in w.values()]))
    return np.array(out)


def spiegel(E, kand, up, down):
    l_n = a_n = g = 0.0
    for (d, k), gg in E.groupby(["signal", "kl"]):
        ks = kand[(d, k)]
        if not ks:
            continue
        i = gg.iloc[0].i_kauf
        cols = [up.columns.get_loc(s) for s in ks]
        l_n += len(gg) * up.iloc[i, cols].astype(float).mean()
        a_n += len(gg) * down.iloc[i, cols].astype(float).mean()
        g += len(gg)
    return (E.lauf.mean() / max(E.absturz.mean(), 1e-9)) / ((l_n / g) / max(a_n / g, 1e-9)), l_n / g, a_n / g


def urteil(E, kand, up, down, nz=200):
    jk = K37.korb(E)
    b = K37.boot(jk.values)
    nl = nullwelt(E, vorrat(E, kand), nz)
    rang = float(np.mean(nl < jk.mean()))
    sp = spiegel(E, kand, up, down)
    if not (len(E) >= 20 and E.mon.nunique() >= 6):
        u = "NICHT ENTSCHEIDBAR"
    elif jk.mean() > 0 and b >= SCHWELLE and rang >= SCHWELLE and sp[0] > 1:
        u = "TRAEGT"
    elif jk.mean() < 0 and b <= 1 - SCHWELLE:
        u = "SCHADET"
    else:
        u = "TRAEGT NICHT"
    return u, jk, b, rang, sp, nl


def main():
    rel, F = T.merkmale()
    up, down, end, fertig = T.ziele(rel)
    m, kl = T.maske()
    m = m & fertig
    # Teil 0 wie k3_machbarkeit (R-R11)
    w = (IDX >= "2023-01-01") & (IDX <= "2023-12-01")
    P = {nm: K3M.perz({nm: F[nm][w]}, m[w], nm) for nm in ("rs7", "schwankung90", "tiefe")}
    basis = P["rs7"].notna()
    sel = (P["schwankung90"] <= 0.2) & (P["tiefe"] <= 0.2)
    ri = (up[w][sel].stack().mean() / up[w][basis].stack().mean()) / (down[w][sel].stack().mean() / down[w][basis].stack().mean())
    if int(sel.values.sum()) != 2720 or abs(ri - 1.90) >= 0.006:
        print("TEIL 0 FEHLGESCHLAGEN - Abbruch"); return
    print("MESSUNG K-3 Ruhiger Boden (§40.2) · Kurse bis %s\n\nTEIL 0 (R-R11): Vorpruefung §35.2 reproduziert (n 2.720, Richtung %.3f) - bestanden\n" % (T.M.ENDE.date(), ri))
    sig = K3M.signal(F, m)
    E = K37.bewerte(KM.einstiege_alle(sig, kl, m, pd.Timestamp("2024-01-01"), T.M.ENDE), up, down)
    kand = kandidaten(E, sig, kl, m)
    u, jk, b, rang, sp, nl = urteil(E, kand, up, down)
    kosten = E.kl.map(KOSTEN).mean()
    print("K-3 ab 2024 (alle Klassen): Einstiege %d an %d Monaten (%d Coins; H %d · M %d · S %d) · Korb %+.2f Pp gegen BTC (Median der Monate %+.2f) · "
          "Bootstrap %.3f · Rang gegen Nullwelt %.3f (Nullwelt %+.2f Pp) · Spiegel %.2f (Lauf %.0f %% / Absturz %.0f %%, Nullwelt %.0f / %.0f %%)  ->  %s" % (
              len(E), E.mon.nunique(), E.sym.nunique(), (E.kl == "H").sum(), (E.kl == "M").sum(), (E.kl == "S").sum(), 100 * jk.mean(), 100 * jk.median(),
              b, rang, 100 * nl.mean(), sp[0], 100 * E.lauf.mean(), 100 * E.absturz.mean(), 100 * sp[1], 100 * sp[2], u))
    print("   nach Kosten (Mittel der Einstiege %.2f %% Hin+Rueck): Korb %+.2f Pp -> %s" % (100 * kosten, 100 * (jk.mean() - kosten), "LOHNT" if jk.mean() - kosten > 0 else "lohnt nicht"))

    print("\nSELBSTTEST:")
    je = E.groupby(["signal", "kl"]).size()
    fehl = 0
    for _ in range(100):
        z = []
        for (d, k), n in je.items():
            i = IDX.get_loc(d)
            pool = kand[(d, k)] + list(E[(E.signal == d) & (E.kl == k)].sym)
            for s in RNG.choice(pool, size=min(n, len(pool)), replace=False):
                z.append((d, s, k, i + 1, i + 31))
        Z = K37.bewerte(pd.DataFrame(z, columns=["signal", "sym", "kl", "i_kauf", "i_aus"]), up, down)
        kz = {}
        for (d, k), gg in Z.groupby(["signal", "kl"]):
            gew = set(gg.sym)
            kz[(d, k)] = [s for s in kand[(d, k)] + list(E[(E.signal == d) & (E.kl == k)].sym) if s not in gew]
        fehl += urteil(Z, kz, up, down, nz=40)[0] == "TRAEGT"
    G = E[E.ex >= 0.10]
    ug = urteil(G, kand, up, down, nz=40)[0]
    print("  (a) Zufalls-Signal 100 Welten: Fehlalarm %d %% (Soll <= 2,5 %%) -> %s · (b) gepflanzt (nur Einstiege >= +10 %%, n %d): %s" % (
        fehl, "bestanden" if fehl <= 2.5 else "NICHT bestanden", len(G), "erkannt" if ug == "TRAEGT" else "NICHT erkannt (%s)" % ug))

    print("\nAUSKUNFT (nach dem Urteil):")
    for k in ("H", "M", "S"):
        g = E[E.kl == k]
        if len(g) < 5:
            print("  Klasse %s: n %d - zu wenige" % (k, len(g))); continue
        kg = {key: v for key, v in kand.items() if key[1] == k}
        nk = nullwelt(g, vorrat(g, kg), 100)
        jg = K37.korb(g)
        print("  Klasse %s: n %d · Korb %+.2f Pp · Rang gegen Nullwelt %.2f · nach Kosten (%.2f %%) %+.2f Pp" % (
            k, len(g), 100 * jg.mean(), np.mean(nk < jg.mean()), 100 * KOSTEN[k], 100 * (jg.mean() - KOSTEN[k])))
    print("  je Jahr: %s" % " · ".join("%d %+.1f Pp (n %d)" % (j, 100 * K37.korb(g).mean(), len(g)) for j, g in E.groupby(E.signal.dt.year)))
    for halte in (15, 60):
        Eh = K37.bewerte(KM.einstiege_alle(sig, kl, m, pd.Timestamp("2024-01-01"), T.M.ENDE, halte=halte), up, down)
        print("  Zeitgrenze %d T: n %d · Korb %+.1f Pp" % (halte, len(Eh), 100 * K37.korb(Eh).mean()))
    x2 = []
    for r in E.itertuples():
        j, _ = FB.marke(K[r.sym].values, r.i_kauf, 0.35, 30)
        x2.append(np.nan if j is None else K37.ex(r.sym, r.i_kauf, j))
    E["x2"] = x2
    print("  Marke X2 (Nachlauf 35 %%, hoechstens 30 T): Korb %+.1f Pp" % (100 * E.groupby("mon").x2.mean().mean()))
    B = pd.Series(BTCV, index=IDX)
    btc = (B / B.shift(90) - 1).reindex(E.signal).values > 0
    print("  BTC 90 T am Signaltag steigt: %+.1f Pp (n %d) · faellt: %+.1f Pp (n %d)" % (
        100 * K37.korb(E[btc]).mean(), int(btc.sum()), 100 * K37.korb(E[~btc]).mean(), int((~btc).sum())))
    try:
        dom = pd.read_sql("select substr(stunde,1,10) tag, close from btcdom where stunde in (select max(stunde) from btcdom group by substr(stunde,1,10))",
                          sqlite3.connect("file:data/richtung_historie.db?mode=ro", uri=True))
        dom = pd.Series(dom.close.values, index=pd.to_datetime(dom.tag)).sort_index()
        sp_ = (dom / dom.shift(30) - 1 >= 0.087).reindex(E.signal).fillna(False).values.astype(bool)
        print("  nach Dominanz-Spitze: %+.1f Pp (n %d) · sonst %+.1f Pp" % (100 * K37.korb(E[sp_]).mean() if sp_.any() else float("nan"), int(sp_.sum()), 100 * K37.korb(E[~sp_]).mean()))
    except Exception as ex:                                  # noqa: BLE001
        print("  Dominanz-Spitze nicht lesbar: %s" % ex)
    top = E.groupby("sym").ex.sum().sort_values(ascending=False).head(5).index
    kat = set(pd.read_csv(os.path.join("data", "_spot", "bitpanda_katalog_krypto_2026-10-08.csv"), sep=";").symbol.str.upper())
    bp = E[E.sym.isin(kat)]
    print("  Weglassprobe ohne %s: %+.1f Pp · nur Bitpanda-handelbar (n %d): %+.1f Pp" % (",".join(top), 100 * K37.korb(E[~E.sym.isin(top)]).mean(), len(bp), 100 * K37.korb(bp).mean()))
    alle_end = []
    for r in E.itertuples():
        i = r.i_kauf - 1
        z = end.iloc[i][m.iloc[i]].dropna()
        alle_end.append(end.iat[i, end.columns.get_loc(r.sym)] - z.mean())
    print("  wie die Vorpruefung (Ende 30 T des Coins gegen ALLE Coins am Tag, nicht gegen BTC): %+.2f Pp" % (100 * np.nanmean(alle_end)))
    E.to_csv(os.path.join("data", "_spot", "k3_messung.csv"), sep=";", index=False)


if __name__ == "__main__":
    main()
