"""P9 Statusseite (10.10.2026, Plan_Asset_Lebenszyklus_14_09.md G-N/G-O) - Pruefstand auf einer KOPIE (nie die Produktion).

    python Basisinfos/Rechenkern_02_10/p9_pruefstand.py <Pruefverzeichnis>

Das Pruefverzeichnis traegt Kopien vom NB (tradinginfotool.db, regel0_signale.db, regel0_modelle, Kursdateien). Die Seite wird mit
``agent.betriebslage.DATEN = <Pruefverzeichnis>`` und einer ``mode=ro``-Verbindung gebaut.

  P1 jede Karte der Betriebslage gefuellt (Feld nicht None), abgeleitet aus RemoteStatus ab `betrieb`
  P2 warmer Aufbau < Warnschwelle (1,0 s); kalter Aufbau ausgewiesen
  P3 Flask: Seite 200, /api/status 200 mit allen Feldern, ohne Token 401, POST ohne Token 401
  P4 entfallene Karten (G-N) sind weg, umgehaengte da; Getter bleiben im Code
  P5 Pruefsumme der Kopie UND der Desktop-Standard-DB unveraendert
  P6 Grundfunktionen (GF1): Portfolio, Preise, CoinGecko, Gemini, API-Status, Knoepfe, Fehler, Z-3 weiter auf der Seite
"""
import dataclasses
import hashlib
import os
import sqlite3
import sys
import time
from pathlib import Path

WURZEL = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, WURZEL)
os.chdir(WURZEL)
D = os.path.abspath(sys.argv[1])
import agent.betriebslage as BL  # noqa: E402

BL.DATEN = D
import config as C  # noqa: E402
import remote.status as RS  # noqa: E402
from remote.server import create_app  # noqa: E402

ERG = []


def pruefe(k, ok, text):
    ERG.append(ok)
    print("%-3s %-9s %s" % (k, "bestanden" if ok else "FEHLER", text))


def summe(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


KOPIE = os.path.join(D, "tradinginfotool.db")
STANDARD = os.path.join(WURZEL, "data", "tradinginfotool.db")
vor = {p: summe(p) for p in (KOPIE, STANDARD) if os.path.exists(p)}


def ro():
    c = sqlite3.connect("file:%s?mode=ro" % KOPIE.replace("\\", "/"), uri=True, check_same_thread=False)
    c.row_factory = sqlite3.Row
    return c


felder = [f.name for f in dataclasses.fields(RS.RemoteStatus)]
neu = felder[felder.index("betrieb"):]
RS.leere_aggregat_cache()
c = ro()
try:
    a = time.monotonic()
    RS.build_status(c, C.get_watchlist(), Path(D) / "keins.log")
    kalt = time.monotonic() - a
    a = time.monotonic()
    st = RS.build_status(c, C.get_watchlist(), Path(D) / "keins.log").to_dict()
    warm = time.monotonic() - a
finally:
    c.close()
leer = [f for f in neu if st.get(f) is None]
pruefe("P1", not leer and len(neu) >= 8, "%d Karten (%s), leer: %s" % (len(neu), ", ".join(neu), leer))
pruefe("P2", warm < RS._BUILD_STATUS_WARNSCHWELLE_SEKUNDEN, "warm %.2f s, kalt %.2f s (Schwelle %.1f s; kalt enthaelt die Erst-Importe)"
       % (warm, kalt, RS._BUILD_STATUS_WARNSCHWELLE_SEKUNDEN))

app = create_app(coingecko_client=None, kraken_client=None, groq_client=None, conn_factory=ro, watchlist_provider=C.get_watchlist,
                 fred_api_key=None, access_token="pruef", log_path=Path(D) / "keins.log")
cl = app.test_client()
r1 = cl.get("/?token=pruef")
r2 = cl.get("/api/status", headers={"X-Access-Token": "pruef"})
r3 = cl.get("/api/status")
r4 = cl.post("/api/marktscan")
js = r2.get_json() or {}
pruefe("P3", r1.status_code == 200 and r2.status_code == 200 and r3.status_code == 401 and r4.status_code == 401
       and all(f in js for f in neu), "Seite %s · Status %s · ohne Token %s · POST ohne Token %s" % (
           r1.status_code, r2.status_code, r3.status_code, r4.status_code))

html = r1.get_data(as_text=True)
weg = ["ALTE KETTE (seit dem Schnitt ohne Aufrufer)", 'id="regime-status-card"', 'id="parameter-overview-card"',
       "section-badge\">A<", "section-badge\">B<", "section-badge\">C<", 'id="budget-total"']
da = ['id="marktscan-erfolgsquote"', 'id="ausstieg-empfehlungen"', '<details class="ruht">', 'id="themenfeld-erfolg-card"',
      'id="wartende-themen-card"', 'id="hedge-card"']
getter = ["_get_budget_heute", "_get_regime_status", "_get_parameter_overview", "_get_rollen_budget"]
pruefe("P4", not [w for w in weg if w in html] and all(x in html for x in da) and all(hasattr(RS, g) for g in getter),
       "noch da: %s · fehlt: %s" % ([w for w in weg if w in html], [x for x in da if x not in html]))

nach = {p: summe(p) for p in vor}
pruefe("P5", vor == nach, "Pruefsumme Kopie %s · Desktop-Standard-DB %s" % (
    "gleich" if vor.get(KOPIE) == nach.get(KOPIE) else "GEAENDERT",
    "gleich" if vor.get(STANDARD) == nach.get(STANDARD) else ("GEAENDERT" if STANDARD in vor else "nicht vorhanden")))

gf = ['id="portfolio-value"', 'id="stale-count"', 'id="coingecko-quota"', 'id="llm-kontingent"', 'id="api-health-llm"',
      'id="btn-prices"', 'id="btn-marktscan"', "restartApp()", 'id="errors-card"', 'id="z3-card"']
felder_gf = ["portfolio_value_eur", "prices", "coingecko_quota", "llm_kontingent", "api_health", "recent_errors", "jobs_running",
             "z3_und_bewertung", "marktscan_erfolgsquote", "ausstiegs_empfehlungen", "rollen_budget"]
pruefe("P6", all(x in html for x in gf) and all(f in js for f in felder_gf),
       "fehlt im HTML: %s · im Status: %s" % ([x for x in gf if x not in html], [f for f in felder_gf if f not in js]))

print()
print("%d von %d bestanden" % (sum(ERG), len(ERG)))
