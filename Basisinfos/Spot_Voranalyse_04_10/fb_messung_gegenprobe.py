"""Gegenprobe der Messung Teil B (Spot §31.3/§31.5) - eigener Rechenweg, nur lesend.

    python Basisinfos/Spot_Voranalyse_04_10/fb_messung_gegenprobe.py

  F1 L: 40 Anker der gewaehlten Stufe (ab 2024) - Ausloesung, Verkaufstag und d mit pandas neu
  F2 L: Korb ab 2024 aus der Ablage neu gemittelt = Ausgabe
  F3 L: Wahlregel (groesster Korb mit Rang >= 0,90, Gleichstand 1 Pp -> erste) auf die ausgegebenen Wahl-Zeilen neu = gewaehlte Stufe
  F4 K: 40 Anker - Ausstieg mit zweiter Umsetzung der Marke (cummax), d neu
  F5 K: Korb ab 2024 aus der Ablage neu = Ausgabe
  F6 K: Wahlregel neu = gewaehlte Stufe
  F7 K: 20 Einstiege - Bedingung Coin/BTC >= 1,3 x 30-T-Tief am Signaltag erfuellt, kein frueherer Einstieg desselben Coins binnen 30 T
  F8 Reihenfolge: alle DOSIS-Zeilen stehen NACH den URTEIL-Zeilen; Teil 0 im Soll
"""
import os
import re
import sys

import numpy as np
import pandas as pd

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HIER)
os.chdir(os.path.dirname(os.path.dirname(HIER)))
import as_messung as M      # noqa: E402

K, POS, BTCV, IDX = M.K, M.POS, M.BTCV, M.IDX
TXT = open(os.path.join(HIER, "fb_messung.txt"), encoding="utf-8").read()
L_TXT, K_TXT = TXT.split("ROLLE K")[0].split("ROLLE L")[1], TXT.split("ROLLE K")[1]
ok = n = 0


def pruefe(name, gut, info):
    global ok, n
    n += 1; ok += bool(gut)
    print("%-3s %s  %s" % (name, "gleich" if gut else "ABWEICHUNG", info), flush=True)


def gewaehlt(teil):
    m = re.search(r"GEWAEHLT \(vorab-Regel\): (.+)", teil)
    return m.group(1).strip() if m else None


def wahl_neu(teil):
    z = re.findall(r"^    (\S.*?)\s{2,}.*?Korb\s+([+-]\d+\.\d+) Pp.*?Rang (\d\.\d\d)", teil, re.M)
    g = [(s.strip(), float(k)) for s, k, r in z if float(r) >= 0.90]
    if not g:
        return None, z
    b = max(k for _, k in g)
    return next(s for s, k in g if k >= b - 1.0 - 1e-9), z


# ---------------------------------------------------------------- Rolle L
gL = gewaehlt(L_TXT)
neuL, zL = wahl_neu(L_TXT.split("URTEIL")[0])
pruefe("F3", (neuL or "keine") == (gL if gL and not gL.startswith("keine") else "keine"),
       "L Wahl neu %s · Ausgabe %s · %d Wahl-Zeilen" % (neuL, gL, len(zL)))
pfad = os.path.join("data", "_spot", "fb_messung_l.csv")
if gL and not gL.startswith("keine") and os.path.exists(pfad):
    L = pd.read_csv(pfad, sep=";", parse_dates=["t"])
    fx = 0
    for r in L.sample(min(40, len(L)), random_state=31).itertuples():
        i = POS[r.t]
        s = pd.Series(K[r.sym].values)
        p0 = s.iloc[i]
        x = s.iloc[i + 1:i + 366].reset_index(drop=True)
        b = pd.Series(BTCV[i + 1:i + 366] / BTCV[i])
        if not x.notna().all():
            m = x.notna().values.argmin()
            x, b = x[:m], b[:m]
        x = x / p0
        if gL.startswith("Z1"):
            ziel = x >= {"Z1 x1,5": 1.5, "Z1 x2": 2, "Z1 x3": 3}[gL]
        elif gL.startswith("Z3"):
            ziel = (x / b) >= {"Z3 +50 %": 1.5, "Z3 +100 %": 2}[gL]
        else:
            sig = np.log(s.iloc[i - 90:i + 1]).diff().std(ddof=0) * np.sqrt(90)
            ziel = x >= np.exp({"Z4 1 s": 1, "Z4 2 s": 2, "Z4 3 s": 3}[gL] * sig)
        hit = np.where(ziel.values)[0]
        j = int(hit[0]) + 1 if len(hit) and hit[0] + 1 < len(x) else None
        d = 0.5 * (x.iloc[j] - x.iloc[-1]) if j is not None else 0.0
        fx += not (abs(d - r.d) < 1e-9 and (j if j is not None else -1) == r.tag)
    pruefe("F1", fx == 0, "L %s: 40 Anker, Abweichungen %d" % (gL, fx))
    k = L.groupby("t").d.mean().mean()
    m = re.search(r"URTEIL ab 2024 .*?Korb\s+([+-]\d+\.\d+) Pp", L_TXT)
    pruefe("F2", m and abs(100 * k - float(m.group(1))) < 0.006, "L Korb neu %+.3f Pp · Ausgabe %s" % (100 * k, m.group(1) if m else None))

