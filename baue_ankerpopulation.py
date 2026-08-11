# -*- coding: utf-8 -*-
"""Die geschichtete Ankerpopulation - Grundlage ALLER offenen Messungen.

WARUM ES SIE BRAUCHT. Jede bisherige Messung lief auf Ankern, die NACH IHREM
AUSGANG ausgewaehlt waren: die acht aus Arbeitsstand 7.8 wurden genommen, weil
sie zweistellige Gewinne brachten. Damit laesst sich zeigen, dass ein Fix etwas
verbessert - aber niemals, dass er nichts kaputt macht. Ein Fix, der
`_struktur()` einfach immer "Aufwaertstrend" sagen liesse, bekaeme dort 6 von 6.

Diese Population wird ausschliesslich nach EINGANGSMERKMALEN geschichtet. Der
Ausgang wird erst NACH der Auswahl berechnet und mitgeschrieben - er kann also
nicht zur Auswahl beigetragen haben. Dasselbe Prinzip stand schon in
`messe_betragsdeckel.py`, wurde dort aber nur fuer die Renditespalte angewandt,
nicht fuer die Ankerwahl selbst.

DIE VIER ZELLEN, aus dem Befund vom 11.08. (Arbeitsstand 7.11):

    A   Etikett ABWAERTS, 60-Tage-Bewegung >= +S     der vermutete Defekt
    B   Etikett ABWAERTS, 60-Tage-Bewegung <= -S     Etikett zu Recht
    C   Etikett AUFWAERTS, 60-Tage-Bewegung <= -S    das SPIEGELBILD
    D   Etikett AUFWAERTS, 60-Tage-Bewegung >= +S    Etikett zu Recht

B und D sind die Falsch-Positiv-Sperre. Ohne sie misst man nur, ob ein Fix in
die gewuenschte Richtung wirkt - nicht, ob er ueberall wirkt. C ist die groessere
Haelfte: das Aufwaerts-Etikett bei fallendem Fenster tritt in 11,39 % der
Krypto-Tage auf, der umgekehrte Fall in 6,21 %.

DREI SCHRANKEN, jede aus einem bezahlten Fehler:

    VORLAUF     220 Kerzen vor dem Anker - dieselbe Schranke wie in der Kette,
                sonst misst die Auswahl etwas anderes als der Betrieb liest.
    ZUKUNFT     40 Handelstage danach. Methodik 2.18, Zusicherung 3: fuer einen
                Horizont von N Tagen muss der Anker N Tage vor dem Reihenende
                liegen - sonst faellt er still heraus statt aufzufallen.
    ABSTAND     mindestens ein Horizont zwischen zwei Ankern DESSELBEN Symbols.
                Ueberlappende Auswertungsfenster verletzen die
                Unabhaengigkeitsannahme (Methodik 2.19.1, Lopez de Prado):
                der 24.06. und der 25.06. schauen auf fast dieselbe Zukunft.
                Ohne diese Schranke sind 32 Anker keine 32 Beobachtungen.

Und eine vierte, aus dem Verlustquellen-Befund: kein Symbol stellt mehr als
`MAX_JE_SYMBOL` Anker je Zelle. Fuenf Symbole stellten einmal 102 % des
Minus - eine Stichprobe, die an wenigen Symbolen haengt, misst diese Symbole.

    python baue_ankerpopulation.py --db <pfad> --je-zelle 8
"""
from __future__ import annotations

import argparse
import json
import random
import sys
from collections import Counter, defaultdict

import numpy as np

from backtest_llm1_historisch import lade_reihen_aus_db
from agent.lagebeschreibung import FENSTER_SWING, _struktur

W = FENSTER_SWING
VORLAUF = 220
ZUKUNFT = 40
MIN_ABSTAND = 40          # ein Horizont zwischen Ankern desselben Symbols
MAX_JE_SYMBOL = 2         # je Zelle
SCHWELLE_PCT = 10.0
SEED = 20260811


