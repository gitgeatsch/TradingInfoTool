"""O21 Stufe 1b VORANALYSE (17.10.2026): das Ergebnis echter Hebel-Trades in EUR aus den Bitpanda-Buchungen. Nur lesend.

    python Basisinfos/Rechenkern_02_10/s1b_voranalyse.py <Wegwerf-Kopie tradinginfotool.db>

Quelle: ``hebel_buch_vorgang.roh`` (die Transaktionen je Vorgang aus /v1/operations, P11b) - keine neue Datenquelle.

AUFBAU EINES VORGANGS (gelesen an ETH/BTC 09.-15.10. und der Liquidation TAO 21.11.2025):
  open_long   Kredit kommt als EURCV aus 'margin-trading-credit' · EURCV -> EUR (eigenes Geld + Kredit) · EUR -> Coin ins Wallet
              'margin-trading'. EIGENKAPITAL = EUR-Kauf - Kredit
  close_long  Gebuehr in Coin ('fee') · Coin -> EUR in Hoehe des Kreditanteils · EUR -> EURCV zurueck an 'margin-trading-credit' ·
  liquidation der REST des Coins als 'transfer' ins Spot-Wallet 'shared-default'. RUECKFLUSS = Rest x Verkaufskurs (+ EUR ueber der Tilgung)

  Ergebnis je Abgang = Rueckfluss - anteiliges Eigenkapital (Anteil = Abgang / Menge davor) · Kosten = Gebuehr x Verkaufskurs

  P1  Mengen: je Abgang  Abgang = verkauft + Gebuehr + Uebertrag   (exakt)
  P2  Kredit: je Lebenszyklus Summe Tilgung = Summe Kredit         (P11b G2)
  P3  EUR: je Eroeffnung EUR-Kauf = EURCV-Verkauf, Kredit = kredit_aenderung
  P4  Verkauf: verkaufte Menge x Kurs = EUR-Eingang (auf den Cent)
  A   Gebuehr je Tag in % des Positionswerts (ist es Finanzierung oder Handelsgebuehr?)
"""
import json
import os
import sqlite3
import sys
from datetime import datetime

WURZEL = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, WURZEL)
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:  # noqa: BLE001
    pass
P = sys.argv[1]
EUR_FIAT = "b88b8466-efe3-11eb-b56f-0691764446a7"
TOL = 1e-9


def f(x):
    return float(x or 0)


c = sqlite3.connect("file:%s?mode=ro" % P.replace("\\", "/"), uri=True)
kat = dict(c.execute("SELECT asset_id, symbol FROM bitpanda_katalog").fetchall())
ops = c.execute("SELECT zeit, typ, asset_id, zugang, abgang, kredit_aenderung, roh FROM hebel_buch_vorgang ORDER BY zeit, operation_id").fetchall()
c.close()
fehler = {"P1": [], "P2": [], "P3": [], "P4": []}
stand, zyklen, gebuehr_tag = {}, [], []
for zeit, typ, aid, zu, ab, kd, roh in ops:
    s = kat.get(aid, aid[:8])
    tx = json.loads(roh)["transactions"]
    t = datetime.fromisoformat(zeit.replace("Z", "")[:19])

    def summe(asset, owner, flow, typ_=None):
        return sum(f(x["asset_amount"]["value"]) for x in tx if (x.get("asset_id") or x.get("currency_id")) == asset
                   and x.get("wallet_owner") == owner and x.get("flow") == flow and (typ_ is None or x.get("transaction_type") == typ_))
    b = stand.get(s)
    if typ == "margin_trading_open_long":
        eur_kauf = summe(EUR_FIAT, "shared-default", "OUTGOING", "buy")
        kredit = sum(f(x["asset_amount"]["value"]) for x in tx if x.get("wallet_owner") == "margin-trading-credit" and x.get("flow") == "OUTGOING")
        eurcv_verk = sum(f(x["asset_amount"]["value"]) for x in tx if x.get("transaction_type") == "sell" and x.get("flow") == "OUTGOING"
                         and x.get("wallet_owner") == "shared-default")
        if abs(eur_kauf - eurcv_verk) > 0.005 or abs(kredit - f(kd)) > 0.005:
            fehler["P3"].append((zeit[:16], s, eur_kauf, eurcv_verk, kredit, kd))
        if b is None or b["menge"] <= TOL:
            b = stand[s] = {"symbol": s, "auf": t, "menge": 0.0, "ek": 0.0, "kredit": 0.0, "kredit_summe": 0.0, "tilgung": 0.0,
                            "rueck": 0.0, "kosten": 0.0, "ergebnis": 0.0, "ek_summe": 0.0, "abgaenge": 0, "liquidiert": False, "pos_eur": 0.0}
        b["menge"] += f(zu)
        b["ek"] += eur_kauf - kredit
        b["ek_summe"] += eur_kauf - kredit
        b["kredit"] += kredit
        b["kredit_summe"] += kredit
        b["pos_eur"] += eur_kauf
        b["letzte_auf"] = t
        continue
    if b is None or b["menge"] <= TOL:
        continue
    coin = aid
    fee = sum(f(x["asset_amount"]["value"]) for x in tx if x.get("transaction_type") == "fee" and (x.get("asset_id") == coin))
    verk = sum(f(x["asset_amount"]["value"]) for x in tx if x.get("transaction_type") == "sell" and x.get("asset_id") == coin)
    rate = next((f(x["trade"]["rate"]) for x in tx if x.get("transaction_type") == "sell" and x.get("asset_id") == coin and x.get("trade")), 0.0)
    eur_ein = summe(EUR_FIAT, "shared-default", "INCOMING", "sell")
    tilg = sum(f(x["asset_amount"]["value"]) for x in tx if x.get("wallet_owner") == "margin-trading-credit" and x.get("flow") == "INCOMING")
    uebertrag = summe(coin, "shared-default", "INCOMING", "transfer")
    if abs(f(ab) - (verk + fee + uebertrag)) > 1e-8:
        fehler["P1"].append((zeit[:16], s, ab, verk, fee, uebertrag))
    if abs(verk * rate - eur_ein) > 0.011:
        fehler["P4"].append((zeit[:16], s, verk * rate, eur_ein))
    anteil = min(f(ab) / b["menge"], 1.0)
    ek_anteil = b["ek"] * anteil
    rueck = uebertrag * rate + (eur_ein - tilg)
    kosten = fee * rate
    tage = max((t - b["letzte_auf"]).total_seconds() / 86400, 1 / 24)
    gebuehr_tag.append((s, zeit[:16], kosten / max(f(ab) * rate, 1e-9) / tage, tage))
    b["rueck"] += rueck
    b["kosten"] += kosten
    b["ergebnis"] += rueck - ek_anteil
    b["ek"] -= ek_anteil
    b["tilgung"] += tilg
    b["menge"] = max(b["menge"] - f(ab), 0.0)
    b["abgaenge"] += 1
    b["liquidiert"] |= typ == "margin_trading_liquidation_long"
    if b["menge"] <= TOL:
        b["zu"] = t
        zyklen.append(b)
        if abs(b["tilgung"] - b["kredit_summe"]) > 0.01:
            fehler["P2"].append((s, b["auf"], b["kredit_summe"], b["tilgung"]))
        del stand[s]
