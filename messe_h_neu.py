# -*- coding: utf-8 -*-
"""H-1 und H-2: traegt der RAUM NACH OBEN, stetig und in ATR? (30.08.2026)

⚠️ DIESER KOPF IST DIE VORABFESTLEGUNG, geschrieben BEVOR gerechnet wurde.

## Woher der Umbau kommt

`messe_h_produktionsgeometrie.py` hat am 30.08. zwei Konstruktionsfehler in
H gemessen - nicht im Markt, sondern in der Bauform:

    B ist wirkungslos     zu 86,75 % wahr. H und A stimmen bei 98,27 % aller
                          Anker ueberein - B fuegt nichts hinzu, sondern
                          zieht nach unten (A allein +0,0819 gegen H +0,0553)
    A misst Volatilitaet  A trifft bei weitem Stop 8,33 %, bei engem 1,80 % -
                          Faktor 4,6

## Der Mechanismus hinter dem zweiten Fehler, und warum ATR ihn aufhebt

Marken zaehlen erst ab `NIVEAU_MIN_ABSTAND_ATR * atr` Abstand (Totzone).
Bei einem volatilen Wert ist diese Zone IN PROZENT breiter - es ueberleben
weniger Marken, und "kein Widerstand bis zum Ziel" wird wahrscheinlicher,
ohne dass der Markt irgendetwas anderes tut. A zaehlt damit teilweise
Volatilitaet.

⚠️ MISST MAN DEN ABSTAND SELBST IN ATR, faellt genau das weg: Totzone und
Abstand haben dann dieselbe Einheit. Das ist der ganze Trick von H-2.

## Die neue Groesse

    raum_atr = (naechster Widerstand ueber dem Kurs - Kurs) / ATR

  H-1  B faellt weg. Nur der Weg nach oben.
  H-2  stetig statt binaer, und in ATR statt "vor dem Ziel". Das Ziel ist
       CRV x Stopabstand, also eine Groesse, die WIR waehlen - ein Merkmal,
       das gegen sie prueft, misst zum Teil die eigene Geometrie.

⚠️ KEIN WIDERSTAND IST NICHT NULL. Findet sich oberhalb keine mehrfach
beruehrte Marke, ist der Raum nicht "0" und auch nicht der groesste
gemessene Wert - er ist unbekannt nach oben. Solche Anker bekommen
`raum_atr = None` und laufen als EIGENE Gruppe mit. Sie in die Rangfolge zu
werfen waere dieselbe Verwechslung wie "fehlend = schlechtestes Fuenftel".

## Die FORM - vorab geklaert (stehende Regel vom 30.08.)

Gemessen wird BEIDES, weil die Antwort nicht vorab feststeht:

    QUERSCHNITT   Rang je Kalendertag ueber alle Symbole. Das ist die Form,
                  in der Funding und Turnover tragen - und die Bauform, die
                  `marktrang.py` liefert.
    ZEITREIHE     H-Anker gegen Nicht-H-Anker desselben Zeitblocks. Das ist
                  die Form, in der H bisher gemessen wurde.

## ⚠️ DIE ENTSCHEIDENDE GEGENPROBE

Wenn `raum_atr` nur die Volatilitaet in neuen Kleidern ist, war nichts
gewonnen. Deshalb laeuft die Korrelation zur relativen ATR mit, und die
Wirkung wird ZUSAETZLICH innerhalb von Volatilitaets-Dritteln gerechnet.
Traegt sie nur in einem Drittel, ist sie ein Mitlaeufer.

## Vorab festgelegt

  traegt        Spanne unterstes gegen oberstes Fuenftel ausserhalb des
                Placebo-Bandes, in BEIDEN Historienhaelften gleiches
                Vorzeichen, UND in allen drei Volatilitaets-Dritteln
                dasselbe Vorzeichen
  Mitlaeufer    nur in einem Teil der Volatilitaets-Dritteln
  traegt nicht  sonst - dann muss die Positivkontrolle zeigen, dass ein
                Effekt dieser Groesse gefunden worden waere

    python messe_h_neu.py
"""
from __future__ import annotations

import io
import json
import os
import statistics as st
import sys
import time

