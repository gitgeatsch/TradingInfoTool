"""Gegenprobe Sofortliste S-1 bis S-5 (10.10.2026) - eigener Rechenweg, Wegwerf-DB, kein Netz, keine Mail.

    python Basisinfos/Rechenkern_02_10/sofortliste_gegenprobe.py

  G1 compute_cost_basis_view gegen eine EIGENE Formel an 2.000 Zufallsbestaenden: ohne `menge` = alte Rechnung auf `quantity`,
     mit `menge` = dieselbe Rechnung auf frei + gestakt (manuell / berechnet / unbekannt, tracked groesser/kleiner)
  G2 alle Aufrufer ausser dem Portfolio rufen ohne `menge` (Analysten unveraendert) - aus dem Quelltext abgeleitet, nicht aufgezaehlt
  G3 PortfolioView an 25 Zufallsbestaenden: jede Zeile = (frei + gestakt) x Preis, Gesamtwert = Summe frei + Summe gestakt + Fiat
  G4 die echte config.yaml faehrt den NEUEN Abgleich (S-2 schuetzt also im Betrieb); wer sonst `staked_quantity` schreibt
  G5 Excel-Rundweg an Zufallsdaten: Import-Bestaende kommen exakt zurueck, Abgleich-Bestaende bleiben unberuehrt
"""
import ast
import glob
import hashlib
import os
import random
import sqlite3
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

WURZEL = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, WURZEL)
os.chdir(WURZEL)
STD = os.path.join("data", "tradinginfotool.db")
vorher = hashlib.sha256(open(STD, "rb").read()).hexdigest() if os.path.exists(STD) else None

import config  # noqa: E402
import database.db as DB  # noqa: E402
from database.models import Holding, PriceSnapshot  # noqa: E402
import importer.bitpanda_avg_cost as AC  # noqa: E402
import importer.excel_import as XI  # noqa: E402

ok = n = 0
rnd = random.Random(20261010)


def pruefe(name, gut, info=""):
    global ok, n
    n += 1; ok += bool(gut)
    print("%-3s %s  %s" % (name, "gleich" if gut else "ABWEICHUNG", info), flush=True)


def eigen(q, avg, manual, tracked, preis):
    eff = manual if manual is not None else avg
    if eff is None:
        bek, unb = 0.0, q
    elif manual is not None:
        bek, unb = q, 0.0
    else:
        bek = min(q, tracked or 0.0); unb = max(0.0, q - bek)
    basis = bek * eff if eff is not None and bek > 0 else None
    wert = q * preis
    pl = ((bek * preis - basis) / basis * 100) if basis else None
    return bek, unb, wert, pl


fx = 0
for _ in range(2000):
    q, st = rnd.choice([0.0, rnd.uniform(0, 100)]), rnd.choice([0.0, rnd.uniform(0, 100)])
    avg = rnd.choice([None, rnd.uniform(0.1, 10)])
    manual = rnd.choice([None, None, rnd.uniform(0.1, 10)])
    tracked = rnd.uniform(0, 200)
    preis = rnd.uniform(0.01, 20)
    h = Holding(symbol="X", quantity=q, updated_at="x", source="bitpanda_sync", staked_quantity=st,
                avg_buy_price_eur=avg, avg_buy_price_tracked_qty=tracked, avg_buy_price_manual_eur=manual)
    for menge, qq in ((None, q), (q + st, q + st)):
        v = AC.compute_cost_basis_view(h, preis, menge=menge)
        e = eigen(qq, avg, manual, tracked, preis)
        gl = (abs(v.known_quantity - e[0]) < 1e-9 and abs(v.unknown_quantity - e[1]) < 1e-9 and abs(v.current_value_eur - e[2]) < 1e-9
              and ((v.pl_pct is None) == (e[3] is None)) and (v.pl_pct is None or abs(v.pl_pct - e[3]) < 1e-6))
        fx += not gl
pruefe("G1", fx == 0, "4.000 Rechnungen (2.000 Bestaende x mit/ohne menge), Abweichungen %d" % fx)

aufrufer = {}
for p in glob.glob("**/*.py", recursive=True):
    if p.startswith(("Basisinfos", ".claude")) or "pruefe_pakete" in p:
        continue
    try:
        baum = ast.parse(open(p, encoding="utf-8").read())
    except Exception:                                                          # noqa: BLE001
        continue
    for k in ast.walk(baum):
        if isinstance(k, ast.Call) and getattr(k.func, "id", getattr(k.func, "attr", None)) == "compute_cost_basis_view":
            aufrufer.setdefault(p.replace("\\", "/"), []).append(any(kw.arg == "menge" for kw in k.keywords))
