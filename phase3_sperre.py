# -*- coding: utf-8 -*-
"""Phase 3: DIE WIEDERHOLUNGSSPERRE MESSEN (18.09.2026, Schritt 59).

Die Sperre ist die groesste Verlustquelle der Kette - im NB-Export vom 18.09.
verliert sie 154 von 372 Zellen (41 %) und **100 % derer, die `anlass` und
`auswahl` ueberlebt haben**. Kein einziger ihrer sechs Werte hat einen Befund;
`VORGABE_JE_STRATEGIE` traegt im Code den Vermerk *"GESETZT, NICHT GEMESSEN"*.

⚠️⚠️ WAS SICH HIER UEBERHAUPT MESSEN LAESST - UND WAS NICHT.

Die Messbasis ist TAEGLICH (`price_history_ohlc` hat die Spalte `date`;
Intraday-Daten gibt es in keiner der 13 Projektdatenbanken). Daraus folgt
zwingend:

    3,5 h (Hebel)          NICHT messbar - unter der Aufloesung
    15 h (Spot), 24 h      nicht von "keine Sperre" unterscheidbar, weil das
                           Tagesraster ohnehin nur einmal je Symbol und Tag
                           fragt
    48 h (Akkumulation)    messbar = EIN Tag Pause
    alles darueber         messbar

Die Frage lautet deshalb nicht "sind 15 h richtig", sondern:

    ⚠️ IST EINE SPERRE, DIE UEBER EINEN TAG HINAUSGEHT, BEGRUENDET -
       ODER KOSTET SIE NUR?

Das trifft genau den einen Wert, der im Code selbst als ungemessen markiert
ist. Ein Vorschlag, der die 15 h "misst", waere eine Scheinmessung.

## Der Aufbau

Aufgesetzt auf `phase3_kette.py` (Befund 2.460-kette, Urteil TRAEGT). Die
Sperre kommt als WEITERE Stufe hinein, an derselben Stelle wie live:

    Stufe 5   Auswahl (oberste 20 % nach 250-Tage-Momentum)
    Stufe 12  funding, turnover, oi_aenderung
    NEU       Sperre: wer an Tag d durchkam, ist an d+1 .. d+k gesperrt

Das bildet die Live-Regel ab, die JEDES Urteil sperrt, auch ein NICHTS_TUN
(`wiederholung.gesperrt_bis`, korrigiert 14.08.).

⚠️ DIE NULLWELT SPERRT GLEICH VIELE, ABER ZUFAELLIG GEWAEHLTE. Der Unterschied
ist das, was "sperre, was ich gerade gefragt habe" gegenueber "sperre
irgendetwas" leistet. Gegen null zu messen wuerde die Mechanik des Sperrens
messen, nicht die Sperre (Messstandard 09.09.).

⚠️ GEMEINSAMES ZEITFENSTER: alle Sperrlaengen werden auf DENSELBEN Tagen
ausgewertet. Sonst vergleicht man Laengen auf verschiedenen Maerkten.

⚠️ STELLVERTRETERMENGE (N3 b): gilt NICHT auf der Live-Menge (Blocker A8).
⚠️ Nur lesend, kein LLM, kein Kontingent.
"""
from __future__ import annotations

import sys
import time

import numpy as np

import messnorm
import messmenge
import phase3_kette as PK
import phase3_reproduktion as R
from messe_beitrag_auf_auswahl import momentum250
from messnorm_auswahl import MENGEN
from n64_schnitt_stufen import band

STUFEN = ("funding", "turnover", "oi_aenderung")
MENGE = "20%"
# Sperrlaengen in TAGEN. 0 = keine Sperre (der Stand von Befund 2.460-kette),
# 1 = die 48 h der Akkumulation, alles weitere ist die Frage, ob laenger hilft.
LAENGEN = (0, 1, 2, 3, 5, 10, 20)
MINDEST_FREI = 3
VORBEHALT = "gilt auf der Stellvertretermenge, NICHT auf der Live-Menge (N3 b)"


