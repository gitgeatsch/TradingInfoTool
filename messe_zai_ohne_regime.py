"""Leitet Z.ai LONG ab, wenn `regime` NICHT im Faktensatz steht?

DER BEFUND, DER DAZU FUEHRT (10.08.). Z.ais unabhaengige Richtungsableitung
lieferte ueber 1.022 Hebel-Signale genau EINMAL LONG (Juli 1/463, August
0/559), waehrend das Primaermodell auf denselben Faellen zu 34,9 % LONG
waehlte. Ursache-Verdacht: `baue_objektive_fakten()` uebergibt sechs Fakten,
und einer davon - `regime` - war auf ALLEN 1.022 Faellen "baer". Der
Systemprompt verlangt "leite ALLEIN aus diesen Fakten deine eigene
Markteinschaetzung ab". Wer bei jedem Aufruf "Baerenmarkt" mitbekommt, kommt
nicht auf LONG.

DAS IST EIN VERDACHT, KEIN NACHWEIS. Er koennte auch falsch sein: vielleicht
sind die uebrigen fuenf Fakten fuer sich genommen baerisch genug, und `regime`
aendert nichts. Genau das misst diese Datei - gepaart, an denselben Ankern:

    Arm A   der Faktensatz, wie die Produktion ihn baut (MIT regime)
    Arm B   derselbe Satz, nur ohne den Schluessel `regime`

Alles andere bleibt bitgleich. Ein Unterschied kann dann nur an diesem einen
Feld liegen.

WARUM GEPAART UND NICHT GEGEN DIE HISTORIE: die 1.022 gespeicherten Urteile
stammen aus der positions-robusten Fassung (zwei Aufrufe, bei Uneinigkeit
NEUTRAL) und aus wechselnden Zeitpunkten. Ein Vergleich dagegen mischt zwei
Aenderungen. Arm A wird deshalb neu erhoben.

Z.AI-EIGENHEITEN, die den Aufbau bestimmen (Nutzer-Hinweis 10.08.): nur kleine
Prompts und begrenzte Abfragefrequenz. Beides ist hier von Natur aus erfuellt -
der Faktensatz hat sechs Felder, und die Aufrufe laufen sequenziell mit Pause.

    python messe_zai_ohne_regime.py --anker 20
"""
from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
import time
from collections import Counter, defaultdict

VORGABE_DB = ("C:/Users/Geatsch/AppData/Local/Temp/claude/"
              "D--CLAUDE-Projects-SoftwareProjekte-TradingInfoTool/"
              "9e774fdd-5a46-48f6-9d20-e6614cad35af/scratchpad/prod_kopie.db")


def _tief(d: dict, *pfad, vorgabe=None):
    for teil in pfad:
        if not isinstance(d, dict):
            return vorgabe
        d = d.get(teil)
    return d if d is not None else vorgabe


def hole_anker(db: str, anzahl: int) -> list[dict]:
    """Anker REIHUM ueber die Symbole - nicht die juengsten am Stueck.

    Dieselbe Lehre wie beim Stichproben-Alias und bei der Phasenverschraenkung:
    eine Auswahl, die nach einem Merkmal sortiert und dann abschneidet,
    schneidet systematisch etwas weg. Hier waeren es die Symbole."""
    c = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    c.row_factory = sqlite3.Row
    zeilen = c.execute(
        "SELECT symbol, created_at, regime, richtung, zai_eigene_richtung, "
        "facts_json FROM hebel_signals "
        "WHERE facts_json IS NOT NULL AND zai_eigene_richtung IS NOT NULL "
        "ORDER BY created_at DESC"
    ).fetchall()
    c.close()

    je_symbol: dict[str, list] = defaultdict(list)
    for z in zeilen:
        je_symbol[z["symbol"]].append(z)
    anker: list[dict] = []
    runde = 0
    while len(anker) < anzahl:
        vorher = len(anker)
        for sym in sorted(je_symbol):
            if runde < len(je_symbol[sym]) and len(anker) < anzahl:
                anker.append(dict(je_symbol[sym][runde]))
        if len(anker) == vorher:
            break
        runde += 1
    return anker


