"""N4-Voranalyse (05.10.2026): Selbsttest der Messregel gegen BEKANNTE WAHRHEIT, bevor ein einziger Gemini-Aufruf faellt (Messstandard).

    python Basisinfos/Rechenkern_02_10/n4_selbsttest_messregel.py

Echte Anker der Entwicklungsmenge (n4_anker_entwicklung.csv) mit ihrem echten 24-h-Ertrag ohne Hebel (data/_vergleich/b0_spur_bestand.csv,
Spalte spot). Die Urteile sind SIMULIERT: Verteilung wie Trader 0.1e im Kalibrierlauf (stuetzt 10 %, neutral 45 %, spricht dagegen 45 %),
gepflanzte Staerke k (k = 0: Urteile unabhaengig vom Ertrag). Gemessen wird, wie oft die Messregel
  R1 (vorab §20.5): Mittel stuetzt - Mittel spricht_dagegen, Nullwelt Vertauschen INNERHALB DES TAGES, Band 95. Perzentil, je Jahr
  R2 (Vorschlag):   dieselbe Groesse, Vertauschen innerhalb der KALENDERWOCHE
  R3 (Vorschlag):   Rangkorrelation Stimmen-Saldo (stuetzt - spricht_dagegen von 5 Stimmen) mit dem Ertrag, Vertauschen innerhalb der Woche
einen Effekt meldet - ohne Effekt (Fehlalarm, Soll <= 5 %) und mit Effekt (Fundquote). Nur lesend, kein Netz.
"""
import os
import numpy as np
import pandas as pd

os.chdir(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
RNG = np.random.default_rng(20261005)
WELTEN, PERM = 200, 200
a = pd.read_csv("Basisinfos/Rechenkern_02_10/n4_anker_entwicklung.csv", sep=";")
s = pd.read_csv("data/_vergleich/b0_spur_bestand.csv", sep=";")[["symbol", "std", "spot"]]
a = a.merge(s, on=["symbol", "std"], how="left")
assert a["spot"].notna().all(), "Anker ohne Ertrag"
a["tag"] = pd.to_datetime(a["signalstunde_utc"]).dt.date
a["woche"] = pd.to_datetime(a["signalstunde_utc"]).dt.strftime("%G-%V")
print("Entwicklungsmenge: %d Anker · Ertrag 24 h ohne Hebel: Mittel %+.2f %%, Streuung %.2f %%" % (len(a), 100 * a["spot"].mean(), 100 * a["spot"].std()))
for j, g in a.groupby("jahr"):
    t = g.groupby("tag").size()
    print("  %d: %d Anker an %d Tagen · Tage mit nur EINEM Anker: %d (%.0f %% der Anker) · %d Wochen" % (
        j, len(g), len(t), int((t == 1).sum()), 100 * (t == 1).sum() / len(g), g["woche"].nunique()))


def gruppen_perm(idx_gruppen, n):
    """Permutation der Positionen nur innerhalb der Gruppen."""
    p = np.arange(n)
    for ix in idx_gruppen:
        if len(ix) > 1:
            p[ix] = RNG.permutation(ix)
    return p


def welt(g, k):
    r = g["spot"].values
    z = (r - r.mean()) / r.std()
    lat = k * z + RNG.standard_normal(len(r))
    q10, q55 = np.quantile(lat, [0.90, 0.45])
    lab = np.where(lat >= q10, 1, np.where(lat <= q55, -1, 0))              # +1 stuetzt, -1 spricht dagegen
    # Stimmen-Saldo: 5 Stimmen, jede mit Wahrscheinlichkeit aus dem latenten Wert
    pst = 1 / (1 + np.exp(-(lat - 1.3) * 2)); pdg = 1 / (1 + np.exp((lat + 0.1) * 2))
    saldo = RNG.binomial(5, np.clip(pst, 0, 1)) - RNG.binomial(5, np.clip(pdg, 0, 1))
    return r, lab, saldo


def stat_diff(r, lab):
    a1, a2 = r[lab == 1], r[lab == -1]
    return a1.mean() - a2.mean() if len(a1) and len(a2) else 0.0


def rang(x):
    return pd.Series(x).rank().values


def test(g, k):
    r, lab, saldo = welt(g, k)
    n = len(r)
    tg = [np.where(g["tag"].values == t)[0] for t in np.unique(g["tag"].values)]
    wo = [np.where(g["woche"].values == w)[0] for w in np.unique(g["woche"].values)]
    s1 = stat_diff(r, lab)
    rr, rs = rang(r), rang(saldo)
    s3 = np.corrcoef(rr, rs)[0, 1]
    n1, n2, n3 = [], [], []
    for _ in range(PERM):
        p = gruppen_perm(tg, n); n1.append(stat_diff(r, lab[p]))
        p = gruppen_perm(wo, n); n2.append(stat_diff(r, lab[p])); n3.append(np.corrcoef(rr, rs[p])[0, 1])
    return s1 > np.percentile(n1, 95), s1 > np.percentile(n2, 95), s3 > np.percentile(n3, 95), s1


print()
print("Fehlalarm (k = 0) und Fundquote je gepflanzter Staerke k, je Jahr %d Welten mit je %d Vertauschungen" % (WELTEN, PERM))
print("  k     | gepflanzter Unterschied stuetzt-dagegen | R1 Tag | R2 Woche | R3 Saldo/Woche")
for k in (0.0, 0.10, 0.20, 0.30, 0.50):
    for j, g in a.groupby("jahr"):
        res = np.array([test(g, k) for _ in range(WELTEN)], dtype=float)
        print("  %.2f  %d | %+6.2f Prozentpunkte (Mittel)             | %4.0f %% | %6.0f %% | %8.0f %%" % (
            k, j, 100 * res[:, 3].mean(), 100 * res[:, 0].mean(), 100 * res[:, 1].mean(), 100 * res[:, 2].mean()))
