# -*- coding: utf-8 -*-
"""Die Umlegung auf den ECHTBETRIEB: gilt 2.607 auch auf der Watchlist?

**26.09.2026**, Nutzerauftrag: *"dann simulation auf unser System -
Watchlist mit Hebel umlegen, Echtbetrieb hier sind es nicht 116 Symbole und
zusaetzlich den aktuellen Abdeckungsgrad auf die Bewertungen der Assets
(haben alle Assets die Bewertung die wir benoetigen?)."*

═══════════════════════════════════════════════════════════════════════
 DIE ZWEI UNTERSCHIEDE ZUM MESSLAUF
═══════════════════════════════════════════════════════════════════════

    ⚠️ ABDECKUNG    Die Hebel-Watchlist (`asset_hebel_settings`) hat 43
                    Symbole, davon haben nur 28 Stundenkurse - 65 %.
                    Ein Drittel ist NICHT bewertbar.

    ⚠️⚠️ RANGFOLGE  Die Schaerfe ist ein QUERSCHNITTS-Perzentil INNERHALB
                    der Stunde. Bei 116 Symbolen sind 1 % rund 1,2
                    Symbole je Stunde, bei 28 nur 0,28 - seltener als
                    eines. Die Auswahl wird damit GROEBER, und ob der
                    Befund das ueberlebt, ist eine eigene Frage.

➤ Deshalb wird BEIDES gemessen: dieselbe Messung auf der Watchlist, und
  zusaetzlich eine ABSOLUTE Schwelle statt eines Perzentils - denn die
  ist im Betrieb die brauchbarere Form.

⚠️ NUR LESEN. `tradinginfotool.db` wird nur mit `mode=ro` gelesen.

    python messe_betrieb_umlegung.py
"""
from __future__ import annotations

import os
import sqlite3
import sys

import numpy as np
from scipy.signal import lfilter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import messnorm as N                                            # noqa: E402
from messe_reverse_scharfe_anstiege import lade_kurse           # noqa: E402
from messe_hebel_geometrie_neutral import atr_tag_relativ       # noqa: E402
from messe_trailing_und_betrieb import ema, trailing            # noqa: E402

BETRIEB_DB = os.path.join("data", "tradinginfotool.db")
EMA_L, VORLAUF, H = 48, 240, 72
SCHAERFEN = (0.20, 0.05, 0.01)
#: absolute Schwellen in ATR - die betriebstaugliche Form
SCHWELLEN = (1.0, 1.5, 2.0, 3.0)
TRAIL_W = 1.0
N_NULL = N.NULL_ZIEHUNGEN
NULL_PERZ = N.NULL_PERZENTIL
MIND = 300
SAAT = 20260926


def watchlist():
    c = sqlite3.connect("file:%s?mode=ro" % BETRIEB_DB, uri=True)
    try:
        s = [r[0] for r in c.execute(
            "SELECT symbol FROM asset_hebel_settings "
            "WHERE hebel_pruefung_erlaubt=1")]
    finally:
        c.close()
    return set(s)


