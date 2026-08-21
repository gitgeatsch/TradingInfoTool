"""Der Drift, zerlegt statt gerichtet (20.08.2026, Umbauplan 113)

⚠️ DIESER KOPF IST DIE VORABFESTLEGUNG, geschrieben BEVOR gerechnet wurde.

WARUM NOCH EINMAL. Kapitel 102 hat den Drift gemessen und weggelegt: "kein
Band erreicht den Breakeven". Das war die HANDELSfrage. Die INFORMATIONSfrage
wurde nie gestellt - und die Zahlen von damals sind bemerkenswert:

    unter -30 %     36,2 %        -30 bis -10 %   27,8 %
    -10 bis +10 %   29,0 %        +10 bis +30 %   34,2 %
    ueber +30 %     35,9 %

⚠️ DIE SPANNE BETRAEGT 8,4 PUNKTE - doppelt so viel wie der Strukturvorsprung
von H (+4,0), den Kapitel 111 als ersten bestaetigten Befund ausweist. Der
Drift TRENNT also stark; er trennt nur nicht ueber die Kostenlinie. Genau das
ist der Unterschied, den Methodik 2.51 verlangt zu berichten.

⚠️ UND DIESE PRUEFUNG IST AUSSERHALB DER EIGENEN DATEN. Kapitel 102 lief auf
39 Reihen. Die 347 Reihen der Messdatenbank hat diese Hypothese NIE gesehen -
es ist keine Wiederholung, sondern ein echter Nachweis an neuen Reihen.

DREI FRAGEN, alle vorab benannt:

    D1  DIE U-FORM      Traegt die Beobachtung aus 102 auch auf 347 Reihen?
                        Vorhergesagt: die Extrembaender (|Drift| gross)
                        treffen oefter als die Mitte.

    D2  DIE KOSTEN      Ueberlebt sie die Bereinigung um den Stopabstand?
                        Der Verdacht ist konkret: starker Trend heisst hoher
                        ATR heisst weiter Stop heisst niedrigere Huerde -
                        derselbe Kanal wie in den Kapiteln 100-103.

    D3  GEGEN H         Traegt der Drift etwas, das H nicht schon hat?
                        Gemessen in BEIDE Richtungen: H innerhalb der
                        Driftbaender, und Drift innerhalb/ausserhalb von H.

⚠️ DREI FRAGEN SIND EIN PREIS (2.49). Ausgewiesen werden die Einzelschwelle
UND die Schwelle fuer das Maximum aus dreien.

⚠️ ZERLEGT, NICHT GERICHTET (2.51). Zu jeder Zahl steht der ABSOLUTE Abstand
zum Breakeven daneben. Eine Groesse, die trennt aber nicht traegt, ist ein
Ergebnis - sie kann mit einer zweiten zusammen tragen, und sie kann eine
bessere Groesse an derselben Stelle sein.

    python messe_drift_zerlegt.py [--blockplacebo 120]
"""
from __future__ import annotations

import argparse
import io
import json
import math
import sys

import numpy as np

sys.path.insert(0, ".")
from messe_drift_absolut import BAENDER as DRIFT_BAENDER        # noqa: E402
from messe_drift_absolut import _band                           # noqa: E402
from messe_marken import bewerte, laufe                         # noqa: E402
from messe_struktur_bereinigt import MINDESTALTER, _reif         # noqa: E402

MIN_FAELLE = 300
BLOCKLAENGE = 250
STOPBAENDER = 5
EXTREM = ("unter -30 %", "ueber +30 %")
MITTE = "-10 bis +10 %"


def _quote(faelle) -> tuple[int, float]:
    ent = [f for f in faelle if f["ausgang"] in ("ziel", "stop")]
    if not ent:
        return 0, float("nan")
    return len(ent), sum(1 for f in ent if f["ausgang"] == "ziel") / len(ent)


def _uform(faelle) -> float:
    """D1 als EINE Zahl: Extrembaender gegen die Mitte."""
    ne, qe = _quote([f for f in faelle if f["driftband"] in EXTREM])
    nm, qm = _quote([f for f in faelle if f["driftband"] == MITTE])
    if ne < MIN_FAELLE or nm < MIN_FAELLE:
        return float("nan")
    return qe - qm


