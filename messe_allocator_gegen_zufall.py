"""Ist die Budget-Allocator-Auswahl besser als Zufall? (05.08.)

DIE FRAGE, die laut Zielgroessen-Doku (Messkette, Stufe 2) NIE gemessen wurde:
ueber die nie aufgerufenen Kandidaten weiss das System nichts. Der Allocator
waehlt taeglich aus einem Vielfachen dessen aus, was er dem LLM vorlegt - ob
diese Auswahl etwas beitraegt, ist unbekannt.

WARUM SIE JETZT LOHNT. Fuenf Selektionsmechanismen wurden inzwischen gemessen,
fuenfmal ohne Nachweis: Screening-Score diskriminiert nicht (04.08.), Konfidenz
traegt keine Information (05.08.), die Richtungswahl ist eine Regime-Wette
(05.08.), Prompt-Aenderungen liegen bei ~1 % des Eigenrauschens (04./05.08.),
und kein CRV-Band ist belastbar (05.08.). Der Allocator ist der letzte grosse
Auswahlschritt, der nie geprueft wurde.

UND DIE ANTWORT NUETZT IN BEIDE RICHTUNGEN:
  traegt er nichts -> die Auswahl kann entfallen, es koennen MEHR Kandidaten
                      durchgelassen werden. Dient direkt "mehr Signale".
  traegt er etwas  -> wir wissen endlich, wo Qualitaet herkommt.

DER SAUBERE VERGLEICH steckt im `status`-Feld der Trigger:
    llm_generiert  1.247  vom Allocator AUSGEWAEHLT, LLM-Aufruf erfolgt
    verfallen      2.669  war Kandidat, wurde NIE ausgewaehlt, ist abgelaufen
Beide Gruppen haben die Kandidatenschwelle passiert - der einzige Unterschied
ist die Auswahl. Ein Vergleich Kandidat gegen Nicht-Kandidat waere etwas
anderes (das misst das Screening, nicht den Allocator).

DIE SIMULATION ist fuer beide Gruppen IDENTISCH: Einstieg zum Schlusskurs des
Screening-Tages, Richtung aus dem Trigger, Bewertung ueber HORIZONT Tage. Kein
LLM, keine Zonen - genau deshalb ist der Vergleich fair. Was das LLM aus einem
Kandidaten macht, ist hier ausdruecklich NICHT die Frage; gemessen wird allein,
ob der Allocator die besseren Ausgangslagen auswaehlt.

KEIN VORAUSSCHAUEN: bewertet wird ausschliesslich der Verlauf NACH dem
Screening-Tag.

ERGEBNIS (05.08.): DIE FRAGE IST AN HISTORISCHEN DATEN NICHT BEANTWORTBAR -
und der Grund ist genau das, was heute abgebaut wurde.

Der erste Durchlauf sah nach einem Befund aus: ausgewaehlt -1,78 % gegen
verfallen +0,16 % Rendite. Die Richtungsmischung entlarvt ihn:

    llm_generiert   LONG 863 (98 %)   SHORT   16 ( 1 %)
    verfallen       LONG 141 ( 6 %)   SHORT 2046 (93 %)

Der Nur-Long-VORFILTER warf SHORT-Kandidaten vor dem LLM-Aufruf weg - sie
konnten nie den Status llm_generiert bekommen und verfielen. Der Vergleich
"ausgewaehlt gegen verfallen" war damit faktisch "LONG gegen SHORT", also
dieselbe Tautologie, an der schon die SHORT-Kante vom Vormittag scheiterte.

Innerhalb von LONG bleibt scheinbar etwas uebrig (-8,85 pp, Intervall
[-12,59 ; -0,37]), aber zwei Konfundierer entkraeften es:
  ZEIT    die 141 verfallenen LONG liegen fast alle im 16.-23.07., die 863
          ausgewaehlten verteilen sich ueber den ganzen Zeitraum
  SYMBOL  ONDO allein stellt 39 % der verfallenen LONG, die zwei groessten 60 %

Das Intervall schliesst null nur knapp aus und ruht auf 141 Faellen aus einer
Woche, dominiert von zwei Symbolen. Als Befund nicht tragfaehig.

WAS DARAUS FOLGT, und es ist die eigentliche Erkenntnis: der Vorfilter hat
diese Messung strukturell unmoeglich gemacht, solange er lief. Seit dem
05.08. ist er entfernt - ab jetzt haben beide Gruppen vergleichbare
Richtungsmischungen, und derselbe Aufbau liefert eine saubere Antwort. Die
Frage ist nicht unbeantwortbar, sie ist nur nicht RUECKWIRKEND beantwortbar.

Wiedervorlage: sobald genug verfallene UND ausgewaehlte Kandidaten aus der
Zeit nach dem 05.08. vorliegen - grob zwei bis drei Wochen. Dieses Skript
laeuft dann unveraendert, nur mit einem Datumsfilter ab 2026-08-05.

Lauf: python -u messe_allocator_gegen_zufall.py [--h 5]
"""
from __future__ import annotations

