"""G7 S8 — SELBSTTEST der Messanlage auf der S8-Hauptgröße |ertrag_s| (BTC, H = 1), VOR dem ersten Blick auf ein S8-Urteil
(Vorabfestlegung Stufe 1 §4: S8 `zustand` ≥ auffällig gegen BTC |ertrag_s|, H = 1, einseitig OBEN; Nutzer 05.11.2026: *„ja - die
punkte bitte machen“*).

|ertrag_s| ist nicht symmetrisch (≥ 0, schief) - der Selbsttest von Stufe 0 b lief nur auf ertrag/tief. Gerechnet wird mit
g7_messanlage.selbsttest auf z = −|ertrag_s|: „unten“ heißt dann „größere Bewegung“ (= einseitig oben auf |ertrag_s|).
Null: geballte Urteile ohne Bezug zur Zukunft (Lauflänge 1/3/10 T), Raten 10/20/40 %; Soll ≤ 5 %, Toleranz 6,5 %.
Pflanzung: |ertrag_s| an den Ja-Tagen um 0,1–0,5 σ erhöht. Kein LLM-Urteil gelesen.

    python Basisinfos/Rechenkern_02_10/g7_s8_selbsttest.py   -> g7_s8_selbsttest.txt
"""
import os
import sys
import time

import numpy as np

HIER = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.dirname(os.path.dirname(HIER))
sys.path.insert(0, PROJ)
sys.path.insert(0, HIER)
import g7_messanlage as M        # noqa: E402
import g7_stufe0 as S0           # noqa: E402

TXT = []


def p(*a):
    s = " ".join(str(x) for x in a)
    print(s, flush=True)
    TXT.append(s)


def main():
    rng = np.random.default_rng(81105)
    z = -M.zielgroesse(S0.kurs_btc(), 1, "ertrag").abs().loc["2025-12-01":"2026-10-31"]
    p("G7 S8 SELBSTTEST · %s · BTC |ertrag_s| H=1, %d Tage · kein LLM-Urteil" % (time.strftime("%Y-%m-%d %H:%M"), z.notna().sum()))
    ok = True
    for rate in (0.1, 0.2, 0.4):
        t0 = time.time()
        r = M.selbsttest(z, 1, rng, ziehungen=1000, rate=rate)
        g = all(v <= 0.065 for v in r["fehlalarm"].values())
        ok &= g
        p("  Rate %2.0f %% · %d Blöcke · Fehlalarm %s · Fund %s · %s (%.0f s)" % (
            100 * rate, r["bloecke"], " ".join("L%d %.1f %%" % (L, 100 * v) for L, v in r["fehlalarm"].items()),
            " ".join("%.1fσ %.0f %%" % (s, 100 * v) for s, v in r["fund"].items()), "OK" if g else "⚠ ZU VIELE FEHLALARME",
            time.time() - t0))
    p("=> %s" % ("BESTANDEN (Fehlalarm ≤ 6,5 % bei allen Raten und Lauflängen)" if ok else "⚠ NICHT BESTANDEN - S8 nicht so messen"))
    open(os.path.join(HIER, "g7_s8_selbsttest.txt"), "w", encoding="utf-8").write("\n".join(TXT) + "\n")


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:                                                  # noqa: BLE001
        pass
    main()
