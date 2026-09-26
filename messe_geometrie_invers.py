# -*- coding: utf-8 -*-
"""Die GEOMETRIE auf der inversen Achse - Horizont, Stop, Trailing

**26.09.2026**, Nutzerauftrag: *"Geometrie auf der inversen Achse
nachmessen, pruefen, gegenpruefen"*.

Vorabfestlegung: `Basisinfos/Vorabfestlegung_24_Geometrie_invers_26_09.md`

═══════════════════════════════════════════════════════════════════════
 WARUM DIE GEOMETRIE AUS 2.620 NICHT UEBERNOMMEN WERDEN DARF
═══════════════════════════════════════════════════════════════════════

Horizont 72 h, Stop 1,0 ATR und Trailing 1,5/0,5 wurden fuer die ALTE
Richtung dimensioniert - die inzwischen widerlegt ist (2.624).

⚠️ Und ein Messwert zeigt, dass sie nicht passt: bei H6 wird der Stop in
0,4 PROZENT der Faelle erreicht (2.627). In sechs Stunden bewegt sich der
Kurs selten um 1 ATR - das ist eine TAGESspanne. Ein Stop, der nie greift,
ist keine Risikobegrenzung, sondern Dekoration.

═══════════════════════════════════════════════════════════════════════
 DREI UNTERSCHIEDE ZU 2.620
═══════════════════════════════════════════════════════════════════════

    AUSWAHL     je Tag die besten 2 Prozent (NIEDRIGSTER Wert), nicht eine
                globale Schwelle - sonst misst man die Tageswahl mit
    NULLWELT    ⭐ TAGESTREU statt gepoolt. Genau daran fiel 2.608:
                `messnorm` haelt fest, dass gepoolt 12,4 Punkte auf einem
                NULLEFFEKT erzeugt
    STOPWEITEN  ⭐ nach UNTEN erweitert (0,15 bis 2,0 statt 1,0 bis 3,0) -
                die 0,4-Prozent-Quote sagt, dass 1,0 ATR bei kurzen
                Horizonten wirkungslos ist

⭐⭐ ZUSAETZLICH BERICHTET WIRD DIE STOPQUOTE. Eine Zelle, in der der Stop
unter 5 Prozent greift, ist als Risikobegrenzung WERTLOS - auch wenn ihr
Ertrag gut aussieht. Das ist vorab festgelegt, nicht nachtraeglich.

⚠️ NUR LESEN.  python messe_geometrie_invers.py [--symbole N]
"""
from __future__ import annotations

import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import messnorm as N                                            # noqa: E402
from messe_reverse_scharfe_anstiege import lade_kurse           # noqa: E402
from messe_hebel_geometrie_neutral import atr_tag_relativ       # noqa: E402
from messe_trailing_und_betrieb import ema, trailing            # noqa: E402
from messe_hebel_neudimension import (                          # noqa: E402
    trailing_mit_ausloeser, geometrisch, laengste_verlustserie,
    EMA_L, VORLAUF)
from messe_inverse_achse import taeglich_beste                  # noqa: E402

HORIZONTE = (2, 3, 6, 12, 24, 48)
STOPWEITEN = (0.15, 0.25, 0.4, 0.6, 1.0, 1.5, 2.0)
AUSLOESER = (0.0, 0.5, 1.0, 1.5)
ABSTAENDE = (0.5, 1.0)
ANTEIL = 0.02
MIND_STOPQUOTE = 0.05
SAAT = 20260926


