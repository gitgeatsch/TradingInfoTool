# -*- coding: utf-8 -*-
"""Welche STOPWEITE traegt? - historisch, gepaart, ueber die Messmenge.

⚠️ DIESER KOPF IST DIE VORABFESTLEGUNG, geschrieben BEVOR gerechnet wurde.

## Warum es dieses Werkzeug gibt

`hebel = risiko_eur / (einsatz x stop_rel)`. Der ZAEHLER ist gemessen -
`r(q)`, halbes Kelly aus der Trefferquote. Der NENNER nicht: `stop_ziel_atr`
= 2,5 steht auf FREMDEN Praxisstandards (Chandelier 3x, Elder 2x) und einem
Backtest mit 61 aufgeloesten Trades; `stop_max_relativ` = 25 % traegt im
Code den Vermerk "NEU, es gab bisher keine" (2.431-grenzen). Damit haengt
der Hebel jedes laufenden Signals an einer Zahl ohne eigenen Befund.

## ⚠️⚠️ Warum die erste Messung nicht gereicht hat - und was daraus folgt

`messe_stop_abstand_baender.py` misst dieselbe Frage auf den SIGNALEN. Sie
loest die Survivorship-Falle richtig (kein Aufloesungsfilter), aber sie
scheitert an der Menge, und der Grund ist mechanisch (2.434):

    Der Block-Bootstrap zieht ueber SYMBOLE, nicht ueber Faelle - und das
    ist RICHTIG, denn mehrere Signale desselben Symbols teilen dieselbe
    Kursreihe. Die wirksame Stichprobe ist damit die SYMBOLZAHL.

    251 Faelle im breitesten Band sind 21 SYMBOLE.

Die Aufloesung lag deshalb bei 0,40 R, waehrend der groesste gemessene
Effekt +0,230 R betrug - und zwei Baender bestanden nicht einmal die
Positivkontrolle. Ein Nullbefund von dort sagt nichts.

## Die zwei Hebel dieses Werkzeugs

    (1) MEHR SYMBOLE      messmenge.V1 statt der Signalsymbole.
                          Die Bandbreite skaliert mit 1/Wurzel(Symbole).

    (2) GEPAART RECHNEN   ⚠️ der staerkere. Auf den Signalen bekommt jeder
                          Fall EINE Stopweite; verglichen werden also
                          VERSCHIEDENE Lagen. Historisch bekommt JEDER
                          Anker JEDE Weite - dieselbe Lage, nur ein
                          anderer Stop. Die Auswahl faellt als Stoerquelle
                          weg, und der Vergleich wird zu einer PAARWEISEN
                          Differenz.

⚠️ DIE TAGESKLAMMER IST DAMIT ERFUELLT, nicht umgangen: `messnorm` verlangt
sie, damit nicht ueber Tage hinweg gepoolt wird. Ein PAARWEISER Vergleich
haelt den Tag per Konstruktion fest - beide Weiten werden am selben Anker
desselben Tages gerechnet.

## Was gemessen wird

    frageart      `geometrie`  -> Menge = MESSUNIVERSUM (messnorm)
    Menge         messmenge.V1, Krypto, Reihen ueber der Mindestlaenge
    Zielgroesse   Ergebnis in R: Ziel vor Stop = +CRV, Stop = -1,
                  sonst Mark-to-Market am Horizont
    Kosten        0,00 % (messnorm G - Gebuehren gehoeren nicht in die
                  Bewertung, Regel 2)
    Band          Block-Bootstrap ueber SYMBOLE
    Trennschaerfe ZENTRIERT gepflanzt (stehende Vorgabe 07.09.)
    Positivkontrolle  5 Ziehungen mit verschiedenen Saaten

⚠️ KEIN AUFLOESUNGSFILTER. Wer bis zum Horizont weder Ziel noch Stop
trifft, bekommt den Stand am Horizont. Ohne das haengt die Stichprobe am
Messgegenstand: ein enger Stop loest fast immer auf, ein weiter faellt
heraus - genau der Fehler, an dem zwei Vormessungen gebrochen sind.

⚠️ GLEICHTAGS-MEHRDEUTIGKEIT KONSERVATIV: beruehrt eine Kerze Stop UND
Ziel, gilt der STOP. Aus Tagesdaten ist die Reihenfolge nicht bekannt, und
die guenstige Annahme waere die, die das Ergebnis schoenrechnet.

AUFRUF:
    python messe_stopweite_historisch.py
    python messe_stopweite_historisch.py --symbole 80 --anker 40   # schneller
"""
from __future__ import annotations

