# -*- coding: utf-8 -*-
"""Absicherung, Betriebswirkung und Trailing für den Selektionsbefund

**26.09.2026**, Nutzerauftrag in dieser Reihenfolge:

    *"zuerst sichere die aktuelle messung ab dass diese auch zukuenftig
    gueltigkeit hat. Was du mir unterschlagen hast ist die UMLEGUNG und
    WIRKUNG AUF UNSER SYSTEM - haeufigkeit der Signale und deren Qualitaet -
    wie erfolgt die Ein-/Aufteilung auf den Hebel: 1. Einstieg und Lage
    2. zum pruefzeitpunkt gerechtfertigter Hebel - risiko chance."*

═══════════════════════════════════════════════════════════════════════
 TEIL 1 - ABSICHERUNG: gilt der Befund auch KUENFTIG?
═══════════════════════════════════════════════════════════════════════

B6 hat zwei Haelften geprueft - das sagt nichts darueber, ob der Effekt im
LETZTEN Jahr noch da ist. Ein Befund, der 2022 stark war und seit 2025
verschwunden ist, bestuende B6 und waere trotzdem wertlos.

    ➤ Gemessen wird JE JAHR. Ein Befund gilt kuenftig nur dann als
      belastbar, wenn er auch im JUENGSTEN Fenster steht.

═══════════════════════════════════════════════════════════════════════
 TEIL 2 - DIE UMLEGUNG AUF DAS SYSTEM
═══════════════════════════════════════════════════════════════════════

    Signale je Tag    aus der Schaerfe und der Ankerzahl
    Qualitaet         MFE/MAE und Trefferquote je Schaerfe
    ⭐ HEBELSTUFUNG   die Schaerfe IST die Abstufung (Nutzeridee):
                      je seltener und klarer das Signal, desto groesser
                      der vertretbare Hebel

⚠️ Die Hebelhoehe folgt NICHT aus MFE, sondern aus dem Verhaeltnis von
Chance zu Risiko - hier MFE/MAE - und aus der Trefferquote.

═══════════════════════════════════════════════════════════════════════
 TEIL 3 - TRAILING
═══════════════════════════════════════════════════════════════════════

Der Ertrag haengt an der Positionsfuehrung (Nutzerpunkt). Gemessen wird
ein Trailing-Stop: `k x ATR` unter dem hoechsten seit Einstieg erreichten
Kurs, Ausstieg bei Beruehrung oder am Horizontende.

    ⚠️ Der ERSTE Stop liegt ebenfalls bei k x ATR unter dem Einstieg -
    sonst waere der Vergleich mit dem festen Stop unfair.

⚠️ NUR LESEN.  python messe_trailing_und_betrieb.py [--symbole N]
"""
from __future__ import annotations

import os
import sys

import numpy as np
from scipy.signal import lfilter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import messnorm as N                                            # noqa: E402
from messe_reverse_scharfe_anstiege import lade_kurse           # noqa: E402
from messe_hebel_geometrie_neutral import atr_tag_relativ       # noqa: E402

EMA_L = 48                       # aus 2.606
HORIZONTE = (24, 72)
SCHAERFEN = (0.20, 0.05, 0.01, 0.001)
TRAIL = (0.5, 1.0, 1.5, 2.0)     # Trailing-Weite in ATR
VORLAUF = 5 * EMA_L
N_NULL = N.NULL_ZIEHUNGEN
NULL_PERZ = N.NULL_PERZENTIL
MIND_ANKER = 300
SAAT = 20260926


def ema(x, p):
    a = 2.0 / (p + 1.0)
    return lfilter([a], [1.0, -(1.0 - a)], x, zi=[(1.0 - a) * x[0]])[0]


