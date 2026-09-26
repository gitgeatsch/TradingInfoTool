# -*- coding: utf-8 -*-
"""Haelt die Bewertung eine GROEBERE Aufloesung - und was kostet der Fallback?

**26.09.2026**, Nutzerauftrag: *"ja messen - pruefen und gegenpruefen - wir
benoetigen auch eine fallback loesung wenn eine Bewertung nicht oder nur zum
Teil gedeckt ist."*

Vorabfestlegung: `Basisinfos/Vorabfestlegung_21_Aufloesung_26_09.md`

═══════════════════════════════════════════════════════════════════════
 DIE FRAGE
═══════════════════════════════════════════════════════════════════════

Die Bewertung aus 2.608 steht auf STUENDLICHEM OHLC von Binance. Fuer 15
von 43 Watchlist-Symbolen gibt es das nicht; CoinGecko liefert eine
stuendliche PREISREIHE und 4-STUNDEN-OHLC (2.613).

    Bleibt die Bewertung gueltig, wenn die ATR groeber wird?

═══════════════════════════════════════════════════════════════════════
 ⚠️⚠️ DIE ZWEI FALLEN, DIE DIE KONSTRUKTION BESTIMMEN
═══════════════════════════════════════════════════════════════════════

    ⚠️ FALLE 1   `R` steht in Einheiten des ANFANGSRISIKOS, also IN ATR.
                 Aendert sich die ATR, aendert sich der NENNER - `E[R]`
                 waere dann nur anders SKALIERT, nicht besser oder
                 schlechter. Das ist der Fehler aus 2.607.
                 ➤ Deshalb wird BEIDES gemessen, und nur der
                   KURSPROZENT-Arm entscheidet die Vergleichsfrage.

    ⚠️ FALLE 2   Die ATR geht an ZWEI Stellen ein - in den NENNER des
                 Merkmals (wer wird gewaehlt) und in die STOPWEITE (wie
                 wird gefuehrt). Beide werden gemeinsam UND einzeln
                 umgestellt.

═══════════════════════════════════════════════════════════════════════
 DIE VIER STUFEN
═══════════════════════════════════════════════════════════════════════

⚠️⚠️ DER AUSWAHLANTEIL WIRD ANGEGLICHEN, NICHT DIE SCHWELLE. Stufe A bei
Schwelle 1,0 gibt die ZAHL der Signale vor; jede andere Stufe nimmt ihre
besten k. Sonst vergliche man die HAERTE der Auswahl statt der ORDNUNG -
im Probelauf standen 0,9 gegen 18,4 Signale je Tag nebeneinander.

    A   1-h-OHLC                        heute (Binance)
    B   4-h-OHLC, aggregiert            entspricht CoinGecko-OHLC
    C   Tages-OHLC, aggregiert          die groebste Fallback-Stufe
    D   ⭐ NUR Schlusskurse, kein High/Low - ATR ersetzt durch die
        Streuung der Stundenschluesse   entspricht CoinGecko `market_chart`

⭐ Stufe D ist die eigentliche Fallbackfrage: die Preisreihe gibt es fuer
15 von 15, das OHLC nur grob.

⚠️ Die groberen Kerzen werden aus den VORHANDENEN 1-h-Kerzen AGGREGIERT.
Damit ist der Unterschied rein die AUFLOESUNG - keine zweite Quelle, keine
andere Grundgesamtheit. Dass CoinGecko-4h-Kerzen den aggregierten
entsprechen, ist damit NICHT gezeigt (eigene Frage).

⚠️ NUR LESEN.  python messe_aufloesung_und_fallback.py [--symbole N]
"""
from __future__ import annotations

import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import messnorm as N                                            # noqa: E402
from messe_reverse_scharfe_anstiege import lade_kurse           # noqa: E402
from messe_hebel_geometrie_neutral import atr_tag_relativ       # noqa: E402
from messe_trailing_und_betrieb import ema, trailing            # noqa: E402

