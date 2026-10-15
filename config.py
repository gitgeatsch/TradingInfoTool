"""Laedt Basisinfos/config.yaml (Watchlist etc.) sowie optional .env fuer den Rest der App.

.env-Loading ist bewusst minimal (nur COINGECKO_API_KEY, siehe P-9/P-10-Kontext) - kein
ANTHROPIC_API_KEY/GITHUB_TOKEN-Gebrauch hier, das bleibt Phase 3 vorbehalten (P-8:
lokale Autonomie, Claude nur optional)."""
from __future__ import annotations

import json
import logging
import re
import shutil
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import yaml
from dotenv import load_dotenv

CONFIG_PATH = Path(__file__).resolve().parent / "Basisinfos" / "config.yaml"
KATEGORIEN_PATH = Path(__file__).resolve().parent / "Basisinfos" / "kategorien.yaml"
ENV_PATH = Path(__file__).resolve().parent / ".env"
BACKUP_DIR = Path(__file__).resolve().parent / ".claude" / "backups"

_config_cache: dict | None = None
_kategorien_cache: dict | None = None


def load_env() -> None:
    """Laedt .env falls vorhanden (kein Fehler falls die Datei fehlt - Key ist optional)."""
    load_dotenv(ENV_PATH)


@dataclass
class WatchlistAsset:
    """Klassifikations-Redesign (2026-07-16, siehe Memory
    project_asset_klassifikation_redesign): drei unabhaengige Achsen statt der
    frueheren zwei Felder typ/status.

    - `rolle` (core | taktisch): rein strategisch, manuell, UNABHAENGIG vom
      aktuellen Bestand (ein core-Asset kann z.B. noch nie gehalten worden
      sein - bewusster Erstkauf-Kandidat). Fuer `ist_cash_aequivalent=True`
      ohne funktionale Bedeutung (siehe dort), traegt trotzdem "taktisch" als
      harmlosen Fuellwert (Schema-Vollstaendigkeit).
    - "gehalten" gibt es bewusst NICHT mehr als gespeichertes Feld - wird
      ueberall live aus database.db.get_all_holdings() (Spot) bzw.
      get_open_hebel_positions() (Hebel) abgeleitet, kann daher nie
      veralten/driften (loeste die fruehere Status-Auf-/Abstufungs-
      Problematik strukturell auf, siehe Memory).
    - `beobachtungsstatus` (beobachtung | ausgemustert): manuell, nur
      relevant/wirksam solange NICHT gehalten (Spot oder Hebel). Kein
      Ausschluss aus der Signal-Rotation, sondern nur eine Prioritaets-/
      Cooldown-Stufe (niedrigste Prioritaet, nie komplett null - "darf nicht
      sterben"). Wird NIE automatisch geschrieben (weder hoch- noch
      runtergestuft) - bewusst rein manuell, um genau die Drift zu vermeiden,
      die das alte `status`-Feld anfaellig gemacht hat.
    - `ist_cash_aequivalent`: ersetzt den frueheren Sonderfall `typ ==
      "stablecoin"` - eine eigene Achse statt eines dritten Werts auf der
      rolle-Skala (ein Stablecoin ist nie "core" oder "taktisch", sondern
      grundsaetzlich kein Risiko-Asset)."""
    symbol: str
    name: str
    rolle: str               # core | taktisch
    beobachtungsstatus: str  # beobachtung | ausgemustert
    # coingecko_id ist nur fuer assetklasse=krypto gesetzt; optional statt required,
    # damit Aktien/ETF/Rohstoffe (kein CoinGecko-Eintrag) denselben Datentyp nutzen
    # koennen (Multi-Asset-Tracking, Nutzer-Idee 2026-07-09, siehe Spezifikation Kap. 11
    # "Zielarchitektur fuer Multi-Asset-Erweiterbarkeit").
    coingecko_id: str | None = None
    # Default "krypto" erhaelt Rueckwaertskompatibilitaet fuer alle bestehenden
    # config.yaml-Eintraege, ohne dass dort ueberall assetklasse: krypto ergaenzt
    # werden muss.
    assetklasse: str = "krypto"  # krypto | aktien | etf | rohstoffe
    # Nur fuer assetklasse != krypto gesetzt - Ticker-Format fuer api/yfinance_client.py
    # (z.B. "VST" fuer US-Aktien, "VVMX.DE" fuer Xetra, ISIN+".SG" fuer duenn gehandelte
    # WisdomTree-ETNs ohne Xetra-Kurzcode bei Yahoo Finance).
    yfinance_symbol: str | None = None
    ist_cash_aequivalent: bool = False
    # Strukturierte inhaltliche/thematische Einordnung (2026-07-19, Nutzer-Wunsch
    # nach Diversifikations-Ueberblick + Marktscan-Schwerpunkten). ERSETZT das
    # anfaenglich gebaute Freitext-Feld `schwerpunkt` NOCH AM SELBEN TAG - Freitext
    # kann fuer automatische Prozesse (Kategorie-Gruppierung, Marktscan-Bias) nicht
    # zuverlaessig verglichen werden. `hauptgruppe`/`unterkategorie` sind IDs aus
    # Basisinfos/kategorien.yaml (siehe get_kategorien()), validiert beim Schreiben
    # (siehe update_watchlist_kategorie()). Optional, KEIN Pflichtfeld.
    hauptgruppe: str | None = None
    unterkategorie: str | None = None


def load_config() -> dict:
    global _config_cache
    if _config_cache is None:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            _config_cache = yaml.safe_load(f)
    return _config_cache


def get_kategorien() -> dict:
    """Laedt Basisinfos/kategorien.yaml (2026-07-19, Kategorie-Taxonomie-
    Infrastruktur, siehe WatchlistAsset-Docstring) - `{"hauptgruppen": [{"id":...,
    "name":..., "unterkategorien": [{"id":..., "name":..., "bitpanda_symbole":
    [...]}]}]}`. Gecacht analog zu `load_config()`, eigener Cache (unabhaengige
    Datei, unabhaengiger Aenderungsrhythmus)."""
    global _kategorien_cache
    if _kategorien_cache is None:
        with open(KATEGORIEN_PATH, "r", encoding="utf-8") as f:
            _kategorien_cache = yaml.safe_load(f)
    return _kategorien_cache


def find_kategorie_fuer_bitpanda_symbol(bitpanda_symbol: str) -> tuple[str, str] | None:
    """Liefert `(hauptgruppe_id, unterkategorie_id)` fuer ein Bitpanda-Symbol
    (z.B. aus `agent/aktien/screener.py::scan_etf_candidates()`), oder `None`
    falls das Symbol in keiner Unterkategorie hinterlegt ist (z.B. ein neues,
    noch nicht in kategorien.yaml erfasstes Bitpanda-Produkt - kein Fehler,
    P-8, der Aufrufer zeigt den Kandidaten dann einfach ohne Kategorie an)."""
    kategorien = get_kategorien()
    for hauptgruppe in kategorien["hauptgruppen"]:
        for unterkategorie in hauptgruppe["unterkategorien"]:
            if bitpanda_symbol in unterkategorie.get("bitpanda_symbole", []):
                return hauptgruppe["id"], unterkategorie["id"]
    return None


def get_hauptgruppe_name(hauptgruppe_id: str | None) -> str | None:
    """Nur der Hauptgruppen-Name (ohne Unterkategorie) - fuer die
    Diversifikations-Uebersicht im Portfolio-Tab (2026-07-19), die bewusst
    auf Hauptgruppen-Ebene gruppiert statt auf die feinere Unterkategorie-
    Ebene (72 Unterkategorien waeren als Tabelle unuebersichtlich). `None`
    bei fehlender/unbekannter ID (P-10, kein Rateergebnis)."""
    if not hauptgruppe_id:
        return None
    kategorien = get_kategorien()
    hauptgruppe = next((hg for hg in kategorien["hauptgruppen"] if hg["id"] == hauptgruppe_id), None)
    return hauptgruppe["name"] if hauptgruppe is not None else None


