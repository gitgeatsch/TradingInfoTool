# -*- coding: utf-8 -*-
"""SCHRITT 3 - DER RANDMASSSTAB, und ob er Trennschaerfe hat (06.09.2026)

## Warum es dieses Modul gibt

Methodik 2.112 hat gemessen, dass unser Markt einen negativen Median hat
(-0,19 R ueber 5 Tage, 2024-2026) und den Ertrag im OBEREN RAND (6,65 % der
Asset-Tage ueber +2 R). In so einem Markt beantwortet die
Mittelwertverschiebung eine andere Frage als die, die wir stellen.

2.115 hat es dann belegt: derselbe Schnitt, zwei Massstaebe,
entgegengesetztes Vorzeichen.

    am MITTELWERT   "tief im Rang und gefallen ist schlechter"
    am RANDMASS     "tief im Rang und gefallen ist BESSER"
                    (+0,0068, Band [+0,0034 , +0,0108], Kontrolle sauber)

## Was hier NICHT behauptet wird

Dass das Randmass besser ist. Ein Randmass hat WENIGER Ereignisse und
damit potentiell weniger Trennschaerfe. Das entscheidet die Messung.

## Der faire Vergleich

Beide Massstaebe bekommen dieselbe koerperliche Pflanzung:

    y[gesperrt] -= s          (s in R)

und beantworten dieselbe Frage: ab welchem s findet dieses Werkzeug den
Effekt? Die Trennschaerfe ist damit fuer BEIDE in R und direkt
vergleichbar - auch wenn die gemessene Wirkung in verschiedenen Einheiten
steht (R gegen Anteilspunkte).

## Trennung von der alten Kette

Dieses Modul AENDERT `messe_regel_wirksamkeit` nicht. Es spiegelt dessen
`wirkung()` mit derselben Rang- und Sperrlogik (`W.rang`, `W.GRENZE`) und
ruft fuer das Band dieselbe Funktion (`M.urteil_tage`). Keine Nachbildung
der Statistik, keine Kopie der alten Logik.

    python messnorm_rand.py        # Selbsttest auf Kunstdaten
"""
from __future__ import annotations

import sys

import numpy as np

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:                                            # noqa: BLE001
    pass

import messe_bewertungskennzahl as M                         # noqa: E402
import messe_regel_wirksamkeit as W                          # noqa: E402
import messnorm as N                                         # noqa: E402
from messnorm import Befund, Lage, Protokoll, SAAT, ZIEHUNGEN  # noqa: E402

# Die Marken, an denen der Rand gemessen wird. +2 R ist der Alltag
# (6,65 % der Asset-Tage), +3 R der schaerfere Schnitt.
MARKEN = (2.0, 3.0)


def _zielgroesse(marke: float) -> str:
    return "randanteil_%gr" % marke


# Die Norm laesst nur registrierte Zielgroessen zu (`Befund.__post_init__`).
# Hier werden sie eingetragen - MIT Einheit, weil die Wirkung nicht in R
# steht, die Trennschaerfe aber schon.
for _m in MARKEN:
    N.ZIELGROESSEN.setdefault(_zielgroesse(_m), {
        "text": "Anteil der Anker mit Bewegung ueber +%g R" % _m,
        "gilt_fuer": "alle Lagen",
        "einheit": "Anteilspunkte",
        "begruendung": (
            "der Ertrag liegt im oberen Rand, nicht im Mittel (2.112): "
            "Median -0,19 R, aber 6,65 % der Asset-Tage ueber +2 R. Eine "
            "Mittelwertverschiebung kann null sein, waehrend die Randquote "
            "steigt - gemessen in 2.115."),
    })


