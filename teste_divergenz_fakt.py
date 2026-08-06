"""Bringt der Divergenz-Fakt etwas? Drei-Arm-Test auf echten Faktensaetzen (06.08.)

WAS GEBAUT WURDE. Der Fakt `regime.btc_zu_ema50` (Abstand in Prozent PLUS
kategoriale Einordnung) und dazu Regel 33 (Hebel) / 37 (Krypto-Spot). Die
Luecke kam aus einer Nutzer-Beobachtung: "BTC ist drei Tage gestiegen, aber
keine Aenderung in den Signalen" - nachgemessen +1,78 %, und unsichtbar, weil
`regime.wert` aus einer ODER-Bedingung stammt, in der Fear & Greed allein
"baer" erzwingt.

DREI ARME - getestet wird die Aenderung ALS GANZES, Regel und Fakt gemeinsam:
    A1  Stand nach dem Umbau - Prompt MIT Regel 33, Fakten MIT btc_zu_ema50
    A2  identisch zu A1 - der Abstand ist der Rauschboden
    B   ohne beides - Regel entfernt UND Fakt aus den Fakten

Eine Regel ohne Fakt verwiese ins Leere, ein Fakt ohne Regel waere eine nackte
Zahl (Kategorie (d) der Entscheidungsmappe) - genau der Zustand, aus dem heute
`score_gesamt` entfernt wurde.

WARUM DER FAKT NACHGERUESTET WERDEN MUSS. Die historischen Faktensaetze tragen
`btc_zu_ema50` noch nicht. Ohne Nachruesten bekaeme der A-Arm eine Regel, die
auf einen nicht vorhandenen Fakt verweist - exakt der kaputte Zustand, der am
05.08. in Regel 2 gefunden wurde ("wird dir separat mitgeteilt", ohne dass
etwas mitgeteilt wurde). Der Wert wird aus der BTC-Kursreihe zum jeweiligen
Signaldatum rekonstruiert, nicht geraten.

MESSGROESSEN, gepaart je Faktensatz:
    PFLICHT    EROEFFNEN-Quote - der Waechter. Ein Fakt, der die Quote drueckt,
               ist schaedlich, egal was er sonst bewirkt. Die Regel enthaelt
               ausdruecklich einen Hedging-Schutz; dieser Test prueft, ob er
               haelt.
    primaer    Konfidenz - reagiert das Modell ueberhaupt?
    sekundaer  Stop-Abstand und CRV.

ERWARTUNG VORAB: die EROEFFNEN-Quote bleibt unveraendert (sonst ist der
Hedging-Schutz gescheitert). Bei den uebrigen Groessen erwarte ich einen
kleinen Effekt - der Fakt beschreibt eine Lage, die heute fast durchgehend
"knapp darunter" lautet, also wenig Variation traegt.

Liest echte Faktensaetze aus dem Export. Braucht MISTRAL_API_KEY.
"""
from __future__ import annotations

import copy
import io
import json
import os
import re
import statistics
import sys
from collections import defaultdict

ORDNER = r"K:\My Drive\Claude_Austauschordner\Notebook_Analysedaten"
REGEL_ANFANG = "33. Regime-Divergenz"
REGEL_ENDE = "\n\nSCHEMA:"


def _arg(name, standard):
    if name in sys.argv:
        return type(standard)(sys.argv[sys.argv.index(name) + 1])
    return standard


def btc_reihe(d: dict) -> dict[str, float]:
    return {r["date"]: r["close"] for r in
            d["preishistorie_signal_symbole"]["preishistorie_je_symbol"]["BTC"]
            if r["currency"] == "USD" and r.get("close")}


def ema_bis(reihe: dict[str, float], datum: str, n: int = 50) -> float | None:
    """EMA50 aus allen Kursen BIS zum Signaldatum - kein Blick in die Zukunft."""
    werte = [v for t, v in sorted(reihe.items()) if t <= datum]
    if len(werte) < n:
        return None
    k = 2.0 / (n + 1)
    e = werte[0]
    for x in werte[1:]:
        e = x * k + e * (1 - k)
    return e


