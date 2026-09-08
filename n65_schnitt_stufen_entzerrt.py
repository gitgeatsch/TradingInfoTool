# -*- coding: utf-8 -*-
"""N-65 — `schnitt`s STUFEN, entzerrt. Und die Frage dahinter (07.09.2026)

## ⚠️⚠️ Warum N-64 nicht ausgereicht hat — die eigene Kontrolle hat es gefangen

N-64 hat die Stufen auf der selektierten Menge gerechnet. Die
Zufallskontrolle (Raenge gemischt) haette null liefern muessen. Sie lieferte:

    Fuenftel 0   +0,1481      Fuenftel 3   +0,1577
    Fuenftel 1   +0,1036      Fuenftel 4   +0,1402
    Fuenftel 2   +0,1290

**Alle fuenf deutlich positiv - in einer Welt ohne jede Information.** Das
ist keine Wirkung, das ist die Statistik selbst:

> `median(Fuenftel) - median(alle)` ist bei kleinen Gruppen nach oben
> verzerrt. Der Stichprobenmedian einer schiefen Verteilung liegt bei n=1
> oder n=2 systematisch ueber dem Median der Gesamtmenge.

⚠️ **Und die Verzerrung ist so gross wie die gesuchten Effekte.** Wer die
rohen Zahlen als Stufen eintraegt, traegt zur Haelfte Rechenartefakt ein.

## Was diese Datei anders macht

    1  ENTZERRT     jede Stufe minus ihrem eigenen Nullwert. Dafuer sind
                    Nullverteilungen da - nicht nur zum Danebenstellen.
                    20 Ziehungen statt 5, damit der Abzug stabil ist.
    2  MONOTONIE    auf den ENTZERRTEN Werten geprueft, nicht auf den rohen
    3  REDUNDANZ    die Frage, die N-64s Besetzung aufgeworfen hat

## ⚠️⚠️ Die Frage, die wichtiger ist als die Stufen

N-64 hat gezaehlt, wieviele Anker je Tag in welchem Fuenftel liegen:

    Fuenftel 0 (tief unter dem Schnitt)    1,49 Anker/Tag
    Fuenftel 4 (ueber dem Schnitt)        29,35 Anker/Tag

**Die Auswahl der Kette waehlt nach 250-Tage-Momentum - und ein Wert mit
hohem Momentum liegt fast zwangslaeufig ueber seinem eigenen
200-Tage-Schnitt.** Beide messen dieselbe Aufwaertsbewegung, nur ueber
verschieden lange Fenster.

> Wenn das stimmt, ist `schnitt` an Stufe 12 **weitgehend redundant zur
> Auswahl an Stufe 5** - er wuerde dort etwas bewerten, das die Kette
> schon entschieden hat.

⚠️ Das ist eine ANDERE Frage als "traegt er". N-59 hat auf der
selektierten Menge +0,1759 R gemessen, und das steht. Hier geht es darum,
ob der Beitrag an DIESER Stelle der Kette noch etwas beitraegt.

Gemessen wird die Korrelation der beiden Raenge je Kalendertag -
Spearman, weil beide als Raenge in die Kette gehen.

    python n65_schnitt_stufen_entzerrt.py
"""
from __future__ import annotations

import sys
import time

import numpy as np

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import messe_beitrag_auf_auswahl as A                        # noqa: E402
import messe_eigenschaft_beitrag as B                        # noqa: E402
import messe_kandidaten_als_regel as K                       # noqa: E402
import messe_regel_wirksamkeit as RW                         # noqa: E402
from messe_beitrag_auf_auswahl import momentum250            # noqa: E402
from messnorm import _block                                   # noqa: E402
from messnorm_auswahl import MENGEN                           # noqa: E402
from n64_schnitt_stufen import PUNKT_JE_R, band, je_fuenftel  # noqa: E402

HORIZONT, MENGE = 20, "20%"
ZIEH, SAAT = 20, 20260907


