"""Fakt-Ablation ueber die VOLLE Kurshistorie - die Replikation zu Stufe 4.

WOZU DIESES ZWEITE SKRIPT. `laufe_fakt_nachweis.py` prueft einen Fakt an den
gespeicherten Faktensaetzen aus dem Betrieb. Das ist die realistischste
Eingabe, die es gibt - sie enthaelt Funding-Rate, Open Interest, Fear&Greed,
Trigger-Herkunft. Aber sie ist eng: der Fakt `liquiditaetszonen` existiert erst
seit dem 23.07., der Horizontfilter schneidet ab dem 02.08., und uebrig bleiben
201 Faelle auf 17 Symbolen in ZEHN Tagen, davon ein Tag mit 34,8 %.

Methodik 2.5 laesst daraus kein operationalisierbares Urteil zu: unter 50
distinkten Symbolen gilt ein Befund als hypothesengenerierend, und er verlangt
ausdruecklich die **Replikation auf einem anderen Zeitraum**.

Genau die liefert dieses Skript. Es baut die Faktensaetze SYNTHETISCH aus der
Kurshistorie - dieselbe Mechanik wie `backtest_llm1_historisch.py`, die aus
einem Nutzer-Einwand vom 04.08. entstand:

    "historische bekannte Daten - beide Varianten an die LLM1 - haetten sie in
     unserem Fenster korrekt ein bestimmtes Level nach oben oder unten erreicht"

    Betrieb (laufe_fakt_nachweis):   201 Faelle, 17 Symbole, 10 Tage
    Historie (dieses Skript):     8.281 moegliche Anker, 20 Symbole, 2 Jahre

KEIN VORAUSSCHAUEN, und das ist nicht verhandelbar. `_reihe_bis()` schneidet
die Kursreihe hart am Ankertag ab, BEVOR ein Indikator gerechnet wird. Ohne das
waere der Backtest wertlos, und der Fehler waere im Ergebnis nicht zu sehen -
es saehe nur verdaechtig gut aus.

DER PREIS, ehrlich benannt: die synthetischen Faktensaetze sind duenner als die
echten. Funding-Rate, Open Interest, Fear&Greed und Long-Konten-Anteil fehlen -
sie reichen nicht ueber die volle Historie zurueck. Fuer den VERGLEICH zweier
Arme ist das unkritisch (beide bekommen denselben Satz), fuer eine Aussage
ueber die absolute Guete waere es das nicht.

WAS DIE BEIDEN LAEUFE ZUSAMMEN KOENNEN. Stimmen sie ueberein, liegt eine
Replikation auf unabhaengigem Zeitraum UND unabhaengiger Faktenbasis vor - das
hebt den Befund aus "hypothesengenerierend" heraus. Widersprechen sie sich,
ist der Befund an seine Eingabe gebunden, und das ist selbst ein Ergebnis.

    python backtest_fakt_ablation.py --db <kopie.db> --fakt liquiditaetszonen \
        --anker 60 --trocken
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sqlite3
import sys
import time
from collections import Counter

import bewerte_fakt_wirkung as nw
from agent.krypto.backward_tracking import lade_kursreihen
from backtest_llm1_historisch import (
    HORIZONT,
    VORLAUF_MIN,
    baue_historische_fakten,
    lade_reihen,
)


def _anker_streuen(reihen: dict, anzahl: int, je_symbol: int) -> list[tuple]:
    """Ankerpunkte ueber Symbole UND Zeit verteilt.

    Die Streuung ueber die ZEIT ist der Punkt, an dem der Betriebslauf scheitert
    (dort stammt ein Drittel aus einem einzigen Tag). Hier wird je Symbol
    gleichmaessig ueber die gesamte verfuegbare Historie gezogen, nicht am Rand
    geclustert."""
    anker = []
    for sym, reihe in sorted(reihen.items()):
        if len(reihe) < VORLAUF_MIN + HORIZONT + 5:
            continue
        moeglich = list(range(VORLAUF_MIN, len(reihe) - HORIZONT - 2))
        if not moeglich:
            continue
        schritt = max(1, len(moeglich) // je_symbol)
        for i in moeglich[::schritt][:je_symbol]:
            anker.append((sym, i))
    # Ueber die Zeit sortieren und gleichmaessig ausduennen, damit keine
    # Marktphase ueberrepraesentiert ist.
    anker.sort(key=lambda x: (x[1], x[0]))
    if anzahl and len(anker) > anzahl:
        anker = anker[:: max(1, len(anker) // anzahl)][:anzahl]
    return anker


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--db", required=True, help="KOPIE der Produktions-DB")
    p.add_argument("--fakt", action="append", required=True)
    p.add_argument("--anker", type=int, default=60)
    p.add_argument("--je-symbol", type=int, default=6)
    p.add_argument("--horizont", type=int, default=HORIZONT)
    p.add_argument("--pause", type=float, default=1.0)
    p.add_argument("--trocken", action="store_true")
    p.add_argument("--ausgabe", default="fakt_ablation_historisch.json")
    args = p.parse_args()

    reihen_kerzen = lade_reihen()
    btc = reihen_kerzen.get("BTC")
    anker = _anker_streuen(reihen_kerzen, args.anker, args.je_symbol)
    if not anker:
        print("ABBRUCH: keine Ankerpunkte mit genug Vorlauf.")
        return 2

    conn = sqlite3.connect(f"file:{args.db}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    reihen_db = lade_kursreihen(conn)

    faelle = []
    ohne_fakt = 0
    for sym, i in anker:
        fakten = baue_historische_fakten(sym, reihen_kerzen[sym], i, btc)
        if fakten is None:
            continue
        if args.fakt[0].split(".")[0] not in fakten:
            ohne_fakt += 1
            continue
        if sym not in reihen_db:
            continue
        fakten["_fall_id"] = f"{sym}@{reihen_kerzen[sym][i].date}"
        faelle.append({"id": fakten["_fall_id"], "symbol": sym,
                       "created_at": reihen_kerzen[sym][i].date,
                       "fakten": fakten})

    tage = Counter(f["created_at"][:7] for f in faelle)
    symbole = Counter(f["symbol"] for f in faelle)
    print("FALLAUSWAHL (synthetisch aus der Kurshistorie)")
    print(f"  moegliche Anker      {len(anker):5}")
    print(f"  ohne den Fakt        {ohne_fakt:5}")
    print(f"  brauchbar            {len(faelle):5}")
    if faelle:
        print(f"  Symbole              {len(symbole):5}   groesstes "
              f"{max(symbole.values())/len(faelle):.1%}")
        print(f"  Monate abgedeckt     {len(tage):5}   {min(tage)} .. {max(tage)}")
        print(f"  groesster Monat            {max(tage.values())/len(faelle):.1%}")
    print()
    if len(faelle) < 20:
        print("ABBRUCH (Leerlauf-Wache): unter 20 Faellen lohnt kein Aufruf.")
        return 2

    aufrufe = len(faelle) * (2 + len(args.fakt))
    print(f"Geplante Aufrufe: {aufrufe}"
          + ("" if args.trocken else f"  (~{aufrufe*6/60:.0f} min)"))
    print()

    if args.trocken:
        zaehler = [0]

        def provider(fakten):
            i = zaehler[0]
            zaehler[0] += 1
            if i % 5 == 0:
                return {"action": "HALTEN"}
            preis = (fakten.get("preis") or {}).get("usd") or 100.0
            streu = ((i * 2654435761) % 100) / 100.0 * 0.02 - 0.01
            return {"action": "ERÖFFNEN",
                    "entry": {"usd_von": preis, "usd_bis": preis},
                    "stop_loss": {"usd_von": preis * (0.96 + streu),
                                  "usd_bis": preis * (0.96 + streu)},
                    "take_profit": {"usd_von": preis * 1.10,
                                    "usd_bis": preis * 1.10}}
    else:
        from laufe_fakt_nachweis import _echter_provider
        protokoll: list = []

    ergebnisse = {}
    beginn = time.time()
    for fakt in args.fakt:
        pv = provider if args.trocken else _echter_provider(protokoll, fakt, {}, args.pause)
        n = nw.nachweisrahmen(pv, faelle, fakt, reihen_db, horizont=args.horizont)
        print(nw.bericht(n))
        print()
        ergebnisse[fakt] = {"urteil": n.urteil, "wirkung_r": n.wirkung_r,
                            "ci": [n.ci_unten, n.ci_oben],
                            "wild_cluster_p": n.wild_cluster_p,
                            "symbole": n.symbole,
                            "gepaarte_faelle": n.gepaarte_faelle}

    pathlib.Path(args.ausgabe).write_text(json.dumps({
        "quelle": "synthetisch aus Kurshistorie (backtest_llm1_historisch)",
        "anker": len(faelle), "symbole": len(symbole),
        "monate": sorted(tage), "horizont": args.horizont,
        "dauer_sekunden": round(time.time() - beginn, 1),
        "ergebnisse": ergebnisse,
        "rohantworten": [] if args.trocken else protokoll,
    }, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"Protokoll: {args.ausgabe}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
