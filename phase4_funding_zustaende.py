# -*- coding: utf-8 -*-
"""FUNDING ALS DREI OEKONOMISCHE ZUSTAENDE - die Messung zu Vorabfestlegung 3.

⚠️⚠️⚠️ DIE FESTLEGUNG STEHT IN
`Basisinfos/Vorabfestlegung_Funding_Form_23_09.md`, Abschnitt
„VORABFESTLEGUNG 3", und wurde VOR dieser Messung committet. Sie wird
hier nicht nachverhandelt.

## Warum drei Zustaende statt fuenf Rangfuenftel

`funding` hat heute KEINE festgelegte Anwendung (2.552): im Betrieb ein
Regler ueber Rangfuenftel, in der Messung ein Schalter, in der Mail ein
Text. Die vier Fundstellen des 23.09. - nicht-monotoner Buckel, verletzte
Monotonie-Vorabfestlegung, 32,5 % Bindungen, Messung gegen Betrieb - sind
Symptome davon.

Die Grenzen kommen deshalb aus der SACHE, nicht aus der Verteilung:

    negativ   Funding < 0              Shorts zahlen Longs - Kapitulation
    normal    0 <= Funding <= Standard kein Ungleichgewicht
    hoch      Funding > Standardrate   Longs zahlen Praemie - Crowding

⚠️ Damit entfallen Bindungsproblem, Monotoniefrage und Tagesbesetzung auf
einen Schlag - alle drei waren Folgen der RANGbildung.

## Die Hypothese, die scheitern koennen muss

    U-FORM: normal am besten, beide Raender schlechter.

## Die Entscheidungsregel (Vorabfestlegung 3, woertlich)

    normal bestes UND beide Raender darunter, Abstaende ueber der
      Trennschaerfe          -> U-Form belegt, Umstellung, R-R9 greift
    hoch am schlechtesten, negativ aber nicht -> Lehrmeinung nur halb,
      einseitiger Schalter oben
    kein Abstand ueber der Trennschaerfe -> nichts entschieden
    hoch ist das beste       -> Hypothese widerlegt

⚠️ NUR LESEND, gegen die Messbasis am Desktop.

    python phase4_funding_zustaende.py
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
STANDARD = 0.0003          # haeufigster Wert, 35,4 % aller Punkte
NAMEN = ("negativ", "normal", "hoch")
ZIEHUNGEN = 300


def lade():
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


def zustand(w):
    """Die drei Zustaende - Grenzen aus der Sache, nicht aus der Verteilung.

    ⚠️ Die Toleranz 1e-9 faengt Fliesskomma: der Massepunkt liegt EXAKT
    auf der Standardrate, und ohne sie fiele er je nach Rundung mal in
    `normal`, mal in `hoch`.
    """
    return np.where(w < -1e-9, 0,
                    np.where(w > STANDARD + 1e-9, 2, 1))


def werte(je_tag, tage):
    """Median je Zustand und Tag, dann ueber die Tage gemittelt.

    ⚠️ Die Kalendertag-Klammer ist Pflicht (R-R8 B2): ohne sie vermischt
    man Marktlagen und misst die Zeitreihe statt des Querschnitts.
    """
    sammel = {k: [] for k in range(3)}
    zahl = {k: 0 for k in range(3)}
    for t in tage:
        z = je_tag[t]
        w = np.array([x[0] for x in z])
        y = np.array([x[1] for x in z])
        g = zustand(w)
        for k in range(3):
            m = g == k
            if m.sum() >= 2:
                sammel[k].append(float(np.median(y[m])))
                zahl[k] += int(m.sum())
    return ([st.mean(sammel[k]) if sammel[k] else float("nan")
             for k in range(3)], zahl,
            {k: len(sammel[k]) for k in range(3)})


def band(je_tag, tage, a, b):
    """Blockbootstrap auf die Differenz a minus b - GEPAART je Tag."""
    blk = messnorm._block(HOR)
    paare = []
    for t in tage:
        z = je_tag[t]
        w = np.array([x[0] for x in z])
        y = np.array([x[1] for x in z])
        g = zustand(w)
        ma, mb = g == a, g == b
        if ma.sum() >= 2 and mb.sum() >= 2:
            paare.append(float(np.median(y[ma])) - float(np.median(y[mb])))
    if len(paare) < blk * 2:
        return None
    d = np.array(paare)
    rng = np.random.default_rng(messnorm.SAAT)
    starts = np.arange(max(1, len(d) - blk + 1))
    n = int(np.ceil(len(d) / blk))
    z = [np.concatenate([d[s:s + blk] for s in rng.choice(starts, n)]
                        )[:len(d)].mean() for _ in range(ZIEHUNGEN)]
    return d.mean(), float(np.percentile(z, 5)), \
        float(np.percentile(z, 95)), len(d)


def main() -> int:
    print("=" * 100)
    print("FUNDING ALS DREI OEKONOMISCHE ZUSTAENDE")
    print("=" * 100)
    print("  Vorabfestlegung 3 · Standardrate %.4f · H%d"
          % (STANDARD, HOR))
    print("  " + messnorm.standardzeile().replace("\n", "\n  "))
    print("\n  Anker laden ...")
    je_tag = lade()
    alle = sorted(je_tag)
    m = len(alle) // 2
    print("  %d Kalendertage, %s bis %s" % (len(alle), alle[0], alle[-1]))

    w, zahl, tage_je = werte(je_tag, alle)
    print("\n  GESAMT")
    print("     %-10s %12s %12s %10s" % ("Zustand", "Wirkung", "Punkte",
                                         "Tage"))
    for k in range(3):
        print("     %-10s %+12.4f %12d %10d"
              % (NAMEN[k], w[k], zahl[k], tage_je[k]))

    gueltig = [k for k in range(3) if np.isfinite(w[k])]
    best = max(gueltig, key=lambda k: w[k])
    print("     ➤ bester Zustand (UNGEPAART): %s" % NAMEN[best])
    # ⚠️⚠️ DIESE REIHUNG IST NICHT ENTSCHEIDUNGSFAEHIG, und das gehoert
    # hierhin statt in eine Fussnote: die drei Zustaende kommen an
    # VERSCHIEDEN VIELEN Tagen vor (unten in der Spalte `Tage`). `hoch`
    # tritt nur an rund der Haelfte auf - und wenn das die guten Tage
    # sind, sieht er besser aus, ohne besser zu sein. Entschieden wird
    # ausschliesslich nach den GEPAARTEN Abstaenden weiter unten.
    print("     ⚠️ nicht entscheidungsfaehig - verschiedene "
          "Tagesmengen (siehe Spalte Tage).")
    print("        Entschieden wird nach den GEPAARTEN Abstaenden unten.")

    print("\n  BEIDE HISTORIENHAELFTEN (R-R8 B6)")
    for nm, tg in (("1. Haelfte", alle[:m]), ("2. Haelfte", alle[m:])):
        wh, _z, _t = werte(je_tag, tg)
        g = [k for k in range(3) if np.isfinite(wh[k])]
        bh = max(g, key=lambda k: wh[k])
        print("     %s  %s  ➤ bester: %s"
              % (nm, "  ".join("%s %+.4f" % (NAMEN[k][:7], wh[k])
                               for k in range(3)), NAMEN[bh]))

    print("\n  DIE ABSTAENDE (gepaart je Tag, Blocklaenge %d)"
          % messnorm._block(HOR))
    ab = {}
    for a, b in ((1, 0), (1, 2), (0, 2)):
        r = band(je_tag, alle, a, b)
        if r is None:
            print("     %-22s zu wenige gepaarte Tage" % (
                "%s minus %s" % (NAMEN[a], NAMEN[b])))
            continue
        d, u, o, n = r
        ab[(a, b)] = (d, u, o)
        print("     %-22s %+.4f R  [%+.4f .. %+.4f]  %d Tage  %s"
              % ("%s minus %s" % (NAMEN[a], NAMEN[b]), d, u, o, n,
                 "✔ Null aus" if u > 0 or o < 0 else "⚠ Null ein"))

    # ---- B6 AUF DEM ENTSCHEIDENDEN MASS ----------------------------
    #
    # ⚠️⚠️ Die Hälften oben stehen UNGEPAART da und taugen damit so wenig
    # wie die Gesamtreihung. R-R8 B6 verlangt beide Hälften für den
    # BEFUND — und der Befund ist der gepaarte Abstand. Also hier noch
    # einmal, gepaart je Hälfte.
    print("\n  B6 - DIE GEPAARTEN ABSTAENDE JE HISTORIENHAELFTE")
    b6 = {}
    for nm, tg in (("1. Haelfte", alle[:m]), ("2. Haelfte", alle[m:])):
        zeile = []
        for a, b in ((1, 0), (1, 2)):
            r = band(je_tag, tg, a, b)
            if r is None:
                zeile.append("%s-%s zu duenn" % (NAMEN[a][:4], NAMEN[b][:4]))
                b6[(nm, a, b)] = False
                continue
            d, u, o, n = r
            belegt = u > 0 or o < 0
            b6[(nm, a, b)] = belegt
            zeile.append("%s minus %s %+.4f [%+.4f .. %+.4f] %s"
                         % (NAMEN[a], NAMEN[b], d, u, o,
                            "✔" if belegt else "⚠"))
        print("     %s  %s" % (nm, "  |  ".join(zeile)))

    # ⚠️⚠️⚠️ B6 IST EINE AUFNAHMEBEDINGUNG, KEINE ZUSATZANGABE (R-R8).
    # Der Wortlaut dort: *„Beide Historienhälften — der Befund trägt nur
    # in der ERSTEN Hälfte"* steht in der Spalte der AUSSCHLUSSGRÜNDE.
    # Meine erste Fassung hat die Hälften nur ausgewiesen und die
    # Entscheidung allein auf der Gesamtmenge getroffen - damit hätte ein
    # Befund, der in der jüngeren Hälfte nicht trägt, einen Umbau
    # ausgelöst.
    _b6_hoch = b6.get(("1. Haelfte", 1, 2)) and b6.get(("2. Haelfte", 1, 2))
    print("     ➤ B6 fuer `normal minus hoch`: %s"
          % ("✔ beide Haelften" if _b6_hoch
             else "⛔ NICHT erfuellt - nur eine Haelfte traegt"))

    # ---- DIE ENTSCHEIDUNG ------------------------------------------
    print("\n" + "=" * 100)
    print("  ENTSCHEIDUNG nach Vorabfestlegung 3")
    print("=" * 100)
    # ⚠️⚠️⚠️ ENTSCHIEDEN WIRD AUSSCHLIESSLICH AUF DEN GEPAARTEN
    # ABSTAENDEN. Meine erste Fassung las `best` aus den UNGEPAARTEN
    # Mittelwerten - und die stehen auf verschiedenen Tagesmengen
    # (hoch nur 1.217 von 2.399 Tagen). Sie meldete deshalb "Hypothese
    # widerlegt", waehrend der gepaarte Abstand `normal minus hoch`
    # +0,2331 R betrug und die Null ausschloss. Derselbe Selektions-
    # fehler wie in 2.545 und beim Bindungsvergleich.
    n_besser = ab.get((1, 0), (0, 0, 0))     # normal minus negativ
    h_besser = ab.get((1, 2), (0, 0, 0))     # normal minus hoch
    normal_ueber_negativ = n_besser[1] > 0
    normal_ueber_hoch = h_besser[1] > 0
    hoch_ueber_normal = h_besser[2] < 0
    u_form = normal_ueber_negativ and normal_ueber_hoch
    nur_oben = normal_ueber_hoch and not normal_ueber_negativ
    if hoch_ueber_normal:
        print("     ➤ HYPOTHESE WIDERLEGT - `hoch` ist GEPAART besser")
        print("       als `normal`. Die Lehrmeinung gilt hier NICHT.")
    elif u_form:
        print("     ➤ U-FORM BELEGT - normal ist bestes, beide Raender")
        print("       liegen darunter, beide Abstaende ueber der Null.")
        print("       Umstellung auf drei Zustaende, R-R9 greift.")
    elif nur_oben and not _b6_hoch:
        print("     ⛔ B6 NICHT ERFUELLT - KEIN UMBAU.")
        print("       Auf der Gesamtmenge ist `hoch` belegt schlechter,")
        print("       aber der Abstand traegt nur in der ERSTEN Haelfte.")
        print("       Die zweite ist die juengere - also die fuer heute")
        print("       relevantere. R-R8 B6 fuehrt genau diesen Fall als")
        print("       AUSSCHLUSSGRUND. Die heutige Anwendung bleibt.")
    elif nur_oben:
        print("     ➤ LEHRMEINUNG NUR HALB - `hoch` ist belegt")
        print("       schlechter, `negativ` nicht, und B6 ist erfuellt.")
        print("       Einseitiger Schalter am oberen Ende, unteres Ende")
        print("       ohne Bonus.")
    else:
        print("     ➤ NICHTS ENTSCHIEDEN - kein Abstand uebersteigt")
        print("       die Trennschaerfe. Die heutige Anwendung bleibt,")
        print("       der Punkt bleibt offen.")
    print("=" * 100)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
