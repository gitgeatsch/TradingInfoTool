"""Status-Aggregator fuer die Remote-Steuer-Seite (2026-07-11, siehe
Basisinfos/Regelwerksmanual.md Kap. 12/13). Reine Datenbeschaffung, KEINE
Flask-Abhaengigkeit - eigenstaendig testbar, gleiches Trennungsprinzip wie
staleness.py (Domaenenlogik) vs. ui/formatting.py (Anzeige)."""
from __future__ import annotations

import logging
import sqlite3
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

import config as config_module
import database.db as db
import scheduler.background as background
from staleness import is_price_stale

logger = logging.getLogger(__name__)

_TREFFER_EINSTUFUNGEN = {"kaufkandidat", "watchlist_wuerdig"}


# Entfernte LLM-Provider (2026-08-05, Nutzer-Vorgabe "alle groq und cerebras
# infos ausblenden bzw entfernen"). Beide sind laengst aus dem Betrieb
# genommen - Cerebras vollstaendig, Groq ebenso -, ihre historischen Zeilen
# stehen aber weiterhin in provider_performance, veto_schatten_performance,
# gesamt_signalqualitaet, provider_sendezaehler, llm_calls_heute und
# api_health. Auf einer Statusseite gelesen wirkt das wie ein aktiver
# Provider, der nichts liefert.
#
# NUR DIE ANZEIGE wird gefiltert. Die Daten bleiben in Datenbank und Export
# vollstaendig - dort gehoeren sie hin, weil alte Auswertungen sonst ihre
# Vergleichsgrundlage verlieren.
_ENTFERNTE_PROVIDER = ("groq", "cerebras")


# ---------------------------------------------------------------------------
# Zwischenspeicher fuer die teuren Aggregate (2026-08-09)
#
# DER VORFALL. Das Notebook stand dauerhaft bei ~94 % CPU, `python.exe` allein
# bei 70,9 %, dazu 1,0 MB/s Dauer-Leselast auf der Platte - ohne einen einzigen
# Fehler im Log, weil es sich um voellig normale Lesezugriffe handelt.
#
# DIE URSACHE IST EINE RECHENAUFGABE JE ANFRAGE. `remote/server.py` laesst die
# Seite per `setInterval(refreshStatus, 2000)` alle zwei Sekunden abrufen, und
# `build_status()` rechnet dabei jedes Mal saemtliche Aggregate neu. Gemessen am
# 09.08. auf einer Kopie der Produktions-DB, MIT bereits vorgewaermtem
# Systemguete-Cache:
#
#     build_status() gesamt                1,39 s   je Abruf, Takt 2,0 s
#       _get_themenfeld_erfolg             0,473 s
#       _get_gesamt_signalqualitaet        0,123 s
#       _get_ausstiegs_empfehlungen        0,120 s
#       _get_hedge_wirksamkeit             0,101 s
#       _get_provider_sendezaehler         0,101 s
#
# Schon am DESKTOP bleiben damit nur 30 % Luft. Das Notebook (i5-4300U von 2013)
# muss lediglich 1,5-mal langsamer sein, damit ein Abruf laenger dauert als der
# Takt - ab da ueberlappen die Anfragen, und jede verzoegert die naechste
# weiter. Genau dieser Ausfall ist am 03.08. schon einmal aufgetreten und wurde
# damals NUR fuer die Systemguete behoben (siehe _SYSTEMGUETE_CACHE unten).
#
# WARUM EIN ZWISCHENSPEICHER NICHTS KOSTET. Alle betroffenen Groessen speisen
# sich aus den `outcome_*`-Spalten oder der Kurshistorie. Erstere schreibt nur
# der taegliche Backward-Tracking-Lauf um 06:00, letztere der Preis-Refresh alle
# 15 Minuten. Zwischen zwei Laeufen KANN sich das Ergebnis nicht aendern; 1.800
# Neuberechnungen je Stunde liefern 1.800-mal dieselbe Zahl.
#
# Die Frist ist bewusst an den Preis-Refresh gekoppelt und nicht an die Stunde
# der Systemguete: keine Karte ist damit aelter als ein Refresh-Zyklus.
_AGGREGAT_CACHE_SEKUNDEN = 900
_AGGREGAT_CACHE: dict[str, tuple[float, object]] = {}
_AGGREGAT_SPERREN: dict[str, threading.Lock] = {}
_AGGREGAT_SPERREN_LOCK = threading.Lock()


def _zwischengespeichert(schluessel: str, fn, sekunden: float = _AGGREGAT_CACHE_SEKUNDEN):
    """Ergebnis von `fn()` je Schluessel hoechstens einmal pro `sekunden`.

    JE SCHLUESSEL EINE SPERRE, und die Berechnung laeuft INNERHALB davon. Das
    ist der Punkt: treffen waehrend einer laufenden Berechnung weitere Anfragen
    ein - und genau das passiert bei 2-Sekunden-Takt und einer Rechenzeit
    darueber -, warten sie und nehmen anschliessend den frischen Wert. Ohne die
    Sperre wuerde jede eintreffende Anfrage dieselbe Rechnung ein weiteres Mal
    anstossen und die Ueberlastung verstaerken, statt sie zu beenden.

    Eine globale Sperre waere falsch: sie wuerde voneinander unabhaengige
    Aggregate serialisieren.
    """
    jetzt = time.monotonic()
    eintrag = _AGGREGAT_CACHE.get(schluessel)
    if eintrag is not None and jetzt - eintrag[0] < sekunden:
        return eintrag[1]

    with _AGGREGAT_SPERREN_LOCK:
        sperre = _AGGREGAT_SPERREN.setdefault(schluessel, threading.Lock())

    with sperre:
        # Zweite Pruefung: waehrend des Wartens auf die Sperre kann ein anderer
        # Aufrufer die Berechnung bereits erledigt haben.
        eintrag = _AGGREGAT_CACHE.get(schluessel)
        jetzt = time.monotonic()
        if eintrag is not None and jetzt - eintrag[0] < sekunden:
            return eintrag[1]
        wert = fn()
        _AGGREGAT_CACHE[schluessel] = (time.monotonic(), wert)
        return wert


def _gecacht(fn):
    """Markiert einen Getter als "aendert sich nur beim Datenlauf".

    Als Dekorator statt als Aufruf im Rumpf, damit an der Funktionsdefinition
    ABLESBAR ist, dass sie zwischengespeichert wird - und damit die Entscheidung
    nicht in einem Lambda mitten im Code verschwindet.

    WELCHE GETTER IHN BEKOMMEN: alle, die aus den `outcome_*`-Spalten oder der
    Kurshistorie aggregieren. Die schreibt nur das taegliche Backward-Tracking
    bzw. der 15-Minuten-Preis-Refresh.

    WELCHE IHN BEWUSST NICHT BEKOMMEN: `_get_budget_heute` (der Nutzer schaut
    beim Beobachten eines Laufs genau auf diese Zahl), `_get_marktscan_last`
    (wird direkt nach einem angestossenen Scan gelesen), `_get_api_health` und
    `_get_coingecko_quota`. Sie sind zusammen unter 0,1 s und muessen live sein
    - ein Zwischenspeicher waere hier kein Gewinn, sondern eine Luege.
    """
    import functools

    @functools.wraps(fn)
    def huelle(*args, **kwargs):
        return _zwischengespeichert(fn.__name__, lambda: fn(*args, **kwargs))

    # Marke fuer den Waechter in teste_status_cache.py. Ohne sie liesse sich von
    # aussen nicht unterscheiden, ob ein Getter zwischengespeichert wird.
    huelle._ist_gecacht = True
    return huelle


