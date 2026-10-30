# -*- coding: utf-8 -*-
"""Selbsttest Messplan W §6 — VOR dem ersten Blick auf echte Ergebnisse. Gibt KEIN echtes Ergebnis aus.

Echte Erträge y, KÜNSTLICHE Signale; derselbe Rechenweg wie die Messung (``p102_wale_basis``):

    S1 Fehlalarm   1.000 Welten, E als AR(1) mit der echten Autokorrelation von E      Soll: TRÄGT in <= 5 % je Zelle
    S2 Ballung     1.000 Welten, E je Monat gleichgerichtet (Regime-Etikett)           Soll: <= 5 %
    S3 Auflösung   Ertrag += k im obersten, -k im untersten Fünftel (D verschiebt um 2k) X = kleinstes k mit >= 80 % gefunden
    D  Orakel      E = künftiger Ertrag + Rauschen gleicher Streuung                    Soll: TRÄGT in >= 95 %

Nullwelt (Vorab-Regel §5): gilt die, die S1 UND S2 in jeder Zelle <= 5 % hält; halten beide, Blockvertauschung.
Stufungsgrenze ausgewiesen: Nennniveau je Hypothese (5 %/6) + 2 Standardfehler.

    python -X utf8 Basisinfos/Rechenkern_02_10/p102_wale_selbsttest.py [--welten 1000]
"""
import json
import os
import socket
import sys
from datetime import datetime

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import p102_wale_basis as B  # noqa: E402

AUSGABE = os.path.join(B.HIER, "p102_wale_selbsttest.txt")
KS = (0.001, 0.0025, 0.005, 0.01, 0.02)


def ar1(rng, n, phi):
    e = np.empty(n)
    e[0] = rng.standard_normal()
    z = rng.standard_normal(n) * np.sqrt(max(1e-9, 1 - phi ** 2))
    for i in range(1, n):
        e[i] = phi * e[i - 1] + z[i]
    return e


def monatlich(rng, tg):
    m = np.array([d.year * 12 + d.month for d in tg])
    _, inv = np.unique(m, return_inverse=True)
    return rng.standard_normal(inv.max() + 1)[inv] + 0.2 * rng.standard_normal(len(tg))


def traegt(r):
    return r["stufe"].startswith("TRAEGT (")


