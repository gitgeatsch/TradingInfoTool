# -*- coding: utf-8 -*-
"""K-1c (Hebel) — Gilt der Beleg auch für `hebel x einstieg`? (09.09.2026)

## Warum das eine EIGENE Messung ist

Bei `hebel` **beendet der Stop den Trade**. Damit ist `bewegung_r`
(barrierenfrei) die falsche Zielgroesse - die Bewegung nach dem Stop
gehoert einem nicht mehr. `messnorm.ZIELGROESSE_JE_LAGE` verlangt dort
`barriere`: **Ziel vor Stop**.

⚠️⚠️ Bis zum 09.09. war die Lage nur ein Etikett - `pruefe_auswahl` hatte
`bewegung_r` fest verdrahtet. Eine Hebelmessung haette Spot-Bewegung
gemessen und "Hebel" daraufgeschrieben.

## Die drei Bausteine, die dafuer noetig waren

    1. `ZIELGROESSEN` bekam `statistik` je Zielgroesse
    2. `je_tag_wirkung` bekam die MITTEL-Variante
    3. Die Barriere auf PRODUKTIONSGEOMETRIE - hier

⚠️ Zu 2: `je_tag_wirkung` rechnet `median(frei) - median(alle)`. Der
Ausgang ist BINAER (Ziel vor Stop = 0/1); der Median ist dann 0 oder 1,
und die Differenz fast immer exakt null - **die Statistik waere
entartet**. Eine Trefferquote ist ein MITTEL.

⚠️ Zu 3: die vorhandene `messe_sentiment_je_horizont.barriere` rechnet
mit `STOP_ATR = 2,5`. Die Produktion rechnet anders:

    stop = min(25 % Kurs, max(5 % Kurs, 0,75 x ATR))     GRENZEN
    ziel = Kurs + 2,0 x stop                              crv

Wer die 2,5-Variante nimmt, misst ein anderes System.

## ⚠️⚠️ Was diese Messung NICHT kann - vorher gesagt

`messnorm.ZIELGROESSEN["barriere"]` sagt es selbst:

> *blind fuer 'wieviel ist zu holen' - der Erwartungswert ist per
> Konstruktion null. Zulaessig als VERGLEICH zweier Arme unter derselben
> Zielregel.*

Gemessen wird also **nicht** "wieviel Potential steckt drin", sondern
**"verschiebt der Beitrag die Trefferquote"**. Das ist eine zulaessige,
aber engere Frage.

⚠️ Und: Anker, bei denen im Fenster WEDER Ziel noch Stop faellt, fallen
heraus. Das ist eine Auswahl, und sie ist verwandt mit den 79 %
"Einstieg nie erreicht" aus K-6. Der Anteil wird ausgewiesen.

⚠️ `hebel` hat in der Produktion NULL Signale (3.513 spot, 11
absicherung, 0 hebel - gemessen 06.09.). Jede Hebel-Aussage traegt
deshalb `simuliert=True`.

## ⚠️ NEUTRAL, ohne Wirtschaftlichkeit

Nutzervorgabe 09.09.: *"fuer Strategie und Bewertung neutral ohne
Wirtschaftlichkeit"*. `barriere` ist Ziel vor Stop - **keine Gebuehr,
kein Breakeven**. Regel 2.

## Die Vorhersage, VOR dem Lauf (Methodik 2.80)

    Erwartung   die Beitraege verschieben die Trefferquote SCHWACH oder
                gar nicht: das Barrierensystem hat brutto Erwartungswert
                NULL, und eine Rangordnung im Querschnitt aendert daran
                nur, wenn sie die DRIFT trifft
    Gegenthese  sie verschieben sie messbar - dann waere der Hebel
                begruendbar steuerbar

⚠️ Ein Nullbefund ist hier die Regel, kein Ausreisser.

    python k1c_hebel_barriere.py
"""
from __future__ import annotations

import sys
import time

