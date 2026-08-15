# -*- coding: utf-8 -*-
"""BESTANDSERHEBUNG: was sieht welche Rolle bei welcher Assetklasse? (16.08.2026)

Schritt 1 des Auftrags. NICHT aus dem Code gelesen, sondern GERENDERT - was
das Modell woertlich bekommt, je Gruppe und Instrument. Ein Code-Studium sagt,
was gebaut ist; nur der gerenderte Satz sagt, was ankommt.

Zusaetzlich je Satz: traegt er eine ZAHL, und wenn ja, ist sie eingeordnet?
Das ist die zweite Haelfte des Auftrags - LLM-Tauglichkeit. Der Grund, warum
`lagebeschreibung.py` ueberhaupt existiert, steht in seinem Kopf: nackte Zahlen
werden zertokenisiert und tragen nicht; Sprache mit Bezug traegt.
"""
from __future__ import annotations

import os
import re
import sys

S = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, r"D:\CLAUDE_Projects\SoftwareProjekte\TradingInfoTool")
os.chdir(r"D:\CLAUDE_Projects\SoftwareProjekte\TradingInfoTool")
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from agent import assetklassen as AK                            # noqa: E402
from agent import rollen_eingabe as RE                          # noqa: E402
from backtest_llm1_historisch import lade_reihen_aus_db         # noqa: E402

DB = os.path.join(S, "nb_0815.db")
# Woran eine Zahl als EINGEORDNET gilt: sie steht neben einem Bezug.
BEZUG = ("perzentil", "gegen", "vergleich", "handelstage", "mittel", "je tag",
         "tage", "%", "ueber", "unter", "seit", "mal beruehrt")


def zahl_lage(satz: str) -> str:
    hat = bool(re.search(r"\d", satz))
    if not hat:
        return "ohne Zahl"
    s = satz.lower()
    return "Zahl MIT Bezug" if any(w in s for w in BEZUG) else "Zahl OHNE Bezug"


def main() -> int:
    reihen = lade_reihen_aus_db(DB)
    print("=" * 78)
    print("BESTANDSERHEBUNG - was die Rolle BC (Trader) je Gruppe sieht")
    print("=" * 78)

    gesehen = {}
    for gruppe, instrument, symbole in AK.laeufe():
        sym = next((s for s in symbole
                    if s in reihen and len(reihen[s]) >= 320), None)
        if not sym:
            print(f"\n### {gruppe}/{instrument}: kein Symbol mit langer Reihe")
            continue
        r = reihen[sym]
        idx = len(r) - 1
        bloecke = {}
        _, bc = RE.baue_fall(symbol=sym, reihe=r, index=idx,
                             reihen={sym: r}, db=DB, mit_finanzierung=False,
                             instrument=instrument, assetklasse=gruppe,
                             bloecke_ziel=bloecke)
        gesehen[(gruppe, instrument)] = (sym, bc, bloecke)
        print(f"\n### {gruppe} / {instrument}   ({sym})")
        print(f"  Schluessel: {sorted(bc)}")
        for satz in (bc.get("auftrag") or []):
            print(f"  [auftrag ] {satz}")
        for block, saetze in bloecke.items():
            for satz in saetze:
                print(f"  [{block:9}] {satz[:150]}")

    print()
    print("=" * 78)
    print("A. UNTERSCHEIDET SICH DER FAKTENSATZ JE GRUPPE?")
    print("=" * 78)
    grund = None
    for (g, i), (sym, bc, bl) in gesehen.items():
        muster = {b: len(s) for b, s in bl.items()}
        if grund is None:
            grund = muster
        gleich = (muster == grund)
        print(f"  {g:12}/{i:12} {sym:8} Bloecke {muster}"
              + ("" if gleich else "   <- ABWEICHEND"))

    print()
    print("=" * 78)
    print("B. LLM-TAUGLICHKEIT: Zahl mit oder ohne Bezug?")
    print("=" * 78)
    from collections import Counter
    je_block = {}
    for (g, i), (sym, bc, bl) in gesehen.items():
        for block, saetze in bl.items():
            for satz in saetze:
                je_block.setdefault(block, Counter())[zahl_lage(satz)] += 1
    print(f"  {'Block':14}{'ohne Zahl':>11}{'MIT Bezug':>11}{'OHNE Bezug':>12}")
    for block, c in je_block.items():
        print(f"  {block:14}{c['ohne Zahl']:>11}{c['Zahl MIT Bezug']:>11}"
              f"{c['Zahl OHNE Bezug']:>12}")
    print()
    print("  Saetze mit Zahl OHNE Bezug (die kritischen):")
    for (g, i), (sym, bc, bl) in gesehen.items():
        for block, saetze in bl.items():
            for satz in saetze:
                if zahl_lage(satz) == "Zahl OHNE Bezug":
                    print(f"    [{g}/{block}] {satz[:130]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