def main() -> int:
    global AUSGABE
    welten = int(sys.argv[sys.argv.index("--welten") + 1]) if "--welten" in sys.argv else 1000
    arten = ("block", "kreis")
    if "--fassung3" in sys.argv:                                  # Messplan W Fassung 3 (vorab d5df61fb): einseitig, Nullwelt Block
        B.fassung3()
        AUSGABE = AUSGABE.replace(".txt", "_f3.txt")
        arten = ("block",)
    vorher = B.fingerabdruck()
    rng = np.random.default_rng(20261029)
    tg, aus = B.lade()
    ws = {s: B.maske(tg, B.urteil(s)) for s in B.SYMBOLE}
    w = ws[B.SYMBOLE[0]]
    zeilen = ["SELBSTTEST Messplan W%s (%s, %s, %d Welten) — echte Erträge, künstliche Signale, KEIN echtes Ergebnis%s"
              % (" FASSUNG 3" if B.EINSEITIG else "", socket.gethostname(), datetime.now().isoformat(timespec="seconds"), welten,
                 " · EINSEITIG (nur HÖHER zählt)" if B.EINSEITIG else "")]
    stufung = B.ALPHA / B.HYPOTHESEN + 2 * np.sqrt((B.ALPHA / B.HYPOTHESEN) * (1 - B.ALPHA / B.HYPOTHESEN) / welten)
    zeilen.append("Soll S1/S2 <= 5 %% je Zelle (vorab) · Stufungsgrenze %.1f %% ausgewiesen · Urteilsfenster %s"
                  % (100 * stufung, " · ".join("%s %s bis %s (%d T)" % (s[:3], *B.urteil(s), int(ws[s].sum())) for s in B.SYMBOLE)))
    fehl = {}                                                     # (art, welt, s, m, h) -> Quote
    phis = {}
    for s in B.SYMBOLE:
        for m in B.MAERKTE:
            e = aus[s]["markt"][m][B.Q_HAUPT][2]
            ok = np.isfinite(e[:-1]) & np.isfinite(e[1:])
            phis[(s, m)] = float(np.corrcoef(e[:-1][ok], e[1:][ok])[0, 1])
    zeilen.append("Autokorrelation (lag 1) der echten E, q 5 %%: %s" % ", ".join("%s %s %+.3f" % (s[:3], m, p) for (s, m), p in phis.items()))
    for welt in ("S1", "S2"):
        for s in B.SYMBOLE:
            for m in B.MAERKTE:
                w = ws[s]
                treffer = {(a, h): 0 for a in arten for h in B.HORIZONTE}
                for _ in range(welten):
                    e = ar1(rng, len(tg), phis[(s, m)]) if welt == "S1" else monatlich(rng, tg)
                    lab = B.fuenftel(e)[w]
                    for h in B.HORIZONTE:
                        y = aus[s]["y"][(h, 0)][w]
                        for a in arten:
                            treffer[(a, h)] += traegt(B.bewerte(lab, y, h, rng, art=a, mit_block=False))
                for (a, h), n in treffer.items():
                    fehl[(a, welt, s, m, h)] = n / welten
        print("  %s fertig" % welt, flush=True)
    zeilen.append("\nFEHLALARM (TRÄGT, Punkt 1) je Zelle — Spalten H 1 / 3 / 7 T")
    for a in arten:
        for welt in ("S1", "S2"):
            for s in B.SYMBOLE:
                for m in B.MAERKTE:
                    q = [fehl[(a, welt, s, m, h)] for h in B.HORIZONTE]
                    zeilen.append("  %-5s %s %s %-7s %s %s" % (a, welt, s, m, "  ".join("%5.1f %%" % (100 * x) for x in q),
                                                             "✔" if max(q) <= 0.05 else "✖ über 5 %"))
    halt = {a: all(v <= 0.05 for (aa, *_), v in fehl.items() if aa == a) for a in arten}
    art = "block" if halt["block"] else ("kreis" if halt.get("kreis") else None)     # Fassung 3: nur Block zulässig
    zeilen.append("\nNULLWELT nach Vorab-Regel: %s (%s)" % (art or "KEINE hält - NICHT MESSEN",
                                                         ", ".join("%s hält: %s" % (a, v) for a, v in halt.items())))
    if art is None:
        _schreibe(zeilen, vorher)
        return 1
    # S3 Auflösung und D Orakel mit der gewählten Nullwelt
    n3 = max(200, welten // 4)
    zeilen.append("\nS3 AUFLÖSUNG (%d Welten je k, Signal wie S1; Fundquote = TRÄGT HÖHER) — k in Pp, D verschiebt um 2k" % n3)
    xs = {}
    for s in B.SYMBOLE:
        for m in B.MAERKTE:
            w = ws[s]
            for h in B.HORIZONTE:
                y0 = aus[s]["y"][(h, 0)][w]
                quote = []
                for k in KS:
                    n = 0
                    for _ in range(n3):
                        lab = B.fuenftel(ar1(rng, len(tg), phis[(s, m)]))[w]
                        y = y0 + k * np.where(np.isfinite(lab), lab, 0)
                        r = B.bewerte(lab, y, h, rng, art=art, mit_block=False)
                        n += traegt(r) and r["D"] > r["nullpunkt"]
                    quote.append(n / n3)
                x = next((k for k, qq in zip(KS, quote) if qq >= 0.8), None)
                xs[(s, m, h)] = x
                zeilen.append("  %s %-7s H%d  %s  ->  X = %s" % (s, m, h, "  ".join("%.2f:%3.0f%%" % (100 * k, 100 * qq) for k, qq in zip(KS, quote)),
                                                               ("%.2f Pp (D-Unterschied %.2f Pp)" % (100 * x, 200 * x)) if x else "über 2 Pp"))
    zeilen.append("\nD ORAKEL (200 Welten, E = y + Rauschen gleicher Streuung) — Soll TRÄGT HÖHER in >= 95 %")
    orakel_ok = True
    for s in B.SYMBOLE:
        w = ws[s]
        for h in B.HORIZONTE:
            yv = aus[s]["y"][(h, 0)]
            sd = np.nanstd(yv)
            n = 0
            for _ in range(200):
                e = np.where(np.isfinite(yv), yv, 0) + sd * rng.standard_normal(len(tg))
                r = B.bewerte(B.fuenftel(e)[w], yv[w], h, rng, art=art, mit_block=False)
                n += traegt(r) and r["D"] > r["nullpunkt"]
            orakel_ok &= n >= 190
            zeilen.append("  %s H%d  %3d von 200 %s" % (s, h, n, "✔" if n >= 190 else "✖"))
    bestanden = orakel_ok
    zeilen.append("\nERGEBNIS: %s · Nullwelt %s · X je Zelle siehe S3" % ("BESTANDEN" if bestanden else "NICHT BESTANDEN", art))
    _schreibe(zeilen, vorher)
    if welten >= 1000:                                            # nur der Lauf nach Projektstandard gibt die Messung frei
        with open(AUSGABE.replace(".txt", ".json"), "w", encoding="utf-8") as f:
            json.dump({"bestanden": bool(bestanden), "nullwelt": art, "welten": welten,
                       "X": {"%s|%s|%d" % k: v for k, v in xs.items()}}, f, indent=1)
    return 0 if bestanden else 1


def _schreibe(zeilen, vorher):
    nachher = B.fingerabdruck()
    zeilen.append("Seiteneffekt: geschützte Datei unverändert: %s" % (vorher == nachher))
    text = "\n".join(zeilen)
    print(text)
    with open(AUSGABE, "w", encoding="utf-8") as f:
        f.write(text + "\n")


if __name__ == "__main__":
    sys.exit(main())
