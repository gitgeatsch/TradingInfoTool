"""P101 Messung H-1 (Messplan Basisinfos/Messplan_H1_Lagegerechte_Handlung_28_10.md, Fassungen 2 und 3). Nur lesend.

    python -X utf8 Basisinfos/Rechenkern_02_10/p101_h1_messung.py

Laeuft nur, wenn der Selbsttest bestanden ist (p101_h1_selbsttest.txt) und R-R11 in der Vorpruefung gruen war.
  H-1b  Haltedauer nach dem Trend DIESES Assets: D72/D120/DF, Zustand a (Haupt), b (zweiter Weg), c und m (Auskunft)
  H-1c  kurz bei Extrem: D6/D72, Zustand extrem (Haupt), ext_mom und ext_rsi (zweiter Weg)
Urteil 2025-26 in der Tagesklammer (brutto); 2025 und 2026 einzeln (Vorzeichen); 2024 Auskunft; gepoolt je Handel Auskunft.
"""
import json
import os
import sys
from datetime import datetime

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import p101_h1_basis as B  # noqa: E402

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:  # noqa: BLE001
    pass
HIER = os.path.dirname(os.path.abspath(__file__))
KOSTEN_FIX, KOSTEN_TAG = 0.0030, 0.0018
STUNDEN = {"r6": 6, "r24": 24, "r72": 72, "r120": 120, "rF": 120}


def vorzeichen(x):
    return 0 if not np.isfinite(x) else (1 if x > 0 else -1)


def richtung(b):
    """+1 / -1 bei TRAEGT (gegen den Nullpunkt), sonst 0."""
    s = b["stufe"]
    return (1 if "HOEHER" in s else -1) if s.startswith("TRAEGT (") else 0


def pp(x):
    return "%+.2f" % (100 * x) if np.isfinite(x) else "  -  "


