# -*- coding: utf-8 -*-
"""Traegt die INVERSE Achse - out of sample und je Asset?

**26.09.2026**, nach 2.625: die Ordnung existiert, zeigt aber in die andere
Richtung. Assets WEIT UNTER ihrem EMA liefern +1,3143 Prozent relativ zum
eigenen Tag, Assets weit darueber -0,9437.

⚠️⚠️ DAS IST BISHER EINE IN-SAMPLE-BEOBACHTUNG. Sie verdient dieselbe
Skepsis wie der Befund, der heute gefallen ist - und genau dieselben
Pruefungen, die ihn zu Fall gebracht haben:

    TAGESTREUE NULLWELT   nur so misst man die AUSWAHL statt der Tageswahl
    OUT OF SAMPLE         rollierend, mit Luecke von H Stunden
    JE ASSET              die Nutzervorgabe *wir messen nicht den Markt*
    POSITIVKONTROLLE      damit *nicht bestanden* aussagekraeftig ist

═══════════════════════════════════════════════════════════════════════
 ⚠️ WAS HIER ANDERS IST ALS BEIM GEFALLENEN BEFUND
═══════════════════════════════════════════════════════════════════════

Die Richtung ist UMGEDREHT: gewaehlt werden die NIEDRIGSTEN Werte von
`ema_abstand_atr`, nicht die hoechsten. Alles andere bleibt gleich -
dieselbe Geometrie, dieselbe Menge, derselbe Pruefstand.

⚠️ Und die Zielgroesse ist der Ertrag RELATIV ZUM EIGENEN TAG. Das ist die
Frage, die der Nutzer stellt: *na und dann darf nur das asset mit den
besten werten gewinnen*. Absolut gemessen wuerde die Tageswahl mitzaehlen.

⚠️ NUR LESEN.  python messe_inverse_achse.py [--symbole N]
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

EMA_L, VORLAUF, H, TW = 48, 240, 72, 1.0
FENSTER = 5
#: Anteil der taeglich BESTEN (= niedrigsten) Werte
ANTEILE = (0.01, 0.02, 0.05)
SAAT = 20260926


def lade():
    kurse = lade_kurse(int(sys.argv[sys.argv.index("--symbole") + 1])
                       if "--symbole" in sys.argv else None)
    alle = set()
    for (s, *_r) in kurse.values():
        alle.update(s)
    sl = sorted(alle); sid = {s: i for i, s in enumerate(sl)}
    G, W, P, S = [], [], [], []
    for i, (sym, (st, h, l, cc, v)) in enumerate(kurse.items()):
        if sym.upper() == "BTC":
            continue
        atr = atr_tag_relativ(h, l, cc)
        e = ema(cc, EMA_L)
        with np.errstate(divide="ignore", invalid="ignore"):
            w = (cc - e) / np.maximum(atr * cc, 1e-12)
        gu = np.isfinite(atr) & (atr > 0) & np.isfinite(w)
        gu[:VORLAUF] = False
        gu[max(0, len(cc) - H):] = False
        s2 = np.flatnonzero(gu)
        if not len(s2):
            continue
        r = trailing(h, l, cc, atr, TW, H)[s2]
        G.append(np.array([sid[x] for x in st], np.int64)[s2])
        W.append(w[s2]); P.append(r * TW * atr[s2])
        S.append(np.full(len(s2), i))
    return (np.concatenate(G), np.concatenate(W), np.concatenate(P),
            np.concatenate(S))


def taeglich_beste(W, tag, anteil, invers=True):
    """-> Maske: je Tag die besten `anteil` nach `W`.

    ⭐ DIE AUSWAHL IST JE TAG, nicht global. Genau das ist die Frage:
    *welches Asset ist HEUTE das beste?* Eine globale Schwelle waehlt an
    guten Tagen viele und an schlechten keine - das misst die Tageswahl mit.
    """
    aus = np.zeros(len(W), bool)
    ordnung = np.argsort(tag, kind="stable")
    t_s = tag[ordnung]
    grenzen = np.searchsorted(t_s, np.unique(t_s))
    grenzen = list(grenzen) + [len(t_s)]
    for a, b in zip(grenzen[:-1], grenzen[1:]):
        idx = ordnung[a:b]
        gut = idx[np.isfinite(W[idx])]
        if len(gut) < 10:
            continue
        k = max(1, int(round(anteil * len(gut))))
        rang = np.argsort(W[gut])           # aufsteigend = niedrigste zuerst
        aus[gut[rang[:k] if invers else rang[-k:]]] = True
    return aus


def main() -> int:
    print("=" * 100)
    print("TRAEGT DIE INVERSE ACHSE - OUT OF SAMPLE UND JE ASSET?")
    print("=" * 100)
    print("  " + N.standardzeile())
    print("  ⚠️ Zielgroesse: Ertrag RELATIV ZUM EIGENEN TAG")
    print("  ⚠️ Auswahl JE TAG (die besten k), nicht ueber eine globale "
          "Schwelle")
    print()

    G, W, P, S = lade()
    n = len(G)
    tag = G // 24
    # ── Ertrag relativ zum eigenen Tag ───────────────────────────────
    ut, inv = np.unique(tag, return_inverse=True)
    mit = (np.bincount(inv, weights=P) /
           np.maximum(np.bincount(inv), 1))[inv]
    REL = P - mit
    print("  %d Anker · %d Tage · %d Symbole"
          % (n, len(ut), len(np.unique(S))), flush=True)

    rng = np.random.default_rng(SAAT)

    def nullband(maske_gross, k_je_tag, ziehungen=N.NULL_ZIEHUNGEN):
        """Tagestreue Nullwelt: je Tag so viele zufaellige wie gewaehlt."""
        werte = []
        pool = {}
        idx_all = np.flatnonzero(maske_gross)
        for i_ in idx_all:
            pool.setdefault(int(tag[i_]), []).append(i_)
        pool = {t: np.array(v) for t, v in pool.items()}
        for _ in range(ziehungen):
            a = []
            for t, c in k_je_tag.items():
                pl = pool.get(t)
                if pl is not None and len(pl):
                    a.append(rng.choice(pl, size=min(c, len(pl)),
                                        replace=False))
            if a:
                werte.append(float(REL[np.concatenate(a)].mean()))
        return np.array(werte)

    # ══ TEIL 1: OUT OF SAMPLE, rollierend ════════════════════════════
    stunden = np.sort(np.unique(G))
    kanten = np.linspace(0, len(stunden) - 1, FENSTER + 1).astype(int)
    gr = [stunden[k] for k in kanten]
    print("=" * 100)
    print("TEIL 1 - OUT OF SAMPLE (rollierend, Luecke %d h)" % H)
    print()
    for anteil in ANTEILE:
        print("  ANTEIL %.0f %% der taeglich BESTEN (niedrigster "
              "ema_abstand_atr)" % (100 * anteil))
        print("    %-9s %9s %11s %11s %11s  %s"
              % ("Fenster", "Signale", "rel. Ertrag", "Nullpunkt", "Band90",
                 "Urteil"))
        ok_n = 0; ges = 0
        for i in range(FENSTER - 1):
            pru = (G >= gr[i + 1] + H) & (G < gr[i + 2])
            if pru.sum() < 5000:
                continue
            # ⚠️ Die Auswahlregel braucht KEINE Kalibrierung - sie ist
            # "die besten k je Tag". Damit ist sie per Bau out-of-sample;
            # geprueft wird, ob sie im NEUEN Fenster traegt.
            sig = taeglich_beste(np.where(pru, W, np.nan), tag, anteil)
            k = int(sig.sum())
            if k < 200:
                continue
            ges += 1
            je_tag = {int(t): int(c) for t, c in
                      zip(*np.unique(tag[sig], return_counts=True))}
            nb = nullband(pru & np.isfinite(W), je_tag)
            if not len(nb):
                continue
            npkt = float(nb.mean())
            b90 = float(np.percentile(nb, N.NULL_PERZENTIL))
            wert = float(REL[sig].mean())
            gut = wert > b90
            ok_n += 1 if gut else 0
            print("    %-9d %9d %+11.4f %+11.4f %+11.4f  %s"
                  % (i + 1, k, 100 * wert, 100 * npkt, 100 * b90,
                     "✔" if gut else "⛔ im Band"), flush=True)
        print("    ➤ %d von %d Fenstern" % (ok_n, ges))
        print()

    # ══ TEIL 2: JE ASSET ═════════════════════════════════════════════
    print("=" * 100)
    print("TEIL 2 - JE ASSET (Nutzervorgabe: wir messen nicht den Markt)")
    print("  Traegt die Ordnung auch symbolweise? Gemessen wird die")
    print("  Rangkorrelation zwischen `ema_abstand_atr` und dem Ertrag")
    print("  relativ zum Tag - negativ heisst: niedrig ist besser.")
    print()
    rhos = []
    for s in np.unique(S):
        m = (S == s) & np.isfinite(W)
        if m.sum() < 2000:
            continue
        a = np.argsort(np.argsort(W[m]))
        b = np.argsort(np.argsort(REL[m]))
        rhos.append(float(np.corrcoef(a, b)[0, 1]))
    rhos = np.array(rhos)
    print("  %d Symbole mit mindestens 2.000 Ankern" % len(rhos))
    print("  Rangkorrelation: Median %+.4f · negativ bei %d von %d (%.0f %%)"
          % (float(np.median(rhos)), int((rhos < 0).sum()), len(rhos),
             100 * float((rhos < 0).mean())))
    print("  Spanne %+.4f bis %+.4f" % (rhos.min(), rhos.max()))
    print("  ⚠️ Zufall traefe in rund 50 %% der Faelle ein negatives "
          "Vorzeichen.")

    # ══ TEIL 3: POSITIVKONTROLLE ═════════════════════════════════════
    print()
    print("=" * 100)
    print("TEIL 3 - POSITIVKONTROLLE (5 Ziehungen, Messstandard)")
    gefunden = 0
    alle_m = np.isfinite(W)
    for _z in range(5):
        sig = taeglich_beste(np.where(alle_m, W, np.nan), tag, 0.02)
        je_tag = {int(t): int(c) for t, c in
                  zip(*np.unique(tag[sig], return_counts=True))}
        gepflanzt = REL.copy()
        gepflanzt[sig] += 0.10
        sicher = REL
        globals()["REL"] = gepflanzt
        nb = nullband(alle_m, je_tag)
        wert = float(gepflanzt[sig].mean())
        globals()["REL"] = sicher
        if len(nb) and wert > float(np.percentile(nb, N.NULL_PERZENTIL)):
            gefunden += 1
    print("  %d von 5 gepflanzten Effekten gefunden  %s"
          % (gefunden, "✔" if gefunden >= 4 else "⛔ der Test ist zu stumpf"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
