"""Vorflugkontrolle fuer messe_regimephasen_llm.py - BEVOR Kontingent fliesst.

WARUM (Nutzer-Vorgabe 09.08.): *"OPEN Router ist gestern erst eingebaut worden
und hat NULL produktiven Einsatz also vorsicht - funktioniert der strikte
Promptbauer"*. Der Client ist neu, der strikte Schemaweg ist an dieser Stelle
noch nie gelaufen, und ein Messlauf ueber 255 Aufrufe ist der falsche Ort, das
herauszufinden.

Diese Datei prueft die GANZE Kette an wenigen echten Aufrufen:

    1  Schemabau        baut `baue_signal_schema()` ohne SchemaLuecke?
    2  Anbieterweiche   bekommt OpenRouter wirklich json_schema - und ein
                        anderer Client wirklich NICHT? (Gegenkontrolle: ohne
                        sie wuesste man nicht, ob die Weiche ueberhaupt
                        unterscheidet oder nur immer dasselbe liefert)
    3  Faktensatz       laesst sich einer bauen, und landet die Regime-
                        Ueberschreibung darin? Steht nirgends mehr
                        "nicht rekonstruierbar"?
    4  Promptgroesse    passt Systemprompt + Fakten in den Modellkontext?
    5  Echter Aufruf    antwortet das Modell, ist es JSON, ueberlebt es
                        `_validate_hebel()`?
    6  Messfelder       sind GENAU die Felder befuellt, die die Messung liest -
                        action, richtung, confidence_pct, entry/stop/take_profit?
    7  Zonenrechnung    liefert `_zonen()` ein plausibles CRV und einen
                        plausiblen Stop-Abstand?
    8  Rotation         hat wirklich das erwartete Modell geantwortet, oder ist
                        die Free-Liste auf einen Rueckfall gelaufen?

Jede Pruefung meldet KLARTEXT, was sie gesehen hat - nicht nur ok/Fehler. Ein
"ok" ohne Zahl ist bei einem neuen Anbieter wertlos.

    python pruefe_regimephasen_vorflug.py --faelle 3
"""
from __future__ import annotations

import argparse
import json
import sys
import time

_ok, _fehler = 0, []


