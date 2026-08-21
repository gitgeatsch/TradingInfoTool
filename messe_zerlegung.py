"""Woraus besteht der Strukturvorteil? (20.08.2026, Umbauplan 111)

⚠️ DIESER KOPF IST DIE VORABFESTLEGUNG, geschrieben BEVOR gerechnet wurde.

ZWEI FRAGEN, EINE DATENBASIS.

FRAGE 1 - DER PHASENHORIZONT. Kapitel 110 hat einen Nebenbefund geliefert, der
alle Lagenaussagen betrifft: Shorts schneiden im "Baermarkt" AM SCHLECHTESTEN
ab. Das ist nur erklaerbar, wenn das Etikett NACHLAEUFT - `_marktphase` misst
die vergangenen 250 Tage, "baer" heisst also "der Markt IST gefallen".

    VORHERSAGE: ist die fehlende Groesse "der Markt steigt GERADE", dann
    trennt ein KURZES Fenster (20, 60 Tage) den Vorsprung von H schaerfer
    als das lange (250).

    ⚠️ Die Schwelle wird mit der Wurzel des Fensters skaliert. +/-20 % sind
    fuer 250 Tage die gaengige Zahl; auf 20 Tagen waeren sie fast nie
    erreicht, und dann hiesse jeder Zeitpunkt "seitwaerts".

FRAGE 2 - IST H NUR "NAHE AM HOCH"? Widerstaende SIND alte Hochs. Wo keiner
mehr ueber dem Kurs liegt, steht der Kurs nahe an seinem Hoch. H koennte also
ein umstaendlicher Momentum-Indikator sein statt einer Aussage ueber Struktur.

⚠️ DIESE FRAGE WIRD ALS ZERLEGUNG GESTELLT, NICHT ALS FALLBEIL.

    Nutzervorgabe (20.08.): *"'erledigt' ist immer so endgueltig und es wird
    weggelegt und als Erkenntnis abgehakt - hier sollten wir vorsichtiger
    vorgehen, sonst fehlen uns die Optionen und wir haben am Ende wieder kein
    Ergebnis, sondern wir haben uns selbst durch einen methodisch harten
    Regel-Filter den Weg verbaut."*

    Gemessen wird deshalb NICHT "besteht H den Test", sondern:

        roher Vorsprung    H gegen den Rest
        Restvorsprung      H gegen den Rest INNERHALB gleicher Hochabstaende
        Anteil erklaert    wie viel der Hochabstand allein traegt

    Und der Hochabstand wird SELBST als Kandidat ausgewiesen. Faellt der
    Restvorsprung auf null, ist das kein Ende, sondern ein TAUSCH: eine
    einfachere und staerkere Groesse an derselben Stelle. Ein Weg schliesst
    sich nur, wenn beide Zahlen null sind.

⚠️ DER HOCHABSTAND WIRD NUR RUECKWAERTS GERECHNET: Kurs gegen das hoechste
Hoch der letzten 250 Kerzen einschliesslich heute.

    python messe_zerlegung.py [--blockplacebo 40]
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
from simuliere_bremse import (PHASE_SCHWELLE, _marktphase,      # noqa: E402
                              _reihen_roh, klassen_aus_db)

FENSTER = (20, 60, 250)
BAENDER = 5
MIN_FAELLE = 300
BLOCKLAENGE = 250
LAGEN = ("bulle", "seitwaerts", "baer")


def _quote(faelle) -> tuple[int, float]:
    ent = [f for f in faelle if f["ausgang"] in ("ziel", "stop")]
    if not ent:
        return 0, float("nan")
    return len(ent), sum(1 for f in ent if f["ausgang"] == "ziel") / len(ent)


def _rest(faelle, grenzen, feld: str) -> tuple[float, list]:
    """H gegen den Rest INNERHALB gleicher Baender - direkte Standardisierung."""
    zeilen, summe, gewicht = [], 0.0, 0.0
    for b in range(BAENDER):
        u, o = grenzen[b], grenzen[b + 1]
        drin = [f for f in faelle
                if (u <= f[feld] < o or (b == BAENDER - 1 and f[feld] >= o))]
        h = [f for f in drin if f["frei"] and f["gedeckt"]]
        r = [f for f in drin if not (f["frei"] and f["gedeckt"])]
        nh, qh = _quote(h)
        nr, qr = _quote(r)
        zeilen.append({"band": b, "u": u, "o": o, "n_h": nh, "n_rest": nr,
                       "quote_h": qh, "quote_rest": qr})
        if nh >= MIN_FAELLE and nr >= MIN_FAELLE:
            summe += nh * (qh - qr)
            gewicht += nh
    return (summe / gewicht if gewicht else float("nan")), zeilen


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="data/messdaten.db")
    ap.add_argument("--klasse", default="krypto")
    ap.add_argument("--blockplacebo", type=int, default=40)
    ap.add_argument("--blocklaenge", type=int, default=BLOCKLAENGE)
    ap.add_argument("--datei", default="messwerte_zerlegung.json")
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    print("=" * 78)
    print("WORAUS BESTEHT DER STRUKTURVORTEIL?")
    print("=" * 78)
    faelle = _reif(laufe(a.db, a.klasse, fortschritt=True), MINDESTALTER)
    print(f"  {len(faelle)} reife Anker")

    # ---- FRAGE 1: DER PHASENHORIZONT ------------------------------------
    print("\n" + "-" * 78)
    print("FRAGE 1 - TRENNT EIN KURZES PHASENFENSTER SCHAERFER?")
    print("  Vorhergesagt: ja, wenn die fehlende Groesse 'der Markt steigt")
    print("  GERADE' ist statt 'der Markt IST gestiegen'.")
    print("-" * 78)
    roh = _reihen_roh(a.db, a.klasse, klassen_aus_db(a.db))
    horizonte = {}
    print(f"  {'Fenster':10}{'Schwelle':>10}" + "".join(
        f"{lage:>14}" for lage in LAGEN) + f"{'Spanne':>10}")
    for fenster in FENSTER:
        etikett = _marktphase(roh, fenster, PHASE_SCHWELLE)
        zeile, werte = f"  {fenster:<10}" \
            f"{100 * PHASE_SCHWELLE * math.sqrt(fenster / 250):9.1f} %", []
        for lage in LAGEN:
            teil = [f for f in faelle
                    if etikett.get(f["datum"], "unbekannt") == lage]
            _nh, _qh, abh = bewerte([f for f in teil
                                     if f["frei"] and f["gedeckt"]], a.klasse)
            _nb, _qb, abb = bewerte(teil, a.klasse)
            v = abh - abb if not (math.isnan(abh) or math.isnan(abb)) \
                else float("nan")
            werte.append(v)
            zeile += (f"{100 * v:+13.1f}" if v == v else f"{'zu wenige':>14}")
        gute = [v for v in werte if v == v]
        spanne = max(gute) - min(gute) if len(gute) > 1 else float("nan")
        horizonte[fenster] = {"vorspruenge": werte, "spanne": spanne}
        print(zeile + (f"{100 * spanne:9.1f}" if spanne == spanne else ""))
    print("\n  Die SPANNE ist das Mass: je groesser, desto schaerfer trennt")
    print("  das Fenster zwischen den Lagen.")

    # ---- FRAGE 2: DIE ZERLEGUNG -----------------------------------------
    print("\n" + "-" * 78)
    print("FRAGE 2 - IST H NUR 'NAHE AM HOCH'? (als Zerlegung, nicht als")
    print("  Fallbeil - eine einfachere Groesse an derselben Stelle waere")
    print("  ein Tausch, kein Ende.)")
    print("-" * 78)
    hh = [f["hoch_abstand"] for f in faelle if f["frei"] and f["gedeckt"]]
    hr = [f["hoch_abstand"] for f in faelle
          if not (f["frei"] and f["gedeckt"])]
    print(f"  Median-Abstand zum 250-Tage-Hoch")
    print(f"    H            {100 * float(np.median(hh)):+7.1f} %")
    print(f"    der Rest     {100 * float(np.median(hr)):+7.1f} %")
    print(f"  -> {'H steht NAEHER am Hoch - der Verdacht ist berechtigt' if np.median(hh) > np.median(hr) else 'kein Zusammenhang sichtbar'}")

    grenzen = np.quantile([f["hoch_abstand"] for f in faelle],
                          np.linspace(0, 1, BAENDER + 1))
    roh_n, roh_q = _quote([f for f in faelle if f["frei"] and f["gedeckt"]])
    _rn, rest_q = _quote([f for f in faelle
                          if not (f["frei"] and f["gedeckt"])])
    roh_vorsprung = roh_q - rest_q
    rest_vorsprung, zeilen = _rest(faelle, grenzen, "hoch_abstand")

    print(f"\n  {'Band (Abstand zum Hoch)':26}{'H':>8}{'Quote H':>10}"
          f"{'Rest':>9}{'Quote Rest':>12}{'Diff':>8}")
    for z in zeilen:
        name = f"{100 * z['u']:+.0f} bis {100 * z['o']:+.0f} %"
        if z["n_h"] < MIN_FAELLE or z["n_rest"] < MIN_FAELLE:
            print(f"  {name:26}{z['n_h']:8}   zu wenige")
            continue
        print(f"  {name:26}{z['n_h']:8}{100 * z['quote_h']:9.1f} %"
              f"{z['n_rest']:9}{100 * z['quote_rest']:11.1f} %"
              f"{100 * (z['quote_h'] - z['quote_rest']):+7.1f}")

    print(f"\n  roher Vorsprung   {100 * roh_vorsprung:+.1f} Punkte")
    print(f"  Restvorsprung     {100 * rest_vorsprung:+.1f} Punkte "
          f"(bei gleichem Hochabstand)")
    if roh_vorsprung:
        anteil = 1.0 - rest_vorsprung / roh_vorsprung
        print(f"  -> Der Hochabstand erklaert {100 * anteil:.0f} % des "
              f"Vorsprungs.")

    # ⚠️ UND DER HOCHABSTAND ALS EIGENER KANDIDAT - das ist der Punkt, an dem
    # ein Nullbefund zu einem Tausch wird statt zu einem Ende.
    print("\n  DER HOCHABSTAND ALS EIGENER KANDIDAT")
    print(f"  {'Band':26}{'Faelle':>10}{'Quote':>10}{'Abstand':>11}")
    kandidat = {}
    for b in range(BAENDER):
        u, o = grenzen[b], grenzen[b + 1]
        teil = [f for f in faelle
                if u <= f["hoch_abstand"] < o
                or (b == BAENDER - 1 and f["hoch_abstand"] >= o)]
        n, q, ab = bewerte(teil, a.klasse)
        name = f"{100 * u:+.0f} bis {100 * o:+.0f} %"
        if math.isnan(ab):
            print(f"  {name:26}{n:10}   zu wenige")
            continue
        kandidat[name] = {"n": n, "quote": q, "abstand": ab}
        print(f"  {name:26}{n:10}{100 * q:9.1f} %{100 * ab:+10.1f}")

    # ---- SCHWELLE FUER DEN RESTVORSPRUNG --------------------------------
    print("\n" + "-" * 78)
    print(f"BLOCK-PERMUTATION fuer den RESTVORSPRUNG - {a.blockplacebo} Laeufe")
    print("-" * 78)
    schwelle = float("nan")
    if not math.isnan(rest_vorsprung):
        ent = [f for f in faelle if f["ausgang"] in ("ziel", "stop")]
        ziel = np.array([f["ausgang"] == "ziel" for f in ent])
        ordnung: dict = {}
        for pos, f in enumerate(ent):
            ordnung.setdefault(f["sym"], []).append((f["i"], pos))
        reihen = [np.array([p for _i, p in sorted(v)])
                  for v in ordnung.values()]
        lang = sum(1 for r in reihen if len(r) >= 2 * a.blocklaenge)
        rng = np.random.default_rng(20260829)
        werte = []
        for _lauf in range(a.blockplacebo):
            gew = ziel.copy()
            for reihe in reihen:
                if len(reihe) < 2 * a.blocklaenge:
                    continue
                v = int(rng.integers(0, a.blocklaenge))
                tl = ([reihe[:v]] if v else []) + [
                    reihe[s:s + a.blocklaenge]
                    for s in range(v, len(reihe), a.blocklaenge)]
                gew[reihe] = ziel[np.concatenate(
                    [tl[j] for j in rng.permutation(len(tl))])]
            getauscht = [{**f, "ausgang": ("ziel" if g else "stop")}
                         for f, g in zip(ent, gew)]
            w, _z = _rest(getauscht, grenzen, "hoch_abstand")
            if w == w:
                werte.append(w)
        schwelle = float(np.quantile(werte, 0.95))
        streu = float(np.std(werte)) / math.sqrt(len(werte))
        print(f"  {lang} Reihen lang genug fuer mindestens zwei Bloecke")
        print(f"  SCHWELLE (95 %)   {100 * schwelle:+.1f} Punkte")
        print(f"  Restvorsprung     {100 * rest_vorsprung:+.1f} Punkte")
        if abs(rest_vorsprung - schwelle) < 2 * streu:
            print("  ⚠️ ZU KNAPP (Methodik 2.48)")
        elif rest_vorsprung > schwelle:
            print("  -> H TRAEGT AUCH BEI GLEICHEM HOCHABSTAND. Die Marken")
            print("     sind eine eigene Information, kein Momentum-Ersatz.")
        else:
            print("  -> BEI GLEICHEM HOCHABSTAND BLEIBT NICHTS. ⚠️ Das ist")
            print("     KEIN Ende: der Hochabstand steht als einfachere")
            print("     Groesse an derselben Stelle bereit (Tabelle oben).")

    print("\n" + "=" * 78)
    if a.datei:
        io.open(a.datei, "w", encoding="utf-8").write(json.dumps({
            "horizonte": {str(k): v for k, v in horizonte.items()},
            "roh_vorsprung": roh_vorsprung, "rest_vorsprung": rest_vorsprung,
            "hochabstand_kandidat": kandidat, "schwelle": schwelle},
            ensure_ascii=False, indent=1, default=float))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
