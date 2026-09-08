# -*- coding: utf-8 -*-
"""N-79 — DIE VIER KLASSEN: traegt in Nicht-Krypto irgendetwas? (N-8, 07.09.)

## Der Anlass

G-6 sperrt vier von fuenf Assetklassen nach DATENLAGE, nicht nach
Bewertung (2.152). In `aktien`, `themen_etf` und `rohstoffe` ist bis
heute **kein einziger Beitrag gemessen**.

## ⚠️ Der Datenbestand, VORHER durchgesehen (Nutzerhinweis 07.09.)

    Kursreihen        ✔ alle vier Klassen, inkl. `open` (100 % gefuellt)
    macro_snapshot    ✔ 3.384 Tage - gilt fuer ALLE Klassen
    makro_historie    ✔ 1.184 Monate - dito
    funding           ✖ Binance-Perpetuals, krypto
    splycur/adractcnt ✖ onchain, krypto
    terminmarkt       ✖ krypto
    tvl               ✖ DeFi, krypto

> **Fuer Nicht-Krypto bleiben die Kursreihen - und Makro.**

⚠️ **Makro ist aber KEIN Beitrag im Sinne dieser Maschinerie.** Sie hat
je Tag EINEN Wert fuer alle Assets; ein Querschnittsrang darueber ist
konstant. Makro waere ein REGIME-Schichter, und das ist eine eigene
Frage - hier nicht gemessen.

## ⚠️⚠️ Das GEMEINSAME ZEITFENSTER — sonst ist es kein Vergleich

    krypto      ab 2017-08
    aktien      ab 1972-06   (13.417 Handelstage)
    themen_etf  ab 1993-01
    rohstoffe   ab 2000-01

Krypto ab 2017 gegen Aktien ab 1972 zu stellen vergliche zwei Welten.
Alle Klassen laufen deshalb **ab 2018-01-01**. Das kostet Aktien den
groessten Teil ihrer Historie - und macht den Vergleich erst moeglich.

## Der Aufbau

    Kandidaten   die Kursreihen-Groessen: schnitt, vola, rsi, momentum
                 (amihud und schnitt50 sind in Krypto abgelehnt bzw.
                  offen - sie laufen mit, wenn Zeit bleibt)
    Menge        `zulaessige_mengen()` je Klasse, Urteil ueber ALLE (N-73)
    Zielgroesse  bewegung_r, H20
    Kontrolle    `zufall` je Klasse - er darf nirgends tragen

## Was ein Befund hier bedeuten wuerde

Traegt eine Kursreihen-Groesse in Aktien, aber nicht in Krypto, dann ist
der Grundbefund *"die Information steckt nicht in den Kursdaten"*
**krypto-spezifisch** - und nicht allgemein. Das waere der erste Hinweis
darauf, seit er am 10.08. aufgestellt wurde.

    python n79_nicht_krypto_klassen.py
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


def beschneide(reihen: dict, ab: str) -> dict:
    """Nur Tage ab `ab` - und nur Reihen, die danach noch lang genug sind.

    ⚠️ Der VORLAUF bleibt noetig: `schnitt` braucht 200 Tage Historie.
    Deshalb wird NICHT die Reihe abgeschnitten, sondern die Kandidatenwelt
    spaeter je Tag gefiltert. Hier faellt nur weg, was komplett vor `ab`
    liegt.
    """
    return {s: v for s, v in reihen.items() if v and v[-1][0] >= ab}


def main() -> int:
    t0 = time.time()
    print("=" * 104)
    print("N-79 — traegt in den Nicht-Krypto-Klassen irgendetwas? (ab %s)" % AB)
    print("=" * 104)
    lage = N.Lage(instrument="spot", strategie="einstieg")
    erg, zul = {}, {}

    for kl in KLASSEN:
        r = beschneide(B.lade(kl), AB)
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
            # ⚠️ Erst HIER auf das gemeinsame Fenster verengen - der
            # Vorlauf (200 Tage fuer `schnitt`) muss davor liegen duerfen.
            je = {t: z for t, z in je.items() if str(t) >= AB}
            if not je:
                print("     %-10s -> keine Tage ab %s" % (a, AB))
                continue
            mengen = MA.zulaessige_mengen(je, mom, horizont=HORIZONT)
            zul[(kl, a)] = mengen
            if not mengen:
                print("     %-10s ⚠️ KEINE zulaessige Menge (%d Tage, %.1f "
                      "Werte/Tag)"
                      % (a, len(je),
                         float(np.mean([len(z) for z in je.values()]))))
                continue
            for m in mengen:
                rng = np.random.default_rng(20260907)
                try:
                    b = MA.pruefe_auswahl(a, je, mom, lage=lage, menge=m,
                                          rng=rng, horizont=HORIZONT,
                                          hypothese="N-8 Assetklassen",
                                          verwendung="Beitrag")
                except Exception as exc:                     # noqa: BLE001
                    print("     %-10s %-6s -> %s" % (a, m, str(exc)[:44]))
                    continue
                erg[(kl, a, m)] = b
                print("     %-10s %-6s %+9.4f [%+.4f .. %+.4f]  %s"
                      % (a, m, b.wirkung, b.unten, b.oben, kurz(b.urteil)),
                      flush=True)

    # ---- Urteil ---------------------------------------------------------
    print()
    print("=" * 104)
    print("WAS DAS HEISST")
    print("=" * 104)
    for kl in KLASSEN:
        zf = [erg[k] for k in erg if k[0] == kl and k[1] == "zufall"]
        if not zf:
            continue
        if any(b.traegt for b in zf):
            print("  ⚠️⚠️ %s: `zufall` traegt - der Aufbau ist dort kaputt."
                  % kl)
            continue
        traeger = []
        for a in KANDIDATEN:
            if a == "zufall":
                continue
            mengen = [m for (k2, a2, m) in erg if k2 == kl and a2 == a]
            if not mengen:
                continue
            t = [m for m in mengen if erg[(kl, a, m)].traegt]
            if t:
                traeger.append("%s (%d/%d Mengen)" % (a, len(t), len(mengen)))
        print("  %-12s ✔ zufall sauber · %s"
              % (kl, ", ".join(traeger) if traeger
                 else "KEIN Kandidat traegt"))
    print()
    print("  ⚠️ Ein Kandidat, der nur auf EINER von mehreren zulaessigen")
    print("     Mengen traegt, ist nicht robust (N-73).")
    print("  Dauer %.1f Minuten" % ((time.time() - t0) / 60.0))
    return 0


if __name__ == "__main__":
    sys.exit(main())
