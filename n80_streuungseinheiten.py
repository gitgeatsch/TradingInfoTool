# -*- coding: utf-8 -*-
"""N-80 — N-11: die Klassen in STREUUNGSEINHEITEN messen (08.09.2026)

## Warum

2.172: `bewegung_r` teilt durch `max(5 % Kurs, 0,75 ATR)`. Der Boden
bindet bei Krypto in 29,1 % der Anker, bei Aktien in 97,1 %, bei ETF in
99,2 %. Der Stop liegt dort 2,29 bzw. 4,43 ATR entfernt statt 0,75 - die
R-Werte sind je Klasse verschieden gestaucht.

    Streuung (IQA) von bewegung_r:
        krypto 3,710 · aktien 1,929 · rohstoffe 1,715 · themen_etf 0,905

**Der Aktien-Nullbefund war deshalb Untermacht, kein Nullbefund.**

## Die Loesung — die MESSUNG aendern, nicht die Produktion

Nutzerentscheidung 08.09.: *"Effekte in Streuungseinheiten messen."*

    in_r_normiert = in_r / IQA(Klasse)

Damit hat jede Klasse per Konstruktion die Streuung 1, und dieselben
Trennschaerfe-Stufen (0,02 / 0,05 / 0,10) bedeuten ueberall dasselbe.

⚠️ **Das aendert NICHTS an der Produktion.** Die Kette rechnet weiter mit
der echten Geometrie; nur die MESSUNG wird vergleichbar gemacht. Der
andere Weg - den 5-%-Boden je Klasse zu kalibrieren - haette die
Produktion geaendert und war deshalb nicht die Wahl.

## ⚠️ Was das mit den bisherigen Krypto-Zahlen macht

Krypto wird durch 3,710 geteilt, also werden die Zahlen KLEINER:
`schnitt` +0,1759 R -> +0,047 Einheiten. Das ist kein Verlust an
Wirkung, sondern ein anderer Massstab - und die Trennschaerfe schrumpft
mit.

⚠️ **Deshalb laeuft Krypto MIT.** Ohne es waere nicht zu sehen, ob die
Umrechnung die bekannte Rangfolge erhaelt.

## Der Aufbau — unveraendert ausser der Normierung

    Fenster      ab 2018-01-01, gemeinsam (bestaetigt 07.09.)
    Kandidaten   schnitt, vola, rsi, momentum
    Menge        `zulaessige_mengen()`, Urteil ueber ALLE (N-73)
    Kontrolle    `zufall` je Klasse

    python n80_streuungseinheiten.py
"""
from __future__ import annotations

import sys
import time

import numpy as np

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import messe_eigenschaft_beitrag as B                        # noqa: E402
import messe_kandidaten_als_regel as K                       # noqa: E402
import messnorm as N                                          # noqa: E402
import messnorm_auswahl as MA                                # noqa: E402
from messe_beitrag_auf_auswahl import momentum250            # noqa: E402

HORIZONT = 20
AB = "2018-01-01"
KLASSEN = ("krypto", "aktien", "themen_etf", "rohstoffe")
KANDIDATEN = ("schnitt", "vola", "rsi", "momentum", "zufall")


def kurz(u: str) -> str:
    return u.split(" (")[0].split(" - ")[0][:26]


def normiere(je_tag: dict) -> tuple:
    """Teilt `in_r` durch den Interquartilsabstand DIESER Welt.

    ⚠️ Der Nenner kommt aus DERSELBEN Welt, die gemessen wird - nicht aus
    einer separaten Rechnung. Zwei Nenner an zwei Orten waeren die Sorte
    Kopie, die still auseinanderlaeuft.
    """
    alle = np.array([x["in_r"] for z in je_tag.values() for x in z], float)
    alle = alle[np.isfinite(alle)]
    if len(alle) < 100:
        return je_tag, float("nan")
    iqa = float(np.percentile(alle, 75) - np.percentile(alle, 25))
    if not (iqa > 0):
        return je_tag, float("nan")
    return ({t: [{**x, "in_r": x["in_r"] / iqa} for x in z]
             for t, z in je_tag.items()}, iqa)


def main() -> int:
    t0 = time.time()
    print("=" * 104)
    print("N-80 (N-11) — die Klassen in STREUUNGSEINHEITEN, Fenster ab %s" % AB)
    print("=" * 104)
    lage = N.Lage(instrument="spot", strategie="einstieg")
    erg, iqas = {}, {}

    for kl in KLASSEN:
        r = {s: v for s, v in B.lade(kl).items() if v and v[-1][0] >= AB}
        if not r:
            print("  %-12s keine Reihen" % kl)
            continue
        mom = momentum250(r)
        print()
        print("  %s — %d Reihen" % (kl.upper(), len(r)))
        for a in KANDIDATEN:
            try:
                je = K.baue(r, a, None, horizont=HORIZONT)
            except Exception as exc:                         # noqa: BLE001
                print("     %-10s -> %s" % (a, str(exc)[:60]))
                continue
            je = {t: z for t, z in je.items() if str(t) >= AB}
            if not je:
                continue
            je, iqa = normiere(je)
            iqas.setdefault(kl, {})[a] = iqa
            mengen = MA.zulaessige_mengen(je, mom, horizont=HORIZONT)
            if not mengen:
                print("     %-10s ⚠️ KEINE zulaessige Menge" % a)
                continue
            for m in mengen:
                rng = np.random.default_rng(20260907)
                try:
                    b = MA.pruefe_auswahl(a, je, mom, lage=lage, menge=m,
                                          rng=rng, horizont=HORIZONT,
                                          hypothese="N-11 Streuungseinheiten",
                                          verwendung="Beitrag")
                except Exception as exc:                     # noqa: BLE001
                    print("     %-10s %-6s -> %s" % (a, m, str(exc)[:44]))
                    continue
                erg[(kl, a, m)] = b
                print("     %-10s %-6s %+9.4f [%+.4f .. %+.4f]  %s"
                      % (a, m, b.wirkung, b.unten, b.oben, kurz(b.urteil)),
                      flush=True)
        print("     (IQA-Nenner: %s)"
              % "  ".join("%s %.3f" % (a, v)
                          for a, v in (iqas.get(kl) or {}).items()))

    # ---- Urteil ---------------------------------------------------------
    print()
    print("=" * 104)
    print("WAS DAS HEISST — jetzt sind die Klassen VERGLEICHBAR")
    print("=" * 104)
    for kl in KLASSEN:
        zf = [erg[k] for k in erg if k[0] == kl and k[1] == "zufall"]
        if not zf:
            continue
        if any(b.traegt for b in zf):
            print("  ⚠️⚠️ %s: `zufall` traegt - Aufbau dort kaputt." % kl)
            continue
        zeilen = []
        for a in KANDIDATEN:
            if a == "zufall":
                continue
            mengen = [m for (k2, a2, m) in erg if k2 == kl and a2 == a]
            if not mengen:
                continue
            t = [m for m in mengen if erg[(kl, a, m)].traegt]
            best = max((erg[(kl, a, m)].wirkung for m in mengen), default=0.0)
            zeilen.append("%s %+.3f (%d/%d)" % (a, best, len(t), len(mengen)))
        print("  %-12s ✔ zufall sauber · %s" % (kl, " · ".join(zeilen)))
    print()
    print("  ⚠️ Die Zahl in Klammern ist 'traegt auf X von Y zulaessigen")
    print("     Mengen'. Nur X = Y ist robust (N-73).")
    print("  Dauer %.1f Minuten" % ((time.time() - t0) / 60.0))
    return 0


if __name__ == "__main__":
    sys.exit(main())
