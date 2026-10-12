"""P16 Spot B3 (12.10.2026, Spot §47.4) - TEIL 0 (R-R11): die Betriebsregel ``spot_upbit.listing`` findet am Upbit-Archiv der Messung
(data/_c2/ankuendigungen.db) DIESELBEN Ereignisse (Kuerzel UND Zeit) wie ``c2_messung.ereignisse`` (Art C2-b). Nur lesend.

    python Basisinfos/Rechenkern_02_10/p16_teil0.py
"""
import os
import sqlite3
import sys

WURZEL = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, WURZEL)
sys.path.insert(0, os.path.join(WURZEL, "Basisinfos", "Spot_Voranalyse_04_10"))
os.chdir(WURZEL)
import agent.spot_upbit as SU  # noqa: E402

c = sqlite3.connect("file:data/_c2/ankuendigungen.db?mode=ro", uri=True)
betrieb = sorted((utc, k) for titel, utc in c.execute("SELECT titel, utc FROM upbit") for k in SU.listing(titel))
import c2_messung as C2  # noqa: E402
E = C2.ereignisse()
E = E[E.art == "C2-b Upbit-Listing"]
messung = sorted((str(t)[:19], s) for t, s in zip(E.zeit, E.sym))
gleich = betrieb == messung
print("TEIL 0: Betrieb %d Ereignisse · Messung %d · gleich %s%s" % (len(betrieb), len(messung), gleich,
      "" if gleich else " · Unterschied %s" % sorted(set(betrieb) ^ set(messung))[:5]))
print("\n%d von 1 gleich" % int(gleich))
