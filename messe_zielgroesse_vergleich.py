# -*- coding: utf-8 -*-
"""E[R] gegen MFE/MAE gegen die SYMMETRISCHE BARRIERE - was misst besser?

**27.09.2026**, Nutzerauftrag: *"im alten System BLOCK hast du E[R]
genommen - aber pruefe noch einmal ob MFE/MAE die bessere Wahl ist."*

═══════════════════════════════════════════════════════════════════════
 ⚠️⚠️ DER MANGEL AN MEINER EIGENEN MESSUNG (2.642)
═══════════════════════════════════════════════════════════════════════

`mfe_mae_zeit` in `messe_zielgroesse.py` nimmt das MAXIMUM und das
MINIMUM ueber das Fenster - und IGNORIERT DIE REIHENFOLGE.

    Faellt der Kurs erst um 1 ATR und steigt DANN um 1 ATR, zeigt
    MFE/MAE eine schoene Symmetrie. Im Betrieb waere die Position
    laengst ausgestoppt gewesen.

⚠️ `messe_selektion.mfe_mae` hat genau das adressiert (*"Das Ereignis
verlangt die REIHENFOLGE"*) - meine Fassung nicht. Das ist ein Mangel
von 2.642, kein Randfall.

═══════════════════════════════════════════════════════════════════════
 DIE DREI KANDIDATEN
═══════════════════════════════════════════════════════════════════════

                          reihenfolge-  regel-   Ausgaenge
                          treu          frei
    E[R]                  ✔             ⛔        drei
                          Barrieren     Stop, Ziel/CRV drin
    MFE/MAE               ⛔            ✔         keine
                          nur Extrema
    symm. Barriere        ✔             ✔ *       drei
    P(+k ATR vor -k ATR)  Barrieren     * bis auf die Skala k

⭐ Die symmetrische Barriere hat BEIDES. Und sie erfuellt 2.586 (*Kelly
setzt zwei Ausgaenge voraus, real sind es drei*), weil sie Ziel, Stop und
OFFEN unterscheidet.

⚠️ NUR LESEN.  python messe_zielgroesse_vergleich.py [--symbole N]
"""
from __future__ import annotations

import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import messnorm as N                                            # noqa: E402
from hebel_neubau import pruefe_quellen                         # noqa: E402
from messe_reverse_scharfe_anstiege import lade_kurse           # noqa: E402
from messe_hebel_geometrie_neutral import (                     # noqa: E402
    atr_tag_relativ, ausgaenge)
from messe_trailing_und_betrieb import ema                      # noqa: E402
from messe_hebel_neudimension import EMA_L, VORLAUF             # noqa: E402
from messe_zielgroesse import mfe_mae_zeit                      # noqa: E402

H = 24
K_ATR = 1.0                 # Skala der Barriere - der einzige Parameter
CRV_ER = 1.5                # nur fuer den E[R]-Arm, wie in 2.597/2.604
ANTEIL = 0.01
MAE_MIN = 0.05
SAAT = 20260927


def mfe_mae_reihenfolge(high, low, close, atr, H, k=K_ATR):
    """MFE und MAE MIT Reihenfolge: nach dem ersten Barrierentreffer ist
    Schluss.

    ⚠️ Das ist der Unterschied zu `mfe_mae_zeit`: dort laeuft das Fenster
    voll durch, egal was dazwischen passiert. Hier endet die Beobachtung,
    wenn der Kurs -k ATR erreicht - so wie eine echte Position enden
    wuerde."""
    n = len(close)
    idx = np.arange(n)
    stop = close * (1.0 - k * atr)
    lauf_h = np.full(n, -np.inf)
    lauf_t = np.full(n, np.inf)
    fertig = np.zeros(n, bool)
    for s in range(1, H + 1):
        j = np.minimum(idx + s, n - 1)
        offen = ~fertig
        lauf_h = np.where(offen, np.maximum(lauf_h, high[j]), lauf_h)
        lauf_t = np.where(offen, np.minimum(lauf_t, low[j]), lauf_t)
        fertig |= offen & (low[j] <= stop)
    with np.errstate(divide="ignore", invalid="ignore"):
        mfe = (lauf_h / np.maximum(close, 1e-12) - 1.0) / np.maximum(atr, 1e-9)
        mae = (lauf_t / np.maximum(close, 1e-12) - 1.0) / np.maximum(atr, 1e-9)
    return mfe, mae


