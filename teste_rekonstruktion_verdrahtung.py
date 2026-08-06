"""E2E-Test der Rekonstruktions-Verdrahtung (Rohstoffe + Hedge), 2026-08-06.

Laeuft ausschliesslich gegen eine TEMPORAERE DB - die Produktiv-DB wird nicht
angefasst (feedback_desktop_kein_produktivstart). Der yfinance-Abruf ist
gemockt, damit der Test deterministisch und offline laeuft; die Rekonstruktion
selbst wurde separat gegen echte Kursdaten geprueft.
"""
import os
import tempfile
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace


import database.db as db
from database.models import OhlcPoint, PriceSnapshot
import agent.rohstoff.pipeline as roh
import agent.hedge.pipeline as hed
from agent.rekonstruktion import QUELLE_GEMESSEN, QUELLE_REKONSTRUIERT

fehler = []
def pruefe(name, bedingung, info=""):
    print(("  OK   " if bedingung else "  FEHL ") + name + ("  " + info if info else ""))
    if not bedingung:
        fehler.append(name)

JETZT = datetime.now(timezone.utc).isoformat()

def tage(n):
    heute = datetime.now(timezone.utc).date()
    return [(heute - timedelta(days=n - 1 - i)).isoformat() for i in range(n)]

def reihe(symbol, currency, datumsliste, closes):
    return [OhlcPoint(symbol=symbol, currency=currency, date=d, open=c, high=c * 1.01,
                      low=c * 0.99, close=c, volume=1000.0, fetched_at=JETZT)
            for d, c in zip(datumsliste, closes)]

import pathlib
pfad = os.path.join(tempfile.mkdtemp(), "test.db")
db.DB_PATH = pathlib.Path(pfad)          # Produktiv-DB bleibt unangetastet
conn = db.get_connection()
assert str(conn.execute("PRAGMA database_list").fetchone()["file"]).endswith("test.db")
db.init_db(conn)
print(f"Temp-DB: {pfad}\n")

# ---------------------------------------------------------------- Rohstoffe
print("A) ROHSTOFFE - OD7C (Kupfer)")
D = tage(40)
# Futures ~6,30 USD/lb mit Wellenform; ETC notiert bei ~34,63
futures_closes = [6.30 * (1 + 0.02 * ((i % 7) - 3) / 3) for i in range(40)]
abrufe = {"n": 0}

def fake_full(ticker, symbol, currency="USD"):
    abrufe["n"] += 1
    return reihe(symbol, currency, D, futures_closes)

roh.get_full_ohlc_history = fake_full

asset_od7c = SimpleNamespace(symbol="OD7C", assetklasse="rohstoffe",
                             yfinance_symbol="OD7C.SG", name="Kupfer ETC")
db.insert_price_snapshot(conn, PriceSnapshot(
    symbol="OD7C", coingecko_id=None, price_usd=34.63, price_eur=29.92,
    market_cap_usd=None, volume_24h_usd=None, change_24h_pct=None, fetched_at=JETZT))

# A0: Ausgangslage vor dem Fix nachstellen - alte, falsch beschriftete
#     Futures-Historie liegt unter OD7C und ist TAGESAKTUELL.
db.upsert_ohlc_points(conn, reihe("OD7C", "USD", D, futures_closes))
vorher = db.get_ohlc_history(conn, "OD7C", "USD")
pruefe("A0 Ausgangslage: OD7C traegt Futures-Niveau",
       abs(vorher[-1].close - futures_closes[-1]) < 1e-9, f"{vorher[-1].close:.2f}")

roh._ensure_ohlc_backfilled(conn, asset_od7c)

fut = db.get_ohlc_history(conn, "_ROHSTOFF_FUTURES_OD7C", "USD")
etc = db.get_ohlc_history(conn, "OD7C", "USD")
pruefe("A1 Abruf lief trotz frischer Reihe unter OD7C", abrufe["n"] == 1)
pruefe("A2 Futures-Reihe unter eigenem Symbol", len(fut) == 40, f"{len(fut)} Punkte")
pruefe("A3 ETC-Reihe rekonstruiert", len(etc) == 40, f"{len(etc)} Punkte")
pruefe("A4 Ankertag trifft den aktuellen Preis exakt",
       abs(etc[-1].close - 34.63) / 34.63 < 1e-9, f"{etc[-1].close:.4f}")
pruefe("A5 alte Futures-Zeilen unter OD7C ueberschrieben",
       all(p.close > 20 for p in etc), f"min {min(p.close for p in etc):.2f}")

def quelle(sym, cur):
    return conn.execute("SELECT quelle FROM price_history_ohlc WHERE symbol=? AND currency=? "
                        "ORDER BY date DESC LIMIT 1", (sym, cur)).fetchone()["quelle"]

pruefe("A6 quelle Futures = gemessen", quelle("_ROHSTOFF_FUTURES_OD7C", "USD") == QUELLE_GEMESSEN)
pruefe("A7 quelle ETC = rekonstruiert", quelle("OD7C", "USD") == QUELLE_REKONSTRUIERT)

