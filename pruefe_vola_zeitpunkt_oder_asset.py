# -*- coding: utf-8 -*-
"""N-43c: Ist `vola` eine ZEITPUNKT- oder eine ASSET-Aussage? (05.09.2026)

## Warum diese Pruefung sein MUSS

**Regel 3: Wir bewerten Zeitpunkte, nicht Assets.**

N-43/N-43b haben `vola` als starken Kandidaten gefunden - volle Abdeckung,
Stabilitaet +0,647, unabhaengig von funding, bedingt 2,73 gegen 0,90 Punkte.

⚠️ **Und genau diese Staerke ist verdaechtig.** Volatilitaet ist zum Teil
eine dauerhafte ASSET-Eigenschaft: dieselben Coins sind ueber Jahre
volatiler als andere. Eine Fuenftel-Ordnung, die ueber sechs Bloecke haelt,
ist genau das, was eine dauerhafte Asset-Eigenschaft erzeugen wuerde - ohne
dass ueber den ZEITPUNKT irgendetwas gesagt waere.

Am selben Tag hat **F-218** gezeigt, dass die Bewertung genau so schon
einmal verdeckt gegen Regel 3 verstossen hat (sie kodierte "hat dieses
Asset Daten"). Der Fehler zweimal am selben Tag waere vermeidbar.

## Die Unterscheidung

    QUER (bisher)   Fuenftel je TAG ueber alle Symbole
                    -> "welche Coins sind heute volatiler als andere"
                    -> kann eine reine Asset-Aussage sein

    LAENGS (hier)   Fuenftel je SYMBOL ueber seine eigene Geschichte
                    -> "ist DIESER Coin gerade volatiler als sonst"
                    -> das ist eine ZEITPUNKT-Aussage

⚠️ Nur wenn `vola` auch LAENGS trennt, sagt sie etwas ueber den Moment.
Trennt sie nur QUER, ist sie eine Rangliste von Assets - und faellt unter
Regel 3, egal wie stabil sie ist.

## Die Kontrolle

`zufall` laeuft laengs mit. Eine Kunstgroesse darf innerhalb eines Symbols
nichts ordnen; tut sie es, misst das Verfahren einen Artefakt.

⚠️ Und die Laengs-Fuenftel werden NACHLAUFEND gebildet - nur aus der
Vergangenheit des Symbols. Ein Perzentil ueber die ganze Reihe kennt die
Zukunft.

    python pruefe_vola_zeitpunkt_oder_asset.py
"""
from __future__ import annotations

import sys
from collections import defaultdict

import numpy as np

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import messe_eigenschaft_beitrag as B                       # noqa: E402
import messe_kandidaten_als_regel as K                      # noqa: E402
import messe_zielregel as ZR                                # noqa: E402
from messe_stufen_aus_quote import quote_je_fuenftel        # noqa: E402

RUECKBLICK = 250          # Tage eigener Geschichte fuer das Perzentil
MIND_JE_FUENFTEL = 2000


def laengs_fuenftel(werte_je_sym: dict, tage_je_sym: dict) -> dict:
    """{tag: {sym: fuenftel}} - Rang IM EIGENEN Rueckblick, nachlaufend.

    ⚠️ Nur Tage vor i gehen ein. Ein Perzentil ueber die ganze Reihe waere
    ein Blick in die Zukunft.
    """
    aus: dict = defaultdict(dict)
    for sym, reihe in werte_je_sym.items():
        tage = tage_je_sym.get(sym)
        if not tage:
            continue
        for i, w in enumerate(reihe):
            if w is None or not np.isfinite(w) or i < RUECKBLICK:
                continue
            hist = [x for x in reihe[i - RUECKBLICK:i]
                    if x is not None and np.isfinite(x)]
            if len(hist) < RUECKBLICK // 2:
                continue
            r = float(np.mean([1.0 if x <= w else 0.0 for x in hist]))
            aus[tage[i]][sym] = min(int(r * 5), 4)
    return dict(aus)


def _als_reihen(gebaut: dict, tage_je_sym: dict) -> dict:
    """{sym: [wert je Tag]} aus dem TAGES-Aufbau von `K.baue`.

    ⚠️ VOR DEM LAUF AN DER QUELLE GEPRUEFT (05.09.). `K.baue` liefert
    `{tag: [{"sym":…, "kennzahl":…, "in_r":…}, …]}` - nach TAG geschluesselt,
    nicht nach Symbol. Die erste Fassung hier nahm `{sym: [(tag, wert)]}` an
    und haette still leere Reihen erzeugt: `_als_reihen` haette nichts
    gefunden, `laengs_fuenftel` nichts gebildet, und der Lauf haette
    "zu duenn" gemeldet - was wie ein Datenmangel ausgesehen haette und
    keiner gewesen waere. Fail-soft ist fail-silent.
    """
    je_sym: dict = defaultdict(dict)
    for tag, liste in gebaut.items():
        for e in liste:
            w = e.get("kennzahl")
            if w is not None:
                je_sym[e["sym"]][tag] = float(w)
    aus = {}
    for sym, je_tag in je_sym.items():
        tage = tage_je_sym.get(sym)
        if tage:
            aus[sym] = [je_tag.get(t) for t in tage]
    return aus


def main() -> int:
    print("Lade Reihen...", flush=True)
    reihen = B.lade()
    tage_je_sym = {s: [z[0] for z in roh] for s, roh in reihen.items()}
    zeilen = ZR.ergebnisse(reihen)
    print("  %d Anker · %d Reihen" % (len(zeilen), len(reihen)))

    for art in ("vola", "zufall"):
        print()
        print("=" * 92)
        print("%s — LAENGS: trennt sie INNERHALB eines Symbols ueber die Zeit?"
              % art.upper())
        print("=" * 92)
        gebaut = K.baue(reihen, art, None, horizont=20)
        werte = _als_reihen(gebaut, tage_je_sym)
        f5 = laengs_fuenftel(werte, tage_je_sym)
        je = quote_je_fuenftel(zeilen, tage_je_sym, f5)
        if not je or any(je.get(f, (0, 0))[1] < MIND_JE_FUENFTEL
                         for f in range(5)):
            n = min((je.get(f, (0, 0))[1] for f in range(5)), default=0)
            print("  zu duenn (n_min %d von %d noetig)" % (n, MIND_JE_FUENFTEL))
            continue
        q = [100.0 * je[f][0] / je[f][1] for f in range(5)]
        n = [je[f][1] for f in range(5)]
        print("  Quote je eigenem Fuenftel: %s"
              % " ".join("%.2f" % x for x in q))
        print("  n je Fuenftel:             %s"
              % " ".join("%6d" % x for x in n))
        print("  Spanne %.2f Punkte" % (max(q) - min(q)))
        # monoton?
        mon = all(q[i] >= q[i + 1] for i in range(4)) or \
              all(q[i] <= q[i + 1] for i in range(4))
        print("  monoton: %s" % ("ja" if mon else "nein"))

    print()
    print("  ⚠️ LESEART")
    print("     vola LAENGS deutlich ueber zufall -> ZEITPUNKT-Aussage, Regel 3")
    print("        ist erfuellt, der Kandidat traegt")
    print("     vola LAENGS wie zufall            -> die Quer-Ordnung war eine")
    print("        ASSET-Rangliste. Nicht registrieren.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
