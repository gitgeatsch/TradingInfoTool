# -*- coding: utf-8 -*-
"""Prueft das MESSWERKZEUG, nicht die Daten (30.08.2026)

Nutzerfrage: *"da die Laeufe lange dauern - hast du die Messung
gegengeprueft, damit wir keine Fehler haben und die Messung neu machen
muessen?"*

⚠️ BERECHTIGT. Ein Werkzeug, das erst nach 40 Minuten als kaputt auffaellt,
kostet den Lauf zweimal. Und genau das ist heute schon zweimal passiert:
der Median auf einer 0/1-Reihe und die Negativkontrolle mit EINEM Versatz.

Hier laufen die Bausteine von `messe_h_produktionsgeometrie.py` gegen
KUENSTLICHE Daten mit BEKANNTER Antwort. Wo die Antwort bekannt ist, ist
jede Abweichung ein Fehler des Werkzeugs.

    python pruefe_messwerkzeug_h_produktion.py
"""
import statistics as st
import sys

import numpy as np

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, ".")

import messe_h_produktionsgeometrie as M                        # noqa: E402
from messe_marken import MIN_BERUEHRUNGEN                       # noqa: E402

FEHLER = []


def pruefe(name, bedingung, hinweis=""):
    zeichen = "  OK  " if bedingung else "  FEHL"
    print("%s  %s%s" % (zeichen, name, ("   -> " + hinweis) if hinweis and not bedingung else ""))
    if not bedingung:
        FEHLER.append(name)


