# -*- coding: utf-8 -*-
"""N-71 — WARUM dreht `turnover`? Der Grund, bevor ein Urteil faellt (07.09.)

## Die Vorgabe, unter der diese Datei steht

Nutzervorgabe 07.09., woertlich: *"bevor eine Bewertung faellt muessen wir
alles unternehmen - was ist der Grund und dass wir eine Loesung finden."*

**Ein Nullbefund ist eine ZERLEGUNG, kein Urteil.** N-70 hat gezeigt, DASS
`turnover` ab 2022 das Vorzeichen dreht (+0,0498 ganz, -0,0112 ab 2022,
-0,0307 ab 2024). Diese Datei fragt **warum** - und ob es zu reparieren
ist.

## ⚠️ Die erste Spur ist schon da, und sie ist ernst zu nehmen

Die Datenlage von `turnover` ist ueber die Zeit NICHT konstant:

    Jahr    Symbole in splycur    Werte je Kalendertag
    2019            49                  18,0
    2020            63                  32,1
    2021            64                  53,5
    2022            64                  57,0
    2025            63                  47,2

**In der starken Aera gab es halb so viele Werte je Tag.** Und die
Beitragsmessung laeuft auf der selektierten Menge - 20 % von 18 sind
**3,6 Anker je Tag.**

> N-65 hat gemessen, was bei so kleinen Gruppen passiert:
> `median(Gruppe) - median(alle)` ist nach oben verzerrt, und zwar um
> +0,10 bis +0,16 R - **groesser als jeder hier gesuchte Effekt.**

⚠️ Die Entzerrung faengt den Erwartungswert, **nicht die Streuung**. Bei
3,6 Ankern ist die Zahl auch entzerrt noch fast reines Rauschen - und
Rauschen mit grossem Betrag sieht aus wie ein starker Effekt.

## Die vier Erklaerungen, alle vorab benannt und unterscheidbar

    A  GRUPPENGROESSE  die fruehe Staerke ist Rauschen kleiner Gruppen.
                       -> dann muesste der Effekt mit der Zahl der Werte
                          je Tag zusammenhaengen, und auf der FREIEN
                          Menge (mehr Anker) schwaecher schwanken.
    B  DATENQUELLE     `splycur` hat sich geaendert (stehende Vorgabe:
                       auch die QUELLE pruefen, nicht nur die Methode).
                       -> dann muesste die Symbolmenge oder die
                          Werteverteilung springen.
    C  MARKTWANDEL     Umsatz je Umlaufmenge bedeutete 2019 etwas
                       anderes als 2025.
                       -> dann bliebe der Effekt auch bei GLEICHER
                          Gruppengroesse verschieden.
    D  NUR DAS OBERSTE das oberste Fuenftel dreht, die uebrigen nicht.
       FUENFTEL        -> dann waere die REGEL zu reparieren, nicht der
                          Beitrag zu streichen.

## Und die Loesungen, die daraus folgen wuerden

    zu A   `turnover` auf einer BREITEREN Menge beurteilen - seine
           Datenlage traegt die 20-%-Menge nicht. Das waere eine
           Aenderung an der MESSUNG, nicht am Beitrag.
    zu B   Quelle reparieren, neu messen.
    zu C   Tabelle auf der heutigen Aera neu herleiten.
    zu D   Regel umbauen (Schnitt verschieben statt Beitrag streichen).

⚠️ **R-R11 zuerst:** bevor irgendetwas gedeutet wird, muss die registrierte
Anlage (`pruefe_auswahl`) den Vorzeichenwechsel selbst zeigen. Tut sie es
nicht, misst N-70 etwas anderes und der ganze Befund faellt.

    python n71_turnover_warum.py
"""
from __future__ import annotations

import sys
import time

import numpy as np

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import messe_bewertungskennzahl as MB                        # noqa: E402
import messe_eigenschaft_beitrag as B                        # noqa: E402
import messe_funding_niveau as F                             # noqa: E402
import messe_kandidaten_als_regel as K                       # noqa: E402
import messe_regel_wirksamkeit as RW                         # noqa: E402
import messnorm as N                                          # noqa: E402
from messe_beitrag_auf_auswahl import (_auswahl_maske,       # noqa: E402
                                       momentum250)
from messnorm_auswahl import MENGEN, pruefe_auswahl          # noqa: E402
from n64_schnitt_stufen import band                          # noqa: E402
from n68_zeitstabilitaet import SAAT, ZIEH, entzerrte_reihe  # noqa: E402
from n69_traegt_er_heute_noch import band_ab                 # noqa: E402
from messnorm import _block                                   # noqa: E402

HORIZONT = 20
AERAS = (("frueh", "2019", "2022"), ("spaet", "2022", "2027"))


def teilwelt(je_tag: dict, von: str, bis: str) -> dict:
    return {t: z for t, z in je_tag.items() if von <= str(t) < bis}


