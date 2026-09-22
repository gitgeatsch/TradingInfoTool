# -*- coding: utf-8 -*-
"""G-2': wieviele PUNKTE traegt Turnover je Fuenftel? (30.08.2026, 2e)

Das Gegenstueck zu `rechne_funding_beitrag.py`. ⚠️ Es fehlte - und ohne diese
Tabelle waere Turnover mit GESCHAETZTEN Stufen registriert worden.
`messe_schwelle_kalibrierung.py` hat genau das getan: dort steht

    TURNOVER_STUFEN = (+0.81, +0.85, +0.25, -0.52, -1.39)   # "dieselbe Form"

also eine KOPIE der Funding-Stufen. Fuer eine Schwellensimulation ist das
vertretbar, fuer die Registrierung im Produktionscode nicht.

## Die Umrechnung, wie bei Funding

    Potential = quote * CRV - (1 - quote)
    d(Potential) = d(quote) * (1 + CRV)
    -> d(quote) = d(Potential) / (1 + CRV)          bei CRV 2,0 also 1/3

## ⚠️ IN-SAMPLE

Diese Zahlen stammen aus derselben Messung, die den Befund ergeben hat. Fuer
eine erste Kalibrierung ueblich, aber es gehoert benannt - und es ist der
Grund fuer die Halbierung ("geschrumpft"), dieselbe Vorsicht wie bei
`trefferbilanz.geschrumpft()`.

    python rechne_turnover_beitrag.py


---

⚠️⚠️⚠️ DIESES WERKZEUG MISST `umschlag_gesamt` - Volumen durch
GESAMTAUSGABE (`data/onchain_historie.db`, Coin Metrics `SplyCur`).
NICHT `umschlag_frei`.

Der Unterschied ist keine Feinheit: die beiden Groessen liegen im Median
25 Prozent auseinander, und ein Nennerwechsel verschiebt 76,7 Prozent
aller Fuenftel (2.505-rangwirkung). Die Namenstabelle steht in
`marktrang.UMSCHLAG_GROESSEN`.

⚠️⚠️ WARUM DER VERMERK HIER STEHT: am 21.09.2026 habe ich die unten
genannte Zahl `H2 Turnover +0,0107 R` als Machbarkeitsargument fuer die
NEUE Quelle benutzt. Sie gehoert zur ALTEN. Der Nutzer hat es gemerkt
(*„kontrolliere ob das das alte oder neue Turnover ist"*) - und genau
deshalb gibt es die Namen jetzt.

# ERWEITERUNG 01.09.2026 — DIE TABELLE JE HORIZONT

⚠️ DIESER ABSCHNITT IST DIE VORABFESTLEGUNG.

Die Stufen dieser Tabelle stammen aus einer Messung auf **H20** - zwanzig
Handelstagen. Das ist die SPOT-Geometrie. Fuer die Hebel-Zellen des
Zellenmodells (24 Assets, Schritt 3) ist sie die falsche: das System plante
`mindestziel_zeitraum_tage_geschaetzt` = **1,2 bis 2,1 Tage**.

Die WIRKUNG auf kurzem Horizont ist am 31.08. bereits gemessen
(`messe_kandidaten_als_regel.py --horizonte 1,2,3,5,10,20`):

    H2   Funding  +0,0026 R  [+0,0011 .. +0,0043]  TRAEGT
    H2   Turnover +0,0107 R  [+0,0068 .. +0,0147]  TRAEGT

**Was fehlt, ist die Umrechnung in Beitragspunkte** - dieselbe Rechnung wie
unten, nur mit einem anderen Horizont.

## Vorab festgelegt

  nutzbar        die Stufen sind MONOTON ueber die Fuenftel und die Spanne
                 ist groesser als null
  nicht nutzbar  sonst - dann bekommt die Hebel-Zelle KEINEN Beitrag und
                 laeuft mit der Notiz "nicht vermessen" durch

⚠️ Die Monotonie ist die Bedingung, an der der Schnittabstand am 31.08.
gescheitert ist (+1,27 / +1,59 / ...) - und ich hatte ihn trotzdem
registriert. Sie steht hier, damit das nicht noch einmal passiert.

    python rechne_turnover_beitrag.py --horizont 2
"""
import statistics as st
import sys

import numpy as np

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import messe_bewertungskennzahl as MB
import messe_eigenschaft_beitrag as B
import messe_kandidaten_als_regel as K

import argparse as _ap
_a = _ap.ArgumentParser()
_a.add_argument("--horizont", type=int, default=20)
# ⚠️⚠️ WELCHE UMSCHLAGGROESSE (21.09.2026, Befund 2.512).
# Vorgabe bleibt `gesamt` - das ist die registrierte und live
# laufende Groesse, und jeder alte Aufruf muss dasselbe liefern
# wie vorher (R-R11).
_a.add_argument("--umschlag",
                choices=("gesamt", "frei", "naeherung"),
                default="gesamt")
_p = _a.parse_known_args()[0]
HOR, UMSCHLAG = _p.horizont, _p.umschlag
CRV = 2.0
print("HORIZONT H%d   GROESSE `umschlag_%s`" % (HOR, UMSCHLAG))

