"""Messung §25 (Voranalyse_Spot_Neubau_04_10.md, vorab Commit dc77d55): Marktwert-Klassen, Strukturprofil A-E, Pruefstein QNT.

    python Basisinfos/Spot_Voranalyse_04_10/mk_messung.py

Nur lesend (mode=ro) auf messdaten, onchain_historie, strukturprofil.db, gebuehren.db; laedt die Halter-Einnahmen von DefiLlama (frei) einmalig
in gebuehren.db (Tabelle halter, Messdatei des Spot-Strangs).

AUSLEGUNG, vor dem ersten Lauf festgelegt:
  - Teil 0 (R-R11): §19.6 mit den Umsatz-Klassen ohne Nullwelt nachrechnen; Abweichung > 1e-9 bricht ab
  - Marktwert(t) = Umlauf x Schluss t; Umlauf = CoinMetrics SplyCur zu t (asof, <= 7 T alt), sonst CoinGecko heute; ohne Umlauf -> Ersatzklasse
    (Umsatz-Klasse). Rang nur unter den an t klassierten Coins mit Marktwert. H = Rang <= 30 an t, t-1M, t-2M und >= 730 T Kurs; M = Rang <= 100
    oder <= 30 ohne H; S = uebrige mit Marktwert
  - Teil 2 binaer: Vergleich je Zelle (Stichtag, Marktwert-Klasse) nur unter Coins MIT bekanntem Fakt; Saldo = (R2-L) der Coins mit Fakt minus
    (R2-L) aller Coins der Zelle mit bekanntem Fakt; Zellen mit < 10 bekannten oder ohne beide Gruppen entfallen; Nullwelt: Fakt in der Zelle
    vertauscht (200); 'deutlich' = Saldo > 0, Rang >= 0,975 in E2 UND E3, Spiegelprobe besteht; 'deutlich unguenstig' = Rang <= 0,025 in beiden
  - Gebuehren-Fakt zu t: Summe der Tagesgebuehren [t-365, t-1] >= 1 Mio USD; bekannt nur, wenn die Reihe des Symbols >= 365 T vor t beginnt
  - Halter-Einnahmen zu t: Summe [t-365, t-1] > 0; bekannt wie oben
"""
import json
import os
import sqlite3
import sys
import time

import numpy as np
import pandas as pd
import requests

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HIER)
import as_messung as M  # noqa: E402
import wl_messung as W  # noqa: E402

A, G = M.A, M.G
K, IDX, POS, ENDE = M.K, M.IDX, M.POS, M.ENDE
RNG = np.random.default_rng(20261014)
NZ = 200

PROFIL = pd.read_sql("SELECT * FROM profil", sqlite3.connect("file:data/_spot/strukturprofil.db?mode=ro", uri=True)).set_index("symbol")
UMLAUF_HEUTE = PROFIL.umlauf.dropna().to_dict()
_c = sqlite3.connect("file:data/onchain_historie.db?mode=ro", uri=True)
SPLY = {s: g.set_index("datum")["wert"].sort_index() for s, g in pd.read_sql("SELECT symbol, datum, wert FROM splycur", _c, parse_dates=["datum"]).groupby("symbol")}
_KLASSE = {}


def umlauf(s, t):
    r = SPLY.get(s)
    if r is not None:
        x = r[:t]
        if len(x) and (t - x.index[-1]).days <= 7 and x.iloc[-1] > 0:
            return x.iloc[-1]
    return UMLAUF_HEUTE.get(s, np.nan)


def rang_mw(t):
    kl = A.klassen(t)[0]
    i = POS[t]
    mw = {s: umlauf(s, t) * K[s].values[i] for s in kl}
    mw = {s: v for s, v in mw.items() if v == v and v > 0}
    r = pd.Series(mw).rank(ascending=False)
    return kl, r


def klassen_mw(t):
    if t in _KLASSE:
        return _KLASSE[t]
    kl, r = rang_mw(t)
    r1 = rang_mw(t - pd.DateOffset(months=1))[1] if (t - pd.DateOffset(months=1)) in POS else pd.Series(dtype=float)
    r2 = rang_mw(t - pd.DateOffset(months=2))[1] if (t - pd.DateOffset(months=2)) in POS else pd.Series(dtype=float)
    out, ersatz = {}, 0
    for s, k_ums in kl.items():
        if s not in r.index:
            out[s] = k_ums; ersatz += 1; continue
        x = r[s]
        if x <= 30 and r1.get(s, 999) <= 30 and r2.get(s, 999) <= 30 and (t - G["ERST"][s]).days >= 730:
            out[s] = "H"
        elif x <= 100:
            out[s] = "M"
        else:
            out[s] = "S"
    _KLASSE[t] = (out, ersatz, kl)
    return _KLASSE[t]


