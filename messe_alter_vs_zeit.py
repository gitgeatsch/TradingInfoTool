"""Asset-Alter oder Marktreife? (25.08.2026, Gegenpruefung zu S4)

⚠️ DIESER KOPF IST DIE VORABFESTLEGUNG, geschrieben BEVOR gerechnet wurde.

DER EINWAND, DER DIESE MESSUNG AUSGELOEST HAT (Nutzer, 25.08.):

    "Denke nicht, dass das Alter der Assets so relevant ist, sondern
     u. U. der Reifegrad des Marktes - aber das musst du feststellen."

Er trifft einen Confounder, den die S4-Auswertung uebersehen hat. Innerhalb
DERSELBEN Reihe liegt das Ankeralter 250-499 IMMER frueher in der Kalenderzeit
als das Band ab 750. Der Befund "der Vorsprung faellt mit dem Ankeralter" ist
damit nicht zu unterscheiden von "der Vorsprung faellt mit dem Kalenderjahr".

Und das ist keine theoretische Sorge. Gemessen (Schwerpunkt der Anker):

    Ankeralter 250-499   Median-Jahr 2022   (25 % 2021, 75 % 2024)
    Ankeralter 500-749   Median-Jahr 2023
    Ankeralter ab 750    Median-Jahr 2024   (25 % 2023, 75 % 2025)

Zwei Jahre Versatz. Dazu kommt, dass H nachweislich phasenabhaengig ist
(bulle +7,6 / seitwaerts +6,0 / baer -6,5, Kapitel 108). Faellt das fruehe
Band ueberwiegend in Bullenphasen und das spaete in Baerenphasen, misst S4
die Marktlage und nennt sie Alter.

DASS ES TRENNBAR IST, steht fest: jedes Altersband hat Anker in jedem Jahr ab
2020. Die Ueberlappung ist ungleich, aber vorhanden.

DIE TRENNUNG. Zwei Achsen, gekreuzt:

    Ankeralter   250-499 . 500-749 . ab 750
    Zeitgruppe   bis 2022 . 2023-2024 . ab 2025

Zeitgruppen statt Einzeljahren, damit die Zellen die Mindestfallzahl
erreichen. Die Grenzen sind vorab gesetzt und NICHT aus den Daten gewaehlt:
sie teilen die Historie in drei etwa gleich lange Abschnitte.

VORAB BENANNT - zwei Groessen, mehr nicht:

    Z1  ALTERSEFFEKT BEI FESTER ZEIT. In der Zeitgruppe mit der besten
        Besetzung: Vorsprung im Band 250-499 minus Vorsprung ab 750.
        Bleibt der Rueckgang bestehen, wenn die Kalenderzeit festgehalten
        wird, dann wirkt das Alter.

    Z2  ZEITEFFEKT BEI FESTEM ALTER. Im Band 250-499: Vorsprung "bis 2022"
        minus Vorsprung "ab 2025". Bleibt der Rueckgang bestehen, wenn das
        Alter festgehalten wird, dann wirkt die Marktreife.

VORAB FESTGELEGT, WAS WELCHES ERGEBNIS BEDEUTET:

    Z1 gross, Z2 klein
        -> DAS ALTER wirkt. S4 steht, der Nutzereinwand ist ausgeraeumt.
    Z1 klein, Z2 gross
        -> ⚠️ DIE MARKTREIFE wirkt. S4 hat die Marktlage gemessen und
           Alter genannt. Der Befund waere dann NICHT "H gilt fuer junge
           Coins", sondern "H galt in einer frueheren Marktphase".
    beide gross
        -> beide Anteile; keine der beiden Erklaerungen allein reicht.
    beide klein
        -> der S4-Rueckgang zerfaellt bei Stratifizierung. Dann ist er
           weder Alter noch Zeit, sondern Zusammensetzung - als Zerlegung
           ablegen (2.51).

⚠️ WAS DIESE MESSUNG NICHT KANN. Die beiden Achsen sind in den Daten
korreliert (das ist der ganze Anlass). Bei ungleicher Besetzung kann eine
Zelle duenn werden und ihr Punktschaetzer wandern. Deshalb wird JE ZELLE die
Fallzahl mitgeschrieben, und Zellen unter der Mindestzahl erscheinen gar
nicht. Ein Ergebnis aus zwei duennen Zellen ist keine Antwort.

⚠️ SUCHPREIS. Neun Zellen werden gerechnet, zwei Groessen sind vorab
benannt. Alles Uebrige ist Beschreibung.

    python messe_alter_vs_zeit.py [--blockplacebo 200]
"""
from __future__ import annotations

import argparse
import io
import json
import sys

import numpy as np

sys.path.insert(0, ".")
from messe_klassen import MIN_FAELLE                              # noqa: E402
from messe_marken import laufe                                    # noqa: E402

ALTER_BAENDER = ((250, 500), (500, 750), (750, 10**9))
ZEIT_GRUPPEN = (("bis 2022", "0000", "2023"),
                ("2023-2024", "2023", "2025"),
                ("ab 2025", "2025", "9999"))
