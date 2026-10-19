"""P65 L-C VORPRUEFUNG NENNUNGSABDECKUNG (19.10.2026, Schritt7 §23.72). Nur lesend. KEIN Ergebnisvergleich nach Meldungsinhalt.

    python Basisinfos/Rechenkern_02_10/p65_lc_nennung.py

Frage: Wie viele REGEL0-Einstiege 2025-26 - und wie viele mit Tief binnen 24 h <= -10 % - haben vor dem Einstieg eine Meldung zum EIGENEN Asset?
Archiv: data/_lc/nachrichten.db (p65_lc_archiv_laden, 9 RSS-Feeds ueber das Wayback-Archiv), Titel + Kurzbeschreibung.
Zuordnung (VOR dem ersten Lauf festgelegt):
  Name   ohne Gross/Klein, ganzes Wort, >= 4 Zeichen; dazu der Stamm ohne Protocol/Network/Finance/Token/Coin/Chain/DAO/Labs/AI/Foundation
         (>= 4 Zeichen); Name je Kuerzel = der CMC-Name mit dem hoechsten Marktwert 2025-26 (o47_cm.db cmc_woche); Stoppliste gaengiger Woerter
  Kuerzel nur GROSS als ganzes Wort, >= 3 Zeichen, nicht in der Abkuerzungs-Stoppliste; '$KUERZEL' zaehlt immer (>= 2 Zeichen)
Fenster: Veroeffentlichung in [Beginn Einstiegsstunde - 7 T / 3 T / 24 h, Beginn Einstiegsstunde) - kein Vorgriff.
Archivluecke: Einstiege ohne JEDE Archivaufnahme (irgendein Feed) in den 7 T davor werden gesondert gezaehlt.
Groesse: CMC-Rang in der letzten Wochenaufnahme vor dem Einstieg (1-50 / 51-200 / nicht in den Top 200).
"""
import os
import re
import sqlite3
import sys
from collections import defaultdict

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import p64_lc_voranalyse as P  # noqa: E402  (Kursreihe, Schalter-Liste)

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:  # noqa: BLE001
    pass
ZUSATZ = {"protocol", "network", "finance", "token", "coin", "chain", "dao", "labs", "ai", "foundation", "swap", "exchange"}
STOPP_NAME = {"status", "maker", "gas", "near", "one", "link", "act", "people", "core", "flow", "dash", "zero", "dent", "safe", "beam", "story", "sonic",
              "movement", "magic", "harmony", "kite", "pundi", "pepe", "turbo", "virtual", "radiant", "space", "echo", "solv", "bitcoin cash", "home",
              "open", "nano", "orca", "ocean", "polygon", "cookie", "sign", "plume", "notcoin", "dogs", "hook", "light", "jupiter", "aave", "uma",
              "mask", "ray", "chill", "fun", "true", "bank", "venus", "aergo", "world", "trust", "stable", "life", "bio", "time", "stop", "base"}
STOPP_KURZ = {"THE", "FOR", "AND", "NEW", "ETF", "SEC", "USD", "CEO", "NFT", "DEX", "CEX", "API", "IPO", "GDP", "CPI", "FED", "ATH", "ONE", "ALL", "TOP",
              "WIN", "GAS", "ACT", "BIG", "OUT", "NOT", "HOT", "MAN", "CAT", "DOG", "SUN", "KEY", "LIT", "BAR", "AIR", "ARE", "CAN", "HAS", "WHY", "HOW",
              "WHO", "NOW", "BUT", "ITS", "YOU", "OUR", "TRUMP", "USA", "UK", "EU", "TVL", "APY", "RWA", "AI", "ETH2", "BTC", "LAB", "OPEN", "GOOD", "ZERO",
              "MOVE", "PUMP", "HOME", "SAFE", "LINK", "NEAR", "COOKIE", "MAGIC", "PEOPLE", "SIGN", "TRUE", "FUN", "SUPER", "WORLD", "FIRE", "TIME"}
STOPP_KURZ -= {"BTC"}                                                       # BTC ist ein eindeutiges Kuerzel


def namen():
    c = sqlite3.connect("file:data/_spot/o47_cm.db?mode=ro", uri=True, timeout=30)
    W = pd.read_sql("SELECT symbol, name, MAX(cap) AS cap FROM cmc_woche WHERE stichtag >= '2025-01-01' GROUP BY symbol, name", c)
    R = pd.read_sql("SELECT stichtag, symbol, rang FROM cmc_woche WHERE stichtag >= '2024-12-01'", c, parse_dates=["stichtag"])
    c.close()
    best = W.sort_values("cap", ascending=False).drop_duplicates("symbol").set_index("symbol").name.to_dict()
    rang = R.sort_values("rang").drop_duplicates(["stichtag", "symbol"])
    return best, rang


def muster_fuer(sym, name):
    teile = []
    if name:
        n = name.strip()
        stamm = " ".join(w for w in n.split() if w.lower() not in ZUSATZ)
        for v in {n, stamm}:
            if len(v) >= 4 and v.lower() not in STOPP_NAME:
                teile.append(r"(?i:\b%s\b)" % re.escape(v))
    if len(sym) >= 3 and sym.upper() not in STOPP_KURZ:
        teile.append(r"(?<![A-Za-z0-9$])%s(?![A-Za-z0-9])" % re.escape(sym.upper()))
    if len(sym) >= 2:
        teile.append(r"\$%s\b" % re.escape(sym.upper()))
    return re.compile("|".join(teile)) if teile else None


