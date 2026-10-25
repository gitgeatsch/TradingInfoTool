"""P86 MESSPLAN A TEIL A1 (Voranalyse_Vorsprungs_Atlas_25_10.md §6.2/§6.4, vorab a5825547 + ec3f83e4): Zerlegung auf der Monatsebene.

    python -X utf8 Basisinfos/Rechenkern_02_10/p86_a1_zerlegung.py

AUSKUNFT, kein Urteil. Je Monatsstichtag x Coin (mk_messung.paare_mw(h), h = 30 und 365 Tage; eingestellte Coins wie B4): Ertrag
Coin und BTC im selben Fenster. Fuenftel nach Wert ohne F9 (B4-Regel) aus paare_mw(1). Gruppen: Klassen H/M/S, Top 30/50/100 nach
Marktwert-Rang am Stichtag (rang_mw), Gesamtmarkt. Je Stichtag gleich gewichtet; Band ueber gleitende Bloecke von Stichtagen
(Blocklaenge nach messnorm._block, in Stichtagen, zirkulaer), 2.000 Ziehungen; unter 20 Bloecken KEIN BEFUND. Dazu je Season-Ampel-Stufe, BTC-Volatilitaet je Jahr, Coins je Gruppe.
Nur lesend.
"""
import os
import sqlite3
import sys

import numpy as np
import pandas as pd

HIER = os.path.dirname(os.path.abspath(__file__))
WURZEL = os.path.dirname(os.path.dirname(HIER))
sys.path.insert(0, os.path.join(WURZEL, "Basisinfos", "Spot_Voranalyse_04_10"))
sys.path.insert(0, HIER)
sys.path.insert(0, WURZEL)
os.chdir(WURZEL)
sys.stdout.reconfigure(encoding="utf-8")
import warnings  # noqa: E402

warnings.filterwarnings("ignore", category=RuntimeWarning)
import p85_atlas_voranalyse as P85  # noqa: E402

MK = P85.MK
RNG = np.random.default_rng(86)
GRUPPEN = ("Top 30", "Top 50", "Top 100", "H", "M", "S", "Gesamt")


def anker(h, T1):
    D = MK.paare_mw(h).reset_index(drop=True)
    D = D.merge(T1[["t", "sym", "p"]], on=["t", "sym"], how="left")
    D["f"] = np.ceil(D.p * 5).clip(1, 5)
    rg = {}
    for t in D.t.unique():
        rg[t] = MK.rang_mw(pd.Timestamp(t))[1]
    D["rang"] = [rg[t].get(s, np.nan) for t, s in zip(D.t, D.sym)]
    D["r"] = D.ende - 1.0
    D["rb"] = D.ende_b - 1.0
    return D


def maske(D, g):
    if g in ("H", "M", "S"):
        return D.kl == g
    if g.startswith("Top"):
        return D.rang <= int(g.split()[1])
    return np.ones(len(D), bool)


def je_stichtag(D):
    """-> DataFrame je Stichtag: btc, gruppe, f5, f1..f5 Mittel, n (D schon auf die Gruppe gefiltert)."""
    z = []
    for t, g in D.groupby("t"):
        if len(g) < 5:
            continue
        row = dict(t=t, ep=g.ep.iloc[0], n=len(g), btc=g.rb.iloc[0], gr=g.r.mean())
        for q in (1, 2, 3, 4, 5):
            x = g.r[g.f == q]
            row["f%d" % q] = x.mean() if len(x) else np.nan
        z.append(row)
    return pd.DataFrame(z)


def block_stichtage(h):
    """messnorm._block: max(15 Tage, 3 x Horizont), umgerechnet auf Monatsstichtage (aufgerundet)."""
    import messnorm
    return int(np.ceil(messnorm._block(h) / 30.4))


def ak(werte, lag):
    """wie messnorm.pruefe_block: Autokorrelation beim Abstand der Blocklaenge (Grenze 0,15)."""
    w = np.asarray(werte, float)
    w = w[np.isfinite(w)]
    if len(w) < lag + 5:
        return np.nan
    a, b = w[:-lag], w[lag:]
    return float(np.corrcoef(a, b)[0, 1]) if a.std() > 1e-12 and b.std() > 1e-12 else 0.0


def band(werte, block, n=2000):
    w = np.asarray(werte, float)
    w = w[np.isfinite(w)]
    if len(w) < 3 or len(w) / block < 20:          # messnorm: unter 20 Bloecken KEIN BEFUND - kein Band ausgegeben
        return np.nan, np.nan
    b = max(1, min(block, len(w) - 1))
    st = RNG.integers(0, len(w), (n, int(np.ceil(len(w) / b))))     # ZIRKULAER: sonst ueberwiegt die Mitte (Punktwert lag ausserhalb des Bands)
    ix = ((st[:, :, None] + np.arange(b)) % len(w)).reshape(n, -1)[:, :len(w)]
    m = w[ix].mean(axis=1)
    return float(np.percentile(m, 2.5)), float(np.percentile(m, 97.5))


