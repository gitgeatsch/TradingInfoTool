# -*- coding: utf-8 -*-
"""HAENGT DAS OPTIMALE CRV VON DER MERKMALSLAGE AB?

## Die Vorabfestlegung - vor der Messung geschrieben

`2.563` hat gemessen: die Trefferquote folgt fast exakt `1/(1+CRV)`, und
der UEBERSCHUSS ueber diese Theorie waechst mit dem CRV (aufwaerts -0,019
bei CRV 1 auf +0,023 bei CRV 5). Dieser Ueberschuss ist das, was Kelly
positiv macht - nicht die Quote selbst.

Gemessen wurde das je MARKTPHASE. Offen und hier gefragt:

    Ist der Ueberschuss je MERKMALSLAGE verschieden - gibt es also Lagen,
    in denen ein anderes CRV als 2,0 richtig waere?

## ⚠️⚠️ DIE MENGE: `messuniversum`, NICHT die selektierte

`messnorm.FRAGEARTEN` legt das fest:

    geometrie   "Wie soll die Geometrie stehen (Stop, Ziel, Horizont)?"
                menge = messuniversum
                "die Geometrie gilt fuer jeden Anker, nicht nur fuer die
                 ausgewaehlten - hier ist die breite Basis richtig"

Das CRV ist eine Geometriefrage. ⚠️ Die selektierte Menge laeuft trotzdem
als GEGENPRUEFUNG mit - weil die Aufschluesselung nach Merkmalen dort
stattfindet, wo die Merkmale auch wirken (F-212).

## Die Entscheidungsregel - vorab

    haengt ab      der Ueberschuss unterscheidet sich zwischen Lagen
                   BELEGT (Baender ohne Ueberschneidung) -> ein CRV je
                   Lage ist begruendbar
    haengt NICHT   die Unterschiede bleiben im Band -> EIN globales CRV,
                   und die Wahl ist eine Abwaegung Signalzahl gegen
                   Qualitaet (Nutzerentscheidung nach 2.521)
    ⛔ nicht       die Aufloesung reicht nicht -> KEIN Urteil, der Punkt
       entscheidbar wird als Datendecke geschlossen

⚠️ MEHRFACHTEST: 25 Lagen. Die Erwartung wird gerechnet, nicht geschaetzt.

## ⚠️⚠️ DIE MACHBARKEITSSTUFE LAEUFT ZUERST

Der Ueberschuss bewegt sich um plus/minus 0,02. Die Baender je Lage lagen
in 2.561 bei plus/minus 0,03 - also BREITER als die gesuchte Groesse. Ohne
S0 waere ein Nullergebnis nicht deutbar (Lehre aus Vorabfestlegung 4).

⚠️ NUR LESEND.

    python phase4_crv_je_lage.py
    python phase4_crv_je_lage.py --menge 20%
    python phase4_crv_je_lage.py --quelle frei
"""
from __future__ import annotations

import math
import sys
from collections import defaultdict

import numpy as np

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import messe_bewertung_kalibrierung as KAL                   # noqa: E402
import messe_eigenschaft_beitrag as B                        # noqa: E402
import messe_funding_niveau as F                             # noqa: E402
import messe_kandidaten_als_regel as K                       # noqa: E402
import messe_zielregel as ZR                                 # noqa: E402
import messnorm                                              # noqa: E402
import phase3_reproduktion as R3                             # noqa: E402

BLOCK = 90
ZIEHUNGEN = 400
MIN_ANKER = 500
CRVS = (1.0, 1.5, 2.0, 3.0, 5.0)
VARIANTE_JE_CRV = {1.0: "ZIEL 1,0", 1.5: "ZIEL 1,5", 2.0: "ZIEL 2,0",
                   3.0: "ZIEL 3,0", 5.0: "ZIEL 5,0"}


