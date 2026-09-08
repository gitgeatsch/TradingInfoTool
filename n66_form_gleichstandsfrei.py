# -*- coding: utf-8 -*-
"""N-66 — Die Formfrage OHNE Gleichstandsfalle, und die echte Redundanz (07.09.)

## ⚠️⚠️ Warum N-63 wiederholt werden muss

N-63 verglich Regler und Schalter mit `pruefe_auswahl`. Der Schalter-Arm
war ungueltig, und die Ursache ist mechanisch:

    `sammle` sperrt   Rang >= 0,8
    0/1-Kennzahl      65,2 % Einsen
    -> das oberste Rangfuenftel liegt GANZ in der Einser-Gruppe
    -> `rang` bricht Gleichstaende mit argsort(kind="mergesort"),
       also nach ARRAY-REIHENFOLGE

**Belegt** (`n63`-Gegenpruefung): an einem Tag mit 306 Werten sind nach
Umsortieren der Zeilen nur **15 von 62** gewaehlten Symbolen dieselben.
Der Arm mass eine beliebige Teilmenge; +0,0040 R ist das erwartete Nichts.

## Wie es hier richtig gemacht wird

Nicht ueber den Rang, sondern ueber die GRUPPE selbst - dann gibt es
nichts zu brechen:

    SCHALTER   median(kurs < sma200) - median(alle Gewaehlten)   je Tag
    REGLER     median(oberstes Rangfuenftel) - median(alle)      je Tag
               (dieselbe Statistik, damit der Vergleich zaehlt)

⚠️ **Beide Arme werden ENTZERRT.** N-65 hat gezeigt, dass
`median(Gruppe) - median(alle)` bei kleinen Gruppen nach oben verzerrt
ist - in einer Welt ohne Information lieferte sie +0,10 bis +0,16 R. Der
Nullwert wird je Arm eigens gezogen und abgezogen.

## ⚠️ Und die Redundanzfrage, diesmal an der richtigen Stelle

N-65 hat Spearman +0,704 zwischen `schnitt`-Rang und Momentum-Rang
gemessen - **im vollen Tagesquerschnitt.** Das ist nicht die Stelle, an
der der Beitrag wirkt.

> An Stufe 12 sind die Werte der Stufe 5 bereits ausgewaehlt. Ob `schnitt`
> dort noch etwas beitraegt, entscheidet die Korrelation INNERHALB der
> Auswahl - und die ist durch die Einengung des Wertebereichs
> typischerweise kleiner.

Beides wird nebeneinander gezeigt. **Die zweite Zahl ist die, die zaehlt.**

    python n66_form_gleichstandsfrei.py
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
from n64_schnitt_stufen import PUNKT_JE_R, band               # noqa: E402

HORIZONT, MENGE = 20, "20%"
ZIEH, SAAT = 20, 20260907


def je_tag_gruppe(je_tag, mom, anteil, art, mische=None):
    """median(Gruppe) - median(alle Gewaehlten), je Kalendertag.

    `art` ist "schalter" (kurs unter dem 200-Schnitt) oder "regler"
    (oberstes Rangfuenftel der stetigen Kennzahl).

    ⚠️ Der SCHALTER geht NICHT ueber den Rang - genau dort lag der Fehler
    von N-63. Er fragt die Kennzahl direkt: `kennzahl < 0` heisst unter
    dem Schnitt. Gleichstaende gibt es dabei nicht.
    """
    aus, groesse = {}, []
    for tag, zeilen in je_tag.items():
        if len(zeilen) < 12:
            continue
        kz = np.array([x["kennzahl"] for x in zeilen], float)
        y = np.array([x["in_r"] for x in zeilen], float)
        if art == "schalter":
            g = kz < 0.0
        else:
            r = RW.rang(kz)
            g = r >= RW.GRENZE
        if mische is not None:
            g = mische.permutation(g)
        m = A._auswahl_maske(zeilen, mom.get(tag) or {}, anteil, None)
        if m is None or not m.any():
            continue
        gw, yw = g[m], y[m]
        if gw.sum() < 1 or (~gw).sum() < 1:
            continue
        groesse.append(int(gw.sum()))
        aus[tag] = float(np.median(yw[gw])) - float(np.median(yw))
    return aus, groesse


def entzerrt(je_tag, mom, anteil, art, block):
    """Punktschaetzer, Band und Nullwert - der Nullwert wird abgezogen."""
    echt, groesse = je_tag_gruppe(je_tag, mom, anteil, art)
    e = band(echt, block)
    if e is None:
        return None
    null = []
    for z in range(ZIEH):
        n, _ = je_tag_gruppe(je_tag, mom, anteil, art,
                             mische=np.random.default_rng(SAAT + z))
        nb = band(n, block, zieh=300, saat=SAAT + z)
        if nb:
            null.append(nb[0])
    nw = float(np.mean(null)) if null else 0.0
    return {"roh": e[0], "unten": e[1], "oben": e[2], "tage": e[3],
            "null": nw, "null_min": min(null) if null else 0.0,
            "null_max": max(null) if null else 0.0,
            "wirkung": e[0] - nw, "groesse": float(np.mean(groesse))}


def main() -> int:
    t0 = time.time()
    print("=" * 96)
    print("N-66 — Formfrage ohne Gleichstandsfalle + Redundanz in der Auswahl")
    print("=" * 96)
    reihen = B.lade()
    mom = momentum250(reihen)
    je_tag = K.baue(reihen, "schnitt", horizont=HORIZONT)
    anteil = MENGEN[MENGE]
    block = _block(HORIZONT)
    print("  %d Reihen . %d Kalendertage . Block %d . %d Nullziehungen"
          % (len(reihen), len(je_tag), block, ZIEH))

    # ---- 1  BEIDE FORMEN, dieselbe Statistik, beide entzerrt -----------
    print()
    print("  1  BEIDE FORMEN — median(Gruppe) - median(alle), entzerrt")
    print("     %-12s %9s %9s %11s %9s %10s"
          % ("Form", "roh R", "Null R", "entzerrt R", "Punkte", "Gruppe/Tag"))
    erg = {}
    for art, lab in (("schalter", "SCHALTER"), ("regler", "REGLER")):
        e = entzerrt(je_tag, mom, anteil, art, block)
        if e is None:
            print("     %-12s  nicht messbar" % lab)
            continue
        erg[art] = e
        print("     %-12s %+9.4f %+9.4f %+11.4f %+9.2f %10.1f"
              % (lab, e["roh"], e["null"], e["wirkung"],
                 e["wirkung"] * PUNKT_JE_R, e["groesse"]), flush=True)
    print("     ⚠️ Der SCHALTER fragt `kennzahl < 0` direkt - kein Rang,")
    print("        keine Gleichstaende. Das war der Fehler in N-63.")

    # ---- 2  DIE REDUNDANZ, an beiden Stellen ---------------------------
    print()
    print("  2  ⚠️⚠️ REDUNDANZ zur Auswahl — voll gegen INNERHALB")
    voll, innen = [], []
    for tag, zeilen in je_tag.items():
        if len(zeilen) < 12:
            continue
        mt = mom.get(tag) or {}
        paare = [(x["kennzahl"], mt.get(x["sym"])) for x in zeilen]
        idx = [i for i, (_a, b) in enumerate(paare) if b is not None]
        if len(idx) < 12:
            continue
        sv = np.array([paare[i][0] for i in idx], float)
        mv = np.array([paare[i][1] for i in idx], float)
        rs, rm = RW.rang(sv), RW.rang(mv)
        if rs.std() > 0 and rm.std() > 0:
            voll.append(float(np.corrcoef(rs, rm)[0, 1]))
        m = A._auswahl_maske(zeilen, mt, anteil, None)
        if m is None or m.sum() < 8:
            continue
        # ⚠️ Der Rang wird INNERHALB der Auswahl neu gebildet - sonst
        # verglichen wir wieder die Position im vollen Querschnitt.
        sv2 = np.array([x["kennzahl"] for x, keep in zip(zeilen, m) if keep],
                       float)
        mv2 = np.array([mt.get(x["sym"], np.nan)
                        for x, keep in zip(zeilen, m) if keep], float)
        ok = np.isfinite(mv2)
        if ok.sum() < 8:
            continue
        r1, r2 = RW.rang(sv2[ok]), RW.rang(mv2[ok])
        if r1.std() > 0 and r2.std() > 0:
            innen.append(float(np.corrcoef(r1, r2)[0, 1]))
    for lab, w in (("im vollen Tagesquerschnitt", voll),
                   ("INNERHALB der Auswahl (Stufe 12)", innen)):
        print("     %-34s %+6.3f  [%+.3f .. %+.3f]  %d Tage"
              % (lab, float(np.mean(w)), float(np.percentile(w, 5)),
                 float(np.percentile(w, 95)), len(w)))

    # ---- Urteil ---------------------------------------------------------
    print()
    print("=" * 96)
    print("WAS DAS HEISST")
    print("=" * 96)
    s, r = erg.get("schalter"), erg.get("regler")
    if s and r:
        print("  SCHALTER %+.4f R  ·  REGLER %+.4f R"
              % (s["wirkung"], r["wirkung"]))
        # ⚠️ Punktschaetzer vergleichen waere der Fehler, den die Messnorm
        # verhindern soll. Die BAENDER entscheiden - roh, weil der Abzug
        # bei beiden aus derselben Konstruktion kommt.
        ueberlappt = not (s["unten"] > r["oben"] or r["unten"] > s["oben"])
        print("  Rohbaender: SCHALTER [%+.4f .. %+.4f] REGLER [%+.4f .. %+.4f]"
              % (s["unten"], s["oben"], r["unten"], r["oben"]))
        print("  %s"
              % ("⚠️ DIE BAENDER UEBERLAPPEN - die Formen sind NICHT "
                 "unterscheidbar." if ueberlappt else
                 "✔ Die Baender trennen - %s traegt mehr."
                 % ("SCHALTER" if s["wirkung"] > r["wirkung"] else "REGLER")))
    if innen:
        ri = float(np.mean(innen))
        print()
        print("  Redundanz INNERHALB der Auswahl: %+.3f" % ri)
        print("  %s"
              % ("⚠️⚠️ auch dort stark - `schnitt` bewertet an Stufe 12, "
                 "was Stufe 5 schon entschied" if ri > 0.5 else
                 "⚠️ teilweise redundant" if ri > 0.25 else
                 "✔ innerhalb der Auswahl weitgehend UNABHAENGIG - die "
                 "+0,704 im vollen Querschnitt sind Bereichseinengung, "
                 "kein Argument gegen den Beitrag"))
    print("  Dauer %.1f Minuten" % ((time.time() - t0) / 60.0))
    return 0


if __name__ == "__main__":
    sys.exit(main())
