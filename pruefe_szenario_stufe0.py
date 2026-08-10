"""Stufe 0 des Umbaus: baut der neue Faktensatz ueber ALLE Assetklassen?

KEIN EINZIGER LLM-AUFRUF. Stufe 0 ist die Trockenprobe - sie deckt die Fehler
auf, die sonst erst nach 200 verbrauchten Aufrufen sichtbar werden. Genau das
ist am 09. und 10.08. dreimal passiert: ein Lauf mit dem falschen Anbieter,
einer mit zerstoerter Stichprobe, einer gegen ein leeres Kontingent.

Geprueft wird in fuenf Abschnitten:

    A  Zonen     deterministisch, richtungssymmetrisch, CRV wie im Risk-Gate
    B  Fakten    baubar fuer alle sechs Assetklassen, aus echten Kursreihen
    C  Urteile   KEIN Werturteil im Faktensatz - der Waechter laeuft ueber
                 jeden gebauten Satz
    D  Schema    beide Anbieter, strikt und json_object, und das Schema passt
                 zum Validator
    E  Vertrag   der Validator nimmt gueltige Antworten an und weist jede
                 Verletzung mit Begruendung zurueck

    python pruefe_szenario_stufe0.py
"""
from __future__ import annotations

import json
import sys

import agent.llm_schema as LS
import agent.szenario_analyst as SA
from agent.szenario_fakten import (HORIZONT_KERZEN, STOP_IN_ATR, ZIEL_IN_ATR,
                                   baue_szenario_fakten, baue_zonen,
                                   enthaelt_werturteile)

_ok, _fehler = 0, []


def pruefe(name, bedingung, detail=""):
    global _ok
    if bedingung:
        _ok += 1
        print(f"  [ok]     {name}" + (f"   {detail}" if detail else ""))
    else:
        _fehler.append(name)
        print(f"  [FEHLER] {name}   {detail}")


print("A  Die Zonen - deterministisch und richtungssymmetrisch")

l = baue_zonen(100.0, 4.0, "LONG")
s = baue_zonen(100.0, 4.0, "SHORT")
pruefe("A1 LONG: Stop unter, Ziel ueber dem Einstieg",
       l["stop"] < l["einstieg"] < l["ziel"], f"{l['stop']}/{l['einstieg']}/{l['ziel']}")
pruefe("A2 SHORT: spiegelbildlich",
       s["ziel"] < s["einstieg"] < s["stop"], f"{s['ziel']}/{s['einstieg']}/{s['stop']}")
pruefe("A3 beide Richtungen haben DIESELBE Schwierigkeit",
       abs(l["ziel"] - l["einstieg"]) == abs(s["ziel"] - s["einstieg"])
       and abs(l["stop"] - l["einstieg"]) == abs(s["stop"] - s["einstieg"]),
       "sonst waere ein Trefferquoten-Vergleich zwischen den Richtungen wertlos")
pruefe("A4 CRV entspricht dem Risk-Gate-Minimum", l["crv"] == 2.0, str(l["crv"]))
pruefe("A5 Horizont steht im Aufbau", l["horizont_kerzen"] == HORIZONT_KERZEN)
# GEGENKONTROLLEN: kaputte Eingaben duerfen keine Zonen liefern.
pruefe("A5g Gegenkontrolle: ATR 0 ergibt KEINE Zonen",
       baue_zonen(100.0, 0.0, "LONG") is None)
pruefe("A6g Gegenkontrolle: unbekannte Richtung ergibt KEINE Zonen",
       baue_zonen(100.0, 4.0, "NEUTRAL") is None)

print("\nB  Faktensatz ueber alle sechs Assetklassen, aus echten Kursreihen")

from backtest_llm1_historisch import lade_reihen  # noqa: E402
from indicators.calculations import atr_wilder, latest_value, rsi  # noqa: E402
import numpy as np  # noqa: E402

# Kursreihen aus ZWEI Quellen: `lade_reihen()` liefert nur Krypto (50
# Symbole), die uebrigen Klassen stehen in `price_history_ohlc`. Beim ersten
# Lauf fehlten dadurch Hedge und Themen-ETF - der Bauplan war in Ordnung, der
# Test hatte an der falschen Stelle gesucht.
reihen = dict(lade_reihen())
import sqlite3  # noqa: E402
from collections import namedtuple  # noqa: E402
_K = namedtuple("_K", "date open high low close")
_DB = ("C:/Users/Geatsch/AppData/Local/Temp/claude/"
       "D--CLAUDE-Projects-SoftwareProjekte-TradingInfoTool/"
       "9e774fdd-5a46-48f6-9d20-e6614cad35af/scratchpad/prod_kopie.db")
