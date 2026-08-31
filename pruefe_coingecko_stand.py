# -*- coding: utf-8 -*-
"""Wie steht das CoinGecko-Kontingent diesen Monat wirklich?"""
import sqlite3, sys, datetime as dt
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
c = sqlite3.connect("file:data/tradinginfotool.db?mode=ro", uri=True)
try:
    print("### Kontingent-Zaehler ###")
    for r in c.execute("SELECT * FROM api_call_kontingent ORDER BY 2 DESC LIMIT 6"):
        print("  %s" % (r,))
except Exception as e:
    print("  Tabelle nicht lesbar: %s" % str(e)[:70])
try:
    print()
    print("### Gesendete Warnungen ###")
    for r in c.execute("SELECT * FROM api_call_kontingent_warnung_gesendet "
                       "ORDER BY 1 DESC LIMIT 5"):
        print("  %s" % (r,))
except Exception as e:
    print("  %s" % str(e)[:70])