def main() -> int:
    t0 = time.time()
    print("=" * 96)
    print("N-65 — `schnitt`s Stufen ENTZERRT, und die Redundanzfrage")
    print("=" * 96)
    reihen = B.lade()
    mom = momentum250(reihen)
    je_tag = K.baue(reihen, "schnitt", horizont=HORIZONT)
    anteil = MENGEN[MENGE]
    block = _block(HORIZONT)
    print("  %d Reihen . %d Kalendertage . Block %d . %d Nullziehungen"
          % (len(reihen), len(je_tag), block, ZIEH))

    # ---- 1  ECHT und NULL, je Fuenftel ---------------------------------
    aus, besetzt, _g = je_fuenftel(je_tag, mom, anteil)
    echt = []
    for k in range(5):
        e = band(aus[k], block)
        echt.append(e[0] if e else None)

    null = {k: [] for k in range(5)}
    for z in range(ZIEH):
        a2, _b, _c = je_fuenftel(je_tag, mom, anteil,
                                 mische=np.random.default_rng(SAAT + z))
        for k in range(5):
            e = band(a2[k], block, zieh=300, saat=SAAT + z)
            if e:
                null[k].append(e[0])

    print()
    print("  1  DIE ENTZERRUNG — jede Stufe minus ihrem eigenen Nullwert")
    print("     %-9s %10s %10s %11s %10s %9s"
          % ("Fuenftel", "roh R", "Null R", "entzerrt R", "Punkte",
             "Anker/Tag"))
    entzerrt = []
    for k in range(5):
        if echt[k] is None or not null[k]:
            print("     %-9d  nicht messbar" % k)
            entzerrt.append(None)
            continue
        n = float(np.mean(null[k]))
        d = echt[k] - n
        entzerrt.append(d)
        print("     %-9d %+10.4f %+10.4f %+11.4f %+10.2f %9.2f"
              % (k, echt[k], n, d, d * PUNKT_JE_R,
                 float(np.mean(besetzt[k]))))
    print("     ⚠️ Der Nullwert ist reine Konstruktion - gemischte Raenge")
    print("        tragen keine Information. Was uebrig bleibt, ist Wirkung.")

    # ---- 2  MONOTONIE auf den entzerrten Werten ------------------------
    print()
    print("  2  MONOTONIE — auf den ENTZERRTEN Werten")
    if any(x is None for x in entzerrt):
        print("     ⚠️ nicht alle Stufen messbar")
        fallend = steigend = False
    else:
        p = [x * PUNKT_JE_R for x in entzerrt]
        fallend = all(p[i] >= p[i + 1] - 1e-9 for i in range(4))
        steigend = all(p[i] <= p[i + 1] + 1e-9 for i in range(4))
        print("     Stufen (Punkte): %s" % " / ".join("%+.2f" % x for x in p))
        print("     %s"
              % ("✔ MONOTON FALLEND - tief unter dem Schnitt ist am besten"
                 if fallend else
                 "⚠️⚠️ MONOTON STEIGEND - Richtung umgekehrt" if steigend else
                 "⚠️⚠️ NICHT MONOTON - ein BUCKEL"))
        if not (fallend or steigend):
            hoch = int(np.argmax(p))
            print("        Der Hochpunkt liegt bei Fuenftel %d, nicht bei 0."
                  % hoch)
            print("        ⚠️ Dieselbe Form wie am 31.08. (+1,27 +1,59 +0,24")
            print("           -1,28 -1,82) und wie der Buckel vom 27.08.")
            print("           Die Vorabfestlegung verlangt Monotonie fuer")
            print("           nutzbar - sie stand VOR dieser Messung fest.")

    # ---- 3  REDUNDANZ zur Auswahl --------------------------------------
    print()
    print("  3  ⚠️⚠️ REDUNDANZ — misst `schnitt` dasselbe wie die AUSWAHL?")
    rhos, anteile = [], []
    for tag, zeilen in je_tag.items():
        if len(zeilen) < 12:
            continue
        mt = mom.get(tag) or {}
        paare = [(x["kennzahl"], mt.get(x["sym"])) for x in zeilen]
        paare = [(a, b) for a, b in paare if b is not None]
        if len(paare) < 12:
            continue
        s = RW.rang(np.array([a for a, _ in paare], float))
        m = RW.rang(np.array([b for _, b in paare], float))
        if s.std() > 0 and m.std() > 0:
            rhos.append(float(np.corrcoef(s, m)[0, 1]))
        # Anteil der Gewaehlten, die UEBER ihrem Schnitt liegen
        maske = A._auswahl_maske(zeilen, mt, anteil, None)
        if maske is not None and maske.any():
            kz = np.array([x["kennzahl"] for x in zeilen], float)
            anteile.append(float((kz[maske] > 0).mean()))
    r = float(np.mean(rhos)) if rhos else float("nan")
    print("     Spearman(schnitt-Rang, momentum250-Rang) je Tag:")
    print("       im Mittel %+.3f  (5.-95. Perzentil %+.3f .. %+.3f, %d Tage)"
          % (r, float(np.percentile(rhos, 5)), float(np.percentile(rhos, 95)),
             len(rhos)))
    print("     Anteil der GEWAEHLTEN, die ueber ihrem 200-Schnitt liegen:")
    print("       im Mittel %.1f %%  (im vollen Querschnitt zum Vergleich:"
          % (100 * float(np.mean(anteile))))
    voll = []
    for tag, zeilen in je_tag.items():
        kz = np.array([x["kennzahl"] for x in zeilen], float)
        if len(kz) >= 12:
            voll.append(float((kz > 0).mean()))
    print("       %.1f %%)" % (100 * float(np.mean(voll))))

    # ---- Urteil ---------------------------------------------------------
    print()
    print("=" * 96)
    print("WAS DAS HEISST")
    print("=" * 96)
    if r > 0.5:
        print("  ⚠️⚠️ `schnitt` und die AUSWAHL messen weitgehend dasselbe")
        print("     (Spearman %+.3f). Beide beschreiben dieselbe" % r)
        print("     Aufwaertsbewegung, nur ueber verschieden lange Fenster.")
        print("     An Stufe 12 bewertet er dann, was Stufe 5 schon")
        print("     entschieden hat.")
    elif r > 0.25:
        print("  ⚠️ TEILWEISE redundant zur Auswahl (Spearman %+.3f) -" % r)
        print("     nicht dasselbe, aber auch nicht unabhaengig.")
    else:
        print("  ✔ `schnitt` ist von der Auswahl weitgehend UNABHAENGIG")
        print("     (Spearman %+.3f) - er traegt eigene Information." % r)
    print()
    if not (fallend or steigend):
        print("  ⚠️⚠️ UND DIE STUFEN SIND NICHT MONOTON. Damit ist die")
        print("     Vorabbedingung fuer 'nutzbar' NICHT erfuellt - zum")
        print("     zweiten Mal bei derselben Groesse.")
    print("  Dauer %.1f Minuten" % ((time.time() - t0) / 60.0))
    return 0


if __name__ == "__main__":
    sys.exit(main())
