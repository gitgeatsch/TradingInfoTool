"""Budget-Allocator (2026-07-14, Phase 5, siehe docs/budget_queue_design.md) -
zentrale Tagesbudget-Verteilung ueber die drei KI-Verbraucher (Hebel-
Kandidaten, Marktscan-Kaufkandidaten, Spot-Rotation), huckepack auf dem
15-Min-Takt (scheduler/background.py::hebel_screening_job). Ersetzt den
automatischen Groq-Zweig in marktscan.py::run_scan() und den fixen
05:00-Uhr-signal_batch_job-Cron - beide liefen bisher unabhaengig voneinander
ohne gemeinsame Budget-Kenntnis.

Verteilungsformel (1:1 aus docs/budget_queue_design.md):
    verfuegbar_1_2 = B - F
    tier1_verbraucht = min(anzahl_hebel_kandidaten, verfuegbar_1_2)
    rest_fuer_2 = verfuegbar_1_2 - tier1_verbraucht
    tier2_verbraucht = min(anzahl_marktscan_kandidaten, rest_fuer_2)
    rest_fuer_3 = B - tier1_verbraucht - tier2_verbraucht
    tier3_verbraucht = min(anzahl_faelliger_spot_assets, rest_fuer_3)

FALLBACK-KETTE, STAND 2026-08-09: Gemini -> OpenRouter -> Mistral.

Begruendet mit Durchsatz, Verfuegbarkeit und Vertragslage - AUSDRUECKLICH NICHT
mit Urteilsqualitaet: dafuer gibt es keine Daten (Gemini hat null aufgeloeste
Signale, siehe Regelwerk_Entscheidungslog.md zum 09.08.).

  Gemini zuerst   - einziger Anbieter mit belegtem Durchsatz am ECHTEN
                    Signal-Prompt (5/5 gueltig, Median 5,5 s, 1,00 Versuche je
                    Fall). Der Grund fuer seine bisherige spaete Position -
                    nicht abwaehlbare Trainings-Nutzung - ist durch die
                    Nutzer-Entscheidung vom 08.08. entfallen (siehe unten).
                    Faktisch trug er seit dem 07.08. ohnehin 100 % der Signale.
  OpenRouter 2.   - `nemotron-3-super-120b`, 16/20 am echten Prompt bei Median
                    47,9 s, mit striktem Schema 20,8 s. Echte Redundanz statt
                    einer zweiten Meinung. Der Client rotiert intern ueber
                    FREE_MODELLE - EIN Kettenschritt kann also bis zu drei
                    HTTP-Aufrufe bedeuten.
  Mistral zuletzt - und NICHT wegen der gemessenen -0,49 R: die sind mit dem
                    Zeitraum verwechselt, derselbe Verfall zeigt sich innerhalb
                    von Mistral bei konstantem Anbieter. Die tragenden Gruende:
                    (1) Mistral kehrt ca. 31.08. zurueck und wuerde den
                    Primaerplatz sonst stillschweigend zurueckerobern, ohne dass
                    jemand das entschieden haette; (2) sein neuer Free-Plan ist
                    ein 10-$-Monatsbudget kontoweit - das traegt keine 142
                    Aufrufe pro Tag.

Der Datenschutz-Grund, der OpenRouter bis zum 08.08. aus dieser Kette
heraushielt, ist ENTFALLEN: Gemini hat laut eigener Doku nicht abwaehlbare
Trainings-Nutzung und trug 100 % der Signale - das Regelwerk war also laengst
Trainingsmaterial. Nutzer-Entscheidung 08.08.: Trainings-Nutzung fuer die
Signal-Kette akzeptiert, fuer beide Anbieter gemeinsam.

--- Ab hier HISTORISCH: die Kette VOR dem 2026-08-09 ---------------------

Fallback-Kette (Stand 2026-07-26) Mistral -> Gemini -> Z.ai - Groq wurde
2026-07-26 vollstaendig aus dieser AUTOMATISCHEN Kette entfernt (siehe
Memory project_groq_entfernung_2026-07-26.md): ein reproduzierter
Vergleichstest zeigte "413 Payload Too Large" bei 2 von 3 echten Signal-
Payloads (Free-Tier-Kontextlimit reicht fuer den inzwischen stark
gewachsenen Fakten-Umfang pro Signal nicht mehr aus), plus 0 jemals
aufgeloeste Signale in provider_performance seit Mistral Prio-1 wurde. Der
GroqClient bleibt trotzdem im Projekt (main.py, api/groq.py) - fuer manuelle
Einzelklick-Analysen (ui/hebel_view.py/ui/signals_view.py, niedriges
Volumen, beaufsichtigt) und Qualitaets-/Prompt-Vergleichstests bleibt er ein
nuetzlicher, kostenloser vierter Datenpunkt, nur eben nicht mehr Teil des
unbeaufsichtigten 15-Min-Takts.

Z.ai (Zhipu AI, GLM-4.5-Flash) wurde zunaechst testweise als erste Stufe
VOR Mistral gehaengt (siehe Memory reference_llm_provider_
recherche_uebersicht.md und project_groq_alternative_recherche_2026-07-20.md),
nach der ersten echten Testnacht aber auf die LETZTE Stufe (nach Gemini)
zurueckgestuft: reproduzierte Live-Tests zeigten, dass GLM-4.5-Flash bei
realistischer Payload-Groesse (System-Prompt + Fakten-JSON) ca. 109s fuer
eine Antwort braucht - deutlich zu langsam fuer eine FRUEHE Fallback-Stufe,
die jeden Kandidaten zusaetzlich verzoegern wuerde (siehe auch Memory
project_delta_berechnung_llm_abfrage_timing.md). Als LETZTE Stufe faellt die
zusaetzliche Wartezeit kaum ins Gewicht, da nur genutzt wenn Mistral/Gemini
beide fehlschlagen. Anders als Mistral/Gemini ist die reale Kapazitaet
NICHT ueber ein Nutzer-Dashboard verifiziert - Z.ai veroeffentlicht fuer die
kostenlosen Modelle nur ein Concurrency-Limit (2), keine RPM/TPM/RPD-Zahl.
(HISTORISCH - siehe Nachtrag 2026-07-26/27 unten: Z.ai ist seit dem
Gegenpruefungs-Umbau kein primaerer Analyst mehr, der damalige eigene
Tages-Deckel `zai_taegliches_budget` existiert nicht mehr.)

2026-07-17: Cerebras vollstaendig
entfernt, siehe Memory project_cerebras_free_tier_aenderung_2026-08-17.md -
urspruenglich war geplant, Cerebras erst zum Auslaufen seines kostenlosen
Tiers am 2026-08-17 zu entfernen, der Nutzer hat sich aber bewusst fuer die
sofortige vollstaendige Entfernung entschieden, um nicht spaeter darueber zu
stolpern. Mistral hat Cerebras' bisherige Rolle als zuverlaessige zweite
Stufe uebernommen (echt verifizierte Kapazitaet weit ueber Cerebras/Gemini,
saubere Vertragsbedingungen). Der `CEREBRAS_API_KEY` bleibt einzig in `.env`
als Referenz stehen, jetzt kommentiert als obsolet fuer die Produktion.

(HISTORISCHE BEGRUENDUNG, seit 2026-08-09 ueberholt: "Gemini bleibt bewusst
nahe am Ende der Kette - vertraglich die unguenstigsten Bedingungen aller
Anbieter (EWR/CH/UK-Sonderklausel, explizite Warnung vor vertraulichen/
Finanzdaten, nicht abwaehlbare Trainings-Nutzung), soll deshalb am seltensten
drankommen." Diese Abwaegung ist mit der Nutzer-Entscheidung vom 08.08.
gegenstandslos geworden - siehe oben.)

--- Ende HISTORISCH ------------------------------------------------------

DER MECHANISMUS, unabhaengig von der jeweiligen Reihenfolge: fuer jeden
ausgewaehlten Kandidaten werden die Stufen der Reihe nach versucht. Schlaegt
ein Call fehl (jede Exception - Netzwerk, HTTP-Fehler, Rate-Limit), ist SOFORT
die naechste Stufe an der Reihe. Eine Stufe wird uebersprungen (nicht versucht),
wenn ihr eigener Tages-Deckel erschoepft ist (config
mistral_/gemini_/openrouter_taegliches_budget) oder der Circuit Breaker sie
fuer diesen Lauf gesperrt hat. Kandidaten, die an ALLEN verfuegbaren Stufen
scheitern, bleiben unverarbeitet - kein Datenverlust (P-10), der naechste
15-Min-Lauf bewertet sie automatisch neu. `gemini_client`/`openrouter_client`/
`mistral_client`/`zai_client` sind alle optional (P-8); welche Stufen es
ueberhaupt gibt, entscheidet allein, welche Clients uebergeben werden.

Nachtrag (2026-07-26, Z.ai-Gegenpruefungslogik, siehe agent/krypto/
gegenpruefung.py): Z.ai ist NICHT mehr Teil dieser Fallback-Kette (weder
Hebel noch Marktscan noch Spot) - dediziert fuer eine neue, kleine
Konsistenz-Gegenpruefung freigehalten (kleine Ein-/Ausgabe = schnell, siehe
Modul-Docstring dort). `zai_client` wird stattdessen direkt an
generate_hebel_signal() durchgereicht.

Nachtrag (2026-07-27, Nutzer-Fund): die alte Zai-Budget-Buchhaltung
(`zai_taegliches_budget`, `zai_calls_verbraucht`, `zai_budget_erschoepft`)
wurde jetzt entfernt - sie konnte seit obigem Umbau nie mehr > 0 werden
(Z.ai erscheint in keiner `calls`-Liste mehr), taeuschte also ein
funktionsloses "Z.ai-Tagesbudget" vor. Die ECHTE Z.ai-Last durch die
Gegenpruefung (1 Aufruf/Spot-Signal, 2 Aufrufe/Hebel-Signal - Konsistenz UND
Richtungs-Abgleich sind unabhaengige Calls) wird jetzt stattdessen rein
informativ ueber `database.db.count_zai_gegenpruefung_calls_today()` auf der
Remote-Steuer-Seite angezeigt, bewusst OHNE Tagesdeckel (Z.ai hat laut
Nutzer-Vorgabe keinen, nur den 120/Min-Rate-Limiter im Client selbst).

Echte Tages-Zaehler (2026-07-14-Fix): das Tagesbudget jedes Anbieters wird zu
Beginn jedes Laufs EINMAL aus der DB gelesen (nicht mehr nur eine lokale, bei
jedem 15-Min-Lauf zurueckgesetzte Variable) - vorher konnte eine feste
Tagesgrenze innerhalb eines einzelnen Laufs (max. ~15 Kandidaten) nie erreicht
werden, die Tagesobergrenze wirkte also nie wirklich.

Nachtrag (2026-08-09, Teil B): gelesen wird jetzt ueber
`db.get_llm_budget_zaehler()`, das ECHTE AUFRUFE zaehlt - nicht mehr ueber
`count_real_llm_calls_today_by_provider()`, das Signal-ZEILEN zaehlt. Ein
fehlgeschlagener Aufruf erzeugt keine Zeile: am 07.08. stand Mistrals Zaehler
den ganzen Tag auf 0, waehrend jeder Kandidat dort ein 402 kassierte, und
`mistral_budget_erschoepft` konnte nie True werden. Fuer das QUALITAETS-Tracking
(wer hat dieses Signal erzeugt) bleibt "Datensaetze" richtig - deshalb zwei
getrennte Zaehler statt eines umgebauten."""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

