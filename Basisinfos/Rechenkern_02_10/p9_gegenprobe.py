"""P9 Statusseite (10.10.2026) - GEGENPROBE: jede angezeigte Zahl der Betriebslage mit EIGENEM SQL / eigener Lesart nachgerechnet.

    python Basisinfos/Rechenkern_02_10/p9_gegenprobe.py <Pruefverzeichnis>

Nicht ueber agent/betriebslage.py, sondern direkt auf den Kopien (mode=ro), mit anderer Formulierung wo moeglich
(z. B. Zaehlen in Python statt SUM in SQL, Ordnung nach Zeitstempel statt rowid).

  G1 Hebel: offene Positionen (Symbole) und Kurs je Symbol aus price_cache
  G2 REGEL0 heute: Signale, Schalter an, letzter Lauf
  G3 Pruefblock: Aufrufe des juengsten Pazifik-Tages
  G4 Ankuendigungen: Schalter aus der YAML, Laeufe
  G5 Jobs: Zahl und juengster Lauf (ohne H15-Meldeschluessel)
  G6 Nachlader: letzter Lauf je Datei (nach lauf_am statt rowid)
  G7 Bestand: mit Menge (frei + gestakt) und davon gestakt, in Python gezaehlt
  G8 Kontingente: Aufrufe je Quelle am juengsten Tag
  G9 Schalter: eigene YAML-Lesung
  G10 Kontrollen: offen/ueberfaellig aus eigener YAML-Lesung, automatische mit eigener Regel
"""
import dataclasses  # noqa: F401
import os
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml

WURZEL = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, WURZEL)
os.chdir(WURZEL)
D = os.path.abspath(sys.argv[1])
import agent.betriebslage as BL  # noqa: E402

BL.DATEN = D
import config as C  # noqa: E402
import remote.status as RS  # noqa: E402

ERG = []


def pruefe(k, ok, text):
    ERG.append(ok)
    print("%-4s %-10s %s" % (k, "gleich" if ok else "ABWEICHUNG", text))


def ro(p):
    c = sqlite3.connect("file:%s?mode=ro" % p.replace("\\", "/"), uri=True)
    c.row_factory = sqlite3.Row
    return c


PROD = os.path.join(D, "tradinginfotool.db")
c = ro(PROD)
RS.leere_aggregat_cache()
st = RS.build_status(c, C.get_watchlist(), Path(D) / "keins.log").to_dict()

# G1
offen = sorted(r["symbol"] for r in c.execute("SELECT symbol FROM hebel_positions WHERE geschlossen_am IS NULL"))
seite = sorted(p["symbol"] for p in st["hebel_lage"]["positionen"])
kurse = {}
for p in st["hebel_lage"]["positionen"]:
    r = c.execute("SELECT price_eur FROM price_cache WHERE symbol=? ORDER BY fetched_at DESC LIMIT 1", (p["symbol"],)).fetchone()
    kurse[p["symbol"]] = (p["kurs_eur"], r[0] if r else None)
pruefe("G1", offen == seite and all(a == b for a, b in kurse.values()), "offen %s / Seite %s · Kurs %s" % (offen, seite, kurse))

# G2
tag = datetime.now(timezone.utc).date().isoformat()
r0 = ro(os.path.join(D, "regel0_signale.db"))
eigen = [r for r in r0.execute("SELECT signalstunde, hebel_schalter FROM signal") if str(r[0]).startswith(tag)]
lauf = r0.execute("SELECT MAX(jetzt) FROM lauf").fetchone()[0]
h = st["regel0_lage"]["heute"]
pruefe("G2", h["signale_heute"] == len(eigen) and h["schalter_an_heute"] == sum(1 for r in eigen if r[1] == 1)
       and h["letzter_lauf"][0] == lauf, "Signale %d/%d · an %d/%d · Lauf %s/%s" % (
           h["signale_heute"], len(eigen), h["schalter_an_heute"], sum(1 for r in eigen if r[1] == 1), h["letzter_lauf"][0], lauf))

# G3
zeilen = r0.execute("SELECT tag_pazifik, aufrufe FROM pruefung WHERE gefragt=1").fetchall()
juengst = max(r[0] for r in zeilen) if zeilen else None
summe = sum((r[1] if r[1] is not None else 1) for r in zeilen if r[0] == juengst)
kt = st["kontingente"]["regel0_pruefblock"]
pb = st["regel0_lage"]["pruefblock"]["je_tag"][0] if st["regel0_lage"]["pruefblock"]["je_tag"] else None
pruefe("G3", kt["tag"] == juengst and kt["aufrufe"] == summe and pb and pb[0] == juengst and pb[1] == summe,
       "Tag %s · Aufrufe Kontingent %s / Pruefblock %s / eigen %d" % (juengst, kt["aufrufe"], pb and pb[1], summe))

