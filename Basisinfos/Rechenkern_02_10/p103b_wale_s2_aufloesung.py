# -*- coding: utf-8 -*-
"""G16 Wale STUFE 2 — VORANALYSE, Teil F: AUFLÖSUNG auf den REGEL0-Einstiegen (31.10.2026).

Kein echtes E: die Fünftel sind KÜNSTLICH (AR(1) je Symbol mit der echten Autokorrelation und dem echten Gleichlauf aus Fassung 4),
die Erträge sind die ECHTEN 24-h-Erträge der REGEL0-Einstiege (wie p71: Schluss der Einstiegsstunde bis 24 h später, hier Log, brutto).

Weil die künstlichen Fünftel vom Ertrag unabhängig sind, ist die Verteilung von D über diese Welten die NULLVERTEILUNG. Eine
Pflanzung +k im obersten, -k im untersten Fünftel verschiebt D um genau 2k; also ist die Auflösung (80 % gefunden bei einseitig 5 %)
X = q95 - q20 der Nullverteilung. Zweiter Weg (Gegenprobe): cluster-robuster Standardfehler je Einstiegstag, X ≈ (1,645 + 0,842)·SE.

Zuordnung im Betrieb (aus Teil E gemessen: die Tagesdatei liegt 1,7-2,7 h nach Mitternacht vor):
    Einstieg ab 03:00 UTC am Tag t  -> E des Tages t-1; der Tag danach (t) überlappt das 24-h-Fenster zu (24 - h)/24
    Einstieg 00:00-02:59 UTC        -> E des Tages t-2; der Tag danach (t-1) ist vorbei -> Überlappung 0
Die Überlappung war die erste Annahme ("gleichmäßig"); ÜBERHOLT durch Teil G (gemessenes Profil): D am Einstieg ≈ 0,86 × Tageseffekt.

    python -X utf8 Basisinfos/Rechenkern_02_10/p103b_wale_s2_aufloesung.py
"""
import os
import sys
from datetime import datetime

import numpy as np
import pandas as pd

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HIER)
import p103_wale_s2_voranalyse as V  # noqa: E402  (setzt das Arbeitsverzeichnis)
import p64_lc_voranalyse as P  # noqa: E402

PHI, RHO = 0.037, 0.021          # Fassung 4: Autokorrelation E (Mittel der sechs) und Gleichlauf (p102_wale_selbsttest_f4.txt)
Z80 = 0.8416                     # Fünftelgrenze der Standardnormalen
WELTEN = 2000
STICHTAG_H = 3                   # ab dieser UTC-Stunde gilt E des Vortags (Tagesdatei + Puffer)
GITTER = (0.10, 0.15, 0.20, 0.25, 0.30, 0.35)   # D am Einstieg in Pp (Teil G: Fassung 4 H1 0,35 × 0,86 ≈ 0,30)
FAKTOR_G = 0.86                  # Teil G (p103c): D am Einstieg = 0,85-0,87 × Tageseffekt H1, gemessenes Profil × Einstiegsstunde
AUS = []


def zeige(s=""):
    print(s, flush=True)
    AUS.append(s)


def ertraege(e):
    y = np.full(len(e), np.nan)
    cache = {}
    for i, (s, st) in enumerate(zip(e.symbol, e.stunde)):
        if s not in cache:
            cache[s] = P.reihe(s)
        x = cache[s]
        if x is None:
            continue
        a, _L, C = x
        j = int(st) - a
        if 0 <= j and j + 24 < len(C) and np.isfinite(C[j]) and np.isfinite(C[j + 24]) and C[j] > 0:
            y[i] = np.log(C[j + 24] / C[j])
    return y


def nullwelten(sym_i, tag_i, nsym, ntag, rng, welten=WELTEN, stapel=100):
    """Künstliche Fünftel (+1/0/-1) je Einstieg, Form (welten, n)."""
    out = np.empty((welten, len(sym_i)), np.int8)
    s1 = np.sqrt(max(1e-9, 1 - PHI ** 2))
    for w0 in range(0, welten, stapel):
        w = min(stapel, welten - w0)
        c = np.empty((w, ntag))
        e = np.empty((w, nsym, ntag))
        c[:, 0] = rng.standard_normal(w)
        e[:, :, 0] = rng.standard_normal((w, nsym))
        for t in range(1, ntag):
            c[:, t] = PHI * c[:, t - 1] + s1 * rng.standard_normal(w)
            e[:, :, t] = PHI * e[:, :, t - 1] + s1 * rng.standard_normal((w, nsym))
        z = np.sqrt(RHO) * c[:, None, :] + np.sqrt(1 - RHO) * e
        zz = z[:, sym_i, tag_i]
        out[w0:w0 + w] = np.where(zz > Z80, 1, np.where(zz < -Z80, -1, 0))
    return out


def d_welten(L, y):
    o, u = (L == 1), (L == -1)
    return (o @ y) / o.sum(1) - (u @ y) / u.sum(1)


def se_cluster(y, tag):
    """Zweiter Weg: SE von D bei zufälligen Fünfteln (20/60/20), cluster-robust je Einstiegstag.
    D = mean_o - mean_u; unter H0 ist Var(D) ≈ Var(Summe der Beiträge je Tag) mit Gewicht ±1/(0,2 n)."""
    n = len(y)
    yc = y - y.mean()
    # je Einstieg Beitrag a_i = (L_i == 1)/n_o - (L_i == -1)/n_u, E[a_i a_j] für i≠j (unabhängige Fünftel) = 0 bis auf Gleichlauf;
    # bei unabhängigen Fünfteln fällt die Tageskorrelation also nur über den Gleichlauf RHO an. Var(a_i) = 2 * 0,2 / (0,2 n)^2.
    var_unab = (yc ** 2).sum() * 2 * 0.2 / (0.2 * n) ** 2
    # Gleichlauf: Korrelation der Fünftel zweier Symbole am selben Tag ≈ RHO (latent) -> Fünftelkorrelation, numerisch geschätzt
    s = pd.Series(yc).groupby(tag).sum()
    paar = (s ** 2).sum() - (yc ** 2).sum()                     # Summe über Paare i≠j desselben Tages von yc_i yc_j
    return np.sqrt(max(0.0, var_unab + paar * KOR_L * 2 * 0.2 / (0.2 * n) ** 2))


