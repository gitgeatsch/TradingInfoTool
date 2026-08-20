"""Traegt H auch bei GLEICHEN KOSTEN? (20.08.2026, Umbauplan 105)

⚠️ DIESER KOPF IST DIE VORABFESTLEGUNG, geschrieben BEVOR gerechnet wurde.

WAS KAPITEL 104 UEBRIG GELASSEN HAT. Die Strukturbedingung H trifft mit
40,6 % gegen 34,4 % - der erste Filter dieses Projekts, der die TREFFERQUOTE
bewegt statt nur die Kostenhuerde. Er zahlt trotzdem nicht, weil er die Huerde
im selben Mass mithebt: H waehlt weite Stops (19,67 % gegen 15,44 %), und ein
weiter Stop bedeutet hoeheren Breakeven.

    6,2 Punkte mehr Treffer - und genau so viel mehr Huerde.

DIE FRAGE, VORAB FESTGELEGT:

    Bleibt der Quotenvorteil von H bestehen, wenn der Stopabstand KONSTANT
    gehalten wird?

    traegt er   -> die Struktur sagt etwas ueber den Markt, das die
                   Kostenarithmetik nicht schon sagt. Erster echter Kanal.
    traegt nicht-> der ganze Vorteil war der weitere Stop, also Kapitel
                   100-103 zum vierten Mal unter neuem Namen.

DAS MASS, EINE ZAHL - KEIN ABSUCHEN VON BAENDERN:

    Die Anker werden in fuenf gleich grosse Stopband-Fuenftel geteilt. In
    jedem Band wird H gegen NICHT-H verglichen; die Einzelbaender werden
    berichtet, ENTSCHIEDEN wird ueber die gewichtete Summe:

        bereinigter Vorsprung = Summe_b  w_b * (Quote_H,b - Quote_nichtH,b)

    mit w_b = Anteil der H-Faelle im Band b. Das ist die direkte
    Standardisierung: H wird gefragt, wie es abschnitte, wenn es dieselbe
    Kostenverteilung haette wie der Rest.

    ⚠️ EIN EINZELNES BAND IST KEIN URTEIL. Fuenf Baender abzusuchen und das
    beste zu nehmen kostet nach Methodik 2.49 die doppelte Huerde.

⚠️ DIE REIFEPROBE IST HIER PFLICHT, NICHT OPTION. Kapitel 104.3: 48 % aller
H-Faelle lagen in den ersten 250 Handelstagen ihrer Reihe, wo "kein
Widerstand im Weg" ein DATENzustand ist. Diese Messung laeuft ab Werk mit
`--mindestalter 250`; wer sie ohne rechnet, misst wieder die Datenlage.

DIE PFLICHTKONTROLLEN, alle vorab:

  1. BLOCK-PERMUTATION statt freiem Placebo (Methodik 2.47).
  2. LAEUFE ERHOEHEN, wenn der Messwert nahe der Schwelle liegt (2.48).
  3. POSITIVKONTROLLE - sonst heisst "traegt nicht" nur "nicht hingesehen".
  4. PHASENPROBE - ein Vorsprung nur im Baermarkt ist die Marktphasenwette.

⚠️ UND EINE GEGENPROBE, DIE ZU DIESER FRAGE GEHOERT: bleibt nach der
Schichtung ueberhaupt noch ein Kostenunterschied uebrig? Ausgewiesen wird der
Median-Stopabstand von H und Nicht-H JE BAND. Sind die dort noch weit
auseinander, ist die Schichtung zu grob und das Ergebnis nichts wert.

    python messe_struktur_bereinigt.py [--blockplacebo 40]
"""
from __future__ import annotations

import argparse
import io
import json
import math
import sys

import numpy as np

sys.path.insert(0, ".")
from messe_marken import laufe                                # noqa: E402

