# -*- coding: utf-8 -*-
"""G16 Wale, Schritt a: STICHPROBE der Binance-Großgeschäfte (29.10.2026, Nutzer: *„ok starten wir mit a bei den Walen“*).

Zweck: die SCHWELLE für „groß“ ist eine Messung, keine Wahl. Deshalb wird hier nicht gezählt, was über einer Schwelle liegt, sondern
die ganze VERTEILUNG der Geschäftsgrößen je Tag festgehalten — jede spätere Schwelle lässt sich daraus ohne neuen Download ablesen.

    Markt      Spot BTCUSDT und USDⓈ-M-Futures BTCUSDT (Binance-Archiv data.binance.vision, aggTrades je Tag)
    Monate     03/2023 (bis 22.03. 00:00 UTC gebührenfrei, danach nicht — der Bruch liegt IM Monat) · 03/2024 · 03/2026
    Einheit    aggTrade (ein Taker-Auftrag zu EINEM Preis) und SWEEP (aufeinanderfolgende aggTrades mit derselben Zeit und
               derselben Seite = ein Auftrag, der mehrere Preisstufen abräumt). ⚠️ Ein großer Auftrag zerfällt sonst in kleine Stücke.
    Ablage     data/_wale/wale_stichprobe.db — NUR Verdichtung, die Rohdatei wird im Speicher gelesen und nicht gespeichert
    Abgleich   Tagesumsatz gegen die Tageskerze per REST (das Archiv hat abgeschnittene Kerzen — hier gilt REST)

    python -X utf8 Basisinfos/Rechenkern_02_10/wale_stichprobe.py            # laden (setzt fort, fertige Tage werden übersprungen)
    python -X utf8 Basisinfos/Rechenkern_02_10/wale_stichprobe.py --ohne-spot-2023   # ohne den 2,66-GB-Monat
    python -X utf8 Basisinfos/Rechenkern_02_10/wale_stichprobe.py --bericht  # Verteilung und Abgleich ausgeben
    python -X utf8 Basisinfos/Rechenkern_02_10/wale_stichprobe.py --schwelle # relative Schwelle: Grenze je q, Großfluss gegen Rest
"""
import calendar
import io
import math
import os
import sqlite3
import sys
import time
import zipfile
from datetime import datetime, timezone

import numpy as np
import pandas as pd
import requests

HIER = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.dirname(os.path.dirname(HIER))
ABLAGE = os.path.join(PROJ, "data", "_wale", "wale_stichprobe.db")
MAERKTE = {"spot": ("spot", "https://api.binance.com/api/v3/klines"),
           "futures": ("futures/um", "https://fapi.binance.com/fapi/v1/klines")}
MONATE = ((2023, 3), (2024, 3), (2026, 3))
# Größenklassen in USD: Viertel-Dekaden von 1 $ bis 1 Mrd. $ (Klasse k = Untergrenze 10^(k/4))
KLASSEN = 37
SPALTEN = ["id", "preis", "menge", "erste", "letzte", "zeit", "kaeufer_maker", "best"]


def verbinde():
    os.makedirs(os.path.dirname(ABLAGE), exist_ok=True)
    c = sqlite3.connect(ABLAGE)
    c.executescript("""
    CREATE TABLE IF NOT EXISTS tag (markt TEXT, datum TEXT, umsatz_usd REAL, kauf_usd REAL, aggtrades INTEGER, sweeps INTEGER,
                                    kerze_usd REAL, kerze_kauf_usd REAL, geholt TEXT, PRIMARY KEY (markt, datum));
    -- einheit: 'agg' oder 'sweep'; seite: 'kauf' (Taker kauft) oder 'verkauf'; klasse k = Untergrenze 10^(k/4) USD
    CREATE TABLE IF NOT EXISTS verteilung (markt TEXT, datum TEXT, einheit TEXT, seite TEXT, klasse INTEGER, anzahl INTEGER,
                                           usd REAL, PRIMARY KEY (markt, datum, einheit, seite, klasse));
    """)
    return c


def _hole(url, params=None, versuche=4):
    for v in range(versuche):
        try:
            r = requests.get(url, params=params, timeout=300)
            if r.status_code == 200:
                return r
        except requests.RequestException:
            pass
        time.sleep(15 * (v + 1))
    return None


def lies_tag(markt: str, datum: str) -> pd.DataFrame | None:
    pfad = MAERKTE[markt][0]
    r = _hole("https://data.binance.vision/data/%s/daily/aggTrades/BTCUSDT/BTCUSDT-aggTrades-%s.zip" % (pfad, datum))
    if r is None:
        return None
    with zipfile.ZipFile(io.BytesIO(r.content)) as z:
        roh = z.read(z.namelist()[0])
    kopf = roh[:40].decode("ascii", "replace")
    df = pd.read_csv(io.BytesIO(roh), header=0 if kopf[:1].isalpha() else None, usecols=[1, 2, 5, 6])
    df.columns = ["preis", "menge", "zeit", "kaeufer_maker"]
    df["kaeufer_maker"] = df["kaeufer_maker"].astype(str).str.lower().isin(("true", "1"))
    return df


