"""VORPRUEFUNG §32 - Ebenen, Zeithorizonte, Alt-Rally, und zwei Luecken des Spot-Konzepts (Spot §32) - nur lesend.

    python Basisinfos/Spot_Voranalyse_04_10/v32_vorpruefung.py [pfad_zur_prod_kopie.db]

Einziger Aufruf nach aussen: FRED DEXUSEU (EUR/USD, kostenfrei) fuer Teil D.
  A  INVENTAR je Kandidat (Desktop gemessen; NB aus dem Teilexport 08.10. 08:35, im Text gefuehrt)
  B  ALT-RALLY-EPISODEN ab 2023 (Ebene 2): taeglicher Altindex Top 100 nach Marktwert ohne BTC/ETH/SOL (monatlich neu gewichtet)
     gegen BTC; Episode = Index/BTC >= 1,15 x Tief der letzten 60 T; Episoden mit Luecke < 30 T verbunden.
     Dazu die Season-Definition aus S1 (Korb schlaegt BTC in 90 T um >= 25 Pp). Lage am Tief nur BESCHRIEBEN (wenige Ereignisse).
  C  LUECKE HANDELBARKEIT: Anteil der Watchlist-Grundgesamtheit (letzter Stichtag) und der Ausbrecher ab 2024 im Bitpanda-Katalog
     (Kopie der Prod-Sicherung, mode=ro; Katalog von HEUTE -> fuer die Vergangenheit eine Obergrenze)
  D  LUECKE KOSTEN: Bitpanda-Kaeufe/-Verkaeufe (Export 03.08.) gegen den Binance-Stundenschluss zur Handelsstunde, EUR/USD taeglich
     -> Aufschlag je Seite je Marktwert-Klasse (Median; die Stunde schwankt beiderseits, der Median ist robust)
"""
import io
import json
import os
import sqlite3
import sys

import numpy as np
import pandas as pd
import requests

PROD = sys.argv[1] if len(sys.argv) > 1 else None   # VOR den Imports: ein importiertes Modul veraendert sys.argv
HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HIER)
os.chdir(os.path.dirname(os.path.dirname(HIER)))
import as_messung as M      # noqa: E402
import ein_vorpruefung as EV  # noqa: E402
import mk_messung as MK     # noqa: E402

K, IDX, POS, BTCV = M.K, M.IDX, M.POS, M.BTCV
KERN = ("BTC", "ETH", "SOL")


def ro(p):
    return sqlite3.connect("file:%s?mode=ro" % p, uri=True)


def spanne(p, sql):
    try:
        return ro(p).execute(sql).fetchone()
    except Exception as e:
        return ("-", str(e)[:40])


