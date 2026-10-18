"""Pruefstand E1-E3 (18.10.2026, Schritt7 §23.69): Positionsfuehrung mit dem gemessenen Haltedauer-Fakt - am SEITENEFFEKT.

    python Basisinfos/Rechenkern_02_10/e123_pruefstand.py

Wegwerf-Ablage und Wegwerf-DB auf D: (wegwerf.py), Versand ersetzt (kein Netz, keine Mail). Standard-DB und echte REGEL0-Ablage
werden vorher und nachher verglichen (Groesse + Aenderungszeit) - ein Schreibzugriff faellt dort auf.
  E1  24-h-Erinnerung: Fakt + Liquidationsnaehe je Stufe, kein 'O13' mehr
  E2  72-h-Erinnerung EINMAL: offene Position nach dem Signal -> Mail; keine Position / schon vorher offen -> entfaellt mit Grund;
      erste nicht verschickt -> keine; zu spaet -> keine; Fuehrung wirft -> Mail trotzdem; Abgleich veraltet -> Mail mit Vermerk
  E3  haltedauer_text (Signal / eigene Entscheidung / Grenze 26 h), Zeile in hebelfuehrung.zeilen, lade() und betriebslage-Feld
"""
import os
import sqlite3
import sys
import tempfile
from datetime import datetime, timedelta, timezone

os.chdir(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.getcwd())
import wegwerf  # noqa: E402,F401
import agent.regel0_ablage as AB  # noqa: E402
import agent.regel0_mail as RM  # noqa: E402
import agent.regel0_messstand as MS  # noqa: E402

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:  # noqa: BLE001
    pass
ok_alle = []


def pruefe(name, bed, info=""):
    ok_alle.append(bool(bed))
    print("  %s  %s%s" % ("OK  " if bed else "FEHL", name, ("  (%s)" % info) if info and not bed else ""))


def fuss(p):
    return (os.path.getsize(p), os.path.getmtime(p)) if os.path.exists(p) else None


STD = [os.path.join("data", "tradinginfotool.db"), os.path.join("data", AB.ABLAGE_NAME)]
vorher = {p: fuss(p) for p in STD}

jetzt = datetime(2026, 10, 18, 10, 9, tzinfo=timezone.utc)
F = "%Y-%m-%d %H:00"
frisch = jetzt - timedelta(minutes=10)


def ablage(sym, ein, stufe=3, erste=True, erste_entfallen=False):
    d = tempfile.mkdtemp(prefix="e123_")
    c = AB.oeffne(d)
    aus = (ein + timedelta(hours=24)).strftime(F)
    c.execute("INSERT INTO signal (symbol, signalstunde, einstieg, ausstieg, stufe, hebel_schalter, bitpanda, mail_signal_am, mail_signal_stufe, "
              "mail_erinnerung_am, erinnerung_entfallen_am) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
              (sym, ein.strftime(F), ein.strftime(F), aus, stufe, 1, sym, ein.strftime(F), stufe,
               aus if erste else None, aus if erste_entfallen else None))
    c.commit(); c.close()
    return d


def lauf(d, position=None, fuehrung=None):
    post = []
    z = RM.versende(d, lambda b, t, *a: post.append((b, t)) or True, jetzt=jetzt, werte={}, position=position, fuehrung=fuehrung)
    c = AB.oeffne(d)
    c.row_factory = sqlite3.Row
    r = dict(c.execute("SELECT * FROM signal").fetchone())
    c.close()
    return z, post, r


def bef(pos, veraltet=False):
    return lambda: {"stand": frisch, "veraltet": veraltet, "stunden": 3.0 if veraltet else 0.2, "positionen": pos}


