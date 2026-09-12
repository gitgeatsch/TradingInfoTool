# -*- coding: utf-8 -*-
"""Hat der Marktscan Wert geliefert? - die Frage vor jeder Entscheidung ueber ihn.

⚠️ NUTZERAUFTRAG 12.09.2026: *"Marktscan Pruefung auf Wert ist notwendig"*.
Er steht vor Schritt 39 (P-Scan) und vor jeder Stilllegung: 4.088 Kandidaten
seit 09.07., davon 4.071 unbearbeitet auf `status='neu'`. Bevor man sie
bearbeitet ODER wegwirft, gehoert die Frage beantwortet, ob die Quelle
ueberhaupt etwas bringt.

WAS ES SCHON GIBT: `agent/krypto/marktscan_backward_tracking.py` MISST seit
dem 30.07. - `outcome_return_pct` steht bei 114 Kandidaten. Was fehlt, ist
die AUSWERTUNG: eine Zahl ohne Bezugspunkt sagt nichts.

    "die Kandidaten machten im Mittel -11,7 %"   klingt schlecht
    "der Markt machte im selben Fenster -14 %"   waere dann gut

⚠️⚠️ DIE MARKTKLAMMER, und zwar JE FALL. Jeder Kandidat hat sein eigenes
Fenster (`outcome_gestartet_am` bis `outcome_geprueft_am`, im Schnitt 5,8
Tage). Verglichen wird gegen die Bewegung unserer Krypto-Symbole in GENAU
diesem Fenster - nicht gegen einen Gesamtzeitraum, sonst misst man den
Kalender.

⚠️ WAS DIESER VERGLEICH SCHIEF MACHT, benannt statt verschwiegen: unsere
Symbole sind Watchlist-Werte (meist etabliert), die Marktscan-Funde sind
Small Caps. Ein Small Cap schwankt staerker, in beide Richtungen. Der
Vergleich beantwortet deshalb NICHT "sind Small Caps besser als Large Caps",
sondern die praktische Frage: *haette ich mit einem Marktscan-Fund mehr
gehabt als mit dem, was ohnehin auf der Liste steht?*

    python messe_marktscan_wert.py [--db PFAD]
"""
from __future__ import annotations

import argparse
import random
import sqlite3
import statistics as st
import sys


def _deutsch_ausgeben() -> None:
    """Umlaute auf die Konsole, ohne den Aufrufer zu stoeren.

    ⚠️ NICHT AUF MODULEBENE - `pruefe_pakete` ersetzt `sys.stdout` durch
    einen Mitschnitt ohne `reconfigure`, und dann laesst sich das Modul gar
    nicht erst importieren (gefunden am 12.09. bei `messe_ausstiegsguete`)."""
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass


# Die Einstufungen, die der Scan selbst vergibt - von grob nach fein.
ECHTE = ("watchlist_wuerdig", "kaufkandidat")


def markt_im_fenster(reihen: dict, von: str, bis: str) -> float | None:
    """Median-Bewegung unserer Symbole in GENAU diesem Fenster.

    `None`, wenn zu wenige Symbole den Zeitraum abdecken - ein fehlender
    Bezugspunkt ist keine Null, sondern ein nicht messbarer Fall."""
    werte = []
    for r, tage in reihen.values():
        a = _kurs_am(r, tage, von)
        b = _kurs_am(r, tage, bis)
        if a and b and a > 0:
            werte.append(b / a - 1.0)
    return st.median(werte) if len(werte) >= 5 else None


