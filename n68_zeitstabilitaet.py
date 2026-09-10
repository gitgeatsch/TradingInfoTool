# -*- coding: utf-8 -*-
"""N-68 — HAELT `schnitt` UEBER DIE ZEIT? Der Unterschied als EINE Frage (07.09.)

## ⚠️⚠️ Warum N-60 nicht weiterkam — ein Aufbaufehler, kein Datenmangel

N-60 hat gefragt: *traegt er in BULL?* und *traegt er in BAER?* **Zwei
halbierte Tests.** Jeder hatte die halbe Aussagekraft, und die eingebaute
Gegenprobe hat es angezeigt: `funding`, ein bekannt tragender Beitrag,
trug in KEINER Phase. Das war ein Befund ueber die Schichtung, nicht ueber
die Kandidaten.

> **Stabilitaet ist keine Frage nach zwei Effekten, sondern nach EINEM
> Unterschied.** Und der wird auf der ganzen Reihe getestet, nicht auf
> zwei Haelften.

    N-60   traegt A? (halbe Daten)  UND  traegt B? (halbe Daten)
    N-68   ist (A - B) von null zu trennen? (ganze Daten)

⚠️ Der zweite Test ist auch dann noch aussagekraeftig, wenn keiner der
beiden Einzeltests es ist.

## ⚠️⚠️ UND: ein Nullbefund braucht hier eine TRENNSCHAERFE

"Kein Unterschied gefunden" ist ohne sie wertlos - es koennte heissen
"stabil" oder "wir sehen nichts". Deshalb wird ein Unterschied
**gepflanzt** und geprueft, ab welcher Groesse er gefunden wird. Erst
dann ist die Aussage `stabil bis X` moeglich - genau die vier Urteile der
Messnorm.

## Die Statistik — die REGISTRIERTE, nicht eine neue

    d[tag]  = je_tag_wirkung(sammle(...))        die Statistik aus N-59
    n[tag]  = dasselbe mit GEMISCHTEN Raengen, ueber ZIEH Ziehungen
    e[tag]  = d[tag] - n[tag]                    entzerrt, je Tag

⚠️ Die Entzerrung ist hier doppelt wichtig: N-65 hat gezeigt, dass die
rohe Statistik bei kleinen Gruppen nach oben verzerrt ist. Fuer einen
UNTERSCHIED zweier Zeitraeume hebt sich eine konstante Verzerrung zwar
auf - aber nur, wenn die Gruppengroessen gleich bleiben. Das ist nicht
garantiert, also wird je Tag entzerrt.

## Drei Schnitte, jeder mit eigener Begruendung

    HAELFTEN     der einfachste Schnitt. Schwaeche: Epoche und Marktlage
                 sind verwechselbar.
    BTC-TREND    BTC ueber/unter seinem 200-Schnitt. Die Phasen WECHSELN
                 sich ab - Schichter und Epoche sind getrennt (N-60s
                 eigene Begruendung, sie war richtig).
    JAHRE        kein Test, sondern der VERLAUF. Er zeigt, ob ein
                 Unterschied aus einem einzelnen Jahr kommt.

## ⚠️⚠️ Das gemessene NIVEAU des Tests — er ist nicht neutral

Vorabtest auf Kunstdaten, 40 Laeufe je Fall (`n68` Vorabtest 07.09.):

    Wahrheit 0, unkorreliert       18 % Fehlalarm   (nominell 10 %)
    Wahrheit 0, autokorreliert     22 % Fehlalarm
    Unterschied +0,03             100 % gefunden
    Unterschied +0,05             100 % gefunden

**Der Test erklaert zu OFT einen Unterschied.** Daraus folgt eine
Leseregel, und sie gilt in beide Richtungen:

    "kein Unterschied"  ist STARK - ein trigger-happy Test hat nichts
                        gefunden
    "UNTERSCHIED"       ist VORSICHTIG zu lesen - jeder fuenfte koennte
                        Fehlalarm sein

⚠️ Der erste Vorabtest prueft EINEN Fall und nannte ihn "falsch". Ein
90-%-Band erlaubt Fehlalarme; eine Ziehung kann das nicht zeigen. Eigener
Grundsatz (*eine Ziehung ist kein Nullpunkt*), selbst verletzt.

## Die Kontrollen — vorab benannt

    funding   traegt bekanntermassen. Findet der Unterschiedstest bei ihm
              KEINEN Unterschied, ist das eine Aussage ueber die
              Stabilitaet von funding - und ein Beleg, dass der Test
              ueberhaupt laeuft (die Trennschaerfe sagt, wie gut).
    zufall    darf keinen Unterschied zeigen. Zeigt er einen, ist der
              Aufbau kaputt.

    python n68_zeitstabilitaet.py
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
from messe_beitrag_auf_auswahl import momentum250, sammle    # noqa: E402
from messe_h_als_filter import btc_ueber_schnitt             # noqa: E402
from messnorm import _block                                   # noqa: E402
from messnorm_auswahl import MENGEN                           # noqa: E402
from pruefe_n31_tagesklammer import je_tag_wirkung           # noqa: E402

HORIZONT, MENGE = 20, "20%"
ZIEH, SAAT = 20, 20260907
ZIEHUNGEN_BAND = 2000
# ⚠️ Die gepflanzten Unterschiede stehen VOR dem Lauf fest.
GEPFLANZT = (0.02, 0.05, 0.10, 0.20)
MIN_BLOECKE = 20


def entzerrte_reihe(je_tag, mom, anteil, auswahl_saat=None):
    """e[tag] = echte Wirkung minus dem Nullwert desselben Tages.

    ## ⚠️⚠️ `auswahl_saat` — die Menge ZUFAELLIG statt nach Momentum

    Nachgetragen am 09.09.2026. N-88 hat gezeigt, dass `schnitt`s
    Haelftenunterschied NUR auf den schmalen Momentum-Mengen kippt
    (-0,431 bei 5 %, +0,197 bei 20 %) und auf den weiten ruhig ist
    (+0,002 bei 50 %, +0,018 auf `frei`).

    **Der Verdacht: Kollinearitaet mit der Auswahl.** `schnitt` und das
    250-Tage-Momentum korrelieren mit Spearman +0,704 - auf der
    Momentumspitze liegen fast alle Werte ueber ihrem eigenen Schnitt,
    also bleibt kaum Streuung uebrig, und die Messung wird instabil.

    Mit `auswahl_saat` wird je Tag GLEICH VIEL gewaehlt, aber zufaellig.
    Traegt die Instabilitaet dann nicht mehr, ist sie eine Eigenschaft der
    AUSWAHL und nicht von `schnitt`.

    ⚠️ Es ist eine SAAT, kein Generator - `sammle` verbraucht je Tag
    Zufall, und die Nullziehungen muessten sonst eine ANDERE Auswahl
    sehen als die Hauptmessung.
    """
    def _aw():
        return (None if auswahl_saat is None
                else np.random.default_rng(int(auswahl_saat)))
    echt = je_tag_wirkung(sammle(je_tag, mom, anteil, mische_auswahl=_aw()))
    summe, zahl = {}, {}
    for z in range(ZIEH):
        n = je_tag_wirkung(sammle(je_tag, mom, anteil,
                                  mische_rang=np.random.default_rng(SAAT + z),
                                  mische_auswahl=_aw()))
        for t, v in n.items():
            summe[t] = summe.get(t, 0.0) + v
            zahl[t] = zahl.get(t, 0) + 1
    return {t: v - (summe[t] / zahl[t] if zahl.get(t) else 0.0)
            for t, v in echt.items()}


def _bloecke(v, block, rng, zieh):
    """Blockbootstrap-Ziehungen des Mittelwerts einer Reihe."""
    starts = np.arange(len(v) - block + 1)
    n = int(np.ceil(len(v) / block))
    z = np.empty(zieh)
    for i in range(zieh):
        s = rng.choice(starts, n)
        z[i] = np.mean(np.concatenate([v[j:j + block] for j in s])[:len(v)])
    return z


def unterschied(e, mengeA, mengeB, block, saat=SAAT, zieh=ZIEHUNGEN_BAND,
                versatz=0.0, zentriere=False):
    """Band fuer (Mittel A - Mittel B), Bloecke je Menge getrennt gezogen.

    `versatz` addiert einen Betrag auf A - so wird ein Unterschied
    GEPFLANZT und die Trennschaerfe messbar.

    ⚠️⚠️ `zentriere` MUSS FUER DIE TRENNSCHAERFE GESETZT WERDEN
    (07.09.2026, eigener Fehler). Die erste Fassung pflanzte auf die
    ECHTE Reihe - also auf einen bereits vorhandenen Unterschied. Ist der
    schon trennbar, bleibt er es bei jedem Versatz, und die gemeldete
    "Trennschaerfe ab 0,02 R" heisst nur "der echte Effekt ist gross",
    nicht "ein Effekt von 0,02 waere gefunden worden".

    Mit `zentriere=True` wird A zuerst auf Bs Mittelwert gezogen. Dann
    misst der gepflanzte Versatz das, was er messen soll: ab welcher
    Groesse ein Unterschied AUS DEM NICHTS gefunden wird.
    """
    ta = sorted(t for t in e if t in mengeA)
    tb = sorted(t for t in e if t in mengeB)
    if len(ta) < 2 * block or len(tb) < 2 * block:
        return None
    va = np.array([e[t] for t in ta], float)
    vb = np.array([e[t] for t in tb], float)
    if zentriere:
        va = va - va.mean() + vb.mean()
    va = va + versatz
    rng = np.random.default_rng(saat)
    za = _bloecke(va, block, rng, zieh)
    zb = _bloecke(vb, block, rng, zieh)
    d = za - zb
    return {"A": float(va.mean()), "B": float(vb.mean()),
            "diff": float(va.mean() - vb.mean()),
            "unten": float(np.percentile(d, 5)),
            "oben": float(np.percentile(d, 95)),
            "nA": len(ta), "nB": len(tb),
            "blA": len(ta) // block, "blB": len(tb) // block}


def stabilitaetsurteil(e, block, staerken=None):
    """EIN Stabilitaetsurteil mit VIER moeglichen Werten - und Trennschaerfe.

    ## ⚠️⚠️⚠️ WARUM ES DIESE FUNKTION GIBT (10.09.2026)

    `n102_vierfachtest.py:135` entschied Kriterium 2 so:

        "stabil": bool(d["unten"] <= 0.0 <= d["oben"])

    **,Stabil' hiess dort nur: das Band schliesst die Null ein.** Ein
    NICHT-Verwerfen, als Haken ausgegeben - und mit einer Richtung, die
    den falschen Kandidaten belohnt:

    > **Je BREITER das Band, desto sicherer das ✔.**

    Gemessen an `schnitt`, dessen Baender rund sechsmal breiter sind als
    `funding`s: er bestand Kriterium 2 nicht, weil er stabil ist,
    sondern weil er unruhig ist. Richtig gemessen faellt er (Diff
    +0,1973 [+0,0717 .. +0,3892] auf der 20-%-Menge).

    ## Die vier Urteile - dieselben wie in `messnorm`

        NICHT STABIL      Band schliesst die Null aus -> ein Unterschied
                          ist NACHGEWIESEN
        STABIL BIS X      |diff| unter der Trennschaerfe -> Unterschiede
                          ab X sind ausgeschlossen. Eine AUSSAGE.
        NICHT TRENNBAR    |diff| ueber X, Band haelt die Null - KEINE
                          Aussage
        KEIN BEFUND       selbst der groesste Versatz wurde nicht gefunden

    ⚠️ Die Reihenfolge folgt 2.193: `traegt` steht VOR der
    Untermacht-Abfrage. Das Band schliesst die Null aus oder nicht; die
    Positivkontrolle aendert daran nichts.

    ## ⚠️⚠️ DIE LEITER IST NICHT DIE ,R'-LEITER DER NORM

    Hier wird der Versatz DIREKT auf die entzerrte Reihe gepflanzt, also
    1:1. `messnorm` pflanzt gegen den Nullpunkt mit der Daempfung aus
    GRENZE = 0,80. **Ein ,bis 0,20' hier ist nicht mit einem ,0,05 R'
    dort zu vergleichen.**

    ⚠️ `zentriere=True` ist Pflicht - sonst wird auf einen bereits
    vorhandenen Unterschied gepflanzt (eigener Fehler 07.09., siehe
    `unterschied`).
    """
    if staerken is None:
        import messnorm as _N
        staerken = _N.STAERKEN
    tage = sorted(e)
    if len(tage) < 4 * block:
        return None
    mitte = tage[len(tage) // 2]
    A = {t for t in e if t < mitte}
    Bm = {t for t in e if t >= mitte}
    d = unterschied(e, A, Bm, block)
    if d is None:
        return None
    ts = None
    for st in staerken:
        p = unterschied(e, A, Bm, block, versatz=st, zentriere=True)
        if p is not None and p["unten"] > 0.0:
            ts = st
            break
    nachgewiesen = not (d["unten"] <= 0.0 <= d["oben"])
    if nachgewiesen:
        u = "NICHT STABIL - Unterschied nachgewiesen"
    elif ts is None:
        u = ("KEIN BEFUND - selbst %+.2f gepflanzt nicht gefunden"
             % max(staerken))
    elif abs(d["diff"]) < ts:
        u = ("STABIL BIS %.2f (Unterschiede ab dieser Groesse "
             "ausgeschlossen)" % ts)
    else:
        u = ("NICHT TRENNBAR - Diff %+.4f ueber %.2f, Band haelt Null"
             % (d["diff"], ts))
    return {"diff": d["diff"], "unten": d["unten"], "oben": d["oben"],
            "ts": ts, "urteil": u, "stabil": (not nachgewiesen) and
            ts is not None and abs(d["diff"]) < ts,
            "nachgewiesen": nachgewiesen,
            "blA": d["blA"], "blB": d["blB"]}


def main() -> int:
    t0 = time.time()
    print("=" * 98)
    print("N-68 — Zeitstabilitaet als EINE Frage: ist der Unterschied trennbar?")
    print("=" * 98)
    reihen = B.lade()
    mom = momentum250(reihen)
    anteil = MENGEN[MENGE]
    block = _block(HORIZONT)
    zus = {"funding": F.lade_funding(),
           "turnover": MB.reihe("data/onchain_historie.db", "splycur")}
    trend = btc_ueber_schnitt()
    print("  %d Reihen . Menge %s . H%d . Block %d . %d Nullziehungen"
          % (len(reihen), MENGE, HORIZONT, block, ZIEH))

    reihenwerte = {}
    for art in ("schnitt", "funding", "zufall"):
        je = K.baue(reihen, art, zus.get(art), horizont=HORIZONT)
        reihenwerte[art] = entzerrte_reihe(je, mom, anteil)
        print("     %-9s %d Kalendertage, Gesamtwirkung %+.4f R"
              % (art, len(reihenwerte[art]),
                 float(np.mean(list(reihenwerte[art].values())))), flush=True)

    tage = sorted(reihenwerte["schnitt"])
    mitte = tage[len(tage) // 2]
    schnitte = {
        "HAELFTEN": ({t for t in tage if t < mitte},
                     {t for t in tage if t >= mitte}, "erste", "zweite"),
        "BTC-TREND": ({t for t in tage if trend.get(t) is True},
                      {t for t in tage if trend.get(t) is False},
                      "BULL", "BAER"),
    }

    # ---- 1  DIE BLOCKZAHL, vor jeder Deutung ---------------------------
    print()
    print("  1  ⚠️ DIE BLOCKZAHL JE SEITE — vor der Deutung")
    print("     %-12s %-8s %8s %9s   %-8s %8s %9s"
          % ("Schnitt", "A", "Tage", "Bloecke", "B", "Tage", "Bloecke"))
    for lab, (ma, mb, na, nb) in schnitte.items():
        print("     %-12s %-8s %8d %9d   %-8s %8d %9d  %s"
              % (lab, na, len(ma), len(ma) // block, nb, len(mb),
                 len(mb) // block,
                 "✔" if min(len(ma), len(mb)) // block >= MIN_BLOECKE
                 else "⚠️ eine Seite unter %d" % MIN_BLOECKE))

    # ---- 2  DER UNTERSCHIEDSTEST ---------------------------------------
    print()
    print("  2  IST DER UNTERSCHIED VON NULL ZU TRENNEN?")
    print("     %-12s %-9s %9s %9s %9s %22s  %s"
          % ("Schnitt", "Kandidat", "A", "B", "A-B", "Band", "Urteil"))
    erg = {}
    for lab, (ma, mb, na, nb) in schnitte.items():
        for art in ("schnitt", "funding", "zufall"):
            u = unterschied(reihenwerte[art], ma, mb, block)
            if u is None:
                print("     %-12s %-9s  zu wenige Tage" % (lab, art))
                continue
            erg[(lab, art)] = u
            trennt = u["unten"] > 0 or u["oben"] < 0
            print("     %-12s %-9s %+9.4f %+9.4f %+9.4f [%+.4f .. %+.4f]  %s"
                  % (lab, art, u["A"], u["B"], u["diff"], u["unten"],
                     u["oben"],
                     "⚠️ UNTERSCHIED" if trennt else "kein Unterschied"),
                  flush=True)
        print()

    # ---- 3  DIE TRENNSCHAERFE — was wuerde gefunden? -------------------
    print("  3  ⚠️⚠️ TRENNSCHAERFE — welcher Unterschied wuerde gefunden?")
    print("     %-12s %-9s %s" % ("Schnitt", "Kandidat", "gepflanzt -> gefunden"))
    schaerfe = {}
    for lab, (ma, mb, _na, _nb) in schnitte.items():
        for art in ("schnitt", "funding"):
            gef, kleinste = [], None
            for g in GEPFLANZT:
                treffer = 0
                for z in range(5):
                    u = unterschied(reihenwerte[art], ma, mb, block,
                                    saat=SAAT + 100 * z, zieh=400, versatz=g)
                    if u and (u["unten"] > 0 or u["oben"] < 0):
                        treffer += 1
                gef.append("%.2f:%d/5" % (g, treffer))
                if kleinste is None and treffer >= 4:
                    kleinste = g
            schaerfe[(lab, art)] = kleinste
            print("     %-12s %-9s %s   -> %s"
                  % (lab, art, "  ".join(gef),
                     "ab %.2f R" % kleinste if kleinste
                     else "⚠️ nicht einmal %.2f R" % max(GEPFLANZT)),
                  flush=True)

    # ---- 4  DER VERLAUF je Jahr ----------------------------------------
    print()
    print("  4  DER VERLAUF — je Kalenderjahr (kein Test, eine Ansicht)")
    jahre = sorted({t[:4] for t in tage})
    print("     %-6s %8s %10s %10s %10s"
          % ("Jahr", "Tage", "schnitt", "funding", "zufall"))
    for j in jahre:
        tj = [t for t in tage if t.startswith(j)]
        if len(tj) < 60:
            continue
        z = []
        for art in ("schnitt", "funding", "zufall"):
            w = [reihenwerte[art][t] for t in tj if t in reihenwerte[art]]
            z.append(float(np.mean(w)) if w else float("nan"))
        print("     %-6s %8d %+10.4f %+10.4f %+10.4f"
              % (j, len(tj), z[0], z[1], z[2]))

    # ---- Urteil ---------------------------------------------------------
    print()
    print("=" * 98)
    print("WAS DAS HEISST")
    print("=" * 98)
    kaputt = [lab for lab, art in erg
              if art == "zufall" and (erg[(lab, art)]["unten"] > 0
                                      or erg[(lab, art)]["oben"] < 0)]
    if kaputt:
        print("  ⚠️⚠️ `zufall` zeigt einen Unterschied in %s - der Aufbau"
              % ", ".join(kaputt))
        print("     ist kaputt, alles Weitere wertlos.")
        print("  Dauer %.1f Minuten" % ((time.time() - t0) / 60.0))
        return 1
    print("  ✔ `zufall` zeigt in keinem Schnitt einen Unterschied.")
    print()
    for lab in schnitte:
        u = erg.get((lab, "schnitt"))
        s = schaerfe.get((lab, "schnitt"))
        if u is None:
            continue
        trennt = u["unten"] > 0 or u["oben"] < 0
        if trennt:
            print("  ⚠️⚠️ %-10s `schnitt` IST instabil: %+.4f R Unterschied"
                  % (lab, u["diff"]))
            print("       [%+.4f .. %+.4f] - das Band schliesst null aus."
                  % (u["unten"], u["oben"]))
        elif s is None:
            print("  ○ %-10s kein Unterschied gefunden - ABER die"
                  % lab)
            print("       Trennschaerfe reicht nicht einmal fuer %.2f R."
                  % max(GEPFLANZT))
            print("       ⚠️ Das ist KEIN Stabilitaetsnachweis, sondern")
            print("          Untermacht. Genau wie bei N-60.")
        else:
            print("  ✔ %-10s `schnitt` ist STABIL BIS %.2f R: der"
                  % (lab, s))
            print("       Unterschied betraegt %+.4f R [%+.4f .. %+.4f],"
                  % (u["diff"], u["unten"], u["oben"]))
            print("       und ein Unterschied von %.2f R waere gefunden"
                  % s)
            print("       worden. Das ist eine AUSSAGE, kein Nullbefund.")
    print("  Dauer %.1f Minuten" % ((time.time() - t0) / 60.0))
    return 0


if __name__ == "__main__":
    sys.exit(main())
