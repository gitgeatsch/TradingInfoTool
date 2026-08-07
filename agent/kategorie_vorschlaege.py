"""KI-Vorschlaege-Job fuer Kategorie-Schwerpunkte (#333, 2026-07-24) - siehe
Basisinfos/Kategorie_Basisinformationen_Release2.md Abschnitt 11-15 fuer die
volle Konzeption. Taeglicher, rein deterministischer Job (Muster wie
agent/krypto/makro_analog.py::run_makro_analog_update() - KEIN LLM-Call,
siehe Punkt 2 der #333-Statustabelle: Schicht 1 ist komplett deterministisch,
Schicht 2 [ein taeglicher LLM-Synthese-Call ueber alle Kategorien] ist noch
nicht gebaut - dieser Job deckt nur Schicht 1 ab).

Iteriert ueber alle Hauptgruppe/Unterkategorie-Schluessel aus
config.PRUEF_MECHANISMUS_MAPPING:

- **Fall A** (keine aktive These fuer diese Kategorie): das Rohsignal wird
  ueber eine SONDE-These ermittelt (feste Annahme-Richtung
  'uebergewichten'/'aktiv', existiert nur im Speicher, wird nie gespeichert)
  - `compute_these_abgleich()` gegen diese Sonde liefert dieselbe Auskunft
    wie gegen eine echte These, ohne die Funktion zu duplizieren. "gestuetzt"
    -> vorgeschlagene Richtung = Sonden-Richtung, "widerspricht" -> Gegenteil.
  Bei anhaltendem Signal (Persistenzschwelle erreicht) wird DIREKT eine neue
  `These` angelegt (`quelle='ki_vorschlag'`, `status='aktiv'`) - sofort ueber
  die bestehende ThesenView bearbeitbar, kein separater Genehmigungsschritt.
- **Fall B** (aktive These existiert): `compute_these_abgleich()` gegen die
  echte These. Bei anhaltendem 'widerspricht' wird der Tracker-Eintrag auf
  'offen' gehoben (sichtbar in der Schwerpunkte-Tab, wartet auf
  Uebernehmen/Ablehnen ueber die GUI) - die bestehende These bleibt bis dahin
  unveraendert.

Persistenzschwellen sind mechanismus-spezifisch (Abschnitt 15) - bei mehreren
Mechanismen fuer eine Kategorie gilt die KUERZESTE (der schnellere Mechanismus
bestimmt den Takt, gleiches Prinzip wie bei den review_am-Vorschlaegen)."""
from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta, timezone

import config
import database.db as db
from agent.kategorie_thesen import compute_these_abgleich
from database.models import These, TheseAenderungsvorschlag

logger = logging.getLogger(__name__)

# Persistenz-Tage je Mechanismus (Abschnitt 15) - m2_liquiditaet nutzt seit
# Punkt 18 primaer die woechentliche Net-Liquidity, deshalb im selben Bucket
# wie COT/EIA (14 Tage), nicht mehr im alten monatlichen M2-Bucket (60 Tage).
_PERSISTENZ_TAGE_JE_MECHANISMUS = {
    "cot_positionierung": 14,
    "m2_liquiditaet": 14,
    "zinskurve": 30,
    "dollar_index": 30,
    "baerenmarkt_overlay": 7,
}
_PERSISTENZ_TAGE_FALLBACK = 30
COOLDOWN_TAGE_NACH_ABLEHNUNG = 30


def _persistenz_tage_fuer_mechanismen(mechanismen: list[str]) -> int:
    tage = [_PERSISTENZ_TAGE_JE_MECHANISMUS.get(m, _PERSISTENZ_TAGE_FALLBACK) for m in mechanismen]
    return min(tage) if tage else _PERSISTENZ_TAGE_FALLBACK


