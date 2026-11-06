"""G7 P-2 — Stundenkurse der im Rückspielzeitraum EINGESTELLTEN Werte (Gegenprüfung 05.11.2026, Befund P-2 Überlebensauswahl;
Nutzer 05.11.: *„ja laden immer prüfen und gegenprüfen“*).

Warum: die Stundenkurse (Arbeitskopie und data/) enthalten nur Werte, die am 01.10.2026 noch gehandelt wurden. Delistete Werte fehlen,
also fallen ihre Ereignisse aus der S7-Eingabe - Auswahl mit Wissen nach T. Hier werden sie nachgeladen.

Quelle: Binance Public Data (data.binance.vision, frei, ohne Konto), Spot 1h-Monatsdateien, sonst USDT-M-Futures. SHA-256 je Datei
(.CHECKSUM). Nur gespeichert und als CSV gelesen, nie ausgeführt. Roh: data/_hist/roh_eingestellt/ (nicht committet).
Ziel: data/_g7/kurse/stundenkurse_eingestellt.db (gleiches Schema wie stundenkurse_alle.db, Marke _g7_rueckspiel).

Kandidaten = (a) Messbasis messreihen_status 'eingestellt' mit Tageskurs ab 2025-11-01, (b) jedes Asset eines Börsen-Ereignisses
im Zeitraum, das in keiner Stundendatei steht. Gegenprüfungen (--pruefe): Tagesschluss aus Stunden gegen den Tageskurs der Messbasis,
Stundenlücken je Monat, Ende der Reihe gegen das Delisting-Ereignis.

    python Basisinfos/Rechenkern_02_10/g7_lade_eingestellt.py            # laden (wiederaufnehmbar)
    python Basisinfos/Rechenkern_02_10/g7_lade_eingestellt.py --pruefe   -> g7_lade_eingestellt.txt
"""
import csv
import hashlib
import io
import json
import os
import re
import sqlite3
import sys
import time
import zipfile

import pandas as pd
import requests

HIER = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.dirname(os.path.dirname(HIER))
sys.path.insert(0, PROJ)
KOPIE = os.path.join(PROJ, "data", "_g7", "kurse")
ZIEL = os.path.join(KOPIE, "stundenkurse_eingestellt.db")
ROH = os.path.join(PROJ, "data", "_hist", "roh_eingestellt")
S3 = "https://s3-ap-northeast-1.amazonaws.com/data.binance.vision"
BASIS = "https://data.binance.vision/"
VON, BIS = "2025-05", "2026-10"           # σ braucht 60 T und die S7-Menge 500 Stunden VOR dem ersten Stichtag 2025-12-01
TXT = []


def p(*a):
    s = " ".join(str(x) for x in a)
    print(s, flush=True)
    TXT.append(s)


def _ro(f):
    return sqlite3.connect("file:%s?mode=ro" % f.replace("\\", "/"), uri=True)


def vorhandene() -> set:
    s = set()
    for ordner in (KOPIE, os.path.join(PROJ, "data")):
        for f in ("stundenkurse.db", "stundenkurse_alle.db"):
            pf = os.path.join(ordner, f)
            if os.path.exists(pf):
                s |= {r[0] for r in _ro(pf).execute("SELECT DISTINCT symbol FROM stundenkurse")}
    return s


def kandidaten() -> dict:
    """-> {symbol: grund}"""
    da = vorhandene()
    k = {}
    c = _ro(os.path.join(PROJ, "data", "messdaten.db"))
    for (s,) in c.execute("""SELECT s.symbol FROM messreihen_status s JOIN price_history_ohlc p USING(symbol)
                             WHERE s.status='eingestellt' AND p.date >= '2025-11-01' GROUP BY s.symbol"""):
        if s not in da:
            k[s] = "messbasis_eingestellt"
    from agent import ereignisse as EV
    E = EV.lade()
    x = E[(E.quelle != "nachricht") & (E.bekannt_ab >= "2025-11-01") & (E.bekannt_ab < "2026-11-01") & (E.ereignis == 1)]
    for a in x.assets:
        for s in json.loads(a):
            if s not in da and s not in k:
                k[s] = "boersen_ereignis"
    return k


def liste(markt, paar):
    pref = ("data/spot/monthly/klines/%s/1h/" if markt == "spot" else "data/futures/um/monthly/klines/%s/1h/") % paar
    r = requests.get(S3, params={"delimiter": "/", "prefix": pref}, timeout=60)
    return [k for k in re.findall(r"<Key>([^<]+)</Key>", r.text) if k.endswith(".zip")]


