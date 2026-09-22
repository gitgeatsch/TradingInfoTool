# -*- coding: utf-8 -*-
"""DIE DREI B3-ZAHLEN - und der Nachweis, dass die Norm sie schon misst.

⚠️⚠️⚠️ DIESES WERKZEUG IST AUS EINEM IRRTUM ENTSTANDEN, und genau das
macht es nuetzlich.

Ich wollte pruefen, ob `umschlag_naeherung` ALS SPERRE traegt - weil
drei Viertel der Spanne im Sprung zum obersten Fuenftel stecken (H5:
Spanne der Fuenftel 0 bis 3 nur 0,35, Sprung zu Fuenftel 4 dagegen
1,07). Das ist die Form einer SPERRE, nicht eines Reglers, und
dieselbe, die F-170 fuer den `volumenanteil` gefunden hat.

Dafuer habe ich die Sperre als BINAERE Kennzahl an `pruefe_auswahl`
gegeben - und bekam ein negatives Ergebnis, wo ein positives stehen
musste.

## ⚠️⚠️ DER IRRTUM: die Norm misst die Sperre SCHON

    messe_regel_wirksamkeit.wirkung(je_tag, oben_sperren=True)
    „Je Kalendertag: Median MIT Regel minus Median OHNE."

`messnorm.pruefe` ruft das mit der Vorgabe `oben_sperren=True`. JEDE
Messung im Haus ist damit bereits eine REGELmessung nach R-R8/B3 - und
keine Merkmalsmessung. Meine binaere Zusatzgroesse hat die Sperre auf
eine bereits gesperrte Groesse angewandt: doppelt, und deshalb mit
umgekehrtem Vorzeichen.

## ✔ Was das Werkzeug jetzt tut

Es rechnet die drei B3-Zahlen EIGENHAENDIG - *wie viele Faelle · waren
die schlechter · was bleibt netto* - und haelt sie gegen die
Hauptmessung. Stimmen sie ueberein, ist belegt, dass die Norm misst,
was sie zu messen behauptet.

    umschlag_naeherung H5   eigene Rechnung  +0,0172
                            Hauptmessung     +0,0172  ✔ identisch

⚠️ Eine Kontrolle, die man nie gegen die Sache haelt, belegt nichts -
das ist die Lehre aus 2.449 („der Schutz stand da und griff nie").

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
import messe_kandidaten_als_regel as K                      # noqa: E402
import messe_regel_wirksamkeit as W                         # noqa: E402
import phase4_c_kalibrierung_freefloat as KF                # noqa: E402
import phase4_c_naeherung_konstante_menge as NK             # noqa: E402


def _arg(a, f, v):
    return a[a.index(f) + 1] if f in a else v


def drei_zahlen(je_tag: dict, anteil: float = 0.20) -> tuple:
    """B3 eigenhaendig: wie viele · waren die schlechter · was netto.

    ⚠️ TAGESKLAMMER - der Vergleich laeuft INNERHALB eines
    Kalendertags, sonst mischt er Marktphasen (Methodik 2.86).
    """
    ges, rest, vor, nach, quote = [], [], [], [], []
    for z in je_tag.values():
        n = len(z)
        if n < 12:
            continue
        w = np.array([x["kennzahl"] for x in z])
        y = np.array([x["in_r"] for x in z])
        r = np.argsort(np.argsort(w)) / max(n - 1, 1)
        m = r >= (1.0 - anteil)
        if m.sum() < 2 or (~m).sum() < 2:
            continue
        ges.append(float(np.median(y[m])))
        rest.append(float(np.median(y[~m])))
        vor.append(float(np.median(y)))
        nach.append(float(np.median(y[~m])))
        quote.append(float(m.sum()) / n)
    if not vor:
        return None
    return (st.mean(quote), st.mean(ges), st.mean(rest),
            st.mean(nach) - st.mean(vor), len(vor))


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    horizonte = tuple(int(x) for x in
                      _arg(args, "--horizonte", "3,5,20").split(","))
    t0 = time.time()
    print("=" * 104)
    print("DIE DREI B3-ZAHLEN - eigene Rechnung gegen die Norm")
    print("=" * 104)

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
    echt = MB.reihe("data/onchain_historie.db", "splycur")

    print()
    print("  %-22s %3s %9s %11s %11s %11s %11s %6s"
          % ("Groesse", "H", "gesperrt", "deren Med", "Rest Med",
             "NETTO eig.", "NETTO Norm", "gleich"))
    print("  " + "-" * 96)
    for name, quelle in (("umschlag_naeherung", naeh),
                         ("umschlag_gesamt (Ktr)", echt)):
        for H in horizonte:
            KF._SPEICHER.clear()
            je = KF.beschneiden(K.baue(reihen, "turnover", quelle,
                                       horizont=H), None, NK.AB)
            e = drei_zahlen(je)
            if not e:
                print("  %-22s %3d  -" % (name, H))
                continue
            q, gm, rm, netto, _t = e
            # ⚠️ DIESELBE Funktion, die `messnorm.pruefe` benutzt -
            # keine Nachbildung. Ihr Mittelwert ueber die Tage ist die
            # Wirkung, die in jeder Messung dieses Hauses steht.
            d, _a, _g, _u = W.wirkung(je, True)
            norm = st.mean(d.values()) if d else float("nan")
            gleich = abs(netto - norm) < 0.0005
            print("  %-22s %3d %8.1f %% %+11.4f %+11.4f %+11.4f %+11.4f %6s"
                  % (name, H, 100 * q, gm, rm, netto, norm,
                     "✔" if gleich else "⚠ NEIN"))
    print("  " + "-" * 96)
    print()
    print("  ⚠️⚠️ STIMMEN DIE BEIDEN NETTO-SPALTEN UEBEREIN, ist belegt:")
    print("     die Norm misst die SPERRE, nicht das Merkmal - und jede")
    print("     Messung dieses Hauses erfuellt R-R8/B3 bereits.")
    print("     Laufen sie auseinander, misst eine von beiden etwas")
    print("     anderes, als ihr Name sagt.")
    print()
    print("  Dauer %.1f Minuten" % ((time.time() - t0) / 60))
    return 0


if __name__ == "__main__":
    sys.exit(main())
