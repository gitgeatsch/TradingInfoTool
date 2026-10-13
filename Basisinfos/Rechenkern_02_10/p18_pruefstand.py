"""P18 Spot B4 Abbau-Reihenfolge (13.10.2026, Spot §48) - Pruefstand am SEITENEFFEKT, NB-Lage nachgestellt. Nur Wegwerf-Dateien.

    python Basisinfos/Rechenkern_02_10/p18_pruefstand.py <Prod-Sicherung tradinginfotool.db>

NB-Lage: Betriebskopie = Messbasis je Reihe auf die letzten 500 T gekuerzt (wie lade_messreihen.kuerze), ohne die 10 Uebernahmen
(nicht Binance); Umlauf CoinGecko erst ab 25.07.2026 (am NB gibt es keine lange Reihe); Binance-Abruf gestellt (die ganze Reihe aus der
Messbasis); Produktion = Wegwerf-Kopie der Sicherung. Bezug = Nachbau p18_voranalyse.B4 auf der VOLLEN Messbasis mit derselben
Umlaufregel - unabhaengiger Rechenweg (volle Geschichte statt Stammsatz + Fenster).

  S1  01.08.2026 Erstlauf: das ganze Universum - jedes Fuenftel wie der Bezug, dieselbe Menge
  S2  Erstliste: art erstliste, neu = unten; Job mit Schalter AUS -> keine Mail, Lauf fertig
  S3  zweiter Lauf am selben Stichtag -> 'schon', nichts neu gerechnet; Schalter AN -> genau EINE Mail (Erstliste, Beleg, je Coin), dann keine
  S4  01.09.2026: Stammsatz FORTGESCHRIEBEN (keine neue Binance-Abfrage fuer bekannte Reihen), Universum wie der Bezug
  S5  01.09.: art neu, neu = unten am 01.09. ohne die schon unten am 01.08.; Mail 'neu'
  S6  wartet: am 3. fehlt einer Produktionsreihe der Schluss von t -> 'wartet'; am 5. gerechnet, der Coin 'ohne Kurs am Stichtag'
  S7  Zuordnung D5: Produktionskurs von KAIA x 1,5 -> 'Zuordnung unsicher', nicht eingeordnet
  S8  Binance-Abruf scheitert fuer einen Coin -> Protokoll 'Stammsatz nicht abrufbar', bis zum 4. 'wartet', am 5. gerechnet, kein Abbruch
  S9  stand() und letzte_fuenftel() fuer Statusseite, Teilexport, Bestand-Tab
  S10 Wegwerf-Produktion und Betriebskopie unveraendert (Pruefsumme)
"""
import hashlib
import os
import shutil
import sqlite3
import sys
import tempfile
from datetime import date

PROD_Q = os.path.abspath(sys.argv[1])
WURZEL = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, WURZEL)
sys.path.insert(0, os.path.join(WURZEL, "Basisinfos", "Spot_Voranalyse_04_10"))
os.chdir(WURZEL)
sys.argv = ["x", PROD_Q]
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

import p18_voranalyse as P  # noqa: E402
import agent.regel0_groesse as G  # noqa: E402
import agent.spot_abbau as SA  # noqa: E402
import config as C  # noqa: E402
import scheduler.background as BG  # noqa: E402

ERG = []


def pruefe(k, ok, text):
    ERG.append(bool(ok))
    print("%-4s %-9s %s" % (k, "bestanden" if ok else "FEHLER", text))


