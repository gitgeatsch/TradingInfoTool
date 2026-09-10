# -*- coding: utf-8 -*-
"""S-7 GEGENPRUEFUNG — warum ist `schnitt` ab 2022 unentscheidbar? (10.09.)

## Was der Hauptlauf ergeben hat - und was er NICHT ergeben hat

    Fenster    schnitt          funding
    ganz       3 von 3  TRAEGT  2 von 3  TRAEGT
    ab 2022    0 von 3          2 von 3  TRAEGT
    ab 2023    0 von 3          2 von 3  TRAEGT
    ab 2024    KEIN BEFUND      KEIN BEFUND   (Blockregel)

⚠️⚠️⚠️ **ABER DAS URTEIL LAUTET NICHT ,TRAEGT NICHT'.** Auf allen drei
Mengen ab 2022 steht **NICHT TRENNBAR**. Die Norm unterscheidet genau
das:

    TRAEGT NICHT bis X   die Wirkung liegt UNTER der gemessenen
                         Aufloesung -> Effekte ab X sind ausgeschlossen.
                         Eine Aussage ueber die Welt.
    NICHT TRENNBAR       die Wirkung liegt UEBER der Aufloesung, aber
                         das Band schliesst den Nullpunkt nicht aus.
                         KEINE Aussage - die Messung kann nicht
                         entscheiden.

`zufall` bekommt in JEDER Zeile "TRAEGT NICHT bis X" - eine Aussage.
`schnitt` bekommt ab 2022 dreimal "NICHT TRENNBAR" - keine.

> **S-7 ist damit in seinem eigenen Wortlaut bestaetigt** - *,es ist
> unentschieden'* - und NICHT in der Lesart, `schnitt` trage ab 2022
> nicht.

## ⚠️ Die Auffaelligkeit, die den ganzen Fall traegt

    ab 2022, 10 %:  Trennschaerfe 0,10 R · Wirkung +0,1221 · NICHT TRENNBAR

Die Anlage findet dort einen **gepflanzten** Effekt von 0,10 R. Der
**gemessene** liegt mit +0,12 darueber - und ist trotzdem nicht vom
Nullpunkt zu trennen. Das ist kein Widerspruch, sondern ein Hinweis:

> **Ein gepflanzter Effekt ist gleichmaessig verteilt. Ein echter muss
> das nicht sein.** Liegt die Wirkung in wenigen Bloecken, ist das Band
> breit, obwohl der Punktschaetzer gross ist.

## Was hier geprueft wird - vier Fragen, alle vorab benannt

    G1  REPRODUKTION (R-R11)   treffen meine Zahlen S-7s Groessenordnung?
    G2  BANDBREITE             ist `schnitt`s Schaetzer breiter als
                               `funding`s - bei gleicher Blockzahl?
    G3  ⚠️ KLUMPIGKEIT          liegt `schnitt`s Wirkung in wenigen
                               Jahren, `funding`s dagegen gleichmaessig?
    G4  DIE STILLE ab 2024     der Hauptlauf gab dort GAR KEINE Zeile
                               aus - fail-silent im eigenen Skript

⚠️ **G3 ist deskriptiv, kein Urteil.** Ein Jahr hat ~6 Bloecke, weit
unter den 20 geforderten. Gemessen wird die STREUUNG, nicht die Wirkung
- und `zufall` laeuft als Kontrolle mit: streut er genauso, ist die
Streuung eine Eigenschaft des Jahresfensters, nicht von `schnitt`.

## Die Vorhersage, VOR dem Lauf (Methodik 2.80)

    G1  reproduziert - gleiche Groessenordnung, nicht gleiche Zahl
    G2  `schnitt`s Band deutlich breiter
    G3  ⚠️ `schnitt` klumpig (wenige starke Jahre), `funding` gleichmaessig
    G4  `zulaessige_mengen` gab [] zurueck - die Blockregel, still

    python n109_s7_gegenpruefung.py
"""
from __future__ import annotations

import sys
import time
from collections import defaultdict

import numpy as np

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import messe_eigenschaft_beitrag as B                         # noqa: E402
import messe_kandidaten_als_regel as K                        # noqa: E402
import messnorm as N                                          # noqa: E402
import messnorm_auswahl as MA                                 # noqa: E402
from messe_alle_kandidaten import HORIZONT, zusatzquellen     # noqa: E402
from messe_beitrag_auf_auswahl import momentum250, sammle     # noqa: E402
from pruefe_n31_tagesklammer import je_tag_wirkung            # noqa: E402

