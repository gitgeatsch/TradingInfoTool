"""G7 S7-ANLAGE — GROBE Vorprüfung der Nullwelt und der Auflösung (Voranalyse_G7_S7_Anlage_05_11.md §3). 200 Ziehungen je Fall,
nicht der Selbsttest (der kommt mit dem Bau, 1.000 Ziehungen). KEIN LLM-Urteil wird gelesen: die Urteile sind KÜNSTLICH, die
Zielgrößen echt.

Panel Asset x Tag (379 Assets x 335 Tage), Zielgröße ertrag_s(H=3) je Zelle (Start T 01:00, σ 60 T vor T). Urteil +1 = stützt,
−1 = belastet, nur auf Ereigniszellen (s7_zellen.csv). Statistik S = Mittel(z | stützt) − Mittel(z | belastet), einseitig OBEN.

Nullwelten im Vergleich:
  NAIV        t-Test, jede Zelle unabhängig (zum Zeigen, warum nicht)
  TAGE        Tages-Kreisverschiebung wie Stufe 3 (Position j des Tages d -> Tag d+k) - zerreißt die Läufe je Asset
  ASSET-ZEIT  Kreisverschiebung der Urteilsreihe JE ASSET um dasselbe k (volle Bahn) - hält Läufe, Asset und Markttag zusammen

    python Basisinfos/Rechenkern_02_10/g7_s7_aufloesung_grob.py   -> g7_s7_aufloesung_grob.txt
"""
import math
import os
import sqlite3
import sys
import time

import numpy as np
import pandas as pd

HIER = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.dirname(os.path.dirname(HIER))
KOPIE = os.path.join(PROJ, "data", "_g7", "kurse")
ZELLEN = os.path.join(PROJ, "data", "_g7", "s7_zellen.csv")
TXT = []
ZIEH = 200
SAAT = 51105


def p(*a):
    s = " ".join(str(x) for x in a)
    print(s, flush=True)
    TXT.append(s)


def panel():
    C = pd.read_csv(ZELLEN, sep=";")
    tage = pd.date_range("2025-12-01", "2026-10-31", freq="D")
    assets = sorted(C.asset.unique())
    mb = {r[0] for r in sqlite3.connect("file:%s?mode=ro" % os.path.join(KOPIE, "stundenkurse.db").replace("\\", "/"), uri=True)
          .execute("SELECT DISTINCT symbol FROM stundenkurse")}
    con = {f: sqlite3.connect("file:%s?mode=ro" % os.path.join(KOPIE, f).replace("\\", "/"), uri=True)
           for f in ("stundenkurse.db", "stundenkurse_alle.db")}
    Z = np.full((len(assets), len(tage)), np.nan)
    for i, s in enumerate(assets):
        c = con["stundenkurse.db" if s in mb else "stundenkurse_alle.db"]
        k = pd.Series(dict(c.execute("SELECT stunde, close FROM stundenkurse WHERE symbol=? AND stunde >= '2025-08-01'", (s,)).fetchall()))
        if not len(k):
            continue
        k.index = pd.to_datetime(k.index)
        k = k.sort_index().astype(float)
        sig = np.log(k.resample("D").last()).diff().rolling(60).std().shift(1)
        p0 = k.reindex(tage)
        p3 = k.reindex(tage + pd.Timedelta(hours=72))
        Z[i] = (np.log(p3.values / p0.values) / (sig.reindex(tage).values * math.sqrt(3)))
    E = np.zeros_like(Z, dtype=bool)
    ai = {a: i for i, a in enumerate(assets)}
    ti = {t.strftime("%Y-%m-%d"): j for j, t in enumerate(tage)}
    for a, t in zip(C.asset, C.tag):
        E[ai[a], ti[t]] = True
    return Z, E, assets, tage


def stat(U, Z):
    ok = np.isfinite(Z)
    a, b = Z[(U == 1) & ok], Z[(U == -1) & ok]
    return a.mean() - b.mean() if len(a) and len(b) else np.nan


def null_asset_zeit(U, Z):
    return np.array([stat(np.roll(U, k, axis=1), Z) for k in range(1, U.shape[1])])


