"""Was Gemini tatsaechlich begrenzt - gemessen, nicht behauptet.

ANLASS. Am 09.08. habe ich ZWEIMAL einen Mechanismus behauptet und beide Male
danebengelegen ("Tageskontingent erschoepft", dann "nur ein rollierendes
Fenster"). Beide Male widersprachen die Messungen. Der Nutzer: *"Pruefe das
Verhalten von gemini das ist alles eigenartig."*

WARUM WIR BISHER BLIND WAREN. `api/gemini.py` spricht den OpenAI-KOMPATIBILI-
TAETS-Endpunkt an (`/v1beta/openai/chat/completions`). Der uebersetzt Googles
Fehlerobjekt in das schlanke OpenAI-Format und wirft dabei genau das Feld weg,
das die Frage beantwortet: `google.rpc.QuotaFailure` mit der `quotaId`. Die
heisst entweder

    GenerateRequestsPerMinutePerProjectPerModel-FreeTier   -> Minutenfenster
    GenerateRequestsPerDayPerProjectPerModel-FreeTier      -> Tagesbudget

Der NATIVE Endpunkt (`:generateContent`) liefert sie. Ein einziger Aufruf
gegen den nativen Endpunkt beantwortet damit die Frage, an der zwei Tage
Spekulation gescheitert sind.

STUFEN, jede mit eigenem Abbruch - keine verbrennt Kontingent auf Verdacht:

    A MODELLLISTE   `GET /v1beta/models`. Zaehlt NICHT gegen das Generierungs-
                    kontingent. Trennt "Modell weg / Schluessel tot" von
                    "Kontingent voll", bevor irgendein Aufruf faellt.
    B NATIV         EIN Aufruf. Bei 429 steht die Antwort im Klartext da.
    C KOMPAT        EIN Aufruf auf den Endpunkt, den die Produktion nutzt.
                    Zeigt, wie viel Information uns die Uebersetzung nimmt.
    D BURST         Nur wenn B und C durchkommen: Aufrufe ohne Pause bis zum
                    ersten 429. Beantwortet, wo das Minutenfenster liegt -
                    die 10/min im Client stammen vom 14.07. und sind seit der
                    dokumentierten April-Kuerzung unbestaetigt.
    E ERHOLUNG      Nach dem 429 die empfohlene Zeit warten, EIN Aufruf.
                    Ein Minutenfenster erholt sich, ein Tagesbudget nicht.

    python pruefe_gemini_verhalten.py            # A-C, hoechstens 2 Aufrufe
    python pruefe_gemini_verhalten.py --burst    # zusaetzlich D und E
"""
from __future__ import annotations

import argparse
import json
import os
import time

import requests

import config as config_module
from api.gemini import BASE_URL, DEFAULT_MODEL

NATIV = ("https://generativelanguage.googleapis.com/v1beta/models/"
         f"{DEFAULT_MODEL}:generateContent")
MODELLE = "https://generativelanguage.googleapis.com/v1beta/models"

# Der kleinstmoegliche Aufruf. Jeder Token kostet Kontingent, und wir messen
# hier das Limit, nicht die Antwortqualitaet.
MINI_NATIV = {"contents": [{"parts": [{"text": "hi"}]}],
              "generationConfig": {"maxOutputTokens": 1}}
MINI_KOMPAT = {"model": DEFAULT_MODEL, "max_tokens": 1,
               "messages": [{"role": "user", "content": "hi"}]}


def melde(text: str = "") -> None:
    print(text, flush=True)


def quota_details(body: str) -> list[dict]:
    """Die QuotaFailure-Details aus dem nativen Fehlerkoerper.

    Das ist der ganze Zweck der Uebung: `quotaId` sagt, WELCHES Limit fiel,
    `quotaValue` sagt, wie hoch es ist. Beides ohne Recherche und ohne Raten."""
    try:
        daten = json.loads(body)
    except (ValueError, TypeError):
        return []
    # Der Kompat-Endpunkt antwortet mit einer LISTE auf oberster Ebene, der
    # native mit einem Objekt. Erst am 09.08. beim Messen aufgefallen.
    if isinstance(daten, list):
        daten = daten[0] if daten and isinstance(daten[0], dict) else {}
    if not isinstance(daten, dict):
        return []
    treffer = []
    for detail in (daten.get("error", {}) or {}).get("details", []) or []:
        if "QuotaFailure" in str(detail.get("@type", "")):
            treffer.extend(detail.get("violations", []) or [])
    return treffer


