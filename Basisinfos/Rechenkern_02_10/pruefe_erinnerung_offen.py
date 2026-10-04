"""Pruefung am SEITENEFFEKT (04.10.2026): die REGEL0-Ausstiegserinnerung geht nur bei OFFENER Hebelposition.

Wegwerf-Ablage im Temp-Ordner, Versand ersetzt (kein Netz, keine Mail), Standard-DB unberuehrt. Fuenf Faelle:
  A  Abgleich frisch, keine offene Position      -> KEINE Mail, erinnerung_entfallen_am gesetzt, Grund als Fakt
  B  offene LONG-Position im Asset               -> Mail mit Vermerk *offene Hebelposition*
  C  Abgleich veraltet                           -> Mail mit Vermerk *Positionsstand unbekannt*
  D  Positionsstand wirft                        -> Mail mit Vermerk *nicht lesbar*
  E  ohne ``position``                           -> altes Verhalten (Mail)
Dazu: der naechste Lauf schickt fuer A NICHTS nach (entfallen ist endgueltig) und fuer B nichts doppelt.
Optional argv[1]: Kopie der NB-Datenbank - dann laeuft auch ``_regel0_positionsstand`` gegen diese KOPIE (db.DB_PATH umgebogen).
"""
import os
import shutil
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

os.chdir(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.getcwd())
import agent.regel0_ablage as AB
import agent.regel0_mail as RM

ok_alle = []


def pruefe(name, bed, info=""):
    ok_alle.append(bool(bed))
    print("  %s  %s%s" % ("OK  " if bed else "FEHL", name, ("  (%s)" % info) if info and not bed else ""))


jetzt = datetime(2026, 10, 4, 14, 9, tzinfo=timezone.utc)
aus = (jetzt - timedelta(hours=1)).strftime("%Y-%m-%d %H:00")
ein = (jetzt - timedelta(hours=25)).strftime("%Y-%m-%d %H:00")
frisch = jetzt - timedelta(minutes=10)


def ablage(sym):
    d = tempfile.mkdtemp(prefix="r0_erin_")
    c = AB.oeffne(d)
    c.execute("INSERT INTO signal (symbol, signalstunde, einstieg, ausstieg, stufe, hebel_schalter, bitpanda, mail_signal_am, "
              "mail_signal_stufe) VALUES (?,?,?,?,?,?,?,?,?)", (sym, ein, ein, aus, 3, 1, sym, ein, 3))
    c.commit(); c.close()
    return d


def lauf(d, position, kennz):
    post = []
    z = RM.versende(d, lambda b, t, *a: post.append((b, t)) or True, jetzt=jetzt, werte={}, position=position)
    c = AB.oeffne(d)
    r = c.execute("SELECT mail_erinnerung_am, erinnerung_entfallen_am, erinnerung_grund FROM signal").fetchone()
    c.close()
    return z, post, r


print("REGEL0-Erinnerung nur bei offener Hebelposition - Pruefung am Seiteneffekt")
d = ablage("SEI")
z, post, r = lauf(d, lambda: {"stand": frisch, "veraltet": False, "stunden": 0.2, "positionen": [("NEAR", "LONG", "2026-10-03")]}, "A")
pruefe("A  keine offene Position -> keine Mail", not post and z["entfallen"] == 1, str(z))
pruefe("A  entfallen als Fakt vermerkt (Zeit + Grund), Erinnerung NICHT als verschickt", r[0] is None and r[1] and "keine offene" in (r[2] or ""), str(r))
z2, post2, _ = lauf(d, lambda: {"stand": frisch, "veraltet": False, "stunden": 0.2, "positionen": [("SEI", "LONG", "x")]}, "A2")
pruefe("A  naechster Lauf schickt NICHTS nach (auch wenn jetzt eine Position da waere)", not post2 and z2["entfallen"] == 0, str(z2))
shutil.rmtree(d, ignore_errors=True)

d = ablage("SEI")
z, post, r = lauf(d, lambda: {"stand": frisch, "veraltet": False, "stunden": 0.2, "positionen": [("SEI", "LONG", "2026-10-03T14:02:00")]}, "B")
pruefe("B  offene Position -> Mail mit Vermerk", len(post) == 1 and "offene Hebelposition SEI LONG" in post[0][1] and r[0], str(post)[:200])
z2, post2, _ = lauf(d, lambda: {"stand": frisch, "veraltet": False, "stunden": 0.2, "positionen": [("SEI", "LONG", "x")]}, "B2")
pruefe("B  nicht doppelt", not post2, str(post2)[:120])
shutil.rmtree(d, ignore_errors=True)

d = ablage("SEI")
z, post, r = lauf(d, lambda: {"stand": frisch - timedelta(hours=3), "veraltet": True, "stunden": 3.2, "positionen": []}, "C")
pruefe("C  Abgleich veraltet -> Mail mit Vermerk *unbekannt*", len(post) == 1 and "Positionsstand unbekannt" in post[0][1] and z["entfallen"] == 0, str(post)[:200])
shutil.rmtree(d, ignore_errors=True)

d = ablage("SEI")


def _wirft():
    raise RuntimeError("Datenbank gesperrt")


z, post, r = lauf(d, _wirft, "D")
pruefe("D  Positionsstand wirft -> Mail mit Vermerk *nicht lesbar*", len(post) == 1 and "nicht lesbar" in post[0][1], str(post)[:200])
shutil.rmtree(d, ignore_errors=True)

d = ablage("SEI")
z, post, r = lauf(d, None, "E")
pruefe("E  ohne position -> altes Verhalten", len(post) == 1 and "Position:" not in post[0][1], str(post)[:200])
shutil.rmtree(d, ignore_errors=True)

pruefe("Abgleich nie gelaufen -> unbekannt (nicht *keine Position*)", RM.position_stand({"bitpanda": "SEI"}, {"stand": None, "veraltet": False,
                                                                                                         "positionen": []})[0] is None)
pruefe("SHORT zaehlt nicht als offene LONG-Position", RM.position_stand({"bitpanda": "SEI"}, {"stand": frisch, "veraltet": False,
                                                                                              "positionen": [("SEI", "SHORT", "x")]})[0] is False)

if len(sys.argv) > 1:
    import database.db as db
    import scheduler.background as BG
    kopie = Path(tempfile.mkdtemp(prefix="r0_nbkopie_")) / "nb.db"
    shutil.copyfile(sys.argv[1], kopie)
    vorher = db.DB_PATH
    db.DB_PATH = kopie
    try:
        bef = BG._regel0_positionsstand()
    finally:
        db.DB_PATH = vorher
    print("  NB-Kopie: Stand %s, veraltet %s, offene Positionen %s" % (bef["stand"], bef["veraltet"], bef["positionen"]))
    pruefe("NB-Kopie lesbar: Befund vollstaendig", set(bef) == {"stand", "veraltet", "stunden", "positionen"}, str(bef))
    shutil.rmtree(kopie.parent, ignore_errors=True)
print("%d Pruefungen, %s" % (len(ok_alle), "ALLE BESTANDEN" if all(ok_alle) else "%d FEHLGESCHLAGEN" % ok_alle.count(False)))