import database.db as db
from agent.krypto.hebel_pipeline import generate_hebel_signal
from agent import provider_sperre
from agent.krypto.llm_provider import llm_model_label
from agent.krypto.marktscan import generate_candidate_writeup, ist_hohes_potential_kandidat
from agent.krypto.pipeline import compute_current_regime, generate_signal
from agent.krypto.signal_batch import (
    SPOT_COOLDOWN_STUNDEN,
    SPOT_COOLDOWN_STUNDEN_AUSGEMUSTERT,
    SPOT_COOLDOWN_STUNDEN_KERN,
    SPOT_COOLDOWN_STUNDEN_RE_EVALUIERUNG,
    select_assets_due_for_signal,
)
from database.models import HebelTrigger, MarktscanCandidate

# Klassifikations-Redesign (2026-07-16, siehe Memory
# project_asset_klassifikation_redesign): offene Hebel-Positionen sind eigene,
# vom Trigger-Screening unabhaengige Investitionsentscheidungen - bekommen
# eine eigene, engere Prioritaetsstufe, unabhaengig davon, ob hebel_screening.py
# fuer dieses Symbol gerade ueberhaupt einen Trigger findet. Nach Schliessen
# der Position faellt das Symbol automatisch zurueck in die normale
# Trigger-basierte Logik (keine gespeicherte Sondermarkierung).
HEBEL_POSITION_COOLDOWN_STUNDEN = 3.0
# Ausgemustert-Stufe fuer Hebel-Trigger, analog Spot - Kern/Taktisch bleiben
# bewusst UNVERAENDERT bei cooldown_stunden (3.5h), nur die neue
# Ausgemustert-Stufe kommt dazu (kleinstmoegliche Aenderung).
HEBEL_COOLDOWN_STUNDEN_AUSGEMUSTERT = 120.0  # 5 Tage

logger = logging.getLogger(__name__)


@dataclass
class AllocationResult:
    hebel_verarbeitet: list[str] = field(default_factory=list)
    marktscan_verarbeitet: list[str] = field(default_factory=list)
    spot_verarbeitet: list[str] = field(default_factory=list)
    provider_je_call: dict[str, str] = field(default_factory=dict)
    fehlgeschlagen: list[str] = field(default_factory=list)
    uebersprungen_cooldown_hebel: int = 0
    uebersprungen_cooldown_marktscan: int = 0
    # Was hat der Circuit Breaker verhindert? Eine Sperre, die niemand sieht,
    # ist die naechste stille Fehlfunktion (Lehre 06.08.).
    provider_sperre_bericht: dict = field(default_factory=dict)
    # DICTS statt Einzelfelder je Anbieter (2026-08-09, C1). Vier feste Felder
    # bedeuteten, dass ein dritter Anbieter zwei weitere braucht - und dass die
    # Zuweisung unten fuer JEDEN Anbieter einzeln ausgeschrieben werden muss.
    # Genau dort war Z.ai 2026-07-27 als Karteileiche haengengeblieben.
    # Geprueft, wer diese Felder liest: NUR zwei Log-Zeilen in
    # scheduler/background.py - keine Persistenz, keine GUI, kein Export.
    calls_verbraucht: dict[str, int] = field(default_factory=dict)
    budget_erschoepft: dict[str, bool] = field(default_factory=dict)
    # 2026-07-14 (Empfehlungs-E-Mails): die echten Signal-/HebelSignal-Objekte
    # zu jedem schluessel aus hebel_verarbeitet/spot_verarbeitet - nur befuellt,
    # wenn provider_je_call[schluessel] ebenfalls gesetzt wurde (also ein
    # ECHTER LLM-Call stattfand, kein Gate-Skip). scheduler/background.py::
    # hebel_screening_job() liest das aus, um E-Mails bei handlungsrelevanten
    # Empfehlungen auszuloesen - budget_allocator.py selbst bleibt frei von
    # E-Mail-Logik (gleiche Trennung wie bei marktscan.py/_notify_marktscan_
    # kaufkandidaten()).
    ergebnis_objekt: dict[str, object] = field(default_factory=dict)


