"""Gegenpruefung S7-2b - der Betriebslauf auf Wegwerfordnern (Ablage und Modelle), Daten nur lesend.

1  Monatsjob im Lauf: fehlt das Paket des Monats, wird es trainiert und mit Pruefsumme abgelegt; der zweite Lauf trainiert nicht neu
2  Lauf zur Stunde T: neue Signale = Referenz-Einstiege der Stunde T, mit vorlaeufiger Stufe und Hebel-Schalter in der Ablage
3  Lauf zur Stunde T+1: dieselben Signale bekommen die ENDGUELTIGE Stufe = Betriebsform B-10
4  zweiter Lauf zur selben Stunde: keine Doppel, Lauf-Zeile ersetzt
5  kein Seiteneffekt: data/*.db und die Produktion unveraendert (Groesse und Aenderungszeit)
6  Stundenjob: der Prozessstart wertet Rueckgabe und Meldung aus (Fehlermail), der Erfolgsfall ohne Mail
7  Laufzeit und Spitzenspeicher des Prozesses (Desktop)
"""
import ctypes
import os
import sqlite3
import subprocess
import sys
import tempfile
import time

import numpy as np
import pandas as pd

HIER = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, HIER)
os.chdir(HIER)
sys.stdout.reconfigure(encoding="utf-8")
import agent.regel0_rechnung as RK                                 # noqa: E402
import agent.regel0_stundenlauf as SL                              # noqa: E402
import messe_k1_schritt2b_kombination as K2                        # noqa: E402

ergebnis = []


def pruef(name, ok, info=""):
    ergebnis.append(bool(ok))
    print("  %s %s%s" % ("✔" if ok else "⛔", name, (" - " + info) if info else ""), flush=True)


def zustand():
    return {f: (os.path.getsize(os.path.join("data", f)), os.path.getmtime(os.path.join("data", f)))
            for f in os.listdir("data") if f.endswith(".db")}


B0 = pd.Timestamp(2020, 1, 1)
h = lambda ts: int((pd.Timestamp(ts) - B0) / pd.Timedelta(hours=1))
ref = pd.read_csv("data/_vergleich/kern48jbz_einstiege_bestand.csv", sep=";")
T = h("2026-08-27 21:00")
soll = sorted(ref.symbol[ref.stunde == T])
vorher = zustand()
abl, mod = tempfile.mkdtemp(), tempfile.mkdtemp()
t0 = time.time()

print("1) + 2) Lauf zur Stunde %s (Paket 2026-08 fehlt noch)" % RK._stunde_txt(T))
e1 = SL.betrieb_lauf(RK.DATEN_VORGABE, T, abl, mod)
pruef("Monatspaket trainiert und mit Pruefsumme abgelegt", e1["trainiert"] == ["2026-08"]
      and os.path.exists(os.path.join(mod, "regel0_modell_2026-08.pkl.sha256")), str(e1["trainiert"]))
c = sqlite3.connect(os.path.join(abl, "regel0_signale.db"))
neu = sorted(r[0] for r in c.execute("SELECT symbol FROM signal WHERE einstieg=?", (RK._stunde_txt(T),)) if r[0] in set(ref.symbol))
pruef("neue Signale = Referenz-Einstiege der Stunde %s" % RK._stunde_txt(T), neu == soll, "%s / %s" % (neu, soll))
z = c.execute("SELECT symbol, stufe_vorlaeufig, stufe, hebel_schalter, bitpanda FROM signal WHERE einstieg=?", (RK._stunde_txt(T),)).fetchall()
pruef("vorlaeufige Stufe gesetzt, endgueltige noch leer", all(r[1] is not None and r[2] is None for r in z), str(z[:4]))
c.close()

print("3) Lauf zur Stunde T+1 - endgueltige Stufe")
e2 = SL.betrieb_lauf(RK.DATEN_VORGABE, T + 1, abl, mod)
pruef("zweiter Lauf trainiert NICHT neu", e2["trainiert"] == [], str(e2["trainiert"]))
zus = RK.zusatz_aus_gruppe("data/_vergleich/kern48jbz_gruppe_bestand.csv")
reihen = RK.lade_reihen(RK.DATEN_VORGABE, zus)
Xh = RK.hebel_anker(RK.DATEN_VORGABE, reihen, set(zus))
MB = RK.hebel_modelle(Xh, [(2026, 7)], bis_stunde=K2._h(pd.Timestamp(2026, 7, 1).to_pydatetime()))
a_ = RK.atr_je_stunde(reihen)
c = sqlite3.connect(os.path.join(abl, "regel0_signale.db"))
z = c.execute("SELECT symbol, stufe_vorlaeufig, stufe FROM signal WHERE einstieg=?", (RK._stunde_txt(T),)).fetchall()
gl = []
for s_, _v, st_ in z:
    if s_ in set(ref.symbol):
        _P, L_ = RK.hebelstufe(np.array([a_.get(s_, {}).get(T, np.nan)]), np.array([int(RK.monat_von(np.array([T]))[0])]), MB)
        gl.append(int(L_[0]) == st_)
