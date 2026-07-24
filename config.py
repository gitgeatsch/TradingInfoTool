"""Laedt Basisinfos/config.yaml (Watchlist etc.) sowie optional .env fuer den Rest der App.

.env-Loading ist bewusst minimal (nur COINGECKO_API_KEY, siehe P-9/P-10-Kontext) - kein
ANTHROPIC_API_KEY/GITHUB_TOKEN-Gebrauch hier, das bleibt Phase 3 vorbehalten (P-8:
lokale Autonomie, Claude nur optional)."""
from __future__ import annotations

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


def get_watchlist() -> list[WatchlistAsset]:
    config = load_config()
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
        for entry in config["watchlist"]
    ]


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
) -> None:
    """Fügt einen neuen Eintrag ans Ende des bestehenden `watchlist:`-Blocks in
    Basisinfos/config.yaml an - reine TEXT-Einfügung (keine vollständige YAML-
    Neuserialisierung mit `yaml.dump()`), damit Kommentare/Formatierung im Rest der
    Datei byte-für-byte unangetastet bleiben (die Datei ist explizit handgepflegt,
    "BEARBEITEN IN NOTEPAD++"). Legt IMMER vorher ein Backup an
    (.claude/backups/config.yaml.<Zeitstempel>.bak), validiert die neue Datei per
    `yaml.safe_load()` und stellt bei Fehlschlag automatisch das Backup wieder her
    (Fail-Loud, P-10) - kein stiller Teilerfolg. Nutzer-Wunsch (2026-07-09), ersetzt
    den reinen Copy-Paste-YAML-Weg aus Marktscan Stufe B/C/D.

    `assetklasse`/`yfinance_symbol` sind fuer Multi-Asset-Tracking (Aktien/ETF/
    Rohstoffe, Nutzer-Idee 2026-07-09) ergaenzt - Default bleibt "krypto" ohne
    Zusatzzeilen, damit bestehende Aufrufer (UI-Watchlist-Button, Marktscan)
    unveraendert funktionieren und der geschriebene Block fuer Krypto-Eintraege
    exakt wie bisher aussieht."""
    if any(existing.symbol == symbol for existing in get_watchlist()):
        raise WatchlistWriteError(f"{symbol} ist bereits in der Watchlist - keine Änderung vorgenommen")

    # Bewusst read_bytes()/write_bytes() statt read_text()/write_text(): Letzteres
    # uebersetzt beim Schreiben unter Windows JEDES "\n" in "\r\n" (Python-Standard-
    # verhalten bei newline=None), was die komplette Datei von LF auf CRLF umgestellt
    # haette - genau das "byte-fuer-byte unangetastet"-Versprechen oben gebrochen
    # haette. Zeilenende-Stil wird stattdessen aus der Originaldatei erkannt und fuer
    # die neuen Zeilen exakt uebernommen (gefunden + gefixt 2026-07-09).
    original_bytes = CONFIG_PATH.read_bytes()
    newline_style = "\r\n" if b"\r\n" in original_bytes else "\n"
    original_text = original_bytes.decode("utf-8")
    lines = original_text.splitlines(keepends=True)
    insert_at = _find_watchlist_insert_point(lines)

    entry_lines = [
        f"  - symbol: {symbol}{newline_style}",
        f"    name: {name}{newline_style}",
        f"    rolle: {rolle}{newline_style}",
        f"    beobachtungsstatus: {beobachtungsstatus}{newline_style}",
    ]
    if coingecko_id is not None:
        entry_lines.append(f"    coingecko_id: {coingecko_id}{newline_style}")
    if assetklasse != "krypto":
        entry_lines.append(f"    assetklasse: {assetklasse}{newline_style}")
    if yfinance_symbol is not None:
        entry_lines.append(f"    yfinance_symbol: {yfinance_symbol}{newline_style}")
    if ist_cash_aequivalent:
        entry_lines.append(f"    ist_cash_aequivalent: true{newline_style}")
    if hauptgruppe is not None:
        entry_lines.append(f"    hauptgruppe: {hauptgruppe}{newline_style}")
    if unterkategorie is not None:
        entry_lines.append(f"    unterkategorie: {unterkategorie}{newline_style}")
    entry_block = "".join(entry_lines)
    new_text = "".join(lines[:insert_at] + [entry_block] + lines[insert_at:])

    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup_path = BACKUP_DIR / f"config.yaml.{timestamp}.bak"
    shutil.copy2(CONFIG_PATH, backup_path)

    CONFIG_PATH.write_bytes(new_text.encode("utf-8"))

    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            reparsed = yaml.safe_load(f)
        if symbol not in {e["symbol"] for e in reparsed["watchlist"]}:
            raise WatchlistWriteError("Validierung fehlgeschlagen: neuer Eintrag nicht im geparsten Ergebnis")
    except Exception as exc:
        shutil.copy2(backup_path, CONFIG_PATH)
        raise WatchlistWriteError(f"Schreiben fehlgeschlagen, Backup wiederhergestellt: {exc}") from exc

    global _config_cache
    _config_cache = None


