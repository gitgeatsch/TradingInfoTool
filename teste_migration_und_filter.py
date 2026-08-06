"""Test der beiden Sicherungen gegen den Scheinwert-Fund (06.08.):
Migration der falsch abgelegten Futures-Reihen + Plausibilitaetsfilter.

Temporaere DB, Produktiv-DB wird nicht angefasst.
"""
import os
import pathlib
import tempfile
from datetime import datetime, timedelta, timezone


import database.db as db
from database.models import OhlcPoint, PriceSnapshot

fehler = []
def pruefe(name, ok, info=""):
    print(("  OK   " if ok else "  FEHL ") + name + ("  " + info if info else ""))
    if not ok:
        fehler.append(name)

JETZT = datetime.now(timezone.utc).isoformat()
heute = datetime.now(timezone.utc).date()
D = [(heute - timedelta(days=9 - i)).isoformat() for i in range(10)]

def reihe(sym, cur, closes):
    return [OhlcPoint(symbol=sym, currency=cur, date=d, open=c, high=c, low=c,
                      close=c, volume=0.0, fetched_at=JETZT)
            for d, c in zip(D, closes)]

db.DB_PATH = pathlib.Path(os.path.join(tempfile.mkdtemp(), "test.db"))
conn = db.get_connection()
db.init_db(conn)

print("A) MIGRATION - Futures-Reihe unter dem ETC-Symbol")
# Ausgangslage: Gold-Future-Kurse unter OD7H, wie in der Produktiv-DB
db.upsert_ohlc_points(conn, reihe("OD7H", "USD", [4200.0 + i for i in range(10)]))
db.upsert_ohlc_points(conn, reihe("OD7C", "USD", [6.6] * 10))
vorher_h = len(db.get_ohlc_history(conn, "OD7H", "USD"))

db._migrate_rohstoff_futures_reihen_umziehen(conn)

pruefe("A1 ETC-Symbol ist leer", len(db.get_ohlc_history(conn, "OD7H", "USD")) == 0)
pruefe("A2 Reihe unter dem Futures-Symbol angekommen",
       len(db.get_ohlc_history(conn, "_ROHSTOFF_FUTURES_OD7H", "USD")) == vorher_h,
       f"{vorher_h} Punkte")
pruefe("A3 Kurse unveraendert (Umzug, keine Umrechnung)",
       db.get_ohlc_history(conn, "_ROHSTOFF_FUTURES_OD7H", "USD")[-1].close == 4209.0)
pruefe("A4 zweites Symbol ebenfalls umgezogen",
       len(db.get_ohlc_history(conn, "_ROHSTOFF_FUTURES_OD7C", "USD")) == 10
       and len(db.get_ohlc_history(conn, "OD7C", "USD")) == 0)

# Idempotenz: die Pipeline schreibt jetzt selbst, danach darf nichts mehr wandern
db.upsert_ohlc_points(conn, reihe("OD7H", "USD", [18.2] * 10))
db._migrate_rohstoff_futures_reihen_umziehen(conn)
h = db.get_ohlc_history(conn, "OD7H", "USD")
pruefe("A5 idempotent - neue ETC-Reihe bleibt stehen", len(h) == 10 and h[-1].close == 18.2)

db._migrate_rohstoff_futures_reihen_umziehen(conn)
pruefe("A6 dritter Aufruf aendert nichts", len(db.get_ohlc_history(conn, "OD7H", "USD")) == 10)

# Symbol ohne jede Reihe
pruefe("A7 fehlende Reihe ist kein Fehlerfall",
       len(db.get_ohlc_history(conn, "_ROHSTOFF_FUTURES_OD7L", "USD")) == 0)

print("\nB) PLAUSIBILITAETSFILTER - Reihe passt nicht zum Instrument")
import agent.portfolio_historie as ph