def get_kategorie_name(hauptgruppe_id: str | None, unterkategorie_id: str | None) -> str | None:
    """Menschenlesbarer Anzeigetext `"Hauptgruppe / Unterkategorie"` fuer die
    GUI (Watchlist-Tab-Spalte, Diversifikations-Tabelle) - `None`, wenn eine der
    beiden IDs fehlt oder nicht in kategorien.yaml existiert (z.B. bei einem
    veralteten/geloeschten Kategorie-Eintrag, P-10: lieber leer als falsch
    anzeigen)."""
    if not hauptgruppe_id or not unterkategorie_id:
        return None
    kategorien = get_kategorien()
    hauptgruppe = next((hg for hg in kategorien["hauptgruppen"] if hg["id"] == hauptgruppe_id), None)
    if hauptgruppe is None:
        return None
    unterkategorie = next(
        (uk for uk in hauptgruppe["unterkategorien"] if uk["id"] == unterkategorie_id), None,
    )
    if unterkategorie is None:
        return None
    return f"{hauptgruppe['name']} / {unterkategorie['name']}"


# Pruef-Mechanismus-Mapping fuer Kategorie-Thesen (2026-07-19, Release 2,
# siehe Basisinfos/Kategorie_Basisinformationen_Release2.md Abschnitt 7) -
# welcher objektive Datencheck fuer these_abgleich() bei welcher Hauptgruppe/
# Unterkategorie anwendbar ist, plus ein Zeithorizont-basierter Vorschlag
# fuer das review_am-Feld (Transparenz-Prinzip: der Vorschlag kommt IMMER
# mit einer Begruendung, siehe get_review_am_vorschlag()). Manche Mechanismen
# gelten nur fuer eine bestimmte Unterkategorie, nicht die ganze Hauptgruppe
# (z.B. Zinskurve nur fuer "Finanzen", nicht "ganz Aktien-Sektoren") - Schluessel
# ist deshalb wahlweise "hauptgruppe" ODER "hauptgruppe:unterkategorie", die
# spezifischere Variante hat Vorrang (siehe get_pruef_mechanismus()).
#
# "mechanismen" (2026-07-24, #333 Multi-Indikator-Design - vorher "mechanismus",
# ein einzelner String): eine Kategorie kann jetzt MEHRERE Mechanismen gleich-
# zeitig haben (z.B. Edelmetalle: M2-Liquiditaet UND COT-Positionierung Gold/
# Silber) - agent/kategorie_thesen.py::compute_these_abgleich() ruft alle auf
# und kombiniert sie ueber eine Einigkeitsregel (_kombiniere_abgleiche()):
# nur wenn ALLE verfuegbaren Mechanismen uebereinstimmen, gilt das Ergebnis als
# "gestuetzt"/"widerspricht", sonst "neutral" - ein einzelnes Signal darf keine
# gemischte Lage als eindeutig ausgeben.
PRUEF_MECHANISMUS_MAPPING: dict[str, dict] = {
    "edelmetalle": {
        "mechanismen": ["m2_liquiditaet", "cot_positionierung"],
        "review_tage_vorschlag": 28,
        "review_begruendung": "COT-Berichte (Gold/Silber) erscheinen woechentlich und sind damit der schnellere der beiden Mechanismen - M2 bleibt als langsamere Bestaetigung im Begruendungstext sichtbar.",
    },
    "industriemetalle": {
        "mechanismen": ["cot_positionierung"],
        "review_tage_vorschlag": 28,
        "review_begruendung": "CFTC-COT-Berichte erscheinen woechentlich, die Positionierung kann sich vergleichsweise schnell verschieben.",
    },
    "energie": {
        "mechanismen": ["cot_positionierung"],
        "review_tage_vorschlag": 28,
        "review_begruendung": "CFTC-COT- und EIA-Daten erscheinen woechentlich.",
    },
    # 2026-07-24, #333 Punkt 9: EIA-Erdgas-5-Jahres-Saisonvergleich betrifft nur
    # Erdgas, nicht Rohoel (anders als der Hauptgruppen-weite COT-Check oben, der
    # beide Rohstoffe poolt) - deshalb eigener, spezifischerer Eintrag statt
    # Erweiterung von "energie".
    "energie:erdgas": {
        "mechanismen": ["cot_positionierung", "eia_erdgas"],
        "review_tage_vorschlag": 28,
        "review_begruendung": "CFTC-COT- und EIA-Lagerbestandsdaten erscheinen beide woechentlich.",
    },
    "anleihen_geldmarkt": {
        "mechanismen": ["m2_liquiditaet"],
        "review_tage_vorschlag": 90,
        "review_begruendung": "Zinsentscheide sind selten (Fed tagt nur alle paar Wochen), ein kuerzeres Intervall bringt keinen neuen Erkenntnisgewinn.",
    },
    "aktien_sektoren:finanzen": {
        "mechanismen": ["zinskurve"],
        "review_tage_vorschlag": 75,
        "review_begruendung": "Die Zinskurve braucht mehrere Monate Verlauf, um aussagekraeftig zu sein.",
    },
    "aktien_regionen:emerging_markets": {
        "mechanismen": ["dollar_index", "baerenmarkt_overlay"],
        "review_tage_vorschlag": 30,
        "review_begruendung": "Baerenmarkt-/VIX-Signal (schneller der beiden, siehe 'aktien_regionen') ist jetzt der bindende Takt - Dollar-Index bleibt als langsamere Bestaetigung im Begruendungstext sichtbar.",
    },
    # 2026-07-24, #333 Punkt 14: gleicher Mechanismus wie Absicherung, aber
    # umgekehrte Polaritaet (Risk-off ist ein allgemeiner Gegenwind fuer
    # Aktien, kein Grund fuer eine Versicherung - siehe agent/kategorie_
    # thesen.py::_abgleich_baerenmarkt_overlay() Docstring). Hauptgruppen-
    # weiter Fallback fuer alle Regionen OHNE eigenen spezifischeren Eintrag
    # (Global/Europa/Nordamerika/USA/Asien-Pazifik/Einzellaender) - Emerging
    # Markets hat oben bereits einen spezifischeren Eintrag, der Vorrang hat.
    "aktien_regionen": {
        "mechanismen": ["baerenmarkt_overlay"],
        "review_tage_vorschlag": 30,
        "review_begruendung": "VIX/Baerenmarkt-Status kann sich innerhalb weniger Wochen deutlich verschieben.",
    },
    "absicherung": {
        "mechanismen": ["baerenmarkt_overlay"],
        "review_tage_vorschlag": None,
        "review_begruendung": "Absicherung wird situativ (de-)aktiviert, kein festes Wiedervorlage-Intervall sinnvoll.",
    },
    # 2026-07-24, #333 Punkt 11: Bellwether-Sentiment (manuell kuratierte
    # Ticker-Koerbe, siehe agent/kategorie_thesen.py::_BELLWETHER_TICKER und
    # Kategorie_Basisinformationen_Release2.md Abschnitt 12). review_tage an
    # der langsamsten der drei Quellen orientiert (FINRA meldet nur zweimal
    # monatlich, Finnhub/SEC EDGAR sind schneller).
    "technologie_ki:halbleiter": {
        "mechanismen": ["bellwether_sentiment"],
        "review_tage_vorschlag": 45,
        "review_begruendung": "FINRA-Short-Interest-Meldungen (langsamste der drei Bellwether-Quellen) erscheinen nur zweimal monatlich.",
    },
    "technologie_ki:ki": {
        "mechanismen": ["bellwether_sentiment"],
        "review_tage_vorschlag": 45,
        "review_begruendung": "FINRA-Short-Interest-Meldungen (langsamste der drei Bellwether-Quellen) erscheinen nur zweimal monatlich.",
    },
    "technologie_ki:cybersicherheit": {
        "mechanismen": ["bellwether_sentiment"],
        "review_tage_vorschlag": 45,
        "review_begruendung": "FINRA-Short-Interest-Meldungen (langsamste der drei Bellwether-Quellen) erscheinen nur zweimal monatlich.",
    },
    "technologie_ki:biotech": {
        "mechanismen": ["bellwether_sentiment"],
        "review_tage_vorschlag": 45,
        "review_begruendung": "FINRA-Short-Interest-Meldungen (langsamste der drei Bellwether-Quellen) erscheinen nur zweimal monatlich.",
    },
    "aktien_sektoren:gesundheit": {
        "mechanismen": ["bellwether_sentiment"],
        "review_tage_vorschlag": 45,
        "review_begruendung": "FINRA-Short-Interest-Meldungen (langsamste der drei Bellwether-Quellen) erscheinen nur zweimal monatlich.",
    },
    "aktien_sektoren:konsum_zyklisch": {
        "mechanismen": ["bellwether_sentiment"],
        "review_tage_vorschlag": 45,
        "review_begruendung": "FINRA-Short-Interest-Meldungen (langsamste der drei Bellwether-Quellen) erscheinen nur zweimal monatlich.",
    },
    "aktien_sektoren:konsum_basis": {
        "mechanismen": ["bellwether_sentiment"],
        "review_tage_vorschlag": 45,
        "review_begruendung": "FINRA-Short-Interest-Meldungen (langsamste der drei Bellwether-Quellen) erscheinen nur zweimal monatlich.",
    },
    "aktien_sektoren:industrie": {
        "mechanismen": ["bellwether_sentiment"],
        "review_tage_vorschlag": 45,
        "review_begruendung": "FINRA-Short-Interest-Meldungen (langsamste der drei Bellwether-Quellen) erscheinen nur zweimal monatlich.",
    },
    "aktien_sektoren:kommunikation": {
        "mechanismen": ["bellwether_sentiment"],
        "review_tage_vorschlag": 45,
        "review_begruendung": "FINRA-Short-Interest-Meldungen (langsamste der drei Bellwether-Quellen) erscheinen nur zweimal monatlich.",
    },
    "aktien_sektoren:grundstoffe": {
        "mechanismen": ["bellwether_sentiment"],
        "review_tage_vorschlag": 45,
        "review_begruendung": "FINRA-Short-Interest-Meldungen (langsamste der drei Bellwether-Quellen) erscheinen nur zweimal monatlich.",
    },
}


