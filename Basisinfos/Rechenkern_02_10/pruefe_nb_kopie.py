"""Gegenprobe zu nb_kopie_regel0.py (05.10.2026): die Kopie fuer F5 ist vollstaendig und stimmig, die Quelle bleibt unberuehrt.

Alles in Wegwerfordnern (ein nachgebautes Projekt mit data/). Optional --echt: zusaetzlich die echte data/stundenkurse.db des
Desktops NUR LESEND kopieren (Zeitmass fuer 352 MB) - in einen Wegwerfordner, die Quelle wird per Pruefsumme bewacht.
"""
import hashlib
import os
import shutil
import sqlite3
import sys
import tempfile
import threading
import time

WURZEL = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(WURZEL)
sys.path.insert(0, WURZEL)
import nb_kopie_regel0 as K

ok_alle = []


def pruefe(name, bed, info=""):
    ok_alle.append(bool(bed))
    print("  %s  %s%s" % ("OK  " if bed else "FEHL", name, ("  (%s)" % info) if info and not bed else ""), flush=True)


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def projekt(n_kurse=20000):
    p = tempfile.mkdtemp(prefix="r0_kp_")
    d = os.path.join(p, "data")
    os.makedirs(os.path.join(d, "regel0_modelle"))
    c = sqlite3.connect(os.path.join(d, "regel0_signale.db"))
    c.execute("CREATE TABLE lauf (jetzt TEXT PRIMARY KEY)")
    c.execute("CREATE TABLE signal (symbol TEXT, signalstunde TEXT, PRIMARY KEY (symbol, signalstunde))")
    c.executemany("INSERT INTO lauf VALUES (?)", [("2026-10-05 %02d:00" % h,) for h in range(10)])
    c.executemany("INSERT INTO signal VALUES (?,?)", [("S%d" % i, "2026-10-05 01:00") for i in range(30)])
    c.commit(); c.close()
    for name in ("stundenkurse.db", "stundenkurse_alle.db"):
        c = sqlite3.connect(os.path.join(d, name))
        c.execute("CREATE TABLE stundenkurse (symbol TEXT, stunde TEXT, close REAL)")
        c.executemany("INSERT INTO stundenkurse VALUES (?,?,?)", [("X%d" % (i % 50), "2026-10-%02d %02d:00" % (1 + i // 2400 % 28, i % 24), 1.0)
                                                                   for i in range(n_kurse)])
        c.commit(); c.close()
    open(os.path.join(d, "regel0_modelle", "regel0_modell_2026-10.pkl"), "wb").write(os.urandom(9000))
    return p, d


print("Gegenprobe nb_kopie_regel0 - Kopie vollstaendig, stimmig, Quelle unberuehrt")
p, d = projekt()
vorher = {f: (sha(os.path.join(d, f)), os.path.getmtime(os.path.join(d, f))) for f in ("regel0_signale.db", "stundenkurse.db", "stundenkurse_alle.db")}
z = tempfile.mkdtemp(prefix="r0_kz_")
rc = K.kopiere(z, ohne_kurse=False, daten=d, projekt=p, ausgabe=lambda s: None)
nachher = {f: (sha(os.path.join(d, f)), os.path.getmtime(os.path.join(d, f))) for f in vorher}
pruefe("Quelle bitgleich und unberuehrt (Pruefsumme und Aenderungszeit)", vorher == nachher)
pruefe("Kopie vollstaendig: Ablage, beide Kursdateien, Modell, KOPIE_INFO.txt, Rueckgabe 0",
       rc == 0 and all(os.path.exists(os.path.join(z, f)) for f in ("regel0_signale.db", "stundenkurse.db", "stundenkurse_alle.db",
                                                                     "KOPIE_INFO.txt", os.path.join("regel0_modelle", "regel0_modell_2026-10.pkl"))))
c = sqlite3.connect(os.path.join(z, "regel0_signale.db"))
n = c.execute("SELECT COUNT(*) FROM signal").fetchone()[0]
c.close()
info = open(os.path.join(z, "KOPIE_INFO.txt"), encoding="utf-8").read()
pruefe("Inhalt gleich (30 Signale) und die Begleitdatei nennt letzten Lauf, Pruefung und Prüfsumme",
       n == 30 and "letzter lauf: 2026-10-05 09:00" in info and "quick_check ok" in info and "SCHLUSS: vollstaendig" in info, info[-300:])
z2 = tempfile.mkdtemp(prefix="r0_kz2_")
rc2 = K.kopiere(z2, ohne_kurse=True, daten=d, projekt=p, ausgabe=lambda s: None)
pruefe("--ohne-kurse: nur Ablage und Modelle", rc2 == 0 and os.path.exists(os.path.join(z2, "regel0_signale.db"))
       and not os.path.exists(os.path.join(z2, "stundenkurse.db")))
innen = os.path.join(p, "irgendwo")
rc3 = K.kopiere(innen, daten=d, projekt=p, ausgabe=lambda s: None)
pruefe("Ziel im Projekt wird VERWEIGERT, es entsteht nichts", rc3 == 3 and not os.path.exists(innen))
rc4 = K.kopiere(os.path.join(d, "x"), daten=d, projekt=p, ausgabe=lambda s: None)
pruefe("Ziel in data/ wird VERWEIGERT", rc4 == 3 and not os.path.exists(os.path.join(d, "x")))

# ein Schreiber waehrend der Kopie: die Kopie muss in sich stimmig sein (Integritaet ok, Zaehlung = ein Stand)
p5, d5 = projekt(n_kurse=400000)
q = os.path.join(d5, "stundenkurse.db")
c0 = sqlite3.connect(q); n0 = c0.execute("SELECT COUNT(*) FROM stundenkurse").fetchone()[0]; c0.close()
stopp = threading.Event()
geschrieben = [0]


def schreiber():
    c = sqlite3.connect(q, timeout=30)
    while not stopp.is_set():
        c.execute("INSERT INTO stundenkurse VALUES ('NEU', '2026-10-06 00:00', 2.0)"); c.commit()
        geschrieben[0] += 1
        time.sleep(0.001)
    c.close()


th = threading.Thread(target=schreiber); th.start()
time.sleep(0.2)
z5 = tempfile.mkdtemp(prefix="r0_kz5_")
k = K.sichere(q, os.path.join(z5, "stundenkurse.db"))
stopp.set(); th.join()
n5 = k["zeilen"]["stundenkurse"]
pruefe("Schreiber waehrend der Kopie: Integritaet ok und EIN stimmiger Stand (zwischen vorher und nachher)",
       k["quick_check"] == "ok" and n0 <= n5 <= n0 + geschrieben[0] and geschrieben[0] > 0, (k["quick_check"], n0, n5, geschrieben[0]))

if "--echt" in sys.argv and os.path.exists(os.path.join("data", "stundenkurse.db")):
    q = os.path.join("data", "stundenkurse.db")
    h0, m0 = sha(q), os.path.getmtime(q)
    z6 = tempfile.mkdtemp(prefix="r0_kz6_")
    t0 = time.time()
    k = K.sichere(q, os.path.join(z6, "stundenkurse.db"))
    dt = time.time() - t0
    pruefe("echte Desktop-Messbasis (%.0f MB) in %.0f s kopiert, quick_check %s, Quelle unberuehrt" % (
        os.path.getsize(q) / 1e6, dt, k["quick_check"]), k["quick_check"] == "ok" and sha(q) == h0 and os.path.getmtime(q) == m0)
    shutil.rmtree(z6, ignore_errors=True)
for x in (p, z, z2, p5, z5):
    shutil.rmtree(x, ignore_errors=True)
print("%d Pruefungen, %s" % (len(ok_alle), "ALLE BESTANDEN" if all(ok_alle) else "%d FEHLGESCHLAGEN" % ok_alle.count(False)))
