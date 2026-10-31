# -*- coding: utf-8 -*-
"""G16 Wale STUFE 2 — der Wal-Fluss als GEWICHT in der REGEL0 (Messplan_Wale_29_10.md §16, vorab f69d1822, Nutzer 31.10.: „Stufe 2 a“).

EIN Rechenweg für Vorprüfung, Selbsttest und Messung (der Selbsttest prüft denselben Pfad: dieselbe Zuordnung, dieselbe
Tagesbereinigung, dieselbe Vertauschung). Die Gegenprobe (``p104b_wale_s2_gegenprobe.py``) rechnet absichtlich NICHT hiermit.

    E   unverändert aus Fassung 3/4 über ``p102_wale_basis`` (fluss q 5 %, residuum 180 T, fuenftel 365 T / mindestens 120)
    L   Fünftel von E am Zuordnungstag: Einstieg (Schluss der Stunde) ab 03:00 UTC -> Vortag, sonst Vorvortag
    y   ln(C[j+24] / C[j]) über ``p64_lc_voranalyse.reihe``, brutto
    D   Mittel(y_tag | L=+1) - Mittel(y_tag | L=-1), y_tag = y minus Mittel der Urteilsmenge am selben Einstiegstag

    --vorpruefung   Vollständigkeit, Archiv = Kerze, Zuordnung Symbol <-> Spotpaar, Fallzahlen, AK und Gleichlauf von E — OHNE Erträge
    --selbsttest    S1/S2 Fehlalarm der Regel, S3 Auflösung, Orakel — echte Einstiege und echte y, künstliche L
    --messung       nur nach bestandenem Selbsttest; Urteil je Menge (5 Punkte), TRÄGT bei >= 3 von 4 Mengen; danach Auskunft

    python -X utf8 Basisinfos/Rechenkern_02_10/p104_wale_s2.py --vorpruefung | --selbsttest [--welten 1000] | --messung
"""
import json
import os
import socket
import sqlite3
import sys
from datetime import date, datetime

import numpy as np
import pandas as pd

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HIER)
import p102_wale_basis as B  # noqa: E402
import p103_wale_s2_voranalyse as V  # noqa: E402  (setzt das Arbeitsverzeichnis auf die Projektwurzel)
import p103b_wale_s2_aufloesung as F  # noqa: E402
import p64_lc_voranalyse as P  # noqa: E402
import messnorm as N  # noqa: E402

S2 = os.path.join(B.WURZEL, "data", "_wale", "wale_s2.db")
KOPF = os.path.join(B.WURZEL, "data", "_wale", "s2_head.csv")
CACHE = os.path.join(B.WURZEL, "data", "_wale", "s2_e.npz")
LAUF_A = os.path.join(B.WURZEL, "data", "_hist", "einstiege_A.csv")
AUS = os.path.join(HIER, "p104_wale_s2_%s.txt")
SELBSTTEST = os.path.join(HIER, "p104_wale_s2_selbsttest.json")
VP = os.path.join(B.WURZEL, "data", "_wale", "s2_vorpruefung.json")      # phi, rho, Ausschluss (Zuordnung) aus der Vorprüfung
B.START = date(2023, 1, 1)
TG = B.tage(V.ENDE)                                    # 2023-01-01 .. 2026-08-31
ND = len(TG)
NULL_BLOCK = 30                                        # §16.2: gemeinsame 30-T-Blöcke (wie Fassung 4d)
PERM = 1000
STICHTAG_H = 3                                         # §16.2 / Voranalyse Teil E
JAHRE = (2024, 2025, 2026)
AUFFAELLIG = 0.005                                     # Archiv/Kerze mehr als 0,5 % daneben -> Tag gilt als fehlend
GRENZE = 0.05 + 2 * np.sqrt(0.05 * 0.95 / 1000)        # 6,4 % (Regel 11.10.)
STARTWERT_SELBST, STARTWERT_MESS = 20261105, 20261106
KS = (0.0005, 0.0010, 0.0015, 0.0020, 0.0025)          # S3-Pflanzung in Log-Einheiten (0,05 .. 0,25 Pp; D verschiebt um ~2k)


def kopf(was, extra=""):
    return "%s G16 STUFE 2 (Messplan §16, %s, %s)%s" % (was, socket.gethostname(), datetime.now().isoformat(timespec="seconds"), extra)


def schreibe(name, z, vorher):
    z.append("\nSeiteneffekt: geschützte Datei unverändert: %s" % (vorher == B.fingerabdruck()))
    text = "\n".join(z)
    print(text)
    with open(AUS % name, "w", encoding="utf-8") as f:
        f.write(text + "\n")


def pp(x):
    return "%+.2f" % (100 * x) if np.isfinite(x) else "  –  "


