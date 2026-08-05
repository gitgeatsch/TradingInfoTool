"""Die Regelwerksaenderungen vom 28./29.07. EINZELN gegen den Backtest (05.08.).

ANLASS. Die Trefferquote der LONG-Signale faellt ab dem 29.07. von 45,1 % auf
3,2 % (p = 0,0029, Block-Bootstrap ueber Symbole). Markt, Stop-Breite,
Richtung, Zensierung und Symbol-Clusterung sind als Erklaerung ausgeschlossen
(messe_short_und_einbruch.py, Phasen A-F). Uebrig bleibt das Deploy-Fenster
28./29.07. mit rund zehn Aenderungen. Drei davon fassen den LLM1-Prompt an -
und nur die lassen sich mit dem historischen Backtest einzeln testen:

  1b0ab91  28.07. 23:15  Enge-Stop-Loss: ATR-Richtwert STATT Hard-Veto.
                         Draengt den Stop auf >= 1,5x ATR, WEITET ihn also.
                         Liefert ausserdem atr.relativ_prozent im Faktensatz.
  c5acf6e  29.07. 12:05  Regel-13-Ausnahme: bei Regime-Konflikt/Alt-Skepsis
                         darf confidence_pct unter 75 % fallen.
  26f70af  29.07. 19:02  Regel 27, Action-Bias-Korrektur: HALTEN muss
                         GLEICHWERTIG gegen eine Empfehlung geprueft werden.

Die drei uebrigen (6756601, 4468a89, f72a700) aendern das deterministische
Gate, nicht den Prompt - sie gehoeren in einen eigenen, deterministischen
Test und sind hier bewusst NICHT enthalten.

WARUM DER RAUSCH-ARM PFLICHT IST. Der LLM1-Prompt-Thread vom 04.08. endete
damit, dass beide untersuchten Aenderungen bei rund 1 % des Eigenrauschens
lagen - also nicht unterscheidbar von Wiederholungsvarianz. Ohne A1/A2 waere
jeder hier gemessene Unterschied bedeutungslos. A1 und A2 sind derselbe
Prompt; was zwischen ihnen liegt, ist die Nachweisgrenze.

WAS GEMESSEN WIRD, ist nicht die Aenderung der Entscheidung, sondern ihre
RICHTIGKEIT: das R-Multiple der vom Modell SELBST gesetzten Zonen gegen den
tatsaechlichen weiteren Kursverlauf (bewerte() aus backtest_llm1_historisch).
Ein Prompt, der zu besseren Zonen fuehrt, gewinnt hier - einer, der nur
zuversichtlicher klingt, nicht.

WAS DIESER TEST NICHT KANN. Er misst die Prompt-Wirkung an historischen
Ankerpunkten, nicht den Produktionsverlauf. Faellt kein Arm auf, ist damit
NICHT bewiesen, dass die drei Aenderungen unschuldig sind - nur, dass ihre
Wirkung kleiner ist als das, was dieser Aufbau bei dieser Ankerzahl aufloest.
Das ist der ehrliche Rahmen, und er gehoert in jede Schlussfolgerung.

Lauf: python -u backtest_regeln_29_07.py [--n 10] [--w 3]
"""
from __future__ import annotations

import io
import os
import re
import statistics
import sys
from collections import defaultdict

from agent.krypto.hebel_analyst import SYSTEM_PROMPT
from api.mistral import MistralClient
from backtest_llm1_historisch import (
    VORLAUF_MIN, _arg, baue_historische_fakten, bewerte, frage, lade_reihen,
)