import argparse
import random
import statistics
import sys
from collections import defaultdict

import numpy as np

import messe_eigenschaft_beitrag as B
import messmenge

# ⚠️ DIESELBEN WEITEN WIE IN DER SIGNALMESSUNG, damit die beiden
# vergleichbar bleiben - und dieselbe Staerkenleiter wie `messnorm`.
WEITEN = (0.02, 0.03, 0.05, 0.08, 0.12, 0.20)
STAERKEN = (0.02, 0.05, 0.10, 0.20, 0.40)
POSITIV_ZIEHUNGEN = 5
HORIZONTE = (5, 10, 20)
CRV = 2.0
BOOTSTRAP = 2000
SAAT = 20260913
# ⚠️ Der heutige Betriebspunkt: `stop_ziel_atr` = 2,5 trifft bei Krypto
# rund 7,5 %. Gegen IHN wird verglichen - eine Aenderung muss sich
# gegenueber dem messen, was heute laeuft, nicht gegen eine Idealweite.
BEZUG = 0.08
MIN_TAGE = 400
VORLAUF = 200


def _ergebnis(hoch, tief, schluss, idx, weite, horizont, short,
              stop_zuerst=True, crv=CRV):
    """Ergebnis in R fuer viele Anker auf einmal - vektorisiert ueber `idx`.

    ⚠️ STOP VOR ZIEL bei Gleichstand (siehe Kopf). `stop_zuerst=False`
    dreht die Regel um - NUR fuer die Gegenpruefung, um zu sehen, ob das
    Ergebnis an dieser Annahme haengt. Im Betrieb gilt die konservative
    Fassung.

    Gibt (ergebnis, aufgeloest) zurueck; `aufgeloest` sagt je Anker, ob
    Stop oder Ziel getroffen wurde - sonst steht dort Mark-to-Market."""
    ein = schluss[idx]
    if short:
        stop, ziel = ein * (1.0 + weite), ein * (1.0 - crv * weite)
    else:
        stop, ziel = ein * (1.0 - weite), ein * (1.0 + crv * weite)
    offen = np.ones(len(idx), dtype=bool)
    aus = np.zeros(len(idx))
    for k in range(1, horizont + 1):
        j = idx + k
        gueltig = offen & (j < len(schluss))
        if not gueltig.any():
            break
        h, t = hoch[np.minimum(j, len(hoch) - 1)], tief[np.minimum(j, len(tief) - 1)]
        if stop_zuerst:
            erst, erst_wert = ((h >= stop) if short else (t <= stop)), -1.0
            dann, dann_wert = ((t <= ziel) if short else (h >= ziel)), crv
        else:
            erst, erst_wert = ((t <= ziel) if short else (h >= ziel)), crv
            dann, dann_wert = ((h >= stop) if short else (t <= stop)), -1.0
        traf = gueltig & erst
        aus[traf] = erst_wert
        offen &= ~traf
        traf = offen & (j < len(schluss)) & dann
        aus[traf] = dann_wert
        offen &= ~traf
    aufgeloest = ~offen
    if offen.any():
        j = np.minimum(idx[offen] + horizont, len(schluss) - 1)
        bew = (schluss[j] / ein[offen] - 1.0) / weite
        aus[offen] = -bew if short else bew
    return aus, aufgeloest


