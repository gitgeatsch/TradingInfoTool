"""P11c Hebelfuehrung folgt dem Wallet-Abgleich (16.10.2026) - Pruefstand am SEITENEFFEKT an einer Wegwerf-Kopie der NB-Sicherung.

    python Basisinfos/Rechenkern_02_10/p11c_pruefstand.py <tradinginfotool_*.db.gz> > Basisinfos/Rechenkern_02_10/p11c_pruefstand.txt

Anlass (Nutzer 16.10.): *"die Hebelfuehrung funktioniert nicht korrekt, ETH ist bereits geschlossen und BTC verringert"*. Echter Stand
in der Sicherung 16.10. 04:34: gespeichert ETH 0,18596404 / BTC 0,01496441 offen, Wallet ETH 0 / BTC 0,01141097, Kredit 560 EUR.

  H1  ECHTER FALL: ETH faellt heraus (laut_bitpanda_geschlossen = [ETH]), BTC mit Wallet-Menge und Wallet-Kredit (einzige offene
      Position); Hebel, Liquidation und Abstand UNABHAENGIG nachgerechnet (estimate_liquidation_price mit denselben Tagen)
  H2  keine Meldung fuer ETH: neue_meldungen/sammel_mail ohne ETH; der Lauf _hebelfuehrung_lauf (gestellter Versand) protokolliert
      'laut Bitpanda geschlossen' und mailt nicht fuer ETH
  H3  VERTRAUEN: Wallet-Stand aelter als die juengste Hebelbuchung -> NICHTS korrigiert (ETH bleibt, BTC gespeichert) und Hinweis
  H4  neue Position, die das Wallet noch nicht kennt (Eroeffnung nach dem Wallet-Stand) -> bleibt in der Fuehrung
  H5  zwei abweichende Positionen -> Kredit anteilig zur Menge, nicht der ganze Wallet-Kredit
  H6  wallet=False -> exakt die alte Rechnung (gespeicherte Werte)
  H7  Statusseite (betriebslage.hebel_fuehrung_jetzt): ETH als 'LAUT BITPANDA GESCHLOSSEN', BTC mit Wallet-Hinweis; Aggregat-Deckel
      zaehlt ETH nicht mehr
  H8  Produktions-DB am Desktop und die Sicherung unveraendert
"""
import gzip
import hashlib
import os
import shutil
import sqlite3
import sys
import tempfile
from datetime import datetime, timedelta, timezone

WURZEL = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(WURZEL)
sys.path.insert(0, WURZEL)
sys.stdout.reconfigure(encoding="utf-8")
import wegwerf  # noqa: E402,F401  Wegwerf-Ordner auf D: und Aufraeumen ohne stilles Scheitern (15.10.2026)

import agent.betriebslage as BL  # noqa: E402
import agent.hebelfuehrung as HF  # noqa: E402
from agent.krypto.hebel_risk_gate import estimate_liquidation_price  # noqa: E402
from database import db  # noqa: E402

ERG = []


def pruefe(k, ok, text):
    ERG.append(bool(ok))
    print("%-4s %-9s %s" % (k, "bestanden" if ok else "FEHLER", text))


def summe(p):
    if not os.path.exists(p):
        return None
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


QUELLE = sys.argv[1]
VOR = {"prod": summe(db.DB_PATH), "quelle": summe(QUELLE)}
T = tempfile.mkdtemp(prefix="p11c_")
BASIS = os.path.join(T, "basis.db")
with gzip.open(QUELLE, "rb") as f, open(BASIS, "wb") as g:
    shutil.copyfileobj(f, g, 1 << 24)


def kopie(name):
    p = os.path.join(T, name + ".db")
    shutil.copy(BASIS, p)
    c = sqlite3.connect(p)
    c.row_factory = sqlite3.Row
    return c


JETZT = datetime(2026, 10, 16, 4, 30, tzinfo=timezone.utc)
NAHE = 0.15

# ══ H1 echter Fall ═════════════════════════════════════════════════════════════════════════════════════════════════════════
c = kopie("h1")
roh = {p.symbol: p for p in db.get_open_hebel_positions(c)}
lage = HF.wallet_lage(c)
tr = HF.lade(c, jetzt=JETZT, nahe_grenze=NAHE)
zu = HF.laut_bitpanda_geschlossen(c)
btc = next((t for t in tr if t["symbol"] == "BTC"), None)
pb = roh["BTC"]
w = lage["zeilen"]["BTC"]["wallet"]
ein = pb.positionswert_eur / pb.positionsmenge
pw2 = ein * w
kr2 = -lage["kredit_wallet"]
L2 = pw2 / (pw2 - kr2)
tage = (JETZT - HF._zeit(pb.eroeffnet_am)).total_seconds() / 86400
from agent.entscheidungsrechnung import GRENZEN  # noqa: E402

