# -*- coding: utf-8 -*-
"""Gegenpruefung zur Schwellen-Kalibrierung (30.08.2026).

Vier Verdachtsmomente:
  V1 SUCHPREIS      neun Schwellen abgesucht - das Maximum ist auch bei
                    Zufall irgendwo
  V2 ZEITSTABIL     haelt das Optimum in beiden Haelften?
  V3 INTERVALL      Bootstrap ueber Bloecke von Kalendertagen
  V4 DISKRET        bei 5x5 Fuenftel-Kombinationen gibt es nur 25 moegliche
                    Potentialwerte - liegen die Schwellen ueberhaupt dazwischen?
"""
import statistics as st, sys, collections
import numpy as np
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import messe_schwelle_kalibrierung as SK
import messe_bewertungskennzahl as MB

je_tag = SK.bewerte(SK.baue())
alle = [x for z in je_tag.values() for x in z]
rng = np.random.default_rng(31415)

print("=" * 84)
print("V4 — welche Potentialwerte gibt es ueberhaupt?")
print("=" * 84)
c = collections.Counter(round(x["potential"], 4) for x in alle)
print("  %d verschiedene Werte. Die haeufigsten:" % len(c))
for w, n in sorted(c.items())[:12]:
    print("    %+.4f  %6d Anker (%.1f %%)" % (w, n, 100*n/len(alle)))
print()
print("=" * 84)
print("V2/V3 — Zeitstabilitaet und Bootstrap je Schwelle")
print("=" * 84)
tage = sorted(je_tag); mitte = tage[len(tage)//2]
print("  %-9s %10s %14s %14s %s"
      % ("Schwelle", "Durchlass", "erste Haelfte", "zweite Haelfte", "Bootstrap ueber Tage"))
for s in (0.000, 0.010, 0.020, 0.030):
    # je Kalendertag: Median mit Schwelle minus Median ohne
    d = {}
    for tag, z in je_tag.items():
        bleibt = [x["in_r"] for x in z if x["potential"] > s]
        if len(bleibt) >= 3:
            d[tag] = float(np.median(bleibt) - np.median([x["in_r"] for x in z]))
    if len(d) < 100:
        print("  %-9.3f zu wenige Tage" % s); continue
    h1 = [v for t, v in d.items() if t < mitte]
    h2 = [v for t, v in d.items() if t >= mitte]
    durch = 100*sum(1 for x in alle if x["potential"] > s)/len(alle)
    zeile = "  %-9.3f %9.1f %% %+13.4f %+14.4f  " % (s, durch, st.mean(h1), st.mean(h2))
    print(zeile, end="")
    MB.urteil_tage("", d, rng, 250)
print()
print("=" * 84)
print("V1 — SUCHPREIS: neun Schwellen abgesucht")
print("=" * 84)
print("  Das Maximum bei 0,020 ist EINE von neun Zellen. Gegenprobe: dieselbe")
print("  Rechnung mit ZUFAELLIG vertauschtem Potential innerhalb jedes Tages.")
beste_zufall = []
for _ in range(200):
    bester = -9
    for s in SK.SCHWELLEN:
        werte = []
        for z in je_tag.values():
            p = rng.permutation([x["potential"] for x in z])
            bleibt = [x["in_r"] for x, pp in zip(z, p) if pp > s]
            if len(bleibt) >= 3:
                werte.append(np.median(bleibt) - np.median([x["in_r"] for x in z]))
        if len(werte) > 100:
            bester = max(bester, float(np.mean(werte)))
    beste_zufall.append(bester)
schwelle95 = float(np.quantile(beste_zufall, 0.95))
echt = []
for z in je_tag.values():
    bleibt = [x["in_r"] for x in z if x["potential"] > 0.020]
    if len(bleibt) >= 3:
        echt.append(np.median(bleibt) - np.median([x["in_r"] for x in z]))
print("  bester Zufallswert aus 200 Laeufen: %+.4f" % max(beste_zufall))
print("  Schwelle (95 %%):                    %+.4f" % schwelle95)
print("  gemessen bei 0,020:                 %+.4f" % float(np.mean(echt)))
print("  -> %s" % ("TRAEGT" if float(np.mean(echt)) > schwelle95 else "⚠️ TRAEGT NICHT"))
