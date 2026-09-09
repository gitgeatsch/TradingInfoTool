# -*- coding: utf-8 -*-
"""K-1w — Tragen die Beiträge auf der WATCHLIST? (09.09.2026)

## Warum diese Messung vor allen anderen kommt

Befund 2.228: die drei live registrierten Beitraege stehen auf `frei` -
das ist nach P6/F-212 die MARKT-Frage. F-212 verlangt aber, einen BEITRAG
auf der SELEKTIERTEN Menge zu beurteilen.

⚠️⚠️ **Der Streit ist der falsche.** K-1b hat gezeigt: die Kette arbeitet
gar nicht auf einer momentum-selektierten Menge - von 43 Krypto-Werten
passieren die meisten, WEIL der Nutzer sie haelt. Damit modelliert
**weder `frei` (536 Symbole) noch eine Momentum-Menge** das, worauf die
Kette wirkt.

> **Die Kette arbeitet auf einer WATCHLIST von 43 Werten.** Ob die
> Beitraege DORT tragen, ist nie gemessen worden - und davon haengen K-1c,
> K-2 und K-3 ab.

## ⚠️⚠️ Die Falle, die das Register benennt

    ⚠️ DER RANG MUSS UEBER DIE MESSBASIS LAUFEN. Ueber die Watchlist
    gerangt DREHT DAS VORZEICHEN (+3,43 gegen -3,10, nur 54 % identische
    Fuenftel).                        - REGISTER_Kandidaten zu `schnitt`

Deshalb wird **ueber 536 Symbole gerangt und auf 43 gemessen** - genau
wie `marktrang` in der Produktion. `sammle(..., nur=...)` verengt NACH
dem Rang; wer stattdessen `je_tag` vorher filtert, misst etwas anderes.

## Der Aufbau

    Kandidaten   funding · turnover · oi_aenderung · schnitt · zufall
    Menge        `frei` - die Watchlist IST die Menge, keine weitere
                 Verengung (die Kette waehlt aus ihr nur k=2 zusaetzlich
                 zum Bestand)
    Rang         ueber die volle Messbasis, wie in der Produktion
    Vergleich    Messbasis (536) gegen Watchlist (43)
    Kontrolle    `zufall` an derselben Stelle

## Die Vorhersage, VOR dem Lauf (Methodik 2.80)

Die Watchlist ist eine **Auswahl des Nutzers** - keine Zufallsstichprobe.
Sie enthaelt ueberwiegend groessere, liquidere Werte.

    Erwartung   die Beitraege tragen weiter, aber SCHWAECHER: bei 43
                statt 313 Werten je Tag ist das Band deutlich breiter,
                und die Extreme des Querschnitts fehlen
    Gegenthese  sie tragen gar nicht mehr - dann steht die Bewertung der
                Kette auf einem Beleg, der fuer ihre Werte nicht gilt

⚠️ **Traegt keiner mehr, ist das der schwerste Befund des Projekts** -
dann waere die gesamte Bewertungsstufe fuer die laufende Kette unbelegt.
⚠️ Und es waere KEIN Widerspruch zu den bisherigen Befunden, sondern eine
Aussage ueber eine andere Menge.

    python k1w_beitrag_auf_der_watchlist.py
"""
from __future__ import annotations

import sqlite3
import sys
import time

import numpy as np

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import bestand as BE                                          # noqa: E402
import messe_eigenschaft_beitrag as B                         # noqa: E402
import messe_kandidaten_als_regel as K                        # noqa: E402
import messnorm as N                                          # noqa: E402
import messnorm_auswahl as MA                                # noqa: E402
from messe_alle_kandidaten import HORIZONT, zusatzquellen    # noqa: E402
from messe_beitrag_auf_auswahl import momentum250            # noqa: E402

DB = "data/tradinginfotool.db"
KANDIDATEN = ("funding", "turnover", "oi_aenderung", "schnitt", "zufall")


def watchlist() -> set:
    """Die 43 Krypto-Werte, auf denen die Kette laeuft.

    ⚠️ `asset_hebel_settings` ist die Liste, die der Lauf benutzt - eine
    Tabelle `watchlist` gibt es nicht. Gegengeprueft wird ueber die Zahl:
    43 ist die in F-172 und im Auswahlbefund genannte Groesse.
    """
    c = sqlite3.connect("file:%s?mode=ro" % DB, uri=True)
    s = {x[0].upper() for x in c.execute(
        "SELECT symbol FROM asset_hebel_settings")}
    c.close()
    return s


def kurz(u: str) -> str:
    return u.split(" (")[0].split(" - ")[0][:26]


