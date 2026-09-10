# -*- coding: utf-8 -*-
"""V1 — KRITERIUM 4, richtig gemessen: der ASSET-ANTEIL (10.09.2026)

## Warum Kriterium 4 neu gemessen wird

Der Vierfachtest hat es mit einem **Signifikanztest auf der Laengs-Achse**
geprueft. Ergebnis: **untermaechtig bei ALLEN Kandidaten, auch bei der
Kontrolle** (2.292). Das ist ein Befund ueber die Anlage, nicht ueber die
Kandidaten - A9 (2.283) sagt, die Laengs-Achse loest erst ab 0,08 R auf,
und alle Kandidaten liegen bei 0,02 bis 0,05 R.

⚠️⚠️ **Aber Kriterium 4 ist auch falsch konstruiert.** Was es wissen
will, ist:

> Ist die Groesse eine ZEITPUNKT-Aussage oder eine ASSET-Eigenschaft?
> BTC hat jeden Tag einen grossen Volumenanteil, ein Altcoin jeden Tag
> einen kleinen. Eine Regel darauf sagt *„dieses Asset ist schlecht"*,
> nicht *„dieser Zeitpunkt ist schlecht"*.

**Dafuer gibt es seit dem 02.09. das richtige Mass - Methodik 2.101, die
STREUUNGSZERLEGUNG:**

    zwischen    Varianz der SYMBOLMITTEL       -> Asset-Eigenschaft
    innerhalb   mittlere Varianz je Symbol     -> Zeitpunkt-Aussage

    Asset-Anteil = zwischen / (zwischen + innerhalb)

⚠️⚠️⚠️ **Das ist BESCHREIBEND, kein Signifikanztest - und deshalb von A9
GAR NICHT betroffen.** Es hat keine Trennschaerfe und braucht keine.

## ⚠️ Die Skala muss geeicht werden, und beide Arme auf DERSELBEN Menge

„69,8 %" ist ohne Massstab bedeutungslos. Zwei Kontrollen spannen die
Skala auf:

    FEST     je Symbol ein konstanter Wert   -> reine Asset-Eigenschaft
    ZUFALL   jeden Tag neu gewuerfelt        -> reine Zeitpunkt-Aussage

⚠️⚠️ **Beide auf der Menge des Kandidaten**, nicht auf einer eigenen. An
genau dieser Stelle ist die erste Fassung von 2.101 gescheitert: sie
stellte 578 Symbole gegen 65. **Der Asset-Anteil haengt an der Zahl der
Symbole** - bei wenigen Symbolen ist der Rang grob, und grobe Raenge
springen staerker, was eine Groesse ZEITPUNKTARTIGER aussehen laesst,
als sie ist.

## ⚠️⚠️ UND WENN EIN KANDIDAT SCHEITERT, WIRD DIE LOESUNG MITGEMESSEN

Nutzervorgabe, mehrfach wiederholt:

> *„Beitraege fallen nicht ohne Grund, und wenn doch, dann muessen wir
> eine Loesung suchen - das System und die Machbarkeit haengen davon ab."*

Beim Volumenanteil hat genau das funktioniert: die **rohe** Form war zu
73 % eine Asset-Eigenschaft und fiel; die **relative** Form (Anteil gegen
die eigenen 20 Tage) kam auf **1 %** und trug. Dieselbe Umformung wird
hier fuer JEDEN Kandidaten mitgemessen:

    roh        die Kennzahl, wie sie heute gebaut wird
    relativ    dieselbe Kennzahl gegen ihren eigenen 20-Tage-Schnitt

**Ein hoher Asset-Anteil ist damit kein Urteil, sondern eine Diagnose.**

⚠️⚠️⚠️ **NACHTRAG NACH DER GEGENPRUEFUNG:** die relative Form ist als
NACHWEIS wertlos. Auf Kunstdaten mit eingestelltem Asset-Anteil:

    gebaut 10 %  ->  roh  7,6 %  ->  relativ 0,0 %
    gebaut 50 %  ->  roh 47,1 %  ->  relativ 0,0 %
    gebaut 90 %  ->  roh 88,9 %  ->  relativ 0,0 %

Die Standardisierung entfernt das Symbolmittel **per Konstruktion**. Sie
bleibt ein moeglicher UMBAU - aber dann muss die WIRKUNG der umgeformten
Groesse neu gemessen werden. Beim Volumenanteil war genau das der Punkt:
relative Form 1,4 % Asset-Anteil **UND** +0,0231 R Wirkung.

## Wer gemessen wird - und warum auch der BESTAND

    vola, schnitt50, amihud, schnitt     die Kandidaten
    funding, turnover, oi_aenderung      ⚠️ der BESTAND
    zufall                               Kontrolle

⚠️ Der Bestand muss mit. `turnover` ist zu **52 %** eine
Asset-Eigenschaft (F-170) - ein registrierter, tragender Beitrag sagt
zur Haelfte, WELCHES Asset. Einen Kandidaten an einer Huerde scheitern
zu lassen, die die laufenden Beitraege nie nehmen mussten, waere
zweierlei Mass (N-2, 2.294).

## Die Vorhersage, VOR dem Lauf (Methodik 2.80)

    FEST        ~ 96 %,  ZUFALL ~ 0 %   - sonst ist die Skala kaputt
    turnover    ~ 52 %   (F-170 reproduziert -> R-R11 erfuellt)
    schnitt     hoch in der rohen Form - er ist ein Abstand zum eigenen
                Schnitt, also schon relativ; die Umformung sollte wenig
                aendern
    amihud      hoch - Liquiditaet ist eine Asset-Eigenschaft
    relativ     bei allen NIEDRIGER als roh

⚠️ Faellt `turnover` nicht auf ~52 %, ist die Messung nicht reproduziert
und der ganze Lauf gilt nicht.

    python n103_v1_asset_anteil.py
"""
from __future__ import annotations

