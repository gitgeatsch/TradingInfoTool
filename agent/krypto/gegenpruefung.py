# -*- coding: utf-8 -*-
"""Z.ai-Gegenpruefungslogik (2026-07-26, Nutzer-Idee: Z.ai aus der
automatischen Fallback-Kette loesen und stattdessen fuer eine kleine,
dedizierte Konsistenzpruefung nutzen - siehe agent/krypto/budget_allocator.py
Modul-Docstring fuer die Fallback-Kette-Aenderung).

Zwei unabhaengige Pruefungen, ZWEI getrennte Z.ai-Calls (siehe Nachtrag
2026-07-26 unten fuer die Begruendung, warum nicht EIN kombinierter Call):

1. **Konsistenz-Check** (`pruefe_konsistenz()`, urspruengliches Feature):
   prueft NICHT, ob die Handelsentscheidung selbst richtig ist (das waere
   eine zweite, primitivere Bewertung und wuerde die eigentliche
   Primaer-Analyse unterlaufen, siehe [[feedback_llm_synthese_kein_deterministischer_override]])
   - sondern nur, ob die vom Primaer-Modell selbst gegebene Kurzbegruendung
   (`short_reasoning`) den harten, deterministisch berechneten Fakten
   WIDERSPRICHT. Eine reine Python-Regel koennte das nicht leisten (Freitext-
   gegen-Zahlen-Konsistenz ist keine Schwellenwert-Frage) - das ist die
   tatsaechliche, einzigartige LLM-Faehigkeit, die hier genutzt wird.

2. **Unabhaengiger Richtungs-Abgleich** (`leite_eigene_richtung()`, Nachtrag
   2026-07-26, gleicher Tag): Nutzer-Wunsch nach einer echten JA/NEIN-Aussage,
   ob Z.ai bei denselben Fakten selbststaendig zum gleichen Ergebnis (Richtung)
   kommt wie das Primaer-Modell. KRITISCH fuer die Kalibrierung: Z.ai bekommt
   hierfuer explizit NICHT dieselbe `fakten`-Struktur wie der Konsistenz-Check
   (die `richtung`/`action`/`confidence_pct` bereits als "Fakt" enthaelt) -
   das waere ein Echo-Effekt/Anker (Z.ai wuerde die vorgegebene Richtung
   quasi nur bestaetigen, weil sie ihm als gegeben praesentiert wird, statt
   sie unabhaengig herzuleiten). Stattdessen bekommt `leite_eigene_richtung()`
   nur `baue_objektive_fakten()` (KEINE richtung/action/confidence_pct) und
   leitet daraus selbst LONG/SHORT/NEUTRAL ab. `uebereinstimmung` wird
   anschliessend deterministisch in Python verglichen (nicht vom Modell
   selbst geurteilt) - robuster, kein zusaetzliches Bias-Risiko durch eine
   dritte Modell-Frage.

   Live-Kalibrierung (2026-07-26): bei eindeutigen Fakten (rein bullisch/rein
   baerisch, keine Gegenindikatoren) liefert Z.ai stabile, korrekte Urteile.
   Bei GRENZWERTIGEN Fakten (z.B. durchgehend baerischer Trend, aber
   ueberverkaufter RSI als Gegenindikator) zeigte ein Wiederholungstest
   echte Uneinheitlichkeit (5/6 SHORT bei temperature=0.2, 4/6 SHORT bei
   temperature=0.0 - die Streuung liegt NICHT an der Temperatur, sondern an
   echter Modell-Unschluessigkeit beim Abwaegen widerspruechlicher Signale).
   Nutzer-Entscheidung nach Vorlage dieses Befunds: Rauschen akzeptieren,
   kein Prompt-Tuning (Risiko eines neuen Anker-Bugs, siehe [[project_konfidenz_prompt_anker_fix]]),
   NEUTRAL zaehlt wie jede andere Nicht-Uebereinstimmung als "nein" - Phase 1
   ist ohnehin rein beobachtend, das Rauschen selbst ist Teil dessen, was
   ueber Zeit beobachtet werden soll.

Live kalibriert (2026-07-26, drei Bias-Testreihen gegen die echte Z.ai-API,
nicht nur angenommen):
1. `response_format={"type": "json_object"}` ist PFLICHT - ohne dieses Feld
   verpackt Z.ai seine Antwort manchmal in Markdown-Codefences statt reinem
   JSON (ein direkter Parse-Fehler in einem von drei Testlaeufen ohne dieses
   Feld, danach 3/3 sauber MIT dem Feld).
2. Sykophantie-/Ueberzeugungs-Bias getestet: ein bewusst UEBERZEUGEND
   formulierter, aber inhaltlich falscher Begruendungstext wurde trotzdem
   korrekt als Widerspruch erkannt - der selbstsichere TON hat das Modell
   nicht getaeuscht.
3. Fehlender-Kontext-Fehlalarm getestet: ein Begruendungstext, der sich auf
   Informationen AUSSERHALB der gegebenen Fakten bezieht (z.B. Nachrichten),
   wurde korrekt NICHT als Widerspruch gewertet.
4. Antizyklik-Vertraeglichkeit getestet: ein Begruendungstext, der die
   gegenlaeufigen Fakten OFFEN benennt und bewusst dagegen argumentiert
   (das Kernprinzip der Antizyklisch-Regeln dieses Projekts), wurde korrekt
   als konsistent gewertet, nicht bestraft.
5. Explizit KEINE Persona-/"sei-kontraer"-Rahmung verwendet - eine Test-
   Variante mit einer "Risikomanager"-Rolle zeigte keinen Erkennungsvorteil
   gegenueber der neutralen Formulierung (die neutrale Variante erkannte
   Selbstueberschaetzung bereits zuverlaessig, weil `confidence_pct` selbst
   Teil der gegebenen Fakten ist) - eine explizite "sei skeptisch"-Anweisung
   haette dagegen das Risiko eines Widerspruchs-Bias eingefuehrt (Spiegelbild
   des Sykophantie-Problems, das Punkt 2 gerade erst ausschliesst).
Kein im Prompt eingebettetes Beispiel (anders als der fruehere Regel-22/13-
Anker-Bug in hebel_analyst.py/analyst.py, der genau daran scheiterte - ein
einzelnes Beispiel wurde vom Modell staerker gewichtet als die eigentliche
Regel, siehe [[project_konfidenz_prompt_anker_fix]]).

Phase 1 (aktueller Stand): REIN BEOBACHTEND. `urteil`/`kurzbegruendung`
werden gespeichert, aber NICHT als Risikofaktor angezeigt, NICHT als Gate
verwendet und beeinflussen `action`/`richtung`/`confidence_pct` in keiner
Weise. Ob ein Gate jemals sinnvoll waere, haengt davon ab, ob sich diese
Gegenpruefung ueber Zeit als tatsaechlich treffsicher erweist (Nutzer-
Position 2026-07-26: "eher zu bezweifeln, es sei denn die Gegenpruefung ist
so erfolgreich, dass dies tatsaechlich als Modell dienen kann").

Scope v1: nur Hebel (siehe budget_allocator.py-Docstring)."""
from __future__ import annotations

