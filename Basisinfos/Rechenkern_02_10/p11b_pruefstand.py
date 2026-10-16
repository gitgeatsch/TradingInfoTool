"""P11b Hebelpositionen als Buch je Symbol (16.10.2026) - Pruefstand am SEITENEFFEKT an Wegwerf-Kopien der NB-Sicherung, kein Netz.

    python Basisinfos/Rechenkern_02_10/p11b_pruefstand.py <nb_bitpanda_buchungen_voll_*.json> <tradinginfotool_*.db.gz>
        > Basisinfos/Rechenkern_02_10/p11b_pruefstand.txt

Der Abruf wird aus der JSON-Datei gestellt (dieselben Vorgaenge wie live, gefiltert nach ``seit``).

  B1  Umstellung: 191 alte Zeilen gesichert (Tabelle hebel_positions_alt_bis_16_10, inhaltsgleich), hebel_positions = 38 Lebenszyklen
      (37 geschlossen davon 7 liquidiert, 1 offen); Werte des offenen = unabhaengige Nachrechnung der Voranalyse (Wallet-Stand)
  B2  Wallet-Abgleich (P11) danach OK - Menge und Kredit stimmen
  B3  Hebelfuehrung (P11c) ohne Korrektur-Hinweis, BTC dieselben Zahlen wie mit P11c (Menge, Kredit, Hebel, Liquidation)
  B4  inkrementell = auf einmal: Erstlauf bis 01.10., dann der Rest -> dieselben Zeilen wie ein einziger Lauf
  B5  idempotent: ein zweiter Lauf ohne neue Vorgaenge aendert nichts
  B6  unvollstaendige erste Historie -> KEINE Umstellung, alte Tabelle unberuehrt, der alte Weg laeuft (sync_hebel_positions)
  B7  sync_hebel_positions (der Pfad des Jobs) liefert das Ergebnisobjekt fuer die Logzeile; der Fehler NACH der Umstellung geht
      an den Aufrufer (kein Rueckfall auf den alten Weg)
  B8  Leser: Liquidationspreis-Rechnung des Jobs, Statusseite, Deckel, Abgleich-Frische, Watchlist-Ergaenzung, Diagnose laufen
  B9  Desktop-Produktion, Sicherung und JSON unveraendert
"""
import gzip
import hashlib
import json
import os
import shutil
import sqlite3
import sys
import tempfile
from datetime import datetime, timezone

WURZEL = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(WURZEL)
sys.path.insert(0, WURZEL)
sys.stdout.reconfigure(encoding="utf-8")
import wegwerf  # noqa: E402,F401

import agent.hebel_wallet_abgleich as HW  # noqa: E402
import agent.hebelfuehrung as HF  # noqa: E402
import importer.bitpanda_margin_positions as BMP  # noqa: E402
import importer.hebel_buch as HB  # noqa: E402
from database import db  # noqa: E402

ERG = []


def pruefe(k, ok, text):
    ERG.append(bool(ok))
    print("%-4s %-9s %s" % (k, "bestanden" if ok else "FEHLER", text))


