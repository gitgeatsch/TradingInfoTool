"""O21 Stufe 1 REGEL0-Messstand (17.10.2026, Schritt7 §23.64) - Pruefstand am SEITENEFFEKT. Nur Wegwerf-Dateien.

    python Basisinfos/Rechenkern_02_10/o21_pruefstand.py <Kopie regel0_signale.db> <NB-Sicherung .db.gz>

NB-Lage: Wegwerf-Ordner mit der Kopie der REGEL0-Ablage (14.10.), Stundenkursen aus Binance-Kerzen (Markt und Paar wie im Signal,
in stundenkurse_alle.db - der Ordner hat wie am NB zwei Kursdateien) und einer Wegwerf-Kopie der NB-Sicherung (Hebel-Buch).

  S1  R-R11: ``ausgang`` auf den Desktop-Kursen fuer die Referenz 2026 (3.693 Einstiege) - t_u / t_d gleich der CSV, Q gleich
  S2  ``lauf`` auf der Oktober-Lage: gemessen wie p61 Teil 2 (eigener Rechenweg): n 532, Mittel +0,737 %, Q +0,094; ohne Kurse begruendet
  S3  idempotent: zweiter Lauf schreibt nichts neu; Zeitreise: am 10.10. sind spaetere Signale 'offen' und NICHT geschrieben
  S4  24 h fertig, 72 h endgueltig: ein Lauf 30 h nach dem Einstieg hat e24 und endgueltig 0; der spaetere Lauf macht ihn endgueltig
  S5  Befund: unter MIN_TAGE 'zu wenige Tage'; ein um -10 % verschobener Betrieb ist 'UNTER der Messung'
  S6  Mail: mit messstand die Zeile 'Messstand' (Tage, Spanne, Messung, Kostenhinweis) und die Technikzeile; ohne sie wie vorher;
      der Versandweg bekommt den Lieferanten (scheitert er, geht die Mail trotzdem)
  S7  echte Trades: ETH -> Signal 09.10. 06:00, Verzug 1,5 h, 149 h; BTC ohne Signal (wie p61 Teil 3)
  S8  Job: mit Wegwerf-Ordner fehlerfrei, Logzeilen; Statusseite, Teilexport, Diagnose lesen den Stand
  S9  kein Seiteneffekt: Quelle der Ablage, Wegwerf-Produktion und die Desktop-Kursdateien unveraendert
"""
import gzip
import hashlib
import logging
import os
import shutil
import sqlite3
import sys
import tempfile
from datetime import datetime, timedelta, timezone

WURZEL = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, WURZEL)
import wegwerf  # noqa: E402
os.chdir(WURZEL)
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

import agent.regel0_mail as RM  # noqa: E402
import agent.regel0_messstand as MS  # noqa: E402
import agent.regel0_nachlader as NL  # noqa: E402

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:  # noqa: BLE001
    pass
QUELLE, SICHERUNG = os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2])
ERG = []
LOG = []


class _Fang(logging.Handler):
    def emit(self, rec):
        LOG.append(rec.getMessage())


logging.getLogger().addHandler(_Fang())
logging.getLogger().setLevel(logging.INFO)


def pruefe(k, ok, text):
    ERG.append(bool(ok))
    print("%-3s %-9s %s" % (k, "bestanden" if ok else "FEHLER", text))


