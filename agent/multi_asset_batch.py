"""Multi-Asset-Batch (2026-07-18) - automatischer Signal-Batch fuer Aktien/
Rohstoffe/Hedge/Themen-ETFs (VST/PLTR, OD7N/OD7H/OD7C/OD7L, DBPK/3QSS,
VVMX/X136/EXH3/CEBS/ISOC - 13 Assets). Bisher NUR ueber den manuellen "Signal
berechnen"-Klick in ui/signals_view.py erreichbar - im Gegensatz zu Krypto
(agent/krypto/budget_allocator.py, 15-Min-Takt) gab es dafuer KEINE
automatische Bewertung (Nutzer-Fund 2026-07-18: das letzte VST-Signal war 3
Tage alt, kein einziger automatischer Versuch seit Erstellung der Rohstoff/
Hedge-Pipelines).

Nachtrag (gleicher Tag, Multi-Asset-Vollstaendigkeitspruefung): die 5
Themen-ETFs standen zu diesem Zeitpunkt bereits als Watchlist-Eintraege in
config.yaml, aber OHNE jede Pipeline (weder manuell noch automatisch) -
agent/themen_etf/ + diese Erweiterung schliessen die Luecke.

Bewusst EIGENER, separater Job (nicht Tier 4 im bestehenden Budget-
Allocator, siehe Regelwerksmanual-Nachtrag fuer die volle Begruendung):
- Die dortige strikte 1>2>3-Kaskade (Hebel>Marktscan>Spot) wuerde ein
  Tier 4 an geschaeftigen Tagen nie erreichen - genau das Problem, das
  hier geloest werden soll.
- Aktien/Rohstoffe/Hedge bewegen sich strukturell langsamer (Boersenzeiten,
  Wochenenden, 5-Tage-OHLC-Staleness-Schwelle vs. Kryptos 2 Tage) - der
  15-Min-Krypto-Takt waere fuer diese Assetklassen verschwendet.
- Nutzt dasselbe gemeinsame LLM-Tagesbudget (count_real_llm_calls_today_by_
  provider zaehlt bereits assetklassen-uebergreifend ueber die signals-
  Tabelle) OHNE die gut getestete Krypto-Kaskade anzufassen (kein
  Regressionsrisiko fuer einen kritischen, funktionierenden Pfad).

Cooldown bewusst NUR 2-stufig (gehalten/beobachtet), kein drittes
"ausgemustert"-Level wie bei Krypto - alle 13 Assets sind aktuell
beobachtungsstatus="beobachtung", ein ausgemustertes Multi-Asset-Symbol
existiert noch nicht. "Gehalten" wird wie bei Krypto (signal_batch.py)
live aus der holdings-Tabelle abgeleitet, nicht aus einem statischen Feld.

Keine Marktscan-Aequivalent-Logik - feste, kleine Watchlist (13 Assets),
keine Discovery (Multi-Asset-Roadmap Phase 4, bewusst zurueckgestellt)."""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone

import database.db as db
from agent import provider_sperre

logger = logging.getLogger(__name__)


@dataclass
class MultiAssetBatchResult:
    verarbeitet: list[str] = field(default_factory=list)
    fehlgeschlagen: list[str] = field(default_factory=list)
    uebersprungen_cooldown: int = 0
    provider_je_symbol: dict[str, str] = field(default_factory=dict)
    ergebnis_objekt: dict[str, object] = field(default_factory=dict)
    # DICTS statt Einzelfelder je Anbieter (2026-08-09, C1) - identisch zu
    # AllocationResult, siehe dortige Begruendung. Beide Ketten muessen
    # dieselbe Form haben, sonst laufen sie auseinander.
    calls_verbraucht: dict[str, int] = field(default_factory=dict)
    budget_erschoepft: dict[str, bool] = field(default_factory=dict)
    # Wie viele Faellige lagen in einem manuellen Schwerpunkt und wurden
    # vorgezogen (2026-08-09, Schritt 6). Steht in der Log-Zeile des Jobs -
    # eine Priorisierung, die niemand sieht, ist von keiner nicht zu
    # unterscheiden.
    vorgezogen_schwerpunkt: int = 0


