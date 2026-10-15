"""P55 VORANALYSE P22c Freigabe-Rhythmus (Spot §55, Nutzer 15.10.: "P22c danach") - nur lesend (Desktop data/umlaufmenge_cg.db).

    python Basisinfos/Spot_Voranalyse_04_10/p55_rhythmus_voranalyse.py

Frage: Laesst sich aus den vergangenen Freigaben (Sprungtage der Umlaufmenge) ein Rhythmus ablesen - und wie oft lag der daraus
abgeleitete NAECHSTE Termin tatsaechlich richtig? (Rueckschau ohne Vorgriff: an jedem Ereignis nur die Daten bis dahin.)

Regel (vorab, hier festgelegt):
  Ereignis    Tag mit Umlauf >= +1 % gegen den Vortag; Ereignistage mit <= 3 T Abstand zaehlen als EIN Ereignis (erster Tag)
  Rhythmus    in den 365 T bis zum Stichtag >= 4 Ereignisse; >= 70 % der Abstaende im Band; die letzten ZWEI Abstaende im Band;
              das letzte Ereignis hoechstens Band-Ende + 5 T zurueck (sonst "Rhythmus endete")
  Baender     monatlich 26-35 T · vierteljaehrlich 80-100 T · woechentlich 6-8 T
  naechster   letztes Ereignis + Median-Abstand; Treffer = naechstes echtes Ereignis innerhalb +-3 T (Auskunft auch +-5 T)
Nullbezug: derselbe Abstand, aber ab einem ZUFAELLIGEN Tag im selben Zeitraum (Trefferquote eines Datums ohne Wissen).
"""
import os
import sqlite3
import sys

import numpy as np
import pandas as pd

HIER = os.path.dirname(os.path.abspath(__file__))
os.chdir(os.path.dirname(os.path.dirname(HIER)))
RNG = np.random.default_rng(20261060)
SPRUNG = 0.01
BAENDER = {"monatlich": (26, 35), "vierteljaehrlich": (80, 100), "woechentlich": (6, 8)}


def ereignisse(r: pd.Series) -> pd.DatetimeIndex:
    p = r.pct_change(fill_method=None)
    t = p.index[(p >= SPRUNG).values]
    if not len(t):
        return pd.DatetimeIndex([])
    erste = [t[0]] + [b for a, b in zip(t[:-1], t[1:]) if (b - a).days > 3]
    return pd.DatetimeIndex(erste)


def rhythmus(ev: pd.DatetimeIndex, stichtag: pd.Timestamp):
    e = ev[(ev <= stichtag) & (ev > stichtag - pd.Timedelta(days=365))]
    if len(e) < 4:
        return None
    ab = np.diff(e.values).astype("timedelta64[D]").astype(int)
    for name, (lo, hi) in BAENDER.items():
        im = (ab >= lo) & (ab <= hi)
        if im.mean() >= 0.7 and im[-2:].all() and (stichtag - e[-1]).days <= hi + 5:
            return name, e, int(np.median(ab[im]))
    return None


def main():
    c = sqlite3.connect("file:data/umlaufmenge_cg.db?mode=ro", uri=True)
    ok = set(pd.read_sql("SELECT symbol FROM abruf_symbol WHERE urteil='ok'", c).symbol)
    d = pd.read_sql("SELECT symbol, substr(datum,1,10) AS d, wert FROM umlaufmenge", c)
    c.close()
    d = d[d.symbol.isin(ok)]
    d["d"] = pd.to_datetime(d.d)
    P = d.pivot(index="d", columns="symbol", values="wert").sort_index().asfreq("D").ffill(limit=3)
    ende = P.index[-1]
    EV = {s: ereignisse(P[s].dropna()) for s in P.columns}
    print("P55 VORANALYSE Freigabe-Rhythmus · Mengenreihe %s bis %s · %d Coins\n" % (P.index[0].date(), ende.date(), P.shape[1]))
    # Rueckschau: an jedem Ereignis (ab dem 4.) mit den Daten bis dahin den naechsten Termin ablesen
    treffer = {k: [] for k in BAENDER}
    nul = {k: [] for k in BAENDER}
    for s, ev in EV.items():
        for i in range(3, len(ev) - 1):
            st = ev[i]
            rh = rhythmus(ev, st)
            if not rh:
                continue
            name, e, med = rh
            ziel = st + pd.Timedelta(days=med)
            nxt = ev[i + 1]
            treffer[name].append(abs((nxt - ziel).days))
            # Nullbezug: zufaelliger Tag zwischen erstem und letztem Ereignis + derselbe Abstand, gegen das naechste echte Ereignis danach
            z = ev[0] + pd.Timedelta(days=int(RNG.integers(0, max(1, (ev[-1] - ev[0]).days))))
            nach = ev[ev > z]
            if len(nach):
                nul[name].append(abs((nach[0] - (z + pd.Timedelta(days=med))).days) if True else 0)
    for name in BAENDER:
        t = np.array(treffer[name])
        n = np.array(nul[name])
        if not len(t):
            print("  %-16s keine Faelle" % name)
            continue
        print("  %-16s Faelle %4d · Treffer +-3 T %3.0f %% (Zufallsdatum %3.0f %%) · +-5 T %3.0f %% (%3.0f %%) · Median-Fehler %d T" % (
            name, len(t), 100 * np.mean(t <= 3), 100 * np.mean(n <= 3) if len(n) else np.nan, 100 * np.mean(t <= 5),
            100 * np.mean(n <= 5) if len(n) else np.nan, int(np.median(t))))
    # Stand heute
    heute = [(s,) + rh for s in EV if (rh := rhythmus(EV[s], ende))]
    print("\nSTAND %s: %d Coins mit lebendem Rhythmus" % (ende.date(), len(heute)))
    for s, name, e, med in sorted(heute, key=lambda x: x[2][-1]):
        g = P[s].pct_change(fill_method=None).reindex(e)
        tag = sorted({x.day for x in e[-4:]})
        print("  %-8s %-14s %2d Ereignisse in 12 M · je Freigabe Median %+.1f %% · zuletzt %s · naechste etwa %s%s" % (
            s, name, len(e), 100 * float(g.median()), e[-1].date(), (e[-1] + pd.Timedelta(days=med)).date(),
            " (Kalendertage %s)" % ",".join(map(str, tag)) if name == "monatlich" else ""))
    endete = [s for s in EV if not rhythmus(EV[s], ende) and any(rhythmus(EV[s], x) for x in EV[s][3:])]
    print("\nRhythmus frueher erkannt, heute nicht mehr (endete oder wurde unregelmaessig): %d - %s" % (len(endete), ", ".join(sorted(endete)[:25])))


if __name__ == "__main__":
    main()
