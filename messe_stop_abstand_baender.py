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
# ⚠️⚠️ DIESELBEN STAERKEN WIE IN `messnorm.STAERKEN` - nicht neu erfunden.
# Eine zweite Leiter waere eine zweite Skala, und Befunde aus beiden waeren
# nicht vergleichbar.
STAERKEN = (0.02, 0.05, 0.10, 0.20, 0.40)
# Positivkontrolle: FUENF Ziehungen, wie die Norm es verlangt. Eine
# Ziehung kann Saatglueck sein.
POSITIV_ZIEHUNGEN = 5


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


def _bootstrap_werte(faelle: list[dict], saat: int) -> tuple[float, float]:
    """Wie `block_bootstrap`, aber mit waehlbarer Saat.

    ⚠️ Ueber SYMBOLE ziehen, nicht ueber Einzelfaelle - sonst zu enge
    Intervalle. Dieselbe Regel wie oben; nur die Saat ist frei, damit die
    Positivkontrolle mehrere Ziehungen fahren kann."""
    je_symbol = defaultdict(list)
    for f in faelle:
        je_symbol[f["symbol"]].append(f["r"])
    symbole = list(je_symbol)
    if len(symbole) < 2:
        return (float("nan"), float("nan"))
    rng = random.Random(saat)
    mittel = []
    for _ in range(BOOTSTRAP):
        werte = []
        for _ in range(len(symbole)):
            werte.extend(je_symbol[rng.choice(symbole)])
        if werte:
            mittel.append(statistics.fmean(werte))
    mittel.sort()
    return (mittel[int(0.025 * len(mittel))], mittel[int(0.975 * len(mittel))])


def _gepflanzt(g: list[dict], bl_ew: float, staerke: float) -> list[dict]:
    """Die Faelle ZENTRIERT auf die Basislinie, dann um `staerke` versetzt.

    ⚠️⚠️ ZENTRIEREN IST PFLICHT (stehende Vorgabe, 07.09.2026). Wer den
    Effekt auf die ECHTE Reihe pflanzt, misst nicht die Trennschaerfe:
    enthaelt sie bereits einen trennbaren Unterschied, bleibt das Ergebnis
    bei JEDEM Versatz signifikant, und gemeldet wird die kleinste
    geprueften Zahl. Das heisst dann nur "der echte Effekt ist gross" -
    nicht "ein Effekt dieser Groesse waere gefunden worden".

        FALSCH   r + staerke
        RICHTIG  r - mittel(Band) + mittel(Basislinie) + staerke

    ⚠️ DER SCHNELLTEST: bei staerke 0 muss der zentrierte Abstand zur
    Basislinie EXAKT 0,0000 sein. Genau das prueft `_probe_zentrierung`.
    """
    ew = statistics.fmean(x["r"] for x in g)
    return [{**x, "r": x["r"] - ew + bl_ew + staerke} for x in g]


def _probe_zentrierung(g: list[dict], bl_ew: float) -> float:
    """Die Gegenprobe zur Zentrierung - muss 0,0 liefern."""
    null = _gepflanzt(g, bl_ew, 0.0)
    return statistics.fmean(x["r"] for x in null) - bl_ew


def trennschaerfe(g: list[dict], bl_ew: float) -> tuple:
    """Die KLEINSTE gepflanzte Staerke, die noch gefunden wird.

    "Gefunden" heisst: das Bootstrap-Band der ZENTRIERTEN, um `s`
    versetzten Reihe schliesst die Basislinie aus.

    ⚠️ OHNE SIE IST EIN ,TRAEGT NICHT' NICHT VON ,HAETTEN WIR GAR NICHT
    SEHEN KOENNEN' ZU UNTERSCHEIDEN. Genau daran ist die alte
    Stop-Messung nie gescheitert - sie hat es nie gefragt.
    """
    for st in STAERKEN:
        lo, hi = _bootstrap_werte(_gepflanzt(g, bl_ew, st), 20260913)
        if lo == lo and lo > bl_ew:          # NaN-sicher
            return st, lo, hi
    return None, float("nan"), float("nan")


def positivkontrolle(g: list[dict], bl_ew: float,
                     staerke: float = 0.40) -> tuple[int, int]:
    """Findet die Anlage einen BEKANNTEN Effekt - in wie vielen Ziehungen?

    ⚠️ FUENF Ziehungen mit verschiedenen Saaten. Eine einzelne kann
    Saatglueck sein; die Norm verlangt deshalb mehrere (`messnorm`,
    Positivkontrolle 5 Ziehungen).
    """
    gefunden = 0
    for i in range(POSITIV_ZIEHUNGEN):
        lo, _hi = _bootstrap_werte(_gepflanzt(g, bl_ew, staerke),
                                   20260913 + 1000 * i)
        if lo == lo and lo > bl_ew:
            gefunden += 1
    return gefunden, POSITIV_ZIEHUNGEN


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
          f"{'Basislinie':>10s} | {'Abstand':>8s} | {'positiv':>7s} | "
          f"{'Trennsch.':>9s} | {'Positivk.':>9s}")
    print("  " + "-" * 112)

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

        # ---- ⚠⚠ TRENNSCHAERFE UND POSITIVKONTROLLE (13.09.2026) -----
        #
        # Ohne sie ist ein "nicht trennbar" nicht von "haetten wir gar
        # nicht sehen koennen" zu unterscheiden - und genau diese Baender
        # sollen ueber die Stopweite JEDES Signals entscheiden.
        ts, ts_lo, _ts_hi = trennschaerfe(g, bl_ew)
        pk, pk_n = positivkontrolle(g, bl_ew)
        # ⚠ DIE GEGENPROBE ZUR ZENTRIERUNG, in jedem Lauf: bei Staerke 0
        # muss der Abstand zur Basislinie exakt 0 sein. Ist er es nicht,
        # pflanzt die Anlage auf die ECHTE Reihe und misst den vorhandenen
        # Effekt noch einmal (stehende Vorgabe 07.09.).
        _z = _probe_zentrierung(g, bl_ew)
        _zwarn = "" if abs(_z) < 1e-9 else "  ⚠ ZENTRIERUNG %+.2e" % _z

        label = f"{b[0]:.0f}-{b[1]:.0f} %" if b[1] < 1e9 else f"> {b[0]:.0f} %"
        warn = "" if len(g) >= MIN_N else "  <-- n zu klein"
        _ts = ("ab %.2f R" % ts) if ts is not None else "> 0,40 R"
        print(f"  {label:>12s} | {len(g):4d} | {ew:+8.3f} | "
              f"[{lo:+6.3f};{hi:+6.3f}] | {bl_ew:+10.3f} | {ew - bl_ew:+8.3f} | "
              f"{positiv:6.1f} % | {_ts:>9s} | {pk:d} von {pk_n:d}"
              f"{warn}{_zwarn}")


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
