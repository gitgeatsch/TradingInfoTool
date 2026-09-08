# -*- coding: utf-8 -*-
"""N-78 — DIE VIER TERMINMARKT-KANAELE unter der Norm (N-9, 07.09.2026)

## Was schon bekannt ist — und warum es die Frage NICHT beantwortet

N-17b (F-205) hat die Kanaele bereits gemessen, aber gegen
**FRONTLOADING**:

    oi_je_umsatz   traegt        long_bias   traegt
    top_bias       traegt        taker_bias  traegt NICHT
    long_bias ~ top_bias   Spearman 0,955 - praktisch dieselbe Groesse

⚠️ **Frontloading ist eine andere Zielgroesse als `bewegung_r`.** Ein
Kandidat, der die Frontloading-Quote verschiebt, muss deshalb nicht das
Ergebnis verbessern. Genau diese Verwechslung hat F-207 schon einmal
erzeugt ("die Kombination verbessert die LIVE-Sperre NICHT - andere
Zielgroesse als F-206").

> **Offen ist also: tragen sie auf `bewegung_r`, unter der Norm, auf
> ihrer ZULAESSIGEN Menge?**

## ⚠️ Und die Frage, die daneben steht: Redundanz zur eigenen Quelle

`oi_aenderung` ist bereits registriert und kommt aus **derselben**
Terminmarkt-Quelle. Ein neuer Kanal von dort nuetzt nur, wenn er etwas
anderes sagt.

    Spearman INNERHALB der Auswahl - nicht im vollen Querschnitt.
    Nur die erste Zahl beschreibt, was an Stufe 12 passiert (N-66).

## Der Aufbau — mit den Lehren dieses Tages

    Menge        `zulaessige_mengen()` je Kandidat, und das Urteil muss
                 ueber ALLE davon halten (N-73: `schnitt` traegt nur auf
                 einer von vier - das ist ein Befund, kein Mengenproblem)
    Zielgroesse  bewegung_r, H20
    Kontrolle    `zufall` mitgemessen; `oi_aenderung` als bekannte
                 Referenz - er MUSS tragen, sonst stimmt der Aufbau nicht

⚠️ `oi_wert` roh ist zwischen Assets **nicht vergleichbar** - das sagt
`messe_kandidaten_als_regel` in eigener Sache. Gemessen wird deshalb
`oi_je_umsatz`, das Verhaeltnis zum Tagesumsatz.

⚠️ `long_bias` und `top_bias` laufen BEIDE mit, obwohl sie mit 0,955
korrelieren - damit die Redundanz auf dieser Zielgroesse reproduziert
wird, statt sie zu unterstellen.

    python n78_terminmarkt_kanaele.py
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
import messnorm_auswahl as MA                                # noqa: E402
from messe_beitrag_auf_auswahl import (_auswahl_maske,       # noqa: E402
                                       momentum250)

HORIZONT = 20
NEU = ("oi_je_umsatz", "long_bias", "top_bias", "taker_bias")
REFERENZ = ("oi_aenderung", "zufall")


def kurz(u: str) -> str:
    return u.split(" (")[0].split(" - ")[0][:26]


def main() -> int:
    t0 = time.time()
    print("=" * 104)
    print("N-78 — die vier Terminmarkt-Kanaele auf `bewegung_r`, unter der Norm")
    print("=" * 104)
    reihen = B.lade()
    mom = momentum250(reihen)
    lage = N.Lage(instrument="spot", strategie="einstieg")
    tm = K.lade_terminmarkt()
    zus = {"oi_aenderung": tm["oi_aenderung"],
           "oi_je_umsatz": tm["oi_wert"],       # ⚠️ roh nicht vergleichbar
           "long_bias": tm["long_bias"],
           "top_bias": tm["top_bias"],
           "taker_bias": tm["taker_bias"],
           "funding": F.lade_funding(),
           "turnover": MB.reihe("data/onchain_historie.db", "splycur")}

    welt = {}
    print("  %-14s %8s %10s %10s   %s"
          % ("Kandidat", "Symbole", "Tage", "Werte/Tag", "zulaessige Mengen"))
    zul = {}
    for a in NEU + REFERENZ:
        try:
            je = K.baue(reihen, a, zus.get(a), horizont=HORIZONT)
        except Exception as exc:                             # noqa: BLE001
            print("  %-14s -> %s" % (a, str(exc)[:60]))
            continue
        if not je:
            print("  %-14s -> leere Welt" % a)
            continue
        welt[a] = je
        zul[a] = MA.zulaessige_mengen(je, mom, horizont=HORIZONT)
        syms = len({x["sym"] for z in je.values() for x in z})
        print("  %-14s %8d %10d %10.1f   %s"
              % (a, syms, len(je),
                 float(np.mean([len(z) for z in je.values()])),
                 ", ".join(zul[a]) or "⚠️ KEINE"), flush=True)

    # ---- 1  DIE MESSUNG ueber ALLE zulaessigen Mengen ------------------
    print()
    print("  1  DAS URTEIL — ueber ALLE zulaessigen Mengen (N-73)")
    print("     %-14s %-6s %10s %22s  %s"
          % ("Kandidat", "Menge", "Wirkung", "Band", "Urteil"))
    erg = {}
    for a in NEU + REFERENZ:
        if a not in welt:
            continue
        for m in zul.get(a, []):
            rng = np.random.default_rng(20260907)
            try:
                b = MA.pruefe_auswahl(a, welt[a], mom, lage=lage, menge=m,
                                      rng=rng, horizont=HORIZONT,
                                      hypothese="N-9 Terminmarkt-Kanaele",
                                      verwendung="Beitrag")
            except Exception as exc:                         # noqa: BLE001
                print("     %-14s %-6s -> %s" % (a, m, str(exc)[:44]))
                continue
            erg[(a, m)] = b
            print("     %-14s %-6s %+10.4f [%+.4f .. %+.4f]  %s"
                  % (a, m, b.wirkung, b.unten, b.oben, kurz(b.urteil)),
                  flush=True)
        print()

    # ---- 2  REDUNDANZ zu den registrierten drei ------------------------
    print("  2  ⚠️ REDUNDANZ — INNERHALB der Auswahl, nicht im Querschnitt")
    for a in ("funding", "turnover"):
        if a not in welt:
            welt[a] = K.baue(reihen, a, zus.get(a), horizont=HORIZONT)
    anteil = MA.MENGEN["20%"]
    print("     %-14s %10s %10s %14s"
          % ("Kandidat", "funding", "turnover", "oi_aenderung"))
    for a in NEU:
        if a not in welt:
            continue
        zeile = []
        for gegen in ("funding", "turnover", "oi_aenderung"):
            r = []
            gt = {t: {x["sym"]: x["kennzahl"] for x in z}
                  for t, z in welt[gegen].items()}
            for tag, z in welt[a].items():
                g = gt.get(tag)
                if not g:
                    continue
                m = _auswahl_maske(z, mom.get(tag) or {}, anteil, None)
                if m is None or m.sum() < 8:
                    continue
                p = [(x["kennzahl"], g.get(x["sym"]))
                     for x, keep in zip(z, m) if keep and x["sym"] in g]
                if len(p) < 8:
                    continue
                u = RW.rang(np.array([x[0] for x in p], float))
                w = RW.rang(np.array([x[1] for x in p], float))
                if u.std() > 0 and w.std() > 0:
                    r.append(float(np.corrcoef(u, w)[0, 1]))
            zeile.append(float(np.mean(r)) if r else float("nan"))
        print("     %-14s %+10.3f %+10.3f %+14.3f" % (a, *zeile), flush=True)
    # ⚠️ Und die Redundanz der beiden Bias-Kanaele UNTEREINANDER -
    # N-17b hat 0,955 gemessen, das gehoert reproduziert.
    if "long_bias" in welt and "top_bias" in welt:
        gt = {t: {x["sym"]: x["kennzahl"] for x in z}
              for t, z in welt["top_bias"].items()}
        r = []
        for tag, z in welt["long_bias"].items():
            g = gt.get(tag)
            if not g:
                continue
            p = [(x["kennzahl"], g.get(x["sym"])) for x in z if x["sym"] in g]
            if len(p) < 12:
                continue
            u = RW.rang(np.array([x[0] for x in p], float))
            w = RW.rang(np.array([x[1] for x in p], float))
            if u.std() > 0 and w.std() > 0:
                r.append(float(np.corrcoef(u, w)[0, 1]))
        print()
        print("     ⚠️ long_bias gegen top_bias: %+.3f  (N-17b: +0,955) - %s"
              % (float(np.mean(r)),
                 "REPRODUZIERT" if abs(float(np.mean(r)) - 0.955) < 0.10
                 else "WEICHT AB"))

    # ---- Urteil ---------------------------------------------------------
    print()
    print("=" * 104)
    print("WAS DAS HEISST")
    print("=" * 104)
    zf = [erg[(a, m)] for (a, m) in erg if a == "zufall"]
    if any(b.traegt for b in zf):
        print("  ⚠️⚠️ `zufall` traegt auf einer Menge - Aufbau kaputt.")
        return 1
    print("  ✔ `zufall` traegt auf keiner zulaessigen Menge.")
    oi = [erg[(a, m)] for (a, m) in erg if a == "oi_aenderung"]
    print("  Referenz `oi_aenderung`: %s"
          % (", ".join("%s %+.4f" % (m, erg[("oi_aenderung", m)].wirkung)
                       for (a, m) in erg if a == "oi_aenderung")))
    print()
    for a in NEU:
        mengen = [m for (x, m) in erg if x == a]
        if not mengen:
            print("  %-14s nicht messbar" % a)
            continue
        traegt = [m for m in mengen if erg[(a, m)].traegt]
        print("  %-14s traegt auf %d von %d zulaessigen Mengen%s"
              % (a, len(traegt), len(mengen),
                 " (%s)" % ", ".join(traegt) if traegt else ""))
    print()
    print("  ⚠️ Ein Kandidat, der nur auf EINER von mehreren zulaessigen")
    print("     Mengen traegt, ist nicht robust - das ist die Lehre aus")
    print("     N-73 und sie gilt hier genauso.")
    print("  Dauer %.1f Minuten" % ((time.time() - t0) / 60.0))
    return 0


if __name__ == "__main__":
    sys.exit(main())
