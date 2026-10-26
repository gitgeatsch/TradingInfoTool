"""P86 GEGENPROBE Messplan A Teil A1 (25.10.2026): zweiter Weg zu den Kernzahlen und zum Band.

    python -X utf8 Basisinfos/Rechenkern_02_10/p86_gegenprobe.py

G1  Top 30 und Gesamt, E3, 12 M: 'Gruppe - BTC' und 'F5 - BTC' direkt aus den Tagesschluessen (as_messung.K, BTC-Reihe) in eigener
    Schleife statt ueber paare_mw/je_stichtag - gleich p86 (+-0,1 Pp; Werte aus p86_a1_zerlegung.txt gelesen)
G2  Band anders (nur wo die Norm ein Band erlaubt: 1 M, alle Jahre): Stichtage in NICHT ueberlappende 3er-Bloecke gemittelt, dann
    einfacher Bootstrap - gleiche Aussage, ob das Band die Null einschliesst (F5-Gruppe und F5-BTC fuer Top 30, Top 100, Gesamt)
G3  R-R11: Dosis E3 ohne F9 nach der B4-Rechnung (d4_wirkung.dosis) auf denselben Ankern = b4_vormessung SOLL (+-0,15 Pp)

E-153 (26.10.2026): mit MK_RANG_QUELLE=cmc (zeitrichtiger Rang) vergleicht G1/G2 gegen p94_a1_neu.txt; G3 gehoert zur ALTEN Basis
(b4_vormessung lief mit dem bisherigen Rang) und ist dann nur Auskunft.
"""
import os
import re
import sys

import numpy as np
import pandas as pd

HIER = os.path.dirname(os.path.abspath(__file__))
WURZEL = os.path.dirname(os.path.dirname(HIER))
sys.path.insert(0, os.path.join(WURZEL, "Basisinfos", "Spot_Voranalyse_04_10"))
sys.path.insert(0, HIER)
os.chdir(WURZEL)
sys.stdout.reconfigure(encoding="utf-8")
import warnings  # noqa: E402

warnings.filterwarnings("ignore", category=RuntimeWarning)
import p86_a1_zerlegung as P  # noqa: E402

MK = P.MK
AM = MK.M                                     # as_messung: K, POS, IDX, BTCV, ziel


def direkt(T1, g, ep="E3", h=365):
    """eigene Schleife: je Stichtag die Gruppe nach rang_mw / Klasse, Ertrag aus K, BTC aus BTCV."""
    p = {(t, s): v for t, s, v in zip(T1.t, T1.sym, T1.p)}
    zeilen = []
    for t in pd.date_range("2019-01-01", MK.ENDE, freq="MS"):
        if t not in AM.POS or AM.POS[t] + 1 + h > len(AM.IDX) - 1:
            continue
        out, _, _ = MK.klassen_mw(t)
        if AM.A.epoche(t) != ep:                       # Epoche wie paare_mw (as_messung.A.epoche) - erste Fassung griff nicht (Fehler, behoben)
            continue
        r = MK.rang_mw(t)[1]
        i0 = AM.POS[t] + 1
        b = AM.BTCV[i0:i0 + h + 1]
        er, f5 = [], []
        for s, k in out.items():
            if g.startswith("Top") and not (r.get(s, np.inf) <= int(g.split()[1])):
                continue
            z = AM.ziel(s, i0, h)
            if z is None:
                continue
            er.append(z["ende"] - 1)
            q = p.get((t, s), np.nan)
            if q == q and np.ceil(q * 5) >= 5:
                f5.append(z["ende"] - 1)
        if len(er) >= 5:
            bt = z["ende_b"] - 1 if er else np.nan
            zeilen.append((t, np.mean(er) - bt, (np.mean(f5) - bt) if f5 else np.nan))
    return pd.DataFrame(zeilen, columns=["t", "gr_btc", "f5_btc"])


def werte(teil, g, ep):
    """Zeile 'Gruppe Epoche' der p86-Ausgabe spaltenweise lesen (Spalten durch '|' getrennt; '–' = kein Band)."""
    f = lambda x: np.nan if x == "–" else float(x)  # noqa: E731
    for z in teil.splitlines():
        if z.startswith("  %-8s %-4s |" % (g, ep)):
            c = z.split("|")
            n2, n3, n4 = (re.findall(r"[+-]?\d+\.\d+|–", c[i]) for i in (2, 3, 4))
            return dict(grbtc=f(n2[2]), f5gr=f(n3[0]), f5gr_lo=f(n3[1]), f5gr_hi=f(n3[2]), f5btc=f(n4[0]), f5btc_lo=f(n4[1]), f5btc_hi=f(n4[2]))
    raise SystemExit("Zeile %s %s nicht gefunden" % (g, ep))