liq = estimate_liquidation_price(ein, L2, "LONG", days_held=tage, sicherheitsmarge_relativ=GRENZEN["liquidations_marge"])
ok1 = (zu == ["ETH"] and "ETH" not in [t["symbol"] for t in tr] and btc is not None and abs(btc["menge"] - w) < 1e-12
       and abs(btc["kredit_eur"] - kr2) < 1e-9 and abs(btc["hebel"] - L2) < 1e-9 and abs(btc["liquidation_eur"] - liq) < 1e-6
       and lage["vertrauen"] and btc["hinweise"][0].startswith("⚠ Gespeicherte Position weicht von Bitpanda ab"))
pruefe("H1", ok1, "gespeichert ETH %.8g / BTC %.8g · Wallet BTC %.8g, Kredit %.2f · geschlossen %s · BTC Hebel %.3f (eigen %.3f), "
       "Liquidation %.2f (eigen %.2f), Abstand %.1f %% · Wallet-Stand %s >= Buchung %s" % (
           roh["ETH"].positionsmenge, pb.positionsmenge, w, kr2, zu, btc["hebel"], L2, btc["liquidation_eur"], liq,
           100 * (btc.get("abstand_liquidation") or 0), lage["buchungen_stand"][:16], lage["position_stand"][:16]))
# vorher (alte Rechnung) zum Vergleich
alt = HF.lade(c, jetzt=JETZT, nahe_grenze=NAHE, wallet=False)
print("     vorher: " + " · ".join("%s %s Abstand %.1f %%" % (t["symbol"], t["empfehlung"], 100 * (t.get("abstand_liquidation") or 0)) for t in alt))
print("     jetzt:  " + " · ".join("%s %s Abstand %.1f %%" % (t["symbol"], t["empfehlung"], 100 * (t.get("abstand_liquidation") or 0)) for t in tr))
c.close()

# ══ H2 keine ETH-Meldung, Lauf ══════════════════════════════════════════════════════════════════════════════════════════════
pfad2 = os.path.join(T, "h2.db")
shutil.copy(BASIS, pfad2)


def fabrik():
    k = sqlite3.connect(pfad2)
    k.row_factory = sqlite3.Row
    return k


import logging  # noqa: E402
import scheduler.background as BG  # noqa: E402

gesehen = []


class Fang(logging.Handler):
    def emit(self, rec):
        gesehen.append(rec.getMessage())


logging.getLogger("scheduler.background").addHandler(Fang())
logging.getLogger("scheduler.background").setLevel(logging.INFO)
post = []
_alt_lade = BG.__dict__.get("_G")
import agent.regel0_groesse as G  # noqa: E402

_g_lade = G.lade
G.lade = lambda *a, **k: dict(_g_lade(*a, **k), hebelfuehrung_aktiv=True)
try:
    r2 = BG._hebelfuehrung_lauf(fabrik, versand=lambda b, t, *a: post.append((b, t)) or True)
finally:
    G.lade = _g_lade
zeile_log = next((z for z in gesehen if z.startswith("Hebelfuehrung:")), "")
ok2 = r2.get("laut_bitpanda_geschlossen") == ["ETH"] and not any("ETH" in b for b, _ in post) and "laut Bitpanda geschlossen" in zeile_log
pruefe("H2", ok2, "Lauf: geschlossen %s · Mails %s · Log: %s" % (r2.get("laut_bitpanda_geschlossen"), [b for b, _ in post] or "keine",
                                                                 zeile_log[:200]))

# ══ H3 Vertrauen fehlt ═════════════════════════════════════════════════════════════════════════════════════════════════════
c = kopie("h3")
c.execute("UPDATE meta SET value='2026-10-14T00:00:00Z' WHERE key='bitpanda_buchungen_stand'")
c.commit()
tr3 = HF.lade(c, jetzt=JETZT, nahe_grenze=NAHE)
b3 = next(t for t in tr3 if t["symbol"] == "BTC")
ok3 = (HF.laut_bitpanda_geschlossen(c) == [] and "ETH" in [t["symbol"] for t in tr3] and abs(b3["menge"] - pb.positionsmenge) < 1e-12
       and "noch nicht auf dem Stand" in b3["hinweise"][0])
pruefe("H3", ok3, "Wallet-Stand 14.10. < Buchung -> ETH bleibt %s, BTC gespeichert %s, Hinweis: %s" % (
    "ETH" in [t["symbol"] for t in tr3], b3["menge"], b3["hinweise"][0][:90]))
c.close()

# ══ H4 neue Position, die das Wallet noch nicht kennt ═════════════════════════════════════════════════════════════════════
c = kopie("h4")
neu_zeit = JETZT + timedelta(minutes=5)
c.execute("INSERT INTO hebel_positions (symbol, richtung, status, eroeffnet_am, geschlossen_am, hebel_effektiv, positionswert_eur, "
          "kreditbetrag_eur, eigenkapital_eur, positionsmenge, letzte_transaktion_unix_timestamp) "
          "VALUES ('SOL','LONG','offen',?,NULL,3.0,300,200,100,2.0,?)", (neu_zeit.isoformat(), int(neu_zeit.timestamp())))