def _fraktale(h: np.ndarray, l: np.ndarray):
    hi, lo = [], []
    for i in range(W, len(h) - W):
        if h[i] == h[i - W:i + W + 1].max():
            hi.append(i)
        if l[i] == l[i - W:i + W + 1].min():
            lo.append(i)
    return hi, lo


def _etikett(h, l, hi_all, lo_all, i: int) -> str | None:
    """Dasselbe Urteil wie `_struktur()`, aus vorberechneten Fraktalen."""
    grenze = i - W
    hi = [j for j in hi_all if j <= grenze]
    lo = [j for j in lo_all if j <= grenze]
    if len(hi) < 2 or len(lo) < 2:
        return None
    hoch = h[hi[-1]] > h[hi[-2]]
    tief = l[lo[-1]] > l[lo[-2]]
    if hoch and tief:
        return "aufwaerts"
    if not hoch and not tief:
        return "abwaerts"
    return None           # Spannenfaelle gehoeren in keine der vier Zellen


def _zelle(etikett: str, bew60: float, schwelle: float) -> str | None:
    if etikett == "abwaerts":
        if bew60 >= schwelle:
            return "A"
        if bew60 <= -schwelle:
            return "B"
    elif etikett == "aufwaerts":
        if bew60 <= -schwelle:
            return "C"
        if bew60 >= schwelle:
            return "D"
    return None


def erstdurchgang(reihe, idx: int, atr: float, ziel_atr=3.0, stop_atr=1.5) -> dict:
    """Was zuerst erreicht wird. Wird ERST NACH der Auswahl gerechnet.

    Beruehren High und Low am selben Tag beide Schwellen, gilt der STOP: aus
    Tagesdaten ist die Reihenfolge innerhalb des Tages nicht erkennbar, und die
    guenstige Annahme waere genau die, die im Rueckblick zu gut aussieht."""
    if atr <= 0:
        return {"ereignis": "unbestimmt"}
    ein = float(reihe[idx].close)
    ziel, stop = ein + ziel_atr * atr, ein - stop_atr * atr
    for n in range(1, ZUKUNFT + 1):
        j = idx + n
        if j >= len(reihe):
            break
        if float(reihe[j].low) <= stop:
            return {"ereignis": "STOP", "tag": n}
        if float(reihe[j].high) >= ziel:
            return {"ereignis": "ZIEL", "tag": n}
    return {"ereignis": "offen", "tag": None}


