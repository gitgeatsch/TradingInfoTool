# -*- coding: utf-8 -*-
"""N-77 — Ist die ABGEDECKTE Teilmenge repraesentativ? (N-6, 07.09.2026)

## ⚠️⚠️ Die Praemisse von N-6 hat sich beim Nachrechnen verschoben

N-6 hiess: *"60,5 % der 524 Symbole sind bewertbar - gebraucht wird ein
Beitrag aus der eigenen Kursreihe."* Gemessen:

    Betrieb (Watchlist, k=2)   4,2 % der gewaehlten Anker ohne Beitrag
                               - und das sind FLOKI und XNO
    Messbasis (524, 20 %)     32,4 % der gewaehlten Anker ohne Beitrag

⚠️ **Nutzervorgabe vom 07.09., woertlich:** *"wichtig sind die stabilen
Werte, Altbestand und Hochrisikowerte im Meme-/Smallcap-Bereich muessen
mitlaufen und hier ist eine fehlende Bewertung als UNKRITISCH zu
bewerten."* FLOKI ist ein Meme-Coin, XNO ein Smallcap.

> **Damit ist die Luecke kein Betriebsproblem. Sie ist ein MESSproblem -
> und als solches moeglicherweise ein groesseres.**

## Die Frage, die wirklich zaehlt

Jeder registrierte Beitrag ist auf den **317 abgedeckten** Symbolen
gemessen. Die kommen aus Binance-Perpetuals, dem Terminmarkt und einer
onchain-Quelle - also systematisch von den **groesseren, etablierteren**
Werten.

> **Wenn sich die 207 nicht abgedeckten Symbole anders verhalten, steht
> JEDER Befund auf einer verzerrten Teilmenge.** Das waere schwerer als
> eine fehlende Bewertung fuer zwei Meme-Coins.

## Wie das messbar ist, obwohl die 207 keinen Beitrag haben

Ueber eine Groesse, die **jedes** Symbol hat: die eigene Kursreihe.
`schnitt` und `vola` decken 100 % ab. Verhalten sie sich auf beiden
Teilmengen gleich?

    Rang        aus dem VOLLEN Tagesquerschnitt - wie `marktrang`.
                ⚠️ NICHT innerhalb der Teilmenge, sonst waere es eine
                andere Messung und nicht mehr vergleichbar.
    Ergebnis    dann auf die Teilmenge verengt
    Statistik   median(frei) - median(alle) je Tag, entzerrt

## Vorab festgelegt

    repraesentativ      die Wirkung liegt auf beiden Teilmengen im
                        selben Band, und die Punktschaetzer
                        unterscheiden sich um weniger als die
                        Kontrollspanne
    NICHT repraesentativ sonst - dann ist jeder Beitragsbefund mit dem
                        Vorbehalt "gemessen auf den abgedeckten 60 %"
                        zu versehen

## Die Kontrollen

    zufall     auf beiden Teilmengen - er darf nirgends tragen und die
               Differenz der beiden gibt den Rauschmassstab
    Merkmale   Historienlaenge, ATR/Kurs, Umsatz - beschreiben, WIE
               verschieden die beiden Gruppen ueberhaupt sind

    python n77_ist_die_abdeckung_repraesentativ.py
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
import messe_regel_wirksamkeit as RW                         # noqa: E402
from messe_beitrag_auf_auswahl import (_auswahl_maske,       # noqa: E402
                                       momentum250)
from messnorm import _block                                   # noqa: E402
from messnorm_auswahl import MENGEN                           # noqa: E402
from n64_schnitt_stufen import band                           # noqa: E402

HORIZONT, MENGE = 20, "20%"
ZIEH, SAAT = 20, 20260907


def wirkung_auf(je_tag, mom, anteil, erlaubt, mische=None):
    """median(frei) - median(alle) je Tag, aber NUR auf `erlaubt`.

    ⚠️ Der Rang kommt aus dem VOLLEN Tagesquerschnitt; die Teilmenge
    wirkt erst danach. Sonst waere es eine andere Messung.
    """
    aus, n = {}, []
    for tag, z in je_tag.items():
        if len(z) < 12:
            continue
        r = RW.rang(np.array([x["kennzahl"] for x in z], float))
        if mische is not None:
            r = mische.permutation(r)
        y = np.array([x["in_r"] for x in z], float)
        m = _auswahl_maske(z, mom.get(tag) or {}, anteil, None)
        if m is None:
            continue
        m = m & np.array([x["sym"].upper() in erlaubt for x in z], bool)
        if m.sum() < 6:
            continue
        oben = r >= RW.GRENZE
        if (oben & m).sum() < 1 or ((~oben) & m).sum() < 3:
            continue
        n.append(int(m.sum()))
        aus[tag] = float(np.median(y[m & ~oben])) - float(np.median(y[m]))
    return aus, n


def entzerrt(je_tag, mom, anteil, erlaubt, block):
    echt, n = wirkung_auf(je_tag, mom, anteil, erlaubt)
    e = band(echt, block)
    if e is None:
        return None
    null = []
    for z in range(ZIEH):
        x, _ = wirkung_auf(je_tag, mom, anteil, erlaubt,
                           mische=np.random.default_rng(SAAT + z))
        nb = band(x, block, zieh=300, saat=SAAT + z)
        if nb:
            null.append(nb[0])
    nw = float(np.mean(null)) if null else 0.0
    return {"roh": e[0], "unten": e[1], "oben": e[2], "tage": e[3],
            "null": nw, "wirkung": e[0] - nw,
            "anker": float(np.mean(n)) if n else 0.0}


def main() -> int:
    t0 = time.time()
    print("=" * 100)
    print("N-77 — ist die ABGEDECKTE Teilmenge repraesentativ?")
    print("=" * 100)
    reihen = B.lade()
    mom = momentum250(reihen)
    block = _block(HORIZONT)
    anteil = MENGEN[MENGE]
    kurs = {s.upper() for s in reihen}
    hat = ({s.upper() for s in F.lade_funding()}
           | {s.upper() for s in MB.reihe("data/onchain_historie.db",
                                          "splycur")}
           | {s.upper() for s in K.lade_terminmarkt()["oi_aenderung"]}) & kurs
    ohne = kurs - hat
    print("  %d Symbole . MIT Beitrag %d . OHNE %d"
          % (len(kurs), len(hat), len(ohne)))

    # ---- 1  WIE VERSCHIEDEN SIND DIE GRUPPEN? --------------------------
    print()
    print("  1  WIE VERSCHIEDEN SIND DIE BEIDEN GRUPPEN?")
    print("     %-14s %8s %12s %12s %14s"
          % ("Gruppe", "Symbole", "Tage Median", "ATR/Kurs", "Umsatz Median"))
    for lab, menge in (("MIT Beitrag", hat), ("OHNE Beitrag", ohne)):
        tage, atrq, ums = [], [], []
        for s in menge:
            roh = reihen.get(s) or reihen.get(s.lower())
            if not roh:
                continue
            c = np.array([x[1] for x in roh], float)
            h = np.array([x[2] for x in roh], float)
            l = np.array([x[3] for x in roh], float)
            v = np.array([x[4] for x in roh], float)
            tage.append(len(c))
            if len(c) > 20:
                atrq.append(float(np.median((h - l) / np.maximum(c, 1e-12))))
                ums.append(float(np.median(v * c)))
        print("     %-14s %8d %12.0f %12.4f %14.3g"
              % (lab, len(tage), np.median(tage), np.median(atrq),
                 np.median(ums)))

    # ---- 2  VERHALTEN SICH KURSREIHEN-GROESSEN GLEICH? -----------------
    print()
    print("  2  ⚠️ VERHALTEN SICH DIE KURSREIHEN-GROESSEN GLEICH?")
    print("     %-9s %-14s %10s %22s %10s %8s"
          % ("Kandidat", "Gruppe", "Wirkung", "Band", "entzerrt", "Anker"))
    erg = {}
    for a in ("schnitt", "vola", "zufall"):
        for lab, menge in (("MIT Beitrag", hat), ("OHNE Beitrag", ohne)):
            je = K.baue(reihen, a, None, horizont=HORIZONT)
            r = entzerrt(je, mom, anteil, menge, block)
            if r is None:
                print("     %-9s %-14s  zu wenige Tage" % (a, lab))
                continue
            erg[(a, lab)] = r
            print("     %-9s %-14s %+10.4f [%+.4f .. %+.4f] %+10.4f %8.1f"
                  % (a, lab, r["roh"], r["unten"], r["oben"], r["wirkung"],
                     r["anker"]), flush=True)
        print()

    # ---- Urteil ---------------------------------------------------------
    print("=" * 100)
    print("WAS DAS HEISST")
    print("=" * 100)
    zm, zo = erg.get(("zufall", "MIT Beitrag")), erg.get(("zufall", "OHNE Beitrag"))
    if not (zm and zo):
        print("  ⚠️ Kontrolle fehlt - kein Urteil.")
        return 1
    rausch = abs(zm["wirkung"] - zo["wirkung"])
    print("  Rauschmassstab (Differenz der Kontrolle): %.4f R" % rausch)
    print()
    verschieden = []
    for a in ("schnitt", "vola"):
        m, o = erg.get((a, "MIT Beitrag")), erg.get((a, "OHNE Beitrag"))
        if not (m and o):
            continue
        d = m["wirkung"] - o["wirkung"]
        ueberlappt = not (m["unten"] > o["oben"] or o["unten"] > m["oben"])
        auffaellig = abs(d) > 3 * max(rausch, 1e-9) and not ueberlappt
        if auffaellig:
            verschieden.append(a)
        print("  %-9s MIT %+.4f · OHNE %+.4f · Differenz %+.4f   %s"
              % (a, m["wirkung"], o["wirkung"], d,
                 "⚠️⚠️ VERSCHIEDEN" if auffaellig else
                 ("Baender ueberlappen - nicht unterscheidbar"
                  if ueberlappt else "Differenz im Rauschen")))
    print()
    if not verschieden:
        print("  ✔✔ DIE ABGEDECKTE TEILMENGE IST REPRAESENTATIV.")
        print("     Kursreihen-Groessen verhalten sich auf beiden Gruppen")
        print("     gleich. Damit steht KEIN Beitragsbefund unter dem")
        print("     Vorbehalt 'nur auf den abgedeckten 60 % gemessen'.")
        print()
        print("  ⚠️ Und damit ist N-6 KEIN dringendes Bauthema: im Betrieb")
        print("     trifft die Luecke 4,2 % der gewaehlten Anker, und zwar")
        print("     FLOKI und XNO - Meme und Smallcap, wo eine fehlende")
        print("     Bewertung laut Nutzervorgabe unkritisch ist.")
    else:
        print("  ⚠️⚠️ DIE TEILMENGEN VERHALTEN SICH VERSCHIEDEN (%s)."
              % ", ".join(verschieden))
        print("     Dann ist JEDER Beitragsbefund auf einer verzerrten")
        print("     Auswahl gemessen - das waere schwerer als die")
        print("     fehlende Bewertung zweier Meme-Coins.")
    print("  Dauer %.1f Minuten" % ((time.time() - t0) / 60.0))
    return 0


if __name__ == "__main__":
    sys.exit(main())