# A8: Form uebertragen? Relative Tagesrenditen muessen uebereinstimmen.
r_fut = [fut[i].close / fut[i - 1].close - 1 for i in range(1, len(fut))]
r_etc = [etc[i].close / etc[i - 1].close - 1 for i in range(1, len(etc))]
pruefe("A8 Tagesrenditen identisch zur Referenz",
       max(abs(a - b) for a, b in zip(r_fut, r_etc)) < 1e-12)

# A9: zweiter Aufruf - Staleness-Wache greift jetzt (Futures-Reihe ist frisch)
roh._ensure_ohlc_backfilled(conn, asset_od7c)
pruefe("A9 zweiter Aufruf ohne erneuten Abruf", abrufe["n"] == 1)

# A9b: DER FALL, DER IM BETRIEB GESCHEITERT IST. Ist die Futures-Reihe frisch,
# wird nicht neu abgerufen - die REKONSTRUKTION muss trotzdem laufen. Sie haengt
# an einem Ankerpreis, der sich taeglich bewegt, nicht an der Futures-Frische.
# Der erste Entwurf sprang bei frischer Futures-Reihe heraus und uebersprang die
# Rekonstruktion mit; im Betrieb hatten die vier ETCs dadurch 91 von 91 Tagen
# ohne Kurs, waehrend der Entwicklungsstand (veraltete Futures-Reihe) sauber aussah.
conn.execute("DELETE FROM price_history_ohlc WHERE symbol='OD7C'")
conn.commit()
vorher_abrufe = abrufe["n"]
roh._ensure_ohlc_backfilled(conn, asset_od7c)
etc_neu = db.get_ohlc_history(conn, "OD7C", "USD")
pruefe("A9b Rekonstruktion laeuft auch bei FRISCHER Futures-Reihe",
       len(etc_neu) == 40 and abs(etc_neu[-1].close - 34.63) / 34.63 < 1e-9,
       f"{len(etc_neu)} Punkte, kein neuer Abruf: {abrufe['n'] == vorher_abrufe}")
pruefe("A9c dabei kein unnoetiger Netzabruf", abrufe["n"] == vorher_abrufe)

# A10: technische Analyse liest die FUTURES-Reihe
d2, closes2, hist2, last2 = roh._load_ohlc(conn, roh._futures_symbol("OD7C"))
pruefe("A10 TA-Pfad liefert Futures-Niveau", abs(closes2[-1] - futures_closes[-1]) < 1e-9,
       f"{closes2[-1]:.2f} statt {etc[-1].close:.2f}")

# A11: Rueckfall, wenn die Futures-Reihe fehlt
conn.execute("DELETE FROM price_history_ohlc WHERE symbol='_ROHSTOFF_FUTURES_OD7C'")
conn.commit()
d3, closes3, hist3, last3 = roh._load_ohlc(conn, roh._futures_symbol("OD7C"))
pruefe("A11 fehlende Futures-Reihe erkannt (Rueckfall greift)", last3 is None)

# --------------------------------------------------------------------- Hedge
print("\nB) HEDGE - 3QSS (Nasdaq-100 3x Short)")
D2 = tage(30)
# Index mit deutlicher Schwankung, damit der Volatilitaets-Drag sichtbar wird
idx_closes = [20000.0 * (1 + 0.03 * ((i % 4) - 1.5) / 1.5) for i in range(30)]
hedge_abrufe = []

def fake_hedge_full(ticker, symbol, currency="USD"):
    hedge_abrufe.append((ticker, symbol))
    if ticker.startswith("^"):
        return reihe(symbol, currency, D2, idx_closes)
    return []          # 3QSS liefert nachweislich keine Historie

hed.get_full_ohlc_history = fake_hedge_full

asset_3qss = SimpleNamespace(symbol="3QSS", assetklasse="hedge",
                             yfinance_symbol="IE00BLRPRJ20.SG", name="Nasdaq 3x Short")
db.insert_price_snapshot(conn, PriceSnapshot(
    symbol="3QSS", coingecko_id=None, price_usd=1.673, price_eur=1.4455,
    market_cap_usd=None, volume_24h_usd=None, change_24h_pct=None, fetched_at=JETZT))

hed._ensure_ohlc_backfilled(conn, asset_3qss)
h = db.get_ohlc_history(conn, "3QSS", "EUR")
pruefe("B1 Reihe entstanden", len(h) == 30, f"{len(h)} Punkte")
pruefe("B2 Ankertag trifft den aktuellen EUR-Preis exakt",
       abs(h[-1].close - 1.4455) / 1.4455 < 1e-9, f"{h[-1].close:.6f}")
pruefe("B3 quelle = rekonstruiert", quelle("3QSS", "EUR") == QUELLE_REKONSTRUIERT)
pruefe("B4 Indexreihe unter eigenem Symbol abgelegt",
       len(db.get_ohlc_history(conn, "_HEDGE_INDEX_3QSS", "USD")) == 30)

