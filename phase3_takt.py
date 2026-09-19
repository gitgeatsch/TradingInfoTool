# -*- coding: utf-8 -*-
"""S3: WAS KOSTET WARTEN? (19.09.2026, Schritt 59)

Die Wiederholungssperre verwirft 39 % aller Zellen - und zwar ausschliesslich
solche, bei denen sich etwas GEAENDERT hatte (sie sitzt hinter `anlass`).
Gemessen ist, dass sie dabei nicht besser waehlt als der Zufall
(2.461-sperre). Offen ist die andere Haelfte der Frage:

    ⚠️ WAS KOSTET ES, EINE BEWERTUNG UM k STUNDEN ZU VERSCHIEBEN?

Denn genau das tut jede Sperre und jeder Takt. Kostet Warten nichts, ist die
Sperre nur Verwaltung; kostet es viel, ist sie teuer bezahlt.

## Die Datenlage - und warum sie neu ist

Bis zum 18.09. galt diese Frage als unmessbar (2.461-sperre-aufloesung).
Das war falsch: `price_cache` der Produktion fuehrt 15-MINUTEN-KURSE fuer
60 Symbole ueber 71 Tage, lueckenlos (2.463-datenlage-intraday).

⚠️⚠️ DIE BASIS IST KURZ UND SCHMAL. 71 Tage sind EIN Marktregime, gegen
1.327 Tage der Normbasis; 60 Symbole statt 536; Punktkurse ohne Hoch/Tief.
Was hier herauskommt, ist ein HINWEIS mit ausgewiesener Basis, KEIN
Normurteil - und nach R-R11 kann es keinen Tagesbefund umstossen.

## Der Aufbau

Fuer jedes echte Signal der Rollen-Kette: der Kurs zum Signalzeitpunkt und
der Kurs k Stunden spaeter, gerechnet in R (R = `stop_ziel_atr` x ATR14).

    Vorzeichen  positiv = der Kurs ist gestiegen, Warten war teuer
                (bei KAUFEN; bei VERKAUFEN gedreht)

⚠️ DIE NULLWELT SIND ZUFAELLIGE ZEITPUNKTE DESSELBEN SYMBOLS im selben
Zeitraum. Ohne sie misst man den Markt, nicht unsere Zeitpunkte: wenn alles
steigt, "kostet" Warten ueberall - das sagt ueber die Sperre nichts.

⚠️ Nur lesend, gegen die Tagessicherung der Produktion. Kein LLM.
"""
from __future__ import annotations

import bisect
import collections
import datetime as dt
import gzip
import os
import shutil
import sqlite3
import sys
import tempfile

import numpy as np

SICHERUNG = ("K:/My Drive/Claude_Austauschordner/DB_Backups/"
             "tradinginfotool_2026-09-18_2320.db.gz")
MESSDATEN = "data/messdaten.db"
STUNDEN = (0.25, 1.0, 3.0, 6.0, 12.0, 24.0)
STOP_ATR = 2.5                      # `stop_ziel_atr`, Befund vom 17.09.
ATR_TAGE = 14
NULL_ZIEHUNGEN = 40
SAAT = 20260919
TOLERANZ_MIN = 20.0                 # wie weit ein Kurspunkt vom Ziel weg darf
VORBEHALT = ("HINWEIS, kein Normurteil: 71 Tage, ein Marktregime, 60 Symbole, "
             "Punktkurse ohne Hoch/Tief - eine ANDERE Basis als die Normbasis "
             "(R-R11)")


def _oeffne_sicherung() -> sqlite3.Connection:
    z = os.path.join(tempfile.mkdtemp(), "nb.db")
    with gzip.open(SICHERUNG, "rb") as ein, open(z, "wb") as aus:
        shutil.copyfileobj(ein, aus)
    return sqlite3.connect("file:%s?mode=ro" % z.replace("\\", "/"), uri=True)


def _zeit(x) -> dt.datetime | None:
    s = str(x or "").replace("T", " ")[:19]
    try:
        return dt.datetime.fromisoformat(s)
    except ValueError:
        return None


def lade_kurse(con) -> dict:
    """symbol -> (Liste der Zeitpunkte, Liste der Kurse). 15-Minuten-Raster."""
    aus: dict = collections.defaultdict(list)
    for sym, ts, preis in con.execute(
            "SELECT symbol, fetched_at, price_eur FROM price_cache"
            " WHERE price_eur IS NOT NULL ORDER BY symbol, fetched_at"):
        t = _zeit(ts)
        if t is not None:
            aus[sym].append((t, float(preis)))
    return {s: ([x[0] for x in v], [x[1] for x in v])
            for s, v in aus.items() if len(v) > 200}


