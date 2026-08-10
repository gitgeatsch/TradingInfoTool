# -*- coding: utf-8 -*-
"""Rolle BC - Aufbau beurteilen und daraus handeln. Ein Aufruf je Asset.

WARUM ZWEI ROLLEN IN EINEM AUFRUF. Der urspruengliche Entwurf trennte Trader
(bewerten) und Entscheider (handeln) - das ergab mit Selbstkonsistenz rund 162
Aufrufe taeglich gegen heute 40. Nutzer am 10.08.: nicht tragbar.

Recherchiert wurde daraufhin, welche der belegten Einwaende gegen mehrere Rollen
in einem Aufruf hier ueberhaupt greifen:

  Schema-Konfusion    nein - wir erzeugen genau ein JSON, nicht mehrere
  Anchoring           nein, hier gewollt - die Handlung SOLL auf den Belegen
                      aufbauen; das ist eine Kette, keine unabhaengige Meinung
  Selbstvalidierung   nein - es wird nichts kritisiert, es wird gefolgert
  HEDGING             JA - "ein einzelner Prompt mit mehreren Perspektiven
                      erzeugt abwaegende Beidseitigkeits-Analysen"

Das Hedging ist der reale Einwand, und er beschreibt exakt den KAS-Fall vom
15.07.: *"Technisch leichte Erholung ... ABER WEITERHIN bearishes Marktumfeld."*

DAGEGEN WIRKT DER AUFBAU DER AUSGABE. `begruendung` und `was_dagegen` sind
getrennte Felder - der Gegengrund hat einen eigenen Platz und muss nicht in die
Begruendung hineinrelativiert werden. Der Validator in `empfehlung_vertrag.py`
lehnt Begruendungen ab, die sich selbst zurueckziehen; am echten KAS-Text
getestet. Damit ist Hedging kein Risiko, sondern ein MESSBARER ZUSTAND: haeufen
sich diese Ablehnungen, ist die Zusammenlegung widerlegt.

EIN ECHTER GEGENPRUEFER DARF NIEMALS HIERHER. Dort greift die Selbstvalidierung
voll - ein Modell bestaetigt, was es gerade geschrieben hat. Falls er gebaut
wird, zwingend als eigener Aufruf mit frischem Kontext.

WAS BEWUSST NICHT GEFRAGT WIRD:

  * keine Konfidenz in Prozent - extern belegt schlecht kalibriert, im eigenen
    System 77,5 % vorhergesagt gegen 33,3 % tatsaechlich
  * keine Rechnung - Tokenisierung zerlegt Zahlen, GPT-4o faellt bei Addition
    auf 15 %. Der Erwartungswert wird spaeter deterministisch gerechnet
  * keine Positionsgroesse - nur die Wahl einer Tranche, gedeckelt durch Rolle A

STATT KONFIDENZ: die Zahl der UNABHAENGIGEN Belege. Die Praxisliteratur nennt
drei bis vier unabhaengige Faktoren als Bereich fuer einen tragfaehigen Aufbau;
eins bis zwei sind duenn. Ob drei Belege wirklich drei Dinge sagen oder dreimal
dasselbe, ist eine Sprachfrage - und damit die Aufgabe, fuer die ein
Sprachmodell hier ueberhaupt eingesetzt wird.
"""
from __future__ import annotations

from agent.empfehlung_vertrag import AKTIONEN, TRANCHEN_EUR

BELEG_RICHTUNGEN = ("dafuer", "dagegen")
BELEG_GEWICHTE = ("hoch", "mittel", "gering")

REQUIRED_FELDER = (
    "belege",
    "unabhaengige_faktoren",
    "aktion",
    "begruendung",
    "was_dagegen",
    "umgeworfen_durch",
)

