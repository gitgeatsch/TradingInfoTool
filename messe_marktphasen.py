# -*- coding: utf-8 -*-
"""Verhaelt sich die Kette in verschiedenen Marktphasen unterschiedlich?

DIE FRAGE (Nutzervorgabe 12.08.). Alles bisher Gemessene stammt aus EINER Phase.
Die stehende Projektvorgabe sagt dazu: *"Regime war IMMER baer - nie fragen ob
Modell oder Markt, das ist unbeantwortbar. Simulieren."* Genau das passiert hier.

Der Abgleich alt gegen neu (7.28) zeigte: die neue Kette handelt auf denselben
Faellen in 34 % statt 0 % - aber **16 von 17 Handlungen waren Verkaeufe**. Ob
das der Baerenmarkt ist oder eine eingebaute Schieflage, entscheidet nur ein
Lauf ueber mehrere Phasen.

DIE PHASEN, aus dem tatsaechlichen BTC-Verlauf abgelesen:

    BULLE      2024-09-18 .. 2025-05-28    61.778 -> 107.812   +74 %
    SEITWAERTS 2025-07-30 .. 2025-10-01   117.821 -> 118.600   +0,7 %
    BAER       2025-10-06 .. 2026-06-30   Allzeithoch, dann -53 %
    WENDE      2026-06-10 .. 2026-08-10    61.464 ->  64.984   +5,7 %

EINSCHRAENKUNG, VOR DEM LAUF GEPRUEFT: Die 220-Kerzen-Schranke schneidet den
Anfang der Bullenphase weg. Die Reihen beginnen am 2024-07-17, der erste
anwaehlbare Anker liegt am 2025-02-22 - der starke Lauf von September bis
November 2024 (+52,7 % im Quartal) ist damit NICHT anwaehlbar. Was tatsaechlich
gemessen wird:

    BULLE      2025-02-22 .. 2025-05-28   + 11,6 %   ( 96 Tage)
    SEITWAERTS 2025-07-30 .. 2025-10-01   +  0,7 %   ( 64 Tage)
    BAER       2025-10-06 .. 2026-06-30   - 53,1 %   (268 Tage)
    WENDE      2026-06-10 .. 2026-07-21   +  8,2 %   ( 42 Tage)

Die Phasen bleiben damit gut getrennt (+11,6 % gegen -53,1 %), aber "BULLE"
meint hier den moderaten spaeteren Teil, nicht die explosive Phase.

NUR SYMBOLE, DIE IN ALLEN VIER PHASEN VORKOMMEN (22 Stueck). Ohne diese
Schranke haette BAER 33 Symbole und BULLE 22 - der Lauf vergliche dann
Symbolmengen statt Phasen.

RUECKBLICKENDE ETIKETTEN, KEIN LOOKAHEAD. Die Phasen werden im Nachhinein
benannt, um Faelle zu GRUPPIEREN - das Modell sieht davon nichts. Seine Eingabe
bleibt streng auf `reihe[:i+1]` beschraenkt. Wer beides verwechselt, baut sich
ein Ergebnis.

MEHRERE SYMBOLE, NICHT NUR BTC. Die Phasen sind am BTC-Verlauf definiert, weil
er der Taktgeber des Kryptomarkts ist; gemessen wird aber ueber mehrere Coins.
Sonst misst der Lauf ein Symbol und nennt es einen Markt.

WAS ERWARTET WIRD, vorab notiert, damit es nachher nicht angepasst wird:
Eine brauchbare Kette kauft im Bullenmarkt haeufiger als im Baerenmarkt. Tut
sie das nicht, ist sie richtungsblind - und das waere ein Befund, kein Zufall.

    python messe_marktphasen.py --db <pfad> --je-phase 12 --trocken
"""
# GESTRICHEN AM 12.08. (L1). Dieses Skript rief `beschreibe_marktbreite()`
# direkt. Nach dem Tausch waere es ein Skript, das eine ANDERE Lage misst als
# die Produktion - genau die Umgehung, die ein glatter Schnitt ausschliessen
# soll. Es geht jetzt ueber `rollen_eingabe.baue_lagebild_eingabe()`, die
# einzige Stelle, an der die Eingabe des Lagebilds entsteht.
#
# WICHTIG FUER ALTE ERGEBNISSE: alles, was vor dem 12.08. mit diesem Skript
# gemessen wurde, traegt die Marktbreite. Ein Vergleich alt/neu ueber diese
# Grenze hinweg misst den Umbau mit, nicht die Sache.
from __future__ import annotations