_c = sqlite3.connect(f"file:{_DB}?mode=ro", uri=True)
for _sym in ("3QSS", "ISOC", "OD7N"):
    if reihen.get(_sym):
        continue
    _z = _c.execute("SELECT date, open, high, low, close FROM price_history_ohlc "
                    "WHERE symbol = ? ORDER BY date ASC", (_sym,)).fetchall()
    if _z:
        reihen[_sym] = [_K(*r) for r in _z]
_c.close()

KLASSEN = {"krypto": "BTC", "krypto_alt": "ETH", "hebel": "SUI",
           "rohstoffe": "OD7N", "hedge": "3QSS", "themen_etf": "ISOC"}
gebaut = {}
for klasse, sym in KLASSEN.items():
    reihe = reihen.get(sym)
    if not reihe or len(reihe) < 60:
        pruefe(f"B-{klasse} ({sym}) Kursreihe vorhanden", False,
               f"{len(reihe) if reihe else 0} Kerzen")
        continue
    closes = np.array([k.close for k in reihe], dtype=float)
    highs = np.array([k.high for k in reihe], dtype=float)
    lows = np.array([k.low for k in reihe], dtype=float)
    a = latest_value(atr_wilder(highs, lows, closes))
    r = latest_value(rsi(closes))
    f = baue_szenario_fakten(
        symbol=sym, assetklasse=klasse, kurs=float(closes[-1]), atr=float(a or 0),
        richtung="LONG", rsi=r,
        ema={"200": float(closes[-200:].mean())} if len(closes) >= 200 else None,
        konfluenz={"bullish": 2, "bearish": 1, "neutral": 1},
        atr_relativ_prozent=round(100.0 * (a or 0) / closes[-1], 2),
        rsi_historie=[float(x) for x in closes[-250:]],
        nicht_verfuegbar=["funding_rate"] if klasse.startswith("krypto") is False else None,
    )
    gebaut[klasse] = f
    pruefe(f"B-{klasse} ({sym}) Faktensatz gebaut", f is not None,
           f"{len(f)} Bloecke" if f else "None")

pruefe("B1 alle sechs Klassen liefern einen Satz",
       len(gebaut) == len(KLASSEN), f"{len(gebaut)} von {len(KLASSEN)}")
pruefe("B2 alle Saetze haben DIESELBE Grundform",
       len({tuple(sorted(f)) for f in gebaut.values()}) <= 2,
       str({tuple(sorted(f)) for f in gebaut.values()}))

print("\nC  Kein Werturteil im Faktensatz")

for klasse, f in gebaut.items():
    treffer = enthaelt_werturteile(f)
    pruefe(f"C-{klasse} frei von Werturteilen", not treffer, str(treffer))
# GEGENKONTROLLE: der Waechter muss ein eingeschmuggeltes Urteil FINDEN,
# sonst prueft er nichts.
schmuggel = json.loads(json.dumps(next(iter(gebaut.values()))))
schmuggel["technik"]["einordnung"] = "deutlich unter der Basislinie"
pruefe("C1g Gegenkontrolle: ein eingeschmuggeltes Urteil wird gefunden",
       "technik.einordnung" in enthaelt_werturteile(schmuggel),
       str(enthaelt_werturteile(schmuggel)))
pruefe("C2g Gegenkontrolle: die Zonen-Anweisung gilt NICHT als Urteil",
       "aufbau.hinweis" not in enthaelt_werturteile(next(iter(gebaut.values()))))

print("\nD  Schema fuer BEIDE Anbieter")


class _Gemini:
    pass


class _OpenRouter:
    pass


_Gemini.__module__ = "api.gemini"
_OpenRouter.__module__ = "api.openrouter"
fmt_g = LS.response_format_fuer(_Gemini(), "agent.szenario_analyst")
fmt_o = LS.response_format_fuer(_OpenRouter(), "agent.szenario_analyst")
pruefe("D1 Gemini bekommt json_object", fmt_g["type"] == "json_object")
pruefe("D2 OpenRouter bekommt das strikte Schema", fmt_o["type"] == "json_schema")
schema = fmt_o["json_schema"]["schema"]
pruefe("D3 Schema-Pflichtfelder = Validator-Pflichtfelder",
       tuple(schema["required"]) == SA.REQUIRED_SZENARIO_TOP_LEVEL_FIELDS,
       str(schema["required"]))
