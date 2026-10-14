"""Buendel P11 + O45 (11.10.2026, Plan Schritt 53 G-T) - Pruefstand am SEITENEFFEKT, nie an der Produktion.

    python Basisinfos/Rechenkern_02_10/p11_o45_pruefstand.py <Pruefverzeichnis mit Kopie tradinginfotool.db>

P11 Hebel-Wallet-Abgleich (nur lesend):
  H1 die NB-Kopie 10.10.: BTC, ETH, Kredit stimmen (Wallet = Position) - kein Fehlalarm
  H2 Wegwerf-DB: Teilschliessung (Wallet kleiner), Kredit weicht ab, Wallet ohne Position, Position ohne Wallet, Menge fehlt
  H3 Zeitversatz: erste Abweichung meldet nicht, die zweite in Folge schon; verschwundene nicht mehr
  H4 der Lauf im Job: Lauf 1 keine Mail, Lauf 2 genau eine, Lauf 3 gesperrt (6 h), nach 7 h wieder; bei Gleichstand nie
  H5 die Mail: eine Handlung (WAS ZU TUN IST), nennt Symbol und Werte, keine Schluessel/Token
O45 Wochen- und Tageschart:
  C1 REGEL0-Signalmail: 1 Signalbild + 2 Charts (Woche, Tag), alle drei im HTML eingesetzt, Text unveraendert
  C2 scheitert das Chart, geht die Mail mit dem Signalbild (P-8); ohne Charts (zu wenig Daten) ebenso
  C3 H15-Mail an einer WEGWERFkopie der NB-Kopie: Versand mit Bildern (Woche + Tag je gemeldeter Position), Logzeile 'Charts n'
  C4 Altpruefstaende mit zwei Argumenten (betreff, text) laufen weiter (Signatur-Weiche)
  C5 Pruefsumme der NB-Kopie unveraendert
"""
import hashlib
import io
import logging
import os
import shutil
import sqlite3
import sys
import tempfile
from datetime import datetime, timedelta, timezone

WURZEL = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, WURZEL)
__import__("sys").path.append(__import__("os").path.abspath(__file__).split("TradingInfoTool")[0] + "TradingInfoTool")  # wegwerf.py
import wegwerf  # noqa: E402,F401  Wegwerf-Ordner auf D: und Aufraeumen ohne stilles Scheitern (15.10.2026)
os.chdir(WURZEL)
D = os.path.abspath(sys.argv[1])
KOPIE = os.path.join(D, "tradinginfotool.db")

import agent.hebel_wallet_abgleich as HW  # noqa: E402
import agent.indikator_chart as IC  # noqa: E402
import agent.regel0_ablage as AB  # noqa: E402
import agent.regel0_groesse as G  # noqa: E402
import agent.regel0_mail as RM  # noqa: E402
import scheduler.background as BG  # noqa: E402
from api.email_notify import html_mit_bildern  # noqa: E402

ERG = []


def pruefe(k, ok, text):
    ERG.append(bool(ok))
    print("%-3s %-9s %s" % (k, "bestanden" if ok else "FEHLER", text))


