# -*- coding: utf-8 -*-
"""Die Details zu TVL-Sammlung, Funding-Sammlung und Kontingent."""
import io, json, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
P = r"K:\My Drive\Claude_Austauschordner\Notebook_Analysedaten\notebook_diagnose.json"
d = json.load(io.open(P, encoding="utf-8"))

print("### 1. CoinGecko-Kontingent ###")
print("  %s" % json.dumps(d.get("coingecko_kontingent"), ensure_ascii=False))
print()
print("### 2. TVL / Lebendigkeit am Notebook ###")
leb = d.get("kapitel93", {}).get("lebendigkeit", {})
for k, v in leb.items():
    print("  %-32s %s" % (k, json.dumps(v, ensure_ascii=False)[:150]))
print()
print("### 3. Funding-Sammlung ###")
oi = d.get("oi_fakten_verlauf", {})
for k, v in oi.items():
    if k != "eintraege":
        print("  %-38s %s" % (k, json.dumps(v, ensure_ascii=False)[:110]))
e = oi.get("eintraege") or []
print("  Eintraege: %d" % len(e))
if e:
    print("  erster: %s" % json.dumps(e[0], ensure_ascii=False)[:170])
    tage = sorted({str(x.get("tag") or x.get("datum") or x.get("stand") or "")[:10]
                   for x in e if any(x.get(s) for s in ("tag","datum","stand"))})
    if tage:
        print("  Zeitraum: %s .. %s (%d Tage)" % (tage[0], tage[-1], len(tage)))
    syms = {x.get("symbol") for x in e if x.get("symbol")}
    print("  Symbole: %d" % len(syms))
