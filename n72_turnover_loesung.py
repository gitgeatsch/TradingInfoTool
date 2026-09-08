# -*- coding: utf-8 -*-
"""N-72 — DIE LOESUNG FUER `turnover`: die Menge muss zur Datenlage passen (07.09.)

## Was N-71 ergeben hat

    R-R11    `pruefe_auswahl` reproduziert den Vorzeichenwechsel NICHT.
             Auf der FREIEN Menge ist turnover spaet +0,0402
             [+0,0105 .. +0,0752] - positiv, Band ohne Null.
             Auf der 20-%-Menge: +0,0070 [-0,0878 .. +0,0922],
             Urteil der Norm woertlich "KEIN BEFUND - untermaechtig".
    A ✔      5,3 gewaehlte Anker je Tag (frueh) bzw. 10,1 (spaet).
             funding hat 8,8 bzw. 33,4.
    B ✖      die Quelle ist in Ordnung. Der splycur-Ausreisser ab 2023
             ist XVG - aber eine grosse UMLAUFMENGE macht den Quotienten
             KLEIN. Die Kennzahl selbst ist stabil (Median 0,003-0,010,
             P95 0,036-0,079 ueber alle Jahre) und geht als RANG ein.
    D ✔      die EXTREME sind stabil: F0 +0,2314 -> +0,2745,
             F4 -0,1354 -> -0,1316. Nur die MITTE dreht.
             ⚠️ Und die Live-Regel sperrt F4.

> **Der Grund ist nicht der Beitrag, sondern die MENGE.** `turnover` deckt
> 66 von 524 Symbolen ab. 20 % davon sind zu wenige Anker fuer die
> Statistik - der "Vorzeichenwechsel" aus N-70 ist Rauschen.

## ⚠️⚠️ Warum das keine Ausrede ist, sondern eine Regel

Es waere billig, jetzt so lange Mengen auszuprobieren, bis eine passt
(Suchpreis!). Deshalb steht das Kriterium **vor** der Messung fest und
gilt fuer ALLE Beitraege gleich:

> **Die schmalste Menge, die noch mindestens 12 Anker je Tag liefert.**

Zwoelf, weil `sammle` selbst Tage unter 12 Werten verwirft - die Zahl ist
also nicht neu erfunden, sondern die im Code bereits gesetzte Untergrenze
(`if len(zeilen) < 12: continue`).

⚠️ **Das Kriterium wird auf alle vier Beitraege angewandt und
mitgedruckt** - auch dort, wo es die bisherige Wahl bestaetigt. Ein
Kriterium, das nur beim Problemfall gilt, ist keins.

## Was gemessen wird

    Fuer jeden Beitrag und jede Menge (frei / 50 % / 20 % / 10 % / 5 %):
      1  Anker je Tag  -> welche Menge erfuellt das Kriterium?
      2  die Wirkung mit `pruefe_auswahl`, spaete Aera (ab 2022)
      3  Kontrolle `zufall` in derselben Menge

⚠️ 50 % ist in `MENGEN` noch nicht vorgesehen. Hier wird sie NUR
gemessen; ob sie eingebaut wird, ist eine Folgeentscheidung.

    python n72_turnover_loesung.py
"""
from __future__ import annotations

import sys
import time

import numpy as np

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import messe_bewertungskennzahl as MB                        # noqa: E402
import messe_eigenschaft_beitrag as B                        # noqa: E402
import messe_funding_niveau as F                             # noqa: E402
import messe_kandidaten_als_regel as K                       # noqa: E402
import messnorm as N                                          # noqa: E402
import messnorm_auswahl as MA                                # noqa: E402
from messe_beitrag_auf_auswahl import (_auswahl_maske,       # noqa: E402
                                       momentum250)

HORIZONT = 20
AB = "2022"
MIND_ANKER = 12          # ⚠️ dieselbe Untergrenze wie in `sammle`
PRUEFMENGEN = ("frei", "50%", "20%", "10%", "5%")


