# -*- coding: utf-8 -*-
"""N-42: die Kalibrierung JE DATENLAGE - der Ersatz fuer F-215 (05.09.2026)

## Warum die alte Messung fiel

F-218: Die Steigung wurde ueber den ROHEN `wert_r` gepoolt ueber alle
Datenlagen gemessen. Die erreichbaren Spannen liegen aber um Faktor 3,4
auseinander:

    nur funding        max +0,039 R
    funding+turnover   max +0,134 R

"Hohes Potential" hiess damit fast zwangslaeufig "hat beide Beitraege" -
eine Aussage ueber das ASSET, nicht den ZEITPUNKT (Regel 3). Nachgewiesen
ueber die Invarianzpruefung: ein additiver Versatz senkte die Steigung von
+0,089 auf +0,052, waehrend sie auf den VOLLSTAENDIGEN Ankern exakt
invariant blieb.

## Die Loesung ist NICHT neu - sie ist schon gebaut

Nutzerentscheidung vom 31.08.: die Schwelle JE DATENLAGE. Sie misst jeden
Anker an SEINER erreichbaren Spanne (`Potential.schwelle`, gerechnet aus
`erreichbar_max / erreichbar_voll`). Nur die MESSUNG hat diese Konstruktion
nie benutzt.

Vorher gefallen und hier nicht zu wiederholen: der Mittelwert statt der
Summe (31.08.) - er benachteiligt die DICHTE Datenlage genauso, wie die
Summe die duenne benachteiligt.

## Drei Formen - die Eigenschaft entscheidet, nicht ich

    ROH      round(wert_r, 3)                  die alte, gefallene Form
    ANTEIL   wert_r / erreichbar_max           wie die Schwelle rechnet
    RANG     Perzentil INNERHALB der Datenlage vergleicht nur Gleiches

RANG ist gegen JEDE monotone Umformung invariant - auch gegen einen
additiven Versatz. Wenn eine Form die Pruefung besteht, dann diese. Ob
ANTEIL sie besteht, ist offen: Zaehler und Nenner wandern gemeinsam, aber
nicht proportional.

## Die Annahmekriterien - VOR dem Lauf festgelegt

    1  INVARIANZ   ein Versatz c auf alle Stufen darf die Steigung nicht
                   aendern
    2  ABDECKUNG   wird ausgewiesen, nicht stillschweigend gepoolt

Eine Form, die 1 nicht besteht, wird NICHT berichtet - egal wie gut ihre
Zahl aussieht.

    python messe_kalibrierung_je_datenlage.py
"""
from __future__ import annotations

import sys
from collections import defaultdict

import numpy as np

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import messe_bewertungskennzahl as MB                       # noqa: E402
import messe_eigenschaft_beitrag as B                       # noqa: E402
import messe_funding_niveau as F                            # noqa: E402
import messe_kandidaten_als_regel as K                      # noqa: E402
import messe_zielregel as ZR                                # noqa: E402
from messe_bewertung_kalibrierung import (                  # noqa: E402
    _fuenftel_je_tag, _steigung, _steigung_wert, _mit_stufen,
    potential_je_anker, VARIANTE, CRV)
from agent import wahrscheinlichkeit as W                   # noqa: E402

SAAT = 20260905


