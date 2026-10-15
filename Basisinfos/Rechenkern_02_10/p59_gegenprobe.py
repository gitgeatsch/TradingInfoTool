"""P59 GEGENPROBE: dieselben Kennzahlen wie p59_termin_vorpruefung.py auf einem ANDEREN Rechenweg (15.10.2026).

    python Basisinfos/Rechenkern_02_10/p59_gegenprobe.py > Basisinfos/Rechenkern_02_10/p59_gegenprobe.txt

Anders gerechnet: Zeitzonen ueber pandas (tz_localize/tz_convert) statt zoneinfo, Zeitstempel statt Stundenindex, Fenster je
Einstieg ueber eine Schleife mit Zeitvergleich statt searchsorted, BTC-Bewegung aus dem Datenbankstring statt Index-Rechnung.
Nur lesend. Prueft: (1) Umrechnung Sommer/Winterzeit an Stichtagen, (2) Zahl der Einstiege im Fenster, (3) B24/A24/D24 im und
ausserhalb des Fensters, (4) BTC |2 h| am Termin je Art.
"""
import json
import os
import sqlite3
import sys

import numpy as np
import pandas as pd

HIER = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.dirname(os.path.dirname(HIER))
os.chdir(PROJ)
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, HIER)
import p59_termin_vorpruefung as V  # noqa: E402  (laedt nur Konstanten - der Hauptteil laeuft beim Import mit, Ausgabe verworfen)

ok = []


def pruef(name, bed, info=""):
    ok.append(bool(bed))
    print("  %s %s%s" % ("✔" if bed else "⛔", name, " - " + info if info else ""))


T = json.load(open(os.path.join("data", "_termine", "termine.json"), encoding="utf-8"))


def utc(tag, uhr):
    return pd.Timestamp("%s %s" % (tag, uhr)).tz_localize("America/New_York").tz_convert("UTC").tz_localize(None)


ZEIT = ([utc(z["tag"], "08:30") for z in T["cpi"] if z["tag"] not in V.AUS["cpi"]]
        + [utc(z["tag"], "08:30") for z in T["nfp"] if z["tag"] not in V.AUS["nfp"]] + [utc(d, "14:00") for d in V.FOMC])
ART = ["cpi"] * (len(T["cpi"]) - 1) + ["nfp"] * (len(T["nfp"]) - 2) + ["fomc"] * len(V.FOMC)
print("P59 GEGENPROBE\n")
pruef("Stichtag CPI 2024-03-12 (Sommerzeit seit 10.03.) -> 12:30 UTC", utc("2024-03-12", "08:30") == pd.Timestamp("2024-03-12 12:30"))
pruef("Stichtag CPI 2024-02-13 (Winterzeit) -> 13:30 UTC", utc("2024-02-13", "08:30") == pd.Timestamp("2024-02-13 13:30"))
pruef("Stichtag FOMC 2024-11-07 (Winterzeit seit 03.11.) -> 19:00 UTC", utc("2024-11-07", "14:00") == pd.Timestamp("2024-11-07 19:00"))
v_std = sorted(h for a in V.TERM for h in V.TERM[a])
g_std = sorted(int((t.floor("h") - pd.Timestamp("2020-01-01")) / pd.Timedelta(hours=1)) for t in ZEIT)
pruef("Terminstunden beider Wege gleich", v_std == g_std, "%d Termine" % len(g_std))

E = pd.read_csv(os.path.join("data", "_vergleich", "kern48jbz_einstiege_bestand.csv"), sep=";")
anker = pd.Timestamp("2020-01-01") + pd.to_timedelta(E.stunde, unit="h")
zs = np.array(sorted(t.floor("h") for t in ZEIT), dtype="datetime64[ns]")
drin = np.zeros(len(E), bool)
for i, a in enumerate(anker.values):
    # Barrierenfenster: Balken Anker+1 h bis Anker+24 h (E2.ergebnisse: s = 1..24)
    drin[i] = bool(((zs >= a + np.timedelta64(1, "h")) & (zs <= a + np.timedelta64(24, "h"))).any())
pruef("Einstiege im Fenster gleich", drin.sum() == V.ECHT.sum(), "Gegenprobe %d · Vorpruefung %d" % (drin.sum(), V.ECHT.sum()))
for name, y in (("B24", (E.t_d <= 24) & (E.t_d <= E.t_u)), ("A24", (E.t_u <= 24) & (E.t_u < E.t_d)), ("D24", E.t_d <= 24)):
    y = y.values
    d = y[drin].mean() - y[~drin].mean()
    dv = V.diff(V.ECHT, {"B24": V.B24, "A24": V.A24, "D24": V.D24}[name])
    pruef("%s Unterschied gleich" % name, abs(d - dv) < 1e-12, "%+.2f Pp" % (100 * d))

c = sqlite3.connect("file:data/stundenkurse.db?mode=ro", uri=True)
k = pd.read_sql("select stunde, close from stundenkurse where symbol='BTC'", c, index_col="stunde")
c.close()
k.index = pd.to_datetime(k.index)
for art in ("cpi", "nfp", "fomc"):
    w = []
    for t, a in zip(ZEIT, ART):
        if a != art:
            continue
        h = t.floor("h")
        vor, nach = h - pd.Timedelta(hours=1), h + pd.Timedelta(hours=1)
        if vor in k.index and nach in k.index:
            w.append(abs(np.log(k.close[nach] / k.close[vor])))
    hs = [h for h in V.TERM[art] if V.H0 < h < V.H1 - 2]
    wv = np.nanmean([V.bew2(h) for h in hs])
    pruef("BTC |2 h| %s gleich" % art, abs(np.mean(w) - wv) < 1e-9, "%.3f %% · n %d" % (100 * np.mean(w), len(w)))
print("\n%d von %d bestanden" % (sum(ok), len(ok)))
