"""Nur LESEN: echte Faktensaetze aus dem Notebook-Export ziehen.

Streamt bis zum gesuchten Top-Level-Schluessel und dekodiert nur DESSEN Wert -
125 MB komplett zu laden waere unnoetig. Schreibt nach fakten_<name>.json im
Scratchpad, ruehrt weder Produktiv-DB noch den Austauschordner an.
"""
import json
import sys

P = r"K:/My Drive/Claude_Austauschordner/Notebook_Analysedaten/notebook_diagnose.json"
SCHLUESSEL = sys.argv[1] if len(sys.argv) > 1 else "hebel_faktensaetze"

marke = f'"{SCHLUESSEL}":'
dec = json.JSONDecoder()
buf = ""
gefunden = -1

with open(P, encoding="utf-8") as f:
    while True:
        stueck = f.read(1 << 22)
        if not stueck:
            break
        buf += stueck
        if gefunden < 0:
            i = buf.find(marke)
            if i < 0:
                buf = buf[-len(marke):]          # Marke koennte an der Naht liegen
                continue
            buf = buf[i + len(marke):].lstrip()
            gefunden = 1
        try:
            wert, _ = dec.raw_decode(buf)
        except ValueError:
            continue                              # noch unvollstaendig, weiterlesen
        ziel = f"fakten_{SCHLUESSEL}.json"
        json.dump(wert, open(ziel, "w", encoding="utf-8"), ensure_ascii=False)
        n = len(wert) if isinstance(wert, (list, dict)) else 1
        print(f"{SCHLUESSEL}: {n} Eintraege -> {ziel}")
        if isinstance(wert, list) and wert:
            print("  Felder je Eintrag:", sorted(wert[0].keys())[:20])
        elif isinstance(wert, dict):
            print("  Schluessel:", list(wert)[:20])
        sys.exit(0)

print(f"{SCHLUESSEL} nicht gefunden oder unvollstaendig.")
sys.exit(1)