def _update_watchlist_field(symbol: str, field_name: str, new_value: str) -> bool:
    """Aktualisiert EIN Feld eines bestehenden Watchlist-Eintrags per reiner
    Text-Ersetzung INNERHALB des betroffenen Eintrags-Blocks (identisches
    Backup+Validierungs-Muster wie `add_watchlist_entry()`). Interner Helfer
    fuer `update_watchlist_rolle()`/`update_watchlist_beobachtungsstatus()` -
    beide manuell vom Nutzer ausgeloest (GUI-Bearbeiten-Dialog), NIE
    automatisch aus einem Sync-Vorgang heraus (Klassifikations-Redesign
    2026-07-16, siehe Memory project_asset_klassifikation_redesign - genau
    diese fehlende Trennung zwischen "manuell" und "automatisch geschrieben"
    war der Kern der Drift-Problematik beim frueheren `status`-Feld).

    Gibt `False` zurück (kein Schreibvorgang, kein Backup) wenn der Eintrag
    nicht existiert, das Feld dort nicht vorkommt, ODER bereits den
    Zielwert hat - nur ein echter Wertwechsel schreibt tatsächlich."""
    original_bytes = CONFIG_PATH.read_bytes()
    newline_style = "\r\n" if b"\r\n" in original_bytes else "\n"
    original_text = original_bytes.decode("utf-8")
    lines = original_text.splitlines(keepends=True)

    entry_start = next(
        (i for i, line in enumerate(lines) if line.strip() == f"- symbol: {symbol}"), None,
    )
    if entry_start is None:
        return False

    entry_end = len(lines)
    for i in range(entry_start + 1, len(lines)):
        if lines[i].lstrip().startswith("- symbol:") or not lines[i].startswith(" "):
            entry_end = i
            break

    field_line_idx = next(
        (i for i in range(entry_start, entry_end) if lines[i].strip().startswith(f"{field_name}:")), None,
    )
    if field_line_idx is None:
        return False

    current_value = lines[field_line_idx].split(":", 1)[1].strip()
    if current_value == new_value:
        return False

    indent = lines[field_line_idx][: len(lines[field_line_idx]) - len(lines[field_line_idx].lstrip())]
    lines[field_line_idx] = f"{indent}{field_name}: {new_value}{newline_style}"
    new_text = "".join(lines)

    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup_path = BACKUP_DIR / f"config.yaml.{timestamp}.bak"
    shutil.copy2(CONFIG_PATH, backup_path)

    CONFIG_PATH.write_bytes(new_text.encode("utf-8"))

    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            reparsed = yaml.safe_load(f)
        matching = next((e for e in reparsed["watchlist"] if e["symbol"] == symbol), None)
        if matching is None or matching.get(field_name) != new_value:
            raise WatchlistWriteError(f"Validierung fehlgeschlagen: {field_name} nicht wie erwartet gesetzt")
    except Exception as exc:
        shutil.copy2(backup_path, CONFIG_PATH)
        raise WatchlistWriteError(f"Schreiben fehlgeschlagen, Backup wiederhergestellt: {exc}") from exc

    global _config_cache
    _config_cache = None
    return True


