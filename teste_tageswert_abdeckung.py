"""Prueft Bezugstag und Abdeckungswache des taeglichen Portfolio-Wert-Jobs.

ANLASS (07.08.). Beide Zeilen, die der Job je geschrieben hat, waren
unbrauchbar - 3,0 % und 42,4 % Abdeckung, gegen 87-98 % bei den nachtraeglich
rekonstruierten Zeilen. Ursache war die Uhrzeit: der Job laeuft um 06:30 und
bewertete den LAUFENDEN Tag, fuer den es noch kaum Tageskerzen gibt.

Zwei Korrekturen, beide hier geprueft:
  1. Bezugstag ist der VORTAG - ein Tagesschlusswert existiert erst nach
     Tagesende.
  2. Abdeckungswache als Netz - faellt die Abdeckung unter die Schwelle, wird
     GAR NICHTS geschrieben statt eines Werts, der wie ein Kurssturz aussieht.
"""
import pathlib
import tempfile
from datetime import datetime, timedelta, timezone

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
GESTERN = (heute - timedelta(days=1)).isoformat()
HEUTE = heute.isoformat()
SYMBOLE = [f"T{i}" for i in range(10)]

import agent.portfolio_historie as ph
from types import SimpleNamespace

watchlist = [SimpleNamespace(symbol=s, coingecko_id=None, ist_cash_aequivalent=False)
             for s in SYMBOLE]
for s in SYMBOLE:
    db.upsert_holding(conn, s, 10.0)

def schreibe_kurse(tage, symbole):
    db.upsert_ohlc_points(conn, [
        OhlcPoint(symbol=s, currency="EUR", date=t, open=100.0, high=100.0,
                  low=100.0, close=100.0, volume=1.0, fetched_at=JETZT)
        for s in symbole for t in tage])

print("A) BEZUGSTAG")
# Alle Symbole haben GESTERN einen Kurs, heute nur eines - der reale Fall um 06:30
schreibe_kurse([GESTERN], SYMBOLE)
schreibe_kurse([HEUTE], SYMBOLE[:1])

erg = ph.schreibe_tageswert(conn, watchlist=watchlist)
pruefe("A1 Job schreibt den VORTAG, nicht heute", erg["datum"] == GESTERN, erg["datum"])
pruefe("A2 Vortag ist vollstaendig abgedeckt", erg.get("abdeckung") == 1.0,
       f"{erg.get('abdeckung', 0)*100:.0f} %")
pruefe("A3 Wert entspricht 10 Symbole x 10 Stueck x 100 EUR",
       abs(erg["wert_eur"] - 10000.0) < 1e-6, f"{erg['wert_eur']:,.2f} EUR")

zeilen = db.get_portfolio_wert_historie(conn)
pruefe("A4 genau eine Zeile geschrieben", len(zeilen) == 1)
pruefe("A5 der laufende Tag steht NICHT in der Reihe",
       all(z["datum"] != HEUTE for z in zeilen))

print("\nB) ABDECKUNGSWACHE")
# Ein Tag, an dem nur 3 von 10 Symbolen einen Kurs haben (30 % < 80 %)
vorvortag = (heute - timedelta(days=2)).isoformat()
schreibe_kurse([vorvortag], SYMBOLE[:3])
erg2 = ph.schreibe_tageswert(conn, datum=vorvortag, watchlist=watchlist)
pruefe("B1 Trueemmertag wird NICHT geschrieben", erg2.get("geschrieben") is False,
       f"Abdeckung {erg2.get('abdeckung', 0)*100:.0f} %")
pruefe("B2 kein wert_eur zurueckgegeben", erg2.get("wert_eur") is None)
pruefe("B3 Reihe unveraendert", len(db.get_portfolio_wert_historie(conn)) == 1)

# Genau an der Schwelle: 8 von 10 = 80 % muss durchgehen
tag80 = (heute - timedelta(days=3)).isoformat()
schreibe_kurse([tag80], SYMBOLE[:8])
erg3 = ph.schreibe_tageswert(conn, datum=tag80, watchlist=watchlist)
pruefe("B4 genau 80 % Abdeckung wird geschrieben", erg3.get("geschrieben") is True,
       f"{erg3.get('abdeckung', 0)*100:.0f} %")

# 7 von 10 = 70 % muss fallen
tag70 = (heute - timedelta(days=4)).isoformat()
schreibe_kurse([tag70], SYMBOLE[:7])
erg4 = ph.schreibe_tageswert(conn, datum=tag70, watchlist=watchlist)
pruefe("B5 70 % Abdeckung faellt durch", erg4.get("geschrieben") is False,
       f"{erg4.get('abdeckung', 0)*100:.0f} %")

