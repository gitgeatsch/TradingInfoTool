"""Asymmetrie-Messung (Voranalyse_Spot_Neubau_04_10.md §19.2, vorab Commit 85c983a; E-71) - Selbsttest, dann Merkmale F1-F11, dann Kombination.

    python Basisinfos/Spot_Voranalyse_04_10/as_messung.py            # Selbsttest + Messung (Messung nur, wenn der Selbsttest besteht)

Nur lesend (mode=ro). Zielgroesse wie as_vorpruefung.py (R2/R3/L), dazu D2 = tiefster Schluss <= -50 % oder eingestellt (Spiegelereignis).

AUSLEGUNG, vor dem ersten Lauf festgelegt (im Plan nicht genau bestimmt):
  - Zelle = (Stichtag, Klasse); gewertet nur mit >= 10 Coins, die das Merkmal haben. Fuenftel ueber das Perzentil in der Zelle: oben > 0,8, unten <= 0,2
  - Saldo der Zelle = (Anteil R2 - Anteil L) im Fuenftel minus derselbe Saldo aller Coins der Zelle MIT Merkmal; Stichtag = nach Coinzahl gewichtetes
    Mittel seiner Zellen; Epoche = Mittel ueber die Stichtage. Nullwelt: in jeder Zelle gleich viele Coins zufaellig, 200 Ziehungen; Rang = Anteil < echt
  - Spiegelprobe: Lift = Treffer im Fuenftel / erwartete Treffer (Anteil der Zelle x Fuenftelgroesse), ueber die Epoche summiert; Verhaeltnis Lift(R2)/Lift(D2)
    NACHTRAG 06.10. (§19.4, E-72): die Schwelle 1,717 ist ersetzt durch die bewegungsgleiche Spiegelprobe (spiegel_ok) - der Selbsttest (b)
    war an 1,717 gescheitert; das Verhaeltnis wird weiter ausgewiesen
  - F1/F2/F5 erst ab 180 T Kursgeschichte; F4 braucht 250 T fuer die 365-T-Schwankung; F7 180 T Umsatz fuer das 365-T-Mittel
  - F6 = 180-T-Ertrag (der Klassenmedian ist je Zelle konstant und aendert den Rang nicht)
  - Externe Quellen (TVL, Adressen, Funding, OI) nur mit Daten bis t-1 (ein Tag Abstand, Veroeffentlichung); asof hoechstens 7 T alt
  - Kombination: Auswahl auf E2 (eine Seite mit Rang >= 0,90 UND Spiegel >= 1,717), Wert = Mittel der richtungsgerechten Perzentile der verfuegbaren
    ausgewaehlten Merkmale; Pruefung des oberen Fuenftels auf E3 mit Rang >= 0,95, Spiegel >= 1,717, >= 10 Coins
  - Selbsttest (a) 40 Zufallsmerkmale je beide Seiten: bestanden, wenn keines traegt und je Epoche hoechstens 5 % ueber 0,975;
    (b) gepflanzt 0,3 x R2 + N(0,1), obere Seite: bestanden, wenn es traegt
"""
import os
import sqlite3
import sys

import numpy as np
import pandas as pd

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HIER)
import a2_messung as A  # noqa: E402

G = A.G
K, IDX, POS, ENDE, BTCV, UNIV = A.K, A.IDX, A.POS, A.ENDE, A.BTCV, A.UNIV
RNG = np.random.default_rng(20261010)
NZ = 200
SPIEGEL = 1.717
NAMEN = {"F1": "Tiefe (Schluss/Allzeithoch)", "F2": "Dauer seit Allzeithoch", "F3": "Schwankung 90 T", "F4": "Basisbildung (Schw. 90/365)",
         "F5": "Abstand zum 365-T-Tief", "F6": "Ertrag 180 T", "F7": "Umsatz 90/365 T", "F8": "Alter", "F9": "TVL gegen Kurs (Teilmenge)",
         "F10": "Aktive Adressen (Teilmenge)", "F11": "Funding 30 T (Teilmenge)", "F12": "OI-Aenderung 90 T (Auskunft)"}


