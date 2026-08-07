"""Signal-Pipeline fuer Portfolio-Hedge-Instrumente (2026-07-18) - siehe
agent/hedge/analyst.py Modul-Docstring fuer die Architektur-Begruendung
(portfolio-exposure-basiert statt einzeltitel-technisch).

Live-Fund waehrend der Rohstoff-Pipeline-Verifikation (siehe agent/rohstoff/
pipeline.py): 3QSS (WisdomTree Nasdaq-100 3x Short, IE00BLRPRJ20.SG) hat wie die
Rohstoff-ETCs KEINE yfinance-.history()-Daten - nur fast_info (aktueller Preis)
funktioniert. DBPK (Xtrackers S&P 500 2x Inverse) hat dagegen funktionierende
Kurshistorie. Statt fuer 3QSS wieder eine Futures-Ersatz-Loesung zu bauen (die
fuer ein GEHEBELTES/INVERSES Produkt zusaetzlich eine korrekte taegliche
Rebalancing-Simulation braeuchte, um nicht selbst wieder falsche technische
Level zu erzeugen), wurde bewusst entschieden, GAR KEINE Einzeltitel-Technik-
analyse fuer Hedge-Instrumente zu betreiben (siehe analyst.py) - konsistent
fuer beide Instrumente, und inhaltlich ohnehin die richtige Bewertungsbasis
fuer ein Absicherungs-Overlay (siehe dortigen Docstring)."""
from __future__ import annotations

import json
import logging
import threading
from datetime import datetime, timezone

import agent.kategorie_thesen as kategorie_thesen
import config
import database.db as db
from agent.hedge.analyst import AnalystResponseInvalid, build_facts, call_llm_for_signal
from agent.krypto.backward_tracking import compute_win_rate_fact
from agent.krypto.gegenpruefung import (
    baue_fakten as baue_zai_fakten,
    baue_objektive_fakten as baue_zai_objektive_fakten,
    fuehre_beide_calls_im_hintergrund,
    richtung_aus_action,
)
from agent.krypto.risk_gate import Risikofaktor
from agent.rekonstruktion import QUELLE_REKONSTRUIERT, rekonstruiere
from api.yfinance_history import get_full_ohlc_history
from agent.krypto.llm_provider import llm_model_label
from agent.krypto.makro_analog import get_cached_makro_analog_fact
from agent.krypto.pipeline import compute_current_regime, eur_aus_usd, log_eur_abweichungen
from agent.krypto.risk_gate import (
    DEFAULT_FAZIT_KONSISTENZ_SCHWELLE_HOCH, DEFAULT_FAZIT_KONSISTENZ_SCHWELLE_NIEDRIG,
    _fazit_konsistenz_hinweis, _portfolio_values_usd,
)
from database.models import Signal
from staleness import is_price_stale

logger = logging.getLogger(__name__)

PIPELINE_VERSION = "1"

# Manuell gepflegt (analog SYMBOL_ZU_FUTURES_TICKER in agent/rohstoff/pipeline.py) -
# bei einem neuen Hedge-Instrument hier ergaenzen. hebel_faktor bestimmt, wie viel
# USD "effektive Abdeckung" 1 USD Positionswert liefert (2x/3x taeglich gehebelt).
SYMBOL_ZU_HEBEL_FAKTOR = {
    "DBPK": 2.0,
    "3QSS": 3.0,
}
SYMBOL_ZU_REFERENZ_INDEX = {
    "DBPK": "S&P 500",
    "3QSS": "Nasdaq-100",
}


def ist_hedge_instrument(asset_oder_symbol) -> bool:
    """Ist dieses Asset ein Absicherungs-Instrument? DIE zentrale Abgrenzung.

    WARUM ES DIESE FUNKTION GIBT (2026-08-06). Hedge ist KEINE Assetklasse -
    die Watchlist kennt nur `aktien`, `rohstoffe`, `krypto` und `etf`. DBPK und
    3QSS stehen als `etf` darin und sind nur ueber ihre Mitgliedschaft in
    SYMBOL_ZU_HEBEL_FAKTOR erkennbar. Diese Pruefung stand bisher als
    `asset.symbol in SYMBOL_ZU_HEBEL_FAKTOR` an sechs verstreuten Stellen; eine
    siebte hat sie am 06.08. schlicht vergessen (der neue OHLC-Refresh filterte
    auf eine Assetklasse "hedge", die es nicht gibt, und liess die beiden
    Instrumente aus). Ein Begriff, der an sechs Stellen wiederholt wird, wird an
    der siebten falsch gemacht.

    DIE TRENNUNG, um die es geht - wo GLEICH, wo ANDERS:

    GLEICH wie jedes andere Asset (Datenversorgung ist Datenversorgung):
      - Kursreihe beschaffen und aktuell halten
      - Portfoliobewertung, Tageswert, Eingang in Z-3
      - Staleness-Ueberwachung, Plausibilitaetspruefung der Reihe
      - Signalerzeugung im Multi-Asset-Batch, Cooldown, Budget-Slot

    ANDERS als jedes andere Asset (die Richtung der Bewertung kehrt sich um):
      - ERFOLGSMASS. Ein Hedge, der Geld verliert waehrend das Portfolio
        steigt, hat FUNKTIONIERT. Nach derselben Systemguete gemessen wie ein
        Long-Signal ist das Ergebnis garantiert negativ und garantiert
        bedeutungslos.
      - RICHTUNGSDEUTUNG. KAUFEN = Hedge aufbauen = baerische Gesamtmarkt-
        erwartung, also SHORT (richtung_aus_action(ist_hedge_invertiert=True)).
      - POSITIONSGROESSE. Sie folgt dem Long-Exposure des Portfolios, nicht
        einer Kante im Instrument selbst (_compute_portfolio_exposure()).
      - TECHNISCHE ANALYSE. Bewusst keine - siehe Modul-Docstring. Bei jedem
        anderen Asset ist sie die Grundlage.
      - REGIME. Umgekehrte Wirkrichtung: ein steigendes Aktienregime ist fuer
        ein inverses Produkt das SCHLECHTE Umfeld (offen, Punkt D-d).

    Nimmt ein Asset-Objekt oder ein Symbol - Aufrufer haben mal das eine, mal
    das andere zur Hand, und ein zweiter Name dafuer waere schon wieder eine
    Abgrenzung zu viel.
    """
    symbol = getattr(asset_oder_symbol, "symbol", asset_oder_symbol)
    return symbol in SYMBOL_ZU_HEBEL_FAKTOR


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _fixed_signal(symbol: str, action: str, gate_passed: bool, gate_reason: str | None, facts: dict | None = None) -> Signal:
    return Signal(
        symbol=symbol,
        created_at=_now(),
        action=action,
        gate_passed=gate_passed,
        gate_reason=gate_reason,
        risk_veto=False,
        facts_json=json.dumps(facts or {}, ensure_ascii=False),
        pipeline_version=PIPELINE_VERSION,
    )


