"""Pruefung am SEITENEFFEKT (05.10.2026): die Bitpanda-Bestandsmail (z. B. *Position ohne Watchlist-Eintrag: Concrete*) kommt
hoechstens einmal je Sperrfrist - AUCH ueber einen Neustart hinweg. Am 03.10. kam sie fuenfmal, weil die Sperre nur im Speicher stand.

argv[1]: Kopie der NB-Datenbank (wird ihrerseits in eine Wegwerfdatei kopiert, db.DB_PATH umgebogen). Versand abgefangen, kein Netz.
"""
import os
import shutil
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

os.chdir(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.getcwd())
import api.email_notify as EN
import config as CFG
import database.db as db
import scheduler.background as BG
from importer.bitpanda_bestand import Meldung

ok_alle = []


def pruefe(name, bed, info=""):
    ok_alle.append(bool(bed))
    print("  %s  %s%s" % ("OK  " if bed else "FEHL", name, ("  (%s)" % info) if info and not bed else ""))


kopie = Path(tempfile.mkdtemp(prefix="r0_bm_")) / "nb.db"
shutil.copyfile(sys.argv[1], kopie)
vorher = db.DB_PATH
db.DB_PATH = kopie
post = []
CFG.load_config = lambda *a, **k: {"benachrichtigung": {"email": {"aktiv": True, "empfaenger": "x@y"}}}
EN.send_notification_email = lambda b, t, e, **k: post.append(b) or True
m = Meldung(schluessel="ohne_watchlist_TEST", betreff="Position ohne Watchlist-Eintrag: Test", name="Test", wert="1 EUR",
            status="s", aktion="a")
print("Bestandsmail - Sperrfrist ueber Neustarts (Kopie der NB-Datenbank)")
try:
    r1 = BG._melde_bitpanda_bestand(m)
    r2 = BG._melde_bitpanda_bestand(m)
    pruefe("erste Meldung geht raus, die zweite im selben Lauf nicht", r1 and not r2 and len(post) == 1, (r1, r2, post))
    BG._bitpanda_meldung_gesendet.clear()                              # = Neustart: der Speicher ist leer
    r3 = BG._melde_bitpanda_bestand(m)
    pruefe("⭐ nach einem NEUSTART (Speicher leer) bleibt sie gesperrt - die Datenbank kennt den Versand", not r3 and len(post) == 1)
    BG._bitpanda_meldung_gesendet.clear()
    spaet = datetime.now(timezone.utc) + timedelta(hours=25)
    pruefe("nach Ablauf der Frist (25 h) waere sie wieder frei", not BG._bitpanda_meldung_gesperrt(m, spaet))
    db.DB_PATH = Path(tempfile.mkdtemp()) / "gibt_es_nicht" / "x.db"   # Datenbank nicht oeffenbar
    m2 = Meldung(schluessel="ohne_watchlist_TEST2", betreff="b2", name="n", wert="w", status="s", aktion="a")
    r4, r5 = BG._melde_bitpanda_bestand(m2), BG._melde_bitpanda_bestand(m2)
    pruefe("Datenbank nicht lesbar: die Meldung geht trotzdem raus, der Speicher sperrt die Wiederholung", r4 and not r5, (r4, r5))
finally:
    db.DB_PATH = vorher
    shutil.rmtree(kopie.parent, ignore_errors=True)
print("%d Pruefungen, %s" % (len(ok_alle), "ALLE BESTANDEN" if all(ok_alle) else "%d FEHLGESCHLAGEN" % ok_alle.count(False)))
