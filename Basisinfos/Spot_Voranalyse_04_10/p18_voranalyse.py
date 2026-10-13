"""P18 VORANALYSE B4 Abbau-Reihenfolge (Spot §48, 13.10.2026) - kann der NB das untere Fuenftel so rechnen, wie es gemessen wurde? Nur lesend.

    python Basisinfos/Spot_Voranalyse_04_10/p18_voranalyse.py <Prod-Sicherung tradinginfotool.db>

Die Betriebsrechnung ist hier EIGENSTAENDIG nachgebaut (Klasse = Haus-Code fuer den spaeteren Betrieb), NICHT ueber mk_messung - so ist sie
zugleich Gegenprobe der Messung:

  Teil 0  dieselbe Regel: der Nachbau auf der Messbasis gibt an allen E3-Stichtagen der Vormessung (§43) dieselben Fuenftel wie
          b4_vormessung.csv - (a) streng auf denselben Coins: bitgleich; (b) frei (alle Coins mit Kurs am Stichtag, wie der Betrieb
          sie kennt - die Messung brauchte zusaetzlich den Kurs am Folgetag)
  Teil 1  D3 Stammdatei: Merkmale F1/F2/F8 aus Stammsatz (Hoch, Datum des Hochs, erster Kurs, Kerzenzahl bis t-500) + 500-T-Fenster
          (so liegt es am NB: Betriebskopie 500 T) gleich den Merkmalen aus der vollen Geschichte - an jedem Coin, 6 Stichtage
  Teil 2  Grundgesamtheit am NB (§42.1): Binance-Spot + Produktionsreihen der GEHALTENEN Coins ausserhalb (>= 400 Kerzen) statt der 10
          festen Uebernahmen; Wirkung auf die Fuenftel (Muster messe_grundgesamtheit), 2026-08-01 und 2026-09-01
  Teil 2b Umlauf am NB: nur CoinGecko (umlaufmenge_cg.db) - CoinMetrics und das Strukturprofil liegen nur am Desktop; Wirkung auf Klasse
          und Fuenftel
  Teil 3  Erstliste: die gehaltenen L-Coins am letzten Stichtag der Messbasis, je Coin Fuenftel oder Grund
"""
import os
import sqlite3
import sys

import numpy as np
import pandas as pd

PROD = os.path.abspath(sys.argv[1])            # vor dem Import: a2_messung setzt sys.argv neu
HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HIER)
os.chdir(os.path.dirname(os.path.dirname(HIER)))
import d4_wirkung as D4  # noqa: E402

MK, M = D4.MK, D4.M
G = M.A.G
UEBERNOMMEN = ["AIOZ", "AKT", "BRETT", "CAT", "GRIFFAIN", "HYPE", "KAS", "MORPHO", "PLUME", "SUPRA"]
KERN = {"BTC", "ETH", "SOL"}