def _tage_bauen(w: dict, mom: dict, anteil: float) -> list:
    """Die Kette EINMAL rechnen - sie haengt nicht von der Sperrlaenge ab.

    ⚠️ Das ist keine Abkuerzung, sondern der Punkt: gemessen wird die SPERRE,
    also muss alles davor fest stehen. Waere die Kette je Durchgang neu
    gewuerfelt, steckte ihr Rauschen im Ergebnis der Sperre."""
    aus = []
    for tag, zeilen in w[STUFEN[0]].items():
        gebaut = PK.tag_maske(w, mom, anteil, STUFEN, tag, zeilen)
        if gebaut is None:
            continue
        syms, y, m, frei = gebaut
        if frei.sum() < MINDEST_FREI or m.sum() == frei.sum():
            continue
        aus.append((tag, syms, y, m, frei))
    aus.sort(key=lambda x: x[0])
    return aus


def sperre(tage: list, k: int, *, rng=None, pflanze: float = 0.0,
           zahlen: dict | None = None) -> tuple[dict, dict]:
    """Die Sperre ueber die Tage. Gibt (Wirkung je Tag, Zaehlung) zurueck.

    `k` ist die Sperrlaenge in Tagen: wer an Tag d durchkam, ist an d+1 bis
    d+k gesperrt. `rng` macht daraus die NULLWELT - dann werden gleich viele
    gesperrt, aber zufaellig gewaehlte; wie viele, sagt `zahlen`.

    ⚠️ DIE UHR LAEUFT JE SYMBOL, nicht je Tag: der Abstand zaehlt zum letzten
    Tag, an dem das Symbol DURCHKAM - genau wie live, wo `gesperrt_bis` auf
    das juengste Signal sieht."""
    aus: dict = {}
    z = {"uebrig": [], "gesperrt": [], "anteil": []}
    zuletzt: dict = {}
    for i, (tag, syms, y, m, frei) in enumerate(tage):
        offen = np.where(frei)[0]
        if rng is None:
            # Die echte Sperre: was zuletzt gefragt wurde, ist dran.
            blockiert = np.array(
                [j for j in offen if i - zuletzt.get(syms[j], -10**9) <= k],
                dtype=int)
        else:
            # Die Nullwelt: gleich viele, aber ohne Information.
            n = int((zahlen or {}).get(tag, 0))
            n = min(n, len(offen))
            blockiert = (rng.choice(offen, n, replace=False) if n
                         else np.array([], dtype=int))
        frei_k = frei.copy()
        frei_k[blockiert] = False
        z["gesperrt"].append(int(len(blockiert)))
        # ⚠️⚠️ DIE UHR WIRD VOR DER WERTUNG GESTELLT (korrigiert 18.09.2026,
        # gefunden beim Schreiben der Gegenpruefung).
        #
        # Hier stand der `continue` VOR dieser Schleife, mit dem Kommentar
        # "die Uhr laeuft trotzdem weiter" - sie lief eben NICHT. An einem
        # Tag, der aus der Wertung fiel, wurde nicht vermerkt, dass gefragt
        # wurde; am Folgetag war dasselbe Symbol wieder frei. Die Sperre war
        # damit im Modell schwaecher als live, und zwar ausgerechnet bei den
        # langen Laengen, wo die duennen Tage haeufig sind.
        #
        # LIVE GEFRAGT WIRD UNABHAENGIG DAVON, ob wir den Tag messen koennen.
        for j in np.where(frei_k)[0]:
            zuletzt[syms[j]] = i
        if frei_k.sum() < MINDEST_FREI:
            continue                 # zu duenn fuer einen Median - kein Wert
        z["uebrig"].append(int(frei_k.sum()))
        z["anteil"].append(float(len(blockiert)) / max(int(frei.sum()), 1))
        y2 = y.copy()
        if pflanze:
            # ⚠️ GEPFLANZT WIRD IN DIE GESPERRTEN - dieselbe Konstruktion wie
            # in `messnorm` und `phase3_kette`: die Sperre wird dadurch zu
            # Recht streng. Auf die Freien zu pflanzen hiesse, den eigenen
            # Effekt zu messen (messnorm 06.09.).
            y2[blockiert] -= pflanze
        aus[tag] = float(np.median(y2[frei_k])) - float(np.median(y2[m]))
    return aus, z


