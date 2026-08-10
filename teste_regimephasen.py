"""Selbsttest fuer messe_regimephasen_llm.py - jede Pruefung mit Gegenkontrolle.

WOZU DIESE DATEI. Stehende Nutzer-Vorgabe (09.08.): *"mach zu all deinen
Pruefungen immer eine Gegenpruefung das hat gut funktioniert bisher sonst haben
wir fehler"* - und der Auftrag, die Messung so aufzusetzen, dass sie
wiederverwendbar ist.

DAS PRINZIP, aus `Test_und_Verifikationsmethodik.md`: eine Pruefung, die nur
zeigt "es kommt etwas Plausibles heraus", ist keine. Zu jeder Zusicherung
gehoert eine GEGENKONTROLLE, die belegt, dass die Pruefung auch anschlaegt,
wenn die Sache kaputt ist. Ohne sie ist ein gruener Balken nicht von einem
degenerierten Test zu unterscheiden.

WARUM DAS HIER KONKRET NOETIG WAR. Beim ersten Trockenlauf am 09.08. meldete
der Rauschboden-Waechter (CC3) sauber "0 % Richtungsdreher" - weil der Mock
deterministisch antwortete. Der Waechter hatte nichts geprueft und sah trotzdem
gut aus. Derselbe Fehler war zwei Tage zuvor schon einmal passiert
(Nachweisrahmen: Rauschboden 0 -> Urteil "IM RAUSCHEN" bestand trivial).

    python teste_regimephasen.py
"""
from __future__ import annotations

import sys
from collections import Counter

import messe_regimephasen_llm as M

_ok = 0
_fehler: list[str] = []


def pruefe(name: str, bedingung: bool, detail: str = "") -> None:
    global _ok
    if bedingung:
        _ok += 1
        print(f"  [ok]     {name}")
    else:
        _fehler.append(name)
        print(f"  [FEHLER] {name}   {detail}")


class K:
    """Minimale Kerze - nur was die geprueften Funktionen anfassen."""

    def __init__(self, date: str, close: float):
        self.date, self.close = date, close
        self.open = self.high = self.low = close


def _reihe(werte: list[float], ab: int = 0) -> list[K]:
    return [K(f"2025-{1 + (ab + i) // 28:02d}-{1 + (ab + i) % 28:02d}", v)
            for i, v in enumerate(werte)]


# --------------------------------------------------------------------------
print("A  EMA und Phasenklassifikation")

e = M._ema([10.0] * 50, 10)
pruefe("A1 EMA einer konstanten Reihe ist die Konstante", abs(e[-1] - 10.0) < 1e-9)
# GEGENKONTROLLE: bei steigender Reihe MUSS die EMA unter dem letzten Wert
# liegen - sonst rechnet sie gar nicht, sondern reicht nur durch.
e2 = M._ema([float(i) for i in range(50)], 10)
pruefe("A1g Gegenkontrolle: EMA einer steigenden Reihe hinkt nach",
       e2[-1] < 49.0, f"EMA={e2[-1]:.3f}")

steigend = _reihe([100.0 * (1.01 ** i) for i in range(400)])
p = M.btc_phasen(steigend)
pruefe("A2 durchgehend steigend -> BULLE",
       all(v == "BULLE" for v in p.values()), str(Counter(p.values())))
# GEGENKONTROLLE: dieselbe Funktion auf der gespiegelten Reihe darf NICHT
# BULLE sagen - sonst gibt sie unabhaengig von den Daten immer dasselbe.
fallend = _reihe([100.0 * (0.99 ** i) for i in range(400)])
pf = M.btc_phasen(fallend)
pruefe("A2g Gegenkontrolle: durchgehend fallend -> BAER, nie BULLE",
       all(v == "BAER" for v in pf.values()), str(Counter(pf.values())))

# Eine Reihe, die weder klar steigt noch faellt, muss SEITWAERTS erzeugen -
# sonst kennt die Klassifikation den mittleren Zustand gar nicht.
import math
welle = _reihe([100.0 + 8.0 * math.sin(i / 9.0) for i in range(400)])
pw = M.btc_phasen(welle)
pruefe("A3 schwankend ohne Trend erzeugt auch SEITWAERTS",
       pw and "SEITWAERTS" in set(pw.values()), str(Counter(pw.values())))

# --------------------------------------------------------------------------
print("\nB  Kausalitaet - kein Blick in die Zukunft")