def teil_a():
    print("A) INVENTAR (Desktop gemessen · NB laut Teilexport 08.10.)")
    z = [
        ("BTC-Dominanz BTCDOM (Binance-Index)", spanne("data/richtung_historie.db", "select min(stunde), max(stunde), count(*) from btcdom"), "stuendlich",
         "FEHLT (richtung_historie mit Absicht nur Desktop); nachladbar: Binance BTCDOMUSDT, frei"),
        ("BTC-Dominanz CoinGecko (macro_snapshot)", spanne("data/tradinginfotool.db", "select min(date), max(date), count(btc_dominance_pct) from macro_snapshot where btc_dominance_pct is not null"),
         "taeglich", "live, ungeeicht (Historie nur kostenpflichtig)"),
        ("ETH/BTC, BTC-Lage, Altindex, Breite (Kurse)", (str(IDX[0].date()), str(IDX[-1].date()), K.shape[1]), "taeglich",
         "messdaten Betriebskopie 500 T + stundenkurse(_alle) ab 2023 - ausreichend fuer 90/200 T"),
        ("Umlauf fuer Marktwert", spanne("data/umlaufmenge_cg.db", "select min(datum), max(datum), count(distinct symbol) from umlaufmenge"), "taeglich",
         "Betriebskopie 14 T + taeglich 06:35 fortgeschrieben"),
        ("Funding Altcoins (Historie)", spanne("data/funding_historie.db", "select min(datum), max(datum), count(distinct symbol) from funding"), "8 h",
         "nur Symbolliste; LIVE open_interest_snapshot (funding_rate)"),
        ("Open Interest (Historie)", spanne("data/terminmarkt_historie.db", "select min(tag), max(tag), count(distinct symbol) from terminmarkt_tag"), "taeglich",
         "nur Symbolliste; LIVE open_interest_snapshot"),
        ("Fear & Greed", spanne("data/tradinginfotool.db", "select min(date), max(date), count(fear_greed_value) from macro_snapshot where fear_greed_value is not null"), "taeglich",
         "macro_snapshot live"),
        ("Makro monatlich (Zins, DXY, 10J, CPI, Oel, SPX)", spanne("data/tradinginfotool.db", "select min(monat), max(monat), count(*) from makro_historie_monat"), "monatlich",
         "makro_historie_monat vorhanden"),
        ("Netto-Liquiditaet FED (WALCL-TGA-RRP)", ("FRED, frei", "live abrufbar", "-"), "woechentlich", "nicht abgelegt (nur in l_messung am Desktop abgerufen)"),
        ("Stablecoin-Umlauf", ("DefiLlama, frei", "live abrufbar", "-"), "taeglich", "nicht abgelegt"),
        ("Halving-Zyklus", ("2020-05-11", "2024-04-20", "Konstanten"), "-", "Konstante"),
    ]
    for name, sp, aufl, nb in z:
        print("  %-45s Desktop %-40s %-12s NB: %s" % (name, " .. ".join(str(x) for x in sp), aufl, nb))


def altindex_taeglich(gewicht="mw"):
    tage = IDX[(IDX >= "2023-01-01")]
    r_tag = K.pct_change(fill_method=None)
    b_tag = pd.Series(BTCV, index=IDX).pct_change()
    werte = []
    for t in pd.date_range("2023-01-01", M.ENDE, freq="MS"):
        if t not in POS:
            continue
        _, rg = MK.rang_mw(t)
        top = [s for s in rg.sort_values().index if s not in KERN][:100]
        i = POS[t]
        w = pd.Series({s: MK.umlauf(s, t) * K[s].values[i] for s in top}).dropna()
        w = w[w > 0]
        if gewicht == "gleich":
            w = w * 0 + 1
        ende = (t + pd.DateOffset(months=1))
        mt = tage[(tage > t) & (tage <= ende)]
        rr = r_tag.loc[mt, w.index]
        tagesr = (rr.mul(w, axis=1).sum(axis=1) / rr.notna().mul(w, axis=1).sum(axis=1))
        werte.append(((1 + tagesr) / (1 + b_tag.loc[mt])) - 1)
    rel = pd.concat(werte)
    rel = rel[~rel.index.duplicated()]
    return (1 + rel.fillna(0)).cumprod()


def episoden(I, schwelle=1.15, fenster=60, luecke=30):
    tief = I.rolling(fenster, min_periods=20).min()
    an = I >= schwelle * tief
    tage = I.index[an.values]
    ep = []
    for d in tage:
        if ep and (d - ep[-1][1]).days < luecke:
            ep[-1][1] = d
        else:
            ep.append([d, d])
    out, gesehen = [], set()
    for a, e in ep:
        f = I[a - pd.Timedelta(days=fenster):a]
        d_tief = f.idxmin()
        nach = I[a:e + pd.Timedelta(days=30)]
        d_hoch = nach.idxmax()
        if d_tief in gesehen:                                       # gleiche Episode, zweimal eingeschaltet -> die spaetere Spitze behalten
            out = [o for o in out if o["tief"] != d_tief]
        gesehen.add(d_tief)
        out.append(dict(tief=d_tief, an=a, hoch=d_hoch, anstieg=I[d_hoch] / I[d_tief] - 1, dauer=(d_hoch - d_tief).days,
                        danach_90=I[min(d_hoch + pd.Timedelta(days=90), I.index[-1])] / I[d_hoch] - 1))
    return pd.DataFrame(out)