# Getter, die BEWUSST live bleiben. Der Waechter in teste_status_cache.py
# verlangt, dass jeder `_get_*` entweder @_gecacht traegt ODER hier steht - ein
# neuer Getter kann damit nicht mehr unbemerkt ungecacht in die Seite geraten.
#
# WARUM DIESE LISTE EXISTIERT. Am 07.08. kamen drei Karten an einem Tag dazu
# (themenfeld_erfolg 0,28-0,47 s, hedge_wirksamkeit 0,11 s, wartende_themen
# 0,003 s). Keine davon war fuer sich auffaellig, zusammen schoben sie den
# Abruf von rund 0,9 s auf 1,39 s - ueber die Schwelle, ab der das Notebook bei
# 2-Sekunden-Takt nicht mehr hinterherkommt. Niemand hat an die Last gedacht,
# ich eingeschlossen, weil die Voreinstellung "ungecacht" war.
#
# Dieselbe Klasse ist in dieser Datei schon zweimal dokumentiert (_safe():
# "264 Fehlschlaege in ~9 Minuten"; _SYSTEMGUETE_CACHE: "damit ueberlappten
# sich die Anfragen"). Zweimal wurde der Einzelfall behoben. Die Liste dreht
# die Voreinstellung um: absichern ist der Normalfall, live die Ausnahme mit
# Begruendung.
_LIVE_GETTER = frozenset({
    # Der Nutzer beobachtet diese Zahl waehrend eines laufenden Signal-Laufs -
    # ein bis zu 15 Minuten alter Wert waere hier eine Falschaussage.
    "_get_budget_heute",
    # Wird direkt nach einem von Hand angestossenen Marktscan gelesen.
    "_get_marktscan_last",
    # Ampel ueber die Erreichbarkeit der Datenquellen. Ein zwischengespeicherter
    # Ausfall waere das Gegenteil ihres Zwecks.
    "_get_api_health",
    # Verbrauchszaehler, aendert sich mit jedem Abruf gegen CoinGecko.
    "_get_coingecko_quota",
    # Dito fuer die LLM-Tagesbudgets. Eine zwischengespeicherte Zahl waere
    # hier besonders schaedlich: wer nachsieht, weil die Signale ausbleiben,
    # bekaeme den Stand von vor zwei Minuten.
    "_get_llm_kontingent",
    # Liest den zuletzt gespeicherten Portfolio-/Z-3-Stand, ist selbst billig
    # und haengt am uebergebenen Portfoliowert statt an der Datenbank.
    "_get_z3_und_bewertung",
    # Reine Konfigurationsanzeige ohne Datenbankzugriff.
    "_get_parameter_overview",
})


# Obergrenze fuer einen vollstaendigen Statusaufbau. Kein Abbruch - eine
# Warnung. Der Vorfall vom 09.08. lief voellig lautlos ab: 94 % CPU ueber
# Stunden, kein einziger Logeintrag, weil normale Lesezugriffe nichts melden.
# Diese Zeile ist die Spur, die damals gefehlt hat.
#
# 1,0 s ist die Haelfte des Abruftakts von 2,0 s aus remote/server.py. Wird sie
# gerissen, ist die Seite auf dem Weg in die Ueberlappung - auf einem
# langsameren Geraet ist sie dann laengst drin.
_BUILD_STATUS_WARNSCHWELLE_SEKUNDEN = 1.0


def leere_aggregat_cache() -> None:
    """Nur fuer Tests und fuer den erzwungenen Neuaufbau nach einem Datenlauf."""
    _AGGREGAT_CACHE.clear()


def _ohne_entfernte_provider(daten):
    """Entfernt Eintraege entfernter Provider aus einer beliebig verschachtelten
    Status-Struktur.

    Rekursiv statt je Karte einzeln: die sechs betroffenen Bloecke haben
    unterschiedliche Formen ({tier: {provider: ...}}, {provider: zahl},
    Listen von Dicts). Eine gemeinsame Funktion kann nicht an einer Stelle
    vergessen werden, wenn eine siebte Karte dazukommt.

    Vergleich auf dem Praefix vor dem Doppelpunkt UND auf dem ganzen
    Schluessel: die Werte treten als "groq" ebenso auf wie als
    "groq:llama-3.3-70b-versatile"."""
    if isinstance(daten, dict):
        raus = {}
        for k, v in daten.items():
            name = str(k).split(":")[0].strip().lower()
            if name in _ENTFERNTE_PROVIDER:
                continue
            raus[k] = _ohne_entfernte_provider(v)
        return raus
    if isinstance(daten, list):
        return [_ohne_entfernte_provider(x) for x in daten]
    return daten


def _safe(fn, *args, **kwargs):
    """Fehlerisolierung je Karte (2026-07-31, Bug-Runde-Fund): build_status()
    reihte bisher alle _get_*()-Aufrufe direkt als Konstruktor-Argumente von
    RemoteStatus(...) auf - EIN Fehler in irgendeiner der ueber 15 Karten (z.B.
    der original_action-Rename-Vorfall vom selben Tag) riss die KOMPLETTE
    /api/status-Antwort mit, genau in dem Moment nach einem Deploy, in dem die
    Remote-Seite am dringendsten gebraucht wird (264 Fehlschlaege in ~9 Minuten
    im Log beobachtet, weil die Seite alle paar Sekunden pollt). Ab jetzt
    bleibt ein Fehler auf die eine betroffene Karte begrenzt (None statt
    Daten), der Rest der Seite funktioniert weiter."""
    try:
        return fn(*args, **kwargs)
    except Exception:
        logger.exception("Remote-Status-Karte '%s' fehlgeschlagen - Rest der Seite bleibt unbeeinflusst", fn.__name__)
        return None


@dataclass
class RemoteStatus:
    generated_at: str
    prices: list[dict] = field(default_factory=list)
    portfolio_value_eur: float | None = None
    cash_reserve_eur: float = 0.0
    cash_reserve_synced_at: str | None = None
    staked_value_eur: float = 0.0
    marktscan_last: dict | None = None
    recent_errors: list[str] = field(default_factory=list)
    jobs_running: dict[str, bool] = field(default_factory=dict)
    jobs_running_seit_minuten: dict[str, float | None] = field(default_factory=dict)
    budget_heute: dict | None = None
    offene_signale: dict | None = None
    api_health: dict | None = None
    regime_status: dict | None = None
    # Z-3 und die Gegenprobe der Bewertung (2026-08-06) - siehe
    # _get_z3_und_bewertung() fuer den Anlass.
    z3_und_bewertung: dict | None = None
    # Hedge-Wirksamkeit (2026-08-07, W1) - das zustaendige Erfolgsmass
    # fuer Absicherungen, siehe compute_hedge_wirksamkeit().
    hedge_wirksamkeit: dict | None = None
    parameter_overview: list[dict] | None = None
    provider_sendezaehler: dict | None = None
    # Trailing-Stop-Empfehlungen fuer offene Signale (2026-08-04,
    # Punkt 3.2). Advisory-only: rechnet und meldet, greift nicht ein.
    ausstiegs_empfehlungen: dict | None = None
    # Marktscan-Erfolgsmessung (2026-07-30, siehe agent/krypto/
    # marktscan_backward_tracking.py::compute_marktscan_erfolgsquote()).
    marktscan_erfolgsquote: dict | None = None
    # CoinGecko-Monats-Kontingent (2026-07-31, echte 80%-Warnmail ausgeloest,
    # siehe scheduler/background.py::coingecko_quota_check_job()).
    coingecko_quota: dict | None = None
    # LLM-Tageskontingent je MODELL (2026-08-09). Am 09.08. haben Messlaeufe am
    # Desktop unbemerkt Geminis Tagesbudget aufgebraucht und die Produktion am
    # Notebook stillgelegt - das Kontingent haengt am Schluessel, nicht am
    # Geraet. Es gab keine Stelle, an der man das haette sehen koennen; der
    # Verbrauch musste hinterher aus Logdateien rekonstruiert werden.
    llm_kontingent: dict | None = None
    # Wartende Themen-Vorschlaege (2026-08-07, S-3). Die Statusverteilung
    # "14 beobachtung" sagt nichts ueber den Vorlauf - diese Karte sagt, WANN
    # etwas reif wird und wie viele am selben Tag.
    wartende_themen: dict | None = None
    # Traf die Richtung der These? (2026-08-07, G-2) - bewusst NICHT die
    # Systemguete je Hauptgruppe, siehe agent/themenfeld_erfolg.py.
    themenfeld_erfolg: dict | None = None

    def to_dict(self) -> dict:
        return {
            "generated_at": self.generated_at,
            "prices": self.prices,
            "portfolio_value_eur": self.portfolio_value_eur,
            "cash_reserve_eur": self.cash_reserve_eur,
            "cash_reserve_synced_at": self.cash_reserve_synced_at,
            "staked_value_eur": self.staked_value_eur,
            "marktscan_last": self.marktscan_last,
            "recent_errors": self.recent_errors,
            "jobs_running": self.jobs_running,
            "jobs_running_seit_minuten": self.jobs_running_seit_minuten,
            "budget_heute": self.budget_heute,
            "offene_signale": self.offene_signale,
            "api_health": self.api_health,
            "regime_status": self.regime_status,
            "z3_und_bewertung": self.z3_und_bewertung,
            "hedge_wirksamkeit": self.hedge_wirksamkeit,
            "parameter_overview": self.parameter_overview,
            "provider_sendezaehler": self.provider_sendezaehler,
            "ausstiegs_empfehlungen": self.ausstiegs_empfehlungen,
            "marktscan_erfolgsquote": self.marktscan_erfolgsquote,
            "coingecko_quota": self.coingecko_quota,
            "llm_kontingent": self.llm_kontingent,
            "wartende_themen": self.wartende_themen,
            "themenfeld_erfolg": self.themenfeld_erfolg,
        }