def _cooldown_grenze(cooldown_stunden: float) -> str:
    return (datetime.now(timezone.utc) - timedelta(hours=cooldown_stunden)).isoformat()


def _kern_symbole_hebel(conn, watchlist: list) -> set[str]:
    """Symbole mit "echtem Engagement" (rolle==core ODER Spot-gehalten ODER
    offene Hebel-Position) - identische Definition wie signal_batch.py::
    select_assets_due_for_signal(), hier wiederverwendet fuer die
    Ausgemustert-Praezedenz-Regel (Kern schlaegt IMMER Ausgemustert)."""
    gehaltene_symbole = {
        h.symbol for h in db.get_all_holdings(conn)
        if (h.quantity or 0.0) + (h.staked_quantity or 0.0) > 0.0
    }
    offene_hebel_symbole = {p.symbol for p in db.get_open_hebel_positions(conn)}
    return {
        a.symbol for a in watchlist
        if a.rolle == "core" or a.symbol in gehaltene_symbole or a.symbol in offene_hebel_symbole
    }


def _filter_hebel_cooldown(
    conn, candidates: list[HebelTrigger], watchlist: list, cooldown_stunden: float,
    cooldown_stunden_ausgemustert: float | None = None,
) -> tuple[list[HebelTrigger], int]:
    """Symbol+Richtung mit einem hebel_signals-Eintrag NACH der Cooldown-Grenze
    (echte Analyse, groq_raw_response gesetzt) ausschliessen - verhindert, dass
    ein dauerhaft ausloesendes Symbol (z.B. anhaltend extreme Funding-Rate)
    jeden 15-Min-Zyklus erneut analysiert wird und damit das Budget allein
    aufbraucht.

    Ausgemustert-Stufe (2026-07-16, Klassifikations-Redesign): ein Kandidat,
    dessen Watchlist-Eintrag `beobachtungsstatus == "ausgemustert"` traegt,
    bekommt den laengeren `cooldown_stunden_ausgemustert` statt des
    Standardwerts - AUSSER das Symbol ist "Kern" (siehe
    _kern_symbole_hebel()), dann gilt weiterhin der Standardwert (Praezedenz:
    Kern schlaegt immer Ausgemustert). `cooldown_stunden_ausgemustert=None`
    deaktiviert diese Stufe (altes, einstufiges Verhalten)."""
    grenze_standard = _cooldown_grenze(cooldown_stunden)
    grenze_ausgemustert = (
        _cooldown_grenze(cooldown_stunden_ausgemustert) if cooldown_stunden_ausgemustert is not None else None
    )
    watchlist_by_symbol = {a.symbol: a for a in watchlist}
    kern_symbole = _kern_symbole_hebel(conn, watchlist) if grenze_ausgemustert is not None else set()

    # BUGFIX (2026-07-24, echter NEAR/HYPE-Fund): war bisher die richtungsblinde
    # get_latest_hebel_signal_per_symbol() (GROUP BY symbol) - ein SHORT-Signal
    # fuer dasselbe Symbol liess `sig.richtung == c.richtung` fuer einen LONG-
    # Kandidaten fehlschlagen und den Cooldown damit komplett wirkungslos werden
    # (bestaetigt an echten Exportdaten: Positions-Ueberwachung lief dadurch alle
    # ~15 Min. statt der vorgesehenen hebel_position_cooldown_stunden). Die
    # richtungsabhaengige Variante existierte bereits (siehe deren eigener
    # Docstring, genutzt in hebel_backward_tracking.py), war aber an dieser
    # Cooldown-Pruefung noch nie verdrahtet. Unabhaengig von der Kontrathese-
    # Uebersetzung in hebel_risk_gate.py::post_check_hebel() richtig - schuetzt
    # z.B. auch zwei echte, unabhaengige LONG-/SHORT-Thesen fuer dasselbe Symbol
    # davor, sich gegenseitig den Cooldown zurueckzusetzen.
    #
    # BUGFIX 2 (2026-07-31, echter VIRTUAL-Fund): der obige Fix nutzte
    # `sig.richtung` (die vom LLM FREI gewaehlte Antwort, siehe HebelSignal.
    # richtung-Docstring) statt der tatsaechlich angefragten Richtung. Wenn das
    # LLM ueber viele Zyklen konsistent in die Gegenrichtung antwortet UND der
    # Nur-Long-Deckel (hebel_risk_gate.py, "Nur-Long-Deckel"-Zweig) greift,
    # bleibt `richtung` bewusst auf der LLM-Antwort stehen (siehe dortiger
    # Docstring) - `latest.get((c.symbol, c.richtung))` fand dann nie mehr
    # einen Treffer fuer die angefragte Richtung, der 3,5h-Cooldown griff nie
    # (jeden 15-Min-Zyklus erneut angefragt, live beobachtet ab 31.07. 12:07
    # UTC fuer VIRTUAL). Fix: eigenstaendiges, additiv erfasstes Feld
    # `angefragte_richtung` (siehe HebelSignal-Docstring) + eigene Lookup-
    # Funktion statt der LLM-Antwort-Richtung - betrifft NUR diesen Cooldown-
    # Filter, alle anderen Konsumenten von get_latest_hebel_signal_per_symbol_
    # and_richtung() (Ueberholt-Erkennung, GUI-Historie, regime.py) bleiben
    # unveraendert auf der LLM-eigenen Richtung.
    latest = db.get_latest_hebel_signal_per_symbol_and_angefragte_richtung(conn)
    gefiltert, uebersprungen = [], 0
    for c in candidates:
        asset = watchlist_by_symbol.get(c.symbol)
        if (
            grenze_ausgemustert is not None and asset is not None
            and asset.beobachtungsstatus == "ausgemustert" and c.symbol not in kern_symbole
        ):
            grenze = grenze_ausgemustert
        else:
            grenze = grenze_standard
        sig = latest.get((c.symbol, c.richtung))
        if sig is not None and sig.created_at >= grenze:
            uebersprungen += 1
            continue
        gefiltert.append(c)
    return gefiltert, uebersprungen


def _offene_positionen_als_kandidaten(conn) -> list[HebelTrigger]:
    """Offene Hebel-Positionen als eigene, vom Trigger-Screening unabhaengige
    Kandidatenquelle (2026-07-16, Nutzer-Wunsch: "getaetigte und aktive
    Positionen haben hohe Prioritaet unabhaengig davon, ob es eine Empfehlung
    gab") - garantiert echtem, gehebeltem Engagement eine regelmaessige
    KI-Neubewertung, unabhaengig davon, ob hebel_screening.py fuer dieses
    Symbol gerade ueberhaupt einen Trigger findet. Synthetischer HebelTrigger
    (trigger_zweig=None, ist_kandidat=True) - generate_hebel_signal() braucht
    nur symbol/richtung/trigger_zweig aus dem Trigger-Objekt, alles andere ist
    fuer diesen Pfad irrelevant. Nach Schliessen der Position verschwindet das
    Symbol automatisch aus dieser Quelle (keine gespeicherte Sondermarkierung
    noetig) und faellt in die normale Trigger-basierte Logik zurueck."""
    now_iso = datetime.now(timezone.utc).isoformat()
    return [
        HebelTrigger(
            symbol=pos.symbol, richtung=pos.richtung, screened_at=now_iso,
            screening_run_id="offene_position_monitoring", ist_kandidat=True,
        )
        for pos in db.get_open_hebel_positions(conn)
    ]


