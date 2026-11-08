"""G18 M1 — Regel-Katalog gegen die Drift (Voranalyse_G18_M1_Regelkatalog_07_11.md §6, E-173; Nutzer 07.11.2026: *„1 Referenzmenge“*).

    python -X utf8 Basisinfos/Rechenkern_02_10/g18_m1_regelkatalog.py --pruefen      # Daten zählen, KEIN Ergebnis -> _pruefen.txt
    python -X utf8 Basisinfos/Rechenkern_02_10/g18_m1_regelkatalog.py --selbsttest   # M2, künstliche Zustände/Ereignisse -> _selbsttest.txt
    python -X utf8 Basisinfos/Rechenkern_02_10/g18_m1_regelkatalog.py --messen       # M3, erst nach bestandenem Selbsttest -> .txt

Vorsprung je Einstieg = 24-h-Ertrag − Mittel der 24-h-Erträge aller 127 Werte ab derselben Stunde (Drift); Tageswert = Mittel des Tages.
A: Spearman(Zustand am Einstiegstag T, Tages-Vorsprung) - die Cache-Zeile T kennt nur, was vor T 00:00 bekannt war (zustaende.stand_am:
   bekannt_ab <= T); Nullwelt Kreisverschiebung des Zustands über die Einstiegstage (gepoolt 2024-01..2026-08, §6.1).
B: Welch-t des Vorsprungs (Einstieg mit Binance/Upbit-Ereignis des Assets an T−3..T−1) gegen ohne; Nullwelt: Ereignisreihe jedes Assets
   um dasselbe k Tage im Kreis. Befund = außerhalb des Bands nach Holm über A (6) und B (3), α 0,05 zweiseitig; Epochen nur Auskunft;
   zweiter Weg vorwärts (M7) -> bis dahin HINWEIS (Voranalyse §6.1/§6.2).
⚠️ Nur lesend (mode=ro): Messbasis-Kurse, Zustands-Cache, sichten.db. Schreibt nur die .txt hier.
"""
import hashlib
import json
import os
import re
import sqlite3
import sys
import time

import numpy as np
import pandas as pd

HIER = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.dirname(os.path.dirname(HIER))
DATEN = os.path.join(PROJ, "data")
EINSTIEGE = os.path.join(DATEN, "_vergleich", "kern48jbz_einstiege_bestand.csv")
ZUSTAENDE = os.path.join(DATEN, "_g7", "zustaende_taeglich_2021-03-01_2026-10-31.csv")
SICHTEN = os.path.join(DATEN, "_sichten", "sichten.db")
T0 = pd.Timestamp("2020-01-01")
EPOCHEN = {"2024": ("2024-01-01", "2024-12-31"), "2025-26": ("2025-01-01", "2026-08-31")}
A_KANDIDATEN = ["S1.funding.BTC", "S1.funding.ETH", "S1.coinbase_praemie.BTC", "S1.coinbase_praemie.ETH", "S1.oi.BTC", "S1.oi.ETH"]
STUETZT = ("airdrop", "netz_upgrade", "etf_fonds")
BELASTET = ("monitoring", "depeg_aussetzung", "hack_exploit")
B_GRUPPEN = ("stuetzend", "belastend", "irgendein")
BLOCK, MIN_BLOECKE, ALPHA = 15, 20, 0.05
MIN_DRIFT = 20
SAAT = 20261108
TXT = []


def p(*a):
    s = " ".join(str(x) for x in a)
    print(s, flush=True)
    TXT.append(s)


def ro(pfad):
    return sqlite3.connect("file:%s?mode=ro" % pfad.replace("\\", "/"), uri=True)


def werkzeug_sha():
    return hashlib.sha256(open(os.path.abspath(__file__), "rb").read()).hexdigest()[:16]


# ══ Daten ═══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════
def einstiege():
    E = pd.read_csv(EINSTIEGE, sep=";")
    E["t"] = T0 + pd.to_timedelta(E.stunde, unit="h")
    return E