def main() -> int:
    if not os.environ.get("MISTRAL_API_KEY"):
        for z in io.open(".env", encoding="utf-8", errors="replace"):
            m = re.match(r"\s*([A-Z_]+)\s*=\s*(.*)", z)
            if m:
                os.environ.setdefault(m.group(1), m.group(2).strip().strip('"').strip("'"))

    from agent.krypto.hebel_analyst import SYSTEM_PROMPT
    from agent.krypto.regime import btc_ema50_einordnung
    from api.mistral import MistralClient
    from backtest_llm1_historisch import frage
    from teste_regime_llm import lade_faelle

    i = SYSTEM_PROMPT.find(REGEL_ANFANG)
    j = SYSTEM_PROMPT.find(REGEL_ENDE, i)
    if i < 0 or j < 0:
        raise SystemExit("Regel 33 im Prompt nicht gefunden")
    ohne_regel = SYSTEM_PROMPT[:i] + SYSTEM_PROMPT[j + 2:]
    weg = len(SYSTEM_PROMPT) - len(ohne_regel)
    if weg < 800:
        raise SystemExit(f"verdaechtig wenig entfernt: {weg} Zeichen")
    if REGEL_ANFANG in ohne_regel:
        raise SystemExit("Regel steht noch im B-Arm")
    print(f"B-Arm: Regel 33 entfernt (-{weg} Zeichen)")

    d = json.load(io.open(ORDNER + r"\notebook_diagnose.json", encoding="utf-8"))
    reihe = btc_reihe(d)
    n = _arg("--n", 12)
    w = _arg("--wdh", 1)
    faelle = [f for f in lade_faelle(n) if "regime" in json.loads(f["facts_json"])]
    arme = {"A1 mit Regel+Fakt": True, "A2 identisch (Rauschen)": True,
            "B ohne beides": False}
    print(f"{len(faelle)} Faktensaetze x {len(arme)} Arme x {w} = "
          f"{len(faelle)*len(arme)*w} Aufrufe")

    client = MistralClient(api_key=os.environ["MISTRAL_API_KEY"])
    akt, konf, stops, antworten = defaultdict(list), defaultdict(list), defaultdict(list), []

    for f in faelle:
        roh = json.loads(f["facts_json"])
        tag = f["created_at"][:10]
        e50 = ema_bis(reihe, tag)
        kurs = reihe.get(tag) or next((v for t, v in sorted(reihe.items(), reverse=True)
                                       if t <= tag), None)
        if not e50 or not kurs:
            print(f"  {f['symbol']}: kein EMA50 zum {tag}, uebersprungen")
            continue
        abstand = round((kurs / e50 - 1.0) * 100.0, 2)
        mit = copy.deepcopy(roh)
        mit["regime"]["btc_zu_ema50"] = {
            "abstand_prozent": abstand,
            "einordnung": btc_ema50_einordnung(abstand),
        }
        print(f"\n{f['symbol']} @ {f['created_at'][:16]}  BTC {abstand:+.2f} % zur EMA50 "
              f"({btc_ema50_einordnung(abstand)}):", flush=True)
        for name, hat in arme.items():
            fakten = mit if hat else roh
            prompt = SYSTEM_PROMPT if hat else ohne_regel
            zeile = []
            for _ in range(w):
                a = frage(client, fakten, prompt)
                if not a:
                    continue
                akt[name].append(str(a.get("action", "?")).upper())
                c = a.get("confidence_pct")
                if isinstance(c, (int, float)):
                    konf[name].append((f["symbol"], float(c)))
                try:
                    e = (a["entry"]["usd_von"] + a["entry"]["usd_bis"]) / 2.0
                    short = str(a.get("richtung", "LONG")).upper() == "SHORT"
                    st = a["stop_loss"]["usd_bis" if short else "usd_von"]
                    s = abs(e - st) / e * 100
                    if 0 < s < 60:
                        stops[name].append((f["symbol"], s))
                except (KeyError, TypeError, ZeroDivisionError):
                    pass
                zeile.append(f"{str(a.get('action','?'))[:4]}/{c}")
                antworten.append({"arm": name, "symbol": f["symbol"],
                                  "created_at": f["created_at"], "antwort": a})
            print(f"  {name:24s} {zeile}", flush=True)

    ziel = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "data", "divergenz_fakt_antworten.json")
    os.makedirs(os.path.dirname(ziel), exist_ok=True)
    alt = json.load(io.open(ziel, encoding="utf-8")) if os.path.exists(ziel) else []
    json.dump(alt + antworten, io.open(ziel, "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)

    print()
    print("=" * 80)
    print("ERGEBNIS (dieser Lauf)")
    print("=" * 80)
    for name in arme:
        a = akt[name]
        if not a:
            continue
        er = sum(1 for x in a if x == "ERÖFFNEN") / len(a) * 100
        k = [v for _, v in konf[name]]
        print(f"  {name:24s} EROEFFNEN {er:5.1f} %   Konfidenz "
              f"{statistics.fmean(k) if k else float('nan'):5.1f}   n={len(a)}")
    print(f"\n  {len(antworten)} Antworten gespeichert "
          f"({len(alt)+len(antworten)} gesamt) - Gesamtauswertung mit "
          f"werte_regime_llm_aus.py auf dieser Datei")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
