"""P22b GEGENPROBE mit ECHTEN CoinGecko-Daten (15.10.2026): drei Coins ueber agent.umlauf_zusatz.pflege in eine Wegwerf-Kopie der
Mengendatei, Verwaesserung 90 T gegen die Voranalyse p57 (eigener Abrufweg: hole_umlaufmenge_cg.zerlege direkt). Netz: 3 + 1 Abrufe.

    python Basisinfos/Rechenkern_02_10/p22b_gegenprobe.py
"""
import os
import shutil
import sys
import tempfile

WURZEL = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(WURZEL)
sys.path.insert(0, WURZEL)
import wegwerf  # noqa: E402,F401

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

import agent.umlauf_zusatz as UZ  # noqa: E402
import agent.verwaesserung as VW  # noqa: E402

SOLL = (("SUPRA", "supra", 39.4), ("KAS", "kaspa", 0.7), ("HYPE", "hyperliquid", 0.0))      # p57_p22b_voranalyse.txt, Stand 15.10.2026
T = tempfile.mkdtemp(prefix="p22b_gp_")
U = os.path.join(T, "umlaufmenge_cg.db")
shutil.copy("data/umlaufmenge_cg.db", U)
wl = [type("A", (), {"symbol": s, "coingecko_id": i, "assetklasse": "krypto", "ist_cash_aequivalent": False})() for s, i, _ in SOLL]
e = UZ.pflege(U, wl)
print("Erstabruf echt: %s · Tageswert %d · Fehler %s" % (e["erstabruf"], e["tageswert"], e["fehler"]))
R = UZ.reihen(U)
t = pd.Timestamp("2026-10-15")
gleich = 0
for s, _, soll in SOLL:
    v = VW.wert(R.get(s), t)
    ist = 100 * np.expm1(v) if v is not None else None
    ok = ist is not None and abs(ist - soll) <= 0.15
    gleich += ok
    print("  %-6s Modul %s · Voranalyse p57 %+.1f %% · %s" % (s, ("%+.1f %%" % ist) if ist is not None else "-", soll, "gleich" if ok else "ABWEICHUNG"))
wegwerf.aufraeumen(T)
print("\n%d von %d gleich (Toleranz 0,15 Pp: der laufende Tageswert bewegt sich zwischen zwei Abrufen)" % (gleich, len(SOLL)))
