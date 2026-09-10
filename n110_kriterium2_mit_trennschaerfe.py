# -*- coding: utf-8 -*-
"""KRITERIUM 2 NACHGEMESSEN — Stabilitaet mit Trennschaerfe (10.09.2026)

## ⚠️⚠️⚠️ Der Fund, der diese Messung ausloest

Aus der S-7-Gegenpruefung. `n102_vierfachtest.py:135` entscheidet
Kriterium 2 so:

    "stabil": bool(d["unten"] <= 0.0 <= d["oben"])

> **,Stabil' heisst dort nur: das Band schliesst die Null ein.**

Das ist ein NICHT-Verwerfen, als Haken ausgegeben. Und es hat eine
Richtung, die genau den falschen Kandidaten belohnt:

    Je BREITER das Band, desto sicherer das ✔.

`schnitt`s Baender sind rund **sechsmal breiter** als `funding`s (G2:
Signal je Bandbreite 0,36 gegen 0,61). Er besteht Kriterium 2 also
nicht, weil er stabil ist, sondern **weil er unruhig ist.**

## ⚠️⚠️ Und der zweite Fund: N-73 wurde bei Kriterium 2 nie angewandt

Im selben `main()`, zehn Zeilen auseinander:

    Kriterium 1   Schleife ueber ALLE zulaessigen Mengen -> "N-73 robust"
    Kriterium 2   stabilitaet(je, mom, menge, block)  <- EINE Menge

Und aus dem Bestand ist bekannt, dass genau das kippt:

> *„sein Haelftenunterschied **dreht mit der Menge** (+0,2238 bei 20 %,
> −0,0647 bei 10 %) - bei `funding` und `zufall` nicht."*
> — `project_zeitstabilitaet_geklaert.md`, Nachtrag 07.09.

## Was hier gemessen wird

    ueber ALLE zulaessigen Mengen                      (N-73)
    MIT Trennschaerfe, auf die ZENTRIERTE Reihe gepflanzt
    und mit denselben VIER Urteilen wie jede andere Frage:

      NICHT STABIL      Band schliesst die Null aus - ein Unterschied
                        ist NACHGEWIESEN
      STABIL BIS X      |diff| unter der gefundenen Trennschaerfe ->
                        Unterschiede ab X sind ausgeschlossen. AUSSAGE.
      NICHT TRENNBAR    |diff| ueber X, Band schliesst Null ein -
                        KEINE Aussage
      KEIN BEFUND       selbst der groesste Versatz wurde nicht gefunden

## ⚠️⚠️ DIE LEITER HIER IST NICHT DIE LEITER AUS `messnorm`

Vom Vorabtest gefunden. Zwei verschiedene Skalen:

    messnorm     pflanzt gegen den NULLPUNKT, mit der Daempfung aus
                 GRENZE = 0,80 - gepflanzte 0,10 R erscheinen als rund
                 0,02 gemessen
    hier         pflanzt den Versatz DIREKT auf die entzerrte Reihe,
                 also 1:1

> **Ein ,bis 0,20' in dieser Tafel ist NICHT mit einem ,0,05 R' aus der
> Norm zu vergleichen.** Die Zahl heisst hier: ein Haelften-Versatz
> dieser Groesse waere aus dem Nichts gefunden worden.

⚠️ **`zentriere=True` ist Pflicht** - sonst wird auf einen bereits
vorhandenen Unterschied gepflanzt und die Trennschaerfe misst nur, dass
der echte Effekt gross ist (`n68_zeitstabilitaet.unterschied`, Warnung
im Code, eigener Fehler vom 07.09.).

## Die Vorhersage, VOR dem Lauf (Methodik 2.80)

    schnitt        ⚠️ das ✔ faellt - entweder NICHT STABIL (bei 20 %,
                   wo 07.09. +0,2238 mit Band ueber null stand) oder
                   NICHT TRENNBAR. Ein "STABIL BIS X" erwarte ich nicht
    funding        STABIL BIS X - schmale Baender, kleiner Unterschied
    oi_aenderung   STABIL BIS X - der solideste Beitrag (2.7-07.09.)
    turnover       offen - nur auf 50 % messbar
    zufall         STABIL BIS X  ⚠️ Kontrolle: bekommt er "NICHT STABIL",
                   gilt der Lauf nicht

    python n110_kriterium2_mit_trennschaerfe.py
"""
from __future__ import annotations

import sys
import time

import numpy as np

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import messe_eigenschaft_beitrag as B                         # noqa: E402
import messe_kandidaten_als_regel as K                        # noqa: E402
import messmenge                                              # noqa: E402
import messnorm as N                                          # noqa: E402
import messnorm_auswahl as MA                                 # noqa: E402
from messe_alle_kandidaten import HORIZONT, zusatzquellen     # noqa: E402
from messe_beitrag_auf_auswahl import momentum250             # noqa: E402
from n68_zeitstabilitaet import (entzerrte_reihe,          # noqa: E402
                                 stabilitaetsurteil)

KAND = ("schnitt", "schnitt50", "funding", "oi_aenderung", "turnover",
        "vola", "zufall")