def _compute_portfolio_exposure(
    asset, watchlist, conn, latest_prices, config_dict, bereits_vorgeschlagen_effektiv_usd: float = 0.0,
) -> dict:
    """Long-Exposure = Portfolio-Wert OHNE die Hedge-Instrumente selbst und OHNE
    Cash-Aequivalente (Stablecoins) - das ist das Risiko, das potenziell
    abgesichert werden muss. Hedge-Abdeckung = Summe ueber ALLE aktuell
    gehaltenen Hedge-Instrumente, je mit ihrem hebel_faktor multipliziert (1 USD
    in einem 3x-Short-ETF deckt effektiv 3 USD Long-Exposure ab). Das
    verbleibende Budget wird bereits durch DIESES Instruments hebel_faktor
    geteilt - der LLM-Vorschlag (`position_size.usd`) ist der NOTIONAL-Wert
    dieses Instruments, nicht die effektive Abdeckung.

    Nachtrag (2026-07-22, echter Fund: DBPK+3QSS im selben Batch-Lauf beide
    NACHKAUFEN-empfohlen): `bereits_vorgeschlagen_effektiv_usd` (optional,
    Standard 0.0 - kein Verhaltensunterschied bei einem einzelnen Aufruf) ist
    die leverage-adjustierte Summe, die ANDERE Hedge-Instrumente im SELBEN
    Batch-Lauf bereits vorgeschlagen haben (siehe agent/multi_asset_batch.py::
    run_multi_asset_batch()). Wird zusaetzlich von aktuelle_hedge_abdeckung_usd
    abgezogen, BEVOR das verbleibende Budget durch diesen Instruments
    hebel_faktor geteilt wird. Ohne das wuerden zwei im selben Lauf verarbeitete
    Hedge-Kandidaten denselben (noch nicht durch eine echte Ausfuehrung
    veraenderten) DB-Bestand als Ausgangspunkt sehen und in Summe ueber
    ziel_hedge_abdeckung_max_prozent hinaus vorschlagen koennen, ohne dass eine
    der beiden Empfehlungen von der anderen wissen konnte."""
    holdings = db.get_all_holdings(conn)
    holdings_by_symbol = {h.symbol: h for h in holdings}
    total_value_usd, values_by_symbol = _portfolio_values_usd(watchlist, holdings, latest_prices)

    hedge_symbole = set(SYMBOL_ZU_HEBEL_FAKTOR.keys())
    stablecoin_symbole = {a.symbol for a in watchlist if a.ist_cash_aequivalent}
    long_exposure_usd = sum(
        v for sym, v in values_by_symbol.items()
        if sym not in hedge_symbole and sym not in stablecoin_symbole
    )
    aktuelle_hedge_abdeckung_usd = sum(
        values_by_symbol.get(sym, 0.0) * hebel for sym, hebel in SYMBOL_ZU_HEBEL_FAKTOR.items()
    )

    # Live-Fund (2026-07-18, Verifikation gegen echtes Portfolio): _portfolio_values_usd()
    # laesst ein Symbol OHNE bekannten Preis (P-10) einfach aus values_by_symbol weg -
    # ein anderes, tatsaechlich gehaltenes Hedge-Instrument mit fehlendem price_usd
    # (z.B. wegen einer fehlgeschlagenen EUR/USD-Umrechnung, siehe generate_signal()s
    # eigenem price_usd-Gate) wuerde sonst STILLSCHWEIGEND als "0 USD Abdeckung"
    # gezaehlt - aktuelle_hedge_abdeckung_usd waere dann UNTERSCHAETZT, und ein darauf
    # basierender KAUFEN/NACHKAUFEN-Vorschlag koennte das Portfolio unbemerkt
    # ueberhedgen. Fix: erkennen + explizit warnen, UND das verbleibende Budget auf 0
    # deckeln (VERKAUFEN/HALTEN bleiben davon unberuehrt, nur ein Hedge-AUFBAU wird
    # blockiert, solange die Abdeckungs-Rechnung unsicher ist).
    fehlende_preise = [
        sym for sym in hedge_symbole
        if (holdings_by_symbol.get(sym) and (holdings_by_symbol[sym].quantity or 0.0) > 0.0)
        and sym not in values_by_symbol
    ]

    hedge_cfg = config_dict.get("hedge", {})
    max_abdeckung_anteil = hedge_cfg.get("max_abdeckung_anteil", 1.0)
    max_hedge_abdeckung_usd = long_exposure_usd * max_abdeckung_anteil
    verbleibendes_budget_usd = max(
        0.0,
        max_hedge_abdeckung_usd - aktuelle_hedge_abdeckung_usd - bereits_vorgeschlagen_effektiv_usd,
    )

    hebel_faktor = SYMBOL_ZU_HEBEL_FAKTOR[asset.symbol]
    verbleibendes_budget_fuer_instrument_usd = verbleibendes_budget_usd / hebel_faktor
    if fehlende_preise:
        verbleibendes_budget_fuer_instrument_usd = 0.0

    hinweis = (
        "aktuelle_hedge_abdeckung_* summiert ALLE aktuell gehaltenen Hedge-"
        "Instrumente zusammen (leverage-adjustiert), nicht nur dieses eine. "
        "verbleibendes_hedge_budget_usd ist bereits durch den hebel_faktor "
        "DIESES Instruments geteilt - das ist der maximale Notional-Wert, den "
        "eine KAUFEN/NACHKAUFEN-Empfehlung fuer DIESES Instrument haben darf, "
        "ohne ziel_hedge_abdeckung_max_prozent zu ueberschreiten."
    )
    if bereits_vorgeschlagen_effektiv_usd > 0:
        hinweis += (
            f" Zusaetzlich wurden in diesem Batch-Lauf bereits "
            f"{bereits_vorgeschlagen_effektiv_usd:.2f} USD effektive Abdeckung durch "
            "ANDERE Hedge-Instrumente vorgeschlagen (noch nicht ausgefuehrt) - "
            "bereits von verbleibendes_hedge_budget_usd abgezogen, damit die "
            "Summe beider Vorschlaege das Ziel-Maximum nicht ueberschreitet."
        )
    if fehlende_preise:
        hinweis += (
            f" WARNUNG: fuer {', '.join(fehlende_preise)} (ebenfalls gehalten) fehlt "
            "aktuell ein Preis - aktuelle_hedge_abdeckung_usd ist dadurch "
            "UNTERSCHAETZT. verbleibendes_hedge_budget_usd wurde deshalb "
            "vorsorglich auf 0 gesetzt (empfiehl KEIN KAUFEN/NACHKAUFEN, bis die "
            "Abdeckung wieder vollstaendig berechenbar ist - VERKAUFEN/HALTEN "
            "bleiben moeglich)."
        )

    return {
        "ungesichertes_long_exposure_usd": round(long_exposure_usd, 2),
        "aktuelle_hedge_abdeckung_usd": round(aktuelle_hedge_abdeckung_usd, 2),
        "aktuelle_hedge_abdeckung_prozent": (
            round(aktuelle_hedge_abdeckung_usd / long_exposure_usd * 100, 1) if long_exposure_usd > 0 else 0.0
        ),
        "ziel_hedge_abdeckung_max_prozent": max_abdeckung_anteil * 100,
        "verbleibendes_hedge_budget_usd": round(verbleibendes_budget_fuer_instrument_usd, 2),
        "berechnung_unsicher_fehlende_preise": fehlende_preise or None,
        "hinweis": hinweis,
    }, verbleibendes_budget_fuer_instrument_usd