def stufen():
    import agent.season_ampel as SA
    Z = pd.read_csv(os.path.join("data", "_spot", "am_kalibrierung.csv"), sep=";", parse_dates=["date"]).set_index("date")
    return SA.geltend(SA.stufen(Z))


def btc_vola():
    c = sqlite3.connect("file:data/_spot/coinmetrics.db?mode=ro", uri=True)
    b = pd.read_sql("SELECT tag, PriceUSD FROM tag WHERE asset='btc' AND PriceUSD IS NOT NULL", c, parse_dates=["tag"]).set_index("tag").PriceUSD
    c.close()
    r = np.log(b).diff().dropna()
    return {int(j): float(g.std() * np.sqrt(365)) for j, g in r.groupby(r.index.year) if j >= 2017}


def pp(x):
    return "    –" if not np.isfinite(x) else "%+6.1f" % (100 * x)


def main():
    print("P86 MESSPLAN A · TEIL A1 ZERLEGUNG AUF DER MONATSEBENE (Auskunft)\n")
    T1 = P85.wert_tabelle(1)
    st = stufen()
    for h, name in ((30, "1 Monat"), (365, "12 Monate")):
        block = block_stichtage(h)
        D = anker(h, T1)
        print("=" * 150)
        print("HORIZONT %s · Stichtage %s..%s · Anker %d · ohne Umlaufangabe (kein Rang) %.0f %% · Block nach messnorm %d Stichtage "
              "(max(15 T, 3 x %d T)); Band nur ab 20 Bloecken, sonst KEIN BEFUND (nur Punktwert)" % (
            name, D.t.min().date(), D.t.max().date(), len(D), 100 * D.rang.isna().mean(), block, h))
        print("  Gruppe   Ep | Stichtage  Coins/Stichtag | BTC      Gruppe   Gr-BTC [Band]          | F5-Gr [Band]           | F5-BTC [Band]          "
              "F5>BTC | Dosis F1..F5 - Gruppe")
        for ep in ("E2", "E3", "alle"):
            for g in GRUPPEN:
                S = je_stichtag(D[maske(D, g) & ((D.ep == ep) if ep != "alle" else (D.ep != ""))])
                if not len(S):
                    continue
                d1 = S.gr - S.btc
                d2 = S.f5 - S.gr
                d3 = S.f5 - S.btc
                b1, b2, b3 = band(d1, block), band(d2, block), band(d3, block)
                dosis = " ".join(pp(np.nanmean(S["f%d" % q] - S.gr)) for q in (1, 2, 3, 4, 5))
                print("  %-8s %-4s | %3d %4.1f Bl. %6.0f        | %s   %s   %s [%s;%s]  | %s [%s;%s]  | %s [%s;%s]  %4.0f %% | %s | AK F5-BTC %s" % (
                    g, ep, len(S), len(S) / block, S.n.mean(), pp(S.btc.mean()), pp(S.gr.mean()), pp(d1.mean()), pp(b1[0]), pp(b1[1]),
                    pp(np.nanmean(d2)), pp(b2[0]), pp(b2[1]), pp(np.nanmean(d3)), pp(b3[0]), pp(b3[1]), 100 * np.nanmean(d3 > 0), dosis,
                    "%.2f" % ak(d3, block) if np.isfinite(ak(d3, block)) else "–"))
            print()
        # je Season-Ampel-Stufe (Gesamt und Top 100, alle Epochen ab 2019-04)
        print("  je SEASON-AMPEL-STUFE am Stichtag (alle Epochen):")
        D["stufe"] = [st.asof(t) if t >= st.index[0] else None for t in D.t]
        for g in ("Top 100", "Gesamt"):
            for sname, gs in D[maske(D, g)].groupby("stufe"):
                S = je_stichtag(gs)
                if len(S) < 2:
                    continue
                print("    %-8s %-14s Stichtage %3d · Gruppe-BTC %s · F5-Gruppe %s · F5-BTC %s · F5>BTC %3.0f %%" % (
                    g, sname, len(S), pp((S.gr - S.btc).mean()), pp(np.nanmean(S.f5 - S.gr)), pp(np.nanmean(S.f5 - S.btc)),
                    100 * np.nanmean((S.f5 - S.btc) > 0)))
        print()
    print("AUSKUNFT BTC-Volatilitaet je Jahr (Tagesrenditen, aufs Jahr gerechnet): " + " · ".join(
        "%d %.0f %%" % (j, 100 * v) for j, v in btc_vola().items()))
    D = anker(30, T1)
    print("AUSKUNFT Coins je Stichtag (Mittel) je Gruppe und Epoche: " + " | ".join(
        "%s %s" % (ep, " ".join("%s %.0f" % (g, D[maske(D, g) & (D.ep == ep)].groupby("t").size().mean()) for g in GRUPPEN))
        for ep in ("E1", "E2", "E3")))


if __name__ == "__main__":
    main()
