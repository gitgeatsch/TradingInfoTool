# -*- coding: utf-8 -*-
"""Phase 3, Punkt 3: WAS TRAEGT DIE STUFE `auswahl`? (19.09.2026)

M1-Kriterium 1 verlangt den Beitrag je Stufe als *mit gegen ohne*. Diese
Messung beantwortet ihn fuer die erste Stufe, die Auswahl.

    MIT     die obersten `anteil` nach 250-Tage-Momentum
    OHNE    alle WAEHLBAREN Anker des Tages

    Zielgroesse = median(bewegung_r der GEWAEHLTEN)
                - median(bewegung_r der WAEHLBAREN)

⚠️ WAEHLBAR heisst: mit 250-Tage-Momentumwert. Wer gegen ALLE Anker
vergleicht, nimmt Symbole in den Nenner, die nie haetten gewaehlt
werden koennen - das ist nicht ,mit gegen ohne die Stufe`, sondern
,mit gegen eine andere Menge` (korrigiert beim Pruefen, 19.09.2026).

⚠️⚠️ DAS IST EINE ANDERE FRAGE ALS F-182. Dort wurde die WIRKUNG im
Betrieb gemessen: die Auswahl laesst live null zusaetzliche Werte durch,
weil der Bestand ohnehin passiert und A1 nur zwei waehlt. Hier geht es um
die QUALITAET: ist die gewaehlte Menge besser als eine zufaellig gleich
grosse? Eine Stufe kann in der einen Frage null und in der anderen
tragend sein - wer beides verwechselt, zieht aus ,wirkt nicht` den
Schluss ,taugt nicht`.

⚠️ `phase3_kette.py` beantwortet das NICHT. Sie misst `median(frei) minus
median(gewaehlt)` - also die Sperren GEGEN die Auswahl. Die Auswahl
selbst steht dort im Nenner und wird nie geprueft.

## Die Nullwelt kommt aus der echten Funktion

`messe_beitrag_auf_auswahl._auswahl_maske` kennt `mische_auswahl`: damit
werden GLEICH VIELE Anker gewaehlt, nur zufaellig. Das ist genau die
Nullwelt, und sie ist nicht nachgebaut, sondern die Betriebsfunktion
selbst.

## ⚠️⚠️ MEHRFACHVERGLEICH - VORAB DEKLARIERT

Gemessen werden VIER Anteile (5, 10, 20, 50 %) bei H20. Das ist die
HAUPTFRAGE, und sie hat vier Zellen.

    Bei 2,5 % Fehlalarmtoleranz je Zelle liegt die Wahrscheinlichkeit,
    dass MINDESTENS EINE zufaellig TRAEGT sagt, bei rund 10 %.

`messnorm.Befund` fuehrt ein Feld `hypothesen` - es wird protokolliert,
aber nirgends verrechnet. Deshalb steht die Zahl hier und im Befund.

➔ GELESEN WIRD DER VERLAUF, NICHT DIE BESTE ZELLE. Eine Wirkung, die
ueber die Anteile glatt laeuft, ist etwas anderes als eine einzelne
Zelle, die heraussticht. Genau daran haette man den Fehlbefund vom
07.09. erkannt (`turnover` bei 20 % untermaechtig, bei 50 % positiv) -
und die Lehre daraus steht in `messnorm_auswahl.MENGEN`: *die Menge ist
kein Geschmack, sie folgt der Datenlage.*

H5 laeuft als ausdruecklich NACHRANGIGE Sondierung und wird getrennt
berichtet - sie gehoert nicht in den Hauptvergleich.

⚠️ Stellvertretermenge (N3 b), Fenster ab 2023, nur lesend, kein LLM.
"""
from __future__ import annotations

import sys
import time

import numpy as np

import messe_beitrag_auf_auswahl as A
import messnorm
import messmenge
import phase3_reproduktion as R
from messe_beitrag_auf_auswahl import momentum250
from messnorm_auswahl import MENGEN, MIND_ANKER
from n64_schnitt_stufen import band
# ⚠️ AUS DER VERKAUFSMESSUNG IMPORTIERT, NICHT KOPIERT. `urteil`,
# `blockpruefung` und `stabilitaet` sind dort am 19.09. entstanden und
# gelten fuer jede Messung dieser Bauart. Ein eigener Abzug waere die
# Kopierfalle; wenn ein dritter Leser dazukommt, ziehen sie in ein
# gemeinsames Modul um.
from phase3_verkaufsregel import blockpruefung, urteil
from phase3_verkaufsregel_basis import stabilitaet

