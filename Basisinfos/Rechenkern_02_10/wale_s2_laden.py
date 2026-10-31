# -*- coding: utf-8 -*-
"""G16 Wale STUFE 2 — Download für alle REGEL0-Assets (31.10.2026, Nutzer: *„Stufe 2 a, prüfen, gegenprüfen, Doku“*).

Umfang aus der Voranalyse (``Voranalyse_Wale_Stufe2_31_10.md`` §3 D, Zwischenspeicher ``data/_wale/s2_head.csv``): 168 Symbole,
5.643 MONATSdateien aggTrades Spot 2023-01 bis 2026-08, 87,5 GB zip. Kern und die sechs aus Fassung 4 liegen schon in
``wale_voll.db`` und werden hier NICHT geladen.

Verdichtung **bitgleich** zu Fassung 3/4: die Monatsdatei wird nach UTC-Tag zerlegt, jeder Tag läuft durch ``wale_stichprobe.verdichte``
(Sweep = Lauf gleicher Zeit und Seite, Viertel-Dekaden-Klassen in USD). Ein Sweep kann keinen Tag überspannen, genau wie in den
Tagesdateien. Abgelegt werden nur Tag und Sweep-Verteilung (E ist eine Tagesgröße); keine Stundentabelle, keine Rohdaten.

    Ablage     data/_wale/wale_s2.db — DASSELBE Schema wie wale_voll.db, damit ``p102_wale_basis.fluss``/``bewegung`` unverändert laufen.
               ⚠️ Tabelle ``kurs`` trägt hier nur TAGESkerzen (ts = 00:00 UTC, Eröffnung/Schluss des Tages); ``bewegung`` braucht nur 00:00.
    Fortsetzen Tabelle ``monat`` markiert fertige Monatsdateien; ein Abbruch kostet höchstens die laufenden Monate.

    python -X utf8 Basisinfos/Rechenkern_02_10/wale_s2_laden.py --laden [--lader 8]   # Monatsdateien (setzt fort)
    python -X utf8 Basisinfos/Rechenkern_02_10/wale_s2_laden.py --kerzen              # REST-Tageskerzen (Abgleich und r_t)
    python -X utf8 Basisinfos/Rechenkern_02_10/wale_s2_laden.py --bericht
"""
import io
import os
import sqlite3
import sys
import time
import zipfile
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import date, datetime, timezone

import numpy as np
import pandas as pd
import requests

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HIER)
import wale_stichprobe as WS  # noqa: E402

ABLAGE = os.path.join(WS.PROJ, "data", "_wale", "wale_s2.db")
KOPF = os.path.join(WS.PROJ, "data", "_wale", "s2_head.csv")
GELADEN = ("BTC", "ETH", "SOL", "BNB", "ADA", "TRX", "AVAX", "LINK", "NEAR")
URL_M = "https://data.binance.vision/data/spot/monthly/aggTrades/{p}/{p}-aggTrades-{m}.zip"
START = date(2023, 1, 1)
ENDE = date(2026, 8, 31)
TAG_MS = 86_400_000
CHUNK = 3_000_000


def verbinde():
    os.makedirs(os.path.dirname(ABLAGE), exist_ok=True)
    c = sqlite3.connect(ABLAGE, timeout=600)
    c.execute("PRAGMA journal_mode=WAL")
    c.executescript("""
    CREATE TABLE IF NOT EXISTS tag (symbol TEXT, markt TEXT, datum TEXT, umsatz_usd REAL, kauf_usd REAL, aggtrades INTEGER,
                                    sweeps INTEGER, kerze_usd REAL, kerze_kauf_usd REAL, erste_utc TEXT, letzte_utc TEXT, geholt TEXT,
                                    PRIMARY KEY (symbol, markt, datum));
    -- nur einheit 'sweep' (E rechnet nur damit); seite 'kauf' (Taker kauft)|'verkauf', klasse k = Untergrenze 10^(k/4) USD
    CREATE TABLE IF NOT EXISTS verteilung (symbol TEXT, markt TEXT, datum TEXT, einheit TEXT, seite TEXT, klasse INTEGER,
                                           anzahl INTEGER, usd REAL, PRIMARY KEY (symbol, markt, datum, einheit, seite, klasse));
    -- TAGESkerzen per REST: ts = 00:00 UTC des Tages
    CREATE TABLE IF NOT EXISTS kurs (symbol TEXT, ts INTEGER, eroeffnung REAL, schluss REAL, PRIMARY KEY (symbol, ts));
    CREATE TABLE IF NOT EXISTS kerze (symbol TEXT, datum TEXT, eroeffnung REAL, schluss REAL, quote_usd REAL, kauf_quote_usd REAL,
                                      PRIMARY KEY (symbol, datum));
    CREATE TABLE IF NOT EXISTS monat (symbol TEXT, monat TEXT, bytes INTEGER, tage INTEGER, zeilen INTEGER, geholt TEXT,
                                      PRIMARY KEY (symbol, monat));
    """)
    return c