def kurse(symbole, ab="2023-12-25", bis="2026-09-03"):
    """Schluss je Stunde, Messbasis: stundenkurse.db, dann stundenkurse_alle.db (die erste Datei gewinnt, wie regel0_messstand)."""
    teile = []
    for i, db in enumerate(("stundenkurse.db", "stundenkurse_alle.db")):
        c = ro(os.path.join(DATEN, db))
        q = "SELECT symbol, stunde, close FROM stundenkurse WHERE stunde >= ? AND stunde < ? AND symbol IN (%s)" % ",".join("?" * len(symbole))
        d = pd.read_sql(q, c, params=[ab, bis] + list(symbole))
        c.close()
        d["rang_datei"] = i
        teile.append(d)
    d = pd.concat(teile).sort_values("rang_datei").drop_duplicates(["symbol", "stunde"], keep="first")
    C = d.pivot_table(index="stunde", columns="symbol", values="close")
    C.index = pd.to_datetime(C.index)
    return C.reindex(pd.date_range(C.index.min(), C.index.max(), freq="h"))


def vorsprung_tabelle():
    """-> Einstiege mit e24, drift, v (Vorsprung), tag; dazu die Drift-Reihe je Stunde."""
    E = einstiege()
    C = kurse(sorted(E.symbol.unique()))
    R24 = C.shift(-24) / C - 1
    n = R24.notna().sum(axis=1)
    drift = R24.mean(axis=1).where(n >= MIN_DRIFT)
    cols = {s: i for i, s in enumerate(R24.columns)}
    zeilen = R24.index.get_indexer(E.t)
    E["e24"] = [R24.iat[z, cols[s]] if z >= 0 and s in cols else np.nan for z, s in zip(zeilen, E.symbol)]
    E["drift"] = [drift.iat[z] if z >= 0 else np.nan for z in zeilen]
    E["v"] = E.e24 - E.drift
    E["tag"] = E.t.dt.normalize()
    return E, drift, n


def zustaende():
    D = pd.read_csv(ZUSTAENDE, parse_dates=["tag"])
    R = D.pivot_table(index="tag", columns="schluessel", values="rang")
    return R.reindex(pd.date_range(R.index.min(), R.index.max(), freq="D"))


def ereignisse():
    """Binance/Upbit-Ereignisse mit Asset: (asset, tag, gruppe-Menge). Tag = UTC-Tag von bekannt_ab."""
    c = ro(SICHTEN)
    e = pd.read_sql("SELECT quelle, bekannt_ab, typ, assets, titel FROM ereignis WHERE quelle IN ('binance','upbit')", c)
    c.close()
    zeilen = []
    for q, b, typ, a, titel in e.itertuples(index=False):
        try:
            assets = json.loads(a) if a and a.startswith("[") else []
        except ValueError:
            assets = []
        if not assets:
            # §6.2 (Gegenprüfung 07.11.): ereignisse.binance_assets erkennt Kürzel erst ab 2 Zeichen und schließt BTC/ETH als
            # Kurswährung aus -> S, A, W, T und die BTC/ETH-Meldungen fehlten. Hier: Kürzel in Klammern aus dem Titel ergänzen
            assets = re.findall(r"\(([A-Z0-9]{1,12})\)", titel or "")
        if not assets:
            continue
        g = {"irgendein"}
        if typ.startswith("listing") or typ in STUETZT:
            g.add("stuetzend")
        if typ.startswith("delisting") or typ in BELASTET:
            g.add("belastend")
        for s in assets:
            zeilen.append((str(s).upper(), pd.Timestamp(b[:10]), g, typ, q))
    return pd.DataFrame(zeilen, columns=["asset", "tag", "gruppen", "typ", "quelle"])


# ══ Statistik ═══════════════════════════════════════════════════════════════════════════════════════════════════════════════════
def _rang(x):
    return pd.Series(x).rank().values


def spearman_bahn(s: np.ndarray, v: np.ndarray) -> np.ndarray:
    """Spearman(roll(s, k), v) für k = 0 … n−1 — Ränge einmal, Korrelation per FFT (Ränge sind unter Verschiebung gleich)."""
    rs, rv = _rang(s), _rang(v)
    rs, rv = rs - rs.mean(), rv - rv.mean()
    n = len(rs)
    kreuz = np.fft.irfft(np.conj(np.fft.rfft(rs)) * np.fft.rfft(rv), n=n)          # [k] = Σ roll(rs,k)·rv
    return kreuz / np.sqrt((rs ** 2).sum() * (rv ** 2).sum())