def lade_atr() -> dict:
    """symbol -> ATR14 als ANTEIL des Kurses (relativ, damit vergleichbar)."""
    if not os.path.exists(MESSDATEN):
        return {}
    con = sqlite3.connect("file:%s?mode=ro" % MESSDATEN, uri=True)
    aus = {}
    for sym, in con.execute("SELECT DISTINCT symbol FROM price_history_ohlc"):
        r = con.execute(
            "SELECT high, low, close FROM price_history_ohlc"
            " WHERE symbol = ? ORDER BY date DESC LIMIT ?",
            (sym, ATR_TAGE + 1)).fetchall()
        if len(r) < ATR_TAGE:
            continue
        h = np.array([x[0] for x in r], float)
        t = np.array([x[1] for x in r], float)
        c = np.array([x[2] for x in r], float)
        if not np.all(np.isfinite(c)) or c[0] <= 0:
            continue
        # ⚠️ ECHTE True Range: auch die Luecke zum Vortagesschluss zaehlt.
        tr = np.maximum(h[:-1] - t[:-1],
                        np.maximum(np.abs(h[:-1] - c[1:]),
                                   np.abs(t[:-1] - c[1:])))
        atr = float(np.mean(tr))
        if atr > 0:
            aus[sym] = atr / float(c[0])
    con.close()
    return aus


def kurs_bei(zeiten: list, preise: list, ziel: dt.datetime) -> float | None:
    """Der naechstgelegene Kurspunkt - oder None, wenn zu weit weg.

    ⚠️ MIT TOLERANZ, NICHT MIT INTERPOLATION: ein erfundener Zwischenwert
    saehe aus wie eine Messung. Fehlt der Punkt, faellt der Fall weg."""
    i = bisect.bisect_left(zeiten, ziel)
    beste = None
    for j in (i - 1, i):
        if 0 <= j < len(zeiten):
            ab = abs((zeiten[j] - ziel).total_seconds()) / 60.0
            if ab <= TOLERANZ_MIN and (beste is None or ab < beste[0]):
                beste = (ab, preise[j])
    return None if beste is None else beste[1]


def bewegung(kurse: dict, atr: dict, anker: list) -> dict:
    """Je Horizont: die Bewegung in R, richtungsbereinigt.

    `anker` ist eine Liste (symbol, zeitpunkt, richtung), richtung +1 fuer
    Kaufen (steigt der Kurs, war Warten teuer) und -1 fuer Verkaufen."""
    aus = {k: [] for k in STUNDEN}
    for sym, t0, richtung in anker:
        reihe = kurse.get(sym)
        r_einheit = atr.get(sym)
        if not reihe or not r_einheit:
            continue
        p0 = kurs_bei(reihe[0], reihe[1], t0)
        if not p0:
            continue
        for k in STUNDEN:
            p1 = kurs_bei(reihe[0], reihe[1], t0 + dt.timedelta(hours=k))
            if not p1:
                continue
            # Bewegung als Anteil, geteilt durch die Stopweite = R
            aus[k].append(richtung * (p1 - p0) / p0 / (STOP_ATR * r_einheit))
    return aus


