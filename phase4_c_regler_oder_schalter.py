# -*- coding: utf-8 -*-
"""TRAEGT DIE ORDNUNG ODER NUR DAS OBERSTE FUENFTEL? - Regler gegen Schalter.

⚠️⚠️⚠️ WARUM DIESE MESSUNG NOETIG IST (21.09.2026). Nutzerauftrag:
*„dann Reglerwirkung messen"* - und beim Nachsehen stellte sich heraus,
dass es die im ganzen Haus noch nie gab.

## Die Lage, die dazu gefuehrt hat

Jeder Beitrag ist mit einer SPERRwirkung registriert:

    funding   „kein Einstieg ab Rangplatz 80 %"   +0,0246 R
    turnover  dieselbe Form                        +0,0616 R

`messnorm.pruefe` ruft `messe_regel_wirksamkeit.wirkung(je_tag,
oben_sperren=True)` - *„Je Kalendertag: Median MIT Regel minus Median
OHNE"*. Die Konstante `GRENZE = 0.80` sperrt das oberste Fuenftel.

⚠️ ANGEWANDT wird aber ein REGLER: die Stufentabelle verteilt Punkte
ueber ALLE fuenf Fuenftel auf die Quote. Die Wirkungszahl belegt, DASS
die Groesse traegt; die Tabelle sagt, WIE die Punkte fallen. Ob die
ORDNUNG der Fuenftel 0 bis 3 ueberhaupt Information traegt, ist damit
NICHT belegt - bei keinem Beitrag.

## ⚠️⚠️ VORABFESTLEGUNG - vor dem ersten Lauf

Gemessen wird dieselbe Wirkung bei WACHSENDER Sperrbreite (20, 40, 60,
80 Prozent). Wer nur im obersten Fuenftel schlecht ist, bringt ab 20
Prozent nichts mehr dazu; wer eine echte Ordnung hat, traegt weiter.

| Verlauf der Wirkung | Deutung |
|---|---|
| steigt ueber 20 % hinaus weiter | ✔ die ORDNUNG traegt - ein Regler ist gerechtfertigt |
| flacht ab 20 % ab oder faellt | ⚠ nur das oberste Fuenftel traegt - SCHALTER |
| faellt schon vor 20 % | ✖ die Groesse ordnet gar nicht |

⚠️ Als KONTROLLE laufen `funding` und `umschlag_gesamt` mit - beide sind
LIVE und als Regler angewandt. Zeigen sie dasselbe Bild wie die
Naeherung, ist die Schalterform kein Einwand gegen sie, sondern eine
Eigenschaft des ganzen Systems.

⚠️ `messe_regel_wirksamkeit.GRENZE` ist eine MODULKONSTANTE. Sie wird
hier gesetzt und in `finally` zurueckgestellt - ein liegengebliebener
Wert wuerde jede spaetere Messung im selben Prozess verfaelschen.

⚠️ NUR LESEND.
"""
import os
import statistics as st
import sys
import time

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
os.chdir("D:/CLAUDE_Projects/SoftwareProjekte/TradingInfoTool")
sys.path.insert(0, "D:/CLAUDE_Projects/SoftwareProjekte/TradingInfoTool")

import numpy as np                                          # noqa: E402

import messe_bewertungskennzahl as MB                       # noqa: E402
import messe_eigenschaft_beitrag as B                       # noqa: E402
import messe_funding_niveau as F                            # noqa: E402
import messe_kandidaten_als_regel as K                      # noqa: E402
import messe_regel_wirksamkeit as W                         # noqa: E402
import phase4_c_kalibrierung_freefloat as KF                # noqa: E402
import phase4_c_naeherung_konstante_menge as NK             # noqa: E402

BREITEN = (0.20, 0.40, 0.60, 0.80)


def _arg(a, f, v):
    return a[a.index(f) + 1] if f in a else v


