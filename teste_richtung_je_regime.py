"""Ist SHORT generell besser - oder nur im fallenden Markt? (05.08.)

DER OFFENE PUNKT. Der Lauf auf echten Faktensaetzen (teste_richtung_und_zonen.py)
ergab: SHORT schlaegt LONG um 1,012 R, Block-Bootstrap ueber Symbole
[-1,737 , -0,412], 0 % der Ziehungen >= 0. Der Vorbehalt war groesser als der
Befund: alle 14 Ankerpunkte lagen im Zeitraum 26.-29.07., 11 von 14
Bewertungsfenstern FIELEN (Median -1,87 %), und es waren nur 7 Symbole.
"SHORT gewinnt, wenn der Markt faellt" ist keine Kante, sondern eine
Tautologie.

DIESER LAUF LOEST DAS AUF, indem er BEIDE Regime mit DERSELBEN Faktenquelle
misst - das ist der entscheidende Unterschied zu einem Vergleich gegen den
vorigen Lauf, der echte Faktensaetze nutzte und damit eine zweite Variable
eingefuehrt haette.

    steigend  2026-04   Median 5-Tage-Rendite +1,73 %, 62 % steigend
    fallend   2026-01   Median 5-Tage-Rendite -4,76 %, 25 % steigend

Beide sind ganze MONATE, keine ausgesuchten Tage. Das ist Absicht: haette ich
Ankerpunkte danach gewaehlt, ob der Kurs danach stieg, waere die Auswahl
selbst schon eine Vorwegnahme des Ergebnisses. Ein Monat ist ein Regime, kein
Rosinenpicken.

WAS DIESER AUFBAU NICHT KANN, und das gehoert vorweg: er nutzt REKONSTRUIERTE
Faktensaetze (baue_historische_fakten), keine echten aus facts_json - echte
gibt es nur fuer den 26.07.-05.08., und der ist durchgehend fallend. Die
rekonstruierten sind duenner: es fehlen Funding-Rate, Open Interest,
Fear&Greed, historische Erfolgsquote und Marktkontext. Fuer die Frage
"EROEFFNEN oder HALTEN" ist dieser Satz nachweislich zu duenn (das Modell
eroeffnet zu 94-100 %). Fuer die Frage "welche RICHTUNG, und wie gut sind die
ZONEN" ist er brauchbar, weil beide Richtungen denselben Satz sehen. Der
absolute R-Wert ist damit aber nicht mit Produktionszahlen vergleichbar - nur
der Vergleich LONG gegen SHORT innerhalb desselben Regimes, und der Vergleich
der beiden Regime miteinander.

BEWERTUNGSFENSTER 5 Tage, wie im vorigen Lauf und wie der vereinbarte Rahmen
"0 bis max. 5 Tage".

Lauf: python -u teste_richtung_je_regime.py [--n 8] [--w 3]
"""
from __future__ import annotations

import io
import os
import random
import re
import statistics
from collections import Counter, defaultdict

import backtest_llm1_historisch as bt
from agent.krypto.hebel_analyst import SYSTEM_PROMPT
from api.mistral import MistralClient
from backtest_llm1_historisch import (
    VORLAUF_MIN, _arg, baue_historische_fakten, bewerte, frage, lade_reihen,
)

HORIZONT_TAGE = 5
REGIME = {"steigend (2026-04)": "2026-04", "fallend (2026-01)": "2026-01"}