# ---------------------------------------------------------------- Rolle K
gK = gewaehlt(K_TXT)
neuK, zK = wahl_neu(K_TXT.split("URTEIL")[0])
pruefe("F6", neuK == gK or (neuK is None and gK == "keine"), "K Wahl neu %s · Ausgabe %s · %d Wahl-Zeilen" % (neuK, gK, len(zK)))
pfad = os.path.join("data", "_spot", "fb_messung_k.csv")
if gK and gK != "keine" and os.path.exists(pfad):
    D = pd.read_csv(pfad, sep=";", parse_dates=["t", "mon"])
    fx = 0
    geprueft = 0
    for r in D.sample(min(60, len(D)), random_state=32).itertuples():
        i0 = POS[r.t] + 1
        if gK.startswith("w "):
            w = int(gK.split()[1]) / 100
        elif gK.startswith("k "):                                   # Schwankungseinheiten: sigma der 30 T bis zum Signaltag, eigene Rechnung
            sig = np.log(pd.Series(K[r.sym].values[i0 - 31:i0])).diff().std(ddof=0) * np.sqrt(30)
            w = min(0.9, float(gK.split()[1].replace(",", ".")) * sig)
        else:
            break
        x = pd.Series(K[r.sym].values[i0:i0 + 182])                # Tag 181 nur als Verkaufstag nach Ausloesung an Tag 180 (wie die Messung)
        hoch = x[:181].cummax()
        x181 = x[:181]
        unter = np.where((x181.values < np.maximum((1 - w) * hoch, 0.5 * x.iloc[0]).values) & (np.arange(len(x181)) > 0))[0]
        unter = [u for u in unter if u + 1 < len(x) and not np.isnan(x.iloc[u + 1])]
        j = unter[0] + 1 if unter else 180
        if x[:181].isna().any():
            continue
        d = x.iloc[j] / x.iloc[0] - x.iloc[180] / x.iloc[0]
        fx += abs(d - r.d) > 1e-9
        geprueft += 1
        if geprueft >= 40:
            break
    pruefe("F4", fx == 0 and geprueft >= 30, "K %s: %d Anker ohne Luecke, Abweichungen %d" % (gK, geprueft, fx))
    k = D.groupby("mon").d.mean().mean()
    m = re.search(r"URTEIL ab 2024 .*?Korb\s+([+-]\d+\.\d+) Pp", K_TXT)
    pruefe("F5", m and abs(100 * k - float(m.group(1))) < 0.006, "K Korb neu %+.3f Pp · Ausgabe %s" % (100 * k, m.group(1) if m else None))
    bad = 0
    for r in D.sample(20, random_state=33).itertuples():
        i = POS[r.t]
        rel = K[r.sym].values / BTCV
        tief = np.nanmin(rel[i - 30:i + 1])
        frueher = D[(D.sym == r.sym) & (D.t < r.t) & (D.t >= r.t - pd.Timedelta(days=30))]
        bad += not (rel[i] >= 1.3 * tief) or len(frueher) > 0
    pruefe("F7", bad == 0, "K 20 Einstiege: Bedingung und Sperre, Verstoesse %d" % bad)

pos_u = [m.start() for m in re.finditer("URTEIL ab 2024", TXT)]
pos_d = [m.start() for m in re.finditer("DOSIS ab 2024", TXT)]
reihe = all(any(u < d for u in pos_u) for d in pos_d) and TXT.index("DOSIS ab 2024", TXT.index("ROLLE L")) > TXT.index("ROLLE L")
t0 = re.search(r"Ausbrecher Median ([+-]\d+\.\d) %.*?alle ([+-]\d+\.\d) %", TXT)
t1 = re.search(r"B5 X2 mit wl_messung.b5: E2 ([+-]\d+\.\d) % · E3 ([+-]\d+\.\d) %.*?gleich an (\d+) von (\d+)", TXT)
pruefe("F8", reihe and t0 and t1 and abs(float(t0.group(1)) - 39.2) <= 1 and abs(float(t0.group(2)) + 23.9) <= 1 and t1.group(3) == t1.group(4),
       "Urteil vor Dosis; Teil 0 %s / %s" % (t0.groups() if t0 else None, t1.groups() if t1 else None))
print("\n%d von %d gleich" % (ok, n))
