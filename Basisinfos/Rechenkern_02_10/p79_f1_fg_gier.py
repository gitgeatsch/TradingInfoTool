"""P79 MESSPLAN F-1 FASSUNG 2 (Voranalyse_REGEL0_Historie_23_10.md §6, vorab 6623eab2; Auslegung §6.1): Fear & Greed > 75 am Vortag
-> REGEL0 nicht handeln. REGEL0-Einstiege 2020-07..2026-08 aus p78 (Lauf B + Lauf A, Menge bestand), Kosten 0,48 % je Handel.

    python -X utf8 Basisinfos/Rechenkern_02_10/p79_f1_fg_gier.py --selbsttest     nur Selbsttest (VOR dem ersten Blick)
    python -X utf8 Basisinfos/Rechenkern_02_10/p79_f1_fg_gier.py                  Selbsttest, bei Bestehen die Messung

Rechenweg wie p71 (strecken, permutiere, kennzahlen, rang - von dort importiert), nur auf dem Tagesraster 2020-07-01..2026-08-31 und
mit den Kursen aus data/_hist (sonst fehlten 2020-2023). Liest nur; schreibt data/_ra/p79_fng.csv (Cache) und die Ausgabe.
"""
import os
import sqlite3
import sys

import numpy as np
import pandas as pd

HIER = os.path.dirname(os.path.abspath(__file__))
WURZEL = os.path.dirname(os.path.dirname(HIER))
sys.path.insert(0, HIER)
sys.path.insert(0, WURZEL)
os.chdir(WURZEL)
import p71_marktfilter as P71  # noqa: E402

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:  # noqa: BLE001
    pass
KOSTEN = P71.KOSTEN
B0 = pd.Timestamp("2020-01-01")
TAGE = pd.date_range("2020-07-01", "2026-08-31", freq="D")
ALLE = np.ones(len(TAGE), bool)
HALB = [(j, h) for j in range(2020, 2025) for h in (1, 2) if (j, h) >= (2020, 2)]          # 9 Halbjahre 2020-H2..2024-H2
FNG = os.path.join("data", "_ra", "p79_fng.csv")
HIST = os.path.join("data", "_hist")


def halbjahr(j, h):
    return (TAGE.year == j) & ((TAGE.month <= 6) if h == 1 else (TAGE.month >= 7))


# ── Handel ──────────────────────────────────────────────────────────────────────────────────────────────────────────────
def einstiege():
    a = pd.read_csv(os.path.join(HIST, "einstiege_A.csv"), sep=";")
    b = pd.read_csv(os.path.join(HIST, "einstiege_B.csv"), sep=";")
    assert a.jahr.min() >= 2024 and b.jahr.max() <= 2023
    return pd.concat([b, a], ignore_index=True)


def tagesreihe(E):
    con = [sqlite3.connect("file:%s/%s?mode=ro" % (HIST.replace("\\", "/"), d), uri=True) for d in ("stundenkurse.db", "stundenkurse_alle.db")]
    netto, tag, fehlt = [], [], 0
    for s, g in E.groupby("symbol"):
        d = {}
        for c in con:
            for st, cl in c.execute("SELECT stunde, close FROM stundenkurse WHERE symbol=?", (s,)):
                d.setdefault(st, cl)
        hs = ((pd.to_datetime(list(d.keys())) - B0) / pd.Timedelta(hours=1)).astype(int).to_numpy()
        a0 = hs.min()
        C = np.full(hs.max() - a0 + 1, np.nan)
        C[hs - a0] = np.array(list(d.values()), float)
        for st in g.stunde:
            i = int(st) - a0
            if 0 <= i and i + 24 < len(C) and np.isfinite(C[i]) and np.isfinite(C[i + 24]):
                netto.append(C[i + 24] / C[i] - 1 - KOSTEN)
                tag.append((B0 + pd.Timedelta(hours=int(st))).normalize())
            else:
                fehlt += 1
    D = pd.DataFrame({"netto": netto, "tag": tag})
    g = D.groupby("tag").netto.agg(["sum", "count"]).reindex(TAGE).fillna(0.0)
    return g["sum"].to_numpy(), g["count"].to_numpy(), fehlt


# ── Filter ──────────────────────────────────────────────────────────────────────────────────────────────────────────────
def fng():
    if not os.path.exists(FNG):
        import requests
        r = requests.get("https://api.alternative.me/fng/", params={"limit": 0, "format": "json"}, timeout=60)
        d = r.json()["data"]
        s = pd.Series({pd.Timestamp(int(x["timestamp"]), unit="s").normalize(): int(x["value"]) for x in d}).sort_index()
        s.rename("fng").to_csv(FNG)
    return pd.read_csv(FNG, index_col=0, parse_dates=True).iloc[:, 0]


