# -*- coding: utf-8 -*-
"""N25 — TRAGEN `funding` UND `turnover` RICHTUNG? Dieselbe Probe wie N24 (06.09.)

## ⚠️⚠️ Warum das JETZT kommt — der Punkt, den ich nicht zu Ende gedacht hatte

N24 hat gezeigt: die **Barrieren-Quote** mischt zwei Dinge, die nichts
miteinander zu tun haben —

    Aufloesungsquote   loest der Anker in der Frist ueberhaupt auf?
                       (ein flacher Auslauf zaehlt als 0, genau wie ein Stop)
    Richtung           und WENN er aufloest, nach welcher Seite?

Bei `vola` war der ganze Befund der erste Kanal. Richtungsrein blieb nichts.

**`funding` und `turnover` sind auf DERSELBEN Barrieren-Quote gemessen und
registriert worden.** Ob ihr Befund richtungsrein ist, wurde nie geprueft.
Sie stehen also auf einem Massstab, der bei der dritten Groesse
nachweislich getaeuscht hat.

⚠️ Das ist KEINE Behauptung, dass sie fallen. Es ist die Feststellung, dass
   die Frage offen ist - und dass `wahrscheinlichkeit.BEITRAEGE` sie heute
   live beantwortet, ohne dass jemand sie gestellt hat.

## Was gemessen wird — alle drei durch dasselbe Verfahren

    G0    Barrieren-Quote CRV 2 auf heutiger ATR   (die REGISTRIERTE Form)
    GS    symmetrisch, nur aufgeloeste Anker       ⚠️ ENTSCHEIDET
          -> Nullpunkt vorab herleitbar bei 0,5, unabhaengig von der Vola
    AUF   die Aufloesungsquote selbst              -> der Artefaktkanal
    G0R   Treffer unter den Aufgeloesten           -> der Rest
    VZ/B  Vorzeichen und `bewegung_r`              ⚠️ kontaminiert, ohne Stimme

**Die entscheidende Diagnose ist AUF.** Traegt eine Groesse dort nichts,
dann lief ihr G0-Befund NICHT ueber den Artefaktkanal - und die
Registrierung war sauber, auch wenn der Massstab unglücklich gewaehlt war.

## Vorabtest (`--probe`) — zwei Kunstwelten, beide mit dem Grenzfall

    Welt N  die Kennzahl ist REINES RAUSCHEN, ohne jeden Bezug
            Erwartung: NICHTS traegt, auch AUF nicht
    Welt V  die Kennzahl ist ein Abbild der VOLATILITAET, sonst nichts
            Erwartung: G0 und AUF feuern (der Artefakt), GS NICHT
            ⚠️ Das ist der Nachweis, dass die Probe den Kanal findet,
               den sie finden soll.

    python n25_richtungsprobe_alle_drei.py --probe
    python n25_richtungsprobe_alle_drei.py
"""
from __future__ import annotations

import sys
import time

import numpy as np

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import messe_bewertungskennzahl as MB                        # noqa: E402
import messe_eigenschaft_beitrag as B                        # noqa: E402
import messe_funding_niveau as F                             # noqa: E402
# ⚠️ Die Mechanik wird IMPORTIERT, nicht kopiert - ein Test, der eine
# Kopie prueft, prueft nicht den Code (stehende Vorgabe).
from n24_vola_geometrieprobe import (MASSSTAEBE, band,        # noqa: E402
                                     drittel, kontrolle, regel,
                                     traegt, _ausgang, MISCHUNGEN)

CRV, BRUCH, HORIZONT = 2.0, 5.0, 5
VORLAUF = 260