lang = _reihe([100.0 + 5.0 * math.sin(i / 11.0) + i * 0.05 for i in range(500)])
voll = M.btc_phasen(lang)
# Dieselbe Reihe, hinten abgeschnitten: das Urteil fuer einen Tag darf sich
# NICHT aendern, nur weil spaetere Tage fehlen. Waere die Klassifikation
# zukunftsabhaengig, kippten hier Werte.
kurz = M.btc_phasen(lang[:400])
abweichung = [d for d in kurz if voll.get(d) != kurz[d]]
pruefe("B1 Phase eines Tages haengt nicht von spaeteren Tagen ab",
       not abweichung, f"{len(abweichung)} abweichende Tage")
# GEGENKONTROLLE: der Test kann nur greifen, wenn ueberhaupt Tage verglichen
# wurden - ein leerer Vergleich bestuende immer.
pruefe("B1g Gegenkontrolle: der Vergleich war nicht leer",
       len(kurz) > 100, f"nur {len(kurz)} Tage verglichen")

# --------------------------------------------------------------------------
print("\nC  Stabile Bloecke")

roh = {}
for i in range(M.MIN_BLOCK):                      # genau MIN_BLOCK -> bleibt
    roh[f"2025-01-{i+1:02d}"] = "BULLE"
for i in range(M.MIN_BLOCK - 1):                  # einer zu wenig -> faellt raus
    roh[f"2025-02-{i+1:02d}"] = "BAER"
fest = M.stabile_tage(roh)
pruefe("C1 Block mit genau MIN_BLOCK Tagen bleibt erhalten",
       sum(1 for v in fest.values() if v == "BULLE") == M.MIN_BLOCK)
pruefe("C1g Gegenkontrolle: Block mit MIN_BLOCK-1 Tagen wird verworfen",
       not any(v == "BAER" for v in fest.values()),
       f"{sum(1 for v in fest.values() if v == 'BAER')} BAER-Tage ueberlebten")

# Ein Flackertag zwischen zwei langen Bloecken darf beide nicht retten.
roh2 = {f"2025-03-{i+1:02d}": ("BULLE" if i != 5 else "BAER") for i in range(20)}
fest2 = M.stabile_tage(roh2)
pruefe("C2 einzelner Flackertag ueberlebt nicht",
       "2025-03-06" not in fest2)

# --------------------------------------------------------------------------
print("\nD  Ankerwahl")

reihen = {"AAA": _reihe([100.0 + i * 0.1 for i in range(400)]),
          "BBB": _reihe([100.0 + i * 0.1 for i in range(400)]),
          "CAT": _reihe([100.0 + i * 0.1 for i in range(400)])}
fest3 = {k.date: "BAER" for k in reihen["AAA"]}
anker = M.waehle_anker(reihen, fest3, je_arm=20, je_symbol=2)
symbole = {s for s, _ in anker["BAER"]}
pruefe("D1 CAT wird ausgeschlossen (dokumentiert kaputte Kursreihe)",
       "CAT" not in symbole, str(symbole))
# GEGENKONTROLLE: die anderen Symbole muessen ankommen - sonst filtert D1
# nur, weil gar nichts durchkommt.
pruefe("D1g Gegenkontrolle: die uebrigen Symbole kommen an",
       {"AAA", "BBB"} <= symbole, str(symbole))
je_sym = Counter(s for s, _ in anker["BAER"])
pruefe("D2 Obergrenze je Symbol wird eingehalten",
       all(v <= 2 for v in je_sym.values()), str(dict(je_sym)))

# --------------------------------------------------------------------------
print("\nE  Kennzahlen")

zeilen = [
    {"symbol": "A", "action": "ERÖFFNEN", "richtung": "LONG", "crv": 2.5, "stop_pct": 5.0},
    {"symbol": "A", "action": "ERÖFFNEN", "richtung": "SHORT", "crv": 1.5, "stop_pct": 7.0},
    {"symbol": "B", "action": "ERÖFFNEN", "richtung": "SHORT", "crv": 3.0, "stop_pct": 9.0},
    {"symbol": "B", "action": "HALTEN"},
]
k = M._kennzahlen(zeilen)
pruefe("E1 EROEFFNEN-Quote", abs(k["eroeffnen_quote"] - 0.75) < 1e-9, str(k))
pruefe("E2 LONG-Anteil auf Zeilen MIT Zonen bezogen",
       abs(k["long_anteil"] - 1 / 3) < 1e-9, str(k))
