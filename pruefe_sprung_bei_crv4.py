"""Gegenpruefung des Befunds "Sprung bei CRV 4,0" (2026-08-06, Nutzer-Einwand).

WORUM ES GEHT. Am 04.08. wurde gemessen: Signale mit CRV >= 4,0 erreichen in
51,0 % der Faelle mindestens 1R (MFE), gegen 26-32 % in den Baendern darunter.
Daraus wurde Regel 36 abgeleitet ("bevorzuge CRV ueber 4,0"). Am 06.08. habe
ich diesen Sprung pauschal als "Trunkierungs-Artefakt" bezeichnet. Der Nutzer
hat widersprochen - zu Recht, denn ich habe zwei verschiedene Messgroessen
unter einem Etikett zusammengeworfen:

  MASS A "MFE >= 1R"     - hat der Kurs sich je um 1R zu meinen Gunsten bewegt?
                           Die Schwelle 1R ist FEST, unabhaengig vom CRV.
  MASS B "Ziel erreicht" - hat der Kurs CRV x R erreicht? Die Schwelle WAECHST
                           mit dem CRV.

Horizont-Trunkierung trifft nur MASS B: je hoeher das CRV, desto weiter das
Ziel, desto seltener wird es im endlichen Fenster erreicht. Auf MASS A wirkt
sie NICHT. Mein pauschales "Artefakt" war deshalb falsch adressiert.

ABER: auf MASS A wirkt ein ANDERER Mechanismus, und zwar in die
Gegenrichtung. CRV = Zielabstand / Stopabstand. Ein hohes CRV entsteht durch
ein weites Ziel ODER einen ENGEN STOP. Bei engem Stop ist 1R eine kleine
Kursbewegung - MFE >= 1R wird also mechanisch LEICHTER. Der Sprung bei 4,0
koennte damit "enge Stops erreichen 1R leicht" heissen statt "hohe CRV sind
bessere Setups".

Das ist genau der Fehlertyp, der in diesem Projekt schon mehrfach zugeschlagen
hat: eine Kennzahl, die zwei Dinge zugleich misst. Deshalb hier drei Schritte:

  1. Replikation - existiert der Sprung in den Daten ueberhaupt?
  2. Konfundierung - faellt der Stop-Abstand mit steigendem CRV?
  3. Kontrolle - haelt der Sprung INNERHALB gleicher Stop-Abstaende?

Schritt 3 ist die eigentliche Pruefung. Haelt der Sprung dort, ist er real und
Regel 36 war inhaltlich richtig. Haelt er nicht, misst er den Stop-Abstand.

Liest ausschliesslich den Notebook-Export, keine Produktiv-DB.
"""
from __future__ import annotations

import io
import json
import math
import os
import statistics

EXPORT = r"K:\My Drive\Claude_Austauschordner\Notebook_Analysedaten\notebook_diagnose.json"
BAENDER = [(2.0, 2.5), (2.5, 3.0), (3.0, 4.0), (4.0, 99.0)]


def lade_signale() -> list[dict]:
    d = json.load(io.open(EXPORT, encoding="utf-8"))
    faelle = []
    for s in d["hebel_signals"]:
        entry = s.get("entry_usd_von")
        stop = s.get("stop_loss_usd_von")
        ziel = s.get("take_profit_usd_von")
        if not all(isinstance(x, (int, float)) for x in (entry, stop, ziel)):
            continue
        if entry <= 0:
            continue
        stop_abstand = abs(entry - stop)
        ziel_abstand = abs(ziel - entry)
        if stop_abstand <= 0 or ziel_abstand <= 0:
            continue
        crv = ziel_abstand / stop_abstand
        # MFE aus dem reaelen ODER dem Schatten-Pfad - dieselbe Population wie
        # die 04.08.-Messung (333 der 491 Faelle stammten aus dem Veto-Schatten).
        mfe = s.get("outcome_max_realisiertes_crv")
        quelle = "real"
        if not isinstance(mfe, (int, float)):
            mfe = s.get("veto_outcome_max_realisiertes_crv")
            quelle = "schatten"
        if not isinstance(mfe, (int, float)):
            continue
        faelle.append({
            "symbol": s["symbol"],
            "crv": crv,
            "stop_rel": stop_abstand / entry * 100.0,   # in Prozent vom Einstieg
            "mfe": mfe,
            "erreichte_1r": mfe >= 1.0,
            "quelle": quelle,
        })
    return faelle


def wilson(treffer: int, n: int) -> tuple[float, float]:
    if n == 0:
        return (0.0, 0.0)
    z = 1.96
    p = treffer / n
    nenner = 1 + z * z / n
    mitte = (p + z * z / (2 * n)) / nenner
    rand = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / nenner
    return (max(0.0, (mitte - rand) * 100), min(100.0, (mitte + rand) * 100))


