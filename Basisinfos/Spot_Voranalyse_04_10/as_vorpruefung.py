"""Vorpruefung Asymmetrie (Voranalyse_Spot_Neubau_04_10.md §19, E-71) - Datenlage und GRUNDRATE der Zielgroesse, OHNE Merkmale.

    python Basisinfos/Spot_Voranalyse_04_10/as_vorpruefung.py

Nur lesend (mode=ro). Kein Blick auf einen Merkmalsschnitt - nur: wie viele Anker, wie oft kommt das rechte und das linke Ende ueberhaupt vor,
und wie viele Coin-Anker haben einen Wert fuer jedes Merkmal.

Zielgroesse je (Coin, Monatserster t): Kauf Schluss t+1, Fenster 365 bzw. 730 T.
  rechtes Ende  R2 / R3 = hoechster Schluss im Fenster >= x2 / x3 des Einstiegs (das POTENTIAL)
  linkes Ende   L      = tiefster Schluss <= -70 % ODER eingestellt (Reihe endet vor dem Fensterende und > 10 T vor Datenende)
  Endwert              = Schluss am Fensterende bzw. letzter Kurs; Korb = Mittel der Endwerte gegen BTC an denselben Tagen
"""
import os
import sqlite3
import sys

import numpy as np
import pandas as pd

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HIER)
import a2_messung as A  # noqa: E402

K, IDX, POS, ENDE, BTCV = A.K, A.IDX, A.POS, A.ENDE, A.BTCV


def ziel(s, i0, h):
    v = K[s].values[i0:i0 + h + 1]
    if np.isnan(v[0]):
        return None
    ok = ~np.isnan(v)
    if not ok.all():
        v = v[:np.argmin(ok)]
    voll = len(v) == h + 1
    eing = (not voll) and (i0 + len(v) - 1 < len(IDX) - 11)
    if not voll and not eing:
        return None                                              # Fenster am Datenende nicht abgeschlossen
    b = BTCV[i0:i0 + len(v)]
    x = v / v[0]
    return dict(r2=x.max() >= 2, r3=x.max() >= 3, l=(x.min() <= 0.30) or eing, eing=eing, ende=x[-1], ende_b=b[-1] / b[0])


def anker(h):
    out = []
    for t in pd.date_range("2019-01-01", ENDE, freq="MS"):
        if t not in POS or POS[t] + 1 + h >= len(IDX) + 0 and t > ENDE - pd.Timedelta(days=h):
            continue
        kl = A.klassen(t)[0]
        for s, k in kl.items():
            z = ziel(s, POS[t] + 1, h)
            if z is not None:
                out.append(dict(z, t=t, sym=s, kl=k, ep=A.epoche(t)))
    return pd.DataFrame(out)


def main():
    print("Vorpruefung Asymmetrie (§19) · Kurse bis %s · nur Grundrate und Datenlage, kein Merkmalsschnitt" % ENDE.date())
    for h in (365, 730):
        D = anker(h)
        print("\nFenster %d T · Anker = Monatserste ab 2019 mit abgeschlossenem Fenster" % h)
        print("  %-3s %-2s %6s %7s | %6s %6s | %6s %6s | Endwert Median | Korb gg. BTC (Mittel je Anker, dann Mittel)" % ("Ep", "Kl", "Paare", "Anker", "R2", "R3", "L", "eing."))
        for ep in ("E1", "E2", "E3"):
            for k in ("H", "M", "S"):
                x = D[(D.ep == ep) & (D.kl == k)]
                if len(x) < 20:
                    print("  %-3s %-2s %6d  zu wenige" % (ep, k, len(x))); continue
                korb = x.groupby("t").apply(lambda g: g["ende"].mean() / g["ende_b"].iloc[0] - 1).mean()
                print("  %-3s %-2s %6d %7d | %5.0f%% %5.0f%% | %5.0f%% %5.0f%% | %+6.0f %%       | %+6.0f %%" % (
                    ep, k, len(x), x.t.nunique(), 100 * x.r2.mean(), 100 * x.r3.mean(), 100 * x.l.mean(), 100 * x.eing.mean(), 100 * (x.ende.median() - 1), 100 * korb))
        if h == 365:
            D365 = D
    # Datenlage je Merkmalsquelle (Anteil der Coin-Anker 365 T mit einem Wert 180 T VOR dem Anker)
    print("\nDatenlage Merkmalsquellen (Anteil der Coin-Anker im 365-T-Fenster mit Werten im Zeitraum [t-180, t]):")
    quellen = {}
    c = sqlite3.connect("file:data/tvl_historie.db?mode=ro", uri=True)
    quellen["TVL"] = {s: (pd.Timestamp(a), pd.Timestamp(b)) for s, a, b in c.execute("SELECT symbol, MIN(datum), MAX(datum) FROM tvl_historie GROUP BY symbol")}
    c = sqlite3.connect("file:data/onchain_historie.db?mode=ro", uri=True)
    quellen["Adressen"] = {s: (pd.Timestamp(a), pd.Timestamp(b)) for s, a, b in c.execute("SELECT symbol, MIN(datum), MAX(datum) FROM adractcnt GROUP BY symbol")}
    c = sqlite3.connect("file:data/funding_historie.db?mode=ro", uri=True)
    quellen["Funding"] = {s: (pd.Timestamp(a), pd.Timestamp(b)) for s, a, b in c.execute("SELECT symbol, MIN(datum), MAX(datum) FROM funding GROUP BY symbol")}
    c = sqlite3.connect("file:data/terminmarkt_historie.db?mode=ro", uri=True)
    quellen["Terminmarkt OI"] = {s: (pd.Timestamp(a), pd.Timestamp(b)) for s, a, b in c.execute("SELECT symbol, MIN(tag), MAX(tag) FROM terminmarkt_tag GROUP BY symbol")}
    for name, q in quellen.items():
        z = []
        for ep in ("E1", "E2", "E3"):
            x = D365[D365.ep == ep]
            hat = [(s in q) and q[s][0] <= t - pd.Timedelta(days=180) and q[s][1] >= t for s, t in zip(x.sym, x.t)]
            kl = x[hat].kl.value_counts().to_dict()
            z.append("%s %4.0f %% (H %d · M %d · S %d)" % (ep, 100 * np.mean(hat), kl.get("H", 0), kl.get("M", 0), kl.get("S", 0)))
        print("  %-15s %s" % (name, " · ".join(z)))
    print("  Kurs/Umsatz     alle Coin-Anker (Tiefe, Dauer, Schwankung, Abstand zum Tief, Staerke in der Klasse, Umsatzverlauf, Alter)")


if __name__ == "__main__":
    main()
