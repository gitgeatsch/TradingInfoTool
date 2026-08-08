"""OpenRouter-Client, ausschliesslich fuer die Gegenpruefung (2026-08-07).

WARUM DIESER ANBIETER UEBERHAUPT. Mistral hat am 07.08. alle Modelle
kostenpflichtig gestellt (Free-Plan: 10 $ Monatsbudget, kontoweit ueber Studio/
Vibe Code/API geteilt, Reset in 24 Tagen). Danach trug **Gemini allein** alle
142 Signale des Tages - ein Ein-Anbieter-Risiko. Die Suche nach einem zweiten
freien Anbieter (Runde 5, siehe Regelwerk-Entscheidungslog) ergab: der
Ausschlussgrund ist unser EIGENER System-Prompt mit ~9.100 Token, nicht das
Tagesvolumen. Cerebras und Z.ai haetten je 1 Mio. Token/Tag, scheitern aber an
8K Kontext. Groq hat 100K Token/TAG - acht Analysen.

WARUM NUR FUER DIE GEGENPRUEFUNG. **Der Grund hat sich am 08.08. geaendert -
wer hier nachliest, muss den neuen kennen, nicht den alten.**

Der urspruengliche Grund war Datenschutz: die meisten freien Endpunkte
verlangten aktiviertes Logging/Training, und unser SYSTEM_PROMPT ist das
inhaltliche Herzstueck des Projekts. **Dieser Grund ist entfallen.** Der Nutzer
hat am 07.08. alle vier Data-Training-Schalter im OpenRouter-Konto
ausgeschaltet; was danach noch antwortet, bekommt unsere Prompts nicht als
Trainingsmaterial. Der Zielkonflikt ist aufgeloest, nicht abgemildert.

Der Grund ist jetzt KAPAZITAET, und er ist gemessen statt vermutet. Haertetest
am 08.08. mit dem echten Hebel-SYSTEM_PROMPT plus einem echten Faktensatz aus
dem Notebook-Export (16.656 Eingabe-Token), 10 Faelle, geprueft gegen die
echte `_validate_hebel()`:

    openai/gpt-oss-20b:free   5 von 10 gueltig, Median 124,9 s, 1,80 Versuche/Fall
                              Fehlschlaege: 4x HTTP 429, 1x erfundene Kategorie
    google/gemma-4-26b:free   0 von  5 gueltig - Upstream-Timeouts nach ~24 s
    Gemini (Referenz)         5 von  5 gueltig, Median 5,5 s, 1,00 Versuche/Fall

Faktor ~23 in der Zeit bei 50 % Ausfall. Die Gegenpruefung dagegen sendet einen
System-Prompt von ~365 Token - **Faktor 35 kleiner als die Signal-Kette**, und
GENAU das ist der Unterschied zwischen "traegt" und "traegt nicht". Der freie
Pool ist fuer kleine Anfragen brauchbar und fuer grosse nicht.

**Wer diesen Client in die Haupt-Signalkette haengt, muss deshalb nicht mehr
den Datenschutz begruenden, sondern die Kapazitaet** - und dafuer gibt es
Messwerte, die dagegen sprechen. Neue Messung schlaegt alte; aber ohne neue
Messung bleibt es dabei.

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

import requests

from api.llm_basis import Mindestabstand, extrahiere_inhalt, zaehle_aufruf
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
# Reihenfolge nach der Messung vom 07.08. spaet - NUR Modelle, die OHNE
# Trainings-Freigabe antworten. Der Nutzer hat alle vier Data-Training-Schalter
# im OpenRouter-Konto ausgeschaltet; damit wird der SYSTEM_PROMPT (~9.100 Token
# Regelwerk) NICHT zu Trainingsmaterial - der Zielkonflikt vom Nachmittag ist
# damit aufgeloest, nicht nur abgemildert.
#
# GEMESSEN an allen 14 Katalog-Eintraegen mit den Schaltern AUS:
#   erreichbar : gemma-4-26b (5,2 s), north-mini-code (5,6 s), gpt-oss-20b (12,7 s)
#   gedrosselt : gemma-4-31b, ling-3.0-tiny  -> 429, NICHT policy-gesperrt
#   gesperrt   : 9 weitere -> 404 "No endpoints available matching your
#                guardrail restrictions and data policy"
#
# Die 429er stehen bewusst MIT in der Liste: sie sind nicht verboten, nur gerade
# ausgelastet - genau der Fall, fuer den die Rotation da ist.
#
# cohere/north-mini-code:free ist erreichbar, bleibt aber DRAUSSEN: Cohere wurde
# in Runde 4 verworfen, weil die Trial-Bedingungen Produktivnutzung ausdruecklich
# verbieten. Ob das ueber OpenRouter anders ist, waere zu pruefen - solange das
# offen ist, nicht benutzen (Nutzer-Entscheidung 07.08.).
#
# DER PREIS, offen benannt: statt 14 Modellen bleiben 4. Ausfaelle werden
# haeufiger, und die 429er zeigen, dass trainingsfreie Endpunkte staerker
# umkaempft sind. Ohne die Rotation waere dieser Pool fahrlaessig; mit ihr ist
# er handhabbar. Faellt alles aus, uebernimmt Z.ai die Gegenpruefung.
#
# NACHTRAG 2026-08-08, GEMESSEN: `inclusionai/ling-3.0-tiny:free` ist wieder
# RAUS. Es war am 07.08. nur wegen eines 429 aufgenommen worden - also unter
# der Annahme, es sei bloss ausgelastet. Der direkte Test zeigt etwas anderes:
#
#     ling-3.0-tiny  MIT response_format -> HTTP 400 INVALID_REQUEST
#     ling-3.0-tiny  OHNE                -> HTTP 200, gueltiges JSON
#
# `response_format={"type":"json_object"}` ist fuer die Gegenpruefung PFLICHT
# (so ausdruecklich in agent/krypto/gegenpruefung.py). Der Eintrag waere also
# nicht "manchmal langsam", sondern bei JEDEM Aufruf ein harter Fehlschlag -
# und zwar erst sichtbar geworden, wenn `openrouter_aktiv` auf true geht.
# Lehre: ein 429 sagt nichts darueber, ob das Modell den Vertrag erfuellt. Fuer
# die Aufnahme in diese Liste zaehlt nur ein Aufruf MIT den Parametern, die wir
# tatsaechlich senden.
#
# `gemma-4-31b` bleibt drin, ist aber UNGEPRUEFT: am 08.08. in beiden Varianten
# 429 ("temporarily rate-limited"), also gedrosselt und nicht abweisend. Faellt
# es beim ersten echten Einsatz mit 400 aus, gehoert es aus demselben Grund
# heraus wie ling.
#
# ENDSTAND 2026-08-09 nach Screening (13 Modelle), Haertetests und dem
# historischen Ruecktest gegen 38 Mistral-Entscheidungen mit bekanntem Ausgang.
# Sortiert nach AEHNLICHKEIT ZU GEMINI, nicht nach Bestenliste - ein Rueckfall
# soll sich verhalten wie das System, das validiert wurde:
#
#                            gueltig   Median   Konfidenz    Richtung   Uebereinst.
#   nemotron-3-super-120b    16/20     20,8 s   Median 65 %  14L/12S    77 % Richtung
#   gpt-oss-20b               5/10    124,9 s   55-70 %      -          -
#   gemma-4-31b                 -         -     -            -          -
#   (Gemini als Referenz)      5/5      5,5 s   Median 65 %  16L/10S    -
#
# RAUS, obwohl es die BESTE R-Zahl hatte: `poolside/laguna-xs-2.1:free`
# (-8,00 R gegen Mistrals -22,82 R auf derselben Menge). Der Grund steht in
# den Verhaltenszahlen, nicht im Ergebnis:
#   * 24 von 26 Entscheidungen LONG - es differenziert die Richtung praktisch
#     nicht (Gemini 16/10, nemotron 14/12)
#   * Konfidenz-Median 42,5 % gegen Geminis 65,0 % - 22,5 Punkte tiefer, und
#     die Pipeline hat eine scharfe Mindestkonfidenz. Der Rueckfall waere
#     anders GEFILTERT, nicht nur langsamer.
#   * nur 46 % Aktions-Uebereinstimmung mit Gemini
# Seine gute R-Zahl kam aus 69 % Ablehnung, nicht aus Auswahl: 0 von 8
# genommenen Faellen war ein Gewinner.
#
# RAUS: `google/gemma-4-26b-a4b-it:free` - 0/5 und 1/3 am echten Signal-Prompt,
# Upstream-Timeouts nach ~24 s (Darkbloom-Endpunkt).
#
# NICHT belegt und deshalb nicht behauptet: dass nemotron BESSER urteilt. Auf
# den 26 gemeinsamen Faellen wies KEIN Modell eine bessere Trefferquote als die
# Basislinie auf - bei einem einzigen Gewinner hatte der Test dafuer aber auch
# keine Kraft.
FREE_MODELLE = (
    "nvidia/nemotron-3-super-120b-a12b:free",  # 262.144 Kontext, Nvidia-Endpunkt
                                        #   99 % Uptime, structured_outputs
    "openai/gpt-oss-20b:free",          # 131.072 Kontext - trug den vollen
                                        #   Prompt, aber langsam und 5/10
    "google/gemma-4-31b-it:free",       # Google AI Studio, 100 % Uptime, aber
                                        #   am 07. UND 08.08. durchgehend 429 -
                                        #   UNGEPRUEFT, reine Reserve
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

# REASONING ABSCHALTEN (2026-08-08). Mehrere der freien Modelle sind
# Reasoning-Modelle und denken ohne Vorgabe lang. GEMESSEN an EINEM echten
# Hebel-Faktensatz (16.656 Eingabe-Token), dreimal dasselbe Modell
# `openai/gpt-oss-20b:free`, nur dieser Regler verstellt:
#
#     nichts gesetzt        398,9 s   5.929 Ausgabe-Token, davon 5.089 Reasoning
#     reasoning.effort=low  117,4 s   1.678 Ausgabe-Token, davon   879 Reasoning
#     reasoning.exclude     44,5 s     710 Ausgabe-Token, davon    20 Reasoning
#
# **86 % der Wartezeit war verstecktes Nachdenken, das niemand angefordert
# hat.** Wer das nicht setzt, misst den eigenen Konfigurationsfehler und haelt
# ihn fuer eine Anbieter-Eigenschaft - genau das war der erste Befund dieses
# Haertetests (488 s je Signal), und er war falsch.
#
# Warum ABSCHALTEN und nicht `effort=low`: unsere Prompts verlangen die
# Herleitung im ANTWORT-JSON (`gegenargument`, `eigene_einschaetzung.
# kurzfazit`) - dort ist sie pruefbar und wird gespeichert. Verstecktes
# Reasoning landet nirgends und kostet trotzdem Zeit und Kontingent.
STANDARD_REASONING = {"exclude": True, "effort": "low"}


class OpenRouterModelNichtFrei(ValueError):
    """Eine Modell-ID ohne `:free`-Suffix wuerde echtes Guthaben kosten."""


class OpenRouterClient:
    """Gleiches `.chat()`-Interface wie die uebrigen Clients (Duck-Typing) -
    `gegenpruefung.py` ruft ausschliesslich `.chat()` auf und muss deshalb
    nicht wissen, welcher Anbieter dahintersteht."""

    def __init__(self, api_key: str, session: requests.Session | None = None):
        self._api_key = api_key
        self._session = session or requests.Session()
        # Seit 2026-08-09 aus api/llm_basis.py statt eigener Fassung - die
        # ANDERE Drossel-Achse als bei den uebrigen Clients (Abstand zwischen
        # zwei Aufrufen statt Volumen je Minute), deshalb Mindestabstand und
        # nicht Minutenfenster. Beide stehen dort nebeneinander, damit niemand
        # versehentlich die falsche kopiert.
        self._drossel = Mindestabstand(MIN_ABSTAND_SEKUNDEN)
        # Welches Modell hat zuletzt tatsaechlich geantwortet? Ohne das waere
        # die Rotation eine stille Qualitaetsaenderung: in der DB stuende ein
        # 550B-Modell, geantwortet haette vielleicht ein 20B.
        self.letztes_modell: str | None = None

    def _respect_rate_limit(self) -> None:
        self._drossel.warte_auf_slot()

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
        # HIER, nicht in chat(): eine Rotation ueber drei Modelle sind drei
        # HTTP-Aufrufe und zaehlen dreimal gegen OpenRouters Tageslimit von
        # 1.000 Anfragen. Am chat()-Eingang gezaehlt waere das EIN Aufruf -
        # der Zaehler laege genau dann zu niedrig, wenn es eng wird.
        zaehle_aufruf("openrouter")
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            # OpenRouter bittet um diese beiden Felder zur Zuordnung; sie sind
            # optional, aber ohne sie landen Anfragen in einem anonymen Topf.
            "HTTP-Referer": "https://github.com/gitgeatsch/TradingInfoTool",
            "X-Title": "TradingInfoTool",
        }
        # REGEL 2: genau EIN Modell, kein `models`-Array, kein `route`-Feld -
        # beides koennte auf einer bezahlten Variante landen.
        payload = {"model": model, "messages": messages, "temperature": temperature,
                   "reasoning": STANDARD_REASONING}
        if response_format is not None:
            payload["response_format"] = response_format
        response = self._session.post(BASE_URL, json=payload, headers=headers, timeout=90)
        response.raise_for_status()
        daten = response.json()
        # Der Guard steht seit 2026-08-09 in api/llm_basis.py und gilt fuer
        # ALLE fuenf Clients - er war hier zuerst eingebaut worden und fehlte
        # in den anderen vier. Der Modellname geht mit in die Meldung, weil bei
        # der Rotation sonst unklar bliebe, welcher Eintrag ausgefallen ist.
        inhalt = extrahiere_inhalt(daten, f"OpenRouter/{model}")
        self.letztes_modell = model
        return inhalt
