"""O47 Schritt 1 - URSACHE der Verspaetung (18.10.2026, AUSKUNFT, aendert das Urteil 'unzulaessig' nicht). Nur 2019-04..2021-06.

    python Basisinfos/Spot_Voranalyse_04_10/o47_schritt1_ursache.py

U1 je Sonntag um die zwei grossen Starts: Vorsprung S1 (90 T, Binance-Korb) gegen Wochenkorb (13 Wochen, CMC) - knapp unter 25 Pp oder weit weg?
U2 Ueberschneidung der Koerbe je Monat 2020 (Kuerzel): wie viele der 50 sind in beiden?
U3 Vorsprung je Teilmenge im April 2020: gemeinsame Coins, nur S1, nur CMC (Mittel der 90-T-Rendite gegen BTC, aus den CMC-Wochenkursen)
"""
import os
import sqlite3
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.chdir(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import s1_messung as S1  # noqa: E402
import o47_schritt1 as O1  # noqa: E402

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:  # noqa: BLE001
    pass
s1 = S1.baue()
E = pd.read_csv("data/_spot/o47_schritt1.csv", sep=";", parse_dates=[0], index_col=0)
print("O47 SCHRITT 1 URSACHE (Auskunft)\n")
print("U1 Vorsprung gegen BTC in den folgenden 90 T / 13 Wochen (Schwelle 25 Pp):")
for a, e in (("2020-03-01", "2020-06-30"), ("2020-10-04", "2021-01-31")):
    for t in E.index[(E.index >= a) & (E.index <= e)]:
        s = s1["rel90_vor"].get(t)
        print("   %s  S1 %+6.1f Pp%s · Wochenkorb %+6.1f Pp%s" % (t.date(), 100 * s, " *" if s >= 0.25 else "  ", 100 * E.rel13[t],
                                                                  " *" if E.rel13[t] >= 0.25 else ""))
    print()
W = O1.lade()
P, btc, sym, stabil, tops, rets, fehlen, wochen = O1.korb(W)
print("U2 Ueberschneidung der Koerbe (Kuerzel) je Monat:")
for m in [t for t in tops if pd.Timestamp("2020-01-01") <= t <= pd.Timestamp("2021-03-31")]:
    a = {str(sym[i]).upper() for i in tops[m]}
    b = {str(x).upper() for x in s1["tops"].get(m.replace(day=1), [])}
    print("   %s  gemeinsam %2d von 50 · nur CMC u. a. %s · nur S1 u. a. %s" % (m.date(), len(a & b), ", ".join(sorted(a - b)[:8]), ", ".join(sorted(b - a)[:8])))
print("\nU3 Vorsprung je Teilmenge (CMC-Wochenkurse, 13 Wochen ab dem ersten Sonntag, gegen BTC):")
for m in (pd.Timestamp("2020-04-05"), pd.Timestamp("2020-11-01")):
    m0 = [t for t in tops if t <= m][-1]
    t13 = wochen[list(wochen).index(m0) + 13]
    br = P.loc[t13, btc] / P.loc[m0, btc]
    a = {str(sym[i]).upper(): i for i in tops[m0]}
    b = {str(x).upper() for x in s1["tops"].get(m0.replace(day=1), [])}
    idsym = W[W.stichtag == m0].set_index("symbol").id.to_dict()

    def vorsprung(namen):
        r = []
        for n in namen:
            i = a.get(n, idsym.get(n))
            if i is None or i not in P.columns:
                continue
            p0, p1 = P.loc[m0].get(i), P.loc[t13].get(i)
            if p0 == p0 and p1 == p1:
                r.append(p1 / p0 / br - 1)
        return (100 * float(np.mean(r)), len(r)) if r else (float("nan"), 0)

    for name, menge in (("gemeinsam", set(a) & b), ("nur CMC", set(a) - b), ("nur S1", b - set(a))):
        v, n = vorsprung(menge)
        print("   %s %-9s %+6.1f Pp (%d Coins mit beiden Kursen)" % (m0.date(), name, v, n))
