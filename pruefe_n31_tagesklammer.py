# -*- coding: utf-8 -*-
"""N-31 Gegenpruefung: dieselbe Frage unter der TAGESKLAMMER (04.09.2026)

## Warum diese Datei noetig ist

`messe_beitrag_auf_auswahl.py` rechnet GEPOOLT (2.109), weil bei 5 %
Auswahl je Tag wenige Anker bleiben. Auf der FREIEN Menge liefert es
aber -0,0016 R, waehrend der registrierte Funding-Beitrag +0,0246 R ist.

⚠️ **Ein Verfahren, das den bekannten Wert nicht reproduziert, darf nicht
gedeutet werden** - genau dieser Unterschied hat bei Vorfilter H einen
Befund gekippt (gepoolt +3,57 / je Kalendertag -1,02).

Hier wird deshalb dieselbe Frage unter der TAGESKLAMMER gestellt - der
Statistik, unter der die Beitraege registriert wurden. Bei Funding bleiben
6,4 Anker je Tag auf der 5-%-Stufe, das reicht dafuer.

  A  REPRODUKTION: freie Menge, Tagesklammer  ->  muss +0,0246 R treffen
  B  dieselbe Statistik auf der 5-%-Menge
  C  gepaart A gegen B ueber die gemeinsamen Tage (2.105)

⚠️ `sammle()` wird aus dem echten Werkzeug importiert, nicht nachgebaut.
"""
import sys
import numpy as np

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import messe_bewertungskennzahl as M
import messe_bewertungskennzahl as MB
import messe_eigenschaft_beitrag as B
import messe_funding_niveau as F
import messe_kandidaten_als_regel as K
import messe_regel_wirksamkeit as W
from messe_beitrag_auf_auswahl import momentum250, sammle

HORIZONT, BLOCK = 20, 90


def je_tag_wirkung(gesammelt: dict) -> dict:
    """Die REGISTRIERTE Statistik: Median(frei) - Median(ALLE).

    ⚠️⚠️ NICHT gegen die GESPERRTEN, sondern gegen ALLE - so rechnet
    `messe_regel_wirksamkeit.wirkung()`:

        aus[tag] = float(np.median(y2[frei]) - np.median(y2))

    Mein erster Anlauf verglich frei gegen gesperrt. Das ist rund das
    3,8-fache (Funding +0,0940 statt +0,0246, Turnover +0,2302 statt
    +0,0616 - derselbe Faktor bei beiden, die Signatur eines
    Definitionsunterschieds). Gefunden hat es die Reproduktionskontrolle.
    """
    aus = {}
    for tag, (oben, y) in gesammelt.items():
        if oben.sum() < 1 or (~oben).sum() < 3:
            continue
        aus[tag] = float(np.median(y[~oben]) - np.median(y))
    return aus


def main():
    reihen = B.lade()
    mom = momentum250(reihen)
    rng = np.random.default_rng(20260904)
    menge = MB.reihe("data/onchain_historie.db", "splycur")
    for klar, art, quelle, erwartet in (
            ("FUNDING", "funding", F.lade_funding(), 0.0246),
            ("TURNOVER", "turnover", menge, 0.0616)):
        je_tag = K.baue(reihen, art, quelle, horizont=HORIZONT)
        print()
        print("=" * 92)
        print("%s — TAGESKLAMMER (die registrierte Statistik)" % klar)
        print("=" * 92)
        gv = sammle(je_tag, mom, 1.00)
        g5 = sammle(je_tag, mom, 0.05)
        d_frei = je_tag_wirkung(gv)
        d_5 = je_tag_wirkung(g5)
        print("  A REPRODUKTION — freie Menge (registriert: %+.4f R)" % erwartet)
        a = M.urteil_tage("    frei, je Tag", d_frei, rng, BLOCK)
        if a and abs(a["mittel"] - erwartet) > 0.02:
            print("    ⚠️⚠️ WEICHT UM MEHR ALS 0,02 R AB - Befund unten NICHT")
            print("       verwenden, bevor die Ursache geklaert ist.")
        else:
            print("    ✔ reproduziert - die Statistik ist die registrierte")
        print()
        print("  B dieselbe Statistik auf der 5-%-Menge (die Produktion)")
        M.urteil_tage("    5 %, je Tag", d_5, rng, BLOCK)
        print()
        print("  C GEPAART (2.105) — faellt der Beitrag auf der Auswahl ab?")
        gem = sorted(set(d_frei) & set(d_5))
        if len(gem) < 60:
            print("    zu wenige gemeinsame Tage (%d)" % len(gem))
            continue
        diff = {t: d_5[t] - d_frei[t] for t in gem}
        M.urteil_tage("    5 % minus frei", diff, rng, BLOCK)
        for s in (0.02, 0.05):
            gp = sammle(je_tag, mom, 0.05, pflanze=s)
            dp = je_tag_wirkung(gp)
            g2 = sorted(set(d_frei) & set(dp))
            M.urteil_tage("    Positivkontrolle: Abfall %.2f gepflanzt" % s,
                          {t: dp[t] - d_frei[t] for t in g2}, rng, BLOCK)
    return 0


if __name__ == "__main__":
    sys.exit(main())
