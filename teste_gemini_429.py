"""Selbsttest fuer die 429-Behandlung im Gemini-Client - mit Gegenkontrollen.

ANLASS (Nutzer, 09.08.): *"wenn das Kontingent erschoepft waere duerfte nichts
durchgehen - du hast geprueft alles ok und dann wieder Fehler? das passt
nicht."* Nachgemessen: drei rohe Aufrufe in drei Sekunden ergaben 200, 200,
429. Es ist also kein hartes Tageskontingent, sondern (mindestens) ein
Burst-Limit - und der Server sagt selbst, wie lange zu warten ist.

Vorher fiel ein 429 als nackter `HTTPError` durch alle Wiederholungsschleifen
der Messlaeufe (die fangen nur JSONDecodeError/ValueError). Ein Lauf verlor
dadurch 19 Messpunkte, geballt am Ende - ein stiller Selektionsfehler.

OHNE ECHTE AUFRUFE: die Antworten sind Attrappen. Ein Test, der echtes
Kontingent verbraucht, um Kontingentfehler zu pruefen, waere absurd.

    python teste_gemini_429.py
"""
from __future__ import annotations

import sys

import database.api_health as _health
import database.db as _db

# DIE DB ABKLEMMEN, BEVOR api.gemini importiert wird.
#
# `chat()` traegt `@track_api_health("gemini")`, und der Dekorator schreibt bei
# JEDEM Aufruf in die echte Datenbank - auch wenn die Session eine Attrappe
# ist. Die erste Fassung dieses Tests hat damit einen ERFUNDENEN
# "HTTP 400: Ungueltiges Schema" in `api_health_status` hinterlassen und die
# Gesundheitsdaten des Anbieters verfaelscht. Ein Test, der Diagnosedaten
# beschreibt, macht die Diagnose kaputt, die er schuetzen soll.
#
# Nicht den Dekorator patchen - der sitzt beim Import fest. Stattdessen die
# beiden Schreibfunktionen, die er benutzt.
_health.db.record_api_health_error = lambda *a, **kw: None
_health.db.record_api_health_success = lambda *a, **kw: None
_db.increment_api_call_counter = lambda *a, **kw: 0

import api.gemini as G  # noqa: E402

_ok, _fehler = 0, []


def pruefe(name, bedingung, detail=""):
    global _ok
    if bedingung:
        _ok += 1
        print(f"  [ok]     {name}" + (f"   {detail}" if detail else ""))
    else:
        _fehler.append(name)
        print(f"  [FEHLER] {name}   {detail}")


class Antwort:
    def __init__(self, status, text="", headers=None, daten=None):
        self.status_code = status
        self.text = text
        self.headers = headers or {}
        self.ok = 200 <= status < 300
        self._daten = daten or {
            "choices": [{"message": {"content": "OK"}}]}

    def json(self):
        return self._daten


class Session:
    """Liefert eine vorgegebene Folge von Antworten und zaehlt die Aufrufe."""

    def __init__(self, folge):
        self.folge = list(folge)
        self.aufrufe = 0

    def post(self, *a, **kw):
        self.aufrufe += 1
        return self.folge.pop(0) if self.folge else Antwort(200)


def client(folge, monkey_sleep):
    k = G.GeminiClient("attrappe", session=Session(folge))
    k._drossel.warte_auf_slot = lambda: None   # Drossel hier nicht messen
    return k


geschlafen = []
G.time.sleep = lambda s: geschlafen.append(s)   # keine echten Wartezeiten

print("A  Wartezeit wird aus der Antwort GELESEN, nicht geraten")

a = Antwort(429, headers={"Retry-After": "12"})
pruefe("A1 Retry-After-Header wird genutzt",
       abs(G._wartezeit_aus_antwort(a) - 12.0) < 1e-9,
       str(G._wartezeit_aus_antwort(a)))

a = Antwort(429, text='{"error":{"details":[{"retryDelay":"40s"}]}}')
pruefe("A2 retryDelay aus dem Body wird genutzt (plus 1 s Sicherheit)",
       abs(G._wartezeit_aus_antwort(a) - 41.0) < 1e-9,
       str(G._wartezeit_aus_antwort(a)))

a = Antwort(429, text="Please retry in 40.566839187s.")
pruefe("A3 Klartext-Variante wird ebenfalls erkannt",
       abs(G._wartezeit_aus_antwort(a) - 41.57) < 0.01,
       str(G._wartezeit_aus_antwort(a)))