import json
import logging

logger = logging.getLogger(__name__)

_JSON_OBJECT_FORMAT = {"type": "json_object"}

SYSTEM_PROMPT = (
    "Du bekommst harte Marktfakten zu einem Krypto-Hebel-Signal UND einen kurzen Begruendungstext, "
    "der fuer eine Handelsentscheidung vorgebracht wurde. Deine einzige Aufgabe: pruefe, ob der "
    "Begruendungstext den gegebenen Fakten WIDERSPRICHT - unabhaengig davon, wie ueberzeugend der "
    "Text klingt. Die Fakten sind die einzige Wahrheitsquelle, der Text ist nur eine zu pruefende "
    "Behauptung. Bezieht sich der Text auf etwas, das nicht in den Fakten steht, ist das KEIN "
    "Widerspruch (dir fehlt nur Kontext). Erfinde NIEMALS eigene Fakten. "
    "WICHTIG zur Bedeutung von `richtung`/`action`: NUR wenn `action` TEILVERKAUF, SCHLIESSEN oder "
    "HEBEL_SENKEN ist, beschreibt `richtung` die BESTEHENDE Position, die reduziert/geschlossen wird "
    "- NICHT eine neue Kaufempfehlung. Ein Begruendungstext, der in GENAU DIESEM Fall (also nur bei "
    "diesen drei Aktionen) GEGEN diese Richtung argumentiert (z.B. baerische Gruende bei richtung "
    "LONG), ist die ERWARTETE, korrekte Rechtfertigung fuer den Abbau - das ist dann KONSISTENT, kein "
    "Widerspruch. Bei ALLEN anderen Aktionen (insbesondere HALTEN, ERÖFFNEN, NACHKAUFEN, "
    "HEBEL_ERHÖHEN) beschreibt `richtung` weiterhin die eigentliche Markteinschaetzung - dort muss "
    "der Text diese Richtung normal stuetzen, ein dagegen argumentierender Text ist dort ein "
    "echter Widerspruch, genau wie ohne diesen Hinweis. Antworte AUSSCHLIESSLICH "
    "mit JSON, exakt diese zwei Felder: "
    '{"urteil": "konsistent" oder "widerspruch", "kurzbegruendung": "<= 12 Woerter"}.'
)