def _kurs_am(reihe: dict, tage: list, tag: str):
    """Der letzte Schluss, der nicht NACH `tag` liegt - Luecken sind normal."""
    treffer = None
    for d in tage:
        if d[:10] <= tag[:10]:
            treffer = d
        else:
            break
    return reihe.get(treffer) if treffer else None


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--db", default="data/tradinginfotool.db")
    a = p.parse_args()
    _deutsch_ausgeben()

    con = sqlite3.connect(a.db)
    faelle = list(con.execute("""
        SELECT symbol, einstufung, outcome_return_pct,
               date(outcome_gestartet_am), date(outcome_geprueft_am),
               score_gesamt, bitpanda_gelistet
          FROM marktscan_candidates
         WHERE outcome_return_pct IS NOT NULL
           AND outcome_gestartet_am IS NOT NULL
           AND outcome_geprueft_am IS NOT NULL"""))
    gesamt = con.execute(
        "SELECT COUNT(*) FROM marktscan_candidates").fetchone()[0]
    print("=" * 78)
    print("HAT DER MARKTSCAN WERT GELIEFERT?")
    print("=" * 78)
    print("Kandidaten insgesamt : %d" % gesamt)
    print("davon mit gemessenem Ertrag: %d  (der Rest ist 'kein_treffer' "
          "und wurde nie verfolgt)" % len(faelle))
    if len(faelle) < 20:
        print("\n⚠️ zu wenige gemessene Faelle - keine Aussage moeglich.")
        return 0

    # unsere Krypto-Reihen als Bezugspunkt
    reihen: dict = {}
    for (sym,) in con.execute(
            "SELECT DISTINCT symbol FROM price_history_ohlc"):
        r = {d: k for d, k in con.execute(
            "SELECT date, close FROM price_history_ohlc "
            "WHERE symbol=? AND close > 0 ORDER BY date", (sym,))}
        if len(r) > 30:
            reihen[sym] = (r, sorted(r))
    print("Bezugsmenge          : %d eigene Symbole mit Kursreihe"
          % len(reihen))

    # ---- die Guete je Fall ----------------------------------------------
    roh: dict = {}
    fenster = []
    for sym, stufe, ertrag, von, bis, score, bp in faelle:
        m = markt_im_fenster(reihen, von, bis)
        if m is None:
            continue
        g = (float(ertrag) / 100.0) - m
        roh.setdefault("alle", []).append(g)
        roh.setdefault(stufe or "?", []).append(g)
        if bp == 1:
            roh.setdefault("bei Bitpanda handelbar", []).append(g)
        fenster.append((von, bis))

    def zeige(schluessel: str) -> None:
        w = roh.get(schluessel) or []
        if len(w) < 10:
            print("  %-24s n=%-4d  zu wenige Faelle" % (schluessel, len(w)))
            return
        pos = 100.0 * sum(1 for x in w if x > 0) / len(w)
        print("  %-24s n=%-4d Median %7.2f %%  Mittel %7.2f %%  "
              "besser als Markt: %.1f %%"
              % (schluessel, len(w), 100 * st.median(w), 100 * st.fmean(w),
                 pos))

    # ---- DIE QUELLE, UND ZWAR ALS UEBERSCHNEIDUNG ----------------------
    #
    # ⚠️ NUTZERANMERKUNG 12.09.: "trending koennte eine Loesung sein". Sie
    # laesst sich NICHT direkt beantworten - reine Trending-Funde haben
    # keinen gemessenen Ertrag, weil sie am Altersfilter haengen bleiben
    # (dokumentierte API-Luecke: /search/trending liefert kein atl_date).
    #
    # WAS SICH BEANTWORTEN LAESST: wie liefen die Coins, die BEIDES waren?
    # Sie haben ueber ihre Top-Gainer-Zeile einen gemessenen Ertrag, und die
    # Trending-Eigenschaft steht in einer zweiten Zeile derselben Tabelle.
    # Keine Aussage ueber REINES Trending - aber die einzige, die heute ohne
    # neuen Datenabruf moeglich ist.
    _trend = {r[0] for r in con.execute(
        "SELECT DISTINCT coingecko_id FROM marktscan_candidates "
        "WHERE discovery_source = 'trending'")}
    _ids = {}
    for _cg, _sym in con.execute(
            "SELECT coingecko_id, symbol FROM marktscan_candidates"):
        _ids.setdefault(_sym, set()).add(_cg)
    for sym, stufe, ertrag, von, bis, score, bp in faelle:
        m = markt_im_fenster(reihen, von, bis)
        if m is None:
            continue
        g = (float(ertrag) / 100.0) - m
        _auch = bool(_ids.get(sym, set()) & _trend)
        roh.setdefault("auch_trending" if _auch else "nur_top_gainer",
                       []).append(g)

    print("\n--- ERTRAG GEGEN DEN MARKT IM GLEICHEN FENSTER ---")
    print("  (positiv = der Fund lief BESSER als unsere Symbole im selben "
          "Zeitraum)")
    for k in ("alle", *ECHTE, "bei Bitpanda handelbar"):
        zeige(k)
    print("")
    print("  ⚠️ und nach der QUELLE - war der Coin AUCH im Trending?")
    for k in ("auch_trending", "nur_top_gainer"):
        zeige(k)

    # ---- die Zufallskontrolle -------------------------------------------
    #
    # ⚠️⚠️ DIESELBEN FENSTER, ein zufaellig gezogenes eigenes Symbol. Damit
    # faellt nur die WAHL weg und der Kalender bleibt gleich. Ohne sie waere
    # jede Zahl oben eine Behauptung (stehende Vorgabe).
    ZIEHUNGEN = 200
    rng = random.Random(20260912)
    syms = sorted(reihen)
    anteile = []
    for _ in range(ZIEHUNGEN):
        w = []
        for von, bis in fenster:
            s2 = rng.choice(syms)
            r, tage = reihen[s2]
            x, y = _kurs_am(r, tage, von), _kurs_am(r, tage, bis)
            m = markt_im_fenster(reihen, von, bis)
            if x and y and x > 0 and m is not None:
                w.append((y / x - 1.0) - m)
        if len(w) >= 10:
            anteile.append(100.0 * sum(1 for v in w if v > 0) / len(w))
    if anteile:
        echt = roh.get("alle") or []
        e = 100.0 * sum(1 for x in echt if x > 0) / len(echt)
        z_med = st.median(anteile)
        z_hi = sorted(anteile)[min(int(0.95 * len(anteile)),
                                   len(anteile) - 1)]
        print("\n--- DIE ZUFALLSKONTROLLE (%d Ziehungen, gleiche Fenster) ---"
              % ZIEHUNGEN)
        print("  Marktscan besser als Markt : %.1f %%" % e)
        print("  Zufall  besser als Markt   : %.1f %%  (95. Perzentil %.1f %%)"
              % (z_med, z_hi))
        print("  ➔ %s" % ("der Marktscan SCHLAEGT den Zufall" if e > z_hi
                          else "der Marktscan schlaegt den Zufall NICHT"))

    print("\n" + "-" * 78)
    print("⚠️ WAS DIESE ZAHLEN NICHT SIND: ein Befund nach Norm. Gemessen")
    print("   wird auf den Faellen, die das Tracking VERFOLGT hat - wer dort")
    print("   hineinkommt, entscheidet die Einstufung des Scans selbst.")
    print("   Und die Bezugsmenge sind Watchlist-Werte, die Funde sind Small")
    print("   Caps. Der Vergleich beantwortet die PRAKTISCHE Frage, nicht die")
    print("   theoretische.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