AB = "2023-01-01"
# ⚠️⚠️ DER TRAEGER BESTIMMT DIE ANKERMENGE - GEFUNDEN BEIM PRUEFEN
# (19.09.2026). `messe_kandidaten_als_regel.baue` verwirft jede Zeile
# ohne Kennzahl (`if wert is None or not np.isfinite(wert): continue`).
# Gemessen: funding 211,8 Anker je Tag, oi_aenderung 87,8, turnover
# 50,0 - dagegen die kursbasierten: rsi 368,6, schnitt 347,9,
# momentum 338,7.
#
# Die erste Fassung nahm `funding` und hat die Auswahl damit auf der
# FUNDING-GEDECKTEN Teilmenge gemessen - eine Auswahl nach DATENLAGE
# (Regel 4), genau der Fehler, den G-6 vermeiden sollte. Der Traeger
# ist jetzt kursbasiert und deckt am breitesten ab; er liefert nur
# `in_r`, seine Kennzahl wird nie gelesen.
TRAEGER = "rsi"
TRAEGER_PROBE = "schnitt"     # Gegenprobe: das Ergebnis darf nicht am Traeger haengen
HAUPT = ("5%", "10%", "20%", "50%")
NEBEN_HORIZONT = 5
NULL_ZIEHUNGEN = messnorm.NULL_ZIEHUNGEN
VORBEHALT = ("gilt auf der Stellvertretermenge (N3 b), NICHT auf der "
             "Live-Menge - live waehlt A1 k=2 und der Bestand passiert "
             "immer (F-182)")


def wirkung(je_tag: dict, mom: dict, anteil: float, rng=None,
            pflanze: float = 0.0) -> dict:
    """tag -> median(gewaehlt) minus median(waehlbar), in R.

    `rng` macht daraus die NULLWELT - `_auswahl_maske` waehlt dann gleich
    viele Anker, aber zufaellig. Ohne sie misst man, DASS ausgewaehlt
    wurde, nicht WONACH."""
    aus = {}
    for tag, zeilen in je_tag.items():
        if tag < AB or len(zeilen) < MIND_ANKER:
            continue
        y = np.array([x["in_r"] for x in zeilen], float)
        if not np.isfinite(y).all():
            zeilen = [z for z, ok in zip(zeilen, np.isfinite(y)) if ok]
            y = y[np.isfinite(y)]
            if len(zeilen) < MIND_ANKER:
                continue
        # ⚠️⚠️ DER BEZUG SIND DIE WAEHLBAREN, NICHT ALLE - korrigiert beim
        # Pruefen (19.09.2026). `_auswahl_maske` kann nur Symbole waehlen,
        # die einen 250-Tage-Momentumwert haben; wer gegen ALLE vergleicht,
        # nimmt Symbole in den Nenner, die nie haetten gewaehlt werden
        # koennen. Das ist nicht ,mit gegen ohne die Stufe`, sondern ,mit
        # gegen eine andere Menge`.
        mt = mom.get(tag) or {}
        waehlbar = np.array([x["sym"] in mt for x in zeilen])
        if waehlbar.sum() < MIND_ANKER:
            continue
        m = A._auswahl_maske(zeilen, mt, anteil, rng)
        if m is None or m.sum() < 3 or m.sum() == int(waehlbar.sum()):
            continue
        y2 = y.copy()
        if pflanze:
            # ⚠️ GEPFLANZT WIRD IN DIE GEWAEHLTEN: sie werden besser
            # gemacht, die Auswahl also zu Recht gut. ⚠️ Die SEITE ist
            # hier - anders als bei einer Differenz zweier disjunkter
            # Gruppen - NICHT beliebig: die Gewaehlten stecken in `alle`
            # mit drin. Wer in `alle` pflanzt, hebt den Effekt teilweise
            # wieder auf (Lehre aus 2.476-positivkontrolle).
            y2[m] += pflanze
        aus[tag] = float(np.median(y2[m])) - float(np.median(y2[waehlbar]))
    return aus


def besetzung(je_tag: dict, mom: dict, anteil: float) -> tuple:
    """(Tage, gewaehlt je Tag, alle je Tag, kleinster Tag).

    ⚠️ STEHENDE VORGABE (07.09.2026): die Besetzung je Gruppe und Tag
    steht VOR der Deutung. Bei 5 % von 40 Ankern sind es zwei - genau der
    Bereich, in dem `median(Gruppe) minus median(Rest)` verzerrt."""
    g, a = [], []
    for tag, zeilen in je_tag.items():
        if tag < AB or len(zeilen) < MIND_ANKER:
            continue
        y = np.array([x["in_r"] for x in zeilen], float)
        zeilen = [z for z, ok in zip(zeilen, np.isfinite(y)) if ok]
        if len(zeilen) < MIND_ANKER:
            continue
        mt = mom.get(tag) or {}
        waehlbar = np.array([x["sym"] in mt for x in zeilen])
        if waehlbar.sum() < MIND_ANKER:
            continue
        m = A._auswahl_maske(zeilen, mt, anteil, None)
        if m is None or m.sum() < 3 or m.sum() == int(waehlbar.sum()):
            continue
        g.append(int(m.sum()))
        a.append(int(waehlbar.sum()))
    return (len(g), float(np.mean(g)) if g else float("nan"),
            float(np.mean(a)) if a else float("nan"),
            int(np.min(g)) if g else 0)


