# -*- coding: utf-8 -*-
"""Der Szenario-Schaetzer - Stufe 0 des Umbaus vom 10.08.2026.

WARUM ES DIESE DATEI GIBT. Der Gesamtbefund vom 10.08.: die Richtungsfrage an
LLM1 hat keine Kante. Gemessen an 94 bis 131 echten EROEFFNEN-Signalen, gegen
die tatsaechliche Kursbewegung, ueber drei Horizonte stabil:

    LLM 25-30 %  |  Konfluenz-Regel 40-52 %  |  Kurs vs EMA-200 56-64 %

Jede triviale Regel schlaegt das Modell. 27,7 % ist dabei KEINE Zufallsquote -
die Ausgabe ist systematisch, nur mit falschem Vorzeichen. Dazu: die Konfidenz
ordnet nicht (hoch 27,8 %, mittel 9,8 %, niedrig 18,9 %), und eine einzelne
Klartext-Zeile im Faktensatz verschob die Richtungswahl um 16 Prozentpunkte
(`einordnung`, Wild-Cluster-p 0,031).

WAS SICH AENDERT - der Kern in einem Satz: wir fragen nicht mehr nach einer
ENTSCHEIDUNG, sondern nach einer VERTEILUNG ueber fest vorgegebene Ausgaenge.

    vorher   "LONG oder SHORT, wie sicher?"      nicht kalibrierbar
    jetzt    "Was wird zuerst erreicht?"         Brier-Score, Kalibrierungskurve

DIE ZONEN SETZT DAS MODELL NICHT. Sie werden deterministisch aus dem ATR
berechnet und ihm MITGETEILT. Das ist keine Formalie: solange entry/stop/target
aus der Modellantwort stammten, war jede Frage nach "erreichst du dein Ziel?"
zirkulaer - ein enges Ziel gewinnt die Frage trivial. Genau diese Sorte
Zirkelschluss hat am 10.08. zweimal ein Messergebnis wertlos gemacht.

WAS DAS MODELL LEISTEN SOLL, und warum ueberhaupt ein Sprachmodell: es soll
heterogene Belege gegeneinander abwaegen und BEDINGUNG und WIDERLEGUNG
benennen - "was muesste zutreffen, damit das Ziel zuerst faellt, und was
widerlegt es". Das ist eine Sprachaufgabe; eine Regel kann sie nicht
formulieren. Die reine Zahlenkombination ueberlassen wir der Regel, die sie
nachweislich besser beherrscht.

WAS ES NICHT MEHR TUT: eine Richtung waehlen, eine Konfidenz vergeben, Zonen
setzen, eine Aktion empfehlen. Die Handelsentscheidung faellt danach
deterministisch aus Verteilung, CRV und Kosten - pruefbar, protokolliert,
umkehrbar.

BEIDE ANBIETER. Die Konstanten unten sind die einzige Quelle: der Validator
liest sie, und `agent/llm_schema.py::baue_szenario_schema()` leitet daraus das
strikte Schema ab. OpenRouter bekommt es strikt, Gemini/Z.ai/Mistral
`json_object` - dieselbe Aufteilung wie bei den sechs Signal-Analysten, am
09.08. je Anbieter gemessen.
"""
from __future__ import annotations

# --- Die Ausgaenge. Fest, sich gegenseitig ausschliessend, vollstaendig. -----
#
# "keines" ist kein Verlegenheitswert, sondern der haeufigste Fall: bei einem
# Horizont von sieben Kerzen erreicht ein Kurs oft weder Ziel noch Stop. Ohne
# diesen Ausgang wuerde das Modell gezwungen, Wahrscheinlichkeit auf zwei
# Ereignisse zu verteilen, von denen keines eintritt - und die Kalibrierung
# waere von vornherein kaputt.
SZENARIEN = ("ziel_zuerst_pct", "stop_zuerst_pct", "keines_pct")