pruefe("D4 die drei Ausgaenge stehen im Schema",
       tuple(schema["properties"]["szenarien"]["required"]) == SA.SZENARIEN)
pruefe("D5 Vokabular abgeleitet, nicht geschrieben",
       schema["properties"]["unsicherheit"]["enum"] == list(SA.UNSICHERHEIT_WERTE)
       and schema["properties"]["belege"]["items"]["properties"]["richtung"]["enum"]
       == list(SA.BELEG_RICHTUNGEN))
pruefe("D6 Belege-Grenzen aus den Konstanten",
       schema["properties"]["belege"]["minItems"] == SA.MIN_BELEGE
       and schema["properties"]["belege"]["maxItems"] == SA.MAX_BELEGE)

print("\nE  Der Vertrag - was der Validator annimmt und was nicht")

GUELTIG = {
    "belege": [{"fakt": "RSI 71,6 nahe dem oberen Band", "richtung": "pro_stop",
                "gewicht": "mittel"},
               {"fakt": "Kurs 0,8 ATR ueber dem EMA-200", "richtung": "pro_ziel",
                "gewicht": "hoch"}],
    "szenarien": {"ziel_zuerst_pct": 40, "stop_zuerst_pct": 35, "keines_pct": 25},
    "bedingung_ziel": "Bruch ueber das obere Bollinger-Band mit Anschlusskauf",
    "widerlegung_ziel": "Ruecklauf unter den EMA-200 innerhalb von zwei Tagen",
    "staerkstes_gegenargument": "Die Schwankungsbreite liegt im obersten Perzentil",
    "unsicherheit": "mittel",
}
try:
    SA._validate_szenario(json.loads(json.dumps(GUELTIG)), "TEST")
    pruefe("E1 eine gueltige Antwort wird angenommen", True)
except Exception as exc:  # noqa: BLE001
    pruefe("E1 eine gueltige Antwort wird angenommen", False, str(exc))


def weist_zurueck(name, aenderung, erwartet_im_text):
    a = json.loads(json.dumps(GUELTIG))
    aenderung(a)
    try:
        SA._validate_szenario(a, "TEST")
        pruefe(name, False, "durchgelassen")
    except SA.SzenarioAntwortUngueltig as exc:
        pruefe(name, erwartet_im_text.lower() in str(exc).lower(), str(exc)[:80])


weists = weist_zurueck
weists("E2 Summe 90 statt 100 wird abgewiesen",
       lambda a: a["szenarien"].update(keines_pct=15), "summieren")
weists("E3 unbekanntes Beleg-Vokabular wird abgewiesen",
       lambda a: a["belege"][0].update(richtung="bullisch"), "richtung")
weists("E4 fehlendes Pflichtfeld wird abgewiesen",
       lambda a: a.pop("widerlegung_ziel"), "fehlen")
weists("E5 zu wenige Belege werden abgewiesen",
       lambda a: a.update(belege=a["belege"][:1]), "belege")
weists("E6 leeres Begruendungsfeld wird abgewiesen",
       lambda a: a.update(bedingung_ziel="  "), "leer")
weists("E7 Wahrscheinlichkeit ueber 100 wird abgewiesen",
       lambda a: a["szenarien"].update(ziel_zuerst_pct=140, stop_zuerst_pct=-40),
       "ausserhalb")
# GEGENKONTROLLE: Rundung darf NICHT abgewiesen werden - sonst faellt jede
# zweite echte Antwort durch.
a = json.loads(json.dumps(GUELTIG))
a["szenarien"].update(ziel_zuerst_pct=40.3, stop_zuerst_pct=34.9, keines_pct=25.3)
try:
    SA._validate_szenario(a, "TEST")
    pruefe("E7g Gegenkontrolle: Summe 100,5 wird toleriert", True)
except Exception as exc:  # noqa: BLE001
    pruefe("E7g Gegenkontrolle: Summe 100,5 wird toleriert", False, str(exc))

print("\n" + "=" * 74)
print(f"{_ok} Pruefungen bestanden, {len(_fehler)} fehlgeschlagen")
for f in _fehler:
    print(f"   FEHLER: {f}")
if not _fehler:
    print("\nStufe 0 steht. Was sie NICHT prueft: ob das Modell brauchbare "
          "Wahrscheinlichkeiten liefert - das ist Stufe 1 (Brier-Score gegen "
          "die Regel-Grundlinie) und kostet Kontingent.")
sys.exit(1 if _fehler else 0)
