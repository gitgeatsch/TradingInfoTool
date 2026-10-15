"""O54 Makro-Lage (15.10.2026, Schritt7 §23.57) - Pruefstand am SEITENEFFEKT, nur Wegwerf-Dateien (D:). Liest FRED live (frei, mit
Schluessel aus .env, nur lesend) - wie am NB.

    python Basisinfos/Rechenkern_02_10/o54_pruefstand.py > Basisinfos/Rechenkern_02_10/o54_pruefstand.txt

  M1  R-R11 BITGLEICH: dieselben Rohreihen durch agent.makro_lage.scores und durch p51_vorpruefung.kanaele/scores (fred() auf die
      Rohreihen umgebogen, Verzug je Reihe geprueft) -> alle 20 Score-Reihen an allen Tagen gleich
  M2  Gesamt lang/kurz an den Monatsstichtagen gegen die gespeicherten Scores der Messung §51.7 (fredgraph.csv): mit vollem Fenster
      alle gleich, ueber die ganze Historie ab 2011-04 mindestens 95 % (Rest = Datenrevisionen)
  M3  lage_aus: heutiger Stand = letzte Zeile von M1; Treiber = die Kanaele in Richtung des Gesamt
  M4  drei Zustaende (fehlt / veraltet / ok) in Zeile und stand(); Fehlervermerk sichtbar
  M5  lauf() mit kaputtem Abruf: alter Stand bleibt MIT Vermerk, Schluessel nicht im Text; ohne alten Stand -> 'fehlt'
  M6  Mails: REGEL0 (Einschaetzung + Technik, Text + HTML, ohne bitgleich, kaputter Lieferant haelt den Versand nicht auf);
      B1/B3/B4 mit Zeile, ohne bitgleich
  M7  Statusseite: Abschnitt Makro VOR Betrieb & Lage, Getter liefert stand(), Render-Code liest data.makro_lage
  M8  Job externe_reihen ruft lauf() und faengt jeden Fehler; Desktop-Prod und die echte Ablage unveraendert
"""
import hashlib
import io
import os
import pickle
import sqlite3
import sys
import tempfile
from contextlib import redirect_stdout
from datetime import date, datetime, timedelta, timezone

WURZEL = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(WURZEL)
sys.path.insert(0, WURZEL)
sys.path.insert(0, os.path.join(WURZEL, "Basisinfos", "Spot_Voranalyse_04_10"))
sys.stdout.reconfigure(encoding="utf-8")
import wegwerf  # noqa: E402,F401  Wegwerf-Ordner auf D: und Aufraeumen ohne stilles Scheitern (15.10.2026)

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

import config  # noqa: E402
import agent.makro_lage as ML  # noqa: E402
import agent.regel0_groesse as G  # noqa: E402
import agent.regel0_mail as RM  # noqa: E402
import agent.spot_abbau as SA  # noqa: E402
import agent.spot_mitnahme as SM  # noqa: E402
import agent.spot_upbit as SU  # noqa: E402
from database import db  # noqa: E402

config.load_env()
KEY = os.environ.get("FRED_API_KEY", "")
ERG = []


def pruefe(k, ok, text):
    ERG.append(bool(ok))
    print("%-4s %-9s %s" % (k, "bestanden" if ok else "FEHLER", text))


def summe(p):
    if not os.path.exists(p):
        return None
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


VOR = {"prod": summe(db.DB_PATH), "ablage": summe(ML.ABLAGE)}
T = tempfile.mkdtemp(prefix="o54_")
HEUTE = date.today()

# ══ M1 R-R11 ══════════════════════════════════════════════════════════════════════════════════════════════════════════════════
roh = ML.hole_alle(KEY, HEUTE)
idx = pd.date_range(min(r.index.min() for r in roh.values()).normalize(), pd.Timestamp(HEUTE), freq="D")
S_mod = ML.scores(roh, idx)
with redirect_stdout(io.TextIOWrapper(io.BytesIO(), encoding="utf-8")):
    import p51_vorpruefung as V
verzug_falsch = []


def fred_gestellt(s, verzug):
    if verzug != ML.REIHEN[s]:
        verzug_falsch.append((s, verzug, ML.REIHEN[s]))
    return roh[s].rename(s)                     # fredgraph.csv benennt die Spalte nach der Reihe