def paare_mw(h):
    z = []
    for t in pd.date_range("2019-01-01", ENDE, freq="MS"):
        if t not in POS or POS[t] + 1 + h > len(IDX) - 1:
            continue
        out, _, _ = klassen_mw(t)
        for s, k in out.items():
            zz = M.ziel(s, POS[t] + 1, h)
            if zz is not None:
                z.append(dict(zz, t=t, sym=s, kl=k, ep=A.epoche(t)))
    return pd.DataFrame(z)


# ---------------------------------------------------------------- Teil 2 Fakten
def halter_laden():
    c = sqlite3.connect("data/_spot/gebuehren.db")
    if c.execute("SELECT name FROM sqlite_master WHERE name='halter'").fetchone():
        return
    quellen = c.execute("SELECT DISTINCT symbol, art, quelle FROM gebuehr").fetchall()
    zeilen = []
    for s, art, key in quellen:
        url = ("https://api.llama.fi/summary/fees/%s?dataType=dailyHoldersRevenue" % key) if art == "protokoll" else \
              ("https://api.llama.fi/overview/fees/%s?excludeTotalDataChartBreakdown=true&dataType=dailyHoldersRevenue" % key)
        try:
            d = requests.get(url, timeout=60).json()
            for ts, v in d.get("totalDataChart") or []:
                zeilen.append((s, pd.Timestamp(int(ts), unit="s").date().isoformat(), float(v)))
        except Exception:                                                    # noqa: BLE001
            pass
        time.sleep(0.3)
    c.execute("CREATE TABLE halter (symbol TEXT, datum TEXT, usd REAL, PRIMARY KEY (symbol, datum))")
    c.executemany("INSERT OR REPLACE INTO halter VALUES (?,?,?)", zeilen)
    c.commit()


def reihen(tab):
    c = sqlite3.connect("file:data/_spot/gebuehren.db?mode=ro", uri=True)
    d = pd.read_sql("SELECT symbol, datum, usd FROM %s" % tab, c, parse_dates=["datum"])
    return {s: g.set_index("datum")["usd"].sort_index() for s, g in d.groupby("symbol")}


def fakten(D, F):
    kat = PROFIL.kategorien.dropna().apply(json.loads).to_dict()
    n = len(D)
    out = {}
    def aus_profil(spalte, fn):
        v = np.full(n, np.nan)
        for j, s in enumerate(D.sym):
            if s in PROFIL.index and PROFIL.at[s, spalte] == PROFIL.at[s, spalte]:
                v[j] = float(fn(PROFIL.at[s, spalte]))
        return v
    out["A1 Hoechstmenge fest"] = aus_profil("fest", lambda x: bool(x))
    out["A2 ausgegeben >= 90 %"] = aus_profil("ausgegeben", lambda x: x >= 0.9)
    out["A3 FDV/Marktwert <= 1,2"] = aus_profil("fdv_mw", lambda x: x <= 1.2)
    geb, hal = reihen("gebuehr"), reihen("halter")
    def zeitfakt(r, fn):
        v = np.full(n, np.nan)
        for j, (s, t) in enumerate(zip(D.sym, D.t)):
            x = r.get(s)
            if x is None or x.index[0] > t - pd.Timedelta(days=365):
                continue
            v[j] = float(fn(x[t - pd.Timedelta(days=365):t - pd.Timedelta(days=1)].sum()))
        return v
    out["B1 Gebuehren >= 1 Mio $/Jahr"] = zeitfakt(geb, lambda x: x >= 1e6)
    out["B2 Halter-Einnahmen > 0"] = zeitfakt(hal, lambda x: x > 0)
    def kategorie(stich):
        v = np.full(n, np.nan)
        for j, s in enumerate(D.sym):
            if s in kat:
                v[j] = float(any(stich in k for k in kat[s]))
        return v
    out["C1 Kategorie RWA"] = kategorie("Real World Assets")
    out["C2 Coinbase 50 Index"] = kategorie("Coinbase 50")
    f1 = F["F1"]
    v = np.full(n, np.nan)
    for (t, k), ix in D.groupby(["t", "kl"]).groups.items():
        ix = np.array(ix); m = ix[~np.isnan(f1[ix])]
        if len(m) >= 10:
            v[m] = (f1[m] > np.median(f1[m])).astype(float)
    out["D1 Widerstand (Rueckgang < Median Klasse)"] = v
    for name, stich in (("E1 Meme", "Meme"), ("E2 Layer 1", "Layer 1"), ("E3 DeFi", "Decentralized Finance"), ("E4 Infrastruktur", "Infrastructure"),
                        ("E5 Gaming", "Gaming"), ("E6 KI", "Artificial Intelligence")):
        out[name] = kategorie(stich)
    return out


