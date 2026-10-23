"""P71 MESSPLAN F-1 FASSUNG 1 (Voranalyse_REGEL0_Marktfilter_23_10.md §4, vorab 590bcdac): REGEL0 nur handeln, wenn der Gesamtmarkt nicht
gegen uns steht. Kosten Bitpanda-Hebel 0,48 % je Handel.

    python Basisinfos/Rechenkern_02_10/p71_marktfilter.py

AUSLEGUNG VOR DEM ERSTEN LAUF (im Plan offen):
- Zustand am Einstiegstag = Wert des VORTAGS (Makro-Reihen sind ueber makro_lage.hole_reihe schon um ihren Verzug verschoben).
- Ein fehlender Zustand (NaN, z. B. Perzentil noch nicht gefuellt) gilt als 'an' (kein Filter).
- Nullwelt-Rang wird JE unverzerrter Menge gerechnet; Kriterium (2) verlangt Rang >= 0,99 in ALLEN DREI (strenger als 'gepoolt').
- Strecken-Permutation auf dem Zeitraum 2025-01-01..2026-08-31 (Tagesraster).
"""
import os
import sqlite3
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
WURZEL = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, WURZEL)
os.chdir(WURZEL)
import p64_lc_voranalyse as P  # noqa: E402
from agent import makro_lage as M  # noqa: E402

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:  # noqa: BLE001
    pass
KOSTEN = 0.0048
MENGEN = ("bestand", "unverzerrt_1", "unverzerrt_2", "unverzerrt_3")
UNV = MENGEN[1:]
TAGE = pd.date_range("2024-01-01", "2026-08-31", freq="D")
T2526 = (TAGE >= "2025-01-01")
CACHE = os.path.join("data", "_ra", "p71_filter.csv")


# ── Filter ──────────────────────────────────────────────────────────────────────────────────────────────────────────────
def filter_tabelle():
    if os.path.exists(CACHE):
        return pd.read_csv(CACHE, index_col=0, parse_dates=True)
    import requests
    from dotenv import dotenv_values
    key = dotenv_values(".env").get("FRED_API_KEY")
    roh = M.hole_alle(key, heute=pd.Timestamp("2026-10-23").date())
    idx = pd.date_range("2012-01-01", "2026-10-23", freq="D")
    S = M.scores(roh, idx)
    r = requests.get("https://api.stlouisfed.org/fred/series/observations", timeout=60,
                     params={"series_id": "NASDAQCOM", "api_key": key, "file_type": "json", "observation_start": "2021-01-01"})
    obs = [(o["date"], float(o["value"])) for o in r.json()["observations"] if o["value"] not in (".", "")]
    nq = pd.Series([v for _, v in obs], index=pd.to_datetime([d for d, _ in obs]) + pd.Timedelta(days=1))
    nq_an = (nq > nq.rolling(200).mean()).where(nq.rolling(200).count() == 200)
    c = sqlite3.connect("file:data/_spot/coinmetrics.db?mode=ro", uri=True)
    btc = pd.read_sql("SELECT tag, PriceUSD FROM tag WHERE asset='btc' AND PriceUSD IS NOT NULL", c, parse_dates=["tag"]).set_index("tag").PriceUSD
    c.close()
    btc_an = (btc > btc.rolling(200).mean()).where(btc.rolling(200).count() == 200)
    F = pd.DataFrame(index=idx)
    F["F1 Makro Gesamt kurz"] = S["Gesamt kurz"] != -1
    F["F2 Makro Gesamt lang"] = S["Gesamt lang"] != -1
    F["F3 Netto-Liquiditaet kurz"] = S["K2 Netto-Liquiditaet kurz"] != -1
    F["F4 Dollar kurz"] = S["K8 Dollar kurz"] != -1
    F["F5 Nasdaq ueber 200 T"] = nq_an.reindex(idx).ffill().fillna(1.0) == 1.0
    F["F6 BTC ueber 200 T"] = btc_an.reindex(idx).ffill().fillna(1.0) == 1.0
    F = F.shift(1)                                         # Zustand des Vortags
    F = F.loc["2023-06-01":"2026-09-30"].fillna(True).astype(int)
    os.makedirs(os.path.dirname(CACHE), exist_ok=True)
    F.to_csv(CACHE)
    return F


# ── Handel ──────────────────────────────────────────────────────────────────────────────────────────────────────────────
_r = {}


def tagesreihe(menge):
    E = pd.read_csv(os.path.join("data", "_vergleich", "kern48jbz_einstiege_%s.csv" % menge), sep=";")
    netto, tag = [], []
    for s, st in zip(E.symbol, E.stunde):
        if s not in _r:
            _r[s] = P.reihe(s)
        x = _r[s]
        if x is None:
            continue
        a, L, C = x
        i = int(st) - a
        if 0 <= i and i + 24 < len(C) and np.isfinite(C[i]) and np.isfinite(C[i + 24]):
            netto.append(C[i + 24] / C[i] - 1 - KOSTEN)
            tag.append((P.B0 + pd.Timedelta(hours=int(st))).normalize())
    D = pd.DataFrame({"netto": netto, "tag": tag})
    g = D.groupby("tag").netto.agg(["sum", "count"]).reindex(TAGE).fillna(0.0)
    return g["sum"].to_numpy(), g["count"].to_numpy()


def strecken(z):
    rand = np.flatnonzero(np.diff(z)) + 1
    return np.split(z, rand)


def permutiere(z, rng):
    st = strecken(z)
    rng.shuffle(st)
    return np.concatenate(st)


