# -*- coding: utf-8 -*-
"""Die SELEKTION: sind die besten 1 Prozent der Lagen wirklich besser?

**26.09.2026** · Vorabfestlegung 20 · Nutzervorgabe:

    *"wir suchen einen Einstieg mit einer ZEITPUNKTMESSUNG - diese KANN nur
    die AUSGANGSLAGE messen und nicht den ERTRAG ueber die ZEIT. Was suchen
    wir? GUTE Einstiege mit OPTIMALEN Voraussetzungen fuer eine SCHNELLE
    HOHE BEWEGUNG NACH OBEN - das ist SELEKTION der besten Ausgangslagen
    mit den besten Ergebnissen innerhalb von 1-5 TAGEN."*

    *"GUTE Lagesignale sind eher SELTEN bzw. koennen NACH UNTEN SKALIEREN
    (kleinerer Hebel, das waere die Abstufung)."*

═══════════════════════════════════════════════════════════════════════
 WAS BISHER FALSCH GEMESSEN WURDE
═══════════════════════════════════════════════════════════════════════

    bisher (2.595-2.604)          hier
    --------------------------    ----------------------------------
    Fuenftel = 20 %, ~575k Anker  SPITZE: 5 % / 1 % / 0,1 %
    Horizont 6 und 24 Stunden     1, 2, 3, 5 TAGE
    `E[R]` bei FESTEM Ausstieg    MFE (max. Aufwaertsbewegung) + Ereignis
    *ordnet das Merkmal?*         *wie gut ist die SPITZE?*

⚠️⚠️ Ein Mittelwert ueber 20 % kann eine Spitze von 1 % nicht zeigen - sie
verschwindet darin. Registriert steht das schon (2.594): *ein Merkmal kann
im Mittel nichts bewegen und trotzdem die Extreme ordnen*.

═══════════════════════════════════════════════════════════════════════
 DIE ZIELGROESSEN - beide, wie vom Nutzer entschieden
═══════════════════════════════════════════════════════════════════════

    MFE        max(high[t+1..t+H]) / close[t] - 1, in ATR
    MAE        min(low [t+1..t+H]) / close[t] - 1, in ATR
               ⭐ das ist zugleich die SPIEGELPROBE - ein Merkmal, das
               beide gleich stark hebt, misst BEWEGUNG
    Ereignis   MFE >= 2 ATR, OHNE dass vorher MAE <= -1 ATR war
               ⭐ die REIHENFOLGE zaehlt: sonst wuerde ein Trade
               mitgezaehlt, der zuerst ausgestoppt worden waere

⚠️ NUR LESEN.  python messe_selektion.py [--symbole N]
"""
from __future__ import annotations

import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import messnorm as N                                            # noqa: E402
from messe_reverse_scharfe_anstiege import (                    # noqa: E402
    lade_kurse, lade_funding, merkmale_je_symbol)
from messe_hebel_dimension import _lade_terminmarkt             # noqa: E402
from messe_a_faktoren import a_faktoren                         # noqa: E402
from messe_hebel_geometrie_neutral import atr_tag_relativ       # noqa: E402

HORIZONTE = (24, 48, 72, 120)          # 1, 2, 3, 5 Tage
SCHAERFEN = (0.20, 0.05, 0.01, 0.001)
ZIEL_ATR, STOP_ATR = 2.0, 1.0
N_NULL = N.NULL_ZIEHUNGEN
NULL_PERZ = N.NULL_PERZENTIL
STAERKEN = (0.0, 0.25, 0.50, 1.0)
N_POSITIV = 5
MIND_ANKER = 500
SAAT = 20260926
MERKMALE = ("momentum_kurz", "rsi", "ema_lage", "ema_abstand_atr",
            "ema_steigung", "trendstruktur", "bandenge", "vola",
            "rsi_umkehr", "oi_aenderung", "zufall")


