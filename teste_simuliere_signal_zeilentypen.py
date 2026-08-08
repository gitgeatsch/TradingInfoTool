"""Regressionstest: simuliere_signal() muss mit sqlite3.Row UND mit dict laufen.

ANLASS (06.08., Betriebsfund). Die Plausibilitaetsschranke gegen den
Instrumenten-Verwechsler (Commit 185d4f3, 09:17) benutzte `p.get("close")`.
`lade_kursreihen()` liefert aber **sqlite3.Row**, und Row kennt kein .get() -
seit 09:17 warf JEDER Aufruf einen AttributeError. Betroffen waren alle drei
Produktivpfade: compute_systemguete(), basislinie_ziel_anteil() und
compute_crv_breakeven_baender() - und damit auch der CRV-Baender-FAKT, der am
selben Tag in alle sechs Prompts eingebaut wurde.

Gefunden wurde es erst im Log, weil jeder Aufrufer den Fehler abfaengt
(`_safe()` auf der Remote-Seite, try/except im Export). Fail-soft hat die
Anwendung am Leben gehalten und den Defekt versteckt.

Der Test bildet deshalb GENAU die Ladeform der Produktion nach - er ruft
lade_kursreihen() gegen eine echte SQLite-Verbindung auf, statt Zeilen
nachzubauen. Ein Test mit selbstgebauten dicts haette den Fehler nicht
gefunden; das war die eigentliche Luecke.
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
TAGE = [(heute - timedelta(days=29 - i)).isoformat() for i in range(30)]

def schreibe(symbol, closes):
    db.upsert_ohlc_points(conn, [
        OhlcPoint(symbol=symbol, currency="USD", date=d, open=c, high=c * 1.02,
                  low=c * 0.98, close=c, volume=100.0, fetched_at=JETZT)
        for d, c in zip(TAGE, closes)])

schreibe("TESTLONG", [100.0 + i for i in range(30)])       # steigt
schreibe("TESTSKALA", [6.30] * 30)                          # Futures-Niveau

from agent.krypto.backward_tracking import lade_kursreihen, simuliere_signal

reihen = lade_kursreihen(conn)
import sqlite3
pruefe("A1 lade_kursreihen liefert sqlite3.Row (wie in der Produktion)",
       isinstance(reihen["TESTLONG"][0], sqlite3.Row),
       type(reihen["TESTLONG"][0]).__name__)

# Zonenformat wie _zonen_absolut() es liefert: risiko + ist_short, nicht "richtung"
zonen = {"entry": 100.0, "stop": 95.0, "ziel": 115.0, "risiko": 5.0, "ist_short": False}
sim = simuliere_signal(zonen, reihen["TESTLONG"], TAGE[0], 10)
pruefe("A2 Simulation laeuft mit sqlite3.Row (war der Absturz)", sim is not None,
       str(sim.get("ergebnis") if isinstance(sim, dict) else sim)[:60])

# Gleiche Daten als dict - beide Formen muessen dasselbe liefern
als_dict = [{k: r[k] for k in r.keys()} for r in reihen["TESTLONG"]]
sim_d = simuliere_signal(zonen, als_dict, TAGE[0], 10)
pruefe("A3 dict liefert dasselbe Ergebnis wie Row", sim == sim_d)

# Die Schranke selbst muss weiter greifen - Entry 34,63 gegen eine Reihe bei 6,30
zonen_skala = {"entry": 34.63, "stop": 36.00, "ziel": 31.50, "risiko": 1.37, "ist_short": True}
sim_s = simuliere_signal(zonen_skala, reihen["TESTSKALA"], TAGE[0], 10)
pruefe("A4 Plausibilitaetsschranke greift weiterhin (Faktor 5,5)", sim_s is None)

# Knapp unterhalb der Schranke muss weiterhin bewertet werden
schreibe("TESTKNAPP", [40.0] * 30)
reihen = lade_kursreihen(conn)
sim_k = simuliere_signal({"entry": 100.0, "stop": 95.0, "ziel": 115.0,
                          "risiko": 5.0, "ist_short": False},
                         reihen["TESTKNAPP"], TAGE[0], 10)
pruefe("A5 Faktor 2,5 wird weiterhin bewertet", sim_k is not None)

# Ein fehlender Schlusskurs darf nicht abstuerzen. In der DB ist die Spalte
# NOT NULL - der urspruengliche .get()-Aufruf war also doppelt falsch: er
# benutzte eine Methode, die es nicht gibt, fuer einen Fall, den es nicht gibt.
# Ueber die dict-Form ist er trotzdem erreichbar (z.B. aus einem Analyseskript).
mit_luecke = [dict(x) for x in als_dict]
mit_luecke[0]["close"] = None
try:
    sim_n = simuliere_signal(zonen, mit_luecke, TAGE[0], 10)
    pruefe("A6 fehlender Schlusskurs ohne Absturz", True, "erster gueltiger Kurs wird genommen")
except Exception as exc:
    pruefe("A6 fehlender Schlusskurs ohne Absturz", False, f"{type(exc).__name__}: {exc}")

# Die beiden anderen Produktivpfade, die dieselben Zeilen durchreichen
from agent.krypto.backward_tracking import basislinie_ziel_anteil
try:
    anteil = basislinie_ziel_anteil(reihen, stop_rel=0.05, crv=2.0, ist_short=False,
                                    horizont=10)
    pruefe("A7 basislinie_ziel_anteil laeuft mit Row", True, str(anteil)[:60])
except Exception as exc:
    pruefe("A7 basislinie_ziel_anteil laeuft mit Row", False, f"{type(exc).__name__}: {exc}")

# --- B) Balkendichte-Kennzeichnung (09.08., Mappe Kapitel 9 Stufe 1) ---------
#
# Der Bewerter nimmt Tageskerzen an. Auf einer Reihe mit 4-Tage-Balken ist
# "Stop schlaegt Ziel am selben Tag" keine konservative Konvention mehr,
# sondern ein Muenzwurf - gemessen: 100,0 % Reproduktion auf dichten Reihen,
# 83,3 % auf duennen. Das Feld macht diese Grenze fuer jeden Auswerter sichtbar.
#
# WICHTIG (Methodik-Nachtrag 09.08., Punkt 5): der Test muss gegen den Fall
# fahren, den er erkennen soll. Ein Feld, das immer None oder immer 1.0
# lieferte, wuerde B1 bestehen - deshalb prueft B2 die Gegenrichtung an einer
# echt duennen Reihe, und B3 haelt fest, dass sich die beiden unterscheiden.
DUENNE_TAGE = [(heute - timedelta(days=4 * (7 - i))).isoformat() for i in range(8)]
db.upsert_ohlc_points(conn, [
    OhlcPoint(symbol="TESTDUENN", currency="USD", date=d, open=c, high=c * 1.02,
              low=c * 0.98, close=c, volume=100.0, fetched_at=JETZT)
    for d, c in zip(DUENNE_TAGE, [100.0 + i for i in range(8)])])
reihen = lade_kursreihen(conn)

sim_dicht = simuliere_signal(zonen, reihen["TESTLONG"], TAGE[0], 10)
pruefe("B1 dichte Reihe wird als 1,0 Tage gekennzeichnet",
       sim_dicht is not None and sim_dicht.get("balkenabstand_median") == 1.0,
       str(None if sim_dicht is None else sim_dicht.get("balkenabstand_median")))

sim_duenn = simuliere_signal(zonen, reihen["TESTDUENN"], DUENNE_TAGE[0], 6)
pruefe("B2 duenne Reihe wird als 4,0 Tage gekennzeichnet",
       sim_duenn is not None and sim_duenn.get("balkenabstand_median") == 4.0,
       str(None if sim_duenn is None else sim_duenn.get("balkenabstand_median")))

pruefe("B3 beide Reihen sind unterscheidbar (Feld ist keine Konstante)",
       sim_dicht is not None and sim_duenn is not None
       and sim_dicht["balkenabstand_median"] != sim_duenn["balkenabstand_median"])

# Einzelner Balken: kein Abstand berechenbar - None statt einer erfundenen Zahl
sim_einzel = simuliere_signal(zonen, [dict(reihen["TESTLONG"][0])], TAGE[0], 10,
                              voller_horizont_noetig=False)
pruefe("B4 einzelner Balken liefert None statt einer erfundenen Dichte",
       sim_einzel is not None and sim_einzel.get("balkenabstand_median") is None,
       str(None if sim_einzel is None else sim_einzel.get("balkenabstand_median")))

# --- C) Die Skalen-Schranke gilt jetzt auch im LIVE-Pfad (09.08.) ------------
#
# Die Schranke vom 06.08. sass nur in simuliere_signal() - also im
# SIMULATIONS-Pfad. Der Live-Tracker, der die Ergebnisse in die Datenbank
# schreibt, hatte keine. Genau darueber kam OD7C #2361 mit +20,37 R in die
# Systemguete: Einstieg 34,63, bewertet gegen die Kupfer-Futures-Reihe bei 6,30.
#
# A4 oben prueft den Simulations-Pfad, C1 hier den Live-Pfad. Beide brauchen es
# einzeln - dass der eine geschuetzt ist, sagt nichts ueber den anderen.
from agent.krypto.backward_tracking import lade_ohlc_auf_signal_skala

# TESTSKALA liegt bei 6,30 (siehe oben). Ein Signal mit Einstieg 34,63 gehoert
# zu einem anderen Instrument.
rows_falsch = lade_ohlc_auf_signal_skala(conn, "TESTSKALA", 34.63, TAGE[0])
pruefe("C1 Live-Pfad verweigert die Bewertung bei Skalenbruch (Faktor 5,5)",
       rows_falsch == [], f"{len(rows_falsch)} Zeilen zurueckgegeben")

# GEGENPROBE: bei passender Skala muessen die Daten ankommen. Ohne sie koennte
# die Funktion einfach immer [] liefern und C1 bestuende trotzdem.
rows_passend = lade_ohlc_auf_signal_skala(conn, "TESTSKALA", 6.50, TAGE[0])
pruefe("C2 Gegenprobe: bei passender Skala kommen die Daten durch",
       len(rows_passend) > 0, f"{len(rows_passend)} Zeilen")

# Faktor 2,5 muss weiterhin durchgehen - echte Gaps und Splits sollen
# auswertbar bleiben, nur die Groessenordnungs-Verwechslung faellt heraus.
rows_knapp = lade_ohlc_auf_signal_skala(conn, "TESTSKALA", 6.30 * 2.5, TAGE[0])
pruefe("C3 Faktor 2,5 bleibt auswertbar (Gaps/Splits nicht abwuergen)",
       len(rows_knapp) > 0, f"{len(rows_knapp)} Zeilen")

# Ohne Einstieg kann nichts geprueft werden - dann darf die Funktion nicht
# stillschweigend alles verwerfen.
rows_ohne = lade_ohlc_auf_signal_skala(conn, "TESTSKALA", None, TAGE[0])
pruefe("C4 ohne Einstiegspreis wird nicht verworfen", len(rows_ohne) > 0,
       f"{len(rows_ohne)} Zeilen")

# Und alle sechs Checker muessen die Wache benutzen, nicht nur einer - dieselbe
# Falle wie bei der Zonenkante, wo zunaechst nur einer von drei umgestellt war.
import pathlib as _pl

for _datei, _erwartet in (("agent/krypto/backward_tracking.py", 3),
                          ("agent/krypto/hebel_backward_tracking.py", 3)):
    _text = _pl.Path(_datei).read_text(encoding="utf-8")
    _n = _text.count("lade_ohlc_auf_signal_skala(\n")
    pruefe(f"C5 {_datei} holt OHLC ueber die Wache", _n >= _erwartet,
           f"{_n} von {_erwartet} Stellen")

print("\n" + ("ALLE TESTS BESTANDEN" if not fehler else f"FEHLER: {fehler}"))
conn.close()
raise SystemExit(1 if fehler else 0)
