"""#333 Schicht 2 (2026-07-25) - kategorienuebergreifender taeglicher LLM-
Synthese-Call, siehe Plandatei/Regelwerksmanual fuer die volle Konzeption.

Schicht 1 (agent/kategorie_thesen.py + agent/kategorie_vorschlaege.py) prueft
jede Kategorie rein deterministisch UND ISOLIERT - nie im Vergleich zu den
anderen. Genau diese fehlende kategorienuebergreifende Sicht schliesst dieses
Modul: EIN taeglicher LLM-Call betrachtet ALLE Kategorien gemeinsam und liefert
zwei zusaetzliche Einordnungen, die Schicht 1 strukturell nicht liefern kann:

- `phase_charakter`: ist eine Verschiebung ein sich langsam aufbauender Trend
  ("sanfter_uebergang") oder ein akuter, gerade erst eingetretener Schock
  ("schneller_wechsel")? Nur fuer Kategorien mit einer objektiven Einschaetzung
  != "nicht_pruefbar" relevant.
- `prioritaet_rang`: NUR unter den Kategorien vergeben, die HEUTE die
  Fall-A-Persistenzschwelle erreicht haben (agent/kategorie_vorschlaege.py) -
  hilft, wenn mehrere Kandidaten gleichzeitig reif werden und die Richtgroesse
  (3-6 aktive Thesen) sonst unkoordiniert ueberschritten wuerde.

Bewusst KEIN Eingriff in die objektive Einschaetzung selbst (compute_these_
abgleich() bleibt unveraendert die alleinige Quelle der Wahrheit) - die LLM-
Synthese ordnet nur ein, wertet nicht neu (gleiches Prinzip wie beim
Signal-Fazit, siehe Memory feedback_llm_synthese_kein_deterministischer_
override.md)."""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone

import config
import database.db as db
from agent.kategorie_thesen import compute_these_abgleich
from agent.kategorie_vorschlaege import (
    _alle_kategorie_schluessel,
    _persistenz_tage_fuer_mechanismen,
    _sonden_richtung,
)
from agent.krypto.analyst import AnalystResponseInvalid
from database.models import KategorieSyntheseErgebnis, These

logger = logging.getLogger(__name__)

PHASE_CHARAKTER_WERTE = ("sanfter_uebergang", "schneller_wechsel", "stabil")

