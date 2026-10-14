"""P22 Verwaesserung als Fakt in Mail und Statusseite (15.10.2026, Spot §54) - Pruefstand am SEITENEFFEKT, nur Wegwerf-Dateien (D:).

    python Basisinfos/Rechenkern_02_10/p22_pruefstand.py <Prod-Sicherung tradinginfotool.db | .db.gz>

NB-Lage wie p18: Betriebskopie = Messbasis je Reihe auf 500 T gekuerzt; Umlauf = volle Desktop-Reihe (Lage NACH der USB-Ergaenzung) bzw.
nur ab 08.09.2026 (Lage OHNE Ergaenzung); Binance-Abruf gestellt aus der Messbasis; Produktion = Wegwerf-Kopie der Sicherung.

  V1  B4 BITGLEICH: dieselbe Rechnung mit P22 und mit einer Verwaesserung, die SCHEITERT -> abbau_fuenftel/abbau_lauf gleich, Fehler
      im Protokoll, B4 'fertig' (P22 kann B4 nicht aufhalten)
  V2  verw_universum = das B4-Universum (dieselbe Menge, dieselben Klassen wie mit_tabelle); Wert und Fuenftel UNABHAENGIG nachgerechnet
      (eigene Lesegrenze, eigener Rang) - alle gleich
  V3  B4-Mail: je Coin eine Verwaesserungszeile + der Messlage-Satz; ohne ``verw`` ist der Text bitgleich zur alten Fassung
  V4  B1- und B3-Mail: mit ``verw_text`` die Zeile + Messlage, ohne bitgleich
  V5  REGEL0-Signalmail ("beim Kauf"): Zeile in der Einschaetzung und in der Technik, Text und HTML; ohne bitgleich; ein scheiternder
      Lieferant haelt die Mail nicht auf (versende)
  V6  fakt(): Wert heute = unabhaengig nachgerechnet, Fuenftel aus den Stichtagsgrenzen; Coin ohne Reihe -> "keine Mengenreihe";
      NB-Lage ohne Ergaenzung -> "noch keine 90 Tage"
  V7  stand(): Bestandscoins im staerksten Fuenftel = unabhaengig gezaehlt
  V8  Diagnose (Nebenfund §54.4): die Mengendatei mit ihrer Marke ist LESBAR (Form betriebskopie, Datenstand), messdaten-Marke weiter
  V9  Wegwerf-Produktion, Betriebskopie und Mengenreihe unveraendert (Pruefsumme)
"""
import gzip
import hashlib
import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile
from datetime import date, datetime, timezone

WURZEL = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(WURZEL)
sys.path.insert(0, WURZEL)
import wegwerf  # noqa: E402,F401  Wegwerf-Ordner auf D: und Aufraeumen ohne stilles Scheitern (15.10.2026)

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

import agent.regel0_groesse as G  # noqa: E402
import agent.regel0_mail as RM  # noqa: E402
import agent.spot_abbau as SA  # noqa: E402
import agent.spot_mitnahme as SM  # noqa: E402
import agent.spot_upbit as SU  # noqa: E402
import agent.verwaesserung as VW  # noqa: E402
import config as C  # noqa: E402

ERG = []
UEBERNOMMEN = ["AIOZ", "AKT", "BRETT", "CAT", "GRIFFAIN", "HYPE", "KAS", "MORPHO", "PLUME", "SUPRA"]   # wie p18 (keine Binance-Reihen)
HEUTE = date(2026, 9, 5)            # Stichtag 01.09.2026; am 5. wird gerechnet, auch wenn ein Produktionskurs fehlt
STICH = "2026-09-01"
NB_AB = "2026-09-08"


def pruefe(k, ok, text):
    ERG.append(bool(ok))
    print("%-4s %-9s %s" % (k, "bestanden" if ok else "FEHLER", text))