def _anker(zeilen, tage_je_sym, fu5, tu5, nur_tage):
    """(tag, treffer, wert_r, erreichbar_max, datenlage) je entschiedenem Anker.

    `erreichbar_max` kommt aus der ECHTEN `Potential`-Eigenschaft, nicht aus
    einer Nachbildung - dieselbe Groesse, die auch `schwelle` benutzt.
    """
    aus = []
    for z in zeilen:
        tage = tage_je_sym.get(z["sym"])
        if not tage or z["i"] >= len(tage):
            continue
        tag = tage[z["i"]]
        if tag not in nur_tage:
            continue
        w = z.get(VARIANTE)
        if w is None:
            continue
        if abs(w - CRV) < 1e-9:
            treffer = 1
        elif abs(w + 1.0) < 1e-9:
            treffer = 0
        else:
            continue
        p = potential_je_anker(fu5, tu5, tag, z["sym"])
        if p is None:
            continue
        lage = tuple(sorted(str(zz.get("name")) for zz in (p.beitraege or [])
                            if zz.get("zustand") == "traegt"))
        # ⚠️ DIE BEHAUPTETE QUOTE WIRD MITGEFUEHRT (05.09.).
        #
        # Die Erwartung "+0,333" gilt nur, wenn x in R gemessen wird
        # (dq/dwert_r = 1/(1+CRV)). Bei ANTEIL und RANG ist x ein Anteil
        # bzw. ein Perzentil - dieselbe Zahl danebenzustellen waere der
        # Formfehler aus Methodik 2.85, also genau der Fehler, der diese
        # ganze Reihe ausgeloest hat.
        #
        # Einheitenfrei geht es so: dieselbe Regression noch einmal, aber
        # mit der BEHAUPTETEN Quote statt des realisierten Treffers. Das
        # Verhaeltnis beider Steigungen IST der Kalibrierungsfaktor - in
        # jeder Form, ohne Umrechnung.
        aus.append((tag, treffer, float(p.wert_r),
                    float(p.erreichbar_max), lage, float(p.quote)))
    return aus


def gruppen_roh(anker):
    g = defaultdict(lambda: defaultdict(list))
    for tag, tr, wr, _mx, _lg, _q in anker:
        g[round(wr, 3)][tag].append(tr)
    return {k: dict(v) for k, v in g.items()}


def gruppen_anteil(anker):
    g = defaultdict(lambda: defaultdict(list))
    for tag, tr, wr, mx, _lg, _q in anker:
        if mx <= 0:
            continue
        g[round(wr / mx, 2)][tag].append(tr)
    return {k: dict(v) for k, v in g.items()}


def gruppen_rang(anker):
    """Perzentil INNERHALB der eigenen Datenlage - vergleicht nur Gleiches."""
    je_lage = defaultdict(list)
    for i, (_t, _tr, wr, _mx, lg, _q) in enumerate(anker):
        je_lage[lg].append((wr, i))
    rang = [0.0] * len(anker)
    for _lg, paare in je_lage.items():
        paare.sort()
        n = len(paare)
        for pos, (_w, i) in enumerate(paare):
            rang[i] = pos / max(n - 1, 1)
    g = defaultdict(lambda: defaultdict(list))
    for i, (tag, tr, _wr, _mx, _lg, _q) in enumerate(anker):
        g[round(rang[i], 2)][tag].append(tr)
    return {k: dict(v) for k, v in g.items()}


FORMEN = (("ROH   ", gruppen_roh),
          ("ANTEIL", gruppen_anteil),
          ("RANG  ", gruppen_rang))


