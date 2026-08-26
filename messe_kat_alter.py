"""Kategorie MAL Ankeralter - was bleibt von Small? (25.08.2026, nach S4)

⚠️ DIESER KOPF IST DIE VORABFESTLEGUNG, geschrieben BEVOR gerechnet wurde.

DER ANLASS. S4 hat gemessen: H traegt nur im Ankeralter 250-499 (+5,24 gegen
Schwelle +4,06). Bei 500-749 (+1,13) und ab 750 (+0,94) traegt es nicht - bei
IDENTISCHER Reihenmenge. Der Vorsprung ist ein Reifeartefakt.

DIE OFFENE RECHNUNG. Kapitel 120/121 haben H je Umsatzkategorie beurteilt und
dabei das Ankeralter NIE herausgerechnet:

    Large +5,9   (S3: kippt bei 2.47-konformen Grenzen)
    Mid   +2,5   (traegt nicht)
    Small +7,9   (S3: haelt in allen drei Blockvarianten)

Small ist damit der letzte Kategorienbefund, der steht. Und Small ist genau
die Kategorie mit den juengsten Reihen. Die Frage ist unausweichlich:

    ⚠️ IST SMALLS VORSPRUNG NUR DAS ALTERSFENSTER?

DIE ACHSEN. Alter = `i - min(i je Symbol)`, also dieselbe Groesse, die `_reif`
zum Schneiden benutzt (messe_struktur_bereinigt:80-84). Baender 250-499,
500-749, ab 750 - deckungsgleich mit S4 bis auf einen Handelstag.
Kategorie = `messe_klassen._kategorie` (BTC / Large / Mid / Small nach
Median-Tagesumsatz).

DIE PERMUTATION laeuft ueber die GANZE Reihe, nicht innerhalb des Bandes
(Methodik 2.77): die Baendergrenzen bleiben stehen, die Ausgaenge wandern
hindurch. Alles andere beantwortete eine andere Frage.

VORAB BENANNT - zwei Groessen, mehr nicht:

    V1  Small, Ankeralter ab 750, gegen seine eigene Schwelle.
        DAS ist die Frage. Traegt H dort, hat Small einen Kern, der das
        Reifeartefakt ueberlebt.
    V2  Small 250-499 MINUS Small ab 750, gegen die Schwelle derselben
        Differenz. Faellt der Vorsprung mit dem Alter wie im Gesamtbild?

VORAB FESTGELEGT, WAS WELCHES ERGEBNIS BEDEUTET:

    V1 traegt
        -> Small hat einen ALTERSUNABHAENGIGEN Kern. Das waere der
           staerkste verbleibende Befund des Projekts, und der erste, der
           eine im Betrieb verfuegbare Achse benutzt (Umsatz).
    V1 traegt nicht, V2 traegt
        -> ⚠️ Smalls Befund IST das Reifeartefakt. Kapitel 121 ist dann in
           derselben Weise beschaedigt wie der Gesamtbefund.
    V1 traegt nicht, V2 auch nicht
        -> nicht entscheidbar auf dieser Basis; als Zerlegung ablegen
           (2.51), NICHT als "Small ist widerlegt".
    keine Zelle traegt und die Positivkontrolle faellt durch
        -> Werkzeugbefund, kein Sachbefund.

⚠️ DER SUCHPREIS. Zwoelf Zellen werden gerechnet, aber nur zwei sind vorab
benannt. Alle uebrigen sind BESCHREIBUNG und duerfen nicht als Bestaetigung
gelesen werden (Methodik: 300 Zellen = +20,5 Punkte Huerde, eine vorab
benannte = +10,2).

⚠️ UND EINE GRENZE, DIE BLEIBT. "Small" wird aus dem Median-Tagesumsatz der
letzten 60 Kerzen gebildet - das ist rueckwaerts und im Betrieb verfuegbar.
Die Kategorie ist also KEINE Zukunftsinformation. Die Reihenlaenge waere es
gewesen (S4, Gegenfrage b); sie kommt hier bewusst nicht vor.

    python messe_kat_alter.py [--blockplacebo 200]
"""
from __future__ import annotations