def sammle(menge: str, quelle: str) -> dict:
    """{(fu, tu): {tag: [(crv -> 0/1/None), ...]}} - alle CRV auf DENSELBEN
    Ankern.

    ⚠️ Das ist der Kern: `messe_zielregel.ergebnisse()` liefert jede
    Variante fuer denselben Anker und denselben Pfad. Ein Vergleich ueber
    verschieden gezogene Mengen waere keiner.
    """
    reihen = B.lade()
    erlaubt = KAL.erlaubte_anker(reihen, menge)
    tage_je_sym = {s: [z[0] for z in roh] for s, roh in reihen.items()}
    zeilen = ZR.ergebnisse(reihen)
    fu5 = KAL._fuenftel_je_tag(K.baue(reihen, "funding", F.lade_funding(),
                                      horizont=20))
    tu5 = KAL._fuenftel_je_tag(K.baue(reihen, "turnover",
                                      R3._zusatz("turnover", quelle),
                                      horizont=20))
    aus: dict = defaultdict(lambda: defaultdict(list))
    for z in zeilen:
        sym, i = z["sym"], z["i"]
        tg = tage_je_sym.get(sym)
        if not tg or i >= len(tg):
            continue
        tag = tg[i]
        if erlaubt is not None and (tag, sym) not in erlaubt:
            continue
        f, t = fu5.get(tag, {}).get(sym), tu5.get(tag, {}).get(sym)
        if f is None or t is None:
            continue
        satz = {}
        for c in CRVS:
            w = z.get(VARIANTE_JE_CRV[c])
            # ⚠️ NUR ENTSCHIEDENE, je CRV eigens: exakt +c (Ziel) oder -1
            # (Stop). Ein Anker kann bei CRV 1 entschieden sein und bei
            # CRV 5 nicht - deshalb je CRV getrennt gezaehlt.
            if w is None:
                continue
            if abs(w - c) < 1e-9:
                satz[c] = 1
            elif abs(w + 1.0) < 1e-9:
                satz[c] = 0
        if satz:
            aus[(f, t)][tag].append(satz)
    return {k: dict(v) for k, v in aus.items()}


def quote_und_band(je_tag: dict, c: float, rng) -> tuple:
    """Trefferquote bei CRV c, mit Blockbootstrap ueber Kalendertage."""
    tage = [t for t in sorted(je_tag)
            if any(c in s for s in je_tag[t])]
    if len(tage) < BLOCK + 10:
        return (float("nan"),) * 3
    tr = {t: sum(s[c] for s in je_tag[t] if c in s) for t in tage}
    n = {t: sum(1 for s in je_tag[t] if c in s) for t in tage}
    ges_n = sum(n.values())
    if ges_n < MIN_ANKER:
        return (float("nan"),) * 3
    q = sum(tr.values()) / ges_n
    starts = np.arange(len(tage) - BLOCK + 1)
    anzahl = int(np.ceil(len(tage) / BLOCK))
    werte = []
    for _ in range(ZIEHUNGEN):
        idx = rng.choice(starts, anzahl)
        tg = [tage[j] for s in idx
              for j in range(s, min(s + BLOCK, len(tage)))][:len(tage)]
        a = sum(tr[t] for t in tg)
        b = sum(n[t] for t in tg)
        if b:
            werte.append(a / b)
    if not werte:
        return (float("nan"),) * 3
    return (q, float(np.percentile(werte, 2.5)),
            float(np.percentile(werte, 97.5)))


def gepaart(je_tag: dict, c1: float, c2: float, rng) -> tuple:
    """Ueberschuss(c1) minus Ueberschuss(c2) auf DENSELBEN Ankern.

    ⚠️⚠️ DAS IST DIE RICHTIGE FRAGE, UND MEINE ERSTE FASSUNG STELLTE SIE
    FALSCH. Sie hielt die Bandbreite der EINZELNEN Quote (rund 0,07) gegen
    die gesuchte Spanne (0,042) und brach als "nicht entscheidbar" ab.
    Das Memory `ueberlappende-baender-sagen-nichts` sagt genau dazu:
    *"ueberlappende Baender sagen NICHTS ueber ihren Unterschied - der
    gepaarte Test ist einer"*.

    Die CRV-Varianten liegen auf DENSELBEN Ankern und DEMSELBEN Pfad.
    Gepaart gemessen ist das Band drei- bis viermal enger: CRV 5 minus 2
    ergab global +0,0265 [+0,0108 .. +0,0398] statt einer Ueberlappung.

    ⚠️ Gezaehlt werden nur Anker, die bei BEIDEN CRV entschieden sind -
    sonst vergliche man zwei verschiedene Mengen.
    """
    tr1, n1, tr2, n2 = {}, {}, {}, {}
    for t in sorted(je_tag):
        s_ = [x for x in je_tag[t] if c1 in x and c2 in x]
        if not s_:
            continue
        tr1[t] = sum(x[c1] for x in s_)
        tr2[t] = sum(x[c2] for x in s_)
        n1[t] = n2[t] = len(s_)
    tg = sorted(tr1)
    if len(tg) < BLOCK + 10 or sum(n1.values()) < MIN_ANKER:
        return (float("nan"),) * 4

    def wert(auswahl):
        a1 = sum(tr1[t] for t in auswahl)
        b1 = sum(n1[t] for t in auswahl)
        a2 = sum(tr2[t] for t in auswahl)
        b2 = sum(n2[t] for t in auswahl)
        if not b1 or not b2:
            return None
        return (a1 / b1 - 1 / (1 + c1)) - (a2 / b2 - 1 / (1 + c2))

    punkt = wert(tg)
    starts = np.arange(len(tg) - BLOCK + 1)
    anzahl = int(np.ceil(len(tg) / BLOCK))
    z = []
    for _ in range(ZIEHUNGEN):
        idx = rng.choice(starts, anzahl)
        aus = [tg[j] for s_ in idx
               for j in range(s_, min(s_ + BLOCK, len(tg)))][:len(tg)]
        v = wert(aus)
        if v is not None:
            z.append(v)
    if not z:
        return (float("nan"),) * 4
    return (punkt, float(np.percentile(z, 2.5)),
            float(np.percentile(z, 97.5)), sum(n1.values()))


