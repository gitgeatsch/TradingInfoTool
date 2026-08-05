"""SHORT als VERGLEICH messen - und was dabei auffiel (05.08.).

ANLASS war eine Korrektur des Nutzers: SHORT ist nicht tot, sondern laeuft
unsichtbar weiter (Veto-Schatten-Tracking), und SHORT muss als VERGLEICH
gemessen werden. Beides war richtig, und beides zusammen drehte den Befund,
den ich Stunden vorher committet hatte.

WAS ICH VORHER FALSCH EINGEORDNET HATTE: ich nannte die 313 wegen "Nur Long"
verworfenen SHORT-Signale "nie ausfuehrbar - 20,8 % der Kapazitaet". Das
unterstellt Verlust. Tatsaechlich sind 311 der 313 im Schatten weiterverfolgt
(veto_outcome_status befuellt).

WAS DIE MESSUNG DANN ZEIGTE (Schatten-Outcome, gleiche Methode fuer alle):

    SHORT, Nur-Long-Veto      n=313  aufgeloest= 88  Treffer 10,2 %  EW -1,136 R
    LONG, ausgefuehrt         n=162  aufgeloest= 70  Treffer 17,1 %  EW -0,332 R
    andere Vetos (Kontrolle)  n=415  aufgeloest=274  Treffer 43,8 %  EW +0,054 R

Die Kontrollgruppe ist der Punkt: andere vetote Signale, mit demselben
Schattenverfahren gemessen, liegen bei 43,8 %. Das Verfahren funktioniert
also - die verworfenen SHORTs sind wirklich die schlechteste Gruppe im
System. Das Nur-Long-Veto vernichtet keine Kapazitaet, es ist der schaerfste
Filter, den wir haben.

DER EIGENTLICHE FUND kam erst beim Zeitschnitt - und er betrifft NICHT SHORT:

                        bis 30.07.        ab 31.07.
    LONG                   38,5 %            4,0 %
    SHORT                  36,6 %            9,1 %

BEIDE Richtungen brechen gleichzeitig ein. Ein Marktrichtungseffekt kann das
nicht sein - eine schaerfere Abwaertsbewegung wuerde LONG schaden und SHORT
helfen. Das Regime war ohnehin an jedem Tag "abwaerts", Fear&Greed 25-33.

DREI EINWAENDE GEGEN DEN BEFUND, ALLE GEPRUEFT:

1. Rechtszensierung (junge Kohorte hat ihre Take-Profits noch vor sich)?
   ENTKRAEFTET. TP und SL loesen gleich schnell auf - Median je 2,0 Tage,
   bis Tag 5 sind 82,8 % der TP und 78,7 % der SL da. Keine Asymmetrie.
2. Die Stops wurden am 31.07. weiter (2,6 % -> 7,5 %), Ziele entsprechend
   (10,4 % -> 14,1 %) - dadurch brauchen neue Signale laenger?
   ENTKRAEFTET per Landmark-Analyse mit identischem Fenster fuer beide
   Kohorten: LONG 42,2->4,2 (H=3), 43,9->5,6 (H=4), 43,8->7,7 (H=5).
3. Symbol-Konzentration (die junge Kohorte hat nur 9 Symbole, groesstes 31 %)?
   ENTKRAEFTET per Block-Bootstrap ueber Symbole, 10.000 Ziehungen:
   Differenz +35,9 pp, 95 %-Intervall [+15,4 ; +56,9], p ~ 0,0001.

BEGLEITBEFUNDE ZUM 31.07., die auf einen Deploy deuten statt auf den Markt:
  - atr_relativ_prozent_bei_signal ist VOR dem 31.07. leer und danach befuellt
  - Signalvolumen an dem Tag 239 gegen 13-21 an den beiden Vortagen
  - SHORT-Anteil springt binnen einer Stunde von 0 % (11:00 UTC) auf 100 %
  - Screening unveraendert: Kontra-Zweig stabil 8-21 %, Trigger-Richtungen gleich

Die Ursache ist damit NICHT gefunden, nur eingekreist. Was feststeht: es ist
kein Marktereignis, kein Messartefakt und keine Richtungsfrage.

Lauf: python -u messe_short_und_einbruch.py
"""
from __future__ import annotations

