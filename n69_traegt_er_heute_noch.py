# -*- coding: utf-8 -*-
"""N-69 — TRAEGT `schnitt` HEUTE NOCH? Die Frage nach N-68 (07.09.2026)

## Warum diese Frage die entscheidende ist

N-68 hat die Zeitstabilitaet geklaert, und zwar negativ:

    HAELFTEN   erste +0,2742   zweite +0,0504   Unterschied +0,2238 R
               [+0,0792 .. +0,3988] - das Band schliesst null AUS,
               Trennschaerfe ab 0,02 R (der Test ist dort scharf)

Der Jahresverlauf zeigt, woher das kommt:

    2019 +0,4532   2021 +0,3440   2023 -0,0498   2025 +0,1280
    2020 +0,5100   2022 +0,0187   2024 +0,1603   2026 -0,1158

⚠️ **`funding` zeigt dasselbe Muster** (2020 +0,2876, danach +0,01 bis
+0,03) - schwaecher, aber gleichgerichtet. Das spricht dafuer, dass ein
Teil davon der EPOCHE gehoert und nicht dem Kandidaten: der fruehe
Kryptomarkt war ineffizienter.

> **Fuer die Bauentscheidung zaehlt nicht der Gesamtwert, sondern der
> heutige.** Ein Beitrag, dessen Wirkung 2020 entstand, hilft 2026 nicht.

## Was gemessen wird

    Zeitraeume   ab 2022, ab 2023, ab 2024 - jeweils bis heute
    Statistik    dieselbe entzerrte Tagesreihe wie N-68 (importiert)
    Band         Blockbootstrap, Block 60
    Trennschaerfe   gepflanzter Effekt - OHNE sie ist ein Nullbefund
                    in einem kurzen Zeitraum bedeutungslos

⚠️ **Und beide Statistiken**, weil sie verschiedene Fragen beantworten:

    ALLEIN      `schnitt` auf der selektierten Menge (N-59/N-68)
    IN DER KETTE nach funding + turnover (N-67) - das ist die Zahl, die
                 eine Bauentscheidung traegt

## Die Kontrollen

    funding   traegt heute? Wenn auch er in den kurzen Zeitraeumen
              verschwindet, ist es die MESSDAUER, nicht der Kandidat.
    zufall    darf nirgends tragen.

    python n69_traegt_er_heute_noch.py
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
from n64_schnitt_stufen import PUNKT_JE_R                     # noqa: E402
from n67_schnitt_ueber_die_kette import kette, welten         # noqa: E402
from n68_zeitstabilitaet import ZIEH, SAAT, _bloecke, entzerrte_reihe  # noqa: E402

HORIZONT, MENGE = 20, "20%"
AB = ("2022", "2023", "2024")
GEPFLANZT = (0.02, 0.05, 0.10)
MIN_BLOECKE = 20


def band_ab(e: dict, ab: str, block: int, saat: int = SAAT,
            zieh: int = 2000, versatz: float = 0.0):
    """Mittelwert und Band der entzerrten Reihe ab einem Jahr."""
    t = sorted(x for x in e if x >= ab)
    if len(t) < 2 * block:
        return None
    v = np.array([e[x] for x in t], float) + versatz
    z = _bloecke(v, block, np.random.default_rng(saat), zieh)
    return {"mittel": float(v.mean()), "unten": float(np.percentile(z, 5)),
            "oben": float(np.percentile(z, 95)), "tage": len(t),
            "bloecke": len(t) // block}


def schaerfe_ab(e, ab, block):
    """Ab welchem gepflanzten Effekt wird er gefunden? 5 Ziehungen."""
    for g in GEPFLANZT:
        treffer = 0
        for z in range(5):
            # ⚠️ Gepflanzt wird auf eine ZENTRIERTE Reihe - sonst prueft
            # man, ob der ECHTE Effekt plus g gefunden wird, und das ist
            # eine andere Frage.
            m = float(np.mean([v for t, v in e.items() if t >= ab]))
            leer = {t: v - m for t, v in e.items()}
            b = band_ab(leer, ab, block, saat=SAAT + 100 * z, zieh=400,
                        versatz=g)
            if b and b["unten"] > 0:
                treffer += 1
        if treffer >= 4:
            return g
    return None


def main() -> int:
    t0 = time.time()
    print("=" * 98)
    print("N-69 — traegt `schnitt` HEUTE noch? Zeitraeume ab 2022/2023/2024")
    print("=" * 98)
    reihen = B.lade()
    mom = momentum250(reihen)
    anteil = MENGEN[MENGE]
    block = _block(HORIZONT)
    zus = {"funding": F.lade_funding(),
           "turnover": MB.reihe("data/onchain_historie.db", "splycur")}
    print("  %d Reihen . Menge %s . Block %d . %d Nullziehungen"
          % (len(reihen), MENGE, block, ZIEH))

    # ---- A  ALLEIN, wie N-59/N-68 --------------------------------------
    print()
    print("  A  ALLEIN auf der selektierten Menge")
    print("     %-9s %-7s %9s %22s %7s %8s   %s"
          % ("Kandidat", "ab", "Wirkung", "Band", "Tage", "Bloecke",
             "Urteil"))
    reihenwerte = {}
    for art in ("schnitt", "funding", "zufall"):
        je = K.baue(reihen, art, zus.get(art), horizont=HORIZONT)
        reihenwerte[art] = entzerrte_reihe(je, mom, anteil)
    ergA = {}
    for art in ("schnitt", "funding", "zufall"):
        e = reihenwerte[art]
        for ab in ("2019",) + AB:
            b = band_ab(e, ab, block)
            if b is None:
                print("     %-9s %-7s  zu wenige Tage" % (art, ab))
                continue
            s = (schaerfe_ab(e, ab, block)
                 if art != "zufall" else None)
            ergA[(art, ab)] = (b, s)
            traegt = b["unten"] > 0
            print("     %-9s %-7s %+9.4f [%+.4f .. %+.4f] %7d %8d   %s"
                  % (art, "ganz" if ab == "2019" else "ab " + ab,
                     b["mittel"], b["unten"], b["oben"], b["tage"],
                     b["bloecke"],
                     ("traegt" if traegt else
                      "traegt nicht bis %.2f R" % s if s else
                      "traegt nicht")
                     + ("" if b["bloecke"] >= MIN_BLOECKE
                        else "  ⚠️ %d Bloecke" % b["bloecke"])),
                  flush=True)
        print()

    # ---- B  IN DER KETTE, wie N-67 -------------------------------------
    print("  B  ⚠️⚠️ IN DER KETTE — nach funding + turnover (die Bauzahl)")
    print("     %-9s %-7s %9s %22s %7s %8s   %s"
          % ("Dritter", "ab", "Wirkung", "Band", "Tage", "Bloecke", "Urteil"))
    w = welten(reihen)
    for dritter in ("schnitt", "zufall"):
        echt, _z = kette(w, mom, anteil, dritter)
        summe, zahl = {}, {}
        for i in range(ZIEH):
            n, _ = kette(w, mom, anteil, dritter,
                         mische=np.random.default_rng(SAAT + i))
            for t, v in n.items():
                summe[t] = summe.get(t, 0.0) + v
                zahl[t] = zahl.get(t, 0) + 1
        e = {t: v - (summe[t] / zahl[t] if zahl.get(t) else 0.0)
             for t, v in echt.items()}
        for ab in ("2019",) + AB:
            b = band_ab(e, ab, block)
            if b is None:
                print("     %-9s %-7s  zu wenige Tage" % (dritter, ab))
                continue
            s = schaerfe_ab(e, ab, block) if dritter != "zufall" else None
            print("     %-9s %-7s %+9.4f [%+.4f .. %+.4f] %7d %8d   %s"
                  % (dritter, "ganz" if ab == "2019" else "ab " + ab,
                     b["mittel"], b["unten"], b["oben"], b["tage"],
                     b["bloecke"],
                     ("traegt" if b["unten"] > 0 else
                      "traegt nicht bis %.2f R" % s if s else
                      "traegt nicht")),
                  flush=True)
            if dritter == "schnitt":
                ergA[("kette", ab)] = (b, s)
        print()

    # ---- Urteil ---------------------------------------------------------
    print("=" * 98)
    print("WAS DAS HEISST")
    print("=" * 98)
    zf = [ergA.get(("zufall", ab)) for ab in ("2019",) + AB]
    if any(x and x[0]["unten"] > 0 for x in zf):
        print("  ⚠️⚠️ `zufall` traegt in einem Zeitraum - Aufbau kaputt.")
        return 1
    print("  ✔ `zufall` traegt in keinem Zeitraum.")
    fu = ergA.get(("funding", "2024"))
    if fu:
        print("  Kontrolle `funding` ab 2024: %+.4f R [%+.4f .. %+.4f] - %s"
              % (fu[0]["mittel"], fu[0]["unten"], fu[0]["oben"],
                 "traegt" if fu[0]["unten"] > 0 else "traegt nicht"))
        if fu[0]["unten"] <= 0:
            print("     ⚠️ Traegt auch `funding` in den kurzen Zeitraeumen")
            print("        nicht, liegt es an der MESSDAUER - dann ist ein")
            print("        Nullbefund bei `schnitt` dort keine Aussage.")
    print()
    for lab, schl in (("ALLEIN", "schnitt"), ("IN DER KETTE", "kette")):
        print("  %s:" % lab)
        for ab in AB:
            x = ergA.get((schl, ab))
            if not x:
                continue
            b, s = x
            print("     ab %s  %+.4f R [%+.4f .. %+.4f]  %+.2f Punkte  %s"
                  % (ab, b["mittel"], b["unten"], b["oben"],
                     b["mittel"] * PUNKT_JE_R,
                     "TRAEGT" if b["unten"] > 0 else
                     ("traegt nicht bis %.2f R" % s if s
                      else "traegt nicht - und die Trennschaerfe reicht "
                           "nicht einmal fuer %.2f R" % max(GEPFLANZT))))
        print()
    print("  Dauer %.1f Minuten" % ((time.time() - t0) / 60.0))
    return 0


if __name__ == "__main__":
    sys.exit(main())