def _kandidaten(watchlist: list) -> list:
    from agent.hedge.pipeline import ist_hedge_instrument

    kandidaten = [
        a for a in watchlist
        if a.assetklasse in ("aktien", "rohstoffe") or ist_hedge_instrument(a)
        # Themen-ETFs (2026-07-18, Multi-Asset-Vollstaendigkeitspruefung): restliche
        # assetklasse=="etf"-Assets, die KEINE Hedge-Instrumente sind (VVMX/X136/
        # EXH3/CEBS/ISOC) - standen bis hierher als einzige Watchlist-Assets ganz
        # ohne Pipeline da, siehe agent/themen_etf/pipeline.py Modul-Docstring.
        or (a.assetklasse == "etf" and not ist_hedge_instrument(a))
    ]
    # 2026-07-19, Konsistenz-Check ueber alle Assetklassen (analog zum Krypto-
    # coingecko_id-Fix in agent/krypto/signal_batch.py): Aktien UND Themen-
    # ETFs brauchen asset.yfinance_symbol fuer generate_signal() (siehe dortige
    # _ensure_ohlc_backfilled()-Guards) - ohne ID waere der Batch-Slot bei
    # JEDEM Lauf verschwendet worden (Fixed-HALTEN ohne groq_raw_response,
    # also fuer immer "nie berechnet"). Rohstoffe/Hedge NICHT betroffen -
    # Rohstoffe nutzen einen hartkodierten Futures-Ticker (SYMBOL_ZU_FUTURES_
    # TICKER), Hedge braucht ueberhaupt keine OHLC-Historie.
    return [
        a for a in kandidaten
        if a.assetklasse == "rohstoffe" or ist_hedge_instrument(a) or a.yfinance_symbol
    ]


def _pipeline_fuer(asset):
    if asset.assetklasse == "aktien":
        from agent.aktien.pipeline import generate_signal
        return generate_signal
    if asset.assetklasse == "rohstoffe":
        from agent.rohstoff.pipeline import generate_signal
        return generate_signal
    from agent.hedge.pipeline import ist_hedge_instrument
    if asset.assetklasse == "etf" and not ist_hedge_instrument(asset):
        from agent.themen_etf.pipeline import generate_signal
        return generate_signal
    from agent.hedge.pipeline import generate_signal
    return generate_signal


def _ist_faellig(
    letztes_signal, gehalten: bool, cooldown_gehalten_stunden: float, cooldown_beobachtet_stunden: float,
    re_evaluierung_faellig: bool = False,
) -> bool:
    # Re-Evaluierung-faellig-Vorrang (2026-08-01, Roadmap-Schritt 3: Ausweitung
    # der Spot-Verkaufs-Luecke-Fixes auf Aktien/Rohstoffe/Themen-ETF, analog
    # zu agent/krypto/signal_batch.py::select_assets_due_for_signal()) - ein
    # erreichtes halte_kriterium ueberstimmt den regulaeren 2-stufigen
    # Cooldown, loest aber KEINEN automatischen Verkauf aus (siehe database/
    # db.py::get_symbole_mit_erreichtem_halte_kriterium()-Docstring).
    if re_evaluierung_faellig:
        return True
    if letztes_signal is None:
        return True
    letzter_zeitpunkt = datetime.fromisoformat(letztes_signal.created_at)
    if letzter_zeitpunkt.tzinfo is None:
        letzter_zeitpunkt = letzter_zeitpunkt.replace(tzinfo=timezone.utc)
    alter_stunden = (datetime.now(timezone.utc) - letzter_zeitpunkt).total_seconds() / 3600
    schwelle = cooldown_gehalten_stunden if gehalten else cooldown_beobachtet_stunden
    return alter_stunden >= schwelle


