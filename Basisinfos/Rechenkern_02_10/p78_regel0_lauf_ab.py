"""P78 REGEL0-NACHRECHNUNG LAUF A + B auf der verlaengerten Historie (23.10.2026, Messplan F-1 Fassung 2, Voranalyse_REGEL0_Historie §6).

    python -X utf8 Basisinfos/Rechenkern_02_10/p78_regel0_lauf_ab.py --probe        R-R11 der Kopie auf data/ (muss zeilengleich sein)
    python -X utf8 Basisinfos/Rechenkern_02_10/p78_regel0_lauf_ab.py                Lauf A + B auf data/_hist

Betriebscode wird NICHT geaendert. Lauf A ruft agent.regel0_rechnung unveraendert auf (lade_reihen, anker, rechne, schreibe_einstiege -
derselbe Weg wie main). Lauf B braucht zwei Konstanten, die in ``rechne`` fest stehen:

    BASIS & (MON >= 2024 * 12)          Schrumpfung nur ab 2024        -> ab 2020-07
    ab = K2._h(datetime(2023, 1, 1))    Lernbeginn der Monatsmodelle   -> 2020-06-01 (wachsendes Fenster ab Datenbeginn)

Dafuer wird der QUELLTEXT von ``rechne`` gelesen, genau diese zwei Stellen ersetzt (je genau einmal, sonst Abbruch) und im
Namensraum des Moduls ausgefuehrt. --probe beweist, dass die Kopie mit den Betriebswerten zeilengleich zur Referenz rechnet.
Schreibt nur data/_hist/einstiege_*.csv und data/_hist/lauf_ab.log.
"""
import inspect
import os
import sys
import time
from datetime import datetime

import numpy as np
import pandas as pd

WURZEL = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(WURZEL)
sys.path.insert(0, WURZEL)
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:  # noqa: BLE001
    pass
import agent.regel0_rechnung as R0  # noqa: E402

K2 = R0.K2
GRUPPE = os.path.join("data", "_vergleich", "kern48jbz_gruppe_bestand.csv")
REFERENZ = os.path.join("data", "_vergleich", "kern48jbz_einstiege_bestand.csv")
ZIEL = os.path.join("data", "_hist")
MONATE_B = [(j, m) for j in range(2020, 2024) for m in range(1, 13) if (j, m) >= (2020, 7)]
ERSATZ = [("BASIS & (MON >= 2024 * 12)", "BASIS & (MON >= _AB_MON)"),
          ("ab = K2._h(datetime(2023, 1, 1))", "ab = K2._h(_LERN)")]


def rechne_lang():
    src = inspect.getsource(R0.rechne)
    for a, b in ERSATZ:
        if src.count(a) != 1:
            raise SystemExit("ABBRUCH: Stelle %r kommt %d-mal vor - rechne() wurde geaendert, Kopie nicht mehr gesichert" % (a, src.count(a)))
        src = src.replace(a, b)
    ns = dict(vars(R0))
    exec(compile(src, "<rechne_lang>", "exec"), ns)  # noqa: S102 - eigener, oben geprueft ersetzter Quelltext des Moduls
    return ns


def gleich(pfad, ref):
    a = pd.read_csv(pfad, sep=";", dtype=str).sort_values(["symbol", "stunde"]).reset_index(drop=True)
    b = pd.read_csv(ref, sep=";", dtype=str).sort_values(["symbol", "stunde"]).reset_index(drop=True)
    return a.shape == b.shape and bool((a.fillna("") == b.fillna("")).all().all()), len(a), len(b)


def main():
    zus = R0.zusatz_aus_gruppe(GRUPPE)
    ns = rechne_lang()
    log = open(os.path.join(ZIEL, "lauf_ab.log"), "a", encoding="utf-8")

    def p(t):
        print(t, flush=True)
        log.write(t + "\n")
    p("== p78 %s %s" % (datetime.now().strftime("%Y-%m-%d %H:%M"), " ".join(sys.argv[1:])))
    if "--probe" in sys.argv:
        A = R0.anker(R0.lade_reihen("data", zus), zukunft_bekannt=True)
        ns["_AB_MON"], ns["_LERN"] = 2024 * 12, datetime(2023, 1, 1)
        R = ns["rechne"](A, set(zus), K2.ROLL_MONATE)
        z = os.path.join(ZIEL, "rr11_kopie.csv")
        R0.schreibe_einstiege(R, z)
        ok, na, nb = gleich(z, REFERENZ)
        p("R-R11 Kopie (Betriebswerte, data/): %s · %d gegen %d Zeilen" % ("ZEILENGLEICH" if ok else "ABWEICHUNG", na, nb))
        return 0 if ok else 1
    t0 = time.time()
    A = R0.anker(R0.lade_reihen(ZIEL, zus), zukunft_bekannt=True)
    p("Anker %d, Assets %d, erste Stunde %s · %.0f s" % (len(A["SYM"]), len(np.unique(A["SYM"])), R0._stunde_txt(int(A["STD"].min())),
                                                       time.time() - t0))
    # Lauf A: Erzeuger unveraendert
    RA = R0.rechne(A, set(zus), K2.ROLL_MONATE)
    ka = R0.schreibe_einstiege(RA, os.path.join(ZIEL, "einstiege_A.csv"))
    p("Lauf A (2024-01..2026-08, Lernbeginn 2023-01): %d Monatsmodelle, %d Einstiege" % (len(RA["modelle"]), ka))
    # Lauf B: Kopie mit Schrumpfung ab 2020-07 und Lernbeginn 2020-06-01
    ns["_AB_MON"], ns["_LERN"] = 2020 * 12 + 6, datetime(2020, 6, 1)
    RB = ns["rechne"](A, set(zus), MONATE_B, jahre=(2020, 2021, 2022, 2023))
    kb = R0.schreibe_einstiege(RB, os.path.join(ZIEL, "einstiege_B.csv"))
    fehlt = [(j, m) for (j, m) in MONATE_B if j * 12 + m - 1 not in RB["modelle"]]
    p("Lauf B (2020-07..2023-12, Lernbeginn 2020-06): %d Monatsmodelle, %d Einstiege · ohne Modell (< 5.000 Treffer): %s" % (
        len(RB["modelle"]), kb, ", ".join("%d-%02d" % x for x in fehlt) or "keiner"))
    eb = pd.read_csv(os.path.join(ZIEL, "einstiege_B.csv"), sep=";")
    p("  Lauf B je Jahr: %s" % eb.groupby("jahr").size().to_dict())
    # Auskunft R-R11 (2): Lauf A gegen die Referenz
    a = pd.read_csv(os.path.join(ZIEL, "einstiege_A.csv"), sep=";")
    b = pd.read_csv(REFERENZ, sep=";")
    m = a.merge(b, on=["symbol", "stunde"], how="outer", indicator=True)
    k = m["_merge"].value_counts().to_dict()
    p("Auskunft Lauf A gegen Referenz: gemeinsam %d, nur A %d, nur Referenz %d · Anteil gleicher Einstiege %.1f %%" % (
        k.get("both", 0), k.get("left_only", 0), k.get("right_only", 0), 100.0 * k.get("both", 0) / max(len(m), 1)))
    log.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
