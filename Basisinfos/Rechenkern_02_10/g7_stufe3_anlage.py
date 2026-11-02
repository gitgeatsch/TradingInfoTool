"""G7 Stufe 3 — MESSANLAGE und SELBSTTEST auf den 903 gemailten REGEL0-Einstiegen (Voranalyse_G7 §10.4 a, §11; Nutzer 02.11.:
*„Ok start mit a, aber vorsicht beim Ergebnis denke ich, regel0 hat im Wesentlichen heute keine Abhängigkeit nur Info der alten bzw
bestehenden LLM Rollen“*). VOR dem ersten LLM-Aufruf: es gibt noch kein Urteil, nur die Anlage und ihre Auflösung.

Nur lesend (Arbeitskopie ``data/_g7/kurse/``, ``data/_g7/regel0/f_einstiege_betrieb_mit_stufe_schalter.csv``). Kein Netz, kein LLM.

VORAB FESTGELEGT (vor jedem Urteil, §11.1):
  Menge       Schalter an + Stufe > 0 (= live gemailt), Einstiege 2025-12-01 .. 2026-10-31
  Urteil      Bedenken des finalen LLM 0/1/2 -> JA = Bedenken >= 1 (Hauptfrage); fachliche Richtung: Bedenken -> SCHLECHTER -> einseitig "unten"
  Zielgröße   ertrag_s = ln(Schluss Einstieg + 24 h / Schluss Einstieg) / σ_T   (σ_T = Std. der Tageslog-Erträge des ASSETS, 60 Tage vor
              dem Einstiegstag) — stetig, je Asset normiert (Zielgröße nicht klassenübergreifend roh). Auskunft: 24-h-Ertrag roh, A24/B24
  Arm HANDEL  Mittel(ertrag_s | ja) − Mittel(| nein); Nullwelt = Kreisverschiebung der Urteile über die zeitlich geordneten Einstiege,
              volle Bahn (exakt; g7_messanlage). Blöcke = 15-Tage-Kalenderblöcke MIT Einstieg (messnorm: H = 24 h -> 15 T); < 20 KEIN BEFUND
  Arm TAG     je Einstiegstag Anteil ja gegen Tagesmittel ertrag_s, Rangkorrelation; Nullwelt Kreisverschiebung über die Einstiegstage
              (Memory *Nullwelt bei geballten Signalen*: Ergebnis je Handel UND je Tag)
  „trägt“     nur, wenn der Arm HANDEL unter dem 5. Perzentil der Nullwelt liegt; der Arm TAG ist Auskunft (wenige Tage, s. Selbsttest)

SELBSTTEST (gegen bekannte Wahrheit, auf den ECHTEN Zielgrößen; 1.000 Ziehungen je Null, Soll ≤ 5 %, Toleranz 6,5 %):
  G-Tag    Tages-Stimmung geballt (Markov über die Einstiegstage, Lauf 1/3/10 T), an Stimmungstagen 80 % ja, sonst 10 %
  G-Handel jeder Einstieg unabhängig, Rate 20 / 40 %
  G-Asset  ein fester Teil der Assets IMMER ja (Asset-Vorurteil, Regel 3) — zeigt, ob die Anlage ein Vorurteil als Wert ausgäbe
  PFLANZUNG an den Ja-Einstiegen ertrag_s − s (s = 0,05 … 0,5 σ) -> Fundquote = Auflösung

    python g7_stufe3_anlage.py
"""
import math
import os
import sqlite3
import sys
import time
from datetime import datetime

import numpy as np
import pandas as pd

HIER = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.dirname(os.path.dirname(HIER))
sys.path.insert(0, PROJ)
import messnorm                                                       # noqa: E402

KOPIE = os.path.join(PROJ, "data", "_g7", "kurse")
EIN = os.path.join(PROJ, "data", "_g7", "regel0", "f_einstiege_betrieb_mit_stufe_schalter.csv")
AUS = os.path.join(PROJ, "data", "_g7", "regel0", "stufe3_einstiege_zielgroesse.csv")
SIGMA_TAGE = 60
H_TAGE = 1
MIN_BLOECKE = 20
TXT = []


def p(*a):
    s = " ".join(str(x) for x in a)
    print(s, flush=True)
    TXT.append(s)


