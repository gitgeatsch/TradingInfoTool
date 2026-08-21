"""Wird aus dem Muster eine Regel? (20.08.2026, Umbauplan 109)

⚠️ DIESER KOPF IST DIE VORABFESTLEGUNG, geschrieben BEVOR gerechnet wurde.

DAS PROBLEM. Kapitel 108 hat gemessen, dass die Strukturbedingung H im
Bullenmarkt +5,1 Punkte UEBER ihrem Breakeven liegt und im Baermarkt -8,5
darunter. Daraus die Regel "H nur ausserhalb des Baermarkts" zu machen, hiesse
eine Bedingung aus einem ERGEBNIS zu benennen - genau der Schritt, dessen
Preis Methodik 2.49 beziffert.

    Die Phasenprobe war als ROBUSTHEITSPRUEFUNG angelegt, nicht als
    Filterdimension. Ein Muster, das man in denselben Daten findet und
    bewertet, ist keine Regel, sondern eine Beschreibung.

DIE PRUEFUNG, VORAB FESTGELEGT - ZWEI HAELFTEN, EINE RICHTUNG:

    FESTLEGUNG   erste Haelfte der Zeitreihe. Hier wird die Regel BESTIMMT:
                 in welchen Marktlagen liegt H ueber seinem Breakeven?
                 Was hier passiert, ist ausdruecklich Suche - erlaubt, weil
                 die zweite Haelfte davon nichts sieht.

    PRUEFUNG     zweite Haelfte. Die Regel wird UNVERAENDERT angewendet und
                 gegen eine Schwelle gestellt, die aus dieser Haelfte selbst
                 stammt. Kein Nachjustieren, keine zweite Runde.

⚠️ DER PUFFER IST NICHT OPTIONAL. Ein Anker kurz vor der Trennlinie hat sein
Vorwaertsfenster JENSEITS davon - sein Ausgang gehoert also schon zur
Pruefhaelfte. Ohne Puffer sickert die Antwort in die Festlegung. Verworfen
werden deshalb die letzten MAX_TAGE der ersten Haelfte.

⚠️ UND EIN VERGLEICH GEHOERT DAZU, sonst sagt das Ergebnis nichts: gemessen
wird in der zweiten Haelfte BEIDES -

    H mit der Regel      nur in den Lagen aus der Festlegung
    H ohne die Regel     in allen Lagen

Traegt die Regel nicht mehr als H ohne sie, war die Lagenbedingung teuer
erkauft und wertlos.

⚠️ DIE ZUSAMMENSETZUNG DER HAELFTEN WIRD AUSGEWIESEN. Faellt die eine
ueberwiegend in den Bullenmarkt und die andere in den Baermarkt, ist der
Vergleich nicht fair - und das muss man sehen, nicht ahnen.

    python messe_zeitteilung.py [--blockplacebo 40]
"""
from __future__ import annotations

import argparse
import collections
import io
import json
import math
import sys

import numpy as np

sys.path.insert(0, ".")
from agent import trefferbilanz as TB                          # noqa: E402
from messe_marken import CRV, bewerte, laufe                   # noqa: E402
from messe_struktur_bereinigt import MINDESTALTER, _reif       # noqa: E402
from simuliere_bremse import MAX_TAGE, gebuehr_je_seite        # noqa: E402

BLOCKLAENGE = 250
MIN_FAELLE = 300
LAGEN = ("bulle", "seitwaerts", "baer")


