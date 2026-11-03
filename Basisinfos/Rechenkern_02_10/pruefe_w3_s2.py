"""W-3 S-2 (03.11.2026, E-166) am SEITENEFFEKT: die Jobs, die nur der alten Kette dienten, ueberspringen sich - und Frage 2:
Thesen und Marktscan fallen bei fehlender/unlesbarer Datei auf AUS.

    python -X utf8 Basisinfos/Rechenkern_02_10/pruefe_w3_s2.py

Ersetzt werden nur Modulwerte in DIESEM Prozess. Datenbank: eine Wegwerfdatei (wegwerf.py, D:). Kein Netz, keine Mail, keine
Produktion - am Ende wird geprueft, dass `data/tradinginfotool.db` unveraendert ist (Groesse und Zeitstempel).
"""
import logging
import os
import sqlite3
import sys
import tempfile

os.chdir(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.getcwd())
sys.stdout.reconfigure(encoding="utf-8")
import wegwerf  # noqa: E402,F401  (tempfile.mkdtemp -> D:, Aufraeumen am Ende)

import hashlib  # noqa: E402

PROD = os.path.join("data", "tradinginfotool.db")


def fingerabdruck():
    """sha256 ueber .db und -wal (Gegenpruefung 03.11.: die DB laeuft im WAL-Modus - ein Schreibzugriff landet zuerst in der -wal
    und liesse Groesse und Zeit der Hauptdatei unveraendert). -shm NICHT: den Index aendert schon jeder LESER. Ein anderer Prozess,
    der die Datei zur selben Zeit schliesst (Checkpoint), kann T14 rot machen - dann einzeln wiederholen."""
    aus = {}
    for end in ("", "-wal"):
        p = PROD + end
        aus[end or ".db"] = hashlib.sha256(open(p, "rb").read()).hexdigest() if os.path.exists(p) else None
    return aus


_prod_vorher = fingerabdruck()

import config as CFG  # noqa: E402
import scheduler.background as BG  # noqa: E402
import scheduler.rollen_job as RJ  # noqa: E402
import agent.regel0_groesse as R0G  # noqa: E402
import agent.lebendigkeit as LB  # noqa: E402
import agent.krypto.backward_tracking as BT  # noqa: E402
import agent.krypto.hebel_backward_tracking as HBT  # noqa: E402
import agent.krypto.ausstiegsregel as AR  # noqa: E402
import agent.fuehrung_protokoll as FP  # noqa: E402
import agent.ausstieg_verfolgung as AV  # noqa: E402
import agent.krypto.marktscan as MS  # noqa: E402
import agent.krypto.pipeline as KP  # noqa: E402
import agent.krypto.marktscan_backward_tracking as MBT  # noqa: E402
import agent.kategorie_synthese as KS  # noqa: E402
import agent.kategorie_vorschlaege as KV  # noqa: E402
import remote.status as ST  # noqa: E402

ORDNER = tempfile.mkdtemp(prefix="w3s2_")
DBP = os.path.join(ORDNER, "wegwerf.db")
from pathlib import Path as _P  # noqa: E402
BG.db.DB_PATH = _P(os.path.join(ORDNER, "umgebogen.db"))     # CLAUDE.md Regel 3: jedes Werkzeug bekommt einen Wegwerfpfad
VERB = {"n": 0}


def conn_factory():
    VERB["n"] += 1
    c = sqlite3.connect(DBP)
    c.row_factory = sqlite3.Row
    return c


def joblauf(job_id):
    c = conn_factory()
    try:
        return BG.db.letzter_joblauf(c, job_id)
    finally:
        c.close()


z = {}


def zaehler(name, rueck=None):
    def f(*a, **k):
        z[name] = z.get(name, 0) + 1
        return rueck() if callable(rueck) else rueck
    return f


class Log(logging.Handler):
    def __init__(self):
        super().__init__()
        self.zeilen = []

    def emit(self, r):
        self.zeilen.append(r.getMessage())


LOG = Log()
BG.logger.addHandler(LOG)
BG.logger.setLevel(logging.INFO)

