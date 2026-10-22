"""A1 BESTANDSAUFNAHME (22.10.2026, Bestandsaufnahme_brutto_netto_22_10.md): rechnet NACH, ob einer der Hebel die Kostenluecke der REGEL0 schliessen
KOENNTE - als OBERGRENZE in der Rueckschau, ausdruecklich keine Messung einer neuen Regel.

    python Basisinfos/Rechenkern_02_10/a1_hebel_rechnung.py

Einstiege: data/_vergleich/kern48jbz_einstiege_<menge>.csv (REGEL0 = Kern s 0,035 + Ruhe 48 h + J, vier Mengen), 2025-01..2026-08.
24-h-Ertrag = Schluss Einstiegsstunde -> Schluss 24 h spaeter (wie O21/R-R11); Kurse wie p64.reihe (stundenkurse, _alle, eingestellt).
R0  R-R11: Mittel 2025-26 'bestand' = Referenz +0,55 % (Schritt7 §23.64)?
H1  Haltedauer: Mittel bei 6 / 12 / 24 h (Auskunft; die Finanzierung je Stunde oder je Tag ist eine offene FAKTfrage)
H2  Signalflut-Sperre als OBERGRENZE: N24 = Zahl der Einstiege derselben Menge in den 24 Stunden VOR der Einstiegsstunde (nur fruehere Stunden,
    vorab beobachtbar). Ohne die Einstiege mit N24 >= Perzentil 70/80/90 aller Einstiege: Mittel und Anteil weg. Tagesblock-95 % (Bootstrap ueber Tage).
H3  Kombination als OBERGRENZE: 12 h halten UND Sperre P70/P80, gegen 0,39 % (0,30 % Gebuehr + halbe Tagesfinanzierung - NUR falls je Stunde
    abgerechnet wird; offene Faktfrage)
Kosten: 0,48 % je Tageshandel (Bitpanda Hebel, 2.690). Fusion ohne Hebel 2 x 0,25 % = 0,50 %.
"""
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.chdir(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import p64_lc_voranalyse as P  # noqa: E402

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:  # noqa: BLE001
    pass
KOSTEN = 0.0048
MENGEN = ("bestand", "unverzerrt_1", "unverzerrt_2", "unverzerrt_3")
_cache = {}


def ertraege(menge):
    E = pd.read_csv(os.path.join("data", "_vergleich", "kern48jbz_einstiege_%s.csv" % menge), sep=";")
    E = E[E.jahr >= 2025].copy()
    r6, r12, r24 = [], [], []
    for s, st in zip(E.symbol, E.stunde):
        if s not in _cache:
            _cache[s] = P.reihe(s)
        x = _cache[s]
        v = [np.nan] * 3
        if x is not None:
            a, _L, C = x
            i = int(st) - a
            if 0 <= i and i + 24 < len(C) and np.isfinite(C[i]):
                v = [C[i + h] / C[i] - 1 if np.isfinite(C[i + h]) else np.nan for h in (6, 12, 24)]
        r6.append(v[0])
        r12.append(v[1])
        r24.append(v[2])
    E["r6"], E["r12"], E["r24"] = r6, r12, r24
    E = E[E.r24.notna()].copy()
    st = np.sort(E.stunde.to_numpy())
    E["n24"] = np.searchsorted(st, E.stunde.to_numpy(), "left") - np.searchsorted(st, E.stunde.to_numpy() - 24, "left")
    E["tag"] = (E.stunde // 24).astype(int)
    return E


def tagesblock(E, saat=1, n=2000):
    g = E.groupby("tag").r24.agg(["sum", "count"])
    rng = np.random.default_rng(saat)
    idx = rng.integers(0, len(g), (n, len(g)))
    m = g["sum"].to_numpy()[idx].sum(axis=1) / g["count"].to_numpy()[idx].sum(axis=1)
    return np.percentile(m, 2.5), np.percentile(m, 97.5)


def main():
    print("A1 HEBEL-RECHNUNG · REGEL0-Einstiege 2025-01..2026-08 · Kosten Bitpanda-Hebel 0,48 %% je Tageshandel\n")
    for menge in MENGEN:
        E = ertraege(menge)
        lo, hi = tagesblock(E)
        print("%s: %d Einstiege an %d Tagen" % (menge, len(E), E.tag.nunique()))
        print("  24 h Mittel %+.3f %% [Tagesblock %+.2f; %+.2f] · Luecke zu 0,48 %%: %+.3f Pp" % (100 * E.r24.mean(), 100 * lo, 100 * hi,
                                                                                               100 * (E.r24.mean() - KOSTEN)))
        print("  H1 Haltedauer: 6 h %+.3f %% · 12 h %+.3f %% · 24 h %+.3f %%" % (100 * E.r6.mean(), 100 * E.r12.mean(), 100 * E.r24.mean()))
        for p in (70, 80, 90):
            grenze = np.percentile(E.n24, p)
            X = E[E.n24 < grenze]
            lo, hi = tagesblock(X)
            print("  H2 Sperre ab N24 >= %4.0f (P%d): weg %4.1f %% · Mittel uebrig %+.3f %% [%+.2f; %+.2f] · weg %+.3f %% · Luecke %+.3f Pp"
                  % (grenze, p, 100 * (1 - len(X) / len(E)), 100 * X.r24.mean(), 100 * lo, 100 * hi, 100 * E[E.n24 >= grenze].r24.mean(),
                     100 * (X.r24.mean() - KOSTEN)))
        for p in (70, 80):
            X = E[E.n24 < np.percentile(E.n24, p)]
            print("  H3 12 h + Sperre P%d: Mittel %+.3f %% · Luecke zu 0,39 %%: %+.3f Pp" % (p, 100 * X.r12.mean(), 100 * (X.r12.mean() - 0.0039)))
        if menge == "bestand":
            ref = E[E.jahr.isin([2025, 2026])].r24.mean()
            print("  R0 R-R11: bestand 2025-26 %+.3f %% (Referenz Schritt7 §23.64: +0,55 %%) -> %s" % (100 * ref, "GLEICH" if abs(100 * ref - 0.55) < 0.015
                                                                                                    else "ABWEICHUNG"))
            E.to_csv(os.path.join("data", "_vergleich", "a1_einstiege_bestand.csv"), sep=";", index=False)
        print()
    print("Fusion ohne Hebel: 2 x 0,25 %% = 0,50 %% je Runde (Stufe 2 ab 100.000 EUR Umsatz in 30 T: 0,42 %%)")


if __name__ == "__main__":
    main()
