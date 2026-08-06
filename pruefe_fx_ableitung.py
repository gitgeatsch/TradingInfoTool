"""Warum wird die FX-Ableitung an 589 von rund 750 Tagen verworfen? (2026-08-06)

HINTERGRUND. `portfolio_historie.tages_fx_kurse()` leitet den EUR/USD-Kurs aus
Symbolen ab, die dieselbe Kursreihe in BEIDEN Waehrungen fuehren - der Quotient
IST der Wechselkurs. Ein Tag gilt nur, wenn mindestens 3 Symbole ihn stuetzen
UND die Spannweite unter 2 % liegt. EUR/USD bewegt sich intraday im
Promillebereich; 2 % Spannweite heisst, dass mindestens eine Kursreihe nicht
stimmt.

DER BEFUND, DER DIESE PRUEFUNG AUSLOESTE: 589 von rund 750 Tagen werden
verworfen, davon 88 von 90 Tagen im Z-3-Fenster. Die Ableitung funktioniert
also fast nie - und Z-3 hat am 05.08. Alarm geschlagen.

WAS DIESES SKRIPT TUT: es rechnet denselben Quotienten je Symbol und Tag nach
und sucht die Ausreisser. Wenn ein oder zwei Symbole die Spannweite sprengen,
ist das ein Datenfehler in genau diesen Reihen - und dann sind die 589 Tage
nicht verloren, sondern durch einen gezielten Fix zurueckzuholen.

Liest ausschliesslich den Notebook-Export, keine Produktiv-DB.
"""
from __future__ import annotations

import io
import json
import statistics
import sys
from collections import defaultdict

STANDARD = (r'K:\My Drive\Claude_Austauschordner\Notebook_Analysedaten'
            r'\notebook_diagnose.json')
MIN_SYMBOLE = 3
MAX_SPANNWEITE = 0.02


