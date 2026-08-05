"""Zweite Ablationsrunde: traegt einer der SIEBEN fehlenden Bloecke? (05.08.)

RUNDE 1 ergab: weder Regime noch Funding/OI noch Fear&Greed senken die
Eroeffnungsrate (je 100 %, alles zusammen 96 %). Das HALTEN kommt NICHT aus
diesen Fakten.

Der Faktensatz-Vergleich gegen den Betrieb ergab dann sieben fehlende Bloecke:
historische_erfolgsquote, historischer_makro_vergleich, markt_kontext,
optionsmarkt, regime_profil, signal_stabilitaet, trigger.

ZWEI DAVON HABEN EINEN KLAREN WIRKMECHANISMUS:

  regime_profil  traegt `min_konfidenz_prozent` - eine EXPLIZITE Schwelle, die
                 dem Modell mitgeteilt wird. Im Baerenregime 75 %. Runde 1 mass
                 77-79 % Konfidenz, also KNAPP darueber - eine Schwelle an
                 dieser Stelle koennte genau den Ausschlag geben.
  trigger        sagt, WARUM dieser Kandidat kam (Zweig, Score). Ohne ihn
                 bewertet das Modell frei, statt einen Vorschlag zu PRUEFEN.

VORGEHEN: erst die Vereinigung testen (V7). Erzeugt sie HALTEN, wird
halbiert (V5 regime_profil allein, V6 trigger allein). Erzeugt sie keines,
liegt die Zurueckhaltung nicht im Faktensatz - dann kommt sie aus dem Gate
oder aus etwas, das dieser Aufbau strukturell nicht abbildet.

Lauf: python -u messe_halten_ursache2.py [--n 8] [--w 3]
"""
from __future__ import annotations

import io
import json
import os
import statistics
import sys
from collections import defaultdict

from agent.krypto.hebel_analyst import SYSTEM_PROMPT
from api.mistral import MistralClient
from backtest_llm1_historisch import (
    VORLAUF_MIN, _arg, baue_historische_fakten, frage, lade_reihen,
)
from messe_halten_ursache import (
    ORDNER, baue, block_antizyklisch, block_regime, block_regime_profil,
    block_stimmung, block_trigger, lade_zusatzfakten,
)


def lade_trigger() -> dict[tuple, list[dict]]:
    d = json.load(io.open(ORDNER + r"\notebook_diagnose.json", encoding="utf-8"))
    raus: dict[tuple, list[dict]] = defaultdict(list)
    for x in d["rohdaten_fuer_backtest"]["hebel_triggers_alle"]:
        tag = str(x.get("screened_at") or "")[:10]
        if tag and x.get("symbol"):
            raus[(x["symbol"], tag)].append(x)
    return dict(raus)


def main() -> int:
    key = os.environ.get("MISTRAL_API_KEY")
    if not key:
        import re
        for z in io.open(".env", encoding="utf-8", errors="replace"):
            m = re.match(r"\s*([A-Z_]+)\s*=\s*(.*)", z)
            if m:
                os.environ.setdefault(m.group(1), m.group(2).strip().strip('"').strip("'"))
        key = os.environ.get("MISTRAL_API_KEY")
    if not key:
        print("MISTRAL_API_KEY fehlt")
        return 1

    n, w = _arg("--n", 8), _arg("--w", 3)
    reihen = lade_reihen()
    btc = reihen.get("BTC")
    makro, oi = lade_zusatzfakten()
    trigger = lade_trigger()

    anker = []
    for sym, reihe in sorted(reihen.items()):
        if len(reihe) < VORLAUF_MIN + 2:
            continue
        for i in range(VORLAUF_MIN, len(reihe) - 1):
            tag = reihe[i].date
            if tag in makro and (sym, tag) in oi and (sym, tag) in trigger:
                anker.append((sym, i, tag))
    if not anker:
        print("keine Ankerpunkte mit Kurs UND Makro UND OI UND Trigger")
        return 1
    anker.sort(key=lambda x: (x[2], x[0]))
    anker = anker[:: max(1, len(anker) // n)][:n]

    client = MistralClient(api_key=key)
    print("=" * 78, flush=True)
    print(f"RUNDE 2: die fehlenden Bloecke   {len(anker)} Ankerpunkte x 4 Varianten"
          f" x {w} = {len(anker)*4*w} Aufrufe", flush=True)
    print(f"Fenster: {anker[0][2]} .. {anker[-1][2]}", flush=True)
    print("=" * 78, flush=True)

    zaehler: dict[str, list[str]] = defaultdict(list)
    konf: dict[str, list[float]] = defaultdict(list)

    for sym, i, tag in anker:
        basis = baue_historische_fakten(sym, reihen[sym], i, btc)
        if basis is None:
            continue
        mz, oz, tz = makro[tag], oi.get((sym, tag)), trigger.get((sym, tag))
        # V4 aus Runde 1 als neue Basislinie - so misst Runde 2 nur den
        # ZUSAETZLICHEN Beitrag der fehlenden Bloecke, nicht noch einmal den
        # der bereits geprueften.
        v4 = baue(basis, block_regime(mz), block_antizyklisch(oz), block_stimmung(mz))
        varianten = {
            "V4 Stand Runde 1": v4,
            "V5 + regime_profil": baue(v4, block_regime_profil(mz)),
            "V6 + trigger": baue(v4, block_trigger(tz)),
            "V7 beide": baue(v4, block_regime_profil(mz), block_trigger(tz)),
        }
        print(f"\n{sym} @ {tag}:", flush=True)
        for name, fakten in varianten.items():
            acts = []
            for _ in range(w):
                a = frage(client, fakten, SYSTEM_PROMPT)
                if not a:
                    continue
                acts.append(str(a.get("action", "?")).upper())
                zaehler[name].append(acts[-1])
                k = a.get("confidence_pct")
                if isinstance(k, (int, float)):
                    konf[name].append(float(k))
            print(f"  {name:22s} {dict((x, acts.count(x)) for x in sorted(set(acts)))}",
                  flush=True)

    print("\n" + "=" * 78, flush=True)
    print(f"{'Variante':24s} {'n':>4s} {'EROEFFNEN':>10s} {'HALTEN':>8s} "
          f"{'Konfidenz':>10s}", flush=True)
    basis_rate = None
    for name in ("V4 Stand Runde 1", "V5 + regime_profil", "V6 + trigger", "V7 beide"):
        acts = zaehler.get(name, [])
        if not acts:
            continue
        er = sum(1 for a in acts if a in ("ERÖFFNEN", "EROEFFNEN")) / len(acts)
        ha = sum(1 for a in acts if a == "HALTEN") / len(acts)
        k = statistics.fmean(konf[name]) if konf.get(name) else float("nan")
        if basis_rate is None:
            basis_rate = er
        marke = ""
        if name != "V4 Stand Runde 1":
            delta = (er - basis_rate) * 100
            marke = f"   {delta:+.0f} pp"
            if delta <= -20:
                marke += "  <-- TRAEGT das HALTEN"
        print(f"{name:24s} {len(acts):4d} {er*100:9.0f}% {ha*100:7.0f}% "
              f"{k:9.1f}{marke}", flush=True)
    print(flush=True)
    print("Bleibt auch hier alles bei ~100 %, liegt die Zurueckhaltung NICHT im",
          flush=True)
    print("Faktensatz - dann ist der naechste Ort das Gate oder etwas, das",
          flush=True)
    print("dieser Aufbau strukturell nicht abbildet.", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
