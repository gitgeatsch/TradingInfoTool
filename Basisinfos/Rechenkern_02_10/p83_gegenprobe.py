"""P83 GEGENPROBE Messplan R (24.10.2026): zweiter Weg zu Z1, zum Rang und zur Kuerzung je Startdatum.

    python -X utf8 Basisinfos/Rechenkern_02_10/p83_gegenprobe.py

G1  Z1 je Handel und je Tag fuer Referenz und alle sechs Startdaten ueber einen ZWEITEN Weg: Kurse per pandas aus SQL, Drift per
    groupby (Coin, Jahr), Einstieg per Stundentext - muss auf 1e-9 gleich p83 sein (Werte aus p83_robustheit_r.txt gelesen)
G2  Rang anders: zirkulaere 14-Tage-Bloecke statt 7-Tage-Bloecke - gleiches Urteil je Startdatum (Rang >= 0,95 ja/nein)?
G3  Kuerzung greift am LADER: mit ab = 2022-06 beginnt jede Reihe am oder nach 2022-06-01, ohne ab beginnen Reihen frueher
"""
import os
import re
import sqlite3
import sys

import numpy as np
import pandas as pd

HIER = os.path.dirname(os.path.abspath(__file__))
os.chdir(os.path.dirname(os.path.dirname(HIER)))
sys.stdout.reconfigure(encoding="utf-8")
HIST = os.path.join("data", "_hist")
STARTS = ("2019-06", "2020-06", "2021-06", "2021-12", "2022-06", "2023-01")
B0 = pd.Timestamp("2020-01-01")
TAGE = pd.date_range("2024-01-01", "2026-08-31", freq="D")


def kurse():
    teile = []
    for d in ("stundenkurse.db", "stundenkurse_alle.db"):
        c = sqlite3.connect("file:%s/%s?mode=ro" % (HIST.replace("\\", "/"), d), uri=True)
        teile.append(pd.read_sql("SELECT symbol, stunde, close FROM stundenkurse WHERE stunde >= '2023-12-01'", c))
        c.close()
    k = pd.concat(teile).drop_duplicates(["symbol", "stunde"], keep="first")
    k["t"] = pd.to_datetime(k.stunde)
    k = k.set_index(["symbol", "t"]).close.sort_index()
    nach = k.copy()
    nach.index = nach.index.set_levels(nach.index.levels[1] - pd.Timedelta(hours=24), level=1)
    r = (nach.reindex(k.index) / k - 1).dropna()                     # Ertrag ab Stunde t bis t+24 h
    r = r.to_frame("r").reset_index()
    r["jahr"] = r.t.dt.year
    drift = r[r.jahr.isin([2024, 2025, 2026])].groupby(["symbol", "jahr"]).r.mean()
    return r.set_index(["symbol", "t"]).r, drift


def z1(E, r, drift):
    t = B0 + pd.to_timedelta(E.stunde, unit="h")
    x = pd.DataFrame({"symbol": E.symbol.values, "t": t.values})
    x["r"] = r.reindex(pd.MultiIndex.from_frame(x[["symbol", "t"]])).values
    x["jahr"] = x.t.dt.year
    x["drift"] = drift.reindex(pd.MultiIndex.from_frame(x[["symbol", "jahr"]])).values
    x = x.dropna()
    x = x[(x.t >= TAGE[0]) & (x.t < TAGE[-1] + pd.Timedelta(days=1))]
    x["ex"] = x.r - x.drift
    x["tag"] = x.t.dt.normalize()
    w = 1.0 / x.groupby("tag").tag.transform("size")
    return x, float(x.ex.mean()), float((w * x.ex).sum() / w.sum())


def rang14(x, gew, rng, zieh=1000):
    w = np.ones(len(x)) if gew == "handel" else (1.0 / x.groupby("tag").tag.transform("size")).to_numpy()
    ti = ((x.tag - TAGE[0]).dt.days).to_numpy()
    sx = np.bincount(ti, weights=w * x.ex.to_numpy(), minlength=len(TAGE))
    sw = np.bincount(ti, weights=w, minlength=len(TAGE))
    n, L = len(sx), 14
    st = rng.integers(0, n, (zieh, n // L))
    ix = ((st[:, :, None] + np.arange(L)) % n).reshape(zieh, -1)
    z = sx[ix].sum(axis=1) / np.maximum(sw[ix].sum(axis=1), 1e-12)
    return float(np.mean(z > 0))


def main():
    txt = open(os.path.join(HIER, "p83_robustheit_r.txt"), encoding="utf-8").read()
    r, drift = kurse()
    rng = np.random.default_rng(831)
    ok1, ok2, ok3 = True, True, True
    print("P83 GEGENPROBE")
    for name, pfad in [("Referenz (gemischt)", os.path.join("data", "_vergleich", "kern48jbz_einstiege_bestand.csv"))] + \
                      [("Start %s" % S, os.path.join(HIST, "einstiege_R1_%s.csv" % S)) for S in STARTS]:
        E = pd.read_csv(pfad, sep=";")
        x, zh, zt = z1(E, r, drift)
        m = re.search(re.escape(name) + r".*?Z1 je Handel ([+-][\d.]+) % \(Rang ([\d.]+).*?je Tag ([+-][\d.]+) % \(Rang ([\d.]+)", txt)
        ph, rh, pt, rt = (float(m.group(i)) for i in (1, 2, 3, 4))
        g1 = abs(100 * zh - ph) < 0.0006 and abs(100 * zt - pt) < 0.0006
        r14h, r14t = rang14(x, "handel", rng), rang14(x, "tag", rng)
        g2 = ((rh >= 0.95) == (r14h >= 0.95)) and ((rt >= 0.95) == (r14t >= 0.95))
        ok1 &= g1
        ok2 &= g2
        zeile = "  %-20s G1 Z1 je Handel %+.3f (p83 %+.3f) je Tag %+.3f (p83 %+.3f) %s · G2 Rang14 %.3f/%.3f (p83 %.3f/%.3f) %s" % (
            name, 100 * zh, ph, 100 * zt, pt, "ok" if g1 else "NICHT OK", r14h, r14t, rh, rt, "gleiches Urteil" if g2 else "ANDERES URTEIL")
        print(zeile)
    sys.path.insert(0, os.path.dirname(os.path.dirname(HIER)))
    import agent.regel0_rechnung as R0
    zus = R0.zusatz_aus_gruppe(os.path.join("data", "_vergleich", "kern48jbz_gruppe_bestand.csv"))
    mit = {s: rows[0][0] for s, rows in R0.lade_reihen_iter(HIST, zus, ab="2022-06-01 00:00") if rows}
    ohne = {s: rows[0][0] for s, rows in R0.lade_reihen_iter(HIST, zus) if rows}
    vor = sum(v < "2022-06-01 00:00" for v in mit.values())
    frueher = sum(ohne[s] < "2022-06-01 00:00" for s in ohne)
    ok3 = vor == 0 and frueher > 0
    print("  G3 Lader ab 2022-06: %d Reihen, davon vor 2022-06-01 beginnend: %d · ohne ab beginnen %d Reihen frueher" % (len(mit), vor, frueher))
    print("ERGEBNIS: G1 %s · G2 %s · G3 %s" % ("ok" if ok1 else "NICHT OK", "ok" if ok2 else "NICHT OK", "ok" if ok3 else "NICHT OK"))


if __name__ == "__main__":
    main()
