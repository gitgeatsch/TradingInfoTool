# -*- coding: utf-8 -*-
"""Die RANGSCHICHTUNG des Marktes messen (06.09.2026).

Nutzerannahme: *"BTC ist das fuehrende Asset, danach kommen bestimmte
Altcoins (ETH etc.), welche ueberleben duerften, danach wird es komplexer -
einige verschwinden und verlieren massiv 90 %, andere kommen nach oben in
die Top 100."*

  S1  UEBERLEBEN: haben wir die Verschwundenen ueberhaupt in den Daten?
      Ohne sie ist jede Messung nach oben verzerrt.
  S2  SCHICHTEN: verhalten sich BTC / Top20 / 21-100 / Rest verschieden?
  S3  AUFSTIEG: was tun die, die in die Top 100 aufsteigen?
"""
from __future__ import annotations
import sys
import numpy as np
if hasattr(sys.stdout, "reconfigure"):        # ⚠️ Suite ersetzt stdout
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import messe_eigenschaft_beitrag as B                       # noqa: E402

BRUCH, H, RB = 5.0, 5, 252


def gleit(x, n):
    """Gleitendes Mittel der letzten n Werte VOR i (nachlaufend)."""
    c = np.concatenate(([0.0], np.cumsum(x)))
    a = np.full(len(x), np.nan)
    a[n:] = (c[n:-1] - c[:-n - 1]) / n
    return a


def main() -> int:
    print("Lade Reihen ...", flush=True)
    reihen = B.lade()
    letzter = max(z[-1][0] for z in reihen.values())
    print("  %d Reihen · letzter Tag im Bestand %s" % (len(reihen), letzter))

    # ---------------- S1  UEBERLEBEN --------------------------------------
    print()
    print("=" * 90)
    print("S1  HABEN WIR DIE VERSCHWUNDENEN?")
    print("=" * 90)
    tot, lebt, verlust = [], [], []
    for sym, z in reihen.items():
        c = np.array([x[1] for x in z], float)
        hoch = float(np.maximum.accumulate(c).max())
        ab = c[-1] / hoch - 1.0 if hoch > 0 else 0.0
        (tot if z[-1][0] < letzter[:8] + "01" else lebt).append(sym)
        verlust.append(ab)
    verlust = np.array(verlust)
    print("  Reihen die im letzten Monat noch laufen : %4d" % len(lebt))
    print("  Reihen die FRUEHER enden (delistet/tot) : %4d" % len(tot))
    print()
    print("  Abstand zum eigenen Hoechststand, alle %d Reihen:" % len(verlust))
    for g in (0.50, 0.80, 0.90, 0.95, 0.99):
        print("    schlechter als -%2d %%  : %4d Reihen  (%5.1f %%)"
              % (100 * g, int((verlust <= -g).sum()),
                 100 * (verlust <= -g).mean()))
    print()
    print("  ⚠️ Wenn hier fast keine toten Reihen stehen, fehlt der")
    print("     Ueberlebensfehler NICHT - er ist dann nur unsichtbar.")

    # ---------------- Rang je Tag ----------------------------------------
    print()
    print("Baue Umsatzrang je Tag ...", flush=True)
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
    print("  %d Tage mit mindestens 50 Reihen" % len(tage))

    # ---------------- S2  SCHICHTEN ---------------------------------------
    SCHICHT = (("BTC", 0, 1), ("Rang 2-20", 1, 20),
               ("Rang 21-100", 20, 100), ("ab Rang 101", 100, 10**6))
    print()
    print("=" * 90)
    print("S2  VERHALTEN SICH DIE SCHICHTEN VERSCHIEDEN?  (Horizont 5, in R)")
    print("=" * 90)
    for name, a, b in (("2018-2020", "2018-01-01", "2020-12-31"),
                       ("2021-2023", "2021-01-01", "2023-12-31"),
                       ("2024-2026", "2024-01-01", "2026-12-31")):
        print("  %s" % name)
        print("    %-13s %7s %8s %8s %8s %9s %9s"
              % ("Schicht", "n/Tag", "p50", "p90", "p99", ">+2R", "p90-p50"))
        for sn, lo, hi in SCHICHT:
            p50, p90, p99, gr, anz = [], [], [], [], []
            for tag in tage:
                if not (a <= tag <= b):
                    continue
                w = sorted(je_tag[tag], key=lambda x: -x[1])
                if sn == "BTC":
                    x = [q[2] for q in w if q[0].upper() in ("BTC", "WBTC")]
                else:
                    x = [q[2] for q in w[lo:hi]]
                if len(x) < (1 if sn == "BTC" else 5):
                    continue
                x = np.array(x, float)
                p50.append(np.percentile(x, 50)); p90.append(np.percentile(x, 90))
                p99.append(np.percentile(x, 99)); gr.append((x > 2.0).mean())
                anz.append(len(x))
            if not p50:
                print("    %-13s  -" % sn); continue
            print("    %-13s %7.1f %8.2f %8.2f %8.2f %8.2f%% %9.2f"
                  % (sn, np.mean(anz), np.mean(p50), np.mean(p90),
                     np.mean(p99), 100 * np.mean(gr),
                     np.mean(p90) - np.mean(p50)))
        print()

    # ---------------- S3  AUFSTIEG ----------------------------------------
    print("=" * 90)
    print("S3  DER AUFSTIEG IN DIE TOP 100  (Rang heute vs. vor 60 Tagen)")
    print("=" * 90)
    idx = {t: i for i, t in enumerate(tage)}
    gruppen = {"neu in Top100": [], "in Top100 geblieben": [],
               "aus Top100 gefallen": [], "ausserhalb geblieben": []}
    for t in tage:
        i = idx[t]
        if i < 60:
            continue
        alt = {q[0]: r for r, q in enumerate(
            sorted(je_tag[tage[i - 60]], key=lambda x: -x[1]))}
        for r, q in enumerate(sorted(je_tag[t], key=lambda x: -x[1])):
            if q[0] not in alt:
                continue
            a, n = alt[q[0]] < 100, r < 100
            k = ("neu in Top100" if n and not a else
                 "in Top100 geblieben" if n and a else
                 "aus Top100 gefallen" if a else "ausserhalb geblieben")
            gruppen[k].append(q[2])
    print("  %-22s %9s %8s %8s %9s"
          % ("Gruppe", "Faelle", "Mittel", "p90", ">+2R"))
    for k, v in gruppen.items():
        if not v:
            continue
        x = np.array(v, float)
        print("  %-22s %9d %8.3f %8.2f %8.2f%%"
              % (k, len(x), x.mean(), np.percentile(x, 90),
                 100 * (x > 2.0).mean()))
    print()
    print("  ⚠️ Die Faelle sind NICHT unabhaengig (ueberlappende Fenster,")
    print("     derselbe Tag). Das ist ein LAGEBILD, kein Befund - eine")
    print("     Aussage braucht die Tagesklammer und den Blockbootstrap.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
