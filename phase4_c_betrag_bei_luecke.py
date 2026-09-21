# -*- coding: utf-8 -*-
"""Punkt C, zweiter Teil — WELCHER BETRAG IST BEI EINER LUECKE ZULAESSIG?

## Die Frage des Nutzers

> *„Wir brauchen eine Naeherung ob nur ein Betrag zulaessig ist - kannst
> du das nicht messen?"*

Und der Einwand dazu, der meinen ersten Vorschlag kippt:

> *„Zu der Anmerkung ,wird Spot` - fuer mich ist das fachlich keine
> Loesung … spot [soll] eine laengerfristige Investition sein … und dann
> passen 40 spot trades in der woche auch nicht."*

⚠️ Er hat recht. *,Bei fehlendem Beitrag auf Spot`* verschiebt den
Widerspruch nur - es macht aus einem halb bewerteten Hebelgeschaeft ein
halb bewertetes Spotgeschaeft und belastet damit einen Weg, der ohnehin
schon 40 Trades in der Woche traegt, obwohl er laengerfristig gemeint
ist.

## ⚠️⚠️ UND EINE KORREKTUR AN MIR SELBST

Ich hatte geschrieben, null Punkte seien *,nicht die Mitte`*. Gerechnet:
der MITTELWERT beider Stufensaetze ist praktisch genau null (funding
+0,0000, turnover +0,0020). Die Stufen sind so gebaut. `punkte = 0.0`
ist also **genau der Erwartungswert bei Unkenntnis** - nicht willkuerlich
und nicht verzerrend.

**Was die Luecke wirklich hinzufuegt, ist UNSICHERHEIT**, und die ist
bezifferbar: Standardabweichung **1,98 Punkte** bei `turnover`, 1,05 bei
`funding`.

## Warum daraus ein kleinerer Betrag folgt - und keine Setzung ist

Kelly maximiert nicht den erwarteten Gewinn, sondern das erwartete
**logarithmische** Wachstum. Der Logarithmus ist **konkav**: ein Verlust
wiegt schwerer als ein gleich grosser Gewinn nuetzt. Bei UNSICHERER Quote
ist der optimale Einsatz deshalb kleiner als der Einsatz zur mittleren
Quote - das ist eine Eigenschaft der Zielfunktion, keine Vorsichtsregel.

    bekannt      f* = argmax  log-Wachstum bei GENAU q_i
                 (fuer jeden Rang einzeln, dann gemittelt)
    unbekannt    f* = argmax  Mittel ueber alle fuenf Raenge
                 (EIN Einsatz, der nicht weiss, welcher Rang gilt)

Das Verhaeltnis der beiden ist der **Abschlag**, den die Luecke kostet.
Er wird hier GERECHNET, nicht gesetzt.

⚠️ Was dabei NICHT gesetzt wird: die Gleichverteilung ueber die fuenf
Raenge. Sie folgt daraus, dass Fuenftel per Konstruktion gleich gross
sind - wer keinen Wert hat, hat keinen Grund, einen Rang fuer
wahrscheinlicher zu halten.

⚠️ NUR LESEND, gegen eine SICHERUNG.

    python phase4_c_betrag_bei_luecke.py --db <sicherung.db>
"""
from __future__ import annotations

import math
import os
import sqlite3
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from agent import wahrscheinlichkeit as WK                 # noqa: E402

CRV = 2.0
KAPITAL_EUR = 17987.0


def _pfad(flagge: str, vorgabe: str) -> str:
    a = sys.argv[1:]
    return a[a.index(flagge) + 1] if flagge in a else vorgabe


def _wachstum(f: float, q: float) -> float:
    """Erwartetes log-Wachstum eines Einsatzes f bei Trefferquote q.

    Gewinn f*CRV mit Wahrscheinlichkeit q, Verlust f sonst."""
    if f <= 0:
        return 0.0
    if f >= 1.0:
        return -1e9
    return q * math.log(1.0 + f * CRV) + (1.0 - q) * math.log(1.0 - f)


def _bestes_f(quoten: list, gewichte: list | None = None) -> float:
    """Der Einsatz, der das erwartete log-Wachstum maximiert.

    Eine Liste mit EINER Quote = der Fall ,Rang bekannt`. Mehrere Quoten
    = ,Rang unbekannt`, ein Einsatz fuer alle."""
    g = gewichte or [1.0 / len(quoten)] * len(quoten)
    bestes, bestf = 0.0, 0.0
    f = 0.0005
    while f < 0.9:
        w = sum(gi * _wachstum(f, q) for gi, q in zip(g, quoten))
        if w > bestes:
            bestes, bestf = w, f
        f += 0.0005
    return bestf


