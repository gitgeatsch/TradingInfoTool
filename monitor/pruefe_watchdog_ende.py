"""Nachweis am SEITENEFFEKT (08.10.2026): endet der Watchdog-PROZESS wirklich, wenn er beendet wird?

    python monitor/pruefe_watchdog_ende.py

Befund NB 08.10.: 40 Watchdog-Prozesse seit 20.09., alle von explorer.exe gestartet, ohne Fenster. Ursache im Code: pystray.Icon.stop()
setzt icon.visible NICHT auf False - die Schleife `while icon.visible` im Ueberwachungs-Thread (kein Hintergrund-Thread) lief endlos weiter
und hielt den Prozess am Leben; die PID-Datei war da schon geloescht, der naechste Start liess sich durch.

Echter Watchdog (echtes Tray-Symbol, kurz sichtbar), aber ein ERSATZ fuer main.py und ein Wegwerf-Datenordner. Proben:
  W1 'Beenden' (on_stop)                 -> der Prozess endet binnen 20 s, PID-Datei weg
  W2 main.py endet normal (Code 0)       -> der Watchdog endet von selbst (App geschlossen = alles zu)
  W3 main.py stuerzt ab (Code 3)         -> der Watchdog BLEIBT (rotes Symbol als Warnung), bis er beendet wird
  W4 fremde PID-Datei                    -> ein endender Watchdog loescht sie NICHT
  W5 zweiter Start bei laufendem         -> endet sofort, OHNE wartendes Hinweisfenster
"""
import os
import subprocess
import sys
import tempfile
import time

HIER = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.dirname(HIER)

HARNESS = r'''
import os, sys, threading, time
sys.path.insert(0, %(proj)r)
import monitor.watchdog as W
from pathlib import Path
d = Path(%(daten)r)
W.DATA_DIR = d; W.PID_PATH = d / "watchdog.pid"; W.HEARTBEAT_PATH = d / "hb.txt"; W.CRASH_LOG_PATH = d / "crash.log"
W.RESTART_FLAG_PATH = d / "restart.txt"; W.MAIN_PY = Path(%(main)r); W.STARTUP_GRACE_SECONDS = 1
modus = %(modus)r
if modus == "zweiter":
    W.main(); sys.exit(0)
W._check_existing_instance()
w = W.Watchdog()
if modus == "stop":
    orig = w._monitor_loop
    def loop(icon):
        threading.Timer(3, lambda: w.on_stop(icon, None)).start()
        orig(icon)
    w._monitor_loop = loop
if modus == "fremd":
    orig = w._monitor_loop
    def loop2(icon):
        def spaeter():
            W.PID_PATH.write_text("4", encoding="utf-8")     # PID 4 = System, lebt immer
            w.on_stop(icon, None)
        threading.Timer(3, spaeter).start()
        orig(icon)
    w._monitor_loop = loop2
w.run()
'''


def starte(modus, daten, main_code):
    m = os.path.join(daten, "ersatz_main.py")
    open(m, "w").write(main_code)
    h = os.path.join(daten, "harness_%s.py" % modus)
    open(h, "w", encoding="utf-8").write(HARNESS % {"proj": PROJ, "daten": daten, "main": m, "modus": modus})
    return subprocess.Popen([sys.executable, h], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def ende_binnen(p, s):
    t0 = time.time()
    while time.time() - t0 < s:
        if p.poll() is not None:
            return True
        time.sleep(0.5)
    return False


ERG = []


def toete(p):
    """Watchdog SAMT Kind (Ersatz-main.py) beenden - sonst haelt das Kind die Wegwerfdateien offen."""
    subprocess.run(["taskkill", "/PID", str(p.pid), "/T", "/F"], capture_output=True)
    time.sleep(1)


def ok(name, b, info=""):
    ERG.append(bool(b))
    print("%s  %s  %s" % ("OK  " if b else "FEHL", name, info), flush=True)


if __name__ == "__main__":
    lang = "import time; time.sleep(120)\n"
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as d:
        p = starte("stop", d, lang)
        e = ende_binnen(p, 25)
        ok("W1 'Beenden' -> Prozess endet binnen 25 s, PID-Datei weg", e and not os.path.exists(os.path.join(d, "watchdog.pid")),
           "beendet" if e else "LAEUFT NOCH (Geister-Watchdog)")
        if not e:
            toete(p)
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as d:
        p = starte("normal", d, "import time; time.sleep(3)\n")
        e = ende_binnen(p, 30)
        ok("W2 main.py endet normal (Code 0) -> Watchdog endet von selbst", e, "beendet" if e else "laeuft weiter")
        if not e:
            toete(p)
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as d:
        p = starte("normal", d, "import time, sys; time.sleep(3); sys.exit(3)\n")
        e = ende_binnen(p, 15)
        ok("W3 main.py stuerzt ab (Code 3) -> Watchdog bleibt als Warnung", not e, "bleibt" if not e else "endete")
        toete(p)
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as d:
        p = starte("fremd", d, lang)
        e = ende_binnen(p, 25)
        inhalt = open(os.path.join(d, "watchdog.pid")).read() if os.path.exists(os.path.join(d, "watchdog.pid")) else None
        ok("W4 fremde PID-Datei bleibt beim Ende stehen", e and inhalt == "4", "Inhalt %r, beendet %s" % (inhalt, e))
        if not e:
            toete(p)
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as d:
        open(os.path.join(d, "watchdog.pid"), "w").write(str(os.getpid()))   # 'laufender' Watchdog = dieser Pruefprozess (PID 4 ist ohne Adminrechte nicht abfragbar)
        p = starte("zweiter", d, lang)
        e = ende_binnen(p, 10)
        ok("W5 zweiter Start bei laufendem Watchdog -> endet sofort, kein wartendes Fenster", e, "beendet" if e else "WARTET (Hinweisfenster)")
        if not e:
            toete(p)
    print("\n%d von %d bestanden" % (sum(ERG), len(ERG)))
