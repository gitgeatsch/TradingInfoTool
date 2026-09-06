# -*- coding: utf-8 -*-
"""N1 VORPRUEFUNG - stimmen die Voraussetzungen? (06.09.2026)

Nutzervorgabe: *"pruefe vorher, ob alle Annahmen, Hypothesen und
Grundlagen korrekt sind, damit wir diesen Schritt gehen koennen."*

  V1  ABDECKUNG: auf wie vielen Symbolen und Tagen kann ein
      Schichtentest zwischen vola und turnover ueberhaupt laufen?
  V2  RICHTUNG: ist "hohe Volatilitaet sperren" die richtige Richtung -
      oder traegt die Gegenrichtung?
  V3  KORRELATION: wie stark haengen die Raenge zusammen? Eine hohe
      Korrelation ist noch kein Mitlaeufer-Beweis, eine niedrige noch
      keine Entlastung (H-4c) - aber sie ordnet ein.
"""
from __future__ import annotations
import sys
import numpy as np
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import messe_bewertungskennzahl as MB                        # noqa: E402
import messe_eigenschaft_beitrag as B                        # noqa: E402
import messe_funding_niveau as F                             # noqa: E402
import messe_kandidaten_als_regel as K                       # noqa: E402
import messnorm as N                                         # noqa: E402
import messnorm_rand as R                                    # noqa: E402
from messnorm import Lage                                    # noqa: E402


def main() -> int:
    reihen = B.lade()
    fu = F.lade_funding()
    tu = MB.reihe("data/onchain_historie.db", "splycur")
    welten = {"vola": K.baue(reihen, "vola", None, horizont=5),
              "funding": K.baue(reihen, "funding", fu, horizont=5),
              "turnover": K.baue(reihen, "turnover", tu, horizont=5)}

    print("=" * 88)
    print("V1  ABDECKUNG - worauf kann ein Schichtentest ueberhaupt laufen?")
    print("=" * 88)
    syms = {k: {x["sym"] for z in v.values() for x in z}
            for k, v in welten.items()}
    for k, v in welten.items():
        print("  %-10s %6d Tage · %4d Symbole" % (k, len(v), len(syms[k])))
    print()
    for a, b in (("vola", "funding"), ("vola", "turnover")):
        gem_t = set(welten[a]) & set(welten[b])
        gem_s = syms[a] & syms[b]
        # je Tag: wie viele Werte haben BEIDE Kennzahlen?
        n_tag = []
        for t in gem_t:
            sa = {x["sym"] for x in welten[a][t]}
            sb = {x["sym"] for x in welten[b][t]}
            n_tag.append(len(sa & sb))
        n_tag = np.array(n_tag) if n_tag else np.array([0])
        # Ein Schichtentest braucht 5 Faecher mit je >= 3 Behaltenen
        brauchbar = int((n_tag >= 20).sum())
        print("  %s ∩ %s" % (a.upper(), b.upper()))
        print("    gemeinsame Tage    %5d      gemeinsame Symbole %4d"
              % (len(gem_t), len(gem_s)))
        print("    Werte je Tag       Median %.0f · p10 %.0f · p90 %.0f"
              % (np.median(n_tag), np.percentile(n_tag, 10),
                 np.percentile(n_tag, 90)))
        print("    Tage mit >= 20 Werten (5 Faecher je >= 3 Werte): %d"
              % brauchbar)
        print("    -> Bloecke bei Block 15: %d   %s"
              % (brauchbar // 15,
                 "✔ messbar" if brauchbar // 15 >= 20 else "⚠️ ZU WENIG"))
        print()

    print("=" * 88)
    print("V2  RICHTUNG - traegt `vola` oben oder unten? (Rand > +2 R, H5 voll)")
    print("=" * 88)
    L = Lage("spot", "einstieg")
    for lab, oben in (("oberstes Fuenftel sperren (bisher)", True),
                      ("UNTERSTES Fuenftel sperren (Gegenrichtung)", False)):
        rng = np.random.default_rng(N.SAAT)
        f = R.pruefe_rand("vola", welten["vola"], lage=L, menge="frei",
                          rng=rng, marke=2.0, horizont=5,
                          staerken=(0.02, 0.05, 0.10, 0.20),
                          oben_sperren=oben)
        print("  %-44s %+8.5f [%+.5f .. %+.5f]  %s"
              % (lab, f.wirkung, f.unten, f.oben, f.urteil[:38]))
    print()
    print("  ⚠️ Traegt BEIDES, misst die Regel nicht die Richtung, sondern")
    print("     die Streuung selbst - dann waere `vola` kein Rangbeitrag.")

    print()
    print("=" * 88)
    print("V3  RANGKORRELATION je Kalendertag (Median ueber die Tage)")
    print("=" * 88)
    for a, b in (("vola", "funding"), ("vola", "turnover"),
                 ("funding", "turnover")):
        rs = []
        for t in set(welten[a]) & set(welten[b]):
            da = {x["sym"]: x["kennzahl"] for x in welten[a][t]}
            db = {x["sym"]: x["kennzahl"] for x in welten[b][t]}
            g = sorted(set(da) & set(db))
            if len(g) < 15:
                continue
            xa = K.W.rang(np.array([da[s] for s in g], float))
            xb = K.W.rang(np.array([db[s] for s in g], float))
            if xa.std() > 1e-12 and xb.std() > 1e-12:
                rs.append(float(np.corrcoef(xa, xb)[0, 1]))
        if rs:
            print("  %-10s / %-10s  Median %+.3f  (p10 %+.3f · p90 %+.3f) "
                  "· %d Tage"
                  % (a, b, np.median(rs), np.percentile(rs, 10),
                     np.percentile(rs, 90), len(rs)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
