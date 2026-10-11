"""STUFE-1-VORPRUEFUNG U1-U5 (Spot §45.5, vorab Commit ce6b022) - genau wie tc_vorpruefung.py (§35). Nur lesend.

    python Basisinfos/Spot_Voranalyse_04_10/kp46_vorpruefung.py

Merkmale am Tagesschluss d bekannt (externe Werte bis d-1):
  stab90     log(Stablecoins der Kette d-1 / d-91) - log(Kurs d / d-90)         (data/_spot/stablecoins_kette.db)
  gebuehr90  log(30-T-Mittel Gebuehren d-1 / d-91) - log(Kurs d / d-90)         (data/_spot/gebuehren.db, gebuehr)   · Auskunft gebuehr180
  halter90   wie gebuehr90 mit Halter-Einnahmen                                 (gebuehren.db, halter)
  mvrv       CapMVRVCur d-1                                                     (data/_spot/coinmetrics_alt.db)
  korr90     Korrelation der Tagesrenditen mit BTC, 90 T                        · Auskunft beta90
WAHL 2023 (Signale bis 01.12.2023): Lift Lauf / Absturz im oberen und unteren Fuenftel, Richtung; ab 2024 nur Abdeckung und Anzahlen.
Querschnitt >= 30; erreicht ein Merkmal das an < 50 % der Tage 2023, zusaetzlich mit >= 15 ('kleiner Querschnitt').
Kandidat: Richtung >= 1,2 auf einer Seite und >= 300 Coin-Tage im Fuenftel (Auswahl, kein Nachweis).
"""
import os
import sqlite3
import sys

import numpy as np
import pandas as pd

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HIER)
import tc_vorpruefung as T  # noqa: E402  (setzt das Arbeitsverzeichnis)

K, IDX, B = T.K, T.IDX, T.B
LOGK = np.log(K.where(K > 0))


def ro(p):
    return sqlite3.connect("file:%s?mode=ro" % p, uri=True)


def breit(df, wert="wert", datum="datum"):
    df[datum] = pd.to_datetime(df[datum])
    return df.pivot_table(index=datum, columns="symbol", values=wert, aggfunc="sum").reindex(IDX).reindex(columns=K.columns)


def wachstum_gegen_kurs(X, tage, glatt=None):
    if glatt:
        X = X.rolling(glatt, min_periods=int(glatt * 2 / 3)).mean()
    X = X.where(X > 0)
    return np.log(X.shift(1) / X.shift(1 + tage)) - (LOGK - LOGK.shift(tage))


def merkmale():
    st = breit(pd.read_sql("SELECT symbol, datum, usd AS wert FROM bestand", ro("data/_spot/stablecoins_kette.db")))
    gb = breit(pd.read_sql("SELECT symbol, datum, usd AS wert FROM gebuehr", ro("data/_spot/gebuehren.db")))
    ha = breit(pd.read_sql("SELECT symbol, datum, usd AS wert FROM halter", ro("data/_spot/gebuehren.db")))
    mv = breit(pd.read_sql("SELECT symbol, datum, wert FROM mvrv", ro("data/_spot/coinmetrics_alt.db")))
    r = LOGK.diff()
    rb = np.log(B).diff()
    F = {"stab90": wachstum_gegen_kurs(st, 90),
         "gebuehr90": wachstum_gegen_kurs(gb, 90, glatt=30),
         "halter90": wachstum_gegen_kurs(ha, 90, glatt=30),
         "mvrv": mv.shift(1),
         "korr90": r.rolling(90, min_periods=60).corr(rb),
         "gebuehr180": wachstum_gegen_kurs(gb, 180, glatt=30),
         "beta90": r.rolling(90, min_periods=60).cov(rb).div(rb.rolling(90, min_periods=60).var(), axis=0)}
    return {k: v.replace([np.inf, -np.inf], np.nan) for k, v in F.items()}