def main() -> int:
    grenze = None
    if "--symbole" in sys.argv:
        grenze = int(sys.argv[sys.argv.index("--symbole") + 1])
    # ⚠️ Der Riegel aus 2.643: keine Spot- oder Ertragsgroesse.
    pruefe_quellen("ema_abstand_atr", "mfe", "mae", "barriere")

    print("=" * 106)
    print("E[R] GEGEN MFE/MAE GEGEN DIE SYMMETRISCHE BARRIERE")
    print("=" * 106)
    print("  " + N.standardzeile())
    print("  H%d · Barriere +-%.2f ATR · E[R]-Arm mit CRV %.1f"
          % (H, K_ATR, CRV_ER))
    print()

    kurse = lade_kurse(grenze)
    alle = set()
    for (s, *_r) in kurse.values():
        alle.update(s)
    sl = sorted(alle); sid = {s: i for i, s in enumerate(sl)}
    G, W = [], []
    Z = {k: [] for k in ("mfe_ohne", "mae_ohne", "mfe_mit", "mae_mit",
                         "barriere", "er")}
    for sym, (st, h, l, cc, v) in kurse.items():
        if sym.upper() == "BTC":
            continue
        gi = np.array([sid[x] for x in st], np.int64)
        atr = atr_tag_relativ(h, l, cc)
        e = ema(cc, EMA_L)
        with np.errstate(divide="ignore", invalid="ignore"):
            w = (cc - e) / np.maximum(atr * cc, 1e-12)
        # ── ohne Reihenfolge (die Fassung aus 2.642) ─────────────────
        mf0, ma0, _z = mfe_mae_zeit(h, l, cc, atr, H)
        # ── mit Reihenfolge ─────────────────────────────────────────
        mf1, ma1 = mfe_mae_reihenfolge(h, l, cc, atr, H)
        # ── symmetrische Barriere: +k ATR vor -k ATR? ───────────────
        stop_rel = K_ATR * atr
        zi, so, _ro, gu_b, _gl = ausgaenge(h, l, cc, stop_rel, stop_rel, H)
        # ── E[R] mit CRV 1,5, wie in 2.597/2.604 ────────────────────
        zi2, so2, ro2, gu_e, _g2 = ausgaenge(h, l, cc, stop_rel,
                                             CRV_ER * stop_rel, H)
        er = np.where(zi2, CRV_ER, np.where(so2, -1.0, ro2))
        gu = (np.isfinite(atr) & (atr > 0) & np.isfinite(w)
              & np.isfinite(mf0) & np.isfinite(mf1) & gu_b & gu_e)
        gu[:VORLAUF] = False
        gu[max(0, len(cc) - H):] = False
        s2 = np.flatnonzero(gu)
        if len(s2) < 500:
            continue
        G.append(gi[s2]); W.append(w[s2])
        Z["mfe_ohne"].append(mf0[s2]); Z["mae_ohne"].append(ma0[s2])
        Z["mfe_mit"].append(mf1[s2]); Z["mae_mit"].append(ma1[s2])
        Z["barriere"].append(zi[s2].astype(float))
        Z["er"].append(er[s2])
    G = np.concatenate(G); W = np.concatenate(W)
    Z = {k: np.concatenate(v) for k, v in Z.items()}
    tag = G // 24
    n = len(G)
    print("  %d Anker · %d Tage · %d Symbole"
          % (n, len(np.unique(tag)), len(kurse)), flush=True)
    print()

    # ══ TEIL 1: WIE OFT KOMMT DER RUECKLAUF ZUERST? ══════════════════
    print("=" * 106)
    print("TEIL 1 - DER MANGEL VON 2.642: wie oft kommt MAE VOR MFE?")
    print()
    verschieden = np.abs(Z["mfe_ohne"] - Z["mfe_mit"]) > 1e-9
    print("  Anker, bei denen die Reihenfolge das MFE aendert: %d (%.1f %%)"
          % (int(verschieden.sum()), 100 * verschieden.mean()))
    print("  mittleres MFE ohne Reihenfolge: %+.4f ATR"
          % Z["mfe_ohne"].mean())
    print("  mittleres MFE MIT Reihenfolge:  %+.4f ATR  (%.1f %% weniger)"
          % (Z["mfe_mit"].mean(),
             100 * (1 - Z["mfe_mit"].mean() / max(Z["mfe_ohne"].mean(), 1e-9))))
    print()
    print("  ➤ %s" % ("⚠️ der Mangel ist erheblich - 2.642 gehoert "
                      "eingeschraenkt"
                      if verschieden.mean() > 0.15
                      else "der Mangel ist klein"))

    # ══ TEIL 2: WELCHE GROESSE ORDNET DIE LAGE AM SCHAERFSTEN? ═══════
    print()
    print("=" * 106)
    print("TEIL 2 - WELCHE ZIELGROESSE ORDNET DIE LAGE AM SCHAERFSTEN?")
    print("  ⭐ Massstab ist Cohens d - z waechst mit der Stichprobe (2.642)")
    print()
    rng = np.random.default_rng(SAAT)
    pool = {}
    for i_ in range(n):
        pool.setdefault(int(tag[i_]), []).append(i_)
    pool = {t: np.array(v) for t, v in pool.items()}
    k = max(50, int(round(ANTEIL * n)))
    o = np.argsort(W, kind="stable")[:k]
    maske = np.zeros(n, bool); maske[o] = True
    je = {int(t): int(c) for t, c in
          zip(*np.unique(tag[maske], return_counts=True))}
    ziehungen = []
    for _ in range(N.NULL_ZIEHUNGEN):
        a = []
        for t, c in je.items():
            pl = pool.get(t)
            if pl is not None and len(pl):
                a.append(rng.choice(pl, size=min(c, len(pl)), replace=False))
        if a:
            ziehungen.append(np.concatenate(a))

    groessen = {
        "MFE/MAE ohne Reihenfolge":
            Z["mfe_ohne"] / np.maximum(np.abs(Z["mae_ohne"]), MAE_MIN),
        "MFE/MAE MIT Reihenfolge":
            Z["mfe_mit"] / np.maximum(np.abs(Z["mae_mit"]), MAE_MIN),
        "MAE allein (MIT Reihenf.)": Z["mae_mit"],
        "symm. Barriere (+-1 ATR)": Z["barriere"],
        "E[R] (CRV 1,5)": Z["er"],
    }
    print("  %-30s %12s %12s %10s %10s"
          % ("Zielgroesse", "echt", "Nullwelt", "z", "d"))
    for lab, x in groessen.items():
        echt = float(x[maske].mean())
        nb = np.array([float(x[i].mean()) for i in ziehungen])
        z = (echt - nb.mean()) / max(nb.std(), 1e-12)
        d = (echt - nb.mean()) / max(float(x.std()), 1e-12)
        print("  %-30s %+12.4f %+12.4f %+10.2f %+10.3f"
              % (lab, echt, nb.mean(), z, d), flush=True)

    print()
    print("  ⚠️ Gebuehren und Finanzierung sind NICHT eingerechnet (Regel 2).")
    print("  ⚠️ Die Barriere ist symmetrisch (+-%.2f ATR) und damit bis auf"
          % K_ATR)
    print("     die SKALA parameterfrei - das CRV 1,5 im E[R]-Arm ist es "
          "nicht.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
