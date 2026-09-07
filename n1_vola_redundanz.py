# -*- coding: utf-8 -*-
"""N1 — TRAEGT `vola` UNABHAENGIG? (06.09.2026)

## Die Frage

`vola` traegt am Randmassstab auf allen drei Laeufen (Schritt 4a). Bevor er
registriert wird: ist er ein eigener Beitrag, oder traegt er nur, weil er
nebenbei `funding` oder `turnover` aussortiert?

## Die Vorpruefung ist durch

    V1  Abdeckung    vola ∩ funding  2.369 Tage · 157 Bloecke  ✔
                     vola ∩ turnover 2.287 Tage · 152 Bloecke  ✔
    V2  Richtung     oben sperren +0,00327 TRAEGT
                     unten sperren -0,00345 - spiegelbildlich negativ.
                     Ein echter Richtungseffekt, kein Streuungsartefakt.
    V3  Korrelation  vola/funding -0,082 · vola/turnover +0,046
                     (entlastet nicht, ordnet nur ein - H-4c)
    T1-T4            die Schichtentest-Spiegelung ist BITGENAU identisch
                     zum Original, die Pflanzung wirkt monoton, die
                     Faecher halten die Schicht fest (+0,0072)

## ⚠️ Der Aufbau — und warum er NICHT symmetrisch ist

Methodik 2.99 verlangt BEIDE Richtungen. Aber die Kandidaten leben auf
verschiedenen Massstaeben:

    vola      traegt am RAND, nicht am Mittel
    funding   traegt am MITTEL, nicht am Rand
    turnover  traegt am MITTEL

Jeder wird deshalb auf dem Massstab geprueft, auf dem er traegt. Das ist
kein Kunstgriff, sondern die Folge von 2.112: wer `vola` am Mittelwert
prueft, prueft ihn dort, wo er ohnehin nichts zeigt.

    Richtung C   vola INNERHALB funding / turnover      -> Rand > +2 R
    Richtung D   funding / turnover INNERHALB vola      -> Mittel

Zusaetzlich `vola` geschichtet am MITTEL - zur Vollstaendigkeit, weil die
Vorpruefung dort +0,0104 zeigte.

## Was die Antworten bedeuten

    C traegt UND D traegt   -> zwei eigene Beitraege, kaum Ueberlappung
    C traegt, D nicht       -> `vola` erklaert den anderen mit
    C nicht, D traegt       -> `vola` ist ein Mitlaeufer - NICHT registrieren
    beide nicht             -> die Faecher sind zu klein. Die Trennschaerfe
                               entscheidet, ob das eine Aussage ist

Dimensionierung nach 2.119: Horizont 5 · Block 15 · VOLLE Historie.

    python n1_vola_redundanz.py
"""
from __future__ import annotations

import sys
import time

import numpy as np

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import messe_bewertungskennzahl as MB                        # noqa: E402
import messe_eigenschaft_beitrag as B                        # noqa: E402
import messe_funding_niveau as F                             # noqa: E402
import messe_kandidaten_als_regel as K                       # noqa: E402
import messnorm as N                                         # noqa: E402
import messnorm_rand as R                                    # noqa: E402
from messnorm import Lage                                    # noqa: E402

HORIZONT = 5
STAERKEN = (0.02, 0.05, 0.10, 0.20)


def _schicht(je_tag: dict) -> dict:
    return {t: {x["sym"]: x["kennzahl"] for x in z} for t, z in je_tag.items()}


def _kurz(f) -> str:
    k = ("TRAEGT" if f.traegt else
         "kein Befund" if f.trennschaerfe_in_r is None else
         "nicht trennbar" if abs(f.wirkung) >= (f.trennschaerfe or 0)
         else "traegt nicht")
    return "%+9.5f [%+.5f .. %+.5f] · Null %+.5f · Trennsch. %s · %s" % (
        f.wirkung, f.unten, f.oben, f.nullpunkt,
        ("%.2f R" % f.trennschaerfe_in_r) if f.trennschaerfe_in_r else "KEINE",
        k)


