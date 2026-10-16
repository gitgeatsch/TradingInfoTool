"""P60 W3 VORPRUEFUNG (Stufe 1, Auskunft): Kurzfristiges BTC-Regime (7 T) auf den REGEL0-Einstiegen (16.10.2026).

    python Basisinfos/Rechenkern_02_10/p60_w3_vorpruefung.py > Basisinfos/Rechenkern_02_10/p60_w3_vorpruefung.txt

VORAB FESTGELEGT in Voranalyse_Schritt7 §23.62 (Commit vor dem ersten Aufruf). Nur lesend (mode=ro), kein Netz, schreibt nichts.

  Merkmal     BTC-Rendite 7 T bis zur Signalstunde t: btc[t]/btc[t-168]-1 (wie regel0_llm.signal_werte -> btc168);
              Zustand = Drittel nach Rang gegen die eigenen letzten 12 Monate (rolling 8760, min 4000), kausal - wie W1/W2
  Ziel        Trefferbilanz Q je Einstieg: +1 (+5 % vor -5 % binnen 24 h), -1 (-5 % zuerst), sonst 0 - wie regel0_rechnung A24/B24
  Haupt       D = Q(hoch) - Q(tief), 2024-2026 gemeinsam; zweiseitig; Tagesblock-Bootstrap 2.000, 95 %
  Weiter      W-a Intervall ohne 0 · W-b gleiches Vorzeichen 2024/2025/2026 · W-c beides in >= 3 von 4 Mengen
  Umkehr      Q je Drittel und Jahr; Q <= 0 in >= 2 von 3 Jahren in allen vier Mengen (Auskunft zur Form)
  R-R11       (1) Merkmal bitgleich zu signal_werte btc168 (30 Einstiege) (2) p58-Korrelationen -0,065 / -0,150 / +0,104
  Gegenpruef. die p58-Korrelationen mit Tagesblock-Unsicherheit statt 1/sqrt(n); Tage und Wetterlagen je Jahr
"""
import os
import sys

HIER = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.dirname(os.path.dirname(HIER))
os.chdir(PROJ)
sys.path.insert(0, PROJ)
sys.path.insert(0, HIER)

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

import messe_e2_beitraege as E2  # noqa: E402
from messe_k3_kontextflaeche import reihe  # noqa: E402
import n5_auswertung as A5  # noqa: E402

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:  # noqa: BLE001
    pass

JAHRE = (2024, 2025, 2026)
MENGEN = ("bestand", "unverzerrt_1", "unverzerrt_2", "unverzerrt_3")
ZN = ("tief", "mitte", "hoch")
BOOT = 2000
rng_b = np.random.default_rng(60)

btc = reihe([(E2.EINGESTELLT_DB, "SELECT stunde, close FROM stundenkurse WHERE symbol='BTC'"),
             (E2.STUNDEN_DB, "SELECT stunde, close FROM stundenkurse WHERE symbol='BTC'")])
LH = len(btc)
b7 = np.full(LH, np.nan)
with np.errstate(divide="ignore", invalid="ignore"):
    b7[168:] = btc[168:] / btc[:-168] - 1.0
rang = pd.Series(b7).rolling(8760, min_periods=4000).rank(pct=True).to_numpy()
zust = np.full(LH, -1, np.int8)
fin = np.isfinite(rang)
zust[fin] = np.where(rang[fin] <= 1 / 3, 0, np.where(rang[fin] <= 2 / 3, 1, 2))


def lade(menge):
    E = pd.read_csv(os.path.join("data", "_vergleich", "kern48jbz_einstiege_%s.csv" % menge), sep=";")
    st = E.stunde.to_numpy(np.int64)
    tu = pd.to_numeric(E.t_u, errors="coerce").to_numpy(float)
    td = pd.to_numeric(E.t_d, errors="coerce").to_numpy(float)
    a = (tu <= 24) & (tu < td)
    b = (td <= 24) & (td <= tu)
    E["q"] = a.astype(int) - b.astype(int)
    ok = st < LH
    E["z"] = -1
    E.loc[ok, "z"] = zust[st[ok]]
    E["b7"] = np.nan
    E.loc[ok, "b7"] = b7[st[ok]]
    E["tag"] = st // 24
    return E


def d_wert(g):
    m = g.groupby("z").q.mean()
    return m.get(2, np.nan) - m.get(0, np.nan)


