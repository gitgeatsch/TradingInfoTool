"""Sagen die Startmeldungen die Wahrheit ueber die Signal-Kette?

DER ANLASS (10.08., aus einem echten Produktionslog des Notebooks). Beim Start
meldete die App vier Stufen-Zuordnungen, von denen DREI falsch waren:

    "Gemini ... letzte Fallback-Stufe"          -> Gemini ist die ERSTE
    "Mistral ... zweite Fallback-Stufe"         -> Mistral ist die DRITTE
    "Z.ai ... letzte Fallback-Stufe (nach       -> Z.ai ist GAR NICHT in der
             Gemini) im Budget-Allocator"          Kette, das ist die
                                                   Gegenpruefung
    "OpenRouter ist zweite Stufe der            -> stimmt
     Signal-Kette (Gemini -> OpenRouter
     -> Mistral)"

Nur die neueste Zeile war richtig; die drei aelteren sind bei Umbauten nicht
mitgewandert. Das sind ausgerechnet die Zeilen, die man liest, wenn nachts die
Produktion klemmt - und sie behaupteten, Gemini komme zuletzt.

WARUM EIN TEST UND NICHT NUR EINE KORREKTUR. Eine Korrektur haelt bis zum
naechsten Umbau. Dieser Test liest die Reihenfolge aus dem CODE
(`calls.append(("gemini", ...))` im budget_allocator) und vergleicht sie mit
dem, was `main.py` beim Start behauptet. Wer die Kette aendert und die
Meldungen vergisst, faellt hier auf - nicht erst im Log um drei Uhr nachts.

    python teste_startmeldungen_kette.py
"""
from __future__ import annotations

import pathlib
import re
import sys

_ok, _fehler = 0, []


def pruefe(name, bedingung, detail=""):
    global _ok
    if bedingung:
        _ok += 1
        print(f"  [ok]     {name}" + (f"   {detail}" if detail else ""))
    else:
        _fehler.append(name)
        print(f"  [FEHLER] {name}   {detail}")


ALLOCATOR = pathlib.Path("agent/krypto/budget_allocator.py").read_text(
    encoding="utf-8")
MAIN = pathlib.Path("main.py").read_text(encoding="utf-8")

print("A  Die WIRKLICHE Reihenfolge, aus dem Code gelesen")

# Jeder Block, der eine Kette aufbaut, endet mit dem Aufruf von
# _mit_fallback_chain. Die Reihenfolge der calls.append() DAVOR ist die Kette.
bloecke = []
aktuell: list[str] = []
for zeile in ALLOCATOR.splitlines():
    treffer = re.search(r'calls\.append\(\("([a-z]+)"', zeile)
    if treffer:
        aktuell.append(treffer.group(1))
    elif aktuell and ("_mit_fallback_chain" in zeile or "calls = [" in zeile
                      or re.match(r"\s*calls = \[\]", zeile)):
        bloecke.append(tuple(aktuell))
        aktuell = []
if aktuell:
    bloecke.append(tuple(aktuell))

pruefe("A1 es gibt ueberhaupt Ketten im Allocator", bool(bloecke),
       str(bloecke))
pruefe("A2 ALLE Ketten haben dieselbe Reihenfolge - sonst gibt es keine "
       "einzelne Wahrheit, die eine Startmeldung nennen koennte",
       len(set(bloecke)) == 1, str(set(bloecke)))
kette = bloecke[0] if bloecke else ()
print(f"      Kette laut Code: {' -> '.join(kette)}")

print("\nB  Nennt jede Startmeldung ihre RICHTIGE Position?")

# Position -> Woerter, die sie korrekt beschreiben. Bewusst grosszuegig: es
# geht darum, dass keine FALSCHE Position behauptet wird.
RICHTIG = {0: ("erste", "1."), 1: ("zweite", "2."), 2: ("dritte", "3.")}
FALSCH_FUER_ERSTE = ("letzte", "zweite", "dritte")


def meldung_fuer(anbieter: str) -> str:
    """Der logger.info-Text, der DIESEN Anbieter ankuendigt.

    Es muss die Meldung sein, die MIT dem Anbieternamen BEGINNT - nicht
    irgendeine, die ihn erwaehnt. Die erste Fassung dieses Tests suchte nach
    "enthaelt den Namen" und fand fuer 'gemini' die MISTRAL-Zeile, weil dort
    "Gemini -> OpenRouter -> Mistral" im Text steht. Damit meldete er drei
    Fehler, die keine waren - ein Test, der am falschen Objekt misst, ist
    schlimmer als keiner."""
    muster = re.compile(r'logger\.info\(\s*((?:"[^"]*"\s*)+)\)', re.S)
    treffer = [" ".join(re.findall(r'"([^"]*)"', m.group(1))).strip()
               for m in muster.finditer(MAIN)]
    passend = [t for t in treffer if t.lower().startswith(anbieter.lower())]
    # OpenRouter wird ZWEIMAL angekuendigt: einmal fuer die Gegenpruefung,
    # einmal fuer die Signal-Kette. Das sind zwei getrennte Schalter an zwei
    # Stellen der Pipeline (siehe Kommentar in main.py) - hier interessiert
    # ausschliesslich die Kette.
    fuer_kette = [t for t in passend if "signal-kette" in t.lower()]
    return (fuer_kette or passend or [""])[0]


for pos, anbieter in enumerate(kette):
    text = meldung_fuer(anbieter)
    if not text:
        pruefe(f"B{pos + 1} {anbieter}: Startmeldung gefunden", False,
               "keine logger.info-Zeile mit 'API-Key gefunden'")
        continue
    klein = text.lower()
    nennt_richtig = any(w in klein for w in RICHTIG[pos])
    pruefe(f"B{pos + 1} {anbieter} nennt sich {RICHTIG[pos][0]} Stufe",
           nennt_richtig, text[:95])
    if pos == 0:
        pruefe(f"B{pos + 1}g Gegenkontrolle: {anbieter} behauptet NICHT, "
               f"letzte oder spaetere Stufe zu sein",
               not any(w in klein for w in FALSCH_FUER_ERSTE), text[:95])

print("\nC  Z.ai ist NICHT Teil der Kette und darf das nicht behaupten")

pruefe("C1 Z.ai kommt in keiner Allocator-Kette vor",
       all("zai" not in b for b in bloecke), str(bloecke))
zai = meldung_fuer("Z.ai")
pruefe("C2 die Z.ai-Startmeldung nennt sie NICHT als Fallback-Stufe der Kette",
       "fallback-stufe" not in zai.lower(), zai[:95])
pruefe("C3 und sie sagt, was Z.ai wirklich ist",
       "gegenpruefung" in zai.lower(), zai[:95])

print("\nD  Gegenkontrolle: der Test wuerde eine falsche Behauptung FINDEN")

# Ohne diese Kontrolle koennte der Test alles durchwinken und niemand merkte es.
kaputt = 'logger.info("Gemini API-Key gefunden - letzte Fallback-Stufe.")'
text = " ".join(re.findall(r'"([^"]*)"', kaputt))
pruefe("D1 die alte, falsche Gemini-Meldung wuerde durchfallen",
       not any(w in text.lower() for w in RICHTIG[0])
       and any(w in text.lower() for w in FALSCH_FUER_ERSTE), text)

print("\n" + "=" * 70)
print(f"{_ok} Pruefungen bestanden, {len(_fehler)} fehlgeschlagen")
for f in _fehler:
    print(f"   FEHLER: {f}")
sys.exit(1 if _fehler else 0)
