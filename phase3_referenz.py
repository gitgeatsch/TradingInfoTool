# -*- coding: utf-8 -*-
"""Phase 3, Punkt 5: TRAEGT `referenz_spy`? (20.09.2026)

Die letzte der vier ungemessenen Groessen aus 2.459-ungemessen, die
ueberhaupt messbar ist. Sie laeuft LIVE in der Faktenlage von Rolle BC,
ohne je geprueft worden zu sein - und das verletzt R-R4/P1:
*Verfuegbarkeit ist kein Aufnahmegrund.*

## Die registrierte Hypothese - sie stand schon da

    `referenz_spy (relative Staerke)`
    "Ein Wert, der besser laeuft als der breite Markt, laeuft weiter
     besser - relative Staerke gegen den S&P-500-ETF ueber 30 und 90 Tage."

⚠️ SIE WIRD ZITIERT, NICHT NEU FORMULIERT. Am 19.09. wurde die Stufe
`auswahl` gemessen, ohne dass ihre registrierte Hypothese auftauchte -
sie stand die ganze Zeit im Kandidatenblatt `momentum`. Das soll sich
nicht wiederholen (Schritt 64, Punkt C).

## ⚠️ DER MASSSTAB BLEIBT SPY - und das ist eine Entscheidung

Der S&P-500-ETF ist fuer Krypto ein fremder Massstab; BTC waere der
naheliegendere. Gemessen wird trotzdem SPY, denn das ist die Groesse, die
LIVE in den Prompt geht. Die Frage von M1-Kriterium 5 lautet *ist die
Eingabe gemessen*, nicht *waere eine andere Eingabe besser*. Wer den
Massstab vor der Messung tauscht, prueft die Groesse nicht, sondern
ersetzt sie - und haette hinterher zu keiner von beiden ein Urteil.

➔ Traegt SPY nicht, ist BTC die naechste Frage. Vorher nicht.

## ⚠️⚠️ DIE ECHTE FUNKTION RECHNET

`rollen_eingabe.relative_staerke` bildet Kalendertage auf Boersentage ab
(`_stand_am`: der juengste Schluss MIT Datum kleiner gleich, nie der
naechstgelegene - ein Feiertag darf nach hinten schieben, nie nach vorn)
und weist die Reihe zurueck, wenn sie mehr als 7 Tage zurueckhaengt.
Diese Abbildung nachzubauen waere genau die Falle, die am 19.09. zweimal
zugeschlagen hat (2.466, 2.479-eigene-fehler).

Damit sie die Messbasis sieht, wird eine WEGWERFDATENBANK mit der
SPY-Reihe unter dem Namen gebaut, den sie erwartet. Die Standard-DB wird
nicht angefasst.

⚠️ EINE Frage, EINE Zelle je Fenster (30 und 90 Tage sind zwei Fenster
DERSELBEN Groesse, so registriert). Stellvertretermenge (N3 b), ab 2023,
nur lesend, kein LLM.
"""
from __future__ import annotations

import os
import sqlite3
import sys
import tempfile
import time

import numpy as np

import bestand as BE
import messnorm
import messnorm_auswahl as MA
import messmenge
import phase3_reproduktion as R
from agent import rollen_eingabe as RE
from messe_beitrag_auf_auswahl import momentum250

AB = "2023-01-01"
MESSBASIS = "data/messdaten.db"
SPY = "SPY"
FENSTER = (30, 90)
MENGE = "20%"
LAGE = messnorm.Lage("spot", "einstieg")
VORBEHALT = ("gilt auf der Stellvertretermenge (N3 b); der Massstab ist "
             "SPY, weil er live gefuettert wird - nicht, weil er fuer Krypto "
             "der richtige waere")


class _Kerze:
    """Was `relative_staerke` von einer Reihe braucht: `date` und `close`.

    ⚠️ KEIN NACHBAU DER RECHNUNG - nur die Form. Die Messbasis liefert
    Tupel, die Betriebsfunktion erwartet Objekte."""

    __slots__ = ("date", "close")

    def __init__(self, datum, schluss):
        self.date = datum
        self.close = schluss


def hypothese() -> str:
    """Die registrierte Hypothese - GEZOGEN, nicht abgeschrieben."""
    for k in BE.KANDIDATEN:
        if k.name.startswith("referenz_spy"):
            return k.hypothese
    raise LookupError("kein Kandidatenblatt `referenz_spy` - ohne "
                      "registrierte Hypothese wird hier nicht gemessen")


def benchmark_datei() -> str:
    """Eine Wegwerfdatenbank mit der SPY-Reihe unter dem erwarteten Namen.

    ⚠️ Die Betriebsfunktion sucht `_THEMEN_ETF_BENCHMARK_SPY` in
    `price_history_ohlc`. In der Messbasis heisst dieselbe Reihe `SPY`.
    Statt die Funktion umzubauen, bekommt sie eine Datei, die aussieht wie
    die, die sie kennt."""
    ziel = os.path.join(tempfile.mkdtemp(prefix="tit_spy_"), "benchmark.db")
    quelle = sqlite3.connect("file:%s?mode=ro" % MESSBASIS, uri=True)
    try:
        zeilen = list(quelle.execute(
            "SELECT date, close FROM price_history_ohlc "
            "WHERE symbol = ? AND close IS NOT NULL ORDER BY date ASC",
            (SPY,)))
    finally:
        quelle.close()
    c = sqlite3.connect(ziel)
    try:
        c.execute("CREATE TABLE price_history_ohlc "
                  "(symbol TEXT, date TEXT, close REAL)")
        c.executemany("INSERT INTO price_history_ohlc VALUES (?,?,?)",
                      [(RE.BENCHMARK_SYMBOL, d, s) for d, s in zeilen])
        c.commit()
    finally:
        c.close()
    return ziel, len(zeilen), (zeilen[0][0] if zeilen else "-"), \
        (zeilen[-1][0] if zeilen else "-")


