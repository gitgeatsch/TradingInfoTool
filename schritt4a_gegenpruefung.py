# -*- coding: utf-8 -*-
"""SCHRITT 4a - DIE GEGENPRUEFUNG (06.09.2026)

Schritt 4a hat drei Behauptungen erzeugt. Zwei davon stehen unter einem
Vorbehalt, den erst das Lesen des eigenen Codes sichtbar gemacht hat.

  G1  IST DER BLOCK LANG GENUG?
      `messnorm.pruefe()` SETZT den Block (3 x Horizont, mindestens 15) und
      ruft `messnorm.pruefe_block()` NIE auf. Die Norm hat die Pruefung und
      benutzt sie im Messpfad nicht.
      ⚠️ Ein zu kurzer Block macht das Band zu ENG - dann sind "TRAEGT"-
      Urteile Scheinbefunde. Betrifft JEDES heutige H5-Ergebnis, auch
      `vola`.
      Der alte Horizontlauf (31.08.) rechnete mit Block 90 statt 15.

  G2  IST "FAELLT AN DER EPOCHE" ECHT - oder nur weniger Daten?
      funding und turnover tragen ueber die volle Historie (2.386 bzw.
      2.741 Tage) und fallen ab 2024 (959 Tage). Ein kuerzerer Abschnitt
      hat aber ein BREITERES Band. Deshalb: gleich lange Fenster AUS DER
      FRUEHEREN Historie. Fallen sie dort auch, ist es Datenmangel und
      keine Epoche.

    python schritt4a_gegenpruefung.py
"""
from __future__ import annotations

import sys
import time

import numpy as np

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import messe_bewertungskennzahl as MB                        # noqa: E402
import messe_eigenschaft_beitrag as B                        # noqa: E402
import messe_funding_niveau as F                             # noqa: E402
import messe_kandidaten_als_regel as K                       # noqa: E402
import messe_regel_wirksamkeit as W                          # noqa: E402
import messnorm as N                                         # noqa: E402
import messnorm_rand as R                                    # noqa: E402
from messnorm import Lage                                    # noqa: E402

STAERKEN = (0.02, 0.05, 0.10, 0.20)
FENSTER = 959                    # so lang wie "ab 2024"


def main() -> int:
    t0 = time.time()
    L = Lage("spot", "einstieg")
    print("Lade Reihen ...", flush=True)
    reihen = B.lade()
    fu = F.lade_funding()
    tu = MB.reihe("data/onchain_historie.db", "splycur")
    try:
        tm = K.lade_terminmarkt()
    except Exception:                                        # noqa: BLE001
        tm = {}
    arten = [("schnitt50", None), ("vola", None), ("amihud", None),
             ("funding", fu), ("turnover", tu)]
    if "oi_aenderung" in tm:
        arten.append(("oi_aenderung", tm["oi_aenderung"]))

    # ---------------- G1  IST DER BLOCK LANG GENUG? ----------------------
    print()
    print("=" * 100)
    print("G1  IST DER BLOCK LANG GENUG?   Autokorrelation der Tageswirkung")
    print("=" * 100)
    print("  Grenze 0,15 - darueber ist der Block zu kurz und das Band zu eng.")
    print()
    print("  %-14s %-16s %8s %10s %9s  %s"
          % ("Kandidat", "Lauf", "Block", "AK@Block", "Tage", "Urteil"))
    for art, quelle in arten:
        for lab, hor, ab in (("A H20 voll", 20, None), ("B H5 voll", 5, None),
                             ("C H5 2024", 5, "2024-01-01")):
            g = K.baue(reihen, art, quelle, horizont=hor)
            if ab:
                g = {t: z for t, z in g.items() if t >= ab}
            if len(g) < 100:
                continue
            d, _a, _b, _c = W.wirkung(g, True)
            blk = N._block(hor)
            p = N.pruefe_block(d, blk)
            print("  %-14s %-16s %8d %10.4f %9d  %s"
                  % (art, lab, blk, p.get("ak", float("nan")), len(d),
                     "✔ lang genug" if p.get("ok") else "⚠️ ZU KURZ"))
        print()

    # ---------------- G2  EPOCHE ODER DATENMANGEL? -----------------------
    print("=" * 100)
    print("G2  EPOCHE ODER DATENMANGEL?   gleich lange Fenster (%d Tage)"
          % FENSTER)
    print("=" * 100)
    for art, quelle in (("funding", fu), ("turnover", tu)):
        g = K.baue(reihen, art, quelle, horizont=5)
        tage = sorted(g)
        print("  %s   %d Tage insgesamt (%s .. %s)"
              % (art.upper(), len(tage), tage[0], tage[-1]))
        print("    %-24s %6s  %-40s  %s"
              % ("Fenster", "Tage", "MITTEL", "RAND > +2 R"))
        # nicht ueberlappende Fenster von hinten nach vorn
        grenzen = []
        i = len(tage)
        while i - FENSTER >= 0:
            grenzen.append((tage[i - FENSTER], tage[i - 1]))
            i -= FENSTER
        for a, b in reversed(grenzen):
            teil = {t: z for t, z in g.items() if a <= t <= b}
            zeile = {}
            for mass in ("mittel", "rand2"):
                rng = np.random.default_rng(N.SAAT)
                try:
                    if mass == "mittel":
                        f = N.pruefe(art, teil, lage=L,
                                     zielgroesse="bewegung_r", menge="frei",
                                     rng=rng, horizont=5, staerken=STAERKEN)
                    else:
                        f = R.pruefe_rand(art, teil, lage=L, menge="frei",
                                          rng=rng, marke=2.0, horizont=5,
                                          staerken=STAERKEN)
                except Exception as e:                       # noqa: BLE001
                    zeile[mass] = None
                    print("      %s: %s" % (mass, e))
                    continue
                zeile[mass] = f

            def kurz(f):
                if f is None:
                    return "-"
                k = ("TRAEGT" if f.traegt else
                     "kein Befund" if f.trennschaerfe_in_r is None else
                     "nicht trennbar" if abs(f.wirkung) >= f.trennschaerfe
                     else "traegt nicht")
                return "%+.5f [%+.5f..%+.5f] %s" % (f.wirkung, f.unten,
                                                    f.oben, k)
            print("    %-24s %6d  %-40s  %s"
                  % ("%s..%s" % (a[:7], b[:7]), len(teil),
                     kurz(zeile.get("mittel")), kurz(zeile.get("rand2"))),
                  flush=True)
        print()
    print("  ⚠️ Traegt der Wert in FRUEHEREN gleich langen Fenstern und nur")
    print("     im letzten nicht, ist es die EPOCHE. Faellt er in allen,")
    print("     ist es die Datenmenge - und 'faellt an der Epoche' waere")
    print("     eine Fehldeutung gewesen.")
    print()
    print("  Dauer %.1f Minuten" % ((time.time() - t0) / 60.0))
    return 0


if __name__ == "__main__":
    sys.exit(main())
