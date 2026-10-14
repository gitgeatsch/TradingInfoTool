"""P51 GEGENPROBE Makro-Umfeld (Spot §51.5) - eigener Rechenweg fuer Score, Ziel und Rang; nur lesend.

    python Basisinfos/Spot_Voranalyse_04_10/p51_gegenprobe.py

Liest die Rohdaten, die p51_messung.py nach data/_spot/p51_eingang.pkl gelegt hat (dieselben Reihen, NICHT dieselbe Rechnung):
  - Perzentil je Stichtag als Schleife: Anteil der Fensterwerte <= heutiger Wert (statt pandas rolling rank mit Mittelrang)
  - Ziel je Stichtag aus dem Kursdatum direkt (Kurs am Tag t+1+h gegen t+1, ohne Vorwaertsfuellung des Ziels)
  - Nullwelt als Verschiebung der Score-DATEN (Kalendertage, zirkulaer im gueltigen Zeitraum) statt Positionsrollen
Vergleich gegen p51_messung_n2.txt fuer die Faelle mit p <= 0,05: Abstand und Vorzeichen (die Nullwelt hier ist N1-artig und nur Auskunft).
"""
import os
import pickle
import re
import sys

import numpy as np
import pandas as pd

HIER = os.path.dirname(os.path.abspath(__file__))
os.chdir(os.path.dirname(os.path.dirname(HIER)))
sys.path.insert(0, HIER)
RNG = np.random.default_rng(777051)
FENSTER, MINDEST = 1826, 1095


def lade():
    with open(os.path.join("data", "_spot", "p51_eingang.pkl"), "rb") as f:
        return pickle.load(f)


def drittel_schleife(x, vz, tage, mittelrang=False):
    """Score nur an den gewuenschten Tagen, Perzentil = Anteil <= x_t im Fenster [t-1825, t] (nur gueltige Werte)."""
    v = x.values
    ix = {d: i for i, d in enumerate(x.index)}
    out = {}
    for d in tage:
        i = ix[d]
        w = v[max(0, i - FENSTER + 1): i + 1]
        w = w[~np.isnan(w)]
        if len(w) < MINDEST or np.isnan(v[i]):
            continue
        p = (np.sum(w < v[i]) + (np.sum(w == v[i]) + 1) / 2) / len(w) if mittelrang else np.mean(w <= v[i])
        out[d] = vz if p > 2 / 3 else (-vz if p < 1 / 3 else 0)
    return pd.Series(out, dtype=float)


def ziel_direkt(preis, h, tage):
    p = preis.dropna().sort_index()
    out = {}
    for d in tage:
        a, b = d + pd.Timedelta(days=1), d + pd.Timedelta(days=1 + h)
        pa, pb = p[:a], p[:b]
        if len(pa) == 0 or b > p.index[-1]:
            continue
        out[d] = np.log(pb.iloc[-1] / pa.iloc[-1])
    return pd.Series(out)


def abstand(s, y):
    j = pd.concat([s, y], axis=1, keys=["s", "y"]).dropna()
    p, m = j.y[j.s == 1], j.y[j.s == -1]
    return (p.mean() - m.mean()) if len(p) >= 5 and len(m) >= 5 else np.nan


