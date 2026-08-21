"""Was die Marke NOCH weiss (20.08.2026, Umbauplan 112)

⚠️ DIESER KOPF IST DIE VORABFESTLEGUNG, geschrieben BEVOR gerechnet wurde.

WARUM. Die Bedingung H fragt bisher nur "gibt es eine Marke mit mindestens
zwei Beruehrungen, ja oder nein". `niveaus_werte` weiss aber mehr, und wir
werfen es weg: die ZAHL der Beruehrungen, das ALTER der letzten, und ob die
Marke schon einmal GEFEGT wurde. Eine dreimal gehaltene Marke von letzter
Woche und eine zweimal beruehrte von 2019 sind heute dasselbe Ja.

⚠️ NUR B LAESST SICH ANREICHERN, NICHT A. A ist eine ABWESENHEIT ("kein
Widerstand im Weg") - an einer Marke, die es nicht gibt, ist kein Merkmal zu
messen. Das ist selbst ein Befund ueber den Bau der Regel und keine
Nachlaessigkeit dieser Messung.

WELCHE MARKE, WENN ES MEHRERE GIBT: die NAECHSTE am Kurs - auf sie faellt der
Kurs zuerst. "Die staerkste" waere schon eine Auswahl nach dem Merkmal, das
geprueft werden soll.

DREI VORHERSAGEN, jede aus einem Grund und jede einzeln benannt:

    E1  STAERKE    eine oefter beruehrte Marke haelt besser.
                   >= 3 Beruehrungen schlaegt genau 2.
    E2  ALTER      eine frisch bestaetigte Marke ist eher noch gueltig.
                   Alter <= Median schlaegt Alter > Median.
                   (Der Median, damit beide Arme gleich gross sind - eine
                   gesetzte Zahl waere eine Auswahl.)
    E3  GEFEGT     eine schon durchbrochene Marke haelt schlechter.
                   nicht gefegt schlaegt gefegt.

⚠️ DREI PRUEFUNGEN SIND EIN PREIS (Methodik 2.49). Ausgewiesen werden deshalb
BEIDE Schwellen: die fuer eine einzelne vorab benannte Frage und die fuer das
Maximum aus dreien. Wer nur die erste liest, unterschlaegt das Absuchen.

⚠️ UND ES WIRD ZERLEGT, NICHT GERICHTET (Methodik 2.51, Nutzervorgabe). Zu
jedem Merkmal steht der ABSOLUTE Abstand beider Arme daneben - ein Merkmal,
das den Vorsprung nicht vergroessert, den Trade aber ueber den Breakeven
hebt, ist ein Ergebnis und kein Fehlschlag.

⚠️ DIE FALLE, DIE HIER FAST ZUGESCHNAPPT WAERE: `LB._gefegt` liest
`c[ab_index + 1:]`, also die GESAMTE restliche Reihe. In der Produktion ist
das richtig, weil die Reihe vorher auf den Anker gekuerzt wird. In einer
Messung mit historischen Ankern waere es ein Blick in die Zukunft - gemessen
haetten 79,0 % der Marken als "gefegt" gegolten statt der korrekten 67,3 %.
`messe_marken._niveaus_schnell` uebergibt deshalb `c[:i + 1]`; 1.950
Vergleiche gegen die Produktionsfunktion, null Abweichungen.

    python messe_anreicherung.py [--blockplacebo 120]
"""
from __future__ import annotations

import argparse
import io
import json
import math
import sys

import numpy as np

sys.path.insert(0, ".")
from messe_marken import bewerte, laufe                        # noqa: E402
from messe_struktur_bereinigt import MINDESTALTER, _reif        # noqa: E402

MIN_FAELLE = 300
BLOCKLAENGE = 250