def summe(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


vor = summe(KOPIE)

# ---- H1 die echte Kopie ----
c = sqlite3.connect("file:%s?mode=ro" % KOPIE.replace("\\", "/"), uri=True)
e1 = HW.pruefe(c)
c.close()
pruefe("H1", e1["ok"] is True and {z["symbol"] for z in e1["zeilen"]} == {"BTC", "ETH"} and e1["kredit"]["ok"], HW.zeile(e1))

# ---- Wegwerf-DB mit den drei Tabellen aus der Kopie ----
T = tempfile.mkdtemp(prefix="p11_")
W = os.path.join(T, "w.db")
w = sqlite3.connect("file:%s" % W.replace("\\", "/"), uri=True)   # URI-Verbindung, sonst nimmt ATTACH kein mode=ro
w.execute("ATTACH DATABASE ? AS k", ("file:%s?mode=ro" % KOPIE.replace("\\", "/"),))
for t in ("bitpanda_wallet_saldo", "hebel_positions", "bitpanda_katalog", "meta"):
    sql = w.execute("SELECT sql FROM k.sqlite_master WHERE name=?", (t,)).fetchone()[0]
    w.execute(sql)
    w.execute("INSERT INTO main.%s SELECT * FROM k.%s" % (t, t))
w.commit()
w.execute("DETACH DATABASE k")
aid = {s: a for a, s in w.execute("SELECT asset_id, symbol FROM bitpanda_katalog")}


def setze_wallet(sym, saldo):
    w.execute("UPDATE bitpanda_wallet_saldo SET saldo=? WHERE wallet_owner='margin-trading' AND asset_id=?", (saldo, aid[sym]))
    if w.execute("SELECT changes()").fetchone()[0] == 0:
        w.execute("INSERT INTO bitpanda_wallet_saldo VALUES (?, 'margin-trading', ?, ?, '2026-10-11T08:00:00Z', '2026-10-11T08:00:00Z')",
                  (aid[sym], "test-" + sym, saldo))
    w.commit()


faelle = []
setze_wallet("ETH", 0.5)                                             # Teilschliessung bei Bitpanda, Importer haelt 0,896
faelle.append(("Teilschliessung", [z["art"] for z in HW.pruefe(w)["zeilen"] if z["symbol"] == "ETH"] == ["Menge weicht ab"]))
setze_wallet("ETH", 0.89636371)
w.execute("UPDATE bitpanda_wallet_saldo SET saldo=-1600 WHERE wallet_owner='margin-trading-credit'"); w.commit()
faelle.append(("Kredit", HW.pruefe(w)["kredit"]["ok"] is False))
w.execute("UPDATE bitpanda_wallet_saldo SET saldo=-2600 WHERE wallet_owner='margin-trading-credit'"); w.commit()
setze_wallet("SOL", 3.0)
faelle.append(("Wallet ohne Position", [z["art"] for z in HW.pruefe(w)["zeilen"] if z["symbol"] == "SOL"] == ["Wallet ohne Position"]))
setze_wallet("SOL", 0.0)
setze_wallet("BTC", 0.0)
faelle.append(("Position ohne Wallet", [z["art"] for z in HW.pruefe(w)["zeilen"] if z["symbol"] == "BTC"] == ["Position ohne Wallet"]))
setze_wallet("BTC", 0.02038541)
w.execute("UPDATE hebel_positions SET positionsmenge=NULL WHERE symbol='ETH' AND geschlossen_am IS NULL"); w.commit()
faelle.append(("Menge fehlt", [z["art"] for z in HW.pruefe(w)["zeilen"] if z["symbol"] == "ETH"] == ["positionsmenge fehlt"]))
w.execute("UPDATE hebel_positions SET positionsmenge=0.89636371 WHERE symbol='ETH' AND geschlossen_am IS NULL"); w.commit()
faelle.append(("wieder gleich", HW.pruefe(w)["ok"] is True))
pruefe("H2", all(ok for _, ok in faelle), " · ".join("%s %s" % (f, "ok" if ok else "FEHLER") for f, ok in faelle))

# ---- H3 Zeitversatz ----
a1 = HW.bestaetigt({"abweichungen": ["menge:ETH"]}, set())
a2 = HW.bestaetigt({"abweichungen": ["menge:ETH"]}, {"menge:ETH"})
a3 = HW.bestaetigt({"abweichungen": []}, {"menge:ETH"})
pruefe("H3", a1 == [] and a2 == ["menge:ETH"] and a3 == [], "erster Lauf %s · zweiter %s · verschwunden %s" % (a1, a2, a3))

# ---- H4 der Lauf im Job ----
post = []


def cf():
    k = sqlite3.connect(W)
    k.row_factory = sqlite3.Row
    return k


HW._VORHER = set()
setze_wallet("ETH", 0.5)
t0 = datetime(2026, 10, 11, 8, 0, tzinfo=timezone.utc)
versand = lambda b, t: post.append((b, t)) or True  # noqa: E731
r1 = BG._hebel_wallet_lauf(cf, versand, t0)
r2 = BG._hebel_wallet_lauf(cf, versand, t0 + timedelta(minutes=15))
r3 = BG._hebel_wallet_lauf(cf, versand, t0 + timedelta(minutes=30))
r4 = BG._hebel_wallet_lauf(cf, versand, t0 + timedelta(hours=7))
n_mail = len(post)
setze_wallet("ETH", 0.89636371)
HW._VORHER = set()
post_gleich = []
for i in range(3):
    BG._hebel_wallet_lauf(cf, lambda b, t: post_gleich.append(b) or True, t0 + timedelta(hours=8, minutes=15 * i))
pruefe("H4", not r1["gemeldet"] and r2["gemeldet"] == ["menge:ETH"] and r2["zugestellt"] and not r3["gemeldet"]
       and r4["gemeldet"] == ["menge:ETH"] and n_mail == 2 and not post_gleich,
       "Lauf1 %s · Lauf2 %s · Lauf3 %s · nach 7 h %s · Mails %d · bei Gleichstand %d" % (
           r1["gemeldet"], r2["gemeldet"], r3["gemeldet"], r4["gemeldet"], n_mail, len(post_gleich)))
b, t = post[0]
pruefe("H5", b.startswith("TradingInfoTool: Hebelposition passt nicht zu Bitpanda: ETH") and t.startswith("WAS ZU TUN IST")
       and "0.5" in t and "0.89636371" in t and "KEY" not in t.upper().replace("SCHLUESSEL", ""), b)
w.close()

# ---- C1/C2 REGEL0-Signalmail mit Charts ----
jetzt = datetime(2026, 9, 25, 11, 9, tzinfo=timezone.utc)


def ablage():
    d = tempfile.mkdtemp(prefix="r0_o45_", dir=T)
    k = AB.oeffne(d)
    k.execute("INSERT INTO signal (symbol, signalstunde, einstieg, ausstieg, vh, stufe_vorlaeufig, p2, p3, p5, hebel_schalter, bitpanda, kurs, "
              "kurs_markt, paar, faktor) VALUES ('ETH','2026-09-25 10:00','2026-09-25 11:00','2026-09-26 11:00',0.0415,5,0.001,0.001,0.013,1,"
              "'ETH',2500.0,'spot','ETHUSDT',1.0)")
    k.commit(); k.close()
    return d


def lauf(**kw):
    d = ablage()
    p = []
    z = RM.versende(d, lambda *a: p.append(("alt",) + a) or True, jetzt=jetzt, werte=G.lade(),
                    kurse=lambda: ({"ETH": 2501.0}, {"ETHUSDT": 2500.0}, {"ETH": 2150.0}), bild=lambda r: b"PNG",   # (Bitpanda USD, Binance, Bitpanda EUR)
                    senden_html=lambda b_, t_, h_, bi: p.append(("html", b_, t_, h_, bi)) or True, **kw)
    return z, p


z0, p0 = lauf()
z1, p1 = lauf(zusatzbilder=lambda r: IC.bilder("data", r["symbol"], r.get("bitpanda"), r.get("eur_je_usd"), praefix="regel0"))
ok1 = z1["signal"] == 1 and len(p1) == 1 and len(p1[0][4]) == 3 and p1[0][4][0]["png"] == b"PNG"
h1 = p1[0][3] if p1 else ""
gesetzt = html_mit_bildern(h1, "|".join("<img %d>" % i for i in range(3))) if h1 else ""
pruefe("C1", ok1 and all(("{{BILD:%d}}" % i) in h1 for i in range(3)) and p0[0][2] == p1[0][2]
       and [x["filename"].split("_")[-1] for x in p1[0][4][1:]] == ["woche.png", "tag.png"],
       "Bilder %s · Platzhalter im HTML %s · Text gleich %s · %s" % (len(p1[0][4]) if p1 else 0,
                                                                     [("{{BILD:%d}}" % i) in h1 for i in range(3)],
                                                                     p0[0][2] == p1[0][2] if p1 else None,
                                                                     [x["filename"] for x in (p1[0][4] if p1 else [])]))


def kaputt(r):
    raise RuntimeError("Testfehler")


z2, p2 = lauf(zusatzbilder=kaputt)
z3, p3 = lauf(zusatzbilder=lambda r: IC.bilder("data", "GIBTSNICHT"))
pruefe("C2", z2["signal"] == 1 and len(p2[0][4]) == 1 and z3["signal"] == 1 and len(p3[0][4]) == 1,
       "Chart scheitert: Mail mit %d Bild · keine Daten: Mail mit %d Bild" % (len(p2[0][4]), len(p3[0][4])))

# ---- C3/C4 H15-Mail an einer Wegwerfkopie ----
WK = os.path.join(T, "h15.db")
s_ = sqlite3.connect("file:%s?mode=ro" % KOPIE.replace("\\", "/"), uri=True)
d_ = sqlite3.connect(WK)
s_.backup(d_)
s_.close(); d_.close()


def cf2():
    k = sqlite3.connect(WK)
    k.row_factory = sqlite3.Row
    return k


log = io.StringIO()
hd = logging.StreamHandler(log)
logging.getLogger("scheduler.background").addHandler(hd)
logging.getLogger("scheduler.background").setLevel(logging.INFO)
gesendet = []
r5 = BG._hebelfuehrung_lauf(cf2, versand=lambda b_, t_, bilder: gesendet.append((b_, t_, bilder)) or True)
k = cf2()
k.execute("DELETE FROM job_laeufe WHERE job_id LIKE 'hebelfuehrung:%' AND job_id LIKE '%" + datetime.now(timezone.utc).date().isoformat() + "'")
k.commit(); k.close()
alt = []
r6 = BG._hebelfuehrung_lauf(cf2, versand=lambda b_, t_: alt.append(b_) or True)
syms = sorted({x[0] for x in (r5.get("empfehlungen") or []) if x[1] != "HALTEN"})
pruefe("C3", r5.get("mail") is not None and gesendet and len(gesendet[0][2]) == 2 * len(syms)
       and all(b_["filename"].startswith("hebel_") for b_ in gesendet[0][2]) and "Charts %d" % (2 * len(syms)) in log.getvalue(),
       "gemeldet %s · Bilder %d · Logzeile %s" % (syms, len(gesendet[0][2]) if gesendet else 0, "Charts %d" % (2 * len(syms)) in log.getvalue()))
pruefe("C4", r6.get("zugestellt") is True and len(alt) == 1, "Versand mit (betreff, text): zugestellt %s" % r6.get("zugestellt"))
wegwerf.aufraeumen(T)
pruefe("C5", summe(KOPIE) == vor, "Pruefsumme der NB-Kopie %s" % ("gleich" if summe(KOPIE) == vor else "GEAENDERT"))
print()
print("%d von %d bestanden" % (sum(ERG), len(ERG)))
