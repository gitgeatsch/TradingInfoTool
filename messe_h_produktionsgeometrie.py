# -*- coding: utf-8 -*-
"""Traegt H auf der PRODUKTIONS-Geometrie? (30.08.2026, Schritt 2)

⚠️ DIESER KOPF IST DIE VORABFESTLEGUNG, geschrieben BEVOR gerechnet wurde.

## Der Anlass - eine Luecke, die sieben Messungen ueberlebt hat

Seit dem 18.08.2026 setzt `entscheidungsrechnung._boeden()` den Stop nach
DREI Boeden, der weiteste gewinnt:

    Rauschen    max(2,5 % Kurs, k x ATR)
    Struktur    Marke +- 0,25 ATR        <-- die Unterstuetzung TRAEGT den Stop
    These       Widerlegungspreis        (vom Modell, hier nicht verfuegbar)

`messe_marken.py:203` rechnet dagegen bis heute

    stop = einstieg - K * atr

also OHNE Strukturboden. ⚠️ ALLE SIEBEN H-MESSUNGEN (Kapitel 104, 104.3, 105,
108, 119, 121, S3/S4) liefen auf dieser alten Geometrie. Die Produktion
verwendet sie seit dem 18.08. nicht mehr.

## Warum das den Befund aendern kann - die Doppelzaehlung

H besteht aus zwei Teilen:

    A  frei     keine mehrfach beruehrte Marke zwischen Einstieg und ZIEL
    B  gedeckt  eine mehrfach beruehrte Marke ueber dem STOP

⚠️ B WIRD IN DER PRODUKTION TEILWEISE PER KONSTRUKTION ERFUELLT. Wenn der
Strukturboden greift, liegt der Stop bei "Marke minus 0,25 ATR" - die Marke
liegt dann zwangslaeufig darueber, und B ist wahr, ohne etwas auszusagen.
Dieselbe Information wirkt zweimal: einmal im Stop (gemessen unschaedlich,
-0,0008 R, Kapitel 124), einmal als +4,5 Punkte Bonus.

Kapitel 124 hat gemessen, dass der Boden bei 1,1 % der Anker greift - aber
das war die Frage "aendert er den Stop", nicht "aendert er B". B kann auch
dort wahr werden, wo der Rauschboden gewinnt und zufaellig unter der Marke
liegt. Was mit B geschieht, ist schlicht ungemessen.

## Die Frage, vorab festgelegt

    Traegt H, wenn A und B auf der Geometrie geprueft werden, die die
    Produktion heute tatsaechlich rechnet?

Und die Zerlegung dazu:

    Wie viele Anker wechseln ihren H-Status zwischen alter und neuer
    Geometrie - und in welche Richtung?

## ⚠️ GERECHNET WIRD MIT DER PRODUKTIONSFUNKTION

`_stop_abstand` wird aufgerufen, nicht nachgebaut - sonst misst man eine
Kopie, die still veraltet (Vorbild: `pruefe_strukturstop.py`, Methodik 2.66).

## ⚠️ WIE WEIT MESSUNG UND PRODUKTION AUSEINANDERLIEGEN — ERHOBEN, NICHT VERMUTET

Nutzerhinweis 30.08.: *"ich weiss nicht ob die aktuelle Produktionsfunktion
noch jene der damaligen MESSUNG ist - das musst du erheben."* Erhoben:

    _boeden / _stop_abstand    seit 18.08.2026 UNVERAENDERT (git log -L)
    Kapitel 104-121            gemessen am 20./21.08. - also NACH dem Umbau,
                               aber auf `messe_marken`, das die Funktion nie
                               aufruft
    S3/S4                      25./26.08., ebenfalls `messe_marken`

Vier Abweichungen zwischen Messung und Produktion:

    ATR-Faktor          messe_marken K = 2,0   |  Produktion stop_ziel_atr = 2,5
    Rauschboden         keiner                 |  max(2,5 % Kurs, 0,75 x ATR)
    Strukturboden       keiner                 |  Marke - 0,25 ATR
    Widerlegungspreis   keiner                 |  vom Modell, macht den Stop ENGER

⚠️ DIE VIERTE LUECKE BLEIBT OFFEN, UND DAS IST HIER AUSDRUECKLICH VERMERKT.
Der Widerlegungspreis kommt vom Sprachmodell und wird nirgends gespeichert -
in `signals` gibt es keine Spalte dafuer. Historisch existiert er nicht und
laesst sich auch nicht rekonstruieren. Diese Messung deckt daher den Fall
OHNE These ab.

Das ist kein voller Ausfall: wo der Strukturboden der weiteste ist, gewinnt
er ohnehin gegen die These (Beispiel Kurs 100 / ATR 3 / Marke 92: Struktur
8,75 gegen These 5,00). Der Lauf weist deshalb aus, WIE OFT welche Regel
gewinnt - dort, wo "Struktur" gewinnt, ist die gemessene Geometrie die
produktive; wo der ATR-Rueckfall gewinnt, koennte die Produktion enger
liegen.

## Die Checkliste aus `Pruefplan_H_als_Regel_30_08.md`, Punkt fuer Punkt

     1 Regel statt Merkmal     ✔ gemessen wird der Unterschied, den die Regel macht
     2 blindes Mass            ✔ Hauptmass ist die BEWEGUNG IN R; "Ziel vor Stop"
                                 laeuft als H's eigenes Mass mit, aber als QUOTE
                                 (der Median einer 0/1-Reihe ist immer 0 - der
                                 Fehler vom 30.08. vormittags)
     3 fremdes Zeitfenster     ✔ Vergleich JE ZEITBLOCK
     4 nicht quotengleich      ✔ Placebo-Band aus zirkulaeren Versaetzen haelt
                                 die H-Quote exakt konstant
     5 Anker als unabhaengig   ✔ Bootstrap ueber Bloecke
     6 Block < Horizont        ✔ Block 120 > Horizont 20
     7 Mittelwert bei Schiefe  ✔ Median fuer `in_r`
     8 Datenbrueche            ✔ Sprung > Faktor 5 im Vorwaertsfenster entfernt
     9 Positivkontrolle        ✔ kuenstlicher Zuschlag bekannter Groesse
    10 Suchpreis               ✔ EINE vorab benannte Frage, keine Variantensuche
    11 nur eine Haelfte        ✔ beide Haelften getrennt
    12 Survivorship            ✔ dieselbe Ankermenge fuer beide Geometrien -
                                 der Vergleich ist GEPAART, Survivorship kuerzt
                                 sich heraus
    13 kleine Basis            ✔ 523 Reihen aus `messdaten.db`
    14 Bytecode-Cache          ✔ `__pycache__` vor dem Lauf loeschen
    15 Struktureinbruch 2024   ✔ je Zeitabschnitt getrennt

## Die Urteilsregel, vorab

  H traegt weiterhin   Vorsprung positiv UND ausserhalb des Placebo-Bandes,
                       in beiden Historienhaelften gleiches Vorzeichen
  H traegt nicht mehr  Vorsprung <= 0 oder im Band, UND die Positivkontrolle
                       zeigt, dass ein Effekt dieser Groesse gefunden worden
                       waere
  unentscheidbar       sonst

    python messe_h_produktionsgeometrie.py
"""
from __future__ import annotations

