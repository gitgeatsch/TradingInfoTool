# -*- coding: utf-8 -*-
"""N19-E GEPRUEFT: bringt die Kalibrierung gegen die BARRIEREN-Quote etwas?

## Die Vorabfestlegung - vor der Messung geschrieben

N19 (06.09.) hat gemessen: die Umrechnung `d(quote) = d(Potential)/(1+CRV)`
setzt die gemessene R-WIRKUNG mit einer Potentialaenderung gleich - eine
ungeprueste Annahme. Faktoren: `funding` 0,24 bis 0,30, `turnover` 0,34
bis 0,35, `vola` 0,82 bis 0,90. Die Stufen im laufenden System sind damit
1,47- bis 1,85-fach zu gross.

N19-E lautet: *"die Stufen neu kalibrieren - DIREKT gegen die gemessene
Barrieren-Quote, nicht ueber die Umrechnung"*. Als Nutzerentscheidung
markiert, nie umgesetzt.

    Bringt das eine BESSERE Kalibrierung von `q` - und reicht sie, um den
    Hebel zu rechtfertigen?

## ⚠️⚠️ ZWEI FRAGEN, DIE NICHT VERWECHSELT WERDEN DUERFEN

    1 KALIBRIERUNG   trifft `q` dann die tatsaechliche Trefferquote?
                     Pruefgroesse: die Steigung, Sollwert 1/(1+CRV) = 0,333
    2 HEBEL          liegt die Quote dann UEBER der Kelly-Nullstelle?
                     Das ist eine ANDERE Frage - eine ehrliche Bewertung
                     kann durchaus ehrlich ZU NIEDRIG sein.

## ⚠️ KEINE ZIRKULARITAET

Die Stufen werden auf der ERSTEN Historienhaelfte gegen die Barrieren-Quote
gefittet und auf der ZWEITEN geprueft - derselbe Split, den
`messe_bewertung_kalibrierung` benutzt. Die Stufen auf denselben Ankern zu
fitten und zu pruefen waere per Konstruktion wahr.

## Die Entscheidungsregel - vorab

    besser      die Steigung ruecken naeher an 0,333 als die +0,200 der
                heutigen Stufen -> N19-E ist belegt richtig
    gleich      keine Verbesserung -> die Umrechnung war nicht die Ursache
    ⛔ und      unabhaengig davon: liegt die Quote in den steuernden Lagen
       trotzdem UNTER der Kelly-Nullstelle, ist der Hebel weiter nicht
       gerechtfertigt - eine ehrliche Bewertung ist kein Freibrief

⚠️ NUR LESEND.

    python phase4_n19e_pruefen.py
    python phase4_n19e_pruefen.py --menge 20%
    python phase4_n19e_pruefen.py --quelle frei
"""
from __future__ import annotations

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
import phase3_reproduktion as R3                             # noqa: E402
from agent import wahrscheinlichkeit as W                    # noqa: E402

CRV = 2.0


def barrieren_stufen(zeilen, tage_je_sym, f5, nur_tage) -> list:
    """Die Quotenverschiebung je Fuenftel, DIREKT gemessen.

    ⚠️ Das ist der Kern von N19-E: statt die R-Wirkung umzurechnen, wird
    die Barrieren-Trefferquote je Fuenftel gegen den Gesamtschnitt
    gehalten. Das Ergebnis IST die Stufe in Quotenpunkten - ohne
    Zwischenannahme.
    """
    tr = defaultdict(int)
    n = defaultdict(int)
    for z in zeilen:
        sym, i = z["sym"], z["i"]
        tg = tage_je_sym.get(sym)
        if not tg or i >= len(tg):
            continue
        tag = tg[i]
        if tag not in nur_tage:
            continue
        w = z.get(KAL.VARIANTE)
        if w is None:
            continue
        if abs(w - CRV) < 1e-9:
            t = 1
        elif abs(w + 1.0) < 1e-9:
            t = 0
        else:
            continue
        k = f5.get(tag, {}).get(sym)
        if k is None:
            continue
        tr[k] += t
        n[k] += 1
    if not n:
        return []
    ges = sum(tr.values()) / max(sum(n.values()), 1)
    # in PROZENTPUNKTEN, wie `Beitrag.stufen` sie erwartet
    return [100.0 * (tr[k] / n[k] - ges) if n[k] else 0.0 for k in range(5)]


