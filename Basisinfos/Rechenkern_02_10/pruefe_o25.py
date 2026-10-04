"""Pruefung am SEITENEFFEKT (04.10.2026, O25 M-a bis M-f): der neue Aufbau der REGEL0-Signalmail.

Wegwerf-Ablage, Versand abgefangen (kein Netz, keine Mail), Standard-DB unberuehrt.
Optional argv[1]: Kopie der NB-Datenbank - dann laeuft der Spot-Hinweis (M-f) gegen eine KOPIE dieser Kopie (db.DB_PATH umgebogen).
"""
import os
import shutil
import sqlite3
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

os.chdir(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.getcwd())
import agent.regel0_ablage as AB
import agent.regel0_groesse as G
import agent.regel0_llm as LLM
import agent.regel0_mail as RM
from api.email_notify import html_mit_bildern

ok_alle = []


def pruefe(name, bed, info=""):
    ok_alle.append(bool(bed))
    print("  %s  %s%s" % ("OK  " if bed else "FEHL", name, ("  (%s)" % str(info)[:300]) if info and not bed else ""))


ERG = {"markt": {"urteil": "neutral", "begruendung": "Umfeld ruhig. Zweiter Satz.", "gegengrund": "Aktien teuer."},
       "trader": {"urteil": "spricht_dagegen", "stimmen": ["spricht_dagegen"] * 5, "begruendung": "Umsatz fehlt. Mehr Text.",
                  "gegengrund": "Trend aufwaerts."}}
jetzt = datetime(2026, 10, 5, 11, 9, tzinfo=timezone.utc)


def ablage():
    d = tempfile.mkdtemp(prefix="r0_o25p_")
    c = AB.oeffne(d)
    c.execute("INSERT INTO signal (symbol, signalstunde, einstieg, ausstieg, vh, stufe_vorlaeufig, p2, p3, p5, hebel_schalter, bitpanda, kurs, "
              "kurs_markt, paar, faktor) VALUES ('KAIA','2026-10-05 10:00','2026-10-05 11:00','2026-10-06 11:00',0.0415,5,0.001,0.001,0.013,1,"
              "'KAIA',0.0375,'spot','KAIAUSDT',1.0)")
    c.commit(); c.close()
    return d


post = []        # gemeinsam fuer beide Versandwege, je Lauf geleert


def lauf(**kw):
    d = ablage()
    post.clear()
    z = RM.versende(d, lambda *a: post.append(("alt",) + a) or True, jetzt=jetzt, werte=G.lade(),
                    kurse=lambda: ({"KAIA": 0.0376}, {"KAIAUSDT": 0.0375}, {"KAIA": 0.0321}), bild=lambda r: b"PNG", **kw)
    shutil.rmtree(d, ignore_errors=True)
    return z, list(post)


print("O25 - neuer Aufbau der REGEL0-Signalmail, Pruefung am Seiteneffekt")
z, post = lauf(pruefung=lambda r: LLM.mail_teile(ERG), spot=lambda r: "Die alte Spot-Kette hat zu KAIA gemailt",
               senden_html=lambda b, t, h, bi: post.append(("html", b, t, h, bi)) or True)
pruefe("HTML-Weg: genau eine Mail, mit Text, HTML und Bild", z["signal"] == 1 and len(post) == 1 and post[0][0] == "html"
       and post[0][3] and post[0][4] and post[0][4][0]["png"] == b"PNG", post)
_, b, t, h, bi = post[0]
pos = [t.find(x) for x in ("1  WAS ZU TUN IST", "2  CHART", "3  EINSCHÄTZUNG", "4  BEGRÜNDUNG DER ROLLEN", "5  TECHNIK")]
pruefe("M-a Reihenfolge: Handlung, Chart, Einschaetzung, Begruendung, Technik", all(p >= 0 for p in pos) and pos == sorted(pos), pos)
oben = t[:pos[4]]
# die Ortszeit aus der Uhr des Geraets - Einstieg = Schluss der Einstiegsstunde 11:00 UTC, also 12:00 UTC (nie fest eintragen:
# am 04.10. stand hier 13:00, richtig ist in der Sommerzeit 14:00)
_ein_lokal = datetime(2026, 10, 5, 12, 0, tzinfo=timezone.utc).astimezone().strftime("%H:%M")
pruefe("M-b/M-c: Handlungsteil in EUR und Ortszeit (heute/morgen) - kein USD, kein UTC vor der Technik",
       "Kurs jetzt      0,0321 EUR" in t and "Liquidation     bei etwa" in t and ("heute %s" % _ein_lokal) in t
       and ("morgen %s" % _ein_lokal) in t
       and "USD" not in oben and "UTC" not in oben, oben[:600])
