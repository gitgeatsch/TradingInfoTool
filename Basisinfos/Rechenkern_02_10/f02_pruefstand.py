"""Pruefstand Fassung 0.2 (E-80, Schritt7 §23.19) - nur lesend, keine Aufrufe, keine Mail.

    python Basisinfos/Rechenkern_02_10/f02_pruefstand.py

  P1 N4 bleibt unberuehrt: Fingerabdruck mit dem eingefrorenen Katalog = der in der N4-Ablage
  P2 0.1e-Eingabe unveraendert: fuer 10 eingefrorene N4-Anker liefert trader_eingabe mit 0.1e GENAU die abgelegte Eingabe
  P3 dieselben Zahlen wie gemessen: signal_werte (Betrieb) gegen a2_messung.merkmale_je_symbol an 60 zufaelligen REGEL0-Einstiegen
     (ohne eingestellte Assets - die gibt es im Betrieb nicht)
  P4 anonym: 0.2-Eingabe an denselben 60 Einstiegen ohne Name, Jahr, Kurs
  P5 Laufzeit je Signal (der Betrieb hat 120 s je Signal fuer alle Rollen)
"""
import json
import os
import sqlite3
import sys
import time
from datetime import timedelta

import numpy as np
import pandas as pd

HIER = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.dirname(os.path.dirname(HIER))
sys.path.insert(0, HIER)
sys.path.insert(0, PROJ)
os.chdir(PROJ)
import a2_messung as A2          # noqa: E402
import n4_rueckspiel as N4       # noqa: E402
import agent.regel0_llm as L     # noqa: E402

ok = n = 0


def pruefe(name, gut, info):
    global ok, n
    n += 1; ok += bool(gut)
    print("%-4s %s  %s" % (name, "gleich" if gut else "ABWEICHUNG", info))


K01 = L.lade(os.path.join(PROJ, "Basisinfos", "regel0_llm_0_1e_n4.yaml"))
K02 = L.lade()
c = sqlite3.connect("file:data/_n4/n4_ablage.db?mode=ro", uri=True)
f_alt = c.execute("SELECT v FROM meta WHERE k='fassung'").fetchone()[0]
pruefe("P1", N4.fassung(dict(K01, stimmen=N4.STIMMEN)) == f_alt, "N4-Fingerabdruck %s (abgelegt %s)" % (N4.fassung(dict(K01, stimmen=N4.STIMMEN)), f_alt))
for pos, sym, sst, stufe, ein in c.execute("SELECT pos, symbol, signalstunde, stufe, eingabe FROM eingabe WHERE eingabe IS NOT NULL "
                                           "ORDER BY pos LIMIT 10").fetchall():
    e = L.trader_eingabe({"symbol": sym, "signalstunde": sst, "stufe": stufe}, "data", K01)
    pruefe("P2", json.dumps(e, ensure_ascii=False, sort_keys=True) == ein, "pos %d %s %s" % (pos, sym, sst))

C = {k: A2.con(f) for k, f in (("sk", "stundenkurse.db"), ("ska", "stundenkurse_alle.db"), ("eh", "eingestellt_historie.db"),
                               ("mh", "markpreis_historie.db"), ("ma", "markpreis_alle.db"), ("tm", "terminmarkt_historie.db"),
                               ("rf", "richtung_historie.db"), ("fu", "funding_historie.db"))}
C["btc"] = A2.reihe([C["sk"], C["ska"]], "stundenkurse", "BTC", "close")
eh = {r[0] for r in C["eh"].execute("SELECT DISTINCT symbol FROM stundenkurse")}
sk = {r[0] for r in C["sk"].execute("SELECT DISTINCT symbol FROM stundenkurse")} | {r[0] for r in C["ska"].execute("SELECT DISTINCT symbol FROM stundenkurse")}
E = pd.concat([pd.read_csv("data/_vergleich/kern48jbz_einstiege_%s.csv" % m, sep=";") for m in A2.MENGEN]).drop_duplicates(["symbol", "stunde"])
E = E[E.symbol.isin(sk - eh)].sample(60, random_state=20261007)
PAAR = (("docht", "c_docht", 1.0), ("fall6", "d_fall6", 1.0), ("fall24", "d_fall24", 1.0), ("kapitulation", "b_kapitul", 1.0),
        ("praemie", "a_praemie", 1.0), ("btc24", "e_btc24", 1.0), ("btc168", "e_btc168", 1.0))
abw, dauer, anon = {}, [], []
for r in E.itertuples():
    t = A2.B0 + timedelta(hours=int(r.stunde))
    rr = {"symbol": r.symbol, "signalstunde": t.strftime("%Y-%m-%d %H:%M"), "stufe": 3}
    t0 = time.time()
    w = L.signal_werte(rr, "data", None)
    dauer.append(time.time() - t0)
    a = A2.merkmale_je_symbol(r.symbol, [t], C)[t]
    for mb, ma, _ in PAAR:
        x, y = w.get(mb, np.nan), a[ma]
        gleich = (np.isnan(x) and np.isnan(y)) or (np.isfinite(x) and np.isfinite(y) and abs(x - y) <= 1e-9 * max(1.0, abs(y)))
        if not gleich:
            abw.setdefault(mb, []).append("%s %s: Betrieb %s / A2 %s" % (r.symbol, rr["signalstunde"], x, y))
    e = L.trader_eingabe(dict(rr, kurs=None), "data", K02)
    if e is not None and L.anonym_verletzt(e, dict(rr, bitpanda=r.symbol)):
        anon.append(r.symbol)
for mb, _, _ in PAAR:
    pruefe("P3", mb not in abw, "%-12s %s" % (mb, ("%d Abweichungen, z. B. %s" % (len(abw[mb]), abw[mb][0])) if mb in abw else "60/60 gleich"))
pruefe("P4", not anon, "nicht anonym: %s" % (anon or "keiner"))
pruefe("P5", max(dauer) < 5.0, "signal_werte je Signal: Mittel %.2f s, hoechstens %.2f s" % (np.mean(dauer), max(dauer)))
ein = L.trader_eingabe({"symbol": E.symbol.iloc[0], "signalstunde": (A2.B0 + timedelta(hours=int(E.stunde.iloc[0]))).strftime("%Y-%m-%d %H:%M"),
                        "stufe": 3}, "data", K02)
print("\nBeispiel einer 0.2-Eingabe (%s):\n%s" % (E.symbol.iloc[0], json.dumps(ein, ensure_ascii=False, indent=1)))
print("\n%d von %d gleich" % (ok, n))