def _dedupe_hebel_kandidaten(vorrang: list[HebelTrigger], rest: list[HebelTrigger]) -> list[HebelTrigger]:
    """`vorrang` (offene Positionen) zuerst, `rest` (Trigger-Kandidaten) nur
    fuer noch nicht enthaltene Symbol+Richtung-Kombinationen - verhindert
    einen doppelten LLM-Call fuer dasselbe Symbol, falls eine offene Position
    ZUSAETZLICH einen frischen Trigger hat."""
    gesehen = {(t.symbol, t.richtung) for t in vorrang}
    return vorrang + [t for t in rest if (t.symbol, t.richtung) not in gesehen]


def _filter_marktscan_cooldown(
    conn, candidates: list[MarktscanCandidate], cooldown_stunden: float
) -> tuple[list[MarktscanCandidate], int]:
    """Analog _filter_hebel_cooldown() - get_pending_marktscan_kaufkandidaten()
    filtert nur auf `groq_generiert_am IS NULL` DER NEUESTEN Zeile, ein neuer
    Scan-Lauf legt aber immer eine neue Zeile an (UNIQUE(coingecko_id,
    scan_run_id)) - ohne diesen Zusatz-Check wuerde ein Coin, der vor 20 Min
    bereits eine Begruendung bekam, beim naechsten Scan erneut als "pending"
    erscheinen."""
    grenze = _cooldown_grenze(cooldown_stunden)
    gefiltert, uebersprungen = [], 0
    for c in candidates:
        letzter = db.get_latest_marktscan_writeup_at(conn, c.coingecko_id)
        if letzter is not None and letzter >= grenze:
            uebersprungen += 1
            continue
        gefiltert.append(c)
    return gefiltert, uebersprungen


def _verteile_budget(
    anzahl_hebel: int, anzahl_marktscan: int, anzahl_spot: int, budget_gesamt: int, spot_reserve: int
) -> tuple[int, int, int]:
    """Verteilungsformel 1:1 aus docs/budget_queue_design.md - reine Funktion,
    kein DB-/Netzwerk-Zugriff, damit sie isoliert gegen Grenzfaelle testbar
    ist (siehe Verifikation im Plan)."""
    verfuegbar_1_2 = budget_gesamt - spot_reserve
    tier1_verbraucht = min(anzahl_hebel, max(0, verfuegbar_1_2))
    rest_fuer_2 = verfuegbar_1_2 - tier1_verbraucht
    tier2_verbraucht = min(anzahl_marktscan, max(0, rest_fuer_2))
    rest_fuer_3 = budget_gesamt - tier1_verbraucht - tier2_verbraucht
    tier3_verbraucht = min(anzahl_spot, max(0, rest_fuer_3))
    return tier1_verbraucht, tier2_verbraucht, tier3_verbraucht


def _priorisiere_nach_wartezeit(
    kandidaten: list, wartezeiten: dict, effektive_sla_je_schluessel: dict, schluessel_fn,
) -> list:
    """SLA-Reservierung statt Soft-Boost (2026-07-21, Budget-Allocator-
    Neuplanung, siehe Plan-Datei swift-napping-muffin.md): teilt
    `kandidaten` (bereits DB-seitig nach score_gesamt DESC sortiert) in
    ueberfaellig (wahre Wartezeit >= effektive SLA-Schwelle des jeweiligen
    Kandidaten) und normal. Ueberfaellig wird nach Wartezeit DESC sortiert
    (echtes FIFO: am laengsten wartender zuerst), normal behaelt die
    score_gesamt-DESC-Reihenfolge unveraendert bei (stabiler Filter, kein
    Re-Sort noetig). Der bestehende `[:tier_n]`-Deckel aus
    `_verteile_budget()` bleibt unveraendert der einzige Kappungsmechanismus
    - diese Funktion aendert nur die REIHENFOLGE innerhalb des gleichen
    Budgets, nicht die Anzahl.

    Der Nutzer hat einen reinen Score-Boost je Wartezeit explizit
    abgelehnt ("Prio erhoeht aber Delta kann weiterhin massiv sein - kein
    Boost, sondern eine echte Garantie"): mit einer einfachen Zusatz-
    Gewichtung haette ein noch hoeher gescorter/frischerer Konkurrent einen
    ueberfaelligen Kandidaten weiterhin verdraengen koennen. Die harte
    Zwei-Gruppen-Reservierung hier garantiert dagegen, dass ein
    ueberfaelliger Kandidat NIE von einem normalen verdraengt wird -
    solange die Kapazitaet pro Zyklus die Zahl neu-ueberfaellig-werdender
    Kandidaten nicht uebersteigt (siehe Backtest-Verifikation), konvergiert
    die maximale Wartezeit damit gegen SLA + wenige Zyklen, nicht gegen
    Tage.

    `effektive_sla_je_schluessel` erlaubt eine PRO KANDIDAT unterschiedliche
    Schwelle (Portfolio-Bonus, siehe db.get_portfolio_prioritaets_bonus_
    je_symbol() - ein bereits gehaltenes/rolle=core-Symbol wird schneller
    "ueberfaellig") - fehlt ein Schluessel darin, gilt effektiv 0.0 (sofort
    ueberfaellig), das kommt hier praktisch nie vor, da die Aufrufer stets
    fuer alle `kandidaten` einen Eintrag befuellen."""
    def ist_ueberfaellig(kandidat) -> bool:
        schluessel = schluessel_fn(kandidat)
        return wartezeiten.get(schluessel, 0.0) >= effektive_sla_je_schluessel.get(schluessel, 0.0)

    ueberfaellig = [k for k in kandidaten if ist_ueberfaellig(k)]
    normal = [k for k in kandidaten if not ist_ueberfaellig(k)]
    ueberfaellig.sort(key=lambda k: wartezeiten.get(schluessel_fn(k), 0.0), reverse=True)
    return ueberfaellig + normal


