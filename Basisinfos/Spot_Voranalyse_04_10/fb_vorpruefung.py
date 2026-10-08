"""VORPRUEFUNG Teil B - Fuehrung und Ausstieg je Bestand, Rolle L (Spot §31.1, Stufe 1) - nur lesend, keine Aufrufe.

    python Basisinfos/Spot_Voranalyse_04_10/fb_vorpruefung.py

Nutzer 08.10.: *"den Einstandspreis oder neue ATH werden nur ganz wenige Assets erreichen, hier benoetigen wir ein anderes Kriterium"*.
Frage der Vorpruefung: WIE OFT wird welches Ausstiegskriterium binnen 365 T ab einem Starttag ueberhaupt erreicht, und wann?

Grundgesamtheit wie die Watchlist (mk_messung.klassen_mw, Umlauf Stufe 3, eingestellte Coins eingeschlossen, ohne BTC/ETH/SOL);
monatliche Starttage mit abgeschlossenem 365-T-Fenster. 'L-Kandidat' = oberstes Fuenftel der Watchlist am Starttag (Fortbestand).
Der Starttag ist KEIN Kauf - er ist der Tag, an dem die Fuehrung beginnt (Altbestand, §30.9).

  Bezug (Nutzeraussage):  ATH  = Allzeithoch bis zum Starttag wieder erreicht
                          E12 / E6 = Kurs von vor 12 / 6 Monaten wieder erreicht (Stellvertreter fuer einen Einstand) - NUR wenn die Position am Start im Minus liegt
  Kandidaten (neu):       Z1 Vielfaches ab Start x1,5 / x2 / x3
                          Z2 Rueckeroberung: Start + q x (ATH - Start), q = 25 % / 50 %
                          Z3 Vorsprung gegen BTC ab Start +50 % / +100 %
                          Z4 Anstieg >= k Schwankungseinheiten, Ziel = Start x exp(k x sigma90 x sqrt(90)), k = 1 / 2 / 3

WAHL-EPOCHE 2023: alle Kriterien mit Anteil erreicht und Tagen bis dahin.
AB 2024 (Urteil): NUR die Bezuege ATH/E12/E6 (Pruefung der Nutzeraussage) - KEINE Kandidaten-Kennzahl, damit die Wahl unberuehrt bleibt.
"""
import os
import sys

import numpy as np
import pandas as pd

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HIER)
os.chdir(os.path.dirname(os.path.dirname(HIER)))
import as_messung as M      # noqa: E402
import mk_messung as MK     # noqa: E402
import wl_messung as W      # noqa: E402

K, IDX, POS, BTCV = M.K, M.IDX, M.POS, M.BTCV
H = 365
BEZUG = ["ATH", "E12", "E6"]
KAND = ["Z1 x1,5", "Z1 x2", "Z1 x3", "Z2 25 %", "Z2 50 %", "Z3 +50 %", "Z3 +100 %", "Z4 1 s", "Z4 2 s", "Z4 3 s"]


def ziele(s, i):
    v = K[s].values
    p0 = v[i]
    ath = np.nanmax(v[:i + 1])
    lr = np.diff(np.log(v[i - 90:i + 1]))
    sig = np.nanstd(lr) * np.sqrt(90) if np.isfinite(lr).sum() >= 60 else np.nan
    return {"ATH": ath, "E12": v[i - 365] if i >= 365 else np.nan, "E6": v[i - 182] if i >= 182 else np.nan,
            "Z1 x1,5": 1.5 * p0, "Z1 x2": 2 * p0, "Z1 x3": 3 * p0,
            "Z2 25 %": p0 + 0.25 * (ath - p0), "Z2 50 %": p0 + 0.5 * (ath - p0),
            "Z4 1 s": p0 * np.exp(sig), "Z4 2 s": p0 * np.exp(2 * sig), "Z4 3 s": p0 * np.exp(3 * sig)}, p0


