# -*- coding: utf-8 -*-
"""⚠️⚠️ VORABFESTLEGUNG — geschrieben VOR dem Lauf (21.09.2026).

IST `turnover` WIRKLICH DER AUSREISSER? - H-Hebel gegen alle vier
tragenden Beitraege geprueft.

Nutzerauftrag: *„wichtig sauber arbeiten."* Und der Anlass: ich habe
eine Hypothese aufgestellt (H-Hebel) und darf sie nicht gegen den
einen Fall pruefen, aus dem sie entstanden ist.

═══════════════════════════════════════════════════════════════════════
 DIE HYPOTHESE, DIE HIER AUF DEN PRUEFSTAND KOMMT
═══════════════════════════════════════════════════════════════════════

**H-Hebel:** *Die Positionsgroesse darf nur von Groessen abhaengen, die
sich zwischen zwei Gelegenheiten DESSELBEN Assets aendern koennen. Eine
Groesse, deren Streuung ueberwiegend ZWISCHEN Assets liegt statt
INNERHALB, ist kein Beitrag zur Wahrscheinlichkeit dieses Trades -
sie ist ein dauerhafter Multiplikator auf das Risiko dieses Assets.*

⚠️ Das ist MEINE Hypothese, nicht die des Hauses. Sie steht oder faellt
mit dieser Messung.

═══════════════════════════════════════════════════════════════════════
 DAS MASS - und warum auf dem RANG, nicht auf dem Rohwert
═══════════════════════════════════════════════════════════════════════

Die Bewertung rechnet mit dem QUERSCHNITTSRANG je Tag, nicht mit dem
Rohwert. Also wird der Rang zerlegt:

    ICC  =  Var(zwischen Assets)  /  ( Var(zwischen) + Var(innerhalb) )

    ICC nahe 1   dasselbe Asset steht immer auf demselben Rang
                 -> EIGENSCHAFT
    ICC nahe 0   das Asset wandert durch die Raenge
                 -> ZUSTAND

⚠️ ZWEITES, UNABHAENGIGES MASS: die Rang-Autokorrelation nach 20, 60
und 250 Tagen. Eine Eigenschaft haelt ueber ein Jahr, ein Zustand nicht.
Zwei Masse, die dasselbe sagen muessen - sagen sie Verschiedenes,
stimmt eines von beiden nicht.

═══════════════════════════════════════════════════════════════════════
 KALIBRIERUNG - das Mass wird zuerst an bekannten Polen geeicht
═══════════════════════════════════════════════════════════════════════

    POL 0   reiner Zufall je Tag         -> ICC muss nahe 0 liegen
    POL 1   je Asset konstant (+Rauschen)-> ICC muss nahe 1 liegen

⚠️⚠️ UND EINE MUTATION, DIE BRECHEN MUSS: dieselben Werte, aber die
ASSET-ETIKETTEN je Tag durchgemischt. Damit ist die Assetidentitaet
zerstoert; der ICC MUSS auf das Niveau von Pol 0 fallen. Tut er es
nicht, misst der Schaetzer etwas anderes als behauptet.

⚠️ Das ist die Lehre aus 2.507-kontrolle: meine erste Mutation an jenem
Tag konnte gar nicht brechen und pruefte deshalb nichts. Diese hier
kann brechen.

═══════════════════════════════════════════════════════════════════════
 VORABFESTLEGUNG - was welches Ergebnis BEDEUTET
═══════════════════════════════════════════════════════════════════════

| Ergebnis | Deutung | Folge fuer H-Hebel |
|---|---|---|
| `turnover` deutlich hoeher als die anderen drei | er IST der Ausreisser | H-Hebel traegt, und die Trennlinie liegt zwischen ihm und dem Rest |
| alle vier aehnlich hoch | ALLE Beitraege sind ueberwiegend Eigenschaften | H-Hebel wuerde den Hebel ganz leerraeumen - die Hypothese ist so nicht brauchbar |
| alle vier aehnlich niedrig | auch `turnover` ist ein Zustand | mein Befund 2.506-zerlegung waere in Frage gestellt - dann zuerst DER |
| kein klares Bild | das Mass trennt nicht | H-Hebel ist nicht operationalisierbar, andere Formulierung suchen |

⚠️ **Was KEIN Ergebnis ist:** eine Rangfolge ohne Abstand. Zwei Werte,
die sich um wenige Prozentpunkte unterscheiden, sind bei
verschiedenen Symbolzahlen und Abdeckungen nicht zu trennen.

⚠️ **Die Vergleichbarkeit ist eingeschraenkt und das gehoert benannt:**
die vier Beitraege haben verschiedene Abdeckung (funding 300,
oi_aenderung 122, turnover 66 Symbole) und verschiedene Fenster. Der
ICC-Schaetzer hat eine Stichprobenverzerrung, die mit der Symbolzahl
faellt. Deshalb laeuft POL 0 zusaetzlich auf JEDER der vier
Symbolmengen mit - so ist der Bodenwert je Menge bekannt.

    python phase4_c_eigenschaft_oder_zustand_alle.py
"""
from __future__ import annotations