def _block_bootstrap(je_symbol: dict, zieh: int = BOOTSTRAP,
                     saat: int = SAAT) -> tuple[float, float]:
    """Ueber SYMBOLE ziehen, nicht ueber Einzelfaelle.

    ⚠️ Mehrere Anker desselben Symbols teilen dieselbe Kursreihe. Ueber
    Einzelfaelle zu ziehen ergaebe zu enge Baender - genau der Grund, aus
    dem die Signalmessung nur 21 wirksame Beobachtungen hatte (2.434)."""
    symbole = list(je_symbol)
    if len(symbole) < 2:
        return (float("nan"), float("nan"))
    # ⚠️ GEWICHTETES MITTEL DER SYMBOLMITTEL - rechnerisch IDENTISCH zum
    # Mittel der aneinandergehaengten Werte, aber ohne sie je zu
    # verketten. Bei 536 Symbolen x 60 Ankern x 2.000 Ziehungen waere die
    # naive Fassung 64 Mio Listenoperationen JE Bootstrap, und es gibt 330
    # davon. Die Gleichheit ist unten gegengeprueft (`--selbsttest`).
    summe = np.array([float(np.sum(je_symbol[s])) for s in symbole])
    anzahl = np.array([len(je_symbol[s]) for s in symbole], dtype=float)
    rng = np.random.default_rng(saat)
    wahl = rng.integers(0, len(symbole), size=(zieh, len(symbole)))
    mittel = summe[wahl].sum(axis=1) / np.maximum(anzahl[wahl].sum(axis=1), 1e-9)
    mittel.sort()
    return (float(mittel[int(0.025 * zieh)]), float(mittel[int(0.975 * zieh)]))


def _zentriert(je_symbol: dict, staerke: float) -> dict:
    """Auf NULL zentriert, dann um `staerke` versetzt.

    ⚠️⚠️ ZENTRIEREN IST PFLICHT (stehende Vorgabe 07.09.2026). Wer auf die
    ECHTE Reihe pflanzt, misst den vorhandenen Effekt noch einmal: ist er
    schon trennbar, bleibt er es bei JEDEM Versatz, und gemeldet wird die
    kleinste geprueft Zahl.

    Hier ist die Groesse eine PAARWEISE DIFFERENZ, ihr Nullpunkt also 0 -
    zentriert wird deshalb auf 0, nicht auf eine Basislinie."""
    alle = [w for v in je_symbol.values() for w in v]
    m = statistics.fmean(alle) if alle else 0.0
    return {s: [w - m + staerke for w in v] for s, v in je_symbol.items()}


def _probe_zentrierung(je_symbol: dict) -> float:
    """Gegenprobe: bei Staerke 0 muss das Mittel EXAKT 0 sein."""
    z = _zentriert(je_symbol, 0.0)
    alle = [w for v in z.values() for w in v]
    return statistics.fmean(alle) if alle else 0.0


def _trennschaerfe(je_symbol: dict) -> float | None:
    """Die KLEINSTE gepflanzte Staerke, deren Band die Null ausschliesst."""
    for st in STAERKEN:
        lo, _hi = _block_bootstrap(_zentriert(je_symbol, st))
        if lo == lo and lo > 0.0:
            return st
    return None


def _positivkontrolle(je_symbol: dict, staerke: float = 0.40) -> int:
    """Findet die Anlage einen BEKANNTEN Effekt - in wie vielen Ziehungen?"""
    n = 0
    for i in range(POSITIV_ZIEHUNGEN):
        lo, _hi = _block_bootstrap(_zentriert(je_symbol, staerke),
                                   saat=SAAT + 1000 * i)
        if lo == lo and lo > 0.0:
            n += 1
    return n


def _urteil(lo: float, hi: float, ts: float | None, pk: int) -> str:
    """Die vier Urteile der Norm - nie zwei davon vermischen."""
    if pk < POSITIV_ZIEHUNGEN or ts is None:
        return "KEIN BEFUND"
    if lo > 0.0 or hi < 0.0:
        return "TRAEGT"
    return "traegt nicht bis %.2f R" % ts


def symbolliste(reihen, symbole: int) -> list:
    return [s for s in sorted(messmenge.V1)
            if len(reihen.get(s) or []) > MIN_TAGE][:symbole]


