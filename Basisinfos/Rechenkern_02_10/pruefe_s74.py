"""Gegenpruefung S7-4 (03.10.2026, E-46: D1-D4) - Wegwerfordner und Speicherkopien, kein echter Versand, keine Produktion.

A  Mails aus der Ablage (gestellte Signale, Versand abgefangen): wer bekommt eine Mail, wann Korrektur und Erinnerung,
   kein Doppel, ein gescheiterter Versand wird wiederholt, Testwoche, Richtwert, alte Signale nicht mehr
B  Ende zu Ende: echter Stundenlauf (historische Stunde, alle Assets) -> Ablage -> Mails mit dem Hebel-Schalter der Sicherung
C  Rollen-Kette: der alte Hebelweg. Schalter AUS -> Hebel wie bisher (Gegenprobe), Schalter AN -> kein Hebel, SHORT verloren
D  O18: die Migration der Hebel-Schalter laeuft nur EINMAL - ein neues Watchlist-Asset bleibt ohne Zeile, also aus

    python Basisinfos/Rechenkern_02_10/pruefe_s74.py <sicherung.db>
"""
import os
import sqlite3
import sys
import tempfile
import time
from datetime import datetime, timedelta, timezone

import pandas as pd

HIER = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, HIER)
os.chdir(HIER)
sys.stdout.reconfigure(encoding="utf-8")
import agent.regel0_ablage as AB                                   # noqa: E402
import agent.regel0_groesse as G                                   # noqa: E402
import agent.regel0_mail as RM                                     # noqa: E402

SICHERUNG = sys.argv[1]
ergebnis = []


def pruef(name, ok, info=""):
    ergebnis.append(bool(ok))
    print("  %s %s%s" % ("✔" if ok else "⛔", name, (" - " + info) if info else ""), flush=True)