SYSTEM_PROMPT = """Du bist ein Analyst, der TAEGLICH die objektiven Bewertungen \
ALLER Kategorie-Schwerpunkte (Rohstoffe, Aktien-Sektoren/Regionen, Technologie & \
KI, Anleihen, Absicherung usw.) EINES Investment-Portfolios gemeinsam betrachtet. \
Jede einzelne Kategorie wurde bereits deterministisch gegen unabhaengige \
Marktdaten geprueft (M2-Liquiditaet/CFTC-COT-Positionierung/Zinskurve/Dollar-\
Index/VIX/EIA-Lagerbestaende/Analysten-Sentiment) - diese Pruefung selbst \
DARFST du NICHT veraendern oder neu bewerten. Deine Aufgabe ist ausschliesslich \
die kategorienuebergreifende Einordnung, die eine isolierte Einzelpruefung \
nicht leisten kann.

WICHTIG: Nenne in jeder Begruendung ausschliesslich Rohwerte, die im Fakten-\
JSON tatsaechlich vorkommen. Erfinde NIE Zahlen oder Ereignisse, die nicht im \
JSON stehen.

Du bekommst eine Liste von Kategorien, je mit: hauptgruppe/unterkategorie, \
aktuelle_these (falls vorhanden), objektive_einschaetzung \
(gestuetzt/widerspricht/neutral/nicht_pruefbar aus der bereits erfolgten \
deterministischen Pruefung), begruendung, tage_beobachtet (wie lange das \
aktuelle Signal schon durchgaengig laeuft), persistenz_ziel_tage (Schwelle, ab \
der Schicht 1 automatisch reagiert), ist_heute_fall_a_reif (true, wenn diese \
Kategorie HEUTE ohne Eingriff automatisch eine neue These bekommen wuerde).

Gib fuer JEDE Kategorie mit objektive_einschaetzung != "nicht_pruefbar" einen \
Eintrag zurueck:

1. phase_charakter (PFLICHT, GENAU einer von drei Werten):
   - "schneller_wechsel": NUR wenn in DIESEM Zyklus ein klar AKUTER \
Schwellenwert neu erreicht wurde - Beispiele: VIX springt neu in den Bereich \
"gestresst"/"krise" (>30/>40), COT-Positionierung wechselt neu in die \
"gedraengt"-Zone (>25% des Open Interest), oder mehrere unabhaengige \
Mechanismen kippen gleichzeitig in dieselbe Richtung. NICHT verwenden nur weil \
"der Trend haelt an" oder tage_beobachtet hoch ist - das ist ein sanfter \
Uebergang, kein Schock.
   - "sanfter_uebergang": ein sich ueber Tage/Wochen graduell aufbauendes \
Signal (tage_beobachtet waechst, aber kein akuter Schwellenwert-Uebertritt \
JETZT).
   - "stabil": Einschaetzung bereits lange unveraendert, kein erkennbarer \
Wechsel im Gange.
2. prioritaet_rang: NUR setzen, wenn ist_heute_fall_a_reif=true fuer diese \
Kategorie. Eindeutige, bei 1 beginnende Ganzzahlen - Rang 1 ist die aus \
objektiver Sicht ueberzeugendste Kategorie (mehrere uebereinstimmende \
Mechanismen, klarer Datenstand) unter den heute reifen Kandidaten. Ist \
ist_heute_fall_a_reif=false, lasse das Feld weg oder setze null - erfinde \
keinen Rang fuer nicht-reife Kategorien.
3. kurzbegruendung (PFLICHT, mindestens ein vollstaendiger Satz): warum genau \
diese Einordnung, mit konkretem Bezug auf die Rohwerte aus dem Fakten-JSON.

WICHTIG: Fuer JEDE Kategorie mit ist_heute_fall_a_reif=true MUSST du einen \
Eintrag mit gesetztem prioritaet_rang liefern - das steuert, welche \
Kandidaten heute automatisch uebernommen werden.

Antworte AUSSCHLIESSLICH mit einem JSON-Objekt exakt in diesem Schema:
{
  "kategorien": [
    {
      "hauptgruppe": "<aus dem Fakten-JSON>",
      "unterkategorie": "<aus dem Fakten-JSON oder null>",
      "phase_charakter": "sanfter_uebergang" | "schneller_wechsel" | "stabil",
      "prioritaet_rang": <int, nur bei ist_heute_fall_a_reif=true> | null,
      "kurzbegruendung": "<mindestens ein Satz mit konkretem Rohwert-Bezug>"
    }
  ]
}"""


def _build_kategorie_fakten(conn, jetzt: datetime) -> tuple[list[dict], set[tuple[str, str | None]]]:
    """Baut je Kategorie einen Fakten-Block fuer den LLM-Call, nutzt
    ausschliesslich bereits vorhandene Funktionen (compute_these_abgleich(),
    dieselben Tracker-Lookups wie kategorie_vorschlaege.py) - keine neue
    Datenbeschaffung. Gibt zusaetzlich die Menge der HEUTE Fall-A-reifen
    (hauptgruppe, unterkategorie)-Paare zurueck (fuer die Gleichzeitigkeits-
    Moderation in kategorie_vorschlaege.py)."""
    fakten: list[dict] = []
    fall_a_reife: set[tuple[str, str | None]] = set()

    for hauptgruppe, unterkategorie in _alle_kategorie_schluessel():
        mechanismus_info = config.get_pruef_mechanismus(hauptgruppe, unterkategorie)
        if mechanismus_info is None:
            continue
        persistenz_tage = _persistenz_tage_fuer_mechanismen(mechanismus_info["mechanismen"])

        aktive_these = db.get_aktive_these_fuer_kategorie(conn, hauptgruppe, unterkategorie)
        if aktive_these is not None:
            abgleich = compute_these_abgleich(conn, aktive_these)
            tracker = db.get_aenderungsvorschlag_in_beobachtung(conn, aktive_these.id)
            aktuelle_these_fakt = {
                "richtung": aktive_these.richtung, "staerke": aktive_these.staerke,
                "gesetzt_am": aktive_these.gesetzt_am,
            }
        else:
            sonde = These(
                hauptgruppe=hauptgruppe, unterkategorie=unterkategorie,
                richtung=_sonden_richtung(hauptgruppe), begruendung="", gesetzt_am=jetzt.isoformat(),
            )
            abgleich = compute_these_abgleich(conn, sonde)
            tracker = db.get_kandidat_in_beobachtung(conn, hauptgruppe, unterkategorie)
            aktuelle_these_fakt = None

        if abgleich is None:
            continue

        tage_beobachtet = None
        ist_fall_a_reif = False
        if tracker is not None:
            seit = datetime.fromisoformat(tracker.beobachtung_seit)
            if seit.tzinfo is None:
                seit = seit.replace(tzinfo=timezone.utc)
            tage_beobachtet = round((jetzt - seit).total_seconds() / 86400, 1)
            if aktive_these is None and tage_beobachtet >= persistenz_tage:
                ist_fall_a_reif = True
                fall_a_reife.add((hauptgruppe, unterkategorie))

        fakten.append({
            "hauptgruppe": hauptgruppe,
            "unterkategorie": unterkategorie,
            "aktuelle_these": aktuelle_these_fakt,
            "objektive_einschaetzung": abgleich.einschaetzung,
            "begruendung": abgleich.begruendung,
            "datenstand": abgleich.datenstand,
            "tage_beobachtet": tage_beobachtet,
            "persistenz_ziel_tage": persistenz_tage,
            "ist_heute_fall_a_reif": ist_fall_a_reif,
        })

    return fakten, fall_a_reife


