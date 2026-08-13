# -*- coding: utf-8 -*-
"""Traegt der TICKERNAME das Urteil? (13.08.2026, Kapitel 15)

DIE FRAGE. Der unabhaengige Richtungsabruf an Z.ai bekommt neben den
Marktsaetzen auch den Namen des Wertes. Die einzige Rechtfertigung dafuer steht
als Nebensatz in `_kehre_objektive_fakten_um()`:

    `symbol` bleibt bewusst an erster Stelle (reiner Bezeichner, keine
    Marktevidenz)

Das ist eine ANNAHME, keine Messung - und sie steht ausgerechnet neben drei
Bias-Testreihen, die am 26.07. gegen die echte API gefahren wurden
(Sykophantie, fehlender Kontext, JSON-Format). Ein Namenstest war nicht dabei.

WARUM ES ZAEHLT. Ein Modell hat zu "BTC" eigene Vorannahmen aus seinem
Training, und die stammen aus einem ANDEREN Regime als heute - die gemessene
Marktphase dieses Projekts war durchgehend "baer". Traegt der Name, dann misst
der Richtungsabgleich teilweise das Training des Modells statt unserer Daten,
und wir saehen im Ergebnis nur "Z.ai widerspricht oft", ohne den Grund.

DAS VERFAHREN - gepaart, wie es die Methodik hier verlangt: dieselben Anker,
derselbe Anbieter, dieselbe Temperatur, EIN Unterschied.

    A   echter Name          {"asset": "BTC",    "stand": [...]}
    A'  echter Name, nochmal  IDENTISCHE Eingabe
    B   neutraler Name       {"asset": "Wert A", "stand": [...]}

    A gegen A'   das RAUSCHEN. Wie oft kippt das Urteil ohne jede Aenderung?
    A gegen B    der NAMENSEFFEKT - aber nur, soweit er das Rauschen schlaegt.

DIESE KONTROLLE IST DER GANZE PUNKT. Ohne sie misst man Unschluessigkeit und
nennt sie Bias. Das Projekt hat den Rauschpegel schon einmal gesehen: bei
grenzwertigen Fakten 5/6 gegen 4/6 SHORT - "die Streuung liegt NICHT an der
Temperatur, sondern an echter Modell-Unschluessigkeit" (gegenpruefung.py).

KOSTEN. 3 Aufrufe je Symbol. Z.ai hat kein Tagesbudget im Code, nur 120/Minute
- das Gemini-Kontingent der Produktion wird NICHT beruehrt. Der Zaehler in
`api_call_kontingent_taeglich` wird trotzdem hochgezaehlt, und das ist richtig:
das Budget haengt am Schluessel, nicht am Geraet.

    python messe_namensanker.py [anzahl_symbole] [--ja]
"""
from __future__ import annotations

import json
import os
import sys
import time
from collections import Counter

NEUTRAL = "Wert A"
WIEDERHOLUNGEN = ("A", "A_wdh", "B")


def _reihen():
    from backtest_llm1_historisch import lade_reihen_aus_db as lade
    return lade("data/tradinginfotool.db")


def _faelle(anzahl: int) -> list:
    """Je Symbol den Faktentext, wie ihn der Richtungsabruf wirklich bekommt."""
    from agent import rollen_eingabe as RE, zweite_meinung as ZM

    reihen = _reihen()
    aus = []
    for sym in sorted(reihen):
        r = reihen[sym]
        if len(r) < 120 or sym.startswith("_"):
            continue
        try:
            _, bc = RE.baue_fall(symbol=sym, reihe=r, index=len(r) - 1,
                                 reihen=reihen, db="data/tradinginfotool.db",
                                 mit_finanzierung=False)
        except Exception as exc:                             # noqa: BLE001
            print(f"  {sym}: uebersprungen ({type(exc).__name__})")
            continue
        markt = ZM.nur_markt(bc)
        if len(markt.get("stand") or []) < 3:
            continue
        aus.append((sym, markt))
        if len(aus) >= anzahl:
            break
    return aus


def _frage(client, fakten: dict) -> str | None:
    from agent import zweite_meinung as ZM
    from agent.krypto import gegenpruefung as G
    # EIN Aufruf, nicht die positionsrobuste Fassung: die faellt bei
    # Uneinigkeit auf NEUTRAL zurueck und wuerde genau das verwischen, was hier
    # gemessen werden soll.
    r = G.leite_eigene_richtung(client, fakten, temperature=0.0,
                                system_prompt=ZM.SYSTEM_RICHTUNG)
    return (r or {}).get("eigene_richtung")


