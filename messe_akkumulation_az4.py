"""AZ-4 gegen DCA: erfuellt die gestaffelte Akkumulation ihren Zweck? (2026-08-06)

DIE LUECKE, DIE DAS SCHLIESST. Krypto-Spot ist laut eigenem Regelwerk ein
AKKUMULATIONS-Kapitel - AZ-4 "Gestaffelt, nie all-in: in Tranchen kaufen, damit
ein tieferer Absturz zur Chance statt zum Ruin wird", mit drei gebauten
Bausteinen (Tranchen, Boden-Zielzone, Cash-Reserve-Ziel). Gemessen wurde es
bisher mit R-Multiple und SQN - Kennzahlen des abgeschlossenen EINZELTRADES.

Die koennen Akkumulation strukturell nicht abbilden. Akkumulation fragt nicht
"war dieser Trade gut", sondern:

    Habe ich ueber den Zeitraum MEHR EINHEITEN zu einem BESSEREN
    Durchschnittspreis aufgebaut als ohne das System?

WARUM DCA UND NICHT BUY-AND-HOLD. Buy-and-Hold ist ein Einmalkauf; AZ-4 kauft
gestaffelt ueber die Zeit. Der ehrliche passive Gegenspieler zu gestaffeltem
Kaufen ist gestaffeltes Kaufen OHNE Signal - also Dollar-Cost-Averaging.

ZWEI BASISLINIEN, WEIL EINE NICHT TRENNT:

  1. DCA-GLEICHMAESSIG - dasselbe Geld, gleichmaessig ueber ALLE Tage verteilt.
     Das ist der passive Standard, gegen den sich die Frage "haette ich mir das
     System sparen koennen" stellt.
  2. ZUFAELLIGE TAGE - dasselbe Geld, dieselbe ANZAHL Kauftage, zufaellig
     platziert. Noetig, weil AZ-4 an wenigen Tagen kauft und DCA an vielen:
     wer nur gegen DCA vergleicht, misst teilweise den Takt statt das Timing.
     Erst diese zweite Linie trennt "gut getimt" von "anders getaktet".

BEIDE BASISLINIEN KAUFEN DIESELBEN SYMBOLE IN DERSELBEN AUFTEILUNG. Sonst
wuerde die Auswahl gemessen statt der Zeitpunkt - AZ-4 behauptet aber nichts
ueber die Auswahl, sondern ueber das gestaffelte Kaufen.

EINSCHRAENKUNGEN, die dazugehoeren und die das Ergebnis begrenzen:

  - MENGENERHOEHUNG IST NICHT ZWINGEND EIN KAUF. `holdings.quantity` enthaelt
    auch Staking-Gutschriften und Airdrops (im Code seit jeher dokumentiert).
    Aus den Mengen allein ist beides nicht zu trennen. Gegenmittel: eine
    Mindest-Erhoehung in Prozent der Position; Belohnungen sind klein und
    haeufig, Kaeufe gross und selten. Der Schwellenwert wird ausgewiesen, das
    Ergebnis mit und ohne gezeigt.
  - NUR 88 REKONSTRUIERTE TAGE (2026-05-08 bis 2026-08-03). Der "laufend"-Teil
    ab 05.08. hat eine andere Symbolbasis (33 statt 156) und bleibt aussen vor.
  - EINE MARKTPHASE. Ein Ergebnis zugunsten von AZ-4 in einer fallenden Phase
    heisst nicht, dass es in einer steigenden haelt - gestaffeltes Kaufen ist
    bei fallenden Kursen strukturell im Vorteil.

Rechnung in USD wie der Produktivcode. Liest nur den Export, keine Produktiv-DB.
"""
from __future__ import annotations

import io
import json
import random
import statistics
import sys
from collections import defaultdict

STANDARD = (r'K:\My Drive\Claude_Austauschordner\Notebook_Analysedaten'
            r'\notebook_diagnose.json')
