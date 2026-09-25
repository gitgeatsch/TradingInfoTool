# -*- coding: utf-8 -*-
"""Ist die ORDNUNG der funding-Fuenftel horizontstabil? (25.09.2026)

Nutzerhypothese: *„Die Bewertung sollte auch die Horizontachse bei der
Hebelentstehung beruecksichtigen (bei Einstieg musst du das als Experte
bewerten ob das erforderlich ist)?"*

═══════════════════════════════════════════════════════════════════════
 DIE FRAGE - und warum sie ueber den EINSTIEG entscheidet
═══════════════════════════════════════════════════════════════════════

Gemessen (A1, 24.09.): `q` haengt massiv vom Horizont ab - 0,136 bei 6 h
gegen 0,335 bei H20. Der Hebel kommt ueber Kelly aus `q`, also haengt die
HOEHE des Hebels am Horizont. Das ist unstrittig.

⚠️⚠️ OFFEN IST ETWAS ANDERES: haengt auch die ORDNUNG daran?

    HOEHE     wieviel `q` betraegt          -> horizontabhaengig (belegt)
    ORDNUNG   welches Fuenftel BESSER ist   -> ???

➤ IST DIE ORDNUNG STABIL, betrifft der Horizont nur die HEBELHOEHE, und
  der EINSTIEG braucht ihn nicht - er fragt nur "ist dieses Asset heute
  besser als jenes".

➤ IST SIE NICHT STABIL, dann ist ein Asset auf 6 h gut und auf 72 h
  schlecht. Dann braucht AUCH der Einstieg die Horizontachse, und die
  N19-E-Stufen gelten nur fuer H3.

═══════════════════════════════════════════════════════════════════════
 ⚠️⚠️ DIE FINANZIERUNG BLEIBT DRAUSSEN - Regel 2
═══════════════════════════════════════════════════════════════════════

Nutzerhinweis 25.09.: *„ACHTUNG: Finanzierungsfrage ist bei der Bewertung
NICHT relevant"* - und das korrigiert einen Fehler von mir: ich hatte
vorgeschlagen, den optimalen Horizont ueber `q(H) minus Finanzierung(H)`
zu bestimmen. Das zieht die Kosten in die Bewertung, genau was Regel 2
verbietet. Die 0,18 %/Tag gehoeren in die MAIL, nicht in die Ausloesung.

═══════════════════════════════════════════════════════════════════════
 DER AUFBAU
═══════════════════════════════════════════════════════════════════════

    Kandidat     funding - der einzige mit einer Stufenleiter (N19-E)
    Menge        frei - dort war sie monoton
    Horizonte    1, 2, 3, 5, 10, 20 Tage
    Zielgroesse  barriere
    Pruefgroesse Spearman zwischen den Stufenvektoren, PAARWEISE
    Nullpunkt    dieselbe Rechnung mit gemischter Zuordnung

⚠️ Der Horizont weicht bewusst von `HORIZONT_JE_LAGE` (= 3) ab - die
Achse IST die Frage. `messnorm.warne_horizont` wird gerufen, damit die
Abweichung im Protokoll steht statt still zu bleiben.

    python n19e_horizontstabilitaet.py
    python n19e_horizontstabilitaet.py --symbole 80
"""
from __future__ import annotations

import sys
from itertools import combinations

import numpy as np

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import messe_beitrag_auf_auswahl as MB                       # noqa: E402
import messe_eigenschaft_beitrag as B                        # noqa: E402
import messe_funding_niveau as F                             # noqa: E402
import messe_kandidaten_als_regel as K                       # noqa: E402
import messnorm as N                                         # noqa: E402
import messnorm_auswahl as MA                                # noqa: E402
import n19e_hebelstufen as S                                 # noqa: E402

HORIZONTE = (1, 2, 3, 5, 10, 20)
KANDIDAT = "funding"
MENGE = "frei"
CRV = S.CRV


def _stufen(je_tag, mom, anteil, rng=None):
    """q je Fuenftel - dieselbe Rechnung wie N19-E, kein Nachbau."""
    if rng is None:
        q, _p, n = S._quote_je_fuenftel(je_tag, mom, anteil)
        return q, n
    # gemischte Zuordnung fuer den Nullpunkt
    sammel = {k: [] for k in range(5)}
    for tag, z in je_tag.items():
        if len(z) < S.MIND_JE_TAG:
            continue
        m = MB._auswahl_maske(z, mom.get(tag) or {}, anteil, None)
        if m is None or m.sum() < 8:
            continue
        g = [x for x, keep in zip(z, m) if keep]
        y = np.array([x["in_r"] for x in g], float)
        r = rng.permutation(len(g)) / max(len(g) - 1, 1)
        for k in range(5):
            sel = (r >= k / 5) & (r < (k + 1) / 5 if k < 4 else r <= 1.0)
            if sel.sum() >= 2:
                sammel[k].append(float(np.mean(y[sel])))
    if any(len(sammel[k]) < 30 for k in range(5)):
        return None, 0
    return [(float(np.mean(sammel[k])) + 1.0) / (1.0 + CRV)
            for k in range(5)], 1


def _spearman(a, b):
    ra = np.argsort(np.argsort(a))
    rb = np.argsort(np.argsort(b))
    return float(np.corrcoef(ra, rb)[0, 1])