import numpy as np

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, ".")

from messe_marken import (CRV, MIN_BERUEHRUNGEN, K, MAX_TAGE,     # noqa: E402
                          _niveaus_schnell, _SwingSpeicher)
from simuliere_bremse import _reihen_roh, klassen_aus_db          # noqa: E402

CACHE = "anker_h_neu_2026_08_30.json"
HORIZONT = 20
MINDESTALTER = 250
BRUCH = 5.0
BLOCK = 120
MIND_JE_TAG = 15
MIND_JE_GRUPPE = 30
ZIEHUNGEN = 20000
PLACEBO_LAEUFE = 40
DECKEL_ATR = 40.0      # nur zur Anzeige; Raenge sind ordinal


def _ausgang(c, h, l, i, stop, ziel):
    for j in range(i + 1, min(i + 1 + MAX_TAGE, len(c))):
        if l[j] <= stop:
            return "stop"
        if h[j] >= ziel:
            return "ziel"
    return "abgelaufen"


def laufe(db="data/messdaten.db", klasse="krypto"):
    roh = _reihen_roh(db, klasse, klassen_aus_db(db))
    aus = []
    t0 = letzte = time.time()
    for nr, (sym, (c, h, l, v, a, off, d)) in enumerate(roh.items(), 1):
        del v
        sp = _SwingSpeicher(h, l)
        cc = np.asarray(c, dtype=float)
        verh = cc[1:] / np.maximum(cc[:-1], 1e-12)
        bruch = (verh > BRUCH) | (verh < 1.0 / BRUCH)
        for i in range(off + 1 + MINDESTALTER, len(c) - HORIZONT - 1):
            atr, kurs = float(a[i - off]), float(c[i])
            if not (atr > 0 and kurs > 0):
                continue
            if bruch[i:i + HORIZONT].any():
                continue
            n = _niveaus_schnell(sp, c, h, l, i, atr)
            oben = [m["preis"] for m in n["oben"]
                    if m["beruehrungen"] >= MIN_BERUEHRUNGEN]
            unten = [m["preis"] for m in n["unten"]
                     if m["beruehrungen"] >= MIN_BERUEHRUNGEN]
            # ⚠️ DER NAECHSTE Widerstand, nicht der staerkste. Dieselbe Wahl
            # wie in der Produktion (`rollen_lauf._marke_am_stop`): auf ihn
            # laeuft der Kurs zuerst. "Der staerkste" waere schon eine
            # Auswahl nach dem Merkmal, das geprueft werden soll.
            raum = (min(oben) - kurs) / atr if oben else None
            boden = (kurs - max(unten)) / atr if unten else None

            # Die ALTE Bauform, am selben Anker - fuer den direkten Vergleich
            stop_alt = kurs - K * atr
            if stop_alt <= 0:
                continue
            ziel_alt = kurs + CRV * (kurs - stop_alt)
            frei = not any(p < ziel_alt for p in oben)
            gedeckt = any(p > stop_alt for p in unten)
            ag = _ausgang(c, h, l, i, stop_alt, ziel_alt)
            aus.append({
                "sym": sym, "datum": d[i],
                "raum_atr": raum, "boden_atr": boden,
                "n_oben": len(oben), "n_unten": len(unten),
                # ⚠️ die Groesse, gegen die H-2 sich behaupten muss
                "atr_rel": atr / kurs,
                "frei": frei, "gedeckt": gedeckt,
                "h_alt": bool(frei and gedeckt),
                "in_r": (float(c[i + HORIZONT]) - kurs) / (K * atr),
                "ziel": (1.0 if ag == "ziel" else 0.0 if ag == "stop" else None)})
        if time.time() - letzte >= 60:
            letzte = time.time()
            print("  [%4.1f min] Reihe %d/%d - %d Anker"
                  % ((letzte - t0) / 60, nr, len(roh), len(aus)), flush=True)
    return aus


