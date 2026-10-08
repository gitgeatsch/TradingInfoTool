"""VORPRUEFUNG Teil C - Ausbruch frueh erkennen (Rolle K, Ebene 3; Spot §35.2, Stufe 1) - nur lesend, keine Aufrufe.

    python Basisinfos/Spot_Voranalyse_04_10/tc_vorpruefung.py

Frage: Welche je Coin verschiedenen Merkmale (Regel 'Beitraege je Asset') zeigen an einem Tag d, dass der Coin in den naechsten 30 T
GEGEN BTC laeuft - und nicht nur, dass er sich BEWEGT (Spiegelprobe)?
  Lauf    = Coin/BTC erreicht binnen 30 T >= x1,3 des Werts an d     (nach Kosten S 6,4 % Hin und Rueck bleibt dann noch etwas)
  Absturz = Coin/BTC faellt binnen 30 T auf <= 1/1,3                  (Spiegel)
  Merkmale (am Tagesschluss d bekannt):
    rs7, rs30        Relativstaerke gegen BTC 7 / 30 T
    umsatz_schub     Umsatz 7 T / 90 T
    hoch90           Schluss / Hoch der 90 T davor (>= 1 = neues 90-T-Hoch)
    schwankung90     Schwankung 90 T (Tagesrenditen)
    tiefe            Schluss / Allzeithoch
    alter            Tage seit erstem Kurs
    kaeufer7         Kaeuferanteil am Umsatz 7 T (richtung_historie, 116 Symbole, ab 2023)
    funding7         Funding 7 T (funding_historie)
    oi30             Open Interest 30 T (terminmarkt_historie, 100 Symbole)
Grundgesamtheit: Watchlist-Klassen des Monats (Umlauf Stufe 3), ohne BTC/ETH/SOL; Querschnitt je Tag (>= 30 Coins mit Merkmal).
WAHL 2023 (d bis 01.12.2023, damit kein Fenster in 2024 reicht): Lift des oberen/unteren Fuenftels fuer Lauf UND Absturz.
AB 2024 (Urteil): NUR Abdeckung und Anzahlen - keine Kennzahl.
"""
import os
import sqlite3
import sys

KOMBI = "--kombi" in sys.argv          # VOR den Imports: ein importiertes Modul veraendert sys.argv

import numpy as np
import pandas as pd

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HIER)
os.chdir(os.path.dirname(os.path.dirname(HIER)))
import as_messung as M      # noqa: E402
import mk_messung as MK     # noqa: E402

K, IDX, POS, BTCV = M.K, M.IDX, M.POS, M.BTCV
U = M.G["U"].reindex(index=K.index, columns=K.columns)
KERN = ("BTC", "ETH", "SOL")
B = pd.Series(BTCV, index=IDX)


def ro(p):
    return sqlite3.connect("file:%s?mode=ro" % p, uri=True)


def merkmale():
    rel = K.div(B, axis=0)
    F = {"rs7": rel / rel.shift(7) - 1, "rs30": rel / rel.shift(30) - 1,
         "umsatz_schub": U.rolling(7, min_periods=5).mean() / U.rolling(90, min_periods=60).mean(),
         "hoch90": K / K.shift(1).rolling(90, min_periods=60).max(),
         "schwankung90": np.log(K).diff().rolling(90, min_periods=60).std(),
         "tiefe": K / K.cummax(),
         "alter": pd.DataFrame({s: (IDX - M.G["ERST"][s]).days for s in K.columns if s in M.G["ERST"]}, index=IDX).reindex(columns=K.columns)}
    fl = pd.read_sql("select symbol, substr(stunde,1,10) tag, sum(kauf_quote) k, sum(quote_volumen) q from fluss group by symbol, tag", ro("data/richtung_historie.db"))
    fl["tag"] = pd.to_datetime(fl.tag)
    kq = fl.pivot_table(index="tag", columns="symbol", values="k").reindex(IDX)
    qq = fl.pivot_table(index="tag", columns="symbol", values="q").reindex(IDX)
    F["kaeufer7"] = (kq.rolling(7, min_periods=5).sum() / qq.rolling(7, min_periods=5).sum()).reindex(columns=K.columns)
    fu = pd.read_sql("select symbol, datum, wert from funding", ro("data/funding_historie.db"), parse_dates=["datum"])
    F["funding7"] = fu.pivot_table(index="datum", columns="symbol", values="wert").reindex(IDX).rolling(7, min_periods=4).mean().reindex(columns=K.columns)
    oi = pd.read_sql("select symbol, tag, oi_wert from terminmarkt_tag", ro("data/terminmarkt_historie.db"), parse_dates=["tag"])
    oi = oi.pivot_table(index="tag", columns="symbol", values="oi_wert").reindex(IDX)
    F["oi30"] = (oi / oi.shift(30) - 1).reindex(columns=K.columns)
    return rel, F