def _alle_kategorie_schluessel() -> list[tuple[str, str | None]]:
    """Parst die Schluessel aus config.PRUEF_MECHANISMUS_MAPPING
    ("hauptgruppe" oder "hauptgruppe:unterkategorie") in (hauptgruppe,
    unterkategorie)-Paare."""
    ergebnis = []
    for schluessel in config.PRUEF_MECHANISMUS_MAPPING:
        if ":" in schluessel:
            hg, uk = schluessel.split(":", 1)
            ergebnis.append((hg, uk))
        else:
            ergebnis.append((schluessel, None))
    return ergebnis


def _sonden_richtung(hauptgruppe: str) -> str:
    return "aktiv" if hauptgruppe == "absicherung" else "uebergewichten"


def _gegenteil_richtung(richtung: str) -> str:
    if richtung == "aktiv":
        return "inaktiv"
    if richtung == "uebergewichten":
        return "meiden"
    return richtung


def _war_kuerzlich_abgelehnt(conn, these_id: int | None, hauptgruppe: str, unterkategorie: str | None,
                             vorgeschlagene_richtung: str, jetzt: datetime) -> bool:
    """Cooldown-Regel (Abschnitt 15): nach einer Ablehnung wird dieselbe
    Richtung fuer COOLDOWN_TAGE_NACH_ABLEHNUNG Tage nicht erneut
    vorgeschlagen - eine GEGENLAEUFIGE Richtung ist davon nicht betroffen
    (echte Trendwende soll nicht blockiert werden)."""
    letzter = db.get_letzter_entschiedener_vorschlag(conn, these_id, hauptgruppe, unterkategorie)
    if letzter is None or letzter.status != "abgelehnt" or letzter.entschieden_am is None:
        return False
    if letzter.vorgeschlagene_richtung != vorgeschlagene_richtung:
        return False
    entschieden = datetime.fromisoformat(letzter.entschieden_am)
    if entschieden.tzinfo is None:
        entschieden = entschieden.replace(tzinfo=timezone.utc)
    return (jetzt - entschieden).days < COOLDOWN_TAGE_NACH_ABLEHNUNG


def _lade_heutiges_schicht2_ergebnis(conn, jetzt: datetime) -> dict[tuple[str, str | None], dict] | None:
    """Laedt die #333-Schicht-2-Kategorie-Eintraege (agent/kategorie_synthese.py),
    falls fuer HEUTE (gleicher UTC-Kalendertag) vorhanden - sonst None (P-8,
    beide Aufrufer unten fallen dann auf unmoderiertes/unbeschleunigtes
    Verhalten zurueck, identisch zum Stand vor Schicht 2)."""
    ergebnis = db.get_latest_kategorie_synthese_ergebnis(conn)
    if ergebnis is None:
        return None
    erstellt = datetime.fromisoformat(ergebnis.erstellt_am)
    if erstellt.tzinfo is None:
        erstellt = erstellt.replace(tzinfo=timezone.utc)
    if erstellt.date() != jetzt.date():
        return None
    kategorien = json.loads(ergebnis.kategorie_ergebnisse_json)
    return {(e.get("hauptgruppe"), e.get("unterkategorie")): e for e in kategorien}


