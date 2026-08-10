"""Selbsttest fuer die Veto-Musterzaehlung - mit Gegenkontrollen.

DER FALL (10.08., an echten Exportdaten). Punkt 6 des Kennzahlen-Katalogs
verlangt, "insbesondere NEUE oder sich haeufende Muster" zu erkennen
(Test_und_Verifikationsmethodik 2.1). Gezaehlt wurde aber nach dem EXAKTEN
Text - und weil die Pipelines ihre Gruende mit eingesetzten Werten bauen,
zerfiel ein Grund in beliebig viele Toepfe:

    15 x "CRV 1.0 unter Minimum 2.0 (unveraendert ggue. Spot)"
     9 x "CRV 1.0000000000000018 unter Minimum 2.0 (unveraendert ggue. Spot)"
     7 x "CRV 1.4 unter Minimum 2.0 (unveraendert ggue. Spot)"

Die Anzeige sortiert nach Haeufigkeit und schneidet ab. Der GROESSTE Grund
kann dadurch vollstaendig unsichtbar bleiben, weil er sich auf zwanzig kleine
Zeilen verteilt - das Gegenteil dessen, wofuer der Punkt gedacht ist.

    python teste_veto_muster.py
"""
from __future__ import annotations

import sys

from extract_notebook_diagnose import (haeufigkeit, haeufigkeit_nach_muster,
                                       veto_muster)

_ok, _fehler = 0, []


def pruefe(name, bedingung, detail=""):
    global _ok
    if bedingung:
        _ok += 1
        print(f"  [ok]     {name}" + (f"   {detail}" if detail else ""))
    else:
        _fehler.append(name)
        print(f"  [FEHLER] {name}   {detail}")


print("A  Zahlen werden zusammengefasst")

CRV = "CRV {} unter Minimum 2.0 (unveraendert ggue. Spot)"
pruefe("A1 zwei CRV-Werte ergeben DASSELBE Muster",
       veto_muster(CRV.format("1.0")) == veto_muster(CRV.format("1.4")),
       veto_muster(CRV.format("1.0")))
pruefe("A2 auch der Fliesskomma-Ausreisser landet dort",
       veto_muster(CRV.format("1.0000000000000018"))
       == veto_muster(CRV.format("1.0")))
pruefe("A3 wissenschaftliche Notation ebenso",
       veto_muster(CRV.format("1.2e-05")) == veto_muster(CRV.format("1.0")),
       veto_muster(CRV.format("1.2e-05")))
pruefe("A4 Komma-Dezimaltrennung ebenso",
       veto_muster(CRV.format("1,4")) == veto_muster(CRV.format("1.0")))

print("\nB  Symbole werden zusammengefasst - aber nur das EIGENE")

pruefe("B1 das Symbol der Zeile wird ersetzt",
       veto_muster("3QSS ist nicht bei Bitpanda gelistet", "3QSS")
       == veto_muster("VVMX ist nicht bei Bitpanda gelistet", "VVMX"),
       veto_muster("3QSS ist nicht bei Bitpanda gelistet", "3QSS"))
pruefe("B2 ein Symbol MIT Ziffer bleibt heil (Symbol vor Zahlen ersetzt)",
       veto_muster("OD7H ist nicht gelistet", "OD7H") == "<symbol> ist nicht gelistet",
       veto_muster("OD7H ist nicht gelistet", "OD7H"))
# GEGENKONTROLLE: ohne Wortgrenze wuerde "CAT" mitten in "CATUSDT" treffen und
# aus zwei verschiedenen Gruenden faelschlich einen machen.
pruefe("B2g Gegenkontrolle: Teilwoerter werden NICHT ersetzt",
       veto_muster("CATUSDT ohne Daten", "CAT") == "CATUSDT ohne Daten",
       veto_muster("CATUSDT ohne Daten", "CAT"))
pruefe("B3g Gegenkontrolle: ohne Symbolangabe bleibt der Text bis auf Zahlen gleich",
       veto_muster("3QSS ist nicht gelistet") == "<zahl>QSS ist nicht gelistet",
       veto_muster("3QSS ist nicht gelistet"))

print("\nC  Verschiedene Gruende bleiben getrennt")

# DAS IST DIE WICHTIGSTE GEGENKONTROLLE. Eine Zusammenfassung, die ALLES
# zusammenwirft, waere schlimmer als die Zersplitterung - sie wuerde echte,
# verschiedene Probleme als ein einziges anzeigen.
pruefe("C1g Gegenkontrolle: CRV-Veto und Nur-Long-Veto bleiben zwei Muster",
       veto_muster(CRV.format("1.0"))
       != veto_muster('"Nur Long"-Einstellung aktiv, LLM empfahl SHORT'))
pruefe("C2g Gegenkontrolle: verschiedene Texte mit gleichen Zahlen bleiben getrennt",
       veto_muster("Historie veraltet: 5 Tage")
       != veto_muster("Preis veraltet: 5 Tage"))
pruefe("C3g Gegenkontrolle: ein Text OHNE Zahlen bleibt unveraendert",
       veto_muster("Preis veraltet oder nicht vorhanden")
       == "Preis veraltet oder nicht vorhanden")

print("\nD  Randfaelle")

pruefe("D1 None bleibt None", veto_muster(None) is None)
pruefe("D2 leerer Text bleibt leer", veto_muster("") == "")
pruefe("D3 'CRV None unter Minimum' - 'None' ist keine Zahl und bleibt stehen",
       "None" in veto_muster(CRV.format("None")),
       veto_muster(CRV.format("None")))

print("\nE  Die Zaehlung ueber Zeilen")

zeilen = [
    {"symbol": "AAA", "risk_veto_reason": CRV.format("1.0")},
    {"symbol": "BBB", "risk_veto_reason": CRV.format("1.4")},
    {"symbol": "CCC", "risk_veto_reason": CRV.format("1.6666666666666667")},
    {"symbol": "DDD", "risk_veto_reason": '"Nur Long"-Einstellung aktiv'},
    {"symbol": "EEE", "risk_veto_reason": None},
]
roh = haeufigkeit(zeilen, "risk_veto_reason")
muster = haeufigkeit_nach_muster(zeilen, "risk_veto_reason")
pruefe("E1 roh zerfaellt in 4 Toepfe", len(roh) == 4, str(len(roh)))
pruefe("E2 nach Muster bleiben 2", len(muster) == 2, str(list(muster)))
pruefe("E3 und der groesste Grund ist jetzt SICHTBAR (3 statt 1)",
       max(muster.values()) == 3 and max(roh.values()) == 1,
       f"Muster {max(muster.values())}, roh {max(roh.values())}")
pruefe("E4g Gegenkontrolle: die Gesamtzahl bleibt gleich - nichts geht verloren "
       "und nichts wird doppelt gezaehlt",
       sum(muster.values()) == sum(roh.values()) == 4,
       f"{sum(muster.values())} vs {sum(roh.values())}")

print("\n" + "=" * 70)
print(f"{_ok} Pruefungen bestanden, {len(_fehler)} fehlgeschlagen")
for f in _fehler:
    print(f"   FEHLER: {f}")
sys.exit(1 if _fehler else 0)
