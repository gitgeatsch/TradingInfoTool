"""V3: Wann wird die Kante real? Der Planungshorizont, gemessen statt gesetzt.

DIE FRAGE. Der Rahmen "0 bis max. 5 Tage" war ein MESSKOMPROMISS (Nutzer-
Klarstellung 06.08.) - gewaehlt, damit Signale schnell genug aufloesen um
ueberhaupt auswertbar zu sein. Inzwischen steht er im Prompt (Kosten-Fakt:
"der Rahmen sind 0 bis max. 5 Tage") und formt damit die Zonen, die das Modell
setzt. Eine Zahl, die zum Messen gewaehlt wurde, formt das Gemessene.

Diese Messung beantwortet nicht "wann ist der Gipfel" - das waere bei
zensierten Daten kaum bestimmbar - sondern die entscheidungsrelevante Variante:

    WIE VIEL GIBT MAN AUF, WENN MAN BEI TAG N ABSCHNEIDET?

Gemessen als Anteil des bis Horizont-Ende erreichten maximalen Buchgewinns
(MFE), der bereits bis Tag N erreicht war. Liegt der Anteil bei Tag 5 nahe
100 %, ist der Rahmen grosszuegig. Liegt er bei 60 %, schneidet er die Haelfte
der Bewegung ab.

ZWEI LESARTEN, beide berichtet:

  A) MFE BIS ZUR BARRIERE - der Trade endet, wenn Stop oder Ziel faellt. Das
     ist die realistische Sicht: so lange lebt die Position wirklich.
  B) MFE OHNE BARRIEREN - wie weit waere der Kurs gelaufen, haette nichts
     gestoppt. Beantwortet die Gegenfrage: laeuft die Bewegung ueber unser
     Fenster hinaus weiter?

Nur A allein waere irrefuehrend: ein enger Stop beendet den Trade frueh und
laesst den Horizont dadurch kurz aussehen - dieselbe Konfundierung, die am
06.08. beim "Sprung bei CRV 4,0" gefunden wurde.

HARTE DATENGRENZE, ehrlich vorweg: die Kursreihen enden am 06.08., die Signale
beginnen im Juli. Ein voller 30-Tage-Vorlauf existiert fuer NULL Signale, ein
21-Tage-Vorlauf fuer 38. Belastbar messbar sind 7 und 14 Tage (589 bzw. 375
Signale). Ob die Bewegung ueber 14 Tage hinaus weiterlaeuft, ist mit den
vorliegenden Daten NICHT beantwortbar - das gehoert zur Antwort dazu.

Simulation und Zonen aus analyse_crv_gate_survivorship importiert.
Liest nur den Export, keine Produktiv-DB.
"""
from __future__ import annotations

import io
import json
import random
import statistics
import sys
from collections import defaultdict

from analyse_crv_gate_survivorship import STANDARD_PFAD, zonen

HORIZONTE = (7, 14)
MIN_N = 15
BOOTSTRAP = 2000


def lade_reihen(d: dict) -> dict:
    reihen = {}
    for sym, rows in d["preishistorie_signal_symbole"]["preishistorie_je_symbol"].items():
        r = sorted([x for x in rows if x.get("currency") == "USD"
                    and None not in (x.get("high"), x.get("low"), x.get("close"))],
                   key=lambda x: x["date"])
        if r:
            reihen[sym] = r
    return reihen


def verlauf(z: dict, reihe: list, ab_datum: str, horizont: int,
            mit_barrieren: bool) -> list[float] | None:
    """Laufender MFE in R je Tag. None, wenn die Reihe den Horizont nicht deckt."""
    tage = [p for p in reihe if p["date"] >= ab_datum][:horizont + 1]
    if len(tage) < horizont + 1:
        return None
    e, risiko, short = z["entry"], z["risiko"], z["ist_short"]
    if risiko <= 0:
        return None
    lauf, bester = [], 0.0
    for p in tage:
        hoch, tief = p["high"], p["low"]
        if hoch is None or tief is None:
            lauf.append(bester)
            continue
        guenstig = (e - tief) if short else (hoch - e)
        bester = max(bester, guenstig / risiko)
        lauf.append(bester)
        if mit_barrieren:
            # Trade endet an der Barriere - danach gibt es keine Position mehr
            hit_stop = (hoch >= z["stop"]) if short else (tief <= z["stop"])
            hit_ziel = (tief <= z["ziel"]) if short else (hoch >= z["ziel"])
            if hit_stop or hit_ziel:
                lauf.extend([bester] * (horizont + 1 - len(lauf)))
                break
    return lauf


def anteile_je_tag(laeufe: list[list[float]], horizont: int) -> list[float]:
    """Median-Anteil des End-MFE, der bis Tag N erreicht war."""
    anteile = []
    for tag in range(horizont + 1):
        werte = [l[tag] / l[-1] for l in laeufe if l[-1] > 0]
        anteile.append(statistics.median(werte) if werte else float("nan"))
    return anteile