def binaer(Z, x):
    res = {}
    for ep in ("E2", "E3"):
        dv, dn, nul = {}, {}, {}
        r2 = r2e = d2 = d2e = 0.0; coins = set(); bek = 0; alle = 0
        for t, k, ix in Z.gruppen:
            if Z.ep[t] != ep:
                continue
            alle += len(ix)
            m = ix[~np.isnan(x[ix])]
            bek += len(m)
            if len(m) < 10:
                continue
            q = m[x[m] == 1]
            if len(q) == 0 or len(q) == len(m):
                continue
            v = Z.a[q].mean() - Z.a[m].mean()
            dv[t] = dv.get(t, 0) + v * len(m); dn[t] = dn.get(t, 0) + len(m)
            r2 += Z.r2[q].sum(); r2e += Z.r2[m].mean() * len(q); d2 += Z.d2[q].sum(); d2e += Z.d2[m].mean() * len(q)
            coins |= set(Z.D.sym.values[q][Z.r2[q] > 0])
            zz = RNG.random((NZ, len(m))).argsort(axis=1)[:, :len(q)]
            nul.setdefault(t, []).append((Z.a[m][zz].mean(axis=1) - Z.a[m].mean()) * len(m))
        if not dn:
            res[ep] = None; continue
        tage = sorted(dn)
        echt = np.mean([dv[t] / dn[t] for t in tage])
        nw = np.mean([np.sum(nul[t], axis=0) / dn[t] for t in tage], axis=0)
        o = dict(saldo=echt, rang=float(np.mean(nw < echt)), lift_r2=r2 / r2e if r2e else np.nan, lift_d2=d2 / d2e if d2e else np.nan,
                 coins=len(coins), tage=len(tage), bekannt=bek / max(alle, 1))
        o["spiegel_ok"] = M.spiegel_ok(o, ep) if o["lift_r2"] == o["lift_r2"] else False
        res[ep] = o
    return res