import io
import json
import random
import statistics
from collections import Counter, defaultdict
from datetime import datetime

ORDNER = r"K:\My Drive\Claude_Austauschordner\Notebook_Analysedaten"
TP, SL = "take_profit_erreicht", "stop_loss_erreicht"
# Die drei Outcome-Familien in der Reihenfolge, in der sie gelten: ein Signal
# hat entweder ein regulaeres Ergebnis, oder - wenn das Gate es drehte - ein
# Veto-Schatten-Ergebnis, oder - bei selbst gewaehltem HALTEN - das dritte.
PRAEFIXE = ("", "veto_", "selbst_halten_")
GRENZE = "2026-07-31"
NAN = float("nan")


def _tag(x):
    try:
        return datetime.strptime(str(x or "")[:10], "%Y-%m-%d")
    except ValueError:
        return None


def ausgang(s):
    for pre in PRAEFIXE:
        st = str(s.get(pre + "outcome_status") or "")
        if st in (TP, SL):
            return st, _tag(s.get(pre + "outcome_entschieden_am"))
    return None, None


def kennzahlen(g, label, pre="veto_"):
    st = [str(s.get(pre + "outcome_status") or "") for s in g]
    tp, sl = st.count(TP), st.count(SL)
    auf = tp + sl
    crv = [s[pre + "outcome_realisiertes_crv"] for s in g
           if isinstance(s.get(pre + "outcome_realisiertes_crv"), (int, float))]
    print("  {:34s} n={:4d}  aufgeloest={:3d}  TP={:3d} SL={:3d}  "
          "Treffer={:5.1f}%  EW={:+6.3f} R".format(
              label, len(g), auf, tp, sl,
              tp / auf * 100 if auf else NAN,
              statistics.fmean(crv) if crv else NAN))


def landmark(g, h, stand):
    """Nur Signale, die am Stichtag mindestens h Tage alt sind - und nur
    Ausgaenge, die binnen h Tagen fielen. Damit sehen alte und junge Kohorte
    exakt dasselbe Beobachtungsfenster."""
    tp = sl = n = 0
    for s in g:
        a = _tag(s.get("created_at"))
        if not a or (stand - a).days < h:
            continue
        n += 1
        st, b = ausgang(s)
        if st and b and (b - a).days <= h:
            tp, sl = (tp + 1, sl) if st == TP else (tp, sl + 1)
    auf = tp + sl
    return n, auf, tp, sl, (tp / auf * 100 if auf else NAN)


def block_bootstrap(alt, neu, ziehungen=10000):
    """Ueber SYMBOLE, nicht ueber Signale. Zwei Signale desselben Symbols am
    selben Tag sind keine zwei unabhaengigen Beobachtungen; naive Intervalle
    ueberschaetzen die Signifikanz entsprechend."""
    def bloecke(g):
        b = defaultdict(list)
        for sym, y in g:
            b[sym].append(y)
        return list(b.values())

    ba, bn = bloecke(alt), bloecke(neu)
    rnd = random.Random(20260805)
    diffs = []
    for _ in range(ziehungen):
        a = [y for _ in ba for y in rnd.choice(ba)]
        n = [y for _ in bn for y in rnd.choice(bn)]
        if a and n:
            diffs.append(sum(a) / len(a) - sum(n) / len(n))
    diffs.sort()
    return (diffs[int(.025 * len(diffs))], diffs[int(.975 * len(diffs))],
            sum(1 for x in diffs if x <= 0) / len(diffs))


