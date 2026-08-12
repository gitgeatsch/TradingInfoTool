# -*- coding: utf-8 -*-
"""Welche Fakten tragen wirklich? Gemessen, nicht behauptet.

NUTZERAUFTRAG (12.08.2026): *"damit es keine Ueberhand nimmt - u.U. kannst du
die 10 Top Fakten (laut modernen Methoden) mit relevanten Zusatzinfos
heranziehen, damit ich etwas anfangen kann."*

"Laut modernen Methoden" haette ich aus der Literatur abschreiben koennen -
Momentum, 52-Wochen-Hoch, Illiquiditaet, alles belegt. Das waere aber eine
Aussage ueber ANDERE Maerkte und andere Zeitraeume. Hier wird gemessen, was in
UNSEREN Reihen traegt, und die Literatur dient als Deutung des Ergebnisses,
nicht als Ersatz dafuer.

DER MASSSTAB IST DIE GEOMETRIE, DIE DIE APP VORSCHLAEGT: Stop 2,5 x ATR, Ziel
CRV 2,0, Fenster 10 Handelstage. Ein Merkmal "traegt", wenn das oberste
Fuenftel eine andere Trefferquote hat als das unterste. Alles andere - hoehere
Rendite, schoenere Korrelation - misst etwas, das wir nicht handeln.

VIER PFLICHTPRUEFUNGEN:

  1. Ueberlappen die Daten?   37 Symbole mit >= 500 Tagen, 63.389 Zeilen
  2. Blickt etwas nach vorn?  nein - Merkmal an t, Ausgang ab t+1. Perzentile
                              laufen ueber ein RUECKWAERTS-Fenster von 250 Tagen
  3. Nullbefund?              kein Unterschied zwischen den Fuenfteln, oder
                              einer ohne Ordnung (Zickzack statt monoton)
  4. Stichprobe?              je Fuenftel einige tausend Anker - ABER die Anker
                              eines Symbols sind nicht unabhaengig, und die
                              Kryptowerte untereinander erst recht nicht.
                              Deshalb CLUSTER-BOOTSTRAP UEBER SYMBOLE, nicht
                              ueber Anker (eigene Methodik, Arbeitsstand 2)

DIE ZWEITE FALLE: ZWOELF MERKMALE SIND ZWOELF TESTS. Bei zwoelf Versuchen sieht
eines zufaellig gut aus. Deshalb zaehlt hier nicht nur der Abstand zwischen
oberstem und unterstem Fuenftel, sondern auch, ob die Ordnung MONOTON ist -
ein Merkmal, das im Zickzack laeuft, hat keinen Mechanismus, sondern Rauschen.
"""
from __future__ import annotations

import sqlite3

import numpy as np

DB = "data/tradinginfotool.db"
MIN_TAGE = 500
HORIZONT = 10
STOP_ATR = 2.5
CRV = 2.0
ATR_FENSTER = 14
RUECKBLICK = 250
FUENFTEL = 5


def lade_symbole() -> dict:
    con = sqlite3.connect(DB)
    syms = [r[0] for r in con.execute(
        "SELECT symbol FROM price_history_ohlc WHERE currency='USD' "
        "GROUP BY symbol HAVING COUNT(*) >= ?", (MIN_TAGE,))]
    aus = {}
    for s in syms:
        rows = con.execute(
            "SELECT date, high, low, close, volume FROM price_history_ohlc "
            "WHERE symbol=? AND currency='USD' ORDER BY date", (s,)).fetchall()
        aus[s] = (np.array([r[0] for r in rows]),
                  np.array([float(r[1]) for r in rows]),
                  np.array([float(r[2]) for r in rows]),
                  np.array([float(r[3]) for r in rows]),
                  np.array([float(r[4] or 0) for r in rows]))
    con.close()
    return aus


def _atr(h, l, c, n=ATR_FENSTER):
    tr = np.maximum(h[1:] - l[1:],
                    np.maximum(np.abs(h[1:] - c[:-1]), np.abs(l[1:] - c[:-1])))
    aus = np.full(len(c), np.nan)
    for i in range(n, len(c)):
        aus[i] = tr[i - n:i].mean()
    return aus


