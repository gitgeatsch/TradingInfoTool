# -*- coding: utf-8 -*-
"""N-46 — ein gueltiger NULLPUNKT fuer die LAENGS-Form (10.09.2026)

## Der Blocker, seit dem 05.09. unveraendert

> **N-46: Ein gueltiger Nullpunkt fuer die LAENGS-Form.** Die
> Tagesmischung taugt dort nicht: sie laesst die marktweite
> Gemeinsamkeit stehen (bei `amihud` lieferte die Kontrolle +0,620 gegen
> einen echten Wert von +0,713). Zu bauen ist eine Mischung **ueber die
> Zeit innerhalb eines Symbols**.
>
> *„Ohne diesen Nullpunkt ist keine Form baureif … Das ist die einzige
> Frage, die den Weg blockiert."*

⚠️ Er blockiert **Kriterium 4 des Vierfachtests** (Regel 3 laengs) - und
damit jeden neuen Beitrag, damit die staerkere Bewertung, damit den
Hebel (F-220: nur EINE Lage erreicht die Zielzone 2-5x).

## Warum die Tagesmischung hier falsch ist

`n75_quer_gegen_laengs` mischt auf BEIDEN Achsen die Raenge INNERHALB des
Tages (`mische.permutation(r)`). Quer ist das richtig - dort ist der Rang
ja gerade der Vergleich der Symbole eines Tages.

**Laengs zerstoert es nichts.** Der Laengs-Rang sagt „wo steht dieser
Wert gegen SEINE eigene Geschichte". Wenn an einem Tag der ganze Markt
hoch steht, stehen fast alle Symbole in ihrem oberen Bereich - und das
bleibt nach dem Mischen genauso. Die Mischung tauscht nur, WELCHES Symbol
welchen hohen Rang bekommt; sie trennt die Gruppe nicht vom Marktzustand
des Tages. Deshalb faellt der Nullpunkt fast so hoch aus wie der echte
Wert.

## Die Loesung: der ZIRKULAERE VERSCHUB — und sie liegt schon im Haus

Genau diese Konstruktion hat der Akkumulationsbefund vom 28.08. benutzt,
bei **H=90 auf 505 Reihen**, mit sauberer Positiv- und Negativkontrolle:

| Zelle | Rang | Zufall 5-95 % | p |
|---|---|---|---|
| UNTER_SMA (Primaerzelle) | +0,0283 | -0,0124 .. +0,0089 | 0,000 |
| TIEFPUNKT (Positivkontrolle) | +0,4242 | -0,0337 .. +0,0292 | 0,000 |
| WOCHENTAG (Negativkontrolle) | -0,0008 | ±0,0007 | 0,978 |

## ⚠️ Die Methodik, richtig zitiert — sie liefert den Pruefsatz

Ich hatte **2.77** zunaechst falsch wiedergegeben. Der Satz ueber
ueberlappende Anker ist **2.47**; **2.77** heisst *„Die Permutation muss
die Grenze respektieren, die man befragt"* - und das ist die Regel, um
die es hier geht:

> **Die Regel:** Die Permutation muss genau die Struktur zerstoeren,
> deren Wirkung geprueft wird — und alles andere erhalten.
>
> **Der Pruefsatz:** *Kann unter meiner Permutation ein Wert die Grenze
> ueberschreiten, um die es geht? Wenn nein, misst der Placebo nicht die
> These.*

**Angewandt auf die Laengs-Form:** die befragte Grenze ist die EIGENE
ZEITACHSE des Symbols („steht dieser Wert hoch in SEINER Geschichte?").
Die Tagesmischung kann einen Anker nicht ueber diese Grenze bewegen - sie
tauscht nur, welches Symbol den hohen Tagesrang bekommt. Der zirkulaere
Verschub kann es. **Nach 2.77 ist die Tagesmischung hier kein gueltiger
Placebo.**

⚠️ Und **2.47** gilt zusaetzlich: taegliche Anker mit H20-Vorwaertsfenster
ueberlappen; deshalb bleibt der Blockbootstrap fuer das BAND, waehrend der
Verschub den NULLPUNKT liefert. Zwei verschiedene Aufgaben.

    Verschub   die Rangreihe wird um d Kalendertage verschoben,
               ZIRKULAER, und fuer JEDES SYMBOL UM DENSELBEN BETRAG

⚠️⚠️ **Der gleiche Betrag ist keine Kleinigkeit.** Der Akkumulationsbefund
haelt einen eigenen Fehler fest: eine Korrektur addierte den Startpunkt
des Symbols hinzu (`(d + eigen) % len(m)`), womit sich jede Reihe wieder
um einen ANDEREN Betrag verschob - und die Gleichzeitigkeit des Marktes
war zerstoert, die der Verschub gerade erhalten soll.

## ⚠️⚠️ VOR ODER NACH DEM UMBAU? — die Herkunft jedes Bausteins

Nutzervorgabe 10.09.: *„du musst sauber trennen nach vor und nach dem
aktuellen Umbau - das gilt fuer Messungen, Dokumente und Code."* Die
Grenze ist der Messstandard vom **2026-09-09**.

| Baustein | Herkunft | was daraus folgt |
|---|---|---|
| `laengs_rang` (n75, 07.09.) | **VOR** | eine DEFINITION (nachlaufender Rang, kein Lookahead), kein Nullmodell - uebernommen |
| `wirkung` (n75, 07.09.) | **VOR** | die Kennzahl `median(frei) - median(alle)` je Tag - dieselbe wie ueberall |
| Tagesmischung als Nullpunkt | **VOR** | ⚠️ laeuft hier NUR als Gegenprobe, nicht als Massstab |
| Blockbootstrap fuer das Band | NACH | `messnorm._block`, Block = 3 x H |
| Nullpunkt, 90. Perzentil | NACH | `messnorm.NULL_PERZENTIL` |
| Trennschaerfeleiter | NACH | `messnorm.STAERKEN` bis 0,40 |
| zirkulaerer Verschub | NACH | hier neu gebaut, begruendet mit 2.77 |

⚠️ **Der Verschub selbst hat einen Vorlaeufer VOR dem Umbau** - den
Akkumulationsbefund vom 28.08. Er dient hier als *Vorbild und
Plausibilitaetspruefung*, NICHT als Beleg. Belegt wird in diesem Lauf
neu, unter dem Standard. Das ist die Regel aus `REGISTER_Werkzeuge`:
*„eine bestehende Messung wird nicht als Beleg fuer einen NEUEN Befund
herangezogen, ohne vorher unter die Norm gestellt zu werden."*

## Was hier gemessen wird — vier Pruefungen, alle vorab benannt

    P1  ZENTRIERT   Streut der Verschub-Nullpunkt um NULL? Er muss, denn
                    unter Verschub gibt es keinen Zusammenhang mehr.
    P2  KONTROLLE   `zufall` darf unter dem Verschub NICHT tragen.
    P3  MACHT       Findet die Anlage einen GEPFLANZTEN Effekt wieder?
                    Ohne das waere ein Nullbefund keine Aussage.
    P4  GEGENPROBE  Ist die Tagesmischung nachweislich zu hoch? Der
                    dokumentierte Fall ist `amihud` (+0,620 gegen +0,713).

⚠️ **P4 ist die eigentliche Abnahme.** Erst wenn beide Nullpunkte
nebeneinander stehen, ist belegt, dass der neue der richtige ist - und
nicht nur der bequemere.

## Die Vorhersage, VOR dem Lauf (Methodik 2.80)

    P1  Verschub-Nullpunkte streuen um 0, Mittel nahe 0
    P2  `zufall` traegt nicht
    P3  ein gepflanzter Effekt von 0,20 R wird gefunden
    P4  die Tagesmischung liegt DEUTLICH hoeher als der Verschub -
        bei `amihud` nahe am echten Wert

⚠️ Faellt P1 oder P3, taugt auch der Verschub nicht, und N-46 bleibt
offen. Das waere ein Befund, kein Rueckschlag.

    python n98_n46_laengs_nullpunkt.py
"""
from __future__ import annotations