def ziele(rel):
    vor = rel[::-1]
    fmax = vor.rolling(30, min_periods=30).max()[::-1].shift(-1)
    fmin = vor.rolling(30, min_periods=30).min()[::-1].shift(-1)
    return fmax / rel >= 1.3, fmin / rel <= 1 / 1.3, rel.shift(-30) / rel - 1, fmax.notna()


def maske():
    m = pd.DataFrame(False, index=IDX, columns=K.columns)
    kl = pd.DataFrame(None, index=IDX, columns=K.columns, dtype=object)
    for t in pd.date_range("2023-01-01", M.ENDE, freq="MS"):
        if t not in POS:
            continue
        kk = {s: k for s, k in MK.klassen_mw(t)[0].items() if s not in KERN and s in K.columns}
        tage = IDX[(IDX >= t) & (IDX < t + pd.DateOffset(months=1))]
        m.loc[tage, list(kk)] = True
        for s, k in kk.items():
            kl.loc[tage, s] = k
    return m & K.notna(), kl


def main():
    rel, F = merkmale()
    up, down, end, fertig = ziele(rel)
    m, kl = maske()
    m = m & fertig
    w = (IDX >= "2023-01-01") & (IDX <= "2023-12-01")
    u = IDX >= "2024-01-01"
    mw, mu = m[w], m[u]
    print("VORPRUEFUNG Teil C (Rolle K, Ebene 3) · Kurse bis %s\n" % M.ENDE.date())
    print("  WAHL 2023: Coin-Tage %d · Lauf (x1,3 gg. BTC in 30 T) %.1f %% · Absturz %.1f %%" % (
        int(mw.values.sum()), 100 * up[w][mw].stack().mean(), 100 * down[w][mw].stack().mean()))
    print("  AB 2024 (nur Anzahlen): Coin-Tage %d · Lauf-Ereignisse %d · Coins %d\n" % (int(mu.values.sum()), int(up[u][mu].stack().sum()), int(mu.any().sum())))
    print("  Merkmal         Abdeckung 2023 / ab 2024 | OBERES Fuenftel: Lift Lauf · Lift Absturz · Richtung (Lauf/Absturz) · Ende 30 T gg. alle | UNTERES Fuenftel: Lift Lauf · Lift Absturz · Richtung")
    zeilen = []
    for name, X in F.items():
        Xw = X[w].where(mw)
        n_tag = Xw.notna().sum(axis=1)
        pct = Xw.rank(axis=1, pct=True)
        pct.loc[n_tag < 30] = np.nan                               # Tage mit weniger als 30 Coins mit Merkmal entfallen
        top, bot = pct >= 0.8, pct <= 0.2
        basis = pct.notna()
        uw, dw, ew = up[w], down[w], end[w]
        p_up, p_dn, e_all = uw[basis].stack().mean(), dw[basis].stack().mean(), ew[basis].stack().mean()
        res = []
        for sel in (top, bot):
            lu = uw[sel].stack().mean() / p_up
            ld = dw[sel].stack().mean() / p_dn
            res.append((lu, ld, lu / ld, ew[sel].stack().mean() - e_all))
        ab_w = X[w].where(mw).notna().values.sum() / max(mw.values.sum(), 1)
        ab_u = X[u].where(mu).notna().values.sum() / max(mu.values.sum(), 1)
        print("  %-14s  %5.0f %% / %5.0f %%          | %5.2f · %5.2f · %5.2f · %+5.1f Pp                               | %5.2f · %5.2f · %5.2f" % (
            name, 100 * ab_w, 100 * ab_u, res[0][0], res[0][1], res[0][2], 100 * res[0][3], res[1][0], res[1][1], res[1][2]))
        zeilen.append(dict(merkmal=name, abd_w=ab_w, abd_u=ab_u, top_lauf=res[0][0], top_absturz=res[0][1], top_richtung=res[0][2], top_ende=res[0][3],
                           bot_lauf=res[1][0], bot_absturz=res[1][1], bot_richtung=res[1][2], bot_ende=res[1][3]))
    pd.DataFrame(zeilen).to_csv(os.path.join("data", "_spot", "tc_vorpruefung.csv"), sep=";", index=False)
    print("\n  Lesart: 'Richtung' > 1 heisst, das Merkmal zeigt Laeufe haeufiger an als Abstuerze. Lift Lauf UND Lift Absturz beide > 1 bei Richtung ~1 = nur BEWEGUNG (Spiegelprobe).")


