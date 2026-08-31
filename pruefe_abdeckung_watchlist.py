# -*- coding: utf-8 -*-
"""Schritt 1, Machbarkeit: decken Funding und Turnover unsere Watchlist ab?

Ein Querschnittsrang braucht genug Symbole AM SELBEN TAG. Wenn nur 12 der 44
Krypto-Werte eine Umlaufmenge haben, ist der Turnover-Rang duenn - und die
Bewertung waere fuer die uebrigen leer.
"""
import io, json, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import messe_funding_niveau as F
import messe_bewertungskennzahl as MB

P = r"K:\My Drive\Claude_Austauschordner\Notebook_Analysedaten\notebook_diagnose.json"
w = json.load(io.open(P, encoding="utf-8"))["watchlist_stammdaten"]
krypto = sorted(s.upper() for s, v in w.items()
                if str(v.get("assetklasse")) == "krypto")
print("Krypto in der Watchlist: %d" % len(krypto))

funding = {s.upper() for s in F.lade_funding()}
menge = {s.upper() for s in MB.reihe("data/onchain_historie.db", "splycur")}
mit_f = [s for s in krypto if s in funding]
mit_m = [s for s in krypto if s in menge]
print()
print("  mit FUNDING  : %2d von %d  (%.0f %%)" % (len(mit_f), len(krypto),
                                                   100*len(mit_f)/len(krypto)))
print("  mit UMLAUFMENGE (fuer Turnover): %2d von %d  (%.0f %%)"
      % (len(mit_m), len(krypto), 100*len(mit_m)/len(krypto)))
print()
print("  ohne Funding: %s" % ", ".join(s for s in krypto if s not in funding))
print()
print("  ohne Umlaufmenge: %s" % ", ".join(s for s in krypto if s not in menge))
print()
print("⚠️ Ein Querschnittsrang aus %d Werten hat Fuenftel von je %d Symbolen."
      % (len(mit_m), max(len(mit_m)//5, 0)))
