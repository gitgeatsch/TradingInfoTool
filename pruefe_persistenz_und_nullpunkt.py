# -*- coding: utf-8 -*-
"""N-48: Ist `zufall` ein gueltiger Nullpunkt fuer PERSISTENTE Groessen? (05.09.2026)

## Der Verdacht

`zufall` zieht fuer jedes Symbol an JEDEM Tag neu. `amihud` ist dagegen
**persistent** - ein illiquider Coin bleibt es monatelang.

Die Barrieren-Ausgaenge ueberlappen: dasselbe Symbol an aufeinanderfolgenden
Tagen teilt weitgehend dieselbe Zukunft. Bei einer taeglich neu gezogenen
Groesse mittelt sich das weg; bei einer persistenten **stapelt es sich** -
die effektive Zahl unabhaengiger Beobachtungen ist dann um Groessenordnungen
kleiner als die rohe Ankerzahl.

⚠️ **Dann waere `zufall` kein gueltiger Nullpunkt fuer genau die Groessen,
um die es geht** - derselbe Fehlertyp wie bei der Laengs-Form (F-222/F-223),
wo die Tagesmischung die marktweite Gemeinsamkeit stehen liess.

⚠️ **Und ein zweiter Effekt kommt dazu:** die Tagesklammer entfernt den
TAGES-Effekt, nicht den SYMBOL-Effekt. Ein Symbol mit dauerhaft hoeherer
Trefferquote zieht sein Fuenftel konstant mit. Bei einer persistenten
Groesse ist das eine ASSET-Aussage - Regel 3.

## Drei Messungen

    1  PERSISTENZ   Wie oft behaelt ein Symbol sein Fuenftel von einem Tag
                    zum naechsten? Zufall waere 20 %.

    2  PERSISTENTER NULLPUNKT
                    Jedes Symbol bekommt EINEN festen Zufallswert; daraus
                    werden die Tagesfuenftel gebildet. Diese Groesse ist
                    maximal persistent und traegt NULL Information.
                    ⚠️ Ihre gemessene Spanne IST der ehrliche Nullpunkt
                    fuer persistente Groessen.

    3  BLOCK-NULLPUNKT
                    Wie 2, aber der feste Wert wird alle 250 Tage neu
                    gezogen - zwischen "taeglich neu" und "nie".

## Die Leseart

    amihud deutlich ueber dem persistenten Nullpunkt
        -> der Befund traegt, die 6,51 sind echt

    amihud nahe am persistenten Nullpunkt
        -> die Spanne entsteht aus PERSISTENZ plus ueberlappenden
           Ausgaengen, nicht aus Information. Dann ist auch die
           Rauschgrenze aus sqrt(p(1-p)/N) um Groessenordnungen zu klein,
           und KEINE der Spannen aus F-224/F-225 gilt.

    python pruefe_persistenz_und_nullpunkt.py
"""
from __future__ import annotations

import sys
from binascii import crc32
from collections import defaultdict

import numpy as np

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import messe_bewertungskennzahl as MB                       # noqa: E402
import messe_eigenschaft_beitrag as B                       # noqa: E402
import messe_funding_niveau as F                            # noqa: E402
import messe_kandidaten_als_regel as K                      # noqa: E402
import messe_zielregel as ZR                                # noqa: E402
from messe_bewertung_kalibrierung import _fuenftel_je_tag   # noqa: E402
# ⚠️ IMPORTIERT, NICHT NACHGEBAUT.
from messe_fuenftel_mit_tagesklammer import (               # noqa: E402
    je_tag_und_fuenftel, abweichung_je_fuenftel, _spanne)

ARTEN = ("amihud", "vola", "schnitt50", "funding", "turnover", "zufall")
SAAT = 20260905


def persistenz(f5: dict, tage_je_sym: dict) -> float:
    """Anteil der Tage, an denen ein Symbol sein Fuenftel behaelt."""
    gleich = ges = 0
    je_sym: dict = defaultdict(dict)
    for tag, d in f5.items():
        for sym, f in d.items():
            je_sym[sym][tag] = f
    for sym, je_tag in je_sym.items():
        tage = [t for t in tage_je_sym.get(sym, []) if t in je_tag]
        for a, b in zip(tage, tage[1:]):
            ges += 1
            if je_tag[a] == je_tag[b]:
                gleich += 1
    return gleich / ges if ges else float("nan")


