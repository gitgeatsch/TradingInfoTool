"""P64 L-C VORANALYSE (18.10.2026, Schritt7 §23.71): Ereignisdaten 2025-26 fuer einen LLM-Ausnahme-/Risikopruefer. Nur lesend.

    python Basisinfos/Rechenkern_02_10/p64_lc_voranalyse.py

Es wird KEIN Ereignis gegen ein Ergebnis gerechnet (das bleibt der vorab festgelegten Messung); gefragt ist die Datenlage.
T0 Zielgroesse    linkes Ende der REGEL0-Einstiege 2025-26 (Menge bestand + unverzerrt_1): 24 h <= -10 %, Tief binnen 24 h <= -10 / -20 %
T1 strukturiert   Binance-Ankuendigungen (data/_e1, E-1), DefiLlama-Hacks (api.llama.fi/hacks), Umlauf-Spruenge (data/umlaufmenge_cg.db):
                  Zahl 2025-26, Zuordnung zu Signal-Assets, Anteil der Einstiege mit Ereignis in den 7 T davor
T2 Textarchive    GDELT DOC 2.0 (Zeitraum 2025), CryptoCompare-News (lTs), Wayback-CDX der RSS-Feeds Cointelegraph/CoinDesk (2025-26):
                  erreichbar? Veroeffentlichungszeit? Tiefe? Stichprobe: wie oft werden die 21 Schalter-Assets genannt?
"""
import json
import os
import re
import sqlite3
import sys
import time
from datetime import datetime, timezone

import numpy as np
import pandas as pd
import requests

WURZEL = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(WURZEL)
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:  # noqa: BLE001
    pass
H = {"User-Agent": "Mozilla/5.0 (TradingInfoTool Forschung)"}
B0 = pd.Timestamp("2020-01-01")
SCHALTER = ("AKT", "ALGO", "AVAX", "BEAMX", "BNB", "BTC", "ETH", "HYPE", "KAIA", "KAITO", "LINK", "MORPHO", "NEAR", "ONDO", "QNT", "SEI", "SOL", "SUI",
            "TAO", "TURBO", "VIRTUAL")
NAMEN = {"AKT": "Akash", "ALGO": "Algorand", "AVAX": "Avalanche", "BEAMX": "Beam", "BNB": "BNB", "BTC": "Bitcoin", "ETH": "Ethereum", "HYPE": "Hyperliquid",
         "KAIA": "Kaia", "KAITO": "Kaito", "LINK": "Chainlink", "MORPHO": "Morpho", "NEAR": "NEAR", "ONDO": "Ondo", "QNT": "Quant", "SEI": "Sei",
         "SOL": "Solana", "SUI": "Sui", "TAO": "Bittensor", "TURBO": "Turbo", "VIRTUAL": "Virtuals"}
DATEIEN = ("stundenkurse.db", "stundenkurse_alle.db", "eingestellt_historie.db")
_con = {d: sqlite3.connect("file:data/%s?mode=ro" % d, uri=True) for d in DATEIEN if os.path.exists(os.path.join("data", d))}


def hole(url, params=None, timeout=60):
    try:
        r = requests.get(url, params=params, headers=H, timeout=timeout)
        return r.status_code, r
    except requests.RequestException as exc:
        return "Fehler %s" % type(exc).__name__, None


def reihe(sym):
    d = {}
    for _n, c in _con.items():
        for st, lo, cl in c.execute("SELECT stunde, low, close FROM stundenkurse WHERE symbol=?", (sym,)):
            d.setdefault(st, (lo, cl))
    if not d:
        return None
    hs = ((pd.to_datetime(list(d.keys())) - B0) / pd.Timedelta(hours=1)).astype(int).to_numpy()
    a = hs.min()
    L, C = np.full(hs.max() - a + 1, np.nan), np.full(hs.max() - a + 1, np.nan)
    v = np.array(list(d.values()), float)
    L[hs - a], C[hs - a] = v[:, 0], v[:, 1]
    return a, L, C


