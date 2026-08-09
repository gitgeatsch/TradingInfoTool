"""Erzeugt die Messdaten, die die Produktion nicht liefert.

DER AUFTRAG, woertlich (Nutzer, 09.08.): *"DU sollst unsere fehlenden Daten
fuer die von uns benoetigten Messungen und Parameter-Einstellungen durchfuehren
- DAMIT wir dann fuer die Produktion die korrekten Massnahmen ableiten
koennen."*

WARUM DAS NOETIG IST - DER DEAD LOOP IN EINER ZAHL. Die Wiedervorlage vom
31.07. verlangt fuer die Validierung der TP-ATR-Leitplanke *"n >= 15 neue,
aufgeloeste Hebel-LONG-Signale mit gesetztem atr_relativ_prozent_bei_signal"*.
Stand 09.08.:

    LONG   3        (noetig 15)
    SHORT  3
    gesamt 6

Und seit dem 05.08. entsteht **kein einziges LONG-EROEFFNEN mehr** - vorher
blockierte der Nur-Long-Filter alle SHORT, danach schlaegt das Screening fast
nur noch SHORT vor. Das System hatte nie beide Richtungen gleichzeitig. Jeder
Befund aus einem Regime ist im anderen nicht pruefbar, und der einzige
bestaetigte Zonenbefund haengt seit neun Tagen in der Luft.

Auf Produktionsdaten zu warten heisst, Monate zu warten - und dann sind die
Parameter fuer eine Marktphase kalibriert, die vorbei ist.

DIE LOESUNG. Wir haben zwei Jahre Kurshistorie ueber 20 Symbole und einen
funktionierenden LLM. Also fragen wir das Modell an historischen Ankerpunkten,
lassen es die Zonen SELBST setzen, und werten gegen den tatsaechlichen
weiteren Verlauf aus. Kein Warten auf Signalfluss.

KEIN VORAUSSCHAUEN. `_reihe_bis()` schneidet die Kursreihe hart am Ankertag ab,
BEVOR ein Indikator gerechnet wird - uebernommen aus
`backtest_llm1_historisch.py`. Ohne das waere alles wertlos, und der Fehler
waere im Ergebnis nicht zu sehen; es saehe nur verdaechtig gut aus.

WAS DIESES SKRIPT ZUSAETZLICH AUFZEICHNET. Das bestehende Werkzeug gibt nur
ein R zurueck. Fuer Parameterfragen ist das zu wenig - wir brauchen die
STELLGROESSEN neben dem Ergebnis:

    stop_pct / stop_atr      wie eng sitzt der Stop, absolut und ATR-relativ
    ziel_pct / ziel_atr      wie weit das Ziel - die offene Frage vom 31.07.
    crv                      was das Modell sich selbst zutraut
    ausgang                  ziel / stop / zensiert
    r, mfe                   Ergebnis und wie weit es guenstig lief
    richtung, regime, atr    Kontext zum Aufschluesseln

Damit beantwortet EIN Lauf mehrere Fragen: welches TP-ATR-Vielfache trifft am
besten, wo liegt die Stop-Untergrenze, sitzt die CRV-Schwelle 2,0 richtig, und
unterscheiden sich LONG und SHORT.

    python erzeuge_parameterdaten.py --anker 40 --trocken     # Verdrahtung
    python erzeuge_parameterdaten.py --anker 300 --pause 2.0
"""
from __future__ import annotations

import argparse
import json
import pathlib
import statistics
import sys
import time
from collections import Counter

from backtest_llm1_historisch import (
    HORIZONT,
    VORLAUF_MIN,
    Kerze,
    baue_historische_fakten,
    lade_reihen,
)
from agent.krypto.backward_tracking import gap_bewusster_fill


