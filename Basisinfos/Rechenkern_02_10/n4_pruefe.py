"""N4 - Pruefung des Laeufers VOR dem ersten echten Aufruf (Nutzer 05.10.: *den ersten Teil der Pruefung und Messungen immer sauber
durchtesten, damit die langen Laeufe ohne Probleme und Fehler beendet werden*).

    python Basisinfos/Rechenkern_02_10/n4_pruefe.py

Alles mit dem PLATZHALTER-Client (kein Gemini-Aufruf) in Wegwerf-Ablagen. Proben:
  P1 Anker: Pruefsumme, Bestaetigungsmenge ausgesperrt, Reihenfolge fest und abwechselnd je Jahr
  P2 ganzer Lauf mit 3 % Netzfehlern und 3 % Formfehlern: vollstaendig, lueckenlos, keine Doppel, Netzfehler nie als Stimme gespeichert
  P3 HARTE ABBRUECHE (Prozess getoetet wie bei Absturz oder Stromausfall) und Fortsetzen, bis fertig: dieselben Pruefungen
  P4 Kontingent: Deckel je Schluessel, Wechsel 2 -> 1, Erschoepfung gemeldet, Ende ohne Warten, Fortsetzen am naechsten Tag
  P5 geaenderte Fassung -> Laeufer verweigert
  P6 Doppelstart -> der zweite Laeufer tut nichts
  P7 Platzhalter nie in die echte Ablage
  P8 Ende zu Ende: Orakel-Urteile -> Bericht TRAEGT; Zufalls-Urteile -> TRAEGT NICHT bzw. STOP-ANPASSEN
  P9 Standard-DB und Messbasen unberuehrt (Aenderungszeit)
"""
import os
import random
import sqlite3
import subprocess
import sys
import tempfile
import time

HIER = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.dirname(os.path.dirname(HIER))
LAEUFER = os.path.join(HIER, "n4_rueckspiel.py")
AUSW = os.path.join(HIER, "n4_auswertung.py")
ERG = []
GROSS = {"N4_DECKEL_2": "1000000", "N4_DECKEL_1": "1000000"}


def ok(name, b, det=""):
    ERG.append((name, bool(b), det))
    print("%s  %s  %s" % ("OK  " if b else "FEHL", name, det), flush=True)


