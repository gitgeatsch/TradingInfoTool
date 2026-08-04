"""Messverfahren fuer Prompt-Nebeneffekte (2026-08-04, Schritt 2).

DIE FRAGE. Aendert ein redundanter Fakt die LLM-Entscheidung ueberhaupt - oder
ist der Unterschied nur das normale Rauschen zwischen zwei identischen
Laeufen? Ohne diese Trennung ist jede Prompt-Aenderung ein Blindflug: das LLM
antwortet auf denselben Prompt nie zweimal exakt gleich.

DAS PROBLEM, DAS DAS VERFAHREN LOEST. Man kann nicht einfach "mit" gegen
"ohne" stellen und den Unterschied als Wirkung lesen. Ein LLM liefert auch bei
voellig unveraendertem Prompt unterschiedliche Antworten. Wer das ignoriert,
"findet" eine Wirkung bei jeder beliebigen Aenderung - und genau davor warnt
die Methodik (2.2, Einschraenkung: bei reinen Kontext-Aenderungen ist ein
hartes Vorher/Nachher oft NICHT isolierbar).

DIE LOESUNG: DREI ARME STATT ZWEI.

    A1  Prompt unveraendert
    A2  Prompt unveraendert  <- IDENTISCH zu A1, misst das Eigenrauschen
    B   Prompt ohne den fraglichen Fakt

Der Abstand A1<->A2 ist der Rauschboden. Nur was darueber hinausgeht, ist
Wirkung. Ohne A2 waere jede Zahl unbrauchbar.

GEMESSEN WIRD je Signal und Arm:
  - action              (ERÖFFNEN/HALTEN) - kategorisch, Uneinigkeitsrate
  - confidence_pct      - numerisch, Mittelwertverschiebung in Rauscheinheiten
  - stop_rel und CRV    - numerisch, aus den Zonen abgeleitet

`provider` ist eine Funktion (fakten_json) -> antwort_dict. Dadurch laesst
sich die gesamte Auswertung mit einem NACHGEBILDETEN LLM pruefen, bevor echtes
Kontingent verbraucht wird - siehe selbsttest() unten.
"""
from __future__ import annotations

import copy
import math
import statistics
from dataclasses import dataclass, field
from typing import Callable


@dataclass
class ArmErgebnis:
    """Alle Antworten EINES Arms fuer EIN Signal."""

    actions: list[str] = field(default_factory=list)
    konfidenzen: list[float] = field(default_factory=list)
    stop_rel: list[float] = field(default_factory=list)
    crv: list[float] = field(default_factory=list)


@dataclass
class Befund:
    fakt: str
    n_signale: int
    wiederholungen: int
    # Uneinigkeit in der action: Anteil unterschiedlicher Entscheidungen
    action_rauschen: float          # A1 gegen A2
    action_wirkung: float           # A1 gegen B
    # Konfidenz: Verschiebung, gemessen in Vielfachen des Eigenrauschens
    konfidenz_rauschen: float
    konfidenz_wirkung: float
    signal_rausch_verhaeltnis: float | None
    urteil: str


def _entferne_pfad(fakten: dict, pfad: str) -> dict:
    """Kopie ohne den Fakt. `pfad` mit Punkten, z.B. 'antizyklisch.funding_rate_perzentil'."""
    kopie = copy.deepcopy(fakten)
    teile = pfad.split(".")
    knoten = kopie
    for t in teile[:-1]:
        if not isinstance(knoten, dict) or t not in knoten:
            return kopie          # Pfad nicht vorhanden - unveraendert zurueck
        knoten = knoten[t]
    if isinstance(knoten, dict):
        knoten.pop(teile[-1], None)
    return kopie


