"""G7 Stufe 3 — die VORLÄUFIGE Hebelstufe je Einstieg der Menge b (Voranalyse Stufe 3 S3-5, Ü8).

Live geht die REGEL0-Mail (und damit der LLM-Aufruf) beim SIGNAL hinaus, mit der Stufe aus der ATR der SIGNALstunde (`stufe_vorlaeufig`,
regel0_mail.py); die endgültige Stufe aus der ATR der Einstiegsstunde kommt eine Stunde später (Korrektur in ≈ 1,6 %, B-9). Die
Mengendatei trägt die ENDGÜLTIGE Stufe (g7_regel0_betrieb.teil_d). Dem finalen LLM darf im Rückspiel nur gezeigt werden, was live zum
Signal bekannt ist → hier die vorläufige, mit DERSELBEN Rechnung (teil_d), nur eine Stunde früher.

GEGENPROBE zuerst: teil_d mit der Einstiegsstunde muss die Stufe der Mengendatei genau treffen — sonst gilt die Rechnung nicht.

Nur lesend (Kurs-Arbeitskopie, NB-Paket). Schreibt ``data/_g7/regel0/stufe3_stufe_vorlaeufig.csv`` und die .txt hierneben.

    python g7_stufe3_stufe_vorlaeufig.py
"""
import os
import sys
import time

import numpy as np
import pandas as pd

HIER = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.dirname(os.path.dirname(HIER))
sys.path.insert(0, HIER)
sys.path.insert(0, PROJ)
import g7_regel0_betrieb as B                                         # noqa: E402

AUS = os.path.join(PROJ, "data", "_g7", "regel0", "stufe3_stufe_vorlaeufig.csv")


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:  # noqa: BLE001
        pass
    t0 = time.time()
    M = pd.read_csv(os.path.join(HIER, "g7_stufe3_menge_b.csv"), sep=";")
    E = M[["symbol", "stunde", "signalstunde", "stufe"]].rename(columns={"stufe": "stufe_menge"}).reset_index(drop=True)
    E["h"] = [B._h(s) for s in E.stunde]
    assert (E.h - 1 == [B._h(s) for s in E.signalstunde]).all(), "Signalstunde ≠ Einstieg − 1 h"
    zus = B.RK.betriebs_zusatz(B.KOPIE)
    mb = {r[0] for r in B.RK._ro(os.path.join(B.KOPIE, "stundenkurse.db")).execute(
        "SELECT symbol FROM stundenkurse GROUP BY symbol HAVING COUNT(*) > 2000")}
    End = B.teil_d(E.copy(), zus, mb)
    gleich = int((End.stufe.to_numpy() == E.stufe_menge.to_numpy()).sum())
    Vor = B.teil_d(E.assign(h=E.h - 1), zus, mb)
    E["stufe_vorlaeufig"] = Vor.stufe.to_numpy()
    E["stufe_end_nachgerechnet"] = End.stufe.to_numpy()
    ab = E.stufe_vorlaeufig != E.stufe_menge
    zeilen = [
        "G7 STUFE 3 — vorläufige Hebelstufe (ATR der Signalstunde) · %s" % time.strftime("%Y-%m-%d %H:%M"),
        "Einstiege %d" % len(E),
        "GEGENPROBE endgültige Stufe nachgerechnet = Mengendatei: %d von %d %s" % (gleich, len(E), "✔" if gleich == len(E) else "⚠ ABWEICHUNG"),
        "vorläufig ≠ endgültig: %d (%.1f %%) · Übergänge %s" % (int(ab.sum()), 100 * ab.mean(),
                                                               dict(pd.crosstab(E.stufe_vorlaeufig, E.stufe_menge).stack().loc[lambda s: s > 0])),
        "vorläufig 0 (kein Handel zum Signal), endgültig > 0: %d" % int(((E.stufe_vorlaeufig == 0) & (E.stufe_menge > 0)).sum()),
        "Rechenzeit %.0f s" % (time.time() - t0)]
    for z in zeilen:
        print(z, flush=True)
    E[["symbol", "stunde", "stufe_vorlaeufig", "stufe_menge"]].to_csv(AUS, sep=";", index=False, lineterminator="\n")
    with open(os.path.join(HIER, "g7_stufe3_stufe_vorlaeufig.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(zeilen) + "\n")


if __name__ == "__main__":
    main()