V.fred, V.IDX = fred_gestellt, idx
S_p51 = V.scores()
abw = []
for k in S_p51:
    a, b = S_p51[k].reindex(idx), S_mod[k].reindex(idx)
    gleich = ((a == b) | (a.isna() & b.isna())).all()
    if not gleich:
        abw.append(k)
pruefe("M1", not abw and not verzug_falsch and set(S_p51) == set(S_mod),
       "%d Score-Reihen x %d Tage (%s bis %s) · abweichend %s · Verzug falsch %s" % (
           len(S_p51), len(idx), idx[0].date(), idx[-1].date(), abw or "keine", verzug_falsch or "keiner"))

# ══ M2 Auskunft gegen §51.7 ═══════════════════════════════════════════════════════════════════════════════════════════════════
with open(os.path.join("data", "_spot", "p51_bank_n2.pkl"), "rb") as f:
    B = pickle.load(f)
st = pd.DatetimeIndex(B["stich"])
ab = idx[0] + pd.Timedelta(days=2 * ML.FENSTER + 800)          # beide 5-J-Fenster voll (Kanal und Gesamt)
sel = (st >= ab) & (st <= idx[-1])
m2 = []
for name in ("Gesamt lang", "Gesamt kurz"):
    e = B["echt"][B["namen"].index(name)][sel]
    m = S_mod[name].reindex(st[sel]).values
    ok = np.isfinite(e) & np.isfinite(m)
    m2.append("%s %d von %d gleich" % (name, int((e[ok] == m[ok]).sum()), int(ok.sum())))
# dazu die GANZE Historie: Rohreihen ab 2003 ueber denselben Abruf, Scores mit dem Modul, gegen alle Stichtage der Messung ab 2011-04
roh03 = {sid: ML.hole_reihe(sid, KEY, "2003-01-01") for sid in ML.REIHEN}
idx03 = pd.date_range("2003-01-01", pd.Timestamp(HEUTE), freq="D")
S03 = ML.scores(roh03, idx03)
sel03 = (st >= pd.Timestamp("2011-04-01")) & (st <= idx03[-1])
quote = []
for name in ("Gesamt lang", "Gesamt kurz"):
    e = B["echt"][B["namen"].index(name)][sel03]
    m = S03[name].reindex(st[sel03]).values
    ok = np.isfinite(e) & np.isfinite(m)
    quote.append((name, int((e[ok] == m[ok]).sum()), int(ok.sum())))
m2.append("ganze Historie ab 2011-04: " + " · ".join("%s %d von %d" % q for q in quote))
pruefe("M2", all(g >= 0.95 * n for _, g, n in quote) and all(x.split()[-4] == x.split()[-2] for x in m2[:2]),             # "Gesamt lang 10 von 10 gleich"
       "FRED-API gegen fredgraph.csv vom 14.10. (Unterschied nur durch Datenrevisionen erwartet; Soll >= 95 %%) - ab %s: %s" % (
           ab.date(), " · ".join(m2)))

# ══ M3 lage_aus ═══════════════════════════════════════════════════════════════════════════════════════════════════════════════
d = ML.lage_aus(roh, HEUTE)
letzt = lambda k: (None if pd.isna(S_p51[k].iloc[-1]) else float(S_p51[k].iloc[-1]))   # noqa: E731
tr_soll = [ML.NAME[n] for n in ML.NAME if letzt(n + " kurz") is not None and d["gesamt_kurz"] not in (None, 0.0)
           and letzt(n + " kurz") == d["gesamt_kurz"]]
pruefe("M3", d["gesamt_lang"] == letzt("Gesamt lang") and d["gesamt_kurz"] == letzt("Gesamt kurz") and ML.treiber(d) == tr_soll,
       "heute lang %s kurz %s (p51: %s / %s) · Treiber %s" % (d["gesamt_lang"], d["gesamt_kurz"], letzt("Gesamt lang"),
                                                              letzt("Gesamt kurz"), ML.treiber(d)))

