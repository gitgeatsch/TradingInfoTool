# -*- coding: utf-8 -*-
"""S5 - WIE VIELE WERTE WECHSELN DAS FUENFTEL, wenn der Nenner wechselt?

⚠️⚠️⚠️ WARUM DIESE MESSUNG PFLICHT IST (CLAUDE.md, *„Die Grundgesamtheit
ist keine Stellschraube"*):

    Ein Rang ist ein Perzentil. Wer die Menge aendert, ueber die gerangt
    wird, aendert JEDEN Wert darin - auch die, die er gar nicht anfassen
    wollte.

Und die Regel dazu: *„Wer sie aendert, MISST die Wirkung: wie viele Werte
wechseln das Fuenftel?"* - nicht schaetzt, nicht begruendet. Diese Datei
beantwortet genau das fuer den geplanten Nennerwechsel.

## Der Aufbau

Die Raenge kommen aus `phase4_c_trefferquote_abdeckung.baue_raenge` -
IMPORTIERT, nicht nachgebaut. Dieselben Anker, dasselbe Fenster (ab 2023),
dieselbe Naeherungsmenge wie in 2.520.

    ALT   turnover-Fuenftel auf `splycur`   (Gesamtausgabe, heutiger Betrieb)
    NEU   turnover-Fuenftel auf der Naeherung (freier Umlauf, 366 Symbole)

## ⚠️⚠️ ZWEI ZAHLEN, DIE NICHT VERMISCHT WERDEN DUERFEN

    WECHSEL    Symbol-Tage, die in BEIDEN Nennern ein Fuenftel haben und
               ein ANDERES bekommen. Das ist der Preis.
    NEU DAZU   Symbol-Tage, die heute GAR KEIN Fuenftel haben und eines
               bekommen. Das ist der Gewinn - und es ist KEIN Wechsel.

Wer beides zusammenzaehlt, macht aus dem Gewinn einen Preis.

## Bezug

Am 21.09. wurde dieselbe Frage fuer `umschlag_frei` (375 Symbole, 365 Tage)
beantwortet: 76,7 % der Symbol-Tage wechselten, 10.946 nach unten gegen 348
nach oben. Diese Datei rechnet es fuer die NAEHERUNG (366 Symbole, Fenster
ab 2023) - eine andere Menge, und deshalb eine eigene Zahl.

⚠️ NUR LESEND.
"""
import collections
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
os.chdir("D:/CLAUDE_Projects/SoftwareProjekte/TradingInfoTool")
sys.path.insert(0, "D:/CLAUDE_Projects/SoftwareProjekte/TradingInfoTool")

import messnorm_auswahl as MA                                # noqa: E402
from messe_beitrag_auf_auswahl import _auswahl_maske         # noqa: E402
import phase4_c_trefferquote_abdeckung as TA                 # noqa: E402


def _arg(a, f, v):
    return a[a.index(f) + 1] if f in a else v