import sys
import time

import numpy as np

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import messe_eigenschaft_beitrag as B                        # noqa: E402
import messe_kandidaten_als_regel as K                       # noqa: E402
import messe_regel_wirksamkeit as RW                         # noqa: E402
import messmenge                                              # noqa: E402
import messnorm as N                                          # noqa: E402
from messe_alle_kandidaten import HORIZONT, zusatzquellen    # noqa: E402
from messe_beitrag_auf_auswahl import momentum250            # noqa: E402
from messnorm_auswahl import MENGEN                           # noqa: E402
from n75_quer_gegen_laengs import laengs_rang, wirkung        # noqa: E402
from n91_rangkorrelation_form import band                     # noqa: E402

KANDIDATEN = ("amihud", "vola", "schnitt", "rsi", "zufall")
VERSCHUEBE = 40
MIN_VERSCHUB = 250       # ⚠️ mindestens ein Jahr - laenger als FENSTER (250)
SAAT = 20260910
PFLANZE = 0.20


def verschiebe(lr: dict, d: int) -> dict:
    """Die Laengs-Rangreihe um d Kalendertage verschieben - ZIRKULAER.

    ⚠️⚠️ FUER JEDES SYMBOL DERSELBE BETRAG. Das ist der Kern: die
    Gleichzeitigkeit des Marktes bleibt erhalten, nur die Zuordnung
    Signal -> Ergebnis wird geloest. Wer je Symbol anders verschiebt,
    zerstoert genau die Eigenschaft, die den Verschub tauglich macht
    (dokumentierter Fehler im Akkumulationsbefund vom 28.08.).

    ⚠️ Verschoben wird die ganze TAGESKARTE. Ein Symbol bekommt damit den
    Laengs-Rang, den es an einem anderen Tag hatte - seine eigene
    Rangverteilung bleibt also erhalten.
    """
    tage = sorted(lr)
    n = len(tage)
    if n < 2:
        return {}
    return {tage[i]: lr[tage[(i + d) % n]] for i in range(n)}


