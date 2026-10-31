# -*- coding: utf-8 -*-
"""G16 Wale URSACHENMESSUNG — GEGENPROBE (Messplan §18) auf EIGENEN Wegen, NICHT über die Rechenfunktionen von ``p105_wale_f4_breit``.

    1  Werteauswahl neu: y aus der Tabelle ``kerze`` (Datum, Eröffnung) statt ``kurs``, eigene Zählung >= 365 Tage -> dieselben Werte
    2  y je Tag: kerze (Datumsschlüssel) gegen kurs (Zeitstempel) — alle Werte, alle Tage
    3  D je Wert, gepoolt, Jahre mit eigener Schleife (Python-Listen) gegen ``p105_wale_f4_breit_messung.txt.json``
    4  Verzug 06:00 direkt aus der Stundenkurs-Ablage (SQL je Zeitpunkt), Stichprobe von 10 Werten gegen den Weg über ``reihe``
    5  VORGRIFF: L des Tages t nutzt nur E bis t (Rang gegen t-365..t-1, eigene Schleife); y beginnt erst 00:00 t+1 (Datumsprobe)
    6  Permutationstest mit eigener Schleife und eigenem Startwert, 2.000 Vertauschungen (p vergleichbar, nicht gleich)
    7  Liquiditätsordnung aus ``kerze.quote_usd`` statt ``tag.umsatz_usd`` -> Drittel und Top 6 gleich?

    python -X utf8 Basisinfos/Rechenkern_02_10/p105b_wale_f4_breit_gegenprobe.py
"""
import json
import os
import socket
import sqlite3
import sys
from datetime import date, datetime, timedelta, timezone

import numpy as np
import pandas as pd

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HIER)
import p104_wale_s2 as W  # noqa: E402  (nur Pfade, Paare, Zwischenspeicher E/L)
import p64_lc_voranalyse as P  # noqa: E402  (nur die Verbindungen zur Stundenkurs-Ablage)

WURZEL = W.B.WURZEL
START = date(2023, 1, 1)
TAGE = [START + timedelta(days=i) for i in range(W.ND)]
A, Bis = date(2024, 1, 1), date(2026, 8, 31)
JAHRE = {"2024": (date(2024, 1, 1), date(2024, 12, 31)), "2025": (date(2025, 1, 1), date(2025, 12, 31)), "2026": (date(2026, 1, 1), date(2026, 8, 31))}
GELADEN = {"BTC", "ETH", "SOL", "BNB", "ADA", "TRX", "AVAX", "LINK", "NEAR"}
MESSUNG = os.path.join(HIER, "p105_wale_f4_breit_messung.txt.json")
AUS = os.path.join(HIER, "p105b_wale_f4_breit_gegenprobe.txt")
Z = []


def zeige(s=""):
    print(s, flush=True)
    Z.append(s)


