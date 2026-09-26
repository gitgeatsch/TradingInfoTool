# -*- coding: utf-8 -*-
"""Die heutigen Kandidaten mit der GEEICHTEN Spiegelprobe neu bewerten

**26.09.2026** · Vorabfestlegung 19 · nach `pruefe_spiegelprobe.py`

═══════════════════════════════════════════════════════════════════════
 WAS SICH GEAENDERT HAT
═══════════════════════════════════════════════════════════════════════

    ⛔ ALT (25./26.09.)   Spiegelprobe auf `E[R]`, Spannen verglichen.
                          NACHWEISLICH FALSCH: Long- und Short-`E[R]` sind
                          auf denselben Ankern strukturell gegenlaeufig.
    ✔ NEU                 Spiegelprobe auf dem EREIGNIS (ZIEL erreicht),
                          Lift hoch gegen Lift runter - die Konstruktion
                          aus 2.594.
    ⭐ SCHWELLE           1,717 statt 1,30, an einer Simulation ABGELESEN
                          (0 % Fehlalarm, 100 % Fundquote, monoton ueber
                          die Dosis). Die registrierte 1,30 ist zu lax:
                          das 90. Perzentil der BEWEGUNG-Welt liegt bei
                          1,362 und damit darueber.

⚠️ Die Schwelle ist eine UNTERE Abschaetzung - normalverteilte Renditen
haben keine fetten Raender und kein Vola-Clustering.

⚠️ NUR LESEN.  python messe_kandidaten_spiegel.py [--symbole N]
"""
from __future__ import annotations

import os
import sqlite3
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from messe_reverse_scharfe_anstiege import (                    # noqa: E402
    lade_kurse, lade_funding, merkmale_je_symbol, _rsi, _schiebe)
from messe_hebel_dimension import _lade_terminmarkt             # noqa: E402
from messe_a_faktoren import a_faktoren                         # noqa: E402
import messe_hebel_geometrie_neutral as GG                      # noqa: E402
from messe_q_beide_seiten import (                              # noqa: E402
    fuenftel_je_stunde, MIND_JE_FUENFTEL)

SCHWELLE = 1.717            # abgelesen aus pruefe_spiegelprobe.py
GEGEN = 1.0 / SCHWELLE      # 0,582 - die inverse Richtung
CRV, H, K = 1.5, 6, 1.0
LEITWERT = os.path.join("data", "btc_leitwert.db")
SAAT = 20260926