print("E1-E3 Positionsfuehrung mit Haltedauer-Fakt - Pruefung am Seiteneffekt")
# ── E1
print("E1  24-h-Erinnerung")
ein1 = (jetzt - timedelta(hours=25)).replace(minute=0)
for st, liq in ((5, "−20 %"), (3, "−33 %"), (2, None)):
    d = ablage("SEI", ein1, stufe=st, erste=False)
    z, post, r = lauf(d, bef([("SEI", "LONG", (ein1 + timedelta(hours=1, minutes=4)).isoformat())]))
    t = post[0][1] if post else ""
    pruefe("E1  Stufe %d: Mail mit Fakt, ohne O13" % st, len(post) == 1 and "Fakt: Gemessen auf den REGEL0-Einstiegen 2025–26" in t
           and "O13" not in t and "0,3–0,4 % je weiteren Tag" in t and "2024 (Aufwärtsjahr) war es umgekehrt" in t, t[-400:])
    pruefe("E1  Stufe %d: Liquidationsnaehe %s" % (st, liq or "keine Zeile"),
           (liq in t and "binnen 7 Tagen" in t) if liq else ("Liquidation" not in t), t[-300:])
    pruefe("E1  Stufe %d: Vermerk Position bleibt, als verschickt vermerkt" % st, "offene Hebelposition SEI LONG" in t and r["mail_erinnerung_am"])
    wegwerf.aufraeumen(d)

# ── E2
print("E2  72-h-Erinnerung")
ein = (jetzt - timedelta(hours=73)).replace(minute=0)            # Einstieg + 1 h + 72 h = 09:00 <= 10:09
nach = (ein + timedelta(hours=1, minutes=5)).replace(tzinfo=timezone.utc).isoformat()
d = ablage("SEI", ein, stufe=5)
z, post, r = lauf(d, bef([("SEI", "LONG", nach)]), fuehrung=lambda r: "SEI - Hebel 5,0x LONG · HALTEN\n   Liquidation  etwa 0,20 EUR")
t = post[0][1] if post else ""
pruefe("E2-A  offene Position nach dem Signal -> genau EINE Mail", len(post) == 1 and z["erinnerung"] == 1, str(z))
pruefe("E2-A  Betreff nennt Haltedauer und Regel", post and "SEI 5x seit 72 h offen (Regel 24 h)" in post[0][0], post[0][0] if post else "")
pruefe("E2-A  Text: Handlung, Fakt, Liquidationsnaehe 5x, Fuehrung, Vermerk, einmalig",
       all(s in t for s in ("Handlung: schliessen", "Fakt: Gemessen", "bei 5x liegt die Liquidation etwa bei −20 %", "Fuehrung (H15):",
                             "Liquidation  etwa 0,20 EUR", "Position: offene Hebelposition SEI LONG", "EINMAL je Signal")), t)
pruefe("E2-A  vermerkt mail_erinnerung72_am, erste unberuehrt", r["mail_erinnerung72_am"] == jetzt.strftime("%Y-%m-%d %H:%M")
       and r["erinnerung72_entfallen_am"] is None and r["mail_erinnerung_am"], str(r))
z2, post2, _ = lauf(d, bef([("SEI", "LONG", nach)]), fuehrung=lambda r: "x")
pruefe("E2-A  naechster Lauf: nichts doppelt", not post2 and z2["erinnerung"] == 0, str(z2))
wegwerf.aufraeumen(d)

d = ablage("SEI", ein)
z, post, r = lauf(d, bef([("NEAR", "LONG", nach)]))
pruefe("E2-B  keine offene Position -> keine Mail, entfaellt mit Grund", not post and r["erinnerung72_entfallen_am"]
       and "keine offene Hebelposition SEI" in (r["erinnerung72_grund"] or "") and r["mail_erinnerung72_am"] is None, str(r))
z2, post2, _ = lauf(d, bef([("SEI", "LONG", nach)]))
pruefe("E2-B  entfallen ist endgueltig", not post2, str(post2)[:100])
wegwerf.aufraeumen(d)

d = ablage("SEI", ein)
z, post, r = lauf(d, bef([("SEI", "LONG", "2026-10-09T04:38:53+00:00")]))
pruefe("E2-C  Position schon VOR dem Signal offen -> entfaellt (eigene Entscheidung)", not post
       and "eigene Entscheidung" in (r["erinnerung72_grund"] or ""), str(r))
wegwerf.aufraeumen(d)