# Wie ein Beleg auf die Ausgaenge zeigt. BEWUSST NICHT "bullisch/baerisch":
# die Zonen sind richtungsneutral definiert (Ziel liegt in Richtung der
# gepruefen These, Stop dagegen), damit dieselbe Form fuer LONG- und
# SHORT-Pruefungen und fuer alle sechs Assetklassen funktioniert.
BELEG_RICHTUNGEN = ("pro_ziel", "pro_stop", "neutral")
BELEG_GEWICHTE = ("hoch", "mittel", "gering")
UNSICHERHEIT_WERTE = ("hoch", "mittel", "gering")

# Reihenfolge ist Absicht: BELEGE VOR SZENARIEN. Das Ausgabeschema bestimmt,
# worauf das Modell sein Schliessen stuetzt - erst die Sammlung der Belege,
# dann die Verteilung. Die Praxisliteratur nennt das "investment thesis
# followed by a trading decision".
REQUIRED_SZENARIO_TOP_LEVEL_FIELDS = (
    "belege",
    "szenarien",
    "bedingung_ziel",
    "widerlegung_ziel",
    "staerkstes_gegenargument",
    "unsicherheit",
)

# Wie weit die Summe der drei Wahrscheinlichkeiten von 100 abweichen darf.
# Ein Prozentpunkt faengt Rundung ab, mehr wuerde eine kaputte Verteilung
# durchlassen - und eine Verteilung, die nicht auf 100 summiert, ist als
# Wahrscheinlichkeit wertlos.
SUMME_TOLERANZ_PP = 1.0

MIN_BELEGE = 2
MAX_BELEGE = 8


SYSTEM_PROMPT = """Du schaetzt Wahrscheinlichkeiten fuer einen bereits \
festgelegten Handelsaufbau. Du triffst KEINE Entscheidung, waehlst KEINE \
Richtung und setzt KEINE Kursziele - all das ist vorgegeben.

Der Aufbau steht im Fakten-JSON unter "aufbau": Einstieg, Stop und Ziel sind \
aus der aktuellen Schwankungsbreite (ATR) berechnet, der Horizont ist die Zahl \
der Handelstage, in denen sich das entscheidet.

DEINE AUFGABE, in dieser Reihenfolge:

1. BELEGE sammeln. Gehe die Fakten durch und notiere je Beleg, ob er fuer das \
Erreichen des ZIELS spricht (pro_ziel), fuer das Erreichen des STOPS \
(pro_stop) oder fuer keines von beidem (neutral) - mit einem Gewicht \
(hoch/mittel/gering). Zwischen zwei und acht Belege. Erfinde keine Fakten; \
nutze nur die gegebenen Werte, und nenne sie beim Namen.

2. VERTEILEN. Schaetze, was innerhalb des Horizonts ZUERST eintritt:
   - ziel_zuerst_pct: der Kurs erreicht das Ziel vor dem Stop
   - stop_zuerst_pct: der Kurs erreicht den Stop vor dem Ziel
   - keines_pct: innerhalb des Horizonts wird keines von beidem erreicht
   Die drei Zahlen muessen auf 100 summieren. "keines" ist haeufig - ein Kurs \
bewegt sich oft nicht weit genug.

3. BEDINGUNG und WIDERLEGUNG benennen: was muesste zutreffen, damit das Ziel \
zuerst faellt - und welche einzelne Beobachtung wuerde diese Erwartung \
widerlegen. Konkret und ueberpruefbar, keine Allgemeinplaetze.

4. Das STAERKSTE GEGENARGUMENT gegen deine eigene Verteilung nennen.

5. UNSICHERHEIT einschaetzen (hoch/mittel/gering) - wie belastbar ist deine \
Verteilung angesichts der Faktenlage.

Antworte AUSSCHLIESSLICH mit JSON in genau dieser Form:
{"belege": [{"fakt": "<kurz>", "richtung": "pro_ziel|pro_stop|neutral", \
"gewicht": "hoch|mittel|gering"}],
 "szenarien": {"ziel_zuerst_pct": <zahl>, "stop_zuerst_pct": <zahl>, \
"keines_pct": <zahl>},
 "bedingung_ziel": "<kurz>", "widerlegung_ziel": "<kurz>",
 "staerkstes_gegenargument": "<kurz>", "unsicherheit": "hoch|mittel|gering"}"""


