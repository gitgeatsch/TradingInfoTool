# -*- coding: utf-8 -*-
"""N9 — WAS KOSTET EINE `vola`-SPERRE AN DURCHLASS? (06.09.2026)

## ⚠️ Die Frage ist umformuliert

N9 stand als *„36 % Sperrmenge bei zwoelf Trichterstufen"*. Nach N8 und N12
ist das nicht mehr die richtige Frage:

    N8   die ODER-Kombination ist im Betrieb nicht abrufbar
         (turnover liegt bei 7 von 57 Werten vor)
    N12  `vola` allein traegt bei jeder Sperrmenge und deckt ALLE Werte ab

**Also: was kostet eine `vola`-Sperre?** Und zwar nicht absolut, sondern
ZUSAETZLICH zu dem, was der Trichter ohnehin aussortiert.

## Warum das der Kern ist

Die 9. Trichterstufe ist `auswahl` — *„gehoert zu den besten k der
Gruppe"*, die 5-%-Auswahl nach 250-Tage-Momentum. Eine `vola`-Sperre kaeme
DANACH. Zwei Faelle:

    UNABHAENGIG   sie sperrt X % der Ausgewaehlten zusaetzlich
                  -> Durchlass faellt von 5 % auf 5 % x (1-X)
    UEBERLAPPEND  sie sperrt, was die Auswahl schon aussortiert hat
                  -> sie kostet Durchlass, ohne etwas beizutragen

⚠️ Das Projekt kennt beide Faelle: *„AUDIT 02.09.: die Sperren sind
KOMPLEMENTAER"* und *„EIN PULL SENKT 113 SIGNALE AUF 2"*.

## Gemessen wird

    A  UEBERSCHNEIDUNG  wie viel der 5-%-Auswahl trifft die vola-Sperre?
                        Gegen den Erwartungswert bei Unabhaengigkeit.
    B  DURCHLASS        was bleibt von 5 % uebrig?
    C  WIRKUNG          traegt die Sperre AUF DER AUSGEWAEHLTEN MENGE?
                        ⚠️ F-212: die Beitraege wirken dort ANDERS als frei.

    python n9_durchlass_vola_sperre.py
"""
from __future__ import annotations

import sys
import time

import numpy as np

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import messe_eigenschaft_beitrag as B                        # noqa: E402
import messe_kandidaten_als_regel as K                       # noqa: E402
import messe_regel_wirksamkeit as W                          # noqa: E402
import messnorm as N                                         # noqa: E402
import messnorm_rand as R                                    # noqa: E402
from messe_beitrag_auf_auswahl import momentum250            # noqa: E402
from messnorm import Lage                                    # noqa: E402

H, MARKE = 5, 2.0
MENGEN = (1.00, 0.20, 0.10, 0.05)      # frei, 20 %, 10 %, 5 % (Produktion)
SPERREN = (0.10, 0.20, 0.30, 0.40)