def main() -> int:
    print("=" * 100)
    print("S3 - WAS KOSTET WARTEN? (Bewegung in R nach k Stunden)")
    print("=" * 100)
    print("  ⚠️ %s" % VORBEHALT)
    print("\n  Sicherung oeffnen ...")
    con = _oeffne_sicherung()
    kurse = lade_kurse(con)
    print("  %d Symbole mit 15-Minuten-Kursen" % len(kurse))
    atr = lade_atr()
    print("  %d Symbole mit ATR%d aus der Messbasis" % (len(atr), ATR_TAGE))

    # ---- Die echten Anker: Signale der Rollen-Kette ----------------------
    anker = []
    for sym, ts, aktion in con.execute(
            "SELECT symbol, created_at, action FROM signals"
            " WHERE quelle_kette = 'rollen' AND created_at >= '2026-07-06'"):
        t = _zeit(ts)
        a = str(aktion or "").upper()
        if t is None:
            continue
        # ⚠️ RICHTUNG AUS DER AKTION, nicht aus dem Vorzeichen des Ergebnisses
        # - sonst misst man sich selbst (die Gleichtagsfalle, 2.444er Reihe).
        if a in ("KAUFEN", "NACHKAUFEN"):
            anker.append((sym, t, +1.0))
        elif a in ("VERKAUFEN", "REDUZIEREN"):
            anker.append((sym, t, -1.0))
    print("  %d Signale als Anker (Kauf und Verkauf, richtungsbereinigt)"
          % len(anker))

    echt = bewegung(kurse, atr, anker)

    # ---- Die Nullwelt: zufaellige Zeitpunkte derselben Symbole -----------
    rng = np.random.default_rng(SAAT)
    symbole = sorted({s for s, _, _ in anker if s in kurse and s in atr})
    spanne = [t for _, t, _ in anker]
    if not spanne or not symbole:
        print("  ⚠️ zu wenige Anker - kein Ergebnis")
        return 1
    von, bis = min(spanne), max(spanne)
    dauer = (bis - von).total_seconds()
    null_je_k = {k: [] for k in STUNDEN}
    for i in range(NULL_ZIEHUNGEN):
        zufall = []
        for sym, _, richtung in anker:
            if sym not in kurse or sym not in atr:
                continue
            t = von + dt.timedelta(seconds=float(rng.random() * dauer))
            zufall.append((sym, t, richtung))
        n = bewegung(kurse, atr, zufall)
        for k in STUNDEN:
            if n[k]:
                null_je_k[k].append(float(np.median(n[k])))

    print("\n  %-10s %9s %11s %11s %11s %11s"
          % ("Warten", "Faelle", "Median R", "Nullwelt", "entzerrt", "Streuung"))
    for k in STUNDEN:
        v = np.array(echt[k], float)
        if v.size < 30:
            print("  %-10s %9d  zu wenige Faelle" % ("%.2f h" % k, v.size))
            continue
        nw = float(np.mean(null_je_k[k])) if null_je_k[k] else float("nan")
        print("  %-10s %9d %+11.4f %+11.4f %+11.4f %11.4f"
              % ("%.2f h" % k, v.size, float(np.median(v)), nw,
                 float(np.median(v)) - nw,
                 float(np.median(np.abs(v)))))

    # ---- DIE POSITIVKONTROLLE --------------------------------------------
    #
    # ⚠️ OHNE SIE IST EIN NULLERGEBNIS WERTLOS. Der Median oben ist null -
    # das kann heissen "Warten kostet nichts" oder "dieser Aufbau findet
    # nichts". Also wird ein bekannter Betrag gepflanzt: der spaetere Kurs
    # wird um `d` R angehoben. Findet die Messung ihn nicht wieder, misst
    # sie ueberhaupt nichts.
    print("\n  POSITIVKONTROLLE - gepflanzte Drift, gemessen bei 3 h")
    k_test = 3.0
    for d in (0.02, 0.05, 0.10):
        werte = []
        for sym, t0, richtung in anker:
            reihe, r_einheit = kurse.get(sym), atr.get(sym)
            if not reihe or not r_einheit:
                continue
            p0 = kurs_bei(reihe[0], reihe[1], t0)
            p1 = kurs_bei(reihe[0], reihe[1], t0 + dt.timedelta(hours=k_test))
            if not p0 or not p1:
                continue
            # `d` R aufschlagen heisst: um d * Stopweite teurer
            p1_g = p1 * (1.0 + richtung * d * STOP_ATR * r_einheit)
            werte.append(richtung * (p1_g - p0) / p0 / (STOP_ATR * r_einheit))
        m = float(np.median(werte)) if werte else float("nan")
        print("     +%.2f R gepflanzt -> gemessen %+.4f R   %s"
              % (d, m, "gefunden" if abs(m - d) < 0.25 * d else "⚠️ NICHT"))

    print("\n  LESEART")
    print("     Median R   >0 heisst: der Kurs lief in die Richtung der")
    print("                Empfehlung - wer k Stunden wartet, zahlt das.")
    print("     Nullwelt   dasselbe an zufaelligen Zeitpunkten (%d Ziehungen)."
          % NULL_ZIEHUNGEN)
    print("     entzerrt   was von UNSEREN Zeitpunkten uebrig bleibt.")
    print("     Streuung   Median des BETRAGS - wie weit der Einstieg")
    print("                wandert, ganz ohne Richtung.")
    print("\n  ⚠️ %s" % VORBEHALT)
    print("=" * 100)
    con.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