def summe(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


JS, GZ = sys.argv[1], sys.argv[2]
VOR = {"prod": summe(db.DB_PATH) if os.path.exists(db.DB_PATH) else None, "gz": summe(GZ), "js": summe(JS)}
OPS = json.load(open(JS, encoding="utf-8"))["vorgaenge"]
T = tempfile.mkdtemp(prefix="p11b_")
BASIS = os.path.join(T, "basis.db")
with gzip.open(GZ, "rb") as f, open(BASIS, "wb") as g:
    shutil.copyfileobj(f, g, 1 << 24)
JETZT = datetime(2026, 10, 16, 6, 0, tzinfo=timezone.utc)


def kopie(n):
    p = os.path.join(T, n + ".db")
    shutil.copy(BASIS, p)
    c = sqlite3.connect(p)
    c.row_factory = sqlite3.Row
    return c


def zeit(o):
    return min(t["credited_at"] for t in o["transactions"])


def hole_aus(ops, vollstaendig=True):
    def hole(api_key, seit=None):
        return [o for o in ops if not seit or zeit(o) >= seit], vollstaendig
    return hole


def zeilen(c):
    return sorted(tuple(r[k] for k in ("symbol", "status", "eroeffnet_am", "geschlossen_am", "positionsmenge", "kreditbetrag_eur",
                                       "positionswert_eur", "hebel_effektiv"))
                  for r in c.execute("SELECT * FROM hebel_positions"))


# ══ B1 Umstellung ══════════════════════════════════════════════════════════════════════════════════════════════════════════
c = kopie("b1")
alt_n = c.execute("SELECT COUNT(*) FROM hebel_positions").fetchone()[0]
alt_summe = sorted(tuple(r) for r in c.execute("SELECT * FROM hebel_positions"))
e1 = HB.sync(c, "x", hole=hole_aus(OPS))
gesichert = sorted(tuple(r) for r in c.execute("SELECT * FROM %s" % HB.ALT))
st = dict(c.execute("SELECT status, COUNT(*) FROM hebel_positions GROUP BY status").fetchall())
btc = c.execute("SELECT * FROM hebel_positions WHERE status='offen'").fetchall()
b = btc[0] if len(btc) == 1 else None
liq = sorted((r["symbol"], r["geschlossen_am"][:10]) for r in c.execute("SELECT * FROM hebel_positions WHERE status='liquidiert'"))
SOLL_LIQ = sorted([("MORPHO", "2025-10-10"), ("AVAX", "2025-10-10"), ("TAO", "2025-10-10"), ("LINK", "2025-10-11"), ("TAO", "2025-10-22"),
                   ("SUI", "2025-11-03"), ("TAO", "2025-11-21")])
ok1 = (e1["umgestellt"] and e1["gesichert"] == alt_n == 191 and gesichert == alt_summe and st.get("geschlossen") == 30
       and st.get("liquidiert") == 7 and st.get("offen") == 1 and b is not None and b["symbol"] == "BTC"
       and abs(b["positionsmenge"] - 0.01141097) < 1e-12 and abs(b["kreditbetrag_eur"] - 560.0) < 1e-6
       and abs(b["positionswert_eur"] / b["positionsmenge"] - 73613.33) < 0.01 and liq == SOLL_LIQ
       and b["eroeffnet_am"] == "2026-10-09T04:38:53+00:00")
pruefe("B1", ok1, "gesichert %d von %d (inhaltsgleich %s) · neu %s · BTC Menge %.8g Kredit %.2f Einstand %.2f Hebel %.3f seit %s · liquidiert %s" % (
    e1["gesichert"], alt_n, gesichert == alt_summe, st, b["positionsmenge"], b["kreditbetrag_eur"], b["positionswert_eur"] / b["positionsmenge"],
    b["hebel_effektiv"], b["eroeffnet_am"], liq == SOLL_LIQ))

# ══ B2 Wallet-Abgleich ════════════════════════════════════════════════════════════════════════════════════════════════════
w = HW.pruefe(c)
pruefe("B2", w["ok"] and not w["abweichungen"], "Wallet-Abgleich nach der Umstellung: %s" % HW.zeile(w))

# ══ B3 Hebelfuehrung ══════════════════════════════════════════════════════════════════════════════════════════════════════
t3 = HF.lade(c, jetzt=JETZT, nahe_grenze=0.15)
t3a = HF.lade(c, jetzt=JETZT, nahe_grenze=0.15, wallet=False)
x = t3[0] if len(t3) == 1 else {}
ok3 = (len(t3) == 1 and x["symbol"] == "BTC" and "wallet_hinweis" not in x and abs(x["menge"] - 0.01141097) < 1e-12
       and abs(x["kredit_eur"] - 560.0) < 1e-6 and abs(x["hebel"] - 3.0) < 1e-3 and abs(x["liquidation_eur"] - t3a[0]["liquidation_eur"]) < 1e-9
       and HF.laut_bitpanda_geschlossen(c) == [])
pruefe("B3", ok3, "Fuehrung: %s · Hebel %.4f · Liquidation %.2f (ohne Wallet-Korrektur gleich %s) · kein Hinweis %s" % (
    [t["symbol"] + " " + t["empfehlung"] for t in t3], x.get("hebel", 0), x.get("liquidation_eur", 0),
    abs(x.get("liquidation_eur", 0) - t3a[0]["liquidation_eur"]) < 1e-9, "wallet_hinweis" not in x))
z_einmal = zeilen(c)
c.close()

# ══ B4 inkrementell = auf einmal ══════════════════════════════════════════════════════════════════════════════════════════
c = kopie("b4")
HB.sync(c, "x", hole=hole_aus([o for o in OPS if zeit(o) < "2026-10-01"]))
e4 = HB.sync(c, "x", hole=hole_aus(OPS))
pruefe("B4", zeilen(c) == z_einmal and not e4["umgestellt"], "Erstlauf bis 01.10., dann der Rest: Zeilen gleich %s (%d) · zweiter Lauf ohne Umstellung %s" % (
    zeilen(c) == z_einmal, len(z_einmal), not e4["umgestellt"]))

# ══ B5 idempotent ═════════════════════════════════════════════════════════════════════════════════════════════════════════
vor5 = zeilen(c)
n5 = c.execute("SELECT COUNT(*) FROM %s" % HB.TABELLE).fetchone()[0]
e5 = HB.sync(c, "x", hole=hole_aus(OPS))
pruefe("B5", zeilen(c) == vor5 and c.execute("SELECT COUNT(*) FROM %s" % HB.TABELLE).fetchone()[0] == n5 and e5["neu_im_buch"] == 0,
       "dritter Lauf: Zeilen gleich, Buch %d Vorgaenge, neu %d" % (n5, e5["neu_im_buch"]))
c.close()

# ══ B6 unvollstaendige erste Historie ══════════════════════════════════════════════════════════════════════════════════════
c = kopie("b6")
vor6 = sorted(tuple(r) for r in c.execute("SELECT * FROM hebel_positions"))
e6 = HB.sync(c, "x", hole=hole_aus(OPS[: len(OPS) // 2], vollstaendig=False))
alt_weg = []
_orig = BMP._sync_alt
BMP._sync_alt = lambda conn, k: alt_weg.append(1) or BMP.HebelPositionSyncResult()
_orig_sync = HB.sync
HB.sync = lambda conn, k, hole=None: _orig_sync(conn, k, hole=hole_aus(OPS[: len(OPS) // 2], vollstaendig=False))
try:
    BMP.sync_hebel_positions(c, "x")
finally:
    HB.sync = _orig_sync
    BMP._sync_alt = _orig
nach6 = sorted(tuple(r) for r in c.execute("SELECT * FROM hebel_positions"))
pruefe("B6", not e6["umgestellt"] and vor6 == nach6 and not HB.umgestellt(c) and alt_weg == [1]
       and not c.execute("SELECT 1 FROM sqlite_master WHERE name=?", (HB.ALT,)).fetchone(),
       "nicht umgestellt %s · alte Tabelle unberuehrt %s · keine Sicherungstabelle %s · alter Weg gelaufen %s" % (
           not e6["umgestellt"], vor6 == nach6, not c.execute("SELECT 1 FROM sqlite_master WHERE name=?", (HB.ALT,)).fetchone(), alt_weg == [1]))
c.close()

# ══ B7 Pfad des Jobs ═══════════════════════════════════════════════════════════════════════════════════════════════════════
c = kopie("b7")
HB.sync, _s = (lambda conn, k, hole=None: _orig_sync(conn, k, hole=hole_aus(OPS))), HB.sync
try:
    r7 = BMP.sync_hebel_positions(c, "x")
    fehler7 = None
    HB.sync = lambda conn, k, hole=None: (_ for _ in ()).throw(ConnectionError("gestellt"))
    alt7 = []
    BMP._sync_alt, _o7 = (lambda conn, k: alt7.append(1)), BMP._sync_alt
    try:
        BMP.sync_hebel_positions(c, "x")
    except ConnectionError as exc:
        fehler7 = str(exc)
    finally:
        BMP._sync_alt = _o7
finally:
    HB.sync = _orig_sync
pruefe("B7", isinstance(r7, BMP.HebelPositionSyncResult) and r7.total_transactions_fetched == len(OPS) and r7.positionen_aktualisiert
       and fehler7 == "gestellt" and alt7 == [],
       "Ergebnis fuer die Logzeile: %d geladen, %s, %d neu geschlossen · Fehler nach der Umstellung an den Aufrufer %s, kein alter Weg %s" % (
           r7.total_transactions_fetched, r7.positionen_aktualisiert, r7.neu_geschlossen, fehler7 == "gestellt", alt7 == []))

# ══ B8 Leser ═══════════════════════════════════════════════════════════════════════════════════════════════════════════════
import scheduler.background as BG  # noqa: E402
import agent.betriebslage as BL  # noqa: E402
import agent.hebel_aggregat as HA  # noqa: E402
from agent import hebel_abgleich as HAB  # noqa: E402

fehl8 = []
try:
    BG._refresh_hebel_position_liquidation_prices(c)
    lq = c.execute("SELECT liquidationspreis_geschaetzt_eur FROM hebel_positions WHERE status='offen'").fetchone()[0]
except Exception as exc:                                         # noqa: BLE001
    fehl8.append("Liquidationspreis %s" % exc)
    lq = None
for name, f in (("Statusseite", lambda: BL.hebel_fuehrung_jetzt(c)), ("Positionen", lambda: BL.hebel_positionen(c) if hasattr(BL, "hebel_positionen") else None),
                ("Deckel", lambda: HA.aggregat(c, kapital_eur=10000.0, anteil=0.2, jetzt=JETZT)),
                ("Abgleich-Frische", lambda: HAB.positionsstand_zeile(HAB.frische(c))),
                ("Diagnose-Abfrage", lambda: c.execute("SELECT * FROM hebel_positions ORDER BY eroeffnet_am ASC").fetchall()),
                ("Backward-Tracking-Abfrage", lambda: c.execute("SELECT symbol FROM hebel_positions WHERE status = 'offen'").fetchall())):
    try:
        f()
    except Exception as exc:                                     # noqa: BLE001
        fehl8.append("%s: %s: %s" % (name, type(exc).__name__, exc))
sb = BL.hebel_fuehrung_jetzt(c)
pruefe("B8", not fehl8 and lq and abs(lq - t3a[0]["liquidation_eur"]) / lq < 0.01 and [p["symbol"] for p in sb] == ["BTC"],
       "Liquidationspreis des Jobs %.2f (Fuehrung %.2f) · Statusseite %s · Fehler %s" % (lq or 0, t3a[0]["liquidation_eur"],
                                                                                       [p["symbol"] + " " + str(p["empfehlung"]) for p in sb], fehl8 or "keine"))
c.close()

# ══ B9 unveraendert ═══════════════════════════════════════════════════════════════════════════════════════════════════════
NACH = {"prod": summe(db.DB_PATH) if os.path.exists(db.DB_PATH) else None, "gz": summe(GZ), "js": summe(JS)}
pruefe("B9", NACH == VOR, "Desktop-Prod %s · Sicherung %s · JSON %s unveraendert" % tuple(NACH[k] == VOR[k] for k in ("prod", "gz", "js")))
wegwerf.aufraeumen(T)
print("\n%d von %d bestanden" % (sum(ERG), len(ERG)))
