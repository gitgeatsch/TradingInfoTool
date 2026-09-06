# -*- coding: utf-8 -*-
"""N19-E — DIE NEUKALIBRIERUNG, gemessen statt umgerechnet (06.09.2026)

## Warum

N19 hat gezeigt: die Umrechnung `d(quote) = d(Potential)/(1+CRV)` traegt
bei `funding` (Faktor 0,30) und `turnover` (0,35) NICHT. Die registrierten
Stufen sind auch nach der Halbierung 1,47x bzw. 1,85x zu gross.

**Der Ausweg ist, die Quotenverschiebung DIREKT zu messen** - sie ist genau
das, was `BEITRAEGE.stufen` erwartet: *„Prozentpunkte auf die Quote, nicht
R"* (`rechne_funding_beitrag.py`, Kopf).

## ⚠️ Die Frage, die der Lauf mitbeantworten muss

Auf WELCHEM Horizont wird kalibriert?

    H20   die Basis, auf der registriert wurde
    H5    der Betriebshorizont (Basisloesung 2.111)

N10 hat gemessen, dass der Umrechnungsfaktor horizontabhaengig ist und sich
umkehrt (1,78 bei H5, 0,77 bei H20). **Auf dem falschen Horizont
kalibrieren heisst, die Stufen fuer eine andere Frage zu setzen.**

## Was gemessen wird

    je Fuenftel   d(Barrieren-Quote) = Trefferquote im Fuenftel
                  minus Trefferquote des Tages, je Kalendertag
    Band          Blockbootstrap ueber die Tagesreihe
    Kontrolle     gemischte Raenge muessen flach liegen
    Monotonie     MIT Band - ueberlappen Nachbarn, ist die Ordnung
                  nicht belegt (die Lehre aus O4)

## Was NICHT entschieden wird

⚠️ Ob die Stufen geaendert werden, ist eine **Nutzerentscheidung** (R-R9):
sie zieht `potential.KALIBRIERT_FUER`, eine neue Schwellenkalibrierung und
`Befundkarte.md` 3.9 nach sich. Dieser Lauf liefert die ZAHLEN, nicht die
Aenderung.

    python n19e_neukalibrierung.py
"""
from __future__ import annotations

import sys
import time

import numpy as np

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import messe_bewertungskennzahl as MB                        # noqa: E402
import messe_eigenschaft_beitrag as B                        # noqa: E402
import messe_funding_niveau as F                             # noqa: E402
import messe_regel_wirksamkeit as W                          # noqa: E402

CRV, BRUCH, FAECHER = 2.0, 5.0, 5
SCHRUMPF = 0.5          # wie bisher: in-sample, deshalb halbiert

REGISTRIERT = {
    "funding": (+0.82, +1.30, +0.12, -0.54, -1.70),
    "turnover": (+3.15, +0.83, +0.22, -1.79, -2.40),
}


def baue(reihen, zusatz, art, horizont):
    je_tag: dict = {}
    for sym, z in reihen.items():
        tage = [x[0] for x in z]
        c = np.array([x[1] for x in z], float)
        h = np.array([x[2] for x in z], float)
        t = np.array([x[3] for x in z], float)
        br = B.spanne(h, t, c, B.SCHWANKUNG)
        vh = c[1:] / np.maximum(c[:-1], 1e-12)
        bruch = (vh > BRUCH) | (vh < 1.0 / BRUCH)
        je_sym = (zusatz or {}).get(sym.upper()) or {}
        for i in range(B.SCHWANKUNG, len(c) - horizont):
            if not np.isfinite(br[i]) or br[i] <= 0 or bruch[i:i + horizont].any():
                continue
            if art == "vola":
                if i < 260:
                    continue
                kz = float(br[i] / np.median(br[i - 250:i + 1]))
            else:
                w = je_sym.get(tage[i])
                if w is None:
                    continue
                kz = float(w)
            ziel, stop = c[i] + CRV * br[i], c[i] - 1.0 * br[i]
            aus = 0
            for j in range(i + 1, i + horizont + 1):
                if t[j] <= stop:
                    aus = -1
                    break
                if h[j] >= ziel:
                    aus = +1
                    break
            je_tag.setdefault(tage[i], []).append(
                {"kennzahl": kz, "treffer": 1.0 if aus > 0 else 0.0,
                 "offen": 1.0 if aus == 0 else 0.0})
    return {t: z for t, z in je_tag.items() if len(z) >= 3 * FAECHER}


