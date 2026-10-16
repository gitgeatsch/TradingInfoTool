"""P11b GEGENPROBE (16.10.2026): die Lebenszyklen des Buchs auf einem ANDEREN Weg - nur aus den von Bitpanda gemeldeten Salden.

    python Basisinfos/Rechenkern_02_10/p11b_gegenprobe.py <nb_bitpanda_buchungen_voll_*.json> <tradinginfotool_*.db.gz>

Anders als ``importer.hebel_buch``: keine Summen von Zu- und Abgang, sondern je Vorgang der KLEINSTE bzw. GROESSTE 'Saldo danach' der
Margin-Wallet-Buchungen (Schliessen: der Endsaldo ist der kleinste, Eroeffnen: der groesste); Symbol ueber die Asset-ID im Katalog,
Lebenszyklus = Endsaldo 0. Kredit je Lebenszyklus aus den Kredit-Wallet-Buchungen. Verglichen werden Symbol, Eroeffnung,
Schliessung, liquidiert, und fuer den offenen Menge und Kredit.

  K1  dieselben Lebenszyklen (Symbol, Eroeffnung, Schliessung, liquidiert) - alle 38
  K2  der offene: Menge und Kredit gleich, und gleich dem Wallet der Sicherung
  K3  jeder geschlossene Lebenszyklus endet mit Kredit 0 (Bitpanda tilgt vollstaendig)
"""
import gzip
import json
import os
import shutil
import sqlite3
import sys
import tempfile
from collections import defaultdict

WURZEL = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(WURZEL)
sys.path.insert(0, WURZEL)
sys.stdout.reconfigure(encoding="utf-8")
import wegwerf  # noqa: E402,F401

import importer.hebel_buch as HB  # noqa: E402

ERG = []


def pruefe(k, ok, text):
    ERG.append(bool(ok))
    print("%-4s %-9s %s" % (k, "bestanden" if ok else "FEHLER", text))


OPS = json.load(open(sys.argv[1], encoding="utf-8"))["vorgaenge"]
T = tempfile.mkdtemp(prefix="p11bg_")
p = os.path.join(T, "k.db")
with gzip.open(sys.argv[2], "rb") as f, open(p, "wb") as g:
    shutil.copyfileobj(f, g, 1 << 24)
c = sqlite3.connect(p)
SYM = {}
for aid, s in c.execute("SELECT asset_id, symbol FROM bitpanda_katalog"):
    SYM.setdefault(aid, s)
wallet = {SYM.get(a): v for a, o, v in c.execute("SELECT asset_id, wallet_owner, saldo FROM bitpanda_wallet_saldo WHERE wallet_owner='margin-trading'") if abs(v) > 1e-9}
kw = -sum(v for (v,) in c.execute("SELECT saldo FROM bitpanda_wallet_saldo WHERE wallet_owner='margin-trading-credit'"))

# eigener Weg
m = sorted((o for o in OPS if str(o.get("operation_type", "")).startswith("margin_trading")),
           key=lambda o: (min(t["credited_at"] for t in o["transactions"]), o["operation_id"]))
offen, kredit, zyklen = {}, defaultdict(float), []
for o in m:
    marg = [t for t in o["transactions"] if t["wallet_owner"] == "margin-trading"]
    s = SYM.get(marg[0]["asset_id"])
    saldi = [float(t["asset_balance_after"]["value"]) for t in marg]
    eroeffnen = o["operation_type"] == "margin_trading_open_long"
    end = max(saldi) if eroeffnen else min(saldi)
    zeit = min(t["credited_at"] for t in o["transactions"])
    kredit[s] += sum(float(t["asset_amount"]["value"]) * (1 if t["flow"] == "OUTGOING" else -1)
                     for t in o["transactions"] if t["wallet_owner"] == "margin-trading-credit")
    if eroeffnen and s not in offen:
        offen[s] = zeit
    if not eroeffnen and end == 0.0 and s in offen:
        zyklen.append((s, HB._iso(offen.pop(s)), HB._iso(zeit), o["operation_type"] == "margin_trading_liquidation_long", round(kredit[s], 6)))
        kredit[s] = 0.0
eigen = sorted(z[:4] for z in zyklen) + sorted((s, HB._iso(t), None, False) for s, t in offen.items())

# das Modul
e = HB.sync(c, "x", hole=lambda k, seit=None: (OPS, True))
modul = sorted((r[0], r[1], r[2], r[3] == "liquidiert") for r in c.execute("SELECT symbol, eroeffnet_am, geschlossen_am, status FROM hebel_positions"))
modul = sorted((s, a, z, l) for s, a, z, l in modul)
eigen = sorted(eigen, key=lambda x: (x[0], x[1]))
modul = sorted(modul, key=lambda x: (x[0], x[1]))
pruefe("K1", eigen == modul, "Lebenszyklen eigen %d / Modul %d · gleich %s%s" % (
    len(eigen), len(modul), eigen == modul, "" if eigen == modul else " · erste Abweichung %s" % next(
        ((a, b) for a, b in zip(eigen, modul) if a != b), None)))
o_mod = c.execute("SELECT symbol, positionsmenge, kreditbetrag_eur FROM hebel_positions WHERE status='offen'").fetchall()
letzt = {}
for o in m:
    for t in o["transactions"]:
        if t["wallet_owner"] == "margin-trading":
            letzt[SYM.get(t["asset_id"])] = float(t["asset_balance_after"]["value"])
ok2 = (len(o_mod) == 1 and o_mod[0][0] in offen and abs(o_mod[0][1] - wallet.get(o_mod[0][0], -1)) < 1e-12
       and abs(o_mod[0][2] - kredit[o_mod[0][0]]) < 1e-6 and abs(o_mod[0][2] - kw) < 0.01)
pruefe("K2", ok2, "offen Modul %s · eigener Kredit %.2f · Wallet Menge %s, Kredit %.2f" % (
    [tuple(x) for x in o_mod], kredit[o_mod[0][0]] if o_mod else -1, wallet, kw))
pruefe("K3", all(abs(z[4]) < 0.01 for z in zyklen), "Kredit nach jeder Vollschliessung: max %.4f EUR ueber %d Lebenszyklen" % (
    max(abs(z[4]) for z in zyklen), len(zyklen)))
c.close()
wegwerf.aufraeumen(T)
print("\n%d von %d bestanden" % (sum(ERG), len(ERG)))