def baue(reihen, zusatz, art):
    """je Tag: Kennzahl + alle Massstaebe. `art='vola'` rechnet sie selbst."""
    je_tag: dict = {}
    for sym, z in reihen.items():
        tage = [x[0] for x in z]
        c = np.array([x[1] for x in z], float)
        h = np.array([x[2] for x in z], float)
        t = np.array([x[3] for x in z], float)
        br = B.spanne(h, t, c, B.SCHWANKUNG)
        vh = c[1:] / np.maximum(c[:-1], 1e-12)
        bruch = (vh > BRUCH) | (vh < 1.0 / BRUCH)
        je_sym = (zusatz or {}).get(sym.upper()) or {}
        # ⚠️ VORLAUF NUR BEI `vola` - sonst waere die Ankermenge bei
        # funding/turnover kuenstlich beschnitten und nicht mehr die,
        # auf der registriert wurde.
        start = max(B.SCHWANKUNG, VORLAUF) if art == "vola" else B.SCHWANKUNG
        for i in range(start, len(c) - HORIZONT):
            if not np.isfinite(br[i]) or br[i] <= 0:
                continue
            if bruch[i:i + HORIZONT].any():
                continue
            if art == "vola":
                med = float(np.median(br[i - 250:i + 1]))
                if not np.isfinite(med) or med <= 0:
                    continue
                kz = float(br[i] / med)
                nenner = med
            else:
                w = je_sym.get(tage[i])
                if w is None:
                    continue
                kz = float(w)
                nenner = float(br[i])
            roh = _ausgang(c, h, t, i, float(br[i]), CRV)
            sym_aus = _ausgang(c, h, t, i, float(br[i]), 1.0)
            rend = float(c[i + HORIZONT] - c[i])
            je_tag.setdefault(tage[i], []).append({
                "kennzahl": kz,
                "g0": 1.0 if roh > 0 else 0.0,
                "ewr": (CRV if roh > 0 else -1.0 if roh < 0
                        else rend / float(br[i])),
                "auf": 0.0 if roh == 0 else 1.0,
                "g0r": None if roh == 0 else (1.0 if roh > 0 else 0.0),
                "gs": (1.0 if sym_aus > 0 else 0.0) if sym_aus != 0 else None,
                "vz": 1.0 if rend > 0 else 0.0,
                "bewegung_r": rend / nenner})
    return {t: z for t, z in je_tag.items() if len(z) >= 20}


def zeige(je_tag, titel):
    print()
    print("  %s  (%d Tage, %d Anker)"
          % (titel, len(je_tag), sum(len(z) for z in je_tag.values())))
    print("     %-28s %10s %24s  %s"
          % ("Massstab", "Regel", "Band", "Kontrolle"))
    erg = {}
    for feld, lab, _b in MASSSTAEBE:
        bb = band(regel(je_tag, feld))
        if not bb:
            print("     %-28s   zu wenige Tage" % lab)
            continue
        k = kontrolle(je_tag, feld, bb[0])
        tr = traegt(bb, k)          # ⚠️ ZWEISEITIG - siehe n24.traegt()
        print("     %-28s %+9.5f [%+.5f .. %+.5f]  %d von %d %s"
              % (lab, bb[0], bb[1], bb[2], k, MISCHUNGEN,
                 "✔ TRAEGT" if tr else ""), flush=True)
        erg[feld] = (bb[0], bb[1], tr)
    for feld, lab, _b in (("gs", "GS", 0), ("auf", "AUF", 0),
                          ("ewr", "EWR", 0)):
        d = drittel(je_tag, feld)
        print("     %-28s %s" % ("Drittel " + lab, "  ".join(
            "%+.4f" % (band(x)[0] if band(x) else float("nan")) for x in d)))
    return erg


# ------------------------------------------------------------- Kunstwelten
def kunstwelt(kennzahl_art, tage=1400, symbole=45, saat=5150):
    """Zufallslauf mit Volatilitaetsclustern, KEINE Richtungsinformation.

    kennzahl_art = "rauschen"  die Kennzahl hat mit nichts zu tun
                 = "vola"      die Kennzahl BILDET die Volatilitaet ab
                               (der Artefaktkanal, kuenstlich hergestellt)
    """
    rng = np.random.default_rng(saat)
    reihen, zusatz = {}, {}
    for s in range(symbole):
        lv = np.zeros(tage)
        for i in range(1, tage):
            lv[i] = 0.97 * lv[i - 1] + rng.normal(0, 0.10)
        vol = 0.03 * np.exp(lv)
        c = np.empty(tage)
        c[0] = 100.0
        for i in range(1, tage):
            c[i] = c[i - 1] * float(np.exp(rng.normal(0, vol[i])
                                           - 0.5 * vol[i] ** 2))
        spanne = c * vol
        h = c + np.abs(rng.normal(0, 0.6, tage)) * spanne
        t = c - np.abs(rng.normal(0, 0.6, tage)) * spanne
        nam = "K%02d" % s
        reihen[nam] = [(("2020-01-01_%04d" % i), c[i], h[i], t[i], 1.0)
                       for i in range(tage)]
        if kennzahl_art == "rauschen":
            w = rng.normal(0, 1, tage)
        else:
            # ⚠️ 1:1 die Volatilitaet, leicht verrauscht - so sieht eine
            # Groesse aus, die NUR ueber den Artefaktkanal wirken kann.
            w = vol * (1.0 + rng.normal(0, 0.05, tage))
        zusatz[nam] = {("2020-01-01_%04d" % i): float(w[i])
                       for i in range(tage)}
    return reihen, zusatz