# Netz, Mail und Rechnung ersetzen - gezaehlt wird jeder Aufruf
LB.job = zaehler("lebendigkeit")
BT.run_backward_tracking = zaehler("bt_spot", lambda: BT.BackwardTrackingResult())
HBT.run_hebel_backward_tracking = zaehler("bt_hebel", lambda: HBT.HebelBackwardTrackingResult())
BG.db.set_backward_tracking_last_run_date = zaehler("bt_datum")
AR.parameter_aus_config = lambda cfg: (1.0, 1.0, True)
BT.compute_ausstiegs_empfehlungen = zaehler("ausstieg_rechnung", lambda: {"empfehlungen": [{"tier": "hebel"}], "geprueft": 1})
FP.schreibe = zaehler("fuehrung", 0)
AV.verfolge = zaehler("verfolgung", {})
BG._sende_ausstiegs_email = zaehler("ausstieg_mail")
BG._notify_job_failure = zaehler("fehlermail")
R0G.spot_mitnahme_aktiv = lambda *a, **k: False
CFG.load_config = lambda *a, **k: dict(_CFG)
_CFG = {"marktscan": {"aktiv": False}}

ERG = []


def pruefe(name, ok, detail):
    ok = bool(ok)
    ERG.append(ok)
    print("%-4s %-9s %s" % (name, "bestanden" if ok else "FEHLER", detail))


def neu():
    z.clear()
    VERB["n"] = 0
    LOG.zeilen.clear()


# ---- T1/T2 lebendigkeit ------------------------------------------------------------------------------------------------
RJ.ALTE_KETTE_STILLGELEGT = True
neu()
rv = BG.lebendigkeit_job(conn_factory, lambda: [])
pruefe("T1", rv is True and z.get("lebendigkeit", 0) == 0 and VERB["n"] == 0 and any("W-3 S-2" in s for s in LOG.zeilen),
       "stillgelegt: lebendigkeit sammelt nicht (Aufrufe %d, DB-Verbindungen %d), Rueckgabe %s, Logzeile %s" % (
           z.get("lebendigkeit", 0), VERB["n"], rv, any("W-3 S-2" in s for s in LOG.zeilen)))
RJ.ALTE_KETTE_STILLGELEGT = False
neu()
BG.lebendigkeit_job(conn_factory, lambda: [])
pruefe("T2", z.get("lebendigkeit", 0) == 1, "UMKEHRBAR: Konstante False -> lebendigkeit sammelt (Aufrufe %d)" % z.get("lebendigkeit", 0))

# ---- T3/T4 Backward-Tracking -------------------------------------------------------------------------------------------
RJ.ALTE_KETTE_STILLGELEGT = True
neu()
BG.backward_tracking_job(conn_factory, lambda: [])
pruefe("T3", z.get("bt_spot", 0) == 0 and z.get("bt_hebel", 0) == 0 and z.get("bt_datum", 0) == 0 and joblauf("backward_tracking")
       and not z.get("fehlermail"),
       "stillgelegt: keine Messung (Spot %d, Hebel %d, Datum %d) - job_laeufe vermerkt %s" % (
           z.get("bt_spot", 0), z.get("bt_hebel", 0), z.get("bt_datum", 0), bool(joblauf("backward_tracking"))))
RJ.ALTE_KETTE_STILLGELEGT = False
neu()
BG.backward_tracking_job(conn_factory, lambda: [])
pruefe("T4", z.get("bt_spot", 0) == 1 and z.get("bt_hebel", 0) == 1 and z.get("bt_datum", 0) == 1,
       "UMKEHRBAR: Spot %d, Hebel %d, Datum %d" % (z.get("bt_spot", 0), z.get("bt_hebel", 0), z.get("bt_datum", 0)))

# ---- T5/T6 07:15 Ausstieg ----------------------------------------------------------------------------------------------
os.remove(DBP)
RJ.ALTE_KETTE_STILLGELEGT = True
neu()
_cfg_echt = CFG.load_config
CFG.load_config = lambda *a, **k: (_ for _ in ()).throw(ValueError("config.yaml kaputt"))   # Gegenpruefung Befund 7
try:
    BG.ausstiegs_job(conn_factory, lambda: [])
    _wurf = None
except Exception as exc:                                     # noqa: BLE001
    _wurf = exc
CFG.load_config = _cfg_echt
pruefe("T5", _wurf is None and not any(z.get(k) for k in ("ausstieg_rechnung", "fuehrung", "verfolgung", "ausstieg_mail"))
       and joblauf("ausstiegs_empfehlungen"),
       "stillgelegt, sogar bei kaputter config.yaml (Wurf %s): Rechnung/Fuehrung/Verfolgung/Mail %s - job_laeufe vermerkt %s" % (
           _wurf, [z.get(k, 0) for k in ("ausstieg_rechnung", "fuehrung", "verfolgung", "ausstieg_mail")],
           bool(joblauf("ausstiegs_empfehlungen"))))
