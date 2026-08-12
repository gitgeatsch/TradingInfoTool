# -*- coding: utf-8 -*-
"""Die Rollenkette an einem echten Fall - Ein- und Ausgabe zum Lesen.

WOZU. Alle Bausteine sind einzeln geprueft: Vertrag, Lagebeschreibung,
Marktbreite, die zwei Prompts, die Schemata, die Validatoren. Was fehlt, ist der
Durchlauf - und der ist die eigentliche Pruefung. Am 10.08. haben wir den ganzen
Tag Zahlen gemessen und kein einziges Mal eine Modellantwort GELESEN.

DREI STUFEN, aufsteigend im Kontingent:

    --trocken              0 Aufrufe.  Was das Modell saehe, ausgedruckt.
                           Plus die Waechter: Werturteile, Konstanten.
    --symbol X             2 Aufrufe.  Rolle A und BC an einem Fall.
    --pruefsteine          8 Aufrufe.  Die vier Faelle mit bekanntem Ausgang.

DIE PRUEFSTEINE stammen aus der eigenen Historie, ihr Ausgang steht in der
Kursreihe und ist nicht verhandelbar:

    BTC  KAUFEN      14.07.  ->  -2,3 % nach 20 Tagen
    KAS  TAUSCHEN    14.07.  ->  -8,9 %
    KAS  NACHKAUFEN  15.07.  ->  -8,6 %   (Position stand -14,6 %)
    GRIFFAIN HALTEN  21.07.  -> +33,8 %   (verpasst)

Der Massstab ist NICHT "hat es recht" - vier Faelle beweisen nichts. Er ist:
kommt bei den drei Verlusten jetzt NICHTS_TUN heraus, und wird beim verpassten
Fall wenigstens ein Beleg genannt, der dafuer sprach?

CAT waere der fuenfte Fall (+44,5 %), ist aber untauglich: seine FX-Ableitung war
nachweislich kaputt, der Anstieg kann ein Datenartefakt sein.

    python pruefe_rollenkette.py --trocken
    python pruefe_rollenkette.py --symbol KAS --datum 2026-07-15 --anbieter gemini35
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys

import numpy as np

import agent.rolle_analyst as RA
import agent.rolle_trader as RT
from agent.empfehlung_vertrag import EmpfehlungUngueltig, cash_hinweis
from agent.lagebeschreibung import beschreibe_lage
from agent.szenario_fakten import enthaelt_werturteile, finde_konstanten
# AUS DER DATENBANK, NICHT AUS DEM EXPORT (Paket 9, 12.08.2026). Der
# JSON-Export traegt 41 Reihen und ausgerechnet ZWEI der drei
# Leitmaerkte nicht (SPY, OD7C). Der Live-Lauf lieferte deshalb ein
# krypto-only Lagebild und `gleichlauf: unbekannt` - und das faellt
# nur auf, wenn man die Ausgabe LIEST. Der Faktenbauer benutzt die
# Datenbank; ein Pruefskript, das eine andere Quelle liest, prueft
# etwas anderes als das, was laeuft.
from backtest_llm1_historisch import lade_reihen_aus_db as lade_reihen
from indicators.calculations import atr_wilder, latest_value

import agent.rollen_eingabe as RE

DB = "data/tradinginfotool.db"

# Symbol, Datum, was das alte System sagte, was danach geschah
PRUEFSTEINE = (
    ("BTC", "2026-07-14", "KAUFEN", "-2,3 % nach 20 Tagen"),
    ("KAS", "2026-07-14", "TAUSCHEN", "-8,9 %"),
    ("KAS", "2026-07-15", "NACHKAUFEN", "-8,6 %, Position stand -14,6 %"),
    ("GRIFFAIN", "2026-07-21", "HALTEN", "+33,8 % - verpasst"),
)


# HELFER LIEGEN JETZT IN agent/rollen_eingabe.py (12.08.2026).
#
# Sie standen hier - in einem SKRIPT -, und sieben Messskripte importierten sie
# von hier und bogen die Modulkonstante `DB` um. Ein Skript als Bibliothek zu
# benutzen funktioniert, bis jemand es ausfuehrt oder umbenennt. Die Logik liegt
# jetzt im Modul; hier stehen nur noch Weiterleitungen, damit bestehende
# Aufrufe und das Umbiegen von `DB` unveraendert weiterlaufen.
def _bestand(symbol: str):
    return RE.bestand(symbol, DB)


def _kurs_eur(symbol: str, reihe, index: int) -> float | None:
    return RE.kurs_eur(symbol, reihe, index, DB)


def _atr(reihe, i: int) -> float:
    return RE.atr_bis(reihe, i)


def baue_eingaben(symbol: str, datum: str | None,
                  reihen: dict) -> tuple[dict, dict, float]:
    """Die Eingaben beider Rollen - jetzt ueber `rollen_eingabe.baue_fall()`.

    Vorher baute diese Funktion sie selbst zusammen. Damit fehlte hier die
    Finanzierungsrate, obwohl sie gebaut war: es gab keine gemeinsame Stelle,
    an der man sie haette anschliessen koennen. Genau deshalb liegt der Aufbau
    jetzt im Modul."""
    import requests
    reihe = reihen.get(symbol)
    if not reihe:
        raise SystemExit(f"[FEHLER] keine Kursreihe fuer {symbol}")
    if datum:
        idx = next((i for i, k in enumerate(reihe) if k.date >= datum), None)
        if idx is None:
            raise SystemExit(f"[FEHLER] {symbol} hat keine Daten ab {datum}")
    else:
        idx = len(reihe) - 1
    sitzung = requests.Session()
    sitzung.headers["User-Agent"] = "TradingInfoTool"
    a_ein, bc_ein = RE.baue_fall(symbol=symbol, reihe=reihe, index=idx,
                                 reihen=reihen, db=DB, session=sitzung)
    # DER ATR IN EUR, fuer die Zonen-Ableitung (Paket 7). Er reist NEBEN der
    # Eingabe mit, nicht darin - `lauf()` kennt weder Reihe noch Index, und ihn
    # dort neu zu berechnen hiesse, dieselbe Groesse an zwei Stellen zu bilden.
    #
    # NICHT IN `bc_ein`: der gesamte Dict geht als Nachricht an das Modell
    # (`frage(..., bc_ein, ...)`). Ein Schluessel darin waere ein Fakt, den
    # niemand gesetzt hat - und ein Unterstrich davor macht ihn nicht
    # unsichtbar. Mein erster Anlauf hatte genau das getan, samt eines
    # Kommentars, der das Gegenteil behauptete.
    return a_ein, bc_ein, RE.atr_eur(symbol, reihe, idx, DB)


def _client(name: str):
    import os
    import config as config_module
    config_module.load_env()
    if name == "gemini":
        # DAS PRODUKTIONSMODELL (Paket 9, 12.08.2026). Bis heute kannte dieses
        # Skript nur "gemini35" - und weil ich das dort gelesen habe, stand in
        # meinem Bericht, die Kette laufe auf 3.5. Die Quelle sagt 3.1
        # (api/gemini.py::DEFAULT_MODEL). Ein Skript ist eine VERWENDUNG,
        # keine Festlegung.
        from api.gemini import DEFAULT_MODEL, GeminiClient
        return GeminiClient(os.environ["GEMINI_API_KEY"]), DEFAULT_MODEL
    if name == "gemini35":
        # NUR FUER MESSUNGEN. Eigener Kontingent-Topf, deshalb nuetzlich fuer
        # Laeufe, die der Produktion nichts wegnehmen sollen - aber KEIN Befund
        # von hier gilt ohne Wiederholung fuer die Produktion.
        from api.gemini import GeminiClient
        return GeminiClient(os.environ["GEMINI_API_KEY"]), "gemini-3.5-flash-lite"
    if name == "openrouter":
        from api.openrouter import OpenRouterClient
        return OpenRouterClient(os.environ["OPENROUTER_API_KEY"]), None
    raise SystemExit(f"[FEHLER] unbekannter Anbieter {name}")


def frage(client, modell, system_prompt: str, eingabe: dict,
          modulname: str) -> dict:
    from agent import llm_schema
    fmt = llm_schema.response_format_fuer(client, modulname)
    roh = client.chat(
        [{"role": "system", "content": system_prompt},
         {"role": "user", "content": json.dumps(eingabe, ensure_ascii=False)}],
        **({"model": modell} if modell else {}), response_format=fmt,
        temperature=0.2)
    text = roh if isinstance(roh, str) else str(roh)
    anfang, ende = text.find("{"), text.rfind("}")
    if anfang < 0 or ende < anfang:
        raise ValueError(f"keine JSON-Struktur in der Antwort: {text[:180]}")
    return json.loads(text[anfang:ende + 1])


def zeige(titel: str, zeilen) -> None:
    print(f"\n--- {titel} ---")
    for z in (zeilen if isinstance(zeilen, list) else [zeilen]):
        print(f"  {z}")


def lauf(symbol: str, datum: str | None, reihen: dict, anbieter: str | None,
         erwartet: str | None = None) -> None:
    a_ein, bc_ein, atr_e = baue_eingaben(symbol, datum, reihen)

    print("\n" + "=" * 78)
    print(f"{symbol}  {datum or 'heute'}" + (f"   [{erwartet}]" if erwartet else ""))
    print("=" * 78)
    zeige("EINGABE ROLLE A (Marktlage, kennt das Asset nicht)", a_ein["marktlage"])
    zeige("EINGABE ROLLE BC (Asset)", bc_ein["stand"])

    # --- Waechter, vor jedem Aufruf ----------------------------------------
    urteile = enthaelt_werturteile({"a": a_ein, "bc": bc_ein})
    if urteile:
        print(f"\n[WARNUNG] Werturteil-Feldnamen: {urteile}")
    ueberschneidung = set(a_ein) & set(bc_ein)
    if ueberschneidung:
        print(f"\n[FEHLER] Block bei BEIDEN Rollen: {ueberschneidung}")

    if not anbieter:
        print("\n  (trocken - keine Aufrufe)")
        return

    client, modell = _client(anbieter)
    try:
        a_roh = frage(client, modell, RA.SYSTEM_PROMPT_ANALYST, a_ein,
                      "agent.rolle_analyst")
        # `datum` kann None sein (= heute); dann das letzte Datum der
        # Reihe nehmen - der Gleichlauf braucht einen Ankertag.
        tag = datum or max(k.date for r in reihen.values() for k in r[-1:])
        a = RE.stempel_gleichlauf(RA.validiere(a_roh), reihen, tag)
    except Exception as e:
        print(f"\n[ROLLE A GESCHEITERT] {type(e).__name__}: {e}")
        return
    zeige("AUSGABE ROLLE A", [f"lage: {a['lage']}",
                              f"gleichlauf (gerechnet): {a['gleichlauf']}"]
          + [f"klasse {k['klasse']:<10}{k['einstufung']:<12}{k['warum']}"
             for k in (a.get("klassen") or [])]
          + [f"beleg: {b}" for b in a["belege"]]
          + ([f"KORREKTUR: {a['_korrekturen']}"] if a.get("_korrekturen") else []))

    bc_ein["marktlage_beurteilung"] = {"lage": a["lage"], "gleichlauf": a.get("gleichlauf")}
    try:
        bc_roh = frage(client, modell, RT.SYSTEM_PROMPT_TRADER, bc_ein,
                       "agent.rolle_trader")
        bc = RT.validiere(bc_roh, symbol, atr=atr_e)
    except (EmpfehlungUngueltig, RT.TraderAntwortUngueltig) as e:
        print(f"\n[ABGELEHNT] {e}")
        return
    except Exception as e:
        print(f"\n[ROLLE BC GESCHEITERT] {type(e).__name__}: {e}")
        return

    menge, einstand = _bestand(symbol)
    zeilen = [f"AKTION: {bc['aktion']}"]
    if bc.get("tranche_eur"):
        zeilen.append(f"Betrag: {bc['tranche_eur']} EUR")
        hinweis = cash_hinweis(1568.72, bc["tranche_eur"])
        if hinweis:
            zeilen.append(hinweis)
    for f in ("einstieg_eur", "stop_eur"):
        if bc.get(f) is not None:
            zeilen.append(f"{f}: {bc[f]}")
    zeilen += [f"unabhaengige Faktoren: {bc['unabhaengige_faktoren']} "
               f"(von {len(bc['belege'])} Belegen)",
               f"Begruendung: {bc['begruendung']}",
               f"Dagegen: {bc['was_dagegen']}",
               f"Umgeworfen durch: {bc['umgeworfen_durch']}"]
    zeilen += [f"{b['richtung']:8} {b['gewicht']:7} {b['fakt']}" for b in bc["belege"]]
    for marker in ("_korrekturen", "_degradiert", "_warnung", "_luecken"):
        if bc.get(marker):
            zeilen.append(f"{marker.upper()}: {bc[marker]}")
    zeige("AUSGABE ROLLE BC", zeilen)

    # --- DER ENTSCHEIDER (Paket 8) -----------------------------------------
    # Er steht am Ende, weil er alles davor voraussetzt - und weil genau das
    # in der E-Mail stehen soll. Er entscheidet nichts: er rechnet und sagt es.
    from agent import trefferbilanz as TB
    ein, stop = bc.get("einstieg_eur"), bc.get("stop_eur")
    kosten = TB.kosten_r_aus_stop(ein, stop)
    if kosten is None:
        zeige("ENTSCHEIDER", ["keine Zonen - keine Kostenrechnung moeglich"])
        return
    con = sqlite3.connect(DB)
    try:
        bilanz = TB.zaehle(con)
    finally:
        con.close()
    schluessel = TB.merkmale(
        unabhaengige_faktoren=bc.get("unabhaengige_faktoren"))
    zeige("ENTSCHEIDER",
          [f"Stopabstand {100 * (ein - stop) / ein:.2f} % des Kurses "
           f"-> Kosten {kosten:.2f} R"]
          + TB.satz(TB.bewerte(bilanz, schluessel, kosten_r=kosten)))


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--symbol")
    p.add_argument("--datum")
    p.add_argument("--anbieter", default=None,
                   help="gemini35 | openrouter; ohne Angabe trocken")
    p.add_argument("--trocken", action="store_true")
    p.add_argument("--pruefsteine", action="store_true")
    args = p.parse_args()

    anbieter = None if args.trocken else args.anbieter
    if args.pruefsteine and anbieter:
        print(f"KONTINGENT: {len(PRUEFSTEINE)} Faelle x 2 Aufrufe = "
              f"{len(PRUEFSTEINE) * 2} Aufrufe an {anbieter}")

    reihen = lade_reihen()
    if args.pruefsteine:
        for sym, datum, alt, folge in PRUEFSTEINE:
            lauf(sym, datum, reihen, anbieter, f"alt: {alt} -> {folge}")
    elif args.symbol:
        lauf(args.symbol, args.datum, reihen, anbieter)
    else:
        print("[FEHLER] --symbol oder --pruefsteine noetig")
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
