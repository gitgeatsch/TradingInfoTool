# -*- coding: utf-8 -*-
"""Der RANGVERFALL - "verschwinden" heisst absinken, nicht delisted (06.09.).

Nutzerpraezisierung: *"mit verschwinden meine ich, dass diese ehemals als
Top-Coin zur breiten Mehrheit der tausenden Kryptowerten fallen mit
niedriger Marktkapitalisierung - nicht als verschwunden im klassischen
Sinn."*

  V1  PERSISTENZ: wie viele der heutigen Top 20 / Top 100 sind es
      in 90 / 365 / 730 Tagen noch?
  V2  RANGTREND als Kandidat: sagt die Rangaenderung ueber 180 Tage
      etwas ueber die naechsten 5 Tage - je Tagesklammer?
"""
from __future__ import annotations
import sys
import numpy as np
if hasattr(sys.stdout, "reconfigure"):        # ⚠️ Suite ersetzt stdout
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import messe_eigenschaft_beitrag as B                       # noqa: E402

BRUCH, H, RB, ZURUECK = 5.0, 5, 252, 180


def gleit(x, n):
    c = np.concatenate(([0.0], np.cumsum(x)))
    a = np.full(len(x), np.nan)
    a[n:] = (c[n:-1] - c[:-n - 1]) / n
    return a


def main() -> int:
    print("Lade Reihen ...", flush=True)
    reihen = B.lade()
    je_tag: dict = {}
    for sym, z in reihen.items():
        tage = [x[0] for x in z]
        c = np.array([x[1] for x in z]); h = np.array([x[2] for x in z])
        t = np.array([x[3] for x in z]); v = np.array([x[4] for x in z])
        br = B.spanne(h, t, c, B.SCHWANKUNG)
        u = gleit(v * c, RB)
        vh = c[1:] / np.maximum(c[:-1], 1e-12)
        bruch = (vh > BRUCH) | (vh < 1.0 / BRUCH)
        for i in range(RB, len(c) - H):
            if not np.isfinite(br[i]) or br[i] <= 0 or not np.isfinite(u[i]):
                continue
            if u[i] <= 0 or bruch[i:i + H].any():
                continue
            je_tag.setdefault(tage[i], []).append(
                (sym, float(u[i]), float((c[i + H] - c[i]) / br[i])))
    tage = sorted(t for t, w in je_tag.items() if len(w) >= 50)
    rang = {t: {q[0]: r for r, q in
                enumerate(sorted(je_tag[t], key=lambda x: -x[1]))}
            for t in tage}
    print("  %d Tage" % len(tage))

    # ---------------- V1  PERSISTENZ --------------------------------------
    print()
    print("=" * 86)
    print("V1  RANGPERSISTENZ - wie viele bleiben oben?")
    print("=" * 86)
    print("  %-14s %10s %10s %10s" % ("Startgruppe", "+90 Tage",
                                      "+365 Tage", "+730 Tage"))
    for lab, grenze in (("Top 20", 20), ("Top 100", 100)):
        zeile = []
        for d in (90, 365, 730):
            q = []
            for i, t in enumerate(tage):
                if i + d >= len(tage):
                    break
                spaeter = rang[tage[i + d]]
                start = [s for s, r in rang[t].items() if r < grenze]
                da = [s for s in start if s in spaeter]
                if len(da) < grenze // 2:
                    continue
                q.append(np.mean([spaeter[s] < grenze for s in da]))
            zeile.append(100 * np.mean(q) if q else float("nan"))
        print("  %-14s %9.1f%% %9.1f%% %9.1f%%" % (lab, *zeile))
    print()
    print("  (nur Werte gezaehlt, die spaeter noch Daten haben - der")
    print("   Verfall ist damit eher UNTERschaetzt)")

    # ---------------- V2  RANGTREND als Kandidat --------------------------
    print()
    print("=" * 86)
    print("V2  RANGTREND ueber %d Tage -> naechste %d Tage in R" % (ZURUECK, H))
    print("=" * 86)
    idx = {t: i for i, t in enumerate(tage)}
    KLASSEN = [("stark gestiegen", -10**9, -20), ("gestiegen", -20, -5),
               ("stabil", -5, 5), ("gefallen", 5, 20),
               ("stark gefallen", 20, 10**9)]
    # je Tag ein Mittelwert je Klasse  ->  Tagesklammer
    proTag: dict = {k[0]: [] for k in KLASSEN}
    for t in tage:
        i = idx[t]
        if i < ZURUECK:
            continue
        alt = rang[tage[i - ZURUECK]]
        eimer: dict = {k[0]: [] for k in KLASSEN}
        for q in je_tag[t]:
            if q[0] not in alt:
                continue
            d = rang[t][q[0]] - alt[q[0]]          # positiv = abgestiegen
            for name, lo, hi in KLASSEN:
                if lo <= d < hi:
                    eimer[name].append(q[2]); break
        for name, v in eimer.items():
            if len(v) >= 5:
                proTag[name].append(float(np.mean(v)))
    print("  %-18s %8s %9s %9s %9s"
          % ("Klasse", "Tage", "Mittel R", "Streufeh.", "t"))
    for name, _, _ in KLASSEN:
        v = np.array(proTag[name], float)
        if len(v) < 30:
            print("  %-18s %8d   zu wenige Tage" % (name, len(v))); continue
        se = v.std(ddof=1) / np.sqrt(len(v))
        print("  %-18s %8d %9.4f %9.4f %9.2f"
              % (name, len(v), v.mean(), se, v.mean() / se if se else 0))
    a = np.array(proTag["stark gestiegen"]); b = np.array(proTag["stark gefallen"])
    n = min(len(a), len(b))
    if n >= 30:
        d = a[:n] - b[:n]
        se = d.std(ddof=1) / np.sqrt(n)
        print()
        print("  Abstand aufgestiegen minus abgestiegen: %+.4f R"
              " (Streufehler %.4f, t = %.2f)" % (d.mean(), se, d.mean() / se))
    print()
    print("  ⚠️ Der t-Wert nutzt UNABHAENGIGE Tage - die Tage sind es aber")
    print("     nicht (ueberlappende %d-Tage-Fenster). Erst der" % H)
    print("     Blockbootstrap gibt ein ehrliches Band. LAGEBILD.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