def null_tage(U, Z, E):
    """Stufe-3-Bahn auf dem Panel: die j-te Ereigniszelle des Tages d bekommt das Urteil der (j mod n)-ten Zelle des Tages d+k."""
    D = U.shape[1]
    zellen = [np.flatnonzero(E[:, d]) for d in range(D)]
    out = []
    for k in range(1, D):
        V = np.zeros_like(U)
        for d in range(D):
            q, z = zellen[(d - k) % D], zellen[d]
            if len(q) and len(z):
                V[z, d] = U[q[np.arange(len(z)) % len(q)], (d - k) % D]
        out.append(stat(V, Z))
    return np.array(out)


def naiv(U, Z):
    ok = np.isfinite(Z)
    a, b = Z[(U == 1) & ok], Z[(U == -1) & ok]
    se = math.sqrt(a.var(ddof=1) / len(a) + b.var(ddof=1) / len(b))
    return (a.mean() - b.mean()) / se > 1.645


def laeufe(E):
    """Läufe je Asset: zusammenhängende Ereignistage."""
    r = []
    for i in range(E.shape[0]):
        x = np.r_[0, E[i].astype(int), 0]
        st, en = np.flatnonzero(np.diff(x) == 1), np.flatnonzero(np.diff(x) == -1)
        r += [(i, s, e) for s, e in zip(st, en)]
    return r


def g_lauf(E, R, rng, je_tag=2.0, anteil_belastet=0.6):
    """Ein Urteil gilt für den ganzen Lauf (wie ein LLM, das dieselbe Meldung 7 Tage gleich liest)."""
    U = np.zeros(E.shape, dtype=int)
    ziel = je_tag * E.shape[1]
    for j in rng.permutation(len(R)):
        if (U != 0).sum() >= ziel:
            break
        i, s, e = R[j]
        U[i, s:e] = -1 if rng.random() < anteil_belastet else 1
    return U


def g_asset(E, rng, anteil=0.05):
    """Asset-Vorurteil: ein fester Teil der Assets an allen Ereignistagen belastet, ein gleich großer stützt."""
    U = np.zeros(E.shape, dtype=int)
    a = rng.permutation(E.shape[0])
    n = max(1, int(anteil * E.shape[0]))
    U[a[:n]] = -1
    U[a[n:2 * n]] = 1
    return U * E


def g_markt(E, rng, L=3, je_tag=2.0):
    """Tagesstimmung (Markov, mittlere Lauflänge L): an Stimmungstagen 'belastet', sonst 'stützt' - je Tag ~je_tag Zellen."""
    D = E.shape[1]
    m = np.zeros(D, dtype=bool)
    for d in range(1, D):
        m[d] = (rng.random() < 1 - 1 / L) if m[d - 1] else (rng.random() < 0.3 / L)
    U = np.zeros(E.shape, dtype=int)
    for d in range(D):
        z = np.flatnonzero(E[:, d])
        if len(z):
            w = rng.choice(z, min(len(z), max(1, rng.poisson(je_tag))), replace=False)
            U[w, d] = -1 if m[d] else 1
    return U


def fehlalarm(gen, Z, E, rng, n, mit_tage=False):
    za = ta = na = 0
    for _ in range(n):
        U = gen(rng)
        s = stat(U, Z)
        za += s > np.nanpercentile(null_asset_zeit(U, Z), 95)
        na += naiv(U, Z)
        if mit_tage:
            ta += s > np.nanpercentile(null_tage(U, Z, E), 95)
    return 100 * za / n, (100 * ta / n if mit_tage else np.nan), 100 * na / n


def bahn_ereignis(E):
    """ASSET-EREIGNIS (zweiter Versuch, 05.11.): je Asset die Folge SEINER Ereigniszellen in Zeitordnung, Kreisverschiebung um k
    Positionen (k = 1 .. D−1, für alle Assets dasselbe k, je Asset mod n_a). Das Urteil bleibt beim Asset und auf einem Ereignistag;
    ein Lauf bleibt weitgehend zusammen. Anlass: ASSET-ZEIT setzte die Urteile auf Tage OHNE Meldung (andere Streuung) -> 7,5–9 %."""
    r, c = np.nonzero(E)                                   # zeilenweise: nach Asset, dann Tag
    n = np.bincount(r, minlength=E.shape[0])
    start = np.r_[0, np.cumsum(n)[:-1]]
    pos = np.arange(len(r)) - start[r]
    k = np.arange(1, E.shape[1])[:, None]
    return r, c, start[r][None, :] + (pos[None, :] + k) % n[r][None, :]