def _perzentil_rueckwaerts(x, fenster=RUECKBLICK):
    """Rang im eigenen Rueckblick - NIE ueber die ganze Reihe.

    Ein Perzentil ueber die Gesamtreihe kennt die Zukunft: es weiss, wie hoch
    die Volatilitaet spaeter noch steigen wird. Genau diese Sorte Blick nach
    vorn hat dieses Projekt schon einmal eine ganze Messreihe gekostet."""
    aus = np.full(len(x), np.nan)
    for i in range(fenster, len(x)):
        f = x[i - fenster:i]
        f = f[~np.isnan(f)]
        if len(f) > 30:
            aus[i] = (f < x[i]).mean()
    return aus


def merkmale(h, l, c, v):
    a = _atr(h, l, c)
    n = len(c)
    m = {}

    def verschoben(k):
        aus = np.full(n, np.nan)
        aus[k:] = c[k:] / c[:-k] - 1
        return aus

    m["Trend 250 Tage"] = verschoben(250)
    m["Trend 60 Tage"] = verschoben(60)
    m["Trend 20 Tage"] = verschoben(20)

    hoch = np.full(n, np.nan); tief = np.full(n, np.nan)
    for i in range(250, n):
        hoch[i] = c[i - 250:i + 1].max(); tief[i] = c[i - 250:i + 1].min()
    m["Stand im Jahresbereich"] = (c - tief) / np.where(hoch - tief > 0, hoch - tief, np.nan)

    ath = np.array([c[:i + 1].max() for i in range(n)])
    m["Abstand zum Allzeithoch"] = c / ath - 1

    ema = np.full(n, np.nan)
    if n > 50:
        k = 2 / 51
        e = c[:50].mean()
        for i in range(50, n):
            e = c[i] * k + e * (1 - k); ema[i] = e
    m["Abstand zur 50-Tage-Linie"] = c / ema - 1

    m["Schwankungsbreite (Perzentil)"] = _perzentil_rueckwaerts(a / c)
    m["Tagesspanne (Perzentil)"] = _perzentil_rueckwaerts((h - l) / c)

    vm = np.full(n, np.nan)
    for i in range(20, n):
        s = v[i - 20:i].mean()
        if s > 0:
            vm[i] = v[i] / s
    m["Volumen zum Mittel"] = vm

    ret = np.full(n, np.nan); ret[1:] = np.abs(c[1:] / c[:-1] - 1)
    umsatz = v * c
    amihud = np.where(umsatz > 0, ret / umsatz, np.nan)
    m["Illiquiditaet (Amihud)"] = _perzentil_rueckwaerts(amihud)

    dd = np.full(n, np.nan)
    for i in range(60, n):
        dd[i] = c[i] / c[i - 60:i + 1].max() - 1
    m["Rueckgang seit 60-Tage-Hoch"] = dd

    gew = np.full(n, np.nan); ver = np.full(n, np.nan)
    d = np.diff(c, prepend=c[0])
    for i in range(14, n):
        f = d[i - 14:i]
        gew[i] = f[f > 0].sum(); ver[i] = -f[f < 0].sum()
    m["RSI 14"] = np.where(gew + ver > 0, 100 * gew / (gew + ver), np.nan)
    return m, a


def ausgang(h, l, c, a, i):
    if np.isnan(a[i]) or a[i] <= 0:
        return None
    stop = c[i] - STOP_ATR * a[i]
    ziel = c[i] + CRV * STOP_ATR * a[i]
    for j in range(i + 1, min(i + 1 + HORIZONT, len(c))):
        if l[j] <= stop:
            return 0.0
        if h[j] >= ziel:
            return 1.0
    return None