def main() -> int:
    t0 = time.time()
    L = Lage("spot", "einstieg")
    print("Lade Reihen ...", flush=True)
    reihen = B.lade()
    fu = F.lade_funding()
    tu = MB.reihe("data/onchain_historie.db", "splycur")
    w = {"vola": K.baue(reihen, "vola", None, horizont=HORIZONT),
         "funding": K.baue(reihen, "funding", fu, horizont=HORIZONT),
         "turnover": K.baue(reihen, "turnover", tu, horizont=HORIZONT)}
    sch = {k: _schicht(v) for k, v in w.items()}
    print("  vola %d · funding %d · turnover %d Tage"
          % tuple(len(w[k]) for k in ("vola", "funding", "turnover")),
          flush=True)

    # --- Bezugswerte OHNE Schichtung -----------------------------------
    print()
    print("=" * 104)
    print("BEZUG — ohne Schichtung, Horizont %d, volle Historie" % HORIZONT)
    print("=" * 104)
    bezug = {}
    for name, marke, lab in (("vola", 2.0, "vola     Rand > +2 R"),
                             ("funding", None, "funding  Mittel    "),
                             ("turnover", None, "turnover Mittel    ")):
        rng = np.random.default_rng(N.SAAT)
        if marke is None:
            f = N.pruefe(name, w[name], lage=L, frageart="markt", zielgroesse="bewegung_r",
                         menge="frei", rng=rng, horizont=HORIZONT,
                         staerken=STAERKEN)
        else:
            f = R.pruefe_rand(name, w[name], lage=L, frageart="markt", menge="frei", rng=rng,
                              marke=marke, horizont=HORIZONT,
                              staerken=STAERKEN)
        bezug[name] = f
        print("  %s  %s" % (lab, _kurz(f)), flush=True)

    # --- Richtung C: vola INNERHALB der anderen ------------------------
    print()
    print("=" * 104)
    print("RICHTUNG C — traegt `vola`, wenn die andere Groesse FESTGEHALTEN"
          " wird?")
    print("=" * 104)
    for schichtname in ("funding", "turnover"):
        for marke, mlab in ((2.0, "Rand > +2 R"), (None, "Mittel     ")):
            rng = np.random.default_rng(N.SAAT)
            try:
                f = R.pruefe_geschichtet(
                    "vola in %s" % schichtname, w["vola"], sch[schichtname],
                    lage=L, frageart="markt", menge="frei", rng=rng, marke=marke,
                    horizont=HORIZONT, staerken=STAERKEN)
            except Exception as e:                           # noqa: BLE001
                print("  vola in %-9s %s  FEHLER: %s"
                      % (schichtname, mlab, e))
                continue
            print("  vola in %-9s %s  %s"
                  % (schichtname, mlab, _kurz(f)), flush=True)
            print("      %d Tage / %d Bloecke · Treffer %s"
                  % (f.n_tage, f.n_bloecke, f.protokoll.positiv_treffer))

    # --- Richtung D: die anderen INNERHALB von vola --------------------
    print()
    print("=" * 104)
    print("RICHTUNG D — tragen `funding` / `turnover`, wenn `vola` "
          "FESTGEHALTEN wird?")
    print("=" * 104)
    for name in ("funding", "turnover"):
        rng = np.random.default_rng(N.SAAT)
        try:
            f = R.pruefe_geschichtet(
                "%s in vola" % name, w[name], sch["vola"], lage=L, frageart="markt",
                menge="frei", rng=rng, marke=None, horizont=HORIZONT,
                staerken=STAERKEN)
        except Exception as e:                               # noqa: BLE001
            print("  %-9s in vola  FEHLER: %s" % (name, e))
            continue
        print("  %-9s in vola  Mittel       %s" % (name, _kurz(f)), flush=True)
        print("      %d Tage / %d Bloecke · Treffer %s"
              % (f.n_tage, f.n_bloecke, f.protokoll.positiv_treffer))

    print()
    print("=" * 104)
    print("WIE ZU LESEN")
    print("=" * 104)
    print("  C traegt UND D traegt   zwei eigene Beitraege, kaum Ueberlappung")
    print("  C traegt, D nicht       `vola` erklaert den anderen mit")
    print("  C nicht, D traegt       `vola` ist Mitlaeufer - NICHT registrieren")
    print("  beide nicht             erst die Trennschaerfe sagt, ob das")
    print("                          eine Aussage ist oder nur zu kleine Faecher")
    print()
    print("  Dauer %.1f Minuten" % ((time.time() - t0) / 60.0))
    return 0


if __name__ == "__main__":
    sys.exit(main())