import io
import json
import statistics as st
import sys
import time

import numpy as np

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, ".")

from agent.entscheidungsrechnung import _stop_abstand            # noqa: E402
from messe_marken import (CRV, MIN_BERUEHRUNGEN,                 # noqa: E402
                          K, MAX_TAGE, _niveaus_schnell, _SwingSpeicher)
from simuliere_bremse import _reihen_roh, klassen_aus_db         # noqa: E402

CACHE = "anker_h_produktion_2026_08_30.json"
HORIZONT = 20
MINDESTALTER = 250
BRUCH = 5.0
BLOCK = 120
MIND_JE_GRUPPE = 30
ZIEHUNGEN = 20000
PLACEBO_LAEUFE = 40
ABSCHNITTE = (("2018-2020", "2018-01-01", "2020-12-31"),
              ("2021-2023", "2021-01-01", "2023-12-31"),
              ("2024-2026", "2024-01-01", "2026-12-31"))


def _ausgang(c, h, l, i, stop, ziel):
    """Vorsichtige Lesart: faellt beides in eine Kerze, gilt der STOP (2.54)."""
    for j in range(i + 1, min(i + 1 + MAX_TAGE, len(c))):
        if l[j] <= stop:
            return "stop"
        if h[j] >= ziel:
            return "ziel"
    return "abgelaufen"


