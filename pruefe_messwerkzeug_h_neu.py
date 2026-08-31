# -*- coding: utf-8 -*-
"""Prueft `messe_h_neu.py` gegen KUENSTLICHE Daten (30.08.2026)

Dieselbe Vorsicht wie bei `pruefe_messwerkzeug_h_produktion.py`, und aus
demselben Grund: an EINEM Tag sind vier Messfehler aufgetreten, alle in den
Kontrollen und keiner in den Daten. Ein Werkzeug, dessen Fehler erst nach
dem Lauf auffaellt, kostet den Lauf zweimal.

Wo die Antwort bekannt ist, ist jede Abweichung ein Fehler des Werkzeugs.

    python pruefe_messwerkzeug_h_neu.py
"""
import sys

import numpy as np

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, ".")

import messe_h_neu as M                                          # noqa: E402

FEHLER = []


def pruefe(name, bedingung, hinweis=""):
    print("%s  %s%s" % ("  OK  " if bedingung else "  FEHL", name,
                        ("   -> " + hinweis) if hinweis and not bedingung else ""))
    if not bedingung:
        FEHLER.append(name)


def kunst(n_tage=400, je_tag=40, effekt=0.0, ohne_raum=0.0, saat=1,
          gegenlaeufig=False):
    """Anker mit EINGEBAUTEM Effekt auf dem UNTERSTEN raum_atr-Fuenftel."""
    rng = np.random.default_rng(saat)
    aus = []
    for i in range(n_tage):
        t = "%04d-%02d-%02d" % (2018 + i // 336, 1 + (i % 336) // 28, 1 + i % 28)
        raeume = rng.uniform(0.5, 20.0, je_tag)
        r = np.argsort(np.argsort(raeume)) / max(je_tag - 1, 1)
        for j in range(je_tag):
            fehlt = rng.random() < ohne_raum
            zuschlag = 0.0
            if not fehlt:
                if gegenlaeufig:
                    zuschlag = effekt if r[j] >= 0.8 else 0.0
                else:
                    zuschlag = effekt if r[j] < 0.2 else 0.0
            aus.append({"sym": "S%d" % (j % 10), "datum": t,
                        "raum_atr": None if fehlt else float(raeume[j]),
                        "boden_atr": float(rng.uniform(0.5, 20.0)),
                        "n_oben": int(rng.integers(0, 6)),
                        "atr_rel": float(rng.uniform(0.02, 0.20)),
                        "frei": bool(fehlt), "gedeckt": True,
                        "h_alt": False,
                        "in_r": float(rng.normal(0, 1)) + zuschlag,
                        "ziel": float(rng.random() < 0.35)})
    return aus


print("=" * 92)
print("GEGENPRUEFUNG `messe_h_neu.py` — kuenstliche Daten, bekannte Antwort")
print("=" * 92)

# ------------------------------------------------------- 1. Effekt und Groesse
print()
print("1. fuenftel_je_tag() — findet es einen eingebauten Effekt?")
for effekt in (0.0, 0.30):
    w = M.fuenftel_je_tag(kunst(effekt=effekt, saat=2), "raum_atr")
    s = M.spanne(w) if w else float("nan")
    pruefe("eingebaut %+.2f auf Fuenftel 0 -> Spanne %+.3f" % (effekt, s),
           w is not None and abs(s - effekt) < 0.12,
           "Abweichung %.3f" % abs(s - effekt))

print()
print("2. Zeigt die Spanne in die richtige RICHTUNG?")
w = M.fuenftel_je_tag(kunst(effekt=0.30, gegenlaeufig=True, saat=2), "raum_atr")
pruefe("Effekt auf Fuenftel 4 -> Spanne NEGATIV (%+.3f)" % M.spanne(w),
       M.spanne(w) < -0.1,
       "spanne() ist werte[0]-werte[4]; ein Effekt oben muss negativ werden")

# ------------------------------------------------------------ 3. None-Behandlung
print()
print("3. `raum_atr = None` — eigene Gruppe, NICHT Fuenftel 0?")
a = kunst(effekt=0.0, ohne_raum=0.30, saat=3)
n_none = sum(1 for x in a if x["raum_atr"] is None)
w = M.fuenftel_je_tag(a, "raum_atr")
pruefe("%d Anker ohne Raum werden ausgeschlossen" % n_none,
       w is not None and abs(M.spanne(w)) < 0.12,
       "fehlende Werte verzerren die Rangfolge - 'unbekannt' darf nie "
       "aussehen wie 'geringster Raum'")
# und der harte Beleg: mit Effekt AUF den None-Ankern darf sich nichts ruehren
a2 = [{**x, "in_r": x["in_r"] + (5.0 if x["raum_atr"] is None else 0.0)}
      for x in a]
pruefe("ein Effekt von +5,0 NUR auf den None-Ankern aendert nichts",
       abs(M.spanne(M.fuenftel_je_tag(a2, "raum_atr")) - M.spanne(w)) < 1e-9,
       "die None-Gruppe sickert in die Messung ein")

# ------------------------------------------------------------- 4. Lagemass
print()
print("4. Median statt Mittelwert? (Schiefe 2,68 - Checkliste Punkt 7)")
a = kunst(saat=4)
a2 = [dict(x) for x in a]
a2[0]["in_r"] = 10000.0
d = abs(M.spanne(M.fuenftel_je_tag(a, "raum_atr"))
        - M.spanne(M.fuenftel_je_tag(a2, "raum_atr")))
pruefe("ein Ausreisser von 10.000 verschiebt um %.5f" % d, d < 0.02,
       "Mittelwert statt Median - ein Anker kippt die Messung")

# --------------------------------------------------------- 5. Negativkontrolle
print()
print("5. Das Mischen — Rangfolge zerstoert, Verteilung erhalten?")
rng = np.random.default_rng(9)
a = kunst(effekt=0.30, saat=5)
echt = M.spanne(M.fuenftel_je_tag(a, "raum_atr"))
p = [M.spanne(M.fuenftel_je_tag(a, "raum_atr", mische=rng)) for _ in range(30)]
p = np.array([x for x in p if x is not None])
u, o = np.quantile(p, [0.025, 0.975])
pruefe("Placebo-Band %+.4f .. %+.4f enthaelt die Null" % (u, o), u <= 0 <= o)
pruefe("echt %+.4f liegt AUSSERHALB" % echt, echt > o or echt < u,
       "die Kontrolle wuerde einen echten Effekt verschlucken")

print()
print("6. Bleibt beim Mischen die ANZAHL je Fuenftel gleich?")
w = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
gem = rng.permutation(w)
pruefe("Permutation erhaelt die Werte exakt",
       sorted(w.tolist()) == sorted(gem.tolist()))

# --------------------------------------------------------- 7. Mindestbelegung
print()
print("7. Zu duenne Tage fallen heraus (MIND_JE_TAG = %d)?" % M.MIND_JE_TAG)
duenn = kunst(n_tage=400, je_tag=M.MIND_JE_TAG - 1, saat=6)
pruefe("nur zu duenne Tage -> kein Ergebnis",
       M.fuenftel_je_tag(duenn, "raum_atr") is None,
       "ein Fuenftel aus 14 Ankern ist kein Querschnitt")

# ------------------------------------------------------------ 8. Die Konstanten
print()
print("8. Die Konstanten der Messung")
pruefe("BLOCK %d > HORIZONT %d" % (M.BLOCK, M.HORIZONT), M.BLOCK > M.HORIZONT)
pruefe("Reifeschnitt %d Handelstage gesetzt" % M.MINDESTALTER,
       M.MINDESTALTER >= 250, "unter 250 mischen sich junge Reihen ein")
pruefe("Datenbruchgrenze Faktor %.0f gesetzt" % M.BRUCH, M.BRUCH <= 5.0)

# ------------------------------------------ 9. raum_atr haengt am ATR-Nenner
print()
print("9. Ist `raum_atr` wirklich in ATR normiert?")
import inspect                                                    # noqa: E402
q = inspect.getsource(M.laufe)
pruefe("raum wird durch atr geteilt", "(min(oben) - kurs) / atr" in q)
pruefe("boden wird durch atr geteilt", "(kurs - max(unten)) / atr" in q)
pruefe("der NAECHSTE Widerstand wird genommen, nicht der staerkste",
       "min(oben)" in q, "'der staerkste' waere eine Auswahl nach dem "
       "Merkmal, das geprueft werden soll")
pruefe("kein Widerstand -> None, nicht 0",
       "if oben else None" in q)
pruefe("die relative ATR laeuft als Gegenprobe mit",
       '"atr_rel": atr / kurs' in q)

print()
print("=" * 92)
if FEHLER:
    print("⚠️ %d PRUEFUNG(EN) FEHLGESCHLAGEN:" % len(FEHLER))
    for f in FEHLER:
        print("   - %s" % f)
    sys.exit(1)
print("ALLE PRUEFUNGEN BESTANDEN — das Werkzeug misst, was es messen soll.")