def main() -> int:
    anzahl = int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1].isdigit() else 20
    scharf = "--ja" in sys.argv

    from dotenv import load_dotenv
    load_dotenv()
    schluessel = os.environ.get("ZAI_API_KEY")
    if not schluessel:
        print("ZAI_API_KEY fehlt - ohne Schluessel keine Messung.")
        return 2

    faelle = _faelle(anzahl)
    aufrufe = len(faelle) * len(WIEDERHOLUNGEN)
    # VORFLUGKONTROLLE VOR DEM ERSTEN AUFRUF (stehende Vorgabe): wie viele
    # Aufrufe, wie lange, gegen welches Kontingent.
    print(f"Faelle           : {len(faelle)} Symbole")
    print(f"Aufrufe          : {aufrufe} ({len(WIEDERHOLUNGEN)} je Symbol)")
    print(f"Dauer geschaetzt : {aufrufe * 18 / 60:.0f} Minuten (18 s je Aufruf)")
    print(f"Kontingent       : Z.ai, 120/Minute, kein Tagesbudget im Code")
    print(f"Gemini           : UNBERUEHRT")
    if not scharf:
        print("\nTrockenlauf - mit --ja wird wirklich gefragt.")
        print(f"Beispiel: {faelle[0][0]} -> {faelle[0][1]['stand'][0][:70]}")
        return 0

    from api.zai import ZaiClient
    client = ZaiClient(schluessel)
    begonnen = time.monotonic()
    ergebnisse = []
    for n, (sym, markt) in enumerate(faelle, 1):
        zeile = {"symbol": sym}
        for arm in WIEDERHOLUNGEN:
            fakten = dict(markt)
            if arm == "B":
                fakten["asset"] = NEUTRAL
            zeile[arm] = _frage(client, fakten)
        ergebnisse.append(zeile)
        print(f"  [{n:>2}/{len(faelle)}] {sym:<10} "
              f"A={zeile['A']} A'={zeile['A_wdh']} B={zeile['B']}")

    print(f"\nDauer: {(time.monotonic() - begonnen) / 60:.1f} Minuten")
    _auswerten(ergebnisse)
    ziel = "messung_namensanker.json"
    with open(ziel, "w", encoding="utf-8") as f:
        json.dump(ergebnisse, f, ensure_ascii=False, indent=1)
    print(f"Roh gespeichert: {ziel}")
    return 0


def _auswerten(ergebnisse: list) -> None:
    voll = [z for z in ergebnisse if all(z.get(a) for a in WIEDERHOLUNGEN)]
    print("=" * 70)
    print(f"Auswertbar: {len(voll)} von {len(ergebnisse)}")
    if not voll:
        return
    rauschen = sum(1 for z in voll if z["A"] != z["A_wdh"])
    effekt = sum(1 for z in voll if z["A"] != z["B"])
    n = len(voll)
    print(f"\n  A gegen A' (RAUSCHEN, nichts geaendert) : "
          f"{rauschen}/{n} = {100 * rauschen / n:.0f} %")
    print(f"  A gegen B  (NAME geaendert)             : "
          f"{effekt}/{n} = {100 * effekt / n:.0f} %")
    print(f"\n  Verteilung mit Namen : {dict(Counter(z['A'] for z in voll))}")
    print(f"  Verteilung ohne Namen: {dict(Counter(z['B'] for z in voll))}")
    print()
    # DIE EINZIGE AUSSAGE, DIE DIESE MESSUNG TRAEGT. Alles darunter ist
    # Unschluessigkeit, die auch ohne Namensaenderung auftritt.
    if effekt <= rauschen:
        print("  BEFUND: kein Namenseffekt ueber dem Rauschen. Der Name kann "
              "bleiben - jetzt mit Beleg statt mit Annahme.")
    else:
        print(f"  BEFUND: der Name kippt {effekt - rauschen} Urteile MEHR als "
              f"das blosse Wiederholen. Er traegt - und gehoert raus.")
    print("\n  ACHTUNG n: bei {} Faellen ist ein Unterschied von 1-2 Urteilen "
          "nichts.".format(n))


if __name__ == "__main__":
    raise SystemExit(main())
