# -*- coding: utf-8 -*-
"""Die VIER HEBELSTUFEN - traegt 2x/3x/4x/5x gegen konstanten Hebel?

**26.09.2026**, Nutzervorgabe woertlich: *"warum soll es nicht moeglich
sein, je nach Qualitaet des Signals - also angenommene HOEHE und RISIKO -
das in 4 TEILE zu teilen ... es soll das positive Chance-Risiko-Verhaeltnis
die Hebelhoehe bestimmen und je nach Verhaeltnis, gemessen von dir, 4
TEILE: HEBEL 2x oder 3x oder 4x oder 5x auf Basis deiner MESSUNGEN"*.

Vorabfestlegung: `Basisinfos/Vorabfestlegung_27_Vier_Hebelstufen_26_09.md`

═══════════════════════════════════════════════════════════════════════
 ⛔ WAS AN DER VORIGEN VORLAGE FALSCH WAR
═══════════════════════════════════════════════════════════════════════

Ich hatte die Hebelhoehe aus KELLY abgeleitet. Kelly beantwortet aber
eine andere Frage:

    Wie viel KAPITAL INSGESAMT darf im Feuer sein?
        -> Kelly, Positionszahl, Korrelation
    Wie hoch ist der Hebel DIESES EINEN Trades?
        -> Chance-Risiko-Verhaeltnis + RM-11

Weil die Hoehe aus Kelly kam, musste die Positionszahl herein - und dann
die Korrelation, um sie zu korrigieren. Ein Umweg zu einer Frage, die
nicht gestellt war.

⚠️ 2.627 hatte es bereits richtig: *die Hebelhoehe folgt dem RISIKO,
nicht der Statistik*.

═══════════════════════════════════════════════════════════════════════
 DER PRUEFSTAND - er steht seit 2.508
═══════════════════════════════════════════════════════════════════════

Logwachstum `ln(1 + einsatz * hebel * kursprozent)` je Anker. Sizing
beurteilt man am GEOMETRISCHEN Wachstum, nicht am Mittelwert.

⚠️ Der Vergleich laeuft bei GLEICHEM mittleren Hebel - sonst misst man,
dass mehr Hebel mehr bewegt, statt ob die ZUORDNUNG traegt.

⚠️ NUR LESEN.  python messe_vier_hebelstufen.py [--symbole N]
"""
from __future__ import annotations

import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import messnorm as N                                            # noqa: E402
from agent.krypto.hebel_risk_gate import max_safe_hebel         # noqa: E402
from messe_hebelkurve_stetig import (                           # noqa: E402
    lade, kurve, kelly_von, HZ, STOP, AUSL, ABST, MARGE)

EINSATZ = 0.25          # Anteil des Kontos je Position (reiner Massstab -
#                         er trifft ALLE Varianten gleich und faellt im
#                         Vergleich heraus)
BLOCK = 60              # Blockbootstrap, wie in 2.508
ZIEHUNGEN = 400
SAAT = 20260926

# Die Varianten. ⚠️ Alle mit demselben MITTLEREN Hebel, sonst ist der
# Vergleich wertlos (Falle 1 der Vorabfestlegung).
VARIANTEN = (
    ("gestuft 5/4/3/2", (5.0, 4.0, 3.0, 2.0)),
    ("flach 3,5", (3.5, 3.5, 3.5, 3.5)),
    ("invers 2/3/4/5", (2.0, 3.0, 4.0, 5.0)),
)
# Zusaetzlich: andere Steilheiten bei jeweils eigenem Mittel - sie werden
# untereinander und gegen ihr eigenes Flach verglichen (Falle 4).
STEILHEITEN = (
    ("flach   3,0/3,3/3,7/4,0", (4.0, 3.7, 3.3, 3.0)),
    ("mittel  2,0/3,0/4,0/5,0", (5.0, 4.0, 3.0, 2.0)),
    ("steil   1,0/3,0/5,0/7,0", (7.0, 5.0, 3.0, 1.0)),
)


def logwachstum(hebel: np.ndarray, kursprozent: np.ndarray) -> np.ndarray:
    """ln(1 + einsatz * hebel * p) - das GEOMETRISCHE Wachstum je Anker.

    ⚠️ Der Logarithmus ist hier nicht Kosmetik: bei festem Risiko
    entscheidet der geometrische, nicht der arithmetische Ertrag. Ein
    Mittelwert wuerde eine Variante bevorzugen, die selten sehr gross
    gewinnt und oft klein verliert."""
    arg = 1.0 + EINSATZ * hebel * kursprozent
    return np.log(np.maximum(arg, 1e-9))


