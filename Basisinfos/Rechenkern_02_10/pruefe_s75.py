"""Gegenpruefung S7-5 (03.10.2026, F-1 bis F-5) - Wegwerfdateien, keine Produktion, kein echter Versand.

1  S7-5a Neuaufnahme: kleine Kopie der Datenbasis OHNE zwei vorhandene Assets (HYPE Futures, FLOKI Spot mit 1000er-Markpreis).
         Die Neuaufnahme muss sie als neu erkennen und ZEILENGLEICH zur echten Datei laden (Kerzen und Markpreis, gemeinsamer Zeitraum).
         Ein Asset, dessen Abruf scheitert, hinterlaesst NICHTS (alles oder nichts) und wird beim naechsten Lauf wieder versucht.
         Faellig einmal je Tag ab 02:00 UTC
2  S7-5b Preisabgleich vor der Signalmail: Kollision -> keine Mail, Meldung einmal; gleicher Coin -> Mail mit Abgleichzeile;
         Ticker weg -> Mail mit *nicht gegengeprueft* (F-2)
3  S7-5c gesperrte Kuerzel auch in der Messbasis: echter Stundenlauf zur Stunde des ZK-Signals (18.06.2026) mit Bitpanda-ZK-Schalter AN
         -> ZK ohne Bitpanda-Namen, keine Mail
"""
import os
import shutil
import sqlite3
import sys
import tempfile
from datetime import datetime, timedelta, timezone

import pandas as pd

HIER = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, HIER)
os.chdir(HIER)
sys.stdout.reconfigure(encoding="utf-8")
import agent.regel0_nachlader as NL                                # noqa: E402
import agent.regel0_mail as RM                                     # noqa: E402
import agent.regel0_ablage as AB                                   # noqa: E402
import agent.regel0_groesse as G                                   # noqa: E402

ergebnis = []


def pruef(name, ok, info=""):
    ergebnis.append(bool(ok))
    print("  %s %s%s" % ("✔" if ok else "⛔", name, (" - " + info) if info else ""), flush=True)


def ro(p):
    return sqlite3.connect("file:%s?mode=ro" % p.replace("\\", "/"), uri=True)


print("1) S7-5a Neuaufnahme")
d = tempfile.mkdtemp()
ECHT_A, ECHT_M = "data/stundenkurse_alle.db", "data/markpreis_alle.db"
WEG = ("HYPE", "FLOKI")
BLEIBT = ("ASTER", "KAS")
for name, quelle, tabs in (("stundenkurse_alle.db", ECHT_A, ("stundenkurse", "_quelle")), ("markpreis_alle.db", ECHT_M, ("markpreis",))):
    q = ro(quelle); z = sqlite3.connect(os.path.join(d, name))
    for (sql,) in q.execute("SELECT sql FROM sqlite_master WHERE type='table' AND sql IS NOT NULL"):
        z.execute(sql)
    for t in tabs:
        rows = q.execute("SELECT * FROM %s WHERE symbol IN (%s)" % (t, ",".join("?" * len(BLEIBT))), BLEIBT).fetchall()
        if rows:
            z.executemany("INSERT INTO %s VALUES (%s)" % (t, ",".join("?" * len(rows[0]))), rows)
    z.commit(); z.close(); q.close()
q = ro(ECHT_A)
quelle = {r[0]: (r[1], r[2]) for r in q.execute("SELECT symbol, markt, paar FROM _quelle WHERE symbol IN (%s)" % ",".join("?" * 4), WEG + BLEIBT)}
q.close()
stub = lambda: ([(s, quelle[s][0], quelle[s][1]) for s in sorted(WEG + BLEIBT)], 0, 0, 0)
b1 = NL.neuaufnahme(d, ausgabe=lambda s: print("   ", s), universum=stub)
pruef("die zwei fehlenden Assets werden als neu erkannt und geladen", sorted(x.split("(")[0] for x in b1["neu"]) == sorted(WEG), str(b1["neu"]))
for s in WEG:
    e, n = ro(ECHT_A), ro(os.path.join(d, "stundenkurse_alle.db"))
    hi = e.execute("SELECT MAX(stunde) FROM stundenkurse WHERE symbol=?", (s,)).fetchone()[0]
    a = e.execute("SELECT * FROM stundenkurse WHERE symbol=? AND stunde < ? ORDER BY stunde", (s, hi)).fetchall()
    b = n.execute("SELECT * FROM stundenkurse WHERE symbol=? AND stunde < ? ORDER BY stunde", (s, hi)).fetchall()
    qn = n.execute("SELECT markt, paar FROM _quelle WHERE symbol=?", (s,)).fetchone()
    e.close(); n.close()
    pruef("%s Kerzen zeilengleich zur echten Datei bis %s (ohne deren letzte, damals offene Stunde), Quelle %s" % (s, hi, qn), a == b and len(a) > 500
          and qn == quelle[s], "%d / %d Zeilen" % (len(a), len(b)))
    e, n = ro(ECHT_M), ro(os.path.join(d, "markpreis_alle.db"))
    hm = e.execute("SELECT MAX(stunde) FROM markpreis WHERE symbol=?", (s,)).fetchone()[0]
    a = {r[0]: r[1:] for r in e.execute("SELECT stunde, open, high, low, close, paar, faktor FROM markpreis WHERE symbol=? AND stunde < ?", (s, hm))}
    b = {r[0]: r[1:] for r in n.execute("SELECT stunde, open, high, low, close, paar, faktor FROM markpreis WHERE symbol=? AND stunde < ?", (s, hm))}
    e.close(); n.close()
    gleich = all(a[t] == b[t] for t in set(a) & set(b))
    fehlt = sorted(set(a) - set(b)); mehr = sorted(set(b) - set(a))
    tage = sorted({t[:10] for t in mehr})
    # ⚠️ 03.10.: das Monatsarchiv hat eine LUECKE am 29.06.2026 (alle Symbole), die Live-Schnittstelle nicht - mehr ist dort richtig
    ganze_tage = all(sum(1 for t in mehr if t[:10] == tg) == 24 for tg in tage)
    pruef("%s Markpreis: gemeinsame Stunden wertgleich, keine Archivstunde fehlt, zusaetzlich nur ganze Archiv-Luecken" % s,
          gleich and not fehlt and ganze_tage and len(a) > 500, "%d Archiv / %d neu · zusaetzlich %s · %s" % (len(a), len(b), tage, next(iter(b.values()))[4:] if b else "-"))
