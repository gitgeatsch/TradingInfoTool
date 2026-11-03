"""G14 (03.11.2026, E-167) am SEITENEFFEKT: BTC/ETH/SOL bleiben fuer REGEL0 und Hebel zugelassen - der Schalter bleibt beim Nutzer,
faellt aber nicht mehr versehentlich (Rueckfrage) und nicht mehr unsichtbar (Statusseite/Teilexport/Diagnose); ein Lesefehler der
Schalter wird gemeldet statt verschluckt (L4).

    python -X utf8 Basisinfos/Rechenkern_02_10/pruefe_g14.py

Die GUI-Handler laufen OHNE Fenster (Attrappen fuer Baum und Status), die Datenbank liegt im Speicher bzw. als Wegwerfdatei (D:).
Kein Netz, keine Mail, keine Produktion - am Ende sha256 von data/tradinginfotool.db (.db und -wal) unveraendert.
"""
import hashlib
import os
import sqlite3
import sys
import tempfile
from types import SimpleNamespace as NS

os.chdir(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.getcwd())
sys.stdout.reconfigure(encoding="utf-8")
import wegwerf  # noqa: E402,F401

PROD = os.path.join("data", "tradinginfotool.db")


def fingerabdruck():
    return {e: (hashlib.sha256(open(PROD + e, "rb").read()).hexdigest() if os.path.exists(PROD + e) else None) for e in ("", "-wal")}


_vorher = fingerabdruck()

import agent.kernwerte as KW  # noqa: E402
import agent.betriebslage as BL  # noqa: E402
import agent.regel0_stundenlauf as SL  # noqa: E402
import scheduler.background as BG  # noqa: E402
import ui.app as APP  # noqa: E402
import ui.hebel_tab as HT  # noqa: E402
from database import db  # noqa: E402

ORDNER = tempfile.mkdtemp(prefix="g14_")
from pathlib import Path as _P  # noqa: E402
db.DB_PATH = _P(os.path.join(ORDNER, "umgebogen.db"))

ERG = []


def pruefe(name, ok, detail):
    ok = bool(ok)
    ERG.append(ok)
    print("%-4s %-9s %s" % (name, "bestanden" if ok else "FEHLER", detail))


# ---- G1 Rueckfrage nur beim AUSschalten eines Kernwerts ----------------------------------------------------------------
f = {(s, an): KW.rueckfrage(s, an) for s in ("BTC", "eth", "SOL", "LINK") for an in (True, False)}
pruefe("G1", all(f[(s, False)] for s in ("BTC", "eth", "SOL")) and not any(f[(s, True)] for s in ("BTC", "eth", "SOL"))
       and f[("LINK", False)] is None and "ETH" in f[("eth", False)],
       "Kern aus -> Frage, Kern an -> keine, LINK aus -> keine")

# ---- G2/G3 die beiden GUI-Knoepfe am echten Handler ---------------------------------------------------------------------
mem = sqlite3.connect(":memory:")
mem.row_factory = sqlite3.Row
mem.execute("CREATE TABLE asset_hebel_settings (symbol TEXT PRIMARY KEY, hebel_pruefung_erlaubt INTEGER)")
mem.executemany("INSERT INTO asset_hebel_settings VALUES (?, 1)", [("BTC",), ("LINK",)])
mem.commit()


class Verb:
    """Die Speicher-DB unter einem close(), das sie NICHT schliesst (die Handler schliessen ihre Verbindung)."""
    def __getattr__(self, n):
        return getattr(mem, n)

    def close(self):
        pass


def wert(s):
    r = mem.execute("SELECT hebel_pruefung_erlaubt FROM asset_hebel_settings WHERE symbol=?", (s,)).fetchone()
    return None if r is None else int(r[0])


fragen = []
antwort = {"ja": False}


def askyesno(titel, text, **k):
    fragen.append(text)
    return antwort["ja"]


APP.messagebox.askyesno = askyesno
HT.messagebox.askyesno = askyesno
APP.messagebox.showinfo = HT.messagebox.showinfo = lambda *a, **k: None


def watchlist_klick(sym):
    tree = NS(selection=lambda: ["i1"], item=lambda i, k: (sym,))
    selbst = NS(_watchlist_frame=NS(tree=tree), _watchlist=[NS(symbol=sym, assetklasse="krypto", ist_cash_aequivalent=False)],
                _db_conn_factory=lambda: Verb(), _refresh_watchlist_from_db=lambda: None)
    APP.TradingInfoToolApp._toggle_hebel_pruefung_erlaubt(selbst)