def update_watchlist_coingecko_id(symbol: str, new_coingecko_id: str) -> bool:
    """Setzt/ergaenzt `coingecko_id` eines bestehenden Watchlist-Eintrags -
    manuell vom Nutzer ausgeloest (GUI-Bearbeiten-Dialog, 2026-07-19,
    Watchlist-Tab-Konsistenzpruefung: automatisch aus einer Hebel-Position
    ergaenzte Symbole bekommen bewusst KEINE coingecko_id, siehe importer/
    bitpanda_margin_positions.py::auto_add_unknown_hebel_symbols() -
    Nachtragen war bisher trotzdem gar nicht moeglich, da AssetEditDialog
    dieses Feld nicht anbot UND `_update_watchlist_field()` nur bereits
    VORHANDENE Feldzeilen aktualisieren kann, keine neuen einfuegen kann
    (add_watchlist_entry() LAESST die Zeile komplett weg, wenn
    coingecko_id=None uebergeben wurde).

    Eigene Implementierung statt Erweiterung von `_update_watchlist_field()`
    (die bleibt unveraendert fuer ihre beiden bestehenden, bereits
    verifizierten Aufrufer) - fuegt die Zeile direkt nach `beobachtungsstatus:`
    ein, falls sie noch fehlt (identische Position wie in
    `add_watchlist_entry()`s Feldreihenfolge), sonst wird die vorhandene
    Zeile aktualisiert. Gleiches Backup+Validierungs+Rollback-Muster wie
    `add_watchlist_entry()`/`_update_watchlist_field()`."""
    original_bytes = CONFIG_PATH.read_bytes()
    newline_style = "\r\n" if b"\r\n" in original_bytes else "\n"
    original_text = original_bytes.decode("utf-8")
    lines = original_text.splitlines(keepends=True)

    entry_start = next(
        (i for i, line in enumerate(lines) if line.strip() == f"- symbol: {symbol}"), None,
    )
    if entry_start is None:
        return False

    entry_end = len(lines)
    for i in range(entry_start + 1, len(lines)):
        if lines[i].lstrip().startswith("- symbol:") or not lines[i].startswith(" "):
            entry_end = i
            break

    field_line_idx = next(
        (i for i in range(entry_start, entry_end) if lines[i].strip().startswith("coingecko_id:")), None,
    )

    if field_line_idx is not None:
        current_value = lines[field_line_idx].split(":", 1)[1].strip()
        if current_value == new_coingecko_id:
            return False
        indent = lines[field_line_idx][: len(lines[field_line_idx]) - len(lines[field_line_idx].lstrip())]
        lines[field_line_idx] = f"{indent}coingecko_id: {new_coingecko_id}{newline_style}"
    else:
        beobachtungsstatus_idx = next(
            (i for i in range(entry_start, entry_end) if lines[i].strip().startswith("beobachtungsstatus:")), None,
        )
        if beobachtungsstatus_idx is None:
            return False
        indent = lines[beobachtungsstatus_idx][
            : len(lines[beobachtungsstatus_idx]) - len(lines[beobachtungsstatus_idx].lstrip())
        ]
        new_line = f"{indent}coingecko_id: {new_coingecko_id}{newline_style}"
        lines.insert(beobachtungsstatus_idx + 1, new_line)

    new_text = "".join(lines)

    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup_path = BACKUP_DIR / f"config.yaml.{timestamp}.bak"
    shutil.copy2(CONFIG_PATH, backup_path)

    CONFIG_PATH.write_bytes(new_text.encode("utf-8"))

    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            reparsed = yaml.safe_load(f)
        matching = next((e for e in reparsed["watchlist"] if e["symbol"] == symbol), None)
        if matching is None or matching.get("coingecko_id") != new_coingecko_id:
            raise WatchlistWriteError("Validierung fehlgeschlagen: coingecko_id nicht wie erwartet gesetzt")
    except Exception as exc:
        shutil.copy2(backup_path, CONFIG_PATH)
        raise WatchlistWriteError(f"Schreiben fehlgeschlagen, Backup wiederhergestellt: {exc}") from exc

    global _config_cache
    _config_cache = None
    return True


def _upsert_field_at_block_end(lines: list[str], entry_start: int, entry_end: int, field_name: str, new_value: str, newline_style: str) -> tuple[list[str], bool]:
    """Interner Helfer fuer `update_watchlist_kategorie()`: setzt eine Feldzeile
    INNERHALB eines bereits abgegrenzten Eintrags-Blocks - aktualisiert eine
    vorhandene Zeile in-place, oder haengt eine neue ans Blockende an (bewahrt
    damit die Reihenfolge bereits vorhandener optionaler Felder wie coingecko_id/
    assetklasse/yfinance_symbol/ist_cash_aequivalent, siehe `add_watchlist_entry()`).
    Gibt (aktualisierte Zeilenliste, ob sich etwas geaendert hat) zurueck - der
    Aufrufer muss `entry_end` bei mehreren Aufrufen hintereinander selbst
    nachfuehren (jede Einfuegung verschiebt nachfolgende Indizes um 1)."""
    field_line_idx = next(
        (i for i in range(entry_start, entry_end) if lines[i].strip().startswith(f"{field_name}:")), None,
    )
    if field_line_idx is not None:
        current_value = lines[field_line_idx].split(":", 1)[1].strip()
        if current_value == new_value:
            return lines, False
        indent = lines[field_line_idx][: len(lines[field_line_idx]) - len(lines[field_line_idx].lstrip())]
        lines[field_line_idx] = f"{indent}{field_name}: {new_value}{newline_style}"
        return lines, True
    last_field_idx = entry_end - 1
    indent = lines[last_field_idx][: len(lines[last_field_idx]) - len(lines[last_field_idx].lstrip())]
    new_line = f"{indent}{field_name}: {new_value}{newline_style}"
    lines.insert(entry_end, new_line)
    return lines, True