def _auf(d: dict, tage_menge: set) -> dict:
    return {t: v for t, v in d.items() if t in tage_menge}


def main() -> int:
    vorab = "--vorab" in sys.argv[1:]
    ziehungen = 5 if vorab else messnorm.NULL_ZIEHUNGEN
    laengen = (0, 1, 20) if vorab else LAENGEN
    t0 = time.time()
    print("=" * 100)
    print("PHASE 3 - DIE WIEDERHOLUNGSSPERRE" + ("  [VORABTEST]" if vorab else ""))
    print("=" * 100)
    print("  " + messmenge.zeile())
    print("  Fenster ab %s · Menge %s · Horizont H%d · %d Nullziehungen"
          % (PK.AB, MENGE, R.HORIZONT, ziehungen))
    print("  ⚠️ Die Messbasis ist TAEGLICH - 3,5 h und 15 h liegen unter der")
    print("     Aufloesung und werden hier NICHT gemessen (siehe Modulkopf).")
    print("  ⚠️ %s" % VORBEHALT)

    print("\n  Kursreihen laden ...")
    reihen = R.B.lade("krypto", "V1")
    mom = momentum250(reihen)
    w = {a: R.K.baue(reihen, a, R._zusatz(a), horizont=R.HORIZONT)
         for a in STUFEN}
    tage = _tage_bauen(w, mom, MENGEN[MENGE])
    print("  %d Reihen · %d Tage in der Kette (%.0f s)"
          % (len(reihen), len(tage), time.time() - t0))
    if len(tage) < 60:
        print("  ⚠️ zu wenige Tage - kein Urteil")
        return 1

    block = messnorm._block(R.HORIZONT)
    # ---- GEMEINSAMES ZEITFENSTER -----------------------------------------
    roh = {k: sperre(tage, k) for k in laengen}
    gemeinsam = set(roh[laengen[0]][0])
    for k in laengen:
        gemeinsam &= set(roh[k][0])
    print("  gemeinsame Tage ueber alle Sperrlaengen: %d" % len(gemeinsam))

    # ⚠️⚠️ DIE SPALTE "roh R" IST ZWISCHEN SPERRLAENGEN NICHT VERGLEICHBAR -
    # gefunden im Vorabtest am 18.09.2026, und die Messung waere ohne diesen
    # Satz falsch gelesen worden.
    #
    # Die Zielgroesse ist ein MEDIAN ueber die freien Anker. Je schaerfer die
    # Sperre, desto kleiner die Stichprobe je Tag (26 -> 15 -> 4), und der
    # Median einer kleinen Stichprobe aus einer rechtsschiefen Verteilung
    # liegt systematisch ZU HOCH. Die Nullwelt zeigt genau das, ganz ohne
    # Information: bei 20 Tagen Sperre steigt sie auf +0,13, waehrend die
    # Kette ohne Sperre +0,03 misst.
    #
    # ⚠️ VERGLEICHBAR IST NUR "entzerrt" - jede Sperrlaenge gegen IHRE EIGENE
    # Nullwelt, die dieselbe Stichprobengroesse hat.
    print("\n  %-8s %10s %26s %11s %11s %9s %6s"
          % ("Sperre", "roh R", "Band", "Nullwelt", "entzerrt", "Anker/Tag",
             "Tage"))
    erg = {}
    for k in laengen:
        echt, z = roh[k]
        echt = _auf(echt, gemeinsam)
        e = band(echt, block)
        if e is None:
            print("  %-8s zu wenige Tage (%d)" % ("%d Tage" % k, len(echt)))
            continue
        if k == 0:
            nw, nulls, nulls_eigen = 0.0, [], []
        else:
            # ⚠️ JE TAG, NICHT JE GEWERTETEM TAG: `z["gesperrt"]` hat einen
            # Eintrag fuer JEDEN Tag in `tage` (auch fuer die, die aus der
            # Wertung fielen) - die Nullwelt muss dieselbe Reihe treffen.
            zahlen = dict(zip([x[0] for x in tage], z["gesperrt"]))
            # ⚠️⚠️ DIESELBEN ZIEHUNGEN, ZWEI FENSTER (18.09., nach dem
            # Vorabtest). Das URTEIL gehoert auf die eigenen Tage der Laenge:
            # dort haben echte Sperre und Nullwelt dieselben Tage und
            # dieselbe Stichprobengroesse, und es geht kein Tag verloren.
            # Das gemeinsame Fenster braucht es nur fuer den Vergleich DER
            # LAENGEN untereinander - es wird von der schaerfsten diktiert.
            nulls, nulls_eigen = [], []
            for i in range(ziehungen):
                n_d, _ = sperre(tage, k, zahlen=zahlen,
                                rng=np.random.default_rng(messnorm.SAAT + i))
                nb = band(_auf(n_d, gemeinsam), block, zieh=300,
                          saat=messnorm.SAAT + i)
                if nb:
                    nulls.append(nb[0])
                ne = band(n_d, block, zieh=300, saat=messnorm.SAAT + i)
                if ne:
                    nulls_eigen.append(ne[0])
            nw = float(np.mean(nulls)) if nulls else 0.0
        eigen = band(roh[k][0], block)
        erg[k] = {"roh": e[0], "band": (e[1], e[2]), "null": nw,
                  "nulls": nulls, "nulls_eigen": nulls_eigen,
                  "entzerrt": e[0] - nw,
                  "uebrig": float(np.mean(z["uebrig"])) if z["uebrig"] else 0.0,
                  "anteil": float(np.mean(z["anteil"])) if z["anteil"] else 0.0,
                  "tage": len(echt),
                  "eigen": (eigen[0] if eigen else float("nan")),
                  "eigen_tage": len(roh[k][0])}
        print("  %-8s %+10.4f [%+.4f .. %+.4f] %+11.4f %+11.4f %9.1f %6d"
              % ("%d Tage" % k, e[0], e[1], e[2], nw, e[0] - nw,
                 erg[k]["uebrig"], erg[k]["tage"]), flush=True)

    # ---- DIE ZAEHLUNG VOR DER DEUTUNG ------------------------------------
    print("\n  DIE ZAEHLUNG VOR DER DEUTUNG - was jede Sperrlaenge KOSTET")
    print("  %-8s %12s %14s %16s" % ("Sperre", "Anker/Tag", "gesperrt %", "gegen 0 Tage"))
    grund = erg.get(0, {}).get("uebrig") or 1.0
    for k in laengen:
        if k not in erg:
            continue
        print("  %-8s %12.1f %13.0f %% %15.0f %%"
              % ("%d Tage" % k, erg[k]["uebrig"], 100.0 * erg[k]["anteil"],
                 100.0 * (erg[k]["uebrig"] / grund - 1.0)))
    # ⚠️ DAS GEMEINSAME FENSTER WIRD VON DER SCHAERFSTEN SPERRE DIKTIERT:
    # bei 20 Tagen bleiben an vielen Tagen weniger als drei Anker, und diese
    # Tage fallen fuer ALLE Laengen aus der Wertung. Was jede Laenge auf
    # IHREN eigenen Tagen misst, steht deshalb daneben - nicht als Ersatz,
    # sondern damit sichtbar ist, was das gemeinsame Fenster kostet.
    print("\n  Dasselbe auf den EIGENEN Tagen je Laenge (nicht untereinander"
          " vergleichbar)")
    print("  %-8s %12s %12s" % ("Sperre", "roh R", "Tage"))
    for k in laengen:
        if k not in erg:
            continue
        print("  %-8s %+12.4f %12d"
              % ("%d Tage" % k, erg[k]["eigen"], erg[k]["eigen_tage"]))

    # ---- DAS NORMURTEIL JE SPERRLAENGE -----------------------------------
    #
    # ⚠️ ANWENDUNG DER NORM, KEINE NACHBILDUNG: Nullpunkt, Perzentil,
    # Staerkenleiter und Ziehungszahl kommen aus `messnorm`.
    print("\n  DAS NORMURTEIL JE SPERRLAENGE")
    print("  Bezug: %s · Nullpunkt = Mittel der Nullwelten (%d. Perzentil als"
          " obere Grenze)" % (messnorm.NULLBEZUG, messnorm.NULL_PERZENTIL))
    print("  ⚠️ Gewertet wird auf den EIGENEN Tagen der Laenge - echte Sperre")
    print("     und Nullwelt haben dort dieselben Tage und dieselbe"
          " Stichprobengroesse.")
    for k in laengen:
        if k == 0 or k not in erg or not erg[k]["nulls_eigen"]:
            continue
        nulls = erg[k]["nulls_eigen"]
        null_oben = float(np.percentile(nulls, messnorm.NULL_PERZENTIL))
        # ⚠️ DIE GEGENRICHTUNG GEHOERT DAZU (18.09.2026). Die Norm fragt, ob
        # eine Groesse TRAEGT - sie hat keine Frage dafuer, ob eine Stufe
        # SCHADET. Bei einer Sperre, die 43 bis 84 % der Anker verwirft, ist
        # das aber die eigentliche Frage. Unter dem unteren Perzentil ihrer
        # eigenen Nullwelt heisst: sie sperrt schlechter als der Zufall.
        null_unten = float(np.percentile(nulls, 100.0 - messnorm.NULL_PERZENTIL))
        null_mittel = float(np.mean(nulls))
        zahlen = dict(zip([x[0] for x in tage], roh[k][1]["gesperrt"]))
        trennschaerfe = None
        leiter = []
        for staerke in messnorm.STAERKEN:
            treffer = 0
            for i in range(messnorm.ZIEHUNGEN):
                pw, _ = sperre(tage, k, pflanze=staerke)
                pb = band(pw, block, zieh=300,
                          saat=messnorm.SAAT + 1000 + i)
                if pb and pb[0] > null_oben:
                    treffer += 1
            gefunden = treffer >= max(3, (4 * messnorm.ZIEHUNGEN) // 5)
            leiter.append("%.2f:%d/%d%s" % (staerke, treffer,
                                            messnorm.ZIEHUNGEN,
                                            "*" if gefunden else ""))
            if gefunden and trennschaerfe is None:
                trennschaerfe = staerke
        wirkung = erg[k]["eigen"] - null_mittel
        if trennschaerfe is None:
            urteil = "KEIN URTEIL - die Positivkontrolle findet nichts"
        elif erg[k]["eigen"] > null_oben and wirkung >= trennschaerfe:
            urteil = "TRAEGT"
        elif erg[k]["eigen"] > null_oben:
            urteil = ("TRAEGT NICHT bis %.2f R (Wirkung %+.4f entzerrt, aber "
                      "ueber dem Nullpunkt)" % (trennschaerfe, wirkung))
        elif erg[k]["eigen"] < null_unten:
            urteil = ("TRAEGT NICHT - und liegt UNTER dem unteren Perzentil "
                      "ihrer eigenen Nullwelt: sie sperrt schlechter als der "
                      "Zufall (%+.4f gegen %+.4f)"
                      % (erg[k]["eigen"], null_unten))
        else:
            urteil = "TRAEGT NICHT - nicht ueber dem Nullpunkt"
        print("   %2d Tage · Null %+.4f [%+.4f .. %+.4f] · gemessen %+.4f · "
              "Leiter %s" % (k, null_mittel, null_unten, null_oben,
                             erg[k]["eigen"], " ".join(leiter)))
        print("            Trennschaerfe %s · ⚠️ URTEIL: %s"
              % ("%.2f R" % trennschaerfe if trennschaerfe else "KEINE",
                 urteil))

    print("\n  ⚠️ WAS DIESE MESSUNG NICHT SAGT:")
    print("     - nichts ueber 3,5 h und 15 h (unter der Tagesaufloesung)")
    print("     - nichts ueber die Trennung der Uhren je Zelle - das ist eine")
    print("       Bauentscheidung, keine Messfrage (die Messbasis kennt keine")
    print("       Strategien je Symbol)")
    print("     - %s" % VORBEHALT)
    print("\n  (%.0f s gesamt)" % (time.time() - t0))
    print("=" * 100)
    return 0


if __name__ == "__main__":
    sys.exit(main())
