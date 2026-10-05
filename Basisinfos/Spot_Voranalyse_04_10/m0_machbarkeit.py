"""Spot M-0 Machbarkeit (E-59, Voranalyse_Spot_Neubau_04_10.md §7) - misst GENAU nach dem vorab festgelegten Messplan §7.2.

    python Basisinfos/Spot_Voranalyse_04_10/m0_machbarkeit.py [a] [b] [c]      (ohne Angabe: alle drei)

Nur lesend (mode=ro) gegen die Messbasis data/stundenkurse.db (116 Assets, eingestellte eingeschlossen), kein Netz, kein LLM, kein
Betriebscode (T-2, T-5). Urteil ab 2024: Wahl 2024, Bestaetigung 2025 und 2026 je Jahr.

M-0a  Welches: 6 Kursmerkmale x 20/90 Tage. Mass = Tagesrang des Folgeertrags, oberes minus unteres Fuenftel des Merkmals, Mittel
      ueber die Tage des Jahres. Nullwelt: das Merkmal je Asset zirkulaer verschoben (40 Verschuebe >= 60 Tage).
      tragfaehig: 2024 ueber dem 95. Perzentil der Nullwelt UND 2025, 2026 gleiches Vorzeichen, mindestens eines ueber dem 95.
      (Der umgekehrte Rand - unter dem 5. Perzentil - steht als AUSKUNFT daneben; er ist nicht vorab als Erfolg festgelegt.)
M-0b  Ob: marktweite Merkmale am Monatsende gegen den Median-Ertrag aller Assets der naechsten 30 Tage (Spearman), Monate ab 2024.
      Nullwelt: zirkulaerer Verschub der Zielreihe. tragfaehig: p < 0,05 UND gleiches Vorzeichen in beiden Haelften.
M-0c  L3: REGEL0-Einstiege (Referenz kern48jbz_einstiege_bestand.csv) ohne Hebel, 72 h / 120 h / 480 h gehalten, Rang gegen alle
      Einstiegsstunden desselben Assets im selben Monat. Nullwelt: je Einstieg eine Zufallsstunde desselben Assets und Monats (200x).
      tragfaehig: 2024 ueber dem 95. Perzentil des Zufalls UND 2025, 2026 gleiches Vorzeichen, mindestens eines ueber dem 95.
"""
import csv
import os
import sqlite3
import sys

import numpy as np
import pandas as pd

