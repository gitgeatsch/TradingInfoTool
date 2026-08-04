"""Messen, BEVOR gebaut wird: zwei Prompt-Aenderungen an LLM1 (2026-08-04).

DIE BEIDEN VORSCHLAEGE, beide aus Recherche und eigener Messung abgeleitet:

  V1  `disclaimers` von der letzten Position wegnehmen.
      Begruendung: die letzte Position bekommt laut "Lost in the Middle"
      verlaesslich das meiste Gewicht (an der echten Z.ai-API am 29.07.
      bestaetigt, an Mistral am 04.08. mit 5,3-fachem Eigenrauschen). Dort
      steht heute ein Hinweistext OHNE Marktevidenz. Das ist keine "klug
      gewaehlte Reihenfolge" - die wurde am 29.07. verworfen, weil vorher
      nicht bekannt ist, welcher Fakt der Ausreisser ist. Es raeumt nur den
      staerksten Platz von etwas, das dort nichts zu suchen hat.

  V2  Chain-of-Thought ausweiten.
      Begruendung: die systematische Auswertung von neun Debiasing-Verfahren
      (arXiv 2604.23178) findet Chain-of-Thought als EINZIGES universell
      positiv (+13,0 pp auf kritischen Faellen), waehrend Position Swapping
      dort signifikant SCHADET (-6,5 bis -11,1 pp, Mechanismus:
      "tie-on-disagreement discards correct verdicts"). Der Prompt hat die
      Technik bereits punktuell - Regel 13 erzwingt `gegenargument` VOR
      `confidence_pct`. V2 weitet sie auf einen kurzen festen Pruefablauf aus.

AUSDRUECKLICH NICHT GEPRUEFT: Position Swapping bei LLM1. Die Literatur raet
bei kritischen Entscheidungen davon ab, und der Schadensmechanismus passt
genau: bei Uneinigkeit der Reihenfolgen waere das Ausweichergebnis HALTEN -
also weniger Signale bei korrekt erkannten Chancen, das Gegenteil des Ziels.

VIER ARME, Rauschboden verpflichtend:
    A1  unveraendert
    A2  unveraendert  <- misst das Eigenrauschen
    V1  disclaimers nicht mehr zuletzt
    V2  erweiterte Chain-of-Thought im System-Prompt

Lauf: python -u messe_prompt_verbesserungen.py [--n 6] [--w 5]
"""
from __future__ import annotations

import json
import os
import statistics
import sys

from agent.krypto.hebel_analyst import SYSTEM_PROMPT
from api.mistral import MistralClient
from messe_llm1_positionsbias import (
    WARTE_SEKUNDEN, VERSUCHE, _arg, abstand, baue_fakten,
)

ORDNER = r"K:\My Drive\Claude_Austauschordner\Notebook_Analysedaten"

# V2: der Zusatz. Bewusst KURZ - ein langer Ablauf verschiebt selbst wieder
# Gewichte, und die Wirkung soll dem Ablauf zuzurechnen sein, nicht der Laenge.
# Bewusst OHNE Zahlenbeispiel (Anker-Kollaps, siehe project_konfidenz_prompt_fixes).
COT_ZUSATZ = """

ARBEITSWEISE (vor der Antwort, in dieser Reihenfolge):
a) Nenne die zwei Fakten, die am staerksten FUER deine These sprechen.
b) Nenne die zwei Fakten, die am staerksten DAGEGEN sprechen.
c) Erst danach entscheide `action` und lege `confidence_pct` fest.
Diese Abwaegung fliesst in `gegenargument` und `short_reasoning` ein; gib sie
nicht als eigenes Feld aus."""


def ohne_disclaimer_zuletzt(fakten: dict) -> dict:
    """`disclaimers` von der letzten auf die zweite Position.

    Nicht entfernt - der Hinweis bleibt im Prompt, nur nicht mehr auf dem
    staerksten Platz. So misst der Arm die POSITION, nicht das Weglassen."""
    if "disclaimers" not in fakten:
        return dict(fakten)
    keys = [k for k in fakten if k not in ("asset", "disclaimers")]
    neu = (["asset"] if "asset" in fakten else []) + ["disclaimers"] + keys
    return {k: fakten[k] for k in neu}


def frage(client, fakten: dict, system: str) -> dict | None:
    import time
    msg = [{"role": "system", "content": system},
           {"role": "user", "content": json.dumps(fakten, ensure_ascii=False)}]
    for versuch in range(VERSUCHE):
        try:
            time.sleep(WARTE_SEKUNDEN)
            return json.loads(client.chat(msg, temperature=0.2,
                                          response_format={"type": "json_object"}))
        except Exception as exc:
            if versuch == VERSUCHE - 1:
                print(f"    (aufgegeben: {type(exc).__name__})", flush=True)
                return None
            time.sleep(WARTE_SEKUNDEN * (2 ** versuch))
    return None


def sammle(client, fakten, system, w):
    acts, konf = [], []
    for _ in range(w):
        a = frage(client, fakten, system)
        if not a:
            continue
        acts.append(str(a.get("action", "?")).upper())
        k = a.get("confidence_pct")
        if isinstance(k, (int, float)):
            konf.append(float(k))
    return acts, konf