def get_pruef_mechanismus(hauptgruppe: str, unterkategorie: str | None) -> dict | None:
    """Liefert die anwendbaren Pruef-Mechanismen fuer these_abgleich() als Dict
    mit Schluessel "mechanismen" (Liste, meist ein Element, Edelmetalle hat
    zwei), oder `None` wenn fuer diese Hauptgruppe/Unterkategorie kein
    etablierter automatischer Check existiert (z.B. Technologie & KI, Sonstige
    - dort bleibt es bei reiner Hervorhebung ohne these_abgleich-Text, P-10
    ehrlich statt vorgetaeuscht). Unterkategorie-spezifischer Eintrag hat
    Vorrang vor der Hauptgruppe."""
    if unterkategorie:
        spezifisch = PRUEF_MECHANISMUS_MAPPING.get(f"{hauptgruppe}:{unterkategorie}")
        if spezifisch is not None:
            return spezifisch
    return PRUEF_MECHANISMUS_MAPPING.get(hauptgruppe)


def bitpanda_bestand_quelle() -> str:
    """Welcher Bestandsabgleich laeuft (16.09.2026, Schritt 61 Stufe 1.2, E12).

    `bitpanda.bestand_quelle` in config.yaml: fehlt oder `neu` -> neue
    Schnittstelle (`importer/bitpanda_bestand.py`); `alt` -> der bisherige
    Abgleich als Rueckweg OHNE Code-Aenderung. Jeder andere Wert gilt als `neu`
    und steht als Warnung im Log - ein Tippfehler darf nicht still den alten,
    fehlerhaften Weg aktivieren."""
    wert = str(((load_config() or {}).get("bitpanda") or {}).get("bestand_quelle") or "neu").strip().lower()
    if wert not in ("neu", "alt"):
        import logging as _lg
        _lg.getLogger(__name__).warning(
            "config bitpanda.bestand_quelle = %r ist unbekannt - es gilt 'neu'", wert)
        return "neu"
    return wert


# ══ P18b (14.10.2026, Plan_Asset_Lebenszyklus G-Z8): Grundliste (config.yaml, versioniert) + Ergaenzung (Datenbank, am Geraet) ══════
ERGAENZUNG_TABELLE = "watchlist_ergaenzung"
WATCHLIST_FELDER = ("name", "rolle", "beobachtungsstatus", "coingecko_id", "assetklasse", "yfinance_symbol", "ist_cash_aequivalent",
                    "hauptgruppe", "unterkategorie")
_PFLICHT = ("name", "rolle", "beobachtungsstatus")


def _db_pfad():
    from database import db as _db              # spaet importiert: database.db importiert config nur innerhalb von init_db

    return _db.DB_PATH


def watchlist_ergaenzung() -> list[dict]:
    """Die Zeilen der Ergaenzung, aelteste zuerst - NUR LESEND (``mode=ro``). Fehlt die Datei oder die Tabelle (Desktop, Pruefskripte,
    App noch nie gestartet), ist die Ergaenzung leer; beim Lesen wird NIE etwas angelegt (Standard-DB-Regel)."""
    import sqlite3

    p = Path(_db_pfad())
    if not p.exists():
        return []
    try:
        c = sqlite3.connect("file:%s?mode=ro" % str(p).replace("\\", "/"), uri=True, timeout=5)
        try:
            zeilen = c.execute("SELECT symbol, eintrag, entfernt, herkunft, angelegt_am, geaendert_am FROM %s "
                               "ORDER BY angelegt_am, symbol" % ERGAENZUNG_TABELLE).fetchall()
        finally:
            c.close()
    except sqlite3.Error:
        return []
    aus = []
    for s, e, ent, h, an, ge in zeilen:
        try:
            felder = json.loads(e) if e else {}
        except ValueError:
            felder = {}
        aus.append({"symbol": s, "felder": felder, "entfernt": bool(ent), "herkunft": h, "angelegt_am": an, "geaendert_am": ge})
    return aus


def watchlist_eintraege() -> list[dict]:
    """Grundliste + Ergaenzung als Eintraege (dict wie in config.yaml) mit ``_quelle`` (grundliste | ergaenzung | grundliste+ergaenzung)
    und ``_herkunft``. Reihenfolge: Grundliste wie in der Datei, neue Symbole der Ergaenzung dahinter (in der Reihenfolge ihrer Aufnahme)."""
    aus = [dict(e, _quelle="grundliste", _herkunft=None) for e in load_config()["watchlist"]]
    pos = {e["symbol"]: i for i, e in enumerate(aus)}
    weg = set()
    for z in watchlist_ergaenzung():
        s = z["symbol"]
        if z["entfernt"]:
            weg.add(s)
            continue
        weg.discard(s)
        if s in pos:
            aus[pos[s]].update({k: v for k, v in z["felder"].items() if k in WATCHLIST_FELDER})
            aus[pos[s]]["_quelle"], aus[pos[s]]["_herkunft"] = "grundliste+ergaenzung", z["herkunft"]
        elif all(z["felder"].get(k) for k in _PFLICHT):
            aus.append(dict({k: v for k, v in z["felder"].items() if k in WATCHLIST_FELDER}, symbol=s, _quelle="ergaenzung",
                            _herkunft=z["herkunft"]))
            pos[s] = len(aus) - 1
        else:
            logging.getLogger(__name__).warning("Watchlist-Ergaenzung %s ohne Pflichtfelder %s - uebergangen", s, _PFLICHT)
    return [e for e in aus if e["symbol"] not in weg]


def watchlist_herkunft() -> dict:
    """{Symbol: (quelle, herkunft)} - fuer Diagnose (P21 Punkt 17) und Teilexport."""
    return {e["symbol"]: (e["_quelle"], e["_herkunft"]) for e in watchlist_eintraege()}


def get_watchlist() -> list[WatchlistAsset]:
    """Die Watchlist = Grundliste aus config.yaml + Ergaenzung aus der Datenbank (P18b). Die Grundliste ist zwischengespeichert
    (``load_config``, geleert von jedem Schreibweg); die Ergaenzung wird bei jedem Aufruf gelesen (0,7 ms, gemessen 14.10.)."""
    return [
        WatchlistAsset(
            symbol=entry["symbol"],
            name=entry["name"],
            rolle=entry["rolle"],
            beobachtungsstatus=entry["beobachtungsstatus"],
            coingecko_id=entry.get("coingecko_id"),
            assetklasse=entry.get("assetklasse", "krypto"),
            yfinance_symbol=entry.get("yfinance_symbol"),
            ist_cash_aequivalent=entry.get("ist_cash_aequivalent", False),
            hauptgruppe=entry.get("hauptgruppe"),
            unterkategorie=entry.get("unterkategorie"),
        )
        for entry in watchlist_eintraege()
    ]


