"""P14 Spot B1 Mitnahme x3 (11.10.2026, Spot §41) - Pruefstand am SEITENEFFEKT: Wegwerf-Produktion, Wegwerf-Ablage, Versand abgefangen.

    python Basisinfos/Rechenkern_02_10/p14_pruefstand.py

Gestellte Dollar-Tagesschluesse ab 2026-01-01; der Job laeuft Tag fuer Tag (``heute``) wie am NB.
  S1 Kreis: L-Coin ja; Kern (BTC), Stablecoin (USDC), Aktie, Bestand 0 nein; voll gestakter Coin ja (frei + gestakt)
  S2 x3 am Tag 200 -> genau EINE Mail (Haelfte von frei + gestakt), danach keine weitere in diesem Fenster
  S3 x2,9 -> nie eine Mail
  S4 Fensterende ohne Ausloesung -> neues Fenster, Startkurs = Schluss am Fensterende; nach Mitnahme: Rest bis Ende, dann neues Fenster
  S5 Treffer am letzten Fenstertag -> KEINE Mitnahme (wie die Messung: kein Folgetag im Fenster)
  S6 Bestand weg -> Fenster geschlossen; Kurs fehlt -> kein Fenster, Protokoll
  S7 Sprung >= 2 x zum Vortag -> "zu pruefen", keine Mail; Ausloesung > 3 T alt (Ausfall) -> "verpasst", keine Mail
  S8 Schalter aus -> Protokoll ja, Mail nein; eingeschaltet innerhalb von 3 T -> Mail kommt nach
  S9 A6: Schalter an -> Stop-Nachzieh-Mail ohne Spot-Zeilen, Hebel-Zeilen bleiben, Protokoll und Verfolgung laufen weiter; aus -> unveraendert
  S10 die Wegwerf-Produktion bleibt unveraendert (Pruefsumme) - der Job schreibt nur die Ablage
"""
import hashlib
import os
import sqlite3
import sys
import tempfile
from datetime import date, timedelta
from types import SimpleNamespace as NS

WURZEL = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, WURZEL)
__import__("sys").path.append(__import__("os").path.abspath(__file__).split("TradingInfoTool")[0] + "TradingInfoTool")  # wegwerf.py
import wegwerf  # noqa: E402,F401  Wegwerf-Ordner auf D: und Aufraeumen ohne stilles Scheitern (15.10.2026)
os.chdir(WURZEL)
import agent.regel0_groesse as G  # noqa: E402
import agent.spot_mitnahme as SM  # noqa: E402
import database.db as db  # noqa: E402
import scheduler.background as BG  # noqa: E402

ERG = []


def pruefe(k, ok, text):
    ERG.append(bool(ok))
    print("%-4s %-9s %s" % (k, "bestanden" if ok else "FEHLER", text))


