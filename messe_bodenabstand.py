# -*- coding: utf-8 -*-
"""Der ABSTAND ZUR NAECHSTEN UNTERSTUETZUNG als Beitrag (31.08.2026)

⚠️ DIESER KOPF IST DIE VORABFESTLEGUNG, geschrieben BEVOR gerechnet wurde.

## Woher die Groesse kommt

Am 30.08. ist H zerlegt worden (`messe_h3_totzone_und_kombination.py`,
`messe_b2_unabhaengigkeit.py`, 621.072 Anker). Ergebnis:

    A  freier Weg oben       trifft  4,0 %   +0,0089 R   traegt nicht
                             und INNERHALB beider B-Schichten negativ
                             (-0,0568 / -0,1451) - es zieht nach unten
    B  Boden unten           trifft 85,7 %   -0,2023 R   ⚠️ ueber der Huerde
    H  = A UND B             trifft  2,2 %   -0,1476 R

**B ist in H als POSITIVE Bedingung eingebaut und wirkt NEGATIV.** Und die
Korrektur allein reicht nicht: `A UND NICHT B` liegt bei +0,1471, aber unter
der Huerde - weil A die Menge auf 1,8 % verengt. Die einfachste Form ist die
beste: `NICHT B` allein traegt +0,2023 bei 14,3 %.

⚠️ DER EIGENTLICHE BEFUND IST ABER STETIG, nicht binaer. Disjunkt nach
Abstandsband gerechnet ist der Verlauf MONOTON:

    naechste Unterstuetzung in [0,25 .. 0,50) ATR   +0,1067   ( 2,3 %)
                                [0,50 .. 1,00)      +0,0360   ( 6,9 %)
                                [1,00 .. 1,50)      -0,0045   (20,1 %)
                                [1,50 .. 2,00)      -0,1030   (58,6 %)

Der Schaden sitzt unmittelbar UEBER DEM STOP (der bei 2,0 ATR liegt).

## Was diese Messung klaeren muss - und warum genau das

Nutzervorgabe 31.08.: *"Ziel ist den Beitrag in korrekter Form zu nutzen."*
Die Groesse ist damit noch nicht so durchgemessen wie Funding und Turnover.
Es fehlen genau die Pruefungen, die dort entschieden haben:

  P1 DIE FORM        feste ATR-Baender oder Querschnittsrang je Kalendertag?
                     ⚠️ Feste Grenzen sind K3 - eine der vier ungepruesften
                     Annahmen. Der Bezug zum Stop spricht fuer feste Baender
                     (der Stop liegt bei 2,0 ATR, die Baender sind relativ
                     dazu definiert). Ein Querschnittsrang wuerde genau diese
                     Beziehung zerstoeren. Gemessen werden BEIDE.
  P2 ALS REGEL       nicht als Merkmal. Bei Funding betrug der Unterschied
                     den Faktor 5,5 (Merkmal +0,132 R, Regel +0,024 R).
                     Drei Zahlen: wieviele Faelle · waren die schlechter ·
                     was bleibt netto.
  P3 SURVIVORSHIP    daran waere Turnover fast gescheitert. Geprueft wird,
                     ob die Groesse bei EINGESTELLTEN Reihen anders wirkt.
  P4 ROBUSTHEIT      Beruehrungszahl 2/3/4, beide Historienhaelften, drei
                     Zeitabschnitte, fuenf Volatilitaets-Fuenftel.
  P5 BEITRAGSTABELLE Punkte je Stufe, geschrumpft - wie
                     `rechne_funding_beitrag.py`.

## Vorab festgelegt, VOR der ersten Zahl

  nutzbar        monoton ueber die Stufen, ausserhalb des Placebo-Bandes,
                 beide Historienhaelften gleiches Vorzeichen, kein
                 Survivorship-Artefakt, UND als REGEL wirksam
  nur Merkmal    traegt als Merkmal, aber die Regel bringt nichts
  nicht nutzbar  sonst

    python messe_bodenabstand.py
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

from messe_marken import (CRV, K, MAX_TAGE,                       # noqa: E402
                          _niveaus_schnell, _SwingSpeicher)
from simuliere_bremse import _reihen_roh, klassen_aus_db          # noqa: E402

CACHE = "anker_boden_2026_08_31.json"
HORIZONT = 20
MINDESTALTER = 250
BRUCH = 5.0
BLOCK = 120
MIND_JE_GRUPPE = 30
MIND_JE_TAG = 15
PLACEBO_LAEUFE = 40
# ⚠️ TOTZONE 0,25 STATT DES PRODUKTIONSWERTS 0,5 - und das ist kein
# Abweichen, sondern die Voraussetzung dafuer, dass die Messung ueberhaupt
# fuenf Stufen hat. Bei 0,5 existiert per Definition KEINE Marke naeher als
# 0,5 ATR; die Stufe "Boden ganz nah am Kurs" waere systematisch leer, und
# die Messung haette vier Stufen statt fuenf gemeldet, ohne dass es
# aufgefallen waere. Vor dem Lauf bemerkt, nicht danach.
#
# Der Produktionswert 0,5 laeuft in P4 als eigene Zeile mit - dort ist
# ablesbar, was das nahe Band beitraegt.
TOTZONE = 0.25
BERUEHRUNGEN = (2, 3, 4)
# Feste Baender in ATR - der Stop liegt bei K = 2,0 ATR
BAENDER = ((0.25, 0.5), (0.5, 1.0), (1.0, 1.5), (1.5, 2.0))


def _ausgang(c, h, l, i, stop, ziel):
    for j in range(i + 1, min(i + 1 + MAX_TAGE, len(c))):
        if l[j] <= stop:
            return "stop"
        if h[j] >= ziel:
            return "ziel"
    return "abgelaufen"


def laufe(db="data/messdaten.db", klasse="krypto"):
    from messe_funding_niveau import lade_funding
    try:
        funding = lade_funding()
        print("Funding geladen: %d Symbole" % len(funding), flush=True)
    except Exception as exc:                                 # noqa: BLE001
        print("⚠️ Funding nicht ladbar (%s)" % exc, flush=True)
        funding = {}

    roh = _reihen_roh(db, klasse, klassen_aus_db(db))
    # ⚠️ SURVIVORSHIP: wann endet die Reihe? Wer frueh endet, ist eingestellt.
    ende = {sym: d[-1] for sym, (c, h, l, v, a, off, d) in roh.items()}
    letztes = max(ende.values())
    print("Letztes Datum im Bestand: %s" % letztes, flush=True)

    aus = []
    t0 = letzte = time.time()
    for nr, (sym, (c, h, l, v, a, off, d)) in enumerate(roh.items(), 1):
        del v
        sp = _SwingSpeicher(h, l)
        f_sym = funding.get(sym.upper(), {})
        # "lebt" = die Reihe reicht bis in die letzten 30 Tage des Bestands
        lebt = ende[sym] >= letztes[:8] + "01"
        cc = np.asarray(c, dtype=float)
        verh = cc[1:] / np.maximum(cc[:-1], 1e-12)
        bruch = (verh > BRUCH) | (verh < 1.0 / BRUCH)
        for i in range(off + 1 + MINDESTALTER, len(c) - HORIZONT - 1):
            atr, kurs = float(a[i - off]), float(c[i])
            if not (atr > 0 and kurs > 0):
                continue
            if bruch[i:i + HORIZONT].any():
                continue
            n = _niveaus_schnell(sp, c, h, l, i, atr, totzone=TOTZONE)
            satz = {"sym": sym, "datum": d[i], "atr_rel": atr / kurs,
                    "lebt": bool(lebt), "funding": f_sym.get(d[i]),
                    "in_r": (float(c[i + HORIZONT]) - kurs) / (K * atr)}
            ag = _ausgang(c, h, l, i, kurs - K * atr, kurs + CRV * K * atr)
            satz["ziel"] = (1.0 if ag == "ziel"
                            else 0.0 if ag == "stop" else None)
            for mb in BERUEHRUNGEN:
                unten = [(kurs - m["preis"]) / atr for m in n["unten"]
                         if m["beruehrungen"] >= mb]
                # ⚠️ DER NAECHSTE Boden - der kleinste Abstand. `None` heisst
                # "kein Boden im Band bis zum Stop", NICHT "Abstand 0".
                nah = [x for x in unten if x < K]
                satz["boden_%d" % mb] = min(nah) if nah else None
            aus.append(satz)
        if time.time() - letzte >= 60:
            letzte = time.time()
            print("  [%4.1f min] Reihe %d/%d - %d Anker"
                  % ((letzte - t0) / 60, nr, len(roh), len(aus)), flush=True)
    return aus


# ------------------------------------------------------------- Werkzeuge
def stufe_fest_geordnet(a, mb=2):
    """Stufe 0 = ferner Boden (schlecht) ... 4 = kein Boden (gut).

    ⚠️ DIE ORDNUNG IST DER BEFUND, nicht eine Wahl. Gemessen ist:
    ferner Boden schlecht, naher Boden gut, kein Boden am besten. Die
    Stufen laufen deshalb von schlecht nach gut - genau wie bei Funding
    und Turnover, wo Fuenftel 0 der niedrigste Rohwert ist.
    """
    w = a.get("boden_%d" % mb)
    if w is None:
        return 4                                    # kein Boden
    if w >= 1.5:
        return 0                                    # unmittelbar ueber Stop
    if w >= 1.0:
        return 1
    if w >= 0.5:
        return 2
    return 3                                        # ganz nah am Kurs


def je_block(anker, schluessel, feld="in_r", bedingung=None, block=BLOCK):
    lage = (lambda x: float(np.mean(x))) if feld == "ziel" else st.median
    teil = [a for a in anker if bedingung is None or bedingung(a)]
    tage = sorted({a["datum"] for a in teil})
    if len(tage) < 2 * block:
        return None
    zu = {t: i // block for i, t in enumerate(tage)}
    eimer = {}
    for a in teil:
        if a.get(feld) is None:
            continue
        k = schluessel(a)
        if k is None:
            continue
        eimer.setdefault(zu[a["datum"]], ([], []))[0 if k else 1] \
            .append(float(a[feld]))
    w = [lage(m) - lage(o) for m, o in eimer.values()
         if len(m) >= MIND_JE_GRUPPE and len(o) >= MIND_JE_GRUPPE]
    return w if len(w) >= 5 else None


def stufen_wirkung(anker, stufe, feld="in_r", bedingung=None, mische=None):
    """Median je Stufe, JE KALENDERTAG gebildet - wie bei Funding."""
    je_tag = {}
    for a in anker:
        if bedingung is not None and not bedingung(a):
            continue
        if a.get(feld) is None:
            continue
        je_tag.setdefault(a["datum"], []).append(a)
    sammel = {k: [] for k in range(5)}
    for tag, z in je_tag.items():
        if len(z) < MIND_JE_TAG:
            continue
        st_ = [stufe(x) for x in z]
        if mische is not None:
            st_ = list(mische.permutation(st_))
        y = [x[feld] for x in z]
        for k in range(5):
            teil = [v for s, v in zip(st_, y) if s == k]
            if len(teil) >= 2:
                sammel[k].append(float(np.median(teil)))
    if any(len(sammel[k]) < 30 for k in range(5)):
        return None
    return [st.mean(sammel[k]) for k in range(5)]


def spanne(w):
    return None if w is None else w[4] - w[0]


def zeige(titel, w, einheit="R", einzug=2):
    if w is None:
        print("%s%-40s zu wenige Tage" % (" " * einzug, titel))
        return None
    print("%s%-40s %s   Spanne %+.4f %s"
          % (" " * einzug, titel, " ".join("%+.3f" % x for x in w),
             spanne(w), einheit))
    return spanne(w)


def main():
    if os.path.exists(CACHE):
        anker = json.loads(io.open(CACHE, encoding="utf-8").read())
        print("%d Anker aus dem Zwischenspeicher." % len(anker))
    else:
        print("Lade Anker (523 Reihen) - das dauert...", flush=True)
        anker = laufe()
        io.open(CACHE, "w", encoding="utf-8").write(json.dumps(anker))
        print("Zwischengespeichert -> %s" % CACHE)
    rng = np.random.default_rng(20260831)
    n = len(anker)
    ohne = sum(1 for a in anker if a.get("boden_2") is None)
    lebt = sum(1 for a in anker if a["lebt"])

    print()
    print("=" * 104)
    print("DER ABSTAND ZUR NAECHSTEN UNTERSTUETZUNG — ALS BEITRAG")
    print("=" * 104)
    print("%d Anker, %d Symbole, %s .. %s"
          % (n, len({a["sym"] for a in anker}),
             min(a["datum"] for a in anker), max(a["datum"] for a in anker)))
    print("kein Boden bis zum Stop: %d (%.1f %%)   aus lebenden Reihen: %.1f %%"
          % (ohne, 100 * ohne / n, 100 * lebt / n))

    # ------------------------------------------------------------- P1
    print()
    print("=" * 104)
    print("P1 — DIE FORM: feste ATR-Baender ODER Querschnittsrang?")
    print("=" * 104)
    print("  Stufe 0 = Boden unmittelbar ueber dem Stop (>= 1,5 ATR)")
    print("  Stufe 4 = KEIN Boden bis zum Stop")
    print()
    print("  FESTE BAENDER (der Bezug zum Stop bleibt erhalten):")
    fest = stufen_wirkung(anker, stufe_fest_geordnet)
    zeige("Bewegung in R", fest, "R", 4)
    zeige("Ziel vor Stop", stufen_wirkung(anker, stufe_fest_geordnet, "ziel"),
          " ", 4)

    print()
    print("  QUERSCHNITTSRANG je Kalendertag (wie Funding/Turnover):")
    print("  ⚠️ Anker OHNE Boden koennen hier nicht eingeordnet werden -")
    print("     sie laufen als eigene Gruppe und fehlen im Rang.")
    je_tag = {}
    for a in anker:
        if a.get("boden_2") is not None:
            je_tag.setdefault(a["datum"], []).append(a)
    for tag, z in je_tag.items():
        if len(z) < MIND_JE_TAG:
            for x in z:
                x["rang"] = None
            continue
        w = np.array([x["boden_2"] for x in z], dtype=float)
        r = np.argsort(np.argsort(-w)) / max(len(w) - 1, 1)   # weit = Stufe 0
        for x, q in zip(z, r):
            x["rang"] = min(int(q * 5), 4)
    quer = stufen_wirkung([a for a in anker if a.get("rang") is not None],
                          lambda a: a["rang"])
    zeige("Bewegung in R", quer, "R", 4)

    print()
    if fest and quer:
        print("  -> feste Baender %+.4f R   Querschnitt %+.4f R"
              % (spanne(fest), spanne(quer)))
        print("  -> %s"
              % ("feste Baender tragen mehr - der Bezug zum Stop ist die "
                 "Information" if abs(spanne(fest)) > abs(spanne(quer))
                 else "⚠️ der Querschnitt traegt mehr - dann ist es eine "
                      "relative Groesse, keine Stopbeziehung"))

    # ------------------------------------------------------------- P4
    print()
    print("=" * 104)
    print("P4 — ROBUSTHEIT")
    print("=" * 104)
    print("  Beruehrungszahl:")
    for mb in BERUEHRUNGEN:
        zeige("mindestens %d Beruehrungen" % mb,
              stufen_wirkung(anker, lambda a, m=mb: stufe_fest_geordnet(a, m)),
              "R", 4)
    print()
    print("  ⚠️ Mit der PRODUKTIONS-Totzone 0,5 (Stufe 3 faellt dort weg):")
    zeige("Totzone 0,5 - nur Marken ab 0,5 ATR",
          stufen_wirkung(anker, lambda a: (
              4 if a.get("boden_2") is None or a["boden_2"] < 0.5
              else stufe_fest_geordnet(a))), "R", 4)
    print("     (Anker mit Boden naeher als 0,5 ATR zaehlen dort als 'kein")
    print("      Boden' - genau so sieht die Produktion sie heute.)")
    print()
    print("  Historienhaelften:")
    tage = sorted({a["datum"] for a in anker})
    mitte = tage[len(tage) // 2]
    for name, bed in (("erste Haelfte", lambda a: a["datum"] < mitte),
                      ("zweite Haelfte", lambda a: a["datum"] >= mitte)):
        zeige(name, stufen_wirkung(anker, stufe_fest_geordnet, bedingung=bed),
              "R", 4)
    print()
    print("  Zeitabschnitte:")
    for name, von, bis in (("2018-2020", "2018-01-01", "2020-12-31"),
                           ("2021-2023", "2021-01-01", "2023-12-31"),
                           ("2024-2026", "2024-01-01", "2026-12-31")):
        zeige(name, stufen_wirkung(
            anker, stufe_fest_geordnet,
            bedingung=lambda a, v=von, b=bis: v <= a["datum"] <= b), "R", 4)
    print()
    print("  Volatilitaets-Fuenftel (daran starb 'ohne Widerstand'):")
    q = np.quantile([a["atr_rel"] for a in anker], [0, .2, .4, .6, .8, 1.0])
    for i in range(5):
        zeige("ATR-Fuenftel %d" % i, stufen_wirkung(
            anker, stufe_fest_geordnet,
            bedingung=lambda a, u=q[i], o=q[i + 1]: u <= a["atr_rel"] <= o),
            "R", 4)

    # ------------------------------------------------------------- P3
    print()
    print("=" * 104)
    print("P3 — SURVIVORSHIP: wirkt es bei EINGESTELLTEN Reihen anders?")
    print("=" * 104)
    for name, bed in (("lebende Reihen", lambda a: a["lebt"]),
                      ("eingestellte Reihen", lambda a: not a["lebt"])):
        zeige(name, stufen_wirkung(anker, stufe_fest_geordnet, bedingung=bed),
              "R", 4)

    # ------------------------------------------------------------- P2
    print()
    print("=" * 104)
    print("P2 — ALS REGEL, NICHT ALS MERKMAL (bei Funding Faktor 5,5)")
    print("=" * 104)
    print('  Die Regel: "kein Einstieg, wenn der Boden unmittelbar ueber dem')
    print('  Stop liegt" (Stufe 0). Drei Zahlen, wie bei Funding:')
    gesperrt = [a for a in anker if stufe_fest_geordnet(a) == 0]
    bleibt = [a for a in anker if stufe_fest_geordnet(a) != 0]
    print("    wieviele Faelle:   %d von %d  (%.1f %% gesperrt)"
          % (len(gesperrt), n, 100 * len(gesperrt) / n))
    print("    waren die schlechter: Median %+.4f R gegen %+.4f R"
          % (st.median([a["in_r"] for a in gesperrt]),
             st.median([a["in_r"] for a in bleibt])))
    w = je_block(anker, lambda a: stufe_fest_geordnet(a) == 0)
    if w:
        b = np.array(w)
        print("    je Block:          %+.4f R  [%d/%d Bloecke +]"
              % (float(b.mean()), int((b > 0).sum()), len(b)))
    alle = st.median([a["in_r"] for a in anker])
    print("    was bleibt netto:  %+.4f R gegen %+.4f R ohne Regel  (%+.4f)"
          % (st.median([a["in_r"] for a in bleibt]), alle,
             st.median([a["in_r"] for a in bleibt]) - alle))

    # -------------------------------------------------------- Kontrollen
    print()
    print("=" * 104)
    print("KONTROLLEN")
    print("=" * 104)
    echt = spanne(fest)
    p = []
    for _ in range(PLACEBO_LAEUFE):
        w = stufen_wirkung(anker, stufe_fest_geordnet, mische=rng)
        if w:
            p.append(spanne(w))
    p = np.array(p)
    u, o = np.quantile(p, [0.025, 0.975])
    print("  NEGATIV (Stufen je Tag gemischt, Verteilung bleibt exakt):")
    print("    Band %+.4f .. %+.4f (Mitte %+.4f, %d Laeufe)"
          % (u, o, float(p.mean()), len(p)))
    print("    echt %+.4f  ->  %s"
          % (echt, "AUSSERHALB - der Befund haelt" if (echt < u or echt > o)
             else "⚠️ INNERHALB - vom Zufall nicht zu trennen"))
    print()
    print("  POSITIV (Zuschlag auf Stufe 4, auf einem NULL-Datensatz):")
    null = []
    for a in anker:
        null.append({**a, "_stufe": None})
    # Bezug zerstoeren: Stufen je Tag mischen, dann pflanzen
    je_tag2 = {}
    for a in null:
        je_tag2.setdefault(a["datum"], []).append(a)
    for tag, z in je_tag2.items():
        st_ = rng.permutation([stufe_fest_geordnet(x) for x in z])
        for x, s_ in zip(z, st_):
            x["_stufe"] = int(s_)
    basis = spanne(stufen_wirkung(null, lambda a: a["_stufe"]))
    print("    Nulldatensatz: %+.4f R" % basis)
    for staerke in (0.02, 0.05, 0.10, 0.20):
        g = [{**a, "in_r": a["in_r"] + (staerke if a["_stufe"] == 4 else 0.0)}
             for a in null]
        s_ = spanne(stufen_wirkung(g, lambda a: a["_stufe"]))
        print("    gepflanzt %+.2f R -> Spanne %+.4f  (%s)"
              % (staerke, s_, "gefunden" if (s_ < u or s_ > o)
                 else "NICHT gefunden"))

    # ------------------------------------------------------------- P5
    print()
    print("=" * 104)
    print("P5 — DIE BEITRAGSTABELLE (wie rechne_funding_beitrag.py)")
    print("=" * 104)
    if fest:
        mittel = st.mean(fest)
        faktor = 1.0 / (1.0 + CRV)
        print("  Stufe  Bewegung   gegen Mittel   Punkte roh   GESCHRUMPFT")
        stufen = []
        for k in range(5):
            ab = fest[k] - mittel
            roh_ = 100.0 * ab * faktor
            stufen.append(round(roh_ / 2.0, 2))
            print("    %d    %+.4f R    %+.4f R      %+5.2f       %+5.2f"
                  % (k, fest[k], ab, roh_, roh_ / 2.0))
        print()
        print("  Fuer `wahrscheinlichkeit.BEITRAEGE`:")
        print("    stufen=(%s)," % ", ".join("%+.2f" % s for s in stufen))
        print()
        print("  ⚠️ Zum Vergleich: Funding +0,82/+1,30/+0,12/-0,54/-1,70")
        print("     Turnover        +3,15/+0,83/+0,22/-1,79/-2,40")
        print("     Vorfilter H     +4,50 als Schalter, bei 2,2 %% der Anker")


if __name__ == "__main__":
    main()