def summe(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


T = tempfile.mkdtemp(prefix="p22_")
QUELLE = sys.argv[1]
PROD_Q = os.path.join(T, "prod_quelle.db")
if QUELLE.endswith(".gz"):
    with gzip.open(QUELLE, "rb") as f, open(PROD_Q, "wb") as g:
        shutil.copyfileobj(f, g)
else:
    shutil.copy(QUELLE, PROD_Q)
KOPIE_Q = os.path.join(T, "kopie_quelle.db")
UML_Q = os.path.join(T, "umlauf_quelle.db")

# ---- Betriebskopie einmal bauen (500 T je Reihe), Mengenreihe einmal kopieren
q = sqlite3.connect("file:data/messdaten.db?mode=ro", uri=True)
z = sqlite3.connect(KOPIE_Q)
z.execute("CREATE TABLE price_history_ohlc (symbol TEXT, assetklasse TEXT, currency TEXT, date TEXT, open REAL, high REAL, low REAL, close REAL, "
          "volume REAL, fetched_at TEXT, quelle TEXT, PRIMARY KEY (symbol, currency, date))")
for s, letzt in q.execute("SELECT symbol, MAX(date) FROM price_history_ohlc WHERE assetklasse='krypto' AND currency='USD' GROUP BY symbol").fetchall():
    if s in UEBERNOMMEN:
        continue
    ab = (pd.Timestamp(letzt) - pd.Timedelta(days=499)).date().isoformat()
    z.executemany("INSERT INTO price_history_ohlc VALUES (?,?,?,?,?,?,?,?,?,?,?)", q.execute(
        "SELECT symbol, assetklasse, currency, date, open, high, low, close, volume, fetched_at, quelle FROM price_history_ohlc "
        "WHERE symbol=? AND assetklasse='krypto' AND currency='USD' AND date >= ?", (s, ab)).fetchall())
z.execute("CREATE TABLE _nur_betrieb (behalte_tage INTEGER, mindest_kerzen INTEGER, gebaut_am TEXT)")
z.execute("INSERT INTO _nur_betrieb VALUES (500, 400, '2026-10-15')")
z.commit()
z.close()
q.close()
shutil.copy("data/umlaufmenge_cg.db", UML_Q)


def baue_ordner(name, umlauf_ab=None):
    o = os.path.join(T, name)
    os.makedirs(o)
    shutil.copy(KOPIE_Q, os.path.join(o, SA.KOPIE))
    shutil.copy(UML_Q, os.path.join(o, SA.UMLAUF))
    if umlauf_ab:
        c = sqlite3.connect(os.path.join(o, SA.UMLAUF))
        c.execute("DELETE FROM umlaufmenge WHERE datum < ?", (umlauf_ab,))
        c.commit()
        c.close()
    shutil.copy(PROD_Q, os.path.join(o, "prod.db"))
    return o, os.path.join(o, "prod.db")


def http_messbasis():
    q = sqlite3.connect("file:data/messdaten.db?mode=ro", uri=True)

    def h(sym):
        return [(d[:10], c) for d, c in q.execute("SELECT date, close FROM price_history_ohlc WHERE symbol=? AND assetklasse='krypto' AND "
                                                  "currency='USD' ORDER BY date", (sym,))]
    return h


WL = C.get_watchlist()


def lauf(o, prod, mit_tabelle=False):
    cp = sqlite3.connect(prod)
    cp.row_factory = sqlite3.Row
    try:
        return SA.lauf(cp, o, WL, HEUTE, http_messbasis(), mit_tabelle=mit_tabelle)
    finally:
        cp.close()


def tabellen(o, *namen):
    c = sqlite3.connect("file:%s?mode=ro" % os.path.join(o, SA.ABLAGE).replace("\\", "/"), uri=True)
    try:
        return {n: sorted(tuple(r) for r in c.execute("SELECT * FROM %s" % n)) for n in namen}
    finally:
        c.close()


# ══ V1 B4 bitgleich ══════════════════════════════════════════════════════════════════════════════════════════════════════════
oA, pA = baue_ordner("A")
oB, pB = baue_ordner("B")
vorA = {k: summe(os.path.join(oA, f)) for k, f in (("prod", "prod.db"), ("kopie", SA.KOPIE), ("umlauf", SA.UMLAUF))}
eA = lauf(oA, pA, mit_tabelle=True)
_echt = VW.speichere


def _kaputt(*a, **k):
    raise RuntimeError("gestellter Fehler P22")


VW.speichere = _kaputt
eB = lauf(oB, pB)
VW.speichere = _echt
tA, tB = tabellen(oA, "abbau_fuenftel", "abbau_lauf"), tabellen(oB, "abbau_fuenftel", "abbau_lauf")
ohne_zeit = lambda rows: [r[:1] + r[2:] for r in rows]                       # noqa: E731  abbau_lauf: Spalte 'am' ist die Uhrzeit
cB = sqlite3.connect(os.path.join(oB, SA.ABLAGE))
prot_b = [r[0] for r in cB.execute("SELECT text FROM protokoll WHERE art='verwaesserung fehler'")]
hat_verw_b = cB.execute("SELECT name FROM sqlite_master WHERE name='verw_universum'").fetchone()
cB.close()
pruefe("V1", eA["status"] == "fertig" and eB["status"] == "fertig" and tA["abbau_fuenftel"] == tB["abbau_fuenftel"]
       and ohne_zeit(tA["abbau_lauf"]) == ohne_zeit(tB["abbau_lauf"]) and prot_b and eB.get("verw") is None,
       "Stichtag %s · Universum %s · unten %s · abbau_fuenftel gleich %s · abbau_lauf gleich %s · mit Fehler: B4 %s, Protokoll %s" % (
           eA["stichtag"], eA["universum"], ",".join(eA["unten"]), tA["abbau_fuenftel"] == tB["abbau_fuenftel"],
           ohne_zeit(tA["abbau_lauf"]) == ohne_zeit(tB["abbau_lauf"]), eB["status"], prot_b[:1]))

# ══ V2 Universum, Klassen, Wert und Fuenftel unabhaengig ═════════════════════════════════════════════════════════════════════
cA = sqlite3.connect(os.path.join(oA, SA.ABLAGE))
vu = pd.read_sql("SELECT * FROM verw_universum WHERE stichtag=?", cA, params=(STICH,))
cA.close()
tab = eA["_tabelle"]
tab = tab[["sym", "kl"]]
gleiche_menge = set(vu.symbol) == set(tab.sym) and dict(zip(vu.symbol, vu.klasse)) == dict(zip(tab.sym, tab.kl))
uq = sqlite3.connect("file:%s?mode=ro" % UML_Q.replace("\\", "/"), uri=True)
roh = pd.read_sql("SELECT symbol, substr(datum,1,10) AS d, wert FROM umlaufmenge", uq)
uq.close()
roh["d"] = pd.to_datetime(roh.d)


def eigen_asof(s, t):
    x = roh[(roh.symbol == s) & (roh.d <= t)].sort_values("d")
    if not len(x) or (t - x.d.iloc[-1]).days > 7 or x.wert.iloc[-1] <= 0:
        return None
    return float(x.wert.iloc[-1])


t0 = pd.Timestamp(STICH)
eig = {}
for s in vu.symbol:
    a, b = eigen_asof(s, t0), eigen_asof(s, t0 - pd.Timedelta(days=90))
    eig[s] = np.log(a / b) if a and b else np.nan
vu["eig"] = vu.symbol.map(eig)
wert_gleich = bool(np.allclose(vu.verw90.astype(float).fillna(-99), vu.eig.fillna(-99), atol=1e-12))
q_eig = {}
for k, g in vu.groupby("klasse"):
    g = g[g.eig.notna()]
    if len(g) < 10:
        continue
    # KORREKTUR 15.10. (erster Lauf V2 rot - Fehler im BEZUG): Bindungen als MITTELRANG wie die Messung §53/§54 (viele Coins haben
    # exakt 0 % = feste Menge); der erste Bezug brach Bindungen willkuerlich. Eigener Mittelrang, ohne pandas.rank:
    v = g.eig.values
    for s, x in zip(g.symbol, v):
        r = (np.sum(v < x) + (np.sum(v == x) + 1) / 2.0) / len(v)
        q_eig[s] = int(min(5, max(1, np.ceil(r * 5))))
q_gleich = all((int(x) if x == x else None) == q_eig.get(s) for s, x in zip(vu.symbol, vu.fuenftel))
pruefe("V2", gleiche_menge and wert_gleich and q_gleich and vu.verw90.notna().sum() > 100,
       "Universum %d (mit Wert %d) · Menge und Klassen wie B4 %s · Wert unabhaengig %s · Fuenftel unabhaengig %s · je Klasse %s" % (
           len(vu), int(vu.verw90.notna().sum()), gleiche_menge, wert_gleich, q_gleich,
           " ".join("%s %d" % (k, int(n)) for k, n in vu[vu.fuenftel.notna()].groupby("klasse").size().items())))

# ══ V3 B4-Mail ═══════════════════════════════════════════════════════════════════════════════════════════════════════════════
fall = SA.faellig(oA, STICH)
werte = {r[0]: 1000.0 for r in fall["liste"]} if fall else {}
verw = SA.verw_am_stichtag(oA, STICH, fall["liste"]) if fall else {}
b1, t1 = SA.mail(fall, werte, set(), verw) if fall else ("", "")
b0, t0m = SA.mail(fall, werte, set()) if fall else ("", "")
mit_zeilen = sum(1 for z in t1.splitlines() if z.strip().startswith("Verwässerung 90 T"))
pruefe("V3", fall and mit_zeilen == len(fall["liste"]) and VW.MESSLAGE in t1 and "Verwässerung" not in t0m and t1.replace(
    "\n".join(z for z in t1.splitlines()), "") == "",
       "Erstliste %s · Zeilen %d von %d Coins · Messlage %s · ohne verw kein Wort 'Verwässerung' %s · Beispiel: %s" % (
           ",".join(r[0] for r in fall["liste"]) if fall else "-", mit_zeilen, len(fall["liste"]) if fall else 0, VW.MESSLAGE in t1,
           "Verwässerung" not in t0m, next((z.strip() for z in t1.splitlines() if z.strip().startswith("Verwässerung 90 T")), "-")))

# ══ V4 B1- und B3-Mail ═══════════════════════════════════════════════════════════════════════════════════════════════════════
f1 = {"symbol": "TAO", "ausloese_kurs": 900.0, "startkurs_usd": 300.0, "menge": 2.0, "ende": "2027-01-01", "start": "2026-01-01",
      "ausloese_tag": "2026-09-01"}
f3 = {"symbol": "TAO", "kuerzel": "TAO", "utc": "2026-09-01 08:00:00", "alter_h": 1.5, "menge": 2.0, "id": 1, "titel": "Test"}
vt = VW.fakt(oA, "TAO", date(2026, 9, 20))["text"]
m1, m1o = SM.mail(f1, 1.5, False, None, vt)[1], SM.mail(f1, 1.5, False, None)[1]
m3, m3o = SU.mail(f3, False, None, 1.0, 1.0, vt)[1], SU.mail(f3, False, None, 1.0, 1.0)[1]
pruefe("V4", vt in m1 and VW.MESSLAGE in m1 and "Verwässerung" not in m1o and vt in m3 and VW.MESSLAGE in m3 and "Verwässerung" not in m3o,
       "B1 mit %s / ohne %s · B3 mit %s / ohne %s · Zeile: %s" % (vt in m1, "Verwässerung" not in m1o, vt in m3, "Verwässerung" not in m3o, vt))

# ══ V5 REGEL0-Signalmail ═════════════════════════════════════════════════════════════════════════════════════════════════════
_rf = dict(symbol="TAO", bitpanda="TAO", signalstunde="2026-09-20 08:00", einstieg="2026-09-20 09:00", ausstieg="2026-09-21 09:00",
           kurs=300.0, kurs_markt="spot", p2=0.001, p3=0.007, p5=0.107, vh=0.0411, kurs_eur=260.0)
_g = G.rechne(3, 0, G.lade())
_j = datetime(2026, 9, 20, 9, 9, tzinfo=timezone.utc)
mt = VW.mailteil(oA, "TAO", date(2026, 9, 20))
s_mit = RM.signal_mail(_rf, 3, False, _g, {}, _j, None, None, None, mt)[1]
s_ohne = RM.signal_mail(_rf, 3, False, _g, {}, _j)[1]
h_mit = RM.signal_html(_rf, 3, False, _g, {}, _j, None, None, 0, None, mt)
_flach = lambda x: " ".join(x.split())                                       # noqa: E731  der Text bricht bei 96 Zeichen um
pruefe("V5", _flach(mt["ein"]) in _flach(s_mit.split("5  TECHNIK")[0]) and "Verwässerung" in s_mit.split("5  TECHNIK")[1] and "Verwässerung" not in s_ohne
       and "Verwässerung" in h_mit and s_ohne == RM.signal_mail(_rf, 3, False, _g, {}, _j, None, None, None, None)[1],
       "Text: Einschaetzung %s, Technik %s · HTML %s · ohne Zeile bitgleich %s" % (
           _flach(mt["ein"]) in _flach(s_mit.split("5  TECHNIK")[0]), "Verwässerung" in s_mit.split("5  TECHNIK")[1], "Verwässerung" in h_mit, "Verwässerung" not in s_ohne))

# ══ V6 fakt() ════════════════════════════════════════════════════════════════════════════════════════════════════════════════
th = pd.Timestamp("2026-09-20")
a, b = eigen_asof("TAO", th), eigen_asof("TAO", th - pd.Timedelta(days=90))
f_tao = VW.fakt(oA, "TAO", th.date())
cA = sqlite3.connect(os.path.join(oA, SA.ABLAGE))
kl_tao, = cA.execute("SELECT klasse FROM verw_universum WHERE stichtag=? AND symbol='TAO'", (STICH,)).fetchone()
gr = __import__("json").loads(cA.execute("SELECT grenzen FROM verw_grenzen WHERE stichtag=? AND klasse=?", (STICH, kl_tao)).fetchone()[0])
cA.close()
q_tao = 1 + sum(np.log(a / b) > x for x in gr)
f_hype = VW.fakt(oA, "HYPE", th.date())
oN, pN = baue_ordner("NB_ohne_ergaenzung", NB_AB)
f_nb = VW.fakt(oN, "TAO", date(2026, 10, 14))
pruefe("V6", abs(f_tao["heute"] - np.log(a / b)) < 1e-12 and f_tao["fuenftel"] == q_tao and "keine Mengenreihe" in f_hype["text"]
       and "noch keine 90 Tage" in f_nb["text"],
       "TAO heute %s (eigen %+.4f) Fuenftel %s (eigen %s) · HYPE: %s · NB ohne Ergaenzung: %s" % (
           f_tao["text"], np.log(a / b), f_tao["fuenftel"], q_tao, f_hype["text"], f_nb["text"]))

# ══ V7 stand() ═══════════════════════════════════════════════════════════════════════════════════════════════════════════════
st = SA.stand(oA)
cA = sqlite3.connect(os.path.join(oA, SA.ABLAGE))
eig7 = sorted(s for s, q5 in cA.execute("SELECT f.symbol, v.fuenftel FROM abbau_fuenftel f JOIN verw_universum v ON v.stichtag=f.stichtag "
                                        "AND v.symbol=f.reihe WHERE f.stichtag=?", (STICH,)) if q5 == 5)
cA.close()
pruefe("V7", sorted(r[0] for r in st.get("verw_staerkstes", [])) == eig7,
       "Statusseite: %s · eigen gezaehlt %s" % (st.get("verw_staerkstes"), eig7))

# ══ V8 Diagnose: Mengendatei mit ihrer Marke lesbar ══════════════════════════════════════════════════════════════════════════
D8 = os.path.join(T, "diag")
os.makedirs(os.path.join(D8, "data"))
shutil.copy("K:/My Drive/Claude_Austauschordner/umlaufmenge_cg.db" if os.path.exists("K:/My Drive/Claude_Austauschordner/umlaufmenge_cg.db")
            else UML_Q, os.path.join(D8, "data", "umlaufmenge_cg.db"))
shutil.copy(KOPIE_Q, os.path.join(D8, "data", "messdaten.db"))
code = ("import sys, json; sys.path.insert(0, %r); import extract_notebook_diagnose as E; "
        "print(json.dumps([ (z['groesse'], z.get('form'), z.get('grund'), z.get('behalte_tage'), z.get('juengste_daten')) "
        "for z in E._messbasen()['je_groesse'] ]))" % WURZEL)
r8 = subprocess.run([sys.executable, "-c", code], cwd=D8, capture_output=True, text=True, encoding="utf-8", errors="replace")
try:
    z8 = {x[0]: x for x in __import__("json").loads(r8.stdout.strip().splitlines()[-1])}
except Exception:                                                # noqa: BLE001
    z8 = {}
pruefe("V8", z8.get("turnover", [None, None])[1] == "betriebskopie" and z8["turnover"][4] and z8.get("schnitt", [None, None])[1] == "betriebskopie"
       and z8["schnitt"][3] == 500,
       "turnover %s · schnitt %s%s" % (z8.get("turnover"), z8.get("schnitt"), ("" if z8 else " · " + (r8.stderr or "")[-300:])))

# ══ V9 unveraendert ══════════════════════════════════════════════════════════════════════════════════════════════════════════
nachA = {k: summe(os.path.join(oA, f)) for k, f in (("prod", "prod.db"), ("kopie", SA.KOPIE), ("umlauf", SA.UMLAUF))}
pruefe("V9", nachA == vorA and summe("data/umlaufmenge_cg.db") == summe(UML_Q), "Wegwerf-Produktion, Betriebskopie, Mengenreihe unveraendert: %s" % (
    {k: nachA[k] == vorA[k] for k in vorA}))

print("\nMuster B4-Mail, Abschnitt 3 (V3):")
print("\n".join(z for z in t1.splitlines() if "Verwässerung" in z or z.startswith("  ") and ": Klasse" in z)[:1500])
print("\nMuster REGEL0, Einschaetzung (V5): " + next((z.strip() for z in s_mit.splitlines() if "Verwässerung" in z), "-"))
wegwerf.aufraeumen(T)
print("\n%d von %d bestanden" % (sum(ERG), len(ERG)))