def null_ereignis(U, Z, B):
    r, c, idx = B
    u, z = U[r, c], Z[r, c]
    ok = np.isfinite(z)
    V = u[idx]
    a = ((V == 1) & ok) @ np.where(ok, z, 0) / np.maximum(((V == 1) & ok).sum(1), 1)
    b = ((V == -1) & ok) @ np.where(ok, z, 0) / np.maximum(((V == -1) & ok).sum(1), 1)
    return a - b


def main_ereignis():
    t0 = time.time()
    rng = np.random.default_rng(SAAT + 1)
    Z, E, A, T = panel()
    R = laeufe(E)
    B = bahn_ereignis(E)
    p("S7 GROB b · ASSET-EREIGNIS · %s · %d Ereigniszellen" % (time.strftime("%Y-%m-%d %H:%M"), E.sum()))
    p("Fehlalarm in %% (Soll <= 5), je %d Ziehungen: ASSET-EREIGNIS | ASSET-ZEIT" % ZIEH)
    for name, gen in (("G-Lauf 2/Tag", lambda r: g_lauf(E, R, r, 2.0)), ("G-Lauf 5/Tag", lambda r: g_lauf(E, R, r, 5.0)),
                      ("G-Asset 5 %", lambda r: g_asset(E, r, 0.05)), ("G-Markt L=3", lambda r: g_markt(E, r, 3)),
                      ("G-Markt L=10", lambda r: g_markt(E, r, 10))):
        fe = fz = 0
        for _ in range(ZIEH):
            U = gen(rng)
            s = stat(U, Z)
            fe += s > np.nanpercentile(null_ereignis(U, Z, B), 95)
            fz += s > np.nanpercentile(null_asset_zeit(U, Z), 95)
        p("  %-14s %5.1f | %5.1f   (%.0f s)" % (name, 100 * fe / ZIEH, 100 * fz / ZIEH, time.time() - t0))
    p("Auflösung ASSET-EREIGNIS (Fundquote %%, je %d Ziehungen): z + s an stützt, z − s an belastet" % ZIEH)
    for je in (2.0, 5.0):
        zeile = []
        for s_ in (0.1, 0.2, 0.3, 0.5):
            f = 0
            for _ in range(ZIEH):
                U = g_lauf(E, R, rng, je)
                Zp = Z + s_ * U
                f += stat(U, Zp) > np.nanpercentile(null_ereignis(U, Zp, B), 95)
            zeile.append("%.1f σ: %3.0f" % (s_, 100 * f / ZIEH))
        p("  %.0f Zellen/Tag  %s" % (je, " · ".join(zeile)))
    open(os.path.join(HIER, "g7_s7_aufloesung_grob_b.txt"), "w", encoding="utf-8").write("\n".join(TXT) + "\n")
    p("fertig %.0f s" % (time.time() - t0))


def tstat(U, Z):
    """Studentisiert: (Mittel stützt − Mittel belastet) / Standardfehler. Teilt die Streuung der Stellen heraus, auf denen die Urteile
    gerade liegen (Ereignistage streuen anders als Tage ohne Meldung)."""
    ok = np.isfinite(Z)
    a, b = Z[(U == 1) & ok], Z[(U == -1) & ok]
    if len(a) < 2 or len(b) < 2:
        return np.nan
    return (a.mean() - b.mean()) / math.sqrt(a.var(ddof=1) / len(a) + b.var(ddof=1) / len(b))