def main() -> int:
    t0 = time.time()
    probe = "--probe" in sys.argv
    print("=" * 92)
    print("N25 — tragen `funding` und `turnover` RICHTUNG?")
    print("=" * 92)

    if probe:
        ok = True
        r, z = kunstwelt("rauschen")
        wn = zeige(baue(r, z, "extern"),
                   "WELT N — Kennzahl ist REINES RAUSCHEN (nichts darf tragen)")
        r, z = kunstwelt("vola", saat=7373)
        wv = zeige(baue(r, z, "extern"),
                   "WELT V — Kennzahl BILDET DIE VOLATILITAET AB "
                   "(⚠️ G0/AUF muessen feuern, GS nicht)")
        print()
        print("  URTEIL DES VORABTESTS")
        stumm = [f for f in ("g0", "gs", "auf")
                 if not wn.get(f, (0, 0, False))[2]]
        if len(stumm) == 3:
            print("     ✔ bei reinem Rauschen traegt NICHTS (G0, GS, AUF)")
        else:
            print("     ⚠️ bei reinem Rauschen feuert etwas: %s"
                  % ", ".join(f for f in ("g0", "gs", "auf") if f not in stumm))
            ok = False
        if wv.get("auf", (0, 0, False))[2]:
            print("     ✔ und die Probe FINDET den Artefaktkanal (AUF %+.5f)"
                  % wv["auf"][0])
        else:
            print("     ⚠️ die Probe findet den Artefaktkanal NICHT (AUF "
                  "%+.5f) - dann kann sie ihn auch nicht ausschliessen"
                  % wv.get("auf", (0.0,))[0])
            ok = False
        if not wv.get("gs", (0, 0, False))[2]:
            print("     ✔ und GS bleibt stumm, wo nur der Kanal wirkt "
                  "(%+.5f)" % wv.get("gs", (0.0,))[0])
        else:
            print("     ⚠️⚠️ GS feuert auf reinem Volatilitaetsabbild "
                  "(%+.5f) - GS waere dann selbst kontaminiert"
                  % wv["gs"][0])
            ok = False
        print("     %s" % ("Der Test darf auf die echten Daten."
                           if ok else
                           "⚠️ NICHT auf die echten Daten - erst reparieren."))
        print("  Dauer %.1f Minuten" % ((time.time() - t0) / 60.0))
        return 0 if ok else 1

    print("  Lade Reihen ...", flush=True)
    reihen = B.lade()
    quellen = (("funding", F.lade_funding(), "extern"),
               ("turnover", MB.reihe("data/onchain_historie.db", "splycur"),
                "extern"),
               ("vola", None, "vola"))
    erg = {}
    for name, quelle, art in quellen:
        erg[name] = zeige(baue(reihen, quelle, art), name.upper())

    print()
    print("=" * 92)
    print("DIE ZUSAMMENSCHAU — wer traegt RICHTUNG, wer nur den Kanal?")
    print("=" * 92)
    print("     %-10s %11s %11s %11s %11s   %s"
          % ("Groesse", "G0 (regist.)", "GS (Rchtg)", "AUF (Kanal)",
             "EWR (Ertrag)", "Urteil"))
    for name in ("funding", "turnover", "vola"):
        e = erg[name]
        g0 = e.get("g0", (0.0, 0.0, False))
        gs = e.get("gs", (0.0, 0.0, False))
        au = e.get("auf", (0.0, 0.0, False))
        ew = e.get("ewr", (0.0, 0.0, False))
        if gs[2] and gs[0] > 0:
            u = "✔ traegt RICHTUNG - echter Beitrag"
        elif gs[2]:
            u = "⚠️ traegt Richtung, aber INVERS - Orientierung falsch"
        elif au[2]:
            u = "⚠️ nur der Kanal - gehoert in die GEOMETRIE"
        else:
            u = "⚠️ weder Richtung noch Kanal - unerklaert"
        print("     %-10s %+11.5f %+11.5f %+11.5f %+11.5f   %s"
              % (name, g0[0], gs[0], au[0], ew[0], u))
    print()
    print("  ⚠️⚠️ EWR IST DIE PROBE AUFS EXEMPEL. Die Trefferquote zaehlt")
    print("     einen flachen Auslauf wie einen Stop. Wer nur die")
    print("     AUFLOESUNG hebt, wandelt Flache in Aufloesungen um - deren")
    print("     Erwartungswert bei CRV 2 und ohne Richtung ist NULL")
    print("     (1/3 x +2 R + 2/3 x -1 R). Er hebt die QUOTE, nicht den")
    print("     ERTRAG. Wer hier nichts bringt, gehoert nicht in die")
    print("     Bewertung - egal wie gut er in der Quote aussieht.")
    print()
    print("  ⚠️ GS entscheidet (Nullpunkt vorab herleitbar). AUF ist die")
    print("     Diagnose: traegt eine Groesse dort nichts, lief ihr")
    print("     G0-Befund NICHT ueber den Artefaktkanal.")
    print("  Dauer %.1f Minuten" % ((time.time() - t0) / 60.0))
    return 0


if __name__ == "__main__":
    sys.exit(main())