def main() -> int:
    t0 = time.time()
    print("=" * 100)
    print("N-72 — die Menge muss zur DATENLAGE passen. Kriterium: >= %d Anker/Tag"
          % MIND_ANKER)
    print("=" * 100)
    reihen = B.lade()
    mom = momentum250(reihen)
    lage = N.Lage(instrument="spot", strategie="einstieg")
    zus = {"turnover": MB.reihe("data/onchain_historie.db", "splycur"),
           "funding": F.lade_funding()}
    try:
        zus["oi_aenderung"] = K.lade_terminmarkt()["oi_aenderung"]
    except Exception as exc:                                 # noqa: BLE001
        print("  ⚠️ oi_aenderung nicht ladbar: %s" % exc)

    # ⚠️ 50 % nur fuer diese Messung eintragen - NICHT eingebaut.
    if "50%" not in MA.MENGEN:
        MA.MENGEN["50%"] = 0.5
        print("  ⚠️ `50%%` nur fuer diesen Lauf in MENGEN eingetragen "
              "(Wert 0,5) - kein Einbau.")

    arten = ("turnover", "funding", "oi_aenderung", "zufall")
    welt = {a: K.baue(reihen, a, zus.get(a), horizont=HORIZONT)
            for a in arten if a in zus or a == "zufall"}
    spaet = {a: {t: z for t, z in w.items() if str(t) >= AB}
             for a, w in welt.items()}

    # ---- 1  DAS KRITERIUM, vor jeder Wirkung ---------------------------
    print()
    print("  1  ⚠️ ANKER JE TAG — das Kriterium steht VOR der Wirkung")
    print("     %-13s %9s %9s %9s %9s %9s   %s"
          % ("Beitrag", *PRUEFMENGEN, "schmalste >= 12"))
    wahl = {}
    for a in arten:
        if a not in spaet:
            continue
        zeile, gewaehlt = [], None
        for menge in PRUEFMENGEN:
            anteil = MA.MENGEN[menge]
            n = []
            for tag, z in spaet[a].items():
                if len(z) < 12:
                    continue
                m = _auswahl_maske(z, mom.get(tag) or {}, anteil, None)
                if m is not None and m.any():
                    n.append(int(m.sum()))
            mw = float(np.mean(n)) if n else 0.0
            zeile.append(mw)
        # ⚠️ SCHMALSTE Menge, die das Kriterium haelt - also die ERSTE
        # von schmal nach breit, dann ABBRECHEN. Die erste Fassung
        # ueberschrieb weiter und waehlte damit immer die BREITESTE
        # (`frei`) - genau das Gegenteil.
        for menge, mw in zip(reversed(PRUEFMENGEN), reversed(zeile)):
            if mw >= MIND_ANKER:
                gewaehlt = menge
                break
        wahl[a] = gewaehlt
        print("     %-13s %9.1f %9.1f %9.1f %9.1f %9.1f   %s"
              % (a, *zeile,
                 gewaehlt if gewaehlt else "⚠️ KEINE"))
    print("     ⚠️ `frei` ist keine Auswahl - sie beantwortet die MARKT-")
    print("        frage (P6). Als Beitragsmenge zaehlt sie nur, wenn")
    print("        keine echte Auswahl das Kriterium haelt.")

    # ---- 2  DIE WIRKUNG in jeder Menge ---------------------------------
    print()
    print("  2  DIE WIRKUNG ab %s — in jeder Menge" % AB)
    print("     %-13s %-6s %10s %24s %8s  %s"
          % ("Beitrag", "Menge", "Wirkung", "Band", "Tage", "Urteil"))
    for a in arten:
        if a not in spaet:
            continue
        for menge in PRUEFMENGEN:
            rng = np.random.default_rng(20260907)
            try:
                b = MA.pruefe_auswahl(a, spaet[a], mom, lage=lage,
                                      menge=menge, rng=rng,
                                      horizont=HORIZONT,
                                      hypothese="Menge nach Datenlage",
                                      verwendung="Beitrag")
            except Exception as exc:                         # noqa: BLE001
                print("     %-13s %-6s -> %s" % (a, menge, str(exc)[:50]))
                continue
            mark = "  <- gewaehlt" if wahl.get(a) == menge else ""
            print("     %-13s %-6s %+10.4f [%+.4f .. %+.4f] %8d  %s%s"
                  % (a, menge, b.wirkung, b.unten, b.oben, b.n_tage,
                     b.urteil.split(" (")[0][:32], mark), flush=True)
        print()

    # ---- Urteil ---------------------------------------------------------
    print("=" * 100)
    print("WAS DAS HEISST")
    print("=" * 100)
    print("  Die nach dem Kriterium gewaehlte Menge je Beitrag:")
    for a in arten:
        if a in wahl:
            print("     %-13s %s" % (a, wahl[a] or "⚠️ KEINE erfuellt es"))
    print()
    print("  ⚠️ Wenn `turnover` eine andere Menge braucht als `funding`,")
    print("     ist das KEIN Sonderrecht - es ist dieselbe Regel, auf eine")
    print("     andere Datenlage angewandt. Wer beide auf 20 % zwingt,")
    print("     misst bei einem von beiden Rauschen.")
    print("  Dauer %.1f Minuten" % ((time.time() - t0) / 60.0))
    return 0


if __name__ == "__main__":
    sys.exit(main())
