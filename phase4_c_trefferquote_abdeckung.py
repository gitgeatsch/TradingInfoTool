# -*- coding: utf-8 -*-
"""WIE VIEL PROZENT MEHR? - Kette mit Lueckenrabatt gegen Kette mit
Abdeckung, auf der NEUTRALEN Einstiegsbewertung.

⚠️⚠️⚠️ ZWEI EIGENE FEHLLESUNGEN STECKEN IN DER VORGESCHICHTE DIESER
DATEI (22.09.2026). Sie stehen hier, weil beide wiederkommen koennen.

## Fehllesung 1 - der angeglichene Auswahlanteil

`phase4_c_ist_das_ergebnis_besser.py` hat die Schwelle des neuen Arms
per Bisektion auf denselben Auswahlanteil gedreht. Das ist richtig, wenn
man ORDNUNG gegen ORDNUNG vergleicht (2.518). Es ist falsch fuer die
Frage, um die es hier geht: der LUECKENRABATT ist genau der Unterschied,
und er steckt im Auswahlanteil. Hier wird deshalb NICHT angeglichen -
der Anteil wird je Arm AUSGEWIESEN (R-R8/B4).

## Fehllesung 2 - der Horizont, und sie war die schwerere

Ich hatte aus 2.513-horizont geschlossen, die Einstiegsbewertung
gehoere auf H3. ⛔ FALSCH. Der Befund traegt seine eigene
Einschraenkung: *„die 555 Faelle sind BESTANDSENTSCHEIDUNGEN
(NACHKAUFEN, REDUZIEREN, HALTEN); Neueinstiege gibt es seit A1 praktisch
nicht."* Gemessen war die FUEHRUNG, nicht der EINSTIEG.

⚠️⚠️ DIE ARCHITEKTUR, die das klaert (Nutzervorgabe 22.09., am Code
nachgeprueft):

    1. EINSTIEGSBEWERTUNG   neutral, gilt fuer Spot UND Hebel GLEICH
                            funding + turnover -> Quote -> Potential
    2. Kommt ein Signal?
    3. ERST DANN            Risiko- und Hebelrechnung, dynamisch je Trade
                            `hebel = verlustanteil / stop_rel`, gedeckelt
                            (entscheidungsrechnung.py:182, 1698)
                            ⇒ HIER kommt die Haltedauer ins Spiel
    4. SPOT                 eher langfristig -> Akkumulation

Die Haltedauer des HEBELS ist nicht der Horizont der BEWERTUNG. Und eine
eigene Hebel-Bewertung darf es nach Regel 3 gar nicht geben - 2a hat das
entschieden. Deshalb misst diese Datei `bewegung_r` (*„wie viel ist zu
holen"*) auf dem registrierten H20, NICHT `barriere` und NICHT H3.

## Die drei Arme

    A  HEUTE      ALT-Tabelle, Abdeckung `splycur`   (Lueckenrabatt aktiv)
    B  LOESUNG    NEU-Tabelle, Abdeckung Naeherung
    C  NUR MENGE  ALT-Tabelle, Abdeckung Naeherung

C trennt Tabelle von Abdeckung. ⚠️ Faellt C mit B zusammen, waehlen
beide Tabellen dieselben Faelle - dann ist die Tabelle folgenlos, und
das ist ein Ergebnis, kein Fehler (es bestaetigt 2.518 von der anderen
Seite).

## ⚠️⚠️ WAS DIESE MESSUNG NICHT KANN

Die Anker stammen aus `K.baue(..., naeh, ...)` - also nur von Symbolen,
die eine Naeherungsmenge haben. Arm B hat darauf per Konstruktion
100 Prozent Abdeckung, im BETRIEB sind es 59. Der gemessene Effekt ist
damit eine OBERGRENZE der Abdeckungswirkung, nicht der Betriebswert.

## ⚠️ VORABFESTLEGUNG (vor dem Lauf geschrieben)

| Ergebnis | Deutung |
|---|---|
| B ueber A, Band ueber null | ✔ die Loesung gewinnt haeufiger |
| Baender ueberlappen | ⚠ kein Unterschied nachweisbar |
| B unter A, Band unter null | ✖ die Loesung gewinnt seltener |

⚠️ NULLKONTROLLE mit gemischten Raengen · POSITIVKONTROLLE auf die
DIFFERENZ (Methodik 2.105) · NUR LESEND.
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
NEU_TAB = (2.32, 0.50, 0.34, -0.11, -3.06)      # H20, ab 2023 (2.517)
BLOCK = 60              # = messnorm._block(20)
ZIEH = 400


def _arg(a, f, v):
    return a[a.index(f) + 1] if f in a else v


def fuenftel(werte: list) -> dict:
    n = len(werte)
    werte = sorted(werte, key=lambda x: x[1])
    return {s: min(int(i / n * 5), 4) for i, (s, _v) in enumerate(werte)}


def potential(fu_pkt, tu_pkt):
    q = WK.basisrate(CRV) + (fu_pkt + tu_pkt) / 100.0
    return q * CRV - (1.0 - q)


def band(werte, saat):
    r = np.random.default_rng(saat)
    nb = max(1, len(werte) // BLOCK)
    z = []
    for _ in range(ZIEH):
        ix = r.integers(0, max(1, len(werte) - BLOCK), size=nb)
        z.append(float(np.mean(np.concatenate(
            [werte[i:i + BLOCK] for i in ix]))))
    z.sort()
    return (float(np.mean(werte)), z[int(.05 * ZIEH)], z[int(.95 * ZIEH)])


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    H = int(_arg(args, "--horizont", "20"))
    saat = int(_arg(args, "--saat", "20260922"))
    t0 = time.time()

    ALT_TAB = next(b.stufen for b in WK.BEITRAEGE
                   if b.merkmal == "turnover_fuenftel")
    FU_TAB = next(b.stufen for b in WK.BEITRAEGE
                  if b.merkmal == "funding_fuenftel")
    voll_alt = max(FU_TAB) + max(ALT_TAB)
    voll_neu = max(FU_TAB) + max(NEU_TAB)
    sch_alt = P.SCHWELLE_VORGABE
    sch_neu = P.SCHWELLE_VORGABE * (
        potential(max(FU_TAB), max(NEU_TAB))
        / potential(max(FU_TAB), max(ALT_TAB)))

    print("=" * 100)
    print("WIE VIEL PROZENT MEHR? - Lueckenrabatt gegen Abdeckung  "
          "(bewegung_r, H%d)" % H)
    print("=" * 100)
    print("  A HEUTE    %s  Schwelle %.4f" % (ALT_TAB, sch_alt))
    print("  B LOESUNG  %s  Schwelle %.4f" % (NEU_TAB, sch_neu))
    print("  C NUR MENGE  ALT-Tabelle auf der Naeherungs-Abdeckung")
    print("  ⚠️ Auswahlanteil NICHT angeglichen - er ist Teil des Effekts.")
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

    KF._SPEICHER.clear()
    je = KF.beschneiden(K.baue(reihen, "turnover", naeh, horizont=H),
                        None, NK.AB)

    r_neu, r_alt, r_fu = {}, {}, {}
    for tag, z in je.items():
        wn = [(x["sym"], x["kennzahl"]) for x in z]
        if len(wn) >= 12:
            r_neu[tag] = fuenftel(wn)
        wa = []
        for x in z:
            s = x["sym"]
            d, zr = echt.get(s), reihen.get(s)
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

    n_ges = sum(len(z) for z in je.values())
    n_alt = sum(1 for t, z in je.items() for x in z
                if (r_alt.get(t) or {}).get(x["sym"]) is not None)
    print("  %d Ankertage, %d Anker" % (len(je), n_ges))
    print("  Anker MIT turnover-Wert:  A %.1f %%  ·  B/C 100,0 %% "
          "(im Betrieb 59 %% - siehe Kopf)"
          % (100.0 * n_alt / max(1, n_ges)))
    print()

    def lauf(modus, mische=None):
        """modus 'gewinn' = Anteil in_r > 0 · 'hoehe' = Median in_r."""
        rng = np.random.default_rng(mische) if mische is not None else None
        tage, q = {}, ([], [], [], [])
        for tag, z in je.items():
            fu_r = r_fu.get(tag)
            if not fu_r:
                continue
            ta, tn = r_alt.get(tag, {}), r_neu.get(tag, {})
            if rng is not None:
                # ⚠️⚠️ KOPIE, NICHT IN PLACE. Mein erster Entwurf rechnete
                # `d.clear(); d.update(...)` auf den Dicts in `r_alt`/`r_neu`
                # - also auf den ECHTEN Raengen. Folge: jede weitere
                # Nullkontrolle mischte bereits Gemischtes.
                ta = dict(zip(list(ta), rng.permutation(list(ta.values()))))
                tn = dict(zip(list(tn), rng.permutation(list(tn.values()))))
            ya, yb, yc, alle = [], [], [], []
            for x in z:
                s = x["sym"]
                y = (1.0 if x["in_r"] > 0 else 0.0) if modus == "gewinn" \
                    else float(x["in_r"])
                alle.append(y)
                f = fu_r.get(s)
                if f is None:
                    continue
                fp = FU_TAB[f]
                a, nn = ta.get(s), tn.get(s)
                if potential(fp, ALT_TAB[a] if a is not None else 0.0) \
                        >= (sch_alt if a is not None
                            else sch_alt * max(FU_TAB) / voll_alt):
                    ya.append(y)
                if potential(fp, NEU_TAB[nn] if nn is not None else 0.0) \
                        >= (sch_neu if nn is not None
                            else sch_neu * max(FU_TAB) / voll_neu):
                    yb.append(y)
                if potential(fp, ALT_TAB[nn] if nn is not None else 0.0) \
                        >= (sch_alt if nn is not None
                            else sch_alt * max(FU_TAB) / voll_alt):
                    yc.append(y)
            if len(alle) < 12 or not ya or not yb or not yc:
                continue
            mit = (np.mean if modus == "gewinn" else np.median)
            m = float(mit(alle))
            tage[tag] = (float(mit(ya)) - m, float(mit(yb)) - m,
                         float(mit(yc)) - m)
            for i, w in enumerate((ya, yb, yc)):
                q[i].append(len(w) / len(alle))
            q[3].append(m)
        return tage, [st.mean(x) if x else 0.0 for x in q]

    def zeige(modus, titel, einheit, skala):
        tage, anteile = lauf(modus)
        if not tage:
            print("  \u26d4 %s: keine auswertbaren Tage" % titel)
            return
        t = sorted(tage)
        mw = [st.mean([tage[x][i] for x in t]) for i in range(3)]
        basis = anteile[3]
        print("  " + "=" * 84)
        print("  %s   (%d Tage)" % (titel, len(t)))
        print("  " + "=" * 84)
        print("  %-34s %12s %12s %12s"
              % ("", "A HEUTE", "B LOESUNG", "C NUR MENGE"))
        print("  " + "-" * 76)
        print("  %-34s %11.1f %% %11.1f %% %11.1f %%"
              % ("Auswahlanteil je Tag", 100 * anteile[0],
                 100 * anteile[1], 100 * anteile[2]))
        f = "%11.1f %%" if skala == 100 else "%13.4f"
        print(("  %-34s " + f + " " + f + " " + f)
              % ((titel.split("  ")[0],) + tuple(
                  skala * (basis + m) for m in mw)))
        print(("  %-34s " + f) % ("dasselbe fuer ALLE Anker",
                                  skala * basis))
        print("  " + "-" * 76)
        print("  %-34s %+12.2f %+12.2f %+12.2f"
              % ("Vorsprung in " + einheit,
                 skala * mw[0], skala * mw[1], skala * mw[2]))
        print()
        for name, i in (("B minus A  (ganze Aenderung)", 1),
                        ("C minus A  (Abdeckung allein)", 2)):
            d = np.array([tage[x][i] - tage[x][0] for x in t]) * skala
            m, u, o = band(d, saat)
            print("  %-32s %+7.2f %s  [%+6.2f .. %+6.2f]  %s"
                  % (name, m, einheit, u, o,
                     "\u2714 TRAEGT" if u > 0 else
                     "\u2716 SCHLECHTER" if o < 0 else
                     "\u26a0 nicht trennbar"))
        nk = []
        for ms in (11, 22, 33):
            tg, _a = lauf(modus, mische=ms)
            if tg:
                nk.append(skala * st.mean(
                    [v[1] - v[0] for v in tg.values()]))
        if nk:
            print("  %-32s %s  Mittel %+6.2f %s"
                  % ("NULLKONTROLLE (gemischt)",
                     " ".join("%+6.2f" % x for x in nk),
                     st.mean(nk), einheit))
        d = np.array([tage[x][1] - tage[x][0] for x in t]) * skala
        ist = band(d, saat)[0]
        gef = []
        print()
        print("  POSITIVKONTROLLE auf die DIFFERENZ (2.105):")
        for auf in ([0.0, 0.5, 1.0, 2.0, 5.0] if skala == 100
                    else [0.0, 0.01, 0.02, 0.05]):
            m, u, o = band(d + auf, saat)
            if auf > 0 and u > 0:
                gef.append(auf)
            print("    %-18s %+7.2f  [%+6.2f .. %+6.2f]  %s"
                  % (("+%.2f %s" % (auf, einheit)) if auf
                     else "nichts (Ist-Lage)", m, u, o,
                     "TRAEGT" if u > 0 else "nicht trennbar"))
        if gef:
            print("    \u27a4 Die Anlage findet eine WAHRE Differenz ab "
                  "%+.2f %s" % (ist + min(gef), einheit))
        else:
            print("    \u26a0 Die Anlage findet KEINE aufgepraegte "
                  "Staerke - diese Messung sagt nichts")
        print()

    zeige("gewinn", "GEWINNANTEIL  (Anteil mit in_r > 0)",
          "Pp", 100)
    zeige("hoehe", "HOEHE  (Median in_r)", "R", 1)

    print("  Dauer %.1f Minuten" % ((time.time() - t0) / 60.0))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