# --- Die drei Prompt-Bloecke, jeweils ueber Anfangs- und Endanker ------------
# Anker statt Volltext: der Prompt enthaelt Zeilenfortsetzungen, Umlaute und
# Backticks - ein Volltextvergleich waere gegen jede spaetere Umformatierung
# zerbrechlich. Die Anker sind so gewaehlt, dass sie genau einmal vorkommen;
# pruefe_bloecke() erzwingt das, statt es anzunehmen.
BLOECKE = {
    "1b0ab91 Stop-ATR-Richtwert": (
        "WICHTIG (2026-07-28, Backtest von 61",
        "explizit in `short_reasoning`.",
    ),
    "c5acf6e Regel-13-Ausnahme": (
        "AUSNAHME von dieser 75%-Untergrenze:",
        "dafür vorgesehene stärkere Abstufung.",
    ),
    "26f70af Regel 27 Action-Bias": (
        "27. Regelwerk-Audit Stufe 3, Punkt 4",
        "siehe project_regelwerk_audit_29_07.md).",
    ),
}


def entferne(prompt: str, anfang: str, ende: str) -> str:
    a = prompt.index(anfang)
    b = prompt.index(ende, a) + len(ende)
    # fuehrendes Leerzeichen mitnehmen, damit keine doppelten Luecken bleiben
    while a > 0 and prompt[a - 1] == " ":
        a -= 1
    return prompt[:a] + prompt[b:]


def pruefe_bloecke() -> None:
    """Ohne diese Pruefung waere ein stiller Fehlschlag moeglich: findet ein
    Anker nicht, entfiele der Block einfach nicht und der Arm waere in
    Wahrheit mit dem Kontrollarm identisch - das Ergebnis saehe dann wie ein
    sauberer Negativbefund aus."""
    for name, (a, e) in BLOECKE.items():
        if SYSTEM_PROMPT.count(a) != 1:
            raise SystemExit(f"Anfangsanker nicht eindeutig: {name} ({SYSTEM_PROMPT.count(a)}x)")
        if SYSTEM_PROMPT.count(e) < 1:
            raise SystemExit(f"Endanker fehlt: {name}")
        neu = entferne(SYSTEM_PROMPT, a, e)
        weg = len(SYSTEM_PROMPT) - len(neu)
        if weg < 100:
            raise SystemExit(f"verdaechtig wenig entfernt bei {name}: {weg} Zeichen")
        print(f"  {name:34s} -{weg:5d} Zeichen")


def baue_varianten() -> dict[str, str]:
    v = {
        "A1 Stand heute": SYSTEM_PROMPT,
        "A2 Stand heute (Rauschen)": SYSTEM_PROMPT,
    }
    for name, (a, e) in BLOECKE.items():
        v["ohne " + name.split()[0]] = entferne(SYSTEM_PROMPT, a, e)
    alle = SYSTEM_PROMPT
    for a, e in BLOECKE.values():
        alle = entferne(alle, a, e)
    v["C Stand vor 28.07."] = alle
    return v