def update_watchlist_kategorie(symbol: str, hauptgruppe: str, unterkategorie: str) -> bool:
    """Setzt/ergaenzt `hauptgruppe`+`unterkategorie` eines bestehenden Watchlist-
    Eintrags ATOMAR (beide Felder oder keins) - 2026-07-19, ersetzt das anfaenglich
    gebaute Freitext-Feld `schwerpunkt` NOCH AM SELBEN TAG (siehe WatchlistAsset-
    Docstring: Freitext war fuer automatische Prozesse/Kategorie-Gruppierung nicht
    zuverlaessig genug). Validiert beide IDs GEGEN Basisinfos/kategorien.yaml
    (`get_kategorien()`) - eine unbekannte ID wirft `WatchlistWriteError`, bevor
    irgendetwas geschrieben wird (P-10, kein stiller Datenmuell in config.yaml).
    Manuell vom Nutzer ausgeloest (GUI-Bearbeiten-Dialog). Einfuegeposition ist
    bewusst das ENDE des Eintrags-Blocks (siehe `_upsert_field_at_block_end()`)."""
    kategorien = get_kategorien()
    hauptgruppe_obj = next((hg for hg in kategorien["hauptgruppen"] if hg["id"] == hauptgruppe), None)
    if hauptgruppe_obj is None:
        raise WatchlistWriteError(f"Unbekannte Hauptgruppe {hauptgruppe!r} - siehe Basisinfos/kategorien.yaml")
    if not any(uk["id"] == unterkategorie for uk in hauptgruppe_obj["unterkategorien"]):
        raise WatchlistWriteError(
            f"Unbekannte Unterkategorie {unterkategorie!r} fuer Hauptgruppe {hauptgruppe!r} - "
            "siehe Basisinfos/kategorien.yaml"
        )

    original_bytes = CONFIG_PATH.read_bytes()
    newline_style = "\r\n" if b"\r\n" in original_bytes else "\n"
    original_text = original_bytes.decode("utf-8")
    lines = original_text.splitlines(keepends=True)

    entry_start = next(
        (i for i, line in enumerate(lines) if line.strip() == f"- symbol: {symbol}"), None,
    )
    if entry_start is None:
        return False

    entry_end = len(lines)
    for i in range(entry_start + 1, len(lines)):
        if lines[i].lstrip().startswith("- symbol:") or not lines[i].startswith(" "):
            entry_end = i
            break

    lines, changed_hg = _upsert_field_at_block_end(lines, entry_start, entry_end, "hauptgruppe", hauptgruppe, newline_style)

    # Blockende NEU bestimmen (nicht rechnerisch fortschreiben) - eine Einfuegung
    # durch den ersten Upsert verschiebt alle nachfolgenden Zeilenindizes, ein
    # unveraendertes Feld (In-Place-Update) tut das nicht. Neu-Suchen ist robuster
    # als die beiden Faelle einzeln zu unterscheiden.
    entry_end_nach_hg = len(lines)
    for i in range(entry_start + 1, len(lines)):
        if lines[i].lstrip().startswith("- symbol:") or not lines[i].startswith(" "):
            entry_end_nach_hg = i
            break
    lines, changed_uk = _upsert_field_at_block_end(lines, entry_start, entry_end_nach_hg, "unterkategorie", unterkategorie, newline_style)

    if not changed_hg and not changed_uk:
        return False

    new_text = "".join(lines)

    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup_path = BACKUP_DIR / f"config.yaml.{timestamp}.bak"
    shutil.copy2(CONFIG_PATH, backup_path)

    CONFIG_PATH.write_bytes(new_text.encode("utf-8"))

    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            reparsed = yaml.safe_load(f)
        matching = next((e for e in reparsed["watchlist"] if e["symbol"] == symbol), None)
        if (
            matching is None
            or matching.get("hauptgruppe") != hauptgruppe
            or matching.get("unterkategorie") != unterkategorie
        ):
            raise WatchlistWriteError("Validierung fehlgeschlagen: hauptgruppe/unterkategorie nicht wie erwartet gesetzt")
    except Exception as exc:
        shutil.copy2(backup_path, CONFIG_PATH)
        raise WatchlistWriteError(f"Schreiben fehlgeschlagen, Backup wiederhergestellt: {exc}") from exc

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