def kennzahlen(z, s, n, maske):
    z = z[maske].astype(bool)
    s, n = s[maske], n[maske]
    an = s[z].sum() / max(n[z].sum(), 1)
    aus = s[~z].sum() / max(n[~z].sum(), 1)
    alle = s.sum() / max(n.sum(), 1)
    return an, aus, alle, int((~z).sum()), s[z].sum() / len(z), s.sum() / len(z)


def rang(z, s, n, maske, rng, k=1000):
    an, _, alle, *_ = kennzahlen(z, s, n, maske)
    echt = an - alle
    zz = z[maske]
    null = np.empty(k)
    for i in range(k):
        zp = permutiere(zz, rng).astype(bool)
        sm, nm = s[maske], n[maske]
        null[i] = sm[zp].sum() / max(nm[zp].sum(), 1) - alle
    return float(np.mean(null < echt))


def urteil(z, R, rng, k=1000):
    """Kriterium §4 fuer einen Filter z (Tagesraster TAGE). R: Menge -> (s, n)."""
    umkehr = True
    for m in UNV:
        s, n = R[m]
        for j in ("2025", "2026"):
            mk = (TAGE.year == int(j))
            an, aus, _, tage_aus, *_ = kennzahlen(z, s, n, mk)
            if tage_aus >= 30:
                umkehr &= an > 0 and aus < 0
            else:
                umkehr = False
    raenge = [rang(z, R[m][0], R[m][1], T2526, rng, k) for m in UNV]
    return umkehr and min(raenge) >= 0.99, umkehr, raenge


def main():
    print("P71 F-1 MARKTFILTER · REGEL0-Einstiege 2024-01..2026-08 · Kosten 0,48 %\n")
    F = filter_tabelle()
    R = {m: tagesreihe(m) for m in MENGEN}
    rng = np.random.default_rng(71)
    # Selbsttest
    z1 = F["F1 Makro Gesamt kurz"].reindex(TAGE).to_numpy()
    fehl = 0
    for i in range(200):
        zr = np.concatenate([z1[~T2526], permutiere(z1[T2526], rng)])
        fehl += int(urteil(zr, R, rng, k=200)[0])
    s1, n1 = R["unverzerrt_1"]
    tn = pd.Series(np.where(n1 > 0, s1 / np.maximum(n1, 1), 0.0), index=TAGE).rolling(31, center=True, min_periods=5).mean()
    zw = (tn > 0).astype(int).to_numpy()
    rang_w = [rang(zw, R[m][0], R[m][1], T2526, rng, 1000) for m in UNV]
    ok = fehl / 200 <= 0.05 and min(rang_w) >= 0.99
    print("SELBSTTEST: Fehlalarm %d von 200 Zufallsfiltern (%.1f %%, Soll <= 5 %%) · Positivkontrolle Rang %s -> %s\n"
          % (fehl, 100 * fehl / 200, " / ".join("%.3f" % r for r in rang_w), "BESTANDEN" if ok else "NICHT BESTANDEN"))
    if not ok:
        print("Selbsttest nicht bestanden - es wird NICHT gemessen (§4).")
        return
    # Aufloesung (Pflanzung +0,3 Pp auf an-Tage eines Zufallsfilters, unverzerrt_1..3)
    fund = 0
    for i in range(100):
        zr = np.concatenate([z1[~T2526], permutiere(z1[T2526], rng)]).astype(bool)
        Rp = {m: (R[m][0] + np.where(zr, 0.003 * R[m][1], 0.0), R[m][1]) for m in MENGEN}
        fund += int(min(rang(zr.astype(int), Rp[m][0], Rp[m][1], T2526, rng, 200) for m in UNV) >= 0.99)
    print("AUFLOESUNG: Pflanzung +0,3 Pp auf die an-Tage (Struktur F1) gefunden in %d von 100\n" % fund)
    for name in F.columns:
        z = F[name].reindex(TAGE).to_numpy()
        wechsel = int(np.abs(np.diff(z)).sum())
        tr, umk, rg = urteil(z, R, rng)
        print("=== %s · Anteil an %.0f %% · Wechsel 2024-26: %d · Umkehr %s · Rang %s -> %s"
              % (name, 100 * z.mean(), wechsel, "ja" if umk else "nein", " / ".join("%.3f" % r for r in rg), "TRAEGT" if tr else "traegt nicht"))
        for m in MENGEN:
            s, n = R[m]
            teile = []
            for j in (2024, 2025, 2026):
                an, aus, alle, ta, g_mit, g_ohne = kennzahlen(z, s, n, TAGE.year == j)
                teile.append("%d an %+.3f aus %+.3f (Tage aus %d) · je Tag mit %+.3f / ohne %+.3f" % (j, 100 * an, 100 * aus, ta, 100 * g_mit, 100 * g_ohne))
            print("   %-13s %s" % (m, " | ".join(teile)))
    alle_an = F.reindex(TAGE).min(axis=1).to_numpy()
    s, n = R["unverzerrt_1"]
    print("\nAuskunft 'alle sechs an' (unverzerrt_1): Anteil an %.0f %% · " % (100 * alle_an.mean()) + " · ".join(
        "%d an %+.3f / aus %+.3f" % (j, 100 * kennzahlen(alle_an, s, n, TAGE.year == j)[0], 100 * kennzahlen(alle_an, s, n, TAGE.year == j)[1])
        for j in (2024, 2025, 2026)))


if __name__ == "__main__":
    main()
