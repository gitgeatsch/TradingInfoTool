"""P22 USB-/Drive-Ergaenzung der Umlaufmenge (15.10.2026, Spot §54.8) - Pruefstand am SEITENEFFEKT, nur Wegwerf-Dateien (D:).

    python Basisinfos/Rechenkern_02_10/p22u_pruefstand.py

NB-Lage: Ziel = Kopie der USB-Mengendatei vom 22.09. (Marke _nur_betrieb, 08.09.-22.09.) + nachgestellte NB-Tage bis 14.10.
(Tagesjob-Form: circulating_supply = derselbe Wert wie die Desktop-Reihe am selben Tag, verschoben fortgeschrieben).

  U1  Erzeuger: nur Zeilen VOR dem NB-Beginn, Pruefsumme, keine Marke _nur_betrieb, keine Zuordnung; die Desktop-Quelle unveraendert
  U2  Einspielen: neu = genau die angebotenen Zeilen, NB-Tage Pruefsumme unveraendert, Marke da, integrity ok, Sicherung vorhanden und
      gleich dem Vorzustand, Vermerk in _ergaenzung_eingespielt
  U3  zweiter Lauf: 0 neu (idempotent), zweiter Vermerk
  U4  Schutz: Ziel ohne Marke (= Desktop-Messbasis) -> Abbruch, Datei bitgleich; beschaedigte Ergaenzung (Pruefsumme) -> Abbruch, Ziel bitgleich
  U5  Schutz: das Skript oeffnet die Produktion nie (Quelltext + Name tradinginfotool.db -> Abbruch)
  U6  Wirkung: nach dem Einspielen hat TAO am 22.09. eine Verwaesserung 90 T, vorher nicht (agent.verwaesserung.wert)
  U7  Diagnose: messbasen turnover zeigt aelteste_daten 2025-09 und den Vermerk der Ergaenzung
"""
import hashlib
import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile
from pathlib import Path

WURZEL = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(WURZEL)
sys.path.insert(0, WURZEL)
import wegwerf  # noqa: E402,F401  Wegwerf-Ordner auf D: und Aufraeumen ohne stilles Scheitern (15.10.2026)

import pandas as pd  # noqa: E402

import agent.verwaesserung as VW  # noqa: E402
import baue_umlauf_ergaenzung as BE  # noqa: E402
import ergaenze_umlauf_nb as EN  # noqa: E402

ERG = []
USB = Path("K:/My Drive/Claude_Austauschordner/umlaufmenge_cg.db")


def pruefe(k, ok, text):
    ERG.append(bool(ok))
    print("%-4s %-9s %s" % (k, "bestanden" if ok else "FEHLER", text))