def stufen_je_tag(je_tag, mische=None):
    reihen = [dict() for _ in range(FAECHER)]
    for tag, z in je_tag.items():
        w = np.array([x["kennzahl"] for x in z], float)
        y = np.array([x["treffer"] for x in z], float)
        r = W.rang(w)
        if mische is not None:
            r = mische.permutation(r)
        f = np.minimum((r * FAECHER).astype(int), FAECHER - 1)
        basis = float(y.mean())
        for i in range(FAECHER):
            m = f == i
            if m.sum() >= 3:
                reihen[i][tag] = float(y[m].mean()) - basis
    return reihen


def band(d, block, zieh=2000, saat=20260906):
    rng = np.random.default_rng(saat)
    x = np.array([d[k] for k in sorted(d)], float)
    n = len(x)
    if n < block + 30:
        return None
    nb = max(1, n // block)
    st = np.arange(n - block + 1)
    aus = np.empty(zieh)
    for k in range(zieh):
        s = rng.choice(st, nb)
        aus[k] = np.concatenate([x[i:i + block] for i in s]).mean()
    return (float(x.mean()), float(np.percentile(aus, 2.5)),
            float(np.percentile(aus, 97.5)))


def main() -> int:
    t0 = time.time()
    print("Lade Reihen ...", flush=True)
    reihen = B.lade()
    quellen = {"funding": F.lade_funding(),
               "turnover": MB.reihe("data/onchain_historie.db", "splycur"),
               "vola": None}

    for horizont in (20, 5):
        block = max(15, 3 * horizont)
        print()
        print("#" * 104)
        print("# HORIZONT %d · Block %d" % (horizont, block))
        print("#" * 104)
        for art, zusatz in quellen.items():
            je_tag = baue(reihen, zusatz, art, horizont)
            if len(je_tag) < 300:
                print("  %-10s zu wenige Tage (%d)" % (art, len(je_tag)))
                continue
            n = sum(len(z) for z in je_tag.values())
            offen = float(np.mean([x["offen"] for z in je_tag.values()
                                   for x in z]))
            print()
            print("  %s — %d Anker · %d Tage · %.1f %% offen"
                  % (art.upper(), n, len(je_tag), 100 * offen))
            echt = [band(d, block) for d in stufen_je_tag(je_tag)]
            null = [band(d, block) for d in
                    stufen_je_tag(je_tag, np.random.default_rng(4242))]
            reg = REGISTRIERT.get(art)
            print("    %-9s %26s %10s %10s  %s"
                  % ("Fuenftel", "GEMESSEN [Band]", "geschr.",
                     "registr.", "Zufallskontrolle"))
            neu = []
            for i in range(FAECHER):
                if echt[i] is None:
                    print("    %-9d  zu wenige Tage" % i); continue
                g = 100 * echt[i][0]
                neu.append(g * SCHRUMPF)
                print("    %-9d %+8.3f [%+7.3f..%+7.3f] %10.2f %10s  "
                      "%+7.3f [%+6.3f..%+6.3f]"
                      % (i, g, 100 * echt[i][1], 100 * echt[i][2],
                         g * SCHRUMPF,
                         ("%+.2f" % reg[i]) if reg else "-",
                         100 * null[i][0], 100 * null[i][1],
                         100 * null[i][2]), flush=True)
            if len(neu) == FAECHER and all(e for e in echt):
                getrennt = sum(1 for i in range(FAECHER - 1)
                               if echt[i][1] > echt[i + 1][2]
                               or echt[i][2] < echt[i + 1][1])
                fall = all(echt[i][1] > echt[i + 1][2]
                           for i in range(FAECHER - 1))
                stg = all(echt[i][2] < echt[i + 1][1]
                          for i in range(FAECHER - 1))
                nullflach = all(z[1] <= 0 <= z[2] for z in null if z)
                print("    -> %s · %d von 4 Nachbarpaaren getrennt · "
                      "Kontrolle %s"
                      % ("MONOTON MIT BAND" if (fall or stg)
                         else "Ordnung NICHT durchgehend belegt",
                         getrennt, "flach ✔" if nullflach else "⚠️ NICHT flach"))
                if reg:
                    sp_g = max(neu) - min(neu)
                    sp_r = max(reg) - min(reg)
                    print("    -> Spanne geschrumpft %.2f Pkt gegen "
                          "registriert %.2f Pkt · Faktor %.2f"
                          % (sp_g, sp_r, sp_r / sp_g if sp_g else 0))
    print()
    print("  ⚠️ Dieser Lauf liefert ZAHLEN, keine Aenderung. Ob die Stufen")
    print("     geaendert werden, ist eine Nutzerentscheidung (R-R9).")
    print("  Dauer %.1f Minuten" % ((time.time() - t0) / 60.0))
    return 0


if __name__ == "__main__":
    sys.exit(main())