def t0():
    print("T0 ZIELGROESSE: linkes Ende der REGEL0-Einstiege 2025-26")
    aus = {}
    for menge in ("bestand", "unverzerrt_1"):
        E = pd.read_csv(os.path.join("data", "_vergleich", "kern48jbz_einstiege_%s.csv" % menge), sep=";")
        E = E[E.jahr >= 2025]
        cache, z = {}, []
        for r in E.itertuples():
            if r.symbol not in cache:
                cache[r.symbol] = reihe(r.symbol)
            x = cache[r.symbol]
            if x is None:
                continue
            a, L, C = x
            i = int(r.stunde) - a
            if i < 0 or i + 24 >= len(C) or not (C[i] == C[i] and np.isfinite(L[i + 1:i + 25]).all() and C[i + 24] == C[i + 24]):
                continue
            z.append(dict(symbol=r.symbol, tag=(B0 + pd.Timedelta(hours=int(r.stunde))).normalize(), e24=C[i + 24] / C[i] - 1,
                          tief=float(L[i + 1:i + 25].min() / C[i] - 1)))
        D = pd.DataFrame(z)
        aus[menge] = D
        for name, m in (("24 h <= -10 %", D.e24 <= -0.10), ("Tief 24 h <= -10 %", D.tief <= -0.10), ("Tief 24 h <= -20 % (5x-Liquidation)", D.tief <= -0.20)):
            print("   %-13s %-36s %4d von %5d Einstiegen (%.2f %%) an %3d Tagen, %3d Assets" % (
                menge, name, int(m.sum()), len(D), 100 * m.mean(), D[m].tag.nunique(), D[m].symbol.nunique()))
        G = D[D.symbol.isin(SCHALTER)]
        print("   %-13s gehandelte 21: Tief 24 h <= -10 %%: %d von %d (%.2f %%)" % (menge, int((G.tief <= -0.10).sum()), len(G), 100 * (G.tief <= -0.10).mean()))
    return aus


def t1(D):
    print("\nT1 STRUKTURIERTE EREIGNISSE 2025-26")
    c = sqlite3.connect("file:data/_e1/binance_ankuendigungen.db?mode=ro", uri=True)
    ev = pd.read_sql("SELECT art, symbol, release_ms FROM ereignis", c)
    c.close()
    ev["zeit"] = pd.to_datetime(ev.release_ms, unit="ms")
    ev25 = ev[ev.zeit >= "2025-01-01"]
    print("   Binance (E-1, geladen bis %s): 2025-26 %d Ereignisse · je Art %s" % (ev.zeit.max().date(), len(ev25),
                                                                                 dict(ev25.art.value_counts())))
    st, r = hole("https://api.llama.fi/hacks", timeout=90)
    hk = []
    if r is not None and st == 200:
        hk = [x for x in r.json() if x.get("date") and datetime.fromtimestamp(int(x["date"]), timezone.utc).year >= 2025]
    print("   DefiLlama-Hacks: Abruf %s · 2025-26: %d Vorfaelle (Tag, Protokollname) · groesste: %s" % (
        st, len(hk), ", ".join("%s %s" % (x.get("name"), datetime.fromtimestamp(int(x["date"]), timezone.utc).date())
                               for x in sorted(hk, key=lambda x: -(x.get("amount") or 0))[:5])))
    nam = {v.lower(): k for k, v in NAMEN.items()}
    treffer = [x.get("name") for x in hk if any(n in str(x.get("name", "")).lower() for n in nam)]
    print("   davon mit Namen eines der 21 gehandelten Assets im Protokollnamen: %d (%s)" % (len(treffer), ", ".join(treffer[:8])))
    if os.path.exists("data/umlaufmenge_cg.db"):
        u = sqlite3.connect("file:data/umlaufmenge_cg.db?mode=ro", uri=True)
        tab = [t[0] for t in u.execute("SELECT name FROM sqlite_master WHERE type='table'")]
        print("   Umlaufmenge (CoinGecko, P22): Tabellen %s" % tab)
        u.close()
    for menge, X in D.items():
        X = X.copy()
        X["zeit"] = X.tag
        n7 = 0
        for s, g in X.groupby("symbol"):
            e = ev25[ev25.symbol == s].zeit.sort_values().to_numpy()
            if not len(e):
                continue
            for t in g.zeit:
                n7 += int(((e <= np.datetime64(t)) & (e > np.datetime64(t - pd.Timedelta(days=7)))).any())
        print("   %-13s Einstiege mit Binance-Ereignis (jede Art) in den 7 T davor: %d von %d (%.2f %%)" % (menge, n7, len(X), 100 * n7 / len(X)))


