# -*- coding: utf-8 -*-
"""Gegenpruefung der A-Kombinationen: Mehrfachtesten und Zeitstabilitaet.

**27.09.2026**, Nutzerauftrag nach dem Lauf von `messe_a_faktoren.py`:
*"ja beides pruefen - Mehrfachtesten und Zeitstabilitaet"*.

═══════════════════════════════════════════════════════════════════════
 WARUM
═══════════════════════════════════════════════════════════════════════

`messe_a_faktoren.py` meldet Treffer gegen ein Band `g90`, das JE
KOMBINATION einzeln gerechnet ist. Die Schleife testet aber

    2 A-Faktoren x 8 B-Faktoren x 2 Raender = 32 Kombinationen je Zelle

⛔ Das Band adjustiert NICHT fuer diese 32 Versuche - genau das verlangt
P5. Gezaehlt ueber zwei vollstaendige Zellen: 20 Treffer bei 64
Versuchen, erwartet 6,4 (p < 0,0001). Als KOLLEKTIVbefund also klar mehr
als Zufall - aber welche EINZELNE Zelle gilt, sagt das nicht.

⚠️⚠️ Und die Zeitstabilitaet hat am 27.09. bereits ZWEI Befunde gekippt
(2.633 Hebelstufung, 2.640 Betriebsschwelle). Sie ist hier Pflicht, nicht
Kuer - besonders bei 4.807 Ankern ueber fuenf Jahre.

⚠️ NUR LESEN.  python pruefe_a_kombinationen.py [--symbole N]
"""
from __future__ import annotations

import datetime as dt
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import messnorm as N                                            # noqa: E402
from hebel_neubau import pruefe_quellen                         # noqa: E402
from messe_a_faktoren import (                                  # noqa: E402
    a_faktoren, K_ATR, MIND_JE_FUENFTEL, N_NULL, NULL_PERZ)
from messe_hebel_geometrie_neutral import (                     # noqa: E402
    atr_tag_relativ, ausgaenge, STOP_MIN, STOP_MAX)
from messe_reverse_scharfe_anstiege import (                    # noqa: E402
    lade_kurse, merkmale_je_symbol)

CRV, H = 1.5, 6             # die Zelle mit den staerksten Treffern
SAAT = 20260927
# Die Kombinationen aus dem Lauf, die ueber Band UND ueber null lagen
PRUEFEN = (("rsi", "ema_abstand_atr", 0),
           ("rsi", "rsi_umkehr", 0),
           ("rsi", "trendstruktur", 0),
           ("rsi", "ema_steigung", 0),
           ("momentum_kurz", "ema_abstand_atr", 0),
           ("momentum_kurz", "trendstruktur", 0))


