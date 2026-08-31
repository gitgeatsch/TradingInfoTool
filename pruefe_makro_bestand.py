# -*- coding: utf-8 -*-
"""Was steht in macro_snapshot - und ist es messbar?"""
import sqlite3, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
c = sqlite3.connect("file:data/tradinginfotool.db?mode=ro", uri=True)
print("### Spalten von macro_snapshot ###")
sp = [r[1] for r in c.execute("PRAGMA table_info(macro_snapshot)")]
print("  " + ", ".join(sp))
print()
r = c.execute("SELECT * FROM macro_snapshot ORDER BY 1 DESC LIMIT 1").fetchone()
print("### Juengste Zeile ###")
for k, v in zip(sp, r):
    print("  %-30s %s" % (k, str(v)[:60]))
print()
print("### Belegung je Spalte (von 3384) und Historie ###")
datum = sp[0]
for s in sp[1:]:
    try:
        n, a, b = c.execute(
            "SELECT COUNT([%s]), MIN([%s]), MAX([%s]) FROM macro_snapshot "
            "WHERE [%s] IS NOT NULL" % (s, datum, datum, s)).fetchone()
        if n >= 100:
            print("  %-30s %6d  %s .. %s" % (s, n, str(a)[:10], str(b)[:10]))
    except Exception:
        pass
print()
print("### Gibt es eine Lebendigkeits-Tabelle (TVL/Entwickler)? ###")
for t in c.execute("SELECT name FROM sqlite_master WHERE type='table'"):
    if any(w in t[0].lower() for w in ("leben", "tvl", "entwickl", "defi")):
        n = c.execute("SELECT COUNT(*) FROM [%s]" % t[0]).fetchone()[0]
        print("  %-34s %d Zeilen" % (t[0], n))