MIN_ERHOEHUNG_REL = 0.01     # 1 % der Position - unterhalb eher Staking als Kauf
MIN_KAUFTAGE = 2             # darunter ist "gestaffelt" nicht einmal versucht
BOOTSTRAP = 2000
STABLECOINS = {"EURCV", "USDC", "USDT", "DAI"}


def lade(pfad: str):
    d = json.load(io.open(pfad, encoding="utf-8"))
    kurse: dict[str, dict[str, float]] = {}
    for sym, rows in d["preishistorie_signal_symbole"]["preishistorie_je_symbol"].items():
        r = {x["date"]: x["close"] for x in rows
             if x.get("currency") == "USD" and x.get("close")}
        if r:
            kurse[sym] = r
    reihe = sorted((r for r in d["rohdaten_fuer_backtest"]["portfolio_wert_historie"]
                    if r.get("quelle") == "rekonstruiert"),
                   key=lambda r: r["datum"])
    klasse = {k: v.get("assetklasse") for k, v in d["watchlist_stammdaten"].items()}
    return kurse, reihe, klasse


def kaeufe_ableiten(reihe: list, kurse: dict, min_rel: float) -> dict:
    """Mengenerhoehungen als Kauf lesen: {symbol: [(datum, menge, kurs), ...]}"""
    je_symbol: dict[str, list] = defaultdict(list)
    for i in range(1, len(reihe)):
        vor = json.loads(reihe[i - 1]["mengen_json"] or "{}")
        jetzt = json.loads(reihe[i]["mengen_json"] or "{}")
        tag = reihe[i]["datum"]
        for sym in set(vor) | set(jetzt):
            alt, neu = float(vor.get(sym, 0) or 0), float(jetzt.get(sym, 0) or 0)
            if neu <= alt:
                continue
            zuwachs = neu - alt
            if alt > 0 and zuwachs / alt < min_rel:
                continue                      # zu klein - eher Staking-Gutschrift
            kurs = (kurse.get(sym) or {}).get(tag)
            if kurs and kurs > 0:
                je_symbol[sym].append((tag, zuwachs, kurs))
    return je_symbol


def dca_menge(ausgabe_usd: float, tage: list[str], kursreihe: dict) -> float | None:
    """Gleichmaessig ueber ALLE Tage verteilt - der passive Standard."""
    gueltig = [t for t in tage if kursreihe.get(t)]
    if not gueltig:
        return None
    je_tag = ausgabe_usd / len(gueltig)
    return sum(je_tag / kursreihe[t] for t in gueltig)


def zufalls_menge(ausgabe_usd: float, tage: list[str], kursreihe: dict,
                  anzahl_kauftage: int, rng: random.Random,
                  menge_az4: float | None = None,
                  zieh: int = 2000) -> tuple[float, float] | None:
    """Dieselbe ANZAHL Kauftage, zufaellig platziert - trennt Timing vom Takt.

    Gibt (Median-Menge, Perzentil) zurueck. Das PERZENTIL ist die eigentliche
    Aussage: der Anteil der Zufallsplatzierungen, den AZ-4 schlaegt. Es ist ein
    Permutationstest je Symbol und braucht keine Symbol-Stichprobe - anders als
    der Bootstrap, der bei vier gleichgerichteten Symbolen die Null gar nicht
    erreichen KANN und dadurch eine Sicherheit vortaeuscht, die er nicht hat.
    """
    gueltig = [t for t in tage if kursreihe.get(t)]
    if len(gueltig) < anzahl_kauftage or anzahl_kauftage < 1:
        return None
    je_kauf = ausgabe_usd / anzahl_kauftage
    mengen = []
    for _ in range(zieh):
        gewaehlt = rng.sample(gueltig, anzahl_kauftage)
        mengen.append(sum(je_kauf / kursreihe[t] for t in gewaehlt))
    mengen.sort()
    perzentil = (sum(1 for m in mengen if menge_az4 > m) / len(mengen)
                 if menge_az4 is not None else float("nan"))
    return statistics.median(mengen), perzentil


