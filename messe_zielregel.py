# -*- coding: utf-8 -*-
"""K-2: Schneidet die ZIELREGEL den Ertrag ab? (29.08.2026)

## Warum diese Frage, und warum sie NEU ist

Drei unabhaengige Messungen dieses Projekts zeigen auf dieselbe Stelle:

  1. TRAILING (26.08., Block-Bootstrap): "Trefferquote steigt ueberall
     (30,6 -> 42,2 %), Erwartungswert faellt trotzdem - mehr kleine Gewinne,
     abgeschnittene grosse." In der Aufwaertsphase -0,043 R je Trade.
  2. DRIFT (29.08., 655.000 Anker): Median -0,41 R, Mittel +0,74 R,
     99-%-Quantil +13,7 R. Der Ertrag steckt in der Schiefe.
  3. K-1 (29.08.): die beste gefundene Regel verbessert den Median und
     HALBIERT den Mittelwert.

⚠️ ABER: gemessen wurde bisher immer nur das TRAILING - und zwar mit einem
festen Ziel bei CRV 2,6 in BEIDEN Armen (`pruefe_regel_je_marktphase.py:39`).
Die Zielregel selbst wurde nie variiert. Genau das geschieht hier.

## Die Frage

    Ein Ziel bei CRV 2,0 verkauft bei +2 R. Wenn der Ertrag im 99-%-Quantil
    bei +13,7 R liegt - wieviel davon wirft die Zielregel weg?

## Der Aufbau

Sieben Ausstiegsvarianten auf DENSELBEN Ankern und DEMSELBEN Pfad. Es gibt
keine Zuordnung, die eine Permutation zerstoeren koennte - deshalb Bootstrap,
nicht Permutation (Methodik 2.55, dieselbe Begruendung wie beim Trailing).

    ZIEL 1,0 / 1,5 / 2,0 / 3,0 / 5,0   Stop bei -1 R, festes Ziel
    OHNE ZIEL                          Stop bei -1 R, sonst bis Horizontende
    NUR ZEIT                           kein Stop, kein Ziel

Stop und Ziel in R, also an der eigenen Schwankungsbreite - damit sind
verschiedene Assets vergleichbar.

## Die Reihenfolge INNERHALB eines Tages

⚠️ Wird an einem Tag sowohl Stop als auch Ziel beruehrt, wird der STOP
angenommen. Das ist die vorsichtige Annahme und dieselbe, die
`backward_tracking` verwendet - sie unterschaetzt den Ertrag eher, als ihn
zu beschoenigen.

## Vorab festgelegt, VOR dem Lauf

  Die Zielregel schneidet ab   OHNE ZIEL hat einen hoeheren Erwartungswert
                               als ZIEL 2,0, und das Bootstrap-Intervall der
                               Differenz schliesst die Null nicht ein
  Sie schneidet nicht ab       sonst
  ⚠️ Erwartet wird BEIDES zugleich: OHNE ZIEL besserer Erwartungswert,
     ZIEL 2,0 bessere Trefferquote. Der Sinn der Messung ist die GROESSE
     des Unterschieds, nicht sein Vorzeichen.
"""
import sys

import numpy as np

if hasattr(sys.stdout, "reconfigure"):        # ⚠️ Suite ersetzt stdout
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import messe_eigenschaft_beitrag as B

HORIZONT = 60
BLOCK = 30          # zusammenhaengende Anker je Reihe - sie teilen sich Kerzen
ZIEHUNGEN = 2000
VARIANTEN = (("ZIEL 1,0", 1.0), ("ZIEL 1,5", 1.5), ("ZIEL 2,0", 2.0),
             ("ZIEL 3,0", 3.0), ("ZIEL 5,0", 5.0),
             ("OHNE ZIEL", None), ("NUR ZEIT", "zeit"))


BRUCH = 5.0     # Tagessprung ab diesem Faktor ist eine Token-Umstellung


