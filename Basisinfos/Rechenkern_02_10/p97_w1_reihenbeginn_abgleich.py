"""P97 W-1 ABGLEICH REIHENBEGINN (E-156, K-R0-ST0): Hat die REGEL0 am NB denselben Reihenbeginn je Asset wie die Desktop-Referenz?

    python -X utf8 Basisinfos/Rechenkern_02_10/p97_w1_reihenbeginn_abgleich.py            # Desktop-Seite rechnen (einmal, ~Minuten)
    python -X utf8 Basisinfos/Rechenkern_02_10/p97_w1_reihenbeginn_abgleich.py --nb       # gegen den Abschnitt regel0_reihenbeginn der NB-Diagnose

Desktop: erster Anker je Asset genau wie der Monatsjob (`regel0_rechnung.anker(lade_reihen_iter(...))`, Zusatz-Assets wie
`betriebs_zusatz`) -> data/_w1/desktop_erster_anker.json. NB: notebook_diagnose.json im Austauschordner (Kopie, nur gelesen).
Nach E-139 haengt das gemessene Plus an der Reife ab diesem Beginn - ungleich heisst: der NB rechnet eine andere Grundgesamtheit.
Nur lesend (die eigene Ablage data/_w1/ ausgenommen).
"""
import json
import os
import sys
from datetime import datetime, timedelta

HIER = os.path.dirname(os.path.abspath(__file__))
WURZEL = os.path.dirname(os.path.dirname(HIER))
sys.path.insert(0, WURZEL)
os.chdir(WURZEL)
sys.stdout.reconfigure(encoding="utf-8")
import numpy as np  # noqa: E402

ABLAGE = os.path.join("data", "_w1", "desktop_erster_anker.json")
NB_DIAGNOSE = os.path.join("K:" + os.sep, "My Drive", "Claude_Austauschordner", "Notebook_Analysedaten", "notebook_diagnose.json")
B0 = datetime(2020, 1, 1)


def desktop():
    from agent import regel0_rechnung as R
    zusatz = R.betriebs_zusatz("data")
    A = R.anker(R.lade_reihen_iter("data", zusatz), zukunft_bekannt=False)
    erster = {A["syms"][int(si)]: (B0 + timedelta(hours=int(A["STD"][A["SYM"] == si].min()))).strftime("%Y-%m-%d %H:%M")
              for si in np.unique(A["SYM"])}
    os.makedirs(os.path.dirname(ABLAGE), exist_ok=True)
    json.dump({"berechnet": datetime.now().strftime("%Y-%m-%d %H:%M"), "je_symbol": erster}, open(ABLAGE, "w", encoding="utf-8"), indent=0)
    ab = sorted(s for s, t in erster.items() if t >= "2023-09-01")
    print("Desktop: %d Assets · Reihenbeginn ab 2023-09: %d (%s ...) -> %s" % (len(erster), len(ab), ", ".join(ab[:12]), ABLAGE))


def nb():
    d = json.load(open(ABLAGE, encoding="utf-8"))["je_symbol"]
    diag = json.load(open(NB_DIAGNOSE, encoding="utf-8"))
    nbx = diag.get("regel0_reihenbeginn")
    if not isinstance(nbx, dict) or "je_symbol" not in nbx:
        print("NB-Diagnose ohne Abschnitt regel0_reihenbeginn (Pull von W-1 noch nicht am NB?): %s" % (nbx if nbx else "fehlt"))
        return 1
    n = nbx["je_symbol"]
    gem = sorted(set(d) & set(n))
    gleich = [s for s in gem if d[s] == n[s]]
    anders = [(s, d[s], n[s]) for s in gem if d[s] != n[s]]
    print("NB-Paket %s (%s): %d Assets · Desktop %d · gemeinsam %d · gleich %d · ANDERS %d · nur NB %d · nur Desktop %d" % (
        nbx.get("datei"), nbx.get("monat"), len(n), len(d), len(gem), len(gleich), len(anders), len(set(n) - set(d)), len(set(d) - set(n))))
    for s, a, b in anders[:40]:
        print("  %-10s Desktop %s · NB %s" % (s, a, b))
    print("-> %s" % ("GLEICH (K-R0-ST0 erfuellt)" if not anders and not (set(n) ^ set(d)) else "ABWEICHUNG - Grundgesamtheit pruefen"))
    return 0


if __name__ == "__main__":
    raise SystemExit(nb() if "--nb" in sys.argv else desktop())
