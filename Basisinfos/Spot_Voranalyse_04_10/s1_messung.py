"""Spot S1 - die Altcoin-Phase als Fakt (Voranalyse_Spot_Neubau_04_10.md §13, vorab Commit 630eae9).

    python Basisinfos/Spot_Voranalyse_04_10/s1_messung.py

Nur lesend: data/messdaten.db (Krypto USD mit eingestellten), data/_spot/coinmetrics.db (ETH/BTC). Korb, Ereignis und Fakten exakt wie in
s1_vorpruefung.py. Fragen S1-H1 Deckung, S1-H2 Verzoegerung, S1-H3 Fehlalarm, S1-H4 Wirkung (Auskunft), dazu die Gegenrichtung.

AUSLEGUNG, vor dem ersten Lauf festgelegt:
  - grosse Phasen = Episoden mit >= 30 Tagen (2020-04, 2020-11, 2022-05); H1 zaehlt nur diese, die 9-Tage-Episode 2023 als Auskunft
  - H2: an bei Phasenbeginn, sonst erster An-Tag in der Phase; verpasst = Korb/BTC vom Phasenbeginn bis dahin (KORREKTUR 06.10.)
  - F2-Breite nur ueber Coins mit Kurs heute UND vor 90 T, mind. 20 (KORREKTUR 06.10.: neue Coins zaehlten als 'schlaegt BTC nicht')
  - H3: An-Tage ausserhalb aller Phasen (Puffer +-30 T) / alle An-Tage
  - H4: Einschaltung = erster An-Tag nach >= 10 Aus-Tagen; Korb gegen BTC in den folgenden 90 T
  - Auswahl (vorab §13.3): unter den Fakten mit H1 und H3 stimmig der mit der hoechsten mittleren Deckung; bei Gleichstand weniger An-Tage
"""
import os
import sqlite3

import numpy as np
import pandas as pd

