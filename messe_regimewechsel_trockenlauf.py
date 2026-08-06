"""V2b: Was passiert beim ersten Regimewechsel? Trockenlauf, bevor er echt kommt.

WARUM DAS NOETIG IST. Am 06.08. gemessen: **ausnahmslos jedes Signal** der
gesamten Historie traegt `regime = "baer"` (1.391 Hebel, 2.223 Spot). Alle
regime-abhaengigen Mechanismen haben damit ueber die gesamte Projektlaufzeit
**genau einen Zweig** ausgefuehrt. Die uebrigen vier Profile sind Code, der nie
mit echten Daten gelaufen ist - und der irgendwann von selbst aktiv wird, ohne
Vorwarnung, an einem beliebigen Morgen um 06:00.

Dieses Skript laesst diesen Wechsel trocken laufen: es nimmt die
aufgezeichneten LLM-Ausgaben und rechnet die deterministischen Gate-Effekte
unter jedem Regime-Profil nach.

WAS ES BEANTWORTET (deterministisch, exakt):
  - R-5.10: wie viele Spot-Kaufsignale kaemen je Regime durch?
  - Positionsgroessen-Sockel: wie skaliert die Obergrenze mit?
  - Small-Cap-Budget: welcher Anteil des Portfolios waere je Regime erlaubt?
  - AZ-7: was bedeutet krise_extrem fuer die Hebel-Seite?

WAS ES NICHT BEANTWORTET, und das gehoert dazu: das Regime geht auch als FAKT
in den Prompt (`regime_profil` mit vier Gewichten, die KEINE Prompt-Regel
haben - Katalog 4.2 "keine Regel, kein Gate"). Wie sich das LLM-Verhalten bei
anderem Regime aendert, ist damit NICHT gemessen. Dafuer braeuchte es einen
Dreiarm-Lauf mit erzwungenem Regime im Faktensatz. Das hier misst die
deterministische Haelfte - die exakt und ohne LLM-Aufrufe bestimmbar ist.

WICHTIGE ABGRENZUNG, die ich zuerst falsch hatte: R-5.10 (die regime-abhaengige
Mindestkonfidenz) greift **nur bei der Spot-Familie**, fuer KAUFEN/NACHKAUFEN.
Der Hebel-Gate nutzt feste Schwellen (KONFIDENZ_SCHWELLE_NIEDRIG/HOCH), die
sich beim Regimewechsel NICHT bewegen. Wer das verwechselt, rechnet den Effekt
auf der falschen Verteilung aus.

Liest nur den Export und die Config, keine Produktiv-DB, keine LLM-Aufrufe.
"""
from __future__ import annotations

import io
import json
import statistics
import sys
from collections import Counter

import config as config_module

STANDARD = (r'K:\My Drive\Claude_Austauschordner\Notebook_Analysedaten'
            r'\notebook_diagnose.json')
KAUF_AKTIONEN = {"KAUFEN", "NACHKAUFEN"}


