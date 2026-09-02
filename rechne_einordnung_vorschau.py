# -*- coding: utf-8 -*-
"""Wie liesse sich ein Signal EINORDNEN? Vier Varianten, vorgerechnet.
(02.09.2026)

## Der Anlass

Nutzerfrage nach dem Lesen einer echten Mail: *„Ich dachte, ich erhalte
auch Informationen zu den Bewertungen — warum war dieses Signal besser
als die anderen Assets? Rangfolge oder sonstige aussagekräftige
Zusammenfassung. Wo liegt der Coin besonders gut, welche Bewertungen und
Potential liegen gut, hoch, mittel, niedrig?"*

Die Mail sagt heute nichts davon. Sie nennt Merkmale und Fünftel, aber
**keine Einordnung der Gesamtbewertung** - und genau das verlangt das
uebergeordnete Ziel: *„wie viel ist hier zu holen, verglichen mit allem
anderen."*

## ⚠️ Was NICHT geht, und warum

Ein Rang des POTENTIALS ueber alle Werte ist heute unmoeglich: das
Potential haengt an Stop und CRV, die kommen aus dem Modellurteil. Eine
Rangfolge ueber 44 Werte braeuchte 44 Urteile je Lauf, neunmal am Tag -
genau der Deadloop, aus dem das System kommt.

## Die vier Varianten, die OHNE Modellurteil auskommen

    A  QUERSCHNITT   wo steht der Wert heute unter allen anderen?
    B  EIGENE LAGE   wie gut ist das fuer DIESEN Wert - gegen seine
                     eigene Geschichte?
    C  ZERLEGUNG     woher kommt die Zahl - welcher Beitrag traegt sie?
    D  DIE ANDEREN   was war heute besser, und warum kam es nicht durch?

⚠️ Alle vier stehen auf den BEITRAEGEN (Funding, Turnover, OI). Die sind
vor jedem Urteil bekannt und kosten nichts.

    python rechne_einordnung_vorschau.py [SYMBOL]
"""
import sys

import numpy as np

sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def punkte(e):
    """Die Beitragspunkte eines Werts - dieselbe Tabelle wie im Betrieb."""
    from agent import wahrscheinlichkeit as W
    summe, teile = 0.0, []
    for b in W.BEITRAEGE:
        if getattr(b, "zustand", "") != "traegt" or not getattr(b, "stufen", None):
            continue
        f = e.get(getattr(b, "merkmal", "") or "")
        if f is None:
            continue
        p = float(b.stufen[int(f)])
        summe += p
        teile.append((b.name, int(f), p))
    return summe, teile