def t2():
    print("\nT2 TEXTARCHIVE (die eigentliche LLM-Frage: unstrukturierter Text mit Veroeffentlichungszeit, 2025-26)")
    st, r = hole("https://api.gdeltproject.org/api/v2/doc/doc", params={"query": "solana", "mode": "artlist", "format": "json", "maxrecords": 50,
                                                                       "startdatetime": "20250301000000", "enddatetime": "20250307235959"})
    n = None
    if r is not None and st == 200:
        try:
            n = len(r.json().get("articles", []))
        except Exception:  # noqa: BLE001
            n = "keine JSON-Antwort (%s)" % r.text[:80].replace("\n", " ")
    print("   GDELT DOC 2.0 'solana' 01.-07.03.2025: Abruf %s · Artikel %s" % (st, n))
    time.sleep(3)
    lts = int(datetime(2025, 3, 7, tzinfo=timezone.utc).timestamp())
    st, r = hole("https://min-api.cryptocompare.com/data/v2/news/", params={"lang": "EN", "lTs": lts})
    info = None
    if r is not None and st == 200:
        j = r.json()
        d = j.get("Data") or []
        info = ("%d Meldungen, aeltestes %s, juengstes %s, Hinweis '%s'" % (
            len(d), datetime.fromtimestamp(min(x["published_on"] for x in d), timezone.utc) if d else "-",
            datetime.fromtimestamp(max(x["published_on"] for x in d), timezone.utc) if d else "-", (j.get("Message") or "")[:80])) if isinstance(d, list) else str(j)[:160]
    print("   CryptoCompare-News lTs=07.03.2025: Abruf %s · %s" % (st, info))
    for name, url in (("Cointelegraph", "cointelegraph.com/rss"), ("CoinDesk", "coindesk.com/arc/outboundfeeds/rss/")):
        time.sleep(2)
        st, r = hole("https://web.archive.org/cdx/search/cdx", params={"url": url, "from": "2025", "to": "2026", "output": "json",
                                                                        "filter": "statuscode:200", "collapse": "timestamp:8", "limit": 2000}, timeout=120)
        tage = []
        if r is not None and st == 200:
            try:
                rows = r.json()[1:]
                tage = sorted({x[1][:8] for x in rows})
            except Exception:  # noqa: BLE001
                pass
        print("   Wayback %s RSS 2025-26: Abruf %s · Tage mit Aufnahme %d%s" % (name, st, len(tage), (" (%s .. %s)" % (tage[0], tage[-1])) if tage else ""))
        if tage:
            ts = rows[len(rows) // 2][1]
            time.sleep(2)
            st2, r2 = hole("https://web.archive.org/web/%sid_/https://%s" % (ts, url), timeout=120)
            if r2 is not None and st2 == 200:
                items = re.findall(r"<item>(.*?)</item>", r2.text, re.S)
                pub = [re.search(r"<pubDate>(.*?)</pubDate>", i) for i in items]
                pub = [p.group(1) for p in pub if p]
                tit = [re.sub(r"<!\[CDATA\[|\]\]>", "", (re.search(r"<title>(.*?)</title>", i, re.S) or [None, ""])[1]) for i in items]
                nenn = sum(any(re.search(r"\b(%s|%s)\b" % (re.escape(s), re.escape(NAMEN[s])), t, re.I) for s in SCHALTER) for t in tit)
                print("      Stichprobe %s: %d Meldungen mit pubDate (%s .. %s), davon %d nennen eines der 21 Assets" % (
                    ts[:8], len(items), pub[-1] if pub else "-", pub[0] if pub else "-", nenn))


def main():
    print("P64 L-C VORANALYSE · Ereignisdaten 2025-26 · nur Datenlage, keine Ereignis-Ergebnis-Rechnung\n")
    D = t0()
    t1(D)
    t2()


if __name__ == "__main__":
    main()