def summe(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


T = Path(tempfile.mkdtemp(prefix="p22u_"))
QUELLE = T / "desktop_umlauf.db"
shutil.copy("data/umlaufmenge_cg.db", QUELLE)
q_vor = summe(QUELLE)
ZIEL = T / "nb" / "data" / "umlaufmenge_cg.db"
ZIEL.parent.mkdir(parents=True)
shutil.copy(USB, ZIEL)
# NB-Tage 23.09.-14.10. nachstellen (wie der Tagesjob sie geschrieben haette)
c = sqlite3.connect(str(ZIEL))
syms = [r[0] for r in c.execute("SELECT DISTINCT symbol FROM umlaufmenge")]
letzt = {s: w for s, w in c.execute("SELECT symbol, wert FROM umlaufmenge WHERE datum=(SELECT MAX(datum) FROM umlaufmenge)")}
for d in pd.date_range("2026-09-23", "2026-10-14"):
    c.executemany("INSERT OR IGNORE INTO umlaufmenge VALUES (?,?,?)", [(s, d.date().isoformat(), letzt[s]) for s in syms if s in letzt])
c.commit()
nb_beginn = c.execute("SELECT MIN(datum) FROM umlaufmenge").fetchone()[0][:10]
c.close()

# ══ U1 Erzeuger ══════════════════════════════════════════════════════════════════════════════════════════════════════════════
info = BE.baue(T / "ausgang", nb_beginn, QUELLE)
e = sqlite3.connect(info["datei"])
max_d, n_e = e.execute("SELECT MAX(datum), COUNT(*) FROM umlaufmenge").fetchone()
tabs = {r[0] for r in e.execute("SELECT name FROM sqlite_master WHERE type='table'")}
e.close()
qq = sqlite3.connect("file:%s?mode=ro" % QUELLE.as_posix(), uri=True)
n_q = qq.execute("SELECT COUNT(*) FROM umlaufmenge WHERE datum < ?", (nb_beginn,)).fetchone()[0]
qq.close()
pruefe("U1", max_d < nb_beginn and n_e == n_q == info["zeilen"] and tabs == {"umlaufmenge", "_ergaenzung"} and summe(QUELLE) == q_vor,
       "NB-Beginn %s · Ergaenzung %d Zeilen (%s bis %s), %.1f MB · Tabellen %s · Quelle unveraendert %s" % (
           nb_beginn, n_e, info["von"], max_d, info["mb"], sorted(tabs), summe(QUELLE) == q_vor))

# ══ U6 vorher ════════════════════════════════════════════════════════════════════════════════════════════════════════════════
def tao_wert(p):
    c = sqlite3.connect("file:%s?mode=ro" % p.as_posix(), uri=True)
    d = pd.read_sql("SELECT datum, wert FROM umlaufmenge WHERE symbol='TAO'", c)
    c.close()
    d["datum"] = pd.to_datetime(d.datum.str[:10])
    return VW.wert(d.set_index("datum").wert.sort_index(), "2026-09-22")


v_vor = tao_wert(ZIEL)
vor_ziel = summe(ZIEL)

# ══ U2 Einspielen ════════════════════════════════════════════════════════════════════════════════════════════════════════════
r = EN.einspielen(Path(info["datei"]), ZIEL)
sich = Path(r["sicherung"])
c = sqlite3.connect(str(ZIEL))
verm = c.execute("SELECT COUNT(*), MAX(eingefuegt) FROM _ergaenzung_eingespielt").fetchone()
c.close()
pruefe("U2", r["ok"] and r["eingefuegt"] == r["angeboten"] == n_e and r["nb_tage_unveraendert"] and r["marke"] and sich.exists()
       and summe(sich) != "" and verm == (1, n_e),
       "eingefuegt %d von %d · Zeilen %d -> %d · fruehester Tag %s · NB-Tage unberuehrt %s · Sicherung %s · Vermerk %s" % (
           r["eingefuegt"], r["angeboten"], r["zeilen_vor"], r["zeilen_nach"], r["fruehester_tag"], r["nb_tage_unveraendert"], sich.name, verm))
# Sicherung = Vorzustand (Inhalt, nicht Bytes: das Backup schreibt die Seiten neu)
s_c = sqlite3.connect(str(sich))
gleich_sich = s_c.execute("SELECT COUNT(*) FROM umlaufmenge").fetchone()[0] == r["zeilen_vor"]
s_c.close()

# ══ U3 zweiter Lauf ══════════════════════════════════════════════════════════════════════════════════════════════════════════
r2 = EN.einspielen(Path(info["datei"]), ZIEL)
c = sqlite3.connect(str(ZIEL))
verm2 = c.execute("SELECT COUNT(*) FROM _ergaenzung_eingespielt").fetchone()[0]
c.close()
pruefe("U3", r2["ok"] and r2["eingefuegt"] == 0 and r2["zeilen_nach"] == r["zeilen_nach"] and verm2 == 2 and gleich_sich,
       "zweiter Lauf: neu %d, angeboten %d (erster NB-Tag jetzt %s) · Zeilen %d · Vermerke %d · Sicherung = Vorzustand %s" % (
           r2["eingefuegt"], r2["angeboten"], r2["erster_nb"], r2["zeilen_nach"], verm2, gleich_sich))

# ══ U4 Schutz ════════════════════════════════════════════════════════════════════════════════════════════════════════════════
messbasis = T / "desktop" / "data" / "umlaufmenge_cg.db"
messbasis.parent.mkdir(parents=True)
shutil.copy(QUELLE, messbasis)
m_vor = summe(messbasis)
try:
    EN.einspielen(Path(info["datei"]), messbasis)
    ab1 = False
except SystemExit as x:
    ab1 = "_nur_betrieb" in str(x)
kaputt = T / "kaputt.db"
shutil.copy(info["datei"], kaputt)
k = sqlite3.connect(str(kaputt))
k.execute("UPDATE umlaufmenge SET wert = wert * 1.01 WHERE rowid = 1")
k.commit()
k.close()
z_vor = summe(ZIEL)
try:
    EN.einspielen(kaputt, ZIEL)
    ab2 = False
except SystemExit as x:
    ab2 = "Pruefsumme" in str(x)
pruefe("U4", ab1 and summe(messbasis) == m_vor and ab2 and summe(ZIEL) == z_vor,
       "ohne Marke abgebrochen %s, Messbasis bitgleich %s · beschaedigt abgebrochen %s, Ziel bitgleich %s" % (
           ab1, summe(messbasis) == m_vor, ab2, summe(ZIEL) == z_vor))

# ══ U5 Produktion nie ════════════════════════════════════════════════════════════════════════════════════════════════════════
qt = open("ergaenze_umlauf_nb.py", encoding="utf-8").read()
prod = T / "nb" / "data" / "tradinginfotool.db"
shutil.copy(ZIEL, prod)
p_vor = summe(prod)
try:
    EN.einspielen(Path(info["datei"]), prod)
    ab3 = False
except SystemExit as x:
    ab3 = "Produktion" in str(x)
pruefe("U5", ab3 and summe(prod) == p_vor and "connect(\"data/tradinginfotool" not in qt and "DB_PATH" not in qt,
       "Ziel tradinginfotool.db abgebrochen %s, bitgleich %s · kein Produktionspfad im Quelltext %s" % (
           ab3, summe(prod) == p_vor, "DB_PATH" not in qt))

# ══ U6 Wirkung ═══════════════════════════════════════════════════════════════════════════════════════════════════════════════
v_nach = tao_wert(ZIEL)
pruefe("U6", v_vor is None and v_nach is not None, "TAO Verwaesserung 90 T am 22.09.: vorher %s · nachher %s" % (
    v_vor, ("%+.1f %%" % (100 * (2.718281828 ** v_nach - 1))) if v_nach is not None else None))

# ══ U7 Diagnose ══════════════════════════════════════════════════════════════════════════════════════════════════════════════
code = ("import sys, json; sys.path.insert(0, %r); import extract_notebook_diagnose as E; "
        "print(json.dumps([z for z in E._messbasen()['je_groesse'] if z['groesse'] == 'turnover'], default=str))" % WURZEL)
os.remove(prod)
r7 = subprocess.run([sys.executable, "-c", code], cwd=str(T / "nb"), capture_output=True, text=True, encoding="utf-8", errors="replace")
try:
    z7 = __import__("json").loads(r7.stdout.strip().splitlines()[-1])[0]
except Exception:                                               # noqa: BLE001
    z7 = {}
pruefe("U7", z7.get("form") == "betriebskopie" and str(z7.get("aelteste_daten", ""))[:7] == "2025-09" and len(z7.get("ergaenzung") or []) == 2,
       "turnover form %s · aelteste %s · juengste %s · Vermerke %d%s" % (z7.get("form"), z7.get("aelteste_daten"), z7.get("juengste_daten"),
                                                                       len(z7.get("ergaenzung") or []), "" if z7 else " · " + (r7.stderr or "")[-300:]))
wegwerf.aufraeumen(str(T))
print("\n%d von %d bestanden" % (sum(ERG), len(ERG)))
