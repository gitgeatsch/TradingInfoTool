"""G7 — SELBSTTEST PRÜFER v2.1 (agent/gutachten_pruefer.py, ``fassung="v2.1"``) VOR dem Neurechnen in Stufe 2
(Voranalyse_G7_S7_Anlage_05_11.md S7-7; Nutzer 05.11.2026: *„ja - die punkte bitte machen“*).

  1  Gelesener Wert v2 gegen v2.1 an ALLEN Zuständen aller 335 Rückspieltage - wo weichen sie ab (e-Schreibweise), und passt v2.1
     zum Rohwert des Zustands?
  2  Der Selbsttest von v2 (g7_stufe0 a: 30 echte Tage, je Fehlerart 1.000 gepflanzte Fehler, dazu korrekte Wiedergaben) mit v2.1 -
     Erkennung muss 100 % bleiben, Fehlalarm 0
  3  Neue Art „Feld vertauscht“: gepflanzt wird eine ANDERE Zahl derselben Zeile als ``wert`` - v2.1 muss sie als ``wert_feld``
     ausweisen (v2: als ``wert``); eine Zahl, die NICHT in der Zeile steht, bleibt ``wert``
  4  Die abgelegten S1-Gutachten des laufenden Laufs mit v2.1 neu gezählt - nur Form und Treue, KEIN Kurs

    python Basisinfos/Rechenkern_02_10/g7_pruefer21_selbsttest.py   -> g7_pruefer21_selbsttest.txt
"""
import collections
import json
import os
import sqlite3
import sys

import numpy as np

HIER = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.dirname(os.path.dirname(HIER))
sys.path.insert(0, PROJ)
sys.path.insert(0, HIER)
from agent import gutachten_pruefer as GP      # noqa: E402
from agent import sichten_gutachten as G       # noqa: E402
from agent import zustaende as Z               # noqa: E402

TXT = []


def p(*a):
    s = " ".join(str(x) for x in a)
    print(s, flush=True)
    TXT.append(s)


def teil1(q):
    n = abw = 0
    bsp, passt_nicht = [], []
    for tag in G.tage():
        for z in q.tag(tag)[0]:
            if z.rang is None or z.quelle == "termin":
                continue
            n += 1
            a2, a21 = GP.angezeigt(z), GP.angezeigt(z, "v2.1")
            if a2 != a21:
                abw += 1
                if len(bsp) < 4:
                    bsp.append((tag, GP.schluessel(z), a2, a21))
            ref = [x for x in (z.wert, z.mass_wert) if x is not None]
            if a21 is not None and ref and not any(GP.ist_rundung(a21, r) or GP.ist_rundung(a21, 100 * r) for r in ref):
                passt_nicht.append((tag, GP.schluessel(z), a21, z.wert, z.mass_wert))
    p("1  gelesener Wert an %d Zuständen (335 Tage): v2 ≠ v2.1 in %d Fällen, Beispiele %s" % (n, abw, bsp))
    arten = collections.Counter(k for _, k, *_ in passt_nicht)
    p("   v2.1 passt weder zum Rohwert noch zum Maß (auch nicht ×100) in %d Fällen, nach Schlüssel %s" % (len(passt_nicht),
                                                                                                      dict(arten.most_common(6))))
    p("   Beispiele %s" % passt_nicht[:3])


def teil2():
    import g7_stufe0 as S0
    alt_e, alt_a = GP.eingabe, GP.angezeigt
    GP.eingabe = lambda zs, ev=None, sicht=None, fassung="v2.1": alt_e(zs, ev, sicht, "v2.1")
    GP.angezeigt = lambda z, fassung="v2.1": alt_a(z, "v2.1")
    try:
        S0.teil_a()
    finally:
        GP.eingabe, GP.angezeigt = alt_e, alt_a
    p("2  Selbsttest v2 mit v2.1 (Ausgabe von g7_stufe0 a, Bezeichnung 'v2' = hier v2.1):")
    for z in S0.AUS:
        p("   " + z)