def trailing(high, low, close, atr, weite, H):
    """-> R je Anker bei Trailing-Stop `weite` x ATR.

    ⚠️ Der Stop startet `weite x ATR` unter dem Einstieg und zieht mit dem
    hoechsten erreichten Kurs nach. Verrechnet wird in Einheiten des
    ANFANGSrisikos - so ist R mit den bisherigen Messungen vergleichbar.
    """
    n = len(close)
    idx = np.arange(n)
    risiko = np.maximum(weite * atr * close, 1e-12)
    stop = close - risiko
    hoechst = close.copy()
    fertig = np.zeros(n, bool)
    ausstieg = np.full(n, np.nan)
    for s in range(1, H + 1):
        j = np.minimum(idx + s, n - 1)
        offen = ~fertig
        # zuerst pruefen, ob der Stop in dieser Stunde faellt (konservativ)
        raus = offen & (low[j] <= stop)
        ausstieg[raus] = stop[raus]
        fertig |= raus
        # dann den Stop nachziehen
        neu = ~fertig
        hoechst = np.where(neu & (high[j] > hoechst), high[j], hoechst)
        stop = np.where(neu, np.maximum(stop, hoechst - risiko), stop)
    je = np.minimum(idx + H, n - 1)
    ausstieg = np.where(np.isnan(ausstieg), close[je], ausstieg)
    return (ausstieg - close) / risiko