def main() -> int:
    t0 = time.time()
    print("Lade Reihen ...", flush=True)
    reihen = B.lade()
    vola = K.baue(reihen, "vola", None, horizont=H)
    mom = momentum250(reihen)
    print("  vola %d Tage · Momentum-Rang fuer %d Tage"
          % (len(vola), len(mom)), flush=True)

    # ---------------- A + B  Ueberschneidung und Durchlass ---------------
    print()
    print("=" * 100)
    print("A/B  UEBERSCHNEIDUNG MIT DER AUSWAHL — sperrt `vola` etwas ANDERES?")
    print("=" * 100)
    print("  %-14s %-10s %10s %12s %12s  %s"
          % ("Auswahl", "Sperre", "getroffen", "erwartet", "Durchlass",
             "Deutung"))
    for menge in MENGEN:
        for sperre in SPERREN:
            treffer, n_tage = [], 0
            for tag, z in vola.items():
                mt = mom.get(tag)
                if not mt:
                    continue
                syms = [x["sym"] for x in z]
                da = [s in mt for s in syms]
                if sum(da) < 20:
                    continue
                # die Auswahl: beste k nach Momentum
                idx = [i for i, ok in enumerate(da) if ok]
                mw = np.array([mt[syms[i]] for i in idx], float)
                k = max(1, int(round(len(idx) * menge)))
                gewaehlt = set(np.array(idx)[np.argsort(mw)[-k:]].tolist())
                # die Sperre: oberstes `sperre` der vola je Tag
                kz = np.array([x["kennzahl"] for x in z], float)
                r = W.rang(kz)
                gesperrt = set(np.flatnonzero(r >= 1.0 - sperre).tolist())
                if not gewaehlt:
                    continue
                treffer.append(len(gewaehlt & gesperrt) / len(gewaehlt))
                n_tage += 1
            if n_tage < 100:
                print("  %-14s %-10s   zu wenige Tage (%d)"
                      % ("%.0f %%" % (100 * menge), "%.0f %%" % (100 * sperre),
                         n_tage))
                continue
            t = float(np.mean(treffer))
            rest = 100 * menge * (1 - t)
            ab = t - sperre
            deut = ("unabhaengig" if abs(ab) < 0.03 else
                    "⚠️ trifft MEHR als zufaellig" if ab > 0 else
                    "trifft WENIGER - teils schon aussortiert")
            print("  %-14s %-10s %9.1f%% %11.1f%% %11.2f%%  %s"
                  % ("%.0f %%" % (100 * menge), "%.0f %%" % (100 * sperre),
                     100 * t, 100 * sperre, rest, deut), flush=True)
        print()

    # ---------------- C  traegt sie AUF DER AUSWAHL? ---------------------
    print("=" * 100)
    print("C  TRAEGT DIE SPERRE AUF DER AUSGEWAEHLTEN MENGE?")
    print("=" * 100)
    print("  ⚠️ F-212: die Beitraege wirken auf der SELEKTIERTEN Menge")
    print("     anders als frei - Funding dort dreimal staerker.")
    print()
    L = Lage("spot", "einstieg")
    print("  %-12s %-10s %10s %24s %6s  %s"
          % ("Auswahl", "Sperre", "Wirkung", "Band", "Blk", "Urteil"))
    for menge in (1.00, 0.20):
        for sperre in (0.20, 0.40):
            teil = {}
            for tag, z in vola.items():
                mt = mom.get(tag)
                if not mt:
                    continue
                syms = [x["sym"] for x in z]
                idx = [i for i, s in enumerate(syms) if s in mt]
                if len(idx) < 20:
                    continue
                mw = np.array([mt[syms[i]] for i in idx], float)
                k = max(1, int(round(len(idx) * menge)))
                sel = np.array(idx)[np.argsort(mw)[-k:]]
                if len(sel) < 12:
                    continue
                teil[tag] = [z[i] for i in sel]
            if len(teil) < 200:
                print("  %-12s %-10s   zu wenige Tage (%d)"
                      % ("%.0f %%" % (100 * menge),
                         "%.0f %%" % (100 * sperre), len(teil)))
                continue
            rng = np.random.default_rng(N.SAAT)
            try:
                f = R.pruefe_rand("vola", teil, lage=L,
                                  menge="%.0f%%" % (100 * menge), rng=rng,
                                  marke=MARKE, horizont=H,
                                  staerken=(0.02, 0.05, 0.10, 0.20),
                                  grenze=1.0 - sperre)
            except Exception as e:                           # noqa: BLE001
                print("  %-12s %-10s   %s"
                      % ("%.0f %%" % (100 * menge),
                         "%.0f %%" % (100 * sperre), e))
                continue
            u = ("TRAEGT" if f.traegt else
                 "kein Befund" if f.trennschaerfe_in_r is None else
                 "nicht trennbar" if abs(f.wirkung) >= (f.trennschaerfe or 0)
                 else "traegt nicht")
            print("  %-12s %-10s %+10.5f  [%+.5f .. %+.5f] %6d  %s"
                  % ("%.0f %%" % (100 * menge), "%.0f %%" % (100 * sperre),
                     f.wirkung, f.unten, f.oben, f.n_bloecke, u), flush=True)

    print()
    print("  ⚠️ Traegt sie auf der Auswahl NICHT, kostet sie Durchlass")
    print("     ohne Gegenwert - dann gehoert sie nicht in den Trichter.")
    print()
    print("  Dauer %.1f Minuten" % ((time.time() - t0) / 60.0))
    return 0


if __name__ == "__main__":
    sys.exit(main())
