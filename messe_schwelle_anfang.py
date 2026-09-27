# -*- coding: utf-8 -*-
"""Die Schwelle auf STRECKENANFAENGEN - dem Betriebsfall.

**27.09.2026**, Nutzerauftrag nach 2.638.

Vorabfestlegung: `Basisinfos/Vorabfestlegung_32_Schwelle_Streckenanfang_27_09.md`

═══════════════════════════════════════════════════════════════════════
 WARUM
═══════════════════════════════════════════════════════════════════════

-1,2881 ist die Kelly-Nullstelle ueber ALLE Anker (2.632). Der Betrieb
kauft aber nur STRECKENANFAENGE (2.638): dort liegt der Ertrag bei
+0,3393 statt +1,2568 Prozent, weil ein Symbol im Schnitt 3,4 Stunden am
Stueck unter der Schwelle liegt und der Tiefpunkt SPAETER kommt.

═══════════════════════════════════════════════════════════════════════
 ⚠️ DAS ZIRKULARITAETSPROBLEM
═══════════════════════════════════════════════════════════════════════

Die Schwelle bestimmt, WO eine Strecke anfaengt. Die Strecken bestimmen,
WELCHE Anker in die Rechnung gehen.

➤ Aufloesung: fuer JEDE Kandidatenschwelle wird die Streckenmenge NEU
abgegrenzt. Keine Iteration, kein Startwert, der das Ergebnis faerbt.

⚠️ Das ist NICHT das gleitende Fenster aus 2.632 - dort lief es ueber die
nach `W` sortierten Anker. Hier ist die Menge je Schwelle eine andere.

⚠️ NUR LESEN.  python messe_schwelle_anfang.py [--symbole N]
"""
from __future__ import annotations

import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import messnorm as N                                            # noqa: E402
from messe_reverse_scharfe_anstiege import lade_kurse           # noqa: E402
from messe_hebel_geometrie_neutral import atr_tag_relativ       # noqa: E402
from messe_trailing_und_betrieb import ema                      # noqa: E402
from messe_hebel_neudimension import (                          # noqa: E402
    trailing_mit_ausloeser, EMA_L, VORLAUF)
from messe_skalenangleich import atr_aus_schluessen             # noqa: E402

HZ, STOP, AUSL, ABST = 24, 1.00, 1.5, 0.5
FAKTOR = 2.0832                     # 2.637
KANDIDATEN = np.round(np.arange(-0.80, -2.601, -0.05), 4)
MINDEST = 150                       # weniger Anfaenge sind nicht auswertbar
SAAT = 20260927


def anfaenge(W, Z, SI, schwelle):
    """Indizes der STRECKENANFAENGE fuer eine gegebene Schwelle.

    ⚠️ Je Schwelle NEU - das ist die Aufloesung des
    Zirkularitaetsproblems."""
    idx = np.flatnonzero(W <= schwelle)
    if not len(idx):
        return idx
    o = np.lexsort((Z[idx], SI[idx]))
    idx = idx[o]
    neu = np.ones(len(idx), bool)
    neu[1:] = (SI[idx][1:] != SI[idx][:-1]) | (np.diff(Z[idx]) > HZ)
    return idx[neu]


def kelly_von(r):
    if len(r) < 50:
        return (float("nan"),) * 3
    q = float((r > 0).mean())
    g, v = r[r > 0], r[r <= 0]
    if not len(g) or not len(v) or v.mean() == 0:
        return q, float("nan"), float("nan")
    crv = float(g.mean() / abs(v.mean()))
    if crv <= 0:
        return q, crv, float("nan")
    return q, crv, (q * (1.0 + crv) - 1.0) / crv


