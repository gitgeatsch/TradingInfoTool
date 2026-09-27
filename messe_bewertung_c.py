# -*- coding: utf-8 -*-
"""Die Bewertung OHNE Ertrag - Weg C. Phase 1b.

**27.09.2026**, Nutzerentscheidung nach fachlicher Abwaegung: *"welche
der drei ist die beste Loesung, nicht die einfachste"*.

Vorabfestlegung: `Basisinfos/Vorabfestlegung_34_Bewertung_ohne_Ertrag_27_09.md`

═══════════════════════════════════════════════════════════════════════
 WARUM C
═══════════════════════════════════════════════════════════════════════

    A  nur Stopwahrscheinlichkeit -> eine Lage mit niedrigem Risiko und
       NULL Chance bekaeme hohen Hebel und ein Signal
    B  nur erwartetes CRV -> ein Verhaeltnis ist masstabsfrei: CRV 2 bei
       MFE 0,2/MAE 0,1 ist etwas anderes als CRV 2 bei MFE 4,0/MAE 2,0
    C  beides - und zwar nicht als zwei Regler an DERSELBEN Frage,
       sondern als ZWEI VERSCHIEDENE FRAGEN:

       Kommt ein Signal?     crv_erwartet(W)          das POTENTIAL
       Wie hoch der Hebel?   + absolutes mae_erwartet das RISIKO
       Harte Grenze          RM-11

═══════════════════════════════════════════════════════════════════════
 ⚠️⚠️ crv_erwartet IST NICHT DAS CRV DER HANDELSREGEL
═══════════════════════════════════════════════════════════════════════

`GRENZEN["crv"] = 2.0` ist das Verhaeltnis von Ziel- zu Stopabstand -
eine REGEL. `crv_erwartet` ist eine Markterwartung in ATR, aus MFE und
MAE. Gleicher Begriff, zwei Groessen. Sie tragen hier absichtlich
verschiedene Namen.

⚠️ NUR LESEN.  python messe_bewertung_c.py [--symbole N]
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
from messe_hebel_neudimension import EMA_L, VORLAUF             # noqa: E402
from messe_zielgroesse import mfe_mae_zeit                      # noqa: E402

H = 24                      # Messfenster aus 2.642 (H12 gleichwertig)
# ⚠️ Die Stopweiten sind PARAMETER, keine Wahrheit: 1,00 ATR stammt aus
# 2.628 und wurde nach ERTRAG optimiert (Falle 4).
WEITEN = (0.50, 0.75, 1.00, 1.50, 2.00)
# Stuetzstellen auf Perzentilen von W - die scharfen Lagen sind duenn
STUETZEN = (0.1, 0.25, 0.5, 1.0, 2.0, 3.0, 5.0, 7.0, 10.0, 15.0, 20.0,
            30.0, 40.0, 50.0, 65.0, 80.0, 95.0)
FENSTER = 6000              # Anker je Stuetzstelle
MAE_MIN = 0.05
SAAT = 20260927


def kurve(W, MFE, MAE, fenster=FENSTER):
    """mae_erwartet, mfe_erwartet und crv_erwartet je Stuetzstelle.

    ⚠️ Gleitendes Fenster ueber die nach W sortierten Anker, Stuetzstellen
    auf PERZENTILEN - gleichgrosse Rangschritte wuerden fast nur das
    Mittelfeld abtasten (dieselbe Falle wie in 2.630)."""
    o = np.argsort(W, kind="stable")
    Ws, Fs, As = W[o], MFE[o], MAE[o]
    n = len(Ws)
    if n < fenster:
        return []
    aus = []
    gesehen = set()
    for p in STUETZEN:
        z = p / 100.0 * n
        if z < fenster / 2.0 or z > n - fenster / 2.0:
            continue
        a = int(round(z - fenster / 2.0))
        if a in gesehen:
            continue
        gesehen.add(a)
        sl = slice(a, a + fenster)
        mae = float(np.mean(As[sl]))
        mfe = float(np.mean(Fs[sl]))
        aus.append(dict(p=p, w=float(np.median(Ws[sl])),
                        w_bis=float(Ws[sl][-1]), n=fenster,
                        mae=mae, mfe=mfe,
                        crv=mfe / max(abs(mae), MAE_MIN),
                        idx=o[sl]))
    return aus


def main() -> int:
    grenze = None
    if "--symbole" in sys.argv:
        grenze = int(sys.argv[sys.argv.index("--symbole") + 1])

    print("=" * 108)
    print("DIE BEWERTUNG OHNE ERTRAG - WEG C")
    print("=" * 108)
    print("  " + N.standardzeile())
    print("  Messfenster H%d (2.642) · MFE und MAE in ATR, REGELFREI" % H)
    print("  ⛔ Kein Ertrag, kein Kelly, kein q, kein CRV aus Ergebnissen")
    print()

    kurse = lade_kurse(grenze)
    alle = set()
    for (s, *_r) in kurse.values():
        alle.update(s)
    sl = sorted(alle); sid = {s: i for i, s in enumerate(sl)}
    G, W, MFE, MAE, SI = [], [], [], [], []
    namen = []
    for sym, (st, h, l, cc, v) in kurse.items():
        if sym.upper() == "BTC":
            continue
        gi = np.array([sid[x] for x in st], np.int64)
        atr = atr_tag_relativ(h, l, cc)
        e = ema(cc, EMA_L)
        with np.errstate(divide="ignore", invalid="ignore"):
            w = (cc - e) / np.maximum(atr * cc, 1e-12)
        mfe, mae, _z = mfe_mae_zeit(h, l, cc, atr, H)
        gu = (np.isfinite(atr) & (atr > 0) & np.isfinite(w)
              & np.isfinite(mfe) & np.isfinite(mae))
        gu[:VORLAUF] = False
        gu[max(0, len(cc) - H):] = False
        s2 = np.flatnonzero(gu)
        if len(s2) < 500:
            continue
        i_sym = len(namen); namen.append(sym)
        G.append(gi[s2]); W.append(w[s2]); MFE.append(mfe[s2])
        MAE.append(mae[s2])
        SI.append(np.full(len(s2), i_sym, np.int64))
    G = np.concatenate(G); W = np.concatenate(W)
    MFE = np.concatenate(MFE); MAE = np.concatenate(MAE)
    SI = np.concatenate(SI)
    tag = G // 24
    n = len(G)
    print("  %d Anker · %d Tage · %d Symbole"
          % (n, len(np.unique(tag)), len(kurse)), flush=True)
    print()

    # ══ TEIL 1: DIE KALIBRIERUNGSKURVEN ══════════════════════════════
    print("=" * 108)
    print("TEIL 1 - DIE KALIBRIERUNG: Lage -> erwartetes Risiko und Chance")
    print()
    k = kurve(W, MFE, MAE)
    print("  %6s %9s %11s %11s %13s %s"
          % ("Perz.", "W", "mae_erw.", "mfe_erw.", "crv_erwartet",
             "  (alles in ATR)"))
    for z in k:
        print("  %5.2f%% %+9.3f %+11.4f %+11.4f %13.4f"
              % (z["p"], z["w"], z["mae"], z["mfe"], z["crv"]), flush=True)

    xs = np.array([z["w"] for z in k])
    cr = np.array([z["crv"] for z in k])
    ma = np.array([z["mae"] for z in k])

    # ══ TEIL 2: DIE STOPWAHRSCHEINLICHKEIT ═══════════════════════════
    print()
    print("=" * 108)
    print("TEIL 2 - DIE STOPWAHRSCHEINLICHKEIT aus der MAE-VERTEILUNG")
    print("  ⚠️ Der MITTLERE MAE sagt das NICHT (Falle 3) - hier wird der")
    print("     Anteil der Anker gezaehlt, deren MAE die Weite reisst.")
    print("  ⚠️ Die Weiten sind PARAMETER: 1,00 ATR stammt aus 2.628 und")
    print("     wurde nach ERTRAG optimiert (Falle 4).")
    print()
    print("  %6s %9s %s" % ("Perz.", "W",
                            " ".join("%11s" % ("Stop %.2f" % x)
                                     for x in WEITEN)))
    for z in k:
        a = MAE[z["idx"]]
        zell = [100.0 * float((a <= -x).mean()) for x in WEITEN]
        print("  %5.2f%% %+9.3f %s"
              % (z["p"], z["w"], " ".join("%10.1f%%" % v for v in zell)),
              flush=True)

    # ══ TEIL 3: MONOTONIE UND SELBSTPROBE ════════════════════════════
    print()
    print("=" * 108)
    print("TEIL 3 - MONOTONIE UND SELBSTPROBE")
    print()
    from scipy.stats import spearmanr
    r1, p1 = spearmanr(xs, cr)
    r2, p2 = spearmanr(xs, ma)
    print("  crv_erwartet gegen W   rho %+.4f  p %.2e" % (r1, p1))
    print("  mae_erwartet gegen W   rho %+.4f  p %.2e" % (r2, p2))
    print("  ➤ erwartet: crv FAELLT mit W (niedriges W = beste Lage),")
    print("    mae STEIGT mit W (weniger negativ = weniger Rueckgang)")
    print()
    # Selbstprobe (Falle 8)
    rng = np.random.default_rng(SAAT)
    stich = rng.choice(n, size=min(200000, n), replace=False)
    crv_markt = float(MFE[stich].mean() / max(abs(MAE[stich].mean()), MAE_MIN))
    mitte = [z for z in k if 45 <= z["p"] <= 55]
    print("  SELBSTPROBE (Falle 8): bei ZUFAELLIGER Lage muss crv_erwartet")
    print("     gegen den Marktdurchschnitt laufen.")
    print("     Marktdurchschnitt      %.4f" % crv_markt)
    if mitte:
        print("     Stuetzstelle um 50 %%   %.4f" % mitte[0]["crv"])
        ok = abs(mitte[0]["crv"] - crv_markt) < 0.25 * crv_markt
        print("     ➤ %s" % ("✔ stimmt ueberein" if ok
                             else "⛔ weicht ab - die Kalibrierung stimmt "
                                  "nicht"))

    # ══ TEIL 4: OUT-OF-SAMPLE ════════════════════════════════════════
    print()
    print("=" * 108)
    print("TEIL 4 - OUT-OF-SAMPLE (Falle 6): Kurve aus der einen Haelfte")
    print()
    ut = np.unique(tag); m2 = ut[len(ut) // 2]
    print("  %-20s %11s %11s %13s %13s  %s"
          % ("Richtung", "W-Band", "crv vorher", "crv nachher", "Abstand",
             "Urteil"))
    for lab, mtr, mte in (("1. Haelfte -> 2.", tag < m2, tag >= m2),
                          ("2. Haelfte -> 1.", tag >= m2, tag < m2)):
        ktr = kurve(W[mtr], MFE[mtr], MAE[mtr])
        if len(ktr) < 4:
            print("  %-20s zu duenn" % lab); continue
        # die schaerfste Stuetzstelle der Trainingshaelfte
        besteW = min(z["w_bis"] for z in ktr[:2])
        vor = ktr[0]["crv"]
        mm = mte & (W <= besteW)
        if mm.sum() < 500:
            print("  %-20s zu wenige (%d)" % (lab, int(mm.sum()))); continue
        nach = float(MFE[mm].mean() / max(abs(MAE[mm].mean()), MAE_MIN))
        print("  %-20s %+11.3f %11.4f %13.4f %13.4f  %s"
              % (lab, besteW, vor, nach, nach - vor,
                 "✔" if nach > crv_markt else "⛔ unter Markt"), flush=True)

    # ══ TEIL 5: ZEITSTABILITAET ══════════════════════════════════════
    print()
    print("=" * 108)
    print("TEIL 5 - ZEITSTABILITAET UND WEGLASSPROBE (Falle 6)")
    print("  ⭐ Sie haben am 27.09. zwei Befunde gekippt (2.633, 2.640).")
    print()
    import datetime as dt
    ende = dt.date(2026, 9, 27)
    start = ende - dt.timedelta(days=int(tag.max()))
    jahr = np.array([(start + dt.timedelta(days=int(t))).year for t in tag])
    scharf = k[0]["w_bis"]           # die schaerfste Stuetzstelle
    print("  Gemessen an der schaerfsten Stuetzstelle: W <= %+.3f" % scharf)
    print()
    print("  %-10s %10s %11s %11s %13s %13s  %s"
          % ("Jahr", "n", "mae_erw.", "mfe_erw.", "crv_erwartet",
             "Markt-crv", "Urteil"))
    for j in (None, 2022, 2023, 2024, 2025, 2026):
        mj = (jahr == j) if j else np.ones(n, bool)
        ms = mj & (W <= scharf)
        if ms.sum() < 200:
            continue
        cv = float(MFE[ms].mean() / max(abs(MAE[ms].mean()), MAE_MIN))
        mk = float(MFE[mj].mean() / max(abs(MAE[mj].mean()), MAE_MIN))
        print("  %-10s %10d %+11.4f %+11.4f %13.4f %13.4f  %s"
              % (j or "alle", int(ms.sum()), MAE[ms].mean(), MFE[ms].mean(),
                 cv, mk, "✔" if cv > mk else "⛔ unter Markt"), flush=True)

    # ══ TEIL 6: STRECKENANFAENGE ═════════════════════════════════════
    print()
    print("=" * 108)
    print("TEIL 6 - GILT DIE KALIBRIERUNG AUCH AUF STRECKENANFAENGEN?")
    print("  ⚠️ 2.638: der Betrieb kauft nur Anfaenge, und dort war der")
    print("     ERTRAG viermal kleiner. Gilt das auch fuer MFE/MAE?")
    print()
    print("  %-22s %10s %11s %11s %13s"
          % ("Menge", "n", "mae_erw.", "mfe_erw.", "crv_erwartet"))
    # ⚠️ Streckenabgrenzung JE SYMBOL - ein globaler Stundenindex allein
    # wuerde zwei verschiedene Symbole in derselben Stunde zu EINER
    # Strecke machen. Deshalb wird nach (Symbol, Stunde) sortiert und
    # eine neue Strecke bei Symbolwechsel ODER mehr als H Stunden Abstand
    # begonnen - genau wie in `messe_schwelle_anfang.anfaenge`.
    idx = np.flatnonzero(W <= scharf)
    idx = idx[np.lexsort((G[idx], SI[idx]))]
    neu = np.ones(len(idx), bool)
    neu[1:] = (SI[idx][1:] != SI[idx][:-1]) | (np.diff(G[idx]) > H)
    an = idx[neu]
    for lab, m in (("alle Anker", idx), ("nur Streckenanfaenge", an)):
        cv = float(MFE[m].mean() / max(abs(MAE[m].mean()), MAE_MIN))
        print("  %-22s %10d %+11.4f %+11.4f %13.4f"
              % (lab, len(m), MAE[m].mean(), MFE[m].mean(), cv))
    print()
    print("  ⭐ Die Streckenabgrenzung laeuft JE SYMBOL - neue Strecke bei")
    print("     Symbolwechsel oder mehr als %d Stunden Abstand, genau wie" % H)
    print("     in `messe_schwelle_anfang.anfaenge`.")

    print()
    print("  ⚠️ Gebuehren und Finanzierung sind NICHT eingerechnet (Regel 2).")
    print("  ⚠️ r_min/r_max (0,5 bis 1,25 %) und die 2x-Grenze sind")
    print("     NUTZERVORGABEN, keine Messergebnisse (Falle 7).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
