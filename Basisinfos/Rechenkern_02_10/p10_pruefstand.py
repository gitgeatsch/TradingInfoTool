"""P10 / O42 (11.10.2026) - Thesen pausieren: Pruefstand OHNE Netz, LLM und Datenbank.

    python Basisinfos/Rechenkern_02_10/p10_pruefstand.py

Die beiden Jobfunktionen aus scheduler/background.py laufen gegen eine WEGWERF-Schalterdatei (``regel0_groesse.DATEI``
umgebogen). Die Arbeit selbst (``run_kategorie_vorschlaege_job``, ``run_kategorie_synthese``) ist durch Attrappen ersetzt, die nur
zaehlen; ``conn_factory`` und der Gemini-Client zaehlen ebenfalls. So ist nachgewiesen, WER aufgerufen wird - nicht nur, was im Log steht.

  T1 Schalter AN: beide Jobs enden sofort - keine Verbindung, kein Abgleich, kein LLM-Aufruf; Logzeile "Thesen pausiert"
  T2 Schalter AUS: beide Jobs arbeiten wie vor P10 (Verbindung, Abgleich, Synthese mit dem Gemini-Client)
  T3 Schluessel FEHLT: wie AUS (Vorgabe = bisheriges Verhalten)
  T4 Datei UNLESBAR / falscher Typ: thesen_pausiert() = NEIN (laeuft weiter), lade() bricht laut ab (wie bei jedem Schalter)
  T5 die echte Basisinfos/regel0_betrieb.yaml: alle Leser laufen (lade, VORGABE = Datei, Schalterkarte, H15-Grenze), Schalter AN
  T6 die Wache im Scheduler bleibt: Zeile llm_clients = [("gemini", gemini_client)] unveraendert, Pruefung VOR dem Client
"""
import io
import logging
import os
import sys
import tempfile

WURZEL = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, WURZEL)
__import__("sys").path.append(__import__("os").path.abspath(__file__).split("TradingInfoTool")[0] + "TradingInfoTool")  # wegwerf.py
import wegwerf  # noqa: E402,F401  Wegwerf-Ordner auf D: und Aufraeumen ohne stilles Scheitern (15.10.2026)
os.chdir(WURZEL)

import agent.kategorie_synthese as KS  # noqa: E402
import agent.kategorie_vorschlaege as KV  # noqa: E402
import agent.regel0_groesse as G  # noqa: E402
import scheduler.background as BG  # noqa: E402

ERG = []
ZAEHLER = {}


def pruefe(k, ok, text):
    ERG.append(ok)
    print("%-3s %-9s %s" % (k, "bestanden" if ok else "FEHLER", text))


def zaehl(name):
    ZAEHLER[name] = ZAEHLER.get(name, 0) + 1


class Verbindung:
    def close(self):
        zaehl("close")


def conn_factory():
    zaehl("verbindung")
    return Verbindung()


class Gemini:
    def chat(self, *a, **k):
        zaehl("llm")
        raise AssertionError("die Attrappe der Synthese ruft chat nie selbst")


def vorschlaege_attrappe(conn):
    zaehl("abgleich_vorschlaege")


def synthese_attrappe(conn, clients):
    zaehl("synthese")
    assert clients and clients[0][0] == "gemini" and clients[0][1] is not None
    return None                                         # wie "kein Ergebnis" - keine Mail


KV.run_kategorie_vorschlaege_job = vorschlaege_attrappe
KS.run_kategorie_synthese = synthese_attrappe
log = io.StringIO()
h = logging.StreamHandler(log)
logging.getLogger("scheduler.background").addHandler(h)
logging.getLogger("scheduler.background").setLevel(logging.INFO)


def lauf(yaml_text):
    ZAEHLER.clear()
    log.truncate(0)
    log.seek(0)
    with tempfile.TemporaryDirectory() as t:
        p = os.path.join(t, "regel0_betrieb.yaml")
        if yaml_text is not None:
            open(p, "w", encoding="utf-8").write(yaml_text)
        alt = G.DATEI
        G.DATEI = p
        try:
            BG.kategorie_vorschlaege_job(conn_factory)
            BG.kategorie_synthese_job(conn_factory, None, None, Gemini())
        finally:
            G.DATEI = alt
    return dict(ZAEHLER), log.getvalue()


z, l = lauf("thesen_pausiert: true\n")
pruefe("T1", z == {} and l.count("Thesen pausiert (O42") == 2, "Zaehler %s · Logzeilen 'pausiert' %d" % (z, l.count("Thesen pausiert (O42")))
z, l = lauf("thesen_pausiert: false\n")
pruefe("T2", z.get("verbindung") == 2 and z.get("abgleich_vorschlaege") == 1 and z.get("synthese") == 1 and "pausiert" not in l,
       "Zaehler %s" % z)
z, l = lauf("positionswert_eur: 1500\n")
pruefe("T3", z.get("abgleich_vorschlaege") == 1 and z.get("synthese") == 1 and "pausiert" not in l, "ohne Schluessel: %s" % z)
with tempfile.TemporaryDirectory() as t:
    p = os.path.join(t, "x.yaml")
    open(p, "w", encoding="utf-8").write("thesen_pausiert: ja\n")
    try:
        G.lade(p)
        laut = False
    except ValueError:
        laut = True
    alt = G.DATEI
    G.DATEI = p
    still = G.thesen_pausiert()
    G.DATEI = alt
pruefe("T4", laut and still is False, "falscher Typ: lade() bricht ab %s · thesen_pausiert() %s (laeuft weiter)" % (laut, still))

import agent.betriebslage as BL  # noqa: E402
import agent.hebelfuehrung as HF  # noqa: E402

w = G.lade()
sch = BL.schalter()
pruefe("T5", set(w) == set(G.VORGABE) and w["thesen_pausiert"] is True and sch.get("thesen_pausiert") is True
       and 0 < float(w["liquidations_warnung_abstand"]) < 1 and bool(HF.LIQ_STUFEN),
       "Datei = Vorgabe %s · Schalter %s · Warnabstand %s" % (set(w) == set(G.VORGABE), sch.get("thesen_pausiert"),
                                                              w["liquidations_warnung_abstand"]))
src = open(os.path.join("scheduler", "background.py"), encoding="utf-8").read()
syn = src[src.index("def kategorie_synthese_job"):src.index("def ", src.index("def kategorie_synthese_job") + 10)]
pruefe("T6", 'llm_clients = [("gemini", gemini_client)]' in src
       and syn.index("_G.thesen_pausiert()") < syn.index('llm_clients = [("gemini", gemini_client)]') < syn.index("conn_factory()"),
       "Wache im Scheduler unveraendert, Schalter vor Client und Verbindung")
print()
print("%d von %d bestanden" % (sum(ERG), len(ERG)))