RJ.ALTE_KETTE_STILLGELEGT = False
neu()
BG.ausstiegs_job(conn_factory, lambda: [])
pruefe("T6", [z.get(k, 0) for k in ("ausstieg_rechnung", "fuehrung", "verfolgung", "ausstieg_mail")] == [1, 1, 1, 1],
       "UMKEHRBAR: Rechnung/Fuehrung/Verfolgung/Mail %s" % [z.get(k, 0) for k in ("ausstieg_rechnung", "fuehrung", "verfolgung",
                                                                                 "ausstieg_mail")])

# ---- T7/T8 die zwei Nachholer beim Start -------------------------------------------------------------------------------
_bt_echt, _mab_echt = BG.backward_tracking_job, BG.multi_asset_batch_job
BG.backward_tracking_job = zaehler("bt_nachgeholt")
BG.multi_asset_batch_job = zaehler("batch_nachgeholt")
BG.db.get_backward_tracking_last_run_date = lambda c: None          # "nie gelaufen": der Nachholer WUERDE feuern
BG.db.get_multi_asset_batch_last_run_iso = lambda c: None
RJ.ALTE_KETTE_STILLGELEGT = True
neu()
BG.backward_tracking_catchup_if_missed(conn_factory, lambda: [])
BG.multi_asset_batch_catchup_if_missed(conn_factory, lambda: [], None, gemini_client=object())
pruefe("T7", not z.get("bt_nachgeholt") and not z.get("batch_nachgeholt") and VERB["n"] == 0
       and not any("hole sofort nach" in s for s in LOG.zeilen),
       "stillgelegt: nichts nachgeholt (BT %d, Batch %d), keine DB-Verbindung (%d), keine Zeile 'hole sofort nach'" % (
           z.get("bt_nachgeholt", 0), z.get("batch_nachgeholt", 0), VERB["n"]))
RJ.ALTE_KETTE_STILLGELEGT = False
neu()
BG.backward_tracking_catchup_if_missed(conn_factory, lambda: [])
BG.multi_asset_batch_catchup_if_missed(conn_factory, lambda: [], None, gemini_client=object())
pruefe("T8", z.get("bt_nachgeholt") == 1 and z.get("batch_nachgeholt") == 1
       and sum("hole sofort nach" in s for s in LOG.zeilen) == 2,
       "UMKEHRBAR: BT %s, Batch %s nachgeholt" % (z.get("bt_nachgeholt"), z.get("batch_nachgeholt")))
BG.backward_tracking_job, BG.multi_asset_batch_job = _bt_echt, _mab_echt

# ---- T9 Statusseite: Karte Ausstieg ------------------------------------------------------------------------------------
_roh = ST._get_ausstiegs_empfehlungen.__wrapped__
RJ.ALTE_KETTE_STILLGELEGT = True
neu()
a9 = _roh(None, [])
RJ.ALTE_KETTE_STILLGELEGT = False
b9 = _roh(None, [])
_qs = open(os.path.join("remote", "server.py"), encoding="utf-8").read()
pruefe("T9", a9.get("stillgelegt") == RJ.S2_TEXT and a9["empfehlungen"] == [] and z.get("ausstieg_rechnung") == 1
       and not b9.get("stillgelegt") and "ae.stillgelegt ? \"stillgelegt\"" in _qs and "if (ae.stillgelegt) {" in _qs,
       "Statusseite: stillgelegt -> %s ohne Rechnung; aus -> rechnet (Aufrufe %d); Seite kennt den Zweig" % (
           a9.get("stillgelegt"), z.get("ausstieg_rechnung", 0)))
RJ.ALTE_KETTE_STILLGELEGT = True

# ---- T10/T11 Frage 2: Marktscan fehlt der Schluessel -> AUS --------------------------------------------------------------
KP.compute_current_regime = zaehler("regime", lambda: type("R", (), {"regime": "x"})())
MS.run_scan = zaehler("scan", [])
MBT.run_marktscan_backward_tracking = zaehler("ms_mess", {"neue_messungen": 0, "geprueft": 0, "erfolge": 0, "kein_erfolg": 0,
                                                          "schnellerfolge": []})