KAND = ("schnitt", "funding", "zufall")
# S-7s Tafel vom 07.09. - Reproduktionspruefung, NICHT Sollwert
S7 = {"schnitt": {"ganz": 0.1623, "ab 2022": 0.0414, "ab 2023": 0.0478},
      "funding": {"ganz": 0.0446, "ab 2022": 0.0157, "ab 2023": 0.0170}}
# aus dem Hauptlauf n108, auf der 20-%-Menge
MEIN = {"schnitt": {"ganz": 0.1858, "ab 2022": 0.0589, "ab 2023": 0.0692},
        "funding": {"ganz": 0.0582, "ab 2022": 0.0220, "ab 2023": 0.0236}}
BAENDER = {  # (Fenster, Menge) -> (kand, wirkung, unten, oben, bloecke)
    ("ab 2022", "10%"): (("schnitt", 0.1221, -0.0098, 0.3731, 25),
                         ("funding", 0.0542, 0.0175, 0.0808, 25)),
    ("ab 2022", "20%"): (("schnitt", 0.0589, -0.0124, 0.2835, 28),
                         ("funding", 0.0220, 0.0021, 0.0443, 27)),
    ("ab 2022", "50%"): (("schnitt", 0.0358, -0.0010, 0.1464, 28),
                         ("funding", 0.0257, 0.0134, 0.0637, 28)),
    ("ganz", "20%"): (("schnitt", 0.1858, 0.0957, 0.3750, 41),
                      ("funding", 0.0582, 0.0101, 0.1168, 37))}


