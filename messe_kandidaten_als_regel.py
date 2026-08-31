# -*- coding: utf-8 -*-
"""Die fuenf Kandidaten, jeder als REGEL gerechnet (30.08.2026).

Ruft `messe_regel_wirksamkeit.bericht()` fuer jeden Kandidaten auf. Die
Merkmale werden hier gebaut, die Wirksamkeitsrechnung liegt dort - so gilt
fuer alle derselbe Massstab.

## Die Kandidaten und ihre Datenlage

  1 TURNOVER    Volumen / Umlaufmenge         66 Symbole (Umlaufmenge noetig)
  2 AMIHUD      |Rendite| / Umsatz            523 Symbole - nur Kursdaten
  3 MOMENTUM    12 Monate ohne den letzten    523 Symbole - nur Kursdaten
  4 FUNDING     Niveau, Querschnitt           290 Symbole - KONTROLLE, muss
                                              +0,024 R reproduzieren
  5 OI / MC     ⚠️ NICHT MESSBAR - Binance liefert Open Interest nur 30 Tage
                rueckwirkend (geprueft 30.08.), eine eigene Reihe gibt es
                erst seit 14.07. und sie ist unterbrochen
  6 VOLA-PRAEMIE ⚠️ NICHT OHNE WEITERES - implizite Volatilitaet gibt es bei
                Deribit nur fuer BTC und ETH; zwei Symbole sind kein
                Querschnitt

## ⚠️ Kandidat 4 ist die eingebaute Kontrolle

Funding ist bereits als Regel gerechnet (+0,0242 R). Weicht das Ergebnis hier
ab, stimmt etwas am gemeinsamen Werkzeug nicht - dann gilt kein Befund dieses
Laufs.

---

# ERWEITERUNG 31.08.2026 — DIE HORIZONTACHSE (Umbau Schritt 1)

⚠️ DIESER ABSCHNITT IST DIE VORABFESTLEGUNG, geschrieben BEVOR gerechnet wurde.

## Warum

Der Umbau gibt jedem Asset mehrere ZELLEN aus (Instrument x Strategie). Die
drei tragenden Beitraege sind aber alle auf **H20** gemessen - zwanzig
Handelstage. Fuer `hebel x einstieg` ist das die falsche Geometrie:

    Nutzervorgabe 31.08.   Hebel ist ein kurzfristiger Trade, 1-20 Tage
    System plante          mindestziel_zeitraum_tage_geschaetzt 1,2-2,1 Tage

⚠️ **NICHT gemessen wird die realisierte Haltedauer.** Aus 188 echten
Bitpanda-Positionen liesse sich ein Median von 0,29 Tagen ableiten - aber das
sind 11 Symbole, davon TAO allein 84, und es ist NUTZERVERHALTEN. Wer das
misst, misst, wann jemand ausgestiegen ist, nicht ob die Empfehlung trug.
Fallstrick F5 im Umsetzungsplan.

## Vorab festgelegt - was als Befund gilt

    traegt auf H       Regelwirkung > 0 UND ausserhalb des Placebo-Bandes
                       UND die Positivkontrolle findet den gepflanzten Effekt
    traegt NICHT       sonst
    ⚠️ nicht uebertragbar  traegt auf H20, aber nicht auf H1..H5
                           -> dann darf der Beitrag fuer `hebel` NICHT
                              registriert werden (Fallstrick F4:
                              "leeres Feld als Erlaubnis lesen")

## ⚠️ DER SUCHPREIS — EINE Zelle entscheidet, nicht achtzehn

Sechs Horizonte mal drei Beitraege sind **18 Zellen**. Frei durchsucht waere
die Huerde +20,5 Punkte, eine vorab benannte kostet +10,2 (Methodik 2.49).
Deshalb wird sie hier benannt, VOR dem Lauf:

    ENTSCHEIDEND IST  H2

Begruendung aus den Daten, nicht aus Bequemlichkeit: das System plante
`mindestziel_zeitraum_tage_geschaetzt` = **1,2 bis 2,1 Tage** (Median der
1.998 Hebel-Signale). H2 ist der Horizont, auf dem die Empfehlung wirken
sollte.

Die uebrigen fuenf Horizonte sind **Robustheitspruefung, keine Suche**:
traegt der Beitrag, muss er ueber H1..H20 einen STETIGEN Verlauf zeigen.
Ein Beitrag, der nur bei H3 auftaucht und bei H2 und H5 verschwindet, ist
Rauschen - egal wie gross die Zahl ist.

## Trennschaerfe - vorab geprueft, nicht angenommen

Gemessen am 31.08. VOR dem Lauf: der Interquartilsabstand von `in_r`
**innerhalb eines Kalendertags** (das ist die Groesse, auf der der
Rangvergleich arbeitet):

    H1   0,38 R      H5   0,87 R      H20  1,85 R

Bei H1 ist die Trennschaerfe rund ein Fuenftel von H20. Sie ist vorhanden,
aber ein Effekt muss dort entsprechend groesser sein, um aus dem
Placebo-Band zu ragen. **Ein Nullbefund bei H1 ist deshalb kein Beweis
gegen den Beitrag** - er ist zuerst ein Hinweis auf fehlende Maechtigkeit
(vgl. [[project_messwerkzeuge_auf_kleiner_basis]]).

⚠️ Die Streuung ueber ALLE Tage (8,97 bei H1 bis 102 bei H20) ist durch die
bekannten Token-Umstellungen aufgeblaeht - 14 von 523 Reihen, LUNA Faktor
177.400. Der Median ist robust, die Streuung nicht; deshalb steht hier der
Interquartilsabstand.

## Die Kontrolle bleibt die Kontrolle

Funding muss bei **H20 weiterhin +0,0242 R** liefern. Weicht das ab, gilt kein
Befund dieses Laufs - unabhaengig davon, was die kurzen Horizonte zeigen.

    python messe_kandidaten_als_regel.py --horizonte 1,2,3,5,10,20
"""
import sys

