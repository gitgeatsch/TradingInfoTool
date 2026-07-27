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

Scope v1: nur Hebel (siehe budget_allocator.py-Docstring).

Erweiterung (2026-07-27): der Konsistenz-Check (`pruefe_konsistenz()`) laeuft
jetzt auch fuer Spot-Signale (agent/krypto/pipeline.py), NICHT der
unabhaengige Richtungs-Abgleich (`leite_eigene_richtung()`, bleibt Hebel-only
- Spot-Signale kennen kein `richtung`/LONG-SHORT-Konzept). `baue_fakten()`
bekommt dafuer ein optionales `richtung`-Argument (Default None) - fehlt es
(Spot-Aufruf), wird der Schluessel im Fakten-Dict komplett weggelassen statt
mit einem erfundenen Wert befuellt. Der SYSTEM_PROMPT unten muss dafuer NICHT
angepasst werden: seine TEILVERKAUF/SCHLIESSEN/HEBEL_SENKEN-Klausel greift
nur bei genau diesen drei (Hebel-exklusiven) Aktionsnamen - Spot-Aktionen
(KAUFEN/VERKAUFEN/TAUSCHEN/NACHKAUFEN/HALTEN) fallen automatisch unter die
"ALLEN anderen Aktionen"-Regel, exakt wie vor der Kontrathese-Erweiterung.

Vollstaendige Vereinheitlichung (Nachtrag, gleicher Monat): BEIDE Calls jetzt
fuer ALLE 6 Pipelines (Krypto-Hebel/Spot, Aktien, Rohstoffe, Themen-ETF,
Hedge) - Nutzer-Vorgabe "soll vom Grundprinzip bei allen Assets ident
funktionieren". Zwei neue, generische Bausteine:

