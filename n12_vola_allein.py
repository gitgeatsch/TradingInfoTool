# -*- coding: utf-8 -*-
"""N12 — TRAEGT `vola` ALLEIN, und trennt es KURZ von LANG? (06.09.2026)

## Warum diese Frage

N8 hat gezeigt: der N5-Kombinationsvorteil braucht `turnover`, und der
liegt bei 7 von 57 beobachteten Werten vor. `vola` kommt aus der Kursreihe
und deckt ALLE ab. Die praktische Frage ist deshalb `vola` allein.

## Nutzervorgabe, die den zweiten Teil bestimmt

*"der Takt bzw. der Zeitgeber entscheidet heute oftmals - nicht die Frage
zum Zeitpunkt der Bewertung im Takt: ist jetzt auf Basis der Indikatoren,
Marktlage und der Bewertung fuer dieses eine Asset z.B. Hebel
wahrscheinlich die bessere Strategie."*

Und vom 01.09., woertlich: *"Hebel steil-kurz, Spot flach-lang."*

⚠️ Eine INSTRUMENT-Achse ist arithmetisch ausgeschlossen (H-1): gebuehren-
frei sind Hebel und Spot dasselbe Geschaeft, `R = Bewegung / stop_rel` -
der Hebel kuerzt sich heraus. Der einzige legitime Unterschied ist der
HORIZONT.

## ⚠️ Was H-1 dazu schon gemessen hat - und warum das hier nicht reicht

H-1 (01.09., 916.021 Anker) hat sechs Kursmerkmale geprueft, `vola`
darunter: **keines trennt steil-kurz von flach-lang.** Aber H-1 mass am
MITTELWERT - vor 2.112. Genau dieser Massstabswechsel hat am 06.09. zweimal
ein Vorzeichen gedreht.

**Die Frage ist also nicht neu, der MASSSTAB ist es.**

## Die drei Teile

    A  ABDECKUNG   `vola` allein - auf wie vielen Werten wirkt es?
    B  KOMPROMISS  Wirkung bei Sperrmengen 10/20/30/40 % - was kostet
                   welche Menge?
    C  STRATEGIE   trennt `vola` am RANDMASSSTAB kurz von lang?
                   Konstruktion wie H-1: K=3 (Hebel), L=20 (Spot),
                   Wahlregel statt Sperrregel, Anteil in der Zahl.

    python n12_vola_allein.py
"""
from __future__ import annotations

import sys
import time

import numpy as np

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import messe_eigenschaft_beitrag as B                        # noqa: E402
import messe_form_kurz_gegen_lang as H1                      # noqa: E402
import messe_kandidaten_als_regel as K                       # noqa: E402
import messnorm as N                                         # noqa: E402
import messnorm_rand as R                                    # noqa: E402
from messnorm import Lage                                    # noqa: E402

MARKE = 2.0
ST = (0.02, 0.05, 0.10, 0.20, 0.40)


def wahl_rand(je_tag, kandidat, mische=None, pflanze=0.0, anteil=0.20):
    """Die WAHL-Regel am Randmassstab — Spiegel von `H1.wahl_je_tag`.

    H-1 misst je Tag `Mittel(R_kurz - R_lang) x Anteil`. Hier stattdessen:

        Anteil der Gewaehlten, die KURZ ueber +MARKE kommen
        minus
        Anteil der Gewaehlten, die LANG ueber +MARKE kommen
        das Ganze x Anteil der Gewaehlten

    ⚠️ Gleiche Auswahl, gleiche Anteilsgewichtung, andere Zielgroesse.
    Positiv heisst: fuer die Gewaehlten lohnt der KURZE Horizont.
    """
    aus = {}
    for tag, z in je_tag.items():
        zeilen = [x for x in z
                  if x.get(kandidat) is not None
                  and x.get("r_kurz") is not None
                  and x.get("r_lang") is not None]
        if len(zeilen) < H1.MIN_JE_TAG:
            continue
        kz = np.array([float(x[kandidat]) for x in zeilen], float)
        rk = np.array([float(x["r_kurz"]) for x in zeilen], float)
        rl = np.array([float(x["r_lang"]) for x in zeilen], float)
        if mische is not None:
            kz = kz[mische.permutation(len(kz))]
        k = max(1, int(round(len(zeilen) * anteil)))
        oben = np.argsort(kz)[-k:]
        if pflanze:
            rk = rk.copy()
            rk[oben] += pflanze
        gew = float((rk[oben] > MARKE).mean() - (rl[oben] > MARKE).mean())
        aus[tag] = gew * (k / len(zeilen))
    return aus


def _band(d, rng, block, titel="x"):
    import contextlib
    import io
    import messe_bewertungskennzahl as MB
    with contextlib.redirect_stdout(io.StringIO()):
        return MB.urteil_tage(titel, d, rng, block)