import numpy as np

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import messe_eigenschaft_beitrag as B                        # noqa: E402
import messe_kandidaten_als_regel as K                       # noqa: E402
import messmenge                                              # noqa: E402
import messnorm as N                                          # noqa: E402
import messnorm_auswahl as MA                                # noqa: E402
from agent.entscheidungsrechnung import GRENZEN              # noqa: E402
from messe_alle_kandidaten import HORIZONT, zusatzquellen    # noqa: E402
from messe_beitrag_auf_auswahl import momentum250            # noqa: E402

KANDIDATEN = ("funding", "turnover", "oi_aenderung", "schnitt", "zufall")


def barriere_je_reihe(reihe, H: int):
    """Ziel vor Stop, auf der PRODUKTIONSGEOMETRIE -> {tag: 1.0/0.0}.

    ⚠️ Genau die Geometrie, die `entscheidungsrechnung` baut - sonst misst
    der Test etwas anderes als das, was die App vorschlaegt.
    """
    tage = [x[0] for x in reihe]
    c = np.array([x[1] for x in reihe], float)
    h = np.array([x[2] for x in reihe], float)
    t = np.array([x[3] for x in reihe], float)
    atr = B.spanne(h, t, c, B.SCHWANKUNG)
    aus = {}
    for i in range(len(c) - 1):
        if not np.isfinite(atr[i]) or c[i] <= 0:
            continue
        stop_abstand = min(GRENZEN["stop_max_relativ"] * c[i],
                           max(GRENZEN["stop_min_relativ"] * c[i],
                               GRENZEN["stop_min_atr"] * atr[i]))
        if stop_abstand <= 0:
            continue
        stop = c[i] - stop_abstand
        ziel = c[i] + GRENZEN["crv"] * stop_abstand
        for j in range(i + 1, min(i + 1 + H, len(c))):
            if t[j] <= stop:
                aus[tage[i]] = 0.0
                break
            if h[j] >= ziel:
                aus[tage[i]] = 1.0
                break
        # ⚠️ Faellt keines im Fenster, bleibt der Anker AUSSEN - und das
        # wird unten als Anteil ausgewiesen, nicht verschwiegen.
    return aus


def barriere_je_tag(je_tag: dict, reihen: dict, H: int):
    """Ersetzt `in_r` durch den Barrierenausgang. -> (je_tag, Anteil geloest)"""
    je_sym = {s: barriere_je_reihe(v, H) for s, v in reihen.items()}
    neu, drin, gesamt = {}, 0, 0
    for tag, zeilen in je_tag.items():
        z = []
        for x in zeilen:
            gesamt += 1
            b = (je_sym.get(x["sym"]) or {}).get(tag)
            if b is None:
                continue
            drin += 1
            z.append({"sym": x["sym"], "kennzahl": x["kennzahl"],
                      "in_r": float(b)})
        if len(z) >= 12:
            neu[tag] = z
    return neu, (drin / gesamt if gesamt else 0.0)


def kurz(u: str) -> str:
    return u.split(" (")[0].split(" - ")[0][:26]


