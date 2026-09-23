# -*- coding: utf-8 -*-
"""IST DER VERSATZ IN ALLEN MERKMALSLAGEN GLEICH? (Befund 2.560 vertieft)

## Die Vorabfestlegung - vor der Messung geschrieben

`2.560` hat gemessen: die Bewertung sagt rund ZWEI Prozentpunkte mehr
voraus, als die Barriere liefert - in drei verschiedenen Mengen gleich
(-2,0 / -2,2 / -2,1 Pp). Das ist eine Zahl auf der GESAMTmenge.

Offen und hier gefragt:

    Ist der Versatz in allen 25 Merkmalslagen gleich gross - oder
    konzentriert er sich?

⚠️⚠️ WARUM DAS ZAEHLT UND NICHT AKADEMISCH IST: nach 2.558 steuert die
Quote den Hebel nur in einem Fenster von EINEM Prozentpunkt (0,3400 bis
0,3500), und nur 5 der 25 Lagen liegen darin. Ein Versatz von zwei
Punkten ist doppelt so breit wie das ganze Fenster. Entscheidend ist
deshalb NICHT der Durchschnitt, sondern der Versatz GENAU IN DIESEN
FUENF LAGEN.

## Die Entscheidungsregel - vorab

    gleichmaessig   der Versatz streut nicht ueber die Lagen hinaus, die
                    ihre Baender zulassen -> er ist ein NIVEAUfehler, und
                    eine Korrektur waere eine Verschiebung der Basisrate
    konzentriert    einzelne Lagen weichen belegt staerker ab -> dann ist
                    es KEIN Niveaufehler, sondern eine falsche STUFE, und
                    die Korrektur waere eine andere
    ⛔ zu duenn     traegt eine Lage zu wenige Anker fuer ein Band, wird
                    sie AUSGEWIESEN und NICHT gedeutet

⚠️ MEHRFACHTEST: 25 Lagen. Ein Band, das bei 5 Prozent Irrtum 25-mal
gezogen wird, schlaegt rein zufaellig rund einmal an. Die Erwartung wird
deshalb VORHER genannt und im Ergebnis gegengerechnet.

## Nichts nachgebaut

Barrieren-Ausgaenge, Fuenftel, Auswahlmaske und Potential kommen aus
`messe_bewertung_kalibrierung` bzw. `agent.potential` - denselben
Funktionen, mit denen 2.559 und 2.560 gerechnet wurden.

⚠️ NUR LESEND.

    python phase4_versatz_je_lage.py
    python phase4_versatz_je_lage.py --menge 20%
    python phase4_versatz_je_lage.py --quelle frei
    python phase4_versatz_je_lage.py --luecke   (der BETRIEBSFALL)
"""
from __future__ import annotations

import sys
from collections import defaultdict

import numpy as np

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import messe_bewertung_kalibrierung as KAL                   # noqa: E402
import messe_eigenschaft_beitrag as B                        # noqa: E402
import messe_funding_niveau as F                             # noqa: E402
import messe_kandidaten_als_regel as K                       # noqa: E402
import messe_zielregel as ZR                                 # noqa: E402
import messnorm                                              # noqa: E402
import phase3_reproduktion as R3                             # noqa: E402
from agent import potential as PT                            # noqa: E402

CRV = 2.0
BLOCK = 90              # wie in messe_bewertung_kalibrierung
ZIEHUNGEN = 500
MIN_ANKER = 300         # darunter wird nur ausgewiesen, nicht gedeutet