import numpy as np

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import messe_bewertungskennzahl as MB
import messe_eigenschaft_beitrag as B
import messe_funding_niveau as F
import messe_regel_wirksamkeit as W

RUECKBLICK = 21          # Standardfenster fuer Amihud
MIND_JE_TAG = 12


SCHNITT_FENSTER = 200          # wie in `messe_schnittabstand_beitrag.py`


def baue(reihen, art, zusatz=None, horizont=None):
    """Anker je Kalendertag mit dem gewuenschten Merkmal."""
    je_tag = {}
    for sym, roh in reihen.items():
        tage = [z[0] for z in roh]
        c = np.array([z[1] for z in roh])
        h = np.array([z[2] for z in roh])
        t_ = np.array([z[3] for z in roh])
        v = np.array([z[4] for z in roh])
        breite = B.spanne(h, t_, c, B.SCHWANKUNG)
        umsatz = v * c
        rendite = np.zeros(len(c))
        rendite[1:] = np.abs(c[1:] / np.maximum(c[:-1], 1e-12) - 1.0)
        extra = (zusatz or {}).get(sym.upper())
        # ⚠️ DER HORIZONT IST JETZT EIN PARAMETER (31.08.2026). Vorher stand
        # hier `W.HORIZONT` fest auf 20 - fuer den Hebel die falsche
        # Geometrie. Die Vorgabe bleibt W.HORIZONT, damit jeder bestehende
        # Aufruf unveraendert dasselbe rechnet.
        _h = int(horizont or W.HORIZONT)
        start = 260 if art == "momentum" else RUECKBLICK + 40
        for i in range(start, len(c) - _h):
            r = breite[i]
            if not np.isfinite(r) or r <= 0:
                continue
            wert = None
            if art == "amihud":
                u = umsatz[i - RUECKBLICK:i]
                rr = rendite[i - RUECKBLICK:i]
                gut = u > 0
                if gut.sum() >= RUECKBLICK // 2:
                    wert = float(np.mean(rr[gut] / u[gut]) * 1e9)
            elif art == "momentum":
                if c[i - 252] > 0:
                    wert = float(c[i - 21] / c[i - 252] - 1.0)
            elif art == "turnover":
                menge = (extra or {}).get(tage[i])
                if menge and menge > 0:
                    wert = float(v[i] / menge)
            elif art == "funding":
                wert = (extra or {}).get(tage[i])
            elif art == "schnitt":
                # ⚠️ DER DRITTE TRAGENDE BEITRAG HAT HIER GEFEHLT
                # (31.08.2026). Er wurde in `messe_schnittabstand_beitrag.py`
                # gemessen, stand aber nie in dieser Kandidatenliste - und
                # damit lief er nie ueber DENSELBEN Massstab wie Funding und
                # Turnover. Genau dafuer ist diese Datei da.
                if i >= SCHNITT_FENSTER:
                    _m = c[i - SCHNITT_FENSTER:i].mean()
                    if _m > 0:
                        wert = float(c[i] / _m - 1.0)
            if wert is None or not np.isfinite(wert):
                continue
            je_tag.setdefault(tage[i], []).append(
                {"sym": sym, "kennzahl": wert,
                 "in_r": float((c[i + _h] - c[i]) / r)})
    return {t: z for t, z in je_tag.items() if len(z) >= MIND_JE_TAG}