def kunst_fuenftel(gebaut: dict, block: int | None, salz: int = 0) -> dict:
    """{tag: {sym: fuenftel}} aus einem FESTEN Zufallswert je Symbol.

    ⚠️ Maximal persistent, null Information. `block=None` heisst: EIN Wert
    fuer immer; `block=250` heisst: alle 250 Tage neu gezogen.

    ⚠️ crc32 statt hash() - hash() ist prozessweise zufaellig (F-218).
    Die Fuenftel entstehen ueber `_fuenftel_je_tag`, also ueber dieselbe
    Rangfunktion wie bei den echten Groessen - nicht ueber einen Nachbau.
    """
    tage_sortiert = sorted(gebaut)
    idx = {t: i for i, t in enumerate(tage_sortiert)}
    kunst = {}
    for tag, liste in gebaut.items():
        b = 0 if block is None else idx[tag] // block
        kunst[tag] = [
            {"sym": e["sym"],
             "kennzahl": float(np.random.default_rng(
                 crc32(("%s|%d|%d" % (e["sym"], b, salz)).encode())).random())}
            for e in liste]
    return _fuenftel_je_tag(kunst)


def main() -> int:
    print("Lade Reihen...", flush=True)
    reihen = B.lade()
    tage_je_sym = {s: [z[0] for z in roh] for s, roh in reihen.items()}
    zeilen = ZR.ergebnisse(reihen)
    print("  %d Anker · %d Reihen · Horizont %d" % (len(zeilen), len(reihen),
                                                    ZR.HORIZONT))
    print("  lade funding ...", flush=True)
    fu = F.lade_funding()
    print("  lade turnover ...", flush=True)
    tu = MB.reihe("data/onchain_historie.db", "splycur")
    quelle = {"funding": fu, "turnover": tu}

    print()
    print("=" * 96)
    print("1. PERSISTENZ — behaelt ein Symbol sein Fuenftel? (Zufall waere 20 %)")
    print("=" * 96)
    gebaut, f5 = {}, {}
    for art in ARTEN:
        gebaut[art] = K.baue(reihen, art, quelle.get(art), horizont=20)
        f5[art] = _fuenftel_je_tag(gebaut[art])
        print("  %-11s %6.1f %%" % (art, 100 * persistenz(f5[art], tage_je_sym)))

    print()
    print("=" * 96)
    print("2. DER EHRLICHE NULLPUNKT — Kunstgroessen mit ECHTER Persistenz")
    print("=" * 96)
    print("  %-24s %-34s %8s %8s" % ("Groesse", "Abweichung je Fuenftel",
                                     "Spanne", "Persist."))
    basis = gebaut["amihud"]
    grenzen = []
    for name, block in (("fest je Symbol (100 %)", None),
                        ("neu alle 250 Tage", 250),
                        ("neu alle 60 Tage", 60)):
        kf = kunst_fuenftel(basis, block)
        tg, n_tage, _feh = abweichung_je_fuenftel(
            je_tag_und_fuenftel(zeilen, tage_je_sym, kf))
        sp = _spanne(tg)
        grenzen.append((name, sp))
        print("  %-24s %-34s %7.2f %7.1f %%"
              % (name, " ".join("%+5.2f" % x for x in tg), sp,
                 100 * persistenz(kf, tage_je_sym)))

    print()
    print("=" * 96)
    print("3. DIE ECHTEN GROESSEN gegen den persistenten Nullpunkt")
    print("=" * 96)
    schaerfste = max(sp for _n, sp in grenzen)
    print("  Schaerfster Kunst-Nullpunkt: %.2f Punkte" % schaerfste)
    print()
    print("  %-11s %-34s %8s %s" % ("Groesse", "Abweichung je Fuenftel",
                                    "Spanne", "Urteil"))
    for art in ARTEN:
        tg, n_tage, _feh = abweichung_je_fuenftel(
            je_tag_und_fuenftel(zeilen, tage_je_sym, f5[art]))
        sp = _spanne(tg)
        urteil = ("traegt ueber den Nullpunkt" if sp > 2 * schaerfste
                  else "⚠️ NICHT vom persistenten Zufall zu trennen"
                  if sp <= schaerfste else "knapp - nicht belastbar")
        print("  %-11s %-34s %7.2f  %s"
              % (art, " ".join("%+5.2f" % x for x in tg), sp, urteil))

    print()
    print("  ⚠️ Faellt amihud hier durch, gilt KEINE Spanne aus F-224/F-225 -")
    print("     dann ist die Rauschgrenze aus sqrt(p(1-p)/N) um Groessen-")
    print("     ordnungen zu klein, weil die Anker nicht unabhaengig sind.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