def _zonen_kennwerte(antwort: dict) -> tuple[float | None, float | None]:
    """(stop_rel, crv) aus einer LLM-Antwort, oder (None, None)."""
    try:
        e = antwort["entry"]
        entry = (e["usd_von"] + e["usd_bis"]) / 2.0
        stop = antwort["stop_loss"]["usd_von"]
        ziel = antwort["take_profit"]["usd_von"]
    except (KeyError, TypeError, ZeroDivisionError):
        return None, None
    if not entry or entry <= 0:
        return None, None
    risiko = entry - stop
    if risiko <= 0:
        return None, None
    return risiko / entry, (ziel - entry) / risiko


def _sammle(provider: Callable[[dict], dict], fakten: dict,
            wiederholungen: int) -> ArmErgebnis:
    arm = ArmErgebnis()
    for _ in range(wiederholungen):
        a = provider(fakten) or {}
        arm.actions.append(str(a.get("action", "?")).upper())
        k = a.get("confidence_pct")
        if isinstance(k, (int, float)):
            arm.konfidenzen.append(float(k))
        s, c = _zonen_kennwerte(a)
        if s is not None:
            arm.stop_rel.append(s)
            arm.crv.append(c)
    return arm


def _uneinigkeit(a: list[str], b: list[str]) -> float:
    """Anteil unterschiedlicher Entscheidungen bei paarweisem Vergleich.

    Verglichen wird die VERTEILUNG, nicht Lauf gegen Lauf - die Reihenfolge
    ist bedeutungslos, weil das LLM nicht deterministisch ist."""
    if not a or not b:
        return 0.0
    von_a = {x: a.count(x) / len(a) for x in set(a) | set(b)}
    von_b = {x: b.count(x) / len(b) for x in set(a) | set(b)}
    # Totalvariationsabstand: 0 = gleiche Verteilung, 1 = voellig verschieden
    return 0.5 * sum(abs(von_a[x] - von_b[x]) for x in von_a)


def messe_fakt(provider: Callable[[dict], dict], fakten_je_signal: list[dict],
               pfad: str, wiederholungen: int = 5) -> Befund:
    """Misst, ob das Entfernen von `pfad` mehr bewirkt als das Eigenrauschen."""
    a_rausch, a_wirk = [], []
    k_rausch, k_wirk, k_streu = [], [], []

    for fakten in fakten_je_signal:
        a1 = _sammle(provider, fakten, wiederholungen)
        a2 = _sammle(provider, fakten, wiederholungen)          # identisch!
        b = _sammle(provider, _entferne_pfad(fakten, pfad), wiederholungen)

        a_rausch.append(_uneinigkeit(a1.actions, a2.actions))
        a_wirk.append(_uneinigkeit(a1.actions, b.actions))

        if a1.konfidenzen and a2.konfidenzen and b.konfidenzen:
            m1, m2, mb = (statistics.fmean(x.konfidenzen) for x in (a1, a2, b))
            k_rausch.append(abs(m1 - m2))
            k_wirk.append(abs(m1 - mb))
            alle = a1.konfidenzen + a2.konfidenzen
            if len(alle) > 1:
                k_streu.append(statistics.stdev(alle))

    ar = statistics.fmean(a_rausch) if a_rausch else 0.0
    aw = statistics.fmean(a_wirk) if a_wirk else 0.0
    kr = statistics.fmean(k_rausch) if k_rausch else 0.0
    kw = statistics.fmean(k_wirk) if k_wirk else 0.0

    # Signal-Rausch-Verhaeltnis: Wirkung geteilt durch Eigenrauschen.
    # Unter 1 heisst: der Fakt bewegt weniger als zwei identische Laeufe.
    nenner = max(ar, 1e-9) if ar > 0 else None
    srv_action = (aw / ar) if ar > 1e-9 else None
    srv_konf = (kw / kr) if kr > 1e-9 else None
    kandidaten = [x for x in (srv_action, srv_konf) if x is not None]
    srv = max(kandidaten) if kandidaten else None

    if srv is None:
        urteil = "unbestimmt (kein Rauschen messbar - Wiederholungen erhoehen)"
    elif srv < 1.0:
        urteil = "KEINE nachweisbare Wirkung - bewegt weniger als das Eigenrauschen"
    elif srv < 2.0:
        urteil = "schwache Wirkung, im Bereich des Rauschens - nicht belastbar"
    else:
        urteil = f"WIRKUNG nachweisbar ({srv:.1f}-faches Eigenrauschen)"

    return Befund(
        fakt=pfad, n_signale=len(fakten_je_signal), wiederholungen=wiederholungen,
        action_rauschen=ar, action_wirkung=aw,
        konfidenz_rauschen=kr, konfidenz_wirkung=kw,
        signal_rausch_verhaeltnis=srv, urteil=urteil)


