"""Z.ai (Zhipu AI) API Anbindung - vierter Kandidat (2026-07-20, siehe Memory
reference_llm_provider_recherche_uebersicht.md und
project_groq_alternative_recherche_2026-07-20.md). Zunaechst testweise VOR
Mistral gehaengt, nach der ersten echten Testnacht (2/2 Timeouts) aber wieder
auf die LETZTE Fallback-Stufe (nach Gemini) zurueckgestuft - siehe
REQUEST_TIMEOUT_SECONDS-Docstring unten fuer den Grund. Anders als bei Mistral/
Gemini/Groq ist die reale Kapazitaet NICHT ueber ein Nutzer-Dashboard verifiziert
- Z.ai veroeffentlicht fuer die kostenlosen Modelle nur ein "Concurrency limit"
(GLM-4.5-Flash=2, GLM-4.7-Flash=1), keine RPM/TPM/RPD-Zahl. Nutzer-Entscheidung:
bewusst KEINE konservative Drosselung im Client (anders als Mistral/Gemini) -
"kein Grund nicht auf ein bestimmtes hoeheres Limit zu gehen, wenn diese Quelle
blockiert wird passiert auch nichts fuer diese eine Nacht". Reale Kapazitaet
zeigt sich ueber echte 429-Fehler in api_health (gleiches Prinzip wie Groq).

Vertragsbedingungen laut offizieller Datenschutzerklaerung
(docs.z.ai/legal-agreement/privacy-policy) fuer API-Kunden gut: keine
Speicherung der Anfrage-/Antwortinhalte (nur Echtzeit-Verarbeitung), keine
Trainings-Nutzung. Verarbeitung laut Policy in Singapur.

DEFAULT_MODEL = "glm-4.5-flash" - eines der beiden dauerhaft kostenlosen
Modelle (GLM-4.5-Flash/GLM-4.7-Flash, laut offizieller Pricing-Seite als
"Free" statt nur "Limited-time Free" gelistet), Concurrency-Limit 2 (etwas
hoeher als GLM-4.7-Flashs 1) - Modellqualitaet ist ohnehin zweitrangig,
risk_gate.py::post_check() validiert jede Empfehlung unabhaengig vom
LLM-Anbieter deterministisch nach (P-7).

OpenAI-kompatible API wie Groq/Mistral/Gemini, identisches `.chat()`-
Interface.

Nachtrag (2026-07-28, echter Notebook-Fund - siehe Regelwerksmanual): die
urspruengliche "keine Drosselung"-Entscheidung oben war fuer Hebel-only-
Volumen kalibriert. Seit der Ausweitung der Z.ai-Gegenpruefung auf alle 6
Signal-Pipelines (Commit 17b1c9b, 2026-07-27, je 2 sequenzielle Calls pro
Signal ueber mehrere gleichzeitig laufende Batches) wurde das dokumentierte
Concurrency-Limit (GLM-4.5-Flash=2) chronisch ueberschritten - echter
Notebook-Export zeigte 210 Z.ai-Log-Zeilen in einem Fenster, praktisch alle
"429 Too Many Requests". Ergebnis: Z.ai-Infos fehlten in nahezu allen
Signal-E-Mails (Hebel UND Spot), weil die Calls schlicht fehlschlugen statt
nur langsamer zu sein. Deshalb jetzt EIN echter Concurrency-Gate
(MAX_CONCURRENT_REQUESTS unten) plus ein begrenzter 429-Retry - die
RATE_LIMIT_PER_MINUTE-Drosselung (Gesamtvolumen/Minute) bleibt davon
unberuehrt, das ist eine andere Achse (Gesamtdurchsatz vs. Gleichzeitigkeit)."""
from __future__ import annotations

import logging
import threading
import time
from collections import deque

import requests

from database.api_health import track_api_health

logger = logging.getLogger(__name__)

