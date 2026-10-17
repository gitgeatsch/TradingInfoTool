"""P11d (17.10.2026, Plan_Hebel 13h) - Betreff der REGEL0-Meldung: 'nachgeholt' ist kein Fehler. Pruefstand am Job-Pfad, ohne Netz/Mail.

    python Basisinfos/Rechenkern_02_10/p11d_pruefstand.py

Gestellt: der Unterprozess ``agent.regel0_stundenlauf --betrieb`` (seine Ausgabezeile REGEL0-ERGEBNIS) und der Mailversand. Es laeuft
der ECHTE Pfad ``_regel0_rechnung_starten`` -> ``_notify_job_failure``.

  D1  der ECHTE Fall vom 16.10. 18:30 (NB-Log, alte Ausgabe ohne die neuen Felder): nur 'nachgeholt: 08:00, 11:00, 12:00, 13:00'
      -> Betreff 'REGEL0 nachgeholt (4 Std.) - Rechnung erfolgreich', Text 'Kein Fehler', die Stunden
  D2  neue Ausgabe, nur nachgeholt (3 Signale) -> derselbe Betreff, 'Signale in diesen Stunden: 3'
  D3  Datenbasis veraltet (mit oder ohne nachgeholt) -> weiter 'Job 'regel0_rechnung' fehlgeschlagen' mit dem Meldungstext
  D4  eine Stunde NICHT nachholbar -> 'fehlgeschlagen'
  D5  keine Meldung -> keine Mail; Rueckgabe != 0 -> 'fehlgeschlagen' (unveraendert)
  D6  Spam-Schutz je Art getrennt: nach einer 'nachgeholt'-Mail kommt ein echter Fehler trotzdem sofort
  D7  der Stundenlauf gibt die neuen Felder aus (Quelltext) - veraltet_gemeldet, nachholen_ausgelassen, nachgeholt_signale
"""
import json
import os
import subprocess
import sys

WURZEL = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, WURZEL)
os.chdir(WURZEL)
import api.email_notify as EN  # noqa: E402
import config as C  # noqa: E402
import scheduler.background as BG  # noqa: E402

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:  # noqa: BLE001
    pass
ERG = []


def pruefe(k, ok, text):
    ERG.append(bool(ok))
    print("%-3s %-9s %s" % (k, "bestanden" if ok else "FEHLER", text))


POST = []
EN.send_notification_email = lambda betreff, text, an, *a, **k: POST.append((betreff, text)) or True
_cfg = C.load_config()
_cfg.setdefault("benachrichtigung", {}).setdefault("email", {}).update(aktiv=True, empfaenger="pruefstand@invalid", job_ausfall_cooldown_minuten=60)
C.load_config = lambda *a, **k: _cfg
LAUF = {"zeile": "", "rc": 0}
subprocess.run = lambda *a, **k: subprocess.CompletedProcess(a, LAUF["rc"], stdout=LAUF["zeile"], stderr="Traceback ... kaputt")


def lauf(erg, rc=0):
    BG._last_failure_email_sent.clear()
    POST.clear()
    LAUF.update(zeile="REGEL0-ERGEBNIS " + json.dumps(erg, ensure_ascii=False), rc=rc)
    BG._regel0_rechnung_starten()
    return list(POST)


ECHT = {"jetzt": "2026-10-16 16:00", "sekunden": 197.0, "neu": 7, "endgueltig": 5,
        "nachgeholt": ["2026-10-16 08:00", "2026-10-16 11:00", "2026-10-16 12:00", "2026-10-16 13:00"], "neu_schalter_an": 0, "aktiv": 637,
        "frisch": 637, "veraltet": 0, "trainiert": [], "meldung": "nachgeholt: 2026-10-16 08:00, 2026-10-16 11:00, 2026-10-16 12:00, 2026-10-16 13:00"}
p = lauf(ECHT)
pruefe("D1", len(p) == 1 and p[0][0] == "TradingInfoTool: REGEL0 nachgeholt (4 Std.) - Rechnung erfolgreich" and p[0][1].startswith("Kein Fehler")
       and "2026-10-16 13:00" in p[0][1] and "fehlgeschlagen" not in p[0][0],
       "echter Fall 16.10. 18:30: %s" % (p[0][0] if p else "keine Mail"))
