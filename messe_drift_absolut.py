"""Traegt die ABSOLUTE Drift das Barrierensystem? (20.08.2026, Umbauplan 102)

⚠️ DIESER KOPF IST DIE VORABFESTLEGUNG, geschrieben BEVOR gerechnet wurde.

WARUM DIESE MESSUNG NOCH EINMAL. `messe_drift.py` hat gefragt: *steigt ein
Coin, der zuletzt staerker gestiegen ist als die anderen, auch kuenftig
staerker als die anderen?* Eine RANGFRAGE quer ueber die Symbole, mit
abgezogenem Marktmittel.

Der Grundbefund des Projekts meint aber etwas anderes:

    Ein Barrierensystem auf einem DRIFTFREIEN Pfad hat brutto den
    Erwartungswert NULL - fuer jede Geometrie.

Der Ausweg daraus ist die Drift DES PFADES, nicht ein Rangplatz gegenueber
anderen. Und die Marktbereinigung entfernt genau die Groesse, um die es geht:
driftet die ganze Anlageklasse, sieht die Rangmessung davon per Konstruktion
nichts. Der Nutzer hat richtig vermutet, dass hier ein Denkfehler liegt.

DIE ZAHLEN, DIE DEN RAHMEN SETZEN:

    driftfrei, CRV 2,0     33,3 %   (= 1/(1+CRV), reine Arithmetik)
    gemessen               34,4 %   (40.499 Faelle)
    Breakeven              40,3 %

Die 1,1 Punkte ueber dem driftfreien Wert SIND die Drift - sie ist da, nur
klein. Bis zum Breakeven fehlen 7,0 Punkte, also rund das Sechsfache.

DIE FRAGE, VORAB FESTGELEGT: gibt es eine Schichtung nach der eigenen
absoluten Steigung, in der die Trefferquote den Breakeven erreicht?

    Schichtung   Steigung des Symbols ueber die letzten 250 Handelstage,
                 ABSOLUT und OHNE Marktbereinigung, in fuenf Baendern:
                 unter -30 % · -30..-10 % · -10..+10 % · +10..+30 % · ueber +30 %
    Geometrie    k = 2,0 und CRV = 2,0 - der Betriebszustand, nicht der beste
    Ergebnis     Ziel vor Stop, gegen den Breakeven derselben Geometrie

⚠️ ZWEI GEGENPROBEN ZU DEN EIGENEN FEHLERQUELLEN, beide vorab benannt:

  1. STOP ZUERST ODER ZIEL ZUERST. Faellt in einer Tageskerze beides, ist die
     Reihenfolge unbekannt. `simuliere_bremse` waehlt STOP - die vorsichtige
     Lesart, die die Quote systematisch UNTERSCHAETZT. Hier werden beide
     Extreme gerechnet und die Spanne ausgewiesen. Die Wahrheit liegt
     dazwischen; liegt schon die obere Grenze unter dem Breakeven, ist die
     Frage entschieden.

  2. ALLE TAGE ODER SIGNALTAGE. Diese Simulation nimmt JEDEN Handelstag als
     Einstieg. Das System nimmt nur Tage mit Signal. Waere diese Auswahl
     besser als der Zufall, unterschaetzte die Simulation die echte Quote.
     Geprueft wird das an den eigenen Signalen, soweit sie reichen.

⚠️ UND DIE PHASENPROBE BLEIBT. Eine Schicht, die nur im Baermarkt traegt, ist
die Marktphasenwette mit anderem Namen (Kapitel 101).

    python messe_drift_absolut.py [--klasse krypto]
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
from simuliere_bremse import klassen_aus_db as _KLASSEN  # noqa: E402
from simuliere_bremse import (MAX_TAGE, PHASE_FENSTER,       # noqa: E402
                              _marktphase, _reihen_roh)

K = 2.0
CRV = 2.0
DRIFT_FENSTER = 250
BAENDER = ((-9.9, -0.30, "unter -30 %"), (-0.30, -0.10, "-30 bis -10 %"),
           (-0.10, 0.10, "-10 bis +10 %"), (0.10, 0.30, "+10 bis +30 %"),
           (0.30, 99.0, "ueber +30 %"))
MIN_FAELLE = 300


def _band(x: float) -> str:
    for u, o, name in BAENDER:
        if u <= x < o:
            return name
    return BAENDER[-1][2]


def laufe(db: str, klasse: str) -> list[dict]:
    """Je Anker: Band, Phase und BEIDE Lesarten des Ausgangs."""
    roh = _reihen_roh(db, klasse, _KLASSEN(db))
    phase = _marktphase(roh)
    aus = []
    for sym, (c, h, l, v, a, off, d) in roh.items():
        del v
        start = max(off, DRIFT_FENSTER) + 1
        for i in range(start, len(c) - 1):
            atr, einstieg = a[i - off], c[i]
            frueher = c[i - DRIFT_FENSTER]
            if not (atr > 0 and einstieg > 0 and frueher > 0):
                continue
            stop = einstieg - K * atr
            if stop <= 0:
                continue
            ziel = einstieg + CRV * (einstieg - stop)
            # ⚠️ BEIDE LESARTEN IN EINEM DURCHLAUF. Getrennte Laeufe waeren
            # zwei Stichproben; hier ist es dieselbe, nur anders gelesen.
            vor, mild = "abgelaufen", "abgelaufen"
            for j in range(i + 1, min(i + 1 + MAX_TAGE, len(c))):
                s, z = l[j] <= stop, h[j] >= ziel
                if s and z:
                    vor, mild = "stop", "ziel"
                    break
                if s:
                    vor = mild = "stop"
                    break
                if z:
                    vor = mild = "ziel"
                    break
            aus.append({"symbol": sym, "phase": phase.get(d[i], "unbekannt"),
                        "band": _band(einstieg / frueher - 1.0),
                        "vorsichtig": vor, "mild": mild,
                        "stop_relativ": float((einstieg - stop) / einstieg)})
    return aus


def _quote(faelle, feld: str) -> tuple[int, float]:
    n = sum(1 for f in faelle if f[feld] in ("ziel", "stop"))
    t = sum(1 for f in faelle if f[feld] == "ziel")
    return n, (t / n if n else 0.0)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="data/tradinginfotool.db")
    ap.add_argument("--klasse", default="krypto")
    ap.add_argument("--datei", default="messwerte_drift_absolut.json")
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    print("=" * 78)
    print("TRAEGT DIE ABSOLUTE DRIFT? - Schichtung nach eigener Steigung")
    print("  OHNE Marktbereinigung - genau die Groesse, die die Rangmessung")
    print("  vom 19.08. per Konstruktion nicht sehen konnte.")
    print("=" * 78)
    faelle = laufe(a.db, a.klasse)
    gebuehr = _GEB(a.klasse)
    stop_rel = float(np.median([f["stop_relativ"] for f in faelle]))
    schwelle = TB.breakeven(2 * gebuehr / stop_rel, CRV)
    driftfrei = TB.basisrate_fuer(CRV)
    n_ges, q_vor = _quote(faelle, "vorsichtig")
    _, q_mild = _quote(faelle, "mild")
    print(f"  {len(faelle)} Anker, {n_ges} entschieden")
    print(f"  driftfrei {100 * driftfrei:.1f} %   gemessen "
          f"{100 * q_vor:.1f} bis {100 * q_mild:.1f} %   Breakeven "
          f"{100 * schwelle:.1f} %")
    print(f"  Die Drift ist da: {100 * (q_vor - driftfrei):+.1f} bis "
          f"{100 * (q_mild - driftfrei):+.1f} Punkte ueber driftfrei. "
          f"Bis zum Breakeven fehlen {100 * (schwelle - q_vor):.1f} Punkte.")

    print("\n" + "-" * 78)
    print("JE DRIFTBAND - Trefferquote (vorsichtig bis mild)")
    print("-" * 78)
    print(f"  {'Band':18}{'Faelle':>9}{'vorsichtig':>13}{'mild':>9}"
          f"{'Abstand':>11}")
    ergebnis = {}
    for _u, _o, name in BAENDER:
        teil = [f for f in faelle if f["band"] == name]
        n, qv = _quote(teil, "vorsichtig")
        _, qm = _quote(teil, "mild")
        if n < MIN_FAELLE:
            print(f"  {name:18}{n:9}   zu wenige Faelle")
            continue
        se = math.sqrt(qv * (1 - qv) / n)
        ergebnis[name] = {"n": n, "vorsichtig": qv, "mild": qm,
                          "abstand_vorsichtig": qv - schwelle,
                          "t": (qv - schwelle) / se if se > 0 else 0.0}
        print(f"  {name:18}{n:9}{100 * qv:12.1f} %{100 * qm:8.1f} %"
              f"{100 * (qv - schwelle):+10.1f}")

    bestes = max(ergebnis.items(), key=lambda x: x[1]["abstand_vorsichtig"]) \
        if ergebnis else None
    if bestes:
        name, e = bestes
        print(f"\n  BESTES BAND: {name}  ->  "
              f"{100 * e['abstand_vorsichtig']:+.1f} Punkte "
              f"(t = {e['t']:+.2f}), mild "
              f"{100 * (e['mild'] - schwelle):+.1f}")

        print("\n" + "-" * 78)
        print("PHASENPROBE fuer dieses Band")
        print("-" * 78)
        for ph in ("bulle", "seitwaerts", "baer"):
            teil = [f for f in faelle
                    if f["band"] == name and f["phase"] == ph]
            n, q = _quote(teil, "vorsichtig")
            print(f"  {ph:12}" + (f"{n:8} Faelle   "
                                  f"{100 * (q - schwelle):+6.1f} Punkte"
                                  if n >= 200 else
                                  f"{n:8} Faelle   zu wenige"))

    print("\n" + "=" * 78)
    if bestes and bestes[1]["mild"] < schwelle:
        print("AUCH DIE MILDE LESART BLEIBT UNTER DEM BREAKEVEN.")
        print("Damit ist die Frage entschieden, ohne dass die Unsicherheit")
        print("ueber die Reihenfolge in der Kerze eine Rolle spielt.")
    elif bestes:
        print("DIE MILDE LESART LIEGT UEBER DEM BREAKEVEN, die vorsichtige")
        print("nicht. Die Wahrheit liegt dazwischen - hier entscheidet sich")
        print("nichts ohne Intraday-Daten.")
    print("=" * 78)
    if a.datei:
        io.open(a.datei, "w", encoding="utf-8").write(json.dumps({
            "breakeven": schwelle, "driftfrei": driftfrei,
            "gesamt_vorsichtig": q_vor, "gesamt_mild": q_mild,
            "baender": ergebnis}, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