def band_von(crv: float):
    for lo, hi in BAENDER:
        if lo <= crv < hi:
            return (lo, hi)
    return None


def quote(gruppe: list[dict]) -> tuple[int, int, float]:
    n = len(gruppe)
    t = sum(1 for g in gruppe if g["erreichte_1r"])
    return t, n, (t / n * 100 if n else float("nan"))


def main() -> None:
    faelle = lade_signale()
    print(f"Auswertbare Signale mit Zonen UND MFE: {len(faelle)}")
    print(f"  davon real: {sum(1 for f in faelle if f['quelle']=='real')}, "
          f"Veto-Schatten: {sum(1 for f in faelle if f['quelle']=='schatten')}")
    print()

    print("=" * 78)
    print("SCHRITT 1 - Replikation: Anteil mit MFE >= 1R je CRV-Band")
    print("=" * 78)
    je_band: dict = {}
    for f in faelle:
        b = band_von(f["crv"])
        if b:
            je_band.setdefault(b, []).append(f)
    for b in BAENDER:
        g = je_band.get(b, [])
        t, n, q = quote(g)
        if n == 0:
            print(f"  CRV {b[0]:.1f}-{b[1]:.1f}: keine Faelle")
            continue
        lo, hi = wilson(t, n)
        stop_med = statistics.median([x["stop_rel"] for x in g])
        print(f"  CRV {b[0]:.1f}-{b[1]:.1f}: {q:5.1f} %  (n={n:3d}, "
              f"95%-KI [{lo:4.1f};{hi:5.1f}])   Median-Stop {stop_med:5.2f} %")
    print()

    print("=" * 78)
    print("SCHRITT 2 - Konfundierung: haengt der Stop-Abstand am CRV?")
    print("=" * 78)
    print("  Wenn hohe CRV vor allem durch ENGE Stops entstehen, ist 1R dort eine")
    print("  kleinere Kursbewegung - MFE >= 1R wird dann mechanisch leichter.")
    print()
    for b in BAENDER:
        g = je_band.get(b, [])
        if not g:
            continue
        stops = sorted(x["stop_rel"] for x in g)
        print(f"  CRV {b[0]:.1f}-{b[1]:.1f}: Stop-Abstand Median {statistics.median(stops):5.2f} %  "
              f"Q1 {stops[len(stops)//4]:5.2f} %  Q3 {stops[3*len(stops)//4]:5.2f} %")
    print()

    print("=" * 78)
    print("SCHRITT 3 - KONTROLLE: haelt der Sprung INNERHALB gleicher Stop-Breite?")
    print("=" * 78)
    alle_stops = sorted(f["stop_rel"] for f in faelle)
    grenzen = [alle_stops[len(alle_stops) // 3], alle_stops[2 * len(alle_stops) // 3]]
    print(f"  Stop-Terzile: eng < {grenzen[0]:.2f} %  |  mittel  |  weit > {grenzen[1]:.2f} %")
    print()
    for name, tief, hoch in (("eng   ", -1e9, grenzen[0]),
                             ("mittel", grenzen[0], grenzen[1]),
                             ("weit  ", grenzen[1], 1e9)):
        teil = [f for f in faelle if tief <= f["stop_rel"] < hoch]
        unter = [f for f in teil if 2.0 <= f["crv"] < 4.0]
        ueber = [f for f in teil if f["crv"] >= 4.0]
        tu, nu, qu = quote(unter)
        to, no, qo = quote(ueber)
        if nu == 0 or no == 0:
            print(f"  Stop {name}: zu duenn (CRV<4: n={nu}, CRV>=4: n={no})")
            continue
        lo_u, hi_u = wilson(tu, nu)
        lo_o, hi_o = wilson(to, no)
        diff = qo - qu
        ueberlappt = not (lo_o > hi_u or lo_u > hi_o)
        print(f"  Stop {name}: CRV 2-4 -> {qu:5.1f} % (n={nu:3d})   "
              f"CRV >=4 -> {qo:5.1f} % (n={no:3d})   Differenz {diff:+6.1f} pp"
              f"   {'KIs ueberlappen' if ueberlappt else 'KIs getrennt'}")
    print()

    print("=" * 78)
    print("SCHRITT 4 - Gegenprobe: trennt der Stop-Abstand ALLEIN, ohne CRV?")
    print("=" * 78)
    for name, tief, hoch in (("eng   ", -1e9, grenzen[0]),
                             ("mittel", grenzen[0], grenzen[1]),
                             ("weit  ", grenzen[1], 1e9)):
        teil = [f for f in faelle if tief <= f["stop_rel"] < hoch]
        t, n, q = quote(teil)
        lo, hi = wilson(t, n)
        print(f"  Stop {name}: {q:5.1f} % erreichen 1R  (n={n:3d}, KI [{lo:4.1f};{hi:5.1f}])")
    print()

    print("=" * 78)
    print("SCHRITT 5 - Symbol-Konzentration im Band CRV >= 4,0")
    print("=" * 78)
    ueber = [f for f in faelle if f["crv"] >= 4.0]
    zaehler: dict = {}
    for f in ueber:
        zaehler[f["symbol"]] = zaehler.get(f["symbol"], 0) + 1
    top = sorted(zaehler.items(), key=lambda x: -x[1])[:5]
    print(f"  n={len(ueber)}, {len(zaehler)} verschiedene Symbole")
    for sym, k in top:
        print(f"    {sym:12s} {k:3d} ({k/len(ueber)*100:.0f} %)")
    if top:
        ohne = [f for f in ueber if f["symbol"] != top[0][0]]
        t, n, q = quote(ohne)
        print(f"  ohne das groesste Symbol: {q:.1f} % (n={n})")


def schritt6_kipppunkt() -> None:
    """Der eigentliche Punkt (Nutzer-Formulierung 06.08.): "es geht nicht um den
    Wert, sondern wann dieser Wert alles zum Kippen bringt."

    MFE >= 1R und das TATSAECHLICHE Ergebnis zeigen bei engen Stops in
    entgegengesetzte Richtungen:
      - enger Stop -> 1R ist eine kleine Bewegung -> MFE >= 1R wird leicht
      - enger Stop -> wird haeufiger ausgeloest UND traegt je R mehr Kosten
    Eine Kennzahl, die das erste belohnt, empfiehlt genau das, was das zweite
    bestraft. Deshalb hier beide Groessen nebeneinander ueber dieselbe
    Stop-Achse - der Kipppunkt ist die Stelle, an der sie auseinanderlaufen."""
    d = json.load(io.open(EXPORT, encoding="utf-8"))
    faelle = []
    for s in d["hebel_signals"]:
        entry, stop = s.get("entry_usd_von"), s.get("stop_loss_usd_von")
        ziel = s.get("take_profit_usd_von")
        if not all(isinstance(x, (int, float)) for x in (entry, stop, ziel)) or entry <= 0:
            continue
        sa, za = abs(entry - stop), abs(ziel - entry)
        if sa <= 0 or za <= 0:
            continue
        mfe = s.get("outcome_max_realisiertes_crv")
        real = s.get("outcome_realisiertes_crv")
        if not isinstance(mfe, (int, float)):
            mfe, real = (s.get("veto_outcome_max_realisiertes_crv"),
                         s.get("veto_outcome_realisiertes_crv"))
        if not isinstance(mfe, (int, float)) or not isinstance(real, (int, float)):
            continue
        faelle.append({"stop_rel": sa / entry * 100.0, "crv": za / sa,
                       "mfe1r": mfe >= 1.0, "real": real})

    print()
    print("=" * 78)
    print("SCHRITT 6 - DER KIPPPUNKT: MFE >= 1R gegen das tatsaechliche Ergebnis")
    print("=" * 78)
    print(f"  Faelle mit MFE UND realisiertem Ergebnis: {len(faelle)}")
    print()
    print(f"  {'Stop-Abstand':>14s} | {'n':>4s} | {'MFE>=1R':>8s} | {'Ergebnis (EW in R)':>19s} | Urteil")
    print("  " + "-" * 74)
    stufen = [(0, 2), (2, 3), (3, 5), (5, 8), (8, 12), (12, 1e9)]
    for lo, hi in stufen:
        g = [f for f in faelle if lo <= f["stop_rel"] < hi]
        if len(g) < 8:
            continue
        mfe_q = sum(1 for x in g if x["mfe1r"]) / len(g) * 100
        ew = statistics.mean(x["real"] for x in g)
        label = f"{lo:.0f}-{hi:.0f} %" if hi < 1e9 else f"> {lo:.0f} %"
        urteil = ("MFE gut, Ergebnis SCHLECHT" if mfe_q >= 45 and ew < 0 else
                  "beide schwach" if ew < 0 else "beide tragen")
        print(f"  {label:>14s} | {len(g):4d} | {mfe_q:7.1f} % | {ew:+18.3f} | {urteil}")
    print()
    print("  Lesart: erreicht eine Stufe hohe MFE-Quoten bei negativem Erwartungswert,")
    print("  misst MFE dort die Stop-Enge und nicht die Signalqualitaet.")


if __name__ == "__main__":
    main()
    schritt6_kipppunkt()