# ── Zuordnung Symbol -> Spotpaar, E und L je Symbol ─────────────────────────────────────────────────────────────────────
def paare():
    T = pd.read_csv(KOPF)
    v = T[T.bytes > 0]
    m = v.groupby("symbol").paar.agg(lambda x: x.value_counts().index[0]).to_dict()
    letzt = v[v.paar == v.symbol.map(m)].groupby("symbol").monat.max().to_dict()
    for s in V.GELADEN:
        m[s] = s + "USDT"
    return m, {s for s, mo in letzt.items() if mo < "2026-08"}       # eingestellt: letzter Archivmonat vor 08/2026


def auffaellig(con, paar):
    return {d for (d,) in con.execute("SELECT datum FROM tag WHERE symbol=? AND markt='spot' AND "
                                      "(kerze_usd IS NULL OR ABS(umsatz_usd / kerze_usd - 1) > ?)", (paar, AUFFAELLIG))}


def berechne_e():
    """-> (Symbole, E, LAB, AUFF) als Matrizen [Symbol, Tag]. Zwischenspeicher, weil 177 x 1.339 Regressionen."""
    if os.path.exists(CACHE):
        z = np.load(CACHE, allow_pickle=False)
        return list(z["sym"]), z["E"], z["LAB"], z["AUFF"]
    m, _ = paare()
    cons = {"s2": B.ro(S2), "voll": B.ro(B.ABLAGE)}
    sym, Es, Ls, As = [], [], [], []
    for s, paar in sorted(m.items()):
        con = cons["voll" if s in V.GELADEN else "s2"]
        g, r = B.fluss(con, paar, "spot", TG)[B.Q_HAUPT]
        if not np.isfinite(g).any():
            continue
        au = auffaellig(con, paar)
        mk = np.array([d.isoformat() in au for d in TG])
        g, r = np.where(mk, np.nan, g), np.where(mk, np.nan, r)
        e = B.residuum(g, r, B.bewegung(B.kurse(con, paar), TG))
        sym.append(s)
        Es.append(e)
        Ls.append(B.fuenftel(e))
        As.append(mk)
    for c in cons.values():
        c.close()
    E, LAB, AUFF = np.array(Es), np.array(Ls), np.array(As)
    np.savez(CACHE, sym=np.array(sym), E=E, LAB=LAB, AUFF=AUFF)
    return sym, E, LAB, AUFF


def fuenftel_matrix(Z):
    """Vektorisiert wie ``B.fuenftel`` (Fenster t-365..t-1, mindestens 120, lineares Quantil) — für den Selbsttest; die Gegenprobe
    prüft die Gleichheit auf dem echten E."""
    sh = pd.DataFrame(Z.T).shift(1).rolling(B.FENSTER_RANG, min_periods=B.MIN_BEOB)
    hi, lo = sh.quantile(0.8).to_numpy().T, sh.quantile(0.2).to_numpy().T
    with np.errstate(invalid="ignore"):
        lab = np.where(Z > hi, 1.0, np.where(Z < lo, -1.0, 0.0))
    lab[~np.isfinite(Z) | ~np.isfinite(hi)] = np.nan
    return lab


# ── Einstiege ───────────────────────────────────────────────────────────────────────────────────────────────────────────
def zuordnungstag(ein, vorvortag_immer=False):
    h = ein.dt.hour.to_numpy()
    zurueck = np.full(len(ein), 2) if vorvortag_immer else np.where(h >= STICHTAG_H, 1, 2)
    return ((ein.dt.normalize() - pd.to_timedelta(zurueck, unit="D") - pd.Timestamp(B.START)) / pd.Timedelta(days=1)).astype(int).to_numpy()


def bereite(e, sym, LAB, vorvortag_immer=False, y=None):
    """Einstiege einer Menge -> DataFrame mit si (Symbolzeile), ei (Zuordnungstag), tag (Einstiegstag), y, L, ungesehen."""
    e = e.copy()
    idx = {s: i for i, s in enumerate(sym)}
    e["si"] = e.symbol.map(idx).fillna(-1).astype(int).to_numpy()
    e["ei"] = zuordnungstag(e.ein, vorvortag_immer)
    e["tag"] = e.ein.dt.normalize()
    e["y"] = F.ertraege(e) if y is None else y
    ok = (e.si >= 0) & (e.ei >= 0) & (e.ei < ND)
    e["L"] = np.nan
    e.loc[ok, "L"] = LAB[e.si[ok], e.ei[ok]]
    e["ungesehen"] = ~e.symbol.isin(V.GELADEN)
    return e


def tagesbereinigt(y, tag):
    return y - pd.Series(y).groupby(np.asarray(tag)).transform("mean").to_numpy()


