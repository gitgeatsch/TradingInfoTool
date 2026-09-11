# -*- coding: utf-8 -*-
"""V11 — `schnitt50` gegen Kriterium 1 und N-73 (11.09.2026)

## Warum V11 laeuft

`schnitt` ist am 10.09. an Kriterium 2 gefallen (2.325). `schnitt50` ist
der benannte Ersatzweg (2.326): er ist auf allen drei Mengen stabil,
unabhaengig (V9) und besteht Regel 3 mit 6,9 % (V1). Offen sind
Kriterium 1 und N-73.

## ⚠️⚠️⚠️ ABER DER BESTAND WIDERSPRICHT SICH UEBER IHN

Vor dem Lauf nachgeschlagen (Faktenregister-Pflicht) - vier Eintraege,
drei Aussagen:

    2.164            urteilt ueber alle Mengen GLEICH
    2.187-was-haelt  bleibt ABGELEHNT, auf ALLEN Mengen
    2.219            WIDERSPRICHT SICH ueber die Mengen
    2.308-vorfrage   traegt auf 20 % mit +0,0698

⚠️ **2.187 und 2.219 haben dieselbe Basis** (Messbasis 08.09., 536
Reihen) und sagen das Gegenteil. Das ist der eigentliche Grund fuer
diesen Lauf - staerker als der aus 2.326.

## ⚠️⚠️ UND DIE VIER KRITERIEN ENTHALTEN ,TRAEGT' GAR NICHT

    1  ABDECKUNG    fuer wie viele Symbole liegt die Groesse vor?
    2  STABILITAET  haelt die Ordnung ueber die Bloecke?
    3  UNABHAENGIG  traegt sie noch, wenn `funding` festgehalten wird?
    4  REGEL 3      trennt sie auch LAENGS, im eigenen Symbol?

Kriterium 1 ist **Verfuegbarkeit**, nicht Wirkung. Ein Kandidat braucht
die WIRKUNG zusaetzlich - und genau die ist bei `schnitt50` strittig.
Deshalb steht sie hier als VORFRAGE vorn.

## Was gemessen wird

    A  ⚠️ VORFRAGE   traegt `schnitt50`? Ueber ALLE zulaessigen Mengen
                     (N-73), unter dem heutigen Standard. Loest 2.187
                     gegen 2.219 auf
    B  KRITERIUM 1   Abdeckung - Reproduktion der ,100 %' aus 2.305
    C  ⚠️⚠️ DIE EHRLICHE GEGENFRAGE
                     Ist seine STABILITAET nur die Stabilitaet von
                     NICHTS? Ein Kandidat ohne Wirkung ist trivial
                     stabil - `zufall` ist es auch (bis 0,02 bis 0,05).
                     Wirkung und Haelftenunterschied stehen deshalb
                     NEBENEINANDER

⚠️ **Nicht in diesem Lauf: die MONOTONIE.** Meine Zeile ,nach 2.222 die
einzige monotone Form' (2.326, 2.305) ist FALSCH ZITIERT - 2.222 handelt
von `schnitt`s Auswahl-Artefakt. Die Behauptung stammt aus
`Anforderungen_Umbau_28_08.md` (O4/N2), gilt dort nur LAENGS, ist
vor-standardlich und ihr eigener Nachtest N2 ist offen. Die Monotonie
gehoert zu Schritt FORM und wird dort gemessen, nicht hier nebenbei.

## Die Vorhersage, VOR dem Lauf (Methodik 2.80)

    A  ⚠️ offen - das ist die Frage. 2.308 laesst 20 % erwarten;
       ob 10 % und 50 % mitgehen, entscheidet N-73
    B  100 % (536 von 536) - er kommt aus der eigenen Kursreihe
    C  ⚠️ ich erwarte, dass seine Wirkung KLEINER ist als `schnitt`s
       (+0,0698 gegen +0,1858 auf 20 %) - dann ist die Stabilitaet
       zwar echt, aber sie hat auch weniger zu halten
    Kontrolle  `zufall` darf auf KEINER Menge tragen

    python n111_v11_schnitt50.py
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
from n68_zeitstabilitaet import (entzerrte_reihe,             # noqa: E402
                                 stabilitaetsurteil)
from n102_vierfachtest import abdeckung                       # noqa: E402

# ⚠️ `schnitt` und `funding` laufen als MASSSTAB mit, `zufall` als
# Kontrolle. `schnitt` ist gestern an Kriterium 2 gefallen - seine
# Wirkung hier ist der Vergleichswert fuer Teil C.
KAND = ("schnitt50", "schnitt", "funding", "zufall")
SAAT = 20260911


def main() -> int:
    t0 = time.time()
    reihen = B.lade()
    mom = momentum250(reihen)
    zus = zusatzquellen()
    lage = N.Lage(instrument="spot", strategie="einstieg")
    block = N._block(HORIZONT)

    print("=" * 118)
    print("V11 — `schnitt50` gegen Kriterium 1 und N-73")
    print("=" * 118)
    print("  %s" % messmenge.zeile())
    print("  %s" % N.standardzeile())
    print("  ⚠️ 2.187 (,abgelehnt auf ALLEN Mengen') und 2.219 "
          "(,widerspricht sich') haben")
    print("     DIESELBE Basis und sagen das Gegenteil. Dieser Lauf "
          "loest das auf.")

    tafel = {}
    for k in KAND:
        je = K.baue(reihen, k, zus.get(k), horizont=HORIZONT)
        syms, anker = abdeckung(je)
        zul = MA.zulaessige_mengen(je, mom, horizont=HORIZONT)
        print()
        print("  %-10s  Abdeckung %d Symbole · %.1f Anker/Tag · "
              "zulaessig: %s"
              % (k.upper(), syms, anker, ", ".join(zul) or "KEINE"))
        print("     %-6s %9s %22s %9s %6s %9s  %s"
              % ("Menge", "Wirkung", "Band", "Nullpkt", "Bloe.",
                 "Trennsch", "Urteil"))
        zeilen = []
        for m in zul:
            try:
                b = MA.pruefe_auswahl(
                    k, je, mom, lage=lage, menge=m,
                    rng=np.random.default_rng(SAAT), horizont=HORIZONT,
                    hypothese="V11 - schnitt50 gegen Kriterium 1 und N-73",
                    verwendung=("Markt" if m == "frei" else "Beitrag"))
            except Exception as exc:                          # noqa: BLE001
                print("     %-6s nicht messbar: %s" % (m, str(exc)[:52]))
                continue
            ts = ("%.2f R" % b.trennschaerfe_in_r
                  if b.trennschaerfe_in_r else "KEINE")
            print("     %-6s %+9.4f [%+.4f .. %+.4f] %+9.4f %6d %9s  %s"
                  % (m, b.wirkung, b.unten, b.oben, b.nullpunkt,
                     b.n_bloecke, ts, b.urteil.split(" (")[0][:34]),
                  flush=True)
            if m == "frei":
                continue                      # Marktfrage, kein Beitrag
            kb = b.urteil.upper().startswith("KEIN BEFUND")
            zeilen.append({"menge": m, "wirkung": b.wirkung,
                           "traegt": bool(b.traegt and not kb)})
        if zeilen:
            tr = sum(1 for z in zeilen if z["traegt"])
            print("     -> N-73: traegt auf %d von %d Beitragsmengen%s"
                  % (tr, len(zeilen),
                     "  ✔ robust" if tr == len(zeilen) else
                     "  ⚠️ NICHT robust"))
        tafel[k] = {"syms": syms, "anker": anker, "zeilen": zeilen}

    # ---- C  DIE EHRLICHE GEGENFRAGE --------------------------------------
    print()
    print("=" * 118)
    print("C  ⚠️⚠️ DIE EHRLICHE GEGENFRAGE — ist die Stabilitaet nur die "
          "Stabilitaet von NICHTS?")
    print("=" * 118)
    print("  Ein Kandidat ohne Wirkung ist TRIVIAL stabil. `zufall` ist "
          "es auch. Deshalb stehen")
    print("  Wirkung und Haelftenunterschied hier NEBENEINANDER - ein ✔ "
          "bei Kriterium 2 ist nur")
    print("  so viel wert wie die Wirkung, die es zu halten hat.")
    print()
    print("  %-10s %-6s %10s %11s %10s  %s"
          % ("Kandidat", "Menge", "Wirkung", "Haelften", "Verhaelt.",
             "Stabilitaetsurteil"))
    for k in KAND:
        je = K.baue(reihen, k, zus.get(k), horizont=HORIZONT)
        for z in tafel[k]["zeilen"]:
            e = entzerrte_reihe(je, mom, MA.MENGEN[z["menge"]])
            r = stabilitaetsurteil(e, block)
            if r is None:
                continue
            w = z["wirkung"]
            q = abs(r["diff"]) / abs(w) if w else float("nan")
            print("  %-10s %-6s %+10.4f %+11.4f %10.2f  %s"
                  % (k, z["menge"], w, r["diff"], q,
                     r["urteil"][:40]), flush=True)

    # ---- Die Abnahme -----------------------------------------------------
    print()
    print("=" * 118)
    print("DIE ABNAHME")
    print("=" * 118)
    print("  %-10s %11s %-18s  %s"
          % ("Kandidat", "Abdeckung", "N-73", "Kriterium 1"))
    for k in KAND:
        t = tafel[k]
        z = t["zeilen"]
        tr = sum(1 for x in z if x["traegt"])
        n73 = ("%d von %d %s" % (tr, len(z),
                                 "✔" if z and tr == len(z) else "⚠️")
               if z else "keine Menge")
        print("  %-10s %6d (%3.0f %%) %-18s  %s"
              % (k, t["syms"], 100.0 * t["syms"] / 536, n73,
                 "✔ volle Abdeckung" if t["syms"] >= 536 else
                 "⚠️ %d von 536" % t["syms"]))
    zf = tafel.get("zufall", {}).get("zeilen") or []
    print()
    if any(x["traegt"] for x in zf):
        print("  ⚠️⚠️⚠️ `zufall` traegt auf einer Menge - der Lauf gilt "
              "NICHT.")
    else:
        print("  ✔ `zufall` traegt auf keiner Beitragsmenge - die "
              "Kontrolle haelt.")
    print()
    print("  ⚠️ ZU LESEN:")
    print("     A  traegt `schnitt50` auf ALLEN zulaessigen Mengen? Nur "
          "dann ist N-73 bestanden")
    print("     B  Abdeckung 536 = 100 %  -> Kriterium 1 erfuellt")
    print("     C  ⚠️ ist seine Wirkung deutlich kleiner als `schnitt`s, "
          "dann ist sein ✔ bei")
    print("        Kriterium 2 echt, aber es haelt WENIGER - das gehoert "
          "in die Entscheidung")
    print("  Dauer %.1f Minuten" % ((time.time() - t0) / 60.0))
    return 0


if __name__ == "__main__":
    sys.exit(main())
