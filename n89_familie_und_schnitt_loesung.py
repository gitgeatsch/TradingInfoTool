# -*- coding: utf-8 -*-
"""N-89 — Die FAMILIE prüfen, und für `schnitt` eine Lösung suchen

## Der Auftrag (Nutzervorgabe 09.09.2026)

> *„ich denke wir haben keine Wahl, einen neuen Kandidaten zu suchen.
> Aber Hebel und Akkumulation bitte nicht gaenzlich verwerfen - wenn
> untermaechtig oder u.U. nicht bewertbar. **Kein Beitrag darf einfach
> fallen, konkrete Begruendung erforderlich und ggf. Loesung suchen.**"*

Deshalb zwei Teile in einem Lauf.

## TEIL A — die Familie

`vier_kandidaten_eine_familie` (05.09.) hat gemessen:

    Gruppe 1   vola · schnitt · schnitt50 · rsi   paarweise 0,25 bis 0,70
    Gruppe 2   amihud                             zu allem unter 0,20
    Gruppe 3   funding                            der bestehende

Aus Gruppe 1 gehoert **EINE** Vertreterin in die Bewertung. `schnitt` ist
an der Zeitstabilitaet gescheitert (N-88). Die Frage ist, ob eine der
uebrigen sie besteht - **an derselben Huerde, ueber ALLE Mengen**.

⚠️ `amihud` laeuft mit, obwohl er als 'traegt nicht' gefuehrt wird: er ist
die EINZIGE Groesse ausserhalb der Familie, und sein Fall stammt aus der
Zeit VOR dem N-19-Fix.

## TEIL B — die Loesung fuer `schnitt`

N-88 zeigt ein Muster, das nach einer Ursache aussieht:

    5 %   -0,431 ⚠️ trennbar     50 %   +0,002   kein Unterschied
    10 %  -0,081                 frei   +0,018   kein Unterschied
    20 %  +0,197 ⚠️ trennbar

**Die Instabilitaet sitzt ausschliesslich auf den SCHMALEN Mengen.** Und
`schnitt` korreliert mit dem Auswahl-Momentum zu **Spearman +0,704**: auf
der Momentumspitze liegen fast alle Werte ueber ihrem eigenen Schnitt,
also bleibt kaum Streuung uebrig.

> **Verdacht: Kollinearitaet mit der Auswahl, nicht Zeitinstabilitaet.**

⚠️ Es erklaert auch K-1b: dort brach `schnitt`s Wirkung auf
Zufallsmengen von +0,186 auf +0,037 ein - derselbe Mechanismus von der
anderen Seite.

**Der Test:** dieselbe Menge*groesse*, aber ZUFAELLIG gewaehlt statt nach
Momentum. Faellt die Instabilitaet weg, ist sie eine Eigenschaft der
AUSWAHL - und `schnitt` waere auf der Kettenmenge (die NICHT
momentum-selektiert ist) brauchbar.

    traegt die Instabilitaet auch zufaellig   -> `schnitt` ist instabil
    faellt sie weg                             -> es war die Auswahl,
                                                  und das ist eine LOESUNG

⚠️ FUENF Zufallsziehungen, nicht eine - eine einzelne waere kein Beleg.

## Die Vorhersage, VOR dem Lauf (Methodik 2.80)

    Teil A   keine Vertreterin besteht die Huerde deutlicher als
             `schnitt` - sie sind eine Familie, und die Familie hat das
             Problem gemeinsam
    Teil B   auf Zufallsmengen verschwindet die Trennbarkeit - die
             Instabilitaet ist Kollinearitaet

⚠️ Bestaetigt sich B, ist `schnitt` NICHT gefallen, sondern **auf der
falschen Menge gemessen worden**.

    python n89_familie_und_schnitt_loesung.py
"""
from __future__ import annotations

import sys
import time

import numpy as np

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import messe_eigenschaft_beitrag as B                        # noqa: E402
import messe_kandidaten_als_regel as K                       # noqa: E402
import messmenge                                              # noqa: E402
from messe_alle_kandidaten import HORIZONT, zusatzquellen    # noqa: E402
from messe_beitrag_auf_auswahl import momentum250            # noqa: E402
from messnorm import _block                                   # noqa: E402
from messnorm_auswahl import MENGEN                           # noqa: E402
from n68_zeitstabilitaet import entzerrte_reihe, unterschied  # noqa: E402

FAMILIE = ("vola", "schnitt50", "rsi", "amihud", "zufall")
MENGEN_A = ("5%", "10%", "20%", "50%", "frei")
SAATEN = (89001, 89002, 89003, 89004, 89005)