def teil3(q, rng):
    n = feld = wert = v2feld = 0
    nicht = 0
    tage = G.tage()
    for _ in range(1000):
        tag = tage[rng.integers(len(tage))]
        L = [z for z in q.tag(tag)[0] if z.rang is not None and z.quelle != "termin"]
        z = L[rng.integers(len(L))]
        w = GP.angezeigt(z, "v2.1")
        andere = [x for x in GP.zeilenzahlen(z) if x != w and not GP.ist_rundung(x, w)]
        if not andere or w is None:
            continue
        x = andere[rng.integers(len(andere))]
        t = {"schluessel": GP.schluessel(z), "wert": x}
        e21 = GP.eingabe([z], None, z.sicht, "v2.1")
        e2 = GP.eingabe([z], None, z.sicht)
        a21 = [v["art"] for v in GP.pruefe({"treiber": [t]}, e21)["verstoesse"]]
        a2 = [v["art"] for v in GP.pruefe({"treiber": [t]}, e2)["verstoesse"]]
        n += 1
        feld += a21 == ["wert_feld"]
        v2feld += a2 == ["wert"] or (a2 == [] and GP.ist_rundung(x, GP.angezeigt(z)))
        fremd = w * 1.37 + 0.11
        if not any(GP.ist_rundung(fremd, y) for y in GP.zeilenzahlen(z)):
            nicht += 1
            wert += [v["art"] for v in GP.pruefe({"treiber": [{"schluessel": GP.schluessel(z), "wert": round(fremd, 4)}]},
                                                 e21)["verstoesse"]] == ["wert"]
    p("3  Feld vertauscht: %d Fälle · v2.1 als wert_feld %d (%.1f %%) · v2 meldete sie als wert %d · eine Zahl NICHT aus der Zeile "
      "bleibt wert: %d/%d" % (n, feld, 100 * feld / max(n, 1), v2feld, wert, nicht))


def teil4(q):
    c = sqlite3.connect("file:%s?mode=ro" % G.ABLAGE.replace("\\", "/"), uri=True)
    rows = c.execute("SELECT tag, sicht, felder, ereignisse, treue_verstoesse FROM gutachten WHERE form_ok=1 AND sicht IN "
                     "('S1','S3','S8','S2','S4') AND wdh=0").fetchall()
    z2, z21 = collections.Counter(), collections.Counter()
    b2 = b21 = 0
    for tag, sicht, f, em, tv in rows:
        liste, ev = q.tag(tag)
        zs = [z for z in liste if z.sicht == sicht]
        x = ev[ev.sicht == sicht]
        g = G.fuer_pruefer(json.loads(f), json.loads(em))
        r2 = GP.pruefe(g, GP.eingabe(zs, x, sicht))
        r21 = GP.pruefe(g, GP.eingabe(zs, x, sicht, "v2.1"))
        b2 += not r2["ok"]
        b21 += not r21["ok"]
        z2.update(v["art"] for v in r2["verstoesse"])
        z21.update(v["art"] for v in r21["verstoesse"])
        if (not r2["ok"]) != bool(tv):
            p("   ⚠ %s %s: abgelegt %s Beanstandungen, v2 neu %d - Eingabe hat sich geändert?" % (tag, sicht, tv, len(r2["verstoesse"])))
    p("4  abgelegte Gutachten (%d, nur Form/Treue): beanstandet v2 %d · v2.1 %d · Arten v2 %s · v2.1 %s" % (
        len(rows), b2, b21, dict(z2), dict(z21)))


def main():
    q = G.Quelle()
    rng = np.random.default_rng(21105)
    p("G7 SELBSTTEST PRÜFER v2.1 · kein Kurs, kein LLM")
    teil1(q)
    teil3(q, rng)
    teil4(q)
    teil2()
    open(os.path.join(HIER, "g7_pruefer21_selbsttest.txt"), "w", encoding="utf-8").write("\n".join(TXT) + "\n")


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:                                                  # noqa: BLE001
        pass
    main()
