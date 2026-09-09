# -*- coding: utf-8 -*-
"""N-97 — d01 auf der WATCHLIST: der Menge, auf der die Kette wirklich laeuft

## ⚠️⚠️⚠️ Warum diese Messung die vorige ueberholt

N-96 hat d01 auf `frei`, 5 %, 10 % und 20 % gemessen, weil
`agent/wahrscheinlichkeit.py` es verlangt:

> **WER DIESE TABELLE AENDERN WILL, MUSS AUF DER SELEKTIERTEN MENGE
> MESSEN.**

⚠️⚠️ EINE EIGENE FEHLAUSSAGE, HIER KORRIGIERT: der erste Entwurf
dieses Kopfes behauptete, die Kette waehle gar nicht nach Momentum.
**Das ist falsch.** `agent/auswahl.py` waehlt mit `RUECKBLICK_TAGE = 250`
die besten **k=2** aus der Watchlist. Der Betriebsablauf ist zweistufig:

    agent/marktrang.raenge   Rang ueber die MESSBASIS (536), fuer unsere
                             Symbole nur ABGELESEN  -> das ist `frei`
    agent/auswahl.waehle     2 von 43 nach 250-Tage-Entwicklung -> 4,7 %

> **F-212s "oberste 5 % nach 250-Tage-Momentum" ist damit kein
> Messkonstrukt, sondern eine Nachbildung der Live-Auswahl** - nur auf
> der Messbasis statt auf der Watchlist.

⚠️⚠️⚠️ Und daraus folgt die eigentliche Frage dieses Laufs: die Menge,
auf der die Live-ENTSCHEIDUNG faellt, sind **zwei Werte pro Tag**. Ob
sich auf ihr eine fuenfstufige Tabelle ueberhaupt beurteilen laesst, ist
keine Frage der Sorgfalt, sondern der Datenlage. Dieser Lauf misst die
naechstgroessere Menge - die ganze Watchlist - als Obergrenze dessen,
was dort ueberhaupt aufloesbar ist.

## Der Aufbau - genau wie K-1w (Befund 2.229)

    Rang       ueber die MESSBASIS (536), wie `marktrang` in Produktion
    Gemessen   nur auf den Watchlist-Zeilen - Verengung NACH dem Rang

⚠️ Die Reihenfolge ist nicht beliebig: ueber die Watchlist zu rangen
dreht bei `funding` das Vorzeichen (2.229, +3,43 gegen -3,10).

    d01 = median(y[Fuenftel 1 & Watchlist]) - median(y[Fuenftel 0 & Watchlist])
    d34 = dasselbe fuer Fuenftel 3 gegen 4 - der unstrittige Schritt

## Die Vorhersage, VOR dem Lauf (Methodik 2.80)

    d01 trennbar positiv   -> der Knick ist im BETRIEB real. Die
                              Live-Stufen bleiben, Zusammenlegen faellt
    d01 nicht trennbar,
    aber d34 trennbar      -> der Knick ist im Betrieb Rauschen;
                              Zusammenlegen waere gedeckt
    beide nicht trennbar   -> untermaechtig. Bei 43 Werten je Tag hat ein
                              Fuenftel ~8 Zeilen - das kann zu duenn sein

⚠️ Die Besetzung wird mitgedruckt. Faellt sie unter 3, ist der Median
nicht belastbar und das Urteil lautet KEIN BEFUND, nicht "traegt nicht".

    python n97_d01_auf_der_watchlist.py
"""
from __future__ import annotations

import sys
import time

import numpy as np

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import messe_eigenschaft_beitrag as B                        # noqa: E402
import messe_kandidaten_als_regel as K                       # noqa: E402
import messmenge                                              # noqa: E402
from k1w_beitrag_auf_der_watchlist import watchlist          # noqa: E402
from messe_alle_kandidaten import HORIZONT, zusatzquellen    # noqa: E402
from messnorm import _block                                   # noqa: E402
from n91_rangkorrelation_form import band                     # noqa: E402

NULL_ZIEH = 40
SAAT = 20260909
MINDEST = 2