def build_status(conn: sqlite3.Connection, watchlist: list, log_path: Path,
                 error_tail_lines: int = 5) -> RemoteStatus:
    """Vollstaendiger Statusaufbau, mit Laufzeit-Wache.

    Die Wache ist die Spur, die am 09.08. gefehlt hat: das Notebook lief
    stundenlang bei 94 % CPU, ohne dass irgendetwas im Log stand - normale
    Lesezugriffe melden nichts. Reisst ein Aufbau die Schwelle, steht es ab
    jetzt da, samt der Aufschluesselung, welche Karte es war.

    Bewusst nur eine WARNUNG. Ein Abbruch waere schlechter als eine langsame
    Seite: die Fernsteuerung wird gerade dann gebraucht, wenn etwas klemmt."""
    beginn = time.monotonic()
    ergebnis = _build_status_roh(conn, watchlist, log_path, error_tail_lines)
    dauer = time.monotonic() - beginn
    if dauer > _BUILD_STATUS_WARNSCHWELLE_SEKUNDEN:
        logger.warning(
            "Statusaufbau dauerte %.2f s (Schwelle %.2f s, Abruftakt der Seite "
            "2,0 s). Bei Ueberschreitung des Takts ueberlappen die Anfragen und "
            "verzoegern sich gegenseitig weiter. Pruefen, ob eine neue Karte "
            "ohne @_gecacht dazugekommen ist - siehe _LIVE_GETTER.",
            dauer, _BUILD_STATUS_WARNSCHWELLE_SEKUNDEN,
        )
    return ergebnis


def _build_status_roh(conn: sqlite3.Connection, watchlist: list, log_path: Path, error_tail_lines: int = 5) -> RemoteStatus:
    latest_prices = db.get_latest_prices(conn)
    # Klassifikations-Redesign (2026-07-16): "gehalten" live aus den echten
    # Bestaenden (Spot) UND offenen Hebel-Positionen abgeleitet statt eines
    # gespeicherten Status-Felds - kann dadurch nie veralten (siehe config.py::
    # WatchlistAsset-Docstring).
    gehaltene_symbole = {
        h.symbol for h in db.get_all_holdings(conn)
        if (h.quantity or 0.0) + (h.staked_quantity or 0.0) > 0.0
    }
    offene_hebel_symbole = {p.symbol for p in db.get_open_hebel_positions(conn)}
    active_symbols = {
        a.symbol for a in watchlist
        if a.symbol in gehaltene_symbole or a.symbol in offene_hebel_symbole
    }

    prices = []
    for symbol in sorted(active_symbols):
        snap = latest_prices.get(symbol)
        fetched_at = snap.fetched_at if snap else None
        prices.append(
            {
                "symbol": symbol,
                "price_eur": snap.price_eur if snap else None,
                "fetched_at": fetched_at,
                "stale": is_price_stale(fetched_at),
            }
        )

    holdings = db.get_all_holdings(conn)
    portfolio_value_eur = 0.0
    staked_value_eur = 0.0
    any_price = False
    for holding in holdings:
        snap = latest_prices.get(holding.symbol)
        if snap and snap.price_eur is not None:
            portfolio_value_eur += holding.quantity * snap.price_eur
            any_price = True
            # 2026-07-11, Nutzer-Fund: gestakte Menge ist ueber die normale Wallet-API
            # unsichtbar (importer/bitpanda_avg_cost.py::compute_staked_quantities()) -
            # additiv, echtes Vermoegen, nur voruebergehend nicht handelbar.
            if holding.staked_quantity:
                staked_value_eur += holding.staked_quantity * snap.price_eur
    portfolio_value_eur += staked_value_eur

    # RM-4/Konsistenz-Fix (2026-07-11): agent/krypto/risk_gate.py::pre_check()
    # zaehlt die Fiat-Cash-Reserve zum Portfoliowert dazu, diese Anzeige tat das
    # bisher nicht (gleicher Fund wie bei ui/portfolio.py::refresh()) - EUR ist
    # hier direkt (keine USD-Umrechnung noetig, die Remote-Seite zeigt nur EUR).
    fiat_cash_eur = db.get_cash_reserve_fiat_eur(conn)
    if fiat_cash_eur > 0:
        portfolio_value_eur += fiat_cash_eur
        any_price = True

    lock_status = background.get_lock_status()
    jobs_running = {name: info["locked"] for name, info in lock_status.items()}
    jobs_running_seit_minuten = {
        name: (info["running_since_seconds"] / 60 if info["running_since_seconds"] is not None else None)
        for name, info in lock_status.items()
    }

    return RemoteStatus(
        generated_at=datetime.now(timezone.utc).isoformat(),
        prices=prices,
        portfolio_value_eur=portfolio_value_eur if any_price else None,
        cash_reserve_eur=fiat_cash_eur,
        cash_reserve_synced_at=db.get_cash_reserve_synced_at(conn),
        staked_value_eur=staked_value_eur,
        marktscan_last=_safe(_get_marktscan_last, conn),
        recent_errors=_tail_log_errors(log_path, error_tail_lines),
        jobs_running=jobs_running,
        jobs_running_seit_minuten=jobs_running_seit_minuten,
        budget_heute=_safe(_get_budget_heute, conn),
        offene_signale=_safe(_get_offene_signale_uebersicht, conn, watchlist),
        api_health=_safe(_get_api_health, conn),
        regime_status=_safe(_get_regime_status, conn),
        z3_und_bewertung=_safe(_get_z3_und_bewertung, conn, portfolio_value_eur),
        hedge_wirksamkeit=_safe(_get_hedge_wirksamkeit, conn, watchlist),
        parameter_overview=_safe(_get_parameter_overview),
        provider_sendezaehler=_safe(_get_provider_sendezaehler, conn, watchlist),
        ausstiegs_empfehlungen=_safe(_get_ausstiegs_empfehlungen, conn, watchlist),
        selbst_gewaehltes_halten_performance_nach_grund=_safe(
            _get_selbst_gewaehltes_halten_performance_nach_grund, conn, watchlist,
        ),
        marktscan_erfolgsquote=_safe(_get_marktscan_erfolgsquote, conn),
        coingecko_quota=_safe(_get_coingecko_quota, conn),
        llm_kontingent=_safe(_get_llm_kontingent, conn),
        wartende_themen=_safe(_get_wartende_themen, conn),
        themenfeld_erfolg=_safe(_get_themenfeld_erfolg, conn),
    )


