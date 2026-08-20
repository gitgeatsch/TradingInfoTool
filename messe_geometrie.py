"""Welche Geometrie traegt sich - und haengt sie an der Lage?
(20.08.2026, Umbauplan 101)

⚠️ DIESER KOPF IST DIE VORABFESTLEGUNG, geschrieben BEVOR gerechnet wurde.

DER GEDANKENGANG, DER HIERHER FUEHRT. Kapitel 100 hat gemessen: die
Trefferquote liegt im Baermarkt bei 42,4 % und im Bullenmarkt bei 28,1 %.
Der naheliegende Schluss waere ein Marktphasen-Filter - und der waere falsch.
"Im Bullenmarkt keine Longs" ist ein statisches Gate, also die Bauform, die
den Deadloop erzeugt hat.

DIE FRAGE IST EINE ANDERE, und der Nutzer hat sie so gestellt: *"das sollte
etwas weiter gedacht werden als ein einfaches Marktphasen-System"* und
*"wir koennten eine Kombination von weiteren Trichterwerten testen"*.

⚠️ WARUM PHASE UND GEOMETRIE DASSELBE THEMA SIND.

Unser Stop steht bei k x ATR, unser Ziel bei CRV x k x ATR. Im Baermarkt ist
der ATR gross, der Stop damit in PROZENT weit - und ein weiter Stop wirkt
zweimal:

    1. Er wird seltener vom Rauschen getroffen (der Trichter aus 93 A sagt
       genau das: liegt der Stop innerhalb der ueblichen Bewegung, faellt er
       auch ohne Gegenargument).
    2. Er SENKT DIE HUERDE. Die Kosten in R sind 2 x Gebuehr / Stopabstand -
       bei doppelt so weitem Stop also halb so gross, und damit sinkt der
       Breakeven.

Der Baermarkt-Befund koennte also gar nichts ueber den Baermarkt sagen,
sondern nur darueber, dass unsere Geometrie im ruhigen Markt ZU ENG ist.

DAS RASTER, VORAB FESTGELEGT:

    Stop-Vielfaches k    1,5 · 2,0 (heute) · 2,5 · 3,0 · 4,0
    Ziel-Verhaeltnis CRV 1,0 · 1,5 · 2,0 (heute) · 3,0

Zwanzig Kombinationen. Beide Reihen decken die Praxisstandards ab (Elder
2 ATR, Chandelier 3 ATR) und reichen nach beiden Seiten darueber hinaus.

DIE ENTSCHEIDENDE ZAHL IST NICHT DIE TREFFERQUOTE, SONDERN IHR ABSTAND ZUM
EIGENEN BREAKEVEN. Beide haengen an k und CRV, und zwar gegenlaeufig:

    Basisrate  1/(1+CRV)              faellt mit CRV
    Breakeven  (1+Kosten_R)/(1+CRV)   faellt auch, aber Kosten_R faellt mit k

Eine hohe Trefferquote bei CRV 1,0 ist nichts wert, wenn der Breakeven
mitwandert. Gemessen wird deshalb ausschliesslich `Quote minus Breakeven`.

⚠️ ZWANZIG FELDER SIND ZWANZIG VERSUCHE - ABER EIN PLACEBO PASST HIER NICHT.

Die erste Fassung wuerfelte die Ausgaenge ueber alle Felder und mass eine
Schwelle von |t| >= 104. Das ist kein strenger Massstab, sondern ein
kaputter: die Felder unterscheiden sich LEGITIM in ihrer Trefferquote - ein
Ziel bei CRV 1,0 wird oefter erreicht als eines bei CRV 3,0, und das ist
Arithmetik, kein Signal. Das Wuerfeln zerstoert genau diesen Unterschied und
erzeugt Abweichungen, die mit der Frage nichts zu tun haben.

DIE REGEL DAHINTER: eine Kontrolle muss ZUR FRAGE PASSEN. Ein Placebo prueft,
ob ein ZUSAMMENHANG zufaellig ist. Hier wird aber gefragt, ob eine Quote ueber
ihrem eigenen Breakeven liegt - und dafuer ist der Binomialfehler das richtige
Mass. Er steht als `t` in jedem Feld.

Gegen Rosinenpickerei hilft hier etwas anderes, und es ist strenger: das
Raster ist VORAB festgelegt, der Verlauf ueber ALLE zwanzig Felder wird
ausgewiesen (ein systematischer Verlauf ist mehr wert als ein Ausreisser),
und ein Befund muss in ALLEN DREI PHASEN stehen.

⚠️ UND DER BEFUND MUSS IN ALLEN DREI PHASEN STEHEN. Eine Geometrie, die nur
im Baermarkt traegt, ist die Marktphasenwette mit anderem Namen.

    python messe_geometrie.py [--klasse krypto]
"""
from __future__ import annotations

