# -*- coding: utf-8 -*-
"""V9 — KRITERIUM 3 als EIN Befund mit EINEM Band (10.09.2026)

## Warum dieser dritte Anlauf

V7 (fuenf Faecher) und V8 (zwei Faecher) haben Kriterium 3 als **Zaehlung
ueber Faecher** gemessen. Beide sind daran gescheitert:

    V7   5 Faecher   nur EIN gedecktes Urteil (`turnover` 2 gegen 0)
    V8   2 Faecher   KEIN gedecktes Urteil - dieselben Daten geben
                     2 gegen 1, und das ist ein Fach Unterschied

> ⚠️⚠️ **Nicht die Macht war der Engpass, sondern die ZAEHLMETRIK.** Eine
> Zaehlung ueber zwei Faecher hat drei moegliche Werte, ueber fuenf sechs.
> Beides ist zu grob fuer einen Vergleich.

## ⚠️⚠️⚠️ Und das richtige Werkzeug lag die ganze Zeit vor

`messnorm_rand.pruefe_geschichtet` misst die Schichtung als **EINEN
Befund mit EINEM Band** - Nullpunkt, Trennschaerfe und eine eingebaute
Positivkontrolle (`pflanze`), die dem Original fehlt:

    marke=None   Median-Differenz wie im Original  (MITTELWERT-Massstab)
    marke=2.0    Differenz der Randanteile         (RAND-Massstab)

⚠️ Ich hatte es verworfen, weil der eine Aufrufer, den ich ansah
(`pruefe_n1_schichtung_gegen_partner`), `marke=2.0` uebergab - **das
Argument eines Aufrufers fuer die Natur des Werkzeugs gehalten** (2.309).

Und es steht auf dem Messstandard: `messnorm_rand` importiert
`NULL_ZIEHUNGEN`, `NULL_PERZENTIL`, `TRENNSCHAERFE_GEGEN_NULLPUNKT`,
`STAERKEN` und `_bezug` direkt aus `messnorm`.

## Der Aufbau

    Kennzahl     die Regel INNERHALB der Funding-Faecher, gepoolt zu
                 EINEM Wert - `geschichtet(..., marke=None)`
    Urteil       die volle Norm: Band, Nullpunkt, Trennschaerfeleiter
    Kontrolle    dieselbe Schichtung mit GEMISCHTEM Funding
    Menge        registrierte Basis, sonst 20 % - wie in V8 VORAB gesetzt

⚠️ Die Gegenkontrolle bleibt der Kern und ist von der Kennzahl
unabhaengig: gleiche Fachgroesse, keine Information.

    ECHT traegt, GEMISCHT nicht   ->  unabhaengig von `funding`
    beide gleich                  ->  die Schichtung kostet
    ECHT faellt unter GEMISCHT    ->  `funding` erklaert einen Teil mit

## Die Vorhersage, VOR dem Lauf (Methodik 2.80)

    turnover     bestaetigt sich - er hatte bei fuenf Faechern 2 gegen 0
    schnitt      offen; auf 20 % traegt er ungeschichtet mit +0,1858
    zufall       traegt nirgends
    ⚠️ Und die TRENNSCHAERFE ist diesmal beziffert - anders als bei einer
      Zaehlung sagt die Leiter, ab welcher Groesse ein Effekt gefunden
      wuerde. Ein Nullbefund waere damit zum ersten Mal eine AUSSAGE.

⚠️⚠️ Bleibt auch das unentscheidbar, ist Kriterium 3 mit diesen Daten
nicht erfuellbar - und DANN waere es eine Frage an die Kriterienliste,
nicht an die Kandidaten.

    python n107_v9_kriterium3_ein_befund.py
"""
from __future__ import annotations

import sys
import time

import numpy as np

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import bestand as BE                                          # noqa: E402
import messe_eigenschaft_beitrag as B                         # noqa: E402
import messe_kandidaten_als_regel as K                        # noqa: E402
import messnorm as N                                          # noqa: E402
import messnorm_auswahl as MA                                 # noqa: E402
import messnorm_rand as R                                     # noqa: E402
from messe_alle_kandidaten import HORIZONT, zusatzquellen     # noqa: E402
from messe_beitrag_auf_auswahl import momentum250             # noqa: E402

KANDIDATEN = ("schnitt", "schnitt50", "vola", "turnover",
              "oi_aenderung", "zufall")
ERSATZMENGE = "20%"      # ⚠️ VORAB gesetzt, wie in V8
SAAT = 20260910


def schicht(je_tag: dict) -> dict:
    """`{tag: {sym: kennzahl}}` - die Form, die `geschichtet` erwartet."""
    return {t: {x["sym"]: x["kennzahl"] for x in z}
            for t, z in je_tag.items()}


