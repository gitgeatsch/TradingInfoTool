"""Prueft die Vorschau auf wartende Themen-Vorschlaege (07.08.2026, Schritt 5).

ANLASS. Am 07.08. standen 14 von 16 Vorschlaegen auf "beobachtung" - und weder
in der GUI noch auf der Uebersichtsseite war erkennbar, dass darunter ein
KI-Vorschlag seit dem 25.07. laeuft und am 24.08. reif wird. Erst die Datierung
von Hand hat es gezeigt. **Ein Vorlauf, den niemand sieht, ist keiner.**

Die wichtigere Zahl ist nicht "wie viele warten", sondern **wie viele am selben
Tag reif werden** - denn dann entscheidet sich, ob das Budget reicht.
"""
import pathlib
import tempfile
from datetime import datetime, timedelta, timezone

import database.db as db

fehler = []
def pruefe(name, ok, info=""):
    print(("  OK   " if ok else "  FEHL ") + name + ("  " + info if info else ""))
    if not ok:
        fehler.append(name)

db.DB_PATH = pathlib.Path(tempfile.mkdtemp()) / "test.db"
conn = db.get_connection()
db.init_db(conn)

JETZT = datetime(2026, 8, 7, 12, 0, tzinfo=timezone.utc)

def lege_vorschlag_an(hauptgruppe, unterkategorie, mechanismus, tage_her, richtung="uebergewichten"):
    seit = (JETZT - timedelta(days=tage_her)).isoformat()
    conn.execute(
        "INSERT INTO these_aenderungsvorschlaege "
        "(these_id, hauptgruppe, unterkategorie, mechanismus_typ, vorgeschlagene_richtung, "
        " begruendung, datenstand, beobachtung_seit, status) "
        "VALUES (NULL, ?, ?, ?, ?, 'Test', '2026-08-07', ?, 'beobachtung')",
        (hauptgruppe, unterkategorie, mechanismus, richtung, seit))
    conn.commit()

# Der echte Stand vom 07.08. nachgestellt
lege_vorschlag_an("technologie_ki", "ki", "bellwether_sentiment", 12)        # Schwelle 30
lege_vorschlag_an("technologie_ki", "halbleiter", "bellwether_sentiment", 13)
lege_vorschlag_an("aktien_sektoren", "gesundheit", "bellwether_sentiment", 12)
lege_vorschlag_an("anleihen_geldmarkt", None, "m2_liquiditaet", 13)          # Schwelle 14
lege_vorschlag_an("aktien_regionen", None, "baerenmarkt_overlay", 9)         # Schwelle 7 -> reif

from agent.kategorie_vorschlaege import wartende_vorschlaege

w = wartende_vorschlaege(conn, JETZT)
nach_kat = {(e["hauptgruppe"], e["unterkategorie"]): e for e in w["vorschlaege"]}

print("A) REIFE-BERECHNUNG je Mechanismus")
ki = nach_kat.get(("technologie_ki", "ki"))
pruefe("A1 KI-Vorschlag erfasst", ki is not None)
pruefe("A2 Bellwether-Schwelle 30 Tage erkannt", ki and ki["schwelle_tage"] == 30,
       str(ki and ki["schwelle_tage"]))
pruefe("A3 noch 18 Tage bis reif", ki and abs(ki["tage_bis_reif"] - 18.0) < 0.2,
       f"{ki['tage_bis_reif']} Tage")
pruefe("A4 Reifedatum 25.08. (26.07. + 30 Tage)", ki and ki["reif_am"] == "2026-08-25", ki and ki["reif_am"])
pruefe("A5 noch nicht reif", ki and ki["ist_reif"] is False)

m2 = nach_kat.get(("anleihen_geldmarkt", None))
pruefe("A6 M2-Schwelle 14 Tage", m2 and m2["schwelle_tage"] == 14)
pruefe("A7 noch 1 Tag", m2 and abs(m2["tage_bis_reif"] - 1.0) < 0.2, f"{m2['tage_bis_reif']}")

