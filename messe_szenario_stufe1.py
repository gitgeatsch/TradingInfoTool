"""Stufe 1: schlaegt der Szenario-Schaetzer die Grundlinien - und sind sich
die Modelle einiger als vorher?

DIE ENTSCHEIDUNGSREGEL STEHT VOR DEM LAUF FEST und wird danach nicht
verhandelt:

    Der Umbau wird ausgerollt, wenn sein Brier-Score BESSER (kleiner) ist als
    der der Basisraten-Grundlinie. Ist er das nicht, wird er nicht ausgerollt -
    unabhaengig davon, wie plausibel die Begruendungen klingen.

WARUM DIE BASISRATE DIE RICHTIGE GRUNDLINIE IST. Sie sagt bei jedem Fall
dasselbe: die historische Haeufigkeit der drei Ausgaenge. Sie hat keinerlei
Information ueber den Einzelfall. Ein Schaetzer, der sie nicht schlaegt, hat
nichts beigetragen - er hat nur die Statistik nachgeplappert. In der
Prognosebewertung heisst diese Grundlinie "Klimatologie", und sie zu schlagen
ist die Mindestanforderung, nicht der Erfolg.

Dazu zwei weitere Grundlinien, damit die Latte nicht zu niedrig haengt:
`immer_keines` (der haeufigste Einzelausgang) und eine einfache Regel aus dem
Abstand zum EMA-200.

DIE ZWEITE FRAGE, Nutzer-Hypothese vom 10.08.: *"wenn wir das gut machen
sollten auch die LLM Abweichungen geringer werden"*. Das ist pruefbar und wird
mitgemessen - die mittlere paarweise Abweichung der Verteilungen zwischen den
Anbietern auf DENSELBEN Ankern. Eine gut gestellte Aufgabe sollte die Modelle
naeher zusammenbringen; eine schlecht gestellte laesst Raum fuer Modelllaunen.

KEINE ZIRKULARITAET: die Zonen sind deterministisch vorgegeben, die Wahrheit
kommt aus der Kursreihe. Weder Modell noch Empfehlung beeinflussen den
Massstab.

    python messe_szenario_stufe1.py --anker 30 --anbieter gemini35,openrouter,zai
"""
from __future__ import annotations

import argparse
import json
import os
import pathlib
import statistics
import sys
import time
from collections import Counter, defaultdict

import numpy as np

import agent.szenario_analyst as SA
import messe_regimephasen_llm as M
from agent.szenario_fakten import (AUSGAENGE, HORIZONT_KERZEN,
                                   baue_szenario_fakten, baue_zonen, brier,
                                   _perzentil, enthaelt_werturteile,
                                   finde_konstanten, loese_auf)
from backtest_llm1_historisch import lade_reihen
from indicators.calculations import atr_wilder, latest_value, rsi
from messe_umbau_wirkung import verschraenke_phasen

SCHLUESSEL = ("ziel_zuerst_pct", "stop_zuerst_pct", "keines_pct")


def baue_client(name: str):
    """Ein Client je Anbieter - mit dem Modell, das wir tatsaechlich messen."""
    import config as config_module
    config_module.load_env()
    if name == "gemini31":
        from api.gemini import GeminiClient
        return GeminiClient(os.environ["GEMINI_API_KEY"]), "gemini-3.1-flash-lite"
    if name == "gemini35":
        from api.gemini import GeminiClient
        return GeminiClient(os.environ["GEMINI_API_KEY"]), "gemini-3.5-flash-lite"
    if name == "openrouter":
        from api.openrouter import OpenRouterClient
        return OpenRouterClient(os.environ["OPENROUTER_API_KEY"]), None
    if name == "zai":
        from api.zai import ZaiClient
        return ZaiClient(api_key=os.environ["ZAI_API_KEY"]), None
    raise ValueError(f"unbekannter Anbieter {name}")


