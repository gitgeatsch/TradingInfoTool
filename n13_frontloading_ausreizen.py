# -*- coding: utf-8 -*-
"""N13 — DIE ZWEI UNGENUTZTEN HEBEL BEIM FRONTLOADING (06.09.2026)

## Warum

**Nutzervorgabe:** *„ich möchte nicht, dass wir aufgrund einer Feststellung
das Gesamtkonzept scheitern lassen — löse die Probleme lösungsorientiert
und präzise."*

F-165 (01.09.) mass Frontloading und schloss *„zu klein für eine
Instrumentwahl"*. Zwei Hebel blieben dabei ungenutzt:

    KOMBINATION      turnover (+3,2 Punkte) und vola (+2,2) wurden EINZELN
                     gemessen, bei Rangkorrelation 0,05 - praktisch
                     unabhaengig. Die ODER-Form wurde nie geprueft.
                     N5 hat sie am Randmassstab mit +26 bis +34 % ueber
                     der besten Einzelgroesse gemessen.

    AUSWAHLBREITE    F-165 nahm fuer ALLE Kandidaten feste 20 %. In seiner
                     eigenen Tabelle waehlte `turnover` nur 21.825 Anker
                     (gegen 183.045 bei `vola`) und erzielte den GROESSTEN
                     Ausschlag. ⚠️ Die engste Auswahl war die beste -
                     ausgereizt wurde sie nie.

## ⚠️ Der richtige Vergleichsmassstab

Nicht "gegen einen perfekten Waehler", sondern **gegen den TAKT** - der
hat null gemessenen Vorteil. Nach Regel 1 darf er nie Signalgeber sein.

## Der Aufbau

Zielgroesse: `Frontloading = |R_kurz| / (|R_kurz| + |R_rest|)` - die
Groesse aus F-165, unveraendert. Gemessen wird die WEGWAHL-Wirkung wie
dort: Mittel ueber die Gewaehlten, mal Anteil der Gewaehlten.

    Breiten     20 % (F-165-Bezug) · 10 % · 5 % · 2 %
    Formen      vola · turnover · ODER · UND
    Kontrollen  Nullpunkt (5 Mischungen) · Positivkontrolle je Zelle

⚠️ Zusaetzlich die PRAKTISCHE Groesse aus F-165: der Anteil der Gewaehlten,
deren Bewegung frontlastiger ist als ein Zufallspfad - das ist die Zahl,
an der "49 % auf 52 %" gemessen wurde.

    python n13_frontloading_ausreizen.py
"""
from __future__ import annotations

import sys
import time

import numpy as np

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import messe_bewertungskennzahl as MB                        # noqa: E402
import messe_eigenschaft_beitrag as B                        # noqa: E402
import messe_form_kurz_gegen_lang as H1                      # noqa: E402
import messnorm as N                                         # noqa: E402

# Der Erwartungswert des Frontloadings auf einem reinen Zufallspfad -
# aus F-165 uebernommen, nicht neu erfunden.
ZUFALLSPFAD = 0.296
BREITEN = (0.20, 0.10, 0.05, 0.02)


def wahl(je_tag, art, anteil, mische=None, pflanze=0.0):
    """Wegwahl-Wirkung beim Frontloading — Bauform wie `H1.wahl_je_tag`.

    `art` ist "vola", "turnover", "oder" oder "und". Bei den Kombinationen
    werden BEIDE Raenge auf DERSELBEN Teilmenge gebildet (die Lehre aus N5,
    wo die asymmetrische Rangbildung ein falsches Ergebnis erzeugte).
    """
    aus, quoten = {}, []
    for tag, z in je_tag.items():
        zeilen = [x for x in z if x.get("frontloading") is not None
                  and x.get("vola") is not None
                  and x.get("turnover") is not None]
        if len(zeilen) < H1.MIN_JE_TAG:
            continue
        fl = np.array([float(x["frontloading"]) for x in zeilen], float)
        v = np.array([float(x["vola"]) for x in zeilen], float)
        t = np.array([float(x["turnover"]) for x in zeilen], float)
        if mische is not None:
            p = mische.permutation(len(zeilen))
            v, t = v[p], t[p]
        n = len(zeilen)
        k = max(1, int(round(n * anteil)))
        rv = np.argsort(np.argsort(v)) / max(n - 1, 1)
        rt = np.argsort(np.argsort(t)) / max(n - 1, 1)
        gr = 1.0 - anteil
        if art == "vola":
            gew = rv >= gr
        elif art == "turnover":
            gew = rt >= gr
        elif art == "oder":
            gew = (rv >= gr) | (rt >= gr)
        elif art == "und":
            gew = (rv >= gr) & (rt >= gr)
        else:
            raise ValueError(art)
        if gew.sum() < 3:
            continue
        f2 = fl.copy()
        if pflanze:
            f2[gew] = np.minimum(f2[gew] + pflanze, 1.0)
        basis = float(f2.mean())
        aus[tag] = float(f2[gew].mean() - basis) * float(gew.mean())
        quoten.append((float((f2[gew] > ZUFALLSPFAD).mean()),
                       float((f2 > ZUFALLSPFAD).mean()),
                       float(gew.mean())))
    return aus, quoten