def main():
    ziel = (sys.argv[1] if len(sys.argv) > 1 else "AVAX").upper()
    import config
    from agent import marktrang as MR

    wl = sorted({a.symbol.upper() for a in config.get_watchlist()
                 if getattr(a, "assetklasse", "") == "krypto"})
    print("Hole die Marktraenge fuer %d Werte ..." % len(wl), flush=True)
    r = MR.raenge(wl)

    bewertet = {}
    for s in wl:
        p, teile = punkte(r[s])
        if teile:
            bewertet[s] = (p, teile, r[s])
    if ziel not in bewertet:
        print("%s hat heute keinen einzigen Beitrag - keine Einordnung "
              "moeglich." % ziel)
        return 1

    reihe = sorted(bewertet.items(), key=lambda x: -x[1][0])
    platz = [s for s, _ in reihe].index(ziel) + 1
    n = len(reihe)
    p_ziel, teile_ziel, e_ziel = bewertet[ziel]
    werte = np.array([v[0] for v in bewertet.values()])

    print()
    print("=" * 78)
    print("VARIANTE A — DER QUERSCHNITT: wo steht %s heute?" % ziel)
    print("=" * 78)
    # ⚠️ Die Woerter sind an FUENFTEL gebunden, nicht frei gewaehlt - eine
    # Skala "hoch/mittel/niedrig" ohne Bezug waere eine erfundene Zahl.
    fuenftel = min(int((platz - 1) / n * 5), 4)
    wort = ["im besten Fuenftel", "im oberen Mittelfeld", "im Mittelfeld",
            "im unteren Mittelfeld", "im schlechtesten Fuenftel"][fuenftel]
    print("  Nach den gemessenen Beitraegen: Platz %d von %d — %s."
          % (platz, n, wort))
    print("  Punkte %+.2f · bester Wert %+.2f (%s) · schlechtester %+.2f (%s)"
          % (p_ziel, reihe[0][1][0], reihe[0][0],
             reihe[-1][1][0], reihe[-1][0]))
    print()
    print("  Die fuenf besten heute:")
    for s, (p, _t, _e) in reihe[:5]:
        print("     %-8s %+.2f%s" % (s, p, "   <- %s" % ziel if s == ziel else ""))

    print()
    print("=" * 78)
    print("VARIANTE B — DIE EIGENE LAGE: ist das fuer %s gut?" % ziel)
    print("=" * 78)
    # ⚠️ AUS DER ECHTEN HISTORIE, nicht geschaetzt. Der Funding-Rang je
    # Kalendertag wird nachgebildet - genau wie im Betrieb, nur rueckwaerts.
    import messe_funding_niveau as _F
    import messe_regel_wirksamkeit as _W
    roh = _F.lade_funding()
    je_tag = {}
    for sym, reihe in roh.items():
        for tag, wert in reihe.items():
            je_tag.setdefault(tag, {})[sym.upper()] = float(wert)
    basis = MR.messbasis("funding")
    verlauf = []
    for tag in sorted(je_tag)[-400:]:
        w = {s: v for s, v in je_tag[tag].items() if s in basis}
        if len(w) < 15 or ziel not in w:
            continue
        syms = sorted(w)
        rg = _W.rang([w[s] for s in syms])
        verlauf.append((tag, float(rg[syms.index(ziel)])))
    if not verlauf:
        print("  keine Historie fuer %s" % ziel)
    else:
        heute = verlauf[-1][1]
        besser = [t for t, x in verlauf if x < heute]
        print("  Funding-Rang von %s heute: %.2f (0 = guenstigstes Funding)"
              % (ziel, heute))
        print("  In den letzten %d Tagen mit Daten lag er %d mal guenstiger "
              "-> Perzentil %.0f" % (len(verlauf), len(besser),
                                     100 * len(besser) / len(verlauf)))
        if besser:
            print("  Zuletzt guenstiger am %s (vor %d Eintraegen)."
                  % (besser[-1], len(verlauf) - [t for t, _ in verlauf].index(besser[-1])))
        else:
            print("  ⚠️ So guenstig wie heute war es in diesem Fenster NIE.")
        print()
        print("  ⚠️ Das ist eine ZEITREIHE - sie sagt, ob der Wert fuer sich")
        print("     selbst guenstig liegt, nicht ob er besser ist als andere.")
        print("     Beides zusammen ist die eigentliche Auskunft.")

    print()
    print("=" * 78)
    print("VARIANTE C — DIE ZERLEGUNG: woher kommt die Zahl?")
    print("=" * 78)
    for name, f, p in sorted(teile_ziel, key=lambda x: -abs(x[2])):
        anteil = 100 * abs(p) / max(sum(abs(x[2]) for x in teile_ziel), 1e-9)
        print("  %-28s Fuenftel %d  %+.2f Punkte  (%.0f %% der Bewegung)"
              % (name, f, p, anteil))
    fehlt = [b.name for b in __import__("agent.wahrscheinlichkeit",
                                        fromlist=["x"]).BEITRAEGE
             if getattr(b, "zustand", "") == "traegt"
             and getattr(b, "stufen", None)
             and e_ziel.get(getattr(b, "merkmal", "") or "") is None]
    if fehlt:
        print("  ⚠️ ohne Wert und deshalb NICHT eingerechnet: %s"
              % ", ".join(fehlt))

    print()
    print("=" * 78)
    print("VARIANTE D — DIE ANDEREN: was war heute besser?")
    print("=" * 78)
    besser = [s for s, (p, _t, _e) in reihe if p > p_ziel]
    print("  %d Werte haben heute bessere Beitraege als %s:" % (len(besser), ziel))
    print("     %s" % (", ".join(besser) if besser else "keiner"))
    print()
    print("  ⚠️ Was daraus eine ANTWORT machen wuerde: der Grund, warum sie")
    print("     nicht empfohlen wurden. Der steht im Trichter (Cooldown,")
    print("     Auswahl, Anlass) und geht seit dem 02.09. ins Log - er ist")
    print("     also beschaffbar, aber noch nicht in der Mail.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