def hole(key: str) -> bytes | None:
    pf = os.path.join(ROH, key.replace("/", "_"))
    if os.path.exists(pf):
        return open(pf, "rb").read()
    d = requests.get(BASIS + key, timeout=120)
    ck = requests.get(BASIS + key + ".CHECKSUM", timeout=60)
    if d.status_code != 200 or ck.status_code != 200:
        return None
    if hashlib.sha256(d.content).hexdigest() != ck.text.split()[0]:
        raise RuntimeError("Prüfsumme falsch: %s" % key)
    os.makedirs(ROH, exist_ok=True)
    open(pf, "wb").write(d.content)
    return d.content


def zeilen(inhalt: bytes):
    z = zipfile.ZipFile(io.BytesIO(inhalt))
    for name in z.namelist():
        for r in csv.reader(io.TextIOWrapper(z.open(name), encoding="utf-8")):
            if not r or not r[0].isdigit():
                continue                                       # Kopfzeile (Futures-Archiv)
            t = int(r[0])
            t = t // 1000 if t > 10 ** 14 else t               # Spot ab 2025: Mikrosekunden
            yield (pd.Timestamp(t, unit="ms").strftime("%Y-%m-%d %H:%M"), float(r[1]), float(r[2]), float(r[3]), float(r[4]), float(r[5]))


def laden():
    t0 = time.time()
    K = kandidaten()
    p("G7 P-2 LADEN · %s · Kandidaten %d (Messbasis eingestellt %d, nur aus Börsen-Ereignissen %d)" % (
        time.strftime("%Y-%m-%d %H:%M"), len(K), sum(v == "messbasis_eingestellt" for v in K.values()),
        sum(v == "boersen_ereignis" for v in K.values())))
    c = sqlite3.connect(ZIEL)
    c.executescript("""CREATE TABLE IF NOT EXISTS stundenkurse (symbol TEXT NOT NULL, stunde TEXT NOT NULL, open REAL, high REAL, low REAL,
                       close REAL, volumen REAL, PRIMARY KEY (symbol, stunde));
                       CREATE TABLE IF NOT EXISTS _quelle (symbol TEXT PRIMARY KEY, markt TEXT, paar TEXT, geholt_am TEXT, grund TEXT);
                       CREATE TABLE IF NOT EXISTS _g7_rueckspiel (hinweis TEXT);""")
    if not c.execute("SELECT 1 FROM _g7_rueckspiel").fetchone():
        c.execute("INSERT INTO _g7_rueckspiel VALUES ('Nur G7-Rückspiel: Stundenkurse eingestellter Werte (P-2), nicht Messbasis')")
    ohne = []
    for i, (s, grund) in enumerate(sorted(K.items())):
        if c.execute("SELECT 1 FROM _quelle WHERE symbol=?", (s,)).fetchone():
            continue
        treffer = None
        for markt in ("spot", "futures"):
            keys = [k for k in liste(markt, s + "USDT") if VON <= k[-11:-4] <= BIS]
            if keys:
                treffer = (markt, keys)
                break
        if not treffer:
            ohne.append(s)
            continue
        n = 0
        for k in treffer[1]:
            inhalt = hole(k)
            if inhalt:
                rows = [(s,) + r for r in zeilen(inhalt)]
                c.executemany("INSERT OR REPLACE INTO stundenkurse VALUES (?,?,?,?,?,?,?)", rows)
                n += len(rows)
        c.execute("INSERT INTO _quelle VALUES (?,?,?,?,?)", (s, treffer[0], s + "USDT", time.strftime("%Y-%m-%d %H:%M"), grund))
        c.commit()
        if i % 10 == 0:
            p("  %d/%d %s %s %d Stunden (%.0f s)" % (i + 1, len(K), s, treffer[0], n, time.time() - t0))
    p("fertig: %d Symbole geladen, ohne Archiv %d: %s · %.0f s" % (
        c.execute("SELECT COUNT(*) FROM _quelle").fetchone()[0], len(ohne), ohne, time.time() - t0))
    c.close()


