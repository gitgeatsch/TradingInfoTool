# -*- coding: utf-8 -*-
"""Warum ist H gepoolt POSITIV und je Zeitblock NEGATIV? (30.08.2026)

## Der Widerspruch, der aufgeloest werden muss

    gepoolt ueber 2017-2026     H-Quote minus Gesamtquote   +4,5 Punkte
    je 120-Tage-Block           H-Quote minus Nicht-H-Quote -4,4 Punkte

Dieselben Anker, dasselbe Mass, entgegengesetztes Vorzeichen. Genau EINE
der beiden Zahlen darf in die Bewertung, und ohne die Aufloesung waere die
Wahl zwischen ihnen Geschmackssache.

## Die Vermutung: ein Kompositionseffekt (Simpson)

Wenn H in Zeitraeumen HAEUFIGER auftritt, in denen ALLE Anker gut laufen,
dann gewinnt H im Topf - auch wenn es in jedem einzelnen Zeitraum verliert.
Der gepoolte Vorsprung waere dann nicht die Leistung von H, sondern die
Auskunft "H tritt in guten Zeiten auf".

## Die Rechnung, die das entscheidet

    gepoolt        = Quote(alle H) - Quote(alle Nicht-H)
    innerhalb      = Mittel ueber Bloecke von [Quote(H|Block) - Quote(nicht|Block)]
                     mit dem H-ANTEIL des Blocks gewichtet
    komposition    = gepoolt - innerhalb

⚠️ Die Gewichtung muss die des gepoolten Masses sein, sonst vergleicht man
zwei verschieden gewichtete Mittel und nennt den Unterschied "Effekt".

Zusaetzlich der direkte Beleg fuer den Mechanismus: die Korrelation
zwischen dem H-ANTEIL eines Blocks und dem NIVEAU des Blocks.
"""
import io
import json
import sys

import numpy as np

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

CACHE = "anker_h_2026_08_30.json"
BLOCK = 120


def main():
    anker = [a for a in json.loads(io.open(CACHE, encoding="utf-8").read())
             if a["ziel"] is not None]
    tage = sorted({a["datum"] for a in anker})
    lage = {t: i // BLOCK for i, t in enumerate(tage)}

    mit = [a["ziel"] for a in anker if a["h"]]
    ohne = [a["ziel"] for a in anker if not a["h"]]
    gepoolt = float(np.mean(mit)) - float(np.mean(ohne))

    print("=" * 92)
    print("DER WIDERSPRUCH — H GEPOOLT POSITIV, JE BLOCK NEGATIV")
    print("=" * 92)
    print("%d entschiedene Anker (Ziel oder Stop), %d mit H (%.1f %%)"
          % (len(anker), len(mit), 100 * len(mit) / len(anker)))
    print("Mass: 'Ziel vor Stop' - H's eigenes Mass.")
    print()
    print("  Quote H          %.4f  (%d Anker)" % (float(np.mean(mit)), len(mit)))
    print("  Quote Nicht-H    %.4f  (%d Anker)" % (float(np.mean(ohne)), len(ohne)))
    print("  GEPOOLT          %+.4f  = %+.2f Punkte" % (gepoolt, 100 * gepoolt))

    je_block = {}
    for a in anker:
        je_block.setdefault(lage[a["datum"]], ([], []))[0 if a["h"] else 1] \
            .append(a["ziel"])

    zeilen = []
    for b, (m, o) in sorted(je_block.items()):
        if len(m) >= 30 and len(o) >= 30:
            zeilen.append({"block": b, "n_h": len(m), "n": len(m) + len(o),
                           "diff": float(np.mean(m)) - float(np.mean(o)),
                           "niveau": float(np.mean(m + o)),
                           "anteil": len(m) / (len(m) + len(o))})
    gew = np.array([z["n_h"] for z in zeilen], dtype=float)
    d = np.array([z["diff"] for z in zeilen])
    innerhalb = float((d * gew).sum() / gew.sum())

    print("  INNERHALB        %+.4f  = %+.2f Punkte   (%d Bloecke, H-gewichtet)"
          % (innerhalb, 100 * innerhalb, len(zeilen)))
    print("  KOMPOSITION      %+.4f  = %+.2f Punkte   <- der Rest"
          % (gepoolt - innerhalb, 100 * (gepoolt - innerhalb)))

    anteil = np.array([z["anteil"] for z in zeilen])
    niveau = np.array([z["niveau"] for z in zeilen])
    r = float(np.corrcoef(anteil, niveau)[0, 1])
    print()
    print("=" * 92)
    print("DER MECHANISMUS — TRITT H IN GUTEN ZEITEN HAEUFIGER AUF?")
    print("=" * 92)
    print("  Korrelation H-Anteil eines Blocks <-> Niveau des Blocks: %+.3f" % r)
    print()
    print("  %-7s %8s %9s %10s %10s" % ("Block", "Anker", "H-Anteil",
                                        "Niveau", "H minus Rest"))
    for z in zeilen:
        print("  %-7d %8d %8.1f %% %9.4f %+10.4f"
              % (z["block"], z["n"], 100 * z["anteil"], z["niveau"], z["diff"]))

    print()
    print("=" * 92)
    print("LESART")
    print("=" * 92)
    if abs(gepoolt - innerhalb) > abs(innerhalb) and r > 0.2:
        print("  Der gepoolte Vorsprung ist ueberwiegend KOMPOSITION: H tritt in")
        print("  Bloecken mit hohem Niveau haeufiger auf. Innerhalb der Bloecke")
        print("  liegt H %+.2f Punkte. Der gepoolte Wert misst, WANN H auftritt -"
              % (100 * innerhalb))
        print("  nicht, was ein H-Anker leistet.")
    else:
        print("  Die Komposition erklaert den Unterschied NICHT allein.")


if __name__ == "__main__":
    main()
