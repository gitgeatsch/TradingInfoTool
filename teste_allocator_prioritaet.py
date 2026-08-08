"""Schritt 6 (S-4): zieht der Multi-Asset-Batch Schwerpunkt-Assets vor?

DIE LUECKE, DIE DAS SCHLIESST, steht im Gesamtkonzept als *"Signal mit Fokus:
der Allocator kennt die Thesen nicht"*. Schritt 3 hat den Schalter gebaut, aber
angeschlossen war er nirgends - ein manuell gesetzter Schwerpunkt hatte auf die
Verarbeitung UEBERHAUPT KEINE Wirkung.

WARUM GEGEN EINE NICHT LEERE LISTE GEPRUEFT WIRD: `schwerpunkte.manuell` ist
produktiv leer. Ein Test gegen den Produktivzustand wuerde durchlaufen, ohne
irgendetwas zu pruefen - die Partition waere ein No-Op. Deshalb setzt dieser
Test einen echten Schwerpunkt und stellt ihn danach wieder her.

GEWAEHLT: `industriemetalle` (VVMX, CEBS, OD7C). Die drei stehen in der
Watchlist an Position 3, 8 und 11 - eine Umsortierung ist also sichtbar. Ein
Schwerpunkt auf die vorderen Assets haette nichts bewiesen.

WAS SCHRITT 6 AUSDRUECKLICH NICHT TUT: die AUSWAHL aendern. Dieser Batch hat
keinen Stueckzahl-Deckel; es werden ohnehin alle Faelligen verarbeitet. Geprueft
wird deshalb die Reihenfolge - und dass die Menge unveraendert bleibt.
"""
import copy
import pathlib
import sys
import tempfile

SCRATCH = pathlib.Path(tempfile.gettempdir()) / "tit_allocator_prio.db"
if SCRATCH.exists():
    SCRATCH.unlink()

import database.db as db  # noqa: E402

db.DB_PATH = SCRATCH
_c = db.get_connection()
db.init_db(_c)
_c.close()

import agent.multi_asset_batch as MA  # noqa: E402
import config  # noqa: E402

fehler = []


def pruefe(name, ok, info=""):
    print(("  OK   " if ok else "  FEHL ") + name + ("  " + info if info else ""))
    if not ok:
        fehler.append(name)


_ORIGINAL_LOAD = config.load_config
_VORHER = config.manuelle_schwerpunkte()


def _mit_schwerpunkten(liste):
    cfg = copy.deepcopy(_ORIGINAL_LOAD())
    cfg.setdefault("schwerpunkte", {})["manuell"] = liste
    config.load_config = lambda *a, **k: cfg


WATCHLIST = config.get_watchlist()
CONFIG = {
    "multi_asset_batch": {"aktiv": True, "cooldown_stunden_gehalten": 0,
                          "cooldown_stunden_beobachtet": 0},
    "budget_allocator": {"gemini_taegliches_budget": 10_000,
                         "mistral_taegliches_budget": 10_000,
                         "openrouter_taegliches_budget": 10_000},
}


class _Client:
    name = "gemini"


def lauf():
    """Ein Batch-Lauf; gibt die Reihenfolge der verarbeiteten Symbole zurueck."""
    reihenfolge = []

    def rekorder(asset, watchlist, conn, client, coingecko_client=None, **kw):
        reihenfolge.append(asset.symbol)

        class _Ergebnis:
            gate_passed = True
            action = "HALTEN"
            position_size_usd = 0.0

        return _Ergebnis()

    alt = MA._pipeline_fuer
    MA._pipeline_fuer = lambda asset: rekorder
    try:
        ergebnis = MA.run_multi_asset_batch(
            db.get_connection, WATCHLIST, None, CONFIG,
            gemini_client=_Client(), mistral_client=None, zai_client=None,
            openrouter_client=None,
        )
    finally:
        MA._pipeline_fuer = alt
    return reihenfolge, ergebnis


print("A) OHNE SCHWERPUNKT - die Reihenfolge muss unveraendert bleiben")
_mit_schwerpunkten([])
ohne, erg_ohne = lauf()
pruefe("A1 ueberhaupt Kandidaten da", len(ohne) >= 5,
       f"{len(ohne)} faellige Assets - sonst prueft der Test nichts")
pruefe("A2 nichts vorgezogen", erg_ohne.vorgezogen_schwerpunkt == 0,
       "leere Liste muss ein No-Op sein")

print("\nB) MIT SCHWERPUNKT industriemetalle (VVMX, CEBS, OD7C)")
_mit_schwerpunkten(["industriemetalle"])
mit, erg_mit = lauf()
ERWARTET = {"VVMX", "CEBS", "OD7C"}
vorne = set(mit[:len(ERWARTET)])
pruefe("B1 die drei Schwerpunkt-Assets stehen VORNE", vorne == ERWARTET,
       f"vorne: {mit[:3]}")
pruefe("B2 Zaehler meldet sie", erg_mit.vorgezogen_schwerpunkt == len(ERWARTET),
       f"{erg_mit.vorgezogen_schwerpunkt} gemeldet")

print("\nC) NUR DIE REIHENFOLGE - nicht die AUSWAHL")
pruefe("C1 dieselbe Menge wie ohne Schwerpunkt", set(mit) == set(ohne),
       f"{len(mit)} gegen {len(ohne)} Assets")
pruefe("C2 dieselbe Anzahl", len(mit) == len(ohne))

print("\nD) STABIL - die uebrigen behalten ihre Reihenfolge")
uebrige_mit = [s for s in mit if s not in ERWARTET]
uebrige_ohne = [s for s in ohne if s not in ERWARTET]
pruefe("D1 Reihenfolge der uebrigen unveraendert", uebrige_mit == uebrige_ohne,
       "kein Re-Sort, nur eine stabile Partition")

print("\nE) UNTERKATEGORIE-SCHWERPUNKT trifft genau eines")
_mit_schwerpunkten(["industriemetalle:kupfer"])
kupfer, erg_kupfer = lauf()
# CEBS und OD7C sind kupfer, VVMX ist seltene_erden
pruefe("E1 nur die Kupfer-Assets vorgezogen",
       set(kupfer[:2]) == {"CEBS", "OD7C"} and erg_kupfer.vorgezogen_schwerpunkt == 2,
       f"vorne: {kupfer[:3]}, gemeldet: {erg_kupfer.vorgezogen_schwerpunkt}")

config.load_config = _ORIGINAL_LOAD
pruefe("F1 Konfiguration nach dem Test unveraendert",
       config.manuelle_schwerpunkte() == _VORHER, str(config.manuelle_schwerpunkte()))
try:
    SCRATCH.unlink()
except Exception:
    pass

print("\n" + ("ALLE TESTS BESTANDEN" if not fehler else f"{len(fehler)} FEHLER: {fehler}"))
sys.exit(1 if fehler else 0)