# GEGENKONTROLLE: ohne jede Angabe darf nicht 0 herauskommen (das waere ein
# sofortiger Wiederholungssturm) und auch nichts Absurdes.
w = G._wartezeit_aus_antwort(Antwort(429, text="irgendwas"))
pruefe("A3g Gegenkontrolle: ohne Angabe eine konservative Vorgabe, nicht 0",
       w == G._VORGABE_WARTEZEIT_SEKUNDEN and w > 0, str(w))
w = G._wartezeit_aus_antwort(Antwort(429, headers={"Retry-After": "99999"}))
pruefe("A4g Gegenkontrolle: absurde Angabe wird gedeckelt",
       w == G._MAX_WARTEZEIT_SEKUNDEN, str(w))

print("\nB  Der 429 wird wiederholt statt durchgereicht")

geschlafen.clear()
k = client([Antwort(429, headers={"Retry-After": "5"}), Antwort(200)], geschlafen)
pruefe("B1 nach einem 429 kommt die Antwort des zweiten Versuchs",
       k.chat([{"role": "user", "content": "x"}]) == "OK")
pruefe("B2 es wurde tatsaechlich gewartet, mit der Server-Angabe",
       geschlafen == [5.0], str(geschlafen))

# GEGENKONTROLLE: ohne 429 darf NICHT gewartet und NICHT wiederholt werden -
# sonst verlangsamt die Reparatur jeden normalen Aufruf.
geschlafen.clear()
s = Session([Antwort(200)])
k = G.GeminiClient("attrappe", session=s)
k._drossel.warte_auf_slot = lambda: None
k.chat([{"role": "user", "content": "x"}])
pruefe("B2g Gegenkontrolle: ohne 429 kein Warten und genau EIN Aufruf",
       geschlafen == [] and s.aufrufe == 1, f"{geschlafen}, {s.aufrufe} Aufrufe")

print("\nC  Aufgeben ist begrenzt und erklaert")

geschlafen.clear()
s = Session([Antwort(429, text='{"retryDelay":"3s"}')] * 5)
k = G.GeminiClient("attrappe", session=s)
k._drossel.warte_auf_slot = lambda: None
try:
    k.chat([{"role": "user", "content": "x"}])
    pruefe("C1 dauerhafter 429 endet in einem Fehler", False, "kein Fehler")
except Exception as exc:  # noqa: BLE001
    pruefe("C1 dauerhafter 429 endet in einem Fehler", True)
    pruefe("C2 die Meldung nennt Statuscode und Versuchszahl",
           "429" in str(exc) and str(G._MAX_VERSUCHE_BEI_429) in str(exc),
           str(exc)[:90])
pruefe("C3 genau MAX_VERSUCHE Aufrufe, nicht mehr",
       s.aufrufe == G._MAX_VERSUCHE_BEI_429, f"{s.aufrufe} Aufrufe")
pruefe("C3g Gegenkontrolle: nach dem letzten Versuch wird NICHT mehr gewartet",
       len(geschlafen) == G._MAX_VERSUCHE_BEI_429 - 1, str(geschlafen))

print("\nD  Andere Fehler tragen jetzt Statuscode und Body")

s = Session([Antwort(400, text='{"error":{"message":"Ungueltiges Schema"}}')])
k = G.GeminiClient("attrappe", session=s)
k._drossel.warte_auf_slot = lambda: None
try:
    k.chat([{"role": "user", "content": "x"}])
    pruefe("D1 ein 400 wirft", False)
except Exception as exc:  # noqa: BLE001
    pruefe("D1 ein 400 wirft", True)
    pruefe("D2 Meldung nennt den Statuscode", "400" in str(exc), str(exc)[:80])
    pruefe("D3 Meldung nennt den Body - genau das fehlte am 09.08.",
           "Ungueltiges Schema" in str(exc), str(exc)[:120])
pruefe("D3g Gegenkontrolle: ein 400 wird NICHT wiederholt (nur 429 wird es)",
       s.aufrufe == 1, f"{s.aufrufe} Aufrufe")

print("\n" + "=" * 70)
print(f"{_ok} Pruefungen bestanden, {len(_fehler)} fehlgeschlagen")
for f in _fehler:
    print(f"   FEHLER: {f}")
sys.exit(1 if _fehler else 0)
