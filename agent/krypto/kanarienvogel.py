"""Kanarienvogel: meldet, wenn sich das LLM-Verhalten aendert (2026-08-05).

WARUM ES DAS GIBT. Am 31.07. kippte das Hebel-Verhalten binnen einer Stunde:
selbst gewaehltes HALTEN von 35-51 auf 2-6 Signale taeglich, Konfidenz im
Mittel von 54,1 % auf 68,3 %, SHORT-Anteil von 7 % auf ueber 60 %. Wir haben
danach TAGE damit verbracht, den Fehler im eigenen Regelwerk zu suchen - drei
Prompt-Regeln einzeln gegen einen Backtest gefahren, das Gate geprueft, den
Markt gemessen, die Messmethodik zweimal korrigiert.

Der Nachweis kam erst, als dieselben Faktensaetze mit dem bitgleichen
Juli-Prompt erneut gefragt wurden: 55,4 % Konfidenz im Betrieb damals gegen
68,0 % heute, +12,6 Punkte, t = +12,8 - und damit exakt das Niveau NACH dem
Sprung. Der Modellname `mistral-small-2506` war die ganze Zeit unveraendert.

DIESE MESSUNG MACHT DEN NACHWEIS ZUM DAUERZUSTAND. Sie fragt in
regelmaessigen Abstaenden dieselben eingefrorenen Faktensaetze mit dem
aktuellen Prompt und vergleicht gegen eine festgehaltene Grundlinie. Weicht
das Ergebnis ab, steht das im Log und im Export - BEVOR jemand tagelang das
eigene Regelwerk verdaechtigt.

WAS SIE NICHT KANN, und das gehoert dazu: sie unterscheidet nicht zwischen
"der Anbieter hat das Modell getauscht" und "unser Prompt hat sich geaendert".
Beides schlaegt hier aus. Deshalb wird der Prompt-Hash mitgeschrieben - aendert
er sich, ist der Ausschlag erklaert und die Grundlinie gehoert neu gesetzt.
Bleibt er gleich und das Verhalten kippt trotzdem, liegt es beim Anbieter.

DIE SCHWELLE IST GEMESSEN, NICHT GERATEN. Zwei identische Arme
(teste_regel28_echt.py, je 33-35 Aufrufe) lagen bei 67,8 % gegen 68,3 %
Konfidenz - das Eigenrauschen betraegt also rund einen halben Punkt. Der
Bruch vom 31.07. betrug 12,6 Punkte. KONFIDENZ_SCHWELLE = 5,0 liegt damit ein
Vielfaches ueber dem Rauschen und deutlich unter dem, was wir tatsaechlich
verpasst haben.
"""
from __future__ import annotations

import hashlib
import json
import logging
import statistics
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)

FIXTURE_DATEI = Path(__file__).resolve().parents[2] / "data" / "kanarienvogel_fixtures.json"
GRUNDLINIE_DATEI = Path(__file__).resolve().parents[2] / "data" / "kanarienvogel_grundlinie.json"

# Gemessen, nicht geraten - siehe Modul-Docstring.
KONFIDENZ_SCHWELLE = 5.0        # Punkte
AKTIONS_SCHWELLE = 0.30         # Anteil EROEFFNEN
WIEDERHOLUNGEN = 2              # je Faktensatz; bei 5 Fixtures also 10 Aufrufe


@dataclass
class Kanarienbefund:
    lauf_konfidenz: float | None = None
    lauf_eroeffnen_anteil: float | None = None
    grundlinie_konfidenz: float | None = None
    grundlinie_eroeffnen_anteil: float | None = None
    prompt_hash: str = ""
    grundlinie_prompt_hash: str = ""
    prompt_geaendert: bool = False
    n_aufrufe: int = 0
    n_fehler: int = 0
    abweichung: bool = False
    meldung: str = ""
    details: list[dict] = field(default_factory=list)

    def als_dict(self) -> dict:
        return {
            "lauf_konfidenz": self.lauf_konfidenz,
            "lauf_eroeffnen_anteil": self.lauf_eroeffnen_anteil,
            "grundlinie_konfidenz": self.grundlinie_konfidenz,
            "grundlinie_eroeffnen_anteil": self.grundlinie_eroeffnen_anteil,
            "prompt_hash": self.prompt_hash,
            "grundlinie_prompt_hash": self.grundlinie_prompt_hash,
            "prompt_geaendert": self.prompt_geaendert,
            "n_aufrufe": self.n_aufrufe,
            "n_fehler": self.n_fehler,
            "abweichung": self.abweichung,
            "meldung": self.meldung,
            "details": self.details,
        }


