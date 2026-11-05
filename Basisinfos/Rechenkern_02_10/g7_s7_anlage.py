"""G7 S7-ANLAGE — Messanlage und Selbsttest für die Sicht S7 (Voranalyse_G7_S7_Anlage_05_11.md §3 B1–B3, §4b; Nutzer 05.11.2026:
*„S7-Anlage zuerst“* und *„Ja, d + Wort-Arm“*).

Panel Asset x Tag (Ereigniszellen = in der S7-Eingabe von T betrifft mindestens eine Ereigniszeile das Asset).
Zielgröße S7-5: ertrag_s = ln(P[T 01:00 + 72 h] / P[T 01:00]) / (σ_a · √3), σ_a aus den 60 Tagen VOR T.
Urteil je Zelle: +1 stützt, −1 belastet, 0 keine (mehrere Einträge: Vorzeichen der Summe, Gleichstand = 0).

Hauptstatistik t = (Mittel stützt − Mittel belastet) / Standardfehler, einseitig OBEN.
Nullwelt ASSET-ZEIT: die Urteilsreihe JEDES Assets um dasselbe k im Kreis verschoben, k = 1 … D−1 (volle Bahn) - per FFT gerechnet,
gegengeprüft gegen die naive Schleife.
Gepaarter Vergleich A − B (S7w − S7, S7 − Typ-Regel): D = t(A) − t(B), Nullwelt = beide Reihen um DASSELBE k verschoben.

    python Basisinfos/Rechenkern_02_10/g7_s7_anlage.py --selbsttest     -> g7_s7_anlage.txt (KEIN LLM-Urteil wird gelesen)
    python Basisinfos/Rechenkern_02_10/g7_s7_anlage.py --messen         -> erst nach dem GANZEN Lauf (S7 und S7w vollständig), Stufe 2

⚠️ Nur lesend: Kurs-Arbeitskopie data/_g7/kurse (mode=ro), s7_zellen.csv, beim Messen gutachten.db (mode=ro).
"""
import json
import math
import os
import sqlite3
import sys
import time

import numpy as np
import pandas as pd

HIER = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.dirname(os.path.dirname(HIER))
sys.path.insert(0, PROJ)
KOPIE = os.path.join(PROJ, "data", "_g7", "kurse")
ZELLEN = os.path.join(PROJ, "data", "_g7", "s7_zellen.csv")
AUS = os.path.join(HIER, "g7_s7_anlage.txt")
TAGE = pd.date_range("2025-12-01", "2026-10-31", freq="D")
BLOCK, MIN_BLOECKE = 15, 20                    # messnorm._block(3) = max(15, 9); unter 20 Blöcken KEIN BEFUND
BAND, TOLERANZ = 95.0, 6.5                     # S7-2: über 6,5 % Fehlalarm wird das Band geeicht
ZIEH, ZIEH_PFL = 1000, 500
SAAT = 61105
KERN = ("BTC", "ETH", "SOL")
TYP_BELASTET = ("hack_exploit", "depeg_aussetzung", "monitoring")      # dazu delisting_*  (S7-4)
TYP_STUETZT = ("etf_fonds", "airdrop", "netz_upgrade")                  # dazu listing_*
TXT = []


def p(*a):
    s = " ".join(str(x) for x in a)
    print(s, flush=True)
    TXT.append(s)


def _ro(f):
    return sqlite3.connect("file:%s?mode=ro" % f.replace("\\", "/"), uri=True)


# ══ Panel ════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════
def zielgroesse(k: pd.Series, H: int = 3) -> np.ndarray:
    """ertrag_s je Tag von TAGE. k = Stundenschlüsse (Index = Stundenbeginn): k[T] ist der Kurs um T 01:00."""
    sig = np.log(k.resample("D").last()).diff().rolling(60).std().shift(1)        # Tag T: Erträge bis Schluss T−1 (= T 00:00)
    p0 = k.reindex(TAGE)
    pH = k.reindex(TAGE + pd.Timedelta(hours=24 * H))
    return np.log(pH.values / p0.values) / (sig.reindex(TAGE).values * math.sqrt(H))