def bootstrap_symbol(paare: list[tuple[str, float]], zieh: int = BOOTSTRAP):
    je_symbol = defaultdict(list)
    for sym, wert in paare:
        je_symbol[sym].append(wert)
    symbole = list(je_symbol)
    if len(symbole) < 2:
        return (float("nan"), float("nan"))
    rng = random.Random(20260806)
    mittel = []
    for _ in range(zieh):
        werte = []
        for _ in range(len(symbole)):
            werte.extend(je_symbol[rng.choice(symbole)])
        if werte:
            mittel.append(statistics.median(werte))
    mittel.sort()
    return (mittel[int(0.025 * len(mittel))], mittel[int(0.975 * len(mittel))])


def auswerten(d: dict, reihen: dict, horizont: int, mit_barrieren: bool,
              richtung: str | None = None) -> None:
    laeufe, paare_tag5, aufloesetag = [], [], []
    for r in d.get("hebel_signals", []):
        if richtung and (r.get("richtung") or "").upper() != richtung:
            continue
        z = zonen(r)
        if not z or r["symbol"] not in reihen:
            continue
        lauf = verlauf(z, reihen[r["symbol"]], r["created_at"][:10], horizont, mit_barrieren)
        if lauf is None or lauf[-1] <= 0:
            continue
        laeufe.append(lauf)
        paare_tag5.append((r["symbol"], lauf[min(5, horizont)] / lauf[-1]))
        # erster Tag, an dem der End-MFE praktisch erreicht ist
        ziel = lauf[-1] * 0.99
        aufloesetag.append(next((i for i, v in enumerate(lauf) if v >= ziel), horizont))

    art = "MIT Barrieren (Trade endet)" if mit_barrieren else "OHNE Barrieren (theoretisch)"
    kopf = f"HORIZONT {horizont} TAGE - {art}"
    if richtung:
        kopf += f" - nur {richtung}"
    print()
    print("=" * 88)
    print(kopf + f"   n={len(laeufe)}")
    print("=" * 88)
    if len(laeufe) < MIN_N:
        print("  zu wenige Faelle")
        return

    anteile = anteile_je_tag(laeufe, horizont)
    print("  Anteil des End-MFE, der bis Tag N erreicht war (Median):")
    zeile = "   "
    for tag in range(horizont + 1):
        zeile += f" T{tag}:{anteile[tag]*100:5.1f}%"
        if tag % 5 == 4:
            print(zeile)
            zeile = "   "
    if zeile.strip():
        print(zeile)

    lo, hi = bootstrap_symbol(paare_tag5)
    a5 = anteile[min(5, horizont)]
    print()
    print(f"  BIS TAG 5 erreicht: {a5*100:.1f} % des End-MFE   "
          f"Bootstrap ueber Symbole [{lo*100:.1f} ; {hi*100:.1f}]")
    print(f"  Median-Tag, an dem 99 % des End-MFE stehen: {statistics.median(aufloesetag):.1f}")
    anteil_nach5 = sum(1 for t in aufloesetag if t > 5) / len(aufloesetag) * 100
    print(f"  Anteil der Signale, deren Bestwert ERST NACH Tag 5 kommt: {anteil_nach5:.1f} %")


def main() -> None:
    pfad = sys.argv[1] if len(sys.argv) > 1 else STANDARD_PFAD
    d = json.load(io.open(pfad, encoding="utf-8"))
    reihen = lade_reihen(d)
    print(f"Export: {pfad}")
    print(f"{len(reihen)} Symbole mit USD-Preisreihe")
    print()
    print("Gemessen: welcher Anteil des am Horizont-Ende erreichten maximalen")
    print("Buchgewinns stand schon an Tag N? Nahe 100 % bei Tag 5 = der Rahmen")
    print("ist grosszuegig. Deutlich darunter = er schneidet Bewegung ab.")

    for horizont in HORIZONTE:
        for mit_b in (True, False):
            auswerten(d, reihen, horizont, mit_b)
    for richtung in ("LONG", "SHORT"):
        auswerten(d, reihen, 14, True, richtung)

    print()
    print("=" * 88)
    print("GRENZE DIESER MESSUNG")
    print("=" * 88)
    print("  Die Kursreihen enden am 06.08., die Signale beginnen im Juli. Ein voller")
    print("  30-Tage-Vorlauf existiert fuer NULL Signale, ein 21-Tage-Vorlauf fuer 38.")
    print("  Ob die Bewegung ueber 14 Tage hinaus weiterlaeuft, ist mit diesen Daten")
    print("  NICHT beantwortbar. Die Messung sagt, wie viel innerhalb von 14 Tagen")
    print("  bis Tag 5 da ist - nicht, ob 14 Tage genug sind.")


if __name__ == "__main__":
    main()
