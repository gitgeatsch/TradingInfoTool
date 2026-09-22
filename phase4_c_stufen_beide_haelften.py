# -*- coding: utf-8 -*-
"""HAELT DIE MONOTONIE IN BEIDEN HISTORIENHAELFTEN? - R-R8 Bedingung B6.

⚠️⚠️ WARUM DIESE GEGENPRUEFUNG. Am 21.09.2026 ergab
`rechne_turnover_beitrag.py --horizont 3 --umschlag frei` eine MONOTONE
Stufentabelle (+0,59 / +0,23 / +0,23 / -0,18 / -0,86), waehrend
`umschlag_gesamt` auf demselben Horizont Zickzack liefert.

Die Tabellenrechnung ist DETERMINISTISCH - eine Saatprobe greift dort
nicht. Was greift, ist R-R8 Bedingung B6: *„Beide Historienhaelften -
faellt durch, wenn der Befund nur in der ersten Haelfte traegt."*

⚠️ Bei 362 Ankertagen sind die Haelften je rund 180 Tage. Das ist FUER
EIN URTEIL ZU WENIG (20 Bloecke brauchen 300) - deshalb wird hier auch
kein Urteil gefaellt. Geprueft wird allein die FORM: bleibt die Ordnung
der Fuenftel erhalten, oder ist die Monotonie ein Artefakt der einen
Haelfte?

## Vorab festgelegt

| Ergebnis | Deutung |
|---|---|
| beide Haelften monoton, gleiche Richtung | ✔ die Form ist stabil |
| eine Haelfte Zickzack | ⚠️ die Monotonie ist nicht belastbar |
| gegenlaeufige Richtungen | ✖ die Form ist ein Artefakt |

⚠️ Zusaetzlich als KONTROLLE: dieselbe Zerlegung fuer
`umschlag_gesamt`. Ist die dort ebenfalls instabil, sagt die Probe etwas
ueber das VERFAHREN und nicht ueber die Groesse.

⚠️ NUR LESEND, keine Netzabrufe, keine Standard-DB.
"""
import os
import statistics as st
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
os.chdir("D:/CLAUDE_Projects/SoftwareProjekte/TradingInfoTool")
sys.path.insert(0, "D:/CLAUDE_Projects/SoftwareProjekte/TradingInfoTool")

import numpy as np                                          # noqa: E402

import messe_bewertungskennzahl as MB                       # noqa: E402
import messe_eigenschaft_beitrag as B                       # noqa: E402
import messe_kandidaten_als_regel as K                      # noqa: E402
import phase4_c_kalibrierung_freefloat as KF                # noqa: E402

CRV = 2.0
# ⚠️ H5 ist der Horizont, auf dem die Naeherung MONOTON ist
# und auf allen zulaessigen Mengen TRAEGT. Ueber --horizont
# aenderbar, damit H3 und H20 nachrechenbar bleiben.
HOR = (int(sys.argv[sys.argv.index("--horizont") + 1])
       if "--horizont" in sys.argv else 5)


def stufen_aus(je_tag: dict) -> tuple:
    """Genau die Rechnung aus `rechne_turnover_beitrag` - nicht eine
    zweite. Wer sie nachbaut, misst beim naechsten Mal etwas anderes."""
    sammel = {k: [] for k in range(5)}
    for z in je_tag.values():
        if len(z) < 15:
            continue
        w = np.array([x["kennzahl"] for x in z])
        y = np.array([x["in_r"] for x in z])
        r = np.argsort(np.argsort(w)) / max(len(w) - 1, 1)
        for k in range(5):
            m = (r >= k / 5) & (r < (k + 1) / 5 if k < 4 else r <= 1.0)
            if m.sum() >= 2:
                sammel[k].append(float(np.median(y[m])))
    if any(not sammel[k] for k in range(5)):
        return None, 0
    werte = [st.mean(sammel[k]) for k in range(5)]
    mittel = st.mean(werte)
    faktor = 1.0 / (1.0 + CRV)
    stufen = [round(100.0 * (werte[k] - mittel) * faktor / 2.0, 2)
              for k in range(5)]
    return stufen, sum(1 for z in je_tag.values() if len(z) >= 15)


def form(stufen) -> str:
    if stufen is None:
        return "keine Tabelle"
    fallend = all(stufen[i] >= stufen[i + 1] for i in range(4))
    steigend = all(stufen[i] <= stufen[i + 1] for i in range(4))
    if fallend and steigend:
        return "flach"
    if fallend:
        return "monoton fallend"
    if steigend:
        return "monoton STEIGEND"
    return "⚠️ Zickzack"


def main() -> int:
    print("=" * 100)
    print("R-R8/B6 - HAELT DIE FORM IN BEIDEN HISTORIENHAELFTEN? (H%d)" % HOR)
    print("=" * 100)
    reihen = B.lade()
    quellen = []
    # ⚠️⚠️ DIE NAEHERUNG DAZU (21.09.2026): sie ist der
    # Kandidat, der auf H5 monoton ist UND auf allen zulaessigen
    # Mengen traegt. Genau ihre Form muss ueber beide Haelften
    # halten - bei `umschlag_frei` tat sie das nicht.
    import phase4_c_naeherung_konstante_menge as NK
    _h, _raus = NK.mengen_heute()
    _umst = NK.umstellungen(reihen)
    _naeh = dict()
    for _s, _m in _h.items():
        if _s in _umst:
            continue
        _z = reihen.get(_s)
        if _z:
            _naeh[_s] = dict((str(_x[0])[:10], _m) for _x in _z)
    quellen.append(("umschlag_naeherung", _naeh))
    neu, _w, _g = KF.menge_neu(KF.MENGE_DB, True)
    quellen.append(("umschlag_frei", neu))
    quellen.append(("umschlag_gesamt",
                    MB.reihe("data/onchain_historie.db", "splycur")))

    for name, menge in quellen:
        KF._SPEICHER.clear()
        je = K.baue(reihen, "turnover", menge, horizont=HOR)
        tage = sorted(je)
        if not tage:
            print("  %s: keine Ankertage" % name)
            continue
        mitte = tage[len(tage) // 2]
        h1 = {t: z for t, z in je.items() if t < mitte}
        h2 = {t: z for t, z in je.items() if t >= mitte}
        print()
        print("-" * 100)
        print("  %s   %d Ankertage · Schnitt bei %s"
              % (name, len(tage), mitte))
        print("-" * 100)
        print("  %-18s %-44s %8s  %s"
              % ("Haelfte", "Stufen", "Tage", "Form"))
        formen = []
        for titel, w in (("GANZ", je), ("1. Haelfte", h1),
                         ("2. Haelfte", h2)):
            stu, n = stufen_aus(w)
            f = form(stu)
            if titel != "GANZ":
                formen.append(f)
            print("  %-18s %-44s %8d  %s"
                  % (titel,
                     ("(" + ", ".join("%+5.2f" % x for x in stu) + ")")
                     if stu else "-", n, f))
        gleich = len(set(formen)) == 1 and "Zickzack" not in formen[0]
        print()
        print("  ==> %s"
              % ("✔ die Form ist in beiden Haelften gleich: %s" % formen[0]
                 if gleich else
                 "⚠️ die Form haelt NICHT: %s" % " gegen ".join(formen)))
    print()
    print("=" * 100)
    print("  ⚠️ Kein Urteil ueber die WIRKUNG - je Haelfte rund 180 Tage,")
    print("     und 20 Bloecke brauchen 300. Geprueft ist allein die FORM.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