def horizontlauf(reihen, menge, funding, horizonte):
    """Die drei TRAGENDEN Beitraege ueber mehrere Horizonte (31.08.2026).

    ⚠️ NUR die drei registrierten - Amihud und Momentum sind gemessen und
    tragen nicht; sie hier mitzurechnen hiesse, die Zellenzahl und damit den
    Suchpreis zu erhoehen, ohne dass eine Entscheidung daran haengt
    (Methodik 2.49).
    """
    rng = np.random.default_rng(20260831)
    fertig = {}
    for h in horizonte:
        print()
        print("#" * 92)
        print("# HORIZONT H%d" % h)
        print("#" * 92)
        for art, klar, oben in (("funding", "FUNDING-Rang", True),
                                ("turnover", "TURNOVER-Rang", True),
                                ("schnitt", "ABSTAND ZUM 200-SCHNITT", True)):
            extra = {"funding": funding, "turnover": menge}.get(art)
            je_tag = baue(reihen, art, extra, horizont=h)
            if not je_tag:
                print("  H%-3d %-26s zu wenige Anker" % (h, klar))
                continue
            e = W.bericht("H%d %s" % (h, klar), je_tag, oben, rng,
                          mit_positivkontrolle=(h == horizonte[0]))
            fertig[(h, art)] = e
    return fertig


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--horizonte", default="",
                    help="z.B. 1,2,3,5,10,20 - loest den Horizontlauf aus")
    a = ap.parse_args()

    reihen = B.lade()
    rng = np.random.default_rng(20260830)
    menge = MB.reihe("data/onchain_historie.db", "splycur")
    funding = F.lade_funding()

    if a.horizonte:
        hs = [int(x) for x in a.horizonte.split(",") if x.strip()]
        # ⚠️ DIE KONTROLLE ZUERST, UND ZWAR BEI H20. Weicht Funding dort von
        # +0,0242 R ab, gilt kein Befund dieses Laufs - egal was die kurzen
        # Horizonte zeigen.
        print("#" * 92)
        print("# KONTROLLE — Funding bei H20 muss +0,0242 R reproduzieren")
        print("#" * 92)
        W.bericht("KONTROLLE FUNDING H20",
                  baue(reihen, "funding", funding, horizont=20),
                  True, rng, mit_positivkontrolle=False)
        horizontlauf(reihen, menge, funding, hs)
        return

    print("#" * 92)
    print("# KONTROLLE ZUERST — Funding muss +0,0242 R reproduzieren")
    print("#" * 92)
    W.bericht("4 FUNDING (Kontrolle)", baue(reihen, "funding", funding),
              True, rng, mit_positivkontrolle=False)

    W.bericht("2 AMIHUD-ILLIQUIDITAET  |Rendite| / Umsatz",
              baue(reihen, "amihud"), True, rng)
    print()
    print("  ⚠️ Gegenrichtung, weil die Literatur eine Praemie fuer ILLIQUIDE")
    print("     Werte behauptet - dann muesste man die LIQUIDEN sperren:")
    W.bericht("2b AMIHUD, Gegenrichtung", baue(reihen, "amihud"), False, rng,
              mit_positivkontrolle=False)

    W.bericht("3 MOMENTUM 12-1", baue(reihen, "momentum"), False, rng)
    W.bericht("1 TURNOVER  Volumen / Umlaufmenge",
              baue(reihen, "turnover", menge), True, rng)

    print()
    print("#" * 92)
    print("# NICHT MESSBAR — und warum")
    print("#" * 92)
    print("  5 OI / Marktkapitalisierung  Binance liefert Open Interest nur")
    print("     30 Tage rueckwirkend (geprueft). Eigene Reihe: 219 Zeilen,")
    print("     36 Symbole, unterbrochen seit 19.07.2026.")
    print("  6 Volatilitaets-Risikopraemie  implizite Volatilitaet nur fuer")
    print("     BTC und ETH (Deribit) - zwei Symbole sind kein Querschnitt.")


if __name__ == "__main__":
    main()
