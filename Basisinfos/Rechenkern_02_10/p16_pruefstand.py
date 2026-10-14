"""P16 Spot B3 Upbit (12.10.2026, Spot §47.4) - Pruefstand am SEITENEFFEKT: Wegwerf-KOPIE der NB-Sicherung als Produktion, Wegwerf-Ablage,
Upbit gestellt, Versand abgefangen. Die NB-Sicherung selbst wird nie geoeffnet ausser zum Kopieren.

    python Basisinfos/Rechenkern_02_10/p16_pruefstand.py <NB-Sicherung tradinginfotool.db>

  S1  erster Lauf: Startmarke - Meldungen abgelegt, KEIN Fall, Protokoll 'upbit startmarke'
  S2  neues KRW-Listing eines Kreis-Coins (BEAMX, 1 h alt), Schalter an -> genau EINE Mail 'BEAMX verkaufen', ganze Menge frei + gestakt;
      zweiter Lauf -> keine weitere Mail
  S3  Listing eines Coins nicht im Bestand und eines Kern-Coins (BTC) -> kein Fall
  S4  CANTON ueber die Zuordnung (Upbit-Kuerzel CC) -> Fall CANTON
  S5  Listing 7 h alt -> 'verpasst', keine Mail
  S6  Schalter aus -> Fall 'faellig', Protokoll, KEINE Mail; danach eingeschaltet (noch <= 6 h) -> Mail kommt nach
  S7  dieselbe Meldung ein zweites Mal -> kein zweiter Fall
  S8  Upbit-Fehler -> Lauf ok=0 mit Fehlertext, keine Ausnahme nach aussen, Job meldet gelaufen
  S9  Kreis ohne KRW = L-Bestaende minus gestellter KRW-Markt (abgeleitet, nicht aufgezaehlt)
  S10 Statusseite/Teilexport: betriebslage.spot_upbit liefert Laeufe, Faelle, Kreis
  S11 die Wegwerf-Produktion bleibt unveraendert (Pruefsumme) - der Job schreibt nur die Ablage
"""
import hashlib
import os
import shutil
import sqlite3
import sys
import tempfile
from datetime import datetime, timedelta, timezone

WURZEL = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, WURZEL)
__import__("sys").path.append(__import__("os").path.abspath(__file__).split("TradingInfoTool")[0] + "TradingInfoTool")  # wegwerf.py
import wegwerf  # noqa: E402,F401  Wegwerf-Ordner auf D: und Aufraeumen ohne stilles Scheitern (15.10.2026)
os.chdir(WURZEL)
import agent.regel0_groesse as G  # noqa: E402
import agent.spot_mitnahme as SM  # noqa: E402
import agent.spot_upbit as SU  # noqa: E402
import config as C  # noqa: E402
import scheduler.background as BG  # noqa: E402
from agent import betriebslage as BL  # noqa: E402

ERG = []


def pruefe(k, ok, text):
    ERG.append(bool(ok))
    print("%-4s %-9s %s" % (k, "bestanden" if ok else "FEHLER", text))