# ------------------------------------------------------------- Querschnitt
def fuenftel_je_tag(anker, feld, ziel_feld="in_r", bedingung=None,
                    mische=None):
    """Je Kalendertag Fuenftel bilden, dann ueber die Tage mitteln.

    Genau der Aufbau von `rechne_funding_beitrag.py` - damit die Zahlen
    unmittelbar vergleichbar sind und in dieselbe Beitragstabelle passen.
    """
    je_tag = {}
    for a in anker:
        if bedingung is not None and not bedingung(a):
            continue
        if a.get(feld) is None or a.get(ziel_feld) is None:
            continue
        je_tag.setdefault(a["datum"], []).append(a)
    sammel = {k: [] for k in range(5)}
    for tag, z in je_tag.items():
        if len(z) < MIND_JE_TAG:
            continue
        w = np.array([x[feld] for x in z], dtype=float)
        y = np.array([x[ziel_feld] for x in z], dtype=float)
        if mische is not None:
            w = mische.permutation(w)
        r = np.argsort(np.argsort(w)) / max(len(w) - 1, 1)
        for k in range(5):
            m = (r >= k / 5) & (r < (k + 1) / 5 if k < 4 else r <= 1.0)
            if m.sum() >= 2:
                sammel[k].append(float(np.median(y[m])))
    if any(len(sammel[k]) < 30 for k in range(5)):
        return None
    return [st.mean(sammel[k]) for k in range(5)]


def spanne(werte):
    return None if werte is None else werte[0] - werte[4]


def zeige_fuenftel(titel, werte, einheit="R"):
    if werte is None:
        print("  %-34s zu wenige Tage" % titel)
        return
    print("  %-34s %s   Spanne %+.4f %s"
          % (titel, " ".join("%+.3f" % x for x in werte),
             spanne(werte), einheit))


