# -*- coding: utf-8 -*-
"""N-46b — welcher Laengs-Nullpunkt hat die RICHTIGE Fehlalarmquote?

## Die Frage, die N-46a offen gelassen hat

N-46a hat den zirkulaeren Verschub gebaut. Drei Pruefungen waren sauber
(zentriert, Kontrolle stumm, gepflanzte 0,20 R gefunden mit +0,0420
gegen erwartete 0,040). **Die vierte ist gescheitert:**

    vorhergesagt   die Tagesmischung liegt DEUTLICH HOEHER
    gemessen       sie liegt durchgehend NIEDRIGER (Faktor 0,2 bis 0,6)

> Damit ist meine Begruendung widerlegt, und der Vergleich der beiden
> Nullpunkte an ihrer HOEHE entscheidet gar nichts. Ein hoeherer
> Nullpunkt ist strenger, ein niedrigerer grosszuegiger - welcher
> RICHTIG ist, sagt nur die **Fehlalarmquote gegen bekannte Wahrheit**.

**Genau dieses Verfahren hat am 09.09. den Nullbezug entschieden**
(150 Nullwelten, drei Basen: `nullpunkt` 2,7 % Fehlalarme bei Soll
2,5 %, `null_oben` 0 % aber nur 63 % Fundquote, `null` 28 %).

## Der Aufbau

    Welten      `selbsttest_welt.welt(staerke=0)` - die Kennzahl sagt
                NICHTS ueber das Ergebnis. Jedes TRAEGT ist ein Fehlalarm.
    Achse       LAENGS - Rang je Symbol ueber die eigene Vergangenheit
    verglichen  VERSCHUB gegen TAGESMISCHUNG, auf DENSELBEN Welten
    Soll        2,5 % - das einseitige Niveau des 95-%-Bandes

⚠️⚠️ **Die Beharrlichkeit ist hier keine Feinheit, sondern die Sache
selbst.** Ein Laengs-Rang ueber eine Kennzahl ohne Gedaechtnis ist
sinnlos - jeder Tag zoege neu. An den echten Daten gemessen (08.09.):

    zufall    -0,001
    funding   +0,608
    schnitt   +0,985

Deshalb laufen **zwei Beharrlichkeiten**: 0,61 (wie `funding`) und
0,985 (wie `schnitt`). Ein Nullpunkt, der nur bei einer davon stimmt,
taugt nicht.

⚠️ Und `ueberlappung=HORIZONT` ist Pflicht - ohne sie hat die Welt rund
zwanzigmal zu viele unabhaengige Beobachtungen, und **jede** Anlage sieht
praeziser aus, als sie ist (2.199).

## Die Vorhersage, VOR dem Lauf (Methodik 2.80)

    Erwartung     der VERSCHUB liegt naeher an 2,5 % als die
                  Tagesmischung - er zerstoert die Struktur, die
                  befragt wird (2.77), die Tagesmischung nicht
    Gegenthese    die Tagesmischung trifft 2,5 % ebenso gut. Dann ist
                  der Verschub Aufwand ohne Ertrag, und N-46 waere mit
                  dem VORHANDENEN Werkzeug erledigt
    ⚠️ Dritter    BEIDE liegen daneben. Dann ist die Laengs-Achse mit
       Ausgang    dieser Anlage nicht messbar - ein Befund, kein
                  Rueckschlag

⚠️⚠️ **Ich habe bei N-46a auf die falsche Groesse gesetzt.** Diesmal ist
das Kriterium vorab benannt und es ist eine QUOTE, keine Rangfolge:
**naeher an 2,5 % gewinnt.**

    python n99_n46b_fehlalarm_laengs.py [--welten 40]
"""
from __future__ import annotations

import sys
import time

import numpy as np

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import messe_regel_wirksamkeit as RW                          # noqa: E402
import messnorm as N                                          # noqa: E402
import selbsttest_welt as SW                                  # noqa: E402
from messe_alle_kandidaten import HORIZONT                    # noqa: E402
from n75_quer_gegen_laengs import laengs_rang, wirkung        # noqa: E402
from n91_rangkorrelation_form import band                     # noqa: E402

