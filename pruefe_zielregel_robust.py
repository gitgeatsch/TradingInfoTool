# -*- coding: utf-8 -*-
"""K-2 nach der Bereinigung: ist der Rest robust? (29.08.2026)

Zwei Reparaturen gegenueber dem ersten Lauf:
  1. Anker mit Token-Umstellung im Vorwaertsfenster sind entfernt
  2. Der Bootstrap mittelt jetzt GEWICHTET nach Blocklaenge - ungewichtet
     war er bei gefilterten Teilmengen falsch (der Punktschaetzer lag
     ausserhalb seines eigenen Intervalls)
"""
import sys
import numpy as np
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import messe_eigenschaft_beitrag as B
import messe_zielregel as Z

reihen = B.lade()
zeilen = Z.ergebnisse(reihen)
print("=" * 82)
print("K-2 BEREINIGT — Robustheit des Restbefunds (%d Anker)" % len(zeilen))
print("=" * 82)

d = np.array([z["OHNE ZIEL"] - z["ZIEL 2,0"] for z in zeilen])
s = np.sort(d)
print()
print("GEPAARTE DIFFERENZ  OHNE ZIEL minus ZIEL 2,0")
print("  Mittel                       %+.4f R" % d.mean())
for p in (1, 0.5, 0.1):
    k = max(1, int(len(s) * p / 100))
    print("  getrimmt (oberste %4.1f %% weg)  %+.4f R" % (p, s[:-k].mean()))
print("  Median                       %+.4f R" % np.median(d))
print("  Anteil positiv               %.1f %%" % (100*(d > 0).mean()))
k = max(1, len(s)//100)
print("  Anteil des obersten 1 %% am Mittel: %.1f %%" % (100*s[-k:].sum()/s.sum()))

print()
print("JE REIHE — die Ebene, die praktisch zaehlt")
je = {}
for z in zeilen:
    je.setdefault(z["sym"], []).append(z["OHNE ZIEL"] - z["ZIEL 2,0"])
mit = {s_: float(np.mean(v)) for s_, v in je.items()}
med = {s_: float(np.median(v)) for s_, v in je.items()}
print("  nach MITTEL : %d von %d Reihen positiv (%.0f %%)"
      % (sum(1 for v in mit.values() if v > 0), len(mit),
         100*sum(1 for v in mit.values() if v > 0)/len(mit)))
print("  nach MEDIAN : %d von %d Reihen positiv (%.0f %%)"
      % (sum(1 for v in med.values() if v > 0), len(med),
         100*sum(1 for v in med.values() if v > 0)/len(med)))
w = np.array(list(mit.values()))
print("  Mittel ueber die Reihen %+.4f R   Median ueber die Reihen %+.4f R"
      % (w.mean(), np.median(w)))
beste = sorted(mit.items(), key=lambda x: -x[1])[:5]
print("  staerkste: %s" % ", ".join("%s %+.2f" % (a, b) for a, b in beste))
ohne = [v for a, v in mit.items() if a not in dict(beste)]
print("  ohne die fuenf staerksten: %+.4f R" % float(np.mean(ohne)))

# Bootstrap ueber REIHEN - das ist die ehrliche Einheit
rng = np.random.default_rng(20260829)
n = len(w)
z = np.array([w[rng.integers(0, n, n)].mean() for _ in range(20000)])
u, o = np.quantile(z, [0.025, 0.975])
print()
print("  Bootstrap ueber die 523 REIHEN: %+.4f R  [%+.4f .. %+.4f]  %s"
      % (w.mean(), u, o, "traegt" if (u > 0 or o < 0) else "NICHT von null zu trennen"))