def main() -> int:
    t0 = time.time()
    reihen = B.lade()
    mom = momentum250(reihen)
    zus = zusatzquellen()
    # ⚠️ `simuliert=True` ist Pflicht: NULL Hebelsignale in der Produktion.
    lage = N.Lage(instrument="hebel", strategie="einstieg", simuliert=True)

    print("=" * 108)
    print("K-1c (Hebel) — gilt der Beleg fuer `hebel x einstieg`?")
    print("=" * 108)
    print("  %s" % N.standardzeile())
    print("  %s" % messmenge.zeile())
    print("  Lage: %s · Zielgroesse: %s · Statistik: %s"
          % (lage, N.ZIELGROESSE_JE_LAGE[("hebel", "einstieg")],
             N.ZIELGROESSEN["barriere"]["statistik"]))
    print("  Geometrie: stop = min(%.0f %% , max(%.0f %% , %.2f x ATR)) · "
          "ziel = Kurs + %.1f x stop"
          % (100 * GRENZEN["stop_max_relativ"],
             100 * GRENZEN["stop_min_relativ"], GRENZEN["stop_min_atr"],
             GRENZEN["crv"]))
    print("  ⚠️ `barriere` ist BLIND fuer 'wieviel ist zu holen' - "
          "gemessen wird, ob der")
    print("     Beitrag die TREFFERQUOTE verschiebt. Neutral, ohne "
          "Gebuehren (Regel 2).")
    print()
    print("  %-14s %9s %20s %9s %8s %7s  %s"
          % ("Kandidat", "Wirkung", "Band", "Bezug", "Tage", "Bloecke",
             "Urteil"))

    erg, anteil = {}, None
    for kand in KANDIDATEN:
        try:
            je0 = K.baue(reihen, kand, zus.get(kand), horizont=HORIZONT)
        except Exception as exc:                             # noqa: BLE001
            print("  %-14s -> %s" % (kand, str(exc)[:60]))
            continue
        je, anteil = barriere_je_tag(je0, reihen, HORIZONT)
        if not je:
            print("  %-14s -> leere Welt nach der Umrechnung" % kand)
            continue
        try:
            b = MA.pruefe_auswahl(
                kand, je, mom, lage=lage, menge="frei",
                rng=np.random.default_rng(20260909), horizont=HORIZONT,
                hypothese="K-1c Hebel", verwendung="Beitrag",
                zielgroesse="barriere")
        except Exception as exc:                             # noqa: BLE001
            print("  %-14s -> %s" % (kand, str(exc)[:70]))
            continue
        erg[kand] = b
        print("  %-14s %+9.4f [%+.4f..%+.4f] %+9.4f %8d %7d  %s"
              % (kand, b.wirkung, b.unten, b.oben, b.bezugswert,
                 b.n_tage, b.n_bloecke, kurz(b.urteil)), flush=True)

    # ---- Urteil ---------------------------------------------------------
    print()
    print("=" * 108)
    print("VERSCHIEBT EIN BEITRAG DIE TREFFERQUOTE?")
    print("=" * 108)
    if anteil is not None:
        print("  ⚠️ Im Fenster von %d Tagen geloest: %.1f %% der Anker - "
              "die uebrigen fielen heraus." % (HORIZONT, 100 * anteil))
        print("     Das ist eine AUSWAHL und verwandt mit den 79 % "
              "'Einstieg nie erreicht' (K-6).")
    kein = [k for k, b in erg.items()
            if b.urteil.upper().startswith("KEIN BEFUND")]
    if kein:
        print("  ⚠️⚠️ KEIN BEFUND bei: %s - die Anlage entscheidet dort "
              "nichts." % ", ".join(kein))
    zf = erg.get("zufall")
    if zf is not None:
        print("  Kontrolle `zufall`: %+.4f · %s"
              % (zf.wirkung, kurz(zf.urteil)))
    traeger = [k for k, b in erg.items()
               if k != "zufall" and b.traegt
               and not b.urteil.upper().startswith("KEIN BEFUND")]
    print()
    if traeger:
        print("  ✔ Verschieben die Trefferquote: %s" % ", ".join(traeger))
        print("     ⚠️ Das heisst NICHT 'mehr Potential' - `barriere` ist "
              "dafuer blind.")
    else:
        print("  ⚠️ KEIN Beitrag verschiebt die Trefferquote messbar.")
        print("     Das war die VORHERGESAGTE Erwartung: das "
              "Barrierensystem hat brutto")
        print("     Erwartungswert NULL, und ein Querschnittsrang aendert "
              "daran nur,")
        print("     wenn er die DRIFT trifft.")
    print()
    print("  ⚠️ `hebel` hat in der Produktion NULL Signale - jede Aussage "
          "hier ist SIMULIERT.")
    print("  Dauer %.1f Minuten" % ((time.time() - t0) / 60.0))
    return 0


if __name__ == "__main__":
    sys.exit(main())
