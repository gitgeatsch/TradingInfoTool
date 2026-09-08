# -*- coding: utf-8 -*-
"""N-64 — DIE STUFEN FUER `schnitt`, auf der selektierten Menge (07.09.2026)

## Was hergeleitet wird

`wahrscheinlichkeit.BEITRAEGE` fuehrt `schnitt` bereits - stillgelegt,
`merkmal="schnitt_fuenftel"`, `stufen=None`. Zum Wiederanschalten fehlen
genau fuenf Zahlen.

⚠️ **Punkte, nicht R.** Die Formel ist `q = basisrate + punkte/100` und
`wert_r = q*CRV - (1-q)`. Bei CRV 2,0 ist `dR/dPunkt = 3/100`, also

    Punkte = R / 0,03

Das ist keine Setzung, sondern die Umkehrung der Produktionsformel.

## ⚠️⚠️ DREI GRUENDE FUEHRTEN AM 31.08. ZUR RUECKNAHME - alle drei gelten

Der Kommentar in `wahrscheinlichkeit.py` nennt sie. 2.153 hat NUR den
Horizontlauf entlastet (kontaminierte Basis, 798 Nicht-Krypto). **Die
anderen beiden sind hier zu erfuellen:**

    1  TAGESKLAMMER    gepoolt gerechnet statt je Kalendertag.
                       -> dieselbe Statistik wie `je_tag_wirkung`.
    2  NICHT MONOTON   (+1,27 +1,59 +0,24 -1,28 -1,82) - Fuenftel 1 lag
                       ueber Fuenftel 0. Die Vorabfestlegung im Kopf von
                       `messe_schnittabstand_beitrag.py` verlangt
                       "monoton ueber die Fuenftel" fuer nutzbar.
                       -> WIRD HIER GEPRUEFT UND ENTSCHEIDET MIT.
    3  FREMDE ZAHL     eingetragen war turnovers H3-Wert.
                       -> jede Zahl unten stammt aus diesem Lauf.

## ⚠️ Der Fallstrick, der VOR der Deutung geprueft wird

`sammle` warnt in eigener Sache: bei 5 % von ~40 Werten sind das zwei
Anker, und ein Median aus zwei Werten ist Rauschen (+0,4469 R, das
Achtzehnfache des registrierten Beitrags). **Fuenf Fuenftel auf einer
Menge von acht Ankern je Tag haetten dasselbe Problem in Reinform.**

Deshalb steht die BESETZUNG je Fuenftel ganz vorne - und wenn sie nicht
reicht, ist das das Ergebnis, nicht ein Zwischenschritt.

## Aufbau

    Rang        aus dem VOLLEN Tagesquerschnitt (wie `marktrang` in der
                Produktion), erst danach auf die Menge verengt
    Menge       20 % selektiert - `frageart='beitrag'` (F-212)
    Wirkung     median(Fuenftel) - median(alle Gewaehlten) JE TAG
    Band        Blockbootstrap, Block 3 x Horizont
    Kontrolle   dieselbe Rechnung mit GEMISCHTEN Raengen, 5 Ziehungen -
                dort darf kein Fuenftel herausragen

    python n64_schnitt_stufen.py
"""
from __future__ import annotations

import sys
import time

import numpy as np

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# ⚠️ NAMENSSCHATTEN (T4c). In `messe_beitrag_auf_auswahl` heisst `W`
# das Modul `messe_regel_wirksamkeit` - dort liegen `rang` und `GRENZE`.
# Wer den Aliasnamen aus fremdem Code uebernimmt, ruft eine ANDERE Datei.
import messe_beitrag_auf_auswahl as A                        # noqa: E402
import messe_regel_wirksamkeit as RW                         # noqa: E402
import messe_eigenschaft_beitrag as B                        # noqa: E402
import messe_kandidaten_als_regel as K                       # noqa: E402
from messe_beitrag_auf_auswahl import momentum250            # noqa: E402
from messnorm import _block                                   # noqa: E402
from messnorm_auswahl import MENGEN                           # noqa: E402

