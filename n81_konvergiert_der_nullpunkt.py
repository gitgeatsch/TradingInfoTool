# -*- coding: utf-8 -*-
"""N-81 — KONVERGIERT `null_oben` UEBERHAUPT? (08.09.2026)

## Der Anlass — 2.188

`funding` bei 50 % traegt bei 5 Ziehungen (Abstand +0,0002 R), bei 20
nicht mehr, bei 40 gar nicht. Die naheliegende Antwort waere: *"dann
nimm mehr Ziehungen."*

⚠️⚠️ **Diese Antwort koennte falsch sein - und zwar grundsaetzlich.**

    null_oben = float(np.max(nullo))     # messnorm_auswahl.py:313

Ein **Maximum** ueber N Ziehungen ist keine Schaetzung einer festen
Groesse. Es waechst mit N, weil jede weitere Ziehung den bisherigen
Hoechstwert nur uebertreffen oder halten kann. Es hat keinen Grenzwert.

> **Wenn das stimmt, gibt es keinen 'richtigen' Wert fuer `ZIEHUNGEN`.**
> Dann ist jede Wahl willkuerlich, und die Strenge des Urteils haengt an
> einer Zahl, die niemand begruenden kann.

## Was hier gemessen wird — und wogegen

Nicht behaupten, sondern zeigen. Fuer zwei echte Faelle werden `Z_MAX`
Nullziehungen gerechnet und daraus **zwei** Kennzahlen ueber die ersten
n gebildet, fuer wachsendes n:

    max(n)     das heutige Verfahren
    p90(n)     das 90. Perzentil derselben Ziehungen

**Die Vorhersage steht VOR dem Lauf** (Methodik 2.80):

    max(n)   waechst monoton und flacht nur logarithmisch ab
             -> kein Grenzwert, kein begruendbares n
    p90(n)   schwankt zuerst und laeuft dann in ein Band
             -> es GIBT einen Wert, den man schaetzen kann

⚠️ Faellt die Vorhersage durch - flacht `max` sichtbar ab - dann ist
`ZIEHUNGEN` erhoehen tatsaechlich die Loesung, und dieser Befund faellt.
Das ist der Ausgang, der die These widerlegen wuerde.

## ⚠️ Warum zwei Faelle und nicht einer

`schnitt` bei 20 % (Abstand +0,0595, robust) und `funding` bei 50 %
(Abstand +0,0002, kippt). Ein Verfahren, das nur beim knappen Fall
versagt, ist ein anderes Problem als eines, das immer waechst.

    python n81_konvergiert_der_nullpunkt.py
"""
from __future__ import annotations

import sys
import time

import numpy as np

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import messe_eigenschaft_beitrag as B                        # noqa: E402
import messe_funding_niveau as F                             # noqa: E402
import messe_kandidaten_als_regel as K                       # noqa: E402
import messnorm_auswahl as MA                                # noqa: E402
from messe_beitrag_auf_auswahl import momentum250, sammle    # noqa: E402
from messnorm import SAAT, _block                            # noqa: E402
from pruefe_n31_tagesklammer import je_tag_wirkung           # noqa: E402

HORIZONT = 20
Z_MAX = 80
STUFEN = (5, 10, 20, 40, 60, 80)
FAELLE = (("schnitt", "20%"), ("funding", "50%"))


def nullziehungen(je_tag, mom, anteil, rng, block, n):
    """Die oberen Bandgrenzen von n Nullziehungen - wie in der Norm."""
    o = []
    for z in range(n):
        gz = sammle(je_tag, mom, anteil,
                    mische_rang=np.random.default_rng(SAAT + z))
        nb = MA._band(je_tag_wirkung(gz), rng, block)
        if nb:
            o.append(nb["oben"])
        if (z + 1) % 10 == 0:
            print("        %d/%d" % (z + 1, n), flush=True)
    return np.array(o, float)


def main() -> int:
    t0 = time.time()
    print("=" * 96)
    print("N-81 — konvergiert `null_oben`, oder waechst es mit den Ziehungen?")
    print("=" * 96)
    print("  Vorhersage stand VOR dem Lauf: max waechst monoton, p90 laeuft")
    print("  in ein Band. Flacht max ab, ist die These widerlegt.")
    reihen = B.lade()
    mom = momentum250(reihen)
    zus = {"funding": F.lade_funding()}
    block = _block(HORIZONT)

    for kand, menge in FAELLE:
        je = K.baue(reihen, kand, zus.get(kand), horizont=HORIZONT)
        anteil = MA.MENGEN[menge]
        print()
        print("  %s bei %s — %d Nullziehungen" % (kand, menge, Z_MAX))
        rng = np.random.default_rng(20260908)
        o = nullziehungen(je, mom, anteil, rng, block, Z_MAX)
        if len(o) < Z_MAX // 2:
            print("     ⚠️ nur %d Ziehungen lieferten ein Band" % len(o))
            continue
        # Das echte Band des Kandidaten, zum Vergleich.
        rng2 = np.random.default_rng(20260908)
        h = MA._band(je_tag_wirkung(sammle(je, mom, anteil)), rng2, block)
        print("     Band des Kandidaten: unten %+.4f" % h["unten"])
        print("     %6s %12s %12s %14s"
              % ("n", "max(n)", "p90(n)", "Urteil mit max"))
        for n in STUFEN:
            if n > len(o):
                continue
            mx = float(np.max(o[:n]))
            p9 = float(np.percentile(o[:n], 90))
            u = "TRAEGT" if h["unten"] > max(0.0, mx) else "traegt nicht"
            print("     %6d %+12.4f %+12.4f %14s" % (n, mx, p9, u))
        wachstum = float(np.max(o)) - float(np.max(o[:5]))
        print("     -> max waechst von 5 auf %d Ziehungen um %+.4f"
              % (len(o), wachstum))

    print()
    print("  Dauer %.1f Minuten" % ((time.time() - t0) / 60.0))
    return 0


if __name__ == "__main__":
    sys.exit(main())