if __name__ == "__main__":
    main()


def kombinationen():
    """Stufe 1b (nur WAHL 2023): Paare der 7 voll abgedeckten Merkmale, oberes/unteres Fuenftel je Merkmal, dazu je Klasse.
    Bewertet mit Richtung (Lift Lauf / Lift Absturz) bei mindestens 300 Coin-Tagen; ALLE 84 Felder werden gezaehlt (Mehrfachtesten offen)."""
    import itertools
    rel, F = merkmale()
    up, down, end, fertig = ziele(rel)
    m, kl = maske()
    m = m & fertig
    w = (IDX >= "2023-01-01") & (IDX <= "2023-12-01")
    mw = m[w]
    voll = ["rs7", "rs30", "umsatz_schub", "hoch90", "schwankung90", "tiefe", "alter"]
    P = {}
    for nm in voll:
        Xw = F[nm][w].where(mw)
        n_tag = Xw.notna().sum(axis=1)
        p = Xw.rank(axis=1, pct=True)
        p.loc[n_tag < 30] = np.nan
        P[nm] = p
    uw, dw, ew = up[w], down[w], end[w]
    basis = P["rs7"].notna()
    p_up, p_dn, e_all = uw[basis].stack().mean(), dw[basis].stack().mean(), ew[basis].stack().mean()
    z = []
    for a, b in itertools.combinations(voll, 2):
        for sa, sb in itertools.product(("oben", "unten"), ("oben", "unten")):
            sel = ((P[a] >= 0.8) if sa == "oben" else (P[a] <= 0.2)) & ((P[b] >= 0.8) if sb == "oben" else (P[b] <= 0.2))
            n = int(sel.values.sum())
            if n < 300:
                continue
            lu, ld = uw[sel].stack().mean() / p_up, dw[sel].stack().mean() / p_dn
            z.append((lu / ld, a, sa, b, sb, n, lu, ld, ew[sel].stack().mean() - e_all))
    z.sort(reverse=True)
    print("\n  STUFE 1b - PAARE (nur 2023, %d Felder mit >= 300 Coin-Tagen), die 8 mit der staerksten Richtung:" % len(z))
    for r in z[:8]:
        print("    Richtung %.2f · %s %s UND %s %s · n %5d · Lift Lauf %.2f / Absturz %.2f · Ende 30 T %+.1f Pp gg. alle" % (r[0], r[1], r[2], r[3], r[4], r[5], r[6], r[7], 100 * r[8]))
    print("  Verteilung der Richtung ueber alle Felder: Median %.2f · oberes Zehntel ab %.2f" % (np.median([r[0] for r in z]), np.percentile([r[0] for r in z], 90)))
    print("\n  STUFE 1b - JE KLASSE (oberes Fuenftel, Richtung):")
    for k in "HMS":
        mk = (kl[w] == k) & mw
        teile = []
        for nm in voll:
            sel = (P[nm] >= 0.8) & mk
            bk = basis & mk
            lu = uw[sel].stack().mean() / uw[bk].stack().mean()
            ld = dw[sel].stack().mean() / dw[bk].stack().mean()
            teile.append("%s %.2f" % (nm, lu / ld))
        print("    %s: %s" % (k, " · ".join(teile)))


if __name__ == "__main__" and KOMBI:
    kombinationen()