baer = nach_kat.get(("aktien_regionen", None))
pruefe("A8 Baerenmarkt-Overlay mit 7 Tagen ist bereits reif",
       baer and baer["ist_reif"] is True and baer["tage_bis_reif"] == 0.0)

print("\nB) DIE ZAHL, DIE DEN ENGPASS ANKUENDIGT")
pruefe("B1 wartende und reife getrennt gezaehlt",
       w["anzahl_wartend"] == 4 and w["anzahl_reif"] == 1,
       f"{w['anzahl_wartend']} wartend, {w['anzahl_reif']} reif")
pruefe("B2 Engpass-Tag ist der 25.08.", w["engpass_am"] == "2026-08-25", str(w["engpass_am"]))
pruefe("B3 zwei Kandidaten an diesem Tag", w["engpass_anzahl"] == 2,
       f"{w['engpass_anzahl']} - ki und gesundheit, beide 12 Tage alt")

print("\nC) BUDGET-BEZUG")
pruefe("C1 aktive Thesen gezaehlt", w["aktive_thesen"] == 0)
pruefe("C2 freies Budget = Richtgroesse", w["freies_budget"] == w["richtgroesse_max"])

print("\nD) SORTIERUNG - was zuerst reif wird, steht oben")
tage = [e["tage_bis_reif"] for e in w["vorschlaege"]]
pruefe("D1 aufsteigend nach Restzeit", tage == sorted(tage), str(tage))

print("\nE) SCHWERPUNKTE WERDEN MARKIERT")
import config
_orig = config.load_config
import copy
cfg = copy.deepcopy(_orig())
cfg.setdefault("schwerpunkte", {})["manuell"] = ["technologie_ki:ki"]
config.load_config = lambda *a, **k: cfg
w2 = wartende_vorschlaege(conn, JETZT)
ki2 = {(e["hauptgruppe"], e["unterkategorie"]): e for e in w2["vorschlaege"]}[("technologie_ki", "ki")]
pruefe("E1 gesetzter Schwerpunkt erkennbar", ki2["ist_schwerpunkt"] is True)
halb = {(e["hauptgruppe"], e["unterkategorie"]): e for e in w2["vorschlaege"]}[("technologie_ki", "halbleiter")]
pruefe("E2 andere nicht", halb["ist_schwerpunkt"] is False)
config.load_config = _orig

print("\nG) KLARTEXT STATT INTERNER IDS")
g = nach_kat[("technologie_ki", "ki")]
pruefe("G1 Kategorie lesbar",
       g["kategorie_anzeige"] == "Technologie & KI / Künstliche Intelligenz",
       g["kategorie_anzeige"])
pruefe("G2 Hauptgruppe ohne Unterkategorie lesbar",
       nach_kat[("aktien_regionen", None)]["kategorie_anzeige"] == "Aktien - Regionen & Länder",
       nach_kat[("aktien_regionen", None)]["kategorie_anzeige"])
pruefe("G3 Richtung lesbar", g["richtung_anzeige"] == "Übergewichten", g["richtung_anzeige"])
pruefe("G4 Mechanismus lesbar", g["mechanismus_anzeige"] == "Bellwether-Sentiment",
       g["mechanismus_anzeige"])
pruefe("G5 stabile IDs bleiben daneben stehen",
       g["hauptgruppe"] == "technologie_ki" and g["unterkategorie"] == "ki",
       "eine Auswertung braucht die ID, kein Anzeigewort")

print("\nF) LEERER ZUSTAND")
conn.execute("DELETE FROM these_aenderungsvorschlaege")
conn.commit()
leer = wartende_vorschlaege(conn, JETZT)
pruefe("F1 keine Vorschlaege ohne Absturz",
       leer["anzahl_wartend"] == 0 and leer["engpass_am"] is None)

print("\n" + ("ALLE TESTS BESTANDEN" if not fehler else f"FEHLER: {fehler}"))
conn.close()
