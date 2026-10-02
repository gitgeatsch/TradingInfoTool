"""Gegenpruefung des REGEL0.1-Rechenkerns (S7-2, 02.10.2026) - nur lesend, schreibt nur in diesen Ordner.

1  R-R11-1   Nachrechnung 2024-01..2026-08 zeilengleich zur Betriebsreferenz kern48jbz_einstiege_bestand.csv
2  Gegenprobe  Schwelle 0,034 statt 0,035 MUSS abweichen
3  Live-Probe  an 20 vergangenen Zeitpunkten T nur die Kerzen BIS T-1 (keine Zukunft, Ankermaske des Betriebs):
              die Signale zur juengsten Stunde T-1 muessen genau die Einstiege der Referenz zur Stunde T sein, und v-dach
              zur Stunde T-1 muss dem der Nachrechnung gleichen (Modelle aus der Nachrechnung, Training ist eigene Pruefung)

    python Basisinfos/Rechenkern_02_10/pruefe_rechenkern.py
"""
import os
import sys
import time

import numpy as np
import pandas as pd

HIER = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, HIER)
os.chdir(HIER)
sys.stdout.reconfigure(encoding="utf-8")
import agent.regel0_rechnung as RK                                 # noqa: E402
import messe_k1_schritt2b_kombination as K2                        # noqa: E402

REF = "data/_vergleich/kern48jbz_einstiege_bestand.csv"
zus = RK.zusatz_aus_gruppe("data/_vergleich/kern48jbz_gruppe_bestand.csv")
ref = pd.read_csv(REF, sep=";")
ergebnis = []


def pruef(name, ok, info=""):
    ergebnis.append(bool(ok))
    print("  %s %s%s" % ("✔" if ok else "⛔", name, (" - " + info) if info else ""), flush=True)


t0 = time.time()
reihen = RK.lade_reihen(RK.DATEN_VORGABE, zus)
A = RK.anker(reihen, zukunft_bekannt=True)
R = RK.rechne(A, set(zus), K2.ROLL_MONATE)
print("Nachrechnung in %.0f s" % (time.time() - t0))


def als_df(R_, idx):
    return pd.DataFrame({"symbol": [R_["syms"][int(R_["SYM"][i])] for i in idx], "stunde": R_["STD"][idx].astype(int)})


print("1) R-R11-1 Nachrechnung")
nr = als_df(R, R["einstiege"])
pruef("zeilengleich zur Betriebsreferenz (symbol, stunde)", nr.equals(ref[["symbol", "stunde"]]), "%d / %d" % (len(nr), len(ref)))

print("2) Gegenprobe Schwelle 0,034")
R2 = RK.rechne(A, set(zus), K2.ROLL_MONATE, modelle=R["modelle"], schwelle=0.034)
d2 = set(zip(*als_df(R2, R2["einstiege"]).values.T)) ^ set(zip(ref.symbol, ref.stunde))
pruef("die Pruefung schlaegt an (andere Einstiege)", len(d2) > 0, "%d abweichende Einstiege" % len(d2))

print("3) Live-Probe: nur Kerzen bis T-1, Ankermaske ohne Zukunft")
rng = np.random.default_rng(20261002)
pos = list(rng.choice(ref.stunde.unique(), 12, replace=False))
neg = list(rng.integers(K2._h(pd.Timestamp(2024, 3, 1).to_pydatetime()), K2._h(pd.Timestamp(2026, 8, 25).to_pydatetime()), 8))
basis = pd.Timestamp(2020, 1, 1)
vh_ref = {(R["syms"][int(R["SYM"][i])], int(R["STD"][i])): R["VH"][i] for i in range(len(R["SYM"]))}
gleich_sig, max_dvh, n_vh = 0, 0.0, 0
for T in sorted(int(x) for x in pos + neg):
    grenze = (basis + pd.Timedelta(hours=T - 1)).strftime("%Y-%m-%d %H:%M")
    rT = [(s, [r for r in rows if r[0] <= grenze]) for s, rows in reihen]
    AT = RK.anker(rT, zukunft_bekannt=False)
    mon = int(RK.monat_von(np.array([T - 1]))[0])
    monate = [((m_ // 12), (m_ % 12) + 1) for m_ in (mon - 1, mon)]
    RT = RK.rechne(AT, set(zus), monate, modelle=R["modelle"])
    jetzt = RT["signale"][RT["STD"][RT["signale"]] == T - 1]
    live = sorted(RT["syms"][int(RT["SYM"][i])] for i in jetzt)
    soll = sorted(ref.symbol[ref.stunde == T])
    letzte = np.flatnonzero(RT["STD"] == T - 1)
    dv = [abs(RT["VH"][i] - vh_ref[(RT["syms"][int(RT["SYM"][i])], T - 1)]) for i in letzte
          if (RT["syms"][int(RT["SYM"][i])], T - 1) in vh_ref and np.isfinite(RT["VH"][i])]
    max_dvh = max([max_dvh] + dv); n_vh += len(dv)
    gleich_sig += live == soll
    print("    T %s: live %s · Referenz %s · v-dach %d Assets, max |Abw| %.1e%s" % (
        (basis + pd.Timedelta(hours=T)).strftime("%Y-%m-%d %H:00"), live or "-", soll or "-", len(dv), max(dv) if dv else 0.0,
        "" if live == soll else "  ⛔"), flush=True)
pruef("Live-Signale = Referenz-Einstiege an allen 20 Zeitpunkten", gleich_sig == 20, "%d von 20" % gleich_sig)
pruef("v-dach zur juengsten Stunde gleich der Nachrechnung (Toleranz 1e-9)", max_dvh <= 1e-9, "%d Werte, max %.1e" % (n_vh, max_dvh))
print("SCHLUSS: %s (%d von %d) · %.0f s" % ("✔ bestanden" if all(ergebnis) else "⛔ NICHT bestanden", sum(ergebnis), len(ergebnis), time.time() - t0))