def run_multi_asset_batch(
    conn_factory,
    watchlist: list,
    coingecko_client,
    config_dict: dict,
    gemini_client=None,
    mistral_client=None,
    zai_client=None,
    openrouter_client=None,
) -> MultiAssetBatchResult:
    """Kettenreihenfolge seit 2026-08-09: Gemini -> OpenRouter -> Mistral -
    identisch zu agent/krypto/budget_allocator.py, Begruendung steht dort im
    Modul-Docstring. Zwei Ketten mit verschiedener Reihenfolge waeren nicht zu
    erklaeren und wuerden garantiert auseinanderlaufen.

    Ob OpenRouter mitspielt, entscheidet allein, ob hier ein Client ankommt -
    dieselbe Bauart wie bei `mistral_client`/`gemini_client`. Der Schalter
    `budget_allocator.openrouter_aktiv` wird in main.py ausgewertet."""
    result = MultiAssetBatchResult()
    cfg = config_dict.get("multi_asset_batch", {})
    if not cfg.get("aktiv", True):
        return result

    cooldown_gehalten = cfg.get("cooldown_stunden_gehalten", 24)
    cooldown_beobachtet = cfg.get("cooldown_stunden_beobachtet", 72)
    # Dieselben Budget-Werte wie der Krypto-Allocator (agent/krypto/
    # budget_allocator.py) - EIN gemeinsames Tagesbudget je Provider, kein
    # separater Deckel fuer Multi-Asset (die 8 Kandidaten sind eine kleine
    # Ergaenzung zum bestehenden Verbrauch, kein eigenes Kontingent noetig).
    ba_cfg = config_dict.get("budget_allocator", {})
    mistral_budget = ba_cfg.get("mistral_taegliches_budget", 150)
    gemini_budget = ba_cfg.get("gemini_taegliches_budget", 200)
    openrouter_budget = ba_cfg.get("openrouter_taegliches_budget", 400)

    conn = conn_factory()
    try:
        gehaltene_symbole = {
            h.symbol for h in db.get_all_holdings(conn)
            if (h.quantity or 0.0) + (h.staked_quantity or 0.0) > 0.0
        }
        # Re-Evaluierung-faellig (2026-08-01, Schritt 3): Themen-ETF teilt sich
        # assetklasse=="etf" mit Hedge - Hedge bewusst ausgeschlossen (nicht Teil
        # dieser Roadmap-Runde, siehe agent/hedge/pipeline.py Modul-Docstring
        # fuer die eigenstaendige Hedge-Handelslogik ohne halte_kriterium-Aequivalent).
        from agent.hedge.pipeline import SYMBOL_ZU_HEBEL_FAKTOR as _hedge_symbole_fuer_ausschluss  # Mengendifferenz, kein Praedikat
        re_eval_symbole = db.get_symbole_mit_erreichtem_halte_kriterium(
            conn, watchlist, assetklassen=frozenset({"aktien", "rohstoffe", "etf"}),
        ) - set(_hedge_symbole_fuer_ausschluss)
        faellige = []
        for asset in _kandidaten(watchlist):
            gehalten = asset.symbol in gehaltene_symbole
            letztes = db.get_latest_signal(conn, asset.symbol)
            if _ist_faellig(
                letztes, gehalten, cooldown_gehalten, cooldown_beobachtet,
                re_evaluierung_faellig=asset.symbol in re_eval_symbole,
            ):
                faellige.append(asset)
            else:
                result.uebersprungen_cooldown += 1
        # SCHRITT 6 - ALLOCATOR-PRIORITAET (S-4, 2026-08-09).
        #
        # Die Luecke, die das schliesst, steht im Gesamtkonzept als
        # "Signal mit Fokus: der Allocator kennt die Thesen nicht". Ein manuell
        # gesetzter Schwerpunkt hatte bis hierher UEBERHAUPT KEINE Wirkung auf
        # die Verarbeitung - Schritt 3 hat den Schalter gebaut, angeschlossen
        # war er nirgends ("die Schutzwirkung ist gegenstandslos geworden, sie
        # wird erst in Schritt 6 wieder greifen").
        #
        # STABILE PARTITION, KEIN RE-SORT. Schwerpunkt-Assets kommen nach vorn,
        # alle anderen behalten ihre bisherige Reihenfolge, und innerhalb beider
        # Gruppen aendert sich nichts. Bewusst NICHT nach Trendstaerke oder
        # Score sortiert - das Gesamtkonzept warnt ausdruecklich: ein Allocator,
        # der nach Trendstaerke priorisiert, tut ohne die manuellen Schwerpunkte
        # systematisch das Gegenteil von antizyklisch.
        #
        # WAS DAS AENDERT UND WAS NICHT: nur die REIHENFOLGE, nicht die Auswahl
        # - dieser Batch hat keinen Stueckzahl-Deckel, es werden ohnehin alle
        # Faelligen verarbeitet. Spuerbar wird die Prioritaet erst, wenn mitten
        # im Lauf ein Anbieter-Tagesbudget auslaeuft oder der Circuit Breaker
        # zuschlaegt: dann bekommen die vorderen noch ein Signal, die hinteren
        # nicht.
        #
        # REICHWEITE, offen benannt: nur 13 der 57 Watchlist-Assets tragen
        # ueberhaupt eine `hauptgruppe` (7 ETF, 4 Rohstoffe, 2 Aktien) - KEIN
        # einziges Krypto-Asset. Die Krypto-Kette kann davon also nicht
        # profitieren, weil dort nichts zuzuordnen ist. Ob Krypto-Assets ein
        # Themenfeld bekommen sollen, ist eine inhaltliche Entscheidung und
        # bleibt offen.
        #
        # Bei leerer `schwerpunkte.manuell`-Liste ist die Partition ein No-Op -
        # `ist_manueller_schwerpunkt()` liefert dann durchgehend False und die
        # Reihenfolge bleibt Zeichen fuer Zeichen dieselbe.
        import config as _config

        # EINE Schleife statt zweier Listenfilter: `a not in bevorzugt` wuerde
        # Dataclass-Objekte ueber `==` vergleichen und bei wertgleichen Assets
        # das falsche Element aussortieren.
        bevorzugt, uebrige = [], []
        for a in faellige:
            ziel = bevorzugt if _config.ist_manueller_schwerpunkt(
                getattr(a, "hauptgruppe", None),
                getattr(a, "unterkategorie", None)) else uebrige
            ziel.append(a)
        if bevorzugt:
            gesamt = len(faellige)
            faellige = bevorzugt + uebrige
            result.vorgezogen_schwerpunkt = len(bevorzugt)
            logger.info(
                "Multi-Asset-Batch: %d von %d faelligen Assets liegen in einem "
                "manuellen Schwerpunkt und werden vorgezogen (%s).",
                len(bevorzugt), gesamt,
                ", ".join(a.symbol for a in bevorzugt),
            )
        # ECHTE AUFRUFE statt erzeugter Datensaetze (2026-08-09, Teil B) -
        # identisch zu budget_allocator.py, siehe dortige Begruendung. Beide
        # Ketten muessen denselben Zaehler lesen, sonst laufen sie auseinander.
        #
        # OPENROUTER STEHT HIER MIT DEMSELBEN VORBEHALT WIE IM KRYPTO-ALLOCATOR
        # (2026-08-09, Teil C3): der DB-Zaehler ist richtig - `zaehle_aufruf()`
        # sitzt in `_ein_call()` und zaehlt jeden HTTP-Aufruf der Modell-
        # Rotation einzeln. Die Hochzaehlung INNERHALB dieses Laufs unten
        # addiert dagegen +1 je erzeugtem Signal und liegt damit bis zu dreimal
        # zu niedrig. Bewusst nicht repariert: beim naechsten Lauf wird ohnehin
        # wieder aus der DB gelesen, die Abweichung lebt maximal einen Lauf.
        tages_verbraucht = {
            "mistral": db.get_llm_budget_zaehler(conn, "mistral"),
            "gemini": db.get_llm_budget_zaehler(conn, "gemini"),
            "openrouter": db.get_llm_budget_zaehler(conn, "openrouter"),
        }
        # DER BREAKER WIRD VOR DER SCHLEIFE AUS api_health_status VORBELEGT:
        # eine Sperre, die erst nach drei Fehlschlaegen greift und beim
        # naechsten Lauf vergessen ist, verhindert bei ein bis zwei Kandidaten
        # je Lauf fast nichts.
        #
        # DIESE ZEILE STAND BIS ZUM 2026-08-09 UNTERHALB DES `finally`-BLOCKS -
        # also NACH `conn.close()`. `vorbelegte_sperre()` faengt jede Exception
        # ab und liefert dann eine leere Sperre, sichtbar nur als logger.info:
        # die Vorbelegung hat in dieser Kette folglich NIE gegriffen, waehrend
        # sie im Krypto-Allocator seit dem 07.08. funktionierte. Empirisch
        # belegt (offene Verbindung sperrt Mistral, geschlossene sperrt nichts).
        # Genau das Muster aus Memory feedback_fail_soft_ist_fail_silent - der
        # Fehler war da, aber er war leise. `teste_provider_sperre.py` prueft
        # bisher nur, DASS das Modul hier verdrahtet ist, nicht dass es wirkt.
        #
        # OPENROUTER TEILT SICH `api_health_status` MIT DER GEGENPRUEFUNG -
        # beide unter der Quelle "openrouter". Ein dauerhafter Fehler dort
        # sperrt auch diese Kette. Das ist gewollt: 401/402/403 sind
        # Kontofragen und gelten fuer jede Verwendung desselben Schluessels.
        sperre = provider_sperre.vorbelegte_sperre(
            conn, ("mistral", "gemini", "openrouter"))
    finally:
        conn.close()
    tages_budget = {
        "mistral": mistral_budget,
        "gemini": gemini_budget,
        "openrouter": openrouter_budget,
    }

    def _mit_conn(fn):
        """Eigene Connection je Call (gleiches Muster wie budget_allocator.py::
        _mit_conn()) - ein LLM-Call ist potenziell langsam, eine gemeinsame
        lang gehaltene Connection ueber alle Kandidaten waere unnoetig
        fehleranfaellig."""
        c = conn_factory()
        try:
            return fn(c)
        finally:
            c.close()

    # 2026-07-22, echter Fund (DBPK+3QSS im selben Lauf beide NACHKAUFEN-
    # empfohlen, siehe agent/hedge/pipeline.py::_compute_portfolio_exposure()-
    # Docstring): Hedge-Kandidaten werden hier sequenziell verarbeitet, aber
    # jeder Aufruf liest den tatsaechlichen DB-Bestand unabhaengig - ohne
    # diesen Akkumulator wuerden zwei Hedge-Instrumente im selben Lauf
    # denselben (noch nicht durch eine echte Ausfuehrung veraenderten)
    # Ausgangsbestand sehen und in Summe ueber das Ziel-Maximum hinaus
    # vorschlagen koennen. Nur fuer Hedge-Symbole relevant, bleibt fuer
    # Aktien/Rohstoffe/Themen-ETF bei 0.0 (kein Effekt, kein extra kwarg).
    from agent.hedge.pipeline import (
        SYMBOL_ZU_HEBEL_FAKTOR as _hedge_hebel_faktoren, ist_hedge_instrument,
    )

    hedge_effektiv_vorgeschlagen_usd = 0.0

    for asset in faellige:
        pipeline_fn = _pipeline_fuer(asset)
        schluessel = asset.symbol
        ist_hedge = ist_hedge_instrument(asset)
        extra_kwargs = (
            {"bereits_vorgeschlagen_effektiv_usd": hedge_effektiv_vorgeschlagen_usd} if ist_hedge
            # Re-Evaluierung-faellig (2026-08-01, Schritt 4): Hedge hat kein
            # halte_kriterium-Aequivalent und generate_signal() dort kennt den
            # Parameter nicht - daher nur fuer Aktien/Rohstoffe/Themen-ETF.
            else {"war_re_evaluierung_faellig": asset.symbol in re_eval_symbole}
        )
        # REIHENFOLGE Gemini -> OpenRouter -> Mistral (2026-08-09, Teil C3) -
        # identisch zum Krypto-Allocator.
        calls = []
        if gemini_client is not None:
            calls.append(("gemini", lambda a=asset, fn=pipeline_fn, kw=extra_kwargs: _mit_conn(
                lambda c: fn(a, watchlist, c, gemini_client, coingecko_client, zai_client=zai_client, **kw)
            )))
        if openrouter_client is not None:
            calls.append(("openrouter", lambda a=asset, fn=pipeline_fn, kw=extra_kwargs: _mit_conn(
                lambda c: fn(a, watchlist, c, openrouter_client, coingecko_client, zai_client=zai_client, **kw)
            )))
        if mistral_client is not None:
            calls.append(("mistral", lambda a=asset, fn=pipeline_fn, kw=extra_kwargs: _mit_conn(
                lambda c: fn(a, watchlist, c, mistral_client, coingecko_client, zai_client=zai_client, **kw)
            )))

        ok = False
        last_exc: Exception | None = None
        for provider_name, call_fn in calls:
            if provider_name in tages_budget and tages_verbraucht[provider_name] >= tages_budget[provider_name]:
                # KEIN Fehler, der hier repariert wird - eine Ergaenzung, die C1
                # bewusst aufgeschoben hat. C1 legte `budget_erschoepft` in
                # MultiAssetBatchResult neu an, ausdruecklich als reine
                # Formangleichung an AllocationResult ("C1 ist reine Form, keine
                # Logik. Die Kettenreihenfolge und OpenRouter kommen in C2/C3").
                # Das Feld war also nicht tot, sondern noch nicht an der Reihe.
                # Hier ist es an der Reihe: ohne diese Zeile ist eine
                # UEBERSPRUNGENE Stufe von aussen nicht von einer GESCHEITERTEN
                # zu unterscheiden - genau der Unterschied, wegen dem der
                # Krypto-Allocator sie fuehrt.
                result.budget_erschoepft[provider_name] = True
                continue
            # CIRCUIT BREAKER (2026-08-07): siehe agent/provider_sperre.py.
            # Ohne ihn versuchte jeder Kandidat zuerst Mistral, kassierte 402
            # und fiel auf Gemini - 142 vergebliche Aufrufe an einem Tag.
            if sperre.ist_gesperrt(provider_name):
                continue
            try:
                res = call_fn()
                if getattr(res, "gate_passed", True) is False:
                    ok = True
                    break
                sperre.melde_erfolg(provider_name)
                result.provider_je_symbol[schluessel] = provider_name
                result.ergebnis_objekt[schluessel] = res
                if provider_name in tages_verbraucht:
                    tages_verbraucht[provider_name] += 1
                    result.calls_verbraucht[provider_name] = tages_verbraucht[provider_name]
                ok = True
                break
            except Exception as exc:
                last_exc = exc
                sperre.melde_fehlschlag(provider_name, exc)
                continue
        if ok:
            result.verarbeitet.append(schluessel)
            if ist_hedge:
                erzeugtes_signal = result.ergebnis_objekt.get(schluessel)
                if (
                    erzeugtes_signal is not None
                    and getattr(erzeugtes_signal, "action", None) in ("KAUFEN", "NACHKAUFEN")
                    and erzeugtes_signal.position_size_usd
                ):
                    hedge_effektiv_vorgeschlagen_usd += (
                        erzeugtes_signal.position_size_usd * _hedge_hebel_faktoren[asset.symbol]
                    )
        else:
            logger.warning("Multi-Asset-Batch: alle Provider fuer %s fehlgeschlagen (letzter Fehler: %s)", schluessel, last_exc)
            result.fehlgeschlagen.append(schluessel)

    return result
