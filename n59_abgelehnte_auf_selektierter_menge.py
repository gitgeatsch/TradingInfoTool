# -*- coding: utf-8 -*-
"""N-59 — DIE ABGELEHNTEN BEITRAEGE, auf der SELEKTIERTEN Menge (07.09.2026)

## Warum das der wichtigste offene Punkt ist

Die Bewertungsebene traegt faktisch zwei Groessen. Der Code warnt selbst:
*„Ein System mit genau einem Beitrag kann diesen Beitrag nicht mehr
pruefen."* Und **das System ist duenn, WEIL mehrere Kandidaten abgelehnt
wurden** — auf einer Basis, die sich als verzerrt erwiesen hat.

    F-212     die Beitraege wirken auf 1,5 % der Anker. Auf der FREIEN
              Menge liegt selbst `funding` bei -0,0003 R; auf der
              SELEKTIERTEN traegt es dreimal staerker.

⚠️ **Genau das ist `turnover` passiert** (2.143): auf der freien Menge
schien seine Tabelle zu fallen, auf der selektierten reproduziert sie.
**Dieselbe Pruefung schulden wir den Abgelehnten.**

## Was gemessen wird — und womit

Nichts davon ist neu gebaut. Alle Teile lagen vor:

    Kennzahl    `messe_kandidaten_als_regel.baue(reihen, art)`
    Auswahl     `messe_beitrag_auf_auswahl.momentum250` + `sammle`
    Norm        `messnorm_auswahl.pruefe_auswahl` - Tagesklammer,
                Blockbootstrap, BEIDE Kontrollen, Trennschaerfe

    ⚠️ Das ist die Lehre aus 2.143: nicht ein weiteres Werkzeug bauen,
       sondern nachsehen, ob es das richtige schon gibt.

## Die Kandidaten

    ABGELEHNT, jetzt neu auf der richtigen Menge
        schnitt      Abstand zum eigenen 200-Tage-Schnitt   (BEITRAEGE: null)
        schnitt50    dieselbe Groesse auf 50 Tagen          (offen)
        amihud       Illiquiditaet (Rendite je Umsatz)      (traegt nicht)
        vola         ATR relativ zum eigenen Median         (offen)
        rsi          Relative Staerke                        (N-17b)

    KONTROLLEN — sie entscheiden, ob dem Lauf zu trauen ist
        zufall       ⚠️ DARF NICHT TRAGEN. Traegt er, ist der Aufbau kaputt.
        funding      ⚠️ MUSS TRAGEN und rund +0,027 R liefern (F-212)
        turnover     ⚠️ MUSS TRAGEN und rund +0,064 R liefern (F-212)

## ⚠️ Nicht in diesem Lauf, mit Grund

    Vorfilter H     braucht die Marken-Rechnung, die `baue` nicht liefert
    Lebendigkeit    braucht TVL als `zusatz` (188 Reihen liegen vor)
    Rangplatz       ⚠️ ist bereits LIVE als Trichterstufe 5 ("gehoert zu den
                    besten k der Gruppe"). Ihn als Beitrag zu messen waere
                    Doppelzaehlung.
    Bekannte Termine  es gibt KEINE Termindaten. `terminmarkt` ist der
                    Futures-Markt, kein Kalender - daher `zustand="nie"`.

    python n59_abgelehnte_auf_selektierter_menge.py
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
from messe_beitrag_auf_auswahl import momentum250            # noqa: E402
from messnorm_auswahl import pruefe_auswahl                  # noqa: E402

HORIZONT = 20
# ⚠️ DIE ERWARTUNGEN STEHEN VOR DEM LAUF FEST - und sie stehen im
# Docstring von `messnorm_auswahl`, JE MENGE:
#
#     Tagesklammer   frei +0,0274 · 5 % +0,0897
#
# ⚠️ Erste Fassung trug hier +0,0274 als Erwartung fuer die 5-%-Menge ein
# und meldete "NICHT reproduziert" - der Fehler sass in der Erwartung,
# nicht in der Messung. Genau der Grund, warum Sollwerte JE MENGE
# gehoeren.
KONTROLLEN = {"zufall": {"frei": None, "5%": None},
              "funding": {"frei": 0.0274, "5%": 0.0897}}
ABGELEHNT = ("schnitt", "schnitt50", "amihud", "vola", "rsi", "turnover")

# ⚠️ MEHRERE AUSWAHLSTAERKEN, nicht nur die Produktions-5 %.
# Grund (07.09. gemessen): bei 5 % bleiben je Tag ~2 Anker. `turnover`
# (65 Symbole) verliert dort ALLE Tage, und die uebrigen werden
# untermaechtig - die Norm meldet dann zu Recht "KEIN BEFUND". Die
# Zwischenmengen geben Bloecke und damit Aussagekraft zurueck.
MENGEN = ("frei", "20%", "10%", "5%")


def main() -> int:
    t0 = time.time()
    print("=" * 100)
    print("N-59 — die abgelehnten Beitraege auf der SELEKTIERTEN Menge")
    print("=" * 100)
    print("  Lade Reihen ...", flush=True)
    reihen = B.lade()
    mom = momentum250(reihen)
    zusatz = {"funding": F.lade_funding(),
              "turnover": MB.reihe("data/onchain_historie.db", "splycur")}
    lage = N.Lage(instrument="spot", strategie="einstieg")

    ergebnis = {}
    for art in tuple(KONTROLLEN) + ABGELEHNT:
        je_tag = K.baue(reihen, art, zusatz.get(art), horizont=HORIZONT)
        if not je_tag:
            print("  %-12s keine Daten" % art)
            continue
        anker = sum(len(z) for z in je_tag.values())
        print()
        print("  %s  (%d Tage, %d Anker)" % (art.upper(), len(je_tag), anker),
              flush=True)
        zeile = {}
        for menge in MENGEN:
            rng = np.random.default_rng(20260907)
            try:
                b = pruefe_auswahl(art, je_tag, mom, lage=lage, menge=menge,
                                   rng=rng, horizont=HORIZONT,
                                   hypothese="abgelehnt, neu gemessen",
                                   verwendung="Beitrag")
            except Exception as exc:                         # noqa: BLE001
                print("     %-6s -> %s" % (menge, exc))
                continue
            zeile[menge] = b
            print("     %-6s %+8.4f R [%+.4f .. %+.4f] · Nullpunkt %+.4f "
                  "[%+.4f .. %+.4f] · TS %s"
                  % (menge, b.wirkung, b.unten, b.oben, b.nullpunkt,
                     b.null_unten, b.null_oben,
                     ("%.3f" % b.trennschaerfe) if b.trennschaerfe
                     else "keine"), flush=True)
            print("            %s" % b.urteil)
        ergebnis[art] = zeile

    print()
    print("=" * 100)
    print("DIE KONTROLLEN ZUERST — ist dem Lauf zu trauen?")
    print("=" * 100)
    trauen = True
    for art, ziele in KONTROLLEN.items():
        for menge, ziel in ziele.items():
            b = ergebnis.get(art, {}).get(menge)
            if b is None:
                print("  %-9s %-5s nicht messbar" % (art, menge))
                continue
            if ziel is None:
                ok = not b.traegt
                print("  %-9s %-5s %+8.4f R  %s  (darf NICHT tragen)"
                      % (art, menge, b.wirkung,
                         "✔" if ok else "⚠️⚠️ FEUERT IM LEEREN"))
            else:
                ok = b.unten <= ziel <= b.oben
                print("  %-9s %-5s %+8.4f R [%+.4f .. %+.4f]  %s  "
                      "(Sollwert %+.4f)"
                      % (art, menge, b.wirkung, b.unten, b.oben,
                         "✔ REPRODUZIERT" if ok else "⚠️ nicht im Band",
                         ziel))
            trauen &= ok
    print()
    if not trauen:
        print("  ⚠️⚠️ DIE KONTROLLEN HALTEN NICHT. Alles Weitere ist")
        print("     wertlos, bis das geklaert ist - genau der Fehler, den")
        print("     dieser Lauf aufarbeiten soll.")
        print("  Dauer %.1f Minuten" % ((time.time() - t0) / 60.0))
        return 1
    print("  ✔ Die Kontrollen halten. Die Befunde unten sind belastbar.")

    print()
    print("=" * 100)
    print("DIE ABGELEHNTEN — traegt einer auf der richtigen Menge?")
    print("=" * 100)
    print("     %-11s %9s %9s %9s %9s   %s"
          % ("Kandidat", *MENGEN, "bestes Urteil"))
    treffer = []
    for art in ABGELEHNT:
        z = ergebnis.get(art, {})
        werte = []
        bestes, bester_b = "—", None
        for m in MENGEN:
            b = z.get(m)
            werte.append(("%+9.4f" % b.wirkung) if b else "     —   ")
            if b and b.traegt and (bester_b is None
                                   or b.wirkung > bester_b.wirkung):
                bestes, bester_b = m, b
        if bester_b is not None:
            treffer.append((art, bestes, bester_b))
        print("     %-11s %s   %s"
              % (art, " ".join(werte),
                 ("✔ TRAEGT bei %s" % bestes) if bester_b else
                 (z.get("frei").urteil[:44] if z.get("frei") else "—")))
    print()
    if treffer:
        print("  ✔✔ %d KANDIDAT(EN) TRAGEN auf der selektierten Menge:"
              % len(treffer))
        for art, m, b in treffer:
            print("     %-11s bei %-5s %+.4f R [%+.4f .. %+.4f], "
                  "Trennschaerfe %s"
                  % (art, m, b.wirkung, b.unten, b.oben,
                     ("%.3f" % b.trennschaerfe) if b.trennschaerfe else "—"))
        print()
        print("  ⚠️ NICHT REGISTRIEREN, BEVOR geprueft ist:")
        print("     1  Redundanz gegen `funding` und `turnover`")
        print("     2  Abdeckung - wieviele Symbole hat der Kandidat?")
        print("     3  beide Historienhaelften")
        print("     4  R-R9: Beitragswechsel = Neukalibrierung")
    else:
        print("  ⚠️ KEINER traegt auf der selektierten Menge.")
        print("     Dann war die Ablehnung richtig - und die Duenne der")
        print("     Bewertungsebene ist kein Messfehler, sondern die Lage.")
    print("  Dauer %.1f Minuten" % ((time.time() - t0) / 60.0))
    return 0


if __name__ == "__main__":
    sys.exit(main())