def main() -> int:
    t0 = time.time()
    print("=" * 100)
    print("N-71 — WARUM dreht `turnover`? Grund suchen, bevor ein Urteil faellt")
    print("=" * 100)
    reihen = B.lade()
    mom = momentum250(reihen)
    lage = N.Lage(instrument="spot", strategie="einstieg")
    block = _block(HORIZONT)
    zus = {"turnover": MB.reihe("data/onchain_historie.db", "splycur"),
           "funding": F.lade_funding()}
    welt = {a: K.baue(reihen, a, zus.get(a), horizont=HORIZONT)
            for a in ("turnover", "funding", "zufall")}

    # ---- 0  R-R11: zeigt die REGISTRIERTE Anlage den Wechsel? ----------
    print()
    print("  0  ⚠️⚠️ R-R11 — zeigt `pruefe_auswahl` selbst den Wechsel?")
    print("     %-9s %-6s %-6s %10s %24s %8s  %s"
          % ("Kandidat", "Aera", "Menge", "Wirkung", "Band", "Tage", "Urteil"))
    rr11 = {}
    for art in ("turnover", "funding", "zufall"):
        for lab, von, bis in AERAS:
            for menge in ("frei", "20%"):
                teil = teilwelt(welt[art], von, bis)
                rng = np.random.default_rng(SAAT)
                try:
                    b = pruefe_auswahl(art, teil, mom, lage=lage, menge=menge,
                                       rng=rng, horizont=HORIZONT,
                                       hypothese="Aera-Zerlegung",
                                       verwendung="Beitrag")
                except Exception as exc:                     # noqa: BLE001
                    print("     %-9s %-6s %-6s -> %s"
                          % (art, lab, menge, str(exc)[:50]))
                    continue
                rr11[(art, lab, menge)] = b
                print("     %-9s %-6s %-6s %+10.4f [%+.4f .. %+.4f] %8d  %s"
                      % (art, lab, menge, b.wirkung, b.unten, b.oben,
                         b.n_tage, b.urteil.split(" (")[0][:34]), flush=True)
        print()

    # ---- A  GRUPPENGROESSE ---------------------------------------------
    print("  A  ERKLAERUNG A — haengt es an der GRUPPENGROESSE?")
    print("     %-9s %-6s %-6s %12s %12s"
          % ("Kandidat", "Aera", "Menge", "Werte/Tag", "Gewaehlt/Tag"))
    for art in ("turnover", "funding"):
        for lab, von, bis in AERAS:
            teil = teilwelt(welt[art], von, bis)
            for menge in ("frei", "20%"):
                anteil = MENGEN[menge]
                alle, gew = [], []
                for tag, z in teil.items():
                    if len(z) < 12:
                        continue
                    m = _auswahl_maske(z, mom.get(tag) or {}, anteil, None)
                    if m is None or not m.any():
                        continue
                    alle.append(len(z))
                    gew.append(int(m.sum()))
                if not gew:
                    continue
                print("     %-9s %-6s %-6s %12.1f %12.1f"
                      % (art, lab, menge, float(np.mean(alle)),
                         float(np.mean(gew))))
    print("     ⚠️ Unter rund 8 Ankern je Tag ist die Statistik Rauschen")
    print("        (N-65: die Verzerrung allein war +0,10 bis +0,16 R).")

    # ---- B  DATENQUELLE -------------------------------------------------
    print()
    print("  B  ERKLAERUNG B — hat sich die QUELLE geaendert?")
    sply = zus["turnover"]
    print("     %-6s %8s %10s %12s %12s"
          % ("Jahr", "Symbole", "Werte", "Median", "Streuung"))
    jw = {}
    for sym, r in sply.items():
        for tag, v in r.items():
            j = str(tag)[:4]
            jw.setdefault(j, []).append(float(v))
    for j in sorted(jw):
        v = np.array(jw[j], float)
        v = v[np.isfinite(v) & (v > 0)]
        if len(v) < 50:
            continue
        print("     %-6s %8d %10d %12.4g %12.4g"
              % (j, len({s for s in sply if any(str(t).startswith(j)
                                                for t in sply[s])}),
                 len(v), float(np.median(v)), float(np.std(v))))

    # ---- D  NUR DAS OBERSTE FUENFTEL? ----------------------------------
    print()
    print("  D  ERKLAERUNG D — dreht NUR das oberste Fuenftel?")
    print("     %-6s %-6s %9s %9s %9s %9s %9s"
          % ("Aera", "Menge", "F0", "F1", "F2", "F3", "F4"))
    for lab, von, bis in AERAS:
        teil = teilwelt(welt["turnover"], von, bis)
        for menge in ("frei", "20%"):
            anteil = MENGEN[menge]
            je = {k: {} for k in range(5)}
            for tag, z in teil.items():
                if len(z) < 12:
                    continue
                kz = np.array([x["kennzahl"] for x in z], float)
                y = np.array([x["in_r"] for x in z], float)
                r = RW.rang(kz)
                m = _auswahl_maske(z, mom.get(tag) or {}, anteil, None)
                if m is None or m.sum() < 5:
                    continue
                rw, yw = r[m], y[m]
                f = np.clip((rw * 5).astype(int), 0, 4)
                alle = float(np.median(yw))
                for k in range(5):
                    if (f == k).sum() >= 1:
                        je[k][tag] = float(np.median(yw[f == k])) - alle
            werte = []
            for k in range(5):
                e = band(je[k], block)
                werte.append(e[0] if e else float("nan"))
            print("     %-6s %-6s %+9.4f %+9.4f %+9.4f %+9.4f %+9.4f"
                  % (lab, menge, *werte), flush=True)
    print("     ⚠️ ROH, nicht entzerrt - der Vergleich laeuft zwischen den")
    print("        Aeren, und die Verzerrung trifft beide gleich, SOFERN")
    print("        die Gruppengroessen aehnlich sind. Spalte A sagt, ob.")

    print()
    print("  Dauer %.1f Minuten" % ((time.time() - t0) / 60.0))
    return 0


if __name__ == "__main__":
    sys.exit(main())
