"""B Teil 0 (Basisinfos/Voranalyse_B_Kern_stabilisieren_01_10.md Abschnitt 1): WO entstehen die Verluste der REGEL0? - NUR AUSKUNFT.

Liest die Spur von ``messe_k6_hebelstufe.py --simulation 24,ohne,0.02 --spur-regel0 <csv>`` (je Handel 2025-26: Symbol, Stunde, Hebelstufe,
Hebelrendite, Kosten, Haltedauer, Liquidation, Spotrendite) und teilt das Hebelkonto (Summe log(1 + 0,01 r), wie die Erfolgsmessung) auf:

    Kosten gegen Verlusthandel   Konto ohne Kosten = Summe log(1 + 0,01 (r + Kosten)); Kostenanteil = Konto - Konto ohne Kosten
    Monatsklasse                 Gegenwind (K_IG < 1) gegen uebrig - aus data/_vergleich/m1_wenig_<menge>.txt (2.697, Modelle vor J)
    Daempfungswahl (nur bestand) knapp (Abstand zur zweitbesten Stufe < 10) gegen deutlich - aus Kern_Short_30_09/m1_1__bestand.txt
    spaeter eingestellt          Symbol in eingestellt_historie.db mit art 'eingestellt' (nur unverzerrt)
    Hebelstufe                   2x / 3x / 5x
    Asset                        die 10 groessten Verlustbringer und der Rest

R-R11: Die Summe aller Handel muss das REGEL0-Konto der Referenz (hebel_neubau.REGEL0) bitgleich treffen (Rundung der Spur < 1e-6).
Die Teile einer Achse sind additiv (log-Summen), ihre Summe ist wieder das Konto. Nur lesen (``mode=ro``).

    python messe_b0_verlustaufteilung.py <spur.csv> <menge>
"""
from __future__ import annotations

import csv
import math
import os
import re
import sqlite3
import sys
from collections import defaultdict
from datetime import datetime, timedelta

HIER = os.path.dirname(os.path.abspath(__file__))
B0 = datetime(2020, 1, 1)
KNAPP = 10.0          # Abstand zur zweitbesten Stufe (Verlust) - Luecke zwischen knapp 2,5-7,8 und deutlich ab 11,9 (M1-1)


def monat(std):
    return (B0 + timedelta(hours=int(std))).strftime("%Y-%m")


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:                                         # noqa: BLE001
        pass
    spur, menge = sys.argv[1], sys.argv[2]
    sys.path.insert(0, HIER)
    import hebel_neubau as HN
    ref = HN.REGEL0["referenz"][menge]["konto"]
    with open(spur, encoding="utf-8") as f:
        zeilen = list(csv.DictReader(f, delimiter=";"))
    m_ = menge.replace(":", "_")
    wenig = set(open(os.path.join(HIER, "data", "_vergleich", "m1_wenig_%s.txt" % m_), encoding="utf-8").read().split())
    knapp = {}
    if menge == "bestand":
        for l in open(os.path.join(HIER, "Basisinfos", "Kern_Short_30_09", "m1_1__bestand.txt"), encoding="utf-8"):
            mm = re.match(r"\s+(\d{4}-\d{2})\s+lambda\s+\d+\s+·\s+\d+\s+·\s+(.+?)\s+·", l)
            if mm:
                d = sorted(float(x) for x in mm.group(2).split("/"))
                knapp[mm.group(1)] = d[1] < KNAPP
    ce = sqlite3.connect("file:%s?mode=ro" % os.path.join(HIER, "data", "eingestellt_historie.db").replace("\\", "/"), uri=True)
    eing = {r[0] for r in ce.execute("SELECT symbol FROM symbole WHERE art='eingestellt'")}
    ce.close()

    def lg(r):
        return math.log1p(0.01 * r)

    G = sum(lg(float(z["r"])) for z in zeilen)
    G0 = sum(lg(float(z["r"]) + float(z["kosten"])) for z in zeilen)
    print("=" * 110)
    print("B TEIL 0 · VERLUSTAUFTEILUNG DER REGEL0 2025-26 · Menge %s · %d Handel (nur Auskunft)" % (menge, len(zeilen)))
    print("=" * 110)
    print("  R-R11 Konto aus der Spur %+.4f gegen Referenz %+.4f -> %s" % (G, ref, "✔ bitgleich" if abs(G - ref) < 5e-4 else "⛔ ABWEICHUNG"))
    print("  KOSTEN: Konto %+.4f = ohne Kosten %+.4f  +  Kostenanteil %+.4f  (Kosten je Handel im Mittel %.3f %% des Einsatzes, Rohvorteil Spot %+.3f %%)" % (
        G, G0, G - G0, 100 * sum(float(z["kosten"]) for z in zeilen) / len(zeilen),
        100 * sum(float(z["spot"]) + 0.003 for z in zeilen) / len(zeilen)))

    def achse(name, schl):
        grp = defaultdict(list)
        for z in zeilen:
            k = schl(z)
            if k is not None:
                grp[k].append(z)
        print("  %s:" % name)
        for k in sorted(grp, key=str):
            zz = grp[k]
            g = sum(lg(float(z["r"])) for z in zz); g0 = sum(lg(float(z["r"]) + float(z["kosten"])) for z in zz)
            roh = 100 * sum(float(z["spot"]) + 0.003 for z in zz) / len(zz)
            liq = sum(int(z["liq"]) for z in zz)
            print("      %-22s %5d Handel · Konto %+.4f · davon Kosten %+.4f · ohne Kosten %+.4f · Rohvorteil %+.3f %% · Liq %d" % (
                k, len(zz), g, g - g0, g0, roh, liq))

    achse("MONATSKLASSE (K_IG aus 2.697)", lambda z: "Gegenwind (K_IG<1)" if monat(z["std"]) in wenig else "uebrig")
    if knapp:
        achse("DAEMPFUNGSWAHL (M1-1, nur bestand)", lambda z: (("knapp" if knapp[monat(z["std"])] else "deutlich")
                                                              if monat(z["std"]) in knapp else "ohne Eintrag"))
    if menge != "bestand":
        achse("SPAETER EINGESTELLT", lambda z: "eingestellt" if z["symbol"] in eing else "besteht")
    achse("HEBELSTUFE", lambda z: "%sx" % z["stufe"])
    achse("JAHR", lambda z: z["jahr"])
    je = defaultdict(float); n_ = defaultdict(int)
    for z in zeilen:
        je[z["symbol"]] += lg(float(z["r"])); n_[z["symbol"]] += 1
    o = sorted(je, key=lambda s: je[s])
    print("  ASSETS: %d mit Handel · die 10 groessten Verlustbringer zusammen %+.4f · die uebrigen %+.4f · Assets im Plus %d" % (
        len(je), sum(je[s] for s in o[:10]), sum(je[s] for s in o[10:]), sum(1 for s in je if je[s] > 0)))
    print("      " + " · ".join("%s %+.4f (%d%s)" % (s, je[s], n_[s], ", eingestellt" if s in eing and menge != "bestand" else "") for s in o[:10]))
    print("SCHLUSS: vollstaendig")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
