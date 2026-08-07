"""Prueft die weiche Richtgroesse und die G-5-Handelbarkeitspruefung (07.08.2026, S-2).

DIE SPEZIFIKATION, im Wortlaut (`Kategorie_Basisinformationen_Release2.md`
Abschnitt 5, Punkt 3): *"Richtgroesse: 3-6 gleichzeitig aktive Thesen, weich in
der GUI angezeigt, kein Hard-Limit im Code."*

Implementiert war das Gegenteil: nur die Obergrenze existierte, sie war ein
hartes Budget, und in der GUI stand sie gar nicht. Der wichtigste Test hier ist
deshalb B2 - **neun reife Kandidaten bei sechs aktiven Thesen, und nichts wird
zurueckgestellt.** Genau dieser Fall steht am 24./25.08. an.

Getestet wird die AUFRUFENDE Funktion, nicht nur der Helfer: dass
`_bestimme_gesperrte_fall_a_kandidaten()` eine leere Menge liefert, nuetzt
nichts, wenn `_verarbeite_signal()` trotzdem keine These anlegt (Lehre vom
02.08., Stop-Regelfamilie).
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

JETZT = datetime(2026, 8, 25, 6, 30, tzinfo=timezone.utc)

from agent.kategorie_vorschlaege import (
    _bestimme_gesperrte_fall_a_kandidaten,
    _verarbeite_signal,
    richtgroessen_lage,
    wartende_vorschlaege,
)


def lege_these_an(hauptgruppe, unterkategorie, richtung="uebergewichten"):
    db.create_these(conn, These(
        hauptgruppe=hauptgruppe, unterkategorie=unterkategorie, richtung=richtung,
        begruendung="Test", gesetzt_am=JETZT.isoformat(), pruef_mechanismus="m2_liquiditaet"))


def lege_kandidat_an(hauptgruppe, unterkategorie, mechanismus, tage_her):
    conn.execute(
        "INSERT INTO these_aenderungsvorschlaege "
        "(these_id, hauptgruppe, unterkategorie, mechanismus_typ, vorgeschlagene_richtung, "
        " begruendung, datenstand, beobachtung_seit, status) "
        "VALUES (NULL, ?, ?, ?, 'uebergewichten', 'Test', '2026-08-25', ?, 'beobachtung')",
        (hauptgruppe, unterkategorie, mechanismus,
         (JETZT - timedelta(days=tage_her)).isoformat()))
    conn.commit()


print("A) DIE RICHTGROESSE HAT JETZT ZWEI ZAHLEN")
minimum, maximum = config.richtgroesse_thesen()
pruefe("A1 Untergrenze aus der Spezifikation", minimum == 3, str(minimum))
pruefe("A2 Obergrenze aus der Spezifikation", maximum == 6, str(maximum))

lage = richtgroessen_lage(conn)
pruefe("A3 null Thesen ist UNTER der Richtgroesse", lage["lage"] == "unter", lage["lage"])
pruefe("A4 und das ist der derzeit relevante Fall",
       "gebraucht" in lage["hinweis"], lage["hinweis"][:50])

# Der reale Stand vom 07.08.: sechs Thesen, vier davon Rohstoffe, zwei neutral
for hg, uk, r in [("absicherung", None, "aktiv"),
                  ("energie", None, "uebergewichten"),
                  ("absicherung", "aktienmarkt_short", "aktiv"),
                  ("agrarrohstoffe", "agrar_diversifiziert", "neutral"),
                  ("industriemetalle", "industriemetalle_diversifiziert", "neutral"),
                  ("edelmetalle", "edelmetalle_diversifiziert", "uebergewichten")]:
    lege_these_an(hg, uk, r)

lage = richtgroessen_lage(conn)
pruefe("A5 sechs Thesen liegen IM Rahmen", lage["lage"] == "im_rahmen", lage["lage"])
pruefe("A6 die Verteilung wird mitgeliefert - sechs Thesen auf fuenf Hauptgruppen",
       lage["hauptgruppen_abgedeckt"] == 5, str(lage["hauptgruppen_abgedeckt"]))
pruefe("A7 zwei davon neutral", lage["davon_neutral"] == 2, str(lage["davon_neutral"]))
pruefe("A8 Anzeigetext fuer die GUI",
       lage["anzeige"] == "6 aktive Thesen · Richtgröße 3–6", lage["anzeige"])

print("\nB) DER FALL VOM 24./25.08. - neun reife Kandidaten bei vollem 'Budget'")
neun = [("technologie_ki", "ki"), ("technologie_ki", "halbleiter"),
        ("technologie_ki", "robotik"), ("technologie_ki", "cybersicherheit"),
        ("aktien_sektoren", "gesundheit"), ("aktien_sektoren", "finanzen"),
        ("aktien_regionen", "usa"), ("anleihen_geldmarkt", None),
        ("sonstige", None)]
angelegt = 0
for hg, uk in neun:
    if config.get_pruef_mechanismus(hg, uk) is None:
        continue
    lege_kandidat_an(hg, uk, "bellwether_sentiment", 40)
    angelegt += 1
pruefe("B1 Kandidaten mit Pruef-Mechanismus angelegt", angelegt >= 5, f"{angelegt} von 9")

gesperrt = _bestimme_gesperrte_fall_a_kandidaten(conn, JETZT)
pruefe("B2 NICHTS wird wegen der Richtgroesse zurueckgestellt",
       gesperrt == set(),
       f"vorher waeren {angelegt} - 0 freie Plaetze = {angelegt} gesperrt gewesen")

print("\nC) DIE AUFRUFENDE FUNKTION legt auch wirklich an")
# Nicht nur der Helfer: _verarbeite_signal() ist die Stelle, die die These baut.
vorher = len(db.get_aktive_thesen(conn))
ziel = next((k for k in neun if config.get_pruef_mechanismus(k[0], k[1]) is not None), None)
_verarbeite_signal(
    conn, these_id=None, hauptgruppe=ziel[0], unterkategorie=ziel[1],
    mechanismus_typ="bellwether_sentiment", vorgeschlagene_richtung="uebergewichten",
    begruendung="Test", datenstand="2026-08-25", persistenz_tage=30, jetzt=JETZT,
    automatische_uebernahme_gesperrt=(ziel in gesperrt))
nachher = len(db.get_aktive_thesen(conn))
pruefe("C1 die siebte These entsteht, obwohl die Richtgroesse 6 sagt",
       nachher == vorher + 1, f"{vorher} -> {nachher}")

lage = richtgroessen_lage(conn)
pruefe("C2 und die Lage meldet das Ueberschreiten", lage["lage"] == "ueber", lage["lage"])
pruefe("C3 als erlaubt, nicht als Fehler", "erlaubt" in lage["hinweis"], lage["hinweis"][:40])

print("\nD) G-5 - handelbare Assets je Kategorie")
pruefe("D1 Katalog-Symbole werden gefunden",
       "ARTINT" in config.kategorie_handelbare_assets("technologie_ki", "ki"))
pruefe("D2 Watchlist-Symbole ebenfalls - SONST waeren die Hedge-Kategorien gesperrt",
       config.kategorie_handelbare_assets("absicherung", "aktienmarkt_short") == ["DBPK"],
       "absicherung/aktienmarkt_short hat KEINE Katalog-Symbole")
pruefe("D3 dasselbe fuer sektor_short",
       config.kategorie_handelbare_assets("absicherung", "sektor_short") == ["3QSS"])
pruefe("D4 Hauptgruppe ohne Unterkategorie deckt alles darunter",
       len(config.kategorie_handelbare_assets("technologie_ki")) > 10,
       str(len(config.kategorie_handelbare_assets("technologie_ki"))))
pruefe("D5 unbekannte Kategorie liefert leer, kein Absturz",
       config.kategorie_handelbare_assets("gibt_es_nicht", "auch_nicht") == [])
pruefe("D6 None ohne Absturz", config.kategorie_handelbare_assets(None) == [])

print("\nE) KEINE KATEGORIE IST HEUTE BETROFFEN - gemessen, nicht vermutet")
leer = []
for g in config.get_kategorien()["hauptgruppen"]:
    for u in (g.get("unterkategorien") or []):
        if not config.kategorie_handelbare_assets(g["id"], u["id"]):
            leer.append(f"{g['id']}/{u['id']}")
pruefe("E1 alle Unterkategorien haben mindestens ein handelbares Asset",
       leer == [], f"ohne Asset: {leer}")
pruefe("E2 die Pruefung bleibt trotzdem als Wachhund fuer neue Kategorien",
       callable(config.kategorie_handelbare_assets))

print("\nF) WAS NOCH GESPERRT WIRD - der Qualitaetsgrund")
# Eine der TATSAECHLICH reifen Kategorien so tun lassen, als haette sie kein
# handelbares Asset - eine erfundene Kategorie waere gar nicht erst reif.
from agent.kategorie_vorschlaege import _reife_fall_a_kandidaten
reife_jetzt = _reife_fall_a_kandidaten(conn, JETZT)
pruefe("F0 es gibt ueberhaupt reife Kandidaten fuer diesen Test",
       len(reife_jetzt) > 1, f"{len(reife_jetzt)} reif")
opfer = sorted(reife_jetzt)[0]

_orig = config.kategorie_handelbare_assets
config.kategorie_handelbare_assets = (
    lambda h, u=None: [] if (h, u) == opfer else _orig(h, u))
gesperrt2 = _bestimme_gesperrte_fall_a_kandidaten(conn, JETZT)
config.kategorie_handelbare_assets = _orig
pruefe("F1 eine Kategorie ohne handelbares Asset WIRD zurueckgestellt",
       gesperrt2 == {opfer}, f"Opfer {opfer}, gesperrt: {sorted(gesperrt2)}")
pruefe("F2 die uebrigen reifen bleiben unberuehrt",
       len(reife_jetzt) - len(gesperrt2) == len(reife_jetzt) - 1,
       "die Sperre ist ein Qualitaets-, kein Mengenkriterium")

print("\nG) DIE VORSCHAU LIEFERT DIE LAGE MIT")
w = wartende_vorschlaege(conn, JETZT)
pruefe("G1 Richtgroessen-Lage im Ergebnis", "richtgroessen_lage" in w)
pruefe("G2 Untergrenze mitgeliefert", w["richtgroesse_min"] == 3, str(w.get("richtgroesse_min")))
pruefe("G3 handelbare Assets je Vorschlag",
       all("handelbare_assets" in v for v in w["vorschlaege"]) or not w["vorschlaege"])
pruefe("G4 die Lesehilfe erklaert, dass nicht mehr gesperrt wird",
       "sperrt" in w["lesehilfe"].lower() or "SPERRT" in w["lesehilfe"],
       "sonst liest sich freies_budget weiter wie ein Gate")

print("\n" + ("ALLE TESTS BESTANDEN" if not fehler else f"FEHLER: {fehler}"))
conn.close()
