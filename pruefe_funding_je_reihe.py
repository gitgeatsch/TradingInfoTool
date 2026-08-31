# -*- coding: utf-8 -*-
"""Funding in der JE-REIHE-Sicht (30.08.2026).

## Die Frage

Der Befund vom 30.08. ist ein QUERSCHNITT: "welches Asset hat heute das
niedrigste Funding im Vergleich zu den anderen". Offen blieb:

    Traegt Funding auch INNERHALB eines Assets ueber die Zeit? Also: ist
    dieses Asset ein besserer Kauf, wenn SEIN Funding niedrig steht -
    gemessen an seiner eigenen Historie?

Das ist die praktisch wichtigere Frage, wenn man ein einzelnes Asset bewertet
und keinen Querschnitt zur Verfuegung hat.

## ⚠️ DER FALLSTRICK, der die Messung sonst wertlos macht

Bei der Je-Reihe-Sicht ist die MARKTLAGE NICHT festgehalten. Wenn ein Symbol
niedriges Funding hat, ist meist der ganze Markt in einer Baerphase - und dann
misst man Markt-Timing, nicht Asset-Bewertung. Deshalb zwei Varianten:

    ROH             Funding-Perzentil in der eigenen Historie (250 Tage).
                    Markt NICHT kontrolliert - das Ergebnis kann Markt-Timing
                    sein.
    MARKTBEREINIGT  Funding MINUS Median aller Symbole desselben Tages.
                    Nur die asset-eigene Abweichung bleibt uebrig.

⚠️ Traegt nur die rohe Variante, ist der Befund Markt-Timing. Traegt auch die
marktbereinigte, ist er asset-eigen - und das ist die Anforderung des Nutzers
("die Bewertung soll NUR fuer das EINE Asset erfolgen").

## Vorab festgelegt

  traegt asset-eigen   die MARKTBEREINIGTE Variante ist von null zu trennen
                       (Bootstrap ueber die Symbole), beide Haelften gleiches
                       Vorzeichen, Negativkontrolle bei null
  nur Markt-Timing     nur die rohe Variante traegt
  traegt nicht         keine von beiden
"""
import statistics as st
import sys

import numpy as np

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import messe_eigenschaft_beitrag as B
import messe_funding_niveau as F

HORIZONT = 20
FENSTER = 250          # eigene Historie fuer das Perzentil
MIND_JE_TERZIL = 40


def baue(reihen, funding):
    """Je Symbol eine Liste: (Tag, rohes Funding, Bewegung in R)."""
    je_sym, je_tag_werte = {}, {}
    for sym, roh in reihen.items():
        f = funding.get(sym.upper())
        if not f or len(f) < FENSTER + 100:
            continue
        tage = [z[0] for z in roh]
        c = np.array([z[1] for z in roh])
        h = np.array([z[2] for z in roh])
        t_ = np.array([z[3] for z in roh])
        breite = B.spanne(h, t_, c, B.SCHWANKUNG)
        eintraege = []
        for i in range(60, len(c) - HORIZONT):
            r = breite[i]
            if not np.isfinite(r) or r <= 0 or tage[i] not in f:
                continue
            eintraege.append((tage[i], f[tage[i]],
                              float((c[i + HORIZONT] - c[i]) / r)))
        if len(eintraege) >= 3 * MIND_JE_TERZIL:
            je_sym[sym] = eintraege
            for tag, wert, _ in eintraege:
                je_tag_werte.setdefault(tag, []).append(wert)
    markt = {t: st.median(v) for t, v in je_tag_werte.items()}
    return je_sym, markt


def perzentile(werte):
    """Rollierendes Perzentil in der eigenen Historie."""
    aus = []
    for i, w in enumerate(werte):
        if i < FENSTER:
            aus.append(None)
            continue
        davor = werte[i - FENSTER:i]
        aus.append(sum(1 for x in davor if x < w) / len(davor))
    return aus


def je_symbol(je_sym, markt, bereinigt, mische=None):
    """Je Symbol: Median(niedrigstes Terzil) minus Median(hoechstes)."""
    aus = {}
    for sym, eintraege in je_sym.items():
        werte = [(w - markt[t]) if bereinigt else w for t, w, _ in eintraege]
        ziel = [z for _, _, z in eintraege]
        p = perzentile(werte)
        paare = [(q, y) for q, y in zip(p, ziel) if q is not None]
        if len(paare) < 3 * MIND_JE_TERZIL:
            continue
        q = np.array([a for a, _ in paare])
        y = np.array([b for _, b in paare])
        if mische is not None:
            q = mische.permutation(q)
        tief = y[q <= 1 / 3.0]
        hoch = y[q >= 2 / 3.0]
        if len(tief) >= MIND_JE_TERZIL and len(hoch) >= MIND_JE_TERZIL:
            aus[sym] = float(np.median(tief) - np.median(hoch))
    return aus


def urteil(titel, werte, rng):
    if len(werte) < 10:
        print("    %-32s zu wenige Symbole (%d)" % (titel, len(werte)))
        return
    w = np.array(list(werte.values()))
    n = len(w)
    boot = np.array([w[rng.integers(0, n, n)].mean() for _ in range(20000)])
    u, o = np.quantile(boot, [0.025, 0.975])
    print("    %-32s %+.4f R  [%+.4f .. %+.4f]  %3d/%3d Symbole +  %s"
          % (titel, w.mean(), u, o, int((w > 0).sum()), n,
             "TRAEGT" if u > 0 else ("UMGEKEHRT" if o < 0 else "nicht trennbar")))


def main():
    reihen = B.lade()
    funding = F.lade_funding()
    je_sym, markt = baue(reihen, funding)
    rng = np.random.default_rng(20260830)
    print("=" * 88)
    print("FUNDING — JE-REIHE-SICHT  (Horizont %d, eigene Historie %d Tage)"
          % (HORIZONT, FENSTER))
    print("=" * 88)
    print("Gelesen: eigenes Funding NIEDRIG minus HOCH. Positiv = Praxislesart.")
    print("%d Symbole mit genug Historie" % len(je_sym))
    print()
    print("  ROH — Marktlage NICHT kontrolliert")
    urteil("niedrig minus hoch", je_symbol(je_sym, markt, False), rng)
    urteil("Negativkontrolle", je_symbol(je_sym, markt, False, rng), rng)
    print()
    print("  MARKTBEREINIGT — nur die asset-eigene Abweichung")
    urteil("niedrig minus hoch", je_symbol(je_sym, markt, True), rng)
    urteil("Negativkontrolle", je_symbol(je_sym, markt, True, rng), rng)
    print()
    print("  Zeitstabilitaet der marktbereinigten Variante")
    for name, anteil in (("erste Haelfte", 0), ("zweite Haelfte", 1)):
        teil = {}
        for sym, e in je_sym.items():
            h = len(e) // 2
            teil[sym] = e[:h] if anteil == 0 else e[h:]
        urteil(name, je_symbol(teil, markt, True), rng)


if __name__ == "__main__":
    main()