pruefe("M-e: Fachbegriffe (v-dach, regel0_betrieb.yaml, D2) nur in der Technik",
       all(x not in oben for x in ("v-dach", "regel0_betrieb.yaml", "(D2)")) and all(x in t[pos[4]:] for x in ("v-dach", "regel0_betrieb.yaml", "D2")))
pruefe("Rollen: kurz in der Einschaetzung (5 von 5), ausfuehrlich in der Begruendung (Gegengrund, Fassung, Messstand)",
       "spricht dagegen (5 von 5) - Umsatz fehlt." in t and "Gegengrund: Trend aufwaerts." in t and "Messstand" in t)
pruefe("M-f: der Spot-Hinweis steht in der Einschaetzung", "Achtung" in t[pos[2]:pos[3]] and "alte Spot-Kette" in t)
pruefe("M-d: HTML hat die fuenf Abschnitte, gegliederte Begruendung (kein <pre>) und den Bildplatz",
       all(x in h for x in ("1 · Was zu tun ist", "2 · Chart", "3 · Einschätzung", "4 · Begründung der Rollen", "5 · Technik"))
       and "<pre" not in h and "{{BILD:0}}" in h and "<b>Trader</b>" in h)
fertig = html_mit_bildern(h, "<img src=x>")
pruefe("M-d: der Versand setzt das Bild AN DEN Bildplatz und laesst keinen Platzhalter stehen",
       "{{BILD" not in fertig and fertig.find("<img src=x>") < fertig.find("3 · Einschätzung"))

z, post = lauf(pruefung=lambda r: (_ for _ in ()).throw(RuntimeError("Probe")), spot=lambda r: (_ for _ in ()).throw(RuntimeError("x")),
               senden_html=lambda b, t, h, bi: post.append(("html", b, t, h, bi)) or True)
pruefe("P-8: Pruefblock und Spot-Hinweis scheitern - die Mail geht trotzdem, *nicht verfuegbar*, kein Hinweis",
       z["signal"] == 1 and "nicht verfuegbar (RuntimeError)" in post[0][2] and "Achtung" not in post[0][2])
z, post = lauf(pruefung=lambda r: ["PRUEFUNG-PROBE"])
pruefe("alter Weg ohne senden_html und alte Zeilenliste bleiben moeglich", z["signal"] == 1 and post[0][0] == "alt"
       and "PRUEFUNG-PROBE" in post[0][2], post)
z, post = lauf(senden_html=lambda b, t, h, bi: False)
pruefe("gescheiterter HTML-Versand wird NICHT als verschickt vermerkt", z["signal"] == 0 and z["fehlgeschlagen"] == 1, z)

if len(sys.argv) > 1:
    import database.db as db
    import scheduler.background as BG
    kopie = Path(tempfile.mkdtemp(prefix="r0_o25nb_")) / "nb.db"
    shutil.copyfile(sys.argv[1], kopie)
    c = sqlite3.connect(kopie)
    c.execute("INSERT INTO signals (symbol, created_at, pipeline_version, action, instrument, quelle_kette, mail_versand, mail_versand_am, gate_passed, facts_json) "
              "VALUES ('ZZTEST', ?, '1', 'NACHKAUFEN', 'spot', 'rollen', 'zugestellt', ?, 1, '{}')",
              ((datetime.now(timezone.utc) - timedelta(hours=2)).isoformat(),) * 2)
    c.execute("INSERT INTO signals (symbol, created_at, pipeline_version, action, instrument, quelle_kette, mail_versand, mail_versand_am, gate_passed, facts_json) "
              "VALUES ('ZZALT', ?, '1', 'NACHKAUFEN', 'spot', 'rollen', 'zugestellt', ?, 1, '{}')",
              ((datetime.now(timezone.utc) - timedelta(hours=30)).isoformat(),) * 2)
    c.commit(); c.close()
    vorher = db.DB_PATH
    db.DB_PATH = kopie
    try:
        h1 = BG._regel0_spot_hinweis({"bitpanda": "ZZTEST"})
        h2 = BG._regel0_spot_hinweis({"bitpanda": "ZZALT"})
        h3 = BG._regel0_spot_hinweis({"bitpanda": "GIBTSNICHT"})
    finally:
        db.DB_PATH = vorher
    pruefe("M-f gegen die NB-Kopie: Spot-Mail vor 2 h -> Hinweis; vor 30 h -> keiner; ohne Spot-Mail -> keiner",
           h1 and "NACHKAUFEN" in h1 and "ZZTEST" in h1 and h2 is None and h3 is None, (h1, h2, h3))
    shutil.rmtree(kopie.parent, ignore_errors=True)
print("%d Pruefungen, %s" % (len(ok_alle), "ALLE BESTANDEN" if all(ok_alle) else "%d FEHLGESCHLAGEN" % ok_alle.count(False)))