def main() -> int:
    key = os.environ.get("MISTRAL_API_KEY")
    if not key:
        for z in io.open(".env", encoding="utf-8", errors="replace"):
            m = re.match(r"\s*([A-Z_]+)\s*=\s*(.*)", z)
            if m:
                os.environ.setdefault(m.group(1),
                                      m.group(2).strip().strip('"').strip("'"))
        key = os.environ.get("MISTRAL_API_KEY")
    if not key:
        print("MISTRAL_API_KEY fehlt")
        return 1

    print("=" * 78)
    print("Blockpruefung - wird ueberhaupt etwas entfernt?")
    print("=" * 78)
    pruefe_bloecke()

    varianten = baue_varianten()
    n, w = _arg("--n", 10), _arg("--w", 3)
    reihen = lade_reihen()
    btc = reihen.get("BTC")

    # ZWEI EINSCHRAENKUNGEN, beide notwendig. Ohne sie zog der erste Lauf
    # Ankerpunkte ab 2001 (OD7L ist eine Aktienreihe mit 6511 Tagen) - fuer
    # eine Frage ueber das heutige Krypto-Hebel-Regelwerk unbrauchbar.
    #   1. nur Reihen der Krypto-Watchlist (Start 2024-07-17, rund 750 Tage)
    #   2. nur Ankertage ab AB_DATUM, damit das Marktumfeld dem heutigen
    #      wenigstens nahekommt
    AB_DATUM = "2025-06-01"
    anker = []
    for sym, reihe in sorted(reihen.items()):
        if len(reihe) < VORLAUF_MIN + 18 or len(reihe) > 1200:
            continue
        for i in range(VORLAUF_MIN, len(reihe) - 16):
            if reihe[i].date >= AB_DATUM:
                anker.append((sym, i, reihe[i].date))
    if not anker:
        print("keine Ankerpunkte")
        return 1
    anker.sort(key=lambda x: (x[2], x[0]))
    anker = anker[:: max(1, len(anker) // n)][:n]

    client = MistralClient(api_key=key)
    print("\n" + "=" * 78)
    print(f"{len(anker)} Ankerpunkte x {len(varianten)} Varianten x {w} = "
          f"{len(anker) * len(varianten) * w} Aufrufe")
    print(f"Fenster: {anker[0][2]} .. {anker[-1][2]}")
    print("=" * 78)

    rr: dict[str, list[float]] = defaultdict(list)
    akt: dict[str, list[str]] = defaultdict(list)
    stopw: dict[str, list[float]] = defaultdict(list)

    for sym, i, tag in anker:
        fakten = baue_historische_fakten(sym, reihen[sym], i, btc)
        if fakten is None:
            continue
        print(f"\n{sym} @ {tag}:", flush=True)
        for name, prompt in varianten.items():
            werte = []
            for _ in range(w):
                a = frage(client, fakten, prompt)
                if not a:
                    continue
                akt[name].append(str(a.get("action", "?")).upper())
                r = bewerte(a, reihen[sym], i)
                if r is not None:
                    rr[name].append(r)
                    werte.append(r)
                try:
                    e = (a["entry"]["usd_von"] + a["entry"]["usd_bis"]) / 2.0
                    ist_s = str(a.get("richtung", "LONG")).upper() == "SHORT"
                    st = a["stop_loss"]["usd_bis" if ist_s else "usd_von"]
                    if e > 0:
                        stopw[name].append(abs(e - st) / e * 100)
                except (KeyError, TypeError, ZeroDivisionError):
                    pass
            print(f"  {name:28s} R = {[round(x, 2) for x in werte]}", flush=True)

    print("\n" + "=" * 78)
    print(f"{'Variante':28s}{'n':>4s}{'EROEFFN':>9s}{'EW R':>9s}{'Median R':>10s}"
          f"{'Stop %':>9s}")
    print("=" * 78)
    for name in varianten:
        a = akt.get(name, [])
        r = rr.get(name, [])
        if not a:
            continue
        er = sum(1 for x in a if x in ("ERÖFFNEN", "EROEFFNEN")) / len(a) * 100
        print(f"{name:28s}{len(a):4d}{er:8.0f}%"
              f"{(statistics.fmean(r) if r else float('nan')):9.3f}"
              f"{(statistics.median(r) if r else float('nan')):10.3f}"
              f"{(statistics.fmean(stopw[name]) if stopw.get(name) else float('nan')):9.2f}")

    a1, a2 = rr.get("A1 Stand heute", []), rr.get("A2 Stand heute (Rauschen)", [])
    if a1 and a2:
        boden = abs(statistics.fmean(a1) - statistics.fmean(a2))
        print("\n" + "=" * 78)
        print(f"NACHWEISGRENZE (A1 gegen A2, identischer Prompt): {boden:.3f} R")
        print("=" * 78)
        basis = statistics.fmean(a1 + a2)
        for name in varianten:
            if name.startswith("A"):
                continue
            r = rr.get(name, [])
            if not r:
                continue
            d = statistics.fmean(r) - basis
            urteil = ("TRAEGT" if abs(d) > 2 * boden else
                      "unter der Nachweisgrenze" if abs(d) < boden else "unklar")
            print(f"  {name:28s} {d:+7.3f} R  = {abs(d) / boden if boden else float('inf'):5.1f}x "
                  f"Rauschen   {urteil}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
