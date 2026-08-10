# -*- coding: utf-8 -*-
"""Von der Verteilung zur Empfehlung - deterministisch, Stufe 2 (10.08.2026).

WARUM DIESER SCHRITT NICHT IM MODELL LIEGT. Bis heute hat das Sprachmodell die
Handlung selbst gewaehlt. Das hatte drei Folgen, alle gemessen:

  * Die Entscheidung war nicht pruefbar - es gab keine Rechnung, nur ein Urteil.
  * Sie war nicht kalibrierbar - "Konfidenz 82 %" traf zu 27,8 %.
  * Sie war durch eine einzelne Textzeile im Faktensatz um 16 Prozentpunkte
    verschiebbar (`einordnung`, Wild-Cluster-p 0,031).

Hier faellt sie stattdessen aus einer Rechnung, die jeder nachvollziehen kann:
Erwartungswert aus der geschaetzten Verteilung, minus Kosten, gegen eine
Schwelle. Das Modell liefert die Wahrscheinlichkeiten, die Entscheidung folgt
daraus - protokolliert, umkehrbar, und ohne Raum fuer Wortwahl-Effekte.

DIE R-WERTE FOLGEN AUS DEN ZONEN, sie sind nicht frei gewaehlt:

    Ziel zuerst   +2 R   Ziel liegt bei 3,0 ATR, Stop bei 1,5 ATR -> CRV 2,0
    Stop zuerst   -1 R   der Stop ist die Definition von 1 R
    keines        ~0 R   die Position wird am Horizontende glattgestellt

Die Null fuer "keines" ist eine NAEHERUNG und die einzige Stelle mit Spielraum:
tatsaechlich endet der Fall irgendwo zwischen Stop und Ziel. Wer es genau will,
reicht `r_keines` aus der Kursreihe herein. Die Naeherung ist konservativ,
solange die Kosten separat abgezogen werden - sie unterstellt weder Gewinn noch
Verlust, wo beides moeglich waere.
"""
from __future__ import annotations

# Aus der Zonengeometrie abgeleitet (agent/szenario_fakten.py).
R_ZIEL = 2.0
R_STOP = -1.0
R_KEINES = 0.0

# Die Schwelle. Ein Erwartungswert knapp ueber null ist kein Grund zu handeln:
# jede Schaetzung hat Fehler, und ein Aufbau, der nur rechnerisch lohnt, wird
# vom Schaetzfehler aufgezehrt. 0,10 R Sicherheitsabstand entspricht rund
# einem Zehntel des Stop-Risikos.
MINDEST_ERWARTUNGSWERT_R = 0.10

# Ab welcher Modell-Unsicherheit gar nicht gehandelt wird. Das Modell nennt
# sie selbst; sie zu ignorieren hiesse, eine Information wegzuwerfen, die wir
# eigens erfragen.
UNSICHERHEIT_SPERRE = ("hoch",)


def erwartungswert_r(verteilung: dict, kosten_r: float = 0.0,
                     r_keines: float = R_KEINES) -> float | None:
    """Erwartungswert in R aus der geschaetzten Verteilung, nach Kosten."""
    if not verteilung:
        return None
    try:
        p_ziel = float(verteilung["ziel_zuerst_pct"]) / 100.0
        p_stop = float(verteilung["stop_zuerst_pct"]) / 100.0
        p_keines = float(verteilung["keines_pct"]) / 100.0
    except (KeyError, TypeError, ValueError):
        return None
    return round(p_ziel * R_ZIEL + p_stop * R_STOP + p_keines * r_keines
                 - abs(kosten_r), 4)


def leite_empfehlung_ab(verteilung: dict, *, kosten_r: float = 0.0,
                        unsicherheit: str | None = None,
                        mindest_ew: float = MINDEST_ERWARTUNGSWERT_R,
                        r_keines: float = R_KEINES) -> dict:
    """Die Empfehlung - mit der Rechnung, die zu ihr gefuehrt hat.

    Gibt IMMER die Rechnung mit zurueck, nicht nur das Ergebnis. Eine
    Empfehlung ohne nachvollziehbare Herleitung ist genau das, was wir
    abgeschafft haben."""
    ew = erwartungswert_r(verteilung, kosten_r, r_keines)
    if ew is None:
        return {"handeln": False, "grund": "keine auswertbare Verteilung",
                "erwartungswert_r": None}
    if unsicherheit in UNSICHERHEIT_SPERRE:
        return {"handeln": False,
                "grund": f"das Modell nennt seine Unsicherheit '{unsicherheit}'",
                "erwartungswert_r": ew, "schwelle_r": mindest_ew}
    handeln = ew >= mindest_ew
    return {
        "handeln": handeln,
        "grund": (f"Erwartungswert {ew:+.3f} R "
                  f"{'erreicht' if handeln else 'verfehlt'} die Schwelle "
                  f"{mindest_ew:+.2f} R"),
        "erwartungswert_r": ew,
        "schwelle_r": mindest_ew,
        "rechnung": {
            "ziel": f"{verteilung.get('ziel_zuerst_pct')} % x {R_ZIEL:+.1f} R",
            "stop": f"{verteilung.get('stop_zuerst_pct')} % x {R_STOP:+.1f} R",
            "keines": f"{verteilung.get('keines_pct')} % x {r_keines:+.1f} R",
            "kosten": f"-{abs(kosten_r):.3f} R",
        },
    }


def realisiertes_r(eingetreten: str, r_keines: float = R_KEINES) -> float | None:
    """Was der Aufbau TATSAECHLICH gebracht haette. Fuer die Nachrechnung.

    Nicht die Schaetzung, sondern das Ergebnis - damit sich eine
    Empfehlungsregel wirtschaftlich bewerten laesst und nicht nur ueber den
    Brier-Score. Ein Schaetzer kann gut kalibriert und trotzdem nutzlos sein,
    wenn er nie ueber die Handlungsschwelle kommt."""
    return {"ziel": R_ZIEL, "stop": R_STOP, "keines": r_keines}.get(eingetreten)
