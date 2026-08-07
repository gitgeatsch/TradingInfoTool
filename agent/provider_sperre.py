"""Circuit Breaker fuer die LLM-Fallback-Kette (2026-08-07).

DER ANLASS, gemessen am Export vom 07.08. 15:16. Mistral steht in der Kette an
erster Stelle und lieferte den ganzen Tag `402 Payment Required`. Es gab keinen
Abbruch: jeder einzelne Kandidat versuchte zuerst Mistral, kassierte den Fehler,
fiel auf Gemini - und beim naechsten Kandidaten begann dasselbe von vorn.

    llm_calls_heute:  groq 0, mistral 0, gemini 142
    56 Spot-Signale heute, alle Gemini. 86 Hebel-Signale, alle Gemini.

Also **mindestens 142 vergebliche Versuche an einem Tag**, jeder davon
zusaetzliche Wartezeit vor jedem einzelnen Signal.

WARUM DAS NIEMAND GEMERKT HAT. `count_real_llm_calls_today_by_provider()` zaehlt
DATENSAETZE, nicht Aufrufe - ein fehlgeschlagener Call erzeugt keine Zeile und
ist damit unsichtbar. Fuer das Qualitaets-Tracking war das richtig gedacht,
als Budget-Zaehler ist es falsch: `mistral_budget_erschoepft` konnte nie True
werden, weil der Zaehler auf 0 stehen blieb.

ZWEI FEHLERKLASSEN, ZWEI ANTWORTEN. Ein Netzwerkfehler oder ein 429 sind
voruebergehend - da ist ein zweiter Versuch sinnvoll. Ein **402/401/403** ist es
nicht: das ist Konto oder Berechtigung, und der naechste Versuch in derselben
Sekunde scheitert garantiert genauso. Der Breaker unterscheidet deshalb:

  * dauerhafte Fehlerklasse  -> sofort gesperrt, schon nach dem ERSTEN Vorfall
  * voruebergehende Fehler   -> gesperrt nach MAX_FEHLSCHLAEGE_IN_FOLGE

UND ER BLEIBT NICHT EWIG ZU. Die Sperre wird nicht neu erfunden, sondern aus
`api_health_status` gelesen - dort steht der letzte Fehler ohnehin schon, weil
`api/mistral.py::chat` mit `@track_api_health("mistral")` dekoriert ist. Nach
`PROBE_INTERVALL_STUNDEN` wird wieder EIN Versuch zugelassen (halb offen).
Ohne das wuerde niemand merken, wenn das Kontingent zurueckkommt - und bei
Mistral steht der Reset laut Konto-Dashboard in 24 Tagen an.

GILT FUER BEIDE KETTEN. `budget_allocator.py` und `multi_asset_batch.py`
enthalten dieselbe Schleife zweimal. Dieses Modul wird von beiden benutzt -
zwei Kopien wuerden garantiert auseinanderlaufen (stehende Regel: Rollout ueber
alle Pipelines entscheiden, nicht ueber eine).
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

import database.db as db

logger = logging.getLogger(__name__)

# Wie viele voruebergehende Fehlschlaege in Folge, bevor ein Anbieter fuer den
# Rest des Laufs uebersprungen wird? Drei ist bewusst niedrig: ein Anbieter, der
# dreimal hintereinander scheitert, ist nicht "kurz zuckig", und die Kette hat
# ohnehin eine naechste Stufe.
MAX_FEHLSCHLAEGE_IN_FOLGE = 3

# Nach wie vielen Stunden wird ein gesperrter Anbieter wieder EINMAL probiert?
# Zu kurz und die Sperre bringt nichts; zu lang und ein zurueckgekehrtes
# Kontingent bleibt tagelang ungenutzt. Sechs Stunden heisst: vier Proben pro
# Tag statt 142 vergeblicher Versuche.
PROBE_INTERVALL_STUNDEN = 6

# Fehlertexte, bei denen ein zweiter Versuch garantiert genauso scheitert.
# Bewusst KEIN 429 und kein "rate limit": das sind Wartefehler, keine
# Berechtigungsfehler - dort ist die naechste Runde eine echte Chance.
_DAUERHAFTE_MUSTER = (
    "402", "payment required",
    "401", "unauthorized", "invalid api key", "invalid_api_key",
    "403", "forbidden",
)


def ist_dauerhafter_fehler(fehlertext: str | None) -> bool:
    """Ist ein sofortiger zweiter Versuch sinnlos? Siehe Modul-Docstring."""
    if not fehlertext:
        return False
    text = fehlertext.lower()
    return any(muster in text for muster in _DAUERHAFTE_MUSTER)


@dataclass
class LaufSperre:
    """Der Zustand EINES Laufs. Bewusst kein Modul-Zustand: zwei parallel
    laufende Pipelines duerfen sich nicht gegenseitig Anbieter sperren."""

    gesperrt: dict[str, str] = field(default_factory=dict)
    fehlschlaege_in_folge: dict[str, int] = field(default_factory=dict)
    uebersprungen: dict[str, int] = field(default_factory=dict)

    def ist_gesperrt(self, provider: str) -> bool:
        if provider in self.gesperrt:
            self.uebersprungen[provider] = self.uebersprungen.get(provider, 0) + 1
            return True
        return False

    def melde_fehlschlag(self, provider: str, fehler: BaseException | str) -> None:
        text = str(fehler)
        if ist_dauerhafter_fehler(text):
            # Schon der erste Vorfall genuegt - weiterprobieren waere reines
            # Zeitverbrennen vor jedem einzelnen Signal.
            self.gesperrt[provider] = f"dauerhafter Fehler: {text[:160]}"
            logger.warning(
                "Provider-Sperre: %s fuer den Rest des Laufs gesperrt - %s. "
                "Ein zweiter Versuch scheitert bei dieser Fehlerklasse garantiert genauso.",
                provider, text[:160],
            )
            return
        anzahl = self.fehlschlaege_in_folge.get(provider, 0) + 1
        self.fehlschlaege_in_folge[provider] = anzahl
        if anzahl >= MAX_FEHLSCHLAEGE_IN_FOLGE:
            self.gesperrt[provider] = (
                f"{anzahl} Fehlschlaege in Folge, zuletzt: {text[:120]}")
            logger.warning(
                "Provider-Sperre: %s nach %d Fehlschlaegen in Folge fuer den Rest des "
                "Laufs gesperrt (zuletzt: %s)", provider, anzahl, text[:120],
            )

    def melde_erfolg(self, provider: str) -> None:
        self.fehlschlaege_in_folge[provider] = 0

    def bericht(self) -> dict:
        """Was hat die Sperre in diesem Lauf verhindert? Gehoert ins Log und in
        den Export - eine Sperre, die niemand sieht, ist die naechste stille
        Fehlfunktion."""
        return {
            "gesperrt": dict(self.gesperrt),
            "uebersprungene_versuche": dict(self.uebersprungen),
            "gesamt_uebersprungen": sum(self.uebersprungen.values()),
        }


def vorbelegte_sperre(conn, provider_namen, jetzt: datetime | None = None) -> LaufSperre:
    """Sperre fuer einen neuen Lauf, vorbelegt aus `api_health_status`.

    OHNE DIESE VORBELEGUNG BRINGT DER BREAKER FAST NICHTS. Das Hebel-Screening
    laeuft alle 15 Minuten, und die meisten Laeufe haben nur ein bis zwei
    Kandidaten - eine Sperre, die erst nach drei Fehlschlaegen greift und beim
    naechsten Lauf vergessen ist, verhindert dann praktisch keinen Aufruf.
    Gerechnet auf den 07.08.: 142 Signale auf 96 Laeufe.

    Deshalb wird der letzte bekannte Fehler mitgenommen - er steht ohnehin
    schon in `api_health_status`, weil die Clients dekoriert sind. Nach
    PROBE_INTERVALL_STUNDEN wird wieder EIN Versuch zugelassen; sonst bliebe
    ein zurueckgekehrtes Kontingent unbemerkt.
    """
    jetzt = jetzt or datetime.now(timezone.utc)
    sperre = LaufSperre()
    try:
        status = db.get_api_health_status(conn)
    except Exception as exc:  # noqa: BLE001 - fehlende Tabelle darf nichts toeten
        logger.info("Provider-Sperre: api_health_status nicht lesbar (%s)", exc)
        return sperre

    for provider in provider_namen:
        eintrag = status.get(provider)
        if not eintrag or eintrag.get("status") != "fehler":
            continue
        if not ist_dauerhafter_fehler(eintrag.get("last_error_message")):
            # Voruebergehende Fehler werden NICHT ueber Laufgrenzen hinweg
            # gemerkt - sonst sperrte ein einzelner Netzwerkhaenger den
            # Anbieter fuer Stunden aus.
            continue
        letzter_fehler = _als_zeit(eintrag.get("last_error_at"))
        if letzter_fehler is None:
            continue
        alter_stunden = (jetzt - letzter_fehler).total_seconds() / 3600
        if alter_stunden >= PROBE_INTERVALL_STUNDEN:
            logger.info(
                "Provider-Sperre: %s war gesperrt, letzter dauerhafter Fehler ist "
                "%.1f Stunden alt - dieser Lauf probiert wieder (halb offen).",
                provider, alter_stunden,
            )
            continue
        sperre.gesperrt[provider] = (
            f"seit {alter_stunden:.1f} h dauerhaft fehlerhaft: "
            f"{str(eintrag.get('last_error_message'))[:140]}")
        logger.warning(
            "Provider-Sperre: %s wird in diesem Lauf uebersprungen - letzter Fehler vor "
            "%.1f h war dauerhafter Art (%s). Naechste Probe in %.1f h.",
            provider, alter_stunden, str(eintrag.get("last_error_message"))[:120],
            PROBE_INTERVALL_STUNDEN - alter_stunden,
        )
    return sperre


def _als_zeit(wert: str | None) -> datetime | None:
    if not wert:
        return None
    try:
        stand = datetime.fromisoformat(wert)
    except ValueError:
        return None
    return stand if stand.tzinfo else stand.replace(tzinfo=timezone.utc)