def main():
    neu = MK.RANG_QUELLE == "cmc"
    txt = open(os.path.join(HIER, "p94_a1_neu.txt" if neu else "p86_a1_zerlegung.txt"), encoding="utf-8").read()
    teil12 = txt.split("HORIZONT 12 Monate")[1]
    T1 = P.P85.wert_tabelle(1)
    ok1 = True
    for g in ("Top 30", "Gesamt"):
        X = direkt(T1, g)
        w = werte(teil12, g, "E3")
        a, b = w["grbtc"], w["f5btc"]
        x, y = 100 * X.gr_btc.mean(), 100 * np.nanmean(X.f5_btc)
        gl = abs(x - a) <= 0.1 and abs(y - b) <= 0.1
        ok1 &= gl
        print("G1 %-7s E3 12 M direkt: Gruppe-BTC %+.1f (p86 %+.1f) · F5-BTC %+.1f (p86 %+.1f) · Stichtage %d -> %s" % (
            g, x, a, y, b, len(X), "ok" if gl else "NICHT OK"))
    D = P.anker(30, T1)
    teil1 = txt.split("HORIZONT 1 Monat")[1].split("HORIZONT 12 Monate")[0]
    rng = np.random.default_rng(861)
    ok2 = True
    for g in ("Top 30", "Top 100", "Gesamt"):
        S = P.je_stichtag(D[P.maske(D, g)]).sort_values("t").reset_index(drop=True)
        w = werte(teil1, g, "alle")
        paare = {"F5-Gruppe": ((S.f5 - S.gr).to_numpy(), w["f5gr_lo"], w["f5gr_hi"]),
                 "F5-BTC": ((S.f5 - S.btc).to_numpy(), w["f5btc_lo"], w["f5btc_hi"])}
        for name, (d, lo, hi) in paare.items():
            d = d[np.isfinite(d)]
            bl = np.array([d[k:k + 3].mean() for k in range(0, len(d) - 2, 3)])
            mm = rng.choice(bl, (4000, len(bl))).mean(axis=1)
            lo2, hi2 = np.percentile(mm, [2.5, 97.5])
            gl = (lo2 <= 0 <= hi2) == (lo <= 0 <= hi)
            ok2 &= gl
            print("G2 %-7s 1 M alle %-9s: 3er-Bloecke (%d) [%+.1f; %+.1f] (p86 [%+.1f; %+.1f]) · Null im Band %s / p86 %s -> %s" % (
                g, name, len(bl), 100 * lo2, 100 * hi2, lo, hi, lo2 <= 0 <= hi2, lo <= 0 <= hi, "gleiche Aussage" if gl else "ANDERE AUSSAGE"))
    import d4_wirkung as D4
    Z = P.P85.M.Zellen(MK.paare_mw(365).reset_index(drop=True))
    F = P.P85.M.merkmale(MK.paare_mw(365).reset_index(drop=True))
    w9 = P.P85.W.wert(Z, F, wahl=D4.OHNE_F9)
    d = D4.dosis(Z, w9, "E3")
    soll = [-17.2, -4.7, 3.0, 6.0, 12.1]
    if neu:
        print("G3 (Auskunft, alte Basis) Dosis E3 ohne F9 mit zeitrichtigem Rang: %s (alter Rang: %s)" % (
            " ".join("%+.1f" % x for x in d), " ".join("%+.1f" % x for x in soll)))
        print("ERGEBNIS %d von 2 (G3 gehoert zur alten Basis)" % sum([ok1, ok2]))
        return
    ok3 = all(abs(a - b) <= 0.15 for a, b in zip(d, soll))
    print("G3 R-R11 Dosis E3 ohne F9: %s (Soll %s) -> %s" % (" ".join("%+.1f" % x for x in d), " ".join("%+.1f" % x for x in soll),
                                                          "ok" if ok3 else "NICHT OK"))
    print("ERGEBNIS %d von 3" % sum([ok1, ok2, ok3]))


if __name__ == "__main__":
    main()
