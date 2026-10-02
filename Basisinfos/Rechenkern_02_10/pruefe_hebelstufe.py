"""Gegenpruefung der Hebelstufe im REGEL0.1-Rechenkern (S7-2 Schritt 3, 02.10.2026) - nur lesend.

1  R-R11-2   je Einstieg P(Liquidation binnen 24 h) fuer 2x/3x/5x und die gewaehlte Stufe zeilengleich zur Referenz aus B-5
             (data/_vergleich/regel01_stufen_bestand.csv, messe_k6_hebelstufe.py --spur-stufen), Toleranz 1e-12
2  Gegenprobe  mit Grenze 0,019 statt 0,02 muessen Stufen abweichen
3  B-10       Training wie im Betrieb (nur Anker, deren 120-h-Fenster zum Quartalsbeginn abgeschlossen ist): wie viele Stufen
             aendern sich? (Auskunft, vorab: >= 99 % gleiche Stufen gelten als unerheblich, sonst vorlegen)
4  Abdeckung  der Betrieb bewertet JEDEN Einstieg (die Messung nur die mit vollem Zukunftsfenster) - wie viele kommen dazu?
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

ergebnis = []


def pruef(name, ok, info=""):
    ergebnis.append(bool(ok))
    print("  %s %s%s" % ("✔" if ok else "⛔", name, (" - " + info) if info else ""), flush=True)


t0 = time.time()
zus = RK.zusatz_aus_gruppe("data/_vergleich/kern48jbz_gruppe_bestand.csv")
reihen = RK.lade_reihen(RK.DATEN_VORGABE, zus)
ein = pd.read_csv("data/_vergleich/kern48jbz_einstiege_bestand.csv", sep=";")
ref = pd.read_csv("data/_vergleich/regel01_stufen_bestand.csv", sep=";")
X = RK.hebel_anker(RK.DATEN_VORGABE, reihen, set(zus))
QU = [(j, m) for j in (2024, 2025, 2026) for m in (1, 4, 7, 10) if (j, m) <= (2026, 7)]
M = RK.hebel_modelle(X, QU)
print("Hebel-Anker %d, Modelle %d (Quartal x Stufe) in %.0f s" % (len(X["std"]), len(M), time.time() - t0), flush=True)
atr = RK.atr_je_stunde(reihen)
a_e = np.array([atr.get(s, {}).get(int(h), np.nan) for s, h in zip(ein.symbol, ein.stunde)])
mon = RK.monat_von(ein.stunde.to_numpy().astype(np.int64))
mon = np.where(mon <= 2026 * 12 + 7, mon, -1)          # wie die Messung: Vorhersage nur bis 2026-08
P, L = RK.hebelstufe(a_e, mon, M)
rk = pd.DataFrame({"symbol": ein.symbol, "std": ein.stunde, "p2": P[2], "p3": P[3], "p5": P[5], "stufe": L})

print("1) R-R11-2 gegen die Referenz aus B-5")
m_ = ref.merge(rk, on=["symbol", "std"], how="left", suffixes=("_ref", "_rk"))
dp = max(float(np.nanmax(np.abs(m_["p%d_ref" % k] - m_["p%d_rk" % k]))) for k in (2, 3, 5))
nan_gleich = all(((m_["p%d_ref" % k].isna()) == (m_["p%d_rk" % k].isna())).all() for k in (2, 3, 5))
pruef("alle %d Referenzzeilen im Rechenkern vorhanden" % len(ref), m_["stufe_rk"].notna().all())
pruef("P(Liquidation) je Stufe gleich (Toleranz 1e-12), fehlende Vorhersagen an denselben Stellen", dp <= 1e-12 and nan_gleich, "max |Abw| %.1e" % dp)
pruef("gewaehlte Stufe zeilengleich", (m_["stufe_ref"] == m_["stufe_rk"]).all(),
      "abweichend %d · Stufen Referenz %s" % (int((m_["stufe_ref"] != m_["stufe_rk"]).sum()), ref.stufe.value_counts().sort_index().to_dict()))

print("2) Gegenprobe Grenze 0,019")
alt = RK.GRENZE
RK.GRENZE = 0.019
_P, L2 = RK.hebelstufe(a_e, mon, M)
RK.GRENZE = alt
g2 = rk.assign(st2=L2).merge(ref, on=["symbol", "std"])
pruef("die Pruefung schlaegt an", int((g2.st2 != g2.stufe_y).sum()) > 0, "%d Stufen anders" % int((g2.st2 != g2.stufe_y).sum()))

print("3) B-10: Training wie im Betrieb (nur abgeschlossene 120-h-Fenster zum Quartalsbeginn)")
MB = {}
for (j, mo) in QU:
    MB.update(RK.hebel_modelle(X, [(j, mo)], bis_stunde=K2._h(pd.Timestamp(j, mo, 1).to_pydatetime())))
PB, LB = RK.hebelstufe(a_e, mon, MB)
gl = float(np.mean(LB == L))
print("    gleiche Stufe %.2f %% · anders %d von %d · max |dP| %.2e" % (100 * gl, int((LB != L).sum()), len(L),
      max(float(np.nanmax(np.abs(PB[k] - P[k]))) for k in (2, 3, 5))))
print("    Stufen Messung %s · Betrieb %s" % (pd.Series(L).value_counts().sort_index().to_dict(), pd.Series(LB).value_counts().sort_index().to_dict()))
pruef("B-10 unerheblich (vorab: >= 99 % gleiche Stufen)", gl >= 0.99, "%.2f %%" % (100 * gl))

print("4) Abdeckung: Einstiege mit Stufe")
print("    Messung bewertet %d von %d Einstiegen (volles Zukunftsfenster) · Rechenkern %d (ATR und Modell vorhanden)" % (
    len(ref), len(ein), int(np.isfinite(P[5]).sum())))
print("SCHLUSS: %s (%d von %d) · %.0f s" % ("✔ bestanden" if all(ergebnis) else "⛔ NICHT bestanden", sum(ergebnis), len(ergebnis), time.time() - t0))
