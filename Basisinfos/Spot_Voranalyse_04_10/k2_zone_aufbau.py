"""Spot K-2, Messplan FASSUNG 2 (Voranalyse_Spot_Neubau_04_10.md §8.8, Commit 91f60dd; E-62) - die Zone als Aufbaufenster, BTC und ETH.

    python Basisinfos/Spot_Voranalyse_04_10/k2_zone_aufbau.py

Nur lesend: data/_spot/coinmetrics.db, fuer V3 (Wende) zusaetzlich data/messdaten.db (Breite). Kein Netz, kein LLM, kein Betriebscode.

Zustaende A1-A3 unveraendert aus Fassung 1 (k1_klima_studie.py); A = mindestens 2 der verfuegbaren, mindestens 2. Jeder Kauf zum Schlusskurs
von t+1, wenn A am Tag t an war. Vergleichsbasis = alle Tage seit 01.01.2017, nie ein Fenster um ein bekanntes Tief.

AUSLEGUNG, vor dem ersten Lauf festgelegt (im Plan nicht genau bestimmt):
  - Folgeertrag F2-H1: Schluss(t+1+h) / Schluss(t+1) - 1
  - Groesster Rueckgang F2-H3: auf dem Verhaeltnis Vermoegen / eingezahltes Kapital (sonst verdecken die Zufluesse jeden Rueckgang)
  - Zufluss am 1. jedes Monats vor dem Kauf desselben Tages; DCA kauft am 1. zum Schluss
  - Nullwelt F2-H3: A-Reihe ab 2017 zirkulaer verschoben (Mindestabstand 30 T), V2 bei Start 2017
"""
import os
import sqlite3

import numpy as np
import pandas as pd