import sys
import time

import numpy as np

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import messe_eigenschaft_beitrag as B                         # noqa: E402
import messe_kandidaten_als_regel as K                        # noqa: E402
import messmenge                                              # noqa: E402
from messe_alle_kandidaten import HORIZONT, zusatzquellen     # noqa: E402
from messe_volumenanteil import zerlege                       # noqa: E402

KANDIDATEN = ("vola", "schnitt50", "amihud", "schnitt",
              "funding", "turnover", "oi_aenderung", "zufall")
FENSTER = 20             # fuer die relative Form
SAAT = 20260910


def als_tageskarte(je_tag: dict) -> dict:
    """`{tag: [zeilen]}` -> `{tag: {sym: kennzahl}}` fuer `zerlege`."""
    return {t: {x["sym"]: float(x["kennzahl"]) for x in z}
            for t, z in je_tag.items() if len(z) >= 12}


def relativ(karte: dict) -> dict:
    """Jede Kennzahl gegen ihren eigenen nachlaufenden 20-Tage-Schnitt.

    ⚠️ NUR VERGANGENHEIT - der heutige Wert geht NICHT in seinen eigenen
    Massstab ein. Sonst waere die Umformung ein Lookahead und wuerde die
    Streuung kuenstlich senken, also genau das Ergebnis erzeugen, das
    gesucht wird.

    ⚠️⚠️ Bei Kennzahlen, die um null schwanken, ist ein VERHAELTNIS
    unbrauchbar (Division durch fast null). Deshalb die DIFFERENZ zum
    eigenen Schnitt, in Einheiten der eigenen Streuung - das ist
    massstabsfrei und fuer jedes Vorzeichen definiert.

    ⚠️ Der erste Entwurf hat die Fensterlaenge per Prozent-Operator in
    den Docstring formatiert. Damit ist es kein Docstring mehr, sondern
    ein Ausdruck - die Funktion haette keine Dokumentation gehabt. Die
    Laenge steht deshalb ausgeschrieben im Text.
    """
    je_sym: dict = {}
    for tag in sorted(karte):
        for s, w in karte[tag].items():
            je_sym.setdefault(s, []).append((tag, w))
    aus: dict = {}
    for s, folge in je_sym.items():
        x = np.array([w for _t, w in folge], float)
        for i in range(FENSTER + 5, len(x)):
            f = x[i - FENSTER:i]
            sd = float(np.std(f))
            if sd <= 1e-12:
                continue
            aus.setdefault(folge[i][0], {})[s] = float((x[i] - f.mean()) / sd)
    return {t: v for t, v in aus.items() if len(v) >= 12}