def panel(H=(1, 3, 5)):
    C = pd.read_csv(ZELLEN, sep=";")
    assets = sorted(C.asset.unique())
    mb = {r[0] for r in _ro(os.path.join(KOPIE, "stundenkurse.db")).execute("SELECT DISTINCT symbol FROM stundenkurse")}
    con = {f: _ro(os.path.join(KOPIE, f)) for f in ("stundenkurse.db", "stundenkurse_alle.db")}
    Z = {h: np.full((len(assets), len(TAGE)), np.nan) for h in H}
    for i, s in enumerate(assets):
        c = con["stundenkurse.db" if s in mb else "stundenkurse_alle.db"]
        k = pd.Series(dict(c.execute("SELECT stunde, close FROM stundenkurse WHERE symbol=? AND stunde >= '2025-08-01'", (s,)).fetchall()))
        if len(k):
            k.index = pd.to_datetime(k.index)
            k = k.sort_index().astype(float)
            for h in H:
                Z[h][i] = zielgroesse(k, h)
    ai = {a: i for i, a in enumerate(assets)}
    ti = {t.strftime("%Y-%m-%d"): j for j, t in enumerate(TAGE)}
    E = np.zeros((len(assets), len(TAGE)), dtype=bool)
    M = {}                                                                         # (i, j) -> Zeile der Zellentabelle
    for r in C.itertuples():
        E[ai[r.asset], ti[r.tag]] = True
        M[(ai[r.asset], ti[r.tag])] = r
    return Z, E, assets, ai, ti, M