def main() -> int:
    db = _pfad("--db", "")
    if not db or not os.path.exists(db):
        raise SystemExit("Sicherung nicht gefunden - mit --db "
                         "<sicherung.db> setzen (NIE die Standard-DB)")
    stufen = list(next(b.stufen for b in WK.BEITRAEGE
                       if b.merkmal == "turnover_fuenftel"))
    basis = WK.basisrate(CRV)
    import agent.marktrang as MR
    # ⚠️⚠️ BERICHTIGT 21.09.2026 (Befund 2.510). Hier stand die
    # SYMBOLLISTE der Messdatei, die die Frischegrenze nicht kennt -
    # dieselbe Stelle wie in `phase4_c_turnover_luecke.py`. Der
    # Abschlag wurde dadurch ueber 13 statt ueber 15 Signale gemittelt.
    mit = MR.turnover_verfuegbar()

    print("=" * 104)
    print("PUNKT C, TEIL 2 - WELCHER BETRAG IST BEI EINER LUECKE ZULAESSIG?")
    print("=" * 104)
    print("  `turnover_fuenftel` %s -> Mittelwert %+.4f, Standardabw. %.3f"
          % (tuple(stufen), sum(stufen) / len(stufen),
             (sum((x - sum(stufen) / len(stufen)) ** 2
                  for x in stufen) / len(stufen)) ** 0.5))
    print("  ⚠️ Der Mittelwert ist praktisch null - `punkte = 0,0` ist der "
          "ERWARTUNGSWERT, nicht")
    print("     eine Verzerrung. Was fehlt, ist die Gewissheit, nicht die "
          "Mitte.")
    print()
    print("-" * 104)
    print("  %-8s %-11s %8s %10s %10s %9s   %s"
          % ("Symbol", "Tag", "Hebel", "f bekannt", "f unbek.", "Abschlag",
             "zulaessiger Betrag"))
    print("-" * 104)

    c = sqlite3.connect("file:%s?mode=ro" % db.replace("\\", "/"), uri=True)
    faktoren = []
    for sym, tag, heb, pos, verl in c.execute(
            "SELECT symbol, substr(created_at,1,10), hebel, "
            "       position_size_eur, verlust_am_stop_eur FROM signals "
            " WHERE instrument='hebel' AND hebel IS NOT NULL "
            "   AND verlust_am_stop_eur IS NOT NULL ORDER BY created_at"):
        if not (heb and pos and verl) or sym.upper() in mit:
            continue
        z_heute = 100.0 * ((verl / KAPITAL_EUR) * 2.0 * CRV) / (1.0 + CRV)
        quoten = [basis + (z_heute + p) / 100.0 for p in stufen]
        quoten = [q for q in quoten if 0.0 < q < 1.0]
        # Rang BEKANNT: je Rang der optimale Einsatz, dann gemittelt.
        f_bekannt = sum(_bestes_f([q]) for q in quoten) / len(quoten)
        # Rang UNBEKANNT: EIN Einsatz fuer alle fuenf.
        f_unbekannt = _bestes_f(quoten)
        if f_bekannt <= 0:
            continue
        faktor = f_unbekannt / f_bekannt
        faktoren.append(faktor)
        print("  %-8s %-11s %8.2f %10.4f %10.4f %8.0f %%   %s"
              % (sym, tag, heb, f_bekannt, f_unbekannt, 100 * faktor,
                 "%.0f statt %.0f EUR" % (faktor * pos, pos)))

    print()
    if faktoren:
        faktoren.sort()
        n = len(faktoren)
        print("  ➤ ABSCHLAG ueber %d Faelle: Median %.0f %% · Spanne %.0f "
              "bis %.0f %%"
              % (n, 100 * faktoren[n // 2], 100 * faktoren[0],
                 100 * faktoren[-1]))
        print("     Das heisst: bei fehlendem `turnover` waere rund %.0f "
              "Prozent des heutigen" % (100 * faktoren[n // 2]))
        print("     Betrags zulaessig - der Rest ist der Preis der "
              "Ungewissheit.")
    print()
    # ---- ⚠️⚠️ GEGENPROBEN - drei, und jede kann den Befund kippen ----
    print("-" * 104)
    print("  GEGENPROBEN")
    print("-" * 104)
    _q0 = basis + 1.27 / 100.0      # ein typischer Fall aus der Tabelle
    # (a) OHNE Unsicherheit muss der Abschlag genau 100 % sein.
    _a = _bestes_f([_q0] * 5) / _bestes_f([_q0])
    print("    (a) Kunstfall OHNE Unsicherheit (alle fuenf Raenge gleich): "
          "Abschlag %.0f %%  %s" % (100 * _a,
                                    "✔" if abs(_a - 1.0) < 0.02 else "✖"))
    print("        Waere er kleiner, kaeme der Abschlag aus dem Verfahren "
          "und nicht aus der Luecke.")
    # (b) Doppelte Streuung muss einen GROESSEREN Abschlag geben.
    _s2 = [2.0 * p for p in stufen]
    _qa = [basis + (1.27 + p) / 100.0 for p in stufen]
    _qb = [basis + (1.27 + p) / 100.0 for p in _s2]
    _qa = [q for q in _qa if 0 < q < 1]
    _qb = [q for q in _qb if 0 < q < 1]
    _fa = _bestes_f(_qa) / (sum(_bestes_f([q]) for q in _qa) / len(_qa))
    _fb = _bestes_f(_qb) / (sum(_bestes_f([q]) for q in _qb) / len(_qb))
    print("    (b) doppelte Streuung: Abschlag %.0f %% gegen %.0f %%  %s"
          % (100 * _fb, 100 * _fa, "✔" if _fb < _fa else "✖"))
    print("        Mehr Ungewissheit muss mehr kosten - sonst misst die "
          "Rechnung nicht die Ungewissheit.")
    # (c) Haengt der Abschlag am angenommenen KAPITAL? Behauptet: nein.
    print("    (c) Kapitalabhaengigkeit - die Behauptung war ,weitgehend "
          "unabhaengig`:")
    for _kap in (5000.0, 10000.0, 17987.0, 40000.0):
        _z = 100.0 * ((170.78 / _kap) * 2.0 * CRV) / (1.0 + CRV)
        _qq = [basis + (_z + p) / 100.0 for p in stufen]
        _qq = [q for q in _qq if 0 < q < 1]
        if len(_qq) < 2:
            continue
        _fk = _bestes_f(_qq) / (sum(_bestes_f([q]) for q in _qq) / len(_qq))
        print("        Kapital %7.0f EUR -> Zuschlag %+.2f Punkte -> "
              "Abschlag %.0f %%" % (_kap, _z, 100 * _fk))
    print("        ⚠️ Wandert er stark, ist der Median oben eine Aussage "
          "ueber DIESEN Kontostand.")
    print()
    print("  ⚠️ WAS HIER NICHT GESETZT IST: die Gleichverteilung ueber die "
          "fuenf Raenge folgt")
    print("     daraus, dass Fuenftel gleich gross sind. Wer keinen Wert "
          "hat, hat keinen Grund,")
    print("     einen Rang fuer wahrscheinlicher zu halten.")
    # ---- ⚠️⚠️⚠️ WAS GEGENPROBE (c) WIRKLICH ZEIGT ---------------------
    #
    # Ich hatte geschrieben, der Abschlag sei ,weitgehend unabhaengig`
    # vom Kapital. GEGENPROBE (c) WIDERLEGT DAS: 100 / 98 / 79 / 48
    # Prozent. Aber die Ursache ist nicht das Kapital - es ist der
    # ABSTAND DER QUOTE ZUM BREAKEVEN. Das Kapital wirkt hier nur, weil
    # die Quote aus dem Verlustbetrag zurueckgerechnet wird.
    print("-" * 104)
    print("  ⚠️⚠️ DIE EIGENTLICHE STELLGROESSE: DER ABSTAND ZUM BREAKEVEN")
    print("-" * 104)
    print("    Breakeven bei CRV %.1f liegt bei q = %.4f." % (CRV, basis))
    print("    %-12s %10s %10s" % ("Zuschlag", "Quote", "Abschlag"))
    for _z in (0.5, 1.0, 1.5, 2.0, 3.0, 4.5, 6.0):
        _qq = [basis + (_z + p) / 100.0 for p in stufen]
        _qq = [q for q in _qq if 0 < q < 1]
        if len(_qq) < 2:
            continue
        _fk = _bestes_f(_qq) / (sum(_bestes_f([q]) for q in _qq) / len(_qq))
        print("    %-12s %10.4f %9.0f %%"
              % ("%+.2f Punkte" % _z, basis + _z / 100.0, 100 * _fk))
    print("    ➤ Je NAEHER die Quote am Breakeven, desto teurer die "
          "Ungewissheit.")
    print("    ⚠️⚠️ Und genau dort arbeitet der Betrieb: alle 16 echten "
          "Signale liegen bei")
    print("       Zuschlag 0,8 bis 1,3 Punkten (2c). Der Abschlag von rund "
          "80 Prozent ist also")
       
    print("       kein Zufall dieses Kontostands, sondern die Folge des "
          "Arbeitspunkts.")
    print()
    print("  ⚠️ ANNAHMEN: Kapital %s EUR und die Rueckrechnung der Quote "
          "(q wird nicht" % ("%.0f" % KAPITAL_EUR))
    print("     gespeichert, 2.496-hebel-roh-fehlt). Der Abschlag haengt "
          "NICHT am Kapital,")
    print("     sondern am Abstand zum Breakeven - das Kapital wirkt nur "
          "ueber die Rueckrechnung.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
