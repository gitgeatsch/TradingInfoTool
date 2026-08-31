# -*- coding: utf-8 -*-
"""Ist der Kryptomarkt abgeflacht? (30.08.2026)

Nutzerhinweis: *"der Kryptomarkt hat sich vor allem im Bereich BTC geaendert,
er ist abgeflachter, geringere Anstiege als vor 2024."*

⚠️ Wenn das stimmt, ist es KEIN Regimewechsel, sondern ein Struktureinbruch -
und dann sind alle Messungen, die 2017-2023 mitzaehlen, auf einem anderen
Markt gerechnet. Das betrifft H (+4,5 Punkte, gemessen 2018-2026) unmittelbar.
"""
import statistics as st, sys
import numpy as np
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import messe_eigenschaft_beitrag as B

reihen = B.lade()
ABSCHNITTE = (("2018-2020", "2018-01-01", "2020-12-31"),
              ("2021-2023", "2021-01-01", "2023-12-31"),
              ("2024-2026", "2024-01-01", "2026-12-31"))

print("=" * 88)
print("HAT SICH DER MARKT VERAENDERT? BTC und der Querschnitt")
print("=" * 88)
for name, symbole in (("BTC allein", ["BTC"]), ("alle 523 Reihen", None)):
    print()
    print("### %s ###" % name)
    print("  %-12s %10s %12s %12s %12s %10s"
          % ("Abschnitt", "Tage", "Rendite p.a.", "Tagesspanne", "Vola p.a.", "Anteil +"))
    for abschnitt, von, bis in ABSCHNITTE:
        renditen, spannen, tage = [], [], 0
        for sym, roh in reihen.items():
            if symbole and sym not in symbole:
                continue
            z = [x for x in roh if von <= x[0] <= bis]
            if len(z) < 60:
                continue
            c = np.array([x[1] for x in z])
            h = np.array([x[2] for x in z]); t_ = np.array([x[3] for x in z])
            tage = max(tage, len(z))
            jahre = len(z) / 252
            if c[0] > 0 and jahre > 0.4:
                renditen.append((c[-1] / c[0]) ** (1 / jahre) - 1)
            tagesrend = c[1:] / np.maximum(c[:-1], 1e-12) - 1
            spannen.append((float(np.median((h - t_) / np.maximum(c, 1e-12))),
                            float(np.std(tagesrend) * np.sqrt(252)),
                            float(np.mean(tagesrend > 0))))
        if not renditen:
            continue
        print("  %-12s %10d %11.1f %% %11.2f %% %11.1f %% %9.1f %%"
              % (abschnitt, tage, 100*st.median(renditen),
                 100*st.median([x[0] for x in spannen]),
                 100*st.median([x[1] for x in spannen]),
                 100*st.median([x[2] for x in spannen])))
print()
print("### Und die Bewegung in R — das Mass, mit dem wir messen ###")
print("  %-12s %14s %14s" % ("Abschnitt", "Median 20 T", "99-%-Quantil"))
for abschnitt, von, bis in ABSCHNITTE:
    werte = []
    for sym, roh in reihen.items():
        tage = [x[0] for x in roh]
        c = np.array([x[1] for x in roh])
        h = np.array([x[2] for x in roh]); t_ = np.array([x[3] for x in roh])
        breite = B.spanne(h, t_, c, B.SCHWANKUNG)
        for i in range(60, len(c) - 20):
            if von <= tage[i] <= bis and np.isfinite(breite[i]) and breite[i] > 0:
                werte.append((c[i+20] - c[i]) / breite[i])
    if werte:
        print("  %-12s %+13.4f %+14.2f"
              % (abschnitt, float(np.median(werte)), float(np.quantile(werte, 0.99))))