mit = sorted(p for p, v in aufrufer.items() if any(v))
ohne = sorted(p for p, v in aufrufer.items() if not any(v))
pruefe("G2", mit == ["ui/portfolio.py"] and len(ohne) >= 4, "mit menge: %s · ohne (unveraendert): %s" % (mit, ohne))

tmp = tempfile.mkdtemp(prefix="sofort_gp_")
pfad = os.path.join(tmp, "w.db")
c = sqlite3.connect(pfad); c.row_factory = sqlite3.Row
DB.init_db(c)
wl = [a for a in config.get_watchlist() if a.assetklasse == "krypto"][:25]
jetzt = datetime.now(timezone.utc).isoformat()
soll = {}
sum_frei = sum_st = 0.0
for a in wl:
    q, st, p = rnd.choice([0.0, rnd.uniform(0.1, 50)]), rnd.choice([0.0, rnd.uniform(0.1, 50)]), rnd.uniform(0.1, 100)
    if q == 0 and st == 0:
        st = 1.0
    DB.upsert_holding(c, a.symbol, q, source="bitpanda_sync"); DB.update_holding_staked_quantity(c, a.symbol, st)
    DB.insert_price_snapshot(c, PriceSnapshot(symbol=a.symbol, coingecko_id=a.coingecko_id, price_usd=p, price_eur=p, market_cap_usd=None,
                                              volume_24h_usd=None, change_24h_pct=None, fetched_at=jetzt))
    soll[a.symbol] = (q + st) * p
    sum_frei += q * p; sum_st += st * p
c.commit(); c.close()


def fab():
    x = sqlite3.connect(pfad); x.row_factory = sqlite3.Row
    return x


import tkinter as tk  # noqa: E402
root = tk.Tk(); root.withdraw()
from ui.portfolio import PortfolioView  # noqa: E402
pv = PortfolioView(root, fab, config.get_watchlist())
pv.refresh() if hasattr(pv, "refresh") else None
fz = 0
for iid in pv.tree.get_children():
    if iid in soll:
        wert = float(str(pv.tree.item(iid, "values")[5]).replace(",", ""))
        fz += abs(wert - soll[iid]) > 0.006
gtxt = pv.total_label.cget("text")
gesamt = float(gtxt.split("Gesamtwert:")[1].split("EUR")[0].replace(",", "").strip())
x = fab(); fiat = DB.get_cash_reserve_fiat_eur(x) if hasattr(DB, "get_cash_reserve_fiat_eur") else 0.0; x.close()
root.destroy()
pruefe("G3", fz == 0 and abs(gesamt - (sum_frei + sum_st + (fiat or 0.0))) < 0.05,
       "%d Zeilen geprueft, Abweichungen %d · Gesamt %.2f gegen eigen %.2f" % (len(soll), fz, gesamt, sum_frei + sum_st + (fiat or 0.0)))

schreiber = sorted({p.replace("\\", "/") for p in glob.glob("**/*.py", recursive=True)
                    if not p.startswith(("Basisinfos", ".claude")) and "pruefe_" not in p and "teste_" not in p
                    and "update_holding_staked_quantity(" in open(p, encoding="utf-8", errors="ignore").read()})
pruefe("G4", config.bitpanda_bestand_quelle() == "neu", "echte config: bestand_quelle = %r · Schreiber von staked_quantity: %s"
       % (config.bitpanda_bestand_quelle(), schreiber))

c = fab()
c.execute("UPDATE holdings SET source='import'")
werte = {r["symbol"]: r["quantity"] for r in c.execute("SELECT symbol, quantity FROM holdings")}
c.commit()
xp = Path(os.path.join(tmp, "e.xlsx"))
XI.export_holdings(c, xp)
schutz = wl[0].symbol
c.execute("UPDATE holdings SET source='bitpanda_sync', quantity=? WHERE symbol=?", (werte[schutz] + 3.0, schutz))
c.commit()
XI.import_holdings(c, xp)
zur = {r["symbol"]: r["quantity"] for r in c.execute("SELECT symbol, quantity FROM holdings")}
c.close()
fr = sum(abs(zur[s] - werte[s]) > 1e-12 for s in werte if s != schutz)
pruefe("G5", fr == 0 and abs(zur[schutz] - (werte[schutz] + 3.0)) < 1e-12,
       "%d Import-Bestaende exakt zurueck (Abweichungen %d) · Abgleich-Bestand %s unberuehrt" % (len(werte) - 1, fr, schutz))
nachher = hashlib.sha256(open(STD, "rb").read()).hexdigest() if os.path.exists(STD) else None
print("Standard-DB %s" % ("unveraendert" if vorher == nachher else "VERAENDERT"))
print("\n%d von %d gleich" % (ok, n))