def wirkung_rand(je_tag: dict, oben_sperren: bool = True, mische=None,
                 pflanze: float = 0.0, marke: float = 2.0) -> tuple:
    """Je Kalendertag: Randanteil MIT Regel minus Randanteil OHNE.

    Exakt die Bauform von `messe_regel_wirksamkeit.wirkung`, nur die
    Kennzahl des Tages ist eine andere: statt des Medians der Anteil ueber
    der Marke. Rang, Sperrgrenze und Pflanzrichtung sind DIESELBEN - sie
    werden aus `W` bezogen, nicht nachgebaut.
    """
    aus, anteil, gesperrt, uebrig = {}, [], [], []
    for tag, z in je_tag.items():
        w = np.array([x["kennzahl"] for x in z])
        y = np.array([x["in_r"] for x in z])
        r = W.rang(w)
        if mische is not None:
            r = mische.permutation(r)
        frei = (r < W.GRENZE) if oben_sperren else (r >= 1.0 - W.GRENZE)
        if frei.sum() < 3 or (~frei).sum() < 1:
            continue
        # Pflanzung auf die GESPERRTEN - wie im Original, und aus demselben
        # Grund (die Freien sind 80 % des Vergleichs und fraessen den
        # eigenen Effekt).
        y2 = y.copy()
        if pflanze:
            y2[~frei] -= pflanze
        aus[tag] = float((y2[frei] > marke).mean() - (y2 > marke).mean())
        anteil.append(float((~frei).mean()))
        gesperrt.append(float((y[~frei] > marke).mean()))
        uebrig.append(float((y[frei] > marke).mean()))
    return aus, anteil, gesperrt, uebrig


