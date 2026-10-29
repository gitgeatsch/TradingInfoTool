# -*- coding: utf-8 -*-
"""G16 Wale, VOLLER Download (29.10.2026, Nutzer: *„Ok a, BTC und ETH voll laden“*, Voranalyse_Wale_29_10.md §7).

Dieselbe Verdichtung wie die Stichprobe (``wale_stichprobe.py``: aggTrade und SWEEP, Viertel-Dekaden-Klassen in USD), dazu
**je Stunde** (nur Sweeps) — damit die Rohdateien nie wieder gebraucht werden: D: hat 92 GB frei, die Rohdaten sind ~100 GB.
Die Rohdatei wird im Speicher gelesen und nicht gespeichert.

    Werte      BTCUSDT, ETHUSDT · Spot und USDⓈ-M-Futures · 01.01.2023 bis gestern
    Ablage     data/_wale/wale_voll.db (WAL, vier Lader gleichzeitig möglich)
    Abgleich   Tagesumsatz gegen die REST-Tageskerze (das Archiv hat abgeschnittene Kerzen — hier gilt REST);
               dazu erste/letzte Geschäftszeit des Tages (eine abgeschnittene Datei fällt dort auf)

    python -X utf8 Basisinfos/Rechenkern_02_10/wale_voll.py --markt spot --symbol BTCUSDT   # ein Lader (setzt fort)
    python -X utf8 Basisinfos/Rechenkern_02_10/wale_voll.py --bericht                       # Vollständigkeit und Abgleich
"""
import os
import sqlite3
import sys
from datetime import date, datetime, timedelta, timezone

import numpy as np

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HIER)
import wale_stichprobe as WS  # noqa: E402

ABLAGE = os.path.join(WS.PROJ, "data", "_wale", "wale_voll.db")
START = date(2023, 1, 1)
SYMBOLE = ("BTCUSDT", "ETHUSDT")


def verbinde():
    os.makedirs(os.path.dirname(ABLAGE), exist_ok=True)
    c = sqlite3.connect(ABLAGE, timeout=300)
    c.execute("PRAGMA journal_mode=WAL")
    c.executescript("""
    CREATE TABLE IF NOT EXISTS tag (symbol TEXT, markt TEXT, datum TEXT, umsatz_usd REAL, kauf_usd REAL, aggtrades INTEGER,
                                    sweeps INTEGER, kerze_usd REAL, kerze_kauf_usd REAL, erste_utc TEXT, letzte_utc TEXT, geholt TEXT,
                                    PRIMARY KEY (symbol, markt, datum));
    -- einheit 'agg'|'sweep', seite 'kauf' (Taker kauft)|'verkauf', klasse k = Untergrenze 10^(k/4) USD
    CREATE TABLE IF NOT EXISTS verteilung (symbol TEXT, markt TEXT, datum TEXT, einheit TEXT, seite TEXT, klasse INTEGER,
                                           anzahl INTEGER, usd REAL, PRIMARY KEY (symbol, markt, datum, einheit, seite, klasse));
    -- nur Sweeps, Stunde 0-23 UTC
    CREATE TABLE IF NOT EXISTS stunde (symbol TEXT, markt TEXT, datum TEXT, stunde INTEGER, seite TEXT, klasse INTEGER,
                                       anzahl INTEGER, usd REAL, PRIMARY KEY (symbol, markt, datum, stunde, seite, klasse));
    """)
    return c


def kerzen(markt: str, symbol: str, bis: date) -> dict:
    """Alle REST-Tageskerzen ab START in wenigen Abrufen: datum -> (Quote-Umsatz, Taker-Kauf-Quote-Umsatz)."""
    aus, ab = {}, int(datetime(START.year, START.month, START.day, tzinfo=timezone.utc).timestamp() * 1000)
    grenze = 1000 if markt == "spot" else 500
    while True:
        r = WS._hole(WS.MAERKTE[markt][1], {"symbol": symbol, "interval": "1d", "startTime": ab, "limit": grenze})
        if r is None:
            raise RuntimeError("REST-Kerzen %s %s nicht abrufbar" % (markt, symbol))
        k = r.json()
        for x in k:
            aus[datetime.fromtimestamp(x[0] / 1000, timezone.utc).strftime("%Y-%m-%d")] = (float(x[7]), float(x[10]))
        if len(k) < grenze or datetime.fromtimestamp(k[-1][0] / 1000, timezone.utc).date() >= bis:
            return aus
        ab = k[-1][0] + 86400000