print("\nC) DER ECHTE FALL AUS DEM BETRIEB")
# 1 von 33 (05.08.) und 14 von 33 (06.08.) - beide muessen abgelehnt werden
for name, anzahl in (("05.08.: 1 von 33", 1), ("06.08.: 14 von 33", 14)):
    ph_symbole = [f"P{i}" for i in range(33)]
    for s in ph_symbole:
        db.upsert_holding(conn, s, 1.0)
    wl = [SimpleNamespace(symbol=s, coingecko_id=None, ist_cash_aequivalent=False)
          for s in ph_symbole]
    tag = (heute - timedelta(days=10 + anzahl)).isoformat()
    schreibe_kurse([tag], ph_symbole[:anzahl])
    e = ph.schreibe_tageswert(conn, datum=tag, watchlist=wl)
    pruefe(f"C {name} abgelehnt", e.get("geschrieben") is False,
           f"Abdeckung {e.get('abdeckung', 0)*100:.1f} %")
    for s in ph_symbole:
        conn.execute("DELETE FROM holdings WHERE symbol = ?", (s,))
    conn.commit()

print("\nD) FX-VERWURF WIRD EINMAL GEMELDET, NICHT ZWANZIGMAL")
# ANLASS (07.08., Nutzer-Fund im Log): EIN verworfener Tag erzeugte zwanzig
# identische WARNING-Zeilen in vier Minuten, weil die Ableitung bei jeder
# Bewertung neu laeuft. In diesem Takt ersaeuft jeder echte Fund.
import io as _io
import logging

import agent.portfolio_historie as _ph

_ph._FX_VERWURF_GEMELDET.clear()
_TAG = "2026-08-06"
for i in range(35):
    # Ein Ausreisser plus eine gespaltene Gruppe -> Interquartilsabstand ueber
    # der Grenze, also ein echter Verwurf.
    quot = 0.86 + (0.05 if i == 0 else 0.0) + (0.02 if i < 12 else 0.0)
    for waehrung, kurs in (("USD", 100.0), ("EUR", quot * 100.0)):
        conn.execute(
            "INSERT OR REPLACE INTO price_history_ohlc "
            "(symbol,date,currency,open,high,low,close,volume,fetched_at) "
            "VALUES (?,?,?,?,?,?,?,0,?)",
            (f"FX{i}", _TAG, waehrung, kurs, kurs, kurs, kurs, heute.isoformat()))
conn.commit()

_puffer = _io.StringIO()
_h = logging.StreamHandler(_puffer)
_h.setLevel(logging.WARNING)
_log = logging.getLogger("agent.portfolio_historie")
_log.addHandler(_h)
_log.setLevel(logging.DEBUG)

for _ in range(20):
    _kurse, _verworfen = _ph.tages_fx_kurse(conn)
_zeilen = [z for z in _puffer.getvalue().splitlines() if "FX-Ableitung" in z]
pruefe("D1 zwanzig Aufrufe erzeugen EINE Warnzeile", len(_zeilen) == 1,
       f"{len(_zeilen)} Zeilen")
pruefe("D2 der Verwurf steht weiter im Rueckgabewert - der Export verliert ihn nicht",
       _TAG in _verworfen, str(_verworfen))
pruefe("D3 die Wiederholungen werden gezaehlt, nicht verschluckt",
       max(_ph._FX_VERWURF_GEMELDET.values()) == 20,
       str(dict(_ph._FX_VERWURF_GEMELDET)))

# Aendert sich die Lage WIRKLICH, muss wieder gemeldet werden - sonst waere aus
# der Entlastung eine Vertuschung geworden.
_puffer.truncate(0)
_puffer.seek(0)
for i in range(12, 24):
    quot = 0.86 + 0.03
    conn.execute(
        "UPDATE price_history_ohlc SET open=?, high=?, low=?, close=? "
        "WHERE symbol=? AND date=? AND currency='EUR'",
        (quot * 100, quot * 100, quot * 100, quot * 100, f"FX{i}", _TAG))
conn.commit()
_ph.tages_fx_kurse(conn)
_neue = [z for z in _puffer.getvalue().splitlines() if "FX-Ableitung" in z]
pruefe("D4 geaenderte Lage wird wieder gemeldet", len(_neue) == 1,
       f"{len(_neue)} Zeilen - Stummschaltung gilt nur fuer dieselbe Aussage")
_log.removeHandler(_h)

print("\n" + ("ALLE TESTS BESTANDEN" if not fehler else f"FEHLER: {fehler}"))
conn.close()