BAENDER = 5
MIN_FAELLE = 200          # je Band und Seite - darunter ist es Rauschen
MINDESTALTER = 250        # Pflicht, nicht Option (Kapitel 104.3)
BLOCKLAENGE = 250
MAX_KOSTENREST = 0.02     # 2 Punkte Stopabstand - darueber ist die
#                           Schichtung zu grob, um von "gleichen Kosten"
#                           zu sprechen


def _reif(faelle: list[dict], mindestalter: int) -> list[dict]:
    erst: dict = {}
    for f in faelle:
        erst[f["sym"]] = min(erst.get(f["sym"], f["i"]), f["i"])
    return [f for f in faelle if f["i"] - erst[f["sym"]] >= mindestalter]


def _bandgrenzen(faelle: list[dict]) -> np.ndarray:
    """Fuenftel des Stopabstands - aus ALLEN Ankern, nicht aus H.

    Aus H allein waeren die Grenzen von der zu pruefenden Gruppe gesetzt."""
    werte = np.array([f["stop_relativ"] for f in faelle])
    return np.quantile(werte, np.linspace(0, 1, BAENDER + 1))


def _band(x: float, grenzen: np.ndarray) -> int:
    return int(min(np.searchsorted(grenzen, x, side="right") - 1,
                   BAENDER - 1))


def _quote(faelle) -> tuple[int, float]:
    ent = [f for f in faelle if f["ausgang"] in ("ziel", "stop")]
    if not ent:
        return 0, float("nan")
    return len(ent), sum(1 for f in ent if f["ausgang"] == "ziel") / len(ent)