def main() -> int:
    menge = KAL._argv_wert("--menge", "frei")
    quelle = KAL._argv_wert("--quelle", "gesamt")
    print("=" * 112)
    print("HAENGT DAS OPTIMALE CRV VON DER MERKMALSLAGE AB?")
    print("=" * 112)
    print("  MENGE %s · QUELLE %s · Block %d · %d Ziehungen"
          % (menge, quelle, BLOCK, ZIEHUNGEN))
    print("  Frageart `geometrie` -> messnorm verlangt das MESSUNIVERSUM")
    print("  ⚠️ Gemessen wird die GEPAARTE Differenz der Ueberschuesse")
    print("     q - 1/(1+CRV) auf DENSELBEN Ankern - nicht zwei Baender")
    print("     nebeneinander (Memory `ueberlappende-baender`).")
    print("  Laden ...")
    lagen = sammle(menge, quelle)
    rng = np.random.default_rng(messnorm.SAAT)
    alle = {}
    for je in lagen.values():
        for tag, sx in je.items():
            alle.setdefault(tag, []).extend(sx)

    # ---- S0  MACHBARKEIT, GEPAART ----------------------------------
    # ⚠️⚠️ DIE ERSTE FASSUNG PRUEFTE DIE BREITE DER EINZELBAENDER (rund
    # 0,07) gegen die gesuchte Spanne (0,042) und brach faelschlich als
    # "nicht entscheidbar" ab. Das war derselbe Fehler, den das Memory
    # `ueberlappende-baender-sagen-nichts` beschreibt. Geprueft wird
    # jetzt die GEPAARTE Differenz - dieselbe Groesse wie die Hauptfrage.
    print("-" * 112)
    print("  S0  MACHBARKEIT - traegt der CRV-Unterschied GLOBAL?")
    print("-" * 112)
    global_ok = False
    for c1, c2 in ((5.0, 2.0), (3.0, 2.0), (2.0, 1.0)):
        d, u, o, n = gepaart(alle, c1, c2, rng)
        if not np.isfinite(d):
            print("     CRV %.1f minus %.1f   kein Band" % (c1, c2))
            continue
        traegt = u > 0 or o < 0
        global_ok = global_ok or traegt
        print("     CRV %.1f minus %.1f   %+.4f  [%+.4f .. %+.4f]  %7d Anker  %s"
              % (c1, c2, d, u, o, n, "✔ TRAEGT" if traegt else "⚠ Null ein"))
    if not global_ok:
        print("  ⛔ ABBRUCH - schon global traegt kein CRV-Unterschied.")
        print("     Je Lage waere er erst recht nicht zu finden.")
        print("=" * 112)
        return 0
    print("     ➤ ✔ MACHBAR - global traegt es, je Lage ist die Frage sinnvoll.")

    # ---- DIE MESSUNG JE LAGE ---------------------------------------
    print("-" * 112)
    print("  CRV 5,0 MINUS 2,0 JE MERKMALSLAGE  (gepaart, dieselben Anker)")
    print("-" * 112)
    print("  %-9s %9s %11s %-24s %s"
          % ("Lage", "Anker", "Differenz", "Band", "Urteil"))
    traegt_zahl, werte, breiten = 0, [], []
    for (f, t), je in sorted(lagen.items()):
        d, u, o, n = gepaart(je, 5.0, 2.0, rng)
        if not np.isfinite(d):
            print("  fu%d/tu%d   %9s %11s %-24s ⚠ NICHT GEDEUTET"
                  % (f, t, "-", "-", "zu wenige Anker"))
            continue
        werte.append(d)
        breiten.append(o - u)
        traegt = u > 0 or o < 0
        traegt_zahl += int(traegt)
        print("  fu%d/tu%d   %9d %+11.4f [%+.4f .. %+.4f]   %s"
              % (f, t, n, d, u, o, "✔ TRAEGT" if traegt else "⚠ Null ein"))

    print("=" * 112)
    print("  AUSWERTUNG")
    print("=" * 112)
    if not werte:
        print("  ⛔ keine Lage gedeutet.")
        return 0
    w = np.array(werte)
    print("  gedeutete Lagen: %d von %d" % (len(w), len(lagen)))
    print("  Differenz CRV 5 minus 2: Median %+.4f · Spanne %+.4f bis %+.4f"
          % (np.median(w), w.min(), w.max()))
    print("  Lagen, in denen der Unterschied traegt: %d von %d"
          % (traegt_zahl, len(w)))
    lam = 0.05 * len(w)
    p_zufall = 1.0 - sum(math.exp(-lam) * lam ** k / math.factorial(k)
                         for k in range(traegt_zahl))
    print("  ⚠️ Erwartung rein zufaellig: %.2f · Poisson p(>=%d) = %.4f"
          % (lam, traegt_zahl, p_zufall))
    # ⚠️⚠️⚠️ DIE EIGENTLICHE FRAGE, UND MEIN ERSTES KRITERIUM WAR SCHWACH.
    #
    # Es hielt die SPANNWEITE der Punktwerte gegen die Median-Bandbreite.
    # Die Spannweite ist aber ein EXTREMWERTmass: sie waechst mit der Zahl
    # der Gruppen UND mit dem Rauschen, auch ganz ohne Heterogenitaet. Auf
    # der selektierten Menge (weniger Anker, breitere Baender) meldete sie
    # deshalb faelschlich "die Lagen streuen weiter" - 0,0675 gegen 0,0646,
    # ein Unterschied von 4,5 Prozent, der nichts belegt.
    #
    # Richtig ist ein HETEROGENITAETSTEST: streuen die Punktwerte MEHR,
    # als ihre eigenen Schaetzfehler erwarten lassen? Cochran Q vergleicht
    # genau das, I-Quadrat gibt den Anteil echter Heterogenitaet.
    sig = np.array([b / 3.92 for b in breiten])      # 95-%-Band -> sigma
    gew = 1.0 / sig ** 2
    mittel = float((gew * w).sum() / gew.sum())
    Q = float((gew * (w - mittel) ** 2).sum())
    fg = len(w) - 1
    I2 = max(0.0, (Q - fg) / Q) if Q > 0 else 0.0
    grenze = fg + 2.0 * math.sqrt(2.0 * fg)
    print("  ➤ HETEROGENITAET - streuen die Lagen mehr als ihre Fehler?")
    print("     gewichtetes Mittel   %+.4f" % mittel)
    print("     Cochran Q            %.2f  bei %d Freiheitsgraden "
          "(Grenze %.1f)" % (Q, fg, grenze))
    print("     I-Quadrat            %.1f %%" % (100 * I2))
    print("-" * 112)
    if Q <= grenze:
        print("  ➤ EIN GLOBALES CRV - die Streuung zwischen den Lagen")
        print("    erklaert sich aus den SCHAETZFEHLERN. Die Merkmalslage")
        print("    aendert die richtige Geometrie NICHT.")
        print("    ⚠️ Die WAHL des CRV bleibt eine Abwaegung Signalzahl")
        print("       gegen Qualitaet - nach 2.521 NUTZERENTSCHEIDUNG.")
    else:
        print("  ⚠️ HETEROGEN - die Lagen streuen mehr als ihre Fehler.")
        print("    Ein CRV je Lage ist damit begruendbar; welche Lagen es")
        print("    betrifft, steht in der Spaltenausgabe oben.")
    print("=" * 112)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