def lauf(ablage, modus="zufall", env=None, extra=(), warte=True, timeout=1800):
    e = {**os.environ, "PYTHONIOENCODING": "utf-8", **GROSS, **(env or {})}
    cmd = [sys.executable, LAEUFER, "lauf", "--ablage", ablage, "--platzhalter", modus, "--kein-warten", *extra]
    if not warte:
        return subprocess.Popen(cmd, env=e, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return subprocess.run(cmd, env=e, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout)


def pruefe_ablage(ablage):
    c = sqlite3.connect(ablage)
    n = c.execute("SELECT COUNT(*) FROM eingabe").fetchone()[0]
    gest = c.execute("SELECT v FROM meta WHERE k='t_gestoppt'").fetchone()
    soll = {"K_a": (50, 1), "K_b": (100, 5), "R_w": (100, 5), "R_v": (100, 5)}
    fehler = []
    leer = {r[0] for r in c.execute("SELECT pos FROM eingabe WHERE eingabe IS NULL")}
    for teil, (m, k) in soll.items():
        for pos in range(m):
            if pos in leer:
                if c.execute("SELECT COUNT(*) FROM stimme WHERE teil=? AND pos=?", (teil, pos)).fetchone()[0]:
                    fehler.append((teil, pos, "Aufruf ohne Eingabe")); break
                continue
            st = [r[0] for r in c.execute("SELECT stimme FROM stimme WHERE teil=? AND pos=? ORDER BY stimme", (teil, pos))]
            if st != list(range(k)):
                fehler.append((teil, pos, st)); break
    t_max = int(gest[0].replace("ENTSCHEID_T", "")) if gest else n
    for pos in range(t_max):
        if pos in leer:
            continue
        st = [r[0] for r in c.execute("SELECT stimme FROM stimme WHERE teil='T' AND pos=? ORDER BY stimme", (pos,))]
        if st != list(range(5)):
            fehler.append(("T", pos, st)); break
    dopp = c.execute("SELECT COUNT(*) FROM (SELECT teil,pos,stimme FROM stimme GROUP BY 1,2,3 HAVING COUNT(*)>1)").fetchone()[0]
    netz = c.execute("SELECT COUNT(*) FROM stimme WHERE fehler LIKE '%Netz%'").fetchone()[0]
    ung = c.execute("SELECT COUNT(*) FROM stimme WHERE gueltig=0").fetchone()[0]
    fertig = c.execute("SELECT COUNT(*) FROM ereignis WHERE art='FERTIG'").fetchone()[0]
    c.close()
    return fehler, dopp, netz, ung, fertig, gest


tmp = tempfile.mkdtemp(prefix="n4_pruefe_")
mt = {p: os.path.getmtime(os.path.join(PROJ, "data", p)) for p in ("tradinginfotool.db", "stundenkurse.db", "stundenkurse_alle.db")
      if os.path.exists(os.path.join(PROJ, "data", p))}

# P1
sys.path.insert(0, HIER)
import n4_rueckspiel as N  # noqa: E402
a = N.lade_anker()
r1, r2 = N.reihenfolge(a), N.reihenfolge(a)
ok("P1 Anker: 1.000, Pruefsumme wie Beleg, Reihenfolge fest", len(a) == 1000 and r1["std"].tolist() == r2["std"].tolist())
ok("P1 Reihenfolge abwechselnd 2025/2026 (je Blick gleich stark)", r1["jahr"].tolist()[:8] == [2025, 2026] * 4
   and int((r1["jahr"][:250] == 2025).sum()) == 125)
import pandas as pd  # noqa: E402
b = pd.read_csv(N.BEST_DATEI, sep=";", dtype={"symbol": str})
falsch = os.path.join(tmp, "falsch.csv")
pd.concat([a.head(5), b.head(1)]).to_csv(falsch, sep=";", index=False)
try:
    N.lade_anker(falsch); gesperrt = False
except SystemExit:
    gesperrt = True
ok("P1 ein Anker der Bestaetigungsmenge in der Liste -> Abbruch", gesperrt)

# P2
ab2 = os.path.join(tmp, "p2.db")
t0 = time.time()
r = lauf(ab2, env={"N4_PH_NETZ": "0.03", "N4_PH_UNGUELTIG": "0.03"})
f, dopp, netz, ung, fertig, gest = pruefe_ablage(ab2)
ok("P2 ganzer Lauf mit 3 %% Netz- und 3 %% Formfehlern: fertig, lueckenlos, keine Doppel (%.0f s)" % (time.time() - t0),
   r.returncode == 0 and fertig == 1 and not f and dopp == 0, "%s %s gestoppt=%s" % (f[:1], r.stdout[-300:] if r.returncode else "", gest))
ok("P2 Netzfehler nie als Stimme gespeichert, Formfehler als ungueltige Stimme (wie im Betrieb)", netz == 0 and ung > 0, "ungueltig %d" % ung)

# P3 harte Abbrueche
ab3 = os.path.join(tmp, "p3.db")
rng = random.Random(7)
abbrueche = mitten = 0
env3 = {"N4_PH_PAUSE": "0.003", "N4_HERZ_TOT": "1", "N4_PH_NETZ": "0.02", "N4_PH_UNGUELTIG": "0.02"}


def stimmen3():
    if not os.path.exists(ab3):
        return 0
    c_ = sqlite3.connect(ab3)
    try:
        return c_.execute("SELECT COUNT(*) FROM stimme").fetchone()[0]
    except sqlite3.Error:
        return 0
    finally:
        c_.close()


t0 = time.time()
while time.time() - t0 < 2400:
    vorher = stimmen3()
    p = lauf(ab3, env=env3, warte=False)
    time.sleep(rng.uniform(5.0, 30.0))                        # lang genug, dass MITTEN im Lauf getoetet wird (Starten dauert einige s)
    if p.poll() is None:
        p.kill(); p.wait(); abbrueche += 1
        mitten += stimmen3() > vorher                          # dieser Abbruch kam nach echtem Fortschritt
        time.sleep(1.2)                                       # Herzschlag-Grenze in der Pruefung: 1 s
    else:
        break
r = lauf(ab3, env=env3)                                       # letzter Lauf zu Ende
f, dopp, netz, ung, fertig, gest = pruefe_ablage(ab3)
ok("P3 %d harte Abbrueche (Prozess getoetet), davon %d MITTEN im Lauf, und Fortsetzen: fertig, lueckenlos, keine Doppel" % (abbrueche, mitten),
   mitten >= 10 and fertig >= 1 and not f and dopp == 0, "%s %s" % (f[:1], r.stdout[-200:]))
c = sqlite3.connect(ab3)
starts = c.execute("SELECT COUNT(*) FROM ereignis WHERE art='START'").fetchone()[0]
eing = c.execute("SELECT COUNT(DISTINCT summe) FROM eingabe").fetchone()[0]
n_e = c.execute("SELECT COUNT(DISTINCT pos) FROM eingabe").fetchone()[0]
c.close()
ok("P3 Eingaben nur EINMAL eingefroren (%d Zeilen), jeder Neustart nimmt dieselben (%d Starts)" % (n_e, starts), starts >= mitten and n_e == 1000 and eing > 900)

# P4 Kontingent
ab4 = os.path.join(tmp, "p4.db")
r = lauf(ab4, env={"N4_DECKEL_2": "30", "N4_DECKEL_1": "20", "N4_TAG": "2030-01-01"})
c = sqlite3.connect(ab4)
k = dict(((s, t), n) for s, t, n in c.execute("SELECT schluessel, tag, n FROM kontingent"))
leer = c.execute("SELECT COUNT(*) FROM ereignis WHERE art='LEER'").fetchone()[0]
nst = c.execute("SELECT COUNT(*) FROM stimme").fetchone()[0]
c.close()
ok("P4 Deckel je Schluessel: erst Schluessel 2 (30), dann 1 (20), dann Ende ohne Warten", k == {(2, "2030-01-01"): 30, (1, "2030-01-01"): 20}
   and leer == 1 and nst == 50, "%s leer=%d stimmen=%d" % (k, leer, nst))
r = lauf(ab4, env={"N4_DECKEL_2": "30", "N4_DECKEL_1": "20", "N4_TAG": "2030-01-02"})
c = sqlite3.connect(ab4); nst2 = c.execute("SELECT COUNT(*) FROM stimme").fetchone()[0]; c.close()
ok("P4 naechster Pazifik-Tag: setzt fort, nichts doppelt", nst2 == 100, "stimmen %d" % nst2)
r = lauf(ab4, env={"N4_DECKEL_2": "1000", "N4_DECKEL_1": "1000", "N4_TAG": "2030-01-03", "N4_PH_LEER_NACH": "10"})
c = sqlite3.connect(ab4)
er = c.execute("SELECT schluessel FROM kontingent WHERE tag='2030-01-03' AND erschoepft=1 ORDER BY schluessel").fetchall()
c.close()
ok("P4 Google meldet 'Tagesbudget leer' -> Schluessel als erschoepft vermerkt, Wechsel auf den anderen", [x[0] for x in er] == [1, 2], str(er))

# P5 Fassung
c = sqlite3.connect(ab4); c.execute("UPDATE meta SET v='andere' WHERE k='fassung'"); c.commit(); c.close()
r = lauf(ab4, env={"N4_TAG": "2030-01-04"})
ok("P5 geaenderte Fassung -> der Laeufer verweigert", r.returncode != 0 and "FASSUNG GEAENDERT" in (r.stdout + r.stderr))

# P6 Doppelstart
ab6 = os.path.join(tmp, "p6.db")
p = lauf(ab6, env={"N4_PH_PAUSE": "0.01"}, warte=False)
time.sleep(8)
r = lauf(ab6, env={"N4_PH_PAUSE": "0.01"}, extra=("--max-aufrufe", "50"))
p.kill(); p.wait()
ok("P6 zweiter Laeufer bei aktivem ersten -> tut nichts", "anderer Laeufer ist aktiv" in r.stdout, r.stdout[-120:])

# P7
r = subprocess.run([sys.executable, LAEUFER, "lauf", "--platzhalter", "zufall"], capture_output=True, text=True, encoding="utf-8", errors="replace")
ok("P7 Platzhalter in die echte Ablage -> verweigert", r.returncode != 0 and "nie in die echte Ablage" in (r.stdout + r.stderr))

# P8 Ende zu Ende
ab8 = os.path.join(tmp, "p8.db")
lauf(ab8, modus="orakel")
r = subprocess.run([sys.executable, AUSW, "--ablage", ab8], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=1800)
c = sqlite3.connect(ab8); ents = c.execute("SELECT name, ergebnis FROM entscheid").fetchall(); c.close()
ok("P8 Orakel-Urteile -> Bericht TRAEGT (oder frueh STOP-TRAEGT)", "P2 TRADER (vorab): TRAEGT (" in r.stdout, str(ents)[:200])
r = subprocess.run([sys.executable, AUSW, "--ablage", ab2], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=1800)
c = sqlite3.connect(ab2); ents = c.execute("SELECT name, ergebnis FROM entscheid").fetchall(); c.close()
ok("P8 Zufalls-Urteile -> TRAEGT NICHT", "TRAEGT NICHT" in r.stdout, str(ents)[:200])
open(os.path.join(HIER, "n4_pruefe_bericht_orakel.txt"), "w", encoding="utf-8").write(
    subprocess.run([sys.executable, AUSW, "--ablage", ab8], capture_output=True, text=True, encoding="utf-8", errors="replace").stdout)

# P10 Start wie die Windows-Aufgabe: pythonw (keine Konsole), Protokoll in die Datei
ab10 = os.path.join(tmp, "p10", "x.db")
os.makedirs(os.path.dirname(ab10), exist_ok=True)
pw = os.path.join(os.path.dirname(sys.executable), "pythonw.exe")
e10 = dict(os.environ, **GROSS)
subprocess.run([pw, LAEUFER, "lauf", "--ablage", ab10, "--platzhalter", "zufall", "--kein-warten", "--max-aufrufe", "30"], env=e10, timeout=600)
c = sqlite3.connect(ab10); n10 = c.execute("SELECT COUNT(*) FROM stimme").fetchone()[0]; c.close()
log10 = open(os.path.join(os.path.dirname(ab10), "n4_lauf.log"), encoding="utf-8").read() if os.path.exists(os.path.join(os.path.dirname(ab10), "n4_lauf.log")) else ""
ok("P10 Start ohne Konsole (pythonw, wie die Windows-Aufgabe): Stimmen gespeichert, Protokoll geschrieben", n10 == 30 and "START" in log10 and "HALT" in log10,
   "stimmen %d" % n10)

# P9
ok("P9 Standard-DB und Messbasen unberuehrt", all(os.path.getmtime(os.path.join(PROJ, "data", p)) == v for p, v in mt.items()), str(list(mt)))

print("\n" + ("ALLE BESTANDEN" if all(b for _n, b, _d in ERG) else "NICHT BESTANDEN: %d von %d" % (sum(b for _n, b, _d in ERG), len(ERG))))
print("Wegwerf-Ablagen:", tmp)
