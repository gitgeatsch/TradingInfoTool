"""GRID STUFE 1 (W-A, Recherche_Grid_Trading_21_10.md §9, Messplan vorab 2d6618bd): Rueckkehr zur Mitte auf Stufenskala.

    python Basisinfos/Spot_Voranalyse_04_10/grid_stufe1.py

AUSLEGUNG, VOR DEM ERSTEN LAUF FESTGELEGT (im Plan offen):
- "Ausfuehrungen" werden nach NENNWERT gezaehlt: jede Fuellung = 1, die Glattstellung am Monatsende = |Bestandswert|. Der Ueberschuss je
  Ausfuehrung ist damit Ueberschuss je gehandelter Geldeinheit - direkt vergleichbar mit der Gebuehr 0,25 % je Seite.
- Stufe erreicht = Log-Kurs >= Stufe (Verkauf) bzw. <= Stufe (Kauf), Toleranz 1e-12.
- Zufallszahlen fest (Startwert 22102026), je Monat dieselben 200 Umordnungen fuer alle Stufen.
"""
import os
import sqlite3
import sys

import numpy as np
import pandas as pd

os.chdir(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:  # noqa: BLE001
    pass

VON, BIS = "2023-09-01", "2026-08-31"
STUFEN = (0.01, 0.02, 0.03)
AUSKUNFT_STUFE = 0.005
GEBUEHR = 0.0025
ZIEHUNGEN = 200


def stunden(symbol):
    c = sqlite3.connect("file:data/stundenkurse.db?mode=ro", uri=True)
    S = pd.read_sql("SELECT stunde, close FROM stundenkurse WHERE symbol=? AND stunde>=? AND stunde<=? ORDER BY stunde", c,
                    params=(symbol, VON, BIS + " 23:00"))
    c.close()
    S["stunde"] = pd.to_datetime(S.stunde)
    S = S.drop_duplicates("stunde").set_index("stunde").close
    voll = pd.date_range(VON + " 00:00", BIS + " 23:00", freq="h")
    fehlt = int(len(voll.difference(S.index)))
    return S.reindex(voll).ffill().bfill(), fehlt


def gitter(x, g):
    """x: Log-Kurs relativ zum Monatsbeginn, Form (D, n). -> Ergebnis (D,), gehandelter Nennwert (D,)."""
    D, n = x.shape
    lg, q = np.log1p(g), 1.0 + g
    ell = np.zeros(D)
    qty = np.zeros(D)
    cash = np.zeros(D)
    fuell = np.zeros(D)
    teil = 1.0 / (1.0 - 1.0 / q)
    for t in range(1, n):
        xt = x[:, t]
        m = np.floor(xt / lg + 1e-12)
        auf = m >= ell + 1
        if auf.any():
            a, b = ell[auf] + 1, m[auf]
            qty[auf] -= (q ** -a - q ** -(b + 1)) * teil
            cash[auf] += b - a + 1
            fuell[auf] += b - a + 1
            ell[auf] = b
        m2 = np.ceil(xt / lg - 1e-12)
        ab = m2 <= ell - 1
        if ab.any():
            a, b = m2[ab], ell[ab] - 1
            qty[ab] += (q ** -a - q ** -(b + 1)) * teil
            cash[ab] -= b - a + 1
            fuell[ab] += b - a + 1
            ell[ab] = a
    wert_bestand = qty * np.exp(x[:, -1])
    return cash + wert_bestand, fuell + np.abs(wert_bestand)


def messe(symbol, stufen, rng_saat=22102026):
    P, fehlt = stunden(symbol)
    rng = np.random.default_rng(rng_saat)
    monate = sorted(set(P.index.to_period("M")))
    zeilen = {g: [] for g in stufen}
    for mo in monate:
        lp = np.log(P[P.index.to_period("M") == mo].values)
        r = np.diff(lp)
        echt = np.concatenate([[0.0], np.cumsum(r)])[None, :]
        perm = rng.permuted(np.tile(r, (ZIEHUNGEN, 1)), axis=1)
        null = np.concatenate([np.zeros((ZIEHUNGEN, 1)), np.cumsum(perm, axis=1)], axis=1)
        for g in stufen:
            e, ne = gitter(echt, g)
            nn, nne = gitter(null, g)
            zeilen[g].append((str(mo), e[0], ne[0], nn, nne))
    return zeilen, fehlt, len(monate)


def auswerten(symbol, zeilen, g):
    echt = np.array([z[1] for z in zeilen])
    nenn = np.array([z[2] for z in zeilen])
    null = np.stack([z[3] for z in zeilen])          # Monate x Ziehungen
    summe_null = null.sum(axis=0)
    ue = echt.sum() - summe_null.mean()
    je = ue / nenn.sum()
    rang = float(np.mean(summe_null < echt.sum()))
    h = len(zeilen) // 2
    ue1 = echt[:h].sum() - null[:h].sum(axis=0).mean()
    ue2 = echt[h:].sum() - null[h:].sum(axis=0).mean()
    netto = echt.sum() - GEBUEHR * nenn.sum()
    traegt = rang >= 0.95 and je >= GEBUEHR and ue1 > 0 and ue2 > 0
    umg = rang <= 0.05
    print("  %-4s g %.1f %%: Ausfuehrungen %7.0f · echt %+8.2f · Nullwelt %+7.2f [%+.2f; %+.2f] · Rang %.3f · Ueberschuss je Ausf. %+.3f %% · "
          "Haelften %+.2f / %+.2f · netto bei 0,25 %% %+8.2f%s"
          % (symbol, 100 * g, nenn.sum(), echt.sum(), summe_null.mean(), np.percentile(summe_null, 5), np.percentile(summe_null, 95), rang,
             100 * je, ue1, ue2, netto, "  ** TRAEGT **" if traegt else ("  ** UMGEKEHRT (Trend) **" if umg else "")))
    return traegt, umg


def main():
    print("GRID STUFE 1 · %s bis %s · %d Nullwelten je Monat · Schwelle %.2f %% je Ausfuehrung" % (VON, BIS, ZIEHUNGEN, 100 * GEBUEHR))
    print("Einheit: Ergebnis in Nennwert-Einheiten (jede Fuellung handelt 1 Einheit Geld)\n")
    urteil = {}
    for sym in ("BTC", "ETH"):
        z, fehlt, nm = messe(sym, STUFEN + (AUSKUNFT_STUFE,))
        print("%s: %d Monate, fehlende Stunden %d" % (sym, nm, fehlt))
        for g in STUFEN:
            urteil[(sym, g)] = auswerten(sym, z[g], g)
        print("  Auskunft:")
        auswerten(sym, z[AUSKUNFT_STUFE], AUSKUNFT_STUFE)
        print()
    tr = [k for k, v in urteil.items() if v[0]]
    um = [k for k, v in urteil.items() if v[1]]
    print("URTEIL nach §9: tragende Zellen %d von %d %s · umgekehrt (Trend) %d %s" % (len(tr), len(urteil), tr, len(um), um))
    print("FOLGE: %s" % ("STUFE 2 (1-Minuten-Rueckspiel, Download braucht Nutzer-Ja)" if tr else "W-A ENDET - zurueck zu Alternativen / Bestehendes"))
    print("\nAUSKUNFT SOL und LINK (gleiches Fenster):")
    for sym in ("SOL", "LINK"):
        z, fehlt, nm = messe(sym, STUFEN)
        print("%s: %d Monate, fehlende Stunden %d" % (sym, nm, fehlt))
        for g in STUFEN:
            auswerten(sym, z[g], g)


if __name__ == "__main__":
    main()