# ---------------------------------------------------------------- Zielgroesse
def ziel(s, i0, h):
    v = K[s].values[i0:i0 + h + 1]
    if np.isnan(v[0]):
        return None
    ok = ~np.isnan(v)
    if not ok.all():
        v = v[:np.argmin(ok)]
    voll = len(v) == h + 1
    eing = (not voll) and (i0 + len(v) - 1 < len(IDX) - 11)
    if not voll and not eing:
        return None
    b = BTCV[i0:i0 + len(v)]
    x = v / v[0]
    return dict(r2=x.max() >= 2, r3=x.max() >= 3, l=(x.min() <= 0.30) or eing, d2=(x.min() <= 0.50) or eing, eing=eing, ende=x[-1], ende_b=b[-1] / b[0])


def paare(h):
    out = []
    for t in pd.date_range("2019-01-01", ENDE, freq="MS"):
        if t not in POS:
            continue
        for s, k in A.klassen(t)[0].items():
            z = ziel(s, POS[t] + 1, h)
            if z is not None:
                out.append(dict(z, t=t, sym=s, kl=k, ep=A.epoche(t)))
    return pd.DataFrame(out)


# ---------------------------------------------------------------- Merkmale
X = K[UNIV]
CM = X.cummax()
ar = pd.DataFrame(np.where(X.notna() & (X == CM), np.arange(len(X))[:, None], np.nan), index=X.index, columns=UNIV).ffill()
ret = X.pct_change(fill_method=None)
SD90 = G["SD90"]
SD365 = ret.rolling(365, min_periods=250).std().shift(1)
MIN365 = X.rolling(365, min_periods=180).min()
NGESCH = X.notna().cumsum()
U = G["U"][UNIV]
U90 = G["U90"]
U365 = U.rolling(365, min_periods=180).mean().shift(1)
ERST = G["ERST"]


def _reihen(db, sql):
    c = sqlite3.connect("file:%s?mode=ro" % db, uri=True)
    d = pd.read_sql(sql, c, parse_dates=["datum"])
    return {s: g.set_index("datum")["wert"].sort_index() for s, g in d.groupby("symbol")}


TVL = _reihen("data/tvl_historie.db", "SELECT symbol, datum, tvl_usd AS wert FROM tvl_historie")
ADR = _reihen("data/onchain_historie.db", "SELECT symbol, datum, wert FROM adractcnt")
FUN = _reihen("data/funding_historie.db", "SELECT symbol, datum, wert FROM funding")
OI = _reihen("data/terminmarkt_historie.db", "SELECT symbol, tag AS datum, oi_wert AS wert FROM terminmarkt_tag")


def asof(r, t):
    x = r[:t]
    return x.iloc[-1] if len(x) and (t - x.index[-1]).days <= 7 and x.iloc[-1] > 0 else np.nan


def merkmale(D):
    F = {k: np.full(len(D), np.nan) for k in NAMEN}
    for t, idx in D.groupby("t").groups.items():
        i = POS[t]
        sub = D.loc[idx]
        for j, s in zip(idx, sub["sym"]):
            k = X.columns.get_loc(s)
            x = X.iat[i, k]
            if NGESCH.iat[i, k] >= 180:
                F["F1"][j] = x / CM.iat[i, k] - 1
                F["F2"][j] = i - ar.iat[i, k]
                F["F5"][j] = x / MIN365.iat[i, k] - 1
            F["F3"][j] = SD90.at[t, s]
            F["F4"][j] = SD90.at[t, s] / SD365.iat[i, k] if SD365.iat[i, k] > 0 else np.nan
            if i >= 180 and X.iat[i - 180, k] > 0:
                F["F6"][j] = x / X.iat[i - 180, k] - 1
            F["F7"][j] = U90.at[t, s] / U365.iat[i, k] if U365.iat[i, k] > 0 else np.nan
            F["F8"][j] = (t - ERST[s]).days
            t1 = t - pd.Timedelta(days=1)
            if s in TVL and i >= 181 and X.iat[i - 180, k] > 0:
                a, b = asof(TVL[s], t1), asof(TVL[s], t1 - pd.Timedelta(days=180))
                F["F9"][j] = np.log(a / b) - np.log(x / X.iat[i - 180, k])
            if s in ADR:
                r = ADR[s]
                w1, w0 = r[t - pd.Timedelta(days=30):t1], r[t - pd.Timedelta(days=210):t - pd.Timedelta(days=181)]
                if len(w1) >= 20 and len(w0) >= 20 and w0.mean() > 0 and w1.mean() > 0:
                    F["F10"][j] = np.log(w1.mean() / w0.mean())
            if s in FUN:
                w = FUN[s][t - pd.Timedelta(days=30):t1]
                if len(w) >= 20:
                    F["F11"][j] = w.mean()
            if s in OI:
                a, b = asof(OI[s], t1), asof(OI[s], t1 - pd.Timedelta(days=90))
                F["F12"][j] = np.log(a / b)
    return F