def richtgroessen_lage(conn) -> dict:
    """Wie steht die Zahl aktiver Thesen zur Richtgroesse 3-6? (2026-08-07, S-2)

    REINE INFORMATION. Weder das Unterschreiten noch das Ueberschreiten
    veraendert das Verhalten - das ist der Punkt: die Spezifikation
    (`Kategorie_Basisinformationen_Release2.md` Abschnitt 5, Punkt 3) sagt
    *"weich in der GUI angezeigt, kein Hard-Limit im Code"*.

    DIE UNTERGRENZE IST DERZEIT DIE INTERESSANTERE. Sechs aktive Thesen klingen
    nach "voll", aber vier davon sind Rohstoffe und zwei stehen auf `neutral` -
    ausserhalb der Rohstoffe traegt praktisch kein Themenfeld eine These. Ein
    Deckel, der bei sechs greift, hat diese Schieflage stabilisiert statt sie
    zu zeigen.
    """
    minimum, maximum = config.richtgroesse_thesen()
    thesen = db.get_aktive_thesen(conn)
    aktive = len(thesen)
    if aktive < minimum:
        lage, hinweis = "unter", (
            "Zu wenige Themenfelder tragen eine These — reife Vorschläge werden "
            "gebraucht, nicht gebremst."
        )
    elif aktive > maximum:
        lage, hinweis = "ueber", (
            "Mehr Thesen als die Richtgröße vorsieht. Das ist erlaubt; ein Blick "
            "auf die schwächsten (Richtung „neutral“, lange ohne Bewegung) lohnt."
        )
    else:
        lage, hinweis = "im_rahmen", "Im Rahmen der Richtgröße."
    # Wie verteilt sich das? Sechs Thesen auf zwei Hauptgruppen sind etwas
    # anderes als sechs auf sechs - die Zahl allein verdeckt genau das.
    je_hauptgruppe: dict[str, int] = {}
    neutrale = 0
    for these in thesen:
        je_hauptgruppe[these.hauptgruppe] = je_hauptgruppe.get(these.hauptgruppe, 0) + 1
        if these.richtung == "neutral":
            neutrale += 1
    return {
        "aktive_thesen": aktive,
        "minimum": minimum,
        "maximum": maximum,
        "lage": lage,
        "hinweis": hinweis,
        "hauptgruppen_abgedeckt": len(je_hauptgruppe),
        "je_hauptgruppe": je_hauptgruppe,
        "davon_neutral": neutrale,
        "anzeige": f"{aktive} aktive Thesen · Richtgröße {minimum}–{maximum}",
    }


# Klartext-Tabellen fuer die Anzeige wartender Vorschlaege (2026-08-07).
# Bewusst hier und nicht in ui/thesen_view.py: Export, Uebersichtsseite und GUI
# sollen dieselben Woerter benutzen - drei Kopien laufen garantiert auseinander.
_RICHTUNG_ANZEIGE = {
    "uebergewichten": "Übergewichten",
    "neutral": "Neutral",
    "meiden": "Meiden",
    "aktiv": "Aktiv",
    "inaktiv": "Inaktiv",
}
_MECHANISMUS_ANZEIGE = {
    "m2_liquiditaet": "M2-Liquidität",
    "cot_positionierung": "CFTC-COT-Positionierung",
    "zinskurve": "Zinskurve (10J minus 2J)",
    "dollar_index": "Dollar-Index-Trend (DXY)",
    "baerenmarkt_overlay": "Bärenmarkt-Overlay",
    "bellwether_sentiment": "Bellwether-Sentiment",
}