def baue_arme(zeile: dict) -> tuple[dict | None, dict | None]:
    """Arm A wie die Produktion, Arm B identisch ohne `regime`."""
    from agent.krypto.gegenpruefung import baue_objektive_fakten
    try:
        f = json.loads(zeile["facts_json"])
    except (ValueError, TypeError):
        return None, None
    ta = f.get("technische_analyse") or {}
    konf = ta.get("confluence") or {}
    optionen = f.get("optionsmarkt") or {}
    skew = (_tief(optionen, "skew_details", "skew_prozentpunkte")
            or optionen.get("skew_prozentpunkte"))
    a = baue_objektive_fakten(
        symbol=zeile["symbol"],
        rsi=ta.get("rsi_14"),
        trend_label=_tief(ta, "trend") or _tief(f, "markt_kontext", "trend"),
        regime=zeile["regime"] or _tief(f, "regime", "wert"),
        funding_rate_stunde=_tief(f, "funding_rate", "aktuell_stunde"),
        confluence_bullish=konf.get("bullish") or 0,
        confluence_bearish=konf.get("bearish") or 0,
        confluence_neutral=konf.get("neutral") or 0,
        optionsmarkt_skew=skew,
    )
    b = {k: v for k, v in a.items() if k != "regime"}
    return a, b


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--anker", type=int, default=20)
    p.add_argument("--pause", type=float, default=1.5)
    p.add_argument("--db", default=VORGABE_DB)
    p.add_argument("--trocken", action="store_true")
    p.add_argument("--ausgabe", default="zai_regime.json")
    args = p.parse_args()

    anker = hole_anker(args.db, args.anker)
    print(f"Anker {len(anker)} ueber {len({a['symbol'] for a in anker})} Symbole")

    print("\n=== EINGRIFFSKONTROLLE ===")
    a0, b0 = baue_arme(anker[0])
    if a0 is None:
        print("  [FEHLER] Faktensatz nicht baubar - Abbruch.")
        return 2
    pruefungen = [
        ("Arm A traegt regime", "regime" in a0, str(a0.get("regime"))),
        ("Arm B traegt KEIN regime", "regime" not in b0, ""),
        ("sonst sind beide Arme bitgleich",
         {k: v for k, v in a0.items() if k != "regime"} == b0, ""),
        ("regime ist tatsaechlich die vermutete Konstante",
         a0.get("regime") == "baer", str(a0.get("regime"))),
        ("der Satz traegt ueberhaupt Marktinformation (>= 3 Felder)",
         len(b0) >= 3, f"{len(b0)} Felder: {sorted(b0)}"),
    ]
    alles = True
    for name, ok, detail in pruefungen:
        print(f"  {'[ok]    ' if ok else '[FEHLER]'} {name}"
              + (f"   {detail}" if detail else ""))
        alles &= ok
    if not alles:
        print("\n  ABBRUCH: die Arme unterscheiden sich nicht wie beabsichtigt.")
        return 2
    print(f"\n  Beispiel Arm A: {a0}")
    print(f"  Beispiel Arm B: {b0}")

    # Feldabdeckung - ein Feld, das fast nie belegt ist, kann nichts erklaeren.
    abdeckung: Counter = Counter()
    for z in anker:
        a, _ = baue_arme(z)
        for k in (a or {}):
            abdeckung[k] += 1
    print(f"\n  Feldabdeckung ueber {len(anker)} Anker: "
          + ", ".join(f"{k}={v}" for k, v in abdeckung.most_common()))

    if args.trocken:
        print("\nTrockenlauf - keine Z.ai-Aufrufe.")
        return 0

    import config as config_module
    from agent.krypto.gegenpruefung import leite_eigene_richtung
    from api.zai import ZaiClient
    config_module.load_env()
    if not os.environ.get("ZAI_API_KEY"):
        print("ZAI_API_KEY fehlt.")
        return 1
    client = ZaiClient(api_key=os.environ["ZAI_API_KEY"])

    print(f"\n{len(anker)} Anker x 2 Arme = {len(anker) * 2} Z.ai-Aufrufe, "
          f"Pause {args.pause} s")
    ergebnis = []
    fehler: Counter = Counter()
    beginn = time.time()
    for nr, z in enumerate(anker, 1):
        a, b = baue_arme(z)
        if a is None:
            continue
        zeile = {"symbol": z["symbol"], "created_at": z["created_at"],
                 "primaer_richtung": z["richtung"],
                 "gespeichert_zai": z["zai_eigene_richtung"]}
        for arm, fakten in (("mit_regime", a), ("ohne_regime", b)):
            time.sleep(args.pause)
            try:
                r = leite_eigene_richtung(client, fakten)
                zeile[arm] = (r or {}).get("eigene_richtung")
                zeile[arm + "_begruendung"] = (r or {}).get("kurzbegruendung")
            except Exception as exc:  # noqa: BLE001
                fehler[type(exc).__name__] += 1
                zeile[arm] = None
        ergebnis.append(zeile)
        if nr % 5 == 0 or nr == len(anker):
            je = (time.time() - beginn) / max(1, nr)
            m = Counter(x.get("mit_regime") for x in ergebnis)
            o = Counter(x.get("ohne_regime") for x in ergebnis)
            print(f"  {nr:3}/{len(anker)}  mit {dict(m)}  ohne {dict(o)}  "
                  f"Fehler {sum(fehler.values())}  {je:.1f} s/Anker")

    print("\n" + "=" * 72)
    print("RICHTUNGSVERTEILUNG - dieselben Anker, ein Feld Unterschied")
    gueltig = [x for x in ergebnis if x.get("mit_regime") and x.get("ohne_regime")]
    m = Counter(x["mit_regime"] for x in gueltig)
    o = Counter(x["ohne_regime"] for x in gueltig)
    print(f"{'Richtung':10} {'MIT regime':>14} {'OHNE regime':>14}")
    for r in ("LONG", "SHORT", "NEUTRAL"):
        print(f"{r:10} {m.get(r, 0):14d} {o.get(r, 0):14d}")
    print(f"{'gepaart n':10} {len(gueltig):14d}")

    print("\nWECHSEL je Anker:")
    wechsel = Counter((x["mit_regime"], x["ohne_regime"]) for x in gueltig)
    for (von, nach), n in wechsel.most_common():
        pfeil = "  (unveraendert)" if von == nach else ""
        print(f"   {von:8s} -> {nach:8s}  {n:3d}{pfeil}")

    print("\n=== URTEIL ===")
    if not gueltig:
        print("  Keine gepaarten Faelle - keine Aussage.")
    elif o.get("LONG", 0) > m.get("LONG", 0):
        print(f"  `regime` UNTERDRUECKT LONG: ohne das Feld leitet Z.ai "
              f"{o.get('LONG', 0)} mal LONG ab statt {m.get('LONG', 0)} mal. "
              f"Der Verdacht ist bestaetigt.")
    elif o.get("LONG", 0) == m.get("LONG", 0) == 0:
        print("  KEIN Unterschied bei LONG - beide Arme leiten nie LONG ab. "
              "Der Verdacht ist WIDERLEGT: es liegt nicht an `regime`, "
              "sondern die uebrigen Fakten sind fuer sich baerisch.")
    else:
        print(f"  Uneindeutig: LONG mit {m.get('LONG', 0)}, "
              f"ohne {o.get('LONG', 0)}.")

    import pathlib
    pathlib.Path(args.ausgabe).write_text(
        json.dumps({"zeilen": ergebnis, "fehler": dict(fehler)},
                   ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\nGeschrieben: {args.ausgabe}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