def main() -> int:
    grenze = None
    if "--symbole" in sys.argv:
        grenze = int(sys.argv[sys.argv.index("--symbole") + 1])
    rng = np.random.default_rng(20260925)

    print("=" * 96)
    print("IST DIE ORDNUNG DER `funding`-FUENFTEL HORIZONTSTABIL?")
    print("=" * 96)
    print("  Kandidat %s · Menge %s · Zielgroesse barriere · CRV %.1f"
          % (KANDIDAT, MENGE, CRV))
    print("  ⚠️ Horizonte %s - die Achse IST die Frage, `HORIZONT_JE_LAGE`"
          % (HORIZONTE,))
    print("     steht auf %d und wird hier bewusst variiert."
          % N.HORIZONT_JE_LAGE[("hebel", "einstieg")])
    print("  ⚠️⚠️ Die FINANZIERUNG bleibt draussen (Regel 2).")

    reihen = B.lade()
    if grenze:
        reihen = {k: reihen[k] for k in list(reihen)[:grenze]}
    mom = MB.momentum250(reihen)
    fund = F.lade_funding()
    anteil = MA.MENGEN[MENGE]

    # ⚠️⚠️ DIE WELTEN WERDEN EINMAL GEBAUT, NICHT JE NULLWELT NEU.
    # Meine erste Fassung rief `K.baue` in jeder der 40 Nullwelten fuer
    # jeden der sechs Horizonte - 240 Neuaufbauten statt 6. Das waere
    # Stunden gelaufen, ohne ein anderes Ergebnis zu liefern.
    welten = {}
    tab = {}
    print()
    print("  %-6s %9s %9s %9s %9s %9s  %8s %s"
          % ("H", "q0", "q1", "q2", "q3", "q4", "Spanne", "monoton"))
    for h in HORIZONTE:
        je = K.baue(reihen, KANDIDAT, fund, horizont=h)
        if not je:
            print("  %-6d leere Welt" % h)
            continue
        welten[h] = je
        q, n = _stufen(je, mom, anteil)
        if q is None:
            print("  %-6d zu duenn" % h)
            continue
        tab[h] = q
        auf = all(q[i] <= q[i + 1] for i in range(4))
        ab = all(q[i] >= q[i + 1] for i in range(4))
        print("  %-6d %s  %8.4f %s"
              % (h, " ".join("%9.4f" % x for x in q), abs(q[0] - q[4]),
                 "fallend ✔" if ab else "steigend ✔" if auf
                 else "⚠️ nicht monoton"), flush=True)

    if len(tab) < 3:
        print("\n  ⛔ zu wenige Horizonte auswertbar")
        return 1

    # ── DIE PRUEFGROESSE: die Ordnung, paarweise ───────────────────────
    print()
    print("─" * 96)
    print("DIE ORDNUNG - Spearman zwischen den Stufenvektoren")
    print("─" * 96)
    hs = sorted(tab)
    werte = []
    for a, b in combinations(hs, 2):
        r = _spearman(tab[a], tab[b])
        werte.append(r)
        print("  H%-3d gegen H%-3d   %+.3f" % (a, b, r))
    mittel = float(np.mean(werte))
    print()
    print("  Mittel ueber %d Paare: %+.3f" % (len(werte), mittel))

    # ── DER NULLPUNKT: wie ordnen sich ZUFAELLIGE Stufen? ──────────────
    print()
    print("─" * 96)
    print("DER NULLPUNKT - dieselbe Rechnung mit GEMISCHTER Zuordnung")
    print("─" * 96)
    print("  ⚠️ Fuenf Werte ordnen sich auch zufaellig manchmal gleich -")
    print("     ohne diesen Bezug ist ein hoher Spearman keine Aussage.",
          flush=True)
    null = []
    for _ in range(N.NULL_ZIEHUNGEN):
        ntab = {}
        for h in hs:
            q, _n = _stufen(welten[h], mom, anteil, rng)
            if q:
                ntab[h] = q
        if len(ntab) >= 3:
            nw = [_spearman(ntab[a], ntab[b])
                  for a, b in combinations(sorted(ntab), 2)]
            null.append(float(np.mean(nw)))
    if len(null) < 10:
        print("  ⛔ zu wenige Nullwelten (%d)" % len(null))
        return 1
    p90 = float(np.percentile(null, N.NULL_PERZENTIL))
    print("  Nullwelten: Mittel %+.3f · %.0f. Perzentil %+.3f (%d Welten)"
          % (float(np.mean(null)), N.NULL_PERZENTIL, p90, len(null)))
    print()
    print("  ➤ gemessen %+.3f gegen Nullpunkt %+.3f" % (mittel, p90))
    if mittel > p90:
        print("  ✔ DIE ORDNUNG IST HORIZONTSTABIL")
        print("    ➤ Der EINSTIEG braucht die Horizontachse NICHT -")
        print("      sie betrifft nur die HEBELHOEHE.")
    else:
        print("  ⛔ DIE ORDNUNG IST NICHT STABIL")
        print("    ➤ Ein Asset ist auf kurzen und langen Horizonten")
        print("      verschieden gut. Dann braucht AUCH der Einstieg die")
        print("      Achse, und die N19-E-Stufen gelten nur fuer H3.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