def wartende_vorschlaege(conn, jetzt: datetime | None = None) -> dict:
    """Welche Themen-Vorschlaege warten, und wann werden sie reif? (2026-08-07)

    ANLASS. Am 07.08. standen 14 von 16 Vorschlaegen auf "beobachtung" - und
    weder in der GUI noch auf der Uebersichtsseite war erkennbar, dass darunter
    ein KI-Vorschlag seit dem 25.07. laeuft und in 18 Tagen reif wird. Erst die
    Datierung von Hand hat es gezeigt. **Ein Vorlauf, den niemand sieht, ist
    keiner.**

    DIE ZWEITE ZAHL IST DIE WICHTIGERE: `gleichzeitig_reif` zaehlt, wie viele
    Kandidaten am selben Tag reif werden. Am 24./25.08. sind das neun - bei
    einem Budget, das heute null betraegt. Ohne diese Vorschau faellt die
    Entscheidung unter Druck statt mit siebzehn Tagen Vorlauf.

    Reine Lesefunktion, kein Seiteneffekt. Persistenzschwellen und
    Reife-Logik kommen aus denselben Funktionen wie der Job selbst - eine
    zweite Fassung wuerde garantiert auseinanderlaufen (Lehre vom 03.08.).
    """
    jetzt = jetzt or datetime.now(timezone.utc)
    eintraege = []
    for hauptgruppe, unterkategorie in _alle_kategorie_schluessel():
        tracker = db.get_kandidat_in_beobachtung(conn, hauptgruppe, unterkategorie)
        if tracker is None:
            continue
        mechanismus_info = config.get_pruef_mechanismus(hauptgruppe, unterkategorie)
        if mechanismus_info is None:
            continue
        schwelle = _persistenz_tage_fuer_mechanismen(mechanismus_info["mechanismen"])
        seit = datetime.fromisoformat(tracker.beobachtung_seit)
        if seit.tzinfo is None:
            seit = seit.replace(tzinfo=timezone.utc)
        beobachtet = (jetzt - seit).total_seconds() / 86400
        rest = max(0.0, schwelle - beobachtet)
        eintraege.append({
            "hauptgruppe": hauptgruppe,
            "unterkategorie": unterkategorie,
            # Klartext NEBEN den IDs, nicht statt ihnen: die Seite und der
            # Export sollen "Technologie & KI / Künstliche Intelligenz" zeigen,
            # eine Auswertung braucht aber weiter die stabile ID.
            "kategorie_anzeige": (
                config._kategorie_klartext(hauptgruppe, unterkategorie)
                or f"{hauptgruppe}{('/' + unterkategorie) if unterkategorie else ''}"
            ),
            "vorgeschlagene_richtung": tracker.vorgeschlagene_richtung,
            "richtung_anzeige": _RICHTUNG_ANZEIGE.get(
                tracker.vorgeschlagene_richtung, tracker.vorgeschlagene_richtung),
            "mechanismus": tracker.mechanismus_typ,
            "mechanismus_anzeige": _MECHANISMUS_ANZEIGE.get(
                tracker.mechanismus_typ, tracker.mechanismus_typ),
            "beobachtung_seit": tracker.beobachtung_seit,
            "tage_beobachtet": round(beobachtet, 1),
            "schwelle_tage": schwelle,
            "tage_bis_reif": round(rest, 1),
            "reif_am": (seit + timedelta(days=schwelle)).date().isoformat(),
            "ist_reif": beobachtet >= schwelle,
            "ist_schwerpunkt": config.ist_manueller_schwerpunkt(hauptgruppe, unterkategorie),
            # G-5: eine These auf einem Themenfeld ohne handelbares Asset kann
            # nichts ausloesen. Steht hier als Attribut, damit es sichtbar ist -
            # zurueckgestellt wird es in _bestimme_gesperrte_fall_a_kandidaten().
            "handelbare_assets": config.kategorie_handelbare_assets(hauptgruppe, unterkategorie),
        })
    eintraege.sort(key=lambda e: (e["tage_bis_reif"], e["hauptgruppe"]))

    # Wie viele werden am selben Tag reif? Das ist die Zahl, die den Engpass
    # ankuendigt - nicht die Gesamtzahl der Wartenden.
    je_tag: dict[str, int] = {}
    for e in eintraege:
        if not e["ist_reif"]:
            je_tag[e["reif_am"]] = je_tag.get(e["reif_am"], 0) + 1
    engpass_tag, engpass_anzahl = (None, 0)
    if je_tag:
        engpass_tag = max(je_tag, key=je_tag.get)
        engpass_anzahl = je_tag[engpass_tag]

    lage = richtgroessen_lage(conn)
    aktive = lage["aktive_thesen"]
    richtgroesse = lage["maximum"]
    return {
        "vorschlaege": eintraege,
        "anzahl_wartend": sum(1 for e in eintraege if not e["ist_reif"]),
        "anzahl_reif": sum(1 for e in eintraege if e["ist_reif"]),
        "aktive_thesen": aktive,
        "richtgroesse_max": richtgroesse,
        "freies_budget": max(0, richtgroesse - aktive),
        "engpass_am": engpass_tag,
        "engpass_anzahl": engpass_anzahl,
        "richtgroesse_min": lage["minimum"],
        "richtgroessen_lage": lage,
        "lesehilfe": (
            "tage_bis_reif zaehlt bis zur Persistenzschwelle des jeweiligen "
            "Mechanismus (7 Tage Baerenmarkt-Overlay, 14 COT/M2, 30 Zinskurve/"
            "Dollar-Index/Bellwether). engpass_anzahl ist die Zahl der Kandidaten, "
            "die am selben Tag reif werden. Seit 07.08. SPERRT die Richtgroesse "
            "nicht mehr (Spezifikation: 'weich, kein Hard-Limit im Code') - "
            "freies_budget ist Orientierung, kein Gate. Zurueckgestellt wird nur "
            "noch, wenn ein Themenfeld gar kein handelbares Asset hat "
            "(handelbare_assets leer, G-5)."
        ),
    }