def stabil(e, block):
    """(Diff, Band, trennbar) fuer die Haelften einer entzerrten Reihe."""
    tage = sorted(e)
    if len(tage) < 4 * block:
        return None
    mitte = tage[len(tage) // 2]
    d = unterschied(e, {t for t in e if t < mitte},
                    {t for t in e if t >= mitte}, block)
    if d is None:
        return None
    return d, not (d["unten"] <= 0.0 <= d["oben"])


def main() -> int:
    t0 = time.time()
    reihen = B.lade()
    mom = momentum250(reihen)
    zus = zusatzquellen()
    block = _block(HORIZONT)

    print("=" * 104)
    print("N-89 — die FAMILIE, und eine Loesung fuer `schnitt`")
    print("=" * 104)
    print("  %s" % messmenge.zeile())
    print("  ⚠️ Kein Beitrag faellt einfach - Nutzervorgabe 09.09.")
    print()
    print("  TEIL A — besteht eine Vertreterin der Familie die Huerde?")
    print("  %-11s %-6s %10s %24s  %s"
          % ("Kandidat", "Menge", "Diff", "Band", "Urteil"))
    tabelle = {}
    for kand in FAMILIE:
        try:
            je = K.baue(reihen, kand, zus.get(kand), horizont=HORIZONT)
        except Exception as exc:                             # noqa: BLE001
            print("  %-11s -> %s" % (kand, str(exc)[:56]))
            continue
        zeile = []
        for menge in MENGEN_A:
            try:
                e = entzerrte_reihe(je, mom, MENGEN[menge])
            except Exception as exc:                         # noqa: BLE001
                print("  %-11s %-6s -> %s" % (kand, menge, str(exc)[:40]))
                continue
            r = stabil(e, block)
            if r is None:
                print("  %-11s %-6s ⚠️ zu wenige Bloecke" % (kand, menge))
                continue
            d, tr = r
            zeile.append((menge, d["diff"], tr))
            print("  %-11s %-6s %+10.4f [%+.4f .. %+.4f]  %s"
                  % (kand, menge, d["diff"], d["unten"], d["oben"],
                     "⚠️ UNTERSCHIED" if tr else "kein Unterschied"),
                  flush=True)
        tabelle[kand] = zeile
        print()

    # ---- TEIL B --------------------------------------------------------
    print("=" * 104)
    print("  TEIL B — ist `schnitt`s Instabilitaet KOLLINEARITAET?")
    print("=" * 104)
    print("  Dieselbe Mengengroesse, aber ZUFAELLIG gewaehlt statt nach "
          "Momentum.")
    print("  Bekannt (N-88, Momentum): 5 %% -0,431 ⚠️ · 20 %% +0,197 ⚠️")
    print()
    print("  %-11s %-6s %-10s %10s %24s  %s"
          % ("Kandidat", "Menge", "Auswahl", "Diff", "Band", "Urteil"))
    je_s = K.baue(reihen, "schnitt", None, horizont=HORIZONT)
    ergB = {}
    for menge in ("5%", "20%"):
        for name, saat in [("Momentum", None)] + \
                          [("Zufall %d" % (i + 1), s)
                           for i, s in enumerate(SAATEN)]:
            try:
                e = entzerrte_reihe(je_s, mom, MENGEN[menge],
                                    auswahl_saat=saat)
            except Exception as exc:                         # noqa: BLE001
                print("  schnitt     %-6s %-10s -> %s"
                      % (menge, name, str(exc)[:36]))
                continue
            r = stabil(e, block)
            if r is None:
                print("  schnitt     %-6s %-10s ⚠️ zu wenige Bloecke"
                      % (menge, name))
                continue
            d, tr = r
            ergB.setdefault(menge, []).append((name, d["diff"], tr))
            print("  %-11s %-6s %-10s %+10.4f [%+.4f .. %+.4f]  %s"
                  % ("schnitt", menge, name, d["diff"], d["unten"],
                     d["oben"], "⚠️ UNTERSCHIED" if tr else "kein"),
                  flush=True)
        print()

    # ---- Urteil ---------------------------------------------------------
    print("=" * 104)
    print("WAS DAS HEISST")
    print("=" * 104)
    print("  TEIL A — die Familie:")
    for kand in FAMILIE:
        z = tabelle.get(kand) or []
        if not z:
            continue
        tr = [m for m, _d, t in z if t]
        vz = {np.sign(d) for _m, d, _t in z if abs(d) > 1e-9}
        print("     %-11s %d Mengen · %s · %s"
              % (kand, len(z),
                 "Vorzeichen DREHT" if len(vz) > 1 else "Vorzeichen stabil",
                 ("⚠️ trennbar auf %s" % ", ".join(tr)) if tr
                 else "✔ NIRGENDS trennbar"))
    print()
    print("  TEIL B — `schnitt` auf Zufallsmengen:")
    for menge, z in ergB.items():
        mo = next((t for n, _d, t in z if n == "Momentum"), None)
        zu = [(n, d, t) for n, d, t in z if n.startswith("Zufall")]
        n_tr = sum(1 for _n, _d, t in zu if t)
        print("     %-6s Momentum: %s · Zufall: %d von %d trennbar"
              % (menge, "⚠️ trennbar" if mo else "kein Unterschied",
                 n_tr, len(zu)))
        if mo and n_tr == 0:
            print("            ✔✔ DIE INSTABILITAET VERSCHWINDET - sie "
                  "war die AUSWAHL,")
            print("               nicht `schnitt`. Das ist eine LOESUNG, "
                  "kein Nullbefund.")
        elif mo and n_tr >= 3:
            print("            ⚠️ sie bleibt - dann ist sie eine "
                  "Eigenschaft von `schnitt`.")
    print()
    print("  Dauer %.1f Minuten" % ((time.time() - t0) / 60.0))
    return 0


if __name__ == "__main__":
    sys.exit(main())