def pflanze_effekt(je_tag: dict, lr: dict, staerke: float) -> dict:
    """Den Ankern im OBERSTEN eigenen Fuenftel `staerke` R abziehen.

    ⚠️ Richtung: die GESPERRTEN schlechter machen laesst die Regel besser
    aussehen - die Kennzahl STEIGT. Dieselbe Konstruktion wie `sammle`.
    """
    aus = {}
    for tag, z in je_tag.items():
        lt = lr.get(tag) or {}
        neu = []
        for x in z:
            r = lt.get(x["sym"])
            if r is not None and r >= RW.GRENZE:
                y = dict(x)
                y["in_r"] = float(x["in_r"]) - float(staerke)
                neu.append(y)
            else:
                neu.append(x)
        aus[tag] = neu
    return aus


def messe(je_tag, mom, lr, block, anteil=1.0):
    """Der echte Wert mit Band - auf der LAENGS-Achse."""
    echt, besetzt = wirkung(je_tag, mom, anteil, "laengs", lr)
    b = band(echt, block)
    if b is None:
        return None
    return {"wert": b[0], "unten": b[1], "oben": b[2], "bloecke": b[3],
            "tage": len(echt),
            "anker": float(np.mean(besetzt)) if besetzt else 0.0}


def nullpunkt_verschub(je_tag, mom, lr, block, anteil=1.0):
    """Die Nullverteilung aus zirkulaeren Verschueben."""
    tage = sorted(lr)
    n = len(tage)
    if n < 2 * MIN_VERSCHUB + 10:
        return None, []
    schritte = np.linspace(MIN_VERSCHUB, n - MIN_VERSCHUB, VERSCHUEBE)
    werte = []
    for d in schritte:
        lv = verschiebe(lr, int(round(d)))
        w, _ = wirkung(je_tag, mom, anteil, "laengs", lv)
        b = band(w, block, zieh=200, saat=SAAT)
        if b:
            werte.append(b[0])
    if not werte:
        return None, []
    return {"mittel": float(np.mean(werte)),
            "p90": float(np.percentile(werte, N.NULL_PERZENTIL)),
            "streuung": float(np.std(werte)),
            "min": float(np.min(werte)), "max": float(np.max(werte)),
            "n": len(werte)}, werte