def _reife_fall_a_kandidaten(conn, jetzt: datetime) -> list[tuple[str, str | None]]:
    """Kandidaten, die HEUTE - vor diesem Lauf, also auf Basis des
    Tracker-Stands von gestern Abend - die Fall-A-Persistenzschwelle bereits
    erreicht haben. Identische Grundlage wie agent/kategorie_synthese.py::
    _build_kategorie_fakten()s `ist_heute_fall_a_reif` - deshalb muss Schicht 2
    zeitlich VOR diesem Job laufen (siehe scheduler/background.py::
    build_scheduler())."""
    kandidaten = []
    for hauptgruppe, unterkategorie in _alle_kategorie_schluessel():
        if db.get_aktive_these_fuer_kategorie(conn, hauptgruppe, unterkategorie) is not None:
            continue
        tracker = db.get_kandidat_in_beobachtung(conn, hauptgruppe, unterkategorie)
        if tracker is None:
            continue
        mechanismus_info = config.get_pruef_mechanismus(hauptgruppe, unterkategorie)
        if mechanismus_info is None:
            continue
        persistenz_tage = _persistenz_tage_fuer_mechanismen(mechanismus_info["mechanismen"])
        seit = datetime.fromisoformat(tracker.beobachtung_seit)
        if seit.tzinfo is None:
            seit = seit.replace(tzinfo=timezone.utc)
        tage_beobachtet = (jetzt - seit).total_seconds() / 86400
        if tage_beobachtet >= persistenz_tage:
            kandidaten.append((hauptgruppe, unterkategorie))
    return kandidaten


def _bestimme_gesperrte_fall_a_kandidaten(
    conn, jetzt: datetime,
) -> set[tuple[str, str | None]]:
    """Wer wird zurueckgestellt? Seit 2026-08-07 NUR noch aus Qualitaetsgruenden.

    BIS ZUM 07.08. war das hier die Gleichzeitigkeits-Moderation (#333 Schicht 2):
    ein hartes Budget aus der Richtgroesse - wurde es ueberschritten, landeten
    reife Kandidaten stumm als 'offen'. Die Spezifikation sagt aber
    (`Kategorie_Basisinformationen_Release2.md` Abschnitt 5, Punkt 3) ausdruecklich
    *"weich in der GUI angezeigt, kein Hard-Limit im Code"* - implementiert war
    das Gegenteil.

    WARUM DER DECKEL WEG KANN, ohne dass die Rangfolge verwaessert: eine aktive
    These bringt einem Screener-Kandidaten NICHT schon durch ihre Existenz einen
    Bonus, sondern nur, wenn `compute_these_abgleich()` sie objektiv als
    "gestuetzt"/"widerspricht" bestaetigt (agent/aktien/screener.py::
    `_kategorie_score_bonus()`). Mehr Thesen erzeugen also nicht mehr Bonus,
    sondern nur mehr Kandidaten fuer denselben objektiven Test. Das war das
    Hauptargument fuer den Deckel - es traegt nicht.

    WAS BLEIBT: eine These auf einem Themenfeld ohne handelbares Asset kann
    nichts ausloesen (G-5). Das ist ein Qualitaets-, kein Mengenkriterium, und
    genau dafuer wird hier noch zurueckgestellt. Die Richtgroesse selbst wird
    nur noch **berichtet** (siehe `richtgroessen_lage()`), nicht durchgesetzt.
    """
    reife = _reife_fall_a_kandidaten(conn, jetzt)
    if not reife:
        return set()

    # G-5: Themenfeld ohne handelbares Asset (2026-08-07).
    #
    # GEMESSEN, bevor gebaut wurde: aktuell trifft das auf KEINE Kategorie zu -
    # 70 der 72 Unterkategorien haben Katalog-Symbole, die restlichen beiden
    # (absicherung/aktienmarkt_short, absicherung/sektor_short) haengen ueber
    # DBPK und 3QSS an der Watchlist. Eine Pruefung nur ueber den Katalog haette
    # ausgerechnet die zwei Hedge-Kategorien gesperrt, die der Nutzer aktiv
    # haelt. Die Pruefung bleibt trotzdem drin - aber als Wachhund fuer neu
    # angelegte Kategorien, nicht als Filter fuer den heutigen Bestand.
    ohne_assets = {
        k for k in reife if not config.kategorie_handelbare_assets(k[0], k[1])
    }
    if ohne_assets:
        logger.warning(
            "Kategorie-Vorschlaege: %d reife Kandidaten haben KEIN handelbares Asset und werden "
            "zurueckgestellt (%s) - eine These darauf koennte nichts ausloesen.",
            len(ohne_assets), ", ".join(f"{h}/{u or '-'}" for h, u in sorted(ohne_assets)),
        )
    return ohne_assets


