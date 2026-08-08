"""Prueft den Circuit Breaker der LLM-Fallback-Kette (07.08.2026).

DER ANLASS, gemessen am Export vom 07.08. 15:16:

    llm_calls_heute:  groq 0, mistral 0, gemini 142
    56 Spot-Signale heute, alle Gemini. 86 Hebel-Signale, alle Gemini.

Mistral stand in der Kette an erster Stelle und lieferte den ganzen Tag
`402 Payment Required` (Konto-Dashboard: Free-Plan, 10 $ Monatsbudget
ausgeschoepft, Reset in 24 Tagen). Es gab keinen Abbruch - **mindestens 142
vergebliche Versuche an einem Tag**, jeder davon Wartezeit vor einem Signal.

DER WICHTIGSTE TEST IST C: die Sperre muss ueber LAUFGRENZEN hinweg wirken.
Das Hebel-Screening laeuft alle 15 Minuten mit typisch ein bis zwei Kandidaten
(142 Signale auf 96 Laeufe). Ein Breaker, der erst nach drei Fehlschlaegen
greift und beim naechsten Lauf vergessen ist, verhindert praktisch nichts.
"""
import pathlib
import tempfile
from datetime import datetime, timedelta, timezone

import database.db as db

fehler = []
def pruefe(name, ok, info=""):
    print(("  OK   " if ok else "  FEHL ") + name + ("  " + info if info else ""))
    if not ok:
        fehler.append(name)

db.DB_PATH = pathlib.Path(tempfile.mkdtemp()) / "test.db"
conn = db.get_connection()
db.init_db(conn)

from agent.provider_sperre import (
    MAX_FEHLSCHLAEGE_IN_FOLGE,
    PROBE_INTERVALL_STUNDEN,
    LaufSperre,
    ist_dauerhafter_fehler,
    vorbelegte_sperre,
)

JETZT = datetime(2026, 8, 7, 16, 0, tzinfo=timezone.utc)
FEHLER_402 = "402 Client Error: Payment Required for url: https://api.mistral.ai/v1/chat/completions"

print("A) ZWEI FEHLERKLASSEN AUSEINANDERHALTEN")
pruefe("A1 402 ist dauerhaft", ist_dauerhafter_fehler(FEHLER_402))
pruefe("A2 401 ebenfalls", ist_dauerhafter_fehler("401 Unauthorized"))
pruefe("A3 403 ebenfalls", ist_dauerhafter_fehler("403 Forbidden"))
pruefe("A4 429 ist es NICHT - ein Wartefehler ist keine Berechtigungsfrage",
       not ist_dauerhafter_fehler("429 Too Many Requests: rate limit exceeded"),
       "sonst sperrte ein Rate-Limit den Anbieter, obwohl die naechste Runde eine echte Chance ist")
pruefe("A5 Netzwerkfehler ist es nicht",
       not ist_dauerhafter_fehler("ConnectTimeout: HTTPSConnectionPool"))
pruefe("A6 leerer Text ohne Absturz", not ist_dauerhafter_fehler(None))

print("\nB) INNERHALB EINES LAUFS")
s = LaufSperre()
pruefe("B1 zu Beginn ist nichts gesperrt", not s.ist_gesperrt("mistral"))
s.melde_fehlschlag("mistral", FEHLER_402)
pruefe("B2 EIN dauerhafter Fehler genuegt - kein zweiter Versuch",
       s.ist_gesperrt("mistral"), s.gesperrt.get("mistral", "")[:50])

s2 = LaufSperre()
for i in range(MAX_FEHLSCHLAEGE_IN_FOLGE - 1):
    s2.melde_fehlschlag("gemini", "ConnectTimeout")
pruefe("B3 voruebergehende Fehler sperren NICHT sofort",
       not s2.ist_gesperrt("gemini"),
       f"{MAX_FEHLSCHLAEGE_IN_FOLGE - 1} von {MAX_FEHLSCHLAEGE_IN_FOLGE}")
s2.melde_fehlschlag("gemini", "ConnectTimeout")
pruefe("B4 aber nach dem dritten schon", s2.ist_gesperrt("gemini"))

s3 = LaufSperre()
s3.melde_fehlschlag("gemini", "ConnectTimeout")
s3.melde_fehlschlag("gemini", "ConnectTimeout")
s3.melde_erfolg("gemini")
s3.melde_fehlschlag("gemini", "ConnectTimeout")
pruefe("B5 ein Erfolg setzt die Serie zurueck", not s3.ist_gesperrt("gemini"),
       "zwei Aussetzer mit einem Erfolg dazwischen sind kein Ausfall")

print("\nC) UEBER LAUFGRENZEN HINWEG - der eigentliche Punkt")
db.record_api_health_error(conn, "mistral", "HTTPError", FEHLER_402)
sperre = vorbelegte_sperre(conn, ("mistral", "gemini"), JETZT)
pruefe("C1 der letzte dauerhafte Fehler sperrt schon VOR dem ersten Versuch",
       sperre.ist_gesperrt("mistral"), sperre.gesperrt.get("mistral", "")[:60])
pruefe("C2 der zweite Anbieter bleibt frei", not sperre.ist_gesperrt("gemini"))

# Ein Erfolg hebt die Sperre auf - api_health_status kippt dann auf "ok".
db.record_api_health_success(conn, "mistral")
sperre = vorbelegte_sperre(conn, ("mistral", "gemini"), JETZT)
pruefe("C3 nach einem Erfolg ist die Sperre weg", not sperre.ist_gesperrt("mistral"))