# OD7N traegt Silber-Future (61,75 USD), echter ETC-Preis 43,80 EUR -> Faktor ~1,6
# ueber FX, aber in USD verglichen: 61,75 vs. 50,70 USD Snapshot -> unauffaellig.
# Der harte Fall ist OD7H: Reihe 4209 USD, Snapshot 21,09 USD -> Faktor 200.
db.upsert_ohlc_points(conn, reihe("OD7H", "USD", [4200.0 + i for i in range(10)]))
db.upsert_ohlc_points(conn, reihe("BTC", "USD", [64000.0] * 10))
db.upsert_ohlc_points(conn, reihe("BTC", "EUR", [55000.0] * 10))
for sym, usd, eur in (("OD7H", 21.09, 18.215), ("BTC", 64593.2, 55838.3)):
    db.insert_price_snapshot(conn, PriceSnapshot(
        symbol=sym, coingecko_id=None, price_usd=usd, price_eur=eur,
        market_cap_usd=None, volume_24h_usd=None, change_24h_pct=None,
        fetched_at=(datetime.now(timezone.utc) + timedelta(seconds=len(sym))).isoformat()))

direkt = {"BTC": {d: 55000.0 for d in D}}
usd_roh = {"OD7H": {d: 4200.0 + i for i, d in enumerate(D)},
           "BTC": {d: 64000.0 for d in D}}
verworfen = ph._verwerfe_unplausible_reihen(conn, direkt, usd_roh)
pruefe("B1 unplausible Reihe verworfen", "OD7H" not in usd_roh, str(verworfen))
pruefe("B2 gesunde Reihen bleiben", "BTC" in usd_roh and "BTC" in direkt)
pruefe("B3 Verwurf wird berichtet", len(verworfen) == 1 and "OD7H" in verworfen[0])

# Ohne Snapshot darf NICHT verworfen werden
usd2 = {"XYZ": {D[0]: 1000.0}}
v2 = ph._verwerfe_unplausible_reihen(conn, {}, usd2)
pruefe("B4 ohne Snapshot kein Verwurf", "XYZ" in usd2 and not v2)

# Grenzfall: Faktor knapp unter und knapp ueber der Schwelle
db.insert_price_snapshot(conn, PriceSnapshot(
    symbol="GRENZ", coingecko_id=None, price_usd=100.0, price_eur=None,
    market_cap_usd=None, volume_24h_usd=None, change_24h_pct=None,
    fetched_at=(datetime.now(timezone.utc) + timedelta(seconds=99)).isoformat()))
u_knapp = {"GRENZ": {D[-1]: 299.0}}
u_drueber = {"GRENZ": {D[-1]: 301.0}}
ph._verwerfe_unplausible_reihen(conn, {}, u_knapp)
ph._verwerfe_unplausible_reihen(conn, {}, u_drueber)
pruefe("B5 Faktor 2,99 bleibt", "GRENZ" in u_knapp)
pruefe("B6 Faktor 3,01 faellt", "GRENZ" not in u_drueber)

# Richtung egal - auch eine zu KLEINE Reihe faellt
u_klein = {"GRENZ": {D[-1]: 1.0}}
ph._verwerfe_unplausible_reihen(conn, {}, u_klein)
pruefe("B7 auch zu kleine Reihe faellt", "GRENZ" not in u_klein)

# B8: eine VERALTETE Reihe wird nicht geprueft - eine grosse Bewegung ueber eine
# Datenluecke ist eine Kursbewegung, kein Etikettenfehler
alt_tag = (heute - timedelta(days=30)).isoformat()
u_alt = {"GRENZ": {alt_tag: 1000.0}}
v_alt = ph._verwerfe_unplausible_reihen(conn, {}, u_alt)
pruefe("B8 veraltete Reihe bleibt unangetastet", "GRENZ" in u_alt and not v_alt)

print("\n" + ("ALLE TESTS BESTANDEN" if not fehler else f"FEHLER: {fehler}"))
conn.close()