def U(txt):
    return datetime.strptime(txt, "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)


W = dict(G.lade(), testwoche_bis="2026-10-10")
print("A) Mails aus der Ablage")
d = tempfile.mkdtemp()
c = AB.oeffne(d)


def zeile(sym, sh, vorl, stufe=None, schalter=1, **k):
    h = U(sh)
    f = lambda x: x.strftime("%Y-%m-%d %H:%M")
    c.execute("INSERT INTO signal (symbol, signalstunde, einstieg, ausstieg, vh, stufe_vorlaeufig, stufe, p2, p3, p5, hebel_schalter, "
              "bitpanda, zusatz, btc, version, kurs, kurs_markt) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
              (sym, f(h), f(h + timedelta(hours=1)), f(h + timedelta(hours=25)), 0.041, vorl, stufe, 0.001, 0.008, 0.042, schalter,
               k.get("bp", sym), k.get("zusatz", 0), int(sym == "BTC"), "REGEL0.1", 1.234, k.get("markt", "spot")))
    c.commit()


zeile("AAA", "2026-10-05 10:00", 3)                       # Mail
zeile("BBB", "2026-10-05 10:00", 5)                       # Mail, spaeter Korrektur auf 3
zeile("CCC", "2026-10-05 10:00", 3, schalter=0)           # Schalter aus -> keine Mail
zeile("DDD", "2026-10-05 10:00", 3, schalter=None)        # Schalter unbekannt -> keine Mail
zeile("EEE", "2026-10-05 10:00", 0)                       # Stufe 0 -> keine Mail (noch)
zeile("FFF", "2026-10-05 05:00", 3)                       # Einstieg zu lange vorbei -> keine Mail
zeile("CC", "2026-10-05 10:00", 3, bp="CANTON", zusatz=1, markt="futures")
post = []
jetzt = U("2026-10-05 11:05")
z1 = RM.versende(d, lambda b, t: post.append((b, t)) or True, jetzt, W)
an = sorted(b.split()[4] for b, _t in post)
pruef("Signalmail nur bei Schalter an, Stufe > 0, frisch", an == ["AAA", "BBB", "CANTON"], "%s · %s" % (an, z1))
t_aaa = [t for b, t in post if " AAA " in b][0]
b_aaa = [b for b, t in post if " AAA " in b][0]
pruef("Testwoche im Betreff und im Text", b_aaa.startswith("[TESTWOCHE]") and "TESTWOCHE bis 2026-10-10" in t_aaa, b_aaa)
pruef("Einstieg = Schluss der Folgestunde (05.10. 12:00 UTC), Ausstieg 24 h danach (06.10. 12:00 UTC)",
      "05.10. 12:00 UTC" in t_aaa and "06.10. 12:00 UTC" in t_aaa)
pruef("vorlaeufige Stufe vermerkt, Bitpanda-Hinweis (D2), Einsatz 500 EUR bei 3x",
      "VORLAEUFIG" in t_aaa and "Bitpanda" in t_aaa and "500 EUR" in t_aaa)
t_cc = [t for b, t in post if "CANTON" in b][0]
pruef("Zusatz-Asset: Bitpanda-Name, Kurs aus Futures, bewertet nicht trainiert",
      "CANTON (Binance CC)" in t_cc and "Kurs aus Futures" in t_cc and "nicht trainiert" in t_cc)
post.clear()
z2 = RM.versende(d, lambda b, t: post.append((b, t)) or True, jetzt, W)
pruef("zweiter Durchgang: keine Doppel", not post, str(z2))

c.execute("UPDATE signal SET stufe=3 WHERE symbol IN ('AAA','BBB','CC')"); c.execute("UPDATE signal SET stufe=3 WHERE symbol='EEE'")
c.commit()
jetzt = U("2026-10-05 12:05")
z3 = RM.versende(d, lambda b, t: post.append((b, t)) or True, jetzt, W)
k = [b for b, _t in post]
pruef("Korrektur nur fuer BBB (5x -> 3x), EEE bekommt jetzt die Signalmail (Stufe erst endgueltig > 0)",
      any("KORREKTUR BBB" in b and "3x statt 5x" in b for b in k) and any(" EEE 3x" in b for b in k) and len(k) == 2, "%s" % k)
e_txt = [t for b, t in post if " EEE " in b][0]
pruef("die spaete Signalmail nennt die Stufe endgueltig", "(endgueltig)" in e_txt)
post.clear()

fail = []
zeile("GGG", "2026-10-05 11:00", 2)
z4 = RM.versende(d, lambda b, t: fail.append(b) and False, U("2026-10-05 12:10"), W)
z5 = RM.versende(d, lambda b, t: post.append((b, t)) or True, U("2026-10-05 12:20"), W)
pruef("gescheiterter Versand wird NICHT vermerkt und beim naechsten Mal wiederholt", z4["fehlgeschlagen"] == 1 and any(" GGG " in b for b, _t in post),
      "%s / %s" % (z4, z5))
post.clear()

for i, s_ in enumerate(("H1", "H2", "H3")):
    zeile(s_, "2026-10-05 11:00", 3)
RM.versende(d, lambda b, t: post.append((b, t)) or True, U("2026-10-05 12:30"), W)
richt = [t for b, t in post if "Richtwert erreicht" in t]
pruef("ab dem 5. offenen Trade: Vermerk Richtwert, Signal kommt trotzdem", len(post) == 3 and len(richt) >= 1, "%d Mails, %d mit Vermerk" % (len(post), len(richt)))
post.clear()

z6 = RM.versende(d, lambda b, t: post.append((b, t)) or True, U("2026-10-06 12:05"), W)
er = sorted(b.split()[4].rstrip(":") for b, _t in post if "AUSSTIEG" in b)
pruef("Erinnerung nach 24 h fuer die gemailten Trades (AAA, BBB, CANTON, EEE)", er == ["AAA", "BBB", "CANTON", "EEE"], "%s · %s" % (er, z6))
post.clear()
RM.versende(d, lambda b, t: post.append((b, t)) or True, U("2026-10-06 12:15"), W)
pruef("keine doppelte Erinnerung", not [b for b, _t in post if "AUSSTIEG" in b and b.split()[4].rstrip(":") in er])
post.clear()
RM.versende(d, lambda b, t: post.append((b, t)) or True, U("2026-10-07 09:00"), W)
pruef("eine Erinnerung, die laenger als 6 h ueberfaellig ist, entfaellt", not [b for b, _t in post if "AUSSTIEG" in b])
b_nach, _t = RM.signal_mail(dict(symbol="X", bitpanda="X", signalstunde="2026-10-12 10:00", einstieg="2026-10-12 11:00",
                                 ausstieg="2026-10-13 11:00", vh=0.04, p2=0.0, p3=0.0, p5=0.0), 3, False, G.rechne(3, 0, W), W, U("2026-10-12 11:05"))
pruef("nach der Testwoche kein TESTWOCHE-Vermerk", not b_nach.startswith("[TESTWOCHE]"), b_nach)
c.close()

print("B) Ende zu Ende: Stundenlauf -> Ablage -> Mails")
import agent.regel0_rechnung as RK                                 # noqa: E402
import agent.regel0_stundenlauf as SL                              # noqa: E402
B0 = pd.Timestamp(2020, 1, 1)
T = int((pd.Timestamp("2026-08-12 12:00") - B0) / pd.Timedelta(hours=1))   # ETH-Einstieg, Schalter an (Sicherung NB)
abl, mod = tempfile.mkdtemp(), tempfile.mkdtemp()
# der Hebel-Schalter kommt aus der Sicherung des Notebooks (nur gelesen, ueber eine Kopie im Wegwerfordner)
dat = tempfile.mkdtemp()
alt_schalter = SL._hebel_schalter
SL._hebel_schalter = lambda ordner: alt_schalter(os.path.dirname(SICHERUNG)) if os.path.basename(SICHERUNG) == "tradinginfotool.db" else \
    {str(r[0]).upper(): bool(r[1]) for r in sqlite3.connect("file:%s?mode=ro" % SICHERUNG.replace("\\", "/"), uri=True).execute(
        "SELECT symbol, hebel_pruefung_erlaubt FROM asset_hebel_settings")}
t0 = time.time()
e1 = SL.betrieb_lauf(RK.DATEN_VORGABE, T, abl, mod, ausgabe=lambda s: None)
post = []
zm = RM.versende(abl, lambda b, t: post.append((b, t)) or True, U(RK._stunde_txt(T)) + timedelta(minutes=10), W)
cs = sqlite3.connect(os.path.join(abl, "regel0_signale.db"))
z_ = cs.execute("SELECT symbol, bitpanda, stufe_vorlaeufig, hebel_schalter, kurs, mail_signal_am FROM signal WHERE einstieg=?", (RK._stunde_txt(T),)).fetchall()
cs.close()
soll = sorted(r[1] for r in z_ if r[3] == 1 and (r[2] or 0) > 0)
ist = sorted(b.split()[4] for b, _t in post if "Hebel LONG" in b)
pruef("Mails genau fuer die Signale mit Schalter an und Stufe > 0 (darunter ETH), mit Kurs", ist == soll and "ETH" in ist and all(r[4] for r in z_),
      "Signale %s · Mails %s · %.0f s" % ([(r[1], r[2], r[3]) for r in z_], ist, time.time() - t0))
print("    Beispiel:\n" + "\n".join("      " + x for x in (post[0][1].splitlines() if post else ["(keine Mail - kein Signal mit Schalter an)"])))
SL._hebel_schalter = alt_schalter

print("C) Rollen-Kette: der alte Hebelweg (Suite-Paket B1: echte Kette im Trockenlauf mit gestelltem Hebel-Lauf)")
import pruefe_pakete as PP                                          # noqa: E402
alt = G.alter_hebelweg_aus


def b1(an):
    alt_b1 = PP.B1_ALTER_HEBELWEG_AUS
    PP.B1_ALTER_HEBELWEG_AUS = an          # B1 setzt den Schalter selbst - hier fuer diese Probe
    PP._ERGEBNISSE.clear()
    try:
        PP.paket_b1()
    finally:
        PP.B1_ALTER_HEBELWEG_AUS = alt_b1
    return {n_: ok_ for _p, n_, ok_, _d in PP._ERGEBNISSE}


aus_, an_ = b1(False), b1(True)
pruef("Gegenprobe: Schalter AUS -> der Hebel-Lauf erzeugt wie bisher eine Hebelmail", aus_.get("ein Hebel-Lauf ebenfalls") is True,
      "%d von %d Pruefungen in B1 gruen" % (sum(aus_.values()), len(aus_)))
pruef("Schalter AN -> derselbe Lauf erzeugt KEINE Hebelmail mehr", an_.get("ein Hebel-Lauf ebenfalls") is False,
      "in B1 anders als mit Schalter aus: %s" % sorted(k for k in aus_ if aus_.get(k) != an_.get(k)))

print("D) O18: Migration der Hebel-Schalter nur einmal")
import database.db as DBM                                          # noqa: E402
import config as CFG                                               # noqa: E402
q = sqlite3.connect("file:%s?mode=ro" % SICHERUNG.replace("\\", "/"), uri=True)
m = sqlite3.connect(":memory:"); q.backup(m); q.close(); m.row_factory = sqlite3.Row
m.execute("DELETE FROM meta WHERE key=?", (DBM.MARKE_HEBEL_SCHALTER,)); m.commit()
alt_wl = CFG.get_watchlist


class _A:
    def __init__(self, s):
        self.symbol, self.assetklasse, self.ist_cash_aequivalent = s, "krypto", False


wl = [_A(r["symbol"]) for r in m.execute("SELECT symbol FROM asset_hebel_settings")]
try:
    CFG.get_watchlist = lambda: wl
    erst = DBM._migrate_hebel_schalter_geradeziehen(m)
    marke = DBM.get_meta_wert(m, DBM.MARKE_HEBEL_SCHALTER)
    wl.append(_A("NEUCOIN"))
    zweit = DBM._migrate_hebel_schalter_geradeziehen(m)
    zeile_neu = m.execute("SELECT * FROM asset_hebel_settings WHERE symbol='NEUCOIN'").fetchone()
    erlaubt = DBM.get_hebel_pruefung_erlaubt(m, "NEUCOIN")
    m.execute("DELETE FROM meta WHERE key=?", (DBM.MARKE_HEBEL_SCHALTER,)); m.commit()
    gegen = DBM._migrate_hebel_schalter_geradeziehen(m)
finally:
    CFG.get_watchlist = alt_wl
pruef("erster Lauf setzt die Marke, ein danach neues Watchlist-Asset bleibt ohne Zeile = AUS", bool(marke) and zweit == [] and zeile_neu is None and erlaubt is False,
      "Marke %s · zweiter Lauf %s · NEUCOIN Zeile %s, erlaubt %s" % (marke, zweit, zeile_neu, erlaubt))
pruef("Gegenprobe: ohne Marke haette die Migration NEUCOIN still eingeschaltet (so war es bisher)", gegen == ["NEUCOIN"], str(gegen))
print("SCHLUSS: %s (%d von %d)" % ("✔ bestanden" if all(ergebnis) else "⛔ NICHT bestanden", sum(ergebnis), len(ergebnis)))