def zaehle(je, r_alt, r_neu, maske_anteil=None, mom=None):
    """-> (gemeinsam, gewechselt, runter, hoch, neu_dazu, je_symbol)."""
    gemeinsam = gewechselt = runter = hoch = neu_dazu = 0
    je_sym = collections.defaultdict(lambda: [0, 0])   # [gemeinsam, Wechsel]
    verschub = collections.Counter()
    for tag, zeilen in je.items():
        ta, tn = r_alt.get(tag, {}), r_neu.get(tag, {})
        if maske_anteil is not None and maske_anteil < 1.0:
            if len(zeilen) < 12:
                continue
            m = _auswahl_maske(zeilen, (mom or {}).get(tag) or {},
                               maske_anteil, None)
            if m is None or not m.any():
                continue
            zeilen = [x for x, ok in zip(zeilen, m) if ok]
        for x in zeilen:
            s = x["sym"]
            a, n = ta.get(s), tn.get(s)
            if n is None:
                continue
            if a is None:
                neu_dazu += 1
                continue
            gemeinsam += 1
            je_sym[s][0] += 1
            if a != n:
                gewechselt += 1
                je_sym[s][1] += 1
                verschub[n - a] += 1
                if n > a:
                    runter += 1        # hoeheres Fuenftel = hoeherer Umschlag
                else:
                    hoch += 1
    return gemeinsam, gewechselt, runter, hoch, neu_dazu, je_sym, verschub


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    H = int(_arg(args, "--horizont", "20"))

    print("=" * 92)
    print("S5 - FUENFTELWECHSEL BEIM NENNERWECHSEL  (splycur -> Naeherung, "
          "H%d)" % H)
    print("=" * 92)
    je, r_neu, r_alt, r_fu, reihen, mom = TA.baue_raenge(H)
    print("  %d Ankertage, Fenster ab %s" % (len(je), TA.NK.AB))
    print()

    zulaessig = MA.zulaessige_mengen(je, mom, horizont=H)
    print("  %-10s %10s %12s %10s %10s %14s"
          % ("Menge", "gemeinsam", "gewechselt", "hoeher", "niedriger",
             "NEU dazu"))
    print("  " + "-" * 74)
    for name in ("10%", "20%", "50%", "frei"):
        if name not in zulaessig and name != "frei":
            continue
        g, w, r, h, nd, js, vs = zaehle(
            je, r_alt, r_neu, MA.MENGEN[name], mom)
        if not g:
            print("  %-10s %10s" % (name, "keine gemeinsamen"))
            continue
        print("  %-10s %10d %9d %3.0f%% %10d %10d %14d"
              % (name, g, w, 100.0 * w / g, r, h, nd))
    print("  " + "-" * 74)
    print("  \u26a0 `gewechselt` bezieht sich auf die GEMEINSAMEN "
          "Symbol-Tage,")
    print("     `NEU dazu` sind Tage OHNE altes Fuenftel - das ist der "
          "Gewinn, kein Preis.")
    print()

    g, w, r, h, nd, js, vs = zaehle(je, r_alt, r_neu)
    print("  AUF DER FREIEN MENGE, im Detail")
    print("  " + "-" * 74)
    print("  gemeinsame Symbol-Tage      %8d" % g)
    print("  davon anderes Fuenftel      %8d  (%.1f %%)"
          % (w, 100.0 * w / max(1, g)))
    print("     in ein HOEHERES Fuenftel %8d" % r)
    print("     in ein NIEDRIGERES       %8d" % h)
    print("  Symbol-Tage NEU mit Wert    %8d" % nd)
    print()
    print("  Verschub in Fuenfteln:", "  ".join(
        "%+d: %d" % (k, vs[k]) for k in sorted(vs)))
    print()
    # ---- ⚠⚠ DIE KONTROLLE: GROESSE oder MENGE? ------------------
    #
    # Die Richtung ist ueberwiegend NACH UNTEN. Das kann zweierlei heissen:
    # der andere NENNER verschiebt die Werte, oder die groessere
    # GRUNDGESAMTHEIT drueckt die alten 66 nach unten. Ohne diese Kontrolle
    # waere beides nicht zu trennen - und am 21.09. war genau das die
    # Zerlegung (25,6 % Groesse gegen 76,7 % gesamt).
    #
    # Dritter Arm: die NAEHERUNGSwerte, aber gerangt NUR ueber die Symbole,
    # die auch `splycur` fuehrt. Gleiche Menge, anderer Nenner.
    r_gem = {}
    for tag, zeilen in je.items():
        ta = r_alt.get(tag) or {}
        paare = [(x["sym"], x["kennzahl"])
                 for x in zeilen if x["sym"] in ta]
        if len(paare) >= 12:
            r_gem[tag] = TA.fuenftel(paare)
    g2, w2, r2, h2, _nd2, _js2, vs2 = zaehle(je, r_alt, r_gem)
    print("  KONTROLLE - nur die GROESSE (gleiche Symbolmenge):")
    print("  " + "-" * 74)
    print("  gemeinsame Symbol-Tage      %8d" % g2)
    print("  davon anderes Fuenftel      %8d  (%.1f %%)   hoeher %d, "
          "niedriger %d" % (w2, 100.0 * w2 / max(1, g2), r2, h2))
    # ⚠ MEINE ERSTE FASSUNG SCHRIEB HIER *,der Unterschied ist die
    # MENGE`* - das war falsch gelesen. Die ANZAHL kommt fast ganz von der
    # GROESSE; die MENGE aendert kaum die Zahl, aber sie kippt die
    # RICHTUNG. Beides gehoert nebeneinander, sonst deutet man 3,7 Punkte
    # als den ganzen Effekt.
    print("  ➤ ANZAHL   GROESSE %.1f %%  →  GESAMT %.1f %%   "
          "(die Menge legt nur %.1f Punkte zu)"
          % (100.0 * w2 / max(1, g2), 100.0 * w / max(1, g),
             100.0 * w / max(1, g) - 100.0 * w2 / max(1, g2)))
    print("  ➤ RICHTUNG GROESSE %d hoeher / %d niedriger (%.2f:1)  "
          "→  GESAMT %d / %d (%.2f:1)"
          % (r2, h2, h2 / max(1, r2), r, h, h / max(1, r)))
    print("     ⚠ DIE MENGE AENDERT NICHT DIE ZAHL, SIE KIPPT DIE "
          "RICHTUNG - die alten Symbole")
    print("       rutschen im groesseren Feld systematisch nach unten.")
    print()

    # ---- ⚠⚠ KONTROLLEN: zaehlt der Zaehler ueberhaupt richtig? ----
    #
    # Ein Zaehler, der nie geprueft wurde, kann Artefakte zaehlen. Zwei
    # Proben, beide mit bekanntem Sollwert:
    #
    #   NULL      ALT gegen ALT      -> muss EXAKT 0 % sein
    #   POSITIV   ALT gegen GEMISCHT -> muss rund 80 % sein, denn ein
    #             zufaelliges Fuenftel trifft in einem von fuenf Faellen
    #
    # Trifft die Positivkontrolle die 80 % nicht, misst der Zaehler etwas
    # anderes als "Anteil geaenderter Fuenftel".
    import numpy as _np
    _r = _np.random.default_rng(20260922)
    g0, w0, *_ = zaehle(je, r_alt, r_alt)
    r_mix = {}
    for tag, d in r_neu.items():
        ks = list(d)
        r_mix[tag] = dict(zip(ks, _r.permutation([d[k] for k in ks])))
    g1, w1, *_ = zaehle(je, r_alt, r_mix)
    print("  KONTROLLEN des Zaehlers")
    print("  " + "-" * 74)
    print("  NULL     ALT gegen ALT        %8d von %d = %5.2f %%   "
          "(Sollwert 0)" % (w0, g0, 100.0 * w0 / max(1, g0)))
    print("  POSITIV  ALT gegen GEMISCHT   %8d von %d = %5.2f %%   "
          "(Sollwert rund 80)" % (w1, g1, 100.0 * w1 / max(1, g1)))
    _ok = (w0 == 0) and 74.0 <= 100.0 * w1 / max(1, g1) <= 86.0
    print("  %s der Zaehler misst, was er soll"
          % ("✔" if _ok else "⛔ FEHL -"))
    # ⚠⚠ UND DAS IST DIE EIGENTLICHE LESART: die Positivkontrolle
    # gibt den Wert fuer VOELLIG UNABHAENGIGE Raenge. Wie weit liegt der
    # gemessene Wechsel davon entfernt? Nahe null hiesse "fast dieselbe
    # Ordnung", nahe der Zufallsquote hiesse "praktisch keine gemeinsame
    # Ordnung mehr". Ohne diesen Bezug sagt "69 %" wenig.
    _zuf = 100.0 * w1 / max(1, g1)
    _ist = 100.0 * w / max(1, g)
    print("  ➤ EINORDNUNG: gemessen %.1f %%, bei ZUFALL %.1f %%, bei "
          "GLEICHHEIT 0 %%" % (_ist, _zuf))
    print("     → von der alten Ordnung bleiben noch %.0f Prozent "
          "uebrig." % (100.0 * (_zuf - _ist) / max(1e-9, _zuf)))
    print()

    ganz = sorted((n / max(1, gg), s, gg) for s, (gg, n) in js.items()
                  if gg >= 30)
    print("  Symbole mit der HOECHSTEN Wechselquote (mind. 30 gem. Tage):")
    for q, s, gg in ganz[-8:][::-1]:
        print("     %-10s %5.1f %%  (%d Tage)" % (s, 100 * q, gg))
    print("  und mit der niedrigsten:")
    for q, s, gg in ganz[:4]:
        print("     %-10s %5.1f %%  (%d Tage)" % (s, 100 * q, gg))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
