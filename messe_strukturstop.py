"""Trägt die Struktur den Stop? (17.08.2026)

DIE FRAGE. `entscheidungsrechnung._stop_abstand` kennt zwei Quellen: den
Widerlegungspreis des Modells und den Rauschboden aus ATR. Die Marken unter
dem Kurs - die Unterstuetzungen, die `lagebeschreibung.niveaus_werte`
liefert - sieht sie NIE. Der eigene Docstring zitiert die strukturbasierte
Schule ("unter das letzte Swing-Tief") und baut sie nicht.

WAS HIER GEMESSEN WIRD, ist NICHT, ob ein Strukturstop besser handelt - das
waere eine Prognose, und dieses Projekt hat gelernt, dass kein Verfahren die
Basisrate schlaegt. Gemessen wird ausschliesslich, was sich an den ZAHLEN
aendert, die heute schon in der Mail stehen:

    Stopabstand  ->  Hebelfaktor  ->  Liquidationsabstand  ->  Breakeven

Das sind Rechnungen, keine Vorhersagen.

BEIDE RICHTUNGEN. Bei LONG traegt die Unterstuetzung den Stop, bei SHORT der
Widerstand - die Rollen tauschen vollstaendig. Ob der Code das spiegelt, ist
bisher ungeprueft, also wird beides gerechnet.

    python messe_strukturstop.py [--db PFAD]
"""
from __future__ import annotations

import argparse
import statistics as stat
import sys

import numpy as np

from agent import entscheidungsrechnung as ER
from agent import lagebeschreibung as LB
from agent.schreibweise import de
from simuliere_kette import _kopie

# Der Puffer UNTER die Marke. Dieselbe Breite, die die Zielrechnung VOR den
# Widerstand legt (`GRENZEN["zone_atr"]`) - keine neue Groesse erfinden.
PUFFER_ATR = ER.GRENZEN["zone_atr"]


def _atr(h, l, c, fenster: int = 14) -> float:
    tr = np.maximum(h[1:] - l[1:],
                    np.maximum(abs(h[1:] - c[:-1]), abs(l[1:] - c[:-1])))
    return float(np.mean(tr[-fenster:])) if len(tr) >= fenster else 0.0


def _messe(symbol: str, kerzen: list) -> dict | None:
    if len(kerzen) < 60:
        return None
    c = np.array([float(k.close) for k in kerzen])
    h = np.array([float(k.high) for k in kerzen])
    l = np.array([float(k.low) for k in kerzen])
    atr = _atr(h, l, c)
    kurs = float(c[-1])
    if atr <= 0 or kurs <= 0:
        return None
    werte = LB.niveaus_werte(c, h, l, len(c) - 1, atr, kurs, kurs)
    aus = {"symbol": symbol, "kurs": kurs, "atr": atr}
    for richtung, ist_short, schluessel in (("long", False, "unterstuetzung"),
                                            ("short", True, "widerstand")):
        # ⚠️ DIE RICHTIGE BASISLINIE IST DIE KLEMME, NICHT DER ATR-STOP.
        #
        # Meine erste Fassung verglich gegen `_stop_aus_atr` (2,5 ATR) -
        # den Zweig, der greift, wenn das Modell NICHTS liefert. Am echten
        # Lauf nachgesehen liefert es aber IMMER etwas (12 von 12), und in
        # 10 von 12 Faellen liegt der Wert im Rauschen und wird auf
        # RM-1b/1c gehoben. Der Stop, den die Produktion wirklich setzt,
        # ist also die Klemme: max(2,5 % Kurs, 0,75 ATR).
        klemme = max(ER.GRENZEN["stop_min_relativ"] * kurs,
                     ER.GRENZEN["stop_min_atr"] * atr)
        heute, regel = klemme, "Widerlegungspreis lag im Rauschen - RM-1b/1c"
        atr_stop = ER._stop_aus_atr(kurs, atr)[0]
        marke = werte.get(schluessel)
        eintrag = {"heute": heute, "heute_regel": regel,
                   "atr_stop": atr_stop, "marke": None}
        if marke:
            preis = float(marke["preis_eur"])
            # Der Stop liegt JENSEITS der Marke, nicht darauf: bei LONG
            # darunter, bei SHORT darueber. Wer genau auf die Marke geht,
            # wird von jedem Test der Marke ausgestoppt.
            roh = ((preis - kurs) + PUFFER_ATR * atr if ist_short
                   else (kurs - preis) + PUFFER_ATR * atr)
            geklemmt = max(roh, ER.GRENZEN["stop_min_relativ"] * kurs,
                           ER.GRENZEN["stop_min_atr"] * atr)
            geklemmt = min(geklemmt, ER.GRENZEN["stop_max_relativ"] * kurs)
            eintrag["marke"] = {
                "preis": preis,
                "beruehrungen": int(marke.get("beruehrungen") or 0),
                "abstand_atr": float(marke.get("abstand_atr") or 0.0),
                "roh": roh, "struktur": geklemmt,
                "geklemmt_unten": geklemmt > roh + 1e-12,
                "geklemmt_oben": geklemmt < roh - 1e-12,
            }
        aus[richtung] = eintrag
    return aus