def _ergaenzung_schreiben(symbol: str, felder: dict, herkunft: str, entfernt: bool = False) -> None:
    """Setzt Felder eines Symbols in der Ergaenzung (vorhandene Felder bleiben, neue ueberschreiben) - der EINZIGE Schreibweg der
    Watchlist seit P18b. Legt die Tabelle an, falls sie fehlt (Schreiben ist hier die Absicht; am NB legt sie init_db beim Start an)."""
    import sqlite3

    c = sqlite3.connect(str(_db_pfad()), timeout=10)
    try:
        c.execute("CREATE TABLE IF NOT EXISTS %s (symbol TEXT PRIMARY KEY, eintrag TEXT, entfernt INTEGER NOT NULL DEFAULT 0, herkunft TEXT, "
                  "angelegt_am TEXT NOT NULL, geaendert_am TEXT NOT NULL)" % ERGAENZUNG_TABELLE)
        r = c.execute("SELECT eintrag FROM %s WHERE symbol=?" % ERGAENZUNG_TABELLE, (symbol,)).fetchone()
        alt = json.loads(r[0]) if r and r[0] else {}
        neu = dict(alt, **felder)
        jetzt = datetime.now(timezone.utc).isoformat(timespec="seconds")
        c.execute("INSERT INTO %s (symbol, eintrag, entfernt, herkunft, angelegt_am, geaendert_am) VALUES (?,?,?,?,?,?) "
                  "ON CONFLICT(symbol) DO UPDATE SET eintrag=excluded.eintrag, entfernt=excluded.entfernt, herkunft=excluded.herkunft, "
                  "geaendert_am=excluded.geaendert_am" % ERGAENZUNG_TABELLE,
                  (symbol, json.dumps(neu, ensure_ascii=False), 1 if entfernt else 0, herkunft, jetzt, jetzt))
        c.commit()
    finally:
        c.close()


def _eintrag(symbol: str) -> dict | None:
    return next((e for e in watchlist_eintraege() if e["symbol"] == symbol), None)


class WatchlistWriteError(Exception):
    pass


def _find_watchlist_insert_point(lines: list[str]) -> int:
    """Findet den Zeilenindex direkt NACH dem letzten watchlist:-Eintrag (vor
    trailenden Leerzeilen/dem naechsten Top-Level-Abschnitt)."""
    in_watchlist = False
    boundary = None
    for i, line in enumerate(lines):
        if line.strip() == "watchlist:" and not line.startswith(" "):
            in_watchlist = True
            continue
        if in_watchlist and not (line.startswith(" ") or line.strip() == ""):
            boundary = i
            break
    if boundary is None:
        raise WatchlistWriteError("watchlist:-Block-Ende nicht gefunden - Abbruch, keine Änderung")
    insert_at = boundary
    while insert_at > 0 and lines[insert_at - 1].strip() == "":
        insert_at -= 1
    return insert_at


def add_watchlist_entry(
    symbol: str,
    name: str,
    rolle: str,
    beobachtungsstatus: str,
    coingecko_id: str | None = None,
    assetklasse: str = "krypto",
    yfinance_symbol: str | None = None,
    ist_cash_aequivalent: bool = False,
    hauptgruppe: str | None = None,
    unterkategorie: str | None = None,
    herkunft: str = "gui",
) -> None:
    """Nimmt ein neues Asset in die Watchlist auf - seit P18b (14.10.2026) in die ERGAENZUNG in der Datenbank, NICHT mehr in die
    versionierte config.yaml (Anlass: XDC und CT standen ab 08.10. nur in der config.yaml am NB, ein Pull mit geaenderter Datei waere
    gescheitert - K-WL-1, Plan_Asset_Lebenszyklus G-Z8). Aufrufer unveraendert: GUI *Asset hinzufuegen*, Marktscan, Screener, Hebel-
    Importer (automatisch). ``herkunft`` haelt fest, welcher Weg geschrieben hat. Die Uebernahme in die Grundliste macht ein Commit.

    Wie bisher: ein Symbol, das schon in der Watchlist steht, ist ein Fehler (keine Aenderung). Fail-Loud (P-10): nach dem Schreiben
    wird zurueckgelesen; fehlt der Eintrag, wird die neue Zeile entfernt und ``WatchlistWriteError`` geworfen."""
    if any(existing.symbol == symbol for existing in get_watchlist()):
        raise WatchlistWriteError(f"{symbol} ist bereits in der Watchlist - keine Änderung vorgenommen")
    felder = {"name": name, "rolle": rolle, "beobachtungsstatus": beobachtungsstatus}
    if coingecko_id is not None:
        felder["coingecko_id"] = coingecko_id
    if assetklasse != "krypto":
        felder["assetklasse"] = assetklasse
    if yfinance_symbol is not None:
        felder["yfinance_symbol"] = yfinance_symbol
    if ist_cash_aequivalent:
        felder["ist_cash_aequivalent"] = True
    if hauptgruppe is not None:
        felder["hauptgruppe"] = hauptgruppe
    if unterkategorie is not None:
        felder["unterkategorie"] = unterkategorie
    try:
        _ergaenzung_schreiben(symbol, felder, herkunft)
        if not any(e.symbol == symbol for e in get_watchlist()):
            raise WatchlistWriteError("Validierung fehlgeschlagen: neuer Eintrag nicht in der Watchlist")
    except Exception as exc:
        _ergaenzung_zeile_loeschen_wenn_neu(symbol, felder)
        if isinstance(exc, WatchlistWriteError):
            raise
        raise WatchlistWriteError(f"Schreiben fehlgeschlagen: {exc}") from exc
    global _config_cache
    _config_cache = None


def _ergaenzung_zeile_loeschen_wenn_neu(symbol: str, felder: dict) -> None:
    """Rueckweg fuer add_watchlist_entry: nur eine Zeile, die GENAU diese Felder traegt (gerade angelegt), wird entfernt."""
    import sqlite3

    try:
        c = sqlite3.connect(str(_db_pfad()), timeout=10)
        try:
            c.execute("DELETE FROM %s WHERE symbol=? AND eintrag=?" % ERGAENZUNG_TABELLE, (symbol, json.dumps(felder, ensure_ascii=False)))
            c.commit()
        finally:
            c.close()
    except sqlite3.Error:
        pass


def _update_watchlist_field(symbol: str, field_name: str, new_value: str, herkunft: str = "gui_bearbeiten") -> bool:
    """Aendert EIN Feld eines Watchlist-Eintrags - seit P18b in der ERGAENZUNG (die Grundliste in config.yaml bleibt unberuehrt).
    Interner Helfer fuer ``update_watchlist_rolle()``/``update_watchlist_beobachtungsstatus()`` - beide manuell vom Nutzer ausgeloest
    (GUI-Bearbeiten-Dialog), NIE automatisch aus einem Sync-Vorgang heraus (Klassifikations-Redesign 2026-07-16).

    Gibt ``False`` zurueck (kein Schreibvorgang), wenn der Eintrag nicht existiert, das Feld dort nicht vorkommt ODER bereits den
    Zielwert hat - nur ein echter Wertwechsel schreibt (wie vor P18b)."""
    e = _eintrag(symbol)
    if e is None or field_name not in e or e.get(field_name) == new_value:
        return False
    _ergaenzung_schreiben(symbol, {field_name: new_value}, herkunft)
    if (_eintrag(symbol) or {}).get(field_name) != new_value:
        raise WatchlistWriteError(f"Validierung fehlgeschlagen: {field_name} nicht wie erwartet gesetzt")
    global _config_cache
    _config_cache = None
    return True


def entfernen_gesperrt(symbol: str) -> str | None:
    """O51 (15.10.2026, Nutzer: *"nur fuer Assets, welche nicht im Bestand sind und aus der Beobachtung fallen sollen"*): warum ein
    Asset NICHT entfernt werden darf - oder None. Liest die Produktions-DB nur (``mode=ro``).

    ⚠️ Gesperrt bei Bestand (frei + gestakt, wie ``spot_mitnahme.kreis``) und bei offener Hebelposition: Fuehrung und Abbau (B3/B4)
    holen ihre Bestaende ueber die Watchlist - ein entferntes Asset mit Bestand fiele dort still heraus. Ist die Datenbank nicht
    lesbar, wird ebenfalls gesperrt: ohne Nachweis kein Entfernen."""
    import sqlite3

    p = Path(_db_pfad())
    if not p.exists():
        return "Datenbank nicht vorhanden - Bestand nicht prüfbar"
    try:
        c = sqlite3.connect("file:%s?mode=ro" % str(p).replace("\\", "/"), uri=True, timeout=5)
        try:
            q, st = c.execute("SELECT COALESCE(SUM(quantity), 0), COALESCE(SUM(staked_quantity), 0) FROM holdings WHERE symbol=?",
                              (symbol,)).fetchone()
            offen = c.execute("SELECT COUNT(*) FROM hebel_positions WHERE symbol=? AND geschlossen_am IS NULL", (symbol,)).fetchone()[0]
        finally:
            c.close()
    except sqlite3.Error as exc:
        return "Bestand nicht prüfbar (%s)" % exc
    if float(q or 0) + float(st or 0) > 0:
        return "im Bestand (frei %s, gestakt %s)" % (q, st)
    if offen:
        return "%d offene Hebelposition(en)" % offen
    return None