def hebeltab_klick(sym):
    selbst = NS(frei_tree=NS(selection=lambda: ["i1"]), _frei_by_iid={"i1": sym}, _conn_factory=lambda: Verb(),
                frei_status=NS(config=lambda **k: None), _freigabe_neu=lambda: None)
    HT.HebelTab._umschalten(selbst)


erg2 = []
for klick, name in ((watchlist_klick, "Watchlist"), (hebeltab_klick, "Hebel-Reiter")):
    mem.execute("UPDATE asset_hebel_settings SET hebel_pruefung_erlaubt=1")
    mem.commit()
    fragen.clear()
    antwort["ja"] = False
    klick("BTC")                                  # Nein -> bleibt an
    nein = wert("BTC")
    antwort["ja"] = True
    klick("BTC")                                  # Ja -> aus
    ja = wert("BTC")
    n_fragen_aus = len(fragen)
    klick("BTC")                                  # wieder an: KEINE Frage
    wieder = wert("BTC")
    klick("LINK")                                 # Nicht-Kern aus: KEINE Frage
    link = wert("LINK")
    erg2.append((name, nein, ja, wieder, link, n_fragen_aus, len(fragen)))
pruefe("G2", all(e[1:] == (1, 0, 1, 0, 2, 2) for e in erg2),
       "je Knopf (Name, nach Nein, nach Ja, wieder an, LINK aus, Fragen bis aus, Fragen gesamt): %s" % erg2)
ohne_neu = KW.rueckfrage
KW.rueckfrage = lambda s, n: None                  # Mutationsprobe: ohne die Regel muss G2 anschlagen
mem.execute("UPDATE asset_hebel_settings SET hebel_pruefung_erlaubt=1")
antwort["ja"] = False
fragen.clear()
watchlist_klick("BTC")
hebeltab_klick("BTC")
mut = (wert("BTC"), len(fragen))
KW.rueckfrage = ohne_neu
pruefe("G3", mut == (1, 0), "MUTATION ohne Rueckfrage: BTC nach zwei Klicks %s (aus, wieder an - ungefragt), Fragen %d - die Pruefung G2 "
       "haengt also an der Regel" % mut)

# ---- G4/G5 Statusseite und Teilexport: Warnzeile, sobald ein Kernwert nicht an ist ------------------------------------
daten = os.path.join(ORDNER, "daten")
os.makedirs(daten)
p = os.path.join(daten, "tradinginfotool.db")
c = sqlite3.connect(p)
c.execute("CREATE TABLE asset_hebel_settings (symbol TEXT PRIMARY KEY, hebel_pruefung_erlaubt INTEGER)")
c.executemany("INSERT INTO asset_hebel_settings VALUES (?, ?)", [("BTC", 1), ("ETH", 0), ("LINK", 1)])   # SOL ohne Zeile
c.commit()
c.close()
_ds_echt = BL.regel0_datensymbole
BL.regel0_datensymbole = lambda d=None: {"BTC", "ETH", "SOL", "LINK"}
na = BL.neuaufnahme_und_abgleich(daten, p)
c = sqlite3.connect(p)
c.execute("UPDATE asset_hebel_settings SET hebel_pruefung_erlaubt=1")
c.execute("INSERT INTO asset_hebel_settings VALUES ('SOL', 1)")
c.commit()
c.close()
na_gut = BL.neuaufnahme_und_abgleich(daten, p)
BL.regel0_datensymbole = lambda d=None: {"ETH", "SOL", "LINK"}
na_ohne_daten = BL.neuaufnahme_und_abgleich(daten, p)
qs = open(os.path.join("remote", "server.py"), encoding="utf-8").read()
qt = open("nb_teilexport_betriebsdaten.py", encoding="utf-8").read()
qd = open("extract_notebook_diagnose.py", encoding="utf-8").read()
pruefe("G4", na["kern_luecke"] == ["ETH", "SOL"] and na_gut["kern_luecke"] == [] and na_ohne_daten["kern_luecke"] == ["BTC ohne REGEL0-Daten"],
       "ETH aus + SOL ohne Zeile -> %s · alle an -> %s · BTC ohne Daten -> %s" % (na["kern_luecke"], na_gut["kern_luecke"],
                                                                                 na_ohne_daten["kern_luecke"]))