def summe(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


T = tempfile.mkdtemp(prefix="p14_")
PROD = os.path.join(T, "prod.db")
from pathlib import Path as _P  # noqa: E402
db.DB_PATH = _P(PROD)
c = db.get_connection()
db.init_db(c) if hasattr(db, "init_db") else None
c.close()
c = sqlite3.connect(PROD)
for t in ("holdings", "price_history_ohlc"):
    assert c.execute("SELECT name FROM sqlite_master WHERE name=?", (t,)).fetchone(), t
T0 = date(2026, 1, 1)


def reihe(sym, punkte):
    """punkte: [(Tag-Index, Faktor gegen 100)] - dazwischen LINEAR (eine steigende Reihe, kein Sprung), nach dem letzten Punkt flach.
    Ein Sprung entsteht nur, wo zwei Punkte direkt aufeinander folgen (EEE)."""
    c.execute("DELETE FROM price_history_ohlc WHERE symbol=?", (sym,))
    pk = sorted(punkte)
    for i in range(0, 800):
        vor = max((p for p in pk if p[0] <= i), default=pk[0])
        nach = min((p for p in pk if p[0] >= i), default=pk[-1])
        f = vor[1] if nach[0] == vor[0] else vor[1] + (nach[1] - vor[1]) * (i - vor[0]) / (nach[0] - vor[0])
        wert = 100.0 * f
        c.execute("INSERT INTO price_history_ohlc (symbol, currency, date, open, high, low, close, volume, fetched_at, quelle) "
                  "VALUES (?,?,?,?,?,?,?,?,?,?)", (sym, "USD", (T0 + timedelta(days=i)).isoformat(), wert, wert, wert, wert, 0, "x", "test"))


# Bestaende
for s, q, st in (("AAA", 10, 0), ("BBB", 4, 6), ("CCC", 5, 0), ("DDD", 5, 0), ("EEE", 5, 0), ("FFF", 5, 0), ("GGG", 5, 0),
                 ("BTC", 1, 0), ("USDC", 100, 0), ("APPL", 3, 0), ("NUL", 0, 0), ("OHNE", 5, 0)):
    c.execute("INSERT OR REPLACE INTO holdings (symbol, quantity, staked_quantity, updated_at) VALUES (?,?,?,?)", (s, q, st, "2026-01-01"))
reihe("AAA", [(0, 1.0), (199, 2.99), (200, 3.05), (201, 2.8)])   # x3 erstmals am Tag 200
reihe("BBB", [(0, 1.0), (149, 2.95), (150, 3.2)])                 # x3 am Tag 150, mit gestaktem Anteil
reihe("CCC", [(0, 1.0), (100, 2.9)])                              # nie x3
reihe("DDD", [(0, 1.0), (364, 2.99), (365, 3.1)])                 # Treffer genau am letzten Fenstertag
reihe("EEE", [(0, 1.0), (99, 1.0), (100, 3.5)])                   # Sprung am Tag 100 (Vortag 100, Tag 350)
reihe("FFF", [(0, 1.0), (49, 2.95), (50, 3.1)])                   # Ausloesung Tag 50 - der Job laeuft erst Tag 60 (Ausfall)
reihe("GGG", [(0, 1.0), (119, 2.95), (120, 3.3)])                 # Schalter aus bei Ausloesung, an am Tag danach
reihe("BTC", [(0, 1.0), (200, 1.5)])
c.commit()
c.close()
WL = [NS(symbol=s, assetklasse="krypto", ist_cash_aequivalent=False) for s in ("AAA", "BBB", "CCC", "DDD", "EEE", "FFF", "GGG", "BTC", "NUL", "OHNE")] + \
     [NS(symbol="USDC", assetklasse="krypto", ist_cash_aequivalent=True), NS(symbol="APPL", assetklasse="aktien", ist_cash_aequivalent=False)]
ORD = os.path.join(T, "daten")
os.makedirs(ORD)
post = []


def fab():
    k = sqlite3.connect(PROD)
    k.row_factory = sqlite3.Row
    return k


schalter = {"an": True}
G.spot_mitnahme_aktiv = lambda werte=None: schalter["an"]


def job(tag_index, nur=None):
    return BG.spot_mitnahme_job(fab, lambda: WL, versand=lambda b, t, bi=None: post.append((tag_index, b, t)) or True,
                                heute=T0 + timedelta(days=tag_index + 1), ordner=ORD)


vor = summe(PROD)
r0 = job(0)                                                 # Starttag = Tag 0 (gestern aus Sicht von Tag 1)
a = SM.oeffne(ORD)
im_kreis = {r[0] for r in a.execute("SELECT symbol FROM fenster")}
a.close()
pruefe("S1", im_kreis == {"AAA", "BBB", "CCC", "DDD", "EEE", "FFF", "GGG"} and r0["kreis"] == 8,
       "Fenster fuer %s · Kreis %d (OHNE ohne Kurs zaehlt mit, bekommt kein Fenster)" % (sorted(im_kreis), r0["kreis"]))
# GGG: Schalter aus am Ausloesetag
for i in range(1, 120):
    if 50 <= i < 60:
        continue                                            # Ausfall Tag 50-59 fuer alle (FFF verpasst)
    job(i)
schalter["an"] = False
job(120)                                                    # GGG ausgeloest am Tag 120, Schalter aus -> keine Mail
job(121)
mails_ggg_aus = [p for p in post if "GGG" in p[1]]
schalter["an"] = True
job(122)                                                    # eingeschaltet am naechsten Tag -> Mail kommt nach
mails_ggg_an = [p for p in post if "GGG" in p[1]]
for i in range(123, 420):
    job(i)
mail = {}
for t, b, txt in post:
    mail.setdefault(b.split(": ")[-1].replace("Hälfte von ", "").replace(" verkaufen oder in EURCV tauschen", "").replace(" verkaufen", ""), []).append((t, txt))
pruefe("S2", len(mail.get("AAA", [])) == 1 and mail["AAA"][0][0] == 200 and "5 Stück von 10" in mail["AAA"][0][1]
       and len(mail.get("BBB", [])) == 1 and "5 Stück von 10" in mail["BBB"][0][1] and "gestakt" in mail["BBB"][0][1],
       "AAA %s · BBB %s" % ([t for t, _ in mail.get("AAA", [])], [t for t, _ in mail.get("BBB", [])]))
pruefe("S3", "CCC" not in mail, "CCC Mails %d" % len(mail.get("CCC", [])))
a = SM.oeffne(ORD)
fen = {s: a.execute("SELECT start, startkurs_usd, ende, ausloese_tag, status, geschlossen_am, grund FROM fenster WHERE symbol=? ORDER BY start",
                    (s,)).fetchall() for s in ("AAA", "CCC", "DDD", "EEE", "FFF")}
a.close()
ccc_neu = len(fen["CCC"]) == 2 and fen["CCC"][0][6] == "Fensterende ohne Ausloesung" and fen["CCC"][1][0] == "2027-01-01" and fen["CCC"][1][1] == 290.0
aaa_neu = len(fen["AAA"]) == 2 and fen["AAA"][0][6] == "Fensterende nach Mitnahme"
pruefe("S4", ccc_neu and aaa_neu, "CCC %s · AAA %s" % ([(f[0], f[1], f[6]) for f in fen["CCC"]], [(f[0], f[3], f[6]) for f in fen["AAA"]]))
pruefe("S5", "DDD" not in mail and fen["DDD"][0][3] is None, "DDD Mails %d · Ausloesung %s · %s" % (len(mail.get("DDD", [])), fen["DDD"][0][3], fen["DDD"][0][6]))
a = SM.oeffne(ORD)
prot_ohne = a.execute("SELECT COUNT(*) FROM protokoll WHERE symbol='OHNE' AND art='kein Kurs'").fetchone()[0]
a.close()
c = sqlite3.connect(PROD)
c.execute("UPDATE holdings SET quantity=0 WHERE symbol='CCC'")
c.commit()
c.close()
vor = summe(PROD)                                          # ab hier misst S10 (die Aenderung oben war der Pruefstand selbst)
job(420)
a = SM.oeffne(ORD)
ccc_zu = a.execute("SELECT grund FROM fenster WHERE symbol='CCC' AND geschlossen_am IS NOT NULL ORDER BY start DESC").fetchone()
a.close()
pruefe("S6", ccc_zu and ccc_zu[0] == "Bestand weg" and prot_ohne == 1, "CCC %s · OHNE Protokoll 'kein Kurs' %d (nur beim Wechsel)" % (ccc_zu, prot_ohne))
pruefe("S7", "EEE" not in mail and fen["EEE"][0][4] == "zu pruefen" and "FFF" not in mail and fen["FFF"][0][4] == "verpasst",
       "EEE %s · FFF %s" % (fen["EEE"][0][4], fen["FFF"][0][4]))
pruefe("S8", not mails_ggg_aus and len(mails_ggg_an) == 1 and mails_ggg_an[0][0] == 122, "GGG aus: %d Mails · an am Tag 122: %s" % (
    len(mails_ggg_aus), [t for t, _, _ in mails_ggg_an]))

pruefe("S10", summe(PROD) == vor, "Produktion nach dem Job %s (gemessen VOR dem A6-Test - der echte Ausstiegsjob vermerkt seinen Lauf)" % (
    "unveraendert" if summe(PROD) == vor else "GEAENDERT"))
# S9 A6
import agent.krypto.backward_tracking as BT  # noqa: E402
import agent.fuehrung_protokoll as FP  # noqa: E402
import agent.ausstieg_verfolgung as AV  # noqa: E402
gesendet, lief = [], []
_alt = (BT.compute_ausstiegs_empfehlungen, BG._sende_ausstiegs_email, FP.schreibe, AV.verfolge)
BT.compute_ausstiegs_empfehlungen = lambda *a_, **k_: {"empfehlungen": [{"tier": "krypto", "symbol": "X"}, {"tier": BT.TIER_HEBEL, "symbol": "Y"}],
                                                        "geprueft": 2}
BG._sende_ausstiegs_email = lambda e, g: gesendet.append([x["symbol"] for x in e])
FP.schreibe = lambda *a_, **k_: lief.append("protokoll") or 1
AV.verfolge = lambda *a_, **k_: lief.append("verfolgung") or {}
import agent.krypto.ausstiegsregel as AR  # noqa: E402
_par = AR.parameter_aus_config
AR.parameter_aus_config = lambda cfg: (1.0, 1.0, True)
schalter["an"] = True
BG.ausstiegs_job(fab, lambda: WL)
schalter["an"] = False
BG.ausstiegs_job(fab, lambda: WL)
BT.compute_ausstiegs_empfehlungen, BG._sende_ausstiegs_email, FP.schreibe, AV.verfolge = _alt
AR.parameter_aus_config = _par
pruefe("S9", gesendet == [["Y"], ["X", "Y"]] and lief.count("protokoll") == 2 and lief.count("verfolgung") == 2,
       "an: %s · aus: %s · Protokoll/Verfolgung %s" % (gesendet[0] if gesendet else None, gesendet[1] if len(gesendet) > 1 else None, lief))
import shutil  # noqa: E402
wegwerf.aufraeumen(T)
print()
print("%d von %d bestanden" % (sum(ERG), len(ERG)))