def _marken(n, stop, ziel):
    """A und B auf EINER Geometrie - dieselbe Regel wie `messe_marken`."""
    frei = not any(m["beruehrungen"] >= MIN_BERUEHRUNGEN and m["preis"] < ziel
                   for m in n["oben"])
    gedeckt = any(m["beruehrungen"] >= MIN_BERUEHRUNGEN and m["preis"] > stop
                  for m in n["unten"])
    return frei, gedeckt


def laufe(db="data/messdaten.db", klasse="krypto"):
    """Je Anker BEIDE Geometrien - alt und Produktion - am selben Punkt."""
    roh = _reihen_roh(db, klasse, klassen_aus_db(db))
    aus = []
    t0 = letzte = time.time()
    for nr, (sym, (c, h, l, v, a, off, d)) in enumerate(roh.items(), 1):
        del v
        sp = _SwingSpeicher(h, l)
        cc = np.asarray(c, dtype=float)
        verh = cc[1:] / np.maximum(cc[:-1], 1e-12)
        bruch = (verh > BRUCH) | (verh < 1.0 / BRUCH)          # Punkt 8
        for i in range(off + 1 + MINDESTALTER, len(c) - HORIZONT - 1):
            atr, kurs = float(a[i - off]), float(c[i])
            if not (atr > 0 and kurs > 0):
                continue
            if bruch[i:i + HORIZONT].any():
                continue
            n = _niveaus_schnell(sp, c, h, l, i, atr)
            unten = [m["preis"] for m in n["unten"]
                     if m["beruehrungen"] >= MIN_BERUEHRUNGEN]
            marke = max(unten) if unten else None

            # ---- DREI ARME, damit die Ursache trennbar bleibt ------------
            # ⚠️ `messe_marken` rechnet K = 2,0 x ATR, die Produktion
            # 2,5 x ATR (GRENZEN["stop_min_atr"]) plus Rausch- und
            # Strukturboden. Ein Zweiarm-Vergleich wuerfe beide Aenderungen
            # zusammen und nennte das Ergebnis "der Strukturboden".
            #
            #   alt    K x ATR                        so wurde H gemessen
            #   ohne   Produktionsfunktion, Marke=None   isoliert k+Rauschen
            #   prod   Produktionsfunktion mit Marke     das echte System
            #
            # Der Unterschied ohne -> prod IST der Strukturboden, allein.
            ab_alt = K * atr
            ab_ohne, _r0 = _stop_abstand(kurs, atr, None, False, None, None)
            ab_prod, regel = _stop_abstand(kurs, atr, None, False, None, marke)
            if ab_alt <= 0 or ab_ohne <= 0 or ab_prod <= 0:
                continue
            stop_alt = kurs - ab_alt
            stop_ohne = kurs - ab_ohne
            stop_prod = kurs - ab_prod
            if stop_alt <= 0 or stop_ohne <= 0 or stop_prod <= 0:
                continue
            ziel_alt = kurs + CRV * ab_alt
            ziel_ohne = kurs + CRV * ab_ohne
            ziel_prod = kurs + CRV * ab_prod

            frei_a, ged_a = _marken(n, stop_alt, ziel_alt)
            frei_o, ged_o = _marken(n, stop_ohne, ziel_ohne)
            frei_p, ged_p = _marken(n, stop_prod, ziel_prod)
            weg = float(c[i + HORIZONT]) - kurs
            # ⚠️ EINMAL je Geometrie. Der erste Entwurf rief `_ausgang`
            # zweimal je Zeile auf (einmal im if, einmal im else) - das
            # verdoppelt den teuersten Teil des Laufs ohne jeden Gewinn.
            aus_a = _ausgang(c, h, l, i, stop_alt, ziel_alt)
            aus_o = _ausgang(c, h, l, i, stop_ohne, ziel_ohne)
            aus_p = _ausgang(c, h, l, i, stop_prod, ziel_prod)
            aus.append({
                "sym": sym, "datum": d[i],
                # ⚠️ R HAENGT AN DER GEOMETRIE. Der Risikobetrag IST der
                # Stopabstand - zwei Geometrien, zwei Nenner. Ein gemeinsamer
                # Nenner waere bequem und falsch.
                "r_alt": weg / ab_alt, "r_ohne": weg / ab_ohne,
                "r_prod": weg / ab_prod,
                "h_alt": bool(frei_a and ged_a),
                "h_ohne": bool(frei_o and ged_o),
                "h_prod": bool(frei_p and ged_p),
                "frei_alt": frei_a, "ged_alt": ged_a,
                "frei_ohne": frei_o, "ged_ohne": ged_o,
                "frei_prod": frei_p, "ged_prod": ged_p,
                "stop_ohne": ab_ohne / kurs,
                "boden_greift": regel == "jenseits der naechsten Marke",
                "regel": regel,
                "stop_alt": ab_alt / kurs, "stop_prod": ab_prod / kurs,
                "ziel_alt": (1.0 if aus_a == "ziel"
                             else 0.0 if aus_a == "stop" else None),
                "ziel_ohne": (1.0 if aus_o == "ziel"
                              else 0.0 if aus_o == "stop" else None),
                "ziel_prod": (1.0 if aus_p == "ziel"
                              else 0.0 if aus_p == "stop" else None)})
        if time.time() - letzte >= 60:
            letzte = time.time()
            print("  [%4.1f min] Reihe %d/%d - %d Anker"
                  % ((letzte - t0) / 60, nr, len(roh), len(aus)), flush=True)
    return aus