EMA_L = 48                       # aus 2.606
VORLAUF = 240                    # 5 x EMA_L
H = 72                           # aus 2.607
TRAIL_W = 1.0
SCHWELLE = 1.0                   # aus 2.608
STUFEN = (("A", 1), ("B", 4), ("C", 24))
N_NULL = N.NULL_ZIEHUNGEN
NULL_PERZ = N.NULL_PERZENTIL
MIND = 200
SAAT = 20260926


# ═══════════════════════════════════════════════════════════════════════
#  Die Aggregation - und ihre Selbstprobe
# ═══════════════════════════════════════════════════════════════════════

def atr_grob(high, low, close, takt):
    """ATR aus Kerzen der Breite `takt` Stunden, zurueck auf Stundenraster.

    ⭐⭐ P1 - DIE SELBSTPROBE STECKT IM BAU: bei `takt == 1` wird
    `atr_tag_relativ` unveraendert aufgerufen. Der Grenzfall ist damit
    nicht nur gleich, sondern DERSELBE Code - eine Abweichung waere
    unmoeglich, und die Probe in `main` weist es am Ergebnis nach.

    ⚠️ KAUSAL: eine grobe Kerze gilt erst, wenn sie ABGESCHLOSSEN ist.
    Der Wert wird deshalb um `takt` Stunden nach vorn versetzt - sonst
    saehe der Anker in seine eigene Kerze hinein (2.600).
    """
    if takt == 1:
        return atr_tag_relativ(high, low, close)
    n = len(close)
    m = n // takt
    if m < 3:
        return np.full(n, np.nan)
    # ── die groben Kerzen bauen ──────────────────────────────────────
    h = high[:m * takt].reshape(m, takt).max(axis=1)
    l = low[:m * takt].reshape(m, takt).min(axis=1)
    c = close[:m * takt].reshape(m, takt)[:, -1]
    # ── ATR auf dem groben Raster, Fenster so dass es 24 h abdeckt ───
    fenster = max(2, int(round(24.0 / takt)))
    vorher = np.concatenate(([c[0]], c[:-1]))
    tr = np.maximum(h - l, np.maximum(np.abs(h - vorher),
                                      np.abs(l - vorher)))
    with np.errstate(divide="ignore", invalid="ignore"):
        trr = tr / np.maximum(c, 1e-12)
    kern = np.ones(fenster) / fenster
    grob = np.convolve(trr, kern, mode="full")[:m]
    grob[:fenster - 1] = np.nan
    # ⚠️⚠️ AUF TAGESMASS, GENAU WIE `atr_tag_relativ`: dort ist es die
    # mittlere STUNDENspanne mal sqrt(24). Hier ist die Einzelspanne
    # schon `takt` Stunden breit, es fehlen also nur noch die
    # verbleibenden 24/takt Schritte. OHNE diesen Faktor lag die
    # 4-h-Stufe bei 0,42x der 1-h-Stufe - und dieselbe Schwelle 1,0
    # erzeugte 18,4 statt 0,9 Signale je Tag. Im Probelauf gefunden.
    grob = grob * np.sqrt(24.0 / takt)
    # ── zurueck auf Stunden, KAUSAL versetzt ─────────────────────────
    aus = np.full(n, np.nan)
    for k in range(m):
        a = (k + 1) * takt                      # erst NACH der Kerze
        b = min(n, a + takt)
        if a < n:
            aus[a:b] = grob[k]
    return aus


def atr_aus_schluessen(close, fenster=24):
    """⭐ STUFE D: ATR-Ersatz OHNE High/Low - nur aus Schlusskursen.

    Genommen wird die mittlere absolute Stundenrendite ueber `fenster`,
    hochgerechnet auf eine Tagesspanne. ⚠️ Der Faktor ist NICHT frei
    gewaehlt: eine Zufallsbewegung waechst mit der Wurzel der Zeit, also
    `sqrt(24)`. Ein angepasster Faktor waere eine Kalibrierung auf das
    Ergebnis - genau das soll die Messung ja pruefen.
    """
    n = len(close)
    with np.errstate(divide="ignore", invalid="ignore"):
        r = np.abs(np.diff(close) / np.maximum(close[:-1], 1e-12))
    r = np.concatenate(([np.nan], r))
    kern = np.ones(fenster) / fenster
    g = np.convolve(np.nan_to_num(r), kern, mode="full")[:n]
    g[:fenster] = np.nan
    return g * np.sqrt(24.0)