WELTEN = 40
ZIEHUNGEN_NULL = 20      # Verschuebe bzw. Mischungen je Welt
ZIEH_BAND = 200
MIN_VERSCHUB = 250
SOLL = 2.5               # einseitiges Niveau des 95-%-Bandes, in Prozent
SAAT = 20260910
PFLANZE = 0.20
# ⚠️ Die Leiter der Fundquote - 0,20 R fand JEDES Modell (Vorabtest 3/3).
LEITER = (0.03, 0.05, 0.08, 0.12)
BEHARRLICHKEITEN = ((0.61, "wie `funding`"), (0.985, "wie `schnitt`"))


def verschiebe(lr: dict, d: int) -> dict:
    """Zirkulaer, fuer JEDES Symbol um denselben Betrag (siehe N-46a)."""
    tage = sorted(lr)
    n = len(tage)
    return {tage[i]: lr[tage[(i + d) % n]] for i in range(n)} if n > 1 else {}


def pflanze_laengs(je_tag: dict, lr: dict, staerke: float) -> dict:
    """Den Ankern im obersten EIGENEN Fuenftel `staerke` R abziehen.

    ⚠️⚠️ WARUM NICHT `selbsttest_welt(staerke=...)`: dort wird der Effekt
    auf den QUER-Rang des Tages gepflanzt. Fuer die Laengs-Achse waere
    das die falsche Gruppe - gemessen wuerde, ob die Laengs-Achse einen
    QUER-Effekt findet.

    ⚠️ Und warum nicht der `pflanze`-Parameter der Norm: `selbsttest_welt`
    warnt ausdruecklich davor, den Mechanismus mit sich selbst zu pruefen.
    Hier wird in die DATEN gepflanzt, bevor die Anlage sie sieht.
    """
    aus = {}
    for tag, z in je_tag.items():
        lt = lr.get(tag) or {}
        aus[tag] = [
            (dict(x, in_r=float(x["in_r"]) - float(staerke))
             if (lt.get(x["sym"]) is not None
                 and lt[x["sym"]] >= RW.GRENZE) else x)
            for x in z]
    return aus


def urteil(je_tag, mom, lr, block, art: str, rng):
    """TRAEGT der Kandidat unter diesem Nullmodell? -> True/False/None."""
    echt, _ = wirkung(je_tag, mom, 1.0, "laengs", lr)
    b = band(echt, block, zieh=ZIEH_BAND, saat=SAAT)
    if b is None:
        return None
    werte = []
    if art == "verschub":
        tage = sorted(lr)
        if len(tage) < 2 * MIN_VERSCHUB + 10:
            return None
        for d in np.linspace(MIN_VERSCHUB, len(tage) - MIN_VERSCHUB,
                             ZIEHUNGEN_NULL):
            w, _ = wirkung(je_tag, mom, 1.0, "laengs",
                           verschiebe(lr, int(round(d))))
            nb = band(w, block, zieh=ZIEH_BAND, saat=SAAT)
            if nb:
                werte.append(nb[0])
    else:
        for z in range(ZIEHUNGEN_NULL):
            w, _ = wirkung(je_tag, mom, 1.0, "laengs", lr,
                           mische=np.random.default_rng(SAAT + z))
            nb = band(w, block, zieh=ZIEH_BAND, saat=SAAT + z)
            if nb:
                werte.append(nb[0])
    if len(werte) < ZIEHUNGEN_NULL // 2:
        return None
    bez = max(0.0, float(np.percentile(werte, N.NULL_PERZENTIL)))
    return bool(b[1] > bez)


