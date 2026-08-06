"""Der Widerspruch 3-5 % gegen 5-8 % beim Stop-Abstand - sauber nachgemessen.

DER WIDERSPRUCH. Zwei Messungen sagen Verschiedenes:
  01.08.  "SL-Abstand < 5 % hat 0-16,7 % Trefferquote, 5-10 % hat 31,2 %"
          -> enge Stops schlecht, mittlere gut. Grundlage: 61 AUFGELOESTE
             Hebel-Trades, Messgroesse Trefferquote.
  06.08.  Band 3-5 % kam auf EW +0,340 R, Band 5-8 % auf -0,438 R
          -> mittlere Stops schlecht. Grundlage: 446 AUFGELOESTE Faelle,
             Messgroesse Erwartungswert.

BEIDE ZAHLEN SIND AUS DEMSELBEN GRUND UNBRAUCHBAR, und es ist der Fehler, den
dieses Projekt schon zweimal gemacht hat: sie werten nur AUFGELOESTE Faelle
aus. Ob ein Signal aufloest, haengt aber vom STOP-ABSTAND ab - genau der
Variablen, um die es hier geht.

  Ein enger Stop wird fast immer getroffen -> das Signal loest schnell auf und
  landet mit -1 R in der Stichprobe.
  Ein weiter Stop wird seltener getroffen -> das Signal bleibt offen und faellt
  aus der Stichprobe HERAUS, auch wenn es spaeter gewonnen haette.

Die Auswahl der Stichprobe haengt also am Messgegenstand. Das ist derselbe
Survivorship-Mechanismus, an dem die CRV-Gate-Messung vom 02.08. gebrochen ist
(widerlegt am 03.08. in bd7aa86) - und ich bin ihm am 06.08. erneut
aufgesessen.

WIE HIER RICHTIG GEMESSEN WIRD:
  1. KEIN Aufloesungs-Filter. Jedes Signal mit Zonen wird gegen die echte
     Preisreihe neu simuliert; wer bis zum Horizont nichts trifft, bekommt
     Mark-to-Market statt aus der Stichprobe zu fallen.
  2. BASISLINIE JE BAND (Methodik 2.5.7, Pflicht). Verglichen wird nicht gegen
     null, sondern gegen einen mechanischen Zufallseinstieg MIT DEMSELBEN
     Stop-Abstand und demselben CRV. Ohne das misst man die Marktphase.
  3. BLOCK-BOOTSTRAP UEBER SYMBOLE. Einzelne Symbole stellen bis zu einem
     Drittel eines Bandes; naive Intervalle waeren zu eng.
  4. GETRENNT NACH RICHTUNG. Der SHORT-Anteil ist seit dem 31.07. von 5 % auf
     ueber 60 % gestiegen - ein Bandvergleich ueber beide Richtungen zusammen
     misst teilweise diese Verschiebung.
  5. ZWEI HORIZONTE (7 und 14 Tage), weil die Bandbreite der Stop-Abstaende
     unterschiedlich schnell aufloest.

Simulation, Zonen und Basislinie werden aus analyse_crv_gate_survivorship.py
importiert statt nachgebaut - zwei Implementierungen wuerden auseinanderlaufen
(Lehre vom 03.08.).

Liest ausschliesslich den Notebook-Export, keine Produktiv-DB.
"""
from __future__ import annotations

import io
import json
import random
import statistics
import sys
from collections import defaultdict

from analyse_crv_gate_survivorship import (
    STANDARD_PFAD, basislinie, simuliere, zonen,
)

# Baender wie in der 06.08.-Auswertung, damit der Widerspruch vergleichbar bleibt
BAENDER = [(0.0, 2.0), (2.0, 3.0), (3.0, 5.0), (5.0, 8.0), (8.0, 12.0), (12.0, 1e9)]
HORIZONTE = (7, 14)
MIN_N = 15
BOOTSTRAP = 2000


def lade_reihen(d: dict) -> dict:
    je = d.get("preishistorie_signal_symbole", {}).get("preishistorie_je_symbol", {})
    reihen = {}
    for sym, rows in je.items():
        r = sorted([x for x in rows if x.get("currency") == "USD"
                    and None not in (x.get("high"), x.get("low"), x.get("close"))],
                   key=lambda x: x["date"])
        if r:
            reihen[sym] = r
    return reihen