d = ablage("SEI", ein, erste=False, erste_entfallen=True)
z, post, r = lauf(d, bef([("SEI", "LONG", nach)]))
pruefe("E2-D  erste Erinnerung nicht verschickt -> keine zweite", not post and r["mail_erinnerung72_am"] is None
       and r["erinnerung72_entfallen_am"] is None, str(r))
wegwerf.aufraeumen(d)

d = ablage("SEI", ein - timedelta(hours=7))
z, post, r = lauf(d, bef([("SEI", "LONG", nach)]))
pruefe("E2-E  mehr als 6 h zu spaet (Stillstand) -> keine Mail", not post and r["mail_erinnerung72_am"] is None, str(r))
wegwerf.aufraeumen(d)
d = ablage("SEI", ein - timedelta(hours=5))   # die Grenze rechnet minutengenau wie bei der ersten
z, post, r = lauf(d, bef([("SEI", "LONG", nach)]))
pruefe("E2-E  5 h spaet -> Mail noch (Rand wie bei der ersten)", len(post) == 1, str(z))
wegwerf.aufraeumen(d)


def _wirft(_r=None):
    raise RuntimeError("DB gesperrt")


d = ablage("SEI", ein)
z, post, r = lauf(d, bef([("SEI", "LONG", nach)]), fuehrung=_wirft)
pruefe("E2-F  Fuehrung wirft -> Mail trotzdem, ohne Fuehrungsblock", len(post) == 1 and "Fuehrung (H15)" not in post[0][1], str(z))
wegwerf.aufraeumen(d)
d = ablage("SEI", ein)
z, post, r = lauf(d, bef([], veraltet=True))
pruefe("E2-G  Abgleich veraltet -> Mail mit Vermerk *unbekannt*", len(post) == 1 and "Positionsstand unbekannt" in post[0][1], str(z))
wegwerf.aufraeumen(d)
d = ablage("SEI", ein)
z, post, r = lauf(d, None)
pruefe("E2-H  ohne position-Lieferant -> Mail (wie die erste)", len(post) == 1, str(z))
wegwerf.aufraeumen(d)
d = ablage("SEI", jetzt.replace(minute=0) - timedelta(hours=72))  # Einstieg+1h+72h = 11:00 > 10:09
z, post, r = lauf(d, bef([("SEI", "LONG", nach)]))
pruefe("E2-I  vor 72 h -> noch nichts", not post and r["erinnerung72_entfallen_am"] is None, str(r))
wegwerf.aufraeumen(d)

# ── E3
print("E3  Haltedauer in der Fuehrung")
d = ablage("BTC", ein)
h1 = MS.haltedauer_text(d, "BTC", nach, jetzt)
h2 = MS.haltedauer_text(d, "BTC", "2026-10-09T04:38:53+00:00", jetzt)
h3 = MS.haltedauer_text(d, "BTC", (ein + timedelta(hours=27)).isoformat(), jetzt)
h4 = MS.haltedauer_text(d, "ETH", nach, jetzt)
h5 = MS.haltedauer_text(d, "btc", (ein + timedelta(hours=2)).replace(tzinfo=None), (ein + timedelta(hours=12)).replace(tzinfo=None))
pruefe("E3  nach dem Signal: 'seit 72 h offen (Regel 24 h, überschritten) · REGEL0-Signal 15.10. 09:00'",
       h1 == "seit 72 h offen (Regel 24 h, überschritten) · REGEL0-Signal %s" % ein.strftime("%d.%m. %H:%M"), h1)
pruefe("E3  BTC seit 09.10. -> eigene Entscheidung, 222 h", h2 == "seit 222 h offen · eigene Entscheidung (kein REGEL0-Signal in den 26 h davor)", h2)
pruefe("E3  27 h nach dem Signal -> eigene Entscheidung (Grenze 26 h wie trades)", "eigene Entscheidung" in (h3 or ""), h3)
pruefe("E3  anderes Asset -> eigene Entscheidung", "eigene Entscheidung" in (h4 or ""), h4)
pruefe("E3  datetime-Eingabe + Kleinschreibung + unter 24 h: 'seit 10 h offen (Regel 24 h)', ohne 'überschritten'",
       h5 == "seit 10 h offen (Regel 24 h) · REGEL0-Signal %s" % ein.strftime("%d.%m. %H:%M"), h5)