def _quote(faelle) -> tuple[int, float]:
    ent = [f for f in faelle if f["ausgang"] in ("ziel", "stop")]
    if not ent:
        return 0, float("nan")
    return len(ent), sum(1 for f in ent if f["ausgang"] == "ziel") / len(ent)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="data/messdaten.db")
    ap.add_argument("--klasse", default="krypto")
    ap.add_argument("--blockplacebo", type=int, default=120)
    ap.add_argument("--blocklaenge", type=int, default=BLOCKLAENGE)
    ap.add_argument("--datei", default="messwerte_anreicherung.json")
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    print("=" * 78)
    print("WAS DIE MARKE NOCH WEISS - Staerke, Alter, gefegt")
    print("=" * 78)
    faelle = _reif(laufe(a.db, a.klasse, fortschritt=True), MINDESTALTER)
    h = [f for f in faelle if f["frei"] and f["gedeckt"]]
    print(f"  {len(faelle)} reife Anker, davon {len(h)} in H")

    median_alter = float(np.median([f["b_alter"] for f in h]))
    print(f"  Median-Alter der tragenden Marke: {median_alter:.0f} "
          f"Handelstage")

    # ⚠️ DIE DREI FRAGEN, VORAB FESTGELEGT - keine vierte.
    tests = (
        ("E1 Staerke", ">= 3 Beruehrungen", "genau 2",
         lambda f: f["b_beruehrungen"] >= 3),
        ("E2 Alter", f"<= {median_alter:.0f} Tage", "aelter",
         lambda f: f["b_alter"] <= median_alter),
        ("E3 gefegt", "nicht gefegt", "gefegt",
         lambda f: not f["b_gefegt"]),
    )

    print("\n" + "-" * 78)
    print("DIE DREI VORHERSAGEN - innerhalb H")
    print("-" * 78)
    ergebnis = {}
    for name, ja, nein, wo in tests:
        arm_a = [f for f in h if wo(f)]
        arm_b = [f for f in h if not wo(f)]
        na, qa = _quote(arm_a)
        nb, qb = _quote(arm_b)
        _x, _y, ab_a = bewerte(arm_a, a.klasse)
        _u, _v, ab_b = bewerte(arm_b, a.klasse)
        print(f"\n  {name}")
        print(f"    {ja:22}{na:8} Faelle   {100 * qa:5.1f} %   "
              + (f"Abstand {100 * ab_a:+6.1f}" if ab_a == ab_a else ""))
        print(f"    {nein:22}{nb:8} Faelle   {100 * qb:5.1f} %   "
              + (f"Abstand {100 * ab_b:+6.1f}" if ab_b == ab_b else ""))
        if na >= MIN_FAELLE and nb >= MIN_FAELLE:
            ergebnis[name] = {"n_ja": na, "n_nein": nb, "quote_ja": qa,
                              "quote_nein": qb, "diff": qa - qb,
                              "abstand_ja": ab_a, "abstand_nein": ab_b}
            print(f"    {'-> Unterschied':22}{'':8}            "
                  f"{100 * (qa - qb):+6.1f} Punkte")
        else:
            print(f"    -> zu wenige Faelle in einem Arm")

    # ---- SCHWELLEN: EINE FRAGE UND DAS MAXIMUM AUS DREIEN ---------------
    print("\n" + "-" * 78)
    print(f"BLOCK-PERMUTATION innerhalb H - {a.blockplacebo} Laeufe")
    print("  Gewuerfelt wird NUR unter den H-Faellen (Methodik 2.50): die")
    print("  Frage ist, ob das Merkmal INNERHALB von H etwas beitraegt.")
    print("-" * 78)
    ent = [f for f in h if f["ausgang"] in ("ziel", "stop")]
    ziel = np.array([f["ausgang"] == "ziel" for f in ent])
    masken = {name: np.array([wo(f) for f in ent])
              for name, _ja, _nein, wo in tests}
    # ⚠️ HIER GREIFT DIE BISHERIGE BLOCKBILDUNG NICHT, UND DAS FIEL FAST
    # NICHT AUF. Die anderen Messungen schneiden Bloecke nach der ANZAHL
    # aufeinanderfolgender Anker - dort ist jeder Handelstag ein Anker, also
    # sind 250 Anker auch 250 Tage. Innerhalb von H ist nur etwa jeder
    # fuenfzigste Tag ein Anker: 9.405 Faelle auf 260 Symbole sind rund 36 je
    # Reihe. Mit `len(reihe) >= 500` wurde damit KEINE einzige Reihe
    # gewuerfelt - jede "Zufallsziehung" war die Messung selbst, und die
    # Schwelle kam exakt auf den gemessenen Wert heraus. Drei "traegt nicht"
    # in Folge sahen aus wie ein sauberer Nullbefund und waren eine
    # Nullkontrolle.
    #
    # RICHTIG IST EIN BLOCK IN KALENDERZEIT, nicht in Ankerzahl: alle
    # H-Anker, deren Index in dasselbe 250-Handelstage-Fenster faellt,
    # bilden einen Block. Die Bloecke sind dann verschieden gross - das ist
    # kein Mangel, sondern genau die Zeitstruktur, die erhalten bleiben soll.
    ordnung: dict = {}
    for pos, f in enumerate(ent):
        ordnung.setdefault(f["sym"], []).append((f["i"], pos))
    reihen = []
    for v in ordnung.values():
        paare = sorted(v)
        bloecke: list = []
        for idx, pos in paare:
            if not bloecke or idx - bloecke[-1][0] >= a.blocklaenge:
                bloecke.append([idx, []])
            bloecke[-1][1].append(pos)
        if len(bloecke) >= 2:
            reihen.append([np.array(b[1]) for b in bloecke])
    lang = len(reihen)
    rng = np.random.default_rng(20260830)
    je_test: dict = {name: [] for name in masken}
    hoechste = []
    for _lauf in range(a.blockplacebo):
        gew = ziel.copy()
        for bloecke in reihen:
            alle = np.concatenate(bloecke)
            neu_ord = np.concatenate([bloecke[j] for j in
                                      rng.permutation(len(bloecke))])
            gew[alle] = ziel[neu_ord]
        beste = -9.9
        for name, m in masken.items():
            if m.sum() < MIN_FAELLE or (~m).sum() < MIN_FAELLE:
                continue
            d = float(gew[m].mean()) - float(gew[~m].mean())
            je_test[name].append(d)
            beste = max(beste, d)
        if beste > -9.0:
            hoechste.append(beste)
    print(f"  {lang} Reihen lang genug fuer mindestens zwei Bloecke")
    s_max = float(np.quantile(hoechste, 0.95)) if hoechste else float("nan")
    print(f"\n  {'Merkmal':16}{'gemessen':>12}{'Schwelle einzeln':>20}"
          f"{'Urteil':>26}")
    schwellen = {}
    for name, _ja, _nein, _wo in tests:
        if name not in ergebnis or not je_test[name]:
            continue
        s1 = float(np.quantile(je_test[name], 0.95))
        streu = float(np.std(je_test[name])) / math.sqrt(len(je_test[name]))
        d = ergebnis[name]["diff"]
        schwellen[name] = {"einzeln": s1, "max_aus_drei": s_max}
        urteil = ("ZU KNAPP (2.48)" if abs(d - s1) < 2 * streu
                  else "traegt" if d > s1 else "traegt nicht")
        if d > s1 and d <= s_max:
            urteil = "traegt einzeln, NICHT aus dreien"
        print(f"  {name:16}{100 * d:+11.1f}{100 * s1:+19.1f}{urteil:>26}")
    print(f"\n  ⚠️ SCHWELLE FUER DAS MAXIMUM AUS DREI FRAGEN: "
          f"{100 * s_max:+.1f} Punkte")
    print("     Das ist der Preis des Absuchens (2.49) - wer nur die")
    print("     Einzelschwelle liest, unterschlaegt ihn.")

    print("\n" + "=" * 78)
    if a.datei:
        io.open(a.datei, "w", encoding="utf-8").write(json.dumps({
            "median_alter": median_alter, "tests": ergebnis,
            "schwellen": schwellen, "schwelle_max_aus_drei": s_max},
            ensure_ascii=False, indent=1, default=float))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