def verdichte(df: pd.DataFrame):
    usd = (df["preis"] * df["menge"]).to_numpy()
    kauf = ~df["kaeufer_maker"].to_numpy()                       # Käufer ist NICHT Maker -> Käufer ist Taker -> Kauf
    zeit = df["zeit"].to_numpy()
    # Sweep: neue Gruppe, sobald Zeit oder Seite wechselt
    neu = np.r_[True, (zeit[1:] != zeit[:-1]) | (kauf[1:] != kauf[:-1])]
    gruppe = np.cumsum(neu) - 1
    sw_usd = np.bincount(gruppe, weights=usd)
    sw_kauf = kauf[neu]
    zeilen = []
    for einheit, u, k in (("agg", usd, kauf), ("sweep", sw_usd, sw_kauf)):
        kl = np.clip(np.floor(4 * np.log10(np.maximum(u, 1.0))).astype(int), 0, KLASSEN - 1)
        for seite, maske in (("kauf", k), ("verkauf", ~k)):
            n = np.bincount(kl[maske], minlength=KLASSEN)
            s = np.bincount(kl[maske], weights=u[maske], minlength=KLASSEN)
            zeilen += [(einheit, seite, int(i), int(n[i]), float(s[i])) for i in range(KLASSEN) if n[i]]
    return float(usd.sum()), float(usd[kauf].sum()), len(usd), len(sw_usd), zeilen


def kerze(markt: str, datum: str):
    t0 = int(datetime.fromisoformat(datum).replace(tzinfo=timezone.utc).timestamp() * 1000)
    r = _hole(MAERKTE[markt][1], {"symbol": "BTCUSDT", "interval": "1d", "startTime": t0, "limit": 1})
    if r is None or not r.json():
        return None, None
    k = r.json()[0]
    return float(k[7]), float(k[10])                              # Quote-Umsatz, Taker-Kauf-Quote-Umsatz


def lade():
    c = verbinde()
    fertig = {(m, d) for m, d in c.execute("SELECT markt, datum FROM tag")}
    for markt in MAERKTE:
        for j, m in MONATE:
            if markt == "spot" and j == 2023 and "--ohne-spot-2023" in sys.argv:   # 2,66 GB - eigenes Ja (29.10.)
                continue
            for t in range(1, calendar.monthrange(j, m)[1] + 1):
                datum = "%d-%02d-%02d" % (j, m, t)
                if (markt, datum) in fertig:
                    continue
                df = lies_tag(markt, datum)
                if df is None:
                    print("  ✖ %s %s nicht abrufbar" % (markt, datum), flush=True)
                    continue
                umsatz, kauf, n_agg, n_sw, zeilen = verdichte(df)
                ku, kk = kerze(markt, datum)
                c.execute("INSERT OR REPLACE INTO tag VALUES (?,?,?,?,?,?,?,?,?)",
                          (markt, datum, umsatz, kauf, n_agg, n_sw, ku, kk, datetime.now(timezone.utc).isoformat(timespec="seconds")))
                c.executemany("INSERT OR REPLACE INTO verteilung VALUES (?,?,?,?,?,?,?)", [(markt, datum) + z for z in zeilen])
                c.commit()
                print("  ✔ %-7s %s  %9d aggTrades  %8d Sweeps  Umsatz %6.2f Mrd $  Kerze %s" % (
                    markt, datum, n_agg, n_sw, umsatz / 1e9, "%.2f" % (ku / 1e9) if ku else "–"), flush=True)
                del df
    c.close()


def bericht():
    c = sqlite3.connect("file:%s?mode=ro" % ABLAGE.replace("\\", "/"), uri=True)
    print("ABGLEICH Archiv gegen REST-Kerze (Tagesumsatz)")
    for markt, n, lo, hi, maxab in c.execute("""SELECT markt, COUNT(*), MIN(umsatz_usd/kerze_usd), MAX(umsatz_usd/kerze_usd),
                                                MAX(ABS(kauf_usd/kerze_kauf_usd - 1)) FROM tag WHERE kerze_usd > 0 GROUP BY markt"""):
        print("  %-7s %3d Tage  Archiv/Kerze %.4f .. %.4f  Kaufanteil max. Abweichung %.4f" % (markt, n, lo, hi, maxab))
    print("\nANTEIL AM UMSATZ ab Größe (je Monat, Sweep, beide Seiten)")
    grenzen = (4, 5, 6, 7)                                            # 10 k$, 100 k$, 1 Mio $, 10 Mio $ -> Klasse 16, 20, 24, 28
    print("  %-7s %-8s %-22s" % ("Markt", "Monat", "  ".join("≥10^%d $" % g for g in grenzen)))
    for markt in MAERKTE:
        for j, m in MONATE:
            mon = "%d-%02d" % (j, m)
            for teil, bed in (("", ""), (" bis 21.", " AND datum < '2023-03-22'"), (" ab 22.", " AND datum >= '2023-03-22'")):
                if teil and mon != "2023-03":
                    continue
                ges = c.execute("SELECT SUM(usd) FROM verteilung WHERE markt=? AND einheit='sweep' AND datum LIKE ?" + bed,
                                (markt, mon + "%")).fetchone()[0]
                if not ges:
                    continue
                ant = [c.execute("SELECT SUM(usd) FROM verteilung WHERE markt=? AND einheit='sweep' AND datum LIKE ? AND klasse >= ?" + bed,
                                 (markt, mon + "%", 4 * g)).fetchone()[0] or 0 for g in grenzen]
                print("  %-7s %-8s %s" % (markt, mon + teil, "  ".join("%7.2f %%" % (100 * a / ges) for a in ant)))
    c.close()