def sammle(symbole, etikett):
    kurse = lade_kurse(None)
    da = {k: v for k, v in kurse.items()
          if (symbole is None or k in symbole)
          and (symbole is not None or k.upper() != "BTC")}
    alle = set()
    for (s, *_r) in da.values():
        alle.update(s)
    sl = sorted(alle); sid = {s: i for i, s in enumerate(sl)}
    G, W, R, MFE, MAE = [], [], [], [], []
    for sym, (st, h, l, cc, v) in da.items():
        idx = np.array([sid[x] for x in st], np.int64)
        atr = atr_tag_relativ(h, l, cc)
        e = ema(cc, EMA_L)
        with np.errstate(divide="ignore", invalid="ignore"):
            w = (cc - e) / np.maximum(atr * cc, 1e-12)
        n_ = len(cc); ii = np.arange(n_)
        hoch = np.full(n_, -np.inf); tief = np.full(n_, np.inf)
        for s2 in range(1, H + 1):
            j = np.minimum(ii + s2, n_ - 1)
            hoch = np.maximum(hoch, h[j]); tief = np.minimum(tief, l[j])
        with np.errstate(divide="ignore", invalid="ignore"):
            mfe = (hoch / np.maximum(cc, 1e-12) - 1.0) / np.maximum(atr, 1e-9)
            mae = (tief / np.maximum(cc, 1e-12) - 1.0) / np.maximum(atr, 1e-9)
        gu = np.isfinite(atr) & (atr > 0) & np.isfinite(w) & np.isfinite(mfe)
        gu[:VORLAUF] = False; gu[max(0, n_ - H):] = False
        sel = np.flatnonzero(gu)
        if not len(sel):
            continue
        G.append(idx[sel]); W.append(w[sel]); MFE.append(mfe[sel])
        MAE.append(mae[sel])
        R.append(trailing(h, l, cc, atr, TRAIL_W, H)[sel])
    if not G:
        return None
    aus = (np.concatenate(G), np.concatenate(W), np.concatenate(R),
           np.concatenate(MFE), np.concatenate(MAE), len(da))
    print("  %-22s %3d Symbole · %d Anker · %d Tage"
          % (etikett, aus[5], len(aus[0]), len(np.unique(aus[0] // 24))),
          flush=True)
    return aus


def main() -> int:
    print("=" * 100)
    print("DIE UMLEGUNG AUF DEN ECHTBETRIEB")
    print("=" * 100)

    wl = watchlist()
    kurse = lade_kurse(None)
    mit = sorted(s for s in wl if s in kurse)
    ohne = sorted(s for s in wl if s not in kurse)
    print("  Hebel-Watchlist: %d Symbole freigegeben" % len(wl))
    print("  ⭐ ABDECKUNG: %d mit Stundenkursen (%.0f %%), %d OHNE"
          % (len(mit), 100.0 * len(mit) / max(len(wl), 1), len(ohne)))
    print("     nicht bewertbar: %s" % ", ".join(ohne))
    print()

    # ── die Liquiditaet je Watchlist-Symbol ──────────────────────────
    #
    # ⭐ Eine Liquiditaetsschwelle ist KEIN Asset-Vorurteil (Regel 3),
    # sondern eine PHYSISCHE Handelsgrenze: bei 13.000 USD Stundenumsatz
    # waere ein Trade von 5.000 USD 38 % des Volumens - der Kurs bewegt
    # sich dann gegen einen selbst.
    import sqlite3 as _s3
    kk = _s3.connect("file:%s?mode=ro" % os.path.join("data",
                                                      "stundenkurse.db"),
                     uri=True)
    liq = {}
    for sym in mit:
        r = kk.execute("SELECT close, volumen FROM stundenkurse "
                       "WHERE symbol=? ORDER BY stunde DESC LIMIT 720",
                       (sym,)).fetchall()
        v = [x[0] * x[1] for x in r if x[0] and x[1]]
        if v:
            liq[sym] = float(np.median(v))
    kk.close()
    LIQ_GRENZE = 100_000.0
    liquide = sorted(s for s in mit if liq.get(s, 0) >= LIQ_GRENZE)
    print("  ⭐ LIQUIDITAET: %d von %d ueber %.0f USD/Stunde"
          % (len(liquide), len(mit), LIQ_GRENZE))
    print("     handelbar: %s" % ", ".join(liquide))
    print("     zu duenn:  %s"
          % ", ".join("%s(%.0fk)" % (s, liq.get(s, 0) / 1000)
                      for s in sorted(mit, key=lambda x: liq.get(x, 0))
                      if liq.get(s, 0) < LIQ_GRENZE))
    print()

    voll = sammle(None, "Messlauf (alle)")
    betr = sammle(set(mit), "Betrieb (Watchlist)")
    liqm = sammle(set(liquide), "Betrieb LIQUIDE")
    if voll is None or betr is None:
        return 1

    rng = np.random.default_rng(SAAT)
    for etikett, d in (("MESSLAUF (116 Symbole)", voll),
                       ("BETRIEB (Watchlist, 28)", betr),
                       ("BETRIEB LIQUIDE", liqm)):
        if d is None:
            continue
        G, W, R, MFE, MAE, nsym = d
        n = len(G)
        tage = len(np.unique(G // 24))
        print()
        print("=" * 100)
        print("%s · %d Symbole · %d Anker" % (etikett, nsym, n))
        print()
        print("  A) PERZENTIL-Schaerfe (wie 2.607)")
        print("     %-9s %8s %9s %9s %9s  %s"
              % ("Schaerfe", "Sig./Tag", "MFE", "MFE/MAE", "E[R]", "Urteil"))
        for sch in SCHAERFEN:
            k = max(MIND, int(round(sch * n)))
            pos = np.flatnonzero(np.isfinite(W))
            if len(pos) < k:
                continue
            ordn = pos[np.argsort(W[pos])[::-1][:k]]
            nb = [float(R[rng.choice(pos, size=k, replace=False)].mean())
                  for _ in range(N_NULL)]
            b90 = float(np.percentile(np.array(nb), NULL_PERZ))
            er = float(R[ordn].mean())
            mf, ma = float(MFE[ordn].mean()), float(MAE[ordn].mean())
            print("     %8.1f%% %8.1f %9.3f %9.2f %+9.4f  %s"
                  % (100 * sch, k / max(tage, 1), mf,
                     mf / max(abs(ma), 1e-9), er,
                     "✔ ueber Band" if er > b90 else "⛔ IM BAND"))
        print()
        print("  B) ABSOLUTE Schwelle in ATR - die betriebstaugliche Form")
        print("     %-9s %8s %8s %9s %9s  %s"
              % ("Schwelle", "Anker", "Sig./Tag", "MFE/MAE", "E[R]",
                 "Urteil"))
        for sw in SCHWELLEN:
            m = np.isfinite(W) & (W >= sw)
            if m.sum() < MIND:
                print("     %8.1f  %8d  (zu duenn)" % (sw, int(m.sum())))
                continue
            k = int(m.sum())
            pos = np.flatnonzero(np.isfinite(W))
            nb = [float(R[rng.choice(pos, size=k, replace=False)].mean())
                  for _ in range(N_NULL)]
            b90 = float(np.percentile(np.array(nb), NULL_PERZ))
            er = float(R[m].mean())
            mf, ma = float(MFE[m].mean()), float(MAE[m].mean())
            print("     %8.1f  %8d %8.2f %9.2f %+9.4f  %s"
                  % (sw, k, k / max(tage, 1), mf / max(abs(ma), 1e-9), er,
                     "✔ ueber Band" if er > b90 else "⛔ IM BAND"))
    print()
    print("  ⚠️ Die absolute Schwelle ist im Betrieb brauchbarer: ein")
    print("     Perzentil ueber 28 Symbole waehlt 0,28 Symbole je Stunde -")
    print("     seltener als eines, und die Rangfolge ist grob.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