def main() -> int:
    grenze = None
    if "--symbole" in sys.argv:
        grenze = int(sys.argv[sys.argv.index("--symbole") + 1])

    print("=" * 100)
    print("ABSICHERUNG, BETRIEBSWIRKUNG UND TRAILING")
    print("=" * 100)
    print("  Merkmal: ema_abstand_atr mit EMA %d h (aus 2.606)" % EMA_L)

    kurse = lade_kurse(grenze)
    alle = set()
    for (s, *_r) in kurse.values():
        alle.update(s)
    sl = sorted(alle); sid = {s: i for i, s in enumerate(sl)}
    jahr_je_stunde = np.array([int(x[:4]) for x in sl])
    print("  %d Symbole · %d Stunden" % (len(kurse), len(sl)), flush=True)

    rng = np.random.default_rng(SAAT)
    for H in HORIZONTE:
        G, W, MFE, MAE, TR = [], [], [], [], {t: [] for t in TRAIL}
        for sym, (st, h, l, cc, v) in kurse.items():
            if sym.upper() == "BTC":
                continue
            idx = np.array([sid[x] for x in st], np.int64)
            atr = atr_tag_relativ(h, l, cc)
            e = ema(cc, EMA_L)
            with np.errstate(divide="ignore", invalid="ignore"):
                w = (cc - e) / np.maximum(atr * cc, 1e-12)
            n_ = len(cc)
            ii = np.arange(n_)
            hoch = np.full(n_, -np.inf); tief = np.full(n_, np.inf)
            for s2 in range(1, H + 1):
                j = np.minimum(ii + s2, n_ - 1)
                hoch = np.maximum(hoch, h[j]); tief = np.minimum(tief, l[j])
            with np.errstate(divide="ignore", invalid="ignore"):
                mfe = (hoch / np.maximum(cc, 1e-12) - 1.0) / np.maximum(atr, 1e-9)
                mae = (tief / np.maximum(cc, 1e-12) - 1.0) / np.maximum(atr, 1e-9)
            gu = np.isfinite(atr) & (atr > 0) & np.isfinite(w) & np.isfinite(mfe)
            gu[:VORLAUF] = False
            gu[max(0, n_ - H):] = False
            sel = np.flatnonzero(gu)
            if not len(sel):
                continue
            G.append(idx[sel]); W.append(w[sel])
            MFE.append(mfe[sel]); MAE.append(mae[sel])
            for t in TRAIL:
                TR[t].append(trailing(h, l, cc, atr, t, H)[sel])
        G = np.concatenate(G); W = np.concatenate(W)
        MFE = np.concatenate(MFE); MAE = np.concatenate(MAE)
        TR = {t: np.concatenate(x) for t, x in TR.items()}
        n = len(G)
        jahre = jahr_je_stunde[G]
        tage_gesamt = len(np.unique(G // 24))
        print()
        print("=" * 100)
        print("HORIZONT %d h (%d Tage) · %d Anker · %d Tage"
              % (H, H // 24, n, tage_gesamt), flush=True)

        # ══ TEIL 1: ABSICHERUNG - gilt es JE JAHR? ══════════════════
        print()
        print("  TEIL 1  ABSICHERUNG: gilt der Befund in JEDEM Jahr?")
        print("  (Schaerfe 1 %, MFE der Auswahl gegen Zufallsauswahl "
              "gleicher Groesse)")
        print("    %-6s %9s %9s %9s %9s  %s"
              % ("Jahr", "Anker", "MFE", "Band90", "MFE/MAE", "Urteil"))
        for j in sorted(set(jahre.tolist())):
            m = jahres = jahre == j
            if m.sum() < 20000:
                continue
            k = max(MIND_ANKER, int(round(0.01 * m.sum())))
            pos = np.flatnonzero(m & np.isfinite(W))
            if len(pos) < k:
                continue
            ordn = pos[np.argsort(W[pos])[::-1][:k]]
            nb = [float(MFE[rng.choice(pos, size=k, replace=False)].mean())
                  for _ in range(N_NULL)]
            b90 = float(np.percentile(np.array(nb), NULL_PERZ))
            mf, ma = float(MFE[ordn].mean()), float(MAE[ordn].mean())
            print("    %-6d %9d %9.3f %9.3f %9.2f  %s"
                  % (j, int(m.sum()), mf, b90, mf / max(abs(ma), 1e-9),
                     "✔ ueber Band" if mf > b90 else "⛔ IM BAND"))

        # ══ TEIL 2: DIE UMLEGUNG AUF DAS SYSTEM ═════════════════════
        print()
        print("  TEIL 2  UMLEGUNG: Signale je Tag, Qualitaet, Hebelstufung")
        print("    %-9s %9s %9s %9s %9s %9s"
              % ("Schaerfe", "Anker", "Sig./Tag", "MFE", "MFE/MAE",
                 "Treffer2R"))
        for sch in SCHAERFEN:
            k = max(MIND_ANKER, int(round(sch * n)))
            pos = np.flatnonzero(np.isfinite(W))
            ordn = pos[np.argsort(W[pos])[::-1][:k]]
            mf, ma = float(MFE[ordn].mean()), float(MAE[ordn].mean())
            tr2 = float((MFE[ordn] >= 2.0).mean())
            print("    %8.1f%% %9d %9.1f %9.3f %9.2f %8.1f%%"
                  % (100 * sch, k, k / max(tage_gesamt, 1), mf,
                     mf / max(abs(ma), 1e-9), 100 * tr2))

        # ══ TEIL 3: TRAILING ════════════════════════════════════════
        print()
        print("  TEIL 3  TRAILING: E[R] je Trailing-Weite und Schaerfe")
        print("    ⚠️ R in Einheiten des ANFANGSrisikos (Weite x ATR)")
        print("    %-9s %s" % ("Schaerfe",
                               " ".join("%10s" % ("%.1f ATR" % t)
                                        for t in TRAIL)))
        for sch in SCHAERFEN:
            k = max(MIND_ANKER, int(round(sch * n)))
            pos = np.flatnonzero(np.isfinite(W))
            ordn = pos[np.argsort(W[pos])[::-1][:k]]
            zeile = []
            for t in TRAIL:
                r = TR[t][ordn]
                nb = [float(TR[t][rng.choice(pos, size=k, replace=False)].mean())
                      for _ in range(N_NULL)]
                b90 = float(np.percentile(np.array(nb), NULL_PERZ))
                w = float(r.mean())
                zeile.append("%+9.4f%s" % (w, "*" if w > b90 else " "))
            print("    %8.1f%% %s" % (100 * sch, " ".join(zeile)))
        # Vergleich: der Durchschnitt aller Anker
        zeile = []
        for t in TRAIL:
            zeile.append("%+9.4f " % float(TR[t].mean()))
        print("    %8s %s" % ("ALLE", " ".join(zeile)))
        print("    (* = ueber dem Nullband der Zufallsauswahl gleicher "
              "Groesse)")
    print()
    print("  ⚠️ Ein positives E[R] beim Trailing ist noch KEIN Ertrag im")
    print("     Betrieb: Gebuehren und Finanzierung bleiben draussen")
    print("     (Regel 2), und die Ausfuehrbarkeit ist ungeprueft.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