def zeige(antwort, kennung: str) -> None:
    melde(f"  {kennung}: HTTP {antwort.status_code}")
    if antwort.status_code == 200:
        return
    for v in quota_details(antwort.text):
        melde(f"      quotaId    {v.get('quotaId', '?')}")
        melde(f"      metric     {v.get('quotaMetric', '?')}")
        melde(f"      Grenzwert  {v.get('quotaValue', '?')}")
        for schl, wert in (v.get("quotaDimensions") or {}).items():
            melde(f"      {schl:10s} {wert}")
    if not quota_details(antwort.text):
        melde(f"      (keine QuotaFailure-Details) {antwort.text[:400]}")


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--burst", action="store_true",
                   help="Stufen D und E - verbraucht Kontingent bis zum 429")
    p.add_argument("--burst-max", type=int, default=25)
    args = p.parse_args()

    config_module.load_env()
    schluessel = os.environ.get("GEMINI_API_KEY")
    if not schluessel:
        melde("GEMINI_API_KEY fehlt.")
        return 1
    kopf = {"x-goog-api-key": schluessel, "Content-Type": "application/json"}
    kopf_kompat = {"Authorization": f"Bearer {schluessel}"}

    melde("=" * 72)
    melde(f"GEMINI-VERHALTEN  Modell {DEFAULT_MODEL}")
    melde(f"lokal {time.strftime('%Y-%m-%d %H:%M:%S')}   "
          f"UTC {time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime())}")
    melde("=" * 72)

    melde("\nA  Modelliste - kostet kein Generierungskontingent")
    try:
        a = requests.get(MODELLE, headers=kopf, timeout=30)
    except Exception as exc:  # noqa: BLE001
        melde(f"  Netzwerkfehler {type(exc).__name__}: {exc}")
        return 1
    melde(f"  HTTP {a.status_code}")
    if a.status_code == 200:
        namen = [m.get("name", "").replace("models/", "")
                 for m in a.json().get("models", [])]
        melde(f"  {len(namen)} Modelle sichtbar")
        melde(f"  unser Modell vorhanden: {DEFAULT_MODEL in namen}")
        verwandte = [n for n in namen if "flash-lite" in n]
        melde(f"  flash-lite-Varianten: {', '.join(verwandte) or 'keine'}")
    else:
        melde(f"  {a.text[:300]}")
        melde("  ABBRUCH: schon die Liste scheitert - das ist kein "
              "Kontingentproblem, sondern Schluessel oder Erreichbarkeit.")
        return 1

    melde("\nB  Nativer Endpunkt - EIN Aufruf, volle Fehlerdetails")
    b = requests.post(NATIV, headers=kopf, json=MINI_NATIV, timeout=45)
    zeige(b, "nativ")

    melde("\nC  Kompatibilitaets-Endpunkt - der, den die Produktion nutzt")
    c = requests.post(BASE_URL, headers=kopf_kompat, json=MINI_KOMPAT,
                      timeout=45)
    zeige(c, "kompat")

    if b.status_code != c.status_code:
        melde(f"  BEFUND: die beiden Endpunkte antworten UNTERSCHIEDLICH "
              f"({b.status_code} vs {c.status_code}) - sie teilen das "
              f"Kontingent also nicht so, wie angenommen.")

    # F ergibt sich ZWINGEND aus der quotaId oben: "PerProjectPerModel". Das
    # Budget haengt also am MODELL, nicht am Schluessel. Wenn das stimmt, ist
    # ein erschoepftes Modell kein erschoepfter Zugang - und die Produktion
    # koennte auf ein Geschwistermodell ausweichen, statt still zu stehen.
    # Ein Aufruf je Modell, gegen dessen EIGENES Budget.
    if b.status_code == 429:
        melde("\nF  Ist das Budget wirklich je Modell? (folgt aus 'PerModel')")
        for modell in ("gemini-2.5-flash-lite", "gemini-flash-lite-latest",
                       "gemini-2.0-flash-lite"):
            url = ("https://generativelanguage.googleapis.com/v1beta/models/"
                   f"{modell}:generateContent")
            try:
                r = requests.post(url, headers=kopf, json=MINI_NATIV,
                                  timeout=45)
            except Exception as exc:  # noqa: BLE001
                melde(f"  {modell}: Netzwerkfehler {type(exc).__name__}")
                continue
            melde(f"  {modell}: HTTP {r.status_code}"
                  + ("   <- eigenes Budget, noch frei"
                     if r.status_code == 200 else ""))
            if r.status_code not in (200, 429):
                melde(f"      {r.text[:200]}")

    if not args.burst:
        melde("\n(Stufen D und E uebersprungen - mit --burst anfordern.)")
        return 0

    if b.status_code != 200 or c.status_code != 200:
        melde("\nD/E UEBERSPRUNGEN: es kommt gerade ohnehin nichts durch. "
              "Ein Burst gegen eine geschlossene Tuer misst nichts.")
        return 0

    melde(f"\nD  Burst ohne Pause, hoechstens {args.burst_max} Aufrufe")
    start = time.time()
    erfolge = 0
    for i in range(args.burst_max):
        r = requests.post(NATIV, headers=kopf, json=MINI_NATIV, timeout=45)
        if r.status_code == 200:
            erfolge += 1
            continue
        dauer = time.time() - start
        melde(f"  erster Fehlschlag bei Aufruf {i + 1} nach {dauer:.1f} s "
              f"({erfolge} Erfolge, {erfolge / max(dauer, 0.001) * 60:.0f}/min)")
        zeige(r, f"Aufruf {i + 1}")
        break
    else:
        dauer = time.time() - start
        melde(f"  KEIN Fehlschlag in {args.burst_max} Aufrufen "
              f"({dauer:.1f} s, {args.burst_max / max(dauer, .001) * 60:.0f}/min)")
        melde("  Damit ist RATE_LIMIT_PER_MINUTE=10 zu konservativ - "
              "oder das Limit liegt woanders als vermutet.")
        return 0

    melde("\nE  Erholung - waertet ein Minutenfenster sich aus?")
    for wartezeit in (30, 30):
        melde(f"  warte {wartezeit} s ...")
        time.sleep(wartezeit)
        r = requests.post(NATIV, headers=kopf, json=MINI_NATIV, timeout=45)
        zeige(r, f"nach {wartezeit} s")
        if r.status_code == 200:
            melde("  BEFUND: erholt sich -> Minutenfenster, kein Tagesbudget.")
            return 0
    melde("  BEFUND: erholt sich innerhalb 60 s NICHT. Zusammen mit der "
          "quotaId oben ist damit geklaert, welches Limit greift.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
