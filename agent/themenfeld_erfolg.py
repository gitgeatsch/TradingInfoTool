"""Erfolgsmaß je Themenfeld (2026-08-07, Schritt 5 des Gesamtkonzepts, G-2).

WARUM NICHT DIE SYSTEMGUETE JE HAUPTGRUPPE, wie ursprünglich geplant. Vor dem
Bau gemessen, am Notebook-Export vom 07.08.:

    2795 Spot-Signale, davon 10 aufgeloest.
    1759 Hebel-Signale, davon 91 aufgeloest.
    Von diesen 101 aufgeloesten gehoert **kein einziges** zu einem Themenfeld.

Das ist kein Zufall und kein Datenloch: die Themen-Taxonomie ist bewusst fuer
Nicht-Krypto gebaut, und Nicht-Krypto hat bisher keine aufgeloesten Signale
hervorgebracht. Eine "Systemguete je Hauptgruppe" waere heute eine Tabelle aus
leeren Zellen - und wuerde dabei aussehen wie ein funktionierendes Instrument.
Das ist schlimmer als keine Zahl.

WAS STATTDESSEN GEMESSEN WIRD. Eine These ist keine Trade-Folge, sondern eine
**Richtungsaussage auf einen Korb**. SQN und Expectancy sind dafuer dieselbe
Art Kategorienfehler wie beim Hedge (siehe portfolio_historie.py::
compute_hedge_wirksamkeit(), 07.08.): Kennzahlen, die eine andere Frage
beantworten als die gestellte. Gemessen wird deshalb:

  1. **Traf die Richtung?** Korbrendite der Kategorie seit `gesetzt_am`,
     gegen die uebrigen Themenfelder als Vergleichsmassstab. "Uebergewichten"
     ist eine RELATIVE Aussage - sie braucht ein Gegenueber, sonst misst man
     nur den Gesamtmarkt.
  2. **Kam die These ueberhaupt bis zu einem Asset?** Wie viele Assets des
     Themenfelds haben eine Kursreihe, wie viele haben je ein Signal erzeugt.
     Das macht die eigentliche Engstelle sichtbar, statt sie zu verdecken.

DIE MESSBARKEIT WIRD MITGELIEFERT, nicht vorausgesetzt. Von den sechs aktiven
Thesen am 07.08. haben **zwei ueberhaupt kein Asset mit Kursreihe**
(industriemetalle und edelmetalle, jeweils "diversifiziert" mit einem einzigen
Katalog-Symbol ohne Historie). Fuer die gibt es kein Ergebnis, und das steht
dann auch so da - `messbar: False` mit Grund.

WAS HIER BEWUSST NICHT GEMESSEN WIRD: die Absicherungs-Hauptgruppe. Ein Hedge,
der verliert waehrend das Portfolio steigt, hat funktioniert - eine
Ueberrendite-Messung wuerde ihn systematisch als Fehlschlag ausweisen. Dafuer
gibt es compute_hedge_wirksamkeit(); hier wird darauf verwiesen statt eine
falsche Zahl zu erzeugen.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone

import config
import database.db as db
# Dieselbe Klartext-Tabelle wie bei den wartenden Vorschlaegen - bewusst
# importiert statt kopiert, damit Karte, Export und GUI dieselben Woerter
# benutzen. Drei Kopien laufen garantiert auseinander.
from agent.kategorie_vorschlaege import _RICHTUNG_ANZEIGE

logger = logging.getLogger(__name__)

# Mindestens so viele Handelstage muessen seit `gesetzt_am` vergangen sein,
# bevor eine Richtungsaussage ueberhaupt bewertet wird. Darunter misst man
# Tagesrauschen und nennt es Treffer - dieselbe Falle wie bei der
# Mindestbeobachtung der Ueberholt-Erkennung.
MIN_TAGE_FUER_URTEIL = 10

# Ab welchem Renditeunterschied gilt eine Richtungsaussage als getroffen?
# Darunter ist das Ergebnis "unentschieden": bei einem Korb aus ein bis drei
# Werten ist ein halber Prozentpunkt kein Signal, sondern Zufall.
SCHWELLE_TREFFER_PROZENT = 2.0

# Die Absicherungs-Hauptgruppe wird bewusst NICHT ueber Ueberrendite gemessen.
HAUPTGRUPPE_ABSICHERUNG = "absicherung"


def _korbrendite(symbole: list[str], reihen: dict, ab_datum: str) -> tuple[float | None, list[str]]:
    """Gleichgewichtete Rendite eines Symbolkorbs seit `ab_datum`.

    Gleichgewichtet und nicht kapitalgewichtet: eine These sagt "dieses
    Themenfeld", nicht "dieser eine grosse Wert darin". Zurueck kommt auch,
    WELCHE Symbole getragen haben - ohne das laesst sich eine Korbzahl aus
    einem einzigen Wert nicht von einer aus zwoelf unterscheiden.
    """
    renditen: list[float] = []
    getragen: list[str] = []
    for symbol in symbole:
        kerzen = [k for k in (reihen.get(symbol) or []) if k["date"] >= ab_datum]
        if len(kerzen) < 2:
            continue
        start, ende = kerzen[0]["close"], kerzen[-1]["close"]
        if not start or start <= 0 or ende is None:
            continue
        renditen.append((ende / start - 1.0) * 100.0)
        getragen.append(symbol)
    if not renditen:
        return None, []
    return sum(renditen) / len(renditen), getragen


def _tage_seit(datum_iso: str, jetzt: datetime) -> float:
    stand = datetime.fromisoformat(datum_iso)
    if stand.tzinfo is None:
        stand = stand.replace(tzinfo=timezone.utc)
    return (jetzt - stand).total_seconds() / 86400


def _signale_je_symbol(conn) -> dict[str, dict]:
    """Wie viele Signale hat ein Symbol je erzeugt, und wie viele davon wurden
    aufgeloest? Beide Signal-Tabellen zusammen - die Frage "erreicht die These
    ueberhaupt ein Asset" unterscheidet nicht nach Pipeline."""
    ergebnis: dict[str, dict] = {}
    for tabelle in ("signals", "hebel_signals"):
        try:
            rows = conn.execute(
                f"SELECT symbol, outcome_status FROM {tabelle}"
            ).fetchall()
        except Exception as exc:  # noqa: BLE001 - fehlende Tabelle darf nichts toeten
            logger.info("Themenfeld-Erfolg: %s nicht lesbar (%s)", tabelle, exc)
            continue
        for row in rows:
            eintrag = ergebnis.setdefault(row["symbol"], {"signale": 0, "aufgeloest": 0})
            eintrag["signale"] += 1
            if row["outcome_status"] in ("take_profit_erreicht", "stop_loss_erreicht",
                                         "horizont_abgelaufen"):
                eintrag["aufgeloest"] += 1
    return ergebnis