def _prompt_hash(prompt: str) -> str:
    return hashlib.sha256(prompt.encode("utf-8")).hexdigest()[:16]


def lade_fixtures() -> list[dict]:
    if not FIXTURE_DATEI.exists():
        return []
    try:
        return json.loads(FIXTURE_DATEI.read_text(encoding="utf-8")).get("fixtures", [])
    except (OSError, ValueError) as exc:
        logger.warning("Kanarienvogel-Fixtures nicht lesbar: %s", exc)
        return []


def lade_grundlinie() -> dict | None:
    if not GRUNDLINIE_DATEI.exists():
        return None
    try:
        return json.loads(GRUNDLINIE_DATEI.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        logger.warning("Kanarienvogel-Grundlinie nicht lesbar: %s", exc)
        return None


def schreibe_grundlinie(daten: dict) -> None:
    GRUNDLINIE_DATEI.parent.mkdir(parents=True, exist_ok=True)
    GRUNDLINIE_DATEI.write_text(json.dumps(daten, ensure_ascii=False, indent=1),
                                encoding="utf-8")


def pruefe_llm_drift(llm_client, system_prompt: str, frage_fn,
                     wiederholungen: int = WIEDERHOLUNGEN) -> Kanarienbefund:
    """Fragt die eingefrorenen Faktensaetze und vergleicht gegen die Grundlinie.

    `frage_fn(client, fakten, prompt) -> dict | None` wird hereingereicht statt
    importiert, damit diese Funktion ohne Netz testbar bleibt - ein
    nachgebildetes LLM genuegt, um die gesamte Auswertung zu pruefen."""
    befund = Kanarienbefund(prompt_hash=_prompt_hash(system_prompt))
    fixtures = lade_fixtures()
    if not fixtures:
        befund.meldung = "keine Fixtures hinterlegt - Messung uebersprungen"
        return befund

    konfidenzen: list[float] = []
    aktionen: list[str] = []
    for fx in fixtures:
        fakten = fx.get("fakten")
        if not isinstance(fakten, dict):
            continue
        for _ in range(wiederholungen):
            befund.n_aufrufe += 1
            try:
                antwort = frage_fn(llm_client, fakten, system_prompt)
            except Exception as exc:                      # Netz/Provider
                befund.n_fehler += 1
                logger.info("Kanarienvogel: Aufruf fehlgeschlagen (%s)", type(exc).__name__)
                continue
            if not antwort:
                befund.n_fehler += 1
                continue
            aktion = str(antwort.get("action", "?")).upper()
            aktionen.append(aktion)
            k = antwort.get("confidence_pct")
            if isinstance(k, (int, float)):
                konfidenzen.append(float(k))
            befund.details.append({"fixture": fx.get("name"), "action": aktion,
                                   "confidence_pct": k})

    if not aktionen:
        befund.meldung = (f"alle {befund.n_aufrufe} Aufrufe fehlgeschlagen - "
                          "keine Aussage moeglich")
        return befund

    befund.lauf_konfidenz = statistics.fmean(konfidenzen) if konfidenzen else None
    # ⚠️ BEIDE VOKABULARE ZAEHLEN (S6a, 22.08.2026).
    #
    # Bis S6a hiess die Eroeffnungsaktion "ERÖFFNEN", seither "KAUFEN".
    # Zaehlte man weiter nur den alten Namen, faele der Anteil auf NULL - und
    # der Kanarienvogel meldete "EROEFFNEN-Anteil 85 % -> 0 %" als
    # Verhaltensbruch des Modells. Ein Fehlalarm, erzeugt allein durch eine
    # Umbenennung, und einer, der genau das Werkzeug unbrauchbar macht, das
    # echte Bruecke finden soll.
    #
    # Die ALTEN Namen bleiben mitgezaehlt: die Grundlinie kann aus der Zeit
    # davor stammen, und ein Vergleich gegen eine Grundlinie mit anderem
    # Vokabular waere derselbe Fehlalarm mit umgekehrtem Vorzeichen.
    _AUFBAU = ("KAUFEN", "ERÖFFNEN", "EROEFFNEN")
    befund.lauf_eroeffnen_anteil = sum(
        1 for a in aktionen if a in _AUFBAU) / len(aktionen)

    grund = lade_grundlinie()
    if grund is None:
        schreibe_grundlinie({
            "erstellt_am_prompt_hash": befund.prompt_hash,
            "konfidenz": befund.lauf_konfidenz,
            "eroeffnen_anteil": befund.lauf_eroeffnen_anteil,
            "n_aufrufe": befund.n_aufrufe,
            "hinweis": ("Erstlauf - diese Werte sind ab jetzt der Vergleichsmassstab. "
                        "Bei einer bewussten Prompt-Aenderung diese Datei loeschen, "
                        "damit sie neu aufgenommen wird."),
        })
        befund.meldung = ("Erstlauf - Grundlinie aufgenommen "
                          f"(Konfidenz {befund.lauf_konfidenz:.1f} %, "
                          f"EROEFFNEN {befund.lauf_eroeffnen_anteil * 100:.0f} %)")
        return befund

    befund.grundlinie_konfidenz = grund.get("konfidenz")
    befund.grundlinie_eroeffnen_anteil = grund.get("eroeffnen_anteil")
    befund.grundlinie_prompt_hash = str(grund.get("erstellt_am_prompt_hash") or "")
    befund.prompt_geaendert = (bool(befund.grundlinie_prompt_hash)
                               and befund.grundlinie_prompt_hash != befund.prompt_hash)

    abweichungen = []
    if (befund.lauf_konfidenz is not None and befund.grundlinie_konfidenz is not None
            and abs(befund.lauf_konfidenz - befund.grundlinie_konfidenz) >= KONFIDENZ_SCHWELLE):
        abweichungen.append(
            f"Konfidenz {befund.grundlinie_konfidenz:.1f} % -> "
            f"{befund.lauf_konfidenz:.1f} % "
            f"({befund.lauf_konfidenz - befund.grundlinie_konfidenz:+.1f} Punkte)")
    if (befund.lauf_eroeffnen_anteil is not None
            and befund.grundlinie_eroeffnen_anteil is not None
            and abs(befund.lauf_eroeffnen_anteil - befund.grundlinie_eroeffnen_anteil)
            >= AKTIONS_SCHWELLE):
        abweichungen.append(
            f"EROEFFNEN-Anteil {befund.grundlinie_eroeffnen_anteil * 100:.0f} % -> "
            f"{befund.lauf_eroeffnen_anteil * 100:.0f} %")

    if not abweichungen:
        befund.meldung = (f"unauffaellig (Konfidenz {befund.lauf_konfidenz:.1f} %, "
                          f"EROEFFNEN {befund.lauf_eroeffnen_anteil * 100:.0f} %)")
        return befund

    befund.abweichung = True
    if befund.prompt_geaendert:
        befund.meldung = (
            "ABWEICHUNG, aber der PROMPT hat sich geaendert "
            f"({befund.grundlinie_prompt_hash} -> {befund.prompt_hash}) - damit ist sie "
            "erklaert. Grundlinie neu setzen: data/kanarienvogel_grundlinie.json "
            "loeschen. Details: " + "; ".join(abweichungen))
    else:
        befund.meldung = (
            "ABWEICHUNG bei UNVERAENDERTEM Prompt - dieselben Fakten, derselbe "
            "Prompt, anderes Verhalten. Das deutet auf eine anbieterseitige "
            "Modellaenderung hin, nicht auf unseren Code (Vorfall 31.07.2026, "
            "siehe agent/krypto/kanarienvogel.py). Details: "
            + "; ".join(abweichungen))
    return befund