def mfe_mae(high, low, close, H):
    """-> (MFE, MAE, Ereignis) in ATR-Einheiten, streng kausal.

    ⚠️ Das Ereignis verlangt die REIHENFOLGE: das Ziel muss erreicht
    werden, BEVOR der Ruecklauf den Stop nimmt. Ein reiner Vergleich der
    Extrema wuerde Trades mitzaehlen, die vorher ausgestoppt gewesen waeren.
    """
    n = len(close)
    hoch = np.full(n, np.nan)
    tief = np.full(n, np.nan)
    ereignis = np.zeros(n, bool)
    atr = atr_tag_relativ(high, low, close)
    ziel = close * (1.0 + ZIEL_ATR * atr)
    stop = close * (1.0 - STOP_ATR * atr)
    fertig = np.zeros(n, bool)
    idx = np.arange(n)
    lauf_h = np.full(n, -np.inf)
    lauf_t = np.full(n, np.inf)
    for s in range(1, H + 1):
        j = np.minimum(idx + s, n - 1)
        lauf_h = np.maximum(lauf_h, high[j])
        lauf_t = np.minimum(lauf_t, low[j])
        offen = ~fertig
        # zuerst der Stop (konservativ, wie 2.583)
        raus = offen & (low[j] <= stop)
        treffer = offen & (high[j] >= ziel) & ~raus
        ereignis |= treffer
        fertig |= (raus | treffer)
    with np.errstate(divide="ignore", invalid="ignore"):
        hoch = (lauf_h / np.maximum(close, 1e-12) - 1.0) / np.maximum(atr, 1e-9)
        tief = (lauf_t / np.maximum(close, 1e-12) - 1.0) / np.maximum(atr, 1e-9)
    gueltig = np.isfinite(atr) & (atr > 0)
    gueltig[:30] = False
    gueltig[max(0, n - H):] = False
    return hoch, tief, ereignis, gueltig


