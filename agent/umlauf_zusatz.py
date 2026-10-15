"""P22b Umlaufmenge fuer Coins AUSSERHALB der Binance-Messmenge - eigene Zusatztabelle (15.10.2026; Spot §56/§57, Variante B).

Nutzer 15.10.: *"Ja, Variante B bauen, pruefen und gegenpruefen"*.

WARUM EINE EIGENE TABELLE (§57 Teil 3, gemessen): Kaemen die Coins in die Tabelle ``umlaufmenge``, bekaemen sie dort einen Marktwert-
Rang - KAS und XDC stiegen in der B4-Klasse auf, drei UNBETEILIGTE Coins (1000CHEEMS, BAT, GLM) fielen ab, und die turnover-Messbasis
(Symbolliste von ``umlaufmenge``) wuechse um HYPE und ASTER. Die Grundgesamtheit ist keine Stellschraube. Deshalb:

    umlaufmenge_zusatz (symbol, datum, wert)   - liest NUR agent.verwaesserung (Wert, Rhythmus) und die Verwaesserungsrechnung im B4-Lauf
    abruf_zusatz       (symbol, coingecko_id, urteil, punkte, weg, spruenge, groesster, stabil, geholt_am)

``umlaufmenge`` (B4-Klassen, turnover, Datenfrische) bleibt unberuehrt, die Marke ``_nur_betrieb`` auch.

WER ZUSATZ-COIN IST: jeder Watchlist-Krypto-Eintrag mit CoinGecko-ID, der in ``umlaufmenge`` keine Reihe hat - also auch jeder kuenftig
aufgenommene Coin ausserhalb Binance. Kein Stablecoin (Median |Tagesrendite| < 0,2 %, dieselbe Regel wie B4).

WIE ER GEFUELLT WIRD (am NB, Job ``externe_reihen``, taeglich 06:35): ``pflege`` holt fuer neue Coins EINMAL 365 T (market_chart,
Zerlegung wie der Vollabruf: Marktwert/Preis, Buendelfaktor, MIND_PUNKTE) und schreibt danach jeden Tag den Wert von heute
(/coins/markets circulating_supply, dieselbe Groesse - Median-Abweichung 0,000 % an 119 Symbolen). Ein Abruffehler ist KEIN Urteil
(naechster Lauf versucht erneut). Freie Grenze gemessen 5 Abrufe je Minute -> Pause aus hole_umlaufmenge_cg, hoechstens ERSTABRUF_JE_LAUF.
"""
from __future__ import annotations

import datetime as dt
import os
import sqlite3
import time

import numpy as np
import pandas as pd

ERSTABRUF_JE_LAUF = 20
STABIL = 0.002


def schema(c: sqlite3.Connection) -> None:
    c.execute("CREATE TABLE IF NOT EXISTS umlaufmenge_zusatz (symbol TEXT NOT NULL, datum TEXT NOT NULL, wert REAL NOT NULL, "
              "PRIMARY KEY (symbol, datum))")
    c.execute("CREATE TABLE IF NOT EXISTS abruf_zusatz (symbol TEXT PRIMARY KEY, coingecko_id TEXT, urteil TEXT, punkte INTEGER, weg INTEGER, "
              "spruenge INTEGER, groesster REAL, stabil REAL, geholt_am TEXT)")


def kandidaten(c: sqlite3.Connection, watchlist) -> list:
    """[(Symbol, CoinGecko-ID)] - Watchlist-Krypto mit ID, ohne Reihe in ``umlaufmenge``."""
    in_haupt = {r[0] for r in c.execute("SELECT DISTINCT symbol FROM umlaufmenge")}
    aus = []
    for a in watchlist:
        s = getattr(a, "symbol", None) or (a.get("symbol") if isinstance(a, dict) else None)
        cid = getattr(a, "coingecko_id", None) or (a.get("coingecko_id") if isinstance(a, dict) else None)
        klasse = str(getattr(a, "asset_class", None) or getattr(a, "assetklasse", None) or
                     ((a.get("asset_class") or a.get("assetklasse")) if isinstance(a, dict) else None) or "krypto").lower()
        cash = bool(getattr(a, "ist_cash_aequivalent", None) or (a.get("ist_cash_aequivalent") if isinstance(a, dict) else False))
        if s and cid and s not in in_haupt and klasse in ("krypto", "crypto") and not cash:
            aus.append((s, cid))
    return sorted(set(aus))


def _urteil(reihe, preise) -> tuple:
    import hole_umlaufmenge_cg as HU
    p = np.array([k for _, k in preise if k], dtype=float)
    med = float(np.median(np.abs(np.diff(p) / p[:-1]))) if len(p) > 2 else None
    if med is not None and med < STABIL:
        return "stablecoin", med
    return ("ok" if len(reihe) >= HU.MIND_PUNKTE else "verworfen"), med