def _fakten_fuer(sym, reihe, i, richtung, klasse="krypto"):
    closes = np.array([k.close for k in reihe[: i + 1]], dtype=float)
    highs = np.array([k.high for k in reihe[: i + 1]], dtype=float)
    lows = np.array([k.low for k in reihe[: i + 1]], dtype=float)
    if len(closes) < 60:
        return None, None
    atr_reihe = atr_wilder(highs, lows, closes)
    a = latest_value(atr_reihe)
    if not a or a <= 0:
        return None, None
    # ATR-PERZENTIL (Fund des Konstanten-Waechters, 10.08.): das Feld stand auf
    # allen 80 Faellen None - ein Platz im Prompt ohne Inhalt. Die Historie lag
    # die ganze Zeit vor, `atr_wilder` gibt die volle Reihe zurueck und nicht
    # nur den letzten Wert. Es war nie eine fehlende Datenquelle, nur ein nicht
    # ausgelesenes Feld.
    atr_hist = [float(v) for v in np.asarray(atr_reihe.value, dtype=float)[-250:]
                if v == v]
    r = latest_value(rsi(closes))
    # ECHTE RSI-Historie (Korrektur 10.08.): hier standen die SCHLUSSKURSE,
    # womit das "Perzentil" nur noch verglich, ob der Kurs ueber 100 liegt -
    # eine Konstante je Asset. Jetzt wird der RSI ueber ein gleitendes Fenster
    # nachgerechnet.
    rsi_hist = []
    for ende in range(max(60, len(closes) - 250), len(closes)):
        v = latest_value(rsi(closes[: ende + 1]))
        if v is not None:
            rsi_hist.append(float(v))
    f = baue_szenario_fakten(
        symbol=sym, assetklasse=klasse, kurs=float(closes[-1]), atr=float(a),
        richtung=richtung, rsi=r,
        # SMA, nicht EMA - der Name sagt jetzt, was es ist.
        sma={"200": float(closes[-200:].mean())} if len(closes) >= 200 else
            {"50": float(closes[-50:].mean())},
        konfluenz=None,
        atr_relativ_prozent=round(100.0 * a / closes[-1], 2),
        atr_perzentil=_perzentil(atr_hist, float(a)),
        rsi_historie=rsi_hist,
    )
    return f, baue_zonen(float(closes[-1]), float(a), richtung)


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--anker", type=int, default=30)
    p.add_argument("--je-symbol", type=int, default=3)
    p.add_argument("--anbieter", default="gemini35,openrouter,zai")
    p.add_argument("--pause", type=float, default=0.3)
    p.add_argument("--trocken", action="store_true")
    p.add_argument("--ausgabe", default="szenario_stufe1.json")
    args = p.parse_args()
    anbieter = [a.strip() for a in args.anbieter.split(",") if a.strip()]

    reihen = lade_reihen()
    btc = reihen["BTC"]
    fest = M.stabile_tage(M.btc_phasen(btc))
    je_phase = M.waehle_anker(reihen, fest, args.anker, args.je_symbol)
    anker = verschraenke_phasen(je_phase, M.ARME, M.LABEL, reihen, args.anker)

    # Jeder Anker in BEIDE Richtungen - sonst misst man die Marktrichtung mit,
    # nicht die Schaetzguete. Bei symmetrischen Zonen ist das der einzige Weg,
    # LONG- und SHORT-Aufbauten fair zu vergleichen.
    faelle = []
    for phase, label, sym, i in anker:
        for richtung in ("LONG", "SHORT"):
            f, zonen = _fakten_fuer(sym, reihen[sym], i, richtung)
            if f is None:
                continue
            wahrheit = loese_auf(reihen[sym], i, zonen)
            if wahrheit is None:
                continue
            urteile = enthaelt_werturteile(f)
            if urteile:
                print(f"[FEHLER] Werturteil im Faktensatz: {urteile}")
                return 2
            faelle.append({"symbol": sym, "datum": reihen[sym][i].date,
                           "phase": phase, "richtung": richtung,
                           "fakten": f, "wahrheit": wahrheit})

    # VOR den Modellaufrufen, nicht danach: ein Feld, das ueber alle Faelle
    # denselben Wert traegt, macht den ganzen Lauf wertlos - und das Kontingent
    # kommt nicht zurueck. Kein Abbruch, weil eine Konstante auch harmlos sein
    # kann; aber sie steht dann im Protokoll und nicht in der Rueckschau.
    konstanten = finde_konstanten([f["fakten"] for f in faelle])
    if konstanten:
        print("\n[WARNUNG] Felder mit demselben Wert ueber ALLE Faelle:")
        for k in konstanten:
            print(f"  {k}")
        print("  Ein konstantes Feld sieht nach Information aus, ist aber")
        print("  keine - und wenn es eine Richtung nahelegt, schiebt es JEDE")
        print("  Antwort in dieselbe. Pruefen, bevor das Ergebnis zaehlt.")

    print(f"Anker {len(anker)}, {len({a[2] for a in anker})} Symbole")
    print(f"Faelle (2 Richtungen je Anker): {len(faelle)}")
    verteilung = Counter(x["wahrheit"] for x in faelle)
    print(f"Tatsaechliche Ausgaenge: {dict(verteilung)}")
    if len(faelle) < 20:
        print("[FEHLER] zu wenige auswertbare Faelle - ABBRUCH.")
        return 2

    # --- Grundlinien, aus denselben Faellen ---------------------------------
    n = len(faelle)
    basisrate = {s: 100.0 * verteilung.get(a, 0) / n
                 for a, s in zip(AUSGAENGE, SCHLUESSEL)}
    print(f"\nBasisrate (Klimatologie): "
          + ", ".join(f"{k}={v:.1f}" for k, v in basisrate.items()))

    def grundlinie_regel(fall):
        """Abstand zum gleitenden Durchschnitt in ATR - die beste einfache
        Regel aus der Nullmessung (Kurs vs Durchschnitt traf 62 %).

        SUCHT ALLE VARIANTEN, nicht einen festen Namen. Beim Umbenennen von
        `ema_200` auf `sma_200` haette ein fester Schluessel ins Leere
        gegriffen, waere stillschweigend auf die Basisrate zurueckgefallen -
        und die Grundlinie haette sich selbst geschlagen, ohne dass es
        auffaellt. Faellt gar nichts, wird das GEZAEHLT statt verschwiegen."""
        ab = ((fall["fakten"].get("technik") or {}).get("abstand_in_atr") or {})
        d = next((ab[k] for k in ("sma_200", "ema_200", "sma_50", "ema_50")
                  if ab.get(k) is not None), None)
        if d is None:
            grundlinie_regel.ohne_wert += 1
            return dict(basisrate)
        pro = (d > 0) == (fall["richtung"] == "LONG")
        return ({"ziel_zuerst_pct": 45, "stop_zuerst_pct": 25, "keines_pct": 30}
                if pro else
                {"ziel_zuerst_pct": 25, "stop_zuerst_pct": 45, "keines_pct": 30})

    grundlinie_regel.ohne_wert = 0

    haeufigster = max(AUSGAENGE, key=lambda a: verteilung.get(a, 0))
    grundlinien = {
        "Basisrate (Klimatologie)": lambda f: dict(basisrate),
        f"immer '{haeufigster}'": lambda f: {
            s: (100.0 if a == haeufigster else 0.0)
            for a, s in zip(AUSGAENGE, SCHLUESSEL)},
        "Regel: Abstand zum Schnitt": grundlinie_regel,
    }
    ergebnisse: dict[str, list] = defaultdict(list)
    for name, fn in grundlinien.items():
        for fall in faelle:
            ergebnisse[name].append(
                {"brier": brier(fn(fall), fall["wahrheit"]), "verteilung": fn(fall)})

    if args.trocken:
        print("\n--- TROCKEN: nur Grundlinien ---")
        for name in grundlinien:
            w = [e["brier"] for e in ergebnisse[name] if e["brier"] is not None]
            print(f"  {name:28s} Brier {statistics.fmean(w):.4f}  (n={len(w)})")
        print("\nKeine LLM-Aufrufe.")
        return 0

    def sichere(stand: str) -> None:
        """Zwischenstand wegschreiben - nach JEDEM Anbieter, nicht am Ende.

        DER GRUND (10.08., am eigenen Lauf gemerkt): die Datei entstand erst
        nach dem letzten Anbieter. Als Z.ai mit 120 s je Fall zwei Stunden
        brauchte, haette ein Abbruch nicht nur Z.ai verworfen, sondern auch
        die 160 fertigen Messpunkte von Gemini und OpenRouter - 25 Minuten
        Laufzeit und 165 Aufrufe.

        Dieselbe Bauweise hat schon am 09.08. zwei abgebrochene Laeufe ohne
        verwertbare Datei enden lassen. Ein Ergebnis, das erst ganz am Schluss
        materialisiert, ist bei jedem Abbruch weg."""
        pathlib.Path(args.ausgabe).write_text(
            json.dumps({"stand": stand,
                        "faelle": [{k: v for k, v in f.items() if k != "fakten"}
                                   for f in faelle],
                        "ergebnisse": {k: v for k, v in ergebnisse.items()},
                        "basisrate": basisrate},
                       ensure_ascii=False, indent=1), encoding="utf-8")

    sichere("nur Grundlinien")

    # --- Die Anbieter -------------------------------------------------------
    from agent import llm_schema
    for a_name in anbieter:
        client, modell = baue_client(a_name)
        fmt = llm_schema.response_format_fuer(client, "agent.szenario_analyst")
        print(f"\n--- {a_name} ({modell or 'Vorgabemodell'}), "
              f"Format {fmt.get('type')} ---")
        fehler: Counter = Counter()
        beginn = time.time()
        for nr, fall in enumerate(faelle, 1):
            zusatz = {"model": modell} if modell else {}
            antwort = None
            for _ in range(3):
                time.sleep(args.pause)
                try:
                    roh = client.chat(
                        [{"role": "system", "content": SA.SYSTEM_PROMPT},
                         {"role": "user",
                          "content": json.dumps(fall["fakten"], ensure_ascii=False)}],
                        temperature=0.2, response_format=fmt, **zusatz)
                    antwort = SA._validate_szenario(json.loads(roh), fall["symbol"])
                    break
                except Exception as exc:  # noqa: BLE001
                    fehler[type(exc).__name__] += 1
            if antwort is None:
                ergebnisse[a_name].append({"brier": None, "verteilung": None})
                continue
            ergebnisse[a_name].append(
                {"brier": brier(antwort["szenarien"], fall["wahrheit"]),
                 "verteilung": antwort["szenarien"],
                 "unsicherheit": antwort.get("unsicherheit")})
            if nr % 10 == 0 or nr == len(faelle):
                je = (time.time() - beginn) / max(1, nr)
                gueltig = [e["brier"] for e in ergebnisse[a_name]
                           if e["brier"] is not None]
                print(f"  {nr:3}/{len(faelle)}  gueltig {len(gueltig)}  "
                      f"Brier {statistics.fmean(gueltig):.4f}  "
                      f"Fehler {sum(fehler.values())}  {je:.1f} s")
        if fehler:
            print(f"  Fehler: {dict(fehler)}")
        sichere(f"bis einschliesslich {a_name}")
        print(f"  Zwischenstand gesichert: {args.ausgabe}")

    # --- Auswertung ---------------------------------------------------------
    print("\n" + "=" * 74)
    print(f"{'Verfahren':30} {'Brier':>9} {'gueltig':>9} {'besser als Basisrate':>22}")
    print("-" * 74)
    basis_w = statistics.fmean([e["brier"] for e in ergebnisse["Basisrate (Klimatologie)"]])
    zeilen = list(grundlinien) + anbieter
    werte = {}
    for name in zeilen:
        w = [e["brier"] for e in ergebnisse[name] if e["brier"] is not None]
        if not w:
            print(f"{name:30} {'-':>9} {0:>9}")
            continue
        m = statistics.fmean(w)
        werte[name] = m
        besser = "JA" if m < basis_w else "nein"
        print(f"{name:30} {m:9.4f} {len(w):9d} {besser:>22}")

    print("\n=== EINIGKEIT DER MODELLE (Nutzer-Hypothese) ===")
    paare = [(a, b) for i, a in enumerate(anbieter) for b in anbieter[i + 1:]]
    for a, b in paare:
        abw = []
        for ea, eb in zip(ergebnisse[a], ergebnisse[b]):
            if ea["verteilung"] and eb["verteilung"]:
                abw.append(statistics.fmean(
                    abs(ea["verteilung"][s] - eb["verteilung"][s]) for s in SCHLUESSEL))
        if abw:
            print(f"  {a} gegen {b}: mittlere Abweichung "
                  f"{statistics.fmean(abw):.1f} Prozentpunkte ueber {len(abw)} Faelle")

    print("\n=== URTEIL nach der vorab festgelegten Regel ===")
    beste = min((k for k in anbieter if k in werte), key=lambda k: werte[k], default=None)
    if beste is None:
        print("  Kein Anbieter lieferte auswertbare Verteilungen.")
    elif werte[beste] < basis_w:
        print(f"  {beste} schlaegt die Basisrate ({werte[beste]:.4f} gegen "
              f"{basis_w:.4f}) -> der Umbau traegt.")
    else:
        print(f"  KEIN Anbieter schlaegt die Basisrate (bester {beste} mit "
              f"{werte[beste]:.4f} gegen {basis_w:.4f}) -> NICHT ausrollen. "
              f"Die Schaetzung traegt keine Information ueber den Einzelfall.")

    sichere("vollstaendig")
    print(f"\nGeschrieben: {args.ausgabe}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