def schwelle():
    """Schwellenvorschlag (Vorprüfung, KEINE Bewertung): die Grenze „groß“ RELATIV je Tag — die größten Sweeps, die zusammen q des
    Tagesumsatzes machen. Je q: wo die Grenze in $ und in BTC liegt, und ob der Netto-Großfluss etwas ANDERES zeigt als der
    Netto-Fluss aller übrigen (ρ nahe 1 = die Großen sagen nichts Eigenes). ⚠️ Kein Blick auf künftige Kurse — der kommt erst nach
    dem Selbsttest (stehende Regel); hier steht nur, was am selben Tag GESCHAH (Fakt)."""
    c = sqlite3.connect("file:%s?mode=ro" % ABLAGE.replace("\\", "/"), uri=True)
    v = pd.read_sql("SELECT markt, datum, seite, klasse, usd FROM verteilung WHERE einheit='sweep'", c)
    t = pd.read_sql("SELECT markt, datum, umsatz_usd, kauf_usd FROM tag", c).set_index(["markt", "datum"])
    c.close()
    preis = {}                                                         # Tagesschluss für die Grenze in BTC (REST, Spot)
    for j, m in MONATE:
        t0 = int(datetime(j, m, 1, tzinfo=timezone.utc).timestamp() * 1000)
        for k in _hole(MAERKTE["spot"][1], {"symbol": "BTCUSDT", "interval": "1d", "startTime": t0, "limit": 31}).json():
            preis[datetime.fromtimestamp(k[0] / 1000, timezone.utc).strftime("%Y-%m-%d")] = float(k[4])
    p = v.pivot_table(index=["markt", "datum", "klasse"], columns="seite", values="usd", aggfunc="sum", fill_value=0.0)
    zeilen = []
    for (markt, datum), g in p.groupby(level=[0, 1]):
        g = g.droplevel([0, 1]).sort_index(ascending=False)
        ges = (g["kauf"] + g["verkauf"]).sum()
        kum = ((g["kauf"] + g["verkauf"]).cumsum() / ges)
        alle_netto = (g["kauf"] - g["verkauf"]).sum() / ges
        for q in (0.20, 0.10, 0.05, 0.01):
            k = kum.index[kum.values >= q][0] if (kum.values >= q).any() else kum.index[-1]   # Grenzklasse (ganz dabei)
            gross = g.loc[g.index >= k]
            gn = (gross["kauf"] - gross["verkauf"]).sum() / ges
            zeilen.append((markt, datum, q, 10 ** (k / 4), 10 ** (k / 4) / preis.get(datum, np.nan), kum.loc[k], gn, alle_netto - gn))
    d = pd.DataFrame(zeilen, columns=["markt", "datum", "q", "grenze_usd", "grenze_btc", "anteil", "netto_gross", "netto_rest"])
    d["monat"] = d["datum"].str[:7]
    print("SCHWELLE RELATIV: die größten Sweeps mit zusammen ≥ q des Tagesumsatzes (Grenze = Klassenuntergrenze, Viertel-Dekade)")
    print("  %-7s %-7s %5s  %12s %9s %7s  %9s %9s  %s" % ("Markt", "Monat", "q", "Grenze $", "Grenze ₿", "Anteil", "sd groß", "sd rest",
                                                           "ρ groß/rest"))
    for (markt, monat, q), g in d.groupby(["markt", "monat", "q"]):
        print("  %-7s %-7s %4.0f%%  %12s %9.3f %6.1f%%  %8.2f%% %8.2f%%  %+.2f" % (
            markt, monat, 100 * q, "{:,.0f}".format(g["grenze_usd"].median()), g["grenze_btc"].median(), 100 * g["anteil"].median(),
            100 * g["netto_gross"].std(), 100 * g["netto_rest"].std(), g["netto_gross"].corr(g["netto_rest"])))
    print("\nSPOT GEGEN FUTURES am selben Tag (ρ Netto-Großfluss) — zeigen die Großen beider Märkte dasselbe?")
    for (monat, q), g in d.groupby(["monat", "q"]):
        w = g.pivot(index="datum", columns="markt", values="netto_gross").dropna()
        if len(w) > 5 and {"spot", "futures"} <= set(w.columns):
            print("  %-7s %4.0f%%  %+.2f  (%d Tage)" % (monat, 100 * q, w["spot"].corr(w["futures"]), len(w)))


if __name__ == "__main__":
    bericht() if "--bericht" in sys.argv else schwelle() if "--schwelle" in sys.argv else lade()
