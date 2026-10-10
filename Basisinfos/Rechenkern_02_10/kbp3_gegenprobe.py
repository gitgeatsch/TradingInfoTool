"""Gegenprobe K-BP-3 (10.10.2026, Schritt7 Par. 23.37) - eigener Rechenweg, nur lesend, kein Netz, keine DB.

    python Basisinfos/Rechenkern_02_10/kbp3_gegenprobe.py

  G1 ROHBUCHUNGEN aus der Datei (nb_bitpanda_buchungen_roh_9900K.txt): Endstand der Spot-Wallet EURCV mit eigener Sortierung
     (datetime, order_id) = 296,04291657; der Kredit -2.600; die ETH-Hebel-Menge 0,89636371
  G2 `zeit_einheitlich` an 20.000 Zufallszeitpunkten (mit/ohne Millisekunden, Offsets): Textordnung = Zeitordnung, Rueckweg verlustfrei auf ms
  G3 die ALTE Logik (Text, `>=`) ergibt aus denselben Zeilen 696,04 - genau der Befund vom 10.10.
"""
import io
import os
import random
import re
import sys
from datetime import datetime, timedelta, timezone

WURZEL = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, WURZEL)
import importer.bitpanda_bestand as BB  # noqa: E402

ok = n = 0


def pruefe(name, gut, info):
    global ok, n
    n += 1; ok += bool(gut)
    print("%-3s %s  %s" % (name, "gleich" if gut else "ABWEICHUNG", info), flush=True)


roh = io.open("K:/My Drive/Claude_Austauschordner/Notebook_Analysedaten/nb_bitpanda_buchungen_roh_9900K.txt", encoding="utf-8").read()
zeilen = []
for m in re.finditer(r"\| (\w+|\?)\s+\| ([\w-]+)\s+\| (\S+) \| Menge \S+ \| Saldo danach (\S+) \| (\{.*)", roh):
    nr = int(re.search(r'"order_id": "(\d+)"', m.group(5)).group(1))
    zeilen.append((m.group(1), m.group(2), m.group(3), float(m.group(4)), nr))
eigen = {}
for asset, wallet, zeit, saldo, nr in zeilen:
    t = datetime.fromisoformat(zeit.replace("Z", "+00:00"))
    k = (asset, wallet)
    if k not in eigen or (t, nr) >= eigen[k][0]:
        eigen[k] = ((t, nr), saldo)
pruefe("G1", abs(eigen[("EURCV", "shared-default")][1] - 296.04291657) < 1e-9 and eigen[("EURCV", "margin-trading-credit")][1] == -2600.0
       and abs(eigen[("ETH", "margin-trading")][1] - 0.89636371) < 1e-12,
       "%d Zeilen gelesen · Spot EURCV %.8f · Kredit %.0f · ETH-Hebel %.8f" % (len(zeilen), eigen[("EURCV", "shared-default")][1],
                                                                            eigen[("EURCV", "margin-trading-credit")][1], eigen[("ETH", "margin-trading")][1]))
rnd = random.Random(20261010)
fx = 0
basis = datetime(2026, 10, 9, 8, 29, 58, tzinfo=timezone.utc)
for _ in range(20000):
    a = basis + timedelta(milliseconds=rnd.randint(-5000, 5000))
    b = basis + timedelta(milliseconds=rnd.randint(-5000, 5000))
    def schreib(t):
        art = rnd.random()
        if t.microsecond == 0 and art < 0.5:
            return t.strftime("%Y-%m-%dT%H:%M:%SZ")
        if art < 0.75:
            return t.strftime("%Y-%m-%dT%H:%M:%S.") + "%03dZ" % (t.microsecond // 1000)
        return t.astimezone(timezone(timedelta(hours=2))).isoformat(timespec="milliseconds")
    sa, sb = BB.zeit_einheitlich(schreib(a)), BB.zeit_einheitlich(schreib(b))
    fx += (sa < sb) != (a < b) or (sa == sb) != (a == b) or datetime.fromisoformat(sa.replace("Z", "+00:00")) != a
pruefe("G2", fx == 0, "20.000 Paare, Abweichungen %d" % fx)
alt = {}
for asset, wallet, zeit, saldo, nr in zeilen:
    k = (asset, wallet)
    if k not in alt or zeit >= alt[k][1]:
        alt[k] = (saldo, zeit)
pruefe("G3", abs(alt[("EURCV", "shared-default")][0] - 696.04291657) < 1e-9, "alte Logik (Text) ergibt %.8f - der Befund" % alt[("EURCV", "shared-default")][0])
print("\n%d von %d gleich" % (ok, n))
