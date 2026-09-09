# -*- coding: utf-8 -*-
"""K-1a Diagnose — wieviel bleibt in `frei`, wenn die A1-Auswahl greift?

## Der Verdacht

K-1a liefert bei `schnitt` auf der schmalsten Menge Werte, die vierzigmal
ueber der ueblichen Skala liegen und mit wachsendem k monoton
zusammenfallen:

    k=2   +0,8697      k=3   +0,4989      k=5   +0,2107

> Das ist die Signatur einer zu kleinen Gruppe, nicht die eines Effekts,
> der sich in der Auswahl konzentriert.

⚠️ Und es gibt einen benannten Grund: **`schnitt` ist mit der A1-Auswahl
kollinear** (Befund 2.242 - seine Zeitinstabilitaet war genau das). Die
A1-Regel waehlt die zwei besten nach 250-Tage-Entwicklung; wer so
gestiegen ist, steht weit ueber seinem eigenen Schnitt. Dann liegen die
Gewaehlten fast alle im GESPERRTEN Fuenftel - und `median(frei)` steht
auf einer Handvoll Werte.

## Was gemessen wird - und warum es kein Bootstrap braucht

Fuer jeden Kandidaten und jedes k nur zwei Zahlen:

    Anteil `oben`     wieviel Prozent der GEWAEHLTEN sperrt die Regel?
    `frei` je Tag     wieviele Anker tragen den Median, der verglichen wird

⚠️ Ohne Auswahl ist der Anteil `oben` per Definition 20 % (`GRENZE
= 0,80`). Weicht er stark ab, misst die Zelle nicht mehr dieselbe Frage:
bei 90 % `oben` vergleicht `median(frei) - median(alle)` eine Handvoll
Ausreisser gegen das Ganze.

    Erwartung   funding, turnover, oi_aenderung nahe 20 % (ihre
                Momentum-Korrelation ist praktisch null, +0,002)
    Verdacht    `schnitt` deutlich darueber - und genau bei kleinem k

    python k1a_diagnose_besetzung.py
"""
from __future__ import annotations

import sys

import numpy as np

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import bestand as BE                                          # noqa: E402
import messe_beitrag_auf_auswahl as A                         # noqa: E402
import messe_eigenschaft_beitrag as B                         # noqa: E402
import messe_kandidaten_als_regel as K                        # noqa: E402
import messe_regel_wirksamkeit as W                           # noqa: E402
from k1a_beitrag_auf_der_a1_menge import (KANDIDATEN, K_WERTE,
                                          a1_menge_je_tag, tagesdaten)
from k1w_beitrag_auf_der_watchlist import watchlist           # noqa: E402
from messe_alle_kandidaten import HORIZONT, zusatzquellen     # noqa: E402


def main() -> int:
    wl = watchlist()
    reihen = B.lade()
    mom = A.momentum250(reihen)
    zus = zusatzquellen()
    mengen = {k: a1_menge_je_tag(mom, wl, k) for k in K_WERTE}

    print("=" * 100)
    print("K-1a DIAGNOSE — wieviel bleibt in `frei`, wenn A1 greift?")
    print("=" * 100)
    print("  ⚠️ Ohne Auswahl sperrt die Regel per Definition 20 %% "
          "(GRENZE = %.2f)." % W.GRENZE)
    print("  ⚠️ Stark darueber heisst: `median(frei)` steht auf wenigen "
          "Werten - dann misst die Zelle")
    print("     eine andere Frage als die registrierte.")
    print()
    kopf = " ".join("%11s" % (k or "alle") for k in K_WERTE)
    print("  ANTEIL DER GEWAEHLTEN, DEN DIE REGEL SPERRT")
    print("     %-14s %s" % ("Kandidat", kopf))

    frei_je_tag = {}
    for kand in KANDIDATEN:
        try:
            _m, fenster = BE.messbasis(kand)
        except KeyError:
            fenster = ""
        je0 = K.baue(reihen, kand, zus.get(kand), horizont=HORIZONT)
        if fenster and fenster != "voll":
            je0 = {t: z for t, z in je0.items() if str(t) >= fenster}
        tage, daten = tagesdaten(je0, mengen)
        zeile = []
        for k in K_WERTE:
            n_oben = n_ges = 0
            n_frei_tage = []
            for t in tage:
                msk = daten[t]["masken"].get(k)
                if msk is None:
                    continue
                o = W.rang(daten[t]["w"]) >= W.GRENZE
                n_ges += int(msk.sum())
                n_oben += int((msk & o).sum())
                n_frei_tage.append(int((msk & ~o).sum()))
            if not n_ges:
                zeile.append("%11s" % "-")
                continue
            zeile.append("%10.1f%%" % (100.0 * n_oben / n_ges))
            frei_je_tag[(kand, k)] = (float(np.mean(n_frei_tage)),
                                      n_ges - n_oben)
        print("     %-14s %s" % (kand, " ".join(zeile)))

    print()
    print("  `frei` JE TAG (und gepoolt) - der Median, der verglichen wird")
    print("     %-14s %s" % ("Kandidat", kopf))
    for kand in KANDIDATEN:
        z = []
        for k in K_WERTE:
            v = frei_je_tag.get((kand, k))
            z.append("%11s" % ("-" if v is None else "%.2f" % v[0]))
        print("     %-14s %s" % (kand, " ".join(z)))
    print()
    print("     %-14s %s" % ("(gepoolt)", kopf))
    for kand in KANDIDATEN:
        z = []
        for k in K_WERTE:
            v = frei_je_tag.get((kand, k))
            z.append("%11s" % ("-" if v is None else "%d" % v[1]))
        print("     %-14s %s" % (kand, " ".join(z)))

    print()
    print("=" * 100)
    print("  ⚠️ Liegt `schnitt` bei kleinem k deutlich ueber 20 %, ist "
          "seine K-1a-Zelle KEIN Befund,")
    print("     sondern die Kollinearitaet aus 2.242 - die A1-Regel und "
          "`schnitt` messen dasselbe:")
    print("     wer 250 Tage gestiegen ist, steht ueber seinem eigenen "
          "Schnitt.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