_GUELTIGE_URTEILE = {"konsistent", "widerspruch"}


def _funding_rate_vorzeichen_text(funding_rate_stunde: float | None) -> str | None:
    if funding_rate_stunde is None:
        return None
    if funding_rate_stunde > 0:
        return f"positiv {funding_rate_stunde:.4f}%/h (Longs zahlen Shorts)"
    if funding_rate_stunde < 0:
        return f"negativ {funding_rate_stunde:.4f}%/h (Shorts zahlen Longs)"
    return "neutral (0%/h)"


def baue_fakten(
    symbol: str,
    richtung: str,
    action: str,
    confidence_pct: float | None,
    rsi: float | None,
    trend_label: str | None,
    regime: str | None,
    funding_rate_stunde: float | None,
    confluence_bullish: int,
    confluence_bearish: int,
    confluence_neutral: int,
    optionsmarkt_skew: float | None,
) -> dict:
    """Bewusst schmale Faktenmenge (siehe Modul-Docstring) - live verifiziert,
    dass eine reichere Menge (inkl. Optionsmarkt-Skew) KEINE zusaetzliche
    Antwortzeit kostet gegenueber einer minimalen Menge (12-16s in beiden
    Faellen), also keine Notwendigkeit, hier weiter zu kuerzen."""
    fakten = {
        "symbol": symbol, "richtung": richtung, "action": action,
        "confidence_pct": confidence_pct,
    }
    if rsi is not None:
        fakten["rsi"] = round(rsi, 1)
    if trend_label:
        fakten["trend"] = trend_label
    if regime:
        fakten["regime"] = regime
    funding_text = _funding_rate_vorzeichen_text(funding_rate_stunde)
    if funding_text:
        fakten["funding_rate_vorzeichen"] = funding_text
    gesamt = confluence_bullish + confluence_bearish + confluence_neutral
    if gesamt > 0:
        fakten["technische_konfluenz"] = (
            f"{confluence_bullish} bullisch / {confluence_bearish} baerisch / "
            f"{confluence_neutral} neutral von {gesamt}"
        )
    if optionsmarkt_skew is not None:
        fakten["optionsmarkt_skew"] = optionsmarkt_skew
    return fakten


def baue_objektive_fakten(
    symbol: str,
    rsi: float | None,
    trend_label: str | None,
    regime: str | None,
    funding_rate_stunde: float | None,
    confluence_bullish: int,
    confluence_bearish: int,
    confluence_neutral: int,
    optionsmarkt_skew: float | None,
) -> dict:
    """Wie baue_fakten(), aber BEWUSST OHNE richtung/action/confidence_pct -
    siehe Modul-Docstring Punkt 2 (Echo-/Anker-Vermeidung fuer
    leite_eigene_richtung()). Nur fuer den unabhaengigen Richtungs-Abgleich
    verwenden, NICHT fuer pruefe_konsistenz() (die braucht richtung/action
    als Vergleichsbasis fuer den Begruendungstext)."""
    fakten = {"symbol": symbol}
    if rsi is not None:
        fakten["rsi"] = round(rsi, 1)
    if trend_label:
        fakten["trend"] = trend_label
    if regime:
        fakten["regime"] = regime
    funding_text = _funding_rate_vorzeichen_text(funding_rate_stunde)
    if funding_text:
        fakten["funding_rate_vorzeichen"] = funding_text
    gesamt = confluence_bullish + confluence_bearish + confluence_neutral
    if gesamt > 0:
        fakten["technische_konfluenz"] = (
            f"{confluence_bullish} bullisch / {confluence_bearish} baerisch / "
            f"{confluence_neutral} neutral von {gesamt}"
        )
    if optionsmarkt_skew is not None:
        fakten["optionsmarkt_skew"] = optionsmarkt_skew
    return fakten