def auftraege():
    """(paar, monat, bytes) aller zu ladenden Monatsdateien, größte zuerst (die langen Läufer starten früh)."""
    T = pd.read_csv(KOPF)
    v = T[(T.bytes > 0) & ~T.symbol.isin(GELADEN)]
    paar = v.groupby("symbol").paar.agg(lambda x: x.value_counts().index[0])
    v = v[v.paar == v.symbol.map(paar)]
    return [(r.paar, r.monat, int(r.bytes)) for r in v.sort_values("bytes", ascending=False).itertuples()]


def _utc(ms: int) -> str:
    return datetime.fromtimestamp(ms / 1000, timezone.utc).isoformat(timespec="seconds")


def _hole(url, versuche=5):
    for v in range(versuche):
        try:
            r = requests.get(url, timeout=600, headers={"User-Agent": "Mozilla/5.0 (TradingInfoTool Forschung)"})
            if r.status_code == 200:
                return r.content
            if r.status_code == 404:
                return None
        except requests.RequestException:
            pass
        time.sleep(20 * (v + 1))
    raise RuntimeError("nicht abrufbar: %s" % url)


def _tag(paar, df):
    """Ein UTC-Tag -> (tag-Zeile ohne Kerze, Sweep-Zeilen) über DENSELBEN Rechenweg wie Fassung 3/4 (``WS.verdichte``)."""
    zeit = df["zeit"].to_numpy()
    ms = zeit // 1000 if zeit.max() > 1e14 else zeit                # Spot ab 2025 in MIKROsekunden
    umsatz, kauf, n_agg, n_sw, zeilen = WS.verdichte(df)
    datum = datetime.fromtimestamp(int(ms[0]) // TAG_MS * 86400, timezone.utc).strftime("%Y-%m-%d")
    return ((paar, "spot", datum, umsatz, kauf, n_agg, n_sw, None, None, _utc(int(ms.min())), _utc(int(ms.max())),
             datetime.now(timezone.utc).isoformat(timespec="seconds")),
            [(paar, "spot", datum) + z for z in zeilen if z[0] == "sweep"])


def lade_monat(paar: str, monat: str, nbytes: int):
    """Lädt eine Monatsdatei im Speicher, zerlegt sie in Stücken nach UTC-Tag und schreibt Tag und Verteilung in EINER Transaktion."""
    roh = _hole(URL_M.format(p=paar, m=monat))
    if roh is None:
        return paar, monat, -1, 0
    tage, vert, zeilen = [], [], 0
    with zipfile.ZipFile(io.BytesIO(roh)) as z, z.open(z.namelist()[0]) as f:
        kopf = f.peek(40)[:40].decode("ascii", "replace")
        leser = pd.read_csv(f, header=0 if kopf[:1].isalpha() else None, usecols=[1, 2, 5, 6], chunksize=CHUNK)
        rest = None
        for ch in leser:
            ch.columns = ["preis", "menge", "zeit", "kaeufer_maker"]
            ch["kaeufer_maker"] = ch["kaeufer_maker"].astype(str).str.lower().isin(("true", "1"))
            zeilen += len(ch)
            if rest is not None:
                ch = pd.concat([rest, ch], ignore_index=True)
            zeit = ch["zeit"].to_numpy()
            tag = (zeit // 1000 if zeit.max() > 1e14 else zeit) // TAG_MS
            fertig = tag < tag[-1]                                        # der letzte Tag des Stücks kann weitergehen
            for _t, g in ch[fertig].groupby(tag[fertig], sort=True):
                a, b = _tag(paar, g.reset_index(drop=True))
                tage.append(a)
                vert += b
            rest = ch[~fertig].reset_index(drop=True)
        if rest is not None and len(rest):
            a, b = _tag(paar, rest)
            tage.append(a)
            vert += b
    del roh
    c = verbinde()
    with c:
        c.executemany("INSERT OR REPLACE INTO tag VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", tage)
        c.executemany("INSERT OR REPLACE INTO verteilung VALUES (?,?,?,?,?,?,?,?)", vert)
        c.execute("INSERT OR REPLACE INTO monat VALUES (?,?,?,?,?,?)",
                  (paar, monat, nbytes, len(tage), zeilen, datetime.now(timezone.utc).isoformat(timespec="seconds")))
    c.close()
    return paar, monat, len(tage), zeilen


def laden(lader: int):
    c = verbinde()
    fertig = {(s, m) for s, m in c.execute("SELECT symbol, monat FROM monat")}
    c.close()
    alle = auftraege()
    offen = [a for a in alle if (a[0], a[1]) not in fertig]
    gb_ges, gb_offen = sum(a[2] for a in alle) / 1e9, sum(a[2] for a in offen) / 1e9
    print("%s · %d Monatsdateien, %.1f GB · offen %d, %.1f GB · %d Lader" % (
        datetime.now().isoformat(timespec="seconds"), len(alle), gb_ges, len(offen), gb_offen, lader), flush=True)
    t0, gb, fehler = time.time(), 0.0, 0
    with ProcessPoolExecutor(lader) as ex:
        zu = {ex.submit(lade_monat, *a): a for a in offen}
        for i, f in enumerate(as_completed(zu), 1):
            a = zu[f]
            try:
                paar, monat, nt, nz = f.result()
                gb += a[2] / 1e9
                h = (time.time() - t0) / 3600
                print("  %s ✔ %4d/%d %-14s %s %3d Tage %10d Zeilen · %.1f/%.1f GB · %.1f GB/h" % (
                    datetime.now().strftime("%H:%M:%S"), i, len(offen), paar, monat, nt, nz, gb, gb_offen, gb / max(h, 1e-6)), flush=True)
            except Exception as ex_:                                       # noqa: BLE001 - Lauf geht weiter, Monat bleibt offen
                fehler += 1
                print("  ✖ %s %s: %s" % (a[0], a[1], ex_), flush=True)
    print("ENDE %s · Fehler %d (offen geblieben, erneuter Aufruf setzt fort)" % (datetime.now().isoformat(timespec="seconds"), fehler), flush=True)
    return fehler


def kerzen():
    """REST-Tageskerzen je Paar ab 2023-01-01: Abgleich Archiv = Kerze (Vorprüfung) und Tagesbewegung r_t (00:00 bis 00:00)."""
    c = verbinde()
    paare = sorted({a[0] for a in auftraege()})
    for paar in paare:
        ab, n = int(datetime(START.year, 1, 1, tzinfo=timezone.utc).timestamp() * 1000), 0
        while True:
            r = WS._hole(WS.MAERKTE["spot"][1], {"symbol": paar, "interval": "1d", "startTime": ab, "limit": 1000})
            if r is None:
                print("  ✖ Kerzen %s nicht abrufbar" % paar, flush=True)
                break
            k = r.json()
            jetzt = int(time.time() * 1000)
            k = [x for x in k if x[6] < jetzt]                             # nur abgeschlossene Tage
            with c:
                c.executemany("INSERT OR REPLACE INTO kerze VALUES (?,?,?,?,?,?)",
                              [(paar, datetime.fromtimestamp(x[0] / 1000, timezone.utc).strftime("%Y-%m-%d"), float(x[1]), float(x[4]),
                                float(x[7]), float(x[10])) for x in k])
                c.executemany("INSERT OR REPLACE INTO kurs VALUES (?,?,?,?)", [(paar, int(x[0]), float(x[1]), float(x[4])) for x in k])
            n += len(k)
            if len(k) < 1000:
                break
            ab = k[-1][0] + TAG_MS
        print("  ✔ Kerzen %-14s %d Tage" % (paar, n), flush=True)
    with c:
        c.execute("UPDATE tag SET kerze_usd = (SELECT quote_usd FROM kerze k WHERE k.symbol = tag.symbol AND k.datum = tag.datum), "
                  "kerze_kauf_usd = (SELECT kauf_quote_usd FROM kerze k WHERE k.symbol = tag.symbol AND k.datum = tag.datum)")
    c.close()


def bericht():
    c = sqlite3.connect("file:%s?mode=ro" % ABLAGE.replace("\\", "/"), uri=True)
    alle = auftraege()
    fertig = dict(((s, m), (t, z)) for s, m, t, z in c.execute("SELECT symbol, monat, tage, zeilen FROM monat"))
    print("Monatsdateien fertig %d von %d · %.1f von %.1f GB" % (
        len(fertig), len(alle), sum(a[2] for a in alle if (a[0], a[1]) in fertig) / 1e9, sum(a[2] for a in alle) / 1e9))
    print("Tage %d · Verteilungszeilen %d · Kerzen %d" % tuple(c.execute("SELECT (SELECT COUNT(*) FROM tag), (SELECT COUNT(*) FROM verteilung), "
                                                                         "(SELECT COUNT(*) FROM kerze)").fetchone()))
    c.close()


if __name__ == "__main__":
    if "--laden" in sys.argv:
        n = int(sys.argv[sys.argv.index("--lader") + 1]) if "--lader" in sys.argv else 8
        sys.exit(1 if laden(n) else 0)
    elif "--kerzen" in sys.argv:
        kerzen()
    elif "--bericht" in sys.argv:
        bericht()
    else:
        print(__doc__)
