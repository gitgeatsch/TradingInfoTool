# -*- coding: utf-8 -*-
"""N-70 — SIND DIE LEBENDEN BEITRAEGE ZEITSTABIL? (07.09.2026)

## Warum das jetzt kommt

N-68/N-69 haben `schnitt` an der Zeitstabilitaet scheitern lassen. Der
Test ist damit da - und **auf die LIVE laufenden Beitraege wurde er nie
angewandt.**

    funding        geprueft (N-68): stabil bis 0,05 R, traegt ab 2024
    turnover       NIE GEPRUEFT   - und er traegt die GROESSTEN Stufen
                                    des Systems (+3,15 bis -2,40)
    oi_aenderung   NIE GEPRUEFT   - Live-Sperre seit N-14

⚠️ **Wer einen Kandidaten an einer Huerde scheitern laesst, die die
laufenden Beitraege nie nehmen mussten, misst mit zweierlei Mass.** Das
ist kein Nachtrag, sondern die Gegenprobe zu N-69.

## ⚠️ F-171 hat es sogar angekuendigt

> *„das Band ist mit [+0,0203 .. +0,1111] sehr breit - eine um 0,9 %
> verschobene Ankermenge bewegt die Wirkung um 22 %. Die GROESSTEN Stufen
> des Systems stehen damit auf der unsichersten Zahl. Kein Fehler, aber
> beim naechsten Nachrechnen zuerst hier hinsehen."*

Das ist der naechste Nachrechnen.

## Der Aufbau — unveraendert aus N-68/N-69

    Stabilitaet   ist (erste Haelfte - zweite Haelfte) von null trennbar?
                  Trennschaerfe durch gepflanzten Unterschied.
    Heute         traegt er ab 2022 / 2023 / 2024 noch?
    Kontrolle     `zufall` in denselben Schnitten.

⚠️ Der Test erklaert zu OFT einen Unterschied (18 % Fehlalarm statt 10 %,
auf Kunstdaten gemessen). Ein gefundener Unterschied ist deshalb
vorsichtig zu lesen, ein Nullbefund dagegen stark.

    python n70_stabilitaet_der_lebenden.py
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
from messe_beitrag_auf_auswahl import momentum250            # noqa: E402
from messnorm import _block                                   # noqa: E402
from messnorm_auswahl import MENGEN                           # noqa: E402
from n68_zeitstabilitaet import (GEPFLANZT, SAAT,             # noqa: E402
                                 entzerrte_reihe, unterschied)
from n69_traegt_er_heute_noch import band_ab, schaerfe_ab     # noqa: E402

HORIZONT, MENGE = 20, "20%"
AB = ("2022", "2024")
MIN_BLOECKE = 20
KANDIDATEN = ("turnover", "oi_aenderung", "funding", "zufall")


def main() -> int:
    t0 = time.time()
    print("=" * 98)
    print("N-70 — sind die LEBENDEN Beitraege zeitstabil?")
    print("=" * 98)
    reihen = B.lade()
    mom = momentum250(reihen)
    anteil = MENGEN[MENGE]
    block = _block(HORIZONT)
    zus = {"funding": F.lade_funding(),
           "turnover": MB.reihe("data/onchain_historie.db", "splycur")}
    # ⚠️ Der Terminmarkt liegt in einer EIGENEN Quelle - `baue` erwartet
    # ihn als `zusatz`, sonst faellt der Kandidat still auf leer.
    try:
        zus["oi_aenderung"] = K.lade_terminmarkt()["oi_aenderung"]
    except Exception as exc:                                 # noqa: BLE001
        print("  ⚠️ oi_aenderung nicht ladbar: %s" % exc)

    werte = {}
    print("  %d Reihen . Menge %s . Block %d" % (len(reihen), MENGE, block))
    for art in KANDIDATEN:
        try:
            je = K.baue(reihen, art, zus.get(art), horizont=HORIZONT)
        except Exception as exc:                             # noqa: BLE001
            print("     %-13s -> %s" % (art, exc))
            continue
        if not je:
            print("     %-13s -> leere Welt, faellt aus" % art)
            continue
        werte[art] = entzerrte_reihe(je, mom, anteil)
        print("     %-13s %d Kalendertage, Gesamtwirkung %+.4f R"
              % (art, len(werte[art]),
                 float(np.mean(list(werte[art].values())))), flush=True)

    if "turnover" not in werte:
        print("  ⚠️⚠️ turnover fehlt - die Hauptfrage ist nicht messbar.")
        return 1

    tage = sorted(werte["turnover"])
    mitte = tage[len(tage) // 2]

    # ---- 1  STABILITAET ------------------------------------------------
    print()
    print("  1  IST DER UNTERSCHIED ZWISCHEN DEN HAELFTEN TRENNBAR?")
    print("     %-13s %9s %9s %9s %22s %8s  %s"
          % ("Kandidat", "erste", "zweite", "Diff", "Band", "Schaerfe",
             "Urteil"))
    for art in KANDIDATEN:
        if art not in werte:
            continue
        e = werte[art]
        ma = {t for t in e if t < mitte}
        mb = {t for t in e if t >= mitte}
        u = unterschied(e, ma, mb, block)
        if u is None:
            print("     %-13s  zu wenige Tage" % art)
            continue
        sch = None
        for g in GEPFLANZT:
            tr = sum(1 for z in range(5)
                     if (x := unterschied(e, ma, mb, block, saat=SAAT + 100 * z,
                                          zieh=400, versatz=g))
                     and (x["unten"] > 0 or x["oben"] < 0))
            if tr >= 4:
                sch = g
                break
        trennt = u["unten"] > 0 or u["oben"] < 0
        print("     %-13s %+9.4f %+9.4f %+9.4f [%+.4f .. %+.4f] %8s  %s"
              % (art, u["A"], u["B"], u["diff"], u["unten"], u["oben"],
                 "%.2f R" % sch if sch else ">%.2f" % max(GEPFLANZT),
                 "⚠️⚠️ INSTABIL" if trennt else
                 ("stabil bis %.2f R" % sch if sch else
                  "⚠️ unentschieden - zu unscharf")), flush=True)

    # ---- 2  TRAEGT ER HEUTE? -------------------------------------------
    print()
    print("  2  TRAEGT ER HEUTE NOCH?")
    print("     %-13s %-7s %9s %22s %8s   %s"
          % ("Kandidat", "ab", "Wirkung", "Band", "Bloecke", "Urteil"))
    for art in KANDIDATEN:
        if art not in werte:
            continue
        e = werte[art]
        for ab in ("2019",) + AB:
            b = band_ab(e, ab, block)
            if b is None:
                print("     %-13s %-7s  zu wenige Tage" % (art, ab))
                continue
            s = schaerfe_ab(e, ab, block) if art != "zufall" else None
            print("     %-13s %-7s %+9.4f [%+.4f .. %+.4f] %8d   %s"
                  % (art, "ganz" if ab == "2019" else "ab " + ab,
                     b["mittel"], b["unten"], b["oben"], b["bloecke"],
                     ("traegt" if b["unten"] > 0 else
                      "traegt nicht bis %.2f R" % s if s else
                      "traegt nicht")
                     + ("" if b["bloecke"] >= MIN_BLOECKE
                        else "  ⚠️ %d Bloecke" % b["bloecke"])),
                  flush=True)
        print()

    print("=" * 98)
    print("  ⚠️ ZUR EINORDNUNG: `schnitt` ist an genau diesem Test")
    print("     gescheitert (Unterschied +0,2238 R, heute nicht mehr")
    print("     nachweisbar). Was oben INSTABIL heisst oder heute nicht")
    print("     mehr traegt, steht LIVE im Betrieb - das waere ein")
    print("     groesseres Thema als der abgelehnte Kandidat.")
    print("  Dauer %.1f Minuten" % ((time.time() - t0) / 60.0))
    return 0


if __name__ == "__main__":
    sys.exit(main())
