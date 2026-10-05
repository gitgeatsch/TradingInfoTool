"""K-MISFIRE (05.10.2026): die Misfire-Toleranz am SEITENEFFEKT nachweisen - echter APScheduler, keine Datenbank, keine Mail.

    python Basisinfos/Rechenkern_02_10/pruefe_misfire.py

Befund NB-Export 05.10. 12:40: staleness_watchdog und coingecko_quota_check 1,07 s zu spaet -> Mail *Verpasster Lauf (Misfire)*,
weil Jobs ohne eigenes misfire_grace_time den APScheduler-Standard von 1 s erben. Fix: scheduler.background._neuer_scheduler().

Proben:
  P1 Gegenprobe: der ALTE Aufbau (BackgroundScheduler()) wertet 2 s Verspaetung als Misfire - der Fehler ist reproduziert
  P2 der neue Scheduler fuehrt denselben Job 2 s zu spaet AUS, kein Misfire
  P3 ein echter Ausfall (400 s > 300 s Toleranz) meldet sich weiter als Misfire
  P4 ein Job mit EIGENER Toleranz behaelt sie (1 s -> 2 s zu spaet ist Misfire)
  P5 der Mailtext nennt geplante Zeit, Verspaetung und Toleranz
  P6 build_scheduler() baut ueber _neuer_scheduler() (Sentinel, abgebrochen vor jedem Datenbankzugriff)
"""
import os
import sys
import threading
import time
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_MISSED  # noqa: E402
from apscheduler.schedulers.background import BackgroundScheduler  # noqa: E402

import scheduler.background as bg  # noqa: E402


def lauf(sched, verspaetung_s, eigene_toleranz=None):
    """Einen Datums-Job mit Startzeit in der Vergangenheit anlegen, Scheduler starten, Ereignis abwarten."""
    erg, fertig = [], threading.Event()

    def hoerer(ev):
        erg.append("ausgefuehrt" if ev.code == EVENT_JOB_EXECUTED else "misfire")
        fertig.set()
    sched.add_listener(hoerer, EVENT_JOB_EXECUTED | EVENT_JOB_MISSED)
    kw = {"misfire_grace_time": eigene_toleranz} if eigene_toleranz is not None else {}
    sched.add_job(lambda: None, "date", run_date=datetime.now() - timedelta(seconds=verspaetung_s), id="probe", **kw)
    sched.start()
    fertig.wait(10)
    sched.shutdown(wait=False)
    return erg[0] if erg else "nichts"


class _Ev:
    def __init__(self, t):
        self.scheduled_run_time = t


ok = []
r = lauf(BackgroundScheduler(), 2)
ok.append(("P1 Gegenprobe: alter Aufbau, 2 s zu spaet -> Misfire (Fehler reproduziert)", r == "misfire", r))
r = lauf(bg._neuer_scheduler(), 2)
ok.append(("P2 neuer Scheduler, 2 s zu spaet -> ausgefuehrt, kein Misfire", r == "ausgefuehrt", r))
r = lauf(bg._neuer_scheduler(), 400)
ok.append(("P3 echter Ausfall 400 s (> Toleranz %d s) -> weiter Misfire" % bg._IMMEDIATE_START_MISFIRE_GRACE_SECONDS, r == "misfire", r))
r = lauf(bg._neuer_scheduler(), 2, eigene_toleranz=1)
ok.append(("P4 eigene Toleranz 1 s bleibt -> 2 s zu spaet ist Misfire", r == "misfire", r))
jetzt = datetime(2026, 10, 5, 7, 18, 35, 197000, tzinfo=timezone.utc)
txt = bg._misfire_text(_Ev(jetzt - timedelta(seconds=1.07)), jetzt)
txt_h = bg._misfire_text(_Ev(jetzt - timedelta(hours=3)), jetzt)
ok.append(("P5 Mailtext nennt geplante Zeit, Verspaetung und Toleranz", "05.10. " in txt and "1 s zu spaet" in txt and "Toleranz 300 s" in txt
           and "3,0 h zu spaet" in txt_h, txt + " | " + txt_h))


class _Sentinel(Exception):
    pass


def _faengt():
    raise _Sentinel()


orig = bg._neuer_scheduler
bg._neuer_scheduler = _faengt
try:
    bg.build_scheduler(None, None, lambda: (_ for _ in ()).throw(AssertionError("keine DB")), lambda: [])
    p6, det = False, "build_scheduler lief ohne _neuer_scheduler()"
except _Sentinel:
    p6, det = True, "Sentinel erreicht"
except Exception as ex:                                       # noqa: BLE001
    p6, det = False, repr(ex)
finally:
    bg._neuer_scheduler = orig
ok.append(("P6 build_scheduler() baut ueber _neuer_scheduler()", p6, det))

for name, b, d in ok:
    print("%s  %s  (%s)" % ("OK  " if b else "FEHL", name, d))
print("ALLE BESTANDEN" if all(b for _n, b, _d in ok) else "NICHT BESTANDEN: %d von %d" % (sum(b for _n, b, _d in ok), len(ok)))