# Ab welchem Anteil des Ziel-Abdeckungsgrades gilt die Absicherung als
# weitgehend aufgebaut? Darueber ist ein Nachkauf ein Ueberhedge-Risiko, kein
# Schutzgewinn (2026-08-07, W2).
_ABDECKUNG_WEITGEHEND_AUFGEBAUT = 0.80
# VIX-Schwellen fuer den "Preis der Versicherung". Derselbe Rohwert wie im
# Regime-Block; die Einordnung passiert hier, weil er fuer Hedge eine ANDERE
# Bedeutung hat als fuer Long-Positionen (siehe compute_risikofaktoren_hedge()).
_VIX_TEUER = 25.0
_VIX_GUENSTIG = 16.0
# Aktionen, bei denen ein Hedge AUFGEBAUT wird - nur dort sind die
# kaufbezogenen Risikofaktoren ueberhaupt anwendbar.
_HEDGE_AUFBAU_AKTIONEN = ("KAUFEN", "NACHKAUFEN")


def compute_risikofaktoren_hedge(
    action: str,
    portfolio_exposure: dict,
    regime_result,
    bull_wahrscheinlichkeit_pct: float | None = None,
    hebel_faktor: float | None = None,
    budget_gedeckelt: bool = False,
    zonen_hinweis: str | None = None,
) -> list[Risikofaktor]:
    """Risikofaktoren fuer ein Absicherungs-Instrument (2026-08-07, W2).

    WARUM ES DAFUER EINE EIGENE FUNKTION BRAUCHT. compute_risikofaktoren()
    prueft eine LONG-KAUFIDEE: Regime-Konflikt gegen LONG, Retail-Long-Bias,
    Konfluenz, Gegenszenario. Auf eine Absicherung angewandt stehen saemtliche
    Vorzeichen falsch herum - ein baerisches Regime ist fuer einen Long ein
    Warnsignal und fuer einen Hedge die Bestaetigung. Deshalb kein Parameter an
    der bestehenden Funktion, sondern eine eigene mit eigener Logik.

    Bis zum 07.08. lieferte die Hedge-Pipeline GAR KEINE Risikofaktoren; die
    E-Mail schrieb "Keine strukturierten Risikofaktoren verfuegbar", was wie ein
    Datenfehler aussah und keiner war.

    DIE FAKTOREN, jeder mit seiner umgekehrten Wirkrichtung:

    1. ABDECKUNGSGRAD (Kontext). Wo steht die Absicherung heute? Ausgangspunkt
       jeder weiteren Entscheidung, kein Urteil - deshalb ist_kontext.
    2. WEITGEHEND AUFGEBAUT. Je naeher am Zielwert, desto weniger bringt ein
       Nachkauf und desto mehr kostet er. Bei einer Long-Position waere eine
       hohe bestehende Quote kein Argument gegen mehr; bei einer Versicherung
       schon.
    3. VIX ALS PREIS. Hoher VIX heisst teure Absicherung - die Praemie ist
       gestiegen, WEIL der Markt die Gefahr schon sieht. Fuer eine Long-Position
       ist hoher VIX ein Risikosignal, fuer einen Hedge-KAUF ein Kostensignal:
       dieselbe Zahl, entgegengesetzte Konsequenz.
    4. AKTIEN-BAERENMARKT. Aktiv heisst, der Einbruch laeuft bereits. Die
       bestehende Absicherung arbeitet - aber JETZT erst aufzustocken heisst,
       nach dem Schaden Versicherung zu kaufen. Nachlaufender Indikator,
       deshalb bewusst nicht als "positiv" gewertet.
    5. VOLATILITAETS-DRAG. Taeglich zuruecksetzende Hebelprodukte verlieren in
       Seitwaertsmaerkten unabhaengig von der Richtung, je hoeher der Faktor
       desto schneller. Struktureller Preis dieser Instrumente, ohne
       Gegenstueck bei einer ungehebelten Long-Position.
    6. BULL-WAHRSCHEINLICHKEIT. Spiegelbild des Gegenszenarios: bei einem Long
       ist die Baer-Wahrscheinlichkeit das Risiko, bei einem Hedge die
       Bull-Wahrscheinlichkeit.
    7. BUDGET-DECKEL. Wurde die Empfehlung bereits gekuerzt, gehoert das
       sichtbar gemacht - nicht nur in der Positionsgroesse.

    Bei allem ausser KAUFEN/NACHKAUFEN bleibt nur der Kontextfaktor: fuer ein
    HALTEN oder VERKAUFEN ist "wie teuer waere der Zukauf" gegenstandslos.
    """
    faktoren: list[Risikofaktor] = []
    exposure = portfolio_exposure or {}

    abdeckung = exposure.get("aktuelle_hedge_abdeckung_prozent")
    ziel_max = exposure.get("ziel_hedge_abdeckung_max_prozent")
    if abdeckung is not None and ziel_max:
        faktoren.append(Risikofaktor(
            "Abdeckungsgrad", "neutral",
            f"Die Absicherung deckt aktuell {abdeckung:.1f} % des Long-Exposure ab "
            f"(Ziel maximal {ziel_max:.1f} %).",
            ist_kontext=True,
        ))

    # Verworfene Zonen gehoeren GANZ nach oben und auch dann in die Liste, wenn
    # sonst nichts anwendbar ist - der Nutzer sieht in der Mail sonst nur, dass
    # Stop und Ziel fehlen, ohne zu erfahren warum.
    if zonen_hinweis:
        faktoren.append(Risikofaktor("Zonen unbrauchbar", "negativ", zonen_hinweis))

    if action not in _HEDGE_AUFBAU_AKTIONEN:
        return faktoren

    if abdeckung is not None and ziel_max and abdeckung / ziel_max >= _ABDECKUNG_WEITGEHEND_AUFGEBAUT:
        faktoren.append(Risikofaktor(
            "Absicherung weitgehend aufgebaut", "negativ",
            f"{abdeckung:.1f} % von maximal {ziel_max:.1f} % sind bereits abgesichert. "
            f"Ein Nachkauf bringt wenig zusaetzlichen Schutz, kostet aber die volle "
            f"Praemie - und erhoeht das Ueberhedge-Risiko, falls der Markt dreht.",
        ))

    vix = getattr(regime_result, "vix_wert", None)
    if vix is not None:
        if vix >= _VIX_TEUER:
            faktoren.append(Risikofaktor(
                "Versicherung ist teuer (VIX)", "negativ",
                f"VIX bei {vix:.1f}. Die Praemie ist hoch, WEIL der Markt die Gefahr "
                f"bereits einpreist - jetzt aufzustocken heisst teuer zu kaufen, was "
                f"guenstiger zu haben war.",
            ))
        elif vix <= _VIX_GUENSTIG:
            faktoren.append(Risikofaktor(
                "Versicherung ist guenstig (VIX)", "positiv",
                f"VIX bei {vix:.1f}. Absicherung ist billig - der bessere Zeitpunkt, "
                f"Schutz aufzubauen, ist bevor er gebraucht wird.",
            ))

    if getattr(regime_result, "equities_baermarkt_aktiv", False):
        faktoren.append(Risikofaktor(
            "Einbruch laeuft bereits", "negativ",
            "Der Aktien-Baerenmarkt ist aktiv. Die bestehende Absicherung arbeitet "
            "gerade - aber JETZT erst aufzustocken heisst, nach dem Schaden "
            "Versicherung zu kaufen. Der Indikator ist nachlaufend.",
        ))

    if hebel_faktor and hebel_faktor > 1.0:
        faktoren.append(Risikofaktor(
            "Volatilitaets-Drag", "negativ",
            f"Taeglich zuruecksetzendes {hebel_faktor:.0f}x-Produkt: in einem "
            f"Seitwaertsmarkt verliert es unabhaengig von der Richtung, je hoeher der "
            f"Faktor desto schneller. Das spricht gegen langes Halten ohne konkreten "
            f"Anlass.",
        ))

    if bull_wahrscheinlichkeit_pct is not None and bull_wahrscheinlichkeit_pct >= 50.0:
        faktoren.append(Risikofaktor(
            "Gegenszenario Aufwaertsmarkt", "negativ",
            f"Das Modell haelt einen steigenden Markt mit "
            f"{bull_wahrscheinlichkeit_pct:.0f} % fuer wahrscheinlich. Fuer eine "
            f"Absicherung ist das genau das Szenario, in dem sie Geld kostet.",
        ))

    if budget_gedeckelt:
        faktoren.append(Risikofaktor(
            "Hedge-Budget ausgeschoepft", "negativ",
            "Die vorgeschlagene Groesse wurde auf das verbleibende Budget gekuerzt. "
            "Mehr Abdeckung ist ueber die Zielquote hinaus nicht vorgesehen.",
        ))

    return faktoren