def main() -> int:
    menge = KAL._argv_wert("--menge", "frei")
    quelle = KAL._argv_wert("--quelle", "gesamt")
    print("=" * 104)
    print("N19-E GEPRUEFT - Stufen direkt gegen die BARRIEREN-Quote")
    print("=" * 104)
    print("  MENGE %s · QUELLE %s · CRV %.1f" % (menge, quelle, CRV))

    print("\n  Laden ...")
    reihen = B.lade()
    tage_je_sym = {s: [z[0] for z in roh] for s, roh in reihen.items()}
    zeilen = ZR.ergebnisse(reihen)
    fu5 = KAL._fuenftel_je_tag(K.baue(reihen, "funding", F.lade_funding(),
                                      horizont=20))
    tu5 = KAL._fuenftel_je_tag(K.baue(reihen, "turnover",
                                      R3._zusatz("turnover", quelle),
                                      horizont=20))
    alle = sorted(set(fu5) | set(tu5))
    mitte = alle[len(alle) // 2]
    erste = {t for t in alle if t < mitte}
    print("  Split bei %s - erste Haelfte %d Tage" % (mitte, len(erste)))

    # ---- DIE NEUEN STUFEN, auf der ERSTEN Haelfte -------------------
    print("\n" + "-" * 104)
    print("  DIE STUFEN - heute gegen N19-E (Quotenpunkte)")
    print("-" * 104)
    neu = {}
    for name, merkmal, f5 in (("funding", "funding_fuenftel", fu5),
                              ("turnover", "turnover_fuenftel", tu5)):
        st = barrieren_stufen(zeilen, tage_je_sym, f5, erste)
        live = next((tuple(b.stufen) for b in W.BEITRAEGE
                     if b.merkmal == merkmal and b.stufen), None)
        neu[merkmal] = st
        print("  %-9s heute   %s   Spanne %.2f"
              % (name, " ".join("%+6.2f" % x for x in live),
                 max(live) - min(live)))
        print("  %-9s N19-E   %s   Spanne %.2f"
              % ("", " ".join("%+6.2f" % x for x in st),
                 (max(st) - min(st)) if st else 0.0))
        if st and live:
            print("  %-9s ➤ Faktor %.2f · Vorzeichen gleich in %d von 5"
                  % ("", (max(st) - min(st)) / max(max(live) - min(live), 1e-9),
                     sum(1 for a, b in zip(st, live)
                         if (a >= 0) == (b >= 0))))
    print("\n  ⚠️ Die N19-E-Stufen sind die GEMESSENE Quotenverschiebung je")
    print("     Fuenftel - ohne Umrechnung, ohne Zwischenannahme.")

    # ---- FRAGE 2: reicht das fuer den Hebel? ------------------------
    # ⚠️⚠️ Das ist die ANDERE Frage. Eine ehrliche Bewertung kann ehrlich
    # zu niedrig sein - dann ist der Hebel weiter nicht gerechtfertigt.
    print("\n" + "-" * 104)
    print("  FRAGE 2 - REICHT DIE EHRLICHE BEWERTUNG FUER EINEN HEBEL?")
    print("-" * 104)
    basis = 1.0 / (1.0 + CRV)
    print("  Kelly-Nullstelle = Basisrate = %.4f" % basis)
    fs, ts = neu["funding_fuenftel"], neu["turnover_fuenftel"]
    if not fs or not ts:
        print("  ⛔ keine Stufen gefunden")
        return 0
    best = basis + (max(fs) + max(ts)) / 100.0
    print("  BESTE erreichbare Quote mit N19-E-Stufen: %.4f" % best)
    print("     (Basisrate + bestes funding %+.2f + bestes turnover %+.2f)"
          % (max(fs), max(ts)))
    kelly = (best * (1 + CRV) - 1) / CRV
    print("  -> kelly = %+.5f · halbes Kelly = %+.5f" % (kelly, kelly / 2))
    print("     r_min = 0,00500 · r_max = 0,01250")
    print()
    if kelly <= 0:
        print("  ⛔⛔ SELBST IM BESTEN FALL IST KELLY NEGATIV.")
        print("     Mit ehrlich kalibrierten Stufen entsteht in KEINER")
        print("     Merkmalslage ein Hebel - auch nicht in der besten.")
    elif kelly / 2 < 0.005:
        print("  ⛔ KELLY IST POSITIV, ABER UNTER r_min - der Hebel waere")
        print("     auf die Untergrenze geklemmt und von der Bewertung")
        print("     unabhaengig. Das ist kein gesteuerter Hebel.")
    else:
        print("  ✔ Im besten Fall steuert die Quote - zu pruefen bleibt,")
        print("    wie oft diese Lage vorkommt.")
    print("\n" + "=" * 104)
    print("  ⚠️ FRAGE 1 (ist `q` dann kalibriert?) beantwortet dieses")
    print("     Werkzeug NICHT - dafuer ist `messe_bewertung_kalibrierung`")
    print("     mit den neuen Stufen zu fahren. Hier steht die BAUFRAGE:")
    print("     reicht die ehrliche Bewertung ueberhaupt fuer einen Hebel?")
    print("=" * 104)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