def remove_watchlist_entry(symbol: str, herkunft: str = "gui_entfernen") -> None:
    """O51: nimmt ein Asset aus der Watchlist (Grundliste UND Ergaenzung) - als Vermerk ``entfernt`` in der Ergaenzung, die
    Grundliste in config.yaml bleibt unberuehrt (P18b). Nichts wird geloescht: Signale, Kurse und Historie bleiben, und ein erneutes
    Hinzufuegen (``add_watchlist_entry``) hebt den Vermerk wieder auf. Wirft ``WatchlistWriteError`` mit dem Grund, wenn gesperrt
    (``entfernen_gesperrt``) oder das Asset nicht in der Watchlist steht."""
    if _eintrag(symbol) is None:
        raise WatchlistWriteError(f"{symbol} steht nicht in der Watchlist")
    grund = entfernen_gesperrt(symbol)
    if grund:
        raise WatchlistWriteError(f"{symbol} kann nicht entfernt werden: {grund}")
    _ergaenzung_schreiben(symbol, {}, herkunft, entfernt=True)
    if _eintrag(symbol) is not None:
        raise WatchlistWriteError(f"Validierung fehlgeschlagen: {symbol} steht weiter in der Watchlist")
    global _config_cache
    _config_cache = None


def update_watchlist_coingecko_id(symbol: str, new_coingecko_id: str, herkunft: str = "gui_bearbeiten") -> bool:
    """Setzt/ergaenzt ``coingecko_id`` eines Watchlist-Eintrags - manuell vom Nutzer ausgeloest (GUI-Bearbeiten-Dialog, 2026-07-19:
    automatisch aus einer Hebel-Position ergaenzte Symbole bekommen bewusst KEINE coingecko_id, siehe importer/bitpanda_margin_positions.py).
    Seit P18b in der ERGAENZUNG; anders als ``_update_watchlist_field`` darf das Feld vorher fehlen (wie vor P18b). ``False`` = kein
    Eintrag oder schon dieser Wert."""
    e = _eintrag(symbol)
    if e is None or e.get("coingecko_id") == new_coingecko_id:
        return False
    _ergaenzung_schreiben(symbol, {"coingecko_id": new_coingecko_id}, herkunft)
    if (_eintrag(symbol) or {}).get("coingecko_id") != new_coingecko_id:
        raise WatchlistWriteError("Validierung fehlgeschlagen: coingecko_id nicht wie erwartet gesetzt")
    global _config_cache
    _config_cache = None
    return True


def update_watchlist_kategorie(symbol: str, hauptgruppe: str, unterkategorie: str, herkunft: str = "gui_bearbeiten") -> bool:
    """Setzt/ergaenzt ``hauptgruppe`` + ``unterkategorie`` ATOMAR (beide Felder oder keins) - 2026-07-19, ersetzt das Freitext-Feld
    ``schwerpunkt``. Validiert beide IDs GEGEN Basisinfos/kategorien.yaml (``get_kategorien()``) - eine unbekannte ID wirft
    ``WatchlistWriteError``, bevor irgendetwas geschrieben wird (P-10). Seit P18b in der ERGAENZUNG. ``False`` = kein Eintrag oder
    beide Felder unveraendert."""
    kategorien = get_kategorien()
    hauptgruppe_obj = next((hg for hg in kategorien["hauptgruppen"] if hg["id"] == hauptgruppe), None)
    if hauptgruppe_obj is None:
        raise WatchlistWriteError(f"Unbekannte Hauptgruppe {hauptgruppe!r} - siehe Basisinfos/kategorien.yaml")
    if not any(uk["id"] == unterkategorie for uk in hauptgruppe_obj["unterkategorien"]):
        raise WatchlistWriteError(
            f"Unbekannte Unterkategorie {unterkategorie!r} fuer Hauptgruppe {hauptgruppe!r} - "
            "siehe Basisinfos/kategorien.yaml"
        )
    e = _eintrag(symbol)
    if e is None or (e.get("hauptgruppe") == hauptgruppe and e.get("unterkategorie") == unterkategorie):
        return False
    _ergaenzung_schreiben(symbol, {"hauptgruppe": hauptgruppe, "unterkategorie": unterkategorie}, herkunft)
    n = _eintrag(symbol) or {}
    if n.get("hauptgruppe") != hauptgruppe or n.get("unterkategorie") != unterkategorie:
        raise WatchlistWriteError("Validierung fehlgeschlagen: hauptgruppe/unterkategorie nicht wie erwartet gesetzt")
    global _config_cache
    _config_cache = None
    return True


def update_watchlist_rolle(symbol: str, new_rolle: str) -> bool:
    """Setzt `rolle` (core|taktisch) eines bestehenden Watchlist-Eintrags -
    ausschliesslich manuell ausgeloest (GUI-Bearbeiten-Dialog), nie
    automatisch."""
    return _update_watchlist_field(symbol, "rolle", new_rolle)


def update_watchlist_beobachtungsstatus(symbol: str, new_beobachtungsstatus: str) -> bool:
    """Setzt `beobachtungsstatus` (beobachtung|ausgemustert) eines bestehenden
    Watchlist-Eintrags - ausschliesslich manuell ausgeloest (GUI-Bearbeiten-
    Dialog), nie automatisch aus einem Sync-Vorgang heraus. Anders als beim
    frueheren `status`-Feld gibt es dafuer bewusst KEINEN Aufrufer in
    importer/bitpanda_sync.py - "gehalten" wird seit dem Klassifikations-
    Redesign live aus den echten Bestaenden abgeleitet, nicht mehr hier
    gespeichert."""
    return _update_watchlist_field(symbol, "beobachtungsstatus", new_beobachtungsstatus)


REGIME_MANUELLER_OVERRIDE_WERTE = ("none", "krise_extrem", "baer", "seitwaerts", "bulle", "euphorie_extrem")


def _set_top_level_skalar(field_name: str, new_value_yaml: str, block_scope: str | None = None) -> bool:
    """Gemeinsame Schreiblogik fuer `set_hebel_richtung_modus()`/`set_email_nur_
    bitpanda_gelistet()` (2026-07-28, Migration von `data/settings.json` -
    geraete-lokal+git-ignoriert - nach `config.yaml` - git-synchronisiert, siehe
    Regelwerksmanual-Nachtrag "Nur-Long-Deckel": der Kandidaten-Filter allein reicht
    nicht, aber unabhaengig davon soll der SCHALTER selbst auf beiden Geraeten
    garantiert denselben Wert haben, nicht nur zufaellig durch manuelle Disziplin).
    Identisches Backup-/Schreib-/Reparse-/Rollback-Muster wie
    `set_regime_manueller_override()`, `new_value_yaml` ist bereits YAML-serialisiert
    (z.B. "nur_long" oder "true"/"false") und wird 1:1 in die Zeile geschrieben.
    `block_scope` (optional) schraenkt die Zeilensuche auf Zeilen NACH der ersten
    Fundstelle von `f"{block_scope}:"` ein - noetig fuer `nur_bitpanda_gelistet`,
    dessen Feldname sonst nicht eindeutig genug waere, falls er je in einem anderen
    Abschnitt wiederverwendet wird."""
    original_bytes = CONFIG_PATH.read_bytes()
    newline_style = "\r\n" if b"\r\n" in original_bytes else "\n"
    original_text = original_bytes.decode("utf-8")
    lines = original_text.splitlines(keepends=True)

    start_idx = 0
    if block_scope is not None:
        scope_idx = next((i for i, line in enumerate(lines) if line.strip() == f"{block_scope}:"), None)
        if scope_idx is None:
            return False
        start_idx = scope_idx

    field_line_idx = next(
        (i for i in range(start_idx, len(lines)) if lines[i].strip().startswith(f"{field_name}:")), None,
    )
    if field_line_idx is None:
        return False

    line = lines[field_line_idx]
    indent = line[: len(line) - len(line.lstrip())]
    rest = line.split(":", 1)[1]
    if "#" in rest:
        value_part, comment_part = rest.split("#", 1)
        comment_part = "#" + comment_part.rstrip("\r\n")
    else:
        value_part, comment_part = rest, ""
    current_value = value_part.strip()
    if current_value == new_value_yaml:
        return False

    padding = " " * max(1, len(value_part) - len(value_part.strip()) - 1) if comment_part else " "
    lines[field_line_idx] = f"{indent}{field_name}: {new_value_yaml}{padding}{comment_part}{newline_style}"
    new_text = "".join(lines)

    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup_path = BACKUP_DIR / f"config.yaml.{timestamp}.bak"
    shutil.copy2(CONFIG_PATH, backup_path)

    CONFIG_PATH.write_bytes(new_text.encode("utf-8"))

    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            yaml.safe_load(f)
    except Exception as exc:
        shutil.copy2(backup_path, CONFIG_PATH)
        raise WatchlistWriteError(f"Schreiben fehlgeschlagen, Backup wiederhergestellt: {exc}") from exc

    global _config_cache
    _config_cache = None
    return True