def main() -> int:
    geschuetzt = os.path.join(WURZEL, "data", "tradinginfotool.db")
    vorher = (os.path.getsize(geschuetzt), os.path.getmtime(geschuetzt))
    ms = json.load(open(MESSUNG, encoding="utf-8"))
    zeige("GEGENPROBE G16 URSACHE (Messplan §18, %s, %s) · eigene Wege" % (socket.gethostname(), datetime.now().isoformat(timespec="seconds")))
    z = np.load(W.CACHE, allow_pickle=False)
    sym, LAB = list(z["sym"]), z["LAB"]
    m, eingestellt = W.paare()
    con = sqlite3.connect("file:%s?mode=ro" % W.S2.replace("\\", "/"), uri=True)
    alle_ok = True

    # 1 + 2  y aus kerze, eigene Auswahl
    fenster = [i for i, d in enumerate(TAGE) if A <= d <= Bis]
    y_k, y_abw, wahl = {}, 0.0, []
    for i, s in enumerate(sym):
        if s in GELADEN:
            continue
        op = {date.fromisoformat(d): o for d, o in con.execute("SELECT datum, eroeffnung FROM kerze WHERE symbol=?", (m[s],))}
        ku = {datetime.fromtimestamp(ts / 1000, timezone.utc).date(): o for ts, o in con.execute("SELECT ts, eroeffnung FROM kurs WHERE symbol=?", (m[s],))}
        yy, n = [], 0
        for t, d in enumerate(TAGE):
            a, b = op.get(d + timedelta(days=1)), op.get(d + timedelta(days=2))
            v = float(np.log(b / a)) if a and b else float("nan")
            yy.append(v)
            a2, b2 = ku.get(d + timedelta(days=1)), ku.get(d + timedelta(days=2))
            if a2 and b2 and np.isfinite(v):
                y_abw = max(y_abw, abs(v - float(np.log(b2 / a2))))
            if t in fenster and np.isfinite(v) and np.isfinite(LAB[i, t]):
                n += 1
        y_k[s] = yy
        if n >= 365:
            wahl.append(s)
    gleich = wahl == ms["werte"]
    alle_ok &= gleich and y_abw < 1e-12
    zeige("\n1 AUSWAHL (y aus kerze, eigene Zählung): %d Werte · gleich der Messung: %s %s" % (len(wahl), gleich, "✔" if gleich else "✖"))
    zeige("2 y kerze gegen kurs: größte Abweichung %.1e %s" % (y_abw, "✔" if y_abw < 1e-12 else "✖"))

    # 3  D je Wert mit eigener Schleife
    def d_wert(s, von, bis_):
        i = sym.index(s)
        o, u = [], []
        for t, d in enumerate(TAGE):
            if von <= d <= bis_ and np.isfinite(y_k[s][t]):
                if LAB[i, t] == 1:
                    o.append(y_k[s][t])
                elif LAB[i, t] == -1:
                    u.append(y_k[s][t])
        return sum(o) / len(o) - sum(u) / len(u) if o and u else float("nan")

    dv = [d_wert(s, A, Bis) for s in wahl]
    abw_dv = max(abs(a - b) for a, b in zip(dv, ms["dv"]))
    d_pool = float(np.mean(dv))
    jahre = {j: float(np.nanmean([d_wert(s, *zr) for s in wahl])) for j, zr in JAHRE.items()}
    abw_j = max(abs(jahre[j] - ms["jahre"][j]) for j in JAHRE)
    gut = abw_dv < 1e-12 and abs(d_pool - ms["D"]) < 1e-12 and abw_j < 1e-12
    alle_ok &= gut
    zeige("3 D je Wert (eigene Schleife): größte Abweichung %.1e · gepoolt %+.4f Pp / Messung %+.4f · Jahre %.1e · D>0 %d/%d (Messung %d/%d) %s"
          % (abw_dv, 100 * d_pool, 100 * ms["D"], abw_j, sum(v > 0 for v in dv), len(dv), ms["n_pos"], ms["n_fin"], "✔" if gut else "✖"))

    # 4  Verzug 06:00 direkt per SQL, Stichprobe
    rng = np.random.default_rng(20261109)
    probe = [wahl[k] for k in rng.choice(len(wahl), 10, replace=False)]
    abw_v, n_v = 0.0, 0
    for s in probe:
        i = sym.index(s)
        x = P.reihe(s)
        if x is None:
            continue
        a0, _L, C = x
        for t in rng.choice(fenster, 20, replace=False):
            d = TAGE[t]
            werte = []
            for k in (1, 2):
                st = (d + timedelta(days=k)).strftime("%Y-%m-%d") + " 05:00"
                cl = None
                for c in P._con.values():
                    r = c.execute("SELECT close FROM stundenkurse WHERE symbol=? AND stunde=?", (s, st)).fetchone()
                    if r:
                        cl = r[0]
                        break
                werte.append(cl)
            if None in werte:
                continue
            eigen = float(np.log(werte[1] / werte[0]))
            hh = int((pd.Timestamp(d + timedelta(days=1)) - P.B0) / pd.Timedelta(hours=1)) + 5 - a0
            weg = float(np.log(C[hh + 24] / C[hh]))
            abw_v = max(abw_v, abs(eigen - weg))
            n_v += 1
    gut = n_v >= 100 and abw_v < 1e-12
    alle_ok &= gut
    zeige("4 VERZUG 06:00 direkt per SQL gegen reihe: %d Zeitpunkte, größte Abweichung %.1e %s" % (n_v, abw_v, "✔" if gut else "✖"))

    # 5  Vorgriff: eigener Rang (nur Vergangenheit) gleich LAB; y-Datum beginnt t+1
    E = z["E"]
    abw_l, n_l = 0, 0
    for s in probe[:5]:
        i = sym.index(s)
        for t in range(len(TAGE)):
            if not np.isfinite(E[i, t]):
                continue
            v = [x for x in E[i, max(0, t - 365):t] if np.isfinite(x)]
            if len(v) < 120:
                continue
            lo, hi = np.quantile(v, (0.2, 0.8))
            l = 1.0 if E[i, t] > hi else (-1.0 if E[i, t] < lo else 0.0)
            abw_l += l != LAB[i, t]
            n_l += 1
    gut = abw_l == 0 and n_l > 1000
    alle_ok &= gut
    zeige("5 VORGRIFF: Rang nur aus t-365..t-1 (eigene Schleife, 5 Werte, %d Tage): %d Abweichungen · y_t = ln(Eröffnung t+2 / Eröffnung t+1) per Datum (Punkt 2) %s"
          % (n_l, abw_l, "✔" if gut else "✖"))

    # 6  eigener Permutationstest
    rng = np.random.default_rng(20261110)
    Lw = {s: np.array([LAB[sym.index(s), t] for t in fenster]) for s in wahl}
    Yw = {s: np.array([y_k[s][t] for t in fenster]) for s in wahl}
    for s in wahl:                                    # gegenseitig maskieren: L nur wo y, y nur wo L
        ok = np.isfinite(Lw[s]) & np.isfinite(Yw[s])
        Lw[s], Yw[s] = np.where(ok, Lw[s], np.nan), np.where(ok, Yw[s], np.nan)
    nbl = -(-len(fenster) // 30)
    null = []
    for _ in range(2000):
        idx = np.array([t for b in rng.permutation(nbl) for t in range(b * 30, min(b * 30 + 30, len(fenster)))])
        ds = []
        for s in wahl:
            l, y = Lw[s][idx], Yw[s]
            o, u = (l == 1) & np.isfinite(y), (l == -1) & np.isfinite(y)
            if o.any() and u.any():
                ds.append(y[o].mean() - y[u].mean())
        null.append(np.mean(ds))
    null = np.array(null)
    p_eigen = (1 + (null >= d_pool).sum()) / (1 + len(null))
    gut = abs(p_eigen - ms["p"]) < 0.03 + 0.5 * ms["p"]
    alle_ok &= gut
    zeige("6 PERMUTATION eigen (2.000, Startwert 20261110): p %.3f (Messung %.3f) · Schwelle %+.2f Pp (Messung %+.2f) %s"
          % (p_eigen, ms["p"], 100 * np.quantile(null, 0.95), 100 * ms["schwelle"], "✔" if gut else "✖ (Abstand groß)"))

    # 7  Liquiditätsordnung aus kerze.quote_usd
    q = {s: con.execute("SELECT COALESCE(SUM(quote_usd), 0) FROM kerze WHERE symbol=? AND datum BETWEEN ? AND ?",
                        (m[s], A.isoformat(), Bis.isoformat())).fetchone()[0] for s in wahl}
    ordn = sorted(wahl, key=lambda s: -q[s])
    top6 = [s for s in ordn if s not in eingestellt][:6]
    drittel = [set(x) for x in np.array_split(np.array(ordn), 3)]
    zeige("7 LIQUIDITÄT aus kerze.quote_usd: Top 6 %s (Messung %s) %s" % (" ".join(top6), " ".join(ms["top6"]["sym"]),
                                                                        "✔ gleich" if top6 == ms["top6"]["sym"] else "– abweichend (Auskunft)"))
    zeige("  Drittelgrößen %s" % [len(d) for d in drittel])
    con.close()
    nachher = (os.path.getsize(geschuetzt), os.path.getmtime(geschuetzt))
    zeige("\nERGEBNIS: %s · geschützte Datei unverändert: %s" % ("BESTANDEN" if alle_ok else "ABWEICHUNG", vorher == nachher))
    with open(AUS, "w", encoding="utf-8") as f:
        f.write("\n".join(Z) + "\n")
    return 0 if alle_ok else 1


if __name__ == "__main__":
    sys.exit(main())
