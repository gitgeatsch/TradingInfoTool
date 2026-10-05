"""Spot K-3, Messplan FASSUNG 3 (Voranalyse_Spot_Neubau_04_10.md §8.10, Commit 78aecd0; E-64) - gewichten statt warten, Klima aus BTC, je Marktepoche.

    python Basisinfos/Spot_Voranalyse_04_10/k3_gewichten.py

Nur lesend: data/_spot/coinmetrics.db. Kein Netz, kein LLM, kein Betriebscode (T-2, T-5).

V3: Zufluss 1 am Zuflusstag ins Bargeld; am selben Tag Kauf von Bargeld x (1 - q des Vortags) zum Schlusskurs. q aus BTC: Mittel der
verfuegbaren (mind. 2) von Perzentil MVRV, 1 - Perzentil (Drawdown / Jahresschwankung), Perzentil Kurs/200-Wochen-Schnitt; wachsend ab 2013.
DCA: ganzer Zufluss am Zuflusstag. Nie verkaufen, Bargeld 0 %, keine Gebuehren.

AUSLEGUNG, vor dem ersten Lauf festgelegt (im Plan nicht genau bestimmt):
  - Zuflusstage: der Starttag selbst und danach jeder Monatserste (bei Start 11.01.2024 also 11.01., 01.02., ...)
  - F3-H2 je Epoche: Zufluesse nur innerhalb der Epoche; danach wird gehalten (Restbargeld bleibt Bargeld) und am 04.10.2026 bewertet
  - Nullwelt F3-H3: q-Reihe ab 16.05.2015 (alle drei Teile da) zirkulaer um 365 T bis Laenge-365 T verschoben
  - Groesster Rueckgang: auf Vermoegen / eingezahltes Kapital
"""
import os
import sqlite3

import numpy as np
import pandas as pd