def boot_d(g):
    """Tagesblock-Bootstrap von D: Tage ziehen (mit Zuruecklegen), je Tag Summe und Zahl je Drittel."""
    g = g[g.z >= 0]
    p = g.pivot_table(index="tag", columns="z", values="q", aggfunc=["sum", "count"], fill_value=0)
    s = np.stack([p[("sum", k)].to_numpy() if ("sum", k) in p else np.zeros(len(p)) for k in (0, 2)], 1)
    n = np.stack([p[("count", k)].to_numpy() if ("count", k) in p else np.zeros(len(p)) for k in (0, 2)], 1)
    T = len(p)
    aus = np.empty(BOOT)
    for i in range(BOOT):
        ix = rng_b.integers(0, T, T)
        ss, nn = s[ix].sum(0), n[ix].sum(0)
        aus[i] = ss[1] / max(nn[1], 1) - ss[0] / max(nn[0], 1)
    return np.percentile(aus, [2.5, 97.5])


def rho_boot(x, y, tag):
    """Rangkorrelation und ihre Tagesblock-Unsicherheit (Standardabweichung ueber 2.000 Tagesziehungen)."""
    d = pd.DataFrame({"x": x, "y": y, "t": tag}).dropna()
    r0 = d.x.rank().corr(d.y.rank())
    tage = d.t.unique()
    grp = {t: g.index.to_numpy() for t, g in d.groupby("t")}
    werte = []
    for _ in range(BOOT // 4):
        ix = np.concatenate([grp[t] for t in rng_b.choice(tage, len(tage))])
        s = d.loc[ix]
        werte.append(s.x.rank().corr(s.y.rank()))
    return r0, float(np.std(werte)), len(d), len(tage)


print("P60 W3 VORPRUEFUNG · BTC 7 T (Drittel nach Rang, 12 Monate kausal) auf den REGEL0-Einstiegen · Auskunft, Stufe 1")
print("BTC-Stunden %d (bis %s)\n" % (int(np.isfinite(btc).sum()), (pd.Timestamp("2020-01-01") + pd.Timedelta(hours=LH - 1))))

# ── R-R11 (1): Merkmal bitgleich zu signal_werte btc168 ─────────────────────────────────────────────
E0 = lade("bestand")
rng1 = np.random.default_rng(601)
gleich, verglichen, maxab = 0, 0, 0.0
for i in rng1.choice(len(E0), 60, replace=False):
    r = E0.iloc[i]
    st = (A5.B0 + pd.Timedelta(hours=int(r.stunde))).strftime("%Y-%m-%d %H:%M")
    v = A5.merkmale(r.symbol, st)["btc168"]
    if not np.isfinite(v) or verglichen >= 30:
        continue
    verglichen += 1
    maxab = max(maxab, abs(v - r.b7))
    gleich += int(abs(v - r.b7) < 1e-12)
print("R-R11 (1) Merkmal gegen signal_werte btc168: %d von %d gleich (max. Abweichung %.1e) -> %s" % (
    gleich, verglichen, maxab, "✔ bitgleich" if gleich == verglichen == 30 else "⛔ ABWEICHUNG"))

# ── R-R11 (2) und Gegenpruefung der Praemisse: p58-Stichprobe ────────────────────────────────────────
print("\nR-R11 (2) p58-Stichprobe (Saat 58, 1.200 je Jahr, btc168 gegen 24-h-Ertrag) und GEGENPRUEFUNG mit Tagesbloecken:")
SOLL = {2024: -0.065, 2025: -0.150, 2026: 0.104}
rng = np.random.default_rng(58)
Eroh = pd.read_csv(os.path.join("data", "_vergleich", "kern48jbz_einstiege_bestand.csv"), sep=";")
alle_gleich = True
for j in JAHRE:
    g = Eroh[Eroh.jahr == j]
    g = g.iloc[rng.choice(len(g), size=min(1200, len(g)), replace=False)]
    xs, ys, ts = [], [], []
    for r in g.itertuples():
        st = (A5.B0 + pd.Timedelta(hours=int(r.stunde))).strftime("%Y-%m-%d %H:%M")
        xs.append(A5.merkmale(r.symbol, st)["btc168"])
        ys.append(A5.ertrag24(r.symbol, st))
        ts.append(int(r.stunde) // 24)
    X = pd.DataFrame({"x": xs, "y": ys, "t": ts}).dropna(subset=["y"])
    r58 = X.x.rank().corr(X.y.rank())
    ok = abs(round(r58, 3) - SOLL[j]) < 1e-9
    alle_gleich &= ok
    r0, sd, n, tage = rho_boot(X.x, X.y, X.t)
    print("   %d  rho %+.3f (p58 %+.3f %s) · n %d an %d Tagen · z naiv %+.1f · z Tagesblock %+.1f (Standardabweichung %.3f)" % (
        j, r58, SOLL[j], "✔" if ok else "⛔", n, tage, r58 * np.sqrt(n), r0 / sd if sd else np.nan, sd))
print("   -> R-R11 (2) %s" % ("✔ reproduziert" if alle_gleich else "⛔ NICHT reproduziert"))

# ── Hauptgroesse D je Menge ──────────────────────────────────────────────────────────────────────────
print("\nHAUPTGROESSE D = Q(hoch) - Q(tief) · Q = +1 (+5 %% zuerst) / -1 (-5 %% zuerst) / 0 · Tagesblock %d, 95 %%" % BOOT)
treffer = []
umkehr = {k: [] for k in range(3)}
for m in MENGEN:
    E = E0 if m == "bestand" else lade(m)
    E = E[E.jahr.isin(JAHRE)]
    Ez = E[E.z >= 0]
    D = d_wert(Ez)
    lo, hi = boot_d(Ez)
    dj = {j: d_wert(Ez[Ez.jahr == j]) for j in JAHRE}
    wa = (lo > 0) or (hi < 0)
    wb = len({np.sign(v) for v in dj.values()}) == 1 and np.sign(D) in {np.sign(v) for v in dj.values()}
    treffer.append(wa and wb)
    print("\n  %-13s Einstiege %d (mit Zustand %d) · D %+.4f [%+.4f, %+.4f] · W-a %s · je Jahr %s · W-b %s" % (
        m, len(E), len(Ez), D, lo, hi, "✔" if wa else "–", " / ".join("%+.4f" % dj[j] for j in JAHRE), "✔" if wb else "–"))
    print("    %-6s %s" % ("", "   ".join("%-24s" % ("%d" % j) for j in JAHRE)))
    for k in range(3):
        zeile = []
        nicht_pos = 0
        for j in JAHRE:
            s = Ez[(Ez.jahr == j) & (Ez.z == k)]
            zeile.append("Q %+.4f (n %4d)        " % (s.q.mean(), len(s)))
            nicht_pos += int(s.q.mean() <= 0)
        umkehr[k].append(nicht_pos >= 2)
        print("    %-6s %s" % (ZN[k], "   ".join(zeile)))
    print("    alle   %s" % "   ".join("Q %+.4f (n %4d)        " % (E[E.jahr == j].q.mean(), int((E.jahr == j).sum())) for j in JAHRE))
    rj = []
    for j in JAHRE:
        s = E[E.jahr == j]
        r0, sd, n, tage = rho_boot(s.b7, s.q, s.tag)
        rj.append("%d %+.3f (z naiv %+.1f, Tagesblock %+.1f)" % (j, r0, r0 * np.sqrt(n), r0 / sd if sd else np.nan))
    print("    Auskunft rho(BTC 7 T, Q) je Jahr: " + " · ".join(rj))

# ── Wetterlagen ─────────────────────────────────────────────────────────────────────────────────────
print("\nWETTERLAGEN (Tageszustand um 00 UTC; Lage = zusammenhaengender Lauf desselben Drittels)")
tage = np.arange(LH // 24)
zt = zust[tage * 24]
for j in JAHRE:
    t0 = (pd.Timestamp("%d-01-01" % j) - pd.Timestamp("2020-01-01")).days
    t1 = (pd.Timestamp("%d-01-01" % (j + 1)) - pd.Timestamp("2020-01-01")).days
    s = zt[t0:min(t1, len(zt))]
    s = s[s >= 0]
    laeufe = 1 + int((np.diff(s) != 0).sum()) if len(s) else 0
    je = [int((s == k).sum()) for k in range(3)]
    print("   %d  Tage %d · Lagen %d · Tage je Drittel tief %d / mitte %d / hoch %d" % (j, len(s), laeufe, *je))

# ── Urteil ──────────────────────────────────────────────────────────────────────────────────────────
wc = sum(treffer)
print("\nWEITER-SCHWELLE (vorab): W-a und W-b in >= 3 von 4 Mengen -> %d von 4 -> %s" % (
    wc, "WEITER: Vollmessung vorlegen (Abbruchregel zur Entscheidung)" if wc >= 3 else "NEIN: W3 beendet, das kurzfristige Regime bleibt Auskunft"))
print("UMKEHR (Auskunft): " + " · ".join("%s %s" % (ZN[k], "JA in allen 4 Mengen" if all(umkehr[k]) else "%d von 4 Mengen" % sum(umkehr[k]))
                                         for k in range(3)))