def main() -> int:
    grenze = None
    if "--symbole" in sys.argv:
        grenze = int(sys.argv[sys.argv.index("--symbole") + 1])

    print("=" * 106)
    print("DIE SCHWELLE AUF STRECKENANFAENGEN - dem Betriebsfall")
    print("=" * 106)
    print("  " + N.standardzeile())
    print("  Geometrie H%d / Stop %.2f ATR / Trailing %.1f / %.1f (2.628)"
          % (HZ, STOP, AUSL, ABST))
    print("  %d Kandidatenschwellen von %.2f bis %.2f, Strecken JE "
          "SCHWELLE neu" % (len(KANDIDATEN), KANDIDATEN[0], KANDIDATEN[-1]))
    print()

    kurse = lade_kurse(grenze)
    alle = set()
    for (s, *_r) in kurse.values():
        alle.update(s)
    sl = sorted(alle); sid = {s: i for i, s in enumerate(sl)}
    Z, SI, WA, WD, P, R = [], [], [], [], [], []
    nam = []
    for sym, (st, h, l, cc, v) in kurse.items():
        if sym.upper() == "BTC":
            continue
        gi = np.array([sid[x] for x in st], np.int64)
        aA = atr_tag_relativ(h, l, cc)
        aD = atr_aus_schluessen(cc)
        e = ema(cc, EMA_L)
        r, p, _g = trailing_mit_ausloeser(h, l, cc, aA, STOP, AUSL, ABST, HZ)
        gu = (np.isfinite(aA) & (aA > 0) & np.isfinite(aD) & (aD > 0)
              & np.isfinite(e) & np.isfinite(p) & np.isfinite(r))
        gu[:VORLAUF] = False
        gu[max(0, len(cc) - HZ):] = False
        s2 = np.flatnonzero(gu)
        if len(s2) < 500:
            continue
        i = len(nam); nam.append(sym)
        Z.append(gi[s2]); SI.append(np.full(len(s2), i, np.int64))
        WA.append((cc[s2] - e[s2]) / np.maximum(aA[s2] * cc[s2], 1e-12))
        WD.append(((cc[s2] - e[s2]) / np.maximum(aD[s2] * cc[s2], 1e-12))
                  / FAKTOR)
        P.append(p[s2]); R.append(r[s2])
    Z = np.concatenate(Z); SI = np.concatenate(SI)
    WA = np.concatenate(WA); WD = np.concatenate(WD)
    P = np.concatenate(P); R = np.concatenate(R)
    tag = Z // 24; tg = len(np.unique(tag))
    print("  %d Anker · %d Symbole · %d Tage" % (len(Z), len(nam), tg),
          flush=True)
    print()

    rng = np.random.default_rng(SAAT)
    pool = {}
    for i_ in range(len(Z)):
        pool.setdefault(int(tag[i_]), []).append(i_)
    pool = {t: np.array(v) for t, v in pool.items()}

    def nullproben(idx):
        je = {int(t): int(c) for t, c in
              zip(*np.unique(tag[idx], return_counts=True))}
        o = []
        for _ in range(N.NULL_ZIEHUNGEN):
            a = []
            for t, c in je.items():
                pl = pool.get(t)
                if pl is not None and len(pl):
                    a.append(rng.choice(pl, size=min(c, len(pl)),
                                        replace=False))
            if a:
                o.append(100 * float(P[np.concatenate(a)].mean()))
        return np.array(o) if o else np.zeros(1)

    # ══ TEIL 1: die Kelly-Kurve auf Streckenanfaengen ════════════════
    print("=" * 106)
    print("TEIL 1 - KELLY AUF STRECKENANFAENGEN, je Kandidatenschwelle")
    print()
    print("  %-10s %9s %8s %8s %9s %11s %11s %11s  %s"
          % ("Schwelle", "Anfaenge", "je Tag", "q", "CRV", "Kelly",
             "Ertrag %", "Nullband", "Urteil"))
    zeilen, proben = [], []
    for sw in KANDIDATEN:
        an = anfaenge(WA, Z, SI, sw)
        if len(an) < MINDEST:
            continue
        q, crv, kel = kelly_von(R[an])
        if kel != kel:
            continue
        nb = nullproben(an)
        band = float(np.percentile(nb, N.NULL_PERZENTIL))
        er = 100 * float(P[an].mean())
        zeilen.append(dict(sw=float(sw), n=len(an), q=q, crv=crv, kelly=kel,
                           er=er, band=band))
        proben.append(nb)
        if abs(sw * 100) % 20 < 1 or abs(kel) < 0.02:   # jede 0,20 + Nullnähe
            print("  %-10.2f %9d %8.2f %7.1f%% %9.3f %+11.4f %+11.4f "
                  "%+11.4f  %s"
                  % (sw, len(an), len(an) / tg, 100 * q, crv, kel, er, band,
                     "✔" if er > band else "⛔ im Band"), flush=True)

    if len(zeilen) < 5:
        print("  ⛔ zu wenige auswertbare Schwellen")
        return 1

    # ══ TEIL 2: die Nullstelle ═══════════════════════════════════════
    print()
    print("=" * 106)
    print("TEIL 2 - DIE KELLY-NULLSTELLE (interpoliert, Falle 3)")
    print()
    xs = np.array([z["sw"] for z in zeilen])
    ks = np.array([z["kelly"] for z in zeilen])
    null = None
    for i in range(len(xs) - 1):
        if ks[i] <= 0 < ks[i + 1]:          # von unten nach oben (sw fällt)
            null = xs[i] + (xs[i + 1] - xs[i]) * \
                (0 - ks[i]) / max(ks[i + 1] - ks[i], 1e-12)
            break
    print("  Kelly bei der loseren Kante (%.2f): %+.4f" % (xs[0], ks[0]))
    print("  Kelly bei der straffsten  (%.2f): %+.4f" % (xs[-1], ks[-1]))
    if null is None:
        print("  ⭐ KEINE Nullstelle im gemessenen Bereich - Kelly bleibt "
              "durchgehend %s" % ("POSITIV" if ks.min() > 0 else "negativ"))
        print("     ➤ dann begrenzt nicht die Bewertung, sondern die "
              "SIGNALZAHL, und die Schwelle folgt aus der Kapazitaet.")
    else:
        print("  ⭐ NULLSTELLE bei W = %+.4f  (zum Vergleich: -1,2881 ueber "
              "ALLE Anker)" % null)

    # ══ TEIL 3: Mehrfachtesten ═══════════════════════════════════════
    print()
    print("=" * 106)
    print("TEIL 3 - MEHRFACHTESTEN ueber %d Schwellen (Falle 2)"
          % len(zeilen))
    arr = np.array([p[:min(len(x) for x in proben)] for p in proben])
    b = float(np.percentile(arr.max(axis=0), N.NULL_PERZENTIL))
    halten = [z for z in zeilen if z["er"] > b]
    print("  Bestes-von-%d-Band: %+.4f %%" % (len(zeilen), b))
    if halten:
        print("  haltende Schwellen: %.2f bis %.2f (%d von %d)"
              % (max(z["sw"] for z in halten), min(z["sw"] for z in halten),
                 len(halten), len(zeilen)))
        best = max(halten, key=lambda z: z["er"])
        print("  beste: %.2f mit %+.4f %% bei %.2f Signalen/Tag"
              % (best["sw"], best["er"], best["n"] / tg))
        lose = max(halten, key=lambda z: z["sw"])
        print("  loseste haltende: %.2f mit %+.4f %% bei %.2f Signalen/Tag"
              % (lose["sw"], lose["er"], lose["n"] / tg))
    else:
        print("  ⛔ KEINE haelt gegen das Mehrfachtesten")

    # ══ TEIL 4: die Nutzerfrage - eine Bewertung oder zwei? ══════════
    print()
    print("=" * 106)
    print("TEIL 4 - EINE BEWERTUNG ODER ZWEI?")
    print("  Nutzerfrage: *brauchen wir fuer Binance und CoinGecko zwei")
    print("  Bewertungen?* - 2.637 sagt nein, aber der Faktor wurde auf")
    print("  ALLEN Ankern bestimmt. Hier auf STRECKENANFAENGEN geprueft.")
    print()
    print("  %-10s %12s %12s %12s %12s %12s"
          % ("Schwelle", "A Anfaenge", "D Anfaenge", "A Kelly", "D Kelly",
             "A Ertrag/D"))
    for sw in (-1.0, -1.2, -1.4, -1.6, -1.8, -2.0):
        aa = anfaenge(WA, Z, SI, sw)
        ad = anfaenge(WD, Z, SI, sw)
        if len(aa) < MINDEST or len(ad) < MINDEST:
            continue
        _q1, _c1, k1 = kelly_von(R[aa])
        _q2, _c2, k2 = kelly_von(R[ad])
        print("  %-10.2f %12d %12d %+12.4f %+12.4f  %+.3f / %+.3f"
              % (sw, len(aa), len(ad), k1, k2,
                 100 * P[aa].mean(), 100 * P[ad].mean()))
    xd = []
    kd = []
    for sw in KANDIDATEN:
        ad = anfaenge(WD, Z, SI, sw)
        if len(ad) < MINDEST:
            continue
        _q, _c, k = kelly_von(R[ad])
        if k == k:
            xd.append(float(sw)); kd.append(k)
    xd = np.array(xd); kd = np.array(kd)
    nulld = None
    for i in range(len(xd) - 1):
        if kd[i] <= 0 < kd[i + 1]:
            nulld = xd[i] + (xd[i + 1] - xd[i]) * \
                (0 - kd[i]) / max(kd[i + 1] - kd[i], 1e-12)
            break
    print()
    print("  Nullstelle A: %s" % ("%+.4f" % null if null is not None
                                  else "keine im Bereich"))
    print("  Nullstelle D: %s" % ("%+.4f" % nulld if nulld is not None
                                  else "keine im Bereich"))
    if null is not None and nulld is not None:
        print("  Abstand: %+.4f  ->  %s"
              % (nulld - null,
                 "✔ EINE Bewertung reicht" if abs(nulld - null) < 0.15
                 else "⛔ zwei Schwellen noetig"))
    else:
        print("  ➤ mindestens eine Seite hat keine Nullstelle - die Frage "
              "entscheidet sich dann nicht an ihr")

    print()
    print("  ⚠️ Gebuehren und Finanzierung sind NICHT eingerechnet (Regel 2).")
    print("  ⚠️ Mindestens %d Anfaenge je Schwelle, sonst nicht ausgewertet."
          % MINDEST)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