def sammle(menge: str, quelle: str, nur_luecke: bool = False) -> tuple:
    """{(fu, tu): {tag: [0/1, ...]}} auf der gewaehlten Menge.

    `nur_luecke=True` nimmt NUR die Anker mit fehlendem turnover -
    den Betriebsfall, in dem die Hebelsignale entstehen (2.534).
    """
    reihen = B.lade()
    erlaubt = KAL.erlaubte_anker(reihen, menge)
    tage_je_sym = {s: [z[0] for z in roh] for s, roh in reihen.items()}
    zeilen = ZR.ergebnisse(reihen)
    nenner = R3._zusatz("turnover", quelle)
    fu5 = KAL._fuenftel_je_tag(K.baue(reihen, "funding", F.lade_funding(),
                                      horizont=20))
    tu5 = KAL._fuenftel_je_tag(K.baue(reihen, "turnover", nenner, horizont=20))
    aus: dict = defaultdict(lambda: defaultdict(list))
    for z in zeilen:
        sym, i = z["sym"], z["i"]
        tage = tage_je_sym.get(sym)
        if not tage or i >= len(tage):
            continue
        tag = tage[i]
        if erlaubt is not None and (tag, sym) not in erlaubt:
            continue
        wert = z.get(KAL.VARIANTE)
        if wert is None:
            continue
        if abs(wert - CRV) < 1e-9:
            treffer = 1
        elif abs(wert + 1.0) < 1e-9:
            treffer = 0
        else:
            continue
        f, t = fu5.get(tag, {}).get(sym), tu5.get(tag, {}).get(sym)
        if f is None:
            continue
        # ⚠️⚠️ ZWEI DATENLAGEN, UND DIE ZWEITE IST DER BETRIEBSFALL.
        #
        # `nur_luecke` nimmt die Anker, bei denen turnover FEHLT. Die
        # Schwelle liegt dort bei 0,022 statt 0,060 (Schwelle je Datenlage,
        # 31.08.) - und 2.534 haelt fest, dass ALLE 21 Hebelsignale seit
        # dem 12.09. genau auf diesem Lueckenrabatt entstanden sind.
        #
        # ⚠️ Die erste Fassung dieses Werkzeugs uebersprang sie stumm
        # (`if t is None: continue`) und mass damit an der Stelle vorbei,
        # an der der Hebel tatsaechlich entsteht.
        if nur_luecke:
            if t is not None:
                continue
            aus[(f, None)][tag].append(treffer)
            continue
        if t is None:
            continue
        aus[(f, t)][tag].append(treffer)
    return {k: dict(v) for k, v in aus.items()}, erlaubt


def band(je_tag: dict, rng) -> tuple:
    """Blockbootstrap ueber Kalendertage auf die Trefferquote."""
    tage = sorted(je_tag)
    if len(tage) < BLOCK + 10:
        return (float("nan"), float("nan"))
    starts = np.arange(len(tage) - BLOCK + 1)
    anzahl = int(np.ceil(len(tage) / BLOCK))
    werte = []
    for _ in range(ZIEHUNGEN):
        idx = rng.choice(starts, anzahl)
        tg = [tage[j] for s in idx
              for j in range(s, min(s + BLOCK, len(tage)))][:len(tage)]
        tr = sum(sum(je_tag[t]) for t in tg)
        n = sum(len(je_tag[t]) for t in tg)
        if n:
            werte.append(tr / n)
    if not werte:
        return (float("nan"), float("nan"))
    return (float(np.percentile(werte, 5)), float(np.percentile(werte, 95)))