def main() -> int:
    from indicators.calculations import atr_wilder, latest_value
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--db", default="data/tradinginfotool.db")
    p.add_argument("--je-zelle", type=int, default=8)
    p.add_argument("--schwelle", type=float, default=SCHWELLE_PCT)
    p.add_argument("--ausgabe", default="ankerpopulation.json")
    args = p.parse_args()

    import config
    reihen = lade_reihen_aus_db(args.db)      # Waechter filtert Nicht-Tageskerzen

    # NUR HANDELBARE ASSETS (Korrektur beim ersten Lauf, 11.08.). Die
    # Kursdatenbank fuehrt neben den Watchlist-Assets auch REFERENZREIHEN:
    # `_ROHSTOFF_FUTURES_*` (die liquide Futures-Reihe hinter einem ETC),
    # `_THEMEN_ETF_BENCHMARK_SPY`, `_HEDGE_INDEX_*`. Im ersten Lauf stellten sie
    # in Zelle A vier von sechs Symbolen.
    #
    # Sie gehoeren nicht in die Population: wir handeln den ETC, nicht den
    # Future, und SPY ist ein Massstab, kein Kandidat. Eine Messung auf ihnen
    # beschriebe ein System, das es nicht gibt - und sie sind ausgerechnet die
    # laengsten Reihen (bis 1993), waeren also ueberproportional vertreten.
    handelbar = {a.symbol for a in config.get_watchlist()}
    verworfen = sorted(set(reihen) - handelbar)
    reihen = {s: r for s, r in reihen.items() if s in handelbar}
    print(f"DATENQUELLE: {args.db}")
    print(f"{len(reihen)} handelbare Reihen; {len(verworfen)} Referenzreihen "
          f"ausgeschlossen: {', '.join(verworfen)}")
    print(f"SCHWELLE: 60-Tage-Bewegung +/- {args.schwelle:.0f} %\n")

    # --- 1. alle in Frage kommenden Anker sammeln, NUR nach Eingangsmerkmalen
    kandidaten: dict[str, list] = defaultdict(list)
    for sym, r in reihen.items():
        if len(r) < VORLAUF + ZUKUNFT + 1:
            continue
        c = np.array([k.close for k in r], dtype=float)
        h = np.array([k.high for k in r], dtype=float)
        l = np.array([k.low for k in r], dtype=float)
        hi, lo = _fraktale(h, l)
        for i in range(VORLAUF, len(c) - ZUKUNFT):
            e = _etikett(h, l, hi, lo, i)
            if e is None:
                continue
            bew60 = 100.0 * (c[i] / c[i - 60] - 1.0)
            z = _zelle(e, bew60, args.schwelle)
            if z:
                kandidaten[z].append((sym, i, r[i].date, round(bew60, 1)))

    print("Kandidaten je Zelle, vor der Ziehung:")
    for z in "ABCD":
        n_sym = len({k[0] for k in kandidaten[z]})
        print(f"  {z}  {len(kandidaten[z]):6} Anker ueber {n_sym:2} Symbole")

    # --- 2. ziehen: Abstand einhalten, Symbole deckeln, reproduzierbar
    rng = random.Random(SEED)
    gezogen: dict[str, list] = {}
    for z in "ABCD":
        pool = sorted(kandidaten[z])
        rng.shuffle(pool)
        gewaehlt, je_symbol, belegt = [], Counter(), defaultdict(list)
        for sym, i, datum, bew60 in pool:
            if len(gewaehlt) >= args.je_zelle:
                break
            if je_symbol[sym] >= MAX_JE_SYMBOL:
                continue
            if any(abs(i - j) < MIN_ABSTAND for j in belegt[sym]):
                continue
            gewaehlt.append({"symbol": sym, "index": i, "datum": datum,
                             "bewegung_60t_pct": bew60, "zelle": z})
            je_symbol[sym] += 1
            belegt[sym].append(i)
        gezogen[z] = gewaehlt

    # --- 3. Ausgang ERST JETZT berechnen ----------------------------------
    for z in "ABCD":
        for a in gezogen[z]:
            r = reihen[a["symbol"]]
            i = a["index"]
            hh = np.array([k.high for k in r[:i + 1]], dtype=float)
            ll = np.array([k.low for k in r[:i + 1]], dtype=float)
            cc = np.array([k.close for k in r[:i + 1]], dtype=float)
            atr = float(latest_value(atr_wilder(hh, ll, cc)) or 0.0)
            a["atr"] = round(atr, 6)
            a["ausgang"] = erstdurchgang(r, i, atr)

    print("\nGezogen:")
    for z in "ABCD":
        aus = Counter(a["ausgang"]["ereignis"] for a in gezogen[z])
        syms = ", ".join(sorted({a["symbol"] for a in gezogen[z]}))
        print(f"  {z}  {len(gezogen[z])} Anker | Ausgang {dict(aus)}")
        print(f"     {syms}")

    alle = [a for z in "ABCD" for a in gezogen[z]]
    with open(args.ausgabe, "w", encoding="utf-8") as f:
        json.dump({"seed": SEED, "schwelle_pct": args.schwelle,
                   "vorlauf": VORLAUF, "zukunft": ZUKUNFT,
                   "min_abstand": MIN_ABSTAND, "max_je_symbol": MAX_JE_SYMBOL,
                   "anker": alle}, f, ensure_ascii=False, indent=1)
    print(f"\n{len(alle)} Anker geschrieben nach {args.ausgabe}")
    print("\nLESART: Die Auswahl kennt den Ausgang NICHT - er steht erst danach")
    print("in der Datei. Eine Zelle, deren Ausgaenge einseitig aussehen, ist ein")
    print("BEFUND ueber den Markt, kein Auswahlfehler.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