SYSTEM_PROMPT_RICHTUNG = (
    "Du bekommst ausschliesslich objektive Marktfakten zu einem Krypto-Hebel-Kandidaten "
    "(technische Indikatoren, Marktregime, Funding-Rate, Optionsmarkt-Daten). Du kennst KEINE "
    "Handelsempfehlung eines anderen Modells. Deine Aufgabe: leite ALLEIN aus diesen Fakten deine "
    "eigene Markteinschaetzung ab - LONG (bullisch), SHORT (baerisch) oder NEUTRAL (keine klare "
    "Tendenz erkennbar). Erfinde NIEMALS eigene Fakten, nutze nur die gegebenen Werte. Antworte "
    "AUSSCHLIESSLICH mit JSON, exakt diese zwei Felder: "
    '{"eigene_richtung": "LONG" oder "SHORT" oder "NEUTRAL", "kurzbegruendung": "<= 12 Woerter"}.'
)

_GUELTIGE_RICHTUNGEN = {"LONG", "SHORT", "NEUTRAL"}


def leite_eigene_richtung(zai_client, objektive_fakten: dict) -> dict | None:
    """Zweiter, GETRENNTER Z.ai-Call (siehe Modul-Docstring Punkt 2) - leitet
    unabhaengig von der Primaer-Empfehlung eine eigene Richtung her. Gibt
    None zurueck, wenn `zai_client` nicht konfiguriert ist oder der Call
    fehlschlaegt (P-8, wie pruefe_konsistenz())."""
    if zai_client is None:
        return None

    user_content = json.dumps({"fakten": objektive_fakten}, ensure_ascii=False)
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT_RICHTUNG},
        {"role": "user", "content": user_content},
    ]
    try:
        antwort = zai_client.chat(messages, temperature=0.2, response_format=_JSON_OBJECT_FORMAT)
        geparst = json.loads(antwort)
        eigene_richtung = geparst.get("eigene_richtung")
        if eigene_richtung not in _GUELTIGE_RICHTUNGEN:
            logger.info("Z.ai-Richtungsabgleich: ungueltiges eigene_richtung-Feld: %r", eigene_richtung)
            return None
        return {
            "eigene_richtung": eigene_richtung,
            "kurzbegruendung": geparst.get("kurzbegruendung"),
        }
    except Exception as exc:
        logger.info("Z.ai-Richtungsabgleich fehlgeschlagen (P-8, ohne Auswirkung auf das Signal): %s", exc)
        return None


def pruefe_konsistenz(zai_client, fakten: dict, begruendungstext: str | None) -> dict | None:
    """Ruft Z.ai fuer die Konsistenzpruefung auf. Gibt None zurueck, wenn
    `zai_client` nicht konfiguriert ist, kein Begruendungstext vorliegt (nichts
    zu pruefen) oder der Call fehlschlaegt (P-8, faengt Netzwerkfehler UND
    ungueltige/nicht parsebare Antworten ab - analog agent/krypto/
    anticyclic.py::assess())."""
    if zai_client is None or not begruendungstext:
        return None

    user_content = json.dumps(
        {"fakten": fakten, "begruendungstext": begruendungstext}, ensure_ascii=False,
    )
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_content},
    ]
    try:
        antwort = zai_client.chat(messages, temperature=0.2, response_format=_JSON_OBJECT_FORMAT)
        geparst = json.loads(antwort)
        urteil = geparst.get("urteil")
        if urteil not in _GUELTIGE_URTEILE:
            logger.info("Z.ai-Gegenpruefung: ungueltiges urteil-Feld: %r", urteil)
            return None
        return {
            "urteil": urteil,
            "kurzbegruendung": geparst.get("kurzbegruendung"),
        }
    except Exception as exc:
        logger.info("Z.ai-Gegenpruefung fehlgeschlagen (P-8, ohne Auswirkung auf das Signal): %s", exc)
        return None
