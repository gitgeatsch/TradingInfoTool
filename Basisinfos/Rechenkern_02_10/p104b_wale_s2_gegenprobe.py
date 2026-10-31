# -*- coding: utf-8 -*-
"""G16 Wale STUFE 2 — GEGENPROBE (Messplan §16) auf EIGENEN Wegen, NICHT über ``p104_wale_s2``/``p102_wale_basis``-Rechenfunktionen.

    1  E und L je Symbol: eigener Fluss (pandas aus der Ablage), eigene Regression (Normalgleichungen), eigener Rang — Stichprobe
    2  vektorisierte Fünftel des Selbsttests gegen den Rang aus 1 — alle Symbole
    3  Zuordnungstag mit eigener Datumsrechnung (datetime), alle Einstiege aller Mengen
    4  y direkt aus der Stundenkurs-Ablage (SQL), Stichprobe
    5  D, Summe, Jahre, Signalbilanz je Menge mit eigener Schleife (Python-Wörterbücher) gegen ``p104_wale_s2_messung.txt.json``
    6  VORGRIFF: Daten ab einem Stichtag gelöscht -> E und L bis zum Stichtag unverändert; Zuordnung nie am Einstiegstag selbst
    7  Permutationstest mit eigener Schleife und eigenem Startwert, 2.000 Vertauschungen (p-Wert vergleichbar, nicht gleich)

    python -X utf8 Basisinfos/Rechenkern_02_10/p104b_wale_s2_gegenprobe.py
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
import p104_wale_s2 as W  # noqa: E402  (nur Daten und Mengen; die Rechnung hier ist eigen)

WURZEL = W.B.WURZEL
START = date(2023, 1, 1)
TAGE = [START + timedelta(days=i) for i in range(W.ND)]
Z = []


def zeige(s=""):
    print(s, flush=True)
    Z.append(s)


def eigener_fluss(con, paar):
    """G, R (q 5 %) je Tag: Klassen absteigend kumulieren, Grenzklasse ganz (wie Messplan §4) — mit pandas."""
    v = pd.read_sql_query("SELECT datum, seite, klasse, usd FROM verteilung WHERE symbol=? AND markt='spot' AND einheit='sweep'", con, params=(paar,))
    v["netto"] = np.where(v.seite == "kauf", v.usd, -v.usd)
    k = v.groupby(["datum", "klasse"]).agg(usd=("usd", "sum"), netto=("netto", "sum")).reset_index()
    g, r = {}, {}
    for d, t in k.groupby("datum"):
        t = t.sort_values("klasse", ascending=False)
        ges = t.usd.sum()
        kum = t.usd.cumsum().to_numpy()
        i = int(np.argmax(kum >= 0.05 * ges))
        g[d] = t.netto.iloc[:i + 1].sum() / ges
        r[d] = t.netto.iloc[i + 1:].sum() / ges
    return g, r


def eigene_kurse(con, paar):
    return {datetime.fromtimestamp(ts / 1000, timezone.utc).date(): o for ts, o in con.execute("SELECT ts, eroeffnung FROM kurs WHERE symbol=?", (paar,))
            if ts % 86_400_000 == 0}


def eigenes_e(con, paar, auff, bis=None):
    g, r = eigener_fluss(con, paar)
    px = eigene_kurse(con, paar)
    n = len(TAGE)
    G, R, M = np.full(n, np.nan), np.full(n, np.nan), np.full(n, np.nan)
    for i, d in enumerate(TAGE):
        if bis is not None and d > bis:
            continue
        s = d.isoformat()
        if s in g and s not in auff:
            G[i], R[i] = g[s], r[s]
        if d in px and d + timedelta(days=1) in px and (bis is None or d + timedelta(days=1) <= bis + timedelta(days=1)):
            M[i] = np.log(px[d + timedelta(days=1)] / px[d])
    e = np.full(n, np.nan)
    ok = np.isfinite(G) & np.isfinite(R) & np.isfinite(M)
    for t in range(n):
        if not ok[t]:
            continue
        idx = [j for j in range(max(0, t - 180), t) if ok[j]]
        if len(idx) < 120:
            continue
        X = np.column_stack([np.ones(len(idx)), R[idx], M[idx]])
        b = np.linalg.solve(X.T @ X, X.T @ G[idx])
        e[t] = G[t] - (b[0] + b[1] * R[t] + b[2] * M[t])
    lab = np.full(n, np.nan)
    for t in range(n):
        if not np.isfinite(e[t]):
            continue
        v = np.sort(e[max(0, t - 365):t][np.isfinite(e[max(0, t - 365):t])])
        if len(v) < 120:
            continue
        lo, hi = np.percentile(v, 20), np.percentile(v, 80)
        lab[t] = 1 if e[t] > hi else (-1 if e[t] < lo else 0)
    return e, lab


def main():
    vorher = W.B.fingerabdruck()
    zeige("GEGENPROBE G16 STUFE 2 (%s, %s) — eigene Rechenwege" % (socket.gethostname(), datetime.now().isoformat(timespec="seconds")))
    sym, E, LAB, vp = W.lade_alles()
    m, _ = W.paare()
    ok_alle = True
    # 1 E und L, Stichprobe
    rng = np.random.default_rng(777)
    neu = [s for s in sym if s not in W.V.GELADEN and s not in vp["ausschluss"]]
    probe = list(rng.choice(neu, 12, replace=False)) + ["AVAX", "BTC"]
    cons = {"s2": sqlite3.connect("file:%s?mode=ro" % W.S2.replace("\\", "/"), uri=True),
            "voll": sqlite3.connect("file:%s?mode=ro" % W.B.ABLAGE.replace("\\", "/"), uri=True)}
    abw_e, gleich_l = [], []
    for s in probe:
        con = cons["voll" if s in W.V.GELADEN else "s2"]
        auff = {d for (d,) in con.execute("SELECT datum FROM tag WHERE symbol=? AND markt='spot' AND (kerze_usd IS NULL OR ABS(umsatz_usd/kerze_usd-1) > 0.005)",
                                          (m[s],))}
        e, lab = eigenes_e(con, m[s], auff)
        i = sym.index(s)
        f = np.isfinite(E[i])
        abw_e.append(float(np.nanmax(np.abs(e[f] - E[i][f]))) if f.any() else 0.0)
        gleich_l.append(bool((np.isnan(e) == np.isnan(E[i])).all() and np.array_equal(lab[np.isfinite(lab)], LAB[i][np.isfinite(LAB[i])])))
        zeige("  1 %-8s E größte Abweichung %.1e · NaN-Muster und Fünftel gleich %s" % (s, abw_e[-1], gleich_l[-1]))
    g1 = max(abw_e) < 1e-9 and all(gleich_l)
    ok_alle &= g1
    zeige("1 E und L (14 Symbole, eigener Weg): %s" % ("✔" if g1 else "✖"))
    # 2 vektorisierte Fünftel gegen den eigenen Rang (alle Symbole, ohne Ausschluss)
    LV = W.fuenftel_matrix(E)
    a, b = LV[np.isfinite(LAB)], LAB[np.isfinite(LAB)]
    g2 = bool((np.isfinite(LV) == np.isfinite(LAB)).all() and (a == b).mean() > 0.9999)
    ok_alle &= g2
    zeige("2 Fünftel des Selbsttests gegen den Rang der Messung: NaN-Muster gleich %s · Labels gleich %.5f %s" % (
        (np.isfinite(LV) == np.isfinite(LAB)).all(), (a == b).mean(), "✔" if g2 else "✖"))
    # 3 Zuordnung mit eigener Datumsrechnung
    falsch = 0
    n3 = 0
    mengen = W.lade_mengen(sym, LAB)
    for name, e in mengen.items():
        for st, ei in zip(e.stunde.to_numpy(), e.ei.to_numpy()):
            ein = datetime(2020, 1, 1) + timedelta(hours=int(st) + 1)
            soll = (ein.date() - timedelta(days=1 if ein.hour >= 3 else 2) - START).days
            falsch += soll != ei
            n3 += 1
    ok_alle &= falsch == 0
    zeige("3 Zuordnungstag: %d Einstiege, abweichend %d %s" % (n3, falsch, "✔" if falsch == 0 else "✖"))
    # 4 y direkt aus der Ablage
    e0 = mengen["unverzerrt_1"]
    st = e0[e0.y.notna()].sample(300, random_state=5)
    dbs = [sqlite3.connect("file:data/%s?mode=ro" % d, uri=True) for d in W.P.DATEIEN if os.path.exists(os.path.join(WURZEL, "data", d))]
    abw = []
    for r in st.itertuples():
        def close(h):
            ts = (pd.Timestamp("2020-01-01") + pd.Timedelta(hours=int(h))).strftime("%Y-%m-%d %H:%M")
            for c in dbs:
                x = c.execute("SELECT close FROM stundenkurse WHERE symbol=? AND stunde=?", (r.symbol, ts)).fetchone()
                if x:
                    return x[0]
            return None
        a1, a2 = close(r.stunde), close(r.stunde + 24)
        abw.append(abs(np.log(a2 / a1) - r.y) if a1 and a2 else np.inf)
    g4 = max(abw) < 1e-12
    ok_alle &= g4
    zeige("4 y aus der Stundenkurs-Ablage (300 Einstiege unverzerrt_1): größte Abweichung %.1e %s" % (max(abw), "✔" if g4 else "✖"))
    # 5 D und Punkte mit eigener Schleife
    ref = json.load(open(W.AUS % "messung" + ".json", encoding="utf-8"))["je"]
    g5 = True
    for name, e in mengen.items():
        u = e[e.ungesehen & e.L.notna() & e.y.notna()]
        tagm = {}
        for t, y in zip(u.tag, u.y):
            tagm.setdefault(t, []).append(y)
        tagm = {t: sum(v) / len(v) for t, v in tagm.items()}
        o, un, je_j, je_a = [], [], {}, {}
        for r in u.itertuples():
            yt = r.y - tagm[r.tag]
            if r.L == 1:
                o.append(yt)
                je_j.setdefault(r.jahr, ([], []))[0].append(yt)
                je_a[r.symbol] = je_a.get(r.symbol, 0.0) + r.y
            elif r.L == -1:
                un.append(yt)
                je_j.setdefault(r.jahr, ([], []))[1].append(yt)
                je_a[r.symbol] = je_a.get(r.symbol, 0.0) - r.y
        d = sum(o) / len(o) - sum(un) / len(un)
        alle = e[e.L.notna() & e.y.notna()]
        summe = sum(y for y, l in zip(alle.y, alle.L) if l == 1) - sum(y for y, l in zip(alle.y, alle.L) if l == -1)
        neg = sum(1 for v in je_a.values() if v < 0) / max(1, sum(1 for v in je_a.values() if v != 0))
        jahre = {j: sum(a) / len(a) - sum(b) / len(b) for j, (a, b) in je_j.items() if a and b}
        r_ = ref[name]
        gleich = (abs(d - r_["D"]) < 1e-12 and abs(summe - r_["summe"]) < 1e-9 and abs(neg - r_["neg"]) < 1e-12
                  and all(abs(jahre[j] - r_["jahre"][str(j)]) < 1e-12 for j in W.JAHRE))
        g5 &= gleich
        zeige("  5 %-13s D %+.6f Pp (Messung %+.6f) · Summe %+.4f (%+.4f) · Assets mit Minus %.4f (%.4f) · Jahre gleich · %s" % (
            name, 100 * d, 100 * r_["D"], summe, r_["summe"], neg, r_["neg"], "✔" if gleich else "✖"))
    ok_alle &= g5
    zeige("5 D, Summe, Jahre, Signalbilanz mit eigener Schleife: %s" % ("✔" if g5 else "✖"))
    # 6 Vorgriff
    s = probe[0]
    con = cons["s2"]
    auff = {d for (d,) in con.execute("SELECT datum FROM tag WHERE symbol=? AND (kerze_usd IS NULL OR ABS(umsatz_usd/kerze_usd-1) > 0.005)", (m[s],))}
    stich = date(2025, 6, 15)
    e_ab, l_ab = eigenes_e(con, m[s], auff, bis=stich)
    i = sym.index(s)
    k = (stich - START).days + 1
    g6a = bool(np.array_equal(np.isnan(e_ab[:k]), np.isnan(E[i][:k])) and np.nanmax(np.abs(e_ab[:k] - E[i][:k])) < 1e-9
               and np.array_equal(l_ab[:k][np.isfinite(l_ab[:k])], LAB[i][:k][np.isfinite(LAB[i][:k])]))
    zuord = [(ei, (pd.Timestamp(t) - pd.Timestamp(START)).days) for e in mengen.values() for ei, t in zip(e.ei, e.tag)]
    g6b = all(ei < tg for ei, tg in zuord)
    ok_alle &= g6a and g6b
    zeige("6 VORGRIFF: %s mit Daten nur bis %s -> E und L bis dahin gleich %s · Zuordnungstag immer VOR dem Einstiegstag %s" % (
        s, stich, "✔" if g6a else "✖", "✔" if g6b else "✖"))
    # 7 Permutationstest, eigene Schleife
    rng = np.random.default_rng(424242)
    for name in ("unverzerrt_1",):
        Mx = W.Menge(mengen[name])
        Lx = LAB[Mx.si, Mx.ei]
        d = Lx == 1
        dobs = Mx.yt[Lx == 1].mean() - Mx.yt[Lx == -1].mean()
        lang = Mx.d1 - Mx.d0 + 1
        bl = [list(range(j, min(j + 30, lang))) for j in range(0, lang, 30)]
        null = []
        for _ in range(2000):
            neu_ = [x for j in rng.permutation(len(bl)) for x in bl[j]]
            lp = np.array([LAB[si, neu_[ei - Mx.d0] + Mx.d0] for si, ei in zip(Mx.si, Mx.ei)])
            null.append(Mx.yt[lp == 1].mean() - Mx.yt[lp == -1].mean())
        p = (1 + sum(v >= dobs for v in null)) / 2001
        zeige("7 Permutation %s, eigene Schleife, 2.000 Vertauschungen: p %.3f (Messung %.3f) · Schwelle %+.3f Pp (Messung %+.3f) — Auskunft" % (
            name, p, ref[name]["p"], 100 * np.quantile(null, 0.95), 100 * ref[name]["schwelle"]))
        del d
    for c in list(cons.values()) + dbs:
        c.close()
    zeige("\nERGEBNIS GEGENPROBE: %s" % ("BESTANDEN" if ok_alle else "NICHT BESTANDEN"))
    zeige("Seiteneffekt: geschützte Datei unverändert: %s" % (vorher == W.B.fingerabdruck()))
    with open(os.path.join(HIER, "p104b_wale_s2_gegenprobe.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(Z) + "\n")


if __name__ == "__main__":
    main()
