"""Prueft die manuellen Schwerpunkte mit garantiertem Raum (07.08.2026).

DIE ANFORDERUNG, im Wortlaut des Nutzers: *"wenn z.B. ein Thema trendet,
bekommen andere wichtige Bereiche keinen Raum, obwohl ich der Meinung bin, dass
Energie aktuell unterbewertet ist und zukuenftig massiv steigen wird - und diese
Trades werden vergessen bzw. gehen unter."*

Das dreht die uebliche Anforderung um: ein Mechanismus, der Aufmerksamkeit nach
TRENDSTAERKE verteilt, tut systematisch das Gegenteil dessen, was antizyklisches
Investieren braucht. Ein Themenfeld ist oft gerade dann interessant, WEIL
niemand hinsieht.

Der Test bildet genau diesen Konflikt nach: mehr reife Kandidaten als Plaetze,
und ein gesetzter Schwerpunkt darunter.
"""
import config

fehler = []
def pruefe(name, ok, info=""):
    print(("  OK   " if ok else "  FEHL ") + name + ("  " + info if info else ""))
    if not ok:
        fehler.append(name)

# Schwerpunkte fuer den Test setzen, am Ende wiederherstellen
_ORIGINAL = config.load_config
_vorher = config.manuelle_schwerpunkte()


def _mit_schwerpunkten(liste):
    import copy
    cfg = copy.deepcopy(_ORIGINAL())
    cfg.setdefault("schwerpunkte", {})["manuell"] = liste
    config.load_config = lambda *a, **k: cfg


print("A) ERKENNUNG")
_mit_schwerpunkten(["energie"])
pruefe("A1 Hauptgruppe erkannt", config.ist_manueller_schwerpunkt("energie"))
pruefe("A2 deckt auch die Unterkategorien ab",
       config.ist_manueller_schwerpunkt("energie", "erdgas"),
       "ein Eintrag auf Hauptgruppen-Ebene schuetzt alles darunter")
pruefe("A3 andere Gruppen unberuehrt",
       not config.ist_manueller_schwerpunkt("technologie_ki"))

_mit_schwerpunkten(["technologie_ki:ki"])
pruefe("A4 Unterkategorie-Eintrag schuetzt NUR diese",
       config.ist_manueller_schwerpunkt("technologie_ki", "ki")
       and not config.ist_manueller_schwerpunkt("technologie_ki", "halbleiter"))

_mit_schwerpunkten([])
pruefe("A5 leere Liste = kein Schwerpunkt",
       not config.ist_manueller_schwerpunkt("energie"))
pruefe("A6 None ohne Absturz", not config.ist_manueller_schwerpunkt(None))

print("\nB) DER KONFLIKTFALL - mehr reife Kandidaten als Plaetze")
# Die Moderation nachbilden: 5 reife Kandidaten, Budget 0, einer davon Schwerpunkt
reife = [("energie", None), ("technologie_ki", "ki"), ("technologie_ki", "halbleiter"),
         ("aktien_sektoren", "gesundheit"), ("aktien_sektoren", "finanzen")]

_mit_schwerpunkten(["energie"])
geschuetzt = {k for k in reife if config.ist_manueller_schwerpunkt(k[0], k[1])}
wettbewerber = [k for k in reife if k not in geschuetzt]
pruefe("B1 Schwerpunkt wird herausgenommen",
       geschuetzt == {("energie", None)}, str(geschuetzt))
pruefe("B2 die anderen vier konkurrieren weiter", len(wettbewerber) == 4)

# Budget 0: alle Wettbewerber werden gesperrt, der Schwerpunkt NICHT
budget = 0
gesperrt = set(sorted(wettbewerber)[budget:])
pruefe("B3 bei Budget 0 werden alle Wettbewerber zurueckgestellt", len(gesperrt) == 4)
pruefe("B4 der Schwerpunkt ist NICHT darunter - er kommt durch",
       ("energie", None) not in gesperrt,
       "genau das war die Sorge: Energie geht nicht unter")

print("\nC) OHNE SCHWERPUNKT - unveraendertes Verhalten")
_mit_schwerpunkten([])
geschuetzt2 = {k for k in reife if config.ist_manueller_schwerpunkt(k[0], k[1])}
pruefe("C1 nichts geschuetzt", geschuetzt2 == set())
pruefe("C2 alle fuenf konkurrieren",
       len([k for k in reife if k not in geschuetzt2]) == 5,
       "ohne gesetzten Schwerpunkt bleibt alles wie vorher")

print("\nD) MEHRERE SCHWERPUNKTE")
_mit_schwerpunkten(["energie", "technologie_ki:ki"])
geschuetzt3 = {k for k in reife if config.ist_manueller_schwerpunkt(k[0], k[1])}
pruefe("D1 beide geschuetzt",
       geschuetzt3 == {("energie", None), ("technologie_ki", "ki")}, str(geschuetzt3))
pruefe("D2 halbleiter NICHT (nur ki war gesetzt)",
       ("technologie_ki", "halbleiter") not in geschuetzt3)

print("\nE) WAS EIN SCHWERPUNKT NICHT TUT")
pruefe("E1 er erfindet keine Richtung - die Funktion sagt nur ja/nein",
       config.ist_manueller_schwerpunkt("energie") is True,
       "Aufmerksamkeits-Entscheidung, keine Richtungsvorgabe")

config.load_config = _ORIGINAL
pruefe("E2 Konfiguration nach dem Test unveraendert",
       config.manuelle_schwerpunkte() == _vorher, str(config.manuelle_schwerpunkte()))

print("\n" + ("ALLE TESTS BESTANDEN" if not fehler else f"FEHLER: {fehler}"))