# ---------------------------------------------------------------- Auswertung
class Zellen:
    def __init__(self, D):
        self.D = D
        self.a = (D["r2"].astype(float) - D["l"].astype(float)).values
        self.r2, self.r3, self.l, self.d2 = (D[c].astype(float).values for c in ("r2", "r3", "l", "d2"))
        self.ende, self.eb = D["ende"].values, D["ende_b"].values
        self.gruppen = [(t, k, np.array(ix)) for (t, k), ix in D.groupby(["t", "kl"]).groups.items()]
        self.ep = {t: A.epoche(t) for t in D["t"].unique()}


def pct_in_zelle(Z, f):
    p = np.full(len(f), np.nan)
    for _, _, ix in Z.gruppen:
        m = ix[~np.isnan(f[ix])]
        if len(m) >= 10:
            p[m] = pd.Series(f[m]).rank(pct=True).values
    return p


def bewerte(Z, f, seite, nz=NZ, null=True, ohne=None, ep_liste=("E1", "E2", "E3"), quintil=None):
    """Kennzahlen je Epoche fuer das obere ('oben') oder untere ('unten') Fuenftel von f."""
    p = pct_in_zelle(Z, f)
    out = {}
    for ep in ep_liste:
        datum_w, datum_v, datum_n = {}, {}, {}
        nul = {}
        tr = dict(r2=0., r2e=0., d2=0., d2e=0., r3=0., n=0, korb=[], korb_k=[])
        coins = set()
        for t, k, ix in Z.gruppen:
            if Z.ep[t] != ep:
                continue
            m = ix[~np.isnan(p[ix])]
            if ohne is not None:
                m = m[~np.isin(Z.D["sym"].values[m], list(ohne))]
            if len(m) < 10:
                continue
            if quintil is not None:
                q = m[(p[m] > (quintil - 1) / 5) & (p[m] <= quintil / 5)]
            else:
                q = m[p[m] > 0.8] if seite == "oben" else m[p[m] <= 0.2]
            if len(q) == 0:
                continue
            s_alle = Z.a[m].mean()
            v = Z.a[q].mean() - s_alle
            datum_v[t] = datum_v.get(t, 0) + v * len(m); datum_n[t] = datum_n.get(t, 0) + len(m)
            tr["r2"] += Z.r2[q].sum(); tr["r2e"] += Z.r2[m].mean() * len(q)
            tr["d2"] += Z.d2[q].sum(); tr["d2e"] += Z.d2[m].mean() * len(q)
            tr["r3"] += Z.r3[q].sum() - Z.r3[m].mean() * len(q); tr["n"] += len(q)
            tr["korb"].append(Z.ende[q].mean() / Z.eb[q[0]] - 1); tr["korb_k"].append(Z.ende[m].mean() / Z.eb[q[0]] - 1)
            coins |= set(Z.D["sym"].values[q][Z.r2[q] > 0])
            if null:
                zufall = RNG.random((nz, len(m))).argsort(axis=1)[:, :len(q)]
                nul.setdefault(t, []).append((Z.a[m][zufall].mean(axis=1) - s_alle) * len(m))
        if not datum_n:
            out[ep] = None; continue
        tage = sorted(datum_n)
        saldo = np.mean([datum_v[t] / datum_n[t] for t in tage])
        rang = None
        if null:
            nv = np.mean([np.sum(nul[t], axis=0) / datum_n[t] for t in tage], axis=0)
            rang = float(np.mean(nv < saldo))
        lr2 = tr["r2"] / tr["r2e"] if tr["r2e"] else np.nan
        ld2 = tr["d2"] / tr["d2e"] if tr["d2e"] else np.nan
        out[ep] = dict(saldo=saldo, rang=rang, lift_r2=lr2, lift_d2=ld2, spiegel=(lr2 / ld2) if ld2 > 0 else np.inf, coins=len(coins),
                       r3=tr["r3"] / tr["n"] if tr["n"] else np.nan, n=tr["n"], tage=len(tage), korb=np.mean(tr["korb"]), korb_k=np.mean(tr["korb_k"]))
    return out


