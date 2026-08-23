# -*- coding: utf-8 -*-
"""Traegt die Tagewahl je SYMBOL - und bleibt sie dort? (23.08.2026)

DIE FRAGE NACH DEM BEFUND VOM 23.08. `messe_akkumulation_phasen.py` hat
gezeigt: antizyklische Regeln schlagen ihren QUOTENGLEICHEN Zufall - dieselben
Betraege, dieselbe Anzahl Kauftage, nur die Tage gewuerfelt. In beiden
Marktphasen, in allen drei Anlageklassen.

Das war eine Aussage ueber die REGEL. Fuer eine Auswahl braucht es eine ueber
das SYMBOL:

    Regelaussage    "antizyklisch kaufen traegt"        -> sagt WIE
    Symbolaussage   "bei DIESEM Wert traegt es mehr"    -> sagt WO

⚠️ UND DIE ZWEITE IST DIE SCHWERERE. Ein Vorsprung, den es nur im Mittel gibt,
begruendet keine Auswahl. Ranggeordnet werden kann nur, was BLEIBT - deshalb
misst dieses Werkzeug nicht nur den Vorsprung je Symbol, sondern auch, ob er
sich im naechsten Fenster wiederholt.

    HOEHE          mittlerer Vorsprung gegen den quotengleichen Zufall
    BESTAENDIGKEIT Rangkorrelation zwischen Fenster t und Fenster t+1

Ohne die zweite Zahl ist die erste eine Rangliste der Vergangenheit.

DER UNTERSCHIED ZUM PHASENWERKZEUG - und warum er beabsichtigt ist:

    Fenster   52 Kauftermine (ein Jahr) statt 104
    Grund     je Symbol werden mehrere Fenster gebraucht, sonst gibt es
              nichts zu wiederholen. Der Preis: kuerzere Fenster rauschen
              staerker.

⚠️ Dass der Befund BEI EINER ANDEREN FENSTERLAENGE ueberhaupt noch steht, ist
selbst eine Pruefung. Verschwindet er hier, war er eine Eigenschaft der
Zweijahresfenster und nicht des Marktes.

DIE GRUPPIERUNG (Nutzerfrage 23.08.: BTC als eigene Klasse? Caps?)

    btc      allein - die Frage, ob er sich anders verhaelt als der Rest
    gross    >= 10 Mrd USD        mittel  1 bis 10 Mrd USD
    klein    < 1 Mrd USD

⚠️ DIE MARKTKAPITALISIERUNG IST DIE VON HEUTE, nicht die des Fensters. Ein
Wert, der heute gross ist, war 2019 klein. Die Einteilung ist deshalb
BESCHREIBEND - genau wie das Phasen-Etikett - und taugt zur Frage "verhalten
sich grosse Werte anders", nicht zu "welche Gruppe kaufe ich".

Vier Gruppen sind VORAB benannt, nicht gesucht. Der Suchpreis waechst mit der
Zahl der Zellen; drei Grenzen sind der uebliche Krypto-Schnitt und nicht aus
den Daten gewaehlt.

EINE Regeldefinition fuer alle drei Werkzeuge: `messe_akkumulation.
anteil_der_regel()`.
"""
from __future__ import annotations

import argparse
from collections import defaultdict

import numpy as np

from messe_akkumulation import BUDGET, PERIODE, VORLAUF, simuliere
from messe_akkumulation_phasen import SAAT, zufall_gleiche_quote

REGELN = ("UNTER_SMA", "RUECKGANG")
FENSTER_TERMINE = 52
MINDEST_TERMINE = 40
# Vorab benannt, nicht aus den Daten gewaehlt (uebliche Krypto-Einteilung).
GROSS_AB = 10e9
MITTEL_AB = 1e9


def fenster(n: int) -> list[tuple[int, int]]:
    aus, laenge, i = [], FENSTER_TERMINE * PERIODE, VORLAUF
    while i + MINDEST_TERMINE * PERIODE <= n:
        aus.append((i, min(i + laenge, n)))
        i += laenge
    return aus


def gruppe(symbol: str, klasse: str, kap: float | None) -> str:
    if klasse != "krypto":
        return klasse
    if symbol == "BTC":
        return "btc"
    if kap is None:
        return "krypto ohne Kap"
    return ("gross" if kap >= GROSS_AB
            else "mittel" if kap >= MITTEL_AB else "klein")


def kapitalisierung(db: str) -> dict:
    import sqlite3
    c = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    aus = {s: k for s, k in c.execute(
        "select symbol, market_cap_usd from price_cache "
        "where market_cap_usd is not null")}
    c.close()
    return aus


