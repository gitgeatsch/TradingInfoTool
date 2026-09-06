# -*- coding: utf-8 -*-
"""Zwei Kontrollen zur Alltagsmessung (06.09.2026).

  K1  Sagt die "Top10%-Konzentration" ueberhaupt etwas?
      Nullpunkt: dieselbe Kennzahl auf einer NORMALVERTEILUNG.
  K2  Taugt die STREUUNG als Phasen-Schichter, wo die BTC-Dominanz
      versagt hat? Bloecke je Phase zaehlen.
"""
from __future__ import annotations
import sys
import numpy as np
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import messe_eigenschaft_beitrag as B                       # noqa: E402

BRUCH, H = 5.0, 5


def konz(x):
    s = np.sort(np.asarray(x, float))[::-1]
    g = np.abs(s).sum()
    return float(s[:max(1, len(s) // 10)].sum() / g) if g > 0 else 0.0


def main() -> int:
    rng = np.random.default_rng(20260906)
    print("=" * 84)
    print("K1  NULLPUNKT der Top10%-Konzentration")
    print("=" * 84)
    for n in (100, 300, 500):
        norm = [konz(rng.standard_normal(n)) for _ in range(2000)]
        t = [konz(rng.standard_t(3, n)) for _ in range(2000)]
        print("  n=%3d   Normalverteilung %5.1f%%   t(3), schwerer Rand %5.1f%%"
              % (n, 100 * np.mean(norm), 100 * np.mean(t)))
    print()
    print("  ⚠️ Gemessen wurden 24,3 % (2024-2026) bis 27,9 % (2021-2023).")
    print("     Die Zahl ist nur brauchbar, wenn sie den Nullpunkt DEUTLICH")
    print("     uebersteigt.")

    print()
    print("Lade Reihen ...", flush=True)
    reihen = B.lade()
    je_tag: dict = {}
    for sym, z in reihen.items():
        tage = [x[0] for x in z]
        c = np.array([x[1] for x in z]); h = np.array([x[2] for x in z])
        t = np.array([x[3] for x in z])
        br = B.spanne(h, t, c, B.SCHWANKUNG)
        v = c[1:] / np.maximum(c[:-1], 1e-12)
        bruch = (v > BRUCH) | (v < 1.0 / BRUCH)
        for i in range(B.SCHWANKUNG, len(c) - H):
            if not np.isfinite(br[i]) or br[i] <= 0 or bruch[i:i + H].any():
                continue
            je_tag.setdefault(tage[i], []).append((c[i + H] - c[i]) / br[i])

    tage = sorted(t for t, w in je_tag.items() if len(w) >= 20)
    streu = np.array([np.percentile(je_tag[t], 90) - np.percentile(je_tag[t], 50)
                      for t in tage])
    print()
    print("=" * 84)
    print("K2  DIE STREUUNG als Phasen-Schichter   (p90 - p50 in R, Horizont 5)")
    print("=" * 84)
    print("  %d Tage · Median %.3f R · p10 %.3f · p90 %.3f"
          % (len(tage), np.median(streu), np.percentile(streu, 10),
             np.percentile(streu, 90)))
    for name, a, b in (("2018-2020", "2018-01-01", "2020-12-31"),
                       ("2021-2023", "2021-01-01", "2023-12-31"),
                       ("2024-2026", "2024-01-01", "2026-12-31")):
        m = np.array([a <= t <= b for t in tage])
        if m.sum():
            print("    %s  Median %.3f R   (%d Tage)"
                  % (name, np.median(streu[m]), m.sum()))

    # geglaettet, damit nicht jeder Tag die Phase wechselt
    g = np.convolve(streu, np.ones(20) / 20, mode="same")
    schwelle = np.median(g)
    hoch = g >= schwelle
    phasen, i = [], 0
    while i < len(hoch):
        j = i
        while j + 1 < len(hoch) and hoch[j + 1] == hoch[i]:
            j += 1
        if j - i + 1 >= 60:
            phasen.append((bool(hoch[i]), tage[i], tage[j], j - i + 1))
        i = j + 1
    print()
    print("  Phasen >= 60 Tage (Schwelle = Median der geglaetteten Streuung):")
    for typ, a, b, n in phasen:
        print("    %-11s %s .. %s  %5d Tage -> %3d Bloecke"
              % ("HOCH" if typ else "niedrig", a, b, n, n // 15))
    for typ, lab in ((True, "HOCH   "), (False, "niedrig")):
        s = sum(n for t, _, _, n in phasen if t == typ)
        print("    Summe %s  %5d Tage -> %3d Bloecke   %s"
              % (lab, s, s // 15, "✔" if s // 15 >= 20 else "✖"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