pruefe("E3  ohne Ablage / ohne Eroeffnung -> None bzw. eigene", MS.haltedauer_text(d, "BTC", None, jetzt) is None
       and "eigene" in MS.haltedauer_text(os.path.join(d, "fehlt"), "BTC", nach, jetzt))
import agent.hebelfuehrung as HF  # noqa: E402
zz = HF.zeilen({"symbol": "BTC", "hebel": 2.0, "richtung": "LONG", "empfehlung": "HALTEN", "haltedauer_text": h2})
pruefe("E3  hebelfuehrung.zeilen: Zeile 'Haltedauer' auch ohne Einstand", any(x.startswith("   Haltedauer   seit 222 h") for x in zz), str(zz))

# lade() + betriebslage + Scheduler-Lieferant gegen eine Wegwerf-DB mit einer offenen Position (Standard-DB unberuehrt)
import database.db as db  # noqa: E402
import agent.regel0_nachlader as NL  # noqa: E402
import agent.betriebslage as BL  # noqa: E402
import scheduler.background as BG  # noqa: E402
w = tempfile.mkdtemp(prefix="e123_db_")
alt_db, alt_nl = db.DB_PATH, NL.DATEN_VORGABE
db.DB_PATH = __import__("pathlib").Path(w) / "t.db"
NL.DATEN_VORGABE = d
try:
    c = db.get_connection()
    db.init_db(c)
    c.execute("INSERT INTO hebel_positions (symbol, richtung, status, eroeffnet_am, hebel_effektiv, positionswert_eur, kreditbetrag_eur, "
              "eigenkapital_eur, positionsmenge, letzte_transaktion_unix_timestamp) VALUES ('BTC','LONG','offen',?,2.0,1000,500,500,0.01,0)", (nach,))
    c.commit()
    tr = HF.lade(c, wallet=False, jetzt=jetzt)
    pruefe("E3  lade(): Feld haltedauer_text gesetzt", tr and (tr[0].get("haltedauer_text") or "").startswith("seit 72 h offen (Regel 24 h"), str(tr[0] if tr else tr)[:300])
    pruefe("E3  lade() -> zeilen(): Haltedauer im Mailtext", any("Haltedauer   seit 72 h" in x for x in HF.zeilen(tr[0])))
    bl = BL.hebel_fuehrung_jetzt(c)
    pruefe("E3  betriebslage.hebel_fuehrung_jetzt: Feld haltedauer (Statusseite)", bl and "REGEL0-Signal" in (bl[0].get("haltedauer") or ""), str(bl)[:300])
    c.close()
    fz = BG._regel0_fuehrung_zeilen({"symbol": "BTC", "bitpanda": "BTC"})
    pruefe("E2  Scheduler-Lieferant _regel0_fuehrung_zeilen liefert die H15-Zeilen", fz and "BTC - Hebel" in fz and "Haltedauer" in fz, str(fz)[:200])
    pruefe("E2  Lieferant: kein Asset offen -> None", BG._regel0_fuehrung_zeilen({"symbol": "XRP", "bitpanda": "XRP"}) is None)
finally:
    db.DB_PATH, NL.DATEN_VORGABE = alt_db, alt_nl
wegwerf.aufraeumen(w)
wegwerf.aufraeumen(d)

src = open(os.path.join("remote", "server.py"), encoding="utf-8").read()
pruefe("E3  Statusseite renderHebel zeigt p.haltedauer", "if (p.haltedauer) x +=" in src)
pruefe("E2  Scheduler reicht fuehrung= an versende", "fuehrung=_regel0_fuehrung_zeilen" in open(os.path.join("scheduler", "background.py"), encoding="utf-8").read())
nachher = {p: fuss(p) for p in STD}
pruefe("Standard-DB und echte REGEL0-Ablage unberuehrt", vorher == nachher, str((vorher, nachher)))
print("%d Pruefungen, %s" % (len(ok_alle), "ALLE BESTANDEN" if all(ok_alle) else "%d FEHLGESCHLAGEN" % ok_alle.count(False)))