BASE_URL = "https://api.z.ai/api/paas/v4/chat/completions"
DEFAULT_MODEL = "glm-4.5-flash"
# Bewusst KEINE Volumen-Drosselung ueber RATE_LIMIT_PER_MINUTE hinaus
# (Nutzer-Vorgabe 2026-07-20, siehe Modul-Docstring) - nur ein grosszuegiger
# Sicherheitsnetz-Wert gegen einen etwaigen Endlosschleifen-Bug, keine
# Kapazitaetsschaetzung. Die reale Obergrenze ist unbekannt und soll sich im
# echten Betrieb zeigen.
RATE_LIMIT_PER_MINUTE = 120
# Gleichzeitigkeits-Bremse (2026-07-28, Nachtrag oben) - GEGENSATZ zu
# RATE_LIMIT_PER_MINUTE: begrenzt nicht das Gesamtvolumen, sondern wie viele
# Requests zeitgleich unterwegs sein duerfen. Deckt sich mit Z.ais eigener
# Doku fuer GLM-4.5-Flash ("Concurrency limit: 2") - alles darueber wird vom
# Server ohnehin per 429 abgewiesen, ein Client-seitiges Warten auf einen
# freien Slot ist strikt besser als ein sofortiger, garantierter Fehlschlag.
MAX_CONCURRENT_REQUESTS = 2
# 429-Retry (2026-07-28) - Ergaenzung zum Concurrency-Gate: selbst mit
# eigener Drosselung kann ein 429 vorkommen (z.B. kurzzeitig hoehere externe
# Last bei Z.ai selbst). 2 zusaetzliche Versuche mit steigender Wartezeit,
# `Retry-After`-Header wird respektiert falls vorhanden. Andere Fehler
# (Timeout, 5xx, Verbindungsfehler) werden NICHT wiederholt - das bleibt wie
# bisher P-8 (kein Hard-Fail, Aufrufer faengt die Exception ab).
RETRY_ON_429_MAX_VERSUCHE = 2
RETRY_ON_429_BASIS_WARTEZEIT_SEKUNDEN = 5.0
# REQUEST_TIMEOUT_SECONDS (2026-07-20, Nachbesserung nach der ersten echten
# Testnacht): urspruenglich 60s, aber reproduzierte Live-Tests (Desktop +
# Notebook) zeigten, dass glm-4.5-flash bei realistischer Payload-Groesse
# (System-Prompt + Fakten-JSON wie in der echten Pipeline) ca. 109s fuer
# eine vollstaendige, valide Antwort braucht - 60s war also strukturell zu
# knapp, nicht nur ein Ausreisser. glm-4.7-flash schaffte es auch mit 150s
# nicht (verworfen). Da Zai jetzt als letzte Fallback-Stufe (nach Gemini)
# haengt statt an erster Stelle, faellt die zusaetzliche Wartezeit kaum
# noch ins Gewicht - 150s geben glm-4.5-flash realistisch eine echte Chance.
REQUEST_TIMEOUT_SECONDS = 150


class ZaiClient:
    def __init__(self, api_key: str, session: requests.Session | None = None):
        self._api_key = api_key
        self._session = session or requests.Session()
        self._call_timestamps_minute: deque[float] = deque()
        # Gleichzeitigkeits-Gate (siehe MAX_CONCURRENT_REQUESTS-Docstring oben) -
        # EIN Semaphore pro Client-Instanz, und main.py erstellt genau EINE
        # ZaiClient-Instanz fuer den ganzen Prozess (siehe main.py), die an alle
        # 6 Pipelines durchgereicht wird - das Semaphore wirkt also global ueber
        # alle gleichzeitig laufenden Hintergrund-Threads hinweg, nicht nur
        # innerhalb einer einzelnen Pipeline.
        self._concurrency_semaphore = threading.Semaphore(MAX_CONCURRENT_REQUESTS)

    def _respect_rate_limit(self) -> None:
        now = time.monotonic()
        while self._call_timestamps_minute and now - self._call_timestamps_minute[0] > 60:
            self._call_timestamps_minute.popleft()
        if len(self._call_timestamps_minute) >= RATE_LIMIT_PER_MINUTE:
            sleep_for = 60 - (now - self._call_timestamps_minute[0])
            if sleep_for > 0:
                time.sleep(sleep_for)
        self._call_timestamps_minute.append(time.monotonic())

    @track_api_health("zai")
    def chat(
        self,
        messages: list[dict],
        model: str = DEFAULT_MODEL,
        temperature: float = 0.3,
        response_format: dict | None = None,
    ) -> str:
        self._respect_rate_limit()
        headers = {"Authorization": f"Bearer {self._api_key}"}
        payload = {"model": model, "messages": messages, "temperature": temperature}
        if response_format is not None:
            payload["response_format"] = response_format
        # Wartet auf einen freien Slot statt sofort zu feuern (siehe
        # MAX_CONCURRENT_REQUESTS-Docstring) - blockiert den aufrufenden
        # Hintergrund-Thread, was hier gewuenscht ist (kein zusaetzlicher
        # Call soll gestartet werden, waehrend schon 2 unterwegs sind).
        with self._concurrency_semaphore:
            versuch = 0
            while True:
                response = self._session.post(
                    BASE_URL, json=payload, headers=headers, timeout=REQUEST_TIMEOUT_SECONDS
                )
                if response.status_code == 429 and versuch < RETRY_ON_429_MAX_VERSUCHE:
                    versuch += 1
                    wartezeit = RETRY_ON_429_BASIS_WARTEZEIT_SEKUNDEN * versuch
                    retry_after = response.headers.get("Retry-After")
                    if retry_after is not None:
                        try:
                            wartezeit = max(wartezeit, float(retry_after))
                        except ValueError:
                            pass
                    logger.info(
                        "Z.ai 429 (Versuch %s/%s) - warte %.1fs vor erneutem Versuch",
                        versuch, RETRY_ON_429_MAX_VERSUCHE, wartezeit,
                    )
                    time.sleep(wartezeit)
                    continue
                break
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]