def anker_im_monat(reihen, monat: str, n: int):
    kand = []
    for sym, reihe in sorted(reihen.items()):
        if not (VORLAUF_MIN + 20 < len(reihe) <= 1200):
            continue          # nur Krypto-Watchlist
        for i in range(VORLAUF_MIN, len(reihe) - HORIZONT_TAGE - 1):
            if reihe[i].date[:7] == monat:
                kand.append((sym, i, reihe[i].date))
    kand.sort(key=lambda x: (x[2], x[0]))
    return kand[:: max(1, len(kand) // n)][:n]


def main() -> int:
    key = os.environ.get("MISTRAL_API_KEY")
    if not key:
        for z in io.open(".env", encoding="utf-8", errors="replace"):
            m = re.match(r"\s*([A-Z_]+)\s*=\s*(.*)", z)
            if m:
                os.environ.setdefault(m.group(1), m.group(2).strip().strip('"').strip("'"))
        key = os.environ.get("MISTRAL_API_KEY")
    if not key:
        print("MISTRAL_API_KEY fehlt")
        return 1

    bt.HORIZONT = HORIZONT_TAGE
    n, w = _arg("--n", 8), _arg("--w", 3)
    reihen = lade_reihen()
    btc = reihen.get("BTC")

    plan = {}
    for label, monat in REGIME.items():
        plan[label] = anker_im_monat(reihen, monat, n)
        tage = [t for _, _, t in plan[label]]
        print(f"  {label:22s} {len(plan[label])} Anker, "
              f"{len({s for s, _, _ in plan[label]})} Symbole, {tage[0]} .. {tage[-1]}")
    gesamt = sum(len(v) for v in plan.values()) * 2 * w
    print(f"  {gesamt} Aufrufe (2 Arme je Anker, {w} Wiederholungen)")

    client = MistralClient(api_key=key)
    # (regime, arm, richtung) -> R-Werte;  (regime, symbol, richtung) fuer Bootstrap
    r_werte: dict[tuple, list[float]] = defaultdict(list)
    r_je_symbol: dict[str, list[tuple]] = defaultdict(list)
    richtungen: dict[tuple, list[str]] = defaultdict(list)
    aktionen: dict[str, list[str]] = defaultdict(list)

    for label, anker in plan.items():
        print(f"\n{'=' * 78}\n{label}\n{'=' * 78}", flush=True)
        for sym, i, tag in anker:
            fakten = baue_historische_fakten(sym, reihen[sym], i, btc)
            if fakten is None:
                continue
            zeile = []
            for arm in ("A1", "A2 (Rauschen)"):
                for _ in range(w):
                    a = frage(client, fakten, SYSTEM_PROMPT)
                    if not a:
                        continue
                    akt = str(a.get("action", "?")).upper()
                    aktionen[label].append(akt)
                    if akt not in ("ERÖFFNEN", "EROEFFNEN"):
                        zeile.append("HALTEN")
                        continue
                    ric = str(a.get("richtung", "?")).upper()
                    richtungen[(label, arm)].append(ric)
                    r = bewerte(a, reihen[sym], i)
                    if r is not None and ric in ("LONG", "SHORT"):
                        r_werte[(label, arm, ric)].append(r)
                        r_je_symbol[label].append((sym, ric, r))
                    zeile.append(f"{ric[:1]}{'/' + format(r, '.2f') if r is not None else ''}")
            print(f"  {sym:9s} {tag}  {zeile}", flush=True)

    print("\n" + "=" * 78)
    print("1. RICHTUNGSWAHL je Regime")
    print("=" * 78)
    for label in plan:
        r = [x for arm in ("A1", "A2 (Rauschen)") for x in richtungen.get((label, arm), [])]
        a = aktionen.get(label, [])
        if not r or not a:
            continue
        lo = sum(1 for x in r if x == "LONG") / len(r)
        er = sum(1 for x in a if x in ("ERÖFFNEN", "EROEFFNEN")) / len(a)
        print(f"  {label:22s} EROEFFNEN {er * 100:3.0f}%   "
              f"LONG {lo * 100:3.0f}%   SHORT {(1 - lo) * 100:3.0f}%   (n={len(r)})")

    print("\n" + "=" * 78)
    print("2. ZONENQUALITAET je Regime und Richtung")
    print("=" * 78)
    print(f"  {'Regime':22s}{'Richtung':>9s}{'n':>5s}{'EW R':>9s}{'Median':>9s}{'Anteil>0':>10s}")
    for label in plan:
        for ric in ("LONG", "SHORT"):
            v = [x for arm in ("A1", "A2 (Rauschen)")
                 for x in r_werte.get((label, arm, ric), [])]
            if not v:
                continue
            print(f"  {label:22s}{ric:>9s}{len(v):5d}{statistics.fmean(v):9.3f}"
                  f"{statistics.median(v):9.3f}"
                  f"{sum(1 for x in v if x > 0) / len(v) * 100:9.0f}%")

    print("\n" + "=" * 78)
    print("3. DIE FRAGE: schlaegt SHORT auch im STEIGENDEN Markt?")
    print("=" * 78)
    rnd = random.Random(20260805)
    for label in plan:
        daten = r_je_symbol.get(label, [])
        lo = [r for _, ric, r in daten if ric == "LONG"]
        sh = [r for _, ric, r in daten if ric == "SHORT"]
        if len(lo) < 3 or len(sh) < 3:
            print(f"  {label:22s} zu wenige Faelle "
                  f"(LONG {len(lo)}, SHORT {len(sh)}) - nicht bewertbar")
            continue
        blk = defaultdict(list)
        for sym, ric, r in daten:
            blk[sym].append((ric, r))
        b = list(blk.values())
        diffs = []
        for _ in range(10000):
            zieh = [x for _ in b for x in rnd.choice(b)]
            l = [r for ric, r in zieh if ric == "LONG"]
            s = [r for ric, r in zieh if ric == "SHORT"]
            if l and s:
                diffs.append(statistics.fmean(l) - statistics.fmean(s))
        diffs.sort()
        u, o = diffs[int(.025 * len(diffs))], diffs[int(.975 * len(diffs))]
        d = statistics.fmean(lo) - statistics.fmean(sh)
        urteil = ("SHORT besser" if o < 0 else "LONG besser" if u > 0
                  else "nicht unterscheidbar")
        print(f"  {label:22s} LONG minus SHORT {d:+6.3f} R   "
              f"95%-Intervall [{u:+.3f} , {o:+.3f}]   {len(b)} Symbole   {urteil}")

    print("\n  Lesart: kippt das Vorzeichen zwischen den beiden Regimen, ist die")
    print("  Richtungswahl eine Regime-Wette und keine Kante des Modells. Bleibt")
    print("  SHORT in BEIDEN besser, waere das ein echter Befund - dann kostet")
    print("  der Nur-Long-Veto tatsaechlich dauerhaft Ertrag.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