def main():
    D = MK.paare_mw(H).reset_index(drop=True)
    Z = M.Zellen(D)
    D["fuenftel"] = M.pct_in_zelle(Z, W.wert(Z, M.merkmale(D))) > 0.8
    D = D[(D.t >= "2023-01-01") & (D.sym != "BTC")]
    zeilen = []
    for r in D.itertuples():
        i = POS[r.t]
        zl, p0 = ziele(r.sym, i)
        v = K[r.sym].values[i + 1:i + 1 + H]
        b = BTCV[i + 1:i + 1 + H] / BTCV[i]
        ok = ~np.isnan(v)
        v, b = (v[:np.argmin(ok)], b[:np.argmin(ok)]) if not ok.all() else (v, b)
        rel = (v / p0) / b
        z = dict(t=r.t, sym=r.sym, kl=r.kl, fuenftel=r.fuenftel, unter_ath=1 - p0 / zl["ATH"], jahr=r.t.year)
        for k, ziel in zl.items():
            # KORREKTUR 08.10. vor der Auswertung: ein Einstand-Stellvertreter UNTER dem Start ist kein Ziel (am Tag 1 'erreicht')
            # -> E12/E6 nur fuer Positionen, die am Start IM MINUS liegen
            if k in ("E12", "E6") and not (np.isfinite(ziel) and ziel > p0):
                z[k] = np.nan
                continue
            if np.isfinite(ziel) and ziel > 0:
                hit = np.where(v >= ziel)[0]
                z[k] = len(hit) > 0
                z[k + "_t"] = hit[0] + 1 if len(hit) else np.nan
            else:
                z[k] = np.nan
        for k, q in (("Z3 +50 %", 1.5), ("Z3 +100 %", 2.0)):
            hit = np.where(rel >= q)[0]
            z[k] = len(hit) > 0
            z[k + "_t"] = hit[0] + 1 if len(hit) else np.nan
        zeilen.append(z)
    R = pd.DataFrame(zeilen)
    print("VORPRUEFUNG Teil B Rolle L (Spot §31.1) · Kurse bis %s · Starttage %s bis %s · Coin-Starttage %d (L-Kandidaten im Fuenftel %d)\n" % (
        M.ENDE.date(), R.t.min().date(), R.t.max().date(), len(R), int(R.fuenftel.sum())))

    print("A) NUTZERAUSSAGE - Einstand / Allzeithoch binnen 365 T wieder erreicht (Anteil der Coin-Starttage):")
    for nm, g in (("2023 (Wahl)", R[R.jahr == 2023]), ("ab 2024 (Urteil)", R[R.jahr >= 2024])):
        for sub, gg in (("alle", g), ("L-Kandidaten", g[g.fuenftel])):
            print("  %-17s %-13s n %5d · ATH %4.1f %% · Einstand vor 12 M %4.1f %% (im Minus %2.0f %%) · vor 6 M %4.1f %% (im Minus %2.0f %%) · Abstand zum ATH am Start Median %3.0f %%" % (
                nm, sub, len(gg), 100 * gg.ATH.mean(), 100 * gg.E12.mean(), 100 * gg.E12.notna().mean(), 100 * gg.E6.mean(), 100 * gg.E6.notna().mean(),
                100 * gg.unter_ath.median()))

    print("\nB) KANDIDATEN - nur WAHL-EPOCHE 2023 (Anteil erreicht · Tage bis dahin Median), alle / L-Kandidaten / je Klasse H M S:")
    g = R[R.jahr == 2023]
    for k in KAND:
        x = g[g[k].notna()]
        teile = ["%4.1f %% · %3s T" % (100 * x[k].mean(), "%d" % x[k + "_t"].median() if x[k].any() else "-")]
        xf = x[x.fuenftel]
        teile.append("%4.1f %%" % (100 * xf[k].mean()))
        teile += ["%s %4.1f %%" % (kl, 100 * x[x.kl == kl][k].mean()) for kl in "HMS"]
        print("  %-10s %s" % (k, " | ".join(teile)))
    print("\nC) FALLZAHL ab 2024 (nur Anzahlen, keine Kennzahl): Coin-Starttage %d an %d Starttagen · L-Kandidaten %d · je Klasse %s" % (
        int((R.jahr >= 2024).sum()), R[R.jahr >= 2024].t.nunique(), int(R[(R.jahr >= 2024)].fuenftel.sum()),
        " ".join("%s %d" % (k, int(((R.jahr >= 2024) & (R.kl == k)).sum())) for k in "HMS")))
    R.to_csv(os.path.join("data", "_spot", "fb_vorpruefung_anker.csv"), sep=";", index=False)


if __name__ == "__main__":
    main()