# B5: invers und 3x - Indexrendite und Produktrendite gegenlaeufig, Faktor 3
r_idx = [idx_closes[i] / idx_closes[i - 1] - 1 for i in range(1, 30)]
r_h = [h[i].close / h[i - 1].close - 1 for i in range(1, 30)]
pruefe("B5 Rendite = -3x Indexrendite (taeglich)",
       max(abs(rh + 3 * ri) for ri, rh in zip(r_idx, r_h)) < 1e-12,
       f"Index {r_idx[0]*100:+.2f} % -> 3QSS {r_h[0]*100:+.2f} %")

# B6: Volatilitaets-Drag - Index seitwaerts, Produkt verliert
idx_ges = idx_closes[-1] / idx_closes[0] - 1
h_ges = h[-1].close / h[0].close - 1
naiv = -3 * idx_ges
pruefe("B6 Verkettung != naive Hochrechnung (Drag sichtbar)",
       abs(h_ges - naiv) > 0.01,
       f"Index {idx_ges*100:+.2f} % | naiv {naiv*100:+.2f} % | verkettet {h_ges*100:+.2f} %")

# B7: Hoch/Tief invertiert - an einem Tag mit high>close muss low<close entstehen
pruefe("B7 Hoch/Tief bei inversem Produkt vertauscht",
       all(p.high >= p.close >= p.low for p in h) and h[5].high > h[5].close)

# B8: erneuter Lauf verankert neu statt die Staleness-Wache greifen zu lassen
db.insert_price_snapshot(conn, PriceSnapshot(
    symbol="3QSS", coingecko_id=None, price_usd=1.73, price_eur=1.5000,
    market_cap_usd=None, volume_24h_usd=None, change_24h_pct=None,
    fetched_at=(datetime.now(timezone.utc) + timedelta(minutes=1)).isoformat()))
hed._ensure_ohlc_backfilled(conn, asset_3qss)
h2 = db.get_ohlc_history(conn, "3QSS", "EUR")
pruefe("B8 Neuverankerung auf den aktuellen Preis",
       abs(h2[-1].close - 1.5000) / 1.5 < 1e-9, f"{h2[-1].close:.6f}")
pruefe("B9 kein Direktabruf bei rekonstruierter Reihe",
       not any(s == "3QSS" for _, s in hedge_abrufe[2:]),
       f"Abrufe gesamt: {[t for t, _ in hedge_abrufe]}")

# B10: DBPK hat echte Historie - keine Rekonstruktion
def fake_hedge_dbpk(ticker, symbol, currency="USD"):
    hedge_abrufe.append((ticker, symbol))
    return reihe(symbol, currency, D2, [12.0 + 0.01 * i for i in range(30)])

hed.get_full_ohlc_history = fake_hedge_dbpk
asset_dbpk = SimpleNamespace(symbol="DBPK", assetklasse="hedge",
                             yfinance_symbol="DBPK.DE", name="S&P 2x Inverse")
hed._ensure_ohlc_backfilled(conn, asset_dbpk)
pruefe("B10 DBPK bleibt gemessen", quelle("DBPK", "EUR") == QUELLE_GEMESSEN)

# ------------------------------------------------------------ Robustheit
print("\nC) ROBUSTHEIT")
# C1: kein Ankerpreis -> keine Reihe, kein Absturz
asset_x = SimpleNamespace(symbol="OD7L", assetklasse="rohstoffe",
                          yfinance_symbol="JE00BN7KB334.SG", name="Erdgas")
roh._rekonstruiere_etc_reihe(conn, asset_x, reihe("_x", "USD", D, futures_closes))
pruefe("C1 ohne Ankerpreis keine Reihe (kein Absturz)",
       len(db.get_ohlc_history(conn, "OD7L", "USD")) == 0)

# C2: kaputter Referenzpunkt pflanzt sich nicht fort
kaputt = list(futures_closes)
kaputt[20] = 0.63          # -90 % Ausreisser
roh._rekonstruiere_etc_reihe(conn, asset_od7c, reihe("_y", "USD", D, kaputt))
e2 = db.get_ohlc_history(conn, "OD7C", "USD")
pruefe("C2 Ausreisser nicht in die Reihe uebernommen",
       all(p.close > 20 for p in e2), f"min {min(p.close for p in e2):.2f}")

# C3: unbekanntes Hedge-Symbol -> sauberer Ausstieg
asset_unb = SimpleNamespace(symbol="XXXX", assetklasse="hedge",
                            yfinance_symbol="XXXX.DE", name="unbekannt")
hed._rekonstruiere_hedge_reihe(conn, asset_unb)
pruefe("C3 unbekanntes Hedge-Symbol ohne Absturz",
       len(db.get_ohlc_history(conn, "XXXX", "EUR")) == 0)

print("\n" + ("ALLE TESTS BESTANDEN" if not fehler else f"FEHLER: {fehler}"))
conn.close()