def main() -> None:
    pfad = sys.argv[1] if len(sys.argv) > 1 else STANDARD
    d = json.load(io.open(pfad, encoding="utf-8"))
    cfg = config_module.load_config()
    profile = cfg["regime"]["profile"]
    sockel = cfg["risiko"].get("konfidenz_positionsgroesse_sockel_anteil", 0.5)

    ist_regime = Counter(s.get("regime") for s in d["spot_signals"]
                         + d["hebel_signals"])
    print(f"Export: {pfad}")
    print(f"Beobachtete Regime ueber ALLE Signale: {dict(ist_regime)}")
    print("  -> genau ein Zustand. Alles Folgende ist ein Zweig, der nie lief.")

    kauf = [s for s in d["spot_signals"]
            if s.get("action") in KAUF_AKTIONEN
            and isinstance(s.get("confidence_pct"), (int, float))]
    konf = sorted(s["confidence_pct"] for s in kauf)

    # ---------------------------------------------------------------- R-5.10
    print()
    print("=" * 92)
    print(f"1) R-5.10 KONFIDENZ-GATE (nur Spot-Familie, KAUFEN/NACHKAUFEN) - n={len(konf)}")
    print("=" * 92)
    print(f"  Konfidenzverteilung: Median {statistics.median(konf):.0f}, "
          f"Spanne {min(konf):.0f}..{max(konf):.0f}")
    print()
    print(f"  {'Regime':16s} {'Schwelle':>9s} {'kaemen durch':>13s} {'Anteil':>8s} "
          f"{'gegen heute':>12s}")
    print("  " + "-" * 64)
    basis = None
    for name, prof in profile.items():
        schwelle = prof.get("min_konfidenz_prozent")
        if schwelle is None:
            continue
        durch = sum(1 for x in konf if x >= schwelle)
        anteil = durch / len(konf) * 100 if konf else 0
        if name == "baer":
            basis = anteil
        rel = "" if basis is None else f"{anteil - basis:+.1f} pp"
        marker = "  <-- heute" if name == "baer" else ""
        print(f"  {name:16s} {schwelle:9.0f} {durch:13d} {anteil:7.1f} % {rel:>12s}{marker}")

    print()
    print("  LESART: die gefaehrliche Richtung ist NICHT seitwaerts/bulle (dort")
    print("  oeffnet das Gate leicht), sondern KRISE_EXTREM - dort bricht der")
    print("  Durchlass ein, und zwar genau dann, wenn der Markt gestresst ist und")
    print("  ein nie gelaufener Codepfad am wenigsten erwuenscht ist.")

    # ------------------------------------------------- Positionsgroessen-Sockel
    print()
    print("=" * 92)
    print("2) POSITIONSGROESSEN-SOCKEL - lineare Skalierung ab der Regime-Schwelle")
    print("=" * 92)
    print(f"  Sockel bei genau der Mindestschwelle: {sockel*100:.0f} % der RM-1/RM-2-Obergrenze,")
    print("  bei 100 % Konfidenz die volle Obergrenze, dazwischen linear.")
    print()
    print(f"  {'Regime':16s} {'Schwelle':>9s} {'mittl. Groessenanteil der durchgelassenen':>44s}")
    print("  " + "-" * 72)
    for name, prof in profile.items():
        schwelle = prof.get("min_konfidenz_prozent")
        if schwelle is None:
            continue
        durch = [x for x in konf if x >= schwelle]
        if not durch:
            print(f"  {name:16s} {schwelle:9.0f} {'keine Signale':>44s}")
            continue
        anteile = [sockel + (1 - sockel) * (x - schwelle) / (100 - schwelle)
                   for x in durch]
        print(f"  {name:16s} {schwelle:9.0f} {statistics.fmean(anteile)*100:43.1f} %")
    print()
    print("  ACHTUNG, gegenlaeufiger Effekt: ein NIEDRIGERES Regime-Minimum laesst")
    print("  mehr Signale durch, gibt ihnen aber im Schnitt KLEINERE Positionen -")
    print("  weil der Abstand zur Schwelle die Groesse bestimmt. Beide Effekte")
    print("  wirken gegeneinander und heben sich teilweise auf.")

    # ------------------------------------------------------- Small-Cap-Budget
    print()
    print("=" * 92)
    print("3) SMALL-CAP-BUDGET und AZ-7")
    print("=" * 92)
    print(f"  {'Regime':16s} {'Small-Cap-Budget':>18s}  Bemerkung")
    print("  " + "-" * 70)
    for name, prof in profile.items():
        scb = prof.get("small_cap_budget_prozent")
        bem = ""
        if name == "krise_extrem":
            bem = "AZ-7: Hebel KOMPLETT AUS, Small-Cap auf 0"
        elif name == "baer":
            bem = "heutiger Zustand"
        print(f"  {name:16s} {scb!s:>18s}  {bem}")

    # ------------------------------------------------------ Gewichts-Fakten
    print()
    print("=" * 92)
    print("4) GEWICHTS-FAKTEN IM PROMPT - ohne jede Regel")
    print("=" * 92)
    print(f"  {'Regime':16s} {'Technik':>8s} {'Fundam.':>8s} {'Momentum':>9s} {'Makro':>8s}")
    print("  " + "-" * 54)
    for name, prof in profile.items():
        print(f"  {name:16s} {prof.get('gewicht_technik'):8} "
              f"{prof.get('gewicht_fundamental'):8} {prof.get('gewicht_momentum'):9} "
              f"{prof.get('gewicht_kontext_makro'):8}")
    print()
    print("  Diese vier Zahlen gehen an das Modell, OHNE dass eine Prompt-Regel")
    print("  erklaert was sie bedeuten (Katalog 4.2: 'keine Regel, kein Gate').")
    print("  Bei einem Regimewechsel aendern sie sich still - von Technik 0,24 auf")
    print("  0,43 zwischen baer und bulle. Wirkung nie gemessen.")

    print()
    print("=" * 92)
    print("WAS DIESER TROCKENLAUF NICHT ABDECKT")
    print("=" * 92)
    print("  Die LLM-Seite. Das Regime steht auch im Faktensatz (regime.wert,")
    print("  regime_profil). Wie sich das Modellverhalten bei anderem Regime")
    print("  aendert, braucht einen Dreiarm-Lauf mit erzwungenem Regime - das")
    print("  hier ist die deterministische Haelfte.")


if __name__ == "__main__":
    main()