def messe(je_tag: dict, mom: dict, anteil: float, block: int) -> tuple:
    """Punkt, Nullwerte und Trennschaerfe - nach dem Messstandard."""
    echt = wirkung(je_tag, mom, anteil)
    if len(echt) < 2 * block:
        return echt, [], None
    nullwerte = []
    for i in range(NULL_ZIEHUNGEN):
        n = wirkung(je_tag, mom, anteil,
                    rng=np.random.default_rng(messnorm.SAAT + i))
        nb = band(n, block, zieh=300, saat=messnorm.SAAT + i)
        if nb:
            nullwerte.append(nb[0])
    oben = (float(np.percentile(nullwerte, messnorm.NULL_PERZENTIL))
            if nullwerte else float("nan"))
    ts = None
    for staerke in messnorm.STAERKEN:
        treffer = 0
        for i in range(messnorm.ZIEHUNGEN):
            pw = wirkung(je_tag, mom, anteil, pflanze=staerke)
            pb = band(pw, block, zieh=300, saat=messnorm.SAAT + 1000 + i)
            if pb and pb[1] > oben:
                treffer += 1
        if treffer >= max(3, (4 * messnorm.ZIEHUNGEN) // 5):
            ts = staerke
            break
    return echt, nullwerte, ts


def familienfehler(zellen: int, je_zelle: float = 0.025) -> float:
    """Wahrscheinlichkeit, dass MINDESTENS EINE Zelle zufaellig traegt.

    ⚠️ `messnorm.Befund` fuehrt `hypothesen` als Feld, verrechnet es aber
    nirgends. Solange das so ist, gehoert die Zahl in die Ausgabe - sonst
    liest sich eine von vier Zellen wie ein Einzelbefund."""
    return 1.0 - (1.0 - je_zelle) ** max(1, int(zellen))


def lauf(titel: str, je_tag: dict, mom: dict, horizont: int,
         anteile: tuple) -> None:
    block = messnorm._block(horizont)
    print("\n  %s" % ("-" * 108))
    print("  %s   ·   Horizont H%d · Block %d · %d Zellen · familienweiter "
          "Fehlalarm rund %.0f %%"
          % (titel, horizont, block, len(anteile),
             100 * familienfehler(len(anteile))))
    print("  %s" % ("-" * 108))
    print("     %-12s %9s %-22s %9s %5s   %s"
          % ("Anteil", "R", "Band", "Nullwelt", "Tage", "Urteil"))
    for name in anteile:
        anteil = MENGEN[name]
        echt, nullwerte, ts = messe(je_tag, mom, anteil, block)
        if len(echt) < 2 * block:
            print("     %-12s zu wenige Tage (%d, %d noetig)"
                  % (name, len(echt), 2 * block))
            continue
        urteil(name, echt, nullwerte, block, ts)
        tage, mg, ma, mn = besetzung(je_tag, mom, anteil)
        print("     %-12s Besetzung je Tag: gewaehlt %.1f (kleinster %d) von "
              "%.1f waehlbaren · Trennschaerfe %s · %s"
              % ("", mg, mn, ma, ("%.2f R" % ts) if ts else "KEINE",
                 blockpruefung(echt, block)))


def main() -> int:
    t0 = time.time()
    print("=" * 112)
    print("PHASE 3 · PUNKT 3 - WAS TRAEGT DIE STUFE `auswahl`?")
    print("=" * 112)
    print("  " + messmenge.zeile())
    print("  " + messnorm.standardzeile().replace("\n", "\n  "))
    print("  Zielgroesse: median(GEWAEHLT) minus median(ALLE) - POSITIV "
          "heisst, die Auswahl liefert die besseren Anker")
    print("  ⚠️ %s" % VORBEHALT)
    print("  ⚠️ Vorab deklariert: %d Zellen in der Hauptfrage, H%d als "
          "nachrangige Sondierung" % (len(HAUPT), NEBEN_HORIZONT))

    print("\n  Kursreihen laden ...")
    reihen = R.B.lade("krypto", "V1")
    mom = momentum250(reihen)
    print("  %d Reihen · %d Tage mit Momentum (%.0f s)"
          % (len(reihen), len(mom), time.time() - t0))

    je20 = R.K.baue(reihen, TRAEGER, None,
                    horizont=R.HORIZONT)
    lauf("HAUPTFRAGE", je20, mom, R.HORIZONT, HAUPT)

    # ---- Saatprobe an der knappsten Zelle -------------------------------
    #
    # ⚠️ NICHT AN ALLEN, SONDERN AN DER KNAPPSTEN (2.477-stabilitaet): die
    # Probe gehoert an die Grenze, nicht an jede Messung. Welche Zelle das
    # ist, entscheidet der Abstand Bandunterkante zu Nullgrenze.
    block = messnorm._block(R.HORIZONT)
    knapp, bester = None, None
    for name in HAUPT:
        anteil = MENGEN[name]
        echt, nullwerte, _ = messe(je20, mom, anteil, block)
        b = band(echt, block)
        if not b or not nullwerte:
            continue
        oben = float(np.percentile(nullwerte, messnorm.NULL_PERZENTIL))
        abstand = abs(b[1] - oben)
        if bester is None or abstand < bester:
            bester, knapp = abstand, (name, anteil, echt)
    if knapp is not None:
        name, anteil, echt = knapp
        print("\n  ⚠️ SAATPROBE an der knappsten Zelle (%s, Abstand %.4f R)"
              % (name, bester))
        print("     %s"
              % stabilitaet(echt,
                            lambda r, _j=je20, _m=mom, _a=anteil: wirkung(
                                _j, _m, _a, rng=r),
                            block))

    # ---- Traegerprobe ---------------------------------------------------
    #
    # ⚠️ DAS ERGEBNIS DARF NICHT AM TRAEGER HAENGEN. Er liefert nur `in_r`;
    # seine Kennzahl wird nie gelesen. Weicht die Trennschaerfe oder das
    # Vorzeichen ab, bestimmt die DATENLAGE des Traegers das Urteil - genau
    # der Fehler, der die erste Fassung auf die funding-gedeckte Teilmenge
    # gestellt hat.
    jep = R.K.baue(reihen, TRAEGER_PROBE, None, horizont=R.HORIZONT)
    print()
    print("  ⚠️ TRAEGERPROBE - dasselbe mit `%s` statt `%s`"
          % (TRAEGER_PROBE, TRAEGER))
    for name in HAUPT:
        anteil = MENGEN[name]
        e1 = band(wirkung(je20, mom, anteil), block)
        e2 = band(wirkung(jep, mom, anteil), block)
        t1 = besetzung(je20, mom, anteil)
        t2 = besetzung(jep, mom, anteil)
        print("     %-6s %s %+.4f (%.0f waehlbar)  ·  %s %+.4f (%.0f waehlbar)"
              "  ·  Abstand %.4f R"
              % (name, TRAEGER, e1[0] if e1 else float("nan"), t1[2],
                 TRAEGER_PROBE, e2[0] if e2 else float("nan"), t2[2],
                 abs((e1[0] if e1 else 0) - (e2[0] if e2 else 0))))

    # ---- Nachrangige Sondierung -----------------------------------------
    je5 = R.K.baue(reihen, TRAEGER, None,
                   horizont=NEBEN_HORIZONT)
    lauf("NACHRANGIG (Sondierung, nicht im Hauptvergleich)", je5, mom,
         NEBEN_HORIZONT, HAUPT)

    print("\n  LESEART")
    print("     R          median(gewaehlt) minus median(WAEHLBAR). POSITIV =")
    print("                die Auswahl liefert die besseren Anker.")
    print("     Nullwelt   gleich viele gewaehlt, aber ZUFAELLIG "
          "(%d Ziehungen)." % NULL_ZIEHUNGEN)
    print("     ⚠️ Gelesen wird der VERLAUF ueber die Anteile, nicht die")
    print("        beste Zelle - bei %d Zellen traegt rund %.0f %% davon"
          % (len(HAUPT), 100 * familienfehler(len(HAUPT))))
    print("        zufaellig.")
    print("     ⚠️ Das beantwortet die QUALITAETSfrage. Die WIRKUNG im")
    print("        Betrieb ist eine andere und steht in F-182: null")
    print("        zusaetzliche Werte, weil der Bestand ohnehin passiert.")
    print("\n  ⚠️ %s" % VORBEHALT)
    print("  (%.0f s)" % (time.time() - t0))
    print("=" * 112)
    return 0


if __name__ == "__main__":
    sys.exit(main())
