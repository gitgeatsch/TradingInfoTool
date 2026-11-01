# -*- coding: utf-8 -*-
"""FÜTTERUNG — Probe der SATZFORM (Ü1) an einem echten Stichtag (Nutzer 31.10.2026: „weiter mit dem Fütterungskonzept für Weg a“).

Seit 01.11.2026 eine dünne Hülle um ``agent/zustaende.py`` (Fütterung §6 Schritt 3, Nutzer: *„a, bauen“*) - die Rechnung steht
NUR dort (SF8: ein Rechenweg). Die alte Fassung hatte das Jahrgangsloch Z1 und stürzte bei leerer Reihe ab (Z2), siehe
``Basisinfos/Voranalyse_Zustaende_Modul_01_11.md``. Nur lesend auf ``data/_sichten/sichten.db``.

    python -X utf8 Basisinfos/Rechenkern_02_10/fuetterung_satzform_probe.py [--stichtag 2026-10-29] [--jahre 5]
"""
from __future__ import annotations

import argparse
import os
import sys

PROJ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
AUS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fuetterung_satzform_probe.txt")
sys.path.insert(0, PROJ)


def main() -> int:
    from agent import zustaende as Z
    a = argparse.ArgumentParser()
    a.add_argument("--stichtag", default="2026-10-29")
    a.add_argument("--jahre", type=int, default=Z.JAHRE)
    o = a.parse_args()
    text = Z.text(o.stichtag, Z.Ablage(), o.jahre)
    print(text)
    with open(AUS, "w", encoding="utf-8") as f:
        f.write(text + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