def _pruefe_hedge_zonen(result: dict) -> str | None:
    """Stehen Stop und Ziel bei einer Hedge-KAUFEMPFEHLUNG richtig herum?

    DER FUND (07.08., am Export gemessen): **9 von 11** auswertbaren
    Hedge-Kaufsignalen hatten die Zonen VERDREHT - Stop UEBER dem Einstieg, Ziel
    DARUNTER. Beispiel DBPK vom 06.08.:

        Entry 0,1217   Stop 0,1565 (+28,6 %)   Ziel 0,0870 (-28,6 %)

    Bei einer KAUFEN-Empfehlung heisst das: der Stop ist schon beim Einstieg
    ausgeloest, und das Ziel liegt in Verlustrichtung. Beide Symbole betroffen,
    also kein Einzelfall.

    DIE URSACHE ist eine Denkrichtung, nicht ein Rechenfehler: das Modell denkt
    in der MARKTrichtung ("wir wollen, dass der Index faellt") statt in der
    INSTRUMENTENrichtung ("wir kaufen ein inverses Produkt, das steigt, wenn der
    Index faellt"). Der Prompt sagt seit dem 18.07. das Richtige - es reicht
    nicht. Deshalb eine deterministische Wache dahinter.

    WARUM VERWORFEN UND NICHT GETAUSCHT. Ein Tausch waere verlockend: die
    Abstaende sehen plausibel aus (6-29 %), nur die Rollen scheinen vertauscht.
    Aber wir wissen NICHT, was die Zahl bedeuten sollte - ob das Modell den
    Instrumentenpreis meinte und die Richtung verwechselte, oder ob es ueber ein
    Indexniveau nachdachte und es als Instrumentenpreis ausgab. Eine Zahl
    umzudeuten, deren Bedeutung unklar ist, waere genau die stille Annahme, an
    der diese Woche schon mehrfach etwas gescheitert ist.

    Verworfen werden nur die ZONEN. Die Handlungsempfehlung selbst bleibt
    bestehen - sie haengt nicht an ihnen (Regel 9 des Hedge-Prompts: die Zonen
    sind informativer Kontext, keine Kauf-Voraussetzung).

    Rueckgabe: Hinweistext, wenn verworfen wurde, sonst None.
    """
    if result.get("action") not in _HEDGE_AUFBAU_AKTIONEN:
        return None
    entry = (result.get("entry") or {}).get("usd_von") or (result.get("entry") or {}).get("usd_bis")
    stop = (result.get("stop_loss") or {}).get("usd_von") or (result.get("stop_loss") or {}).get("usd_bis")
    ziel = (result.get("take_profit") or {}).get("usd_von") or (result.get("take_profit") or {}).get("usd_bis")
    if entry is None or stop is None or ziel is None:
        return None
    if stop < entry < ziel:
        return None

    result["stop_loss"] = {}
    result["take_profit"] = {}
    return (
        f"Zonen verworfen: bei einer Kaufempfehlung muss der Stop UNTER und das Ziel "
        f"UEBER dem Einstieg liegen. Geliefert wurden Entry {entry:.4f}, Stop "
        f"{stop:.4f}, Ziel {ziel:.4f} - das ist die Marktrichtung statt der "
        f"Instrumentenrichtung. Die Empfehlung bleibt, die Zonen sind unbrauchbar."
    )