def stunden(df) -> list:
    """Sweeps je Stunde und Klasse. ⚠️ Spot-Zeitstempel ab 2025 in MIKROsekunden, davor und bei Futures in Millisekunden."""
    zeit = df["zeit"].to_numpy()
    ms = zeit // 1000 if zeit.max() > 1e14 else zeit
    usd = (df["preis"] * df["menge"]).to_numpy()
    kauf = ~df["kaeufer_maker"].to_numpy()
    neu = np.r_[True, (zeit[1:] != zeit[:-1]) | (kauf[1:] != kauf[:-1])]
    gruppe = np.cumsum(neu) - 1
    sw_usd = np.bincount(gruppe, weights=usd)
    sw_kauf, sw_h = kauf[neu], ((ms[neu] // 3600000) % 24).astype(int)
    kl = np.clip(np.floor(4 * np.log10(np.maximum(sw_usd, 1.0))).astype(int), 0, WS.KLASSEN - 1)
    zeilen = []
    for seite, maske in (("kauf", sw_kauf), ("verkauf", ~sw_kauf)):
        schl = sw_h[maske] * WS.KLASSEN + kl[maske]
        n = np.bincount(schl, minlength=24 * WS.KLASSEN)
        s = np.bincount(schl, weights=sw_usd[maske], minlength=24 * WS.KLASSEN)
        zeilen += [(int(i // WS.KLASSEN), seite, int(i % WS.KLASSEN), int(n[i]), float(s[i])) for i in np.nonzero(n)[0]]
    return zeilen, int(ms.min()), int(ms.max())


def _utc(ms: int) -> str:
    return datetime.fromtimestamp(ms / 1000, timezone.utc).isoformat(timespec="seconds")


def lade(markt: str, symbol: str) -> int:
    c = verbinde()
    bis = date.today() - timedelta(days=1)
    fertig = {d for (d,) in c.execute("SELECT datum FROM tag WHERE symbol=? AND markt=?", (symbol, markt))}
    kz = kerzen(markt, symbol, bis)
    fehlt, d = 0, START
    while d <= bis:
        datum, d = d.isoformat(), d + timedelta(days=1)
        if datum in fertig:
            continue
        df = WS.lies_tag(markt, datum, symbol)
        if df is None:
            fehlt += 1
            print("  ✖ %s %s %s nicht abrufbar" % (symbol, markt, datum), flush=True)
            continue
        umsatz, kauf, n_agg, n_sw, zeilen = WS.verdichte(df)
        st, erste, letzte = stunden(df)
        ku, kk = kz.get(datum, (None, None))
        c.execute("INSERT OR REPLACE INTO tag VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                  (symbol, markt, datum, umsatz, kauf, n_agg, n_sw, ku, kk, _utc(erste), _utc(letzte),
                   datetime.now(timezone.utc).isoformat(timespec="seconds")))
        c.executemany("INSERT OR REPLACE INTO verteilung VALUES (?,?,?,?,?,?,?,?)", [(symbol, markt, datum) + z for z in zeilen])
        c.executemany("INSERT OR REPLACE INTO stunde VALUES (?,?,?,?,?,?,?,?)", [(symbol, markt, datum) + z for z in st])
        c.commit()
        print("  ✔ %s %-7s %s  %9d agg  %8d Sweeps  %6.2f Mrd $  Kerze %s" % (
            symbol, markt, datum, n_agg, n_sw, umsatz / 1e9, "%.2f" % (ku / 1e9) if ku else "–"), flush=True)
        del df
    c.close()
    print("ENDE %s %s: %d Tage nicht abrufbar" % (symbol, markt, fehlt), flush=True)
    return fehlt


def bericht():
    c = sqlite3.connect("file:%s?mode=ro" % ABLAGE.replace("\\", "/"), uri=True)
    bis = date.today() - timedelta(days=1)
    soll = (bis - START).days + 1
    print("VOLLSTÄNDIGKEIT und ABGLEICH gegen die REST-Kerze (Soll %d Tage je Reihe, %s bis %s)" % (soll, START, bis))
    for sym, markt, n, lo, hi, ohne in c.execute("""SELECT symbol, markt, COUNT(*), MIN(umsatz_usd/kerze_usd), MAX(umsatz_usd/kerze_usd),
                                                    SUM(kerze_usd IS NULL) FROM tag GROUP BY symbol, markt"""):
        print("  %s %-7s %4d/%d Tage  Archiv/Kerze %.4f .. %.4f  ohne Kerze %d" % (sym, markt, n, soll, lo or 0, hi or 0, ohne))
    ab = c.execute("""SELECT symbol, markt, datum, umsatz_usd/kerze_usd, erste_utc, letzte_utc FROM tag
                      WHERE ABS(umsatz_usd/kerze_usd - 1) > 0.005 OR substr(erste_utc,12,5) > '00:05' OR substr(letzte_utc,12,5) < '23:55'
                      ORDER BY 1, 2, 3""").fetchall()
    print("\nAUFFÄLLIGE TAGE (Umsatz > 0,5 %% neben der Kerze oder Datei deckt den Tag nicht ab): %d" % len(ab))
    for z in ab[:40]:
        print("  %s %-7s %s  Archiv/Kerze %.4f  %s .. %s" % z)
    sw = c.execute("""SELECT COUNT(*) FROM (SELECT t.symbol, t.markt, t.datum, ABS(SUM(s.usd) / t.umsatz_usd - 1) a FROM tag t
                      JOIN stunde s USING (symbol, markt, datum) GROUP BY 1, 2, 3 HAVING a > 1e-6)""").fetchone()[0]
    print("\nStunden summieren sich NICHT zum Tagesumsatz: %d Tage" % sw)
    c.close()


if __name__ == "__main__":
    if "--bericht" in sys.argv:
        bericht()
    else:
        a = sys.argv
        lade(a[a.index("--markt") + 1], a[a.index("--symbol") + 1])