# ══ Statistik ═══════════════════════════════════════════════════════════════════════════════════════════════════════════════════
def _korr(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """Σ_Zeilen Σ_d a[i, d−k] · b[i, d] für k = 0 … D−1 (Kreis) - entspricht np.roll(a, k, axis=1) gegen b."""
    return np.fft.irfft((np.conj(np.fft.rfft(a, axis=1)) * np.fft.rfft(b, axis=1)).sum(0), n=a.shape[1])


def _t_aus(n1, s1, q1, n2, s2, q2):
    with np.errstate(invalid="ignore", divide="ignore"):
        m1, m2 = s1 / n1, s2 / n2
        v1, v2 = (q1 - n1 * m1 ** 2) / (n1 - 1), (q2 - n2 * m2 ** 2) / (n2 - 1)
        t = (m1 - m2) / np.sqrt(v1 / n1 + v2 / n2)
    return np.where((n1 >= 2) & (n2 >= 2), t, np.nan)


def t_bahn(U: np.ndarray, Z: np.ndarray) -> np.ndarray:
    """t für k = 0 (beobachtet) … D−1 (Nullwelt Asset-Zeit)."""
    ok = np.isfinite(Z)
    z = np.where(ok, Z, 0.0)
    o = ok.astype(float)
    a, b = (U == 1).astype(float), (U == -1).astype(float)
    n1, s1, q1 = (np.rint(_korr(a, o)), _korr(a, z), _korr(a, z * z))
    n2, s2, q2 = (np.rint(_korr(b, o)), _korr(b, z), _korr(b, z * z))
    return _t_aus(n1, s1, q1, n2, s2, q2)


def t_naiv(U, Z):
    ok = np.isfinite(Z)
    a, b = Z[(U == 1) & ok], Z[(U == -1) & ok]
    if len(a) < 2 or len(b) < 2:
        return np.nan
    return (a.mean() - b.mean()) / math.sqrt(a.var(ddof=1) / len(a) + b.var(ddof=1) / len(b))


def rang(bahn: np.ndarray) -> float:
    """Anteil der Nullwelt UNTER dem beobachteten Wert (k = 0); NaN-Verschiebungen zählen nicht."""
    n = bahn[1:][np.isfinite(bahn[1:])]
    return float((n < bahn[0]).mean()) if len(n) and np.isfinite(bahn[0]) else np.nan


def bloecke(U: np.ndarray, Z: np.ndarray) -> int:
    j = np.flatnonzero(((U != 0) & np.isfinite(Z)).any(0))
    return len(set(j // BLOCK))


def arm(U, Z, band=BAND) -> dict:
    b = t_bahn(U, Z)
    nb = bloecke(U, Z)
    n = b[1:][np.isfinite(b[1:])]
    grenze = float(np.percentile(n, band)) if len(n) else np.nan
    urteil = "KEIN BEFUND" if nb < MIN_BLOECKE else "TRÄGT" if b[0] > grenze else "trägt nicht"
    return {"t": float(b[0]), "grenze": grenze, "rang": rang(b), "stuetzt": int((U == 1).sum()), "belastet": int((U == -1).sum()),
            "bloecke": nb, "urteil": urteil}


def paar(UA, UB, Z, band=BAND) -> dict:
    """A besser als B? D = t(A) − t(B), beide um dasselbe k verschoben."""
    d = t_bahn(UA, Z) - t_bahn(UB, Z)
    n = d[1:][np.isfinite(d[1:])]
    grenze = float(np.percentile(n, band)) if len(n) else np.nan
    return {"D": float(d[0]), "grenze": grenze, "rang": rang(d), "urteil": "BESSER" if d[0] > grenze else "nicht besser"}


# ══ Vergleichsarme ohne LLM ═════════════════════════════════════════════════════════════════════════════════════════════════════
def typ_seite(typ: str) -> int:
    if typ in TYP_BELASTET or typ.startswith("delisting"):
        return -1
    if typ in TYP_STUETZT or typ.startswith("listing"):
        return 1
    return 0


def typ_regel(E, M) -> tuple[np.ndarray, np.ndarray]:
    """-> (Urteil, Gewicht = Zahl der Meldungszeilen) je Zelle."""
    U, W = np.zeros(E.shape, dtype=int), np.zeros(E.shape)
    for (i, j), r in M.items():
        s = sum(typ_seite(t) for t in str(r.typen).split(","))
        U[i, j] = int(np.sign(s))
        W[i, j] = r.n_zeilen
    return U, W


def gleiche_rate(U_regel, W, n_st, n_bel, rng) -> np.ndarray:
    """Typ-Regel auf der GLEICHEN Zahl Zellen je Seite wie das LLM, gewählt nach Zahl der Meldungen (Gleichstand: Los)."""
    V = np.zeros_like(U_regel)
    for seite, n in ((1, n_st), (-1, n_bel)):
        idx = np.flatnonzero(U_regel.ravel() == seite)
        if not len(idx) or not n:
            continue
        ordn = np.lexsort((rng.random(len(idx)), -W.ravel()[idx]))
        V.ravel()[idx[ordn[:n]]] = seite
    return V


def kurs_regel(E, M, fortsetzung=True) -> np.ndarray:
    """Auskunft: das WORT (Kursreaktion gegen BTC in üblichen Schwankungen, Grenze wie agent.kursreaktion) als Urteil."""
    from agent import kursreaktion as KR
    U = np.zeros(E.shape, dtype=int)
    for (i, j), r in M.items():
        if np.isfinite(r.reaktion_btc) and np.isfinite(r.sigma) and r.sigma > 0:
            alter = max((pd.Timestamp(r.tag).tz_localize("UTC") - pd.Timestamp(r.erst)).total_seconds() / 86400, 1 / 24)
            z = r.reaktion_btc / (r.sigma * math.sqrt(alter))
            s = 1 if z > KR.GRENZE else -1 if z < -KR.GRENZE else 0
            U[i, j] = s if fortsetzung else -s
    return U


# ══ Erzeuger künstlicher Urteile (Selbsttest) ═══════════════════════════════════════════════════════════════════════════════════
def laeufe(E):
    r = []
    for i in range(E.shape[0]):
        x = np.r_[0, E[i].astype(int), 0]
        st, en = np.flatnonzero(np.diff(x) == 1), np.flatnonzero(np.diff(x) == -1)
        r += [(i, s, e) for s, e in zip(st, en)]
    return r


def g_lauf(E, R, rng, je_tag=2.0, anteil_belastet=0.6):
    U = np.zeros(E.shape, dtype=int)
    ziel = je_tag * E.shape[1]
    for j in rng.permutation(len(R)):
        if (U != 0).sum() >= ziel:
            break
        i, s, e = R[j]
        U[i, s:e] = -1 if rng.random() < anteil_belastet else 1
    return U


def g_asset(E, rng, anteil=0.05):
    U = np.zeros(E.shape, dtype=int)
    a = rng.permutation(E.shape[0])
    n = max(1, int(anteil * E.shape[0]))
    U[a[:n]], U[a[n:2 * n]] = -1, 1
    return U * E


def g_markt(E, rng, L=3, je_tag=2.0):
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


def g_paar(E, R, rng, je_tag=2.0, abweichung=0.3):
    """Zwei Arme mit GLEICHER Information: gemeinsamer Kern C, je Arm 30 % der Läufe unabhängig neu gelost."""
    C = g_lauf(E, R, rng, je_tag)
    A, B = C.copy(), C.copy()
    for X in (A, B):
        for (i, s, e) in R:
            if C[i, s] != 0 and rng.random() < abweichung:
                X[i, s:e] = rng.choice((-1, 1))
    return C, A, B


# ══ Selbsttest ══════════════════════════════════════════════════════════════════════════════════════════════════════════════════
def gegenprobe(Z, E, R, rng) -> float:
    U = g_lauf(E, R, rng, 3.0)
    f = t_bahn(U, Z)
    naiv = np.array([t_naiv(np.roll(U, k, axis=1), Z) for k in range(E.shape[1])])
    return float(np.nanmax(np.abs(f - naiv)))


def fa(raenge, band):
    r = np.asarray(raenge, dtype=float)
    r = r[np.isfinite(r)]
    return 100 * float((r > band / 100).mean())


def selbsttest():
    t0 = time.time()
    rng = np.random.default_rng(SAAT)
    Z, E, A, ai, ti, M = panel()
    Z3 = Z[3]
    R = laeufe(E)
    p("G7 S7-ANLAGE SELBSTTEST · %s · Panel %d Assets x %d Tage · Ereigniszellen %d (mit Zielgröße %d) · Läufe %d · %d Ziehungen" % (
        time.strftime("%Y-%m-%d %H:%M"), len(A), len(TAGE), E.sum(), (E & np.isfinite(Z3)).sum(), len(R), ZIEH))
    p("KEIN LLM-Urteil gelesen: alle Urteile künstlich, Zielgrößen echt (H = 3, Start T 01:00).")
    p("Gegenprobe FFT-Bahn gegen naive Schleife (334 Verschiebungen): größte Abweichung %.1e" % gegenprobe(Z3, E, R, rng))

    U_typ, W = typ_regel(E, M)
    erzeuger = (("G-Lauf 2/Tag", lambda r: g_lauf(E, R, r, 2.0)), ("G-Lauf 5/Tag", lambda r: g_lauf(E, R, r, 5.0)),
                ("G-Asset 5 %", lambda r: g_asset(E, r, 0.05)), ("G-Markt L=3", lambda r: g_markt(E, r, 3)),
                ("G-Markt L=10", lambda r: g_markt(E, r, 10)))
    p("")
    p("1 FEHLALARM der Hauptstatistik (Nullwelt Asset-Zeit, Soll ≤ 5 %%, Toleranz %.1f %%, Standardfehler bei %d Ziehungen ≈ 0,7 Pp)"
      % (TOLERANZ, ZIEH))
    raenge = {}
    for name, gen in erzeuger:
        raenge[name] = [rang(t_bahn(gen(rng), Z3)) for _ in range(ZIEH)]
        p("  %-14s %5.1f %%   (%.0f s)" % (name, fa(raenge[name], BAND), time.time() - t0))

    p("")
    p("2 FEHLALARM des gepaarten Vergleichs (zwei Arme mit GLEICHER Information, 'BESSER' darf ≤ 5 % fallen)")
    pr = {"G-Paar 2/Tag, mit Wirkung 0,2 σ": [], "G-Paar 2/Tag, ohne Wirkung": [], "G-Typ (zwei gleich große Zufallsauswahlen der Typ-Regel)": []}
    for _ in range(ZIEH):
        C, Aa, Bb = g_paar(E, R, rng)
        Zp = Z3 + 0.2 * C
        pr["G-Paar 2/Tag, mit Wirkung 0,2 σ"].append(rang(t_bahn(Aa, Zp) - t_bahn(Bb, Zp)))
        pr["G-Paar 2/Tag, ohne Wirkung"].append(rang(t_bahn(Aa, Z3) - t_bahn(Bb, Z3)))
        n_st, n_bel = int((Aa == 1).sum() * 0.5), int((Aa == -1).sum() * 0.5)
        V1 = gleiche_rate(U_typ, rng.random(W.shape), n_st, n_bel, rng)
        V2 = gleiche_rate(U_typ, rng.random(W.shape), n_st, n_bel, rng)
        pr["G-Typ (zwei gleich große Zufallsauswahlen der Typ-Regel)"].append(rang(t_bahn(V1, Z3) - t_bahn(V2, Z3)))
    for name, r_ in pr.items():
        raenge[name] = r_
        p("  %-56s %5.1f %%   (%.0f s)" % (name, fa(r_, BAND), time.time() - t0))

    # Eichung (S7-2): nur wenn ein Erzeuger über der Toleranz liegt - das kleinste Perzentil, bei dem ALLE ≤ 5 % liegen
    p("")
    ueber = [n for n, r_ in raenge.items() if fa(r_, BAND) > TOLERANZ]
    band = BAND
    if ueber:
        for b_ in np.arange(95.0, 99.91, 0.1):
            if all(fa(r_, b_) <= 5.0 for r_ in raenge.values()):
                band = round(float(b_), 1)
                break
        p("3 EICHUNG: über der Toleranz %s -> Band = %.1f. Perzentil (alle Erzeuger ≤ 5 %%: %s)" % (
            ueber, band, ", ".join("%.1f" % fa(r_, band) for r_ in raenge.values())))
    else:
        p("3 EICHUNG: nicht nötig - alle Erzeuger ≤ %.1f %%; Band bleibt das %.0f. Perzentil" % (TOLERANZ, BAND))

    p("")
    p("4 AUFLÖSUNG der Hauptstatistik (Fundquote %%, %d Ziehungen, Band %.1f): z + s an stützt, z − s an belastet, Urteile je Lauf"
      % (ZIEH_PFL, band))
    for je in (2.0, 5.0):
        zeile = []
        for s_ in (0.1, 0.2, 0.3):
            f = 0
            for _ in range(ZIEH_PFL):
                U = g_lauf(E, R, rng, je)
                f += rang(t_bahn(U, Z3 + s_ * U)) > band / 100
            zeile.append("%.1f σ: %3.0f" % (s_, 100 * f / ZIEH_PFL))
        p("  %.0f Urteile/Tag  %s   (%.0f s)" % (je, " · ".join(zeile), time.time() - t0))
    p("")
    p("5 AUFLÖSUNG des gepaarten Vergleichs (Fundquote 'BESSER'): A trägt s, B ist A mit einem Teil der Läufe neu gelost (weniger Info)")
    for s_ in (0.2, 0.3):
        zeile = []
        for anteil in (0.3, 0.5, 1.0):
            f = 0
            for _ in range(ZIEH_PFL // 2):
                U = g_lauf(E, R, rng, 2.0)
                B = U.copy()
                for (i, s, e) in R:
                    if U[i, s] != 0 and rng.random() < anteil:
                        B[i, s:e] = rng.choice((-1, 1))
                Zp = Z3 + s_ * U
                f += rang(t_bahn(U, Zp) - t_bahn(B, Zp)) > band / 100
            zeile.append("B %3.0f %% neu: %3.0f" % (100 * anteil, 100 * f / (ZIEH_PFL // 2)))
        p("  Wirkung %.1f σ  %s   (%.0f s)" % (s_, " · ".join(zeile), time.time() - t0))
    p("")
    p("6 VERGLEICHSARME auf den echten Zielgrößen (Auskunft, KEIN LLM): Typ-Regel voll, Kurs-Regel Fortsetzung / Gegenrichtung")
    for name, U in (("Typ-Regel voll", U_typ), ("Kurs-Regel Fortsetzung", kurs_regel(E, M, True)),
                    ("Kurs-Regel Gegenrichtung", kurs_regel(E, M, False))):
        a_ = arm(U, Z3, band)
        p("  %-26s t %+.2f · Grenze %+.2f · Rang %.3f · stützt %d / belastet %d · Blöcke %d · %s" % (
            name, a_["t"], a_["grenze"], a_["rang"], a_["stuetzt"], a_["belastet"], a_["bloecke"], a_["urteil"]))
    p("")
    p("fertig %.0f s · Band für die Messung: %.1f. Perzentil" % (time.time() - t0, band))
    open(AUS, "w", encoding="utf-8").write("\n".join(TXT) + "\n")
    return band


# ══ Messung (Stufe 2, erst nach dem GANZEN Lauf) ════════════════════════════════════════════════════════════════════════════════
def urteile(sicht: str, ai, ti, E) -> np.ndarray:
    from agent import sichten_gutachten as G
    c = _ro(G.ABLAGE)
    zeilen = c.execute("SELECT tag, felder FROM gutachten WHERE sicht=? AND wdh=0 AND modell=? AND prompt_sha=? AND form_ok=1",
                       (sicht, G.MODELL, G.prompt_sha(sicht))).fetchall()
    n_soll = len(G.tage())
    n_alle = c.execute("SELECT COUNT(*) FROM gutachten WHERE sicht=? AND wdh=0 AND modell=? AND prompt_sha=?",
                       (sicht, G.MODELL, G.prompt_sha(sicht))).fetchone()[0]
    if n_alle < n_soll:
        raise SystemExit("%s: %d von %d Tagen - gemessen wird erst nach dem GANZEN Lauf (Stufe 1 §5.1)" % (sicht, n_alle, n_soll))
    U = np.zeros(E.shape)
    for tag, f in zeilen:
        for e in (json.loads(f).get("assets") or []):
            if isinstance(e, dict) and e.get("asset") in ai and tag in ti:
                w = {"stützt": 1, "stuetzt": 1, "belastet": -1}.get(str(e.get("wirkung")).lower(), 0)
                U[ai[e["asset"]], ti[tag]] += w
    return (np.sign(U) * E).astype(int)


def messen(band: float):
    rng = np.random.default_rng(SAAT + 9)
    Z, E, A, ai, ti, M = panel()
    U7, U7w = urteile("S7", ai, ti, E), urteile("S7w", ai, ti, E)
    U_typ, W = typ_regel(E, M)
    p("G7 S7 MESSUNG · %s · Band %.1f" % (time.strftime("%Y-%m-%d %H:%M"), band))
    for name, U in (("S7 (Form d, HAUPTARM)", U7), ("S7w (Wort-Arm e)", U7w),
                    ("Typ-Regel, Rate wie S7", gleiche_rate(U_typ, W, int((U7 == 1).sum()), int((U7 == -1).sum()), rng))):
        a_ = arm(U, Z[3], band)
        p("  %-24s %s" % (name, a_))
    p("  S7 − Typ-Regel   %s" % paar(U7, gleiche_rate(U_typ, W, int((U7 == 1).sum()), int((U7 == -1).sum()), rng), Z[3], band))
    p("  S7w − S7         %s" % paar(U7w, U7, Z[3], band))
    p("Auskunft (nie hochgestuft): H = 1, H = 5")
    for h in (1, 5):
        p("  H=%d  S7 %s · S7w %s" % (h, arm(U7, Z[h], band)["urteil"], arm(U7w, Z[h], band)["urteil"]))
    kern = np.zeros(E.shape, dtype=bool)
    kern[[ai[k] for k in KERN if k in ai]] = True
    p("  Kern getrennt: S7 %s · ohne Kern %s" % (arm(U7 * kern, Z[3], band), arm(U7 * ~kern, Z[3], band)))
    open(os.path.join(HIER, "g7_s7_messung.txt"), "w", encoding="utf-8").write("\n".join(TXT) + "\n")


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:                                                  # noqa: BLE001
        pass
    if "--messen" in sys.argv:
        import re
        messen(float(re.findall(r"Band für die Messung: (\d+(?:\.\d)?)\.", open(AUS, encoding="utf-8").read())[-1]))
    else:
        selbsttest()