def sammle(reihen, syms, anker: int, horizont: int, short: bool,
           saat: int = SAAT, bezug: float = BEZUG, stop_zuerst: bool = True,
           ab: str | None = None, atr_band: tuple | None = None,
           weiten: tuple = WEITEN,
           crv: float = CRV) -> tuple[dict, dict, int, dict]:
    """⚠️ DIE EINE Sammelschleife - `lauf` UND die Gegenpruefung rufen
    sie auf. Ein Gegentest, der die Rechnung nachbaut, prueft die Kopie.

    `ab`        nur Anker ab diesem Datum (Zeitfenster-Gegenprobe)
    `atr_band`  nur Anker, deren ATR-RUECKFALLSTOP (`stop_ziel_atr` x ATR
                / Kurs) in diesem Band liegt. ⚠️ DAMIT WIRD DIE
                DECKELFRAGE MESSBAR: Anker ueber 0,25 sind genau die, die
                der Deckel `stop_max_relativ` heute abschneidet.
                Das ATR kommt aus `indicators.calculations.atr_wilder` -
                DERSELBEN Funktion, die auch die Kette benutzt.
    """
    assert bezug in weiten, "der Bezugspunkt muss im Raster liegen"
    rng = np.random.default_rng(saat)
    roh: dict = {w: defaultdict(list) for w in weiten}
    paar: dict = {w: defaultdict(list) for w in weiten}
    quote: dict = {w: [0, 0] for w in weiten}
    n_anker = 0
    for sym in syms:
        r = reihen[sym]
        h = np.array([x[2] for x in r], dtype=float)
        t = np.array([x[3] for x in r], dtype=float)
        c = np.array([x[1] for x in r], dtype=float)
        moegl = np.arange(VORLAUF, len(c) - horizont - 1)
        if ab:
            moegl = moegl[[r[i][0] >= ab for i in moegl]]
        if atr_band is not None:
            from agent.entscheidungsrechnung import GRENZEN as _G
            from indicators.calculations import atr_wilder as _aw
            _res = _aw(h, t, c)
            if not _res.available:
                continue
            _a = np.asarray(_res.value, dtype=float)
            with np.errstate(invalid="ignore", divide="ignore"):
                _rel = _G["stop_ziel_atr"] * _a / c
            _lo, _hi = atr_band
            _ok = np.isfinite(_rel) & (_rel >= _lo) & (_rel < _hi)
            moegl = moegl[_ok[moegl]]
        if len(moegl) < 5:
            continue
        idx = rng.choice(moegl, size=min(anker, len(moegl)), replace=False)
        n_anker += len(idx)
        je_w = {}
        for w in weiten:
            wert, auf = _ergebnis(h, t, c, idx, w, horizont, short,
                                  stop_zuerst, crv=crv)
            je_w[w] = wert
            quote[w][0] += int(auf.sum())
            quote[w][1] += len(idx)
        for w in weiten:
            roh[w][sym].extend(je_w[w].tolist())
            # ⚠️ DIE PAARUNG: derselbe Anker, andere Weite.
            paar[w][sym].extend((je_w[w] - je_w[bezug]).tolist())
    return roh, paar, n_anker, quote


def lauf(symbole: int, anker: int, horizont: int, short: bool) -> None:
    reihen = B.lade()
    syms = symbolliste(reihen, symbole)
    roh, paar, n_anker, _quote = sammle(reihen, syms, anker, horizont, short)

    print()
    print("=" * 104)
    print("HORIZONT %d TAGE - %s   |   %d Symbole, %d Anker, jeder mit %d Weiten"
          % (horizont, "SHORT" if short else "LONG", len(syms), n_anker,
             len(WEITEN)))
    print("=" * 104)
    print("  %-9s %8s %9s | %-24s %9s %9s %s"
          % ("Weite", "n", "EW (R)", "GEPAART gegen 8 % (KI)", "Trennsch.",
             "Positivk.", "URTEIL"))
    print("  " + "-" * 100)
    for w in WEITEN:
        alle = [x for v in roh[w].values() for x in v]
        ew = statistics.fmean(alle)
        if abs(w - BEZUG) < 1e-12:
            print("  %8.0f %% %8d %+9.3f | %-24s %9s %9s %s"
                  % (100 * w, len(alle), ew, "(der Bezugspunkt)", "-", "-",
                     "Betriebspunkt heute"))
            continue
        d = paar[w]
        dm = statistics.fmean([x for v in d.values() for x in v])
        lo, hi = _block_bootstrap(d)
        ts = _trennschaerfe(d)
        pk = _positivkontrolle(d)
        z = _probe_zentrierung(d)
        warn = "" if abs(z) < 1e-9 else "  ⚠️ ZENTRIERUNG %+.1e" % z
        print("  %8.0f %% %8d %+9.3f | %+7.3f [%+6.3f;%+6.3f] %9s %5d/%d  %s%s"
              % (100 * w, len(alle), ew, dm, lo, hi,
                 ("ab %.2f R" % ts) if ts else "> 0,40 R", pk,
                 POSITIV_ZIEHUNGEN, _urteil(lo, hi, ts, pk), warn))