c.execute("UPDATE meta SET value=? WHERE key='hebel_position_last_synced_unix'", (str(int(neu_zeit.timestamp())),))
c.commit()
tr4 = HF.lade(c, jetzt=JETZT + timedelta(minutes=6), nahe_grenze=NAHE)
ok4 = "SOL" in [t["symbol"] for t in tr4] and HF.laut_bitpanda_geschlossen(c) == []
pruefe("H4", ok4, "SOL eroeffnet nach dem Wallet-Stand -> in der Fuehrung %s, nichts als geschlossen gewertet %s" % (
    "SOL" in [t["symbol"] for t in tr4], HF.laut_bitpanda_geschlossen(c) == []))
c.close()

# ══ H5 zwei abweichende -> Kredit anteilig ═════════════════════════════════════════════════════════════════════════════════
c = kopie("h5")
aid_eth = c.execute("SELECT k.asset_id FROM bitpanda_katalog k JOIN bitpanda_wallet_saldo w ON w.asset_id=k.asset_id "
                    "WHERE k.symbol='ETH' AND w.wallet_owner='margin-trading'").fetchone()[0]      # ETH steht zweimal im Katalog
c.execute("UPDATE bitpanda_wallet_saldo SET saldo=0.1 WHERE asset_id=? AND wallet_owner='margin-trading'", (aid_eth,))
c.commit()
tr5 = HF.lade(c, jetzt=JETZT, nahe_grenze=NAHE)
e5 = next((t for t in tr5 if t["symbol"] == "ETH"), None)
b5 = next(t for t in tr5 if t["symbol"] == "BTC")
pe = roh["ETH"]
ok5 = (e5 is not None and abs(e5["kredit_eur"] - pe.kreditbetrag_eur * 0.1 / pe.positionsmenge) < 1e-9
       and abs(b5["kredit_eur"] - pb.kreditbetrag_eur * w / pb.positionsmenge) < 1e-9 and "anteilig" in b5["hinweise"][0])
pruefe("H5", ok5, "ETH-Wallet 0,1 und BTC abweichend -> Kredit anteilig: ETH %.2f, BTC %.2f (nicht 560)" % (
    e5["kredit_eur"] if e5 else -1, b5["kredit_eur"]))
c.close()

# ══ H6 wallet=False = alte Rechnung ════════════════════════════════════════════════════════════════════════════════════════
c = kopie("h6")
tr6 = HF.lade(c, jetzt=JETZT, nahe_grenze=NAHE, wallet=False)
soll = [HF.fuehre(symbol=p.symbol, richtung=p.richtung, eroeffnet_am=p.eroeffnet_am, hebel=p.hebel_effektiv,
                  positionswert_eur=p.positionswert_eur, kreditbetrag_eur=p.kreditbetrag_eur, eigenkapital_eur=p.eigenkapital_eur,
                  positionsmenge=p.positionsmenge, kurs_eur=None, jetzt=JETZT)["liquidation_eur"] for p in db.get_open_hebel_positions(c)]
ok6 = sorted(t["liquidation_eur"] for t in tr6) == sorted(soll) and all("wallet_hinweis" not in t for t in tr6)
pruefe("H6", ok6, "ohne Wallet: Liquidationen %s = gespeicherte Rechnung" % [round(x, 2) for x in sorted(soll)])
c.close()

# ══ H7 Statusseite und Deckel ══════════════════════════════════════════════════════════════════════════════════════════════
c = kopie("h7")
st = BL.hebel_fuehrung_jetzt(c)
e7 = next((x for x in st if x["symbol"] == "ETH"), {})
b7 = next((x for x in st if x["symbol"] == "BTC"), {})
import agent.hebel_aggregat as HA  # noqa: E402

ag = HA.aggregat(c, kapital_eur=10000.0, anteil=0.2, jetzt=JETZT)
ok7 = (e7.get("empfehlung") == HF.LAUT_BITPANDA_GESCHLOSSEN and "Gespeicherte Position weicht" in (b7.get("grund") or "")
       and "ETH" not in str(ag.get("positionen") or ag))
pruefe("H7", ok7, "Statusseite ETH: %s · BTC grund: %s · Deckel ohne ETH %s" % (
    e7.get("empfehlung"), (b7.get("grund") or "")[:70], "ETH" not in str(ag.get("positionen") or ag)))
c.close()

# ══ H8 unveraendert ═══════════════════════════════════════════════════════════════════════════════════════════════════════
NACH = {"prod": summe(db.DB_PATH), "quelle": summe(QUELLE)}
pruefe("H8", NACH == VOR, "Desktop-Prod unveraendert %s · Sicherung unveraendert %s" % (NACH["prod"] == VOR["prod"], NACH["quelle"] == VOR["quelle"]))
wegwerf.aufraeumen(T)
print("\n%d von %d bestanden" % (sum(ERG), len(ERG)))