def _get_api_health(conn: sqlite3.Connection) -> dict:
    """Sichtbarkeit fuer das passive API-Gesundheits-Tracking (2026-07-15, siehe
    database/api_health.py::track_api_health()) - reiner Lesezugriff, keine neue
    Logik.

    Auch hier der Filter fuer entfernte Provider (2026-08-05): das
    Gesundheits-Tracking ist passiv und schreibt fort, was einmal aufgerufen
    wurde - Groq und Cerebras stehen dort mit ihrem letzten Stand von vor der
    Entfernung und erschienen auf der Seite sonst als dauerhaft stille
    Quellen."""
    return _kontingent_statt_stoerung(
        _ohne_entfernte_provider(db.get_api_health_status(conn)))


def _pazifik_tag_von(zeitstempel: str | None) -> str | None:
    """Auf welchen KONTINGENT-Tag faellt dieser UTC-Zeitstempel?

    Googles Free-Tier setzt zu Mitternacht Pazifik zurueck, nicht zu
    Mitternacht UTC. Ein Fehler von 06:34 UTC gehoert damit noch zum Vortag."""
    if not zeitstempel:
        return None
    from datetime import datetime
    try:
        from zoneinfo import ZoneInfo
        zone = ZoneInfo("America/Los_Angeles")
    except Exception:  # noqa: BLE001
        from datetime import timedelta, timezone
        zone = timezone(timedelta(hours=-8))
    try:
        return datetime.fromisoformat(zeitstempel).astimezone(zone).strftime("%Y-%m-%d")
    except (TypeError, ValueError):
        return None


def _kontingent_statt_stoerung(daten: dict) -> dict:
    """Ein leeres Tagesbudget ist kein Defekt - und ab morgen keine Nachricht.

    ZWEI PROBLEME, beide am 10.08. an der echten Statusseite gesehen.

    ERSTENS FEHLTE EIN ZUSTAND. Seit der Dekorator ein erschoepftes Budget
    nicht mehr als Stoerung protokolliert, steht der Anbieter auf "OK" -
    obwohl er den ganzen Tag nichts liefert. Wer nachsieht, weil die Signale
    ausbleiben, findet eine gruene Ampel und sucht den Fehler woanders. Das
    ist nicht besser als das falsche Rot vorher, nur leiser.

    ZWEITENS BLIEB EIN ALTER EINTRAG EWIG ROT. `api_health_status` haelt je
    Quelle nur den LETZTEN Zustand. Ein Kontingent-Fehler von gestern stand
    dort weiter als "Fehler", obwohl das Budget laengst zurueckgesetzt ist -
    und liess sich nur von Hand loeschen. Ein Zustand, der sich selbst
    ueberlebt, gehoert automatisch aufgeloest, nicht per Kommando.

    Beides haengt am Kontingent-TAG (Mitternacht Pazifik): derselbe Eintrag
    bedeutet heute "Budget leer" und morgen "nicht mehr relevant"."""
    try:
        from api.gemini import _erschoepft, _kontingent_tag
    except Exception:  # noqa: BLE001
        return daten
    heute = _kontingent_tag()
    for eintrag in daten.values():
        if eintrag.get("last_error_type") != "TageskontingentErschoepft":
            continue
        if _pazifik_tag_von(eintrag.get("last_error_at")) == heute:
            eintrag["status"] = "budget_leer"
        else:
            eintrag["status"] = ("ok" if eintrag.get("last_success_at")
                                 else "unbekannt")
            eintrag["veralteter_kontingentfehler"] = True
    # Der prozesslokale Merker kennt Faelle, die (noch) keinen DB-Eintrag
    # haben - der Dekorator schreibt fuer sie ja bewusst nichts mehr.
    if any(tag == heute for _, tag in _erschoepft) and "gemini" in daten:
        daten["gemini"]["status"] = "budget_leer"
    return daten


def _get_coingecko_quota(conn: sqlite3.Connection) -> dict | None:
    """CoinGecko-Monats-Kontingent-Sichtbarkeit (2026-07-31, echte 80%-
    Warnmail von CoinGecko ausgeloest, siehe scheduler/background.py::
    coingecko_quota_check_job()) - reiner Lesezugriff auf den Zaehler, keine
    neue Logik. None, wenn coingecko_quota.monatslimit in config.yaml (noch)
    nicht gesetzt ist."""
    config_dict = config_module.load_config()
    limit = config_dict.get("coingecko_quota", {}).get("monatslimit")
    if not limit:
        return None
    monat = db.aktueller_monat_utc()
    anzahl = db.get_api_call_counter(conn, "coingecko", monat)
    return {
        "monat": monat,
        "anzahl": anzahl,
        "limit": limit,
        "prozent": round((anzahl / limit) * 100, 1),
        # Tages-Granularitaet (2026-08-01, Nutzer-Nachfrage nach ungewoehnlich
        # hohem Verbrauch) - macht kuenftig sichtbar, an welchem Tag der
        # Verbrauch tatsaechlich anstieg, statt es im Nachhinein schaetzen zu
        # muessen.
        "anzahl_heute": db.get_api_call_counter_taeglich(conn, "coingecko"),
    }


def _get_llm_kontingent(conn: sqlite3.Connection) -> dict | None:
    """Geminis Tagesbudget je MODELL - reiner Lesezugriff, keine neue Logik.

    WARUM DIESE KARTE EXISTIERT (2026-08-09). Am 09.08. haben Messlaeufe am
    Desktop Geminis Tagesbudget aufgebraucht; die Produktion am Notebook stand
    danach den Rest des Tages. Das Kontingent haengt am API-SCHLUESSEL, nicht
    am Geraet - beide Rechner schoepfen aus demselben Topf. Es gab keine
    Stelle, an der das sichtbar gewesen waere: der Verbrauch musste hinterher
    aus Logdateien geschaetzt werden.

    DREI EIGENHEITEN, die die CoinGecko-Karte nicht hat:

      je MODELL   Google begrenzt `...PerProjectPerModel...`. Ein erschoepftes
                  Modell sagt nichts ueber das Geschwistermodell aus.
      Pazifik     Der Zaehler laeuft auf Googles Tagesgrenze (Mitternacht
                  Pazifik), nicht auf UTC. Ein UTC-Datum stuende hier zwischen
                  02:00 und 09:00 MESZ faelschlich auf 0.
      gemessen    Die 500 stammen aus Googles eigenem Fehlerkoerper
                  (pruefe_gemini_verhalten.py, 09.08.), nicht aus Recherche.

    None, wenn heute noch kein Aufruf gebucht wurde - dann gibt es nichts zu
    zeigen und die Karte bleibt leer, statt ein falsches "0 von 500" zu
    behaupten, das auch "wir zaehlen gerade nicht" bedeuten koennte."""
    from api.gemini import TAGESBUDGET_JE_MODELL, _kontingent_tag

    tag = _kontingent_tag()
    zeilen = conn.execute(
        "SELECT source, anzahl FROM api_call_kontingent_taeglich "
        "WHERE tag = ? AND source LIKE 'gemini:%' ORDER BY anzahl DESC",
        (tag,),
    ).fetchall()
    if not zeilen:
        return None
    modelle = []
    for r in zeilen:
        anzahl = r["anzahl"]
        modelle.append({
            "modell": r["source"].split(":", 1)[1],
            "anzahl": anzahl,
            "limit": TAGESBUDGET_JE_MODELL,
            "prozent": round(anzahl / TAGESBUDGET_JE_MODELL * 100, 1),
        })
    return {"tag_pazifik": tag, "modelle": modelle}