def cluster_bootstrap(je_symbol: dict, runden=2000):
    """Ueber SYMBOLE ziehen, nicht ueber Anker.

    Die Anker eines Symbols ueberlappen (250-Tage-Fenster, 10-Tage-Horizont),
    und die Kryptowerte laufen untereinander stark im Gleichschritt. Ein
    Bootstrap ueber Anker wuerde Intervalle liefern, die um ein Vielfaches zu
    eng sind - der Fehler, der am 09.08. eine 8.441-Faelle-Messung entwertet
    hat."""
    syms = [s for s, w in je_symbol.items() if len(w[0]) and len(w[1])]
    if len(syms) < 5:
        return float("nan"), float("nan")
    rng = np.random.default_rng(20260812)
    zieh = []
    for _ in range(runden):
        pick = rng.choice(syms, size=len(syms), replace=True)
        o = [x for s in pick for x in je_symbol[s][1]]
        u = [x for s in pick for x in je_symbol[s][0]]
        if o and u:
            zieh.append(np.mean(o) - np.mean(u))
    if not zieh:
        return float("nan"), float("nan")
    return float(np.percentile(zieh, 2.5)), float(np.percentile(zieh, 97.5))


def main() -> int:
    daten = lade_symbole()
    print(f"{len(daten)} Symbole, {sum(len(x[0]) for x in daten.values()):,} Zeilen\n"
          f"Massstab: Stop {STOP_ATR} x ATR, Ziel CRV {CRV}, Fenster {HORIZONT} Tage\n")

    sammel: dict[str, dict] = {}
    basis_alle = []
    for sym, (d, h, l, c, v) in daten.items():
        m, a = merkmale(h, l, c, v)
        aus = np.array([ausgang(h, l, c, a, i) if i < len(c) - HORIZONT else None
                        for i in range(len(c))], dtype=object)
        gueltig = np.array([x is not None for x in aus])
        basis_alle += [float(x) for x in aus[gueltig]]
        for name, werte in m.items():
            ok = gueltig & ~np.isnan(np.asarray(werte, dtype=float))
            if ok.sum() < 100:
                continue
            w = np.asarray(werte, dtype=float)[ok]
            e = np.array([float(x) for x in aus[ok]])
            gr = np.quantile(w, np.linspace(0, 1, FUENFTEL + 1)[1:-1])
            eimer = np.digitize(w, gr)
            sammel.setdefault(name, {})[sym] = [e[eimer == k] for k in range(FUENFTEL)]

    basis = float(np.mean(basis_alle))
    print(f"Basis ueber alle {len(basis_alle):,} Anker: {100 * basis:.1f} % Treffer\n")

    ergebnis = []
    for name, je_sym in sammel.items():
        eimer = [np.concatenate([je_sym[s][k] for s in je_sym
                                 if len(je_sym[s][k])]) for k in range(FUENFTEL)]
        if any(len(e) < 100 for e in eimer):
            continue
        quoten = [float(e.mean()) for e in eimer]
        spanne = quoten[-1] - quoten[0]
        # MONOTON? Ein Zickzack hat keinen Mechanismus. Gezaehlt wird, wie
        # viele der vier Schritte in dieselbe Richtung gehen wie die Spanne.
        schritte = np.diff(quoten)
        gleich = int(sum(1 for s in schritte if np.sign(s) == np.sign(spanne)))
        u, o = cluster_bootstrap(
            {s: (je_sym[s][0], je_sym[s][-1]) for s in je_sym}, runden=600)
        ergebnis.append((abs(spanne), name, quoten, spanne, gleich, u, o))

    ergebnis.sort(reverse=True)
    print(f"{'Merkmal':<32}{'unterstes':>10}{'oberstes':>10}{'Spanne':>9}"
          f"{'monoton':>9}   95 %-Band (Cluster ueber Symbole)")
    print("-" * 104)
    for _, name, q, sp, gl, u, o in ergebnis:
        traegt = "" if (np.isnan(u) or u <= 0 <= o) else "   <- Band ohne Null"
        print(f"{name:<32}{100 * q[0]:>9.1f}%{100 * q[-1]:>9.1f}%"
              f"{100 * sp:>+8.1f}pp{gl:>6}/4   "
              f"{100 * u:>+6.1f} .. {100 * o:>+6.1f} pp{traegt}")
    print(f"\nZwoelf Merkmale sind zwoelf Tests - bei zwoelf Versuchen sieht eines\n"
          f"zufaellig gut aus. Belastbar ist nur, was BEIDES hat: ein Band ohne\n"
          f"Null UND eine monotone Ordnung (4/4 oder 3/4).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
