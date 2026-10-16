"""P60 GEGENPROBE zur W3-Vorpruefung (16.10.2026): haengt das NEIN an der Drittelbildung, am Zeitpunkt oder an der Zielgroesse?

    python Basisinfos/Rechenkern_02_10/p60_gegenprobe.py > Basisinfos/Rechenkern_02_10/p60_gegenprobe.txt

Nur lesend. Zweiter Rechenweg, unabhaengig von pandas fuer die Zielgroesse (csv-Modul, eigene Auswertung von t_u/t_d).
  G1  Zielgroesse auf zweitem Weg: Summe Q je Menge gleich p60?
  G2  absolute Teilung BTC 7 T < 0 gegen >= 0 statt Drittel: Vorzeichen des Unterschieds je Jahr
  G3  Zustand zur EINSTIEGSstunde (t+1) statt zur Signalstunde: D je Jahr
"""
import csv
import os
import sys

HIER = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.dirname(os.path.dirname(HIER))
os.chdir(PROJ)
sys.path.insert(0, PROJ)

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

import messe_e2_beitraege as E2  # noqa: E402
from messe_k3_kontextflaeche import reihe  # noqa: E402

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:  # noqa: BLE001
    pass

JAHRE = (2024, 2025, 2026)
btc = reihe([(E2.EINGESTELLT_DB, "SELECT stunde, close FROM stundenkurse WHERE symbol='BTC'"),
             (E2.STUNDEN_DB, "SELECT stunde, close FROM stundenkurse WHERE symbol='BTC'")])
LH = len(btc)
b7 = np.full(LH, np.nan)
b7[168:] = btc[168:] / btc[:-168] - 1.0
rang = pd.Series(b7).rolling(8760, min_periods=4000).rank(pct=True).to_numpy()


def drittel(h):
    r = rang[h]
    return -1 if not np.isfinite(r) else (0 if r <= 1 / 3 else (1 if r <= 2 / 3 else 2))


def q_von(tu, td):
    u = float(tu) if tu not in ("", None) else float("inf")
    d = float(td) if td not in ("", None) else float("inf")
    if u <= 24 and u < d:
        return 1
    if d <= 24 and d <= u:
        return -1
    return 0


def mittel(werte):
    return sum(werte) / len(werte) if werte else float("nan")


print("P60 GEGENPROBE · W3-Vorpruefung auf einem zweiten Weg\n")
for m in ("bestand", "unverzerrt_1", "unverzerrt_2", "unverzerrt_3"):
    zeilen = list(csv.DictReader(open(os.path.join("data", "_vergleich", "kern48jbz_einstiege_%s.csv" % m), encoding="utf-8"),
                                 delimiter=";"))
    zeilen = [z for z in zeilen if int(z["jahr"]) in JAHRE]
    q = [q_von(z["t_u"], z["t_d"]) for z in zeilen]
    print("%-13s G1 Summe Q %d bei %d Einstiegen (Mittel %+.4f)" % (m, sum(q), len(q), mittel(q)))
    g2, g3 = [], []
    for j in JAHRE:
        pos = [qq for z, qq in zip(zeilen, q) if int(z["jahr"]) == j and np.isfinite(b7[int(z["stunde"])]) and b7[int(z["stunde"])] >= 0]
        neg = [qq for z, qq in zip(zeilen, q) if int(z["jahr"]) == j and np.isfinite(b7[int(z["stunde"])]) and b7[int(z["stunde"])] < 0]
        g2.append("%d %+.4f (n %d/%d)" % (j, mittel(pos) - mittel(neg), len(pos), len(neg)))
        hoch = [qq for z, qq in zip(zeilen, q) if int(z["jahr"]) == j and drittel(int(z["stunde"]) + 1) == 2]
        tief = [qq for z, qq in zip(zeilen, q) if int(z["jahr"]) == j and drittel(int(z["stunde"]) + 1) == 0]
        g3.append("%d %+.4f" % (j, mittel(hoch) - mittel(tief)))
    print("              G2 Q(BTC 7 T >= 0) - Q(< 0): " + " · ".join(g2))
    print("              G3 D zur Einstiegsstunde t+1: " + " · ".join(g3))