SYSTEM_PROMPT_TRADER = """Du bist ein erfahrener Haendler und triffst eine \
Entscheidung ueber genau einen Wert. Du bekommst seine Lage in Worten, deinen \
aktuellen Bestand darin und eine Obergrenze fuer den Einsatz.

DEINE AUFGABE, in dieser Reihenfolge:

1. BELEGE sammeln. Gehe die Angaben durch und notiere, was fuer einen Einstieg \
spricht und was dagegen - je mit einem Gewicht (hoch/mittel/gering). Zwischen \
zwei und acht. Nenne den Wert, auf den sich der Beleg stuetzt. Erfinde nichts.

2. UNABHAENGIGE FAKTOREN zaehlen. Wie viele deiner Belege sagen wirklich \
VERSCHIEDENE Dinge? Zwei Belege, die beide auf denselben Abwaertstrend zeigen, \
sind EIN Faktor, nicht zwei. Diese Zahl ist wichtiger als ihre Menge: drei bis \
vier unabhaengige Faktoren tragen einen Aufbau, einer oder zwei nicht.

3. HANDELN. Waehle: KAUFEN (neu aufbauen), NACHKAUFEN (bestehende Position \
vergroessern), REDUZIEREN, VERKAUFEN oder NICHTS_TUN. Bei allem ausser \
NICHTS_TUN nenne den Betrag - 100, 300 oder 500 Euro, hoechstens die vorgegebene \
Obergrenze. Bei KAUFEN und NACHKAUFEN zusaetzlich den Einstiegskurs und den \
Ausstiegskurs, beide in Euro; der Ausstieg liegt unter dem Einstieg.

4. BEGRUENDUNG. Ein bis zwei Saetze, die deine Wahl TRAGEN. Keine Einschraenkung \
im Nachsatz - was dagegen spricht, gehoert in das naechste Feld.

5. WAS DAGEGEN SPRICHT. Der staerkste Gegengrund, klar benannt. Er entwertet \
deine Entscheidung nicht; er gehoert dazu.

6. UMGEWORFEN DURCH. Welche einzelne, ueberpruefbare Beobachtung wuerde deine \
Entscheidung als falsch erweisen? Ein Kurs, ein Datum, ein Ereignis - nichts \
Allgemeines.

Antworte AUSSCHLIESSLICH mit JSON:
{"belege": [{"fakt": "<kurz, mit Wert>", "richtung": "dafuer|dagegen", \
"gewicht": "hoch|mittel|gering"}],
 "unabhaengige_faktoren": <zahl>,
 "aktion": "KAUFEN|NACHKAUFEN|REDUZIEREN|VERKAUFEN|NICHTS_TUN",
 "tranche_eur": 100|300|500,
 "einstieg_eur": <zahl>, "stop_eur": <zahl>,
 "begruendung": "<ein bis zwei Saetze>",
 "was_dagegen": "<der staerkste Gegengrund>",
 "umgeworfen_durch": "<eine ueberpruefbare Beobachtung>"}"""


class TraderAntwortUngueltig(ValueError):
    """Die Antwort erfuellt ihren Vertrag nicht."""


def validiere(antwort: dict, symbol: str = "?",
              max_tranche_eur: int | None = None) -> dict:
    """Prueft die Rollen-eigenen Felder; der Handlungsteil laeuft danach durch
    `empfehlung_vertrag.validiere()`.

    `max_tranche_eur` ist die Obergrenze aus Rolle A. Sie wird hier geprueft und
    nicht dem Modell ueberlassen: eine Obergrenze, die nur im Prompt steht und
    nicht kontrolliert wird, ist eine Bitte."""
    from agent.empfehlung_vertrag import validiere as vertrag_validieren

    if not isinstance(antwort, dict):
        raise TraderAntwortUngueltig(f"{symbol}: Antwort ist kein Objekt")
    fehlend = [f for f in REQUIRED_FELDER if antwort.get(f) in (None, "", [])]
    if fehlend:
        raise TraderAntwortUngueltig(f"{symbol}: Felder fehlen: {fehlend}")

    belege = antwort["belege"]
    if not isinstance(belege, list) or not 2 <= len(belege) <= 8:
        raise TraderAntwortUngueltig(
            f"{symbol}: belege {len(belege) if isinstance(belege, list) else '?'}, "
            f"erwartet 2 bis 8")
    for b in belege:
        if not isinstance(b, dict):
            raise TraderAntwortUngueltig(f"{symbol}: Beleg ist kein Objekt")
        if b.get("richtung") not in BELEG_RICHTUNGEN:
            raise TraderAntwortUngueltig(
                f"{symbol}: Beleg-richtung={b.get('richtung')!r}, "
                f"erlaubt {BELEG_RICHTUNGEN}")
        if b.get("gewicht") not in BELEG_GEWICHTE:
            raise TraderAntwortUngueltig(
                f"{symbol}: Beleg-gewicht={b.get('gewicht')!r}, "
                f"erlaubt {BELEG_GEWICHTE}")
        if not str(b.get("fakt") or "").strip():
            raise TraderAntwortUngueltig(f"{symbol}: Beleg ohne Fakt")

    try:
        faktoren = int(antwort["unabhaengige_faktoren"])
    except (TypeError, ValueError):
        raise TraderAntwortUngueltig(
            f"{symbol}: unabhaengige_faktoren ist keine Zahl")
    # Mehr unabhaengige Faktoren als Belege ist logisch unmoeglich - und ein
    # verlaesslicher Hinweis darauf, dass das Modell die Frage nicht beantwortet,
    # sondern eine Zahl geraten hat.
    if not 0 <= faktoren <= len(belege):
        raise TraderAntwortUngueltig(
            f"{symbol}: {faktoren} unabhaengige Faktoren bei {len(belege)} "
            f"Belegen - unmoeglich")

    if max_tranche_eur is not None and antwort.get("tranche_eur"):
        try:
            gewaehlt = int(float(antwort["tranche_eur"]))
        except (TypeError, ValueError):
            gewaehlt = None
        if gewaehlt and gewaehlt > max_tranche_eur:
            raise TraderAntwortUngueltig(
                f"{symbol}: tranche_eur {gewaehlt} ueberschreitet die Obergrenze "
                f"{max_tranche_eur} aus der Marktlage")

    return vertrag_validieren(antwort, symbol)