BG._notify_marktscan_kaufkandidaten = zaehler("ms_mail")
BG._notify_marktscan_watchlist_heiss = zaehler("ms_mail2")
BG._notify_marktscan_schnellerfolg = zaehler("ms_mail3")
erg10 = []
for cfg, soll in (({}, 0), ({"marktscan": {}}, 0), ({"marktscan": None}, 0), ({"marktscan": {"aktiv": False}}, 0),
                  ({"marktscan": {"aktiv": True, "erfolgsmessung": {"watchlist_heiss_fenster_stunden": 48}}}, 1)):
    _CFG.clear()
    _CFG.update(cfg)
    neu()
    BG.marktscan_job(None, None, conn_factory, lambda: [], None)
    BG.marktscan_backward_tracking_job(None, None, conn_factory, lambda: [], None, gemini_client=object())
    erg10.append((z.get("scan", 0), z.get("ms_mess", 0), z.get("fehlermail", 0), soll))
pruefe("T10", all(s == m == soll and f == 0 for s, m, f, soll in erg10),
       "Marktscan + Erfolgsmessung je Konfiguration (ohne Abschnitt / leer / None / false / true): Scan, Messung, Fehlermail %s" % erg10)
pruefe("T11", not BG.marktscan_lock.locked(), "Marktscan-Sperre nach allen Laeufen frei")

# ---- T12/T13 Frage 2: Thesen fallen im Zweifel auf PAUSIERT -------------------------------------------------------------
KS.run_kategorie_synthese = zaehler("synthese")
KV.run_kategorie_vorschlaege_job = zaehler("vorschlaege")
_lade_echt = R0G.lade
R0G.lade = lambda *a, **k: (_ for _ in ()).throw(ValueError("regel0_betrieb.yaml: unbekannte Schluessel ['kaputt']"))
neu()
BG.kategorie_synthese_job(conn_factory, gemini_client=object())
BG.kategorie_vorschlaege_job(conn_factory)
kaputt = (R0G.thesen_pausiert(), z.get("synthese", 0), z.get("vorschlaege", 0), VERB["n"])
R0G.lade = _lade_echt
fehlt = R0G.lade(os.path.join(ORDNER, "gibt_es_nicht.yaml"))["thesen_pausiert"]
leer_yaml = os.path.join(ORDNER, "ohne_schluessel.yaml")
open(leer_yaml, "w", encoding="utf-8").write("positionswert_eur: 1500\n")
ohne = R0G.lade(leer_yaml)["thesen_pausiert"]
pruefe("T12", kaputt == (True, 0, 0, 0) and fehlt is True and ohne is True and R0G.VORGABE["thesen_pausiert"] is True,
       "Thesen: yaml kaputt -> pausiert %s, Synthese %d, Vorschlaege %d, DB %d · Datei fehlt -> %s · Schluessel fehlt -> %s" % (
           kaputt + (fehlt, ohne)))
neu()
_wieder = R0G.thesen_pausiert({"thesen_pausiert": False})
R0G.thesen_pausiert = lambda werte=None: False
BG.kategorie_synthese_job(conn_factory, gemini_client=object())
BG.kategorie_vorschlaege_job(conn_factory)
pruefe("T13", _wieder is False and z.get("synthese") == 1 and z.get("vorschlaege") == 1,
       "UMKEHRBAR: thesen_pausiert: false -> Synthese %s, Vorschlaege %s" % (z.get("synthese"), z.get("vorschlaege")))

# ---- T14 kein Seiteneffekt auf die Produktion ---------------------------------------------------------------------------
_prod_nachher = fingerabdruck()
pruefe("T14", _prod_vorher == _prod_nachher and z.get("fehlermail", 0) == 0 and not os.path.exists(str(BG.db.DB_PATH)),
       "Standard-DB unveraendert (sha256 .db/-wal: %s) · umgebogener Pfad nie angelegt %s · Fehlermails %d · Wegwerf %s" % (
           "gleich" if _prod_vorher == _prod_nachher else "VERAENDERT", not os.path.exists(str(BG.db.DB_PATH)),
           z.get("fehlermail", 0), ORDNER))
print("\nW-3 S-2 am Seiteneffekt: %d von %d bestanden" % (sum(ERG), len(ERG)))