offen = list(stand.values())
print("S1b VORANALYSE · Ergebnis echter Hebel-Trades in EUR aus den Bitpanda-Buchungen · %d Vorgaenge\n" % len(ops))
for k, v in fehler.items():
    print("%s %s %s" % (k, "✔ 0 Abweichungen" if not v else "⛔ %d Abweichungen" % len(v), "" if not v else v[:4]))
print("\nLEBENSZYKLEN (geschlossen %d, offen %d):" % (len(zyklen), len(offen)))
print("   %-8s %-16s %-16s %-11s %10s %10s %9s %10s %8s" % ("Asset", "auf", "zu", "Status", "Eigenkap.", "Rueckfluss", "Kosten", "Ergebnis", "auf EK"))
ges = {"ek": 0.0, "erg": 0.0, "kosten": 0.0}
for b in zyklen:
    st = "liquidiert" if b["liquidiert"] else "geschlossen"
    print("   %-8s %-16s %-16s %-11s %10.2f %10.2f %9.2f %+10.2f %+7.1f%%" % (
        b["symbol"], b["auf"].strftime("%Y-%m-%d %H:%M"), b["zu"].strftime("%Y-%m-%d %H:%M"), st, b["ek_summe"], b["rueck"], b["kosten"],
        b["ergebnis"], 100 * b["ergebnis"] / b["ek_summe"] if b["ek_summe"] else 0))
    ges["ek"] += b["ek_summe"]
    ges["erg"] += b["ergebnis"]
    ges["kosten"] += b["kosten"]
for b in offen:
    print("   %-8s %-16s %-16s %-11s %10.2f %10.2f %9.2f %+10.2f (realisiert aus Teilschliessungen; Rest offen: %.8f, EK %.2f)" % (
        b["symbol"], b["auf"].strftime("%Y-%m-%d %H:%M"), "offen", "offen", b["ek_summe"], b["rueck"], b["kosten"], b["ergebnis"], b["menge"], b["ek"]))
print("\n   SUMME geschlossene: Eigenkapital %.2f EUR · Ergebnis %+.2f EUR (%+.1f %%) · Kosten (Gebuehr in Coin) %.2f EUR" % (
    ges["ek"], ges["erg"], 100 * ges["erg"] / ges["ek"] if ges["ek"] else 0, ges["kosten"]))
gt = sorted(x[2] for x in gebuehr_tag if x[3] >= 0.5)
if gt:
    print("\nA  Gebuehr je Tag in %% des Positionswerts (Abgaenge mit >= 12 h): Median %.3f %%, 10./90. Perzentil %.3f / %.3f %% (n %d)" % (
        100 * gt[len(gt) // 2], 100 * gt[len(gt) // 10], 100 * gt[9 * len(gt) // 10], len(gt)))
    kurz = [x for x in gebuehr_tag if x[3] < 0.5]
    if kurz:
        print("   Abgaenge unter 12 h: %d · Gebuehr je Abgang im Median %.3f %% des Werts" % (
            len(kurz), 100 * sorted(x[2] * x[3] for x in kurz)[len(kurz) // 2]))
