"""Warum empfiehlt LLM1 seit dem 31.07. mehrheitlich SHORT? (05.08.)

DIE FRAGE. Der SHORT-Anteil der Hebel-Signale springt am 31.07. binnen einer
Stunde von 0 % (11:00 UTC) auf 100 % (12:00 UTC) und bleibt danach bei
54-77 %. Auf Bitpanda ist SHORT nicht ausfuehrbar, also faellt seither der
Grossteil der Signale ins Nur-Long-Veto. Das ist der verbliebene ungeklaerte
Punkt aus dem Dead-Loop ("warum kommen so wenige Signale").

DIE GEGENPRUEFUNG, die der Nutzer verlangt hat, und sie ist die wichtigere
Haelfte: wenn die INDIKATOREN, die das Modell tatsaechlich sieht, zum selben
Zeitpunkt kippen, dann sind die SHORT-Empfehlungen schlicht RICHTIG - und es
gibt gar kein Modellproblem, sondern nur ein Ausfuehrungsproblem. Erst wenn
die Indikatoren stabil bleiben, waehrend die Empfehlungen kippen, liegt der
Fehler bei uns.

Bisher habe ich nur die rohe Kursbewegung geprueft (Median-Tagesbewegung ueber
41 Symbole: 21.-28.07. -0,46 %, 29.07.-05.08. -0,04 % - die spaetere Periode
war minimal BESSER). Das ist zu grob: das Modell entscheidet nicht auf der
Tagesbewegung, sondern auf EMA-Lage, RSI, MACD und vor allem auf der
Konfluenz-Gesamttendenz, die genau diese Einzelsignale zu einem bullish/
bearish-Urteil zusammenfasst.

WAS HIER GERECHNET WIRD, ist deshalb exakt der Indikatorsatz aus dem Betrieb -
build_technical_snapshot() und compute_confluence(), dieselben Funktionen, die
auch die Produktion aufruft, angewendet auf jeden Tag im Fenster. Keine
Nachbildung, kein Naeherungswert.

KEIN VORAUSSCHAUEN: die Kursreihe wird am jeweiligen Tag hart abgeschnitten
(_reihe_bis aus backtest_llm1_historisch), bevor ein Indikator gerechnet wird.

DATIERUNG WIE IM VORIGEN SCHRITT: der Trennpunkt wird GESUCHT, nicht gesetzt
(Max-Statistik ueber alle Trennpunkte, Block-Permutation ueber Symbole). Ein
selbst gewaehlter 31.07. waere hier derselbe Fehler wie beim 29.07.

Lauf: python -u pruefe_short_ursache.py
"""
from __future__ import annotations

import io
import json
import random
import statistics
from collections import Counter, defaultdict
from datetime import datetime

import numpy as np

from indicators.calculations import build_technical_snapshot, summarize_confluence
from backtest_llm1_historisch import _reihe_bis, lade_reihen, VORLAUF_MIN
from datiere_einbruch import ORDNER, max_statistik


def indikatorreihe(ab="2026-07-10", bis="2026-08-06"):
    """Je Symbol und Tag: die Konfluenz-Gesamttendenz und ihre Bestandteile,
    gerechnet mit den Produktionsfunktionen auf abgeschnittener Historie."""
    reihen = lade_reihen()
    raus = []
    for sym, reihe in sorted(reihen.items()):
        if len(reihe) < VORLAUF_MIN + 2 or len(reihe) > 1200:
            continue          # nur Krypto-Watchlist, keine 25-Jahre-Aktienreihen
        for i in range(VORLAUF_MIN, len(reihe)):
            tag = reihe[i].date
            if not (ab <= tag < bis):
                continue
            hist = _reihe_bis(reihe, i)
            closes = np.array([k.close for k in hist], dtype=float)
            dates = np.array([k.date for k in hist])
            try:
                snap = build_technical_snapshot(closes, dates, hist)
                konf = summarize_confluence(snap, float(closes[-1]))
            except Exception:
                continue
            raus.append({
                "tag": tag, "symbol": sym,
                "bias": str(getattr(konf, "overall_bias", "") or ""),
                "bull": int(getattr(konf, "bullish_count", 0) or 0),
                "bear": int(getattr(konf, "bearish_count", 0) or 0),
            })
    return raus


def main():
    print("=" * 78)
    print("A. Konfluenz-Gesamttendenz je Tag - kippt der Indikatorsatz?")
    print("=" * 78)
    daten = indikatorreihe()
    if not daten:
        print("  keine Indikatordaten berechenbar")
        return 1
    proTag = defaultdict(list)
    for z in daten:
        proTag[z["tag"]].append(z)
    print(f"  {len(daten)} Symbol-Tage, {len({z['symbol'] for z in daten})} Symbole\n")
    print(f"{'Tag':12s}{'n':>4s}{'bearish':>9s}{'bullish':>9s}{'neutral':>9s}"
          f"{'bear-Zaehler':>14s}")
    for tag in sorted(proTag):
        v = proTag[tag]
        c = Counter(z["bias"].lower() for z in v)
        be = sum(1 for z in v if "bear" in z["bias"].lower())
        bu = sum(1 for z in v if "bull" in z["bias"].lower())
        ne = len(v) - be - bu
        print(f"{tag:12s}{len(v):4d}{be * 100 // len(v):8d}%{bu * 100 // len(v):8d}%"
              f"{ne * 100 // len(v):8d}%{statistics.fmean(z['bear'] for z in v):14.2f}")

    print("\n" + "=" * 78)
    print("B. Trennpunkt SUCHEN - kippt der Indikatorsatz messbar, und wann?")
    print("=" * 78)
    rnd = random.Random(20260805)
    reihe = [(datetime.strptime(z["tag"], "%Y-%m-%d"), z["symbol"],
              1 if "bear" in z["bias"].lower() else 0, "") for z in daten]
    (diff, k, na, nb), p = max_statistik(reihe, ziehungen=3000, rnd=rnd)
    if k is None:
        print("  kein bewertbarer Trennpunkt")
    else:
        print(f"  Anteil bearish: bester Schnitt {k:%d.%m.}  {diff * 100:+.1f} pp  "
              f"(n {na}/{nb})  p={p:.4f}  "
              + ("SIGNIFIKANT" if p < 0.05 else "nicht signifikant"))

    print("\n" + "=" * 78)
    print("C. Zum Vergleich: der SHORT-Anteil der Signale, derselbe Test")
    print("=" * 78)
    d = json.load(io.open(ORDNER + r"\notebook_diagnose.json", encoding="utf-8"))
    sig = []
    for s in d["hebel_signals"]:
        t = str(s.get("created_at") or "")[:10]
        r = str(s.get("richtung") or "").upper()
        if t and r in ("LONG", "SHORT"):
            sig.append((datetime.strptime(t, "%Y-%m-%d"), s.get("symbol") or "?",
                        1 if r == "SHORT" else 0, ""))
    (diff, k, na, nb), p = max_statistik(sig, ziehungen=3000, rnd=rnd)
    if k is None:
        print("  kein bewertbarer Trennpunkt")
    else:
        print(f"  SHORT-Anteil:   bester Schnitt {k:%d.%m.}  {diff * 100:+.1f} pp  "
              f"(n {na}/{nb})  p={p:.4f}  "
              + ("SIGNIFIKANT" if p < 0.05 else "nicht signifikant"))
    print("\n  Fallen BEIDE Trennpunkte zusammen, folgt das Modell den Daten -")
    print("  dann ist der SHORT-Anteil richtig und nur nicht ausfuehrbar.")
    print("  Kippt nur der SHORT-Anteil, liegt der Fehler bei uns.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
