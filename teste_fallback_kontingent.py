"""Weicht die Produktion auf OpenRouter aus, wenn Geminis Tag leer ist?

DER ANLASS (Nutzer, 09.08.): *"das NB laeuft aktuell nicht - danach muss es auf
open router laufen ueber das fallback."* Der Messlauf verbraucht Geminis
Tagesbudget; wenn das Notebook wieder hochfaehrt, muss die Produktion ohne
Zutun auf OpenRouter umschwenken statt stillzustehen.

WARUM DER VORHANDENE ZAEHLER DAFUER NICHT REICHT. `tages_verbraucht` zaehlt,
was DIESES GERAET verbraucht hat. Geminis Kontingent haengt aber am
API-SCHLUESSEL (500/Tag je Projekt und je Modell, gemessen am 09.08.). Ein
Messlauf am Desktop ist fuer den Zaehler des Notebooks unsichtbar - der steht
auf 0, waehrend Google laengst abweist. Der einzige verlaessliche Zeuge ist
der Anbieter selbst, im Fehlerkoerper.

WAS HIER GEPRUEFT WIRD: die Unterscheidung, an der die ganze Kette haengt -
"Budget leer" gegen "Anbieter gestoert". Sie hat zwei verschiedene Folgen:

    Budget leer    sofort und fuer den ganzen Lauf ueberspringen; KEIN
                   Eintrag in api_health_status, der Anbieter ist gesund
    Stoerung       normaler Fehlschlag, Circuit Breaker sperrt nach dreien

    python teste_fallback_kontingent.py
"""
from __future__ import annotations

import sys

import requests

_ok, _fehler = 0, []


def pruefe(name, bedingung, detail=""):
    global _ok
    if bedingung:
        _ok += 1
        print(f"  [ok]     {name}" + (f"   {detail}" if detail else ""))
    else:
        _fehler.append(name)
        print(f"  [FEHLER] {name}   {detail}")


from agent.krypto.budget_allocator import (_ist_kontingent_leer,  # noqa: E402
                                           _TageskontingentErschoepft)
from api.gemini import TageskontingentErschoepft  # noqa: E402

print("A  Der Typ ist ueberhaupt angekommen")

# Der Import im Allocator ist bewusst in try/except gekapselt, damit ein
# kaputtes api/ den Allocator nicht mitnimmt. Der Preis: faellt er aus, wird
# still auf () zurueckgefallen und die Unterscheidung ist WIRKUNGSLOS - genau
# die Sorte stiller Ausfall, die uns schon zweimal Tage gekostet hat.
pruefe("A1 der echte Typ ist importiert, nicht der stille Rueckfall auf ()",
       _TageskontingentErschoepft is TageskontingentErschoepft,
       str(_TageskontingentErschoepft))

print("\nB  Budget leer wird erkannt")

exc = TageskontingentErschoepft("Tagesbudget erschoepft", modell="m")
pruefe("B1 ein leeres Tageskontingent wird als solches erkannt",
       _ist_kontingent_leer(exc))

print("\nC  Gegenkontrollen - was NICHT als leeres Budget gelten darf")

# DIE FALLE: TageskontingentErschoepft ERBT von requests.HTTPError. Wer auf den
# Elterntyp pruefte, erklaerte jeden HTTP-Fehler zum leeren Budget und naehme
# den Anbieter wegen eines 500ers bis morgen frueh aus der Kette.
pruefe("C1 die Vererbung ist da (sonst faengt except HTTPError ihn nicht)",
       issubclass(TageskontingentErschoepft, requests.HTTPError))
pruefe("C1g Gegenkontrolle: ein GEWOEHNLICHER HTTPError ist KEIN leeres Budget",
       not _ist_kontingent_leer(requests.HTTPError("Gemini HTTP 500")))
pruefe("C2g Gegenkontrolle: ein Zeitueberschreitungsfehler ebenso wenig",
       not _ist_kontingent_leer(requests.Timeout("timeout")))
pruefe("C3g Gegenkontrolle: ein Schemafehler ebenso wenig",
       not _ist_kontingent_leer(ValueError("kein JSON")))
pruefe("C4g Gegenkontrolle: ein 429 aus dem MINUTENfenster ebenso wenig - "
       "der heilt durch Warten",
       not _ist_kontingent_leer(requests.HTTPError("Gemini HTTP 429")))

print("\nD  Die Kette faengt ihn ueberhaupt")

# `_mit_fallback_chain` faengt mit `except Exception`. Erbte der Typ nicht von
# Exception, fiele er durch und risse den ganzen Lauf mit.
pruefe("D1 der Typ ist eine Exception - 'except Exception' greift",
       issubclass(TageskontingentErschoepft, Exception))
pruefe("D2 das Modell haengt als Feld daran, nicht nur im Text",
       exc.modell == "m", str(exc.modell))

print("\nE  Die Reihenfolge in der Kette stimmt")

# Ohne diesen Test koennte OpenRouter vor Gemini stehen und das Ausweichen
# waere zufaellig richtig. Gemini MUSS vor OpenRouter kommen, sonst weicht
# nichts aus - es liefe von vornherein OpenRouter.
import inspect  # noqa: E402

import agent.krypto.budget_allocator as BA  # noqa: E402

quelle = inspect.getsource(BA)
i_g = quelle.find('calls.append(("gemini"')
i_o = quelle.find('calls.append(("openrouter"')
pruefe("E1 Gemini steht in der Kette VOR OpenRouter",
       0 < i_g < i_o, f"gemini@{i_g}, openrouter@{i_o}")

print("\n" + "=" * 70)
print(f"{_ok} Pruefungen bestanden, {len(_fehler)} fehlgeschlagen")
for f in _fehler:
    print(f"   FEHLER: {f}")
sys.exit(1 if _fehler else 0)