import io
import json
import random
import statistics
import sys
from collections import Counter, defaultdict

from backtest_llm1_historisch import lade_reihen
from datiere_einbruch import ORDNER

HORIZONT = 5


def _arg(name: str, default: int) -> int:
    if name in sys.argv:
        try:
            return int(sys.argv[sys.argv.index(name) + 1])
        except (IndexError, ValueError):
            pass
    return default


def simuliere(reihe, idx: int, ist_short: bool, horizont: int):
    """Rendite und guenstigster Ausschlag ueber `horizont` Tage, vorzeichen-
    richtig zur Trigger-Richtung. Bewusst OHNE Stop/Ziel: jede Zonenannahme
    waere eine zusaetzliche Regel, die beide Gruppen zwar gleich trifft, das
    Ergebnis aber von einer willkuerlichen Wahl abhaengig machen wuerde."""
    einstieg = reihe[idx].close
    fenster = reihe[idx + 1:idx + 1 + horizont]
    if not einstieg or einstieg <= 0 or not fenster:
        return None, None
    ende = fenster[-1].close
    rendite = (einstieg - ende) / einstieg if ist_short else (ende - einstieg) / einstieg
    extrem = min(k.low for k in fenster) if ist_short else max(k.high for k in fenster)
    guenstigst = ((einstieg - extrem) / einstieg if ist_short
                  else (extrem - einstieg) / einstieg)
    return rendite * 100, guenstigst * 100


def block_bootstrap(a, b, ziehungen=10000, seed=11):
    """Ueber SYMBOLE. Dieselben 35 Symbole tauchen tausendfach auf - naive
    Intervalle waeren hier besonders irrefuehrend."""
    def bloecke(daten):
        z = defaultdict(list)
        for sym, wert in daten:
            z[sym].append(wert)
        return list(z.values())

    ba, bb = bloecke(a), bloecke(b)
    rnd = random.Random(seed)
    diffs = []
    for _ in range(ziehungen):
        x = [w for _ in ba for w in rnd.choice(ba)]
        y = [w for _ in bb for w in rnd.choice(bb)]
        if x and y:
            diffs.append(statistics.fmean(x) - statistics.fmean(y))
    diffs.sort()
    return diffs[int(.025 * len(diffs))], diffs[int(.975 * len(diffs))], len(ba), len(bb)


