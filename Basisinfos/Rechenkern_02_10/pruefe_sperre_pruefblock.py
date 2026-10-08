"""Nachweis am SEITENEFFEKT (08.10.2026, Schritt7 §23.25): schreibt der Pruefblock seine Zeilen, wenn er AUS dem Mailversand gerufen wird?

    python Basisinfos/Rechenkern_02_10/pruefe_sperre_pruefblock.py

Befund NB 07.10.: BEAMX gemailt 20:10 UTC, KEINE pruefung-Zeile; im Protokoll 51 s zwischen Markt-Eingabe und Versand, kein Fehler.
Verdacht: regel0_mail.versende fuehrt das UPDATE mail_verpasst_am aus (E-57, seit 05.10.) und committet nur bei rowcount > 0 - die
implizite Schreibtransaktion bleibt offen, die zweite Verbindung des Pruefblocks wartet 30 s und scheitert mit 'database is locked'.

Wegwerf-Ablage, Versand abgefangen (keine Mail), Platzhalter-Client (kein Gemini), echte Funktionen versende + pruefe_signal.
"""
import os
import sqlite3
import sys
import tempfile
import time
from datetime import datetime, timedelta, timezone

HIER = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.dirname(os.path.dirname(HIER))
os.chdir(PROJ)
sys.path.insert(0, PROJ)
import agent.regel0_ablage as AB      # noqa: E402
import agent.regel0_llm as LLM        # noqa: E402
import agent.regel0_mail as RM        # noqa: E402


class Fake:
    n = 0

    def chat(self, msgs, model=None, temperature=None, response_format=None):
        Fake.n += 1
        return '{"belege":[{"fakt":"f","richtung":"dafuer"}],"urteil":"neutral","begruendung":"b","gegengrund":"g"}'


def lauf(d):
    jetzt = datetime(2026, 9, 24, 5, 10, tzinfo=timezone.utc)
    c = AB.oeffne(d)
    cols = [r[1] for r in c.execute("PRAGMA table_info(signal)")]
    werte = {"symbol": "BEAMX", "signalstunde": "2026-09-24 04:00", "einstieg": "2026-09-24 05:00", "ausstieg": "2026-09-25 05:00",
             "vh": 0.0418, "stufe_vorlaeufig": 3, "stufe": 3, "p2": 0.001, "p3": 0.007, "p5": 0.1, "hebel_schalter": 1, "bitpanda": "BEAMX",
             "zusatz": 0, "btc": 0, "version": "REGEL0.1", "erfasst_am": "2026-09-24 05:09", "kurs": 0.00257, "kurs_markt": "spot"}
    c.execute("INSERT INTO signal (%s) VALUES (%s)" % (",".join(werte), ",".join("?" * len(werte))), list(werte.values()))
    c.commit(); c.close()
    K = LLM.lade()
    um = LLM.Umlauf(K, Fake(), d)
    fehler = {}

    def pruef(r):
        t0 = time.time()
        try:
            return LLM.mail_teile(LLM.pruefe_signal(r, Fake(), d, os.path.join(PROJ, "data"), os.path.join(PROJ, "data", "tradinginfotool.db"),
                                                     K, umlauf=um), K)
        except Exception as exc:                               # noqa: BLE001
            fehler["typ"] = "%s: %s (nach %.0f s)" % (type(exc).__name__, exc, time.time() - t0)
            raise
    gesendet = []
    z = RM.versende(d, lambda b, t, *a, **k: gesendet.append(b) or True, jetzt=jetzt,
                    kurse=lambda: ({"BEAMX": 0.00256}, {"BEAMXUSDT": 0.002566}, {"BEAMX": 0.0022}), pruefung=pruef)
    c = sqlite3.connect(os.path.join(d, AB.ABLAGE_NAME))
    zeilen = c.execute("SELECT rolle, fassung, fehler FROM pruefung").fetchall()
    c.close()
    return z, gesendet, zeilen, fehler


if __name__ == "__main__":
    with tempfile.TemporaryDirectory() as d:
        t0 = time.time()
        z, g, zeilen, fehler = lauf(d)
        print("versende: %s · Mails %d · Laufzeit %.0f s" % ({k: v for k, v in z.items() if v}, len(g), time.time() - t0))
        print("Pruefblock-Fehler: %s" % (fehler.get("typ") or "keiner"))
        print("pruefung-Zeilen: %s" % zeilen)
        print("ERGEBNIS: %s" % ("Zeilen geschrieben - Pruefblock arbeitet" if zeilen else "KEINE Zeile - der Pruefblock scheitert im Mailversand"))