def nullpunkt_tagesmischung(je_tag, mom, lr, block, anteil=1.0):
    """Die ALTE Konstruktion - zur Gegenprobe (P4)."""
    werte = []
    for z in range(VERSCHUEBE):
        w, _ = wirkung(je_tag, mom, anteil, "laengs", lr,
                       mische=np.random.default_rng(SAAT + z))
        b = band(w, block, zieh=200, saat=SAAT + z)
        if b:
            werte.append(b[0])
    if not werte:
        return None
    return {"mittel": float(np.mean(werte)),
            "p90": float(np.percentile(werte, N.NULL_PERZENTIL)),
            "n": len(werte)}


def main() -> int:
    t0 = time.time()
    reihen = B.lade()
    mom = momentum250(reihen)
    zus = zusatzquellen()
    block = N._block(HORIZONT)

    print("=" * 112)
    print("N-46 — ein gueltiger NULLPUNKT fuer die LAENGS-Form")
    print("=" * 112)
    print("  %s" % messmenge.zeile())
    print("  Block %d Tage · %d Verschuebe (min. %d Tage) · Leiter bis "
          "%.2f R" % (block, VERSCHUEBE, MIN_VERSCHUB, max(N.STAERKEN)))
    print("  ⚠️ Verschoben wird ZIRKULAER und fuer JEDES SYMBOL UM "
          "DENSELBEN BETRAG.")
    print("  ⚠️ Die Tagesmischung laeuft als GEGENPROBE mit - sie ist der "
          "Nullpunkt, der zu hoch ist.")

    ergebnis = {}
    for kand in KANDIDATEN:
        try:
            je = K.baue(reihen, kand, zus.get(kand), horizont=HORIZONT)
        except Exception as exc:                             # noqa: BLE001
            print("\n  %-12s -> %s" % (kand, str(exc)[:60]))
            continue
        lr = laengs_rang(je)
        if not lr:
            print("\n  %-12s -> kein Laengs-Rang bestimmbar" % kand)
            continue

        echt = messe(je, mom, lr, block)
        if echt is None:
            print("\n  %-12s -> zu wenige Bloecke" % kand)
            continue
        nv, rohwerte = nullpunkt_verschub(je, mom, lr, block)
        nt = nullpunkt_tagesmischung(je, mom, lr, block)
        if nv is None:
            print("\n  %-12s -> Verschub-Nullpunkt nicht bestimmbar" % kand)
            continue

        bez_v = max(0.0, nv["p90"])
        traegt_v = echt["unten"] > bez_v
        traegt_t = (echt["unten"] > max(0.0, nt["p90"])) if nt else None

        print()
        print("  %s   (%d Tage, %d Bloecke, %.1f Anker/Tag)"
              % (kand.upper(), echt["tage"], echt["bloecke"],
                 echt["anker"]))
        print("     echt                 %+9.4f [%+.4f .. %+.4f]"
              % (echt["wert"], echt["unten"], echt["oben"]))
        print("     Verschub-Nullpunkt   %+9.4f   p90 %+.4f   Streuung "
              "%.4f   [%+.4f .. %+.4f]  n=%d"
              % (nv["mittel"], nv["p90"], nv["streuung"], nv["min"],
                 nv["max"], nv["n"]))
        if nt:
            print("     Tagesmischung        %+9.4f   p90 %+.4f   "
                  "⚠️ GEGENPROBE" % (nt["mittel"], nt["p90"]))
        print("     Urteil               Verschub: %s   ·   "
              "Tagesmischung: %s"
              % ("TRAEGT" if traegt_v else "traegt nicht",
                 ("TRAEGT" if traegt_t else "traegt nicht")
                 if nt else "-"), flush=True)
        ergebnis[kand] = (echt, nv, nt, rohwerte)

    # ---- P3: die Positivkontrolle ---------------------------------------
    print()
    print("=" * 112)
    print("P3 — DIE POSITIVKONTROLLE: wird ein GEPFLANZTER Effekt "
          "gefunden?")
    print("=" * 112)
    print("  ⚠️ Gepflanzt wird auf `zufall` - dort gibt es nichts zu "
          "finden, was den Effekt")
    print("     verdecken oder verstaerken koennte. Erwartet wird rund "
          "%.2f R x (1 - GRENZE) = %.3f R."
          % (PFLANZE, PFLANZE * (1.0 - RW.GRENZE)))
    try:
        je = K.baue(reihen, "zufall", zus.get("zufall"), horizont=HORIZONT)
        lr = laengs_rang(je)
        jep = pflanze_effekt(je, lr, PFLANZE)
        ep = messe(jep, mom, lr, block)
        npv, _ = nullpunkt_verschub(jep, mom, lr, block)
        if ep and npv:
            bez = max(0.0, npv["p90"])
            print("     gepflanzt %.2f R     %+9.4f [%+.4f .. %+.4f]"
                  % (PFLANZE, ep["wert"], ep["unten"], ep["oben"]))
            print("     Verschub-Nullpunkt   %+9.4f   p90 %+.4f"
                  % (npv["mittel"], npv["p90"]))
            print("     %s"
                  % ("✔ GEFUNDEN - die Anlage hat Macht"
                     if ep["unten"] > bez else
                     "⚠️⚠️ NICHT GEFUNDEN - ein Nullbefund waere hier "
                     "keine Aussage"))
        else:
            print("     nicht messbar")
    except Exception as exc:                                 # noqa: BLE001
        print("     Positivkontrolle ausgefallen: %s" % str(exc)[:70])

    # ---- Die Abnahme -----------------------------------------------------
    print()
    print("=" * 112)
    print("DIE ABNAHME — P1 bis P4")
    print("=" * 112)
    if "zufall" in ergebnis:
        e, nv, nt, _ = ergebnis["zufall"]
        print("  P1 ZENTRIERT   Verschub-Nullpunkt bei `zufall`: %+.4f "
              "(Streuung %.4f)" % (nv["mittel"], nv["streuung"]))
        print("  P2 KONTROLLE   `zufall` traegt unter Verschub: %s"
              % ("⚠️⚠️ JA - der Nullpunkt taugt NICHT"
                 if e["unten"] > max(0.0, nv["p90"]) else "✔ nein"))
    print("  P4 GEGENPROBE  Verschub gegen Tagesmischung:")
    print("     %-12s %14s %14s %10s" % ("Kandidat", "Verschub p90",
                                         "Tagesm. p90", "Faktor"))
    for k, (e, nv, nt, _) in ergebnis.items():
        if not nt:
            continue
        f = (nt["p90"] / nv["p90"]) if abs(nv["p90"]) > 1e-9 else float("nan")
        print("     %-12s %+14.4f %+14.4f %10.1f" % (k, nv["p90"],
                                                     nt["p90"], f))
    print()
    print("  ⚠️ Liegt die Tagesmischung durchgehend HOEHER, ist belegt, "
          "dass sie zu streng ist -")
    print("     und der Verschub ist der richtige Nullpunkt fuer die "
          "Laengs-Form.")
    print("  ⚠️⚠️ Liegt sie NIEDRIGER oder gleich, ist meine Begruendung "
          "falsch und N-46 bleibt offen.")
    print("  Dauer %.1f Minuten" % ((time.time() - t0) / 60.0))
    return 0


if __name__ == "__main__":
    sys.exit(main())