def main() -> int:
    key = os.environ.get("MISTRAL_API_KEY")
    if not key:
        import io as _io, re as _re
        for z in _io.open(".env", encoding="utf-8", errors="replace"):
            m = _re.match(r"\s*([A-Z_]+)\s*=\s*(.*)", z)
            if m:
                os.environ.setdefault(m.group(1), m.group(2).strip().strip('"').strip("'"))
        key = os.environ.get("MISTRAL_API_KEY")
    if not key:
        print("MISTRAL_API_KEY fehlt")
        return 1

    n, w = _arg("--n", 6), _arg("--w", 5)
    import io
    d = json.load(io.open(ORDNER + r"\notebook_diagnose.json", encoding="utf-8"))
    stamm = d.get("watchlist_stammdaten") or {}
    SCHWELLE = 60.0
    mz = [s for s in d["hebel_signals"]
          if s.get("entry_usd_von") and s.get("take_profit_usd_von")
          and isinstance(s.get("confidence_pct"), (int, float))]
    kand, gesehen = [], set()
    for s in sorted(mz, key=lambda x: abs(x["confidence_pct"] - SCHWELLE)):
        if s["symbol"] in gesehen:
            continue
        gesehen.add(s["symbol"])
        kand.append(s)
        if len(kand) >= n:
            break

    client = MistralClient(api_key=key)
    print("=" * 74, flush=True)
    print(f"ZWEI PROMPT-AENDERUNGEN, gemessen   {len(kand)} Faelle x 4 Arme x {w}"
          f" = {len(kand)*4*w} Aufrufe", flush=True)
    print(f"grenzwertige Konfidenz {min(s['confidence_pct'] for s in kand):.0f}-"
          f"{max(s['confidence_pct'] for s in kand):.0f} % (Schwelle {SCHWELLE:.0f})",
          flush=True)
    print("=" * 74, flush=True)

    r_a, r_k, v1_a, v1_k, v2_a, v2_k, kipper = [], [], [], [], [], [], []
    for sig in kand:
        f = baue_fakten(sig, stamm)
        print(f"\n{sig['symbol']} (Konfidenz war {sig['confidence_pct']:.0f} %):",
              flush=True)
        a1 = sammle(client, f, SYSTEM_PROMPT, w)
        a2 = sammle(client, f, SYSTEM_PROMPT, w)
        b1 = sammle(client, ohne_disclaimer_zuletzt(f), SYSTEM_PROMPT, w)
        b2 = sammle(client, f, SYSTEM_PROMPT + COT_ZUSATZ, w)
        for name, arm in (("A1 unveraendert", a1), ("A2 unveraendert", a2),
                          ("V1 disclaimer weg vom Ende", b1),
                          ("V2 erweiterte CoT", b2)):
            k = f"{statistics.fmean(arm[1]):.1f}" if arm[1] else "-"
            print(f"  {name:28s} {dict((x, arm[0].count(x)) for x in set(arm[0]))}"
                  f"   Konfidenz {k}", flush=True)
        for name, arm in (("V1", b1), ("V2", b2)):
            if arm[0] and a1[0] and set(a1[0]) != set(arm[0]):
                print(f"  ** ENTSCHEIDUNG KIPPT bei {name}: "
                      f"{sorted(set(a1[0]))} -> {sorted(set(arm[0]))}", flush=True)
                kipper.append((sig["symbol"], name))
        r_a.append(abstand(a1[0], a2[0]))
        v1_a.append(abstand(a1[0], b1[0]))
        v2_a.append(abstand(a1[0], b2[0]))
        if a1[1] and a2[1]:
            m1 = statistics.fmean(a1[1])
            r_k.append(abs(m1 - statistics.fmean(a2[1])))
            if b1[1]:
                v1_k.append(abs(m1 - statistics.fmean(b1[1])))
            if b2[1]:
                v2_k.append(abs(m1 - statistics.fmean(b2[1])))

    def m(x):
        return statistics.fmean(x) if x else 0.0

    print("\n" + "=" * 74, flush=True)
    rb_a, rb_k = m(r_a), m(r_k)
    print(f"{'':30s} {'action':>9s} {'Konfidenz':>12s} {'x Rauschen':>12s}", flush=True)
    print(f"{'RAUSCHBODEN (A1 vs A2)':30s} {rb_a:9.3f} {rb_k:10.2f} pp {'-':>12s}",
          flush=True)
    for name, a, k in (("V1 disclaimer weg vom Ende", m(v1_a), m(v1_k)),
                       ("V2 erweiterte CoT", m(v2_a), m(v2_k))):
        srv = max((a / rb_a) if rb_a > 1e-9 else 0, (k / rb_k) if rb_k > 1e-9 else 0)
        print(f"{name:30s} {a:9.3f} {k:10.2f} pp {srv:11.1f}x", flush=True)
    print(flush=True)
    print(f"Entscheidung kippte: {kipper if kipper else 'in keinem Fall'}", flush=True)
    print(flush=True)
    print("Lesart: ab etwa 2x Eigenrauschen ist eine Wirkung nachweisbar. Ob sie", flush=True)
    print("ERWUENSCHT ist, sagt die Messung NICHT - dafuer braucht es Ergebnisse.", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