pruef("endgueltige Stufe = Betriebsform B-10", gl and all(gl), "%s" % z)

print("4) zweiter Lauf zur selben Stunde T+1")
n1 = c.execute("SELECT COUNT(*) FROM signal").fetchone()[0]
c.close()
SL.betrieb_lauf(RK.DATEN_VORGABE, T + 1, abl, mod)
c = sqlite3.connect(os.path.join(abl, "regel0_signale.db"))
n2 = c.execute("SELECT COUNT(*) FROM signal").fetchone()[0]
nl = c.execute("SELECT COUNT(*) FROM lauf").fetchone()[0]
c.close()
pruef("keine Doppel, Lauf-Zeile ersetzt", n1 == n2 and nl == 2, "Signale %d -> %d, Laeufe %d" % (n1, n2, nl))

print("5) kein Seiteneffekt")
nachher = zustand()
pruef("data/*.db unveraendert (Groesse und Aenderungszeit), auch die Produktion", vorher == nachher,
      "geaendert: %s" % sorted(k for k in nachher if vorher.get(k) != nachher[k]))
leer = tempfile.mkdtemp()
SL._ablage(leer).close()
angelegt = sorted(os.listdir(leer))
pruef("die Ablage legt in einem leeren Ordner GENAU regel0_signale.db an, sonst nichts", angelegt == ["regel0_signale.db"], str(angelegt))

print("6) Stundenjob wertet den Prozess aus")
import scheduler.background as BG                                   # noqa: E402
mails = []
BG._notify_job_failure = lambda j, t: mails.append((j, t))
alt = subprocess.run
try:
    subprocess.run = lambda *a, **k: subprocess.CompletedProcess(a, 0, 'REGEL0-ERGEBNIS {"neu": 1, "meldung": ""}\n', "")
    BG._regel0_rechnung_starten(); m0 = len(mails)
    subprocess.run = lambda *a, **k: subprocess.CompletedProcess(a, 0, 'REGEL0-ERGEBNIS {"neu": 0, "meldung": "40 von 500 veraltet"}\n', "")
    BG._regel0_rechnung_starten(); m1 = len(mails)
    subprocess.run = lambda *a, **k: subprocess.CompletedProcess(a, 1, "", "Traceback ...\nValueError: Probe\n")
    BG._regel0_rechnung_starten(); m2 = len(mails)

    def _zu_lang(*a, **k):
        raise subprocess.TimeoutExpired(a, 1)
    subprocess.run = _zu_lang
    BG._regel0_rechnung_starten(); m3 = len(mails)
finally:
    subprocess.run = alt
pruef("Erfolg ohne Mail, Frische-Meldung / Fehler / Zeitgrenze je mit Fehlermail", (m0, m1, m2, m3) == (0, 1, 2, 3), str(mails))

print("7) Laufzeit und Speicher als eigener Prozess (Stunde T+2)")
t1 = time.time()
p = subprocess.Popen([sys.executable, "-m", "agent.regel0_stundenlauf", "--betrieb", "--jetzt", str(T + 2), "--ablage", abl, "--modelle", mod],
                     stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8")
spitze = 0


class PMC(ctypes.Structure):
    _fields_ = [("cb", ctypes.c_ulong), ("PageFaultCount", ctypes.c_ulong), ("PeakWorkingSetSize", ctypes.c_size_t),
                ("WorkingSetSize", ctypes.c_size_t), ("QuotaPeakPagedPoolUsage", ctypes.c_size_t), ("QuotaPagedPoolUsage", ctypes.c_size_t),
                ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t), ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                ("PagefileUsage", ctypes.c_size_t), ("PeakPagefileUsage", ctypes.c_size_t)]


k32 = ctypes.WinDLL("kernel32"); ps = ctypes.WinDLL("psapi")
hp = k32.OpenProcess(0x1000 | 0x0010, False, p.pid)
while p.poll() is None:
    m = PMC(); m.cb = ctypes.sizeof(PMC)
    if ps.GetProcessMemoryInfo(hp, ctypes.byref(m), m.cb):
        spitze = max(spitze, m.PeakWorkingSetSize)
    time.sleep(1)
out, err = p.communicate()
print("    %s" % [z for z in out.splitlines() if z.startswith("REGEL0-ERGEBNIS")][-1:])
pruef("Prozess laeuft durch (Rueckgabe 0)", p.returncode == 0, (err or "").strip().splitlines()[-1:] and (err or "").strip().splitlines()[-1] or "")
print("    Laufzeit %.0f s · Spitzenspeicher %.2f GB (Desktop; am NB rund Faktor 3,5 in der Zeit)" % (time.time() - t1, spitze / 1e9))
print("SCHLUSS: %s (%d von %d) · %.0f s" % ("✔ bestanden" if all(ergebnis) else "⛔ NICHT bestanden", sum(ergebnis), len(ergebnis), time.time() - t0))