def main() -> int:
    grenze = None
    if "--symbole" in sys.argv:
        grenze = int(sys.argv[sys.argv.index("--symbole") + 1])

    print("=" * 112)
    print("DIE GEOMETRIE AUF DER INVERSEN ACHSE")
    print("=" * 112)
    print("  " + N.standardzeile())
    print("  Auswahl: je Tag die besten %.0f %% (NIEDRIGSTER "
          "ema_abstand_atr) · Nullwelt TAGESTREU" % (100 * ANTEIL))
    print("  ⚠️ Stopweiten nach unten erweitert - bei H6 griff 1,0 ATR nur "
          "in 0,4 %% der Faelle (2.627)")
    print()

    kurse = lade_kurse(grenze)
    alle = set()
    for (s, *_r) in kurse.values():
        alle.update(s)
    sl = sorted(alle); sid = {s: i for i, s in enumerate(sl)}
    Hmax = max(HORIZONTE)
    roh = []
    for sym, (st, h, l, cc, v) in kurse.items():
        if sym.upper() == "BTC":
            continue
        atr = atr_tag_relativ(h, l, cc)
        e = ema(cc, EMA_L)
        with np.errstate(divide="ignore", invalid="ignore"):
            w = (cc - e) / np.maximum(atr * cc, 1e-12)
        gu = np.isfinite(atr) & (atr > 0) & np.isfinite(w)
        gu[:VORLAUF] = False
        gu[max(0, len(cc) - Hmax):] = False
        sel = np.flatnonzero(gu)
        if len(sel):
            roh.append((np.array([sid[x] for x in st], np.int64),
                        h, l, cc, atr, w, sel))
    G = np.concatenate([d[0][d[6]] for d in roh])
    W = np.concatenate([d[5][d[6]] for d in roh])
    A = np.concatenate([d[4][d[6]] for d in roh])
    n = len(G); tag = G // 24
    sig = taeglich_beste(W, tag, ANTEIL)
    print("  %d Anker (P3: fuer Hmax gueltig) · %d Signale"
          % (n, int(sig.sum())), flush=True)

    # ── die tagestreue Nullwelt, EINMAL vorbereitet ──────────────────
    rng = np.random.default_rng(SAAT)
    frei = np.flatnonzero(np.isfinite(W))
    je_tag = {int(t): int(c) for t, c in
              zip(*np.unique(tag[sig], return_counts=True))}
    pool = {}
    for i_ in frei:
        pool.setdefault(int(tag[i_]), []).append(i_)
    pool = {t: np.array(v) for t, v in pool.items()}

    def zieh():
        a = []
        for t, c in je_tag.items():
            pl = pool.get(t)
            if pl is not None and len(pl):
                a.append(rng.choice(pl, size=min(c, len(pl)),
                                    replace=False))
        return np.concatenate(a) if a else np.array([], int)

    def trailing_mit_stopmarke(high, low, close, atr, weite, ausl, abst, hz):
        """Wie `trailing_mit_ausloeser`, aber mit der Marke GESTOPPT.

        ⚠️⚠️ WARUM EIGENS: die Stopquote ueber die DAUER zu erkennen
        (`dauer < H`) ist falsch - ein Stop, der genau in der letzten
        Stunde greift, faellt durch. Im Probelauf sprang die Quote dadurch
        von 15,9 Prozent bei H2 auf 97,0 bei H3, weil bei H2 nur der
        Ausstieg nach EINER Stunde gezaehlt wurde. Die Marke wird deshalb
        dort gesetzt, wo der Stop tatsaechlich greift.
        """
        n_ = len(close)
        idx = np.arange(n_)
        risiko = np.maximum(weite * atr * close, 1e-12)
        stop = close - risiko
        hoechst = close.copy()
        fertig = np.zeros(n_, bool)
        ausstieg = np.full(n_, np.nan)
        for s in range(1, hz + 1):
            j = np.minimum(idx + s, n_ - 1)
            offen = ~fertig
            raus = offen & (low[j] <= stop)
            ausstieg[raus] = stop[raus]
            fertig |= raus
            neu = ~fertig
            hoechst = np.where(neu & (high[j] > hoechst), high[j], hoechst)
            mfe_r = (hoechst - close) / risiko
            zieht = neu & (mfe_r >= ausl)
            stop = np.where(zieht, np.maximum(stop, hoechst - abst * risiko),
                            stop)
        je = np.minimum(idx + hz, n_ - 1)
        gestoppt = fertig.copy()          # ⭐ die Marke, nicht die Dauer
        ausstieg = np.where(np.isnan(ausstieg), close[je], ausstieg)
        return ((ausstieg - close) / risiko,
                (ausstieg - close) / np.maximum(close, 1e-12),
                gestoppt.astype(float))

    def rechne(hz, weite, ausl, abst):
        rr, pp, ss = [], [], []
        for idx, h, l, cc, atr, w, sel in roh:
            a, b, g_ = trailing_mit_stopmarke(h, l, cc, atr, weite, ausl,
                                              abst, hz)
            rr.append(a[sel]); pp.append(b[sel]); ss.append(g_[sel])
        return (np.concatenate(rr), np.concatenate(pp),
                np.concatenate(ss))

    # ── P1: die NEUE Funktion gegen die bestehende ───────────────────
    # ⚠️ Geprueft wird `trailing_mit_stopmarke`, nicht die importierte -
    # sie ist der Rechner, der hier laeuft. Eine Probe auf fremdem Code
    # sagt nichts ueber den eigenen.
    d0 = roh[0]
    a1, _p, _g = trailing_mit_stopmarke(d0[1], d0[2], d0[3], d0[4],
                                        1.0, 0.0, 1.0, 24)
    a2 = trailing(d0[1], d0[2], d0[3], d0[4], 1.0, 24)
    a3, _p3, _d3 = trailing_mit_ausloeser(d0[1], d0[2], d0[3], d0[4],
                                          1.0, 0.0, 1.0, 24)
    ok = bool(np.allclose(np.nan_to_num(a1), np.nan_to_num(a2), rtol=0, atol=0)
              and np.allclose(np.nan_to_num(a1), np.nan_to_num(a3),
                              rtol=0, atol=0))
    print("  P1  neue Funktion bitgleich mit trailing() UND "
          "trailing_mit_ausloeser(): %s"
          % ("✔ JA" if ok else "⛔ NEIN - ABBRUCH"))
    if not ok:
        return 1

    # ══ STUFE G ══════════════════════════════════════════════════════
    print()
    print("=" * 112)
    print("STUFE G - HORIZONT x STOPWEITE (Trailing wie 2.607: ausloese 0, "
          "abstand = weite)")
    print("  ⚠️ Nur KURSPROZENT vergleicht ueber Stopweiten. "
          "⭐ STOPQUOTE < %.0f %% = als Risikobegrenzung wertlos"
          % (100 * MIND_STOPQUOTE))
    print()
    print("  %-5s %-6s %10s %10s %10s %9s %8s  %s"
          % ("H", "Stop", "Kurs %", "geom %", "Band90", "Stopquote",
             "Serie", "Urteil"))
    zellen = []; nullproben = []
    for hz in HORIZONTE:
        for weite in STOPWEITEN:
            r, p, s_ = rechne(hz, weite, 0.0, weite)
            rs, ps = r[sig], p[sig]
            nb = np.array([float(p[zieh()].mean())
                           for _ in range(N.NULL_ZIEHUNGEN)])
            nullproben.append(nb)
            b90 = 100 * float(np.percentile(nb, N.NULL_PERZENTIL))
            pz = 100 * float(ps.mean())
            ge = 100 * geometrisch(rs)
            sq = float(s_[sig].mean())
            serie = laengste_verlustserie(rs[np.argsort(G[sig])])
            brauchbar = sq >= MIND_STOPQUOTE
            zellen.append(dict(h=hz, weite=weite, pz=pz, ge=ge, sq=sq,
                               serie=serie, b90=b90, ok=pz > b90,
                               brauchbar=brauchbar))
            print("  %-5d %-6.2f %+10.4f %+10.5f %+10.4f %8.1f%% %8d  %s"
                  % (hz, weite, pz, ge, b90, 100 * sq, serie,
                     ("✔" if pz > b90 else "⛔ im Band")
                     + ("" if brauchbar else " · ⚠️ Stop greift kaum")),
                  flush=True)

    # ── P5 ───────────────────────────────────────────────────────────
    gute = [z for z in zellen if z["brauchbar"]]
    if not gute:
        print()
        print("  ⛔ KEINE Zelle mit brauchbarer Stopquote - die Geometrie "
              "ist nicht bestimmbar")
        return 0
    arr = np.array(nullproben) * 100
    b90_mehr = float(np.percentile(arr.max(axis=0), N.NULL_PERZENTIL))
    best = max(gute, key=lambda z: z["pz"])
    print()
    print("  P5  MEHRFACHTESTEN ueber %d Zellen · Bestes-von-%d-Band "
          "%+.4f %%" % (len(zellen), len(zellen), b90_mehr))
    print("      beste BRAUCHBARE Zelle: H%d / Stop %.2f mit %+.4f %% "
          "(Stopquote %.1f %%) -> %s"
          % (best["h"], best["weite"], best["pz"], 100 * best["sq"],
             "✔✔ haelt" if best["pz"] > b90_mehr else "⛔ Auslese"))
    print()
    print("  DIE DREI BESTEN BRAUCHBAREN")
    for z in sorted(gute, key=lambda x: -x["pz"])[:3]:
        print("      H%-3d Stop %.2f  Kurs %+7.4f %%  geom %+8.5f %%  "
              "Stopquote %.1f %%  Serie %d"
              % (z["h"], z["weite"], z["pz"], z["ge"], 100 * z["sq"],
                 z["serie"]))

    # ══ STUFE T ══════════════════════════════════════════════════════
    for rang, geo in enumerate(sorted(gute, key=lambda x: -x["pz"])[:2], 1):
        print()
        print("=" * 112)
        print("STUFE T (%d. Geometrie) - AUSLOESER x ABSTAND auf H%d / "
              "Stop %.2f" % (rang, geo["h"], geo["weite"]))
        print("  %-9s %-8s %10s %11s %10s %9s  %s"
              % ("Ausloeser", "Abstand", "Kurs %", "geom %", "Band90",
                 "Stopquote", "Urteil"))
        tz, tn = [], []
        for ausl in AUSLOESER:
            for abst in ABSTAENDE:
                r, p, s_ = rechne(geo["h"], geo["weite"], ausl, abst)
                rs, ps = r[sig], p[sig]
                nb = np.array([float(p[zieh()].mean())
                               for _ in range(N.NULL_ZIEHUNGEN)])
                tn.append(nb)
                b90 = 100 * float(np.percentile(nb, N.NULL_PERZENTIL))
                pz = 100 * float(ps.mean())
                tz.append(dict(ausl=ausl, abst=abst, pz=pz,
                               ge=100 * geometrisch(rs),
                               sq=float(s_[sig].mean())))
                print("  %-9.1f %-8.1f %+10.4f %+11.5f %+10.4f %8.1f%%  %s"
                      % (ausl, abst, pz, tz[-1]["ge"], b90,
                         100 * tz[-1]["sq"],
                         "✔" if pz > b90 else "⛔ im Band"), flush=True)
        bt = max(tz, key=lambda z: z["pz"])
        b90t = float(np.percentile((np.array(tn) * 100).max(axis=0),
                                   N.NULL_PERZENTIL))
        print("  P5  Bestes-von-%d-Band %+.4f %% · beste Zelle "
              "Ausloeser %.1f / Abstand %.1f mit %+.4f %% -> %s"
              % (len(tz), b90t, bt["ausl"], bt["abst"], bt["pz"],
                 "✔✔ haelt" if bt["pz"] > b90t else "⛔ Auslese"))
    print()
    print("  ⚠️ Gebuehren, Finanzierung, Gaps und Slippage sind NICHT "
          "eingerechnet.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