def _post_check_hedge(
    parsed: dict, verbleibendes_budget_usd: float, eur_usd_fx_rate: float | None, config_dict: dict,
) -> dict:
    """Deterministischer Deckel (P-10, mirror risk_gate.py::post_check()s RM-1/2-
    Klemm-Logik, aber eigenstaendig - siehe analyst.py Modul-Docstring, warum
    risk_gate.post_check() hier NICHT wiederverwendet wird): kuerzt eine zu
    grosse KAUFEN/NACHKAUFEN-Positionsgroesse auf das verbleibende Hedge-Budget,
    statt die Empfehlung selbst zu verwerfen.

    PLUS Bull-Wahrscheinlichkeits-Deckel (2026-07-18, Multi-Asset-Vollstaendig-
    keitspruefung): das Hedge-Pendant zum Gegenszenario-Deckel aus
    risk_gate.py::post_check(), aber bewusst NICHT 1:1 uebernommen, sondern
    SPIEGELVERKEHRT. Bei einer normalen Directional-Long-Position (Spot/Aktien/
    Rohstoffe) ist eine hohe forecast.bear.probability_pct das Risiko-Szenario
    ("die Position koennte gegen mich laufen") - der bestehende Deckel kappt
    dort folgerichtig die Positionsgroesse. Fuer ein inverses Hedge-Instrument
    (DBPK/3QSS) ist das Verhaeltnis GENAU UMGEKEHRT: die Position GEWINNT bei
    fallenden Kursen, ihr Risiko-Szenario ist eine hohe forecast.bull.
    probability_pct - dann decayt eine grosse, taeglich neu gehebelte Position
    ohne Absicherungsnutzen zu liefern (Volatility-Decay, siehe SYSTEM_PROMPT
    Regel 4). Ein naiv wiederverwendeter Bear-Deckel waere hier funktional
    falschherum gewesen (haette die Positionsgroesse ausgerechnet dann NICHT
    gekappt, wenn der Decay-Effekt am staerksten drueckt)."""
    gedeckelt = False
    result = dict(parsed)
    action = result.get("action")
    if action in ("KAUFEN", "NACHKAUFEN"):
        position_size = result.get("position_size") or {}
        proposed_usd = position_size.get("usd")
        if proposed_usd is not None and proposed_usd > verbleibendes_budget_usd:
            note = (
                f"Von {proposed_usd:.2f} USD auf verbleibendes Hedge-Budget "
                f"{verbleibendes_budget_usd:.2f} USD gekuerzt (deterministisch erzwungen, "
                "Gesamt-Hedge-Abdeckung darf das konfigurierte Maximum nicht ueberschreiten)."
            )
            position_size["usd"] = verbleibendes_budget_usd
            # Nachtrag 2026-07-27 (siehe Regelwerksmanual): der reale Live-Kurs
            # ersetzt den zuvor aus der LLM-Eigenangabe abgeleiteten fx-Wert -
            # eur_aus_usd() statt einer aus proposed_usd/proposed_eur
            # (unverifizierte LLM-Zahlen) berechneten Rate.
            position_size["eur"] = eur_aus_usd(verbleibendes_budget_usd, eur_usd_fx_rate)
            existing_note = position_size.get("note")
            position_size["note"] = f"{existing_note} {note}" if existing_note else note
            result["position_size"] = position_size

        hedge_cfg = config_dict.get("hedge", {})
        bull_pct = ((result.get("forecast") or {}).get("bull") or {}).get("probability_pct")
        schwelle = hedge_cfg.get("bull_wahrscheinlichkeit_schwelle_prozent")
        deckel_anteil = hedge_cfg.get("bull_wahrscheinlichkeit_deckel_anteil")
        if (
            bull_pct is not None and schwelle is not None and deckel_anteil is not None
            and bull_pct >= schwelle
        ):
            position_size = result.get("position_size") or {}
            proposed_usd = position_size.get("usd")
            if proposed_usd is not None:
                gedeckelt_usd = proposed_usd * deckel_anteil
                if gedeckelt_usd < proposed_usd:
                    note = (
                        f"Zusaetzlich auf {deckel_anteil * 100:.0f}% reduziert (Bull-Wahrscheinlichkeit "
                        f"{bull_pct:.0f}% >= Schwelle {schwelle:.0f}% - Decay-Risiko bei anhaltendem "
                        "Aufwaertstrend, Bull-Wahrscheinlichkeits-Deckel)."
                    )
                    position_size["usd"] = gedeckelt_usd
                    position_size["eur"] = eur_aus_usd(gedeckelt_usd, eur_usd_fx_rate)
                    existing_note = position_size.get("note")
                    position_size["note"] = f"{existing_note} {note}" if existing_note else note
                    result["position_size"] = position_size
                    gedeckelt = True

    # Signal-Fazit Konsistenz-Hinweis (2026-07-25) - rein diagnostisch, siehe
    # agent/krypto/risk_gate.py::_fazit_konsistenz_hinweis()-Docstring.
    eigene_einschaetzung = result.get("eigene_einschaetzung") or {}
    fazit_cfg = config_dict.get("signal_fazit", {})
    # Wurde die Groesse gekuerzt? Der Risikofaktor "Hedge-Budget ausgeschoepft"
    # braucht die Information, und sie stand bisher nur im Freitext der
    # position_size.note (2026-08-07, W2).
    result["_budget_gedeckelt"] = bool(gedeckelt)
    result["_zonen_hinweis"] = _pruefe_hedge_zonen(result)
    result["_fazit_konsistenz_hinweis"] = _fazit_konsistenz_hinweis(
        eigene_einschaetzung.get("folgen"),
        result.get("confidence_pct"),
        fazit_cfg.get("konsistenz_schwelle_niedrig", DEFAULT_FAZIT_KONSISTENZ_SCHWELLE_NIEDRIG),
        fazit_cfg.get("konsistenz_schwelle_hoch", DEFAULT_FAZIT_KONSISTENZ_SCHWELLE_HOCH),
    )
    return result



# OHLC-Historie fuer Hedge-Instrumente - NUR ZUR BEWERTUNG (2026-08-06).
#
# ZUERST DIE ABGRENZUNG ZUR BESTEHENDEN ENTSCHEIDUNG, damit hier nichts
# stillschweigend ueberschrieben wird. Der Modul-Docstring haelt fest, dass
# fuer Hedge-Instrumente BEWUSST KEINE Einzeltitel-Technikanalyse betrieben
# wird - konsistent fuer beide Instrumente, und inhaltlich richtig, weil ein
# Absicherungs-Overlay ueber die Portfolio-Exposure bewertet gehoert und nicht
# ueber Chartlevel. DIESE ENTSCHEIDUNG BLEIBT UNANGETASTET: der Analyst
# bekommt weiterhin keine technischen Indikatoren fuer DBPK/3QSS.
#
# WAS SIE NICHT ABDECKT, und das ist die Luecke: die PORTFOLIO-BEWERTUNG. Ohne
# Kursreihe hat eine gehaltene Position keinen Tageswert. DBPK (1.739
# Einheiten) und 3QSS (218) stehen im Mengenkorb der Portfolio-Wertreihe und
# fallen mangels Kurs heraus - mit der Folge, dass Z-3 den Drawdown OHNE die
# Absicherung misst, die ihn daempfen soll. Am 06.08. fehlten 19 von 33
# Symbolen; die beiden Hedges darunter.
#
# Bewertung und Technikanalyse sind zwei verschiedene Zwecke. Die Reihe hier
# zu speichern beruehrt die Analyse-Entscheidung nicht - der Hedge-Analyst
# liest sie schlicht nicht.
#
# ABRUF-TEST 06.08.: OD7N/OD7H/OD7C/OD7L und 3QSS liefern LEER (bestaetigt die
# Liste YFINANCE_HISTORY_UNRELIABLE_TICKERS), DBPK.DE dagegen 4.159 Zeilen.
# Fuer 3QSS bleibt eine Rekonstruktion aus dem Referenzindex der naechste
# Schritt - und der Docstring nennt bereits den Grund, warum sie nicht trivial
# ist: ein taeglich gehebeltes inverses Produkt braucht eine korrekte
# Rebalancing-Simulation, sonst entstehen wieder falsche Werte. Siehe
# Plan_Nicht_Krypto_Umbau_06_08.md, Phase A2.
#
# Groessenordnung ehrlich dazu: die DBPK-Position ist rund 230 EUR wert
# (1.739 x 0,1321). Die Z-3-Korrektur daraus ist klein - richtig ist sie
# trotzdem, und sie ist die Voraussetzung dafuer, den Hedge ueberhaupt je
# bewerten zu koennen.
_HEDGE_HISTORY_STALE_THRESHOLD_TAGE = 3

# Referenzindizes fuer die Rekonstruktion (2026-08-06).
SYMBOL_ZU_INDEX_TICKER = {
    "DBPK": "^GSPC",   # S&P 500
    "3QSS": "^NDX",    # Nasdaq-100
}
_INDEX_SYMBOL_PRAEFIX = "_HEDGE_INDEX_"