def lage(d):
    i = POS.get(d)
    if i is None:
        i = int(np.searchsorted(IDX, d))
    dom = None
    try:
        c = ro("data/richtung_historie.db")
        x = pd.read_sql("select stunde, close from btcdom where stunde between ? and ?", c,
                        params=[(d - pd.Timedelta(days=30)).strftime("%Y-%m-%d"), (d + pd.Timedelta(days=1)).strftime("%Y-%m-%d")])
        dom = x.close.iloc[-1] / x.close.iloc[0] - 1 if len(x) > 24 else None
    except Exception:
        pass
    ath = np.nanmax(BTCV[:i + 1])
    eth = K["ETH"].values
    return dict(btc90=BTCV[i] / BTCV[i - 90] - 1, btc_unter_ath=1 - BTCV[i] / ath, eth_btc30=(eth[i] / eth[i - 30]) / (BTCV[i] / BTCV[i - 30]) - 1,
                dom30=dom, breite=EV.breite(d.to_period("M").to_timestamp()) if d.to_period("M").to_timestamp() in POS else np.nan)


def teil_b():
    print("\nB) ALT-RALLY-EPISODEN ab 2023 (Ebene 2) - Index Top 100 nach Marktwert ohne BTC/ETH/SOL, gegen BTC, taeglich")
    for gw in ("mw", "gleich"):
        I = altindex_taeglich(gw)
        E = episoden(I)
        print("  %s gewichtet: Index/BTC %s %.3f -> %s %.3f · Episoden (>= +15 %% in 60 T): %d" % (
            "marktwert" if gw == "mw" else "gleich", I.index[0].date(), I.iloc[0], I.index[-1].date(), I.iloc[-1], len(E)))
        for r in E.itertuples():
            l = lage(r.tief)
            print("    Tief %s -> Hoch %s (%3d T) %+5.0f %% · 90 T nach dem Hoch %+4.0f %% | am Tief: BTC 90T %+4.0f %% · BTC unter ATH %3.0f %% · ETH/BTC 30T %+4.0f %% · BTCDOM 30T %s · Breite %s" % (
                r.tief.date(), r.hoch.date(), r.dauer, 100 * r.anstieg, 100 * r.danach_90, 100 * l["btc90"], 100 * l["btc_unter_ath"], 100 * l["eth_btc30"],
                "%+.1f %%" % (100 * l["dom30"]) if l["dom30"] is not None else "-", "%.2f" % l["breite"] if l["breite"] == l["breite"] else "-"))
        fw = I.shift(-90) / I - 1
        season = (fw >= 0.25)
        print("    Season nach S1 (>= +25 %% in den folgenden 90 T): Tage %d von %d" % (int(season.sum()), int(fw.notna().sum())))
        if gw == "mw":
            I.to_csv(os.path.join("data", "_spot", "v32_altindex_mw.csv"), sep=";")


def teil_c():
    print("\nC) LUECKE HANDELBARKEIT (Bitpanda-Katalog von heute, Kopie der Prod-Sicherung)")
    if not PROD:
        print("  ohne Prod-Kopie nicht pruefbar"); return set()
    kat = pd.read_sql("select symbol, gruppe from bitpanda_katalog where gruppe in ('coin','token')", ro(PROD))
    bp = set(kat.symbol.str.upper())
    letzte = max(t for t in pd.date_range("2023-01-01", M.ENDE, freq="MS") if t in POS)
    kl = MK.klassen_mw(letzte)[0]
    kl = {s: k for s, k in kl.items() if s not in KERN}
    basis = lambda s: MK.HU.vervielfacher(s)[1]                    # 1000SATS -> SATS
    drin = {s: (s in bp or basis(s) in bp) for s in kl}
    print("  Bitpanda Krypto-Werte: %d · Watchlist-Grundgesamtheit am %s: %d Coins · bei Bitpanda %d (%.0f %%) · H %s · M %s · S %s" % (
        len(bp), letzte.date(), len(kl), sum(drin.values()), 100 * np.mean(list(drin.values())),
        *("%d/%d" % (sum(drin[s] for s in kl if kl[s] == k), sum(1 for s in kl if kl[s] == k)) for k in "HMS")))
    la = pd.read_csv(os.path.join("data", "_spot", "lage_e3_anker.csv"), sep=";", parse_dates=["t"])
    a = la[(la.t >= "2024-01-01") & (la.hoch >= 1)]
    sy = a.sym.unique()
    print("  Ausbrecher ab 2024 (Lagebild L2): %d Coins · bei Bitpanda %d (%.0f %%) · die 15 groessten: %s" % (
        len(sy), sum(s in bp or basis(s) in bp for s in sy), 100 * np.mean([s in bp or basis(s) in bp for s in sy]),
        " ".join("%s%s" % (s, "" if (s in bp or basis(s) in bp) else "(-)") for s in a.groupby("sym").hoch.max().sort_values(ascending=False).head(15).index)))
    return bp


