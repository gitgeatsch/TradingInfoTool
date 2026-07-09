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
    symbol: str
    name: str
    typ: str        # core | taktisch | stablecoin
    status: str     # aktiv | watchlist
    coingecko_id: str


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
            typ=entry["typ"],
            status=entry["status"],
            coingecko_id=entry["coingecko_id"],
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


def add_watchlist_entry(symbol: str, name: str, typ: str, status: str, coingecko_id: str) -> None:
    """Fügt einen neuen Eintrag ans Ende des bestehenden `watchlist:`-Blocks in
    Basisinfos/config.yaml an - reine TEXT-Einfügung (keine vollständige YAML-
    Neuserialisierung mit `yaml.dump()`), damit Kommentare/Formatierung im Rest der
    Datei byte-für-byte unangetastet bleiben (die Datei ist explizit handgepflegt,
    "BEARBEITEN IN NOTEPAD++"). Legt IMMER vorher ein Backup an
    (.claude/backups/config.yaml.<Zeitstempel>.bak), validiert die neue Datei per
    `yaml.safe_load()` und stellt bei Fehlschlag automatisch das Backup wieder her
    (Fail-Loud, P-10) - kein stiller Teilerfolg. Nutzer-Wunsch (2026-07-09), ersetzt
    den reinen Copy-Paste-YAML-Weg aus Marktscan Stufe B/C/D."""
    if any(existing.symbol == symbol for existing in get_watchlist()):
        raise WatchlistWriteError(f"{symbol} ist bereits in der Watchlist - keine Änderung vorgenommen")

    original_text = CONFIG_PATH.read_text(encoding="utf-8")
    lines = original_text.splitlines(keepends=True)
    insert_at = _find_watchlist_insert_point(lines)

    entry_block = (
        f"  - symbol: {symbol}\n"
        f"    name: {name}\n"
        f"    typ: {typ}\n"
        f"    status: {status}\n"
        f"    coingecko_id: {coingecko_id}\n"
    )
    new_text = "".join(lines[:insert_at] + [entry_block] + lines[insert_at:])

    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup_path = BACKUP_DIR / f"config.yaml.{timestamp}.bak"
    shutil.copy2(CONFIG_PATH, backup_path)

    CONFIG_PATH.write_text(new_text, encoding="utf-8")

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
