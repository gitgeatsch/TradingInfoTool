"""P77 AUFBAU data/_hist/ (23.10.2026, Messplan F-1 Fassung 2, Voranalyse_REGEL0_Historie_23_10.md §6).

    python -I -X utf8 Basisinfos/Rechenkern_02_10/p77_hist_aufbau.py

Baut den REGEL0-Ordner mit verlaengerter Historie - NUR in data/_hist/, die Quellen werden ausschliesslich mode=ro gelesen:

    data/_hist/stundenkurse.db       Kopie von data/stundenkurse.db (sqlite-Backup) + Binance-Stundenkerzen 2019-06 bis Datenbeginn
    data/_hist/stundenkurse_alle.db  nur die Zusatz-Assets der Gruppe bestand (kern48jbz_gruppe_bestand.csv) + _quelle + Marke

Eingelesen werden die von p76 geladenen und per SHA-256 geprueften Monatsdateien (data/_hist/roh/<paar>/*.zip, Marker .ok) - als CSV
aus dem Zip, nichts wird entpackt oder ausgefuehrt. stunde = open_time UTC 'YYYY-MM-DD HH:MM' (ms; ab 2025 Spot in Mikrosekunden).
INSERT OR IGNORE: vorhandene Zeilen bleiben unberuehrt. Monatsdateien des ERSTEN vorhandenen Monats (p76 --erster-monat) schliessen
die Luecke bis zum Datenbeginn und dienen dem Abgleich: jede ueberlappende Zeile wird gegen den Bestand verglichen.
Bericht: data/_hist/aufbau_bericht.csv (je Symbol) und Ausgabe.
"""
import csv
import io
import os
import sqlite3
import sys
import zipfile
from datetime import datetime, timezone

WURZEL = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(WURZEL)
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:  # noqa: BLE001
    pass
ZIEL = os.path.join("data", "_hist")
ROH = os.path.join(ZIEL, "roh")
PROT = os.path.join(ZIEL, "download_protokoll.csv")
GRUPPE = os.path.join("data", "_vergleich", "kern48jbz_gruppe_bestand.csv")


def _ro(p):
    return sqlite3.connect("file:%s?mode=ro" % p.replace("\\", "/"), uri=True)


def zusatz():
    """Wie agent.regel0_rechnung.zusatz_aus_gruppe (neu=1) - hier nachgeschrieben, damit das Skript mit -I nur die Standardbibliothek braucht."""
    with open(GRUPPE, encoding="utf-8") as f_:
        return sorted({r["symbol"] for r in csv.DictReader(f_, delimiter=";") if r["neu"] == "1"})


def stunde_txt(ot):
    ot = int(float(ot))
    if ot > 10 ** 14:          # Mikrosekunden (Binance Spot ab 2025-01)
        ot //= 1000
    return datetime.fromtimestamp(ot / 1000, tz=timezone.utc).strftime("%Y-%m-%d %H:%M")


def zeilen(pfad):
    with zipfile.ZipFile(pfad) as z:
        for name in z.namelist():
            if not name.endswith(".csv"):
                continue
            for r in csv.reader(io.TextIOWrapper(z.open(name), encoding="utf-8")):
                if not r or not r[0].strip().lstrip("-").isdigit():
                    continue           # Kopfzeile (Futures ab 2022)
                yield stunde_txt(r[0]), float(r[1]), float(r[2]), float(r[3]), float(r[4]), float(r[5])