os.chdir(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
RNG = np.random.default_rng(20261005)
JAHRE = (2024, 2025, 2026)
B0 = pd.Timestamp("2020-01-01")


def ro(p):
    return sqlite3.connect("file:%s?mode=ro" % p.replace("\\", "/"), uri=True)


def tage():
    c = ro("data/stundenkurse.db")
    d = pd.read_sql("SELECT symbol, stunde, close, volumen FROM stundenkurse WHERE stunde >= '2022-06-01'", c)
    c.close()
    d["tag"] = pd.to_datetime(d["stunde"].str[:10])
    K = d[d["stunde"].str[11:13] == "23"].pivot(index="tag", columns="symbol", values="close").sort_index().asfreq("D")
    V = d.groupby(["tag", "symbol"])["volumen"].sum().unstack().reindex(K.index)
    return K, V


def rsi(K, n=14):
    r = K.diff()
    auf = r.clip(lower=0).ewm(alpha=1 / n, adjust=False).mean()
    ab = (-r.clip(upper=0)).ewm(alpha=1 / n, adjust=False).mean()
    return 100 - 100 / (1 + auf / ab)


def merkmale(K, V):
    lr = np.log(K).diff()
    return {"schnitt200": K / K.rolling(200, min_periods=200).mean() - 1,
            "momentum60": K / K.shift(60) - 1,
            "momentum250": K / K.shift(250) - 1,
            "rsi14": rsi(K),
            "schwankung30": lr.rolling(30, min_periods=25).std(),
            "volumen_rel30": V / V.rolling(30, min_periods=25).mean()}


def spreizung(M, RANG, jahr_idx):
    """oberes minus unteres Fuenftel (Tagesrang des Folgeertrags), Mittel je Jahr."""
    q = M.rank(axis=1, pct=True)
    gueltig = RANG.notna() & q.notna()
    oben = RANG.where(gueltig & (q > 0.8)).mean(axis=1)
    unten = RANG.where(gueltig & (q <= 0.2)).mean(axis=1)
    s = oben - unten
    return {j: float(s[jahr_idx == j].mean()) for j in JAHRE}


def m0a(K, V):
    print("== M-0a Welches (Querschnitt) - 6 Merkmale x 2 Horizonte = 12 Tests, ~0,6 Zufallstreffer erwartet", flush=True)
    jahr = K.index.year
    erg = []
    for h in (20, 90):
        R = K.shift(-h) / K - 1
        RANG = R.rank(axis=1, pct=True)
        for name, M in merkmale(K, V).items():
            echt = spreizung(M, RANG, jahr)
            null = {j: [] for j in JAHRE}
            n = len(M)
            for _ in range(40):
                Mv = pd.DataFrame({s: np.roll(M[s].values, int(RNG.integers(60, n - 60))) for s in M.columns}, index=M.index)
                for j, v in spreizung(Mv, RANG, jahr).items():
                    null[j].append(v)
            p95 = {j: float(np.nanpercentile(null[j], 95)) for j in JAHRE}
            p05 = {j: float(np.nanpercentile(null[j], 5)) for j in JAHRE}
            ueber = {j: echt[j] > p95[j] for j in JAHRE}
            unter = {j: echt[j] < p05[j] for j in JAHRE}
            traegt = (ueber[2024] and echt[2025] > 0 and echt[2026] > 0 and (ueber[2025] or ueber[2026]))
            umgekehrt = (unter[2024] and echt[2025] < 0 and echt[2026] < 0 and (unter[2025] or unter[2026]))
            erg.append((name, h, traegt))
            print("  %-14s %3d T | %s | %s%s" % (name, h, " ".join("%d %+.3f (N95 %+.3f)" % (j, echt[j], p95[j]) for j in JAHRE),
                                              "TRAEGT" if traegt else "traegt nicht",
                                              " · AUSKUNFT: umgekehrt in allen drei Jahren am unteren Rand" if umgekehrt else ""), flush=True)
    t = [e for e in erg if e[2]]
    print("  -> tragfaehig: %s" % (", ".join("%s %d T" % (a, b) for a, b, _ in t) or "KEIN Kandidat"), flush=True)
    return t


def m0b(K):
    print("== M-0b Ob (Niveau) - Monatsende ab 2024, Ziel: Median-Ertrag aller Assets der naechsten 30 Tage", flush=True)
    me = K.groupby(K.index.to_period("M")).apply(lambda x: x.index.max())
    me = pd.DatetimeIndex([t for t in me if t >= pd.Timestamp("2024-01-01")])
    R30 = (K.shift(-30) / K - 1).median(axis=1)
    sma = K.rolling(200, min_periods=200).mean()
    kand = {"BTC Abstand Schnitt": (K["BTC"] / sma["BTC"] - 1) if "BTC" in K else None,
            "Marktbreite (Anteil ueber Schnitt)": (K > sma).where(sma.notna()).mean(axis=1),
            "Median-Momentum 60 T": (K / K.shift(60) - 1).median(axis=1)}
    t = []
    for name, X in kand.items():
        if X is None:
            continue
        x, y = X.reindex(me), R30.reindex(me)
        ok = x.notna() & y.notna()
        x, y = x[ok].values, y[ok].values
        n = len(x)
        if n < 12:
            print("  %-36s zu wenige Monate (%d)" % (name, n))
            continue
        rx, ry = pd.Series(x).rank().values, pd.Series(y).rank().values
        rho = float(np.corrcoef(rx, ry)[0, 1])
        null = [float(np.corrcoef(rx, np.roll(ry, k))[0, 1]) for k in range(1, n)]
        p = float(np.mean(np.abs(null) >= abs(rho)))
        hz = n // 2
        r1 = float(np.corrcoef(rx[:hz], ry[:hz])[0, 1]); r2 = float(np.corrcoef(rx[hz:], ry[hz:])[0, 1])
        traegt = p < 0.05 and np.sign(r1) == np.sign(r2) == np.sign(rho)
        if traegt:
            t.append(name)
        print("  %-36s Monate %d | rho %+.2f | p %.3f | Haelften %+.2f / %+.2f | %s (nachweisbar erst ab etwa |rho| %.2f)" % (
            name, n, rho, p, r1, r2, "TRAEGT" if traegt else "traegt nicht", float(np.nanpercentile(np.abs(null), 95))), flush=True)
    print("  -> tragfaehig: %s" % (", ".join(t) or "KEIN Kandidat"), flush=True)
    return t


def m0c():
    print("== M-0c L3 - REGEL0-Einstieg ohne Hebel, laenger gehalten (Rang gegen Zufallsstunden desselben Assets und Monats)", flush=True)
    c = ro("data/stundenkurse.db")
    d = pd.read_sql("SELECT symbol, stunde, close FROM stundenkurse WHERE stunde >= '2023-12-01'", c)
    c.close()
    d["h"] = ((pd.to_datetime(d["stunde"]) - B0) / pd.Timedelta(hours=1)).astype(int)
    H = d.pivot(index="h", columns="symbol", values="close").sort_index()
    H = H.reindex(range(H.index.min(), H.index.max() + 1))
    ein = []
    with open("data/_vergleich/kern48jbz_einstiege_bestand.csv", encoding="utf-8") as f:
        for z in csv.DictReader(f, delimiter=";"):
            if int(z["jahr"]) in JAHRE and z["symbol"] in H.columns:
                ein.append((z["symbol"], int(z["stunde"]) + 1))           # Einstieg zum Schlusskurs der Folgestunde (REGEL0)
    t = []
    for h in (72, 120, 480):
        R = H.shift(-h) / H - 1
        monat = pd.Series((B0 + pd.to_timedelta(R.index, unit="h")).to_period("M"), index=R.index)
        RP = R.groupby(monat.values).rank(pct=True)                     # Rang je Asset innerhalb seines Monats
        echt = {j: [] for j in JAHRE}
        for s, e in ein:
            if e in RP.index and not np.isnan(RP.at[e, s]):
                echt[(B0 + pd.Timedelta(hours=e)).year].append(RP.at[e, s])
        stunden_je = {}
        for s in {x[0] for x in ein}:
            g = RP[s].dropna()
            stunden_je[s] = g.groupby(monat.reindex(g.index).values).apply(lambda x: x.index.values).to_dict()
        null = {j: [] for j in JAHRE}
        for _ in range(200):
            z = {j: [] for j in JAHRE}
            for s, e in ein:
                if e not in RP.index or np.isnan(RP.at[e, s]):
                    continue
                kand = stunden_je[s].get(monat.at[e])
                if kand is None or not len(kand):
                    continue
                zz = kand[int(RNG.integers(0, len(kand)))]
                z[(B0 + pd.Timedelta(hours=e)).year].append(RP.at[zz, s])
            for j in JAHRE:
                null[j].append(np.mean(z[j]) if z[j] else np.nan)
        m = {j: float(np.mean(echt[j])) if echt[j] else float("nan") for j in JAHRE}
        p95 = {j: float(np.nanpercentile(null[j], 95)) for j in JAHRE}
        mu = {j: float(np.nanmean(null[j])) for j in JAHRE}
        traegt = m[2024] > p95[2024] and m[2025] > mu[2025] and m[2026] > mu[2026] and (m[2025] > p95[2025] or m[2026] > p95[2026])
        if traegt:
            t.append(h)
        print("  %4d h | %s | %s" % (h, " ".join("%d %.3f (Zufall %.3f, N95 %.3f, n %d)" % (j, m[j], mu[j], p95[j], len(echt[j])) for j in JAHRE),
                                    "TRAEGT" if traegt else "traegt nicht"), flush=True)
    print("  -> tragfaehig: %s" % (", ".join("%d h" % h for h in t) or "KEIN Horizont"), flush=True)
    return t


if __name__ == "__main__":
    was = set(sys.argv[1:]) or {"a", "b", "c"}
    print("Spot M-0 Machbarkeit - Messplan Voranalyse_Spot §7.2 (vorab festgelegt, Commit 0e776be)", flush=True)
    K = V = None
    if was & {"a", "b"}:
        K, V = tage()
        K = K[K.index >= "2022-06-01"]
        print("Messbasis: %d Assets, Tage %s bis %s" % (K.shape[1], K.index[0].date(), K.index[-1].date()), flush=True)
    a = m0a(K, V) if "a" in was else None
    b = m0b(K) if "b" in was else None
    c = m0c() if "c" in was else None
    print("== ZUSAMMEN (Folgen vorab, §7.3): Welches %s · Ob %s · L3 %s" % (
        "-" if a is None else ("TRAEGT" if a else "nein"), "-" if b is None else ("TRAEGT" if b else "nein"),
        "-" if c is None else ("TRAEGT" if c else "nein")), flush=True)
