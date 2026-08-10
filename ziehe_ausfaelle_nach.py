"""Zellen nachziehen, die an einem TECHNISCHEN Fehler gescheitert sind.

DER ANLASS (Nutzer, 10.08.): *"die Ausfaelle musst du manuell nachziehen dann
haben wir ein ergebnis"* - und die Praezisierung: *"nur nachziehen was legitim
ist - mit denselben modell"*.

WAS LEGITIM IST. Eine Zelle, deren Aufruf an einem ReadTimeout oder einer
unlesbaren Antwort gescheitert ist, war ausgewaehlt und ihr Prompt stand fest.
Sie erneut zu fragen stellt den GEPLANTEN Zustand her - das ist keine Auswahl,
sondern eine Reparatur.

WAS NICHT LEGITIM WAERE, und wogegen dieses Skript gebaut ist:

  * eine Zelle nachziehen, deren ANTWORT nicht gefaellt. Deshalb wird
    ausschliesslich nachgezogen, was FEHLT - bestehende Zeilen werden nie
    angefasst, nie ersetzt, nie zweimal gefragt.
  * nur die Ausfaelle EINES Arms nachziehen. Deshalb laeuft die Suche ueber
    alle Arme und alle Anker; wer fehlt, wird nachgezogen, egal wo.
  * das Modell wechseln. Ein anderes Modell mitten in der Messung waere ein
    zweiter Eingriff - das Ergebnis waere dann nicht mehr dem Faktenumbau
    zuzuschreiben. `--modell` ist deshalb PFLICHT und muss dasselbe sein.

UND ES WIRD BEZIFFERT. Am Ende steht, wie viele Zellen je Arm hinzugekommen
sind - und die Auswertung laeuft ZWEIMAL: einmal ohne und einmal mit den
Nachzueglern. Verschiebt sich das Urteil erst durch sie, ist es kein Urteil.

    python ziehe_ausfaelle_nach.py --datei A_31.json --modell gemini-3.1-flash-lite
    python ziehe_ausfaelle_nach.py --datei A_31.json --modell ... --trocken
"""
from __future__ import annotations

import argparse
import json
import os
import pathlib
import sys
import time
from collections import Counter

import messe_regimephasen_llm as M
from backtest_llm1_historisch import baue_historische_fakten, lade_reihen
from messe_umbau_wirkung import (ALT_HINWEIS, ALT_LESEHILFE, ARME, NEU_GUETE,
                                 NEU_QUOTE, als_alt, baue_arm,
                                 hole_echte_fakten, verschraenke_phasen)

