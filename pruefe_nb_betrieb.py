# -*- coding: utf-8 -*-
"""Was sagt der NB-Export zu den offenen Betriebsfragen? (30.08.2026)

Drei Fragen, die von der Desktop-Kopie aus nicht beantwortbar waren:
  1. Sammelt das Notebook TVL (lebendigkeit_beobachtung)?
  2. Sammelt es Funding (open_interest_snapshot)?
  3. Wie steht das CoinGecko-Kontingent?
"""
import io, json, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
P = r"K:\My Drive\Claude_Austauschordner\Notebook_Analysedaten\notebook_diagnose.json"
d = json.load(io.open(P, encoding="utf-8"))
print("Oberste Schluessel: %s" % ", ".join(list(d)[:25]))
print()

def suche(o, worte, pfad="", tiefe=0):
    tref = []
    if tiefe > 6: return tref
    if isinstance(o, dict):
        for k, v in o.items():
            if any(w in k.lower() for w in worte):
                groesse = len(v) if isinstance(v, (list, dict)) else str(v)[:60]
                tref.append((pfad + "/" + k, type(v).__name__, groesse))
            tref += suche(v, worte, pfad + "/" + k, tiefe+1)
    elif isinstance(o, list) and o and isinstance(o[0], dict):
        tref += suche(o[0], worte, pfad + "[0]", tiefe+1)
    return tref

for name, worte in (("TVL / Lebendigkeit", ("lebendigkeit", "tvl", "entwickl")),
                    ("Funding / Open Interest", ("funding", "open_interest", "positionier")),
                    ("Kontingent", ("kontingent", "coingecko", "quota"))):
    print("### %s ###" % name)
    t = suche(d, worte)
    if not t:
        print("  -> nichts gefunden")
    for p, typ, g in t[:8]:
        print("  %-56s %-6s %s" % (p[:56], typ, g))
    print()
