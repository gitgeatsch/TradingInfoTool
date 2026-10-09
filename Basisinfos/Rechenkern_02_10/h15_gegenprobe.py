"""H15 Gegenprobe (09.10.2026) - eigener Rechenweg zu Prüfstand und Bau, nur lesend (Wegwerf-Pfade, keine Mail).

    python Basisinfos/Rechenkern_02_10/h15_gegenprobe.py

  G1 Einstand und Abstand der BTC-Position mit eigener Rechnung (Positionswert / Menge; (Kurs - Liquidation) / Kurs)
  G2 Warnstufen: zweite Umsetzung (Intervalle) ueber 0 .. 30 % in 0,1-Pp-Schritten = nahe_stufe
  G3 Mailsperre: andere Stufe -> anderer Schluessel, gleiche Stufe gleicher Tag -> gleicher, anderer Tag -> anderer
  G4 alter Aufruf der Rollen-Kette (HF.lade(conn, symbole=...)) passt weiter und warnt mit der Vorgabe 15 %
  G5 Schalter: falsche Werte (1,5 / 'ja') brechen beim Laden ab
  G6 Teilexport: der Abschnitt HEBELFUEHRUNG ist syntaktisch im Exportskript und liest nur job_laeufe
"""
import io
import os
import re
import sqlite3
import sys
import tempfile

WURZEL = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, WURZEL)
os.chdir(WURZEL)
import agent.hebelfuehrung as HF          # noqa: E402
import agent.regel0_groesse as G          # noqa: E402

ok = n = 0


def pruefe(name, gut, info=""):
    global ok, n
    n += 1; ok += bool(gut)
    print("%-3s %s  %s" % (name, "gleich" if gut else "ABWEICHUNG", info))


t = HF.fuehre(symbol="BTC", richtung="LONG", eroeffnet_am="2026-10-09T04:38:53+00:00", hebel=3.0, positionswert_eur=1500.0,
              kreditbetrag_eur=1000.0, eigenkapital_eur=500.0, positionsmenge=0.02038541, kurs_eur=62000.0, jetzt="2026-10-09T08:00:00+00:00")
einstand = 1500.0 / 0.02038541
abstand = (62000.0 - t["liquidation_eur"]) / 62000.0
pruefe("G1", abs(t["einstand_eur"] - einstand) < 1e-6 and abs(t["abstand_liquidation"] - abstand) < 1e-12 and 53000 < t["liquidation_eur"] < 55000,
       "Einstand %.2f · Liquidation %.0f · Abstand %.4f" % (einstand, t["liquidation_eur"], abstand))


def zweite(a, g=0.15):
    if a is None or a < 0 or a >= g:
        return None
    if a >= g * 2 / 3:
        return round(g, 4)
    if a >= g / 3:
        return round(g * 2 / 3, 4)
    return round(g / 3, 4)


fehl = [i / 1000 for i in range(0, 301) if HF.nahe_stufe(i / 1000, 0.15) != zweite(i / 1000)]
pruefe("G2", not fehl, "301 Werte, Abweichungen %d %s" % (len(fehl), fehl[:5]))

a = dict(t, empfehlung=HF.LIQ_NAHE, nahe_stufe=0.15, position_id=7)
b = dict(a, nahe_stufe=0.10)
pruefe("G3", HF.schluessel(a, "2026-10-09") != HF.schluessel(b, "2026-10-09") and HF.schluessel(a, "2026-10-09") == HF.schluessel(dict(a), "2026-10-09")
       and HF.schluessel(a, "2026-10-09") != HF.schluessel(a, "2026-10-10"), HF.schluessel(a, "2026-10-09"))

d = tempfile.mkdtemp(prefix="h15g_")
c = sqlite3.connect(os.path.join(d, "w.db"))
c.row_factory = sqlite3.Row
import database.db as DB  # noqa: E402
DB.init_db(c)
werte = {"symbol": "BTC", "richtung": "LONG", "status": "offen", "eroeffnet_am": "2026-10-09T04:38:53+00:00", "hebel_effektiv": 3.0,
         "positionswert_eur": 1500.0, "kreditbetrag_eur": 1000.0, "eigenkapital_eur": 500.0, "positionsmenge": 0.02038541}
for cid, name, typ, notnull, vorgabe, pk in c.execute("PRAGMA table_info(hebel_positions)").fetchall():
    if notnull and vorgabe is None and not pk and name not in werte:
        werte[name] = 1759984733 if "unix" in name else (0 if "INT" in (typ or "").upper() or "REAL" in (typ or "").upper() else "")
c.execute("INSERT INTO hebel_positions (%s) VALUES (%s)" % (", ".join(werte), ", ".join("?" * len(werte))), list(werte.values()))
c.execute("INSERT INTO price_cache (symbol, coingecko_id, price_usd, price_eur, fetched_at) VALUES ('BTC','bitcoin',1,60000,'2026-10-09T08:00:00+00:00')")
c.commit()
tr = HF.lade(c, symbole=["BTC"])
c.close()
quelle = io.open(os.path.join("agent", "rollen_lauf.py"), encoding="utf-8").read()
pruefe("G4", "_HF.lade(conn, symbole=list(symbole or ()))" in quelle and tr and tr[0]["empfehlung"] == HF.LIQ_NAHE,
       "alter Aufruf unveraendert; Empfehlung bei 60.000: %s" % (tr[0]["empfehlung"] if tr else "-"))

fx = 0
for falsch in ("liquidations_warnung_abstand: 1.5\n", "hebelfuehrung_aktiv: ja\n"):
    p = os.path.join(d, "r.yaml")
    io.open(p, "w", encoding="utf-8").write(falsch)
    try:
        G.lade(p)
        fx += 1
    except ValueError:
        pass
pruefe("G5", fx == 0, "falsche Werte ohne Abbruch: %d" % fx)

ex = io.open("nb_teilexport_betriebsdaten.py", encoding="utf-8").read()
import ast  # noqa: E402
ast.parse(ex)
teil = ex[ex.index("H15 (09.10.2026)"):ex.index("H15 (09.10.2026)") + 600]
pruefe("G6", "FROM job_laeufe WHERE job_id LIKE 'hebelfuehrung:%'" in teil and not re.search(r"\b(INSERT|UPDATE|DELETE)\b", teil),
       "Exportabschnitt liest nur")
print("\n%d von %d gleich" % (ok, n))