def main() -> int:
    import config

    from backtest_llm1_historisch import lade_reihen_aus_db

    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--db", default="data/tradinginfotool.db")
    p.add_argument("--schwelle", type=float, default=0.20)
    args = p.parse_args()

    klasse_von = {a.symbol: a.assetklasse for a in config.get_watchlist()}
    kap = kapitalisierung(args.db)
    reihen = {s: r for s, r in lade_reihen_aus_db(args.db).items()
              if s in klasse_von}
    rng = np.random.RandomState(SAAT)

    # symbol -> regel -> Liste der Fenstervorspruenge (in Reihenfolge!)
    je_symbol: dict = defaultdict(lambda: defaultdict(list))
    for sym, r in reihen.items():
        c = np.array([k.close for k in r], dtype=float)
        if len(c) < VORLAUF + MINDEST_TERMINE * PERIODE:
            continue
        kl = klasse_von[sym]
        for von, bis in fenster(len(c)):
            gesamt = BUDGET * len(range(von, bis, PERIODE))
            for regel in REGELN:
                wert = simuliere(c, kl, regel, args.schwelle,
                                 von=von, bis=bis)[0] / gesamt
                zufall = zufall_gleiche_quote(c, kl, regel, args.schwelle,
                                              von, bis, rng) / gesamt
                if zufall == zufall:
                    je_symbol[sym][regel].append(wert - zufall)

    print(f"{len(je_symbol)} Symbole · Fenster a {FENSTER_TERMINE} "
          f"Kauftermine · Vorsprung gegen den QUOTENGLEICHEN Zufall\n")

    # --- 1. je Symbol ----------------------------------------------------
    print(f"{'Symbol':10} {'Gruppe':16} {'k':>3} "
          + " ".join(f"{r:>22}" for r in REGELN))
    zeilen = []
    for sym, z in je_symbol.items():
        g = gruppe(sym, klasse_von[sym], kap.get(sym))
        k = len(z[REGELN[0]])
        mittel = {r: float(np.mean(z[r])) if z[r] else float("nan")
                  for r in REGELN}
        traegt = {r: sum(1 for v in z[r] if v > 0) for r in REGELN}
        zeilen.append((mittel[REGELN[0]], sym, g, k, mittel, traegt))
    for _s, sym, g, k, mittel, traegt in sorted(zeilen, reverse=True):
        print(f"{sym:10} {g:16} {k:3} " + " ".join(
            f"{mittel[r]:+.4f} ({traegt[r]:2}/{k:<2})".rjust(22)
            for r in REGELN))

    # --- 2. je Gruppe ----------------------------------------------------
    print(f"\n{'Gruppe':16} {'Symbole':>7} {'Fenster':>7} "
          + " ".join(f"{r:>24}" for r in REGELN))
    nach_gruppe: dict = defaultdict(lambda: defaultdict(list))
    for sym, z in je_symbol.items():
        g = gruppe(sym, klasse_von[sym], kap.get(sym))
        for r in REGELN:
            nach_gruppe[g][r] += z[r]
    for g in sorted(nach_gruppe):
        n_sym = sum(1 for s in je_symbol
                    if gruppe(s, klasse_von[s], kap.get(s)) == g)
        n_f = len(nach_gruppe[g][REGELN[0]])
        print(f"{g:16} {n_sym:7} {n_f:7} " + " ".join(
            f"{np.mean(nach_gruppe[g][r]):+.4f} "
            f"({100*np.mean([v > 0 for v in nach_gruppe[g][r]]):3.0f}% "
            f"positiv)".rjust(24) for r in REGELN))

    # --- 3. BESTAENDIGKEIT ----------------------------------------------
    print("\n⚠️ BESTAENDIGKEIT - wiederholt sich der Vorsprung im naechsten "
          "Fenster?")
    print("   (Rangkorrelation ueber alle Paare Fenster t -> t+1 desselben "
          "Symbols)")
    for r in REGELN:
        a, b = [], []
        for sym, z in je_symbol.items():
            v = z[r]
            for i in range(len(v) - 1):
                a.append(v[i])
                b.append(v[i + 1])
        if len(a) < 10:
            print(f"   {r:12} zu wenige Paare ({len(a)})")
            continue
        ra = np.argsort(np.argsort(a))
        rb = np.argsort(np.argsort(b))
        rho = float(np.corrcoef(ra, rb)[0, 1])
        gleiches_vz = float(np.mean([(x > 0) == (y > 0)
                                     for x, y in zip(a, b)]))
        print(f"   {r:12} {len(a):3} Paare · Spearman {rho:+.3f} · "
              f"gleiches Vorzeichen {100*gleiches_vz:3.0f} %"
              + ("   -> ranggeeignet" if rho > 0.2
                 else "   -> ⚠️ NICHT ranggeeignet"))
    print("\n⚠️ Ohne Bestaendigkeit ist die Rangliste oben eine Rangliste der "
          "Vergangenheit.\n   Die Marktkapitalisierung ist die von HEUTE - "
          "die Gruppierung ist beschreibend.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
