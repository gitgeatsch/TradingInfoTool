# -*- coding: utf-8 -*-
"""Funding in der RICHTIGEN Form: Niveau statt Veraenderung (30.08.2026).

## Warum nicht die Veraenderung

Die Durchsicht vom 30.08. hat drei Messungen mit falscher Form gefunden - TVL,
aktive Adressen und Funding. Bei Funding lautet die Praxislesart:

    Hohes positives Funding = viele Longs zahlen fuer ihre Position
                            = ueberhitzte Positionierung
                            = KONTRAindikator fuer weitere Aufwaertsbewegung

Das ist ein NIVEAU, keine Veraenderung. Gemessen wird deshalb der Querschnitt:
welches Asset hat heute das niedrigste Funding im Vergleich zu den anderen.

## Leserichtung

    Median(niedrigstes Funding) minus Median(hoechstes Funding)

Ein POSITIVER Wert bestaetigt die Praxislesart: wo wenig fuer Longs gezahlt
wird, laeuft es besser.

## Vorab festgelegt

  traegt        Bootstrap ueber Bloecke von Kalendertagen (Block > Horizont!)
                schliesst die Null nicht ein, beide Haelften gleiches Vorzeichen,
                Negativkontrolle bei null
  traegt nicht  sonst
"""
import sqlite3, statistics as st, sys
import numpy as np
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import messe_bewertungskennzahl as M
import messe_eigenschaft_beitrag as B

def lade_funding():
    c = sqlite3.connect("file:data/funding_historie.db?mode=ro", uri=True)
    aus = {}
    for s, t, w in c.execute("SELECT symbol, datum, wert FROM funding"):
        aus.setdefault(str(s).upper(), {})[str(t)[:10]] = float(w)
    c.close()
    return aus

def baue(reihen, funding, horizont, form="niveau", fenster=90):
    je_tag = {}
    for sym, roh in reihen.items():
        f = funding.get(sym.upper())
        if not f or len(f) < fenster + 30:
            continue
        tage = [z[0] for z in roh]
        schluss = np.array([z[1] for z in roh])
        hoch = np.array([z[2] for z in roh]); tief = np.array([z[3] for z in roh])
        breite = B.spanne(hoch, tief, schluss, B.SCHWANKUNG)
        sortiert = sorted(f); lage = {t: i for i, t in enumerate(sortiert)}
        for i in range(60, len(schluss) - horizont):
            r = breite[i]
            if not np.isfinite(r) or r <= 0 or tage[i] not in lage:
                continue
            j = lage[tage[i]]
            if j < fenster:
                continue
            jetzt = f[sortiert[j]]
            if form == "niveau":
                wert = jetzt
            else:                       # Perzentil in der eigenen Historie
                davor = [f[sortiert[k]] for k in range(j - fenster, j)]
                wert = sum(1 for x in davor if x < jetzt) / len(davor)
            je_tag.setdefault(tage[i], []).append({
                "sym": sym, "kennzahl": wert,
                "in_r": float((schluss[i + horizont] - schluss[i]) / r)})
    return {t: z for t, z in je_tag.items() if len(z) >= 10}

def main():
    reihen = B.lade(); funding = lade_funding()
    rng = np.random.default_rng(20260830)
    print("=" * 92)
    print("FUNDING-RATE — Niveau und Perzentil (die Praxisformen)")
    print("=" * 92)
    print("Gelesen: NIEDRIGES Funding minus HOHES. Positiv = Praxislesart bestaetigt.")
    print("Fremdreihe: %d Symbole" % len(funding))
    for horizont in (5, 20):
        for form in ("niveau", "perzentil"):
            je_tag = baue(reihen, funding, horizont, form)
            if not je_tag:
                print("\nHORIZONT %d / %s: keine Ueberschneidung" % (horizont, form))
                continue
            n = sum(len(z) for z in je_tag.values())
            syms = len({x["sym"] for z in je_tag.values() for x in z})
            print()
            print("-" * 92)
            print("HORIZONT %d — %s — %d Anker, %d Symbole, %d Kalendertage"
                  % (horizont, form.upper(), n, syms, len(je_tag)))
            print("-" * 92)
            block = max(90, horizont * 3)
            M.urteil_tage("niedrig minus hoch", M.je_tag_quer(je_tag), rng, block)
            M.urteil_tage("Negativkontrolle (gemischt)",
                          M.je_tag_quer(je_tag, rng), rng, block)
            tage = sorted(je_tag); mitte = tage[len(tage)//2]
            M.urteil_tage("davon erste Haelfte",
                          M.je_tag_quer({t: z for t, z in je_tag.items() if t < mitte}),
                          rng, block)
            M.urteil_tage("davon zweite Haelfte",
                          M.je_tag_quer({t: z for t, z in je_tag.items() if t >= mitte}),
                          rng, block)
            if horizont == 20:
                for s in (0.05, 0.10):
                    M.urteil_tage("Positivkontrolle %+.2f R" % s,
                                  M.je_tag_quer(je_tag, pflanze=s), rng, block)


if __name__ == "__main__":
    main()