def bootstrap_symbole(werte: list[tuple[str, float, float]], zieh: int = BOOTSTRAP):
    """Block-Bootstrap ueber Symbole (Projektstandard) auf dem gewichteten Vorteil."""
    if len(werte) < 2:
        return (float("nan"), float("nan"))
    rng = random.Random(20260806)
    ergebnisse = []
    for _ in range(zieh):
        stichprobe = [rng.choice(werte) for _ in werte]
        gew = sum(w for _, _, w in stichprobe)
        if gew > 0:
            ergebnisse.append(sum(v * w for _, v, w in stichprobe) / gew)
    ergebnisse.sort()
    if not ergebnisse:
        return (float("nan"), float("nan"))
    return (ergebnisse[int(0.025 * len(ergebnisse))],
            ergebnisse[int(0.975 * len(ergebnisse))])


def auswerten(kurse, reihe, klasse, min_rel: float, nur_krypto: bool) -> None:
    kaeufe = kaeufe_ableiten(reihe, kurse, min_rel)
    tage = [r["datum"] for r in reihe]
    rng = random.Random(20260806)

    titel = f"Mindest-Erhoehung {min_rel*100:.0f} % der Position"
    titel += " | nur Krypto" if nur_krypto else " | alle Assetklassen"
    print()
    print("=" * 96)
    print(titel)
    print("=" * 96)
    print(f"  {'Symbol':10s} {'Kauf-':>6s} {'Ausgabe':>11s} {'AZ-4':>13s} "
          f"{'DCA':>13s} {'Zufall':>13s} {'vs DCA':>9s} {'vs Zufall':>10s} {'Perzentil':>9s}")
    print(f"  {'':10s} {'tage':>6s} {'USD':>11s} {'Einheiten':>13s} "
          f"{'Einheiten':>13s} {'Einheiten':>13s} {'':>9s} {'':>10s} {'ggn Zufall':>9s}")
    print("  " + "-" * 92)

    gegen_dca: list[tuple[str, float, float]] = []
    gegen_zufall: list[tuple[str, float, float]] = []
    perzentile: list[float] = []
    for sym in sorted(kaeufe):
        if sym in STABLECOINS:
            continue
        if nur_krypto and klasse.get(sym) != "krypto":
            continue
        posten = kaeufe[sym]
        if len(posten) < MIN_KAUFTAGE:
            continue
        ausgabe = sum(menge * kurs for _, menge, kurs in posten)
        menge_az4 = sum(menge for _, menge, _ in posten)
        reihe_sym = kurse[sym]
        m_dca = dca_menge(ausgabe, tage, reihe_sym)
        zuf = zufalls_menge(ausgabe, tage, reihe_sym, len(posten), rng, menge_az4)
        if not m_dca or not zuf:
            continue
        m_zuf, perzentil = zuf
        v_dca = menge_az4 / m_dca - 1
        v_zuf = menge_az4 / m_zuf - 1
        gegen_dca.append((sym, v_dca, ausgabe))
        gegen_zufall.append((sym, v_zuf, ausgabe))
        perzentile.append(perzentil)
        print(f"  {sym:10s} {len(posten):6d} {ausgabe:11.2f} {menge_az4:13.4g} "
              f"{m_dca:13.4g} {m_zuf:13.4g} {v_dca*100:+8.2f}% {v_zuf*100:+9.2f}% "
              f"{perzentil*100:8.0f}%")

    if not gegen_dca:
        print("  (keine auswertbaren Symbole)")
        return

    gesamt_ausgabe = sum(a for _, _, a in gegen_dca)
    gew_dca = sum(v * a for _, v, a in gegen_dca) / gesamt_ausgabe
    gew_zuf = sum(v * a for _, v, a in gegen_zufall) / gesamt_ausgabe
    lo_d, hi_d = bootstrap_symbole(gegen_dca)
    lo_z, hi_z = bootstrap_symbole(gegen_zufall)

    print("  " + "-" * 102)
    print(f"  {len(gegen_dca)} Symbole, {gesamt_ausgabe:.2f} USD eingesetzt")
    print(f"  AZ-4 gegen DCA        : {gew_dca*100:+7.2f} % mehr Einheiten   "
          f"Bootstrap [{lo_d*100:+6.2f} ; {hi_d*100:+6.2f}]")
    print(f"  AZ-4 gegen Zufallstage: {gew_zuf*100:+7.2f} % mehr Einheiten   "
          f"Bootstrap [{lo_z*100:+6.2f} ; {hi_z*100:+6.2f}]")
    for name, lo, hi in (("DCA", lo_d, hi_d), ("Zufallstage", lo_z, hi_z)):
        if lo == lo and (lo > 0 or hi < 0):
            print(f"    -> gegen {name}: Bootstrap-Intervall schliesst die Null AUS")
        else:
            print(f"    -> gegen {name}: Bootstrap-Intervall enthaelt die Null - kein Nachweis")

    # DIE EIGENTLICHE AUSSAGE. Der Bootstrap ueber Symbole kann bei wenigen,
    # gleichgerichteten Symbolen die Null gar nicht erreichen - er taeuscht dann
    # eine Sicherheit vor, die er nicht hat. Das Perzentil ist ein
    # Permutationstest JE SYMBOL und braucht keine Symbol-Stichprobe.
    gleiches_vorzeichen = all(v > 0 for _, v, _ in gegen_zufall) or all(
        v < 0 for _, v, _ in gegen_zufall)
    if gleiches_vorzeichen and len(gegen_zufall) < 8:
        print(f"    !! WARNUNG: alle {len(gegen_zufall)} Symbole zeigen dasselbe "
              f"Vorzeichen - ein Bootstrap ueber Symbole KANN hier die Null nicht")
        print(f"       erreichen. Das Intervall ist Mechanik, kein Beleg.")
    mp = statistics.fmean(perzentile) * 100
    ueber50 = sum(1 for p in perzentile if p > 0.5)
    print(f"  PERMUTATION je Symbol: AZ-4 schlaegt im Mittel {mp:.0f} % der "
          f"Zufallsplatzierungen ({ueber50} von {len(perzentile)} Symbolen ueber 50 %)")
    if mp >= 90:
        print("    -> deutlich besser als Zufall")
    elif mp >= 70:
        print("    -> besser als Zufall, aber nicht deutlich")
    else:
        print("    -> nicht von Zufall zu trennen")