def main():
    for p in ("stundenkurse.db", "stundenkurse_alle.db"):
        if os.path.exists(os.path.join(ZIEL, p)):
            print("ABBRUCH: %s existiert schon - erst bewusst wegraeumen (wegwerf.py)" % os.path.join(ZIEL, p))
            return 2
    zus = set(zusatz())
    # 1) Kopie der Messbasis
    q = _ro(os.path.join("data", "stundenkurse.db"))
    h = sqlite3.connect(os.path.join(ZIEL, "stundenkurse.db"))
    q.backup(h)
    q.close()
    db_syms = {s: a for s, a in h.execute("SELECT symbol, MIN(stunde) FROM stundenkurse GROUP BY symbol")}
    # 2) verkleinerte Zusatzdatei
    qa = _ro(os.path.join("data", "stundenkurse_alle.db"))
    ha = sqlite3.connect(os.path.join(ZIEL, "stundenkurse_alle.db"))
    for (sql,) in qa.execute("SELECT sql FROM sqlite_master WHERE type='table' AND sql IS NOT NULL"):
        ha.execute(sql)
    for (hw,) in qa.execute("SELECT hinweis FROM _nur_bewertung"):
        ha.execute("INSERT INTO _nur_bewertung VALUES (?)", (hw,))
    zs = sorted(zus - set(db_syms))
    for s in zs:
        ha.executemany("INSERT INTO stundenkurse VALUES (?,?,?,?,?,?,?)",
                       qa.execute("SELECT * FROM stundenkurse WHERE symbol=?", (s,)).fetchall())
        ha.executemany("INSERT INTO _quelle VALUES (?,?,?,?)", qa.execute("SELECT * FROM _quelle WHERE symbol=?", (s,)).fetchall())
    qa.close()
    ha.commit()
    zus_syms = {s: a for s, a in ha.execute("SELECT symbol, MIN(stunde) FROM stundenkurse GROUP BY symbol")}
    for con in (h, ha):
        con.execute("CREATE TABLE _hist_aufbau (hinweis TEXT)")
        con.execute("INSERT INTO _hist_aufbau VALUES (?)", ("Verlaengerte REGEL0-Historie fuer die MESSUNG F-1 Fassung 2 (p77, %s), "
                    "Binance 1h ab 2019-06. Nicht Betrieb, nicht Notebook." % datetime.now().strftime("%Y-%m-%d %H:%M"),))
    # 3) Historie einlesen
    paar_sym = {}
    with open(PROT, encoding="utf-8") as f:
        for r in csv.DictReader(f, delimiter=";"):
            paar_sym[r["paar"]] = r["symbol"]
    bericht = {}
    for paar in sorted(os.listdir(ROH)):
        s = paar_sym.get(paar)
        if s in db_syms:
            con, erst = h, db_syms[s]
        elif s in zus_syms:
            con, erst = ha, zus_syms[s]
        else:
            continue
        b = bericht.setdefault(s, dict(symbol=s, paar=paar, erst_alt=erst, dateien=0, neu=0, ueberlapp=0, abweichend=0, max_rel=0.0))
        for datei in sorted(os.listdir(os.path.join(ROH, paar))):
            pf = os.path.join(ROH, paar, datei)
            if not datei.endswith(".zip") or not os.path.exists(pf + ".ok"):
                continue
            b["dateien"] += 1
            rows = list(zeilen(pf))
            alt = {r[0]: r[1:] for r in con.execute("SELECT stunde, open, high, low, close FROM stundenkurse WHERE symbol=? AND stunde "
                                                    "BETWEEN ? AND ?", (s, rows[0][0], rows[-1][0]))} if rows else {}
            for st, o, hi, lo, c, v in rows:
                if st in alt:
                    b["ueberlapp"] += 1
                    rel = max(abs(x - y) / max(abs(y), 1e-12) for x, y in zip((o, hi, lo, c), alt[st]))
                    b["max_rel"] = max(b["max_rel"], rel)
                    b["abweichend"] += rel > 1e-9
            cur = con.executemany("INSERT OR IGNORE INTO stundenkurse VALUES (?,?,?,?,?,?,?)", [(s,) + r for r in rows])
            b["neu"] += cur.rowcount
        con.commit()
    for con, syms in ((h, db_syms), (ha, zus_syms)):
        for s in syms:
            if s in bericht:
                r = con.execute("SELECT MIN(stunde), COUNT(*) FROM stundenkurse WHERE symbol=?", (s,)).fetchone()
                bericht[s]["erst_neu"], bericht[s]["zeilen"] = r
                vor = con.execute("SELECT MAX(stunde) FROM stundenkurse WHERE symbol=? AND stunde < ?", (s, syms[s])).fetchone()[0]
                bericht[s]["luecke_h"] = "" if vor is None else int((datetime.strptime(syms[s], "%Y-%m-%d %H:%M") -
                                                                      datetime.strptime(vor, "%Y-%m-%d %H:%M")).total_seconds() // 3600)
    h.close(); ha.close()
    sp = ["symbol", "paar", "erst_alt", "erst_neu", "zeilen", "dateien", "neu", "ueberlapp", "abweichend", "max_rel", "luecke_h"]
    with open(os.path.join(ZIEL, "aufbau_bericht.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, sp, delimiter=";")
        w.writeheader()
        for s in sorted(bericht):
            w.writerow({k: bericht[s].get(k, "") for k in sp})
    B = list(bericht.values())
    print("AUFBAU data/_hist: Messbasis %d Symbole, Zusatz %d (%s)" % (len(db_syms), len(zus_syms), ",".join(sorted(zus_syms))))
    print("  mit Historie: %d Symbole, %d Dateien, %d neue Zeilen" % (sum(b["neu"] > 0 for b in B), sum(b["dateien"] for b in B),
                                                                    sum(b["neu"] for b in B)))
    print("  Abgleich: %d ueberlappende Zeilen, davon abweichend %d (max rel %.2e)" % (
        sum(b["ueberlapp"] for b in B), sum(b["abweichend"] for b in B), max([b["max_rel"] for b in B] or [0])))
    lk = [b for b in B if b.get("luecke_h") not in ("", None, 1)]
    print("  Uebergang Historie -> Bestand nicht lueckenlos (>1 h): %d Symbole %s" % (
        len(lk), ", ".join("%s %sh" % (b["symbol"], b["luecke_h"]) for b in sorted(lk, key=lambda b: -b["luecke_h"])[:12])))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