def pruefe():
    """Gegenprüfungen: (1) Tagesschluss gegen Messbasis, (2) Lücken, (3) Reihenende gegen Delisting-Ereignis."""
    p("G7 P-2 GEGENPRÜFUNG · %s" % time.strftime("%Y-%m-%d %H:%M"))
    c = _ro(ZIEL)
    md = _ro(os.path.join(PROJ, "data", "messdaten.db"))
    Q = pd.read_sql("SELECT * FROM _quelle", c)
    p("geladen %d Symbole (Spot %d, Futures %d)" % (len(Q), (Q.markt == "spot").sum(), (Q.markt == "futures").sum()))
    ende0 = dict(c.execute("SELECT symbol, MAX(stunde) FROM stundenkurse GROUP BY 1").fetchall())
    Q = Q[[ende0.get(s_, "9") < "2026-10-01" for s_ in Q.symbol]]
    p("davon eingestellt (Reihe endet vor 2026-10-01) und damit benutzt: %d (Spot %d, Futures %d); die übrigen leben weiter und "
      "bleiben draußen (andere Grundgesamtheit)" % (len(Q), (Q.markt == "spot").sum(), (Q.markt == "futures").sum()))
    abw, luecke, kein_vergleich = [], [], []
    for s, markt in zip(Q.symbol, Q.markt):
        k = pd.read_sql("SELECT stunde, close FROM stundenkurse WHERE symbol=?", c, params=(s,))
        k.index = pd.to_datetime(k.stunde)
        tag = k.close.resample("D").last().dropna()
        m = pd.read_sql("SELECT date, close FROM price_history_ohlc WHERE symbol=? AND assetklasse='krypto' AND date >= '2025-05-01'", md, params=(s,))
        if len(m):
            m.index = pd.to_datetime(m.date)
            j = tag.to_frame("h").join(m.close.rename("m"), how="inner")
            if len(j):
                d = (j.h / j.m - 1).abs()
                abw.append((s, markt, len(j), float(d.median()), float(d.max()), float((d > 0.01).mean())))
            else:
                kein_vergleich.append(s)
        else:
            kein_vergleich.append(s)
        if k.stunde.max() >= "2026-10-01":
            continue                                           # lebt weiter -> wird ohnehin nicht benutzt (nur eingestellte zählen)
        voll = pd.date_range(k.index.min(), k.index.max(), freq="h")
        fehl = len(voll) - len(k)
        if fehl:
            luecke.append((s, fehl, len(voll)))
    A = pd.DataFrame(abw, columns=["symbol", "markt", "tage", "median", "max", "anteil_ueber_1pct"])
    p("(1) Tagesschluss aus Stunden gegen Messbasis-Tageskurs: %d Symbole verglichen, %d ohne Vergleich %s" % (
        len(A), len(kein_vergleich), kein_vergleich[:15]))
    if len(A):
        p("    Abweichung Median über Symbole %.4f %% · Symbole mit > 1 %% an mehr als 5 %% der Tage: %d %s" % (
            100 * A["median"].median(), (A.anteil_ueber_1pct > 0.05).sum(),
            A[A.anteil_ueber_1pct > 0.05][["symbol", "markt", "anteil_ueber_1pct"]].values.tolist()[:10]))
    p("(2) Stundenlücken: %d Symbole mit Lücken; größte %s" % (len(luecke), sorted(luecke, key=lambda x: -x[1])[:8]))
    from agent import ereignisse as EV
    E = EV.lade()
    x = E[(E.quelle == "binance") & E.typ.isin(["delisting_token"]) & (E.ereignis == 1)]
    ende = dict(c.execute("SELECT symbol, MAX(stunde) FROM stundenkurse GROUP BY 1").fetchall())
    vgl = []
    for t, a in zip(x.bekannt_ab, x.assets):
        for s in json.loads(a):
            if s in ende:
                vgl.append((s, t[:10], ende[s][:10], (pd.Timestamp(ende[s]) - pd.Timestamp(t[:16])).days))
    V = pd.DataFrame(vgl, columns=["symbol", "meldung", "reihe_endet", "tage_danach"])
    if len(V):
        p("(3) Reihenende nach der Delisting-Meldung: %d Fälle · Tage Median %.0f, Min %d, Max %d (erwartet: einige Tage bis Wochen)" % (
            len(V), V.tage_danach.median(), V.tage_danach.min(), V.tage_danach.max()))
        p("    auffällig (< 0 oder > 60 Tage): %s" % V[(V.tage_danach < 0) | (V.tage_danach > 60)].values.tolist()[:10])
    open(os.path.join(HIER, "g7_lade_eingestellt.txt"), "w", encoding="utf-8").write("\n".join(TXT) + "\n")


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:                                                  # noqa: BLE001
        pass
    if "--pruefe" in sys.argv:
        pruefe()
    elif "--kandidaten" in sys.argv:
        K = kandidaten()
        print(len(K), K)
    else:
        laden()
