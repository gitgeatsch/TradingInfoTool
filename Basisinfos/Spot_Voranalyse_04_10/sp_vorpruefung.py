"""Voranalyse Strukturprofil (Voranalyse_Spot §24, E-74) - NUR Datenlage, keine Wirkung.

    python Basisinfos/Spot_Voranalyse_04_10/sp_vorpruefung.py

Quellen frei und ohne Schluessel: CoinGecko /coins/markets (Marktwert, Umlauf, Gesamt- und Hoechstmenge) und /coins/{id} (Kategorien,
Projektstart), DefiLlama /protocols (RWA-Protokolle je Blockchain). Zuordnung Symbol -> CoinGecko-ID ueber umlaufmenge_cg.abruf_symbol
(sonst eindeutiges Kuerzel). Schreibt NUR nach data/_spot/strukturprofil.db (Messdatei des Spot-Strangs).

Fragen: (1) Abdeckung je Fakt fuer unser Universum, (2) Klassen nach MARKTWERT gegen Klassen nach Binance-Umsatz - wer wechselt (QNT?),
(3) Angebotsfakten (Hoechstmenge fest, Anteil ausgegeben, FDV/Marktwert), (4) Kategorien und Projektstart, (5) RWA je Blockchain heute.
"""
import json
import os
import sqlite3
import sys
import time

import numpy as np
import pandas as pd
import requests

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HIER)
import a2_messung as A  # noqa: E402

ZIEL = os.path.join("data", "_spot", "strukturprofil.db")
KOPF = {"User-Agent": "TradingInfoTool/1.0 (Analyse, nicht kommerziell)"}


def hole(url, pause=0.0):
    for k in range(4):
        try:
            r = requests.get(url, headers=KOPF, timeout=60)
            if r.status_code == 200:
                time.sleep(pause)
                return r.json()
            if r.status_code == 429:
                time.sleep(30 + 15 * k); continue
        except Exception:                                     # noqa: BLE001
            pass
        time.sleep(5)
    return None


