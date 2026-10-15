"""Buendel O52 + O51 + W1 (15.10.2026, Schritt7 §23.53, E-112) - Pruefstand am SEITENEFFEKT, kein Netz, nur Wegwerf-Dateien (D:).

    python Basisinfos/Rechenkern_02_10/o52_pruefstand.py > Basisinfos/Rechenkern_02_10/o52_pruefstand.txt

  T1  Terminzeile CPI 14.10.2026 (Einstieg 12:00 UTC): "14.10. 14:30 Uhr (30 min nach dem Einstieg)", Faktor 1,8 und 1,1 aus der Messung
  T2  Zeitumstellung: CPI 11.03.2026 (USA schon Sommerzeit, Europa noch nicht) -> 13:30 Ortszeit; FOMC 28.10.2026 -> 19:00;
      CPI 10.11.2026 -> 14:30; je unabhaengig ueber pandas gerechnet
  T3  Fenster: Termin 1 h VOR dem Einstieg zaehlt ("vor dem Einstieg"), 3 h davor und nach dem Ausstieg nicht
  T4  drei Zustaende: Termin / kein Termin / NICHT ABGEFRAGT (kein Schluessel, FRED-Fehler, FOMC-Liste zu Ende) - nie verwechselt
  T5  ein FRED-Abruf je Tag und Art, auch ein Fehlschlag wird gemerkt (gezaehlte Aufrufe)
  T6  REGEL0-Mail: Zeile "Termin" in Einschaetzung und Technik, Text und HTML; ohne Lieferant bitgleich; ein scheiternder Lieferant
      haelt die Mail nicht auf (versende mit gestelltem Versand)
  W1  Pruefblock: erste Kurzzeile ist die Markierung "trennt nicht", Langfassung ohne "noch nicht gemessen"; in der Mail sichtbar
  E1  Entfernen gesperrt bei Bestand frei, nur gestakt, offener Hebelposition - Watchlist unveraendert
  E2  Entfernen erlaubt ohne Bestand: weg aus get_watchlist (Grundliste UND Ergaenzung), Spot-Kreis unveraendert, Rueckweg ueber
      add_watchlist_entry holt es zurueck
  E3  Unbekanntes Symbol -> Fehler; config.yaml und die Desktop-Produktions-DB unveraendert (Pruefsumme)
"""
import hashlib
import os
import sqlite3
import sys
import tempfile
from datetime import date, datetime, timedelta, timezone

WURZEL = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(WURZEL)
sys.path.insert(0, WURZEL)
sys.stdout.reconfigure(encoding="utf-8")
import wegwerf  # noqa: E402,F401  Wegwerf-Ordner auf D: und Aufraeumen ohne stilles Scheitern (15.10.2026)

import pandas as pd  # noqa: E402

import agent.regel0_groesse as G  # noqa: E402
import agent.regel0_llm as LLM  # noqa: E402
import agent.regel0_mail as RM  # noqa: E402
import agent.spot_mitnahme as SM  # noqa: E402
import agent.termin_fakt as TF  # noqa: E402
import config as C  # noqa: E402
from database import db  # noqa: E402

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


PROD_ECHT = db.DB_PATH
VOR = {"config": summe(os.path.join("Basisinfos", "config.yaml")), "prod": summe(PROD_ECHT)}

# gestellte FRED-Termine (Stand der echten Veroeffentlichungstage, data/_termine/termine.json)
FRED_TAGE = {"cpi": [date(2026, 3, 11), date(2026, 10, 14), date(2026, 11, 10)], "nfp": [date(2026, 10, 2), date(2026, 11, 6)]}
AUFRUFE = []


def fred_gestellt(art, heute, fred_key):
    AUFRUFE.append((art, heute))
    return next((t for t in FRED_TAGE[art] if t >= heute), None), True