class Menge:
    """Urteilsmenge einer Einstiegsmenge: ungesehene Symbole, mit L und y. Tagesbereinigung INNERHALB dieser Menge."""

    def __init__(self, e, maske=None):
        mk = e.ungesehen & np.isfinite(e.L) & np.isfinite(e.y) if maske is None else maske
        u = e[mk].reset_index(drop=True)
        self.e = u
        self.si, self.ei, self.y = u.si.to_numpy(), u.ei.to_numpy(), u.y.to_numpy()
        self.tag = u.tag.to_numpy()
        self.yt = tagesbereinigt(self.y, self.tag)
        self.jahr = u.jahr.to_numpy()
        self.d0, self.d1 = int(self.ei.min()), int(self.ei.max())
        self.codes, self.assets = pd.factorize(u.symbol)
        self.onehot = np.zeros((len(u), len(self.assets)))
        self.onehot[np.arange(len(u)), self.codes] = 1.0
        self.n_bloecke = -(-(self.d1 - self.d0 + 1) // NULL_BLOCK)

    def neu_y(self, y):
        self.y = y
        self.yt = tagesbereinigt(y, self.tag)


def vertauschungen(rng, d0, d1, n=PERM):
    """(n, Länge) — neue Tagesnummer je Kalendertag des Rasters; Block 30 T, für alle Symbole DIESELBE Vertauschung."""
    lang = d1 - d0 + 1
    bl = [np.arange(i * NULL_BLOCK, min((i + 1) * NULL_BLOCK, lang)) for i in range(-(-lang // NULL_BLOCK))]
    return np.array([np.concatenate([bl[i] for i in rng.permutation(len(bl))]) for _ in range(n)]) + d0


def d_zeilen(L, yt):
    o, u = (L == 1), (L == -1)
    with np.errstate(invalid="ignore", divide="ignore"):
        return (o @ yt) / o.sum(1) - (u @ yt) / u.sum(1)


def anteil_neg(L, y, onehot):
    """Signalbilanz je Asset: Anteil der Assets mit Sum y(oben) - Sum y(unten) < 0 (roh), unter den Assets mit Wert != 0."""
    w = (L == 1).astype(float) - (L == -1).astype(float)
    delta = (w * y) @ onehot
    nz = np.abs(delta) > 0
    return ((delta < 0) & nz).sum(1) / np.maximum(nz.sum(1), 1)


def test_punkt1(M, LAB, rng, voll=False):
    """Punkt 1: D (tagesbereinigt) gegen 1.000 gemeinsame 30-T-Vertauschungen der L-Reihen. ``voll``: dazu die Nullverteilung der
    Signalbilanz (Punkt 4) aus denselben Vertauschungen."""
    L = LAB[M.si, M.ei][None, :]
    d = float(d_zeilen(L, M.yt)[0])
    maps = vertauschungen(rng, M.d0, M.d1)
    Lp = LAB[M.si[None, :], maps[:, M.ei - M.d0]]
    null = d_zeilen(Lp, M.yt)
    null = null[np.isfinite(null)]
    aus = {"D": d, "schwelle": float(np.quantile(null, 0.95)), "null_mittel": float(null.mean()), "p": float((1 + (null >= d).sum()) / (1 + len(null)))}
    aus["p1"] = bool(d > aus["schwelle"] and M.n_bloecke >= 20)
    if voll:
        aus["neg"] = float(anteil_neg(L, M.y, M.onehot)[0])
        nn = anteil_neg(Lp, M.y, M.onehot)
        aus["neg_q95"], aus["neg_null"] = float(np.quantile(nn, 0.95)), float(nn.mean())
        aus["null_q95_abstand"] = aus["schwelle"] - aus["null_mittel"]
    return aus


def lade_mengen(sym, LAB, vorvortag_immer=False):
    return {m: bereite(e, sym, LAB, vorvortag_immer) for m, e in V.einstiege().items()}


def regel(p1s):
    return sum(p1s) >= 3


# ── Vorprüfung ──────────────────────────────────────────────────────────────────────────────────────────────────────────
def vorpruefung() -> int:
    vorher = B.fingerabdruck()
    z = [kopf("VORPRÜFUNG", " · OHNE Erträge (keine y, kein D)")]
    ok = True
    m, eingestellt = paare()
    con = B.ro(S2)
    # 1 Vollständigkeit der Monatsdateien
    import wale_s2_laden as WL
    alle = WL.auftraege()
    fertig = {(s, mo): (t, zl) for s, mo, t, zl in con.execute("SELECT symbol, monat, tage, zeilen FROM monat")}
    fehlt = [a for a in alle if (a[0], a[1]) not in fertig]
    erst = {}
    letzt = {}
    for p_, mo, _b in alle:
        erst[p_] = min(erst.get(p_, mo), mo)
        letzt[p_] = max(letzt.get(p_, mo), mo)
    kurz = [(p_, mo, fertig[(p_, mo)][0]) for p_, mo, _b in alle if (p_, mo) in fertig and mo not in (erst[p_], letzt[p_])
            and fertig[(p_, mo)][0] != pd.Period(mo).days_in_month]
    # Maßstab (31.10., nach dem ersten Lauf): ein Tag FEHLT, wenn REST für ihn Umsatz meldet und das Archiv ihn nicht hat. Monate mit
    # weniger Tagen als der Kalender sind bei REST genauso kurz (Handelspause, BNX 2023-02, KEY 2023-02/03) und keine Lücke.
    rest = {(s, d) for s, d in con.execute("SELECT symbol, datum FROM kerze WHERE quote_usd > 0 AND datum BETWEEN ? AND ?",
                                            (B.START.isoformat(), V.ENDE.isoformat()))}
    archiv = {(s, d) for s, d in con.execute("SELECT symbol, datum FROM tag")}
    spanne = {p_: (erst[p_] + "-01", letzt[p_] + "-31") for p_ in erst}
    luecke = sorted(x for x in rest - archiv if x[0] in spanne and spanne[x[0]][0] <= x[1] <= spanne[x[0]][1])
    ok &= not fehlt and not luecke
    z.append("\n1 VOLLSTÄNDIGKEIT: Monatsdateien %d von %d geladen · fehlend %d · Tage mit REST-Umsatz, die im Archiv fehlen: %d %s"
             % (len(fertig), len(alle), len(fehlt), len(luecke), "✔" if not fehlt and not luecke else "✖"))
    z.append("    Auskunft: Monate (nicht erster/letzter) mit weniger Tagen als der Kalender: %d %s — bei REST gleich kurz (Handelspause)"
             % (len(kurz), [k[:2] for k in kurz]))
    for x in (fehlt[:5] + luecke[:10]):
        z.append("    %s" % (x,))
    # 2 Archiv = Kerze
    t = pd.read_sql_query("SELECT symbol, datum, umsatz_usd, kerze_usd, erste_utc, letzte_utc FROM tag", con)
    t["v"] = t.umsatz_usd / t.kerze_usd
    t["auff"] = t.kerze_usd.isna() | ((t.v - 1).abs() > AUFFAELLIG)
    je = t.groupby("symbol").auff.mean()
    anteil = float(t.auff.mean())
    gut = anteil <= 0.01 and je.max() <= 0.05
    ok &= gut
    z.append("\n2 ARCHIV = KERZE (Tagesumsatz Archiv / REST, ±0,5 %%): %d Tage · auffällig %d (%.2f %%) · Symbole mit > 1 %%: %d · größter Anteil %.1f %% (%s) %s"
             % (len(t), t.auff.sum(), 100 * anteil, (je > 0.01).sum(), 100 * je.max(), je.idxmax(), "✔" if gut else "✖ (Soll <= 1 % gesamt, <= 5 % je Symbol)"))
    z.append("    Verhältnis Archiv/Kerze: Median %.5f · 1.–99. Perzentil %.4f .. %.4f · auffällige Tage gelten als FEHLEND (G und R NaN)" % (
        t.v.median(), t.v.quantile(0.01), t.v.quantile(0.99)))
    spaet = ((t.erste_utc.str[11:16] > "01:00") | (t.letzte_utc.str[11:16] < "23:00")).mean()
    z.append("    Tagesabdeckung: erster Handel nach 01:00 oder letzter vor 23:00 an %.2f %% der Tage (dünne Werte, Auskunft)" % (100 * spaet))
    # 3 Zuordnung Symbol <-> Spotpaar (vier Symbolwelten: keine Brücke ohne Nachweis)
    z.append("\n3 ZUORDNUNG Symbol (REGEL0, reihe) <-> Spotpaar (Archiv): Tagesrendite-Korrelation >= 0,9 und Preisverhältnis stabil (Streuung < 2 %)")
    kz = pd.read_sql_query("SELECT symbol, datum, schluss FROM kerze", con)
    kz["datum"] = pd.to_datetime(kz.datum)
    schlecht = []
    E_sym = sorted(set().union(*[set(e.symbol) for e in V.einstiege().values()]))
    n_gepr = 0
    for s in E_sym:
        if s not in m or s in V.GELADEN:
            continue
        x = P.reihe(s)
        k = kz[kz.symbol == m[s]].set_index("datum").schluss
        if x is None or k.empty:
            schlecht.append((s, "keine Reihe" if x is None else "keine Kerze"))
            continue
        a, _L, C = x
        h = ((k.index - P.B0) / pd.Timedelta(hours=1)).astype(int).to_numpy() + 23 - a      # Stunde 23:00-24:00 des Tages
        okh = (h >= 0) & (h < len(C))
        c = pd.Series(np.where(okh, C[np.clip(h, 0, len(C) - 1)], np.nan), index=k.index)
        f = pd.DataFrame({"r": np.log(c).diff(), "s": np.log(k).diff(), "v": c / k}).dropna()
        f = f[np.isfinite(f).all(axis=1)]
        if len(f) < 100:
            schlecht.append((s, "nur %d gemeinsame Tage" % len(f)))
            continue
        n_gepr += 1
        kor, streu = f.r.corr(f.s), f.v.std() / f.v.mean()
        if kor < 0.9 or streu > 0.02:
            schlecht.append((s, "Korrelation %.3f, Verhältnis %.4f ± %.1f %%" % (kor, f.v.median(), 100 * streu)))
    z.append("    geprüft %d Symbole · auffällig %d" % (n_gepr, len(schlecht)))
    for s, g in schlecht:
        z.append("    ✖ %-10s %s" % (s, g))
    z.append("    ⚠️ auffällige Zuordnungen bleiben OHNE E (keine Brücke ohne Nachweis); %s" % ("keine" if not schlecht else "siehe oben"))
    con.close()
    # 4 E, Fallzahlen, AK, Gleichlauf
    sym, E, LAB, AUFF = berechne_e()
    for s, g in schlecht:
        if s in sym:
            LAB[sym.index(s)] = np.nan
    phis = []
    for e in E:
        f = np.isfinite(e[:-1]) & np.isfinite(e[1:])
        if f.sum() > 200:
            phis.append(np.corrcoef(e[:-1][f], e[1:][f])[0, 1])
    kor = pd.DataFrame(E.T).corr(min_periods=200).to_numpy()
    rho = float(np.nanmean(kor[np.triu_indices_from(kor, 1)]))
    z.append("\n4 E: %d Symbole mit E · AK(1) Mittel %+.3f (Spanne %+.3f .. %+.3f) · Gleichlauf rho %+.3f (Mittel aller Paare, >= 200 gemeinsame Tage)"
             % (len(sym), np.mean(phis), np.min(phis), np.max(phis), rho))
    mengen = lade_mengen(sym, LAB)
    for name, e in mengen.items():
        U = e.ungesehen & np.isfinite(e.L) & e.y.notna()
        M = Menge(e)
        je = " · ".join("%d: %d/%d/%d" % (j, ((e.L == 1) & U & (e.jahr == j)).sum(), ((e.L == 0) & U & (e.jahr == j)).sum(),
                                          ((e.L == -1) & U & (e.jahr == j)).sum()) for j in JAHRE)
        z.append("  %-13s Urteilsmenge %5d Einstiege, %3d Symbole · oben/mitte/unten %s · Zuordnungstage %s..%s -> %d Blöcke %s · mit L gesamt %d"
                 % (name, U.sum(), e[U].symbol.nunique(), je, TG[M.d0], TG[M.d1], M.n_bloecke, "✔" if M.n_bloecke >= 20 else "✖",
                    (np.isfinite(e.L) & e.y.notna()).sum()))
        ok &= M.n_bloecke >= 20
    with open(VP, "w", encoding="utf-8") as f:
        json.dump({"phi": float(np.mean(phis)), "rho": rho, "ausschluss": [s for s, _ in schlecht], "bestanden": bool(ok)}, f)
    ok &= vorher == B.fingerabdruck()
    z.append("\nERGEBNIS: %s" % ("BESTANDEN" if ok else "NICHT BESTANDEN"))
    schreibe("vorpruefung", z, vorher)
    return 0 if ok else 1


def lade_alles():
    sym, E, LAB, AUFF = berechne_e()
    vp = json.load(open(VP, encoding="utf-8"))
    for s in vp["ausschluss"]:
        if s in sym:
            LAB[sym.index(s)] = np.nan
            E[sym.index(s)] = np.nan
    return sym, E, LAB, vp


# ── Selbsttest ──────────────────────────────────────────────────────────────────────────────────────────────────────────
def selbsttest() -> int:
    welten = int(sys.argv[sys.argv.index("--welten") + 1]) if "--welten" in sys.argv else 1000
    vorher = B.fingerabdruck()
    rng = np.random.default_rng(STARTWERT_SELBST)
    sym, E, LAB, vp = lade_alles()
    phi, rho = vp["phi"], max(0.0, vp["rho"])
    maske = np.isfinite(E)
    ns = len(sym)
    mengen = lade_mengen(sym, LAB)
    MS = {m: Menge(e) for m, e in mengen.items()}
    monat = np.unique(np.array([d.year * 12 + d.month for d in TG]), return_inverse=True)[1]
    s1f = np.sqrt(max(1e-9, 1 - phi ** 2))
    z = [kopf("SELBSTTEST", " · %d Welten · echte Einstiege und y, künstliche L · EINSEITIG · Startwert %d" % (welten, STARTWERT_SELBST))]
    z.append("Soll: Fehlalarm der REGEL (Punkt 1 in >= 3 von 4 Mengen) S1/S2 <= %.1f %% · Orakel >= 190/200 · Nullwelt 30 T gemeinsam, %d Vertauschungen"
             % (100 * GRENZE, PERM))
    z.append("phi %.3f · rho %.3f (aus der Vorprüfung) · Urteilsmengen %s" % (phi, rho, " · ".join("%s %d" % (m, len(M.y)) for m, M in MS.items())))

    def s1():
        c = np.empty(ND)
        e = np.empty((ns, ND))
        c[0], e[:, 0] = rng.standard_normal(), rng.standard_normal(ns)
        for t in range(1, ND):
            c[t] = phi * c[t - 1] + s1f * rng.standard_normal()
            e[:, t] = phi * e[:, t - 1] + s1f * rng.standard_normal(ns)
        return np.where(maske, np.sqrt(rho) * c[None, :] + np.sqrt(1 - rho) * e, np.nan)

    def s2():
        mm = rng.standard_normal(monat.max() + 1)[monat]
        return np.where(maske, mm[None, :] + 0.2 * rng.standard_normal((ns, ND)), np.nan)

    fehl = {}
    for name, welt in (("S1", s1), ("S2", s2)):
        regel_n, je = 0, {m: 0 for m in MS}
        for w in range(welten):
            LW = fuenftel_matrix(welt())
            p1 = {m: test_punkt1(M, LW, rng)["p1"] for m, M in MS.items()}
            regel_n += regel(p1.values())
            for m in MS:
                je[m] += p1[m]
            if (w + 1) % 100 == 0:
                print("  %s %d/%d · Regel %.1f %%" % (name, w + 1, welten, 100 * regel_n / (w + 1)), flush=True)
        fehl[name] = {"regel": regel_n / welten, **{m: je[m] / welten for m in MS}}
    z.append("\nFEHLALARM (TRÄGT HÖHER, Punkt 1)")
    for name in ("S1", "S2"):
        f = fehl[name]
        z.append("  %s  Regel %5.1f %% %s · je Menge %s" % (name, 100 * f["regel"], "✔" if f["regel"] <= GRENZE else "✖ über %.1f %%" % (100 * GRENZE),
                                                         " · ".join("%s %.1f %%" % (m, 100 * f[m]) for m in MS)))
    halt = fehl["S1"]["regel"] <= GRENZE and fehl["S2"]["regel"] <= GRENZE
    n3 = max(100, welten // 4) if welten >= 400 else welten          # kleine Läufe nur als Codeprobe
    z.append("\nS3 AUFLÖSUNG (%d Welten je k, Signal wie S1, Pflanzung y + k·L vor der Tagesbereinigung) — k in Pp" % n3)
    y0 = {m: M.y.copy() for m, M in MS.items()}
    quote = []
    for k in KS:
        t = 0
        for _ in range(n3):
            LW = fuenftel_matrix(s1())
            p1 = []
            for m, M in MS.items():
                lw = LW[M.si, M.ei]
                M.neu_y(y0[m] + k * np.where(np.isfinite(lw), lw, 0))
                p1.append(test_punkt1(M, LW, rng)["p1"])
            t += regel(p1)
        quote.append(t / n3)
        print("  S3 k %.2f Pp: %.0f %%" % (100 * k, 100 * quote[-1]), flush=True)
    for m, M in MS.items():
        M.neu_y(y0[m])
    x = next((k for k, q in zip(KS, quote) if q >= 0.8), None)
    z.append("  %s  ->  X = %s" % ("  ".join("%.2f:%3.0f%%" % (100 * k, 100 * q) for k, q in zip(KS, quote)),
                                    ("%.2f Pp (D-Unterschied ~%.2f Pp)" % (100 * x, 200 * x)) if x else "über 0,25 Pp"))
    z.append("\nORAKEL (200 Welten, E = y des Einstiegs am Zuordnungstag + Rauschen gleicher Streuung)")
    sy = float(np.nanstd(np.concatenate([M.y for M in MS.values()])))
    summe, zahl = np.zeros((ns, ND)), np.zeros((ns, ND))
    for M in MS.values():
        np.add.at(summe, (M.si, M.ei), M.y)
        np.add.at(zahl, (M.si, M.ei), 1)
    sig = np.where(zahl > 0, summe / np.maximum(zahl, 1), 0.0)
    orakel = 0
    for _ in range(200):
        LW = fuenftel_matrix(np.where(maske, sig + sy * rng.standard_normal((ns, ND)), np.nan))
        orakel += regel([test_punkt1(M, LW, rng)["p1"] for M in MS.values()])
    z.append("  %d von 200 %s" % (orakel, "✔" if orakel >= 190 else "✖"))
    bestanden = bool(halt and orakel >= 190)
    z.append("\nERGEBNIS: %s · X %s" % ("BESTANDEN" if bestanden else "NICHT BESTANDEN", ("%.2f Pp" % (100 * x)) if x else "über 0,25 Pp"))
    schreibe("selbsttest", z, vorher)
    if welten >= 1000:
        with open(SELBSTTEST, "w", encoding="utf-8") as f:
            json.dump({"bestanden": bestanden, "null_block": NULL_BLOCK, "welten": welten, "grenze": GRENZE, "phi": phi, "rho": rho,
                       "fehl": fehl, "X": x, "quote": dict(zip(map(str, KS), quote)), "orakel": orakel, "startwert": STARTWERT_SELBST}, f, indent=1)
    return 0 if bestanden else 1


# ── Messung ─────────────────────────────────────────────────────────────────────────────────────────────────────────────
def block_ok(M, LAB):
    L = LAB[M.si, M.ei]
    v = pd.Series(np.where(L != 0, L * M.yt, np.nan)).groupby(M.ei).mean().dropna()
    pb = N.pruefe_block(v.to_dict(), NULL_BLOCK)
    return pb["ok"] or not np.isfinite(pb["ak"]), pb["ak"]


def messung() -> int:
    if not os.path.exists(SELBSTTEST):
        print("✖ kein Selbsttest Stufe 2 (%s) - nicht messen" % SELBSTTEST)
        return 1
    st = json.load(open(SELBSTTEST, encoding="utf-8"))
    if not st.get("bestanden") or st.get("null_block") != NULL_BLOCK or st.get("welten", 0) < 1000:
        print("✖ Selbsttest nicht bestanden oder für eine andere Nullwelt - nicht messen")
        return 1
    vorher = B.fingerabdruck()
    rng = np.random.default_rng(STARTWERT_MESS)
    sym, E, LAB, vp = lade_alles()
    _m, eingestellt = paare()
    mengen = lade_mengen(sym, LAB)
    X = st["X"]
    z = [kopf("MESSUNG", " · einseitig (oberstes Fünftel HÖHER) · q 5 % · 24 h Log brutto · Urteilsmenge ungesehen, tagesbereinigt")]
    z.append("Selbsttest ✔ (S1 %.1f %%, S2 %.1f %%, Orakel %d/200, X %s)" % (100 * st["fehl"]["S1"]["regel"], 100 * st["fehl"]["S2"]["regel"],
                                                                         st["orakel"], ("%.2f Pp" % (100 * X)) if X else "über 0,25 Pp"))
    z.append("\n══ URTEIL je Menge (§16.3) ══")
    erg, traegt_je = {}, {}
    for name, e in mengen.items():
        M = Menge(e)
        r = test_punkt1(M, LAB, rng, voll=True)
        bok, ak = block_ok(M, LAB)
        alle = e[np.isfinite(e.L) & e.y.notna()]
        summe = float(alle.y[alle.L == 1].sum() - alle.y[alle.L == -1].sum())
        Lm = LAB[M.si, M.ei]
        jahre = {j: float(d_zeilen(Lm[None, M.jahr == j], M.yt[M.jahr == j])[0]) for j in JAHRE}
        p = [r["p1"] and bok, summe > 0, sum(v > 0 for v in jahre.values()) >= 2, r["neg"] <= r["neg_q95"], True]
        traegt_je[name] = all(p)
        obergrenze = r["D"] + r["null_q95_abstand"] - r["null_mittel"]
        stufe = ("TRÄGT" if all(p) else ("TRÄGT NICHT BIS %.2f Pp" % (200 * X) if X and obergrenze < 2 * X else "NICHT TRENNBAR")
                 if bok else "KEIN BEFUND - Block 30 zu kurz (AK %.3f)" % ak)
        erg[name] = dict(r, summe=summe, jahre=jahre, block_ak=ak, punkte=p, stufe=stufe, n=len(M.y), n_sym=len(M.assets),
                         n_oben=int((Lm == 1).sum()), n_unten=int((Lm == -1).sum()))
        z.append("  %-13s n %5d (%d Symbole, oben %d / unten %d) · D %s Pp · Schwelle %s (p %.3f) · Null %s · Blöcke %d, AK %.3f" % (
            name, len(M.y), len(M.assets), erg[name]["n_oben"], erg[name]["n_unten"], pp(r["D"]), pp(r["schwelle"]), r["p"], pp(r["null_mittel"]),
            M.n_bloecke, ak))
        z.append("                1 Test %s · 2 Summe roh %s Pp-Einstiege %s · 3 Jahre %s %s · 4 Assets mit Minus %.1f %% (Null %.1f %%, 95. P. %.1f %%) %s · 5 Selbsttest ✔"
                 % ("✔" if p[0] else "✖", pp(summe), "✔" if p[1] else "✖", " ".join("%d %s" % (j, pp(v)) for j, v in jahre.items()),
                    "✔" if p[2] else "✖", 100 * r["neg"], 100 * r["neg_null"], 100 * r["neg_q95"], "✔" if p[3] else "✖"))
        z.append("                -> %s" % stufe)
    n_tr = sum(traegt_je.values())
    gesamt = n_tr >= 3
    z.append("\n══ GESAMT (>= 3 von 4 Mengen) ══")
    z.append("  %d von 4 Mengen tragen -> %s" % (n_tr, "TRÄGT: E ordnet die REGEL0-Einstiege, ohne Verschlechterung -> Bauentscheid zur Abstimmung"
                                                   if gesamt else "TRÄGT NICHT nach §16.3 -> REGEL0 unverändert, G16 als Dashboard-Befund"))
    # ── Auskunft (§16.5), nach dem Urteil, nicht Teil davon ──
    z.append("\n══ AUSKUNFT (§16.5) — nach dem Urteil, NICHT Teil davon ══")
    for name, e in mengen.items():
        M = Menge(e)
        Lm = LAB[M.si, M.ei]
        d_roh = float(d_zeilen(Lm[None, :], M.y)[0])
        mittel = " / ".join(pp(M.y[Lm == k].mean()) for k in (1, 0, -1))
        teile = []
        for titel, mk in (("Kern", e.symbol.isin(V.KERN)), ("Fassung 4", e.symbol.isin(V.F4)), ("eingestellt", e.symbol.isin(eingestellt))):
            mm = mk & np.isfinite(e.L) & e.y.notna()
            if ((e.L[mm] == 1).sum() > 0) and ((e.L[mm] == -1).sum() > 0):
                MM = Menge(e, mm)
                LL = LAB[MM.si, MM.ei]
                teile.append("%s n %d: tb %s / roh %s" % (titel, len(MM.y), pp(d_zeilen(LL[None, :], MM.yt)[0]), pp(d_zeilen(LL[None, :], MM.y)[0])))
        z.append("  %-13s D roh %s · y je Fünftel oben/Mitte/unten %s Pp · %s" % (name, pp(d_roh), mittel, " · ".join(teile)))
    vv = lade_mengen(sym, LAB, vorvortag_immer=True)
    z.append("  Zuordnung strenger (alle Einstiege L des Vorvortags), tagesbereinigt: %s" % " · ".join(
        "%s %s (p %.3f)" % (m, pp(r["D"]), r["p"]) for m, r in ((m, test_punkt1(Menge(e), LAB, rng)) for m, e in vv.items())))
    a = pd.read_csv(LAUF_A, sep=";")
    a = a[(a.jahr >= 2024)].copy()
    a["zeit"] = V.B0 + pd.to_timedelta(a.stunde, unit="h")
    a["ein"] = a.zeit + pd.Timedelta(hours=1)
    a = a[a.ein <= pd.Timestamp(V.ENDE) + pd.Timedelta(days=1)]
    ea = bereite(a, sym, LAB)
    MA = Menge(ea)
    ra = test_punkt1(MA, LAB, rng)
    LA = LAB[MA.si, MA.ei]
    z.append("  Gegenrechnung Lauf A (REGEL0 mit Historie ab 2019, 2024-01..2026-08, ungesehen): n %d, %d Symbole · D tb %s (p %.3f) · roh %s"
             % (len(MA.y), len(MA.assets), pp(ra["D"]), ra["p"], pp(d_zeilen(LA[None, :], MA.y)[0])))
    schreibe("messung", z, vorher)
    with open(AUS % "messung" + ".json", "w", encoding="utf-8") as f:
        json.dump({"gesamt": gesamt, "n_traegt": n_tr, "je": {m: {k: v for k, v in r.items()} for m, r in erg.items()}}, f, indent=1, default=float)
    return 0


if __name__ == "__main__":
    if "--vorpruefung" in sys.argv:
        sys.exit(vorpruefung())
    if "--selbsttest" in sys.argv:
        sys.exit(selbsttest())
    if "--messung" in sys.argv:
        sys.exit(messung())
    print(__doc__)
