"""Wo sitzt der Unterschied - Phase, Asset, oder in der Zahl selbst?
(20.08.2026, Umbauplan 100)

⚠️ DIESER KOPF IST DIE VORABFESTLEGUNG. Er ist geschrieben, BEVOR die erste
Zahl gerechnet wurde. Wer ihn nachtraeglich an ein Ergebnis anpasst, hat sich
ein Ergebnis gesucht - dieselbe Regel wie in Methodik 2.45 und 2.46.

DER ANLASS. Kapitel 99 hat die rechnerische Bremse simuliert: sie blockiert
96 % und hebt die Trefferquote um 0,3 Punkte. In den Aufschluesselungen, die
der Nutzer verlangt hat, standen dagegen Unterschiede von 13 (Marktphase) und
31 Punkten (Asset) - zehnmal mehr als der Filter bewirkt. Beide waren aber
NICHT vorab festgelegt und gelten deshalb als Anlass, nicht als Befund.

DIE DREI FRAGEN, IN DIESER REIHENFOLGE FESTGELEGT:

  H1  MARKTPHASE. Unterscheidet sich die Trefferquote zwischen Bulle,
      Seitwaerts und Baer? Gemessen wird der Abstand Baer minus Bulle.

  H2  ASSET. Unterscheiden sich die Symbole staerker, als der Zufall
      erlaubt? Gemessen wird die Streuung der Symbolquoten gegen die
      Streuung, die bei gleicher Fallzahl rein zufaellig entstuende.

  H3  ZWISCHENSTUFEN - DIE FRAGE DES NUTZERS. *"Wie kann man die harte
      Bewertung traegt sich / traegt sich nicht so skalieren, dass ein
      weicherer Uebergang entsteht und mit Glueck mehr schlechte
      wegfallen?"*

      Eine weiche Schwelle hilft nur, wenn die zugrundeliegende Zahl
      SORTIERT. Gemessen wird deshalb die Trefferquote je Zehntel von `p`.
      Steigt sie monoton, lohnen Zwischenstufen. Ist sie flach, hilft keine
      Schwelle - weder hart noch weich.

WAS ALS BEFUND GILT: |t| ueber der Schwelle, die der Placebo misst. Der
Placebo wuerfelt die Etiketten (Phase, Symbol, Zehntel) neu; was dann noch
anschlaegt, ist der Fehler der Methode. Ohne diesen Lauf gilt nichts.

⚠️ UND EINE WARNUNG VORAB, DIE FUER H2 GILT: Symbole nach ihrer vergangenen
Trefferquote auszuwaehlen ist genau die Falle, die dieses Projekt am 20.08.
schon einmal erwischt hat (Kapitel 93.17: das Momentum-Signal lebte in der
nachgeladenen, auswahlverzerrten Zeit). Ein Unterschied ZWISCHEN Symbolen ist
noch keine Auswahlregel - dafuer muesste er sich vorwaerts wiederholen.

    python messe_konstellationen.py [--instrument spot] [--placebo 40]
"""
from __future__ import annotations

import argparse
import io
import json
import math
import sys

import numpy as np

sys.path.insert(0, ".")
from agent import trefferbilanz as TB                        # noqa: E402
from simuliere_bremse import baue_anker                      # noqa: E402

ZEHNTEL = 10
MIN_JE_GRUPPE = 100


def _quote(faelle) -> tuple[int, float]:
    n = sum(1 for f in faelle if f["ausgang"] in ("ziel", "stop"))
    t = sum(1 for f in faelle if f["ausgang"] == "ziel")
    return n, (t / n if n else 0.0)


def _t_wert(a_n, a_q, b_n, b_q) -> float:
    """Zwei Quoten vergleichen. Standardfehler aus der Binomialverteilung."""
    if a_n < 30 or b_n < 30:
        return 0.0
    se = math.sqrt(a_q * (1 - a_q) / a_n + b_q * (1 - b_q) / b_n)
    return (a_q - b_q) / se if se > 0 else 0.0