TF._fred_naechster = fred_gestellt
U = lambda s: datetime.strptime(s, "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)  # noqa: E731


def ort(tag, uhr):
    return pd.Timestamp("%s %s" % (tag, uhr)).tz_localize("America/New_York").tz_convert("Europe/Vienna").strftime("%d.%m. %H:%M")


# ══ T1 ═════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════
z1 = TF.zeile(U("2026-10-14 12:00"), U("2026-10-15 12:00"), "x")
pruefe("T1", "US-Inflation (CPI) 14.10. 14:30 Uhr (30 min nach dem Einstieg)" in z1 and "1,8×" in z1 and "1,1×" in z1
       and "NICHT ABGEFRAGT" not in z1, z1)

# ══ T2 ═════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════
fall = [("cpi", "2026-03-11", "08:30", U("2026-03-11 10:00")), ("fomc", "2026-10-28", "14:00", U("2026-10-28 12:00")),
        ("cpi", "2026-11-10", "08:30", U("2026-11-10 12:00"))]
ok2, txt2 = True, []
for art, tag, uhr, ein in fall:
    z = TF.zeile(ein, ein + timedelta(hours=24), "x")
    soll = "%s %s Uhr" % (TF.NAME[art], ort(tag, uhr))
    ok2 &= soll in z
    txt2.append("%s -> %s %s" % (tag, soll, "✔" if soll in z else "✘ " + z))
pruefe("T2", ok2, " · ".join(txt2))

# ══ T3 ═════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════
cpi = U("2026-10-14 12:30")
z_vor1 = TF.zeile(cpi + timedelta(hours=1), cpi + timedelta(hours=25), "x")
z_vor3 = TF.zeile(cpi + timedelta(hours=3), cpi + timedelta(hours=27), "x")
z_nach = TF.zeile(cpi - timedelta(hours=30), cpi - timedelta(hours=6), "x")
pruefe("T3", "(1 h vor dem Einstieg)" in z_vor1 and "kein US-" in z_vor3 and "kein US-" in z_nach,
       "1 h davor: %s · 3 h davor: %s · Ausstieg davor: %s" % ("CPI" in z_vor1, "kein" in z_vor3, "kein" in z_nach))

# ══ T4 ═════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════
z_ohne_key = TF.zeile(U("2026-10-16 07:00"), U("2026-10-17 07:00"), "")
_alt = TF._fred_naechster
TF._fred_naechster = lambda art, heute, k: (None, False)
z_fehler = TF.zeile(U("2026-10-16 07:00"), U("2026-10-17 07:00"), "x")
TF._fred_naechster = _alt
z_kein = TF.zeile(U("2026-10-16 07:00"), U("2026-10-17 07:00"), "x")
z_ende = TF.zeile(U("2027-12-20 10:00"), U("2027-12-21 10:00"), "x")
pruefe("T4", "NICHT ABGEFRAGT" in z_ohne_key and "US-Inflation (CPI), US-Arbeitsmarkt" in z_ohne_key
       and "NICHT ABGEFRAGT" in z_fehler and "kein US-" in z_kein and "NICHT ABGEFRAGT" not in z_kein
       and "NICHT ABGEFRAGT (kein Nein): US-Zinsentscheid (FOMC)" in z_ende,
       "ohne Schluessel / FRED-Fehler / kein Termin / FOMC-Liste zu Ende: %s / %s / %s / %s" % (
           "NICHT ABGEFRAGT" in z_ohne_key, "NICHT ABGEFRAGT" in z_fehler, "kein US-" in z_kein and "NICHT" not in z_kein,
           "FOMC" in z_ende.split("NICHT ABGEFRAGT")[-1] if "NICHT ABGEFRAGT" in z_ende else False))

# ══ T5 ═════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════
import api.macro as AM  # noqa: E402

TF._fred_naechster = _gespeichert = TF.__dict__.get("_fred_naechster_orig") or _alt
import importlib  # noqa: E402

importlib.reload(TF)                 # die echte _fred_naechster mit Speicher
zaehler = {"n": 0}


class _R:
    date = "2026-10-14"


def _gnr(rid, name, key, session=None, today=None):
    zaehler["n"] += 1
    if rid == 50:
        raise RuntimeError("502 gestellt")
    return _R()


_orig_gnr = AM.get_next_fred_release
AM.get_next_fred_release = _gnr
TF._SPEICHER.clear()
a = TF.zeile(U("2026-10-14 12:00"), U("2026-10-15 12:00"), "x")
b = TF.zeile(U("2026-10-14 12:00"), U("2026-10-15 12:00"), "x")
AM.get_next_fred_release = _orig_gnr
pruefe("T5", zaehler["n"] == 2 and a == b and "US-Inflation (CPI) 14.10." in a and "NICHT ABGEFRAGT (kein Nein): US-Arbeitsmarkt" in a,
       "Abrufe %d bei zwei Zeilen (CPI ok, Arbeitsmarkt gestellt 502 und gemerkt) · %s" % (zaehler["n"], a))
TF._fred_naechster = fred_gestellt

# ══ T6 REGEL0-Mail ═════════════════════════════════════════════════════════════════════════════════════════════════════════════
_rf = dict(symbol="TAO", bitpanda="TAO", signalstunde="2026-10-14 10:00", einstieg="2026-10-14 11:00", ausstieg="2026-10-15 11:00",
           kurs=300.0, kurs_markt="spot", p2=0.001, p3=0.007, p5=0.107, vh=0.0411, kurs_eur=260.0)
_g = G.rechne(3, 0, G.lade())
_j = datetime(2026, 10, 14, 11, 9, tzinfo=timezone.utc)
mt = TF.mailteil(_rf, "x")
s_mit = RM.signal_mail(_rf, 3, False, _g, {}, _j, None, None, None, None, mt)[1]
s_ohne = RM.signal_mail(_rf, 3, False, _g, {}, _j)[1]
h_mit = RM.signal_html(_rf, 3, False, _g, {}, _j, None, None, 0, None, None, mt)
_fl = lambda x: " ".join(x.split())  # noqa: E731
vorn, tech = s_mit.split("5  TECHNIK")[0], s_mit.split("5  TECHNIK")[1]
ok6 = (_fl(mt["ein"]) in _fl(vorn) and "Fakt, nicht Teil der Regel (O52)" in _fl(tech) and "14.10. 14:30 Uhr" in h_mit
       and "Termin" not in s_ohne and s_ohne == RM.signal_mail(_rf, 3, False, _g, {}, _j, None, None, None, None, None)[1])
# versende mit scheiterndem Termin-Lieferanten (Muster o29_pruefstand): die Mail geht trotzdem, und mit Lieferant steht die Zeile darin
T = tempfile.mkdtemp(prefix="o52_")
import agent.regel0_ablage as AB  # noqa: E402


def _post(d, sym, st, termin):
    c = AB.oeffne(d)
    aus = (datetime.strptime(st, "%Y-%m-%d %H:%M") + timedelta(hours=24)).strftime("%Y-%m-%d %H:%M")    # wie im Betrieb: 24 h
    w = {"symbol": sym, "signalstunde": st, "einstieg": st, "ausstieg": aus, "vh": 0.042, "stufe_vorlaeufig": 3, "stufe": 3, "p2": 0.001,
         "p3": 0.007, "p5": 0.1, "hebel_schalter": 1, "bitpanda": sym, "zusatz": 0, "btc": 0, "version": "REGEL0.1",
         "erfasst_am": st, "kurs": 1.0, "kurs_markt": "spot"}
    c.execute("INSERT OR REPLACE INTO signal (%s) VALUES (%s)" % (",".join(w), ",".join("?" * len(w))), list(w.values()))
    c.commit()
    c.close()
    post = []
    jetzt = datetime.strptime(st, "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc, minute=10) + timedelta(hours=1)
    RM.versende(d, lambda b, t, *a, **k: post.append(t) or True, jetzt=jetzt,
                kurse=lambda: ({sym: 1.0}, {sym + "USDT": 1.0}, {sym: 0.9}), termin=termin)
    return [t for t in post if "HEBEL-SIGNAL" in t]      # nur die Signalmail - der Ausstieg ist im Test sofort faellig (Erinnerung)


def _kaputt(r):
    raise RuntimeError("Termin-Lieferant gestellt kaputt")


d1, d2 = os.path.join(T, "a"), os.path.join(T, "b")
os.makedirs(d1)
os.makedirs(d2)
p_kaputt = _post(d1, "TAO", "2026-10-14 11:00", _kaputt)
p_gut = _post(d2, "TAO", "2026-10-14 11:00", lambda r: TF.mailteil(r, "x"))
ok6v = len(p_kaputt) == 1 and "Termin" not in p_kaputt[0].split("5  TECHNIK")[0] and len(p_gut) == 1 and "14.10. 14:30 Uhr" in _fl(p_gut[0])
pruefe("T6", ok6 and ok6v, "Einschaetzung %s · Technik %s · HTML %s · ohne bitgleich %s · versende: kaputter Lieferant -> Mail geht %s, "
       "echter Lieferant -> Zeile in der versandten Mail %s" % (
           _fl(mt["ein"]) in _fl(vorn), "O52" in tech, "14.10. 14:30 Uhr" in h_mit, "Termin" not in s_ohne, len(p_kaputt) == 1,
           len(p_gut) == 1 and "14.10. 14:30 Uhr" in _fl(p_gut[0])))

# ══ W1 Pruefblock ══════════════════════════════════════════════════════════════════════════════════════════════════════════════
erg = {"trader": {"urteil": "dagegen", "stimmen": ["dagegen"] * 4 + ["neutral"], "begruendung": "Abwärtsstruktur. Rest."}}
kat = LLM.lade()
mtl = LLM.mail_teile(erg, kat)
s_w = RM.signal_mail(_rf, 3, False, _g, {}, _j, mtl)[1]
pruefe("W1", mtl["kurz"][0] == LLM.MARKE and not any("noch nicht gemessen" in z for z in mtl["lang"])
       and any("trennt NICHT" in z for z in mtl["lang"]) and "trennt nicht – nicht danach handeln" in _fl(s_w.split("5  TECHNIK")[0]),
       "Kurz[0] %s · Langfassung: %s" % (mtl["kurz"][0], next(z.strip() for z in mtl["lang"] if "Messstand" in z)[:120]))

# ══ E1-E3 Entfernen (Wegwerf-DB) ═══════════════════════════════════════════════════════════════════════════════════════════════
WEG = os.path.join(T, "prod.db")
c = sqlite3.connect(WEG)
c.execute("CREATE TABLE holdings (symbol TEXT PRIMARY KEY, quantity REAL, staked_quantity REAL)")
c.execute("CREATE TABLE hebel_positions (id INTEGER PRIMARY KEY, symbol TEXT, status TEXT, geschlossen_am TEXT)")
grund = [e["symbol"] for e in C.load_config()["watchlist"] if e.get("assetklasse", "krypto") == "krypto" and not e.get("ist_cash_aequivalent")]
frei, gestakt, hebel, leer = grund[1], grund[2], grund[3], grund[4]
c.executemany("INSERT INTO holdings VALUES (?,?,?)", [(frei, 1.5, 0), (gestakt, 0, 2.0), (leer, 0, 0)])
c.execute("INSERT INTO hebel_positions (symbol, status, geschlossen_am) VALUES (?, 'offen', NULL)", (hebel,))
c.execute("INSERT INTO hebel_positions (symbol, status, geschlossen_am) VALUES (?, 'geschlossen', '2026-10-01')", (leer,))
c.commit()
c.close()
db.DB_PATH = WEG
C._config_cache = None
vor_wl = [a.symbol for a in C.get_watchlist()]
fehler = {}
for s in (frei, gestakt, hebel):
    try:
        C.remove_watchlist_entry(s)
        fehler[s] = None
    except C.WatchlistWriteError as exc:
        fehler[s] = str(exc)
pruefe("E1", all(fehler.values()) and [a.symbol for a in C.get_watchlist()] == vor_wl,
       " · ".join("%s: %s" % (s, f) for s, f in fehler.items()))

cw = sqlite3.connect(WEG)
kreis_vor = SM.kreis(cw, C.get_watchlist())
C.add_watchlist_entry("ZZTEST", "Testasset", "taktisch", "beobachtung", coingecko_id="zztest", herkunft="pruefung")
C.remove_watchlist_entry(leer)
C.remove_watchlist_entry("ZZTEST")
nach_wl = [a.symbol for a in C.get_watchlist()]
kreis_nach = SM.kreis(cw, C.get_watchlist())
C.add_watchlist_entry(leer, "zurueck", "taktisch", "beobachtung", herkunft="pruefung")
zurueck = leer in [a.symbol for a in C.get_watchlist()]
cw.close()
pruefe("E2", leer not in nach_wl and "ZZTEST" not in nach_wl and set(nach_wl) == set(vor_wl) - {leer} and kreis_vor == kreis_nach and zurueck,
       "%s (Grundliste) und ZZTEST (Ergaenzung) entfernt · uebrige gleich %s · Spot-Kreis gleich %s %s · Rueckweg %s" % (
           leer, set(nach_wl) == set(vor_wl) - {leer}, kreis_vor == kreis_nach, sorted(kreis_nach), zurueck))

try:
    C.remove_watchlist_entry("GIBTESNICHT")
    e3 = False
except C.WatchlistWriteError as exc:
    e3 = "nicht in der Watchlist" in str(exc)
db.DB_PATH = PROD_ECHT
C._config_cache = None
NACH = {"config": summe(os.path.join("Basisinfos", "config.yaml")), "prod": summe(PROD_ECHT)}
pruefe("E3", e3 and NACH == VOR, "unbekanntes Symbol abgewiesen %s · config.yaml unveraendert %s · Desktop-Prod unveraendert %s" % (
    e3, NACH["config"] == VOR["config"], NACH["prod"] == VOR["prod"]))

print("\nMuster REGEL0, Einschaetzung (T6): " + next((z.strip() for z in s_mit.splitlines() if "Termin" in z), "-"))
wegwerf.aufraeumen(T)
print("\n%d von %d bestanden" % (sum(ERG), len(ERG)))