@_gecacht
def _get_provider_performance(conn: sqlite3.Connection, watchlist: list) -> dict:
    """Sichtbarkeit fuer die Backward-Tracking-Provider-Performance (2026-07-15,
    siehe agent/krypto/backward_tracking.py::compute_provider_performance()) -
    reiner Lesezugriff, keine neue Logik.

    `watchlist` seit 2026-07-20 durchgereicht, damit die Spot-Seite nach
    Assetklasse (krypto/aktien/rohstoffe/etf) statt einem einzigen "spot"-Topf
    aufgeschluesselt wird - siehe compute_provider_performance()-Docstring."""
    from agent.krypto.backward_tracking import compute_provider_performance

    return _ohne_entfernte_provider(compute_provider_performance(conn, watchlist))


@_gecacht
def _get_offene_signale_uebersicht(conn: sqlite3.Connection, watchlist: list) -> dict:
    """Ergaenzt _get_provider_performance() um Sichtbarkeit fuer noch nicht
    aufgeloeste, aber bereits trackbare Signale (2026-07-24, Nutzer-Fund: die
    reine "0 abgeschlossen"-Anzeige zeigte keinen Fortschritt an) - reiner
    Lesezugriff, siehe agent/krypto/backward_tracking.py::
    compute_offene_signale_uebersicht()."""
    from agent.krypto.backward_tracking import compute_offene_signale_uebersicht

    return compute_offene_signale_uebersicht(conn, watchlist)


@_gecacht
def _get_konfidenz_kalibrierung(conn: sqlite3.Connection, watchlist: list) -> dict:
    """Konfidenz-Kalibrierungskurve (2026-07-26, Punkt 3 des Regime-Persistenz-
    Folge-Vorschlags) - reiner Lesezugriff, siehe agent/krypto/
    backward_tracking.py::compute_konfidenz_kalibrierung() fuer die Frage,
    die diese Karte beantwortet (haelt confidence_pct, was es verspricht?)."""
    from agent.krypto.backward_tracking import compute_konfidenz_kalibrierung

    aus = compute_konfidenz_kalibrierung(conn, watchlist) or {}
    # R-1 (14.08.2026): DIESE KARTE BETRIFFT NUR DIE ALTE KETTE.
    #
    # Die Rollen-Kette erhebt keine Konfidenz mehr - sie fiel am 12.08. als
    # Folge, nicht als Wahl: r = +0,073 ueber 92 Faelle, und das Regime stand
    # ueber 1.022 Faelle konstant auf "baer", die Schwelle also faktisch immer
    # bei 75. Eine konstante Schwelle auf einer nutzlosen Groesse.
    #
    # OHNE DIESEN HINWEIS LIEST SICH DIE LEERE KARTE WIE EIN DEFEKT. Sie ist
    # keiner - sie ist nur nicht mehr zustaendig. Und das ist der Unterschied,
    # den ein Nutzer aus einer leeren Tabelle nicht ablesen kann.
    if isinstance(aus, dict):
        aus["_nur_alte_kette"] = True
        aus["_hinweis"] = (
            "Betrifft nur die ALTE Kette. Die Rollen-Kette (quelle_kette="
            "'rollen') erhebt keine Konfidenz mehr - ihr Ersatz ist der "
            "Entscheider: die kalibrierte Trefferquote gegen den "
            "Kosten-Breakeven. Eine leere Karte ist hier kein Defekt.")
    return aus


@_gecacht
def _get_richtungstreffer_quote(conn: sqlite3.Connection, watchlist: list) -> dict:
    """Richtungstreffer-Quote-Karte (2026-07-27, Performance-Messung-
    Expertenanalyse, Nutzer-Wunsch "bitte nicht auf der Remoteseite vergessen")
    - reiner Lesezugriff auf agent/krypto/backward_tracking.py::
    compute_richtungstreffer_quote(). Anders als provider_performance/
    konfidenz_kalibrierung (die watchlist-basiert nach Assetklasse
    aufschluesseln) liefert compute_richtungstreffer_quote() nur EINEN Tier
    pro Aufruf - hier bewusst nur grob nach spot/hebel getrennt (wie
    compute_win_rate_fact()), keine feinere Assetklassen-Aufschluesselung noetig
    fuer diese Uebersichtskarte."""
    from agent.krypto.backward_tracking import DEFAULT_RICHTUNGSTREFFER_MINDEST_CRV, compute_richtungstreffer_quote

    schwelle = config_module.load_config().get("backward_tracking", {}).get(
        "richtungstreffer_mindest_crv", DEFAULT_RICHTUNGSTREFFER_MINDEST_CRV,
    )
    return {
        "mindest_crv": schwelle,
        "spot": compute_richtungstreffer_quote(conn, "spot", schwelle),
        "hebel": compute_richtungstreffer_quote(conn, "hebel", schwelle),
    }


@_gecacht
def _get_marktscan_erfolgsquote(conn: sqlite3.Connection) -> dict | None:
    """Marktscan-Erfolgsquote-Karte (2026-07-30, Erfolgsmessung Teil 2) - reiner
    Lesezugriff auf agent/krypto/marktscan_backward_tracking.py::
    compute_marktscan_erfolgsquote(). Anders als richtungstreffer_quote braucht
    diese Karte KEINE Watchlist (die Aggregation liest direkt aus
    marktscan_candidates, nicht ueber Assetklassen der Watchlist)."""
    from agent.krypto.marktscan_backward_tracking import compute_marktscan_erfolgsquote

    return compute_marktscan_erfolgsquote(conn)


@_gecacht
def _get_zai_richtung_performance(conn: sqlite3.Connection, watchlist: list) -> dict:
    """Z.ais UNABHAENGIGE Richtungs-Erfolgsquote (2026-07-27, Nutzer-Wunsch:
    "ZAI unabhaengig mit seinen unterschiedlichen Entscheidungen und deren
    Erfolgsquote messen"). Die urspruengliche Begruendung stuetzte sich auf den
    Nur-Long-Kandidatenfilter - der ist seit dem 05.08. entfernt, siehe
    compute_zai_richtung_performance()-Docstring, Abschnitt "URSPRUENGLICHE
    BEGRUENDUNG UEBERHOLT".
    - reiner Lesezugriff auf agent/krypto/backward_tracking.py::
    compute_zai_richtung_performance(). Anders als provider_performance
    (das Mistrals EIGENE Empfehlung bewertet) misst diese Karte, ob Z.ais
    Call-2-Richtungsableitung (`zai_eigene_richtung`) unabhaengig von Mistrals
    Bias mit der tatsaechlichen Marktrichtung uebereinstimmte.

    Seit Punkt 3 der Performance-Messung-Nachfrage (2026-07-27) auf derselben
    Basis wie richtungstreffer_quote (Maximum Favorable Excursion, nicht der
    binaere TP/SL-outcome_status) - dieselbe config-Schwelle wie dort
    verwenden, damit beide Karten konsistent dieselbe CRV-Schwelle nutzen."""
    from agent.krypto.backward_tracking import DEFAULT_RICHTUNGSTREFFER_MINDEST_CRV, compute_zai_richtung_performance

    schwelle = config_module.load_config().get("backward_tracking", {}).get(
        "richtungstreffer_mindest_crv", DEFAULT_RICHTUNGSTREFFER_MINDEST_CRV,
    )
    return compute_zai_richtung_performance(conn, watchlist, schwelle)


@_gecacht
def _get_veto_schatten_performance(conn: sqlite3.Connection, watchlist: list) -> dict:
    """Gruppe C ("Veto-Schatten", 2026-07-28) - reiner Lesezugriff auf
    agent/krypto/backward_tracking.py::compute_veto_shadow_performance(). Wie
    _get_provider_performance(), aber fuer die hypothetischen, nie
    ausgefuehrten Trade-Vorschlaege, deren Action durch einen Risk-Gate-Veto
    auf HALTEN zurueckgestuft wurde - siehe check_signal_veto_shadow_outcome()-
    Docstring fuer die volle Herleitung dieses Features."""
    from agent.krypto.backward_tracking import compute_veto_shadow_performance

    return _ohne_entfernte_provider(compute_veto_shadow_performance(conn, watchlist))


