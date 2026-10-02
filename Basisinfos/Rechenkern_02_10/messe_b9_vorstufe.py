"""B-9 (S7-2, 02.10.2026, Auskunft fuer S7-4): wie oft weicht die VORLAEUFIGE Hebelstufe (ATR der Signalstunde, sofort bekannt)
von der ENDGUELTIGEN (ATR der Einstiegsstunde, eine Stunde spaeter, wie die Messung) ab? Ueber alle 10.732 Einstiege der
Betriebsreferenz, ATR-Modelle in Betriebsform (B-10). Nur lesend.
"""
import os
import sys

import numpy as np
import pandas as pd

HIER = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, HIER)
os.chdir(HIER)
sys.stdout.reconfigure(encoding="utf-8")
import agent.regel0_rechnung as RK                                 # noqa: E402
import messe_k1_schritt2b_kombination as K2                        # noqa: E402

zus = RK.zusatz_aus_gruppe("data/_vergleich/kern48jbz_gruppe_bestand.csv")
reihen = RK.lade_reihen(RK.DATEN_VORGABE, zus)
ein = pd.read_csv("data/_vergleich/kern48jbz_einstiege_bestand.csv", sep=";")
X = RK.hebel_anker(RK.DATEN_VORGABE, reihen, set(zus))
M = {}
for (j, mo) in [(j, m) for j in (2024, 2025, 2026) for m in (1, 4, 7, 10) if (j, m) <= (2026, 7)]:
    M.update(RK.hebel_modelle(X, [(j, mo)], bis_stunde=K2._h(pd.Timestamp(j, mo, 1).to_pydatetime())))
atr = RK.atr_je_stunde(reihen)
mon = RK.monat_von(ein.stunde.to_numpy().astype(np.int64))
mon = np.where(mon <= 2026 * 12 + 7, mon, -1)
a_e = np.array([atr.get(s, {}).get(int(h), np.nan) for s, h in zip(ein.symbol, ein.stunde)])
a_s = np.array([atr.get(s, {}).get(int(h) - 1, np.nan) for s, h in zip(ein.symbol, ein.stunde)])
_P, Le = RK.hebelstufe(a_e, mon, M)
_P, Lv = RK.hebelstufe(a_s, mon, M)
t = pd.crosstab(pd.Series(Lv, name="vorlaeufig"), pd.Series(Le, name="endgueltig"))
print("B-9 vorlaeufige (ATR Signalstunde) gegen endgueltige Stufe (ATR Einstiegsstunde), %d Einstiege, Betriebsform B-10" % len(ein))
print(t.to_string())
gl = float(np.mean(Lv == Le))
hoeher = int((Lv > Le).sum()); tiefer = int((Lv < Le).sum())
print("gleich %.2f %% · vorlaeufig HOEHER als endgueltig %d (Risiko: zu viel Hebel) · tiefer %d" % (100 * gl, hoeher, tiefer))
print("SCHLUSS: vollstaendig")
