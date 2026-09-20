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

## ⚠️⚠️⚠️ DIE MENGE ENTSCHEIDET HIER DAS URTEIL - GEMESSEN 20.09.2026

Der Lauf stand seit dem 09.09. fest auf `menge='frei'`. Das ist ein
Verstoss gegen **F-212** (Beitragsurteile gehoeren auf die
SELEKTIERTE Menge), und `messnorm.py:527` weist ihn auch ab - aber
nur ueber `frageart='beitrag'`. Hier wird `verwendung='Beitrag'`
uebergeben, und **das ist ein anderes Feld**. Der Riegel griff nie.

⚠️ Es ist kein Schoenheitsfehler, es kippt das Urteil der
KONTROLLE - und damit den ganzen Lauf:

    zufall auf `frei`    +0,0007  [+0,0003 .. +0,0014]  2.945 Tage  TRAEGT
    zufall auf `20%`     +0,0008  [-0,0010 .. +0,0025]  2.459 Tage  traegt nicht

**Die Wirkung ist dieselbe.** Was sich unterscheidet, ist das BAND:
auf `frei` liegen rund 226 Anker je Tag, auf der selektierten Menge
rund 45. Ein engeres Band laesst dieselbe Winzigkeit ,tragen`.

⚠️ **Damit ist 2.237 erklaert, ohne 2.485 zu widersprechen** - die
beiden Befunde stehen auf VERSCHIEDENEN Mengen, und beide sind
richtig. Was falsch war, ist die Vorgabe dieses Werkzeugs.

## Die Mengen, die es kennt

    --menge frei     die alte Vorgabe - fuer die Reproduktion (R-R11)
    --menge 20%      eine feste selektierte Menge
    --menge auto     ⭐ je Kandidat die SCHMALSTE, die die Datenlage
                     traegt (`menge_nach_datenlage`: mindestens
                     MIND_ANKER je Tag UND 20 Bloecke). Gemessen am
                     07.09.: turnover 50 %, funding 10 %, oi 20 % -
                     wer alle auf dieselbe Menge zwingt, misst bei
                     einem von ihnen Rauschen

⚠️ Gibt `menge_nach_datenlage` **None** zurueck, ist die Frage auf
dieser Datenlage nicht als Beitragsfrage zu stellen. Das ist ein
ERGEBNIS und wird als solches ausgewiesen, nicht uebersprungen.

## ⚠️⚠️ UND DAS ZEITFENSTER - sonst ist der Vergleich unzulaessig

Der Vergleich, auf den **2.291-ausloeser** zielt (*,traegt ein
Beitrag auf `barriere` ANDERS als auf `bewegung_r`?`*), geht nur
auf **demselben Fenster**. Die Gegenseite **2.460-norm** laeuft
**ab 2023**; dieser Lauf umfasst ohne `--ab` rund acht Jahre.