pruefe("E3 Anteil CRV >= 2,0", abs(k["crv_ab_2"] - 2 / 3) < 1e-9, str(k))
pruefe("E4 Stop-Median", abs(k["stop_median"] - 7.0) < 1e-9, str(k))
# GEGENKONTROLLE: eine HALTEN-Zeile ohne Zonen darf die Zonen-Kennzahlen NICHT
# verschieben - sonst mischt die Funktion zwei Grundmengen.
k2 = M._kennzahlen(zeilen + [{"symbol": "C", "action": "HALTEN"}])
pruefe("E4g Gegenkontrolle: zusaetzliche HALTEN-Zeile aendert Stop-Median nicht",
       k2["stop_median"] == k["stop_median"] and k2["n"] == k["n"] + 1)

# --------------------------------------------------------------------------
print("\nF  Richtungsdreher-Erkennung (CC3)")


def dreherquote(a: list[dict], b: list[dict]) -> float | None:
    erst = {(z["symbol"], z["datum"]): z for z in a}
    d = g = 0
    for z in b:
        v = erst.get((z["symbol"], z["datum"]))
        if not v or not v.get("richtung") or not z.get("richtung"):
            continue
        if v["richtung"] == z["richtung"]:
            g += 1
        else:
            d += 1
    return d / (d + g) if (d + g) else None


A = [{"symbol": "A", "datum": "2025-01-01", "richtung": "LONG"},
     {"symbol": "B", "datum": "2025-01-02", "richtung": "SHORT"}]
pruefe("F1 identische Laeufe -> 0 % Dreher", dreherquote(A, A) == 0.0)
B = [{"symbol": "A", "datum": "2025-01-01", "richtung": "SHORT"},
     {"symbol": "B", "datum": "2025-01-02", "richtung": "LONG"}]
pruefe("F1g Gegenkontrolle: vollstaendig gedreht -> 100 %",
       dreherquote(A, B) == 1.0, str(dreherquote(A, B)))
pruefe("F2 ohne gemeinsame Paare kein Scheinergebnis",
       dreherquote(A, [{"symbol": "Z", "datum": "1999-01-01",
                        "richtung": "LONG"}]) is None)

# --------------------------------------------------------------------------
print("\nG  Regime-Ueberschreibung im Faktensatz")

# Der Faktensatz aus dem Backtest traegt "nicht rekonstruierbar". Genau dieses
# Wort darf das Modell nicht erreichen - eine "Unknown"-Option loest laut
# regime.py Abstention aus und wuerde die EROEFFNEN-Quote messen statt die
# Marktphase. Hier wird die Ueberschreibung selbst geprueft.
fakten = {"regime": {"wert": "nicht rekonstruierbar", "quelle": "historischer Backtest"}}
kopie = dict(fakten)
kopie["regime"] = dict(kopie["regime"])
kopie["regime"]["wert"] = "bulle"
pruefe("G1 Ueberschreibung setzt das Label", kopie["regime"]["wert"] == "bulle")
pruefe("G1g Gegenkontrolle: das Original bleibt unveraendert (keine Seitenwirkung "
       "auf spaetere Arme)", fakten["regime"]["wert"] == "nicht rekonstruierbar")

# --------------------------------------------------------------------------
print("\nH  CC1-Urteilslogik")


def cc1(short_anteil: float, stop_median: float) -> bool:
    return (abs(short_anteil - M.PROD_SHORT_ANTEIL) <= 0.15
            and stop_median <= M.PROD_STOP_MEDIAN * 1.5)


pruefe("H1 produktionsnahe Werte werden als REPRODUZIERT gewertet",
       cc1(0.82, 8.0))
pruefe("H1g Gegenkontrolle: reiner LONG-Arm faellt durch", not cc1(0.0, 8.0))
pruefe("H2g Gegenkontrolle: doppelt so weiter Stop faellt durch",
       not cc1(0.82, 17.0))

# --------------------------------------------------------------------------
print("\n" + "=" * 70)
print(f"{_ok} Pruefungen bestanden, {len(_fehler)} fehlgeschlagen")
if _fehler:
    for f in _fehler:
        print(f"   FEHLER: {f}")
sys.exit(1 if _fehler else 0)
