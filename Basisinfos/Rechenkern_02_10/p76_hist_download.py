"""P76 DOWNLOAD REGEL0-HISTORIE (23.10.2026, Nutzer-Ja "L-A" + "und Download"; Voranalyse_REGEL0_Historie_23_10.md §2).

    python Basisinfos/Rechenkern_02_10/p76_hist_download.py [--nur-liste] [--erster-monat]

--erster-monat: statt der Historie nur den ERSTEN vorhandenen Monat je Symbol der REGEL0-Menge (Messbasis + Zusatz bestand) - schliesst
die Luecke vom Monatsanfang bis zum Datenbeginn und liefert die Ueberlappung fuer den Abgleich in p77.

Binance Public Data (data.binance.vision, frei, ohne Konto): Stundenkerzen 1h, Monatsdateien, 2019-06 bis zum Monat VOR dem ersten Datensatz
des Symbols in den vorhandenen Dateien (stundenkurse.db = Messbasis, stundenkurse_alle.db = Zusatz). Spot: data/spot/monthly/klines,
Futures (Markt 'futures' in _quelle): data/futures/um/monthly/klines. Je Datei wird die SHA-256-Pruefsumme (.CHECKSUM) geprueft.
Ablage: data/_hist/roh/<paar>/<datei>.zip (nicht committet). Wiederaufnehmbar (vorhandene, gepruefte Dateien werden uebersprungen).
Protokoll: data/_hist/download_protokoll.csv. Keine Ausfuehrung heruntergeladener Inhalte - nur Speichern; gelesen wird spaeter als CSV.
"""
import csv
import hashlib
import os
import re
import sqlite3
import sys
import time

import requests

WURZEL = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(WURZEL)
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:  # noqa: BLE001
    pass
ROH = os.path.join("data", "_hist", "roh")
PROT = os.path.join("data", "_hist", "download_protokoll.csv")
S3 = "https://s3-ap-northeast-1.amazonaws.com/data.binance.vision"
BASIS = "https://data.binance.vision/"
AB = "2019-06"


def symbole():
    out = {}
    c = sqlite3.connect("file:data/stundenkurse.db?mode=ro", uri=True)
    for s, a in c.execute("SELECT symbol, MIN(stunde) FROM stundenkurse GROUP BY symbol"):
        out[s] = ("spot", s + "USDT", a[:7])
    c.close()
    c = sqlite3.connect("file:data/stundenkurse_alle.db?mode=ro", uri=True)
    erst = dict(c.execute("SELECT symbol, MIN(stunde) FROM stundenkurse GROUP BY symbol").fetchall())
    for s, markt, paar in c.execute("SELECT symbol, markt, paar FROM _quelle"):
        a = erst.get(s)
        if a is None:
            continue
        if s in out:
            out[s] = (out[s][0], out[s][1], min(out[s][2], a[:7]))
        else:
            out[s] = (markt, paar, a[:7])
    c.close()
    return out


def liste(markt, paar):
    pref = ("data/spot/monthly/klines/%s/1h/" if markt == "spot" else "data/futures/um/monthly/klines/%s/1h/") % paar
    keys, marke = [], None
    while True:
        par = {"delimiter": "/", "prefix": pref}
        if marke:
            par["marker"] = marke
        r = requests.get(S3, params=par, timeout=60)
        k = re.findall(r"<Key>([^<]+)</Key>", r.text)
        keys += k
        if "<IsTruncated>true</IsTruncated>" in r.text and k:
            marke = k[-1]
        else:
            break
    return [k for k in keys if k.endswith(".zip")]


def main():
    os.makedirs(ROH, exist_ok=True)
    S = symbole()
    print("Symbole %d (Spot %d, Futures %d)" % (len(S), sum(1 for v in S.values() if v[0] == "spot"), sum(1 for v in S.values() if v[0] != "spot")), flush=True)
    plan = []
    erster = "--erster-monat" in sys.argv
    if erster:   # nur der ERSTE vorhandene Monat der REGEL0-Menge (Messbasis + Zusatz bestand): Luecke bis Datenbeginn + Abgleich (p77)
        c = sqlite3.connect("file:data/stundenkurse.db?mode=ro", uri=True)
        menge = {r[0] for r in c.execute("SELECT DISTINCT symbol FROM stundenkurse")}
        c.close()
        with open(os.path.join("data", "_vergleich", "kern48jbz_gruppe_bestand.csv"), encoding="utf-8") as g:
            menge |= {r["symbol"] for r in csv.DictReader(g, delimiter=";") if r["neu"] == "1"}
        S = {s: v for s, v in S.items() if s in menge}
    for i, (s, (markt, paar, erst)) in enumerate(sorted(S.items())):
        if erst <= AB and not erster:
            continue
        try:
            ks = liste(markt, paar)
        except requests.RequestException:
            time.sleep(5)
            ks = liste(markt, paar)
        for k in ks:
            m = re.search(r"-(\d{4}-\d{2})\.zip$", k)
            if m and (m.group(1) == erst if erster else AB <= m.group(1) < erst):
                plan.append((s, markt, paar, k))
        time.sleep(0.05)
        if i % 50 == 0:
            print("  Liste %d/%d · geplant %d Dateien" % (i, len(S), len(plan)), flush=True)
    print("GEPLANT: %d Monatsdateien fuer %d Symbole" % (len(plan), len({p[0] for p in plan})), flush=True)
    if "--nur-liste" in sys.argv:
        return
    neu = os.path.exists(PROT)
    f = open(PROT, "a", newline="", encoding="utf-8")
    w = csv.writer(f, delimiter=";")
    if not neu:
        w.writerow(["symbol", "markt", "paar", "datei", "bytes", "sha256_ok", "zeit"])
    groesse = 0
    for j, (s, markt, paar, k) in enumerate(plan):
        ziel = os.path.join(ROH, paar, os.path.basename(k))
        if os.path.exists(ziel) and os.path.exists(ziel + ".ok"):
            continue
        os.makedirs(os.path.dirname(ziel), exist_ok=True)
        for v in range(5):
            try:
                d = requests.get(BASIS + k, timeout=120).content
                cs = requests.get(BASIS + k + ".CHECKSUM", timeout=60).text.split()[0]
                break
            except (requests.RequestException, IndexError):
                time.sleep(5 * (v + 1))
        else:
            w.writerow([s, markt, paar, k, 0, "FEHLER", time.strftime("%Y-%m-%d %H:%M:%S")])
            continue
        ok = hashlib.sha256(d).hexdigest() == cs.lower()
        if ok:
            with open(ziel, "wb") as g:
                g.write(d)
            open(ziel + ".ok", "w").close()
        groesse += len(d)
        w.writerow([s, markt, paar, k, len(d), "ja" if ok else "NEIN", time.strftime("%Y-%m-%d %H:%M:%S")])
        if j % 200 == 0:
            f.flush()
            print("  %d/%d Dateien · %.0f MB" % (j, len(plan), groesse / 1e6), flush=True)
        time.sleep(0.02)
    f.close()
    print("FERTIG: %.0f MB geladen" % (groesse / 1e6), flush=True)


if __name__ == "__main__":
    main()