def main():
    if os.path.exists(CACHE):
        anker = json.loads(io.open(CACHE, encoding="utf-8").read())
        print("%d Anker aus dem Zwischenspeicher." % len(anker))
    else:
        print("Lade Anker (523 Reihen) - das dauert...", flush=True)
        anker = laufe()
        io.open(CACHE, "w", encoding="utf-8").write(json.dumps(anker))
        print("Zwischengespeichert -> %s" % CACHE)
    rng = np.random.default_rng(20260830)
    n = len(anker)
    ohne_raum = sum(1 for a in anker if a["raum_atr"] is None)

    print()
    print("=" * 104)
    print("H-1 UND H-2 — DER RAUM NACH OBEN, STETIG UND IN ATR")
    print("=" * 104)
    print("%d Anker, %d Symbole, %s .. %s"
          % (n, len({a["sym"] for a in anker}),
             min(a["datum"] for a in anker), max(a["datum"] for a in anker)))
    mit = [a["raum_atr"] for a in anker if a["raum_atr"] is not None]
    print("kein Widerstand oberhalb: %d Anker (%.1f %%) - eigene Gruppe, "
          "NICHT in die Rangfolge" % (ohne_raum, 100 * ohne_raum / n))
    print("raum_atr: Median %.2f ATR, Fuenftelgrenzen %s"
          % (st.median(mit),
             " / ".join("%.2f" % x for x in np.quantile(mit, [.2, .4, .6, .8]))))

    print()
    print("-" * 104)
    print("  ⚠️ DIE GEGENPROBE ZUERST — ist `raum_atr` nur die Volatilitaet?")
    print("-" * 104)
    r = np.array(mit)
    v = np.array([a["atr_rel"] for a in anker if a["raum_atr"] is not None])
    print("  Korrelation raum_atr <-> relative ATR: %+.3f" % float(np.corrcoef(r, v)[0, 1]))
    fr = np.array([1.0 if a["frei"] else 0.0 for a in anker])
    va = np.array([a["atr_rel"] for a in anker])
    print("  ...zum Vergleich die ALTE Groesse A:   %+.3f" % float(np.corrcoef(fr, va)[0, 1]))
    print("  (A war der Fehler - je hoeher die ATR, desto oefter 'frei')")

    print()
    print("=" * 104)
    print("QUERSCHNITT — Rang je Kalendertag, wie Funding und Turnover")
    print("=" * 104)
    print("  Fuenftel 0 = geringster Raum ... 4 = groesster Raum")
    print()
    for feld, klar in (("raum_atr", "H-2  Raum nach oben (ATR)"),
                       ("boden_atr", "     Boden nach unten (ATR)"),
                       ("n_oben", "     Anzahl Widerstaende"),
                       ("atr_rel", "     relative ATR (Kontrolle)")):
        zeige_fuenftel(klar, fuenftel_je_tag(anker, feld))

    print()
    print("  ZIEL VOR STOP (H's eigenes Mass)")
    zeige_fuenftel("H-2  Raum nach oben (ATR)",
                   fuenftel_je_tag(anker, "raum_atr", "ziel"), " ")

    print()
    print("-" * 104)
    print("  BEIDE HISTORIENHAELFTEN")
    print("-" * 104)
    tage = sorted({a["datum"] for a in anker})
    mitte = tage[len(tage) // 2]
    for name, bed in (("erste Haelfte", lambda a: a["datum"] < mitte),
                      ("zweite Haelfte", lambda a: a["datum"] >= mitte)):
        zeige_fuenftel(name, fuenftel_je_tag(anker, "raum_atr", bedingung=bed))

    print()
    print("-" * 104)
    print("  ⚠️ JE VOLATILITAETS-DRITTEL — traegt es ueberall oder nur irgendwo?")
    print("-" * 104)
    q = np.quantile([a["atr_rel"] for a in anker], [1 / 3, 2 / 3])
    for name, bed in (
            ("ruhig  (ATR unter %.3f)" % q[0], lambda a: a["atr_rel"] < q[0]),
            ("mittel", lambda a: q[0] <= a["atr_rel"] < q[1]),
            ("volatil (ATR ab %.3f)" % q[1], lambda a: a["atr_rel"] >= q[1])):
        zeige_fuenftel(name, fuenftel_je_tag(anker, "raum_atr", bedingung=bed))

    print()
    print("-" * 104)
    print("  DIE GRUPPE OHNE WIDERSTAND — was ist sie wert?")
    print("-" * 104)
    o = [a["in_r"] for a in anker if a["raum_atr"] is None]
    m = [a["in_r"] for a in anker if a["raum_atr"] is not None]
    print("  ohne Widerstand  %6d Anker   Median %+.4f R" % (len(o), st.median(o)))
    print("  mit  Widerstand  %6d Anker   Median %+.4f R" % (len(m), st.median(m)))

    print()
    print("=" * 104)
    print("KONTROLLEN")
    print("=" * 104)
    echt = spanne(fuenftel_je_tag(anker, "raum_atr"))
    p = []
    for _ in range(PLACEBO_LAEUFE):
        w = fuenftel_je_tag(anker, "raum_atr", mische=rng)
        if w:
            p.append(spanne(w))
    p = np.array(p)
    u, o_ = np.quantile(p, [0.025, 0.975])
    print("  NEGATIV (Rang je Tag gemischt, Quote bleibt exakt):")
    print("    Band %+.4f .. %+.4f (Mitte %+.4f, %d Laeufe)"
          % (u, o_, float(p.mean()), len(p)))
    print("    echt %+.4f  ->  %s"
          % (echt, "AUSSERHALB - der Befund haelt" if (echt < u or echt > o_)
             else "⚠️ INNERHALB - vom Zufall nicht zu trennen"))
    print()
    print("  POSITIV (kuenstlicher Zuschlag auf das UNTERSTE Fuenftel):")
    for staerke in (0.02, 0.05, 0.10, 0.20):
        gepflanzt = []
        je_tag = {}
        for a in anker:
            if a["raum_atr"] is not None:
                je_tag.setdefault(a["datum"], []).append(a)
        for tag, z in je_tag.items():
            w = np.array([x["raum_atr"] for x in z])
            rr = np.argsort(np.argsort(w)) / max(len(w) - 1, 1)
            for x, q_ in zip(z, rr):
                gepflanzt.append({**x, "in_r": x["in_r"]
                                  + (staerke if q_ < 0.2 else 0.0)})
        s = spanne(fuenftel_je_tag(gepflanzt, "raum_atr"))
        print("    gepflanzt %+.2f R -> Spanne %+.4f  (%s)"
              % (staerke, s, "gefunden" if (s < u or s > o_) else "NICHT gefunden"))


if __name__ == "__main__":
    main()