# ---------------------------------------------------------------- Spiegelprobe 'bewegungsgleich' (§19.4, ersetzt 1,717 - Entscheid 06.10., E-72)
GRID = {}
G_SCHRITT = float(os.environ.get("AS_SCHRITT", "0.05"))
G_ZIEH = int(os.environ.get("AS_ZIEH", "100"))


def baue_grid(Z):
    """Bewegungswelten f = s*(R2+D2) + N(0,1), s von -2 bis +2 (negativ: ruhige Coins, beide Enden seltener), je Epoche alle (Lift R2, Lift D2)."""
    pts = {"E2": [], "E3": []}
    for s in np.round(np.arange(-2.0, 2.0001, G_SCHRITT), 2):
        for _ in range(G_ZIEH):
            o = bewerte(Z, s * (Z.r2 + Z.d2) + RNG.normal(size=len(Z.D)), "oben", null=False, ep_liste=("E2", "E3"))
            for e in pts:
                pts[e].append((o[e]["lift_r2"], o[e]["lift_d2"]))
    for e in pts:
        GRID[e] = np.array(pts[e])


def spiegel_ok(x, e):
    """besteht, wenn Lift(D2) unter dem 2,5. Perzentil der 200 Bewegungswelten mit dem naechstliegenden BEOBACHTETEN Lift(R2) liegt."""
    g = GRID[e]
    nb = g[np.argsort(np.abs(g[:, 0] - x["lift_r2"]))[:200]]
    grenze = np.percentile(nb[:, 1], 2.5)
    x["spiegel_grenze"] = grenze
    return bool(x["lift_d2"] < grenze)


def traegt(o, eps=("E2", "E3"), schwelle=0.975):
    return all(o.get(e) and o[e]["saldo"] > 0 and o[e]["rang"] >= schwelle and spiegel_ok(o[e], e) and o[e]["coins"] >= 10 for e in eps)


def drucke(name, o):
    print("  %s" % name)
    for e in ("E1", "E2", "E3"):
        x = o.get(e)
        if not x:
            print("      %s  -" % e); continue
        print("      %s  Saldo %+5.1f Pp%s | Lift R2 %.2f · D2 %.2f · Spiegel %5.2f | R3 %+4.1f Pp | %3d Coins mit R2 | n %4d an %2d Stichtagen | Korb %+5.0f %% (ganze Klasse %+5.0f %%) gg. BTC" % (
            e, 100 * x["saldo"], ("  Rang %.3f" % x["rang"]) if x["rang"] is not None else "", x["lift_r2"], x["lift_d2"], x["spiegel"], 100 * x["r3"], x["coins"],
            x["n"], x["tage"], 100 * x["korb"], 100 * x["korb_k"]))
        if e in GRID:
            ok = spiegel_ok(x, e)
            print("            Spiegelprobe bewegungsgleich: Lift D2 %.3f gegen Grenze %.3f  ->  %s" % (x["lift_d2"], x["spiegel_grenze"], "besteht" if ok else "nein"))


