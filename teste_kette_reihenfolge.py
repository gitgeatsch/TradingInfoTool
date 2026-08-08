"""Kettenreihenfolge des Budget-Allocators - Teil C2 (2026-08-09).

PRUEFT: Gemini -> OpenRouter -> Mistral, und zwar an der ECHTEN
`run_budget_allocator()`, nicht an einem Nachbau der Auswahllogik. Der Grund
steht in Memory project_stop_regelfamilie_und_testluecke_02_08: eine
Gate-Aenderung braucht einen E2E der AUFRUFENDEN Funktion - ein Test, der die
Kette selbst zusammensetzt, prueft den Test.

WAS ECHT IST UND WAS ATTRAPPE:
  echt      - run_budget_allocator() samt Budgetlogik, Circuit Breaker,
              Kandidatenauswahl und Cooldown-Filtern
  echt      - die Watchlist aus config.yaml und die DB-Zeilen aus einer KOPIE
              der Produktiv-DB (Memory feedback_fail_soft_ist_fail_silent:
              Tests muessen DB-Zeilen LADEN statt nachbauen)
  Attrappe  - nur die drei Signal-Erzeuger (generate_hebel_signal,
              generate_signal, generate_candidate_writeup) und
              compute_current_regime. Sie machen echte Netzwerk- und
              LLM-Aufrufe; hier interessiert ausschliesslich, WELCHER Client
              bei ihnen ankommt.

LAEUFT NIE GEGEN DIE PRODUKTIV-DB (stehende Vorgabe, Memory
feedback_desktop_kein_produktivstart). Die Kopie wird am Ende geloescht.

AUFRUF:  python teste_kette_reihenfolge.py
"""
import os
import pathlib
import shutil
import sys
import tempfile

from dotenv import load_dotenv

load_dotenv()

SCRATCH = pathlib.Path(tempfile.gettempdir()) / "tit_kette_reihenfolge.db"
shutil.copy("data/tradinginfotool.db", SCRATCH)

import database.db as db  # noqa: E402

db.DB_PATH = SCRATCH

# MIGRATION AUF DER KOPIE (2026-08-09). Die Desktop-Datei ist eine Export-Kopie
# und liegt regelmaessig ein paar Schema-Schritte hinter dem Notebook zurueck -
# ohne diesen Aufruf stirbt der Test an `no such column: angefragte_richtung`
# und sieht dann aus wie ein Fehler der Kette. init_db() ist idempotent.
_conn = db.get_connection()
try:
    db.init_db(_conn)
finally:
    _conn.close()

import config  # noqa: E402
import agent.krypto.budget_allocator as ba  # noqa: E402

WATCHLIST = config.get_watchlist()
BASIS_CONFIG = config.load_config()

fehler: list[str] = []
lauf_nr = 0


class Attrappe:
    """Ein Client, der nur seinen Namen kennt - und auf Wunsch scheitert.

    `fehler_text` ist bewusst frei waehlbar: der Circuit Breaker unterscheidet
    dauerhafte (402/401/403) von voruebergehenden Fehlern, und dieser
    Unterschied ist einer der Pruefpunkte."""

    def __init__(self, name: str, fehler_text: str | None = None):
        self.name = name
        self.fehler_text = fehler_text
        self.aufrufe = 0


def _mache_attrappen_erzeuger(protokoll: list):
    """Ersetzt die drei Signal-Erzeuger durch Rekorder, die festhalten, welcher
    Client sie erreicht hat - und die scheitern, wenn dieser Client scheitern
    soll."""

    def _rekorder(client):
        protokoll.append(client.name)
        client.aufrufe += 1
        if client.fehler_text is not None:
            raise RuntimeError(client.fehler_text)

        class _Ergebnis:
            gate_passed = True
            symbol = "TEST"
            action = "HALTEN"
            short_reasoning = "Attrappe"

        return _Ergebnis()

    def hebel(trigger, asset, watchlist, conn, client, *a, **kw):
        return _rekorder(client)

    def spot(asset, watchlist, conn, client, *a, **kw):
        return _rekorder(client)

    def writeup(candidate, regime, client, *a, **kw):
        _rekorder(client)
        return {"short_reasoning": "Attrappe", "long_reasoning": {}}

    return hebel, spot, writeup


