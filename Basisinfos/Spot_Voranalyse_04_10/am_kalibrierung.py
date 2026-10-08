"""KALIBRIERUNG der Season-Ampel (Spot §36.3, Plan vorab 1cd5ae8) - nur lesend; Abrufe FRED/DefiLlama (frei) ueber e33_analyse.reihen.

    python Basisinfos/Spot_Voranalyse_04_10/am_kalibrierung.py

Wahrheit (Rueckschau): S1-Korb (Top 50 nach Umsatz, gleich gewichtet, ohne Umlauf) schlaegt BTC in den FOLGENDEN 90 T um >= 25 Pp.
Bedingungen (am Tag bekannt): B1 BTC 91 T > 20 % · B2 M2 J/J > 5 % (Verzug 35 T) · B3 Stablecoins 91 T > 10 % (Verzug 1 T).
K1 Fuenftel je Bedingung · K2 Stand X von 3 (+ Leave-one-out) · K3 Plateau der Schwellen · K4 Uebergaenge und Start · K5 Fehlalarm-Zeiten.
"""
import os
import sys

import numpy as np
import pandas as pd

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HIER)
os.chdir(os.path.dirname(os.path.dirname(HIER)))
import e33_analyse as E    # noqa: E402
import s1_messung as S1    # noqa: E402

SCHWELLE = {"B1": 0.20, "B2": 0.05, "B3": 0.10}
GITTER = {"B1": [0.10, 0.15, 0.20, 0.25, 0.30], "B2": [0.03, 0.04, 0.05, 0.06, 0.07], "B3": [0.05, 0.075, 0.10, 0.15, 0.20]}


def taeglich(r, idx):
    return r.sort_index().reindex(r.index.union(idx)).ffill().reindex(idx)


def daten():
    s1 = S1.baue()
    idx = s1["idx"]
    R = E.reihen()
    m2 = R["m2"].sort_index()
    T = pd.DataFrame(index=idx)
    T["season"] = s1["rel90_vor"] >= 0.25
    T["wahr_bekannt"] = s1["rel90_vor"].notna()
    Bi = s1["Bi"]
    T["B1"] = Bi / Bi.shift(91) - 1
    T["B2"] = taeglich(m2 / m2.shift(12) - 1, idx)
    st = taeglich(R["stable"], idx)
    T["B3"] = st / st.shift(91) - 1
    T["Breite"] = s1["breite"]
    eth = s1["K"]["ETH"].reindex(idx)
    T["ETH/BTC 91T"] = (eth / eth.shift(91)) / (Bi / Bi.shift(91)) - 1
    nt = taeglich(R["netto"], idx)
    T["Netto-Liq 13W"] = nt / nt.shift(91) - 1
    T["Fear&Greed"] = taeglich(R["fg"], idx)
    return T, s1


def stand(T, s=SCHWELLE):
    return (T.B1 > s["B1"]).astype(int) + (T.B2 > s["B2"]).astype(int) + (T.B3 > s["B3"]).astype(int)