def je_tag_bauen(reihen: dict, pfad: str, tage: int) -> tuple[dict, dict]:
    """tag -> [{sym, kennzahl, in_r}] plus die Zaehlung der Ausfaelle."""
    aus: dict = {}
    zaehlung = {"anker": 0, "ohne_wert": 0}
    h = R.HORIZONT
    for sym, roh in reihen.items():
        kerzen = [_Kerze(z[0], z[1]) for z in roh]
        c = np.array([z[1] for z in roh], float)
        hoch = np.array([z[2] for z in roh], float)
        tief = np.array([z[3] for z in roh], float)
        breite = R.B.spanne(hoch, tief, c, R.B.SCHWANKUNG)
        for i in range(len(kerzen) - h):
            datum = str(kerzen[i].date)[:10]
            if datum < AB:
                continue
            r = breite[i]
            if not np.isfinite(r) or r <= 0:
                continue
            zaehlung["anker"] += 1
            # ⚠️ DIE BETRIEBSFUNKTION, mit der Messbasis als Vergleichsreihe.
            rel = RE.relative_staerke(kerzen, i, db=pfad, fenster=(tage,))
            wert = (rel or {}).get("rel_%d" % tage)
            if wert is None or not np.isfinite(float(wert)):
                zaehlung["ohne_wert"] += 1
                continue
            aus.setdefault(datum, []).append(
                {"sym": sym, "kennzahl": float(wert),
                 "in_r": float((c[i + h] - c[i]) / r)})
    return {t: z for t, z in aus.items() if len(z) >= 12}, zaehlung


def main() -> int:
    t0 = time.time()
    print("=" * 112)
    print("PHASE 3 · PUNKT 5 - TRAEGT `referenz_spy`?")
    print("=" * 112)
    print("  " + messmenge.zeile())
    print("  " + messnorm.standardzeile().replace("\n", "\n  "))
    print("\n  HYPOTHESE (registriert, Kandidatenblatt `referenz_spy`):")
    print("     " + hypothese())
    print("\n  ⚠️ %s" % VORBEHALT)

    pfad, n_spy, spy_von, spy_bis = benchmark_datei()
    print("\n  Vergleichsreihe: %d SPY-Punkte, %s bis %s" % (n_spy, spy_von,
                                                             spy_bis))
    if n_spy < 500:
        print("  ⚠️ zu kurz - Abbruch")
        return 1
    reihen = R.B.lade("krypto", "V1")
    mom = momentum250(reihen)
    print("  %d Kryptoreihen geladen (%.0f s)" % (len(reihen),
                                                  time.time() - t0))

    for tage in FENSTER:
        t1 = time.time()
        print("\n  %s" % ("-" * 108))
        print("  FENSTER %d TAGE" % tage)
        je_tag, z = je_tag_bauen(reihen, pfad, tage)
        ohne = 100.0 * z["ohne_wert"] / max(z["anker"], 1)
        print("     %d Tage mit Ankern · %d Anker geprueft, davon OHNE "
              "Vergleichswert %d (%.1f %%)"
              % (len(je_tag), z["anker"], z["ohne_wert"], ohne))
        if ohne > 50.0:
            # ⚠️ DIE ABDECKUNG STEHT VOR DEM URTEIL. Faellt die Haelfte der
            # Anker aus, misst man eine Teilmenge und nennt sie die Menge.
            print("     ⚠️⚠️ MEHR ALS DIE HAELFTE OHNE WERT - das Urteil "
                  "gaelte auf einer Teilmenge, nicht auf der Messmenge")
        if len(je_tag) < 2 * messnorm._block(R.HORIZONT):
            print("     zu wenige Tage (%d, %d noetig)"
                  % (len(je_tag), 2 * messnorm._block(R.HORIZONT)))
            continue
        try:
            b = MA.pruefe_auswahl(
                "referenz_spy_%d" % tage, je_tag, mom, lage=LAGE,
                menge=MENGE, rng=np.random.default_rng(messnorm.SAAT),
                horizont=R.HORIZONT, zielgroesse="bewegung_r",
                hypothese=hypothese(),
                verwendung="Block `referenz` im BC-Faktentext (laeuft live)")
        except ValueError as x:
            print("     ⚠️ von der Norm zurueckgewiesen: %s" % x)
            continue
        print("     " + b.zeile())
        if getattr(b, "urteil", None) is not None:
            print("     Urteil: %s" % b.urteil)
        print("     (%.0f s)" % (time.time() - t1))

    print("\n  LESEART")
    print("     Zielgroesse `bewegung_r` auf der selektierten Menge (%s) -"
          % MENGE)
    print("     ein Beitragsurteil auf der freien Menge weist die Norm ab")
    print("     (F-212).")
    print("     ⚠️ 30 und 90 Tage sind zwei Fenster DERSELBEN Groesse, so")
    print("        registriert - keine zwei Hypothesen.")
    print("\n  ⚠️ %s" % VORBEHALT)
    print("  (%.0f s)" % (time.time() - t0))
    print("=" * 112)
    return 0


if __name__ == "__main__":
    sys.exit(main())