def p_zweiseitig(b: np.ndarray) -> float:
    null = b[1:]
    return float(min(1.0, 2 * min((null <= b[0]).mean(), (null >= b[0]).mean())))


def holm(pw: dict) -> dict:
    """{name: p} -> {name: bool} Holm, α = ALPHA."""
    ordn = sorted(pw, key=lambda k: pw[k])
    m, aus, weiter = len(ordn), {}, True
    for i, k in enumerate(ordn):
        ok = weiter and pw[k] <= ALPHA / (m - i)
        aus[k] = ok
        weiter = ok
    return aus


def bloecke(tage) -> int:
    t = pd.to_datetime(pd.Series(tage)).values.astype("datetime64[D]").astype(np.int64)
    return len(set(t // BLOCK))


def a_epoche(tagv: pd.Series, zust: pd.Series):
    """tagv: Tages-Vorsprung (Index Tag); zust: Zustand je Kalendertag, Zeile T = Stand T 00:00 (§6.2). -> (bahn, n Tage, Blöcke)."""
    s = zust.reindex(tagv.index).values
    ok = np.isfinite(s) & np.isfinite(tagv.values)
    if ok.sum() < 30:
        return None, int(ok.sum()), 0
    return spearman_bahn(s[ok], tagv.values[ok]), int(ok.sum()), bloecke(tagv.index[ok])


def b_marken(E: pd.DataFrame, EV: pd.DataFrame, gruppe: str, tage: pd.DatetimeIndex):
    """Matrix W[asset, tag] = Ereignis der Gruppe an T−3..T−1 -> Index je Einstieg für die Kreisverschiebung."""
    assets = sorted(E.symbol.unique())
    ai = {a: i for i, a in enumerate(assets)}
    D = len(tage)
    di = {t: j for j, t in enumerate(tage)}
    M = np.zeros((len(assets), D), dtype=bool)
    for a, t, g in zip(EV.asset, EV.tag, EV.gruppen):
        if gruppe in g and a in ai and t in di:
            M[ai[a], di[t]] = True
    W = np.zeros_like(M)
    for L in (1, 2, 3):                                   # Ereignis an T−L -> Marke am Tag T
        W[:, L:] |= M[:, :-L]
    return W, np.array([ai[s] for s in E.symbol]), np.array([di[t] for t in E.tag])


def b_bahn(W, ia, it, v, k_max=None):
    """Welch-t v (Marke) gegen v (ohne) für Verschiebung k = 0 … D−1 (jedes Asset um dasselbe k)."""
    D = W.shape[1]
    ks = range(D if k_max is None else k_max)
    aus = np.full(len(ks), np.nan)
    for k in ks:
        m = W[ia, (it - k) % D]
        if m.sum() >= 2 and (~m).sum() >= 2:
            a, b = v[m], v[~m]
            aus[k] = (a.mean() - b.mean()) / np.sqrt(a.var(ddof=1) / len(a) + b.var(ddof=1) / len(b))     # Welch-t (§6.2)
    return aus


# ══ Prüfen (ohne Ergebnis) ══════════════════════════════════════════════════════════════════════════════════════════════════════
def pruefen():
    p("G18 M1 PRÜFEN · %s · nur Zählungen, KEIN Vorsprung gegen Zustand oder Ereignis" % time.strftime("%Y-%m-%d %H:%M"))
    E, drift, n = vorsprung_tabelle()
    p("Einstiege %d · mit 24-h-Ertrag %d · mit Drift %d · mit Vorsprung %d" % (len(E), E.e24.notna().sum(), E.drift.notna().sum(),
                                                                                  E.v.notna().sum()))
    p("Werte je Stunde für die Drift: Median %d, Minimum %d (Stunden mit Einstieg)" % (
        n.reindex(E.t).median(), n.reindex(E.t).min()))
    # Gegenprobe e24 an 5 Einstiegen direkt aus der Datei
    c = ro(os.path.join(DATEN, "stundenkurse.db"))
    for r in E.dropna(subset=["e24"]).sample(5, random_state=1).itertuples():
        a = c.execute("SELECT close FROM stundenkurse WHERE symbol=? AND stunde=?", (r.symbol, r.t.strftime("%Y-%m-%d %H:%M"))).fetchone()
        b = c.execute("SELECT close FROM stundenkurse WHERE symbol=? AND stunde=?", (r.symbol, (r.t + pd.Timedelta(hours=24)).strftime(
            "%Y-%m-%d %H:%M"))).fetchone()
        p("  Gegenprobe %s %s: Tabelle %+.5f · direkt %s" % (r.symbol, r.t, r.e24, ("%+.5f" % (b[0] / a[0] - 1)) if a and b else "nicht in "
                                                                                    "stundenkurse.db (aus _alle)"))
    c.close()
    E = E.dropna(subset=["v"])
    R = zustaende()
    EV = ereignisse()
    tage = pd.date_range("2023-12-01", "2026-09-01", freq="D")
    for ep, (a, b) in EPOCHEN.items():
        Ee = E[(E.tag >= a) & (E.tag <= b)]
        tv = Ee.groupby("tag").v.mean()
        p("")
        p("Epoche %s: Einstiege %d · Tage mit Einstieg %d · Blöcke %d" % (ep, len(Ee), len(tv), bloecke(tv.index)))
        for k in A_KANDIDATEN:
            s = R[k].reindex(tv.index)
            p("  A %-24s Tage mit Zustandswert %d" % (k, s.notna().sum()))
        for g in B_GRUPPEN:
            W, ia, it = b_marken(Ee, EV, g, tage)
            m = W[ia, it]
            p("  B %-10s markierte Einstiege %4d (%.1f %%) · Blöcke mit Marke %d" % (g, m.sum(), 100 * m.mean(), bloecke(Ee.tag[m])))
    p("")
    p("Ereignisse Binance/Upbit mit Asset: %d · davon Asset in der Referenzmenge %d · Typen: %s" % (
        len(EV), EV.asset.isin(set(E.symbol)).sum(), EV.typ.value_counts().head(12).to_dict()))
    open(os.path.join(HIER, "g18_m1_regelkatalog_pruefen.txt"), "w", encoding="utf-8").write("\n".join(TXT) + "\n")


VON, BIS = "2024-01-01", "2026-08-31"          # §6.1: gepoolt
TAGE = pd.date_range("2023-12-01", "2026-09-01", freq="D")
AUS_ST = os.path.join(HIER, "g18_m1_regelkatalog_selbsttest.txt")
AUS = os.path.join(HIER, "g18_m1_regelkatalog.txt")


def basis():
    E, _, _ = vorsprung_tabelle()
    E = E.dropna(subset=["v"])
    E = E[(E.tag >= VON) & (E.tag <= BIS)].reset_index(drop=True)
    return E, E.groupby("tag").v.mean(), zustaende(), ereignisse()


def ar1(n, rho, rng):
    x = np.empty(n)
    x[0] = rng.standard_normal()
    e = rng.standard_normal(n) * np.sqrt(1 - rho ** 2)
    for i in range(1, n):
        x[i] = rho * x[i - 1] + e[i]
    return x


def ersatz(x: np.ndarray, rng) -> np.ndarray:
    """AAFT-Ersatzreihe: zufällige Phase bei gleichem Betragsspektrum, danach auf die ECHTE Werteverteilung zurückgerangt."""
    x = np.asarray(x, float)
    ok = np.isfinite(x)
    y = np.where(ok, x, np.nanmedian(x))
    F = np.fft.rfft(y - y.mean())
    ph = rng.uniform(0, 2 * np.pi, len(F))
    ph[0] = 0
    s = np.fft.irfft(np.abs(F) * np.exp(1j * ph), n=len(y))
    return np.sort(y)[pd.Series(s).rank(method="first").values.astype(int) - 1]


def p_geeicht(s_echt: np.ndarray, v: np.ndarray, rng, n: int = 1000) -> tuple[float, float]:
    """§6.3 Eichung (Selbsttest 07.11.: Kreisverschiebung allein je Kandidat bis 6,9 % Fehlalarm): Anteil der Ersatzreihen DESSELBEN
    Zustands, deren p ≤ dem beobachteten p ist. -> (p roh, p geeicht). Ersatzreihen kennen den Vorsprung nicht."""
    p0 = p_zweiseitig(spearman_bahn(s_echt, v))
    ps = np.array([p_zweiseitig(spearman_bahn(ersatz(s_echt, rng), v)) for _ in range(n)])
    return p0, float((ps <= p0).mean())


def selbsttest(ziehungen=1000, ziehungen_b=300):
    t0 = time.time()
    rng = np.random.default_rng(SAAT)
    E, tv, R, EV = basis()
    p("G18 M1 SELBSTTEST · %s · KEIN echter Zustand/kein echtes Ereignis gegen den Vorsprung · gepoolt %s..%s" % (
        time.strftime("%Y-%m-%d %H:%M"), VON, BIS))
    p("Einstiege %d · Tage %d · Blöcke %d · Werkzeug %s" % (len(E), len(tv), bloecke(tv.index), werkzeug_sha()))
    n = len(tv)
    ok_alle = True
    # A (§6.2, Gegenprüfung 07.11.): Ersatzreihen mit ZUFÄLLIGER PHASE aus der ECHTEN Zustandsreihe (gleiches Spektrum = gleiche
    # Beständigkeit über alle Fristen, gleiche Werteverteilung) - nie gegen den echten Vorsprung gekoppelt
    p("")
    p("A  Zustände als Ersatzreihen (zufällige Phase, Werteverteilung erhalten) aus der echten Reihe, gegen den ECHTEN Tages-Vorsprung")
    v = tv.values
    zeile_ok = True
    echt = {k: R[k].reindex(tv.index).values for k in A_KANDIDATEN}
    from scipy.stats import spearmanr
    s = ersatz(echt[A_KANDIDATEN[0]], rng)
    b = spearman_bahn(s, v)
    naiv = [spearmanr(np.roll(s, k), v)[0] for k in (0, 1, 7, 100, n - 1)]
    abw = max(abs(b[k] - x) for k, x in zip((0, 1, 7, 100, n - 1), naiv))
    p("  Gegenprobe Bahn (FFT) gegen scipy.spearmanr an 5 Verschiebungen: größte Abweichung %.1e" % abw)
    zeile_ok &= abw < 1e-9
    for k in A_KANDIDATEN:
        fa = sum(p_zweiseitig(spearman_bahn(ersatz(echt[k], rng), v)) <= ALPHA for _ in range(ziehungen)) / ziehungen
        p("  %-24s Beständigkeit %.2f · Fehlalarm roh %.1f %% (nur Auskunft seit §6.3)" % (k, pd.Series(echt[k]).autocorr(1), 100 * fa))
    # §6.3: die ENTSCHEIDENDE Regel ist p geeicht -> Fehlalarm je Kandidat und der Familie auf FRISCHEN Ersatzreihen ("Schein-echt")
    zg, ne = 1000, 200        # §6.4: 300 Ziehungen waren zu grob (oi.BTC 8,7 % -> mit 1.000 Ziehungen 5,1 %)
    fam = 0
    fa_k = {k: 0 for k in A_KANDIDATEN}
    for _ in range(zg):
        pw = {}
        for k in A_KANDIDATEN:
            x = ersatz(echt[k], rng)                         # spielt den echten Zustand, ohne Bezug zum Vorsprung
            pw[k] = p_geeicht(x, v, rng, ne)[1]
            fa_k[k] += pw[k] <= ALPHA
        fam += any(holm(pw).values())
    grenze = 0.05 + 2 * np.sqrt(0.05 * 0.95 / zg)
    for k in A_KANDIDATEN:
        p("  %-24s geeicht: Fehlalarm %.1f %% (Auskunft)" % (k, 100 * fa_k[k] / zg))
    # §6.5: "jeder der 6 unter 5 % + 2 SE" ist selbst ein Mehrfachtest (bei echten 5 % reißt einer in ≈ 13 % der Läufe) -> geprüft
    # wird, was §6 verlangt: die GANZE Regel (Familie) und das Mittel über alle Einzelziehungen
    mittel = sum(fa_k.values()) / (zg * len(A_KANDIDATEN))
    g_mittel = 0.05 + 2 * np.sqrt(0.05 * 0.95 / (zg * len(A_KANDIDATEN)))
    p("  Mittel über %d Einzelziehungen: Fehlalarm %.2f %% (Grenze %.2f %%)" % (zg * len(A_KANDIDATEN), 100 * mittel, 100 * g_mittel))
    zeile_ok &= mittel <= g_mittel
    p("  Familie (6, Holm, geeicht): Fehlalarm %.1f %% (Grenze %.1f %% = 5 %% + 2 Standardfehler bei %d Ziehungen)" % (
        100 * fam / zg, 100 * grenze, zg))
    zeile_ok &= fam / zg <= grenze
    # Auflösung je Kandidat bei SEINER Beständigkeit: Unterschied oberes − unteres Fünftel d Pp, gepflanzt v + β·z, d ≈ 2,8 β
    sd = v.std()
    for k in A_KANDIDATEN:
        teile = []
        for d in (0.001, 0.002, 0.003, 0.005):
            f6 = 0
            for _ in range(ziehungen // 4):
                z = ersatz(echt[k], rng)
                z = (z - z.mean()) / z.std()
                f6 += p_zweiseitig(spearman_bahn(z, v + d / 2.8 * z)) <= ALPHA / 6
            teile.append("%.1f Pp %3.0f %%" % (100 * d, 100 * f6 / (ziehungen // 4)))
        p("  Auflösung %-24s (erste Holm-Stufe α/6): %s" % (k, " · ".join(teile)))
    p("  Streuung des Tages-Vorsprungs: %.2f Pp" % (100 * sd))
    p("  => A %s" % ("BESTANDEN" if zeile_ok else "⚠ NICHT BESTANDEN"))
    ok_alle &= zeile_ok

    # B: echte Ereignisse, je Asset um ein ZUFÄLLIGES eigenes k verschoben (zerstört den Bezug zum Einstieg, erhält die Ballung)
    p("")
    p("B  echte Ereignisse, je Asset um ein eigenes zufälliges k verschoben; Nullwelt der Messung: alle Assets um dasselbe k")
    zeile_ok = True
    for g in B_GRUPPEN:
        W, ia, it = b_marken(E, EV, g, TAGE)
        m0 = W[ia, it]
        fa = 0
        for _ in range(ziehungen_b):
            ks = rng.integers(1, W.shape[1], W.shape[0])
            Wz = np.stack([np.roll(W[i], ks[i]) for i in range(W.shape[0])])
            bb = b_bahn(Wz, ia, it, E.v.values)
            fa += np.isfinite(bb[0]) and p_zweiseitig(bb[np.isfinite(bb)]) <= ALPHA
        fa2 = 0
        for _ in range(ziehungen_b):                     # §6.2: alle Assets um DASSELBE zufällige k - erhält die Ballung über Assets
            Wz = np.roll(W, int(rng.integers(1, W.shape[1])), axis=1)
            bb = b_bahn(Wz, ia, it, E.v.values)
            fa2 += np.isfinite(bb[0]) and p_zweiseitig(bb[np.isfinite(bb)]) <= ALPHA
        p("  %-10s markiert %d · Blöcke mit Marke %d · Fehlalarm eigenes k %.1f %% · gemeinsames k %.1f %%" % (
            g, m0.sum(), bloecke(E.tag[m0]), 100 * fa / ziehungen_b, 100 * fa2 / ziehungen_b))
        grenze = 0.05 + 2 * np.sqrt(0.05 * 0.95 / ziehungen_b)                 # 5 % + 2 Standardfehler (300 Ziehungen: 7,5 %)
        zeile_ok &= fa / ziehungen_b <= grenze and fa2 / ziehungen_b <= grenze
        for d in (0.005, 0.01, 0.02):
            f = 0
            for _ in range(ziehungen_b // 3):
                ks = rng.integers(1, W.shape[1], W.shape[0])
                Wz = np.stack([np.roll(W[i], ks[i]) for i in range(W.shape[0])])
                mz = Wz[ia, it]
                bb = b_bahn(Wz, ia, it, E.v.values + d * mz)
                f += np.isfinite(bb[0]) and p_zweiseitig(bb[np.isfinite(bb)]) <= ALPHA
            p("    Auflösung gepflanzt %.1f Pp: Fund %.0f %%" % (100 * d, 100 * f / (ziehungen_b // 3)))
    p("  => B %s (%.0f s)" % ("BESTANDEN" if zeile_ok else "⚠ NICHT BESTANDEN", time.time() - t0))
    ok_alle &= zeile_ok
    p("")
    p("SELBSTTEST %s · Prüfsumme Werkzeug %s" % ("BESTANDEN" if ok_alle else "NICHT BESTANDEN", werkzeug_sha()))
    open(AUS_ST, "w", encoding="utf-8").write("\n".join(TXT) + "\n")


def messen():
    st = open(AUS_ST, encoding="utf-8").read() if os.path.exists(AUS_ST) else ""
    if "SELBSTTEST BESTANDEN" not in st or werkzeug_sha() not in st:
        sys.exit("Selbsttest fehlt, nicht bestanden oder Werkzeug seitdem geändert")
    E, tv, R, EV = basis()
    p("G18 M1 MESSUNG · %s · Werkzeug %s · Vorabfestlegung Voranalyse_G18_M1 §6/§6.1 · gepoolt %s..%s · %d Einstiege, %d Tage" % (
        time.strftime("%Y-%m-%d %H:%M"), werkzeug_sha(), VON, BIS, len(E), len(tv)))
    p("Vorsprung gegen die Drift (brutto), Tageswert. Befund nach Holm = HINWEIS bis zum zweiten Weg (vorwärts, M7)")
    for gruppe, kand, rechne in (("A", A_KANDIDATEN, "a"), ("B", B_GRUPPEN, "b")):
        p("")
        p("%s %s" % (gruppe, "Tageszustand des Vortags: Spearman mit dem Tages-Vorsprung" if gruppe == "A" else
                     "Ereignis des Assets an T−3..T−1 (Binance/Upbit): Mittel Vorsprung mit − ohne Marke"))
        pw, zeilen = {}, {}
        for k in kand:
            if rechne == "a":
                b, nt, nb = a_epoche(tv, R[k])
                stat = b[0]
                extra = "Tage %d · Blöcke %d" % (nt, nb)
                ep = []
                for e, (a_, b_) in EPOCHEN.items():
                    tve = tv[(tv.index >= a_) & (tv.index <= b_)]
                    be, nte, nbe = a_epoche(tve, R[k])
                    ep.append("%s %+.3f (p %.2f, %d Bl.)" % (e, be[0], p_zweiseitig(be), nbe))
            else:
                W, ia, it = b_marken(E, EV, k, TAGE)
                m = W[ia, it]
                nb = bloecke(E.tag[m])
                b = b_bahn(W, ia, it, E.v.values)
                b = b[np.isfinite(b)] if np.isfinite(b[0]) else b
                stat = b[0]
                extra = "markiert %d · Blöcke mit Marke %d" % (m.sum(), nb)
                ep = []
                for e, (a_, b_) in EPOCHEN.items():
                    sel = ((E.tag >= a_) & (E.tag <= b_)).values
                    me = m & sel
                    ep.append("%s %s (n %d)" % (e, ("%+.2f Pp" % (100 * (E.v[me].mean() - E.v[sel & ~m].mean()))) if me.sum() >= 2 else "–",
                                                  me.sum()))
            if nb < MIN_BLOECKE or not np.isfinite(stat):
                zeilen[k] = "%-24s KEIN BEFUND (Mindestmaß: %s)" % (k, extra)
                continue
            if gruppe == "A":
                p_roh, pw[k] = p_geeicht(R[k].reindex(tv.index).values, tv.values, np.random.default_rng(SAAT + 7))
                extra += " · p roh %.3f" % p_roh
            else:
                pw[k] = p_zweiseitig(b)
            null = b[1:][np.isfinite(b[1:])]
            zeilen[k] = "%-24s %s %+.4f · Band %+.4f/%+.4f · p %.3f · %s · Epochen (Auskunft): %s" % (
                k, "ρ" if gruppe == "A" else "Δ", stat, np.percentile(null, 2.5), np.percentile(null, 97.5), pw[k], extra, " · ".join(ep))
        h = holm(pw) if pw else {}
        for k in kand:
            urteil = "" if k not in pw else ("HINWEIS (Holm gehalten)" if h[k] else "trägt nicht")
            p("  %s%s" % (zeilen[k], (" · " + urteil) if urteil else ""))
    open(AUS, "w", encoding="utf-8").write("\n".join(TXT) + "\n")


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:  # noqa: BLE001
        pass
    if "--pruefen" in sys.argv:
        pruefen()
    elif "--selbsttest" in sys.argv:
        selbsttest()
    elif "--messen" in sys.argv:
        messen()
    else:
        print(__doc__)
