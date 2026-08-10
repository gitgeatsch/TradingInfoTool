"""Selbsttest fuer bewerte_dynamisch.py - jede Pruefung mit Gegenkontrolle.

Konstruierte Faelle mit BEKANNTER Antwort. Ein Bewerter, der nur "plausible"
Zahlen liefert, ist nicht geprueft - genau daran ist am 09.08. der erste
Negativtest gescheitert (die vertauschten Zonen stimmten aus dem falschen
Grund zu).

    python teste_bewerte_dynamisch.py
"""
from __future__ import annotations

import sys

from bewerte_dynamisch import bewerte_mit_trailing, breakeven_trefferquote

_ok, _fehler = 0, []


def pruefe(name, bedingung, detail=""):
    global _ok
    if bedingung:
        _ok += 1
        print(f"  [ok]     {name}" + (f"   {detail}" if detail else ""))
    else:
        _fehler.append(name)
        print(f"  [FEHLER] {name}   {detail}")


class K:
    def __init__(self, high, low, close=None, open=None):
        self.high, self.low = high, low
        self.close = close if close is not None else (high + low) / 2
        self.open = open if open is not None else self.close


# LONG: entry 100, stop 90 (Risiko 10), Ziel 120 (CRV 2,0)
LONG = {"entry": 100.0, "stop": 90.0, "ziel": 120.0, "risiko": 10.0,
        "ist_short": False}
SHORT = {"entry": 100.0, "stop": 110.0, "ziel": 80.0, "risiko": 10.0,
         "ist_short": True}

print("A  Grundfaelle")

e = bewerte_mit_trailing(LONG, [K(121, 99)], horizont=14)
pruefe("A1 Ziel am ersten Tag", e.ausgang == "ziel" and abs(e.r - 2.0) < 1e-9,
       f"{e.ausgang} r={e.r:.2f}")

e = bewerte_mit_trailing(LONG, [K(101, 89)], horizont=14)
pruefe("A2 Stop am ersten Tag", e.ausgang == "stop" and abs(e.r + 1.0) < 1e-9,
       f"{e.ausgang} r={e.r:.2f}")

# GEGENKONTROLLE zu A1/A2: trifft ein Tag BEIDE Zonen, muss der Stop gewinnen.
e = bewerte_mit_trailing(LONG, [K(121, 89)], horizont=14)
pruefe("A2g Gegenkontrolle: beide Zonen am selben Tag -> STOP gewinnt",
       e.ausgang == "stop" and e.r < 0, f"{e.ausgang} r={e.r:.2f}")

e = bewerte_mit_trailing(LONG, [K(101, 99), K(102, 98)], horizont=14)
pruefe("A3 nichts erreicht -> zensiert", e.ausgang == "zensiert",
       f"{e.ausgang} r={e.r:.2f}")

print("\nB  Der Trailing-Stop - der eigentliche Zweck")

# Tag 1 laeuft auf 115 (MFE 1,5 R) -> Stop wird auf 100 + 10*(1,5-1,0) = 105
# nachgezogen, GILT AB TAG 2. Tag 2 faellt auf 104 -> Trailing greift, +0,5 R.
e = bewerte_mit_trailing(LONG, [K(115, 99), K(106, 104)], horizont=14)
pruefe("B1 Trailing greift und sichert Gewinn",
       e.ausgang == "trailing" and abs(e.r - 0.5) < 1e-9,
       f"{e.ausgang} r={e.r:.2f} stop={e.stop_am_ende:.1f}")

# GEGENKONTROLLE: derselbe Verlauf OHNE Trailing muss anders enden. Der Kurs
# faellt nach dem Hoch weiter - mit Trailing wird bei 105 gesichert, ohne ihn
# laeuft die Position bis zum Horizont und schliesst im Minus.
VERLAUF = [K(115, 99), K(106, 104), K(103, 96, close=97)]
e_mit = bewerte_mit_trailing(LONG, VERLAUF, horizont=14)
e_ohne = bewerte_mit_trailing(LONG, VERLAUF, horizont=14, ausloese_r=99.0)
pruefe("B1g Gegenkontrolle: ohne Trailing anderer Ausgang UND schlechteres R",
       e_ohne.ausgang != "trailing" and e_ohne.r < e_mit.r,
       f"mit {e_mit.ausgang} {e_mit.r:+.2f} gegen ohne {e_ohne.ausgang} "
       f"{e_ohne.r:+.2f}")

# Der Stop darf sich NIE verschlechtern. Damit der Trailing ueberhaupt zum Zug
# kommt, muss das Ziel WEIT genug weg sein - sonst greift es vorher (genau
# daran ist die erste Fassung dieses Tests gescheitert: Ziel 120 bei einem
# Tageshoch von 130).
WEIT = {"entry": 100.0, "stop": 90.0, "ziel": 200.0, "risiko": 10.0,
        "ist_short": False}