class SzenarioAntwortUngueltig(ValueError):
    """Die Antwort erfuellt den Vertrag nicht - mit Angabe, woran es lag."""


def _validate_szenario(antwort: dict, symbol: str = "?") -> dict:
    """Prueft den Vertrag. Wirft mit klarer Begruendung statt still zu heilen.

    STILLES HEILEN WAERE HIER DER FEHLER: eine Verteilung, die nicht auf 100
    summiert, laesst sich zwar normieren - dann misst der Brier-Score aber
    unsere Normierung mit, nicht die Schaetzung des Modells. Lieber ein
    Fehlschlag, der gezaehlt wird, als ein stillschweigend veraenderter Wert.
    """
    if not isinstance(antwort, dict):
        raise SzenarioAntwortUngueltig(f"{symbol}: Antwort ist kein Objekt")
    fehlend = [f for f in REQUIRED_SZENARIO_TOP_LEVEL_FIELDS if f not in antwort]
    if fehlend:
        raise SzenarioAntwortUngueltig(f"{symbol}: Felder fehlen: {fehlend}")

    belege = antwort["belege"]
    if not isinstance(belege, list) or not (MIN_BELEGE <= len(belege) <= MAX_BELEGE):
        raise SzenarioAntwortUngueltig(
            f"{symbol}: 'belege' braucht {MIN_BELEGE} bis {MAX_BELEGE} Eintraege, "
            f"hat {len(belege) if isinstance(belege, list) else type(belege).__name__}")
    for i, b in enumerate(belege):
        if not isinstance(b, dict) or "fakt" not in b:
            raise SzenarioAntwortUngueltig(f"{symbol}: Beleg {i} ohne 'fakt'")
        if b.get("richtung") not in BELEG_RICHTUNGEN:
            raise SzenarioAntwortUngueltig(
                f"{symbol}: Beleg {i} richtung={b.get('richtung')!r}, "
                f"erlaubt {BELEG_RICHTUNGEN}")
        if b.get("gewicht") not in BELEG_GEWICHTE:
            raise SzenarioAntwortUngueltig(
                f"{symbol}: Beleg {i} gewicht={b.get('gewicht')!r}, "
                f"erlaubt {BELEG_GEWICHTE}")

    sz = antwort["szenarien"]
    if not isinstance(sz, dict):
        raise SzenarioAntwortUngueltig(f"{symbol}: 'szenarien' ist kein Objekt")
    werte = []
    for k in SZENARIEN:
        v = sz.get(k)
        if not isinstance(v, (int, float)) or isinstance(v, bool):
            raise SzenarioAntwortUngueltig(f"{symbol}: szenarien.{k}={v!r} ist keine Zahl")
        if not 0 <= v <= 100:
            raise SzenarioAntwortUngueltig(f"{symbol}: szenarien.{k}={v} ausserhalb 0-100")
        werte.append(float(v))
    summe = sum(werte)
    if abs(summe - 100.0) > SUMME_TOLERANZ_PP:
        raise SzenarioAntwortUngueltig(
            f"{symbol}: Wahrscheinlichkeiten summieren auf {summe:.1f} statt 100 "
            f"(Toleranz {SUMME_TOLERANZ_PP} pp)")

    if antwort.get("unsicherheit") not in UNSICHERHEIT_WERTE:
        raise SzenarioAntwortUngueltig(
            f"{symbol}: unsicherheit={antwort.get('unsicherheit')!r}, "
            f"erlaubt {UNSICHERHEIT_WERTE}")
    for feld in ("bedingung_ziel", "widerlegung_ziel", "staerkstes_gegenargument"):
        if not isinstance(antwort.get(feld), str) or not antwort[feld].strip():
            raise SzenarioAntwortUngueltig(f"{symbol}: '{feld}' fehlt oder ist leer")
    return antwort
