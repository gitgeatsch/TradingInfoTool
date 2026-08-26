"""Warum faellt H mit steigendem Reifeschnitt? (25.08.2026, S4-Gegenpruefung)

⚠️ DIESER KOPF IST DIE VORABFESTLEGUNG, geschrieben BEVOR gerechnet wurde.

S4 hat gemessen: H traegt bei Mindestalter 250 (+3,8 gegen +3,4), faellt bei
500 (+2,0 gegen +3,7) und bei 750 (+1,0 gegen +4,9). Die Quote selbst faellt
monoton - 38,1 -> 35,7 -> 33,8 % - es ist also nicht bloss die duennere Basis.

DAS PROBLEM: ZWEI ERKLAERUNGEN, EIN BEFUND. Mit steigendem Mindestalter
fallen nicht nur alte Anker weg, sondern GANZE REIHEN: 523 -> 470 -> 401.
Die verschwundenen sind die kurzen - tendenziell junge Werte. Damit sind
zwei voellig verschiedene Lesarten moeglich:

    (a) REIFEARTEFAKT. Innerhalb derselben Reihe sind spaete Anker
        schlechter. Dann misst H bei jungen Reihen Datenlage statt Markt,
        und der Befund ist beschaedigt.

    (b) AUSWAHLEFFEKT. Die kurzen Reihen, die ganz herausfallen, tragen den
        Effekt. Dann ist H kein Artefakt, sondern eine Eigenschaft junger
        bzw. kleiner Werte - und die Frage waere, wo genau es gilt.

Beide erklaeren dieselben Zahlen. Sie fuehren zu entgegengesetzten
Konsequenzen: (a) entwertet H, (b) verortet es.

DIE TRENNUNG: dieselben Reihen, verschiedenes Ankeralter. Nur Reihen, die
ueberhaupt bis 750 reichen, werden nach Ankeralter gebaendert. Faellt der
Vorsprung DORT mit dem Band, gilt (a). Bleibt er dort stabil und liegt der
Unterschied zwischen kurzen und langen Reihen, gilt (b).

    LANG  = die Reihe hat Anker mit Alter >= 750
    KURZ  = die Reihe endet vorher

    Baender nach Ankeralter (Handelstage seit Reihenbeginn):
      250-499 . 500-749 . ab 750

VORAB FESTGELEGT, WAS WELCHES ERGEBNIS BEDEUTET:

    LANG faellt ueber die Baender, KURZ 250-499 wie LANG 250-499
        -> (a) REIFEARTEFAKT. H ist beschaedigt.
    LANG bleibt stabil, KURZ 250-499 traegt deutlich mehr
        -> (b) AUSWAHLEFFEKT. H gilt bei kurzen Reihen, nicht generell.
    beides zugleich
        -> beide Anteile; dann entscheidet die Groesse, was ueberwiegt.
    keine Zelle traegt
        -> Positivkontrolle pruefen, bevor irgendetwas geschlossen wird.

⚠️ DIE ZELLEN SIND KLEIN. Bei sechs angesehenen Zellen ist der Suchpreis zu
zahlen; die Schwelle je Zelle ist deshalb OHNE Anspruch auf Bestaetigung zu
lesen, solange nicht eine Zelle vorab benannt war. Vorab benannt ist genau
eine: LANG, Band 250-499 gegen LANG, Band ab 750. Alles andere ist
Beschreibung.

    python messe_reifeband.py [--blockplacebo 200]
"""
from __future__ import annotations

import argparse
import io
import json
import sys

import numpy as np

sys.path.insert(0, ".")
from bewerte_neu import BETRIEB, _pruefe                         # noqa: E402
from messe_dosis import MIN_FAELLE, sammle                       # noqa: E402

SCHNITT = 250          # der Bestandswert, auf dem gesammelt wird
BAENDER = ((250, 500), (500, 750), (750, 10**9))
LANG_AB = 750          # eine Reihe gilt als "lang", wenn sie so weit reicht