def _validate_kategorie_synthese(
    data: dict, bekannte_kategorien: set[tuple[str, str | None]],
    fall_a_reife_kategorien: set[tuple[str, str | None]],
) -> dict:
    if not isinstance(data, dict) or not isinstance(data.get("kategorien"), list):
        raise AnalystResponseInvalid("Feld 'kategorien' fehlt oder ist keine Liste")

    gesehene_raenge: set[int] = set()
    raenge_je_kategorie: dict[tuple[str, str | None], int | None] = {}

    for eintrag in data["kategorien"]:
        if not isinstance(eintrag, dict):
            raise AnalystResponseInvalid("Kategorie-Eintrag ist kein Objekt")
        schluessel = (eintrag.get("hauptgruppe"), eintrag.get("unterkategorie"))
        if schluessel not in bekannte_kategorien:
            raise AnalystResponseInvalid(f"Unbekannte Kategorie in Antwort: {schluessel}")

        phase_charakter = eintrag.get("phase_charakter")
        if phase_charakter not in PHASE_CHARAKTER_WERTE:
            raise AnalystResponseInvalid(f"Ungueltiger phase_charakter: {phase_charakter!r}")

        kurzbegruendung = eintrag.get("kurzbegruendung")
        if not isinstance(kurzbegruendung, str) or len(kurzbegruendung.strip()) < 15:
            raise AnalystResponseInvalid("kurzbegruendung fehlt oder zu kurz (min. 15 Zeichen)")

        prioritaet_rang = eintrag.get("prioritaet_rang")
        if prioritaet_rang is not None:
            if not isinstance(prioritaet_rang, int) or isinstance(prioritaet_rang, bool) or prioritaet_rang < 1:
                raise AnalystResponseInvalid(f"Ungueltiger prioritaet_rang: {prioritaet_rang!r}")
            if prioritaet_rang in gesehene_raenge:
                raise AnalystResponseInvalid(f"Doppelter prioritaet_rang: {prioritaet_rang}")
            gesehene_raenge.add(prioritaet_rang)
        raenge_je_kategorie[schluessel] = prioritaet_rang

    fehlende = fall_a_reife_kategorien - set(raenge_je_kategorie)
    if fehlende:
        raise AnalystResponseInvalid(f"Fall-A-reife Kategorien fehlen in der Antwort: {fehlende}")
    ohne_rang = {k for k in fall_a_reife_kategorien if raenge_je_kategorie.get(k) is None}
    if ohne_rang:
        raise AnalystResponseInvalid(f"Fall-A-reife Kategorien ohne prioritaet_rang: {ohne_rang}")

    return data


