# -*- coding: utf-8 -*-
"""Die zwei Annahmen des Nutzers messen (06.09.2026).

  A1  Die Extreme werden SELTENER.
  A2  Nicht alle Altcoins steigen - EINZELNE bringen massiven Gewinn.

Beides je Epoche und je Horizont. Zielgroesse wie im Projekt:
in_r = (c[i+H] - c[i]) / spanne14[i].
"""
from __future__ import annotations
import sys
import numpy as np
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import messe_eigenschaft_beitrag as B                       # noqa: E402

BRUCH = 5.0
EPOCHEN = [("2018-2020", "2018-01-01", "2020-12-31"),
           ("2021-2023", "2021-01-01", "2023-12-31"),
           ("2024-2026", "2024-01-01", "2026-12-31")]


def quer(reihen, H):
    """Je Kalendertag der Querschnitt: (pct, in_r) ueber alle Symbole."""
    je_tag: dict = {}
    for sym, z in reihen.items():
        tage = [x[0] for x in z]
        c = np.array([x[1] for x in z]); h = np.array([x[2] for x in z])
        t = np.array([x[3] for x in z])
        br = B.spanne(h, t, c, B.SCHWANKUNG)
        v = c[1:] / np.maximum(c[:-1], 1e-12)
        bruch = (v > BRUCH) | (v < 1.0 / BRUCH)
        n = len(c)
        for i in range(B.SCHWANKUNG, n - H):
            if not np.isfinite(br[i]) or br[i] <= 0:
                continue
            if bruch[i:i + H].any():          # Token-Umstellung im Fenster
                continue
            weg = c[i + H] - c[i]
            je_tag.setdefault(tage[i], []).append(
                (weg / c[i], weg / br[i]))
    return je_tag


def epoche(je_tag, a, b, spalte):
    """Mittel UEBER DIE TAGE der Querschnitts-Perzentile (Tagesklammer)."""
    p = {k: [] for k in (10, 50, 90, 99)}
    anteil_gross, anteil_top = [], []
    for tag, werte in je_tag.items():
        if not (a <= tag <= b) or len(werte) < 20:
            continue
        x = np.array([w[spalte] for w in werte], float)
        for k in p:
            p[k].append(np.percentile(x, k))
        anteil_gross.append(float((x > (0.5 if spalte == 0 else 2.0)).mean()))
        s = np.sort(x)[::-1]
        oben = s[:max(1, len(s) // 10)].sum()
        ges = np.abs(s).sum()
        anteil_top.append(float(oben / ges) if ges > 0 else 0.0)
    if not p[50]:
        return None
    return {"tage": len(p[50]),
            **{("p%d" % k): float(np.mean(v)) for k, v in p.items()},
            "gross": float(np.mean(anteil_gross)),
            "top": float(np.mean(anteil_top))}


def main() -> int:
    print("Lade Reihen ...", flush=True)
    reihen = B.lade()
    print("  %d Kryptoreihen" % len(reihen), flush=True)

    # ---- A1: werden die Extreme seltener? -------------------------------
    print()
    print("=" * 88)
    print("A1  WERDEN DIE EXTREME SELTENER?   Anteil Tage mit |Tagesbewegung| >")
    print("=" * 88)
    print("  %-12s %8s %8s %8s   %8s %8s %8s"
          % ("Epoche", "BTC>5%", "BTC>10%", "BTC>20%",
             "Alt>5%", "Alt>10%", "Alt>20%"))
    for name, a, b in EPOCHEN:
        z = {"btc": [[], [], []], "alt": [[], [], []]}
        for sym, r in reihen.items():
            tage = [x[0] for x in r]
            c = np.array([x[1] for x in r])
            v = np.abs(c[1:] / np.maximum(c[:-1], 1e-12) - 1.0)
            ok = np.array([a <= tage[i + 1] <= b for i in range(len(v))])
            ok &= (v < BRUCH - 1.0)
            if ok.sum() < 30:
                continue
            w = v[ok]
            k = "btc" if sym.upper() in ("BTC", "WBTC") else "alt"
            for j, g in enumerate((0.05, 0.10, 0.20)):
                z[k][j].append(float((w > g).mean()))
        print("  %-12s %7.2f%% %7.2f%% %7.2f%%   %7.2f%% %7.2f%% %7.2f%%"
              % (name,
                 *[100 * np.mean(z["btc"][j]) if z["btc"][j] else float("nan")
                   for j in range(3)],
                 *[100 * np.mean(z["alt"][j]) if z["alt"][j] else float("nan")
                   for j in range(3)]))

    # ---- A2: traegt die SELEKTION? --------------------------------------
    for H in (5, 60):
        je_tag = quer(reihen, H)
        for spalte, einheit, marke in ((0, "PROZENT", "> +50 %"),
                                       (1, "in R", "> +2 R")):
            print()
            print("=" * 88)
            print("A2  QUERSCHNITT ueber %d Tage, %s   (Mittel ueber die Tage)"
                  % (H, einheit))
            print("=" * 88)
            print("  %-12s %6s %9s %9s %9s %9s %9s %8s"
                  % ("Epoche", "Tage", "p10", "p50", "p90", "p99",
                     marke, "Top10%"))
            for name, a, b in EPOCHEN:
                e = epoche(je_tag, a, b, spalte)
                if not e:
                    print("  %-12s  -" % name)
                    continue
                f = "%9.1f%%" if spalte == 0 else "%9.2f "
                print(("  %-12s %6d " + f * 4 + " %8.2f%% %7.1f%%")
                      % (name, e["tage"], *[100 * e["p%d" % k] if spalte == 0
                                            else e["p%d" % k]
                                            for k in (10, 50, 90, 99)],
                         100 * e["gross"], 100 * e["top"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