import argparse
import io
import json
import math
import sys

import numpy as np

sys.path.insert(0, ".")
from agent import trefferbilanz as TB                        # noqa: E402
from simuliere_bremse import gebuehr_je_seite as _GEB  # noqa: E402
from simuliere_bremse import (MAX_TAGE, PHASE_FENSTER,       # noqa: E402
                              PHASE_SCHWELLE, _atr, _marktphase,
                              _reihen_roh)

K_WERTE = (1.5, 2.0, 2.5, 3.0, 4.0)
CRV_WERTE = (1.0, 1.5, 2.0, 3.0)
MIN_FAELLE = 500


def laufe(db: str, klasse: str) -> list[dict]:
    """Je Anker und Geometrie den Ausgang - EINMAL durch die Reihen.

    ⚠️ ALLE ZWANZIG FELDER AUS DEMSELBEN ANKER. Wer je Feld neu anlaeuft,
    bekommt zwanzig verschiedene Stichproben und vergleicht Aepfel mit
    Birnen - die Unterschiede waeren dann teils Auswahl, teils Geometrie."""
    roh = _reihen_roh(db, klasse)
    phase = _marktphase(roh)
    aus = []
    for sym, (c, h, l, v, a, off, d) in roh.items():
        del v
        for i in range(off + PHASE_FENSTER, len(c) - 1):
            atr, einstieg = a[i - off], c[i]
            if not (atr > 0 and einstieg > 0):
                continue
            ph = phase.get(d[i], "unbekannt")
            for k in K_WERTE:
                stop = einstieg - k * atr
                if stop <= 0:
                    continue
                risiko = einstieg - stop
                for crv in CRV_WERTE:
                    ziel = einstieg + crv * risiko
                    ausgang = "abgelaufen"
                    for j in range(i + 1, min(i + 1 + MAX_TAGE, len(c))):
                        # Stop zuerst - die Kerze verraet die Reihenfolge
                        # nicht (dieselbe Regel wie in simuliere_bremse).
                        if l[j] <= stop:
                            ausgang = "stop"
                            break
                        if h[j] >= ziel:
                            ausgang = "ziel"
                            break
                    aus.append({"symbol": sym, "phase": ph, "k": k,
                                "crv": crv, "ausgang": ausgang,
                                "stop_relativ": float(risiko / einstieg)})
    return aus