def main():
    st = open(os.path.join(HIER, "p101_h1_selbsttest.txt"), encoding="utf-8").read()
    vp = open(os.path.join(HIER, "p101_h1_vorpruefung.txt"), encoding="utf-8").read()
    if "SELBSTTEST: ✔ BESTANDEN" not in st or "R-R11 gesamt: ✔" not in vp:
        print("✖ Selbsttest oder R-R11 nicht gruen - keine Messung (Messplan §6)")
        return 1
    X = json.load(open(os.path.join(B.ABLAGE, "aufloesung.json"), encoding="utf-8"))
    vorher = B.fingerabdruck()
    rng = np.random.default_rng(20261029)
    print("P101 MESSUNG H-1 (Fassung 2/3) · %s · Desktop · brutto, Tagesklammer, Band zweiseitig nach Bonferroni\n"
          % datetime.now().strftime("%d.%m.%Y %H:%M"))
    gesamt = {}
    for teil, hyps, haupt, zweite, auskunft in (("H-1b", B.H1B, "a", ("b",), ("c", "m")),
                                                ("H-1c", B.H1C, "extrem", ("ext_mom", "ext_rsi"), ())):
        nh = len(hyps)
        for name, lang, kurz in hyps:
            key = "%s_%s" % (teil, name)
            gesamt[key] = {"haupt": [], "jahre": [], "zweite": []}
            print("=" * 118)
            print("%s %s = %s - %s · Hauptzustand %s · zweiter Weg %s · Auskunft %s" % (
                teil, name, lang, kurz, haupt, "/".join(zweite), "/".join(auskunft) or "-"))
            print("   %-13s %-6s %8s %18s %8s %6s %6s  %s" % ("Menge", "Zust.", "Mittel", "Band", "Null", "Tage", "Bl.", "Stufe"))
            for menge in B.MENGEN:
                D = B.tabelle(menge)
                U = D[D.jahr >= 2025]
                xk = X[menge].get(key)
                for zst in (haupt,) + zweite + auskunft:
                    b = B.bewerte(U.tag.to_numpy(), U[zst].to_numpy(float), B.delta(U, lang, kurz), rng, nh, aufloesung=xk)
                    print("   %-13s %-6s %8s [%7s;%7s] %8s %6d %6d  %s" % (
                        menge, zst, pp(b["mittel"]), pp(b.get("unten", np.nan)), pp(b.get("oben", np.nan)),
                        pp(b.get("nullpunkt", np.nan)), b["n_tage"], b["n_bloecke"], b["stufe"]))
                    if zst == haupt:
                        gesamt[key]["haupt"].append((richtung(b), vorzeichen(b["mittel"])))
                        j = {}
                        for jahr in (2024, 2025, 2026):
                            V = D[D.jahr == jahr]
                            j[jahr] = B.klammer(V.tag.to_numpy(), V[zst].to_numpy(float), B.delta(V, lang, kurz))
                        gesamt[key]["jahre"].append((vorzeichen(j[2025]), vorzeichen(j[2026])))
                        z = U[zst].to_numpy(float)
                        d = B.delta(U, lang, kurz)
                        ok = np.isfinite(z) & np.isfinite(d)
                        m1, m0 = d[ok & (z == 1)].mean(), d[ok & (z == 0)].mean()
                        kost = KOSTEN_TAG * (STUNDEN[lang] - STUNDEN[kurz]) / 24.0
                        print("   %-13s        je Jahr (Klammer): 2024 %s · 2025 %s · 2026 %s  |  gepoolt je Handel: Zustand %s / "
                              "sonst %s Pp (Unterschied %s) · netto-Niveau je Zustand %s / %s (Mehrkosten %.2f Pp, in der "
                              "Klammer gleich)" % ("", pp(j[2024]), pp(j[2025]), pp(j[2026]), pp(m1), pp(m0), pp(m1 - m0),
                                                   pp(m1 - kost), pp(m0 - kost), 100 * kost))
                    elif zst in zweite:
                        gesamt[key]["zweite"].append((zst, richtung(b), vorzeichen(b["mittel"])))
    print("\n" + "=" * 118)
    print("GESAMTURTEIL je Hypothese (vorab: alle Punkte; >= 3 von 4 Mengen)")
    for key, g in gesamt.items():
        rh = [r for r, _v in g["haupt"]]
        for ri in (1, -1):
            n_tr = sum(r == ri for r in rh)
            if n_tr >= 3:
                break
        else:
            ri, n_tr = 0, max(sum(r == 1 for r in rh), sum(r == -1 for r in rh))
        p1 = ri != 0
        p2 = p1 and sum(a == ri and b_ == ri for a, b_ in g["jahre"]) >= 3
        if key.startswith("H-1b"):
            p3 = p1 and sum(r == ri for _z, r, _v in g["zweite"]) >= 3
        else:
            p3 = p1 and all(sum(v == ri for z, _r, v in g["zweite"] if z == zz) >= 3 for zz in ("ext_mom", "ext_rsi"))
        urteil = "TRAEGT (%s)" % ("HOEHER im Zustand" if ri > 0 else "NIEDRIGER im Zustand") if (p1 and p2 and p3) else "traegt nicht"
        print("   %-10s (1) Band %d/4%s · (2) 2025 und 2026 gleich %s · (3) zweiter Weg %s · (4) Selbsttest ✔  ->  %s" % (
            key, n_tr, "" if p1 else " ✖", "✔" if p2 else "✖", "✔" if p3 else "✖", urteil))
    nachher = B.fingerabdruck()
    print("\nSeiteneffekt Produktionsdatei: %s" % ("✔ unveraendert" if vorher == nachher else "✖ VERAENDERT"))
    print("Geltungsbereich: REGEL0-Einstiege (vier Mengen) mit lueckenlosen 168 h, 2025-01 bis 2026-08, Tagesklammer "
          "(jeder Tag mit beiden Zustaenden gleich gewichtet), brutto, Spot-Stundenkurse.")
    return 0 if vorher == nachher else 1


if __name__ == "__main__":
    sys.exit(main())