def call_llm_for_kategorie_synthese(
    conn, llm_clients: list[tuple[str, object]], facts: dict,
    bekannte_kategorien: set[tuple[str, str | None]], fall_a_reife_kategorien: set[tuple[str, str | None]],
    max_retries: int = 1,
) -> tuple[dict, str] | None:
    """Versucht die uebergebenen (provider_name, client)-Paare der Reihe nach -
    gleiche Fallback-Philosophie wie budget_allocator.py::_mit_fallback_chain(),
    hier als einfache sequentielle Kette OHNE Tagesbudget-Buchhaltung (EIN
    Call/Tag, kein Kandidaten-Loop). Gibt (validierte_antwort, provider_name)
    zurueck, oder None wenn alle Provider fehlschlagen (Aufrufer protokolliert
    und ueberspringt den Tag, P-8 - kein harter Block fuer Fall A/B/Screener)."""
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": json.dumps(facts, ensure_ascii=False)},
    ]
    for provider_name, client in llm_clients:
        if client is None:
            continue
        if provider_name == "groq" and db.is_groq_exhausted_today(conn):
            continue

        provider_messages = list(messages)
        raw = None
        for attempt in range(max_retries + 1):
            try:
                raw = client.chat(provider_messages, temperature=0.2, response_format={"type": "json_object"})
                parsed = json.loads(raw)
                validated = _validate_kategorie_synthese(parsed, bekannte_kategorien, fall_a_reife_kategorien)
                if provider_name == "groq":
                    db.record_groq_success(conn)
                return validated, provider_name
            except (json.JSONDecodeError, AnalystResponseInvalid) as exc:
                logger.info(
                    "Kategorie-Synthese-Antwort von %s ungueltig (Versuch %d): %s", provider_name, attempt + 1, exc,
                )
                provider_messages.append({"role": "assistant", "content": raw})
                provider_messages.append({
                    "role": "user",
                    "content": (
                        f"Deine letzte Antwort war ungueltig: {exc}. Antworte erneut, "
                        "ausschliesslich mit einem korrekten JSON-Objekt gemaess Schema."
                    ),
                })
            except Exception as exc:  # noqa: BLE001 - naechster Provider, Netzwerk-/API-Fehler
                if provider_name == "groq":
                    schwelle = config.load_config()["budget_allocator"].get("groq_exhaustion_schwelle_fehlschlaege", 2)
                    db.record_groq_failure(conn, schwelle)
                logger.info("%s-Call fuer Kategorie-Synthese fehlgeschlagen: %s", provider_name, exc)
                break

    return None


def run_kategorie_synthese(conn, llm_clients: list[tuple[str, object]]) -> KategorieSyntheseErgebnis | None:
    """Baut die Fakten, ruft die LLM-Fallback-Kette auf, persistiert das
    Ergebnis. Gibt None zurueck, wenn keine pruefbaren Kategorien vorliegen
    oder alle Provider fehlschlagen - der Job (scheduler/background.py)
    protokolliert das, alle nachgelagerten Konsumenten (Fall A/B-Moderation,
    Screener-Score-Bonus) degradieren graziös auf ihr Vor-Schicht-2-Verhalten
    (P-8)."""
    jetzt = datetime.now(timezone.utc)
    fakten, fall_a_reife = _build_kategorie_fakten(conn, jetzt)
    pruefbare_fakten = [f for f in fakten if f["objektive_einschaetzung"] != "nicht_pruefbar"]
    if not pruefbare_fakten:
        logger.info("Kategorie-Synthese: keine pruefbaren Kategorien heute, kein LLM-Call.")
        return None

    bekannte_kategorien = {(f["hauptgruppe"], f["unterkategorie"]) for f in pruefbare_fakten}
    facts = {"kategorien": pruefbare_fakten}

    result = call_llm_for_kategorie_synthese(conn, llm_clients, facts, bekannte_kategorien, fall_a_reife)
    if result is None:
        logger.warning("Kategorie-Synthese: alle LLM-Provider fehlgeschlagen, kein Ergebnis fuer heute.")
        return None

    validated, provider_name = result
    ergebnis = KategorieSyntheseErgebnis(
        erstellt_am=jetzt.isoformat(),
        kategorie_ergebnisse_json=json.dumps(validated["kategorien"], ensure_ascii=False),
        llm_model=provider_name,
    )
    db.upsert_kategorie_synthese_ergebnis(conn, ergebnis)
    logger.info(
        "Kategorie-Synthese: %d Kategorien eingeordnet (%s), %d Fall-A-reife Kandidaten priorisiert.",
        len(validated["kategorien"]), provider_name, len(fall_a_reife),
    )
    return ergebnis