import remote.status as ST  # noqa: E402
_alt_na = BL.neuaufnahme_und_abgleich
BL.neuaufnahme_und_abgleich = lambda d, prod=None: {"neuaufnahme": [], "ohne_daten": [], "gesperrt": [], "kern_luecke": ["ETH"]}
st = ST._get_neuaufnahme.__wrapped__()
BL.neuaufnahme_und_abgleich = _alt_na
pruefe("G5", st.get("kern_luecke") == ["ETH"] and "b.kern_luecke && b.kern_luecke.length" in qs and "unter err" in qs.split("b.kern_luecke.length) x +=")[1][:80]
       and 'na.get("kern_luecke")' in qt and '"kern_hebel_luecke"' in qd,
       "Statusseite reicht die Luecke durch (%s) und zeigt sie ROT; Teilexport und Diagnose fuehren sie" % st.get("kern_luecke"))

# ---- G6 der Kern steht im REGEL0-Betrieb: Zuordnung nicht gesperrt, Daten vorhanden (Desktop-Datenstand) -------------------
zu_bp, _fak = SL._binance_zu_bitpanda()
BL.regel0_datensymbole = _ds_echt
try:
    datensym = _ds_echt()
except Exception as exc:                                     # noqa: BLE001
    datensym = {"fehlt: %s" % exc}
pruefe("G6", all(zu_bp.get(k, k) == k for k in KW.KERN) and set(KW.KERN) <= datensym,
       "symbol_zuordnung: Kern %s (nicht gesperrt) · REGEL0-Datenbestand am Rechner enthaelt %s" % (
           {k: zu_bp.get(k, k) for k in KW.KERN}, sorted(set(KW.KERN) & datensym)))

# ---- G7/G8 L4: Lesefehler der Schalter wird gemeldet, nicht verschluckt --------------------------------------------------
kaputt = os.path.join(ORDNER, "kaputt")
os.makedirs(kaputt)
open(os.path.join(kaputt, "tradinginfotool.db"), "wb").write(b"das ist keine sqlite-datei" * 100)
r_k = SL._hebel_schalter(kaputt)
f_k = list(SL.SCHALTER_FEHLER)
r_ok = SL._hebel_schalter(daten)
f_ok = list(SL.SCHALTER_FEHLER)
r_fehlt = SL._hebel_schalter(os.path.join(ORDNER, "gibt_es_nicht"))
f_fehlt = list(SL.SCHALTER_FEHLER)
pruefe("G7", r_k == {} and f_k and r_ok.get("BTC") is True and not f_ok and r_fehlt == {} and not f_fehlt,
       "kaputte Datei -> {} + Fehler %s · gute Datei -> kein Fehler · fehlende Datei (Probe) -> still" % (f_k[:1]))
art = (BG.regel0_meldung_art({"meldung": "Hebel-Schalter nicht lesbar", "nachgeholt": [], "veraltet_gemeldet": False,
                              "nachholen_ausgelassen": [], "schalter_fehler": ["x"]}),
       BG.regel0_meldung_art({"meldung": "nachgeholt: a · Hebel-Schalter nicht lesbar", "nachgeholt": ["a"], "veraltet_gemeldet": False,
                              "nachholen_ausgelassen": [], "schalter_fehler": ["x"]}),
       BG.regel0_meldung_art({"meldung": "nachgeholt: a", "nachgeholt": ["a"], "veraltet_gemeldet": False,
                              "nachholen_ausgelassen": [], "schalter_fehler": []}))
# G8 am ECHTEN betrieb_lauf (Gegenpruefung 03.11.: vorher nur Textreihenfolge): Rechnung durch Attrappen ersetzt, Schalterdatei kaputt
_sl = {k: getattr(SL, k) for k in ("benoetigte_pakete", "verpasste_stunden", "bewerte", "betriebs_zusatz")}
SL.benoetigte_pakete = lambda j: []
SL.verpasste_stunden = lambda *a, **k: []
SL.betriebs_zusatz = lambda o: []
_sig = dict(symbol="BTC", signalstunde="2026-11-03 07:00", einstieg="2026-11-03 08:00", ausstieg="2026-11-04 08:00", vh=0.04, stufe=5,
            p2=0.0, p3=0.0, p5=0.01, zusatz=0, btc=1, kurs=1.0)
