"""Selbsttest fuer den Gemini-Tageswaechter - mit Gegenkontrollen.

ANLASS (09.08.). Ich habe an einem Tag ueber 500 Gemini-Aufrufe verbrannt und
damit die Produktion stillgelegt, ohne es zu merken. Die Messung mit
`pruefe_gemini_verhalten.py` hat danach ergeben, was Google die ganze Zeit in
jedem Fehlerkoerper mitgeschickt hat:

    GenerateRequestsPerDayPerProjectPerModel-FreeTier = 500

Drei Dinge folgen daraus, und dieser Test sichert alle drei ab:

    PerDay      Ein 429 daraus ist NICHT durch Warten zu heilen. Die alte
                Fassung hat ihn dreimal wiederholt - bis zu zwei Minuten je
                Aufruf, um dreimal dasselbe zu hoeren.
    PerProject  Das Budget haengt am Schluessel. Der Waechter muss im CLIENT
                sitzen, nicht im budget_allocator - Messskripte gehen an
                letzterem vorbei, und genau das ist passiert.
    PerModel    Je Modell ein eigener Topf, also je Modell ein eigener Zaehler.

Dazu die Tagesgrenze: Google setzt zu Mitternacht PAZIFIK zurueck. Ein
UTC-Zaehler steht zwischen 00:00 und ~08:00 UTC auf 0, waehrend Google noch
den Vortag fuehrt - der Waechter liesse genau dann durch, wenn nichts mehr da
ist.

OHNE ECHTE AUFRUFE und ohne echte DB: beides ist Attrappe. Ein Test, der
Kontingent verbraucht, um Kontingentschutz zu pruefen, waere absurd - und ein
Test, der in die echte Zaehlung schreibt, faelscht genau die Zahl, auf die
sich der Waechter morgen verlaesst.

    python teste_gemini_tagesbudget.py
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta, timezone

import database.api_health as _health
import database.db as _db

# DB abklemmen, BEVOR api.gemini importiert wird - siehe teste_gemini_429.py:
# `@track_api_health` schreibt sonst in die echte Datenbank.
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
        self._daten = daten or {"choices": [{"message": {"content": "OK"}}]}

    def json(self):
        return self._daten


class Session:
    def __init__(self, folge):
        self.folge = list(folge)
        self.aufrufe = 0

    def post(self, *a, **kw):
        self.aufrufe += 1
        return self.folge.pop(0) if self.folge else Antwort(200)


def koerper(quota_id, wert=500, als_liste=False):
    """Ein echter Google-Fehlerkoerper, wie am 09.08. gemessen."""
    d = {"error": {"code": 429, "message": "Quota exceeded", "details": [
        {"@type": "type.googleapis.com/google.rpc.QuotaFailure",
         "violations": [{"quotaId": quota_id, "quotaValue": str(wert),
                         "quotaMetric": "generativelanguage.googleapis.com/"
                                        "generate_content_free_tier_requests"}]}]}}
    return json.dumps([d] if als_liste else d)


TAG = "GenerateRequestsPerDayPerProjectPerModel-FreeTier"
MINUTE = "GenerateRequestsPerMinutePerProjectPerModel-FreeTier"

# Zaehlerstand als Attrappe: {source: anzahl}. So laesst sich ein voller Tag
# herstellen, ohne 500 Aufrufe zu machen.
_stand = {}
_gebucht = []
G.verbrauch_heute = lambda source, tag=None: _stand.get(source, 0)
G.zaehle_aufruf = lambda source, tag=None: _gebucht.append((source, tag))
G.time.sleep = lambda s: _geschlafen.append(s)
_geschlafen = []


def client(folge, budget=500, reserve=0):
    k = G.GeminiClient("attrappe", session=Session(folge),
                       tagesbudget=budget, reserve=reserve)
    k._drossel.warte_auf_slot = lambda: None
    return k


print("A  Der Tagesschluessel folgt GOOGLE, nicht UTC")

tag = G._kontingent_tag()
pruefe("A1 Format YYYY-MM-DD", len(tag) == 10 and tag[4] == "-", tag)
pazifik_erwartet = (datetime.now(timezone.utc) - timedelta(hours=8)).date()
utc_heute = datetime.now(timezone.utc).date()
pruefe("A2 der Schluessel liegt auf dem Pazifik-Datum (heute oder gestern UTC)",
       tag in (str(pazifik_erwartet), str(utc_heute),
               str(pazifik_erwartet + timedelta(days=1))),
       f"{tag}, UTC {utc_heute}")
# GEGENKONTROLLE: in den ersten UTC-Stunden MUSS er vom UTC-Datum abweichen -
# genau dort versagt ein UTC-Zaehler. Nur pruefbar, wenn wir gerade in dem
# Fenster sind; sonst wird die Rechnung selbst geprueft.
h = datetime.now(timezone.utc).hour
if h < 8:
    pruefe("A2g Gegenkontrolle: im UTC-Fruehfenster weicht er ab",
           tag != str(utc_heute), f"{tag} vs UTC {utc_heute}")
else:
    pruefe("A2g Gegenkontrolle: ausserhalb des Fensters stimmen sie ueberein",
           tag == str(utc_heute), f"{tag} vs UTC {utc_heute}")

print("\nB  Der Fehlerkoerper wird GELESEN - in beiden Formen")

pruefe("B1 Objekt-Form (nativer Endpunkt)",
       [v["quotaId"] for v in G._quota_verletzungen(Antwort(429, koerper(TAG)))]
       == [TAG])
pruefe("B2 Listen-Form (Kompat-Endpunkt) - daran lag es",
       [v["quotaId"] for v in
        G._quota_verletzungen(Antwort(429, koerper(TAG, als_liste=True)))]
       == [TAG])
pruefe("B3 der Grenzwert kommt mit",
       G._quota_verletzungen(Antwort(429, koerper(TAG)))[0]["quotaValue"] == "500")
# GEGENKONTROLLEN: nichts erfinden, wo nichts steht.
pruefe("B3g Gegenkontrolle: Muell ergibt eine leere Liste, keinen Absturz",
       G._quota_verletzungen(Antwort(429, "<html>502</html>")) == [])
pruefe("B4g Gegenkontrolle: ein Fehler OHNE QuotaFailure ergibt nichts",
       G._quota_verletzungen(Antwort(400, json.dumps(
           {"error": {"message": "Ungueltiges Schema", "details": []}}))) == [])

print("\nC  Tageslimit und Minutenlimit werden UNTERSCHIEDEN")

pruefe("C1 PerDay wird als Tageslimit erkannt",
       G._ist_tageskontingent(Antwort(429, koerper(TAG))))
pruefe("C1g Gegenkontrolle: PerMinute wird NICHT als Tageslimit erkannt",
       not G._ist_tageskontingent(Antwort(429, koerper(MINUTE))))
pruefe("C2g Gegenkontrolle: ohne Details gilt nicht 'Tag' (sonst wuerde jeder "
       "unklare 429 den Rest des Tages sperren)",
       not G._ist_tageskontingent(Antwort(429, "")))

print("\nD  Ein Tages-429 wird nicht wiederholt, ein Minuten-429 schon")

_stand.clear(); _geschlafen.clear(); G._erschoepft.clear()
s = Session([Antwort(429, koerper(TAG))])
k = G.GeminiClient("attrappe", session=s); k._drossel.warte_auf_slot = lambda: None
try:
    k.chat([{"role": "user", "content": "x"}])
    pruefe("D1 Tages-429 wirft", False, "kein Fehler")
except G.TageskontingentErschoepft as exc:
    pruefe("D1 Tages-429 wirft den EIGENEN Typ", True)
    pruefe("D2 die Meldung nennt quotaId und Grenzwert",
           TAG in str(exc) and "500" in str(exc), str(exc)[:100])
    pruefe("D3 das Modell steht als Feld daran, nicht nur im Text",
           exc.modell == G.DEFAULT_MODEL, str(exc.modell))
except Exception as exc:  # noqa: BLE001
    pruefe("D1 Tages-429 wirft den EIGENEN Typ", False, type(exc).__name__)
pruefe("D4 GENAU EIN Aufruf - keine Wiederholung, kein Warten",
       s.aufrufe == 1 and _geschlafen == [], f"{s.aufrufe} Aufrufe, {_geschlafen}")

# GEGENKONTROLLE: der Minutenfall muss weiter wiederholt werden - sonst hat die
# Reparatur die Reparatur vom Vormittag kaputtgemacht.
_geschlafen.clear(); G._erschoepft.clear()
s = Session([Antwort(429, koerper(MINUTE)), Antwort(200)])
k = G.GeminiClient("attrappe", session=s); k._drossel.warte_auf_slot = lambda: None
pruefe("D4g Gegenkontrolle: Minuten-429 wird wiederholt und liefert",
       k.chat([{"role": "user", "content": "x"}]) == "OK",
       f"{s.aufrufe} Aufrufe, geschlafen {_geschlafen}")
pruefe("D5g Gegenkontrolle: dabei wurde tatsaechlich gewartet",
       len(_geschlafen) == 1, str(_geschlafen))

print("\nE  Der Waechter greift VOR dem Aufruf")

_stand.clear(); G._erschoepft.clear()
_stand["gemini:" + G.DEFAULT_MODEL] = 500
s = Session([Antwort(200)])
k = G.GeminiClient("attrappe", session=s, tagesbudget=500)
k._drossel.warte_auf_slot = lambda: None
try:
    k.chat([{"role": "user", "content": "x"}])
    pruefe("E1 bei vollem Zaehler wird abgebrochen", False, "durchgelassen")
except G.TageskontingentErschoepft:
    pruefe("E1 bei vollem Zaehler wird abgebrochen", True)
pruefe("E2 und zwar OHNE einen einzigen HTTP-Aufruf",
       s.aufrufe == 0, f"{s.aufrufe} Aufrufe")

# GEGENKONTROLLE: knapp darunter muss er durchlassen, sonst blockiert der
# Waechter den Normalbetrieb.
_stand["gemini:" + G.DEFAULT_MODEL] = 499
G._erschoepft.clear()
s = Session([Antwort(200)])
k = G.GeminiClient("attrappe", session=s, tagesbudget=500)
k._drossel.warte_auf_slot = lambda: None
pruefe("E2g Gegenkontrolle: bei 499 von 500 laeuft der Aufruf",
       k.chat([{"role": "user", "content": "x"}]) == "OK" and s.aufrufe == 1)

# GEGENKONTROLLE: der Zaehler ist JE MODELL. Ein volles Modell darf ein
# anderes nicht sperren - das war der ganze Punkt des PerModel-Befunds.
_stand.clear(); G._erschoepft.clear()
_stand["gemini:" + G.DEFAULT_MODEL] = 500
s = Session([Antwort(200)])
k = G.GeminiClient("attrappe", session=s, tagesbudget=500)
k._drossel.warte_auf_slot = lambda: None
pruefe("E3g Gegenkontrolle: ein anderes Modell hat sein eigenes Budget",
       k.chat([{"role": "user", "content": "x"}],
              model="gemini-3.5-flash-lite") == "OK", f"{s.aufrufe} Aufrufe")

print("\nF  Reserve und Buchung")

_stand.clear(); G._erschoepft.clear()
_stand["gemini:" + G.DEFAULT_MODEL] = 460
k = G.GeminiClient("attrappe", session=Session([]), tagesbudget=500, reserve=50)
st = k.budget_status()
pruefe("F1 Reserve wird abgezogen (500-50-460 = 0 verfuegbar)",
       st["verfuegbar"] == 0 and st["erschoepft"], str(st))
s = Session([Antwort(200)])
k = G.GeminiClient("attrappe", session=s, tagesbudget=500, reserve=50)
k._drossel.warte_auf_slot = lambda: None
try:
    k.chat([{"role": "user", "content": "x"}])
    pruefe("F2 die Reserve haelt die Produktion frei", False, "durchgelassen")
except G.TageskontingentErschoepft:
    pruefe("F2 die Reserve haelt die Produktion frei", s.aufrufe == 0)

_stand.clear(); G._erschoepft.clear(); _gebucht.clear()
s = Session([Antwort(200)])
k = G.GeminiClient("attrappe", session=s)
k._drossel.warte_auf_slot = lambda: None
k.chat([{"role": "user", "content": "x"}])
pruefe("F3 es wird ZWEIMAL gebucht: Anbieter (UTC) und Modell (Pazifik)",
       [q[0] for q in _gebucht] == ["gemini", f"gemini:{G.DEFAULT_MODEL}"],
       str(_gebucht))
pruefe("F3g Gegenkontrolle: der Anbieterzaehler bleibt auf UTC (kein Tag "
       "mitgegeben) - sonst verschiebt sich der budget_allocator",
       _gebucht[0][1] is None and _gebucht[1][1] == G._kontingent_tag(),
       str(_gebucht))

print("\nG  Einmal erschoepft, danach ohne Aufruf")

G._erschoepft.clear(); _stand.clear()
s = Session([Antwort(429, koerper(TAG)), Antwort(200)])
k = G.GeminiClient("attrappe", session=s)
k._drossel.warte_auf_slot = lambda: None
for _ in range(3):
    try:
        k.chat([{"role": "user", "content": "x"}])
    except G.TageskontingentErschoepft:
        pass
pruefe("G1 drei Versuche nach einem Tages-429 kosten EINEN Aufruf",
       s.aufrufe == 1, f"{s.aufrufe} Aufrufe")
# GEGENKONTROLLE: die Sperre gilt fuer DIESES Modell, nicht global.
s2 = Session([Antwort(200)])
k2 = G.GeminiClient("attrappe", session=s2)
k2._drossel.warte_auf_slot = lambda: None
pruefe("G1g Gegenkontrolle: ein anderes Modell bleibt erreichbar",
       k2.chat([{"role": "user", "content": "x"}],
               model="gemini-3.5-flash-lite") == "OK")

print("\n" + "=" * 70)
print(f"{_ok} Pruefungen bestanden, {len(_fehler)} fehlgeschlagen")
for f in _fehler:
    print(f"   FEHLER: {f}")
sys.exit(1 if _fehler else 0)
