# -*- coding: utf-8 -*-
"""N8 - DIE LIVE-ABDECKUNG (06.09.2026)

Die Arithmetik sagt: ein Wert OHNE turnover-Rang kann die Schwelle nie
erreichen. Wie viele Werte betrifft das im laufenden Betrieb?
"""
from __future__ import annotations
import sqlite3
import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, ".")
from agent import marktrang as MR                            # noqa: E402


def main() -> int:
    print("=" * 88)
    print("DIE MESSBASEN im laufenden Betrieb")
    print("=" * 88)
    basen = {}
    for name in MR.MESSBASIS:
        try:
            basen[name] = MR.messbasis(name)
            print("  %-12s %4d Symbole" % (name, len(basen[name])))
        except Exception as e:                               # noqa: BLE001
            print("  %-12s FEHLER: %s" % (name, e))

    c = sqlite3.connect("data/tradinginfotool.db")
    beobachtet = {r[0] for r in c.execute(
        "SELECT DISTINCT symbol FROM holdings") if r[0]}
    beobachtet |= {r[0] for r in c.execute(
        "SELECT DISTINCT symbol FROM asset_hebel_settings") if r[0]}
    print()
    print("  beobachtete Werte (Bestand + Hebel-Liste): %d" % len(beobachtet))

    print()
    print("=" * 88)
    print("WIE VIELE DAVON KOENNEN DIE SCHWELLE UEBERHAUPT ERREICHEN?")
    print("=" * 88)
    tu = basen.get("turnover", set())
    fu = basen.get("funding", set())
    mit_tu = beobachtet & tu
    mit_fu = beobachtet & fu
    print("  mit turnover-Rang : %3d von %d  (%.0f %%)"
          % (len(mit_tu), len(beobachtet),
             100 * len(mit_tu) / max(len(beobachtet), 1)))
    print("  mit funding-Rang  : %3d von %d  (%.0f %%)"
          % (len(mit_fu), len(beobachtet),
             100 * len(mit_fu) / max(len(beobachtet), 1)))
    print()
    print("  ⚠️ OHNE turnover-Rang kann ein Wert die Schwelle NIE erreichen")
    print("     (bestes Funding allein: +1,30 Punkte -> +0,0390 R < 0,080).")
    print("     Betroffen: %d von %d beobachteten Werten (%.0f %%)"
          % (len(beobachtet) - len(mit_tu), len(beobachtet),
             100 * (len(beobachtet) - len(mit_tu)) / max(len(beobachtet), 1)))
    print()
    print("  Und selbst MIT Rang muss er im NIEDRIGSTEN Fuenftel liegen:")
    print("     rund 20 %% von %d  ->  etwa %d Werte koennen an einem Tag"
          % (len(mit_tu), round(0.2 * len(mit_tu))))
    print("     ueberhaupt die Schwelle erreichen.")
    fehlt = sorted(beobachtet - tu)
    print()
    print("  ohne turnover-Rang (Auszug): %s" % ", ".join(fehlt[:24]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