def main():
    # ---- Teil 0: Reproduktion §19.6
    D0 = M.paare(365).reset_index(drop=True)
    Z0 = M.Zellen(D0)
    F0 = M.merkmale(D0)
    w0 = W.wert(Z0, F0)
    o0 = M.bewerte(Z0, w0, "oben", null=False, ep_liste=("E2", "E3"))
    print("Messung §25 · Kurse bis %s\n\nTEIL 0 (R-R11) Reproduktion §19.6 mit Umsatz-Klassen: E2 Saldo %+.4f · E3 Saldo %+.4f (Soll +0,110 / +0,132)" % (
        ENDE.date(), o0["E2"]["saldo"], o0["E3"]["saldo"]))
    if abs(o0["E2"]["saldo"] - 0.110) > 0.0015 or abs(o0["E3"]["saldo"] - 0.132) > 0.0015:
        print("REPRODUKTION FEHLGESCHLAGEN - Abbruch"); return
    # ---- Teil 1
    D = paare_mw(365).reset_index(drop=True)
    Z = M.Zellen(D)
    M.baue_grid(Z)
    print("\nTEIL 1 Marktwert-Klassen · %d Coin-Anker · Bewegungswelten %d je Epoche" % (len(D), len(M.GRID["E2"])))
    for ep in ("E1", "E2", "E3"):
        x = D[D.ep == ep]
        ers = np.mean([klassen_mw(t)[1] / max(len(klassen_mw(t)[0]), 1) for t in x.t.unique()]) if len(x) else 0
        ums = {(t, s): k for t in x.t.unique() for s, k in klassen_mw(t)[2].items()}
        kreuz = pd.crosstab(pd.Series([ums.get((t, s)) for t, s in zip(x.t, x.sym)], name="Umsatz"), pd.Series(x.kl.values, name="Marktwert"))
        print("  %s Ersatzklasse (ohne Umlauf) %.0f %% der Coins · Kreuztabelle Umsatz (Zeilen) gegen Marktwert (Spalten):\n%s" % (
            ep, 100 * ers, "\n".join("      " + z for z in kreuz.to_string().split("\n"))))
    ok, _ = M.selbsttest(Z)
    if not ok:
        print("SELBSTTEST NICHT BESTANDEN - Teil 1 ohne Urteil")
    F = M.merkmale(D)
    w = W.wert(Z, F)
    o = M.bewerte(Z, w, "oben")
    t1 = ok and M.traegt(o)
    M.drucke("Kombination (unveraendert §19.6) auf Marktwert-Klassen, oberes Fuenftel  ->  %s" % ("TRAEGT" if t1 else "traegt nicht"), o)
    for kl in ("H", "M", "S"):
        m = D.kl.values == kl
        ok_ = M.bewerte(M.Zellen(D[m].reset_index(drop=True)), w[m], "oben", null=False, ep_liste=("E2", "E3"))
        print("  Klasse %s  %s" % (kl, " · ".join("%s Saldo %+5.1f Pp · Lift R2 %.2f / D2 %.2f · Korb %+4.0f %% (Klasse %+4.0f %%)" % (
            e, 100 * ok_[e]["saldo"], ok_[e]["lift_r2"], ok_[e]["lift_d2"], 100 * ok_[e]["korb"], 100 * ok_[e]["korb_k"]) if ok_.get(e) else "%s -" % e for e in ("E2", "E3"))))
    for e in ("E2", "E3"):
        d = [M.bewerte(Z, w, "oben", null=False, ep_liste=(e,), quintil=q)[e] for q in (1, 2, 3, 4, 5)]
        print("  Dosis %s Fuenftel 1..5: %s" % (e, " ".join("%+5.1f" % (100 * x["saldo"]) if x else "  -  " for x in d)))
        p = M.pct_in_zelle(Z, w)
        q = (p > 0.8) & (D.ep.values == e) & (Z.r2 > 0)
        top5 = pd.Series(D.sym.values[q]).value_counts().index[:5].tolist()
        ow = M.bewerte(Z, w, "oben", null=False, ep_liste=(e,), ohne=top5)[e]
        print("  Weglassprobe %s ohne %s: Saldo %+5.1f Pp · Spiegelprobe %s" % (e, ",".join(top5), 100 * ow["saldo"], "besteht" if M.spiegel_ok(ow, e) else "nein"))
    for j in sorted(D.t.dt.year.unique()):
        m = (D.t.dt.year == j).values
        oj = M.bewerte(M.Zellen(D[m].reset_index(drop=True)), w[m], "oben", null=False, ep_liste=(A.epoche(pd.Timestamp("%d-06-01" % j)),))
        x = list(oj.values())[0]
        print("  Jahr %d %s" % (j, ("Saldo %+5.1f Pp · Lift R2 %.2f / D2 %.2f" % (100 * x["saldo"], x["lift_r2"], x["lift_d2"])) if x else "-"))
    # ---- Teil 2
    halter_laden()
    FA = fakten(D, F)
    print("\nTEIL 2 STRUKTURPROFIL (Auskunft; Fakten von heute ausser B1/B2; Vergleich nur unter Coins mit bekanntem Fakt)")
    for name, x in FA.items():
        r = binaer(Z, x)
        teile, urteil = [], "-"
        if r.get("E2") and r.get("E3"):
            if all(r[e]["saldo"] > 0 and r[e]["rang"] >= 0.975 and r[e]["spiegel_ok"] for e in ("E2", "E3")):
                urteil = "DEUTLICH guenstig"
            elif all(r[e]["rang"] <= 0.025 for e in ("E2", "E3")):
                urteil = "DEUTLICH unguenstig"
        for e in ("E2", "E3"):
            o_ = r.get(e)
            teile.append("%s -" % e if not o_ else "%s Saldo %+5.1f Pp Rang %.3f · Lift R2 %.2f / D2 %.2f · Spiegel %s · %d Coins · bekannt %3.0f %%" % (
                e, 100 * o_["saldo"], o_["rang"], o_["lift_r2"], o_["lift_d2"], "ja" if o_["spiegel_ok"] else "nein", o_["coins"], 100 * o_["bekannt"]))
        print("  %-42s %s  ->  %s" % (name, " | ".join(teile), urteil))
    # ---- Teil 3 QNT
    print("\nTEIL 3 PRUEFSTEIN QNT (Anschauung, keine Regel)")
    p = M.pct_in_zelle(Z, w)
    for t in pd.date_range("2022-04-01", "2022-12-01", freq="MS"):
        j = np.where((D.t.values == np.datetime64(t)) & (D.sym.values == "QNT"))[0]
        if not len(j):
            print("  %s QNT nicht in den Paaren" % t.date()); continue
        j = j[0]
        _, r = rang_mw(t)
        f = {k: FA[k][j] for k in FA}
        print("  %s Klasse %s (Marktwert-Rang %s) · Watchlist-Perzentil %.2f%s · Fakten: %s" % (
            t.date(), D.kl[j], int(r["QNT"]) if "QNT" in r.index else "-", p[j], " FUENFTEL" if p[j] > 0.8 else "",
            ", ".join("%s=%s" % (k.split(" ")[0], "ja" if v == 1 else "nein" if v == 0 else "?") for k, v in f.items())))


if __name__ == "__main__":
    main()
