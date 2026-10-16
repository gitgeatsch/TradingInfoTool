"""P11b VORANALYSE (16.10.2026): Hebelpositionen als BUCH JE SYMBOL aus der NEUEN Bitpanda-Schnittstelle (/v1/operations).

    python Basisinfos/Rechenkern_02_10/p11b_voranalyse.py <nb_bitpanda_buchungen_voll_*.json> <tradinginfotool_*.db.gz>
        > Basisinfos/Rechenkern_02_10/p11b_voranalyse.txt

Nur lesend: die JSON-Datei aus `nb_bitpanda_buchungen_roh.py --voll` und eine Wegwerf-Kopie der NB-Sicherung (Katalog, alte
hebel_positions, Wallet-Salden). Schreibt nichts ausser der Ausgabe.

DAS BUCH (aus dem Aufbau der Vorgaenge, 16.10. gesehen):
    open_long         Kredit-Wallet OUTGOING k (Kredit), Margin-Wallet INCOMING q zum Kurs r  -> Menge +q, Kredit +k, Kosten +q*r
    close_long /      Margin-Wallet: Gebuehr, Verkauf (zahlt den Kredit), Rest als Coin ins Spot-Wallet (= dein Eigenkapital);
    liquidation_long  Kredit-Wallet INCOMING k  -> Kredit -k, Menge = Saldo danach, Kosten anteilig zur Restmenge
    Lebenszyklus      von Margin-Saldo 0 -> > 0 bis wieder 0 (je Symbol); Liquidation = Vorgangstyp liquidation_long (ausdruecklich)

PRUEFUNGEN (Gegenprobe mit unabhaengigen Groessen):
  G1  Menge aus den Bewegungen (Zugang - Abgang) = Saldo danach, bei JEDEM Vorgang
  G2  Summe der Symbol-Kredite = -Saldo des Kredit-Wallets, bei JEDEM Vorgang mit Kreditbuchung; am Ende gegen die Sicherung
  G3  Rueckzahlung bei Teilschliessung anteilig zur Menge (Kredit * q / Q)? - Auskunft, wie Bitpanda tilgt
  G4  offene Positionen heute = Margin-Wallets der Sicherung (BTC 0,01141097, Kredit 560)
  G5  Liquidationen: ausdruecklich getaggt gegen die alte Erkennung (Gebuehren-Anomalie, Befund 2.679: 3 von 7 uebersehen)
  G6  Lebenszyklen gegen die alte hebel_positions: wie viele gleich, wie viele weichen ab - und warum
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

KREDIT_ASSET = "1ef96b30-6729-657a-aa72-7bae1036a7b1"         # EURCV (Kredit-Wallet)
TOL = 1e-9

d = json.load(open(sys.argv[1], encoding="utf-8"))
T = tempfile.mkdtemp(prefix="p11b_")
kopie = os.path.join(T, "prod.db")
with gzip.open(sys.argv[2], "rb") as f, open(kopie, "wb") as g:
    shutil.copyfileobj(f, g, 1 << 24)
c = sqlite3.connect("file:%s?mode=ro" % kopie.replace("\\", "/"), uri=True)
SYM = {}
for aid, s in c.execute("SELECT asset_id, symbol FROM bitpanda_katalog"):
    SYM.setdefault(aid, s)
alt = [dict(zip([x[0] for x in c.execute("SELECT * FROM hebel_positions LIMIT 0").description], r))
       for r in c.execute("SELECT * FROM hebel_positions")]
wallet = {(a, o): s for a, o, s in c.execute("SELECT asset_id, wallet_owner, saldo FROM bitpanda_wallet_saldo "
                                             "WHERE wallet_owner IN ('margin-trading','margin-trading-credit')")}
c.close()

ops = [o for o in d["vorgaenge"] if str(o.get("operation_type", "")).startswith("margin_trading")]


def zeit(o):
    return min(t["credited_at"] for t in o["transactions"])


ops.sort(key=lambda o: (zeit(o), o["operation_id"]))
print("P11b VORANALYSE · %d Margin-Vorgaenge %s bis %s (Datei %s, %s)\n" % (len(ops), zeit(ops[0])[:10], zeit(ops[-1])[:10],
                                                                         os.path.basename(sys.argv[1]), d.get("von")))

stand = defaultdict(lambda: {"menge": 0.0, "kredit": 0.0, "kosten": 0.0, "auf": None, "vorgaenge": 0})
zyklen, g1_fehl, g2_fehl, g2_n, g3 = [], [], [], 0, []
for o in ops:
    typ = o["operation_type"]
    tx = o["transactions"]
    marg = [t for t in tx if t["wallet_owner"] == "margin-trading"]
    if not marg:
        continue
    aid = marg[0].get("asset_id")
    s = SYM.get(aid, aid[:8])
    b = stand[s]
    vor = b["menge"]
    zu = sum(float(t["asset_amount"]["value"]) for t in marg if t["flow"] == "INCOMING")
    ab = sum(float(t["asset_amount"]["value"]) for t in marg if t["flow"] == "OUTGOING")
    # Saldo danach: die LETZTE Margin-Buchung des Vorgangs in Antwortreihenfolge ist nicht sicher die letzte - der Endsaldo ist
    # vor + zu - ab; G1 prueft, dass genau dieser Wert unter den 'Saldo danach' der Buchungen vorkommt
    nach = vor + zu - ab
    salden = [float(t["asset_balance_after"]["value"]) for t in marg if t.get("asset_balance_after")]
    if not any(abs(x - nach) <= max(TOL, 1e-7 * max(1.0, abs(x))) for x in salden):
        g1_fehl.append((s, typ, zeit(o), vor, nach, salden))
    kr = [t for t in tx if t["wallet_owner"] == "margin-trading-credit"]
    dk = sum(float(t["asset_amount"]["value"]) * (1 if t["flow"] == "OUTGOING" else -1) for t in kr)   # + = neuer Kredit
    if typ == "margin_trading_open_long":
        rate = next((float(t["trade"]["rate"]) for t in marg if t.get("trade") and t["flow"] == "INCOMING"), None)
        if b["menge"] <= TOL:
            b.update(auf=zeit(o), kredit=0.0, kosten=0.0)
        b["kosten"] += zu * (rate or 0.0)
        b["kredit"] += dk
    else:
        if b["menge"] > TOL and dk < 0:
            soll = b["kredit"] * (vor - max(nach, 0.0)) / vor
            g3.append((s, zeit(o), -dk, soll, nach <= TOL))
        b["kredit"] += dk
        b["kosten"] *= (max(nach, 0.0) / vor) if vor > TOL else 0.0
    b["menge"] = max(nach, 0.0)
    b["vorgaenge"] += 1
    if kr:
        g2_n += 1
        ges = sum(x["kredit"] for x in stand.values())
        kw = float(kr[-1]["asset_balance_after"]["value"]) if kr[-1].get("asset_balance_after") else None
        saldi = [float(t["asset_balance_after"]["value"]) for t in kr if t.get("asset_balance_after")]
        if not any(abs(ges + x) <= 0.02 for x in saldi):
            g2_fehl.append((s, typ, zeit(o), ges, saldi))
    if typ != "margin_trading_open_long" and b["menge"] <= TOL and b["auf"]:
        zyklen.append({"symbol": s, "auf": b["auf"], "zu": zeit(o), "liquidiert": typ == "margin_trading_liquidation_long",
                       "vorgaenge": b["vorgaenge"], "rest_kredit": b["kredit"]})
        b.update(auf=None, kredit=0.0, kosten=0.0, vorgaenge=0)

print("G1 Menge = Saldo danach bei jedem Vorgang: %d von %d Abweichungen %s" % (len(g1_fehl), len(ops), g1_fehl[:3] or ""))
print("G2 Summe Symbol-Kredite = -Kredit-Wallet: %d von %d Vorgaengen mit Kreditbuchung weichen ab (> 2 ct) %s"
      % (len(g2_fehl), g2_n, [(x[0], x[1][15:], x[2][:16], round(x[3], 2), x[4]) for x in g2_fehl[:4]] or ""))
teil = [x for x in g3 if not x[4]]
voll = [x for x in g3 if x[4]]
gleich = [x for x in teil if abs(x[2] - x[3]) <= max(0.02, 0.002 * x[3])]
print("G3 Tilgung bei TEILschliessung anteilig zur Menge: %d von %d (Vollschliessungen %d: Rest-Kredit danach max %.2f EUR)"
      % (len(gleich), len(teil), len(voll), max([abs(z["rest_kredit"]) for z in zyklen] or [0])))
for x in [x for x in teil if x not in gleich][:5]:
    print("     abweichend: %s %s getilgt %.2f, anteilig %.2f" % (x[0], x[1][:16], x[2], x[3]))

offen = {s: b for s, b in stand.items() if b["menge"] > TOL}
kw = -sum(v for (a, o), v in wallet.items() if o == "margin-trading-credit")
print("\nG4 offen heute (Buch): %s · Kredit-Summe %.2f EUR" % (
    ", ".join("%s Menge %.8g, Kredit %.2f, Einstand %.2f, seit %s" % (s, b["menge"], b["kredit"], b["kosten"] / b["menge"], b["auf"][:16])
              for s, b in offen.items()), sum(b["kredit"] for b in offen.values())))
ws = {SYM.get(a, a[:8]): v for (a, o), v in wallet.items() if o == "margin-trading" and abs(v) > TOL}
print("   Sicherung (Wallets): %s · Kredit %.2f EUR" % (ws, kw))
ok4 = set(ws) == set(offen) and all(abs(ws[s] - offen[s]["menge"]) <= TOL for s in ws) and abs(kw - sum(b["kredit"] for b in offen.values())) <= 0.02
print("   -> %s" % ("GLEICH" if ok4 else "ABWEICHUNG"))

liq = [z for z in zyklen if z["liquidiert"]]
print("\nG5 Liquidationen ausdruecklich: %d · %s" % (len(liq), ", ".join("%s %s" % (z["symbol"], z["zu"][:10]) for z in liq)))
alt_liq = [a for a in alt if str(a.get("status")) == "wahrscheinlich_liquidiert"]
print("   alte Erkennung (Gebuehren-Anomalie): %d · %s" % (len(alt_liq), ", ".join("%s %s" % (a["symbol"], str(a.get("geschlossen_am"))[:10]) for a in alt_liq)))
treffer = [z for z in liq if any(a["symbol"] == z["symbol"] and str(a.get("geschlossen_am"))[:10] == z["zu"][:10] for a in alt_liq)]
print("   davon von der alten Erkennung gefunden: %d von %d" % (len(treffer), len(liq)))

print("\nG6 Lebenszyklen: Buch %d geschlossen + %d offen · alte hebel_positions %d Zeilen (%d offen)" % (
    len(zyklen), len(offen), len(alt), sum(1 for a in alt if a.get("geschlossen_am") is None)))
alt_je = defaultdict(list)
for a in alt:
    alt_je[a["symbol"]].append(a)
buch_je = defaultdict(list)
for z in zyklen:
    buch_je[z["symbol"]].append(z)
gleich6 = 0
for s in sorted(set(alt_je) | set(buch_je)):
    na, nb = len(alt_je[s]), len(buch_je[s]) + (1 if s in offen else 0)
    gleich6 += na == nb
print("   Symbole mit gleicher Zahl an Lebenszyklen: %d von %d" % (gleich6, len(set(alt_je) | set(buch_je))))
print("   je Symbol (alt / Buch): " + " · ".join("%s %d/%d" % (s, len(alt_je[s]), len(buch_je[s]) + (1 if s in offen else 0))
                                               for s in sorted(set(alt_je) | set(buch_je)) if len(alt_je[s]) != len(buch_je[s]) + (1 if s in offen else 0))[:1500])
print("   Vorgaenge je Lebenszyklus: Median %d, max %d" % (sorted(z["vorgaenge"] for z in zyklen)[len(zyklen) // 2] if zyklen else 0,
                                                       max([z["vorgaenge"] for z in zyklen] or [0])))
wegwerf.aufraeumen(T)