def main() -> int:
    grenze = None
    if "--symbole" in sys.argv:
        grenze = int(sys.argv[sys.argv.index("--symbole") + 1])

    print("=" * 100)
    print("DIE HEUTIGEN KANDIDATEN - mit der GEEICHTEN Spiegelprobe")
    print("=" * 100)
    print("  Ereignis: ZIEL erreicht · Lift oberstes Fuenftel gegen Mittel")
    print("  Schwelle %.3f (abgelesen, nicht gesetzt) · inverse Richtung "
          "<= %.3f" % (SCHWELLE, GEGEN))
    print("  ⚠️ Die alte Probe auf `E[R]` war falsch konstruiert - ihre")
    print("     Urteile vom 25./26.09. sind damit zurueckgezogen.")

    kurse = lade_kurse(grenze)
    tm = _lade_terminmarkt(set(kurse))
    fund = lade_funding()
    alle = set()
    for (s, *_r) in kurse.values():
        alle.update(s)
    sl = sorted(alle); sid = {s: i for i, s in enumerate(sl)}; T = len(sl)
    print("  %d Symbole · %d Stunden · Terminmarkt %d · Funding %d"
          % (len(kurse), T, len(tm), len(fund)), flush=True)

    # ── die Sperre aus 2.602, damit auf DERSELBEN Menge geurteilt wird ──
    c = sqlite3.connect("file:%s?mode=ro" % LEITWERT, uri=True)
    btc = np.full(T, np.nan)
    for st, cl in c.execute("SELECT stunde, close FROM leitwert "
                            "WHERE symbol='BTC'"):
        i = sid.get(st)
        if i is not None:
            btc[i] = cl
    c.close()
    br = np.full(T, np.nan)
    br[6:] = btc[6:] / np.maximum(btc[:-6], 1e-12) - 1.0
    asum, anum = np.zeros(T), np.zeros(T)
    for sym, (st, h, l, cc, v) in kurse.items():
        if sym.upper() == "BTC":
            continue
        ii = np.array([sid[x] for x in st], np.int64)
        rr = np.full(len(cc), np.nan)
        if len(cc) > 6:
            rr[6:] = cc[6:] / np.maximum(cc[:-6], 1e-12) - 1.0
        g = np.isfinite(rr)
        np.add.at(asum, ii[g], rr[g]); np.add.at(anum, ii[g], 1.0)
    with np.errstate(invalid="ignore"):
        am = np.where(anum >= 5, asum / np.maximum(anum, 1), np.nan)
    gesperrt = (br > 0.005) & ((br - am) > 0.0)

    rng = np.random.default_rng(SAAT)
    KAND = ("momentum_kurz", "rsi", "vola", "ema_lage", "trendstruktur",
            "ema_abstand_atr", "rsi_umkehr", "bandenge", "ema_steigung",
            "rueckstand_beta", "oi_aenderung", "funding", "zufall")
    G, ZL, ZS, MM = [], [], [], {k: [] for k in KAND}
    for sym, (st, h, l, cc, v) in kurse.items():
        if sym.upper() == "BTC":
            continue
        idx = np.array([sid[x] for x in st], np.int64)
        atr = GG.atr_tag_relativ(h, l, cc)
        stop = np.clip(K * atr, GG.STOP_MIN, GG.STOP_MAX)
        zz, _s1, _r1, gu, _g1 = GG.ausgaenge(h, l, cc, stop, CRV * stop, H)
        zs, _s2, _r2, _g2, _g3 = GG.ausgaenge(h, l, cc, stop, CRV * stop, H,
                                              runter=True)
        mk = dict(a_faktoren(cc, atr))
        mr = merkmale_je_symbol(sym, st, h, l, cc, v, tm, fund)
        mk.update({k: val for k, val in mr.items() if k in KAND})
        # Rueckstand gegen BTC (2.601)
        a6 = np.full(len(cc), np.nan)
        if len(cc) > 6:
            a6[6:] = cc[6:] / np.maximum(cc[:-6], 1e-12) - 1.0
        mk["rueckstand_beta"] = br[idx] - a6
        mk["zufall"] = rng.random(len(cc))
        gu = gu & ~np.nan_to_num(gesperrt[idx], nan=False)
        sel = np.flatnonzero(gu)
        if not len(sel):
            continue
        G.append(idx[sel]); ZL.append(zz[sel]); ZS.append(zs[sel])
        for k in KAND:
            MM[k].append(mk[k][sel] if k in mk
                         else np.full(len(sel), np.nan))
    G = np.concatenate(G); ZL = np.concatenate(ZL); ZS = np.concatenate(ZS)
    MM = {k: np.concatenate(v) for k, v in MM.items()}
    print("  %d Anker (Sperre angewandt) · P(ZIEL) long %.4f · short %.4f"
          % (len(G), ZL.mean(), ZS.mean()))
    print()
    print("  %-17s %9s %9s %9s   %s"
          % ("Merkmal", "Lift hoch", "Lift runt", "Verh.", "Urteil"))
    for name in KAND:
        fz = fuenftel_je_stunde(G, MM[name])
        if fz is None:
            continue
        i2, f2 = fz
        n5 = np.bincount(f2, minlength=5).astype(float)
        if (n5 < MIND_JE_FUENFTEL).any():
            continue
        pl = np.bincount(f2, weights=ZL[i2].astype(float), minlength=5) / n5
        ps = np.bincount(f2, weights=ZS[i2].astype(float), minlength=5) / n5
        # das Fuenftel mit dem hoechsten Long-Lift - so wie ein Betrieb
        # es waehlen wuerde
        b = int(np.argmax(pl))
        lh = float(pl[b] / max(pl.mean(), 1e-12))
        lr = float(ps[b] / max(ps.mean(), 1e-12))
        v = lh / max(lr, 1e-9)
        urteil = ("✔✔ RICHTUNG" if v >= SCHWELLE
                  else ("✔ inverse Richtung" if v <= GEGEN
                        else "⛔ BEWEGUNG ohne Richtung"))
        kz = "  <- KONTROLLE" if name == "zufall" else ""
        print("  %-17s %9.3f %9.3f %9.3f   %s (F%d)%s"
              % (name, lh, lr, v, urteil, b, kz))
    print()
    print("  ⚠️ `zufall` muss nahe 1,0 liegen - sonst ist die Anlage schief.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
