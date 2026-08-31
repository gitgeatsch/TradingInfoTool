# -*- coding: utf-8 -*-
"""Pruefung fuer agent/marktrang.py (30.08.2026, G-2' Schritt 1).

Prueft die BAUFORM, nicht den Befund - der steht in `Befundkarte.md` 3.9.
Drei Dinge, die schiefgehen koennen und im Betrieb still blieben:

  1 ein fehlender Wert sieht aus wie ein geprueftes Nein
  2 ein zu duenner Querschnitt liefert trotzdem Fuenftel
  3 die Mailzeile wird zur Empfehlung statt zur Tatsache
"""
import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from agent import marktrang as MR

fehl = 0


def pruefe(name, bedingung, hinweis=""):
    global fehl
    print("  %-58s %s" % (name, "OK" if bedingung else "FEHL"))
    if not bedingung:
        fehl += 1
        if hinweis:
            print("      -> %s" % hinweis)


print("### 1. Rangbildung ###")
r = MR._rang({"A": 1.0, "B": 2.0, "C": 3.0})
pruefe("niedrigster Wert bekommt Rang 0.0", r["A"] == 0.0)
pruefe("hoechster Wert bekommt Rang 1.0", r["C"] == 1.0)
pruefe("mittlerer Wert dazwischen", 0 < r["B"] < 1)
pruefe("ein einzelner Wert ergibt KEINEN Rang", MR._rang({"A": 1.0}) == {},
       "ein Rang aus einem Wert waere erfunden")

print()
print("### 2. Fuenftel ###")
pruefe("None bleibt None, wird NICHT 0", MR._fuenftel(None) is None,
       "ein unbekanntes Merkmal darf nie aussehen wie ein geprueftes")
pruefe("0.0 -> Fuenftel 0", MR._fuenftel(0.0) == 0)
pruefe("1.0 -> Fuenftel 4 (nicht 5)", MR._fuenftel(1.0) == 4)
pruefe("0.79 -> Fuenftel 3", MR._fuenftel(0.79) == 3)
pruefe("0.80 -> Fuenftel 4", MR._fuenftel(0.80) == 4)

print()
print("### 3. Mindestquerschnitt ###")
pruefe("gesetzt und mindestens 15", MR.MINDEST_QUERSCHNITT >= 15,
       "bei 10 Werten enthaelt ein Fuenftel zwei - das waere Zufall")

print()
print("### 4. Verhalten ohne Netz - der haeufigste Betriebsfall ###")
echt = MR.funding_werte
MR.funding_werte = lambda *a, **k: (_ for _ in ()).throw(OSError("kein Netz"))
try:
    e = MR.raenge(["BTC", "ETH"], mit_turnover=False)
    pruefe("kein Absturz bei Netzfehler", True)
    pruefe("Rang ist None, nicht 0", e["BTC"]["funding_rang"] is None)
    pruefe("Fuenftel ist None, nicht 0", e["BTC"]["funding_fuenftel"] is None)
finally:
    MR.funding_werte = echt

print()
print("### 5. Zu duenner Querschnitt liefert NICHTS ###")
echt = MR.funding_werte
MR.funding_werte = lambda *a, **k: {"BTC": 0.1, "ETH": 0.2, "SOL": 0.3}
try:
    e = MR.raenge(["BTC", "ETH", "SOL"], mit_turnover=False)
    pruefe("drei Werte ergeben KEIN Fuenftel",
           e["BTC"]["funding_fuenftel"] is None,
           "unter %d Werten ist ein Fuenftel kein Fuenftel"
           % MR.MINDEST_QUERSCHNITT)
finally:
    MR.funding_werte = echt

print()
print("### 6. Die Mailzeile ist eine TATSACHE ###")
pruefe("leerer Eintrag -> keine Zeile", MR.saetze(None) == [])
s = MR.saetze({"funding_fuenftel": 4, "querschnitt_funding": 27})
pruefe("Fuenftel 4 erzeugt eine Zeile", len(s) == 1)
pruefe("die Zeile nennt den Querschnitt", "27" in s[0])
pruefe("keine Empfehlung im Text",
       not any(w in s[0].lower() for w in
               ("kaufen", "verkaufen", "meiden", "empfehl", "sollte")),
       "R-A: eine Tatsache gehoert in die Mail, eine Wertung nicht")