SL.bewerte = lambda *a, **k: {"neu": [dict(_sig)], "endgueltig": [], "frische": {"aktiv": 1, "frisch": 1, "veraltet": [], "nicht_im_handel": 0}}
_aus = []
abl_k, abl_g = os.path.join(ORDNER, "abl_k"), os.path.join(ORDNER, "abl_g")
os.makedirs(abl_k)
os.makedirs(abl_g)
erg_k = SL.betrieb_lauf(kaputt, 59000, abl_k, os.path.join(ORDNER, "mod_k"), ausgabe=_aus.append)
erg_g = SL.betrieb_lauf(daten, 59000, abl_g, os.path.join(ORDNER, "mod_g"), ausgabe=_aus.append)
for k, v in _sl.items():
    setattr(SL, k, v)


def _schalter_in(abl):
    c_ = sqlite3.connect(os.path.join(abl, SL.ABLAGE_NAME))
    try:
        return c_.execute("SELECT hebel_schalter FROM signal WHERE symbol='BTC'").fetchone()
    finally:
        c_.close()


art_k, art_g = BG.regel0_meldung_art(erg_k), BG.regel0_meldung_art(erg_g)
pruefe("G8", erg_k.get("schalter_fehler") and "Hebel-Schalter nicht lesbar" in erg_k.get("meldung", "") and art_k == "fehler"
       and _schalter_in(abl_k) == (None,) and not erg_g.get("schalter_fehler") and art_g == "keine" and _schalter_in(abl_g) == (1,)
       and art == ("fehler", "fehler", "nachgeholt"),
       "betrieb_lauf mit KAPUTTER Schalterdatei: Meldung %r -> Art %s (Fehlermail), Signal mit Schalter %s abgelegt · mit GUTER Datei: "
       "Art %s, Schalter %s · Meldungsart-Tabelle %s" % ((erg_k.get("meldung") or "")[:60], art_k, _schalter_in(abl_k), art_g,
                                                         _schalter_in(abl_g), art))

# ---- G9 eine Liste ------------------------------------------------------------------------------------------------------
import agent.ereignisse as ER  # noqa: E402
import ui.bestand_tab as BT  # noqa: E402
import agent.spot_mitnahme as SM  # noqa: E402
pruefe("G9", ER.KERN is KW.KERN and BT.KERN is KW.KERN and SM.KERN is KW.KERN, "ereignisse, bestand_tab, spot_mitnahme lesen kernwerte.KERN")

# ---- G11 die Diagnose rechnet wie die Statusseite (Gegenpruefung: vorher nur der Schalter) -------------------------------
import extract_notebook_diagnose as ED  # noqa: E402
_na = BL.neuaufnahme_und_abgleich
BL.neuaufnahme_und_abgleich = lambda *a, **k: {"kern_luecke": ["SOL ohne REGEL0-Daten"]}
d1 = ED._kern_hebel_luecke([{"symbol": "BTC", "hebel_pruefung_erlaubt": 1}])
BL.neuaufnahme_und_abgleich = lambda *a, **k: (_ for _ in ()).throw(RuntimeError("weg"))
d2 = ED._kern_hebel_luecke([{"symbol": "BTC", "hebel_pruefung_erlaubt": 1}, {"symbol": "ETH", "hebel_pruefung_erlaubt": 0}])
BL.neuaufnahme_und_abgleich = _na
pruefe("G11", d1 == ["SOL ohne REGEL0-Daten"] and d2 == ["ETH", "SOL", "(nur Schalter geprueft)"],
       "Diagnose: ueber betriebslage %s · Rueckfall bei Fehler %s" % (d1, d2))

# ---- G10 keine Produktion -------------------------------------------------------------------------------------------------
_nachher = fingerabdruck()
pruefe("G10", _vorher == _nachher and not os.path.exists(str(db.DB_PATH)),
       "Standard-DB sha256 (.db/-wal) %s · umgebogener Pfad nie angelegt · Wegwerf %s" % (
           "gleich" if _vorher == _nachher else "VERAENDERT", ORDNER))
print("\nG14 am Seiteneffekt: %d von %d bestanden" % (sum(ERG), len(ERG)))