# ══ M4 drei Zustaende ═════════════════════════════════════════════════════════════════════════════════════════════════════════
alt = dict(d, stand=(HEUTE - timedelta(days=ML.VERALTET_TAGE + 1)).isoformat())
mitf = dict(d, fehler="HTTPError: 502 (heute)")
z_f, z_v, z_ok, z_e = ML.zeile({}), ML.zeile(alt), ML.zeile(d), ML.zeile(mitf)
pruefe("M4", ML.zustand(None) == "fehlt" and ML.zustand(alt) == "veraltet" and ML.zustand(d) == "ok"
       and "NICHT VERFÜGBAR" in z_f and "VERALTET" in z_v and "VERALTET" not in z_ok and "letzter Abruf gescheitert" in z_e
       and "ATR" in z_ok and ML.stand(alt)["zustand"] == "veraltet",
       "fehlt / veraltet / ok / Fehlervermerk: %s / %s / %s / %s" % (
           "NICHT VERFÜGBAR" in z_f, "VERALTET" in z_v, ML.zustand(d), "gescheitert" in z_e))


# ══ M5 lauf mit kaputtem Abruf ════════════════════════════════════════════════════════════════════════════════════════════════
class Kaputt:
    def get(self, *a, **k):
        raise ConnectionError("gestellt: kein Netz, api_key=%s" % KEY)


z5 = os.path.join(T, "m.json")
ML._schreibe(z5, d)
r5 = ML.lauf(z5, KEY, HEUTE, http=Kaputt(), pause=0)
z5b = os.path.join(T, "leer.json")
r5b = ML.lauf(z5b, KEY, HEUTE, http=Kaputt(), pause=0)
pruefe("M5", r5["gesamt_kurz"] == d["gesamt_kurz"] and r5["fehler"] and KEY not in r5["fehler"] and ML.lade(z5)["fehler"]
       and ML.zustand(ML.lade(z5b)) == "fehlt" and "NICHT VERFÜGBAR" in ML.zeile(ML.lade(z5b)),
       "alter Stand bleibt %s · Vermerk '%s' · Schluessel verborgen %s · ohne alten Stand: %s" % (
           r5["gesamt_kurz"] == d["gesamt_kurz"], (r5["fehler"] or "")[:60], KEY not in (r5["fehler"] or ""), ML.zustand(ML.lade(z5b))))

# ══ M6 Mails ══════════════════════════════════════════════════════════════════════════════════════════════════════════════════
_fl = lambda x: " ".join(x.split())  # noqa: E731
mt = ML.mailteil(d)
_rf = dict(symbol="TAO", bitpanda="TAO", signalstunde="2026-10-14 10:00", einstieg="2026-10-14 11:00", ausstieg="2026-10-15 11:00",
           kurs=300.0, kurs_markt="spot", p2=0.001, p3=0.007, p5=0.107, vh=0.0411, kurs_eur=260.0)
_g = G.rechne(3, 0, G.lade())
_j = datetime(2026, 10, 14, 11, 9, tzinfo=timezone.utc)
s_mit = RM.signal_mail(_rf, 3, False, _g, {}, _j, None, None, None, None, None, mt)[1]
s_ohne = RM.signal_mail(_rf, 3, False, _g, {}, _j)[1]
h_mit = RM.signal_html(_rf, 3, False, _g, {}, _j, None, None, 0, None, None, None, mt)
vorn, tech = s_mit.split("5  TECHNIK")
ok_r = _fl(mt["ein"]) in _fl(vorn) and "O54" in tech and _fl(mt["ein"])[:40] in _fl(h_mit) and "Makro" not in s_ohne

import agent.regel0_ablage as AB  # noqa: E402


def _post(dd, makro):
    st_ = "2026-10-14 11:00"
    c = AB.oeffne(dd)
    w = {"symbol": "TAO", "signalstunde": st_, "einstieg": st_, "ausstieg": "2026-10-15 11:00", "vh": 0.042, "stufe_vorlaeufig": 3,
         "stufe": 3, "p2": 0.001, "p3": 0.007, "p5": 0.1, "hebel_schalter": 1, "bitpanda": "TAO", "zusatz": 0, "btc": 0,
         "version": "REGEL0.1", "erfasst_am": st_, "kurs": 1.0, "kurs_markt": "spot"}
    c.execute("INSERT OR REPLACE INTO signal (%s) VALUES (%s)" % (",".join(w), ",".join("?" * len(w))), list(w.values()))
    c.commit()
    c.close()
    post = []
    RM.versende(dd, lambda b, t, *a, **k: post.append(t) or True, jetzt=datetime(2026, 10, 14, 12, 10, tzinfo=timezone.utc),
                kurse=lambda: ({"TAO": 1.0}, {"TAOUSDT": 1.0}, {"TAO": 0.9}), makro=makro)
    return [t for t in post if "HEBEL-SIGNAL" in t]


