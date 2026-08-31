# -*- coding: utf-8 -*-
"""Gibt es ASSET-spezifische Nicht-Kurs-Daten - und liefern die Quellen Historie?"""
import sqlite3, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
c = sqlite3.connect("file:data/tradinginfotool.db?mode=ro", uri=True)
print("### ALLE Tabellen mit einer symbol-Spalte (= asset-spezifisch) ###")
for (t,) in c.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"):
    sp = [r[1].lower() for r in c.execute("PRAGMA table_info([%s])" % t)]
    if not any(s in sp for s in ("symbol", "coin", "asset", "ticker")):
        continue
    try:
        n = c.execute("SELECT COUNT(*) FROM [%s]" % t).fetchone()[0]
    except Exception:
        continue
    if n < 10:
        continue
    print("  %-34s %8d Zeilen   %s" % (t, n, ", ".join(sp[:7])))