def lauf(titel, *, gemini, openrouter, mistral, openrouter_budget=400):
    """Ein vollstaendiger Allocator-Lauf mit Attrappen-Clients.

    Cooldowns auf 0: sonst haengt die Anzahl der Kandidaten davon ab, wann die
    kopierte DB zuletzt echte Signale gesehen hat - der Test waere dann mal
    aussagekraeftig und mal leer, ohne dass man es merkt."""
    global lauf_nr
    lauf_nr += 1
    protokoll: list[str] = []
    hebel, spot, writeup = _mache_attrappen_erzeuger(protokoll)

    cfg = dict(BASIS_CONFIG)
    cfg["budget_allocator"] = {
        **BASIS_CONFIG.get("budget_allocator", {}),
        "aktiv": True,
        "taegliches_budget_gesamt": 6,
        "spot_rotation_reserve": 6,
        "cooldown_stunden": 0,
        "spot_cooldown_stunden": 0,
        "spot_cooldown_stunden_kern": 0,
        "spot_cooldown_stunden_ausgemustert": 0,
        "spot_cooldown_stunden_re_evaluierung": 0,
        "openrouter_taegliches_budget": openrouter_budget,
        # Hohe Deckel fuer die beiden anderen: dieser Test misst die
        # REIHENFOLGE, nicht die Budgets - ein zufaellig erschoepftes
        # Gemini-Budget wuerde stillschweigend das Falsche pruefen.
        "gemini_taegliches_budget": 10_000,
        "mistral_taegliches_budget": 10_000,
    }

    alt = (ba.generate_hebel_signal, ba.generate_signal,
           ba.generate_candidate_writeup, ba.compute_current_regime)
    ba.generate_hebel_signal = hebel
    ba.generate_signal = spot
    ba.generate_candidate_writeup = writeup
    ba.compute_current_regime = lambda *a, **kw: None
    try:
        ergebnis = ba.run_budget_allocator(
            db.get_connection, WATCHLIST, None, None, None, cfg,
            gemini_client=gemini, mistral_client=mistral,
            zai_client=None, on_signal_ready=None,
            openrouter_client=openrouter,
        )
    finally:
        (ba.generate_hebel_signal, ba.generate_signal,
         ba.generate_candidate_writeup, ba.compute_current_regime) = alt

    bediener = sorted(set(ergebnis.provider_je_call.values()))
    print(f"\n{lauf_nr}. {titel}")
    print(f"   Kandidaten verarbeitet: {len(ergebnis.provider_je_call)}")
    print(f"   bedient von: {bediener or 'niemandem'}")
    print(f"   Aufrufversuche: {protokoll.count('gemini')}x gemini, "
          f"{protokoll.count('openrouter')}x openrouter, "
          f"{protokoll.count('mistral')}x mistral")
    if ergebnis.budget_erschoepft:
        print(f"   Budget erschoepft: {dict(ergebnis.budget_erschoepft)}")
    return ergebnis, protokoll


def pruefe(bedingung, text):
    if bedingung:
        print(f"   OK   {text}")
    else:
        print(f"   FEHL {text}")
        fehler.append(text)


print("=" * 74)
print("KETTENREIHENFOLGE Gemini -> OpenRouter -> Mistral")
print(f"Watchlist: {len(WATCHLIST)} Assets aus config.yaml")
print(f"DB-Kopie:  {SCRATCH}")
print("=" * 74)

# --- 1. Grundfall: alle drei da, alle gesund --------------------------------
g, o, m = Attrappe("gemini"), Attrappe("openrouter"), Attrappe("mistral")
erg, prot = lauf("Alle drei gesund - Gemini muss ALLES bedienen",
                 gemini=g, openrouter=o, mistral=m)

# WACHE GEGEN EINEN LEEREN TEST: ohne Kandidaten waeren alle folgenden
# Zusicherungen wahr, ohne irgendetwas geprueft zu haben.
KANDIDATEN = len(erg.provider_je_call)
pruefe(KANDIDATEN >= 2,
       f"mindestens 2 Kandidaten im Lauf (sonst prueft der Test nichts) - {KANDIDATEN}")