def main() -> int:
    t0 = time.time()
    welten = WELTEN
    if "--welten" in sys.argv:
        welten = int(sys.argv[sys.argv.index("--welten") + 1])
    block = N._block(HORIZONT)

    print("=" * 104)
    print("N-46b — welcher LAENGS-Nullpunkt hat die richtige "
          "Fehlalarmquote?")
    print("=" * 104)
    print("  %d Nullwelten je Beharrlichkeit · Block %d · %d Ziehungen je "
          "Nullpunkt" % (welten, block, ZIEHUNGEN_NULL))
    print("  ⚠️ `staerke = 0` - die Kennzahl sagt NICHTS. Jedes TRAEGT "
          "ist ein Fehlalarm.")
    print("  ⚠️ `ueberlappung = %d` ist Pflicht (2.199), sonst ist jede "
          "Anlage zu praezise." % HORIZONT)
    print("  ⚠️⚠️ Kriterium VORAB: **naeher an %.1f %% gewinnt** - eine "
          "Quote, keine Rangfolge." % SOLL)

    ergebnis = {}
    for ak, wie in (() if "--nur-fund" in sys.argv else BEHARRLICHKEITEN):
        zaehler = {"verschub": [0, 0], "tagesmischung": [0, 0]}
        print()
        print("  BEHARRLICHKEIT %.3f (%s)" % (ak, wie))
        for i in range(welten):
            rng = np.random.default_rng(SAAT + i)
            je_tag, mom = SW.welt(rng, staerke=0.0, kennzahl_ak=ak,
                                  ueberlappung=HORIZONT)
            lr = laengs_rang(je_tag)
            if not lr:
                continue
            for art in ("verschub", "tagesmischung"):
                u = urteil(je_tag, mom, lr, block, art, rng)
                if u is None:
                    continue
                zaehler[art][1] += 1
                if u:
                    zaehler[art][0] += 1
            if (i + 1) % 10 == 0:
                print("     %d Welten ... Verschub %d/%d · Tagesmischung "
                      "%d/%d"
                      % (i + 1, zaehler["verschub"][0],
                         zaehler["verschub"][1],
                         zaehler["tagesmischung"][0],
                         zaehler["tagesmischung"][1]), flush=True)
        print("     %-16s %8s %10s %10s" % ("Nullmodell", "Fehlal.",
                                            "Quote", "Abstand zu 2,5 %"))
        for art in ("verschub", "tagesmischung"):
            treffer, gesamt = zaehler[art]
            if not gesamt:
                print("     %-16s nicht messbar" % art)
                continue
            q = 100.0 * treffer / gesamt
            ergebnis[(ak, art)] = q
            print("     %-16s %4d/%-3d %9.1f %% %14.1f"
                  % (art, treffer, gesamt, q, abs(q - SOLL)))

    # ---- Die FUNDQUOTE - ohne sie entscheidet die Fehlalarmquote nichts
    #
    # ⚠️⚠️ Am 09.09. verlor `null_oben` den Nullbezug-Vergleich NICHT an
    # der Fehlalarmquote (0 %, besser als das Soll), sondern an der
    # FUNDQUOTE (63 %). Ein Nullpunkt, der nie Alarm schlaegt, findet
    # auch nichts. Beide Quoten gehoeren zusammen.
    if "--nur-fehlalarm" not in sys.argv:
        print()
        print("=" * 104)
        print("DIE FUNDQUOTE — findet der Nullpunkt einen ECHTEN Effekt?")
        print("=" * 104)
        print("  Gepflanzt wird auf das oberste EIGENE Fuenftel, als "
              "LEITER: %s R"
              % " / ".join("%.2f" % x for x in LEITER))
        print("  ⚠️ In die DATEN, nicht ueber den `pflanze`-Parameter der "
              "Norm - sonst prueft sich")
        print("     der Mechanismus mit sich selbst (selbsttest_welt).")
        print("  ⚠️ 0,20 R fand im Vorabtest JEDES Modell (3/3) - ein zu "
              "grosser Effekt trennt nicht.")
        # ⚠️ EINE LEITER statt einer Staerke. Der Vorabtest zeigte bei
        # 0,20 R **100 % fuer beide** - ein zu grosser Effekt trennt
        # nicht. Getrennt wird dort, wo die Anlage an ihre Grenze kommt.
        for ak, wie in BEHARRLICHKEITEN:
            print()
            print("  BEHARRLICHKEIT %.3f (%s)" % (ak, wie))
            print("     %-10s %16s %16s" % ("gepflanzt", "Verschub",
                                            "Tagesmischung"))
            for staerke in LEITER:
                z = {"verschub": [0, 0], "tagesmischung": [0, 0]}
                for i in range(welten):
                    rng = np.random.default_rng(SAAT + 5000 + i)
                    je_tag, mom = SW.welt(rng, staerke=0.0, kennzahl_ak=ak,
                                          ueberlappung=HORIZONT)
                    lr = laengs_rang(je_tag)
                    if not lr:
                        continue
                    jep = pflanze_laengs(je_tag, lr, staerke)
                    for art in ("verschub", "tagesmischung"):
                        u = urteil(jep, mom, lr, block, art, rng)
                        if u is None:
                            continue
                        z[art][1] += 1
                        if u:
                            z[art][0] += 1
                zeile = []
                for art in ("verschub", "tagesmischung"):
                    tr, ges = z[art]
                    q = (100.0 * tr / ges) if ges else float("nan")
                    ergebnis[(ak, art, staerke)] = q
                    zeile.append("%10.1f %% (%d/%d)" % (q, tr, ges))
                print("     %8.2f R %s" % (staerke, " ".join(zeile)),
                      flush=True)

    # ---- Die Abnahme -----------------------------------------------------
    print()
    print("=" * 104)
    print("DIE ABNAHME — naeher an %.1f %% gewinnt" % SOLL)
    print("=" * 104)
    sieger = []
    for ak, wie in BEHARRLICHKEITEN:
        v = ergebnis.get((ak, "verschub"))
        t = ergebnis.get((ak, "tagesmischung"))
        if v is None or t is None:
            print("  %.3f (%s): nicht entscheidbar" % (ak, wie))
            continue
        # ⚠️⚠️ GLEICHSTAND DARF NICHT NACH REIHENFOLGE BRECHEN.
        # Der Vorabtest lieferte 0,0 %% gegen 0,0 %% - und `<` erklaerte
        # stillschweigend die Tagesmischung zum Sieger. Bei N Welten ist
        # die feinste unterscheidbare Quote 100/N; alles darunter ist
        # kein Unterschied, sondern Aufloesungsgrenze.
        feinheit = 100.0 / max(welten, 1)
        if abs(abs(v - SOLL) - abs(t - SOLL)) < feinheit:
            wer = "unentschieden"
        else:
            wer = ("verschub" if abs(v - SOLL) < abs(t - SOLL)
                   else "tagesmischung")
        sieger.append(wer)
        print("  %.3f (%s): Verschub %.1f %% · Tagesmischung %.1f %% "
              "-> %s   (Aufloesung %.1f %%)"
              % (ak, wie, v, t, wer.upper(), feinheit))
    print()
    if sieger and set(sieger) == {"unentschieden"}:
        print("  ⚠️⚠️ UNENTSCHIEDEN bei beiden Beharrlichkeiten - die "
              "beiden Nullmodelle sind in ihrer")
        print("     Fehlalarmquote NICHT unterscheidbar. Dann ist der "
              "Verschub Aufwand ohne Ertrag,")
        print("     und N-46 ist mit dem VORHANDENEN Werkzeug erledigt.")
    elif sieger and len(set(sieger)) == 1:
        print("  ✔ EINDEUTIG: %s trifft bei BEIDEN Beharrlichkeiten "
              "besser." % sieger[0].upper())
        print("     Damit ist N-46 entschieden - der Laengs-Nullpunkt "
              "steht.")
    elif sieger:
        print("  ⚠️⚠️ NICHT EINDEUTIG - die Beharrlichkeit entscheidet, "
              "welcher Nullpunkt besser trifft.")
        print("     Dann braucht die Laengs-Form einen Nullpunkt JE "
              "BEHARRLICHKEIT, und das waere ein eigener Befund.")
    print()
    print("  ⚠️ Liegen BEIDE weit ueber 2,5 %, ist die Laengs-Achse mit "
          "dieser Anlage nicht")
    print("     messbar - und N-46 waere nicht durch die Wahl des "
          "Nullpunkts zu loesen.")
    print("  Dauer %.1f Minuten" % ((time.time() - t0) / 60.0))
    return 0


if __name__ == "__main__":
    sys.exit(main())
