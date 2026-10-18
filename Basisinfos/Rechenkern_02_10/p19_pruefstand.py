"""P19 Spot C1 Season-Ampel (17.10.2026, Spot §49) - Pruefstand am SEITENEFFEKT, NB-Lage nachgestellt. Nur Wegwerf-Dateien.

    python Basisinfos/Rechenkern_02_10/p19_pruefstand.py <Prod-Sicherung tradinginfotool.db>

NB-Lage: Betriebskopie = Messbasis je Reihe auf die letzten 500 T gekuerzt (wie p18_pruefstand), ohne die 10 Uebernahmen; kein
B4-Stammsatz (Stablecoins dann ueber das Fenster der Kopie); Produktion = Wegwerf-Kopie der Sicherung (Fear & Greed). FRED und DefiLlama
EINMAL echt abgerufen (nur lesend) und als ``quellen`` gestellt - so sind alle Laeufe auf denselben Rohdaten. Bezug = die Kalibrierung
(data/_spot/am_kalibrierung.csv, §36.4) und der Nachbau ``p19_voranalyse`` (unabhaengig geschrieben, 14.10.).

  S1  Regel R-R11: stand/stufen des Moduls = p19_voranalyse = Kalibrierung (2.639 Tage); Haltezeit 7 T = 18 Wechsel (p19_gegenprobe G2)
  S2  NB-Lage: Lauf ok; B1/B2 bitgleich zur Kalibrierung auf den gemeinsamen Tagen; B3 nur in der Revisionsspanne (§49.5); Stufe roh
      gleich der Kalibrierung, wo die Breite dieselbe Seite von 0,6 hat; heute (20.09.) 'ungewohnt', 2 von 3
  S3  erster Lauf = Startmarke, keine Mail; zweiter Lauf: keine neue Meldung
  S4  Haltezeit: B3 fuer 5 Tage ueber 10 % -> Stufe roh wechselt, die GELTENDE nicht -> nichts faellig
  S5  B3 fuer 10 Tage ueber 10 % -> geltend Season-Klima/Ueberhitzung -> faellig; Job Schalter AUS: keine Mail, 'ohne_mail', danach nicht
      nachgeholt
  S6  Schalter AN (neue Ablage): genau EINE Mail mit Handlung, Bedingungen, Makro-Zeile; Versand scheitert -> bleibt faellig, naechster
      Lauf mailt einmal
  S7  Revision: B3 in der Vergangenheit geaendert -> revision_b3 > 0, KEIN Scheinwechsel
  S8  Fehler: ohne FRED-Schluessel -> status fehler, alter Stand bleibt, Zeile 'letzter Abruf gescheitert'
  S9  Mail-Zeilen B1/B3/B4: mit ampel_text die Zeile 'Season-Ampel ...', ohne sie unveraendert gegen den alten Aufruf
  S10 A3: Kandidaten aus _universum_ablegen + kandidaten auf dem Nachbau-Universum 01.09. = p19_voranalyse Teil 4 (69 / 67, H-Liste)
  S11 Anzeige: uebersicht, Statusseiten-Getter, Schalter, Teilexport-Abschnitt; Reiter Markt (Krypto) und Spot bauen ohne Fehler
  S12 kein Seiteneffekt: Wegwerf-Produktion, Betriebskopie, Desktop-data/spot_betrieb.db unveraendert
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
import wegwerf  # noqa: E402,F401  Wegwerf-Ordner auf D: und Aufraeumen ohne stilles Scheitern (15.10.2026)
os.chdir(WURZEL)
sys.argv = ["x", PROD_Q]
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

import config as C  # noqa: E402
C.load_env()
import p19_voranalyse as P  # noqa: E402
import agent.regel0_groesse as G  # noqa: E402
import agent.season_ampel as SA  # noqa: E402
import agent.spot_abbau as AB  # noqa: E402
import agent.spot_mitnahme as SM  # noqa: E402
import agent.spot_upbit as SU  # noqa: E402
import scheduler.background as BG  # noqa: E402

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:  # noqa: BLE001
    pass
ERG = []
NL = chr(10)


def pruefe(k, ok, text):
    ERG.append(bool(ok))
    print("%-4s %-9s %s" % (k, "bestanden" if ok else "FEHLER", text))


def summe(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest() if os.path.exists(p) else None


T = tempfile.mkdtemp(prefix="p19_")
HEUTE = date(2026, 9, 21)                                    # Messbasis endet 20.09. -> letzter abgeschlossener Tag
Z = pd.read_csv("data/_spot/am_kalibrierung.csv", sep=";", parse_dates=["date"]).set_index("date")
DESK_ABLAGE = os.path.join("data", SA.ABLAGE)
vor_desk = summe(DESK_ABLAGE)


def baue_kopie(o):
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


O = os.path.join(T, "A")
os.makedirs(O)
baue_kopie(O)
PROD = os.path.join(T, "prod.db")
shutil.copy(PROD_Q, PROD)
vor_prod, vor_kopie = summe(PROD), summe(os.path.join(O, SA.KOPIE))
cf = lambda: sqlite3.connect("file:%s?mode=ro" % PROD.replace("\\", "/"), uri=True)   # noqa: E731

FR = SA.fred_reihen(os.environ["FRED_API_KEY"], date.today())
STB = SA.stablecoins()
Q = {"fred": FR, "stb": STB}

# ── S1 ────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
st_m = np.array([SA.stand(a, b, c) for a, b, c in zip(Z.B1, Z.B2, Z.B3)])
st_p = np.array([P.stand(a, b, c) for a, b, c in zip(Z.B1, Z.B2, Z.B3)])
sf_m, sf_p = SA.stufen(Z), P.stufen(Z)
g = SA.geltend(sf_m)
w = int((g != g.shift(1)).iloc[1:].sum())
pruefe("S1", (st_m == Z.stand.values).all() and (st_m == st_p).all() and (sf_m == sf_p).all() and w == 18,
       "Stand %d/%d gleich der Kalibrierung, gleich p19 %d/%d · Stufe gleich p19 %d/%d · Haltezeit 7 T: %d Wechsel (Soll 18)" % (
           int((st_m == Z.stand.values).sum()), len(Z), int((st_m == st_p).sum()), len(Z), int((sf_m == sf_p).sum()), len(Z), w))

# ── S2 ────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
c = cf()
e = SA.lauf(O, c, heute=HEUTE, quellen=Q)
d = SA.lade(O)
Tn = pd.read_sql("SELECT * FROM ampel_tag", sqlite3.connect(os.path.join(O, SA.ABLAGE)), parse_dates=["datum"]).set_index("datum")
gem = Z.index.intersection(Tn.index)
d1, d2, d3 = [float((Tn[a].reindex(gem) - Z[b].reindex(gem)).abs().max()) for a, b in (("b1", "B1"), ("b2", "B2"), ("b3", "B3"))]
br_seite = ((Tn.breite.reindex(gem) >= 0.6) == (Z.Breite.reindex(gem) >= 0.6)) | Z.Breite.reindex(gem).isna()
st_gl = (Tn.stufe_roh.reindex(gem) == sf_p.reindex(gem))
db_ = (Tn.breite.reindex(gem) - Z.Breite.reindex(gem)).abs()
pruefe("S2", e["status"] == "ok" and d1 < 1e-12 and d2 < 1e-12 and d3 < 0.012 and bool(st_gl[br_seite].all()) and d["tag"]["stufe"] == "ungewohnt"
       and d["tag"]["stand"] == 2,
       "Lauf %s, %d Tage ab %s · gemeinsam mit der Kalibrierung %d Tage: B1 %.1e · B2 %.1e · B3 %.4f (Revision) · Breite 500 T gegen voll: "
       "mittel %.4f, groesste %.4f, andere Seite von 0,6 an %d Tagen · Stufe roh gleich %d/%d (wo die Breite dieselbe Seite hat: %d/%d) · "
       "heute %s %s, %d von 3" % (e["status"], e["tage"], Tn.index[0].date(), len(gem), d1, d2, d3, float(db_.mean()), float(db_.max()),
                                  int((~br_seite).sum()), int(st_gl.sum()), len(gem), int(st_gl[br_seite].sum()), int(br_seite.sum()),
                                  d["tag"]["datum"], d["tag"]["stufe"], d["tag"]["stand"]))

# ── S3 ────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
def meldungen(o):
    k = sqlite3.connect(os.path.join(o, SA.ABLAGE))
    try:
        return k.execute("SELECT stufe, art FROM ampel_meldung ORDER BY rowid").fetchall()
    finally:
        k.close()


m1 = meldungen(O)
e2 = SA.lauf(O, c, heute=HEUTE, quellen=Q)
pruefe("S3", m1 == [("ungewohnt", "startmarke")] and e["faellig"] is None and e2["faellig"] is None and meldungen(O) == m1,
       "erster Lauf: %s, faellig %s · zweiter Lauf: Meldungen %s, faellig %s" % (m1, e["faellig"], meldungen(O), e2["faellig"]))


# ── S4 / S5 ───────────────────────────────────────────────────────────────────────────────────────────────────────────────────
# ⚠️ KORREKTUR 17.10. (erster Lauf S5/S6 rot - Fehler im SZENARIO, nicht im Modul): am 20.09. faellt B1 zwischen 11. und 16.09. unter
# 20 %, die Rohstufe wechselt Season-Klima <-> Ende, und die Haltezeit haelt die geltende Stufe richtig fest. Jetzt der 31.07.2026:
# B1 aus (-15 %), B2 an (+5,3 %) -> mit B3 > 10 % ist die Rohstufe VORLAUF an jedem Tag des Boosts
HEUTE_V = date(2026, 7, 31)


def mit_b3(tage, faktor=1.15, heute=HEUTE_V):
    s = STB.copy()
    s[s.index > pd.Timestamp(heute) - pd.Timedelta(days=tage + 1)] *= faktor
    return {"fred": FR, "stb": s}


O4 = os.path.join(T, "V")
os.makedirs(O4)
shutil.copy(os.path.join(O, SA.KOPIE), os.path.join(O4, SA.KOPIE))
e40 = SA.lauf(O4, c, heute=HEUTE_V, quellen=Q)
d40 = SA.lade(O4)
e4 = SA.lauf(O4, c, heute=HEUTE_V, quellen=mit_b3(5))
d4 = SA.lade(O4)
pruefe("S4", d40["tag"]["stufe"] == "kalt" and d4["tag"]["stufe_roh"] == "Vorlauf" and d4["tag"]["stufe"] == "kalt" and e4["faellig"] is None,
       "31.07. ohne Boost: %s (%d von 3) · B3 5 Tage > 10 %%: roh %s, geltend %s, faellig %s" % (
           d40["tag"]["stufe"], d40["tag"]["stand"], d4["tag"]["stufe_roh"], d4["tag"]["stufe"], e4["faellig"]))
POST = []
SCH = {"an": False}
_SCHALTER_ECHT = G.season_ampel_aktiv
G.season_ampel_aktiv = lambda werte=None: SCH["an"]
versand = lambda b, t, bi=None: POST.append((b, t)) or True                  # noqa: E731
j5 = BG.season_ampel_job(cf, versand=versand, heute=HEUTE_V, ordner=O4, quellen=mit_b3(10))
j5b = BG.season_ampel_job(cf, versand=versand, heute=HEUTE_V, ordner=O4, quellen=mit_b3(10))
m5 = meldungen(O4)
pruefe("S5", bool(j5.get("faellig")) and j5["faellig"]["stufe"] == "Vorlauf" and not POST and m5[-1][1] == "ohne_mail" and not j5b["faellig"],
       "B3 10 Tage: faellig %s (Handlung '%s') · Schalter aus: Mails %d, Meldung %s · naechster Lauf faellig %s" % (
           (j5.get("faellig") or {}).get("stufe"), (j5.get("faellig") or {}).get("handlung"), len(POST), m5[-1], j5b.get("faellig")))

# ── S6 ────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
O6 = os.path.join(T, "B")
os.makedirs(O6)
shutil.copy(os.path.join(O, SA.KOPIE), os.path.join(O6, SA.KOPIE))
SA.lauf(O6, c, heute=HEUTE_V, quellen=Q)                                       # Startmarke kalt
SCH["an"] = True
geht = {"ok": False}
versand2 = lambda b, t, bi=None: POST.append((b, t)) or geht["ok"]           # noqa: E731
ja = BG.season_ampel_job(cf, versand=versand2, heute=HEUTE_V, ordner=O6, quellen=mit_b3(10))
n_fehl = len(POST)
geht["ok"] = True
jb = BG.season_ampel_job(cf, versand=versand2, heute=HEUTE_V, ordner=O6, quellen=mit_b3(10))
jc = BG.season_ampel_job(cf, versand=versand2, heute=HEUTE_V, ordner=O6, quellen=mit_b3(10))
txt = POST[-1][1] if POST else ""
pruefe("S6", n_fehl == 1 and not ja["gemailt"] and jb["gemailt"] and not jc["gemailt"] and len(POST) == 2 and meldungen(O6)[-1][1] == "gemailt"
       and "Season-Ampel Vorlauf" in POST[-1][0] and "BTC 91 T" in txt and "Stablecoins 91 T" in txt and "zwei zyklen" in txt.lower() and "beginn nicht genau vorab" in txt.lower()
       and "L-Kandidaten bereit" in txt,
       "Versand scheitert: Versuche %d, gemailt %s · naechster Lauf gemailt %s · dritter %s · Mails gesamt %d · Betreff '%s'" % (
           n_fehl, ja["gemailt"], jb["gemailt"], jc["gemailt"], len(POST), POST[-1][0] if POST else "-"))
SCH["an"] = False
print("     Mailtext S6:" + NL + NL.join("       | " + z for z in txt.split(NL)))

# ── S7 ────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
O7 = os.path.join(T, "C")
os.makedirs(O7)
shutil.copy(os.path.join(O, SA.KOPIE), os.path.join(O7, SA.KOPIE))
SA.lauf(O7, c, heute=HEUTE, quellen=Q)
s7 = STB.copy()
s7[(s7.index > pd.Timestamp("2025-12-01")) & (s7.index < pd.Timestamp("2026-01-15"))] *= 0.99
e7 = SA.lauf(O7, c, heute=HEUTE, quellen={"fred": FR, "stb": s7})
pruefe("S7", (e7["revision_b3"] or 0) > 0.005 and e7["faellig"] is None and e7["wechsel"] is None and len(meldungen(O7)) == 1,
       "Revision Stablecoins Dez./Jan. -1 %%: revision_b3 %.4f, Wechsel %s, Meldungen %d" % (e7["revision_b3"] or 0, e7["wechsel"], len(meldungen(O7))))

# ── S8 ────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
tag_vor = SA.lade(O7)["tag"]
e8 = SA.lauf(O7, c, fred_key="", heute=HEUTE)
d8 = SA.lade(O7)
z8 = SA.zeile(O7, d8, heute=HEUTE)
pruefe("S8", e8["status"] == "fehler" and d8["tag"] == tag_vor and "letzter Abruf gescheitert" in z8 and d8["lauf"]["status"] == "fehler",
       "ohne Schluessel: %s (%s) · Tageswert unveraendert %s · Zeile: '%s'" % (e8["status"], e8["fehler"], d8["tag"] == tag_vor, z8[-60:]))

# ── S9 ────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
am = SA.zeile(O, SA.lade(O), heute=HEUTE)
Z9 = "  Season-Ampel " + am + "." + NL
f1 = {"symbol": "XRP", "ausloese_kurs": 3.0, "startkurs_usd": 1.0, "menge": 10.0, "ende": "2026-12-31", "start": "2026-01-01",
      "ausloese_tag": "2026-09-20"}
erg9 = {}
for name, fn in (("B1", lambda a: SM.mail(f1, 2.0, False, None, None, "lang: neutral", *a)),
                 ("B3", lambda a: SU.mail({"symbol": "XRP", "kuerzel": "XRP", "alter_h": 2.0, "menge": 10.0, "utc": "2026-09-20 10:00", "id": 1, "titel": "t"}, False, None, 1.0,
                                          0.9, None, "lang: neutral", *a)),
                 ("B4", lambda a: AB.mail({"stichtag": "2026-09-01", "art": "neu", "liste": [], "neu": []}, {}, set(), None, "lang: neutral", *a))):
    try:
        ohne, mit = fn(())[1], fn((am,))[1]
        erg9[name] = "ok" if (Z9 in mit and mit.replace(Z9, "") == ohne) else "ABWEICHUNG (Zeile %s, Rest gleich %s)" % (
            Z9 in mit, mit.replace(Z9, "") == ohne)
    except Exception as ex:                                                   # noqa: BLE001
        erg9[name] = "%s: %s" % (type(ex).__name__, ex)
pruefe("S9", all(v == "ok" for v in erg9.values()), "mit Zeile, ohne sie wie vorher: %s · Zeile: '%s'" % (erg9, am))

# ── S10 ───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
import p18_voranalyse as P18  # noqa: E402
Gx = P18.G
aus = set(Gx["SONDER"]) | {s for s in Gx["K"].columns if s not in Gx["UNIV"]} | set(P.UEBERNOMMEN)
z10 = P18.B4(Gx["K"], Gx["U"], aus, P18.cgh_nur).fuenftel(pd.Timestamp("2026-09-01")).set_index("sym")
O10 = os.path.join(T, "D")
os.makedirs(O10)
k10 = sqlite3.connect(os.path.join(O10, SA.ABLAGE))
gehalten = {r[0] for r in c.execute("SELECT symbol FROM holdings WHERE COALESCE(quantity,0) + COALESCE(staked_quantity,0) > 0")}
n10 = AB._universum_ablegen(k10, c, "2026-09-01", z10, {s for s in z10.index if AB._zuordnung().get(s, (s, 1))[0] in gehalten or s in gehalten})
k10.commit()
k10.close()
kd = AB.kandidaten(O10)
pruefe("S10", kd["oben_gesamt"] == 69 and kd["anzahl"] == 67 and [x[0] for x in kd["liste"]["H"]] == ["ETC", "LTC", "ADA", "DOGE", "ICP", "UNI"],
       "Universum %d abgelegt · oberes Fuenftel %d, handelbar %d (p19 Teil 4: 69 / 67) · H %s · M %s" % (
           n10, kd["oben_gesamt"], kd["anzahl"], ", ".join(x[0] for x in kd["liste"]["H"]), ", ".join(x[0] for x in kd["liste"].get("M", [])[:4])))

# ── S11 ───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
import agent.betriebslage as BL  # noqa: E402
import remote.status as RS  # noqa: E402
import ui.markt_tab as MT  # noqa: E402
u = SA.uebersicht(O, heute=HEUTE)
RS._daten_ordner = lambda: O                                               # noqa: E731
try:
    gs = RS._get_season_ampel.__wrapped__() if hasattr(RS._get_season_ampel, "__wrapped__") else RS._get_season_ampel()
except Exception as ex:                                                       # noqa: BLE001
    gs = {"fehler": str(ex)}
sch = BL.schalter()
html = open("remote/server.py", encoding="utf-8").read()
zl = MT.ampel_zeilen(u)
tk_ok, tk_txt = False, ""
try:
    import tkinter as tk
    from tkinter import ttk
    root = tk.Tk()
    root.withdraw()
    nb = ttk.Notebook(root)
    mk, sp = MT.MarktKryptoTab(nb, nb), MT.SpotTab(nb, nb)
    nb.add(mk, text="Markt (Krypto)")
    nb.add(sp, text="Spot")
    mk._ordner = sp._ordner = O
    mk.refresh(erzwingen=True)
    sp.refresh(erzwingen=True)
    tk_ok = len(mk.ampel_tree.get_children()) == 3 and mk.kopf.cget("text").startswith("Season-Ampel: ungewohnt")
    tk_txt = "%s · Spot: %s" % (mk.kopf.cget("text"), sp.kopf.cget("text"))
    root.destroy()
except Exception as ex:                                                       # noqa: BLE001
    tk_txt = "%s: %s" % (type(ex).__name__, ex)
pruefe("S11", u["zustand"] == "ok" and u["stufe"] == "ungewohnt" and gs.get("stufe") == "ungewohnt"
       and sch.get("season_ampel_aktiv") is True and 'id="ampel-kopf"' in html and len(zl) == 3 and tk_ok,
       "uebersicht %s/%s · Statusseite %s · Schalter season_ampel_aktiv %s · Bedingungszeilen %d · Reiter: %s" % (
           u["zustand"], u.get("stufe"), gs.get("stufe"), sch.get("season_ampel_aktiv"), len(zl), tk_txt))
c.close()

# ── S13 / S14 (E-124, 18.10.2026): der Uebergang am NB - Schalter von aus auf an ────────────────────────────────────────────────
POST.clear()
SCH["an"] = True                                                              # O4: Vorlauf war faellig, mit Schalter aus 'ohne_mail' vermerkt (S5)
j13 = BG.season_ampel_job(cf, versand=versand, heute=HEUTE_V, ordner=O4, quellen=mit_b3(10))
pruefe("S13", not POST and not j13.get("faellig") and not j13.get("gemailt") and meldungen(O4)[-1][1] == "ohne_mail",
       "nach dem Einschalten: faellig %s, gemailt %s, Mails %d, letzte Meldung %s (nicht nachgeholt)" % (
           j13.get("faellig"), j13.get("gemailt"), len(POST), meldungen(O4)[-1]))
SCH["an"] = False
G.season_ampel_aktiv = _SCHALTER_ECHT                                         # der echte Schalter aus Basisinfos/regel0_betrieb.yaml
z14 = SA.zeile(O, SA.lade(O), heute=HEUTE)
pruefe("S14", G.season_ampel_aktiv() is True and G.VORGABE["season_ampel_aktiv"] is False and "zwei Zyklen" in z14
       and "Beginn nicht genau vorab" in z14 and "einem Zyklus" not in z14,
       "regel0_betrieb.yaml season_ampel_aktiv %s (Code-Vorgabe %s) · Zeile: '...%s'" % (G.season_ampel_aktiv(), G.VORGABE["season_ampel_aktiv"], z14[-110:]))

# ── S12 ───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
pruefe("S12", summe(PROD) == vor_prod and summe(os.path.join(O, SA.KOPIE)) == vor_kopie and summe(DESK_ABLAGE) == vor_desk,
       "Wegwerf-Produktion, Betriebskopie und Desktop-%s unveraendert" % DESK_ABLAGE)

wegwerf.aufraeumen(T)
print("\n%d von %d bestanden" % (sum(ERG), len(ERG)))
sys.exit(0 if all(ERG) else 1)
