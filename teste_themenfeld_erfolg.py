"""Prueft das Erfolgsmaß je Themenfeld (07.08.2026, Schritt 5, G-2).

DER BEFUND, DER DIE BAUART BESTIMMT HAT - gemessen am Notebook-Export vom
07.08., vor dem ersten Zeilencode:

    2795 Spot-Signale, davon    10 aufgeloest.
    1759 Hebel-Signale, davon   91 aufgeloest.
    Von diesen 101 gehoert **kein einziges** zu einem Themenfeld.

Eine "Systemguete je Hauptgruppe" waere heute also eine Tabelle aus leeren
Zellen - und saehe dabei aus wie ein funktionierendes Instrument. Gemessen wird
stattdessen die Richtungsaussage auf einen Korb.

Die Kursreihen werden hier SIMULIERT, nicht abgewartet: ohne sie liesse sich
nur der Nicht-Messbar-Zweig testen, und genau das waere der Fehler, den die
stehende Vorgabe verbietet ("die Daten die wir nicht haben simulieren und
testen wir").
"""
import pathlib
import tempfile
from datetime import datetime, timedelta, timezone

import config
import database.db as db
from database.models import These

fehler = []
def pruefe(name, ok, info=""):
    print(("  OK   " if ok else "  FEHL ") + name + ("  " + info if info else ""))
    if not ok:
        fehler.append(name)

db.DB_PATH = pathlib.Path(tempfile.mkdtemp()) / "test.db"
conn = db.get_connection()
db.init_db(conn)

JETZT = datetime(2026, 8, 7, 12, 0, tzinfo=timezone.utc)
GESETZT = JETZT - timedelta(days=40)

from agent.themenfeld_erfolg import (
    MIN_TAGE_FUER_URTEIL,
    SCHWELLE_TREFFER_PROZENT,
    compute_themenfeld_erfolg,
)


def these(hauptgruppe, unterkategorie, richtung, tage_alt=40):
    db.create_these(conn, These(
        hauptgruppe=hauptgruppe, unterkategorie=unterkategorie, richtung=richtung,
        begruendung="Test", gesetzt_am=(JETZT - timedelta(days=tage_alt)).isoformat(),
        pruef_mechanismus="m2_liquiditaet"))


def kursreihe(symbol, start_preis, end_preis, tage=45):
    """Lineare Reihe - fuer eine Renditemessung reicht Anfang und Ende, aber
    die Funktion verlangt mindestens zwei Punkte je Symbol."""
    schritt = (end_preis - start_preis) / max(1, tage - 1)
    for i in range(tage):
        tag = (JETZT - timedelta(days=tage - 1 - i)).date().isoformat()
        conn.execute(
            "INSERT OR REPLACE INTO price_history_ohlc "
            "(symbol, date, currency, open, high, low, close, volume, fetched_at) "
            "VALUES (?,?,'USD',?,?,?,?,0,?)",
            (symbol, tag, start_preis + schritt * i, start_preis + schritt * i,
             start_preis + schritt * i, start_preis + schritt * i, JETZT.isoformat()))
    conn.commit()


print("A) DER GRUND FUER DIE BAUART - Absicherung bekommt keine Ueberrendite")
these("absicherung", None, "aktiv")
e = compute_themenfeld_erfolg(conn, JETZT)["thesen"][0]
pruefe("A1 Absicherung wird nicht ueber Ueberrendite gemessen", e["messbar"] is False)
pruefe("A2 mit Verweis auf das richtige Werkzeug",
       "compute_hedge_wirksamkeit" in e["grund"], e["grund"][:60])
pruefe("A3 kein erfundenes Urteil", e["treffer"] is None)

print("\nB) NICHT MESSBAR WIRD ALS SOLCHES AUSGEWIESEN, nicht als Null")
these("industriemetalle", "industriemetalle_diversifiziert", "neutral")
res = compute_themenfeld_erfolg(conn, JETZT)
im = next(t for t in res["thesen"] if t["hauptgruppe"] == "industriemetalle")
pruefe("B1 Kategorie ohne Kursreihe ist nicht messbar", im["messbar"] is False)
pruefe("B2 Grund nennt die Zahlen", "Kursreihe" in im["grund"], im["grund"][:60])
pruefe("B3 die Wirkungskette steht trotzdem da",
       im["wirkungskette"]["assets_gesamt"] >= 1 and im["wirkungskette"]["assets_mit_kursreihe"] == 0,
       str(im["wirkungskette"]))

