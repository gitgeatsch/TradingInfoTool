# -*- coding: utf-8 -*-
"""IST DAS ERGEBNIS BESSER? - die Kette mit alter gegen neue Tabelle.

⚠️⚠️⚠️ WARUM DIESE MESSUNG DIE EIGENTLICHE IST (21.09.2026).
Nutzerauftrag: *„führe eine Fachliche prüfung durch ob das Ergebnis und
die Simulation ein besseres Ergebnis ist"*.

Bis hierher war gemessen:

    2.515  DASS `umschlag_naeherung` traegt (+0,0172 R Sperrwirkung)
    2.516  dass die ORDNUNG traegt (Regler gerechtfertigt)
    2.517  WAS sich im Betrieb aendert (mehr Werte, weniger Signale,
           hoeherer Hebel)

⚠️ NICHT gemessen war: ob die Anker, die durchkommen, ein BESSERES
Ergebnis haben. Das ist die Frage `wirksamkeit-statt-merkmalsmessung` -
und sie ist die einzige, die zaehlt.

## Der Aufbau

Je Kalendertag wird die ganze Auswahlregel nachgebildet:

    Quote    = Basisrate + (funding-Punkte + turnover-Punkte) / 100
    Potential= Quote x CRV - (1 - Quote)
    Auswahl  = Potential >= Schwelle je Datenlage

Einmal mit der REGISTRIERTEN Tabelle auf `umschlag_gesamt`, einmal mit
der NEUEN auf `umschlag_naeherung`. Verglichen wird der Median des
Ergebnisses (`in_r`) der jeweils Ausgewaehlten - gegen den Median ALLER
Anker desselben Tages.

⚠️ TAGESKLAMMER: der Vergleich laeuft INNERHALB eines Tages. Sonst
mischt er Marktphasen, und eine Regel, die in guten Zeiten mehr
auswaehlt, saehe besser aus, ohne besser zu sein (Methodik 2.86).

## ⚠️⚠️ VORABFESTLEGUNG

| Ergebnis | Deutung |
|---|---|
| NEU besser als ALT, Band ueber null | ✔ die neue Tabelle ist besser |
| Baender ueberlappen | ⚠ kein Unterschied nachweisbar |
| ALT besser | ✖ die neue Tabelle ist schlechter |

⚠️ ZUSAETZLICH WIRD DIE AUSWAHLMENGE AUSGEWIESEN. Eine Regel, die
weniger auswaehlt, hat es leichter - der Vergleich braucht beide
Zahlen (R-R8/B4).

⚠️ NULLKONTROLLE: dieselbe Rechnung mit gemischten Raengen. Liefert sie
auch einen Unterschied, misst die Anlage sich selbst
(`median-minus-median-verzerrt`).

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

import agent.potential as P                                 # noqa: E402
import agent.wahrscheinlichkeit as WK                       # noqa: E402
import messe_bewertungskennzahl as MB                       # noqa: E402
import messe_eigenschaft_beitrag as B                       # noqa: E402
import messe_funding_niveau as F                            # noqa: E402
import messe_kandidaten_als_regel as K                      # noqa: E402
import phase4_c_kalibrierung_freefloat as KF                # noqa: E402
import phase4_c_naeherung_konstante_menge as NK             # noqa: E402

CRV = 2.0
ALT_TAB = None          # wird aus der Registrierung gelesen
NEU_TAB = (2.32, 0.50, 0.34, -0.11, -3.06)      # H20, ab 2023
FU_TAB = None
BLOCK = 60              # = messnorm._block(20)
ZIEH = 400


def _arg(a, f, v):
    return a[a.index(f) + 1] if f in a else v


def fuenftel(werte: list) -> dict:
    n = len(werte)
    werte = sorted(werte, key=lambda x: x[1])
    return {s: min(int(i / n * 5), 4) for i, (s, _v) in enumerate(werte)}


def potential(fu_pkt, tu_pkt, hat_tu):
    """Quote, Potential und Schwelle je Datenlage - dieselbe Rechnung
    wie `wahrscheinlichkeit.rechne` und `Potential.schwelle`, aber ohne
    den Umweg ueber 2.550 Einzelaufrufe."""
    basis = WK.basisrate(CRV)
    q = basis + (fu_pkt + tu_pkt) / 100.0
    pot = q * CRV - (1.0 - q)
    return pot


sch_neu = 0.0


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    H = int(_arg(args, "--horizont", "20"))
    saat = int(_arg(args, "--saat", "20260921"))
    t0 = time.time()

    global ALT_TAB, FU_TAB
    ALT_TAB = next(b.stufen for b in WK.BEITRAEGE
                   if b.merkmal == "turnover_fuenftel")
    FU_TAB = next(b.stufen for b in WK.BEITRAEGE
                  if b.merkmal == "funding_fuenftel")
    basis = WK.basisrate(CRV)
    voll = max(FU_TAB) + max(ALT_TAB)
    voll_neu = max(FU_TAB) + max(NEU_TAB)

    print("=" * 104)
    print("IST DAS ERGEBNIS BESSER? - die ganze Auswahlregel, H%d" % H)
    print("=" * 104)
    print("  ALT %s   voll %.2f Pkt" % (ALT_TAB, voll))
    print("  NEU %s   voll %.2f Pkt" % (NEU_TAB, voll_neu))
    print("  ⚠️ Die Schwelle wird je Tabelle MITGEZOGEN (R-R9): derselbe")
    print("     Anteil der erreichbaren Spanne wie heute.")
    anteil = P.SCHWELLE_VORGABE / (basis * CRV - (1 - basis)
                                   + voll / 100.0 * (1 + CRV))
    global sch_neu
    sch_alt = P.SCHWELLE_VORGABE
    sch_neu = P.SCHWELLE_VORGABE * (
        (potential(max(FU_TAB), max(NEU_TAB), True))
        / (potential(max(FU_TAB), max(ALT_TAB), True)))
    print("     Schwelle ALT %.4f · NEU %.4f" % (sch_alt, sch_neu))
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
    echt = MB.reihe("data/onchain_historie.db", "splycur")
    fund = F.lade_funding()

    # Die Anker MIT Ergebnis - dafuer braucht es den Horizont
    KF._SPEICHER.clear()
    je = KF.beschneiden(K.baue(reihen, "turnover", naeh, horizont=H),
                        None, NK.AB)
    print("  %d Ankertage mit Ergebnis" % len(je))

    # Raenge je Tag: turnover ALT, turnover NEU, funding
    r_neu, r_alt, r_fu = {}, {}, {}
    for tag, z in je.items():
        syms = [x["sym"] for x in z]
        wn = [(x["sym"], x["kennzahl"]) for x in z]
        if len(wn) >= 12:
            r_neu[tag] = fuenftel(wn)
        wa = []
        for s in syms:
            d = echt.get(s)
            zr = reihen.get(s)
            if not d or not zr:
                continue
            m = d.get(tag)
            if not m or m <= 0:
                continue
            for t, c, _h, _l, v in zr:
                if str(t)[:10] == tag and v and c and c > 0:
                    wa.append((s, float(v) / (float(c) * float(m))))
                    break
        if len(wa) >= 12:
            r_alt[tag] = fuenftel(wa)
        wf = [(s, d[tag]) for s, d in fund.items() if tag in d]
        if len(wf) >= 12:
            r_fu[tag] = fuenftel(wf)
    print("  Raenge: neu %d · alt %d · funding %d Tage"
          % (len(r_neu), len(r_alt), len(r_fu)))
    print()

    # Je Tag: Auswahl treffen und Ergebnis messen
    def lauf(mische=None):
        rng = np.random.default_rng(mische) if mische is not None else None
        tage, n_alt, n_neu = {}, [], []
        for tag, z in je.items():
            fu_r = r_fu.get(tag)
            if not fu_r:
                continue
            ta, tn = r_alt.get(tag, {}), r_neu.get(tag, {})
            if rng is not None:
                ks = list(tn)
                vs = rng.permutation(list(tn.values()))
                tn = dict(zip(ks, vs))
                ks = list(ta)
                vs = rng.permutation(list(ta.values()))
                ta = dict(zip(ks, vs))
            ya, yn, alle = [], [], []
            for x in z:
                s, y = x["sym"], x["in_r"]
                alle.append(y)
                f = fu_r.get(s)
                if f is None:
                    continue
                fp = FU_TAB[f]
                a = ta.get(s)
                pa = potential(fp, ALT_TAB[a] if a is not None else 0.0, a)
                s_a = sch_alt if a is not None else sch_alt * (
                    max(FU_TAB) / voll)
                if pa >= s_a:
                    ya.append(y)
                nn = tn.get(s)
                pn = potential(fp, NEU_TAB[nn] if nn is not None else 0.0, nn)
                s_n = sch_neu if nn is not None else sch_neu * (
                    max(FU_TAB) / voll_neu)
                if pn >= s_n:
                    yn.append(y)
            if len(alle) < 12 or not ya or not yn:
                continue
            m_alle = float(np.median(alle))
            tage[tag] = (float(np.median(ya)) - m_alle,
                         float(np.median(yn)) - m_alle)
            n_alt.append(len(ya) / len(alle))
            n_neu.append(len(yn) / len(alle))
        return tage, (st.mean(n_alt) if n_alt else 0,
                      st.mean(n_neu) if n_neu else 0)

    # ⚠️⚠️ DER AUSWAHLANTEIL MUSS GLEICH SEIN (21.09.2026, eigener
    # Einwand nach dem ersten Lauf). Der erste Lauf verglich 23,6 %
    # gegen 9,0 % - und eine strengere Regel hat bessere Mediane, auch
    # OHNE bessere Information. Der Vergleich misst dann die Strenge.
    #
    # Deshalb wird die NEUE Schwelle so gesetzt, dass sie denselben
    # Anteil auswaehlt wie die alte. Erst dann vergleicht man die
    # ORDNUNG statt der Haerte.
    _t0, _a0 = lauf()
    ziel = _a0[0]
    lo, hi = 0.0, 0.30
    for _ in range(24):
        mitte = (lo + hi) / 2.0
        sch_neu = mitte
        _t, _a = lauf()
        if _a[1] > ziel:
            lo = mitte
        else:
            hi = mitte
    print("  ⚠️ Schwelle NEU auf gleichen Auswahlanteil gesetzt: %.4f"
          % sch_neu)
    print("     (Ziel %.1f %% wie ALT)" % (100 * ziel))
    print()
    tage, anteile = lauf()
    if not tage:
        print("  ⛔ keine auswertbaren Tage")
        return 2
    a = [v[0] for v in tage.values()]
    n = [v[1] for v in tage.values()]
    print("  %-30s %11s %11s" % ("", "ALT", "NEU"))
    print("  " + "-" * 56)
    print("  %-30s %10.1f %% %10.1f %%"
          % ("Auswahlanteil je Tag", 100 * anteile[0], 100 * anteile[1]))
    print("  %-30s %+11.4f %+11.4f"
          % ("Ergebnis gegen Tagesmedian", st.mean(a), st.mean(n)))
    print("  " + "-" * 56)

    # Blockbootstrap auf die DIFFERENZ
    t = sorted(tage)
    d = np.array([tage[x][1] - tage[x][0] for x in t])
    rng = np.random.default_rng(saat)
    nb = max(1, len(d) // BLOCK)
    zieh = []
    for _ in range(ZIEH):
        idx = rng.integers(0, max(1, len(d) - BLOCK), size=nb)
        zieh.append(float(np.mean(np.concatenate(
            [d[i:i + BLOCK] for i in idx]))))
    zieh.sort()
    unten, oben = zieh[int(.05 * ZIEH)], zieh[int(.95 * ZIEH)]
    print()
    print("  ➤ DIFFERENZ NEU minus ALT: %+.4f R  [%+.4f .. %+.4f]"
          % (float(np.mean(d)), unten, oben))
    print("     %d Bloecke a %d Tage" % (nb, BLOCK))

    # Nullkontrolle
    print()
    print("  NULLKONTROLLE - dieselbe Rechnung mit gemischten Raengen:")
    nulls = []
    for i in range(3):
        tn, _an = lauf(mische=5000 + i)
        if tn:
            nulls.append(st.mean([v[1] - v[0] for v in tn.values()]))
    if nulls:
        print("     %s  Mittel %+.4f"
              % ("  ".join("%+.4f" % x for x in nulls), st.mean(nulls)))
    # ---- ⚠️⚠️⚠️ DIE POSITIVKONTROLLE AUF DIE DIFFERENZ
    #
    # Methodik 2.105: *„Ohne sie ist ,nicht trennbar` nicht von
    # ,die Anlage kann es nicht sehen` zu unterscheiden.*
    #
    # Aufgepraegt wird auf die DIFFERENZ je Tag, nicht auf die
    # Einzelreihen - genau so verlangt es die Regel. Findet die
    # Anlage die aufgepraegte Staerke, ist ein Nullbefund BELEGT;
    # findet sie sie nicht, sagt die Messung ueberhaupt nichts.
    def band(werte):
        r2 = np.random.default_rng(saat)
        nb2 = max(1, len(werte) // BLOCK)
        zz = []
        for _ in range(ZIEH):
            ix = r2.integers(0, max(1, len(werte) - BLOCK), size=nb2)
            zz.append(float(np.mean(np.concatenate(
                [werte[i:i + BLOCK] for i in ix]))))
        zz.sort()
        return (float(np.mean(werte)), zz[int(.05 * ZIEH)],
                zz[int(.95 * ZIEH)])

    print()
    print("  POSITIVKONTROLLE auf die DIFFERENZ (Methodik 2.105):")
    print("  %-22s %11s %22s  %s"
          % ("aufgepraegt", "gemessen", "Band", "Urteil"))
    print("  " + "-" * 70)
    gefunden = []
    for auf in (0.00, 0.01, 0.02, 0.05):
        m, u, o = band(d + auf)
        traegt = u > 0
        if auf > 0:
            gefunden.append((auf, traegt))
        print("  %-22s %+11.4f [%+9.4f..%+9.4f]  %s"
              % ("%+.2f R" % auf if auf else "nichts (Ist-Lage)",
                 m, u, o, "TRAEGT" if traegt else "nicht trennbar"))
    print("  " + "-" * 70)
    kleinste = min((a for a, t in gefunden if t), default=None)
    if kleinste:
        print("  ➤ Die Anlage findet ab %+.2f R" % kleinste)
    else:
        print("  ⚠️ Die Anlage findet KEINE der aufgepraegten "
              "Staerken - sie kann hier nichts sehen.")

    print()
    print("  ==> %s"
          % ("✔ NEU ist BESSER - das Band schliesst null aus"
             if unten > 0 else
             "✖ ALT ist besser" if oben < 0 else
             ("⚠️ KEIN Unterschied nachweisbar - und die Anlage findet "
              "ab %+.2f R, der Nullbefund ist damit BELEGT"
              % kleinste) if kleinste else
             "⛔ die Anlage kann hier NICHTS sehen - diese Messung "
             "sagt nichts"))
    print()
    print("  Dauer %.1f Minuten" % ((time.time() - t0) / 60))
    return 0


if __name__ == "__main__":
    sys.exit(main())