import os
import sys

import numpy as np

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
os.chdir("D:/CLAUDE_Projects/SoftwareProjekte/TradingInfoTool")
sys.path.insert(0, "D:/CLAUDE_Projects/SoftwareProjekte/TradingInfoTool")

import messe_eigenschaft_beitrag as B                      # noqa: E402
import messe_kandidaten_als_regel as K                     # noqa: E402
import messe_regel_wirksamkeit as W                        # noqa: E402
from messe_alle_kandidaten import zusatzquellen            # noqa: E402

SAAT = 20260921
LAGS = (20, 60, 250)
MIND_TAGE_JE_SYM = 60


def raenge_je_tag(je_tag: dict) -> dict:
    """{tag: {sym: rang}} - genau der Rang, mit dem die Bewertung rechnet."""
    aus = {}
    for t, z in je_tag.items():
        if len(z) < 12:
            continue
        r = W.rang([x["kennzahl"] for x in z])
        aus[t] = {x["sym"]: float(r[i]) for i, x in enumerate(z)}
    return aus


def icc(rang: dict) -> tuple:
    """Anteil der Rangstreuung, der auf die ASSETIDENTITAET entfaellt.

    Gibt (ICC, Symbole, Punkte). Klassische Zerlegung:
        Var_gesamt = Var_zwischen + Var_innerhalb
    """
    je_sym = {}
    for t, d in rang.items():
        for s, r in d.items():
            je_sym.setdefault(s, []).append(r)
    je_sym = {s: v for s, v in je_sym.items() if len(v) >= MIND_TAGE_JE_SYM}
    if len(je_sym) < 5:
        return float("nan"), len(je_sym), 0
    alle = np.concatenate([np.asarray(v, float) for v in je_sym.values()])
    gesamt = float(alle.var())
    if gesamt <= 0:
        return float("nan"), len(je_sym), len(alle)
    # innerhalb: mit der Beobachtungszahl gewichtetes Mittel der
    # Symbolvarianzen
    n = np.array([len(v) for v in je_sym.values()], float)
    v_in = np.array([np.var(np.asarray(v, float))
                     for v in je_sym.values()], float)
    innerhalb = float((n * v_in).sum() / n.sum())
    zwischen = max(0.0, gesamt - innerhalb)
    return zwischen / gesamt, len(je_sym), int(n.sum())


def autokorr(rang: dict, lag: int) -> float:
    """Rang heute gegen Rang in `lag` Tagen - JE SYMBOL, dann gemittelt."""
    je_sym = {}
    for t, d in sorted(rang.items()):
        for s, r in d.items():
            je_sym.setdefault(s, []).append((t, r))
    werte = []
    for s, paare in je_sym.items():
        if len(paare) < lag + 30:
            continue
        v = np.array([p[1] for p in paare], float)
        a, b = v[:-lag], v[lag:]
        if a.std() > 1e-12 and b.std() > 1e-12:
            werte.append(float(np.corrcoef(a, b)[0, 1]))
    return float(np.median(werte)) if werte else float("nan")


def mische_etiketten(rang: dict, rng) -> dict:
    """⚠️ DIE MUTATION, DIE BRECHEN MUSS: Assetetiketten je Tag drehen.

    Die Werte bleiben, nur wem sie gehoeren aendert sich. Damit ist die
    Assetidentitaet zerstoert - der ICC MUSS auf Pol 0 fallen.
    """
    aus = {}
    for t, d in rang.items():
        syms = list(d.keys())
        werte = list(d.values())
        rng.shuffle(syms)
        aus[t] = dict(zip(syms, werte))
    return aus


def zeile(titel, rang, rng=None):
    w, nsym, npkt = icc(rang)
    ak = [autokorr(rang, l) for l in LAGS]
    mut = ""
    if rng is not None:
        wm, _a, _b = icc(mische_etiketten(rang, rng))
        mut = "%.3f" % wm
    print("  %-26s %6d %8d %8.3f   %6.3f %6.3f %6.3f   %6s"
          % (titel, nsym, npkt, w, ak[0], ak[1], ak[2], mut))
    return w, ak


