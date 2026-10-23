"""P68b (23.10.2026, Voranalyse_REGEL0_Kosten_23_10.md §6): Limit-Einstieg (O3) als SPOT ueber Fusion - Nutzer 23.10.: bei Bitpanda-Hebel
KEIN Limit-Kauf (nur Verkauf mit TP/SL), bei Spot fast durchgaengig (ausser kleine Coins). Auskunft, Obergrenze in der Rueckschau.

    python Basisinfos/Rechenkern_02_10/p68b_spot_limit.py

Kosten Fusion 2 x 0,25 % = 0,50 % (Grundstufe, keine Finanzierung). Abdeckung gegen den Bitpanda-Katalog vom 08.10.2026 (844 Krypto-Werte,
Stellvertreter fuer Fusion - die Fusion-Paarliste selbst ist nicht geladen). Limit wie p68 O3, je Jahr und Menge.
"""
import os
import sys

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.chdir(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import p68_gegenprobe as GP  # noqa: E402  (zeilen() und limit_netto() - dort gegen SQL geprueft, G1 300/300)

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:  # noqa: BLE001
    pass
KAT = set(pd.read_csv(os.path.join("data", "_spot", "bitpanda_katalog_krypto_2026-10-08.csv"), sep=";").symbol.str.upper())
print("\nP68b LIMIT-EINSTIEG ALS FUSION-SPOT (Kosten 0,50 %%) · Bitpanda-Katalog %d Werte\n" % len(KAT))
for m in GP.MENGEN:
    D = GP.alle[m]
    B = D[D.symbol.isin(KAT)]
    teile = []
    for x in (0.0, 0.005, 0.01, 0.015, 0.02):
        if x == 0.0:
            r = B.c24 / B.c0 - 1
            teile.append("ohne Limit %+.3f (2025 %+.3f / 2026 %+.3f)" % (100 * (r.mean() - 0.005), 100 * (r[B.jahr == 2025].mean() - 0.005),
                                                                         100 * (r[B.jahr == 2026].mean() - 0.005)))
            continue
        n, f, _ = GP.limit_netto(B, x, kosten=0.005)
        n5 = GP.limit_netto(B[B.jahr == 2025], x, kosten=0.005)[0]
        n6 = GP.limit_netto(B[B.jahr == 2026], x, kosten=0.005)[0]
        teile.append("%.1f %% %+.3f (2025 %+.3f / 2026 %+.3f, gefuellt %.0f %%)" % (100 * x, 100 * n, 100 * n5, 100 * n6, 100 * f))
    print("%s: Abdeckung Bitpanda %.1f %% (%d von %d)\n   %s\n" % (m, 100 * len(B) / len(D), len(B), len(D), "\n   ".join(teile)))