def run_budget_allocator(
    conn_factory,
    watchlist: list,
    coingecko_client,
    kraken_client,
    fred_api_key: str | None,
    config_dict: dict,
    gemini_client=None,
    mistral_client=None,
    zai_client=None,
    on_signal_ready=None,
    openrouter_client=None,
) -> AllocationResult:
    """Kettenreihenfolge seit 2026-08-09: Gemini -> OpenRouter -> Mistral.

    `openrouter_client` steht bewusst HINTER `on_signal_ready` statt bei den
    anderen Clients: alle bestehenden Aufrufer uebergeben ihre Argumente
    benannt, aber ein neuer Parameter in der Mitte waere trotzdem eine Falle
    fuer jeden kuenftigen positionellen Aufruf.

    Ob OpenRouter mitspielt, entscheidet AUSSCHLIESSLICH, ob hier ein Client
    ankommt - dieselbe Bauart wie bei `mistral_client`/`gemini_client`. Der
    Schalter `budget_allocator.openrouter_aktiv` wird deshalb in main.py
    ausgewertet und nicht hier noch einmal: zwei Tore fuer eine Entscheidung
    bedeuten, dass irgendwann eines vergessen wird."""
    cfg = config_dict.get("budget_allocator", {})
    result = AllocationResult()
    if not cfg.get("aktiv", True):
        return result

    budget_gesamt = cfg.get("taegliches_budget_gesamt", 15)
    spot_reserve = cfg.get("spot_rotation_reserve", 5)
    mistral_budget = cfg.get("mistral_taegliches_budget", 150)
    gemini_budget = cfg.get("gemini_taegliches_budget", 200)
    # OpenRouter (2026-08-09, Teil C2). Der Wert steht seit 0753f4e in der
    # config und wurde bis hierher von niemandem gelesen.
    openrouter_budget = cfg.get("openrouter_taegliches_budget", 400)
    cooldown_stunden = cfg.get("cooldown_stunden", 3.5)
    marktscan_kandidat_verfall_stunden = cfg.get("marktscan_kandidat_verfall_stunden", 48.0)
    hebel_cooldown_stunden_ausgemustert = cfg.get(
        "hebel_cooldown_stunden_ausgemustert", HEBEL_COOLDOWN_STUNDEN_AUSGEMUSTERT
    )
    hebel_position_cooldown_stunden = cfg.get(
        "hebel_position_cooldown_stunden", HEBEL_POSITION_COOLDOWN_STUNDEN
    )
    spot_cooldown_stunden = cfg.get("spot_cooldown_stunden", SPOT_COOLDOWN_STUNDEN)
    spot_cooldown_stunden_kern = cfg.get("spot_cooldown_stunden_kern", SPOT_COOLDOWN_STUNDEN_KERN)
    spot_cooldown_stunden_ausgemustert = cfg.get(
        "spot_cooldown_stunden_ausgemustert", SPOT_COOLDOWN_STUNDEN_AUSGEMUSTERT
    )
    spot_cooldown_stunden_re_evaluierung = cfg.get(
        "spot_cooldown_stunden_re_evaluierung", SPOT_COOLDOWN_STUNDEN_RE_EVALUIERUNG
    )

    # GUI-Schalter (2026-07-15, Nutzer-Wunsch): "Nur Long" filtert Hebel-
    # Kandidaten VOR dem Cooldown-Check/LLM-Call heraus, nicht erst
    # nachtraeglich in der Anzeige - direkter Hebel auf die tatsaechliche
    # LLM-Aufrufzahl (siehe Memory project_llm_budget_ueberlast_2026-07-15:
    # 13 von 14 echten ERGOEFFNEN-Empfehlungen waren SHORT, auf Bitpanda
    # aber gar nicht ausfuehrbar).
    # Nachtrag 2026-07-28: aus data/settings.json (geraete-lokal+git-ignoriert)
    # nach config.yaml migriert (siehe Regelwerksmanual-Nachtrag "Nur-Long-
    # Deckel") - wirkt jetzt erst nach Commit+Push+Pull, nicht mehr sofort,
    # dafuer garantiert konsistent zwischen Desktop und Notebook.
    # KEIN Richtungsfilter mehr (2026-08-05). Bis heute warf hier ein
    # hebel_richtung_modus=="nur_long"-Filter alle SHORT-Kandidaten weg, BEVOR
    # sie das LLM sahen (15.07., Begruendung damals woertlich: "jede
    # SHORT-Analyse war faktisch verschwendetes LLM-Budget").
    #
    # Diese Begruendung traegt nicht mehr. Sie entstand, als Groq und Cerebras
    # harte Limits hatten - beide Provider sind entfernt, Mistral erlaubt 300
    # Anfragen pro MINUTE, und der Budget-Realitaetscheck vom 27.07. haelt
    # fest: "kein echtes Provider-Limit mehr, B ist ein reines Pacing-Ventil,
    # keine technische Notwendigkeit".
    #
    # Der Filter schuetzte ohnehin nicht, was er sollte: er filtert
    # `trigger.richtung`, also die Einstufung VOR dem Aufruf - das Modell
    # waehlt seine Richtung frei und drehte LONG-Kandidaten in 120 gemessenen
    # Faellen zu SHORT. Genau dagegen war 2026-07-28 ein zweiter Veto im
    # Risk-Gate nachgeruestet worden, der die Messung verdarb (313
    # SHORT-Vorschlaege lagen als "HALTEN" in der DB).
    #
    # Die Bitpanda-Beschraenkung wirkt seither ausschliesslich an der
    # Praesentationsgrenze: scheduler/background.py::
    # _ist_email_relevante_richtung() und ui/hebel_view.py. Siehe
    # hebel_risk_gate.py::post_check_hebel()-Docstring, "Nachtrag 2026-08-05".

    conn = conn_factory()
    try:
        hebel_pending = db.get_pending_hebel_candidates(conn)
        hebel_trigger_kandidaten, uebersprungen_trigger = _filter_hebel_cooldown(
            conn, hebel_pending, watchlist, cooldown_stunden,
            cooldown_stunden_ausgemustert=hebel_cooldown_stunden_ausgemustert,
        )
        # SLA-Reservierung (2026-07-21, Budget-Allocator-Neuplanung, siehe
        # _priorisiere_nach_wartezeit()-Docstring + Plan-Datei) - Portfolio-
        # Bonus einmal pro Zyklus berechnen, fuer Hebel UND Marktscan
        # wiederverwendet (keine doppelte DB-Abfrage). Bewusst NUR auf
        # hebel_trigger_kandidaten angewandt, NICHT auf
        # offene_positionen_kandidaten - letztere haben kein
        # hebel_trigger_id/keine ist_kandidat=1-Historie (siehe
        # _offene_positionen_als_kandidaten()) und werden von
        # _dedupe_hebel_kandidaten() ohnehin schon immer zuerst
        # eingereiht, brauchen also keine SLA-Sonderbehandlung.
        cfg_hebel_screening = config_dict.get("hebel_screening", {})
        portfolio_bonus = db.get_portfolio_prioritaets_bonus_je_symbol(
            conn, watchlist, cfg.get("bonus_gehalten_stunden", 12.0),
            cfg.get("bonus_kern_rolle_stunden", 6.0),
        )
        hebel_wartezeiten = db.get_hebel_wartezeit_stunden_je_paar(
            conn, cfg_hebel_screening.get("hebel_wartezeit_lookback_tage_cap", 14.0),
            cfg_hebel_screening.get("hebel_kandidat_luecken_toleranz_stunden", 1.5),
        )
        basis_sla_hebel = cfg.get("hebel_kandidat_sla_stunden", 6.0)
        effektive_sla_hebel = {
            (t.symbol, t.richtung): max(0.0, basis_sla_hebel - portfolio_bonus.get(t.symbol, 0.0))
            for t in hebel_trigger_kandidaten
        }
        hebel_trigger_kandidaten = _priorisiere_nach_wartezeit(
            hebel_trigger_kandidaten, hebel_wartezeiten, effektive_sla_hebel,
            lambda t: (t.symbol, t.richtung),
        )
        # Offene Hebel-Positionen: eigene, vom Trigger-Screening unabhaengige
        # Kandidatenquelle mit engerem Cooldown (siehe _offene_positionen_
        # als_kandidaten()-Docstring) - zuerst in die Liste, damit sie im
        # Zweifel vor reinen Trigger-Kandidaten das Tier-1-Budget bekommen.
        # BUGFIX (2026-07-17): "Nur Long" muss auch hier greifen - bisher
        # bekamen offene SHORT-Positionen weiterhin unbegrenzt LLM-Neu-
        # bewertungen (und darüber unnoetige Short-Empfehlungs-E-Mails,
        # siehe _notify_hebel_signal() in scheduler/background.py), obwohl
        # die Einstellung laut eigenem Kommentar oben SHORT-Kandidaten
        # komplett vom LLM fernhalten soll - galt bisher nur fuer frisch
        # entdeckte Trigger-Kandidaten (hebel_pending oben), nicht fuer
        # diesen zweiten, unabhaengigen Kandidatenpfad.
        offene_positionen_roh = _offene_positionen_als_kandidaten(conn)
        offene_positionen_kandidaten, uebersprungen_position = _filter_hebel_cooldown(
            conn, offene_positionen_roh, watchlist, hebel_position_cooldown_stunden,
        )
        hebel_kandidaten = _dedupe_hebel_kandidaten(offene_positionen_kandidaten, hebel_trigger_kandidaten)
        result.uebersprungen_cooldown_hebel = uebersprungen_trigger + uebersprungen_position
        # Info-Leichen-Fix (2026-07-19, Konsistenz-Ausweitung des Hebel-Fixes
        # in hebel_screening.py) - hier statt in marktscan.py::run_scan()
        # platziert, weil der Allocator alle 15 Min laeuft (Marktscan-Discovery
        # nur 2x/Tag) und die Pending-Liste so bei jedem Lauf aktuell bleibt.
        marktscan_kandidat_luecken_toleranz_stunden = cfg.get("marktscan_kandidat_luecken_toleranz_stunden", 20.0)
        marktscan_wartezeit_lookback_tage_cap = cfg.get("marktscan_wartezeit_lookback_tage_cap", 14.0)
        verfallen_marktscan = db.expire_stale_marktscan_candidates(
            conn, marktscan_kandidat_verfall_stunden,
            marktscan_wartezeit_lookback_tage_cap, marktscan_kandidat_luecken_toleranz_stunden,
        )
        if verfallen_marktscan:
            logger.info(
                "Budget-Allocator: %d veraltete Marktscan-Kandidaten (status=neu, aelter als %.0fh) "
                "automatisch auf status=verfallen gesetzt.",
                verfallen_marktscan, marktscan_kandidat_verfall_stunden,
            )
        marktscan_kandidaten, result.uebersprungen_cooldown_marktscan = _filter_marktscan_cooldown(
            conn, db.get_pending_marktscan_kaufkandidaten(conn), cooldown_stunden,
        )
        # SLA-Reservierung, analog Hebel oben (siehe _priorisiere_nach_
        # wartezeit()-Docstring) - portfolio_bonus wurde bereits oben
        # einmal berechnet, hier ueber c.symbol wiederverwendet (Bonus ist
        # je Symbol, get_marktscan_wartezeit_stunden_je_coin() schluesselt
        # dagegen ueber coingecko_id - Zuordnung ueber die Kandidatenliste).
        marktscan_wartezeiten = db.get_marktscan_wartezeit_stunden_je_coin(
            conn, marktscan_wartezeit_lookback_tage_cap, marktscan_kandidat_luecken_toleranz_stunden,
        )
        basis_sla_marktscan = cfg.get("marktscan_kandidat_sla_stunden", 30.0)
        # Reifegrad-Bonus (2026-07-30, Diskussion Punkt 4): "hohes Potential"-
        # Kandidaten (frisch + starker Score, siehe marktscan.py::
        # ist_hohes_potential_kandidat() - dieselbe Definition wie der Mail-1-
        # Hinweis in scheduler/background.py) bekommen zusaetzlich zum
        # portfolio_bonus eine gesenkte SLA, damit sie eher ins naechste Tier-2-
        # Budget-Fenster fallen - analog zum bestehenden portfolio_bonus-Muster,
        # OHNE den Zwei-Eimer-Mechanismus in _priorisiere_nach_wartezeit() selbst
        # zu veraendern.
        reifegrad_bonus_stunden = cfg.get("marktscan_reifegrad_bonus_stunden", 10.0)
        effektive_sla_marktscan = {
            c.coingecko_id: max(
                0.0,
                basis_sla_marktscan - portfolio_bonus.get(c.symbol, 0.0)
                - (reifegrad_bonus_stunden if ist_hohes_potential_kandidat(c, config_dict) else 0.0),
            )
            for c in marktscan_kandidaten
        }
        marktscan_kandidaten = _priorisiere_nach_wartezeit(
            marktscan_kandidaten, marktscan_wartezeiten, effektive_sla_marktscan,
            lambda c: c.coingecko_id,
        )
        # "halte_kriterium scharfschalten" (2026-08-01, siehe db.py::
        # get_symbole_mit_erreichtem_halte_kriterium()-Docstring): macht das
        # bisher rein deskriptive LLM-eigene Kriterium erstmals wirksam -
        # KEIN automatischer Verkauf, nur schnellere Neubewertung.
        re_evaluierung_faellig = db.get_symbole_mit_erreichtem_halte_kriterium(conn, watchlist)
        spot_kandidaten = select_assets_due_for_signal(
            conn, watchlist, max_count=budget_gesamt, cooldown_stunden=spot_cooldown_stunden,
            cooldown_stunden_kern=spot_cooldown_stunden_kern,
            cooldown_stunden_ausgemustert=spot_cooldown_stunden_ausgemustert,
            re_evaluierung_faellig_symbole=re_evaluierung_faellig,
            cooldown_stunden_re_evaluierung=spot_cooldown_stunden_re_evaluierung,
        )
        # Echte Tages-Zaehler (2026-07-14-Fix) - EINMAL pro Lauf aus der DB
        # gelesen, statt einer lokalen Variable, die bei jedem 15-Min-Lauf
        # auf 0 zurueckgesetzt wurde (siehe Modul-Docstring).
        # ECHTE AUFRUFE statt erzeugter Datensaetze (2026-08-09, Teil B).
        #
        # `count_real_llm_calls_today_by_provider()` zaehlt Signal-ZEILEN. Ein
        # fehlgeschlagener Aufruf erzeugt keine Zeile - am 07.08. stand Mistrals
        # Zaehler den ganzen Tag auf 0, waehrend jeder Kandidat dort vergeblich
        # anklopfte und ein 402 kassierte. `mistral_budget_erschoepft` konnte
        # nie True werden. Fuer das QUALITAETS-Tracking ist "Datensaetze"
        # richtig (wer hat dieses Signal erzeugt), als BUDGET-Zaehler ist es
        # falsch - deshalb zwei getrennte Zaehler.
        #
        # `get_api_call_counter_taeglich()` existierte bereits (seit 2026-08-01
        # fuer CoinGecko) und zaehlt echte Aufrufe; geschrieben wird in
        # api/llm_basis.py::zaehle_aufruf().
        #
        # OPENROUTER STEHT HIER MIT EINEM VORBEHALT (2026-08-09, Teil C2). Der
        # DB-Zaehler ist fuer ihn richtig - `zaehle_aufruf()` sitzt in
        # `_ein_call()`, zaehlt also jeden HTTP-Aufruf der Modell-Rotation
        # einzeln. Die Hochzaehlung INNERHALB eines Laufs weiter unten in
        # `_mit_fallback_chain()` addiert dagegen +1 je erzeugtem Signal und
        # liegt damit fuer OpenRouter bis zu dreimal zu niedrig (drei Modelle in
        # der Rotation, dazu 1,31 Versuche je Fall). Das ist bewusst nicht
        # repariert: ein Lauf hat typisch ein bis zwei Kandidaten, und beim
        # naechsten Lauf wird ohnehin wieder aus der DB gelesen - die Abweichung
        # lebt maximal 15 Minuten und korrigiert sich von selbst. Der Tagesdeckel
        # greift also ueber den DB-Wert, nicht ueber die Laufvariable.
        tages_verbraucht = {
            "mistral": db.get_llm_budget_zaehler(conn, "mistral"),
            "gemini": db.get_llm_budget_zaehler(conn, "gemini"),
            "openrouter": db.get_llm_budget_zaehler(conn, "openrouter"),
        }
        # CIRCUIT BREAKER, vorbelegt aus api_health_status (2026-08-07).
        #
        # WARUM DIE VORBELEGUNG NOETIG IST: dieser Lauf hat typisch ein bis zwei
        # Kandidaten (142 Signale auf 96 Laeufe am 07.08.). Eine Sperre, die erst
        # nach drei Fehlschlaegen greift und beim naechsten Lauf vergessen ist,
        # verhindert dann praktisch keinen einzigen vergeblichen Aufruf.
        #
        # WARUM DER ZAEHLER DARUEBER NICHT REICHT: er zaehlt DATENSAETZE, nicht
        # Aufrufe - ein fehlgeschlagener Call erzeugt keine Zeile und bleibt
        # unsichtbar. Deshalb stand fuer Mistral am 07.08. den ganzen Tag 0,
        # waehrend jeder Kandidat dort vergeblich anklopfte.
        #
        # OPENROUTER TEILT SICH `api_health_status` MIT DER GEGENPRUEFUNG
        # (2026-08-09) - beide Verwendungen sind unter derselben Quelle
        # "openrouter" dekoriert. Ein dauerhafter Fehler, den die Gegenpruefung
        # kassiert, sperrt also auch die Signal-Kette. Das ist GEWOLLT und nicht
        # bloss hingenommen: 401/402/403 sind Kontofragen, die gelten fuer jede
        # Verwendung desselben Schluessels gleichermassen. Nur voruebergehende
        # Fehler (429, Timeout) wandern nicht ueber Laufgrenzen - siehe
        # ist_dauerhafter_fehler(); genau deshalb sperrt der 429 von
        # `gemma-4-31b-it:free` hier nichts.
        sperre = provider_sperre.vorbelegte_sperre(conn, ("mistral", "gemini", "openrouter"))
    finally:
        conn.close()
    tages_budget = {
        "mistral": mistral_budget,
        "gemini": gemini_budget,
        "openrouter": openrouter_budget,
    }

    tier1_n, tier2_n, tier3_n = _verteile_budget(
        len(hebel_kandidaten), len(marktscan_kandidaten), len(spot_kandidaten), budget_gesamt, spot_reserve,
    )
    # SLA-Ueberfaellig-Zaehler fuers Log (2026-07-21) - Verlaufskontrolle, ob die
    # neue Reservierung greift (Zaehler sollte gegen 0 tendieren, nicht wachsen).
    hebel_ueberfaellig_n = sum(
        1 for t in hebel_trigger_kandidaten
        if hebel_wartezeiten.get((t.symbol, t.richtung), 0.0) >= effektive_sla_hebel.get((t.symbol, t.richtung), 0.0)
    )
    marktscan_ueberfaellig_n = sum(
        1 for c in marktscan_kandidaten
        if marktscan_wartezeiten.get(c.coingecko_id, 0.0) >= effektive_sla_marktscan.get(c.coingecko_id, 0.0)
    )
    logger.info(
        "Budget-Allocator: Hebel %d/%d (Richtung=%s, ueberfaellig=%d), Marktscan %d/%d (ueberfaellig=%d), "
        "Spot %d/%d ausgewaehlt (B=%d, F=%d), Cooldown uebersprungen: Hebel %d, Marktscan %d, "
        "halte_kriterium faellig: %d",
        tier1_n, len(hebel_kandidaten), "beide (Filter entfernt 2026-08-05)",
        hebel_ueberfaellig_n,
        tier2_n, len(marktscan_kandidaten), marktscan_ueberfaellig_n,
        tier3_n, len(spot_kandidaten),
        budget_gesamt, spot_reserve, result.uebersprungen_cooldown_hebel, result.uebersprungen_cooldown_marktscan,
        len(re_evaluierung_faellig),
    )

    def _mit_conn(fn):
        """Oeffnet/schliesst einen eigenen conn je Aufruf - jeder LLM-Call ist
        potenziell langsam (Netzwerk), eine gemeinsame lang gehaltene
        Connection ueber alle Kandidaten waere unnoetig fehleranfaellig.
        Auch fuer die kurzen Groq-Erschoepfungs-DB-Zugriffe unten
        wiederverwendet (2026-07-20)."""
        conn = conn_factory()
        try:
            return fn(conn)
        finally:
            conn.close()

    def _mit_fallback_chain(schluessel: str, calls: list[tuple[str, object]]) -> bool:
        """Versucht `calls` (Liste von (provider_name, call_fn)) der Reihe nach.
        "mistral"/"gemini" werden nur versucht, wenn ihr echter Tages-Zaehler
        (`tages_verbraucht`) das eigene Budget (`tages_budget`) noch nicht
        erreicht hat - sonst wird diese Stufe uebersprungen (NICHT versucht)
        und die naechste Stufe an der Reihe. Z.ai ist seit 2026-07-26 kein
        Bestandteil von `calls` mehr (siehe Modul-Docstring), taucht hier
        also nie auf.

        Wichtig: ein Datenqualitaets-Gate (Signal.gate_passed/HebelSignal.
        gate_passed == False, z.B. veralteter Preis) schlaegt VOR jedem echten
        LLM-Call fehl - kein Fehler, aber auch KEIN echter Call. Ein Retry an
        der naechsten Stufe waere hier sinnlos (identische zugrundeliegende
        Datenlage), UND `provider_je_call` darf keinen Anbieter zuschreiben,
        der nie tatsaechlich aufgerufen wurde (verfaelscht sonst das in
        docs/budget_queue_design.md geforderte Qualitaets-Tracking)."""
        last_exc: Exception | None = None
        for provider_name, call_fn in calls:
            if provider_name in tages_budget:
                if tages_verbraucht[provider_name] >= tages_budget[provider_name]:
                    result.budget_erschoepft[provider_name] = True
                    continue
            # CIRCUIT BREAKER (2026-08-07): siehe agent/provider_sperre.py.
            if sperre.ist_gesperrt(provider_name):
                continue
            try:
                res = call_fn()
                if getattr(res, "gate_passed", True) is False:
                    # Datenqualitaets-Gate hat VOR jedem echten LLM-Call blockiert - kein
                    # echter Groq-Erfolg, also auch KEIN record_groq_success() hier (wuerde
                    # den Fehlschlag-Zaehler faelschlich auf Basis eines gar nicht
                    # stattgefundenen Calls zuruecksetzen).
                    return True
                sperre.melde_erfolg(provider_name)
                result.provider_je_call[schluessel] = provider_name
                result.ergebnis_objekt[schluessel] = res
                # E-Mail-Latenz-Fix (2026-07-23, echter Fund: ein einzelner Batch-Lauf
                # mit 38 Kandidaten hing 18+ Minuten an langsamen/timeoutenden externen
                # Abrufen fest - da die Benachrichtigung bisher erst NACH vollstaendigem
                # Abschluss von run_budget_allocator() ausgeloest wurde (siehe scheduler/
                # background.py::hebel_screening_job()), blieben laengst fertige echte
                # Signale (NEAR/SUI/VIRTUAL) ohne jede E-Mail haengen. on_signal_ready()
                # feuert stattdessen SOFORT hier, pro Kandidat - Fehler darin duerfen die
                # Allocator-Schleife selbst nie stoppen (P-10), daher eigenes try/except.
                if on_signal_ready is not None:
                    try:
                        on_signal_ready(schluessel, res)
                    except Exception:
                        logger.exception("on_signal_ready-Callback fuer %s fehlgeschlagen", schluessel)
                if provider_name in tages_verbraucht:
                    tages_verbraucht[provider_name] += 1
                    result.calls_verbraucht[provider_name] = tages_verbraucht[provider_name]
                return True
            except Exception as exc:
                last_exc = exc
                logger.info("%s-Call für %s fehlgeschlagen (%s)", provider_name, schluessel, exc)
                sperre.melde_fehlschlag(provider_name, exc)

        logger.warning("Alle Provider für %s fehlgeschlagen (letzter Fehler: %s)", schluessel, last_exc)
        result.fehlgeschlagen.append(schluessel)
        return False

    # --- Tier 1: Hebel ---
    for trigger in hebel_kandidaten[:tier1_n]:
        asset = next((a for a in watchlist if a.symbol == trigger.symbol), None)
        if asset is None:
            continue
        schluessel = f"hebel:{trigger.symbol}:{trigger.richtung}"
        # REIHENFOLGE Gemini -> OpenRouter -> Mistral (2026-08-09, Teil C2).
        # Begruendung im Modul-Docstring - kurz: Durchsatz und Vertragslage,
        # NICHT Urteilsqualitaet.
        calls = []
        if gemini_client is not None:
            calls.append(("gemini", lambda t=trigger, a=asset: _mit_conn(
                lambda c: generate_hebel_signal(
                    t, a, watchlist, c, gemini_client, coingecko_client, kraken_client, fred_api_key,
                    zai_client=zai_client,
                )
            )))
        if openrouter_client is not None:
            calls.append(("openrouter", lambda t=trigger, a=asset: _mit_conn(
                lambda c: generate_hebel_signal(
                    t, a, watchlist, c, openrouter_client, coingecko_client, kraken_client, fred_api_key,
                    zai_client=zai_client,
                )
            )))
        if mistral_client is not None:
            calls.append(("mistral", lambda t=trigger, a=asset: _mit_conn(
                lambda c: generate_hebel_signal(
                    t, a, watchlist, c, mistral_client, coingecko_client, kraken_client, fred_api_key,
                    zai_client=zai_client,
                )
            )))
        # Z.ai (2026-07-26, siehe agent/krypto/gegenpruefung.py) NICHT mehr Teil
        # dieser Fallback-Kette - dediziert fuer die Gegenpruefungslogik
        # freigehalten, wird oben bereits als zai_client durchgereicht.
        ok = _mit_fallback_chain(schluessel, calls)
        if ok:
            result.hebel_verarbeitet.append(schluessel)

    # --- Tier 2: Marktscan-Kaufkandidaten ---
    if tier2_n > 0:
        conn = conn_factory()
        try:
            regime_result = compute_current_regime(conn, coingecko_client, watchlist, fred_api_key, config_dict)
        finally:
            conn.close()

        def _writeup(candidate, llm_client):
            """Gibt seit 2026-07-30 `candidate` (mit frisch gesetztem
            `groq_kurzbegruendung`) zurueck, statt implizit `None` - das Ergebnis
            wird als `res` an `on_signal_ready()` durchgereicht (siehe
            _mit_fallback_chain()) und war zuvor immer `None`, wodurch ein
            spaeterer `"marktscan:"`-Zweig im Dispatcher (scheduler/background.py)
            nie Inhalt gehabt haette."""
            conn = conn_factory()
            try:
                parsed = generate_candidate_writeup(
                    candidate, regime_result, llm_client, kraken_client, conn, watchlist, config_dict,
                    fred_api_key,
                )
                kurzbegruendung = parsed.get("short_reasoning")
                db.update_marktscan_candidate_groq_writeup(
                    conn, candidate.id, kurzbegruendung,
                    json.dumps(parsed.get("long_reasoning") or {}, ensure_ascii=False),
                    llm_model=llm_model_label(llm_client),
                )
                candidate.groq_kurzbegruendung = kurzbegruendung
                return candidate
            finally:
                conn.close()

        for candidate in marktscan_kandidaten[:tier2_n]:
            schluessel = f"marktscan:{candidate.coingecko_id}"
            # REIHENFOLGE Gemini -> OpenRouter -> Mistral (2026-08-09, Teil C2).
            calls = []
            if gemini_client is not None:
                calls.append(("gemini", lambda c=candidate: _writeup(c, gemini_client)))
            if openrouter_client is not None:
                calls.append(("openrouter", lambda c=candidate: _writeup(c, openrouter_client)))
            if mistral_client is not None:
                calls.append(("mistral", lambda c=candidate: _writeup(c, mistral_client)))
            # Z.ai (2026-07-26) NICHT mehr Teil dieser Fallback-Kette - siehe
            # Hebel-Kandidatenschleife oben fuer die Begruendung.
            ok = _mit_fallback_chain(schluessel, calls)
            if ok:
                result.marktscan_verarbeitet.append(schluessel)

    # --- Tier 3: Spot-Rotation ---
    for asset in spot_kandidaten[:tier3_n]:
        schluessel = f"spot:{asset.symbol}"
        # REIHENFOLGE Gemini -> OpenRouter -> Mistral (2026-08-09, Teil C2).
        calls = []
        if gemini_client is not None:
            calls.append(("gemini", lambda a=asset: _mit_conn(
                lambda c: generate_signal(
                    a, watchlist, c, gemini_client, coingecko_client, kraken_client, fred_api_key,
                    zai_client=zai_client,
                    war_re_evaluierung_faellig=a.symbol in re_evaluierung_faellig,
                )
            )))
        if openrouter_client is not None:
            calls.append(("openrouter", lambda a=asset: _mit_conn(
                lambda c: generate_signal(
                    a, watchlist, c, openrouter_client, coingecko_client, kraken_client, fred_api_key,
                    zai_client=zai_client,
                    war_re_evaluierung_faellig=a.symbol in re_evaluierung_faellig,
                )
            )))
        if mistral_client is not None:
            calls.append(("mistral", lambda a=asset: _mit_conn(
                lambda c: generate_signal(
                    a, watchlist, c, mistral_client, coingecko_client, kraken_client, fred_api_key,
                    zai_client=zai_client,
                    war_re_evaluierung_faellig=a.symbol in re_evaluierung_faellig,
                )
            )))
        # Z.ai (2026-07-26) NICHT mehr Teil dieser Fallback-Kette als
        # Primaer-Analyst - wird oben aber bereits als zai_client fuer die
        # Konsistenz-Gegenpruefung durchgereicht (2026-07-27, Ausweitung von
        # Hebel auf Spot, siehe agent/krypto/gegenpruefung.py Modul-Docstring).
        ok = _mit_fallback_chain(schluessel, calls)
        if ok:
            result.spot_verarbeitet.append(schluessel)

    # Was hat der Breaker verhindert? Ohne diese Zeile bliebe die Ersparnis
    # unsichtbar - und eine unsichtbare Sperre ist von einem stillen Ausfall
    # nicht zu unterscheiden.
    result.provider_sperre_bericht = sperre.bericht()
    if result.provider_sperre_bericht["gesamt_uebersprungen"]:
        logger.info(
            "Provider-Sperre: %d Aufrufe uebersprungen (%s)",
            result.provider_sperre_bericht["gesamt_uebersprungen"],
            result.provider_sperre_bericht["gesperrt"],
        )

    return result