os.chdir(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
RNG = np.random.default_rng(20261005)
START = pd.Timestamp("2017-01-01")
N_NULL = 200


def ro(p):
    return sqlite3.connect("file:%s?mode=ro" % p.replace("\\", "/"), uri=True)


def lade(asset):
    c = ro("data/_spot/coinmetrics.db")
    d = pd.read_sql("SELECT tag, PriceUSD AS kurs, CapMVRVCur AS mvrv FROM tag WHERE asset=? ORDER BY tag", c, params=(asset,),
                    parse_dates=["tag"]).set_index("tag")
    c.close()
    return d["kurs"].asfreq("D").ffill(), d["mvrv"].asfreq("D").ffill()


def zone(p, mvrv, ab):
    def pw(x):
        return x[x.index >= ab].expanding(min_periods=365).rank(pct=True).reindex(p.index)
    dd = p / p.cummax() - 1
    vol = np.log(p).diff().rolling(365, min_periods=300).std() * np.sqrt(365)
    r = [pw(mvrv), pw(-dd / vol), pw(p / p.rolling(1400, min_periods=1400).mean())]
    an = (r[0] <= 0.20).astype(int) + (r[1] >= 0.80).astype(int) + (r[2] <= 0.20).astype(int)
    verf = sum(x.notna().astype(int) for x in r)
    return (an >= 2) & (verf >= 2)


def wende_btc(p):
    c = ro("data/messdaten.db")
    k = pd.read_sql("SELECT symbol, date, close FROM price_history_ohlc WHERE assetklasse='krypto' AND currency='USD'", c, parse_dates=["date"])
    c.close()
    K = k.pivot(index="date", columns="symbol", values="close").sort_index().asfreq("D")
    s50 = K.rolling(50, min_periods=40).mean()
    g = s50.notna().sum(axis=1)
    breite = (((K > s50) & s50.notna()).sum(axis=1) / g.where(g >= 50)).reindex(p.index)
    sprung = (breite >= 0.80) & (breite.rolling(20, min_periods=15).min() <= 0.30)
    B1 = sprung.astype(float).rolling(60, min_periods=1).max().fillna(0) > 0
    s200 = p.rolling(200, min_periods=200).mean()
    B = ((p > s200) & (s200 > s200.shift(20))) & (p.rolling(30).min() > p.shift(30).rolling(60).min()) & (B1 | breite.isna())
    return B & (B.rolling(11).sum() == 1)                     # Einschaltung wie Fassung 1


def episoden(A):
    an = A[A & (A.index >= START)].index
    ep = []
    for t in an:
        if ep and (t - ep[-1][1]).days < 30:
            ep[-1][1] = t
            ep[-1][2] += 1
        else:
            ep.append([t, t, 1])
    return ep


def simuliere(p, A, start, variante, wende=None):
    """Endvermoegen-Reihe (Vermoegen, eingezahlt) taeglich ab start; Kauf an t+1 nach A[t]."""
    idx = p.index[p.index >= start]
    kurs = p.reindex(idx).values
    a_vor = A.shift(1).reindex(idx).fillna(False).values.astype(bool)
    w_vor = wende.shift(1).reindex(idx).fillna(False).values.astype(bool) if wende is not None else np.zeros(len(idx), bool)
    erster = (idx.day == 1)
    bestand = bar = ein = 0.0
    kaeufe = 0
    verm, einz = np.empty(len(idx)), np.empty(len(idx))
    for i in range(len(idx)):
        if erster[i]:
            ein += 1.0
            bar += 1.0
        kauf = 0.0
        if variante == "DCA":
            kauf = bar if erster[i] else 0.0
        elif variante == "V1":
            kauf = bar if a_vor[i] else 0.0
        elif variante in ("V2", "V3"):
            kauf = bar / 30.0 if a_vor[i] else 0.0
            if variante == "V3" and w_vor[i]:
                kauf = bar
        if kauf > 0:
            bestand += kauf / kurs[i]
            bar -= kauf
            kaeufe += 1
        verm[i] = bestand * kurs[i] + bar
        einz[i] = ein
    r = pd.DataFrame({"verm": verm, "ein": einz}, index=idx)
    r.attrs.update(bestand=bestand, bar=bar, kaeufe=kaeufe, investiert=ein - bar)
    return r


def max_rueckgang(r):
    q = r["verm"] / r["ein"]
    return float((q / q.cummax() - 1).min())


def h1(p, A, ab, bis=None):
    zeilen = []
    for h in (180, 365):
        f = (p.shift(-(1 + h)) / p.shift(-1) - 1)
        m = f.notna() & (f.index >= ab) & (True if bis is None else (f.index < bis))
        fw, aw = f[m].values, A[m].values.astype(bool)
        if aw.sum() < 10:
            zeilen.append((h, None, None, int(aw.sum()), None))
            continue
        diff = fw[aw].mean() - fw.mean()
        null = [fw[np.roll(aw, int(RNG.integers(30, len(aw) - 30)))].mean() - fw.mean() for _ in range(N_NULL)]
        zeilen.append((h, diff, float(np.mean(np.array(null) < diff)), int(aw.sum()), (fw[aw].mean(), fw.mean())))
    return zeilen


ergebnis = {}
print("Spot K-2 Zone als Aufbaufenster - Messplan Fassung 2 (Voranalyse_Spot §8.8), BTC und ETH, Messbeginn 2017-01-01")
for asset, ab in (("btc", pd.Timestamp("2013-01-01")), ("eth", pd.Timestamp("2015-08-08"))):
    p, mvrv = lade(asset)
    A = zone(p, mvrv, ab)
    ende = p.index[-1]
    E = asset.upper()
    print()
    print("=" * 20, E, "(Daten bis %s)" % ende.date(), "=" * 20)

    # ---- F2-H1 ----
    print("F2-H1 Zone-Ertrag: Folgeertrag ab t+1, A-Tage gegen alle Tage, zweiseitig (>= 0,95 besser, <= 0,05 UMGEKEHRT)")
    tests = []
    for name, von, bis, zaehlt in (("seit 2017", START, None, True), ("ab 2019 (Auskunft)", pd.Timestamp("2019-01-01"), None, False),
                                   ("ab 2023 (Auskunft, Messfokus)", pd.Timestamp("2023-01-01"), None, False)):
        if name.startswith("ab 2019") and asset == "btc":
            continue
        for h, diff, rang, n, mw in h1(p, A, von, bis):
            if diff is None:
                print("  %-30s %3d T: zu wenige A-Tage mit vollem Ertrag (%d)" % (name, h, n))
                continue
            urteil = "BESSER" if rang >= 0.95 else "UMGEKEHRT" if rang <= 0.05 else "unauffaellig"
            print("  %-30s %3d T: A-Tage %4d  Ertrag %+5.0f %% gegen alle Tage %+5.0f %% (Unterschied %+5.0f Pp)  Nullwelt-Rang %.3f  %s" % (
                name, h, n, 100 * mw[0], 100 * mw[1], 100 * diff, rang, urteil))
            if zaehlt:
                tests.append(urteil)
    ergebnis.setdefault("h1", []).extend(tests)

    # ---- F2-H2 ----
    print("F2-H2 fallendes Messer: je Episode (Luecke >= 30 T trennt), Einstieg zum Schluss am Tag nach dem ersten A-Tag")
    voll, ueber = 0, 0
    for a, b, n in episoden(A):
        t1 = a + pd.Timedelta(days=1)
        e = p[t1]
        fenster = p[t1:t1 + pd.Timedelta(days=365)]
        tief = fenster.min()
        hat = t1 + pd.Timedelta(days=365) <= ende
        nach = p[t1 + pd.Timedelta(days=365)] / e - 1 if hat else None
        if hat:
            voll += 1
            ueber += nach > 0
        print("  %s..%s (%3d A-Tage)  Einstieg %9.2f  danach tiefstens %+4.0f %% (am %s)%s  nach 365 T %s" % (
            a.date(), b.date(), n, e, 100 * (tief / e - 1), fenster.idxmin().date(), "  WEITERE -20 %" if tief < 0.8 * e else "",
            "%+.0f %%" % (100 * nach) if hat else "offen bis %s" % (t1 + pd.Timedelta(days=365)).date()))
    print("  -> Kurs nach 365 T ueber dem Einstieg: %d von %d Episoden mit vollem Fenster: %s" % (
        ueber, voll, "GESTUETZT" if voll and ueber / voll >= 2 / 3 else "nicht gestuetzt"))
    ergebnis.setdefault("h2", []).append(voll and ueber / voll >= 2 / 3)

    # ---- F2-H3 ----
    wende = wende_btc(p) if asset == "btc" else None
    print("F2-H3 Aufbau gegen DCA: Zufluss 1 je Monat, nie verkaufen, Bargeld 0 %%, keine Gebuehren; Endstand %s" % ende.date())
    print("  Start | eingezahlt | DCA Verm. | V2 Verm. (V2/DCA) | V1/DCA | V3/DCA | V2>=DCA an Monatsenden | groesster Rueckgang DCA / V2 | Einstand DCA / V2 | Bargeld V2 am Ende | Kaeufe DCA/V2")
    sieg = 0
    for jahr in range(2017, 2024):
        st = pd.Timestamp("%d-01-01" % jahr)
        r = {v: simuliere(p, A, st, v, wende) for v in (("DCA", "V1", "V2", "V3") if wende is not None else ("DCA", "V1", "V2"))}
        d, v2 = r["DCA"], r["V2"]
        me = d.index[(d.index.is_month_end) & (d.index >= st + pd.DateOffset(years=1))]
        anteil = float((v2.loc[me, "verm"] >= d.loc[me, "verm"]).mean())
        q = v2["verm"].iloc[-1] / d["verm"].iloc[-1]
        sieg += q > 1
        ein_d = d.attrs["investiert"] / d.attrs["bestand"]
        ein_2 = v2.attrs["investiert"] / v2.attrs["bestand"] if v2.attrs["bestand"] > 0 else float("nan")
        print("  %d  | %4d | %8.1f | %8.1f (%.2f) | %.2f | %s | %4.0f %% | %+4.0f %% / %+4.0f %% | %9.2f / %9.2f | %5.1f (%3.0f %%) | %d/%d" % (
            jahr, d["ein"].iloc[-1], d["verm"].iloc[-1], v2["verm"].iloc[-1], q, r["V1"]["verm"].iloc[-1] / d["verm"].iloc[-1],
            "%.2f" % (r["V3"]["verm"].iloc[-1] / d["verm"].iloc[-1]) if "V3" in r else "  - ", 100 * anteil,
            100 * max_rueckgang(d), 100 * max_rueckgang(v2), ein_d, ein_2, v2.attrs["bar"], 100 * v2.attrs["bar"] / d["ein"].iloc[-1],
            d.attrs["kaeufe"], v2.attrs["kaeufe"]))
    print("  -> V2 vor DCA in %d von 7 Startjahren: %s" % (sieg, "GESTUETZT" if sieg >= 5 else "nicht gestuetzt"))
    ergebnis.setdefault("h3", []).append(sieg >= 5)

    # Nullwelt V2 bei Start 2017 (Auskunft)
    basis_d = simuliere(p, A, START, "DCA")["verm"].iloc[-1]
    echt = simuliere(p, A, START, "V2")["verm"].iloc[-1] / basis_d
    a_ab = A[A.index >= START]
    null = []
    for _ in range(N_NULL):
        sv = pd.Series(np.roll(a_ab.values, int(RNG.integers(30, len(a_ab) - 30))), index=a_ab.index)
        null.append(simuliere(p, sv, START, "V2")["verm"].iloc[-1] / basis_d)
    print("  Nullwelt V2 Start 2017 (Auskunft): echt %.2f x DCA · Zufallszonen gleicher Laenge Median %.2f, 95. Perzentil %.2f · Rang %.3f" % (
        echt, float(np.median(null)), float(np.percentile(null, 95)), float(np.mean(np.array(null) < echt))))

print()
print("=" * 20, "GESAMT nach den vorab festen Regeln (§8.8)", "=" * 20)
t = ergebnis["h1"]
g1 = sum(x == "BESSER" for x in t) >= 3 and "UMGEKEHRT" not in t
print("F2-H1 Zone-Ertrag: %s -> %s" % (", ".join(t), "GESTUETZT" if g1 else "nicht gestuetzt" + (" (UMGEKEHRT dabei)" if "UMGEKEHRT" in t else "")))
print("F2-H2 fallendes Messer: BTC %s, ETH %s" % tuple("gestuetzt" if x else "nicht gestuetzt" for x in ergebnis["h2"]))
g3 = all(ergebnis["h3"])
print("F2-H3 Aufbau gegen DCA: BTC %s, ETH %s -> %s" % (*("ja" if x else "nein" for x in ergebnis["h3"]), "GESTUETZT" if g3 else "nicht gestuetzt"))
print("FOLGE (vorab): %s" % ("Zone wird Aufbaugrundlage -> Voranalyse Betrieb" if g1 and g3 else
                             "kein Aufbau, Klima-Ampel als Fakt in der Mail, Ob beim Nutzer" if g1 or g3 else
                             "Spot ueber das Klima so nicht nachweisbar - festhalten"))