HORIZONT, MENGE = 20, "20%"
PUNKT_JE_R = 1.0 / 0.03      # Umkehrung von q = basisrate + punkte/100
ZIEH, SAAT = 5, 20260907


def je_fuenftel(je_tag: dict, mom: dict, anteil: float, mische=None):
    """Je Kalendertag: median(Fuenftel k) - median(alle Gewaehlten).

    ⚠️ Baut Rang und Auswahlmaske mit DENSELBEN Funktionen wie `sammle` -
    keine Kopie, sonst misst diese Datei etwas anderes als der Massstab,
    gegen den sie antritt.
    """
    aus = {k: {} for k in range(5)}
    besetzt = {k: [] for k in range(5)}
    gewaehlt = []
    for tag, zeilen in je_tag.items():
        if len(zeilen) < 12:
            continue
        kz = np.array([x["kennzahl"] for x in zeilen], float)
        r = RW.rang(kz)
        if mische is not None:
            r = mische.permutation(r)
        y = np.array([x["in_r"] for x in zeilen], float)
        m = A._auswahl_maske(zeilen, mom.get(tag) or {}, anteil, None)
        if m is None or not m.any():
            continue
        rw, yw = r[m], y[m]
        gewaehlt.append(len(yw))
        # Fuenftel 0 = kleinster Rang = am WEITESTEN unter dem Schnitt
        f = np.clip((rw * 5).astype(int), 0, 4)
        alle = float(np.median(yw))
        for k in range(5):
            n = int((f == k).sum())
            besetzt[k].append(n)
            if n >= 1:
                aus[k][tag] = float(np.median(yw[f == k])) - alle
    return aus, besetzt, gewaehlt


def band(d: dict, block: int, zieh: int = 2000, saat: int = SAAT):
    """Blockbootstrap ueber die Kalendertage - Punktschaetzer und Band."""
    tage = sorted(d)
    v = np.array([d[t] for t in tage], float)
    if len(v) < 2 * block:
        return None
    rng = np.random.default_rng(saat)
    starts = np.arange(len(v) - block + 1)
    n = int(np.ceil(len(v) / block))
    z = np.empty(zieh)
    for i in range(zieh):
        s = rng.choice(starts, n)
        z[i] = np.mean(np.concatenate([v[j:j + block] for j in s])[:len(v)])
    return float(np.mean(v)), float(np.percentile(z, 5)), \
        float(np.percentile(z, 95)), len(v)