def ergebnisse(reihen, bereinigt=True, horizont=None, mit_gleichstand=False):
    """Je Anker: Ergebnis in R fuer jede Variante, plus Phase und Blockindex.

    ⚠️⚠️⚠️ `mit_gleichstand` KAM AM 24.09.2026 DAZU (P-9, Stundenbasis).

    DER ANLASS steht eine Zeile tiefer im Code: `stop_tag <= ziel_tag` -
    werden Ziel und Stop am SELBEN TAG beruehrt, gewinnt der Stop. Auf
    TAGESdaten ist die Reihenfolge unbekannt, also ist das die vorsichtige
    Annahme - aber sie ist SYSTEMATISCH PESSIMISTISCH, und `q` (die
    Barrieren-Trefferquote, an der der ganze Hebel haengt) ist genau diese
    Zahl.

    Seit dem 24.09. liegen 3,24 Mio STUNDENkerzen vor. Auf ihnen ist die
    Reihenfolge aufloesbar - gemessen sind dort nur 0,00 bis 0,04 Prozent
    der Faelle mehrdeutig (2.582-Nachfolge).

    ⚠️ DIESER SCHALTER LOEST NICHTS AUF. Er MELDET nur, welche Anker
    betroffen sind, damit ein zweites Werkzeug genau diese - und nur diese -
    stuendlich nachrechnen kann. Chirurgisch statt reihenweise: was heute
    eindeutig ist, bleibt bitgleich, und die Aenderung ist zuordenbar.

    ⚠️⚠️ DIE VORGABE IST `False`, und dann ist die Rueckgabe UNVERAENDERT -
    kein zusaetzlicher Schluessel, kein anderer Wert. 44 Skripte rufen diese
    Funktion; R-R11 verlangt, dass sie alle bitgleich weiterrechnen.

    Bei `True` kommt je Zeile dazu:

        gleichstand    True, wenn Ziel UND Stop am selben Tag beruehrt
                       werden (nur fuer CRV 2,0 - die Groesse, aus der
                       `q` entsteht)
        entscheid_tag  das DATUM des Tages, an dem die erste Barriere
                       faellt - AUCH wenn er eindeutig ist. Genau das
                       traegt die Gegenpruefung: an einem eindeutigen Tag
                       muss die Stundenrechnung dieselbe Barriere zuerst
                       sehen, sonst stimmt sie nicht
        erwartet       'ziel' | 'stop' | 'unklar' | None - was die
                       TAGESrechnung sagt, als Sollwert fuer ebendiese
                       Gegenpruefung
        anker_tag      das Datum des Ankers
        stop_kurs      die beiden Schwellen, damit das zweite Werkzeug sie
        ziel_kurs      nicht neu herleiten muss (und dabei abweichen kann)

    ⚠️⚠️⚠️ `horizont` KAM AM 24.09.2026 DAZU - vorher war der Wert ein
    Modul-Global (60), und jeder Aufrufer bekam ihn ungefragt.

    DER ANLASS: `phase4_n19e_pruefen` baut die Fuenftel mit `horizont=20`
    und liess die Ergebnisse hier ueber 60 Tage rechnen - ein eingebauter
    Horizontbruch, genau der, der am 24.09. schon einmal gekostet hat
    (2.569: *„ich sprach von H20 und mass in Wahrheit ueber 60 Tage"*).
    Gefunden VOR der Messung, nicht danach.

    ⚠️ DIE VORGABE BLEIBT DER MODULWERT (60), damit jeder bestehende
    Aufruf BITGLEICH weiterrechnet (R-R11). Wer einen anderen Horizont
    will, sagt es ausdruecklich.

    ⚠️ `bereinigt`: Anker, deren VORWAERTSFENSTER einen Tagessprung ueber
    Faktor `BRUCH` enthaelt, werden uebersprungen. Grund (29.08.2026): in
    `messdaten.db` stehen Token-Umstellungen als Kurssprung - LUNA Faktor
    177.400 (Neuausgabe nach dem Kollaps), COCOS 1.295 (Redenominierung
    1:1000), DREP 108 (Swap 1:100). Sie erzeugten in der ersten Fassung
    Einzelwerte bis +80.584 R und trugen 112 % des Mittelwerts.

    Chirurgisch statt reihenweise: nur die betroffenen Anker fallen weg,
    die uebrige Historie derselben Reihe bleibt nutzbar.
    """
    H = int(HORIZONT if horizont is None else horizont)
    zeilen = []
    for sym, roh in reihen.items():
        schluss = np.array([z[1] for z in roh])
        hoch = np.array([z[2] for z in roh])
        tief = np.array([z[3] for z in roh])
        breite = B.spanne(hoch, tief, schluss, B.SCHWANKUNG)
        n = len(schluss)
        verhaeltnis = schluss[1:] / np.maximum(schluss[:-1], 1e-12)
        bruch = (verhaeltnis > BRUCH) | (verhaeltnis < 1.0 / BRUCH)
        for i in range(200, n - H):
            r = breite[i]
            if not np.isfinite(r) or r <= 0:
                continue
            if bereinigt and bruch[i:i + H].any():
                continue
            schnitt = schluss[i - 200:i].mean()
            if schnitt <= 0:
                continue
            e = schluss[i]
            stop = e - r
            # Pfad
            ph = hoch[i + 1:i + 1 + H]
            pt = tief[i + 1:i + 1 + H]
            pc = schluss[i + 1:i + 1 + H]
            # erster Tag, an dem der Stop beruehrt wird
            stop_tag = np.argmax(pt <= stop) if (pt <= stop).any() else H
            zeile = {"sym": sym, "i": i, "steigend": bool(e > schnitt)}
            for name, crv in VARIANTEN:
                if crv == "zeit":
                    zeile[name] = float((pc[-1] - e) / r)
                    continue
                if crv is None:
                    zeile[name] = (-1.0 if stop_tag < H
                                   else float((pc[-1] - e) / r))
                    continue
                ziel = e + r * crv
                ziel_tag = (np.argmax(ph >= ziel) if (ph >= ziel).any()
                            else H)
                if stop_tag <= ziel_tag and stop_tag < H:
                    zeile[name] = -1.0          # Stop gewinnt bei Gleichstand
                elif ziel_tag < H:
                    zeile[name] = float(crv)
                else:
                    zeile[name] = float((pc[-1] - e) / r)
                # ⚠️ NUR MELDEN, NICHT AUFLOESEN - und nur fuer CRV 2,0,
                # weil `q` aus genau dieser Variante entsteht. Ohne den
                # Schalter passiert hier nichts (R-R11).
                if mit_gleichstand and crv == 2.0:
                    _gleich = (stop_tag == ziel_tag) and stop_tag < H
                    _erst = min(int(stop_tag), int(ziel_tag))
                    zeile["gleichstand"] = bool(_gleich)
                    zeile["anker_tag"] = roh[i][0]
                    zeile["stop_kurs"] = float(stop)
                    zeile["ziel_kurs"] = float(ziel)
                    # ⚠️ DER ENTSCHEIDUNGSTAG, auch wenn er EINDEUTIG ist.
                    # Er traegt die Gegenpruefung: an einem eindeutigen Tag
                    # MUSS die Stundenrechnung dieselbe Barriere zuerst
                    # sehen. Am ANKERtag zu pruefen waere falsch - der
                    # Einstieg ist dessen SCHLUSSkurs, und die Kerzen davor
                    # koennen die Schwelle laengst beruehrt haben.
                    zeile["entscheid_tag"] = (roh[i + 1 + _erst][0]
                                              if _erst < H else None)
                    zeile["erwartet"] = (None if _erst >= H else
                                         "unklar" if _gleich else
                                         "stop" if stop_tag < ziel_tag
                                         else "ziel")
            zeilen.append(zeile)
    return zeilen