os.chdir(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


def lade():
    c = sqlite3.connect("file:data/messdaten.db?mode=ro", uri=True)
    k = pd.read_sql("SELECT symbol, date, close, volume FROM price_history_ohlc WHERE assetklasse='krypto' AND currency='USD' AND date>='2018-09-01'",
                    c, parse_dates=["date"])
    c.close()
    K = k.pivot(index="date", columns="symbol", values="close").sort_index().asfreq("D")
    U = k.assign(u=k.close * k.volume).pivot(index="date", columns="symbol", values="u").sort_index().asfreq("D")
    return K, U


def top50(U, alts, m):
    vol = U.loc[m - pd.Timedelta(days=30):m, alts].mean().dropna()
    return vol.sort_values(ascending=False).index[:50]


def baue():
    K, U = lade()
    ret = K.pct_change(fill_method=None)
    stable = {s for s in K.columns if ret[s].abs().median() < 0.002}
    alts = [s for s in K.columns if s not in stable and s != "BTC"]
    B = K["BTC"]
    idx = K.index[K.index >= "2019-01-01"]
    korb_r = pd.Series(0.0, index=idx)
    tops = {}
    for m in pd.date_range("2019-01-01", idx[-1], freq="MS"):
        top = top50(U, alts, m)
        tops[m] = top
        sl = (idx >= m) & (idx < m + pd.offsets.MonthBegin(1))
        korb_r[idx[sl]] = ret.loc[idx[sl], top].fillna(0.0).mean(axis=1)
    korb = (1 + korb_r).cumprod()
    Bi = B.reindex(idx)
    rel90_vor = (korb.shift(-90) / korb) / (Bi.shift(-90) / Bi) - 1
    cm = sqlite3.connect("file:data/_spot/coinmetrics.db?mode=ro", uri=True)
    eb = pd.read_sql("SELECT tag, PriceUSD FROM tag WHERE asset='eth'", cm, parse_dates=["tag"]).set_index("tag").PriceUSD
    bb = pd.read_sql("SELECT tag, PriceUSD FROM tag WHERE asset='btc'", cm, parse_dates=["tag"]).set_index("tag").PriceUSD
    ethbtc = (eb / bb).reindex(idx)
    s200 = ethbtc.rolling(200).mean()
    F1 = (ethbtc > s200) & (s200 > s200.shift(20))
    breite = pd.Series(np.nan, index=idx)
    for t in idx[90:]:
        top = tops[t.replace(day=1)]
        a90 = (K.loc[t, top] / K.loc[t - pd.Timedelta(days=90), top]).dropna()   # KORREKTUR 06.10.: nur Coins mit beiden Kursen
        breite[t] = float((a90 > B[t] / B[t - pd.Timedelta(days=90)]).mean()) if len(a90) >= 20 else np.nan
    F2 = breite >= 0.75
    rs = korb / Bi
    r200 = rs.rolling(200).mean()
    F3 = (rs > r200) & (r200 > r200.shift(20))
    F4 = (F1.astype(int) + F2.astype(int) + F3.astype(int)) >= 2
    return dict(K=K, U=U, alts=alts, idx=idx, korb=korb, korb_r=korb_r, Bi=Bi, rel90_vor=rel90_vor, breite=breite, tops=tops,
                F={"F1 ETH/BTC ueber steigendem 200-T-Schnitt": F1, "F2 Altseason-Breite >= 75 %": F2,
                   "F3 Korb/BTC ueber steigendem 200-T-Schnitt": F3, "F4 mind. 2 von F1-F3": F4})


def episoden(phase):
    ep, a0 = [], None
    for t, v in phase.items():
        if v and a0 is None:
            a0 = t
        if not v and a0 is not None:
            if ep and (a0 - ep[-1][1]).days < 30:
                ep[-1] = (ep[-1][0], t)
            else:
                ep.append((a0, t))
            a0 = None
    return [(a, e) for a, e in ep if (e - a).days >= 7]


def main():
    d = baue()
    idx, korb, Bi = d["idx"], d["korb"], d["Bi"]
    ep = episoden(d["rel90_vor"] >= 0.25)
    gross = [(a, e) for a, e in ep if (e - a).days >= 30]
    print("Spot S1 - Altcoin-Phase als Fakt (Voranalyse_Spot §13) · Daten bis %s" % idx[-1].date())
    print("Phasen:", " · ".join("%s..%s (%d T)%s" % (a.date(), e.date(), (e - a).days, "" if (e - a).days >= 30 else " [Auskunft]") for a, e in ep))
    puffer = pd.Series(False, index=idx)
    for a, e in ep:
        puffer[a - pd.Timedelta(days=30):e + pd.Timedelta(days=30)] = True
    erg = {}
    for name, f in d["F"].items():
        f = f.reindex(idx).fillna(False)
        print("\n%s - an an %d Tagen" % (name, int(f.sum())))
        deck = []
        for a, e in ep:
            tage = f[a:e]
            dk = float(tage.mean())
            # KORREKTUR 06.10.: an bei Phasenbeginn? sonst erster An-Tag INNERHALB der Phase
            if bool(f.get(a, False)):
                h2 = "schon AN bei Phasenbeginn"
            else:
                w = f[a:e]
                erst = w[w].index.min() if w.any() else None
                if erst is not None:
                    verp = (korb[erst] / korb[a]) / (Bi[erst] / Bi[a]) - 1
                    h2 = "eingeschaltet %d T nach Beginn, bis dahin %+.0f %% Vorsprung verpasst" % ((erst - a).days, 100 * verp)
                else:
                    h2 = "waehrend der Phase NIE an"
            if (e - a).days >= 30:
                deck.append(dk)
            print("  Phase %s (%3d T): Deckung %3.0f %% (Gegenrichtung: aus an %3.0f %%) · %s%s" % (
                a.date(), (e - a).days, 100 * dk, 100 * (1 - dk), h2, "" if (e - a).days >= 30 else "  [Auskunft]"))
        h1 = sum(x >= 0.5 for x in deck) >= 2
        fa = float((f & ~puffer).sum() / max(f.sum(), 1))
        h3 = fa <= 0.5
        print("  S1-H1 Deckung >= 50 %% in >= 2 von 3 grossen Phasen: %s (%s) · S1-H3 Fehlalarm %.0f %% der An-Tage ausserhalb (Puffer 30 T): %s" % (
            "STIMMIG" if h1 else "nicht", " / ".join("%.0f %%" % (100 * x) for x in deck), 100 * fa, "STIMMIG" if h3 else "nicht"))
        ein = [t for t in f.index[f & (f.rolling(11).sum() == 1)]]
        w4 = []
        for t in ein:
            t90 = t + pd.Timedelta(days=90)
            if t90 <= idx[-1]:
                w4.append((t, (korb[t90] / korb[t]) / (Bi[t90] / Bi[t]) - 1))
        print("  S1-H4 Auskunft - Korb gegen BTC in 90 T nach jedem Einschalten: %s" % " · ".join("%s %+.0f %%" % (t.date(), 100 * v) for t, v in w4))
        if w4:
            print("         Median %+.0f %% · positiv %d von %d" % (100 * np.median([v for _t, v in w4]), sum(v > 0 for _t, v in w4), len(w4)))
        erg[name] = (h1, h3, float(np.mean(deck)) if deck else 0.0, int(f.sum()))
    gut = [(n, v) for n, v in erg.items() if v[0] and v[1]]
    print("\nAUSWAHL nach der Regel (§13.3):", (sorted(gut, key=lambda x: (-x[1][2], x[1][3]))[0][0] + " -> als FAKT in die Klima-Ampel") if gut else
          "KEIN Fakt erfuellt H1 und H3 -> die Ampel zeigt nur die Altseason-Breite als Zahl")
    from importlib import import_module  # noqa: F401
    q_src = open("Basisinfos/Spot_Voranalyse_04_10/k3_gewichten.py", encoding="utf-8").read().split("pb, mb = lade")[0]
    g = {"__file__": os.path.abspath("Basisinfos/Spot_Voranalyse_04_10/k3_gewichten.py")}
    exec(compile(q_src, "k3", "exec"), g)
    pb, mb = g["lade"]("btc")
    q = g["klima"](pb, mb, pd.Timestamp("2013-01-01"))
    print("\nKONTEXT BTC-Klima q waehrend der Phasen (Auskunft): " + " · ".join("%s Mittel %.2f (%.2f..%.2f)" % (
        a.date(), q[a:e].mean(), q[a:e].min(), q[a:e].max()) for a, e in ep))
    print("Altseason-Breite heute (%s): %.0f %% der Top 50 schlugen BTC in 90 T" % (d["breite"].dropna().index[-1].date(), 100 * d["breite"].dropna().iloc[-1]))


if __name__ == "__main__":
    main()