def selbsttest() -> None:
    """⚠⚠ DIE GEGENPROBE ZUR ABKUERZUNG: liefert das gewichtete Mittel
    der Symbolmittel dasselbe wie das Mittel der verketteten Werte?

    Eine Beschleunigung, die man nicht gegen die langsame Fassung prueft,
    ist eine stille Aenderung des Ergebnisses."""
    rng = np.random.default_rng(4711)
    je = {"A": list(rng.normal(0.1, 1.0, 37)),
          "B": list(rng.normal(-0.2, 2.0, 61)),
          "C": list(rng.normal(0.0, 0.5, 12))}

    def _langsam(js, zieh, saat):
        syms = list(js)
        r = random.Random(saat)
        m = []
        for _ in range(zieh):
            w = []
            for _ in range(len(syms)):
                w.extend(js[r.choice(syms)])
            m.append(statistics.fmean(w))
        m.sort()
        return (m[int(0.025 * zieh)], m[int(0.975 * zieh)])

    print("SELBSTTEST - schnelle gegen langsame Bootstrap-Fassung")
    print("=" * 74)
    # 1. Punktschaetzer: bei DERSELBEN Auswahl muessen beide gleich sein
    alle = [w for v in je.values() for w in v]
    summe = sum(alle)
    gew = summe / len(alle)
    print("  Mittel verkettet      %+.12f" % statistics.fmean(alle))
    print("  gewichtetes Mittel    %+.12f" % gew)
    print("  Unterschied           %.2e   %s"
          % (abs(statistics.fmean(alle) - gew),
             "OK" if abs(statistics.fmean(alle) - gew) < 1e-12 else "✖ FALSCH"))
    # 2. Die Baender muessen sich decken (andere Saatmechanik, also nicht
    #    ziffergleich - aber innerhalb weniger Prozent)
    a = _block_bootstrap(je, zieh=4000, saat=99)
    b = _langsam(je, 4000, 99)
    print("  Band schnell          [%+.4f;%+.4f]" % a)
    print("  Band langsam          [%+.4f;%+.4f]" % b)
    breite_a, breite_b = a[1] - a[0], b[1] - b[0]
    ab = abs(breite_a - breite_b) / max(breite_b, 1e-9)
    print("  Breitenabweichung     %.1f %%   %s"
          % (100 * ab, "OK" if ab < 0.05 else "✖ zu gross"))
    # 3. Zentrierung
    print("  Zentrierungsprobe     %+.2e   %s"
          % (_probe_zentrierung(je),
             "OK" if abs(_probe_zentrierung(je)) < 1e-12 else "✖ FALSCH"))


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--symbole", type=int, default=10000)
    p.add_argument("--anker", type=int, default=60)
    p.add_argument("--selbsttest", action="store_true",
                   help="die Abkuerzung gegen die langsame Fassung pruefen")
    p.add_argument("--horizont", type=int, default=0,
                   help="nur dieser Horizont, sonst alle drei")
    a = p.parse_args()
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if a.selbsttest:
        selbsttest()
        return

    print("=" * 104)
    print("WELCHE STOPWEITE TRAEGT? - historisch, GEPAART, ueber die Messmenge")
    print("=" * 104)
    print(messmenge.zeile())
    print("frageart `geometrie` -> Menge = Messuniversum (messnorm) · "
          "Kosten 0,00 %% · CRV %.1f" % CRV)
    print("⚠️ KEIN Aufloesungsfilter · Gleichstand zaehlt als STOP · "
          "Bezugspunkt %.0f %% (der heutige Betriebspunkt)" % (100 * BEZUG))
    print("⚠️ Die TAGESKLAMMER ist per Konstruktion erfuellt: beide Weiten "
          "werden am SELBEN Anker desselben Tages gerechnet.")

    for hz in ([a.horizont] if a.horizont else HORIZONTE):
        for short in (False, True):
            lauf(a.symbole, a.anker, hz, short)


if __name__ == "__main__":
    main()
