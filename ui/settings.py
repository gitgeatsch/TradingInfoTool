"""Lokale UI-Einstellungen (Dark Mode, Nutzer-Idee 2026-07-09). Bewusst NICHT
in Basisinfos/config.yaml (die Datei ist handgepflegt/versioniert, siehe deren
Kopfkommentar) - eine reine GERAETE-LOKALE UI-Praeferenz gehoert nicht dort hin.
Stattdessen eine kleine, nicht versionierte JSON-Datei neben der DB (gleiches
Verzeichnis-Muster wie database/db.py::DB_PATH).

Nachtrag 2026-07-28 (siehe Regelwerksmanual-Nachtrag "Nur-Long-Deckel"):
`email_empfehlungen_nur_bitpanda`/`hebel_richtung_modus` waren urspruenglich
hier, sind aber nach Basisinfos/config.yaml migriert worden - beide steuern
tatsaechliches Trading-/Versand-Verhalten auf der 24/7-Notebook-Instanz, nicht
bloss eine kosmetische GUI-Praeferenz wie Dark Mode. Der Nachteil (kein
sofortiges Wirken mehr, sondern erst nach Commit+Push+Pull) wurde bewusst in
Kauf genommen, weil eine per-Geraet abweichende `data/settings.json` (git-
ignoriert) sonst unbemerkt zu inkonsistentem Verhalten zwischen Desktop und
Notebook fuehren kann - siehe echter NEAR/TAO-SHORT-Vorfall trotz aktivem
"Nur Long"-Schalter. Siehe config.py::set_hebel_richtung_modus()/
set_email_nur_bitpanda_gelistet() fuer die neuen Schreibfunktionen."""
from __future__ import annotations

import json
from pathlib import Path

SETTINGS_PATH = Path(__file__).resolve().parent.parent / "data" / "settings.json"

_DEFAULTS = {
    "dark_mode": False,
}


def load_settings() -> dict:
    if not SETTINGS_PATH.exists():
        return dict(_DEFAULTS)
    try:
        with open(SETTINGS_PATH, encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        # P-10: eine kaputte/fehlende Settings-Datei blockiert den Start nicht,
        # faellt einfach auf Standardwerte zurueck.
        return dict(_DEFAULTS)
    return {**_DEFAULTS, **data}


def save_settings(settings: dict) -> None:
    SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=2)