def bewerte(faelle: list, klasse: str, mischen=None) -> dict:
    """Je Feld: Quote, Breakeven und der Abstand dazwischen."""
    gebuehr = _GEB(klasse)
    if mischen is not None:
        ausgaenge = list(mischen.permutation([f["ausgang"] for f in faelle]))
    else:
        ausgaenge = [f["ausgang"] for f in faelle]
    felder: dict = {}
    for f, ausg in zip(faelle, ausgaenge):
        e = felder.setdefault((f["k"], f["crv"]),
                              {"ziel": 0, "n": 0, "stop_rel": [],
                               "phase": {}})
        if ausg in ("ziel", "stop"):
            e["n"] += 1
            e["ziel"] += 1 if ausg == "ziel" else 0
            p = e["phase"].setdefault(f["phase"], {"ziel": 0, "n": 0})
            p["n"] += 1
            p["ziel"] += 1 if ausg == "ziel" else 0
        e["stop_rel"].append(f["stop_relativ"])
    aus = {}
    for (k, crv), e in felder.items():
        if e["n"] < MIN_FAELLE:
            continue
        stop_rel = float(np.median(e["stop_rel"]))
        kosten_r = 2 * gebuehr / stop_rel
        schwelle = TB.breakeven(kosten_r, crv)
        quote = e["ziel"] / e["n"]
        se = math.sqrt(quote * (1 - quote) / e["n"])
        aus[(k, crv)] = {
            "quote": quote, "breakeven": schwelle, "n": e["n"],
            "stop_relativ": stop_rel, "kosten_r": kosten_r,
            "abstand": quote - schwelle,
            "t": (quote - schwelle) / se if se > 0 else 0.0,
            "je_phase": {ph: (p["ziel"] / p["n"] - schwelle)
                         for ph, p in e["phase"].items() if p["n"] >= 200}}
    return aus


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="data/tradinginfotool.db")
    ap.add_argument("--klasse", default="krypto")
    ap.add_argument("--datei", default="messwerte_geometrie.json")
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    print("=" * 78)
    print("WELCHE GEOMETRIE TRAEGT SICH? - Stop-Vielfaches gegen CRV")
    print("  Gemessen wird NICHT die Quote, sondern ihr Abstand zum")
    print("  eigenen Breakeven - beide wandern mit k und CRV.")
    print("=" * 78)
    faelle = laufe(a.db, a.klasse)
    print(f"  {len(faelle)} Anker-Geometrie-Paare aus denselben Ankern")
    r = bewerte(faelle, a.klasse)

    print("\n" + "-" * 78)
    print("ABSTAND ZUM BREAKEVEN in Prozentpunkten (positiv = traegt sich)")
    print("-" * 78)
    print("     CRV " + "".join(f"{c:>12.1f}" for c in CRV_WERTE))
    for k in K_WERTE:
        zeile = f"  k={k:>4.1f} "
        for crv in CRV_WERTE:
            e = r.get((k, crv))
            zeile += (f"{100 * e['abstand']:>11.1f} " if e
                      else f"{'-':>12}")
        print(zeile)

    print("\n  Zum Vergleich - Quote und Breakeven je Feld (Auswahl):")
    for k in K_WERTE:
        for crv in CRV_WERTE:
            e = r.get((k, crv))
            if e and (k, crv) in ((2.0, 2.0), (K_WERTE[-1], CRV_WERTE[0])):
                print(f"    k={k}, CRV={crv}: Stop {100 * e['stop_relativ']:.1f} %, "
                      f"Kosten {e['kosten_r']:.2f} R, Quote "
                      f"{100 * e['quote']:.1f} %, Breakeven "
                      f"{100 * e['breakeven']:.1f} %")

    bestes = max(r.items(), key=lambda x: x[1]["abstand"]) if r else None
    if bestes:
        (k, crv), e = bestes
        print("\n" + "-" * 78)
        print(f"BESTES FELD: k={k}, CRV={crv}  ->  "
              f"{100 * e['abstand']:+.1f} Punkte  (t = {e['t']:+.2f})")
        print(f"  Quote {100 * e['quote']:.1f} % gegen Breakeven "
              f"{100 * e['breakeven']:.1f} %, {e['n']} entschiedene Faelle")
        print("  ⚠️ UND IN DEN PHASEN - eine Geometrie, die nur im Baermarkt")
        print("     traegt, ist die Marktphasenwette mit anderem Namen:")
        for ph in ("bulle", "seitwaerts", "baer"):
            w = e["je_phase"].get(ph)
            print(f"     {ph:12} " + (f"{100 * w:+6.1f} Punkte" if w is not None
                                      else "zu wenige Faelle"))
        alle_positiv = all(v is not None and v > 0
                           for v in (e["je_phase"].get(p)
                                     for p in ("bulle", "seitwaerts", "baer")))
        print("     -> " + ("in ALLEN drei Phasen positiv"
                            if alle_positiv else
                            "NICHT in allen Phasen positiv"))


    print("\n" + "=" * 78)
    if a.datei:
        io.open(a.datei, "w", encoding="utf-8").write(json.dumps(
            {f"k{k}_crv{c}": {kk: vv for kk, vv in v.items()
                              if kk != "je_phase"}
             for (k, c), v in r.items()}, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
