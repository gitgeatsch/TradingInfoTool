# -*- coding: utf-8 -*-
"""Wieviele UNSERER Symbole haben ueberhaupt TVL bei DefiLlama?

Entscheidet, ob TVL als Bewertungsbeitrag taugt: eine Groesse, die nur ein
Fuenftel der Werte abdeckt, kann keine Rangfolge ueber alle bilden.
"""
import json, sys, urllib.request, collections
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import messe_eigenschaft_beitrag as B

r = urllib.request.Request("https://api.llama.fi/protocols",
                           headers={"User-Agent": "TradingInfoTool/1.0"})
with urllib.request.urlopen(r, timeout=60) as a:
    prot = json.loads(a.read().decode("utf-8"))
print("DefiLlama kennt %d Protokolle." % len(prot))

# Symbol -> Summe TVL (ein Symbol kann mehrere Protokolle haben)
tvl = collections.defaultdict(float)
name = {}
for p in prot:
    s = str(p.get("symbol") or "").upper().strip()
    v = p.get("tvl")
    if s and s not in ("-", "NONE") and v:
        tvl[s] += float(v)
        name.setdefault(s, p.get("name"))
print("Davon mit brauchbarem Kuerzel: %d Symbole" % len(tvl))
print()

unsere = set(B.lade().keys())
treffer = sorted(unsere & set(tvl), key=lambda s: -tvl[s])
print("### Abdeckung unserer %d Messreihen ###" % len(unsere))
print("  mit TVL: %d (%.0f %%)" % (len(treffer), 100*len(treffer)/len(unsere)))
print()
print("  %-9s %16s   %s" % ("Symbol", "TVL USD", "Protokoll"))
for s in treffer[:15]:
    print("  %-9s %16.0f   %s" % (s, tvl[s], name.get(s, "")))
if len(treffer) > 15:
    print("  ... und %d weitere" % (len(treffer)-15))
print()
ohne = sorted(unsere - set(tvl))
print("  OHNE TVL (%d): %s ..." % (len(ohne), ", ".join(ohne[:18])))