def main() -> int:
    grenze = None
    if "--symbole" in sys.argv:
        grenze = int(sys.argv[sys.argv.index("--symbole") + 1])

    print("=" * 104)
    print("DIE SELEKTION: sind die besten 1 Prozent der Lagen wirklich "
          "besser?")
    print("=" * 104)
    print("  Vorabfestlegung 20 · Schaerfe %s · Horizonte %s Tage"
          % ("/".join("%.1f%%" % (100 * s) for s in SCHAERFEN),
             "/".join("%d" % (h // 24) for h in HORIZONTE)))
    print("  Ziel %g ATR, Stop %g ATR · Ereignis verlangt die REIHENFOLGE"
          % (ZIEL_ATR, STOP_ATR))
    print("  ⚠️ Gemessen wird die AUSGANGSLAGE, nicht der Ertrag - der")
    print("     entsteht in der Positionsfuehrung (Nutzerpunkt).")

    kurse = lade_kurse(grenze)
    tm = _lade_terminmarkt(set(kurse))
    fund = lade_funding()
    alle = set()
    for (s, *_r) in kurse.values():
        alle.update(s)
    sl = sorted(alle); sid = {s: i for i, s in enumerate(sl)}
    print("  %d Symbole · %d Stunden" % (len(kurse), len(sl)), flush=True)

    rng = np.random.default_rng(SAAT)
    for H in HORIZONTE:
        G, MFE, MAE, EV, MM = [], [], [], [], {k: [] for k in MERKMALE}
        for sym, (st, h, l, cc, v) in kurse.items():
            if sym.upper() == "BTC":
                continue
            idx = np.array([sid[x] for x in st], np.int64)
            atr = atr_tag_relativ(h, l, cc)
            hoch, tief, ev, gu = mfe_mae(h, l, cc, H)
            mk = dict(a_faktoren(cc, atr))
            mr = merkmale_je_symbol(sym, st, h, l, cc, v, tm, fund)
            mk.update({k: val for k, val in mr.items() if k in MERKMALE})
            mk["zufall"] = rng.random(len(cc))
            gu = gu & np.isfinite(hoch) & np.isfinite(tief)
            sel = np.flatnonzero(gu)
            if not len(sel):
                continue
            G.append(idx[sel]); MFE.append(hoch[sel]); MAE.append(tief[sel])
            EV.append(ev[sel])
            for k in MERKMALE:
                MM[k].append(mk[k][sel] if k in mk
                             else np.full(len(sel), np.nan))
        if not G:
            continue
        G = np.concatenate(G); MFE = np.concatenate(MFE)
        MAE = np.concatenate(MAE); EV = np.concatenate(EV)
        MM = {k: np.concatenate(v) for k, v in MM.items()}
        n = len(G)
        print()
        print("=" * 104)
        print("HORIZONT %d h (%d Tage) · %d Anker · MFE %.3f ATR · "
              "MAE %.3f ATR · Trefferquote %.2f %%"
              % (H, H // 24, n, float(np.mean(MFE)), float(np.mean(MAE)),
                 100 * float(EV.mean())), flush=True)

        # ── Nullwelt je Schaerfe: ZUFALLSauswahl GLEICHER Groesse ────
        #
        # ⚠️ Eine Fuenftelpermutation waere hier die falsche Nullwelt - sie
        # enthaelt die VERKLEINERUNG der Menge nicht. Eine Auswahl von
        # 0,1 % streut naturgemaess staerker als eine von 20 %.
        bands = {}
        for sch in SCHAERFEN:
            k = max(MIND_ANKER, int(round(sch * n)))
            w = []
            for _ in range(N_NULL):
                p = rng.choice(n, size=k, replace=False)
                w.append((float(MFE[p].mean()), float(EV[p].mean())))
            w = np.array(w)
            bands[sch] = (float(w[:, 0].mean()),
                          float(np.percentile(w[:, 0], NULL_PERZ)),
                          float(w[:, 1].mean()),
                          float(np.percentile(w[:, 1], NULL_PERZ)), k)
        print("  Nullwelt (Zufallsauswahl gleicher Groesse):")
        for sch in SCHAERFEN:
            m0, m9, e0, e9, k = bands[sch]
            print("     %6.1f %% (%7d Anker): MFE %.3f / %d. Perz %.3f · "
                  "Treffer %.2f %% / %.2f %%"
                  % (100 * sch, k, m0, int(NULL_PERZ), m9,
                     100 * e0, 100 * e9))

        print()
        print("  %-16s %8s %8s %8s %8s %9s  %s"
              % ("Merkmal", "Schaerfe", "MFE", "MAE", "MFE/MAE", "Treffer",
                 "Urteil"))
        for name in MERKMALE:
            w = MM[name]
            if not np.isfinite(w).any():
                continue
            zeilen = []
            for sch in SCHAERFEN:
                k = max(MIND_ANKER, int(round(sch * n)))
                gut = np.isfinite(w)
                if gut.sum() < k:
                    continue
                # oberste k nach dem Merkmal
                pos = np.flatnonzero(gut)
                ordn = pos[np.argsort(w[pos])[::-1][:k]]
                mfe, mae = float(MFE[ordn].mean()), float(MAE[ordn].mean())
                tr = float(EV[ordn].mean())
                m0, m9, e0, e9, _k = bands[sch]
                zeilen.append((sch, mfe, mae, tr, mfe > m9, tr > e9))
            if not zeilen:
                continue
            kz = "  <- KONTROLLE" if name in ("zufall", "vola") else ""
            for i, (sch, mfe, mae, tr, ok_m, ok_t) in enumerate(zeilen):
                print("  %-16s %7.1f%% %8.3f %8.3f %8.2f %8.2f%%  %s%s"
                      % (name if i == 0 else "", 100 * sch, mfe, mae,
                         mfe / max(abs(mae), 1e-9), 100 * tr,
                         ("⭐ MFE+Treffer" if ok_m and ok_t
                          else ("MFE" if ok_m else ("Treffer" if ok_t
                                                    else "-"))),
                         kz if i == 0 else ""))
            # ── DOSIS: waechst der Vorsprung mit der Schaerfe? ───────
            vor = [z[1] - bands[z[0]][0] for z in zeilen]
            if len(vor) >= 3:
                print("      ➤ Vorsprung MFE ueber die Schaerfe: %s   %s"
                      % (" ".join("%+.3f" % x for x in vor),
                         "⭐⭐ WAECHST" if all(
                             vor[i + 1] > vor[i] for i in range(len(vor) - 1))
                         else ("⚠️ faellt" if all(
                             vor[i + 1] < vor[i] for i in range(len(vor) - 1))
                             else "- uneinheitlich")))
    print()
    print("  ⚠️ `zufall` muss ueber ALLE Schaerfegrade flach bleiben -")
    print("     steigt es mit der Schaerfe, ist die Nullwelt falsch gebaut.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