def main() -> None:
    pfad = sys.argv[1] if len(sys.argv) > 1 else STANDARD
    kurse, reihe, klasse = lade(pfad)
    print(f"Export: {pfad}")
    print(f"Rekonstruierte Tage: {len(reihe)} ({reihe[0]['datum']} .. {reihe[-1]['datum']})")
    print(f"Symbole mit USD-Kursreihe: {len(kurse)}")
    print()
    print("Gemessen wird die MENGE je eingesetztem Dollar - mehr Einheiten fuer")
    print("dasselbe Geld heisst besser akkumuliert. Beide Basislinien kaufen")
    print("dieselben Symbole in derselben Aufteilung, nur zu anderen Zeitpunkten.")

    for nur_krypto in (True, False):
        for min_rel in (MIN_ERHOEHUNG_REL, 0.0):
            auswerten(kurse, reihe, klasse, min_rel, nur_krypto)

    print()
    print("=" * 96)
    print("LESEHILFE")
    print("=" * 96)
    print("  'vs DCA'    - haette gleichmaessiges Kaufen ueber alle Tage mehr Einheiten")
    print("                gebracht? Der passive Standard.")
    print("  'vs Zufall' - haette dieselbe Anzahl Kauftage an ZUFAELLIGEN Tagen mehr")
    print("                gebracht? Trennt Timing von Taktung. DIESE Zahl ist die")
    print("                eigentliche Aussage ueber AZ-4.")
    print()
    print("  Vorsicht: gestaffeltes Kaufen ist bei FALLENDEN Kursen strukturell im")
    print("  Vorteil. Ein positives Ergebnis in dieser Marktphase belegt noch keine")
    print("  Kante - es braucht die Gegenprobe in einer steigenden Phase.")


if __name__ == "__main__":
    main()
