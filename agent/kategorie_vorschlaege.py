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

import logging
from datetime import datetime, timezone

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


def _verarbeite_signal(
    conn, *, these_id: int | None, hauptgruppe: str, unterkategorie: str | None,
    mechanismus_typ: str, vorgeschlagene_richtung: str, begruendung: str, datenstand: str | None,
    persistenz_tage: int, jetzt: datetime,
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

    if tage_beobachtet < persistenz_tage:
        aktualisiert = TheseAenderungsvorschlag(
            these_id=bestehender.these_id, hauptgruppe=bestehender.hauptgruppe,
            unterkategorie=bestehender.unterkategorie, mechanismus_typ=mechanismus_typ,
            vorgeschlagene_richtung=vorgeschlagene_richtung, begruendung=begruendung, datenstand=datenstand,
            beobachtung_seit=bestehender.beobachtung_seit, erkannt_am=bestehender.erkannt_am,
            status=bestehender.status, entschieden_am=bestehender.entschieden_am,
        )
        db.update_these_aenderungsvorschlag(conn, bestehender.id, aktualisiert)
        return

    # Persistenzschwelle erreicht.
    if these_id is None:
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
        logger.info("Kategorie-Vorschlag: Aenderungsaufforderung auf 'offen' gehoben (these_id=%s)", these_id)


def run_kategorie_vorschlaege_job(conn) -> None:
    jetzt = datetime.now(timezone.utc)
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
                _verarbeite_signal(
                    conn, these_id=aktive_these.id, hauptgruppe=hauptgruppe, unterkategorie=unterkategorie,
                    mechanismus_typ=mechanismus_typ, vorgeschlagene_richtung=vorgeschlagene_richtung,
                    begruendung=abgleich.begruendung, datenstand=abgleich.datenstand,
                    persistenz_tage=persistenz_tage, jetzt=jetzt,
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
                )
        except Exception as exc:  # noqa: BLE001 - P-8, eine fehlgeschlagene Kategorie blockiert nicht die anderen
            logger.warning("Kategorie-Vorschlaege-Job: Fehler bei %s/%s: %s", hauptgruppe, unterkategorie, exc)