os.chdir(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
RNG = np.random.default_rng(20261005)
N_NULL = 200
EPOCHEN = (("E1 Fruehzeit", "2017-01-01", "2020-12-31"), ("E2 Uebergang", "2021-01-01", "2024-01-10"), ("E3 ETF-Markt", "2024-01-11", None))
STARTS = ["%d-01-01" % j for j in range(2017, 2024)] + ["2024-01-11"]


def lade(asset):
    c = sqlite3.connect("file:data/_spot/coinmetrics.db?mode=ro", uri=True)
    d = pd.read_sql("SELECT tag, PriceUSD AS kurs, CapMVRVCur AS mvrv FROM tag WHERE asset=? ORDER BY tag", c, params=(asset,),
                    parse_dates=["tag"]).set_index("tag")
    c.close()
    return d["kurs"].asfreq("D").ffill(), d["mvrv"].asfreq("D").ffill()


def klima(p, mvrv, ab, rollend=False):
    def pct(x):
        if rollend:
            return x.rolling(1460, min_periods=730).rank(pct=True)
        return x[x.index >= ab].expanding(min_periods=365).rank(pct=True).reindex(p.index)
    dd = p / p.cummax() - 1
    vol = np.log(p).diff().rolling(365, min_periods=300).std() * np.sqrt(365)
    teile = [pct(mvrv), 1 - pct(-dd / vol), pct(p / p.rolling(1400, min_periods=1400).mean())]
    verf = sum(t.notna().astype(int) for t in teile)
    return (sum(t.fillna(0) for t in teile) / verf).where(verf >= 2)


def simuliere(p, q, start, zufluss_bis=None, variante="V3"):
    """Taegliche Reihe Vermoegen/eingezahlt ab start bis Datenende; Zufluesse bis zufluss_bis."""
    start = pd.Timestamp(start)
    idx = p.index[p.index >= start]
    bis = pd.Timestamp(zufluss_bis) if zufluss_bis else idx[-1]
    zt = [t for t in idx if (t == start or t.day == 1) and t <= bis]
    qv = q.shift(1).reindex(zt).values
    kurs = p.reindex(zt).values
    bar = coins = ein = 0.0
    c_l, b_l, e_l = [], [], []
    for i in range(len(zt)):
        ein += 1.0
        bar += 1.0
        kauf = bar if variante == "DCA" else bar * (1.0 - qv[i])
        coins += kauf / kurs[i]
        bar -= kauf
        c_l.append(coins); b_l.append(bar); e_l.append(ein)
    z = pd.DataFrame({"coins": c_l, "bar": b_l, "ein": e_l}, index=pd.DatetimeIndex(zt)).reindex(idx).ffill()
    verm = z["coins"] * p.reindex(idx) + z["bar"]
    r = pd.DataFrame({"verm": verm, "ein": z["ein"], "bar": z["bar"], "coins": z["coins"]})
    r.attrs["kaeufe"] = len(zt)
    return r


def rueckgang(r):
    x = r["verm"] / r["ein"]
    return float((x / x.cummax() - 1).min())


def einstand(r):
    return (r["ein"].iloc[-1] - r["bar"].iloc[-1]) / r["coins"].iloc[-1]


pb, mb = lade("btc")
pe, me_ = lade("eth")
q_btc = klima(pb, mb, pd.Timestamp("2013-01-01"))
q_btc_roll = klima(pb, mb, None, rollend=True)
q_eth_eigen = klima(pe, me_, pd.Timestamp("2015-08-08"))
ENDE = min(pb.index[-1], pe.index[-1])
pb, pe = pb[:ENDE], pe[:ENDE]
print("Spot K-3 gewichten statt warten - Messplan Fassung 3 (Voranalyse_Spot §8.10), Klima q aus BTC, Ende %s" % ENDE.date())

urteil = {}
for asset, p in (("BTC", pb), ("ETH", pe)):
    print()
    print("=" * 20, asset, "mit BTC-Klima", "=" * 20)
    print("F3-H1 Vermoegen gegen DCA, 8 Starts (Auskunft rechts: rollendes Fenster%s)" % (", ETH mit eigenem q" if asset == "ETH" else ""))
    print("  Start      | eingez. | DCA Verm. | V3 Verm. | V3/DCA | V3>=DCA Monatsenden | Rueckgang DCA / V3 | Einstand DCA / V3 | Bargeld V3 | Ausk. rollend%s" % (
        " | Ausk. ETH-eigen" if asset == "ETH" else ""))
    sieg = 0
    for st in STARTS:
        d, v = simuliere(p, q_btc, st, variante="DCA"), simuliere(p, q_btc, st)
        m = d.index[d.index.is_month_end & (d.index >= pd.Timestamp(st) + pd.DateOffset(years=1))]
        anteil = float((v.loc[m, "verm"] >= d.loc[m, "verm"]).mean()) if len(m) else float("nan")
        qv = v["verm"].iloc[-1] / d["verm"].iloc[-1]
        sieg += qv >= 1
        roll = simuliere(p, q_btc_roll, st)["verm"].iloc[-1] / d["verm"].iloc[-1]
        eig = (simuliere(p, q_eth_eigen, st)["verm"].iloc[-1] / d["verm"].iloc[-1]) if asset == "ETH" else None
        print("  %s |   %3d   | %9.1f | %8.1f |  %.3f |       %4.0f %%        | %+4.0f %% / %+4.0f %%   | %9.2f / %9.2f | %4.1f | %.3f%s" % (
            st, d["ein"].iloc[-1], d["verm"].iloc[-1], v["verm"].iloc[-1], qv, 100 * anteil, 100 * rueckgang(d), 100 * rueckgang(v),
            einstand(d), einstand(v), v["bar"].iloc[-1], roll, " | %.3f" % eig if eig is not None else ""))
    print("  -> V3 >= DCA in %d von 8 Starts: %s" % (sieg, "STIMMIG" if sieg >= 6 else "nicht stimmig"))
    urteil.setdefault("h1", []).append(sieg >= 6)

    print("F3-H2 je Epoche (Zufluesse nur in der Epoche, danach gehalten)")
    alle = True
    for name, a, b in EPOCHEN:
        d, v = simuliere(p, q_btc, a, b, "DCA"), simuliere(p, q_btc, a, b)
        e_end = pd.Timestamp(b) if b else ENDE
        q_end, q_fin = v.loc[e_end, "verm"] / d.loc[e_end, "verm"], v["verm"].iloc[-1] / d["verm"].iloc[-1]
        alle &= q_fin >= 1
        print("  %-13s %s..%s  V3/DCA am Epochenende %.3f · am %s %.3f  (Einstand DCA %.2f / V3 %.2f, Restbargeld %.1f von %d)" % (
            name, a, (b or str(ENDE.date())), q_end, ENDE.date(), q_fin, einstand(d.loc[:e_end]), einstand(v.loc[:e_end]),
            v.loc[e_end, "bar"], v.loc[e_end, "ein"]))
    print("  -> V3 >= DCA in allen drei Epochen: %s" % ("STIMMIG" if alle else "nicht stimmig"))
    urteil.setdefault("h2", []).append(alle)

print()
print("=" * 20, "F3-H3 Nullwelt (BTC): q-Reihe zirkulaer verschoben, %d x, Abstand >= 365 T" % N_NULL, "=" * 20)
q_ab = q_btc[q_btc.index >= "2015-05-16"]
h3 = []
for st in ("2017-01-01", "2021-01-01"):
    basis = simuliere(pb, q_btc, st, variante="DCA")["verm"].iloc[-1]
    echt = simuliere(pb, q_btc, st)["verm"].iloc[-1] / basis
    null = []
    for _ in range(N_NULL):
        qs = pd.Series(np.roll(q_ab.values, int(RNG.integers(365, len(q_ab) - 365))), index=q_ab.index)
        null.append(simuliere(pb, qs, st)["verm"].iloc[-1] / basis)
    rang = float(np.mean(np.array(null) < echt))
    h3.append(rang >= 0.90)
    print("  Start %s: echt %.3f x DCA · verschobenes Klima Median %.3f, 90. Perzentil %.3f · Rang %.3f -> %s" % (
        st, echt, float(np.median(null)), float(np.percentile(null, 90)), rang, "STIMMIG" if rang >= 0.90 else "nicht stimmig"))
urteil["h3"] = all(h3)

print()
print("=" * 20, "GESAMT nach den vorab festen Regeln (§8.10)", "=" * 20)
print("F3-H1 Vermoegen: BTC %s, ETH %s" % tuple("stimmig" if x else "nicht stimmig" for x in urteil["h1"]))
print("F3-H2 Epochen:   BTC %s, ETH %s" % tuple("stimmig" if x else "nicht stimmig" for x in urteil["h2"]))
print("F3-H3 Nullwelt:  %s" % ("stimmig" if urteil["h3"] else "nicht stimmig"))
h1, h3 = all(urteil["h1"]), urteil["h3"]
print("FOLGE (vorab): %s" % ("KANDIDAT -> laufende Mitschrift ab dem naechsten Monatsersten + Voranalyse Klima-Ampel (E3 siehe F3-H2)" if h1 and h3 else
                             "teilweise stimmig -> WORAN messen (E-63), Klima-Ampel als Fakt in der Mail" if h1 or h3 or any(urteil["h2"]) else
                             "fuer den heutigen Markt nicht belegt - festhalten, Ampel bleibt Fakt"))