pruefe(set(erg.provider_je_call.values()) == {"gemini"},
       "jeder Kandidat wurde von Gemini bedient")
pruefe(o.aufrufe == 0 and m.aufrufe == 0,
       "OpenRouter und Mistral wurden gar nicht erst versucht")

# --- 2. Gemini faellt aus ---------------------------------------------------
g, o, m = Attrappe("gemini", "503 Service Unavailable"), Attrappe("openrouter"), Attrappe("mistral")
erg, prot = lauf("Gemini faellt aus - OpenRouter muss uebernehmen",
                 gemini=g, openrouter=o, mistral=m)
pruefe(set(erg.provider_je_call.values()) == {"openrouter"},
       "jeder Kandidat wurde von OpenRouter bedient")
pruefe(m.aufrufe == 0,
       "Mistral wurde nicht versucht - OpenRouter steht VOR ihm")

# --- 3. Gemini und OpenRouter fallen aus ------------------------------------
g = Attrappe("gemini", "503 Service Unavailable")
o = Attrappe("openrouter", "500 Internal Server Error")
m = Attrappe("mistral")
erg, prot = lauf("Gemini + OpenRouter aus - Mistral ist die letzte Stufe",
                 gemini=g, openrouter=o, mistral=m)
pruefe(set(erg.provider_je_call.values()) == {"mistral"},
       "jeder Kandidat wurde von Mistral bedient")
pruefe(len(erg.fehlgeschlagen) == 0,
       "kein Kandidat blieb unverarbeitet")

# --- 4. OpenRouter-Budget erschoepft ----------------------------------------
g = Attrappe("gemini", "503 Service Unavailable")
o, m = Attrappe("openrouter"), Attrappe("mistral")
erg, prot = lauf("OpenRouter-Budget auf 0 - Stufe muss UEBERSPRUNGEN werden",
                 gemini=g, openrouter=o, mistral=m, openrouter_budget=0)
pruefe(o.aufrufe == 0,
       "OpenRouter wurde NICHT versucht (uebersprungen, nicht gescheitert)")
pruefe(erg.budget_erschoepft.get("openrouter") is True,
       "budget_erschoepft meldet openrouter")
pruefe(set(erg.provider_je_call.values()) == {"mistral"},
       "Mistral hat uebernommen")

# --- 5. Circuit Breaker bei dauerhaftem Fehler ------------------------------
g = Attrappe("gemini", "503 Service Unavailable")
o = Attrappe("openrouter", "402 Payment Required")
m = Attrappe("mistral")
erg, prot = lauf("OpenRouter mit 402 - Breaker muss nach dem ERSTEN Fehler sperren",
                 gemini=g, openrouter=o, mistral=m)
pruefe(o.aufrufe == 1,
       f"OpenRouter genau EINMAL versucht, nicht {KANDIDATEN}x (402 ist ein "
       f"dauerhafter Fehler) - tatsaechlich {o.aufrufe}x")
pruefe(set(erg.provider_je_call.values()) == {"mistral"},
       "Mistral hat trotzdem alle Kandidaten bedient")

# --- 6. Kein OpenRouter-Client (Schalter aus) -------------------------------
g = Attrappe("gemini", "503 Service Unavailable")
m = Attrappe("mistral")
erg, prot = lauf("Kein OpenRouter-Client - alte Kette muss unveraendert tragen",
                 gemini=g, openrouter=None, mistral=m)
pruefe(set(erg.provider_je_call.values()) == {"mistral"},
       "Gemini -> Mistral funktioniert weiterhin ohne OpenRouter")
pruefe("openrouter" not in erg.provider_je_call.values(),
       "kein Kandidat wurde openrouter zugeschrieben")

# --- Ergebnis ---------------------------------------------------------------
print("\n" + "=" * 74)
if fehler:
    print(f"{len(fehler)} PRUEFUNG(EN) FEHLGESCHLAGEN:")
    for f in fehler:
        print(f"  - {f}")
else:
    print("Alle Pruefungen bestanden.")
print("=" * 74)

try:
    SCRATCH.unlink()
except Exception:
    pass

sys.exit(1 if fehler else 0)