`richtung_aus_action()` - die Spot-family (alle ausser Hebel) hat kein
echtes `richtung`-Feld (LONG/SHORT), nur Action-Verben (KAUFEN/VERKAUFEN/
NACHKAUFEN/TAUSCHEN/HALTEN). Deterministisches Mapping auf die fuer den
Richtungs-Abgleich erwartete Richtung, HALTEN liefert None (kein Vergleich,
analog dazu, dass Hebel bestimmte Aktionen wie TEILVERKAUF/SCHLIESSEN vom
Konsistenz-Check-Sonderfall betrifft). Hedge-Sonderfall: Hedge-Instrumente
sind inverse Absicherungen - KAUFEN (Hedge aufbauen) korreliert mit einer
BAERISCHEN Gesamtmarkterwartung, nicht mit einer bullischen Erwartung an das
Hedge-Instrument selbst (die an Call 2 uebergebenen Fakten sind bei Hedge
ohnehin nur Makro-/Regime-Fakten, kein instrumentenspezifisches RSI/
Konfluenz - Z.ais `eigene_richtung` bedeutet dort faktisch "Einschaetzung
zum Gesamtmarkt"). Deshalb `ist_hedge_invertiert=True` NUR beim Aufruf aus
agent/hedge/pipeline.py - deterministisch in Python, kein neuer Fakt/Prompt-
Zweig fuer Z.ai (mit Nutzer abgestimmt, 2026-07-27).

`fuehre_beide_calls_im_hintergrund()` - verallgemeinerte Version von
hebel_pipeline.py::_zai_gegenpruefung_im_hintergrund() (dorthin verschoben),
parametrisiert ueber `update_fn` (entweder db.update_hebel_signal_zai_
gegenpruefung oder db.update_signal_zai_gegenpruefung - seit deren
Erweiterung identische 5-Werte-Signatur). Von ALLEN 6 Pipelines
wiederverwendet statt pro Pipeline dupliziert."""
from __future__ import annotations

import json
import logging

import database.db as db

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
    richtung: str | None = None,
) -> dict:
    """Bewusst schmale Faktenmenge (siehe Modul-Docstring) - live verifiziert,
    dass eine reichere Menge (inkl. Optionsmarkt-Skew) KEINE zusaetzliche
    Antwortzeit kostet gegenueber einer minimalen Menge (12-16s in beiden
    Faellen), also keine Notwendigkeit, hier weiter zu kuerzen.

    `richtung` optional (Default None, 2026-07-27) - Spot-Signale haben kein
    LONG/SHORT-Konzept, der Schluessel wird dann komplett weggelassen statt
    mit einem erfundenen Wert befuellt (siehe Modul-Docstring "Erweiterung")."""
    fakten = {"symbol": symbol, "action": action, "confidence_pct": confidence_pct}
    if richtung is not None:
        fakten["richtung"] = richtung
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


_LONG_ACTIONS = {"KAUFEN", "NACHKAUFEN"}
_SHORT_ACTIONS = {"VERKAUFEN", "TAUSCHEN"}  # TAUSCHEN nur Krypto-Spot-exklusiv


def richtung_aus_action(action: str, ist_hedge_invertiert: bool = False) -> str | None:
    """Deterministisches Mapping Action -> erwartete Richtung fuer Call 2 bei
    der Spot-family (Krypto-Spot/Aktien/Rohstoffe/Themen-ETF/Hedge - keine hat
    ein echtes `richtung`-Feld wie Hebel). Siehe Modul-Docstring
    "Vollstaendige Vereinheitlichung" fuer die volle Begruendung.

    HALTEN (und jede unbekannte Action) liefert None - kein Vergleich, analog
    dazu, dass bestimmte Hebel-Aktionen ebenfalls Sonderbehandlung erfahren.
    KAUFEN/NACHKAUFEN = bullische Erwartung an das Asset selbst -> LONG.
    VERKAUFEN/TAUSCHEN = baerische Erwartung an das Asset selbst -> SHORT
    (TAUSCHEN: das Ziel-Asset wird gekauft, aber DIESES Symbol wird als
    schwaecher bewertet - bearish auf dieses Symbol).

    `ist_hedge_invertiert=True` NUR fuer agent/hedge/pipeline.py setzen (dort
    IMMER True, da diese Pipeline ausschliesslich Hedge-Instrumente
    verarbeitet - kein Symbol-Lookup noetig): KAUFEN/NACHKAUFEN (Hedge
    aufbauen/verstaerken) -> SHORT (baerische Gesamtmarkterwartung),
    VERKAUFEN -> LONG."""
    if action == "HALTEN":
        return None
    ist_long = action in _LONG_ACTIONS
    ist_short = action in _SHORT_ACTIONS
    if not ist_long and not ist_short:
        return None
    if ist_hedge_invertiert:
        return "SHORT" if ist_long else "LONG"
    return "LONG" if ist_long else "SHORT"


def fuehre_beide_calls_im_hintergrund(
    signal_id: int,
    fakten: dict,
    begruendungstext: str | None,
    objektive_fakten: dict,
    primaer_richtung_erwartet: str | None,
    zai_client,
    update_fn,
) -> None:
    """Generische, wiederverwendbare Version von hebel_pipeline.py::
    _zai_gegenpruefung_im_hintergrund() (von dort hierher verschoben, siehe
    Modul-Docstring "Vollstaendige Vereinheitlichung") - laeuft in einem
    eigenen Thread (Aufrufstelle in jeder der 6 Pipelines), GENUINE
    Entkopplung von der eigentlichen Signal-Erstellung: Z.ai hat einen
    150s-Timeout (api/zai.py::REQUEST_TIMEOUT_SECONDS), ein synchroner Call
    vor `return signal` wuerde die jeweilige `generate_signal()`/
    `generate_hebel_signal()` selbst verzoegern - und damit auch den
    `on_signal_ready`-E-Mail-Callback, der erst NACH der Rueckkehr dieser
    Funktion feuert (siehe project_email_latenz_fix_batch_notification.md).

    `update_fn` ist entweder db.update_hebel_signal_zai_gegenpruefung oder
    db.update_signal_zai_gegenpruefung (seit deren Erweiterung identische
    5-Werte-Signatur). `primaer_richtung_erwartet` ist bei Hebel die echte
    `richtung` (LONG/SHORT), bei der Spot-family das Ergebnis von
    richtung_aus_action() (None -> kein Vergleich, z.B. bei HALTEN).

    Eigene DB-Connection (sqlite3-Connections sind nicht thread-uebergreifend
    teilbar) statt der von der aufrufenden Funktion verwendeten. Fehler in
    einem der beiden Calls duerfen das Schreiben des jeweils anderen nicht
    verhindern (try/except pro Call bereits in pruefe_konsistenz()/
    leite_eigene_richtung() selbst, hier zusaetzlich fuer den Thread-Kontext,
    z.B. falls die neue DB-Connection scheitert) - beide Ergebnisse werden
    gemeinsam in EINEM DB-Update geschrieben, damit ein fehlgeschlagener
    zweiter Call das Ergebnis des ersten nicht durch Nones ueberschreibt."""
    urteil = kurzbegruendung = eigene_richtung = uebereinstimmung = richtung_kurzbegruendung = None
    try:
        konsistenz_ergebnis = pruefe_konsistenz(zai_client, fakten, begruendungstext)
        if konsistenz_ergebnis is not None:
            urteil = konsistenz_ergebnis.get("urteil")
            kurzbegruendung = konsistenz_ergebnis.get("kurzbegruendung")

        richtung_ergebnis = leite_eigene_richtung(zai_client, objektive_fakten)
        if richtung_ergebnis is not None:
            eigene_richtung = richtung_ergebnis.get("eigene_richtung")
            richtung_kurzbegruendung = richtung_ergebnis.get("kurzbegruendung")
            if primaer_richtung_erwartet is not None:
                uebereinstimmung = "ja" if eigene_richtung == primaer_richtung_erwartet else "nein"

        if urteil is None and eigene_richtung is None:
            return  # beide Calls fehlgeschlagen - nichts zu speichern

        thread_conn = db.get_connection()
        try:
            update_fn(
                thread_conn, signal_id, urteil, kurzbegruendung,
                eigene_richtung, uebereinstimmung, richtung_kurzbegruendung,
            )
        finally:
            thread_conn.close()
    except Exception:
        logger.exception(
            "Z.ai-Gegenpruefung im Hintergrund-Thread fehlgeschlagen (signal_id=%s)", signal_id,
        )