def wirkung_bei(je_tag: dict, breite: float) -> float:
    """Die Sperrwirkung bei GEGEBENER Breite - dieselbe Funktion wie
    die Norm, nur mit anderer Grenze."""
    alt = W.GRENZE
    try:
        W.GRENZE = 1.0 - breite
        d, _a, _g, _u = W.wirkung(je_tag, True)
        return st.mean(d.values()) if d else float("nan")
    finally:
        W.GRENZE = alt


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    H = int(_arg(args, "--horizont", "5"))
    t0 = time.time()

    print("=" * 100)
    print("REGLER ODER SCHALTER? - Wirkung bei wachsender Sperrbreite "
          "(H%d)" % H)
    print("=" * 100)
    print("  Vorab festgelegt: steigt die Wirkung ueber 20 %% hinaus")
    print("  weiter, traegt die ORDNUNG (Regler). Flacht sie ab, traegt")
    print("  nur das oberste Fuenftel (Schalter).")
    print()

    reihen = B.lade()
    heute, _r = NK.mengen_heute()
    umst = NK.umstellungen(reihen)
    naeh = {}
    for s, m in heute.items():
        if s in umst:
            continue
        z = reihen.get(s)
        if z:
            naeh[s] = {str(x[0])[:10]: m for x in z}

    quellen = [("umschlag_naeherung", "turnover", naeh),
               ("umschlag_gesamt (live)", "turnover",
                MB.reihe("data/onchain_historie.db", "splycur"))]
    try:
        quellen.append(("funding (live)", "funding", F.lade_funding()))
    except Exception as exc:                                # noqa: BLE001
        print("  ⚠️ funding nicht ladbar: %s" % str(exc)[:60])

    print("  %-26s %s" % ("Groesse", "  ".join("%5.0f %%" % (100 * b)
                                               for b in BREITEN)))
    print("  " + "-" * 72)
    ergebnis = {}
    for name, art, quelle in quellen:
        KF._SPEICHER.clear()
        try:
            je = KF.beschneiden(K.baue(reihen, art, quelle, horizont=H),
                                None, NK.AB)
        except Exception as exc:                            # noqa: BLE001
            print("  %-26s -> %s" % (name, str(exc)[:44]))
            continue
        if not je:
            print("  %-26s -> leere Welt" % name)
            continue
        werte = [wirkung_bei(je, b) for b in BREITEN]
        ergebnis[name] = werte
        print("  %-26s %s"
              % (name, "  ".join("%+7.4f" % w for w in werte)))
    print("  " + "-" * 72)
    print()

    print("  DER VERLAUF - jede Breite gegen die vorige")
    print("  %-26s %s" % ("Groesse", "  ".join(
        "%5.0f->%2.0f" % (100 * BREITEN[i], 100 * BREITEN[i + 1])
        for i in range(len(BREITEN) - 1))))
    print("  " + "-" * 72)
    for name, w in ergebnis.items():
        d = [w[i + 1] - w[i] for i in range(len(w) - 1)]
        steigt = sum(1 for x in d if x > 0)
        print("  %-26s %s   %s"
              % (name, "  ".join("%+8.4f" % x for x in d),
                 "✔ steigt weiter (Regler)" if steigt == len(d) else
                 "⚠️ flacht ab (Schalter)" if steigt == 0 else
                 "gemischt (%d von %d steigend)" % (steigt, len(d))))
    print("  " + "-" * 72)
    print()
    print("  ⚠️⚠️ ZEIGEN ALLE DREI DASSELBE BILD, ist die Schalterform")
    print("     kein Einwand gegen die Naeherung, sondern eine")
    print("     Eigenschaft des ganzen Systems - dann waere die Frage")
    print("     nicht *ob die Naeherung taugt*, sondern *ob irgendein")
    print("     Beitrag als Regler gerechtfertigt ist*.")
    print()
    print("  ⚠️ Kein Band - dies ist eine FORMfrage, keine Wirkungsfrage.")
    print("     Ob die Wirkung bei 20 %% traegt, steht in 2.515.")
    print()
    print("  Dauer %.1f Minuten" % ((time.time() - t0) / 60))
    return 0


if __name__ == "__main__":
    sys.exit(main())
