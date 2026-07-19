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
ENV_PATH = Path(__file__).resolve().parent / ".env"
BACKUP_DIR = Path(__file__).resolve().parent / ".claude" / "backups"

_config_cache: dict | None = None


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


def load_config() -> dict:
    global _config_cache
    if _config_cache is None:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            _config_cache = yaml.safe_load(f)
    return _config_cache


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