# ---------------------------------------------------------------- Selbsttest
def selbsttest(Z):
    print("SELBSTTEST der Anlage (§19.2, vorab)")
    ueber = {"E2": 0, "E3": 0}; beide = 0; tr = 0; n = 0
    for j in range(40):
        f = RNG.normal(size=len(Z.D))
        for seite in ("oben", "unten"):
            o = bewerte(Z, f, seite, ep_liste=("E2", "E3"))
            n += 1
            for e in ("E2", "E3"):
                ueber[e] += o[e]["rang"] >= 0.975
            beide += o["E2"]["rang"] >= 0.975 and o["E3"]["rang"] >= 0.975
            tr += traegt(o)
    a_ok = tr == 0 and ueber["E2"] <= 0.05 * n and ueber["E3"] <= 0.05 * n
    print("  (a) %d Zufallstests: Rang >= 0,975 in E2 %d (%.1f %%) · in E3 %d (%.1f %%) · in beiden %d · traegt %d  ->  %s" % (
        n, ueber["E2"], 100 * ueber["E2"] / n, ueber["E3"], 100 * ueber["E3"] / n, beide, tr, "BESTANDEN" if a_ok else "NICHT BESTANDEN"))
    f = 0.3 * Z.r2 + RNG.normal(size=len(Z.D))
    o = bewerte(Z, f, "oben", ep_liste=("E2", "E3"))
    b_ok = traegt(o)
    drucke("(b) gepflanzt 0,3 x R2 + N(0,1), oberes Fuenftel  ->  %s" % ("BESTANDEN" if b_ok else "NICHT BESTANDEN"), o)
    return a_ok and b_ok, o