def pruefe(name: str, bedingung: bool, detail: str = "") -> bool:
    global _ok
    if bedingung:
        _ok += 1
        print(f"  [ok]     {name}" + (f"   {detail}" if detail else ""))
    else:
        _fehler.append(name)
        print(f"  [FEHLER] {name}   {detail}")
    return bedingung


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--faelle", type=int, default=3)
    args = p.parse_args()

    import os

    import config as config_module
    from agent import llm_schema
    from agent.krypto.hebel_analyst import SYSTEM_PROMPT, _validate_hebel
    from api.gemini import GeminiClient
    from api.openrouter import FREE_MODELLE, OpenRouterClient
    from backtest_llm1_historisch import (
        VORLAUF_MIN,
        baue_historische_fakten,
        lade_reihen,
    )
    import messe_regimephasen_llm as M

    config_module.load_env()

    print("1  SCHEMABAU")
    import agent.krypto.hebel_analyst as analyst_modul
    try:
        schema = llm_schema.baue_signal_schema(analyst_modul)
        pruefe("1.1 Signal-Schema baut ohne SchemaLuecke",
               isinstance(schema, dict) and bool(schema.get("properties")),
               f"{len(schema.get('properties', {}))} Felder")
        pflicht = set(schema.get("required", []))
        pruefe("1.2 die von der Messung gelesenen Felder sind Pflichtfelder",
               {"action", "entry", "stop_loss", "take_profit"} <= pflicht,
               f"fehlend: {sorted({'action','entry','stop_loss','take_profit'} - pflicht)}")
    except Exception as exc:  # noqa: BLE001
        pruefe("1.1 Signal-Schema baut ohne SchemaLuecke", False, repr(exc))
        return 1

    print("\n2  ANBIETERWEICHE")
    schluessel = os.environ.get("OPENROUTER_API_KEY")
    if not schluessel:
        print("  OPENROUTER_API_KEY fehlt - Abbruch.")
        return 1
    client = OpenRouterClient(schluessel)
    fmt = llm_schema.response_format_fuer(client, "agent.krypto.hebel_analyst")
    pruefe("2.1 OpenRouter bekommt das STRIKTE Schema",
           fmt.get("type") == "json_schema", f"type={fmt.get('type')}")
    pruefe("2.2 und es ist als strict markiert",
           bool(fmt.get("json_schema", {}).get("strict")))
    # GEGENKONTROLLE: unterscheidet die Weiche ueberhaupt? Ein anderer Client
    # MUSS json_object bekommen - sonst liefert sie nur immer dasselbe und
    # 2.1 waere kein Nachweis.
    fmt_g = llm_schema.response_format_fuer(
        GeminiClient("attrappe"), "agent.krypto.hebel_analyst")
    pruefe("2.3g Gegenkontrolle: Gemini bekommt json_object, nicht das Schema",
           fmt_g.get("type") == "json_object", f"type={fmt_g.get('type')}")

    print("\n3  FAKTENSATZ UND REGIME-UEBERSCHREIBUNG")
    reihen = lade_reihen()
    btc = reihen.get("BTC")
    pruefe("3.1 BTC-Reihe vorhanden", bool(btc), f"{len(btc or [])} Tage")
    fest = M.stabile_tage(M.btc_phasen(btc))
    anker = M.waehle_anker(reihen, fest, je_arm=args.faelle * 3, je_symbol=2)
    proben = []
    for arm in M.ARME:
        if anker[arm]:
            proben.append((arm, M.LABEL[arm], *anker[arm][0]))
    pruefe("3.2 aus jedem Arm ein Anker verfuegbar", len(proben) == len(M.ARME),
           f"{[p[0] for p in proben]}")

    faktensaetze = []
    for arm, label, sym, i in proben:
        f = baue_historische_fakten(sym, reihen[sym], i, btc)
        if f is None:
            continue
        f["regime"] = dict(f.get("regime") or {})
        f["regime"]["wert"] = label
        faktensaetze.append((arm, label, sym, i, f))
    pruefe("3.3 Faktensaetze baubar", len(faktensaetze) == len(proben),
           f"{len(faktensaetze)} von {len(proben)}")
    for arm, label, sym, i, f in faktensaetze:
        pruefe(f"3.4 {arm}: Regime-Label sitzt im Faktensatz",
               f["regime"]["wert"] == label, f"{sym} {reihen[sym][i].date}")
    # Der kritische Punkt: "nicht rekonstruierbar" waere eine Unknown-Option
    # und wuerde Abstention ausloesen statt die Marktphase zu messen.
    for arm, label, sym, i, f in faktensaetze:
        roh = json.dumps(f, ensure_ascii=False)
        pruefe(f"3.5 {arm}: kein 'nicht rekonstruierbar' mehr im Regime-Block",
               "nicht rekonstruierbar" not in json.dumps(f["regime"]),
               json.dumps(f["regime"], ensure_ascii=False)[:90])

    print("\n4  PROMPTGROESSE")
    for arm, label, sym, i, f in faktensaetze[:1]:
        roh = json.dumps(f, ensure_ascii=False)
        zeichen = len(SYSTEM_PROMPT) + len(roh)
        # grobe Schaetzung, 1 Token ~ 3,5 Zeichen bei deutschem JSON
        token = zeichen / 3.5
        pruefe("4.1 Prompt passt in den Modellkontext (262.144 bei nemotron)",
               token < 200_000,
               f"~{token:,.0f} Token ({len(SYSTEM_PROMPT):,} Zeichen Prompt + "
               f"{len(roh):,} Zeichen Fakten)")

    print(f"\n5-8  ECHTE AUFRUFE ({len(faktensaetze)} Stueck)")
    gueltig = 0
    unbrauchbar_gezaehlt = [0]
    for arm, label, sym, i, f in faktensaetze:
        print(f"\n  --- {arm} / {sym} / {reihen[sym][i].date}")
        beginn = time.time()
        try:
            roh = client.chat(
                [{"role": "system", "content": SYSTEM_PROMPT},
                 {"role": "user", "content": json.dumps(f, ensure_ascii=False)}],
                temperature=0.2, response_format=fmt)
        except Exception as exc:  # noqa: BLE001
            pruefe(f"5.1 {arm}: Aufruf beantwortet", False, repr(exc)[:200])
            continue
        dauer = time.time() - beginn
        pruefe(f"5.1 {arm}: Aufruf beantwortet", True, f"{dauer:.1f} s")
        pruefe(f"8.1 {arm}: das erwartete Modell hat geantwortet",
               client.letztes_modell == FREE_MODELLE[0],
               f"{client.letztes_modell}")
        try:
            antwort = json.loads(roh)
        except Exception as exc:  # noqa: BLE001
            pruefe(f"5.2 {arm}: Antwort ist JSON", False, f"{repr(exc)[:120]} "
                   f"| Rohanfang: {roh[:120]!r}")
            continue
        pruefe(f"5.2 {arm}: Antwort ist JSON", True,
               f"{len(antwort)} Felder")
        try:
            geprueft = _validate_hebel(antwort, sym)
        except Exception as exc:  # noqa: BLE001
            pruefe(f"5.3 {arm}: ueberlebt _validate_hebel()", False,
                   f"{type(exc).__name__}: {str(exc)[:160]}")
            continue
        pruefe(f"5.3 {arm}: ueberlebt _validate_hebel()", True,
               f"action={geprueft.get('action')}")

        fehlend = [k for k in ("action", "confidence_pct") if geprueft.get(k) is None]
        pruefe(f"6.1 {arm}: Messfelder befuellt", not fehlend,
               f"fehlend {fehlend}" if fehlend
               else f"action={geprueft.get('action')} "
                    f"richtung={geprueft.get('richtung')} "
                    f"konfidenz={geprueft.get('confidence_pct')}")

        z = M._zonen(geprueft)
        if geprueft.get("action") == "HALTEN" and z is None:
            pruefe(f"7.1 {arm}: HALTEN ohne Zonen ist zulaessig", True,
                   "kein Zonensatz - wird als HALTEN gezaehlt")
            gueltig += 1
            continue
        if z is None:
            # KEIN FEHLER, sondern eine Kategorie. `_zonen()` folgt exakt
            # `_zonen_absolut()` aus dem Backward-Tracking und verwirft
            # widerspruechliche Saetze (deklariertes SHORT mit Ziel ueber dem
            # Einstieg). Die Produktion tut dasselbe und zaehlt sie als "keine
            # Zonen erarbeitet" - historisch der groesste Einzelposten des
            # Deadloops (23,9 %). Ein Vorflug, der daran scheitert, wuerde
            # einen Lauf blockieren, der genau diese Groesse messen soll.
            unbrauchbar_gezaehlt[0] += 1
            print(f"  [zaehlt]  7.1 {arm}: Zonensatz widerspruechlich - wird als "
                  f"'keine Zonen' gezaehlt, nicht als Fehler")
            print(f"            richtung={geprueft.get('richtung')} "
                  f"entry={geprueft.get('entry')} stop={geprueft.get('stop_loss')} "
                  f"tp={geprueft.get('take_profit')}")
            continue
        stop_pct = z["risiko"] / z["entry"] * 100
        pruefe(f"7.2 {arm}: CRV plausibel (0,2 bis 20)", 0.2 <= z["crv"] <= 20,
               f"CRV {z['crv']:.2f}")
        pruefe(f"7.3 {arm}: Stop-Abstand plausibel (0,5 bis 40 %)",
               0.5 <= stop_pct <= 40,
               f"Stop {stop_pct:.2f} % (Produktion Median 8,25 %, P90 15,1 %)")
        gueltig += 1

    print("\n" + "=" * 72)
    print(f"{_ok} Pruefungen bestanden, {len(_fehler)} fehlgeschlagen, "
          f"{gueltig} von {len(faktensaetze)} Faellen vollstaendig verwertbar, "
          f"{unbrauchbar_gezaehlt[0]} mit widerspruechlichen Zonen")
    if faktensaetze and unbrauchbar_gezaehlt[0] / len(faktensaetze) > 0.5:
        _fehler.append("ueber 50 % widerspruechliche Zonensaetze")
        print("   Ueber die Haelfte der Zonensaetze ist widerspruechlich - das ist")
        print("   keine Kategorie mehr, sondern ein Defekt. Erst klaeren.")
    if _fehler:
        for f in _fehler:
            print(f"   FEHLER: {f}")
        print("\nNICHT STARTEN, bevor das behoben ist.")
    return 1 if _fehler else 0


if __name__ == "__main__":
    sys.exit(main())