b2 = NL.neuaufnahme(d, ausgabe=lambda s: None, universum=stub)
pruef("zweiter Lauf: nichts Neues", b2["neu"] == [], str(b2))

# alles oder nichts: ein drittes Asset, dessen Abruf scheitert
q = ro(ECHT_A); paar_x = q.execute("SELECT markt, paar FROM _quelle WHERE symbol='PLUME'").fetchone(); q.close()
stub3 = lambda: ([(s, quelle[s][0], quelle[s][1]) for s in sorted(WEG + BLEIBT)] + [("PLUME", paar_x[0], paar_x[1])], 0, 0, 0)
alt_hole = NL._hole
NL._hole = lambda url, paar, a, b: (_ for _ in ()).throw(ConnectionError("Probe")) if paar == paar_x[1] else alt_hole(url, paar, a, b)
b3 = NL.neuaufnahme(d, ausgabe=lambda s: None, universum=stub3)
NL._hole = alt_hole
n = ro(os.path.join(d, "stundenkurse_alle.db"))
rest = n.execute("SELECT COUNT(*) FROM stundenkurse WHERE symbol='PLUME'").fetchone()[0] + n.execute("SELECT COUNT(*) FROM _quelle WHERE symbol='PLUME'").fetchone()[0]
n.close()
pruef("ein gescheiterter Abruf hinterlaesst NICHTS und wird gemeldet", rest == 0 and b3["fehler"] and b3["neu"] == [], "%s" % b3["fehler"])
b4 = NL.neuaufnahme(d, ausgabe=lambda s: None, universum=stub3)
pruef("... und der naechste Lauf holt es nach", [x.split("(")[0] for x in b4["neu"]] == ["PLUME"], str(b4["neu"]))
U = lambda t: datetime.strptime(t, "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
heute = datetime.now(timezone.utc).strftime("%Y-%m-%d")
pruef("faellig: vor 02:00 UTC nein, heute nach dem Lauf nein, morgen ja",
      not NL.neuaufnahme_faellig(d, U(heute + " 01:30")) and not NL.neuaufnahme_faellig(d, U(heute + " 23:00"))
      and NL.neuaufnahme_faellig(d, U(heute + " 02:10") + timedelta(days=1)))
import inspect                                                     # noqa: E402
quelltext = inspect.getsource(NL.neuaufnahme)
pruef("die Neuaufnahme schreibt NIE in die Messbasis (nur stundenkurse_alle.db und markpreis_alle.db)",
      '_pruefe_ziel(ordner, "stundenkurse_alle.db")' in quelltext and '_pruefe_ziel(ordner, "markpreis_alle.db")' in quelltext
      and '"stundenkurse.db"' not in quelltext and "markpreis_historie" not in quelltext)

print("2) S7-5b Preisabgleich vor der Signalmail")
d2 = tempfile.mkdtemp()
c = AB.oeffne(d2)
for sym, bp, paar, fak in (("ZK", "ZKX", "ZKUSDT", 1.0), ("BTC", "BTC", "BTCUSDT", 1.0), ("1000CAT", "CAT", "1000CATUSDT", 1000.0), ("ETH", "ETH", "ETHUSDT", 1.0)):
    c.execute("INSERT INTO signal (symbol, signalstunde, einstieg, ausstieg, vh, stufe_vorlaeufig, hebel_schalter, bitpanda, paar, faktor, kurs) "
              "VALUES (?,?,?,?,?,?,?,?,?,?,?)", (sym, "2026-10-05 10:00", "2026-10-05 11:00", "2026-10-06 11:00", 0.04, 3, 1, bp, paar, fak, 1.0))
c.commit(); c.close()
kurse = lambda: ({"ZKX": 0.0062, "BTC": 84640.0, "CAT": 0.0000301, "ETH": 2677.0}, {"ZKUSDT": 0.0125, "BTCUSDT": 84590.0, "1000CATUSDT": 0.0301})
post, meld = [], []
W = dict(G.lade(), testwoche_bis="")
z = RM.versende(d2, lambda b, t: post.append((b, t)) or True, datetime(2026, 10, 5, 11, 5, tzinfo=timezone.utc), W, kurse=kurse, melden=meld.append)
an = sorted(b.split()[3] for b, _t in post)
pruef("Kollision (ZK, +101,6 %) -> keine Mail, eine Meldung; BTC und CAT (Faktor 1000) -> Mail; ETH ohne Binance-Kurs -> Mail *nicht gegengeprueft*",
      an == ["BTC", "CAT", "ETH"] and z["gesperrt"] == 1 and len(meld) == 1 and "ZKX" in meld[0], "%s · %s · %s" % (an, z, meld[:1]))
t_btc = [t for b, t in post if " BTC " in b][0]
t_eth = [t for b, t in post if " ETH " in b][0]
pruef("die Mail nennt den Abgleich (BTC mit Abweichung, ETH *nicht gegengeprueft*)", "Zuordnung: Bitpanda" in t_btc and "nicht gegengeprueft" in t_eth)
post.clear(); meld.clear()
z = RM.versende(d2, lambda b, t: post.append((b, t)) or True, datetime(2026, 10, 5, 11, 15, tzinfo=timezone.utc), W, kurse=kurse, melden=meld.append)
pruef("zweiter Durchgang: keine Mail und KEINE zweite Meldung fuer ZK", not post and not meld, str(z))
d3 = tempfile.mkdtemp()
c = AB.oeffne(d3)
c.execute("INSERT INTO signal (symbol, signalstunde, einstieg, ausstieg, vh, stufe_vorlaeufig, hebel_schalter, bitpanda, paar, faktor) "
          "VALUES ('ZK','2026-10-05 10:00','2026-10-05 11:00','2026-10-06 11:00',0.04,3,1,'ZKX','ZKUSDT',1.0)")
c.commit(); c.close()
post = []
RM.versende(d3, lambda b, t: post.append((b, t)) or True, datetime(2026, 10, 5, 11, 5, tzinfo=timezone.utc), W,
            kurse=lambda: (_ for _ in ()).throw(ConnectionError("Ticker weg")), melden=meld.append)
pruef("Ticker nicht erreichbar -> die Mail geht mit Vermerk raus (F-2)", len(post) == 1 and "nicht gegengeprueft (Ticker nicht erreichbar)" in post[0][1])

print("3) S7-5c gesperrtes Kuerzel in der Messbasis (ZK, echter Stundenlauf)")
import agent.regel0_rechnung as RK                                 # noqa: E402
import agent.regel0_stundenlauf as SL                              # noqa: E402
B0 = pd.Timestamp(2020, 1, 1)
T = int((pd.Timestamp("2026-06-18 17:00") - B0) / pd.Timedelta(hours=1))
abl, mod = tempfile.mkdtemp(), tempfile.mkdtemp()
alt_s = SL._hebel_schalter
SL._hebel_schalter = lambda ordner: {"ZK": True, "ETH": True}
try:
    SL.betrieb_lauf(RK.DATEN_VORGABE, T, abl, mod, ausgabe=lambda s: None)
finally:
    SL._hebel_schalter = alt_s
cz = sqlite3.connect(os.path.join(abl, "regel0_signale.db"))
zk = cz.execute("SELECT symbol, bitpanda, hebel_schalter FROM signal WHERE symbol='ZK'").fetchall()
cz.close()
post = []
RM.versende(abl, lambda b, t: post.append((b, t)) or True, datetime(2026, 6, 18, 17, 10, tzinfo=timezone.utc), W, kurse=lambda: (None, None))
pruef("ZK-Signal: in der Ablage OHNE Bitpanda-Namen und ohne Schalter, keine Mail", zk and zk[0][1] is None and zk[0][2] is None and not [b for b, _t in post if " ZK " in b],
      "%s · Mails %s" % (zk, [b for b, _t in post]))
for x in (d, d2, d3, abl, mod):
    shutil.rmtree(x, ignore_errors=True)
print("SCHLUSS: %s (%d von %d)" % ("✔ bestanden" if all(ergebnis) else "⛔ NICHT bestanden", sum(ergebnis), len(ergebnis)))
