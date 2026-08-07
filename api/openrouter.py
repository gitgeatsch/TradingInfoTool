"""OpenRouter-Client, ausschliesslich fuer die Gegenpruefung (2026-08-07).

WARUM DIESER ANBIETER UEBERHAUPT. Mistral hat am 07.08. alle Modelle
kostenpflichtig gestellt (Free-Plan: 10 $ Monatsbudget, kontoweit ueber Studio/
Vibe Code/API geteilt, Reset in 24 Tagen). Danach trug **Gemini allein** alle
142 Signale des Tages - ein Ein-Anbieter-Risiko. Die Suche nach einem zweiten
freien Anbieter (Runde 5, siehe Regelwerk-Entscheidungslog) ergab: der
Ausschlussgrund ist unser EIGENER System-Prompt mit ~9.100 Token, nicht das
Tagesvolumen. Cerebras und Z.ai haetten je 1 Mio. Token/Tag, scheitern aber an
8K Kontext. Groq hat 100K Token/TAG - acht Analysen.

WARUM NUR FUER DIE GEGENPRUEFUNG. Die meisten freien Endpunkte auf OpenRouter
verlangen, dass Logging/Training aktiviert ist - Prompts werden Trainings- bzw.
Evaluierungsmaterial. Unser SYSTEM_PROMPT ist mit ~9.100 Token das inhaltliche
Herzstueck des Projekts (Regelwerk, Bewertungslogik, Risikokriterien); den
dorthin zu schicken hiesse, genau diese Arbeit wegzugeben.

Die Gegenpruefung (`agent/krypto/gegenpruefung.py`) benutzt dagegen einen
bewusst schlanken Faktensatz von rund zehn Feldern und bekommt den
SYSTEM_PROMPT **nie** zu sehen. Der Nutzer hat die Trainings-Freigabe genau
dafuer - und nur dafuer - ausdruecklich erteilt (07.08.).

**Wer diesen Client in die Haupt-Signalkette haengt, macht diese Entscheidung
rueckgaengig, ohne sie zu treffen.** Deshalb steht das hier und nicht nur im
Entscheidungslog.

WIE KEINE KOSTEN ENTSTEHEN. Zwei Regeln, beide hier im Code durchgesetzt statt
auf Disziplin gebaut:

  1. **Nur `:free`-Modell-IDs.** Auf OpenRouter existieren Modelle doppelt -
     einmal bezahlt, einmal mit `:free`-Suffix zum Nullpreis. `chat()` weist
     jede ID ohne dieses Suffix ab.
  2. **Kein Auto-Router, kein Modell-Fallback.** OpenRouters `models`-Feld und
     die Auto-Routing-Endpunkte koennen eine Anfrage auf einer bezahlten
     Variante landen lassen. Wir senden immer genau EIN explizites Modell.

Damit zehrt die Nutzung das Guthaben nicht auf. Das ist wichtig, weil der
Tagesboden fuer freie Modelle an "Credits purchased (all time)" haengt: ab
10 $ Lebenszeit-Kauf dauerhaft 1.000 statt 50 Anfragen/Tag, **unabhaengig vom
aktuellen Kontostand**. Eine Ueberschreitung liefert 429, keine stille
Abbuchung.
"""
from __future__ import annotations

import logging
import threading
import time

import requests

from database.api_health import track_api_health

logger = logging.getLogger(__name__)

BASE_URL = "https://openrouter.ai/api/v1/chat/completions"

# Nur Modelle mit diesem Suffix kosten nichts. Siehe Modul-Docstring, Regel 1.
FREE_SUFFIX = ":free"