def _ro(f):
    return sqlite3.connect("file:%s?mode=ro" % os.path.join(KOPIE, f).replace("\\", "/"), uri=True)


def einstiege(E: pd.DataFrame | None = None, aus: str = AUS) -> pd.DataFrame:
    """Die 903 gemailten Einstiege (oder ``E``) mit Zielgröße. Kurse: erste Datei gewinnt (wie regel0_messstand)."""
    if E is None:
        E = pd.read_csv(EIN, sep=";")
        E = E[(E.schalter.astype(str) == "True") & (E.stufe > 0)].copy()
    mb = {r[0] for r in _ro("stundenkurse.db").execute("SELECT DISTINCT symbol FROM stundenkurse")}
    con = {f: _ro(f) for f in ("stundenkurse.db", "stundenkurse_alle.db")}
    z = []
    for sym, g in E.groupby("symbol"):
        c = con["stundenkurse.db" if sym in mb else "stundenkurse_alle.db"]
        k = pd.Series(dict(c.execute("SELECT stunde, close FROM stundenkurse WHERE symbol=? AND stunde >= '2025-08-01'", (sym,)).fetchall()))
        k.index = pd.to_datetime(k.index)
        k = k.sort_index().astype(float)
        tag = k.resample("D").last()
        sig = np.log(tag).diff().rolling(SIGMA_TAGE).std().shift(1)            # nur Tage VOR dem Einstiegstag
        for _i, r in g.iterrows():
            t0 = pd.Timestamp(r.stunde)
            p0, p24 = k.get(t0), k.get(t0 + pd.Timedelta(hours=24))
            s_ = sig.get(t0.normalize())
            er = math.log(p24 / p0) if (p0 and p24) else np.nan
            z.append(dict(symbol=sym, stunde=r.stunde, tag=r.stunde[:10], ertrag24=(p24 / p0 - 1) if (p0 and p24) else np.nan,
                          sigma=s_, ertrag_s=er / s_ if (s_ and np.isfinite(er)) else np.nan,
                          a24=(r.t_u <= 24) and (r.t_u < r.t_d), b24=(r.t_d <= 24) and (r.t_d <= r.t_u)))
    for c_ in con.values():
        c_.close()
    Z = pd.DataFrame(z).sort_values(["stunde", "symbol"]).reset_index(drop=True)
    Z.to_csv(aus, sep=";", index=False)
    return Z