print()
print("=" * 66)

# ---------------------------------------------------------------------------
print()
print("### 7. ⚠️ DIE GRUNDGESAMTHEIT DES RANGS (31.08.2026) ###")
print("Die Frage, an der H gescheitert ist: worueber wird gerangt?")
print("  Watchlist -> haengt an unserer Auswahl  ✖")
print("  Markt     -> nie gemessen (58 % Uebereinstimmung)  ✖")
print("  MESSBASIS -> genau das, worauf die Beitragstabelle entstand  ✔")
print()
for _n, _erw in (("funding", 200), ("turnover", 30)):
    _b = MR.messbasis(_n)
    pruefe("Messbasis %s ist lesbar (%d Symbole)" % (_n, len(_b)),
           len(_b) >= _erw,
           "unter %d - dann ist die Grundgesamtheit nicht die gemessene" % _erw)

# ⚠️ DER KERNTEST: derselbe Wert muss dasselbe Fuenftel bekommen, egal
# wieviele Symbole uebergeben werden. Nutzervorgabe 31.08.: "ein neutraler
# Trade ist unabhaengig von der Anzahl der Assets zu bewerten."
_basis = sorted(MR.messbasis("funding"))[:40]
_gestellt = {s: float(i) for i, s in enumerate(sorted(MR.messbasis("funding")))}
_echt_f, _echt_t = MR.funding_werte, MR.turnover_werte
MR.funding_werte = lambda *a, **k: dict(_gestellt)
try:
    _viele = MR.raenge(_basis, mit_turnover=False)
    _wenige = MR.raenge(_basis[:3], mit_turnover=False)
    _zwei = MR.raenge(_basis[:2], mit_turnover=False)
    _gleich = all(
        _viele[s]["funding_fuenftel"] == _wenige[s]["funding_fuenftel"]
        == _zwei[s]["funding_fuenftel"] for s in _basis[:2])
    pruefe("⚠️ dasselbe Fuenftel bei 40, 3 und 2 uebergebenen Symbolen",
           _gleich,
           "bekommen: %s / %s / %s" % (
               [_viele[s]["funding_fuenftel"] for s in _basis[:2]],
               [_wenige[s]["funding_fuenftel"] for s in _basis[:2]],
               [_zwei[s]["funding_fuenftel"] for s in _basis[:2]]))
    pruefe("und der Querschnitt bleibt die Messbasis, nicht die Uebergabe",
           _viele[_basis[0]]["querschnitt_funding"]
           == _zwei[_basis[0]]["querschnitt_funding"] == len(_gestellt))
    # Der Watchlist-PLATZ dagegen MUSS sich unterscheiden - er ist eine
    # Auskunft ueber die eigene Liste.
    pruefe("der Watchlist-Platz haengt sehr wohl an der Uebergabe",
           _viele[_basis[0]]["platz_von"] != _zwei[_basis[0]]["platz_von"],
           "sonst waere er dieselbe Groesse wie das Fuenftel - und die "
           "Trennung von Bewertung und Auskunft waere aufgehoben")
finally:
    MR.funding_werte, MR.turnover_werte = _echt_f, _echt_t

# ⚠️ OHNE MESSBASIS KEIN RANG - lieber nichts als die falsche Menge.
_gemerkt = dict(MR._MESSBASIS_ZWISCHEN)
MR._MESSBASIS_ZWISCHEN["funding"] = set()
MR.funding_werte = lambda *a, **k: dict(_gestellt)
try:
    _ohne = MR.raenge(_basis, mit_turnover=False)
    pruefe("ohne lesbare Messbasis gibt es KEINEN Rang",
           all(v["funding_fuenftel"] is None for v in _ohne.values()),
           "ein Rang ueber die falsche Menge saehe aus wie ein richtiger")
finally:
    MR._MESSBASIS_ZWISCHEN.clear()
    MR._MESSBASIS_ZWISCHEN.update(_gemerkt)
    MR.funding_werte = _echt_f

print("ERGEBNIS: %d FEHL" % fehl)
sys.exit(1 if fehl else 0)