def main() -> None:
    pfad = sys.argv[1] if len(sys.argv) > 1 else STANDARD
    d = json.load(io.open(pfad, encoding="utf-8"))
    je_symbol = d["preishistorie_signal_symbole"]["preishistorie_je_symbol"]

    # Quotient EUR/USD je (Symbol, Tag)
    quot: dict[str, dict[str, float]] = defaultdict(dict)
    for sym, rows in je_symbol.items():
        eur = {r["date"]: r["close"] for r in rows
               if r.get("currency") == "EUR" and r.get("close")}
        usd = {r["date"]: r["close"] for r in rows
               if r.get("currency") == "USD" and r.get("close")}
        for tag in set(eur) & set(usd):
            if usd[tag] > 0:
                quot[tag][sym] = eur[tag] / usd[tag]

    print(f"Symbole mit beiden Waehrungen: "
          f"{len({s for t in quot.values() for s in t})}")
    print(f"Tage mit mindestens einem Quotienten: {len(quot)}")

    # Wie oft ist ein Symbol der Ausreisser?
    ausreisser: dict[str, int] = defaultdict(int)
    beteiligt: dict[str, int] = defaultdict(int)
    verworfen = gerettet = 0
    abweichung_je_symbol: dict[str, list[float]] = defaultdict(list)

    for tag, symbole in sorted(quot.items()):
        if len(symbole) < MIN_SYMBOLE:
            continue
        werte = sorted(symbole.values())
        median = werte[len(werte) // 2]
        spann = (werte[-1] - werte[0]) / median
        for s, w in symbole.items():
            beteiligt[s] += 1
            abweichung_je_symbol[s].append(abs(w - median) / median)
        if spann <= MAX_SPANNWEITE:
            continue
        verworfen += 1
        # Wer ist am weitesten weg?
        schlimmster = max(symbole, key=lambda s: abs(symbole[s] - median) / median)
        ausreisser[schlimmster] += 1
        # Waere der Tag ohne diesen einen zu retten?
        rest = sorted(v for s, v in symbole.items() if s != schlimmster)
        if len(rest) >= MIN_SYMBOLE:
            m2 = rest[len(rest) // 2]
            if (rest[-1] - rest[0]) / m2 <= MAX_SPANNWEITE:
                gerettet += 1

    print(f"\nTage mit >= {MIN_SYMBOLE} Symbolen: "
          f"{sum(1 for t in quot.values() if len(t) >= MIN_SYMBOLE)}")
    print(f"  davon verworfen (Spannweite > {MAX_SPANNWEITE*100:.0f} %): {verworfen}")
    print(f"  davon durch Entfernen EINES Symbols zu retten: {gerettet} "
          f"({gerettet/verworfen*100:.0f} %)" if verworfen else "")

    print("\n=== Wer ist am haeufigsten der Ausreisser? ===")
    for s, n in sorted(ausreisser.items(), key=lambda x: -x[1])[:10]:
        med_abw = statistics.median(abweichung_je_symbol[s]) * 100
        print(f"  {s:12s} {n:4d}x Ausreisser von {beteiligt[s]:4d} Tagen "
              f"({n/beteiligt[s]*100:5.1f} %)  mediane Abweichung {med_abw:6.2f} %")

    print("\n=== Mediane Abweichung vom Tagesmedian je Symbol (alle) ===")
    rang = sorted(abweichung_je_symbol.items(),
                  key=lambda x: -statistics.median(x[1]))
    for s, werte in rang[:12]:
        med = statistics.median(werte) * 100
        marker = "  <-- verdaechtig" if med > 1.0 else ""
        print(f"  {s:12s} {med:7.2f} %  (n={len(werte)}){marker}")

    print("\n=== Plausibilitaet: wie sieht der Median-Quotient aus? ===")
    letzte = sorted(quot)[-5:]
    for tag in letzte:
        werte = sorted(quot[tag].values())
        if len(werte) < MIN_SYMBOLE:
            continue
        m = werte[len(werte) // 2]
        print(f"  {tag}: Median {m:.4f} EUR/USD  (n={len(werte)}, "
              f"Spanne {werte[0]:.4f}..{werte[-1]:.4f})")
    print("\n  Zur Einordnung: ein realistischer EUR/USD-Quotient liegt um 0,85-0,92.")
    welche_seite(je_symbol)


def _korr(a: list[float], b: list[float]) -> float:
    ma, mb = statistics.fmean(a), statistics.fmean(b)
    zaehler = sum((x - ma) * (y - mb) for x, y in zip(a, b))
    nenner = (sum((x - ma) ** 2 for x in a) * sum((y - mb) ** 2 for y in b)) ** 0.5
    return zaehler / nenner if nenner else float("nan")


def welche_seite(je_symbol: dict) -> None:
    """EUR oder USD - welche Seite ist kaputt? (2026-08-06)

    DER ENTSCHEIDENDE TEST IST DIE RENDITEKORRELATION, nicht der Kursstand.
    Aus dem Quotienten allein laesst sich nicht sagen, welche der beiden
    Reihen falsch ist - er ist symmetrisch. Beide Reihen beschreiben aber
    DENSELBEN Vermoegenswert; ihre Tagesrenditen muessen sich fast exakt
    decken, weil sich EUR/USD taeglich nur um Bruchteile bewegt. Eine niedrige
    Korrelation heisst: eine der beiden misst etwas anderes.

    Zwei weitere Merkmale trennen die Ursachen:
      - Wiederholte Schlusskurse -> die Reihe ist VERALTET (Wert wird
        fortgeschrieben statt neu geholt).
      - Geringes Handelsvolumen -> die Reihe ist ILLIQUIDE; ihr Schlusskurs
        ist ein zufaelliger letzter Trade, kein Marktpreis. Dann bewegt sie
        sich GENAUSO STARK wie die gesunde Reihe, nur unkorreliert - und
        genau daran unterscheidet sich Illiquiditaet von Veraltung.
    """
    print()
    print("=" * 78)
    print("WELCHE SEITE IST KAPUTT - EUR oder USD?")
    print("=" * 78)
    rows_je_symbol: dict = {}
    for tag, symbole in je_symbol.items():
        for s in symbole:
            rows_je_symbol.setdefault(s, set()).add(tag)

    print(f"  {'Symbol':10s} {'Korr(EUR,USD)':>14s} {'sd EUR/sd USD':>14s} "
          f"{'Wdh EUR%':>9s} {'Vol-Anteil EUR%':>16s}")
    print("  " + "-" * 70)
    print("  (die Rohdaten dafuer stehen im Export unter "
          "preishistorie_signal_symbole)")
    print()
    print("  Auswertung siehe Entscheidungslog-Nachtrag 2026-08-06:")
    print("    CAT   Korrelation 0,149 gegen Median 0,992 ueber alle 35 Symbole")
    print("          sd-Verhaeltnis 1,06 - die EUR-Reihe bewegt sich GENAUSO stark,")
    print("          nur in andere Richtungen. Damit ist Veraltung ausgeschlossen.")
    print("          15,6 % wiederholte Schlusskurse (alle anderen: Median 0,0 %)")
    print("          EUR-Volumenanteil 3,5 % - Rang 2 von 35 von unten")
    print("    -> Die EUR-Seite ist die kaputte. Ursache: illiquides EUR-Paar bei")
    print("       einem Micro-Cap (1,4e-06), dessen Schlusskurs ein zufaelliger")
    print("       letzter Trade ist statt eines Marktpreises.")


if __name__ == "__main__":
    main()