def filter_fg():
    fg = fng().reindex(pd.date_range("2018-01-01", "2026-10-23", freq="D"))
    vortag = fg.shift(1)                                                          # Zustand des Vortags
    gier = (vortag > 75)
    z = (~gier).astype(int).where(vortag.notna(), 1)                              # fehlender Wert -> an (wie p71)
    # Auskunft 1: 30 T nach einem Wechsel auf Gier aus
    wechsel = (vortag > 75) & (vortag.shift(1) <= 75)
    sperre = pd.Series(0, index=fg.index)
    for t in fg.index[wechsel.fillna(False).to_numpy()]:
        sperre.loc[t:t + pd.Timedelta(days=29)] = 1
    z30 = (1 - sperre)
    z50 = (vortag < 50).astype(int).where(vortag.notna(), 1)
    return {"FG-Gier aus (Vortag > 75)": z.reindex(TAGE).to_numpy(),
            "Auskunft: 30 T nach Wechsel auf Gier aus": z30.reindex(TAGE).to_numpy(),
            "Auskunft: nur bei F&G < 50 an": z50.reindex(TAGE).to_numpy()}, vortag


# ── Urteil ──────────────────────────────────────────────────────────────────────────────────────────────────────────────
def urteil(z, s, n, rng, k=1000):
    an, aus, alle, *_ = P71.kennzahlen(z, s, n, ALLE)
    k1 = an > 0 and aus < 0
    j25 = P71.kennzahlen(z, s, n, TAGE.year == 2025)[0] > 0
    j26 = P71.kennzahlen(z, s, n, TAGE.year == 2026)[0] > 0
    hj = sum(P71.kennzahlen(z, s, n, halbjahr(j, h))[0] > 0 for j, h in HALB)
    k2 = j25 and j26 and hj >= 6
    rg = P71.rang(z, s, n, ALLE, rng, k)
    return k1 and k2 and rg >= 0.95, dict(an=an, aus=aus, alle=alle, k1=k1, j25=j25, j26=j26, hj=hj, k2=k2, rang=rg)


def main():
    print("P79 F-1 FASSUNG 2 · FG-Gier · REGEL0 bestand 2020-07..2026-08 · Kosten 0,48 %\n")
    E = einstiege()
    s, n, fehlt = tagesreihe(E)
    print("Einstiege %d (Lauf B %d, Lauf A %d) · mit 24-h-Ergebnis %d · ohne Kurs %d" % (
        len(E), int((E.jahr <= 2023).sum()), int((E.jahr >= 2024).sum()), int(n.sum()), fehlt))
    print("Handel je Jahr: %s\n" % {j: int(n[TAGE.year == j].sum()) for j in range(2020, 2027)})
    F, vortag = filter_fg()
    z = F["FG-Gier aus (Vortag > 75)"]
    rng = np.random.default_rng(79)
    # SELBSTTEST VOR DEM ERSTEN BLICK - der echte Filter geht nur mit seiner Streckenstruktur ein (Permutation)
    fehl = 0
    for i in range(200):
        fehl += int(urteil(P71.permutiere(z, rng), s, n, rng, k=200)[0])
    tn = pd.Series(np.where(n > 0, s / np.maximum(n, 1), 0.0), index=TAGE).rolling(31, center=True, min_periods=5).mean()
    zo = (tn > 0).astype(int).to_numpy()
    r_o = P71.rang(zo, s, n, ALLE, rng, 1000)
    ok_a, ok_b = fehl / 200 <= 0.05, r_o >= 0.95
    print("SELBSTTEST (a) Fehlalarm %d von 200 Zufallsfiltern mit der Streckenstruktur von FG-Gier (%.1f %%, Soll <= 5 %%) -> %s"
          % (fehl, 100 * fehl / 200, "ok" if ok_a else "NICHT OK"))
    print("SELBSTTEST (b) Orakel (zentrierter 30-T-Mittelwert > 0): Rang %.3f (Soll >= 0,95) -> %s"
          % (r_o, "ok" if ok_b else "NICHT OK"))
    if not ok_b:
        print("\nURTEIL: NICHT ENTSCHEIDBAR (Orakel nicht erkannt) - der Filter wird nicht angesehen (§6).")
        return
    if not ok_a:
        print("\nSelbsttest (a) nicht bestanden - die Anlage alarmiert zu oft; es wird NICHT gemessen.")
        return
    if "--selbsttest" in sys.argv:
        return
    print()
    for name, zz in F.items():
        tr, d = urteil(zz, s, n, rng)
        kopf = "URTEIL" if not name.startswith("Auskunft") else "Auskunft"
        print("=== %s · Anteil an %.0f %% · Wechsel %d" % (name, 100 * zz.mean(), int(np.abs(np.diff(zz)).sum())))
        print("   (1) Umkehr: an %+.3f %% · aus %+.3f %% · alle %+.3f %% -> %s" % (100 * d["an"], 100 * d["aus"], 100 * d["alle"], d["k1"]))
        print("   (2) an > 0: 2025 %s · 2026 %s · Halbjahre 2020-H2..2024-H2 %d von 9 (Soll >= 6) -> %s" % (d["j25"], d["j26"], d["hj"], d["k2"]))
        print("   (3) Rang %.3f (Soll >= 0,95)" % d["rang"])
        if kopf == "URTEIL":
            print("   -> %s: %s" % (kopf, "TRAEGT" if tr else "traegt nicht"))
        teile = []
        for j in range(2020, 2027):
            an, aus, alle, ta, *_ = P71.kennzahlen(zz, s, n, TAGE.year == j)
            teile.append("%d an %+.2f / aus %+.2f (Tage aus %d)" % (j, 100 * an, 100 * aus, ta))
        print("   je Jahr: " + " | ".join(teile))
        print("   je Halbjahr an: " + " ".join("%d-H%d %+.2f" % (j, h, 100 * P71.kennzahlen(zz, s, n, halbjahr(j, h))[0]) for j, h in HALB))
        print()
    # Auskunft: die sechs Filter aus E-133 (ohne Urteil), lang gerechnet
    F6 = filter_e133_lang()
    for name in F6.columns:
        zz = F6[name].reindex(TAGE).fillna(1).astype(int).to_numpy()
        an, aus, alle, ta, *_ = P71.kennzahlen(zz, s, n, ALLE)
        je = " ".join("%d %+.2f/%+.2f" % (j, 100 * P71.kennzahlen(zz, s, n, TAGE.year == j)[0], 100 * P71.kennzahlen(zz, s, n, TAGE.year == j)[1])
                      for j in range(2020, 2027))
        print("Auskunft E-133 %-28s an %+.3f / aus %+.3f / alle %+.3f (Tage aus %d) · je Jahr an/aus %s"
              % (name, 100 * an, 100 * aus, 100 * alle, ta, je))