# Tag 1 auf 130 -> MFE 3,0 R -> Stop 120.  Tag 2 nur noch 122/121 -> das
# Tages-MFE waere 2,2 und ergaebe Stop 112; der Stop MUSS bei 120 bleiben.
# Tag 3 faellt auf 119: nur wenn der Stop NICHT zurueckgezogen wurde, greift er.
e = bewerte_mit_trailing(WEIT, [K(130, 99), K(122, 121), K(121, 119)], horizont=14)
pruefe("B2 Stop wird nie zurueckgezogen",
       e.ausgang == "trailing" and abs(e.stop_am_ende - 120.0) < 1e-9
       and abs(e.r - 2.0) < 1e-9,
       f"{e.ausgang} stop={e.stop_am_ende:.1f} r={e.r:.2f} Tag {e.tag}")
# GEGENKONTROLLE dazu: wuerde der Stop mitfallen, waere Tag 3 nicht getroffen.
# Mit abstand_r=3,0 liegt der Stop bei 100 und Tag 3 laeuft durch.
e2 = bewerte_mit_trailing(WEIT, [K(130, 99), K(122, 121), K(121, 119)],
                          horizont=14, abstand_r=3.0)
pruefe("B2g Gegenkontrolle: weiterer Trailing-Abstand -> Tag 3 laeuft durch",
       e2.ausgang != "trailing", f"{e2.ausgang} stop={e2.stop_am_ende:.1f}")

# KAUSALITAET: der am Tagesende gesetzte Stop darf denselben Tag nicht mehr
# treffen. Tag 1 laeuft von 99 auf 115 - der daraus folgende Stop 105 liegt
# UEBER dem Tagestief 99. Wuerde er ruecwirkend gelten, waere Tag 1 schon
# ausgestoppt.
e = bewerte_mit_trailing(LONG, [K(115, 99), K(116, 106)], horizont=14)
pruefe("B3 der heute gesetzte Stop trifft NICHT den heutigen Tag",
       e.ausgang != "trailing" or e.tag > 1, f"{e.ausgang} Tag {e.tag}")

print("\nC  SHORT spiegelbildlich")

e = bewerte_mit_trailing(SHORT, [K(101, 79)], horizont=14)
pruefe("C1 SHORT Ziel", e.ausgang == "ziel" and abs(e.r - 2.0) < 1e-9,
       f"{e.ausgang} r={e.r:.2f}")
e = bewerte_mit_trailing(SHORT, [K(111, 99)], horizont=14)
pruefe("C2 SHORT Stop", e.ausgang == "stop" and abs(e.r + 1.0) < 1e-9,
       f"{e.ausgang} r={e.r:.2f}")
# Tag 1 auf 85 (MFE 1,5 R) -> Stop auf 95, gilt ab Tag 2; Tag 2 auf 96.
e = bewerte_mit_trailing(SHORT, [K(101, 85), K(96, 94)], horizont=14)
pruefe("C3 SHORT Trailing sichert Gewinn",
       e.ausgang == "trailing" and abs(e.r - 0.5) < 1e-9,
       f"{e.ausgang} r={e.r:.2f} stop={e.stop_am_ende:.1f}")

print("\nD  Kappung")

lang = [K(101, 99)] * 10
e = bewerte_mit_trailing(LONG, lang, horizont=14, kappung_tage=3)
pruefe("D1 Kappung beendet frueher", e.ausgang == "gekappt" and e.tag == 3,
       f"{e.ausgang} Tag {e.tag}")
e = bewerte_mit_trailing(LONG, lang, horizont=14)
pruefe("D1g Gegenkontrolle: ohne Kappung laeuft es weiter",
       e.ausgang == "zensiert" and e.tag == 10, f"{e.ausgang} Tag {e.tag}")

print("\nE  Robustheit")

pruefe("E1 kaputte Zonen liefern None (kein Ersatzwert)",
       bewerte_mit_trailing({"entry": 0, "stop": 1, "ziel": 2, "risiko": 1},
                            [K(1, 1)]) is None)
pruefe("E2 negatives Risiko liefert None",
       bewerte_mit_trailing({**LONG, "risiko": -5}, [K(1, 1)]) is None)

print("\nF  Breakeven-Latte")
pruefe("F1 CRV 2,0 -> 33,3 %", abs(breakeven_trefferquote(2.0) - 1 / 3) < 1e-9)
pruefe("F2 CRV 3,0 -> 25,0 %", abs(breakeven_trefferquote(3.0) - 0.25) < 1e-9)
pruefe("F2g Gegenkontrolle: CRV 1,0 -> 50 %, NICHT immer 33 %",
       abs(breakeven_trefferquote(1.0) - 0.5) < 1e-9,
       f"{breakeven_trefferquote(1.0):.3f}")

print("\n" + "=" * 66)
print(f"{_ok} Pruefungen bestanden, {len(_fehler)} fehlgeschlagen")
for f in _fehler:
    print(f"   FEHLER: {f}")
sys.exit(1 if _fehler else 0)
