# -*- coding: utf-8 -*-
"""N-17b: sind die tragenden Kandidaten unabhängig, oder messen sie
dasselbe zweimal? (04.09.2026)

## Warum

Vorbedingung für jede Kombinationsmessung (Nutzervorgabe 04.09.:
*"auch wenn eine bestimmte Kombination keine Aussage hat... sollten
diese Indikatoren mit anderen in Kombination gemessen werden"* —
[[feedback_indikatoren_auch_in_kombination_pruefen]]). Zwei Kandidaten,
die stark korrelieren, "bestätigen" sich in einer Kombination nur
scheinbar und zählen denselben Effekt doppelt. Dieselbe Prüfung wie
F-165 (dort: momentum_kurz/schnitt50 ρ=0,364, alle übrigen ≤0,09) -
hier auf die ELF tragenden Kandidaten aus dem N-17b-Lauf erweitert.

## Vorabfestlegung

    Frage      Wie stark korrelieren die Kandidaten, die im N-17b-Lauf
               tragen, PAARWEISE untereinander?
    Massstab   Spearman-Rangkorrelation, INNERHALB jedes Kalendertags
               berechnet (Tagesklammer - dieselbe Groesse, auf der die
               ganze Messung aufbaut), dann der MEDIAN ueber alle Tage
               berichtet (robust gegen einzelne Tage mit wenigen
               Symbolen).
    Schwelle   |ρ| < 0,2 gilt als unabhaengig genug fuer eine
               Kombination, |ρ| >= 0,2 als redundant (dieselbe
               Groessenordnung wie F-165s Trennung 0,09 gegen 0,364).

    python messe_kandidaten_redundanz.py [--selbsttest]
"""
from __future__ import annotations

import statistics as st
import sys

import numpy as np

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import messe_eigenschaft_beitrag as B                          # noqa: E402
import messe_form_kurz_gegen_lang as FL                        # noqa: E402

# ⚠️ VORAB BENANNT: alle Kandidaten, die im N-17b-Lauf vom 04.09. in
# MINDESTENS einer Richtung "TRAEGT" zeigten (nach dem Krypto-Filter-Fix,
# F-204). Nicht alle KANDIDATEN aus messe_form_kurz_gegen_lang.py - nur
# die tragenden, denn nur sie kommen fuer eine Kombination in Frage.
TRAGENDE = ("vola", "momentum_kurz", "spanne_aus", "schnitt50", "funding",
            "turnover", "funding_extrem", "er_rueck", "adx", "choppiness",
            "varianzverh", "oi_aenderung", "oi_je_umsatz", "long_bias",
            "top_bias", "rsi")


def _rang(werte: list[float]) -> np.ndarray:
    r = np.argsort(np.argsort(np.asarray(werte, float)))
    return r / max(len(r) - 1, 1)


def _spearman(x: np.ndarray, y: np.ndarray) -> float | None:
    if np.std(x) == 0 or np.std(y) == 0:
        return None
    return float(np.corrcoef(x, y)[0, 1])


def matrix(je_tag: dict, kandidaten: tuple) -> dict:
    """Je Kandidatenpaar: Liste der Tageskorrelationen (nur Tage, an denen
    BEIDE Kandidaten fuer genug Symbole vorliegen)."""
    aus = {(a, b): [] for i, a in enumerate(kandidaten)
           for b in kandidaten[i + 1:]}
    for tag, zeilen in je_tag.items():
        werte = {k: [] for k in kandidaten}
        for z in zeilen:
            for k in kandidaten:
                if k in z:
                    werte[k].append((id(z), z[k]))
        for i, a in enumerate(kandidaten):
            if len(werte[a]) < 15:
                continue
            ids_a = dict(werte[a])
            for b in kandidaten[i + 1:]:
                if len(werte[b]) < 15:
                    continue
                ids_b = dict(werte[b])
                gemeinsam = sorted(set(ids_a) & set(ids_b))
                if len(gemeinsam) < 15:
                    continue
                xa = _rang([ids_a[i2] for i2 in gemeinsam])
                xb = _rang([ids_b[i2] for i2 in gemeinsam])
                r = _spearman(xa, xb)
                if r is not None:
                    aus[(a, b)].append(r)
    return aus


def bericht(aus: dict) -> list[tuple]:
    zeilen = []
    for (a, b), werte in aus.items():
        if len(werte) < 30:
            continue
        zeilen.append((a, b, st.median(werte), len(werte)))
    zeilen.sort(key=lambda z: -abs(z[2]))
    return zeilen


def selbsttest() -> bool:
    """Kunstdaten: ein Paar mit garantierter Redundanz (b = a + wenig
    Rauschen), ein Paar unabhaengig (b = eigener Zufallswert). Muss beide
    richtig unterscheiden."""
    rng = np.random.default_rng(11)
    je_tag = {}
    for tag in range(300):
        n = 40
        a = rng.normal(size=n)
        zeilen = []
        for i in range(n):
            zeilen.append({"a": float(a[i]),
                           "b_redundant": float(a[i] + rng.normal(0, 0.1)),
                           "c_unabhaengig": float(rng.normal())})
        je_tag[f"tag{tag}"] = zeilen
    aus = matrix(je_tag, ("a", "b_redundant", "c_unabhaengig"))
    r_redundant = st.median(aus[("a", "b_redundant")])
    r_unabhaengig = st.median(aus[("a", "c_unabhaengig")])
    print(f"  redundantes Paar: ρ={r_redundant:+.3f} (erwartet nahe +1)")
    print(f"  unabhaengiges Paar: ρ={r_unabhaengig:+.3f} (erwartet nahe 0)")
    ok = r_redundant > 0.8 and abs(r_unabhaengig) < 0.2
    print("  ✔ Selbsttest bestanden" if ok else "  ✖ SELBSTTEST FEHLGESCHLAGEN")
    return ok


def main():
    if "--selbsttest" in sys.argv:
        return 0 if selbsttest() else 1

    print("Lade Reihen und baue Anker (dieselbe Basis wie N-17b)...",
          flush=True)
    reihen = B.lade()
    zusatz = FL.lade_zusatz()
    je_tag = FL.baue(reihen, zusatz)
    print(f"{len(je_tag)} Kalendertage")
    print()
    aus = matrix(je_tag, TRAGENDE)
    zeilen = bericht(aus)
    print("=" * 78)
    print("PAARWEISE RANGKORRELATION DER TRAGENDEN KANDIDATEN (Median je Tag)")
    print("=" * 78)
    print("  %-16s %-16s %8s   %s" % ("Kandidat A", "Kandidat B", "ρ", "Tage"))
    for a, b, r, n in zeilen:
        marke = "  ⚠️ REDUNDANT" if abs(r) >= 0.2 else ""
        print("  %-16s %-16s %+.3f    %4d%s" % (a, b, r, n, marke))
    print()
    redundant = [(a, b, r) for a, b, r, n in zeilen if abs(r) >= 0.2]
    if redundant:
        print(f"  ⚠️ {len(redundant)} Paar(e) mit |ρ| >= 0,2 — vor einer "
              "Kombination diese Paare NICHT als unabhaengige Bestaetigung "
              "werten.")
    else:
        print("  ✔ Kein Paar erreicht |ρ| >= 0,2 - alle tragenden "
              "Kandidaten sind fuer eine Kombination unabhaengig genug.")


if __name__ == "__main__":
    sys.exit(main())