def urteile(e, block, menge):
    """⚠️ Duenne Huelle - das Urteil steht in `n68.stabilitaetsurteil`.

    Vorgabe: ein Test muss die ECHTE Funktion rufen, nie eine Kopie. Die
    erste Fassung hatte die Logik hier stehen; sie ist an die Quelle
    gehoben, damit `n102` und dieses Skript dasselbe rechnen.
    """
    r = stabilitaetsurteil(e, block)
    if r is None:
        return None
    r["menge"] = menge
    return r


def main() -> int:
    t0 = time.time()
    reihen = B.lade()
    mom = momentum250(reihen)
    zus = zusatzquellen()
    block = N._block(HORIZONT)

    print("=" * 114)
    print("KRITERIUM 2 NACHGEMESSEN — Stabilitaet ueber ALLE Mengen, "
          "MIT Trennschaerfe")
    print("=" * 114)
    print("  %s" % messmenge.zeile())
    print("  %s" % N.standardzeile())
    print("  ⚠️ `n102:135` entschied allein ueber ,Band haelt die Null' - "
          "ein breites Band")
    print("     bestand damit sicherer als ein schmales. Hier steht die "
          "Trennschaerfe daneben.")

    tafel = {}
    for k in KAND:
        je = K.baue(reihen, k, zus.get(k), horizont=HORIZONT)
        zul = MA.zulaessige_mengen(je, mom, horizont=HORIZONT)
        print()
        print("  %s   zulaessig: %s" % (k.upper(), ", ".join(zul) or "KEINE"))
        print("     %-6s %9s %22s %9s %5s  %s"
              % ("Menge", "Diff", "Band", "Trennsch", "Bloe.", "Urteil"))
        zeilen = []
        for m in zul:
            if m == "frei":
                continue                      # Marktfrage, kein Beitrag
            e = entzerrte_reihe(je, mom, MA.MENGEN[m])
            r = urteile(e, block, m)
            if r is None:
                print("     %-6s nicht messbar (zu wenige Bloecke)" % m)
                continue
            zeilen.append(r)
            print("     %-6s %+9.4f [%+.4f .. %+.4f] %9s %5s  %s"
                  % (m, r["diff"], r["unten"], r["oben"],
                     ("%.2f" % r["ts"]) if r["ts"] else "KEINE",
                     "%d/%d" % (r["blA"], r["blB"]), r["urteil"]), flush=True)
        tafel[k] = zeilen

    # ---- Die Abnahme -----------------------------------------------------
    print()
    print("=" * 114)
    print("DIE ABNAHME — haelt das Urteil ueber ALLE Mengen? (N-73)")
    print("=" * 114)
    print("  %-13s %-28s %s" % ("Kandidat", "Urteile je Menge", "Kriterium 2"))
    for k in KAND:
        z = tafel.get(k) or []
        if not z:
            print("  %-13s %-28s %s" % (k, "keine messbare Menge",
                                        "KEIN BEFUND"))
            continue
        kurz = []
        for r in z:
            u = r["urteil"]
            kurz.append("NICHT STABIL" if u.startswith("NICHT ST") else
                        "stabil" if u.startswith("STABIL") else
                        "n.trennbar" if u.startswith("NICHT TR") else "k.Bef.")
        nicht = sum(1 for x in kurz if x == "NICHT STABIL")
        stab = sum(1 for x in kurz if x == "stabil")
        if nicht:
            urteil = "✖ FAELLT - auf %d von %d Mengen ist ein Unterschied " \
                     "NACHGEWIESEN" % (nicht, len(kurz))
        elif stab == len(kurz):
            urteil = "✔ STABIL auf allen %d Mengen - eine Aussage" % len(kurz)
        else:
            urteil = "⚠️ KEINE AUSSAGE - %d von %d nur ,nicht trennbar'" \
                     % (len(kurz) - stab, len(kurz))
        print("  %-13s %-28s %s"
              % (k, " · ".join("%s:%s" % (r["menge"], x)
                               for r, x in zip(z, kurz))[:28], urteil))

    zf = [x for x in (tafel.get("zufall") or [])
          if x["urteil"].startswith("NICHT ST")]
    print()
    if zf:
        print("  ⚠️⚠️⚠️ `zufall` bekommt ,NICHT STABIL' - der Lauf gilt NICHT.")
    else:
        print("  ✔ `zufall` bekommt nirgends ,NICHT STABIL' - die Kontrolle "
              "haelt.")
    print()
    print("  ⚠️ ZU LESEN IST DER UNTERSCHIED ZWISCHEN DREI DINGEN:")
    print("     ✔ STABIL BIS X   eine Aussage - Unterschiede ab X sind "
          "ausgeschlossen")
    print("     ⚠️ X ist HIER 1:1 auf die entzerrte Reihe gepflanzt - NICHT "
          "dieselbe Skala")
    print("        wie die ,R'-Leiter der Norm, die gegen den Nullpunkt "
          "pflanzt (GRENZE 0,80).")
    print("     ⚠️ NICHT TRENNBAR  KEINE Aussage - das alte `n102` haette "
          "hier ✔ gesagt")
    print("     ✖ NICHT STABIL    ein Unterschied ist nachgewiesen")
    print("  Dauer %.1f Minuten" % ((time.time() - t0) / 60.0))
    return 0


if __name__ == "__main__":
    sys.exit(main())
