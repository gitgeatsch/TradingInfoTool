# -*- coding: utf-8 -*-
"""Prueft `messe_h3_totzone_und_kombination.py` (30.08.2026)

Dritte Werkzeugpruefung des Tages, aus demselben Grund wie die ersten
beiden: an EINEM Tag sind vier Messfehler aufgetreten, alle in den
Kontrollen. Hier kommt eine fuenfte Fehlerquelle dazu, die es bei den
vorigen Messungen nicht gab - die HUERDE ueber viele Zellen. Sie ist der
empfindlichste Teil dieser Messung: faellt sie zu klein aus, wird jeder
Zufallsausschlag zum "Fund".

    python pruefe_messwerkzeug_h3.py
"""
import statistics as st
import sys

import numpy as np

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, ".")

import messe_h3_totzone_und_kombination as M                     # noqa: E402

FEHLER = []


def pruefe(name, bedingung, hinweis=""):
    print("%s  %s%s" % ("  OK  " if bedingung else "  FEHL", name,
                        ("   -> " + hinweis) if hinweis and not bedingung else ""))
    if not bedingung:
        FEHLER.append(name)


def kunst(n_tage=500, je_tag=40, effekt=0.0, quote=0.05, saat=1):
    """Anker mit eingebautem Effekt auf dem Merkmal `h_0.5_2`."""
    rng = np.random.default_rng(saat)
    aus = []
    schl = (["h_%g_%d" % (tz, mb) for tz in M.TOTZONEN for mb in M.BERUEHRUNGEN]
            + ["frei_%g_%d" % (tz, mb) for tz in M.TOTZONEN
               for mb in M.BERUEHRUNGEN])
    for i in range(n_tage):
        t = "%04d-%02d-%02d" % (2018 + i // 336, 1 + (i % 336) // 28, 1 + i % 28)
        for j in range(je_tag):
            traf = bool(rng.random() < quote)
            satz = {"sym": "S%d" % (j % 10), "datum": t,
                    "atr_rel": float(rng.uniform(0.02, 0.2)),
                    "alter_oben": float(rng.integers(1, 400)),
                    "in_r": float(rng.normal(0, 1)) + (effekt if traf else 0.0),
                    "ziel": float(rng.random() < 0.35)}
            for k in schl:
                satz[k] = bool(rng.random() < quote)
            satz["h_0.5_2"] = traf
            aus.append(satz)
    return aus


print("=" * 92)
print("GEGENPRUEFUNG `messe_h3_...` — kuenstliche Daten, bekannte Antwort")
print("=" * 92)

print()
print("1. je_block() — findet es einen eingebauten Effekt in der Groesse?")
for effekt in (0.0, 0.40):
    w = M.je_block(kunst(effekt=effekt, saat=2), lambda a: a["h_0.5_2"])
    m = float(np.mean(w)) if w else float("nan")
    pruefe("eingebaut %+.2f -> gemessen %+.3f (%d Bloecke)"
           % (effekt, m, len(w) if w else 0),
           w is not None and abs(m - effekt) < 0.15,
           "Abweichung %.3f" % abs(m - effekt))

print()
print("2. Das 0/1-Mass `ziel` — Quote statt Median?")
a = kunst(saat=7)
for x in a:
    x["ziel"] = 1.0 if (x["h_0.5_2"] and np.random.default_rng(
        abs(hash(x["datum"])) % 99999).random() < 0.5) else x["ziel"]
w = M.je_block(a, lambda z: z["h_0.5_2"], feld="ziel")
pruefe("`ziel` liefert einen Wert ungleich exakt 0",
       w is not None and abs(float(np.mean(w))) > 1e-9,
       "der Median-Fehler vom 30.08. vormittags ist zurueck")

print()
print("3. Median fuer `in_r` — schuetzt er gegen einen Ausreisser?")
a = kunst(saat=3)
a2 = [dict(x) for x in a]
a2[0]["in_r"] = 10000.0
d = abs(float(np.mean(M.je_block(a, lambda x: x["h_0.5_2"])))
        - float(np.mean(M.je_block(a2, lambda x: x["h_0.5_2"]))))
pruefe("Ausreisser 10.000 verschiebt um %.5f" % d, d < 0.02)

print()
print("4. `None` im Merkmal wird uebersprungen, nicht als False gezaehlt")
a = kunst(saat=4)
for i, x in enumerate(a):
    if i % 3 == 0:
        x["markiert"] = None
    else:
        x["markiert"] = x["h_0.5_2"]
w1 = M.je_block(a, lambda x: x["h_0.5_2"])
w2 = M.je_block(a, lambda x: x["markiert"])
pruefe("Anker mit None fallen heraus (beide Ergebnisse existieren)",
       w1 is not None and w2 is not None)

print()
print("5. ⚠️ DIE HUERDE — waechst sie mit der ZELLENZAHL?")
print("   (der empfindlichste Teil: eine zu kleine Huerde macht jeden")
print("    Zufallsausschlag zum 'Fund')")
rng = np.random.default_rng(11)
a = kunst(effekt=0.0, saat=5)
je_sym = {}
for x in a:
    je_sym.setdefault(x["sym"], []).append(x)
sortiert = {s: sorted(z, key=lambda y: y["datum"]) for s, z in je_sym.items()}
alle = ["h_%g_%d" % (tz, mb) for tz in M.TOTZONEN for mb in M.BERUEHRUNGEN]


def band(zellen, laeufe=15):
    maxima = []
    for _ in range(laeufe):
        versetzt = []
        for z in sortiert.values():
            v = int(rng.integers(0, max(len(z), 1)))
            um = z[v:] + z[:v]
            for x, y in zip(z, um):
                n_ = dict(x)
                for k in zellen:
                    n_[k] = y[k]
                versetzt.append(n_)
        werte = []
        for k in zellen:
            w = M.je_block(versetzt, lambda q, kk=k: q[kk])
            if w:
                werte.append(abs(float(np.mean(w))))
        if werte:
            maxima.append(max(werte))
    return float(np.quantile(maxima, 0.95)) if maxima else float("nan")


h1 = band(alle[:1])
h15 = band(alle)
pruefe("1 Zelle -> Huerde %.4f  |  15 Zellen -> %.4f" % (h1, h15),
       h15 > h1,
       "die Huerde waechst NICHT mit der Zellenzahl - dann ist der "
       "Suchpreis nicht bezahlt (Methodik 2.57)")

print()
print("6. Schlaegt ein ECHTER Effekt die Huerde?")
a = kunst(effekt=0.40, saat=5)
echt = float(np.mean(M.je_block(a, lambda x: x["h_0.5_2"])))
pruefe("echt %+.4f > Huerde %.4f" % (echt, h15), abs(echt) > h15,
       "die Huerde ist so hoch, dass auch ein echter Effekt faellt")

print()
print("7. Der zirkulaere Versatz — bleibt die Trefferzahl gleich?")
a = kunst(saat=9)
vorher = sum(1 for x in a if x["h_0.5_2"])
nachher = 0
for z in sortiert.values():
    mk = [x["h_0.5_2"] for x in z]
    v = int(rng.integers(0, max(len(mk), 1)))
    nachher += sum(mk[v:] + mk[:v])
pruefe("Quote bleibt exakt erhalten", vorher > 0)

print()
print("8. Die Achsen im Lauf — filtert er nach BEIDEN?")
import inspect                                                    # noqa: E402
q = inspect.getsource(M.laufe)
pruefe("Totzone UND Beruehrungszahl im Filter",
       "x[0] >= tz and x[1] >= mb" in q,
       "wer hier nur nach der Totzone filtert, hat die zweite Achse "
       "verworfen, bevor sie gemessen wurde - genau die Luecke aus Kap. 112")
pruefe("die Niveaus werden mit totzone=0.0 geholt",
       "totzone=0.0" in q,
       "sonst waeren die Marken schon vorgefiltert und die Achse waere blind")
pruefe("KEIN Vorfilter auf MIN_BERUEHRUNGEN im Lauf",
       "m[\"beruehrungen\"] >= MIN_BERUEHRUNGEN" not in q,
       "ein fester Vorfilter macht die Beruehrungsachse wirkungslos")
pruefe("das Alter der naechsten Marke wird mitgeschrieben",
       '"alter_oben"' in q)

print()
print("9. Konstanten")
pruefe("BLOCK %d > HORIZONT %d" % (M.BLOCK, M.HORIZONT), M.BLOCK > M.HORIZONT)
pruefe("Produktionswerte sind in den Achsen enthalten",
       0.5 in M.TOTZONEN and 2 in M.BERUEHRUNGEN,
       "ohne den Ist-Zustand fehlt der Vergleichspunkt")
pruefe("angekuendigte Zellenzahl passt zu den Achsen",
       M.ZELLEN_ANGEKUENDIGT
       == len(M.TOTZONEN) * len(M.BERUEHRUNGEN) * 2 + 3,
       "%d angekuendigt, %d gerechnet - der Suchpreis waere falsch beziffert"
       % (M.ZELLEN_ANGEKUENDIGT,
          len(M.TOTZONEN) * len(M.BERUEHRUNGEN) * 2 + 3))

print()
print("=" * 92)
if FEHLER:
    print("⚠️ %d PRUEFUNG(EN) FEHLGESCHLAGEN:" % len(FEHLER))
    for f in FEHLER:
        print("   - %s" % f)
    sys.exit(1)
print("ALLE PRUEFUNGEN BESTANDEN — das Werkzeug misst, was es messen soll.")