def _verarbeite_signal(
    conn, *, these_id: int | None, hauptgruppe: str, unterkategorie: str | None,
    mechanismus_typ: str, vorgeschlagene_richtung: str, begruendung: str, datenstand: str | None,
    persistenz_tage: int, jetzt: datetime,
    automatische_uebernahme_gesperrt: bool = False, schneller_wechsel: bool = False,
) -> None:
    jetzt_iso = jetzt.isoformat()
    if these_id is not None:
        bestehender = db.get_aenderungsvorschlag_in_beobachtung(conn, these_id)
    else:
        bestehender = db.get_kandidat_in_beobachtung(conn, hauptgruppe, unterkategorie)

    if _war_kuerzlich_abgelehnt(conn, these_id, hauptgruppe, unterkategorie, vorgeschlagene_richtung, jetzt):
        if bestehender is not None:
            db.delete_these_aenderungsvorschlag(conn, bestehender.id)
        return

    if bestehender is None or bestehender.vorgeschlagene_richtung != vorgeschlagene_richtung:
        if bestehender is not None:
            # Richtung hat waehrend der Beobachtung gedreht - Serie neu starten.
            db.delete_these_aenderungsvorschlag(conn, bestehender.id)
        neuer = TheseAenderungsvorschlag(
            these_id=these_id, hauptgruppe=None if these_id is not None else hauptgruppe,
            unterkategorie=None if these_id is not None else unterkategorie,
            mechanismus_typ=mechanismus_typ, vorgeschlagene_richtung=vorgeschlagene_richtung,
            begruendung=begruendung, datenstand=datenstand, beobachtung_seit=jetzt_iso,
        )
        db.create_these_aenderungsvorschlag(conn, neuer)
        return

    seit = datetime.fromisoformat(bestehender.beobachtung_seit)
    if seit.tzinfo is None:
        seit = seit.replace(tzinfo=timezone.utc)
    tage_beobachtet = (jetzt - seit).total_seconds() / 86400

    # Schnell-Pfad (#333 Schicht 2, 2026-07-25, NUR Fall B): ein von Schicht 2
    # als akut eingestufter Wechsel ueberspringt die normale Persistenzfrist -
    # spiegelt das Hebel-Kontrathese-Hochkonfidenz-Muster (hebel_risk_gate.py::
    # KONFIDENZ_SCHWELLE_HOCH, sofortige Reaktion statt Zeitfenster-Wartezeit).
    schnell_pfad_ausgeloest = schneller_wechsel and these_id is not None and tage_beobachtet < persistenz_tage
    if tage_beobachtet < persistenz_tage and not schnell_pfad_ausgeloest:
        aktualisiert = TheseAenderungsvorschlag(
            these_id=bestehender.these_id, hauptgruppe=bestehender.hauptgruppe,
            unterkategorie=bestehender.unterkategorie, mechanismus_typ=mechanismus_typ,
            vorgeschlagene_richtung=vorgeschlagene_richtung, begruendung=begruendung, datenstand=datenstand,
            beobachtung_seit=bestehender.beobachtung_seit, erkannt_am=bestehender.erkannt_am,
            status=bestehender.status, entschieden_am=bestehender.entschieden_am,
        )
        db.update_these_aenderungsvorschlag(conn, bestehender.id, aktualisiert)
        return

    # Persistenzschwelle erreicht ODER Schnell-Pfad ausgeloest.
    if these_id is None:
        if automatische_uebernahme_gesperrt:
            # Gleichzeitigkeits-Moderation (#333 Schicht 2): reif, aber durch
            # die Richtgroesse zurueckgestellt - landet als 'offen' zur
            # manuellen Bestaetigung statt automatischer Anlage (siehe
            # ui/thesen_view.py, Fall-A-Zweig im Vorschlags-Panel).
            aktualisiert = TheseAenderungsvorschlag(
                these_id=None, hauptgruppe=hauptgruppe, unterkategorie=unterkategorie,
                mechanismus_typ=mechanismus_typ, vorgeschlagene_richtung=vorgeschlagene_richtung,
                begruendung=begruendung, datenstand=datenstand,
                beobachtung_seit=bestehender.beobachtung_seit, erkannt_am=jetzt_iso,
                status="offen", entschieden_am=None,
            )
            db.update_these_aenderungsvorschlag(conn, bestehender.id, aktualisiert)
            logger.info(
                "Kategorie-Vorschlag: Fall-A-Kandidat reif, aber wegen Gleichzeitigkeits-Moderation "
                "zurueckgestellt (%s/%s, %s)", hauptgruppe, unterkategorie, vorgeschlagene_richtung,
            )
        else:
            pruef_mechanismus = ",".join(config.get_pruef_mechanismus(hauptgruppe, unterkategorie)["mechanismen"])
            neue_these = These(
                hauptgruppe=hauptgruppe, unterkategorie=unterkategorie, richtung=vorgeschlagene_richtung,
                begruendung=begruendung, gesetzt_am=jetzt_iso, pruef_mechanismus=pruef_mechanismus,
                quelle="ki_vorschlag",
            )
            db.create_these(conn, neue_these)
            db.set_these_aenderungsvorschlag_status(conn, bestehender.id, "uebernommen", jetzt_iso)
            logger.info("Kategorie-Vorschlag: neue These automatisch angelegt (%s/%s, %s)", hauptgruppe, unterkategorie, vorgeschlagene_richtung)
    else:
        aktualisiert = TheseAenderungsvorschlag(
            these_id=these_id, hauptgruppe=None, unterkategorie=None, mechanismus_typ=mechanismus_typ,
            vorgeschlagene_richtung=vorgeschlagene_richtung, begruendung=begruendung, datenstand=datenstand,
            beobachtung_seit=bestehender.beobachtung_seit, erkannt_am=jetzt_iso, status="offen", entschieden_am=None,
        )
        db.update_these_aenderungsvorschlag(conn, bestehender.id, aktualisiert)
        if schnell_pfad_ausgeloest:
            logger.info(
                "Kategorie-Vorschlag: Schnell-Pfad ausgeloest, Persistenzfrist uebersprungen "
                "(these_id=%s, %.1f/%d Tage)", these_id, tage_beobachtet, persistenz_tage,
            )
        else:
            logger.info("Kategorie-Vorschlag: Aenderungsaufforderung auf 'offen' gehoben (these_id=%s)", these_id)