def compute_themenfeld_erfolg(conn, jetzt: datetime | None = None) -> dict:
    """Je aktiver These: traf die Richtung, und kam sie ueberhaupt bei einem
    Asset an? Siehe Modul-Docstring fuer die Herleitung.

    Reine Lesefunktion.
    """
    jetzt = jetzt or datetime.now(timezone.utc)
    from agent.krypto.backward_tracking import lade_kursreihen

    reihen = lade_kursreihen(conn)
    signale = _signale_je_symbol(conn)
    thesen = db.get_aktive_thesen(conn)

    # Der Vergleichsmassstab: alle Assets, die zu IRGENDEINEM Themenfeld
    # gehoeren. "Uebergewichten" ist eine relative Aussage - ohne Gegenueber
    # misst man den Gesamtmarkt und nennt es Themenwahl.
    alle_themen_symbole: set[str] = set()
    for gruppe in config.get_kategorien().get("hauptgruppen") or []:
        alle_themen_symbole.update(config.kategorie_handelbare_assets(gruppe["id"]))

    eintraege = []
    for these in thesen:
        symbole = config.kategorie_handelbare_assets(these.hauptgruppe, these.unterkategorie)
        mit_reihe = [s for s in symbole if len(reihen.get(s) or []) >= 2]
        tage = _tage_seit(these.gesetzt_am, jetzt)
        wirkungskette = {
            "assets_gesamt": len(symbole),
            "assets_mit_kursreihe": len(mit_reihe),
            "assets_mit_signal": sum(1 for s in symbole if signale.get(s, {}).get("signale")),
            "signale_gesamt": sum(signale.get(s, {}).get("signale", 0) for s in symbole),
            "signale_aufgeloest": sum(signale.get(s, {}).get("aufgeloest", 0) for s in symbole),
        }
        basis = {
            "hauptgruppe": these.hauptgruppe,
            "unterkategorie": these.unterkategorie,
            "kategorie_anzeige": (
                config._kategorie_klartext(these.hauptgruppe, these.unterkategorie)
                or these.hauptgruppe
            ),
            "richtung": these.richtung,
            # Klartext neben der stabilen ID - dieselbe Regel wie bei den
            # wartenden Vorschlaegen: die Anzeige liest sich, die Auswertung
            # rechnet mit der ID.
            "richtung_anzeige": _RICHTUNG_ANZEIGE.get(these.richtung, these.richtung),
            "gesetzt_am": these.gesetzt_am,
            "tage_aktiv": round(tage, 1),
            "wirkungskette": wirkungskette,
        }

        # Absicherung: andere Frage, anderes Werkzeug (siehe Modul-Docstring).
        if these.hauptgruppe == HAUPTGRUPPE_ABSICHERUNG:
            eintraege.append({**basis, "messbar": False, "treffer": None,
                              "grund": "Absicherung wird über die Dämpfung gemessen, nicht "
                                       "über Überrendite — siehe compute_hedge_wirksamkeit()."})
            continue
        if not mit_reihe:
            eintraege.append({**basis, "messbar": False, "treffer": None,
                              "grund": f"kein Asset dieser Kategorie hat eine Kursreihe "
                                       f"({len(symbole)} Assets, 0 mit Historie)"})
            continue
        if tage < MIN_TAGE_FUER_URTEIL:
            eintraege.append({**basis, "messbar": False, "treffer": None,
                              "grund": f"erst {tage:.1f} Tage aktiv, Urteil ab "
                                       f"{MIN_TAGE_FUER_URTEIL} Tagen"})
            continue

        ab = these.gesetzt_am[:10]
        korb, getragen = _korbrendite(mit_reihe, reihen, ab)
        vergleich, _ = _korbrendite(
            sorted(alle_themen_symbole - set(symbole)), reihen, ab)
        # WELCHER Korb fehlt, muss dastehen. "Zu wenige Kurspunkte" allein
        # laesst offen, ob die Kategorie oder der Vergleichsmassstab leer ist -
        # und das sind voellig verschiedene Probleme: das eine betrifft eine
        # Kategorie, das andere macht ALLE Messungen unmoeglich.
        if korb is None or vergleich is None:
            if korb is None and vergleich is None:
                grund = (f"weder die Kategorie noch der Vergleichskorb haben Kurspunkte "
                         f"seit {ab} - vermutlich fehlt die Kurshistorie insgesamt")
            elif korb is None:
                grund = (f"die {len(mit_reihe)} Assets dieser Kategorie haben keine "
                         f"Kurspunkte seit {ab} (Reihen enden frueher)")
            else:
                grund = (f"der Vergleichskorb hat keine Kurspunkte seit {ab} - "
                         f"das blockiert JEDE Themenfeld-Messung, nicht nur diese")
            eintraege.append({**basis, "messbar": False, "treffer": None, "grund": grund})
            continue

        ueberrendite = korb - vergleich
        # `neutral` trifft keine Richtungsaussage - dafuer gibt es kein Urteil,
        # nur die Zahl. Ein Treffer waere hier eine erfundene Aussage.
        if these.richtung == "neutral":
            treffer = None
        elif abs(ueberrendite) < SCHWELLE_TREFFER_PROZENT:
            treffer = "unentschieden"
        elif these.richtung == "uebergewichten":
            treffer = ueberrendite > 0
        elif these.richtung == "meiden":
            treffer = ueberrendite < 0
        else:
            treffer = None

        eintraege.append({
            **basis,
            "messbar": True,
            "korb_rendite_prozent": round(korb, 2),
            "vergleich_rendite_prozent": round(vergleich, 2),
            "ueberrendite_prozentpunkte": round(ueberrendite, 2),
            "getragen_von": getragen,
            "treffer": treffer,
            "grund": None,
        })

    messbare = [e for e in eintraege if e["messbar"]]
    mit_urteil = [e for e in messbare if e["treffer"] in (True, False)]
    return {
        "thesen": eintraege,
        "anzahl_thesen": len(eintraege),
        "anzahl_messbar": len(messbare),
        "anzahl_mit_urteil": len(mit_urteil),
        "treffer": sum(1 for e in mit_urteil if e["treffer"] is True),
        "fehlschlaege": sum(1 for e in mit_urteil if e["treffer"] is False),
        "schwelle_treffer_prozent": SCHWELLE_TREFFER_PROZENT,
        "min_tage_fuer_urteil": MIN_TAGE_FUER_URTEIL,
        "lesehilfe": (
            "Gemessen wird die Richtungsaussage einer These auf einen Korb, NICHT "
            "eine Trade-Folge: von 101 aufgeloesten Signalen (Stand 07.08.) gehoert "
            "keines zu einem Themenfeld, eine Systemguete je Hauptgruppe waere leer. "
            "ueberrendite_prozentpunkte ist die gleichgewichtete Korbrendite der "
            "Kategorie minus der aller uebrigen Themen-Assets seit gesetzt_am. "
            "'unentschieden' heisst: Unterschied unter der Schwelle. Richtung "
            "'neutral' bekommt kein Urteil, weil sie keine Aussage trifft. "
            "Absicherung wird ueber compute_hedge_wirksamkeit() gemessen. "
            "wirkungskette zeigt, ob die These ueberhaupt bei einem Asset ankommt - "
            "das ist derzeit die eigentliche Engstelle."
        ),
    }