def summe(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


vor_quelle = summe(QUELLE)
vor_desk = {n: (os.path.getsize(os.path.join("data", n)), os.path.getmtime(os.path.join("data", n))) for n in MS.KURSE}
T = tempfile.mkdtemp(prefix="o21_")
O = os.path.join(T, "daten")
os.makedirs(O)
shutil.copy(QUELLE, os.path.join(O, "regel0_signale.db"))
PROD = os.path.join(T, "prod.db")
with gzip.open(SICHERUNG, "rb") as f, open(PROD, "wb") as g:
    shutil.copyfileobj(f, g)
vor_prod = summe(PROD)

# ── Kursdateien wie am NB (aus Binance-Kerzen) ────────────────────────────────────────────────────────────────────────────────
k = sqlite3.connect("file:%s?mode=ro" % os.path.join(O, "regel0_signale.db").replace("\\", "/"), uri=True)
S = pd.read_sql("SELECT symbol, signalstunde, einstieg, kurs_markt, paar FROM signal", k)
k.close()
jetzt_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
z = sqlite3.connect(os.path.join(O, "stundenkurse_alle.db"))
z.execute("CREATE TABLE stundenkurse (symbol TEXT NOT NULL, stunde TEXT NOT NULL, open REAL, high REAL, low REAL, close REAL, volumen REAL, "
          "PRIMARY KEY (symbol, stunde))")
sqlite3.connect(os.path.join(O, "stundenkurse.db")).execute(
    "CREATE TABLE stundenkurse (symbol TEXT NOT NULL, stunde TEXT NOT NULL, open REAL, high REAL, low REAL, close REAL, volumen REAL, "
    "PRIMARY KEY (symbol, stunde))").connection.close()
for (sym, markt, paar), _g in S.groupby([S.symbol, S.kurs_markt.fillna("spot"), S.paar.fillna(S.symbol + "USDT")]):
    try:
        kz = NL._hole(NL.FUT[1] if markt == "futures" else NL.SPOT[1], paar, NL._ms("2026-10-02 00:00"), jetzt_ms)
    except Exception:                                                         # noqa: BLE001
        continue
    z.executemany("INSERT OR IGNORE INTO stundenkurse VALUES (?,?,?,?,?,?,?)",
                  [(sym, NL._stunde(int(x[0])), float(x[1]), float(x[2]), float(x[3]), float(x[4]), float(x[5])) for x in kz])
z.commit()
z.close()

# ── S1 R-R11 auf der Referenz ─────────────────────────────────────────────────────────────────────────────────────────────────
E = pd.read_csv(os.path.join("data", "_vergleich", "kern48jbz_einstiege_bestand.csv"), sep=";")
G = E[E.jahr == 2026]
B0 = datetime(2020, 1, 1)
jetzt_ref = datetime(2026, 9, 25)
gl, n, okq = 0, 0, 0
for r in G.itertuples():
    ein = (B0 + timedelta(hours=int(r.stunde))).strftime("%Y-%m-%d %H:%M")
    a = MS.ausgang("data", r.symbol, ein, jetzt_ref)
    if a["status"] != "ok":
        continue
    n += 1
    tu, td = str(a["t_u"]), str(a["t_d"])
    gl += int(tu == str(r.t_u) and td == str(r.t_d))
    tur = 999 if str(r.t_u) in ("", "nan") else int(r.t_u)
    tdr = 999 if str(r.t_d) in ("", "nan") else int(r.t_d)
    okq += int(a["q"] == (1 if (tur <= 24 and tur < tdr) else (-1 if (tdr <= 24 and tdr <= tur) else 0)))
pruefe("S1", gl == n == len(G) and okq == n, "Referenz 2026: %d von %d gemessen, t_u/t_d gleich %d, Q gleich %d" % (n, len(G), gl, okq))

# ── S2 Oktober ────────────────────────────────────────────────────────────────────────────────────────────────────────────────
JETZT = datetime(2026, 10, 17, 6, 0)
e2 = MS.lauf(O, JETZT)
st = MS.stand(O, JETZT)
g = st["gesamt"]
# ⚠️ KORREKTUR 17.10. (erster Lauf rot - Fehler im PRUEFSTAND): der Bezug waren die festen Zahlen von p61 (532 Signale) - dort war der
# Abruf von AIOT und ELSA gescheitert, hier nicht (558). Jetzt je Signal gegen die Schleife aus p61 Teil 2 auf DENSELBEN Kursen.
kz2 = {}
k2 = sqlite3.connect("file:%s?mode=ro" % os.path.join(O, "stundenkurse_alle.db").replace("\\", "/"), uri=True)
for sym_, st_, h_, l_, c_ in k2.execute("SELECT symbol, stunde, high, low, close FROM stundenkurse"):
    kz2.setdefault(sym_, {})[st_] = (h_, l_, c_)
k2.close()
k2 = sqlite3.connect("file:%s?mode=ro" % os.path.join(O, "regel0_signale.db").replace("\\", "/"), uri=True)
aus2 = {(r_[0], r_[1]): r_[2:] for r_ in k2.execute("SELECT symbol, signalstunde, status, e24, q FROM ausgang")}
sig2 = k2.execute("SELECT symbol, signalstunde, einstieg FROM signal").fetchall()
k2.close()
gl2, n2, oh2 = 0, 0, 0
for sym_, sh_, ein_ in sig2:
    kk = kz2.get(sym_, {})
    e_ = datetime.strptime(ein_, "%Y-%m-%d %H:%M")
    h_ = [kk.get((e_ + timedelta(hours=s_)).strftime("%Y-%m-%d %H:%M")) for s_ in range(0, 25)]
    if any(x is None for x in h_):
        oh2 += int(aus2.get((sym_, sh_), ("",))[0] == "ohne_kurse")
        continue
    cc_ = h_[0][2]
    tu_ = next((s_ for s_ in range(1, 25) if h_[s_][0] >= 1.05 * cc_), 999)
    td_ = next((s_ for s_ in range(1, 25) if h_[s_][1] <= 0.95 * cc_), 999)
    q_ = 1 if (tu_ <= 24 and tu_ < td_) else (-1 if (td_ <= 24 and td_ <= tu_) else 0)
    m_ = aus2.get((sym_, sh_))
    n2 += 1
    gl2 += int(m_ is not None and m_[0] == "ok" and abs(m_[1] - (h_[24][2] / cc_ - 1)) < 1e-12 and m_[2] == q_)
pruefe("S2", gl2 == n2 == g["n"] and oh2 == e2["ohne_kurse"],
       "Lauf %s · je Signal gegen die Schleife aus p61 Teil 2: %d von %d gleich (e24 und Q), ohne Kurse beidseits %d · gesamt n %d an %d Tagen, "
       "Mittel %+.3f %%, Q %+.3f, Halbbreite %.2f Pp · Befund '%s'" % (e2, gl2, n2, oh2, g["n"], g["tage"], 100 * g["mittel"], g["q"],
                                                                     100 * g["halb"], st["befund"]))

# ── S3 idempotent + Zeitreise ─────────────────────────────────────────────────────────────────────────────────────────────────
e3 = MS.lauf(O, JETZT)
O3 = os.path.join(T, "zeit")
os.makedirs(O3)
for nm in ("regel0_signale.db", "stundenkurse.db", "stundenkurse_alle.db"):
    shutil.copy(os.path.join(O, nm), os.path.join(O3, nm))
c3 = sqlite3.connect(os.path.join(O3, "regel0_signale.db"))
c3.execute("DELETE FROM ausgang")
c3.commit()
c3.close()
e3b = MS.lauf(O3, datetime(2026, 10, 10, 0, 0))
c3 = sqlite3.connect("file:%s?mode=ro" % os.path.join(O3, "regel0_signale.db").replace("\\", "/"), uri=True)
spaet = c3.execute("SELECT COUNT(*) FROM ausgang WHERE einstieg > '2026-10-08 23:00'").fetchone()[0]
c3.close()
pruefe("S3", e3["neu"] == 0 and e3["ok"] == 0 and e3b["offen"] > 0 and spaet == 0,
       "zweiter Lauf %s · Lauf am 10.10.: %s, Ausgaenge nach Einstieg 08.10. 23:00 geschrieben: %d" % (e3, e3b, spaet))

# ── S4 24 h / 72 h ────────────────────────────────────────────────────────────────────────────────────────────────────────────
c4 = sqlite3.connect("file:%s?mode=ro" % os.path.join(O, "regel0_signale.db").replace("\\", "/"), uri=True)
sym4, sh4, ein4 = c4.execute("SELECT symbol, signalstunde, einstieg FROM ausgang WHERE status='ok' ORDER BY signalstunde LIMIT 1").fetchone()
c4.close()
a30 = MS.ausgang(O, sym4, ein4, datetime.strptime(ein4, "%Y-%m-%d %H:%M") + timedelta(hours=30))
a80 = MS.ausgang(O, sym4, ein4, datetime.strptime(ein4, "%Y-%m-%d %H:%M") + timedelta(hours=80))
a20 = MS.ausgang(O, sym4, ein4, datetime.strptime(ein4, "%Y-%m-%d %H:%M") + timedelta(hours=20))
pruefe("S4", a20["status"] == "offen" and a30["status"] == "ok" and a30["endgueltig"] == 0 and a80["endgueltig"] == 1
       and a30["e24"] == a80["e24"] and a30["q"] == a80["q"],
       "%s Einstieg %s: nach 20 h %s · nach 30 h e24 %+.4f endgueltig %s · nach 80 h e24 %+.4f endgueltig %s (t_u %s / %s)" % (
           sym4, ein4, a20["status"], a30["e24"], a30["endgueltig"], a80["e24"], a80["endgueltig"], a30["t_u"], a80["t_u"]))

# ── S5 Befund ─────────────────────────────────────────────────────────────────────────────────────────────────────────────────
k5 = MS._kennzahl([("2026-10-0%d" % (i % 5 + 1), 0.01, 1) for i in range(50)])
k6 = dict(g, mittel=g["mittel"] - 0.10, tage=max(g["tage"], MS.MIN_TAGE))
pruefe("S5", MS._befund(k5).startswith("zu wenige Tage") and MS._befund(k6) == "UNTER der Messung" and
       MS._befund(dict(g, tage=max(g["tage"], MS.MIN_TAGE))) in ("im Band der Messung", "über der Messung"),
       "5 Tage: '%s' · um -10 %% verschoben: '%s' · echt (Tage auf %d gesetzt): '%s'" % (
           MS._befund(k5), MS._befund(k6), max(g["tage"], MS.MIN_TAGE), MS._befund(dict(g, tage=max(g["tage"], MS.MIN_TAGE)))))

# ── S6 Mail ───────────────────────────────────────────────────────────────────────────────────────────────────────────────────
import agent.regel0_groesse as GR  # noqa: E402
c6 = sqlite3.connect("file:%s?mode=ro" % os.path.join(O, "regel0_signale.db").replace("\\", "/"), uri=True)
c6.row_factory = sqlite3.Row
r6 = dict(c6.execute("SELECT * FROM signal WHERE hebel_schalter=1 ORDER BY signalstunde LIMIT 1").fetchone())
c6.close()
w6 = GR.lade()
mt = MS.mailteil(O)
_b1, t_ohne = RM.signal_mail(r6, r6["stufe"], False, GR.rechne(r6["stufe"], 0, w6), w6, JETZT.replace(tzinfo=timezone.utc))
_b2, t_mit = RM.signal_mail(r6, r6["stufe"], False, GR.rechne(r6["stufe"], 0, w6), w6, JETZT.replace(tzinfo=timezone.utc), messstand=mt)
zeile = mt["ein"]
qb = open("scheduler/background.py", encoding="utf-8").read()
qm = open("agent/regel0_mail.py", encoding="utf-8").read()
_flach = " ".join(t_mit.split())
pruefe("S6", "Messstand im Betrieb seit" in _flach and zeile in _flach and "Tagen" in zeile and "Spanne 99 %" in zeile and "0,48 %" in zeile and "Messstand im Betrieb" not in t_ohne
       and 'messstand=lambda r: __import__("agent.regel0_messstand"' in qb and "_ms = messstand(r)" in qm and "except Exception as exc" in qm.split("_ms = messstand(r)")[1][:200],
       "Zeile: '%s'" % zeile)

# ── S7 echte Trades ───────────────────────────────────────────────────────────────────────────────────────────────────────────
cp = sqlite3.connect("file:%s?mode=ro" % PROD.replace("\\", "/"), uri=True)
tr = MS.trades(cp, O)
cp.close()
d7 = {t["symbol"]: t for t in tr}
pruefe("S7", "ETH" in d7 and d7["ETH"]["signal"] == "2026-10-09 06:00" and abs(d7["ETH"]["verzug_h"] - 1.5) < 0.1 and round(d7["ETH"]["dauer_h"]) == 149
       and "BTC" in d7 and d7["BTC"]["signal"] is None,
       " | ".join(MS.trade_text(t) for t in tr))

# ── S8 Job + Anzeige ──────────────────────────────────────────────────────────────────────────────────────────────────────────
import scheduler.background as BG  # noqa: E402
import agent.betriebslage as BL  # noqa: E402
LOG.clear()
j = BG.regel0_messstand_job(lambda: sqlite3.connect("file:%s?mode=ro" % PROD.replace("\\", "/"), uri=True), ordner=O, jetzt=JETZT)
cp = sqlite3.connect("file:%s?mode=ro" % PROD.replace("\\", "/"), uri=True)
bl = BL.regel0_messstand(O, cp)
cp.close()
qs, qd, qt = (open(p, encoding="utf-8").read() for p in ("remote/server.py", "extract_notebook_diagnose.py", "nb_teilexport_betriebsdaten.py"))
pruefe("S8", j["gelaufen"] and any(x.startswith("REGEL0-Messstand: neu") for x in LOG) and any("Trade: ETH" in x for x in LOG)
       and bl["vorhanden"] and bl["zeile"] == zeile and len(bl["trades"]) == 2 and "renderMessstand(data.regel0_messstand)" in qs
       and '"regel0_messstand": _regel0_messstand()' in qd and "REGEL0-MESSSTAND (O21)" in qt,
       "Job %s · Log: %s" % ({k_: j[k_] for k_ in ("gelaufen", "neu", "ok", "befund")}, [x for x in LOG if "Messstand" in x][:1]))

# ── S9 kein Seiteneffekt ──────────────────────────────────────────────────────────────────────────────────────────────────────
nach_desk = {n: (os.path.getsize(os.path.join("data", n)), os.path.getmtime(os.path.join("data", n))) for n in MS.KURSE}
pruefe("S9", summe(QUELLE) == vor_quelle and summe(PROD) == vor_prod and nach_desk == vor_desk,
       "Quelle der Ablage, Wegwerf-Produktion und Desktop-Kursdateien unveraendert")
wegwerf.aufraeumen(T)
print("\n%d von %d bestanden" % (sum(ERG), len(ERG)))
sys.exit(0 if all(ERG) else 1)