HORIZONT = 120
BLOCKLAENGE = 250


def _abandname(von: int, bis: int) -> str:
    return f"{von}-{bis if bis < 10**8 else '+'}"


def _vorsprung(ziel, istH, maske) -> float:
    mh, mr = maske & istH, maske & ~istH
    if int(mh.sum()) < MIN_FAELLE or int(mr.sum()) < MIN_FAELLE:
        return float("nan")
    return float(ziel[mh].mean()) - float(ziel[mr].mean())


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="data/messdaten.db")
    ap.add_argument("--klasse", default="krypto")
    ap.add_argument("--blockplacebo", type=int, default=200)
    ap.add_argument("--positivkontrolle", type=int, default=300)
    ap.add_argument("--datei", default="messwerte_alter_vs_zeit.json")
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    print("=" * 78)
    print("ASSET-ALTER ODER MARKTREIFE? - die beiden Achsen gekreuzt")
    print("=" * 78)
    faelle = laufe(a.db, a.klasse, fortschritt=True)

    erst: dict = {}
    for f in faelle:
        erst[f["sym"]] = min(erst.get(f["sym"], f["i"]), f["i"])
    alter = np.array([f["i"] - erst[f["sym"]] for f in faelle])
    jahr = np.array([str(f["datum"])[:4] for f in faelle])
    ziel = np.array([1.0 if (f["ausgang"] == "ziel"
                             and f["tage"] <= HORIZONT) else 0.0
                     for f in faelle])
    istH = np.array([bool(f["frei"] and f["gedeckt"]) for f in faelle])
    sym = np.array([f["sym"] for f in faelle])
    idx = np.array([f["i"] for f in faelle])
    print(f"  {len(faelle)} Anker, {int(istH.sum())} in H")

    # ---- Zellen: Alter x Zeit ----------------------------------------
    zellen, mess = {}, {}
    print("\n" + "-" * 78)
    print("GEMESSEN - Zeilen: Ankeralter, Spalten: Zeitgruppe")
    print("-" * 78)
    kopf = f"  {'Alter':10}" + "".join(f"{z[0]:>22}" for z in ZEIT_GRUPPEN)
    print(kopf)
    for von, bis in ALTER_BAENDER:
        an = _abandname(von, bis)
        zeile = f"  {an:10}"
        for zname, zvon, zbis in ZEIT_GRUPPEN:
            maske = ((alter >= von) & (alter < bis)
                     & (jahr >= zvon) & (jahr < zbis))
            nh = int((maske & istH).sum())
            nr = int((maske & ~istH).sum())
            if nh < MIN_FAELLE or nr < MIN_FAELLE:
                zeile += f"{'(' + str(nh) + ' zu duenn)':>22}"
                continue
            name = f"{an} | {zname}"
            zellen[name] = maske
            mess[name] = _vorsprung(ziel, istH, maske)
            zeile += f"{100 * mess[name]:>+15.2f} (n{nh:>4})"
        print(zeile)

    # ---- Placebo (2.77: ueber die ganze Reihe) ------------------------
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
    rng = np.random.default_rng(20260917)
    rngv = np.random.default_rng(20260918)
    zieh = {n: [] for n in zellen}
    zieh["Z1"], zieh["Z2"] = [], []
    # Die Zeitgruppe mit der besten Besetzung fuer Z1 - VORAB nach Fallzahl,
    # nicht nach Ergebnis.
    kand = [z[0] for z in ZEIT_GRUPPEN
            if f"250-500 | {z[0]}" in zellen and f"750-+ | {z[0]}" in zellen]
    z1_gruppe = max(kand, key=lambda z: int((zellen[f"250-500 | {z}"]
                                             & istH).sum())) if kand else None
    print(f"  Z1 nutzt die Zeitgruppe: {z1_gruppe or 'keine auswertbar'}")
    for _lauf in range(a.blockplacebo):
        bl = schneide(int(rngv.integers(1, BLOCKLAENGE + 1)))
        z = ziel.copy()
        for gr in bl:
            al = np.concatenate(gr)
            z[al] = ziel[np.concatenate([gr[j]
                                         for j in rng.permutation(len(gr))])]
        w = {n: _vorsprung(z, istH, m) for n, m in zellen.items()}
        for n in zellen:
            zieh[n].append(w[n])
        if z1_gruppe:
            zieh["Z1"].append(w[f"250-500 | {z1_gruppe}"]
                              - w[f"750-+ | {z1_gruppe}"])
        if ("250-500 | bis 2022" in w and "250-500 | ab 2025" in w):
            zieh["Z2"].append(w["250-500 | bis 2022"]
                              - w["250-500 | ab 2025"])

    erg = {}
    print(f"\n  {'Zelle':26}{'gemessen':>11}{'Schwelle':>11}"
          f"{'2xStreu':>10}  Urteil")
    for n in zellen:
        gut = [x for x in zieh[n] if x == x]
        if len(gut) < 10:
            continue
        s = float(np.quantile(gut, 0.95))
        streu = float(np.std(gut)) / np.sqrt(len(gut))
        m = mess[n]
        urteil = ("ZU KNAPP" if abs(m - s) < 2 * streu
                  else "TRAEGT" if m > s else "traegt nicht")
        erg[n] = {"vorsprung": m, "schwelle": s, "streu": streu,
                  "urteil": urteil, "n_h": int((zellen[n] & istH).sum())}
        print(f"  {n:26}{100 * m:>+11.2f}{100 * s:>+11.2f}"
              f"{200 * streu:>10.2f}  {urteil}")

    # ---- Z1 und Z2 ----------------------------------------------------
    print("\n" + "=" * 78)
    print("DIE VORAB BENANNTEN GROESSEN")
    print("=" * 78)
    aus = {}
    for kuerzel, titel, paar, ziehung in (
            ("Z1", f"ALTERSEFFEKT bei fester Zeit ({z1_gruppe})",
             (f"250-500 | {z1_gruppe}", f"750-+ | {z1_gruppe}"), "Z1"),
            ("Z2", "ZEITEFFEKT bei festem Alter (Band 250-499)",
             ("250-500 | bis 2022", "250-500 | ab 2025"), "Z2")):
        if paar[0] not in mess or paar[1] not in mess:
            print(f"\n  {kuerzel}  {titel}: nicht auswertbar (Zelle zu duenn)")
            continue
        d = mess[paar[0]] - mess[paar[1]]
        gut = [x for x in zieh[ziehung] if x == x]
        s = float(np.quantile(gut, 0.95))
        streu = float(np.std(gut)) / np.sqrt(len(gut))
        urteil = ("ZU KNAPP" if abs(d - s) < 2 * streu
                  else "TRAEGT" if d > s else "traegt nicht")
        print(f"\n  {kuerzel}  {titel}")
        print(f"      {paar[0]:26} {100 * mess[paar[0]]:+.2f}")
        print(f"      {paar[1]:26} {100 * mess[paar[1]]:+.2f}")
        print(f"      Differenz {100 * d:+.2f} gegen Schwelle {100 * s:+.2f}"
              f" (2xStreu {200 * streu:.2f}) -> {urteil}")
        aus[kuerzel] = {"differenz": d, "schwelle": s, "streu": streu,
                        "urteil": urteil, "zellen": list(paar)}

    if "Z1" in aus and "Z2" in aus:
        print("\n" + "-" * 78)
        d1, d2 = aus["Z1"]["differenz"], aus["Z2"]["differenz"]
        print(f"  Alterseffekt {100 * d1:+.2f}  gegen  "
              f"Zeiteffekt {100 * d2:+.2f}")
        if aus["Z1"]["urteil"] == "TRAEGT" and aus["Z2"]["urteil"] != "TRAEGT":
            print("  -> DAS ALTER wirkt. S4 steht.")
        elif aus["Z2"]["urteil"] == "TRAEGT" and aus["Z1"]["urteil"] != "TRAEGT":
            print("  -> ⚠️ DIE MARKTREIFE wirkt. S4 hat die Marktlage")
            print("     gemessen und sie Alter genannt.")
        elif aus["Z1"]["urteil"] == "TRAEGT" and aus["Z2"]["urteil"] == "TRAEGT":
            print("  -> BEIDE Anteile. Keine Erklaerung allein reicht.")
        else:
            print("  -> WEDER NOCH: der Rueckgang zerfaellt bei")
            print("     Stratifizierung. Als Zerlegung ablegen (2.51).")

    # ---- Positivkontrolle ---------------------------------------------
    pk = None
    if a.positivkontrolle > 0 and erg:
        duenn = min(erg, key=lambda n: erg[n]["n_h"])
        maske = zellen[duenn]
        offen = np.flatnonzero(maske & istH & (ziel == 0.0))
        n_pk = min(a.positivkontrolle, len(offen))
        z2 = ziel.copy()
        z2[np.random.default_rng(20260919).choice(offen, size=n_pk,
                                                  replace=False)] = 1.0
        erwartet = n_pk / max(1, int((maske & istH).sum()))
        gemessen = _vorsprung(z2, istH, maske) - mess[duenn]
        print("\n" + "-" * 78)
        print(f"POSITIVKONTROLLE (93 B) auf {duenn} "
              f"({erg[duenn]['n_h']} H-Faelle)")
        print(f"  ERWARTET {100 * erwartet:+.2f} | GEMESSEN "
              f"{100 * gemessen:+.2f} | Abweichung "
              f"{100 * abs(gemessen - erwartet):.3f}")
        best = abs(gemessen - erwartet) < 0.002
        print(f"  -> {'BESTANDEN' if best else 'DURCHGEFALLEN'}")
        pk = {"zelle": duenn, "erwartet": erwartet, "gemessen": gemessen,
              "bestanden": bool(best)}

    if a.datei:
        io.open(a.datei, "w", encoding="utf-8").write(json.dumps(
            {"horizont": HORIZONT, "z1_gruppe": z1_gruppe, "zellen": erg,
             "vorab": aus, "positivkontrolle": pk},
            ensure_ascii=False, indent=1, default=float))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
