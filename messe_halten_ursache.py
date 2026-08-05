"""Welcher Fakt traegt das HALTEN? (2026-08-05, Punkt 1)

DIE FRAGE. Im Betrieb sagt LLM1 zu 65 % HALTEN. Im historischen Backtest mit
rein kursbasierten Fakten eroeffnete es in 36 von 36 Faellen. Die Anreicherung
um Konfluenz, Fibonacci, Liquiditaetszonen und BTC-Relativwert aenderte daran
NICHTS - die Rate blieb bei 100 %. Die Zurueckhaltung muss also aus den
Fakten kommen, die bis gestern nicht rekonstruierbar waren.

Seit dem 05.08. liegen sie vor: `macro_historie` (30 Tage, mit Regime,
Fear&Greed, BTC-Dominanz, Zyklus-Risiko, VIX, Dollar-Index) und `oi_historie`
(97.625 Zeilen, 39 Symbole, Funding-Rate/Open Interest/Long-Konten-Anteil).

DAS VERFAHREN IST EIN ABLATIONSEXPERIMENT, kein Vergleich von Korrelationen.
Derselbe Ankerpunkt wird mehrfach gefragt - einmal mit dem duennen Faktensatz,
dann mit je EINEM zusaetzlichen Block. Was die Eroeffnungsrate senkt, traegt
das HALTEN. Das ist eine Ursache, keine Begleiterscheinung.

    V0  nur Kurs-/Technikfakten        (Basislinie, erwartet ~100 % EROEFFNEN)
    V1  + Regime                        (regime.wert, btc_trend, regime_reason)
    V2  + Funding-Rate / Open Interest  (aus oi_historie)
    V3  + Fear&Greed / Zyklus-Risiko
    V4  alles zusammen                  (naeher am Betrieb)

KEIN BEWERTUNGSFENSTER NOETIG - und das erweitert die Datenbasis erheblich.
Gemessen wird die ENTSCHEIDUNG, nicht ihr Ausgang; es braucht also keine 14
Tage Zukunft je Ankerpunkt. Nutzbar ist damit die volle Ueberlappung von
macro_historie und oi_historie (14.07. bis 05.08.) statt nur acht Tage.

KEIN VORAUSSCHAUEN trotzdem: Kursreihe, Makrozeile und OI-Zeilen werden hart
am Ankertag abgeschnitten. Der Ausgang interessiert hier zwar nicht, aber ein
Faktensatz mit Zukunftswissen waere auch fuer eine Entscheidungsfrage falsch.

Lauf: python -u messe_halten_ursache.py [--n 8] [--w 3]
"""
from __future__ import annotations

import io
import json
import math
import os
import statistics
import sys
from collections import defaultdict

import numpy as np

from agent.krypto.hebel_analyst import SYSTEM_PROMPT
from api.mistral import MistralClient
from backtest_llm1_historisch import (
    VORLAUF_MIN, Kerze, _arg, baue_historische_fakten, frage, lade_reihen,
)

ORDNER = r"K:\My Drive\Claude_Austauschordner\Notebook_Analysedaten"


def lade_zusatzfakten():
    d = json.load(io.open(ORDNER + r"\notebook_diagnose.json", encoding="utf-8"))
    r = d["rohdaten_fuer_backtest"]
    makro = {x["date"]: x for x in r["macro_historie"] if x.get("date")}
    # OI je (Symbol, Tag) verdichten - mehrere Boersen und mehrere Abrufe je Tag
    oi: dict[tuple, dict] = defaultdict(lambda: {"fr": [], "oi": [], "long": []})
    for x in r["oi_historie"]:
        tag = str(x.get("fetched_at") or "")[:10]
        if not tag or not x.get("symbol"):
            continue
        e = oi[(x["symbol"], tag)]
        for feld, schluessel in (("funding_rate", "fr"), ("open_interest_usd", "oi"),
                                 ("long_account_pct", "long")):
            v = x.get(feld)
            if isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v):
                e[schluessel].append(float(v))
    return makro, dict(oi)


def block_regime(makro_zeile: dict) -> dict:
    return {"regime": {
        "wert": "aus regime_reason abgeleitet",
        "quelle": "macro_snapshot (historisch)",
        "begruendung": makro_zeile.get("regime_reason"),
        "btc_trend": makro_zeile.get("btc_trend_label"),
        "btc_dominanz_prozent": makro_zeile.get("btc_dominance_pct"),
        "liquiditaets_regime": makro_zeile.get("liquiditaets_regime"),
        "dollar_index": {"wert": makro_zeile.get("dollar_index_wert"),
                         "trend": makro_zeile.get("dollar_index_trend")},
    }}


def block_antizyklisch(oi_zeile: dict | None) -> dict:
    if not oi_zeile:
        return {}
    def med(k):
        v = oi_zeile.get(k) or []
        return round(statistics.median(v), 8) if v else None
    fr = med("fr")
    return {"antizyklisch": {
        "funding_rate_aktuell_prozent_pro_stunde": fr,
        "funding_rate_aktuell_prozent_pro_tag": (round(fr * 24, 8) if fr is not None else None),
        "funding_rate_extrem": (abs(fr) > 0.0005 if fr is not None else None),
        "open_interest_usd": med("oi"),
        "long_konten_anteil_prozent": med("long"),
    }}