def bericht(b: Befund) -> str:
    return (
        f"{b.fakt}\n"
        f"  {b.n_signale} Signale x {b.wiederholungen} Wiederholungen x 3 Arme\n"
        f"  action     Rauschen {b.action_rauschen:.3f}   Wirkung {b.action_wirkung:.3f}\n"
        f"  Konfidenz  Rauschen {b.konfidenz_rauschen:.2f} pp   "
        f"Wirkung {b.konfidenz_wirkung:.2f} pp\n"
        f"  -> {b.urteil}")


# --- Selbsttest mit nachgebildetem LLM -------------------------------------
def selbsttest() -> int:
    """Prueft die Auswertung, BEVOR echtes Kontingent verbraucht wird.

    Zwei kuenstliche LLMs mit bekannter Wahrheit:
      - eines ignoriert den Fakt vollstaendig  -> Verfahren MUSS "keine
        Wirkung" melden
      - eines haengt stark daran               -> Verfahren MUSS "Wirkung"
        melden
    Beide rauschen gleich stark. Findet das Verfahren den Unterschied nicht,
    ist es unbrauchbar - und das faellt hier auf, nicht nach 150 API-Aufrufen."""
    import random

    rng = random.Random(20260804)
    PFAD = "antizyklisch.funding_rate_perzentil"

    def basis_fakten(i: int) -> dict:
        return {"asset": {"symbol": f"T{i}"},
                "antizyklisch": {"funding_rate_perzentil": 50.0 + i * 5,
                                 "long_konten_anteil_prozent": 60.0},
                "preis": {"usd": 100.0}}

    def antwort(konf: float) -> dict:
        return {"action": "ERÖFFNEN" if konf >= 60 else "HALTEN",
                "confidence_pct": konf,
                "entry": {"usd_von": 99.0, "usd_bis": 101.0},
                "stop_loss": {"usd_von": 95.0},
                "take_profit": {"usd_von": 110.0}}

    def taub(fakten):
        """Ignoriert den Fakt - nur Rauschen."""
        return antwort(62.0 + rng.gauss(0, 4))

    def empfindlich(fakten):
        """Haengt stark am Fakt."""
        p = (fakten.get("antizyklisch") or {}).get("funding_rate_perzentil")
        versatz = 0.0 if p is None else -14.0
        return antwort(62.0 + versatz + rng.gauss(0, 4))

    signale = [basis_fakten(i) for i in range(6)]
    fehler = []
    print("=== Selbsttest mit nachgebildetem LLM ===")
    for name, prov, erwartet_wirkung in (("taub (ignoriert den Fakt)", taub, False),
                                         ("empfindlich (haengt daran)", empfindlich, True)):
        b = messe_fakt(prov, signale, PFAD, wiederholungen=12)
        print()
        print(f"--- {name} ---")
        print(bericht(b))
        hat = b.signal_rausch_verhaeltnis is not None and b.signal_rausch_verhaeltnis >= 2.0
        ok = hat == erwartet_wirkung
        print(f"  {'OK  ' if ok else 'FEHL'}  erwartet: "
              f"{'Wirkung' if erwartet_wirkung else 'keine Wirkung'}")
        if not ok:
            fehler.append(name)

    print()
    if fehler:
        print(f"FEHLGESCHLAGEN: {fehler}")
        return 1
    print("Verfahren trennt Wirkung von Rauschen. Bereit fuer echte LLM-Laeufe.")
    return 0


if __name__ == "__main__":
    raise SystemExit(selbsttest())