def kontrollen(karte: dict, rng) -> tuple:
    """FEST und ZUFALL auf DERSELBEN Menge - die geeichte Skala.

    ⚠️⚠️ Auf derselben Menge, nicht auf einer eigenen. Der Asset-Anteil
    haengt an der Zahl der Symbole (2.101): bei wenigen ist der Rang
    grob, und grobe Raenge springen staerker.
    """
    syms = sorted({s for v in karte.values() for s in v})
    fest_wert = {s: float(rng.normal()) for s in syms}
    fest = {t: {s: fest_wert[s] for s in v} for t, v in karte.items()}
    zuf = {t: {s: float(rng.normal()) for s in v}
           for t, v in karte.items()}
    return fest, zuf


def main() -> int:
    t0 = time.time()
    reihen = B.lade()
    zus = zusatzquellen()

    print("=" * 104)
    print("V1 — KRITERIUM 4, richtig gemessen: der ASSET-ANTEIL "
          "(Methodik 2.101)")
    print("=" * 104)
    print("  %s" % messmenge.zeile())
    print("  ⚠️ BESCHREIBEND, kein Signifikanztest - deshalb von A9 "
          "(Aufloesung) nicht betroffen.")
    print("  ⚠️⚠️ Beide Kontrollen auf der Menge DES KANDIDATEN - der "
          "Asset-Anteil haengt an")
    print("     der Symbolzahl (2.101, erste Fassung daran gescheitert).")
    print("  ⚠️ Und die RELATIVE Form laeuft mit: sie hat den "
          "Volumenanteil von 73 %% auf 1 %% gebracht.")

    erg = {}
    for kand in KANDIDATEN:
        try:
            je = K.baue(reihen, kand, zus.get(kand), horizont=HORIZONT)
        except Exception as exc:                              # noqa: BLE001
            print("\n  %-14s -> %s" % (kand, str(exc)[:60]))
            continue
        karte = als_tageskarte(je)
        if not karte:
            print("\n  %-14s -> keine Tageskarte" % kand)
            continue
        rng = np.random.default_rng(SAAT)
        fest, zuf = kontrollen(karte, rng)

        print()
        print("  %s" % kand.upper())
        print("  %-26s  %12s  %10s  %10s  %s"
              % ("", "Asset-Anteil", "Autokorr.1", "Autokorr.20", "Symbole"))
        z_fest = zerlege(fest, "  Skala FEST (Asset)")
        z_zuf = zerlege(zuf, "  Skala ZUFALL (Zeitpunkt)")
        z_roh = zerlege(karte, "  roh")
        z_rel = zerlege(relativ(karte), "  relativ (%d Tage)" % FENSTER)
        erg[kand] = {"fest": z_fest, "zufall": z_zuf,
                     "roh": z_roh, "relativ": z_rel}

    # ---- Die Abnahme -----------------------------------------------------
    print()
    print("=" * 104)
    print("DIE ABNAHME")
    print("=" * 104)
    # 1) Ist die Skala geeicht?
    schief = []
    for kand, v in erg.items():
        f, z = v.get("fest"), v.get("zufall")
        if not f or not z:
            continue
        if f["anteil_asset"] < 0.85 or z["anteil_asset"] > 0.15:
            schief.append("%s (FEST %.0f %%, ZUFALL %.0f %%)"
                          % (kand, 100 * f["anteil_asset"],
                             100 * z["anteil_asset"]))
    if schief:
        print("  ⚠️⚠️⚠️ DIE SKALA IST NICHT GEEICHT bei: %s"
              % "; ".join(schief))
        print("     Ohne geeichte Skala ist jede Prozentzahl darunter "
              "bedeutungslos.")
    else:
        print("  ✔ Die Skala ist bei allen geeicht (FEST > 85 %, "
              "ZUFALL < 15 %).")

    # 2) R-R11: reproduziert `turnover` seine 52 %?
    tv = erg.get("turnover", {}).get("roh")
    if tv:
        ok = 0.40 <= tv["anteil_asset"] <= 0.65
        print("  %s R-R11: `turnover` roh %.1f %% gegen registrierte "
              "52 %% (F-170)%s"
              % ("✔" if ok else "⚠️⚠️", 100 * tv["anteil_asset"],
                 "" if ok else " - NICHT reproduziert, der Lauf gilt nicht"))

    # 3) Die Tafel
    print()
    print("     %-14s %10s %10s %12s  %s"
          % ("Kandidat", "roh", "relativ", "Verbesserung", "Lesart"))
    for kand in KANDIDATEN:
        v = erg.get(kand)
        if not v or not v.get("roh"):
            continue
        r = 100 * v["roh"]["anteil_asset"]
        rel = (100 * v["relativ"]["anteil_asset"]
               if v.get("relativ") else float("nan"))
        besser = r - rel if np.isfinite(rel) else float("nan")
        lesart = ("⚠️ ueberwiegend ASSET" if r > 50 else
                  ("gemischt" if r > 20 else "✔ ZEITPUNKT"))
        # ⚠️⚠️⚠️ HIER STAND "-> ✔ die relative Form loest es". DAS WAR
        # FALSCH, und meine eigene Gegenpruefung hat es widerlegt:
        #
        #     gebaut 10 % Asset -> roh  7,6 % -> relativ 0,0 %
        #     gebaut 50 % Asset -> roh 47,1 % -> relativ 0,0 %
        #     gebaut 90 % Asset -> roh 88,9 % -> relativ 0,0 %
        #
        # Die Standardisierung `(x - Schnitt) / Streuung` je Symbol
        # entfernt das Symbolmittel PER KONSTRUKTION - also genau die
        # "zwischen"-Varianz. Sie senkt JEDE Groesse auf null und beweist
        # damit NICHTS.
        #
        # ⚠️ Sie bleibt ein moeglicher UMBAU - aber der Nachweis muss dann
        # ueber die WIRKUNG der umgeformten Groesse laufen, nicht ueber
        # ihren Asset-Anteil. Genau so war es beim Volumenanteil: relative
        # Form 1,4 % Asset-Anteil UND +0,0231 R Wirkung. Beides.
        if np.isfinite(rel) and rel <= 20 < r:
            lesart += " · relativ ~0 % ⚠️ ARITHMETIK, kein Nachweis"
        print("     %-14s %9.1f %% %9.1f %% %11.1f  %s"
              % (kand, r, rel, besser, lesart))
    print()
    print("  ⚠️ Ein hoher Asset-Anteil ist eine DIAGNOSE, kein Urteil.")
    print("  ⚠️⚠️⚠️ ABER DIE RELATIVE SPALTE IST KEIN NACHWEIS. "
          "Gegengeprueft auf Kunstdaten:")
    print("     gebaut 10/50/90 %% Asset -> relativ 0,0 / 0,0 / 0,0 %%. "
          "Die Standardisierung")
    print("     entfernt das Symbolmittel PER KONSTRUKTION. Wer eine "
          "Groesse so umbaut, muss")
    print("     ihre WIRKUNG neu messen - der Asset-Anteil sagt danach "
          "nichts mehr.")
    print("  ⚠️⚠️ Und der BESTAND steht mit in der Tafel: wer einen "
          "Kandidaten an einer Huerde")
    print("     scheitern laesst, die `funding` und `turnover` nie nehmen "
          "mussten, misst zweierlei.")
    print("  Dauer %.1f Minuten" % ((time.time() - t0) / 60.0))
    return 0


if __name__ == "__main__":
    sys.exit(main())