def main() -> int:
    horizont = _arg("--h", HORIZONT)
    d = json.load(io.open(ORDNER + r"\notebook_diagnose.json", encoding="utf-8"))
    trigger = d["rohdaten_fuer_backtest"]["hebel_triggers_alle"]
    reihen = lade_reihen()
    index = {}
    for sym, reihe in reihen.items():
        index[sym] = {k.date: i for i, k in enumerate(reihe)}

    gruppen = {"ausgewaehlt (llm_generiert)": [], "verfallen (nie ausgewaehlt)": []}
    scores = {k: [] for k in gruppen}
    verworfen = Counter()
    for t in trigger:
        status = str(t.get("status") or "")
        if status == "llm_generiert":
            g = "ausgewaehlt (llm_generiert)"
        elif status == "verfallen":
            g = "verfallen (nie ausgewaehlt)"
        else:
            verworfen["Status weder llm_generiert noch verfallen"] += 1
            continue
        sym = t.get("symbol")
        reihe = reihen.get(sym)
        if not reihe:
            verworfen["keine Kursreihe"] += 1
            continue
        tag = str(t.get("screened_at") or "")[:10]
        idx = index[sym].get(tag)
        if idx is None:
            verworfen["Screening-Tag nicht in der Reihe"] += 1
            continue
        if len(reihe) - idx - 1 < horizont:
            verworfen["zu wenig Vorlauf"] += 1
            continue
        rendite, guenstigst = simuliere(
            reihe, idx, str(t.get("richtung") or "").upper() == "SHORT", horizont)
        if rendite is None:
            verworfen["nicht simulierbar"] += 1
            continue
        gruppen[g].append((sym, rendite, guenstigst))
        s = t.get("score_gesamt")
        if isinstance(s, (int, float)):
            scores[g].append(float(s))

    print("=" * 78)
    print(f"Allocator gegen Zufall - identische mechanische Simulation, "
          f"Horizont {horizont} Tage")
    print("=" * 78)
    print(f"  verworfen: {dict(verworfen)}")
    print()
    print(f"{'Gruppe':30s}{'n':>6s}{'Symbole':>9s}{'Score-Md':>10s}"
          f"{'Rendite %':>11s}{'guenstigst %':>14s}{'Anteil>0':>10s}")
    for g, werte in gruppen.items():
        if not werte:
            continue
        r = [x[1] for x in werte]
        m = [x[2] for x in werte]
        sc = scores[g]
        print(f"{g:30s}{len(werte):6d}{len({x[0] for x in werte}):9d}"
              f"{(statistics.median(sc) if sc else float('nan')):10.1f}"
              f"{statistics.fmean(r):11.2f}{statistics.fmean(m):14.2f}"
              f"{sum(1 for x in r if x > 0) / len(r) * 100:9.0f}%")

    a = [(x[0], x[1]) for x in gruppen["ausgewaehlt (llm_generiert)"]]
    b = [(x[0], x[1]) for x in gruppen["verfallen (nie ausgewaehlt)"]]
    if len(a) < 30 or len(b) < 30:
        print("\n  zu wenige Faelle fuer einen Vergleich")
        return 1

    print("\n" + "=" * 78)
    print("Waehlt der Allocator die besseren Ausgangslagen?")
    print("=" * 78)
    for label, feld in (("Rendite ueber das Fenster", 1), ("guenstigster Ausschlag", 2)):
        aa = [(x[0], x[feld]) for x in gruppen["ausgewaehlt (llm_generiert)"]]
        bb = [(x[0], x[feld]) for x in gruppen["verfallen (nie ausgewaehlt)"]]
        diff = (statistics.fmean([w for _, w in aa])
                - statistics.fmean([w for _, w in bb]))
        u, o, na, nb = block_bootstrap(aa, bb)
        urteil = ("Allocator waehlt BESSER" if u > 0 else
                  "Allocator waehlt SCHLECHTER" if o < 0 else
                  "kein Unterschied nachweisbar")
        print(f"  {label:26s} Differenz {diff:+6.2f} pp   "
              f"95%-Intervall [{u:+.2f} , {o:+.2f}]   {na}/{nb} Symbole   {urteil}")

    print("\n  Lesart: kein Unterschied heisst, die Auswahl traegt nichts bei -")
    print("  dann koennen MEHR Kandidaten durchgelassen werden, ohne Qualitaet")
    print("  zu verlieren. Das dient direkt dem Ziel 'mehr Signale'.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