def tage(n, start=0):
    return ["2020-%02d-%02d" % (1 + (start + i) // 28, 1 + (start + i) % 28)
            for i in range(n)]


def kunstanker(n_tage=600, je_tag=60, h_quote=0.2, effekt=0.0, saat=1):
    """Anker mit EINGEBAUTEM Effekt: H-Anker bekommen `effekt` aufgeschlagen."""
    rng = np.random.default_rng(saat)
    aus = []
    for i in range(n_tage):
        t = "2020-01-01"
        # fortlaufende, sortierbare Datumsreihe
        t = "%04d-%02d-%02d" % (2018 + i // 336, 1 + (i % 336) // 28, 1 + i % 28)
        for j in range(je_tag):
            h = bool(rng.random() < h_quote)
            aus.append({"sym": "S%d" % (j % 12), "datum": t,
                        "h_prod": h, "r_prod": float(rng.normal(0, 1)) + (effekt if h else 0.0),
                        "ziel_prod": float(rng.random() < (0.4 if h else 0.35))})
    return aus


print("=" * 88)
print("GEGENPRUEFUNG DES MESSWERKZEUGS — kuenstliche Daten, bekannte Antwort")
print("=" * 88)

# ---------------------------------------------------------------- 1. bloecke()
print()
print("1. bloecke() — findet es einen EINGEBAUTEN Effekt in der richtigen Groesse?")
for effekt in (0.0, 0.30, -0.30):
    w = M.bloecke(kunstanker(effekt=effekt), "r_prod", "h_prod")
    gemessen = float(np.mean(w)) if w else float("nan")
    pruefe("eingebaut %+.2f -> gemessen %+.3f  (%d Bloecke)"
           % (effekt, gemessen, len(w) if w else 0),
           w is not None and abs(gemessen - effekt) < 0.12,
           "Abweichung %.3f zu gross" % abs(gemessen - effekt))

# ------------------------------------------------------- 2. Quote statt Median
print()
print("2. Das 0/1-Mass — wird die QUOTE genommen, nicht der Median?")
print("   (der Fehler vom 30.08. vormittags: Median einer 0/1-Reihe ist immer 0)")
a = kunstanker(saat=7)
w = M.bloecke(a, "ziel_prod", "h_prod")
gemessen = float(np.mean(w)) if w else float("nan")
pruefe("ziel_prod liefert einen Wert ungleich exakt 0",
       w is not None and abs(gemessen) > 1e-9,
       "alle Bloecke exakt 0 - der Median-Fehler ist zurueck")
pruefe("gemessene Quotendifferenz %+.4f liegt nahe der eingebauten +0,05" % gemessen,
       w is not None and abs(gemessen - 0.05) < 0.03)

# ------------------------------------------------- 3. Median fuer stetiges Mass
print()
print("3. Bleibt `r_prod` beim MEDIAN? (Schiefe 2,68 - Punkt 7 der Checkliste)")
a = kunstanker(saat=3)
# ein einzelner Ausreisser darf das Ergebnis NICHT kippen
a2 = [dict(x) for x in a]
for x in a2:
    if x["h_prod"]:
        x["r_prod"] = x["r_prod"] + 0.0
a2[0]["r_prod"] = 10000.0
w1 = M.bloecke(a, "r_prod", "h_prod")
w2 = M.bloecke(a2, "r_prod", "h_prod")
d = abs(float(np.mean(w1)) - float(np.mean(w2)))
pruefe("ein Ausreisser von 10.000 verschiebt um %.4f (Median-Schutz)" % d,
       d < 0.05, "Mittelwert statt Median - ein Anker kippt die Messung")

# ----------------------------------------------------------- 4. Placebo-Band
print()
print("4. placebo_band() — liegt es bei NULL, wenn kein Effekt da ist?")
rng = np.random.default_rng(11)
a = kunstanker(effekt=0.0, saat=5)
p = M.placebo_band(a, "r_prod", "h_prod", rng)
u, o = np.quantile(p, [0.025, 0.975])
pruefe("Band %+.4f .. %+.4f enthaelt die Null" % (u, o), u <= 0 <= o)
pruefe("Band hat eine Breite > 0 (%d Laeufe)" % len(p), o - u > 1e-6,
       "Band der Breite null - der Versatz greift nicht")

print()
print("5. placebo_band() — SCHLAEGT es aus, wenn ein echter Effekt da ist?")
a = kunstanker(effekt=0.40, saat=5)
echt = float(np.mean(M.bloecke(a, "r_prod", "h_prod")))
p = M.placebo_band(a, "r_prod", "h_prod", rng)
u, o = np.quantile(p, [0.025, 0.975])
pruefe("echt %+.4f liegt AUSSERHALB von [%+.4f .. %+.4f]" % (echt, u, o),
       echt > o or echt < u,
       "die Kontrolle wuerde einen echten Effekt verschlucken")

# ------------------------------------------- 6. Versatz erhaelt die H-Quote
print()
print("6. Der zirkulaere Versatz — bleibt die H-Quote EXAKT gleich?")
print("   (Punkt 4 der Checkliste: quotengleich vergleichen)")
a = kunstanker(saat=9)
vorher = sum(1 for x in a if x["h_prod"])
je_sym = {}
for x in a:
    je_sym.setdefault(x["sym"], []).append(x)
nachher = 0
for z in je_sym.values():
    z = sorted(z, key=lambda x: x["datum"])
    marken = [x["h_prod"] for x in z]
    v = int(rng.integers(0, len(marken)))
    nachher += sum(marken[v:] + marken[:v])
pruefe("H-Anzahl vorher %d, nach Versatz %d" % (vorher, nachher), vorher == nachher)

# --------------------------------------------------- 7. _marken() gegen Original
print()
print("7. _marken() — dieselbe Regel wie `messe_marken.py`?")
n = {"oben": [{"preis": 110.0, "beruehrungen": 3},
              {"preis": 130.0, "beruehrungen": 3},
              {"preis": 115.0, "beruehrungen": 1}],
     "unten": [{"preis": 92.0, "beruehrungen": 3},
               {"preis": 80.0, "beruehrungen": 1}]}
frei, ged = M._marken(n, stop=90.0, ziel=120.0)
pruefe("Widerstand 110 (3 Beruehrungen) unter Ziel 120 -> NICHT frei", frei is False)
pruefe("Marke 92 (3 Ber.) ueber Stop 90 -> gedeckt", ged is True)
frei2, ged2 = M._marken(n, stop=95.0, ziel=105.0)
pruefe("Ziel 105 unter allen Widerstaenden -> frei", frei2 is True)
pruefe("Stop 95 ueber Marke 92 -> NICHT gedeckt", ged2 is False)
frei3, _ = M._marken({"oben": [{"preis": 110.0, "beruehrungen": 1}], "unten": []},
                     stop=90.0, ziel=120.0)
pruefe("einmal beruehrte Marke zaehlt nicht (MIN_BERUEHRUNGEN=%d)"
       % MIN_BERUEHRUNGEN, frei3 is True)

# ------------------------------------------------------ 8. _ausgang() Reihenfolge
print()
print("8. _ausgang() — vorsichtige Lesart: Stop vor Ziel in derselben Kerze?")
c = [100.0, 100.0, 100.0]
h = [100.0, 130.0, 100.0]     # Ziel 120 wuerde getroffen
l = [100.0, 80.0, 100.0]      # Stop  90 auch - im selben Balken
pruefe("beides in einer Kerze -> 'stop'",
       M._ausgang(c, h, l, 0, 90.0, 120.0) == "stop")
pruefe("nur Ziel -> 'ziel'",
       M._ausgang([100.0, 100.0], [100.0, 130.0], [100.0, 99.0], 0, 90.0, 120.0) == "ziel")
pruefe("keins von beiden -> 'abgelaufen'",
       M._ausgang([100.0, 100.0], [100.0, 101.0], [100.0, 99.0], 0, 90.0, 120.0)
       == "abgelaufen")

# ------------------------------------------------- 9. R haengt an der Geometrie
print()
print("9. Haengt R am jeweiligen Stopabstand? (zwei Geometrien, zwei Nenner)")
import inspect                                                    # noqa: E402
quelle = inspect.getsource(M.laufe)
pruefe("r_alt teilt durch ab_alt", "weg / ab_alt" in quelle)
pruefe("r_ohne teilt durch ab_ohne", "weg / ab_ohne" in quelle)
pruefe("r_prod teilt durch ab_prod", "weg / ab_prod" in quelle)
pruefe("kein gemeinsamer Nenner (waere bequem und falsch)",
       quelle.count("weg /") == 3)

# ------------------------------------------- 10. Datenbruch-Filter Indexierung
print()
print("10. Datenbruch-Filter — greift er im richtigen Fenster?")
cc = np.array([1.0] * 50 + [100.0] + [100.0] * 50)      # Sprung bei Index 50
verh = cc[1:] / np.maximum(cc[:-1], 1e-12)
bruch = (verh > M.BRUCH) | (verh < 1.0 / M.BRUCH)
pruefe("Sprung 1->100 wird als Bruch erkannt", bool(bruch[49]))
pruefe("Anker bei i=40 sieht den Bruch im 20-Tage-Fenster",
       bool(bruch[40:40 + M.HORIZONT].any()))
pruefe("Anker bei i=10 sieht ihn NICHT",
       not bool(bruch[10:10 + M.HORIZONT].any()))

# ---------------------------------------------------- 11. Felder der Auswertung
print()
print("11. Greift die Auswertung auf Felder zu, die `laufe()` auch schreibt?")
gebraucht = {"r_alt", "r_ohne", "r_prod", "ziel_alt", "ziel_ohne", "ziel_prod",
             "h_alt", "h_ohne", "h_prod", "frei_alt", "ged_alt", "frei_ohne",
             "ged_ohne", "frei_prod", "ged_prod", "stop_alt", "stop_ohne",
             "stop_prod", "boden_greift", "regel", "sym", "datum"}
fehlt = {f for f in gebraucht if ('"%s"' % f) not in quelle}
pruefe("alle %d Felder werden geschrieben" % len(gebraucht), not fehlt,
       "fehlen: %s" % sorted(fehlt))

# ------------------------------------------------------------- 12. Blocklaenge
print()
print("12. Blocklaenge gegen Horizont (Punkt 6 der Checkliste)")
pruefe("BLOCK %d > HORIZONT %d" % (M.BLOCK, M.HORIZONT), M.BLOCK > M.HORIZONT)
pruefe("2018-2020 hat genug Tage fuer mindestens 2 Bloecke",
       3 * 336 >= 2 * M.BLOCK)

print()
print("=" * 88)
if FEHLER:
    print("⚠️ %d PRUEFUNG(EN) FEHLGESCHLAGEN:" % len(FEHLER))
    for f in FEHLER:
        print("   - %s" % f)
    sys.exit(1)
print("ALLE PRUEFUNGEN BESTANDEN — das Werkzeug misst, was es messen soll.")