def summe(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


MK = P.MK
K, U = P.G["K"], P.G["U"]
UMLAUF_AB = pd.Timestamp("2026-07-25")
T = tempfile.mkdtemp(prefix="p18_")


def baue_ordner(name, prod_aendern=None):
    o = os.path.join(T, name)
    os.makedirs(o)
    # Betriebskopie
    q = sqlite3.connect("file:data/messdaten.db?mode=ro", uri=True)
    z = sqlite3.connect(os.path.join(o, SA.KOPIE))
    z.execute("CREATE TABLE price_history_ohlc (symbol TEXT, assetklasse TEXT, currency TEXT, date TEXT, open REAL, high REAL, low REAL, close REAL, "
              "volume REAL, fetched_at TEXT, quelle TEXT, PRIMARY KEY (symbol, currency, date))")
    for s, letzt in q.execute("SELECT symbol, MAX(date) FROM price_history_ohlc WHERE assetklasse='krypto' AND currency='USD' GROUP BY symbol").fetchall():
        if s in P.UEBERNOMMEN:
            continue
        ab = (pd.Timestamp(letzt) - pd.Timedelta(days=499)).date().isoformat()
        z.executemany("INSERT INTO price_history_ohlc VALUES (?,?,?,?,?,?,?,?,?,?,?)", q.execute(
            "SELECT symbol, assetklasse, currency, date, open, high, low, close, volume, fetched_at, quelle FROM price_history_ohlc "
            "WHERE symbol=? AND assetklasse='krypto' AND currency='USD' AND date >= ?", (s, ab)).fetchall())
    z.execute("CREATE TABLE _nur_betrieb (x)")
    z.commit()
    z.close()
    q.close()
    # Umlauf ab 25.07.2026
    q = sqlite3.connect("file:data/umlaufmenge_cg.db?mode=ro", uri=True)
    z = sqlite3.connect(os.path.join(o, SA.UMLAUF))
    z.execute("CREATE TABLE umlaufmenge (symbol TEXT, datum TEXT, wert REAL)")
    z.executemany("INSERT INTO umlaufmenge VALUES (?,?,?)", q.execute("SELECT symbol, datum, wert FROM umlaufmenge WHERE datum >= ?",
                                                                     (UMLAUF_AB.date().isoformat(),)).fetchall())
    z.commit()
    z.close()
    q.close()
    prod = os.path.join(o, "prod.db")
    shutil.copy(PROD_Q, prod)
    if prod_aendern:
        c = sqlite3.connect(prod)
        prod_aendern(c)
        c.commit()
        c.close()
    return o, prod


def http_messbasis(fehler=()):
    q = sqlite3.connect("file:data/messdaten.db?mode=ro", uri=True)
    zaehl = {"n": 0}

    def h(sym):
        zaehl["n"] += 1
        if sym in fehler:
            raise ConnectionError("Binance gestellt nicht erreichbar")
        return [(d[:10], c) for d, c in q.execute("SELECT date, close FROM price_history_ohlc WHERE symbol=? AND assetklasse='krypto' AND currency='USD' ORDER BY date", (sym,))]
    return h, zaehl


# ---- Bezug: Nachbau auf der vollen Messbasis, NB-Universum, Umlauf CoinGecko ab 25.07. mit Ersatz am Stichtag
cpq = sqlite3.connect("file:%s?mode=ro" % PROD_Q.replace("\\", "/"), uri=True)
wl = {a.symbol: a for a in C.get_watchlist()}
WL = C.get_watchlist()
kreis = SA.SM.kreis(cpq, WL)
zu = SA._zuordnung()
# ⚠️ KORREKTUR 13.10. (erster Lauf S1/S2/S4 rot - Fehler im BEZUG, nicht im Modul): die 10 Uebernahmen der Messbasis sind KEINE
# Binance-Reihen; der Bezug hatte sie als 'live' gezaehlt und damit ihre Produktionsreihen weggelassen
live = {s for s in K.columns if s not in P.UEBERNOMMEN and K[s].loc["2026-07-01":].notna().any()}
draussen = sorted(s for s in kreis if zu.get(s, (s, 1))[0] not in live)
alle_prod = {s: SA._prod_reihe(cpq, s) for s in draussen}


def bezug_basis(t):
    """⚠️ KORREKTUR 13.10. (S4 rot - Fehler im BEZUG): die 400-Kerzen-Grenze gilt JE STICHTAG (HYPE: 386 T am 01.08., 417 T am 01.09.),
    wie im Modul - nicht einmal fuer den 01.08."""
    pk = {s: pr for s, pr in alle_prod.items() if len(pr[pr.index <= t]) >= SA.MIN_KERZEN}
    Kb = K.drop(columns=[x for x in P.UEBERNOMMEN if x in K.columns]).copy()
    Ub = U.drop(columns=[x for x in P.UEBERNOMMEN if x in U.columns]).copy()
    for s, pr in pk.items():
        Kb[s] = pr.close.reindex(Kb.index)
        Ub[s] = pr.umsatz.reindex(Kb.index)
    aus = (set(P.G["SONDER"]) | {s for s in K.columns if s not in P.G["UNIV"]}) - set(pk)
    aus |= {s for s in pk if float(pk[s].close.asfreq("D").pct_change(fill_method=None).abs().median()) < SA.STABIL}
    return Kb, Ub, aus, pk


def umlauf_bezug(t):
    def u(s, m):
        r = MK.CGH.get(s)
        if r is None:
            return np.nan
        r = r[UMLAUF_AB:]
        h = MK._asof(r, m) if len(r) else None
        if h is None and len(r):
            h = MK._asof(r, t)
        return h if h is not None else np.nan
    return u


def bezug(t):
    Kb, Ub, aus, _ = bezug_basis(t)
    return P.B4(Kb, Ub, aus, umlauf_bezug(t)).fuenftel(t)


def vergleiche(k, t, tab, extra=""):
    ref = bezug(t)
    a = dict(zip(ref.sym, ref.q))
    b = dict(zip(tab.sym, tab.q))
    gem = set(a) | set(b)
    gl = sum((a.get(s) == b.get(s)) or (a.get(s) != a.get(s) and b.get(s) != b.get(s)) for s in gem)
    pruefe(k, gl == len(gem) and set(a) == set(b), "%s Modul gegen Bezug: %d von %d Coins gleiches Fuenftel · Mengen %s%s" % (
        t.date(), gl, len(gem), "gleich" if set(a) == set(b) else "VERSCHIEDEN (nur Bezug %s, nur Modul %s)" % (
            sorted(set(a) - set(b))[:6], sorted(set(b) - set(a))[:6]), extra))
    return ref


# ======================================================================================================================
O, PROD = baue_ordner("A")
vor_prod, vor_kopie = summe(PROD), summe(os.path.join(O, SA.KOPIE))
http, zaehl = http_messbasis()
POST = []
SCHALTER = {"an": False}
G.spot_abbau_aktiv = lambda werte=None: SCHALTER["an"]
cf = lambda: sqlite3.connect("file:%s?mode=ro" % PROD.replace("\\", "/"), uri=True)   # noqa: E731
cp = cf()

# S1 / S2
import logging  # noqa: E402
logging.basicConfig(level=logging.ERROR)
e1 = SA.lauf(cp, O, WL, date(2026, 8, 20), http, mit_tabelle=True)
if "_tabelle" not in e1:
    print("ABBRUCH S1: %s" % {k: v for k, v in e1.items() if k != "_tabelle"})
    sys.exit(1)
ref1 = vergleiche("S1", pd.Timestamp("2026-08-01"), e1["_tabelle"], " · Stammsaetze von Binance %d" % e1["geholt"])
_pk1 = bezug_basis(pd.Timestamp("2026-08-01"))[3]
unten_ref = sorted(s for s, b in ((s, zu.get(s, (s, 1))[0] if s not in _pk1 else s) for s in kreis)
                   if b in set(ref1.sym[ref1.q == 1]))
pruefe("S2", e1["art"] == "erstliste" and sorted(e1["neu"]) == sorted(e1["unten"]) == unten_ref,
       "Erstliste 01.08.: unten %s (Bezug %s)" % (e1["unten"], unten_ref))
j = BG.spot_abbau_job(cf, lambda: WL, versand=lambda b, t, bi=None: POST.append((b, t)) or True, heute=date(2026, 8, 20), ordner=O, http=http)
pruefe("S2b", j["status"] == "schon" and not POST and j["schalter"] is False, "Job Schalter aus: Status %s, Mails %d" % (j["status"], len(POST)))
# S3
SCHALTER["an"] = True
n_vor = zaehl["n"]
j = BG.spot_abbau_job(cf, lambda: WL, versand=lambda b, t, bi=None: POST.append((b, t)) or True, heute=date(2026, 8, 21), ordner=O, http=http)
j2 = BG.spot_abbau_job(cf, lambda: WL, versand=lambda b, t, bi=None: POST.append((b, t)) or True, heute=date(2026, 8, 22), ordner=O, http=http)
m1 = POST[0] if POST else ("", "")
pruefe("S3", len(POST) == 1 and zaehl["n"] == n_vor and "Erstliste" in m1[1] and "zuerst" in m1[0] and "12,5 Prozentpunkte" in m1[1]
       and all(s in m1[0] for s in e1["unten"]) and "nicht nach Güte" in m1[1] and j2["gemailt"] is False,
       "Schalter an: Mails %d · Betreff %s · Binance-Abrufe neu %d" % (len(POST), m1[0], zaehl["n"] - n_vor))
# S4 / S5
n_vor = zaehl["n"]
e2 = SA.lauf(cp, O, WL, date(2026, 9, 20), http, mit_tabelle=True)
ref2 = vergleiche("S4", pd.Timestamp("2026-09-01"), e2["_tabelle"], " · neue Binance-Abrufe %d (Stammsatz fortgeschrieben)" % (zaehl["n"] - n_vor))
q2 = sqlite3.connect(os.path.join(O, SA.ABLAGE))
fort = q2.execute("SELECT COUNT(*) FROM abbau_stamm WHERE quelle='fortgeschrieben'").fetchone()[0]
pruefe("S4b", fort > 100 and zaehl["n"] - n_vor <= 5, "Stammsaetze fortgeschrieben %d · neue Abrufe %d" % (fort, zaehl["n"] - n_vor))
erwartet_neu = sorted(set(e2["unten"]) - set(e1["unten"]))
POST.clear()
j = BG.spot_abbau_job(cf, lambda: WL, versand=lambda b, t, bi=None: POST.append((b, t)) or True, heute=date(2026, 9, 21), ordner=O, http=http)
pruefe("S5", e2["art"] == "neu" and sorted(e2["neu"]) == erwartet_neu and (len(POST) == (1 if erwartet_neu else 0))
       and (not POST or "Neu im unteren Fünftel" in POST[0][1]),
       "01.09.: unten %s · neu %s (erwartet %s) · Mails %d" % (e2["unten"], e2["neu"], erwartet_neu, len(POST)))
# S9
st = SA.stand(O)
lf = SA.letzte_fuenftel(O)
pruefe("S9", st["laeufe"] == 2 and st["letzter"][0] == "2026-09-01" and st["stamm"] > 100 and set(lf) == set(kreis)
       and all(lf[s][0] == "2026-09-01" for s in lf), "stand: Laeufe %s, letzter %s, Stammsaetze %s · letzte_fuenftel %d Coins" % (
           st["laeufe"], st["letzter"][:3], st["stamm"], len(lf)))
q2.close()
cp.close()
# S10
pruefe("S10", summe(PROD) == vor_prod and summe(os.path.join(O, SA.KOPIE)) == vor_kopie, "Wegwerf-Produktion und Betriebskopie unveraendert")

# ======================================================================================================================
# S6 / S7 in einem zweiten Ordner: XDC ohne Schluss am 01.09., KAIA-Kurs x 1,5


def aendern(c):
    c.execute("DELETE FROM price_history_ohlc WHERE symbol='XDC' AND date LIKE '2026-09-01%'")
    c.execute("UPDATE price_history_ohlc SET close = close * 1.5 WHERE symbol='KAIA'")


O2, PROD2 = baue_ordner("B", aendern)
http2, _ = http_messbasis()
c2 = sqlite3.connect("file:%s?mode=ro" % PROD2.replace("\\", "/"), uri=True)
w = SA.lauf(c2, O2, WL, date(2026, 9, 3), http2)
e3 = SA.lauf(c2, O2, WL, date(2026, 9, 5), http2)
g = {r[0]: r[1] for r in sqlite3.connect(os.path.join(O2, SA.ABLAGE)).execute("SELECT symbol, grund FROM abbau_fuenftel WHERE stichtag='2026-09-01'")}
pruefe("S6", w["status"] == "wartet" and "XDC" in w["fehlend"] and e3["status"] == "fertig" and "XDC" in e3["fehlend"]
       and "ohne Kurs" in (g.get("XDC") or ""), "am 3.: %s (fehlend %s) · am 5.: %s · XDC: %s" % (w["status"], w["fehlend"], e3["status"], g.get("XDC")))
pruefe("S7", "Zuordnung unsicher" in (g.get("KAIA") or ""), "KAIA: %s" % g.get("KAIA"))
c2.close()
# S8 in einem dritten Ordner ohne andere Stoerung: der Binance-Abruf fuer SUI scheitert
O3, PROD3 = baue_ordner("C")
http3, _ = http_messbasis(fehler=("SUI",))
c3 = sqlite3.connect("file:%s?mode=ro" % PROD3.replace("\\", "/"), uri=True)
w4 = SA.lauf(c3, O3, WL, date(2026, 9, 4), http3)
e5 = SA.lauf(c3, O3, WL, date(2026, 9, 5), http3)
g3 = {r[0]: r[1] for r in sqlite3.connect(os.path.join(O3, SA.ABLAGE)).execute("SELECT symbol, grund FROM abbau_fuenftel WHERE stichtag='2026-09-01'")}
pr = [r for r in sqlite3.connect(os.path.join(O3, SA.ABLAGE)).execute("SELECT symbol, text FROM protokoll WHERE art='abbau stamm'")]
pruefe("S8", w4["status"] == "wartet" and "Stammsatz SUI" in w4["fehlend"] and e5["status"] == "fertig" and g3.get("SUI") is not None
       and any(r[0] == "SUI" and "nicht abrufbar" in r[1] for r in pr),
       "am 4.: %s (%s) · am 5.: %s · Protokoll %s · SUI: %s" % (w4["status"], w4["fehlend"], e5["status"], pr[:1], g3.get("SUI")))
c3.close()
print("\nMuster der Mail (S3):\n" + m1[1])
cpq.close()
shutil.rmtree(T, ignore_errors=True)
print("\n%d von %d bestanden" % (sum(ERG), len(ERG)))