# G4
yb = yaml.safe_load(open(os.path.join(WURZEL, "Basisinfos", "regel0_betrieb.yaml"), encoding="utf-8"))
tab = {r[0] for r in r0.execute("SELECT name FROM sqlite_master WHERE type='table'")}
n_lauf = r0.execute("SELECT COUNT(*) FROM ankuendigung_lauf").fetchone()[0] if "ankuendigung_lauf" in tab else None
a = st["regel0_lage"]["ankuendigung"]
pruefe("G4", a["an"] == bool(yb.get("ankuendigung_aktiv")) and (a["laeufe"] == n_lauf if a["lauf"] else n_lauf in (None,)),
       "Schalter %s/%s · Laeufe %s/%s" % (a["an"], yb.get("ankuendigung_aktiv"), a["laeufe"], n_lauf))

# G5
jobs = [r for r in c.execute("SELECT job_id, zuletzt_am FROM job_laeufe") if not str(r[0]).startswith("hebelfuehrung:")]
sj = st["betrieb"]["jobs"]
pruefe("G5", len(sj) == len(jobs) and sj[0]["zuletzt_am"] == max(r[1] for r in jobs),
       "Jobs %d/%d · juengster %s/%s" % (len(sj), len(jobs), sj[0]["zuletzt_am"], max(r[1] for r in jobs)))

# G6
abw = []
for e in st["betrieb"]["nachlader"]["dateien"]:
    if e["fehlt"]:
        continue
    k = ro(os.path.join(D, e["datei"]))
    r = k.execute("SELECT * FROM _nachlader ORDER BY lauf_am DESC LIMIT 1").fetchone()
    k.close()
    if (tuple(r) if r else None) != (tuple(e["letzter_lauf"]) if e["letzter_lauf"] else None):
        abw.append(e["datei"])
pruefe("G6", not abw, "%d Dateien, Abweichungen %s" % (len(st["betrieb"]["nachlader"]["dateien"]), abw))

# G7
mit, gest = 0, 0
for r in c.execute("SELECT quantity, staked_quantity FROM holdings"):
    q, s_ = float(r[0] or 0), float(r[1] or 0)
    mit += (q + s_) > 0
    gest += s_ > 0
b = st["bestand_lage"]
pruefe("G7", b["mit_menge"] == mit and b["davon_gestakt"] == gest, "mit Menge %s/%d · gestakt %s/%d" % (b["mit_menge"], mit, b["davon_gestakt"], gest))

# G8
mt = c.execute("SELECT MAX(tag) FROM api_call_kontingent_taeglich").fetchone()[0]
eig = sorted((r[0], r[1]) for r in c.execute("SELECT source, anzahl FROM api_call_kontingent_taeglich WHERE tag=?", (mt,)))
pruefe("G8", sorted(tuple(x) for x in st["kontingente"]["je_quelle_heute"]) == eig, "Tag %s · %s" % (mt, eig))

# G9
pruefe("G9", all(st["schalter"][k] == yb.get(k) for k in st["schalter"]) and len(st["schalter"]) == 5,
       "%s" % {k: (st["schalter"][k], yb.get(k)) for k in st["schalter"]})

# G10 - eigene Regel: k_bp_3 = meta-Fassung '2'; k_ank_1 = Schalter an, Laeufe > 0, alle ok
yk = yaml.safe_load(open(os.path.join(WURZEL, "Basisinfos", "nb_kontrollen.yaml"), encoding="utf-8"))["kontrollen"]
meta = dict(c.execute("SELECT key, value FROM meta").fetchall())
ank_ok = bool(yb.get("ankuendigung_aktiv")) and "ankuendigung_lauf" in tab and n_lauf and \
    r0.execute("SELECT COUNT(*) FROM ankuendigung_lauf WHERE ok=1").fetchone()[0] == n_lauf
auto = {"k_bp_3": meta.get("bitpanda_wallet_salden_fassung") == "2", "k_ank_1": bool(ank_ok)}
heute = datetime.now(timezone.utc).date().isoformat()
off = [e for e in yk if e["status"] == "offen" and not (e.get("art") == "automatisch" and auto.get(e.get("pruefung")))]
ueb = [e for e in off if e.get("faellig_bis") and str(e["faellig_bis"]) < heute]
k = st["kontrollen"]
pruefe("G10", k["offen"] == len(off) and k["ueberfaellig"] == len(ueb) and sorted(e["id"] for e in k["eintraege"])
       == sorted(e["id"] for e in yk if e["status"] == "offen"), "offen %s/%d · ueberfaellig %s/%d · automatisch %s" % (
           k["offen"], len(off), k["ueberfaellig"], len(ueb), auto))
c.close()
r0.close()
print()
print("%d von %d gleich" % (sum(ERG), len(ERG)))
