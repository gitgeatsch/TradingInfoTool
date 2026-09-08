# -*- coding: utf-8 -*-
"""N-73 — DIE DURCHSICHT: stand ein Kandidat auf zu duenner Menge? (07.09.)

## Warum diese Durchsicht faellig ist

`turnover` schien ab 2022 zu drehen. Der Grund war nicht der Beitrag,
sondern die MENGE: bei 66 von 524 Symbolen sind 20 % nur 10,1 Anker je
Tag. Auf 50 % ist er positiv (2.162).

> **Alle frueheren Beitragsmessungen liefen auf 20 % oder 5 %, ohne dass
> je geprueft wurde, ob die Datenlage das traegt.**

`menge_nach_datenlage()` beantwortet das seit dem 07.09. in Sekunden.
Diese Datei wendet es auf JEDEN Kandidaten des Registers an.

## Was gemessen wird

Je Kandidat, auf der ganzen Historie:

    1  welche Menge verlangt seine Datenlage?
       (schmalste mit >= 12 Ankern/Tag UND >= 20 Bloecken)
    2  das Urteil auf der BISHER benutzten Menge
    3  das Urteil auf der RICHTIGEN Menge
    4  aendert sich etwas?

⚠️ **Die bisher benutzte Menge steht im Register**, sie wird hier NICHT
geraten: `funding`/`turnover`/`oi_aenderung` wurden zuletzt auf `frei`
und `5%`/`20%` gemessen (messbasis_anker.json), die offenen Kandidaten
auf `20%` (N-59, N-63) bzw. `frei` (N-52 bis N-58, die Audit-Faelle).
Verglichen wird deshalb gegen BEIDE gaengigen Mengen.

## ⚠️ Was diese Datei NICHT tut

Sie stellt **kein** Urteil um. Sie zeigt, wo eines zu pruefen ist. Ein
Kandidat, dessen Urteil sich mit der Menge aendert, braucht eine eigene
Messung mit Zufallskontrolle und Trennschaerfe - nicht diese Uebersicht.

## Die Kontrolle

`zufall` laeuft mit und darf auf KEINER Menge tragen. Traegt er, ist die
Durchsicht wertlos.

    python n73_durchsicht_kandidaten.py
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
from messe_beitrag_auf_auswahl import momentum250            # noqa: E402

HORIZONT = 20
# ⚠️ Die Kandidaten des Registers, soweit `baue` sie erzeugen kann.
# `vola ODER turnover` ist eine Kombination und faellt hier heraus -
# sie braucht ihr eigenes Werkzeug.
KANDIDATEN = ("funding", "turnover", "oi_aenderung", "vola", "schnitt",
              "schnitt50", "amihud", "rsi", "momentum", "zufall")
VERGLEICH = ("frei", "20%", "5%")


def kurz(urteil: str) -> str:
    u = urteil.split(" (")[0].split(" - ")[0]
    return u[:26]


def traegt(b) -> bool:
    """⚠️ ZWEISEITIG und gegen den Nullpunkt - wie `messnorm` es meint."""
    return bool(getattr(b, "traegt", False))


def main() -> int:
    t0 = time.time()
    print("=" * 104)
    print("N-73 — DURCHSICHT: stand ein Kandidat auf einer zu duennen Menge?")
    print("=" * 104)
    reihen = B.lade()
    mom = momentum250(reihen)
    lage = N.Lage(instrument="spot", strategie="einstieg")
    zus = {"funding": F.lade_funding(),
           "turnover": MB.reihe("data/onchain_historie.db", "splycur")}
    try:
        zus["oi_aenderung"] = K.lade_terminmarkt()["oi_aenderung"]
    except Exception as exc:                                 # noqa: BLE001
        print("  ⚠️ Terminmarkt nicht ladbar: %s" % exc)

    print("  %d Reihen . H%d . Kriterium >= %d Anker/Tag UND >= 20 Bloecke"
          % (len(reihen), HORIZONT, MA.MIND_ANKER))
    print()
    print("  1  WELCHE MENGE VERLANGT DIE DATENLAGE?")
    print("     %-14s %8s %10s %10s   %s"
          % ("Kandidat", "Symbole", "Werte/Tag", "-> Menge", "Anmerkung"))
    welt, wahl = {}, {}
    for a in KANDIDATEN:
        try:
            je = K.baue(reihen, a, zus.get(a), horizont=HORIZONT)
        except Exception as exc:                             # noqa: BLE001
            print("     %-14s -> %s" % (a, str(exc)[:60]))
            continue
        if not je:
            print("     %-14s -> leere Welt" % a)
            continue
        welt[a] = je
        syms = len({x["sym"] for z in je.values() for x in z})
        proTag = float(np.mean([len(z) for z in je.values()]))
        g = MA.menge_nach_datenlage(je, mom, horizont=HORIZONT)
        wahl[a] = g
        print("     %-14s %8d %10.1f %10s   %s"
              % (a, syms, proTag, g or "KEINE",
                 "" if g else "⚠️ keine Auswahl traegt die Frage"),
              flush=True)

    print()
    print("  2  DAS URTEIL — auf der richtigen Menge gegen die gaengigen")
    print("     %-14s %-6s %10s %22s  %s"
          % ("Kandidat", "Menge", "Wirkung", "Band", "Urteil"))
    erg = {}
    for a in KANDIDATEN:
        if a not in welt:
            continue
        mengen = []
        for m in ((wahl[a],) if wahl[a] else ()) + VERGLEICH:
            if m and m not in mengen:
                mengen.append(m)
        for m in mengen:
            rng = np.random.default_rng(20260907)
            try:
                b = MA.pruefe_auswahl(a, welt[a], mom, lage=lage, menge=m,
                                      rng=rng, horizont=HORIZONT,
                                      hypothese="Durchsicht 07.09.",
                                      verwendung="Beitrag")
            except Exception as exc:                         # noqa: BLE001
                print("     %-14s %-6s -> %s" % (a, m, str(exc)[:44]))
                continue
            erg[(a, m)] = b
            mark = "  <- Datenlage" if m == wahl[a] else ""
            print("     %-14s %-6s %+10.4f [%+.4f .. %+.4f]  %s%s"
                  % (a, m, b.wirkung, b.unten, b.oben, kurz(b.urteil), mark),
                  flush=True)
        print()

    # ---- 3  WO AENDERT SICH ETWAS? -------------------------------------
    print("=" * 104)
    print("  3  ⚠️ WO WEICHT DAS URTEIL AB? — nur hier ist etwas zu tun")
    print("=" * 104)
    zf = [erg.get(("zufall", m)) for m in VERGLEICH + (wahl.get("zufall"),)]
    if any(x is not None and traegt(x) for x in zf):
        print("  ⚠️⚠️ `zufall` traegt auf einer Menge - die Durchsicht ist")
        print("     wertlos.")
        return 1
    print("  ✔ `zufall` traegt auf keiner Menge.")
    print()
    offen = []
    for a in KANDIDATEN:
        if a == "zufall" or a not in welt or not wahl.get(a):
            continue
        richtig = erg.get((a, wahl[a]))
        if richtig is None:
            continue
        for m in VERGLEICH:
            if m == wahl[a]:
                continue
            anders = erg.get((a, m))
            if anders is None:
                continue
            if traegt(richtig) != traegt(anders):
                offen.append((a, wahl[a], m, richtig, anders))
    if not offen:
        print("  ✔✔ KEIN Kandidat aendert sein Urteil mit der Menge.")
        print("     Die bisherigen Befunde stehen - `turnover` war der")
        print("     Einzelfall, nicht die Regel.")
    else:
        print("  ⚠️⚠️ %d Faelle, in denen die Menge das Urteil dreht:"
              % len(offen))
        for a, mr, mf, br, bf in offen:
            print("     %-14s auf %-5s %s  ·  auf %-5s %s"
                  % (a, mr, "TRAEGT" if traegt(br) else "traegt nicht",
                     mf, "TRAEGT" if traegt(bf) else "traegt nicht"))
            print("        %+.4f [%+.4f .. %+.4f]  gegen  %+.4f [%+.4f .. %+.4f]"
                  % (br.wirkung, br.unten, br.oben,
                     bf.wirkung, bf.unten, bf.oben))
        print()
        print("     ⚠️ Das ist KEIN neues Urteil - es ist die Liste dessen,")
        print("        was eine eigene Messung braucht.")
    print()
    print("  Dauer %.1f Minuten" % ((time.time() - t0) / 60.0))
    return 0


if __name__ == "__main__":
    sys.exit(main())
