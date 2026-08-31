# -*- coding: utf-8 -*-
"""Prueft `messe_bodenabstand.py` gegen kuenstliche Daten (31.08.2026)

Vierte Werkzeugpruefung dieser Arbeit. Die drei vorigen haben jeweils
mindestens einen echten Fehler gefunden - Median auf 0/1, Placebo mit einem
Versatz, Positivkontrolle auf echten Werten. Hier kommt eine Fehlerquelle
dazu, die es vorher nicht gab: die STUFENZUORDNUNG. Sie ist der Kern dieser
Messung, und eine vertauschte Ordnung wuerde den Befund lautlos umdrehen.

    python pruefe_messwerkzeug_bodenabstand.py
"""
import statistics as st
import sys

import numpy as np

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, ".")

import messe_bodenabstand as M                                   # noqa: E402

FEHLER = []


def pruefe(name, bedingung, hinweis=""):
    print("%s  %s%s" % ("  OK  " if bedingung else "  FEHL", name,
                        ("   -> " + hinweis) if hinweis and not bedingung else ""))
    if not bedingung:
        FEHLER.append(name)


def kunst(n_tage=500, je_tag=40, effekt=0.0, saat=1, ohne_boden=0.15):
    """Anker mit eingebautem Effekt auf STUFE 4 (kein Boden)."""
    rng = np.random.default_rng(saat)
    aus = []
    for i in range(n_tage):
        t = "%04d-%02d-%02d" % (2018 + i // 336, 1 + (i % 336) // 28, 1 + i % 28)
        for j in range(je_tag):
            if rng.random() < ohne_boden:
                b = None
            else:
                b = float(rng.uniform(0.25, 2.0))
            s = M.stufe_fest_geordnet({"boden_2": b})
            aus.append({"sym": "S%d" % (j % 10), "datum": t,
                        "boden_2": b, "boden_3": b, "boden_4": b,
                        "atr_rel": float(rng.uniform(0.02, 0.2)),
                        "lebt": bool(rng.random() < 0.8),
                        "funding": float(rng.normal(0, 1)),
                        "in_r": float(rng.normal(0, 1)) + (effekt if s == 4 else 0.0),
                        "ziel": float(rng.random() < 0.35)})
    return aus


print("=" * 92)
print("GEGENPRUEFUNG `messe_bodenabstand.py`")
print("=" * 92)

print()
print("1. ⚠️ DIE STUFENZUORDNUNG — der Kern dieser Messung")
faelle = ((None, 4, "kein Boden bis zum Stop"),
          (0.30, 3, "ganz nah am Kurs"),
          (0.49, 3, "knapp unter 0,5"),
          (0.50, 2, "Bandgrenze 0,5 gehoert nach oben"),
          (0.99, 2, "knapp unter 1,0"),
          (1.00, 1, "Bandgrenze 1,0"),
          (1.49, 1, "knapp unter 1,5"),
          (1.50, 0, "Bandgrenze 1,5 - unmittelbar ueber dem Stop"),
          (1.99, 0, "knapp unter dem Stop"))
for w, erw, klar in faelle:
    got = M.stufe_fest_geordnet({"boden_2": w})
    pruefe("boden=%-5s -> Stufe %d  (%s)" % (w, got, klar), got == erw,
           "erwartet %d" % erw)

print()
print("2. Die ORDNUNG — ist Stufe 0 wirklich das SCHLECHTE Ende?")
print("   (eine vertauschte Ordnung dreht den Befund lautlos um)")
a = kunst(effekt=0.40, saat=2)
w = M.stufen_wirkung(a, M.stufe_fest_geordnet)
pruefe("Stufe 4 (kein Boden) hat den hoechsten Wert",
       w is not None and w[4] == max(w),
       "der eingebaute Effekt sitzt auf Stufe 4 - erscheint er woanders, "
       "ist die Zuordnung verdreht")
pruefe("spanne() = Stufe4 - Stufe0 ist POSITIV (%+.3f)" % M.spanne(w),
       M.spanne(w) > 0.2,
       "spanne() muss so herum rechnen, dass ein Effekt auf Stufe 4 "
       "positiv erscheint")

print()
print("3. Findet die Messung den eingebauten Effekt in der GROESSE?")
for effekt in (0.0, 0.20, 0.40):
    w = M.stufen_wirkung(kunst(effekt=effekt, saat=3), M.stufe_fest_geordnet)
    s = M.spanne(w) if w else float("nan")
    pruefe("eingebaut %+.2f -> Spanne %+.3f" % (effekt, s),
           w is not None and abs(s - effekt) < 0.12,
           "Abweichung %.3f" % abs(s - effekt))

print()
print("4. `boden = None` heisst 'kein Boden', NICHT 'Abstand 0'")
a = kunst(saat=4, ohne_boden=0.15)
ohne = [x for x in a if x["boden_2"] is None]
pruefe("%d Anker ohne Boden landen alle auf Stufe 4" % len(ohne),
       all(M.stufe_fest_geordnet(x) == 4 for x in ohne))
pruefe("und KEINER auf Stufe 3 (das waere 'ganz nah')",
       not any(M.stufe_fest_geordnet(x) == 3 for x in ohne))

print()
print("5. Median statt Mittelwert bei `in_r`?")
a = kunst(saat=5)
a2 = [dict(x) for x in a]
a2[0]["in_r"] = 10000.0
d = abs(M.spanne(M.stufen_wirkung(a, M.stufe_fest_geordnet))
        - M.spanne(M.stufen_wirkung(a2, M.stufe_fest_geordnet)))
pruefe("Ausreisser 10.000 verschiebt um %.5f" % d, d < 0.02)

print()
print("6. Quote statt Median beim 0/1-Mass `ziel`?")
a = kunst(saat=6)
for x in a:
    if M.stufe_fest_geordnet(x) == 4:
        x["ziel"] = 1.0
w = M.stufen_wirkung(a, M.stufe_fest_geordnet, feld="ziel")
pruefe("`ziel` liefert eine Spanne ungleich exakt 0 (%+.4f)"
       % (M.spanne(w) if w else float("nan")),
       w is not None and abs(M.spanne(w)) > 1e-9,
       "der Median-Fehler vom 30.08. ist zurueck")

print()
print("7. Die Negativkontrolle — mischt sie die STUFEN, nicht die Werte?")
rng = np.random.default_rng(11)
a = kunst(effekt=0.0, saat=7)
p = []
for _ in range(20):
    w = M.stufen_wirkung(a, M.stufe_fest_geordnet, mische=rng)
    if w:
        p.append(M.spanne(w))
p = np.array(p)
u, o = np.quantile(p, [0.025, 0.975])
pruefe("Placebo-Band %+.4f .. %+.4f enthaelt die Null" % (u, o), u <= 0 <= o)
a = kunst(effekt=0.40, saat=7)
echt = M.spanne(M.stufen_wirkung(a, M.stufe_fest_geordnet))
pruefe("echt %+.4f liegt ausserhalb" % echt, echt > o or echt < u)

print()
print("8. Der Lauf — die Felder und die Nichtfilterung")
import inspect                                                    # noqa: E402
q = inspect.getsource(M.laufe)
pruefe("der Boden wird durch atr geteilt",
       '(kurs - m["preis"]) / atr' in q)
pruefe("nur Boeden DIESSEITS des Stops zaehlen (x < K)",
       "x < K" in q,
       "ein Boden unterhalb des Stops ist fuer diese Frage bedeutungslos")
pruefe("kein Boden -> None, nicht 0",
       "min(nah) if nah else None" in q)
pruefe("Beruehrungszahl bleibt eine Achse (2/3/4)",
       "for mb in BERUEHRUNGEN" in q)
pruefe("Survivorship-Feld `lebt` wird geschrieben", '"lebt"' in q)
pruefe("Funding wird gejoint", '"funding"' in q)

print()
print("9. Konstanten und Bandgrenzen")
pruefe("TOTZONE %.2f < unterste Bandgrenze %.2f" % (M.TOTZONE, M.BAENDER[0][0])
       or True,
       M.TOTZONE <= M.BAENDER[0][0],
       "liegt die Totzone UEBER der untersten Bandgrenze, ist Stufe 3 leer - "
       "genau der Fehler, der vor dem Lauf gefunden wurde")
pruefe("oberste Bandgrenze %.1f == Stopabstand K %.1f"
       % (M.BAENDER[-1][1], M.K), abs(M.BAENDER[-1][1] - M.K) < 1e-9,
       "die Baender muessen genau bis zum Stop reichen")
pruefe("BLOCK %d > HORIZONT %d" % (M.BLOCK, M.HORIZONT), M.BLOCK > M.HORIZONT)

print()
print("=" * 92)
if FEHLER:
    print("⚠️ %d PRUEFUNG(EN) FEHLGESCHLAGEN:" % len(FEHLER))
    for f in FEHLER:
        print("   - %s" % f)
    sys.exit(1)
print("ALLE PRUEFUNGEN BESTANDEN — das Werkzeug misst, was es messen soll.")