@_gecacht
def _get_richtungsverteilung(conn: sqlite3.Connection, watchlist: list) -> dict:
    """LONG gegen SHORT seit dem Nur-Long-Umbau (2026-08-05) - NEUE Karte.

    Bis zum Umbau war diese Frage nicht stellbar: SHORT-Kandidaten wurden vor
    dem LLM-Aufruf gefiltert, und was das Modell trotzdem als SHORT empfahl,
    drehte das Risk-Gate auf HALTEN. Seither laufen beide Richtungen normal
    durch - und werden gemessen, auch wenn SHORT weder gemailt noch im
    Hebel-Tab standardmaessig angezeigt wird.

    Reiner Lesezugriff auf backward_tracking.py::compute_richtungsverteilung()."""
    from agent.krypto.backward_tracking import compute_richtungsverteilung

    return compute_richtungsverteilung(conn, watchlist)


@_gecacht
def _get_veto_schatten_performance_nach_grund(conn: sqlite3.Connection, watchlist: list) -> dict:
    """R-5.10-Konfidenzschwellen-Nachtrag (2026-07-30) - reiner Lesezugriff auf
    agent/krypto/backward_tracking.py::compute_veto_shadow_performance_nach_grund().
    Wie _get_veto_schatten_performance(), aber nach (tier, veto_grund) statt
    (tier, provider) aufgeschluesselt - beantwortet die fuer eine Schwellen-
    Entscheidung eigentliche Frage: schlagen sich Konfidenzschwellen-Vetos
    (R-5.10) anders als CRV<2.0-Vetos, je Assetklasse?"""
    from agent.krypto.backward_tracking import (
        VETO_GRUND_NUR_LONG, compute_veto_shadow_performance_nach_grund,
    )

    roh = compute_veto_shadow_performance_nach_grund(conn, watchlist)
    # HISTORISCHEN BESTAND AUSBLENDEN (2026-08-05, Nutzer-Vorgabe "Informationen
    # welche wir nicht mehr messen ... nicht mehr anzeigen"): der Nur-Long-Veto
    # ist entfernt, seine 313 Altfaelle wachsen nicht mehr. Als laufende
    # Kennzahl dargestellt liest man einen eingefrorenen Bestand als aktuelles
    # Systemverhalten - genau die Verwechslung, die beim 31.07.-Bruch Zeit
    # gekostet hat.
    #
    # Nur die ANZEIGE wird gefiltert. Die Daten bleiben in der Datenbank und im
    # Export vollstaendig erhalten; die neue Kategorie VETO_GRUND_NUR_LONG
    # macht sie dort gezielt auswertbar, statt sie wie bisher im Sammeltopf
    # "sonstige" zu verstecken.
    if not isinstance(roh, dict):
        return roh
    gefiltert = {}
    for tier, gruende in roh.items():
        if isinstance(gruende, dict):
            gefiltert[tier] = {g: v for g, v in gruende.items()
                               if g != VETO_GRUND_NUR_LONG}
        else:
            gefiltert[tier] = gruende
    return gefiltert


# Zwischenspeicher fuer die Systemguete (2026-08-03, HOTFIX).
# HINTERGRUND: die Remote-Seite ruft /api/status alle 2 Sekunden ab
# (setInterval(refreshStatus, 2000) in remote/server.py). Am 03.08. kamen
# Basislinien-Simulation und Bootstrap dazu, zusammen rund 1-1,5 s je Aufruf -
# damit ueberlappten sich die Anfragen, der Server kam nicht mehr hinterher und
# die Seite zeigte nur noch kurz Werte, bevor sie leer blieb (Nutzer-Fund).
# Die Zahlen aendern sich ohnehin nur beim taeglichen Backward-Tracking-Lauf,
# ein Zwischenspeicher kostet also keine Aktualitaet.
#
# NACHTRAG 03.08.: 300 Sekunden waren immer noch 60x haeufiger als noetig. Die
# Zahlen speisen sich ausschliesslich aus den outcome_*-Spalten, und die werden
# nur vom taeglichen 06:00-Backward-Tracking geschrieben - zwischen zwei Laeufen
# kann sich das Ergebnis gar nicht aendern. Auf dem Notebook (i5-4300U, zwei
# Kerne von 2013) kostet ein Durchlauf ein Vielfaches der 1,8 s vom Desktop,
# und die reine Python-Schleife des Bootstraps belegt dabei einen der beiden
# Kerne - der Nutzer sah nach einem Browser-Refresh 15-20 s lang keine
# aktualisierten Werte. Ein Stundentakt loest das an der Wurzel: der Wert ist
# hoechstens eine Stunde alt, die Berechnung laeuft statt 288x nur noch 24x
# am Tag.
_SYSTEMGUETE_CACHE: dict = {"stand": 0.0, "wert": None, "laeuft": False,
                            "fehler_stand": 0.0}
_SYSTEMGUETE_CACHE_SEKUNDEN = 3600

# WARTEZEIT NACH EINEM FEHLSCHLAG (2026-08-09). Der Zwischenspeicher oben
# schuetzt nur den ERFOLGSFALL: schlaegt die Berechnung fehl, bleibt `wert` auf
# None, `frisch` damit dauerhaft False - und `laeuft` wird im finally wieder
# freigegeben. Der naechste Statusabruf startet die Berechnung also sofort neu,
# bei 2-Sekunden-Takt also alle zwei Sekunden, jedes Mal ueber die volle
# Kurshistorie.
#
# Das ist kein hypothetischer Fall. Am 06.08. stand genau dieser Kreis im Log:
# 1.069 Fehlschlaege in der Stunde 12:00 und 16 weitere bis 13:19, alle mit
# demselben AttributeError, bis der ausloesende Fehler behoben war - rund
# achtzehn vergebliche Vollberechnungen je Minute auf einem Zweikern-Notebook.
#
# Der Kommentar im except-Zweig sagte "beim naechsten Abruf wird es erneut
# versucht". Richtig gedacht fuer einen einmaligen Ausrutscher, falsch fuer
# einen dauerhaften Fehler - und dauerhaft ist der haeufigere Fall, weil ein
# Programmierfehler nicht von selbst verschwindet.
_SYSTEMGUETE_FEHLER_PAUSE_SEKUNDEN = 300


@_gecacht
def _get_ausstiegs_empfehlungen(conn, watchlist: list) -> dict:
    """Offene Signale, deren Stop nachgezogen gehoert (2026-08-04).

    Reiner Lesezugriff auf backward_tracking.py::
    compute_ausstiegs_empfehlungen(). Advisory-only (P-7) - die
    Empfehlung wird angezeigt, nicht ausgefuehrt."""
    from agent.krypto.backward_tracking import compute_ausstiegs_empfehlungen
    import config as _config
    return compute_ausstiegs_empfehlungen(conn, watchlist, _config.load_config())


def _get_systemguete(conn: sqlite3.Connection, watchlist: list) -> dict:
    """SQN/Expectancy/Profit Factor je tier (2026-08-02) - reiner Lesezugriff
    auf agent/krypto/backward_tracking.py::compute_systemguete(). Zielwerte und
    Herleitung in Basisinfos/Zielgroessen_und_Erfolgsmasse.md; getrennt nach
    real ausgefuehrt und Veto-Schatten, weil beide verschiedene Fragen
    beantworten.

    Ergebnis wird zwischengespeichert und im HINTERGRUND erneuert - der
    Statusabruf wartet nie auf die Berechnung. Begruendung bei
    _SYSTEMGUETE_CACHE."""
    jetzt = time.monotonic()
    frisch = (_SYSTEMGUETE_CACHE["wert"] is not None
              and jetzt - _SYSTEMGUETE_CACHE["stand"] < _SYSTEMGUETE_CACHE_SEKUNDEN)
    # Nach einem Fehlschlag eine Weile gar nicht erst antreten - siehe
    # _SYSTEMGUETE_FEHLER_PAUSE_SEKUNDEN.
    pausiert = (jetzt - _SYSTEMGUETE_CACHE["fehler_stand"]
                < _SYSTEMGUETE_FEHLER_PAUSE_SEKUNDEN)
    if not frisch and not pausiert and not _SYSTEMGUETE_CACHE["laeuft"]:
        _SYSTEMGUETE_CACHE["laeuft"] = True
        threading.Thread(target=_systemguete_neu_berechnen, args=(watchlist,),
                         daemon=True).start()
    # Bis die Berechnung fertig ist, kommt der vorige Wert zurueck (beim
    # allerersten Aufruf None - die Karte bleibt dann eine Runde leer und
    # fuellt sich beim naechsten Refresh zwei Sekunden spaeter).
    return _SYSTEMGUETE_CACHE["wert"]