HEBEL_RICHTUNG_MODUS_WERTE = ("beide", "nur_long")


def set_hebel_richtung_modus(new_value: str) -> bool:
    """Setzt `budget_allocator.hebel_richtung_modus` (2026-07-28, migriert aus
    `ui/settings.py`/`data/settings.json` - siehe Regelwerksmanual-Nachtrag
    "Nur-Long-Deckel"). Aufrufer: `ui/app.py::_toggle_hebel_richtung()`."""
    if new_value not in HEBEL_RICHTUNG_MODUS_WERTE:
        raise ValueError(f"Ungültiger Richtungsmodus: {new_value!r} (erlaubt: {HEBEL_RICHTUNG_MODUS_WERTE})")
    return _set_top_level_skalar("hebel_richtung_modus", new_value, block_scope="budget_allocator")


# Bitpandas `group`-Feld in Klartext (2026-08-07). Die Werte stammen aus
# api/bitpanda.py::NON_CRYPTO_ASSET_GROUPS/CRYPTO_ASSET_GROUPS - sie beantworten
# die halbe Frage "was ist das eigentlich" bereits ohne jede neue Datenquelle.
_INSTRUMENTENTYP_KLARTEXT = {
    "stock": "Einzelaktie",
    "etf": "ETF (Korb aus vielen Werten)",
    "etc": "ETC (besichertes Rohstoff-Zertifikat)",
    "metal": "physisches Edelmetall",
    "security_token": "Security Token",
    "coin": "Kryptowaehrung",
    "token": "Krypto-Token",
    "leveraged_token": "gehebelter Krypto-Token",
    "index": "Krypto-Index",
}


def asset_steckbrief(symbol: str, name: str | None = None,
                     bitpanda_group: str | None = None,
                     hauptgruppe: str | None = None,
                     unterkategorie: str | None = None,
                     bitpanda_gelistet: bool | None = None) -> str:
    """Kurzer Klartext: was ist dieses Symbol, und was bildet es ab?

    ANLASS (Nutzer 07.08.): *"falls moeglich waere es hilfreich zu wissen, wenn
    ein Symbol z.B. ABCDE vorgeschlagen wird, welches Asset und was macht das
    Asset - vor allem bei ETF relevant, da oft ueber einen Themenbereich
    verteilt."*

    KEINE NEUE DATENQUELLE NOETIG. Drei Bausteine liegen bereits vor:

      - `name`            aus dem Bitpanda-Katalog
      - `bitpanda_group`  liefert den INSTRUMENTENTYP (stock/etf/etc/metal)
      - Haupt-/Unterkategorie aus Basisinfos/kategorien.yaml

    Zusammen ergeben sie: "COPPERMINE - ETF (Korb aus vielen Werten),
    Industriemetalle / Kupfer, Thema Kupfer". Das beantwortet die Frage fuer
    die grosse Mehrheit der Faelle.

    LUECKEN SIND ERLAUBT (Nutzer-Vorgabe: "auch wenn kleine Luecken
    entstehen"). Fehlt eine Angabe, faellt sie weg statt geraten zu werden -
    ein erfundener Steckbrief waere schlechter als ein knapper.
    """
    teile: list[str] = []
    if name and name != symbol:
        teile.append(str(name))
    typ = _INSTRUMENTENTYP_KLARTEXT.get((bitpanda_group or "").lower())
    if typ:
        teile.append(typ)
    if hauptgruppe:
        gruppe_name = _kategorie_klartext(hauptgruppe, unterkategorie)
        if gruppe_name:
            teile.append(gruppe_name)
    thema = bruecken_name_fuer(hauptgruppe, unterkategorie)
    if thema:
        teile.append(f"Thema {thema}")
    if bitpanda_gelistet is False:
        teile.append("bei Bitpanda NICHT handelbar")
    return f"{symbol} - " + ", ".join(teile) if teile else symbol


def _kategorie_klartext(hauptgruppe: str, unterkategorie: str | None) -> str | None:
    """Lesbare Namen statt der internen IDs ("Industriemetalle / Kupfer")."""
    for g in get_kategorien().get("hauptgruppen") or []:
        if g.get("id") != hauptgruppe:
            continue
        hg = g.get("name") or hauptgruppe
        if not unterkategorie:
            return hg
        for u in (g.get("unterkategorien") or []):
            if u.get("id") == unterkategorie:
                return f"{hg} / {u.get('name') or unterkategorie}"
        return hg
    return None


def richtgroesse_thesen() -> tuple[int, int]:
    """Die Richtgroesse fuer gleichzeitig aktive Thesen - (min, max). (2026-08-07)

    `Kategorie_Basisinformationen_Release2.md` Abschnitt 5, Punkt 3, im
    Wortlaut: *"Richtgroesse: 3-6 gleichzeitig aktive Thesen, weich in der GUI
    angezeigt, kein Hard-Limit im Code."*

    Implementiert war bis zum 07.08. das Gegenteil: nur die Obergrenze
    existierte, und sie war ein hartes Budget - wurde sie ueberschritten,
    landeten reife Kandidaten stumm als "offen" statt als These. Die
    Untergrenze gab es gar nicht, obwohl sie derzeit die interessantere ist:
    ausserhalb der Rohstoffe traegt kaum ein Themenfeld eine These.

    Diese Funktion liefert die Zahlen; sie zu UNTERSCHREITEN oder zu
    UEBERSCHREITEN ist kein Fehler, sondern eine Lage, die angezeigt wird.
    """
    cfg = load_config().get("kategorie_vorschlaege") or {}
    minimum = int(cfg.get("richtgroesse_min_aktive_thesen", 3))
    maximum = int(cfg.get("richtgroesse_max_aktive_thesen", 6))
    return minimum, maximum


def kategorie_handelbare_assets(hauptgruppe: str | None,
                                unterkategorie: str | None = None) -> list[str]:
    """Welche handelbaren Assets stehen hinter dieser Kategorie? (2026-08-07, G-5)

    Eine These auf einem Themenfeld ohne handelbares Asset kann nichts
    ausloesen - sie erzeugt Aufmerksamkeit ohne Ziel. Geprueft werden zwei
    Quellen, weil beide vorkommen:

      1. `bitpanda_symbole` aus dem Kategorien-Katalog (per Definition
         handelbar), und
      2. die Watchlist, ueber `hauptgruppe`/`unterkategorie`.

    Quelle 2 ist nicht optional: `absicherung/aktienmarkt_short` und
    `absicherung/sektor_short` haben KEINE Katalog-Symbole - dort haengen DBPK
    und 3QSS ausschliesslich an der Watchlist. Eine Pruefung nur ueber den
    Katalog haette also ausgerechnet die beiden Hedge-Kategorien gesperrt, die
    der Nutzer aktiv haelt.

    Ohne `unterkategorie` zaehlt die ganze Hauptgruppe (eine These auf
    Hauptgruppen-Ebene erreicht alles darunter).
    """
    if not hauptgruppe:
        return []
    treffer: list[str] = []
    for g in get_kategorien().get("hauptgruppen") or []:
        if g.get("id") != hauptgruppe:
            continue
        for u in (g.get("unterkategorien") or []):
            if unterkategorie and u.get("id") != unterkategorie:
                continue
            treffer.extend(u.get("bitpanda_symbole") or [])
    for asset in get_watchlist():
        if asset.hauptgruppe != hauptgruppe:
            continue
        if unterkategorie and asset.unterkategorie != unterkategorie:
            continue
        treffer.append(asset.symbol)
    return sorted(set(treffer))


