# -*- coding: utf-8 -*-
"""N-41f: TAUGT das Messgeraet? - Invarianzpruefung (05.09.2026)

## Der Anlass

Dieselbe Groesse, dreimal gemessen, drei Antworten:

    N-37  registrierte Stufen                     +0,056
    N-41  aus der Quote, THEORIE-Basis            +0,138
    N-41d aus der Quote, GEMESSENE Basis          +0,067

Die Basis ist eine additive Konstante. `wahrscheinlichkeit.rechne()` bildet
die Quote streng linear (`quote = basis + zuschlag/100`, kein Deckel), also
verschiebt eine andere Basis JEDEN Anker um denselben Betrag. **Eine
Regressionssteigung darf sich davon nicht aendern.**

## Der Verdacht

`baue_gruppen()` schluesselt nach `round(p.wert_r, 3)`. Die Gruppen sind
also GERUNDETE Absolutwerte - ein konstanter Versatz schneidet sie neu
(gemessen 33 gegen 34 Gruppen). Die Regression laeuft ueber diese Gruppen.

## Was hier geprueft wird - eine EIGENSCHAFT, keine Zahl

    Verschiebe ALLE Stufen um c. Die Steigung muss gleich bleiben.

Haelt das nicht, ist nicht die Basiswahl das Thema, sondern das Messgeraet -
und dann gilt keine der drei Zahlen oben.

⚠️ Zweiter Fund im selben Modul: `baue_gruppen()` benutzt im `pflanze`-Zweig
`abs(hash((sym, tag)))`. `hash()` ist fuer Zeichenketten PROZESSWEISE
zufaellig - die Positivkontrolle ist damit nicht reproduzierbar. Wird hier
mitgeprueft, aber nicht stillschweigend repariert.

    python pruefe_steigung_invarianz.py
"""
from __future__ import annotations

import sys

import numpy as np

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import messe_bewertungskennzahl as MB                       # noqa: E402
import messe_eigenschaft_beitrag as B                       # noqa: E402
import messe_funding_niveau as F                            # noqa: E402
import messe_kandidaten_als_regel as K                      # noqa: E402
import messe_zielregel as ZR                                # noqa: E402
import messe_bewertung_kalibrierung as MK                   # noqa: E402
from messe_bewertung_kalibrierung import (                  # noqa: E402
    _fuenftel_je_tag, _steigung, baue_gruppen, _mit_stufen)
from agent import wahrscheinlichkeit as W                   # noqa: E402

SAAT = 20260905


def _hash_reproduzierbar() -> bool:
    """⚠️ Ist `hash()` ueber Prozesse hinweg stabil? Nein, wenn PYTHONHASHSEED frei."""
    import subprocess
    ruf = [sys.executable, "-c", "print(hash(('BTC','2024-01-01')))"]
    a = subprocess.run(ruf, capture_output=True, text=True).stdout.strip()
    b = subprocess.run(ruf, capture_output=True, text=True).stdout.strip()
    print("  hash() in zwei Prozessen: %s / %s  ->  %s"
          % (a, b, "stabil" if a == b else "⚠️ ZUFAELLIG - Kontrolle nicht reproduzierbar"))
    return a == b


def main() -> int:
    print("=== BEFUND 2: reproduzierbarkeit von hash() im pflanze-Zweig ===")
    _hash_reproduzierbar()
    print()

    print("Lade Reihen...", flush=True)
    reihen = B.lade()
    tage_je_sym = {s: [z[0] for z in roh] for s, roh in reihen.items()}
    zeilen = ZR.ergebnisse(reihen)
    quellen = {"funding": F.lade_funding(),
               "turnover": MB.reihe("data/onchain_historie.db", "splycur")}
    f5 = {a: _fuenftel_je_tag(K.baue(reihen, a, quellen[a], horizont=20))
          for a in ("funding", "turnover")}
    alle = sorted(set(f5["funding"]) | set(f5["turnover"]))
    zweite = {t for t in alle if t >= alle[len(alle) // 2]}

    grund_f = next((b.stufen for b in W.BEITRAEGE
                    if b.merkmal == "funding_fuenftel" and b.stufen), [0.0] * 5)
    grund_t = next((b.stufen for b in W.BEITRAEGE
                    if b.merkmal == "turnover_fuenftel" and b.stufen), [0.0] * 5)

    print()
    print("=" * 92)
    print("BEFUND 1: aendert ein KONSTANTER Versatz die Steigung?")
    print("=" * 92)
    print("  Verschoben werden BEIDE Beitraege um denselben Betrag c.")
    print("  Die Rangfolge bleibt exakt gleich - nur das Niveau wandert.")
    print()
    alt = W.BEITRAEGE
    ergebnisse = []
    try:
        for c in (0.0, 0.5, 1.0, 2.0):
            W.BEITRAEGE = _mit_stufen([x + c for x in grund_f],
                                      [x + c for x in grund_t])
            rng = np.random.default_rng(SAAT)
            g = baue_gruppen(zeilen, tage_je_sym, f5["funding"], f5["turnover"],
                             nur_tage=zweite)
            print("  c = %+.1f Punkte · %d Gruppen" % (c, len(g)))
            _steigung(g, rng)
            ergebnisse.append(len(g))
            print()
    finally:
        W.BEITRAEGE = alt

    print("  ⚠️ LESEART")
    print("     Gruppenzahl und Steigung KONSTANT -> das Geraet taugt,")
    print("        und der Unterschied +0,138/+0,067 hat eine andere Ursache")
    print("     Sie WANDERN -> die Gruppierung nach round(wert_r, 3) macht")
    print("        die Steigung von einer willkuerlichen Konstante abhaengig.")
    print("        Dann gilt WEDER +0,056 NOCH +0,138 NOCH +0,067.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