def auswerten(X, up, down, end, m, kl, w, mindest):
    Xw = X[w].where(m[w])
    pct = Xw.rank(axis=1, pct=True)
    pct.loc[Xw.notna().sum(axis=1) < mindest] = np.nan
    basis = pct.notna()
    uw, dw, ew = up[w], down[w], end[w]
    p_up, p_dn, e_all = uw[basis].stack().mean(), dw[basis].stack().mean(), ew[basis].stack().mean()
    out = {}
    for seite, sel in (("oben", pct >= 0.8), ("unten", pct <= 0.2)):
        lu, ld = uw[sel].stack().mean() / p_up, dw[sel].stack().mean() / p_dn
        jk = {}
        for k in "HMS":
            selk, bk = sel & (kl[w] == k), basis & (kl[w] == k)
            if selk.values.sum() >= 50:
                jk[k] = (uw[selk].stack().mean() / uw[bk].stack().mean()) / (dw[selk].stack().mean() / dw[bk].stack().mean())
        out[seite] = dict(lift_lauf=lu, lift_absturz=ld, richtung=lu / ld, ende=ew[sel].stack().mean() - e_all, n=int(sel.values.sum()),
                          coins=int(sel.any().sum()), je_klasse=jk)
    out["tage"] = int(basis.any(axis=1).sum())
    return out


def main():
    rel = K.div(B, axis=0)
    up, down, end, fertig = T.ziele(rel)
    m, kl = T.maske()
    m = m & fertig
    w = (IDX >= "2023-01-01") & (IDX <= "2023-12-01")
    u = IDX >= "2024-01-01"
    F = merkmale()
    n_w = int(w.sum())
    print("STUFE-1-VORPRUEFUNG U1-U5 (§45.5) · Kurse bis %s · WAHL 2023 (%d Tage), ab 2024 nur Anzahlen\n" % (T.M.ENDE.date(), n_w))
    zeilen = []
    for name, X in F.items():
        abd_w = X[w].where(m[w]).notna().values.sum() / max(m[w].values.sum(), 1)
        abd_u = X[u].where(m[u]).notna().values.sum() / max(m[u].values.sum(), 1)
        coins_w = int(X[w].where(m[w]).notna().any().sum())
        coins_u = int(X[u].where(m[u]).notna().any().sum())
        tage30 = int((X[w].where(m[w]).notna().sum(axis=1) >= 30).sum())
        laeufe = [(30, "")]
        if tage30 < n_w / 2:
            laeufe.append((15, " (kleiner Querschnitt)"))
        for mindest, zus in laeufe:
            o = auswerten(X, up, down, end, m, kl, w, mindest)
            print("%-11s Abdeckung 2023 %4.1f %% (%d Coins) / ab 2024 %4.1f %% (%d Coins) · Tage mit >= %d Coins: %d%s" % (
                name, 100 * abd_w, coins_w, 100 * abd_u, coins_u, mindest, o["tage"], zus))
            for seite in ("oben", "unten"):
                x = o[seite]
                kand = x["richtung"] >= 1.2 and x["n"] >= 300
                print("   %-5s Lift Lauf %.2f · Lift Absturz %.2f · RICHTUNG %.2f · Ende 30 T %+.1f Pp gg. alle · %d Coin-Tage, %d Coins · je Klasse %s%s" % (
                    seite, x["lift_lauf"], x["lift_absturz"], x["richtung"], 100 * x["ende"], x["n"], x["coins"],
                    " ".join("%s %.2f" % kv for kv in x["je_klasse"].items()) or "-", "   <- KANDIDAT" if kand else ""))
                zeilen.append(dict(merkmal=name, mindest=mindest, seite=seite, richtung=x["richtung"], lift_lauf=x["lift_lauf"],
                                   lift_absturz=x["lift_absturz"], ende=x["ende"], n=x["n"], coins=x["coins"], kandidat=kand,
                                   haupt=name in ("stab90", "gebuehr90", "halter90", "mvrv", "korr90")))
        print()
    D = pd.DataFrame(zeilen)
    D.to_csv(os.path.join("data", "_spot", "kp46_vorpruefung.csv"), sep=";", index=False)
    h = D[D.haupt & (D.mindest == 30)]
    print("=> Kandidaten (Haupt, Querschnitt 30): %s" % (", ".join("%s %s %.2f" % (r.merkmal, r.seite, r.richtung) for r in h[h.kandidat].itertuples()) or "keine"))
    hk = D[D.haupt & (D.mindest == 15) & D.kandidat]
    if len(hk):
        print("   bei kleinem Querschnitt (15): %s" % ", ".join("%s %s %.2f" % (r.merkmal, r.seite, r.richtung) for r in hk.itertuples()))
    print("   Vergleich §35: 84 Felder, Median der Richtung 0,91, oberes Zehntel ab 1,18 · 10 Haupt-Felder hier (5 Merkmale x 2 Seiten)")


if __name__ == "__main__":
    main()
