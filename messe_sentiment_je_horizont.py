# -*- coding: utf-8 -*-
"""Ist schlechte Stimmung gut fuer den langen und schlecht fuer den kurzen Horizont?

DIE THESE STAMMT VOM NUTZER (12.08.2026): *"sehr schlechtes sentiment ist oft
fuer DCA oder Spot (laengerfristig) gut, eher schlecht bei hebel (ist meine
Meinung, nicht bewiesen)."* Genau deshalb wird sie gemessen und nicht
uebernommen.

WAS FEAR & GREED IST - und was nicht. Der Index von alternative.me bezieht sich
auf BITCOIN, nicht auf den Kryptomarkt insgesamt. Er setzt sich zusammen aus
Volatilitaet (25 %), Marktdynamik/Volumen (25 %), Social Media (15 %),
Umfragen (15 %, ausgesetzt), BTC-Dominanz (10 %) und Google Trends (10 %) -
die Haelfte davon ist also aus dem KURS abgeleitet, nicht aus einer Befragung.

VIER PFLICHTPRUEFUNGEN VOR DEM START (stehende Vorgabe):

  1. Ueberlappen die Daten?      3.087 Tage mit Kurs UND Stimmung, 2017-08
                                 bis 2026-07 - mehrere Zyklen, nicht nur einer
  2. Blickt etwas nach vorn?     nein: Stimmung an Tag t, Ergebnis ab t+1
  3. Wie saehe ein Nullbefund    keine monotone Ordnung ueber die Baender, oder
     aus?                        eine, die auf beiden Horizonten gleich laeuft
  4. Reicht die Stichprobe?      je Band 400-800 Tage - ABER die Fenster
                                 ueberlappen. Bei 90 Tagen Horizont stecken in
                                 3.087 Tagen nur rund 34 UNABHAENGIGE Fenster.
                                 Deshalb wird die effektive Zahl mitgefuehrt und
                                 ueber nicht-ueberlappende Bloecke gebootstrappt

DIE FALLE, DIE FAST JEDE BTC-MESSUNG KIPPT: Bitcoin ist ueber den Zeitraum
massiv gestiegen. JEDES Band hat positive Vorwaertsrenditen. Die Frage ist nie
"ist es positiv", sondern "ist es besser als der Durchschnitt aller Tage".
Deshalb steht ueberall der Abstand zur Gesamtbasis, nicht der Rohwert.
"""
from __future__ import annotations

import sqlite3
import sys

import numpy as np

DB = "data/tradinginfotool.db"

# Die Baender folgen der ueblichen Einteilung von alternative.me.
BAENDER = ((0, 25, "extreme Angst"), (25, 45, "Angst"), (45, 55, "neutral"),
           (55, 75, "Gier"), (75, 101, "extreme Gier"))

# Kurz = Hebel/Swing, lang = Akkumulation/Spot. Die Zahlen entsprechen den
# Horizonten des Backward-Trackings (7/14) und einem Quartal.
HORIZONTE = ((10, "kurz (Hebel/Swing)"), (90, "lang (Akkumulation/Spot)"))

ATR_FENSTER = 14
STOP_ATR = 2.5          # wie in entscheidungsrechnung.GRENZEN
CRV = 2.0


def lade() -> tuple[np.ndarray, ...]:
    con = sqlite3.connect(DB)
    rows = con.execute("""
        SELECT p.date, p.high, p.low, p.close, m.fear_greed_value
        FROM price_history_ohlc p
        JOIN macro_snapshot m ON m.date = p.date
        WHERE p.symbol='BTC' AND p.currency='USD'
          AND m.fear_greed_value IS NOT NULL
        ORDER BY p.date""").fetchall()
    con.close()
    d = np.array([r[0] for r in rows])
    h = np.array([float(r[1]) for r in rows])
    l = np.array([float(r[2]) for r in rows])
    c = np.array([float(r[3]) for r in rows])
    f = np.array([float(r[4]) for r in rows])
    return d, h, l, c, f


