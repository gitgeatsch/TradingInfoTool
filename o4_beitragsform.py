# -*- coding: utf-8 -*-
"""O4 — REGLER ODER SCHALTER? Die Fünftelstufen auf gültiger Basis (06.09.)

## ⚠️ Warum das statt N-46 gemessen wird

N-46 lautete: *„ein Nullpunkt fuer die LAENGS-Form, der die marktweite
Gemeinsamkeit mitzerstoert - ohne ihn ist keine Form baureif."*

**Die Praemisse ist auf drei Ebenen ueberholt:**

1  Die Messung, die das Problem zeigte, ist GESPERRT. F-222 traegt seit
   dem 06.09.: *„Nicht gueltig: die Spannen und Verhaeltnisse"* - und
   „laengs haelt die Ordnung nicht" besteht genau daraus.

2  Der GRUND, die Laengs-Form zu suchen, ist entfallen. Sie wurde gesucht,
   weil der Regel-3-Bezug bei quer „nur indirekt" sei. CLAUDE.md sagt seit
   dem 05./06.09.: **„Regel 3 verbietet NICHT den Querschnittsvergleich."**

3  Die heutigen Messungen sind bereits QUER (Rang je Kalendertag,
   Tagesklammer, messnorm) - also regel-3-konform und gueltig.

## ⚠️⚠️ Und die Aussage, an der die HEBELLEITER haengt, ist ebenfalls gesperrt

F-222: *„`vola` ist ein Schalter - nur das unterste eigene Fuenftel hebt
sich ab. `schnitt50` ist die einzige monotone Groesse."* Das stammt aus dem
ungueltigen Teil.

**Und es ist die entscheidende Aussage:** die Hebelleiter 2-5x braucht eine
ABSTUFUNG. Ein Schalter liefert sie nicht, ein Regler schon.

## Was hier gemessen wird — O4 direkt

    FORM        Fuenftelstufen je Kandidat: monoton (Regler) oder nur EIN
                Fuenftel (Schalter)?
    BASIS       messnorm/messnorm_rand · Tagesklammer · Blockbootstrap ·
                Nullpunkt aus 5 Ziehungen · Trennschaerfe
    MENGE       ⚠️ FREI **und** SELEKTIERT - F-212: die Beitraege wirken
                auf der selektierten Menge anders (funding dort 3x staerker)
    HAELFTEN    beide Historienhaelften einzeln
    MASSSTAB    Mittel UND Rand > +2 R (Schritt 3)

    python o4_beitragsform.py
"""
from __future__ import annotations

import sys
import time

import numpy as np

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import messe_bewertungskennzahl as MB                        # noqa: E402
import messe_eigenschaft_beitrag as B                        # noqa: E402
import messe_kandidaten_als_regel as K                       # noqa: E402
import messe_regel_wirksamkeit as W                          # noqa: E402
import messnorm as N                                         # noqa: E402
import messnorm_rand as R                                    # noqa: E402
from messe_beitrag_auf_auswahl import momentum250            # noqa: E402
from messnorm import Lage                                    # noqa: E402

H, MARKE = 5, 2.0
KANDIDATEN = ("vola", "schnitt50", "amihud")


def stufen(je_tag: dict, marke=None, faecher: int = 5) -> tuple:
    """Die Wirkung je FUENFTEL — daran haengt Regler gegen Schalter.

    Je Kalendertag werden die Werte nach der Kennzahl in Fuenftel geteilt;
    je Fuenftel der Ueberschuss gegenueber dem Tagesmittel. Ueber die Tage
    gemittelt ergibt das die Stufenreihe.

    marke=None  Median-Ueberschuss (Mittelwert-Massstab)
    marke=2.0   Randanteil-Ueberschuss (Rand-Massstab)
    """
    reihen = [[] for _ in range(faecher)]
    for _tag, z in je_tag.items():
        if len(z) < 3 * faecher:
            continue
        w = np.array([x["kennzahl"] for x in z], float)
        y = np.array([x["in_r"] for x in z], float)
        f = np.minimum((W.rang(w) * faecher).astype(int), faecher - 1)
        basis = (float(np.median(y)) if marke is None
                 else float((y > marke).mean()))
        for i in range(faecher):
            m = f == i
            if m.sum() < 3:
                continue
            wert = (float(np.median(y[m])) if marke is None
                    else float((y[m] > marke).mean()))
            reihen[i].append(wert - basis)
    return tuple(float(np.mean(r)) if r else float("nan") for r in reihen), \
        tuple(len(r) for r in reihen)


def _monoton(s) -> str:
    """Regler = monoton fallend oder steigend. Schalter = nur EINES faellt auf."""
    gut = [x for x in s if np.isfinite(x)]
    if len(gut) < 5:
        return "unvollstaendig"
    d = np.diff(gut)
    if all(d < 0) or all(d > 0):
        return "REGLER (monoton)"
    # Schalter: ein Fuenftel weicht weit ab, die uebrigen liegen eng
    ohne = sorted(gut)
    spanne_rest = ohne[-2] - ohne[1]
    spanne_ganz = ohne[-1] - ohne[0]
    if spanne_ganz > 0 and spanne_rest / spanne_ganz < 0.45:
        return "SCHALTER (ein Fuenftel)"
    return "weder noch"


