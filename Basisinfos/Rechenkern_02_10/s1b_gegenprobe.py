"""S1b GEGENPROBE (17.10.2026), zweiter Weg: Lebenszyklen aus importer.hebel_buch.lebenszyklen (P11b), Ergebnis BRUTTO gerechnet -
alles, was beim Abgang zum Kurs bewertet herausgeht (verkauft + Uebertrag), minus allem, was bei der Eroeffnung in EUR hineinging.
Der Kredit hebt sich auf (Tilgung = Kredit, P2). Muss je geschlossenem Lebenszyklus der Voranalyse gleichen. Nur lesend (Wegwerf-Kopie).

    python Basisinfos/Rechenkern_02_10/s1b_gegenprobe.py <Wegwerf-Kopie tradinginfotool.db> <s1b_voranalyse.txt>
"""
import json
import os
import re
import sqlite3
import sys

WURZEL = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, WURZEL)
import importer.hebel_buch as HB  # noqa: E402

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:  # noqa: BLE001
    pass
EUR = "b88b8466-efe3-11eb-b56f-0691764446a7"
c = sqlite3.connect(sys.argv[1])
zy = HB.lebenszyklen(c)
kat = {}                                         # ⚠️ KORREKTUR 17.10.: ein Symbol kann MEHRERE Asset-IDs haben (ETH, SUI, SEI, HYPE ...)
for _aid, _sym in c.execute("SELECT asset_id, symbol FROM bitpanda_katalog").fetchall():
    kat.setdefault(_sym, set()).add(_aid)
ops = c.execute("SELECT zeit, typ, asset_id, roh FROM hebel_buch_vorgang ORDER BY zeit, operation_id").fetchall()
c.close()
soll = {}
for z_ in open(sys.argv[2], encoding="utf-8"):
    m = re.match(r"\s+(\S+)\s+(\d{4}-\d\d-\d\d \d\d:\d\d) (\d{4}-\d\d-\d\d \d\d:\d\d) \S+\s+[\d.]+\s+[\d.]+\s+[\d.]+\s+([+-][\d.]+)", z_)
    if m:
        soll[(m.group(1), m.group(2))] = float(m.group(4))
gleich, n = 0, 0
for z in zy:
    if not z.get("zu"):
        continue
    aid = kat.get(z["symbol"])
    a, e = str(z["auf"]).replace("T", " ")[:19], str(z["zu"]).replace("T", " ")[:19]
    rein = raus = 0.0
    for zeit, typ, ai, roh in ops:
        zt = zeit.replace("T", " ")[:19]
        if ai not in aid or zt < a or zt > e:
            continue
        tx = json.loads(roh)["transactions"]
        if typ == "margin_trading_open_long":
            rein += sum(float(x["asset_amount"]["value"]) for x in tx if x.get("currency_id") == EUR and x.get("flow") == "OUTGOING"
                        and x.get("transaction_type") == "buy")
        else:
            rate = next(float(x["trade"]["rate"]) for x in tx if x.get("transaction_type") == "sell" and x.get("asset_id") == ai)
            raus += rate * sum(float(x["asset_amount"]["value"]) for x in tx if x.get("asset_id") == ai and x.get("flow") == "OUTGOING"
                               and x.get("transaction_type") in ("sell", "transfer"))
            raus -= sum(float(x["asset_amount"]["value"]) for x in tx if x.get("wallet_owner") == "margin-trading-credit" and x.get("flow") == "INCOMING")
    kredit = 0.0
    for zeit, typ, ai, roh in ops:
        zt = zeit.replace("T", " ")[:19]
        if ai in aid and a <= zt <= e and typ == "margin_trading_open_long":
            kredit += sum(float(x["asset_amount"]["value"]) for x in json.loads(roh)["transactions"] if x.get("wallet_owner") == "margin-trading-credit")
    erg = raus - (rein - kredit)
    k = (z["symbol"], a[:16])
    n += 1
    ok = k in soll and abs(soll[k] - erg) < 0.011
    gleich += int(ok)
    if not ok:
        print("   ABWEICHUNG %s %s: zweiter Weg %+.2f, Voranalyse %s" % (k[0], k[1], erg, soll.get(k)))
print("S1b GEGENPROBE: %d von %d geschlossenen Lebenszyklen gleich (auf den Cent) -> %s" % (gleich, n, "GLEICH" if gleich == n and n else "ABWEICHUNG"))