def fuenftel(stunde, wert):
    """Fuenftel JE STUNDE - der Querschnitt, nicht die Zeitreihe."""
    gut = np.isfinite(wert)
    if gut.sum() < 100:
        return None
    idx = np.flatnonzero(gut)
    o = np.lexsort((wert[idx], stunde[idx]))
    idx = idx[o]
    st = stunde[idx]
    grenzen = np.flatnonzero(np.diff(st)) + 1
    f = np.empty(len(idx), np.int64)
    start = 0
    for ende in list(grenzen) + [len(idx)]:
        k = ende - start
        if k >= 5:
            f[start:ende] = np.minimum((np.arange(k) * 5) // k, 4)
        else:
            f[start:ende] = -1
        start = ende
    ok = f >= 0
    return idx[ok], f[ok]


def main() -> int:
    grenze = None
    if "--symbole" in sys.argv:
        grenze = int(sys.argv[sys.argv.index("--symbole") + 1])
    pruefe_quellen("rsi", "momentum_kurz", "ema_abstand_atr", "trendstruktur",
                   "rsi_umkehr", "ema_steigung")

    print("=" * 104)
    print("GEGENPRUEFUNG DER A-KOMBINATIONEN")
    print("=" * 104)
    print("  " + N.standardzeile())
    print("  Zelle CRV %.1f / H%d · Stop k = %.1f x ATR" % (CRV, H, K_ATR))
    print()

    kurse = lade_kurse(grenze)
    alle = set()
    for (s, *_r) in kurse.values():
        alle.update(s)
    sl = sorted(alle); sid = {s: i for i, s in enumerate(sl)}
    NAMEN = ("rsi", "momentum_kurz", "rsi_umkehr", "rsi_aenderung",
             "ema_lage", "ema_steigung", "ema_abstand_atr", "bandenge",
             "trendstruktur")
    G, R = [], []
    MM = {k: [] for k in NAMEN}
    for sym, (st, h, l, cc, v) in kurse.items():
        if sym.upper() == "BTC":
            continue
        idx = np.array([sid[s] for s in st], np.int64)
        atr = atr_tag_relativ(h, l, cc)
        stop = np.clip(K_ATR * atr, STOP_MIN, STOP_MAX)
        zz, ss, ro, gu, _g = ausgaenge(h, l, cc, stop, CRV * stop, H)
        mk = dict(a_faktoren(cc, atr))
        mr = merkmale_je_symbol(sym, st, h, l, cc, v, {}, {})
        for k, val in mr.items():
            if k in NAMEN:
                mk[k] = val
        for k in NAMEN:
            if k not in mk:
                mk[k] = np.full(len(cc), np.nan)
            gu = gu & np.isfinite(mk[k])
        sel = np.flatnonzero(gu)
        if not len(sel):
            continue
        G.append(idx[sel])
        R.append(np.where(zz[sel], CRV,
                          np.where(ss[sel], -1.0, np.nan_to_num(ro[sel]))))
        for k in NAMEN:
            MM[k].append(mk[k][sel])
    G = np.concatenate(G); R = np.concatenate(R)
    MM = {k: np.concatenate(v) for k, v in MM.items()}
    n = len(G)
    tag = G // 24
    ende = dt.date(2026, 9, 27)
    start = ende - dt.timedelta(days=int(tag.max()))
    jahr = np.array([(start + dt.timedelta(days=int(t))).year for t in tag])
    print("  %d Anker · %d Tage · E[R] gesamt %+.5f"
          % (n, len(np.unique(tag)), float(R.mean())), flush=True)
    print()

    rng = np.random.default_rng(SAAT)
    # ── die Fuenftel einmal je Merkmal ───────────────────────────────
    f5 = {}
    for k in NAMEN:
        fz = fuenftel(G, MM[k])
        if fz is not None:
            f5[k] = fz

    # ══ TEIL 1: DAS ADJUSTIERTE BAND (P5) ════════════════════════════
    print("=" * 104)
    print("TEIL 1 - DAS BAND, ADJUSTIERT FUER 32 VERSUCHE")
    print("  ⭐ Das Band aus dem Lauf gilt je EINZELNER Kombination. Hier")
    print("     wird das BESTE von 32 Zufallsschnitten gezogen - so oft,")
    print("     wie tatsaechlich gesucht wurde.")
    print()
    print("  %-38s %9s %12s %12s %12s  %s"
          % ("Kombination", "Anker", "E[R]", "Zugewinn", "Band(32)",
             "Urteil"))
    ergebnis = {}
    for a_name, b_name, rand in PRUEFEN:
        if a_name not in f5 or b_name not in f5:
            continue
        ia, fa = f5[a_name]
        top_a = np.zeros(n, bool); top_a[ia[fa == 4]] = True
        ib, fb = f5[b_name]
        top_b = np.zeros(n, bool); top_b[ib[fb == rand]] = True
        beide = top_a & top_b
        if beide.sum() < MIND_JE_FUENFTEL:
            continue
        er_a = float(R[top_a].mean())
        er_ab = float(R[beide].mean())
        zug = er_ab - er_a
        quote = beide.sum() / max(top_a.sum(), 1)
        # ⭐ Bestes von 32 - genau so oft, wie gesucht wurde
        bestes = []
        for _ in range(N_NULL):
            werte = []
            for _v in range(32):
                z = rng.random(n)
                sw = np.quantile(z[top_a], quote)
                m = top_a & (z <= sw)
                if m.sum() >= MIND_JE_FUENFTEL:
                    werte.append(float(R[m].mean()) - er_a)
            if werte:
                bestes.append(max(werte))
        b32 = float(np.percentile(np.array(bestes), NULL_PERZ))
        haelt = zug > b32
        ergebnis[(a_name, b_name, rand)] = (beide, er_ab, zug, b32, haelt)
        print("  %-38s %9d %+12.5f %+12.5f %+12.5f  %s"
              % ("%s ∧ %s %s" % (a_name, b_name,
                                 "unten" if rand == 0 else "oben"),
                 int(beide.sum()), er_ab, zug, b32,
                 "✔ haelt" if haelt else "⛔ im Band(32)"), flush=True)

    # ══ TEIL 2: ZEITSTABILITAET ══════════════════════════════════════
    print()
    print("=" * 104)
    print("TEIL 2 - ZEITSTABILITAET  (sie hat am 27.09. zwei Befunde "
          "gekippt)")
    print()
    JJ = (2022, 2023, 2024, 2025, 2026)
    print("  %-38s %s  %s"
          % ("Kombination", " ".join("%13d" % j for j in JJ), "Urteil"))
    for schluessel, (beide, er_ab, zug, b32, haelt) in ergebnis.items():
        a_name, b_name, rand = schluessel
        zeil, posi, zaehl = [], 0, 0
        for j in JJ:
            m = beide & (jahr == j)
            if m.sum() < 60:
                zeil.append("     -       ")
                continue
            e = float(R[m].mean())
            zaehl += 1
            posi += 1 if e > 0 else 0
            zeil.append("%+8.5f(%3d)" % (e, int(m.sum())))
        print("  %-38s %s  %d von %d positiv"
              % ("%s ∧ %s" % (a_name, b_name), " ".join("%13s" % x
                                                        for x in zeil),
                 posi, zaehl), flush=True)

    print()
    print("  ⚠️ Gebuehren und Finanzierung sind NICHT eingerechnet (Regel 2).")
    print("  ⚠️ Die Sperre aus 2.602 ist hier NICHT angewandt - der Lauf")
    print("     misst auf der vollen Menge. Die Zahlen sind deshalb nicht")
    print("     bitgleich mit `messe_a_faktoren.py`, die ORDNUNG zaehlt.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