def main() -> int:
    print("Lade Reihen...", flush=True)
    reihen = B.lade()
    tage_je_sym = {s: [z[0] for z in roh] for s, roh in reihen.items()}
    zeilen = ZR.ergebnisse(reihen)
    quellen = {"funding": F.lade_funding(),
               "turnover": MB.reihe("data/onchain_historie.db", "splycur")}
    f5 = {a: _fuenftel_je_tag(K.baue(reihen, a, quellen[a], horizont=20))
          for a in ("funding", "turnover")}
    alle = sorted(set(f5["funding"]) | set(f5["turnover"]))
    zweite = {t for t in alle if t >= alle[len(alle) // 2]}

    grund_f = next((b.stufen for b in W.BEITRAEGE
                    if b.merkmal == "funding_fuenftel" and b.stufen), [0.0] * 5)
    grund_t = next((b.stufen for b in W.BEITRAEGE
                    if b.merkmal == "turnover_fuenftel" and b.stufen), [0.0] * 5)

    alt = W.BEITRAEGE
    ergebnis = {}
    try:
        for c in (0.0, 2.0):
            W.BEITRAEGE = _mit_stufen([x + c for x in grund_f],
                                      [x + c for x in grund_t])
            anker = _anker(zeilen, tage_je_sym, f5["funding"],
                           f5["turnover"], zweite)
            if c == 0.0:
                lagen = defaultdict(int)
                for _t, _tr, _wr, _mx, lg, _q in anker:
                    lagen[len(lg)] += 1
                ges = sum(lagen.values())
                print()
                print("=" * 92)
                print("ABDECKUNG (Kriterium 2) - %d entschiedene Anker" % ges)
                print("=" * 92)
                for k in sorted(lagen):
                    print("    %d Beitraege  %8d  (%5.1f %%)"
                          % (k, lagen[k], 100 * lagen[k] / max(ges, 1)))
            print()
            print("=" * 92)
            print("VERSATZ c = %+.1f" % c)
            print("=" * 92)
            for name, fn in FORMEN:
                g = fn(anker)
                rng = np.random.default_rng(SAAT)
                print("  %s  %d Gruppen" % (name, len(g)))
                _steigung(g, rng)
                # Die EIGENE Erwartung dieser Form: dieselbe Gruppierung,
                # gefuettert mit der behaupteten Quote statt dem Treffer.
                beh = fn([(t, q, wr, mx, lg, q)
                          for t, _tr, wr, mx, lg, q in anker])
                erw = _steigung_wert(beh)
                ist = _steigung_wert(g)
                if erw and erw == erw and abs(erw) > 1e-9:
                    ergebnis[(name, c, "faktor")] = ist / erw
                    print("           erwartet %+.4f · gemessen %+.4f"
                          "  ->  KALIBRIERUNG %.1f %%"
                          % (erw, ist, 100.0 * ist / erw))
                # ⚠️ `_steigung` DRUCKT nur und gibt None zurueck - der
                # Vergleichswert kommt aus `_steigung_wert`, derselben
                # Rechnung ohne Bericht.
                ergebnis[(name, c)] = _steigung_wert(g)
    finally:
        W.BEITRAEGE = alt

    print()
    print("=" * 92)
    print("KRITERIUM 1 - INVARIANZ")
    print("=" * 92)
    for name, _fn in FORMEN:
        a, b = ergebnis.get((name, 0.0)), ergebnis.get((name, 2.0))
        # ⚠️ DIE TOLERANZ MUSS RELATIV SEIN (05.09., eigener Fehler).
        #
        # Erste Fassung nahm 0,005 ABSOLUT - und ANTEIL bestand damit,
        # obwohl sein Kalibrierungsfaktor von 19,3 % auf 4,6 % fiel. Seine
        # Steigungen sind selbst winzig (0,0032 gegen 0,0017), da ist eine
        # absolute Schranke bedeutungslos. Geprueft wird der FAKTOR, denn
        # der ist die Groesse, die berichtet wird.
        fa = ergebnis.get((name, 0.0, "faktor"))
        fb = ergebnis.get((name, 2.0, "faktor"))
        try:
            d = abs(float(a) - float(b))
            if fa and fb and fa == fa and fb == fb:
                rel = abs(fa - fb) / max(abs(fa), 1e-9)
                urteil = "OK" if rel < 0.10 else "FAELLT DURCH"
                zusatz = " · Faktor %.1f%% gegen %.1f%% (rel. %.0f %%)" % (
                    100 * fa, 100 * fb, 100 * rel)
            else:
                urteil, zusatz = "kein Faktor", ""
            print("  %s  c=0 %+.4f · c=2 %+.4f · Abstand %.4f%s  ->  %s"
                  % (name, float(a), float(b), d, zusatz, urteil))
        except (TypeError, ValueError):
            print("  %s  c=0 %r · c=2 %r   (Rueckgabe nicht numerisch - "
                  "Vergleich an der Ausgabe oben)" % (name, a, b))
    print()
    print("  Eine Form, die hier durchfaellt, wird NICHT berichtet.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