def main():
    T, s1 = daten()
    Z = T[(T.index >= "2019-04-01") & T.wahr_bekannt & T[["B1", "B2", "B3"]].notna().all(axis=1)].copy()
    ep = S1.episoden(Z.season)
    basis = Z.season.mean()
    print("KALIBRIERUNG Season-Ampel (§36.3) · %s bis %s · %d Tage · Season-Tage %.1f %% · Episoden %d: %s\n" % (
        Z.index[0].date(), Z.index[-1].date(), len(Z), 100 * basis, len(ep), " · ".join("%s bis %s" % (a.date(), e.date()) for a, e in ep)))

    print("K1 GUT/SCHLECHT JE BEDINGUNG (Fuenftel ueber den Zeitraum; Anteil Season-Tage, Lift gegen %.1f %%):" % (100 * basis))
    for c in ["B1", "B2", "B3", "Breite", "ETH/BTC 91T", "Netto-Liq 13W", "Fear&Greed"]:
        x = Z[c].dropna()
        q = pd.qcut(x, 5, duplicates="drop")
        g = Z.loc[x.index].groupby(q, observed=True).season.mean()
        print("  %-14s %s" % (c, " | ".join("%s: %4.1f %% (Lift %.1f%s)" % (
            "%.3g..%.3g" % (iv.left, iv.right), 100 * v, v / basis, " GUT" if v / basis >= 1.5 else (" schlecht" if v / basis <= 0.5 else "")) for iv, v in g.items())))

    Z["stand"] = stand(Z)
    print("\nK2 STAND X VON 3 (Schwellen B1 > 20 %, B2 > 5 %, B3 > 10 %):")
    for x, g in Z.groupby("stand"):
        print("  %d von 3: Tage %4d (%4.1f %%) · Season-Tage %5.1f %% · Lift %.2f" % (x, len(g), 100 * len(g) / len(Z), 100 * g.season.mean(), g.season.mean() / basis))
    print("  Leave-one-out (je Episode ihre Tage herausgenommen):")
    for a, e in ep:
        Y = Z[(Z.index < a) | (Z.index > e)]
        r = Y.groupby("stand").season.mean()
        mono = all(r.iloc[i] <= r.iloc[i + 1] + 1e-12 for i in range(len(r) - 1))
        print("    ohne %s..%s: %s -> %s" % (a.date(), e.date(), " · ".join("%d: %.1f %%" % (k, 100 * v) for k, v in r.items()), "Ordnung haelt" if mono else "Ordnung BRICHT"))

    print("\nK3 GRENZEN - PLATEAU STATT MAXIMUM (die anderen Schwellen bleiben beim Vorschlag):")
    for b, werte in GITTER.items():
        teile = []
        for v in werte:
            s = dict(SCHWELLE); s[b] = v
            st = stand(Z, s)
            drei = Z[st == 3]
            teile.append("%s %.3g: 3/3 an %d T, Season %.0f %%, erfasst %.0f %% der Season-Tage" % (
                "*" if v == SCHWELLE[b] else " ", v, len(drei), 100 * drei.season.mean() if len(drei) else 0, 100 * (drei.season.sum() / Z.season.sum())))
        print("  %s: %s" % (b, " | ".join(teile)))

    print("\nK4 UEBERGAENGE UND START je Episode:")
    for a, e in ep:
        teile = []
        for b in ("B1", "B2", "B3"):
            an = Z[b] > SCHWELLE[b]
            if an.get(a, False):
                vor = an[:a]
                aus = vor[~vor]
                seit = (a - aus.index[-1]).days if len(aus) else None
                teile.append("%s an seit %s T" % (b, seit))
            else:
                danach = an[a:e]
                teile.append("%s aus%s" % (b, " (an nach %d T)" % (danach.idxmax() - a).days if danach.any() else ""))
        st_a = int(Z.stand.get(a, -1))
        fall = Z.stand[a:][Z.stand[a:] < max(st_a, 1)]
        br_e = Z.Breite[:e].iloc[-1]
        print("  %s..%s (%3d T): Stand am Start %d · %s · Stand faellt unter den Startwert am %s · Breite am Ende %.2f" % (
            a.date(), e.date(), (e - a).days, st_a, " · ".join(teile), fall.index[0].date() if len(fall) else "-", br_e))
    erst3 = Z.stand.ge(3) & ~Z.stand.shift(1).fillna(0).ge(3)
    print("  Einschalten von 3/3 (alle): %s" % ", ".join(str(d.date()) for d in Z.index[erst3]))

    print("\nK5 FEHLALARM-ZEITEN (3/3 ueber >= 14 T, keine Season in diesen Tagen und den 90 T danach):")
    lauf, a0 = [], None
    for d, v in (Z.stand >= 3).items():
        if v and a0 is None:
            a0 = d
        if not v and a0 is not None:
            lauf.append((a0, d)); a0 = None
    if a0 is not None:
        lauf.append((a0, Z.index[-1]))
    for a, e in lauf:
        if (e - a).days < 14:
            continue
        fenster = T.season[a:e + pd.Timedelta(days=90)]
        if not fenster.any():
            print("  %s..%s (%d T) FEHLALARM · BTC 91T %+.0f %% · M2 %+.1f %% · Stablecoins %+.0f %% · Breite %.2f" % (
                a.date(), e.date(), (e - a).days, 100 * Z.B1[a], 100 * Z.B2[a], 100 * Z.B3[a], Z.Breite[a]))
        else:
            print("  %s..%s (%d T) mit Season" % (a.date(), e.date(), (e - a).days))

    h = T[T[["B1", "B2", "B3"]].notna().all(axis=1)].iloc[-1]
    v30 = T[T[["B1", "B2", "B3"]].notna().all(axis=1)].iloc[-31]
    print("\nAMPEL HEUTE (%s): %s · Stand %d von 3 · Breite %.2f" % (
        T[T[["B1", "B2", "B3"]].notna().all(axis=1)].index[-1].date(),
        " · ".join("%s %+.1f %% (Schwelle %.0f %%, vor 30 T %+.1f %%)" % (b, 100 * h[b], 100 * SCHWELLE[b], 100 * v30[b]) for b in ("B1", "B2", "B3")),
        int(h.B1 > SCHWELLE["B1"]) + int(h.B2 > SCHWELLE["B2"]) + int(h.B3 > SCHWELLE["B3"]), h.Breite))   # KORREKTUR: numpy-bool '+' ist ODER
    Z.to_csv(os.path.join("data", "_spot", "am_kalibrierung.csv"), sep=";")


if __name__ == "__main__":
    main()


def muster():
    """K2b (Auskunft, nach K2): WELCHE Bedingungen erfuellt sind - je Kombination Tage, Season-Anteil, Episoden mit Season-Tagen."""
    Z = pd.read_csv(os.path.join("data", "_spot", "am_kalibrierung.csv"), sep=";", index_col=0, parse_dates=True)
    Z["season"] = Z.season.astype(str).str.lower().eq("true")
    b1, b2, b3 = Z.B1 > SCHWELLE["B1"], Z.B2 > SCHWELLE["B2"], Z.B3 > SCHWELLE["B3"]
    print("\nK2b MUSTER - welche Bedingungen an sind (B1 BTC · B2 M2 · B3 Stablecoins):")
    for name, m in (("keine", ~b1 & ~b2 & ~b3), ("nur BTC", b1 & ~b2 & ~b3), ("nur Geld (M2 oder Stable)", ~b1 & (b2 ^ b3)), ("nur Geld (M2 und Stable)", ~b1 & b2 & b3),
                    ("BTC + M2, Stablecoins fehlen", b1 & b2 & ~b3), ("BTC + Stablecoins, M2 fehlt", b1 & ~b2 & b3), ("alle drei", b1 & b2 & b3)):
        g = Z[m]
        jahre = sorted(set(g[g.season].index.year))
        print("  %-30s Tage %4d · Season-Tage %5.1f %% · Season-Tage in den Jahren %s" % (name, len(g), 100 * g.season.mean() if len(g) else 0, jahre or "-"))
    h = Z.iloc[-1]


if __name__ == "__main__" and "--muster" in os.environ.get("AM_MODUS", ""):
    muster()
