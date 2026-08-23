# -*- coding: utf-8 -*-
"""WELCHE Eigenschaft eines Assets erklaert den Tagewahl-Vorsprung? (23.08.2026)

DIE NUTZERKRITIK, DIE DAZU GEFUEHRT HAT. Am 23.08. wurde gemessen, dass der
Vorsprung gegen den quotengleichen Zufall sich je Symbol NICHT wiederholt
(Spearman +0,019). Daraus hatte ich geschlossen, die Einzelsymbolebene sei
nicht brauchbar. ⚠️ DAS WAR EIN ZU ENGER SCHLUSS - und er verletzt die eigene
Regel "einen Nullbefund als ZERLEGUNG ablegen, nicht als erledigt":

    Nicht messbar war, ob ein Symbol seinen VORSPRUNG wiederholt.
    Nicht gemessen war, ob eine EIGENSCHAFT des Symbols ihn erklaert.

Das ist nicht dasselbe. Der Vorsprung eines Fensters ist ein Ergebnis und
rauscht; eine Eigenschaft wie Liquiditaet ist ein Zustand und ist traege.

DIE LITERATUR SAGT DIE ANTWORT VORAUS, und sie nennt die Groesse:

    "Illiquid cryptocurrencies exhibit daily short-term price reversals,
     whereas liquid ones display daily momentum ... this daily reversal effect
     results from the illiquidity of the vast majority of traded
     cryptocurrencies."
     - Up or down? Short-term reversal, momentum, and liquidity effects in
       cryptocurrency markets, International Review of Financial Analysis 2021
       https://www.sciencedirect.com/science/article/pii/S1057521921002349

    Drei Faktoren - Markt, GROESSE, Momentum - erklaeren den Querschnitt der
    Kryptorenditen.
     - Liu, Tsyvinski, Wu: Common Risk Factors in Cryptocurrency,
       Journal of Finance 2022, https://onlinelibrary.wiley.com/doi/abs/10.1111/jofi.13119

⚠️ DAMIT IST DIE VERMUTUNG PRUEFBAR: nicht die Marktkapitalisierung ist die
relevante Groesse, sondern die ILLIQUIDITAET. Und genau dazu passt der eigene
Befund, dass BTC - der liquideste Wert - den KLEINSTEN Vorsprung aller
Kryptogruppen hat (+0,052 gegen +0,153).

DER AUFBAU - und was ihn ehrlich haelt:

    Eigenschaft   aus den 252 Tagen VOR dem Fenster
    Ergebnis      Vorsprung IM Fenster
    -> die Eigenschaft ist zum Zeitpunkt der Entscheidung bekannt.

⚠️ DAS IST DER UNTERSCHIED ZUR KAPITALISIERUNGSGRUPPE von heute Vormittag:
jene war der Stand von HEUTE, rueckwirkend auf alte Fenster geklebt. Diese hier
ist vorwaerts verwendbar.

FUENF EIGENSCHAFTEN, VORAB BENANNT (Suchpreis: fuenf benannte Zellen, keine
Suche ueber Dutzende):

    illiquiditaet   Amihud 2002: Mittel von |Rendite| / Umsatz in USD
    volatilitaet    Standardabweichung der Tagesrenditen
    umsatz          mittlerer Tagesumsatz in USD (Groessenproxy, historisch
                    sauber - die Kapitalisierung ist es nicht)
    alter           Handelstage seit Reihenbeginn
    beta_btc        Korrelation der Tagesrenditen zu BTC (nur Krypto)

Positivkontrolle: `umsatz` und `illiquiditaet` muessen stark gegenlaeufig sein.
Sind sie es nicht, ist eine der beiden falsch gerechnet.
"""
from __future__ import annotations

import argparse
from collections import defaultdict

import numpy as np

from messe_akkumulation import BUDGET, PERIODE, VORLAUF, simuliere
from messe_akkumulation_phasen import SAAT, zufall_gleiche_quote
from messe_tagewahl_je_symbol import FENSTER_TERMINE, MINDEST_TERMINE, fenster