⚠️ Die stehende Vorgabe ZEITFENSTER-AB-2023 sagt dazu woertlich,
die lange Tabelle *,mittelt eine gute und eine schlechte Haelfte`*
(+8,64 gegen +2,77). Wer ohne `--ab` mit 2.460-norm vergleicht,
vergleicht zwei verschiedene Maerkte.

    python k1c_hebel_barriere.py                # wie bisher (frei, ganzes Fenster)
    python k1c_hebel_barriere.py --menge auto   # Zelle 2
    python k1c_hebel_barriere.py --menge auto --ab 2023-01-01   # Zelle 3
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


def barriere_je_reihe(reihe, H: int, crv: float | None = None,
                      ungeloest: float | None = None):
    """Ziel vor Stop, auf der PRODUKTIONSGEOMETRIE -> {tag: 1.0/0.0}.

    ⚠️ Genau die Geometrie, die `entscheidungsrechnung` baut - sonst misst
    der Test etwas anderes als das, was die App vorschlaegt.

    crv        Zielhoehe in Stop-Abstaenden. None = `GRENZEN['crv']`,
               also die Produktionsvorgabe 2,0. 2b variiert sie.

    ungeloest  ⚠️⚠️ WAS MIT ANKERN GESCHIEHT, bei denen im Fenster
               WEDER Ziel noch Stop faellt. Das ist keine Feinheit,
               es ist die Frage nach dem MASS:

                 None   sie fallen HERAUS -> gemessen wird
                        P(Ziel | aufgeloest), der RICHTUNGSKANAL.
                        Die alte und weiter die VORGABE.
                 0.0    sie zaehlen als VERFEHLT -> gemessen wird
                        die unbedingte QUOTE. Das ist `q` der
                        Potentialformel (2.139-quote).

               ⚠️ Die beiden koennen GEGENEINANDER laufen: `turnover`
               traegt Richtung (+0,00512), auf der Quote nicht, weil
               sein Aufloesungskanal (-0,00218) dagegenhaelt (2.136).
               Wer nur eines misst, kann das nicht sehen.
    """
    crv = float(GRENZEN["crv"] if crv is None else crv)
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
        ziel = c[i] + crv * stop_abstand
        for j in range(i + 1, min(i + 1 + H, len(c))):
            if t[j] <= stop:
                aus[tage[i]] = 0.0
                break
            if h[j] >= ziel:
                aus[tage[i]] = 1.0
                break
        else:
            # ⚠️ Faellt im Fenster KEINES von beiden: mit
            # `ungeloest=None` bleibt der Anker aussen (Richtungskanal,
            # alte Vorgabe), mit 0.0 zaehlt er als verfehlt (Quote).
            # Der Anteil wird so oder so ausgewiesen, nicht verschwiegen.
            if ungeloest is not None:
                aus[tage[i]] = float(ungeloest)
    return aus


def barriere_je_tag(je_tag: dict, reihen: dict, H: int,
                    crv: float | None = None,
                    ungeloest: float | None = None):
    """Ersetzt `in_r` durch den Barrierenausgang. -> (je_tag, Anteil geloest)

    ⚠️ `crv` und `ungeloest` reicht sie nur durch - die Bedeutung
    steht bei `barriere_je_reihe`."""
    je_sym = {s: barriere_je_reihe(v, H, crv, ungeloest)
              for s, v in reihen.items()}
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


def main(argv: list[str] | None = None) -> int:
    # ⚠️ VORGABE `frei` - damit ein Aufruf ohne Argument weiter
    # BITGLEICH den 09.09.-Lauf rechnet (R-R11, Reproduktion von
    # 2.237). Die Vorgabe ist falsch nach F-212; sie bleibt
    # trotzdem, weil sonst der Vergleichspunkt verschwindet.
    args = list(sys.argv[1:] if argv is None else argv)
    wunsch = "frei"
    if "--menge" in args:
        wunsch = args[args.index("--menge") + 1]
    if wunsch != "auto" and wunsch not in MA.MENGEN:
        print("unbekannte Menge %r - erlaubt: auto, %s"
              % (wunsch, ", ".join(MA.MENGEN)))
        return 2
    # ⚠️ Leer = ganzes Fenster. Das ist die alte Lage und bleibt die
    # Vorgabe, damit Zelle 1 reproduzierbar bleibt - NICHT, weil es
    # das richtige Fenster waere (ZEITFENSTER-AB-2023).
    ab = ""
    if "--ab" in args:
        ab = args[args.index("--ab") + 1]
    # ⚠️ SAATPROBE (Methodik 2.477). Die Vorgabe 20260909 ist die des
    # Erstlaufs und bleibt, damit Zelle 1 reproduzierbar ist. Ein
    # Urteil - erst recht ein NULLBEFUND - darf nicht an ihr haengen.
    saat = 20260909
    if "--saat" in args:
        saat = int(args[args.index("--saat") + 1])
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
    print("  Menge: %s%s" % (
        wunsch,
        ("  ⚠️ F-212-WIDRIG - nur fuer die Reproduktion von 2.237"
         if wunsch == "frei" else "")))
    print("  Fenster: %s" % (
        ("ab %s" % ab) if ab else
        "GANZ (⚠️ nicht mit 2.460-norm vergleichbar - die laeuft ab 2023)"))
    print("  Saat: %d%s" % (saat, "" if saat == 20260909
                            else "  (Saatprobe, nicht der Erstlauf)"))
    print()
    print("  %-14s %6s %9s %20s %9s %8s %7s  %s"
          % ("Kandidat", "Menge", "Wirkung", "Band", "Bezug", "Tage",
             "Bloecke", "Urteil"))

    erg, anteil = {}, None
    for kand in KANDIDATEN:
        try:
            je0 = K.baue(reihen, kand, zus.get(kand), horizont=HORIZONT)
        except Exception as exc:                             # noqa: BLE001
            print("  %-14s -> %s" % (kand, str(exc)[:60]))
            continue
        je, anteil = barriere_je_tag(je0, reihen, HORIZONT)
        # ⚠️ NACH der Umrechnung filtern, nicht davor: `barriere_je_reihe`
        # braucht die Kurse VOR dem Fenster nicht, aber die ATR-Spanne
        # schon. Wer die Reihe vorher kuerzt, misst eine andere Geometrie.
        if ab:
            je = {t: z for t, z in je.items() if str(t)[:10] >= ab}
        if not je:
            print("  %-14s -> leere Welt nach der Umrechnung" % kand)
            continue
        # ⚠️ `auto` fragt die DATENLAGE, nicht den Geschmack. Gibt sie
        # None, ist die Frage hier nicht als Beitragsfrage zu stellen -
        # das wird ausgewiesen, nicht stillschweigend weggelassen.
        _m = wunsch
        if wunsch == "auto":
            _m = MA.menge_nach_datenlage(je, mom, horizont=HORIZONT)
            if _m is None:
                print("  %-14s %6s -> KEINE Menge haelt Anker UND Bloecke - die Frage"
                      "%s      ist auf dieser Datenlage keine Beitragsfrage" % (kand, "-", chr(10)), flush=True)
                continue
        try:
            b = MA.pruefe_auswahl(
                kand, je, mom, lage=lage, menge=_m,
                rng=np.random.default_rng(saat), horizont=HORIZONT,
                hypothese="K-1c Hebel", verwendung="Beitrag",
                zielgroesse="barriere")
        except Exception as exc:                             # noqa: BLE001
            print("  %-14s -> %s" % (kand, str(exc)[:70]))
            continue
        erg[kand] = b
        print("  %-14s %6s %+9.4f [%+.4f..%+.4f] %+9.4f %8d %7d  %s"
              % (kand, _m, b.wirkung, b.unten, b.oben, b.bezugswert,
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