print("\nC) DER MESSBARE FALL - Uebergewichten getroffen")
# Energie: OD7L steigt kraeftig. Vergleichskorb aus anderen Themen faellt.
these("energie", None, "uebergewichten")
kursreihe("OD7L", 100.0, 130.0)          # +30 %
kursreihe("ARTINT", 100.0, 100.0)        # technologie_ki, flach
kursreihe("SEMICON", 100.0, 95.0)        # technologie_ki, -5 %
res = compute_themenfeld_erfolg(conn, JETZT)
en = next(t for t in res["thesen"] if t["hauptgruppe"] == "energie")
pruefe("C1 messbar", en["messbar"] is True, en.get("grund") or "")
# Die Reihe laeuft ueber 45 Tage (+30 %), die These steht erst seit 40 Tagen.
# Gemessen wird ab GESETZT_AM, nicht ab Reihenbeginn - sonst schriebe man der
# These Bewegung gut, die vor ihr lag.
pruefe("C2 gemessen ab gesetzt_am, nicht ab Reihenbeginn",
       25.0 < en["korb_rendite_prozent"] < 28.0,
       f"{en['korb_rendite_prozent']} % statt der vollen 30 % der Reihe")
pruefe("C3 Vergleichskorb ist NICHT die eigene Kategorie",
       "OD7L" not in en["getragen_von"] or en["vergleich_rendite_prozent"] < 1.0,
       f"Vergleich {en['vergleich_rendite_prozent']} %")
pruefe("C4 Ueberrendite positiv", en["ueberrendite_prozentpunkte"] > 25,
       f"{en['ueberrendite_prozentpunkte']} pp")
pruefe("C5 Uebergewichten gilt als getroffen", en["treffer"] is True)
pruefe("C6 getragen_von nennt die Symbole - eine Korbzahl aus einem Wert ist "
       "etwas anderes als eine aus zwoelf", en["getragen_von"] == ["OD7L"],
       str(en["getragen_von"]))

print("\nD) DIE GEGENRICHTUNG - Uebergewichten daneben")
conn.execute("DELETE FROM thesen"); conn.commit()
these("energie", None, "uebergewichten")
kursreihe("OD7L", 100.0, 80.0)           # -20 %
kursreihe("ARTINT", 100.0, 110.0)        # +10 %
kursreihe("SEMICON", 100.0, 110.0)       # +10 %
res = compute_themenfeld_erfolg(conn, JETZT)
en = res["thesen"][0]
pruefe("D1 Ueberrendite negativ", en["ueberrendite_prozentpunkte"] < -25,
       f"{en['ueberrendite_prozentpunkte']} pp")
pruefe("D2 als Fehlschlag ausgewiesen", en["treffer"] is False)
pruefe("D3 in der Bilanz gezaehlt", res["fehlschlaege"] == 1 and res["treffer"] == 0)

print("\nE) MEIDEN dreht die Bewertung um")
conn.execute("DELETE FROM thesen"); conn.commit()
these("energie", None, "meiden")
res = compute_themenfeld_erfolg(conn, JETZT)
pruefe("E1 dieselbe Unterperformance ist bei 'meiden' ein TREFFER",
       res["thesen"][0]["treffer"] is True,
       "-20 % gegen +10 % - genau das war die Aussage")

print("\nF) WAS KEIN URTEIL BEKOMMT")
conn.execute("DELETE FROM thesen"); conn.commit()
these("energie", None, "neutral")
res = compute_themenfeld_erfolg(conn, JETZT)
pruefe("F1 'neutral' trifft keine Aussage - also auch kein Treffer",
       res["thesen"][0]["treffer"] is None and res["thesen"][0]["messbar"] is True,
       "die Zahl steht trotzdem da")
pruefe("F2 und zaehlt nicht in die Bilanz", res["anzahl_mit_urteil"] == 0)

conn.execute("DELETE FROM thesen"); conn.commit()
these("energie", None, "uebergewichten", tage_alt=3)
res = compute_themenfeld_erfolg(conn, JETZT)
pruefe("F3 zu junge These bekommt kein Urteil",
       res["thesen"][0]["messbar"] is False and "Tage" in res["thesen"][0]["grund"],
       res["thesen"][0]["grund"][:50])

print("\nG) DIE SCHWELLE GEGEN ZUFALLSTREFFER")
conn.execute("DELETE FROM thesen"); conn.commit()
these("energie", None, "uebergewichten")
kursreihe("OD7L", 100.0, 101.0)          # +1 %
kursreihe("ARTINT", 100.0, 100.0)
kursreihe("SEMICON", 100.0, 100.0)
res = compute_themenfeld_erfolg(conn, JETZT)
pruefe("G1 ein Prozentpunkt Unterschied ist 'unentschieden', kein Treffer",
       res["thesen"][0]["treffer"] == "unentschieden",
       f"{res['thesen'][0]['ueberrendite_prozentpunkte']} pp bei Schwelle "
       f"{SCHWELLE_TREFFER_PROZENT}")
pruefe("G2 zaehlt weder als Treffer noch als Fehlschlag",
       res["treffer"] == 0 and res["fehlschlaege"] == 0)

print("\nH) DIE WIRKUNGSKETTE - kommt die These bei einem Asset an?")
spalten = {r[1] for r in conn.execute("PRAGMA table_info(signals)")}
pflicht = {"symbol": "OD7L", "created_at": JETZT.isoformat(), "action": "KAUFEN",
           "confidence_pct": 70, "short_reasoning": "T",
           "outcome_status": "take_profit_erreicht"}
