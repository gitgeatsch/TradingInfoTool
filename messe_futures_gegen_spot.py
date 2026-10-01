"""Frage 3 der Datenbasis (Basisinfos/Voranalyse_Datenbasis_alle_Assets_01_10.md Abschnitt 3): sind FUTURES-Kurse fuer die REGEL0 gleichwertig?

Fuer 20 Assets mit Spot UND Futures bei Binance (aus der Messbasis, gleichmaessig ueber die Liquiditaet, Saat fest) werden 2025-01..2026-08
stuendlich verglichen: Spot aus ``data/stundenkurse.db`` (nur lesen), Futures (Last Price, USDT-Perpetual) frisch von der oeffentlichen
Schnittstelle (``fapi/v1/klines``, Gewicht gering). Nichts wird gespeichert ausser der Ausgabe.

Gleichwertig, wenn ALLE vier gelten (Median ueber die Assets):
    Stundenrendite Korrelation >= 0,99 · rsi14 Median |d| <= 1,0 und P95 <= 3,0 · ATR relativ Futures/Spot 0,95..1,05 · Rendite 24 h Median |d| <= 0,10 Pp

    python messe_futures_gegen_spot.py [--probe]
"""
from __future__ import annotations

import os
import sqlite3
import sys
import time
from datetime import datetime, timezone

import numpy as np
import pandas as pd
import requests

HIER = os.path.dirname(os.path.abspath(__file__))
URL = "https://fapi.binance.com/fapi/v1/klines"
VON, BIS = "2025-01-01 00:00", "2026-08-31 23:00"


def rsi14(cc):
    d = np.diff(cc, prepend=cc[0])
    auf = pd.Series(np.where(d > 0, d, 0.0)).rolling(14, min_periods=14).sum() / 14
    ab = pd.Series(np.where(d < 0, -d, 0.0)).rolling(14, min_periods=14).sum() / 14
    with np.errstate(divide="ignore", invalid="ignore"):
        return (100 - 100 / (1 + auf / ab)).to_numpy()


def atr_rel(h, l, cc):
    return pd.Series((h - l) / cc).rolling(24, min_periods=24).mean().to_numpy() * np.sqrt(24.0)


def futures(sym):
    t0 = int(datetime.strptime(VON, "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc).timestamp() * 1000)
    t1 = int(datetime.strptime(BIS, "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc).timestamp() * 1000)
    aus = {}
    while t0 <= t1:
        r = requests.get(URL, params={"symbol": sym + "USDT", "interval": "1h", "startTime": t0, "endTime": t1, "limit": 1500}, timeout=30)
        r.raise_for_status()
        k = r.json()
        if not k:
            break
        for x in k:
            aus[datetime.fromtimestamp(x[0] / 1000, timezone.utc).strftime("%Y-%m-%d %H:%M")] = (float(x[2]), float(x[3]), float(x[4]))
        t0 = k[-1][0] + 3600 * 1000
        time.sleep(0.15)
    return aus


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:                                         # noqa: BLE001
        pass
    probe = "--probe" in sys.argv
    fi = requests.get("https://fapi.binance.com/fapi/v1/exchangeInfo", timeout=30).json()
    fut = {x["baseAsset"] for x in fi["symbols"] if x["quoteAsset"] == "USDT" and x.get("contractType") == "PERPETUAL" and x["status"] == "TRADING"}
    c = sqlite3.connect("file:%s?mode=ro" % os.path.join(HIER, "data", "stundenkurse.db").replace("\\", "/"), uri=True)
    vol = c.execute("SELECT symbol, AVG(close * volumen) FROM stundenkurse WHERE stunde BETWEEN ? AND ? GROUP BY symbol HAVING COUNT(*) > 10000",
                    (VON, BIS)).fetchall()
    kand = sorted([(v, s) for s, v in vol if s in fut and s != "BTC"])
    rng = np.random.default_rng(20261001)
    # gleichmaessig ueber die Liquiditaet: je ein Asset aus 20 gleich grossen Abschnitten
    teile = np.array_split(np.arange(len(kand)), 3 if probe else 20)
    wahl = [kand[int(rng.choice(t))][1] for t in teile if len(t)]
    print("=" * 110)
    print("FUTURES GEGEN SPOT · %d Assets (Saat 20261001, gleichmaessig ueber die Liquiditaet) · %s .. %s" % (len(wahl), VON, BIS))
    print("=" * 110)
    erg = []
    for s in wahl:
        sp = {r[0]: r[1:] for r in c.execute("SELECT stunde, high, low, close FROM stundenkurse WHERE symbol=? AND stunde BETWEEN ? AND ? ORDER BY stunde",
                                             (s, VON, BIS))}
        fu = futures(s)
        st = sorted(set(sp) & set(fu))
        if len(st) < 5000:
            print("  %-8s zu wenige gemeinsame Stunden (%d)" % (s, len(st)))
            continue
        hs, ls, cs = (np.array([sp[t][i] for t in st], float) for i in range(3))
        hf, lf, cf = (np.array([fu[t][i] for t in st], float) for i in range(3))
        r_s, r_f = np.diff(np.log(cs)), np.diff(np.log(cf))
        kor = float(np.corrcoef(r_s, r_f)[0, 1])
        dr = np.abs(rsi14(cs) - rsi14(cf)); dr = dr[np.isfinite(dr)]
        av = atr_rel(hf, lf, cf) / atr_rel(hs, ls, cs); av = av[np.isfinite(av)]
        d24 = np.abs((cs[24:] / cs[:-24] - 1) - (cf[24:] / cf[:-24] - 1))
        erg.append((s, kor, float(np.median(dr)), float(np.percentile(dr, 95)), float(np.median(av)), 100 * float(np.median(d24))))
        print("  %-8s %6d h · Korrelation %.4f · rsi |d| Median %.2f / P95 %.2f · ATR F/S %.3f · Rendite 24 h |d| %.3f Pp" % (s, len(st), *erg[-1][1:]))
    if not erg:
        print("SCHLUSS: vollstaendig")
        return 1
    m = [float(np.median([e[i] for e in erg])) for i in range(1, 6)]
    ok = [m[0] >= 0.99, m[1] <= 1.0 and m[2] <= 3.0, 0.95 <= m[3] <= 1.05, m[4] <= 0.10]
    print("  MEDIAN · Korrelation %.4f %s · rsi |d| %.2f / P95 %.2f %s · ATR F/S %.3f %s · Rendite 24 h |d| %.3f Pp %s" % (
        m[0], "✔" if ok[0] else "⛔", m[1], m[2], "✔" if ok[1] else "⛔", m[3], "✔" if ok[2] else "⛔", m[4], "✔" if ok[3] else "⛔"))
    sch = min(erg, key=lambda e: e[1])
    print("  schlechtestes Asset (Korrelation): %s %.4f · rsi P95 %.2f · ATR F/S %.3f" % (sch[0], sch[1], sch[3], sch[4]))
    print("  URTEIL: %s" % ("✔ GLEICHWERTIG - Futures-Kurse fuer Assets ohne Spot zulaessig" if all(ok) else "⛔ NICHT GLEICHWERTIG"))
    print("SCHLUSS: vollstaendig")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