def main() -> int:
    t0 = time.time()
    wl = watchlist()
    reihen = B.lade()
    mom = momentum250(reihen)
    lage = N.Lage(instrument="spot", strategie="einstieg")
    zus = zusatzquellen()

    print("=" * 108)
    print("K-1w — tragen die Beitraege auf der WATCHLIST der Kette?")
    print("=" * 108)
    print("  %s" % N.standardzeile())
    print("  Watchlist: %d Symbole · Messbasis: %d Reihen"
          % (len(wl), len(reihen)))
    print("  ⚠️ Rang ueber die MESSBASIS, gemessen auf der Watchlist -")
    print("     ueber die Watchlist gerangt dreht das Vorzeichen.")
    print("  In der Messbasis vorhanden: %d der %d Watchlist-Symbole"
          % (len(wl & set(reihen)), len(wl)))

    erg = {}
    print()
    print("  %-14s %-11s %9s %20s %8s %8s %7s  %s"
          % ("Kandidat", "Menge", "Wirkung", "Band", "Anker", "Symbole",
             "traegt", "Urteil"))
    for kand in KANDIDATEN:
        # ⚠️ Die REGISTRIERUNGSBASIS aus dem Register, nicht geraten -
        # dreimal an einem Tag ging genau das schief (Befund 2.227).
        try:
            menge, fenster = BE.messbasis(kand)
        except KeyError:
            menge, fenster = "", ""
        menge = menge or "frei"
        je0 = K.baue(reihen, kand, zus.get(kand), horizont=HORIZONT)
        if fenster and fenster != "voll":
            je0 = {t: z for t, z in je0.items() if str(t) >= fenster}
        for wie, nur in (("Messbasis", None), ("Watchlist", wl)):
            try:
                b = MA.pruefe_auswahl(
                    kand, je0, mom, lage=lage, menge=menge,
                    rng=np.random.default_rng(20260909), horizont=HORIZONT,
                    hypothese="K-1w Watchlist", verwendung="Beitrag",
                    nur=nur)
            except Exception as exc:                         # noqa: BLE001
                print("  %-14s %-11s -> %s" % (kand, wie, str(exc)[:52]))
                continue
            erg[(kand, wie)] = b
            print("  %-14s %-11s %+9.4f [%+.4f..%+.4f] %8d %8d %7s  %s"
                  % (kand, wie, b.wirkung, b.unten, b.oben, b.n_anker,
                     b.abdeckung_symbole, b.traegt, kurz(b.urteil)),
                  flush=True)
        print()

    # ---- Urteil ---------------------------------------------------------
    print("=" * 108)
    print("GILT DIE BEWERTUNG AUF DER MENGE, AUF DER DIE KETTE ARBEITET?")
    print("=" * 108)
    zf = erg.get(("zufall", "Watchlist"))
    if zf is not None:
        print("  Kontrolle `zufall` auf der Watchlist: %+.4f · %s"
              % (zf.wirkung, "⚠️ TRAEGT" if zf.traegt else "traegt nicht"))
        if zf.traegt:
            print("  ⚠️⚠️ Die Kontrolle traegt. Bei EINER Ziehung ist das "
                  "bei 2,7 % Fehlalarmquote")
            print("     unwahrscheinlich, aber moeglich - es ist KEIN "
                  "Beweis, dass der Lauf kaputt ist.")
            print("     Die uebrigen Ergebnisse sind mit Vorsicht zu lesen.")
    print()
    traeger, gefallen = [], []
    for kand in KANDIDATEN:
        if kand == "zufall":
            continue
        m = erg.get((kand, "Messbasis"))
        w = erg.get((kand, "Watchlist"))
        if m is None or w is None:
            continue
        pfeil = "%+.4f -> %+.4f" % (m.wirkung, w.wirkung)
        if w.traegt:
            traeger.append(kand)
            zus_txt = "✔ traegt auch auf der Watchlist"
        elif m.traegt:
            gefallen.append(kand)
            zus_txt = "⚠️⚠️ traegt auf der Messbasis, NICHT auf der Watchlist"
        else:
            zus_txt = "traegt auf keiner von beiden"
        print("  %-14s %-24s %8d -> %-8d Anker   %s"
              % (kand, pfeil, m.n_anker, w.n_anker, zus_txt))
    print()
    if not traeger:
        print("  ⚠️⚠️⚠️ KEIN Beitrag traegt auf der Watchlist. Dann steht "
              "die Bewertungsstufe")
        print("     der laufenden Kette auf einem Beleg, der fuer ihre "
              "Werte nicht gilt.")
    else:
        print("  Auf der Watchlist tragen: %s" % ", ".join(traeger))
        if gefallen:
            print("  ⚠️ Auf der Watchlist NICHT mehr: %s"
                  % ", ".join(gefallen))
    print()
    print("  ⚠️ Die Watchlist ist eine AUSWAHL DES NUTZERS, keine "
          "Zufallsstichprobe -")
    print("     ein Ergebnis hier gilt fuer DIESE Liste, nicht allgemein.")
    print("  Dauer %.1f Minuten" % ((time.time() - t0) / 60.0))
    return 0


if __name__ == "__main__":
    sys.exit(main())