def pflege(ziel: str, watchlist, http=None, heute: dt.date | None = None, pause: float | None = None) -> dict:
    """Erstabruf fuer neue Zusatz-Coins (hoechstens ERSTABRUF_JE_LAUF) und der Tageswert fuer alle 'ok'. Schreibt NUR die beiden
    Zusatztabellen. ``http(url) -> (status, json)`` (Pruefstand); Vorgabe hole_umlaufmenge_cg.hole. Scheitert nie nach aussen."""
    import hole_umlaufmenge_cg as HU
    hole = http or HU.hole
    pause = HU._PAUSE[0] if pause is None else pause
    heute = heute or dt.datetime.now(dt.timezone.utc).date()
    erg = {"kandidaten": 0, "erstabruf": [], "fehler": [], "tageswert": 0, "ohne_wert": 0}
    if not os.path.exists(ziel):
        erg["grund"] = "%s fehlt" % ziel
        return erg
    c = sqlite3.connect(ziel, timeout=60)
    try:
        schema(c)
        kand = kandidaten(c, watchlist)
        erg["kandidaten"] = len(kand)
        fertig = {r[0] for r in c.execute("SELECT symbol FROM abruf_zusatz WHERE urteil IN ('ok','verworfen','stablecoin')")}
        jt = dt.datetime.now(dt.timezone.utc).isoformat()
        for sym, cid in [k for k in kand if k[0] not in fertig][:ERSTABRUF_JE_LAUF]:
            st, d = hole("%s/coins/%s/market_chart?vs_currency=usd&days=%d&interval=daily" % (HU.CG, cid, HU.TAGE))
            if not isinstance(d, dict):
                c.execute("INSERT OR REPLACE INTO abruf_zusatz (symbol, coingecko_id, urteil, geholt_am) VALUES (?,?,?,?)",
                          (sym, cid, "abruf %s" % st, jt))
                erg["fehler"].append(sym)
            else:
                faktor, _ = HU.vervielfacher(sym)
                reihe, weg, spr, gr = HU.zerlege(sym, d, faktor)
                urteil, med = _urteil(reihe, d.get("prices") or [])
                if urteil == "ok":
                    c.executemany("INSERT OR REPLACE INTO umlaufmenge_zusatz VALUES (?,?,?)", reihe)
                c.execute("INSERT OR REPLACE INTO abruf_zusatz VALUES (?,?,?,?,?,?,?,?,?)",
                          (sym, cid, urteil, len(reihe), weg, spr, round(gr, 4), med, jt))
                erg["erstabruf"].append((sym, urteil, len(reihe)))
            c.commit()
            if pause:
                time.sleep(pause)
        # Tageswert fuer alle 'ok' (ein Buendelabruf)
        ok = {r[0]: r[1] for r in c.execute("SELECT symbol, coingecko_id FROM abruf_zusatz WHERE urteil='ok'")}
        schon = {r[0] for r in c.execute("SELECT symbol FROM umlaufmenge_zusatz WHERE datum=?", (heute.isoformat(),))}
        offen = [(s, i) for s, i in ok.items() if s not in schon]
        if offen:
            st, d = hole("%s/coins/markets?vs_currency=usd&ids=%s&per_page=250" % (HU.CG, ",".join(i for _, i in offen)))
            if isinstance(d, list):
                je = {e.get("id"): e.get("circulating_supply") for e in d}
                for s, i in offen:
                    w = je.get(i)
                    if not w or float(w) <= 0:
                        erg["ohne_wert"] += 1
                        continue
                    f, _ = HU.vervielfacher(s)
                    c.execute("INSERT OR REPLACE INTO umlaufmenge_zusatz VALUES (?,?,?)", (s, heute.isoformat(), float(w) / f))
                    erg["tageswert"] += 1
                c.commit()
            else:
                erg["fehler"].append("markets %s" % st)
    except Exception as exc:                                     # noqa: BLE001
        erg["fehler"].append("%s: %s" % (type(exc).__name__, exc))
    finally:
        c.close()
    return erg


def reihen(ordner_oder_datei: str) -> dict:
    """{Symbol: pd.Series} aus ``umlaufmenge_zusatz`` (nur 'ok'); leer, wenn es die Tabelle nicht gibt. Nur lesend."""
    p = ordner_oder_datei if ordner_oder_datei.endswith(".db") else os.path.join(ordner_oder_datei, "umlaufmenge_cg.db")
    if not os.path.exists(p):
        return {}
    c = sqlite3.connect("file:%s?mode=ro" % p.replace("\\", "/"), uri=True, timeout=10)
    try:
        if not c.execute("SELECT name FROM sqlite_master WHERE name='umlaufmenge_zusatz'").fetchone():
            return {}
        d = pd.read_sql("SELECT z.symbol, z.datum, z.wert FROM umlaufmenge_zusatz z JOIN abruf_zusatz a ON a.symbol = z.symbol "
                        "WHERE a.urteil = 'ok'", c)
    finally:
        c.close()
    if not len(d):
        return {}
    d["datum"] = pd.to_datetime(d.datum.str[:10])
    return {s: g.set_index("datum")["wert"].sort_index() for s, g in d.groupby("symbol")}


def stand(ordner_oder_datei: str) -> dict:
    """Diagnose/Teilexport: Zahl je Urteil, Datenstand."""
    p = ordner_oder_datei if ordner_oder_datei.endswith(".db") else os.path.join(ordner_oder_datei, "umlaufmenge_cg.db")
    if not os.path.exists(p):
        return {"vorhanden": False}
    c = sqlite3.connect("file:%s?mode=ro" % p.replace("\\", "/"), uri=True, timeout=10)
    try:
        if not c.execute("SELECT name FROM sqlite_master WHERE name='abruf_zusatz'").fetchone():
            return {"vorhanden": True, "tabelle": False}
        je = {r[0]: r[1] for r in c.execute("SELECT urteil, COUNT(*) FROM abruf_zusatz GROUP BY urteil")}
        a, b, n = c.execute("SELECT MIN(datum), MAX(datum), COUNT(DISTINCT symbol) FROM umlaufmenge_zusatz").fetchone()
        ok = [r[0] for r in c.execute("SELECT symbol FROM abruf_zusatz WHERE urteil='ok' ORDER BY symbol")]
        return {"vorhanden": True, "tabelle": True, "je_urteil": je, "von": a, "bis": b, "symbole": n, "ok": ok}
    finally:
        c.close()