def _rekonstruiere_hedge_reihe(conn, asset) -> None:
    """Reihe fuer ein Hedge-Instrument ohne abrufbare Historie (3QSS).

    VERFAHREN: taegliche Rendite = -faktor x Indexrendite, TAG FUER TAG
    VERKETTET. Die Verkettung ist nicht optional: ein taeglich zuruecksetzendes
    Produkt bildet das Faktor-fache der TAGESrendite ab, nicht der
    Gesamtrendite. Der Unterschied ist der Volatilitaets-Drag - schwankt der
    Index +10 %/-10 % im Wechsel, verliert ein 3x-Short trotz seitwaerts
    laufendem Index. An einem konstruierten Fall geprueft: naive Hochrechnung
    haette +5,97 % gesagt, die Verkettung liefert -17,19 %.

    Genau deshalb hat der Modul-Docstring diese Rekonstruktion bisher gemieden -
    sie braucht die korrekte Rebalancing-Simulation, sonst erzeugt sie selbst
    falsche Werte. Die ist jetzt in agent/rekonstruktion.py gebaut und getestet.

    GRENZE: Gebuehren und Swap-Kosten fehlen, und 3QSS notiert in EUR waehrend
    der Nasdaq-100 in USD laeuft - die FX-Bewegung ist in der Reihe nicht
    enthalten. Beides wirkt ueber laengere Zeitraeume zu optimistisch. Die
    Reihe ist als `quelle='rekonstruiert'` markiert und dient der BEWERTUNG,
    nicht der technischen Analyse (die bleibt fuer Hedge-Instrumente bewusst
    ausgeschlossen, siehe Modul-Docstring).
    """
    ticker = SYMBOL_ZU_INDEX_TICKER.get(asset.symbol)
    faktor = SYMBOL_ZU_HEBEL_FAKTOR.get(asset.symbol)
    if not ticker or not faktor:
        logger.info("Keine Rekonstruktion fuer %s - kein Referenzindex hinterlegt", asset.symbol)
        return
    try:
        index_symbol = f"{_INDEX_SYMBOL_PRAEFIX}{asset.symbol}"
        punkte_index = get_full_ohlc_history(ticker, index_symbol, "USD")
        if punkte_index:
            db.upsert_ohlc_points(conn, punkte_index)
        else:
            punkte_index = db.get_ohlc_history(conn, index_symbol, "USD")
        if len(punkte_index) < 2:
            logger.warning("Keine Indexreihe (%s) fuer %s - Rekonstruktion nicht moeglich",
                           ticker, asset.symbol)
            return
        snap = db.get_latest_prices(conn).get(asset.symbol)
        anker = getattr(snap, "price_eur", None) if snap else None
        if not anker or anker <= 0:
            logger.info("Keine Rekonstruktion fuer %s - kein aktueller Preis als Anker",
                        asset.symbol)
            return
        referenz = [{"date": p.date, "close": p.close, "high": p.high, "low": p.low}
                    for p in punkte_index]
        punkte = rekonstruiere(asset.symbol, "EUR", referenz, anker_preis=anker,
                               faktor=float(faktor), invers=True)
        if not punkte:
            logger.warning("Rekonstruktion fuer %s ergab keine Punkte", asset.symbol)
            return
        db.upsert_ohlc_points(conn, punkte, quelle=QUELLE_REKONSTRUIERT)
        logger.info("Hedge-Reihe fuer %s rekonstruiert: %d Punkte aus %s, Faktor %.1fx invers, "
                    "Anker %.4f EUR (quelle=rekonstruiert, Gebuehren und FX NICHT enthalten)",
                    asset.symbol, len(punkte), ticker, faktor, anker)
    except Exception:
        logger.exception("Rekonstruktion fuer %s fehlgeschlagen - Signal laeuft ohne Reihe weiter",
                         asset.symbol)


def _ensure_ohlc_backfilled(conn, asset) -> None:
    """Fail-soft: schlaegt der Abruf fehl, laeuft das Signal ohne Historie
    weiter - genau wie bisher. Die Historie ist ein Gewinn, keine Bedingung."""
    if not getattr(asset, "yfinance_symbol", None):
        return
    try:
        # Eine REKONSTRUIERTE Reihe faellt nicht unter die Staleness-Wache
        # (2026-08-06). Sie haengt an einem Ankerpreis, der sich jeden Tag
        # bewegt; wuerde die Wache greifen, bliebe die Reihe bis zum Ablauf der
        # Frist auf einem alten Anker stehen - und weil ihr letzter Tag mit dem
        # Index mitwaechst, wuerde die Frist nie ablaufen. Der Direktabruf wird
        # in diesem Fall uebersprungen (er ist bei diesen Tickern nachweislich
        # leer), die Rekonstruktion laeuft dafuer bei jedem Lauf neu.
        if db.get_ohlc_quelle_letzter_punkt(conn, asset.symbol, "EUR") == QUELLE_REKONSTRUIERT:
            _rekonstruiere_hedge_reihe(conn, asset)
            return
        letztes = db.get_last_ohlc_date(conn, asset.symbol, "EUR")
        if letztes is not None:
            alter = (datetime.now(timezone.utc).date()
                     - datetime.fromisoformat(str(letztes)).date()).days
            if alter <= _HEDGE_HISTORY_STALE_THRESHOLD_TAGE:
                return
        punkte = get_full_ohlc_history(asset.yfinance_symbol, asset.symbol, "EUR")
        if punkte:
            db.upsert_ohlc_points(conn, punkte)
            logger.info("Hedge-OHLC fuer %s (%s): %d Punkte nachgeladen",
                        asset.symbol, asset.yfinance_symbol, len(punkte))
        else:
            _rekonstruiere_hedge_reihe(conn, asset)
    except Exception:
        logger.exception("Hedge-OHLC-Nachladen fuer %s fehlgeschlagen - "
                         "Signal laeuft ohne Historie weiter", asset.symbol)