REGELN = ("UNTER_SMA", "RUECKGANG")
EIGENSCHAFTEN = ("illiquiditaet", "volatilitaet", "umsatz", "alter",
                 "beta_btc", "abstand_sma", "eigener_rueckgang",
                 "markt_abstand_sma")
RUECKBLICK = 252


def eigenschaften(c, v, von, btc_rend=None, btc_index=None,
                  markt=None) -> dict:
    """Alles aus den 252 Tagen VOR `von` - nichts aus dem Fenster."""
    a = max(0, von - RUECKBLICK)
    kurse, vol = c[a:von], v[a:von]
    if len(kurse) < 60:
        return {}
    rend = np.diff(kurse) / kurse[:-1]
    umsatz = vol[1:] * kurse[1:]
    gilt = umsatz > 0
    if gilt.sum() < 30:
        return {}
    aus = {
        # Amihud: je hoeher, desto illiquider. x 1e6, damit die Zahl lesbar ist.
        "illiquiditaet": float(np.mean(np.abs(rend[gilt]) / umsatz[gilt]) * 1e6),
        "volatilitaet": float(np.std(rend)),
        "umsatz": float(np.mean(umsatz[gilt])),
        "alter": float(von),
        # ZUSTAND STATT SCHALTER (Nutzervorgabe 23.08.): die Marktphase als
        # stetige Groesse, bekannt VOR dem Fenster. Ein Etikett
        # "steigend/fallend" waere ein Schalter und zudem erst hinterher
        # bekannt; der Abstand zum eigenen Schnitt ist beides nicht.
        "eigener_rueckgang": float(1.0 - kurse[-1] / kurse.max()),
    }
    if len(kurse) >= 200:
        aus["abstand_sma"] = float(kurse[-1] / kurse[-200:].mean() - 1.0)
    if markt is not None:
        aus["markt_abstand_sma"] = markt
    if btc_rend is not None and btc_index is not None:
        # Gepaart auf gemeinsame Tage, sonst vergleicht man Kalender.
        paare = [(r, btc_rend[btc_index[t]])
                 for r, t in zip(rend, range(a + 1, von))
                 if t in btc_index]
        if len(paare) >= 30:
            x, y = np.array([p[0] for p in paare]), np.array([p[1] for p in paare])
            if x.std() > 0 and y.std() > 0:
                aus["beta_btc"] = float(np.corrcoef(x, y)[0, 1])
    return aus