def lade_meldungen():
    c = sqlite3.connect("file:data/_lc/nachrichten.db?mode=ro", uri=True, timeout=30)
    M = pd.read_sql("SELECT feed, titel, beschreibung, pub_utc, aufnahme_ts FROM meldung WHERE pub_utc IS NOT NULL", c, parse_dates=["pub_utc"])
    A = pd.read_sql("SELECT feed, ts FROM aufnahme WHERE status='ok'", c)
    c.close()
    M["text"] = M.titel.fillna("") + " " + M.beschreibung.fillna("")
    A["zeit"] = pd.to_datetime(A.ts.str[:14], format="%Y%m%d%H%M%S")
    return M, A


def main():
    best, rang = namen()
    M, A = lade_meldungen()
    M = M.drop_duplicates(["titel", "pub_utc"])
    print("P65 NENNUNGSABDECKUNG · Archiv: %d Meldungen (%s .. %s) aus %d Feeds, %d Aufnahmen\n" % (
        len(M), M.pub_utc.min(), M.pub_utc.max(), M.feed.nunique(), len(A)))
    for menge in ("bestand", "unverzerrt_1"):
        E = pd.read_csv(os.path.join("data", "_vergleich", "kern48jbz_einstiege_%s.csv" % menge), sep=";")
        E = E[E.jahr >= 2025].copy()
        E["zeit"] = P.B0 + pd.to_timedelta(E.stunde, unit="h")
        cache, tief = {}, []
        for r in E.itertuples():
            if r.symbol not in cache:
                cache[r.symbol] = P.reihe(r.symbol)
            x = cache[r.symbol]
            t = np.nan
            if x is not None:
                a, L, C = x
                i = int(r.stunde) - a
                if 0 <= i and i + 24 < len(C) and C[i] == C[i] and np.isfinite(L[i + 1:i + 25]).all():
                    t = float(L[i + 1:i + 25].min() / C[i] - 1)
            tief.append(t)
        E["tief"] = tief
        E = E[E.tief.notna()].copy()
        treffer_zeiten = {}
        for s in E.symbol.unique():
            mu = muster_fuer(s, best.get(s))
            treffer_zeiten[s] = np.sort(M.pub_utc[M.text.str.contains(mu, regex=True)].to_numpy()) if mu is not None else np.array([], "datetime64[ns]")
        az = np.sort(A.zeit.to_numpy())
        for fen in (7, 3, 1):
            E["n%d" % fen] = [((treffer_zeiten[s] < np.datetime64(z)) & (treffer_zeiten[s] >= np.datetime64(z - pd.Timedelta(days=fen)))).any()
                              for s, z in zip(E.symbol, E.zeit)]
        E["archiv7"] = [((az < np.datetime64(z)) & (az >= np.datetime64(z - pd.Timedelta(days=7)))).any() for z in E.zeit]
        rr = []
        for s, z in zip(E.symbol, E.zeit):
            q = rang[(rang.symbol == s) & (rang.stichtag <= z)]
            rr.append(int(q.sort_values("stichtag").rang.iloc[-1]) if len(q) else 999)
        E["groesse"] = pd.cut(pd.Series(rr, index=E.index), [0, 50, 200, 10 ** 6], labels=["Top 50", "51-200", "nicht Top 200"])
        T = E.tief <= -0.10
        print("=" * 112)
        print("%s: %d Einstiege, davon mit Archivaufnahme in den 7 T davor %d (%.1f %%)" % (menge, len(E), int(E.archiv7.sum()), 100 * E.archiv7.mean()))
        for name, sel in (("alle", E.index == E.index), ("Tief 24 h <= -10 %", T), ("gehandelte 21", E.symbol.isin(P.SCHALTER)),
                          ("gehandelte 21, Tief <= -10 %", E.symbol.isin(P.SCHALTER) & T)):
            X = E[sel & E.archiv7]
            print("   %-30s n %5d · Meldung zum Asset 7 T %5.1f %% · 3 T %5.1f %% · 24 h %5.1f %%" % (
                name, len(X), 100 * X.n7.mean(), 100 * X.n3.mean(), 100 * X.n1.mean()))
        print("   je Groesse (mit Archiv):")
        for gname, X in E[E.archiv7].groupby("groesse", observed=True):
            XT = X[X.tief <= -0.10]
            print("     %-14s Einstiege %5d · mit Meldung 7 T %5.1f %% · davon Tief <= -10 %%: %3d, mit Meldung %5.1f %%" % (
                gname, len(X), 100 * X.n7.mean(), len(XT), 100 * XT.n7.mean() if len(XT) else float("nan")))
        ta = E[T & E.archiv7]
        nie = sorted(set(ta.symbol) - {s for s in ta.symbol.unique() if len(treffer_zeiten[s])})
        print("   Tief-Assets ohne JEDE Nennung 2025-26: %d von %d (u. a. %s)" % (len(nie), ta.symbol.nunique(), ", ".join(nie[:15])))
        if menge == "bestand":
            E.to_csv(os.path.join("data", "_lc", "p65_einstiege.csv"), sep=";", index=False)
    print("\nNennungen je der 21 gehandelten Assets 2025-26 (Meldungen gesamt): %s" % " · ".join(
        "%s %d" % (s, int(M.text.str.contains(muster_fuer(s, best.get(s)), regex=True).sum())) for s in P.SCHALTER if muster_fuer(s, best.get(s))))


if __name__ == "__main__":
    main()