def main() -> int:
    print("=" * 108)
    print("DIE VIER HEBELSTUFEN - traegt 2x/3x/4x/5x gegen konstanten Hebel?")
    print("=" * 108)
    print("  " + N.standardzeile())
    print("  Geometrie H%d / Stop %.2f ATR / Trailing %.1f / %.1f (2.628)"
          % (HZ, STOP, AUSL, ABST))
    print("  Massstab: ln(1 + %.2f * hebel * kursprozent), Blockbootstrap "
          "Block %d, %d Ziehungen" % (EINSATZ, BLOCK, ZIEHUNGEN))
    print()

    G, W, P, R, A, nsym = lade()
    tag = G // 24
    gut = np.isfinite(W) & np.isfinite(R) & np.isfinite(A) & np.isfinite(P)
    G, W, P, R, A, tag = (x[gut] for x in (G, W, P, R, A, tag))
    print("  %d Anker · %d Tage · %d Symbole"
          % (len(W), len(np.unique(tag)), nsym), flush=True)
    print()

    # ══ 1. DIE SCHWELLE - gerechnet aus der Kurve von 2.630 ══════════
    print("=" * 108)
    print("TEIL 1 - DIE SCHWELLE: wo schneidet kelly(W) die Null?")
    print("  ⭐ Nicht gesetzt - sie faellt aus der stetigen Kurve (2.630).")
    print()
    k = kurve(W, R, A)
    xs = np.array([z["w_mitte"] for z in k])
    ks = np.array([z["kelly"] for z in k])
    schwelle = None
    for i in range(len(xs) - 1):
        if ks[i] > 0 >= ks[i + 1]:
            schwelle = xs[i] + (xs[i + 1] - xs[i]) * \
                ks[i] / max(ks[i] - ks[i + 1], 1e-12)
            break
    if schwelle is None:
        print("  ⛔ kelly(W) schneidet die Null im gemessenen Bereich nicht")
        return 1
    m = W <= schwelle
    print("  Nullstelle von kelly(W):  W = %+.4f" % schwelle)
    print("  Signale darunter:         %d  (%.2f je Tag, %.1f %% der Tage)"
          % (int(m.sum()), m.sum() / len(np.unique(tag)),
             100 * len(np.unique(tag[m])) / len(np.unique(tag))))
    print()

    Ws, Ps, Rs, As, Ts = W[m], P[m], R[m], A[m], tag[m]
    ordnung = np.argsort(Ts, kind="stable")     # zeitlich fuer den Bootstrap
    Ws, Ps, Rs, As, Ts = (x[ordnung] for x in (Ws, Ps, Rs, As, Ts))

    # ══ 2. DIE VIER VIERTEL ══════════════════════════════════════════
    print("=" * 108)
    print("TEIL 2 - DIE VIER VIERTEL (gleich gross, keine gesetzte Grenze)")
    print()
    kanten = np.percentile(Ws, [0, 25, 50, 75, 100])
    viertel = np.clip(np.searchsorted(kanten[1:4], Ws, side="right"), 0, 3)
    print("  %-10s %13s %8s %8s %9s %10s %11s %10s"
          % ("Viertel", "W-Spanne", "n", "q", "CRV", "Kelly",
             "Ertrag %", "RM-11"))
    for v in range(4):
        mv = viertel == v
        q, crv, kel = kelly_von(Rs[mv])
        rm = max_safe_hebel(100 * float(np.median(STOP * As[mv])), MARGE)
        print("  %-10s %13s %8d %7.1f%% %9.3f %+10.4f %+11.4f %9.2fx"
              % ("%d (%s)" % (v + 1, "bestes" if v == 0 else
                              ("schlecht." if v == 3 else "  ")),
                 "%+.2f/%+.2f" % (Ws[mv].min(), Ws[mv].max()),
                 int(mv.sum()), 100 * q, crv, kel,
                 100 * float(Ps[mv].mean()), rm), flush=True)
    print()
    print("  ⚠️ RM-11 erlaubt ueberall mehr als 5x - der Deckel bindet also")
    print("     in KEINEM Viertel. Die Stufung muss sich selbst tragen.")

    # ══ 3. TRAEGT DIE STUFUNG? ═══════════════════════════════════════
    print()
    print("=" * 108)
    print("TEIL 3 - TRAEGT DIE STUFUNG? (gleicher mittlerer Hebel %.2f)"
          % np.mean(VARIANTEN[0][1]))
    print()
    rng = np.random.default_rng(SAAT)
    n = len(Ws)
    starts = np.arange(0, max(1, n - BLOCK))
    nblock = max(1, n // BLOCK)

    def bootstrap(werte: np.ndarray) -> np.ndarray:
        """Blockbootstrap: die Anker sind zeitlich gekoppelt (rho 0,30 in
        2.630), unabhaengige Ziehungen wuerden das Band zu eng machen."""
        aus = np.empty(ZIEHUNGEN)
        for i in range(ZIEHUNGEN):
            s = rng.choice(starts, size=nblock, replace=True)
            idx = (s[:, None] + np.arange(BLOCK)[None, :]).ravel()
            idx = idx[idx < n]
            aus[i] = float(werte[idx].mean())
        return aus

    wachstum = {}
    for lab, stufen in VARIANTEN:
        h = np.array(stufen)[viertel]
        wachstum[lab] = logwachstum(h, Ps)
    # zufaellige Zuordnung als vierte Variante
    hz = rng.choice(np.array([2.0, 3.0, 4.0, 5.0]), size=n)
    wachstum["zufaellig"] = logwachstum(hz, Ps)

    print("  %-18s %13s %26s %11s"
          % ("Variante", "Logwachstum", "Bootstrapband (5./95.)",
             "je 1000 Tr."))
    bands = {}
    for lab in list(wachstum):
        bs = bootstrap(wachstum[lab])
        bands[lab] = bs
        mw = float(wachstum[lab].mean())
        print("  %-18s %+13.6f %12.6f .. %+.6f %+11.4f"
              % (lab, mw, float(np.percentile(bs, 5)),
                 float(np.percentile(bs, 95)), 1000 * mw), flush=True)

    print()
    print("  ⭐ DER VERGLEICH - jede Variante gegen FLACH, gepaart")
    print("     (dieselben Anker, nur andere Zuordnung - das Band ist")
    print("      deshalb viel enger als oben)")
    print()
    print("  %-18s %14s %26s  %s"
          % ("gegen flach", "Unterschied", "Band (5./95.)", "Urteil"))
    basis = wachstum["flach 3,5"]
    for lab in list(wachstum):
        if lab == "flach 3,5":
            continue
        diff = wachstum[lab] - basis
        bs = bootstrap(diff)
        u5, u95 = float(np.percentile(bs, 5)), float(np.percentile(bs, 95))
        mw = float(diff.mean())
        haelt = "✔ besser" if u5 > 0 else ("⛔ schlechter" if u95 < 0
                                           else "- im Band")
        print("  %-18s %+14.6f %12.6f .. %+.6f  %s"
              % (lab, mw, u5, u95, haelt))

    # ══ 4. IST DIE STEILHEIT RICHTIG? ════════════════════════════════
    print()
    print("=" * 108)
    print("TEIL 4 - IST 2-5 DIE RICHTIGE STEILHEIT? (Falle 4)")
    print("  ⚠️ Jede Steilheit hat ein ANDERES Mittel und damit anderes")
    print("     gebundenes Kapital. Verglichen wird deshalb jede gegen IHR")
    print("     EIGENES Flach - nicht untereinander.")
    print()
    print("  %-26s %7s %14s %24s  %s"
          % ("Steilheit", "Mittel", "gegen flach", "Band (5./95.)",
             "Urteil"))
    for lab, stufen in STEILHEITEN:
        h = np.array(stufen)[viertel]
        mitte = float(np.mean(stufen))
        g = logwachstum(h, Ps)
        f = logwachstum(np.full(n, mitte), Ps)
        bs = bootstrap(g - f)
        u5, u95 = float(np.percentile(bs, 5)), float(np.percentile(bs, 95))
        print("  %-26s %7.2f %+14.6f %11.6f .. %+.6f  %s"
              % (lab, mitte, float((g - f).mean()), u5, u95,
                 "✔ besser" if u5 > 0 else ("⛔ schlechter" if u95 < 0
                                            else "- im Band")), flush=True)

    print()
    print("  ⚠️ Gebuehren und Finanzierung sind NICHT eingerechnet (Regel 2).")
    print("  ⚠️ Der Einsatz %.2f je Position ist ein reiner MASSSTAB - er"
          % EINSATZ)
    print("     trifft alle Varianten gleich und faellt im Vergleich heraus.")
    print("  ⚠️ Wie viel Kapital INSGESAMT gebunden wird, ist eine ANDERE")
    print("     Frage (Kelly, Positionszahl, Korrelation - siehe 2.630).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