neu = dict(ECHT, nachgeholt=["2026-10-17 01:00", "2026-10-17 02:00"], meldung="nachgeholt: 2026-10-17 01:00, 2026-10-17 02:00",
           veraltet_gemeldet=False, nachholen_ausgelassen=[], nachgeholt_signale=3)
p = lauf(neu)
pruefe("D2", len(p) == 1 and "nachgeholt (2 Std.)" in p[0][0] and "Signale in diesen Stunden: 3" in p[0][1], "neue Ausgabe: %s" % (p[0][0] if p else "-"))
v1 = dict(neu, veraltet_gemeldet=True, meldung="40 von 637 aktiven Assets ohne die Stunde 2026-10-17 02:00 - Datenbasis veraltet (Nachlader?) · "
                                                 "nachgeholt: 2026-10-17 01:00")
v2 = dict(ECHT, meldung="40 von 637 aktiven Assets ohne die Stunde 2026-10-17 02:00 - Datenbasis veraltet (Nachlader?)", nachgeholt=[])
p1, p2 = lauf(v1), lauf(v2)
pruefe("D3", [x[0] for x in p1 + p2] == ["TradingInfoTool: Job 'regel0_rechnung' fehlgeschlagen"] * 2 and "Datenbasis veraltet" in p1[0][1],
       "veraltet mit/ohne nachgeholt: %s" % [x[0] for x in p1 + p2])
a1 = dict(neu, nachholen_ausgelassen=["2026-10-17 00:00"], meldung="nachgeholt: 2026-10-17 01:00 · NICHT nachholbar (Modellpaket fehlt): 2026-10-17 00:00")
a2 = dict(ECHT, meldung="nachgeholt: - · NICHT nachholbar (Modellpaket fehlt): 2026-10-17 00:00", nachgeholt=[])
p1, p2 = lauf(a1), lauf(a2)
pruefe("D4", [x[0] for x in p1 + p2] == ["TradingInfoTool: Job 'regel0_rechnung' fehlgeschlagen"] * 2 and "NICHT nachholbar" in p1[0][1],
       "nicht nachholbar (neu/alt): %s" % [x[0] for x in p1 + p2])
p1 = lauf(dict(ECHT, meldung="", nachgeholt=[]))
p2 = lauf(ECHT, rc=1)
pruefe("D5", p1 == [] and len(p2) == 1 and p2[0][0] == "TradingInfoTool: Job 'regel0_rechnung' fehlgeschlagen" and "Rueckgabe 1" in p2[0][1],
       "ohne Meldung: %d Mails · Rueckgabe 1: %s" % (len(p1), p2[0][0] if p2 else "-"))
BG._last_failure_email_sent.clear()
POST.clear()
LAUF.update(zeile="REGEL0-ERGEBNIS " + json.dumps(neu), rc=0)
BG._regel0_rechnung_starten()
LAUF.update(zeile="REGEL0-ERGEBNIS " + json.dumps(v2), rc=0)
BG._regel0_rechnung_starten()
BG._regel0_rechnung_starten()
pruefe("D6", [x[0][:40] for x in POST] == ["TradingInfoTool: REGEL0 nachgeholt (2 St", "TradingInfoTool: Job 'regel0_rechnung' f"],
       "nachgeholt, dann zweimal veraltet: %s (der zweite Fehler im Spam-Schutz)" % [x[0] for x in POST])
q = open("agent/regel0_stundenlauf.py", encoding="utf-8").read()
pruefe("D7", all(s in q for s in ("veraltet_gemeldet=veraltet_gemeldet", "nachholen_ausgelassen=list(", "nachgeholt_signale=len(")),
       "Stundenlauf gibt veraltet_gemeldet, nachholen_ausgelassen, nachgeholt_signale aus")
print("\n%d von %d bestanden" % (sum(ERG), len(ERG)))
sys.exit(0 if all(ERG) else 1)