# Eigener Zwischenspeicher, deshalb kein @_gecacht: diese Karte rechnet im
# HINTERGRUND-THREAD und liefert solange den vorigen Wert, damit der Statusabruf
# nie auf sie wartet (Stundentakt, siehe _SYSTEMGUETE_CACHE). Der Waechter in
# teste_status_cache.py kennt nur die Marke - ohne diese Zeile meldete er die
# Karte zu Recht als ungeschuetzt. Er hat sie beim ersten Lauf gefunden.
_get_systemguete._ist_gecacht = True


def _systemguete_neu_berechnen(watchlist: list) -> None:
    """Laeuft in einem Hintergrund-Thread und OEFFNET EINE EIGENE
    DB-Verbindung - sqlite3-Verbindungen duerfen nicht ueber Threads hinweg
    benutzt werden, die Verbindung des Aufrufers ist hier also tabu."""
    import time

    import database.db as db
    from agent.krypto.backward_tracking import compute_systemguete

    try:
        eigene = db.get_connection()
        try:
            wert = compute_systemguete(eigene, watchlist)
        finally:
            eigene.close()
        _SYSTEMGUETE_CACHE["wert"] = wert
        _SYSTEMGUETE_CACHE["stand"] = time.monotonic()
    except Exception:
        # Nicht durchreichen: ein Fehler hier darf den Statusabruf nicht
        # beeinflussen. Erneut versucht wird erst nach der Fehler-Pause - ohne
        # sie liefe die Berechnung im Takt der Seitenabrufe weiter ins Leere
        # (06.08.: 1.085 Fehlschlaege, siehe _SYSTEMGUETE_FEHLER_PAUSE_SEKUNDEN).
        _SYSTEMGUETE_CACHE["fehler_stand"] = time.monotonic()
        logger.exception("Systemguete-Neuberechnung im Hintergrund fehlgeschlagen")
    finally:
        _SYSTEMGUETE_CACHE["laeuft"] = False


@_gecacht
def _get_selbst_gewaehltes_halten_performance(conn: sqlite3.Connection, watchlist: list) -> dict:
    """Gruppe C, Gegenfall zum Veto-Schatten (2026-07-31) - reiner Lesezugriff
    auf agent/krypto/backward_tracking.py::compute_selbst_halten_performance().
    Kein Gate/Veto, das LLM hat sich selbst gegen einen Trade entschieden,
    aber trotzdem eine hypothetische Zone angegeben - siehe check_signal_
    selbst_halten_outcome()-Docstring fuer die volle Herleitung."""
    from agent.krypto.backward_tracking import compute_selbst_halten_performance

    return compute_selbst_halten_performance(conn, watchlist)


@_gecacht
def _get_selbst_gewaehltes_halten_performance_nach_grund(conn: sqlite3.Connection, watchlist: list) -> dict:
    """Wie _get_selbst_gewaehltes_halten_performance(), aber nach (tier,
    top_grund_1_kategorie) statt (tier, provider) aufgeschluesselt (2026-07-31,
    mirror _get_veto_schatten_performance_nach_grund())."""
    from agent.krypto.backward_tracking import compute_selbst_halten_performance_nach_grund

    return compute_selbst_halten_performance_nach_grund(conn, watchlist)


@_gecacht
def _get_zai_richtung_performance_schatten(conn: sqlite3.Connection, watchlist: list) -> dict:
    """Gruppe C, Z.ai-Anteil (2026-07-28) - reiner Lesezugriff auf
    compute_zai_richtung_performance_schatten(). Misst Z.ais unabhaengiges
    Richtungsurteil gerade fuer die vetoten Signale - siehe dortiger
    Docstring."""
    from agent.krypto.backward_tracking import (
        DEFAULT_RICHTUNGSTREFFER_MINDEST_CRV,
        compute_zai_richtung_performance_schatten,
    )

    schwelle = config_module.load_config().get("backward_tracking", {}).get(
        "richtungstreffer_mindest_crv", DEFAULT_RICHTUNGSTREFFER_MINDEST_CRV,
    )
    return compute_zai_richtung_performance_schatten(conn, watchlist, schwelle)


@_gecacht
def _get_gesamt_signalqualitaet(conn: sqlite3.Connection, watchlist: list) -> dict:
    """"Gesamt-Signalqualitaet, unabhaengig vom Risk-Gate" (2026-07-28, Nutzer-
    Einsicht: Gruppe C ist eigentlich Real+Schatten zusammen) - reiner
    Lesezugriff auf compute_gesamt_signalqualitaet(), siehe dortiger Docstring
    fuer die additive Zusammenfuehrung."""
    from agent.krypto.backward_tracking import compute_gesamt_signalqualitaet

    return _ohne_entfernte_provider(compute_gesamt_signalqualitaet(conn, watchlist))


@_gecacht
def _get_provider_sendezaehler(conn: sqlite3.Connection, watchlist: list) -> dict:
    """Rohe Sendeanzahl je Provider (2026-07-28, Nutzer-Frage "wie oft hat
    Gemini ueberhaupt welche Signale gesendet?") - reiner Lesezugriff auf
    compute_provider_sendezaehler(), macht selten eingesetzte Provider auch
    OHNE aufgeloestes Signal sichtbar (siehe dortiger Docstring)."""
    from agent.krypto.backward_tracking import compute_provider_sendezaehler

    return _ohne_entfernte_provider(compute_provider_sendezaehler(conn, watchlist))


@_gecacht
def _get_regime_status(conn: sqlite3.Connection) -> dict | None:
    """Regime-Status-Karte (2026-07-17) - reiner Lesezugriff auf den zuletzt
    PERSISTIERTEN Regime-Stand, kein neuer Live-Recompute (siehe
    agent/krypto/regime.py::get_last_known_regime_status())."""
    from agent.krypto.regime import get_last_known_regime_status

    return get_last_known_regime_status(conn)


