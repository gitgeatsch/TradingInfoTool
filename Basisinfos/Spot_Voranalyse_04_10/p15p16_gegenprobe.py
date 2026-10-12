"""Voranalyse P15 + P16 - GEGENPROBE der Fakten auf eigenem Weg. Nur lesend.

    python Basisinfos/Spot_Voranalyse_04_10/p15p16_gegenprobe.py <NB-Sicherung tradinginfotool.db>

  G1 Bestaende mit frei + gestakt > 0 per eigenem SQL (Summe statt Python-Schleife): 47 (V1: 1 + 3 + 27 + 3 + 8 + 4 + 1)
  G2 offene Hebelpositionen ueber geschlossen_am IS NULL statt Status-Text: BTC, ETH
  G3 Upbit je Kreis-Coin ueber eine ZWEITE Schnittstelle (/v1/ticker?markets=KRW-X): die 11 ohne KRW-Markt liefern keinen Kurs,
     drei gelistete Gegenbeispiele (BIO, TAO, CC) liefern einen
  G4 Upbit-Ereignisse ueber die Funktion der MESSUNG (c2_messung.ereignisse, Art C2-b) gegen die Zaehlung V4 (137)
"""
import os
import sqlite3
import sys
import time

import requests

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HIER)
NB = sys.argv[1]
ERG = []


def pruefe(k, ok, text):
    ERG.append(bool(ok))
    print("%-3s %-10s %s" % (k, "gleich" if ok else "ABWEICHUNG", text))


c = sqlite3.connect("file:%s?mode=ro" % NB.replace("\\", "/"), uri=True)
n = c.execute("SELECT SUM(COALESCE(quantity,0) + COALESCE(staked_quantity,0) > 0) FROM holdings").fetchone()[0]
pruefe("G1", n == 47, "Bestaende mit frei + gestakt > 0: %d (V1 47)" % n)
o = sorted(s for (s,) in c.execute("SELECT symbol FROM hebel_positions WHERE geschlossen_am IS NULL"))
pruefe("G2", o == ["BTC", "ETH"], "offen (geschlossen_am leer): %s" % o)
kreis = ["ASTER", "BEAMX", "BNB", "BRETT", "CAT", "HYPE", "KAS", "QNT", "SUPRA", "TURBO", "VSN"]
ohne = []
for s in kreis + ["BIO", "TAO", "CC"]:
    r = requests.get("https://api.upbit.com/v1/ticker", params={"markets": "KRW-%s" % s}, timeout=30)
    ok = r.status_code == 200 and isinstance(r.json(), list) and len(r.json()) > 0
    if not ok:
        ohne.append(s)
    time.sleep(0.15)
pruefe("G3", sorted(ohne) == sorted(kreis), "ohne KRW-Kurs: %s (erwartet die 11 des Kreises; BIO/TAO/CC mit Kurs)" % ", ".join(sorted(ohne)))
os.chdir(os.path.dirname(os.path.dirname(HIER)))
import c2_messung as C2  # noqa: E402
E = C2.ereignisse()
nu = int((E.art == "C2-b Upbit-Listing").sum())
pruefe("G4", nu == 137, "Upbit-Listings ueber c2_messung.ereignisse: %d (V4 137)" % nu)
print("\n%d von %d gleich" % (sum(ERG), len(ERG)))