def stundenkurs(sym, ts):
    for db in ("data/stundenkurse.db", "data/stundenkurse_alle.db"):
        try:
            x = ro(db).execute("select close from stundenkurse where symbol=? and stunde=?", (sym, ts)).fetchone()
            if x and x[0]:
                return x[0]
        except Exception:
            continue
    return None


def teil_d():
    print("\nD) LUECKE KOSTEN - Bitpanda-Handel (Export 03.08.) gegen Binance-Stundenschluss zur Handelsstunde")
    d = json.load(open(r"K:/My Drive/Claude_Austauschordner/Notebook_Analysedaten/bitpanda_transaktionen.json", encoding="utf-8"))
    tr = [x for x in d["transaktionen"] if x["type"] in ("buy", "sell") and x.get("trade_price") and x.get("unix_timestamp")]
    fx = pd.read_csv(io.StringIO(requests.get("https://fred.stlouisfed.org/graph/fredgraph.csv?id=DEXUSEU", timeout=60).text))
    fx.columns = ["datum", "eurusd"]
    fx["datum"] = pd.to_datetime(fx.datum)
    fx["eurusd"] = pd.to_numeric(fx.eurusd, errors="coerce")
    fx = fx.dropna().set_index("datum").eurusd
    z = []
    for x in tr:
        s = x["cryptocoin_symbol"].upper()
        if s in ("EURCV", "USDC", "USDT", "BEST"):
            continue
        ts = pd.Timestamp(int(x["unix_timestamp"]), unit="s")
        h = ts.floor("h").strftime("%Y-%m-%d %H:00")
        k = stundenkurs(s, h)
        e = fx[:ts.normalize()]
        if k is None or not len(e):
            z.append(dict(sym=s, seite=x["type"], ok=False)); continue
        auf = float(x["trade_price"]) * e.iloc[-1] / k - 1
        t = ts.normalize().to_period("M").to_timestamp()
        kl = MK.klassen_mw(t)[0].get(s, "?") if t in POS else "?"
        z.append(dict(sym=s, seite=x["type"], ok=True, auf=auf, kl=kl, t=ts))
    D = pd.DataFrame(z)
    ok = D[D.ok]
    ok = ok[ok.auf.abs() < 0.5]                                            # grobe Zuordnungsfehler (andere Symbolwelt) heraus
    print("  Handel %d · mit Binance-Stundenkurs %d (%.0f %%) · nach Ausreisserfilter |Aufschlag| < 50 %%: %d" % (len(D), int(D.ok.sum()), 100 * D.ok.mean(), len(ok)))
    for kl in ("H", "M", "S", "?", "alle"):
        g = ok if kl == "alle" else ok[ok.kl == kl]
        b, v = g[g.seite == "buy"].auf, g[g.seite == "sell"].auf
        if len(b) < 10 or len(v) < 10:
            continue
        print("    %-4s Kauf n %4d Median %+5.2f %% · Verkauf n %4d Median %+5.2f %% -> halbe Spanne %.2f %% je Seite (Annahme bisher 1,25 %%)" % (
            kl, len(b), 100 * b.median(), len(v), 100 * v.median(), 100 * (b.median() - v.median()) / 2))
    ok.to_csv(os.path.join("data", "_spot", "v32_kosten.csv"), sep=";", index=False)


def main():
    print("VORPRUEFUNG §32 · Kurse bis %s\n" % M.ENDE.date())
    teil_a()
    teil_b()
    teil_c()
    teil_d()


if __name__ == "__main__":
    main()