def main():
    D = lade()
    K, Z, IDX = D["K"], D["Z"], D["IDX"]
    soll = {}
    txt = io_lesen(os.path.join(HIER, "p51_messung_n2.txt"))
    ziel = None
    for z in txt.splitlines():
        m = re.match(r"^(\S[^\[]+?)\s+\[(\w+)\]", z)
        if m:   # KORREKTUR: jeder Kopf setzt das Ziel neu, sonst ueberschreiben die Probe-/Auskunft-Abschnitte die T-Werte
            ziel = m.group(1).strip() if m.group(1).startswith("T") else None
        m = re.match(r"^\s{2}(K\d [A-Za-z0-9\- ]+? (?:lang|kurz))\s+n\+.*?\|\s+([+-]\d+\.\d) %.*?p hoch ([\d.]+) tief ([\d.]+)", z)
        if m and ziel:
            soll[(ziel, m.group(1).strip())] = (float(m.group(2)), min(float(m.group(3)), float(m.group(4))))
    faelle = [(k, v) for k, v in soll.items() if v[1] <= 0.05]
    print("P51 GEGENPROBE · %d Faelle mit p <= 0,05 aus p51_messung.txt\n" % len(faelle))
    # Ziel direkt aus dem Kurs: Ziel-Rohreihe rekonstruieren aus dem gespeicherten Ziel ist NICHT unabhaengig -> BTC aus CoinMetrics neu
    import p51_vorpruefung as V
    btc = V.coinmetrics_btc()
    preise = {"T1 BTC 90T": (btc, 90, "2013-01-01"), "T1 BTC 180T": (btc, 180, "2013-01-01")}
    gleich = 0
    for (zn, kn), (a_soll, p_soll) in faelle:
        name, art = kn.rsplit(" ", 1)
        lg, vl, kz, vk = K[name]
        if zn in preise:
            pr, h, ab = preise[zn]
            tage = [d for d in IDX if d.day == 1 and d >= pd.Timestamp(ab)]
            y = ziel_direkt(pr, h, tage)
        else:   # T2 Korb: Zielreihe aus der Messung (Korbbau ist eigenes Modul s1_messung, dort gegengeprueft)
            yv, ab = Z[zn]
            tage = [d for d in IDX if d.day == 1 and d >= pd.Timestamp(ab)]
            y = yv.reindex(tage).dropna()
        if art == "kurz" and kz is None:
            dk, d2 = lg - lg.shift(91), None
            print("  %-20s %-26s K5 kurz diskret - uebersprungen" % (zn, kn))
            continue
        x, vz = (lg, vl) if art == "lang" else (kz, vk)
        alle = [d for d in IDX if d.day == 1]
        s = drittel_schleife(x, vz, alle)
        a = abstand(s, y)
        a_mr = abstand(drittel_schleife(x, vz, alle, mittelrang=True), y)   # Bindungen (Wochenreihen taeglich gefuellt) als Mittelrang
        # Nullwelt: Score-Datum verschieben (zirkulaer im Zeitraum, in dem Score UND Ziel gueltig sind)
        gem = s.index.intersection(y.index)
        if len(gem) < 30:
            continue
        sv = s[gem].values
        yv_ = y[gem].values
        n = len(gem)
        null = []
        for _ in range(1000):
            k = int(RNG.integers(12, n - 12))     # in Monaten (Stichtage), Rand 12 M = 365 T
            null.append(abstand(pd.Series(np.roll(sv, k)), pd.Series(yv_)))
        null = np.array([v for v in null if v == v])
        p = min((np.sum(null >= a) + 1), (np.sum(null <= a) + 1)) / (len(null) + 1)
        ok_a = abs(100 * a - a_soll) <= max(1.0, 0.1 * abs(a_soll))
        ok_p = np.sign(a) == np.sign(a_soll)
        gleich += int(ok_a and ok_p)
        print("  %-20s %-26s Abstand %+6.1f %% (Mittelrang %+6.1f, Messung %+6.1f) · p %.4f (Messung %.4f) · %s" % (
            zn, kn, 100 * a, 100 * a_mr, a_soll, p, p_soll, "gleich" if (ok_a and ok_p) else "ABWEICHUNG"))
    print("\n=> %d von %d Faellen gleich (Abstand +-max(1 Pp, 10 %%), gleiches Vorzeichen)" % (gleich, len(faelle)))
    print("   Hinweis: p hier = Verschiebung in Monaten (N1-artig, laut Selbsttest zu eng) - nur Auskunft, kein Vergleichsmass.")


def io_lesen(p):
    import io
    return io.open(p, encoding="utf-8", errors="replace").read()


if __name__ == "__main__":
    main()