def main() -> int:
    t0 = time.time()
    L = Lage("spot", "einstieg")
    print("Lade Reihen ...", flush=True)
    reihen = B.lade()
    mom = momentum250(reihen)
    welten = {a: K.baue(reihen, a, None, horizont=H) for a in KANDIDATEN}
    for a, w in welten.items():
        syms = len({x["sym"] for z in w.values() for x in z})
        print("  %-10s %d Tage · %d Symbole" % (a, len(w), syms), flush=True)

    def selektiert(je_tag, anteil):
        aus = {}
        for tag, z in je_tag.items():
            mt = mom.get(tag)
            if not mt:
                continue
            syms = [x["sym"] for x in z]
            idx = [i for i, s in enumerate(syms) if s in mt]
            if len(idx) < 20:
                continue
            mw = np.array([mt[syms[i]] for i in idx], float)
            k = max(1, int(round(len(idx) * anteil)))
            sel = np.array(idx)[np.argsort(mw)[-k:]]
            if len(sel) >= 15:
                aus[tag] = [z[i] for i in sel]
        return aus

    print()
    print("=" * 108)
    print("O4 — REGLER ODER SCHALTER?  Die Fuenftelstufen (Fuenftel 0 = "
          "niedrigste Kennzahl)")
    print("=" * 108)
    for menge, mlab in ((1.00, "frei"), (0.20, "20 % selektiert")):
        print("  --- Menge: %s ---" % mlab)
        for art in KANDIDATEN:
            teil = welten[art] if menge >= 1.0 else selektiert(welten[art], menge)
            if len(teil) < 300:
                print("    %-10s   zu wenige Tage (%d)" % (art, len(teil)))
                continue
            for marke, malab in ((None, "Mittel"), (MARKE, "Rand >+2R")):
                s, n = stufen(teil, marke=marke)
                skal = 1.0 if marke is None else 100.0
                print("    %-10s %-10s %s   %s"
                      % (art, malab,
                         " ".join("%+7.4f" % (x * skal) for x in s),
                         _monoton(s)), flush=True)
        print()

    print("=" * 108)
    print("BEIDE HISTORIENHAELFTEN — haelt die Form?")
    print("=" * 108)
    for art in KANDIDATEN:
        tage = sorted(welten[art])
        mitte = tage[len(tage) // 2]
        print("  %s" % art)
        for lab, filt in (("erste Haelfte", lambda t: t < mitte),
                          ("zweite Haelfte", lambda t: t >= mitte)):
            teil = {t: z for t, z in welten[art].items() if filt(t)}
            s, _n = stufen(teil, marke=MARKE)
            print("    %-16s %s   %s"
                  % (lab, " ".join("%+7.4f" % (x * 100) for x in s),
                     _monoton(s)), flush=True)
        print()

    print("=" * 108)
    print("DIE WIRKUNG ALS REGEL — auf beiden Massstaeben, frei")
    print("=" * 108)
    print("  %-10s %-10s %10s %24s %6s  %s"
          % ("Kandidat", "Massstab", "Wirkung", "Band", "Blk", "Urteil"))
    for art in KANDIDATEN:
        for marke, malab in ((None, "Mittel"), (MARKE, "Rand >+2R")):
            rng = np.random.default_rng(N.SAAT)
            try:
                if marke is None:
                    f = N.pruefe(art, welten[art], lage=L, frageart="markt",
                                 zielgroesse="bewegung_r", menge="frei",
                                 rng=rng, horizont=H,
                                 staerken=(0.02, 0.05, 0.10, 0.20))
                else:
                    f = R.pruefe_rand(art, welten[art], lage=L, frageart="markt", menge="frei",
                                      rng=rng, marke=marke, horizont=H,
                                      staerken=(0.02, 0.05, 0.10, 0.20))
            except Exception as e:                           # noqa: BLE001
                print("  %-10s %-10s   %s" % (art, malab, e))
                continue
            u = ("TRAEGT" if f.traegt else
                 "kein Befund" if f.trennschaerfe_in_r is None else
                 "nicht trennbar" if abs(f.wirkung) >= (f.trennschaerfe or 0)
                 else "traegt nicht")
            print("  %-10s %-10s %+10.5f  [%+.5f .. %+.5f] %6d  %s"
                  % (art, malab, f.wirkung, f.unten, f.oben, f.n_bloecke, u),
                  flush=True)

    print()
    print("  ⚠️ Fuer die HEBELLEITER 2-5x braucht es einen REGLER.")
    print("     Ein Schalter loest O4 (der Blocker), aber nicht K1.")
    print()
    print("  Dauer %.1f Minuten" % ((time.time() - t0) / 60.0))
    return 0


if __name__ == "__main__":
    sys.exit(main())
