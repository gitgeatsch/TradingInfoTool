# -*- coding: utf-8 -*-
"""HAT DER FUNDING-BEITRAG DIE RICHTIGE FORM? Zwei unabhaengige Wege.

⚠️⚠️⚠️ DIE VORABFESTLEGUNG STEHT IN
`Basisinfos/Vorabfestlegung_Funding_Form_23_09.md` UND WIRD HIER NICHT
NACHVERHANDELT. Sie nennt Fragestellung, Hypothesen und - das
Entscheidende - was welches Ergebnis BEDEUTET, geschrieben vor der
Messung.

## Die Frage

Ist die Wirkung von `funding` im Querschnittsrang MONOTON, oder hat sie
ein Maximum INNERHALB der Verteilung?

    H0  monoton fallend, Maximum am unteren Ende (heutige Festlegung
        im Werkzeug `rechne_funding_beitrag.py`)
    H1  nicht monoton, Maximum bei MODERAT niedrigem Funding
        (Praxisliteratur: extreme Raten in BEIDE Richtungen markieren
        gedraengte Positionierung)
    H2  der Buckel ist ein Artefakt der Gruppenbildung

## Zwei unabhaengige Wege

    A  DEZILE statt Fuenftel - andere Gruppengrenzen. Ein Schnittartefakt
       verschiebt sich, ein echtes Maximum bleibt.
    B  Gruppen nach dem ABSOLUTEN Funding-Niveau statt nach dem Tagesrang
       - kommt ohne den Rangschnitt aus, der in H2 verdaechtigt wird.

⚠️ Die Ladung ist dieselbe wie in `rechne_funding_beitrag.py` -
IMPORTIERT ueber `messe_eigenschaft_beitrag` und
`phase3_reproduktion.F`, nicht nachgebaut.

## Der Messstandard gilt vollstaendig

Blocklaenge aus `messnorm._block(H20)`, Band ueber Blockbootstrap, beide
Historienhaelften einzeln (R-R8 B6), Haeufigkeit je Gruppe (B4).

⚠️ NUR LESEND, gegen die Messbasis am Desktop.

    python phase4_funding_form.py
"""
from __future__ import annotations

import statistics as st
import sys

import numpy as np

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import messe_eigenschaft_beitrag as B                      # noqa: E402
import messnorm                                            # noqa: E402
import phase3_reproduktion as R                            # noqa: E402

HOR = 20
ZIEHUNGEN = 300


def lade_anker():
    """(Funding-Wert, Bewegung in R) je Kalendertag - wie im Werkzeug."""
    reihen = B.lade()
    funding = R.F.lade_funding()
    je_tag = {}
    for sym, roh in reihen.items():
        f = funding.get(sym.upper())
        if not f:
            continue
        tage = [z[0] for z in roh]
        c = np.array([z[1] for z in roh])
        h = np.array([z[2] for z in roh])
        t_ = np.array([z[3] for z in roh])
        breite = B.spanne(h, t_, c, B.SCHWANKUNG)
        for i in range(60, len(c) - HOR):
            r = breite[i]
            if not np.isfinite(r) or r <= 0 or tage[i] not in f:
                continue
            je_tag.setdefault(tage[i], []).append(
                (f[tage[i]], float((c[i + HOR] - c[i]) / r)))
    return {t: z for t, z in je_tag.items() if len(z) >= 15}


def weg_a(je_tag, tage, n=10):
    """RANGgruppen je Tag - wie heute, nur feiner. Gibt (Werte, Zahl)."""
    sammel = {k: [] for k in range(n)}
    zahl = {k: 0 for k in range(n)}
    for t in tage:
        z = je_tag[t]
        w = np.array([x[0] for x in z])
        y = np.array([x[1] for x in z])
        r = np.argsort(np.argsort(w)) / max(len(w) - 1, 1)
        for k in range(n):
            m = (r >= k / n) & (r < (k + 1) / n if k < n - 1 else r <= 1.0)
            if m.sum() >= 2:
                sammel[k].append(float(np.median(y[m])))
                zahl[k] += int(m.sum())
    return ([st.mean(sammel[k]) if sammel[k] else float("nan")
             for k in range(n)], zahl)


def weg_b(je_tag, tage, n=10):
    """Gruppen nach dem ABSOLUTEN Funding-Niveau.

    ⚠️⚠️ DAS IST DER UNABHAENGIGE WEG: die Grenzen kommen aus der
    Gesamtverteilung ALLER Werte, nicht aus dem Rang je Tag. Damit kann
    ein Schnittartefakt des Tagesrangs (H2) hier nicht dieselbe Form
    erzeugen.

    ⚠️ Die Kalendertag-Klammer bleibt trotzdem: gemittelt wird ueber die
    Tagesmediane, nicht ueber alle Punkte. Ohne sie vermischte man
    Marktlagen (R-R8 B2).
    """
    alle = np.array([x[0] for t in tage for x in je_tag[t]])
    grenzen = np.percentile(alle, [100.0 * k / n for k in range(1, n)])
    sammel = {k: [] for k in range(n)}
    zahl = {k: 0 for k in range(n)}
    for t in tage:
        z = je_tag[t]
        w = np.array([x[0] for x in z])
        y = np.array([x[1] for x in z])
        idx = np.searchsorted(grenzen, w, side="right")
        for k in range(n):
            m = idx == k
            if m.sum() >= 2:
                sammel[k].append(float(np.median(y[m])))
                zahl[k] += int(m.sum())
    return ([st.mean(sammel[k]) if sammel[k] else float("nan")
             for k in range(n)], zahl)