def main():
    t = A.ENDE.replace(day=1)
    kl = A.klassen(t)[0]
    c = sqlite3.connect("file:data/umlaufmenge_cg.db?mode=ro", uri=True)
    cgid = {s: i for s, i in c.execute("SELECT symbol, coingecko_id FROM abruf_symbol WHERE coingecko_id IS NOT NULL")}
    markt = []
    for seite in range(1, 7):
        d = hole("https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=250&page=%d" % seite, pause=2.5)
        if not d:
            break
        markt += d
    M = pd.DataFrame(markt)
    print("Strukturprofil Vorpruefung (§24) · Klassen zum %s · CoinGecko-Markt: %d Coins" % (t.date(), len(M)))
    nach_id = M.set_index("id")
    sym_eindeutig = M.groupby(M.symbol.str.upper()).id.agg(lambda x: x.iloc[0] if len(x) == 1 else None).dropna().to_dict()
    zeilen = []
    for s, k in kl.items():
        i = cgid.get(s) or sym_eindeutig.get(s)
        r = nach_id.loc[i] if i in nach_id.index else None
        zeilen.append(dict(symbol=s, klasse_umsatz=k, cg_id=i, mw=r["market_cap"] if r is not None else np.nan,
                           umlauf=r["circulating_supply"] if r is not None else np.nan, gesamt=r["total_supply"] if r is not None else np.nan,
                           hoechst=r["max_supply"] if r is not None else np.nan, fdv=r["fully_diluted_valuation"] if r is not None else np.nan))
    P = pd.DataFrame(zeilen)
    P["rang_mw"] = P.mw.rank(ascending=False)
    P["klasse_mw"] = np.where(P.rang_mw <= 30, "H", np.where(P.rang_mw <= 100, "M", np.where(P.mw.notna(), "S", "-")))
    P["fest"] = P.hoechst.notna() & (P.hoechst > 0)
    P["ausgegeben"] = np.where(P.fest, P.umlauf / P.hoechst, P.umlauf / P.gesamt)
    P["fdv_mw"] = P.fdv / P.mw
    print("\n(1) Abdeckung: %d Coins im Universum · mit CoinGecko-ID %d · mit Marktwert %d · mit Hoechstmenge %d" % (
        len(P), P.cg_id.notna().sum(), P.mw.notna().sum(), P.fest.sum()))
    print("\n(2) Klasse nach Binance-Umsatz (Zeilen) gegen Klasse nach Marktwert (Spalten):")
    print(pd.crosstab(P.klasse_umsatz, P.klasse_mw).to_string())
    for s in ("QNT", "LINK", "XLM", "HBAR", "ONDO", "KAS", "ALGO"):
        x = P[P.symbol == s]
        if len(x):
            r = x.iloc[0]
            print("   %-5s Umsatz-Klasse %s · Marktwert %.2f Mrd (Rang %s) -> Klasse %s · Hoechstmenge %s · ausgegeben %s · FDV/MW %s" % (
                s, r.klasse_umsatz, r.mw / 1e9 if r.mw == r.mw else np.nan, int(r.rang_mw) if r.rang_mw == r.rang_mw else "-", r.klasse_mw,
                "fest" if r.fest else "offen", "%.0f %%" % (100 * r.ausgegeben) if r.ausgegeben == r.ausgegeben else "-",
                "%.2f" % r.fdv_mw if r.fdv_mw == r.fdv_mw else "-"))
    print("\n(3) Angebot je Marktwert-Klasse: Anteil mit fester Hoechstmenge · Median ausgegeben · Anteil FDV/MW > 1,5 (viel kommt noch)")
    for k in ("H", "M", "S"):
        x = P[P.klasse_mw == k]
        print("   %s  n %3d · fest %3.0f %% · ausgegeben Median %3.0f %% · FDV/MW > 1,5 bei %3.0f %%" % (
            k, len(x), 100 * x.fest.mean(), 100 * x.ausgegeben.median(), 100 * (x.fdv_mw > 1.5).mean()))
    # (4) Kategorien und Projektstart
    kat = []
    ids = [i for i in P.cg_id.dropna().unique()]
    for n, i in enumerate(ids):
        d = hole("https://api.coingecko.com/api/v3/coins/%s?localization=false&tickers=false&market_data=false&community_data=false&developer_data=false" % i, pause=2.4)
        if d:
            kat.append(dict(cg_id=i, kategorien=json.dumps(d.get("categories") or [], ensure_ascii=False), start=d.get("genesis_date")))
        if n % 50 == 0:
            print("   ... Kategorien %d / %d" % (n, len(ids)), flush=True)
    KT = pd.DataFrame(kat)
    P = P.merge(KT, on="cg_id", how="left")
    alle = pd.Series([k for v in P.kategorien.dropna() for k in json.loads(v)]).value_counts()
    print("\n(4) Kategorien: %d Coins mit Kategorie · Projektstart bekannt bei %d · haeufigste: %s" % (
        P.kategorien.notna().sum(), P.start.notna().sum(), ", ".join("%s %d" % kv for kv in alle.head(20).items())))
    meme = P.kategorien.fillna("").str.contains("Meme")
    rwa = P.kategorien.fillna("").str.contains("Real World Assets")
    print("   Meme: %d · RWA: %d · je Marktwert-Klasse Meme H/M/S: %s · RWA H/M/S: %s" % (
        meme.sum(), rwa.sum(), "/".join(str(int((meme & (P.klasse_mw == k)).sum())) for k in "HMS"),
        "/".join(str(int((rwa & (P.klasse_mw == k)).sum())) for k in "HMS")))
    # (5) RWA je Blockchain heute (DefiLlama)
    prot = hole("https://api.llama.fi/protocols") or []
    rwa_chain = {}
    for p in prot:
        if p.get("category") == "RWA":
            for ch, v in (p.get("chainTvls") or {}).items():
                if "-" not in ch and isinstance(v, (int, float)):
                    rwa_chain[ch] = rwa_chain.get(ch, 0) + v
    top = sorted(rwa_chain.items(), key=lambda kv: -kv[1])[:15]
    print("\n(5) RWA-Volumen je Blockchain heute (DefiLlama, Mrd USD): %s" % ", ".join("%s %.2f" % (k, v / 1e9) for k, v in top))
    os.makedirs(os.path.dirname(ZIEL), exist_ok=True)
    z = sqlite3.connect(ZIEL)
    P.to_sql("profil", z, if_exists="replace", index=False)
    pd.DataFrame(list(rwa_chain.items()), columns=["chain", "rwa_tvl_usd"]).to_sql("rwa_chain", z, if_exists="replace", index=False)
    z.execute("CREATE TABLE IF NOT EXISTS _herkunft (schluessel TEXT PRIMARY KEY, wert TEXT)")
    z.execute("INSERT OR REPLACE INTO _herkunft VALUES ('quelle', 'CoinGecko markets + coins, DefiLlama protocols; Stand %s')" % time.strftime("%Y-%m-%d %H:%M"))
    z.commit()
    print("\ngeschrieben: %s (%d Coins)" % (ZIEL, len(P)))
    print("\nHISTORIE (fuer die Messbarkeit): CoinGecko frei nur 365 T Marktwert-Verlauf; Angebot historisch nur umlaufmenge_cg (ab 09/2025) und "
          "CoinMetrics (66 Coins ab 2013); Kategorien und Hoechstmenge nur HEUTE -> als Merkmal der Vergangenheit nur mit Vorgriffsvorbehalt")


if __name__ == "__main__":
    main()
