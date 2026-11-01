# -*- coding: utf-8 -*-
"""NACHWEIS Ebene-1-Modul ``agent/zustaende.py`` (01.11.2026, Nutzer: *„a, bauen – prüfen, gegenprüfen und doku“*).

Nur lesend: ``data/_sichten/sichten.db``, die alte Probe aus Git (Stand ceb7df73) und FRED ``release/dates`` (zwei Abfragen).

    N1  Modul = alte Probe an 01.12.2025 und 29.10.2026 - Zeile für Zeile, ohne SF9-Zusatz und ohne den neuen S8-Block
    N2  Rückspiel 01.12.2025–29.10.2026: keine FRED-Zeile leer, der Stand keines Zustands läuft rückwärts (alte Regel: 59 Lochtage)
    N3  ⚠⚠ Vorgriff am ERGEBNIS: je Stichtag volle Ablage = Ablage, die nur Zeilen mit bekannt_ab <= T kennt (und ``bis`` nur, wenn
        der Nachfolger schon bekannt ist) - an allen Stichtagen
    N4  alle Stichtage ohne Fehler, Laufzeit
    N5  S8: FOMC = agent.cycles; CPI/NFP = FRED release/dates; nächster Termin je Stichtag unabhängig nachgerechnet

    python -X utf8 Basisinfos/Rechenkern_02_10/zustaende_nachweis.py
"""
from __future__ import annotations

import os
import subprocess
import sys
import time
import types
from datetime import datetime, timezone

import pandas as pd
import requests

PROJ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, PROJ)
from agent import zustaende as Z          # noqa: E402

ALT = "ceb7df73"                          # letzter Stand der Probe mit eigenem Rechenweg
TAGE = pd.date_range("2025-12-01", "2026-10-29", freq="D")
ergebnis = []


def urteil(name, ok, text):
    ergebnis.append((name, ok))
    print("  %s  %-52s %s" % ("OK  " if ok else "FEHL", name, text), flush=True)


def alte_probe():
    q = subprocess.run(["git", "show", "%s:Basisinfos/Rechenkern_02_10/fuetterung_satzform_probe.py" % ALT], cwd=PROJ,
                       capture_output=True, text=True, encoding="utf-8", check=True).stdout
    m = types.ModuleType("probe_alt")
    m.__file__ = os.path.join(PROJ, "Basisinfos", "Rechenkern_02_10", "fuetterung_satzform_probe.py")
    exec(compile(q, "probe_alt", "exec"), m.__dict__)
    return m


def gekuerzt(df: pd.DataFrame, T: str) -> pd.DataFrame:
    """Was man am Stichtag weiß: Zeilen mit bekannt_ab <= T; ``bis`` nur, wenn der Nachfolger (bis + 2 T 00:00) schon bekannt ist."""
    x = df[df.bekannt_ab <= T].copy()
    nach = (pd.to_datetime(x.bis) + pd.Timedelta(days=2)).dt.strftime("%Y-%m-%dT00:00:00+00:00")
    x.loc[x.bis.notna() & (nach > T), "bis"] = None
    return x