def main() -> int:
    import config

    from backtest_llm1_historisch import lade_reihen_aus_db

    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--db", default="data/tradinginfotool.db")
    p.add_argument("--schwelle", type=float, default=0.20)
    p.add_argument("--klasse", default="krypto")
    args = p.parse_args()

    klasse_von = {a.symbol: a.assetklasse for a in config.get_watchlist()}
    reihen = {s: r for s, r in lade_reihen_aus_db(args.db).items()
              if klasse_von.get(s) == args.klasse}
    rng = np.random.RandomState(SAAT)

    btc = reihen.get("BTC")
    btc_rend = btc_pos = None
    btc_sma = {}
    if btc:
        bc = np.array([k.close for k in btc], dtype=float)
        btc_rend = np.diff(bc) / bc[:-1]
        # Datum -> Index in btc_rend (Rendite von i-1 auf i steht bei i-1)
        btc_pos = {k.date: i - 1 for i, k in enumerate(btc) if i > 0}
        # DER MARKT als stetiger Zustand: BTCs Abstand zu seinem eigenen
        # 200-Tage-Schnitt am Tag des Fensterbeginns. Kein Etikett, kein
        # Schalter - und bekannt, BEVOR gekauft wird.
        btc_datum = {k.date: i for i, k in enumerate(btc)}
        btc_sma = {}
        for datum, i in btc_datum.items():
            if i >= 200:
                btc_sma[datum] = float(bc[i] / bc[i - 200:i].mean() - 1.0)

    # Ein Datensatz je (Symbol, Fenster): Eigenschaften davor, Vorsprung darin
    zeilen = []
    for sym, r in reihen.items():
        c = np.array([k.close for k in r], dtype=float)
        v = np.array([(k.volume or 0.0) for k in r], dtype=float)
        if len(c) < VORLAUF + MINDEST_TERMINE * PERIODE:
            continue
        # Datum -> gemeinsamer Index fuer die BTC-Paarung
        idx = {k.date: btc_pos.get(k.date) for k in r} if btc_pos else {}
        idx = {i: idx[k.date] for i, k in enumerate(r)
               if idx.get(k.date) is not None}
        for von, bis in fenster(len(c)):
            e = eigenschaften(c, v, von, btc_rend, idx,
                              markt=btc_sma.get(r[von].date))
            if not e:
                continue
            gesamt = BUDGET * len(range(von, bis, PERIODE))
            for regel in REGELN:
                wert = simuliere(c, args.klasse, regel, args.schwelle,
                                 von=von, bis=bis)[0] / gesamt
                zufall = zufall_gleiche_quote(c, args.klasse, regel,
                                              args.schwelle, von, bis,
                                              rng) / gesamt
                if zufall == zufall:
                    zeilen.append({"symbol": sym, "regel": regel,
                                   "vorsprung": wert - zufall, **e})

    print(f"{args.klasse}: {len({z['symbol'] for z in zeilen})} Symbole · "
          f"{len(zeilen)//len(REGELN)} Fenster · Eigenschaften aus den "
          f"{RUECKBLICK} Tagen DAVOR\n")

    # --- Positivkontrolle -----------------------------------------------
    ill = [z["illiquiditaet"] for z in zeilen if z["regel"] == REGELN[0]]
    ums = [z["umsatz"] for z in zeilen if z["regel"] == REGELN[0]]
    r_ill = _spearman(ill, ums)
    print(f"POSITIVKONTROLLE  Illiquiditaet gegen Umsatz: Spearman "
          f"{r_ill:+.3f}   " + ("BESTANDEN" if r_ill < -0.5
                                else "⚠️ NICHT BESTANDEN - eine der beiden "
                                     "Groessen ist falsch gerechnet"))

    # --- Terzile je Eigenschaft -----------------------------------------
    for regel in REGELN:
        z = [x for x in zeilen if x["regel"] == regel]
        print(f"\n=== {regel} · {len(z)} Fenster ===")
        print(f"{'Eigenschaft':16} {'Spearman':>9}   "
              f"{'unteres Drittel':>16} {'mittleres':>12} {'oberes':>12}")
        for e in EIGENSCHAFTEN:
            hat = [x for x in z if e in x]
            if len(hat) < 15:
                print(f"{e:16} {'zu wenige':>9}   ({len(hat)} Fenster)")
                continue
            w = [x[e] for x in hat]
            y = [x["vorsprung"] for x in hat]
            rho = _spearman(w, y)
            g1, g2 = np.percentile(w, [33.3, 66.7])
            terzile = [
                np.mean([b for a, b in zip(w, y) if a <= g1]),
                np.mean([b for a, b in zip(w, y) if g1 < a <= g2]),
                np.mean([b for a, b in zip(w, y) if a > g2])]
            print(f"{e:16} {rho:+9.3f}   " + " ".join(
                f"{t:+12.4f}" for t in terzile)
                + ("   <-- traegt" if abs(rho) >= 0.25 else ""))
    print("\n⚠️ Keine Signifikanzaussage: die Fenster ueberlappen ueber "
          "Symbole hinweg in der Zeit.\n   Was zaehlt, ist ein Vorzeichen, "
          "das in beiden Regeln dasselbe ist.")
    return 0


def _spearman(a, b) -> float:
    if len(a) < 3:
        return float("nan")
    ra = np.argsort(np.argsort(a))
    rb = np.argsort(np.argsort(b))
    return float(np.corrcoef(ra, rb)[0, 1])


if __name__ == "__main__":
    raise SystemExit(main())