# ----------------------------------------------------------------- Auswertung
def bloecke(anker, feld, marke, bedingung=None, block=BLOCK):
    """Je Zeitblock: Lagemass(H) minus Lagemass(Nicht-H) - wie Verwendung 4."""
    quote = feld.startswith("ziel")
    lagemass = (lambda x: float(np.mean(x))) if quote else st.median
    teil = [a for a in anker if bedingung is None or bedingung(a)]
    tage = sorted({a["datum"] for a in teil})
    if len(tage) < 2 * block:
        return None
    lage = {t: i // block for i, t in enumerate(tage)}
    je_block = {}
    for a in teil:
        w = a.get(feld)
        if w is None:
            continue
        je_block.setdefault(lage[a["datum"]], ([], []))[0 if a[marke] else 1] \
            .append(float(w))
    werte = [lagemass(mit) - lagemass(ohne)
             for mit, ohne in je_block.values()
             if len(mit) >= MIND_JE_GRUPPE and len(ohne) >= MIND_JE_GRUPPE]
    return werte if len(werte) >= 5 else None


def urteil(titel, werte, rng, einheit="R", einzug=2):
    if werte is None:
        print("%s%-40s zu wenige Bloecke" % (" " * einzug, titel))
        return None
    b = np.array(werte)
    n = len(b)
    boot = np.array([b[rng.integers(0, n, n)].mean() for _ in range(ZIEHUNGEN)])
    u, o = np.quantile(boot, [0.025, 0.975])
    print("%s%-40s %+.4f %s [%+.4f .. %+.4f] %2d/%2d +  %s"
          % (" " * einzug, titel, b.mean(), einheit, u, o,
             int((b > 0).sum()), n,
             "TRAEGT" if u > 0 else ("UMGEKEHRT" if o < 0 else "nicht trennbar")))
    return float(b.mean())


def placebo_band(anker, feld, marke, rng):
    """Zirkulaere Versaetze je Symbol - haelt die H-Quote exakt konstant."""
    je_sym = {}
    for a in anker:
        je_sym.setdefault(a["sym"], []).append(a)
    sortiert = {s: sorted(z, key=lambda x: x["datum"]) for s, z in je_sym.items()}
    werte = []
    for _ in range(PLACEBO_LAEUFE):
        versetzt = []
        for z in sortiert.values():
            marken = [x[marke] for x in z]
            v = int(rng.integers(0, max(len(marken), 1)))
            for x, m in zip(z, marken[v:] + marken[:v]):
                versetzt.append({**x, marke: m})
        w = bloecke(versetzt, feld, marke)
        if w:
            werte.append(float(np.mean(w)))
    return np.array(werte)


def main():
    import os
    if os.path.exists(CACHE):
        anker = json.loads(io.open(CACHE, encoding="utf-8").read())
        print("%d Anker aus dem Zwischenspeicher." % len(anker))
    else:
        print("Lade Anker (523 Reihen, beide Geometrien) - das dauert...",
              flush=True)
        anker = laufe()
        io.open(CACHE, "w", encoding="utf-8").write(json.dumps(anker))
        print("Zwischengespeichert -> %s" % CACHE)
    rng = np.random.default_rng(20260830)

    n = len(anker)
    n_alt = sum(1 for a in anker if a["h_alt"])
    n_prod = sum(1 for a in anker if a["h_prod"])
    print()
    print("=" * 104)
    print("H AUF DER PRODUKTIONS-GEOMETRIE — SCHRITT 2")
    print("=" * 104)
    print("%d Anker, %d Symbole, %s .. %s"
          % (n, len({a["sym"] for a in anker}),
             min(a["datum"] for a in anker), max(a["datum"] for a in anker)))
    print("Reifeschnitt %d Handelstage, Datenbrueche > Faktor %.0f entfernt."
          % (MINDESTALTER, BRUCH))

    print()
    print("-" * 104)
    print("  WAS DIE PRODUKTIONS-GEOMETRIE AN H AENDERT")
    print("-" * 104)
    import collections
    print("  Welche Regel bestimmt den Stop (ohne These - siehe Modulkopf):")
    for r, z in collections.Counter(a["regel"] for a in anker).most_common():
        print("    %-34s %7d  (%5.2f %%)" % (r, z, 100 * z / n))
    print()
    greift = sum(1 for a in anker if a["boden_greift"])
    print("  Strukturboden greift          %7d  (%5.2f %%)" % (greift, 100 * greift / n))
    print("  Stopabstand Median      alt %5.2f %%   Produktion %5.2f %%"
          % (100 * st.median([a["stop_alt"] for a in anker]),
             100 * st.median([a["stop_prod"] for a in anker])))
    print()
    print("  Stopabstand Median      ohne Marke %5.2f %%"
          % (100 * st.median([a["stop_ohne"] for a in anker])))
    print()
    print("  %-18s %10s %12s %12s   %s"
          % ("", "alt (K=2,0)", "ohne Marke", "Produktion", "was der Boden macht"))
    for teil, klar in (("frei", "A  freier Weg"), ("ged", "B  Stop gedeckt"),
                       ("h", "H  A UND B")):
        a_ = sum(1 for x in anker if x[teil + "_alt"])
        o_ = sum(1 for x in anker if x[teil + "_ohne"])
        p_ = sum(1 for x in anker if x[teil + "_prod"])
        print("  %-18s %9.2f %% %11.2f %% %11.2f %%   %+6.2f Punkte"
              % (klar, 100 * a_ / n, 100 * o_ / n, 100 * p_ / n,
                 100 * (p_ - o_) / n))
    wechsel_auf = sum(1 for a in anker if a["h_prod"] and not a["h_alt"])
    wechsel_ab = sum(1 for a in anker if a["h_alt"] and not a["h_prod"])
    print()
    print("  Wechsel  nein->JA %d (%.2f %%)   JA->nein %d (%.2f %%)"
          % (wechsel_auf, 100 * wechsel_auf / n, wechsel_ab, 100 * wechsel_ab / n))
    if n_alt and n_prod:
        beide = sum(1 for a in anker if a["h_alt"] and a["h_prod"])
        print("  Ueberschneidung: %d Anker sind in BEIDEN H (%.1f %% der alten,"
              " %.1f %% der neuen)"
              % (beide, 100 * beide / n_alt, 100 * beide / n_prod))

    for marke, feld_r, feld_z, klar in (
            ("h_alt", "r_alt", "ziel_alt", "ALTE GEOMETRIE (so wurde H gemessen)"),
            ("h_ohne", "r_ohne", "ziel_ohne", "OHNE MARKE (isoliert k und Rauschboden)"),
            ("h_prod", "r_prod", "ziel_prod", "⚠️ PRODUKTIONS-GEOMETRIE (so rechnet das System)")):
        print()
        print("=" * 104)
        print("  %s" % klar)
        print("=" * 104)
        for feld, mklar, einheit in ((feld_r, "BEWEGUNG IN R", "R"),
                                     (feld_z, "ZIEL VOR STOP (Quote)", " ")):
            print("  %s" % mklar)
            echt = urteil("gesamt", bloecke(anker, feld, marke), rng, einheit, 4)
            for name, von, bis in ABSCHNITTE:
                urteil(name, bloecke(anker, feld, marke,
                                     lambda a, v=von, b=bis: v <= a["datum"] <= b),
                       rng, einheit, 6)
            tage = sorted({a["datum"] for a in anker})
            mitte = tage[len(tage) // 2]
            for name, bed in (("erste Haelfte", lambda a, m=mitte: a["datum"] < m),
                              ("zweite Haelfte", lambda a, m=mitte: a["datum"] >= m)):
                urteil(name, bloecke(anker, feld, marke, bed), rng, einheit, 6)
            p = placebo_band(anker, feld, marke, rng)
            u, o = np.quantile(p, [0.025, 0.975])
            print("    PLACEBO-BAND (%d Versaetze)  %+.4f .. %+.4f  (Mitte %+.4f)"
                  % (len(p), u, o, float(p.mean())))
            if echt is not None:
                print("    -> %s"
                      % ("AUSSERHALB - der Befund haelt" if (echt < u or echt > o)
                         else "⚠️ INNERHALB des Bandes - vom Zufall nicht zu trennen"))
            print()

    print("=" * 104)
    print("POSITIVKONTROLLE — auf der Produktions-Geometrie")
    print("=" * 104)
    basis = float(np.mean(bloecke(anker, "r_prod", "h_prod")))
    for staerke in (0.05, 0.10, 0.20, 0.40):
        gepflanzt = [{**a, "r_prod": a["r_prod"] + (staerke if a["h_prod"] else 0.0)}
                     for a in anker]
        w = bloecke(gepflanzt, "r_prod", "h_prod")
        urteil("gepflanzt %+.2f R (Versatz %+.3f)"
               % (staerke, float(np.mean(w)) - basis), w, rng, "R", 4)


if __name__ == "__main__":
    main()
