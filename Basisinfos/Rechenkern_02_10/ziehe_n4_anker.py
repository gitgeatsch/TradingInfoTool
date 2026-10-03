"""Die Anker fuer das Rueckspiel N4 - VORAB eingefroren (E-51, Voranalyse_Schritt7 Par. 20.11.5, R-3).

    Entwicklungsmenge   1.000 REGEL0-Einstiege - hier wird gemessen und angepasst (Versuchszaehler)
    Bestaetigungsmenge  1.000 REGEL0-Einstiege - UNBERUEHRT, einmal gemessen mit der endgueltigen Fassung

Quelle: die Spur der REGEL0-Messung (data/_vergleich/b0_spur_bestand.csv, 2025-26, Stufe > 0). Je Jahr geschichtet (gleich viele
aus 2025 und 2026), feste Saat. Die Anker, die in den Kalibrierlaeufen P1 schon verwendet wurden (dieselbe Saat 20261003, die ersten
50 aus 2026 und die 20 Monatsanker), sind GESEHEN und duerfen nur in die Entwicklungsmenge, nie in die Bestaetigungsmenge.
Ausgabe mit SHA-256, damit spaeter nachpruefbar ist, dass die Bestaetigungsmenge nicht veraendert wurde.

    python Basisinfos/Rechenkern_02_10/ziehe_n4_anker.py
"""
from __future__ import annotations

import collections as C
import csv
import hashlib
import os
import random
from datetime import datetime, timedelta

HIER = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
AUS = os.path.dirname(os.path.abspath(__file__))
B0 = datetime(2020, 1, 1)
N = 1000
SAAT = 20261004


def main() -> int:
    sp = [r for r in csv.DictReader(open(os.path.join(HIER, "data", "_vergleich", "b0_spur_bestand.csv")), delimiter=";")
          if r["jahr"] in ("2025", "2026") and int(r["stufe"]) > 0]
    # GESEHEN: die Kalibrieranker (Nachbau der Ziehung in kalibrier_llm.py und kalibrier_markt.py)
    k26 = [r for r in sp if r["jahr"] == "2026"]
    random.Random(20261003).shuffle(k26)
    gesehen = {(r["symbol"], r["std"]) for r in k26[:60]}
    je_monat = C.defaultdict(list)
    for z in sp:
        je_monat[(B0 + timedelta(hours=int(z["std"]))).strftime("%Y-%m")].append(z)
    rnd = random.Random(20261003)
    for m in sorted(m for m in je_monat if "2025-01" <= m <= "2026-08"):
        z = rnd.choice(je_monat[m])
        gesehen.add((z["symbol"], z["std"]))
    rnd = random.Random(SAAT)
    ent, best = [], []
    for jahr in ("2025", "2026"):
        topf = [r for r in sp if r["jahr"] == jahr]
        rnd.shuffle(topf)
        frei = [r for r in topf if (r["symbol"], r["std"]) not in gesehen]
        gs = [r for r in topf if (r["symbol"], r["std"]) in gesehen]
        best += frei[:N // 2]
        rest = gs + frei[N // 2:]
        ent += rest[:N // 2]
    assert not ({(r["symbol"], r["std"]) for r in ent} & {(r["symbol"], r["std"]) for r in best}), "Mengen nicht disjunkt"
    assert not ({(r["symbol"], r["std"]) for r in best} & gesehen), "gesehener Anker in der Bestaetigungsmenge"
    zeilen = []
    for name, menge in (("n4_anker_entwicklung.csv", ent), ("n4_anker_bestaetigung.csv", best)):
        p = os.path.join(AUS, name)
        with open(p, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f, delimiter=";")
            w.writerow(["symbol", "std", "signalstunde_utc", "jahr", "stufe"])
            for r in sorted(menge, key=lambda r: (r["jahr"], int(r["std"]), r["symbol"])):
                w.writerow([r["symbol"], r["std"], (B0 + timedelta(hours=int(r["std"]))).strftime("%Y-%m-%d %H:%M"), r["jahr"], r["stufe"]])
        sha = hashlib.sha256(open(p, "rb").read()).hexdigest()
        zeilen.append("%s  %d Anker  je Jahr %s  %d Symbole  SHA-256 %s" % (
            name, len(menge), dict(C.Counter(r["jahr"] for r in menge)), len({r["symbol"] for r in menge}), sha))
    beleg = os.path.join(AUS, "n4_anker_beleg.txt")
    open(beleg, "w", encoding="utf-8").write(
        "Rueckspiel-Anker N4, gezogen %s mit Saat %d aus %d REGEL0-Einstiegen 2025-26 (Spur b0_spur_bestand.csv)\n"
        "gesehen (Kalibrierlaeufe, nur Entwicklungsmenge): %d\n%s\n" % (datetime.now().strftime("%Y-%m-%d %H:%M"), SAAT, len(sp),
                                                                       len(gesehen), "\n".join(zeilen)))
    print(open(beleg, encoding="utf-8").read())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