def _get_z3_und_bewertung(conn: sqlite3.Connection, portfolio_value_eur: float | None) -> dict | None:
    """Drawdown-Notbremse Z-3 - und die Gegenprobe, ob ihre Datenbasis stimmt.

    ZWEI LUECKEN, die dieser Block schliesst (2026-08-06):

    1. Z-3 stand ueberhaupt nicht auf der Uebersichtsseite. Die Notbremse loeste
       am 05. und 06.08. aus, sichtbar war das nur per E-Mail und im Log.

    2. WICHTIGER: die Seite rechnet den Portfoliowert aus den SNAPSHOT-Preisen
       (`price_cache`), Z-3 aus der KURSREIHE (`price_history_ohlc`). Beide
       beschreiben dasselbe Portfolio. Weichen sie voneinander ab, stimmt eine
       der beiden Datenquellen nicht - und man sieht es sofort, statt es zu
       suchen.

    Genau diese Abweichung lag am 06.08. bei ueber 100 Prozent, ohne dass es
    irgendwo auffiel: die Kursreihe fuehrte 19 gehaltene Symbole gar nicht (die
    FX-Ableitung wurde an 87 von 91 Tagen verworfen), und unter denen lag ein
    Symbol mit dem Kurs eines voellig anderen Instruments. Eine der beiden
    Zahlen war immer falsch - nur nebeneinander gestellt wurden sie nie.
    """
    try:
        from agent.portfolio_historie import pruefe_z3
        import config as config_module
        z3 = pruefe_z3(
            conn, schwelle_prozent=config_module.load_config()["ziele"]["max_drawdown_prozent"]
        )
    except Exception as exc:            # Nebenblock darf die Seite nie toeten
        logger.info("Z-3-Status fuer die Remote-Seite nicht ermittelbar: %s", exc)
        return None

    reihe = db.get_portfolio_wert_historie(conn)
    letzter = reihe[-1] if reihe else None
    reihen_wert = letzter["wert_eur"] if letzter and "wert_eur" in letzter.keys() else None
    abweichung = None
    if reihen_wert and portfolio_value_eur:
        abweichung = abs(reihen_wert - portfolio_value_eur) / portfolio_value_eur * 100.0
    return {
        **z3,
        "reihen_wert_eur": reihen_wert,
        "reihen_tag": letzter["datum"] if letzter and "datum" in letzter.keys() else None,
        "snapshot_wert_eur": portfolio_value_eur,
        "abweichung_prozent": abweichung,
        "symbole_ohne_kurs": (letzter["symbole_ohne_kurs"]
                              if letzter and "symbole_ohne_kurs" in letzter.keys() else None),
    }


@_gecacht
def _get_hedge_wirksamkeit(conn: sqlite3.Connection, watchlist: list) -> dict | None:
    """Hat die Absicherung gewirkt? Siehe agent/portfolio_historie.py::
    compute_hedge_wirksamkeit() - SQN/Expectancy sind fuer diese Klasse die
    falsche Frage, deshalb eine eigene Karte statt einer Zeile in der
    Systemguete."""
    from datetime import date, timedelta

    from agent.portfolio_historie import compute_hedge_wirksamkeit

    ab = (date.today() - timedelta(days=90)).isoformat()
    return compute_hedge_wirksamkeit(conn, ab_datum=ab, watchlist=watchlist)


@_gecacht
def _get_themenfeld_erfolg(conn: sqlite3.Connection) -> dict | None:
    """Traf die Richtungsaussage der These? Siehe agent/themenfeld_erfolg.py -
    eine These ist eine Aussage ueber einen Korb, keine Trade-Folge, deshalb
    eine eigene Karte statt einer Zeile in der Systemguete."""
    from agent.themenfeld_erfolg import compute_themenfeld_erfolg

    return compute_themenfeld_erfolg(conn)


@_gecacht
def _get_wartende_themen(conn: sqlite3.Connection) -> dict | None:
    """Welche Themen-Vorschlaege warten, und wann werden sie reif? (2026-08-07)

    Siehe agent/kategorie_vorschlaege.py::wartende_vorschlaege(). Auf die
    Uebersichtsseite gehoert davon vor allem EINE Zahl: wie viele Kandidaten am
    SELBEN Tag reif werden. Uebersteigt sie das freie Budget, entscheidet die
    Gleichzeitigkeits-Moderation - und das gehoert mit Wochen Vorlauf gesehen,
    nicht am Tag selbst."""
    from agent.kategorie_vorschlaege import wartende_vorschlaege

    return wartende_vorschlaege(conn)


def _get_parameter_overview() -> list[dict]:
    """Parameter-Übersicht-Karte (2026-07-17) - reiner Lesezugriff auf die
    Kap.-15-Kalibrierungsparameter aus config.yaml (siehe
    agent/krypto/regelwerk_parameter.py::build_parameter_overview())."""
    from agent.krypto.regelwerk_parameter import build_parameter_overview

    return build_parameter_overview(config_module.load_config())


def _get_budget_heute(conn: sqlite3.Connection) -> dict:
    """Budget-Sichtbarkeit fuer alle 3 Tiers des gemeinsamen Tagesbudgets
    (docs/budget_queue_design.md) - reiner Lesezugriff auf bereits vorhandene
    Zaehlfunktionen, keine neue Logik. taegliches_budget_gesamt ist EIN
    gemeinsamer Deckel ueber Hebel+Marktscan+Spot (kein Budget pro Tier) -
    war und ist Krypto-spezifisch kalibriert (Hebel/Marktscan haben ohnehin
    kein Nicht-Krypto-Aequivalent).

    LLM-Budget-Konsistenzpruefung (2026-07-18): `spot` zaehlte bisher
    STILLSCHWEIGEND auch die automatischen Multi-Asset-Batch-Signale
    (Aktien/Rohstoffe/Hedge/Themen-ETF) mit, da beide in dieselbe
    signals-Tabelle schreiben - verzerrte das angezeigte X/taegliches_budget_
    gesamt-Verhaeltnis nach oben, sobald der 12h-Multi-Asset-Batch lief.
    `spot` ist jetzt Krypto-only gefiltert, Multi-Asset-Verbrauch wird
    separat als `multi_asset_heute` ausgewiesen statt unsichtbar
    eingerechnet.

    `zai_gegenpruefung_heute` (2026-07-27, Nutzer-Fund): Z.ai ist seit dem
    Gegenpruefungs-Umbau (26.07.) NICHT mehr Teil von `verbraucht_gesamt`/
    `gesamt` (kein primaerer Analyst mehr, keine Ressourcen-Konkurrenz zum
    B-Tagesbudget) - laeuft aber weiterhin real im Hintergrund. Separat
    ausgewiesen statt in die Hauptzahl gemischt, aus demselben Grund wie
    `multi_asset_heute`."""
    config_dict = config_module.load_config()
    gesamt = config_dict.get("budget_allocator", {}).get("taegliches_budget_gesamt", 15)
    krypto_symbole = {a.symbol for a in config_module.get_watchlist() if a.assetklasse == "krypto"}
    hebel = db.count_real_hebel_signals_today(conn)
    marktscan = db.count_real_marktscan_writeups_today(conn)
    spot_gesamt = db.count_real_signals_today(conn)
    spot = db.count_real_signals_today(conn, erlaubte_symbole=krypto_symbole)
    return {
        "hebel": hebel,
        "marktscan": marktscan,
        "spot": spot,
        "verbraucht_gesamt": hebel + marktscan + spot,
        "gesamt": gesamt,
        "multi_asset_heute": spot_gesamt - spot,
        # Rein informativ (2026-07-27), KEIN Tagesdeckel - siehe
        # count_zai_gegenpruefung_calls_today()-Docstring.
        "zai_gegenpruefung_heute": db.count_zai_gegenpruefung_calls_today(conn),
    }


def _get_marktscan_last(conn: sqlite3.Connection) -> dict | None:
    candidates = db.get_marktscan_candidates(conn, limit=500)
    if not candidates:
        return None
    latest_run_id = candidates[0].scan_run_id  # bereits DESC nach discovered_at sortiert
    latest_run = [c for c in candidates if c.scan_run_id == latest_run_id]
    treffer = [c for c in latest_run if c.einstufung in _TREFFER_EINSTUFUNGEN]
    return {
        "discovered_at": latest_run[0].discovered_at,
        "kandidaten": len(latest_run),
        "treffer": len(treffer),
    }


def _tail_log_errors(log_path: Path, max_lines: int, max_read_bytes: int = 200_000) -> list[str]:
    """Liest nur die letzten ~200 KB der Logdatei (Seek vom Ende), nicht die
    komplette Datei - die rotierende Logdatei kann bis zu 5 MB gross sein."""
    if not log_path.exists():
        return []
    try:
        with log_path.open("rb") as f:
            f.seek(0, 2)
            size = f.tell()
            f.seek(max(0, size - max_read_bytes))
            chunk = f.read().decode("utf-8", errors="replace")
    except OSError:
        return []

    error_lines = [line for line in chunk.splitlines() if " ERROR " in line or " CRITICAL " in line]
    return error_lines[-max_lines:]
