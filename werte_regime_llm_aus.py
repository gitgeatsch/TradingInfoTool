"""Auswertung des Regime-LLM-Tests ueber ALLE Laeufe zusammen (06.08.).

`teste_regime_llm.py` berichtet nur seinen eigenen Lauf. Aufstockungslaeufe
(--versatz) haengen ihre Antworten aber an dieselbe Datei an - erst ueber alle
zusammen entsteht die Stichprobe, die eine Aussage traegt.

WARUM AUFSTOCKEN PFLICHT IST: dieses Projekt ist zweimal darauf hereingefallen,
dass ein vielversprechender Zwischenstand beim Verdoppeln der Stichprobe
verschwand - Regel-Ablation +0,281 bei 12 Ankern gegen +0,014 bei 28,
Fakten-Test -0,734 bei 12 Faellen gegen -0,334 bei 24. Beide Male in der
erwarteten Richtung, beide Male weg.

GEPAART je (Symbol, Zeitpunkt): alle drei Arme sehen denselben Faktensatz, die
Symbolstreuung kuerzt sich damit heraus. Der Rauschboden ist die Streuung
zwischen A1 und A2 - zwei ARMEN MIT IDENTISCHER EINGABE. Ein Effekt unterhalb
davon ist nicht interpretierbar, egal wie gross sein t-Wert aussieht.
"""
from __future__ import annotations

import io
import json
import os
import random
import statistics
from collections import defaultdict

DATEI = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                     "data", "regime_llm_antworten.json")


def stop_abstand(a) -> float | None:
    try:
        e = (a["entry"]["usd_von"] + a["entry"]["usd_bis"]) / 2.0
        short = str(a.get("richtung", "LONG")).upper() == "SHORT"
        st = a["stop_loss"]["usd_bis" if short else "usd_von"]
    except (KeyError, TypeError):
        return None
    if not e or e <= 0 or st is None:
        return None
    w = abs(e - st) / e * 100
    return w if 0 < w < 60 else None


def crv(a) -> float | None:
    try:
        e = (a["entry"]["usd_von"] + a["entry"]["usd_bis"]) / 2.0
        short = str(a.get("richtung", "LONG")).upper() == "SHORT"
        st = a["stop_loss"]["usd_bis" if short else "usd_von"]
        tp = a["take_profit"]["usd_von" if short else "usd_bis"]
    except (KeyError, TypeError):
        return None
    if None in (e, st, tp) or abs(e - st) <= 0:
        return None
    v = abs(tp - e) / abs(e - st)
    return v if 0 < v < 50 else None


def bootstrap(werte: list[float], zieh: int = 5000):
    if len(werte) < 2:
        return (float("nan"), float("nan"))
    rng = random.Random(20260806)
    m = sorted(statistics.fmean(rng.choice(werte) for _ in werte) for _ in range(zieh))
    return (m[int(0.025 * len(m))], m[int(0.975 * len(m))])


def main() -> None:
    roh = json.load(io.open(DATEI, encoding="utf-8"))
    print(f"Antworten gesamt: {len(roh)}")

    arme = sorted({r["arm"] for r in roh})
    a1 = next(a for a in arme if a.startswith("A1"))
    a2 = next(a for a in arme if a.startswith("A2"))
    b = next(a for a in arme if a.startswith("B"))
    print(f"Arme: {arme}")

    je_fall: dict = defaultdict(lambda: defaultdict(list))
    for r in roh:
        schluessel = (r["symbol"], r["created_at"])
        je_fall[schluessel][r["arm"]].append(r["antwort"])

    vollstaendig = [k for k, v in je_fall.items() if all(n in v for n in (a1, a2, b))]
    print(f"Faelle mit allen drei Armen: {len(vollstaendig)} von {len(je_fall)}")

    print()
    print("=" * 84)
    print("AKTION")
    print("=" * 84)
    for arm in (a1, a2, b):
        akt = [str(x.get("action", "?")).upper()
               for k in vollstaendig for x in je_fall[k][arm]]
        er = sum(1 for x in akt if x == "ERÖFFNEN") / len(akt) * 100 if akt else float("nan")
        print(f"  {arm:22s} EROEFFNEN {er:5.1f} %   n={len(akt)}")

    for label, funk in (("Konfidenz", lambda a: a.get("confidence_pct")),
                        ("Stop-Abstand %", stop_abstand),
                        ("CRV", crv)):
        paare_b, paare_r = [], []
        for k in vollstaendig:
            werte = {}
            for arm in (a1, a2, b):
                v = [funk(x) for x in je_fall[k][arm]]
                v = [x for x in v if isinstance(x, (int, float))]
                if v:
                    werte[arm] = statistics.fmean(v)
            if len(werte) == 3:
                paare_b.append(werte[b] - werte[a1])
                paare_r.append(werte[a2] - werte[a1])
        print()
        print("=" * 84)
        print(f"{label.upper()}  -  gepaart, n={len(paare_b)}")
        print("=" * 84)
        if len(paare_b) < 3:
            print("  zu wenige vollstaendige Faelle")
            continue
        eff = statistics.fmean(paare_b)
        se = statistics.stdev(paare_b) / (len(paare_b) ** 0.5)
        rausch = statistics.stdev(paare_r)
        lo, hi = bootstrap(paare_b)
        print(f"  Wirkung (B - A1)   {eff:+8.3f}   SE {se:.3f}   "
              f"t {eff/se if se else 0:+6.2f}")
        print(f"  Bootstrap 95 %     [{lo:+.3f} ; {hi:+.3f}]")
        print(f"  RAUSCHBODEN (A2-A1) sd {rausch:.3f}   "
              f"Verhaeltnis |Effekt|/Rauschen {abs(eff)/rausch if rausch else 0:.2f}x")
        if lo > 0 or hi < 0:
            print("  -> Bootstrap-Intervall schliesst die Null AUS")
        else:
            print("  -> Bootstrap-Intervall enthaelt die Null - kein Nachweis")
        if abs(eff) < rausch:
            print("  -> Effekt KLEINER als das Eigenrauschen - nicht interpretierbar")
        # noetiges n fuer diesen Effekt
        if se > 0 and eff != 0:
            noetig = (1.96 * statistics.stdev(paare_b) / abs(eff)) ** 2
            print(f"  noetiges n fuer Nachweis dieser Effektgroesse: {noetig:.0f} "
                  f"(vorhanden {len(paare_b)})")


if __name__ == "__main__":
    main()