def _anker(reihen: dict, anzahl: int, je_symbol: int) -> list[tuple[str, int]]:
    """Ueber Symbole UND Zeit verteilt - keine Marktphase darf dominieren."""
    roh = []
    for sym, reihe in sorted(reihen.items()):
        if len(reihe) < VORLAUF_MIN + HORIZONT + 5:
            continue
        moeglich = list(range(VORLAUF_MIN, len(reihe) - HORIZONT - 2))
        schritt = max(1, len(moeglich) // je_symbol)
        for i in moeglich[::schritt][:je_symbol]:
            roh.append((sym, i))
    roh.sort(key=lambda x: (x[1], x[0]))
    if anzahl and len(roh) > anzahl:
        roh = roh[:: max(1, len(roh) // anzahl)][:anzahl]
    return roh


def _zonen(antwort: dict) -> dict | None:
    """Die vom MODELL gesetzten Zonen, richtungsbewusst wie `_zonen_absolut()`."""
    try:
        e = (antwort["entry"]["usd_von"] + antwort["entry"]["usd_bis"]) / 2.0
        s_von, s_bis = antwort["stop_loss"]["usd_von"], antwort["stop_loss"]["usd_bis"]
        t_von, t_bis = antwort["take_profit"]["usd_von"], antwort["take_profit"]["usd_bis"]
    except (KeyError, TypeError):
        return None
    if not e or e <= 0 or None in (s_von, s_bis, t_von, t_bis):
        return None
    ist_short = t_von < e
    stop = s_bis if ist_short else s_von
    ziel = t_bis if ist_short else t_von
    risiko = (stop - e) if ist_short else (e - stop)
    chance = (e - ziel) if ist_short else (ziel - e)
    if risiko <= 0 or chance <= 0:
        return None
    return {"entry": e, "stop": stop, "ziel": ziel, "risiko": risiko,
            "chance": chance, "ist_short": ist_short, "crv": chance / risiko}


def _auswerten(z: dict, reihe: list[Kerze], i: int) -> dict:
    """Ausgang, R und MFE gegen den echten weiteren Verlauf."""
    e, stop, ziel, risiko = z["entry"], z["stop"], z["ziel"], z["risiko"]
    kurz = z["ist_short"]
    mfe = None
    for tag, k in enumerate(reihe[i + 1:i + 2 + HORIZONT]):
        guenstig = k.low if kurz else k.high
        r_guenstig = ((e - guenstig) if kurz else (guenstig - e)) / risiko
        mfe = r_guenstig if mfe is None else max(mfe, r_guenstig)
        # Stop schlaegt Ziel am selben Tag - konservativ, wie im Backward-Tracking.
        if (k.high >= stop) if kurz else (k.low <= stop):
            f = gap_bewusster_fill(stop, k.open, True, kurz)
            return {"ausgang": "stop", "tag": tag,
                    "r": ((e - f) if kurz else (f - e)) / risiko, "mfe": mfe}
        if (k.low <= ziel) if kurz else (k.high >= ziel):
            f = gap_bewusster_fill(ziel, k.open, False, kurz)
            return {"ausgang": "ziel", "tag": tag,
                    "r": ((e - f) if kurz else (f - e)) / risiko, "mfe": mfe}
    letzte = reihe[min(i + 1 + HORIZONT, len(reihe) - 1)]
    return {"ausgang": "zensiert", "tag": HORIZONT,
            "r": ((e - letzte.close) if kurz else (letzte.close - e)) / risiko,
            "mfe": mfe}


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--anker", type=int, default=300)
    p.add_argument("--je-symbol", type=int, default=25)
    p.add_argument("--pause", type=float, default=2.0)
    p.add_argument("--trocken", action="store_true")
    p.add_argument("--anbieter", choices=("openrouter", "gemini"),
                   default="openrouter",
                   help="openrouter (Vorgabe, ~1.000 Anfragen/Tag frei) oder "
                        "gemini (nur 500/Tag - am 09.08. daran gescheitert)")
    p.add_argument("--fortsetzen")
    p.add_argument("--ausgabe", default="parameterdaten.json")
    args = p.parse_args()

    reihen = lade_reihen()
    btc = reihen.get("BTC")
    anker = _anker(reihen, args.anker, args.je_symbol)
    print(f"Ankerpunkte: {len(anker)} ueber {len({s for s, _ in anker})} Symbole")
    if anker:
        von = min(reihen[s][i].date for s, i in anker)
        bis = max(reihen[s][i].date for s, i in anker)
        print(f"Zeitraum:    {von} .. {bis}")
    print(f"Horizont:    {HORIZONT} Tage, Vorlauf {VORLAUF_MIN}")
    print()

    bekannt = {}
    if args.fortsetzen and pathlib.Path(args.fortsetzen).exists():
        alt = json.loads(pathlib.Path(args.fortsetzen).read_text(encoding="utf-8"))
        for z in alt.get("zeilen", []):
            if z.get("antwort"):
                bekannt[z["id"]] = z["antwort"]
        print(f"Wiederaufnahme: {len(bekannt)} Antworten werden wiederverwendet.\n")

    if args.trocken:
        zaehler = [0]

        def frage(fakten):
            zaehler[0] += 1
            preis = (fakten.get("preis") or {}).get("usd") or 100.0
            if zaehler[0] % 4 == 0:
                return {"action": "HALTEN"}
            streu = ((zaehler[0] * 2654435761) % 100) / 100.0 * 0.04
            return {"action": "ERÖFFNEN",
                    "entry": {"usd_von": preis, "usd_bis": preis},
                    "stop_loss": {"usd_von": preis * (0.95 + streu * 0.5),
                                  "usd_bis": preis * (0.95 + streu * 0.5)},
                    "take_profit": {"usd_von": preis * (1.06 + streu * 2),
                                    "usd_bis": preis * (1.06 + streu * 2)}}
    else:
        import os
        import config as config_module
        from agent.krypto.hebel_analyst import SYSTEM_PROMPT
        config_module.load_env()

        # ANBIETERWAHL (2026-08-09). Der erste Lauf ging auf Gemini und starb an
        # 200x HTTP 429: das freie Tageskontingent liegt bei 500 Anfragen und war
        # aufgebraucht. Deshalb hier ausdruecklich waehlbar - und OpenRouter als
        # Vorgabe, weil dessen Free-Boden bei 1.000/Tag liegt und
        # `nemotron-3-super-120b` den echten Hebel-Prompt nachweislich traegt
        # (16/20 gueltig, Median 20,8 s, Messung 08.08.).
        if args.anbieter == "gemini":
            from api.gemini import GeminiClient
            schluessel = os.environ.get("GEMINI_API_KEY")
            if not schluessel:
                print("GEMINI_API_KEY fehlt.")
                return 1
            client = GeminiClient(schluessel)
        else:
            from api.openrouter import OpenRouterClient
            schluessel = os.environ.get("OPENROUTER_API_KEY")
            if not schluessel:
                print("OPENROUTER_API_KEY fehlt.")
                return 1
            client = OpenRouterClient(schluessel)

        def frage(fakten):
            time.sleep(args.pause)
            roh = client.chat(
                [{"role": "system", "content": SYSTEM_PROMPT},
                 {"role": "user", "content": json.dumps(fakten, ensure_ascii=False)}],
                temperature=0.2, response_format={"type": "json_object"})
            antwort = json.loads(roh)
            # Welches Modell hat WIRKLICH geantwortet? Die Rotation in
            # OpenRouterClient.chat() faellt bei Ausfall auf ein anderes Modell
            # zurueck - ohne diese Zeile stuende im Protokoll ein 120B-Modell und
            # geantwortet haette vielleicht ein 20B. Das waere eine stille
            # Qualitaetsaenderung mitten im Datensatz.
            modell = getattr(client, "letztes_modell", None)
            if modell:
                antwort["_modell"] = modell
            return antwort

    zeilen, fehler = [], Counter()
    beginn = time.time()
    for nr, (sym, i) in enumerate(anker, 1):
        reihe = reihen[sym]
        kennung = f"{sym}@{reihe[i].date}"
        fakten = baue_historische_fakten(sym, reihe, i, btc)
        if fakten is None:
            fehler["kein_faktensatz"] += 1
            continue
        antwort = bekannt.get(kennung)
        if antwort is None:
            try:
                antwort = frage(fakten)
            except Exception as exc:
                fehler[type(exc).__name__] += 1
                zeilen.append({"id": kennung, "symbol": sym, "datum": reihe[i].date,
                               "fehler": type(exc).__name__})
                continue
        satz = {"id": kennung, "symbol": sym, "datum": reihe[i].date,
                "antwort": antwort, "action": antwort.get("action"),
                "konfidenz": antwort.get("confidence_pct")}
        # Der historische Faktensatz fuehrt `atr` als ABSOLUTEN Wert (der
        # Betriebs-Faktensatz dagegen als Dict mit `relativ_prozent`). Hier
        # also selbst relativieren - ohne das ist kein ATR-Vielfaches
        # rechenbar, und genau die sind die offene Frage vom 31.07.
        ta = fakten.get("technische_analyse") or {}
        atr_abs = ta.get("atr")
        preis_usd = (fakten.get("preis") or {}).get("usd")
        if isinstance(atr_abs, dict):
            satz["atr_pct"] = atr_abs.get("relativ_prozent")
        elif atr_abs and preis_usd:
            satz["atr_pct"] = round(atr_abs / preis_usd * 100, 4)
        else:
            satz["atr_pct"] = None
        satz["atr_perzentil"] = ta.get("atr_perzentil")
        satz["regime"] = (fakten.get("regime") or {}).get("wert")
        z = _zonen(antwort)
        if z is not None:
            erg = _auswerten(z, reihe, i)
            satz.update({
                "richtung": "SHORT" if z["ist_short"] else "LONG",
                "crv": round(z["crv"], 3),
                "stop_pct": round(z["risiko"] / z["entry"] * 100, 3),
                "ziel_pct": round(z["chance"] / z["entry"] * 100, 3),
                **erg,
            })
            if satz["atr_pct"]:
                satz["stop_atr"] = round(satz["stop_pct"] / satz["atr_pct"], 3)
                satz["ziel_atr"] = round(satz["ziel_pct"] / satz["atr_pct"], 3)
        zeilen.append(satz)
        if nr % 25 == 0 or nr == len(anker):
            bewertet = sum(1 for x in zeilen if x.get("ausgang"))
            print(f"  {nr}/{len(anker)}  bewertet {bewertet}  "
                  f"Fehler {sum(fehler.values())}  "
                  f"{(time.time()-beginn)/60:.0f} min", flush=True)
            pathlib.Path(args.ausgabe).write_text(
                json.dumps({"zeilen": zeilen, "fehler": dict(fehler),
                            "horizont": HORIZONT}, ensure_ascii=False),
                encoding="utf-8")

    bewertbar = [z for z in zeilen if z.get("ausgang")]
    print()
    print(f"Fertig: {len(zeilen)} Anker, {len(bewertbar)} mit Zonen und Ausgang")
    print(f"Fehler: {dict(fehler)}")
    if bewertbar:
        print(f"Richtung:  {dict(Counter(z['richtung'] for z in bewertbar))}")
        print(f"Ausgang:   {dict(Counter(z['ausgang'] for z in bewertbar))}")
        print(f"Median CRV {statistics.median(z['crv'] for z in bewertbar):.2f}, "
              f"Stop {statistics.median(z['stop_pct'] for z in bewertbar):.2f} %, "
              f"Ziel {statistics.median(z['ziel_pct'] for z in bewertbar):.2f} %")
    pathlib.Path(args.ausgabe).write_text(
        json.dumps({"zeilen": zeilen, "fehler": dict(fehler),
                    "horizont": HORIZONT}, ensure_ascii=False), encoding="utf-8")
    print(f"Geschrieben: {args.ausgabe}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