# ══ der Nachbau (spaeter agent/spot_abbau.py) ═══════════════════════════════════════════════════════════════════════════
class B4:
    """Fuenftel des Watchlist-Werts ohne F9 (F1 Tiefe unten, F2 Dauer seit Hoch oben, F8 Alter oben) je Zelle Stichtag x Marktwert-Klasse."""

    def __init__(self, K, U, ausschluss, umlauf, stamm=None):
        univ = [s for s in K.columns if s not in ausschluss]
        self.X = K[univ]
        self.U90 = U.reindex(columns=univ).rolling(90, min_periods=30).mean().shift(1)
        self.ERST = self.X.apply(lambda x: x.first_valid_index())
        self.umlauf = umlauf
        self.stamm = stamm                       # None = volle Geschichte; sonst {Symbol: (hoch, datum_hoch, erst, n)} bis Schnitt + Fenster
        self.pos = {t: i for i, t in enumerate(self.X.index)}
        self._r = {}

    def _rang_umsatz(self, m):
        if m not in self._r:
            da = self.X.columns[self.X.loc[m].notna().values] if m in self.pos else []
            self._r[m] = self.U90.loc[m, da].dropna().rank(ascending=False) if m in self.pos else pd.Series(dtype=float)
        return self._r[m]

    def klassen_umsatz(self, m):
        r, r1, r2 = self._rang_umsatz(m), self._rang_umsatz(m - pd.DateOffset(months=1)), self._rang_umsatz(m - pd.DateOffset(months=2))
        out = {}
        for s, x in r.items():
            if x <= 30 and r1.get(s, 999) <= 30 and r2.get(s, 999) <= 30 and (m - self.ERST[s]).days >= 730:
                out[s] = "H"
            else:
                out[s] = "M" if x <= 100 else "S"
        return out

    def _rang_mw(self, m):
        kl = self.klassen_umsatz(m)
        mw = {s: self.umlauf(s, m) * self.X.at[m, s] for s in kl}
        mw = {s: v for s, v in mw.items() if v == v and v > 0}
        return kl, pd.Series(mw, dtype=float).rank(ascending=False)

    def klassen(self, m):
        kl, r = self._rang_mw(m)
        r1 = self._rang_mw(m - pd.DateOffset(months=1))[1] if (m - pd.DateOffset(months=1)) in self.pos else pd.Series(dtype=float)
        r2 = self._rang_mw(m - pd.DateOffset(months=2))[1] if (m - pd.DateOffset(months=2)) in self.pos else pd.Series(dtype=float)
        out = {}
        for s, k_ums in kl.items():
            if s not in r.index:
                out[s] = k_ums                       # Ersatzklasse ohne Umlauf
            elif r[s] <= 30 and r1.get(s, 999) <= 30 and r2.get(s, 999) <= 30 and (m - self.ERST[s]).days >= 730:
                out[s] = "H"
            else:
                out[s] = "M" if r[s] <= 100 else "S"
        return out

    def merkmale(self, m, s):
        i = self.pos[m]
        x = self.X[s].values[: i + 1]
        if self.stamm is None:
            ok = ~np.isnan(x)
            n = int(ok.sum())
            hoch = np.nanmax(x)
            idx = np.where(ok & (x == np.fmax.accumulate(np.where(ok, x, -np.inf))))[0]
            tage = i - idx[-1]
            erst = self.ERST[s]
        else:
            hoch0, i_hoch0, erst, n0, schnitt = self.stamm[s]
            w = x[schnitt + 1:]
            okw = ~np.isnan(w)
            n = n0 + int(okw.sum())
            cm = np.fmax.accumulate(np.r_[hoch0 if hoch0 == hoch0 else -np.inf, np.where(okw, w, -np.inf)])[1:]
            gl = np.where(okw & (w == cm))[0]
            hoch = cm[-1]
            tage = i - (schnitt + 1 + gl[-1]) if len(gl) else i - i_hoch0
        if np.isnan(x[-1]):
            return np.nan, np.nan, np.nan
        f1 = x[-1] / hoch - 1 if n >= 180 else np.nan
        f2 = float(tage) if n >= 180 else np.nan
        return f1, f2, float((m - erst).days)

    def fuenftel(self, m, nur=None):
        """-> DataFrame sym, kl, F1, F2, F8, wert, p, q (q = Fuenftel 1..5; 1 = unten)."""
        kl = self.klassen(m)
        if nur is not None:
            kl = {s: k for s, k in kl.items() if s in nur}
        z = pd.DataFrame([(s, k) + self.merkmale(m, s) for s, k in kl.items()], columns=["sym", "kl", "F1", "F2", "F8"])
        z["wert"] = np.nan
        z["p"] = np.nan
        for _, g in z.groupby("kl"):
            P = []
            for f, seite in (("F1", "unten"), ("F2", "oben"), ("F8", "oben")):
                v = g[f]
                pc = pd.Series(np.nan, index=g.index)
                if v.notna().sum() >= 10:
                    pc[v.notna()] = v[v.notna()].rank(pct=True)
                P.append(1 - pc if seite == "unten" else pc)
            P = pd.concat(P, axis=1)
            with np.errstate(all="ignore"):
                w = P.mean(axis=1, skipna=True)
            z.loc[g.index, "wert"] = w
            ok = w.notna()
            if ok.sum() >= 10:
                z.loc[g.index[ok.values], "p"] = w[ok].rank(pct=True).values
        z["q"] = np.where(z.p.isna(), np.nan, np.clip(np.ceil(z.p * 5), 1, 5))
        return z


def stamm_bis(X, schnitt_pos):
    """D3: Stammsatz je Coin aus der Geschichte bis einschliesslich Position schnitt_pos."""
    out = {}
    for s in X.columns:
        x = X[s].values[: schnitt_pos + 1]
        ok = ~np.isnan(x)
        if not ok.any():
            out[s] = (np.nan, -1, X[s].first_valid_index(), 0, schnitt_pos)
            continue
        cm = np.fmax.accumulate(np.where(ok, x, -np.inf))
        gl = np.where(ok & (x == cm))[0]
        out[s] = (cm[-1], gl[-1], X[s].first_valid_index(), int(ok.sum()), schnitt_pos)
    return out


def cgh_nur(s, t):
    """NB-Regel: Umlauf nur aus umlaufmenge_cg.db (CoinGecko, Buendelfaktor schon angewandt), asof <= 7 T."""
    h = MK._asof(MK.CGH.get(s), t)
    return h if h is not None else np.nan