reihen = B.lade()
if UMSCHLAG == "naeherung":
    # ⚠️⚠️ DIE NAEHERUNG (2.417-naeherung, gemessen 21.09.):
    # heutige Menge rueckwaerts konstant. Loest Abdeckung UND
    # Fensterlaenge - damit ist H20 ueberhaupt erst rechenbar.
    # ⚠️ Ausschluesse aus dem Messwerkzeug uebernommen, nicht
    # neu gesetzt: Mengendrift > 6,53 (= Breite eines Fuenftels) und
    # Preissprung > 5 (Umstellungen, `pruefe_datenqualitaet`).
    import phase4_c_naeherung_konstante_menge as _NK
    _h, _raus = _NK.mengen_heute()
    _umst = _NK.umstellungen(reihen)
    menge = {}
    for _s, _m in _h.items():
        if _s in _umst:
            continue
        _z = reihen.get(_s)
        if _z:
            menge[_s] = {str(_x[0])[:10]: _m for _x in _z}
    print("  Quelle: NAEHERUNG · %d Symbole · %d Driftausschluesse · "
          "%d Umstellungen" % (len(menge), len(_raus), len(_umst)))
elif UMSCHLAG == "frei":
    # ⚠️ DIESELBE Aufbereitung wie in der Kalibrierung, nicht
    # eine zweite: `menge_neu` wirft die Tagesartefakte der Quelle
    # aus (2.502-mengenspitzen). Wer hier roh laedt, rechnet eine
    # andere Tabelle als die, die gemessen wurde.
    import phase4_c_kalibrierung_freefloat as _KF
    menge, _weg, _ges = _KF.menge_neu(_KF.MENGE_DB, True)
    print("  Quelle: %s · %d Symbole · %d von %d Punkten ausgeworfen"
          % (_KF.MENGE_DB, len(menge), _weg, _ges))
else:
    menge = MB.reihe("data/onchain_historie.db", "splycur")
    print("  Quelle: data/onchain_historie.db · %d Symbole"
          % len(menge))
je_tag = K.baue(reihen, "turnover", menge, horizont=HOR)

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
werte = [st.mean(sammel[k]) for k in range(5)]
mittel = st.mean(werte)

print("=" * 74)
print("G-2' — die BEITRAGSTABELLE fuer Turnover")
print("=" * 74)
print("%d Kalendertage, Horizont %d, CRV %.1f"
      % (sum(1 for z in je_tag.values() if len(z) >= 15), HOR, CRV))
print()
print("  Fuenftel  Bewegung   gegen Mittel   Punkte roh   Punkte GESCHRUMPFT")
faktor = 1.0 / (1.0 + CRV)
stufen = []
for k in range(5):
    ab = werte[k] - mittel
    roh = 100.0 * ab * faktor
    stufen.append(round(roh / 2.0, 2))
    print("     %d     %+.4f R    %+.4f R      %+5.2f       %+5.2f"
          % (k, werte[k], ab, roh, roh / 2.0))
print()
# ---- ⚠️⚠️⚠️ DIE VORABFESTLEGUNG VOM 01.09.2026, HIER GEPRUEFT
#
#   "nutzbar = die Stufen sind MONOTON ueber die Fuenftel und die
#    Spanne ist groesser als null; nicht nutzbar = sonst."
#
# ⚠️ Sie steht seit dem 01.09. im Modulkopf und wurde bis
# zum 21.09.2026 NIE GERECHNET - man musste die Zahlen von Hand
# ansehen. Genau daran ist der Schnittabstand am 31.08. gescheitert:
# die Bedingung stand da, und ich habe ihn trotzdem registriert.
_fallend = all(stufen[i] >= stufen[i + 1] for i in range(4))
_steigend = all(stufen[i] <= stufen[i + 1] for i in range(4))
_spanne = abs(stufen[0] - stufen[4])
print()
print("=" * 74)
print("  VORABFESTLEGUNG (01.09.2026): monoton UND Spanne > 0")
print("=" * 74)
print("  Stufen        %s" % (tuple(stufen),))
print("  monoton       %s"
      % ("JA, fallend" if _fallend else
         "JA, steigend" if _steigend else
         "⚠️ NEIN - Zickzack"))
print("  Spanne        %.2f Punkte" % _spanne)
_nutzbar = (_fallend or _steigend) and _spanne > 0
print()
print("  ==> %s"
      % ("✔✔ NUTZBAR - die Tabelle erfuellt die Vorabfestlegung"
         if _nutzbar else
         "⚠️ NICHT NUTZBAR - die Zelle bekommt KEINEN Beitrag "
         "und laeuft mit der Notiz 'nicht vermessen' durch"))
print()
print("  ⚠️ Eine monotone Tabelle ist noch kein TRAEGT. Ob die Groesse "
      "auf diesem Horizont ueberhaupt WIRKT, beantwortet")
print("     `phase4_c_kalibrierung_freefloat`, nicht diese Rechnung -"
      " sie setzt die Wirkung voraus")
print("     und verteilt sie auf Stufen.")

print()
print("  Spanne unterstes gegen oberstes Fuenftel: %+.2f Punkte roh, %+.2f geschrumpft"
      % (100 * (werte[0] - werte[4]) * faktor,
         100 * (werte[0] - werte[4]) * faktor / 2))
print()
print("  Fuer `wahrscheinlichkeit.BEITRAEGE`:")
print("    stufen=(%s)," % ", ".join("%+.2f" % s for s in stufen))