def main() -> int:
    menge = KAL._argv_wert("--menge", "20%")
    quelle = KAL._argv_wert("--quelle", "gesamt")
    luecke = "--luecke" in sys.argv
    print("=" * 108)
    print("DER VERSATZ JE MERKMALSLAGE  (Vertiefung zu Befund 2.560)")
    print("=" * 108)
    print("  MENGE %s · QUELLE %s · CRV %.1f · Block %d"
          % (menge, quelle, CRV, BLOCK))
    print("  Vorhersage je Lage: agent.potential.rechne() mit den LIVE-Stufen")
    _n_lagen = 5 if luecke else 25
    print("  ⚠️ %d Lagen = Mehrfachtest. Bei 5 %% Irrtum je Band sind rund"
          % _n_lagen)
    print("     %.1f Fehlalarme zu ERWARTEN - das steht hier VOR dem Ergebnis."
          % (0.05 * _n_lagen))

    print("\n  Laden ...")
    lagen, erlaubt = sammle(menge, quelle, luecke)
    if luecke:
        print("  ⚠️ NUR die LUECKE (turnover fehlt) - Schwelle 0,022 "
              "statt 0,060")
    if erlaubt is not None:
        print("  selektierte Menge: %d (tag, sym)-Paare" % len(erlaubt))
    rng = np.random.default_rng(messnorm.SAAT)

    print("\n" + "-" * 108)
    print("  %-8s %8s %10s %12s %11s %-22s %s"
          % ("Lage", "Anker", "gemessen", "vorhergesagt", "Versatz",
             "Band gemessen", "Hebel-Lage"))
    print("-" * 108)
    zeilen, versaetze, im_fenster = [], [], []
    r_min, r_max = 0.005, 0.0125
    for f in range(5):
        for t in ([None] if luecke else range(5)):
            je_tag = lagen.get((f, t))
            if not je_tag:
                continue
            n = sum(len(v) for v in je_tag.values())
            q = sum(sum(v) for v in je_tag.values()) / max(n, 1)
            _m = {"funding_fuenftel": f}
            if t is not None:
                _m["turnover_fuenftel"] = t
            vor = PT.rechne(crv=CRV, stop_relativ=0.08, klasse="krypto",
                            merkmale=_m).quote
            halb = ((vor * (1 + CRV) - 1) / CRV) / 2
            lage = ("kein Hebel" if halb <= 0 else
                    "unter r_min" if halb < r_min else
                    "an r_max" if halb > r_max else "✔ STEUERT")
            u, o = band(je_tag, rng) if n >= MIN_ANKER else (float("nan"),) * 2
            v = q - vor
            deut = n >= MIN_ANKER and np.isfinite(u)
            if deut:
                versaetze.append(v)
                if lage == "✔ STEUERT":
                    im_fenster.append(v)
            print("  fu%d/tu%-4s %8d %9.1f %% %11.1f %% %+10.1f Pp "
                  "%-22s %s%s"
                  % (f, "-" if t is None else t, n, 100 * q, 100 * vor, 100 * v,
                     ("[%.1f .. %.1f] %%" % (100 * u, 100 * o)) if deut
                     else "zu wenige Anker",
                     lage, "" if deut else "  ⚠ NICHT GEDEUTET"))
            zeilen.append((f, t, n, q, vor, v, u, o, lage, deut))

    # ---- DIE AUSWERTUNG --------------------------------------------
    print("\n" + "=" * 108)
    print("  AUSWERTUNG")
    print("=" * 108)
    if not versaetze:
        print("  ⛔ keine Lage mit genug Ankern - nichts zu deuten.")
        return 0
    va = np.array(versaetze)
    print("  gedeutete Lagen: %d von %d" % (len(va), len(zeilen)))
    print("  Versatz: Median %+.1f Pp · Spanne %+.1f bis %+.1f Pp"
          % (100 * np.median(va), 100 * va.min(), 100 * va.max()))
    print("  2.560 mass auf der Gesamtmenge: -2,0 bis -2,2 Pp")

    # ⚠️ Wie viele Lagen schliessen ihre eigene Vorhersage AUS?
    raus = [(f, t, v) for f, t, _n, _q, vor, v, u, o, _l, d in zeilen
            if d and not (u <= vor <= o)]
    print("\n  Lagen, deren Band die eigene Vorhersage AUSSCHLIESST: %d von %d"
          % (len(raus), len(va)))
    print("  ⚠️ ERWARTET waren rund %.1f rein zufaellig (%d Lagen x 5 %%)."
          % (0.05 * len(va), len(va)))
    for f, t, v in raus:
        print("     fu%d/tu%-4s Versatz %+.1f Pp"
              % (f, "-" if t is None else t, 100 * v))

    if im_fenster:
        iw = np.array(im_fenster)
        print("\n  ➤➤ DIE FUENF LAGEN, IN DENEN DIE QUOTE DEN HEBEL STEUERT:")
        print("     %d gedeutet · Versatz Median %+.1f Pp · Spanne %+.1f bis %+.1f"
              % (len(iw), 100 * np.median(iw), 100 * iw.min(), 100 * iw.max()))
        print("     ⚠️ Das steuernde Fenster ist EINEN Prozentpunkt breit")
        print("        (Quote 0,3400 bis 0,3500, Befund 2.558).")

        # ⚠️⚠️⚠️ DIE ZAHL, DIE FUER DEN HEBEL DIREKT ENTSCHEIDET.
        #
        # Kelly wird null bei q = 1/(1+CRV). Liegt die GEMESSENE Quote
        # einer steuernden Lage BELEGT darunter (ihr Band schliesst die
        # Nullstelle aus), dann duerfte dort gar kein Hebel entstehen -
        # die Rechnung erzeugt ihn nur, weil sie mit der VORHERGESAGTEN
        # Quote arbeitet.
        #
        # ⚠️ Ein Band, das die Nullstelle EINSCHLIESST, sagt NICHTS - weder
        # dafuer noch dagegen. Diese Lagen werden getrennt gezaehlt.
        null = 1.0 / (1.0 + CRV)
        print("\n     Kelly-Nullstelle: %.1f %%" % (100 * null))
        drunter = gleich = drueber = 0
        for f, t, n, q, vor, v, u, o, lage, d in zeilen:
            if lage != "✔ STEUERT" or not d:
                continue
            if o < null:
                urteil, drunter = "⛔ BELEGT UNTER der Nullstelle", drunter + 1
            elif u > null:
                urteil, drueber = "✔ belegt darueber", drueber + 1
            else:
                urteil, gleich = "⚠ Band enthaelt sie - keine Aussage", gleich + 1
            print("       fu%d/tu%-4s gemessen %.1f %%  [%.1f .. %.1f]  %s"
                  % (f, "-" if t is None else t, 100 * q, 100 * u,
                     100 * o, urteil))
        print("     ➤ %d belegt DARUNTER · %d ohne Aussage · %d belegt darueber"
              % (drunter, gleich, drueber))
        if drunter:
            print("     ⚠️⚠️ IN %d DER STEUERNDEN LAGEN LIEGT DIE TATSAECHLICHE"
                  % drunter)
            print("        QUOTE BELEGT UNTER DER KELLY-NULLSTELLE. Dort")
            print("        entsteht heute ein Hebel, der rechnerisch nicht")
            print("        gerechtfertigt ist.")
    else:
        print("\n  ⚠️ KEINE der steuernden Lagen hat genug Anker - die Frage,")
        print("     die fuer den Hebel zaehlt, bleibt damit OFFEN.")

    # ---- DIE BETRIEBSSICHT -----------------------------------------
    # ⚠️⚠️ WIE VIELE SIGNALE BETRIFFT DAS REAL? Die bisherigen Zahlen sind
    # je LAGE. Im Betrieb entsteht ein Signal aber nur ueber der SCHWELLE -
    # und die Lagen sind ungleich besetzt. Erst beides zusammen sagt, wie
    # gross der Schaden ist.
    #
    # ⚠️ `schwelle` ist eine Property JE DATENLAGE (31.08.). Sie wird
    # deshalb je Lage aus `potential.rechne()` gelesen, nicht als Konstante
    # gesetzt - eine feste Zahl waere wieder eine, die still veraltet.
    print("\n" + "=" * 108)
    print("  BETRIEBSSICHT - wie viele ANKER liegen ueber der Schwelle?")
    print("=" * 108)
    ges = sum(n for _f, _t, n, *_r in zeilen)
    ueber = ueber_steuernd = ueber_belegt_drunter = 0
    null = 1.0 / (1.0 + CRV)
    print("  %-8s %8s %10s %10s %11s %s"
          % ("Lage", "Anker", "Potential", "Schwelle", "Anteil", "Lage/Urteil"))
    for f, t, n, q, vor, v, u, o, lage, d in zeilen:
        _mm = {"funding_fuenftel": f}
        if t is not None:
            _mm["turnover_fuenftel"] = t
        p = PT.rechne(crv=CRV, stop_relativ=0.08, klasse="krypto",
                      merkmale=_mm)
        durch = p.wert_r >= p.schwelle
        if not durch:
            continue
        ueber += n
        urteil = lage
        if lage == "✔ STEUERT":
            ueber_steuernd += n
            if d and o < null:
                ueber_belegt_drunter += n
                urteil += " · ⛔ Quote BELEGT unter Kelly"
        print("  fu%d/tu%-4s %8d %+9.4f R %8.3f R %9.1f %% %s"
              % (f, "-" if t is None else t, n, p.wert_r, p.schwelle,
                 100.0 * n / max(ges, 1), urteil))
    print("\n  ueber der Schwelle:            %7d von %d Ankern = %5.1f %%"
          % (ueber, ges, 100.0 * ueber / max(ges, 1)))
    if ueber:
        print("  davon in STEUERNDEN Lagen:     %7d = %5.1f %% der Durchlaesse"
              % (ueber_steuernd, 100.0 * ueber_steuernd / ueber))
        print("  davon Quote BELEGT unter Kelly:%7d = %5.1f %% der Durchlaesse"
              % (ueber_belegt_drunter,
                 100.0 * ueber_belegt_drunter / ueber))
    print("\n  ⚠️ Das sind ANKER, keine Signale: der Trichter hat vor der")
    print("     Bewertung elf weitere Stufen (F-212). Die Zahl ist eine")
    print("     OBERGRENZE fuer den betroffenen Anteil, kein Signalzaehler.")

    print("\n" + "-" * 108)
    # ⚠️⚠️ DIE GRENZE HAENGT AN DER ERWARTUNG, NICHT AN EINER FESTEN ZAHL.
    #
    # Die erste Fassung schrieb `len(raus) <= 2` - gedacht fuer 25 Lagen
    # (Erwartung 1,25). Im Lueckenmodus sind es nur FUENF Lagen, Erwartung
    # 0,25 - dort sind zwei Ausreisser sehr viel, und die feste Schwelle
    # meldete faelschlich "gleichmaessig". Genau die Falle einer Zahl, die
    # still falsch wird, sobald sich die Menge aendert.
    #
    # Gerechnet wird jetzt die Poisson-Wahrscheinlichkeit, MINDESTENS so
    # viele Ausreisser rein zufaellig zu sehen.
    import math
    lam = 0.05 * len(va)
    p_zufall = 1.0 - sum(math.exp(-lam) * lam ** i / math.factorial(i)
                         for i in range(len(raus)))
    print("  Zufallswahrscheinlichkeit fuer >= %d Ausreisser bei Erwartung "
          "%.2f: %.4f" % (len(raus), lam, p_zufall))
    if p_zufall >= 0.05:
        print("  ➤ GLEICHMAESSIG - nicht mehr Ausreisser als der Mehrfachtest")
        print("    erwarten laesst. Der Versatz ist ein NIVEAUfehler; eine")
        print("    Korrektur waere eine Verschiebung der BASISRATE, keine")
        print("    Aenderung einzelner Stufen.")
    else:
        print("  ⚠️ KONZENTRIERT - mehr Ausreisser als erwartet. Dann ist es")
        print("    KEIN reiner Niveaufehler, sondern betrifft einzelne STUFEN.")
    print("=" * 108)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