def summe(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


T = tempfile.mkdtemp(prefix="p16_")
PROD = os.path.join(T, "prod.db")
shutil.copy(sys.argv[1], PROD)
vor = summe(PROD)
ABL = os.path.join(T, "ablage")
os.makedirs(ABL)
WL = C.get_watchlist()
conn_factory = lambda: sqlite3.connect("file:%s?mode=ro" % PROD.replace("\\", "/"), uri=True)   # noqa: E731
kreis = SM.kreis(conn_factory(), WL)
KRW = ["KRW-ALGO", "KRW-AVAX", "KRW-LINK", "KRW-NEAR", "KRW-SUI", "KRW-XLM", "KRW-INJ", "KRW-KAIA", "KRW-SEI", "KRW-TAO", "KRW-W", "KRW-BIO",
       "KRW-MORPHO", "KRW-PLUME", "KRW-MON", "BTC-BEAMX"]           # CANTON (CC) bewusst NICHT, BEAMX nur im BTC-Markt
J0 = datetime(2026, 10, 12, 9, 0, tzinfo=timezone.utc)
MELD = []
FEHLER = {"an": False}


def meldung(i, titel, alter_h, jetzt):
    MELD.insert(0, {"id": i, "title": titel, "first_listed_at": (jetzt - timedelta(hours=alter_h)).isoformat(), "listed_at": None})


def http(url, params):
    if FEHLER["an"]:
        raise ConnectionError("Upbit gestellt nicht erreichbar")
    if url == SU.MAERKTE:
        return [{"market": m} for m in KRW]
    seite = (params or {}).get("page", 1)
    return {"data": {"notices": MELD if seite == 1 else []}}


POST = []


def versand(b, t, bilder=None):
    POST.append((b, t))
    return True


SCHALTER = {"an": True}
G.spot_upbit_aktiv = lambda werte=None: SCHALTER["an"]


def job(jetzt):
    return BG.spot_upbit_job(conn_factory, lambda: WL, versand=versand, jetzt=jetzt, ordner=ABL, http=http)


# S1
meldung(900, "알트코인(ALT) 신규 거래지원 안내 (KRW 마켓)", 30, J0)
r = job(J0)
c = sqlite3.connect(os.path.join(ABL, SM.ABLAGE))
n_fall = c.execute("SELECT COUNT(*) FROM upbit_fall").fetchone()[0]
pruefe("S1", r.get("startmarke") and n_fall == 0 and not POST and c.execute("SELECT COUNT(*) FROM protokoll WHERE art='upbit startmarke'").fetchone()[0] == 1,
       "erster Lauf: Startmarke %s · Faelle %d · Mails %d" % (r.get("startmarke"), n_fall, len(POST)))
# S9
soll = sorted(s for s in kreis if {"CANTON": "CC"}.get(s, s) not in {m.split("-")[1] for m in KRW if m.startswith("KRW-")})
pruefe("S9", r.get("ohne_krw") == soll and "BEAMX" in soll and "ALGO" not in soll and "CANTON" in soll,
       "Kreis ohne KRW %d (abgeleitet %d) · BEAMX drin, ALGO nicht, CANTON drin" % (len(r.get("ohne_krw") or []), len(soll)))
# S2
J1 = J0 + timedelta(hours=1)
meldung(901, "빔엑스(BEAMX) 신규 거래지원 안내 (KRW, USDT 마켓)", 1, J1)
r = job(J1)
m = [p for p in POST if "BEAMX" in p[0]]
menge = kreis.get("BEAMX")
pruefe("S2", len(m) == 1 and "GANZE Position" in m[0][1] and "erst positiv und dann negativ" in m[0][1] and "gemessen ist nur der Kursverlauf" in m[0][1] and SM._menge(menge) in m[0][1] and m[0][0].startswith("TradingInfoTool: Spot: BEAMX verkaufen"),
       "Mail %d · Betreff %s · Menge %s" % (len(m), m[0][0] if m else "-", SM._menge(menge) if menge else "-"))
r2 = job(J1 + timedelta(minutes=30))
pruefe("S2b", len([p for p in POST if "BEAMX" in p[0]]) == 1, "zweiter Lauf: Mails BEAMX weiter %d" % len([p for p in POST if "BEAMX" in p[0]]))
# S3
J3 = J1 + timedelta(hours=1)
meldung(902, "엑스(XYZQ) 신규 거래지원 안내 (KRW 마켓)", 1, J3)
meldung(903, "비트코인(BTC) 신규 거래지원 안내 (KRW 마켓)", 1, J3)
n_vor = len(POST)
r = job(J3)
pruefe("S3", not r["faelle"] and len(POST) == n_vor, "XYZQ (nicht im Bestand) und BTC (Kern): Faelle %d, neue Mails %d" % (len(r["faelle"]), len(POST) - n_vor))
# S4
J4 = J3 + timedelta(hours=1)
meldung(904, "캔톤(CC) 신규 거래지원 안내 (KRW 마켓)", 2, J4)
r = job(J4)
pruefe("S4", [f["symbol"] for f in r["faelle"]] == ["CANTON"] and any("CANTON verkaufen" in p[0] and "(CC)" in p[1] for p in POST),
       "Faelle %s · Mail CANTON (CC) %s" % ([f["symbol"] for f in r["faelle"]], any("CANTON verkaufen" in p[0] for p in POST)))
# S5
J5 = J4 + timedelta(hours=1)
meldung(905, "하이프(HYPE) 신규 거래지원 안내 (KRW 마켓)", 7, J5)
n_vor = len(POST)
r = job(J5)
st5 = c.execute("SELECT status FROM upbit_fall WHERE id=905").fetchone()
pruefe("S5", st5 and st5[0] == "verpasst" and len(POST) == n_vor, "HYPE 7 h alt: Status %s, neue Mails %d" % (st5, len(POST) - n_vor))
# S6
J6 = J5 + timedelta(hours=1)
SCHALTER["an"] = False
meldung(906, "퀀트(QNT) 신규 거래지원 안내 (KRW 마켓)", 1, J6)
n_vor = len(POST)
r = job(J6)
st6 = c.execute("SELECT status FROM upbit_fall WHERE id=906").fetchone()
aus_ok = st6 and st6[0] == "faellig" and len(POST) == n_vor and r.get("schalter") is False
SCHALTER["an"] = True
r = job(J6 + timedelta(hours=2))
pruefe("S6", aus_ok and any("QNT verkaufen" in p[0] for p in POST), "Schalter aus: Status %s, keine Mail; eingeschaltet 3 h nach der Meldung: Mail QNT %s" % (
    st6, any("QNT verkaufen" in p[0] for p in POST)))
# S7
n_fall = c.execute("SELECT COUNT(*) FROM upbit_fall").fetchone()[0]
MELD.insert(0, dict(MELD[[x["id"] for x in MELD].index(901)]))
r = job(J6 + timedelta(hours=3))
pruefe("S7", c.execute("SELECT COUNT(*) FROM upbit_fall").fetchone()[0] == n_fall, "dieselbe Meldung erneut: Faelle %d -> %d" % (
    n_fall, c.execute("SELECT COUNT(*) FROM upbit_fall").fetchone()[0]))
# S8
FEHLER["an"] = True
r = job(J6 + timedelta(hours=4))
fl = c.execute("SELECT ok, fehler FROM upbit_lauf ORDER BY am DESC LIMIT 1").fetchone()
FEHLER["an"] = False
pruefe("S8", r.get("gelaufen") and r.get("ok") is False and fl[0] == 0 and "ConnectionError" in (fl[1] or ""), "Upbit-Fehler: Job gelaufen %s, ok %s, Lauf %s" % (
    r.get("gelaufen"), r.get("ok"), fl))
# S10
s = BL.spot_upbit(ABL)
pruefe("S10", s.get("laeufe", 0) >= 8 and s.get("ok", 0) == s["laeufe"] - 1 and dict(s["je_status"]).get("gemailt") == 3 and s["letzter_fehler"],
       "Stand: Laeufe %s, ok %s, je Status %s, letzter Fehler %s" % (s.get("laeufe"), s.get("ok"), s.get("je_status"), bool(s.get("letzter_fehler"))))
c.close()
# S11
pruefe("S11", summe(PROD) == vor, "Wegwerf-Produktion %s" % ("unveraendert" if summe(PROD) == vor else "GEAENDERT"))
print("\nMuster der Mail (S2):\n" + (m[0][1] if m else "-"))
wegwerf.aufraeumen(T)
print("\n%d von %d bestanden" % (sum(ERG), len(ERG)))