def band_von(stop_pct: float):
    for lo, hi in BAENDER:
        if lo <= stop_pct < hi:
            return (lo, hi)
    return None


def block_bootstrap(faelle: list[dict], zieh: int = BOOTSTRAP) -> tuple[float, float]:
    """Ueber SYMBOLE ziehen, nicht ueber Einzelfaelle - sonst zu enge Intervalle."""
    je_symbol = defaultdict(list)
    for f in faelle:
        je_symbol[f["symbol"]].append(f["r"])
    symbole = list(je_symbol)
    if len(symbole) < 2:
        return (float("nan"), float("nan"))
    rng = random.Random(20260806)          # fester Seed: Unsicherheit abbilden,
    mittel = []                            # nicht die Anzeige unruhig machen
    for _ in range(zieh):
        werte = []
        for _ in range(len(symbole)):
            werte.extend(je_symbol[rng.choice(symbole)])
        if werte:
            mittel.append(statistics.fmean(werte))
    mittel.sort()
    return (mittel[int(0.025 * len(mittel))], mittel[int(0.975 * len(mittel))])


def auswerten(d: dict, reihen: dict, horizont: int, richtung: str | None) -> None:
    je_band: dict = defaultdict(list)
    ohne_reihe = 0
    for r in d.get("hebel_signals", []):
        if richtung and (r.get("richtung") or "").upper() != richtung:
            continue
        z = zonen(r)
        if not z or r["symbol"] not in reihen:
            continue
        sim = simuliere(z, reihen[r["symbol"]], r["created_at"][:10], horizont)
        if sim is None:
            ohne_reihe += 1
            continue
        b = band_von(z["stop_rel"] * 100.0)
        if b:
            je_band[b].append({**sim, **z, "symbol": r["symbol"]})

    titel = f"HORIZONT {horizont} TAGE" + (f" - nur {richtung}" if richtung else " - alle Richtungen")
    print()
    print("=" * 92)
    print(titel + f"   ({ohne_reihe} ohne ausreichende Preisreihe verworfen)")
    print("=" * 92)
    print(f"  {'Stop-Band':>12s} | {'n':>4s} | {'EW (R)':>8s} | {'Bootstrap-KI':>18s} | "
          f"{'Basislinie':>10s} | {'Abstand':>8s} | {'positiv':>7s}")
    print("  " + "-" * 88)

    for b in BAENDER:
        g = je_band.get(b, [])
        if not g:
            continue
        werte = [x["r"] for x in g]
        ew = statistics.fmean(werte)
        positiv = sum(1 for w in werte if w > 0) / len(werte) * 100
        lo, hi = block_bootstrap(g)

        # Basislinie mit EXAKT dem Stop und CRV dieses Bandes
        med_stop = statistics.median(x["stop_rel"] for x in g)
        med_crv = statistics.median(x["crv"] for x in g)
        anteil_short = sum(1 for x in g if x.get("short")) / len(g)
        bl = basislinie(reihen, med_stop, med_crv, anteil_short >= 0.5, horizont)
        bl_ew = statistics.fmean(bl) if bl else float("nan")

        label = f"{b[0]:.0f}-{b[1]:.0f} %" if b[1] < 1e9 else f"> {b[0]:.0f} %"
        warn = "" if len(g) >= MIN_N else "  <-- n zu klein"
        print(f"  {label:>12s} | {len(g):4d} | {ew:+8.3f} | "
              f"[{lo:+6.3f};{hi:+6.3f}] | {bl_ew:+10.3f} | {ew - bl_ew:+8.3f} | "
              f"{positiv:6.1f} %{warn}")


def main() -> None:
    pfad = sys.argv[1] if len(sys.argv) > 1 else STANDARD_PFAD
    d = json.load(io.open(pfad, encoding="utf-8"))
    reihen = lade_reihen(d)
    print(f"Export: {pfad}")
    print(f"{len(reihen)} Symbole mit USD-Preisreihe")
    print()
    print("KEIN Aufloesungs-Filter: jedes Signal mit Zonen wird neu simuliert.")
    print("Damit faellt kein weit gestopptes Signal aus der Stichprobe heraus -")
    print("genau der Fehler, an dem beide Vormessungen leiden.")

    for horizont in HORIZONTE:
        auswerten(d, reihen, horizont, None)
    for richtung in ("LONG", "SHORT"):
        auswerten(d, reihen, 7, richtung)


if __name__ == "__main__":
    main()