def atr(h, l, c, n=ATR_FENSTER):
    tr = np.maximum(h[1:] - l[1:],
                    np.maximum(np.abs(h[1:] - c[:-1]), np.abs(l[1:] - c[:-1])))
    aus = np.full(len(c), np.nan)
    for i in range(n, len(c)):
        aus[i] = tr[i - n:i].mean()
    return aus


def barriere(h, l, c, a, i, tage):
    """Ziel oder Stop zuerst? None, wenn keines im Fenster faellt.

    Genau die Geometrie, die die Entscheidungsrechnung baut - sonst misst der
    Test etwas anderes als das, was die App vorschlaegt."""
    if np.isnan(a[i]) or a[i] <= 0:
        return None
    ein = c[i]
    stop = ein - STOP_ATR * a[i]
    ziel = ein + CRV * STOP_ATR * a[i]
    for j in range(i + 1, min(i + 1 + tage, len(c))):
        if l[j] <= stop:
            return False
        if h[j] >= ziel:
            return True
    return None


def bootstrap(werte: list[float], bloecke: int, runden: int = 2000) -> tuple:
    """Blockweise, nicht tageweise - ueberlappende Fenster sind nicht unabhaengig."""
    if len(werte) < bloecke or bloecke < 2:
        return float("nan"), float("nan")
    # np.array_split liefert ungleich lange Bloecke; die kann rng.choice nicht
    # als Array behandeln. Ueber die INDIZES ziehen statt ueber die Bloecke.
    teile = np.array_split(np.array(werte), bloecke)
    rng = np.random.default_rng(20260812)
    zieh = [np.concatenate([teile[k] for k in
                            rng.integers(0, bloecke, size=bloecke)]).mean()
            for _ in range(runden)]
    return float(np.percentile(zieh, 2.5)), float(np.percentile(zieh, 97.5))


def main() -> int:
    d, h, l, c, f = lade()
    a = atr(h, l, c)
    print(f"BTC, {len(d)} Tage mit Kurs UND Stimmung: {d[0]} bis {d[-1]}\n")

    for tage, name in HORIZONTE:
        print("=" * 78)
        print(f"HORIZONT {tage} TAGE - {name}")
        print("=" * 78)
        gueltig = np.arange(ATR_FENSTER, len(c) - tage)
        # Basis ueber ALLE Tage - Bitcoin ist gestiegen, der Rohwert sagt nichts.
        rend_alle = [(c[i + tage] / c[i] - 1) for i in gueltig]
        tref_alle = [t for t in (barriere(h, l, c, a, i, tage) for i in gueltig)
                     if t is not None]
        basis_r = float(np.mean(rend_alle))
        basis_t = float(np.mean(tref_alle))
        eff = max(2, (len(c) - tage) // tage)
        print(f"Basis ueber alle Tage: Rendite {100 * basis_r:+.1f} %, "
              f"Trefferquote {100 * basis_t:.1f} %   "
              f"(n={len(gueltig)}, unabhaengige Fenster ~{eff})\n")
        print(f"{'Stimmung':<16}{'n':>6}{'Rendite':>10}{'ggü Basis':>11}"
              f"{'Treffer':>9}{'ggü Basis':>11}   95 %-Band der Rendite")
        print("-" * 92)
        for lo, hi, etikett in BAENDER:
            idx = [i for i in gueltig if lo <= f[i] < hi]
            if len(idx) < 30:
                print(f"{etikett:<16}{len(idx):>6}   zu wenige Faelle")
                continue
            rend = [(c[i + tage] / c[i] - 1) for i in idx]
            tref = [t for t in (barriere(h, l, c, a, i, tage) for i in idx)
                    if t is not None]
            b = max(2, len(idx) // tage)
            u, o = bootstrap(rend, b)
            print(f"{etikett:<16}{len(idx):>6}{100 * np.mean(rend):>9.1f}%"
                  f"{100 * (np.mean(rend) - basis_r):>+10.1f}pp"
                  f"{100 * np.mean(tref):>8.1f}%"
                  f"{100 * (np.mean(tref) - basis_t):>+10.1f}pp"
                  f"   {100 * u:>+6.1f} .. {100 * o:>+6.1f} %"
                  + ("" if u <= 0 <= o else "  <- Band ohne Null"))
        print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