def main() -> int:
    print("=" * 110)
    print("ZUSTÄNDE — NACHWEIS (%s UTC)" % datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M"))
    print("=" * 110)
    a = Z.Ablage()
    import sqlite3
    c = sqlite3.connect("file:%s?mode=ro" % Z.ABLAGE.replace("\\", "/"), uri=True)
    roh = pd.read_sql("SELECT quelle, symbol, datum, wert, bekannt_ab, bis FROM reihe", c)
    c.close()

    # N1
    P = alte_probe()
    for tag in ("2025-12-01", "2026-10-29"):
        T = tag + "T00:00:00+00:00"
        df = roh.copy()
        alt = []
        for d in P.ZUSTAENDE:
            s = P.stand_am(df[(df.quelle == d[1]) & (df.symbol == d[2])], T) if d[2] != "NETTO" else None
            if s is None:                                     # NETTO wie in der alten main()
                w, g, r = (P.stand_am(df[(df.quelle == "fred") & (df.symbol == k)], T) for k in ("WALCL", "WTREGEN", "RRPONTSYD"))
                tg = pd.date_range(min(w.index.min(), g.index.min()), T[:10])
                f = lambda s: s.set_axis(pd.to_datetime(s.index)).reindex(tg).ffill()   # noqa: E731
                n = (f(w) / 1000 - f(g) / 1000 - f(r).fillna(0)).dropna()
                s = n[n.index.isin(pd.to_datetime(w.index))]
                s = s.set_axis(s.index.strftime("%Y-%m-%d"))
            elif d[1] == "stablecoins":
                s = s / 1e9
            alt.append(P.satz(d[0], d[3], d[4], d[5], d[6], s.copy(), T, 5)[0])
        neu = [z.satz for z in Z.zustaende(T, a) if z.sicht != "S8"]
        import re
        ohne = [re.sub(r" ⚠ Stand \d+ T alt \(üblich ≤ \d+ T\)", "", z) for z in neu]
        gleich = sum(x == y for x, y in zip(alt, ohne))
        sf9 = sum(x != y for x, y in zip(neu, ohne))
        urteil("N1 Modul = alte Probe %s" % tag, gleich == len(alt) == len(neu),
               "%d von %d Zeilen gleich (ohne SF9-Zusatz; SF9 an %d Zeilen)" % (gleich, len(alt), sf9))

    # N2 + N3 + N4
    t0 = time.time()
    fehler, leer, rueck, vorgriff, vor_tage = [], 0, [], 0, []
    letzter: dict = {}
    for d in TAGE:
        T = d.strftime("%Y-%m-%dT00:00:00+00:00")
        try:
            liste = Z.zustaende(T, a)
        except Exception as e:                                   # noqa: BLE001
            fehler.append("%s %s" % (T[:10], type(e).__name__))
            continue
        for z in liste:
            k = (z.sicht, z.quelle, z.symbol)
            if z.quelle == "fred" and "KEINE Werte" in z.satz:
                leer += 1
            if z.sicht != "S8" and z.stand and k in letzter and z.stand < letzter[k]:
                rueck.append("%s %s %s<%s" % (T[:10], z.symbol, z.stand, letzter[k]))
            if z.sicht != "S8" and z.stand:
                letzter[k] = z.stand
        k_liste = Z.zustaende(T, Z.Ablage(df=gekuerzt(roh, T)))
        if [z.satz for z in k_liste] != [z.satz for z in liste]:
            vorgriff += 1
            if len(vor_tage) < 3:
                diff = [(x.symbol, x.satz[-70:], y.satz[-70:]) for x, y in zip(liste, k_liste) if x.satz != y.satz][:2]
                vor_tage.append((T[:10], diff))
    dauer = time.time() - t0
    urteil("N2 keine FRED-Zeile leer", leer == 0, "%d Stichtage, leere FRED-Zeilen: %d (alte Regel: 59 Lochtage)" % (len(TAGE), leer))
    urteil("N2 kein Stand läuft rückwärts", not rueck, "%d Fälle %s" % (len(rueck), ", ".join(rueck[:3])))
    urteil("N3 Vorgriff: volle = gekürzte Ablage", vorgriff == 0, "an %d von %d Stichtagen verschieden %s" % (vorgriff, len(TAGE), vor_tage))
    urteil("N4 alle Stichtage ohne Fehler", not fehler, "%d Fehler · %.0f s für %d Stichtage (je zweimal gerechnet)"
           % (len(fehler), dauer, len(TAGE)))

    # N5 Termine
    from agent import cycles as CY
    from agent import termin_fakt as TF
    fomc = sorted(set(CY.FOMC_ERKLAERUNG_2023_2025) | {e for _s, e in CY.FOMC_MEETING_DATES})
    ab = a.gruppen[("termin", "fomc")]
    urteil("N5 FOMC in der Ablage = agent.cycles", sorted(ab.datum) == [x.isoformat() for x in fomc], "%d Termine" % len(fomc))
    from dotenv import load_dotenv
    load_dotenv(os.path.join(PROJ, ".env"))
    for art in ("cpi", "nfp"):
        r = requests.get("https://api.stlouisfed.org/fred/release/dates",
                         params={"release_id": TF.FRED[art], "api_key": os.environ["FRED_API_KEY"], "file_type": "json",
                                 "realtime_start": "2020-01-01", "realtime_end": "9999-12-31",
                                 "include_release_dates_with_no_data": "true", "limit": 10000}, timeout=60).json()
        frisch = sorted({x["date"] for x in r["release_dates"]})
        abl = sorted(a.gruppen[("termin", art)].datum)
        urteil("N5 %s in der Ablage = FRED release/dates" % art.upper(), abl == frisch, "%d Termine (FRED %d)" % (len(abl), len(frisch)))
    falsch = 0
    for d in TAGE:
        T = pd.Timestamp(d, tz="UTC")
        z = {x.symbol: x for x in Z.termine(a, T)}
        nxt = next(f for f in fomc if TF._zeitpunkt(f, "fomc") > T)
        falsch += nxt.isoformat() not in z["fomc"].satz or TF._komma(TF.FAKTOR_2H["fomc"]) + "×" not in z["fomc"].satz
    urteil("N5 nächster FOMC je Stichtag unabhängig nachgerechnet", falsch == 0, "%d Stichtage, falsch %d" % (len(TAGE), falsch))

    print("=" * 110)
    fehl = [x for x, ok in ergebnis if not ok]
    print("%d Prüfungen, %s" % (len(ergebnis), "ALLE BESTANDEN" if not fehl else "%d FEHLGESCHLAGEN: %s" % (len(fehl), ", ".join(fehl))))
    return 1 if fehl else 0


if __name__ == "__main__":
    sys.exit(main())
