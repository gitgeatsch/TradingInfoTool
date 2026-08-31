# -*- coding: utf-8 -*-
"""R-B Schritt 1: welche NICHT-Kurs-Daten sammelt das System wirklich?"""
import sqlite3, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
c = sqlite3.connect("file:data/tradinginfotool.db?mode=ro", uri=True)
tab = [r[0] for r in c.execute(
    "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]
KURS = ("price_history", "ohlc", "signals", "hebel_signals", "portfolio",
        "llm_", "mail", "log", "cache", "settings", "watchlist", "holdings")
print("=" * 82)
print("NICHT-KURS-TABELLEN mit Inhalt")
print("=" * 82)
print("%-40s %9s  %s" % ("Tabelle", "Zeilen", "Zeitraum"))
treffer = []
for t in tab:
    if any(k in t.lower() for k in KURS):
        continue
    try:
        n = c.execute("SELECT COUNT(*) FROM [%s]" % t).fetchone()[0]
    except Exception:
        continue
    if n < 20:
        continue
    sp = [r[1] for r in c.execute("PRAGMA table_info([%s])" % t)]
    datum = next((s for s in sp if any(w in s.lower()
                  for w in ("date", "datum", "zeit", "stand", "am", "ts"))), None)
    z = ""
    if datum:
        try:
            a, b = c.execute("SELECT MIN([%s]), MAX([%s]) FROM [%s]"
                             % (datum, datum, t)).fetchone()
            z = "%s .. %s" % (str(a)[:10], str(b)[:10])
        except Exception:
            pass
    print("%-40s %9d  %s" % (t, n, z))
    treffer.append(t)
print()
print("  -> %d Tabellen mit Nicht-Kurs-Daten" % len(treffer))