def main():
    d = json.load(io.open(ORDNER + r"\notebook_diagnose.json", encoding="utf-8"))
    sig = d["hebel_signals"]
    stand = max((_tag(s.get("created_at")) for s in sig if _tag(s.get("created_at"))),
                default=datetime.now())

    print("=" * 78)
    print("A. Werden die Nur-Long-Vetos ueberhaupt weiterverfolgt?")
    print("=" * 78)
    nl = [s for s in sig if "Nur Long" in str(s.get("risk_veto_reason") or "")]
    print("  Faelle {}, davon mit Schatten-Status {}".format(
        len(nl), sum(1 for s in nl if s.get("veto_outcome_status"))))
    print("  Status: {}".format(
        dict(Counter(str(s.get("veto_outcome_status") or "LEER") for s in nl))))

    print("\n" + "=" * 78)
    print("B. SHORT gegen LONG - mit Kontrollgruppe")
    print("=" * 78)
    kennzahlen(nl, "SHORT, Nur-Long-Veto (Schatten)")
    ausg = [s for s in sig if not s.get("risk_veto_reason")
            and str(s.get("action") or "") != "HALTEN"]
    for r in ("LONG", "SHORT"):
        kennzahlen([s for s in ausg if str(s.get("richtung") or "").upper() == r],
                   r + ", ausgefuehrt", "")
    kennzahlen([s for s in sig if s.get("risk_veto_reason")
                and "Nur Long" not in str(s["risk_veto_reason"])],
               "andere Vetos (KONTROLLE)")

    print("\n" + "=" * 78)
    print("C. Landmark-Analyse: identisches Fenster fuer beide Kohorten")
    print("=" * 78)
    for h in (3, 4, 5):
        print("--- H = {} Tage ---".format(h))
        for r in ("LONG", "SHORT"):
            for lab, frueh in (("bis 30.07.", True), ("ab 31.07.", False)):
                g = [s for s in sig if str(s.get("richtung") or "").upper() == r
                     and ((str(s.get("created_at") or "")[:10] < GRENZE) == frueh)]
                n, auf, tp, sl, wr = landmark(g, h, stand)
                print("  {:28s} n>=H={:4d} aufgeloest={:3d} TP={:3d} SL={:3d} "
                      "Treffer={:6.1f}%".format(r + " " + lab, n, auf, tp, sl, wr))

    print("\n" + "=" * 78)
    print("D. Block-Bootstrap ueber Symbole (H=4, beide Richtungen zusammen)")
    print("=" * 78)

    def hol(frueh):
        raus = []
        for s in sig:
            a = _tag(s.get("created_at"))
            if not a or (stand - a).days < 4:
                continue
            if (str(s.get("created_at") or "")[:10] < GRENZE) != frueh:
                continue
            st, b = ausgang(s)
            if st and b and (b - a).days <= 4:
                raus.append((s.get("symbol") or "?", 1 if st == TP else 0))
        return raus

    alt, neu = hol(True), hol(False)
    if not alt or not neu:
        print("  eine der Kohorten ist leer - Vergleich nicht moeglich")
        return 1
    for lab, g in (("bis 30.07.", alt), ("ab 31.07.", neu)):
        c = Counter(x[0] for x in g)
        top = c.most_common(4)
        print("  {:12s} n={:4d} Symbole={:3d} groesstes={}% Top4={}%".format(
            lab, len(g), len(c), top[0][1] * 100 // len(g),
            sum(n for _, n in top) * 100 // len(g)))
    ra = sum(y for _, y in alt) / len(alt)
    rn = sum(y for _, y in neu) / len(neu)
    lo, hi, p = block_bootstrap(alt, neu)
    print("\n  alt {:.1f}%  neu {:.1f}%  Differenz {:+.1f} pp".format(
        ra * 100, rn * 100, (ra - rn) * 100))
    print("  95%-Intervall [{:+.1f} pp , {:+.1f} pp]   p = {:.4f}".format(
        lo * 100, hi * 100, p))
    print("\n  " + ("BESTAETIGT - der Einbruch ueberlebt die Symbol-Clusterung"
                    if lo > 0 else "NICHT belastbar - Intervall schliesst 0 ein"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