def run_kategorie_vorschlaege_job(conn) -> None:
    jetzt = datetime.now(timezone.utc)
    schicht2 = _lade_heutiges_schicht2_ergebnis(conn, jetzt)
    gesperrte_kategorien = _bestimme_gesperrte_fall_a_kandidaten(conn, jetzt)

    # Die Richtgroesse wird BERICHTET, nicht durchgesetzt (2026-08-07, S-2).
    # Sie ist Orientierung fuer den Nutzer - die Spezifikation sagt "weich in
    # der GUI angezeigt, kein Hard-Limit im Code". Eine Zeile im Log, damit die
    # Lage auch ohne GUI nachvollziehbar bleibt.
    lage = richtgroessen_lage(conn)
    if lage["lage"] != "im_rahmen":
        logger.info(
            "Kategorie-Vorschlaege: %d aktive Thesen - %s der Richtgroesse %d-%d. %s",
            lage["aktive_thesen"], "UNTER" if lage["lage"] == "unter" else "UEBER",
            lage["minimum"], lage["maximum"], lage["hinweis"],
        )

    for hauptgruppe, unterkategorie in _alle_kategorie_schluessel():
        mechanismus_info = config.get_pruef_mechanismus(hauptgruppe, unterkategorie)
        if mechanismus_info is None:
            continue
        mechanismen = mechanismus_info["mechanismen"]
        persistenz_tage = _persistenz_tage_fuer_mechanismen(mechanismen)
        mechanismus_typ = ",".join(mechanismen)

        aktive_these = db.get_aktive_these_fuer_kategorie(conn, hauptgruppe, unterkategorie)
        try:
            if aktive_these is not None:
                abgleich = compute_these_abgleich(conn, aktive_these)
                if abgleich is None:
                    continue
                if abgleich.einschaetzung != "widerspricht":
                    laufender = db.get_aenderungsvorschlag_in_beobachtung(conn, aktive_these.id)
                    if laufender is not None:
                        db.delete_these_aenderungsvorschlag(conn, laufender.id)
                    continue
                vorgeschlagene_richtung = _gegenteil_richtung(aktive_these.richtung)
                schneller_wechsel = bool(
                    schicht2 and (schicht2.get((hauptgruppe, unterkategorie)) or {}).get("phase_charakter")
                    == "schneller_wechsel"
                )
                _verarbeite_signal(
                    conn, these_id=aktive_these.id, hauptgruppe=hauptgruppe, unterkategorie=unterkategorie,
                    mechanismus_typ=mechanismus_typ, vorgeschlagene_richtung=vorgeschlagene_richtung,
                    begruendung=abgleich.begruendung, datenstand=abgleich.datenstand,
                    persistenz_tage=persistenz_tage, jetzt=jetzt, schneller_wechsel=schneller_wechsel,
                )
            else:
                sonde_richtung = _sonden_richtung(hauptgruppe)
                sonde = These(
                    hauptgruppe=hauptgruppe, unterkategorie=unterkategorie, richtung=sonde_richtung,
                    begruendung="", gesetzt_am=jetzt.isoformat(),
                )
                abgleich = compute_these_abgleich(conn, sonde)
                if abgleich is None or abgleich.einschaetzung not in ("gestuetzt", "widerspricht"):
                    laufender = db.get_kandidat_in_beobachtung(conn, hauptgruppe, unterkategorie)
                    if laufender is not None:
                        db.delete_these_aenderungsvorschlag(conn, laufender.id)
                    continue
                vorgeschlagene_richtung = (
                    sonde_richtung if abgleich.einschaetzung == "gestuetzt" else _gegenteil_richtung(sonde_richtung)
                )
                _verarbeite_signal(
                    conn, these_id=None, hauptgruppe=hauptgruppe, unterkategorie=unterkategorie,
                    mechanismus_typ=mechanismus_typ, vorgeschlagene_richtung=vorgeschlagene_richtung,
                    begruendung=abgleich.begruendung, datenstand=abgleich.datenstand,
                    persistenz_tage=persistenz_tage, jetzt=jetzt,
                    automatische_uebernahme_gesperrt=(hauptgruppe, unterkategorie) in gesperrte_kategorien,
                )
        except Exception as exc:  # noqa: BLE001 - P-8, eine fehlgeschlagene Kategorie blockiert nicht die anderen
            logger.warning("Kategorie-Vorschlaege-Job: Fehler bei %s/%s: %s", hauptgruppe, unterkategorie, exc)