# Vorgabemodell fuer die Gegenpruefung. Bewusst ein grosses, offen gewichtetes
# Modell: der Gegenpruefungs-Faktensatz ist zwar schlank, aber die Frage
# ("stuetzt die Begruendung die Richtung?") verlangt echtes Schlussfolgern -
# an genau dieser Anforderung ist Groqs 8B strukturell gescheitert.
#
# ACHTUNG, WARTUNGSPUNKT: die Free-Liste auf OpenRouter rotiert ohne
# Vorwarnung. Faellt dieses Modell weg, liefert die API einen Fehler - der
# Circuit Breaker (agent/provider_sperre.py) faengt das ab, aber der Eintrag
# hier muss dann nachgezogen werden. Aktuelle Liste: openrouter.ai/models,
# Preisfilter 0. Oder direkt: GET https://openrouter.ai/api/v1/models und auf
# pricing.prompt == 0 filtern - das ist die einzige Quelle, die stimmt.
#
# GEMESSEN 07.08. an vier Kandidaten (Konsistenzfrage mit bekannter Antwort):
#   nemotron-3-ultra-550b   1.000.000 Kontext    7,6 s   JSON ok, Urteil richtig
#   nemotron-3-super-120b     262.144 Kontext   12,8 s   JSON ok, Urteil richtig
#   gpt-oss-20b               131.072 Kontext   11,2 s   JSON ok, Urteil richtig
#   gemma-4-31b               262.144 Kontext      -     429, temporaer gesperrt
#
# Der zuvor eingetragene deepseek-r1:free war aus der Free-Liste rotiert und
# lieferte 404 mit dem Hinweis auf die BEZAHLTE Variante - der :free-Schutz in
# chat() hat das abgefangen, es floss kein Geld.
# GEORDNETE MODELL-LISTE STATT EINES FESTGENAGELTEN MODELLS (2026-08-07,
# Nutzer-Idee). Der erste Eintrag wird zuerst versucht; faellt er aus, geht es
# der Reihe nach weiter.
#
# WARUM DAS NOETIG IST: die Free-Liste rotiert ohne Vorwarnung, und das ist
# nicht theoretisch - beim allerersten echten Lauf war `deepseek-r1:free`
# bereits verschwunden (404 mit Verweis auf die BEZAHLTE Variante). Mit einem
# einzelnen Modell heisst das Ausfall bis jemand von Hand nachzieht.
#
# WARUM DAS NICHT DER ALTE ABLEHNUNGSGRUND IST: Runde 4 verwarf OpenRouter u.a.
# weil "das zugrundeliegende Modell pro Call wechselt, nicht vorhersagbar".
# Das betraf OpenRouters AUTO-ROUTER. Hier ist das Gegenteil der Fall: WIR
# bestimmen die Reihenfolge, jeder Call nennt genau ein explizites Modell, und
# welches geantwortet hat, steht hinterher in der DB (siehe `letztes_modell`).
#
# Reihenfolge nach Messung vom 07.08. (Konsistenzfrage mit bekannter Antwort):
# groesster Kontext und schnellste Antwort zuerst.
FREE_MODELLE = (
    "nvidia/nemotron-3-ultra-550b-a55b:free",   # 1.000.000 Kontext,  7,6 s
    "nvidia/nemotron-3-super-120b-a12b:free",   #   262.144 Kontext, 12,8 s
    "openai/gpt-oss-20b:free",                  #   131.072 Kontext, 11,2 s
    "google/gemma-4-31b-it:free",               #   262.144 Kontext, am 07.08. 429
    "nvidia/nemotron-3-nano-30b-a3b:free",      #   256.000 Kontext, Reserve
)

# Rueckwaertskompatibel: einzelne Aufrufer und Tests nennen weiterhin ein Modell.
DEFAULT_MODEL = FREE_MODELLE[0]

# Regel 1 gilt fuer die ganze Liste, nicht nur fuer den Standardwert - ein
# vergessenes Suffix in einem Reserve-Eintrag waere sonst eine Zeitbombe, die
# erst beim Ausfall der davorstehenden Modelle zuendet.
assert all(m.endswith(":free") for m in FREE_MODELLE), (
    "Jeder Eintrag in FREE_MODELLE muss auf ':free' enden - sonst kostet der "
    "Rueckfall echtes Guthaben.")

# Free-Tier: 20 Anfragen/Minute (OpenRouter-Doku, Stand 07.08.2026). Ein
# eigener Drosselwert statt blindem Feuern - dieselbe Bauart wie bei Z.ai.
MIN_ABSTAND_SEKUNDEN = 3.0


class OpenRouterModelNichtFrei(ValueError):
    """Eine Modell-ID ohne `:free`-Suffix wuerde echtes Guthaben kosten."""