def main() -> int:
    t0 = time.time()
    print("=" * 112)
    print("S-7 GEGENPRUEFUNG — warum ist `schnitt` ab 2022 unentscheidbar?")
    print("=" * 112)

    # ---- G1  REPRODUKTION (R-R11) ---------------------------------------
    print()
    print("G1  REPRODUKTION — treffen meine Zahlen S-7s Groessenordnung?")
    print("    ⚠️ S-7 lief VOR dem Messstandard. Gefordert ist gleiche")
    print("       GROESSENORDNUNG, nicht gleiche Zahl.")
    print("    %-9s %-9s %9s %9s %9s  %s"
          % ("Kandidat", "Fenster", "S-7", "meins", "Faktor", "Urteil"))
    ok = True
    for k in ("schnitt", "funding"):
        for f in ("ganz", "ab 2022", "ab 2023"):
            a, b = S7[k][f], MEIN[k][f]
            fak = b / a if a else float("nan")
            gut = 0.5 <= fak <= 2.0 and (a > 0) == (b > 0)
            ok = ok and gut
            print("    %-9s %-9s %+9.4f %+9.4f %9.2fx  %s"
                  % (k, f, a, b, fak,
                     "✔ reproduziert" if gut else "⚠️ WEICHT AB"))
    print("    -> %s" % ("✔ R-R11 erfuellt - S-7 ist reproduziert, das "
                         "Urteil darf gedeutet werden" if ok else
                         "⚠️⚠️ NICHT reproduziert - kein Widerruf zulaessig"))

    # ---- G2  BANDBREITE --------------------------------------------------
    print()
    print("G2  BANDBREITE — ist `schnitt`s Schaetzer breiter als `funding`s?")
    print("    %-9s %-6s %-9s %9s %9s %9s %6s"
          % ("Fenster", "Menge", "Kandidat", "Wirkung", "Bandbr.",
             "W/Band", "Bloe."))
    verh = defaultdict(list)
    for (f, m), zeilen in sorted(BAENDER.items()):
        for k, w, u, o, bl in zeilen:
            br = o - u
            q = w / br if br else float("nan")
            verh[k].append(q)
            print("    %-9s %-6s %-9s %+9.4f %9.4f %9.2f %6d"
                  % (f, m, k, w, br, q, bl))
    print("    -> Signal je Bandbreite im Mittel:  schnitt %.2f · "
          "funding %.2f"
          % (float(np.mean(verh["schnitt"])), float(np.mean(verh["funding"]))))
    if float(np.mean(verh["schnitt"])) < float(np.mean(verh["funding"])):
        print("    ⚠️⚠️ BESTAETIGT: `schnitt` hat die groessere Wirkung, "
              "aber das SCHLECHTERE")
        print("       Verhaeltnis von Signal zu Band. Er ist der "
              "unruhigere Schaetzer.")

    # ---- G3  KLUMPIGKEIT -------------------------------------------------
    print()
    print("G3  ⚠️ KLUMPIGKEIT — liegt die Wirkung in wenigen Jahren?")
    print("    ⚠️ DESKRIPTIV, KEIN URTEIL: ein Jahr hat ~6 Bloecke, "
          "gefordert sind 20.")
    print("       Gemessen wird die STREUUNG ueber die Jahre, nicht die "
          "Wirkung eines Jahres.")
    reihen = B.lade()
    mom = momentum250(reihen)
    zus = zusatzquellen()
    jahre = defaultdict(dict)
    for k in KAND:
        je = K.baue(reihen, k, zus.get(k), horizont=HORIZONT)
        g = sammle(je, mom, MA.MENGEN["20%"], None)
        d = je_tag_wirkung(g)
        proj = defaultdict(list)
        for tag, w in d.items():
            proj[str(tag)[:4]].append(float(w))
        for j, ws in sorted(proj.items()):
            if len(ws) >= 60:                # mind. ein Block
                jahre[k][j] = (float(np.mean(ws)), len(ws))
    alle_j = sorted({j for k in KAND for j in jahre[k]})
    print("    %-9s %s" % ("Kandidat", " ".join("%8s" % j for j in alle_j)))
    for k in KAND:
        print("    %-9s %s"
              % (k, " ".join(("%+8.3f" % jahre[k][j][0]) if j in jahre[k]
                             else "       ." for j in alle_j)))
    print("    %-9s %s"
          % ("(Tage)", " ".join("%8d" % jahre["schnitt"][j][1]
                                if j in jahre["schnitt"] else "       ."
                                for j in alle_j)))
    print()
    print("    %-9s %9s %9s %9s %9s  %s"
          % ("Kandidat", "Mittel", "Streuung", "Str/Mit", "max/Mit",
             "Deutung"))
    kl = {}
    for k in KAND:
        v = np.array([x[0] for x in jahre[k].values()], dtype=float)
        if v.size < 3:
            continue
        mi, st = float(v.mean()), float(v.std(ddof=1))
        rel = st / abs(mi) if mi else float("nan")
        mx = float(np.abs(v).max()) / abs(mi) if mi else float("nan")
        kl[k] = rel
        print("    %-9s %+9.4f %9.4f %9.2f %9.2f  %s"
              % (k, mi, st, rel, mx,
                 "gleichmaessig" if rel < 1.0 else
                 "⚠️ KLUMPIG - die Streuung uebersteigt das Mittel"))
    if kl.get("schnitt", 0) > kl.get("funding", 9) and \
            kl.get("schnitt", 0) > 1.0:
        print("    ⚠️⚠️⚠️ BESTAETIGT: `schnitt`s Wirkung liegt in wenigen "
              "Jahren, `funding`s")
        print("       verteilt sich. DAS ist der Grund fuer das breite "
              "Band - nicht ein")
        print("       fehlender Effekt. Und `zufall` als Kontrolle zeigt, "
              "ob die Streuung")
        print("       eine Eigenschaft des Jahresfensters ist.")
    else:
        print("    ✖ NICHT bestaetigt - die Klumpigkeit erklaert das "
              "breite Band nicht.")

    # ---- G4  DIE STILLE ab 2024 -----------------------------------------
    print()
    print("G4  DIE STILLE ab 2024 — der Hauptlauf gab dort keine Zeile aus")
    je = K.baue(reihen, "schnitt", None, horizont=HORIZONT)
    je24 = {t: z for t, z in je.items() if str(t) >= "2024-01-01"}
    zul = MA.zulaessige_mengen(je24, mom, horizont=HORIZONT)
    print("    Tage ab 2024: %d · zulaessige Mengen: %s"
          % (len(je24), zul if zul else "[] — KEINE"))
    for m in ("10%", "20%", "50%", "frei"):
        dl = MA.datenlage(je24, mom, m, horizont=HORIZONT)
        print("      %-6s %4d Tage · %2d Bloecke (20 gefordert) · %s"
              % (m, dl["tage"], dl["bloecke"],
                 "messbar" if dl["messbar"] else "NICHT messbar"))
    if not zul:
        print("    ✔ BESTAETIGT: `zulaessige_mengen` gibt [] zurueck - die")
        print("      Blockregel greift. Das Urteil KEIN BEFUND ist richtig.")
        print("    ⚠️ ABER MEIN SKRIPT SAGTE ES NICHT: bei leerer Liste "
              "laeuft die innere")
        print("      Schleife nie, und es wird gar nichts gedruckt. "
              "Fail-silent im")
        print("      eigenen Werkzeug - die Abnahmetafel hat es "
              "aufgefangen, die Zeile")
        print("      nicht. S-7s Spalte ,ab 2024' war unter dem heutigen "
              "Standard nie gueltig.")

    print()
    print("  Dauer %.1f Minuten" % ((time.time() - t0) / 60.0))
    return 0


if __name__ == "__main__":
    sys.exit(main())