def main():
    K, U = G["K"], G["U"]
    ausschluss = set(G["SONDER"]) | {s for s in K.columns if s not in G["UNIV"]}
    print("P18 VORANALYSE B4 · Messbasis bis %s · Universum %d Coins (ohne Stablecoins/Sonder/Kern)\n" % (K.index.max().date(), len(G["UNIV"])))

    # ---- Teil 0
    ref = pd.read_csv(os.path.join("data", "_spot", "b4_vormessung.csv"), sep=";", parse_dates=["t"])
    ref = ref[ref.ep == "E3"]
    R = B4(K, U, ausschluss, MK.umlauf)
    st_gl = st_n = fr_gl = fr_n = nur_b = 0
    for t, g in ref.groupby("t"):
        q_ref = dict(zip(g.sym, D4.fuenftel(g.p9.values)))
        z = R.fuenftel(t, nur=set(g.sym))
        qa = dict(zip(z.sym, z.q))
        for s, q in q_ref.items():
            if q == q:
                st_n += 1
                st_gl += qa.get(s) == q
        zf = R.fuenftel(t)
        qf = dict(zip(zf.sym, zf.q))
        for s, q in q_ref.items():
            if q == q and qf.get(s) == qf.get(s):
                fr_n += 1
                fr_gl += qf.get(s) == q
        nur_b += len(set(zf.sym) - set(g.sym))
    print("TEIL 0 dieselbe Regel (E3, %d Stichtage der Vormessung):" % ref.t.nunique())
    print("   (a) streng, dieselben Coins wie die Messung: %d von %d Anker mit gleichem Fuenftel (%s)" % (st_gl, st_n, "BITGLEICH" if st_gl == st_n else "ABWEICHUNG"))
    print("   (b) frei, alle Coins mit Kurs am Stichtag: %d von %d gleich (%.2f %%) · %d Anker nur im Betrieb (ohne Kurs am Folgetag)\n" % (
        fr_gl, fr_n, 100 * fr_gl / max(fr_n, 1), nur_b))

    # ---- Teil 1 D3
    X = R.X
    st_tage = [pd.Timestamp(x) for x in ("2025-04-01", "2025-09-01", "2026-01-01", "2026-05-01", "2026-08-01", "2026-09-01")]
    ab = n_v = 0
    for t in st_tage:
        sp = R.pos[t] - 500
        RS = B4(K, U, ausschluss, MK.umlauf, stamm=stamm_bis(X, sp))
        for s in R.klassen(t):
            a, b = R.merkmale(t, s), RS.merkmale(t, s)
            n_v += 1
            ab += not all((u == v) or (u != u and v != v) for u, v in zip(a, b))
    print("TEIL 1 D3 Stammsatz (bis t-500) + 500-T-Fenster gegen volle Geschichte: %d Coin-Stichtage, %d mit Abweichung in F1/F2/F8 (%s)\n" % (
        n_v, ab, "GLEICH" if ab == 0 else "ABWEICHUNG"))

    # ---- Bestand und Produktionsreihen
    c = sqlite3.connect("file:%s?mode=ro" % PROD.replace("\\", "/"), uri=True)
    import config as C
    wl = {a.symbol: a for a in C.get_watchlist()}
    zuord = pd.read_csv("Basisinfos/symbol_zuordnung.csv", sep=";")
    spot_name = {r.bitpanda: r.binance for r in zuord.itertuples() if r.markt == "spot"}
    bestand = {}
    for s, q, st in c.execute("SELECT symbol, quantity, staked_quantity FROM holdings"):
        a = wl.get(s)
        if float(q or 0) + float(st or 0) > 0 and a and a.assetklasse == "krypto" and not a.ist_cash_aequivalent and s not in KERN:
            bestand[s] = spot_name.get(s, s)
    live = {s for s in K.columns if K[s].loc["2026-09-01":].notna().any()}
    ausserhalb = sorted(s for s, b in bestand.items() if b not in live)
    prod_k, prod_u = {}, {}
    for s in ausserhalb:
        d = pd.read_sql("SELECT date, close, volume FROM price_history_ohlc WHERE symbol=? AND currency='USD' AND COALESCE(quelle,'') != 'rekonstruiert' "
                        "ORDER BY date", c, params=(s,), parse_dates=["date"])
        d["date"] = d.date.dt.normalize()
        d = d.drop_duplicates("date", keep="last").set_index("date")
        if len(d) >= 400:
            prod_k[s], prod_u[s] = d.close, d.close * d.volume
    print("BESTAND (Prod-Sicherung): %d L-Coins · Binance-Spot (live bis Messbasis-Ende) %d · ausserhalb %d: %s" % (
        len(bestand), len(bestand) - len(ausserhalb), len(ausserhalb), ", ".join(ausserhalb)))
    print("   davon mit Produktionsreihe >= 400 Kerzen (Uebernahmeregel): %s · zu jung/kurz: %s" % (
        ", ".join(sorted(prod_k)), ", ".join(sorted(set(ausserhalb) - set(prod_k)))))
    # Gegenprobe: Uebernahme = Produktionsreihe bis zum Ende der Uebernahme
    for s in sorted(set(prod_k) & set(UEBERNOMMEN)):
        a = K[s].dropna()
        b = prod_k[s].reindex(a.index)
        ua = U[s].reindex(a.index)
        ub = prod_u[s].reindex(a.index)
        print("   Gegenprobe Uebernahme %s: %d Tage gemeinsam, groesste rel. Abweichung Kurs %.2e · Umsatz %.2e" % (
            s, b.notna().sum(), float(np.nanmax(np.abs(b / a - 1))), float(np.nanmax(np.abs(ub / ua - 1)))))

    # ---- Teil 2 Grundgesamtheit NB
    weg = [s for s in UEBERNOMMEN if s not in prod_k]
    K_nb = K.drop(columns=weg).copy()
    U_nb = U.drop(columns=[s for s in weg if s in U.columns]).copy()
    for s in prod_k:
        K_nb[s] = prod_k[s].reindex(K_nb.index)
        U_nb[s] = prod_u[s].reindex(K_nb.index)
    R_nb = B4(K_nb, U_nb, ausschluss - set(prod_k), MK.umlauf)
    R_nb2 = B4(K_nb, U_nb, ausschluss - set(prod_k), cgh_nur)
    print("\nTEIL 2 Grundgesamtheit NB: ohne %s, mit Produktionsreihe %s" % (", ".join(weg), ", ".join(sorted(prod_k))))
    for t in (pd.Timestamp("2026-08-01"), pd.Timestamp("2026-09-01")):
        a, b, b2 = R.fuenftel(t), R_nb.fuenftel(t), R_nb2.fuenftel(t)
        for name, x in (("Teil 2  Universum NB", b), ("Teil 2b + Umlauf nur CoinGecko", b2)):
            m = a.merge(x, on="sym", suffixes=("_m", "_b"))
            m = m[m.q_m.notna() & m.q_b.notna()]
            anders = m[m.q_m != m.q_b]
            kl_anders = (m.kl_m != m.kl_b).sum()
            u_weg = ((m.q_m == 1) & (m.q_b != 1)).sum()
            u_neu = ((m.q_b == 1) & (m.q_m != 1)).sum()
            bes = [s for s in bestand.values() if s in set(m.sym)]
            bes_anders = sorted(anders.sym[anders.sym.isin(bes)])
            print("   %s %-32s gemeinsam %3d · anderes Fuenftel %3d (%.1f %%) · andere Klasse %d · unteres Fuenftel verlassen %d / neu %d · "
                  "Bestand anders: %s" % (t.date(), name, len(m), len(anders), 100 * len(anders) / max(len(m), 1), kl_anders, u_weg, u_neu,
                                          ", ".join("%s %d->%d" % (s, m.set_index("sym").q_m[s], m.set_index("sym").q_b[s]) for s in bes_anders) or "-"))
        ohne_u = [s for s in R_nb2.klassen_umsatz(t) if cgh_nur(s, t) != cgh_nur(s, t)]
        print("   %s Coins ohne CoinGecko-Umlauf am NB (Ersatzklasse): %d von %d" % (t.date(), len(ohne_u), len(R_nb2.klassen_umsatz(t))))

    # ---- Teil 3 Erstliste
    t = pd.Timestamp("2026-09-01")
    z = R_nb2.fuenftel(t).set_index("sym")
    print("\nTEIL 3 ERSTLISTE am %s (NB-Regel: Universum NB, Umlauf nur CoinGecko) - gehaltene L-Coins:" % t.date())
    zeilen = []
    for s, b in sorted(bestand.items()):
        if b in z.index and z.q[b] == z.q[b]:
            zeilen.append((int(z.q[b]), s, "Fuenftel %d (Klasse %s, Perzentil %.2f)" % (z.q[b], z.kl[b], z.p[b])))
        else:
            n = int(K_nb[b].loc[:t].notna().sum()) if b in K_nb.columns else 0
            zeilen.append((9, s, "nicht eingeordnet - %s" % (("zu jung (%d T)" % n) if 0 < n < 400 else
                                                             "keine Reihe im Universum" if n == 0 else "ohne Wert/Klasse")))
    for q, s, text in sorted(zeilen):
        print("   %s %-8s %s" % ("UNTEN" if q == 1 else "     ", s, text))


if __name__ == "__main__":
    main()