class OpenRouterClient:
    """Gleiches `.chat()`-Interface wie die uebrigen Clients (Duck-Typing) -
    `gegenpruefung.py` ruft ausschliesslich `.chat()` auf und muss deshalb
    nicht wissen, welcher Anbieter dahintersteht."""

    def __init__(self, api_key: str, session: requests.Session | None = None):
        self._api_key = api_key
        self._session = session or requests.Session()
        self._lock = threading.Lock()
        self._letzter_call = 0.0
        # Welches Modell hat zuletzt tatsaechlich geantwortet? Ohne das waere
        # die Rotation eine stille Qualitaetsaenderung: in der DB stuende ein
        # 550B-Modell, geantwortet haette vielleicht ein 20B.
        self.letztes_modell: str | None = None

    def _respect_rate_limit(self) -> None:
        with self._lock:
            wartezeit = MIN_ABSTAND_SEKUNDEN - (time.monotonic() - self._letzter_call)
            if wartezeit > 0:
                time.sleep(wartezeit)
            self._letzter_call = time.monotonic()

    @track_api_health("openrouter")
    def chat(
        self,
        messages: list[dict],
        model: str | None = None,
        temperature: float = 0.3,
        response_format: dict | None = None,
    ) -> str:
        """Ruft der Reihe nach die Modelle aus FREE_MODELLE auf, bis eines
        antwortet. Mit ausdruecklichem `model` wird NICHT rotiert - Tests und
        Vergleichslaeufe sollen genau das messen, was sie angeben.

        Das Gesundheits-Tracking (`@track_api_health`) sieht nur das Ergebnis
        der GANZEN Kette: ein Fehler wird erst vermerkt, wenn alle Modelle
        gescheitert sind. Ein einzelnes weggerotiertes Modell ist kein
        Anbieter-Ausfall und darf den Circuit Breaker nicht ausloesen.
        """
        if model is not None:
            return self._ein_call(messages, model, temperature, response_format)

        letzter_fehler: Exception | None = None
        for kandidat in FREE_MODELLE:
            try:
                antwort = self._ein_call(messages, kandidat, temperature, response_format)
                if kandidat != FREE_MODELLE[0]:
                    logger.info(
                        "OpenRouter: %s hat geantwortet (Rueckfall - %s war nicht "
                        "verfuegbar). Steht die Liste dauerhaft auf einem spaeteren "
                        "Eintrag, lohnt ein Blick auf GET /api/v1/models.",
                        kandidat, FREE_MODELLE[0],
                    )
                return antwort
            except Exception as exc:  # noqa: BLE001
                letzter_fehler = exc
                logger.info("OpenRouter: %s nicht nutzbar (%s) - naechstes Modell",
                            kandidat, str(exc)[:120])
        raise RuntimeError(
            f"Kein Modell aus FREE_MODELLE hat geantwortet ({len(FREE_MODELLE)} "
            f"versucht). Letzter Fehler: {letzter_fehler}"
        ) from letzter_fehler

    def _ein_call(
        self,
        messages: list[dict],
        model: str,
        temperature: float,
        response_format: dict | None,
    ) -> str:
        # REGEL 1 aus dem Modul-Docstring, hier durchgesetzt statt vorausgesetzt.
        # Ein Tippfehler in einer Modell-ID waere sonst eine stille Abbuchung.
        if not model.endswith(FREE_SUFFIX):
            raise OpenRouterModelNichtFrei(
                f"Modell '{model}' hat kein '{FREE_SUFFIX}'-Suffix und wuerde echtes "
                f"Guthaben kosten. Dieser Client ist ausschliesslich fuer die "
                f"kostenlosen Varianten gedacht (siehe Modul-Docstring)."
            )
        self._respect_rate_limit()
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            # OpenRouter bittet um diese beiden Felder zur Zuordnung; sie sind
            # optional, aber ohne sie landen Anfragen in einem anonymen Topf.
            "HTTP-Referer": "https://github.com/gitgeatsch/TradingInfoTool",
            "X-Title": "TradingInfoTool",
        }
        # REGEL 2: genau EIN Modell, kein `models`-Array, kein `route`-Feld -
        # beides koennte auf einer bezahlten Variante landen.
        payload = {"model": model, "messages": messages, "temperature": temperature}
        if response_format is not None:
            payload["response_format"] = response_format
        response = self._session.post(BASE_URL, json=payload, headers=headers, timeout=90)
        response.raise_for_status()
        daten = response.json()
        self.letztes_modell = model
        return daten["choices"][0]["message"]["content"]