def _alter(rz) -> tuple[np.ndarray, dict]:
    """Ankeralter in Handelstagen seit Reihenbeginn, je Reihe der Hoechstwert.

    ⚠️ `off` STEHT NICHT IN DEN DATEN, wird aber gebraucht: `sammle` beginnt
    je Reihe bei `off + 1 + SCHNITT`. Der kleinste `i` einer Reihe ist also
    genau dieser Startwert - daraus folgt `off` rueckwaerts. Das ist keine
    Schaetzung, sondern die Umkehrung einer Zeile.
    """
    r, i = rz["r"], rz["i"]
    off, hoch = {}, {}
    for reihe in np.unique(r):
        werte = i[r == reihe]
        off[reihe] = int(werte.min()) - 1 - SCHNITT
    alter = np.array([int(i[k]) - off[int(r[k])] for k in range(len(r))])
    for reihe in np.unique(r):
        hoch[int(reihe)] = int(alter[r == reihe].max())
    return alter, hoch


def _vorsprung(rz, maske, aus, tg, hz) -> float:
    """H gegen Nicht-H innerhalb der Maske, vorsichtige Lesart (2.54)."""
    mh, mr = maske & rz["h"], maske & ~rz["h"]
    nh, nr = int(mh.sum()), int(mr.sum())
    if nh < MIN_FAELLE or nr < MIN_FAELLE:
        return float("nan")
    return (int((mh & (aus == 1) & (tg <= hz)).sum()) / nh
            - int((mr & (aus == 1) & (tg <= hz)).sum()) / nr)