def bootstrap(werte, bloecke, rng):
    """Bloecke von 30 zusammenhaengenden Ankern ziehen, mit Zuruecklegen.

    Gerechnet wird ueber die BLOCKMITTEL, nicht ueber die Einzelwerte - bei
    634.000 Ankern waere das Zusammensetzen je Ziehung nicht rechenbar. Da
    alle Bloecke dieselbe Laenge haben (bis auf den letzten je Reihe), ist
    das Mittel der Blockmittel dasselbe Mass.
    """
    mittel = np.array([b.mean() for b in bloecke])
    n = len(mittel)
    aus = []
    for anfang in range(0, ZIEHUNGEN, 200):        # in Haeppchen, sonst Speicher
        wieviele = min(200, ZIEHUNGEN - anfang)
        idx = rng.integers(0, n, (wieviele, n))
        aus.extend(mittel[idx].mean(axis=1).tolist())
    return aus


def bloecke_bilden(zeilen, name):
    """Zusammenhaengende Bloecke je Reihe."""
    aus, laufend, letzte = [], [], None
    for z in zeilen:
        kennung = (z["sym"], z["i"] // BLOCK)
        if kennung != letzte and laufend:
            aus.append(np.array(laufend))
            laufend = []
        laufend.append(z[name])
        letzte = kennung
    if laufend:
        aus.append(np.array(laufend))
    return aus


def zeige(titel, zeilen, rng):
    print()
    print("-" * 86)
    print("%s — %d Anker" % (titel, len(zeilen)))
    print("-" * 86)
    print("  %-11s %11s %11s %11s   %s"
          % ("Variante", "Mittel R", "Median R", "Treffer %", "95-%-Bereich des Mittels"))
    basis = None
    for name, _ in VARIANTEN:
        w = np.array([z[name] for z in zeilen])
        bl = bloecke_bilden(zeilen, name)
        z = bootstrap(w, bl, rng)
        u, o = np.quantile(z, [0.025, 0.975])
        treffer = 100.0 * (w > 0).mean()
        marke = ""
        if name == "ZIEL 2,0":
            basis = (w, bl)
            marke = "  <- heute"
        print("  %-11s %+11.4f %+11.4f %10.1f    [%+7.4f .. %+7.4f]%s"
              % (name, w.mean(), np.median(w), treffer, u, o, marke))
    # gepaarte Differenz OHNE ZIEL minus ZIEL 2,0
    if basis is not None:
        a = np.array([z["OHNE ZIEL"] for z in zeilen])
        d = a - basis[0]
        bl = bloecke_bilden([{**z, "d": z["OHNE ZIEL"] - z["ZIEL 2,0"]}
                             for z in zeilen], "d")
        zz = bootstrap(d, bl, rng)
        u, o = np.quantile(zz, [0.025, 0.975])
        print()
        print("  GEPAART: OHNE ZIEL minus ZIEL 2,0   %+.4f R   [%+.4f .. %+.4f]   %s"
              % (d.mean(), u, o,
                 "das Ziel SCHNEIDET AB" if u > 0 else
                 ("das Ziel NUETZT" if o < 0 else "nicht von null zu trennen")))


def main():
    reihen = B.lade()
    print("=" * 86)
    print("K-2 — SCHNEIDET DIE ZIELREGEL DEN ERTRAG AB?")
    print("=" * 86)
    print("523 Reihen · Horizont %d Handelstage · Stop fest bei -1 R" % HORIZONT)
    print("Bei Beruehrung von Stop UND Ziel am selben Tag gilt der STOP.")
    zeilen = ergebnisse(reihen)
    rng = np.random.default_rng(20260829)
    zeige("ALLE LAGEN", zeilen, rng)
    zeige("AUFWAERTS (Kurs ueber dem 200-Schnitt)",
          [z for z in zeilen if z["steigend"]], rng)
    zeige("ABWAERTS (Kurs unter dem 200-Schnitt)",
          [z for z in zeilen if not z["steigend"]], rng)


if __name__ == "__main__":
    main()
