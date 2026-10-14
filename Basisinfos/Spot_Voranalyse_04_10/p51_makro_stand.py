"""P51 Makro-Umfeld - Stand der Reihen (Spot §51, 14.10.2026). Nur lesend, FRED fredgraph.csv (frei, ohne Schluessel).

    python Basisinfos/Spot_Voranalyse_04_10/p51_makro_stand.py

Je Reihe: letzter Wert, vor 3 und vor 12 Monaten, Perzentil im 5-Jahres-Fenster. BESCHREIBUNG, keine Messung eines Zusammenhangs.
"""
import io

import pandas as pd
import requests

REIHEN = [("DFF", "Leitzins (eff.)"), ("DGS2", "Rendite 2 J"), ("DGS10", "Rendite 10 J"), ("T10Y2Y", "Kurve 10J-2J"), ("T10Y3M", "Kurve 10J-3M"),
          ("DFII10", "Realzins 10 J (TIPS)"), ("T10YIE", "Inflationserwartung 10 J"), ("BAMLH0A0HYM2", "Kreditaufschlag High Yield"),
          ("BAMLC0A0CM", "Kreditaufschlag Investment Grade"), ("NFCI", "Finanzierungsbedingungen NFCI"), ("DTWEXBGS", "Dollar breit"),
          ("VIXCLS", "VIX"), ("M2SL", "Geldmenge M2"), ("WALCL", "Fed-Bilanz"), ("WTREGEN", "TGA"), ("RRPONTSYD", "Reverse Repo")]


def fred(s):
    r = requests.get("https://fred.stlouisfed.org/graph/fredgraph.csv?id=" + s, timeout=90)
    d = pd.read_csv(io.StringIO(r.text))
    d.columns = ["datum", s]
    d["datum"] = pd.to_datetime(d.datum)
    return pd.to_numeric(d.set_index("datum")[s], errors="coerce").dropna()


def an(s, tage):
    x = s[:s.index[-1] - pd.Timedelta(days=tage)]
    return x.iloc[-1] if len(x) else float("nan")


def main():
    R = {s: (t, fred(s)) for s, t in REIHEN}
    print("%-34s %-11s %10s %10s %10s %10s" % ("Reihe", "Stand", "jetzt", "vor 3 M", "vor 12 M", "5-J-Perz."))
    for s, (txt, r) in R.items():
        if s in ("WALCL", "WTREGEN", "RRPONTSYD"):
            continue
        if s == "M2SL":
            r, txt = r / r.shift(12) - 1, "M2 J/J"
        v = r.iloc[-1]
        p5 = (r[r.index >= r.index[-1] - pd.Timedelta(days=1826)] <= v).mean()
        print("%-34s %-11s %10.3f %10.3f %10.3f %10.2f" % (txt, r.index[-1].date(), v, an(r, 91), an(r, 365), p5))
    w = pd.concat([R["WALCL"][1], R["WTREGEN"][1], R["RRPONTSYD"][1].resample("W-WED").last()], axis=1, sort=True).ffill().dropna()
    n = (w["WALCL"] - w["WTREGEN"] - w["RRPONTSYD"] * 1000) / 1e6
    print("%-34s %-11s %10.2f %10.2f %10.2f  (Bio USD; 13 W %+.1f %%, 52 W %+.1f %%)" % (
        "Netto-Liquiditaet Fed", n.index[-1].date(), n.iloc[-1], an(n, 91), an(n, 365), 100 * (n.iloc[-1] / an(n, 91) - 1), 100 * (n.iloc[-1] / an(n, 365) - 1)))


if __name__ == "__main__":
    main()