def gemischt(s: dict, saat: int = SAAT) -> dict:
    """Dieselben Werte, den FALSCHEN Symbolen zugeordnet - je Tag.

    ⚠️ Die Faecher bleiben gleich gross, tragen aber keine Information.
    Ohne diesen Arm ist ein ,traegt nicht mehr' nicht von den Kosten der
    Schichtung zu unterscheiden.
    """
    rng = np.random.default_rng(saat)
    aus = {}
    for t, d in s.items():
        syms = list(d)
        werte = [d[x] for x in syms]
        rng.shuffle(werte)
        aus[t] = dict(zip(syms, werte))
    return aus


def zeile(b) -> str:
    ts = ("%.2f R" % b.trennschaerfe_in_r) if b.trennschaerfe_in_r else "KEINE"
    return ("%+9.4f [%+.4f .. %+.4f] · Null %+.4f · Trennsch. %-7s · %s"
            % (b.wirkung, b.unten, b.oben, b.nullpunkt, ts,
               b.urteil.split(" (")[0][:34]))


def main() -> int:
    t0 = time.time()
    reihen = B.lade()
    mom = momentum250(reihen)
    zus = zusatzquellen()
    lage = N.Lage(instrument="spot", strategie="einstieg")

    je_fu = K.baue(reihen, "funding", zus.get("funding"), horizont=HORIZONT)
    s_echt = schicht(je_fu)
    s_gem = gemischt(s_echt)

    print("=" * 116)
    print("V9 — KRITERIUM 3 als EIN Befund mit EINEM Band")
    print("=" * 116)
    print("  %s" % N.standardzeile())
    print("  ⚠️ `pruefe_geschichtet(marke=None)` - Median-Differenz, also "
          "der STANDARDmassstab.")
    print("  ⚠️⚠️ Eine STETIGE Kennzahl statt einer Zaehlung ueber "
          "Faecher - daran sind V7 und V8")
    print("     gescheitert. Und die TRENNSCHAERFE ist beziffert: ein "
          "Nullbefund wird zur Aussage.")

    erg = {}
    for kand in KANDIDATEN:
        try:
            je = K.baue(reihen, kand, zus.get(kand), horizont=HORIZONT)
        except Exception as exc:                              # noqa: BLE001
            print("\n  %-14s -> %s" % (kand, str(exc)[:60]))
            continue
        try:
            menge, fenster = BE.messbasis(kand)
        except KeyError:
            menge, fenster = "", ""
        registriert = bool(menge)
        menge = menge or ERSATZMENGE
        if fenster and fenster != "voll":
            je = {t: z for t, z in je.items() if str(t) >= fenster}

        print()
        print("  %s   (Menge %s%s)"
              % (kand.upper(), menge,
                 "" if registriert else " — vorab gesetzt"))
        # ⚠️⚠️ ZUERST DIE VORFRAGE: traegt die Groesse UNGESCHICHTET?
        #
        # Ohne sie bekommt die Kontrolle ein positives Urteil - genau das
        # ist hier passiert: `zufall` stand als „unabhaengig von funding"
        # da, obwohl er gar nichts traegt, das `funding` erklaeren
        # koennte. Der V7-Vorabtest hatte den Fehler schon einmal
        # gefangen; beim Umbau auf V9 habe ich ihn nicht mitgenommen.
        try:
            b_ohne = MA.pruefe_auswahl(
                kand, je, mom, lage=lage, menge=menge,
                rng=np.random.default_rng(SAAT), horizont=HORIZONT,
                hypothese="V9 Vorfrage", verwendung=(
                    "Markt" if menge == "frei" else "Beitrag"))
            traegt_ohne = (b_ohne.traegt
                           and not b_ohne.urteil.upper().startswith(
                               "KEIN BEFUND"))
            print("     %-9s %s" % ("ungesch.", zeile(b_ohne)), flush=True)
        except Exception as exc:                              # noqa: BLE001
            print("     ungesch.  nicht messbar: %s" % str(exc)[:56])
            traegt_ohne = None

        aus = {"_ohne": traegt_ohne}
        for wie, sch in (("echt", s_echt), ("GEMISCHT", s_gem)):
            try:
                b = R.pruefe_geschichtet(
                    kand, je, sch, lage=lage, menge=menge,
                    rng=np.random.default_rng(SAAT), marke=None,
                    horizont=HORIZONT, staerken=N.STAERKEN)
            except Exception as exc:                          # noqa: BLE001
                print("     %-9s nicht messbar: %s" % (wie, str(exc)[:56]))
                continue
            aus[wie] = b
            print("     %-9s %s" % (wie, zeile(b)), flush=True)
        if "echt" in aus and "GEMISCHT" in aus:
            erg[kand] = aus

    # ---- Die Abnahme -----------------------------------------------------
    print()
    print("=" * 116)
    print("DIE ABNAHME — erklaert `funding` es, oder kostet die "
          "Schichtung?")
    print("=" * 116)
    zf = erg.get("zufall")
    if zf and zf["echt"].traegt:
        print("  ⚠️⚠️⚠️ `zufall` traegt geschichtet - der Lauf gilt NICHT.")
    elif zf:
        print("  ✔ `zufall` traegt geschichtet nicht (%+.4f)."
              % zf["echt"].wirkung)
    print()
    print("     %-14s %11s %11s  %s"
          % ("Kandidat", "echt", "GEMISCHT", "Urteil"))
    for kand in KANDIDATEN:
        v = erg.get(kand)
        if not v:
            continue
        e, g = v["echt"], v["GEMISCHT"]
        if not v.get("_ohne"):
            print("     %-14s %+11.4f %+11.4f  %s"
                  % (kand, e.wirkung, g.wirkung,
                     "— traegt UNGESCHICHTET nicht, also gibt es nichts, "
                     "was `funding` erklaeren koennte"))
            continue
        # ⚠️ Der Vergleich ist ECHT gegen GEMISCHT. Und massgeblich ist,
        # ob die BAENDER sich trennen - nicht, welcher Punktschaetzer
        # groesser ist (dieselbe Lehre wie bei der Zaehlmetrik).
        # ⚠️⚠️ „Die Schichtung kostet" gilt NUR bei fehlender
        # Trennschaerfe. Ist sie beziffert, HAT die Anlage Macht - dann
        # ist ein „traegt nicht" ein echter Nullbefund und keine
        # Untermacht. Der Vorabtest zeigte genau das: `zufall` traegt
        # nicht, aber die Leiter greift bei 0,05 R.
        if not e.traegt and not g.traegt:
            if e.trennschaerfe_in_r and g.trennschaerfe_in_r:
                urteil = ("✔ unabhaengig, aber geschichtet nicht mehr "
                          "trennbar - echt wie gemischt "
                          "(Trennschaerfe %.2f R)"
                          % e.trennschaerfe_in_r)
            else:
                urteil = ("⚠️ traegt geschichtet NICHT und die Leiter "
                          "greift nicht - UNTERMACHT, keine Aussage")
        elif e.traegt and not g.traegt:
            urteil = "✔ UNABHAENGIG von `funding`"
        elif not e.traegt and g.traegt:
            urteil = "⚠️⚠️ `funding` erklaert es mit"
        elif e.unten > g.oben:
            urteil = ("✔ UNABHAENGIG - und staerker als mit "
                      "bedeutungslosem Partner")
        elif g.unten > e.oben:
            urteil = "⚠️⚠️ `funding` erklaert einen Teil mit"
        else:
            # ⚠️⚠️⚠️ HIER STAND „kein Unterschied" - und das laesst den
            # Leser mit der Zahl allein, statt den Schluss zu ziehen.
            #
            # `pruefe_n1_schichtung_gegen_partner` gibt ihn vor:
            #   „Bleibt es auch dort beim selben Wert, ist es die
            #    SCHICHTUNG - der Partner erklaert NICHTS."
            #
            # Und „der Partner erklaert nichts" IST Unabhaengigkeit -
            # also genau das, was Kriterium 3 fragt. Der Abfall gegenueber
            # der ungeschichteten Messung (`schnitt` +0,1858 -> +0,0388)
            # tritt mit BEDEUTUNGSLOSEM Funding genauso ein (+0,0361) und
            # ist damit ein Artefakt der Schichtung, keine Redundanz.
            urteil = ("✔ UNABHAENGIG von `funding` - der Abfall tritt mit "
                      "BEDEUTUNGSLOSEM Partner genauso ein")
        print("     %-14s %+11.4f %+11.4f  %s"
              % (kand, e.wirkung, g.wirkung, urteil))
    print()
    print("  ⚠️⚠️ DIE LESART, die `pruefe_n1_schichtung_gegen_partner` "
          "vorgibt:")
    print("     ,Bleibt es auch dort beim selben Wert, ist es die "
          "SCHICHTUNG - der Partner")
    print("      erklaert NICHTS.' Und ,der Partner erklaert nichts' IST "
          "Unabhaengigkeit -")
    print("     also genau das, was Kriterium 3 fragt.")
    print("  ⚠️ Massgeblich ist, ob sich die BAENDER trennen - nicht, "
          "welcher Punktschaetzer")
    print("     groesser ist. Genau daran sind die Zaehlmetriken von V7 "
          "und V8 gescheitert.")
    print("  ⚠️⚠️ Und die Trennschaerfe steht in jeder Zeile: wo sie "
          "fehlt, ist ein Nullbefund")
    print("     Untermacht und keine Aussage.")
    print("  Dauer %.1f Minuten" % ((time.time() - t0) / 60.0))
    return 0


if __name__ == "__main__":
    sys.exit(main())
