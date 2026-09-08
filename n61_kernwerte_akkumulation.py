# -*- coding: utf-8 -*-
"""N-61 — WARUM traegt das Akkumulationsmass bei BTC/ETH/SOL nicht? (07.09.2026)

## Die Lage

Methodik 2.154: das Akkumulationsmass haelt auf der neuen Basis (UNTER_SMA
+0,0288 ueber 516 Kryptowerte). **Aber bei den drei Kernwerten dreht es:**

    BTC  -0,0251      ETH  -0,0308      SOL  -0,0291

⚠️ Und `asset_dca_settings` enthaelt genau BTC und ETH - die Akkumulation
laeuft also **auf den Werten, auf denen das Mass nicht traegt.**

## ⚠️ Ein Nullbefund waere hier die falsche Antwort

Alle drei liegen im MINUS, nicht bei null. Das ist kein "wirkt nicht",
sondern ein "wirkt umgekehrt" - falls es echt ist. Zwei Erklaerungen sind
moeglich und sie sind UNTERSCHEIDBAR:

    A  VERFUEGBARKEIT  die tiefen Baender werden nie erreicht. Dann feuert
                       der Schalter nur oben, wo er schwach ist - und das
                       Vorzeichen ist Rauschen um null.
    B  ECHTE UMKEHR    die Kennlinie selbst laeuft bei den Kernwerten
                       anders herum. Dann waere es ein Befund ueber diese
                       Werte, kein Artefakt der Datenlage.

⚠️ **A und B verlangen entgegengesetzte Konsequenzen.** Bei A braucht die
Akkumulation ein anderes Mass; bei B braucht sie das umgekehrte Vorzeichen.
Wer das nicht trennt, baut das Falsche.

## ⚠️⚠️ Die Ziehungszahl steht VOR der Deutung

Drei Symbole sind drei Symbole. Wieviele TAGE und wieviele BLOECKE
dahinterstehen, wird zuerst gezeigt - nicht danach, wenn das Ergebnis
schon auf dem Tisch liegt (stehende Vorgabe, dreimal verletzt).

## Die Kontrolle

`WOCHENTAG` laeuft mit. Er ist die eingebaute Negativkontrolle des Masses
und darf bei den Kernwerten so wenig tragen wie ueberall sonst. Traegt er
hier, ist der Aufbau kaputt und alles Weitere wertlos.

    python n61_kernwerte_akkumulation.py
"""
from __future__ import annotations

import sys

import numpy as np

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# ⚠️ DIE ECHTEN FUNKTIONEN, keine Kopien (stehende Vorgabe).
from messe_akkumulationsmass import (BAENDER, VORLAUF, lade_reihen,  # noqa: E402
                                     messe)

DB, H = "data/messdaten.db", 90
KERN = ("BTC", "ETH", "SOL")


def main() -> int:
    print("=" * 96)
    print("N-61 — warum traegt das Akkumulationsmass bei BTC/ETH/SOL nicht?")
    print("=" * 96)
    # ⚠️ DIESELBE Ladung wie `main()` des Masses - min_tage, Achse und
    # Startindizes kommen von dort, nicht aus eigener Rechnung.
    reihen, start, achse = lade_reihen(DB, VORLAUF + H + 60)
    da = [s for s in KERN if s in reihen]
    fehlt = [s for s in KERN if s not in reihen]
    if fehlt:
        print("  ⚠️⚠️ NICHT IN DER MESSBASIS: %s" % ", ".join(fehlt))
    rest = [s for s in reihen if s not in KERN]

    # ---- 1  DIE ZIEHUNGSZAHL, vor jeder Deutung ------------------------
    print()
    print("  1  WIEVIELE BEOBACHTUNGEN SIND ES WIRKLICH?")
    print("     %-8s %8s %10s %10s" % ("Symbol", "Tage", "Bloecke", "H=90"))
    for s in da:
        n = len(reihen[s])
        print("     %-8s %8d %10d %10s"
              % (s, n, n // (3 * H),
                 "✔" if n // (3 * H) >= 20 else "⚠️ UNTERMAECHTIG"))
    print("     %-8s %8d %10s" % ("(uebrige)", sum(len(reihen[s])
                                                   for s in rest), "-"))
    print("     ⚠️ Block = 3 x H = %d Tage. Unter 20 Bloecken je Reihe ist"
          % (3 * H))
    print("        eine EINZELreihe kein Befund, sondern Untermacht.")

    # ---- 2  BANDBESETZUNG: wird das wirksame Band ueberhaupt erreicht? --
    print()
    print("  2  WO LIEGEN SIE? — Anteil der Tage je Abstandsband")
    print("     %-16s %8s %8s %8s   %8s" % ("Abstand zum SMA", "BTC", "ETH",
                                            "SOL", "uebrige"))

    def besetzung(syms):
        zaehler = np.zeros(len(BAENDER))
        ges = 0
        for s in syms:
            c = np.asarray(reihen[s], dtype=float)
            if len(c) < 200 + H + 1:
                continue
            sma = np.convolve(c, np.ones(200) / 200.0, mode="valid")
            # abst[i] gehoert zu c[199+i]; nur Tage mit vollem H-Fenster
            bis = min(len(sma), len(c) - 199 - H)
            if bis <= 0:
                continue
            abst = c[199:199 + bis] / sma[:bis] - 1.0
            for k, (u, o) in enumerate(BAENDER):
                zaehler[k] += int(((abst >= u) & (abst < o)).sum())
            ges += bis
        return (zaehler / ges if ges else zaehler), ges

    je = {s: besetzung([s]) for s in da}
    ub, ub_n = besetzung(rest)
    for k, (u, o) in enumerate(BAENDER):
        lab = ("unter %+.0f %%" % (100 * o) if u < -9 else
               "ueber %+.0f %%" % (100 * u) if o > 9 else
               "%+.0f .. %+.0f %%" % (100 * u, 100 * o))
        print("     %-16s %7s %7s %7s   %7.1f %%"
              % (lab,
                 *["%.1f %%" % (100 * je[s][0][k]) if s in je else "-"
                   for s in KERN],
                 100 * ub[k]))
    print("     Tage gesamt: %s · uebrige %d"
          % (" · ".join("%s %d" % (s, je[s][1]) for s in da), ub_n))

    # ---- 3  DIE MESSUNG selbst, je Gruppe -------------------------------
    print()
    print("  3  DAS MASS, getrennt gemessen")
    print("     %-24s %10s %8s   %s" % ("Menge", "Rang", "p", "Urteil"))
    for lab, syms in (("BTC+ETH+SOL", da), ("uebrige %d" % len(rest), rest)):
        teil = {s: reihen[s] for s in syms}
        st = {s: start[s] for s in syms}
        for name in ("UNTER_SMA", "WOCHENTAG"):
            rng = np.random.default_rng(20260907)
            try:
                e = messe(teil, st, achse, name, H, rng)
            except Exception as exc:                         # noqa: BLE001
                print("     %-24s %s -> %s" % (lab, name, exc))
                continue
            print("     %-24s %-10s %+8.4f %7.3f   %s"
                  % (lab, name, e["vorsprung"], e["p"],
                     "traegt" if e["p"] < 0.05 else "traegt nicht"),
                  flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