def _uform_bereinigt(faelle, grenzen) -> float:
    """D2: dieselbe Zahl INNERHALB gleicher Stopabstaende (2.50)."""
    summe = gewicht = 0.0
    for b in range(STOPBAENDER):
        u, o = grenzen[b], grenzen[b + 1]
        drin = [f for f in faelle
                if u <= f["stop_relativ"] < o
                or (b == STOPBAENDER - 1 and f["stop_relativ"] >= o)]
        ne, qe = _quote([f for f in drin if f["driftband"] in EXTREM])
        nm, qm = _quote([f for f in drin if f["driftband"] == MITTE])
        if ne >= MIN_FAELLE and nm >= MIN_FAELLE:
            summe += ne * (qe - qm)
            gewicht += ne
    return summe / gewicht if gewicht else float("nan")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="data/messdaten.db")
    ap.add_argument("--klasse", default="krypto")
    ap.add_argument("--blockplacebo", type=int, default=120)
    ap.add_argument("--blocklaenge", type=int, default=BLOCKLAENGE)
    ap.add_argument("--datei", default="messwerte_drift_zerlegt.json")
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    print("=" * 78)
    print("DER DRIFT, ZERLEGT - und auf Reihen, die er nie gesehen hat")
    print("=" * 78)
    faelle = [f for f in _reif(laufe(a.db, a.klasse, fortschritt=True),
                               MINDESTALTER) if f["drift"] is not None]
    for f in faelle:
        f["driftband"] = _band(f["drift"])
    print(f"  {len(faelle)} reife Anker mit Drift")

    # ---- D1: DIE U-FORM, AUF NEUEN REIHEN -------------------------------
    print("\n" + "-" * 78)
    print("D1 - DIE U-FORM AUS KAPITEL 102, auf 347 statt 39 Reihen")
    print("-" * 78)
    print(f"  {'Driftband':18}{'Faelle':>10}{'Quote':>10}{'Abstand':>11}"
          f"   (102 auf 39 Reihen)")
    alt = {"unter -30 %": 36.2, "-30 bis -10 %": 27.8, "-10 bis +10 %": 29.0,
           "+10 bis +30 %": 34.2, "ueber +30 %": 35.9}
    baender = {}
    for _u, _o, name in DRIFT_BAENDER:
        teil = [f for f in faelle if f["driftband"] == name]
        n, q, ab = bewerte(teil, a.klasse)
        if math.isnan(ab):
            print(f"  {name:18}{n:10}   zu wenige Faelle")
            continue
        baender[name] = {"n": n, "quote": q, "abstand": ab}
        print(f"  {name:18}{n:10}{100 * q:9.1f} %{100 * ab:+10.1f}"
              f"        {alt[name]:5.1f} %")
    d1 = _uform(faelle)
    print(f"\n  D1 - Extreme gegen Mitte: {100 * d1:+.1f} Punkte")
    print(f"     (auf 39 Reihen waren es "
          f"{(alt['unter -30 %'] + alt['ueber +30 %']) / 2 - alt[MITTE]:+.1f})")

    # ---- D2: UEBERLEBT SIE DIE KOSTENBEREINIGUNG? -----------------------
    print("\n" + "-" * 78)
    print("D2 - DIESELBE ZAHL BEI GLEICHEM STOPABSTAND")
    print("  Der Verdacht: starker Trend -> hoher ATR -> weiter Stop ->")
    print("  niedrigere Huerde. Derselbe Kanal wie in 100-103.")
    print("-" * 78)
    grenzen = np.quantile([f["stop_relativ"] for f in faelle],
                          np.linspace(0, 1, STOPBAENDER + 1))
    print(f"  {'Stopband':16}{'Extreme':>10}{'Quote':>9}{'Mitte':>9}"
          f"{'Quote':>9}{'Diff':>9}")
    for b in range(STOPBAENDER):
        u, o = grenzen[b], grenzen[b + 1]
        drin = [f for f in faelle
                if u <= f["stop_relativ"] < o
                or (b == STOPBAENDER - 1 and f["stop_relativ"] >= o)]
        ne, qe = _quote([f for f in drin if f["driftband"] in EXTREM])
        nm, qm = _quote([f for f in drin if f["driftband"] == MITTE])
        name = f"{100 * u:.0f}-{100 * o:.0f} %"
        if ne < MIN_FAELLE or nm < MIN_FAELLE:
            print(f"  {name:16}{ne:10}{'':9}{nm:9}   zu wenige")
            continue
        print(f"  {name:16}{ne:10}{100 * qe:8.1f} %{nm:9}{100 * qm:8.1f} %"
              f"{100 * (qe - qm):+8.1f}")
    d2 = _uform_bereinigt(faelle, grenzen)
    print(f"\n  D2 - bereinigt: {100 * d2:+.1f} Punkte")
    if d1 == d1 and d1:
        print(f"     Vom rohen Effekt bleiben {100 * d2 / d1:.0f} %.")

    # ---- D3: TRAEGT DER DRIFT ETWAS, DAS H NICHT HAT? -------------------
    print("\n" + "-" * 78)
    print("D3 - DRIFT UND H: dasselbe oder verschiedenes?")
    print("-" * 78)
    h = [f for f in faelle if f["frei"] and f["gedeckt"]]
    print(f"  {'':22}{'Faelle':>10}{'Quote':>10}{'Abstand':>11}")
    vier = {}
    for name, wo in (
            ("H, Drift extrem", lambda f: f["frei"] and f["gedeckt"]
             and f["driftband"] in EXTREM),
            ("H, Drift Mitte", lambda f: f["frei"] and f["gedeckt"]
             and f["driftband"] == MITTE),
            ("kein H, Drift extrem", lambda f: not (f["frei"] and f["gedeckt"])
             and f["driftband"] in EXTREM),
            ("kein H, Drift Mitte", lambda f: not (f["frei"] and f["gedeckt"])
             and f["driftband"] == MITTE)):
        n, q, ab = bewerte([f for f in faelle if wo(f)], a.klasse)
        vier[name] = {"n": n, "quote": q, "abstand": ab}
        print(f"  {name:22}{n:10}{100 * q:9.1f} %"
              + (f"{100 * ab:+10.1f}" if ab == ab else "   zu wenige"))
    if all(vier[k]["quote"] == vier[k]["quote"] for k in vier):
        h_in_extrem = vier["H, Drift extrem"]["quote"] \
            - vier["kein H, Drift extrem"]["quote"]
        h_in_mitte = vier["H, Drift Mitte"]["quote"] \
            - vier["kein H, Drift Mitte"]["quote"]
        d3 = h_in_extrem - h_in_mitte
        print(f"\n  H bringt im Extremband {100 * h_in_extrem:+.1f}, "
              f"in der Mitte {100 * h_in_mitte:+.1f} Punkte")
        print(f"  D3 - Wechselwirkung: {100 * d3:+.1f} Punkte")
        print("     Nahe null heisst: die beiden addieren sich schlicht,")
        print("     sie tragen also VERSCHIEDENES.")
    else:
        d3 = float("nan")
    print(f"  H insgesamt: {len(h)} Faelle")

    # ---- SCHWELLEN ------------------------------------------------------
    print("\n" + "-" * 78)
    print(f"BLOCK-PERMUTATION - {a.blockplacebo} Laeufe, Bloecke in "
          f"KALENDERZEIT (2.52)")
    print("-" * 78)
    ent = [f for f in faelle if f["ausgang"] in ("ziel", "stop")]
    ziel = np.array([f["ausgang"] == "ziel" for f in ent])
    ordnung: dict = {}
    for pos, f in enumerate(ent):
        ordnung.setdefault(f["sym"], []).append((f["i"], pos))
    reihen = []
    for v in ordnung.values():
        bloecke: list = []
        for idx, pos in sorted(v):
            if not bloecke or idx - bloecke[-1][0] >= a.blocklaenge:
                bloecke.append([idx, []])
            bloecke[-1][1].append(pos)
        if len(bloecke) >= 2:
            reihen.append([np.array(b[1]) for b in bloecke])
    print(f"  {len(reihen)} Reihen lang genug fuer mindestens zwei Bloecke")
    rng = np.random.default_rng(20260831)
    w1, w2, wmax = [], [], []
    for _lauf in range(a.blockplacebo):
        gew = ziel.copy()
        for bloecke in reihen:
            alle = np.concatenate(bloecke)
            gew[alle] = ziel[np.concatenate(
                [bloecke[j] for j in rng.permutation(len(bloecke))])]
        getauscht = [{**f, "ausgang": ("ziel" if g else "stop")}
                     for f, g in zip(ent, gew)]
        x1, x2 = _uform(getauscht), _uform_bereinigt(getauscht, grenzen)
        if x1 == x1:
            w1.append(x1)
        if x2 == x2:
            w2.append(x2)
        gute = [x for x in (x1, x2) if x == x]
        if gute:
            wmax.append(max(gute))
    s1 = float(np.quantile(w1, 0.95)) if w1 else float("nan")
    s2 = float(np.quantile(w2, 0.95)) if w2 else float("nan")
    smax = float(np.quantile(wmax, 0.95)) if wmax else float("nan")
    print(f"\n  {'Frage':28}{'gemessen':>12}{'Schwelle':>12}{'Urteil':>16}")
    for name, wert, s in (("D1 U-Form roh", d1, s1),
                          ("D2 kostenbereinigt", d2, s2)):
        if wert != wert or s != s:
            print(f"  {name:28}{'zu wenige':>12}")
            continue
        print(f"  {name:28}{100 * wert:+11.1f}{100 * s:+11.1f}"
              f"{('traegt' if wert > s else 'traegt nicht'):>16}")
    print(f"\n  ⚠️ Schwelle fuer das Maximum aus den Fragen: "
          f"{100 * smax:+.1f} Punkte (2.49)")

    print("\n" + "=" * 78)
    if a.datei:
        io.open(a.datei, "w", encoding="utf-8").write(json.dumps({
            "baender": baender, "d1": d1, "d2": d2, "d3": d3,
            "vier_felder": vier, "schwelle_d1": s1, "schwelle_d2": s2,
            "schwelle_max": smax}, ensure_ascii=False, indent=1,
            default=float))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