def paar_je_tag(je_tag, wl, a, b, mische=None):
    """d(a,b) je Tag: Rang ueber die Messbasis, gemessen auf `wl`."""
    aus, bes = {}, {a: [], b: []}
    for tag, zeilen in je_tag.items():
        if len(zeilen) < 15:
            continue
        w = np.array([x["kennzahl"] for x in zeilen], float)
        y = np.array([x["in_r"] for x in zeilen], float)
        # ⚠️ Der Rang ueber ALLE - erst danach verengen. Andersherum
        # dreht `funding` das Vorzeichen (2.229).
        r = np.argsort(np.argsort(w)) / max(len(w) - 1, 1)
        if mische is not None:
            r = mische.permutation(r)
        auf = (np.array([x["sym"].upper() in wl for x in zeilen])
               if wl is not None else np.ones(len(zeilen), bool))

        def f(k):
            m = (r >= k / 5) & ((r < (k + 1) / 5) if k < 4 else (r <= 1.0))
            m = m & auf
            bes[k].append(int(m.sum()))
            return float(np.median(y[m])) if m.sum() >= MINDEST else None
        va, vb = f(a), f(b)
        if va is not None and vb is not None:
            aus[tag] = va - vb
    return aus, {k: (float(np.mean(v)) if v else 0.0) for k, v in bes.items()}


def nullpunkt(je_tag, wl, a, b, block):
    w = []
    for z in range(NULL_ZIEH):
        r, _ = paar_je_tag(je_tag, wl, a, b,
                           np.random.default_rng(SAAT + z))
        bb = band(r, block, zieh=300, saat=SAAT + z)
        if bb:
            w.append(bb[0])
    return float(np.mean(w)) if w else float("nan")


def main() -> int:
    t0 = time.time()
    wl = watchlist()
    reihen = B.lade()
    zus = zusatzquellen()
    block = _block(HORIZONT)

    print("=" * 104)
    print("N-97 — d01 auf der WATCHLIST: der Menge, auf der die Kette laeuft")
    print("=" * 104)
    print("  %s" % messmenge.zeile())
    print("  Watchlist %d Symbole · Rang ueber die Messbasis · Verengung "
          "NACH dem Rang (2.229)" % len(wl))
    print("  ⚠️ Der Betrieb waehlt ZWEISTUFIG: Rang ueber die Messbasis "
          "(marktrang), dann k=2")
    print("     aus der Watchlist nach 250-Tage-Entwicklung (auswahl.py) "
          "- rund 4,7 %.")
    print("  ⚠️ Besetzung unter %d -> KEIN BEFUND, nicht 'traegt nicht'."
          % 3)

    for kand in ("funding", "zufall"):
        je = K.baue(reihen, kand, zus.get(kand), horizont=HORIZONT)
        print()
        print("  %s" % kand.upper())
        print("     %-10s %-5s %10s %22s %10s %11s  %s"
              % ("Menge", "Paar", "Wert", "Band", "Nullpunkt", "Besetzung",
                 "Urteil"))
        for name, w in (("Watchlist", wl), ("Messbasis", None)):
            for paar, (a, b) in (("d01", (1, 0)), ("d34", (3, 4))):
                reihe, bes = paar_je_tag(je, w, a, b)
                if not reihe:
                    print("     %-10s %-5s nicht messbar" % (name, paar))
                    continue
                bb = band(reihe, block)
                if bb is None:
                    print("     %-10s %-5s zu wenige Bloecke (%d Tage)"
                          % (name, paar, len(reihe)))
                    continue
                n0 = nullpunkt(je, w, a, b, block)
                duenn = min(bes[a], bes[b]) < 3
                traegt = bb[1] > max(0.0, n0) or bb[2] < min(0.0, n0)
                urteil = ("⚠️ KEIN BEFUND (zu duenn)" if duenn else
                          ("⚠️ TRENNBAR" if traegt else "nicht trennbar"))
                print("     %-10s %-5s %+10.4f [%+.4f .. %+.4f] %+10.4f "
                      "%5.1f/%-5.1f  %s"
                      % (name, paar, bb[0], bb[1], bb[2], n0,
                         bes[a], bes[b], urteil), flush=True)
            print()

    print("=" * 104)
    print("WAS DAS HEISST")
    print("=" * 104)
    print("  ⚠️ Die Watchlist-Zeile ist die entscheidende - dort faellt "
          "die Live-Entscheidung.")
    print("  ⚠️ `d34` sagt, ob der Aufbau dort ueberhaupt traegt. Ist er "
          "es nicht, ist auch")
    print("     ein Nullbefund bei `d01` keine Aussage.")
    print("  ⚠️⚠️ Und die Kontrolle `zufall` muss ueberall nicht trennbar "
          "sein.")
    print("  Dauer %.1f Minuten" % ((time.time() - t0) / 60.0))
    return 0


if __name__ == "__main__":
    sys.exit(main())