def _teile(faelle: list[dict]) -> tuple[list, list, str, str]:
    """Zwei Haelften nach DATUM - mit Puffer gegen das Vorwaertsfenster."""
    tage = sorted({f["datum"] for f in faelle})
    trenn = tage[len(tage) // 2]
    # ⚠️ Der Puffer wird in HANDELSTAGEN der Reihe gezaehlt, nicht in
    # Kalendertagen - die Reihen sind taeglich, also fallen beide zusammen.
    puffer_bis = tage[max(0, len(tage) // 2 - MAX_TAGE)]
    erste = [f for f in faelle if f["datum"] < puffer_bis]
    zweite = [f for f in faelle if f["datum"] >= trenn]
    return erste, zweite, puffer_bis, trenn


def _schwelle(faelle: list[dict], regel: set, klasse: str,
              laeufe: int, blocklaenge: int) -> tuple[float, int, float]:
    """Block-Permutation fuer GENAU diese Regel auf DIESER Haelfte.

    ⚠️ DIE KONTROLLE MUSS ZUR FRAGE PASSEN (dieselbe Lehre wie 101.6). Die
    erste Fassung wuerfelte die Ausgaenge ueber ALLE Lagen der Pruefhaelfte -
    also auch ueber den Baermarkt. Die Regel beschraenkt sich aber auf Bulle
    und Seitwaerts, und die haben in der zweiten Haelfte eine NIEDRIGERE
    Grundquote (28,4 %) als der Durchschnitt (33,0 %).

    Der Zufallsarm bekam damit 4,6 Punkte geschenkt, die nichts mit H zu tun
    haben, sondern mit der Lagenwahl. Gemessen wird hier aber, ob H INNERHALB
    seiner Lagen etwas beitraegt - also wird auch nur INNERHALB dieser Lagen
    gewuerfelt."""
    ent = [f for f in faelle
           if f["ausgang"] in ("ziel", "stop") and f["phase"] in regel]
    ziel = np.array([f["ausgang"] == "ziel" for f in ent])
    drin = np.array([f["frei"] and f["gedeckt"] and f["phase"] in regel
                     for f in ent])
    if drin.sum() < MIN_FAELLE:
        return float("nan"), int(drin.sum()), float("nan")
    stop_rel = float(np.median([f["stop_relativ"]
                                for f, m in zip(ent, drin) if m]))
    be = TB.breakeven(2 * gebuehr_je_seite(klasse) / stop_rel, CRV)
    ordnung: dict = {}
    for pos, f in enumerate(ent):
        ordnung.setdefault(f["sym"], []).append((f["i"], pos))
    reihen = [np.array([p for _i, p in sorted(v)]) for v in ordnung.values()]
    lang = sum(1 for r in reihen if len(r) >= 2 * blocklaenge)
    rng = np.random.default_rng(20260827)
    werte = []
    for _lauf in range(laeufe):
        gew = ziel.copy()
        for reihe in reihen:
            if len(reihe) < 2 * blocklaenge:
                continue
            v = int(rng.integers(0, blocklaenge))
            teile = ([reihe[:v]] if v else []) + [
                reihe[s:s + blocklaenge]
                for s in range(v, len(reihe), blocklaenge)]
            gew[reihe] = ziel[np.concatenate(
                [teile[j] for j in rng.permutation(len(teile))])]
        werte.append(float(gew[drin].mean()) - be)
    return (float(np.quantile(werte, 0.95)), lang,
            float(np.std(werte)) / math.sqrt(len(werte)))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="data/messdaten.db")
    ap.add_argument("--klasse", default="krypto")
    ap.add_argument("--blockplacebo", type=int, default=40)
    ap.add_argument("--blocklaenge", type=int, default=BLOCKLAENGE)
    ap.add_argument("--datei", default="messwerte_zeitteilung.json")
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    print("=" * 78)
    print("WIRD AUS DEM MUSTER EINE REGEL?")
    print("  Festlegung auf der ersten Haelfte, Pruefung auf der zweiten.")
    print("=" * 78)
    faelle = _reif(laufe(a.db, a.klasse, fortschritt=True), MINDESTALTER)
    erste, zweite, puffer_bis, trenn = _teile(faelle)
    print(f"  {len(faelle)} reife Anker")
    print(f"  Festlegung  bis {puffer_bis}  {len(erste):7} Anker")
    print(f"  Puffer      {puffer_bis} bis {trenn} - "
          f"{len(faelle) - len(erste) - len(zweite)} Anker verworfen, weil "
          f"ihr Ausgang jenseits der Trennlinie liegt")
    print(f"  Pruefung    ab  {trenn}  {len(zweite):7} Anker")

    # ⚠️ SIND DIE HAELFTEN VERGLEICHBAR? Ein Bullenmarkt gegen einen
    # Baermarkt zu stellen misst die Lage, nicht die Regel.
    print("\n" + "-" * 78)
    print("ZUSAMMENSETZUNG DER HAELFTEN")
    print("-" * 78)
    print(f"  {'Lage':14}{'Festlegung':>14}{'Pruefung':>14}")
    for lage in LAGEN:
        e = collections.Counter(f["phase"] for f in erste)[lage]
        z = collections.Counter(f["phase"] for f in zweite)[lage]
        print(f"  {lage:14}{100 * e / max(len(erste), 1):13.1f} %"
              f"{100 * z / max(len(zweite), 1):13.1f} %")

    # ---- FESTLEGUNG -----------------------------------------------------
    print("\n" + "-" * 78)
    print("FESTLEGUNG - erste Haelfte. Hier IST Suche erlaubt.")
    print("-" * 78)
    print(f"  {'Lage':14}{'H-Faelle':>10}{'Quote':>10}{'Abstand':>11}")
    regel = set()
    for lage in LAGEN:
        n, q, ab = bewerte([f for f in erste if f["frei"] and f["gedeckt"]
                            and f["phase"] == lage], a.klasse)
        if math.isnan(ab):
            print(f"  {lage:14}{n:10}   zu wenige Faelle")
            continue
        if ab > 0:
            regel.add(lage)
        print(f"  {lage:14}{n:10}{100 * q:9.1f} %{100 * ab:+10.1f}"
              f"{'   -> in die Regel' if ab > 0 else ''}")
    print(f"\n  DIE REGEL, hier und jetzt festgelegt: "
          f"H nur in {sorted(regel) if regel else '- keiner Lage -'}")
    if not regel:
        print("  Keine Lage traegt in der ersten Haelfte. Nichts zu pruefen.")
        return 0

    # ---- PRUEFUNG -------------------------------------------------------
    print("\n" + "-" * 78)
    print("PRUEFUNG - zweite Haelfte. Die Regel wird NICHT mehr angefasst.")
    print("-" * 78)
    ergebnis = {}
    for name, wo in (("H MIT der Regel", regel), ("H OHNE die Regel",
                                                  set(LAGEN))):
        n, q, ab = bewerte([f for f in zweite if f["frei"] and f["gedeckt"]
                            and f["phase"] in wo], a.klasse)
        ergebnis[name] = {"n": n, "quote": q, "abstand": ab}
        print(f"  {name:20}{n:8} Faelle   {100 * q:5.1f} %   "
              + (f"{100 * ab:+6.1f} Punkte" if not math.isnan(ab)
                 else "zu wenige"))
    # ⚠️ DER MASSSTAB MUSS ZUR REGEL PASSEN. Die erste Fassung verglich H in
    # den Regel-Lagen gegen ALLE Anker in ALLEN Lagen - das mischt die
    # Lagenwahl in den Vergleich und laedt zu einem falschen Schluss ein.
    # Gefragt ist: was bringt H INNERHALB der Lagen, in denen es angewendet
    # wird?
    n0, q0, ab0 = bewerte([f for f in zweite if f["phase"] in regel],
                          a.klasse)
    print(f"  {'alle Anker IN diesen Lagen':26}{n0:8} Faelle   "
          f"{100 * q0:5.1f} %   {100 * ab0:+6.1f} Punkte")
    na, qa, aba = bewerte(list(zweite), a.klasse)
    print(f"  {'alle Anker, alle Lagen':26}{na:8} Faelle   "
          f"{100 * qa:5.1f} %   {100 * aba:+6.1f} Punkte")
    if not math.isnan(ab0):
        print(f"  Und H bringt gegenueber diesen Ankern "
              f"{100 * (ergebnis['H MIT der Regel']['abstand'] - ab0):+.1f} "
              f"Punkte - DAS ist der faire Vergleich.")

    mit = ergebnis["H MIT der Regel"]["abstand"]
    ohne = ergebnis["H OHNE die Regel"]["abstand"]
    if not (math.isnan(mit) or math.isnan(ohne)):
        print(f"\n  Die Lagenbedingung bringt {100 * (mit - ohne):+.1f} "
              f"Punkte gegenueber H ohne sie.")

    # ---- SCHWELLE AUS DER PRUEFHAELFTE ----------------------------------
    print("\n" + "-" * 78)
    print(f"BLOCK-PERMUTATION auf der PRUEFHAELFTE - {a.blockplacebo} Laeufe")
    print("-" * 78)
    schwelle, lang, streu = _schwelle(zweite, regel, a.klasse,
                                      a.blockplacebo, a.blocklaenge)
    print(f"  {lang} Reihen lang genug fuer mindestens zwei Bloecke")
    if math.isnan(schwelle):
        print("  Zu wenige Faelle fuer eine Schwelle.")
    else:
        print(f"  SCHWELLE (95 %)  {100 * schwelle:+.1f} Punkte")
        print(f"  gemessen         {100 * mit:+.1f} Punkte")
        if abs(mit - schwelle) < 2 * streu:
            print("  ⚠️ ZU KNAPP - im Schaetzfehler der Schwelle "
                  "(Methodik 2.48).")
        elif mit > schwelle:
            print("  -> DIE REGEL HAELT AUSSERHALB IHRER EIGENEN DATEN.")
        else:
            print("  -> DIE REGEL HAELT NICHT. Das Muster der ersten Haelfte")
            print("     wiederholt sich in der zweiten nicht.")

    print("\n" + "=" * 78)
    if a.datei:
        io.open(a.datei, "w", encoding="utf-8").write(json.dumps({
            "trennlinie": trenn, "puffer_bis": puffer_bis,
            "regel": sorted(regel), "pruefung": ergebnis,
            "schwelle": schwelle}, ensure_ascii=False, indent=1,
            default=float))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