def _kennzahlen(stop_rel: float, risiko_eur: float = 25.0,
                betrag_eur: float = 500.0) -> dict:
    """Was am Stopabstand haengt - alles Rechnung, keine Prognose."""
    from agent.krypto.hebel_risk_gate import max_safe_hebel

    noetig = risiko_eur / (betrag_eur * stop_rel)
    sicher = max_safe_hebel(100 * stop_rel, ER.GRENZEN["liquidations_marge"])
    hebel = max(1.0, min(noetig, sicher, ER.GRENZEN["hebel_max"]))
    # Breakeven-Trefferquote bei CRV 2,0 und 3 % Kosten auf den Einsatz,
    # ausgedrueckt in R: Kosten/Risiko = 0,03 / stop_rel.
    kosten_r = 0.03 / stop_rel
    breakeven = (1 + kosten_r) / (1 + ER.GRENZEN["crv"])
    return {"hebel": hebel, "sicher": sicher, "kosten_r": kosten_r,
            "breakeven": breakeven}


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--db", default="data/tradinginfotool.db")
    a = p.parse_args()
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    from backtest_llm1_historisch import lade_reihen_aus_db

    db = _kopie(a.db)
    reihen = lade_reihen_aus_db(db)
    faelle = [m for m in (_messe(s, k) for s, k in sorted(reihen.items()))
              if m]
    print("=" * 76)
    print("TRAEGT DIE STRUKTUR DEN STOP?")
    print("=" * 76)
    print(f"{len(faelle)} Symbole mit ausreichender Reihe\n")

    for richtung, wort in (("long", "LONG - der Stop liegt unter der "
                                    "Unterstuetzung"),
                           ("short", "SHORT - der Stop liegt ueber dem "
                                     "Widerstand")):
        mit = [f for f in faelle if f[richtung]["marke"]]
        print("-" * 76)
        print(f"{wort}")
        print("-" * 76)
        print(f"  Marke vorhanden            {len(mit)} von {len(faelle)}")
        if not mit:
            continue
        roh = [f[richtung]["marke"]["roh"] / f["atr"] for f in mit]
        print(f"  Rohabstand zur Marke       Median {de(stat.median(roh), 2)} "
              f"ATR   Spanne {de(min(roh), 2)} bis {de(max(roh), 2)}")
        u = sum(1 for f in mit if f[richtung]["marke"]["geklemmt_unten"])
        o = sum(1 for f in mit if f[richtung]["marke"]["geklemmt_oben"])
        print(f"  davon vom Rauschboden angehoben  {u}   "
              f"von der Obergrenze gekappt  {o}")

        weiter = enger = gleich = 0
        verh, hebel_alt, hebel_neu, be_alt, be_neu = [], [], [], [], []
        for f in mit:
            h, s = f[richtung]["heute"], f[richtung]["marke"]["struktur"]
            verh.append(s / h)
            if s > h * 1.02:
                weiter += 1
            elif s < h * 0.98:
                enger += 1
            else:
                gleich += 1
            ka = _kennzahlen(h / f["kurs"])
            kn = _kennzahlen(s / f["kurs"])
            hebel_alt.append(ka["hebel"])
            hebel_neu.append(kn["hebel"])
            be_alt.append(ka["breakeven"])
            be_neu.append(kn["breakeven"])
        print(f"\n  gegen den heutigen Stop (Klemme RM-1b/1c):")
        print(f"    weiter {weiter}   enger {enger}   praktisch gleich "
              f"{gleich}")
        print(f"    Verhaeltnis Struktur/heute  Median "
              f"{de(stat.median(verh), 2)}x")
        print(f"\n  was daran haengt (Risiko 25 EUR, Betrag 500 EUR, CRV 2,0, "
              f"Kosten 3 %):")
        print(f"    Hebel      heute Median {de(stat.median(hebel_alt), 1)}   "
              f"mit Struktur {de(stat.median(hebel_neu), 1)}")
        print(f"    Breakeven  heute Median "
              f"{de(100 * stat.median(be_alt), 1)} %   "
              f"mit Struktur {de(100 * stat.median(be_neu), 1)} %")
        print(f"    (Basisrate bei CRV 2,0: {de(100 / 3, 1)} %)")

    # ---- WAS DER HEBEL DAZU SAGT ----
    # Ein weiterer Stop senkt den noetigen Hebel. Faellt er unter 1,0, ist
    # das Signal kein Hebelgeschaeft mehr - `rechne()` stuft es dann als
    # SPOT ein. Das ist die einzige Nebenwirkung, die eine Kategorie
    # wechselt, und sie gehoert vor die Entscheidung.
    print()
    print("=" * 76)
    print("FOLGE FUER DEN HEBEL (Risiko 25 EUR, Betrag 500 EUR)")
    print("=" * 76)
    from agent.krypto.hebel_risk_gate import max_safe_hebel
    for richtung in ("long", "short"):
        mit = [f for f in faelle if f[richtung]["marke"]]
        raus = 0
        for f in mit:
            s = f[richtung]["marke"]["struktur"] / f["kurs"]
            if 25.0 / (500.0 * s) < 1.0:
                raus += 1
        alt_raus = sum(1 for f in mit
                       if 25.0 / (500.0 * (f[richtung]["heute"] / f["kurs"]))
                       < 1.0)
        print(f"  {richtung:6} faellt unter Hebel 1,0 (wird SPOT):  "
              f"heute {alt_raus} -> mit Struktur {raus} von {len(mit)}")

    # ---- VARIANTE B: DAS WEITERE VON BEIDEN ----
    # Nicht ersetzen, sondern einen dritten Boden einziehen. Die Klemme ist
    # schon einer ("nie enger als das Rauschen"); die Struktur waere der
    # zweite ("nie enger als die naechste Marke"). Damit kann der Stop nie
    # ENGER werden als heute - eine Aenderung, die in eine Richtung nicht
    # schaden kann, braucht keine Prognose als Rechtfertigung.
    print()
    print("=" * 76)
    print("VARIANTE B - STRUKTUR ALS ZUSAETZLICHER BODEN")
    print("=" * 76)
    for richtung in ("long", "short"):
        mit = [f for f in faelle if f[richtung]["marke"]]
        enger = sum(1 for f in mit
                    if max(f[richtung]["heute"],
                           f[richtung]["marke"]["struktur"])
                    < f[richtung]["heute"] - 1e-12)
        be = [(1 + 0.03 / (max(f[richtung]["heute"],
                              f[richtung]["marke"]["struktur"]) / f["kurs"]))
              / 3 for f in mit]
        print(f"  {richtung:6} jemals ENGER als heute: {enger}   "
              f"Breakeven Median {de(100 * stat.median(be), 1)} %")

    # DIE SPIEGELUNG SELBST. Sie ist der Punkt, an dem ein Vorzeichenfehler
    # unsichtbar bliebe: beide Richtungen muessen eine Marke auf der
    # RICHTIGEN Seite des Kurses benutzen.
    print("\n" + "=" * 76)
    print("SPIEGELUNG LONG/SHORT")
    print("=" * 76)
    falsch = []
    for f in faelle:
        ml = f["long"]["marke"]
        ms = f["short"]["marke"]
        if ml and ml["preis"] >= f["kurs"]:
            falsch.append(f"{f['symbol']}: LONG-Stopmarke liegt NICHT unter "
                          f"dem Kurs")
        if ms and ms["preis"] <= f["kurs"]:
            falsch.append(f"{f['symbol']}: SHORT-Stopmarke liegt NICHT ueber "
                          f"dem Kurs")
    print(f"  Marken auf der falschen Seite: {len(falsch)}")
    for z in falsch[:8]:
        print(f"    {z}")

    # WIE OFT GAEBE ES UEBERHAUPT KEINE STRUKTUR? Ein Verfahren, das in der
    # Haelfte der Faelle nicht greift, braucht einen Rueckfall - und der ist
    # dann die eigentliche Regel.
    print("\n" + "=" * 76)
    print("WIE OFT GREIFT ES NICHT")
    print("=" * 76)
    for richtung in ("long", "short"):
        ohne = [f["symbol"] for f in faelle if not f[richtung]["marke"]]
        print(f"  {richtung:6} ohne Marke: {len(ohne)} von {len(faelle)}"
              + (f"   {', '.join(ohne[:8])}" if ohne else ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