print("\nD) SIE BLEIBT NICHT EWIG ZU - halb offen nach der Probefrist")
conn.execute("DELETE FROM api_health_status")
conn.commit()
db.record_api_health_error(conn, "mistral", "HTTPError", FEHLER_402)
conn.execute("UPDATE api_health_status SET last_error_at = ? WHERE source = 'mistral'",
             ((JETZT - timedelta(hours=PROBE_INTERVALL_STUNDEN - 1)).isoformat(),))
conn.commit()
pruefe("D1 kurz vor der Frist noch gesperrt",
       vorbelegte_sperre(conn, ("mistral",), JETZT).ist_gesperrt("mistral"))

conn.execute("UPDATE api_health_status SET last_error_at = ? WHERE source = 'mistral'",
             ((JETZT - timedelta(hours=PROBE_INTERVALL_STUNDEN + 1)).isoformat(),))
conn.commit()
pruefe("D2 nach der Frist wird wieder EINMAL probiert",
       not vorbelegte_sperre(conn, ("mistral",), JETZT).ist_gesperrt("mistral"),
       f"sonst bliebe ein zurueckgekehrtes Kontingent unbemerkt - bei Mistral "
       f"kommt es laut Dashboard in 24 Tagen zurueck")

print("\nE) VORUEBERGEHENDE FEHLER WERDEN NICHT UEBER LAEUFE GEMERKT")
conn.execute("DELETE FROM api_health_status")
conn.commit()
db.record_api_health_error(conn, "gemini", "ConnectTimeout", "ConnectTimeout: HTTPSConnectionPool")
pruefe("E1 ein Netzwerkhaenger sperrt den naechsten Lauf NICHT",
       not vorbelegte_sperre(conn, ("gemini",), JETZT).ist_gesperrt("gemini"),
       "sonst legte ein einzelner Aussetzer den Anbieter fuer Stunden still")

print("\nF) DIE ERSPARNIS WIRD GEZAEHLT, NICHT VERSCHWIEGEN")
s4 = LaufSperre()
s4.melde_fehlschlag("mistral", FEHLER_402)
for _ in range(9):
    s4.ist_gesperrt("mistral")
b = s4.bericht()
pruefe("F1 uebersprungene Versuche gezaehlt", b["gesamt_uebersprungen"] == 9, str(b))
pruefe("F2 mit Grund", "402" in b["gesperrt"]["mistral"], b["gesperrt"]["mistral"][:60])

print("\nG) BEIDE KETTEN BENUTZEN DASSELBE MODUL")
# ACHTUNG, GRENZE DIESER PRUEFUNG (2026-08-09): G ist STRUKTURELL - sie liest
# den Quelltext und stellt fest, DASS das Modul verdrahtet ist. Sie sagt nichts
# darueber, ob die VORBELEGUNG tatsaechlich wirkt.
#
# Das ist keine theoretische Einschraenkung: in multi_asset_batch.py wurde
# `vorbelegte_sperre()` vom 07. bis 09.08. mit einer bereits GESCHLOSSENEN
# Verbindung aufgerufen. Die Funktion faengt jede Exception ab und lieferte
# eine leere Sperre - G war die ganze Zeit gruen. Der funktionale Gegenbeweis
# steht in teste_kette_reihenfolge.py (Laeufe M5 und Krypto-Pendant): ein
# dauerhafter Fehler in api_health_status bei KERNGESUNDEM Client muss zu null
# Aufrufversuchen fuehren. Diese Datei prueft das Modul, jene die Ketten.
import io as _io
for pfad in ("agent/krypto/budget_allocator.py", "agent/multi_asset_batch.py"):
    quelle = _io.open(pfad, encoding="utf-8").read()
    pruefe(f"G {pfad.split('/')[-1]} verdrahtet",
           "provider_sperre" in quelle
           and "sperre.ist_gesperrt(provider_name)" in quelle
           and "sperre.melde_fehlschlag(provider_name" in quelle,
           "zwei Kopien wuerden garantiert auseinanderlaufen")

print("\nG2) DIE FEHLERKLASSE, DIE G NICHT SIEHT")
# Ein geschlossener Connection-Handle liefert eine LEERE Sperre statt eines
# Fehlers. Hier festgehalten, damit die Fehlerklasse benannt ist und niemand
# den fail-soft-Zweig fuer harmlos haelt.
import sqlite3 as _sq
_zu = _sq.connect(":memory:")
_zu.close()
pruefe("G2 geschlossene Verbindung -> leere Sperre, kein Absturz",
       vorbelegte_sperre(_zu, ("mistral",), JETZT).gesperrt == {},
       "fail-soft - und genau deshalb war der Defekt in multi_asset_batch.py unsichtbar")

print("\nH) FEHLENDE TABELLE TOETET NICHTS")
class KaputteConn:
    def execute(self, *a, **k):
        raise RuntimeError("no such table: api_health_status")
pruefe("H1 unlesbarer Status liefert eine leere Sperre",
       vorbelegte_sperre(KaputteConn(), ("mistral",), JETZT).gesperrt == {},
       "fail-soft, aber mit Log-Zeile")

print("\n" + ("ALLE TESTS BESTANDEN" if not fehler else f"FEHLER: {fehler}"))
conn.close()