def _pruefe_band(rz, zellen, hz, laeufe, blocklaenge=250):
    """Block-Permutation ueber die GANZE Reihe, gemessen JE ALTERSBAND.

    ⚠️ WARUM NICHT BLOECKE JE BAND (der erste, verworfene Aufbau). Die
    Baender sind 250 Handelstage breit, die Blocklaenge ist es auch - je
    Reihe und Band entstuende also etwa EIN Block. Die Permutation koennte
    nichts mischen, und die Schwelle waere kuenstlich breit (gemessen:
    +16,3 Punkte, wo der Messwert +5,2 betraegt). Das ist Methodik 2.52.

    ⚠️ UND ES IST NICHT NUR ZU GROB, SONDERN DIE FALSCHE NULLHYPOTHESE. Die
    Frage lautet "macht das Ankeralter einen Unterschied?". Unter der
    Nullhypothese darf ein Ausgang aus einem spaeten Band genauso gut in
    einem fruehen stehen. Genau das leistet die Permutation ueber die ganze
    Reihe: die Baendergrenzen bleiben stehen, die Ausgaenge wandern
    hindurch. Die Blockstruktur haelt dabei die zeitliche Abhaengigkeit
    fest, die es zu respektieren gilt.
    """
    ordn = {}
    for pos in range(len(rz["r"])):
        ordn.setdefault(int(rz["r"][pos]), []).append((int(rz["i"][pos]), pos))
    sortiert = {r: sorted(v) for r, v in ordn.items()}

    def schneide(versatz):
        aus_ = []
        for vv in sortiert.values():
            gr = []
            for ii, pos in vv:
                schl = (ii - versatz) // blocklaenge
                if not gr or gr[-1][0] != schl:
                    gr.append([schl, []])
                gr[-1][1].append(pos)
            if len(gr) >= 2:
                aus_.append([np.array(g[1]) for g in gr])
        return aus_

    rng = np.random.default_rng(20260912)
    rngv = np.random.default_rng(20260913)
    zieh = {name: [] for name in zellen}
    zieh["UNTERSCHIED"] = []
    for _lauf in range(laeufe):
        bl = schneide(int(rngv.integers(1, blocklaenge + 1)))
        aus, tg = rz["aus"].copy(), rz["tg"].copy()
        for gr in bl:
            al = np.concatenate(gr)
            neu = np.concatenate([gr[j] for j in rng.permutation(len(gr))])
            aus[al] = rz["aus"][neu]
            tg[al] = rz["tg"][neu]
        werte = {}
        for name, maske in zellen.items():
            werte[name] = _vorsprung(rz, maske, aus, tg, hz)
            zieh[name].append(werte[name])
        # DIE VORAB BENANNTE GROESSE: fruehes Band gegen spaetes, LANG.
        if "LANG 250-500" in werte and "LANG 750-+" in werte:
            zieh["UNTERSCHIED"].append(werte["LANG 250-500"]
                                       - werte["LANG 750-+"])
    return zieh


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="data/messdaten.db")
    ap.add_argument("--klasse", default="krypto")
    ap.add_argument("--blockplacebo", type=int, default=200)
    ap.add_argument("--blocklaenge", type=int, default=250)
    ap.add_argument("--positivkontrolle", type=int, default=300)
    ap.add_argument("--datei", default="messwerte_reifeband.json")
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    print("=" * 78)
    print("WARUM FAELLT H MIT DEM REIFESCHNITT? - Artefakt oder Auswahl")
    print("=" * 78)
    _z, _stops, roh = sammle(a.db, a.klasse, None, SCHNITT)
    k, crv, hz = BETRIEB
    rz = roh[(k, crv)]
    alter, hoch = _alter(rz)
    lang = np.array([hoch[int(x)] >= LANG_AB for x in rz["r"]])
    n_reihen = len(hoch)
    n_lang = sum(1 for v in hoch.values() if v >= LANG_AB)
    print(f"  {len(rz['r'])} Anker aus {n_reihen} Reihen")
    print(f"  davon LANG (reicht bis {LANG_AB} HT): {n_lang} Reihen, "
          f"{int(lang.sum())} Anker")
    print(f"  KURZ: {n_reihen - n_lang} Reihen, {int((~lang).sum())} Anker")

    # ---- Die Zellen ------------------------------------------------
    zellen, messwerte = {}, {}
    for gruppe, maske_g in (("LANG", lang), ("KURZ", ~lang)):
        for von, bis in BAENDER:
            maske = maske_g & (alter >= von) & (alter < bis)
            name = f"{gruppe} {von}-{bis if bis < 10**8 else '+'}"
            nh = int((maske & rz["h"]).sum())
            if nh < MIN_FAELLE:
                print(f"  {name}: nur {nh} H-Faelle (Mindestzahl "
                      f"{MIN_FAELLE}) - nicht auswertbar")
                continue
            zellen[name] = maske
            messwerte[name] = _vorsprung(rz, maske, rz["aus"], rz["tg"], hz)

    print(chr(10) + "-" * 78)
    print("GEMESSEN - dieselben Reihen, nach Ankeralter gebaendert")
    print("-" * 78)
    print(f"  {'Zelle':16}{'H-Faelle':>10}{'Quote H':>10}"
          f"{'Quote Rest':>12}{'Vorsprung':>11}")
    for name, maske in zellen.items():
        mh, mr = maske & rz["h"], maske & ~rz["h"]
        qh = int((mh & (rz["aus"] == 1) & (rz["tg"] <= hz)).sum()) / int(mh.sum())
        qr = int((mr & (rz["aus"] == 1) & (rz["tg"] <= hz)).sum()) / int(mr.sum())
        print(f"  {name:16}{int(mh.sum()):>10}{100 * qh:>9.1f}%"
              f"{100 * qr:>11.1f}%{100 * messwerte[name]:>+11.2f}")

    # ---- Placebo: Permutation ueber die GANZE Reihe -------------------
    print(chr(10) + "-" * 78)
    print(f"BLOCK-PERMUTATION ueber die ganze Reihe, {a.blockplacebo} Laeufe")
    print("  (Baendergrenzen bleiben stehen, die Ausgaenge wandern hindurch)")
    print("-" * 78)
    zieh = _pruefe_band(rz, zellen, hz, a.blockplacebo, a.blocklaenge)
    ergebnisse = {}
    print(f"  {'Zelle':16}{'gemessen':>11}{'Schwelle':>11}"
          f"{'2xStreu':>10}  Urteil")
    for name in zellen:
        w = [x for x in zieh[name] if x == x]
        if len(w) < 10:
            print(f"  {name:16}  Placebo unbrauchbar ({len(w)} gueltige)")
            continue
        s = float(np.quantile(w, 0.95))
        streu = float(np.std(w)) / np.sqrt(len(w))
        m = messwerte[name]
        urteil = ("ZU KNAPP" if abs(m - s) < 2 * streu
                  else "TRAEGT" if m > s else "traegt nicht")
        ergebnisse[name] = {"vorsprung": m, "schwelle": s,
                            "streu": streu, "urteil": urteil,
                            "n_h": int((zellen[name] & rz["h"]).sum())}
        print(f"  {name:16}{100 * m:>+11.2f}{100 * s:>+11.2f}"
              f"{200 * streu:>10.2f}  {urteil}")

    # ---- Die VORAB BENANNTE Groesse ----------------------------------
    print(chr(10) + "=" * 78)
    print("DIE VORAB BENANNTE FRAGE: faellt der Vorsprung INNERHALB")
    print("derselben Reihen mit dem Ankeralter?")
    print("=" * 78)
    unt = None
    if "LANG 250-500" in messwerte and "LANG 750-+" in messwerte:
        d = messwerte["LANG 250-500"] - messwerte["LANG 750-+"]
        w = [x for x in zieh["UNTERSCHIED"] if x == x]
        s = float(np.quantile(w, 0.95))
        streu = float(np.std(w)) / np.sqrt(len(w))
        urteil = ("ZU KNAPP" if abs(d - s) < 2 * streu
                  else "TRAEGT" if d > s else "traegt nicht")
        print(f"  LANG 250-499  {100 * messwerte['LANG 250-500']:+.2f}")
        print(f"  LANG ab 750   {100 * messwerte['LANG 750-+']:+.2f}")
        print(f"  UNTERSCHIED   {100 * d:+.2f} Punkte")
        print(f"  SCHWELLE      {100 * s:+.2f}  (2xStreu {200 * streu:.2f})")
        print(f"  -> {urteil}")
        if urteil == "TRAEGT":
            print(chr(10) + "  ⚠️ Das Ankeralter macht einen Unterschied, der ueber")
            print("     dem Zufall liegt - bei IDENTISCHER Reihenmenge.")
            print("     Das ist das Reifeartefakt (a), nicht die Auswahl (b).")
        unt = {"unterschied": d, "schwelle": s, "streu": streu,
               "urteil": urteil}

    # ---- KURZ gegen LANG bei gleichem Alter --------------------------
    if "KURZ 250-500" in messwerte and "LANG 250-500" in messwerte:
        print(chr(10) + "-" * 78)
        print("GEGENFRAGE (b): tragen die KURZEN Reihen den Effekt?")
        print("-" * 78)
        print(f"  KURZ 250-499  {100 * messwerte['KURZ 250-500']:+.2f}")
        print(f"  LANG 250-499  {100 * messwerte['LANG 250-500']:+.2f}")
        print(f"  Unterschied   "
              f"{100 * (messwerte['KURZ 250-500'] - messwerte['LANG 250-500']):+.2f}"
              f" Punkte - gleiches Ankeralter, andere Reihen")

    # ---- POSITIVKONTROLLE auf der duennsten AUSWERTBAREN Zelle --------
    pk = None
    if a.positivkontrolle > 0 and ergebnisse:
        duenn = min(ergebnisse, key=lambda n: ergebnisse[n]["n_h"])
        maske = zellen[duenn]
        aus2, tg2 = rz["aus"].copy(), rz["tg"].copy()
        offen = np.flatnonzero(maske & rz["h"]
                               & ~((rz["aus"] == 1) & (rz["tg"] <= hz)))
        n_pk = min(a.positivkontrolle, len(offen))
        wahl = np.random.default_rng(20260911).choice(offen, size=n_pk,
                                                      replace=False)
        aus2[wahl] = 1
        tg2[wahl] = 1
        erwartet = n_pk / max(1, int((maske & rz["h"]).sum()))
        gemessen = (_vorsprung(rz, maske, aus2, tg2, hz)
                    - messwerte[duenn])
        print(chr(10) + "-" * 78)
        print(f"POSITIVKONTROLLE (93 B) auf der duennsten Zelle: {duenn}")
        print(f"  ({ergebnisse[duenn]['n_h']} H-Faelle)")
        print("-" * 78)
        print(f"  {n_pk} von {len(offen)} offenen H-Faellen auf 'Ziel' gesetzt")
        print(f"  ERWARTET {100 * erwartet:+.2f} Punkte")
        print(f"  GEMESSEN {100 * gemessen:+.2f} Punkte  "
              f"(Abweichung {100 * abs(gemessen - erwartet):.3f})")
        best = abs(gemessen - erwartet) < 0.002
        print(f"  -> {'BESTANDEN' if best else 'DURCHGEFALLEN'}")
        pk = {"zelle": duenn, "n": n_pk, "erwartet": erwartet,
              "gemessen": gemessen, "bestanden": bool(best)}

    if a.datei:
        io.open(a.datei, "w", encoding="utf-8").write(json.dumps(
            {"schnitt": SCHNITT, "lang_ab": LANG_AB,
             "blocklaenge": a.blocklaenge,
             "reihen_gesamt": n_reihen, "reihen_lang": n_lang,
             "zellen": ergebnisse, "vorab_benannt": unt,
             "positivkontrolle": pk},
            ensure_ascii=False, indent=1, default=float))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