def block_stimmung(makro_zeile: dict) -> dict:
    return {"marktstimmung": {
        "fear_greed": {"wert": makro_zeile.get("fear_greed_value"),
                       "einstufung": makro_zeile.get("fear_greed_label")},
        "zyklus_risiko": makro_zeile.get("zyklus_risiko"),
        "vix": makro_zeile.get("vix_wert"),
    }}


def baue(fakten_basis: dict, *bloecke: dict) -> dict:
    """Basis plus Zusatzbloecke, VOR den disclaimers eingehaengt."""
    neu = dict(fakten_basis)
    disc = neu.pop("disclaimers", None)
    for b in bloecke:
        neu.update(b)
    # `nicht_verfuegbar` mitpflegen: was jetzt geliefert wird, darf dort nicht
    # mehr als fehlend stehen - sonst widerspricht sich der Faktensatz.
    nv = set(neu.get("nicht_verfuegbar") or [])
    if "antizyklisch" in neu:
        nv -= {"funding_rate", "open_interest", "long_short_ratio"}
    if "marktstimmung" in neu:
        nv -= {"fear_greed"}
    neu["nicht_verfuegbar"] = sorted(nv)
    if disc is not None:
        neu["disclaimers"] = disc
    return neu


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

    # Ankerpunkte: Symbol muss Kurshistorie UND OI-Daten haben, Tag muss in
    # macro_historie stehen. Ueber Symbole und Tage gestreut.
    anker = []
    for sym, reihe in sorted(reihen.items()):
        if len(reihe) < VORLAUF_MIN + 2:
            continue
        for i in range(VORLAUF_MIN, len(reihe) - 1):
            tag = reihe[i].date
            if tag in makro and (sym, tag) in oi:
                anker.append((sym, i, tag))
    if not anker:
        print("keine Ankerpunkte mit Kurs UND Makro UND OI")
        return 1
    anker.sort(key=lambda x: (x[2], x[0]))
    anker = anker[:: max(1, len(anker) // n)][:n]

    client = MistralClient(api_key=key)
    print("=" * 78, flush=True)
    print(f"WELCHER FAKT TRAEGT DAS HALTEN?   {len(anker)} Ankerpunkte x 5 Varianten"
          f" x {w} = {len(anker)*5*w} Aufrufe", flush=True)
    print(f"Ueberlappungsfenster: {anker[0][2]} .. {anker[-1][2]}", flush=True)
    print("=" * 78, flush=True)

    zaehler: dict[str, list[str]] = defaultdict(list)
    konf: dict[str, list[float]] = defaultdict(list)

    for sym, i, tag in anker:
        basis = baue_historische_fakten(sym, reihen[sym], i, btc)
        if basis is None:
            continue
        mz, oz = makro[tag], oi.get((sym, tag))
        varianten = {
            "V0 nur Kurs/Technik": basis,
            "V1 + Regime": baue(basis, block_regime(mz)),
            "V2 + Funding/OI": baue(basis, block_antizyklisch(oz)),
            "V3 + Fear&Greed": baue(basis, block_stimmung(mz)),
            "V4 alles": baue(basis, block_regime(mz), block_antizyklisch(oz),
                             block_stimmung(mz)),
        }
        print(f"\n{sym} @ {tag}:", flush=True)
        for name, fakten in varianten.items():
            acts = []
            for _ in range(w):
                a = frage(client, fakten, SYSTEM_PROMPT)
                if not a:
                    continue
                act = str(a.get("action", "?")).upper()
                acts.append(act)
                zaehler[name].append(act)
                k = a.get("confidence_pct")
                if isinstance(k, (int, float)):
                    konf[name].append(float(k))
            vert = {x: acts.count(x) for x in sorted(set(acts))}
            print(f"  {name:22s} {vert}", flush=True)

    print("\n" + "=" * 78, flush=True)
    print(f"{'Variante':24s} {'n':>4s} {'EROEFFNEN':>10s} {'HALTEN':>8s} "
          f"{'Konfidenz':>10s}", flush=True)
    basis_rate = None
    for name in ("V0 nur Kurs/Technik", "V1 + Regime", "V2 + Funding/OI",
                 "V3 + Fear&Greed", "V4 alles"):
        acts = zaehler.get(name, [])
        if not acts:
            continue
        er = sum(1 for a in acts if a in ("ERÖFFNEN", "EROEFFNEN")) / len(acts)
        ha = sum(1 for a in acts if a == "HALTEN") / len(acts)
        k = statistics.fmean(konf[name]) if konf.get(name) else float("nan")
        if basis_rate is None:
            basis_rate = er
        marke = ""
        if name != "V0 nur Kurs/Technik" and basis_rate is not None:
            delta = (er - basis_rate) * 100
            marke = f"   {delta:+.0f} pp gegen V0"
            if delta <= -20:
                marke += "  <-- TRAEGT das HALTEN"
        print(f"{name:24s} {len(acts):4d} {er*100:9.0f}% {ha*100:7.0f}% "
              f"{k:9.1f}{marke}", flush=True)
    print(flush=True)
    print("Lesart: senkt ein Block die Eroeffnungsrate deutlich, traegt ER die", flush=True)
    print("Zurueckhaltung. Bleibt alles bei 100 %, liegt sie NICHT in den Fakten", flush=True)
    print("- dann kommt sie aus dem Gate oder aus Faktoren, die hier fehlen.", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