def band_diff(je_tag, tage, fn, a, b, n=10):
    """Blockbootstrap auf die Differenz Gruppe a minus Gruppe b."""
    block = messnorm._block(HOR)
    rng = np.random.default_rng(messnorm.SAAT)
    starts = np.arange(max(1, len(tage) - block + 1))
    anzahl = int(np.ceil(len(tage) / block))
    d = []
    for _ in range(ZIEHUNGEN):
        idx = rng.choice(starts, anzahl)
        tg = [tage[j] for s in idx
              for j in range(s, min(s + block, len(tage)))][:len(tage)]
        w, _z = fn(je_tag, tg, n)
        if np.isfinite(w[a]) and np.isfinite(w[b]):
            d.append(w[a] - w[b])
    d = np.array(d)
    return float(d.mean()), float(np.percentile(d, 5)), \
        float(np.percentile(d, 95))


def zeige(name, werte, zahl, n=10):
    print("     %-10s %s" % (name, "  ".join(
        "%d:%+.4f" % (k, werte[k]) if np.isfinite(werte[k]) else "%d:  --" % k
        for k in range(n))))
    print("     %-10s %s" % ("(Punkte)", "  ".join(
        "%d:%6d" % (k, zahl[k]) for k in range(n))))
    gueltig = [k for k in range(n) if np.isfinite(werte[k])]
    bester = max(gueltig, key=lambda k: werte[k])
    print("     ➤ hoechste Gruppe: %d von %d  %s"
          % (bester, n, "(MAXIMUM AM RAND)" if bester == 0
             else "(MAXIMUM IM INNEREN)"))
    return bester


def main() -> int:
    print("=" * 100)
    print("FUNDING - HAT DER BEITRAG DIE RICHTIGE FORM?")
    print("=" * 100)
    print("  Vorabfestlegung: Basisinfos/Vorabfestlegung_Funding_Form_23_09.md")
    print("  " + messnorm.standardzeile().replace("\n", "\n  "))
    print("\n  Anker laden ...")
    je_tag = lade_anker()
    alle = sorted(je_tag)
    m = len(alle) // 2
    print("  %d Kalendertage, %s bis %s" % (len(alle), alle[0], alle[-1]))

    ergebnis = {}
    for weg, fn in (("A  Dezile (Rang)", weg_a),
                    ("B  Dezile (absolutes Niveau)", weg_b)):
        print("\n" + "-" * 100)
        print("  WEG %s" % weg)
        print("-" * 100)
        w, z = fn(je_tag, alle)
        best = zeige("gesamt", w, z)
        haelften = []
        for nm, tg in (("1. Haelfte", alle[:m]), ("2. Haelfte", alle[m:])):
            wh, zh = fn(je_tag, tg)
            g = [k for k in range(10) if np.isfinite(wh[k])]
            bh = max(g, key=lambda k: wh[k])
            haelften.append(bh)
            print("     %-10s hoechste Gruppe %d  %s"
                  % (nm, bh, "innen" if bh else "am Rand"))
        # ⚠️ DIE TRENNSCHAERFE-FRAGE: uebersteigt der Abstand des Maximums
        # zur untersten Gruppe das Band? Vorab festgelegt in § 4.
        if best != 0:
            d, u, o = band_diff(je_tag, alle, fn, best, 0)
            print("     Abstand Gruppe %d minus Gruppe 0: %+.4f R "
                  "[%+.4f .. %+.4f]" % (best, d, u, o))
            belegt = u > 0
            print("     %s" % ("✔ Band schliesst die Null AUS - "
                               "Maximum im Inneren BELEGT" if belegt else
                               "⚠ Band schliesst die Null EIN - nicht "
                               "von Rauschen zu trennen"))
        else:
            belegt = False
            print("     Maximum liegt am Rand - kein Abstand zu pruefen")
        ergebnis[weg[0]] = (best != 0, belegt, haelften)

    # ---- DIE ENTSCHEIDUNG NACH DER VORABFESTLEGUNG -------------------
    print("\n" + "=" * 100)
    print("  DIE ENTSCHEIDUNG - nach der Tabelle in Vorabfestlegung Paragraf 4")
    print("=" * 100)
    a_innen = ergebnis["A"][0] and ergebnis["A"][1]
    b_innen = ergebnis["B"][0] and ergebnis["B"][1]
    print("     Weg A: Maximum im Inneren und belegt? %s" % a_innen)
    print("     Weg B: Maximum im Inneren und belegt? %s" % b_innen)
    print()
    if a_innen and b_innen:
        print("     ➤ H1 GESTUETZT - die Form ist nicht monoton.")
        print("       Die Stufen BLEIBEN, die Vorabfestlegung im Werkzeug")
        print("       wird korrigiert.")
    elif not a_innen and not b_innen:
        print("     ➤ H0 GESTUETZT - der Buckel ist ein "
              "Fuenftel-Artefakt.")
        print("       Fuenftel 0+1 werden zusammengefasst, Stufen monoton.")
    else:
        print("     ➤ NICHTS ENTSCHIEDEN - die Wege widersprechen sich.")
        print("       Alles bleibt unveraendert, der Punkt wird als OFFEN")
        print("       gefuehrt. Keine Nachverhandlung der Festlegung.")
    print("=" * 100)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
