"""Prueft das Hedge-Erfolgsmass (W1, 2026-08-07).

WAS HIER GEPRUEFT WIRD, UND WARUM ES NICHT "INVERTIEREN" HEISST. Der naive
Ansatz waere, das R-Multiple eines Hedge-Trades umzudrehen. Das waere falsch:
kauft man 3QSS bei 1,45 mit Ziel 1,65 und der Nasdaq faellt, steigt 3QSS und
der Trade gewinnt - die R-Rechnung stimmt bereits. Falsch ist nur, sie zu einer
Guetekennzahl zu aggregieren, die "negativ = schlecht" bedeutet.

Das richtige Mass ist ein PORTFOLIO-Mass: derselbe Bestand einmal mit und
einmal ohne Absicherung, beide mengenkonstant verkettet, dann die Rueckschlaege
verglichen. Genau das prueft dieser Test - an einem konstruierten Fall mit
BEKANNTER Antwort, damit die Rechnung falsifizierbar ist.
"""
import pathlib
import tempfile
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import database.db as db
from database.models import OhlcPoint

fehler = []
def pruefe(name, ok, info=""):
    print(("  OK   " if ok else "  FEHL ") + name + ("  " + info if info else ""))
    if not ok:
        fehler.append(name)

db.DB_PATH = pathlib.Path(tempfile.mkdtemp()) / "test.db"
conn = db.get_connection()
db.init_db(conn)

JETZT = datetime.now(timezone.utc).isoformat()
heute = datetime.now(timezone.utc).date()
TAGE = [(heute - timedelta(days=29 - i)).isoformat() for i in range(30)]
AB = TAGE[0]

def schreibe(symbol, kurse):
    db.upsert_ohlc_points(conn, [
        OhlcPoint(symbol=symbol, currency="EUR", date=t, open=k, high=k, low=k,
                  close=k, volume=1.0, fetched_at=JETZT)
        for t, k in zip(TAGE, kurse)])

# Long-Position: steigt 10 Tage, faellt dann um 30 %, erholt sich leicht.
long_kurse = ([100.0 + i for i in range(10)]
              + [110.0 * (1 - 0.30 * (i + 1) / 10) for i in range(10)]
              + [77.0 + i for i in range(10)])
# Hedge: exakt gegenlaeufig mit Faktor 1 (der Einfachheit halber)
hedge_kurse = [100.0 * (2 - k / 100.0) for k in long_kurse]

schreibe("LONGX", long_kurse)
schreibe("HEDGEX", hedge_kurse)
db.upsert_holding(conn, "LONGX", 100.0)
db.upsert_holding(conn, "HEDGEX", 100.0)

watchlist = [
    SimpleNamespace(symbol="LONGX", assetklasse="krypto", coingecko_id=None,
                    ist_cash_aequivalent=False),
    SimpleNamespace(symbol="HEDGEX", assetklasse="etf", coingecko_id=None,
                    ist_cash_aequivalent=False),
]

import agent.hedge.pipeline as hedge_pipeline
hedge_pipeline.SYMBOL_ZU_HEBEL_FAKTOR = {"HEDGEX": 1.0}

from agent.portfolio_historie import compute_hedge_wirksamkeit

print("A) KONSTRUIERTER FALL MIT BEKANNTER ANTWORT")
erg = compute_hedge_wirksamkeit(conn, ab_datum=AB, watchlist=watchlist)
pruefe("A1 messbar", erg.get("messbar") is True, erg.get("grund", ""))
pruefe("A2 nur das Hedge-Instrument erkannt",
       erg.get("hedge_symbole_bewertet") == ["HEDGEX"])
pruefe("A3 beide Reihen abgedeckt",
       all(n >= 2 for n in (erg.get("abdeckung_je_symbol") or {}).values()))

r_mit = erg["rueckschlag_mit_hedge_prozent"]
r_ohne = erg["rueckschlag_ohne_hedge_prozent"]
pruefe("A4 Rueckschlag OHNE Hedge ist der volle Einbruch",
       25.0 < r_ohne < 32.0, f"{r_ohne:.2f} %")
pruefe("A5 Absicherung daempft den Rueckschlag",
       erg["daempfung_prozentpunkte"] > 5.0,
       f"{r_ohne:.2f} % ohne -> {r_mit:.2f} % mit  (Daempfung "
       f"{erg['daempfung_prozentpunkte']:.2f} pp)")
pruefe("A6 Praemie wird ausgewiesen", erg.get("praemie_prozent") is not None,
       f"{erg['praemie_prozent']:+.2f} %")

print("\nB) DIE PRAEMIE - im steigenden Markt kostet Absicherung Rendite")
# Nur steigender Markt, kein Einbruch
schreibe("LONGX", [100.0 + 2 * i for i in range(30)])
schreibe("HEDGEX", [100.0 * (2 - (100.0 + 2 * i) / 100.0) for i in range(30)])
erg2 = compute_hedge_wirksamkeit(conn, ab_datum=AB, watchlist=watchlist)
pruefe("B1 keine Daempfung noetig, keine vorhanden",
       abs(erg2["daempfung_prozentpunkte"]) < 1e-6,
       f"{erg2['daempfung_prozentpunkte']:.4f} pp")
pruefe("B2 Praemie ist NEGATIV - die Versicherung hat Rendite gekostet",
       erg2["praemie_prozent"] < 0, f"{erg2['praemie_prozent']:+.2f} %")

print("\nC) MESSBARKEITS-WACHE - der stille Nullfall")
conn.execute("DELETE FROM price_history_ohlc WHERE symbol = 'HEDGEX'")
conn.commit()
erg3 = compute_hedge_wirksamkeit(conn, ab_datum=AB, watchlist=watchlist)
pruefe("C1 ohne Hedge-Kurse: NICHT messbar statt Daempfung 0,0",
       erg3.get("messbar") is False, erg3.get("grund", ""))
pruefe("C2 Grund wird benannt", "Kursreihe" in (erg3.get("grund") or ""))

conn.execute("DELETE FROM holdings WHERE symbol = 'HEDGEX'")
conn.commit()
erg4 = compute_hedge_wirksamkeit(conn, ab_datum=AB, watchlist=watchlist)
pruefe("C3 ohne Hedge-Bestand: NICHT messbar",
       erg4.get("messbar") is False and "Bestand" in (erg4.get("grund") or ""),
       erg4.get("grund", ""))

print("\nD) TIER-TRENNUNG")
from agent.krypto.backward_tracking import _assetklasse_index, TIER_HEDGE
idx = _assetklasse_index(watchlist, "test")
pruefe("D1 Hedge bekommt eigenen Tier", idx.get("HEDGEX") == TIER_HEDGE, idx.get("HEDGEX"))
pruefe("D2 andere Assets unveraendert", idx.get("LONGX") == "krypto")

print("\n" + ("ALLE TESTS BESTANDEN" if not fehler else f"FEHLER: {fehler}"))
conn.close()