def pruefe_rand(kandidat: str, je_tag: dict, *, lage: Lage, menge: str, rng,
                marke: float = 2.0, horizont: int = 5,
                staerken: tuple = (0.02, 0.05, 0.10, 0.20),
                hypothesen: int = 1, oben_sperren: bool = True,
                still: bool = True) -> Befund:
    """Dieselbe Pruefung wie `messnorm.pruefe`, am Randmass.

    Rueckgabe ist ein echter `Befund` - er durchlaeuft dieselben
    Pflichtpruefungen (Protokoll, Positivkontrolle, Tagesklammer, Kosten
    null) und liefert dieselben vier Urteile.
    """
    block = N._block(horizont)

    def _band(d, titel):
        if still:
            import contextlib
            import io
            with contextlib.redirect_stdout(io.StringIO()):
                return M.urteil_tage(titel, d, rng, block)
        return M.urteil_tage(titel, d, rng, block)

    d, _a, _g, _u = wirkung_rand(je_tag, oben_sperren, marke=marke)
    haupt = _band(d, kandidat)
    if haupt is None:
        raise ValueError("zu wenige Tage fuer ein Band (%d)" % len(d))

    nullwerte, nullunten, nulloben = [], [], []
    for z in range(ZIEHUNGEN):
        n0, _a2, _g2, _u2 = wirkung_rand(
            je_tag, oben_sperren, mische=np.random.default_rng(SAAT + z),
            marke=marke)
        nb = _band(n0, "null %d" % z)
        if nb:
            nullwerte.append(nb["mittel"])
            nullunten.append(nb["unten"])
            nulloben.append(nb["oben"])
    null = {"mittel": float(np.mean(nullwerte)) if nullwerte else 0.0,
            "unten": float(np.min(nullunten)) if nullunten else 0.0,
            "oben": float(np.max(nulloben)) if nulloben else 0.0}

    # ⚠️ ZWEI GROESSEN, NICHT EINE (06.09., vom Vorabtest gefunden).
    #
    # Gepflanzt wird in R, gemessen wird in ANTEILSPUNKTEN. `urteil`
    # vergleicht die Wirkung gegen die Trennschaerfe - das geht nur in
    # derselben Einheit. Deshalb:
    #
    #   trennschaerfe        die gemessene Wirkung bei der kleinsten
    #                        gefundenen Pflanzung  -> Anteilspunkte
    #   trennschaerfe_in_r   die gepflanzte Staerke selbst -> R, und damit
    #                        die einzige Groesse, die ZWISCHEN den
    #                        Massstaeben vergleichbar ist
    trennschaerfe, trennschaerfe_in_r, treffer = None, None, {}
    for s in sorted(staerken):
        gefunden, werte = 0, []
        for z in range(ZIEHUNGEN):
            misch = np.random.default_rng(SAAT + 1000 * z + int(s * 1000))
            p, _a3, _g3, _u3 = wirkung_rand(
                je_tag, oben_sperren, mische=misch, pflanze=s, marke=marke)
            pb = _band(p, "pflanze %.2f/%d" % (s, z))
            if pb:
                werte.append(pb["mittel"])
                if pb["unten"] > 0:
                    gefunden += 1
        treffer[s] = gefunden
        if trennschaerfe_in_r is None and gefunden >= max(3, (4 * ZIEHUNGEN) // 5):
            trennschaerfe_in_r = s
            trennschaerfe = float(np.mean(werte)) if werte else None

    n_anker = sum(len(z) for z in je_tag.values())
    syms = len({x["sym"] for z in je_tag.values() for x in z})
    return Befund(
        kandidat=kandidat, lage=lage, zielgroesse=_zielgroesse(marke),
        menge=menge, wirkung=haupt["mittel"], unten=haupt["unten"],
        oben=haupt["oben"], nullpunkt=null["mittel"],
        null_unten=null["unten"], null_oben=null["oben"],
        trennschaerfe=trennschaerfe, trennschaerfe_in_r=trennschaerfe_in_r,
        gepflanzt=tuple(sorted(staerken)),
        n_anker=n_anker, n_tage=haupt["tage"],
        n_bloecke=max(1, haupt["tage"] // block), abdeckung_symbole=syms,
        hypothesen=hypothesen,
        protokoll=Protokoll(
            wirkung_funktion=("messnorm_rand.wirkung_rand (Marke +%g R)"
                              % marke),
            band_funktion="messe_bewertungskennzahl.urteil_tage",
            null_konstruktion="Raenge je Tag gemischt",
            null_ziehungen=ZIEHUNGEN,
            positiv_konstruktion="in die gemischte Welt gepflanzt, "
                                 "auf die Gesperrten",
            positiv_ziehungen=ZIEHUNGEN, positiv_treffer=treffer,
            blocklaenge=block, saat=SAAT))


# --------------------------------------------------------- Kunstwelten
def _welt_nur_rand(rng, tage=2400, syms=60, breite_gesperrt=0.60):
    """Eine Welt, in der NUR der Rand einen Unterschied macht.

    Der Grenzfall, den dieses Modul betrifft - und deshalb der wichtigste
    Vorabtest (stehende Vorgabe: vor langen Laeufen auf Kunstdaten pruefen,
    INKLUSIVE dem Grenzfall, den die Korrektur betrifft).

        die obersten 20 % nach Kennzahl ziehen aus N(0, breite_gesperrt)
        alle anderen aus N(0, 1)

    Median und Mittelwert sind in BEIDEN Gruppen null - der Mittelwert-
    massstab darf hier NICHTS finden. Der Randanteil unterscheidet sich
    dagegen stark: P(X > 2) ist 2,3 % gegen 0,00 % bei Breite 0,60.
    """
    je_tag = {}
    grenze = int(round(syms * 0.80))
    for t in range(tage):
        ks = [float(rng.random()) for _ in range(syms)]
        ordnung = sorted(range(syms), key=lambda i: ks[i])
        z = []
        for platz, i in enumerate(ordnung):
            sd = breite_gesperrt if platz >= grenze else 1.0
            z.append({"sym": "S%02d" % i, "kennzahl": ks[i],
                      "in_r": float(rng.normal(0, sd))})
        je_tag["t%04d" % t] = z
    return je_tag


def selbsttest() -> bool:
    """Drei Welten - und die dritte ist der eigentliche Test."""
    print("=" * 96)
    print("SELBSTTEST DES RANDMASSSTABS")
    print("=" * 96)
    ok = True
    L = Lage("spot", "einstieg")
    rng = np.random.default_rng(SAAT)

    print()
    print("1. LEERE WELT - kein Effekt. BEIDE Massstaebe muessen schweigen.")
    leer = N._welt(np.random.default_rng(1), tage=2400, syms=60, effekt=0.0)
    a = N.pruefe("leer/mittel", leer, lage=L, zielgroesse="bewegung_r",
                 menge="frei", rng=rng, horizont=5)
    b = pruefe_rand("leer/rand", leer, lage=L, menge="frei", rng=rng,
                    marke=2.0, horizont=5)
    for lab, f in (("Mittel", a), ("Rand  ", b)):
        gut = not f.traegt
        ok &= gut
        print("   %s %s  %s" % (lab, "OK " if gut else "FEHLER",
                                f.urteil.split(" (")[0]))

    print()
    print("2. VERSCHIEBUNG im Mittel (0,10 R) - eine reine Lageaenderung.")
    print("   ⚠️ Die erste Fassung verlangte hier, dass BEIDE ihn finden.")
    print("      Das war eine falsche Erwartung, und der Test hat sie")
    print("      gefangen: eine Verschiebung um 0,10 R bewegt den Anteil")
    print("      ueber +2 R nur um rund 0,10 Prozentpunkte. Der Rand MUSS")
    print("      hier schwaecher sein - das ist gemessen, kein Fehler.")
    stark = N._welt(np.random.default_rng(2), tage=2400, syms=60, effekt=0.10)
    a = N.pruefe("stark/mittel", stark, lage=L, zielgroesse="bewegung_r",
                 menge="frei", rng=rng, horizont=5)
    b = pruefe_rand("stark/rand", stark, lage=L, menge="frei", rng=rng,
                    marke=2.0, horizont=5)
    ok &= a.traegt                       # NUR der Mittelwert ist Pflicht
    for lab, f in (("Mittel", a), ("Rand  ", b)):
        print("   %s  Wirkung %+.4f  %s"
              % (lab, f.wirkung, f.urteil.split(" (")[0]))

    print()
    print("3. DER GRENZFALL - Unterschied NUR im Rand, Median identisch.")
    print("   Erwartung: der Mittelwert findet NICHTS, der Rand FINDET es.")
    nur = _welt_nur_rand(np.random.default_rng(3), tage=2400, syms=60)
    a = N.pruefe("nurrand/mittel", nur, lage=L, zielgroesse="bewegung_r",
                 menge="frei", rng=rng, horizont=5)
    b = pruefe_rand("nurrand/rand", nur, lage=L, menge="frei", rng=rng,
                    marke=2.0, horizont=5)
    print("   Mittel %s  Wirkung %+.4f R      %s"
          % ("(schweigt, richtig)" if not a.traegt else "(FINDET - FEHLER)",
             a.wirkung, a.urteil.split(" (")[0]))
    print("   Rand   %s  Wirkung %+.4f Anteil %s"
          % ("(findet, richtig)  " if b.traegt else "(schweigt - FEHLER)",
             b.wirkung, b.urteil.split(" (")[0]))
    ok &= (not a.traegt) and b.traegt

    print()
    print("4. DIE TRENNSCHAERFE NEBENEINANDER - dieselbe Pflanzung in R")
    leer2 = N._welt(np.random.default_rng(7), tage=2400, syms=60, effekt=0.0)
    st = (0.02, 0.05, 0.10, 0.20, 0.40)
    am = N.pruefe("ts/mittel", leer2, lage=L, zielgroesse="bewegung_r",
                  menge="frei", rng=rng, horizont=5, staerken=st)
    print("   Mittel       kleinste gefundene Pflanzung: %s"
          % (("%.2f R" % am.trennschaerfe_in_r)
             if am.trennschaerfe_in_r else "KEINE bis 0,40 R"))
    print("                Treffer je Staerke: %s" % am.protokoll.positiv_treffer)
    for mk in MARKEN:
        br = pruefe_rand("ts/rand%g" % mk, leer2, lage=L, menge="frei",
                         rng=rng, marke=mk, horizont=5, staerken=st)
        print("   Rand > +%g R  kleinste gefundene Pflanzung: %s"
              % (mk, ("%.2f R" % br.trennschaerfe_in_r)
                 if br.trennschaerfe_in_r else "KEINE bis 0,40 R"))
        print("                Treffer je Staerke: %s"
              % br.protokoll.positiv_treffer)

    print()
    print("=" * 96)
    print("SELBSTTEST %s" % ("BESTANDEN" if ok else "FEHLGESCHLAGEN"))
    print("=" * 96)
    return ok


if __name__ == "__main__":
    sys.exit(0 if selbsttest() else 1)
