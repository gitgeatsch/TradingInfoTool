# -*- coding: utf-8 -*-
"""Traegt die Achse auf TAGESBASIS - der Betriebsfall.

**27.09.2026**, aus der Voranalyse zu Schritt 1.

Vorabfestlegung: `Basisinfos/Vorabfestlegung_28_Tagesbasis_27_09.md`

═══════════════════════════════════════════════════════════════════════
 WARUM DIESE MESSUNG NOETIG IST
═══════════════════════════════════════════════════════════════════════

Die gemessene Achse `ema_abstand_atr` beruht auf STUENDLICHEN Ankern mit
EMA ueber 48 STUNDEN. Der Betrieb hat ausschliesslich TAGESDATEN - keine
einzige stuendliche Kursreihe in 31 Tabellen (Voranalyse 27.09.).

⚠️ 2.616 beantwortet das NICHT: dort wurden nur die KERZEN groeber, die
ANKER und die EMA blieben stuendlich (`messe_aufloesung_und_fallback.py`
Zeilen 217, 130-134, 222).

═══════════════════════════════════════════════════════════════════════
 DER AUFBAU ZERLEGT ZWEI URSACHEN
═══════════════════════════════════════════════════════════════════════

    Arm 1   Merkmal aus Stunden, Anker jede Stunde   -> Referenz
    Arm 2   Merkmal aus Stunden, 1 Anker pro Tag     -> Kosten der
                                                        Ankerreduktion
    Arm 3   Merkmal aus TAGEN,   1 Anker pro Tag     -> BETRIEBSFALL

Differenz 1->2 ist die Ankerzahl, 2->3 ist die Aufloesung.

⭐ Die ZIELGROESSE bleibt stuendlich - sie ist die Wahrheit darueber, was
tatsaechlich passiert waere, und aendert sich nicht dadurch, dass der
Betrieb sie nicht sieht. Genau so lief 2.618 (Bewertung aus CoinGecko,
Ertrag auf Binance).

⚠️ NUR LESEN.  python messe_tagesbasis.py [--symbole N]
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

HZ, STOP, AUSL, ABST = 24, 1.00, 1.5, 0.5
# 2.606: 48 h ist das gemessene Optimum = 2 Tage. Eine Tages-EMA ueber
# 2 Punkte ist aber nicht dasselbe wie eine Stunden-EMA ueber 48.
TAGES_EMA = (2, 3, 5, 8, 13, 21)
ANTEIL = 0.01          # gleicher Auswahlanteil in ALLEN Armen (Falle 3)
SAAT = 20260927
# ⚠️ NUR fuer die Kausalitaetsprobe (--ohne-versatz): laesst den Anker von
# Tag k den Tageswert VON Tag k lesen - also in die Zukunft blicken. Das
# Ergebnis MUSS dann besser werden; wird es das nicht, ist der Versatz im
# Normalbetrieb wirkungslos und die Messung wertlos.
OHNE_VERSATZ = "--ohne-versatz" in sys.argv


def tagesreihe(st, h, l, cc):
    """Aggregiert die Stundenreihe zu TAGESKERZEN.

    ⚠️ Der Tagesschluessel kommt aus dem globalen Stundenindex, nicht aus
    einem Datumstext - so kann kein Zeitformatfehler entstehen (der hat
    am 26.09. schon einmal still null gemeinsame Stunden erzeugt)."""
    tag = st // 24
    ut, start = np.unique(tag, return_index=True)
    ende = np.append(start[1:], len(tag))
    th = np.array([h[a:b].max() for a, b in zip(start, ende)])
    tl = np.array([l[a:b].min() for a, b in zip(start, ende)])
    tc = np.array([cc[b - 1] for a, b in zip(start, ende)])
    return ut, th, tl, tc, start


def atr_aus_tageskerzen(h, l, c, fenster=14):
    """ATR aus echten Tageskerzen, relativ zum Kurs.

    ⚠️ Nicht `atr_tag_relativ` - die rechnet Stundenspannen mal Wurzel 24
    hoch. Hier sind die Kerzen schon Tage breit."""
    vt = np.maximum(h - l, np.maximum(
        np.abs(h - np.concatenate(([c[0]], c[:-1]))),
        np.abs(l - np.concatenate(([c[0]], c[:-1])))))
    out = np.full(len(c), np.nan)
    if len(c) <= fenster:
        return out
    roll = np.convolve(vt, np.ones(fenster) / fenster, mode="full")[:len(c)]
    out[fenster:] = roll[fenster - 1:-1]          # kausal: ohne heute
    with np.errstate(divide="ignore", invalid="ignore"):
        return out / np.maximum(c, 1e-12)


def main() -> int:
    grenze = None
    if "--symbole" in sys.argv:
        grenze = int(sys.argv[sys.argv.index("--symbole") + 1])

    print("=" * 104)
    print("TRAEGT DIE ACHSE AUF TAGESBASIS? - der Betriebsfall")
    print("=" * 104)
    print("  " + N.standardzeile())
    print("  Geometrie H%d / Stop %.2f ATR / Trailing %.1f / %.1f (2.628)"
          % (HZ, STOP, AUSL, ABST))
    print("  Auswahlanteil %.1f %% in ALLEN Armen (Falle 3)" % (100 * ANTEIL))
    print()

    kurse = lade_kurse(grenze)
    alle = set()
    for (s, *_r) in kurse.values():
        alle.update(s)
    sl = sorted(alle); sid = {s: i for i, s in enumerate(sl)}

    # je Arm: Listen von (globaler Stundenindex, W, kursprozent)
    G1, W1, P1 = [], [], []          # Stundenmerkmal, Stundenanker
    G2, W2, P2 = [], [], []          # Stundenmerkmal, Tagesanker
    G3 = {e: [] for e in TAGES_EMA}  # Tagesmerkmal, Tagesanker
    W3 = {e: [] for e in TAGES_EMA}
    P3 = {e: [] for e in TAGES_EMA}

    for sym, (st, h, l, cc, v) in kurse.items():
        if sym.upper() == "BTC":
            continue
        gi = np.array([sid[x] for x in st], np.int64)
        atr = atr_tag_relativ(h, l, cc)
        e48 = ema(cc, EMA_L)
        with np.errstate(divide="ignore", invalid="ignore"):
            w_std = (cc - e48) / np.maximum(atr * cc, 1e-12)
        _r, p, _g = trailing_mit_ausloeser(h, l, cc, atr, STOP, AUSL,
                                           ABST, HZ)
        gu = np.isfinite(atr) & (atr > 0) & np.isfinite(w_std) & np.isfinite(p)
        gu[:VORLAUF] = False
        gu[max(0, len(cc) - HZ):] = False

        # ── Arm 1 ────────────────────────────────────────────────────
        s1 = np.flatnonzero(gu)
        if len(s1):
            G1.append(gi[s1]); W1.append(w_std[s1]); P1.append(p[s1])

        # ── Tagesgeruest ─────────────────────────────────────────────
        ut, th, tl, tc, start = tagesreihe(gi, h, l, cc)
        if len(ut) < 40:
            continue
        # Der Anker sitzt auf der ERSTEN Stunde jedes Tages.
        anker = start
        gueltig = gu[anker]

        # ── Arm 2: Stundenmerkmal, aber nur an den Tagesankern ───────
        s2 = anker[gueltig]
        if len(s2):
            G2.append(gi[s2]); W2.append(w_std[s2]); P2.append(p[s2])

        # ── Arm 3: Merkmal aus TAGESKERZEN ───────────────────────────
        # ⚠️ KAUSAL: am Anker von Tag k darf nur bis Tag k-1 gelesen
        # werden. Deshalb werden die Tagesreihen um EINS versetzt.
        atr_t = atr_aus_tageskerzen(th, tl, tc)
        for el in TAGES_EMA:
            e_t = ema(tc, el)
            with np.errstate(divide="ignore", invalid="ignore"):
                w_t = (tc - e_t) / np.maximum(atr_t * tc, 1e-12)
            # Versatz: Wert von Tag k-1 gilt am Anker von Tag k
            w_v = (w_t.copy() if OHNE_VERSATZ
                   else np.concatenate(([np.nan], w_t[:-1])))
            ok = gueltig & np.isfinite(w_v)
            ok[:max(30, 5 * el)] = False
            if not ok.any():
                continue
            idx = anker[ok]
            G3[el].append(gi[idx]); W3[el].append(w_v[ok]); P3[el].append(p[idx])

    def bau(G, W, P):
        if not G:
            return None
        return (np.concatenate(G), np.concatenate(W), np.concatenate(P))

    a1 = bau(G1, W1, P1)
    a2 = bau(G2, W2, P2)
    a3 = {el: bau(G3[el], W3[el], P3[el]) for el in TAGES_EMA}

    print("  Arm 1 (Stundenmerkmal, Stundenanker): %d Anker" % len(a1[0]))
    print("  Arm 2 (Stundenmerkmal, Tagesanker):   %d Anker" % len(a2[0]))
    for el in TAGES_EMA:
        if a3[el]:
            print("  Arm 3, EMA %2d Tage:                   %d Anker"
                  % (el, len(a3[el][0])))
    print(flush=True)

    rng = np.random.default_rng(SAAT)

    def urteil(daten, k_anteil=ANTEIL, ziehungen=N.NULL_ZIEHUNGEN):
        """Ertrag der besten `anteil` gegen die tagestreue Nullwelt."""
        G, W, P = daten
        tag = G // 24
        n = len(W)
        k = max(50, int(round(k_anteil * n)))
        o = np.argsort(W, kind="stable")[:k]        # invers: niedrigste
        m = np.zeros(n, bool); m[o] = True
        pool = {}
        for i_ in range(n):
            pool.setdefault(int(tag[i_]), []).append(i_)
        pool = {t: np.array(v) for t, v in pool.items()}
        je = {int(t): int(c) for t, c in
              zip(*np.unique(tag[m], return_counts=True))}
        aus = []
        for _ in range(ziehungen):
            a = []
            for t, c in je.items():
                pl = pool.get(t)
                if pl is not None and len(pl):
                    a.append(rng.choice(pl, size=min(c, len(pl)),
                                        replace=False))
            if a:
                aus.append(float(P[np.concatenate(a)].mean()))
        nb = np.array(aus) if aus else np.zeros(1)
        return dict(n=n, k=k, er=100 * float(P[m].mean()),
                    band=100 * float(np.percentile(nb, N.NULL_PERZENTIL)),
                    tage=len(np.unique(tag)), proben=100 * nb)

    print("=" * 104)
    print("DIE DREI ARME")
    print()
    print("  %-34s %9s %8s %9s %12s %12s %10s  %s"
          % ("Arm", "Anker", "Tage", "Auswahl", "Ertrag %", "Nullband",
             "Abstand", "Urteil"))
    erg = {}
    for lab, d in (("1  Stundenmerkmal, Stundenanker", a1),
                   ("2  Stundenmerkmal, Tagesanker", a2)):
        u = urteil(d); erg[lab] = u
        print("  %-34s %9d %8d %9d %+12.4f %+12.4f %+10.4f  %s"
              % (lab, u["n"], u["tage"], u["k"], u["er"], u["band"],
                 u["er"] - u["band"], "✔" if u["er"] > u["band"]
                 else "⛔ im Band"), flush=True)
    proben3 = []
    for el in TAGES_EMA:
        if not a3[el]:
            continue
        lab = "3  Tagesmerkmal, EMA %2d Tage" % el
        u = urteil(a3[el]); erg[lab] = u; proben3.append(u["proben"])
        print("  %-34s %9d %8d %9d %+12.4f %+12.4f %+10.4f  %s"
              % (lab, u["n"], u["tage"], u["k"], u["er"], u["band"],
                 u["er"] - u["band"], "✔" if u["er"] > u["band"]
                 else "⛔ im Band"), flush=True)

    # ══ P5: sechs EMA-Laengen sind sechs Ziehungen ═══════════════════
    print()
    print("=" * 104)
    print("P5 - MEHRFACHTESTEN ueber die %d EMA-Laengen" % len(proben3))
    if proben3:
        arr = np.array(proben3)
        b = float(np.percentile(arr.max(axis=0), N.NULL_PERZENTIL))
        print("  Bestes-von-%d-Band: %+.4f %%" % (len(proben3), b))
        halten = [(lab, u) for lab, u in erg.items()
                  if lab.startswith("3") and u["er"] > b]
        print("  haltende Tages-Laengen: %s"
              % (", ".join(l.split("EMA")[1].strip() for l, _ in halten)
                 if halten else "⛔ KEINE"))
        if halten:
            best = max(halten, key=lambda x: x[1]["er"])
            print("  beste: %s mit %+.4f %%" % (best[0], best[1]["er"]))

    # ══ DIE ZERLEGUNG ════════════════════════════════════════════════
    print()
    print("=" * 104)
    print("DIE ZERLEGUNG - woran liegt ein Verlust?")
    print()
    e1 = erg["1  Stundenmerkmal, Stundenanker"]["er"]
    e2 = erg["2  Stundenmerkmal, Tagesanker"]["er"]
    beste3 = max((u["er"] for lab, u in erg.items() if lab.startswith("3")),
                 default=float("nan"))
    print("  Arm 1 -> Arm 2  (Ankerreduktion): %+.4f -> %+.4f  = %+.4f Pp"
          % (e1, e2, e2 - e1))
    print("  Arm 2 -> Arm 3  (Aufloesung):     %+.4f -> %+.4f  = %+.4f Pp"
          % (e2, beste3, beste3 - e2))
    print()
    # ⚠️ Das Urteil kommt aus dem P5-Band, nicht aus einem Einzelvergleich -
    # sechs Laengen sind sechs Ziehungen.
    traegt3 = bool(proben3) and any(
        u["er"] > float(np.percentile(np.array(proben3).max(axis=0),
                                      N.NULL_PERZENTIL))
        for lab, u in erg.items() if lab.startswith("3"))
    traegt2 = e2 > erg["2  Stundenmerkmal, Tagesanker"]["band"]
    if traegt3:
        print("  ➤ ✔ DER BETRIEBSFALL TRAEGT - Schritt 1 ist klein:")
        print("       Tages-EMA und Tages-ATR in marktrang.py, fertig.")
    elif traegt2:
        print("  ➤ ⛔ DIE AUFLOESUNG IST DAS PROBLEM. Mit Tagesankern traegt")
        print("       das STUNDENmerkmal noch, das TAGESmerkmal nicht.")
        print("       ➜ Stundendaten muessen in den Betrieb.")
    else:
        print("  ➤ ⛔ SCHON DIE ANKERZAHL IST DAS PROBLEM - Arm 2 liegt")
        print("       bereits im Band. ➜ Stundendaten muessen in den")
        print("       Betrieb, und die Signalzahlen aus 2.633 gelten NICHT")
        print("       fuer einen Betrieb mit einem Anker pro Tag.")
    if OHNE_VERSATZ:
        print()
        print("  ⚠️⚠️ DIESER LAUF LIEF MIT --ohne-versatz (Zukunftsblick).")
        print("     Er ist KEIN Ergebnis, sondern die Kausalitaetsprobe.")
        print("     Sein Ertrag MUSS ueber dem des normalen Laufs liegen.")
    print()
    print("  ⚠️ Gebuehren und Finanzierung sind NICHT eingerechnet (Regel 2).")
    print("  ⚠️ Die ZIELGROESSE ist in allen Armen dieselbe (stuendlich) -")
    print("     nur die BEWERTUNG unterscheidet sich. Das ist Absicht.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