def manuelle_schwerpunkte() -> list[tuple[str, str | None]]:
    """Vom Nutzer gesetzte Themen-Schwerpunkte (2026-08-07).

    Siehe Basisinfos/config.yaml, Block `schwerpunkte`, fuer die Begruendung -
    kurz: ein Mechanismus, der Aufmerksamkeit nach Trendstaerke verteilt, wuerde
    das Gegenteil dessen tun, was antizyklisches Investieren braucht. Ein
    gesetzter Schwerpunkt behaelt seinen Platz auch dann, wenn gerade ein
    anderes Thema laeuft.

    Rueckgabe: [(hauptgruppe, unterkategorie|None), ...]
    """
    roh = (load_config().get("schwerpunkte") or {}).get("manuell") or []
    ergebnis: list[tuple[str, str | None]] = []
    for eintrag in roh:
        teile = str(eintrag).split(":", 1)
        ergebnis.append((teile[0].strip(), teile[1].strip() if len(teile) > 1 else None))
    return ergebnis


def ist_manueller_schwerpunkt(hauptgruppe: str | None,
                              unterkategorie: str | None = None) -> bool:
    """Ist diese Kategorie ein gesetzter Schwerpunkt?

    Ein Eintrag auf HAUPTGRUPPEN-Ebene deckt alle ihre Unterkategorien ab -
    "energie" schuetzt damit auch "energie:erdgas". Umgekehrt schuetzt ein
    Eintrag auf Unterkategorie-Ebene NUR diese eine.
    """
    if not hauptgruppe:
        return False
    for hg, uk in manuelle_schwerpunkte():
        if hg != hauptgruppe:
            continue
        if uk is None or uk == unterkategorie:
            return True
    return False


def setze_manuellen_schwerpunkt(hauptgruppe: str, unterkategorie: str | None,
                                aktiv: bool) -> bool:
    """Setzt oder entfernt einen Schwerpunkt in config.yaml.

    Schreibt wie die uebrigen GUI-Schalter direkt in die Datei und wirkt damit
    auf dem anderen Geraet erst nach Commit+Push und Pull - dafuer garantiert
    konsistent. In der laufenden GUI wirkt es beim naechsten Lauf, weil die
    Aufrufer bei jedem Zugriff neu lesen."""
    schluessel = f"{hauptgruppe}:{unterkategorie}" if unterkategorie else hauptgruppe
    aktuell = [f"{h}:{u}" if u else h for h, u in manuelle_schwerpunkte()]
    if aktiv and schluessel not in aktuell:
        aktuell.append(schluessel)
    elif not aktiv and schluessel in aktuell:
        aktuell.remove(schluessel)
    else:
        return True
    return _schreibe_schwerpunkte(aktuell)


def _schreibe_schwerpunkte(eintraege: list[str]) -> bool:
    """Ersetzt die `manuell:`-Liste im Block `schwerpunkte`. Bewusst
    zeilenbasiert wie die uebrigen Config-Schreiber - ein YAML-Roundtrip wuerde
    saemtliche Kommentare der Datei verlieren, und die Kommentare sind hier die
    eigentliche Dokumentation."""
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as fh:
            zeilen = fh.readlines()
    except OSError:
        return False
    start = None
    for i, z in enumerate(zeilen):
        if z.rstrip() == "schwerpunkte:":
            start = i
            break
    if start is None:
        return False
    # `manuell:`-Zeile und ihre bisherigen Listeneintraege finden
    j = start + 1
    while j < len(zeilen) and not zeilen[j].lstrip().startswith("manuell:"):
        if zeilen[j].strip() and not zeilen[j].startswith((" ", "\t", "#")):
            return False
        j += 1
    if j >= len(zeilen):
        return False
    ende = j + 1
    while ende < len(zeilen) and zeilen[ende].lstrip().startswith("- "):
        ende += 1
    neu = ["  manuell: []\n"] if not eintraege else \
          ["  manuell:\n"] + [f"    - {e}\n" for e in eintraege]
    zeilen[j:ende] = neu
    try:
        with open(CONFIG_PATH, "w", encoding="utf-8") as fh:
            fh.writelines(zeilen)
    except OSError:
        return False
    global _config_cache
    _config_cache = None
    return True


def themen_bruecken() -> list[dict]:
    """Themen, die quer zu den Hauptgruppen laufen (2026-08-07).

    Die Hauptgruppen sind nach INSTRUMENTENTYP geschnitten, ein Thema laeuft
    quer dazu: "Kupfer" betrifft das Material, die Minenbetreiber und ETFs auf
    beides. Siehe Basisinfos/kategorien.yaml, Abschnitt `themen_bruecken`, fuer
    die volle Begruendung - und dafuer, warum Luecken erlaubt sind.
    """
    return get_kategorien().get("themen_bruecken") or []


def verwandte_kategorien(hauptgruppe: str | None,
                         unterkategorie: str | None = None) -> list[tuple[str, str | None]]:
    """Welche anderen Kategorien gehoeren thematisch dazu?

    Gibt die Kategorien aller Bruecken zurueck, in denen diese Kategorie
    vorkommt - ohne sie selbst. Leere Liste, wenn keine Bruecke greift; das ist
    der Normalfall und kein Fehler.

    Eine Bruecke kann eine ganze Hauptgruppe nennen ("edelmetalle") oder eine
    einzelne Unterkategorie ("industriemetalle:kupfer"). Wird eine Hauptgruppe
    genannt, passt jede ihrer Unterkategorien.
    """
    if not hauptgruppe:
        return []
    eigen = (hauptgruppe, unterkategorie)

    def _passt(schluessel: str) -> bool:
        teile = schluessel.split(":", 1)
        if teile[0] != hauptgruppe:
            return False
        return len(teile) == 1 or teile[1] == unterkategorie

    treffer: list[tuple[str, str | None]] = []
    for bruecke in themen_bruecken():
        schluessel = bruecke.get("kategorien") or []
        if not any(_passt(s) for s in schluessel):
            continue
        for s in schluessel:
            teile = s.split(":", 1)
            kandidat = (teile[0], teile[1] if len(teile) > 1 else None)
            if kandidat != eigen and kandidat not in treffer:
                treffer.append(kandidat)
    return treffer


def bruecken_name_fuer(hauptgruppe: str | None,
                       unterkategorie: str | None = None) -> str | None:
    """Name der ersten Bruecke, in der diese Kategorie vorkommt - fuer die
    Anzeige ("Thema: Kupfer")."""
    if not hauptgruppe:
        return None
    for bruecke in themen_bruecken():
        for s in (bruecke.get("kategorien") or []):
            teile = s.split(":", 1)
            if teile[0] == hauptgruppe and (len(teile) == 1 or teile[1] == unterkategorie):
                return bruecke.get("name")
    return None


def marktsuche_nur_bitpanda_gelistet() -> bool:
    """Sollen Screener und Marktscan nur bei Bitpanda handelbare Kandidaten
    zeigen? (2026-08-07)

    Beide erfassen `bitpanda_gelistet` schon lange als Merkmal, gefiltert wurde
    danach aber nie - ein nicht handelbarer Kandidat stand gleichberechtigt in
    der Liste, obwohl die Umsetzung ueber die Bitpanda-App laeuft.

    Bewusst ein SCHALTER und kein hartes Gate: die Information "es gaebe da
    etwas, nur nicht bei deinem Broker" kann wertvoll sein. Standard true.
    """
    return bool((load_config().get("marktsuche") or {}).get("nur_bitpanda_gelistet", True))


def set_marktsuche_nur_bitpanda_gelistet(new_value: bool) -> bool:
    """Schreibt den Schalter zurueck in config.yaml - analog
    set_email_nur_bitpanda_gelistet(). Aenderung wirkt nach Commit+Push
    (Desktop) und Pull (Notebook)."""
    return _set_top_level_skalar("nur_bitpanda_gelistet", "true" if new_value else "false",
                                 block_scope="marktsuche")


def kandidat_ist_handelbar(bitpanda_gelistet: bool | None) -> bool:
    """Faellt dieser Kandidat durch den Marktsuche-Filter?

    UNBEKANNT (None) BLEIBT DRIN - dieselbe P-10-Regel wie beim Gate
    RM-Bitpanda in risk_gate.py::pre_check(): ein fehlgeschlagener Abruf ist
    kein Ausschlussgrund. Nur ein AUSDRUECKLICHES False filtert.
    """
    if not marktsuche_nur_bitpanda_gelistet():
        return True
    return bitpanda_gelistet is not False