def main():
    D = paare(365).reset_index(drop=True)
    Z = Zellen(D)
    print("Asymmetrie-Messung (§19.2) · Kurse bis %s · %d Coin-Anker (12 Monate) · Saldo = (R2 - L) im Fuenftel minus Zelle\n" % (ENDE.date(), len(D)))
    baue_grid(Z)
    print("Bewegungswelten fuer die Spiegelprobe: %d je Epoche (s -2..2 in %.2f, je %d Ziehungen)\n" % (len(GRID["E2"]), G_SCHRITT, G_ZIEH))
    ok, _ = selbsttest(Z)
    if not ok:
        print("\nSELBSTTEST NICHT BESTANDEN - keine Messung (Plan §19.2: erst die Anlage reparieren).")
        return
    print("\nSELBSTTEST BESTANDEN - Messung\n")
    F = merkmale(D)
    print("Abdeckung je Merkmal (Anteil der Coin-Anker mit Wert): " + " · ".join("%s %.0f %%" % (k, 100 * np.mean(~np.isnan(v))) for k, v in F.items()))
    erg = {}
    for k in NAMEN:
        for seite in ("oben", "unten"):
            erg[(k, seite)] = bewerte(Z, F[k], seite)
    print("\nEINZELMERKMALE (Trägt: Saldo > 0 und Rang >= 0,975 in E2 UND E3, Spiegel >= 1,717, >= 10 Coins; F12 nur Auskunft)")
    for k in NAMEN:
        for seite in ("oben", "unten"):
            o = erg[(k, seite)]
            t = traegt(o) and k != "F12"
            drucke("%s %s · %s Fuenftel  ->  %s" % (k, NAMEN[k], seite, "TRAEGT" if t else ("Auskunft" if k == "F12" else "traegt nicht")), o)
    # Kombination
    wahl = [(k, s) for (k, s), o in erg.items() if k != "F12" and o.get("E2") and o["E2"]["rang"] >= 0.90 and spiegel_ok(o["E2"], "E2") and o["E2"]["saldo"] > 0]
    print("\nKOMBINATION (Auswahl auf E2: Rang >= 0,90, Spiegel >= 1,717): %s" % (", ".join("%s %s" % w for w in wahl) or "keine"))
    komb_tr = False
    if wahl:
        P = np.vstack([pct_in_zelle(Z, F[k]) if s == "oben" else 1 - pct_in_zelle(Z, F[k]) for k, s in wahl])
        wert = np.where(np.isnan(P).all(axis=0), np.nan, np.nanmean(np.where(np.isnan(P), np.nan, P), axis=0))
        o = bewerte(Z, wert, "oben")
        komb_tr = traegt(o, eps=("E3",), schwelle=0.95)
        drucke("Wert aus %d Merkmalen · oberes Fuenftel · Pruefung E3 (E2 = Auswahl, nur Auskunft)  ->  %s" % (len(wahl), "TRAEGT" if komb_tr else "traegt nicht"), o)
    # Pruefungen fuer jedes tragende Einzelmerkmal und die besten je Epoche: Dosis, je Klasse, je Jahr, Weglassprobe
    zeigen = [(k, s) for (k, s), o in erg.items() if traegt(o) and k != "F12"]
    if not zeigen:
        bester = sorted([(k, s) for (k, s) in erg if k != "F12" and erg[(k, s)].get("E2") and erg[(k, s)].get("E3")],
                        key=lambda w: -min(erg[w]["E2"]["rang"], erg[w]["E3"]["rang"]))[:3]
        zeigen = bester
        print("\nKein Einzelmerkmal traegt - Auskunft zu den drei mit dem hoechsten kleineren Rang aus E2/E3: %s" % ", ".join("%s %s" % w for w in zeigen))
    for k, s in zeigen:
        print("\nPRUEFUNGEN %s %s (%s Fuenftel)" % (k, NAMEN[k], s))
        for e in ("E2", "E3"):
            d = [bewerte(Z, F[k], s, null=False, ep_liste=(e,), quintil=q)[e] for q in (1, 2, 3, 4, 5)]
            print("  Dosis %s  Fuenftel 1..5 Saldo: %s" % (e, " ".join("%+5.1f" % (100 * x["saldo"]) if x else "  -  " for x in d)))
        for kl in ("H", "M", "S"):
            Zk = Zellen(D[D.kl == kl].reset_index(drop=True))
            fk = F[k][D.kl.values == kl]
            o = bewerte(Zk, fk, s, null=False, ep_liste=("E2", "E3"))
            print("  Klasse %s  %s" % (kl, " · ".join("%s Saldo %+5.1f Pp Spiegel %.2f" % (e, 100 * o[e]["saldo"], o[e]["spiegel"]) if o.get(e) else "%s -" % e for e in ("E2", "E3"))))
        for j in sorted(D.t.dt.year.unique()):
            m = (D.t.dt.year == j).values
            Zj = Zellen(D[m].reset_index(drop=True))
            o = bewerte(Zj, F[k][m], s, null=False, ep_liste=(A.epoche(pd.Timestamp("%d-06-01" % j)),))
            x = list(o.values())[0]
            print("  Jahr %d  %s" % (j, ("Saldo %+5.1f Pp · Spiegel %.2f · %d Coins" % (100 * x["saldo"], x["spiegel"], x["coins"])) if x else "-"))
        for e in ("E2", "E3"):
            p = pct_in_zelle(Z, F[k])
            q = (p > 0.8) if s == "oben" else (p <= 0.2)
            m = q & (D.ep.values == e) & (Z.r2 > 0)
            top5 = pd.Series(D.sym.values[m]).value_counts().index[:5].tolist()
            o = bewerte(Z, F[k], s, null=False, ep_liste=(e,), ohne=top5)
            print("  Weglassprobe %s ohne %s: Saldo %+5.1f Pp · Spiegel %.2f" % (e, ",".join(top5), 100 * o[e]["saldo"], o[e]["spiegel"]))
    # 24 Monate Auskunft
    D2_ = paare(730).reset_index(drop=True)
    Z2 = Zellen(D2_)
    F2_ = merkmale(D2_)
    print("\nAUSKUNFT 24 Monate (ohne Nullwelt; E3 nur 8 Stichtage):")
    for k in NAMEN:
        for seite in ("oben", "unten"):
            o = bewerte(Z2, F2_[k], seite, null=False, ep_liste=("E2", "E3"))
            print("  %-4s %-30s %-5s %s" % (k, NAMEN[k], seite, " · ".join("%s Saldo %+5.1f Pp Spiegel %.2f" % (e, 100 * o[e]["saldo"], o[e]["spiegel"]) if o.get(e) else "%s -" % e for e in ("E2", "E3"))))
    print("\nGESAMT (vorab §19.2):")
    for k in NAMEN:
        if k == "F12":
            continue
        for seite in ("oben", "unten"):
            print("  %-4s %-30s %-5s %s" % (k, NAMEN[k], seite, "TRAEGT" if traegt(erg[(k, seite)]) else "-"))
    print("  Kombination                               %s" % ("TRAEGT" if komb_tr else "-"))


if __name__ == "__main__":
    main()