def _p_je_anker(faelle: list) -> list:
    """Walk-Forward: `p` fuer jeden Anker aus dem, was davor bekannt war."""
    tabelle: dict = {}
    basis = TB.basisrate_fuer(TB.CRV)
    aus = []
    for f in faelle:
        e = tabelle.get(f["schluessel"]) or {"treffer": 0, "faelle": 0}
        aus.append(TB.geschrumpft(e["treffer"], e["faelle"], basisrate=basis))
        if f["ausgang"] in ("ziel", "stop"):
            e["faelle"] += 1
            e["treffer"] += 1 if f["ausgang"] == "ziel" else 0
            tabelle[f["schluessel"]] = e
    return aus


def messe(faelle: list, p_werte: list, mischen=None) -> dict:
    """Alle drei Fragen auf einmal. `mischen` wuerfelt die Etiketten."""
    phasen = [f["phase"] for f in faelle]
    symbole = [f["symbol"] for f in faelle]
    p = np.array(p_werte)
    if mischen is not None:
        phasen = list(mischen.permutation(phasen))
        symbole = list(mischen.permutation(symbole))
        p = mischen.permutation(p)

    aus: dict = {}

    # H1 - Marktphase.
    je_phase = {}
    for f, ph in zip(faelle, phasen):
        je_phase.setdefault(ph, []).append(f)
    aus["phase"] = {ph: _quote(v) for ph, v in je_phase.items()}
    b, bl = aus["phase"].get("baer", (0, 0.0)), aus["phase"].get("bulle", (0, 0.0))
    aus["t_phase"] = _t_wert(b[0], b[1], bl[0], bl[1])

    # H2 - Asset: Streuung gegen die zufaellig erwartete.
    je_sym = {}
    for f, s in zip(faelle, symbole):
        je_sym.setdefault(s, []).append(f)
    quoten = [(n, q) for n, q in (_quote(v) for v in je_sym.values())
              if n >= MIN_JE_GRUPPE]
    aus["symbole_gewertet"] = len(quoten)
    if len(quoten) >= 5:
        qs = np.array([q for _n, q in quoten])
        ns = np.array([n for n, _q in quoten])
        gesamt = float(np.average(qs, weights=ns))
        # Erwartete Streuung, wenn ALLE dieselbe Quote haetten.
        erwartet = math.sqrt(float(np.mean(
            gesamt * (1 - gesamt) / ns)))
        aus["streuung_ist"] = float(qs.std(ddof=1))
        aus["streuung_zufall"] = erwartet
        aus["streuung_faktor"] = (float(qs.std(ddof=1)) / erwartet
                                  if erwartet > 0 else None)

    # H3 - sortiert die Zahl? Zehntel von p.
    if len(p) == len(faelle):
        ordn = np.argsort(p)
        gross = len(faelle) // ZEHNTEL
        stufen = []
        for k in range(ZEHNTEL):
            teil = [faelle[i] for i in ordn[k * gross:(k + 1) * gross]]
            n, q = _quote(teil)
            stufen.append({"zehntel": k + 1, "n": n, "quote": q,
                           "p_mittel": float(np.mean(
                               [p[i] for i in ordn[k * gross:(k + 1) * gross]]))})
        aus["zehntel"] = stufen
        oben, unten = stufen[-1], stufen[0]
        aus["t_zehntel"] = _t_wert(oben["n"], oben["quote"],
                                   unten["n"], unten["quote"])
    return aus


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="data/tradinginfotool.db")
    ap.add_argument("--klasse", default="krypto")
    ap.add_argument("--instrument", default="spot",
                    choices=("spot", "hebel"))
    ap.add_argument("--placebo", type=int, default=0)
    ap.add_argument("--datei", default="messwerte_konstellationen.json")
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    print("=" * 78)
    print(f"WO SITZT DER UNTERSCHIED? - {a.klasse}/{a.instrument}")
    print("  H1 Marktphase · H2 Asset · H3 sortiert die Zahl ueberhaupt?")
    print("=" * 78)
    faelle = baue_anker(a.db, a.klasse, a.instrument)
    p_werte = _p_je_anker(faelle)
    n_ges, q_ges = _quote(faelle)
    print(f"  {len(faelle)} Anker, {n_ges} entschieden, "
          f"Trefferquote {100 * q_ges:.1f} %")

    r = messe(faelle, p_werte)

    print("\n" + "-" * 78)
    print("H1 - MARKTPHASE")
    print("-" * 78)
    for ph in ("bulle", "seitwaerts", "baer"):
        n, q = r["phase"].get(ph, (0, 0.0))
        print(f"  {ph:12} {n:7} entschieden   {100 * q:5.1f} %")
    print(f"  Abstand Baer minus Bulle: "
          f"{100 * (r['phase'].get('baer', (0, 0))[1] - r['phase'].get('bulle', (0, 0))[1]):+.1f} "
          f"Punkte   t = {r['t_phase']:+.2f}")

    print("\n" + "-" * 78)
    print("H2 - ASSET")
    print("-" * 78)
    if "streuung_faktor" in r:
        print(f"  {r['symbole_gewertet']} Symbole mit mindestens "
              f"{MIN_JE_GRUPPE} entschiedenen Faellen")
        print(f"  Streuung der Symbolquoten: {100 * r['streuung_ist']:.1f} "
              f"Punkte")
        print(f"  bei reinem Zufall erwartet: "
              f"{100 * r['streuung_zufall']:.1f} Punkte")
        print(f"  Faktor: {r['streuung_faktor']:.2f}"
              + ("  - die Symbole unterscheiden sich mehr als zufaellig"
                 if r["streuung_faktor"] > 1.5 else
                 "  - kaum mehr als Zufall"))
    else:
        print("  zu wenige Symbole - KEIN URTEIL")

    print("\n" + "-" * 78)
    print("H3 - SORTIERT DIE ZAHL? (Zehntel von p, aufsteigend)")
    print("  Die Frage des Nutzers: lohnen Zwischenstufen statt der harten")
    print("  Schwelle? Nur wenn die Quote mit p steigt.")
    print("-" * 78)
    for s in r.get("zehntel", []):
        print(f"  {s['zehntel']:2}. Zehntel  p={100 * s['p_mittel']:5.1f} %   "
              f"{s['n']:6} Faelle   Quote {100 * s['quote']:5.1f} %")
    if "t_zehntel" in r:
        print(f"  Abstand oberstes minus unterstes Zehntel: "
              f"{100 * (r['zehntel'][-1]['quote'] - r['zehntel'][0]['quote']):+.1f} "
              f"Punkte   t = {r['t_zehntel']:+.2f}")

    if a.placebo:
        print("\n" + "-" * 78)
        print(f"PLACEBO - {a.placebo} Laeufe mit gewuerfelten Etiketten")
        print("-" * 78)
        rng = np.random.default_rng(20260820)
        hoch = {"phase": [], "zehntel": [], "streuung": []}
        for _ in range(a.placebo):
            z = messe(faelle, p_werte, mischen=rng)
            hoch["phase"].append(abs(z.get("t_phase") or 0.0))
            hoch["zehntel"].append(abs(z.get("t_zehntel") or 0.0))
            if z.get("streuung_faktor"):
                hoch["streuung"].append(z["streuung_faktor"])
        for k in ("phase", "zehntel", "streuung"):
            if not hoch[k]:
                continue
            s = float(np.quantile(hoch[k], 0.95))
            print(f"  {k:10} Schwelle (95 %): {s:5.2f}   "
                  f"groesster Zufallswert {max(hoch[k]):5.2f}")
            r[f"schwelle_{k}"] = s

    print("\n" + "=" * 78)
    for name, wert, schl in (("H1 Marktphase", abs(r.get("t_phase") or 0),
                              r.get("schwelle_phase")),
                             ("H3 Zehntel", abs(r.get("t_zehntel") or 0),
                              r.get("schwelle_zehntel")),
                             ("H2 Asset-Streuung", r.get("streuung_faktor"),
                              r.get("schwelle_streuung"))):
        if wert is None:
            continue
        if schl is None:
            print(f"  {name:20} {wert:5.2f}   (ohne Placebo kein Urteil)")
        else:
            print(f"  {name:20} {wert:5.2f} gegen Schwelle {schl:5.2f}   "
                  + ("TRAEGT" if wert > schl else "nichts"))
    print("=" * 78)
    if a.datei:
        io.open(a.datei, "w", encoding="utf-8").write(
            json.dumps({k: v for k, v in r.items() if k != "phase"},
                       ensure_ascii=False, indent=1, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