def main() -> int:
    t0 = time.time()
    print("=" * 96)
    print("N-64 — DIE STUFEN FUER `schnitt`, selektierte Menge %s" % MENGE)
    print("=" * 96)
    reihen = B.lade()
    mom = momentum250(reihen)
    je_tag = K.baue(reihen, "schnitt", horizont=HORIZONT)
    anteil = MENGEN[MENGE]
    block = _block(HORIZONT)
    print("  %d Reihen . %d Kalendertage . Block %d Tage"
          % (len(reihen), len(je_tag), block))

    aus, besetzt, gewaehlt = je_fuenftel(je_tag, mom, anteil)

    # ---- 1  DIE BESETZUNG, vor jeder Deutung ---------------------------
    print()
    print("  1  ⚠️ REICHT DIE BESETZUNG? — vor der Deutung")
    print("     Gewaehlte Anker je Tag: im Mittel %.1f (min %d, max %d)"
          % (float(np.mean(gewaehlt)), min(gewaehlt), max(gewaehlt)))
    print("     %-10s %10s %12s %14s"
          % ("Fuenftel", "Tage>=1", "Anker/Tag", "Tage mit >=3"))
    knapp = []
    for k in range(5):
        b = np.array(besetzt[k], float)
        print("     %-10d %10d %12.2f %14d"
              % (k, int((b >= 1).sum()), float(b.mean()), int((b >= 3).sum())))
        if float(b.mean()) < 2.0:
            knapp.append(k)
    if knapp:
        print("     ⚠️⚠️ Fuenftel %s haben im Mittel unter ZWEI Anker je Tag."
              % ", ".join(map(str, knapp)))
        print("        Ein Median aus ein bis zwei Werten ist Rauschen -")
        print("        `sammle` warnt in eigener Sache davor (+0,4469 R).")
    else:
        print("     ✔ Jedes Fuenftel hat im Mittel mindestens zwei Anker.")

    # ---- 2  DIE STUFEN --------------------------------------------------
    print()
    print("  2  DIE STUFEN — median(Fuenftel) - median(alle Gewaehlten)")
    print("     %-10s %10s %24s %8s %10s"
          % ("Fuenftel", "Wirkung R", "Band", "Tage", "Punkte"))
    werte = []
    for k in range(5):
        e = band(aus[k], block)
        if e is None:
            print("     %-10d  zu wenige Tage (%d)" % (k, len(aus[k])))
            werte.append(None)
            continue
        w, u, o, n = e
        werte.append((w, u, o))
        print("     %-10d %+10.4f [%+.4f .. %+.4f] %8d %+10.2f"
              % (k, w, u, o, n, w * PUNKT_JE_R), flush=True)

    # ---- 3  DIE KONTROLLE ----------------------------------------------
    print()
    print("  3  KONTROLLE — dieselbe Rechnung mit GEMISCHTEN Raengen")
    print("     %-10s %10s %24s   %s"
          % ("Fuenftel", "Wirkung R", "Spanne der Ziehungen", "Urteil"))
    null = {k: [] for k in range(5)}
    for z in range(ZIEH):
        a2, _, _ = je_fuenftel(je_tag, mom, anteil,
                               mische=np.random.default_rng(SAAT + z))
        for k in range(5):
            e = band(a2[k], block, zieh=400, saat=SAAT + z)
            if e:
                null[k].append(e[0])
    for k in range(5):
        if not null[k]:
            print("     %-10d  keine Ziehung gelungen" % k)
            continue
        m = float(np.mean(null[k]))
        echt = werte[k][0] if werte[k] else 0.0
        print("     %-10d %+10.4f [%+.4f .. %+.4f]   %s"
              % (k, m, min(null[k]), max(null[k]),
                 "✔ echt liegt ausserhalb"
                 if echt < min(null[k]) or echt > max(null[k])
                 else "⚠️ echt liegt IN der Nullspanne"))

    # ---- Urteil ---------------------------------------------------------
    print()
    print("=" * 96)
    print("WAS DAS HEISST")
    print("=" * 96)
    if any(w is None for w in werte):
        print("  ⚠️ Nicht alle Fuenftel messbar - keine Stufen.")
        print("  Dauer %.1f Minuten" % ((time.time() - t0) / 60.0))
        return 1
    p = [w[0] * PUNKT_JE_R for w in werte]
    # ⚠️ MONOTONIE: Fuenftel 0 (tief unter dem Schnitt) soll den GROESSTEN
    # Wert haben, Fuenftel 4 den kleinsten - das ist die Richtung, die
    # N-59 mit +0,1759 R gemessen hat.
    fallend = all(p[i] >= p[i + 1] - 1e-9 for i in range(4))
    steigend = all(p[i] <= p[i + 1] + 1e-9 for i in range(4))
    print("  Stufen (Punkte): %s" % " / ".join("%+.2f" % x for x in p))
    print("  Monotonie: %s"
          % ("✔ FALLEND - tief unter dem Schnitt ist am besten, wie erwartet"
             if fallend else
             "⚠️⚠️ STEIGEND - die Richtung ist umgekehrt" if steigend else
             "⚠️⚠️ NICHT MONOTON"))
    if not (fallend or steigend):
        print("     ⚠️ GENAU DER GRUND 2 DER RUECKNAHME VOM 31.08. Die")
        print("        Vorabfestlegung verlangt Monotonie fuer nutzbar -")
        print("        und sie stand VOR dieser Messung fest.")
    print("  Dauer %.1f Minuten" % ((time.time() - t0) / 60.0))
    return 0


if __name__ == "__main__":
    sys.exit(main())