def set_email_nur_bitpanda_gelistet(new_value: bool) -> bool:
    """Setzt `benachrichtigung.email.nur_bitpanda_gelistet` (2026-07-28, migriert aus
    `ui/settings.py`/`data/settings.json` - siehe Regelwerksmanual-Nachtrag
    "Nur-Long-Deckel"). Aufrufer: `ui/app.py::_toggle_email_nur_bitpanda()`."""
    return _set_top_level_skalar("nur_bitpanda_gelistet", "true" if new_value else "false", block_scope="email")


def set_regime_score_override(new_value: float | None) -> bool:
    """Setzt `regime.manueller_override_score` (E4, 2026-08-13).

    DERSELBE HEBEL, FEINERE AUFLOESUNG. Der Etikett-Override kennt vier
    Schubladen; der Score ist stetig und bestimmt seit dem 06.08. die
    Mindestkonfidenz ueber vier Stuetzstellen. Ihn zu setzen ist deshalb kein
    zweiter Eingriff, sondern derselbe mit mehr Aufloesung.

    NICHT BEIDE GLEICHZEITIG. Ein gesetztes Etikett UND ein gesetzter Score
    waeren zwei Wahrheiten ueber denselben Zustand - und es waere nicht
    ablesbar, welche gilt. Wer den Score setzt, muss das Etikett auf 'none'
    stellen; das wird hier geprueft und nicht stillschweigend aufgeloest.

    `None` schaltet den Override ab. Gleiches Schreib-/Rollback-Muster wie
    `set_regime_manueller_override()`."""
    if new_value is not None:
        try:
            wert = float(new_value)
        except (TypeError, ValueError):
            raise ValueError(f"Score-Override muss eine Zahl sein: {new_value!r}")
        if not 0.0 <= wert <= 1.0:
            raise ValueError(f"Score-Override liegt ausserhalb 0.00-1.00: {wert}")
        etikett = load_config().get("regime", {}).get("manueller_override", "none")
        if etikett and etikett != "none":
            raise ValueError(
                f"Es ist bereits ein Etikett-Override aktiv ('{etikett}'). Beide "
                f"gleichzeitig waeren zwei Wahrheiten - erst auf 'Kein Override' "
                f"stellen, dann den Score setzen.")
    return _setze_top_level_skalar(
        "manueller_override_score",
        "null" if new_value is None else f"{float(new_value):.2f}")


def _setze_top_level_skalar(schluessel: str, roher_wert: str) -> bool:
    """Schreibt EINEN Skalar in die config.yaml - und laesst alles andere in
    Ruhe, byte-genau.

    ZWEI FALLEN, BEIDE SELBST HINEINGETAPPT (13.08.2026):

    1. WRITE_TEXT statt WRITE_BYTES. Die Warnung steht seit dem 09.07. weiter
       oben in dieser Datei: write_text uebersetzt unter Windows jedes "
" in
       "
". Ergebnis war eine config.yaml mit 19.426 verirrten CR, ein
       unlesbarer Diff und eine Wiederherstellung aus dem letzten guten Stand.
    2. DEN KOMMENTAR NEU ZUSAMMENGEBAUT. Die erste Fassung zerlegte die Zeile
       in Wert und Kommentar und setzte sie mit festem Abstand wieder zusammen -
       damit war die Ausrichtung der ganzen Datei dahin, und jeder Schreibvorgang
       aenderte die Datei ein Stueck weiter.

    DESHALB: nur der WERT wird ersetzt. Einzug, Abstand, Kommentar und
    Zeilenende bleiben exakt, wie sie waren."""
    original_bytes = CONFIG_PATH.read_bytes()
    original_text = original_bytes.decode("utf-8")
    lines = original_text.splitlines(keepends=True)
    idx = next((i for i, line in enumerate(lines)
                if line.strip().startswith(f"{schluessel}:")), None)
    if idx is None:
        return False

    # Gruppe 1 = Einzug + Schluessel + ": ", Gruppe 2 = der Wert,
    # Gruppe 3 = alles danach (Abstand, Kommentar, Zeilenende) - unangetastet.
    treffer = re.match(rf"^(\s*{re.escape(schluessel)}:\s*)(\S+)(.*)$",
                       lines[idx], re.DOTALL)
    if treffer is None:
        return False
    neu_zeile = f"{treffer.group(1)}{roher_wert}{treffer.group(3)}"
    if neu_zeile == lines[idx]:
        return False

    lines[idx] = neu_zeile
    sicherung = CONFIG_PATH.with_suffix(CONFIG_PATH.suffix + ".bak")
    sicherung.write_bytes(original_bytes)
    try:
        CONFIG_PATH.write_bytes("".join(lines).encode("utf-8"))
        # CACHE INVALIDIEREN. `load_config()` haelt ein Modul-Global; ohne das
        # las derselbe Prozess nach dem Schreiben weiter den alten Wert - im
        # Test stand "geschrieben: True" neben "gelesen: None".
        global _config_cache
        _config_cache = None
    except Exception:
        CONFIG_PATH.write_bytes(original_bytes)
        raise
    return True


def set_regime_manueller_override(new_value: str) -> bool:
    """Setzt den TOP-LEVEL Skalar `regime.manueller_override` (RG-8, Basisinfos/
    config.yaml Zeile ~1005) - bisher ein reines "Uboot" (nur per Hand in der
    YAML-Datei editierbar), jetzt ueber ui/regime_view.py als sichtbares
    GUI-Setting bedienbar (2026-07-26, Nutzer-Wunsch). Gleiches Backup-/
    Schreib-/Reparse-/Rollback-Muster wie `_update_watchlist_field()`, aber
    fuer einen einzelnen Top-Level-Schluessel statt eines Watchlist-Eintrag-
    Blocks - `manueller_override:` kommt in der Datei nur genau einmal vor,
    daher reicht eine einfache Zeilensuche ohne Block-Grenzen.

    Ein evtl. vorhandener Inline-Kommentar (`# RG-8: none | krise_extrem | ...`)
    bleibt beim Schreiben erhalten - nur der Wert vor dem `#` wird ersetzt.

    Gibt `False` zurück (kein Schreibvorgang) wenn der Schlüssel nicht
    gefunden wird oder bereits den Zielwert hat."""
    if new_value not in REGIME_MANUELLER_OVERRIDE_WERTE:
        raise ValueError(f"Ungültiger Override-Wert: {new_value!r} (erlaubt: {REGIME_MANUELLER_OVERRIDE_WERTE})")

    original_bytes = CONFIG_PATH.read_bytes()
    newline_style = "\r\n" if b"\r\n" in original_bytes else "\n"
    original_text = original_bytes.decode("utf-8")
    lines = original_text.splitlines(keepends=True)

    field_line_idx = next(
        (i for i, line in enumerate(lines) if line.strip().startswith("manueller_override:")), None,
    )
    if field_line_idx is None:
        return False

    line = lines[field_line_idx]
    indent = line[: len(line) - len(line.lstrip())]
    rest = line.split(":", 1)[1]
    if "#" in rest:
        value_part, comment_part = rest.split("#", 1)
        comment_part = "#" + comment_part.rstrip("\r\n")
    else:
        value_part, comment_part = rest, ""
    current_value = value_part.strip()
    if current_value == new_value:
        return False

    padding = " " * max(1, len(value_part) - len(value_part.strip()) - 1) if comment_part else " "
    lines[field_line_idx] = f"{indent}manueller_override: {new_value}{padding}{comment_part}{newline_style}"
    new_text = "".join(lines)

    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup_path = BACKUP_DIR / f"config.yaml.{timestamp}.bak"
    shutil.copy2(CONFIG_PATH, backup_path)

    CONFIG_PATH.write_bytes(new_text.encode("utf-8"))

    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            reparsed = yaml.safe_load(f)
        if reparsed.get("regime", {}).get("manueller_override") != new_value:
            raise WatchlistWriteError("Validierung fehlgeschlagen: manueller_override nicht wie erwartet gesetzt")
    except Exception as exc:
        shutil.copy2(backup_path, CONFIG_PATH)
        raise WatchlistWriteError(f"Schreiben fehlgeschlagen, Backup wiederhergestellt: {exc}") from exc

    global _config_cache
    _config_cache = None
    return True