def ertrag_prozent(high, low, close, atr, weite, hz):
    """⭐ FALLE 1: derselbe Trailing-Ausstieg, aber in KURSPROZENT.

    `trailing()` teilt durch `weite*atr` - das ist der ATR-abhaengige
    Massstab. Hier wird durch den EINSTIEGSKURS geteilt, und der haengt
    von keiner Aufloesung ab. Nur dieser Arm entscheidet die
    Vergleichsfrage.
    """
    r = trailing(high, low, close, atr, weite, hz)
    # trailing gibt (Ausstieg-Einstieg)/(weite*atr*close); zurueckrechnen
    return r * weite * atr


def main() -> int:
    grenze = None
    if "--symbole" in sys.argv:
        grenze = int(sys.argv[sys.argv.index("--symbole") + 1])

    print("=" * 100)
    print("HAELT DIE BEWERTUNG EINE GROEBERE AUFLOESUNG?")
    print("=" * 100)
    print("  " + N.standardzeile())
    print("  Schwelle %.1f ATR · Trailing %.1f ATR · Horizont %d h · EMA %d h"
          % (SCHWELLE, TRAIL_W, H, EMA_L))
    print()

    kurse = lade_kurse(grenze)
    alle = set()
    for (s, *_r) in kurse.values():
        alle.update(s)
    sl = sorted(alle); sid = {s: i for i, s in enumerate(sl)}
    print("  %d Symbole · %d Stunden" % (len(kurse), len(sl)), flush=True)

    # ── sammeln: je Stufe Merkmal, R und Kursprozent ─────────────────
    marken = [m for m, _t in STUFEN] + ["D"]
    G = []
    W = {m: [] for m in marken}      # Merkmal (ATR im Nenner)
    R = {m: [] for m in marken}      # E[R], ATR-abhaengig
    P = {m: [] for m in marken}      # Kursprozent, ATR-UNabhaengig
    ATRW = {m: [] for m in marken}   # die ATR selbst
    # Kreuzarm: Merkmal aus A, Stop aus B (Falle 2)
    WA_RB = []
    probe_ok = None

    for sym, (st, h, l, cc, v) in kurse.items():
        if sym.upper() == "BTC":
            continue
        idx = np.array([sid[x] for x in st], np.int64)
        atr = {}
        for m, takt in STUFEN:
            atr[m] = atr_grob(h, l, cc, takt)
        atr["D"] = atr_aus_schluessen(cc)
        # ── P1: der Grenzfall muss bitgleich sein ────────────────────
        if probe_ok is None:
            eins = atr_grob(h, l, cc, 1)
            ref = atr_tag_relativ(h, l, cc)
            probe_ok = bool(np.array_equal(np.nan_to_num(eins, nan=-1.0),
                                           np.nan_to_num(ref, nan=-1.0)))
        e = ema(cc, EMA_L)
        # ── P3: nur Anker, die in ALLEN Stufen gueltig sind ──────────
        gu = np.ones(len(cc), bool)
        for m in marken:
            gu &= np.isfinite(atr[m]) & (atr[m] > 0)
        gu[:VORLAUF] = False
        gu[max(0, len(cc) - H):] = False
        sel = np.flatnonzero(gu)
        if not len(sel):
            continue
        G.append(idx[sel])
        for m in marken:
            with np.errstate(divide="ignore", invalid="ignore"):
                w = (cc - e) / np.maximum(atr[m] * cc, 1e-12)
            W[m].append(w[sel])
            R[m].append(trailing(h, l, cc, atr[m], TRAIL_W, H)[sel])
            P[m].append(ertrag_prozent(h, l, cc, atr[m], TRAIL_W, H)[sel])
            ATRW[m].append(atr[m][sel])
        # Kreuzarm: Auswahl nach A, Fuehrung mit B
        WA_RB.append(trailing(h, l, cc, atr["B"], TRAIL_W, H)[sel])

    if not G:
        print("  keine Anker")
        return 1
    G = np.concatenate(G)
    W = {m: np.concatenate(x) for m, x in W.items()}
    R = {m: np.concatenate(x) for m, x in R.items()}
    P = {m: np.concatenate(x) for m, x in P.items()}
    ATRW = {m: np.concatenate(x) for m, x in ATRW.items()}
    WA_RB = np.concatenate(WA_RB)
    n = len(G)
    tage = G // 24
    ntage = len(np.unique(tage))
    print("  %d Anker (in ALLEN Stufen gueltig, P3) · %d Tage"
          % (n, ntage), flush=True)
    print()
    print("  P1  Grenzfall takt=1 bitgleich mit atr_tag_relativ: %s"
          % ("✔ JA" if probe_ok else "⛔ NEIN - ABBRUCH"))
    if not probe_ok:
        return 1

    # ── wie gross ist der ATR-Unterschied ueberhaupt? ────────────────
    print()
    print("  DIE ATR SELBST (Median ueber alle Anker)")
    print("    %-6s %10s %10s  %s" % ("Stufe", "Median", "zu A", "Beschreibung"))
    besch = {"A": "1-h-OHLC (heute)", "B": "4-h-OHLC (CoinGecko)",
             "C": "Tages-OHLC", "D": "nur Schlusskurse, kein High/Low"}
    ma = float(np.median(ATRW["A"]))
    for m in marken:
        mm = float(np.median(ATRW[m]))
        print("    %-6s %10.5f %9.2fx  %s" % (m, mm, mm / max(ma, 1e-12),
                                              besch[m]))

    rng = np.random.default_rng(SAAT)

    def band(werte, k):
        nb = [float(werte[rng.choice(n, size=k, replace=False)].mean())
              for _ in range(N_NULL)]
        return float(np.percentile(np.array(nb), NULL_PERZ))

    # ── die Bewertung je Stufe ───────────────────────────────────────
    print()
    print("=" * 100)
    print("DIE BEWERTUNG JE STUFE · Schwelle %.1f ATR" % SCHWELLE)
    print("  ⚠️ E[R] ist ATR-ABHAENGIG (Falle 1) - nur KURSPROZENT vergleicht")
    print()
    print("  %-6s %8s %9s %9s %10s %11s %11s  %s"
          % ("Stufe", "Signale", "Sig./Tag", "Schwelle", "E[R]", "Kurs %",
             "Band90 %", "Urteil"))
    # ⭐⭐ DER AUSWAHLANTEIL WIRD ANGEGLICHEN, NICHT DIE SCHWELLE.
    # Stufe A bei Schwelle 1,0 gibt die ZAHL vor; jede andere Stufe nimmt
    # ihre besten k Anker. Sonst vergliche man die HAERTE der Auswahl
    # statt der ORDNUNG - im Probelauf standen 0,9 gegen 18,4 Signale
    # je Tag nebeneinander. Die dafuer noetige Schwelle wird
    # ausgewiesen: laeuft sie weit von 1,0 weg, ist die Skala eine andere.
    k_soll = int((np.isfinite(W["A"]) & (W["A"] >= SCHWELLE)).sum())
    ausw = {}
    for m in marken:
        pos = np.flatnonzero(np.isfinite(W[m]))
        if len(pos) < max(k_soll, MIND):
            print("  %-6s  (zu duenn)" % m)
            continue
        ordn = pos[np.argsort(W[m][pos])[::-1][:k_soll]]
        sig = np.zeros(n, bool); sig[ordn] = True
        ausw[m] = sig
        k = k_soll
        schw = float(W[m][ordn].min())
        er = float(R[m][sig].mean())
        pz = float(P[m][sig].mean()) * 100.0
        b90 = band(P[m], k) * 100.0
        print("  %-6s %8d %9.2f %9.3f %+10.4f %+11.4f %+11.4f  %s"
              % (m, k, k / max(ntage, 1), schw, er, pz, b90,
                 "✔ ueber Band" if pz > b90 else "⛔ IM BAND"))

    # ── P4: der GEPAARTE Fehler, nicht zwei Baender ──────────────────
    print()
    print("  P4  DER GEPAARTE VERGLEICH ZU STUFE A (Differenz je Tag)")
    print("      ⚠️ zwei getrennte Baender sagen NICHTS ueber ihren "
          "Unterschied")
    print("      %-6s %12s %12s %10s  %s"
          % ("Stufe", "Kurs % A", "Kurs % X", "Diff ±Fehler", "Urteil"))
    for m in marken:
        if m == "A" or m not in ausw:
            continue
        # je Tag: Mittel unter A-Auswahl und unter X-Auswahl
        ta = tage[ausw["A"]]; tx = tage[ausw[m]]
        gem = np.intersect1d(np.unique(ta), np.unique(tx))
        if len(gem) < 30:
            print("      %-6s (zu wenige gemeinsame Tage)" % m); continue
        da, dx = [], []
        for t in gem:
            da.append(P["A"][ausw["A"]][ta == t].mean())
            dx.append(P[m][ausw[m]][tx == t].mean())
        da = np.array(da); dx = np.array(dx)
        d = dx - da
        se = float(np.std(d, ddof=1) / np.sqrt(len(d)))
        mi = float(d.mean())
        drin = abs(mi) <= 1.645 * se
        print("      %-6s %+12.4f %+12.4f %+9.4f±%.4f  %s"
              % (m, 100 * da.mean(), 100 * dx.mean(), 100 * mi, 100 * se,
                 "✔ kein Unterschied" if drin else "⛔ UNTERSCHIED"))

    # ── P5: waehlt die Stufe DIESELBEN Anker? ────────────────────────
    print()
    print("  P5  WAEHLT DIE STUFE DIESELBEN ANKER?")
    print("      (gleiches Mittel aus anderer Auswahl waere Zufall)")
    print("      %-6s %12s %12s %12s"
          % ("Stufe", "Rangkorr.", "Ueberlappung", "gemeinsam"))
    for m in marken:
        if m == "A" or m not in ausw:
            continue
        gut = np.isfinite(W["A"]) & np.isfinite(W[m])
        pr = np.flatnonzero(gut)
        st = pr if len(pr) <= 200000 else rng.choice(pr, 200000, replace=False)
        ra = np.argsort(np.argsort(W["A"][st]))
        rb = np.argsort(np.argsort(W[m][st]))
        rho = float(np.corrcoef(ra, rb)[0, 1])
        ueb = int((ausw["A"] & ausw[m]).sum())
        anteil = ueb / max(int(ausw["A"].sum()), 1)
        print("      %-6s %12.4f %11.1f %% %12d" % (m, rho, 100 * anteil, ueb))

    # ── FALLE 2: welche der beiden Stellen traegt den Unterschied? ───
    print()
    print("  FALLE 2  WELCHE STELLE TRAEGT DEN UNTERSCHIED?")
    print("      (Auswahl nach A, aber Stopweite aus B)")
    sig = ausw.get("A")
    if sig is not None:
        rein = float(R["A"][sig].mean())
        kreuz = float(WA_RB[sig].mean())
        print("      Auswahl A + Stop A : E[R] %+.4f" % rein)
        print("      Auswahl A + Stop B : E[R] %+.4f  (Differenz %+.4f)"
              % (kreuz, kreuz - rein))
        print("      ➤ %s"
              % ("die STOPWEITE traegt den Unterschied"
                 if abs(kreuz - rein) > 0.02 else
                 "die Stopweite allein aendert wenig - es ist die AUSWAHL"))

    print()
    print("  ⚠️ Die groben Kerzen sind AGGREGIERT aus den 1-h-Kerzen.")
    print("     Dass CoinGecko-4h-Kerzen diesen entsprechen, ist damit")
    print("     NICHT gezeigt - das ist eine eigene Frage.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