def generate_signal(
    asset, watchlist, conn, llm_client, coingecko_client, *,
    bereits_vorgeschlagen_effektiv_usd: float = 0.0, zai_client=None,
) -> Signal:
    """`asset.symbol` muss in SYMBOL_ZU_HEBEL_FAKTOR stehen. `watchlist` muss die
    VOLLSTAENDIGE Watchlist sein (fuer compute_current_regime() UND fuer die
    Portfolio-Exposure-Berechnung ueber alle Assetklassen hinweg - anders als
    bei Aktien/Rohstoff wird hier bewusst NICHT auf eine Assetklassen-Teilmenge
    gefiltert, das Hedge-Instrument sichert das GESAMTE Portfolio ab).

    `bereits_vorgeschlagen_effektiv_usd` (keyword-only, 2026-07-22, siehe
    _compute_portfolio_exposure()-Docstring) - optional, Standard 0.0."""
    if not ist_hedge_instrument(asset):
        raise ValueError(f"generate_signal() (agent/hedge) erwartet ein bekanntes Hedge-Symbol, bekam {asset.symbol!r}")

    _ensure_ohlc_backfilled(conn, asset)

    # RM-BITPANDA AUCH FUER HEDGE (2026-08-07). Die Regel existiert seit dem
    # 16.07. in risk_gate.py::pre_check() und ist assetklassen-neutral - aber
    # Hedge nutzt ein eigenes Gate (_post_check_hedge) und hat sie deshalb nie
    # bekommen. Als einzige der sechs Pipelines.
    #
    # Heute kein akuter Fehler: DBPK und 3QSS SIND bei Bitpanda gelistet, sonst
    # koennten sie nicht im Bestand sein. Aber ein kuenftiges Hedge-Instrument,
    # das dort nicht handelbar ist, wuerde lautlos empfohlen - genau die Sorte
    # Luecke, die der Rollout-Check (pruefe_fakten_rollout.py) sichtbar machen
    # soll. Fail-soft wie ueberall: unbekannt ist kein Ausschlussgrund (P-10).
    _bitpanda_gelistet = None
    try:
        from api.bitpanda import get_listed_non_crypto_assets
        from api.bitpanda import is_listed as _bitpanda_is_listed

        _bitpanda_gelistet = _bitpanda_is_listed(
            asset.symbol, get_listed_non_crypto_assets(), name=asset.name)
        if not _bitpanda_gelistet and db.get_bitpanda_gelistet_override(conn, asset.symbol):
            _bitpanda_gelistet = True
    except Exception as exc:
        logger.info("Bitpanda-Listing-Abruf fuer %s fehlgeschlagen: %s", asset.symbol, exc)
    if _bitpanda_gelistet is False:
        logger.warning("%s ist nicht bei Bitpanda gelistet - Hedge-Signal wird als "
                       "HALTEN gefuehrt (RM-Bitpanda)", asset.symbol)
        signal = _fixed_signal(
            asset.symbol, "HALTEN", gate_passed=False,
            gate_reason=(f"{asset.symbol} ist nicht bei Bitpanda gelistet - auf der "
                         "Handelsbörse des Nutzers aktuell nicht kaufbar"))
        db.insert_signal(conn, signal)
        return signal

    latest_prices = db.get_latest_prices(conn)
    price_snap = latest_prices.get(asset.symbol)

    if price_snap is None or is_price_stale(price_snap.fetched_at):
        signal = _fixed_signal(asset.symbol, "HALTEN", gate_passed=False, gate_reason="Preis veraltet oder nicht vorhanden")
        db.insert_signal(conn, signal)
        return signal
    if price_snap.price_usd is None:
        signal = _fixed_signal(
            asset.symbol, "HALTEN", gate_passed=False,
            gate_reason="USD-Preis nicht verfuegbar (EUR/USD-Kurs fehlte beim letzten Preisabruf)",
        )
        db.insert_signal(conn, signal)
        return signal

    config_dict = config.load_config()
    regime_result = compute_current_regime(conn, coingecko_client, watchlist, None, config_dict)

    portfolio_exposure, verbleibendes_budget_usd = _compute_portfolio_exposure(
        asset, watchlist, conn, latest_prices, config_dict, bereits_vorgeschlagen_effektiv_usd,
    )

    eurcv_snap = latest_prices.get("EURCV")
    eur_usd_fx_rate = (
        eurcv_snap.price_usd / eurcv_snap.price_eur
        if eurcv_snap and eurcv_snap.price_usd and eurcv_snap.price_eur
        else None
    )

    holdings = {h.symbol: h for h in db.get_all_holdings(conn)}
    price_age_minutes = None
    fetched = datetime.fromisoformat(price_snap.fetched_at)
    if fetched.tzinfo is None:
        fetched = fetched.replace(tzinfo=timezone.utc)
    price_age_minutes = (datetime.now(timezone.utc) - fetched).total_seconds() / 60

    historischer_makro_vergleich = get_cached_makro_analog_fact(conn)
    letztes_signal = db.get_latest_signal(conn, asset.symbol)
    # Eigener Pool (2026-07-18, Multi-Asset-Vollstaendigkeitspruefung): Hedge-
    # Signale sind qualitativ anders (Absicherung statt Gewinnerwartung) als
    # Krypto/Aktien - eine geliehene fremde Trefferquote waere irrefuehrend.
    _hedge_symbole = set(SYMBOL_ZU_HEBEL_FAKTOR.keys())
    historische_erfolgsquote = compute_win_rate_fact(conn, "spot", erlaubte_symbole=_hedge_symbole)
    these_abgleich = kategorie_thesen.build_these_abgleich_fact(conn, asset)

    facts = build_facts(
        asset, price_snap, holdings.get(asset.symbol), SYMBOL_ZU_HEBEL_FAKTOR[asset.symbol],
        SYMBOL_ZU_REFERENZ_INDEX[asset.symbol], portfolio_exposure, regime_result, price_age_minutes,
        historischer_makro_vergleich=historischer_makro_vergleich,
        historische_erfolgsquote=historische_erfolgsquote,
        letztes_signal=letztes_signal,
        these_abgleich=these_abgleich,
    )

    try:
        parsed = call_llm_for_signal(llm_client, facts)
    except AnalystResponseInvalid as exc:
        logger.warning("LLM-Antwort fuer %s ungueltig: %s", asset.symbol, exc)
        signal = _fixed_signal(asset.symbol, "HALTEN", gate_passed=True, gate_reason=f"Agent-Antwort ungültig: {exc}", facts=facts)
        db.insert_signal(conn, signal)
        return signal

    raw_response = parsed.pop("_raw_response", None)
    corrected = _post_check_hedge(parsed, verbleibendes_budget_usd, eur_usd_fx_rate, config_dict)
    fazit_konsistenz_hinweis = corrected.pop("_fazit_konsistenz_hinweis", None)
    budget_gedeckelt = corrected.pop("_budget_gedeckelt", False)
    zonen_hinweis = corrected.pop("_zonen_hinweis", None)
    if zonen_hinweis:
        logger.warning("Hedge-Zonen fuer %s verworfen: %s", asset.symbol, zonen_hinweis)
    # RISIKOFAKTOREN FUER DIE ABSICHERUNG (2026-08-07, W2). Bis hierher lieferte
    # diese Pipeline gar keine - die E-Mail schrieb "Keine strukturierten
    # Risikofaktoren verfuegbar", was wie ein Datenfehler aussah und keiner war.
    # Eigene Funktion statt compute_risikofaktoren(), weil dort saemtliche
    # Vorzeichen fuer eine Long-Kaufidee stehen.
    try:
        risikofaktoren = compute_risikofaktoren_hedge(
            action=corrected.get("action"),
            portfolio_exposure=portfolio_exposure,
            regime_result=regime_result,
            bull_wahrscheinlichkeit_pct=(
                (corrected.get("forecast") or {}).get("bull") or {}).get("probability_pct"),
            hebel_faktor=SYMBOL_ZU_HEBEL_FAKTOR.get(asset.symbol),
            budget_gedeckelt=budget_gedeckelt,
            zonen_hinweis=zonen_hinweis,
        )
    except Exception:
        logger.exception("Hedge-Risikofaktoren fuer %s fehlgeschlagen - Signal laeuft ohne",
                         asset.symbol)
        risikofaktoren = None
    eigene_einschaetzung = corrected.get("eigene_einschaetzung") or {}

    long_reasoning = corrected.get("long_reasoning", {})
    position_size = corrected.get("position_size", {})
    entry = corrected.get("entry", {})
    stop_loss = corrected.get("stop_loss", {})
    take_profit = corrected.get("take_profit", {})
    halte_kriterium = corrected.get("halte_kriterium", {})
    top_gruende_by_rang = {g.get("rang"): g for g in corrected.get("top_gruende", [])}
    forecast = corrected.get("forecast", {})

    top_grund_fields = {}
    for rang in range(1, 6):
        eintrag = top_gruende_by_rang.get(rang, {})
        top_grund_fields[f"top_grund_{rang}_kategorie"] = eintrag.get("kategorie")
        top_grund_fields[f"top_grund_{rang}_text"] = eintrag.get("text")

    log_eur_abweichungen(asset.symbol, {
        "position_size": (position_size.get("eur"), eur_aus_usd(position_size.get("usd"), eur_usd_fx_rate)),
        "entry_von": (entry.get("eur_von"), eur_aus_usd(entry.get("usd_von"), eur_usd_fx_rate)),
        "entry_bis": (entry.get("eur_bis"), eur_aus_usd(entry.get("usd_bis"), eur_usd_fx_rate)),
        "stop_loss_von": (stop_loss.get("eur_von"), eur_aus_usd(stop_loss.get("usd_von"), eur_usd_fx_rate)),
        "stop_loss_bis": (stop_loss.get("eur_bis"), eur_aus_usd(stop_loss.get("usd_bis"), eur_usd_fx_rate)),
        "take_profit_von": (take_profit.get("eur_von"), eur_aus_usd(take_profit.get("usd_von"), eur_usd_fx_rate)),
        "take_profit_bis": (take_profit.get("eur_bis"), eur_aus_usd(take_profit.get("usd_bis"), eur_usd_fx_rate)),
        "halte_kriterium_ziel_preis": (
            halte_kriterium.get("ziel_preis_eur"), eur_aus_usd(halte_kriterium.get("ziel_preis_usd"), eur_usd_fx_rate),
        ),
    })

    signal = Signal(
        symbol=asset.symbol,
        created_at=_now(),
        action=corrected["action"],
        gate_passed=True,
        gate_reason=None,
        risk_veto=False,
        risk_veto_reason=None,
        facts_json=json.dumps(facts, ensure_ascii=False),
        pipeline_version=PIPELINE_VERSION,
        risikofaktoren_json=(
            json.dumps([f.__dict__ for f in risikofaktoren], ensure_ascii=False)
            if risikofaktoren else None),
        confidence_pct=corrected.get("confidence_pct"),
        short_reasoning=corrected.get("short_reasoning"),
        long_reasoning_technisch=long_reasoning.get("technisch"),
        long_reasoning_fundamental=long_reasoning.get("fundamental"),
        long_reasoning_makro=long_reasoning.get("makro"),
        position_size_usd=position_size.get("usd"),
        position_size_eur=eur_aus_usd(position_size.get("usd"), eur_usd_fx_rate),
        position_size_note=position_size.get("note"),
        entry_usd_von=entry.get("usd_von"),
        entry_usd_bis=entry.get("usd_bis"),
        entry_eur_von=eur_aus_usd(entry.get("usd_von"), eur_usd_fx_rate),
        entry_eur_bis=eur_aus_usd(entry.get("usd_bis"), eur_usd_fx_rate),
        stop_loss_usd_von=stop_loss.get("usd_von"),
        stop_loss_usd_bis=stop_loss.get("usd_bis"),
        stop_loss_eur_von=eur_aus_usd(stop_loss.get("usd_von"), eur_usd_fx_rate),
        stop_loss_eur_bis=eur_aus_usd(stop_loss.get("usd_bis"), eur_usd_fx_rate),
        take_profit_usd_von=take_profit.get("usd_von"),
        take_profit_usd_bis=take_profit.get("usd_bis"),
        take_profit_eur_von=eur_aus_usd(take_profit.get("usd_von"), eur_usd_fx_rate),
        take_profit_eur_bis=eur_aus_usd(take_profit.get("usd_bis"), eur_usd_fx_rate),
        halte_kriterium_bucket=halte_kriterium.get("bucket"),
        halte_kriterium_ziel_preis_usd=halte_kriterium.get("ziel_preis_usd"),
        halte_kriterium_ziel_preis_eur=eur_aus_usd(halte_kriterium.get("ziel_preis_usd"), eur_usd_fx_rate),
        halte_kriterium_ziel_datum=halte_kriterium.get("ziel_datum"),
        halte_kriterium_bedingung_text=halte_kriterium.get("bedingung_text"),
        halte_kriterium_reasoning=halte_kriterium.get("reasoning"),
        key_risks_text="\n".join(corrected.get("key_risks", [])),
        regime=regime_result.regime,
        regime_source=regime_result.source,
        forecast_bull_text=forecast.get("bull", {}).get("scenario"),
        forecast_bull_prob_pct=forecast.get("bull", {}).get("probability_pct"),
        forecast_base_text=forecast.get("base", {}).get("scenario"),
        forecast_base_prob_pct=forecast.get("base", {}).get("probability_pct"),
        forecast_bear_text=forecast.get("bear", {}).get("scenario"),
        forecast_bear_prob_pct=forecast.get("bear", {}).get("probability_pct"),
        gegenargument=corrected.get("gegenargument"),
        fazit_folgen=eigene_einschaetzung.get("folgen"),
        fazit_kurzfazit=eigene_einschaetzung.get("kurzfazit"),
        fazit_konsistenz_hinweis=fazit_konsistenz_hinweis,
        groq_raw_response=raw_response,
        groq_model=llm_model_label(llm_client),
        **top_grund_fields,
    )
    new_id = db.insert_signal(conn, signal)
    signal.id = new_id

    # Z.ai-Gegenpruefung (Ausweitung auf Hedge, siehe agent/krypto/
    # gegenpruefung.py Modul-Docstring "Vollstaendige Vereinheitlichung") -
    # rein beobachtend, laeuft asynchron NACH dem Insert. KEIN RSI/Konfluenz-
    # Fakt (Hedge betreibt bewusst GAR KEINE Einzeltitel-Technikanalyse, siehe
    # Modul-Docstring oben) - baue_fakten()/baue_objektive_fakten() lassen den
    # technische_konfluenz-Eintrag dann einfach weg (gesamt==0-Guard dort).
    # ist_hedge_invertiert=True IMMER hier (diese Pipeline verarbeitet
    # ausschliesslich Hedge-Instrumente) - siehe richtung_aus_action()-
    # Docstring fuer die Begruendung der Invertierung (KAUFEN = Hedge
    # aufbauen = baerische GESAMTMARKT-Erwartung, nicht bullisch auf das
    # Hedge-Instrument selbst).
    if zai_client is not None:
        zai_fakten = baue_zai_fakten(
            symbol=asset.symbol,
            action=corrected.get("action"),
            confidence_pct=corrected.get("confidence_pct"),
            rsi=None,
            trend_label=None,
            regime=regime_result.regime,
            funding_rate_stunde=None,
            confluence_bullish=0,
            confluence_bearish=0,
            confluence_neutral=0,
            optionsmarkt_skew=None,
        )
        zai_objektive_fakten = baue_zai_objektive_fakten(
            symbol=asset.symbol,
            rsi=None,
            trend_label=None,
            regime=regime_result.regime,
            funding_rate_stunde=None,
            confluence_bullish=0,
            confluence_bearish=0,
            confluence_neutral=0,
            optionsmarkt_skew=None,
        )
        primaer_richtung_erwartet = richtung_aus_action(
            corrected.get("action"), ist_hedge_invertiert=True,
        )
        threading.Thread(
            target=fuehre_beide_calls_im_hintergrund,
            args=(
                new_id, zai_fakten, corrected.get("short_reasoning"),
                zai_objektive_fakten, primaer_richtung_erwartet, zai_client,
                db.update_signal_zai_gegenpruefung,
            ),
            daemon=True,
        ).start()

    return signal