def main() -> int:
    t0 = time.time()
    L = Lage("spot", "einstieg")
    print("Lade Reihen ...", flush=True)
    reihen = B.lade()

    # ---------------- A + B  vola allein als Sperre ---------------------
    vola = K.baue(reihen, "vola", None, horizont=5)
    syms = len({x["sym"] for z in vola.values() for x in z})
    print("  `vola` deckt %d Symbole an %d Tagen ab" % (syms, len(vola)),
          flush=True)

    print()
    print("=" * 104)
    print("A/B  `vola` ALLEIN als Sperre — was kostet welche Sperrmenge?")
    print("     (Rand > +%g R · H5 · volle Historie)" % MARKE)
    print("=" * 104)
    print("  %-18s %9s %9s %8s %5s  %s"
          % ("Sperrmenge", "WIRKUNG", "Reinheit", "gesperrt", "Blk", "Urteil"))
    for gr, lab in ((0.90, "10 %"), (0.80, "20 % (Bezug)"),
                    (0.70, "30 %"), (0.60, "40 %")):
        d, ant, ges, ueb = R.wirkung_rand(vola, True, marke=MARKE, grenze=gr)
        if not d:
            print("  %-18s   keine Tage" % lab); continue
        rng = np.random.default_rng(N.SAAT)
        f = R.pruefe_rand("vola", vola, lage=L, menge="frei", rng=rng,
                          marke=MARKE, horizont=5, staerken=ST, grenze=gr)
        u = ("TRAEGT" if f.traegt else
             "kein Befund" if f.trennschaerfe_in_r is None else
             "nicht trennbar" if abs(f.wirkung) >= (f.trennschaerfe or 0)
             else "traegt nicht")
        print("  %-18s %+9.5f %+9.5f %7.2f%% %5d  [%+.5f..%+.5f] %s"
              % (lab, f.wirkung,
                 float(np.mean(ueb)) - float(np.mean(ges)),
                 100 * float(np.mean(ant)), f.n_bloecke,
                 f.unten, f.oben, u), flush=True)

    # ---------------- C  die Strategiefrage -----------------------------
    print()
    print("=" * 104)
    print("C  TRENNT `vola` KURZ VON LANG?  (K=%d Hebel · L=%d Spot · "
          "Randmassstab)" % (H1.KURZ, H1.LANG))
    print("=" * 104)
    print("  ⚠️ H-1 hat dieselbe Frage am MITTELWERT gemessen (01.09., "
          "916.021 Anker):")
    print("     kein Kursmerkmal trennt steil-kurz von flach-lang, `vola` "
          "darunter.")
    print("     Hier derselbe Aufbau am RANDMASSSTAB.")
    print()
    print("  Lade H-1-Grundlage ...", flush=True)
    zusatz = H1.lade_zusatz()
    je_tag = H1.baue(reihen, zusatz)
    print("  %d Tage · %d Anker"
          % (len(je_tag), sum(len(z) for z in je_tag.values())), flush=True)

    block = N._block(H1.KURZ)
    rng = np.random.default_rng(N.SAAT)
    print()
    print("  %-26s %10s %24s  %s"
          % ("", "Wirkung", "Band", "Urteil"))
    echt = wahl_rand(je_tag, "vola")
    he = _band(echt, rng, block)
    print("  %-26s %+10.5f   [%+.5f .. %+.5f]"
          % ("vola waehlt KURZ", he["mittel"], he["unten"], he["oben"]))

    nu, no = [], []
    for z in range(N.ZIEHUNGEN):
        n0 = wahl_rand(je_tag, "vola",
                       mische=np.random.default_rng(N.SAAT + z))
        nb = _band(n0, rng, block)
        if nb:
            nu.append(nb["unten"]); no.append(nb["oben"])
    print("  %-26s %10s   [%+.5f .. %+.5f]"
          % ("Nullpunkt (5 Ziehungen)", "", min(nu), max(no)))

    treffer = {}
    for s in (0.5, 1.0, 2.0):
        g = 0
        for z in range(N.ZIEHUNGEN):
            p = wahl_rand(je_tag, "vola",
                          mische=np.random.default_rng(N.SAAT + 1000 * z),
                          pflanze=s)
            pb = _band(p, rng, block)
            if pb and pb["unten"] > 0:
                g += 1
        treffer[s] = g
    print("  Positivkontrolle (R auf den Gewaehlten): %s" % treffer)

    traegt = he["unten"] > max(0.0, max(no))
    maechtig = any(v >= 4 for v in treffer.values())
    print()
    print("  URTEIL: %s"
          % ("TRAEGT - `vola` waehlt den kurzen Horizont richtig" if traegt
             else ("traegt nicht" if maechtig
                   else "KEIN BEFUND - die Positivkontrolle schlaegt nicht an")))
    print()
    print("  Dauer %.1f Minuten" % ((time.time() - t0) / 60.0))
    return 0


if __name__ == "__main__":
    sys.exit(main())