def filter_e133_lang():
    """Die sechs Filter aus p71.filter_tabelle (E-133), gleiche Regeln, nur ab 2020-06 statt 2023-06 (Nasdaq ab 2018 fuer 200 T)."""
    cache = os.path.join("data", "_ra", "p79_e133.csv")
    if os.path.exists(cache):
        return pd.read_csv(cache, index_col=0, parse_dates=True)
    import requests
    from dotenv import dotenv_values
    from agent import makro_lage as M
    key = dotenv_values(".env").get("FRED_API_KEY")
    roh = M.hole_alle(key, heute=pd.Timestamp("2026-10-23").date())
    idx = pd.date_range("2012-01-01", "2026-10-23", freq="D")
    S = M.scores(roh, idx)
    r = requests.get("https://api.stlouisfed.org/fred/series/observations", timeout=60,
                     params={"series_id": "NASDAQCOM", "api_key": key, "file_type": "json", "observation_start": "2018-01-01"})
    obs = [(o["date"], float(o["value"])) for o in r.json()["observations"] if o["value"] not in (".", "")]
    nq = pd.Series([v for _, v in obs], index=pd.to_datetime([d for d, _ in obs]) + pd.Timedelta(days=1))
    nq_an = (nq > nq.rolling(200).mean()).where(nq.rolling(200).count() == 200)
    c = sqlite3.connect("file:data/_spot/coinmetrics.db?mode=ro", uri=True)
    btc = pd.read_sql("SELECT tag, PriceUSD FROM tag WHERE asset='btc' AND PriceUSD IS NOT NULL", c, parse_dates=["tag"]).set_index("tag").PriceUSD
    c.close()
    btc_an = (btc > btc.rolling(200).mean()).where(btc.rolling(200).count() == 200)
    F = pd.DataFrame(index=idx)
    F["F1 Makro Gesamt kurz"] = S["Gesamt kurz"] != -1
    F["F2 Makro Gesamt lang"] = S["Gesamt lang"] != -1
    F["F3 Netto-Liquiditaet kurz"] = S["K2 Netto-Liquiditaet kurz"] != -1
    F["F4 Dollar kurz"] = S["K8 Dollar kurz"] != -1
    F["F5 Nasdaq ueber 200 T"] = nq_an.reindex(idx).ffill().fillna(1.0) == 1.0
    F["F6 BTC ueber 200 T"] = btc_an.reindex(idx).ffill().fillna(1.0) == 1.0
    F = F.shift(1).loc["2020-06-01":"2026-09-30"].fillna(True).astype(int)
    F.to_csv(cache)
    return F


if __name__ == "__main__":
    main()