import argparse
import json
import random
import sys
from collections import Counter, defaultdict

import numpy as np

SEED = 20260812
MIN_ABSTAND = 20        # Handelstage zwischen Ankern desselben Symbols

PHASEN = {
    "BULLE":      ("2024-09-18", "2025-05-28"),
    "SEITWAERTS": ("2025-07-30", "2025-10-01"),
    "BAER":       ("2025-10-06", "2026-06-30"),
    "WENDE":      ("2026-06-10", "2026-08-10"),
}


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--db", default="data/tradinginfotool.db")
    p.add_argument("--je-phase", type=int, default=12)
    p.add_argument("--anbieter", default="gemini35")
    p.add_argument("--ausgabe", default="marktphasen.json")
    p.add_argument("--trocken", action="store_true")
    args = p.parse_args()

    import pruefe_rollenkette as PR
    PR.DB = args.db

    import config
    import agent.rolle_analyst as RA
    import agent.rolle_trader as RT
    from agent.lagebeschreibung import beschreibe_lage
    from backtest_llm1_historisch import lade_reihen_aus_db
    from indicators.calculations import atr_wilder, latest_value

    klasse = {a.symbol: a.assetklasse for a in config.get_watchlist()}
    reihen = lade_reihen_aus_db(args.db)
    krypto = {s: r for s, r in reihen.items() if klasse.get(s) == "krypto"}

    # Nur Symbole, die in ALLEN Phasen anwaehlbar sind - sonst vergleicht der
    # Lauf Symbolmengen statt Phasen (vor dem Lauf geprueft: BAER haette 33,
    # BULLE 22 Symbole).
    je_phase_symbole = []
    for von, bis in PHASEN.values():
        je_phase_symbole.append({
            sym for sym, r in krypto.items()
            for i, k in enumerate(r)
            if i >= 220 and i + 20 < len(r) and von <= k.date <= bis})
    gemeinsam = set.intersection(*je_phase_symbole)
    krypto = {s: r for s, r in krypto.items() if s in gemeinsam}
    print(f"{len(gemeinsam)} Symbole in allen vier Phasen anwaehlbar\n")

    rng = random.Random(SEED)
    gezogen: dict = {}
    for name, (von, bis) in PHASEN.items():
        kandidaten = []
        for sym, r in krypto.items():
            for i, k in enumerate(r):
                if i < 220 or i + 20 >= len(r):
                    continue
                if von <= k.date <= bis:
                    kandidaten.append((sym, i, k.date))
        rng.shuffle(kandidaten)
        gewaehlt, belegt = [], defaultdict(list)
        for sym, i, datum in kandidaten:
            if len(gewaehlt) >= args.je_phase:
                break
            if any(abs(i - j) < MIN_ABSTAND for j in belegt[sym]):
                continue
            gewaehlt.append({"phase": name, "symbol": sym, "index": i,
                             "datum": datum})
            belegt[sym].append(i)
        gezogen[name] = gewaehlt
        print(f"{name:11} {von} .. {bis}   {len(kandidaten):5} Kandidaten "
              f"ueber {len({k[0] for k in kandidaten}):2} Symbole "
              f"-> {len(gewaehlt)} gezogen")

    alle = [a for v in gezogen.values() for a in v]
    tage = sorted({a["datum"] for a in alle})
    print(f"\nKONTINGENT: {len(tage)} Lagebilder + {len(alle)} Entscheidungen "
          f"= {len(tage)+len(alle)} Aufrufe")
    print(f"  Gemini 10/min, 500/Tag -> rund {(len(tage)+len(alle))/10:.0f} Minuten")
    print("\nERWARTUNG, vorab: eine brauchbare Kette kauft im BULLE haeufiger")
    print("als im BAER. Tut sie das nicht, ist sie richtungsblind.\n")
    if args.trocken:
        print("TROCKEN - keine Aufrufe.")
        return 0

    client, modell = PR._client(args.anbieter)
    lagebilder: dict = {}
    ergebnisse = []
    for a in alle:
        sym, i, tag = a["symbol"], a["index"], a["datum"]
        r = reihen[sym]
        try:
            if tag not in lagebilder:
                lagebilder[tag] = RE.stempel_gleichlauf(
                    RA.validiere(PR.frage(
                        client, modell, RA.SYSTEM_PROMPT_ANALYST,
                        RE.baue_lagebild_eingabe(reihen, tag),
                        "agent.rolle_analyst")), reihen, tag)
            lage = lagebilder[tag]
            menge, einstand = PR._bestand(sym)
            hh = np.array([k.high for k in r[:i + 1]], dtype=float)
            ll = np.array([k.low for k in r[:i + 1]], dtype=float)
            cc = np.array([k.close for k in r[:i + 1]], dtype=float)
            atr = float(latest_value(atr_wilder(hh, ll, cc)) or 0.0)
            # DIE ZONEN BRAUCHEN DEN ATR IN EUR (Paket 7): die Kurse, die
            # das Modell nennt, sind EUR - der ATR aus der Reihe ist USD.
            # `beschreibe_lage` bekommt weiterhin den USD-Wert, weil sie
            # durchgehend in der Quellwaehrung rechnet.
            atr_e = atr * RE.fx_eur_je_usd(sym, r, i)
            ein = {"asset": sym,
                   "stand": beschreibe_lage(symbol=sym, reihe=r, index=i,
                                            kurs_eur=PR._kurs_eur(sym, r, i) or 0.0,
                                            atr=atr, menge=menge,
                                            einstand_eur=einstand),
                   "marktlage_beurteilung": {"lage": lage["lage"], "gleichlauf": lage.get("gleichlauf")}}
            ent = RT.validiere(dict(PR.frage(client, modell,
                                             RT.SYSTEM_PROMPT_TRADER, ein,
                                             "agent.rolle_trader")), sym, atr=atr_e)
            a["aktion"] = ent.get("aktion")
            a["faktoren"] = ent.get("unabhaengige_faktoren")
            a["lage_gleichlauf"] = lage.get("gleichlauf")
            # Ausgang: was der Kurs danach tat - NACH der Entscheidung gelesen
            j = min(i + 20, len(r) - 1)
            a["rendite_20t"] = round(100.0 * (r[j].close / r[i].close - 1), 1)
        except Exception as e:                                   # noqa: BLE001
            a["fehler"] = f"{type(e).__name__}: {str(e)[:90]}"
        print(f"  {a['phase']:11} {sym:8} {tag}  "
              f"{str(a.get('aktion') or a.get('fehler','?')):12} "
              f"danach {a.get('rendite_20t','?')} %")
        ergebnisse.append(a)
        with open(args.ausgabe, "w", encoding="utf-8") as fh:
            json.dump(ergebnisse, fh, ensure_ascii=False, indent=1)

    ok = [z for z in ergebnisse if "fehler" not in z]
    KAUF = ("KAUFEN", "NACHKAUFEN")
    VERKAUF = ("REDUZIEREN", "VERKAUFEN", "TAUSCHEN")
    print("\n" + "=" * 72)
    print(f"{'Phase':12} {'n':>3} {'Kaeufe':>8} {'Verkaeufe':>10} "
          f"{'nichts':>8} {'Kurs danach':>12}")
    print("-" * 72)
    for name in PHASEN:
        g = [z for z in ok if z["phase"] == name]
        if not g:
            continue
        k = sum(1 for z in g if z["aktion"] in KAUF)
        v = sum(1 for z in g if z["aktion"] in VERKAUF)
        n = len(g) - k - v
        med = float(np.median([z["rendite_20t"] for z in g]))
        print(f"{name:12} {len(g):3} {k:8} {v:10} {n:8} {med:11.1f} %")
    print("\nLESART: Kauft die Kette im BULLE haeufiger als im BAER, unterscheidet")
    print("sie die Phasen. Sind die Zeilen gleich, ist sie richtungsblind - und")
    print("dann half der Umbau zwar gegen den Deadloop, aber nicht gegen die")
    print("eigentliche Aufgabe.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