def main_t():
    t0 = time.time()
    rng = np.random.default_rng(SAAT + 2)
    Z, E, A, T = panel()
    R = laeufe(E)
    p("S7 GROB c · ASSET-ZEIT STUDENTISIERT · %s" % time.strftime("%Y-%m-%d %H:%M"))
    p("Fehlalarm in %% (Soll <= 5), je %d Ziehungen: ASSET-ZEIT t | ASSET-ZEIT Mittelwertdifferenz" % ZIEH)
    for name, gen in (("G-Lauf 2/Tag", lambda r: g_lauf(E, R, r, 2.0)), ("G-Lauf 5/Tag", lambda r: g_lauf(E, R, r, 5.0)),
                      ("G-Asset 5 %", lambda r: g_asset(E, r, 0.05)), ("G-Markt L=3", lambda r: g_markt(E, r, 3)),
                      ("G-Markt L=10", lambda r: g_markt(E, r, 10))):
        ft = fd = 0
        for _ in range(ZIEH):
            U = gen(rng)
            nt = np.array([tstat(np.roll(U, k, axis=1), Z) for k in range(1, U.shape[1])])
            ft += tstat(U, Z) > np.nanpercentile(nt, 95)
            fd += stat(U, Z) > np.nanpercentile(null_asset_zeit(U, Z), 95)
        p("  %-14s %5.1f | %5.1f   (%.0f s)" % (name, 100 * ft / ZIEH, 100 * fd / ZIEH, time.time() - t0))
    p("Auflösung ASSET-ZEIT t (Fundquote %%, je %d Ziehungen)" % ZIEH)
    for je in (2.0, 5.0):
        zeile = []
        for s_ in (0.1, 0.2, 0.3, 0.5):
            f = 0
            for _ in range(ZIEH):
                U = g_lauf(E, R, rng, je)
                Zp = Z + s_ * U
                nt = np.array([tstat(np.roll(U, k, axis=1), Zp) for k in range(1, U.shape[1])])
                f += tstat(U, Zp) > np.nanpercentile(nt, 95)
            zeile.append("%.1f σ: %3.0f" % (s_, 100 * f / ZIEH))
        p("  %.0f Zellen/Tag  %s" % (je, " · ".join(zeile)))
    open(os.path.join(HIER, "g7_s7_aufloesung_grob_c.txt"), "w", encoding="utf-8").write("\n".join(TXT) + "\n")
    p("fertig %.0f s" % (time.time() - t0))


def main():
    if "--ereignis" in sys.argv:
        return main_ereignis()
    if "--t" in sys.argv:
        return main_t()
    t0 = time.time()
    rng = np.random.default_rng(SAAT)
    Z, E, A, T = panel()
    R = laeufe(E)
    p("S7 GROB · %s · Panel %d Assets x %d Tage · Ereigniszellen %d (mit Zielgröße %d) · Läufe %d · %.0f s" % (
        time.strftime("%Y-%m-%d %H:%M"), len(A), len(T), E.sum(), (E & np.isfinite(Z)).sum(), len(R), time.time() - t0))
    p("Fehlalarm in %% (Soll <= 5), je %d Ziehungen: ASSET-ZEIT | TAGE (nur 20 Ziehungen) | NAIV" % ZIEH)
    for name, gen in (("G-Lauf 2/Tag", lambda r: g_lauf(E, R, r, 2.0)), ("G-Lauf 5/Tag", lambda r: g_lauf(E, R, r, 5.0)),
                      ("G-Asset 5 %", lambda r: g_asset(E, r, 0.05)), ("G-Markt L=3", lambda r: g_markt(E, r, 3)),
                      ("G-Markt L=10", lambda r: g_markt(E, r, 10))):
        za, _, na = fehlalarm(gen, Z, E, rng, ZIEH)
        _, ta, _ = fehlalarm(gen, Z, E, rng, 20, mit_tage=True)
        p("  %-14s %5.1f | %5.1f | %5.1f   (%.0f s)" % (name, za, ta, na, time.time() - t0))
    p("Auflösung ASSET-ZEIT (Fundquote %%, je %d Ziehungen): z + s an stützt, z − s an belastet" % ZIEH)
    for je in (2.0, 5.0):
        zeile = []
        for s_ in (0.1, 0.2, 0.3, 0.5):
            f = 0
            for _ in range(ZIEH):
                U = g_lauf(E, R, rng, je)
                Zp = Z + s_ * U
                f += stat(U, Zp) > np.nanpercentile(null_asset_zeit(U, Zp), 95)
            zeile.append("%.1f σ: %3.0f" % (s_, 100 * f / ZIEH))
        p("  %.0f Zellen/Tag  %s" % (je, " · ".join(zeile)))
    open(os.path.join(HIER, "g7_s7_aufloesung_grob.txt"), "w", encoding="utf-8").write("\n".join(TXT) + "\n")
    p("fertig %.0f s" % (time.time() - t0))


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:                                                  # noqa: BLE001
        pass
    main()
