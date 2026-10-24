"""P80 GEGENPROBE zu F-1 Fassung 2 / E-136 (24.10.2026): die beiden Befunde auf einem zweiten Weg.

    python -X utf8 Basisinfos/Rechenkern_02_10/p80_gegenprobe_historie.py

G1  Lauf A ueber die KOMMANDOZEILE des Erzeugers (python -m agent.regel0_rechnung --nachrechnung --ordner data/_hist) ist zeilengleich
    zu data/_hist/einstiege_A.csv (p78 rief die Funktionen direkt).
G2  Netto je Handel unabhaengig von p79/p71: je Einstieg zwei SQL-Abfragen ueber den Stundentext (Schluss t und t+24 h), ohne Raster.
    Referenz, Lauf A, Lauf B; dazu die Zerlegung gemeinsam / nur A / nur Referenz.
G3  Die Stunden ueber der Schwelle 2021 (Lauf B ohne Signal) liegen an Datenluecken: je Asset die Stunde vor dem ersten Treffer eines
    Laufs fehlt in den Kursen oder der Lauf beginnt nach einer Luecke binnen 48 h.
"""
import os
import sqlite3
import subprocess
import sys
from datetime import datetime, timedelta

import pandas as pd

WURZEL = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(WURZEL)
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:  # noqa: BLE001
    pass
H = os.path.join("data", "_hist")
REF = os.path.join("data", "_vergleich", "kern48jbz_einstiege_bestand.csv")
B0 = datetime(2020, 1, 1)
KOSTEN = 0.0048


def g1():
    ziel = os.path.join(H, "einstiege_A_cli.csv")
    r = subprocess.run([sys.executable, "-X", "utf8", "-m", "agent.regel0_rechnung", "--nachrechnung", "--ordner", H, "--zusatz-aus",
                        os.path.join("data", "_vergleich", "kern48jbz_gruppe_bestand.csv"), "--ziel", ziel], capture_output=True, text=True)
    print("   " + (r.stdout.strip().splitlines() or ["(keine Ausgabe)"])[0])
    a = pd.read_csv(ziel, sep=";", dtype=str).sort_values(["symbol", "stunde"]).reset_index(drop=True)
    b = pd.read_csv(os.path.join(H, "einstiege_A.csv"), sep=";", dtype=str).sort_values(["symbol", "stunde"]).reset_index(drop=True)
    ok = a.shape == b.shape and bool((a.fillna("") == b.fillna("")).all().all())
    print("G1 Lauf A Kommandozeile gegen p78: %s (%d / %d Zeilen)" % ("ZEILENGLEICH" if ok else "ABWEICHUNG", len(a), len(b)))
    return ok


def netto(E, cons):
    out = []
    for s, st in zip(E.symbol, E.stunde):
        t = B0 + timedelta(hours=int(st))
        a = t.strftime("%Y-%m-%d %H:%M")
        e = (t + timedelta(hours=24)).strftime("%Y-%m-%d %H:%M")
        ca = ce = None
        for c in cons:
            ca = ca or (c.execute("SELECT close FROM stundenkurse WHERE symbol=? AND stunde=?", (s, a)).fetchone() or [None])[0]
            ce = ce or (c.execute("SELECT close FROM stundenkurse WHERE symbol=? AND stunde=?", (s, e)).fetchone() or [None])[0]
        if ca and ce:
            out.append(ce / ca - 1 - KOSTEN)
    return pd.Series(out, dtype=float)


def g2():
    cons = [sqlite3.connect("file:%s/%s?mode=ro" % (H.replace("\\", "/"), d), uri=True) for d in ("stundenkurse.db", "stundenkurse_alle.db")]
    a = pd.read_csv(os.path.join(H, "einstiege_A.csv"), sep=";")
    b = pd.read_csv(REF, sep=";")
    bb = pd.read_csv(os.path.join(H, "einstiege_B.csv"), sep=";")
    for name, E in (("Referenz", b), ("Lauf A", a), ("Lauf B", bb)):
        x = netto(E, cons)
        print("G2 %-9s %6d Handel netto je Handel %+.3f %%" % (name, len(x), 100 * x.mean()))
    m = a.merge(b, on=["symbol", "stunde"], how="outer", indicator=True)
    for k, n in (("both", "gemeinsam"), ("left_only", "nur Lauf A"), ("right_only", "nur Referenz")):
        x = netto(m[m._merge == k], cons)
        print("G2 %-12s %6d Handel netto je Handel %+.3f %%" % (n, len(x), 100 * x.mean()))


def g3():
    sys.path.insert(0, WURZEL)
    sys.path.insert(0, os.path.join(WURZEL, "Basisinfos", "Rechenkern_02_10"))
    import numpy as np
    import p78_regel0_lauf_ab as P
    R0 = P.R0
    zus = R0.zusatz_aus_gruppe(P.GRUPPE)
    A = R0.anker(R0.lade_reihen(H, zus), zukunft_bekannt=True)
    ns = P.rechne_lang()
    ns["_AB_MON"], ns["_LERN"] = 2020 * 12 + 6, datetime(2020, 6, 1)
    R = ns["rechne"](A, set(zus), P.MONATE_B, jahre=(2020, 2021, 2022, 2023))
    J, VH, SYM, STD = R["JAHR"], R["VH"], R["SYM"], R["STD"]
    laeufe = luecke = 0
    tage = set()
    for u in np.unique(SYM[(J == 2021) & (VH >= 0.035)]):
        st = np.sort(STD[(J == 2021) & (SYM == u) & (VH >= 0.035)])
        anf = st[np.r_[True, np.diff(st) > 1]]
        alle = np.sort(STD[SYM == u])
        for t in anf:
            laeufe += 1
            vor = alle[(alle < t) & (alle >= t - 48)]
            luecke += int(len(vor) < 48)
            tage.add(R0._stunde_txt(int(t))[:10])
    print("G3 2021: %d Laeufe ueber der Schwelle, davon nach einer Ankerluecke binnen 48 h: %d · Tage: %s"
          % (laeufe, luecke, ", ".join(sorted(tage))))
    return laeufe == luecke


def main():
    print("P80 GEGENPROBE F-1 Fassung 2 / E-136")
    ok1 = g1()
    g2()
    ok3 = g3()
    print("ERGEBNIS: G1 %s · G3 %s (G2 Werte gegen p79 vergleichen)" % ("ok" if ok1 else "NICHT OK", "ok" if ok3 else "NICHT OK"))


if __name__ == "__main__":
    main()