def _kaputt(r):
    raise RuntimeError("Makro-Lieferant gestellt kaputt")


d1, d2 = os.path.join(T, "a"), os.path.join(T, "b")
os.makedirs(d1)
os.makedirs(d2)
p_k, p_g = _post(d1, _kaputt), _post(d2, lambda r: ML.mailteil(d))
ok_v = len(p_k) == 1 and len(p_g) == 1 and _fl(mt["ein"])[:40] in _fl(p_g[0])
zl = ML.zeile(d)
f1 = {"symbol": "TAO", "ausloese_kurs": 900.0, "startkurs_usd": 300.0, "menge": 2.0, "ende": "2027-01-01", "start": "2026-01-01",
      "ausloese_tag": "2026-09-01"}
f3 = {"symbol": "TAO", "kuerzel": "TAO", "utc": "2026-09-01 08:00:00", "alter_h": 1.5, "menge": 2.0, "id": 1, "titel": "Test"}
f4 = {"stichtag": "2026-10-01", "art": "erstliste", "liste": [("TAO", "TAO", "M", 0.8, 300, 900, 0.1, 1, None, 2.0)]}
b1, b1o = SM.mail(f1, 1.5, False, None, None, zl)[1], SM.mail(f1, 1.5, False, None)[1]
b3, b3o = SU.mail(f3, False, None, 1.0, 1.0, None, zl)[1], SU.mail(f3, False, None, 1.0, 1.0)[1]
b4, b4o = SA.mail(f4, {"TAO": 100.0}, set(), None, zl)[1], SA.mail(f4, {"TAO": 100.0}, set())[1]
ok_s = all(_fl(zl) in _fl(x) for x in (b1, b3, b4)) and all("Makro" not in x for x in (b1o, b3o, b4o)) \
    and b1o == SM.mail(f1, 1.5, False, None, None, None)[1] and b4o == SA.mail(f4, {"TAO": 100.0}, set(), None, None)[1]
pruefe("M6", ok_r and ok_v and ok_s, "REGEL0 Einschaetzung/Technik/HTML/ohne %s · Versand kaputt -> Mail geht %s, gut -> Zeile %s · "
       "B1/B3/B4 mit Zeile und ohne bitgleich %s" % (ok_r, len(p_k) == 1, len(p_g) == 1 and _fl(mt["ein"])[:40] in _fl(p_g[0]), ok_s))

# ══ M7 Statusseite ════════════════════════════════════════════════════════════════════════════════════════════════════════════
qs = open("remote/server.py", encoding="utf-8").read()
import remote.status as RS  # noqa: E402

ML.ABLAGE, _alt_ab = z5, ML.ABLAGE
try:
    g = RS._get_makro_lage.__wrapped__() if hasattr(RS._get_makro_lage, "__wrapped__") else RS._get_makro_lage()
finally:
    ML.ABLAGE = _alt_ab
pruefe("M7", 0 < qs.index('id="makro-kopf"') < qs.index('section-header section-system') and "data.makro_lage" in qs
       and g.get("kurz") == ML._wort(d["gesamt_kurz"]) and "makro_lage" in open("remote/status.py", encoding="utf-8").read(),
       "Makro-Abschnitt vor Betrieb & Lage %s · Getter: %s / %s · Render liest data.makro_lage %s" % (
           qs.index('id="makro-kopf"') < qs.index('section-header section-system'), g.get("lang"), g.get("kurz"), "data.makro_lage" in qs))

# ══ M8 Job und unveraendert ═══════════════════════════════════════════════════════════════════════════════════════════════════
qb = open("scheduler/background.py", encoding="utf-8").read()
job = qb[qb.index("def externe_reihen_job"):qb.index("def ", qb.index("def externe_reihen_job") + 10)]
NACH = {"prod": summe(db.DB_PATH), "ablage": summe(ML.ABLAGE)}
pruefe("M8", "_ML.lauf()" in job and "Makro-Lage nicht berechnet" in job and NACH == VOR,
       "Job ruft lauf() und faengt %s · Desktop-Prod unveraendert %s · echte Ablage unveraendert %s" % (
           "Makro-Lage nicht berechnet" in job, NACH["prod"] == VOR["prod"], NACH["ablage"] == VOR["ablage"]))

print("\nMuster Zeile (heute): " + zl)
wegwerf.aufraeumen(T)
print("\n%d von %d bestanden" % (sum(ERG), len(ERG)))