# Alle uebrigen NOT-NULL-Spalten ohne Vorgabewert mit 0 fuellen - der Test
# braucht nur EINE Signalzeile, nicht ein realistisches Signal.
for r in conn.execute("PRAGMA table_info(signals)"):
    if r[3] and r[4] is None and r[1] not in pflicht and r[1] != "id":
        pflicht[r[1]] = 0
conn.execute(
    f"INSERT INTO signals ({', '.join(pflicht)}) "
    f"VALUES ({', '.join('?' * len(pflicht))})", tuple(pflicht.values()))
conn.commit()
res = compute_themenfeld_erfolg(conn, JETZT)
wk = res["thesen"][0]["wirkungskette"]
pruefe("H1 Signale des Themenfelds gezaehlt", wk["signale_gesamt"] == 1, str(wk))
pruefe("H2 aufgeloeste getrennt", wk["aufgeloest"] if False else wk["signale_aufgeloest"] == 1)
pruefe("H3 Assets mit Signal gezaehlt", wk["assets_mit_signal"] == 1)
pruefe("H4 und die Assets OHNE Kursreihe bleiben sichtbar",
       wk["assets_gesamt"] > wk["assets_mit_kursreihe"],
       f"{wk['assets_gesamt']} Assets, {wk['assets_mit_kursreihe']} mit Reihe - "
       "genau das ist die Engstelle")

print("\nJ) WELCHER KORB FEHLT, MUSS DASTEHEN")
# "Zu wenige Kurspunkte" allein laesst offen, ob die Kategorie oder der
# Vergleichsmassstab leer ist - und das sind verschiedene Probleme: das eine
# betrifft eine Kategorie, das andere blockiert JEDE Messung.
conn.execute("DELETE FROM thesen"); conn.execute("DELETE FROM price_history_ohlc")
conn.commit()
these("energie", None, "uebergewichten")
res = compute_themenfeld_erfolg(conn, JETZT)
pruefe("J1 ganz ohne Kursreihe greift die SPEZIFISCHERE Meldung zuerst",
       "kein Asset dieser Kategorie hat eine Kursreihe" in res["thesen"][0]["grund"],
       "die Reihenfolge der Pruefungen ist Absicht - die genauere Aussage gewinnt")

# Der "weder ... noch"-Zweig braucht Reihen, die es GIBT, die aber vor dem
# Setzen der These enden. Genau der Fall, in dem eine Kursreihe vorhanden
# aussieht und trotzdem nichts hergibt.
def alte_kursreihe(symbol, preis, endet_vor_tagen=60):
    for i in range(5):
        tag = (JETZT - timedelta(days=endet_vor_tagen + 5 - i)).date().isoformat()
        conn.execute(
            "INSERT OR REPLACE INTO price_history_ohlc "
            "(symbol, date, currency, open, high, low, close, volume, fetched_at) "
            "VALUES (?,?,'USD',?,?,?,?,0,?)",
            (symbol, tag, preis, preis, preis, preis, JETZT.isoformat()))
    conn.commit()

conn.execute("DELETE FROM price_history_ohlc"); conn.commit()
alte_kursreihe("OD7L", 100.0)
alte_kursreihe("ARTINT", 100.0)
res = compute_themenfeld_erfolg(conn, JETZT)
pruefe("J1b veraltete Reihen auf beiden Seiten: beide Koerbe genannt",
       "weder die Kategorie noch der Vergleichskorb" in res["thesen"][0]["grund"],
       res["thesen"][0]["grund"][:70])

conn.execute("DELETE FROM price_history_ohlc"); conn.commit()

# Nur der Vergleichskorb hat Daten -> die Kategorie ist das Problem
kursreihe("ARTINT", 100.0, 110.0)
kursreihe("SEMICON", 100.0, 110.0)
res = compute_themenfeld_erfolg(conn, JETZT)
pruefe("J2 nur die Kategorie leer: das steht auch so da",
       "Kursreihe" in res["thesen"][0]["grund"], res["thesen"][0]["grund"][:60])

# Nur die Kategorie hat Daten -> der Vergleichskorb blockiert ALLES
conn.execute("DELETE FROM price_history_ohlc"); conn.commit()
kursreihe("OD7L", 100.0, 120.0)
res = compute_themenfeld_erfolg(conn, JETZT)
pruefe("J3 leerer Vergleichskorb wird als ALLGEMEINES Problem markiert",
       "blockiert JEDE" in res["thesen"][0]["grund"], res["thesen"][0]["grund"][:70])

print("\nI) LEERER ZUSTAND")
conn.execute("DELETE FROM thesen"); conn.commit()
leer = compute_themenfeld_erfolg(conn, JETZT)
pruefe("I1 keine Thesen ohne Absturz",
       leer["anzahl_thesen"] == 0 and leer["treffer"] == 0)
pruefe("I2 Lesehilfe erklaert, warum nicht die Systemguete gemessen wird",
       "101" in leer["lesehilfe"] and "Systemguete" in leer["lesehilfe"])

print("\n" + ("ALLE TESTS BESTANDEN" if not fehler else f"FEHLER: {fehler}"))
conn.close()