import argparse
import io
import json
import sys

import numpy as np

sys.path.insert(0, ".")
from messe_klassen import KATEGORIEN, MIN_FAELLE, _kategorie      # noqa: E402
from messe_marken import laufe                                    # noqa: E402

BAENDER = ((250, 500), (500, 750), (750, 10**9))
HORIZONT = 120          # der Betriebszustand, wie in bewerte_neu.BETRIEB
BLOCKLAENGE = 250


def _bandname(von: int, bis: int) -> str:
    return f"{von}-{bis if bis < 10**8 else '+'}"


def _quote(ziel: np.ndarray, maske: np.ndarray) -> float:
    n = int(maske.sum())
    return float(ziel[maske].mean()) if n else float("nan")


def _vorsprung(ziel, istH, maske) -> float:
    mh, mr = maske & istH, maske & ~istH
    if int(mh.sum()) < MIN_FAELLE or int(mr.sum()) < MIN_FAELLE:
        return float("nan")
    return _quote(ziel, mh) - _quote(ziel, mr)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="data/messdaten.db")
    ap.add_argument("--klasse", default="krypto")
    ap.add_argument("--blockplacebo", type=int, default=200)
    ap.add_argument("--positivkontrolle", type=int, default=300)
    ap.add_argument("--datei", default="messwerte_kat_alter.json")
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    print("=" * 78)
    print("KATEGORIE MAL ANKERALTER - was bleibt von Small?")
    print("=" * 78)
    faelle = laufe(a.db, a.klasse, fortschritt=True)

    # ---- Achsen ------------------------------------------------------
    erst: dict = {}
    for f in faelle:
        erst[f["sym"]] = min(erst.get(f["sym"], f["i"]), f["i"])
    alter = np.array([f["i"] - erst[f["sym"]] for f in faelle])
    kat = np.array([_kategorie(f) for f in faelle])
    # ⚠️ VORSICHTIGE LESART (2.54): ein Ablauf zaehlt als Fehlschlag. Ohne
    # Haltedauerpruefung waere das Ergebnis nicht mit S4 vergleichbar.
    # ⚠️ f["tage"] ABSICHTLICH OHNE .get(): fehlte das Feld, wuerde ein
    # Vorgabewert 0 jeden Treffer als "im Horizont" durchwinken und die
    # Quote still anheben. Ein KeyError ist hier das bessere Verhalten.
    ziel = np.array([1.0 if (f["ausgang"] == "ziel"
                             and f["tage"] <= HORIZONT) else 0.0
                     for f in faelle])
    istH = np.array([bool(f["frei"] and f["gedeckt"]) for f in faelle])
    sym = np.array([f["sym"] for f in faelle])
    idx = np.array([f["i"] for f in faelle])
    print(f"  {len(faelle)} Anker, {len(set(sym))} Symbole, "
          f"{int(istH.sum())} davon in H")

    # ⚠️ EINE STILLE ZUORDNUNG, DIE GENAU DIE GEPRUEFTE KATEGORIE TRIFFT.
    # `_kategorie` rechnet `u = f["umsatz"] or 0.0` - ein FEHLENDER Umsatz
    # wird damit zu 0 und landet in "Small". Wer Small beurteilt, ohne das
    # zu wissen, beurteilt teilweise die Datenluecke. Deshalb ausgewiesen.
    ohne = np.array([f["umsatz"] is None for f in faelle])
    n_small = int((kat == "Small").sum())
    print(f"  ⚠️ ohne Umsatzangabe: {int(ohne.sum())} Anker "
          f"({100 * ohne.mean():.1f} %) - sie landen per `or 0.0` in Small")
    if n_small:
        print(f"     Anteil an Small: {int((ohne & (kat == 'Small')).sum())}"
              f" von {n_small} = "
              f"{100 * int((ohne & (kat == 'Small')).sum()) / n_small:.1f} %")

    # ---- Zellen ------------------------------------------------------
    zellen, messwerte = {}, {}
    print("\n" + "-" * 78)
    print("GEMESSEN")
    print("-" * 78)
    print(f"  {'Zelle':18}{'H-Faelle':>10}{'Quote H':>10}"
          f"{'Quote Rest':>12}{'Vorsprung':>11}")
    for k in KATEGORIEN:
        for von, bis in BAENDER:
            maske = (kat == k) & (alter >= von) & (alter < bis)
            nh = int((maske & istH).sum())
            nr = int((maske & ~istH).sum())
            name = f"{k} {_bandname(von, bis)}"
            if nh < MIN_FAELLE or nr < MIN_FAELLE:
                print(f"  {name:18}{nh:>10}   unter MIN_FAELLE "
                      f"({MIN_FAELLE}) - nicht auswertbar")
                continue
            zellen[name] = maske
            messwerte[name] = _vorsprung(ziel, istH, maske)
            print(f"  {name:18}{nh:>10}"
                  f"{100 * _quote(ziel, maske & istH):>9.1f}%"
                  f"{100 * _quote(ziel, maske & ~istH):>11.1f}%"
                  f"{100 * messwerte[name]:>+11.2f}")

    # Zusatzzelle, nicht vorab benannt: Small OHNE die umsatzlosen Faelle.
    # Reine Beschreibung - sie sagt, wie viel von Small die Datenluecke ist.
    for von, bis in BAENDER:
        maske = ((kat == "Small") & ~ohne & (alter >= von) & (alter < bis))
        if (int((maske & istH).sum()) >= MIN_FAELLE
                and int((maske & ~istH).sum()) >= MIN_FAELLE):
            name = f"Small* {_bandname(von, bis)}"
            zellen[name] = maske
            messwerte[name] = _vorsprung(ziel, istH, maske)
            print(f"  {name:18}{int((maske & istH).sum()):>10}"
                  f"{100 * _quote(ziel, maske & istH):>9.1f}%"
                  f"{100 * _quote(ziel, maske & ~istH):>11.1f}%"
                  f"{100 * messwerte[name]:>+11.2f}")
    print("  (Small* = Small ohne die Anker ohne Umsatzangabe)")

    # ---- Placebo ueber die ganze Reihe (2.77) ------------------------
    ordn: dict = {}
    for pos in range(len(faelle)):
        ordn.setdefault(sym[pos], []).append((int(idx[pos]), pos))
    sortiert = {s: sorted(v) for s, v in ordn.items()}

    def schneide(versatz: int) -> list:
        aus = []
        for vv in sortiert.values():
            gr: list = []
            for ii, pos in vv:
                schl = (ii - versatz) // BLOCKLAENGE
                if not gr or gr[-1][0] != schl:
                    gr.append([schl, []])
                gr[-1][1].append(pos)
            if len(gr) >= 2:
                aus.append([np.array(g[1]) for g in gr])
        return aus

    print("\n" + "-" * 78)
    print(f"BLOCK-PERMUTATION ueber die ganze Reihe, {a.blockplacebo} Laeufe")
    print("-" * 78)
    rng = np.random.default_rng(20260914)
    rngv = np.random.default_rng(20260915)
    zieh = {n: [] for n in zellen}
    zieh["V2"] = []
    for _lauf in range(a.blockplacebo):
        bl = schneide(int(rngv.integers(1, BLOCKLAENGE + 1)))
        z = ziel.copy()
        for gr in bl:
            al = np.concatenate(gr)
            z[al] = ziel[np.concatenate([gr[j]
                                         for j in rng.permutation(len(gr))])]
        w = {}
        for n, maske in zellen.items():
            w[n] = _vorsprung(z, istH, maske)
            zieh[n].append(w[n])
        if "Small 250-500" in w and "Small 750-+" in w:
            zieh["V2"].append(w["Small 250-500"] - w["Small 750-+"])

    ergebnisse = {}
    print(f"  {'Zelle':18}{'gemessen':>11}{'Schwelle':>11}"
          f"{'2xStreu':>10}  Urteil")
    for n in zellen:
        gut = [x for x in zieh[n] if x == x]
        if len(gut) < 10:
            print(f"  {n:18}  Placebo unbrauchbar")
            continue
        s = float(np.quantile(gut, 0.95))
        streu = float(np.std(gut)) / np.sqrt(len(gut))
        m = messwerte[n]
        urteil = ("ZU KNAPP" if abs(m - s) < 2 * streu
                  else "TRAEGT" if m > s else "traegt nicht")
        ergebnisse[n] = {"vorsprung": m, "schwelle": s, "streu": streu,
                         "urteil": urteil,
                         "n_h": int((zellen[n] & istH).sum())}
        print(f"  {n:18}{100 * m:>+11.2f}{100 * s:>+11.2f}"
              f"{200 * streu:>10.2f}  {urteil}")

    # ---- V1 und V2 ---------------------------------------------------
    print("\n" + "=" * 78)
    print("DIE VORAB BENANNTEN GROESSEN")
    print("=" * 78)
    v1 = ergebnisse.get("Small 750-+")
    if v1:
        print(f"  V1  Small ab 750 : {100 * v1['vorsprung']:+.2f} gegen "
              f"Schwelle {100 * v1['schwelle']:+.2f}  -> {v1['urteil']}")
        if v1["urteil"] == "TRAEGT":
            print("      ⚠️ Small hat einen ALTERSUNABHAENGIGEN Kern.")
        else:
            print("      Smalls Vorsprung ueberlebt das Altersfenster NICHT.")
    else:
        print("  V1  Small ab 750: nicht auswertbar (unter MIN_FAELLE)")

    v2 = None
    if "Small 250-500" in messwerte and "Small 750-+" in messwerte:
        d = messwerte["Small 250-500"] - messwerte["Small 750-+"]
        gut = [x for x in zieh["V2"] if x == x]
        s = float(np.quantile(gut, 0.95))
        streu = float(np.std(gut)) / np.sqrt(len(gut))
        urteil = ("ZU KNAPP" if abs(d - s) < 2 * streu
                  else "TRAEGT" if d > s else "traegt nicht")
        print(f"\n  V2  Small 250-499 {100 * messwerte['Small 250-500']:+.2f}"
              f"  minus  Small ab 750 {100 * messwerte['Small 750-+']:+.2f}")
        print(f"      Differenz {100 * d:+.2f} gegen Schwelle "
              f"{100 * s:+.2f} (2xStreu {200 * streu:.2f}) -> {urteil}")
        v2 = {"differenz": d, "schwelle": s, "streu": streu, "urteil": urteil}

    # ---- Positivkontrolle --------------------------------------------
    pk = None
    if a.positivkontrolle > 0 and ergebnisse:
        duenn = min(ergebnisse, key=lambda n: ergebnisse[n]["n_h"])
        maske = zellen[duenn]
        offen = np.flatnonzero(maske & istH & (ziel == 0.0))
        n_pk = min(a.positivkontrolle, len(offen))
        z2 = ziel.copy()
        z2[np.random.default_rng(20260916).choice(offen, size=n_pk,
                                                  replace=False)] = 1.0
        erwartet = n_pk / max(1, int((maske & istH).sum()))
        gemessen = _vorsprung(z2, istH, maske) - messwerte[duenn]
        print("\n" + "-" * 78)
        print(f"POSITIVKONTROLLE (93 B) auf der duennsten Zelle: {duenn}"
              f" ({ergebnisse[duenn]['n_h']} H-Faelle)")
        print("-" * 78)
        print(f"  ERWARTET {100 * erwartet:+.2f} | "
              f"GEMESSEN {100 * gemessen:+.2f} | "
              f"Abweichung {100 * abs(gemessen - erwartet):.3f}")
        best = abs(gemessen - erwartet) < 0.002
        print(f"  -> {'BESTANDEN' if best else 'DURCHGEFALLEN'}")
        pk = {"zelle": duenn, "n": n_pk, "erwartet": erwartet,
              "gemessen": gemessen, "bestanden": bool(best)}

    if a.datei:
        io.open(a.datei, "w", encoding="utf-8").write(json.dumps(
            {"horizont": HORIZONT, "blocklaenge": BLOCKLAENGE,
             "zellen": ergebnisse, "V1": v1, "V2": v2,
             "positivkontrolle": pk},
            ensure_ascii=False, indent=1, default=float))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