def _band(d, rng, block):
    import contextlib
    import io as _io
    with contextlib.redirect_stdout(_io.StringIO()):
        return MB.urteil_tage("x", d, rng, block)


def main() -> int:
    t0 = time.time()
    print("Lade Reihen und H-1-Grundlage ...", flush=True)
    reihen = B.lade()
    je_tag = H1.baue(reihen, H1.lade_zusatz())
    print("  %d Tage · %d Anker"
          % (len(je_tag), sum(len(z) for z in je_tag.values())), flush=True)

    block = N._block(H1.KURZ)
    print()
    print("=" * 112)
    print("N13 — FRONTLOADING: KOMBINATION x AUSWAHLBREITE")
    print("=" * 112)
    print("  %-10s %-7s %10s %8s %9s  %s"
          % ("Form", "Breite", "Wirkung", "gewaehlt", "frontlast.",
             "VERSCHIEBUNG gegen Basis, mit Band"))
    bestes = None
    for art in ("vola", "turnover", "oder", "und"):
        for anteil in BREITEN:
            rng = np.random.default_rng(N.SAAT)
            d, q = wahl(je_tag, art, anteil)
            if not d or not q:
                print("  %-10s %-7s   keine Tage" % (art, "%.0f %%" % (100 * anteil)))
                continue
            h = _band(d, rng, block)
            if h is None:
                print("  %-10s %-7s   zu wenige Tage fuer ein Band"
                      % (art, "%.0f %%" % (100 * anteil)))
                continue
            no = []
            for z in range(N.ZIEHUNGEN):
                n0, _ = wahl(je_tag, art, anteil,
                             mische=np.random.default_rng(N.SAAT + z))
                nb = _band(n0, rng, block)
                if nb:
                    no.append(nb["oben"])
            traegt = h["unten"] > max(0.0, max(no) if no else 0.0)
            qa = np.array(q, float)
            fl_gew, fl_basis, ant = (100 * qa[:, 0].mean(),
                                     100 * qa[:, 1].mean(),
                                     100 * qa[:, 2].mean())
            # ⚠️ BAND AUF DIE ZITIERTE ZAHL (06.09.): "+4,5 Punkte" ist die
            # Zahl, mit der argumentiert wird - sie braucht ein eigenes
            # Band, nicht nur die anteilgewichtete Wirkung. Die
            # Quotenverschiebung je Tag IST eine Tagesreihe.
            tage_d = sorted(d)
            versatz = {t: 100.0 * (qa[i, 0] - qa[i, 1])
                       for i, t in enumerate(tage_d[:len(qa)])}
            vb = _band(versatz, np.random.default_rng(N.SAAT), block)
            marke = "✔" if traegt else " "
            print("  %-10s %-7s %+10.5f %8.1f%% %8.1f%%  %+.1f Punkte "
                  "[%+.1f .. %+.1f] %s"
                  % (art, "%.0f %%" % (100 * anteil), h["mittel"],
                     ant, fl_gew, fl_gew - fl_basis,
                     vb["unten"] if vb else float("nan"),
                     vb["oben"] if vb else float("nan"), marke), flush=True)
            if traegt and (bestes is None or fl_gew - fl_basis > bestes[1]):
                bestes = (("%s @ %.0f %%" % (art, 100 * anteil)),
                          fl_gew - fl_basis, ant)
        print()

    print("=" * 112)
    print("DIE PRAKTISCHE ZAHL — und der richtige Vergleich")
    print("=" * 112)
    print("  F-165 (01.09.): beste Regel verschob die Quote von 48,9 %% auf")
    print("                  52,0 %% = +3,2 Punkte (turnover @ 20 %%)")
    if bestes:
        print("  N13:            beste tragende Regel %s -> %+.1f Punkte"
              % (bestes[0], bestes[1]))
        print("                  waehlt %.1f %% der Anker" % bestes[2])
    print()
    print("  ⚠️ Der Vergleichsmassstab ist der TAKT - und der hat NULL")
    print("     gemessenen Vorteil. Nach Regel 1 darf er nie Signalgeber")
    print("     sein. Jeder gemessene Vorsprung ist eine Verbesserung.")
    print()
    print("  Dauer %.1f Minuten" % ((time.time() - t0) / 60.0))
    return 0


if __name__ == "__main__":
    sys.exit(main())