VORGABE_DB = ("C:/Users/Geatsch/AppData/Local/Temp/claude/"
              "D--CLAUDE-Projects-SoftwareProjekte-TradingInfoTool/"
              "9e774fdd-5a46-48f6-9d20-e6614cad35af/scratchpad/prod_kopie.db")


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--datei", required=True, help="Ergebnisdatei des Laufs")
    p.add_argument("--modell", required=True,
                   help="DASSELBE Modell wie im Lauf - Pflicht, kein Vorgabewert")
    p.add_argument("--anker", type=int, default=50)
    p.add_argument("--je-symbol", type=int, default=5)
    p.add_argument("--pause", type=float, default=0.2)
    p.add_argument("--db", default=VORGABE_DB)
    p.add_argument("--trocken", action="store_true",
                   help="nur zeigen, was fehlt - keine Aufrufe")
    args = p.parse_args()

    pfad = pathlib.Path(args.datei)
    daten = json.loads(pfad.read_text(encoding="utf-8"))
    zeilen = daten["zeilen"]

    # Die Ankerliste ist deterministisch - dieselben Parameter, dieselbe Liste.
    # Geprueft am 10.08.: zwei Aufrufe ergeben bitgleiche Listen.
    reihen = lade_reihen()
    btc = reihen["BTC"]
    fest = M.stabile_tage(M.btc_phasen(btc))
    je_phase = M.waehle_anker(reihen, fest, args.anker, args.je_symbol)
    anker = verschraenke_phasen(je_phase, M.ARME, M.LABEL, reihen, args.anker)

    # Was ist da, was fehlt? Schluessel wie in der Auswertung: (symbol, datum).
    vorhanden = {arm: {(z["symbol"], z["datum"]) for z in zeilen.get(arm, [])}
                 for arm in ARME}
    fehlend: list[tuple] = []
    for phase, label, sym, i in anker:
        datum = reihen[sym][i].date
        for arm in ARME:
            if (sym, datum) not in vorhanden[arm]:
                fehlend.append((phase, label, sym, i, arm))

    print(f"Anker {len(anker)}, Arme {len(ARME)} -> {len(anker) * len(ARME)} "
          f"Zellen geplant")
    for arm in ARME:
        print(f"   {arm:8s} vorhanden {len(vorhanden[arm]):3d}")
    je_arm = Counter(f[4] for f in fehlend)
    print(f"\nFEHLEND: {len(fehlend)} Zellen  {dict(je_arm)}")
    if not fehlend:
        print("Nichts nachzuziehen.")
        return 0

    # GEGENKONTROLLE gegen einseitiges Nachziehen: faellt fast alles in EINEN
    # Arm, ist das ein Hinweis auf ein systematisches Problem, nicht auf
    # Zufallsausfaelle - dann muss man hinsehen statt nachzufuellen.
    if je_arm and max(je_arm.values()) > 0.7 * len(fehlend) and len(fehlend) > 5:
        print(f"\n  [WARNUNG] {max(je_arm, key=je_arm.get)} traegt "
              f"{max(je_arm.values())} von {len(fehlend)} Ausfaellen - das "
              f"sieht nicht nach Zufall aus. Nachziehen wuerde ein "
              f"systematisches Problem zudecken. Erst die Ursache klaeren.")

    if args.trocken:
        print("\nTrockenlauf - keine Aufrufe.")
        return 0

    quote_neu, guete_neu = hole_echte_fakten(args.db)
    quote_alt = als_alt(quote_neu, NEU_QUOTE, "hinweis",
                        ALT_HINWEIS.format(n=quote_neu["anzahl_ausgewertete_signale"]))
    guete_alt = als_alt(guete_neu, NEU_GUETE, "lesehilfe", ALT_LESEHILFE)

    import config as config_module
    from agent import llm_schema
    from agent.krypto.hebel_analyst import SYSTEM_PROMPT, _validate_hebel
    from api.gemini import GeminiClient
    config_module.load_env()
    client = GeminiClient(os.environ["GEMINI_API_KEY"])
    fmt = llm_schema.response_format_fuer(client, "agent.krypto.hebel_analyst")
    print(f"\nModell {args.modell}, Antwortformat {fmt.get('type')}")
    stand = client.budget_status(args.modell)
    print(f"Budget: {stand['verbraucht']}/{stand['budget']}, "
          f"{stand['verfuegbar']} frei - Bedarf ~{int(len(fehlend) * 1.35)}")
    if stand["verfuegbar"] < len(fehlend):
        print("[FEHLER] Budget reicht nicht einmal fuer einen Versuch je "
              "Zelle. ABBRUCH - halbes Nachziehen waere schlimmer als keines, "
              "weil es genau die Auswahl erzeugt, die wir vermeiden wollen.")
        return 1

    neu_gezogen = Counter()
    fehler = Counter()
    for nr, (phase, label, sym, i, arm) in enumerate(fehlend, 1):
        basis = baue_historische_fakten(sym, reihen[sym], i, btc)
        if basis is None:
            fehler["ohne_fakten"] += 1
            continue
        fakten = baue_arm(basis, arm, label, quote_neu, quote_alt,
                          guete_neu, guete_alt)
        letzter = None
        antwort = None
        for _ in range(3):
            time.sleep(args.pause)
            try:
                roh = client.chat(
                    [{"role": "system", "content": SYSTEM_PROMPT},
                     {"role": "user",
                      "content": json.dumps(fakten, ensure_ascii=False)}],
                    temperature=0.2, response_format=fmt, model=args.modell)
                antwort = _validate_hebel(json.loads(roh), sym)
                break
            except Exception as exc:  # noqa: BLE001
                letzter = exc
        if antwort is None:
            fehler[type(letzter).__name__ if letzter else "unbekannt"] += 1
            continue
        z = M._zeile(sym, reihen[sym], i, antwort, arm, label)
        z["phase"] = phase
        z["nachgezogen"] = True          # bleibt im Datensatz sichtbar
        zeilen.setdefault(arm, []).append(z)
        neu_gezogen[arm] += 1
        if nr % 10 == 0 or nr == len(fehlend):
            print(f"  {nr:3}/{len(fehlend)}  nachgezogen {dict(neu_gezogen)}  "
                  f"Fehler {sum(fehler.values())}")

    daten["nachgezogen"] = {"anzahl": dict(neu_gezogen),
                            "fehlgeschlagen": dict(fehler),
                            "modell": args.modell}
    ziel = pfad.with_name(pfad.stem + "_nachgezogen.json")
    ziel.write_text(json.dumps(daten, ensure_ascii=False, indent=1),
                    encoding="utf-8")
    print(f"\nNachgezogen: {sum(neu_gezogen.values())} Zellen {dict(neu_gezogen)}")
    if fehler:
        print(f"Weiterhin fehlgeschlagen: {dict(fehler)}")
    print(f"Geschrieben: {ziel}")
    print("\nDie ALTE Datei bleibt unveraendert. Werte beide aus und vergleiche "
          "das Urteil - verschiebt es sich erst durch die Nachzuegler, ist es "
          "kein Urteil.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