def bereinigter_vorsprung(faelle, grenzen) -> tuple[float, list[dict]]:
    """Die EINE Zahl - und die Baender, die sie tragen."""
    zeilen, summe, gewicht_summe = [], 0.0, 0.0
    for b in range(BAENDER):
        drin = [f for f in faelle if _band(f["stop_relativ"], grenzen) == b]
        h = [f for f in drin if f["frei"] and f["gedeckt"]]
        rest = [f for f in drin if not (f["frei"] and f["gedeckt"])]
        nh, qh = _quote(h)
        nr, qr = _quote(rest)
        zeile = {"band": b, "n_h": nh, "n_rest": nr, "quote_h": qh,
                 "quote_rest": qr,
                 "stop_h": float(np.median([f["stop_relativ"] for f in h]))
                 if h else float("nan"),
                 "stop_rest": float(np.median([f["stop_relativ"]
                                               for f in rest]))
                 if rest else float("nan")}
        zeilen.append(zeile)
        if nh >= MIN_FAELLE and nr >= MIN_FAELLE:
            summe += nh * (qh - qr)
            gewicht_summe += nh
    return (summe / gewicht_summe if gewicht_summe else float("nan")), zeilen


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="data/tradinginfotool.db")
    ap.add_argument("--klasse", default="krypto")
    ap.add_argument("--mindestalter", type=int, default=MINDESTALTER)
    ap.add_argument("--blockplacebo", type=int, default=40)
    ap.add_argument("--blocklaenge", type=int, default=BLOCKLAENGE)
    ap.add_argument("--positiv", type=float, default=0.0)
    ap.add_argument("--datei", default="messwerte_struktur_bereinigt.json")
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    print("=" * 78)
    print("TRAEGT H AUCH BEI GLEICHEN KOSTEN?")
    print("  Kapitel 104: H trifft 6,2 Punkte oefter - und hat 6,2 Punkte")
    print("  mehr Huerde. Hier wird der Stopabstand konstant gehalten.")
    print("=" * 78)
    faelle = _reif(laufe(a.db, a.klasse), a.mindestalter)
    print(f"  {len(faelle)} reife Anker (erste {a.mindestalter} Handelstage "
          f"je Reihe verworfen - Pflicht nach 104.3)")

    if a.positiv:
        rngp = np.random.default_rng(20260825)
        traf = 0
        for f in faelle:
            if f["frei"] and f["gedeckt"] and f["ausgang"] == "stop" \
                    and rngp.random() < a.positiv:
                f["ausgang"] = "ziel"
                traf += 1
        print(f"  ⚠️ POSITIVKONTROLLE AKTIV: {traf} Stops in H zu Zielen "
              f"gemacht - die Probe MUSS das finden.")

    grenzen = _bandgrenzen(faelle)
    vorsprung, zeilen = bereinigter_vorsprung(faelle, grenzen)

    print("\n" + "-" * 78)
    print("JE STOPBAND - H gegen den Rest, bei nahezu gleichen Kosten")
    print("-" * 78)
    print(f"  {'Stopband':16}{'H':>7}{'Quote H':>10}{'Rest':>8}"
          f"{'Quote Rest':>12}{'Diff':>8}{'Kostenrest':>12}")
    zu_grob = False
    for z in zeilen:
        spanne = f"{100 * grenzen[z['band']]:.0f}-" \
                 f"{100 * grenzen[z['band'] + 1]:.0f} %"
        if z["n_h"] < MIN_FAELLE or z["n_rest"] < MIN_FAELLE:
            print(f"  {spanne:16}{z['n_h']:7}   zu wenige Faelle")
            continue
        rest_kosten = abs(z["stop_h"] - z["stop_rest"])
        zu_grob = zu_grob or rest_kosten > MAX_KOSTENREST
        print(f"  {spanne:16}{z['n_h']:7}{100 * z['quote_h']:9.1f} %"
              f"{z['n_rest']:8}{100 * z['quote_rest']:11.1f} %"
              f"{100 * (z['quote_h'] - z['quote_rest']):+7.1f}"
              f"{100 * rest_kosten:11.2f} P")

    print(f"\n  BEREINIGTER VORSPRUNG (die eine Zahl): "
          f"{100 * vorsprung:+.1f} Punkte")
    n_h, q_h = _quote([f for f in faelle if f["frei"] and f["gedeckt"]])
    n_r, q_r = _quote([f for f in faelle
                       if not (f["frei"] and f["gedeckt"])])
    print(f"  UNBEREINIGT waeren es {100 * (q_h - q_r):+.1f} Punkte "
          f"({n_h} gegen {n_r} Faelle)")
    if q_h != q_r and not math.isnan(vorsprung):
        print(f"  -> Von dem rohen Vorsprung bleiben nach Kostenbereinigung "
              f"{100 * vorsprung / (q_h - q_r):.0f} %.")
    if zu_grob:
        print(f"\n  ⚠️ IN MINDESTENS EINEM BAND STEHEN DIE STOPABSTAENDE NOCH "
              f"MEHR ALS {100 * MAX_KOSTENREST:.0f} PUNKTE AUSEINANDER.")
        print("     Dann ist die Schichtung zu grob, um von 'gleichen "
              "Kosten' zu sprechen.")

    # ---- PHASENPROBE ----------------------------------------------------
    print("\n" + "-" * 78)
    print("PHASENPROBE - in allen Lagen oder nur im Baermarkt?")
    print("-" * 78)
    phasen = {}
    for ph in ("bulle", "seitwaerts", "baer"):
        teil = [f for f in faelle if f["phase"] == ph]
        v, _z = bereinigter_vorsprung(teil, grenzen)
        nh = sum(1 for f in teil if f["frei"] and f["gedeckt"])
        if math.isnan(v):
            print(f"  {ph:12}{nh:8} H-Faelle   zu wenige je Band")
            continue
        phasen[ph] = {"n_h": nh, "vorsprung": v}
        print(f"  {ph:12}{nh:8} H-Faelle   {100 * v:+6.1f} Punkte")

    # ---- BLOCK-PERMUTATION ----------------------------------------------
    schwelle = float("nan")
    if a.blockplacebo and not math.isnan(vorsprung):
        print("\n" + "-" * 78)
        print(f"BLOCK-PERMUTATION - {a.blockplacebo} Laeufe, Zeitbloecke von "
              f"{a.blocklaenge} Tagen (Methodik 2.47)")
        print("-" * 78)
        rngb = np.random.default_rng(20260826)
        ordnung: dict = {}
        for pos, f in enumerate(faelle):
            ordnung.setdefault(f["sym"], []).append((f["i"], pos))
        reihen = [np.array([p for _i, p in sorted(v)])
                  for v in ordnung.values()]
        lang = sum(1 for r in reihen if len(r) >= 2 * a.blocklaenge)
        bd = np.array([_band(f["stop_relativ"], grenzen) for f in faelle])
        istH = np.array([f["frei"] and f["gedeckt"] for f in faelle])
        ent = np.array([f["ausgang"] in ("ziel", "stop") for f in faelle])
        ziel = np.array([f["ausgang"] == "ziel" for f in faelle])

        def statistik(z: np.ndarray) -> float:
            """Dieselbe Formel wie `bereinigter_vorsprung`, in Zahlen."""
            summe = gew = 0.0
            for b in range(BAENDER):
                mh = ent & istH & (bd == b)
                mr = ent & ~istH & (bd == b)
                nh, nr = int(mh.sum()), int(mr.sum())
                if nh < MIN_FAELLE or nr < MIN_FAELLE:
                    continue
                summe += nh * (z[mh].mean() - z[mr].mean())
                gew += nh
            return summe / gew if gew else float("nan")

        # ⚠️ GLEICHHEIT BELEGEN, NICHT BEHAUPTEN - die Zahlenfassung muss auf
        # den echten Daten dasselbe liefern wie die Woerterbuchfassung.
        if abs(statistik(ziel) - vorsprung) > 1e-12:
            raise SystemExit("Zahlenfassung weicht ab - Messung ungueltig")
        print("  Zahlenfassung gegen die Woerterbuchfassung geprueft - gleich")
        werte = []
        for _lauf in range(a.blockplacebo):
            gew_ziel = ziel.copy()
            for reihe in reihen:
                if len(reihe) < 2 * a.blocklaenge:
                    continue
                v = int(rngb.integers(0, a.blocklaenge))
                teile = ([reihe[:v]] if v else []) + [
                    reihe[s:s + a.blocklaenge]
                    for s in range(v, len(reihe), a.blocklaenge)]
                gemischt = np.concatenate([teile[j] for j in
                                           rngb.permutation(len(teile))])
                gew_ziel[reihe] = ziel[gemischt]
            w = statistik(gew_ziel)
            if not math.isnan(w):
                werte.append(w)
        schwelle = float(np.quantile(werte, 0.95))
        print(f"  {lang} Reihen lang genug fuer mindestens zwei Bloecke")
        print(f"  groesster Zufallswert  {100 * max(werte):+.1f} Punkte")
        print(f"  SCHWELLE (95 %)        {100 * schwelle:+.1f} Punkte")
        print(f"  gemessen               {100 * vorsprung:+.1f} Punkte")
        streu = float(np.std(werte)) / math.sqrt(len(werte))
        if abs(vorsprung - schwelle) < 2 * streu:
            print(f"  ⚠️ ZU KNAPP - der Abstand liegt im Schaetzfehler der "
                  f"Schwelle (Methodik 2.48).")
            print("     Hier gilt nichts, bevor die Zahl der Laeufe erhoeht "
                  "ist.")
        elif vorsprung > schwelle:
            print("  -> TRAEGT. Die Struktur sagt etwas ueber den Markt, das")
            print("     die Kostenarithmetik nicht schon sagt.")
        else:
            print("  -> TRAEGT NICHT. Der Vorsprung war der weitere Stop -")
            print("     also Kapitel 100-103 unter neuem Namen.")

    print("\n" + "=" * 78)
    if a.datei:
        io.open(a.datei, "w", encoding="utf-8").write(json.dumps({
            "vorsprung_bereinigt": vorsprung, "vorsprung_roh": q_h - q_r,
            "baender": zeilen, "phasen": phasen, "schwelle": schwelle},
            ensure_ascii=False, indent=1, default=float))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