def main() -> int:
    rng = np.random.default_rng(SAAT)
    print("=" * 104)
    print("EIGENSCHAFT ODER ZUSTAND - alle vier tragenden Beitraege am "
          "selben Massstab")
    print("=" * 104)
    print("  ICC = Anteil der RANGstreuung, der auf die "
          "ASSETIDENTITAET entfaellt.")
    print("  nahe 1 = EIGENSCHAFT (immer derselbe Rang) · nahe 0 = "
          "ZUSTAND (wandert)")
    print()
    reihen = B.lade()
    zus = zusatzquellen()
    print("  %-26s %6s %8s %8s   %6s %6s %6s   %6s"
          % ("Groesse", "Syms", "Punkte", "ICC", "AK20", "AK60", "AK250",
             "Mutat."))
    print("  " + "-" * 96)

    # ---- KALIBRIERUNG: die beiden Pole -------------------------------
    je_z = K.baue(reihen, "zufall", None, horizont=20)
    r_z = raenge_je_tag(je_z)
    zeile("POL 0  reiner Zufall", r_z, rng)
    # Pol 1: je Asset konstant plus winziges Rauschen
    syms = sorted({s for d in r_z.values() for s in d})
    fest = {s: float(rng.random()) for s in syms}
    r_1 = {t: {s: fest[s] + 1e-6 * rng.standard_normal()
               for s in d} for t, d in r_z.items()}
    r_1 = {t: dict(zip(d.keys(),
                       W.rang(list(d.values()))))
           for t, d in r_1.items()}
    zeile("POL 1  je Asset konstant", r_1, rng)
    print("  " + "-" * 96)

    # ---- DIE VIER BEITRAEGE ------------------------------------------
    erg = {}
    for art, name in (("funding", "funding"),
                      ("turnover", "turnover"),
                      ("oi_aenderung", "oi_aenderung"),
                      ("schnitt", "schnitt")):
        try:
            je = K.baue(reihen, art, zus.get(art), horizont=20)
        except Exception as exc:                           # noqa: BLE001
            print("  %-26s -> %s" % (name, str(exc)[:60]))
            continue
        r = raenge_je_tag(je)
        if not r:
            print("  %-26s -> leere Welt" % name)
            continue
        erg[name] = zeile(name, r, rng)
        # ⚠️ POL 0 AUF DERSELBEN SYMBOLMENGE - der Bodenwert haengt an
        # der Symbolzahl, und ohne ihn sind die vier nicht vergleichbar.
        s_eig = sorted({s for d in r.values() for s in d})
        r_boden = {t: {s: float(rng.random()) for s in d}
                   for t, d in r.items()}
        wb, _n, _p = icc(r_boden)
        print("  %-26s %6s %8s %8.3f   %6s %6s %6s   %6s"
              % ("   Boden (Zufall, gleiche Menge)", "", "", wb,
                 "", "", "", ""))
    print()
    print("=" * 104)
    print("  AUSWERTUNG NACH DER VORABFESTLEGUNG")
    print("=" * 104)
    print("  ⚠️ Die Spalte ,Mutat.` ist die Probe, die BRECHEN MUSS: "
          "Assetetiketten je Tag")
    print("     gedreht. Faellt sie nicht auf Pol-0-Niveau, misst der "
          "Schaetzer etwas anderes.")
    print()
    if erg:
        s = sorted(erg.items(), key=lambda x: -x[1][0])
        print("  Rangfolge nach ICC:")
        for name, (w, ak) in s:
            print("     %-16s ICC %.3f · Rang haelt nach 250 Tagen zu "
                  "%+.3f" % (name, w, ak[2]))
        hoch, tief = s[0], s[-1]
        print()
        print("  ➤ Spanne: %s %.3f bis %s %.3f (Abstand %.3f)"
              % (hoch[0], hoch[1][0], tief[0], tief[1][0],
                 hoch[1][0] - tief[1][0]))
        print("  ⚠️ Eine Rangfolge OHNE Abstand ist kein Ergebnis. "
              "Erst wenn `turnover`")
        print("     deutlich ueber den anderen liegt, traegt H-Hebel - "
              "liegen alle hoch,")
        print("     wuerde die Hypothese den Hebel ganz leerraeumen und "
              "waere so nicht")
        print("     brauchbar.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