KOR_L = None


def main():
    global KOR_L
    rng = np.random.default_rng(20261031)
    # Fünftelkorrelation bei latentem Gleichlauf RHO (für den zweiten Weg), numerisch
    # zwei SYMBOLE mit gemeinsamem Faktor c: corr(a, b) = RHO (31.10.: zuerst c selbst als Symbol genommen -> corr sqrt(RHO), falsch)
    c = rng.standard_normal(2_000_000)
    a = np.sqrt(RHO) * c + np.sqrt(1 - RHO) * rng.standard_normal(2_000_000)
    b = np.sqrt(RHO) * c + np.sqrt(1 - RHO) * rng.standard_normal(2_000_000)
    la = np.where(a > Z80, 1, np.where(a < -Z80, -1, 0))
    lb = np.where(b > Z80, 1, np.where(b < -Z80, -1, 0))
    KOR_L = float(np.corrcoef(la, lb)[0, 1])

    zeige("VORANALYSE G16 STUFE 2 — F AUFLÖSUNG (Gerät %s, %s) · künstliche Fünftel AR(1) phi %.3f, Gleichlauf rho %.3f "
          "(Fünftelkorrelation %.4f) · %d Welten · echte 24-h-Erträge (Log, brutto)" % (
              os.environ.get("COMPUTERNAME", "?"), datetime.now().isoformat(timespec="seconds"), PHI, RHO, KOR_L, WELTEN))
    E = V.einstiege()
    T = V.spot_tabelle(sorted(set().union(*[set(e.symbol) for e in E.values()])))
    MASKE, *_ = V.abdeckung(E, T)

    for m, e in E.items():
        e = e[MASKE[m]].copy()
        e["y"] = ertraege(e)
        e = e[np.isfinite(e.y)].reset_index(drop=True)
        h = e.ein.dt.hour.to_numpy()                   # Einstieg = Schluss der Einstiegsstunde
        tag = e.ein.dt.normalize()
        eday = tag - pd.to_timedelta(np.where(h >= STICHTAG_H, 1, 2), unit="D")
        ueber = np.where(h >= STICHTAG_H, (24 - h) / 24.0, 0.0)
        sym_c = pd.Categorical(e.symbol)
        d0 = eday.min()
        tag_i = ((eday - d0) / pd.Timedelta(days=1)).astype(int).to_numpy()
        L = nullwelten(sym_c.codes, tag_i, len(sym_c.categories), tag_i.max() + 1, rng)
        y = e.y.to_numpy()
        ytag = y - pd.Series(y).groupby(tag.to_numpy()).transform("mean").to_numpy()
        zeige("\n══ %s · %d Einstiege mit E und Kurs · %d Symbole · Streuung 24 h %.2f %% · tagesbereinigt %.2f %% ══" % (
            m, len(e), e.symbol.nunique(), 100 * y.std(), 100 * ytag.std()))
        zeige("  Einstiegsstunde UTC: 00-02 %.1f %% · 03-11 %.1f %% · 12-17 %.1f %% · 18-23 %.1f %%  ->  Überlappung mit dem Folgetag "
              "%.3f (Annahme 'gleichmäßig' — ÜBERHOLT durch Teil G: gemessen %.2f)" % (100 * (h < 3).mean(), 100 * ((h >= 3) & (h < 12)).mean(), 100 * ((h >= 12) & (h < 18)).mean(),
                                     100 * (h >= 18).mean(), ueber.mean(), FAKTOR_G))
        teil = {"2024-01..2026-08": np.ones(len(e), bool)}
        for j in (2024, 2025, 2026):
            teil[str(j)] = (e.jahr == j).to_numpy()
        teil["ungesehen (ohne Kern/F4)"] = ~e.symbol.isin(V.GELADEN).to_numpy()
        for art, yy in (("roh", y), ("tagesbereinigt", ytag)):
            for name, mk in teil.items():
                D0 = d_welten(L[:, mk], yy[mk])
                q95, q20 = np.quantile(D0, 0.95), np.quantile(D0, 0.20)
                x = 100 * (q95 - q20)
                se2 = 100 * 2.487 * se_cluster(yy[mk], tag.to_numpy()[mk])
                zeile = "  %-15s %-26s n %5d · Null-SD %.3f Pp · X (D am Einstieg, 80 %%) %.2f Pp [2. Weg %.2f] · Tageseffekt nötig %.2f Pp" % (
                    art, name, mk.sum(), 100 * D0.std(), x, se2, x / FAKTOR_G)
                zeige(zeile)
                if name == "2024-01..2026-08":
                    # Teil G (p103c): gemessenes Tagesprofil, gewichtet mit der Einstiegsstunde -> D am Einstieg ≈ 0,87 × H1
                    zeige("        Fundquote nach D am Einstieg: " + " · ".join(
                        "%.2f Pp %3.0f %%" % (d, 100 * (D0 + d / 100 > q95).mean()) for d in GITTER))

    with open(os.path.join(HIER, "p103b_wale_s2_aufloesung.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(AUS) + "\n")


if __name__ == "__main__":
    main()