def bloecke(tage) -> int:
    """15-Tage-Kalenderblöcke (messnorm._block(H)), die mindestens einen Einstieg enthalten."""
    t = pd.to_datetime(pd.Series(tage))
    return int(((t - pd.Timestamp("2025-12-01")).dt.days // messnorm._block(H_TAGE)).nunique())


def _kreuz(u: np.ndarray, z: np.ndarray) -> np.ndarray:
    """c[k] = Σ_j u[j] · z[(j+k) mod n] für alle k — die volle Bahn der Kreisverschiebung in einem Schritt (FFT)."""
    return np.fft.ifft(np.conj(np.fft.fft(u)) * np.fft.fft(z)).real


def arm_handel(u: np.ndarray, z: np.ndarray) -> tuple:
    """-> (Statistik, Nullwelt k = 1..n-1). Mittel(z | ja) − Mittel(z | nein); m = Zahl ja ist für jede Verschiebung gleich."""
    n, m = len(u), u.sum()
    if m == 0 or m == n:
        return np.nan, np.array([])
    c = _kreuz(u, z)
    s = c / m - (z.sum() - c) / (n - m)
    return float(s[0]), s[1:]


def arm_tag(anteil: np.ndarray, zt: np.ndarray) -> tuple:
    """Rangkorrelation Anteil ja je Tag gegen Tagesmittel; Nullwelt Kreisverschiebung der Tage."""
    a = pd.Series(anteil).rank().to_numpy(); b = pd.Series(zt).rank().to_numpy()
    a = (a - a.mean()) / (a.std() or 1); b = (b - b.mean()) / (b.std() or 1)
    c = _kreuz(a, b) / len(a)
    return float(c[0]), c[1:]


_BAHN = {}


def bahn_tage(Z: pd.DataFrame) -> np.ndarray:
    """Indexmatrix der TAGES-Kreisverschiebung (k = 1 .. Tage−1): der Einstieg an Position j des Tages d bekommt das Urteil des
    Einstiegs an Position (j mod n) des Tages d+k. Eine Tagesstimmung wandert als Ganzes (Selbsttest 02.11.: die Verschiebung um
    EINSTIEGE zerreißt die Tage und gab bei je Tag gebündelten Urteilen 7,1 % Fehlalarm)."""
    key = hash(tuple(Z.tag))          # nach der TAGESSTRUKTUR, nicht id(Z): ids werden neu vergeben (02.11.: falsche Matrix bei Mengenwechsel)
    if key not in _BAHN:
        tage = Z.tag.to_numpy()
        _, start, anz = np.unique(tage, return_index=True, return_counts=True)
        tag_nr = np.repeat(np.arange(len(start)), anz)
        pos = np.arange(len(Z)) - start[tag_nr]
        D = len(start)
        k = np.arange(1, D)[:, None]
        ziel = (tag_nr[None, :] + k) % D
        _BAHN[key] = start[ziel] + pos[None, :] % anz[ziel]
    return _BAHN[key]


def arm_handel_tage(u: np.ndarray, z: np.ndarray, idx: np.ndarray) -> tuple:
    """Wie arm_handel, Nullwelt aber die Tagesbahn (idx aus bahn_tage)."""
    U = u[idx]
    m = U.sum(axis=1)
    with np.errstate(divide="ignore", invalid="ignore"):
        null = (U @ z) / m - ((1 - U) @ z) / (len(z) - m)
    m0 = u.sum()
    s = z[u == 1].mean() - z[u == 0].mean() if 0 < m0 < len(u) else np.nan
    return float(s), null[np.isfinite(null)]


def messe(Z: pd.DataFrame, u: np.ndarray) -> dict:
    z = Z.ertrag_s.to_numpy()
    s_e, null_e = arm_handel(u, z)                       # Auskunft: Verschiebung um EINSTIEGE (erster Bau)
    s, null = arm_handel_tage(u, z, bahn_tage(Z))         # HAUPTARM: Verschiebung um TAGE
    lo = float(np.percentile(null, 5)) if len(null) else np.nan
    T = pd.DataFrame({"tag": Z.tag, "u": u, "z": z}).groupby("tag").mean()
    st, nt = arm_tag(T.u.to_numpy(), T.z.to_numpy())
    return dict(stat=s, null_mitte=float(null.mean()) if len(null) else np.nan, band_unten=lo, traegt=bool(s < lo),
                p=float((null <= s).mean()) if len(null) else np.nan, tag_stat=st, tag_traegt=bool(st < np.percentile(nt, 5)),
                einst_traegt=bool(len(null_e) and s_e < np.percentile(null_e, 5)))


def gegenprobe_fft(rng):
    """Die FFT-Bahn gegen die naive Schleife (np.roll) — dieselben Zahlen?"""
    u = (rng.random(50) < 0.3).astype(float); z = rng.normal(size=50)
    s, null = arm_handel(u, z)
    naiv = [z[np.roll(u, k) == 1].mean() - z[np.roll(u, k) == 0].mean() for k in range(50)]
    return max(abs(s - naiv[0]), float(np.max(np.abs(null - np.array(naiv[1:])))))


def gegenprobe_tage(Z, rng):
    """Die Tagesbahn gegen eine naive Schleife über die Tage — und: ist jede Zeile eine Permutation der Tagesinhalte?"""
    idx = bahn_tage(Z)
    u = (rng.random(len(Z)) < 0.3).astype(float); z = Z.ertrag_s.to_numpy()
    _s, null = arm_handel_tage(u, z, idx)
    tage = list(dict.fromkeys(Z.tag)); grp = {t: np.flatnonzero(Z.tag.to_numpy() == t) for t in tage}
    naiv = []
    for k in range(1, len(tage)):
        v = np.empty(len(Z))
        for d, t in enumerate(tage):
            q = grp[tage[(d + k) % len(tage)]]
            v[grp[t]] = u[q[np.arange(len(grp[t])) % len(q)]]
        if 0 < v.sum() < len(v):
            naiv.append(z[v == 1].mean() - z[v == 0].mean())
    return "größte Abweichung %.1e über %d Verschiebungen" % (float(np.max(np.abs(null - np.array(naiv)))), len(naiv))


def g_tag(Z, rng, L, ja=0.8, nein=0.1, rate=0.3):
    tage = Z.tag.unique()
    p_aus = 1.0 / L
    p_ein = rate * p_aus / (1 - rate)
    x = np.zeros(len(tage), bool); x[0] = rng.random() < rate
    for i in range(1, len(tage)):
        x[i] = (rng.random() >= p_aus) if x[i - 1] else (rng.random() < p_ein)
    st = dict(zip(tage, x))
    pr = np.where(Z.tag.map(st).to_numpy(), ja, nein)
    return (rng.random(len(Z)) < pr).astype(float)


def g_handel(Z, rng, rate):
    return (rng.random(len(Z)) < rate).astype(float)


def g_asset(Z, rng, anteil):
    syms = Z.symbol.unique()
    ja = set(rng.choice(syms, max(1, int(round(anteil * len(syms)))), replace=False))
    return Z.symbol.isin(ja).to_numpy().astype(float)


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:  # noqa: BLE001
        pass
    rng = np.random.default_rng(20261102)
    t0 = time.time()
    p("G7 STUFE 3 — Messanlage und Selbsttest auf den gemailten REGEL0-Einstiegen · %s" % datetime.now().strftime("%Y-%m-%d %H:%M"))
    p("   Gegenprobe FFT-Bahn gegen naive Schleife: größte Abweichung %.1e" % gegenprobe_fft(rng))
    Z = einstiege()
    p("   Gegenprobe Tagesbahn: %s" % gegenprobe_tage(Z.dropna(subset=["ertrag_s"]).reset_index(drop=True), rng))
    ok = Z.ertrag_s.notna()
    p("\n1  EINSTIEGE: %d gemailt · mit Zielgröße %d (ohne: %d) · Tage %d · Assets %d · Blöcke (15 T, mit Einstieg) %d"
      % (len(Z), int(ok.sum()), int((~ok).sum()), Z[ok].tag.nunique(), Z[ok].symbol.nunique(), bloecke(Z[ok].tag)))
    Z = Z[ok].reset_index(drop=True)
    p("   ertrag_s Mittel %+.3f, Std %.3f · 24-h-Ertrag Mittel %+.2f %% · σ (Tag) Median %.2f %% · A24 %.1f %% · B24 %.1f %%"
      % (Z.ertrag_s.mean(), Z.ertrag_s.std(), 100 * Z.ertrag24.mean(), 100 * Z.sigma.median(), 100 * Z.a24.mean(), 100 * Z.b24.mean()))
    p("   je Tag Einstiege: Median %d, max %d · größter Anteil eines Assets %.1f %% (%s)" % (
        Z.groupby("tag").size().median(), Z.groupby("tag").size().max(), 100 * Z.symbol.value_counts(normalize=True).iloc[0],
        Z.symbol.value_counts().index[0]))
    if bloecke(Z.tag) < MIN_BLOECKE:
        p("   ⚠ unter %d Blöcken — KEIN BEFUND möglich" % MIN_BLOECKE)
    N = 1000
    p("\n2  SELBSTTEST NULL (kein Bezug zur Zukunft; einseitig 'unten'; Soll ≤ 5 %%, Toleranz 6,5 %%; %d Ziehungen)" % N)
    p("   %-34s %14s %18s %14s" % ("Generator", "HANDEL (Tage)", "HANDEL (Einstiege)", "TAG (Auskunft)"))
    faelle = [("G-Tag Lauf 1 T", lambda: g_tag(Z, rng, 1)), ("G-Tag Lauf 3 T", lambda: g_tag(Z, rng, 3)),
              ("G-Tag Lauf 10 T", lambda: g_tag(Z, rng, 10)), ("G-Handel Rate 20 %", lambda: g_handel(Z, rng, 0.2)),
              ("G-Handel Rate 40 %", lambda: g_handel(Z, rng, 0.4)), ("G-Asset 20 % der Assets", lambda: g_asset(Z, rng, 0.2)),
              ("G-Asset 40 % der Assets", lambda: g_asset(Z, rng, 0.4))]
    bestanden = True
    for name, gen in faelle:
        fh = ft = fe = 0
        for _ in range(N):
            r = messe(Z, gen())
            fh += r["traegt"]; ft += r["tag_traegt"]; fe += r["einst_traegt"]
        ok_ = fh / N <= 0.065
        bestanden &= ok_ or name.startswith("G-Asset")
        p("   %-34s %12.1f %% %16.1f %% %12.1f %%%s" % (name, 100 * fh / N, 100 * fe / N, 100 * ft / N, "" if ok_ else "  ⚠ über der Toleranz"))
    p("\n3  AUFLÖSUNG (Pflanzung: Ja-Einstiege um s σ schlechter; 500 Ziehungen je Stärke; Fundquote HANDEL (Tage) / TAG)")
    stark = (0.05, 0.1, 0.2, 0.3, 0.5)
    med_sig = float(Z.sigma.median())
    for name, gen in (("G-Handel Rate 30 %", lambda: g_handel(Z, rng, 0.3)), ("G-Tag Lauf 3 T", lambda: g_tag(Z, rng, 3))):
        zeile = []
        for s in stark:
            kh = kt = 0
            for _ in range(500):
                u = gen()
                Zp = Z.assign(ertrag_s=Z.ertrag_s - s * u)
                r = messe(Zp, u)
                kh += r["traegt"]; kt += r["tag_traegt"]
            zeile.append("%.2fσ (≈%.1f %%): %3.0f / %3.0f" % (s, 100 * s * med_sig, kh / 5, kt / 5))
        p("   %-20s %s" % (name, " · ".join(zeile)))
    p("\n   => MESSANLAGE %s (%.0f s)" % ("BESTANDEN (Null HANDEL ≤ 6,5 % bei G-Tag und G-Handel)" if bestanden else "⚠ NICHT BESTANDEN", time.time() - t0))
    with open(os.path.join(HIER, "g7_stufe3_anlage.txt"), "w", encoding="utf-8") as f_:
        f_.write("\n".join(TXT) + "\n")


def mengen():
    """§11.3: dieselbe Auflösung für die Mengen a / b / c der Frage §10.4 — gemessen statt angenommen."""
    rng = np.random.default_rng(20261103)
    E = pd.read_csv(EIN, sep=";")
    gem = (E.schalter.astype(str) == "True") & (E.stufe > 0)
    rest = E[~gem]
    stich = rest.groupby(rest.stunde.str[:10], group_keys=False).apply(lambda g: g.sample(min(5, len(g)), random_state=1))
    p("\n4  AUFLÖSUNG JE MENGE (§10.4) — Pflanzung wie 3, 200 Ziehungen je Stärke; Null 300 Ziehungen (G-Tag Lauf 1 T / G-Handel 30 %)")
    for name, sub in (("a gemailt", E[gem]), ("b gemailt + 5/Tag Stichprobe", pd.concat([E[gem], stich])), ("c alle", E)):
        t0 = time.time()
        Z = einstiege(sub.copy(), os.path.join(PROJ, "data", "_g7", "regel0", "stufe3_zielgroesse_%s.csv" % name[0]))
        Z = Z.dropna(subset=["ertrag_s"]).reset_index(drop=True)
        nh = sum(messe(Z, g_tag(Z, rng, 1))["traegt"] for _ in range(300)) / 300
        ng = sum(messe(Z, g_handel(Z, rng, 0.3))["traegt"] for _ in range(300)) / 300
        z_ = []
        for s_ in (0.05, 0.1, 0.2, 0.3):
            kh = sum(messe(Z.assign(ertrag_s=Z.ertrag_s - s_ * u), u)["traegt"] for u in (g_handel(Z, rng, 0.3) for _ in range(200)))
            kt = sum(messe(Z.assign(ertrag_s=Z.ertrag_s - s_ * u), u)["traegt"] for u in (g_tag(Z, rng, 3) for _ in range(200)))
            z_.append("%.2fσ (≈%.2f %%): %3.0f/%3.0f" % (s_, 100 * s_ * Z.sigma.median(), kh / 2, kt / 2))
        p("   %-30s %6d Einst. %4d Tage %3d Assets · Null %.1f/%.1f %% · Fund G-Handel/G-Tag: %s · %.0f s" % (
            name, len(Z), Z.tag.nunique(), Z.symbol.nunique(), 100 * nh, 100 * ng, " · ".join(z_), time.time() - t0))
    with open(os.path.join(HIER, "g7_stufe3_anlage_mengen.txt"), "w", encoding="utf-8") as f_:
        f_.write("\n".join(TXT) + "\n")


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:  # noqa: BLE001
        pass
    mengen() if "--mengen" in sys.argv else main()
